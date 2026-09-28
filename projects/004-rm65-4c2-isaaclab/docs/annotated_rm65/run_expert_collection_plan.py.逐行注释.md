# `run_expert_collection_plan.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_expert_collection_plan.py`
- 快照 SHA-256：`8547a7f9e86a0435e2fee003beefb1b8f6f0dd9cc206e5decee3c7c710226e10`
- 总行数：104
- 程序作用：按 45 条机器可读计划采集或恢复脚本专家数据；只复用经过完整验证且属于同一 case 的 episode。
- 推荐读法：先读 completed_episode() 的复用条件，再读 main() 怎样逐 case 调用单条采集脚本并回写 split。

## 功能块地图

- 第 1-16 行：依赖、项目路径和 episode validator
- 第 19-33 行：判断已有 episode 是否真的完整、成功且属于当前 case
- 第 36-53 行：读取采集计划并按 train/validation 过滤
- 第 54-86 行：逐 case 运行脚本专家、补充 metadata 并做采集后复核
- 第 87-104 行：输出采集/复用统计和退出码

## 函数/类索引

- `completed_episode()`：第 19-33 行
- `main()`：第 36-100 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Run or resume a machine-readable scripted-expert collection plan on Linux.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run or resume a machine-readable scripted-expert collection plan on Linux."""
# 【L0003】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】从 `subprocess` 引入 `subprocess`。在这份程序里，`subprocess` 用于启动和管理另一个系统进程；后续出现这些名字时调用的是这里的外部能力。
import subprocess
# 【L0009】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0012】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0013】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0014】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 episode validator”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0015】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0016】从 `openpi_extension` 引入 `validate_episode`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import validate_episode
# 【L0017】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】定义函数 `completed_episode(directory: Path, case_id: str)`；调用者把参数交给它完成“判断已有 episode 是否真的完整、成功且属于当前 case”，后面的缩进代码是具体实现。
def completed_episode(directory: Path, case_id: str) -> bool:
# 【L0020】判断 `not (directory / "metadata.json").is_file() or not (` 是否成立；`directory` 表示目录相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`json` 表示本功能块中的 `json` 值
    if not (directory / "metadata.json").is_file() or not (
# 【L0021】把表达式/参数 `directory / "task_report.json"` 接入当前完整语句；`directory` 表示目录相关值；`task_report` 表示报告相关值；`json` 表示本功能块中的 `json` 值。在“判断已有 episode 是否真的完整、成功且属于当前 case”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        directory / "task_report.json"
# 【L0022】以 `).is_file():` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“判断已有 episode 是否真的完整、成功且属于当前 case”。
    ).is_file():
# 【L0023】结束当前函数并把 `False` 交回调用者；这个值的含义是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
        return False
# 【L0024】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(directory, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`require_images` 表示本功能块中的 `require_images` 值。
    validation = validate_episode(directory, require_images=True)
# 【L0025】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0026】得到 `task`，它在本项目中表示本功能块中的 `task` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    task = json.loads((directory / "task_report.json").read_text(encoding="utf-8"))
# 【L0027】结束当前函数并把 `bool(` 交回调用者；这个值的含义是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    return bool(
# 【L0028】把比较条件 `validation["status"] == "pass"` 接到上一行尚未结束的布尔表达式；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值。比较结果共同决定“判断已有 episode 是否真的完整、成功且属于当前 case”是否通过。
        validation["status"] == "pass"
# 【L0029】把条件 `metadata.get("metadata", {}).get("task_success") is True` 用“并且”接到上一行判断中；判断 `metadata.get("metadata", {}).get("task_success") is True` 是否成立；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`get` 表示本功能块中的 `get` 值；`task_success` 表示成功相关值。所有连接条件共同决定是否进入后续分支。
        and metadata.get("metadata", {}).get("task_success") is True
# 【L0030】把条件 `metadata.get("metadata", {}).get("collection_case_id") == case_id` 用“并且”接到上一行判断中；判断 `metadata.get("metadata", {}).get("collection_case_id") == case_id` 是否成立；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`get` 表示本功能块中的 `get` 值；`collection_case_id` 表示本功能块中的 `collection_case_id` 值。所有连接条件共同决定是否进入后续分支。
        and metadata.get("metadata", {}).get("collection_case_id") == case_id
# 【L0031】把条件 `task.get("status") == "pass"` 用“并且”接到上一行判断中；判断 `task.get("status") == "pass"` 是否成立；`task` 表示本功能块中的 `task` 值；`get` 表示本功能块中的 `get` 值；`status` 表示本功能块中的 `status` 值。所有连接条件共同决定是否进入后续分支。
        and task.get("status") == "pass"
# 【L0032】把条件 `task.get("unassisted_full_task_complete") is True` 用“并且”接到上一行判断中；判断 `task.get("unassisted_full_task_complete") is True` 是否成立；`task` 表示本功能块中的 `task` 值；`get` 表示本功能块中的 `get` 值；`unassisted_full_task_complete` 表示本功能块中的 `unassisted_full_task_complete` 值。所有连接条件共同决定是否进入后续分支。
        and task.get("unassisted_full_task_complete") is True
# 【L0033】结束或闭合当前语法结构；它属于“判断已有 episode 是否真的完整、成功且属于当前 case”。
    )
# 【L0034】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0035】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0036】定义函数 `main()`；调用者把参数交给它完成“读取采集计划并按 train/validation 过滤”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0037】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0038】声明命令行参数 `--plan`；启动脚本可用它改变“读取采集计划并按 train/validation 过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--plan", type=Path, required=True)
# 【L0039】声明命令行参数 `--dataset-root`；启动脚本可用它改变“读取采集计划并按 train/validation 过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--dataset-root", type=Path, required=True)
# 【L0040】声明命令行参数 `--split`；启动脚本可用它改变“读取采集计划并按 train/validation 过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--split", choices=("train", "validation", "all"), default="all")
# 【L0041】声明命令行参数 `--max-cases`；启动脚本可用它改变“读取采集计划并按 train/validation 过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--max-cases", type=int)
# 【L0042】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0043】得到 `plan`，它在本项目中表示从 JSON 读取的专家采集计划或闭环评测计划；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
# 【L0044】判断 `plan.get("format") != "rm65_expert_collection_plan_v1"` 是否成立；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if plan.get("format") != "rm65_expert_collection_plan_v1":
# 【L0045】主动抛出 `ValueError("unsupported collection plan")` 并停止当前路径；说明当前输入违反“读取采集计划并按 train/validation 过滤”要求，不能继续进入仿真、训练或评测。
        raise ValueError("unsupported collection plan")
# 【L0046】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
    cases = [
# 【L0047】这是生成式/推导式 `item for item in plan["cases"] if args.split == "all" or item["split"] == args.split`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`item` 表示本功能块中的 `item` 值；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。产生的序列交给外层列表、字典或函数完成“读取采集计划并按 train/validation 过滤”。
        item for item in plan["cases"] if args.split == "all" or item["split"] == args.split
# 【L0048】结束或闭合当前语法结构；它属于“读取采集计划并按 train/validation 过滤”。
    ]
# 【L0049】检查 `args.max_cases is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.max_cases is not None:
# 【L0050】判断 `args.max_cases <= 0` 是否成立；`max_cases` 表示本功能块中的 `max_cases` 值
        if args.max_cases <= 0:
# 【L0051】主动抛出 `ValueError("--max-cases must be positive")` 并停止当前路径；说明当前输入违反“读取采集计划并按 train/validation 过滤”要求，不能继续进入仿真、训练或评测。
            raise ValueError("--max-cases must be positive")
# 【L0052】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cases[: args.max_cases]`；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表；`max_cases` 表示本功能块中的 `max_cases` 值。
        cases = cases[: args.max_cases]
# 【L0053】调用 `mkdir`：创建目录；本行实际操作 `args.dataset_root.mkdir(parents=True, exist_ok=True)`。`dataset_root` 表示数据集相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
    args.dataset_root.mkdir(parents=True, exist_ok=True)
# 【L0054】得到 `completed`，它在本项目中表示本功能块中的 `completed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    completed = 0
# 【L0055】得到 `skipped`，它在本项目中表示本功能块中的 `skipped` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    skipped = 0
# 【L0056】遍历 `cases`，每次把当前元素放进 `case`；这会逐个处理“逐 case 运行脚本专家、补充 metadata 并做采集后复核”所需的帧、episode、动作或实验 case。
    for case in cases:
# 【L0057】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.dataset_root / f"episode_{case['episode_index']:06d}"`；`dataset_root` 表示数据集相关值；`f` 表示本功能块中的 `f` 值；`episode_` 表示一条轨迹相关值。
        directory = args.dataset_root / f"episode_{case['episode_index']:06d}"
# 【L0058】判断 `completed_episode(directory, case["case_id"])` 是否成立；`completed_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`case` 表示本功能块中的 `case` 值
        if completed_episode(directory, case["case_id"]):
# 【L0059】用 `skipped + 1` 更新 `skipped` 原值；`skipped` 表示本功能块中的 `skipped` 值，常用于累计步数、距离、损失或成功次数。
            skipped += 1
# 【L0060】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中不满足继续条件。
            continue
# 【L0061】判断 `directory.exists()` 是否成立；`directory` 表示目录相关值；`exists` 表示本功能块中的 `exists` 值
        if directory.exists():
# 【L0062】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“逐 case 运行脚本专家、补充 metadata 并做采集后复核”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L0063】把表达式/参数 `f"existing episode is incomplete or belongs to another case: {directory}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`existing` 表示本功能块中的 `existing` 值；`episode` 表示一条轨迹相关值。在“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"existing episode is incomplete or belongs to another case: {directory}"
# 【L0064】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            )
# 【L0065】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        command = [
# 【L0066】提供文本片段 `"bash"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "bash",
# 【L0067】调用 `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),
# 【L0068】调用 `str(directory)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(directory),
# 【L0069】调用 `str(case["transfer_joint_1_rad"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["transfer_joint_1_rad"]),
# 【L0070】调用 `str(case["source_offset_x_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["source_offset_x_m"]),
# 【L0071】调用 `str(case["source_offset_y_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["source_offset_y_m"]),
# 【L0072】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            case["prompt"],
# 【L0073】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        ]
# 【L0074】对 `subprocess` 调用 `run(command, cwd=PROJECT_ROOT, check=True)`：调用 `subprocess` 提供的 `run` 操作。本行产生的修改/返回值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
# 【L0075】得到 `manifest_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `directory / "metadata.json"`；`directory` 表示目录相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`json` 表示本功能块中的 `json` 值。
        manifest_path = directory / "metadata.json"
# 【L0076】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
# 【L0077】开始对 `manifest["metadata"]` 调用多行方法 `update`：用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态；具体参数写在随后几行，用于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        manifest["metadata"].update(
# 【L0078】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            {
# 【L0079】定义字典/JSON 字段 `collection_case_id`，它表示“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的 `collection_case_id` 数据；字段值来自 `case["case_id"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "collection_case_id": case["case_id"],
# 【L0080】定义字典/JSON 字段 `collection_split`，它表示“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的 `collection_split` 数据；字段值来自 `case["split"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "collection_split": case["split"],
# 【L0081】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            }
# 【L0082】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        )
# 【L0083】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")`。`manifest_path` 表示路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
# 【L0084】判断 `not completed_episode(directory, case["case_id"])` 是否成立；`completed_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`case` 表示本功能块中的 `case` 值
        if not completed_episode(directory, case["case_id"]):
# 【L0085】主动抛出 `RuntimeError(f"recorded episode failed post-run validation: {directory}")` 并停止当前路径；说明当前输入违反“逐 case 运行脚本专家、补充 metadata 并做采集后复核”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed post-run validation: {directory}")
# 【L0086】用 `completed + 1` 更新 `completed` 原值；`completed` 表示本功能块中的 `completed` 值，常用于累计步数、距离、损失或成功次数。
        completed += 1
# 【L0087】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0088】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0089】定义字典/JSON 字段 `plan`，它表示“输出采集/复用统计和退出码”中的 `plan` 数据；字段值来自 `str(args.plan.resolve())`，因此保存/传递的是这个表达式当前计算出的结果。
        "plan": str(args.plan.resolve()),
# 【L0090】定义字典/JSON 字段 `dataset_root`，它表示“输出采集/复用统计和退出码”中的 `dataset_root` 数据；字段值来自 `str(args.dataset_root.resolve())`，因此保存/传递的是这个表达式当前计算出的结果。
        "dataset_root": str(args.dataset_root.resolve()),
# 【L0091】定义字典/JSON 字段 `requested_case_count`，它表示“输出采集/复用统计和退出码”中的 `requested_case_count` 数据；字段值来自 `len(cases)`，因此保存/传递的是这个表达式当前计算出的结果。
        "requested_case_count": len(cases),
# 【L0092】定义字典/JSON 字段 `newly_completed_count`，它表示“输出采集/复用统计和退出码”中的 `newly_completed_count` 数据；字段值来自 `completed`，因此保存/传递的是这个表达式当前计算出的结果。
        "newly_completed_count": completed,
# 【L0093】定义字典/JSON 字段 `already_completed_count`，它表示“输出采集/复用统计和退出码”中的 `already_completed_count` 数据；字段值来自 `skipped`，因此保存/传递的是这个表达式当前计算出的结果。
        "already_completed_count": skipped,
# 【L0094】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0095】定义字典/JSON 字段 `expert`，它表示“输出采集/复用统计和退出码”中的 `expert` 数据；字段值来自 `"scripted"`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": "scripted",
# 【L0096】定义字典/JSON 字段 `pi05_used`，它表示“输出采集/复用统计和退出码”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": False,
# 【L0097】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0098】结束或闭合当前语法结构；它属于“输出采集/复用统计和退出码”。
    }
# 【L0099】把 `json.dumps(report, indent=2)` 的当前值/文字输出到终端；它用于观察“输出采集/复用统计和退出码”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2))
# 【L0100】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0101】空行：分隔“输出采集/复用统计和退出码”中的逻辑段，让结构更容易看清。

# 【L0102】空行：分隔“输出采集/复用统计和退出码”中的逻辑段，让结构更容易看清。

# 【L0103】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0104】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“输出采集/复用统计和退出码”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```
