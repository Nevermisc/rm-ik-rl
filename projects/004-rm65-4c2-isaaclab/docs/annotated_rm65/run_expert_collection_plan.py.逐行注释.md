# `run_expert_collection_plan.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_expert_collection_plan.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`503180aebc738113da16391541c93f1da4fb2b4f30579464d264f30060b56361`
- 总行数：136

## 1. 先把这个程序放进整个项目

- 所处阶段：数据采集编排：按预注册计划可恢复地生成专家轨迹。
- 输入：采集计划、case/split 过滤、输出目录和专家脚本。
- 输出：完整 episode 集合、补充 metadata 和采集 summary。
- 一句话作用：按 45 条机器可读计划采集或恢复脚本专家数据；只复用经过完整验证且属于同一 case 的 episode。

### 为什么要写它

- 原先的问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。
- 采用的解决办法：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **argparse**：命令行参数解析：把 `--checkpoint` 等启动选项转换成 `args.checkpoint` 字段。
- **JSON**：JSON：只含通用键值、列表、数字和字符串的文本格式；用于计划、metadata 和报告证据。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-17` `82b3846f` **Add resumable RM65 expert collection plan**：把多条专家采集改成可恢复计划，避免中断后全部重跑。
- `2026-09-29` `a2167ed7` **Preregister RM65 v4 correction and confirmation**：预注册 v4 修正与确认数据，避免看过结果后随意改计划。

### 与上一版教学快照的源码差异

- 当前第 19-21 行相对旧教学快照发生 `replace`：旧版 1 行，当前 3 行。 旧代码摘录：`def completed_episode(directory: Path, case_id: str) -> bool:` 当前代码摘录：`def completed_episode(` / `directory: Path, case_id: str, expected_simulation_seed: int | None = None` / `) -> bool:`
- 当前第 33-37 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`and (` / `expected_simulation_seed is None` / `or metadata.get("metadata", {}).get("collection_simulation_seed")` / `== expected_simulation_seed`
- 当前第 41-58 行相对旧教学快照发生 `insert`：旧版 0 行，当前 18 行。 当前代码摘录：`def build_command(case: dict, directory: Path) -> list[str]:` / `command = [` / `"bash",` / `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),`
- 当前第 83-83 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`if completed_episode(directory, case["case_id"]):` 当前代码摘录：`if completed_episode(directory, case["case_id"], case.get("simulation_seed")):`
- 当前第 90-90 行相对旧教学快照发生 `replace`：旧版 9 行，当前 1 行。 旧代码摘录：`command = [` / `"bash",` / `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),` / `str(directory),` 当前代码摘录：`command = build_command(case, directory)`
- 当前第 94-112 行相对旧教学快照发生 `replace`：旧版 6 行，当前 19 行。 旧代码摘录：`manifest["metadata"].update(` / `{` / `"collection_case_id": case["case_id"],` / `"collection_split": case["split"],` 当前代码摘录：`collection_metadata = {` / `"collection_case_id": case["case_id"],` / `"collection_split": case["split"],` / `}`

## 4. 模块地图

- 模块 1｜第 1-18 行：依赖、项目路径和 episode validator
- 模块 2｜第 19-42 行：判断已有 episode 是否完整、成功且确实属于当前 case
- 模块 3｜第 43-60 行：把一个计划 case 转成 run_pick_place_baseline.py 命令
- 模块 4｜第 61-78 行：读取采集计划并按 split、case 数量和输出目录过滤
- 模块 5｜第 79-118 行：逐 case 运行脚本专家、补 metadata 并做采集后复核
- 模块 6｜第 119-136 行：输出采集、复用、失败统计和命令行退出码

### 函数/类快速索引

- `completed_episode()`：第 19-40 行
- `build_command()`：第 43-58 行
- `main()`：第 61-132 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、项目路径和 episode validator（源码第 1-18 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、项目路径和 episode validator。
- 下游：处理结果继续交给模块 2“判断已有 episode 是否完整、成功且确实属于当前 case”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、项目路径和 episode validator”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.C 本模块主要变量

- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `sys.path.insert(...)`：圆括号表示真正执行调用；把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run or resume a machine-readable scripted-expert collection plan on Linux.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run or resume a machine-readable scripted-expert collection plan on Linux."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】语法拆解：`import` 加载模块；`subprocess` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `subprocess` 引入 `subprocess`。在这份程序里，`subprocess` 用于启动和管理另一个系统进程；后续出现这些名字时调用的是这里的外部能力。
import subprocess
# 【L0009】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0012】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0013】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0014】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 episode validator”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：`from openpi_extension.expert_episode` 指定来源模块；`import validate_episode` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `validate_episode`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import validate_episode
# 【L0017】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

# 【L0018】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode validator”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、项目路径和 episode validator”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：判断已有 episode 是否完整、成功且确实属于当前 case（源码第 19-42 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、项目路径和 episode validator”。
- 本模块：判断已有 episode 是否完整、成功且确实属于当前 case。
- 下游：处理结果继续交给模块 3“把一个计划 case 转成 run_pick_place_baseline.py 命令”。

### 5.B 为什么需要这一组代码

这一组负责“判断已有 episode 是否完整、成功且确实属于当前 case”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.C 本模块主要变量

- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。

### 5.D 本模块首次阅读要认识的调用

- `completed_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `is_file(...)`：圆括号表示真正执行调用；检查路径是否存在且确实是普通文件。
- `validate_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `metadata.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `task.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。

### 5.E 本模块定义的新函数

### 函数卡：`completed_episode()`（第 19-40 行）

- 定义了什么：判断已有 episode 是否完整、成功且确实属于当前 case。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`directory`：类型 `Path`；项目含义是目录相关值；`case_id`：类型 `str`；项目含义是本功能块中的 `case_id` 值；`expected_simulation_seed`：类型 `int | None`，默认 `None`；项目含义是本功能块中的 `expected_simulation_seed` 值
- 返回类型标注：`bool`。
- 函数体实际 return：`bool(validation['status'] == 'pass' and metadata.get('metadata', {}).get('task_success') is True and (metadata.get('metadata', {}).get('collection_case_id') == case_id) and (expected_simulation_seed is None or metadata.get('metadata', {}).get('collection_simulation_seed') == expected_simulation_seed) and (task.get('status') == 'pass') and (task.get('unassisted_full_task_complete') is True))`；`False`
- 项目中的实际调用位置：`run_expert_collection_plan.py:83` 的 `if completed_episode(directory, case["case_id"], case.get("simulation_seed")):`；`run_expert_collection_plan.py:114` 的 `if not completed_episode(`


### 5.F 这一模块的版本变化

- 当前第 19-21 行相对旧教学快照发生 `replace`：旧版 1 行，当前 3 行。 旧代码摘录：`def completed_episode(directory: Path, case_id: str) -> bool:` 当前代码摘录：`def completed_episode(` / `directory: Path, case_id: str, expected_simulation_seed: int | None = None` / `) -> bool:`
- 当前第 33-37 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`and (` / `expected_simulation_seed is None` / `or metadata.get("metadata", {}).get("collection_simulation_seed")` / `== expected_simulation_seed`
- 当前第 41-58 行相对旧教学快照发生 `insert`：旧版 0 行，当前 18 行。 当前代码摘录：`def build_command(case: dict, directory: Path) -> list[str]:` / `command = [` / `"bash",` / `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),`

### 5.G 逐行精读

```python
# 【L0019】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `completed_episode(参数在后续行继续)`；调用者把参数交给它完成“判断已有 episode 是否完整、成功且确实属于当前 case”，后面的缩进代码是具体实现。
def completed_episode(
# 【L0020】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `directory: Path, case_id: str, expected_simulation_seed: int | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    directory: Path, case_id: str, expected_simulation_seed: int | None = None
# 【L0021】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> bool:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“判断已有 episode 是否完整、成功且确实属于当前 case”。
) -> bool:
# 【L0022】语法拆解：`if` 要求条件 `not (directory / "metadata.json").is_file() or not (` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not (directory / "metadata.json").is_file() or not (` 是否成立；`directory` 表示目录相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`json` 表示本功能块中的 `json` 值
    if not (directory / "metadata.json").is_file() or not (
# 【L0023】语法拆解：表达式 `directory / "task_report.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `directory / "task_report.json"` 接入当前完整语句；`directory` 表示目录相关值；`task_report` 表示报告相关值；`json` 表示本功能块中的 `json` 值。在“判断已有 episode 是否完整、成功且确实属于当前 case”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        directory / "task_report.json"
# 【L0024】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `).is_file():` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“判断已有 episode 是否完整、成功且确实属于当前 case”。
    ).is_file():
# 【L0025】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】结束当前函数并把 `False` 交回调用者；这个值的含义是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
        return False
# 【L0026】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `validation`。右侧语法为：`validate_episode` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `directory`；第 2 个实参 `require_images=True`。
# 【项目含义】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(directory, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`require_images` 表示本功能块中的 `require_images` 值。
    validation = validate_episode(directory, require_images=True)
# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(directory / "metadata.json").read_text(encoding="utf-8")`。
# 【项目含义】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0028】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `task`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(directory / "task_report.json").read_text(encoding="utf-8")`。
# 【项目含义】得到 `task`，它在本项目中表示本功能块中的 `task` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    task = json.loads((directory / "task_report.json").read_text(encoding="utf-8"))
# 【L0029】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `bool(` 交回调用者；这个值的含义是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    return bool(
# 【L0030】语法拆解：表达式 `validation["status"] == "pass"` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `validation["status"] == "pass"` 接到上一行尚未结束的布尔表达式；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值。比较结果共同决定“判断已有 episode 是否完整、成功且确实属于当前 case”是否通过。
        validation["status"] == "pass"
# 【L0031】语法拆解：`and metadata.get("metadata", {}).get("task_success") is True` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `metadata.get("metadata", {}).get("task_success") is True` 用“并且”接到上一行判断中；判断 `metadata.get("metadata", {}).get("task_success") is True` 是否成立；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`get` 表示本功能块中的 `get` 值；`task_success` 表示成功相关值。所有连接条件共同决定是否进入后续分支。
        and metadata.get("metadata", {}).get("task_success") is True
# 【L0032】语法拆解：表达式 `and metadata.get("metadata", {}).get("collection_case_id") == case_id` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `metadata.get("metadata", {}).get("collection_case_id") == case_id` 用“并且”接到上一行判断中；判断 `metadata.get("metadata", {}).get("collection_case_id") == case_id` 是否成立；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`get` 表示本功能块中的 `get` 值；`collection_case_id` 表示本功能块中的 `collection_case_id` 值。所有连接条件共同决定是否进入后续分支。
        and metadata.get("metadata", {}).get("collection_case_id") == case_id
# 【L0033】语法拆解：`and (` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `(` 用“并且”接到上一行判断中；判断 `(` 是否成立；成立时执行紧随其后的缩进代码。所有连接条件共同决定是否进入后续分支。
        and (
# 【L0034】语法拆解：`expected_simulation_seed is None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `expected_simulation_seed is None` 接入当前完整语句；`expected_simulation_seed` 表示本功能块中的 `expected_simulation_seed` 值。在“判断已有 episode 是否完整、成功且确实属于当前 case”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            expected_simulation_seed is None
# 【L0035】语法拆解：`or metadata.get("metadata", {}).get("collection_simulation_seed")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `or metadata` 调用 `get("metadata", {}).get("collection_simulation_seed")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“判断已有 episode 是否完整、成功且确实属于当前 case”。
            or metadata.get("metadata", {}).get("collection_simulation_seed")
# 【L0036】语法拆解：表达式 `== expected_simulation_seed` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `== expected_simulation_seed` 接入当前完整语句；`expected_simulation_seed` 表示本功能块中的 `expected_simulation_seed` 值。在“判断已有 episode 是否完整、成功且确实属于当前 case”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            == expected_simulation_seed
# 【L0037】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“判断已有 episode 是否完整、成功且确实属于当前 case”。
        )
# 【L0038】语法拆解：表达式 `and task.get("status") == "pass"` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `task.get("status") == "pass"` 用“并且”接到上一行判断中；判断 `task.get("status") == "pass"` 是否成立；`task` 表示本功能块中的 `task` 值；`get` 表示本功能块中的 `get` 值；`status` 表示本功能块中的 `status` 值。所有连接条件共同决定是否进入后续分支。
        and task.get("status") == "pass"
# 【L0039】语法拆解：`and task.get("unassisted_full_task_complete") is True` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `task.get("unassisted_full_task_complete") is True` 用“并且”接到上一行判断中；判断 `task.get("unassisted_full_task_complete") is True` 是否成立；`task` 表示本功能块中的 `task` 值；`get` 表示本功能块中的 `get` 值；`unassisted_full_task_complete` 表示本功能块中的 `unassisted_full_task_complete` 值。所有连接条件共同决定是否进入后续分支。
        and task.get("unassisted_full_task_complete") is True
# 【L0040】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“判断已有 episode 是否完整、成功且确实属于当前 case”。
    )
# 【L0041】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“判断已有 episode 是否完整、成功且确实属于当前 case”中的逻辑段，让结构更容易看清。

# 【L0042】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“判断已有 episode 是否完整、成功且确实属于当前 case”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“判断已有 episode 是否完整、成功且确实属于当前 case”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：把一个计划 case 转成 run_pick_place_baseline.py 命令（源码第 43-60 行）

### 5.A 数据流位置

- 上游：模块 2“判断已有 episode 是否完整、成功且确实属于当前 case”。
- 本模块：把一个计划 case 转成 run_pick_place_baseline.py 命令。
- 下游：处理结果继续交给模块 4“读取采集计划并按 split、case 数量和输出目录过滤”。

### 5.B 为什么需要这一组代码

这一组负责“把一个计划 case 转成 run_pick_place_baseline.py 命令”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.D 本模块首次阅读要认识的调用

- `build_command(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `case.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `isinstance(...)`：圆括号表示真正执行调用；判断一个对象是否属于指定类型；本项目常用它区分 bytes、字符串或数组。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `command.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。

### 5.E 本模块定义的新函数

### 函数卡：`build_command()`（第 43-58 行）

- 定义了什么：把一个计划 case 转成 run_pick_place_baseline.py 命令。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`case`：类型 `dict`；项目含义是本功能块中的 `case` 值；`directory`：类型 `Path`；项目含义是目录相关值
- 返回类型标注：`list[str]`。
- 函数体实际 return：`command`
- 项目中的实际调用位置：`run_expert_collection_plan.py:90` 的 `command = build_command(case, directory)`


### 5.F 这一模块的版本变化

- 当前第 41-58 行相对旧教学快照发生 `insert`：旧版 0 行，当前 18 行。 当前代码摘录：`def build_command(case: dict, directory: Path) -> list[str]:` / `command = [` / `"bash",` / `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),`

### 5.G 逐行精读

```python
# 【L0043】语法拆解：`def` 定义函数 `build_command`；第一对圆括号列出形参，逗号负责分隔：`case: dict` 用冒号给参数加类型提示；`directory: Path` 用冒号给参数加类型提示；`-> list[str]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `build_command(case: dict, directory: Path)`；调用者把参数交给它完成“把一个计划 case 转成 run_pick_place_baseline.py 命令”，后面的缩进代码是具体实现。
def build_command(case: dict, directory: Path) -> list[str]:
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
    command = [
# 【L0045】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"bash"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“把一个计划 case 转成 run_pick_place_baseline.py 命令”中的帮助说明、错误原因、任务名称或报告文字。
        "bash",
# 【L0046】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"`。
# 【项目含义】调用 `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh")`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),
# 【L0047】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `directory`。
# 【项目含义】调用 `str(directory)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        str(directory),
# 【L0048】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["transfer_joint_1_rad"]`；其中 `case["transfer_joint_1_rad"]` 的方括号表示先从 `case` 按键/索引 `"transfer_joint_1_rad"` 取值。
# 【项目含义】调用 `str(case["transfer_joint_1_rad"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        str(case["transfer_joint_1_rad"]),
# 【L0049】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_x_m"]`；其中 `case["source_offset_x_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_x_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_x_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        str(case["source_offset_x_m"]),
# 【L0050】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case["source_offset_y_m"]`；其中 `case["source_offset_y_m"]` 的方括号表示先从 `case` 按键/索引 `"source_offset_y_m"` 取值。
# 【项目含义】调用 `str(case["source_offset_y_m"])`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        str(case["source_offset_y_m"]),
# 【L0051】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `case["prompt"]`；`case` 表示本功能块中的 `case` 值；`prompt` 表示本功能块中的 `prompt` 值，它参与“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        case["prompt"],
# 【L0052】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
    ]
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_seed`。右侧语法为：`case` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"simulation_seed"`。
# 【项目含义】得到 `simulation_seed`，它在本项目中表示本功能块中的 `simulation_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case.get("simulation_seed")`；`case` 表示本功能块中的 `case` 值；`get` 表示本功能块中的 `get` 值；`simulation_seed` 表示本功能块中的 `simulation_seed` 值。
    simulation_seed = case.get("simulation_seed")
# 【L0054】语法拆解：`if` 要求条件 `simulation_seed is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `simulation_seed is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if simulation_seed is not None:
# 【L0055】语法拆解：`if` 要求条件 `not isinstance(simulation_seed, int) or simulation_seed < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not isinstance(simulation_seed, int) or simulation_seed < 0` 是否成立；`isinstance` 表示本功能块中的 `isinstance` 值；`simulation_seed` 表示本功能块中的 `simulation_seed` 值
        if not isinstance(simulation_seed, int) or simulation_seed < 0:
# 【L0056】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"invalid simulation_seed for {case.get('case_id')}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"invalid simulation_seed for {case.get('case_id')}")` 并停止当前路径；说明当前输入违反“把一个计划 case 转成 run_pick_place_baseline.py 命令”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"invalid simulation_seed for {case.get('case_id')}")
# 【L0057】语法拆解：`command` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `str(simulation_seed)`。
# 【项目含义】对 `command` 执行 `append`，把 `str(simulation_seed)` 加入已有结果；该集合表示控制命令相关值，随后会用于“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
        command.append(str(simulation_seed))
# 【L0058】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `command` 交回调用者；这个值的含义是：计算表达式 `command`；`command` 表示控制命令相关值。
    return command
# 【L0059】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把一个计划 case 转成 run_pick_place_baseline.py 命令”中的逻辑段，让结构更容易看清。

# 【L0060】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把一个计划 case 转成 run_pick_place_baseline.py 命令”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“把一个计划 case 转成 run_pick_place_baseline.py 命令”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：读取采集计划并按 split、case 数量和输出目录过滤（源码第 61-78 行）

### 5.A 数据流位置

- 上游：模块 3“把一个计划 case 转成 run_pick_place_baseline.py 命令”。
- 本模块：读取采集计划并按 split、case 数量和输出目录过滤。
- 下游：处理结果继续交给模块 5“逐 case 运行脚本专家、补 metadata 并做采集后复核”。

### 5.B 为什么需要这一组代码

这一组负责“读取采集计划并按 split、case 数量和输出目录过滤”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.C 本模块主要变量

- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `args.plan.read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `plan.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `args.dataset_root.mkdir(...)`：圆括号表示真正执行调用；创建目录。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 61-132 行）

- 定义了什么：读取采集计划并按 split、case 数量和输出目录过滤。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0061】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“读取采集计划并按 split、case 数量和输出目录过滤”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0063】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--plan"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--plan`；启动脚本可用它改变“读取采集计划并按 split、case 数量和输出目录过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--plan", type=Path, required=True)
# 【L0064】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--dataset-root"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--dataset-root`；启动脚本可用它改变“读取采集计划并按 split、case 数量和输出目录过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--dataset-root", type=Path, required=True)
# 【L0065】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--split"`；第 2 个实参 `choices=("train", "validation", "all")`；第 3 个实参 `default="all"`。
# 【项目含义】声明命令行参数 `--split`；启动脚本可用它改变“读取采集计划并按 split、case 数量和输出目录过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--split", choices=("train", "validation", "all"), default="all")
# 【L0066】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--max-cases"`；第 2 个实参 `type=int`。
# 【项目含义】声明命令行参数 `--max-cases`；启动脚本可用它改变“读取采集计划并按 split、case 数量和输出目录过滤”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--max-cases", type=int)
# 【L0067】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0068】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `plan`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.plan.read_text(encoding="utf-8")`。
# 【项目含义】得到 `plan`，它在本项目中表示从 JSON 读取的专家采集计划或闭环评测计划；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
# 【L0069】语法拆解：`if` 要求条件 `plan.get("format") != "rm65_expert_collection_plan_v1"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `plan.get("format") != "rm65_expert_collection_plan_v1"` 是否成立；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if plan.get("format") != "rm65_expert_collection_plan_v1":
# 【L0070】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("unsupported collection plan")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("unsupported collection plan")` 并停止当前路径；说明当前输入违反“读取采集计划并按 split、case 数量和输出目录过滤”要求，不能继续进入仿真、训练或评测。
        raise ValueError("unsupported collection plan")
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
    cases = [
# 【L0072】语法拆解：表达式 `item for item in plan["cases"] if args.split == "all" or item["split"] == args.split` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】这是生成式/推导式 `item for item in plan["cases"] if args.split == "all" or item["split"] == args.split`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`item` 表示本功能块中的 `item` 值；`plan` 表示从 JSON 读取的专家采集计划或闭环评测计划；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表。产生的序列交给外层列表、字典或函数完成“读取采集计划并按 split、case 数量和输出目录过滤”。
        item for item in plan["cases"] if args.split == "all" or item["split"] == args.split
# 【L0073】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“读取采集计划并按 split、case 数量和输出目录过滤”。
    ]
# 【L0074】语法拆解：`if` 要求条件 `args.max_cases is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.max_cases is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.max_cases is not None:
# 【L0075】语法拆解：`if` 要求条件 `args.max_cases <= 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.max_cases <= 0` 是否成立；`max_cases` 表示本功能块中的 `max_cases` 值
        if args.max_cases <= 0:
# 【L0076】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--max-cases must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--max-cases must be positive")` 并停止当前路径；说明当前输入违反“读取采集计划并按 split、case 数量和输出目录过滤”要求，不能继续进入仿真、训练或评测。
            raise ValueError("--max-cases must be positive")
# 【L0077】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cases`。右侧语法为：`cases[: args.max_cases]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】得到 `cases`，它在本项目中表示经过 split/max-cases 过滤后本次要运行的实验条件列表；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cases[: args.max_cases]`；`cases` 表示经过 split/max-cases 过滤后本次要运行的实验条件列表；`max_cases` 表示本功能块中的 `max_cases` 值。
        cases = cases[: args.max_cases]
# 【L0078】语法拆解：`args.dataset_root` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.dataset_root.mkdir(parents=True, exist_ok=True)`。`dataset_root` 表示数据集相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
    args.dataset_root.mkdir(parents=True, exist_ok=True)
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“读取采集计划并按 split、case 数量和输出目录过滤”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：逐 case 运行脚本专家、补 metadata 并做采集后复核（源码第 79-118 行）

### 5.A 数据流位置

- 上游：模块 4“读取采集计划并按 split、case 数量和输出目录过滤”。
- 本模块：逐 case 运行脚本专家、补 metadata 并做采集后复核。
- 下游：处理结果继续交给模块 6“输出采集、复用、失败统计和命令行退出码”。

### 5.B 为什么需要这一组代码

这一组负责“逐 case 运行脚本专家、补 metadata 并做采集后复核”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.C 本模块主要变量

- `manifest`：描述磁盘数据含义、数量和路径的元数据清单。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。

### 5.D 本模块首次阅读要认识的调用

- `completed_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `case.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `directory.exists(...)`：圆括号表示真正执行调用；检查文件或目录路径是否存在。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `build_command(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `subprocess.run(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `manifest_path.read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `update(...)`：圆括号表示真正执行调用；用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态。
- `manifest_path.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。

### 5.F 这一模块的版本变化

- 当前第 83-83 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`if completed_episode(directory, case["case_id"]):` 当前代码摘录：`if completed_episode(directory, case["case_id"], case.get("simulation_seed")):`
- 当前第 90-90 行相对旧教学快照发生 `replace`：旧版 9 行，当前 1 行。 旧代码摘录：`command = [` / `"bash",` / `str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),` / `str(directory),` 当前代码摘录：`command = build_command(case, directory)`
- 当前第 94-112 行相对旧教学快照发生 `replace`：旧版 6 行，当前 19 行。 旧代码摘录：`manifest["metadata"].update(` / `{` / `"collection_case_id": case["case_id"],` / `"collection_split": case["split"],` 当前代码摘录：`collection_metadata = {` / `"collection_case_id": case["case_id"],` / `"collection_split": case["split"],` / `}`
- 当前第 114-116 行相对旧教学快照发生 `replace`：旧版 1 行，当前 3 行。 旧代码摘录：`if not completed_episode(directory, case["case_id"]):` 当前代码摘录：`if not completed_episode(` / `directory, case["case_id"], case.get("simulation_seed")` / `):`

### 5.G 逐行精读

```python
# 【L0079】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `completed`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `completed`，它在本项目中表示本功能块中的 `completed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    completed = 0
# 【L0080】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `skipped`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `skipped`，它在本项目中表示本功能块中的 `skipped` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    skipped = 0
# 【L0081】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `cases`，每次把当前元素放进 `case`；这会逐个处理“逐 case 运行脚本专家、补 metadata 并做采集后复核”所需的帧、episode、动作或实验 case。
    for case in cases:
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `directory`。右侧语法为：表达式 `args.dataset_root / f"episode_{case['episode_index']:06d}"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.dataset_root / f"episode_{case['episode_index']:06d}"`；`dataset_root` 表示数据集相关值；`f` 表示本功能块中的 `f` 值；`episode_` 表示一条轨迹相关值。
        directory = args.dataset_root / f"episode_{case['episode_index']:06d}"
# 【L0083】语法拆解：`if` 要求条件 `completed_episode(directory, case["case_id"], case.get("simulation_seed"))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `completed_episode(directory, case["case_id"], case.get("simulation_seed"))` 是否成立；`completed_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`case` 表示本功能块中的 `case` 值
        if completed_episode(directory, case["case_id"], case.get("simulation_seed")):
# 【L0084】语法拆解：表达式 `skipped += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `skipped + 1` 更新 `skipped` 原值；`skipped` 表示本功能块中的 `skipped` 值，常用于累计步数、距离、损失或成功次数。
            skipped += 1
# 【L0085】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“逐 case 运行脚本专家、补 metadata 并做采集后复核”中不满足继续条件。
            continue
# 【L0086】语法拆解：`if` 要求条件 `directory.exists()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `directory.exists()` 是否成立；`directory` 表示目录相关值；`exists` 表示本功能块中的 `exists` 值
        if directory.exists():
# 【L0087】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“逐 case 运行脚本专家、补 metadata 并做采集后复核”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L0088】语法拆解：`f"existing episode is incomplete or belongs to another case: {directory}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"existing episode is incomplete or belongs to another case: {directory}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`existing` 表示本功能块中的 `existing` 值；`episode` 表示一条轨迹相关值。在“逐 case 运行脚本专家、补 metadata 并做采集后复核”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"existing episode is incomplete or belongs to another case: {directory}"
# 【L0089】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
            )
# 【L0090】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：`build_command` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `case`；第 2 个实参 `directory`。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `build_command(case, directory)`；`build_command` 表示控制命令相关值；`case` 表示本功能块中的 `case` 值；`directory` 表示目录相关值。
        command = build_command(case, directory)
# 【L0091】语法拆解：`subprocess` 是模块/对象，点号 `.` 从中取出 `run` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `command`；第 2 个实参 `cwd=PROJECT_ROOT`；第 3 个实参 `check=True`。
# 【项目含义】对 `subprocess` 调用 `run(command, cwd=PROJECT_ROOT, check=True)`：调用 `subprocess` 提供的 `run` 操作。本行产生的修改/返回值服务于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest_path`。右侧语法为：表达式 `directory / "metadata.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `manifest_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `directory / "metadata.json"`；`directory` 表示目录相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`json` 表示本功能块中的 `json` 值。
        manifest_path = directory / "metadata.json"
# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `manifest_path.read_text(encoding="utf-8")`。
# 【项目含义】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
# 【L0094】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collection_metadata`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `collection_metadata`，它在本项目中表示元数据相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        collection_metadata = {
# 【L0095】语法拆解：这是字典键值对：`"collection_case_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case["case_id"]` 使用方括号索引；先计算 `"case_id"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `collection_case_id`，它表示“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的 `collection_case_id` 数据；字段值来自 `case["case_id"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "collection_case_id": case["case_id"],
# 【L0096】语法拆解：这是字典键值对：`"collection_split"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`case["split"]` 使用方括号索引；先计算 `"split"`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `collection_split`，它表示“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的 `collection_split` 数据；字段值来自 `case["split"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "collection_split": case["split"],
# 【L0097】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        }
# 【L0098】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for key in (` 中给出的序列，逐项完成“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        for key in (
# 【L0099】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"simulation_seed"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "simulation_seed",
# 【L0100】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"physical_group_id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "physical_group_id",
# 【L0101】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"physical_variant"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "physical_variant",
# 【L0102】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"render_repeat_index"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "render_repeat_index",
# 【L0103】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"render_repeat_count"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "render_repeat_count",
# 【L0104】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"source_evaluation_case_id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "source_evaluation_case_id",
# 【L0105】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"source_outcome_pattern"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
            "source_outcome_pattern",
# 【L0106】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        ):
# 【L0107】语法拆解：`if` 要求条件 `key in case` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `key in case` 是否成立；`key` 表示本功能块中的 `key` 值；`case` 表示本功能块中的 `case` 值
            if key in case:
# 【L0108】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata_key`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `metadata_key`，它在本项目中表示元数据相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
                metadata_key = (
# 【L0109】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"collection_simulation_seed" if key == "simulation_seed" else key`；Python 会把相邻字符串自动拼接，外层参数会把它用作“逐 case 运行脚本专家、补 metadata 并做采集后复核”中的帮助说明、错误原因、任务名称或报告文字。
                    "collection_simulation_seed" if key == "simulation_seed" else key
# 【L0110】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
                )
# 【L0111】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collection_metadata[metadata_key]`。右侧语法为：`case[key]` 使用方括号索引；先计算 `key`，再从 `case` 取对应字典字段或数组元素。
# 【项目含义】把右侧结果写进 `collection_metadata[metadata_key]`（写入 `collection_metadata[metadata_key]` 指定的字段）；右侧具体做的是：计算表达式 `case[key]`；`case` 表示本功能块中的 `case` 值；`key` 表示本功能块中的 `key` 值。
                collection_metadata[metadata_key] = case[key]
# 【L0112】语法拆解：`manifest["metadata"].update(collection_metadata)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `manifest["metadata"]` 调用 `update(collection_metadata)`：用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态。本行产生的修改/返回值服务于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        manifest["metadata"].update(collection_metadata)
# 【L0113】语法拆解：`manifest_path` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(manifest, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")`。`manifest_path` 表示路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
# 【L0114】语法拆解：`if` 要求条件 `not completed_episode(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not completed_episode(` 是否成立；`completed_episode` 表示一条轨迹相关值
        if not completed_episode(
# 【L0115】语法拆解：`directory, case["case_id"], case.get("simulation_seed")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `directory, case["case_id"], case` 调用 `get("simulation_seed")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
            directory, case["case_id"], case.get("simulation_seed")
# 【L0116】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
        ):
# 【L0117】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"recorded episode failed post-run validation: {directory}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"recorded episode failed post-run validation: {directory}")` 并停止当前路径；说明当前输入违反“逐 case 运行脚本专家、补 metadata 并做采集后复核”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed post-run validation: {directory}")
# 【L0118】语法拆解：表达式 `completed += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `completed + 1` 更新 `completed` 原值；`completed` 表示本功能块中的 `completed` 值，常用于累计步数、距离、损失或成功次数。
        completed += 1
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“逐 case 运行脚本专家、补 metadata 并做采集后复核”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 6：输出采集、复用、失败统计和命令行退出码（源码第 119-136 行）

### 5.A 数据流位置

- 上游：模块 5“逐 case 运行脚本专家、补 metadata 并做采集后复核”。
- 本模块：输出采集、复用、失败统计和命令行退出码。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“输出采集、复用、失败统计和命令行退出码”。它服务于本文件要解决的总问题：手工逐条运行容易漏 case、重复覆盖或把失败轨迹混进训练集。 这一组的处理结果会参与：为每个 case 建独立目录，检查已有完成状态，只补缺失轨迹并做采集后复核。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `plan`：从 JSON 读取的专家采集计划或闭环评测计划。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。

### 5.D 本模块首次阅读要认识的调用

- `args.plan.resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `args.dataset_root.resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0119】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0120】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0121】语法拆解：这是字典键值对：`"plan"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.plan.resolve()`。
# 【项目含义】定义字典/JSON 字段 `plan`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `plan` 数据；字段值来自 `str(args.plan.resolve())`，因此保存/传递的是这个表达式当前计算出的结果。
        "plan": str(args.plan.resolve()),
# 【L0122】语法拆解：这是字典键值对：`"dataset_root"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.dataset_root.resolve()`。
# 【项目含义】定义字典/JSON 字段 `dataset_root`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `dataset_root` 数据；字段值来自 `str(args.dataset_root.resolve())`，因此保存/传递的是这个表达式当前计算出的结果。
        "dataset_root": str(args.dataset_root.resolve()),
# 【L0123】语法拆解：这是字典键值对：`"requested_case_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cases`。
# 【项目含义】定义字典/JSON 字段 `requested_case_count`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `requested_case_count` 数据；字段值来自 `len(cases)`，因此保存/传递的是这个表达式当前计算出的结果。
        "requested_case_count": len(cases),
# 【L0124】语法拆解：这是字典键值对：`"newly_completed_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`completed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `newly_completed_count`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `newly_completed_count` 数据；字段值来自 `completed`，因此保存/传递的是这个表达式当前计算出的结果。
        "newly_completed_count": completed,
# 【L0125】语法拆解：这是字典键值对：`"already_completed_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`skipped` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `already_completed_count`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `already_completed_count` 数据；字段值来自 `skipped`，因此保存/传递的是这个表达式当前计算出的结果。
        "already_completed_count": skipped,
# 【L0126】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0127】语法拆解：这是字典键值对：`"expert"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"scripted"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `expert`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `expert` 数据；字段值来自 `"scripted"`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": "scripted",
# 【L0128】语法拆解：这是字典键值对：`"pi05_used"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `pi05_used`，它表示“输出采集、复用、失败统计和命令行退出码”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": False,
# 【L0129】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0130】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“输出采集、复用、失败统计和命令行退出码”。
    }
# 【L0131】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2)`。
# 【项目含义】把 `json.dumps(report, indent=2)` 的当前值/文字输出到终端；它用于观察“输出采集、复用、失败统计和命令行退出码”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2))
# 【L0132】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0133】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“输出采集、复用、失败统计和命令行退出码”中的逻辑段，让结构更容易看清。

# 【L0134】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“输出采集、复用、失败统计和命令行退出码”中的逻辑段，让结构更容易看清。

# 【L0135】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0136】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“输出采集、复用、失败统计和命令行退出码”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“输出采集、复用、失败统计和命令行退出码”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。