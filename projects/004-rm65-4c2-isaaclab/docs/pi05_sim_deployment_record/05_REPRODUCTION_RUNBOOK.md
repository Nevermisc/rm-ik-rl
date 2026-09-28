# 正式结果复现手册

本手册复现当前 RM65-B + 4C2 + pi0.5 的仿真闭环门槛。默认在实验室 Linux 电脑执行，不会向真实机械臂发送命令。

## 1. 固定版本与路径

项目目录：

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
git rev-parse HEAD
git status --short
```

当前正式 checkpoint：

```text
outputs/openpi_checkpoints/pi05_rm65_lora/rm65_policy_window_v2_lora_30k/29999
```

当前正式计划：

```text
config/rm65_pi05_evaluation_plan_deterministic_v2_confirmation.json
```

归一化统计仓库标识必须为：

```text
local/rm65_sim_policy_train
```

## 2. 运行前检查

```bash
nvidia-smi
ss -ltnp | grep -E ':(8000|8016)\b' || true
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
test -d outputs/openpi_checkpoints/pi05_rm65_lora/rm65_policy_window_v2_lora_30k/29999
test -f generated/rm65_4c2_wide_pads.usd
```

要求：

- GPU 有足够空间同时运行策略服务与 Isaac Sim；
- 计划使用的策略端口未被其他进程占用；
- 旧的 `libero-openpi_server-1` 不应占用约 8 GB 显存或 8000 端口；
- checkpoint、RM65/4C2 资产和 Isaac Lab 均存在；
- Git 工作区的已有用户文件不得因复现被删除或覆盖。

## 3. 单案例冒烟检查

先使用独立输出目录运行 1 个案例：

```bash
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
  --checkpoint outputs/openpi_checkpoints/pi05_rm65_lora/rm65_policy_window_v2_lora_30k/29999 \
  --plan config/rm65_pi05_evaluation_plan_deterministic_v2_confirmation.json \
  --output-root datasets/rm65_pi05_smoke_repro \
  --summary results/rm65_pi05_smoke_repro_summary.json \
  --policy-port 8016 \
  --repo-id local/rm65_sim_policy_train \
  --gripper-open-threshold 0.12 \
  --gripper-actual-open-threshold 0.20 \
  --policy-max-action-chunks 120 \
  --max-cases 1
```

因为门槛要求至少 20 个案例，这个命令即使单案例成功也会返回非零 suite 状态；它只用于检查服务、相机、动作和报告链路。

## 4. 正式 20 案例确认集

```bash
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
  --checkpoint outputs/openpi_checkpoints/pi05_rm65_lora/rm65_policy_window_v2_lora_30k/29999 \
  --plan config/rm65_pi05_evaluation_plan_deterministic_v2_confirmation.json \
  --output-root datasets/rm65_pi05_release_supervisor_confirmation_20 \
  --summary results/rm65_pi05_release_supervisor_confirmation_20_summary.json \
  --policy-port 8016 \
  --repo-id local/rm65_sim_policy_train \
  --gripper-open-threshold 0.12 \
  --gripper-actual-open-threshold 0.20 \
  --policy-max-action-chunks 120 \
  --case-timeout-seconds 1200 \
  --infrastructure-retries 1
```

`--infrastructure-retries` 只允许重试没有生成有效报告的基础设施故障。一个模型案例正常生成 `status=fail` 后不得自动重跑来提高成功率。

## 5. 生成可审计证据

```bash
python3 scripts/compact_closed_loop_suite_summary.py \
  --input results/rm65_pi05_release_supervisor_confirmation_20_summary.json \
  --output results/rm65_pi05_release_supervisor_confirmation_20_compact_evidence.json

python3 scripts/analyze_rm65_closed_loop_failures.py \
  --plan config/rm65_pi05_evaluation_plan_deterministic_v2_confirmation.json \
  --episode-root datasets/rm65_pi05_release_supervisor_confirmation_20 \
  --output results/rm65_pi05_release_supervisor_confirmation_20_failure_taxonomy.json

python3 scripts/analyze_deterministic_release_failures.py \
  --plan config/rm65_pi05_evaluation_plan_deterministic_v2_confirmation.json \
  --episode-root datasets/rm65_pi05_release_supervisor_confirmation_20 \
  --output results/rm65_pi05_release_supervisor_confirmation_20_release_analysis.json \
  --gripper-open-threshold 0.12
```

## 6. 复核清单

正式结果必须同时满足：

- `planned_case_count=20` 且 `episode_count=20`；
- `success_count>=16` 且 `success_rate>=0.8`；
- `diagnostic_only=false`；
- `all_reports_present=true`；
- `all_cases_simulation_only=true`；
- `real_robot_command_sent=false`；
- 每个案例的策略种子和仿真种子唯一；
- checkpoint id、归一化 repo id、阈值和最大 chunk 数与计划一致；
- 不存在通过重复模型失败案例而挑选最好结果的情况。

## 7. 恢复运行语义

套件可以恢复中断运行，但只复用同时匹配以下字段的报告：checkpoint、策略夹爪阈值、真实夹爪阈值、最大 chunk 数、策略种子和仿真种子。任何一项不同都会重新运行该案例，从而避免混用不同实验条件。

## 8. 运行结束检查

```bash
ss -ltnp | grep ':8016\b' || true
nvidia-smi
git status --short
```

策略服务应由 suite 的 `finally` 路径停止。原始 episode、图像和日志保留在 `datasets/`/`outputs/`，Git 中只保存必要的紧凑证据和分析结果。

## 9. 复核 20×3 重复性矩阵

三次运行必须使用同一个冻结计划和三个独立输出根目录。完成后执行：

```bash
python3 scripts/analyze_rm65_repeatability_matrix.py \
  --plan config/rm65_pi05_repeatability_plan_v1_20x3.json \
  --run-root datasets/rm65_pi05_repeatability_v1_run1 \
  --run-root datasets/rm65_pi05_repeatability_v1_run2 \
  --run-root datasets/rm65_pi05_repeatability_v1_run3 \
  --output results/rm65_pi05_repeatability_matrix_v1_20x3.json
```

当前正式结果会返回非零，因为状态一致率为 85%、翻转数为 3，未达到 95%/最多 1 个翻转的预注册门槛。这是预期的门禁失败，不是分析脚本故障。

`--reset-renderer-accumulation-before-policy-observation` 只用于诊断，并会强制 `diagnostic_only=true`；默认关闭，且恢复逻辑不会混用开启/关闭该选项的报告。单次两运行探针没有消除像素和首动作差异，因此禁止把它当作已经验证的正式改进。
