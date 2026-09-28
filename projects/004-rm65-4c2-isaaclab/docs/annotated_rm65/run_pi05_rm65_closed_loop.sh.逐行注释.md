# `run_pi05_rm65_closed_loop.sh` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_pi05_rm65_closed_loop.sh`
- 快照 SHA-256：`9c0ec355574166b0d3464c45f2be7bcecff02d535c894eb2e0c53025baec01f6`
- 总行数：124
- 程序作用：一次闭环实验的进程编排器：启动模型服务、等待端口、启动 IsaacLab、传入验证参数并检查报告。
- 推荐读法：它不实现模型或物理，而是保证两个 Python 进程按正确顺序和环境变量运行。

## 功能块地图

- 第 1-21 行：严格 Shell 模式、目录、checkpoint 和实验参数
- 第 23-31 行：检查端口工具并设置 Python/GPU 内存环境
- 第 32-72 行：启动或复用 WebSocket policy server，并做超时/清理
- 第 74-118 行：用固定参数启动 RM65 IsaacLab 闭环
- 第 120-124 行：独立检查 task_report 并打印结果目录

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```bash
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env bash
# 【L0002】启用严格 Shell 模式：命令失败、未定义变量或管道失败都会让脚本停止。
set -euo pipefail
# 【L0003】空行：分隔“严格 Shell 模式、目录、checkpoint 和实验参数”中的逻辑段，让结构更容易看清。

# 【L0004】计算并保存变量 `project_root`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 【L0005】计算并保存变量 `isaaclab_root`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
# 【L0006】计算并保存变量 `openpi_root`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
# 【L0007】计算并保存变量 `rm65_root`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"
# 【L0008】给变量 `checkpoint` 赋值：一次训练保存的模型参数目录。
checkpoint="${1:?usage: $0 CHECKPOINT [EPISODE_DIR] [TRANSFER_ANGLE] [SOURCE_X] [SOURCE_Y] [PROMPT]}"
# 【L0009】计算并保存变量 `episode_dir`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
episode_dir="${2:-datasets/rm65_pi05_eval/episode_000000}"
# 【L0010】计算并保存变量 `transfer_angle`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
transfer_angle="${3:-0.8}"
# 【L0011】计算并保存变量 `source_offset_x`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
source_offset_x="${4:-0.0}"
# 【L0012】计算并保存变量 `source_offset_y`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
source_offset_y="${5:-0.0}"
# 【L0013】计算并保存变量 `episode_prompt`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
episode_prompt="${6:-pick up the block and place it on the target}"
# 【L0014】计算并保存变量 `policy_port`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
policy_port="${POLICY_PORT:-8000}"
# 【L0015】计算并保存变量 `policy_server_mode`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
policy_server_mode="${POLICY_SERVER_MODE:-managed}"
# 【L0016】计算并保存变量 `repo_id`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
repo_id="${RM65_REPO_ID:-local/rm65_sim_train}"
# 【L0017】计算并保存变量 `gripper_open_threshold`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
gripper_open_threshold="${POLICY_GRIPPER_OPEN_THRESHOLD:-0.12}"
# 【L0018】计算并保存变量 `server_log`；该值服务于“严格 Shell 模式、目录、checkpoint 和实验参数”。
server_log="$project_root/outputs/rm65_pi05_policy_server.log"
# 【L0019】空行：分隔“严格 Shell 模式、目录、checkpoint 和实验参数”中的逻辑段，让结构更容易看清。

# 【L0020】执行“严格 Shell 模式、目录、checkpoint 和实验参数”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
cd "$project_root"
# 【L0021】调用 `mkdir`：创建目录。本行位于“严格 Shell 模式、目录、checkpoint 和实验参数”。
mkdir -p outputs "$(dirname "$episode_dir")"
# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if ! command -v ss >/dev/null 2>&1; then
# 【L0024】向终端打印状态或最终结果路径。
  echo "ERROR: ss is required to check the policy port" >&2
# 【L0025】执行“检查端口工具并设置 Python/GPU 内存环境”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit 2
# 【L0026】结束或闭合当前语法结构；它属于“检查端口工具并设置 Python/GPU 内存环境”。
fi
# 【L0027】设置并导出环境变量，让随后启动的 Python/JAX 进程读取该配置。
export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
# 【L0028】源码注释：Reserve half of the 16 GB GPU for Isaac Sim. This is the same split that
# Reserve half of the 16 GB GPU for Isaac Sim. This is the same split that
# 【L0029】源码注释：passed the earlier Franka + pi0.5 closed-loop evaluation on this workstation.
# passed the earlier Franka + pi0.5 closed-loop evaluation on this workstation.
# 【L0030】设置并导出环境变量，让随后启动的 Python/JAX 进程读取该配置。
export XLA_PYTHON_CLIENT_MEM_FRACTION="${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.50}"
# 【L0031】空行：分隔“检查端口工具并设置 Python/GPU 内存环境”中的逻辑段，让结构更容易看清。

# 【L0032】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if [[ "$policy_server_mode" == "managed" ]]; then
# 【L0033】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
  if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0034】向终端打印状态或最终结果路径。
    echo "ERROR: policy port $policy_port is already in use" >&2
# 【L0035】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    exit 2
# 【L0036】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  fi
# 【L0037】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "$openpi_root/.venv/bin/python" -u scripts/serve_rm65_policy.py \
# 【L0038】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --checkpoint "$checkpoint" \
# 【L0039】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --repo-id "$repo_id" \
# 【L0040】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    --port "$policy_port" \
# 【L0041】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    >"$server_log" 2>&1 &
# 【L0042】计算并保存变量 `server_pid`；该值服务于“启动或复用 WebSocket policy server，并做超时/清理”。
  server_pid=$!
# 【L0043】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  cleanup() {
# 【L0044】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    kill "$server_pid" 2>/dev/null || true
# 【L0045】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    wait "$server_pid" 2>/dev/null || true
# 【L0046】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  }
# 【L0047】注册退出/中断清理函数，避免模型服务残留在后台。
  trap cleanup EXIT INT TERM
# 【L0048】for 循环：依次处理序列中的每个元素/时间步/episode/case。
  for _ in $(seq 1 180); do
# 【L0049】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if ! kill -0 "$server_pid" 2>/dev/null; then
# 【L0050】向终端打印状态或最终结果路径。
      echo "ERROR: policy server stopped during startup" >&2
# 【L0051】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
      tail -n 80 "$server_log" >&2
# 【L0052】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
      exit 1
# 【L0053】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
    fi
# 【L0054】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0055】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
      break
# 【L0056】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
    fi
# 【L0057】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sleep 1
# 【L0058】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  done
# 【L0059】追加条件分支：前面的条件不成立时再检查这一条件。
elif [[ "$policy_server_mode" != "external" ]]; then
# 【L0060】向终端打印状态或最终结果路径。
  echo "ERROR: POLICY_SERVER_MODE must be managed or external" >&2
# 【L0061】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit 2
# 【L0062】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
fi
# 【L0063】空行：分隔“启动或复用 WebSocket policy server，并做超时/清理”中的逻辑段，让结构更容易看清。

# 【L0064】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if ! ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0065】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
  if [[ "$policy_server_mode" == "managed" ]]; then
# 【L0066】向终端打印状态或最终结果路径。
    echo "ERROR: policy server did not listen within 180 seconds" >&2
# 【L0067】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    tail -n 80 "$server_log" >&2
# 【L0068】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  else
# 【L0069】向终端打印状态或最终结果路径。
    echo "ERROR: no external policy server is listening on port $policy_port" >&2
# 【L0070】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  fi
# 【L0071】执行“启动或复用 WebSocket policy server，并做超时/清理”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  exit 1
# 【L0072】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
fi
# 【L0073】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0074】计算并保存变量 `checkpoint_id`；该值服务于“用固定参数启动 RM65 IsaacLab 闭环”。
checkpoint_id="$(basename "$(dirname "$checkpoint")")/$(basename "$checkpoint")"
# 【L0075】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
"$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
# 【L0076】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --usd generated/rm65_4c2_wide_pads.usd \
# 【L0077】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
# 【L0078】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --description "$rm65_root/rm65_robot_description.yaml" \
# 【L0079】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --output "$episode_dir/task_report.json" \
# 【L0080】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --record-episode-dir "$episode_dir" \
# 【L0081】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --record-stride-steps 12 \
# 【L0082】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --record-images \
# 【L0083】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --episode-prompt "$episode_prompt" \
# 【L0084】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --robot-base-z-m 0.65 \
# 【L0085】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --transfer-joint-1-rad "$transfer_angle" \
# 【L0086】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --source-offset-x-m "$source_offset_x" \
# 【L0087】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --source-offset-y-m "$source_offset_y" \
# 【L0088】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --pregrasp-distance-m 0.09 \
# 【L0089】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --grasp-world-offset-x-m -0.04 \
# 【L0090】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --grasp-world-offset-z-m -0.053 \
# 【L0091】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --grasp-orientation-mode top_down \
# 【L0092】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --top-down-yaw-rad 0.0 \
# 【L0093】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --top-down-tilt-rad 0.0 \
# 【L0094】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --top-down-blend 1.0 \
# 【L0095】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --top-down-ik-multistart 128 \
# 【L0096】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --natural-source-gravity \
# 【L0097】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --enable-moving-gripper-gravity \
# 【L0098】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --arm-effort-limit-sim 1000 \
# 【L0099】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --arm-stiffness 5000 \
# 【L0100】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --arm-damping 300 \
# 【L0101】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --gripper-effort-limit-sim 200 \
# 【L0102】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --gripper-stiffness 2000 \
# 【L0103】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --gripper-damping 80 \
# 【L0104】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --gripper-close-target-rad 0.80 \
# 【L0105】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --lift-mode cartesian_vertical \
# 【L0106】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --cartesian-lift-height-m 0.04 \
# 【L0107】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --target-support-mode wide_platform \
# 【L0108】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --target-collision-enable-stage after_transfer \
# 【L0109】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --place-descent \
# 【L0110】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --place-descent-distance-m 0.13 \
# 【L0111】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --place-waypoint-steps 180 \
# 【L0112】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --unassisted-release \
# 【L0113】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --pi05-closed-loop \
# 【L0114】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --policy-gripper-open-threshold "$gripper_open_threshold" \
# 【L0115】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --policy-port "$policy_port" \
# 【L0116】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --policy-checkpoint-id "$checkpoint_id" \
# 【L0117】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --headless \
# 【L0118】执行“用固定参数启动 RM65 IsaacLab 闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --enable_cameras
# 【L0119】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0120】执行“独立检查 task_report 并打印结果目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
python3 scripts/check_closed_loop_task_report.py \
# 【L0121】执行“独立检查 task_report 并打印结果目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  "$episode_dir/task_report.json" \
# 【L0122】执行“独立检查 task_report 并打印结果目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
  --checkpoint-id "$checkpoint_id"
# 【L0123】空行：分隔“独立检查 task_report 并打印结果目录”中的逻辑段，让结构更容易看清。

# 【L0124】向终端打印状态或最终结果路径。
echo "RM65_PI05_EVALUATION_EPISODE=$episode_dir"
```
