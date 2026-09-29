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

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```bash
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env bash` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env bash
# 【L0002】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】启用 Bash 选项 `set -euo pipefail`；本项目通常用 `-euo pipefail` 让命令失败、未定义变量或管道失败立即停止流水线。
set -euo pipefail
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格 Shell 模式、目录和可覆盖流水线参数”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `project_root`。右侧语法为：`"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `project_root`，它在本项目中表示本功能块中的 `project_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`；`cd` 表示本功能块中的 `cd` 值；`dirname` 表示本功能块中的 `dirname` 值；`BASH_SOURCE` 表示源位置相关值。
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 【L0005】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `openpi_root`。右侧语法为：`"${OPENPI_ROOT:-$HOME/robot-learning/openpi}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `openpi_root`，它在本项目中表示本功能块中的 `openpi_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${OPENPI_ROOT:-$HOME/robot-learning/openpi}"`；`OPENPI_ROOT` 表示本功能块中的 `OPENPI_ROOT` 值；`HOME` 表示本功能块中的 `HOME` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
openpi_root="${OPENPI_ROOT:-$HOME/robot-learning/openpi}"
# 【L0006】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `training_pid`。右侧语法为：`"${1:?usage: $0 TRAINING_PID}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `training_pid`，它在本项目中表示本功能块中的 `training_pid` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${1:?usage: $0 TRAINING_PID}"`；`usage` 表示本功能块中的 `usage` 值；`TRAINING_PID` 表示本功能块中的 `TRAINING_PID` 值。
training_pid="${1:?usage: $0 TRAINING_PID}"
# 【L0007】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `training_report`。右侧语法为：`"${RM65_TRAINING_REPORT:-$project_root/results/pi05_rm65_formal_30k.json}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `training_report`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_TRAINING_REPORT:-$project_root/results/pi05_rm65_formal_30k.json}"`；`RM65_TRAINING_REPORT` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值。
training_report="${RM65_TRAINING_REPORT:-$project_root/results/pi05_rm65_formal_30k.json}"
# 【L0008】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id`。右侧语法为：`"${RM65_REPO_ID:-local/rm65_sim_train}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `repo_id`，它在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_REPO_ID:-local/rm65_sim_train}"`；`RM65_REPO_ID` 表示RM65 机械约束或项目常量；`local` 表示本功能块中的 `local` 值；`rm65_sim_train` 表示仿真相关值。
repo_id="${RM65_REPO_ID:-local/rm65_sim_train}"
# 【L0009】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `norm_stats`。右侧语法为：`"${RM65_NORM_STATS:-$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `norm_stats`，它在本项目中表示最终得到的 state/actions 归一化统计；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_NORM_STATS:-$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json}"`；`RM65_NORM_STATS` 表示RM65 机械约束或项目常量；`openpi_root` 表示本功能块中的 `openpi_root` 值；`assets` 表示本功能块中的 `assets` 值。
norm_stats="${RM65_NORM_STATS:-$openpi_root/assets/pi05_rm65_lora/$repo_id/norm_stats.json}"
# 【L0010】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result_prefix`。右侧语法为：`"${RM65_RESULT_PREFIX:-pi05_rm65_formal}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `result_prefix`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_RESULT_PREFIX:-pi05_rm65_formal}"`；`RM65_RESULT_PREFIX` 表示RM65 机械约束或项目常量；`pi05_rm65_formal` 表示本功能块中的 `pi05_rm65_formal` 值。
result_prefix="${RM65_RESULT_PREFIX:-pi05_rm65_formal}"
# 【L0011】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `evaluation_root`。右侧语法为：`"${RM65_EVALUATION_ROOT:-$project_root/datasets/rm65_pi05_eval_v1}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `evaluation_root`，它在本项目中表示本功能块中的 `evaluation_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_EVALUATION_ROOT:-$project_root/datasets/rm65_pi05_eval_v1}"`；`RM65_EVALUATION_ROOT` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`datasets` 表示本功能块中的 `datasets` 值。
evaluation_root="${RM65_EVALUATION_ROOT:-$project_root/datasets/rm65_pi05_eval_v1}"
# 【L0012】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `evaluation_summary`。右侧语法为：`"${RM65_EVALUATION_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `evaluation_summary`，它在本项目中表示本功能块中的 `evaluation_summary` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_EVALUATION_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"`；`RM65_EVALUATION_SUMMARY` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值。
evaluation_summary="${RM65_EVALUATION_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"
# 【L0013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint_report`。右侧语法为：`"$project_root/results/${result_prefix}_checkpoint_inference.json"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `checkpoint_report`，它在本项目中表示模型检查点、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/results/${result_prefix}_checkpoint_inference.json"`；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值；`result_prefix` 表示结果相关值。
checkpoint_report="$project_root/results/${result_prefix}_checkpoint_inference.json"
# 【L0014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `offline_report`。右侧语法为：`"$project_root/results/${result_prefix}_offline_validation.json"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `offline_report`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/results/${result_prefix}_offline_validation.json"`；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值；`result_prefix` 表示结果相关值。
offline_report="$project_root/results/${result_prefix}_offline_validation.json"
# 【L0015】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `artifact_report`。右侧语法为：`"$project_root/results/${result_prefix}_policy_artifact.json"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `artifact_report`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/results/${result_prefix}_policy_artifact.json"`；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值；`result_prefix` 表示结果相关值。
artifact_report="$project_root/results/${result_prefix}_policy_artifact.json"
# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `taxonomy_report`。右侧语法为：`"$project_root/results/${result_prefix}_failure_taxonomy.json"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `taxonomy_report`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/results/${result_prefix}_failure_taxonomy.json"`；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值；`result_prefix` 表示结果相关值。
taxonomy_report="$project_root/results/${result_prefix}_failure_taxonomy.json"
# 【L0017】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `baseline_summary`。右侧语法为：`"${RM65_BASELINE_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `baseline_summary`，它在本项目中表示本功能块中的 `baseline_summary` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_BASELINE_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"`；`RM65_BASELINE_SUMMARY` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值。
baseline_summary="${RM65_BASELINE_SUMMARY:-$project_root/results/rm65_pi05_eval_v1_summary.json}"
# 【L0018】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `comparison_report`。右侧语法为：`"${RM65_COMPARISON_REPORT:-$project_root/results/${result_prefix}_comparison_to_v1.json}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `comparison_report`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_COMPARISON_REPORT:-$project_root/results/${result_prefix}_comparison_to_v1.json}"`；`RM65_COMPARISON_REPORT` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`results` 表示本功能块中的 `results` 值。
comparison_report="${RM65_COMPARISON_REPORT:-$project_root/results/${result_prefix}_comparison_to_v1.json}"
# 【L0019】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sentinel`。右侧语法为：`"${RM65_PIPELINE_STATUS:-$project_root/outputs/rm65_post_training_pipeline.status}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `sentinel`，它在本项目中表示本功能块中的 `sentinel` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_PIPELINE_STATUS:-$project_root/outputs/rm65_post_training_pipeline.status}"`；`RM65_PIPELINE_STATUS` 表示RM65 机械约束或项目常量；`project_root` 表示本功能块中的 `project_root` 值；`outputs` 表示本功能块中的 `outputs` 值。
sentinel="${RM65_PIPELINE_STATUS:-$project_root/outputs/rm65_post_training_pipeline.status}"
# 【L0020】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_window`。右侧语法为：`"${RM65_POLICY_WINDOW:-false}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `policy_window`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_POLICY_WINDOW:-false}"`；`RM65_POLICY_WINDOW` 表示RM65 机械约束或项目常量；`false` 表示本功能块中的 `false` 值。
policy_window="${RM65_POLICY_WINDOW:-false}"
# 【L0021】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first_case_timeout_seconds`。右侧语法为：`"${RM65_FIRST_CASE_TIMEOUT_SECONDS:-1200}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `first_case_timeout_seconds`，它在本项目中表示秒相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"${RM65_FIRST_CASE_TIMEOUT_SECONDS:-1200}"`；`RM65_FIRST_CASE_TIMEOUT_SECONDS` 表示RM65 机械约束或项目常量。
first_case_timeout_seconds="${RM65_FIRST_CASE_TIMEOUT_SECONDS:-1200}"
# 【L0022】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格 Shell 模式、目录和可覆盖流水线参数”中的逻辑段，让结构更容易看清。

# 【L0023】语法拆解：`cd "$project_root"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `cd "$project_root"` 接入当前完整语句；`cd` 表示本功能块中的 `cd` 值；`project_root` 表示本功能块中的 `project_root` 值。在“严格 Shell 模式、目录和可覆盖流水线参数”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
cd "$project_root"
# 【L0024】语法拆解：表达式 `mkdir -p outputs results` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `mkdir -p outputs results`。`mkdir` 表示本功能块中的 `mkdir` 值；`p` 表示本功能块中的 `p` 值。
mkdir -p outputs results
# 【L0025】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"initialization"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"initialization"`；`initialization` 表示本功能块中的 `initialization` 值。
current_stage="initialization"
# 【L0026】语法拆解：`on_error() {` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `on_error() {` 接入当前完整语句；`on_error` 表示本功能块中的 `on_error` 值。在“失败哨兵、参数检查和 policy-window 选项”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
on_error() {
# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `exit_code`。右侧语法为：`$?` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `exit_code`，它在本项目中表示本功能块中的 `exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `$?` 的结果保存下来，供当前功能块后续使用。
  exit_code=$?
# 【L0028】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "failed: stage`。右侧语法为：`$current_stage exit_code=$exit_code" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"failed: stage=$current_stage exit_code=$exit_code" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "failed: stage=$current_stage exit_code=$exit_code" | tee "$sentinel"
# 【L0029】语法拆解：`exit "$exit_code"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit "$exit_code"` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值；`exit_code` 表示本功能块中的 `exit_code` 值。在“失败哨兵、参数检查和 policy-window 选项”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit "$exit_code"
# 【L0030】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
}
# 【L0031】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `on_error ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap on_error ERR
# 【L0032】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“失败哨兵、参数检查和 policy-window 选项”中的逻辑段，让结构更容易看清。

# 【L0033】语法拆解：`if` 要求条件 `[[ ! "$first_case_timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ ! "$first_case_timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then` 是否成立；`first_case_timeout_seconds` 表示秒相关值；`then` 表示本功能块中的 `then` 值
if [[ ! "$first_case_timeout_seconds" =~ ^[1-9][0-9]*$ ]]; then
# 【L0034】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"RM65_FIRST_CASE_TIMEOUT_SECONDS must be a positive integer" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "RM65_FIRST_CASE_TIMEOUT_SECONDS must be a positive integer" >&2
# 【L0035】语法拆解：`false` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `false`；在本项目中它表示本功能块中的 `false` 值。
  false
# 【L0036】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0037】语法拆解：`if` 要求条件 `[[ "$policy_window" != "true" && "$policy_window" != "false" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ "$policy_window" != "true" && "$policy_window" != "false" ]]; then` 是否成立；`policy_window` 表示策略相关值；`true` 表示本功能块中的 `true` 值；`false` 表示本功能块中的 `false` 值
if [[ "$policy_window" != "true" && "$policy_window" != "false" ]]; then
# 【L0038】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"RM65_POLICY_WINDOW must be true or false" >&2` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "RM65_POLICY_WINDOW must be true or false" >&2
# 【L0039】语法拆解：`false` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `false`；在本项目中它表示本功能块中的 `false` 值。
  false
# 【L0040】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `offline_view_args`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `offline_view_args`，它在本项目中表示本功能块中的 `offline_view_args` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `()` 的结果保存下来，供当前功能块后续使用。
offline_view_args=()
# 【L0042】语法拆解：`if` 要求条件 `[[ "$policy_window" == "true" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ "$policy_window" == "true" ]]; then` 是否成立；`policy_window` 表示策略相关值；`true` 表示本功能块中的 `true` 值；`then` 表示本功能块中的 `then` 值
if [[ "$policy_window" == "true" ]]; then
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `offline_view_args`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `offline_view_args`，它在本项目中表示本功能块中的 `offline_view_args` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(--policy-window)`；`policy` 表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；`window` 表示本功能块中的 `window` 值。
  offline_view_args=(--policy-window)
# 【L0044】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“失败哨兵、参数检查和 policy-window 选项”。
fi
# 【L0045】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0046】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"wait_for_training"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"wait_for_training"`；`wait_for_training` 表示本功能块中的 `wait_for_training` 值。
current_stage="wait_for_training"
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "waiting_for_training_pid`。右侧语法为：`$training_pid" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"waiting_for_training_pid=$training_pid" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "waiting_for_training_pid=$training_pid" | tee "$sentinel"
# 【L0048】语法拆解：`while` 在条件为 True 时反复运行下面缩进块；末尾冒号打开循环体。
# 【项目含义】只要 `kill -0 "$training_pid" 2>/dev/null; do` 仍成立就重复后面的控制/等待步骤；判断 `kill -0 "$training_pid" 2>/dev/null; do` 是否成立；`kill` 表示本功能块中的 `kill` 值；`training_pid` 表示本功能块中的 `training_pid` 值；`dev` 表示本功能块中的 `dev` 值。
while kill -0 "$training_pid" 2>/dev/null; do
# 【L0049】语法拆解：`sleep 30` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `sleep 30` 接入当前完整语句；`sleep` 表示本功能块中的 `sleep` 值。在“等待训练 PID 并从训练报告提取 checkpoint”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  sleep 30
# 【L0050】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
done
# 【L0051】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“等待训练 PID 并从训练报告提取 checkpoint”中的逻辑段，让结构更容易看清。

# 【L0052】语法拆解：`if` 要求条件 `[[ ! -f "$training_report" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ ! -f "$training_report" ]]; then` 是否成立；`f` 表示本功能块中的 `f` 值；`training_report` 表示报告相关值；`then` 表示本功能块中的 `then` 值
if [[ ! -f "$training_report" ]]; then
# 【L0053】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"failed: training report missing: $training_report" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "failed: training report missing: $training_report" | tee "$sentinel"
# 【L0054】语法拆解：`exit 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 1` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“等待训练 PID 并从训练报告提取 checkpoint”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit 1
# 【L0055】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
fi
# 【L0056】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`"$($openpi_root/.venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("status")=="pass", d; print(d["latest_checkpoint"])' "$training_report")"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$($openpi_root/.venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("status")=="pass", d; print(d["latest_checkpoint"])' "$training_report")"`；`openpi_root` 表示本功能块中的 `openpi_root` 值；`venv` 表示本功能块中的 `venv` 值；`bin` 表示本功能块中的 `bin` 值。
checkpoint="$($openpi_root/.venv/bin/python -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d.get("status")=="pass", d; print(d["latest_checkpoint"])' "$training_report")"
# 【L0057】语法拆解：`if` 要求条件 `[[ ! -d "$checkpoint" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ ! -d "$checkpoint" ]]; then` 是否成立；`d` 表示本功能块中的 `d` 值；`checkpoint` 表示一次训练保存的模型参数目录；`then` 表示本功能块中的 `then` 值
if [[ ! -d "$checkpoint" ]]; then
# 【L0058】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"failed: checkpoint missing: $checkpoint" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "failed: checkpoint missing: $checkpoint" | tee "$sentinel"
# 【L0059】语法拆解：`exit 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit 1` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值。在“等待训练 PID 并从训练报告提取 checkpoint”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit 1
# 【L0060】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“等待训练 PID 并从训练报告提取 checkpoint”。
fi
# 【L0061】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `export PYTHONPATH`。右侧语法为：`"$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】设置并导出环境变量 `PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"`；随后启动的 OpenPI/JAX/Isaac 进程会从环境读取这个运行配置。
export PYTHONPATH="$project_root:$openpi_root/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
# 【L0063】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `validation_episode`。右侧语法为：`"$project_root/datasets/rm65_scripted_v1/episode_000000"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `validation_episode`，它在本项目中表示校验结果、一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"$project_root/datasets/rm65_scripted_v1/episode_000000"`；`project_root` 表示本功能块中的 `project_root` 值；`datasets` 表示本功能块中的 `datasets` 值；`rm65_scripted_v1` 表示本功能块中的 `rm65_scripted_v1` 值。
validation_episode="$project_root/datasets/rm65_scripted_v1/episode_000000"
# 【L0064】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“单帧 checkpoint 推理和验证集离线评测”中的逻辑段，让结构更容易看清。

# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"single_checkpoint_inference"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"single_checkpoint_inference"`；`single_checkpoint_inference` 表示模型检查点相关值。
current_stage="single_checkpoint_inference"
# 【L0066】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage checkpoint=$checkpoint" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage checkpoint=$checkpoint" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage checkpoint=$checkpoint" | tee "$sentinel"
# 【L0067】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$openpi_root/.venv/bin/python" scripts/validate_rm65_checkpoint.py \`；在“单帧 checkpoint 推理和验证集离线评测”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
"$openpi_root/.venv/bin/python" scripts/validate_rm65_checkpoint.py \
# 【L0068】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--checkpoint`，值为 `"$checkpoint"`；该参数表示一次训练保存的模型参数目录，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --checkpoint "$checkpoint" \
# 【L0069】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--episode`，值为 `"$validation_episode"`；该参数表示一条轨迹相关值，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --episode "$validation_episode" \
# 【L0070】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--repo-id`，值为 `"$repo_id"`；该参数表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --repo-id "$repo_id" \
# 【L0071】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$checkpoint_report"`；该参数表示输出文件路径，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --output "$checkpoint_report"
# 【L0072】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“单帧 checkpoint 推理和验证集离线评测”中的逻辑段，让结构更容易看清。

# 【L0073】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"offline_validation"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"offline_validation"`；`offline_validation` 表示校验结果相关值。
current_stage="offline_validation"
# 【L0074】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0075】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$openpi_root/.venv/bin/python" scripts/evaluate_rm65_checkpoint_offline.py \`；在“单帧 checkpoint 推理和验证集离线评测”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
"$openpi_root/.venv/bin/python" scripts/evaluate_rm65_checkpoint_offline.py \
# 【L0076】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--checkpoint`，值为 `"$checkpoint"`；该参数表示一次训练保存的模型参数目录，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --checkpoint "$checkpoint" \
# 【L0077】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--dataset-root`，值为 `datasets/rm65_scripted_v1`；该参数表示数据集相关值，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --dataset-root datasets/rm65_scripted_v1 \
# 【L0078】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--split`，值为 `validation`；该参数表示本功能块中的 `split` 值，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --split validation \
# 【L0079】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--repo-id`，值为 `"$repo_id"`；该参数表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --repo-id "$repo_id" \
# 【L0080】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--frames-per-episode`，值为 `5`；该参数表示一条轨迹相关值，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --frames-per-episode 5 \
# 【L0081】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$offline_report"`；该参数表示输出文件路径，会改变“单帧 checkpoint 推理和验证集离线评测”的运行配置。
  --output "$offline_report" \
# 【L0082】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"${offline_view_args[@]}"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“单帧 checkpoint 推理和验证集离线评测”中的帮助说明、错误原因、任务名称或报告文字。
  "${offline_view_args[@]}"
# 【L0083】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0084】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"simulation_manifest"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"simulation_manifest"`；`simulation_manifest` 表示本功能块中的 `simulation_manifest` 值。
current_stage="simulation_manifest"
# 【L0085】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0086】语法拆解：表达式 `python3 scripts/build_rm65_policy_artifact.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/build_rm65_policy_artifact.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`build_rm65_policy_artifact` 表示策略相关值。在“构建策略资产清单并验证仿真 gate/评测计划”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/build_rm65_policy_artifact.py \
# 【L0087】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--training-report`，值为 `"$training_report"`；该参数表示报告相关值，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --training-report "$training_report" \
# 【L0088】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--norm-stats`，值为 `"$norm_stats"`；该参数表示最终得到的 state/actions 归一化统计，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --norm-stats "$norm_stats" \
# 【L0089】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$artifact_report"`；该参数表示输出文件路径，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --output "$artifact_report"
# 【L0090】语法拆解：表达式 `python3 scripts/check_policy_execution_gate.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/check_policy_execution_gate.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`check_policy_execution_gate` 表示策略相关值。在“构建策略资产清单并验证仿真 gate/评测计划”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/check_policy_execution_gate.py \
# 【L0091】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"$artifact_report" --target simulation`；Python 会把相邻字符串自动拼接，外层参数会把它用作“构建策略资产清单并验证仿真 gate/评测计划”中的帮助说明、错误原因、任务名称或报告文字。
  "$artifact_report" --target simulation
# 【L0092】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“构建策略资产清单并验证仿真 gate/评测计划”中的逻辑段，让结构更容易看清。

# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"evaluation_plan_validation"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"evaluation_plan_validation"`；`evaluation_plan_validation` 表示校验结果相关值。
current_stage="evaluation_plan_validation"
# 【L0094】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0095】语法拆解：表达式 `python3 scripts/validate_rm65_evaluation_plan.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/validate_rm65_evaluation_plan.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`validate_rm65_evaluation_plan` 表示本功能块中的 `validate_rm65_evaluation_plan` 值。在“构建策略资产清单并验证仿真 gate/评测计划”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/validate_rm65_evaluation_plan.py \
# 【L0096】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--collection-plan`，值为 `config/rm65_expert_collection_plan_v1.json`；该参数表示本功能块中的 `collection_plan` 值，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --collection-plan config/rm65_expert_collection_plan_v1.json \
# 【L0097】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--evaluation-plan`，值为 `config/rm65_pi05_evaluation_plan_v1.json`；该参数表示本功能块中的 `evaluation_plan` 值，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --evaluation-plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0098】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `results/rm65_pi05_evaluation_plan_validation.json`；该参数表示输出文件路径，会改变“构建策略资产清单并验证仿真 gate/评测计划”的运行配置。
  --output results/rm65_pi05_evaluation_plan_validation.json
# 【L0099】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0100】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"first_closed_loop"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"first_closed_loop"`；`first_closed_loop` 表示本功能块中的 `first_closed_loop` 值。
current_stage="first_closed_loop"
# 【L0101】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage timeout_seconds=$first_case_timeout_seconds" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage timeout_seconds=$first_case_timeout_seconds" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage timeout_seconds=$first_case_timeout_seconds" | tee "$sentinel"
# 【L0102】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把表达式/参数 `set +e` 接入当前完整语句；`set` 表示本功能块中的 `set` 值；`e` 表示本功能块中的 `e` 值。在“先运行一条闭环，但无论任务成败都继续完整 suite”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
set +e
# 【L0103】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `- ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap - ERR
# 【L0104】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timeout --signal`。右侧语法为：表达式 `TERM --kill-after=30s "${first_case_timeout_seconds}s" \` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `timeout --signal=TERM --kill-after=30s "${first_case_timeout_seconds}s" \` 接入当前完整语句；`timeout` 表示本功能块中的 `timeout` 值；`signal` 表示本功能块中的 `signal` 值；`TERM` 表示本功能块中的 `TERM` 值。在“先运行一条闭环，但无论任务成败都继续完整 suite”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
timeout --signal=TERM --kill-after=30s "${first_case_timeout_seconds}s" \
# 【L0105】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `env RM65_REPO_ID`。右侧语法为：表达式 `"$repo_id" bash scripts/run_pi05_rm65_closed_loop.sh \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `env RM65_REPO_ID="$repo_id" bash scripts/run_pi05_rm65_closed_loop.sh \` 接入当前完整语句；`env` 表示本功能块中的 `env` 值；`RM65_REPO_ID` 表示RM65 机械约束或项目常量；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。在“先运行一条闭环，但无论任务成败都继续完整 suite”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  env RM65_REPO_ID="$repo_id" bash scripts/run_pi05_rm65_closed_loop.sh \
# 【L0106】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"$checkpoint" \`；Python 会把相邻字符串自动拼接，外层参数会把它用作“先运行一条闭环，但无论任务成败都继续完整 suite”中的帮助说明、错误原因、任务名称或报告文字。
  "$checkpoint" \
# 【L0107】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"$evaluation_root/eval_000" \`；在“先运行一条闭环，但无论任务成败都继续完整 suite”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
  "$evaluation_root/eval_000" \
# 【L0108】语法拆解：表达式 `0.65 -0.0075 -0.0075 \` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `0.65 -0.0075 -0.0075 \` 接入当前完整语句；它补全了上一行尚未结束的数据或调用。在“先运行一条闭环，但无论任务成败都继续完整 suite”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  0.65 -0.0075 -0.0075 \
# 【L0109】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"pick up the block and place it on the target"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“先运行一条闭环，但无论任务成败都继续完整 suite”中的帮助说明、错误原因、任务名称或报告文字。
  "pick up the block and place it on the target"
# 【L0110】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first_case_exit_code`。右侧语法为：`$?` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `first_case_exit_code`，它在本项目中表示本功能块中的 `first_case_exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `$?` 的结果保存下来，供当前功能块后续使用。
first_case_exit_code=$?
# 【L0111】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `on_error ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap on_error ERR
# 【L0112】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】启用 Bash 选项 `set -e`；本项目通常用 `-euo pipefail` 让命令失败、未定义变量或管道失败立即停止流水线。
set -e
# 【L0113】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage exit_code=$first_case_exit_code continuing_to_full_suite" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage exit_code=$first_case_exit_code continuing_to_full_suite" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage exit_code=$first_case_exit_code continuing_to_full_suite" | tee "$sentinel"
# 【L0114】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0115】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"twenty_case_closed_loop_suite"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"twenty_case_closed_loop_suite"`；`twenty_case_closed_loop_suite` 表示本功能块中的 `twenty_case_closed_loop_suite` 值。
current_stage="twenty_case_closed_loop_suite"
# 【L0116】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0117】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把表达式/参数 `set +e` 接入当前完整语句；`set` 表示本功能块中的 `set` 值；`e` 表示本功能块中的 `e` 值。在“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
set +e
# 【L0118】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `- ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap - ERR
# 【L0119】语法拆解：表达式 `python3 scripts/run_pi05_rm65_closed_loop_suite.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/run_pi05_rm65_closed_loop_suite.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`run_pi05_rm65_closed_loop_suite` 表示本功能块中的 `run_pi05_rm65_closed_loop_suite` 值。在“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/run_pi05_rm65_closed_loop_suite.py \
# 【L0120】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--checkpoint`，值为 `"$checkpoint"`；该参数表示一次训练保存的模型参数目录，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --checkpoint "$checkpoint" \
# 【L0121】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--repo-id`，值为 `"$repo_id"`；该参数表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --repo-id "$repo_id" \
# 【L0122】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--plan`，值为 `config/rm65_pi05_evaluation_plan_v1.json`；该参数表示从 JSON 读取的专家采集计划或闭环评测计划，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0123】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output-root`，值为 `"$evaluation_root"`；该参数表示输出相关值，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --output-root "$evaluation_root" \
# 【L0124】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--summary`，值为 `"$evaluation_summary"`；该参数表示本功能块中的 `summary` 值，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --summary "$evaluation_summary"
# 【L0125】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `suite_exit_code`。右侧语法为：`$?` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `suite_exit_code`，它在本项目中表示本功能块中的 `suite_exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `$?` 的结果保存下来，供当前功能块后续使用。
suite_exit_code=$?
# 【L0126】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `on_error ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap on_error ERR
# 【L0127】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】启用 Bash 选项 `set -e`；本项目通常用 `-euo pipefail` 让命令失败、未定义变量或管道失败立即停止流水线。
set -e
# 【L0128】语法拆解：表达式 `python3 scripts/analyze_rm65_closed_loop_failures.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/analyze_rm65_closed_loop_failures.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`analyze_rm65_closed_loop_failures` 表示本功能块中的 `analyze_rm65_closed_loop_failures` 值。在“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/analyze_rm65_closed_loop_failures.py \
# 【L0129】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--plan`，值为 `config/rm65_pi05_evaluation_plan_v1.json`；该参数表示从 JSON 读取的专家采集计划或闭环评测计划，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0130】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--episode-root`，值为 `"$evaluation_root"`；该参数表示一条轨迹相关值，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --episode-root "$evaluation_root" \
# 【L0131】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$taxonomy_report"`；该参数表示输出文件路径，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
  --output "$taxonomy_report"
# 【L0132】语法拆解：`if` 要求条件 `[[ -f "$baseline_summary" ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ -f "$baseline_summary" ]]; then` 是否成立；`f` 表示本功能块中的 `f` 值；`baseline_summary` 表示本功能块中的 `baseline_summary` 值；`then` 表示本功能块中的 `then` 值
if [[ -f "$baseline_summary" ]]; then
# 【L0133】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"compare_to_v1"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"compare_to_v1"`；`compare_to_v1` 表示本功能块中的 `compare_to_v1` 值。
  current_stage="compare_to_v1"
# 【L0134】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "stage=$current_stage" | tee "$sentinel"
# 【L0135】语法拆解：表达式 `python3 scripts/compare_rm65_closed_loop_runs.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/compare_rm65_closed_loop_runs.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`compare_rm65_closed_loop_runs` 表示本功能块中的 `compare_rm65_closed_loop_runs` 值。在“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  python3 scripts/compare_rm65_closed_loop_runs.py \
# 【L0136】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--baseline`，值为 `"$baseline_summary"`；该参数表示本功能块中的 `baseline` 值，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
    --baseline "$baseline_summary" \
# 【L0137】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--candidate`，值为 `"$evaluation_summary"`；该参数表示本功能块中的 `candidate` 值，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
    --candidate "$evaluation_summary" \
# 【L0138】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--plan`，值为 `config/rm65_pi05_evaluation_plan_v1.json`；该参数表示从 JSON 读取的专家采集计划或闭环评测计划，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
    --plan config/rm65_pi05_evaluation_plan_v1.json \
# 【L0139】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$comparison_report"`；该参数表示输出文件路径，会改变“20 条闭环、失败分类、与 v1 比较并保留真实退出码”的运行配置。
    --output "$comparison_report"
# 【L0140】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
fi
# 【L0141】语法拆解：`if` 要求条件 `[[ "$suite_exit_code" -ne 0 ]]; then` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `[[ "$suite_exit_code" -ne 0 ]]; then` 是否成立；`suite_exit_code` 表示本功能块中的 `suite_exit_code` 值；`ne` 表示本功能块中的 `ne` 值；`then` 表示本功能块中的 `then` 值
if [[ "$suite_exit_code" -ne 0 ]]; then
# 【L0142】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"twenty_case_closed_loop_suite"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"twenty_case_closed_loop_suite"`；`twenty_case_closed_loop_suite` 表示本功能块中的 `twenty_case_closed_loop_suite` 值。
  current_stage="twenty_case_closed_loop_suite"
# 【L0143】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `- ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
  trap - ERR
# 【L0144】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "failed: stage`。右侧语法为：`$current_stage exit_code=$suite_exit_code" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"failed: stage=$current_stage exit_code=$suite_exit_code" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
  echo "failed: stage=$current_stage exit_code=$suite_exit_code" | tee "$sentinel"
# 【L0145】语法拆解：`exit "$suite_exit_code"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `exit "$suite_exit_code"` 接入当前完整语句；`exit` 表示本功能块中的 `exit` 值；`suite_exit_code` 表示本功能块中的 `suite_exit_code` 值。在“20 条闭环、失败分类、与 v1 比较并保留真实退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
  exit "$suite_exit_code"
# 【L0146】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“20 条闭环、失败分类、与 v1 比较并保留真实退出码”。
fi
# 【L0147】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0148】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_stage`。右侧语法为：`"final_manifest"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `current_stage`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"final_manifest"`；`final_manifest` 表示本功能块中的 `final_manifest` 值。
current_stage="final_manifest"
# 【L0149】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "stage`。右侧语法为：`$current_stage" | tee "$sentinel"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"stage=$current_stage" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "stage=$current_stage" | tee "$sentinel"
# 【L0150】语法拆解：表达式 `python3 scripts/build_rm65_policy_artifact.py \` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `python3 scripts/build_rm65_policy_artifact.py \` 接入当前完整语句；`python3` 表示本功能块中的 `python3` 值；`scripts` 表示本功能块中的 `scripts` 值；`build_rm65_policy_artifact` 表示策略相关值。在“构建含仿真结果的最终清单并写 pass 哨兵”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
python3 scripts/build_rm65_policy_artifact.py \
# 【L0151】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--training-report`，值为 `"$training_report"`；该参数表示报告相关值，会改变“构建含仿真结果的最终清单并写 pass 哨兵”的运行配置。
  --training-report "$training_report" \
# 【L0152】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--norm-stats`，值为 `"$norm_stats"`；该参数表示最终得到的 state/actions 归一化统计，会改变“构建含仿真结果的最终清单并写 pass 哨兵”的运行配置。
  --norm-stats "$norm_stats" \
# 【L0153】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--simulation-summary`，值为 `"$evaluation_summary"`；该参数表示本功能块中的 `simulation_summary` 值，会改变“构建含仿真结果的最终清单并写 pass 哨兵”的运行配置。
  --simulation-summary "$evaluation_summary" \
# 【L0154】语法拆解：开头 `--` 表示长命令行选项；后面的文本/数字是该选项的值；行尾反斜杠 `\` 表示 Bash 命令下一行继续。
# 【项目含义】给上一条 Bash 命令传入 `--output`，值为 `"$artifact_report"`；该参数表示输出文件路径，会改变“构建含仿真结果的最终清单并写 pass 哨兵”的运行配置。
  --output "$artifact_report"
# 【L0155】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“构建含仿真结果的最终清单并写 pass 哨兵”中的逻辑段，让结构更容易看清。

# 【L0156】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】注册退出处理 `- ERR`；脚本结束或被中断时清理 π0.5 服务等后台进程。
trap - ERR
# 【L0157】语法拆解：这是 Bash 命令；空格分隔命令和参数，`$变量` 会在执行前替换成环境变量或脚本变量的当前值。
# 【项目含义】把 `"pass" | tee "$sentinel"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "pass" | tee "$sentinel"
# 【L0158】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `echo "RM65_POST_TRAINING_PIPELINE`。右侧语法为：`PASS"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `"RM65_POST_TRAINING_PIPELINE=PASS"` 打到终端，告诉操作者当前流水线阶段、命令或最终证据路径。
echo "RM65_POST_TRAINING_PIPELINE=PASS"
```
