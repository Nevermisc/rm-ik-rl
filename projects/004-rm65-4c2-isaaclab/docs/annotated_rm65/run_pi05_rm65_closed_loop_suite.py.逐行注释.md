# `run_pi05_rm65_closed_loop_suite.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_pi05_rm65_closed_loop_suite.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`5717e71972b04000d4a393d86edf117046fef29226bad1ee85848c6d49cc883c`
- 总行数：517

## 1. 先把这个程序放进整个项目

- 所处阶段：批量评测：运行可恢复、可追溯的多 case 仿真 gate。
- 输入：评测计划、checkpoint、split、重试和重复性配置。
- 输出：每 case 报告/日志、suite summary、成功率和失败阶段。
- 一句话作用：只启动一次 π0.5 服务，按 20 个未见条件运行可恢复批量评测并计算是否达到 80% 门槛。

### 为什么要写它

- 原先的问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。
- 采用的解决办法：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **ndarray**：NumPy ndarray：带 shape/dtype 的多维数值数组，用于图像、关节、动作和统计计算。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **argparse**：命令行参数解析：把 `--checkpoint` 等启动选项转换成 `args.checkpoint` 字段。
- **JSON**：JSON：只含通用键值、列表、数字和字符串的文本格式；用于计划、metadata 和报告证据。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-19` `be75d24a` **Add resumable RM65 pi0.5 simulation gate**：把批量仿真评测改成可恢复 gate。
- `2026-09-19` `66429003` **Record RM65 pi0.5 v1 evaluation and harden camera startup**：记录 v1 评测并增强相机启动检查。
- `2026-09-19` `28aef624` **Propagate RM65 policy normalization repo id**：把 norm-stats 数据集标识贯穿训练、服务和评测，避免加载错统计量。
- `2026-09-19` `66d5d71b` **Calibrate RM65 simulated release verification**：校准仿真松爪阈值和释放成功判定。
- `2026-09-28` `203c9b9b` **Make RM65 pi0.5 sampling deterministic**：固定随机采样与观测证据，解决相同输入难以复现的问题。
- `2026-09-28` `5d113153` **Seed RM65 simulation and diagnose camera divergence**：固定仿真种子并诊断相机观测分歧。
- `2026-09-28` `009b15d1` **Improve RM65 pi0.5 release supervision**：增强释放阶段监督，针对到位后不可靠松爪。
- `2026-09-28` `98de4494` **Fail closed on incomplete RM65 evaluation reports**：报告不完整时按失败处理，避免缺字段被误判通过。
- `2026-09-28` `0264302f` **Record RM65 pi0.5 repeatability gate**：加入重复性 gate，单次偶然成功不再足够。
- `2026-09-28` `a2f7ace3` **Prepare RM65 pi0.5 failure-correction v3**：根据闭环失败准备 v3 修正数据与训练配置。
- `2026-09-29` `79e66ceb` **Complete RM65 v3 training and harden evaluation provenance**：完成 v3 训练并强化评测来源链。

### 与上一版教学快照的源码差异

- 当前第 11-10 行相对旧教学快照发生 `delete`：旧版 1 行，当前 0 行。 旧代码摘录：`import sys`
- 当前第 16-16 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`EVALUATION_POLICY_MAX_ACTION_CHUNKS = 120`
- 当前第 35-119 行相对旧教学快照发生 `insert`：旧版 0 行，当前 85 行。 当前代码摘录：`def report_gripper_actual_open_threshold(report: dict) -> float | None:` / `configured = report.get("controller_config", {}).get(` / `"policy_gripper_actual_open_threshold"` / `)`
- 当前第 121-132 行相对旧教学快照发生 `replace`：旧版 1 行，当前 12 行。 旧代码摘录：`path: Path, checkpoint_id: str, gripper_open_threshold: float` 当前代码摘录：`path: Path,` / `checkpoint_id: str,` / `gripper_open_threshold: float,` / `gripper_actual_open_threshold: float,`
- 当前第 140-141 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`if report.get("status") not in {"pass", "fail"}:` / `return None`
- 当前第 144-162 行相对旧教学快照发生 `replace`：旧版 1 行，当前 19 行。 旧代码摘录：`if report.get("pi05_used") is not True or report.get("simulation_only") is not True:` 当前代码摘录：`if (` / `report.get("pi05_used") is not True` / `or report.get("simulation_only") is not True` / `or report.get("real_robot_command_sent") is not False`

## 4. 模块地图

- 模块 1｜第 1-24 行：依赖、项目路径和 policy 端口探测
- 模块 2｜第 25-63 行：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子
- 模块 3｜第 64-86 行：检查评测计划 case 数量、ID 唯一性和任务扰动字段
- 模块 4｜第 87-119 行：根据有效报告数、成功率和重复性条件计算 suite gate
- 模块 5｜第 120-190 行：严格核对旧报告身份与完整性，决定能否安全复用
- 模块 6｜第 191-264 行：解析批量评测参数与互斥、范围和重复性门槛
- 模块 7｜第 265-336 行：载入 checkpoint/计划、准备环境并启动一次 policy server
- 模块 8｜第 337-453 行：逐 case 运行、验证、复用报告并只重试基础设施故障
- 模块 9｜第 454-461 行：无论任务结果如何都关闭 policy server
- 模块 10｜第 462-515 行：汇总失败阶段、重复性和成功率，执行正式 suite gate
- 模块 11｜第 516-517 行：脚本入口

### 函数/类快速索引

- `port_open()`：第 19-22 行
- `report_gripper_open_threshold()`：第 25-32 行
- `report_gripper_actual_open_threshold()`：第 35-39 行
- `report_policy_noise_seed()`：第 42-50 行
- `report_simulation_seed()`：第 53-61 行
- `validate_evaluation_cases()`：第 64-84 行
- `evaluate_suite_gate()`：第 87-117 行
- `load_existing_report()`：第 120-188 行
- `main()`：第 191-513 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、项目路径和 policy 端口探测（源码第 1-24 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、项目路径和 policy 端口探测。
- 下游：处理结果继续交给模块 2“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、项目路径和 policy 端口探测”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `port_open(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `socket.socket(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `client.settimeout(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `client.connect_ex(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`port_open()`（第 19-22 行）

- 定义了什么：依赖、项目路径和 policy 端口探测。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`port`：类型 `int`；项目含义是本功能块中的 `port` 值
- 返回类型标注：`bool`。
- 函数体实际 return：`client.connect_ex(('127.0.0.1', port)) == 0`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:276` 的 `if port_open(args.policy_port):`；`run_pi05_rm65_closed_loop_suite.py:331` 的 `if port_open(args.policy_port):`


### 5.F 这一模块的版本变化

- 当前第 11-10 行相对旧教学快照发生 `delete`：旧版 1 行，当前 0 行。 旧代码摘录：`import sys`
- 当前第 16-16 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`EVALUATION_POLICY_MAX_ACTION_CHUNKS = 120`

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

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
# 【L0011】语法拆解：`import` 加载模块；`time` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `time` 引入 `time`。在这份程序里，`time` 用于计时和短暂等待；后续出现这些名字时调用的是这里的外部能力。
import time
# 【L0012】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0013】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0014】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0015】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `EVALUATION_POLICY_MAX_ACTION_CHUNKS`。右侧语法为：`120` 是直接写在源码中的数值常量。
# 【项目含义】得到 `EVALUATION_POLICY_MAX_ACTION_CHUNKS`，它在本项目中表示策略、动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `120` 的结果保存下来，供当前功能块后续使用。
EVALUATION_POLICY_MAX_ACTION_CHUNKS = 120
# 【L0017】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0018】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0019】语法拆解：`def` 定义函数 `port_open`；第一对圆括号列出形参，逗号负责分隔：`port: int` 用冒号给参数加类型提示；`-> bool` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `port_open(port: int)`；调用者把参数交给它完成“依赖、项目路径和 policy 端口探测”，后面的缩进代码是具体实现。
def port_open(port: int) -> bool:
# 【L0020】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
# 【L0021】语法拆解：`client` 是模块/对象，点号 `.` 从中取出 `settimeout` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0.5`。
# 【项目含义】对 `client` 调用 `settimeout(0.5)`：调用 `client` 提供的 `settimeout` 操作。本行产生的修改/返回值服务于“依赖、项目路径和 policy 端口探测”。
        client.settimeout(0.5)
# 【L0022】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：表达式 `client.connect_ex(("127.0.0.1", port)) == 0` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】结束当前函数并把 `client.connect_ex(("127.0.0.1", port)) == 0` 交回调用者；这个值的含义是：计算表达式 `client.connect_ex(("127.0.0.1", port)) == 0`；`client` 表示本功能块中的 `client` 值；`connect_ex` 表示本功能块中的 `connect_ex` 值；`port` 表示本功能块中的 `port` 值。
        return client.connect_ex(("127.0.0.1", port)) == 0
# 【L0023】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 policy 端口探测”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、项目路径和 policy 端口探测”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子（源码第 25-63 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、项目路径和 policy 端口探测”。
- 本模块：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子。
- 下游：处理结果继续交给模块 3“检查评测计划 case 数量、ID 唯一性和任务扰动字段”。

### 5.B 为什么需要这一组代码

这一组负责“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。

### 5.D 本模块首次阅读要认识的调用

- `report_gripper_open_threshold(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `report.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `isinstance(...)`：圆括号表示真正执行调用；判断一个对象是否属于指定类型；本项目常用它区分 bytes、字符串或数组。
- `report_gripper_actual_open_threshold(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `report_policy_noise_seed(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `sampling.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `any(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `report_simulation_seed(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `determinism.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。

### 5.E 本模块定义的新函数

### 函数卡：`report_gripper_open_threshold()`（第 25-32 行）

- 定义了什么：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`report`：类型 `dict`；项目含义是机器可读实验报告字典
- 返回类型标注：`float | None`。
- 函数体实际 return：`None`；`float(configured)`；`float(historical)`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:164` 的 `existing_threshold = report_gripper_open_threshold(report)`

### 函数卡：`report_gripper_actual_open_threshold()`（第 35-39 行）

- 定义了什么：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`report`：类型 `dict`；项目含义是机器可读实验报告字典
- 返回类型标注：`float | None`。
- 函数体实际 return：`float(configured) if isinstance(configured, (int, float)) else None`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:167` 的 `existing_actual_threshold = report_gripper_actual_open_threshold(report)`

### 函数卡：`report_policy_noise_seed()`（第 42-50 行）

- 定义了什么：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`report`：类型 `dict`；项目含义是机器可读实验报告字典
- 返回类型标注：`int | None`。
- 函数体实际 return：`top_level`；`None`；`None`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:184` 的 `if report_policy_noise_seed(report) != policy_noise_seed:`

### 函数卡：`report_simulation_seed()`（第 53-61 行）

- 定义了什么：从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`report`：类型 `dict`；项目含义是机器可读实验报告字典
- 返回类型标注：`int | None`。
- 函数体实际 return：`top_level`；`None`；`None`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:186` 的 `if report_simulation_seed(report) != simulation_seed:`


### 5.F 这一模块的版本变化

- 当前第 35-119 行相对旧教学快照发生 `insert`：旧版 0 行，当前 85 行。 当前代码摘录：`def report_gripper_actual_open_threshold(report: dict) -> float | None:` / `configured = report.get("controller_config", {}).get(` / `"policy_gripper_actual_open_threshold"` / `)`

### 5.G 逐行精读

```python
# 【L0025】语法拆解：`def` 定义函数 `report_gripper_open_threshold`；第一对圆括号列出形参，逗号负责分隔：`report: dict` 用冒号给参数加类型提示；`-> float | None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `report_gripper_open_threshold(report: dict)`；调用者把参数交给它完成“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”，后面的缩进代码是具体实现。
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
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0034】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0035】语法拆解：`def` 定义函数 `report_gripper_actual_open_threshold`；第一对圆括号列出形参，逗号负责分隔：`report: dict` 用冒号给参数加类型提示；`-> float | None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `report_gripper_actual_open_threshold(report: dict)`；调用者把参数交给它完成“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”，后面的缩进代码是具体实现。
def report_gripper_actual_open_threshold(report: dict) -> float | None:
# 【L0036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `configured`。右侧语法为：`report.get("controller_config", {}).get(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `configured`，它在本项目中表示本功能块中的 `configured` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("controller_config", {}).get(`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`controller_config` 表示配置相关值。
    configured = report.get("controller_config", {}).get(
# 【L0037】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"policy_gripper_actual_open_threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的帮助说明、错误原因、任务名称或报告文字。
        "policy_gripper_actual_open_threshold"
# 【L0038】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”。
    )
# 【L0039】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`float(configured) if isinstance(configured, (int, float)) else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `float(configured) if isinstance(configured, (int, float)) else None` 交回调用者；这个值的含义是：计算表达式 `float(configured) if isinstance(configured, (int, float)) else None`；`configured` 表示本功能块中的 `configured` 值；`isinstance` 表示本功能块中的 `isinstance` 值。
    return float(configured) if isinstance(configured, (int, float)) else None
# 【L0040】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0041】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0042】语法拆解：`def` 定义函数 `report_policy_noise_seed`；第一对圆括号列出形参，逗号负责分隔：`report: dict` 用冒号给参数加类型提示；`-> int | None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `report_policy_noise_seed(report: dict)`；调用者把参数交给它完成“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”，后面的缩进代码是具体实现。
def report_policy_noise_seed(report: dict) -> int | None:
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_level`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"policy_noise_seed"`。
# 【项目含义】得到 `top_level`，它在本项目中表示本功能块中的 `top_level` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("policy_noise_seed")`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`policy_noise_seed` 表示策略相关值。
    top_level = report.get("policy_noise_seed")
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sampling`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"deterministic_sampling"`；第 2 个实参 `{}`。
# 【项目含义】得到 `sampling`，它在本项目中表示本功能块中的 `sampling` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("deterministic_sampling", {})`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`deterministic_sampling` 表示本功能块中的 `deterministic_sampling` 值。
    sampling = report.get("deterministic_sampling", {})
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `nested`。右侧语法为：`sampling.get("case_seed") if isinstance(sampling, dict) else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `nested`，它在本项目中表示本功能块中的 `nested` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sampling.get("case_seed") if isinstance(sampling, dict) else None`；`sampling` 表示本功能块中的 `sampling` 值；`get` 表示本功能块中的 `get` 值；`case_seed` 表示本功能块中的 `case_seed` 值。
    nested = sampling.get("case_seed") if isinstance(sampling, dict) else None
# 【L0046】语法拆解：`if` 要求条件 `any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested))` 是否成立；`any` 表示本功能块中的 `any` 值；`isinstance` 表示本功能块中的 `isinstance` 值；`value` 表示本功能块中的 `value` 值
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested)):
# 【L0047】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0048】语法拆解：`if` 要求条件 `top_level < 0 or nested < 0 or top_level != nested` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `top_level < 0 or nested < 0 or top_level != nested` 是否成立；`top_level` 表示本功能块中的 `top_level` 值；`nested` 表示本功能块中的 `nested` 值
    if top_level < 0 or nested < 0 or top_level != nested:
# 【L0049】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0050】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`top_level` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `top_level` 交回调用者；这个值的含义是：计算表达式 `top_level`；`top_level` 表示本功能块中的 `top_level` 值。
    return top_level
# 【L0051】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0052】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0053】语法拆解：`def` 定义函数 `report_simulation_seed`；第一对圆括号列出形参，逗号负责分隔：`report: dict` 用冒号给参数加类型提示；`-> int | None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `report_simulation_seed(report: dict)`；调用者把参数交给它完成“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”，后面的缩进代码是具体实现。
def report_simulation_seed(report: dict) -> int | None:
# 【L0054】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_level`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"simulation_seed"`。
# 【项目含义】得到 `top_level`，它在本项目中表示本功能块中的 `top_level` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("simulation_seed")`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`simulation_seed` 表示本功能块中的 `simulation_seed` 值。
    top_level = report.get("simulation_seed")
# 【L0055】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `determinism`。右侧语法为：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"simulation_determinism"`；第 2 个实参 `{}`。
# 【项目含义】得到 `determinism`，它在本项目中表示本功能块中的 `determinism` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report.get("simulation_determinism", {})`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`simulation_determinism` 表示本功能块中的 `simulation_determinism` 值。
    determinism = report.get("simulation_determinism", {})
# 【L0056】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `nested`。右侧语法为：`determinism.get("seed") if isinstance(determinism, dict) else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `nested`，它在本项目中表示本功能块中的 `nested` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `determinism.get("seed") if isinstance(determinism, dict) else None`；`determinism` 表示本功能块中的 `determinism` 值；`get` 表示本功能块中的 `get` 值；`seed` 表示本功能块中的 `seed` 值。
    nested = determinism.get("seed") if isinstance(determinism, dict) else None
# 【L0057】语法拆解：`if` 要求条件 `any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested))` 是否成立；`any` 表示本功能块中的 `any` 值；`isinstance` 表示本功能块中的 `isinstance` 值；`value` 表示本功能块中的 `value` 值
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested)):
# 【L0058】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0059】语法拆解：`if` 要求条件 `top_level < 0 or nested < 0 or top_level != nested` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `top_level < 0 or nested < 0 or top_level != nested` 是否成立；`top_level` 表示本功能块中的 `top_level` 值；`nested` 表示本功能块中的 `nested` 值
    if top_level < 0 or nested < 0 or top_level != nested:
# 【L0060】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0061】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`top_level` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `top_level` 交回调用者；这个值的含义是：计算表达式 `top_level`；`top_level` 表示本功能块中的 `top_level` 值。
    return top_level
# 【L0062】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

# 【L0063】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：检查评测计划 case 数量、ID 唯一性和任务扰动字段（源码第 64-86 行）

### 5.A 数据流位置

- 上游：模块 2“从单条报告读取实际/命令夹爪阈值与策略、仿真随机种子”。
- 本模块：检查评测计划 case 数量、ID 唯一性和任务扰动字段。
- 下游：处理结果继续交给模块 4“根据有效报告数、成功率和重复性条件计算 suite gate”。

### 5.B 为什么需要这一组代码

这一组负责“检查评测计划 case 数量、ID 唯一性和任务扰动字段”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。

### 5.D 本模块首次阅读要认识的调用

- `validate_evaluation_cases(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `case.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `any(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `isinstance(...)`：圆括号表示真正执行调用；判断一个对象是否属于指定类型；本项目常用它区分 bytes、字符串或数组。
- `set(...)`：圆括号表示真正执行调用；修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。

### 5.E 本模块定义的新函数

### 函数卡：`validate_evaluation_cases()`（第 64-84 行）

- 定义了什么：检查评测计划 case 数量、ID 唯一性和任务扰动字段。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`cases`：类型 `list[dict]`；项目含义是经过 split/max-cases 过滤后本次要运行的实验条件列表
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:275` 的 `validate_evaluation_cases(cases)`


### 5.F 这一模块的版本变化

- 当前第 35-119 行相对旧教学快照发生 `insert`：旧版 0 行，当前 85 行。 当前代码摘录：`def report_gripper_actual_open_threshold(report: dict) -> float | None:` / `configured = report.get("controller_config", {}).get(` / `"policy_gripper_actual_open_threshold"` / `)`

### 5.G 逐行精读

```python
# 【L0064】语法拆解：`def` 定义函数 `validate_evaluation_cases`；第一对圆括号列出形参，逗号负责分隔：`cases: list[dict]` 用冒号给参数加类型提示；`-> None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `validate_evaluation_cases(cases: list[dict])`；调用者把参数交给它完成“检查评测计划 case 数量、ID 唯一性和任务扰动字段”，后面的缩进代码是具体实现。
def validate_evaluation_cases(cases: list[dict]) -> None:
# 【L0065】语法拆解：`if` 要求条件 `not cases` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not cases` 是否成立；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表
    if not cases:
# 【L0066】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation plan has no cases")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation plan has no cases")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation plan has no cases")
# 【L0067】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_ids`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `case_ids`，它在本项目中表示本功能块中的 `case_ids` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[case.get("case_id") for case in cases]`；`case` 表示本功能块中的 `case` 值；`get` 表示本功能块中的 `get` 值；`case_id` 表示本功能块中的 `case_id` 值。
    case_ids = [case.get("case_id") for case in cases]
# 【L0068】语法拆解：`if` 要求条件 `any(not isinstance(case_id, str) or not case_id for case_id in case_ids)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `any(not isinstance(case_id, str) or not case_id for case_id in case_ids)` 是否成立；`any` 表示本功能块中的 `any` 值；`isinstance` 表示本功能块中的 `isinstance` 值；`case_id` 表示本功能块中的 `case_id` 值
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
# 【L0069】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("every evaluation case must have a non-empty case_id")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("every evaluation case must have a non-empty case_id")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("every evaluation case must have a non-empty case_id")
# 【L0070】语法拆解：`if` 要求条件 `len(set(case_ids)) != len(case_ids)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(set(case_ids)) != len(case_ids)` 是否成立；`set` 表示本功能块中的 `set` 值；`case_ids` 表示本功能块中的 `case_ids` 值
    if len(set(case_ids)) != len(case_ids):
# 【L0071】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation case ids must be unique")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation case ids must be unique")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation case ids must be unique")
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `seeds`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `seeds`，它在本项目中表示本功能块中的 `seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[case.get("policy_noise_seed") for case in cases]`；`case` 表示本功能块中的 `case` 值；`get` 表示本功能块中的 `get` 值；`policy_noise_seed` 表示策略相关值。
    seeds = [case.get("policy_noise_seed") for case in cases]
# 【L0073】语法拆解：`if` 要求条件 `any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds)` 是否成立；`any` 表示本功能块中的 `any` 值；`isinstance` 表示本功能块中的 `isinstance` 值；`seed` 表示本功能块中的 `seed` 值
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
# 【L0074】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("every evaluation case must have a non-negative integer policy_noise_seed")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("every evaluation case must have a non-negative integer policy_noise_seed")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("every evaluation case must have a non-negative integer policy_noise_seed")
# 【L0075】语法拆解：`if` 要求条件 `len(set(seeds)) != len(seeds)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(set(seeds)) != len(seeds)` 是否成立；`set` 表示本功能块中的 `set` 值；`seeds` 表示本功能块中的 `seeds` 值
    if len(set(seeds)) != len(seeds):
# 【L0076】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation policy_noise_seed values must be unique")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation policy_noise_seed values must be unique")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation policy_noise_seed values must be unique")
# 【L0077】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_seeds`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `simulation_seeds`，它在本项目中表示本功能块中的 `simulation_seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[case.get("simulation_seed") for case in cases]`；`case` 表示本功能块中的 `case` 值；`get` 表示本功能块中的 `get` 值；`simulation_seed` 表示本功能块中的 `simulation_seed` 值。
    simulation_seeds = [case.get("simulation_seed") for case in cases]
# 【L0078】语法拆解：`if` 要求条件 `any(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `any(` 是否成立；`any` 表示本功能块中的 `any` 值
    if any(
# 【L0079】语法拆解：表达式 `isinstance(seed, bool) or not isinstance(seed, int) or seed < 0` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `isinstance(seed, bool) or not isinstance(seed, int) or seed < 0` 接到上一行尚未结束的布尔表达式；`isinstance` 表示本功能块中的 `isinstance` 值；`seed` 表示本功能块中的 `seed` 值。比较结果共同决定“检查评测计划 case 数量、ID 唯一性和任务扰动字段”是否通过。
        isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
# 【L0080】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for seed in simulation_seeds` 中给出的序列，逐项完成“检查评测计划 case 数量、ID 唯一性和任务扰动字段”。
        for seed in simulation_seeds
# 【L0081】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“检查评测计划 case 数量、ID 唯一性和任务扰动字段”。
    ):
# 【L0082】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("every evaluation case must have a non-negative integer simulation_seed")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("every evaluation case must have a non-negative integer simulation_seed")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("every evaluation case must have a non-negative integer simulation_seed")
# 【L0083】语法拆解：`if` 要求条件 `len(set(simulation_seeds)) != len(simulation_seeds)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(set(simulation_seeds)) != len(simulation_seeds)` 是否成立；`set` 表示本功能块中的 `set` 值；`simulation_seeds` 表示本功能块中的 `simulation_seeds` 值
    if len(set(simulation_seeds)) != len(simulation_seeds):
# 【L0084】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("evaluation simulation_seed values must be unique")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("evaluation simulation_seed values must be unique")` 并停止当前路径；说明当前输入违反“检查评测计划 case 数量、ID 唯一性和任务扰动字段”要求，不能继续进入仿真、训练或评测。
        raise ValueError("evaluation simulation_seed values must be unique")
# 【L0085】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“检查评测计划 case 数量、ID 唯一性和任务扰动字段”中的逻辑段，让结构更容易看清。

# 【L0086】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“检查评测计划 case 数量、ID 唯一性和任务扰动字段”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“检查评测计划 case 数量、ID 唯一性和任务扰动字段”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：根据有效报告数、成功率和重复性条件计算 suite gate（源码第 87-119 行）

### 5.A 数据流位置

- 上游：模块 3“检查评测计划 case 数量、ID 唯一性和任务扰动字段”。
- 本模块：根据有效报告数、成功率和重复性条件计算 suite gate。
- 下游：处理结果继续交给模块 5“严格核对旧报告身份与完整性，决定能否安全复用”。

### 5.B 为什么需要这一组代码

这一组负责“根据有效报告数、成功率和重复性条件计算 suite gate”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `success_rate`：有效闭环报告中 status=pass 的比例。
- `passed`：当前单条任务或整套评测是否满足所有硬性门槛。

### 5.D 本模块首次阅读要认识的调用

- `evaluate_suite_gate(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `min(...)`：圆括号表示真正执行调用；从候选值中选择最小者；常用于限制执行步数或选择代价最小的 IK 分支。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `all(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `checks.values(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`evaluate_suite_gate()`（第 87-117 行）

- 定义了什么：根据有效报告数、成功率和重复性条件计算 suite gate。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`planned_case_count`：类型 `int`；项目含义是数量相关值；`valid_report_count`：类型 `int`；项目含义是报告、数量相关值；`success_count`：类型 `int`；项目含义是成功、数量相关值；`minimum_episode_count`（仅关键字）：类型 `int`，默认 `20`；项目含义是一条轨迹、数量相关值；`minimum_success_rate`（仅关键字）：类型 `float`，默认 `0.8`；项目含义是成功相关值
- 返回类型标注：`dict`。
- 函数体实际 return：`{'passed': all(checks.values()), 'minimum_episode_count': minimum_episode_count, 'minimum_success_rate': minimum_success_rate, 'require_all_planned_reports': True, 'missing_report_count': planned_case_count - valid_report_count, 'success_rate': success_rate, 'checks': checks}`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:466` 的 `gate = evaluate_suite_gate(`


### 5.F 这一模块的版本变化

- 当前第 35-119 行相对旧教学快照发生 `insert`：旧版 0 行，当前 85 行。 当前代码摘录：`def report_gripper_actual_open_threshold(report: dict) -> float | None:` / `configured = report.get("controller_config", {}).get(` / `"policy_gripper_actual_open_threshold"` / `)`

### 5.G 逐行精读

```python
# 【L0087】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `evaluate_suite_gate(参数在后续行继续)`；调用者把参数交给它完成“根据有效报告数、成功率和重复性条件计算 suite gate”，后面的缩进代码是具体实现。
def evaluate_suite_gate(
# 【L0088】语法拆解：`planned_case_count` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `planned_case_count`，类型提示为 `int`；在本项目中它表示数量相关值。
    planned_case_count: int,
# 【L0089】语法拆解：`valid_report_count` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `valid_report_count`，类型提示为 `int`；在本项目中它表示报告、数量相关值。
    valid_report_count: int,
# 【L0090】语法拆解：`success_count` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `success_count`，类型提示为 `int`；在本项目中它表示成功、数量相关值。
    success_count: int,
# 【L0091】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“根据有效报告数、成功率和重复性条件计算 suite gate”。
    *,
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_episode_count: int`。右侧语法为：`20` 是直接写在源码中的数值常量。
# 【项目含义】得到 `minimum_episode_count`，它在本项目中表示一条轨迹、数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `20` 的结果保存下来，供当前功能块后续使用。
    minimum_episode_count: int = 20,
# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_success_rate: float`。右侧语法为：`0.8` 是直接写在源码中的数值常量。
# 【项目含义】得到 `minimum_success_rate`，它在本项目中表示成功相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.8` 的结果保存下来，供当前功能块后续使用。
    minimum_success_rate: float = 0.8,
# 【L0094】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> dict:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“根据有效报告数、成功率和重复性条件计算 suite gate”。
) -> dict:
# 【L0095】语法拆解：`if` 要求条件 `min(planned_case_count, valid_report_count, success_count) < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `min(planned_case_count, valid_report_count, success_count) < 0` 是否成立；`planned_case_count` 表示数量相关值；`valid_report_count` 表示报告、数量相关值；`success_count` 表示成功、数量相关值
    if min(planned_case_count, valid_report_count, success_count) < 0:
# 【L0096】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("suite counts must be non-negative")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("suite counts must be non-negative")` 并停止当前路径；说明当前输入违反“根据有效报告数、成功率和重复性条件计算 suite gate”要求，不能继续进入仿真、训练或评测。
        raise ValueError("suite counts must be non-negative")
# 【L0097】语法拆解：`if` 要求条件 `valid_report_count > planned_case_count or success_count > valid_report_count` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `valid_report_count > planned_case_count or success_count > valid_report_count` 是否成立；`valid_report_count` 表示报告、数量相关值；`planned_case_count` 表示数量相关值；`success_count` 表示成功、数量相关值
    if valid_report_count > planned_case_count or success_count > valid_report_count:
# 【L0098】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("suite counts are inconsistent")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("suite counts are inconsistent")` 并停止当前路径；说明当前输入违反“根据有效报告数、成功率和重复性条件计算 suite gate”要求，不能继续进入仿真、训练或评测。
        raise ValueError("suite counts are inconsistent")
# 【L0099】语法拆解：`if` 要求条件 `minimum_episode_count < 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `minimum_episode_count < 1` 是否成立；`minimum_episode_count` 表示一条轨迹、数量相关值
    if minimum_episode_count < 1:
# 【L0100】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("minimum_episode_count must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("minimum_episode_count must be positive")` 并停止当前路径；说明当前输入违反“根据有效报告数、成功率和重复性条件计算 suite gate”要求，不能继续进入仿真、训练或评测。
        raise ValueError("minimum_episode_count must be positive")
# 【L0101】语法拆解：`if` 要求条件 `not 0.0 <= minimum_success_rate <= 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= minimum_success_rate <= 1.0` 是否成立；`minimum_success_rate` 表示成功相关值
    if not 0.0 <= minimum_success_rate <= 1.0:
# 【L0102】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("minimum_success_rate must be within [0, 1]")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("minimum_success_rate must be within [0, 1]")` 并停止当前路径；说明当前输入违反“根据有效报告数、成功率和重复性条件计算 suite gate”要求，不能继续进入仿真、训练或评测。
        raise ValueError("minimum_success_rate must be within [0, 1]")
# 【L0103】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `success_rate`。右侧语法为：表达式 `success_count / valid_report_count if valid_report_count else 0.0` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `success_rate`，它在本项目中表示有效闭环报告中 status=pass 的比例；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `success_count / valid_report_count if valid_report_count else 0.0`；`success_count` 表示成功、数量相关值；`valid_report_count` 表示报告、数量相关值。
    success_rate = success_count / valid_report_count if valid_report_count else 0.0
# 【L0104】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checks`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `checks`，它在本项目中表示本功能块中的 `checks` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    checks = {
# 【L0105】语法拆解：这是字典键值对：`"minimum_episode_count_met"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `valid_report_count >= minimum_episode_count` 使用运算符 `>=`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `minimum_episode_count_met`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `minimum_episode_count_met` 数据；字段值来自 `valid_report_count >= minimum_episode_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "minimum_episode_count_met": valid_report_count >= minimum_episode_count,
# 【L0106】语法拆解：这是字典键值对：`"all_planned_reports_present"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `valid_report_count == planned_case_count` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `all_planned_reports_present`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `all_planned_reports_present` 数据；字段值来自 `valid_report_count == planned_case_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_planned_reports_present": valid_report_count == planned_case_count,
# 【L0107】语法拆解：这是字典键值对：`"minimum_success_rate_met"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `success_rate >= minimum_success_rate` 使用运算符 `>=`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `minimum_success_rate_met`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `minimum_success_rate_met` 数据；字段值来自 `success_rate >= minimum_success_rate`，因此保存/传递的是这个表达式当前计算出的结果。
        "minimum_success_rate_met": success_rate >= minimum_success_rate,
# 【L0108】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据有效报告数、成功率和重复性条件计算 suite gate”。
    }
# 【L0109】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0110】语法拆解：这是字典键值对：`"passed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`all` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checks.values()`。
# 【项目含义】定义字典/JSON 字段 `passed`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `passed` 数据；字段值来自 `all(checks.values())`，因此保存/传递的是这个表达式当前计算出的结果。
        "passed": all(checks.values()),
# 【L0111】语法拆解：这是字典键值对：`"minimum_episode_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`minimum_episode_count` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `minimum_episode_count`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `minimum_episode_count` 数据；字段值来自 `minimum_episode_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "minimum_episode_count": minimum_episode_count,
# 【L0112】语法拆解：这是字典键值对：`"minimum_success_rate"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`minimum_success_rate` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `minimum_success_rate`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `minimum_success_rate` 数据；字段值来自 `minimum_success_rate`，因此保存/传递的是这个表达式当前计算出的结果。
        "minimum_success_rate": minimum_success_rate,
# 【L0113】语法拆解：这是字典键值对：`"require_all_planned_reports"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `require_all_planned_reports`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `require_all_planned_reports` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "require_all_planned_reports": True,
# 【L0114】语法拆解：这是字典键值对：`"missing_report_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `planned_case_count - valid_report_count` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `missing_report_count`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `missing_report_count` 数据；字段值来自 `planned_case_count - valid_report_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "missing_report_count": planned_case_count - valid_report_count,
# 【L0115】语法拆解：这是字典键值对：`"success_rate"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`success_rate` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `success_rate`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `success_rate` 数据；字段值来自 `success_rate`，因此保存/传递的是这个表达式当前计算出的结果。
        "success_rate": success_rate,
# 【L0116】语法拆解：这是字典键值对：`"checks"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`checks` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `checks`，它表示“根据有效报告数、成功率和重复性条件计算 suite gate”中的 `checks` 数据；字段值来自 `checks`，因此保存/传递的是这个表达式当前计算出的结果。
        "checks": checks,
# 【L0117】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据有效报告数、成功率和重复性条件计算 suite gate”。
    }
# 【L0118】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据有效报告数、成功率和重复性条件计算 suite gate”中的逻辑段，让结构更容易看清。

# 【L0119】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据有效报告数、成功率和重复性条件计算 suite gate”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“根据有效报告数、成功率和重复性条件计算 suite gate”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：严格核对旧报告身份与完整性，决定能否安全复用（源码第 120-190 行）

### 5.A 数据流位置

- 上游：模块 4“根据有效报告数、成功率和重复性条件计算 suite gate”。
- 本模块：严格核对旧报告身份与完整性，决定能否安全复用。
- 下游：处理结果继续交给模块 6“解析批量评测参数与互斥、范围和重复性门槛”。

### 5.B 为什么需要这一组代码

这一组负责“严格核对旧报告身份与完整性，决定能否安全复用”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。

### 5.D 本模块首次阅读要认识的调用

- `load_existing_report(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `path.is_file(...)`：圆括号表示真正执行调用；检查路径是否存在且确实是普通文件。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `path.read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `report.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `abs(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `report_gripper_open_threshold(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `report_gripper_actual_open_threshold(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `report_policy_noise_seed(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `report_simulation_seed(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.E 本模块定义的新函数

### 函数卡：`load_existing_report()`（第 120-188 行）

- 定义了什么：严格核对旧报告身份与完整性，决定能否安全复用。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`path`：类型 `Path`；项目含义是路径相关值；`checkpoint_id`：类型 `str`；项目含义是模型检查点相关值；`gripper_open_threshold`：类型 `float`；项目含义是夹爪相关值；`gripper_actual_open_threshold`：类型 `float`；项目含义是夹爪、物理仿真实际值相关值；`policy_max_action_chunks`：类型 `int`；项目含义是策略、动作相关值；`reset_renderer_accumulation`：类型 `bool`；项目含义是本功能块中的 `reset_renderer_accumulation` 值；`policy_noise_seed`：类型 `int`；项目含义是策略相关值；`simulation_seed`：类型 `int`；项目含义是本功能块中的 `simulation_seed` 值；`prompt`：类型 `str`；项目含义是本功能块中的 `prompt` 值；`transfer_joint_1_rad`：类型 `float`；项目含义是关节相关值；`source_offset_x_m`：类型 `float`；项目含义是源位置相关值；`source_offset_y_m`：类型 `float`；项目含义是源位置相关值
- 返回类型标注：`dict | None`。
- 函数体实际 return：`report`；`None`；`None`；`None`；`None`
- 项目中的实际调用位置：`run_pi05_rm65_closed_loop_suite.py:344` 的 `existing = load_existing_report(`；`run_pi05_rm65_closed_loop_suite.py:417` 的 `report = load_existing_report(`


### 5.F 这一模块的版本变化

- 当前第 121-132 行相对旧教学快照发生 `replace`：旧版 1 行，当前 12 行。 旧代码摘录：`path: Path, checkpoint_id: str, gripper_open_threshold: float` 当前代码摘录：`path: Path,` / `checkpoint_id: str,` / `gripper_open_threshold: float,` / `gripper_actual_open_threshold: float,`
- 当前第 140-141 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`if report.get("status") not in {"pass", "fail"}:` / `return None`
- 当前第 144-162 行相对旧教学快照发生 `replace`：旧版 1 行，当前 19 行。 旧代码摘录：`if report.get("pi05_used") is not True or report.get("simulation_only") is not True:` 当前代码摘录：`if (` / `report.get("pi05_used") is not True` / `or report.get("simulation_only") is not True` / `or report.get("real_robot_command_sent") is not False`
- 当前第 166-186 行相对旧教学快照发生 `insert`：旧版 0 行，当前 21 行。 当前代码摘录：`return None` / `existing_actual_threshold = report_gripper_actual_open_threshold(report)` / `if (` / `existing_actual_threshold is None`

### 5.G 逐行精读

```python
# 【L0120】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `load_existing_report(参数在后续行继续)`；调用者把参数交给它完成“严格核对旧报告身份与完整性，决定能否安全复用”，后面的缩进代码是具体实现。
def load_existing_report(
# 【L0121】语法拆解：`path` 是参数/字段名；冒号 `:` 添加类型提示 `Path`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `path`，类型提示为 `Path`；在本项目中它表示路径相关值。
    path: Path,
# 【L0122】语法拆解：`checkpoint_id` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `checkpoint_id`，类型提示为 `str`；在本项目中它表示模型检查点相关值。
    checkpoint_id: str,
# 【L0123】语法拆解：`gripper_open_threshold` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `gripper_open_threshold`，类型提示为 `float`；在本项目中它表示夹爪相关值。
    gripper_open_threshold: float,
# 【L0124】语法拆解：`gripper_actual_open_threshold` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `gripper_actual_open_threshold`，类型提示为 `float`；在本项目中它表示夹爪、物理仿真实际值相关值。
    gripper_actual_open_threshold: float,
# 【L0125】语法拆解：`policy_max_action_chunks` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `policy_max_action_chunks`，类型提示为 `int`；在本项目中它表示策略、动作相关值。
    policy_max_action_chunks: int,
# 【L0126】语法拆解：`reset_renderer_accumulation` 是参数/字段名；冒号 `:` 添加类型提示 `bool`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `reset_renderer_accumulation`，类型提示为 `bool`；在本项目中它表示本功能块中的 `reset_renderer_accumulation` 值。
    reset_renderer_accumulation: bool,
# 【L0127】语法拆解：`policy_noise_seed` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `policy_noise_seed`，类型提示为 `int`；在本项目中它表示策略相关值。
    policy_noise_seed: int,
# 【L0128】语法拆解：`simulation_seed` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `simulation_seed`，类型提示为 `int`；在本项目中它表示本功能块中的 `simulation_seed` 值。
    simulation_seed: int,
# 【L0129】语法拆解：`prompt` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `prompt`，类型提示为 `str`；在本项目中它表示本功能块中的 `prompt` 值。
    prompt: str,
# 【L0130】语法拆解：`transfer_joint_1_rad` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `transfer_joint_1_rad`，类型提示为 `float`；在本项目中它表示关节相关值。
    transfer_joint_1_rad: float,
# 【L0131】语法拆解：`source_offset_x_m` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `source_offset_x_m`，类型提示为 `float`；在本项目中它表示源位置相关值。
    source_offset_x_m: float,
# 【L0132】语法拆解：`source_offset_y_m` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `source_offset_y_m`，类型提示为 `float`；在本项目中它表示源位置相关值。
    source_offset_y_m: float,
# 【L0133】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> dict | None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
) -> dict | None:
# 【L0134】语法拆解：`if` 要求条件 `not path.is_file()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not path.is_file()` 是否成立；`path` 表示路径相关值；`is_file` 表示本功能块中的 `is_file` 值
    if not path.is_file():
# 【L0135】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0136】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“严格核对旧报告身份与完整性，决定能否安全复用”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0137】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `path.read_text(encoding="utf-8")`。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
        report = json.loads(path.read_text(encoding="utf-8"))
# 【L0138】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `(OSError, json.JSONDecodeError)`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
    except (OSError, json.JSONDecodeError):
# 【L0139】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0140】语法拆解：`if` 要求条件 `report.get("status") not in {"pass", "fail"}` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report.get("status") not in {"pass", "fail"}` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`status` 表示本功能块中的 `status` 值
    if report.get("status") not in {"pass", "fail"}:
# 【L0141】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0142】语法拆解：`if` 要求条件 `report.get("policy_checkpoint_id") != checkpoint_id` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report.get("policy_checkpoint_id") != checkpoint_id` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`policy_checkpoint_id` 表示策略、模型检查点相关值
    if report.get("policy_checkpoint_id") != checkpoint_id:
# 【L0143】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0144】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
    if (
# 【L0145】语法拆解：`report.get("pi05_used") is not True` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `report.get("pi05_used") is not True` 接入当前完整语句；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`pi05_used` 表示本功能块中的 `pi05_used` 值。在“严格核对旧报告身份与完整性，决定能否安全复用”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        report.get("pi05_used") is not True
# 【L0146】语法拆解：`or report.get("simulation_only") is not True` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `report.get("simulation_only") is not True` 用“或者”接到上一行判断中；判断 `report.get("simulation_only") is not True` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`simulation_only` 表示本功能块中的 `simulation_only` 值。所有连接条件共同决定是否进入后续分支。
        or report.get("simulation_only") is not True
# 【L0147】语法拆解：`or report.get("real_robot_command_sent") is not False` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `report.get("real_robot_command_sent") is not False` 用“或者”接到上一行判断中；判断 `report.get("real_robot_command_sent") is not False` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`real_robot_command_sent` 表示控制命令相关值。所有连接条件共同决定是否进入后续分支。
        or report.get("real_robot_command_sent") is not False
# 【L0148】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
    ):
# 【L0149】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0150】语法拆解：`if` 要求条件 `report.get("prompt") != prompt` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report.get("prompt") != prompt` 是否成立；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`prompt` 表示本功能块中的 `prompt` 值
    if report.get("prompt") != prompt:
# 【L0151】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0152】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“严格核对旧报告身份与完整性，决定能否安全复用”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0153】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_angle`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report.get("transfer_joint_1_rad")`。
# 【项目含义】得到 `report_angle`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(report.get("transfer_joint_1_rad"))`；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值；`transfer_joint_1_rad` 表示关节相关值。
        report_angle = float(report.get("transfer_joint_1_rad"))
# 【L0154】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_offsets`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `report_offsets`，它在本项目中表示报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[float(value) for value in report.get("source_offset_xy_m", [])]`；`value` 表示本功能块中的 `value` 值；`report` 表示机器可读实验报告字典；`get` 表示本功能块中的 `get` 值。
        report_offsets = [float(value) for value in report.get("source_offset_xy_m", [])]
# 【L0155】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `(TypeError, ValueError)`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
    except (TypeError, ValueError):
# 【L0156】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0157】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
    if (
# 【L0158】语法拆解：表达式 `abs(report_angle - transfer_joint_1_rad) > 1e-9` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `abs(report_angle - transfer_joint_1_rad) > 1e-9` 接到上一行尚未结束的布尔表达式；`abs` 表示本功能块中的 `abs` 值；`report_angle` 表示报告相关值；`transfer_joint_1_rad` 表示关节相关值。比较结果共同决定“严格核对旧报告身份与完整性，决定能否安全复用”是否通过。
        abs(report_angle - transfer_joint_1_rad) > 1e-9
# 【L0159】语法拆解：表达式 `or len(report_offsets) != 2` 使用运算符 `!=`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `len(report_offsets) != 2` 用“或者”接到上一行判断中；判断 `len(report_offsets) != 2` 是否成立；`report_offsets` 表示报告相关值。所有连接条件共同决定是否进入后续分支。
        or len(report_offsets) != 2
# 【L0160】语法拆解：表达式 `or abs(report_offsets[0] - source_offset_x_m) > 1e-9` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `abs(report_offsets[0] - source_offset_x_m) > 1e-9` 用“或者”接到上一行判断中；判断 `abs(report_offsets[0] - source_offset_x_m) > 1e-9` 是否成立；`abs` 表示本功能块中的 `abs` 值；`report_offsets` 表示报告相关值；`source_offset_x_m` 表示源位置相关值。所有连接条件共同决定是否进入后续分支。
        or abs(report_offsets[0] - source_offset_x_m) > 1e-9
# 【L0161】语法拆解：表达式 `or abs(report_offsets[1] - source_offset_y_m) > 1e-9` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `abs(report_offsets[1] - source_offset_y_m) > 1e-9` 用“或者”接到上一行判断中；判断 `abs(report_offsets[1] - source_offset_y_m) > 1e-9` 是否成立；`abs` 表示本功能块中的 `abs` 值；`report_offsets` 表示报告相关值；`source_offset_y_m` 表示源位置相关值。所有连接条件共同决定是否进入后续分支。
        or abs(report_offsets[1] - source_offset_y_m) > 1e-9
# 【L0162】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
    ):
# 【L0163】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0164】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `existing_threshold`。右侧语法为：`report_gripper_open_threshold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report`。
# 【项目含义】得到 `existing_threshold`，它在本项目中表示本功能块中的 `existing_threshold` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report_gripper_open_threshold(report)`；`report_gripper_open_threshold` 表示报告、夹爪相关值；`report` 表示机器可读实验报告字典。
    existing_threshold = report_gripper_open_threshold(report)
# 【L0165】语法拆解：`if` 要求条件 `existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9:
# 【L0166】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0167】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `existing_actual_threshold`。右侧语法为：`report_gripper_actual_open_threshold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report`。
# 【项目含义】得到 `existing_actual_threshold`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `report_gripper_actual_open_threshold(report)`；`report_gripper_actual_open_threshold` 表示报告、夹爪、物理仿真实际值相关值；`report` 表示机器可读实验报告字典。
    existing_actual_threshold = report_gripper_actual_open_threshold(report)
# 【L0168】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
    if (
# 【L0169】语法拆解：`existing_actual_threshold is None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `existing_actual_threshold is None` 接入当前完整语句；`existing_actual_threshold` 表示物理仿真实际值相关值。在“严格核对旧报告身份与完整性，决定能否安全复用”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        existing_actual_threshold is None
# 【L0170】语法拆解：表达式 `or abs(existing_actual_threshold - gripper_actual_open_threshold) > 1e-9` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `abs(existing_actual_threshold - gripper_actual_open_threshold) > 1e-9` 用“或者”接到上一行判断中；判断 `abs(existing_actual_threshold - gripper_actual_open_threshold) > 1e-9` 是否成立；`abs` 表示本功能块中的 `abs` 值；`existing_actual_threshold` 表示物理仿真实际值相关值；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值。所有连接条件共同决定是否进入后续分支。
        or abs(existing_actual_threshold - gripper_actual_open_threshold) > 1e-9
# 【L0171】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
    ):
# 【L0172】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0173】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
    if (
# 【L0174】语法拆解：`report` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"controller_config"`；第 2 个实参 `{}).get("policy_max_action_chunks"`。
# 【项目含义】对 `report` 调用 `get("controller_config", {}).get("policy_max_action_chunks")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“严格核对旧报告身份与完整性，决定能否安全复用”。
        report.get("controller_config", {}).get("policy_max_action_chunks")
# 【L0175】语法拆解：表达式 `!= policy_max_action_chunks` 使用运算符 `!=`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `!= policy_max_action_chunks` 接入当前完整语句；`policy_max_action_chunks` 表示策略、动作相关值。在“严格核对旧报告身份与完整性，决定能否安全复用”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        != policy_max_action_chunks
# 【L0176】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
    ):
# 【L0177】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0178】语法拆解：`if` 要求条件 `bool(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `bool(` 是否成立；成立时执行紧随其后的缩进代码
    if bool(
# 【L0179】语法拆解：`report.get("controller_config", {}).get(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `report.get("controller_config", {})` 调用多行方法 `get`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值；具体参数写在随后几行，用于“严格核对旧报告身份与完整性，决定能否安全复用”。
        report.get("controller_config", {}).get(
# 【L0180】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"reset_renderer_accumulation_before_policy_observation", False`；Python 会把相邻字符串自动拼接，外层参数会把它用作“严格核对旧报告身份与完整性，决定能否安全复用”中的帮助说明、错误原因、任务名称或报告文字。
            "reset_renderer_accumulation_before_policy_observation", False
# 【L0181】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“严格核对旧报告身份与完整性，决定能否安全复用”。
        )
# 【L0182】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) != reset_renderer_accumulation:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“严格核对旧报告身份与完整性，决定能否安全复用”。
    ) != reset_renderer_accumulation:
# 【L0183】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0184】语法拆解：`if` 要求条件 `report_policy_noise_seed(report) != policy_noise_seed` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report_policy_noise_seed(report) != policy_noise_seed` 是否成立；`report_policy_noise_seed` 表示报告、策略相关值；`report` 表示机器可读实验报告字典；`policy_noise_seed` 表示策略相关值
    if report_policy_noise_seed(report) != policy_noise_seed:
# 【L0185】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0186】语法拆解：`if` 要求条件 `report_simulation_seed(report) != simulation_seed` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `report_simulation_seed(report) != simulation_seed` 是否成立；`report_simulation_seed` 表示报告相关值；`report` 表示机器可读实验报告字典；`simulation_seed` 表示本功能块中的 `simulation_seed` 值
    if report_simulation_seed(report) != simulation_seed:
# 【L0187】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        return None
# 【L0188】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`report` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `report` 交回调用者；这个值的含义是：计算表达式 `report`；`report` 表示机器可读实验报告字典。
    return report
# 【L0189】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格核对旧报告身份与完整性，决定能否安全复用”中的逻辑段，让结构更容易看清。

# 【L0190】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“严格核对旧报告身份与完整性，决定能否安全复用”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“严格核对旧报告身份与完整性，决定能否安全复用”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 6：解析批量评测参数与互斥、范围和重复性门槛（源码第 191-264 行）

### 5.A 数据流位置

- 上游：模块 5“严格核对旧报告身份与完整性，决定能否安全复用”。
- 本模块：解析批量评测参数与互斥、范围和重复性门槛。
- 下游：处理结果继续交给模块 7“载入 checkpoint/计划、准备环境并启动一次 policy server”。

### 5.B 为什么需要这一组代码

这一组负责“解析批量评测参数与互斥、范围和重复性门槛”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `report`：机器可读实验报告字典。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `checkpoint`：一次训练保存的模型参数目录。
- `output`：输出文件路径。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `os.environ.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 191-513 行）

- 定义了什么：解析批量评测参数与互斥、范围和重复性门槛。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0 if passed else 1`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 当前第 197-197 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json",` 当前代码摘录：`default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_deterministic_v1.json",`
- 当前第 217-222 行相对旧教学快照发生 `insert`：旧版 0 行，当前 6 行。 当前代码摘录：`"--gripper-actual-open-threshold",` / `type=float,` / `default=0.20,` / `help="Normalized actual 4C2 feedback threshold for release detection.",`
- 当前第 229-237 行相对旧教学快照发生 `insert`：旧版 0 行，当前 9 行。 当前代码摘录：`"--policy-max-action-chunks",` / `type=int,` / `default=EVALUATION_POLICY_MAX_ACTION_CHUNKS,` / `help=(`
- 当前第 242-249 行相对旧教学快照发生 `insert`：旧版 0 行，当前 8 行。 当前代码摘录：`)` / `parser.add_argument(` / `"--reset-renderer-accumulation-before-policy-observation",` / `action="store_true",`
- 当前第 256-257 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`if args.policy_max_action_chunks < 1:` / `raise ValueError("--policy-max-action-chunks must be positive")`
- 当前第 260-263 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`if not args.gripper_open_threshold <= args.gripper_actual_open_threshold < 1.0:` / `raise ValueError(` / `"--gripper-actual-open-threshold must be at least the target threshold and below 1"` / `)`

### 5.G 逐行精读

```python
# 【L0191】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“解析批量评测参数与互斥、范围和重复性门槛”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0192】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0193】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--checkpoint"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--checkpoint`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0194】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0195】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--plan"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--plan",
# 【L0196】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=Path,
# 【L0197】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_deterministic_v1.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_deterministic_v1.json"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_deterministic_v1.json",
# 【L0198】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0199】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0200】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--output-root"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--output-root",
# 【L0201】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=Path,
# 【L0202】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1",
# 【L0203】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0204】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0205】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--summary"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--summary",
# 【L0206】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=Path,
# 【L0207】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：表达式 `PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json",
# 【L0208】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0209】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-port"`；第 2 个实参 `type=int`；第 3 个实参 `default=8000`。
# 【项目含义】声明命令行参数 `--policy-port`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--policy-port", type=int, default=8000)
# 【L0210】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0211】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--gripper-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--gripper-open-threshold",
# 【L0212】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=float,
# 【L0213】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=0.12,
# 【L0214】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Normalized 4C2 threshold used for in-loop release verification."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Normalized 4C2 threshold used for in-loop release verification."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        help="Normalized 4C2 threshold used for in-loop release verification.",
# 【L0215】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0216】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0217】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--gripper-actual-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--gripper-actual-open-threshold",
# 【L0218】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=float,
# 【L0219】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.20` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.20`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=0.20,
# 【L0220】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Normalized actual 4C2 feedback threshold for release detection."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Normalized actual 4C2 feedback threshold for release detection."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        help="Normalized actual 4C2 feedback threshold for release detection.",
# 【L0221】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0222】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0223】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--repo-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--repo-id",
# 【L0224】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`os.environ` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"RM65_REPO_ID"`；第 2 个实参 `"local/rm65_sim_train"`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `os.environ.get("RM65_REPO_ID", "local/rm65_sim_train")`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=os.environ.get("RM65_REPO_ID", "local/rm65_sim_train"),
# 【L0225】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"LeRobot repository id whose normalization statistics belong to the checkpoint."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"LeRobot repository id whose normalization statistics belong to the checkpoint."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        help="LeRobot repository id whose normalization statistics belong to the checkpoint.",
# 【L0226】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0227】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--case-timeout-seconds"`；第 2 个实参 `type=int`；第 3 个实参 `default=1200`。
# 【项目含义】声明命令行参数 `--case-timeout-seconds`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--case-timeout-seconds", type=int, default=1200)
# 【L0228】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0229】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-max-action-chunks"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--policy-max-action-chunks",
# 【L0230】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=int,
# 【L0231】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`EVALUATION_POLICY_MAX_ACTION_CHUNKS` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `EVALUATION_POLICY_MAX_ACTION_CHUNKS`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=EVALUATION_POLICY_MAX_ACTION_CHUNKS,
# 【L0232】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        help=(
# 【L0233】语法拆解：`f"Use {EVALUATION_POLICY_MAX_ACTION_CHUNKS} for evaluation; other values "` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"Use {EVALUATION_POLICY_MAX_ACTION_CHUNKS} for evaluation; other values "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`Use` 表示本功能块中的 `Use` 值；`EVALUATION_POLICY_MAX_ACTION_CHUNKS` 表示策略、动作相关值。在“解析批量评测参数与互斥、范围和重复性门槛”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            f"Use {EVALUATION_POLICY_MAX_ACTION_CHUNKS} for evaluation; other values "
# 【L0234】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"are diagnostic-only."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
            "are diagnostic-only."
# 【L0235】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
        ),
# 【L0236】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0237】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0238】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--infrastructure-retries"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--infrastructure-retries",
# 【L0239】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        type=int,
# 【L0240】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`1` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `1`；该参数在本项目中表示本功能块中的 `default` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        default=1,
# 【L0241】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Retry only cases that fail to produce a valid task report."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Retry only cases that fail to produce a valid task report."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        help="Retry only cases that fail to produce a valid task report.",
# 【L0242】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0243】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0244】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--reset-renderer-accumulation-before-policy-observation"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
        "--reset-renderer-accumulation-before-policy-observation",
# 【L0245】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“解析批量评测参数与互斥、范围和重复性门槛”。
        action="store_true",
# 【L0246】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        help=(
# 【L0247】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Diagnostic-only renderer accumulation reset; included in the resume "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
            "Diagnostic-only renderer accumulation reset; included in the resume "
# 【L0248】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"contract and disabled by default."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
            "contract and disabled by default."
# 【L0249】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
        ),
# 【L0250】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
    )
# 【L0251】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--max-cases"`；第 2 个实参 `type=int`。
# 【项目含义】声明命令行参数 `--max-cases`；启动脚本可用它改变“解析批量评测参数与互斥、范围和重复性门槛”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--max-cases", type=int)
# 【L0252】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0253】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析批量评测参数与互斥、范围和重复性门槛”中的逻辑段，让结构更容易看清。

# 【L0254】语法拆解：`if` 要求条件 `args.infrastructure_retries < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.infrastructure_retries < 0` 是否成立；`infrastructure_retries` 表示本功能块中的 `infrastructure_retries` 值
    if args.infrastructure_retries < 0:
# 【L0255】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--infrastructure-retries must be non-negative")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--infrastructure-retries must be non-negative")` 并停止当前路径；说明当前输入违反“解析批量评测参数与互斥、范围和重复性门槛”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--infrastructure-retries must be non-negative")
# 【L0256】语法拆解：`if` 要求条件 `args.policy_max_action_chunks < 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.policy_max_action_chunks < 1` 是否成立；`policy_max_action_chunks` 表示策略、动作相关值
    if args.policy_max_action_chunks < 1:
# 【L0257】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--policy-max-action-chunks must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--policy-max-action-chunks must be positive")` 并停止当前路径；说明当前输入违反“解析批量评测参数与互斥、范围和重复性门槛”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--policy-max-action-chunks must be positive")
# 【L0258】语法拆解：`if` 要求条件 `not 0.0 < args.gripper_open_threshold < 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 < args.gripper_open_threshold < 1.0` 是否成立；`gripper_open_threshold` 表示夹爪相关值
    if not 0.0 < args.gripper_open_threshold < 1.0:
# 【L0259】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--gripper-open-threshold must be between 0 and 1")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--gripper-open-threshold must be between 0 and 1")` 并停止当前路径；说明当前输入违反“解析批量评测参数与互斥、范围和重复性门槛”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--gripper-open-threshold must be between 0 and 1")
# 【L0260】语法拆解：`if` 要求条件 `not args.gripper_open_threshold <= args.gripper_actual_open_threshold < 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.gripper_open_threshold <= args.gripper_actual_open_threshold < 1.0` 是否成立；`gripper_open_threshold` 表示夹爪相关值；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值
    if not args.gripper_open_threshold <= args.gripper_actual_open_threshold < 1.0:
# 【L0261】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(` 并停止当前路径；说明当前输入违反“解析批量评测参数与互斥、范围和重复性门槛”要求，不能继续进入仿真、训练或评测。
        raise ValueError(
# 【L0262】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--gripper-actual-open-threshold must be at least the target threshold and below 1"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析批量评测参数与互斥、范围和重复性门槛”中的帮助说明、错误原因、任务名称或报告文字。
            "--gripper-actual-open-threshold must be at least the target threshold and below 1"
# 【L0263】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析批量评测参数与互斥、范围和重复性门槛”。
        )
# 【L0264】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析批量评测参数与互斥、范围和重复性门槛”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“解析批量评测参数与互斥、范围和重复性门槛”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 7：载入 checkpoint/计划、准备环境并启动一次 policy server（源码第 265-336 行）

### 5.A 数据流位置

- 上游：模块 6“解析批量评测参数与互斥、范围和重复性门槛”。
- 本模块：载入 checkpoint/计划、准备环境并启动一次 policy server。
- 下游：处理结果继续交给模块 8“逐 case 运行、验证、复用报告并只重试基础设施故障”。

### 5.B 为什么需要这一组代码

这一组负责“载入 checkpoint/计划、准备环境并启动一次 policy server”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `checkpoint`：一次训练保存的模型参数目录。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。
- `policy_port`：OpenPI WebSocket policy server 监听的 TCP 端口。

### 5.D 本模块首次阅读要认识的调用

- `args.checkpoint.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `checkpoint.is_dir(...)`：圆括号表示真正执行调用；检查路径是否存在且确实是目录。
- `FileNotFoundError(...)`：圆括号表示真正执行调用；创建“需要的文件不存在”的异常。
- `args.plan.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `plan_path.read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `plan.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `validate_evaluation_cases(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `port_open(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。

### 5.F 这一模块的版本变化

- 当前第 270-270 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`if plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1":` 当前代码摘录：`if plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1":`
- 当前第 275-275 行相对旧教学快照发生 `replace`：旧版 5 行，当前 1 行。 旧代码摘录：`if not cases:` / `raise ValueError("evaluation plan has no cases")` / `case_ids = [case["case_id"] for case in cases]` / `if len(set(case_ids)) != len(case_ids):` 当前代码摘录：`validate_evaluation_cases(cases)`
- 当前第 298-304 行相对旧教学快照发生 `insert`：旧版 0 行，当前 7 行。 当前代码摘录：`environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"] = str(` / `args.gripper_actual_open_threshold` / `)` / `environment["POLICY_MAX_ACTION_CHUNKS"] = str(args.policy_max_action_chunks)`

### 5.G 逐行精读

```python
# 【L0265】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`args.checkpoint` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.checkpoint.expanduser().resolve()`；`checkpoint` 表示一次训练保存的模型参数目录；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0266】语法拆解：`if` 要求条件 `not checkpoint.is_dir()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not checkpoint.is_dir()` 是否成立；`checkpoint` 表示一次训练保存的模型参数目录；`is_dir` 表示本功能块中的 `is_dir` 值
    if not checkpoint.is_dir():
# 【L0267】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileNotFoundError(checkpoint)` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileNotFoundError(checkpoint)` 并停止当前路径；说明当前输入违反“载入 checkpoint/计划、准备环境并启动一次 policy server”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(checkpoint)
# 【L0268】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `plan_path`。右侧语法为：`args.plan` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `plan_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.plan.expanduser().resolve()`；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    plan_path = args.plan.expanduser().resolve()
# 【L0269】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `plan`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `plan_path.read_text(encoding="utf-8")`。
# 【项目含义】得到 `plan`，它在本项目中表示从 JSON 读取的专家采集计划或闭环评测计划；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
# 【L0270】语法拆解：`if` 要求条件 `plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1"` 是否成立；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1":
# 【L0271】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("unsupported evaluation plan format")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("unsupported evaluation plan format")` 并停止当前路径；说明当前输入违反“载入 checkpoint/计划、准备环境并启动一次 policy server”要求，不能继续进入仿真、训练或评测。
        raise ValueError("unsupported evaluation plan format")
# 【L0272】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`plan` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"cases"`；第 2 个实参 `[]`。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `plan.get("cases", [])`；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。
    cases = plan.get("cases", [])
# 【L0273】语法拆解：`if` 要求条件 `args.max_cases is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.max_cases is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.max_cases is not None:
# 【L0274】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`cases[: args.max_cases]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cases[: args.max_cases]`；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表；`max_cases` 表示本功能块中的 `max_cases` 值。
        cases = cases[: args.max_cases]
# 【L0275】语法拆解：`validate_evaluation_cases` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cases`。
# 【项目含义】调用函数 `validate_evaluation_cases`，传入 `cases`；函数名对应本功能块中的 `validate_evaluation_cases` 值。这一返回值或副作用被外层表达式用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
    validate_evaluation_cases(cases)
# 【L0276】语法拆解：`if` 要求条件 `port_open(args.policy_port)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `port_open(args.policy_port)` 是否成立；`port_open` 表示本功能块中的 `port_open` 值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口
    if port_open(args.policy_port):
# 【L0277】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"policy port {args.policy_port} is already in use")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"policy port {args.policy_port} is already in use")` 并停止当前路径；说明当前输入违反“载入 checkpoint/计划、准备环境并启动一次 policy server”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"policy port {args.policy_port} is already in use")
# 【L0278】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“载入 checkpoint/计划、准备环境并启动一次 policy server”中的逻辑段，让结构更容易看清。

# 【L0279】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_root`。右侧语法为：`args.output_root` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `output_root`，它在本项目中表示输出相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.output_root.expanduser().resolve()`；`output_root` 表示输出相关值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    output_root = args.output_root.expanduser().resolve()
# 【L0280】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary_path`。右侧语法为：`args.summary` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `summary_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.summary.expanduser().resolve()`；`summary` 表示本功能块中的 `summary` 值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    summary_path = args.summary.expanduser().resolve()
# 【L0281】语法拆解：`output_root` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output_root.mkdir(parents=True, exist_ok=True)`。`output_root` 表示输出相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
    output_root.mkdir(parents=True, exist_ok=True)
# 【L0282】语法拆解：`summary_path.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `summary_path.parent.mkdir(parents=True, exist_ok=True)`。`summary_path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
    summary_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0283】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `openpi_root`。右侧语法为：表达式 `Path.home() / "robot-learning" / "openpi"` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `openpi_root`，它在本项目中表示本功能块中的 `openpi_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path.home() / "robot-learning" / "openpi"`；`home` 表示本功能块中的 `home` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`learning` 表示本功能块中的 `learning` 值。
    openpi_root = Path.home() / "robot-learning" / "openpi"
# 【L0284】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint_id`。右侧语法为：`f"{checkpoint.parent.name}/{checkpoint.name}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】得到 `checkpoint_id`，它在本项目中表示模型检查点相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"{checkpoint.parent.name}/{checkpoint.name}"`；`f` 表示本功能块中的 `f` 值；`checkpoint` 表示一次训练保存的模型参数目录；`parent` 表示本功能块中的 `parent` 值。
    checkpoint_id = f"{checkpoint.parent.name}/{checkpoint.name}"
# 【L0285】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment`。右侧语法为：`os.environ` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `environment`，它在本项目中表示本功能块中的 `environment` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    environment = os.environ.copy()
# 【L0286】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["PYTHONPATH"]`。右侧语法为：`os.pathsep.join(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["PYTHONPATH"]`（写入 `environment["PYTHONPATH"]` 指定的字段）；右侧具体做的是：计算表达式 `os.pathsep.join(`；`os` 表示本功能块中的 `os` 值；`pathsep` 表示本功能块中的 `pathsep` 值；`join` 表示本功能块中的 `join` 值。
    environment["PYTHONPATH"] = os.pathsep.join(
# 【L0287】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“载入 checkpoint/计划、准备环境并启动一次 policy server”。
        [
# 【L0288】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT`。
# 【项目含义】调用 `str(PROJECT_ROOT)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            str(PROJECT_ROOT),
# 【L0289】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `openpi_root / "packages" / "openpi-client" / "src"`。
# 【项目含义】调用 `str(openpi_root / "packages" / "openpi-client" / "src")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            str(openpi_root / "packages" / "openpi-client" / "src"),
# 【L0290】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`environment` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PYTHONPATH"`；第 2 个实参 `""`。
# 【项目含义】对 `environment` 调用 `get("PYTHONPATH", "")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            environment.get("PYTHONPATH", ""),
# 【L0291】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
        ]
# 【L0292】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `rstrip(os.pathsep)`：调用 `)` 提供的 `rstrip` 操作。本行产生的修改/返回值服务于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
    ).rstrip(os.pathsep)
# 【L0293】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]`。右侧语法为：`environment.get(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]`（写入 `environment["XLA_PYTHON_CLIENT_MEM_FRACTION"]` 指定的字段）；右侧具体做的是：计算表达式 `environment.get(`；`environment` 表示本功能块中的 `environment` 值；`get` 表示本功能块中的 `get` 值。
    environment["XLA_PYTHON_CLIENT_MEM_FRACTION"] = environment.get(
# 【L0294】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
        "XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"
# 【L0295】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
    )
# 【L0296】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["RM65_REPO_ID"]`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】把右侧结果写进 `environment["RM65_REPO_ID"]`（写入 `environment["RM65_REPO_ID"]` 指定的字段）；右侧具体做的是：计算表达式 `args.repo_id`；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。
    environment["RM65_REPO_ID"] = args.repo_id
# 【L0297】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.gripper_open_threshold`。
# 【项目含义】把右侧结果写进 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]`（写入 `environment["POLICY_GRIPPER_OPEN_THRESHOLD"]` 指定的字段）；右侧具体做的是：计算表达式 `str(args.gripper_open_threshold)`；`gripper_open_threshold` 表示夹爪相关值。
    environment["POLICY_GRIPPER_OPEN_THRESHOLD"] = str(args.gripper_open_threshold)
# 【L0298】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"]`。右侧语法为：`str(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"]`（写入 `environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"]` 指定的字段）；右侧具体做的是：把表达式 `str(` 的结果保存下来，供当前功能块后续使用。
    environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"] = str(
# 【L0299】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_actual_open_threshold`。
# 【项目含义】把表达式/参数 `args.gripper_actual_open_threshold` 接入当前完整语句；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值。在“载入 checkpoint/计划、准备环境并启动一次 policy server”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        args.gripper_actual_open_threshold
# 【L0300】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
    )
# 【L0301】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["POLICY_MAX_ACTION_CHUNKS"]`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_max_action_chunks`。
# 【项目含义】把右侧结果写进 `environment["POLICY_MAX_ACTION_CHUNKS"]`（写入 `environment["POLICY_MAX_ACTION_CHUNKS"]` 指定的字段）；右侧具体做的是：计算表达式 `str(args.policy_max_action_chunks)`；`policy_max_action_chunks` 表示策略、动作相关值。
    environment["POLICY_MAX_ACTION_CHUNKS"] = str(args.policy_max_action_chunks)
# 【L0302】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `environment["RESET_RENDERER_ACCUMULATION_BEFORE_POLICY_OBSERVATION"]`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `environment["RESET_RENDERER_ACCUMULATION_BEFORE_POLICY_OBSERVATION"]`（写入 `environment["RESET_RENDERER_ACCUMULATION_BEFORE_POLICY_OBSERVATION"]` 指定的字段）；右侧具体做的是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    environment["RESET_RENDERER_ACCUMULATION_BEFORE_POLICY_OBSERVATION"] = (
# 【L0303】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"1" if args.reset_renderer_accumulation_before_policy_observation else "0"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
        "1" if args.reset_renderer_accumulation_before_policy_observation else "0"
# 【L0304】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
    )
# 【L0305】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_log_path`。右侧语法为：表达式 `PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `server_log_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"`；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`outputs` 表示本功能块中的 `outputs` 值；`rm65_pi05_policy_server_suite` 表示策略相关值。
    server_log_path = PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"
# 【L0306】语法拆解：`server_log_path.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `server_log_path.parent.mkdir(parents=True, exist_ok=True)`。`server_log_path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
    server_log_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0307】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `server_log_path.open("w", encoding="utf-8") as server_log`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with server_log_path.open("w", encoding="utf-8") as server_log:
# 【L0308】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server`。右侧语法为：`subprocess.Popen(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `server`，它在本项目中表示本功能块中的 `server` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `subprocess.Popen(`；`subprocess` 表示本功能块中的 `subprocess` 值；`Popen` 表示本功能块中的 `Popen` 值。
        server = subprocess.Popen(
# 【L0309】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            [
# 【L0310】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `openpi_root / ".venv" / "bin" / "python"`。
# 【项目含义】调用 `str(openpi_root / ".venv" / "bin" / "python")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                str(openpi_root / ".venv" / "bin" / "python"),
# 【L0311】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"-u"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
                "-u",
# 【L0312】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"`。
# 【项目含义】调用 `str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"),
# 【L0313】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--checkpoint"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
                "--checkpoint",
# 【L0314】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】调用 `str(checkpoint)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                str(checkpoint),
# 【L0315】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--repo-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
                "--repo-id",
# 【L0316】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.repo_id`；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，它参与“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                args.repo_id,
# 【L0317】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--port"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“载入 checkpoint/计划、准备环境并启动一次 policy server”中的帮助说明、错误原因、任务名称或报告文字。
                "--port",
# 【L0318】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_port`。
# 【项目含义】调用 `str(args.policy_port)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                str(args.policy_port),
# 【L0319】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            ],
# 【L0320】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cwd`。右侧语法为：`PROJECT_ROOT` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cwd` 传入 `PROJECT_ROOT`；该参数在本项目中表示本功能块中的 `cwd` 值，会参与“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            cwd=PROJECT_ROOT,
# 【L0321】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `env`。右侧语法为：`environment` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `env` 传入 `environment`；该参数在本项目中表示本功能块中的 `env` 值，会参与“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            env=environment,
# 【L0322】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stdout`。右侧语法为：`server_log` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stdout` 传入 `server_log`；该参数在本项目中表示本功能块中的 `stdout` 值，会参与“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            stdout=server_log,
# 【L0323】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stderr`。右侧语法为：`subprocess` 是起始对象；每个点号 `.` 依次读取属性/成员：`STDOUT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stderr` 传入 `subprocess.STDOUT`；该参数在本项目中表示本功能块中的 `stderr` 值，会参与“载入 checkpoint/计划、准备环境并启动一次 policy server”。
            stderr=subprocess.STDOUT,
# 【L0324】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
        )
# 【L0325】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“载入 checkpoint/计划、准备环境并启动一次 policy server”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
        try:
# 【L0326】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(180)`，每次把当前元素放进 `_`；这会逐个处理“载入 checkpoint/计划、准备环境并启动一次 policy server”所需的帧、episode、动作或实验 case。
            for _ in range(180):
# 【L0327】语法拆解：`if` 要求条件 `server.poll() is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `server.poll() is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                if server.poll() is not None:
# 【L0328】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“载入 checkpoint/计划、准备环境并启动一次 policy server”要求，不能继续进入仿真、训练或评测。
                    raise RuntimeError(
# 【L0329】语法拆解：`f"policy server stopped during startup; see {server_log_path}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"policy server stopped during startup; see {server_log_path}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`policy` 表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；`server` 表示本功能块中的 `server` 值。在“载入 checkpoint/计划、准备环境并启动一次 policy server”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        f"policy server stopped during startup; see {server_log_path}"
# 【L0330】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                    )
# 【L0331】语法拆解：`if` 要求条件 `port_open(args.policy_port)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `port_open(args.policy_port)` 是否成立；`port_open` 表示本功能块中的 `port_open` 值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口
                if port_open(args.policy_port):
# 【L0332】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“载入 checkpoint/计划、准备环境并启动一次 policy server”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                    break
# 【L0333】语法拆解：`time` 是模块/对象，点号 `.` 从中取出 `sleep` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `1`。
# 【项目含义】对 `time` 调用 `sleep(1)`：调用 `time` 提供的 `sleep` 操作。本行产生的修改/返回值服务于“载入 checkpoint/计划、准备环境并启动一次 policy server”。
                time.sleep(1)
# 【L0334】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“载入 checkpoint/计划、准备环境并启动一次 policy server”中处理剩余输入或备用路径。
            else:
# 【L0335】语法拆解：`raise` 主动制造并抛出异常；后面的 `TimeoutError("policy server did not listen within 180 seconds")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `TimeoutError("policy server did not listen within 180 seconds")` 并停止当前路径；说明当前输入违反“载入 checkpoint/计划、准备环境并启动一次 policy server”要求，不能继续进入仿真、训练或评测。
                raise TimeoutError("policy server did not listen within 180 seconds")
# 【L0336】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“载入 checkpoint/计划、准备环境并启动一次 policy server”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“载入 checkpoint/计划、准备环境并启动一次 policy server”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 8：逐 case 运行、验证、复用报告并只重试基础设施故障（源码第 337-453 行）

### 5.A 数据流位置

- 上游：模块 7“载入 checkpoint/计划、准备环境并启动一次 policy server”。
- 本模块：逐 case 运行、验证、复用报告并只重试基础设施故障。
- 下游：处理结果继续交给模块 9“无论任务结果如何都关闭 policy server”。

### 5.B 为什么需要这一组代码

这一组负责“逐 case 运行、验证、复用报告并只重试基础设施故障”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `checkpoint`：一次训练保存的模型参数目录。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `case_results`：每个评测 case 的退出码、日志和 task report 汇总。
- `policy_port`：OpenPI WebSocket policy server 监听的 TCP 端口。

### 5.D 本模块首次阅读要认识的调用

- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `load_existing_report(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `case_results.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `episode_dir.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `environment.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `case_log_path.open(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `subprocess.run(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `attempt_results.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `report.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。

### 5.F 这一模块的版本变化

- 当前第 340-341 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`case_seed = case["policy_noise_seed"]` / `simulation_seed = case["simulation_seed"]`
- 当前第 345-356 行相对旧教学快照发生 `replace`：旧版 1 行，当前 12 行。 旧代码摘录：`report_path, checkpoint_id, args.gripper_open_threshold` 当前代码摘录：`report_path,` / `checkpoint_id,` / `args.gripper_open_threshold,` / `args.gripper_actual_open_threshold,`
- 当前第 361-368 行相对旧教学快照发生 `replace`：旧版 1 行，当前 8 行。 旧代码摘录：`{"case_id": case_id, "runner_returncode": 0, "report": existing, "reused": True}` 当前代码摘录：`{` / `"case_id": case_id,` / `"policy_noise_seed": case_seed,` / `"simulation_seed": simulation_seed,`
- 当前第 384-385 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`str(case_seed),` / `str(simulation_seed),`
- 当前第 418-429 行相对旧教学快照发生 `replace`：旧版 1 行，当前 12 行。 旧代码摘录：`report_path, checkpoint_id, args.gripper_open_threshold` 当前代码摘录：`report_path,` / `checkpoint_id,` / `args.gripper_open_threshold,` / `args.gripper_actual_open_threshold,`
- 当前第 442-443 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`"policy_noise_seed": case_seed,` / `"simulation_seed": simulation_seed,`

### 5.G 逐行精读

```python
# 【L0337】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_results`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `case_results`，它在本项目中表示每个评测 case 的退出码、日志和 task report 汇总；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
            case_results = []
# 【L0338】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(cases, start=1)`，每次把当前元素放进 `position, case`；这会逐个处理“逐 case 运行、验证、复用报告并只重试基础设施故障”所需的帧、episode、动作或实验 case。
            for position, case in enumerate(cases, start=1):
# 【L0339】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_id`。右侧语法为：`case["case_id"]` 使用方括号索引；先计算 `"case_id"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】得到 `case_id`，它在本项目中表示本功能块中的 `case_id` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case["case_id"]`；`case` 表示本功能块中的 `case` 值；`case_id` 表示本功能块中的 `case_id` 值。
                case_id = case["case_id"]
# 【L0340】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_seed`。右侧语法为：`case["policy_noise_seed"]` 使用方括号索引；先计算 `"policy_noise_seed"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】得到 `case_seed`，它在本项目中表示本功能块中的 `case_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case["policy_noise_seed"]`；`case` 表示本功能块中的 `case` 值；`policy_noise_seed` 表示策略相关值。
                case_seed = case["policy_noise_seed"]
# 【L0341】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_seed`。右侧语法为：`case["simulation_seed"]` 使用方括号索引；先计算 `"simulation_seed"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】得到 `simulation_seed`，它在本项目中表示本功能块中的 `simulation_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case["simulation_seed"]`；`case` 表示本功能块中的 `case` 值；`simulation_seed` 表示本功能块中的 `simulation_seed` 值。
                simulation_seed = case["simulation_seed"]
# 【L0342】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_dir`。右侧语法为：表达式 `output_root / case_id` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `episode_dir`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `output_root / case_id`；`output_root` 表示输出相关值；`case_id` 表示本功能块中的 `case_id` 值。
                episode_dir = output_root / case_id
# 【L0343】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_path`。右侧语法为：表达式 `episode_dir / "task_report.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `report_path`，它在本项目中表示报告、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_dir / "task_report.json"`；`episode_dir` 表示一条轨迹相关值；`task_report` 表示报告相关值；`json` 表示本功能块中的 `json` 值。
                report_path = episode_dir / "task_report.json"
# 【L0344】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `existing`。右侧语法为：`load_existing_report(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `existing`，它在本项目中表示本功能块中的 `existing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `load_existing_report(`；`load_existing_report` 表示报告相关值。
                existing = load_existing_report(
# 【L0345】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`report_path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `report_path`；在本项目中它表示报告、路径相关值。
                    report_path,
# 【L0346】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`checkpoint_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `checkpoint_id`；在本项目中它表示模型检查点相关值。
                    checkpoint_id,
# 【L0347】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_open_threshold`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.gripper_open_threshold`；`gripper_open_threshold` 表示夹爪相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    args.gripper_open_threshold,
# 【L0348】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_actual_open_threshold`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.gripper_actual_open_threshold`；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    args.gripper_actual_open_threshold,
# 【L0349】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_max_action_chunks`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.policy_max_action_chunks`；`policy_max_action_chunks` 表示策略、动作相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    args.policy_max_action_chunks,
# 【L0350】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.reset_renderer_accumulation_before_policy_observation`；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    args.reset_renderer_accumulation_before_policy_observation,
# 【L0351】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `case_seed`；在本项目中它表示本功能块中的 `case_seed` 值。
                    case_seed,
# 【L0352】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`simulation_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `simulation_seed`；在本项目中它表示本功能块中的 `simulation_seed` 值。
                    simulation_seed,
# 【L0353】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    case["prompt"],
# 【L0354】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["transfer_joint_1_rad"]`；其中 `case["transfer_joint_1_rad"]` 的方括号表示先从 `case` 按键/索引 `"transfer_joint_1_rad"` 取值。
# 【项目含义】调用 `float(case["transfer_joint_1_rad"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    float(case["transfer_joint_1_rad"]),
# 【L0355】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_x_m"]`；其中 `case["source_offset_x_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_x_m"` 取值。
# 【项目含义】调用 `float(case["source_offset_x_m"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    float(case["source_offset_x_m"]),
# 【L0356】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_y_m"]`；其中 `case["source_offset_y_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_y_m"` 取值。
# 【项目含义】调用 `float(case["source_offset_y_m"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    float(case["source_offset_y_m"]),
# 【L0357】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                )
# 【L0358】语法拆解：`if` 要求条件 `existing is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `existing is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                if existing is not None:
# 【L0359】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、验证、复用报告并只重试基础设施故障”进度，也给日志留下可搜索证据。
                    print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True)
# 【L0360】语法拆解：`case_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `case_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    case_results.append(
# 【L0361】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        {
# 【L0362】语法拆解：这是字典键值对：`"case_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `case_id`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `case_id` 数据；字段值来自 `case_id`，因此保存/传递的是这个表达式当前计算出的结果。
                            "case_id": case_id,
# 【L0363】语法拆解：这是字典键值对：`"policy_noise_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `policy_noise_seed`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `policy_noise_seed` 数据；字段值来自 `case_seed`，因此保存/传递的是这个表达式当前计算出的结果。
                            "policy_noise_seed": case_seed,
# 【L0364】语法拆解：这是字典键值对：`"simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`simulation_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_seed`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `simulation_seed` 数据；字段值来自 `simulation_seed`，因此保存/传递的是这个表达式当前计算出的结果。
                            "simulation_seed": simulation_seed,
# 【L0365】语法拆解：这是字典键值对：`"runner_returncode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `runner_returncode`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `runner_returncode` 数据；字段值来自 `0`，因此保存/传递的是这个表达式当前计算出的结果。
                            "runner_returncode": 0,
# 【L0366】语法拆解：这是字典键值对：`"report"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`existing` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `report`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `report` 数据；字段值来自 `existing`，因此保存/传递的是这个表达式当前计算出的结果。
                            "report": existing,
# 【L0367】语法拆解：这是字典键值对：`"reused"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `reused`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `reused` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
                            "reused": True,
# 【L0368】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        }
# 【L0369】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    )
# 【L0370】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“逐 case 运行、验证、复用报告并只重试基础设施故障”中不满足继续条件。
                    continue
# 【L0371】语法拆解：`episode_dir` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `episode_dir.mkdir(parents=True, exist_ok=True)`。`episode_dir` 表示一条轨迹相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
                episode_dir.mkdir(parents=True, exist_ok=True)
# 【L0372】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment`。右侧语法为：`environment` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `case_environment`，它在本项目中表示本功能块中的 `case_environment` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
                case_environment = environment.copy()
# 【L0373】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment["POLICY_SERVER_MODE"]`。右侧语法为：`"external"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】把右侧结果写进 `case_environment["POLICY_SERVER_MODE"]`（写入 `case_environment["POLICY_SERVER_MODE"]` 指定的字段）；右侧具体做的是：计算表达式 `"external"`；`external` 表示外部相机相关值。
                case_environment["POLICY_SERVER_MODE"] = "external"
# 【L0374】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_environment["POLICY_PORT"]`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_port`。
# 【项目含义】把右侧结果写进 `case_environment["POLICY_PORT"]`（写入 `case_environment["POLICY_PORT"]` 指定的字段）；右侧具体做的是：计算表达式 `str(args.policy_port)`；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口。
                case_environment["POLICY_PORT"] = str(args.policy_port)
# 【L0375】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
                command = [
# 【L0376】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"bash"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行、验证、复用报告并只重试基础设施故障”中的帮助说明、错误原因、任务名称或报告文字。
                    "bash",
# 【L0377】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"`。
# 【项目含义】调用 `str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"),
# 【L0378】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】调用 `str(checkpoint)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(checkpoint),
# 【L0379】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_dir`。
# 【项目含义】调用 `str(episode_dir)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(episode_dir),
# 【L0380】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["transfer_joint_1_rad"]`；其中 `case["transfer_joint_1_rad"]` 的方括号表示先从 `case` 按键/索引 `"transfer_joint_1_rad"` 取值。
# 【项目含义】调用 `str(case["transfer_joint_1_rad"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(case["transfer_joint_1_rad"]),
# 【L0381】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_x_m"]`；其中 `case["source_offset_x_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_x_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_x_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(case["source_offset_x_m"]),
# 【L0382】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_y_m"]`；其中 `case["source_offset_y_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_y_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_y_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(case["source_offset_y_m"]),
# 【L0383】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    case["prompt"],
# 【L0384】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case_seed`。
# 【项目含义】调用 `str(case_seed)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(case_seed),
# 【L0385】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `simulation_seed`。
# 【项目含义】调用 `str(simulation_seed)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    str(simulation_seed),
# 【L0386】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                ]
# 【L0387】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"[{position}/{len(cases)}] {case_id}: run"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: run", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、验证、复用报告并只重试基础设施故障”进度，也给日志留下可搜索证据。
                print(f"[{position}/{len(cases)}] {case_id}: run", flush=True)
# 【L0388】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `attempt_results`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `attempt_results`，它在本项目中表示本功能块中的 `attempt_results` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
                attempt_results = []
# 【L0389】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
                report = None
# 【L0390】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(args.infrastructure_retries + 1)`，每次把当前元素放进 `attempt`；这会逐个处理“逐 case 运行、验证、复用报告并只重试基础设施故障”所需的帧、episode、动作或实验 case。
                for attempt in range(args.infrastructure_retries + 1):
# 【L0391】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `log_name`。右侧语法为：`"runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `log_name`，它在本项目中表示本功能块中的 `log_name` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"`；`runner` 表示本功能块中的 `runner` 值；`log` 表示本功能块中的 `log` 值；`attempt` 表示本功能块中的 `attempt` 值。
                    log_name = "runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"
# 【L0392】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `case_log_path`。右侧语法为：表达式 `episode_dir / log_name` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `case_log_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_dir / log_name`；`episode_dir` 表示一条轨迹相关值；`log_name` 表示本功能块中的 `log_name` 值。
                    case_log_path = episode_dir / log_name
# 【L0393】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `case_log_path.open("w", encoding="utf-8") as case_log`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
                    with case_log_path.open("w", encoding="utf-8") as case_log:
# 【L0394】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“逐 case 运行、验证、复用报告并只重试基础设施故障”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
                        try:
# 【L0395】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `completed`。右侧语法为：`subprocess.run(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `completed`，它在本项目中表示本功能块中的 `completed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `subprocess.run(`；`subprocess` 表示本功能块中的 `subprocess` 值；`run` 表示本功能块中的 `run` 值。
                            completed = subprocess.run(
# 【L0396】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `command`；在本项目中它表示控制命令相关值。
                                command,
# 【L0397】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cwd`。右侧语法为：`PROJECT_ROOT` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cwd` 传入 `PROJECT_ROOT`；该参数在本项目中表示本功能块中的 `cwd` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                cwd=PROJECT_ROOT,
# 【L0398】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `env`。右侧语法为：`case_environment` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `env` 传入 `case_environment`；该参数在本项目中表示本功能块中的 `env` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                env=case_environment,
# 【L0399】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stdout`。右侧语法为：`case_log` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stdout` 传入 `case_log`；该参数在本项目中表示本功能块中的 `stdout` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                stdout=case_log,
# 【L0400】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stderr`。右侧语法为：`subprocess` 是起始对象；每个点号 `.` 依次读取属性/成员：`STDOUT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stderr` 传入 `subprocess.STDOUT`；该参数在本项目中表示本功能块中的 `stderr` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                stderr=subprocess.STDOUT,
# 【L0401】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timeout`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`case_timeout_seconds`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `timeout` 传入 `args.case_timeout_seconds`；该参数在本项目中表示本功能块中的 `timeout` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                timeout=args.case_timeout_seconds,
# 【L0402】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `check`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `check` 传入 `False`；该参数在本项目中表示本功能块中的 `check` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                                check=False,
# 【L0403】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                            )
# 【L0404】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`code = completed.returncode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `returncode`，它在本项目中表示本功能块中的 `returncode` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `completed.returncode`；`completed` 表示本功能块中的 `completed` 值；`returncode` 表示本功能块中的 `returncode` 值。
                            returncode = completed.returncode
# 【L0405】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timed_out`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `timed_out`，它在本项目中表示本功能块中的 `timed_out` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
                            timed_out = False
# 【L0406】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `subprocess.TimeoutExpired`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
                        except subprocess.TimeoutExpired:
# 【L0407】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`code = 124` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `returncode`，它在本项目中表示本功能块中的 `returncode` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `124` 的结果保存下来，供当前功能块后续使用。
                            returncode = 124
# 【L0408】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timed_out`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `timed_out`，它在本项目中表示本功能块中的 `timed_out` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                            timed_out = True
# 【L0409】语法拆解：`attempt_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `attempt_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    attempt_results.append(
# 【L0410】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        {
# 【L0411】语法拆解：这是字典键值对：`"attempt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `attempt + 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `attempt`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `attempt` 数据；字段值来自 `attempt + 1`，因此保存/传递的是这个表达式当前计算出的结果。
                            "attempt": attempt + 1,
# 【L0412】语法拆解：这是字典键值对：`"runner_returncode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`returncode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `runner_returncode`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `runner_returncode` 数据；字段值来自 `returncode`，因此保存/传递的是这个表达式当前计算出的结果。
                            "runner_returncode": returncode,
# 【L0413】语法拆解：这是字典键值对：`"timed_out"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`timed_out` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `timed_out`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `timed_out` 数据；字段值来自 `timed_out`，因此保存/传递的是这个表达式当前计算出的结果。
                            "timed_out": timed_out,
# 【L0414】语法拆解：这是字典键值对：`"log"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case_log_path`。
# 【项目含义】定义字典/JSON 字段 `log`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `log` 数据；字段值来自 `str(case_log_path)`，因此保存/传递的是这个表达式当前计算出的结果。
                            "log": str(case_log_path),
# 【L0415】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        }
# 【L0416】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    )
# 【L0417】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`load_existing_report(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `load_existing_report(`；`load_existing_report` 表示报告相关值。
                    report = load_existing_report(
# 【L0418】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`report_path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `report_path`；在本项目中它表示报告、路径相关值。
                        report_path,
# 【L0419】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`checkpoint_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `checkpoint_id`；在本项目中它表示模型检查点相关值。
                        checkpoint_id,
# 【L0420】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_open_threshold`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.gripper_open_threshold`；`gripper_open_threshold` 表示夹爪相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        args.gripper_open_threshold,
# 【L0421】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_actual_open_threshold`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.gripper_actual_open_threshold`；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        args.gripper_actual_open_threshold,
# 【L0422】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_max_action_chunks`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.policy_max_action_chunks`；`policy_max_action_chunks` 表示策略、动作相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        args.policy_max_action_chunks,
# 【L0423】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.reset_renderer_accumulation_before_policy_observation`；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        args.reset_renderer_accumulation_before_policy_observation,
# 【L0424】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `case_seed`；在本项目中它表示本功能块中的 `case_seed` 值。
                        case_seed,
# 【L0425】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`simulation_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `simulation_seed`；在本项目中它表示本功能块中的 `simulation_seed` 值。
                        simulation_seed,
# 【L0426】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        case["prompt"],
# 【L0427】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["transfer_joint_1_rad"]`；其中 `case["transfer_joint_1_rad"]` 的方括号表示先从 `case` 按键/索引 `"transfer_joint_1_rad"` 取值。
# 【项目含义】调用 `float(case["transfer_joint_1_rad"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        float(case["transfer_joint_1_rad"]),
# 【L0428】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_x_m"]`；其中 `case["source_offset_x_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_x_m"` 取值。
# 【项目含义】调用 `float(case["source_offset_x_m"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        float(case["source_offset_x_m"]),
# 【L0429】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_y_m"]`；其中 `case["source_offset_y_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_y_m"` 取值。
# 【项目含义】调用 `float(case["source_offset_y_m"])`：把输入转换成浮点数，用作关节角、距离、阈值或统计量。它的结果/修改用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        float(case["source_offset_y_m"]),
# 【L0430】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    )
# 【L0431】语法拆解：`if` 要求条件 `report is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `report is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
                    if report is not None:
# 【L0432】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“逐 case 运行、验证、复用报告并只重试基础设施故障”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                        break
# 【L0433】语法拆解：`if` 要求条件 `attempt < args.infrastructure_retries` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `attempt < args.infrastructure_retries` 是否成立；`attempt` 表示本功能块中的 `attempt` 值；`infrastructure_retries` 表示本功能块中的 `infrastructure_retries` 值
                    if attempt < args.infrastructure_retries:
# 【L0434】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“逐 case 运行、验证、复用报告并只重试基础设施故障”进度，也给日志留下可搜索证据。
                        print(
# 【L0435】语法拆解：`f"[{position}/{len(cases)}] {case_id}: missing_report; "` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"[{position}/{len(cases)}] {case_id}: missing_report; "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`position` 表示位置相关值；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。在“逐 case 运行、验证、复用报告并只重试基础设施故障”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                            f"[{position}/{len(cases)}] {case_id}: missing_report; "
# 【L0436】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"retry infrastructure attempt {attempt + 2}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"retry infrastructure attempt {attempt + 2}"`；`f` 表示本功能块中的 `f` 值；`retry` 表示本功能块中的 `retry` 值；`infrastructure` 表示本功能块中的 `infrastructure` 值，它参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                            f"retry infrastructure attempt {attempt + 2}",
# 【L0437】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                            flush=True,
# 【L0438】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                        )
# 【L0439】语法拆解：`case_results.append(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `case_results` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                case_results.append(
# 【L0440】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    {
# 【L0441】语法拆解：这是字典键值对：`"case_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `case_id`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `case_id` 数据；字段值来自 `case_id`，因此保存/传递的是这个表达式当前计算出的结果。
                        "case_id": case_id,
# 【L0442】语法拆解：这是字典键值对：`"policy_noise_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `policy_noise_seed`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `policy_noise_seed` 数据；字段值来自 `case_seed`，因此保存/传递的是这个表达式当前计算出的结果。
                        "policy_noise_seed": case_seed,
# 【L0443】语法拆解：这是字典键值对：`"simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`simulation_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_seed`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `simulation_seed` 数据；字段值来自 `simulation_seed`，因此保存/传递的是这个表达式当前计算出的结果。
                        "simulation_seed": simulation_seed,
# 【L0444】语法拆解：这是字典键值对：`"runner_returncode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`returncode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `runner_returncode`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `runner_returncode` 数据；字段值来自 `returncode`，因此保存/传递的是这个表达式当前计算出的结果。
                        "runner_returncode": returncode,
# 【L0445】语法拆解：这是字典键值对：`"timed_out"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`timed_out` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `timed_out`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `timed_out` 数据；字段值来自 `timed_out`，因此保存/传递的是这个表达式当前计算出的结果。
                        "timed_out": timed_out,
# 【L0446】语法拆解：这是字典键值对：`"report"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`report` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `report`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `report` 数据；字段值来自 `report`，因此保存/传递的是这个表达式当前计算出的结果。
                        "report": report,
# 【L0447】语法拆解：这是字典键值对：`"reused"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `reused`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `reused` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                        "reused": False,
# 【L0448】语法拆解：这是字典键值对：`"log"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case_log_path`。
# 【项目含义】定义字典/JSON 字段 `log`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `log` 数据；字段值来自 `str(case_log_path)`，因此保存/传递的是这个表达式当前计算出的结果。
                        "log": str(case_log_path),
# 【L0449】语法拆解：这是字典键值对：`"infrastructure_attempts"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`attempt_results` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `infrastructure_attempts`，它表示“逐 case 运行、验证、复用报告并只重试基础设施故障”中的 `infrastructure_attempts` 数据；字段值来自 `attempt_results`，因此保存/传递的是这个表达式当前计算出的结果。
                        "infrastructure_attempts": attempt_results,
# 【L0450】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                    }
# 【L0451】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行、验证、复用报告并只重试基础设施故障”。
                )
# 【L0452】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `status`。右侧语法为：`report.get("status") if report else "missing_report"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `status`，它在本项目中表示本功能块中的 `status` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：本阶段的机器可读通过/失败状态。
                status = report.get("status") if report else "missing_report"
# 【L0453】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"[{position}/{len(cases)}] {case_id}: {status}"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"[{position}/{len(cases)}] {case_id}: {status}", flush=True` 的当前值/文字输出到终端；它用于观察“逐 case 运行、验证、复用报告并只重试基础设施故障”进度，也给日志留下可搜索证据。
                print(f"[{position}/{len(cases)}] {case_id}: {status}", flush=True)
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“逐 case 运行、验证、复用报告并只重试基础设施故障”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 9：无论任务结果如何都关闭 policy server（源码第 454-461 行）

### 5.A 数据流位置

- 上游：模块 8“逐 case 运行、验证、复用报告并只重试基础设施故障”。
- 本模块：无论任务结果如何都关闭 policy server。
- 下游：处理结果继续交给模块 10“汇总失败阶段、重复性和成功率，执行正式 suite gate”。

### 5.B 为什么需要这一组代码

这一组负责“无论任务结果如何都关闭 policy server”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.D 本模块首次阅读要认识的调用

- `server.terminate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `server.wait(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `server.kill(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0454】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
        finally:
# 【L0455】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `terminate` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `server` 调用 `terminate()`：调用 `server` 提供的 `terminate` 操作。本行产生的修改/返回值服务于“无论任务结果如何都关闭 policy server”。
            server.terminate()
# 【L0456】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“无论任务结果如何都关闭 policy server”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
            try:
# 【L0457】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `wait` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `timeout=20`。
# 【项目含义】对 `server` 调用 `wait(timeout=20)`：调用 `server` 提供的 `wait` 操作。本行产生的修改/返回值服务于“无论任务结果如何都关闭 policy server”。
                server.wait(timeout=20)
# 【L0458】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `subprocess.TimeoutExpired`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
            except subprocess.TimeoutExpired:
# 【L0459】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `kill` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `server` 调用 `kill()`：调用 `server` 提供的 `kill` 操作。本行产生的修改/返回值服务于“无论任务结果如何都关闭 policy server”。
                server.kill()
# 【L0460】语法拆解：`server` 是模块/对象，点号 `.` 从中取出 `wait` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `timeout=20`。
# 【项目含义】对 `server` 调用 `wait(timeout=20)`：调用 `server` 提供的 `wait` 操作。本行产生的修改/返回值服务于“无论任务结果如何都关闭 policy server”。
                server.wait(timeout=20)
# 【L0461】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“无论任务结果如何都关闭 policy server”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“无论任务结果如何都关闭 policy server”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 10：汇总失败阶段、重复性和成功率，执行正式 suite gate（源码第 462-515 行）

### 5.A 数据流位置

- 上游：模块 9“无论任务结果如何都关闭 policy server”。
- 本模块：汇总失败阶段、重复性和成功率，执行正式 suite gate。
- 下游：处理结果继续交给模块 11“脚本入口”。

### 5.B 为什么需要这一组代码

这一组负责“汇总失败阶段、重复性和成功率，执行正式 suite gate”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `checkpoint`：一次训练保存的模型参数目录。
- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `case_results`：每个评测 case 的退出码、日志和 task report 汇总。
- `success_rate`：有效闭环报告中 status=pass 的比例。
- `passed`：当前单条任务或整套评测是否满足所有硬性门槛。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `item.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `sum(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `report.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `plan.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `evaluate_suite_gate(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `gate_contract.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `summary_path.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `summary.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 465-474 行相对旧教学快照发生 `replace`：旧版 2 行，当前 10 行。 旧代码摘录：`success_rate = successes / episode_count if episode_count else 0.0` / `passed = episode_count >= 20 and success_rate >= 0.8` 当前代码摘录：`gate_contract = plan.get("gate", {})` / `gate = evaluate_suite_gate(` / `len(cases),` / `episode_count,`
- 当前第 485-503 行相对旧教学快照发生 `insert`：旧版 0 行，当前 19 行。 当前代码摘录：`"gripper_actual_open_threshold_normalized": (` / `args.gripper_actual_open_threshold` / `),` / `"policy_max_action_chunks": args.policy_max_action_chunks,`
- 当前第 508-508 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`"gate": {"minimum_episode_count": 20, "minimum_success_rate": 0.8},` 当前代码摘录：`"gate": gate,`

### 5.G 逐行精读

```python
# 【L0462】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `valid_reports`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `valid_reports`，它在本项目中表示本功能块中的 `valid_reports` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[item["report"] for item in case_results if item.get("report") is not None]`；`item` 表示本功能块中的 `item` 值；`report` 表示机器可读实验报告字典；`case_results` 表示每个评测 case 的退出码、日志和 task report 汇总。
    valid_reports = [item["report"] for item in case_results if item.get("report") is not None]
# 【L0463】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `successes`。右侧语法为：`sum` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `report.get("status") == "pass" for report in valid_reports`。
# 【项目含义】得到 `successes`，它在本项目中表示本功能块中的 `successes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：本阶段的机器可读通过/失败状态。
    successes = sum(report.get("status") == "pass" for report in valid_reports)
# 【L0464】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_count`。右侧语法为：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `valid_reports`。
# 【项目含义】得到 `episode_count`，它在本项目中表示一条轨迹、数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(valid_reports)`；`valid_reports` 表示本功能块中的 `valid_reports` 值。
    episode_count = len(valid_reports)
# 【L0465】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gate_contract`。右侧语法为：`plan` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"gate"`；第 2 个实参 `{}`。
# 【项目含义】得到 `gate_contract`，它在本项目中表示本功能块中的 `gate_contract` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `plan.get("gate", {})`；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`gate` 表示本功能块中的 `gate` 值。
    gate_contract = plan.get("gate", {})
# 【L0466】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gate`。右侧语法为：`evaluate_suite_gate(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `gate`，它在本项目中表示本功能块中的 `gate` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `evaluate_suite_gate(`；`evaluate_suite_gate` 表示本功能块中的 `evaluate_suite_gate` 值。
    gate = evaluate_suite_gate(
# 【L0467】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cases`。
# 【项目含义】调用函数 `len`，传入 `cases`；函数名对应本功能块中的 `len` 值。这一返回值或副作用被外层表达式用于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        len(cases),
# 【L0468】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_count` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_count`；在本项目中它表示一条轨迹、数量相关值。
        episode_count,
# 【L0469】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`successes` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `successes`；在本项目中它表示本功能块中的 `successes` 值。
        successes,
# 【L0470】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_episode_count`。右侧语法为：`gate_contract` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"minimum_episode_count"`；第 2 个实参 `20`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `minimum_episode_count` 传入 `gate_contract.get("minimum_episode_count", 20)`；该参数在本项目中表示一条轨迹、数量相关值，会参与“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        minimum_episode_count=gate_contract.get("minimum_episode_count", 20),
# 【L0471】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_success_rate`。右侧语法为：`gate_contract` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"minimum_success_rate"`；第 2 个实参 `0.8`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `minimum_success_rate` 传入 `gate_contract.get("minimum_success_rate", 0.8)`；该参数在本项目中表示成功相关值，会参与“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        minimum_success_rate=gate_contract.get("minimum_success_rate", 0.8),
# 【L0472】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
    )
# 【L0473】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `success_rate`。右侧语法为：`gate["success_rate"]` 使用方括号索引；先计算 `"success_rate"`，再从 `gate` 取对应字典字段或数组元素。
# 【项目含义】得到 `success_rate`，它在本项目中表示有效闭环报告中 status=pass 的比例；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `gate["success_rate"]`；`gate` 表示本功能块中的 `gate` 值；`success_rate` 表示有效闭环报告中 status=pass 的比例。
    success_rate = gate["success_rate"]
# 【L0474】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `passed`。右侧语法为：`gate["passed"]` 使用方括号索引；先计算 `"passed"`，再从 `gate` 取对应字典字段或数组元素。
# 【项目含义】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `gate["passed"]`；`gate` 表示本功能块中的 `gate` 值；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    passed = gate["passed"]
# 【L0475】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `summary`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `summary`，它在本项目中表示本功能块中的 `summary` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    summary = {
# 【L0476】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass" if passed else "fail"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L0477】语法拆解：这是字典键值对：`"evaluation_kind"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"isaaclab_pi0.5_closed_loop"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `evaluation_kind`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `evaluation_kind` 数据；字段值来自 `"isaaclab_pi0.5_closed_loop"`，因此保存/传递的是这个表达式当前计算出的结果。
        "evaluation_kind": "isaaclab_pi0.5_closed_loop",
# 【L0478】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0479】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0480】语法拆解：这是字典键值对：`"plan"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `plan_path`。
# 【项目含义】定义字典/JSON 字段 `plan`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `plan` 数据；字段值来自 `str(plan_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "plan": str(plan_path),
# 【L0481】语法拆解：这是字典键值对：`"checkpoint"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】定义字典/JSON 字段 `checkpoint`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0482】语法拆解：这是字典键值对：`"policy_checkpoint_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`checkpoint_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `checkpoint_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_checkpoint_id": checkpoint_id,
# 【L0483】语法拆解：这是字典键值对：`"repo_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】定义字典/JSON 字段 `repo_id`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0484】语法拆解：这是字典键值对：`"gripper_open_threshold_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_open_threshold`。
# 【项目含义】定义字典/JSON 字段 `gripper_open_threshold_normalized`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `gripper_open_threshold_normalized` 数据；字段值来自 `args.gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_open_threshold_normalized": args.gripper_open_threshold,
# 【L0485】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_actual_open_threshold_normalized`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `gripper_actual_open_threshold_normalized` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_actual_open_threshold_normalized": (
# 【L0486】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_actual_open_threshold`。
# 【项目含义】把表达式/参数 `args.gripper_actual_open_threshold` 接入当前完整语句；`gripper_actual_open_threshold` 表示夹爪、物理仿真实际值相关值。在“汇总失败阶段、重复性和成功率，执行正式 suite gate”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            args.gripper_actual_open_threshold
# 【L0487】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        ),
# 【L0488】语法拆解：这是字典键值对：`"policy_max_action_chunks"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_max_action_chunks`。
# 【项目含义】定义字典/JSON 字段 `policy_max_action_chunks`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `policy_max_action_chunks` 数据；字段值来自 `args.policy_max_action_chunks`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_max_action_chunks": args.policy_max_action_chunks,
# 【L0489】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `reset_renderer_accumulation_before_policy_observation`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `reset_renderer_accumulation_before_policy_observation` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "reset_renderer_accumulation_before_policy_observation": (
# 【L0490】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】把表达式/参数 `args.reset_renderer_accumulation_before_policy_observation` 接入当前完整语句；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值。在“汇总失败阶段、重复性和成功率，执行正式 suite gate”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            args.reset_renderer_accumulation_before_policy_observation
# 【L0491】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        ),
# 【L0492】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `diagnostic_only`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `diagnostic_only` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "diagnostic_only": (
# 【L0493】语法拆解：表达式 `args.policy_max_action_chunks != EVALUATION_POLICY_MAX_ACTION_CHUNKS` 使用运算符 `!=`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `args.policy_max_action_chunks != EVALUATION_POLICY_MAX_ACTION_CHUNKS` 接到上一行尚未结束的布尔表达式；`policy_max_action_chunks` 表示策略、动作相关值；`EVALUATION_POLICY_MAX_ACTION_CHUNKS` 表示策略、动作相关值。比较结果共同决定“汇总失败阶段、重复性和成功率，执行正式 suite gate”是否通过。
            args.policy_max_action_chunks != EVALUATION_POLICY_MAX_ACTION_CHUNKS
# 【L0494】语法拆解：`or args.reset_renderer_accumulation_before_policy_observation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `args.reset_renderer_accumulation_before_policy_observation` 用“或者”接到上一行判断中；判断 `args.reset_renderer_accumulation_before_policy_observation` 是否成立；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值。所有连接条件共同决定是否进入后续分支。
            or args.reset_renderer_accumulation_before_policy_observation
# 【L0495】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        ),
# 【L0496】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `deterministic_sampling`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `deterministic_sampling` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "deterministic_sampling": {
# 【L0497】语法拆解：这是字典键值对：`"mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"explicit_numpy_gaussian_noise_v1"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `mode`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `mode` 数据；字段值来自 `"explicit_numpy_gaussian_noise_v1"`，因此保存/传递的是这个表达式当前计算出的结果。
            "mode": "explicit_numpy_gaussian_noise_v1",
# 【L0498】语法拆解：这是字典键值对：`"case_seed_source"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"evaluation_plan"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `case_seed_source`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `case_seed_source` 数据；字段值来自 `"evaluation_plan"`，因此保存/传递的是这个表达式当前计算出的结果。
            "case_seed_source": "evaluation_plan",
# 【L0499】语法拆解：这是字典键值对：`"chunk_seed_rule"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"case_seed + chunk_index"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `chunk_seed_rule`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `chunk_seed_rule` 数据；字段值来自 `"case_seed + chunk_index"`，因此保存/传递的是这个表达式当前计算出的结果。
            "chunk_seed_rule": "case_seed + chunk_index",
# 【L0500】语法拆解：这是字典键值对：`"resume_requires_matching_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `resume_requires_matching_seed`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `resume_requires_matching_seed` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "resume_requires_matching_seed": True,
# 【L0501】语法拆解：这是字典键值对：`"simulation_seed_source"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"evaluation_plan"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `simulation_seed_source`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `simulation_seed_source` 数据；字段值来自 `"evaluation_plan"`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_seed_source": "evaluation_plan",
# 【L0502】语法拆解：这是字典键值对：`"resume_requires_matching_simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `resume_requires_matching_simulation_seed`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `resume_requires_matching_simulation_seed` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "resume_requires_matching_simulation_seed": True,
# 【L0503】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
        },
# 【L0504】语法拆解：这是字典键值对：`"planned_case_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cases`。
# 【项目含义】定义字典/JSON 字段 `planned_case_count`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `planned_case_count` 数据；字段值来自 `len(cases)`，因此保存/传递的是这个表达式当前计算出的结果。
        "planned_case_count": len(cases),
# 【L0505】语法拆解：这是字典键值对：`"episode_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_count` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `episode_count`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `episode_count` 数据；字段值来自 `episode_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode_count": episode_count,
# 【L0506】语法拆解：这是字典键值对：`"success_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`successes` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `success_count`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `success_count` 数据；字段值来自 `successes`，因此保存/传递的是这个表达式当前计算出的结果。
        "success_count": successes,
# 【L0507】语法拆解：这是字典键值对：`"success_rate"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`success_rate` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `success_rate`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `success_rate` 数据；字段值来自 `success_rate`，因此保存/传递的是这个表达式当前计算出的结果。
        "success_rate": success_rate,
# 【L0508】语法拆解：这是字典键值对：`"gate"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`gate` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gate`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `gate` 数据；字段值来自 `gate`，因此保存/传递的是这个表达式当前计算出的结果。
        "gate": gate,
# 【L0509】语法拆解：这是字典键值对：`"cases"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case_results` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `cases`，它表示“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的 `cases` 数据；字段值来自 `case_results`，因此保存/传递的是这个表达式当前计算出的结果。
        "cases": case_results,
# 【L0510】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
    }
# 【L0511】语法拆解：`summary_path` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(summary, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")`。`summary_path` 表示路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
# 【L0512】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2)`。
# 【项目含义】把 `json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2)` 的当前值/文字输出到终端；它用于观察“汇总失败阶段、重复性和成功率，执行正式 suite gate”进度，也给日志留下可搜索证据。
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
# 【L0513】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0 if passed else 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L0514】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的逻辑段，让结构更容易看清。

# 【L0515】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“汇总失败阶段、重复性和成功率，执行正式 suite gate”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“汇总失败阶段、重复性和成功率，执行正式 suite gate”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 11：脚本入口（源码第 516-517 行）

### 5.A 数据流位置

- 上游：模块 10“汇总失败阶段、重复性和成功率，执行正式 suite gate”。
- 本模块：脚本入口。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“脚本入口”。它服务于本文件要解决的总问题：长时间评测会被基础设施故障中断，简单重跑可能混用旧报告；单次成功不能证明鲁棒性。 这一组的处理结果会参与：预注册 case、校验 checkpoint/report 身份、只重试缺报告故障、保留失败来源并汇总未见条件表现。

### 5.D 本模块首次阅读要认识的调用

- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0516】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0517】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“脚本入口”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“脚本入口”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。