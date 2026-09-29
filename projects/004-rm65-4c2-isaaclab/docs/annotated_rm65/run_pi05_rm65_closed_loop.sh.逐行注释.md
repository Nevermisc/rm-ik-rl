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

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```bash
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env bash` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env bash
# 【L0002】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】启用 Bash 选项 `set -euo pipefail`；本项目通常用 `-euo pipefail` 让命令失败、未定义变量或管道失败立即停止流水线。
set -euo pipefail
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格 Shell 模式、目录、checkpoint 和实验参数”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `project_root`。右侧语法为：`"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `project_root`，它在本项目中表示本功能块中的 `project_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`；`cd` 表示本功能块中的 `cd` 值；`dirname` 表示本功能块中的 `dirname` 值；`BASH_SOURCE` 表示源位置相关值。
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 【L0005】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `isaaclab_root`。右侧语法为：`"${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `isaaclab_root`，它在本项目中表示本功能块中的 `isaaclab_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"`；`ISAACLAB_ROOT` 表示本功能块中的 `ISAACLAB_ROOT` 值；`HOME` 表示本功能块中的 `HOME` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
isaaclab_root="${ISAACLAB_ROOT:-$HOME/robot-learning/IsaacLab}"
# 【L0006】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `openpi_root`。右侧语法为：`"${OPENPI_ROOT:-$HOME/robot-learning/openpi}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `openpi_root`，它在本项目中表示本功能块中的 `openpi_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${OPENPI_ROOT:-$HOME/robot-learning/openpi}"`；`OPENPI_ROOT` 表示本功能块中的 `OPENPI_ROOT` 值；`HOME` 表示本功能块中的 `HOME` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
# 【L0007】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rm65_root`。右侧语法为：`"${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `rm65_root`，它在本项目中表示本功能块中的 `rm65_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"`；`RM65_ROOT` 表示RM65 机械约束或项目常量；`HOME` 表示本功能块中的 `HOME` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
rm65_root="${RM65_ROOT:-$HOME/robot-learning/rm-ik-rl}"
# 【L0008】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`"${1:?usage: $0 CHECKPOINT [EPISODE_DIR] [TRANSFER_ANGLE] [SOURCE_X] [SOURCE_Y] [PROMPT]}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${1:?usage: $0 CHECKPOINT [EPISODE_DIR] [TRANSFER_ANGLE] [SOURCE_X] [SOURCE_Y] [PROMPT]}"`；`usage` 表示本功能块中的 `usage` 值；`CHECKPOINT` 表示模型检查点相关值；`EPISODE_DIR` 表示一条轨迹相关值。
checkpoint="${1:?usage: $0 CHECKPOINT [EPISODE_DIR] [TRANSFER_ANGLE] [SOURCE_X] [SOURCE_Y] [PROMPT]}"
# 【L0009】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_dir`。右侧语法为：`"${2:-datasets/rm65_pi05_eval/episode_000000}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `episode_dir`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${2:-datasets/rm65_pi05_eval/episode_000000}"`；`datasets` 表示本功能块中的 `datasets` 值；`rm65_pi05_eval` 表示本功能块中的 `rm65_pi05_eval` 值；`episode_000000` 表示一条轨迹相关值。
episode_dir="${2:-datasets/rm65_pi05_eval/episode_000000}"
# 【L0010】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `transfer_angle`。右侧语法为：`"${3:-0.8}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `transfer_angle`，它在本项目中表示本功能块中的 `transfer_angle` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `"${3:-0.8}"` 的结果保存下来，供当前功能块后续使用。
transfer_angle="${3:-0.8}"
# 【L0011】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_offset_x`。右侧语法为：`"${4:-0.0}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `source_offset_x`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `"${4:-0.0}"` 的结果保存下来，供当前功能块后续使用。
source_offset_x="${4:-0.0}"
# 【L0012】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_offset_y`。右侧语法为：`"${5:-0.0}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `source_offset_y`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `"${5:-0.0}"` 的结果保存下来，供当前功能块后续使用。
source_offset_y="${5:-0.0}"
# 【L0013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_prompt`。右侧语法为：`"${6:-pick up the block and place it on the target}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `episode_prompt`，它在本项目中表示当前 episode 发送给 π0.5 的自然语言任务指令；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${6:-pick up the block and place it on the target}"`；`pick` 表示本功能块中的 `pick` 值；`up` 表示本功能块中的 `up` 值；`the` 表示本功能块中的 `the` 值。
episode_prompt="${6:-pick up the block and place it on the target}"
# 【L0014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_port`。右侧语法为：`"${POLICY_PORT:-8000}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `policy_port`，它在本项目中表示OpenPI WebSocket policy server 监听的 TCP 端口；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${POLICY_PORT:-8000}"`；`POLICY_PORT` 表示策略相关值。
policy_port="${POLICY_PORT:-8000}"
# 【L0015】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_server_mode`。右侧语法为：`"${POLICY_SERVER_MODE:-managed}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `policy_server_mode`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${POLICY_SERVER_MODE:-managed}"`；`POLICY_SERVER_MODE` 表示策略相关值；`managed` 表示本功能块中的 `managed` 值。
policy_server_mode="${POLICY_SERVER_MODE:-managed}"
# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id`。右侧语法为：`"${RM65_REPO_ID:-local/rm65_sim_train}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `repo_id`，它在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_REPO_ID:-local/rm65_sim_train}"`；`RM65_REPO_ID` 表示RM65 机械约束或项目常量；`local` 表示本功能块中的 `local` 值；`rm65_sim_train` 表示仿真相关值。
repo_id="${RM65_REPO_ID:-local/rm65_sim_train}"
# 【L0017】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_open_threshold`。右侧语法为：`"${POLICY_GRIPPER_OPEN_THRESHOLD:-0.12}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `gripper_open_threshold`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${POLICY_GRIPPER_OPEN_THRESHOLD:-0.12}"`；`POLICY_GRIPPER_OPEN_THRESHOLD` 表示策略、夹爪相关值。
gripper_open_threshold="${POLICY_GRIPPER_OPEN_THRESHOLD:-0.12}"
# 【L0018】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_log`。右侧语法为：`"$project_root/outputs/rm65_pi05_policy_server.log"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `server_log`，它在本项目中表示本功能块中的 `server_log` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/outputs/rm65_pi05_policy_server.log"`；`project_root` 表示本功能块中的 `project_root` 值；`outputs` 表示本功能块中的 `outputs` 值；`rm65_pi05_policy_server` 表示策略相关值。
server_log="$project_root/outputs/rm65_pi05_policy_server.log"
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格 Shell 模式、目录、checkpoint 和实验参数”中的逻辑段，让结构更容易看清。

# 【L0020】语法拆解：`cd "$project_root"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `cd "$project_root"` 接入当前完整语句；`cd` 表示本功能块中的 `cd` 值；`project_root` 表示本功能块中的 `project_root` 值。在“严格 Shell 模式、目录、checkpoint 和实验参数”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
cd "$project_root"
# 【L0021】语法拆解：表达式 `mkdir -p outputs "$(dirname "$episode_dir")"` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `mkdir -p outputs "$(dirname "$episode_dir")"`。`mkdir` 表示本功能块中的 `mkdir` 值；`p` 表示本功能块中的 `p` 值。
mkdir -p outputs "$(dirname "$episode_dir")"
# 【L0022】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】语法拆解：`if` 要求条件 `! command -v ss >/dev/null 2>&1; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `! command -v ss >/dev/null 2>&1; then` 是否成立；`command` 表示控制命令相关值；`v` 表示本功能块中的 `v` 值；`ss` 表示本功能块中的 `ss` 值
if ! command -v ss >/dev/null 2>&1; then
# 【L0024】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: ss is required to check the policy port" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "ERROR: ss is required to check the policy port" >&2
# 【L0025】语法拆解：`exit 2` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 2` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“检查端口工具并设置 Python/GPU 内存环境”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit 2
# 【L0026】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“检查端口工具并设置 Python/GPU 内存环境”。
fi
# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `export PYTHONPATH`。右侧语法为：`"$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】设置并导出环境变量 `PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"`；随后启动的 OpenPI/JAX/Isaac 进程会从环境读取这个运行配置。
export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
# 【L0028】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：Reserve half of the 16 GB GPU for Isaac Sim. This is the same split that
# Reserve half of the 16 GB GPU for Isaac Sim. This is the same split that
# 【L0029】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：passed the earlier Franka + pi0.5 closed-loop evaluation on this workstation.
# passed the earlier Franka + pi0.5 closed-loop evaluation on this workstation.
# 【L0030】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `export XLA_PYTHON_CLIENT_MEM_FRACTION`。右侧语法为：`"${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.50}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】设置并导出环境变量 `XLA_PYTHON_CLIENT_MEM_FRACTION="${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.50}"`；随后启动的 OpenPI/JAX/Isaac 进程会从环境读取这个运行配置。
export XLA_PYTHON_CLIENT_MEM_FRACTION="${XLA_PYTHON_CLIENT_MEM_FRACTION:-0.50}"
# 【L0031】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“检查端口工具并设置 Python/GPU 内存环境”中的逻辑段，让结构更容易看清。

# 【L0032】语法拆解：`if` 要求条件 `[[ "$policy_server_mode" == "managed" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ "$policy_server_mode" == "managed" ]]; then` 是否成立；`policy_server_mode` 表示策略相关值；`managed` 表示本功能块中的 `managed` 值；`then` 表示本功能块中的 `then` 值
if [[ "$policy_server_mode" == "managed" ]]; then
# 【L0033】语法拆解：`if` 要求条件 `ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 是否成立；`ss` 表示本功能块中的 `ss` 值；`ltn` 表示本功能块中的 `ltn` 值；`sport` 表示本功能块中的 `sport` 值
  if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0034】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: policy port $policy_port is already in use" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
    echo "ERROR: policy port $policy_port is already in use" >&2
# 【L0035】语法拆解：`exit 2` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 2` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    exit 2
# 【L0036】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  fi
# 【L0037】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$openpi_root/.venv/bin/python" -u scripts/serve_rm65_policy.py \`；在“启动或复用 WebSocket policy server，并做超时/清理”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
  "$openpi_root/.venv/bin/python" -u scripts/serve_rm65_policy.py \
# 【L0038】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--checkpoint`，值为 `"$checkpoint"`；该参数表示一次训练保存的模型参数目录，会改变“启动或复用 WebSocket policy server，并做超时/清理”的运行配置。
    --checkpoint "$checkpoint" \
# 【L0039】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--repo-id`，值为 `"$repo_id"`；该参数表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会改变“启动或复用 WebSocket policy server，并做超时/清理”的运行配置。
    --repo-id "$repo_id" \
# 【L0040】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--port`，值为 `"$policy_port"`；该参数表示本功能块中的 `port` 值，会改变“启动或复用 WebSocket policy server，并做超时/清理”的运行配置。
    --port "$policy_port" \
# 【L0041】语法拆解：表达式 `>"$server_log" 2>&1 &` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `>"$server_log" 2>&1 &` 接入当前完整语句；`server_log` 表示本功能块中的 `server_log` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    >"$server_log" 2>&1 &
# 【L0042】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_pid`。右侧语法为：`$!` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `server_pid`，它在本项目中表示本功能块中的 `server_pid` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `$!` 的结果保存下来，供当前功能块后续使用。
  server_pid=$!
# 【L0043】语法拆解：`cleanup() {` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `cleanup() {` 接入当前完整语句；`cleanup` 表示本功能块中的 `cleanup` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  cleanup() {
# 【L0044】语法拆解：表达式 `kill "$server_pid" 2>/dev/null || true` 使用运算符 `/`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `kill "$server_pid" 2>/dev/null || true` 接入当前完整语句；`kill` 表示本功能块中的 `kill` 值；`server_pid` 表示本功能块中的 `server_pid` 值；`dev` 表示本功能块中的 `dev` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    kill "$server_pid" 2>/dev/null || true
# 【L0045】语法拆解：表达式 `wait "$server_pid" 2>/dev/null || true` 使用运算符 `/`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `wait "$server_pid" 2>/dev/null || true` 接入当前完整语句；`wait` 表示本功能块中的 `wait` 值；`server_pid` 表示本功能块中的 `server_pid` 值；`dev` 表示本功能块中的 `dev` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    wait "$server_pid" 2>/dev/null || true
# 【L0046】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  }
# 【L0047】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `cleanup EXIT INT TERM`；脚本结束或被中断时清理 π0.5 服务等后台进程。
  trap cleanup EXIT INT TERM
# 【L0048】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for _ in $(seq 1 180); do` 中给出的序列，逐项完成“启动或复用 WebSocket policy server，并做超时/清理”。
  for _ in $(seq 1 180); do
# 【L0049】语法拆解：`if` 要求条件 `! kill -0 "$server_pid" 2>/dev/null; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `! kill -0 "$server_pid" 2>/dev/null; then` 是否成立；`kill` 表示本功能块中的 `kill` 值；`server_pid` 表示本功能块中的 `server_pid` 值；`dev` 表示本功能块中的 `dev` 值
    if ! kill -0 "$server_pid" 2>/dev/null; then
# 【L0050】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: policy server stopped during startup" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
      echo "ERROR: policy server stopped during startup" >&2
# 【L0051】语法拆解：表达式 `tail -n 80 "$server_log" >&2` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `tail -n 80 "$server_log" >&2` 接入当前完整语句；`tail` 表示本功能块中的 `tail` 值；`n` 表示本功能块中的 `n` 值；`server_log` 表示本功能块中的 `server_log` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
      tail -n 80 "$server_log" >&2
# 【L0052】语法拆解：`exit 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 1` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
      exit 1
# 【L0053】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
    fi
# 【L0054】语法拆解：`if` 要求条件 `ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 是否成立；`ss` 表示本功能块中的 `ss` 值；`ltn` 表示本功能块中的 `ltn` 值；`sport` 表示本功能块中的 `sport` 值
    if ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0055】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“启动或复用 WebSocket policy server，并做超时/清理”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
      break
# 【L0056】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
    fi
# 【L0057】语法拆解：`sleep 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `sleep 1` 接入当前完整语句；`sleep` 表示本功能块中的 `sleep` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    sleep 1
# 【L0058】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  done
# 【L0059】语法拆解：`elif` 要求条件 `[[ "$policy_server_mode" != "external" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】前面的条件未成立时，继续判断 `[[ "$policy_server_mode" != "external" ]]; then` 是否成立；`policy_server_mode` 表示策略相关值；`external` 表示外部相机相关值；`then` 表示本功能块中的 `then` 值
elif [[ "$policy_server_mode" != "external" ]]; then
# 【L0060】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: POLICY_SERVER_MODE must be managed or external" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "ERROR: POLICY_SERVER_MODE must be managed or external" >&2
# 【L0061】语法拆解：`exit 2` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 2` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit 2
# 【L0062】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
fi
# 【L0063】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动或复用 WebSocket policy server，并做超时/清理”中的逻辑段，让结构更容易看清。

# 【L0064】语法拆解：`if` 要求条件 `! ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `! ss -ltn "sport = :$policy_port" | grep -q LISTEN; then` 是否成立；`ss` 表示本功能块中的 `ss` 值；`ltn` 表示本功能块中的 `ltn` 值；`sport` 表示本功能块中的 `sport` 值
if ! ss -ltn "sport = :$policy_port" | grep -q LISTEN; then
# 【L0065】语法拆解：`if` 要求条件 `[[ "$policy_server_mode" == "managed" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ "$policy_server_mode" == "managed" ]]; then` 是否成立；`policy_server_mode` 表示策略相关值；`managed` 表示本功能块中的 `managed` 值；`then` 表示本功能块中的 `then` 值
  if [[ "$policy_server_mode" == "managed" ]]; then
# 【L0066】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: policy server did not listen within 180 seconds" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
    echo "ERROR: policy server did not listen within 180 seconds" >&2
# 【L0067】语法拆解：表达式 `tail -n 80 "$server_log" >&2` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `tail -n 80 "$server_log" >&2` 接入当前完整语句；`tail` 表示本功能块中的 `tail` 值；`n` 表示本功能块中的 `n` 值；`server_log` 表示本功能块中的 `server_log` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    tail -n 80 "$server_log" >&2
# 【L0068】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】声明/传入参数 `else`；在本项目中它表示本功能块中的 `else` 值。
  else
# 【L0069】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"ERROR: no external policy server is listening on port $policy_port" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
    echo "ERROR: no external policy server is listening on port $policy_port" >&2
# 【L0070】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
  fi
# 【L0071】语法拆解：`exit 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 1` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“启动或复用 WebSocket policy server，并做超时/清理”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit 1
# 【L0072】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动或复用 WebSocket policy server，并做超时/清理”。
fi
# 【L0073】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0074】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint_id`。右侧语法为：`"$(basename "$(dirname "$checkpoint")")/$(basename "$checkpoint")"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `checkpoint_id`，它在本项目中表示模型检查点相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$(basename "$(dirname "$checkpoint")")/$(basename "$checkpoint")"`；`basename` 表示本功能块中的 `basename` 值；`dirname` 表示本功能块中的 `dirname` 值；`checkpoint` 表示一次训练保存的模型参数目录。
checkpoint_id="$(basename "$(dirname "$checkpoint")")/$(basename "$checkpoint")"
# 【L0075】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \`；在“用固定参数启动 RM65 IsaacLab 闭环”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
"$isaaclab_root/isaaclab.sh" -p scripts/run_pick_place_baseline.py \
# 【L0076】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--usd`，值为 `generated/rm65_4c2_wide_pads.usd`；该参数表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --usd generated/rm65_4c2_wide_pads.usd \
# 【L0077】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--urdf`，值为 `"$rm65_root/assets/RM65-B/urdf/RM65-B.urdf"`；该参数表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --urdf "$rm65_root/assets/RM65-B/urdf/RM65-B.urdf" \
# 【L0078】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--description`，值为 `"$rm65_root/rm65_robot_description.yaml"`；该参数表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --description "$rm65_root/rm65_robot_description.yaml" \
# 【L0079】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$episode_dir/task_report.json"`；该参数表示输出文件路径，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --output "$episode_dir/task_report.json" \
# 【L0080】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--record-episode-dir`，值为 `"$episode_dir"`；该参数表示一条轨迹相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --record-episode-dir "$episode_dir" \
# 【L0081】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--record-stride-steps`，值为 `12`；该参数表示每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --record-stride-steps 12 \
# 【L0082】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--record-images`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `record_images` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --record-images \
# 【L0083】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--episode-prompt`，值为 `"$episode_prompt"`；该参数表示当前 episode 发送给 π0.5 的自然语言任务指令，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --episode-prompt "$episode_prompt" \
# 【L0084】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--robot-base-z-m`，值为 `0.65`；该参数表示本功能块中的 `robot_base_z_m` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --robot-base-z-m 0.65 \
# 【L0085】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--transfer-joint-1-rad`，值为 `"$transfer_angle"`；该参数表示关节相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --transfer-joint-1-rad "$transfer_angle" \
# 【L0086】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--source-offset-x-m`，值为 `"$source_offset_x"`；该参数表示源位置相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --source-offset-x-m "$source_offset_x" \
# 【L0087】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--source-offset-y-m`，值为 `"$source_offset_y"`；该参数表示源位置相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --source-offset-y-m "$source_offset_y" \
# 【L0088】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--pregrasp-distance-m`，值为 `0.09`；该参数表示预抓取位姿到实际抓取位姿之间的直线距离，单位米，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --pregrasp-distance-m 0.09 \
# 【L0089】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--grasp-world-offset-x-m`，值为 `-0.04`；该参数表示本功能块中的 `grasp_world_offset_x_m` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --grasp-world-offset-x-m -0.04 \
# 【L0090】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--grasp-world-offset-z-m`，值为 `-0.053`；该参数表示本功能块中的 `grasp_world_offset_z_m` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --grasp-world-offset-z-m -0.053 \
# 【L0091】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--grasp-orientation-mode`，值为 `top_down`；该参数表示本功能块中的 `grasp_orientation_mode` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --grasp-orientation-mode top_down \
# 【L0092】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--top-down-yaw-rad`，值为 `0.0`；该参数表示本功能块中的 `top_down_yaw_rad` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --top-down-yaw-rad 0.0 \
# 【L0093】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--top-down-tilt-rad`，值为 `0.0`；该参数表示本功能块中的 `top_down_tilt_rad` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --top-down-tilt-rad 0.0 \
# 【L0094】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--top-down-blend`，值为 `1.0`；该参数表示本功能块中的 `top_down_blend` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --top-down-blend 1.0 \
# 【L0095】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--top-down-ik-multistart`，值为 `128`；该参数表示本功能块中的 `top_down_ik_multistart` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --top-down-ik-multistart 128 \
# 【L0096】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--natural-source-gravity`，值为 `布尔开关（出现即启用）`；该参数表示源位置相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --natural-source-gravity \
# 【L0097】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--enable-moving-gripper-gravity`，值为 `布尔开关（出现即启用）`；该参数表示夹爪相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --enable-moving-gripper-gravity \
# 【L0098】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--arm-effort-limit-sim`，值为 `1000`；该参数表示仿真相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --arm-effort-limit-sim 1000 \
# 【L0099】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--arm-stiffness`，值为 `5000`；该参数表示本功能块中的 `arm_stiffness` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --arm-stiffness 5000 \
# 【L0100】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--arm-damping`，值为 `300`；该参数表示本功能块中的 `arm_damping` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --arm-damping 300 \
# 【L0101】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--gripper-effort-limit-sim`，值为 `200`；该参数表示夹爪、仿真相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --gripper-effort-limit-sim 200 \
# 【L0102】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--gripper-stiffness`，值为 `2000`；该参数表示夹爪相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --gripper-stiffness 2000 \
# 【L0103】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--gripper-damping`，值为 `80`；该参数表示夹爪相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --gripper-damping 80 \
# 【L0104】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--gripper-close-target-rad`，值为 `0.80`；该参数表示夹爪、目标相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --gripper-close-target-rad 0.80 \
# 【L0105】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--lift-mode`，值为 `cartesian_vertical`；该参数表示本功能块中的 `lift_mode` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --lift-mode cartesian_vertical \
# 【L0106】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--cartesian-lift-height-m`，值为 `0.04`；该参数表示本功能块中的 `cartesian_lift_height_m` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --cartesian-lift-height-m 0.04 \
# 【L0107】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--target-support-mode`，值为 `wide_platform`；该参数表示目标相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --target-support-mode wide_platform \
# 【L0108】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--target-collision-enable-stage`，值为 `after_transfer`；该参数表示目标相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --target-collision-enable-stage after_transfer \
# 【L0109】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--place-descent`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `place_descent` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --place-descent \
# 【L0110】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--place-descent-distance-m`，值为 `0.13`；该参数表示本功能块中的 `place_descent_distance_m` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --place-descent-distance-m 0.13 \
# 【L0111】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--place-waypoint-steps`，值为 `180`；该参数表示步数相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --place-waypoint-steps 180 \
# 【L0112】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--unassisted-release`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `unassisted_release` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --unassisted-release \
# 【L0113】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--pi05-closed-loop`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `pi05_closed_loop` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --pi05-closed-loop \
# 【L0114】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--policy-gripper-open-threshold`，值为 `"$gripper_open_threshold"`；该参数表示策略、夹爪相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --policy-gripper-open-threshold "$gripper_open_threshold" \
# 【L0115】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--policy-port`，值为 `"$policy_port"`；该参数表示OpenPI WebSocket policy server 监听的 TCP 端口，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --policy-port "$policy_port" \
# 【L0116】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--policy-checkpoint-id`，值为 `"$checkpoint_id"`；该参数表示策略、模型检查点相关值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --policy-checkpoint-id "$checkpoint_id" \
# 【L0117】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--headless`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `headless` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --headless \
# 【L0118】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--enable_cameras`，值为 `布尔开关（出现即启用）`；该参数表示本功能块中的 `enable_cameras` 值，会改变“用固定参数启动 RM65 IsaacLab 闭环”的运行配置。
  --enable_cameras
# 【L0119】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0120】语法拆解：表达式 `python3 scripts/check_closed_loop_task_report.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/check_closed_loop_task_report.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`check_closed_loop_task_report` 表示报告相关值。在“独立检查 task_report 并打印结果目录”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/check_closed_loop_task_report.py \
# 【L0121】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$episode_dir/task_report.json" \`；在“独立检查 task_report 并打印结果目录”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
  "$episode_dir/task_report.json" \
# 【L0122】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--checkpoint-id`，值为 `"$checkpoint_id"`；该参数表示模型检查点相关值，会改变“独立检查 task_report 并打印结果目录”的运行配置。
  --checkpoint-id "$checkpoint_id"
# 【L0123】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“独立检查 task_report 并打印结果目录”中的逻辑段，让结构更容易看清。

# 【L0124】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "RM65_PI05_EVALUATION_EPISODE`。右侧语法为：`$episode_dir"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"RM65_PI05_EVALUATION_EPISODE=$episode_dir"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "RM65_PI05_EVALUATION_EPISODE=$episode_dir"
```
