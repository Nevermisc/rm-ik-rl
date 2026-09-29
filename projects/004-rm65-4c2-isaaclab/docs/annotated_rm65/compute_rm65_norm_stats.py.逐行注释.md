# `compute_rm65_norm_stats.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/compute_rm65_norm_stats.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`6c280572c1890377c18747afe9c3989787360cb08748d24575f7cf72b0a94e11`
- 总行数：112

## 1. 先把这个程序放进整个项目

- 所处阶段：训练数据准备：按实际 transform 计算 RM65 state/actions 归一化统计。
- 输入：LeRobot 数据集、TrainConfig 和最大样本数。
- 输出：均值、标准差、分位数 norm stats 与来源证明。
- 一句话作用：让 RM65 训练数据经过与训练相同的输入 transform，再统计 state/actions 的归一化参数并保存哈希证据。

### 为什么要写它

- 原先的问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。
- 采用的解决办法：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **ndarray**：NumPy ndarray：带 shape/dtype 的多维数值数组，用于图像、关节、动作和统计计算。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **dataclass**：数据类：根据字段声明自动生成初始化方法；适合固定配置或结构化记录。
- **argparse**：命令行参数解析：把 `--checkpoint` 等启动选项转换成 `args.checkpoint` 字段。
- **JSON**：JSON：只含通用键值、列表、数字和字符串的文本格式；用于计划、metadata 和报告证据。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-19` `0f92fcd8` **Prepare RM65 data and low-memory pi0.5 training**：针对显存限制补充低内存训练与 RM65 统计量配置。
- `2026-09-29` `a7c7b3d2` **Validate RM65 v3 correction training data**：在训练前验证 v3 修正数据的结构和来源。

### 与上一版教学快照的源码差异

- 当前第 7-7 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`import dataclasses`
- 当前第 43-47 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`parser.add_argument(` / `"--assets-base-dir",` / `type=Path,` / `help="OpenPI assets root that training will use (for example /path/to/openpi/assets).",`
- 当前第 55-59 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`if args.assets_base_dir is not None:` / `config = dataclasses.replace(` / `config,` / `assets_base_dir=str(args.assets_base_dir.expanduser().resolve()),`
- 当前第 98-98 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`"assets_base_dir": str(config.assets_base_dir),`

## 4. 模块地图

- 模块 1｜第 1-27 行：OpenPI 数据加载、归一化组件和 RM65 配置
- 模块 2｜第 28-38 行：去掉不能参与数值统计的 prompt 字符串
- 模块 3｜第 39-73 行：创建与训练一致的数据集和 transform 链
- 模块 4｜第 74-90 行：不打乱数据，逐 batch 更新 state/actions RunningStats
- 模块 5｜第 91-112 行：保存 norm_stats.json、SHA-256 和统计报告

### 函数/类快速索引

- `class RemoveStrings`：第 28-36 行
  - `RemoveStrings.__call__()`：第 31-36 行
- `main()`：第 39-108 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：OpenPI 数据加载、归一化组件和 RM65 配置（源码第 1-27 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：OpenPI 数据加载、归一化组件和 RM65 配置。
- 下游：处理结果继续交给模块 2“去掉不能参与数值统计的 prompt 字符串”。

### 5.B 为什么需要这一组代码

这一组负责“OpenPI 数据加载、归一化组件和 RM65 配置”。它服务于本文件要解决的总问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。 这一组的处理结果会参与：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

### 5.C 本模块主要变量

- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `sys.path.insert(...)`：圆括号表示真正执行调用；把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。

### 5.F 这一模块的版本变化

- 当前第 7-7 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`import dataclasses`

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Compute OpenPI normalization statistics for the RM65 LeRobot dataset.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Compute OpenPI normalization statistics for the RM65 LeRobot dataset."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`dataclasses` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0008】语法拆解：`import` 加载模块；`hashlib` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `hashlib` 引入 `hashlib`。在这份程序里，`hashlib` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import hashlib
# 【L0009】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0010】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0011】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0014】语法拆解：`import` 加载模块；`tqdm` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `tqdm` 引入 `tqdm`。在这份程序里，`tqdm` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import tqdm
# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：`import` 加载模块；`openpi.shared.normalize as normalize` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `openpi` 引入 `openpi.shared.normalize as normalize`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.shared.normalize as normalize
# 【L0017】语法拆解：`import` 加载模块；`openpi.training.data_loader as data_loader` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `openpi` 引入 `openpi.training.data_loader as data_loader`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.training.data_loader as data_loader
# 【L0018】语法拆解：`import` 加载模块；`openpi.transforms as transforms` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `openpi` 引入 `openpi.transforms as transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.transforms as transforms
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0020】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0021】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0022】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0023】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“OpenPI 数据加载、归一化组件和 RM65 配置”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：`from openpi_extension.rm65_training_config` 指定来源模块；`import make_pi05_rm65_lora_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `make_pi05_rm65_lora_config`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0026】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0027】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“OpenPI 数据加载、归一化组件和 RM65 配置”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：去掉不能参与数值统计的 prompt 字符串（源码第 28-38 行）

### 5.A 数据流位置

- 上游：模块 1“OpenPI 数据加载、归一化组件和 RM65 配置”。
- 本模块：去掉不能参与数值统计的 prompt 字符串。
- 下游：处理结果继续交给模块 3“创建与训练一致的数据集和 transform 链”。

### 5.B 为什么需要这一组代码

这一组负责“去掉不能参与数值统计的 prompt 字符串”。它服务于本文件要解决的总问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。 这一组的处理结果会参与：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

### 5.D 本模块首次阅读要认识的调用

- `RemoveStrings(...)`：圆括号表示真正执行调用；创建一个 transform，移除模型张量计算不需要的字符串字段。
- `__call__(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `sample.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.issubdtype(...)`：圆括号表示真正执行调用；判断一个 NumPy dtype 是否属于某类；这里常用于识别浮点图像。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。

### 5.E 本模块定义的新函数

### 函数卡：`RemoveStrings.__call__()`（第 31-36 行）

- 定义了什么：去掉不能参与数值统计的 prompt 字符串。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`sample`：类型 `dict`；项目含义是本功能块中的 `sample` 值
- 返回类型标注：`dict`。
- 函数体实际 return：`{key: value for key, value in sample.items() if not np.issubdtype(np.asarray(value).dtype, np.str_)}`
- 怎样调用：实现 `__call__` 后，`对象(data)` 等价于 `对象.__call__(data)`。


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0028】语法拆解：`class` 定义类 `RemoveStrings`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `RemoveStrings` 类并继承 `transforms.DataTransformFn`；它把“去掉不能参与数值统计的 prompt 字符串”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class RemoveStrings(transforms.DataTransformFn):
# 【L0029】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Drop prompt strings, which are irrelevant to numeric normalization.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Drop prompt strings, which are irrelevant to numeric normalization."""
# 【L0030】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“去掉不能参与数值统计的 prompt 字符串”中的逻辑段，让结构更容易看清。

# 【L0031】语法拆解：`def` 定义函数 `__call__`；第一对圆括号列出形参，逗号负责分隔：`self` 指调用该方法的当前对象；`sample: dict` 用冒号给参数加类型提示；`-> dict` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `__call__(self, sample: dict)`；调用者把参数交给它完成“去掉不能参与数值统计的 prompt 字符串”，后面的缩进代码是具体实现。
    def __call__(self, sample: dict) -> dict:
# 【L0032】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        return {
# 【L0033】语法拆解：`key` 是参数/字段名；冒号 `:` 添加类型提示 `value`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `key`，类型提示为 `value`；在本项目中它表示本功能块中的 `key` 值。
            key: value
# 【L0034】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for key, value in sample.items()` 中给出的序列，逐项完成“去掉不能参与数值统计的 prompt 字符串”。
            for key, value in sample.items()
# 【L0035】语法拆解：`if` 要求条件 `not np.issubdtype(np.asarray(value).dtype, np.str_)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not np.issubdtype(np.asarray(value).dtype, np.str_)` 是否成立；`issubdtype` 表示本功能块中的 `issubdtype` 值；`asarray` 表示本功能块中的 `asarray` 值；`value` 表示本功能块中的 `value` 值
            if not np.issubdtype(np.asarray(value).dtype, np.str_)
# 【L0036】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“去掉不能参与数值统计的 prompt 字符串”。
        }
# 【L0037】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“去掉不能参与数值统计的 prompt 字符串”中的逻辑段，让结构更容易看清。

# 【L0038】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“去掉不能参与数值统计的 prompt 字符串”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“去掉不能参与数值统计的 prompt 字符串”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：创建与训练一致的数据集和 transform 链（源码第 39-73 行）

### 5.A 数据流位置

- 上游：模块 2“去掉不能参与数值统计的 prompt 字符串”。
- 本模块：创建与训练一致的数据集和 transform 链。
- 下游：处理结果继续交给模块 4“不打乱数据，逐 batch 更新 state/actions RunningStats”。

### 5.B 为什么需要这一组代码

这一组负责“创建与训练一致的数据集和 transform 链”。它服务于本文件要解决的总问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。 这一组的处理结果会参与：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

### 5.C 本模块主要变量

- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `output`：输出文件路径。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `data_transforms`：训练和推理共享的 RM65 输入/输出及动作语义变换链。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `data_config`：从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `use(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `make_pi05_rm65_lora_config(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `dataclasses.replace(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `args.assets_base_dir.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `config.data.create(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `data_loader.create_torch_dataset(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `data_loader.TransformedDataset(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 39-108 行）

- 定义了什么：创建与训练一致的数据集和 transform 链。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 当前第 43-47 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`parser.add_argument(` / `"--assets-base-dir",` / `type=Path,` / `help="OpenPI assets root that training will use (for example /path/to/openpi/assets).",`
- 当前第 55-59 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`if args.assets_base_dir is not None:` / `config = dataclasses.replace(` / `config,` / `assets_base_dir=str(args.assets_base_dir.expanduser().resolve()),`

### 5.G 逐行精读

```python
# 【L0039】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“创建与训练一致的数据集和 transform 链”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0041】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--repo-id"`；第 2 个实参 `default="local/rm65_sim_train"`。
# 【项目含义】声明命令行参数 `--repo-id`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0042】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--batch-size"`；第 2 个实参 `type=int`；第 3 个实参 `default=64`。
# 【项目含义】声明命令行参数 `--batch-size`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--batch-size", type=int, default=64)
# 【L0043】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0044】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--assets-base-dir"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“创建与训练一致的数据集和 transform 链”中的帮助说明、错误原因、任务名称或报告文字。
        "--assets-base-dir",
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“创建与训练一致的数据集和 transform 链”。
        type=Path,
# 【L0046】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"OpenPI assets root that training will use (for example /path/to/openpi/assets)."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"OpenPI assets root that training will use (for example /path/to/openpi/assets)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“创建与训练一致的数据集和 transform 链”。
        help="OpenPI assets root that training will use (for example /path/to/openpi/assets).",
# 【L0047】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0048】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--output"`；第 2 个实参 `type=Path`。
# 【项目含义】声明命令行参数 `--output`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--output", type=Path)
# 【L0049】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0050】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“创建与训练一致的数据集和 transform 链”中的逻辑段，让结构更容易看清。

# 【L0051】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config`。右侧语法为：`make_pi05_rm65_lora_config(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建训练与推理共用的 RM65 π0.5/LoRA、数据 transform 和基础权重配置。
    config = make_pi05_rm65_lora_config(
# 【L0052】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `args.repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“创建与训练一致的数据集和 transform 链”。
        repo_id=args.repo_id,
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `batch_size`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`batch_size`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `batch_size` 传入 `args.batch_size`；该参数在本项目中表示本功能块中的 `batch_size` 值，会参与“创建与训练一致的数据集和 transform 链”。
        batch_size=args.batch_size,
# 【L0054】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0055】语法拆解：`if` 要求条件 `args.assets_base_dir is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.assets_base_dir is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.assets_base_dir is not None:
# 【L0056】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config`。右侧语法为：`dataclasses.replace(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `dataclasses.replace(`；`dataclasses` 表示本功能块中的 `dataclasses` 值；`replace` 表示本功能块中的 `replace` 值。
        config = dataclasses.replace(
# 【L0057】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`config` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `config`；在本项目中它表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
            config,
# 【L0058】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `assets_base_dir`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.assets_base_dir.expanduser().resolve()`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `assets_base_dir` 传入 `str(args.assets_base_dir.expanduser().resolve())`；该参数在本项目中表示本功能块中的 `assets_base_dir` 值，会参与“创建与训练一致的数据集和 transform 链”。
            assets_base_dir=str(args.assets_base_dir.expanduser().resolve()),
# 【L0059】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
        )
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_config`。右侧语法为：`config.data` 是模块/对象，点号 `.` 从中取出 `create` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `config.assets_dirs`；第 2 个实参 `config.model`。
# 【项目含义】得到 `data_config`，它在本项目中表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `config.data.create(config.assets_dirs, config.model)`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`create` 表示本功能块中的 `create` 值。
    data_config = config.data.create(config.assets_dirs, config.model)
# 【L0061】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset`。右侧语法为：`data_loader.create_torch_dataset(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.create_torch_dataset(`；`data_loader` 表示本功能块中的 `data_loader` 值；`create_torch_dataset` 表示数据集相关值。
    dataset = data_loader.create_torch_dataset(
# 【L0062】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`data_config` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `data_config`；在本项目中它表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
        data_config,
# 【L0063】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model` → `action_horizon`。
# 【项目含义】向上一行的函数调用或容器继续传入 `config.model.action_horizon`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`model` 表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置；`action_horizon` 表示动作相关值，它参与“创建与训练一致的数据集和 transform 链”。
        config.model.action_horizon,
# 【L0064】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model`。
# 【项目含义】向上一行的函数调用或容器继续传入 `config.model`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`model` 表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置，它参与“创建与训练一致的数据集和 transform 链”。
        config.model,
# 【L0065】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0066】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dataset`。右侧语法为：`data_loader.TransformedDataset(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.TransformedDataset(`；`data_loader` 表示本功能块中的 `data_loader` 值；`TransformedDataset` 表示本功能块中的 `TransformedDataset` 值。
    dataset = data_loader.TransformedDataset(
# 【L0067】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`dataset` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `dataset`；在本项目中它表示LeRobotDataset 对象，用于逐帧构造训练集。
        dataset,
# 【L0068】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“创建与训练一致的数据集和 transform 链”。
        [
# 【L0069】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*data_config.repack_transforms.inputs` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*data_config.repack_transforms.inputs,` 接到上一行未结束的数学公式；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；`repack_transforms` 表示本功能块中的 `repack_transforms` 值；`inputs` 表示本功能块中的 `inputs` 值，整条公式用于“创建与训练一致的数据集和 transform 链”。
            *data_config.repack_transforms.inputs,
# 【L0070】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*data_config.data_transforms.inputs` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*data_config.data_transforms.inputs,` 接到上一行未结束的数学公式；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；`data_transforms` 表示训练和推理共享的 RM65 输入/输出及动作语义变换链；`inputs` 表示本功能块中的 `inputs` 值，整条公式用于“创建与训练一致的数据集和 transform 链”。
            *data_config.data_transforms.inputs,
# 【L0071】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`RemoveStrings` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】调用 `RemoveStrings()`：创建一个 transform，移除模型张量计算不需要的字符串字段。它的结果/修改用于“创建与训练一致的数据集和 transform 链”。
            RemoveStrings(),
# 【L0072】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
        ],
# 【L0073】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“创建与训练一致的数据集和 transform 链”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：不打乱数据，逐 batch 更新 state/actions RunningStats（源码第 74-90 行）

### 5.A 数据流位置

- 上游：模块 3“创建与训练一致的数据集和 transform 链”。
- 本模块：不打乱数据，逐 batch 更新 state/actions RunningStats。
- 下游：处理结果继续交给模块 5“保存 norm_stats.json、SHA-256 和统计报告”。

### 5.B 为什么需要这一组代码

这一组负责“不打乱数据，逐 batch 更新 state/actions RunningStats”。它服务于本文件要解决的总问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。 这一组的处理结果会参与：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `data_config`：从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
- `running`：分别为 state 和 actions 在线累计均值、方差与分位数的 RunningStats。
- `norm_stats`：最终得到的 state/actions 归一化统计。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `data_loader.TorchDataLoader(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `normalize.RunningStats(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `tqdm.tqdm(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `running.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `stats.update(...)`：圆括号表示真正执行调用；用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `stats.get_statistics(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `normalize.save(...)`：圆括号表示真正执行调用；保存当前数据对象，供训练、验证或之后恢复。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0074】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_batches`。右侧语法为：表达式 `len(dataset) // args.batch_size` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `num_batches`，它在本项目中表示本功能块中的 `num_batches` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(dataset) // args.batch_size`；`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`batch_size` 表示本功能块中的 `batch_size` 值。
    num_batches = len(dataset) // args.batch_size
# 【L0075】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `loader`。右侧语法为：`data_loader.TorchDataLoader(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `loader`，它在本项目中表示本功能块中的 `loader` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.TorchDataLoader(`；`data_loader` 表示本功能块中的 `data_loader` 值；`TorchDataLoader` 表示本功能块中的 `TorchDataLoader` 值。
    loader = data_loader.TorchDataLoader(
# 【L0076】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`dataset` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `dataset`；在本项目中它表示LeRobotDataset 对象，用于逐帧构造训练集。
        dataset,
# 【L0077】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_batch_size`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`batch_size`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `local_batch_size` 传入 `args.batch_size`；该参数在本项目中表示本功能块中的 `local_batch_size` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        local_batch_size=args.batch_size,
# 【L0078】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_workers`。右侧语法为：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`num_workers`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `num_workers` 传入 `config.num_workers`；该参数在本项目中表示本功能块中的 `num_workers` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_workers=config.num_workers,
# 【L0079】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `shuffle`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `shuffle` 传入 `False`；该参数在本项目中表示本功能块中的 `shuffle` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        shuffle=False,
# 【L0080】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_batches`。右侧语法为：`num_batches` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `num_batches` 传入 `num_batches`；该参数在本项目中表示本功能块中的 `num_batches` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_batches=num_batches,
# 【L0081】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    )
# 【L0082】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0083】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `running`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `running`，它在本项目中表示分别为 state 和 actions 在线累计均值、方差与分位数的 RunningStats；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：送入 π0.5 的七维机器人状态：六个 RM65 关节角加一个夹爪状态。
    running = {key: normalize.RunningStats() for key in ("state", "actions")}
# 【L0084】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats")`，每次把当前元素放进 `batch`；这会逐个处理“不打乱数据，逐 batch 更新 state/actions RunningStats”所需的帧、episode、动作或实验 case。
    for batch in tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats"):
# 【L0085】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `running.items()`，每次把当前元素放进 `key, stats`；这会逐个处理“不打乱数据，逐 batch 更新 state/actions RunningStats”所需的帧、episode、动作或实验 case。
        for key, stats in running.items():
# 【L0086】语法拆解：`stats` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.asarray(batch[key])`。
# 【项目含义】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `stats.update(np.asarray(batch[key]))`。`stats` 表示本功能块中的 `stats` 值；`update` 表示本功能块中的 `update` 值。
            stats.update(np.asarray(batch[key]))
# 【L0087】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0088】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `norm_stats`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `norm_stats`，它在本项目中表示最终得到的 state/actions 归一化统计；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{key: stats.get_statistics() for key, stats in running.items()}`；`key` 表示本功能块中的 `key` 值；`stats` 表示本功能块中的 `stats` 值；`get_statistics` 表示本功能块中的 `get_statistics` 值。
    norm_stats = {key: stats.get_statistics() for key, stats in running.items()}
# 【L0089】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_dir`。右侧语法为：表达式 `config.assets_dirs / data_config.repo_id` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `output_dir`，它在本项目中表示输出相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `config.assets_dirs / data_config.repo_id`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`assets_dirs` 表示本功能块中的 `assets_dirs` 值；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
    output_dir = config.assets_dirs / data_config.repo_id
# 【L0090】语法拆解：`normalize` 是模块/对象，点号 `.` 从中取出 `save` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `output_dir`；第 2 个实参 `norm_stats`。
# 【项目含义】对 `normalize` 调用 `save(output_dir, norm_stats)`：保存当前数据对象，供训练、验证或之后恢复。本行产生的修改/返回值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    normalize.save(output_dir, norm_stats)
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“不打乱数据，逐 batch 更新 state/actions RunningStats”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：保存 norm_stats.json、SHA-256 和统计报告（源码第 91-112 行）

### 5.A 数据流位置

- 上游：模块 4“不打乱数据，逐 batch 更新 state/actions RunningStats”。
- 本模块：保存 norm_stats.json、SHA-256 和统计报告。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“保存 norm_stats.json、SHA-256 和统计报告”。它服务于本文件要解决的总问题：沿用 DROID/Franka 统计量会把 RM65 数值缩放到错误分布，模型即使训练也会接收失真的状态和动作。 这一组的处理结果会参与：复用训练完全相同的 repack/delta transform，逐样本累计统计并写入 checkpoint assets。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `output`：输出文件路径。
- `norm_stats`：最终得到的 state/actions 归一化统计。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `hashlib.sha256(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `stats_path.read_bytes(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `hexdigest(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sorted(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `args.output.parent.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `args.output.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 当前第 98-98 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`"assets_base_dir": str(config.assets_base_dir),`

### 5.G 逐行精读

```python
# 【L0091】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stats_path`。右侧语法为：表达式 `output_dir / "norm_stats.json"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `stats_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `output_dir / "norm_stats.json"`；`output_dir` 表示输出相关值；`norm_stats` 表示最终得到的 state/actions 归一化统计；`json` 表示本功能块中的 `json` 值。
    stats_path = output_dir / "norm_stats.json"
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0093】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0094】语法拆解：这是字典键值对：`"repo_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】定义字典/JSON 字段 `repo_id`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0095】语法拆解：这是字典键值对：`"dataset_frames"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `dataset`。
# 【项目含义】定义字典/JSON 字段 `dataset_frames`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `dataset_frames` 数据；字段值来自 `len(dataset)`，因此保存/传递的是这个表达式当前计算出的结果。
        "dataset_frames": len(dataset),
# 【L0096】语法拆解：这是字典键值对：`"processed_frames"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `num_batches * args.batch_size` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `processed_frames`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `processed_frames` 数据；字段值来自 `num_batches * args.batch_size`，因此保存/传递的是这个表达式当前计算出的结果。
        "processed_frames": num_batches * args.batch_size,
# 【L0097】语法拆解：这是字典键值对：`"batch_size"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`batch_size`。
# 【项目含义】定义字典/JSON 字段 `batch_size`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `batch_size` 数据；字段值来自 `args.batch_size`，因此保存/传递的是这个表达式当前计算出的结果。
        "batch_size": args.batch_size,
# 【L0098】语法拆解：这是字典键值对：`"assets_base_dir"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `config.assets_base_dir`。
# 【项目含义】定义字典/JSON 字段 `assets_base_dir`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `assets_base_dir` 数据；字段值来自 `str(config.assets_base_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
        "assets_base_dir": str(config.assets_base_dir),
# 【L0099】语法拆解：这是字典键值对：`"output_path"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `stats_path`。
# 【项目含义】定义字典/JSON 字段 `output_path`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `output_path` 数据；字段值来自 `str(stats_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "output_path": str(stats_path),
# 【L0100】语法拆解：这是字典键值对：`"sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`hashlib` 是模块/对象，点号 `.` 从中取出 `sha256` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `stats_path.read_bytes()).hexdigest(`。
# 【项目含义】定义字典/JSON 字段 `sha256`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `sha256` 数据；字段值来自 `hashlib.sha256(stats_path.read_bytes()).hexdigest()`，因此保存/传递的是这个表达式当前计算出的结果。
        "sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
# 【L0101】语法拆解：这是字典键值对：`"keys"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`sorted` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `norm_stats`。
# 【项目含义】定义字典/JSON 字段 `keys`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `keys` 数据；字段值来自 `sorted(norm_stats)`，因此保存/传递的是这个表达式当前计算出的结果。
        "keys": sorted(norm_stats),
# 【L0102】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 norm_stats.json、SHA-256 和统计报告”。
    }
# 【L0103】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `text`。右侧语法为：表达式 `json.dumps(report, indent=2) + "\n"` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `text`，它在本项目中表示本功能块中的 `text` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 Python 字典序列化为 JSON 文本，供日志、报告或下游程序读取。
    text = json.dumps(report, indent=2) + "\n"
# 【L0104】语法拆解：`if` 要求条件 `args.output is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.output is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.output is not None:
# 【L0105】语法拆解：`args.output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0106】语法拆解：`args.output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `args.output.write_text(text, encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        args.output.write_text(text, encoding="utf-8")
# 【L0107】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `end=""`。
# 【项目含义】把 `text, end=""` 的当前值/文字输出到终端；它用于观察“保存 norm_stats.json、SHA-256 和统计报告”进度，也给日志留下可搜索证据。
    print(text, end="")
# 【L0108】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0109】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0110】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0111】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0112】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“保存 norm_stats.json、SHA-256 和统计报告”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“保存 norm_stats.json、SHA-256 和统计报告”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。