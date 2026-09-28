# 从 Franka π0.5 到 RM65-B + 4C2：架构、迁移与代码零基础导读

> 适用范围：IsaacLab / Isaac Sim 仿真。本文不包含、也不授权真实 RM65 运动。
>
> 对应项目提交：`80f6af6743e9fb8a54fac8dd12ee7818828f37f7`
>
> 本地源码快照：`rm65_source_snapshot/`
>
> 逐行注释入口：`RM65_PI05_CODE_ATLAS_ZH/README.md`

## 0. 先说清楚现在到底完成了什么

从 Franka 参考实验迁移到 RM65-B + 4C2 的完整**仿真工程链路**已经建立：

1. RM65-B 与 4C2 模型能合并、导入 Isaac Sim，并作为一个 articulation 运行；
2. 脚本专家能在仿真中抓起方块、搬运、下降、松爪和稳定放置；
3. 已采集 45 条成功专家 episode，36 条训练、9 条验证；
4. 已转换为 OpenPI 可读的 LeRobot 数据格式并计算 RM65 自己的归一化统计；
5. 已从 π0.5 base checkpoint 做两次 30,000 step LoRA 微调；
6. 已建立 RM65 专用 policy transform、WebSocket 服务和 IsaacLab 闭环；
7. 已运行 20 条未见条件评测：v1 为 12/20，也就是 60%；v2 为 11/20，也就是 55%。

因此，**部署链路已经跑通，但“稳定成功”还没有完成**。项目设定的通过门槛是至少 20 条、成功率至少 80%。目前两个 checkpoint 都没有达到这个门槛。不能把“模型能输出动作、机械臂偶尔能完成任务”描述为“RM65 π0.5 已成功部署”。

你可以把现状表述为：

> 我完成了 π0.5 从 Franka/DROID 参考链路到 RM65-B+4C2 自定义仿真平台的资产、数据、微调、服务、闭环和评测迁移；两个 30k LoRA checkpoint 在 20 条未见条件中分别达到 60% 和 55%，由此发现数据分布和释放阶段仍需继续优化。

## 1. 整套系统用一句话怎么理解

两台“机器”在协作：

- **π0.5 模型进程**负责看图像、看关节状态、读文字，然后预测未来 10 个动作；
- **IsaacLab 仿真进程**负责执行其中前 5 个动作、模拟物理、拍新图，然后再次问 π0.5。

它们通过本机 8000 端口上的 WebSocket 传数据。

```text
外部相机图像 ─┐
腕部相机图像 ─┼─> RM65Inputs ─> 归一化 ─> π0.5 ─> 10×7 动作块
6个关节角 ────┤                                      │
1个夹爪值 ─────┤                                      v
文字指令 ──────┘                               RM65Outputs
                                                      │
                                                      v
                                               action_guard
                                                      │
                                                      v
Isaac Sim <─ 执行前5步 <─ WebSocket client <──────────┘
    │
    ├─ PhysX 更新机器人、夹爪、方块、碰撞和重力
    ├─ RTX/相机产生下一帧图像
    └─ 成功检测：抬起、到目标、松爪、稳定
```

这叫**闭环控制**：执行一小段后重新观察，再重新规划。它不同于一次预测完整轨迹后从头执行到尾的开环控制。

## 2. 先把容易混淆的名词讲明白

### 2.1 Isaac Sim

Isaac Sim 是 NVIDIA 的机器人仿真应用，负责：

- 物理：质量、重力、摩擦、碰撞、关节；
- 渲染：相机看到的 RGB 图像；
- USD 场景：机器人、方块、平台在世界中的表示。

它相当于“物理世界和摄像机”。

### 2.2 IsaacLab

IsaacLab 是构建在 Isaac Sim 上的开源 Python 框架。我们用它创建：

- `SimulationContext`：物理时钟；
- `Articulation`：RM65+4C2 多关节机器人；
- `RigidObject`：方块；
- `Camera`：外部相机和腕部相机；
- `ContactSensor`：手指与方块接触力；
- actuator：关节位置控制器。

它相当于“用 Python 组织仿真实验的工具箱”。

### 2.3 URDF 与 USD

URDF 是 XML 格式的机器人说明书，描述：

- `link`：刚体部件；
- `joint`：两个 link 怎么连接和运动；
- visual mesh：看起来什么样；
- collision mesh：物理碰撞形状；
- mass/inertia：质量和惯量；
- limit：关节上下限。

USD 是 Isaac Sim 原生场景格式。它能表达 URDF 的内容，还能保存 Isaac/PhysX 的物理属性和场景层级。

本项目先把两份 URDF 合并，再把合并结果导入 USD：

```text
RM65-B.urdf + 4C2.urdf
          │
          v
build_combined_urdf.py
          │
          v
rm65_4c2.urdf
          │
          v
import_combined_urdf.py + Isaac Sim URDF importer
          │
          v
rm65_4c2_wide_pads.usd
```

### 2.4 articulation

一个方块只有一个刚体，可以用 `RigidObject`。机械臂由多个 link 和 joint 连接，IsaacLab 把整个关节系统称为 `Articulation`。

### 2.5 IK

IK 是 inverse kinematics，中文叫逆运动学。

- 输入：希望末端到达的位置和姿态；
- 输出：六个 RM65 关节应该分别转多少角度。

本项目调用 NVIDIA Lula 求解 IK，没有自己从零实现数学求解器。我们自己写了：

- 怎样构造抓取/抬升/放置目标；
- 多个 IK seed 怎样搜索；
- 怎样选择离当前姿态最近的等价解；
- 怎样拒绝突然跳动的关节解。

### 2.6 expert、episode 与 dataset

**expert** 是能产生正确动作的老师。本项目的老师不是人遥操作，而是用 IK 和固定阶段写成的脚本专家。

**episode** 是从任务开始到结束的一整段轨迹。每一帧包含：

```text
观测：6个当前关节角 + 1个夹爪状态 + 外部图像 + 腕部图像 + 指令
动作：6个下一目标关节角 + 1个下一夹爪目标
附加证据：时间、物理步、阶段名、方块姿态
```

**dataset** 是很多 episode 按统一 schema 组织后的集合。OpenPI 训练使用 LeRobot 数据集格式。

### 2.7 transform

transform 不是神经网络主体。它是数据“翻译器”。

例如项目记录的是：

```python
observation/joint_position
observation/gripper_position
observation/external_image
observation/wrist_image
```

π0.5 内部需要的是：

```python
state
image["base_0_rgb"]
image["left_wrist_0_rgb"]
image["right_wrist_0_rgb"]
image_mask
```

`RM65Inputs` 负责做这次翻译。`RM65Outputs` 负责把模型动作裁成 RM65 使用的 7 维。

### 2.8 norm stats

不同关节的数值范围不相同。训练前会计算数据的统计量，把输入和动作缩放到模型更容易学习的范围。这个统计量叫 normalization statistics，简称 norm stats。

DROID/Franka 的统计量不能用于 RM65，因为两台机械臂的：

- 关节数量不同；
- 关节顺序不同；
- 零位不同；
- 运动范围不同；
- 夹爪语义不同；
- 动作分布不同。

### 2.9 LoRA

LoRA 是参数高效微调。不是把 π0.5 的所有权重都重新训练，而是在部分线性层旁边加入小的可训练矩阵。

本项目使用：

- `gemma_2b_lora`：语言/视觉主干相关的 LoRA 变体；
- `gemma_300m_lora`：动作专家相关的 LoRA 变体；
- 冻结图像编码器；
- batch size 1；
- 30,000 step。

这样才能在实验室 16 GB 显存上训练。

### 2.10 checkpoint

checkpoint 是某个训练步骤保存的模型参数和配套资产。它不是数据集，也不是 Python 源码。

本项目两个正式 checkpoint 都在训练第 `29999` 步的目录中。

## 3. Franka 阶段到底给 RM65 阶段留下了什么

Franka 阶段使用：

- sim-evals 的 DROID 环境；
- Franka 七轴机械臂和 Robotiq 夹爪；
- OpenPI 已训练好的 DROID joint-position checkpoint；
- DROID 自己的输入/输出 transform；
- `(15, 8)` 动作：15 个未来时间步，每步七个 Franka 关节目标加一个夹爪命令。

Franka 阶段**没有重新训练 π0.5**。主要验证了基础设施：

1. IsaacLab 能产生模型需要的图像和状态；
2. π0.5 server 能在 GPU 上加载；
3. WebSocket 能传 NumPy 图像和动作；
4. 模型和仿真能按“观察→推理→执行→再观察”闭环；
5. 可以对位置、指令、亮度等扰动做批量评测；
6. 可以留下视频、NPZ 和 JSON 证据。

这些可以复用：

```text
双进程结构
WebSocket client/server
动作块 + receding horizon
相机/状态/指令三类观测
批量评测与可恢复执行
机器可读证据
```

这些不能直接复用：

```text
Franka/Robotiq USD
DROID 环境中的关节索引
DROID 请求键和动作语义
DROID norm stats
DROID checkpoint 对 RM65 的直接控制
DROID 的成功条件和任务几何
```

## 4. 为什么不能只把 Franka 模型换成 RM65 模型

这是整个迁移最重要的理解。

| 契约 | Franka/DROID | RM65-B+4C2 | 为什么必须改 |
|---|---|---|---|
| 手臂自由度 | 7 | 6 | 动作维度和关节对应不同 |
| 夹爪 | Robotiq，二值/特定方向 | 4C2，多 mimic joint，归一化 0 开 1 闭 | 控制和反馈语义不同 |
| policy action | 15×8 | 10×7 | horizon、关节维数和夹爪定义不同 |
| 环境 | sim-evals DROID | 自建 RM65 方块搬运场景 | 任务对象和坐标不同 |
| 数据 | 大规模 DROID | 45 条 RM65 脚本专家 | 模型必须看到 RM65 分布 |
| transform | `DroidInputs/Outputs` | `RM65Inputs/Outputs` | 字段名、state、image slot 不同 |
| norm stats | DROID | RM65 train/validation | 数值尺度不同 |
| checkpoint | 官方 DROID | RM65 LoRA 30k | 旧 checkpoint 不认识 RM65 动作 |
| 成功判定 | DROID 场景对象关系 | 抬升、目标误差、释放、漂移 | 任务几何不同 |

假设 DROID 输出的第一个数字是 Franka `panda_joint1` 目标。把它直接当 RM65 `joint_1` 目标，数值虽然都是浮点数，但它们的训练含义、零位、连杆结构和影响完全不同。形状能对上不等于语义能对上。

所以迁移不是“改模型文件”，而是重建下面五层：

1. **资产层**：RM65+4C2 在物理世界中正确；
2. **控制层**：七维动作准确表示 6 轴+夹爪；
3. **数据层**：采集 RM65 自己的观测和动作；
4. **模型层**：用 RM65 数据、统计量和 transform 微调；
5. **评测层**：用 RM65 任务条件判断成败。

## 5. 哪些代码是下载的，哪些是我们写的

### 5.1 下载或外部提供

| 内容 | 来源 | 本项目怎样用 | 是否逐行注释 |
|---|---|---|---|
| OpenPI | Physical Intelligence，Apache-2.0；commit `15a9616a...` | π0.5 模型、transform 框架、JAX trainer、checkpoint loader、WebSocket server/client | 不逐行注释整个框架，只讲调用接口 |
| IsaacLab | NVIDIA/Isaac Lab，BSD-3-Clause；commit `37ddf626...` | Python 仿真框架、Articulation、Camera、ContactSensor | 不逐行注释整个框架 |
| Isaac Sim | NVIDIA 应用 | PhysX、RTX、USD、URDF importer | 不是本项目源码 |
| sim-evals | `arhanjain/sim-evals`，commit `3a6b0e8` | Franka/DROID 参考环境 | 只在 Franka 导读中解释关键环境代码 |
| DROID checkpoint | OpenPI 发布的预训练资产 | Franka 参考实验 | 不属于我们的训练结果 |
| π0.5 base checkpoint | `gs://openpi-assets/checkpoints/pi05_base/params` | RM65 LoRA 的初始化权重 | 二进制权重，不是要读的代码 |
| LeRobot | Hugging Face 生态中的机器人数据集库 | 数据集 schema、图像和 episode 存储 | 讲 API，不逐行注释库内部 |
| RM65-B URDF/mesh/description | 实验室已有 RM65 工程资产 | 手臂外观、关节、限位和 Lula 描述 | 模型数据，不是我们写的控制程序 |
| 4C2 URDF/mesh | 你提供的 Windows `D:\d\4C2` | 夹爪模型；原始树有 24 个文件和 SHA-256 清单 | 模型数据，不逐行注释 STL/URDF 全文 |
| Lula IK | NVIDIA Isaac Motion Generation | 从末端目标求六关节角 | 调用接口，不重写求解算法 |

### 5.2 我们为 RM65 迁移编写

| 程序 | 自己解决的问题 |
|---|---|
| `build_combined_urdf.py` | 合并两台设备的 URDF，处理名字、mesh、mimic、惯量和接触片 |
| `import_combined_urdf.py` | 调 Isaac importer 生成 USD，并记录关节和 articulation root |
| `run_pick_place_baseline.py` | 场景、IK、脚本专家、相机、数据采集、π0.5 闭环和证据 |
| `expert_episode.py` | 定义并严格校验中间 episode 格式 |
| `run_expert_collection_plan.py` | 按 45 条计划可恢复地采集专家 episode，并防止错误复用 |
| `convert_expert_episodes_to_lerobot.py` | 中间格式→OpenPI 可训练的 LeRobot 数据集 |
| `compute_rm65_norm_stats.py` | 对 transform 后的 state/actions 计算并保存归一化统计 |
| `rm65_policy.py` | RM65 字段↔π0.5 通用字段 |
| `grasp_geometry.py` | 从已校准姿态计算顶部抓取位置与旋转 |
| `rm65_training_config.py` | 数据 transform、动作 delta 语义、LoRA 和显存配置 |
| `train_rm65_pi05.py` | 调官方 trainer、管理 checkpoint、写训练证据 |
| `validate_rm65_checkpoint.py` | 用记录帧离线检查 checkpoint 加载、推理、shape 和 guard |
| `serve_rm65_policy.py` | 载入 RM65 checkpoint，启动 WebSocket policy server |
| `websocket_compat.py` | 兼容 Isaac Sim/OpenPI 自带的不同 websockets 版本 |
| `action_guard.py` | 在执行前限制关节范围、单步变化和夹爪范围 |
| `closed_loop_report.py` | 独立核对闭环报告是否真的满足成功门槛 |
| `check_closed_loop_task_report.py` | 把独立报告验证变成 Shell 可使用的退出码 |
| `run_pi05_rm65_closed_loop.sh` | 编排一次 server+IsaacLab 闭环 |
| `run_pi05_rm65_closed_loop_suite.py` | 运行 20 条可恢复评测并计算 80% gate |
| `run_rm65_post_training_pipeline.sh` | 串起训练后的离线、单 case、20-case、失败分析和最终清单 |

此外还有很多测试、诊断和结果分析代码。它们非常有用，但第一遍学习不需要逐行读。本文把会影响主数据流的 20 个程序、4659 行生产源码全部做了逐行学习副本。

## 6. 文件之间究竟怎样关联

### 6.1 构建机器人模型

```text
RM65-B.urdf ──────────┐
RM65 meshes ──────────┤
4C2.urdf ─────────────┼─> build_combined_urdf.py
4C2 meshes ───────────┘              │
                                     ├─> generated/*.urdf
                                     └─> results/*urdf_report.json
                                                   │
                                                   v
                                    import_combined_urdf.py
                                                   │
                                                   ├─> generated/*.usd
                                                   └─> results/*import_report.json
```

### 6.2 生成专家数据

```text
generated/rm65_4c2_wide_pads.usd
rm65_robot_description.yaml
rm65_expert_collection_plan_v1.json
                │
                v
run_expert_collection_plan.py
                │  每个 case 调一次
                v
run_pick_place_baseline.py --record-images
                │
                ├─ ExpertEpisodeCapture：从 Isaac 缓冲区同步取数据
                └─ EpisodeRecorder：检查并写盘
                           │
                           v
dataset_root/episode_xxxxxx/
  ├─ metadata.json
  ├─ episode.npz
  └─ images/{external,wrist}/*.png
```

### 6.3 数据变成训练输入

```text
45 个 portable episode
        │
        v
convert_expert_episodes_to_lerobot.py
        │
        ├─ local/rm65_sim_train       36 episodes
        └─ local/rm65_sim_validation   9 episodes
                    │
                    v
OpenPI dataset loader
                    │
                    v
RepackTransform
 image       ─────────> observation/external_image
 wrist_image ─────────> observation/wrist_image
 joints      ─────────> observation/joint_position
 gripper     ─────────> observation/gripper_position
 actions     ─────────> actions
 task/prompt ─────────> prompt
                    │
                    v
RM65Inputs / RM65Outputs
                    │
                    v
normalization + DeltaActions
                    │
                    v
π0.5 training batch
```

### 6.4 checkpoint 回到仿真闭环

```text
train_rm65_pi05.py
        │ 调用
        v
OpenPI scripts/train.py
        │
        v
outputs/openpi_checkpoints/.../29999
        │
        v
serve_rm65_policy.py ──监听 8000──┐
                                  │ WebSocket
run_pick_place_baseline.py <──────┘
        │
        v
task_report.json + episode.npz + images
        │
        v
closed_loop_report.py / suite summary
```

## 7. 按时间顺序，我们实际做了哪些迁移步骤

### 第一步：先把 Franka 参考链路跑通

目的不是证明 RM65 能用，而是确认：

- GPU/JAX/OpenPI 能加载；
- IsaacLab 能启动 DROID 场景；
- 两张相机图和关节状态能发到模型；
- `(15,8)` 动作能通过 WebSocket 返回；
- 动作块执行和重新规划能工作；
- 批量测试、日志和成功判定能工作。

### 第二步：定义 RM65 的接口合同

我们先规定“一个观测”和“一个动作”是什么意思：

```text
observation:
  external_rgb: 480×640×3 uint8，进模型前 resize/pad 为 224×224×3
  wrist_rgb:    480×640×3 uint8，进模型前 resize/pad 为 224×224×3
  joints:       (6,) rad，顺序 joint_1 ... joint_6
  gripper:      (1,)，clip(position_rad / 0.865, 0, 1)
  prompt:       string

action:
  (7,) = 6 个 absolute joint target rad + 1 个 normalized gripper target
```

这是后面所有代码共同遵守的“协议”。如果任何一个文件把第 7 维解释成别的含义，模型就会学错或执行错。

### 第三步：合并 RM65 与 4C2 模型

直接拼 XML 会出现名字冲突、相对 mesh 路径失效、mimic joint 在 PhysX 中不稳定、CAD 惯量太小等问题。

`build_combined_urdf.py` 做了：

1. 验证两份 XML 根节点都是 `<robot>`；
2. 把 mesh 文件名解析成真实绝对 URI；
3. 给夹爪所有 link/joint 加 `tool_` 前缀；
4. 更新 parent、child、mimic、transmission 中的引用；
5. 可选地提高过小质量/惯量；
6. 默认移除 mimic tag，改为运行时软件同步 follower joints；
7. 在指尖增加薄盒接触片，让 40 mm 方块有可靠双侧接触；
8. 添加固定关节 `rm65_to_4c2`，parent 为 `link_6`；
9. 输出合成 URDF 和 JSON 审计报告。

### 第四步：导入 USD 并验证 articulation

`import_combined_urdf.py` 在 Isaac Sim 进程中调用官方 URDF importer：

- 固定机器人底座；
- 合并固定关节；
- 导入惯量；
- 关闭自碰撞；
- 默认把 mimic followers 作为可由程序同步的自由度；
- 重新打开 USD，统计物理 joint 和 articulation root。

随后通过 smoke test、IK test、夹爪 aperture/contact test，逐步确认：

- 六个 RM65 关节顺序正确；
- 关节限位正确；
- link_6 位置能由 Lula FK/IK 对上；
- 4C2 增大 command 时会闭合；
- 指尖接触片能同时接触方块；
- 开启自然重力后模型不爆炸、不穿透。

### 第五步：写脚本专家

脚本专家用状态机把任务拆为：

```text
SOURCE_SETTLE
→ APPROACH_1...N
→ GRASP_HOLD
→ CLOSE
→ CLOSE_HOLD
→ LIFT
→ LIFT_HOLD
→ TRANSFER
→ PLACE_DESCENT_1...N
→ PLACE_HOLD
→ OPEN
→ RELEASE_SETTLE
→ RETREAT
→ FINAL_SETTLE
```

关键点不是阶段名称，而是每个阶段都有同步的观测和“下一步目标动作”。这才能成为模仿学习数据。

### 第六步：解决 IK 分支跳变

RM65 腕部可能存在多个达到同一末端姿态的等价关节解。例如 q4/q5/q6 可以通过腕部翻转或 `2π` 平移表示相同姿态。

如果从一个表示直接插值到另一个表示，末端几乎没变，关节却可能突然转几弧度。

因此我们写了：

- `closest_equivalent_rm65_solution()`：枚举已知等价表示；
- 用 FK 重新验证它们确实到达同一末端位姿；
- 选择相对上一命令最大单关节变化最小的候选；
- `require_continuous_joint_step()`：变化超过 0.75 rad 就拒绝；
- `solve_continuous_cartesian_path()`：沿多个 1 cm 左右路点逐点求解。

这类代码是从 Franka 换到另一台机械臂时经常必须重新写的“机器人几何适配层”。

### 第七步：记录 45 条专家轨迹

采集计划组合了：

- 5 个 transfer angle：0.6、0.7、0.8、0.9、1.0 rad；
- 3 个 source x 偏移；
- 3 个 source y 偏移；
- 5 种等价自然语言指令轮换。

总数 `5×3×3=45`，其中固定规则分出 36 条训练和 9 条验证。

脚本专家 45/45 成功，只说明脚本生成器和这些仿真条件稳定。它不说明 π0.5 也会 100% 成功。

### 第八步：转换 LeRobot 数据集

`convert_expert_episodes_to_lerobot.py` 只接受：

- `validate_episode()` 通过；
- 两路图像齐全；
- metadata 标记 `task_success=true`；
- state/action 均为 7 维；
- 全部 episode 帧率一致；
- 相机尺寸一致。

逐帧映射为：

```python
{
    "image": external_rgb,
    "wrist_image": wrist_rgb,
    "joints": state[:6],
    "gripper": state[6:7],
    "actions": action,
    "task": prompt,
}
```

### 第九步：创建 RM65 policy transform

`RM65Inputs` 做四件事：

1. 要求 `joints.shape == (6,)`；
2. 要求 `gripper.shape == (1,)`；
3. 将两张图放入 π0.5 三个 image slot，第三个 slot 用零图并把 mask 设为 false；
4. 拼出 `state.shape == (7,)`。

`RM65Outputs` 返回动作最后一维的前 7 个数。

训练和推理必须使用同一个 transform。否则训练时的第一个图像槽位与推理时不同，模型即使训练正常也会在闭环失败。

### 第十步：定义动作是 absolute 还是 delta

脚本专家保存的是绝对关节目标。OpenPI 配置中：

```python
delta_action_mask = transforms.make_bool_mask(6, -1)
```

意思是：

- 前 6 维关节在训练内部转成“相对当前 state 的变化”；
- 最后一维夹爪保持绝对目标；
- 推理输出时再把前 6 维还原为绝对关节目标。

这不是 NumPy mask，而是 OpenPI transform 使用的布尔维度规则。

### 第十一步：用 LoRA 微调 π0.5

`rm65_training_config.py` 创建模型和数据配置，`train_rm65_pi05.py` 动态载入 OpenPI 官方 `scripts/train.py`。

我们没有重写：

- loss；
- optimizer；
- JAX 梯度；
- checkpoint 序列化；
- π0.5 网络结构。

我们写的是“把 RM65 的数据和设置交给官方 trainer”的适配层。

显存优化包括：

- batch size 1；
- `max_token_len=64`；
- LoRA；
- 冻结图像编码器；
- `num_workers=0`；
- 关闭 W&B。

### 第十二步：启动 RM65 专用模型服务

`serve_rm65_policy.py`：

1. 用同一 `make_pi05_rm65_lora_config()` 重建配置；
2. 从 checkpoint 加载训练权重和 norm stats；
3. 创建 `policy`；
4. 启动 `WebsocketPolicyServer`；
5. 监听 `0.0.0.0:8000`。

它不连接机械臂。它只接受请求字典并返回动作字典。

### 第十三步：运行 receding-horizon 闭环

`run_pi05_closed_loop()` 每轮做：

```python
external_rgb, wrist_rgb = render_images()
current_arm = read_six_joints()
current_gripper = normalize_gripper()
observation = build_request(...)
raw_actions = client.infer(observation)["actions"]
safe_actions = guard_action_chunk(raw_actions, current_arm)
execute(safe_actions[:5])
check_success_candidate()
```

为什么模型输出 10 步，只执行 5 步？

- 10 步给模型表达短期计划；
- 只执行前 5 步能更快利用新图像修正误差；
- 全执行 10 步会降低反馈频率；
- 每步只执行 1 步则会增加推理频率和延迟影响。

这是工程折中，可以通过实验调整。

### 第十四步：防止一次“碰巧经过目标”被判成功

成功候选必须同时满足：

- 方块曾抬起超过 2 cm；
- 方块到目标三维距离小于 5 cm；
- 实际夹爪反馈低于开阈值；
- 最后执行的模型夹爪命令也低于开阈值；
- 连续 3 个 action chunk 都满足。

然后控制器锁住当前手臂姿态、完全打开夹爪，再等待 240 个物理步，验证方块没有明显漂移。

这个低层释放后置条件不是替模型选择何时释放；触发条件仍来自模型已经给出张开命令。它的作用是让最终稳定性验证可重复。

### 第十五步：运行 20 条未见条件

训练角度是 `0.6/0.7/0.8/0.9/1.0`，评测使用夹在它们中间的 `0.65/0.75/0.85/0.95`，同时使用新的 ±0.0075 m source 偏移和多种指令。

`run_pi05_rm65_closed_loop_suite.py`：

- 只启动一次 server，避免每个 case 重复加载模型；
- 每个 case 单独启动 Isaac Sim，避免仿真状态污染；
- 可复用 checkpoint、阈值完全一致的已有报告；
- 只有“没有产生有效报告”的基础设施故障才重试；
- 任务实际失败不会靠反复试到成功来掩盖；
- 最终要求 20 条且成功率 ≥ 0.8。

## 8. NumPy 零基础：读这些程序必须会的十件事

### 8.1 `np.ndarray`

NumPy 数组是同一类型数字组成的多维表。

```python
joints = np.array([0.1, -0.2, 0.3, 0.0, 0.5, 0.0])
```

这是形状 `(6,)` 的一维数组。括号中的逗号表示它是一个维度，不是 `(6, 1)` 列向量。

### 8.2 `shape`

```python
joints.shape == (6,)
actions.shape == (10, 7)
image.shape == (480, 640, 3)
```

- `(10, 7)`：10 个时间步，每步 7 个值；
- `(480, 640, 3)`：480 行、640 列、RGB 三通道。

### 8.3 `dtype`

- `float32`：模型和机器人状态常用；
- `float64`：IK 几何计算中保留更多精度；
- `uint8`：图像 0 到 255；
- `int64/int16`：索引和阶段编号；
- `bool`：mask。

### 8.4 切片

```python
action[:6]     # 第 0 到第 5 个值：六个关节
action[6]      # 第 7 个值：夹爪
actions[:, 6]  # 所有时间步的夹爪列
state[6:7]     # 保留一维形状 (1,)，不是标量
```

### 8.5 `np.asarray`

把列表、Torch 转出的值或已有数组统一成 NumPy 数组。已有数组时通常不复制。

### 8.6 `np.concatenate`

```python
state = np.concatenate([joints, gripper])
```

`(6,) + (1,) -> (7,)`。

### 8.7 `np.stack`

```python
all_states = np.stack(list_of_states)
```

如果列表里有 100 个 `(7,)`，结果是 `(100,7)`。

### 8.8 `np.clip`

```python
gripper = np.clip(value, 0.0, 1.0)
```

小于 0 变成 0，大于 1 变成 1，中间值不变。

### 8.9 `np.isfinite`

检查有没有 `NaN` 或无穷。机器人动作中出现非有限数必须立即拒绝，否则物理仿真可能发散。

### 8.10 `np.linalg.norm`

```python
distance = np.linalg.norm(actual_xyz - target_xyz)
```

先得到位置误差向量，再计算它的欧氏长度，也就是直线距离。

## 9. 二十个核心程序应该按什么顺序读

不要按文件大小读。按数据经过系统的顺序读：

1. `rm65_policy.py`：73 行，先建立模型输入输出概念；
2. `expert_episode.py`：理解一帧训练数据；
3. `run_expert_collection_plan.py`：理解 45 条数据怎样可恢复采集；
4. `convert_expert_episodes_to_lerobot.py`：理解数据如何进训练库；
5. `compute_rm65_norm_stats.py`：理解统计量必须经过相同 transform；
6. `rm65_training_config.py`：理解 transform、delta、LoRA；
7. `train_rm65_pi05.py`：理解我们怎样调用官方 trainer；
8. `validate_rm65_checkpoint.py`：理解训练后第一道离线检查；
9. `serve_rm65_policy.py`：理解 checkpoint 怎样变成服务；
10. `websocket_compat.py`：理解早期 ping timeout 怎样工程化修复；
11. `action_guard.py`：理解执行前安全裁剪；
12. `run_pick_place_baseline.py` 第 602-881 行：理解闭环；
13. 同一主程序第 925-1576 行：理解场景和分支；
14. 同一主程序其余部分：补 IK、脚本专家、接触和报告；
15. `grasp_geometry.py`：理解顶部抓取姿态怎样由局部/世界坐标构造；
16. `run_pi05_rm65_closed_loop.sh`：理解两个进程如何启动；
17. `run_pi05_rm65_closed_loop_suite.py`：理解批量评测；
18. `closed_loop_report.py` 与 `check_closed_loop_task_report.py`：理解独立成功验收；
19. `run_rm65_post_training_pipeline.sh`：理解训练结束到完整评测的总编排；
20. 最后读 `build_combined_urdf.py` 和 `import_combined_urdf.py` 的全部细节。

资产脚本放到最后精读，是因为它们在时间上最先运行，但对理解模型闭环不是最短路径。

## 10. 最重要的几个程序，应该抓住哪些主线

### 10.1 `rm65_policy.py`

你要能回答：

- 为什么 joints 必须是 `(6,)`？
- 为什么 gripper 标量要变成 `(1,)`？
- 为什么第三张 image 是零图，但 mask 是 false？
- 为什么训练数据里有 actions 时也要经过相同 transform？
- 为什么输出只取 `[..., :7]`？

### 10.2 `expert_episode.py`

你要能回答：

- 为什么“当前 observation”和“同索引 action”必须同步？
- 为什么时间和 sim_step 必须严格递增？
- 为什么两路图像必须同时有或同时没有？
- `npz` 保存数值、PNG 保存图像、JSON 保存语义，各自有什么好处？
- 为什么保存之后还要重新读取验证？

### 10.3 `run_pick_place_baseline.py`

这个文件大，是因为它同时有两种模式：

```text
共同部分：建场景、机器人、方块、相机、初始状态
                     │
       ┌─────────────┴──────────────┐
       v                            v
脚本专家模式                   π0.5 闭环模式
IK 路点和阶段状态机             图像+状态→server
生成训练数据                    动作块→guard→执行
```

第一遍只追踪对象：

- `sim`：世界时间；
- `robot`：机器人；
- `cube`：方块；
- `state`：关节控制目标；
- `episode_capture`：采样桥；
- `client`：π0.5 WebSocket 客户端；
- `raw_actions/safe_actions`：模型动作和安全动作；
- `report`：证据。

### 10.4 `rm65_training_config.py`

它回答三个问题：

1. 磁盘数据的键怎样改名？`RepackTransform`；
2. RM65 字段怎样变为 π0.5 字段？`RM65Inputs/Outputs`；
3. 哪些动作维度训练为 delta？前六维；夹爪保持 absolute。

### 10.5 `run_pi05_rm65_closed_loop_suite.py`

它不做机器人控制，而是做实验管理：

- 模型服务生命周期；
- case 遍历；
- timeout；
- 日志隔离；
- resume；
- 失败与基础设施错误区分；
- 汇总 gate。

## 11. 重要外部代码，你至少要知道它们怎样被调用

### OpenPI `Policy.infer`

大致内部流程是：

```text
原始 request
→ input transforms
→ normalization
→ 图像 resize/pad、tokenize prompt
→ model.sample_actions
→ unnormalize
→ output transforms
→ response["actions"]
```

我们的代码从 `client.infer()` 进入，不需要自己调用每一个内部步骤。

### OpenPI `WebsocketPolicyServer`

它负责：

- 接受 msgpack 编码的 NumPy 数据；
- 调 `policy.infer()`；
- 把动作和可选 metadata 回传。

它不懂 Isaac、RM65、碰撞或成功条件。

### OpenPI 官方 `scripts/train.py`

它负责：

- 创建数据 loader；
- 初始化 JAX/Flax 模型；
- 加载 base checkpoint；
- 前向、loss、反向、optimizer；
- 定期日志和 checkpoint。

我们的 `train_rm65_pi05.py` 只给它一份完整 `TrainConfig`。

### IsaacLab `Articulation`

它同时暴露：

- `robot.data.joint_pos`：观测到的实际关节角；
- `set_joint_position_target()`：设置控制器目标；
- `write_data_to_sim()`：提交命令；
- `update()`：读回物理结果。

注意“目标”和“实际”不是同一个数组。受惯性、控制器和碰撞影响，实际关节不会瞬间等于目标。

### Lula `compute_inverse_kinematics`

输入末端 link 名、目标位置、目标四元数和 warm start，返回关节解以及 success 标志。Lula 给出数学解之后，我们仍要检查：

- 是否落在 RM65 限位；
- 是否选择了连续分支；
- 是否与上一步差太大；
- 沿路径是否每个路点都可达。

## 12. 为什么第一次训练成功，闭环却只有 60%

“训练完成”只表示优化器跑完并保存 checkpoint，不表示机器人任务成功。

可能的误差来源包括：

1. 45 条数据覆盖仍窄；
2. 脚本专家轨迹高度确定，策略对略不同视觉/状态的恢复能力不足；
3. episode 中静止 hold 帧很多，模型容易学成“保持不动”；
4. 夹爪打开阈值、实际动态和模型连续输出之间有偏差；
5. 物体靠近平台边缘时，小位置误差会放大成掉落；
6. 模型输出关节目标经过 0.05 rad 单步裁剪后，时序与训练动作不同；
7. 执行 5/10 action chunk 的控制频率可能不是最佳；
8. 训练/评测初始条件有分布差异。

v2 压缩静止阶段后只有 55%，说明“删除静止标签”并没有单独解决问题。它是一次有证据的负结果：策略还需要更好的失败恢复数据、相机/状态覆盖和闭环控制调参。

## 13. 如果你以后要迁移到另一台机械臂，通用方法是什么

按下面顺序，而不是先改模型输出：

1. 列出新机器人的关节、限位、零位、末端 link、夹爪语义；
2. 在 Isaac 中只做 articulation smoke test；
3. 验证 FK/IK 与世界坐标/基座坐标；
4. 验证夹爪开闭、接触、重力和物体尺寸；
5. 写明确的 observation/action contract；
6. 先做 deterministic/scripted expert；
7. 为 episode 写独立 validator；
8. 收集覆盖任务条件的数据并分 train/validation；
9. 写新 robot transform；
10. 计算新 norm stats；
11. 微调并做离线 batch 检查；
12. 建立 action guard；
13. 单条闭环；
14. 未见条件 suite；
15. 分析失败阶段，再决定补数据还是改控制器。

每一步都有可单独验证的输出。这样失败时你知道是哪一层，而不是看到“机械臂没抓到”后同时怀疑模型、相机、坐标、夹爪和网络。

## 14. 你应该能对别人完整讲出的版本

> 我先用 OpenPI 官方 π0.5 DROID joint-position checkpoint 和 sim-evals，在 IsaacLab 中完成 Franka+Robotiq 的视觉语言闭环，验证模型服务、WebSocket、相机观测、动作块执行和批量评测基础设施。迁移 RM65 时我没有直接复用 DROID 动作，因为 Franka 是七轴，而 RM65 是六轴，关节语义、夹爪、统计量和训练分布都不同。我把实验室 RM65 URDF 和用户提供的 4C2 URDF 合并，在 link_6 添加固定安装关系，修正 mesh、mimic joint、惯量和指尖碰撞片，再导入 USD 并验证 articulation、IK、夹爪接触和自然重力。
>
> 然后我用 Lula IK 和阶段状态机写了脚本专家，定义观测为两路 RGB、六个关节、一个归一化夹爪和语言指令，动作为六个绝对关节目标加一个夹爪目标。采集 45 条成功 episode，分成 36 条训练和 9 条验证，转换为 LeRobot 格式，计算 RM65 的 norm stats。接着编写 RM65Inputs/Outputs，将自定义字段翻译为 π0.5 通用字段，并配置前六维 delta action、夹爪 absolute action、LoRA、冻结图像编码器和 30k step，在 16 GB GPU 上从 π0.5 base checkpoint 微调。
>
> 推理时 checkpoint 由 OpenPI WebSocket server 加载，IsaacLab client 每轮发送新图像、状态和指令，模型返回 10×7 动作块。动作先经过关节限位、单步 0.05 rad 和夹爪范围裁剪，再执行前 5 步并重新观察。成功必须满足抬升、目标误差、模型选择松爪以及释放后稳定。最后用 20 个未见角度、位置和语言条件批量评测；v1 为 60%，v2 为 55%，均未达到 80% gate，所以仿真链路已打通，但鲁棒性优化仍未完成。

## 15. 这套逐行注释怎么使用

当前逐行注释已升级为 v2“项目语义版”。例如它不会只把
`actions = np.asarray(data["actions"])` 解释成“给变量赋值”，而会逐层说明：

- `data` 是 OpenPI transform 收到的一条 RM65 样本；
- `data["actions"]` 是未来动作块，每步为六个 RM65 关节目标加一个 4C2 夹爪目标；
- `np.asarray` 把列表或其他数组对象统一成 NumPy `ndarray`；
- 完整一行把动作块取出并标准化，随后检查最后一维是否为 7，再进入 delta action、归一化和训练。

其余程序也按“项目对象—本行运算—后续去向”解释。单独的 `)`、`}` 等闭合行没有新的业务数据，注释会明确它闭合的是前面的多行调用或容器。

每份逐行注释文件都包含：

- 原仓库路径；
- 源码 SHA-256；
- 程序职责；
- 建议阅读顺序；
- 功能块行号地图；
- 函数/类行号索引；
- 每一行原始代码；
- 每一行之前的中文解释。

它们是学习副本，不参与执行。真正运行的是实验室电脑仓库里的原始源码。这样可以放心添加大量教学说明，而不会因为注释位置、Markdown 或编码问题破坏生产程序。

阅读一个文件时采用四轮法：

1. 只看功能块地图，回答“输入、输出、作用”；
2. 只看函数名和主流程，忽略公式；
3. 逐行读一个函数，并手写变量形状；
4. 关掉注释，自己复述并修改一个小参数。

如果第三轮读到一个数组，请在纸上写：

```text
变量名：
shape：
dtype：
单位：
每一维/每一列语义：
来源：
去向：
```

只要能持续回答这七个问题，你就会逐渐具备迁移和排错能力，而不只是记住命令。

## 16. 当前仍未完成的技术工作

仿真方向的下一步应围绕失败证据展开：

1. 按失败阶段拆分 v1/v2 的 9/8 条失败；
2. 给失败附近初始状态补 recovery demonstration；
3. 平衡接近、闭合、抬升、搬运、放置、释放各阶段样本；
4. 对比 action execution 数量 1/3/5 和单步裁剪 0.03/0.05 rad；
5. 加入相机轻微位姿、光照和物体位置随机化；
6. 新建不与训练网格重合的开发集，避免反复针对正式评测调参；
7. 训练新 checkpoint 后重新跑完整 20 条；
8. 只有成功率达到门槛，才可以称为“通过仿真部署 gate”。

真机接口、网络协议、急停、速度限制和空场测试不在本文当前范围，也不会从这套仿真代码自动获得。
