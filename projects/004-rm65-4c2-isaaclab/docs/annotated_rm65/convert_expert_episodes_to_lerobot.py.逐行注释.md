# `convert_expert_episodes_to_lerobot.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/convert_expert_episodes_to_lerobot.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`e9fbfe6e748fa7526e6f7c99f294c3dc9450068323eeded0ae7385a7e205ac1d`
- 总行数：313

## 1. 先把这个程序放进整个项目

- 所处阶段：训练数据准备：把自定义专家 episode 转成 OpenPI 可读的 LeRobot 数据集。
- 输入：通过验证的专家 NPZ、PNG、metadata 和 split/窗口选择参数。
- 输出：带 feature schema、task 文本和 frame/episode 索引的 LeRobotDataset。
- 一句话作用：把便于调试的本地 episode 格式转换成 OpenPI 能训练的 LeRobot 数据集。

### 为什么要写它

- 原先的问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。
- 采用的解决办法：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

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

- `2026-09-17` `c6a87c23` **Add RM65 expert episode data pipeline**：建立同步记录、保存和验证专家 episode 的数据合同。
- `2026-09-17` `82b3846f` **Add resumable RM65 expert collection plan**：把多条专家采集改成可恢复计划，避免中断后全部重跑。
- `2026-09-19` `1b21e1d1` **Add optional RM65 policy-window dataset**：增加只选择策略有效窗口的数据版本，减少长静止段。
- `2026-09-28` `a2f7ace3` **Prepare RM65 pi0.5 failure-correction v3**：根据闭环失败准备 v3 修正数据与训练配置。
- `2026-09-28` `67d26c20` **Audit RM65 v3 training data provenance**：增加 v3 训练数据来源审计，防止数据集和 checkpoint 对不上。

### 与上一版教学快照的源码差异

- 当前第 138-183 行相对旧教学快照发生 `insert`：旧版 0 行，当前 46 行。 当前代码摘录：`def discover_dataset_roots(` / `dataset_roots: list[Path], *, collection_split: str | None = None` / `) -> list[dict[str, Any]]:` / `"""Load one logical dataset from independent, immutable episode roots."""`
- 当前第 186-191 行相对旧教学快照发生 `replace`：旧版 1 行，当前 6 行。 旧代码摘录：`parser.add_argument("dataset_root", type=Path)` 当前代码摘录：`parser.add_argument(` / `"dataset_roots",` / `type=Path,` / `nargs="+",`
- 当前第 194-194 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`parser.add_argument("--report", type=Path)`
- 当前第 210-212 行相对旧教学快照发生 `replace`：旧版 2 行，当前 3 行。 旧代码摘录：`episodes = discover_episodes(` / `args.dataset_root.expanduser().resolve(), collection_split=args.split` 当前代码摘录：`dataset_roots = [path.expanduser().resolve() for path in args.dataset_roots]` / `episodes = discover_dataset_roots(` / `dataset_roots, collection_split=args.split`
- 当前第 287-308 行相对旧教学快照发生 `replace`：旧版 17 行，当前 22 行。 旧代码摘录：`print(` / `json.dumps(` / `{` / `"status": "pass",` 当前代码摘录：`report = {` / `"status": "pass",` / `"repo_id": args.repo_id,` / `"dataset_roots": [str(path) for path in dataset_roots],`

## 4. 模块地图

- 模块 1｜第 1-22 行：依赖、项目路径和 episode 校验器
- 模块 2｜第 23-49 行：读取且只接收成功、图像完整的 episode
- 模块 3｜第 50-93 行：选择有效策略窗口，减少大量静止标签
- 模块 4｜第 94-98 行：读取并统一 RGB PNG
- 模块 5｜第 99-137 行：发现 episode 并检查帧率、状态/动作维度和相机尺寸一致
- 模块 6｜第 138-183 行：发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并
- 模块 7｜第 184-234 行：解析命令行、选择 split、数据源和 LeRobot 输出目录
- 模块 8｜第 235-259 行：声明 LeRobot 图像、状态、动作、任务和索引 schema
- 模块 9｜第 260-286 行：逐 episode、逐帧写入 LeRobot 数据集
- 模块 10｜第 287-313 行：保存数据集并输出转换数量、来源和跳过原因

### 函数/类快速索引

- `load_episode()`：第 23-47 行
- `select_policy_window_indices()`：第 50-91 行
- `read_rgb()`：第 94-96 行
- `discover_episodes()`：第 99-135 行
- `discover_dataset_roots()`：第 138-181 行
- `main()`：第 184-309 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、项目路径和 episode 校验器（源码第 1-22 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、项目路径和 episode 校验器。
- 下游：处理结果继续交给模块 2“读取且只接收成功、图像完整的 episode”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、项目路径和 episode 校验器”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

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
# 【项目含义】说明字符串 `Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】语法拆解：`import` 加载模块；`shutil` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `shutil` 引入 `shutil`。在这份程序里，`shutil` 用于标准库文件目录操作；后续出现这些名字时调用的是这里的外部能力。
import shutil
# 【L0009】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】语法拆解：`from typing` 指定来源模块；`import Any` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0014】语法拆解：`from PIL` 指定来源模块；`import Image` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
from PIL import Image
# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 episode 校验器”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0020】语法拆解：`from openpi_extension.expert_episode` 指定来源模块；`import validate_episode` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `validate_episode`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import validate_episode
# 【L0021】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

# 【L0022】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 episode 校验器”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、项目路径和 episode 校验器”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：读取且只接收成功、图像完整的 episode（源码第 23-49 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、项目路径和 episode 校验器”。
- 本模块：读取且只接收成功、图像完整的 episode。
- 下游：处理结果继续交给模块 3“选择有效策略窗口，减少大量静止标签”。

### 5.B 为什么需要这一组代码

这一组负责“读取且只接收成功、图像完整的 episode”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `manifest`：描述磁盘数据含义、数量和路径的元数据清单。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。
- `phase_ids`：每一帧所处专家阶段的整数编号。
- `phase_names`：阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。

### 5.D 本模块首次阅读要认识的调用

- `load_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `validate_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `manifest.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `np.load(...)`：圆括号表示真正执行调用；从 NPZ/NPY 文件读取 NumPy 数据。
- `astype(...)`：圆括号表示真正执行调用；把 NumPy 数组元素转换到指定 dtype，例如把像素转成 uint8。

### 5.E 本模块定义的新函数

### 函数卡：`load_episode()`（第 23-47 行）

- 定义了什么：读取且只接收成功、图像完整的 episode。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`directory`：类型 `Path`；项目含义是目录相关值
- 返回类型标注：`dict[str, Any]`。
- 函数体实际 return：`{'directory': directory, 'prompt': manifest['prompt'], 'fps': float(manifest['control_hz']), 'states': states, 'actions': actions, 'phase_ids': phase_ids, 'phase_names': manifest['phase_names'], 'external_paths': manifest['image_paths']['external'], 'wrist_paths': manifest['image_paths']['wrist'], 'collection_split': manifest.get('metadata', {}).get('collection_split')}`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:107` 的 `episodes = [load_episode(directory) for directory in directories]`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0023】语法拆解：`def` 定义函数 `load_episode`；第一对圆括号列出形参，逗号负责分隔：`directory: Path` 用冒号给参数加类型提示；`-> dict[str, Any]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `load_episode(directory: Path)`；调用者把参数交给它完成“读取且只接收成功、图像完整的 episode”，后面的缩进代码是具体实现。
def load_episode(directory: Path) -> dict[str, Any]:
# 【L0024】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Load and validate one successful episode without requiring LeRobot.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Load and validate one successful episode without requiring LeRobot."""
# 【L0025】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“读取且只接收成功、图像完整的 episode”中的逻辑段，让结构更容易看清。

# 【L0026】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `validation`。右侧语法为：`validate_episode` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `directory`；第 2 个实参 `require_images=True`。
# 【项目含义】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(directory, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`require_images` 表示本功能块中的 `require_images` 值。
    validation = validate_episode(directory, require_images=True)
# 【L0027】语法拆解：`if` 要求条件 `validation["status"] != "pass"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `validation["status"] != "pass"` 是否成立；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
    if validation["status"] != "pass":
# 【L0028】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"invalid episode {directory}: {validation['errors']}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"invalid episode {directory}: {validation['errors']}")` 并停止当前路径；说明当前输入违反“读取且只接收成功、图像完整的 episode”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"invalid episode {directory}: {validation['errors']}")
# 【L0029】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(directory / "metadata.json").read_text(encoding="utf-8")`。
# 【项目含义】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0030】语法拆解：`if` 要求条件 `manifest.get("metadata", {}).get("task_success") is not True` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `manifest.get("metadata", {}).get("task_success") is not True` 是否成立；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息
    if manifest.get("metadata", {}).get("task_success") is not True:
# 【L0031】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"episode is not marked successful: {directory}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"episode is not marked successful: {directory}")` 并停止当前路径；说明当前输入违反“读取且只接收成功、图像完整的 episode”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episode is not marked successful: {directory}")
# 【L0032】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `np.load(directory / "episode.npz") as arrays`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with np.load(directory / "episode.npz") as arrays:
# 【L0033】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `states`。右侧语法为：`arrays["observation_state"].astype(np.float32, copy=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `states`，它在本项目中表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["observation_state"].astype(np.float32, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`observation_state` 表示状态相关值；`astype` 表示本功能块中的 `astype` 值。
        states = arrays["observation_state"].astype(np.float32, copy=True)
# 【L0034】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actions`。右侧语法为：`arrays["action"].astype(np.float32, copy=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actions`，它在本项目中表示一个动作块；形状通常为 (时间步数, 7)；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["action"].astype(np.float32, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`action` 表示动作相关值；`astype` 表示本功能块中的 `astype` 值。
        actions = arrays["action"].astype(np.float32, copy=True)
# 【L0035】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_ids`。右侧语法为：`arrays["phase_id"].astype(np.int64, copy=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["phase_id"].astype(np.int64, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`phase_id` 表示本功能块中的 `phase_id` 值；`astype` 表示本功能块中的 `astype` 值。
        phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
# 【L0036】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0037】语法拆解：这是字典键值对：`"directory"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`directory` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `directory`，它表示“读取且只接收成功、图像完整的 episode”中的 `directory` 数据；字段值来自 `directory`，因此保存/传递的是这个表达式当前计算出的结果。
        "directory": directory,
# 【L0038】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `manifest["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": manifest["prompt"],
# 【L0039】语法拆解：这是字典键值对：`"fps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `manifest["control_hz"]`；其中 `manifest["control_hz"]` 的方括号表示先从 `manifest` 按键/索引 `"control_hz"` 取值。
# 【项目含义】定义字典/JSON 字段 `fps`，它表示“读取且只接收成功、图像完整的 episode”中的 `fps` 数据；字段值来自 `float(manifest["control_hz"])`，因此保存/传递的是这个表达式当前计算出的结果。
        "fps": float(manifest["control_hz"]),
# 【L0040】语法拆解：这是字典键值对：`"states"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`states` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `states`，它表示“读取且只接收成功、图像完整的 episode”中的 `states` 数据；字段值来自 `states`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": states,
# 【L0041】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actions` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `actions`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": actions,
# 【L0042】语法拆解：这是字典键值对：`"phase_ids"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`phase_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `phase_ids`，它表示“读取且只接收成功、图像完整的 episode”中的 `phase_ids` 数据；字段值来自 `phase_ids`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": phase_ids,
# 【L0043】语法拆解：这是字典键值对：`"phase_names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest["phase_names"]` 使用方括号索引；先计算 `"phase_names"`，再从 `manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `phase_names`，它表示“读取且只接收成功、图像完整的 episode”中的 `phase_names` 数据；字段值来自 `manifest["phase_names"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_names": manifest["phase_names"],
# 【L0044】语法拆解：这是字典键值对：`"external_paths"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest["image_paths"]["external"]` 使用方括号索引；先计算 `"image_paths"]["external"`，再从 `manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `external_paths`，它表示“读取且只接收成功、图像完整的 episode”中的 `external_paths` 数据；字段值来自 `manifest["image_paths"]["external"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "external_paths": manifest["image_paths"]["external"],
# 【L0045】语法拆解：这是字典键值对：`"wrist_paths"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest["image_paths"]["wrist"]` 使用方括号索引；先计算 `"image_paths"]["wrist"`，再从 `manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `wrist_paths`，它表示“读取且只接收成功、图像完整的 episode”中的 `wrist_paths` 数据；字段值来自 `manifest["image_paths"]["wrist"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "wrist_paths": manifest["image_paths"]["wrist"],
# 【L0046】语法拆解：这是字典键值对：`"collection_split"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"metadata"`；第 2 个实参 `{}).get("collection_split"`。
# 【项目含义】定义字典/JSON 字段 `collection_split`，它表示“读取且只接收成功、图像完整的 episode”中的 `collection_split` 数据；字段值来自 `manifest.get("metadata", {}).get("collection_split")`，因此保存/传递的是这个表达式当前计算出的结果。
        "collection_split": manifest.get("metadata", {}).get("collection_split"),
# 【L0047】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“读取且只接收成功、图像完整的 episode”。
    }
# 【L0048】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“读取且只接收成功、图像完整的 episode”中的逻辑段，让结构更容易看清。

# 【L0049】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“读取且只接收成功、图像完整的 episode”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“读取且只接收成功、图像完整的 episode”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：选择有效策略窗口，减少大量静止标签（源码第 50-93 行）

### 5.A 数据流位置

- 上游：模块 2“读取且只接收成功、图像完整的 episode”。
- 本模块：选择有效策略窗口，减少大量静止标签。
- 下游：处理结果继续交给模块 4“读取并统一 RGB PNG”。

### 5.B 为什么需要这一组代码

这一组负责“选择有效策略窗口，减少大量静止标签”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `phase_ids`：每一帧所处专家阶段的整数编号。
- `phase_names`：阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
- `indices`：当前 episode 中会被写入目标数据集的帧索引。

### 5.D 本模块首次阅读要认识的调用

- `select_policy_window_indices(...)`：圆括号表示真正执行调用；按阶段和运动变化挑选训练帧，减少长时间静止 hold 对数据分布的占比。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `phase.startswith(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `set(...)`：圆括号表示真正执行调用；修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。
- `np.flatnonzero(...)`：圆括号表示真正执行调用；返回布尔条件为真的扁平索引。
- `tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `selected.update(...)`：圆括号表示真正执行调用；用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态。
- `sorted(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。

### 5.E 本模块定义的新函数

### 函数卡：`select_policy_window_indices()`（第 50-91 行）

- 定义了什么：选择有效策略窗口，减少大量静止标签。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`episode`：类型 `dict[str, Any]`；项目含义是一条轨迹相关值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`result`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:266` 的 `select_policy_window_indices(episode)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0050】语法拆解：`def` 定义函数 `select_policy_window_indices`；第一对圆括号列出形参，逗号负责分隔：`episode: dict[str, Any]` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `select_policy_window_indices(episode: dict[str, Any])`；调用者把参数交给它完成“选择有效策略窗口，减少大量静止标签”，后面的缩进代码是具体实现。
def select_policy_window_indices(episode: dict[str, Any]) -> np.ndarray:
# 【L0051】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Keep control-relevant motion while reducing ambiguous stationary labels.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Keep control-relevant motion while reducing ambiguous stationary labels.
# 【L0052】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0053】语法拆解：`The full portable episode remains unchanged. This optional view retains the` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `The full portable episode remains unchanged. This optional view retains the`；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    The full portable episode remains unchanged. This optional view retains the
# 【L0054】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `last two frames of pre-transition holds, the first 15 release-settle frames` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `last two frames of pre-transition holds, the first 15 release-settle frames,`；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    last two frames of pre-transition holds, the first 15 release-settle frames,
# 【L0055】语法拆解：表达式 `and every motion frame through release. Retreat and final-settle frames are` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `and every motion frame through release. Retreat and final-settle frames are`；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    and every motion frame through release. Retreat and final-settle frames are
# 【L0056】语法拆解：表达式 `omitted because the closed-loop success detector stops after stable release.` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `omitted because the closed-loop success detector stops after stable release.`；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    omitted because the closed-loop success detector stops after stable release.
# 【L0057】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“选择有效策略窗口，减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0058】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择有效策略窗口，减少大量静止标签”中的逻辑段，让结构更容易看清。

# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_ids`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode["phase_ids"]`；第 2 个实参 `dtype=np.int64`；其中 `episode["phase_ids"]` 的方括号表示先从 `episode` 按键/索引 `"phase_ids"` 取值。
# 【项目含义】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `episode["phase_ids"], dtype=np.int64`（一条轨迹相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_names`。右侧语法为：`episode["phase_names"]` 使用方括号索引；先计算 `"phase_names"`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode["phase_names"]`；`episode` 表示一条轨迹相关值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
    phase_names = episode["phase_names"]
# 【L0061】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phases`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[phase_names[int(index)] for index in phase_ids]`；第 2 个实参 `dtype=object`。
# 【项目含义】得到 `phases`，它在本项目中表示本功能块中的 `phases` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `[phase_names[int(index)] for index in phase_ids], dtype=object`（本功能块中的 `` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    phases = np.asarray([phase_names[int(index)] for index in phase_ids], dtype=object)
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `motion_mask`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `motion_mask`，它在本项目中表示掩码相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    motion_mask = np.array(
# 【L0063】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“选择有效策略窗口，减少大量静止标签”。
        [
# 【L0064】语法拆解：`phase` 是模块/对象，点号 `.` 从中取出 `startswith` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"APPROACH_"`。
# 【项目含义】对 `phase` 调用 `startswith("APPROACH_")`：调用 `phase` 提供的 `startswith` 操作。本行产生的修改/返回值服务于“选择有效策略窗口，减少大量静止标签”。
            phase.startswith("APPROACH_")
# 【L0065】语法拆解：`or phase.startswith("PLACE_DESCENT_")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `or phase` 调用 `startswith("PLACE_DESCENT_")`：调用 `or phase` 提供的 `startswith` 操作。本行产生的修改/返回值服务于“选择有效策略窗口，减少大量静止标签”。
            or phase.startswith("PLACE_DESCENT_")
# 【L0066】语法拆解：`or phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}` 用“或者”接到上一行判断中；判断 `phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}` 是否成立；`phase` 表示本功能块中的 `phase` 值；`CLOSE` 表示本功能块中的 `CLOSE` 值；`LIFT` 表示本功能块中的 `LIFT` 值。所有连接条件共同决定是否进入后续分支。
            or phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}
# 【L0067】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for phase in phases` 中给出的序列，逐项完成“选择有效策略窗口，减少大量静止标签”。
            for phase in phases
# 【L0068】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择有效策略窗口，减少大量静止标签”。
        ],
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`bool` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `bool`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“选择有效策略窗口，减少大量静止标签”。
        dtype=bool,
# 【L0070】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择有效策略窗口，减少大量静止标签”。
    )
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `selected`。右侧语法为：`set` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.flatnonzero(motion_mask).tolist()`。
# 【项目含义】得到 `selected`，它在本项目中表示本功能块中的 `selected` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `set(np.flatnonzero(motion_mask).tolist())`；`set` 表示本功能块中的 `set` 值；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`motion_mask` 表示掩码相关值。
    selected = set(np.flatnonzero(motion_mask).tolist())
# 【L0072】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for phase in (` 中给出的序列，逐项完成“选择有效策略窗口，减少大量静止标签”。
    for phase in (
# 【L0073】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"SOURCE_SETTLE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "SOURCE_SETTLE",
# 【L0074】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"GRASP_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "GRASP_HOLD",
# 【L0075】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"CLOSE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "CLOSE_HOLD",
# 【L0076】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"LIFT_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "LIFT_HOLD",
# 【L0077】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"TARGET_COLLISION_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "TARGET_COLLISION_HOLD",
# 【L0078】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"PLACE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择有效策略窗口，减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "PLACE_HOLD",
# 【L0079】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择有效策略窗口，减少大量静止标签”。
    ):
# 【L0080】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `indices`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `flatnonzero` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `phases == phase`。
# 【项目含义】得到 `indices`，它在本项目中表示当前 episode 中会被写入目标数据集的帧索引；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.flatnonzero(phases == phase)`；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`phases` 表示本功能块中的 `phases` 值；`phase` 表示本功能块中的 `phase` 值。
        indices = np.flatnonzero(phases == phase)
# 【L0081】语法拆解：`selected` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `indices[-2:].tolist()`。
# 【项目含义】对 `selected` 执行 `update`，把 `indices[-2:].tolist()` 加入已有结果；该集合表示本功能块中的 `selected` 值，随后会用于“选择有效策略窗口，减少大量静止标签”。
        selected.update(indices[-2:].tolist())
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_indices`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `flatnonzero` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `phases == "RELEASE_SETTLE"`。
# 【项目含义】得到 `release_indices`，它在本项目中表示本功能块中的 `release_indices` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.flatnonzero(phases == "RELEASE_SETTLE")`；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`phases` 表示本功能块中的 `phases` 值；`RELEASE_SETTLE` 表示本功能块中的 `RELEASE_SETTLE` 值。
    release_indices = np.flatnonzero(phases == "RELEASE_SETTLE")
# 【L0083】语法拆解：`selected` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `release_indices[:15].tolist()`。
# 【项目含义】对 `selected` 执行 `update`，把 `release_indices[:15].tolist()` 加入已有结果；该集合表示本功能块中的 `selected` 值，随后会用于“选择有效策略窗口，减少大量静止标签”。
    selected.update(release_indices[:15].tolist())
# 【L0084】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sorted(selected)`；第 2 个实参 `dtype=np.int64`。
# 【项目含义】得到 `result`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `sorted(selected), dtype=np.int64`（本功能块中的 `sorted(selected), dtype=np.int64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    result = np.asarray(sorted(selected), dtype=np.int64)
# 【L0085】语法拆解：`if` 要求条件 `len(result) == 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(result) == 0` 是否成立；`result` 表示结果相关值
    if len(result) == 0:
# 【L0086】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"episode contains no recognized policy phases: {episode['directory']}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"episode contains no recognized policy phases: {episode['directory']}")` 并停止当前路径；说明当前输入违反“选择有效策略窗口，减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episode contains no recognized policy phases: {episode['directory']}")
# 【L0087】语法拆解：`if` 要求条件 `phases[result[0]] != "SOURCE_SETTLE"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `phases[result[0]] != "SOURCE_SETTLE"` 是否成立；`phases` 表示本功能块中的 `phases` 值；`result` 表示结果相关值；`SOURCE_SETTLE` 表示源位置方块/平台的任务常量
    if phases[result[0]] != "SOURCE_SETTLE":
# 【L0088】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("policy window must begin with a SOURCE_SETTLE transition frame")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("policy window must begin with a SOURCE_SETTLE transition frame")` 并停止当前路径；说明当前输入违反“选择有效策略窗口，减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy window must begin with a SOURCE_SETTLE transition frame")
# 【L0089】语法拆解：`if` 要求条件 `"OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `"OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]` 是否成立；`OPEN` 表示本功能块中的 `OPEN` 值；`phases` 表示本功能块中的 `phases` 值；`result` 表示结果相关值
    if "OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]:
# 【L0090】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("policy window must contain OPEN and RELEASE_SETTLE")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("policy window must contain OPEN and RELEASE_SETTLE")` 并停止当前路径；说明当前输入违反“选择有效策略窗口，减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy window must contain OPEN and RELEASE_SETTLE")
# 【L0091】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`result` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `result` 交回调用者；这个值的含义是：计算表达式 `result`；`result` 表示结果相关值。
    return result
# 【L0092】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择有效策略窗口，减少大量静止标签”中的逻辑段，让结构更容易看清。

# 【L0093】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择有效策略窗口，减少大量静止标签”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“选择有效策略窗口，减少大量静止标签”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：读取并统一 RGB PNG（源码第 94-98 行）

### 5.A 数据流位置

- 上游：模块 3“选择有效策略窗口，减少大量静止标签”。
- 本模块：读取并统一 RGB PNG。
- 下游：处理结果继续交给模块 5“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。

### 5.B 为什么需要这一组代码

这一组负责“读取并统一 RGB PNG”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.D 本模块首次阅读要认识的调用

- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `Image.open(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `image.convert(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`read_rgb()`（第 94-96 行）

- 定义了什么：读取并统一 RGB PNG。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`path`：类型 `Path`；项目含义是路径相关值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`np.asarray(image.convert('RGB'), dtype=np.uint8)`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:122` 的 `first_external = read_rgb(first["directory"] / first["external_paths"][0])`；`convert_expert_episodes_to_lerobot.py:123` 的 `first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])`；`convert_expert_episodes_to_lerobot.py:163` 的 `expected_external_shape = read_rgb(`；`convert_expert_episodes_to_lerobot.py:166` 的 `expected_wrist_shape = read_rgb(`；`convert_expert_episodes_to_lerobot.py:236` 的 `external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0094】语法拆解：`def` 定义函数 `read_rgb`；第一对圆括号列出形参，逗号负责分隔：`path: Path` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `read_rgb(path: Path)`；调用者把参数交给它完成“读取并统一 RGB PNG”，后面的缩进代码是具体实现。
def read_rgb(path: Path) -> np.ndarray:
# 【L0095】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `Image.open(path) as image`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with Image.open(path) as image:
# 【L0096】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image.convert("RGB")`；第 2 个实参 `dtype=np.uint8`。
# 【项目含义】结束当前函数并把 `np.asarray(image.convert("RGB"), dtype=np.uint8)` 交回调用者；这个值的含义是：读取/计算 `image.convert("RGB"), dtype=np.uint8`（本功能块中的 `image.convert("RGB"), dtype=np.uint8` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
# 【L0097】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“读取并统一 RGB PNG”中的逻辑段，让结构更容易看清。

# 【L0098】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“读取并统一 RGB PNG”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“读取并统一 RGB PNG”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：发现 episode 并检查帧率、状态/动作维度和相机尺寸一致（源码第 99-137 行）

### 5.A 数据流位置

- 上游：模块 4“读取并统一 RGB PNG”。
- 本模块：发现 episode 并检查帧率、状态/动作维度和相机尺寸一致。
- 下游：处理结果继续交给模块 6“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。

### 5.B 为什么需要这一组代码

这一组负责“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。

### 5.D 本模块首次阅读要认识的调用

- `discover_episodes(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `sorted(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `dataset_root.glob(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `FileNotFoundError(...)`：圆括号表示真正执行调用；创建“需要的文件不存在”的异常。
- `load_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `round(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.E 本模块定义的新函数

### 函数卡：`discover_episodes()`（第 99-135 行）

- 定义了什么：发现 episode 并检查帧率、状态/动作维度和相机尺寸一致。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`dataset_root`：类型 `Path`；项目含义是数据集相关值；`collection_split`（仅关键字）：类型 `str | None`，默认 `None`；项目含义是本功能块中的 `collection_split` 值
- 返回类型标注：`list[dict[str, Any]]`。
- 函数体实际 return：`episodes`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:149` 的 `for episode in discover_episodes(root, collection_split=collection_split):`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0099】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `discover_episodes(参数在后续行继续)`；调用者把参数交给它完成“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”，后面的缩进代码是具体实现。
def discover_episodes(
# 【L0100】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset_root: Path, *, collection_split: str | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `dataset_root`，它在本项目中表示数据集相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    dataset_root: Path, *, collection_split: str | None = None
# 【L0101】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> list[dict[str, Any]]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
) -> list[dict[str, Any]]:
# 【L0102】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `directories`。右侧语法为：`sorted(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `directories`，它在本项目中表示本功能块中的 `directories` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sorted(`；`sorted` 表示本功能块中的 `sorted` 值。
    directories = sorted(
# 【L0103】语法拆解：表达式 `path.parent for path in dataset_root.glob("episode_*/metadata.json")` 使用运算符 `*`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】对 `path.parent for path in dataset_root` 调用 `glob("episode_*/metadata.json")`：调用 `path.parent for path in dataset_root` 提供的 `glob` 操作。本行产生的修改/返回值服务于“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
        path.parent for path in dataset_root.glob("episode_*/metadata.json")
# 【L0104】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
    )
# 【L0105】语法拆解：`if` 要求条件 `not directories` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not directories` 是否成立；`directories` 表示本功能块中的 `directories` 值
    if not directories:
# 【L0106】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")
# 【L0107】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episodes`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[load_episode(directory) for directory in directories]`；`load_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`directories` 表示本功能块中的 `directories` 值。
    episodes = [load_episode(directory) for directory in directories]
# 【L0108】语法拆解：`if` 要求条件 `collection_split is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `collection_split is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if collection_split is not None:
# 【L0109】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episodes`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        episodes = [
# 【L0110】语法拆解：`episode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode`；在本项目中它表示一条轨迹相关值。
            episode
# 【L0111】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for episode in episodes` 中给出的序列，逐项完成“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
            for episode in episodes
# 【L0112】语法拆解：`if` 要求条件 `episode["collection_split"] == collection_split` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `episode["collection_split"] == collection_split` 是否成立；`episode` 表示一条轨迹相关值；`collection_split` 表示本功能块中的 `collection_split` 值
            if episode["collection_split"] == collection_split
# 【L0113】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
        ]
# 【L0114】语法拆解：`if` 要求条件 `not episodes` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not episodes` 是否成立；`episodes` 表示本功能块中的 `episodes` 值
        if not episodes:
# 【L0115】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(
# 【L0116】语法拆解：`f"no episodes use collection split {collection_split!r}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"no episodes use collection split {collection_split!r}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`no` 表示本功能块中的 `no` 值；`episodes` 表示本功能块中的 `episodes` 值。在“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"no episodes use collection split {collection_split!r}"
# 【L0117】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
            )
# 【L0118】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `fps_values`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `fps_values`，它在本项目中表示本功能块中的 `fps_values` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{round(item["fps"], 9) for item in episodes}`；`round` 表示本功能块中的 `round` 值；`item` 表示本功能块中的 `item` 值；`fps` 表示本功能块中的 `fps` 值。
    fps_values = {round(item["fps"], 9) for item in episodes}
# 【L0119】语法拆解：`if` 要求条件 `len(fps_values) != 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(fps_values) != 1` 是否成立；`fps_values` 表示本功能块中的 `fps_values` 值
    if len(fps_values) != 1:
# 【L0120】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")
# 【L0121】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first`。右侧语法为：`episodes[0]` 使用方括号索引；先计算 `0`，再从 `episodes` 取对应字典字段或数组元素。
# 【项目含义】得到 `first`，它在本项目中表示本功能块中的 `first` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]`；`episodes` 表示本功能块中的 `episodes` 值。
    first = episodes[0]
# 【L0122】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first_external`。右侧语法为：`read_rgb` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `first["directory"] / first["external_paths"][0]`；其中 `first["directory"] / first["external_paths"][0]` 的方括号表示先从 `first` 按键/索引 `"directory"] / first["external_paths"][0` 取值。
# 【项目含义】得到 `first_external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    first_external = read_rgb(first["directory"] / first["external_paths"][0])
# 【L0123】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first_wrist`。右侧语法为：`read_rgb` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `first["directory"] / first["wrist_paths"][0]`；其中 `first["directory"] / first["wrist_paths"][0]` 的方括号表示先从 `first` 按键/索引 `"directory"] / first["wrist_paths"][0` 取值。
# 【项目含义】得到 `first_wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])
# 【L0124】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `episodes`，每次把当前元素放进 `episode`；这会逐个处理“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”所需的帧、episode、动作或实验 case。
    for episode in episodes:
# 【L0125】语法拆解：`if` 要求条件 `episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,)` 是否成立；`episode` 表示一条轨迹相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；`shape` 表示本功能块中的 `shape` 值
        if episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,):
# 【L0126】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"unexpected state/action dimensions in {episode['directory']}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"unexpected state/action dimensions in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"unexpected state/action dimensions in {episode['directory']}")
# 【L0127】语法拆解：`if` 要求条件 `len(episode["external_paths"]) != len(episode["states"])` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(episode["external_paths"]) != len(episode["states"])` 是否成立；`episode` 表示一条轨迹相关值；`external_paths` 表示外部相机相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪
        if len(episode["external_paths"]) != len(episode["states"]):
# 【L0128】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"external image count changed in {episode['directory']}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"external image count changed in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"external image count changed in {episode['directory']}")
# 【L0129】语法拆解：`if` 要求条件 `len(episode["wrist_paths"]) != len(episode["states"])` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(episode["wrist_paths"]) != len(episode["states"])` 是否成立；`episode` 表示一条轨迹相关值；`wrist_paths` 表示腕部相机相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪
        if len(episode["wrist_paths"]) != len(episode["states"]):
# 【L0130】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"wrist image count changed in {episode['directory']}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"wrist image count changed in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"wrist image count changed in {episode['directory']}")
# 【L0131】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_shape`。右侧语法为：表达式 `read_rgb(episode["directory"] / episode["external_paths"][0]).shape` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        external_shape = read_rgb(episode["directory"] / episode["external_paths"][0]).shape
# 【L0132】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_shape`。右侧语法为：表达式 `read_rgb(episode["directory"] / episode["wrist_paths"][0]).shape` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        wrist_shape = read_rgb(episode["directory"] / episode["wrist_paths"][0]).shape
# 【L0133】语法拆解：`if` 要求条件 `external_shape != first_external.shape or wrist_shape != first_wrist.shape` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `external_shape != first_external.shape or wrist_shape != first_wrist.shape` 是否成立；`external_shape` 表示外部相机相关值；`first_external` 表示外部相机相关值；`shape` 表示本功能块中的 `shape` 值
        if external_shape != first_external.shape or wrist_shape != first_wrist.shape:
# 【L0134】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("camera shapes must remain constant across all episodes")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("camera shapes must remain constant across all episodes")` 并停止当前路径；说明当前输入违反“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError("camera shapes must remain constant across all episodes")
# 【L0135】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`episodes` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `episodes` 交回调用者；这个值的含义是：计算表达式 `episodes`；`episodes` 表示本功能块中的 `episodes` 值。
    return episodes
# 【L0136】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”中的逻辑段，让结构更容易看清。

# 【L0137】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 6：发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并（源码第 138-183 行）

### 5.A 数据流位置

- 上游：模块 5“发现 episode 并检查帧率、状态/动作维度和相机尺寸一致”。
- 本模块：发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并。
- 下游：处理结果继续交给模块 7“解析命令行、选择 split、数据源和 LeRobot 输出目录”。

### 5.B 为什么需要这一组代码

这一组负责“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。

### 5.D 本模块首次阅读要认识的调用

- `discover_dataset_roots(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `set(...)`：圆括号表示真正执行调用；修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。
- `root.resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `discover_episodes(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `seen_directories.add(...)`：圆括号表示真正执行调用；把机器人、刚体、传感器或配置注册到当前场景/集合。
- `episodes.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `round(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sorted(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.E 本模块定义的新函数

### 函数卡：`discover_dataset_roots()`（第 138-181 行）

- 定义了什么：发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`dataset_roots`：类型 `list[Path]`；项目含义是数据集相关值；`collection_split`（仅关键字）：类型 `str | None`，默认 `None`；项目含义是本功能块中的 `collection_split` 值
- 返回类型标注：`list[dict[str, Any]]`。
- 函数体实际 return：`episodes`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:211` 的 `episodes = discover_dataset_roots(`


### 5.F 这一模块的版本变化

- 当前第 138-183 行相对旧教学快照发生 `insert`：旧版 0 行，当前 46 行。 当前代码摘录：`def discover_dataset_roots(` / `dataset_roots: list[Path], *, collection_split: str | None = None` / `) -> list[dict[str, Any]]:` / `"""Load one logical dataset from independent, immutable episode roots."""`

### 5.G 逐行精读

```python
# 【L0138】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `discover_dataset_roots(参数在后续行继续)`；调用者把参数交给它完成“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”，后面的缩进代码是具体实现。
def discover_dataset_roots(
# 【L0139】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset_roots: list[Path], *, collection_split: str | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `dataset_roots`，它在本项目中表示数据集相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    dataset_roots: list[Path], *, collection_split: str | None = None
# 【L0140】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> list[dict[str, Any]]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
) -> list[dict[str, Any]]:
# 【L0141】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Load one logical dataset from independent, immutable episode roots.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Load one logical dataset from independent, immutable episode roots."""
# 【L0142】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中的逻辑段，让结构更容易看清。

# 【L0143】语法拆解：`if` 要求条件 `not dataset_roots` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not dataset_roots` 是否成立；`dataset_roots` 表示数据集相关值
    if not dataset_roots:
# 【L0144】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("at least one dataset root is required")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("at least one dataset root is required")` 并停止当前路径；说明当前输入违反“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”要求，不能继续进入仿真、训练或评测。
        raise ValueError("at least one dataset root is required")
# 【L0145】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episodes`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    episodes = []
# 【L0146】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `seen_directories: set[Path]`。右侧语法为：`set` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】把右侧结果写进 `seen_directories: set[Path]`（写入 `seen_directories: set[Path]` 指定的字段）；右侧具体做的是：计算表达式 `set()`；`set` 表示本功能块中的 `set` 值。
    seen_directories: set[Path] = set()
# 【L0147】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `dataset_roots`，每次把当前元素放进 `root`；这会逐个处理“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”所需的帧、episode、动作或实验 case。
    for root in dataset_roots:
# 【L0148】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `resolved_root`。右侧语法为：`root` 是模块/对象，点号 `.` 从中取出 `resolve` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `resolved_root`，它在本项目中表示本功能块中的 `resolved_root` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `root.resolve()`；`root` 表示本功能块中的 `root` 值；`resolve` 表示本功能块中的 `resolve` 值。
        resolved_root = root.resolve()
# 【L0149】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `discover_episodes(root, collection_split=collection_split)`，每次把当前元素放进 `episode`；这会逐个处理“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”所需的帧、episode、动作或实验 case。
        for episode in discover_episodes(root, collection_split=collection_split):
# 【L0150】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `directory`。右侧语法为：`episode["directory"].resolve()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode["directory"].resolve()`；`episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`resolve` 表示本功能块中的 `resolve` 值。
            directory = episode["directory"].resolve()
# 【L0151】语法拆解：`if` 要求条件 `directory in seen_directories` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `directory in seen_directories` 是否成立；`directory` 表示目录相关值；`seen_directories` 表示本功能块中的 `seen_directories` 值
            if directory in seen_directories:
# 【L0152】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"duplicate episode directory: {directory}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"duplicate episode directory: {directory}")` 并停止当前路径；说明当前输入违反“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”要求，不能继续进入仿真、训练或评测。
                raise ValueError(f"duplicate episode directory: {directory}")
# 【L0153】语法拆解：`seen_directories` 是模块/对象，点号 `.` 从中取出 `add` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `directory`。
# 【项目含义】对 `seen_directories` 调用 `add(directory)`：把机器人、刚体、传感器或配置注册到当前场景/集合。本行产生的修改/返回值服务于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
            seen_directories.add(directory)
# 【L0154】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode["dataset_root"]`。右侧语法为：`resolved_root` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `episode["dataset_root"]`（写入 `episode["dataset_root"]` 指定的字段）；右侧具体做的是：计算表达式 `resolved_root`；`resolved_root` 表示本功能块中的 `resolved_root` 值。
            episode["dataset_root"] = resolved_root
# 【L0155】语法拆解：`episodes` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode`。
# 【项目含义】对 `episodes` 执行 `append`，把 `episode` 加入已有结果；该集合表示本功能块中的 `episodes` 值，随后会用于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
            episodes.append(episode)
# 【L0156】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中的逻辑段，让结构更容易看清。

# 【L0157】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `fps_values`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `fps_values`，它在本项目中表示本功能块中的 `fps_values` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{round(item["fps"], 9) for item in episodes}`；`round` 表示本功能块中的 `round` 值；`item` 表示本功能块中的 `item` 值；`fps` 表示本功能块中的 `fps` 值。
    fps_values = {round(item["fps"], 9) for item in episodes}
# 【L0158】语法拆解：`if` 要求条件 `len(fps_values) != 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(fps_values) != 1` 是否成立；`fps_values` 表示本功能块中的 `fps_values` 值
    if len(fps_values) != 1:
# 【L0159】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(` 并停止当前路径；说明当前输入违反“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”要求，不能继续进入仿真、训练或评测。
        raise ValueError(
# 【L0160】语法拆解：`f"dataset roots use different control frequencies: {sorted(fps_values)}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"dataset roots use different control frequencies: {sorted(fps_values)}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`roots` 表示本功能块中的 `roots` 值。在“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            f"dataset roots use different control frequencies: {sorted(fps_values)}"
# 【L0161】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
        )
# 【L0162】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first`。右侧语法为：`episodes[0]` 使用方括号索引；先计算 `0`，再从 `episodes` 取对应字典字段或数组元素。
# 【项目含义】得到 `first`，它在本项目中表示本功能块中的 `first` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]`；`episodes` 表示本功能块中的 `episodes` 值。
    first = episodes[0]
# 【L0163】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_external_shape`。右侧语法为：`read_rgb(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expected_external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    expected_external_shape = read_rgb(
# 【L0164】语法拆解：`first["directory"] / first["external_paths"][0]` 使用方括号索引；先计算 `"directory"] / first["external_paths"][0`，再从 `first` 取对应字典字段或数组元素。
# 【项目含义】把表达式/参数 `first["directory"] / first["external_paths"][0]` 接入当前完整语句；`first` 表示本功能块中的 `first` 值；`directory` 表示目录相关值；`external_paths` 表示外部相机相关值。在“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        first["directory"] / first["external_paths"][0]
# 【L0165】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `).shape` 中的索引或转换；`shape` 表示本功能块中的 `shape` 值，用于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
    ).shape
# 【L0166】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_wrist_shape`。右侧语法为：`read_rgb(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expected_wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    expected_wrist_shape = read_rgb(
# 【L0167】语法拆解：`first["directory"] / first["wrist_paths"][0]` 使用方括号索引；先计算 `"directory"] / first["wrist_paths"][0`，再从 `first` 取对应字典字段或数组元素。
# 【项目含义】把表达式/参数 `first["directory"] / first["wrist_paths"][0]` 接入当前完整语句；`first` 表示本功能块中的 `first` 值；`directory` 表示目录相关值；`wrist_paths` 表示腕部相机相关值。在“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        first["directory"] / first["wrist_paths"][0]
# 【L0168】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `).shape` 中的索引或转换；`shape` 表示本功能块中的 `shape` 值，用于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
    ).shape
# 【L0169】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `episodes[1:]`，每次把当前元素放进 `episode`；这会逐个处理“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”所需的帧、episode、动作或实验 case。
    for episode in episodes[1:]:
# 【L0170】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_shape`。右侧语法为：`read_rgb(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        external_shape = read_rgb(
# 【L0171】语法拆解：`episode["directory"] / episode["external_paths"][0]` 使用方括号索引；先计算 `"directory"] / episode["external_paths"][0`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】把表达式/参数 `episode["directory"] / episode["external_paths"][0]` 接入当前完整语句；`episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`external_paths` 表示外部相机相关值。在“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode["directory"] / episode["external_paths"][0]
# 【L0172】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `).shape` 中的索引或转换；`shape` 表示本功能块中的 `shape` 值，用于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
        ).shape
# 【L0173】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_shape`。右侧语法为：`read_rgb(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        wrist_shape = read_rgb(
# 【L0174】语法拆解：`episode["directory"] / episode["wrist_paths"][0]` 使用方括号索引；先计算 `"directory"] / episode["wrist_paths"][0`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】把表达式/参数 `episode["directory"] / episode["wrist_paths"][0]` 接入当前完整语句；`episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`wrist_paths` 表示腕部相机相关值。在“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode["directory"] / episode["wrist_paths"][0]
# 【L0175】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `).shape` 中的索引或转换；`shape` 表示本功能块中的 `shape` 值，用于“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
        ).shape
# 【L0176】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
        if (
# 【L0177】语法拆解：表达式 `external_shape != expected_external_shape` 使用运算符 `!=`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `external_shape != expected_external_shape` 接到上一行尚未结束的布尔表达式；`external_shape` 表示外部相机相关值；`expected_external_shape` 表示外部相机相关值。比较结果共同决定“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”是否通过。
            external_shape != expected_external_shape
# 【L0178】语法拆解：表达式 `or wrist_shape != expected_wrist_shape` 使用运算符 `!=`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `wrist_shape != expected_wrist_shape` 用“或者”接到上一行判断中；判断 `wrist_shape != expected_wrist_shape` 是否成立；`wrist_shape` 表示腕部相机相关值；`expected_wrist_shape` 表示腕部相机相关值。所有连接条件共同决定是否进入后续分支。
            or wrist_shape != expected_wrist_shape
# 【L0179】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
        ):
# 【L0180】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("camera shapes differ across dataset roots")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("camera shapes differ across dataset roots")` 并停止当前路径；说明当前输入违反“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”要求，不能继续进入仿真、训练或评测。
            raise ValueError("camera shapes differ across dataset roots")
# 【L0181】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`episodes` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `episodes` 交回调用者；这个值的含义是：计算表达式 `episodes`；`episodes` 表示本功能块中的 `episodes` 值。
    return episodes
# 【L0182】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中的逻辑段，让结构更容易看清。

# 【L0183】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 7：解析命令行、选择 split、数据源和 LeRobot 输出目录（源码第 184-234 行）

### 5.A 数据流位置

- 上游：模块 6“发现并校验多个数据源目录，支持修正轨迹与原始轨迹合并”。
- 本模块：解析命令行、选择 split、数据源和 LeRobot 输出目录。
- 下游：处理结果继续交给模块 8“声明 LeRobot 图像、状态、动作、任务和索引 schema”。

### 5.B 为什么需要这一组代码

这一组负责“解析命令行、选择 split、数据源和 LeRobot 输出目录”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `path.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `discover_dataset_roots(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `round(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.isclose(...)`：圆括号表示真正执行调用；NumPy 的 `isclose` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `Path(...)`：圆括号表示真正执行调用；创建路径对象。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 184-309 行）

- 定义了什么：解析命令行、选择 split、数据源和 LeRobot 输出目录。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 当前第 186-191 行相对旧教学快照发生 `replace`：旧版 1 行，当前 6 行。 旧代码摘录：`parser.add_argument("dataset_root", type=Path)` 当前代码摘录：`parser.add_argument(` / `"dataset_roots",` / `type=Path,` / `nargs="+",`
- 当前第 194-194 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`parser.add_argument("--report", type=Path)`
- 当前第 210-212 行相对旧教学快照发生 `replace`：旧版 2 行，当前 3 行。 旧代码摘录：`episodes = discover_episodes(` / `args.dataset_root.expanduser().resolve(), collection_split=args.split` 当前代码摘录：`dataset_roots = [path.expanduser().resolve() for path in args.dataset_roots]` / `episodes = discover_dataset_roots(` / `dataset_roots, collection_split=args.split`

### 5.G 逐行精读

```python
# 【L0184】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“解析命令行、选择 split、数据源和 LeRobot 输出目录”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0185】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0186】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0187】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"dataset_roots"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
        "dataset_roots",
# 【L0188】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        type=Path,
# 【L0189】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `nargs`。右侧语法为：`"+"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `nargs` 传入 `"+"`；该参数在本项目中表示本功能块中的 `nargs` 值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        nargs="+",
# 【L0190】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"One or more immutable episode roots to combine into one LeRobot dataset."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"One or more immutable episode roots to combine into one LeRobot dataset."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        help="One or more immutable episode roots to combine into one LeRobot dataset.",
# 【L0191】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
    )
# 【L0192】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--repo-id"`；第 2 个实参 `required=True`；第 3 个实参 `help="LeRobot repository id, e.g. local/rm65_sim"`。
# 【项目含义】声明命令行参数 `--repo-id`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", required=True, help="LeRobot repository id, e.g. local/rm65_sim")
# 【L0193】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--overwrite"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--overwrite`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--overwrite", action="store_true")
# 【L0194】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--report"`；第 2 个实参 `type=Path`。
# 【项目含义】声明命令行参数 `--report`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--report", type=Path)
# 【L0195】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0196】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--split"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
        "--split",
# 【L0197】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `choices`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `choices` 传入 `("train", "validation")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        choices=("train", "validation"),
# 【L0198】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Convert only the declared collection split."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Convert only the declared collection split."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        help="Convert only the declared collection split.",
# 【L0199】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
    )
# 【L0200】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析命令行、选择 split、数据源和 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0201】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-window"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
        "--policy-window",
# 【L0202】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        action="store_true",
# 【L0203】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        help=(
# 【L0204】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"Compress stationary holds and omit post-success retreat/final settle. "`；在“解析命令行、选择 split、数据源和 LeRobot 输出目录”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "Compress stationary holds and omit post-success retreat/final settle. "
# 【L0205】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Use a new repo id; the source episodes are never modified."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
            "Use a new repo id; the source episodes are never modified."
# 【L0206】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        ),
# 【L0207】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
    )
# 【L0208】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0209】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0210】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset_roots`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `dataset_roots`，它在本项目中表示数据集相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[path.expanduser().resolve() for path in args.dataset_roots]`；`path` 表示路径相关值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    dataset_roots = [path.expanduser().resolve() for path in args.dataset_roots]
# 【L0211】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episodes`。右侧语法为：`discover_dataset_roots(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `discover_dataset_roots(`；`discover_dataset_roots` 表示数据集相关值。
    episodes = discover_dataset_roots(
# 【L0212】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset_roots, collection_split`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`split`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `dataset_roots, collection_split`；`dataset_roots` 表示数据集相关值；`collection_split` 表示本功能块中的 `collection_split` 值。右侧的来源是：计算表达式 `args.split`；`split` 表示本功能块中的 `split` 值。
        dataset_roots, collection_split=args.split
# 【L0213】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
    )
# 【L0214】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `fps`。右侧语法为：`episodes[0]["fps"]` 使用方括号索引；先计算 `0]["fps"`，再从 `episodes` 取对应字典字段或数组元素。
# 【项目含义】得到 `fps`，它在本项目中表示本功能块中的 `fps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]["fps"]`；`episodes` 表示本功能块中的 `episodes` 值；`fps` 表示本功能块中的 `fps` 值。
    fps = episodes[0]["fps"]
# 【L0215】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rounded_fps`。右侧语法为：`round` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `fps`。
# 【项目含义】得到 `rounded_fps`，它在本项目中表示本功能块中的 `rounded_fps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `round(fps)`；`round` 表示本功能块中的 `round` 值；`fps` 表示本功能块中的 `fps` 值。
    rounded_fps = round(fps)
# 【L0216】语法拆解：`if` 要求条件 `not np.isclose(fps, rounded_fps)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not np.isclose(fps, rounded_fps)` 是否成立；`isclose` 表示本功能块中的 `isclose` 值；`fps` 表示本功能块中的 `fps` 值；`rounded_fps` 表示本功能块中的 `rounded_fps` 值
    if not np.isclose(fps, rounded_fps):
# 【L0217】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"LeRobot conversion requires an integer fps, got {fps}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"LeRobot conversion requires an integer fps, got {fps}")` 并停止当前路径；说明当前输入违反“解析命令行、选择 split、数据源和 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"LeRobot conversion requires an integer fps, got {fps}")
# 【L0218】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0219】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“解析命令行、选择 split、数据源和 LeRobot 输出目录”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0220】语法拆解：`from lerobot.common.datasets.lerobot_dataset` 指定来源模块；`import HF_LEROBOT_HOME, LeRobotDataset` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `lerobot` 引入 `HF_LEROBOT_HOME, LeRobotDataset`。在这份程序里，`lerobot` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
        from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset
# 【L0221】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `ImportError as error`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
    except ImportError as error:
# 【L0222】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“解析命令行、选择 split、数据源和 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0223】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
            "LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."
# 【L0224】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `) from error` 中的索引或转换；`from` 表示本功能块中的 `from` 值；`error` 表示本功能块中的 `error` 值，用于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        ) from error
# 【L0225】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0226】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_path`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `output_path`，它在本项目中表示输出、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(HF_LEROBOT_HOME / args.repo_id).resolve()`；`HF_LEROBOT_HOME` 表示本功能块中的 `HF_LEROBOT_HOME` 值；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；`resolve` 表示本功能块中的 `resolve` 值。
    output_path = (HF_LEROBOT_HOME / args.repo_id).resolve()
# 【L0227】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `hf_home`。右侧语法为：`Path` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `HF_LEROBOT_HOME).resolve(`。
# 【项目含义】得到 `hf_home`，它在本项目中表示本功能块中的 `hf_home` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(HF_LEROBOT_HOME).resolve()`；`HF_LEROBOT_HOME` 表示本功能块中的 `HF_LEROBOT_HOME` 值；`resolve` 表示本功能块中的 `resolve` 值。
    hf_home = Path(HF_LEROBOT_HOME).resolve()
# 【L0228】语法拆解：`if` 要求条件 `hf_home not in output_path.parents` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `hf_home not in output_path.parents` 是否成立；`hf_home` 表示本功能块中的 `hf_home` 值；`output_path` 表示输出、路径相关值；`parents` 表示本功能块中的 `parents` 值
    if hf_home not in output_path.parents:
# 【L0229】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("repo id resolves outside HF_LEROBOT_HOME")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("repo id resolves outside HF_LEROBOT_HOME")` 并停止当前路径；说明当前输入违反“解析命令行、选择 split、数据源和 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise ValueError("repo id resolves outside HF_LEROBOT_HOME")
# 【L0230】语法拆解：`if` 要求条件 `output_path.exists()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `output_path.exists()` 是否成立；`output_path` 表示输出、路径相关值；`exists` 表示本功能块中的 `exists` 值
    if output_path.exists():
# 【L0231】语法拆解：`if` 要求条件 `not args.overwrite` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.overwrite` 是否成立；`overwrite` 表示本功能块中的 `overwrite` 值
        if not args.overwrite:
# 【L0232】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")` 并停止当前路径；说明当前输入违反“解析命令行、选择 split、数据源和 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
            raise FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")
# 【L0233】语法拆解：`shutil` 是模块/对象，点号 `.` 从中取出 `rmtree` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `output_path`。
# 【项目含义】对 `shutil` 调用 `rmtree(output_path)`：调用 `shutil` 提供的 `rmtree` 操作。本行产生的修改/返回值服务于“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
        shutil.rmtree(output_path)
# 【L0234】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析命令行、选择 split、数据源和 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“解析命令行、选择 split、数据源和 LeRobot 输出目录”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 8：声明 LeRobot 图像、状态、动作、任务和索引 schema（源码第 235-259 行）

### 5.A 数据流位置

- 上游：模块 7“解析命令行、选择 split、数据源和 LeRobot 输出目录”。
- 本模块：声明 LeRobot 图像、状态、动作、任务和索引 schema。
- 下游：处理结果继续交给模块 9“逐 episode、逐帧写入 LeRobot 数据集”。

### 5.B 为什么需要这一组代码

这一组负责“声明 LeRobot 图像、状态、动作、任务和索引 schema”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `joints`：六个 RM65 关节位置的一维 NumPy 数组。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `LeRobotDataset.create(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0235】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `first`。右侧语法为：`episodes[0]` 使用方括号索引；先计算 `0`，再从 `episodes` 取对应字典字段或数组元素。
# 【项目含义】得到 `first`，它在本项目中表示本功能块中的 `first` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]`；`episodes` 表示本功能块中的 `episodes` 值。
    first = episodes[0]
# 【L0236】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_shape`。右侧语法为：表达式 `read_rgb(first["directory"] / first["external_paths"][0]).shape` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape
# 【L0237】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_shape`。右侧语法为：表达式 `read_rgb(first["directory"] / first["wrist_paths"][0]).shape` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    wrist_shape = read_rgb(first["directory"] / first["wrist_paths"][0]).shape
# 【L0238】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset`。右侧语法为：`LeRobotDataset.create(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `LeRobotDataset.create(`；`LeRobotDataset` 表示本功能块中的 `LeRobotDataset` 值；`create` 表示本功能块中的 `create` 值。
    dataset = LeRobotDataset.create(
# 【L0239】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `args.repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        repo_id=args.repo_id,
# 【L0240】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `robot_type`。右侧语法为：`"rm65_4c2"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `robot_type` 传入 `"rm65_4c2"`；该参数在本项目中表示本功能块中的 `robot_type` 值，会参与“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        robot_type="rm65_4c2",
# 【L0241】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `fps`。右侧语法为：`int` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `rounded_fps`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `fps` 传入 `int(rounded_fps)`；该参数在本项目中表示本功能块中的 `fps` 值，会参与“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        fps=int(rounded_fps),
# 【L0242】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `features`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `features`，它在本项目中表示本功能块中的 `features` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        features={
# 【L0243】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `image`，它表示π0.5 按名称索引的三个图像槽位字典；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "image": {
# 【L0244】语法拆解：这是字典键值对：`"dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"image"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `dtype`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `dtype` 数据；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": "image",
# 【L0245】语法拆解：这是字典键值对：`"shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`external_shape` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `shape`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `shape` 数据；字段值来自 `external_shape`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": external_shape,
# 【L0246】语法拆解：这是字典键值对：`"names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `names`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `names` 数据；字段值来自 `["height", "width", "channel"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "names": ["height", "width", "channel"],
# 【L0247】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
            },
# 【L0248】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_image`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `wrist_image` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "wrist_image": {
# 【L0249】语法拆解：这是字典键值对：`"dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"image"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `dtype`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `dtype` 数据；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": "image",
# 【L0250】语法拆解：这是字典键值对：`"shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`wrist_shape` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `shape`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `shape` 数据；字段值来自 `wrist_shape`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": wrist_shape,
# 【L0251】语法拆解：这是字典键值对：`"names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `names`，它表示“声明 LeRobot 图像、状态、动作、任务和索引 schema”中的 `names` 数据；字段值来自 `["height", "width", "channel"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "names": ["height", "width", "channel"],
# 【L0252】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
            },
# 【L0253】语法拆解：这是字典键值对：`"joints"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】定义字典/JSON 字段 `joints`，它表示LeRobot 一帧中的六个 RM65 关节角；字段值来自 `{"dtype": "float32", "shape": (6,), "names": ["joints"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "joints": {"dtype": "float32", "shape": (6,), "names": ["joints"]},
# 【L0254】语法拆解：这是字典键值对：`"gripper"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `{"dtype": "float32", "shape": (1,), "names": ["gripper"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper": {"dtype": "float32", "shape": (1,), "names": ["gripper"]},
# 【L0255】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `{"dtype": "float32", "shape": (7,), "names": ["actions"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "actions": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
# 【L0256】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        },
# 【L0257】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image_writer_threads`。右侧语法为：`10` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `image_writer_threads` 传入 `10`；该参数在本项目中表示图像相关值，会参与“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        image_writer_threads=10,
# 【L0258】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image_writer_processes`。右侧语法为：`5` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `image_writer_processes` 传入 `5`；该参数在本项目中表示图像相关值，会参与“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
        image_writer_processes=5,
# 【L0259】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“声明 LeRobot 图像、状态、动作、任务和索引 schema”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 9：逐 episode、逐帧写入 LeRobot 数据集（源码第 260-286 行）

### 5.A 数据流位置

- 上游：模块 8“声明 LeRobot 图像、状态、动作、任务和索引 schema”。
- 本模块：逐 episode、逐帧写入 LeRobot 数据集。
- 下游：处理结果继续交给模块 10“保存数据集并输出转换数量、来源和跳过原因”。

### 5.B 为什么需要这一组代码

这一组负责“逐 episode、逐帧写入 LeRobot 数据集”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `joints`：六个 RM65 关节位置的一维 NumPy 数组。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。
- `phase_ids`：每一帧所处专家阶段的整数编号。
- `phase_names`：阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
- `indices`：当前 episode 中会被写入目标数据集的帧索引。

### 5.D 本模块首次阅读要认识的调用

- `select_policy_window_indices(...)`：圆括号表示真正执行调用；按阶段和运动变化挑选训练帧，减少长时间静止 hold 对数据分布的占比。
- `np.arange(...)`：圆括号表示真正执行调用；按起点、终点和步长创建等间隔数值序列。
- `selected_phase_counts.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `dataset.add_frame(...)`：圆括号表示真正执行调用；把一帧观测、动作和任务文字加入 LeRobot 数据集。
- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `dataset.save_episode(...)`：圆括号表示真正执行调用；结束并保存当前 LeRobot episode。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0260】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `total_frames`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `total_frames`，它在本项目中表示本功能块中的 `total_frames` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_frames = 0
# 【L0261】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_frames`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `source_frames`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    source_frames = 0
# 【L0262】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `selected_phase_counts: dict[str, int]`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】把右侧结果写进 `selected_phase_counts: dict[str, int]`（写入 `selected_phase_counts: dict[str, int]` 指定的字段）；右侧具体做的是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    selected_phase_counts: dict[str, int] = {}
# 【L0263】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `episodes`，每次把当前元素放进 `episode`；这会逐个处理“逐 episode、逐帧写入 LeRobot 数据集”所需的帧、episode、动作或实验 case。
    for episode in episodes:
# 【L0264】语法拆解：表达式 `source_frames += len(episode["states"])` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `source_frames + len(episode["states"])` 更新 `source_frames` 原值；`source_frames` 表示源位置相关值，常用于累计步数、距离、损失或成功次数。
        source_frames += len(episode["states"])
# 【L0265】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `indices`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `indices`，它在本项目中表示当前 episode 中会被写入目标数据集的帧索引；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        indices = (
# 【L0266】语法拆解：`select_policy_window_indices` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode`。
# 【项目含义】调用 `select_policy_window_indices(episode)`：按阶段和运动变化挑选训练帧，减少长时间静止 hold 对数据分布的占比。它的结果/修改用于“逐 episode、逐帧写入 LeRobot 数据集”。
            select_policy_window_indices(episode)
# 【L0267】语法拆解：`if` 要求条件 `args.policy_window` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.policy_window` 是否成立；`policy_window` 表示策略相关值
            if args.policy_window
# 【L0268】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】对 `else np` 调用 `arange(len(episode["states"]), dtype=np.int64)`：调用 `else np` 提供的 `arange` 操作。本行产生的修改/返回值服务于“逐 episode、逐帧写入 LeRobot 数据集”。
            else np.arange(len(episode["states"]), dtype=np.int64)
# 【L0269】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入 LeRobot 数据集”。
        )
# 【L0270】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `indices`，每次把当前元素放进 `index`；这会逐个处理“逐 episode、逐帧写入 LeRobot 数据集”所需的帧、episode、动作或实验 case。
        for index in indices:
# 【L0271】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `index`。右侧语法为：`int` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `index`。
# 【项目含义】得到 `index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `int(index)`；`index` 表示索引相关值。
            index = int(index)
# 【L0272】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase`。右侧语法为：`episode["phase_names"][int(episode["phase_ids"][index])]` 使用方括号索引；先计算 `"phase_names"][int(episode["phase_ids"][index])`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】得到 `phase`，它在本项目中表示本功能块中的 `phase` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode["phase_names"][int(episode["phase_ids"][index])]`；`episode` 表示一条轨迹相关值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；`phase_ids` 表示每一帧所处专家阶段的整数编号。
            phase = episode["phase_names"][int(episode["phase_ids"][index])]
# 【L0273】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `selected_phase_counts[phase]`。右侧语法为：表达式 `selected_phase_counts.get(phase, 0) + 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把右侧结果写进 `selected_phase_counts[phase]`（写入 `selected_phase_counts[phase]` 指定的字段）；右侧具体做的是：计算表达式 `selected_phase_counts.get(phase, 0) + 1`；`selected_phase_counts` 表示本功能块中的 `selected_phase_counts` 值；`get` 表示本功能块中的 `get` 值；`phase` 表示本功能块中的 `phase` 值。
            selected_phase_counts[phase] = selected_phase_counts.get(phase, 0) + 1
# 【L0274】语法拆解：`dataset.add_frame(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `dataset.add_frame`：把一帧观测、动作和任务文字加入 LeRobot 数据集；本行实际操作 `dataset.add_frame(`。`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`add_frame` 表示帧相关值。
            dataset.add_frame(
# 【L0275】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 episode、逐帧写入 LeRobot 数据集”。
                {
# 【L0276】语法拆解：这是字典键值对：`"image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`read_rgb` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode["directory"] / episode["external_paths"][index]`；其中 `episode["directory"] / episode["external_paths"][index]` 的方括号表示先从 `episode` 按键/索引 `"directory"] / episode["external_paths"][index` 取值。
# 【项目含义】定义字典/JSON 字段 `image`，它表示π0.5 按名称索引的三个图像槽位字典；字段值来自 `read_rgb(episode["directory"] / episode["external_paths"][index])`，因此保存/传递的是这个表达式当前计算出的结果。
                    "image": read_rgb(episode["directory"] / episode["external_paths"][index]),
# 【L0277】语法拆解：这是字典键值对：`"wrist_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`read_rgb` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode["directory"] / episode["wrist_paths"][index]`；其中 `episode["directory"] / episode["wrist_paths"][index]` 的方括号表示先从 `episode` 按键/索引 `"directory"] / episode["wrist_paths"][index` 取值。
# 【项目含义】定义字典/JSON 字段 `wrist_image`，它表示“逐 episode、逐帧写入 LeRobot 数据集”中的 `wrist_image` 数据；字段值来自 `read_rgb(episode["directory"] / episode["wrist_paths"][index])`，因此保存/传递的是这个表达式当前计算出的结果。
                    "wrist_image": read_rgb(episode["directory"] / episode["wrist_paths"][index]),
# 【L0278】语法拆解：这是字典键值对：`"joints"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode["states"][index, :6]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】定义字典/JSON 字段 `joints`，它表示LeRobot 一帧中的六个 RM65 关节角；字段值来自 `episode["states"][index, :6]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "joints": episode["states"][index, :6],
# 【L0279】语法拆解：这是字典键值对：`"gripper"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode["states"][index, 6:7]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `episode["states"][index, 6:7]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "gripper": episode["states"][index, 6:7],
# 【L0280】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode["actions"][index]` 使用方括号索引；先计算 `"actions"][index`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `episode["actions"][index]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "actions": episode["actions"][index],
# 【L0281】语法拆解：这是字典键值对：`"task"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `episode` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `task`，它表示LeRobot 使用的语言任务字段，训练时会成为 prompt；字段值来自 `episode["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "task": episode["prompt"],
# 【L0282】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入 LeRobot 数据集”。
                }
# 【L0283】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入 LeRobot 数据集”。
            )
# 【L0284】语法拆解：表达式 `total_frames += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `total_frames + 1` 更新 `total_frames` 原值；`total_frames` 表示本功能块中的 `total_frames` 值，常用于累计步数、距离、损失或成功次数。
            total_frames += 1
# 【L0285】语法拆解：`dataset` 是模块/对象，点号 `.` 从中取出 `save_episode` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】调用 `dataset.save_episode`：结束并保存当前 LeRobot episode；本行实际操作 `dataset.save_episode()`。`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`save_episode` 表示一条轨迹相关值。
        dataset.save_episode()
# 【L0286】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“逐 episode、逐帧写入 LeRobot 数据集”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“逐 episode、逐帧写入 LeRobot 数据集”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 10：保存数据集并输出转换数量、来源和跳过原因（源码第 287-313 行）

### 5.A 数据流位置

- 上游：模块 9“逐 episode、逐帧写入 LeRobot 数据集”。
- 本模块：保存数据集并输出转换数量、来源和跳过原因。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“保存数据集并输出转换数量、来源和跳过原因”。它服务于本文件要解决的总问题：OpenPI 不能直接训练自定义 NPZ；长时间静止帧还会让模型过度学习不动。 这一组的处理结果会参与：验证来源、选择有效帧或 policy window、声明七维动作/状态和两路图像 schema，再逐帧写入数据集。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `sum(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sorted(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `selected_phase_counts.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `args.report.parent.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `args.report.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 当前第 287-308 行相对旧教学快照发生 `replace`：旧版 17 行，当前 22 行。 旧代码摘录：`print(` / `json.dumps(` / `{` / `"status": "pass",` 当前代码摘录：`report = {` / `"status": "pass",` / `"repo_id": args.repo_id,` / `"dataset_roots": [str(path) for path in dataset_roots],`

### 5.G 逐行精读

```python
# 【L0287】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0288】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0289】语法拆解：这是字典键值对：`"repo_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】定义字典/JSON 字段 `repo_id`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0290】语法拆解：这是字典键值对：`"dataset_roots"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `dataset_roots`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `dataset_roots` 数据；字段值来自 `[str(path) for path in dataset_roots]`，因此保存/传递的是这个表达式当前计算出的结果。
        "dataset_roots": [str(path) for path in dataset_roots],
# 【L0291】语法拆解：这是字典键值对：`"output_path"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `output_path`。
# 【项目含义】定义字典/JSON 字段 `output_path`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `output_path` 数据；字段值来自 `str(output_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "output_path": str(output_path),
# 【L0292】语法拆解：这是字典键值对：`"episode_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episodes`。
# 【项目含义】定义字典/JSON 字段 `episode_count`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `episode_count` 数据；字段值来自 `len(episodes)`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode_count": len(episodes),
# 【L0293】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `episode_count_by_dataset_root`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `episode_count_by_dataset_root` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode_count_by_dataset_root": {
# 【L0294】语法拆解：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `root): sum(episode["dataset_root"] == root for episode in episodes`。
# 【项目含义】调用 `str(root): sum(episode["dataset_root"] == root for episode in episodes)`：把路径、数字或其他对象转换为命令行参数需要的文本；这一行通常是外层命令列表中的一个元素。它的结果/修改用于“保存数据集并输出转换数量、来源和跳过原因”。
            str(root): sum(episode["dataset_root"] == root for episode in episodes)
# 【L0295】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for root in dataset_roots` 中给出的序列，逐项完成“保存数据集并输出转换数量、来源和跳过原因”。
            for root in dataset_roots
# 【L0296】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存数据集并输出转换数量、来源和跳过原因”。
        },
# 【L0297】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`total_frames` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `frame_count` 数据；字段值来自 `total_frames`，因此保存/传递的是这个表达式当前计算出的结果。
        "frame_count": total_frames,
# 【L0298】语法拆解：这是字典键值对：`"source_frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_frames` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_frame_count`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `source_frame_count` 数据；字段值来自 `source_frames`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_frame_count": source_frames,
# 【L0299】语法拆解：这是字典键值对：`"policy_window"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_window`。
# 【项目含义】定义字典/JSON 字段 `policy_window`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `policy_window` 数据；字段值来自 `args.policy_window`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_window": args.policy_window,
# 【L0300】语法拆解：这是字典键值对：`"selected_phase_counts"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`dict` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sorted(selected_phase_counts.items())`。
# 【项目含义】定义字典/JSON 字段 `selected_phase_counts`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `selected_phase_counts` 数据；字段值来自 `dict(sorted(selected_phase_counts.items()))`，因此保存/传递的是这个表达式当前计算出的结果。
        "selected_phase_counts": dict(sorted(selected_phase_counts.items())),
# 【L0301】语法拆解：这是字典键值对：`"fps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`int` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `rounded_fps`。
# 【项目含义】定义字典/JSON 字段 `fps`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `fps` 数据；字段值来自 `int(rounded_fps)`，因此保存/传递的是这个表达式当前计算出的结果。
        "fps": int(rounded_fps),
# 【L0302】语法拆解：这是字典键值对：`"collection_split"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`split`。
# 【项目含义】定义字典/JSON 字段 `collection_split`，它表示“保存数据集并输出转换数量、来源和跳过原因”中的 `collection_split` 数据；字段值来自 `args.split`，因此保存/传递的是这个表达式当前计算出的结果。
        "collection_split": args.split,
# 【L0303】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存数据集并输出转换数量、来源和跳过原因”。
    }
# 【L0304】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `text`。右侧语法为：表达式 `json.dumps(report, indent=2) + "\n"` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `text`，它在本项目中表示本功能块中的 `text` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 Python 字典序列化为 JSON 文本，供日志、报告或下游程序读取。
    text = json.dumps(report, indent=2) + "\n"
# 【L0305】语法拆解：`if` 要求条件 `args.report is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.report is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.report is not None:
# 【L0306】语法拆解：`args.report.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.report.parent.mkdir(parents=True, exist_ok=True)`。`report` 表示机器可读实验报告字典；`parent` 表示本功能块中的 `parent` 值。
        args.report.parent.mkdir(parents=True, exist_ok=True)
# 【L0307】语法拆解：`args.report` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `args.report.write_text(text, encoding="utf-8")`。`report` 表示机器可读实验报告字典；`write_text` 表示本功能块中的 `write_text` 值。
        args.report.write_text(text, encoding="utf-8")
# 【L0308】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `end=""`。
# 【项目含义】把 `text, end=""` 的当前值/文字输出到终端；它用于观察“保存数据集并输出转换数量、来源和跳过原因”进度，也给日志留下可搜索证据。
    print(text, end="")
# 【L0309】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0310】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存数据集并输出转换数量、来源和跳过原因”中的逻辑段，让结构更容易看清。

# 【L0311】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存数据集并输出转换数量、来源和跳过原因”中的逻辑段，让结构更容易看清。

# 【L0312】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0313】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“保存数据集并输出转换数量、来源和跳过原因”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“保存数据集并输出转换数量、来源和跳过原因”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。