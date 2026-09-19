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

## 2026-09-19 的实测进度

双相机同步采样和完整任务已经在新实验室电脑上实际回归，不再只是待验证代码。正式采集计划的 45 个条件全部通过：36 条 train、9 条 validation，总计 20,175 帧。每条 episode 同时满足任务成功、无辅助完整任务、双图像完整、图像健康和计划参数一致。汇总证据是 `results/rm65_scripted_v1_summary.json`。

最后一条 case 44 最初仅因释放后漂移 `22.65 mm` 超过 `20 mm` 阈值失败。检查发现放置段末端关节跟踪误差为 `0.166 rad`，因此把每个约 1 cm 放置路点的执行步数从 120 增加到 180；重跑后通过。失败样本单独归档到 `datasets/rm65_failed_v1/`，没有混入训练集。

数据已经分别转换为：

```text
~/.cache/huggingface/lerobot/local/rm65_sim_train
  36 episodes / 16,179 frames

~/.cache/huggingface/lerobot/local/rm65_sim_validation
  9 episodes / 3,996 frames
```

两份数据都通过 OpenPI loader contract：图像为 `224×224×3`，七维 RM65 状态进入模型前补齐为 32 维，模型 action horizon 为 10，逆变换后输出 `(10, 7)` 的六轴绝对目标和一个归一化夹爪目标。

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

python3 scripts/summarize_expert_dataset.py \
  datasets/rm65_scripted_v1 \
  --plan config/rm65_expert_collection_plan_v1.json \
  --output results/rm65_scripted_dataset_summary.json
```

计划包含 5 个转运角 × 3×3 个源位置，共 45 条条件，其中 36 条标记为 `train`，9 条标记为 `validation`，并轮换五种同义指令。运行器会识别已经完整通过的同一 case 并跳过，从中断位置继续；遇到同名但不完整或属于其他 case 的 episode 会停止，避免静默覆盖证据。汇总器逐项核对 case ID、split、角度、源位置和指令，只有 45 条条件全部一致才给出 `collection_plan_complete=true`。这里的 validation 只检查示教分布，不能代替 π0.5 闭环评测。

## OpenPI 数据、归一化和训练

`openpi_extension/rm65_training_config.py` 已准备 RM65 专用数据映射和 π0.5 LoRA 配置。它把数据集字段映射回推理时使用的观测名称，并把前六个绝对关节目标转换成相对当前状态的 delta；夹爪维度保持绝对值。这样模型训练输出经过逆变换后仍是安全层需要的六轴绝对目标与夹爪目标。

生成 LeRobot 数据集之后，先只检查一个 batch：

```bash
cd ~/robot-learning/openpi
PYTHONPATH=../004-rm65-4c2-isaaclab \
  uv run ../004-rm65-4c2-isaaclab/scripts/validate_rm65_openpi_data.py \
  --repo-id local/rm65_sim_train \
  --output ../004-rm65-4c2-isaaclab/outputs/rm65_openpi_data_contract.json
```

归一化统计已由 `scripts/compute_rm65_norm_stats.py` 计算，并保存到：

```text
~/robot-learning/openpi/assets/pi05_rm65_lora/local/rm65_sim_train/norm_stats.json
```

训练从官方 `pi05_base` 开始，保留 10 步动作块，使用 PaliGemma rank-16 LoRA 和 action expert rank-32 LoRA。第一次按默认配置训练时，16 GB 显卡发生 OOM；实测不是数据错误，而是视觉塔、两个 LoRA 分支和反向图同时占用超过显存。解决方法是把短指令的最大 token 数从 200 降到 64，并冻结预训练 SigLIP 视觉编码器。训练步显存估算由约 `15.98 GiB + 5.36 GiB` 降为 `7.35 GiB`，两步 smoke test 和 20 步 benchmark 均通过。

正式训练命令由 `scripts/train_rm65_pi05.py` 封装：

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
PYTHONPATH="$PWD:$HOME/robot-learning/openpi/src" \
  ~/robot-learning/openpi/.venv/bin/python scripts/train_rm65_pi05.py \
  --repo-id local/rm65_sim_train \
  --exp-name rm65_scripted_v1_lora_30k \
  --num-train-steps 30000 \
  --batch-size 1 \
  --save-interval 5000 \
  --log-interval 100 \
  --report results/pi05_rm65_formal_30k.json
```

训练完成后按三层验收，不能跳级：

1. `validate_rm65_checkpoint.py` 检查单帧输出形状、有限值和动作安全层；
2. `evaluate_rm65_checkpoint_offline.py` 在 9 条 validation episode 上批量统计动作误差和安全层触发次数；
3. `run_pi05_rm65_closed_loop.sh` 才允许在 IsaacLab 中执行动作，报告必须明确写出 `simulation_only=true` 和 `real_robot_command_sent=false`。

单次闭环命令格式为：

```bash
bash scripts/run_pi05_rm65_closed_loop.sh \
  outputs/openpi_checkpoints/pi05_rm65_lora/rm65_scripted_v1_lora_30k/FINAL_STEP \
  datasets/rm65_pi05_eval/episode_000000
```

闭环评测会同时启动 RM65 专用策略服务器和 IsaacLab，用外部相机、腕部相机、六轴状态、夹爪状态和文字指令反复推理。每次只执行动作块前几步，然后重新观察，形成 receding-horizon 控制；关节限位、单步最大 `0.05 rad`、夹爪 `[0,1]` 限幅仍在执行路径中。

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
