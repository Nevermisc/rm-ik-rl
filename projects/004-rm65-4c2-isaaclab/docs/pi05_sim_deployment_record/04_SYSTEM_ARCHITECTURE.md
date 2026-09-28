# 系统架构

## 总体数据流

```text
Isaac Lab 场景
  ├─ 外部 RGB 640×480 ─┐
  ├─ 腕部 RGB 640×480 ─┼─→ RM65 观测 transform ─→ 224×224 双视角图像
  ├─ RM65 六轴反馈 ────┤                         + 6 关节 + 1 夹爪 + prompt
  └─ 4C2 夹爪反馈 ─────┘
                                                  ↓
                                      pi0.5 policy server
                                      确定性噪声 + checkpoint
                                                  ↓
                                      10×7 绝对目标动作 chunk
                                                  ↓
                 动作限位 → 闭环执行 → 释放监督器 → 物理仿真
                     ↓          ↓           ↓           ↓
                  拒绝原因   chunk 证据   状态转移    任务指标
                     └──────────┴───────────┴───────────┘
                                      task_report.json
                                                  ↓
                          suite summary / compact evidence / failure taxonomy
```

## 核心组件

| 层 | 主要文件 | 职责 |
|---|---|---|
| 接口契约 | `config/rm65_pi05_interface.json` | 定义图像、六轴状态、夹爪状态和 `10×7` 动作语义 |
| 策略输入输出 | `openpi_extension/rm65_policy.py` | RM65 专用 observation/action transform |
| 确定性采样 | `openpi_extension/deterministic_policy.py` | 生成显式噪声、种子派生和哈希证据 |
| 策略服务 | `scripts/serve_rm65_policy.py` | 加载 checkpoint、接收观测并返回动作 chunk |
| 单案例入口 | `scripts/run_pi05_rm65_closed_loop.sh` | 启动/连接策略服务并运行一个 Isaac Lab 案例 |
| 仿真控制 | `scripts/run_pick_place_baseline.py` | 场景、闭环动作执行、释放状态机和任务报告 |
| 批量评测 | `scripts/run_pi05_rm65_closed_loop_suite.py` | 复用一个服务、运行计划、校验恢复条件和生成汇总 |
| 动作安全 | `openpi_extension/action_guard.py` | 非有限值、关节限位和最大步长检查 |
| 执行门 | `openpi_extension/execution_gate.py` | checkpoint、归一化和评测证据不全时失败关闭 |
| 报告审计 | `scripts/check_closed_loop_task_report.py` | 校验 checkpoint、种子、执行语义和报告字段 |
| 证据压缩 | `scripts/compact_closed_loop_suite_summary.py` | 从完整汇总提取可进入 Git 的紧凑证据 |
| 失败分析 | `scripts/analyze_rm65_closed_loop_failures.py` | 按提示词、角度和成功条件分类 |
| 释放诊断 | `scripts/analyze_deterministic_release_failures.py` | 分析目标区、夹爪信号和候选 streak |

## 观测与动作契约

策略观测包含：

- 外部 RGB：渲染为 `480×640×3 uint8`，模型输入经 padding resize 为 `224×224×3`；
- 腕部 RGB：同样为双视角 `224×224×3` 模型输入；
- RM65 六轴关节位置，顺序固定为 `joint_1` 到 `joint_6`；
- 4C2 归一化夹爪位置，`0=张开`、`1=闭合`；
- 自然语言任务提示词。

策略输出为 `10×7` 动作 chunk：前六维是 RM65 六轴绝对目标弧度，第七维是归一化夹爪闭合目标。DROID/Franka 的 `15×8` 动作只能做张量接口 dry-run，禁止截取前六维控制 RM65。

## 三个确定性边界

### 1. 策略采样

每个案例有唯一 `policy_noise_seed`，每个 chunk 使用 `case_seed + chunk_index`。噪声、原始动作和安全动作都写入 SHA-256 证据。该边界已验证跨交错调用及服务重启逐位一致。

### 2. 物理初始状态

Python、NumPy、Torch/CUDA、Warp、Replicator 和 PhysX 使用案例级 `simulation_seed`。机器人和方块初始状态能够精确复现。

### 3. RTX 相机渲染

不同进程仍可能出现稀疏像素差异。当前目标不是以破坏输入分布的方式强求逐像素一致，而是保留哈希证据，并通过训练增强和更大规模任务结果评测提高对该变化的鲁棒性。

## 执行层状态机

```text
REACH → GRASP → LIFTED → APPROACH_TARGET
                              ↓
                      RELEASE_CANDIDATE
                     （连续 2 个 chunk）
                              ↓
                     HOLD_ARM_AND_OPEN
                              ↓
                       VERIFY_PLACEMENT
```

进入释放候选需同时满足：方块已抬升、目标误差小于 5 cm、策略夹爪目标小于 `0.12`、真实夹爪反馈小于 `0.20`。触发后锁存真实机械臂姿态、全开夹爪并验证 240 个物理步。方块越过 1.0 m 工作空间包络时立即安全中止。

## 仿真与真机隔离

当前闭环路径只允许 `simulation_only=true`，报告必须记录 `real_robot_command_sent=false`。真机适配器、只读反馈探针和影子模式是独立路径；仿真通过不会自动解锁任何 ROS2 控制发布器。
