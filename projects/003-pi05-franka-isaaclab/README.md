# π0.5 × Franka × Isaac Lab

这是一个可复现的具身智能仿真项目：使用 OpenPI 的 π0.5 DROID joint-position 策略，控制 Isaac Lab 中的 Franka + Robotiq 完成三个视觉语言操作任务，并评测位置、指令和亮度扰动下的鲁棒性。

## 已验证结果

严格成功要求操作物进入目标、实际夹爪张开，并稳定保持 15 个控制步。

| 评测 | 成功数 | 总数 |
|---|---:|---:|
| 三个官方场景，每个重复 3 次 | 9 | 9 |
| 位置、语言和亮度扰动 | 17 | 18 |
| 任务评测合计 | 26 | 27 |

三个任务分别是：

1. 把魔方放进红碗；
2. 把肉罐头放进红杯；
3. 把香蕉放进紫色收纳盒。

鲁棒性测试包括操作物位置偏移、目标位置偏移、英文同义指令、图像亮度降低 25% 和增加 25%。唯一失败发生在“移动红杯后放入罐头”的用例。

工程审计确认：

- 所有策略动作和关节观测均为有限数值；
- 最小关节限位余量为 0.267 rad；
- 最大实际关节单步变化为 0.080 rad；
- 重新规划推理延迟中位数约为 0.318 秒。

这些数字只描述仓库记录的固定测试矩阵，不代表 π0.5 在任意 Franka 场景中的通用成功率。

## 系统结构

```text
任务指令 + 外部相机 + 腕部相机 + 7 关节状态 + 夹爪状态
                            │
                            ▼
              π0.5 推理服务（Docker / JAX）
                            │
                            ▼
          7 个绝对目标关节角 + 1 个夹爪命令
                            │
                            ▼
               Isaac Lab → Isaac Sim
                            │
                            └──── 新观测反馈给 π0.5
```

策略一次预测 `15×8` 动作块，执行前 8 步后使用最新观测重新规划。仿真控制频率为 15 Hz。

## 外部依赖

本仓库不包含模型权重、Isaac Sim、Isaac Lab 或仿真资产。验证使用：

- Ubuntu 22.04
- NVIDIA RTX 4060 Ti 16 GB
- Isaac Sim 5.1.0
- Isaac Lab 2.3.2
- OpenPI commit `15a9616`
- sim-evals commit `3a6b0e8`
- `pi05_droid_jointpos_polaris`
- `gs://openpi-assets/checkpoints/pi05_droid_jointpos`

默认目录结构：

```text
~/robot-learning/openpi
~/robot-learning/IsaacLab
~/robot-learning/sim-evals
~/robot-learning/pi05-franka-isaaclab
```

也可以通过 `OPENPI_DIR`、`ISAACLAB_DIR` 和 `SIM_EVALS_DIR` 环境变量覆盖路径。

## 快速复现

先启动模型并进行 JAX 预热：

```bash
cd ~/robot-learning/pi05-franka-isaaclab
bash scripts/start_and_warmup_pi05.sh
```

运行完整的三个场景、三组评测：

```bash
bash scripts/run_all_suites.sh
```

这会依次运行 30 个回合，通常需要较长时间。也可以只跑一个场景：

```bash
cd ~/robot-learning/sim-evals
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  ~/robot-learning/pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py \
  --scene 1 --suite baseline --device cuda:0 --headless
```

停止服务并释放显存：

```bash
bash scripts/stop_pi05_server.sh
```

## 项目内容

```text
config/
  openpi-gpu-memory.override.yml     # π0.5 与 Isaac Sim 共享 16 GB 显存
docs/
  FRANKA_STAGE_REPORT_ZH.md          # 中文原理、命令、结果和排错手册
results/
  pi05_franka_summary_20260914.json  # 已验证结果的小型摘要
scripts/
  start_and_warmup_pi05.sh           # 启动模型并预热
  validate_droid_sim_scene.py        # 验证场景、相机和关节接口
  run_pi05_droid_scene1.py           # 最小单场景示例
  run_pi05_franka_robustness_suite.py# 完整严格评测程序
  run_all_suites.sh                   # 依次执行全部评测
  stop_pi05_server.sh                 # 停止模型服务
```

完整说明请阅读 [Franka 阶段报告与复现手册](docs/FRANKA_STAGE_REPORT_ZH.md)。

## 当前边界与下一步

当前项目完成了 π0.5 在 DROID 风格 Franka 仿真中的参考基线。sim-evals 本身针对 DROID 策略调整过，因此结果不能直接外推到 RM65 或真实实验室环境。

下一阶段是导入 RM65 与夹爪模型，完成关节、碰撞体、末端坐标系和确定性控制测试，再设计 7 关节 Franka 策略到 6 轴 RM65 的状态与动作适配方案。
