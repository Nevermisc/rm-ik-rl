# `check_closed_loop_task_report.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/check_closed_loop_task_report.py`
- 快照 SHA-256：`d34bde70e527666adfb72e8fb388f703163cb4ffdd97b91e7bbfdd5d57471766`
- 总行数：35
- 程序作用：命令行验收入口：读取单条 task_report，调用独立 validator，并用退出码阻止失败结果进入后续步骤。
- 推荐读法：它与 closed_loop_report.py 分离，使验证逻辑既能被测试导入，也能由 Shell 调用。

## 功能块地图

- 第 1-16 行：依赖、项目路径和独立 validator
- 第 19-31 行：读取报告、校验 checkpoint 和全部成功条件并返回退出码
- 第 34-35 行：脚本入口

## 函数/类索引

- `main()`：第 19-31 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Fail unless an RM65 pi0.5 task report independently satisfies all criteria."""
# 【L0003】空行：分隔“依赖、项目路径和独立 validator”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和独立 validator”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0009】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0010】空行：分隔“依赖、项目路径和独立 validator”中的逻辑段，让结构更容易看清。

# 【L0011】空行：分隔“依赖、项目路径和独立 validator”中的逻辑段，让结构更容易看清。

# 【L0012】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和独立 validator”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0013】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0014】执行“依赖、项目路径和独立 validator”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0015】空行：分隔“依赖、项目路径和独立 validator”中的逻辑段，让结构更容易看清。

# 【L0016】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.closed_loop_report import validate_closed_loop_task_report
# 【L0017】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】定义函数 main；其职责属于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”，缩进块是函数体。
def main() -> int:
# 【L0020】计算并保存变量 `parser`；该值服务于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0021】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("report", type=Path)
# 【L0022】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--checkpoint-id", required=True)
# 【L0023】计算并保存变量 `args`；该值服务于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”。
    args = parser.parse_args()
# 【L0024】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.report.is_file():
# 【L0025】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise FileNotFoundError(f"closed-loop task report missing: {args.report}")
# 【L0026】调用 `read_text`：从磁盘读取文本。本行位于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”。
    report = json.loads(args.report.read_text(encoding="utf-8"))
# 【L0027】计算并保存变量 `validation`；该值服务于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”。
    validation = validate_closed_loop_task_report(
# 【L0028】执行“读取报告、校验 checkpoint 和全部成功条件并返回退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        report, expected_checkpoint_id=args.checkpoint_id
# 【L0029】结束或闭合当前语法结构；它属于“读取报告、校验 checkpoint 和全部成功条件并返回退出码”。
    )
# 【L0030】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(validation, indent=2))
# 【L0031】结束当前函数并把结果交给调用者；这里完成“读取报告、校验 checkpoint 和全部成功条件并返回退出码”的输出。
    return 0 if validation["execution_verified"] else 2
# 【L0032】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0033】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0034】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0035】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
