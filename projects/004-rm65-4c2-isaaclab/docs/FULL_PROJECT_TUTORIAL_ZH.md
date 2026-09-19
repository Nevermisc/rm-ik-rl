# 从零完成 RM65-B + 4C2 + π0.5：项目路线、代码和问题复盘

这份教程面向有 Python 基础、第一次做具身智能的人。它记录本项目实际采用的路线、每一步为什么存在、代码放在哪里、遇到过什么问题，以及如何判断“真的成功”而不是只看到机械臂动了一下。

## 0. 最终目标和当前边界

最终目标有两层：

1. 在 IsaacLab 中输入文字指令，由针对 RM65-B + 4C2 微调的 π0.5 根据双相机和机器人状态闭环完成抓放；
2. 在满足安全门以后，把同一套观测、策略和动作语义部署到真实 RM65-B 与真实 4C2。

必须分开记录三类结果：

- **脚本专家仿真**：传统 IK 和状态机控制，负责产生可靠示教；
- **π0.5 仿真闭环**：模型真正反复观察并输出动作；
- **π0.5 真机闭环**：模型动作经过真机安全层后实际执行。

前一种成功不能代替后一种。任何报告都应包含 `expert`、`pi05_used`、`simulation_only` 和 `real_robot_command_sent`，避免把不同阶段混在一起。

## 1. 先建立概念地图

```text
π0.5
  学习得到的视觉-语言-动作策略，负责根据观测提出动作

Isaac Sim
  物理、渲染、USD 场景和传感器运行时

IsaacLab
  建立在 Isaac Sim 上的机器人学习框架，负责环境、批量仿真和训练接口

LIBERO
  另一套机器人操作 benchmark，不是 Isaac Sim，也不是 RM65 驱动

ROS2 / RealMan driver
  真机通信层，负责读取反馈和把安全动作发给 RM65 控制器
```

π0.5 是“大脑”，仿真器是可重复、可测量的练习场，ROS2 驱动是连接真实硬件的神经和肌肉接口。模型本身不会自动知道 RM65 有六个关节、4C2 如何开合、相机装在哪里，这些都要通过接口定义、数据和标定补齐。

## 2. 为什么先跑官方 Franka，再换 RM65

先用官方或近官方的 Franka 场景，目的是把两类问题分开：

```text
官方 Franka 也失败
  → 优先检查 checkpoint、OpenPI、CUDA、WebSocket、图像和推理环境

官方 Franka 成功，RM65 失败
  → 优先检查 RM65 资产、关节顺序、动作语义、相机和微调数据
```

本项目的 Franka + π0.5 IsaacLab 闭环已经完成 3/3。它证明新机器能同时运行模型服务器和仿真客户端，但它不证明 Franka checkpoint 能控制 RM65。

曾经出现第一次推理超过 WebSocket keepalive 时间，连接报 `ping timeout`。模型实际上仍在做 JAX 首次编译。处理方法是对本地长推理连接关闭 keepalive ping，先做一次 warm-up，再统计稳态延迟。这个修复解决通信超时，不改变模型输出。

## 3. 把 RM65 和 4C2 变成可用仿真资产

### 3.1 输入文件

RM65 模型来自：

```text
~/robot-learning/rm-ik-rl/assets/RM65-B
```

4C2 原始模型来自用户给出的 Windows `D:\d\4C2`，迁移到新实验室电脑后保存在：

```text
~/robot-learning/004-rm65-4c2-isaaclab/external/4C2
```

原始 4C2 包只有 URDF、STL、惯性和关节信息，没有真机通信驱动。

### 3.2 组合与导入

`scripts/build_combined_urdf.py` 做四件事：

1. 读取 RM65 URDF；
2. 给 4C2 的 link 和 joint 加 `tool_` 前缀，避免重名；
3. 用固定关节把夹爪基座安装到 RM65 `link_6`；
4. 按需要加入仿真碰撞垫，再输出组合 URDF。

`scripts/import_combined_urdf.py` 把组合 URDF 转为 Isaac 使用的 USD。导入后必须检查 articulation root、6 个机械臂关节、6 个活动夹指和碰撞体数量，不能只看画面外形。

### 3.3 为什么夹爪模型看起来对，最初却抓不住

原始网格的视觉表面与有效碰撞面不完全一致。最初闭合时主要是夹爪基座碰到方块，左右指面没有形成持续双侧接触。我们通过接触传感器和局部坐标反算定位问题，加入两个薄碰撞垫，并分别做：

- 五个静态扰动位置；
- 中心、左右 ±2 mm 的重力运输；
- 多目标机械臂到位回归。

这里的碰撞垫是仿真修正，不能直接当作真实夹爪尺寸。真机前仍要测量指面和开口。

另一个问题是 NumPy `float64` 目标写入 PyTorch `float32` 状态张量，表面上像 PhysX 崩溃，实际是类型不一致。修复方式是所有关节命令在写入前显式转换到仿真状态的 device 和 dtype。

## 4. 先写传统专家，再训练 π0.5

直接让随机或未适配模型探索抓取会浪费大量计算，也很难判断失败来自哪里。传统专家把任务拆成可检查阶段：

```text
SOURCE_SETTLE
→ APPROACH
→ CLOSE
→ LIFT
→ TRANSFER
→ PLACE_DESCENT
→ OPEN
→ RETREAT
→ FINAL_SETTLE
```

核心脚本是：

```text
scripts/run_pick_place_baseline.py
```

它使用 Lula 解 RM65 的全位姿 IK，再以平滑关节目标驱动 articulation。每个阶段都打印标记，并在最后计算抬升高度、移动距离、落点误差、释放漂移和状态有限性。

### 4.1 实际遇到的运动学问题

**基座高度错误。** 旧场景把机械臂安装面放在世界 `z=0`，桌面却在约 `z=0.733 m`，严格顶部抓取超出工作半径。加入 `--robot-base-z-m 0.65`，并明确世界坐标与机器人基座坐标的换算后，顶部抓取才可达。

**下降过程跳到等价 IK 分支。** 某些路点姿态相同，但求解器选了完全不同的腕部关节组合，相邻命令跳变约 3.51 rad。解决方法是在未旋转的基座坐标中先求一条连续下降轨迹，再只对关节 1 应用转运旋转；最大相邻变化降到约 0.04031 rad。

**边界位置不可达。** case 12 在固定 9 cm 预抓取距离上靠近 IK 边界。改为从安全距离开始，根据可解性自适应选择预抓取路点，同时保持抓取几何不变。

**放置后漂移超阈值。** case 44 的任务动作都完成，但释放后漂移 22.65 mm，大于 20 mm 阈值。证据显示放置末端关节跟踪误差约 0.166 rad。把每个约 1 cm 放置路点从 120 个物理步增加到 180 个，重跑通过。原失败样本单独归档，没有混进训练集。

## 5. 一帧专家数据究竟是什么

物理仿真运行在 240 Hz，每 12 个物理步采样一次，因此数据频率为 20 Hz。每帧先记录当前观测，再记录即将执行的动作：

```text
observation_state: 6 个实际关节角 + 1 个归一化夹爪状态
external_image:    外部 RGB
wrist_image:       腕部 RGB
prompt:            文字指令
action:            6 个绝对关节目标 + 1 个归一化夹爪目标
cube_pose:         只用于验证任务，不作为策略输入
phase:             专家状态机阶段，用于排错
```

夹爪接口在仿真中约定 `0=张开、1=闭合`：

```python
normalized = clip(tool_gripper_joint / 0.865, 0, 1)
```

真实夹爪不能照抄这个角度映射，必须单独标定。

`openpi_extension/expert_episode.py` 负责记录和格式校验，`scripts/validate_expert_episode.py` 检查形状、有限值、时间单调、图像配对和范围。

## 6. 为什么收集 45 条，而不是只录一次

一次成功只教会模型一个固定轨迹。正式计划覆盖：

```text
5 个转运角 × 3 个 x 偏移 × 3 个 y 偏移 = 45 个条件
```

同时轮换五种意思相同的英文指令。`config/rm65_expert_collection_plan_v1.json` 是机器可读计划，`scripts/run_expert_collection_plan.py` 支持中断后续跑，且不会静默覆盖条件不一致的旧 episode。

最终实测：

```text
45 / 45 通过
36 train      16,179 frames
9 validation   3,996 frames
总计          20,175 frames
```

validation 按条件固定划分，不参与训练。它用于离线检查泛化，但只有闭环任务才能证明模型真正完成操作。

## 7. 转换成 OpenPI 能读的数据

原始 episode 是本项目的便携中间格式。`scripts/convert_expert_episodes_to_lerobot.py` 只接受满足以下条件的样本：

- `task_success=true`；
- `unassisted_full_task_complete=true`；
- 双图像完整且尺寸一致；
- 状态、动作和图像帧数一致。

转换后的本地 LeRobot 数据集位于：

```text
~/.cache/huggingface/lerobot/local/rm65_sim_train
~/.cache/huggingface/lerobot/local/rm65_sim_validation
```

完整 episode 中约 31% 是保持或最终静止帧。策略没有显式的“当前阶段计时器”，所以几乎相同的起始画面可能同时对应“继续保持”和“开始靠近”两种标签。机器分析给出的结果是：v1 的 855 个 `SOURCE_SETTLE` 帧中，只有 270 个（31.6%）的 10 步动作窗口包含开始运动。若模型学成保持动作，它可能在闭环起点一直等待。

因此项目同时准备了一个不修改原始数据的 policy-window 视图：

```text
~/.cache/huggingface/lerobot/local/rm65_sim_policy_train
~/.cache/huggingface/lerobot/local/rm65_sim_policy_validation
```

它保留所有实际运动阶段，只缩短保持段，去掉任务成功后才发生的 retreat/final-settle。起始帧从每条 19 帧缩到最后 2 帧，90/90 个保留起始帧的动作窗口都包含开始运动。`analyze_policy_window_transitions.py` 还验证了筛选没有制造大动作断点：跨被删帧的最大关节目标变化约 `0.00307 rad`，低于 `0.05 rad` 仿真门限。

正式 v1 训练已经开始，所以没有在中途更换数据。先完成 v1 并做闭环；若证据显示它停在起点，再使用 `train_rm65_pi05_policy_window.sh` 训练 v2。这是由失败模式触发的受控迭代，不是看到 loss 不够低就随意换方案。

`openpi_extension/rm65_policy.py` 把仓库字段转换为 π0.5 通用字段。RM65 有 7 维状态和 7 维动作，而模型内部使用 32 维槽位；transform 负责补齐和在输出时只取前 7 维。训练时前六轴动作转换为相对当前状态的 delta，夹爪保持绝对值；推理输出再逆变换为六轴绝对目标和夹爪目标。

## 8. 归一化统计为什么必须重新算

Franka、DROID 与 RM65 的关节范围和数据分布不同。若沿用别的机器人统计量，相同数值在模型看来代表完全不同的尺度。

`scripts/compute_rm65_norm_stats.py` 计算 train split 的 `state` 和 `actions` 统计，并写到：

```text
~/robot-learning/openpi/assets/pi05_rm65_lora/local/rm65_sim_train/norm_stats.json
```

当前计算处理 16,128/16,179 帧；51 帧因固定 batch 的 floor 行为没有进入统计，占约 0.3%。正式训练使用的就是这份有哈希记录的统计，不能在训练中途更换。

## 9. π0.5 微调配置与 16 GB 显存问题

`openpi_extension/rm65_training_config.py` 定义：

```text
基础模型              pi05_base
动作块长度            10
PaliGemma LoRA         rank 16
action expert LoRA     rank 32
batch size             1
```

第一次按默认长度和视觉塔训练，XLA 训练图约需 15.98 GiB，随后还要申请约 5.36 GiB，RTX 4080 SUPER 16 GB 因此 OOM。解决方案有两项：

1. 任务指令很短，把最大 token 数从 200 降到 64；
2. 冻结预训练 SigLIP 视觉编码器，只训练语言/动作适配部分和投影。

调整后估算训练步约 7.35 GiB；2 步 smoke test 与 20 步 benchmark 都实际通过。正式训练命令封装在 `scripts/train_rm65_pi05.py`，训练日志由 `scripts/summarize_pi05_training_log.py` 转成机器可读 loss、gradient 和 parameter norm 证据。

## 10. 三种验证不要混淆

### 10.1 单帧 checkpoint 验证

`validate_rm65_checkpoint.py` 检查：

- checkpoint 能恢复；
- 输出形状为 `(10, 7)`；
- 所有值有限；
- 动作安全层能处理输出。

它不能证明任务成功。

### 10.2 validation 离线模仿误差

`evaluate_rm65_checkpoint_offline.py` 只加载一次模型，在 9 条 held-out episode 上抽样，比较预测动作与专家动作，并统计安全层触发次数。它能发现明显的数据/模型问题，仍不能代替闭环。

### 10.3 IsaacLab 闭环

`run_pi05_rm65_closed_loop.sh` 同时启动策略服务器和 IsaacLab：

```text
观察当前双图像和状态
→ π0.5 输出 10 步动作块
→ 安全层限位
→ 只执行前几步
→ 重新观察并再次推理
```

这叫 receding-horizon control。相比一次执行完整动作块，它能用新图像修正误差。

`run_pi05_rm65_closed_loop_suite.py` 使用 20 条新角度/位置组合做可恢复评测。真机门要求至少 20 条有效仿真 episode 且成功率不低于 80%。

`validate_rm65_evaluation_plan.py` 会在启动 Isaac 前证明这些条件是留出的范围内插值：示范角度为 `0.6/0.7/0.8/0.9/1.0`，评测角度为 `0.65/0.75/0.85/0.95`；20 个完整的角度与位置组合都没有出现在示范中，同时仍位于训练范围内。评测还混合一个见过的指令和四个未见过的同义措辞。它衡量的是训练范围内的插值鲁棒性，不能解释为任意物体或任意场景泛化。

> 本节最终成功率必须读取 `results/rm65_pi05_eval_v1_summary.json`。文件尚未生成时，不得写成已经成功。

## 11. 策略清单和 fail-closed 安全门

`build_rm65_policy_artifact.py` 对整个 checkpoint 目录做确定性树哈希，对 norm stats 做文件哈希，并把训练、仿真评测和硬件准备证据写入 manifest。

`openpi_extension/execution_gate.py` 的原则是：缺证据就阻止执行，不根据文件名或口头描述猜测。仿真门要求 RM65-B、4C2、π0.5、动作维度、checkpoint 和统计量全部匹配。真机门还要求仿真成功率、急停、软件停止、限速、工作空间、关节顺序、夹爪标定、双相机标定和 watchdog 全部通过。

## 12. 真机侧已经知道什么，还缺什么

新电脑有 RealMan ROS2 Jazzy 驱动。当前 RM65 配置为：

```text
arm_ip: 192.168.1.19
udp_ip: 192.168.1.10
joint names: joint1 ... joint6
UDP cycle: 5 ms
```

通用 C++ 默认地址是 `192.168.1.18`，但当前 YAML 覆盖为 `.19`，最终要与示教器核对。

实时关节接口 `rm_ros_interfaces/msg/Jointpos` 使用弧度，驱动内部再转换为控制器角度。`openpi_extension/real_robot_adapter.py` 会按 `joint1...joint6` 重排反馈，把真机初期单步限制收紧为 `0.01 rad`，再把 20 Hz 策略目标插值成 50 Hz 驱动目标。这样 0.5 秒、10 个策略点会成为 25 个均匀控制点；测试轨迹的相邻驱动点最大约为 `0.004 rad`。这个函数没有 ROS 副作用，真正发送前仍必须核对最新反馈并运行 watchdog。

RealMan gripper 消息把 1～1000 描述为 0～70 mm 开口，但还不知道当前 4C2 是否接入这个原生接口。`config/rm65_4c2_gripper_calibration_template.json` 默认 `verified=false`；没有实际开闭命令和宽度测量，代码拒绝做映射。

ROS2 已安装 RealSense 包，但当前 USB 没有检测到 D435i。旧的 `Link6 → camera_link` 只是临时 TF，不是手眼标定结果。

`scripts/audit_real_robot_readiness.py` 可以随时重跑电脑侧准备审计。当前报告是 `blocked`：有线口还没有 `192.168.1.x` 地址、控制器不可达、没有相机设备、4C2 标定未验证，现场急停与人工监护也必须手动确认。报告是只读的，并明确写入 `real_robot_command_sent=false`。

接好机械臂并启动驱动后，先运行 `scripts/probe_rm65_joint_feedback.py`。它只订阅 `/joint_states`，不创建发布器；检查 `joint1...joint6` 名称、六轴弧度有限值、关节范围、消息时间单调和至少 20 Hz 的反馈。只有探针通过，才能把“只读反馈已验证”写入真机门禁。

下一步运行 `scripts/run_rm65_policy_shadow.py`：它读取关节与双相机、调用 RM65 专用 π0.5、执行真机限幅和 50 Hz 插值，只把建议写入 JSONL。它没有 RealMan 控制消息和 ROS 发布器，所以这是验证“真实传感器 → 模型 → 安全层”的只读阶段。RealMan 驱动当前没有连续夹爪位置 topic，夹爪状态必须作为现场确认的静态值输入并记录来源。连续传感器错误会在达到上限后退出，不能无限产生重复拒绝记录。真机门禁额外要求 `policy_shadow_passed=true`；`human_supervisor_required=true` 只表示制度要求，实际运动前还必须单独确认 `human_supervisor_present=true`。

## 13. 真机应按什么顺序推进

```text
1. 连接网线，只 ping 和读取状态
2. 核对 joint1...joint6 顺序、单位和反馈频率
3. 测试实体急停和软件 move_stop
4. 连接相机，只做图像与时间戳检查
5. 标定外部相机和腕部相机
6. 单独低速标定 4C2 开、闭、方向、宽度和反馈
7. π0.5 shadow mode：推理并记录，但不发布命令
8. 空工作区执行一个 0.01 rad 以内的已知关节小步
9. 空载低速执行短动作块，watchdog 随时停止
10. π0.5 空载闭环，夹爪保持张开
11. 抓取轻质测试物
12. 完整抓放并统计成功率
```

真实执行期间任何观测超过时限、出现 NaN、关节顺序不符、相机丢帧或人员离开，系统都必须停止发布并触发 `move_stop`。

## 14. 代码框架怎么读

建议按这个顺序阅读：

```text
openpi_extension/expert_episode.py
  数据帧的定义、保存和校验

openpi_extension/rm65_policy.py
  RM65 数据字段与 π0.5 通用字段之间的变换

openpi_extension/action_guard.py
  仿真动作限位和非有限值拒绝

openpi_extension/rm65_training_config.py
  模型、LoRA、数据和冻结策略

scripts/run_pick_place_baseline.py
  场景、IK、脚本专家、相机和 π0.5 闭环执行

scripts/train_rm65_pi05.py
  训练入口和 checkpoint 保存

scripts/serve_rm65_policy.py
  checkpoint 到 WebSocket 服务

scripts/run_pi05_rm65_closed_loop_suite.py
  多条件闭环评测、续跑和汇总

scripts/analyze_policy_start_ambiguity.py
  比较完整数据与 policy-window 的起始动作标签歧义

scripts/validate_rm65_evaluation_plan.py
  证明闭环用例是留出的范围内插值条件

openpi_extension/execution_gate.py
  仿真与真机 fail-closed 门禁

openpi_extension/real_robot_adapter.py
  ROS2 关节顺序、真机小步限制和夹爪标定映射

scripts/audit_real_robot_readiness.py
  只读检查网口、驱动、相机、夹爪标定和现场门禁

scripts/probe_rm65_joint_feedback.py
  只订阅 joint_states，验证六轴反馈契约
```

读每个文件时回答四个问题：输入是什么、输出是什么、单位是什么、失败时如何停止。能回答这四个问题，才算真正看懂机器人控制代码。

## 15. 你可以亲手完成的练习

1. 修改一条 prompt，同义表达保持任务不变，检查数据中的文字字段；
2. 把一个 source offset 改小，解释为什么 IK 仍可达；
3. 在 `action_guard.py` 测试 NaN、越界和过大步长；
4. 画出一个 episode 的六轴状态与动作曲线，找出 CLOSE、LIFT 和 OPEN；
5. 在离线评测报告中找安全层触发最多的阶段；
6. 把闭环每次执行动作数从 5 改为 3，预测响应速度与稳定性的变化，再用仿真验证；
7. 不接电机，写一个 ROS2 节点订阅 `/joint_states` 并按固定顺序打印六轴；
8. 完成 4C2 标定 JSON，但在测量前保持 `verified=false`。

完成这些练习后，你掌握的不只是“运行一个现成模型”，而是资产、运动学、物理接触、数据、VLA 微调、闭环评测、ROS2 接口和安全门之间的完整关系。
