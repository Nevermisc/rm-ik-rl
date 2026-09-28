# `run_pi05_rm65_closed_loop_suite.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_pi05_rm65_closed_loop_suite.py`
- 快照 SHA-256：`adbbf3bde7718417363ff780a74e909adc02c8999df1d9badaa2ad5e6802eb61`
- 总行数：286
- 程序作用：只启动一次 π0.5 服务，按 20 个未见条件运行可恢复批量评测并计算是否达到 80% 门槛。
- 推荐读法：重点理解服务生命周期、已有报告复用、基础设施重试和任务失败不能被重试掩盖。

## 功能块地图

- 第 1-22 行：依赖、项目路径和端口探测
- 第 25-51 行：判断旧报告能否安全复用
- 第 54-97 行：评测参数和范围校验
- 第 99-137 行：载入 checkpoint/评测计划并准备环境变量
- 第 138-167 行：启动一次策略服务并等待就绪
- 第 168-249 行：逐 case 运行、复用报告、仅对缺报告的基础设施故障重试
- 第 250-256 行：无论结果如何都关闭服务
- 第 258-282 行：统计成功率并执行 20 条、80% 门槛
- 第 285-286 行：脚本入口

## 函数/类索引

- `port_open()`：第 19-22 行
- `report_gripper_open_threshold()`：第 25-32 行
- `load_existing_report()`：第 35-51 行
- `main()`：第 54-282 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan."""
# 【L0003】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 os：项目或第三方模块；后面的代码会调用其中的类或函数。
import os
# 【L0009】导入 socket：TCP 端口探测与主机信息；后面的代码会调用其中的类或函数。
import socket
# 【L0010】导入 subprocess：启动和管理另一个系统进程；后面的代码会调用其中的类或函数。
import subprocess
# 【L0011】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0012】导入 time：计时和短暂等待；后面的代码会调用其中的类或函数。
import time
# 【L0013】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0014】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0015】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0016】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和端口探测”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0018】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0019】定义函数 port_open；其职责属于“依赖、项目路径和端口探测”，缩进块是函数体。
def port_open(port: int) -> bool:
# 【L0020】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
# 【L0021】执行“依赖、项目路径和端口探测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        client.settimeout(0.5)
# 【L0022】结束当前函数并把结果交给调用者；这里完成“依赖、项目路径和端口探测”的输出。
        return client.connect_ex(("127.0.0.1", port)) == 0
# 【L0023】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0024】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】定义函数 report_gripper_open_threshold；其职责属于“判断旧报告能否安全复用”，缩进块是函数体。
def report_gripper_open_threshold(report: dict) -> float | None:
# 【L0026】计算并保存变量 `configured`；该值服务于“判断旧报告能否安全复用”。
    configured = report.get("controller_config", {}).get("policy_gripper_open_threshold")
# 【L0027】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if isinstance(configured, (int, float)):
# 【L0028】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return float(configured)
# 【L0029】计算并保存变量 `historical`；该值服务于“判断旧报告能否安全复用”。
    historical = report.get("criteria", {}).get("final_gripper_normalized_lt")
# 【L0030】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if isinstance(historical, (int, float)):
# 【L0031】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return float(historical)
# 【L0032】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
    return None
# 【L0033】空行：分隔“判断旧报告能否安全复用”中的逻辑段，让结构更容易看清。

# 【L0034】空行：分隔“判断旧报告能否安全复用”中的逻辑段，让结构更容易看清。

# 【L0035】定义函数 load_existing_report；其职责属于“判断旧报告能否安全复用”，缩进块是函数体。
def load_existing_report(
# 【L0036】调用 `Path`：创建路径对象。本行位于“判断旧报告能否安全复用”。
    path: Path, checkpoint_id: str, gripper_open_threshold: float
# 【L0037】开始一个缩进代码块或键值结构；该块负责“判断旧报告能否安全复用”。
) -> dict | None:
# 【L0038】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not path.is_file():
# 【L0039】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return None
# 【L0040】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
    try:
# 【L0041】调用 `read_text`：从磁盘读取文本。本行位于“判断旧报告能否安全复用”。
        report = json.loads(path.read_text(encoding="utf-8"))
# 【L0042】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
    except (OSError, json.JSONDecodeError):
# 【L0043】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return None
# 【L0044】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if report.get("policy_checkpoint_id") != checkpoint_id:
# 【L0045】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return None
# 【L0046】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if report.get("pi05_used") is not True or report.get("simulation_only") is not True:
# 【L0047】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return None
# 【L0048】计算并保存变量 `existing_threshold`；该值服务于“判断旧报告能否安全复用”。
    existing_threshold = report_gripper_open_threshold(report)
# 【L0049】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9:
# 【L0050】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
        return None
# 【L0051】结束当前函数并把结果交给调用者；这里完成“判断旧报告能否安全复用”的输出。
    return report
# 【L0052】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0053】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0054】定义函数 main；其职责属于“评测参数和范围校验”，缩进块是函数体。
def main() -> int:
# 【L0055】计算并保存变量 `parser`；该值服务于“评测参数和范围校验”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0056】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0057】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0058】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--plan",
# 【L0059】调用 `Path`：创建路径对象。本行位于“评测参数和范围校验”。
        type=Path,
# 【L0060】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json",
# 【L0061】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0062】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0063】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--output-root",
# 【L0064】调用 `Path`：创建路径对象。本行位于“评测参数和范围校验”。
        type=Path,
# 【L0065】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1",
# 【L0066】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0067】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0068】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--summary",
# 【L0069】调用 `Path`：创建路径对象。本行位于“评测参数和范围校验”。
        type=Path,
# 【L0070】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json",
# 【L0071】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0072】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--policy-port", type=int, default=8000)
# 【L0073】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0074】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--gripper-open-threshold",
# 【L0075】计算并保存变量 `type`；该值服务于“评测参数和范围校验”。
        type=float,
# 【L0076】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=0.12,
# 【L0077】计算并保存变量 `help`；该值服务于“评测参数和范围校验”。
        help="Normalized 4C2 threshold used for in-loop release verification.",
# 【L0078】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0079】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0080】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--repo-id",
# 【L0081】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=os.environ.get("RM65_REPO_ID", "local/rm65_sim_train"),
# 【L0082】计算并保存变量 `help`；该值服务于“评测参数和范围校验”。
        help="LeRobot repository id whose normalization statistics belong to the checkpoint.",
# 【L0083】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0084】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--case-timeout-seconds", type=int, default=1200)
# 【L0085】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0086】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“评测参数和范围校验”。
        "--infrastructure-retries",
# 【L0087】计算并保存变量 `type`；该值服务于“评测参数和范围校验”。
        type=int,
# 【L0088】计算并保存变量 `default`；该值服务于“评测参数和范围校验”。
        default=1,
# 【L0089】计算并保存变量 `help`；该值服务于“评测参数和范围校验”。
        help="Retry only cases that fail to produce a valid task report.",
# 【L0090】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0091】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--max-cases", type=int)
# 【L0092】计算并保存变量 `args`；该值服务于“评测参数和范围校验”。
    args = parser.parse_args()
# 【L0093】空行：分隔“评测参数和范围校验”中的逻辑段，让结构更容易看清。

# 【L0094】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.infrastructure_retries < 0:
# 【L0095】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--infrastructure-retries must be non-negative")
# 【L0096】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 < args.gripper_open_threshold < 1.0:
# 【L0097】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--gripper-open-threshold must be between 0 and 1")
# 【L0098】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0099】给变量 `checkpoint` 赋值：一次训练保存的模型参数目录。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0100】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not checkpoint.is_dir():
# 【L0101】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise FileNotFoundError(checkpoint)
# 【L0102】计算并保存变量 `plan_path`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    plan_path = args.plan.expanduser().resolve()
# 【L0103】调用 `read_text`：从磁盘读取文本。本行位于“载入 checkpoint/评测计划并准备环境变量”。
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
# 【L0104】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1":
# 【L0105】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("unsupported evaluation plan format")
# 【L0106】计算并保存变量 `cases`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    cases = plan.get("cases", [])
# 【L0107】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.max_cases is not None:
# 【L0108】计算并保存变量 `cases`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
        cases = cases[: args.max_cases]
# 【L0109】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not cases:
# 【L0110】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("evaluation plan has no cases")
# 【L0111】计算并保存变量 `case_ids`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    case_ids = [case["case_id"] for case in cases]
# 【L0112】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(set(case_ids)) != len(case_ids):
# 【L0113】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("evaluation case ids must be unique")
# 【L0114】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if port_open(args.policy_port):
# 【L0115】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(f"policy port {args.policy_port} is already in use")
# 【L0116】空行：分隔“载入 checkpoint/评测计划并准备环境变量”中的逻辑段，让结构更容易看清。

# 【L0117】计算并保存变量 `output_root`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    output_root = args.output_root.expanduser().resolve()
# 【L0118】计算并保存变量 `summary_path`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    summary_path = args.summary.expanduser().resolve()
# 【L0119】调用 `mkdir`：创建目录。本行位于“载入 checkpoint/评测计划并准备环境变量”。
    output_root.mkdir(parents=True, exist_ok=True)
# 【L0120】调用 `mkdir`：创建目录。本行位于“载入 checkpoint/评测计划并准备环境变量”。
    summary_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0121】调用 `Path`：创建路径对象。本行位于“载入 checkpoint/评测计划并准备环境变量”。
    openpi_root = Path.home() / "robot-learning" / "openpi"
# 【L0122】计算并保存变量 `checkpoint_id`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    checkpoint_id = f"{checkpoint.parent.name}/{checkpoint.name}"
# 【L0123】计算并保存变量 `environment`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    environment = os.environ.copy()
# 【L0124】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    environment["PYTHONPATH"] = os.pathsep.join(
# 【L0125】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“载入 checkpoint/评测计划并准备环境变量”。
        [
# 【L0126】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“载入 checkpoint/评测计划并准备环境变量”。
            str(PROJECT_ROOT),
# 【L0127】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“载入 checkpoint/评测计划并准备环境变量”。
            str(openpi_root / "packages" / "openpi-client" / "src"),
# 【L0128】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“载入 checkpoint/评测计划并准备环境变量”。
            environment.get("PYTHONPATH", ""),
# 【L0129】结束或闭合当前语法结构；它属于“载入 checkpoint/评测计划并准备环境变量”。
        ]
# 【L0130】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ).rstrip(os.pathsep)
# 【L0131】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    environment["XLA_PYTHON_CLIENT_MEM_FRACTION"] = environment.get(
# 【L0132】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"
# 【L0133】结束或闭合当前语法结构；它属于“载入 checkpoint/评测计划并准备环境变量”。
    )
# 【L0134】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    environment["RM65_REPO_ID"] = args.repo_id
# 【L0135】执行“载入 checkpoint/评测计划并准备环境变量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    environment["POLICY_GRIPPER_OPEN_THRESHOLD"] = str(args.gripper_open_threshold)
# 【L0136】计算并保存变量 `server_log_path`；该值服务于“载入 checkpoint/评测计划并准备环境变量”。
    server_log_path = PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"
# 【L0137】调用 `mkdir`：创建目录。本行位于“载入 checkpoint/评测计划并准备环境变量”。
    server_log_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0138】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with server_log_path.open("w", encoding="utf-8") as server_log:
# 【L0139】计算并保存变量 `server`；该值服务于“启动一次策略服务并等待就绪”。
        server = subprocess.Popen(
# 【L0140】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“启动一次策略服务并等待就绪”。
            [
# 【L0141】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                str(openpi_root / ".venv" / "bin" / "python"),
# 【L0142】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                "-u",
# 【L0143】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"),
# 【L0144】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                "--checkpoint",
# 【L0145】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                str(checkpoint),
# 【L0146】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                "--repo-id",
# 【L0147】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                args.repo_id,
# 【L0148】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                "--port",
# 【L0149】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动一次策略服务并等待就绪”。
                str(args.policy_port),
# 【L0150】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
            ],
# 【L0151】计算并保存变量 `cwd`；该值服务于“启动一次策略服务并等待就绪”。
            cwd=PROJECT_ROOT,
# 【L0152】计算并保存变量 `env`；该值服务于“启动一次策略服务并等待就绪”。
            env=environment,
# 【L0153】计算并保存变量 `stdout`；该值服务于“启动一次策略服务并等待就绪”。
            stdout=server_log,
# 【L0154】计算并保存变量 `stderr`；该值服务于“启动一次策略服务并等待就绪”。
            stderr=subprocess.STDOUT,
# 【L0155】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
        )
# 【L0156】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
        try:
# 【L0157】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for _ in range(180):
# 【L0158】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if server.poll() is not None:
# 【L0159】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
                    raise RuntimeError(
# 【L0160】执行“启动一次策略服务并等待就绪”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                        f"policy server stopped during startup; see {server_log_path}"
# 【L0161】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
                    )
# 【L0162】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if port_open(args.policy_port):
# 【L0163】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
                    break
# 【L0164】执行“启动一次策略服务并等待就绪”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                time.sleep(1)
# 【L0165】否则分支：前面的 if/elif 都不成立时执行。
            else:
# 【L0166】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
                raise TimeoutError("policy server did not listen within 180 seconds")
# 【L0167】空行：分隔“启动一次策略服务并等待就绪”中的逻辑段，让结构更容易看清。

# 【L0168】计算并保存变量 `case_results`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
            case_results = []
# 【L0169】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for position, case in enumerate(cases, start=1):
# 【L0170】计算并保存变量 `case_id`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                case_id = case["case_id"]
# 【L0171】计算并保存变量 `episode_dir`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                episode_dir = output_root / case_id
# 【L0172】计算并保存变量 `report_path`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                report_path = episode_dir / "task_report.json"
# 【L0173】计算并保存变量 `existing`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                existing = load_existing_report(
# 【L0174】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    report_path, checkpoint_id, args.gripper_open_threshold
# 【L0175】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                )
# 【L0176】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if existing is not None:
# 【L0177】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                    print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True)
# 【L0178】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    case_results.append(
# 【L0179】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        {"case_id": case_id, "runner_returncode": 0, "report": existing, "reused": True}
# 【L0180】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0181】跳过本次循环剩余语句，继续处理下一个候选项。
                    continue
# 【L0182】调用 `mkdir`：创建目录。本行位于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                episode_dir.mkdir(parents=True, exist_ok=True)
# 【L0183】计算并保存变量 `case_environment`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                case_environment = environment.copy()
# 【L0184】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                case_environment["POLICY_SERVER_MODE"] = "external"
# 【L0185】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                case_environment["POLICY_PORT"] = str(args.policy_port)
# 【L0186】计算并保存变量 `command`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                command = [
# 【L0187】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    "bash",
# 【L0188】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"),
# 【L0189】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(checkpoint),
# 【L0190】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(episode_dir),
# 【L0191】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["transfer_joint_1_rad"]),
# 【L0192】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["source_offset_x_m"]),
# 【L0193】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["source_offset_y_m"]),
# 【L0194】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    case["prompt"],
# 【L0195】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                ]
# 【L0196】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                print(f"[{position}/{len(cases)}] {case_id}: run", flush=True)
# 【L0197】计算并保存变量 `attempt_results`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                attempt_results = []
# 【L0198】给变量 `report` 赋值：机器可读实验报告字典。
                report = None
# 【L0199】for 循环：依次处理序列中的每个元素/时间步/episode/case。
                for attempt in range(args.infrastructure_retries + 1):
# 【L0200】计算并保存变量 `log_name`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    log_name = "runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"
# 【L0201】计算并保存变量 `case_log_path`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    case_log_path = episode_dir / log_name
# 【L0202】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
                    with case_log_path.open("w", encoding="utf-8") as case_log:
# 【L0203】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
                        try:
# 【L0204】计算并保存变量 `completed`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            completed = subprocess.run(
# 【L0205】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                command,
# 【L0206】计算并保存变量 `cwd`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                cwd=PROJECT_ROOT,
# 【L0207】计算并保存变量 `env`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                env=case_environment,
# 【L0208】计算并保存变量 `stdout`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                stdout=case_log,
# 【L0209】计算并保存变量 `stderr`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                stderr=subprocess.STDOUT,
# 【L0210】计算并保存变量 `timeout`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                timeout=args.case_timeout_seconds,
# 【L0211】计算并保存变量 `check`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                check=False,
# 【L0212】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            )
# 【L0213】计算并保存变量 `returncode`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            returncode = completed.returncode
# 【L0214】计算并保存变量 `timed_out`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            timed_out = False
# 【L0215】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
                        except subprocess.TimeoutExpired:
# 【L0216】计算并保存变量 `returncode`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            returncode = 124
# 【L0217】计算并保存变量 `timed_out`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            timed_out = True
# 【L0218】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    attempt_results.append(
# 【L0219】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        {
# 【L0220】定义字典/JSON 字段 `attempt`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                            "attempt": attempt + 1,
# 【L0221】定义字典/JSON 字段 `runner_returncode`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                            "runner_returncode": returncode,
# 【L0222】定义字典/JSON 字段 `timed_out`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                            "timed_out": timed_out,
# 【L0223】定义字典/JSON 字段 `log`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                            "log": str(case_log_path),
# 【L0224】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        }
# 【L0225】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0226】给变量 `report` 赋值：机器可读实验报告字典。
                    report = load_existing_report(
# 【L0227】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                        report_path, checkpoint_id, args.gripper_open_threshold
# 【L0228】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0229】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                    if report is not None:
# 【L0230】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
                        break
# 【L0231】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                    if attempt < args.infrastructure_retries:
# 【L0232】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                        print(
# 【L0233】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                            f"[{position}/{len(cases)}] {case_id}: missing_report; "
# 【L0234】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            f"retry infrastructure attempt {attempt + 2}",
# 【L0235】计算并保存变量 `flush`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            flush=True,
# 【L0236】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        )
# 【L0237】执行“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                case_results.append(
# 【L0238】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    {
# 【L0239】定义字典/JSON 字段 `case_id`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "case_id": case_id,
# 【L0240】定义字典/JSON 字段 `runner_returncode`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "runner_returncode": returncode,
# 【L0241】定义字典/JSON 字段 `timed_out`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "timed_out": timed_out,
# 【L0242】定义字典/JSON 字段 `report`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "report": report,
# 【L0243】定义字典/JSON 字段 `reused`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "reused": False,
# 【L0244】定义字典/JSON 字段 `log`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "log": str(case_log_path),
# 【L0245】定义字典/JSON 字段 `infrastructure_attempts`；它把“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的结果用稳定键名记录下来。
                        "infrastructure_attempts": attempt_results,
# 【L0246】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    }
# 【L0247】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                )
# 【L0248】计算并保存变量 `status`；该值服务于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                status = report.get("status") if report else "missing_report"
# 【L0249】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                print(f"[{position}/{len(cases)}] {case_id}: {status}", flush=True)
# 【L0250】清理块：无论前面成功还是抛错都执行，常用于关闭服务和 Isaac Sim。
        finally:
# 【L0251】执行“无论结果如何都关闭服务”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            server.terminate()
# 【L0252】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
            try:
# 【L0253】执行“无论结果如何都关闭服务”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                server.wait(timeout=20)
# 【L0254】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
            except subprocess.TimeoutExpired:
# 【L0255】执行“无论结果如何都关闭服务”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                server.kill()
# 【L0256】执行“无论结果如何都关闭服务”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                server.wait(timeout=20)
# 【L0257】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0258】计算并保存变量 `valid_reports`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    valid_reports = [item["report"] for item in case_results if item.get("report") is not None]
# 【L0259】计算并保存变量 `successes`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    successes = sum(report.get("status") == "pass" for report in valid_reports)
# 【L0260】计算并保存变量 `episode_count`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    episode_count = len(valid_reports)
# 【L0261】计算并保存变量 `success_rate`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    success_rate = successes / episode_count if episode_count else 0.0
# 【L0262】计算并保存变量 `passed`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    passed = episode_count >= 20 and success_rate >= 0.8
# 【L0263】计算并保存变量 `summary`；该值服务于“统计成功率并执行 20 条、80% 门槛”。
    summary = {
# 【L0264】定义字典/JSON 字段 `status`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "status": "pass" if passed else "fail",
# 【L0265】定义字典/JSON 字段 `evaluation_kind`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "evaluation_kind": "isaaclab_pi0.5_closed_loop",
# 【L0266】定义字典/JSON 字段 `simulation_only`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L0267】定义字典/JSON 字段 `real_robot_command_sent`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L0268】定义字典/JSON 字段 `plan`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "plan": str(plan_path),
# 【L0269】定义字典/JSON 字段 `checkpoint`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "checkpoint": str(checkpoint),
# 【L0270】定义字典/JSON 字段 `policy_checkpoint_id`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "policy_checkpoint_id": checkpoint_id,
# 【L0271】定义字典/JSON 字段 `repo_id`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "repo_id": args.repo_id,
# 【L0272】定义字典/JSON 字段 `gripper_open_threshold_normalized`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "gripper_open_threshold_normalized": args.gripper_open_threshold,
# 【L0273】定义字典/JSON 字段 `planned_case_count`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "planned_case_count": len(cases),
# 【L0274】定义字典/JSON 字段 `episode_count`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "episode_count": episode_count,
# 【L0275】定义字典/JSON 字段 `success_count`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "success_count": successes,
# 【L0276】定义字典/JSON 字段 `success_rate`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "success_rate": success_rate,
# 【L0277】定义字典/JSON 字段 `gate`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "gate": {"minimum_episode_count": 20, "minimum_success_rate": 0.8},
# 【L0278】定义字典/JSON 字段 `cases`；它把“统计成功率并执行 20 条、80% 门槛”中的结果用稳定键名记录下来。
        "cases": case_results,
# 【L0279】结束或闭合当前语法结构；它属于“统计成功率并执行 20 条、80% 门槛”。
    }
# 【L0280】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“统计成功率并执行 20 条、80% 门槛”。
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
# 【L0281】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
# 【L0282】结束当前函数并把结果交给调用者；这里完成“统计成功率并执行 20 条、80% 门槛”的输出。
    return 0 if passed else 1
# 【L0283】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0284】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0285】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0286】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
