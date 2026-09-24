# RM65-B + 4C2 + π0.5 手把手复现与理解教程

更新时间：2026-09-24  
适用对象：有 Python 基础、第一次系统做具身智能项目的人  
当前执行边界：只做 IsaacLab/Isaac Sim 仿真，不连接或控制真实机械臂

## 1. 这份教程怎么使用

这不是一组“复制后看到机械臂动起来”的命令。你的目标是每一步都能回答：

1. 输入是什么？
2. 输出是什么？
3. 数据的 shape、单位和坐标系是什么？
4. 成功由哪份机器可读证据证明？
5. 失败时应该先检查哪一层？
6. 这一步能证明什么，不能证明什么？

建议每次只完成一个小节。你亲自在终端输入命令，把输出写进学习日志；我根据输出解释，再进入下一步。不要跳过失败结果，因为排错过程正是这个项目最有价值的能力。

所有正式操作都在新实验室电脑执行：

```text
主机：chengyu-Z790-AORUS-ELITE-AX
系统：Ubuntu 24.04
GPU：RTX 4080 SUPER 16 GB
项目仓库：~/robot-learning/rm-ik-rl
RM65 项目：~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
OpenPI：~/robot-learning/openpi
IsaacLab：~/robot-learning/IsaacLab
Isaac Sim：~/isaac-sim-5.1.0
```

密码、令牌和 SSH 私钥不得写入代码、文档或 Git。

## 2. 先看清整个系统

```text
文字指令 + 外部相机 + 腕部相机 + 6 轴状态 + 夹爪状态
                         │
                         ▼
                  RM65Inputs transform
                         │
                         ▼
              π0.5 预测未来 10×7 动作块
                         │
                         ▼
                  RM65Outputs transform
                         │
                         ▼
        有限值检查、关节限位、最大步长、夹爪范围
                         │
                         ▼
          IsaacLab 只执行前 5 步，再重新观察和推理
                         │
                         ▼
       物体抬升、搬运、落点、释放、稳定性任务报告
```

### 2.1 核心概念

| 名称 | 本项目中的作用 | 常用场景 |
|---|---|---|
| π0.5 | 视觉-语言-动作策略，相当于控制“大脑” | 根据图像、状态和文字预测机器人动作 |
| Isaac Sim | USD、渲染、PhysX 物理和传感器运行时 | 搭场景、碰撞、相机、物理仿真 |
| IsaacLab | Isaac Sim 上的机器人学习框架 | 环境、批量实验、控制与评测 |
| URDF | link、joint、惯量、碰撞与网格结构说明 | ROS、运动学、机器人资产交换 |
| USD | Isaac 使用的场景与资产格式 | 保存仿真材质、物理属性和场景层 |
| Lula IK | 从末端位姿求六轴关节角 | 脚本专家、可达性和轨迹生成 |
| LeRobot | 机器人轨迹数据格式 | 组织视频、状态、动作和 episode |
| LoRA | 只训练少量适配参数 | 显存有限时微调大模型 |
| WebSocket | 仿真进程与模型进程通信 | GPU 模型服务、跨环境推理 |
| receding horizon | 每次预测一段，只执行前几步再重规划 | 用新观测修正累积误差 |
| Docker | 隔离依赖和运行环境 | 官方 LIBERO/OpenPI 示例和可复现环境 |

### 2.2 三种成功必须分开

| 类型 | 控制者 | 当前结果 | 能否证明 π0.5 已部署成功 |
|---|---|---:|---|
| 脚本专家仿真 | IK + 状态机 | 45/45 数据 episode 成功 | 不能 |
| π0.5 RM65 仿真闭环 v1 | 微调模型 | 12/20，60% | 证明部分成功，未过门禁 |
| π0.5 RM65 仿真闭环 v2 | policy-window 微调模型 | 11/20，55% | 未优于 v1，未过门禁 |
| 真机闭环 | π0.5 + 真机安全层 | 未执行 | 尚无结果 |

## 3. 第 0 课：确认你在正确电脑、正确仓库

### 目标

学会在运行任何实验前检查主机、路径、Git、GPU、内存和磁盘。这个习惯能避免在错误电脑、错误分支或错误环境中运行数小时。

### 你亲手执行

```bash
hostname
cat /etc/os-release | head
nvidia-smi
free -h
df -h ~

cd ~/robot-learning/rm-ik-rl
git branch --show-current
git rev-parse --short HEAD
git status --short
```

### 当前预期

```text
hostname：chengyu-Z790-AORUS-ELITE-AX
系统：Ubuntu 24.04
GPU：RTX 4080 SUPER
分支：main
当前已验证提交：2130709 或其后续提交
```

`git status --short` 可能显示历史遗留的未跟踪文件。不要使用 `git add .`，只添加自己确认过的文件。

### 常见问题

- `nvidia-smi` 不存在：驱动未安装或 PATH 错误。
- 显存被占满：先用 `nvidia-smi` 看 PID，不要盲目重启。
- Git 出现大量意外修改：停止实验，先确认是不是进入了错误仓库。
- SSH 可达但 NoMachine 不可用：SSH 是命令行链路，NoMachine 是图形桌面链路，它们相互独立。

### 常用场景

训练、仿真、服务器部署、远程排障之前都应执行这组 preflight。

## 4. 第 1 课：先验证官方链路，再迁移机器人

### 目标

把“模型与 CUDA 问题”和“RM65 资产问题”分开。若官方 Franka 场景也失败，先查 OpenPI、checkpoint、CUDA、相机和 WebSocket；若 Franka 成功而 RM65 失败，再查 RM65 关节与动作语义。

### 我们实际完成了什么

- LIBERO 示例观测能让 π0.5 返回有限动作张量。
- 第一次 JAX 编译曾超过 WebSocket keepalive 时间，出现 `ping timeout`；关闭本地 keepalive 并预热后，稳态推理约 0.32 秒。
- Franka 参考项目的严格基线为 9/9；鲁棒性矩阵为 17/18，总计 26/27。
- 这证明新电脑可以同时运行 π0.5 服务、双相机观测和 IsaacLab 闭环，但不证明 Franka checkpoint 可以控制 RM65。

### 你应该怎么复现

先读：

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
less docs/FRANKA_STAGE_REPORT_ZH.md
```

然后只运行该项目报告中已经记录的 smoke test 和单场景脚本。不要把 Franka 的 `15×8` 动作直接发送给 6 轴 RM65。

### 这一步的意义

这是软件工程中的“已知良好基线”。它让排错从“所有东西都可能错”缩小为“RM65 迁移层可能错”。

## 5. 第 2 课：把 RM65 与 4C2 组合成机器人资产

### 目标

把 RM65 URDF 和用户提供的 4C2 URDF/STL 合成一棵无重名的机器人树，再导入 USD。

### 你亲手执行

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab

python3 scripts/build_combined_urdf.py \
  --rm65-urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --rm65-mesh-dir ~/robot-learning/rm-ik-rl/assets/RM65-B/meshes \
  --gripper-urdf external/4C2/urdf/4C2.urdf \
  --gripper-mesh-dir external/4C2/meshes \
  --gripper-root-link base_link \
  --gripper-name-prefix tool_ \
  --output generated/learning_rm65_4c2.urdf \
  --report outputs/learning_combined_urdf_report.json

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/import_combined_urdf.py \
  --urdf generated/learning_rm65_4c2.urdf \
  --usd generated/learning_rm65_4c2.usd \
  --report outputs/learning_import_report.json \
  --headless
```

使用 `learning_` 前缀，避免覆盖正式资产。

### 你应检查的证据

```bash
python3 -m json.tool outputs/learning_combined_urdf_report.json | less
python3 -m json.tool outputs/learning_import_report.json | less
```

当前正式资产应包含 16 个 link、15 个 URDF joint、12 个可动 joint。12 个自由度由 6 个 RM65 关节、1 个夹爪主关节和 5 个软件耦合随动关节组成，并不代表有 12 个电机。

### 常见问题与解决思路

- RM65 和夹爪都有 `base_link`：给夹爪所有 link/joint 加 `tool_` 前缀。
- mesh 找不到：URDF 中的 package URI 必须解析成正确路径。
- 模型能显示但不能控制：显示成功不等于 articulation、drive、limit 和 collision 正确。
- 安装方向不对：修改固定关节变换，但最终要以真实法兰测量为准。

### 常用场景

换夹爪、换相机支架、把多个机器人部件组合成一个可控制资产时都会用到。

## 6. 第 3 课：验证关节、运动学和夹爪物理

### 目标

证明组合资产不是“只有外观”，而是关节顺序、限位、IK、开合方向和碰撞都正确。

### 关节与 IK

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/learning_articulation_smoke.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --disable-moving-gripper-gravity \
  --headless

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_combined_ik.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/learning_combined_ik.json
```

正式结果中 Lula 位置误差约 `1.03e-6 m`、旋转误差约 `9.18e-4 rad`；12 个可达目标回归为 12/12。

### 夹爪方向和开口

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_gripper_aperture.py \
  --usd generated/rm65_4c2_wide_pads.usd \
  --output outputs/learning_gripper_aperture.json \
  --headless
```

本项目约定：归一化 `0=张开`、`1=闭合`。几何校准显示归一化 0.20 时接触垫净空约 52.6 mm，能让 40 mm 方块通过并保留 5 mm 以上余量。

### 我们遇到的关键问题

- 原始凸包的接触主要来自夹爪基座，不是双侧指面。
- 加入独立薄碰撞垫后才形成可测量的双侧接触。
- NumPy `float64` 命令写入 PyTorch `float32` 张量会报错；写入前要匹配 device 与 dtype。
- 仿真碰撞垫是工程代理，不能冒充真实夹爪尺寸。

### 常用场景

任何涉及抓取、接触、末端工具或运动学求解的仿真项目都需要这一层验证。

## 7. 第 4 课：先让脚本专家完成任务

### 目标

用可解释的 IK 和状态机证明任务在当前场景中物理可完成，并产生训练示教。

### 状态机

```text
SOURCE_SETTLE → APPROACH → CLOSE → LIFT → TRANSFER
→ PLACE_DESCENT → OPEN → RETREAT → FINAL_SETTLE
```

### 运行小规模全重力套件

```bash
bash scripts/run_top_down_full_gravity_suite.sh
```

正式三角度结果为 3/3。注意这仍是脚本专家，且使用假定的 0.65 m 安装高度和未按实物标定的宽碰撞垫。

### 我们解决过的问题

| 问题 | 根因 | 解决方法 |
|---|---|---|
| 顶部抓取不可达 | 机器人安装面和世界桌面高度混淆 | 加 `robot_base_z_m=0.65` 并显式变换坐标系 |
| 下降途中腕部跳变 | IK 切换到等价但遥远的关节分支 | 用上一解 warm start，约束连续路径 |
| 边界样本无 IK | 固定预抓取距离越出工作空间 | 从安全距离向内搜索可解路点 |
| 释放后漂移 22.65 mm | 放置跟踪时间不足 | 每个约 1 cm 路点增加到 180 物理步 |

### 这一步的意义

专家成功证明“任务和场景可解”，并提供模型学习的目标行为。专家成功绝不能写成 π0.5 成功。

## 8. 第 5 课：采集可恢复的专家数据集

### 目标

用位置、转运角和同义指令的组合覆盖任务，而不是只录一条轨迹。

### 先小规模体验

```bash
python3 scripts/run_expert_collection_plan.py \
  --plan config/rm65_expert_collection_plan_v1.json \
  --dataset-root datasets/rm65_scripted_learning \
  --split train \
  --max-cases 1
```

确认一个 episode 后，再决定是否完整采集。正式数据集已经完成，不要覆盖它：

```text
datasets/rm65_scripted_v1
45/45 episode 通过
36 train，9 validation
20,175 帧
```

### 一帧数据

```text
observation_state：6 个实际关节角 + 1 个夹爪状态
external_image：外部 RGB
wrist_image：腕部 RGB
prompt：任务文字
action：6 个绝对关节目标 + 1 个夹爪目标
phase：脚本专家阶段，仅用于分析
cube_pose：任务验证信息，不作为策略输入
```

物理频率 240 Hz，每 12 步采样一次，数据频率为 20 Hz。必须先保存当前观测，再保存即将执行的动作，避免错一帧。

### 常用场景

示教学习、行为克隆、VLA 微调、失败回放和数据质量审计。

## 9. 第 6 课：转换 LeRobot 数据并计算归一化统计

### 目标

把项目 episode 转成 OpenPI 的数据契约，并只用训练集计算 state/action 统计。

### 练习命令

```bash
python3 scripts/convert_expert_episodes_to_lerobot.py \
  datasets/rm65_scripted_v1 \
  --repo-id local/rm65_sim_learning

python3 scripts/compute_rm65_norm_stats.py \
  --repo-id local/rm65_sim_learning \
  --output outputs/learning_norm_stats_report.json
```

不要在不理解 `--overwrite` 的情况下覆盖正式数据。正式 repo id 是：

```text
v1：local/rm65_sim_train / local/rm65_sim_validation
v2：local/rm65_sim_policy_train / local/rm65_sim_policy_validation
```

### 为什么 repo id 很重要

OpenPI 根据 repo id 查找归一化统计。训练与推理 repo id 不一致时，模型可能仍能运行，却会把动作反归一化到错误尺度，这是很隐蔽的错误。

### policy-window v2 的目的

v1 开头有大量静止帧，只有约 31.6% 的起始 10 步窗口包含运动。v2 缩短等待段，使保留的 90/90 个起始窗口都包含开始运动。它是一次有证据的假设实验；最终闭环从 60% 降到 55%，说明这个改动单独使用没有提升总体任务成功率。

## 10. 第 7 课：在 16 GB 显存上微调 π0.5

### 目标

理解 LoRA、显存预算、训练 smoke test、checkpoint 和 loss 证据。

### 当前配置

```text
基础模型：pi05_base
动作 horizon：10
模型内部动作宽度：32，RM65 有效语义为前 7 维
PaliGemma LoRA rank：16
action expert LoRA rank：32
batch size：1
最大 token：64
冻结 SigLIP 视觉编码器
```

默认配置曾需要额外约 5.36 GiB，导致 16 GB GPU OOM。缩短 token 并冻结视觉塔后，估计训练显存约 7.35 GiB。

### 正确的学习顺序

```bash
# 1. 只做前置检查，不训练
bash scripts/train_rm65_pi05_policy_window.sh preflight

# 2. 阅读配置
less openpi_extension/rm65_training_config.py
less scripts/train_rm65_pi05.py

# 3. 真正重训前先确认没有别的训练进程
pgrep -af train_rm65_pi05.py || true
nvidia-smi
```

正式 v1、v2 都训练了 30,000 步。v2 训练日志有 300 个记录点，loss 从 0.2278 降至 0.0022，数值全部有限。loss 下降只代表优化正常，不代表任务成功。

### 常用场景

低显存微调、检查 OOM、比较不同数据视图、恢复中断训练。

## 11. 第 8 课：理解三层验证

### 11.1 checkpoint 单帧验证

检查权重能加载、输出 `(10,7)`、数值有限和动作安全层可处理。它不运行完整任务。

### 11.2 validation 离线误差

比较模型动作与未参与训练的专家动作。v1 六轴动作 MAE 约 0.00470 rad；v2 policy-window 六轴 horizon MAE 约 0.00534 rad。低 MAE 仍不能替代闭环。

### 11.3 IsaacLab 闭环评测

```text
观察 → 推理 10 步 → 安全层 → 执行前 5 步 → 重新观察
```

20 个评测条件使用训练范围内的新角度 `0.65/0.75/0.85/0.95`、新位置组合和多种同义指令。通过门槛：至少 20 个有效 episode 且成功率至少 80%。

正式结果：

```text
v1：12/20 = 60%，FAIL
v2：11/20 = 55%，FAIL
v2 相对 v1：4 改善、5 退步、7 稳定成功、4 稳定失败
```

运行单例或全套前必须先解决第 12 节的确定性采样问题。

## 12. 当前正在解决的问题：可复现的 π0.5 采样

π0.5 的 flow-matching 推理会从随机高斯噪声开始。OpenPI 默认在服务器内维护一个不断推进的 JAX RNG。如果评测从中途续跑，已经完成的案例被跳过，新服务器却从 RNG 0 重新开始，后续案例会拿到与原完整运行不同的噪声。

我们通过同一 checkpoint 的复测发现明显翻转，甚至某案例最终误差从 5.7 cm 变成 38.8 m。已完成 16 个开发复测，8/16 通过；这个结果只用于暴露问题，不能作为新的正式模型成功率。

正确修复目标是：

1. 每个 case 有固定 `policy_noise_seed`；
2. 每个 action chunk 使用 `case_seed + chunk_index`；
3. 客户端把 seed 发给策略服务；
4. 服务显式生成 `10×32 float32` 高斯噪声并传给 `Policy.infer(noise=...)`；
5. 报告记录 seed 和 noise SHA-256；
6. 单例运行、完整运行和断点续跑的相同 case 必须得到相同噪声哈希与动作。

截至本文生成时，这个修复只有 Windows 临时草稿，尚未同步、测试或提交，不能写成已完成。

## 13. 安全层和门禁

`action_guard.py` 检查：

- NaN/Inf；
- 六轴关节限位与余量；
- 单步最大关节变化 0.05 rad；
- 夹爪范围 `[0,1]`。

仿真报告必须明确：

```json
{
  "simulation_only": true,
  "real_robot_command_sent": false
}
```

当前机器可读进度中：脚本专家、数据集、微调和离线验证已完成；π0.5 仿真闭环未过 80%；真机阶段按用户要求延期。因此不能执行真机动作。

## 14. 如何读代码并开始自己修改

按下面顺序，每个文件只回答输入、输出、单位、失败行为：

```text
openpi_extension/expert_episode.py       数据帧与 episode
openpi_extension/rm65_policy.py          RM65 ↔ π0.5 字段变换
openpi_extension/action_guard.py         动作安全层
openpi_extension/rm65_training_config.py 训练配置
scripts/run_pick_place_baseline.py        场景、专家与模型闭环
scripts/convert_expert_episodes_to_lerobot.py
scripts/train_rm65_pi05.py
scripts/serve_rm65_policy.py
scripts/run_pi05_rm65_closed_loop_suite.py
scripts/analyze_rm65_closed_loop_failures.py
```

推荐练习：

1. 用 `rg -n "policy_execute_actions_per_chunk"` 找到动作块执行数量；
2. 解释从 5 改成 3 对响应速度、推理频率和稳定性的影响；
3. 在单元测试中加入 NaN 动作，观察 fail-closed；
4. 画一条 episode 的六轴 state/action 曲线并标出 CLOSE、LIFT、OPEN；
5. 为确定性 seed 先写测试，再修改服务器和运行器。

## 15. 你何时算真正掌握了这一阶段

你能独立完成以下任务时，才算能力已经迁移给你：

- 从 URDF 解释 link、joint、limit、mimic 和固定安装关节；
- 通过报告证明 USD articulation 与 IK 正确；
- 分清脚本专家、离线模型和 π0.5 闭环结果；
- 解释 7 维真实动作为什么在模型内部填充到 32 维；
- 从一个 episode 追踪图像、状态、动作和时间对齐；
- 解释 norm stats 与 repo id 的关系；
- 独立运行 preflight、单帧验证、离线验证和闭环单例；
- 根据机器报告定位物理、数据、模型、控制器或基础设施问题；
- 不用“机械臂动了”代替严格任务成功；
- 能让相同随机种子的评测重复得到同一动作序列。

## 16. 配套权威资料

```text
docs/FULL_PROJECT_TUTORIAL_ZH.md
docs/CODE_ARCHITECTURE_GUIDE_ZH.md
docs/RM65_4C2_STAGE_REPORT_ZH.md
docs/RM65_EXPERT_DATASET_ZH.md
results/project_progress.json
results/rm65_pi05_eval_v1_summary.json
results/rm65_pi05_eval_v2_summary.json
results/pi05_rm65_policy_window_v2_comparison_to_v1.json
```

任何结论都优先以当前 Git 提交和 `results/*.json` 为准，而不是以聊天记忆为准。
