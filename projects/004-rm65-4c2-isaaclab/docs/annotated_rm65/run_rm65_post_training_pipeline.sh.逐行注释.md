# `run_rm65_post_training_pipeline.sh` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_rm65_post_training_pipeline.sh`
- 快照 SHA-256：`480407f58a828a2df197f90e3d1167ebbaa22cfe99fcd08a81d77e7508051398`
- 总行数：158
- 程序作用：等待训练结束后依次执行单帧推理、离线验证、资产 gate、计划验证、单 case、20-case suite、失败分析和最终清单。
- 推荐读法：它是训练后的总编排器；每个阶段本身由独立 Python 程序实现。

## 功能块地图

- 第 1-24 行：严格 Shell 模式、目录和可覆盖流水线参数
- 第 25-44 行：失败哨兵、参数检查和 policy-window 选项
- 第 46-60 行：等待训练 PID 并从训练报告提取 checkpoint
- 第 62-82 行：单帧 checkpoint 推理和验证集离线评测
- 第 84-98 行：构建策略资产清单并验证仿真 gate/评测计划
- 第 100-113 行：先运行一条闭环，但无论任务成败都继续完整 suite
- 第 115-146 行：20 条闭环、失败分类、与 v1 比较并保留真实退出码
- 第 148-158 行：构建含仿真结果的最终清单并写 pass 哨兵

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```bash
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env bash
# 【L0002】启用严格 Shell 模式：命令失败、未定义变量或管道失败都会让脚本停止。
set -euo pipefail
# 【L0003】空行：分隔“严格 Shell 模式、目录和可覆盖流水线参数”中的逻辑段，让结构更容易看清。

# 【L0004】计算并保存变量 `project_root`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 【L0005】计算并保存变量 `openpi_root`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
# 【L0006】计算并保存变量 `training_pid`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
training_pid="${1:?usage: $0 TRAINING_PID}"
# 【L0007】计算并保存变量 `training_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
training_report="${RM65_TRAINING_REPORT:-$project_root/results/pi05_rm65_formal_30k.json}"
# 【L0008】计算并保存变量 `repo_id`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
repo_id="${RM65_REPO_ID:-local/rm65_sim_train}"
# 【L0009】计算并保存变量 `norm_stats`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
norm_stats="${RM65_NORM_STATS:-$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json}"
# 【L0010】计算并保存变量 `result_prefix`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
result_prefix="${RM65_RESULT_PREFIX:-pi05_rm65_formal}"
# 【L0011】计算并保存变量 `evaluation_root`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
evaluation_root="${RM65_EVALUATION_ROOT:-$project_root/datasets/rm65_pi05_eval_v1}"
# 【L0012】计算并保存变量 `evaluation_summary`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
evaluation_summary="${RM65_EVALUATION_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"
# 【L0013】计算并保存变量 `checkpoint_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
checkpoint_report="$project_root/results/${result_prefix}_checkpoint_inference.json"
# 【L0014】计算并保存变量 `offline_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
offline_report="$project_root/results/${result_prefix}_offline_validation.json"
# 【L0015】计算并保存变量 `artifact_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
artifact_report="$project_root/results/${result_prefix}_policy_artifact.json"
# 【L0016】计算并保存变量 `taxonomy_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
taxonomy_report="$project_root/results/${result_prefix}_failure_taxonomy.json"
# 【L0017】计算并保存变量 `baseline_summary`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
baseline_summary="${RM65_BASELINE_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"
# 【L0018】计算并保存变量 `comparison_report`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
comparison_report="${RM65_COMPARISON_REPORT:-$project_root/results/${result_prefix}_comparison_to_v1.json}"
# 【L0019】计算并保存变量 `sentinel`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
sentinel="${RM65_PIPELINE_STATUS:-$project_root/outputs/rm65_post_training_pipeline.status}"
# 【L0020】计算并保存变量 `policy_window`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
policy_window="${RM65_POLICY_WINDOW:-false}"
# 【L0021】计算并保存变量 `first_case_timeout_seconds`；该值服务于“严格 Shell 模式、目录和可覆盖流水线参数”。
first_case_timeout_seconds="${RM65_FIRST_CASE_TIMEOUT_SECONDS:-1200}"
# 【L0022】空行：分隔“严格 Shell 模式、目录和可覆盖流水线参数”中的逻辑段，让结构更容易看清。

# 【L0023】执行“严格 Shell 模式、目录和可覆盖流水线参数”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
cd "$project_root"
# 【L0024】调用 `mkdir`：创建目录。本行位于“严格 Shell 模式、目录和可覆盖流水线参数”。
mkdir -p outputs results
# 【L0025】计算并保存变量 `current_stage`；该值服务于“失败哨兵、参数检查和 policy-window 选项”。
current_stage="initialization"
# 【L0026】执行“失败哨兵、参数检查和 policy-window 选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
on_error() {
# 【L0027】计算并保存变量 `exit_code`；该值服务于“失败哨兵、参数检查和 policy-window 选项”。
  exit_code=$?
# 【L0028】向终端打印状态或最终结果路径。
  echo "failed: stage=$current_stage exit_code=$exit_code" | tee "$sentinel"
# 【L0029】执行“失败哨兵、参数检查和 policy-window 选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit "$exit_code"
# 【L0030】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
}
# 【L0031】注册退出/中断清理函数，避免模型服务残留在后台。
trap on_error ERR
# 【L0032】空行：分隔“失败哨兵、参数检查和 policy-window 选项”中的逻辑段，让结构更容易看清。

# 【L0033】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ ! "$first_case_timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then
# 【L0034】向终端打印状态或最终结果路径。
  echo "RM65_FIRST_CASE_TIMEOUT_SECONDS must be a positive integer" >&2
# 【L0035】执行“失败哨兵、参数检查和 policy-window 选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  false
# 【L0036】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0037】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ "$policy_window" != "true" && "$policy_window" != "false" ]]; then
# 【L0038】向终端打印状态或最终结果路径。
  echo "RM65_POLICY_WINDOW must be true or false" >&2
# 【L0039】执行“失败哨兵、参数检查和 policy-window 选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  false
# 【L0040】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0041】计算并保存变量 `offline_view_args`；该值服务于“失败哨兵、参数检查和 policy-window 选项”。
offline_view_args=()
# 【L0042】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ "$policy_window" == "true" ]]; then
# 【L0043】计算并保存变量 `offline_view_args`；该值服务于“失败哨兵、参数检查和 policy-window 选项”。
  offline_view_args=(--policy-window)
# 【L0044】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0045】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0046】计算并保存变量 `current_stage`；该值服务于“等待训练 PID 并从训练报告提取 checkpoint”。
current_stage="wait_for_training"
# 【L0047】向终端打印状态或最终结果路径。
echo "waiting_for_training_pid=$training_pid" | tee "$sentinel"
# 【L0048】while 循环：条件保持为真时持续执行。
while kill -0 "$training_pid" 2>/dev/null; do
# 【L0049】执行“等待训练 PID 并从训练报告提取 checkpoint”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  sleep 30
# 【L0050】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
done
# 【L0051】空行：分隔“等待训练 PID 并从训练报告提取 checkpoint”中的逻辑段，让结构更容易看清。

# 【L0052】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ ! -f "$training_report" ]]; then
# 【L0053】向终端打印状态或最终结果路径。
  echo "failed: training report missing: $training_report" | tee "$sentinel"
# 【L0054】执行“等待训练 PID 并从训练报告提取 checkpoint”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit 1
# 【L0055】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
fi
# 【L0056】给变量 `checkpoint` 赋值：一次训练保存的模型参数目录。
checkpoint="$($openpi_root/.venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("status")=="pass", d; print(d["latest_checkpoint"])' "$training_report")"
# 【L0057】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ ! -d "$checkpoint" ]]; then
# 【L0058】向终端打印状态或最终结果路径。
  echo "failed: checkpoint missing: $checkpoint" | tee "$sentinel"
# 【L0059】执行“等待训练 PID 并从训练报告提取 checkpoint”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit 1
# 【L0060】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
fi
# 【L0061】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0062】设置并导出环境变量，让随后启动的 Python/JAX 进程读取该配置。
export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
# 【L0063】计算并保存变量 `validation_episode`；该值服务于“单帧 checkpoint 推理和验证集离线评测”。
validation_episode="$project_root/datasets/rm65_scripted_v1/episode_000000"
# 【L0064】空行：分隔“单帧 checkpoint 推理和验证集离线评测”中的逻辑段，让结构更容易看清。

# 【L0065】计算并保存变量 `current_stage`；该值服务于“单帧 checkpoint 推理和验证集离线评测”。
current_stage="single_checkpoint_inference"
# 【L0066】向终端打印状态或最终结果路径。
echo "stage=$current_stage checkpoint=$checkpoint" | tee "$sentinel"
# 【L0067】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
"$openpi_root/.venv/bin/python" scripts/validate_rm65_checkpoint.py \
# 【L0068】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --checkpoint "$checkpoint" \
# 【L0069】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --episode "$validation_episode" \
# 【L0070】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --repo-id "$repo_id" \
# 【L0071】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$checkpoint_report"
# 【L0072】空行：分隔“单帧 checkpoint 推理和验证集离线评测”中的逻辑段，让结构更容易看清。

# 【L0073】计算并保存变量 `current_stage`；该值服务于“单帧 checkpoint 推理和验证集离线评测”。
current_stage="offline_validation"
# 【L0074】向终端打印状态或最终结果路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0075】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
"$openpi_root/.venv/bin/python" scripts/evaluate_rm65_checkpoint_offline.py \
# 【L0076】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --checkpoint "$checkpoint" \
# 【L0077】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --dataset-root datasets/rm65_scripted_v1 \
# 【L0078】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --split validation \
# 【L0079】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --repo-id "$repo_id" \
# 【L0080】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --frames-per-episode 5 \
# 【L0081】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$offline_report" \
# 【L0082】执行“单帧 checkpoint 推理和验证集离线评测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "${offline_view_args[@]}"
# 【L0083】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0084】计算并保存变量 `current_stage`；该值服务于“构建策略资产清单并验证仿真 gate/评测计划”。
current_stage="simulation_manifest"
# 【L0085】向终端打印状态或最终结果路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0086】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/build_rm65_policy_artifact.py \
# 【L0087】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --training-report "$training_report" \
# 【L0088】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --norm-stats "$norm_stats" \
# 【L0089】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$artifact_report"
# 【L0090】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/check_policy_execution_gate.py \
# 【L0091】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "$artifact_report" --target simulation
# 【L0092】空行：分隔“构建策略资产清单并验证仿真 gate/评测计划”中的逻辑段，让结构更容易看清。

# 【L0093】计算并保存变量 `current_stage`；该值服务于“构建策略资产清单并验证仿真 gate/评测计划”。
current_stage="evaluation_plan_validation"
# 【L0094】向终端打印状态或最终结果路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0095】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/validate_rm65_evaluation_plan.py \
# 【L0096】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --collection-plan config/rm65_expert_collection_plan_v1.json \
# 【L0097】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --evaluation-plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0098】执行“构建策略资产清单并验证仿真 gate/评测计划”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output results/rm65_pi05_evaluation_plan_validation.json
# 【L0099】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0100】计算并保存变量 `current_stage`；该值服务于“先运行一条闭环，但无论任务成败都继续完整 suite”。
current_stage="first_closed_loop"
# 【L0101】向终端打印状态或最终结果路径。
echo "stage=$current_stage timeout_seconds=$first_case_timeout_seconds" | tee "$sentinel"
# 【L0102】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
set +e
# 【L0103】注册退出/中断清理函数，避免模型服务残留在后台。
trap - ERR
# 【L0104】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
timeout --signal=TERM --kill-after=30s "${first_case_timeout_seconds}s" \
# 【L0105】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  env RM65_REPO_ID="$repo_id" bash scripts/run_pi05_rm65_closed_loop.sh \
# 【L0106】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "$checkpoint" \
# 【L0107】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "$evaluation_root/eval_000" \
# 【L0108】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  0.65 -0.0075 -0.0075 \
# 【L0109】执行“先运行一条闭环，但无论任务成败都继续完整 suite”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "pick up the block and place it on the target"
# 【L0110】计算并保存变量 `first_case_exit_code`；该值服务于“先运行一条闭环，但无论任务成败都继续完整 suite”。
first_case_exit_code=$?
# 【L0111】注册退出/中断清理函数，避免模型服务残留在后台。
trap on_error ERR
# 【L0112】启用严格 Shell 模式：命令失败、未定义变量或管道失败都会让脚本停止。
set -e
# 【L0113】向终端打印状态或最终结果路径。
echo "stage=$current_stage exit_code=$first_case_exit_code continuing_to_full_suite" | tee "$sentinel"
# 【L0114】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0115】计算并保存变量 `current_stage`；该值服务于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
current_stage="twenty_case_closed_loop_suite"
# 【L0116】向终端打印状态或最终结果路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0117】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
set +e
# 【L0118】注册退出/中断清理函数，避免模型服务残留在后台。
trap - ERR
# 【L0119】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
# 【L0120】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --checkpoint "$checkpoint" \
# 【L0121】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --repo-id "$repo_id" \
# 【L0122】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0123】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output-root "$evaluation_root" \
# 【L0124】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --summary "$evaluation_summary"
# 【L0125】计算并保存变量 `suite_exit_code`；该值服务于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
suite_exit_code=$?
# 【L0126】注册退出/中断清理函数，避免模型服务残留在后台。
trap on_error ERR
# 【L0127】启用严格 Shell 模式：命令失败、未定义变量或管道失败都会让脚本停止。
set -e
# 【L0128】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/analyze_rm65_closed_loop_failures.py \
# 【L0129】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0130】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --episode-root "$evaluation_root" \
# 【L0131】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$taxonomy_report"
# 【L0132】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ -f "$baseline_summary" ]]; then
# 【L0133】计算并保存变量 `current_stage`；该值服务于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
  current_stage="compare_to_v1"
# 【L0134】向终端打印状态或最终结果路径。
  echo "stage=$current_stage" | tee "$sentinel"
# 【L0135】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  python3 scripts/compare_rm65_closed_loop_runs.py \
# 【L0136】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --baseline "$baseline_summary" \
# 【L0137】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --candidate "$evaluation_summary" \
# 【L0138】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0139】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --output "$comparison_report"
# 【L0140】结束或闭合当前语法结构；它属于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
fi
# 【L0141】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ "$suite_exit_code" -ne 0 ]]; then
# 【L0142】计算并保存变量 `current_stage`；该值服务于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
  current_stage="twenty_case_closed_loop_suite"
# 【L0143】注册退出/中断清理函数，避免模型服务残留在后台。
  trap - ERR
# 【L0144】向终端打印状态或最终结果路径。
  echo "failed: stage=$current_stage exit_code=$suite_exit_code" | tee "$sentinel"
# 【L0145】执行“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit "$suite_exit_code"
# 【L0146】结束或闭合当前语法结构；它属于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
fi
# 【L0147】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0148】计算并保存变量 `current_stage`；该值服务于“构建含仿真结果的最终清单并写 pass 哨兵”。
current_stage="final_manifest"
# 【L0149】向终端打印状态或最终结果路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0150】执行“构建含仿真结果的最终清单并写 pass 哨兵”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/build_rm65_policy_artifact.py \
# 【L0151】执行“构建含仿真结果的最终清单并写 pass 哨兵”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --training-report "$training_report" \
# 【L0152】执行“构建含仿真结果的最终清单并写 pass 哨兵”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --norm-stats "$norm_stats" \
# 【L0153】执行“构建含仿真结果的最终清单并写 pass 哨兵”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --simulation-summary "$evaluation_summary" \
# 【L0154】执行“构建含仿真结果的最终清单并写 pass 哨兵”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$artifact_report"
# 【L0155】空行：分隔“构建含仿真结果的最终清单并写 pass 哨兵”中的逻辑段，让结构更容易看清。

# 【L0156】注册退出/中断清理函数，避免模型服务残留在后台。
trap - ERR
# 【L0157】向终端打印状态或最终结果路径。
echo "pass" | tee "$sentinel"
# 【L0158】向终端打印状态或最终结果路径。
echo "RM65_POST_TRAINING_PIPELINE=PASS"
```
