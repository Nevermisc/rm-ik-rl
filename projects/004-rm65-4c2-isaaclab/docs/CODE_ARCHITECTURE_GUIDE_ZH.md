# RM65-B + 4C2 + π0.5 代码架构导读

这份导读回答三个问题：一帧数据怎样流过项目、每个文件解决什么问题、你应该按什么顺序读和改代码。它只描述当前已落地的代码；实际 π0.5 仿真闭环和真机结果以 `results/project_progress.json` 为准。

## 1. 先建立一条主线

项目的核心数据流是：

```text
IsaacLab / 真实传感器
  ├─ 6 个 RM65 关节角（rad）
  ├─ 1 个 4C2 归一化开度（0 开，1 闭）
  ├─ 外部 RGB 图像
  ├─ 腕部 RGB 图像
  └─ 文字指令
        ↓
RM65Inputs：改成 π0.5 的 state/image/prompt 字段
        ↓
π0.5：输出 10×7 动作块
        ↓
RM65Outputs：只取 6 个关节目标 + 1 个夹爪目标
        ↓
动作安全层：有限值、关节限位、相邻步长、夹爪范围
        ↓
IsaacLab 闭环执行，或真机影子记录
        ↓
任务报告与门禁
```

“10×7”表示模型一次预测未来 10 个控制时刻，每个时刻包含 6 个 RM65 绝对关节目标和 1 个夹爪目标。模型每次只执行动作块的一部分，然后重新观察和推理，这叫 receding-horizon（滚动时域）闭环。

## 2. 资产层：让仿真知道机械结构

### `scripts/build_combined_urdf.py`

输入是 RM65-B URDF 和用户提供的 4C2 URDF/STL，输出组合 URDF。这里解决：

- 把夹爪挂到 `link6`；
- 保留 6 个机械臂关节和夹爪关节；
- 给夹爪网格、惯量和碰撞体正确路径；
- 生成仿真使用的经验接触垫版本。

你修改真实安装位姿时，主要看“机械臂末端到夹爪基座”的固定关节 origin。不要用视觉上“看起来差不多”代替测量。

### `scripts/import_combined_urdf.py` 与 `scripts/inspect_usd_physics.py`

前者把 URDF 导入 USD，后者检查刚体、关节、碰撞 API 和碰撞近似。导入成功只说明文件可解析；物理清单通过才说明 Isaac Sim 真的给对应 prim 启用了物理。

## 3. 任务层：先用可解释专家证明环境可完成

### `scripts/run_pick_place_baseline.py`

这是当前任务环境和控制主程序。它同时包含两条互斥路径：

1. 脚本专家：用 IK 和阶段状态机完成接近、闭合、抬升、搬运、下降、释放；
2. π0.5 闭环：每次读取相机与状态，向策略服务请求动作，再经安全层执行。

重要参数由命令行传入，例如源物体偏移、底座转角、抓取偏移、放置下降距离和是否启用 π0.5。这样实验条件会写进命令和报告，而不是藏在代码常量里。

阅读时先搜索：

```bash
rg -n "pi05_closed_loop|run_pi05|phase|task_report|return 0 if passed" scripts/run_pick_place_baseline.py
```

先读参数定义，再读 π0.5 分支，最后读报告中的成功条件。不要从 2000 行脚本的第一行顺序硬读到最后。

### `openpi_extension/expert_episode.py`

它负责把每个控制时刻写成训练样本。关键约定是“先保存当前观测，再保存下一条要执行的动作”，避免图像与动作错一帧。一个 episode 包含：

- `observation_state`：6 关节 + 1 夹爪；
- `action`：未来要执行的 6 关节 + 1 夹爪；
- `phase_id`：当前任务阶段；
- 外部和腕部图像路径；
- prompt 与实验条件元数据。

### `scripts/run_expert_collection_plan.py`

它读取 `config/rm65_expert_collection_plan_v1.json`，逐条运行 45 个可恢复用例。已经成功的 episode 会经校验后复用，失败或损坏的才重跑。这里学到的是批处理、断点恢复和实验可追溯性。

## 4. 数据层：从 episode 变成 OpenPI 能读的格式

### `scripts/convert_expert_episodes_to_lerobot.py`

它把原始 episode 转成 LeRobot 数据集。转换不是简单复制文件；它要声明每个字段的 shape、dtype、时间索引和 episode 边界。训练集与验证集必须由 collection plan 决定，不能训练后再挑好看的 episode 当验证集。

### `scripts/validate_rm65_openpi_data.py`

它实例化真实训练配置并取一个 batch，检查：

- 三个模型图像槽存在，其中第三个未使用槽有 mask；
- state 被填充到模型宽度，但真实语义仍只有 7 维；
- action 为 `1×10×32` 模型张量，前 7 维属于 RM65；
- token 长度和有限值正确。

这个测试能发现“数据文件存在但字段名或维度不匹配”的问题。

### `scripts/compute_rm65_norm_stats.py`

它只用训练集计算归一化统计。验证集不能参与，否则会产生数据泄漏。统计文件必须放在与 repo id 对应的 OpenPI assets 路径，训练和推理必须使用同一份统计。

## 5. 模型层：告诉 OpenPI 什么是 RM65

### `openpi_extension/rm65_policy.py`

这是最值得先读懂的模型接口文件。

`RM65Inputs.__call__()` 做四件事：

1. 检查关节必须正好 6 维、夹爪必须 1 维；
2. 把两幅图像统一成 HWC RGB；
3. 组成 7 维真实 state；
4. 映射为 π0.5 的相机名称和 mask。

`RM65Outputs.__call__()` 从模型输出中只取前 7 维。这里不能把 Franka 的 7 轴动作硬删一轴；RM65 checkpoint 必须用 RM65 的 7 维“6 轴 + 夹爪”语义训练。

### `openpi_extension/rm65_training_config.py`

它组装 π0.5 LoRA 训练配置，包括数据 repo id、模型类型、动作 horizon、最大 token 长度、冻结视觉编码器和 LoRA rank。16 GB 显存机器使用 batch size 1、较短 token 和冻结视觉编码器，是为了在保留语言与动作微调能力的同时控制显存。

### `scripts/train_rm65_pi05.py`

它调用 OpenPI 训练入口，并在结束后写 `pi05_rm65_formal_30k.json`。日志中的 loss 只能证明优化过程数值正常；不能证明机械臂会成功抓取。任务能力必须由闭环评测单独证明。

## 6. 推理与仿真闭环

### `scripts/serve_rm65_policy.py`

它加载 RM65 专用训练配置、checkpoint 和 norm stats，启动 WebSocket 策略服务。服务元数据明确声明 robot、gripper、模型和动作语义。

### `openpi_extension/action_guard.py`

它对每个动作块执行 fail-closed 检查：

- shape 必须是 `T×7`；
- 拒绝 NaN/Inf；
- 关节目标夹在带 margin 的关节范围内；
- 相邻目标变化不能超过上限；
- 夹爪限制在 `[0,1]`。

仿真上限和真机首次上限不同。`real_robot_adapter.py` 把真机每个策略步进一步限制为 `0.01 rad`。

### `scripts/run_pi05_rm65_closed_loop.sh`

它负责一次完整用例：启动策略服务、等待端口、启动 IsaacLab、传入 checkpoint id 和实验条件，退出时清理服务。

### `scripts/run_pi05_rm65_closed_loop_suite.py`

它只启动一次模型服务，再运行 20 个留出条件。每个任务有独立日志和超时，可复用同一 checkpoint 的完整报告。最终门槛是至少 20 条有效 episode 且成功率不低于 80%。

`config/rm65_pi05_evaluation_plan_v1.json` 的角度与位置组合没有出现在训练示范中，但仍位于训练范围内，因此它证明留出插值鲁棒性，不证明任意场景泛化。

## 7. 真机安全层

### `openpi_extension/real_robot_adapter.py`

它目前全部是无副作用函数：

- 按 `joint1...joint6` 重排 ROS 反馈；
- 校验 4C2 实测标定文件；
- 将归一化夹爪目标映射到驱动命令；
- 使用更严格的 `0.01 rad` 动作限幅；
- 把 20 Hz 策略目标插值为 50 Hz 驱动目标。

### `scripts/probe_rm65_joint_feedback.py`

它只订阅 `/joint_states`，检查名称、弧度、范围、时间顺序和频率，不创建发布器。

### `scripts/run_rm65_policy_shadow.py`

它订阅关节和双相机，运行 π0.5 与安全层，只写 JSONL。源码没有 RealMan 控制消息，也没有发布器。`validate_rm65_policy_shadow.py` 再从原始 JSONL 证明 20 个样本都满足只读约束。

### `openpi_extension/execution_gate.py`

它不猜测“应该可以”，只检查证据字段。仿真门要求 RM65/4C2/π0.5、checkpoint、统计和动作语义一致。真机门还要求 20 条仿真评测、网络与反馈、急停、低速、工作空间、夹爪和相机标定、watchdog、影子模式和现场监护全部通过。

## 8. 你修改代码时采用的循环

每次只改一个可验证假设：

1. 写出问题，例如“腕部图像时间比关节状态晚 180 ms”；
2. 找到拥有这项责任的最小文件；
3. 先写能复现失败的测试或机器报告；
4. 修改实现；
5. 运行最小测试；
6. 再运行相关集成测试；
7. 保存 JSON 证据并提交 Git；
8. 不把离线通过解释成闭环通过，也不把仿真通过解释成真机通过。

一个适合入门的练习顺序：

1. 修改 evaluation plan 的 prompt，但不改几何条件，运行 plan validator；
2. 给 `action_guard` 增加一个 NaN 或越界测试，观察它如何拒绝；
3. 在一个 episode 中打印 state/action shape 和阶段名；
4. 跟踪一帧从 dataset 到 `RM65Inputs` 后的 key、shape 和 mask；
5. 修改影子模式允许的时间偏差，构造一条测试证明新阈值；
6. 最后才修改 IsaacLab 任务几何或真实控制频率。

## 9. 需要掌握的 Python 能力

优先级从高到低：

- NumPy：shape、dtype、广播、切片、有限值与范数；
- Python 数据结构：dict/list、dataclass、类型标注；
- 文件与实验记录：`pathlib`、JSON、NPZ、哈希；
- 命令行：`argparse`、退出码、stdout/stderr；
- 进程与网络：`subprocess`、WebSocket、端口和超时；
- 测试：构造最小输入、断言、fail-closed；
- ROS2：node、topic、message、QoS、时间戳；
- Git：小提交、diff、恢复和证据追踪。

LeetCode 能训练基本数据结构和边界意识，但与这个项目重合较少。对具身智能更直接的练习是：用 NumPy 实现轨迹插值、坐标变换、关节限幅、数据窗口采样和同步队列，再给每个函数写边界测试。
