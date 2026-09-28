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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Run or resume a machine-readable scripted-expert collection plan on Linux."""
# 【L0003】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 subprocess：启动和管理另一个系统进程；后面的代码会调用其中的类或函数。
import subprocess
# 【L0009】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0010】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0011】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0012】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和 episode validator”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0013】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0014】执行“依赖、项目路径和 episode validator”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0015】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0016】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.expert_episode import validate_episode
# 【L0017】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】定义函数 completed_episode；其职责属于“判断已有 episode 是否真的完整、成功且属于当前 case”，缩进块是函数体。
def completed_episode(directory: Path, case_id: str) -> bool:
# 【L0020】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not (directory / "metadata.json").is_file() or not (
# 【L0021】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        directory / "task_report.json"
# 【L0022】开始一个缩进代码块或键值结构；该块负责“判断已有 episode 是否真的完整、成功且属于当前 case”。
    ).is_file():
# 【L0023】结束当前函数并把结果交给调用者；这里完成“判断已有 episode 是否真的完整、成功且属于当前 case”的输出。
        return False
# 【L0024】计算并保存变量 `validation`；该值服务于“判断已有 episode 是否真的完整、成功且属于当前 case”。
    validation = validate_episode(directory, require_images=True)
# 【L0025】调用 `read_text`：从磁盘读取文本。本行位于“判断已有 episode 是否真的完整、成功且属于当前 case”。
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0026】调用 `read_text`：从磁盘读取文本。本行位于“判断已有 episode 是否真的完整、成功且属于当前 case”。
    task = json.loads((directory / "task_report.json").read_text(encoding="utf-8"))
# 【L0027】结束当前函数并把结果交给调用者；这里完成“判断已有 episode 是否真的完整、成功且属于当前 case”的输出。
    return bool(
# 【L0028】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        validation["status"] == "pass"
# 【L0029】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and metadata.get("metadata", {}).get("task_success") is True
# 【L0030】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and metadata.get("metadata", {}).get("collection_case_id") == case_id
# 【L0031】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and task.get("status") == "pass"
# 【L0032】执行“判断已有 episode 是否真的完整、成功且属于当前 case”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and task.get("unassisted_full_task_complete") is True
# 【L0033】结束或闭合当前语法结构；它属于“判断已有 episode 是否真的完整、成功且属于当前 case”。
    )
# 【L0034】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0035】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0036】定义函数 main；其职责属于“读取采集计划并按 train/validation 过滤”，缩进块是函数体。
def main() -> int:
# 【L0037】计算并保存变量 `parser`；该值服务于“读取采集计划并按 train/validation 过滤”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0038】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--plan", type=Path, required=True)
# 【L0039】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--dataset-root", type=Path, required=True)
# 【L0040】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--split", choices=("train", "validation", "all"), default="all")
# 【L0041】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--max-cases", type=int)
# 【L0042】计算并保存变量 `args`；该值服务于“读取采集计划并按 train/validation 过滤”。
    args = parser.parse_args()
# 【L0043】调用 `read_text`：从磁盘读取文本。本行位于“读取采集计划并按 train/validation 过滤”。
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
# 【L0044】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if plan.get("format") != "rm65_expert_collection_plan_v1":
# 【L0045】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("unsupported collection plan")
# 【L0046】计算并保存变量 `cases`；该值服务于“读取采集计划并按 train/validation 过滤”。
    cases = [
# 【L0047】执行“读取采集计划并按 train/validation 过滤”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        item for item in plan["cases"] if args.split == "all" or item["split"] == args.split
# 【L0048】结束或闭合当前语法结构；它属于“读取采集计划并按 train/validation 过滤”。
    ]
# 【L0049】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.max_cases is not None:
# 【L0050】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.max_cases <= 0:
# 【L0051】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("--max-cases must be positive")
# 【L0052】计算并保存变量 `cases`；该值服务于“读取采集计划并按 train/validation 过滤”。
        cases = cases[: args.max_cases]
# 【L0053】调用 `mkdir`：创建目录。本行位于“读取采集计划并按 train/validation 过滤”。
    args.dataset_root.mkdir(parents=True, exist_ok=True)
# 【L0054】计算并保存变量 `completed`；该值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
    completed = 0
# 【L0055】计算并保存变量 `skipped`；该值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
    skipped = 0
# 【L0056】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for case in cases:
# 【L0057】计算并保存变量 `directory`；该值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        directory = args.dataset_root / f"episode_{case['episode_index']:06d}"
# 【L0058】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if completed_episode(directory, case["case_id"]):
# 【L0059】执行“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            skipped += 1
# 【L0060】跳过本次循环剩余语句，继续处理下一个候选项。
            continue
# 【L0061】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if directory.exists():
# 【L0062】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L0063】执行“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                f"existing episode is incomplete or belongs to another case: {directory}"
# 【L0064】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            )
# 【L0065】计算并保存变量 `command`；该值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        command = [
# 【L0066】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            "bash",
# 【L0067】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),
# 【L0068】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(directory),
# 【L0069】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["transfer_joint_1_rad"]),
# 【L0070】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["source_offset_x_m"]),
# 【L0071】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            str(case["source_offset_y_m"]),
# 【L0072】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            case["prompt"],
# 【L0073】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        ]
# 【L0074】执行“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
# 【L0075】计算并保存变量 `manifest_path`；该值服务于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        manifest_path = directory / "metadata.json"
# 【L0076】调用 `read_text`：从磁盘读取文本。本行位于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
# 【L0077】执行“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        manifest["metadata"].update(
# 【L0078】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            {
# 【L0079】定义字典/JSON 字段 `collection_case_id`；它把“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的结果用稳定键名记录下来。
                "collection_case_id": case["case_id"],
# 【L0080】定义字典/JSON 字段 `collection_split`；它把“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的结果用稳定键名记录下来。
                "collection_split": case["split"],
# 【L0081】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
            }
# 【L0082】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        )
# 【L0083】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“逐 case 运行脚本专家、补充 metadata 并做采集后复核”。
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
# 【L0084】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not completed_episode(directory, case["case_id"]):
# 【L0085】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed post-run validation: {directory}")
# 【L0086】执行“逐 case 运行脚本专家、补充 metadata 并做采集后复核”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        completed += 1
# 【L0087】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0088】定义字典/JSON 字段 `status`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0089】定义字典/JSON 字段 `plan`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "plan": str(args.plan.resolve()),
# 【L0090】定义字典/JSON 字段 `dataset_root`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "dataset_root": str(args.dataset_root.resolve()),
# 【L0091】定义字典/JSON 字段 `requested_case_count`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "requested_case_count": len(cases),
# 【L0092】定义字典/JSON 字段 `newly_completed_count`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "newly_completed_count": completed,
# 【L0093】定义字典/JSON 字段 `already_completed_count`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "already_completed_count": skipped,
# 【L0094】定义字典/JSON 字段 `simulation_only`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L0095】定义字典/JSON 字段 `expert`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "expert": "scripted",
# 【L0096】定义字典/JSON 字段 `pi05_used`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "pi05_used": False,
# 【L0097】定义字典/JSON 字段 `real_robot_command_sent`；它把“输出采集/复用统计和退出码”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L0098】结束或闭合当前语法结构；它属于“输出采集/复用统计和退出码”。
    }
# 【L0099】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(report, indent=2))
# 【L0100】结束当前函数并把结果交给调用者；这里完成“输出采集/复用统计和退出码”的输出。
    return 0
# 【L0101】空行：分隔“输出采集/复用统计和退出码”中的逻辑段，让结构更容易看清。

# 【L0102】空行：分隔“输出采集/复用统计和退出码”中的逻辑段，让结构更容易看清。

# 【L0103】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0104】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
