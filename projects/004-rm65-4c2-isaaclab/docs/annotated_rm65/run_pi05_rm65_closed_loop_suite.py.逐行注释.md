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

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】语法拆解：`import` 加载模块；`os` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `os` 引入 `os`。在这份程序里，`os` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import os
# 【L0009】语法拆解：`import` 加载模块；`socket` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `socket` 引入 `socket`。在这份程序里，`socket` 用于TCP 端口探测与主机信息；后续出现这些名字时调用的是这里的外部能力。
import socket
# 【L0010】语法拆解：`import` 加载模块；`subprocess` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `subprocess` 引入 `subprocess`。在这份程序里，`subprocess` 用于启动和管理另一个系统进程；后续出现这些名字时调用的是这里的外部能力。
import subprocess
# 【L0011】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0012】语法拆解：`import` 加载模块；`time` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `time` 引入 `time`。在这份程序里，`time` 用于计时和短暂等待；后续出现这些名字时调用的是这里的外部能力。
import time
# 【L0013】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0014】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0018】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和端口探测”中的逻辑段，让结构更容易看清。

# 【L0019】语法拆解：`def` 定义函数 `port_open`；第一对圆括号列出形参，逗号负责分隔：`port: int` 用冒号给参数加类型提示；`-> bool` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `port_open(port: int)`；调用者把参数交给它完成“依赖、项目路径和端口探测”，后面的缩进代码是具体实现。
def port_open(port: int) -> bool:
# 【L0020】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
# 【L0021】语法拆解：`client` 是模块/对象，点号 `.` 从中取出 `settimeout` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0.5`。
# 【项目含义】对 `client` 调用 `settimeout(0.5)`：调用 `client` 提供的 `settimeout` 操作。本行产生的修改/返回值服务于“依赖、项目路径和端口探测”。
        client.settimeout(0.5)
# 【L0022】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：表达式 `client.connect_ex(("127.0.0.1", port)) == 0` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】结束当前函数并把 `client.connect_ex(("127.0.0.1", port)) == 0` 交回调用者；这个值的含义是：计算表达式 `client.connect_ex(("127.0.0.1", port)) == 0`；`client` 表示本功能块中的 `client` 值；`connect_ex` 表示本功能块中的 `connect_ex` 值；`port` 表示本功能块中的 `port` 值。
        return client.connect_ex(("127.0.0.1", port)) == 0
# 【L0023】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：`def` 定义函数 `report_gripper_open_threshold`；第一对圆括号列出形参，逗号负责分隔：`report: dict` 用冒号给参数加类型提示；`-> float | None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `report_gripper_open_threshold(report: dict)`；调用者把参数交给它完成“判断旧报告能否安全复用”，后面的缩进代码是具体实现。
def report_gripper_open_threshold(report: dict) -> float | None:
# 【L0026】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `configured`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"controller_config"`；第 2 个实参 `{}).get("policy_gripper_open_threshold"`。
# 【项目含义】得到 `configured`，它在本项目中表示本功能块中的 `configured` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("controller_config", {}).get("policy_gripper_open_threshold")`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`controller_config` 表示配置相关值。
    configured = report.get("controller_config", {}).get("policy_gripper_open_threshold")
# 【L0027】语法拆解：`if` 要求条件 `isinstance(configured, (int, float))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `isinstance(configured, (int, float))` 是否成立；`isinstance` 表示本功能块中的 `isinstance` 值；`configured` 表示本功能块中的 `configured` 值
    if isinstance(configured, (int, float)):
# 【L0028】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `configured`。
# 【项目含义】结束当前函数并把 `float(configured)` 交回调用者；这个值的含义是：计算表达式 `float(configured)`；`configured` 表示本功能块中的 `configured` 值。
        return float(configured)
# 【L0029】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `historical`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"criteria"`；第 2 个实参 `{}).get("final_gripper_normalized_lt"`。
# 【项目含义】得到 `historical`，它在本项目中表示本功能块中的 `historical` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("criteria", {}).get("final_gripper_normalized_lt")`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`criteria` 表示本功能块中的 `criteria` 值。
    historical = report.get("criteria", {}).get("final_gripper_normalized_lt")
# 【L0030】语法拆解：`if` 要求条件 `isinstance(historical, (int, float))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `isinstance(historical, (int, float))` 是否成立；`isinstance` 表示本功能块中的 `isinstance` 值；`historical` 表示本功能块中的 `historical` 值
    if isinstance(historical, (int, float)):
# 【L0031】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `historical`。
# 【项目含义】结束当前函数并把 `float(historical)` 交回调用者；这个值的含义是：计算表达式 `float(historical)`；`historical` 表示本功能块中的 `historical` 值。
        return float(historical)
# 【L0032】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    return None
# 【L0033】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“判断旧报告能否安全复用”中的逻辑段，让结构更容易看清。

# 【L0034】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“判断旧报告能否安全复用”中的逻辑段，让结构更容易看清。

# 【L0035】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `load_existing_report(参数在后续行继续)`；调用者把参数交给它完成“判断旧报告能否安全复用”，后面的缩进代码是具体实现。
def load_existing_report(
# 【L0036】语法拆解：`path` 是参数/字段名；冒号 `:` 添加类型提示 `Path, checkpoint_id: str, gripper_open_threshold: float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】调用 `Path`：创建路径对象；本行实际操作 `path: Path, checkpoint_id: str, gripper_open_threshold: float`。`path` 表示路径相关值；`checkpoint_id` 表示模型检查点相关值。
    path: Path, checkpoint_id: str, gripper_open_threshold: float
# 【L0037】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> dict | None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“判断旧报告能否安全复用”。
) -> dict | None:
# 【L0038】语法拆解：`if` 要求条件 `not path.is_file()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not path.is_file()` 是否成立；`path` 表示路径相关值；`is_file` 表示本功能块中的 `is_file` 值
    if not path.is_file():
# 【L0039】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0040】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“判断旧报告能否安全复用”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `path.read_text(encoding="utf-8")`。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
        report = json.loads(path.read_text(encoding="utf-8"))
# 【L0042】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `(OSError, json.JSONDecodeError)`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
    except (OSError, json.JSONDecodeError):
# 【L0043】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0044】语法拆解：`if` 要求条件 `report.get("policy_checkpoint_id") != checkpoint_id` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report.get("policy_checkpoint_id") != checkpoint_id` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`policy_checkpoint_id` 表示策略、模型检查点相关值
    if report.get("policy_checkpoint_id") != checkpoint_id:
# 【L0045】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0046】语法拆解：`if` 要求条件 `report.get("pi05_used") is not True or report.get("simulation_only") is not True` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report.get("pi05_used") is not True or report.get("simulation_only") is not True` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`pi05_used` 表示本功能块中的 `pi05_used` 值
    if report.get("pi05_used") is not True or report.get("simulation_only") is not True:
# 【L0047】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `existing_threshold`。右侧语法为：`report_gripper_open_threshold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report`。
# 【项目含义】得到 `existing_threshold`，它在本项目中表示本功能块中的 `existing_threshold` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report_gripper_open_threshold(report)`；`report_gripper_open_threshold` 表示报告、夹爪相关值；`report` 表示机器可读实验报告字典。
    existing_threshold = report_gripper_open_threshold(report)
# 【L0049】语法拆解：`if` 要求条件 `existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9:
# 【L0050】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0051】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`report` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `report` 交回调用者；这个值的含义是：计算表达式 `report`；`report` 表示机器可读实验报告字典。
    return report
# 【L0052】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0053】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0054】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“评测参数和范围校验”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0055】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0056】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--checkpoint", type`。右侧语法为：`Path, required=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--checkpoint`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0057】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0058】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--plan"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--plan",
# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“评测参数和范围校验”。
        type=Path,
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json",
# 【L0061】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0062】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0063】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--output-root"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--output-root",
# 【L0064】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“评测参数和范围校验”。
        type=Path,
# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1",
# 【L0066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0067】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0068】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--summary"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--summary",
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“评测参数和范围校验”。
        type=Path,
# 【L0070】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json",
# 【L0071】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--policy-port", type`。右侧语法为：`int, default=8000)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--policy-port`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--policy-port", type=int, default=8000)
# 【L0073】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0074】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--gripper-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--gripper-open-threshold",
# 【L0075】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“评测参数和范围校验”。
        type=float,
# 【L0076】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=0.12,
# 【L0077】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Normalized 4C2 threshold used for in-loop release verification."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Normalized 4C2 threshold used for in-loop release verification."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“评测参数和范围校验”。
        help="Normalized 4C2 threshold used for in-loop release verification.",
# 【L0078】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0079】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0080】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--repo-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--repo-id",
# 【L0081】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`os.environ` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"RM65_REPO_ID"`；第 2 个实参 `"local/rm65_sim_train"`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `os.environ.get("RM65_REPO_ID", "local/rm65_sim_train")`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=os.environ.get("RM65_REPO_ID", "local/rm65_sim_train"),
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"LeRobot repository id whose normalization statistics belong to the checkpoint."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"LeRobot repository id whose normalization statistics belong to the checkpoint."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“评测参数和范围校验”。
        help="LeRobot repository id whose normalization statistics belong to the checkpoint.",
# 【L0083】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0084】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--case-timeout-seconds", type`。右侧语法为：`int, default=1200)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--case-timeout-seconds`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--case-timeout-seconds", type=int, default=1200)
# 【L0085】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0086】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--infrastructure-retries"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“评测参数和范围校验”中的帮助说明、错误原因、任务名称或报告文字。
        "--infrastructure-retries",
# 【L0087】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“评测参数和范围校验”。
        type=int,
# 【L0088】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`1` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `1`；该参数在本项目中表示本功能块中的 `default` 值，会参与“评测参数和范围校验”。
        default=1,
# 【L0089】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Retry only cases that fail to produce a valid task report."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Retry only cases that fail to produce a valid task report."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“评测参数和范围校验”。
        help="Retry only cases that fail to produce a valid task report.",
# 【L0090】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“评测参数和范围校验”。
    )
# 【L0091】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--max-cases", type`。右侧语法为：`int)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--max-cases`；启动脚本可用它改变“评测参数和范围校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--max-cases", type=int)
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0093】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“评测参数和范围校验”中的逻辑段，让结构更容易看清。

# 【L0094】语法拆解：`if` 要求条件 `args.infrastructure_retries < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.infrastructure_retries < 0` 是否成立；`infrastructure_retries` 表示本功能块中的 `infrastructure_retries` 值
    if args.infrastructure_retries < 0:
# 【L0095】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--infrastructure-retries must be non-negative")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--infrastructure-retries must be non-negative")` 并停止当前路径；说明当前输入违反“评测参数和范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--infrastructure-retries must be non-negative")
# 【L0096】语法拆解：`if` 要求条件 `not 0.0 < args.gripper_open_threshold < 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 < args.gripper_open_threshold < 1.0` 是否成立；`gripper_open_threshold` 表示夹爪相关值
    if not 0.0 < args.gripper_open_threshold < 1.0:
# 【L0097】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--gripper-open-threshold must be between 0 and 1")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--gripper-open-threshold must be between 0 and 1")` 并停止当前路径；说明当前输入违反“评测参数和范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--gripper-open-threshold must be between 0 and 1")
# 【L0098】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0099】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`args.checkpoint` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.checkpoint.expanduser().resolve()`；`checkpoint` 表示一次训练保存的模型参数目录；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0100】语法拆解：`if` 要求条件 `not checkpoint.is_dir()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not checkpoint.is_dir()` 是否成立；`checkpoint` 表示一次训练保存的模型参数目录；`is_dir` 表示本功能块中的 `is_dir` 值
    if not checkpoint.is_dir():
# 【L0101】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileNotFoundError(checkpoint)` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileNotFoundError(checkpoint)` 并停止当前路径；说明当前输入违反“载入 checkpoint/评测计划并准备环境变量”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(checkpoint)
# 【L0102】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `plan_path`。右侧语法为：`args.plan` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `plan_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.plan.expanduser().resolve()`；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    plan_path = args.plan.expanduser().resolve()
# 【L0103】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `plan`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `plan_path.read_text(encoding="utf-8")`。
# 【项目含义】得到 `plan`，它在本项目中表示从 JSON 读取的专家采集计划或闭环评测计划；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
# 【L0104】语法拆解：`if` 要求条件 `plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1"` 是否成立；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1":
# 【L0105】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("unsupported evaluation plan format")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("unsupported evaluation plan format")` 并停止当前路径；说明当前输入违反“载入 checkpoint/评测计划并准备环境变量”要求，不能继续进入仿真、训练或评测。
        raise ValueError("unsupported evaluation plan format")
# 【L0106】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`plan` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"cases"`；第 2 个实参 `[]`。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `plan.get("cases", [])`；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。
    cases = plan.get("cases", [])
# 【L0107】语法拆解：`if` 要求条件 `args.max_cases is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.max_cases is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.max_cases is not None:
# 【L0108】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`cases[: args.max_cases]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cases[: args.max_cases]`；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表；`max_cases` 表示本功能块中的 `max_cases` 值。
        cases = cases[: args.max_cases]
# 【L0109】语法拆解：`if` 要求条件 `not cases` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not cases` 是否成立；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表
    if not cases:
# 【L0110】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation plan has no cases")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation plan has no cases")` 并停止当前路径；说明当前输入违反“载入 checkpoint/评测计划并准备环境变量”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation plan has no cases")
# 【L0111】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_ids`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `case_ids`，它在本项目中表示本功能块中的 `case_ids` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[case["case_id"] for case in cases]`；`case` 表示本功能块中的 `case` 值；`case_id` 表示本功能块中的 `case_id` 值；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。
    case_ids = [case["case_id"] for case in cases]
# 【L0112】语法拆解：`if` 要求条件 `len(set(case_ids)) != len(case_ids)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(set(case_ids)) != len(case_ids)` 是否成立；`set` 表示本功能块中的 `set` 值；`case_ids` 表示本功能块中的 `case_ids` 值
    if len(set(case_ids)) != len(case_ids):
# 【L0113】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation case ids must be unique")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation case ids must be unique")` 并停止当前路径；说明当前输入违反“载入 checkpoint/评测计划并准备环境变量”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation case ids must be unique")
# 【L0114】语法拆解：`if` 要求条件 `port_open(args.policy_port)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `port_open(args.policy_port)` 是否成立；`port_open` 表示本功能块中的 `port_open` 值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口
    if port_open(args.policy_port):
# 【L0115】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"policy port {args.policy_port} is already in use")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"policy port {args.policy_port} is already in use")` 并停止当前路径；说明当前输入违反“载入 checkpoint/评测计划并准备环境变量”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"policy port {args.policy_port} is already in use")
# 【L0116】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“载入 checkpoint/评测计划并准备环境变量”中的逻辑段，让结构更容易看清。

# 【L0117】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_root`。右侧语法为：`args.output_root` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `output_root`，它在本项目中表示输出相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.output_root.expanduser().resolve()`；`output_root` 表示输出相关值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    output_root = args.output_root.expanduser().resolve()
# 【L0118】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary_path`。右侧语法为：`args.summary` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `summary_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.summary.expanduser().resolve()`；`summary` 表示本功能块中的 `summary` 值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    summary_path = args.summary.expanduser().resolve()
# 【L0119】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_root.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output_root.mkdir(parents=True, exist_ok=True)`。`output_root` 表示输出相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
    output_root.mkdir(parents=True, exist_ok=True)
# 【L0120】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary_path.parent.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `summary_path.parent.mkdir(parents=True, exist_ok=True)`。`summary_path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
    summary_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0121】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `openpi_root`。右侧语法为：表达式 `Path.home() / "robot-learning" / "openpi"` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `openpi_root`，它在本项目中表示本功能块中的 `openpi_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path.home() / "robot-learning" / "openpi"`；`home` 表示本功能块中的 `home` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`learning` 表示本功能块中的 `learning` 值。
    openpi_root = Path.home() / "robot-learning" / "openpi"
# 【L0122】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint_id`。右侧语法为：`f"{checkpoint.parent.name}/{checkpoint.name}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】得到 `checkpoint_id`，它在本项目中表示模型检查点相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"{checkpoint.parent.name}/{checkpoint.name}"`；`f` 表示本功能块中的 `f` 值；`checkpoint` 表示一次训练保存的模型参数目录；`parent` 表示本功能块中的 `parent` 值。
    checkpoint_id = f"{checkpoint.parent.name}/{checkpoint.name}"
# 【L0123】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment`。右侧语法为：`os.environ` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `environment`，它在本项目中表示本功能块中的 `environment` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    environment = os.environ.copy()
# 【L0124】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["PYTHONPATH"]`。右侧语法为：`os.pathsep.join(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["PYTHONPATH"]`（写入 `environment["PYTHONPATH"]` 指定的字段）；右侧具体做的是：计算表达式 `os.pathsep.join(`；`os` 表示本功能块中的 `os` 值；`pathsep` 表示本功能块中的 `pathsep` 值；`join` 表示本功能块中的 `join` 值。
    environment["PYTHONPATH"] = os.pathsep.join(
# 【L0125】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“载入 checkpoint/评测计划并准备环境变量”。
        [
# 【L0126】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT`。
# 【项目含义】调用 `str(PROJECT_ROOT)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/评测计划并准备环境变量”。
            str(PROJECT_ROOT),
# 【L0127】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `openpi_root / "packages" / "openpi-client" / "src"`。
# 【项目含义】调用 `str(openpi_root / "packages" / "openpi-client" / "src")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/评测计划并准备环境变量”。
            str(openpi_root / "packages" / "openpi-client" / "src"),
# 【L0128】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`environment` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PYTHONPATH"`；第 2 个实参 `""`。
# 【项目含义】对 `environment` 调用 `get("PYTHONPATH", "")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“载入 checkpoint/评测计划并准备环境变量”。
            environment.get("PYTHONPATH", ""),
# 【L0129】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/评测计划并准备环境变量”。
        ]
# 【L0130】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `rstrip(os.pathsep)`：调用 `)` 提供的 `rstrip` 操作。本行产生的修改/返回值服务于“载入 checkpoint/评测计划并准备环境变量”。
    ).rstrip(os.pathsep)
# 【L0131】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]`。右侧语法为：`environment.get(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]`（写入 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]` 指定的字段）；右侧具体做的是：计算表达式 `environment.get(`；`environment` 表示本功能块中的 `environment` 值；`get` 表示本功能块中的 `get` 值。
    environment["XLA_PYTHON_CLIENT_MEM_FRACTION"] = environment.get(
# 【L0132】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/评测计划并准备环境变量”中的帮助说明、错误原因、任务名称或报告文字。
        "XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"
# 【L0133】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/评测计划并准备环境变量”。
    )
# 【L0134】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["RM65_REPO_ID"]`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】把右侧结果写进 `environment["RM65_REPO_ID"]`（写入 `environment["RM65_REPO_ID"]` 指定的字段）；右侧具体做的是：计算表达式 `args.repo_id`；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。
    environment["RM65_REPO_ID"] = args.repo_id
# 【L0135】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.gripper_open_threshold`。
# 【项目含义】把右侧结果写进 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]`（写入 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]` 指定的字段）；右侧具体做的是：计算表达式 `str(args.gripper_open_threshold)`；`gripper_open_threshold` 表示夹爪相关值。
    environment["POLICY_GRIPPER_OPEN_THRESHOLD"] = str(args.gripper_open_threshold)
# 【L0136】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_log_path`。右侧语法为：表达式 `PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `server_log_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"`；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`outputs` 表示本功能块中的 `outputs` 值；`rm65_pi05_policy_server_suite` 表示策略相关值。
    server_log_path = PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"
# 【L0137】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_log_path.parent.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `server_log_path.parent.mkdir(parents=True, exist_ok=True)`。`server_log_path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
    server_log_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0138】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `server_log_path.open("w", encoding="utf-8") as server_log`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with server_log_path.open("w", encoding="utf-8") as server_log:
# 【L0139】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server`。右侧语法为：`subprocess.Popen(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `server`，它在本项目中表示本功能块中的 `server` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `subprocess.Popen(`；`subprocess` 表示本功能块中的 `subprocess` 值；`Popen` 表示本功能块中的 `Popen` 值。
        server = subprocess.Popen(
# 【L0140】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“启动一次策略服务并等待就绪”。
            [
# 【L0141】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `openpi_root / ".venv" / "bin" / "python"`。
# 【项目含义】调用 `str(openpi_root / ".venv" / "bin" / "python")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“启动一次策略服务并等待就绪”。
                str(openpi_root / ".venv" / "bin" / "python"),
# 【L0142】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"-u"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“启动一次策略服务并等待就绪”中的帮助说明、错误原因、任务名称或报告文字。
                "-u",
# 【L0143】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"`。
# 【项目含义】调用 `str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“启动一次策略服务并等待就绪”。
                str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"),
# 【L0144】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--checkpoint"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“启动一次策略服务并等待就绪”中的帮助说明、错误原因、任务名称或报告文字。
                "--checkpoint",
# 【L0145】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】调用 `str(checkpoint)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“启动一次策略服务并等待就绪”。
                str(checkpoint),
# 【L0146】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--repo-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“启动一次策略服务并等待就绪”中的帮助说明、错误原因、任务名称或报告文字。
                "--repo-id",
# 【L0147】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.repo_id`；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，它参与“启动一次策略服务并等待就绪”。
                args.repo_id,
# 【L0148】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--port"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“启动一次策略服务并等待就绪”中的帮助说明、错误原因、任务名称或报告文字。
                "--port",
# 【L0149】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_port`。
# 【项目含义】调用 `str(args.policy_port)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“启动一次策略服务并等待就绪”。
                str(args.policy_port),
# 【L0150】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
            ],
# 【L0151】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cwd`。右侧语法为：`PROJECT_ROOT` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cwd` 传入 `PROJECT_ROOT`；该参数在本项目中表示本功能块中的 `cwd` 值，会参与“启动一次策略服务并等待就绪”。
            cwd=PROJECT_ROOT,
# 【L0152】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `env`。右侧语法为：`environment` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `env` 传入 `environment`；该参数在本项目中表示本功能块中的 `env` 值，会参与“启动一次策略服务并等待就绪”。
            env=environment,
# 【L0153】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stdout`。右侧语法为：`server_log` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stdout` 传入 `server_log`；该参数在本项目中表示本功能块中的 `stdout` 值，会参与“启动一次策略服务并等待就绪”。
            stdout=server_log,
# 【L0154】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stderr`。右侧语法为：`subprocess` 是起始对象；每个点号 `.` 依次读取属性/成员：`STDOUT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stderr` 传入 `subprocess.STDOUT`；该参数在本项目中表示本功能块中的 `stderr` 值，会参与“启动一次策略服务并等待就绪”。
            stderr=subprocess.STDOUT,
# 【L0155】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
        )
# 【L0156】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“启动一次策略服务并等待就绪”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
        try:
# 【L0157】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(180)`，每次把当前元素放进 `_`；这会逐个处理“启动一次策略服务并等待就绪”所需的帧、episode、动作或实验 case。
            for _ in range(180):
# 【L0158】语法拆解：`if` 要求条件 `server.poll() is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `server.poll() is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                if server.poll() is not None:
# 【L0159】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“启动一次策略服务并等待就绪”要求，不能继续进入仿真、训练或评测。
                    raise RuntimeError(
# 【L0160】语法拆解：`f"policy server stopped during startup; see {server_log_path}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"policy server stopped during startup; see {server_log_path}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`policy` 表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；`server` 表示本功能块中的 `server` 值。在“启动一次策略服务并等待就绪”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        f"policy server stopped during startup; see {server_log_path}"
# 【L0161】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动一次策略服务并等待就绪”。
                    )
# 【L0162】语法拆解：`if` 要求条件 `port_open(args.policy_port)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `port_open(args.policy_port)` 是否成立；`port_open` 表示本功能块中的 `port_open` 值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口
                if port_open(args.policy_port):
# 【L0163】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“启动一次策略服务并等待就绪”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                    break
# 【L0164】语法拆解：`time` 是模块/对象，点号 `.` 从中取出 `sleep` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `1`。
# 【项目含义】对 `time` 调用 `sleep(1)`：调用 `time` 提供的 `sleep` 操作。本行产生的修改/返回值服务于“启动一次策略服务并等待就绪”。
                time.sleep(1)
# 【L0165】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“启动一次策略服务并等待就绪”中处理剩余输入或备用路径。
            else:
# 【L0166】语法拆解：`raise` 主动制造并抛出异常；后面的 `TimeoutError("policy server did not listen within 180 seconds")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `TimeoutError("policy server did not listen within 180 seconds")` 并停止当前路径；说明当前输入违反“启动一次策略服务并等待就绪”要求，不能继续进入仿真、训练或评测。
                raise TimeoutError("policy server did not listen within 180 seconds")
# 【L0167】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动一次策略服务并等待就绪”中的逻辑段，让结构更容易看清。

# 【L0168】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_results`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `case_results`，它在本项目中表示每个评测 case 的退出码、日志和 task report 汇总；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
            case_results = []
# 【L0169】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(cases, start=1)`，每次把当前元素放进 `position, case`；这会逐个处理“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”所需的帧、episode、动作或实验 case。
            for position, case in enumerate(cases, start=1):
# 【L0170】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_id`。右侧语法为：`case["case_id"]` 使用方括号索引；先计算 `"case_id"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】得到 `case_id`，它在本项目中表示本功能块中的 `case_id` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case["case_id"]`；`case` 表示本功能块中的 `case` 值；`case_id` 表示本功能块中的 `case_id` 值。
                case_id = case["case_id"]
# 【L0171】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_dir`。右侧语法为：表达式 `output_root / case_id` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `episode_dir`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `output_root / case_id`；`output_root` 表示输出相关值；`case_id` 表示本功能块中的 `case_id` 值。
                episode_dir = output_root / case_id
# 【L0172】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_path`。右侧语法为：表达式 `episode_dir / "task_report.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `report_path`，它在本项目中表示报告、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_dir / "task_report.json"`；`episode_dir` 表示一条轨迹相关值；`task_report` 表示报告相关值；`json` 表示本功能块中的 `json` 值。
                report_path = episode_dir / "task_report.json"
# 【L0173】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `existing`。右侧语法为：`load_existing_report(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `existing`，它在本项目中表示本功能块中的 `existing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `load_existing_report(`；`load_existing_report` 表示报告相关值。
                existing = load_existing_report(
# 【L0174】语法拆解：`report_path, checkpoint_id, args.gripper_open_threshold` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `report_path, checkpoint_id, args.gripper_open_threshold` 接入当前完整语句；`report_path` 表示报告、路径相关值；`checkpoint_id` 表示模型检查点相关值；`gripper_open_threshold` 表示夹爪相关值。在“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    report_path, checkpoint_id, args.gripper_open_threshold
# 【L0175】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                )
# 【L0176】语法拆解：`if` 要求条件 `existing is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `existing is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                if existing is not None:
# 【L0177】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush`。右侧语法为：`True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”进度，也给日志留下可搜索证据。
                    print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True)
# 【L0178】语法拆解：`case_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `case_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    case_results.append(
# 【L0179】语法拆解：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{"case_id": case_id, "runner_returncode": 0, "report": existing, "reused": True}`；`case_id` 表示本功能块中的 `case_id` 值；`runner_returncode` 表示本功能块中的 `runner_returncode` 值；`report` 表示机器可读实验报告字典，共同完成“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        {"case_id": case_id, "runner_returncode": 0, "report": existing, "reused": True}
# 【L0180】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0181】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中不满足继续条件。
                    continue
# 【L0182】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_dir.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `episode_dir.mkdir(parents=True, exist_ok=True)`。`episode_dir` 表示一条轨迹相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
                episode_dir.mkdir(parents=True, exist_ok=True)
# 【L0183】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment`。右侧语法为：`environment` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `case_environment`，它在本项目中表示本功能块中的 `case_environment` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
                case_environment = environment.copy()
# 【L0184】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment["POLICY_SERVER_MODE"]`。右侧语法为：`"external"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】把右侧结果写进 `case_environment["POLICY_SERVER_MODE"]`（写入 `case_environment["POLICY_SERVER_MODE"]` 指定的字段）；右侧具体做的是：计算表达式 `"external"`；`external` 表示外部相机相关值。
                case_environment["POLICY_SERVER_MODE"] = "external"
# 【L0185】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment["POLICY_PORT"]`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_port`。
# 【项目含义】把右侧结果写进 `case_environment["POLICY_PORT"]`（写入 `case_environment["POLICY_PORT"]` 指定的字段）；右侧具体做的是：计算表达式 `str(args.policy_port)`；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口。
                case_environment["POLICY_PORT"] = str(args.policy_port)
# 【L0186】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
                command = [
# 【L0187】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"bash"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的帮助说明、错误原因、任务名称或报告文字。
                    "bash",
# 【L0188】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"`。
# 【项目含义】调用 `str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"),
# 【L0189】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】调用 `str(checkpoint)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(checkpoint),
# 【L0190】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_dir`。
# 【项目含义】调用 `str(episode_dir)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(episode_dir),
# 【L0191】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["transfer_joint_1_rad"]`；其中 `case["transfer_joint_1_rad"]` 的方括号表示先从 `case` 按键/索引 `"transfer_joint_1_rad"` 取值。
# 【项目含义】调用 `str(case["transfer_joint_1_rad"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["transfer_joint_1_rad"]),
# 【L0192】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_x_m"]`；其中 `case["source_offset_x_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_x_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_x_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["source_offset_x_m"]),
# 【L0193】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_y_m"]`；其中 `case["source_offset_y_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_y_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_y_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    str(case["source_offset_y_m"]),
# 【L0194】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    case["prompt"],
# 【L0195】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                ]
# 【L0196】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `print(f"[{position}/{len(cases)}] {case_id}: run", flush`。右侧语法为：`True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: run", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”进度，也给日志留下可搜索证据。
                print(f"[{position}/{len(cases)}] {case_id}: run", flush=True)
# 【L0197】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `attempt_results`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `attempt_results`，它在本项目中表示本功能块中的 `attempt_results` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
                attempt_results = []
# 【L0198】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
                report = None
# 【L0199】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(args.infrastructure_retries + 1)`，每次把当前元素放进 `attempt`；这会逐个处理“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”所需的帧、episode、动作或实验 case。
                for attempt in range(args.infrastructure_retries + 1):
# 【L0200】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `log_name`。右侧语法为：`"runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `log_name`，它在本项目中表示本功能块中的 `log_name` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"`；`runner` 表示本功能块中的 `runner` 值；`log` 表示本功能块中的 `log` 值；`attempt` 表示本功能块中的 `attempt` 值。
                    log_name = "runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"
# 【L0201】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_log_path`。右侧语法为：表达式 `episode_dir / log_name` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `case_log_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_dir / log_name`；`episode_dir` 表示一条轨迹相关值；`log_name` 表示本功能块中的 `log_name` 值。
                    case_log_path = episode_dir / log_name
# 【L0202】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `case_log_path.open("w", encoding="utf-8") as case_log`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
                    with case_log_path.open("w", encoding="utf-8") as case_log:
# 【L0203】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
                        try:
# 【L0204】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `completed`。右侧语法为：`subprocess.run(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `completed`，它在本项目中表示本功能块中的 `completed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `subprocess.run(`；`subprocess` 表示本功能块中的 `subprocess` 值；`run` 表示本功能块中的 `run` 值。
                            completed = subprocess.run(
# 【L0205】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `command`；在本项目中它表示控制命令相关值。
                                command,
# 【L0206】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cwd`。右侧语法为：`PROJECT_ROOT` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cwd` 传入 `PROJECT_ROOT`；该参数在本项目中表示本功能块中的 `cwd` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                cwd=PROJECT_ROOT,
# 【L0207】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `env`。右侧语法为：`case_environment` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `env` 传入 `case_environment`；该参数在本项目中表示本功能块中的 `env` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                env=case_environment,
# 【L0208】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stdout`。右侧语法为：`case_log` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stdout` 传入 `case_log`；该参数在本项目中表示本功能块中的 `stdout` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                stdout=case_log,
# 【L0209】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stderr`。右侧语法为：`subprocess` 是起始对象；每个点号 `.` 依次读取属性/成员：`STDOUT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stderr` 传入 `subprocess.STDOUT`；该参数在本项目中表示本功能块中的 `stderr` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                stderr=subprocess.STDOUT,
# 【L0210】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timeout`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`case_timeout_seconds`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `timeout` 传入 `args.case_timeout_seconds`；该参数在本项目中表示本功能块中的 `timeout` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                timeout=args.case_timeout_seconds,
# 【L0211】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `check`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `check` 传入 `False`；该参数在本项目中表示本功能块中的 `check` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                                check=False,
# 【L0212】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            )
# 【L0213】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`code = completed.returncode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `returncode`，它在本项目中表示本功能块中的 `returncode` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `completed.returncode`；`completed` 表示本功能块中的 `completed` 值；`returncode` 表示本功能块中的 `returncode` 值。
                            returncode = completed.returncode
# 【L0214】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timed_out`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `timed_out`，它在本项目中表示本功能块中的 `timed_out` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
                            timed_out = False
# 【L0215】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `subprocess.TimeoutExpired`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
                        except subprocess.TimeoutExpired:
# 【L0216】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`code = 124` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `returncode`，它在本项目中表示本功能块中的 `returncode` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `124` 的结果保存下来，供当前功能块后续使用。
                            returncode = 124
# 【L0217】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timed_out`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `timed_out`，它在本项目中表示本功能块中的 `timed_out` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                            timed_out = True
# 【L0218】语法拆解：`attempt_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `attempt_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    attempt_results.append(
# 【L0219】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        {
# 【L0220】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `attempt`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `attempt` 数据；字段值来自 `attempt + 1`，因此保存/传递的是这个表达式当前计算出的结果。
                            "attempt": attempt + 1,
# 【L0221】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `runner_returncode`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `runner_returncode` 数据；字段值来自 `returncode`，因此保存/传递的是这个表达式当前计算出的结果。
                            "runner_returncode": returncode,
# 【L0222】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `timed_out`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `timed_out` 数据；字段值来自 `timed_out`，因此保存/传递的是这个表达式当前计算出的结果。
                            "timed_out": timed_out,
# 【L0223】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `log`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `log` 数据；字段值来自 `str(case_log_path)`，因此保存/传递的是这个表达式当前计算出的结果。
                            "log": str(case_log_path),
# 【L0224】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        }
# 【L0225】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0226】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`load_existing_report(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `load_existing_report(`；`load_existing_report` 表示报告相关值。
                    report = load_existing_report(
# 【L0227】语法拆解：`report_path, checkpoint_id, args.gripper_open_threshold` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `report_path, checkpoint_id, args.gripper_open_threshold` 接入当前完整语句；`report_path` 表示报告、路径相关值；`checkpoint_id` 表示模型检查点相关值；`gripper_open_threshold` 表示夹爪相关值。在“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        report_path, checkpoint_id, args.gripper_open_threshold
# 【L0228】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    )
# 【L0229】语法拆解：`if` 要求条件 `report is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `report is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                    if report is not None:
# 【L0230】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                        break
# 【L0231】语法拆解：`if` 要求条件 `attempt < args.infrastructure_retries` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `attempt < args.infrastructure_retries` 是否成立；`attempt` 表示本功能块中的 `attempt` 值；`infrastructure_retries` 表示本功能块中的 `infrastructure_retries` 值
                    if attempt < args.infrastructure_retries:
# 【L0232】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”进度，也给日志留下可搜索证据。
                        print(
# 【L0233】语法拆解：`f"[{position}/{len(cases)}] {case_id}: missing_report; "` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"[{position}/{len(cases)}] {case_id}: missing_report; "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`position` 表示位置相关值；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。在“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                            f"[{position}/{len(cases)}] {case_id}: missing_report; "
# 【L0234】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"retry infrastructure attempt {attempt + 2}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"retry infrastructure attempt {attempt + 2}"`；`f` 表示本功能块中的 `f` 值；`retry` 表示本功能块中的 `retry` 值；`infrastructure` 表示本功能块中的 `infrastructure` 值，它参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            f"retry infrastructure attempt {attempt + 2}",
# 【L0235】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                            flush=True,
# 【L0236】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                        )
# 【L0237】语法拆解：`case_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `case_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                case_results.append(
# 【L0238】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    {
# 【L0239】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `case_id`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `case_id` 数据；字段值来自 `case_id`，因此保存/传递的是这个表达式当前计算出的结果。
                        "case_id": case_id,
# 【L0240】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `runner_returncode`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `runner_returncode` 数据；字段值来自 `returncode`，因此保存/传递的是这个表达式当前计算出的结果。
                        "runner_returncode": returncode,
# 【L0241】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `timed_out`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `timed_out` 数据；字段值来自 `timed_out`，因此保存/传递的是这个表达式当前计算出的结果。
                        "timed_out": timed_out,
# 【L0242】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `report`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `report` 数据；字段值来自 `report`，因此保存/传递的是这个表达式当前计算出的结果。
                        "report": report,
# 【L0243】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `reused`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `reused` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                        "reused": False,
# 【L0244】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `log`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `log` 数据；字段值来自 `str(case_log_path)`，因此保存/传递的是这个表达式当前计算出的结果。
                        "log": str(case_log_path),
# 【L0245】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `infrastructure_attempts`，它表示“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”中的 `infrastructure_attempts` 数据；字段值来自 `attempt_results`，因此保存/传递的是这个表达式当前计算出的结果。
                        "infrastructure_attempts": attempt_results,
# 【L0246】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                    }
# 【L0247】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”。
                )
# 【L0248】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `status`。右侧语法为：`report.get("status") if report else "missing_report"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `status`，它在本项目中表示本功能块中的 `status` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：本阶段的机器可读通过/失败状态。
                status = report.get("status") if report else "missing_report"
# 【L0249】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `print(f"[{position}/{len(cases)}] {case_id}: {status}", flush`。右侧语法为：`True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: {status}", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、复用报告、仅对缺报告的基础设施故障重试”进度，也给日志留下可搜索证据。
                print(f"[{position}/{len(cases)}] {case_id}: {status}", flush=True)
# 【L0250】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
        finally:
# 【L0251】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `terminate` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `server` 调用 `terminate()`：调用 `server` 提供的 `terminate` 操作。本行产生的修改/返回值服务于“无论结果如何都关闭服务”。
            server.terminate()
# 【L0252】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“无论结果如何都关闭服务”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
            try:
# 【L0253】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server.wait(timeout`。右侧语法为：`20)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `server` 调用 `wait(timeout=20)`：调用 `server` 提供的 `wait` 操作。本行产生的修改/返回值服务于“无论结果如何都关闭服务”。
                server.wait(timeout=20)
# 【L0254】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `subprocess.TimeoutExpired`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
            except subprocess.TimeoutExpired:
# 【L0255】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `kill` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `server` 调用 `kill()`：调用 `server` 提供的 `kill` 操作。本行产生的修改/返回值服务于“无论结果如何都关闭服务”。
                server.kill()
# 【L0256】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server.wait(timeout`。右侧语法为：`20)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `server` 调用 `wait(timeout=20)`：调用 `server` 提供的 `wait` 操作。本行产生的修改/返回值服务于“无论结果如何都关闭服务”。
                server.wait(timeout=20)
# 【L0257】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0258】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `valid_reports`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `valid_reports`，它在本项目中表示本功能块中的 `valid_reports` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[item["report"] for item in case_results if item.get("report") is not None]`；`item` 表示本功能块中的 `item` 值；`report` 表示机器可读实验报告字典；`case_results` 表示每个评测 case 的退出码、日志和 task report 汇总。
    valid_reports = [item["report"] for item in case_results if item.get("report") is not None]
# 【L0259】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `successes`。右侧语法为：`sum` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report.get("status") == "pass" for report in valid_reports`。
# 【项目含义】得到 `successes`，它在本项目中表示本功能块中的 `successes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：本阶段的机器可读通过/失败状态。
    successes = sum(report.get("status") == "pass" for report in valid_reports)
# 【L0260】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_count`。右侧语法为：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `valid_reports`。
# 【项目含义】得到 `episode_count`，它在本项目中表示一条轨迹、数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(valid_reports)`；`valid_reports` 表示本功能块中的 `valid_reports` 值。
    episode_count = len(valid_reports)
# 【L0261】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `success_rate`。右侧语法为：表达式 `successes / episode_count if episode_count else 0.0` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `success_rate`，它在本项目中表示有效闭环报告中 status=pass 的比例；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `successes / episode_count if episode_count else 0.0`；`successes` 表示本功能块中的 `successes` 值；`episode_count` 表示一条轨迹、数量相关值。
    success_rate = successes / episode_count if episode_count else 0.0
# 【L0262】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `passed`。右侧语法为：表达式 `episode_count >= 20 and success_rate >= 0.8` 使用运算符 `>=`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_count >= 20 and success_rate >= 0.8`；`episode_count` 表示一条轨迹、数量相关值；`success_rate` 表示有效闭环报告中 status=pass 的比例。
    passed = episode_count >= 20 and success_rate >= 0.8
# 【L0263】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `summary`，它在本项目中表示本功能块中的 `summary` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    summary = {
# 【L0264】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L0265】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `evaluation_kind`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `evaluation_kind` 数据；字段值来自 `"isaaclab_pi0.5_closed_loop"`，因此保存/传递的是这个表达式当前计算出的结果。
        "evaluation_kind": "isaaclab_pi0.5_closed_loop",
# 【L0266】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0267】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0268】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `plan`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `plan` 数据；字段值来自 `str(plan_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "plan": str(plan_path),
# 【L0269】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `checkpoint`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0270】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `checkpoint_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_checkpoint_id": checkpoint_id,
# 【L0271】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `repo_id`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0272】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_open_threshold_normalized`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `gripper_open_threshold_normalized` 数据；字段值来自 `args.gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_open_threshold_normalized": args.gripper_open_threshold,
# 【L0273】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `planned_case_count`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `planned_case_count` 数据；字段值来自 `len(cases)`，因此保存/传递的是这个表达式当前计算出的结果。
        "planned_case_count": len(cases),
# 【L0274】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `episode_count`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `episode_count` 数据；字段值来自 `episode_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode_count": episode_count,
# 【L0275】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `success_count`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `success_count` 数据；字段值来自 `successes`，因此保存/传递的是这个表达式当前计算出的结果。
        "success_count": successes,
# 【L0276】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `success_rate`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `success_rate` 数据；字段值来自 `success_rate`，因此保存/传递的是这个表达式当前计算出的结果。
        "success_rate": success_rate,
# 【L0277】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gate`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `gate` 数据；字段值来自 `{"minimum_episode_count": 20, "minimum_success_rate": 0.8}`，因此保存/传递的是这个表达式当前计算出的结果。
        "gate": {"minimum_episode_count": 20, "minimum_success_rate": 0.8},
# 【L0278】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `cases`，它表示“统计成功率并执行 20 条、80% 门槛”中的 `cases` 数据；字段值来自 `case_results`，因此保存/传递的是这个表达式当前计算出的结果。
        "cases": case_results,
# 【L0279】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“统计成功率并执行 20 条、80% 门槛”。
    }
# 【L0280】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary_path.write_text(json.dumps(summary, indent`。右侧语法为：表达式 `2) + "\n", encoding="utf-8")` 使用运算符 `+`, `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")`。`summary_path` 表示路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
# 【L0281】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2)`。
# 【项目含义】把 `json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2)` 的当前值/文字输出到终端；它用于观察“统计成功率并执行 20 条、80% 门槛”进度，也给日志留下可搜索证据。
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
# 【L0282】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0 if passed else 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L0283】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0284】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0285】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0286】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“脚本入口”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```
