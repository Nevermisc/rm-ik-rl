# RM65 专家示教数据：从成功动画到 π0.5 训练样本

## 这一层在解决什么

前一阶段的脚本专家已经能在 Isaac Lab 中完成一次完整的顶部抓取、转运、下降、释放和撤离。但“机械臂完成了动画”还不能训练 π0.5。训练需要把每个时刻模型能看到的内容和专家随后执行的动作一一对齐。

当前实现先建立可检查的中间格式 `rm65_expert_episode_v1`。它不是最终 LeRobot 数据集，也不声称可以直接送入 OpenPI；这样做是为了先验证最容易出错的时间同步、关节顺序、夹爪归一化和动作语义，再单独完成图像与 OpenPI 转换。

## 一帧数据的含义

默认物理频率是 240 Hz，每 12 个物理步记录一帧，因此策略数据频率是 20 Hz。第 `i` 帧表示：

1. 读取执行动作前的 RM65 六个实际关节角；
2. 读取 4C2 主关节并换算为 `0=张开、1=闭合`；
3. 读取方块世界位姿，便于检查任务是否真的成功；
4. 保存这个时刻即将执行的六轴绝对目标角和夹爪目标；
5. 保存当前任务阶段，例如 `APPROACH_1`、`CLOSE`、`LIFT`、`TRANSFER`。

状态和动作使用相同索引，但动作发生在该状态之后。`metadata.json` 中把这一点写成了 `observation immediately before applying action at the same index`。

## 文件结构

```text
episode_000000/
├── metadata.json
└── episode.npz
```

接入相机后还会出现：

```text
episode_000000/images/external/000000.png
episode_000000/images/wrist/000000.png
```

`episode.npz` 当前包含：

| 数组 | 形状 | 含义 |
|---|---:|---|
| `timestamp_s` | `(N,)` | 仿真时间 |
| `sim_step` | `(N,)` | 物理步编号 |
| `observation_state` | `(N, 7)` | 六轴实际角 + 归一化夹爪 |
| `action` | `(N, 7)` | 六轴绝对目标角 + 归一化夹爪目标 |
| `cube_pose_wxyz` | `(N, 7)` | 方块位置与四元数 |
| `phase_id` | `(N,)` | 对应 `metadata.json` 中的阶段名 |

夹爪归一化沿用接口定义：`clip(tool_gripper_joint / 0.865, 0, 1)`。这只是软件接口约定；真机前还必须用实际开口宽度和驱动器反馈校准。

## 在实验室电脑运行

进入项目目录后执行：

```bash
bash scripts/run_recorded_expert_demo.sh
```

默认输出到：

```text
datasets/rm65_scripted_v1/episode_000000
```

也可以指定目录和转运角：

```bash
bash scripts/run_recorded_expert_demo.sh \
  datasets/rm65_scripted_v1/episode_000001 0.6
```

单独检查已有 episode：

```bash
python3 scripts/validate_expert_episode.py \
  datasets/rm65_scripted_v1/episode_000000
```

校验器会检查数组形状、有限数值、时间单调性、仿真步单调性、夹爪范围、阶段编号和图像文件完整性。

双相机接入并收集多条成功 episode 后，在 OpenPI 环境中转换：

```bash
cd ~/robot-learning/openpi
uv run ../004-rm65-4c2-isaaclab/scripts/convert_expert_episodes_to_lerobot.py \
  ../004-rm65-4c2-isaaclab/datasets/rm65_scripted_v1 \
  --repo-id local/rm65_sim \
  --split train
```

转换器只接受 `task_success=true` 且双相机文件完整的 episode，并要求所有 episode 的频率与相机尺寸一致。它输出 `image`、`wrist_image`、`joints`、`gripper`、`actions` 和 `task` 字段；这与 OpenPI 官方 UR5 自定义机器人示例的拆分状态写法一致，也能直接复用本项目的 RM65 transform。若输出目录已经存在，必须显式加入 `--overwrite` 才会替换。

## 当前边界

低维状态、动作和双相机采样代码已经进入同一个控制循环。每个 20 Hz 采样点先读取当前状态，更新工具坐标系中的腕部相机位姿，渲染外部与腕部图，再保存下一步动作。实验室主机离线期间只能完成本地格式与转换器测试；双 Camera 对象的 IsaacLab 全任务运行仍待在线回归。只有实际报告同时满足任务成功、episode 校验通过、`images_recorded=true` 和 `training_ready=true`，该条记录才允许进入转换器。

全任务回归通过后，下一步是收集带起点、目标位置和视觉扰动的多条成功示教，转换成 OpenPI 当前使用的数据格式，并计算 RM65 自己的归一化统计量。

第一批多扰动采集使用三种转运角和九个源位置组合：

```bash
bash scripts/run_recorded_expert_suite.sh
```

源位置偏移限制在世界 x/y 各 ±40 mm；首批套件只使用 ±15 mm。顶部抓取会保留已校准的夹爪到方块局部变换，再把完整抓取位姿平移到新源位置。纯 NumPy 测试验证了这种平移不会改变闭合轴、顶部方向或夹爪到方块的相对几何。

套件会生成 `results/rm65_scripted_dataset_summary.json`，并对每条 episode 检查完整任务成功、双图像配对、图像尺寸、非黑帧、红色目标可见性及抽样帧是否发生变化。该汇总通过仍只代表脚本专家数据合格，不代表 π0.5 已经学会任务。

九条套件通过以后，使用机器可读的正式采集计划：

```bash
python3 scripts/run_expert_collection_plan.py \
  --plan config/rm65_expert_collection_plan_v1.json \
  --dataset-root datasets/rm65_scripted_v1
```

计划包含 5 个转运角 × 3×3 个源位置，共 45 条条件，其中 36 条标记为 `train`，9 条标记为 `validation`，并轮换五种同义指令。运行器会识别已经完整通过的同一 case 并跳过，从中断位置继续；遇到同名但不完整或属于其他 case 的 episode 会停止，避免静默覆盖证据。这里的 validation 只检查示教分布，不能代替 π0.5 闭环评测。

## OpenPI 数据配置预检

`openpi_extension/rm65_training_config.py` 已准备 RM65 专用数据映射和 π0.5 LoRA 配置。它把数据集字段映射回推理时使用的观测名称，并把前六个绝对关节目标转换成相对当前状态的 delta；夹爪维度保持绝对值。这样模型训练输出经过逆变换后仍是安全层需要的六轴绝对目标与夹爪目标。

在 OpenPI 环境中、生成 LeRobot 数据集之后，先只检查一个 batch，不下载或开始训练：

```bash
cd ~/robot-learning/openpi
PYTHONPATH=../004-rm65-4c2-isaaclab \
  uv run ../004-rm65-4c2-isaaclab/scripts/validate_rm65_openpi_data.py \
  --repo-id local/rm65_sim \
  --output ../004-rm65-4c2-isaaclab/outputs/rm65_openpi_data_contract.json
```

这一步通过后才运行 OpenPI 的归一化统计脚本。训练配置使用 `pi05_base`、10 步动作块和 LoRA，默认 batch size 为 1，以便先测试 16 GB 显存是否足够。显存是否足够仍必须实测，不能依据配置文件推断。

## 与最终目标的关系

完整链路是：

```text
脚本专家成功
  → 同步记录状态、动作、双相机、指令
  → 多扰动成功示教
  → 转换并校验 OpenPI 数据集
  → RM65 专属微调与归一化统计
  → π0.5 在 Isaac Lab 闭环执行
  → 安全层、低速真机空载测试
  → RM65 + 4C2 真机任务
```

当前完成到“双相机同步代码与 LeRobot 转换器已准备，本地输入测试通过”，下一道门槛是在实验室 IsaacLab 中跑通并检查真实生成的图像序列。
