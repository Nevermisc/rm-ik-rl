# `expert_episode.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/expert_episode.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`a2223a61169c0a1e22a66ab3d760a42c39110532fc2ff01e6f63bf058c150b1f`
- 总行数：254

## 1. 先把这个程序放进整个项目

- 所处阶段：数据采集：定义一条 RM65 专家轨迹在内存和磁盘中的合同。
- 输入：每个采样时刻的关节、夹爪、动作、方块位姿、阶段和两路 RGB。
- 输出：压缩 NPZ、逐帧 PNG、metadata JSON 以及可独立复核的验证结果。
- 一句话作用：定义 RM65 专家轨迹的中间格式；确保每帧观测与同索引动作严格同步，并负责保存和校验。

### 为什么要写它

- 原先的问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。
- 采用的解决办法：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **ndarray**：NumPy ndarray：带 shape/dtype 的多维数值数组，用于图像、关节、动作和统计计算。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **dataclass**：数据类：根据字段声明自动生成初始化方法；适合固定配置或结构化记录。
- **JSON**：JSON：只含通用键值、列表、数字和字符串的文本格式；用于计划、metadata 和报告证据。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-17` `c6a87c23` **Add RM65 expert episode data pipeline**：建立同步记录、保存和验证专家 episode 的数据合同。

### 与上一版教学快照的源码差异

- 当前源码与上一版教学快照一致。

## 4. 模块地图

- 模块 1｜第 1-22 行：格式常量与夹爪归一化
- 模块 2｜第 23-53 行：EpisodeRecorder 的字段与初始化校验
- 模块 3｜第 54-122 行：校验并追加一帧状态、动作、物体姿态和图像
- 模块 4｜第 123-131 行：RGB 图像格式校验
- 模块 5｜第 132-175 行：保存 episode.npz 和 metadata.json
- 模块 6｜第 176-254 行：重新读取磁盘数据并做独立完整性校验

### 函数/类快速索引

- `normalize_gripper()`：第 17-20 行
- `class EpisodeRecorder`：第 24-173 行
  - `EpisodeRecorder.__post_init__()`：第 47-52 行
  - `EpisodeRecorder.add_frame()`：第 54-121 行
  - `EpisodeRecorder._validate_image()`：第 124-130 行
  - `EpisodeRecorder.save()`：第 132-173 行
- `validate_episode()`：第 176-254 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：格式常量与夹爪归一化（源码第 1-22 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：格式常量与夹爪归一化。
- 下游：处理结果继续交给模块 2“EpisodeRecorder 的字段与初始化校验”。

### 5.B 为什么需要这一组代码

这一组负责“格式常量与夹爪归一化”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.C 本模块主要变量

- `gripper`：一个归一化夹爪值组成的一维数组。

### 5.D 本模块首次阅读要认识的调用

- `normalize_gripper(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `np.clip(...)`：圆括号表示真正执行调用；把数值限制在给定上下界内。

### 5.E 本模块定义的新函数

### 函数卡：`normalize_gripper()`（第 17-20 行）

- 定义了什么：格式常量与夹爪归一化。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`position_rad`：类型 `float`；项目含义是位置相关值；`closed_position_rad`：类型 `float`，默认 `0.865`；项目含义是位置相关值
- 返回类型标注：`float`。
- 函数体实际 return：`float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))`
- 项目中的实际调用位置：`run_pick_place_baseline.py:983` 的 `final_gripper = normalize_gripper(`；`run_pick_place_baseline.py:602` 的 `observed_gripper = normalize_gripper(`；`run_pick_place_baseline.py:606` 的 `target_gripper = normalize_gripper(`；`run_pick_place_baseline.py:910` 的 `actual_gripper_normalized = normalize_gripper(`；`run_pick_place_baseline.py:768` 的 `[normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0001】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Portable intermediate format for RM65 expert demonstration episodes.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Portable intermediate format for RM65 expert demonstration episodes."""
# 【L0002】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0003】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0005】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0006】语法拆解：`from dataclasses` 指定来源模块；`import dataclass, field` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `dataclasses` 引入 `dataclass, field`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
from dataclasses import dataclass, field
# 【L0007】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0008】语法拆解：`from typing` 指定来源模块；`import Any` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0009】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0010】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0011】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `FORMAT_NAME`。右侧语法为：`"rm65_expert_episode_v1"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `FORMAT_NAME`，它在本项目中表示本功能块中的 `FORMAT_NAME` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"rm65_expert_episode_v1"`；`rm65_expert_episode_v1` 表示一条轨迹相关值。
FORMAT_NAME = "rm65_expert_episode_v1"
# 【L0014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `JOINT_NAMES`。右侧语法为：`tuple` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"joint_{index}" for index in range(1, 7)`。
# 【项目含义】得到 `JOINT_NAMES`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tuple(f"joint_{index}" for index in range(1, 7))`；`f` 表示本功能块中的 `f` 值；`joint_` 表示关节相关值；`index` 表示索引相关值。
JOINT_NAMES = tuple(f"joint_{index}" for index in range(1, 7))
# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0017】语法拆解：`def` 定义函数 `normalize_gripper`；第一对圆括号列出形参，逗号负责分隔：`position_rad: float` 用冒号给参数加类型提示；`closed_position_rad: float = 0.865` 用冒号给参数加类型提示；`-> float` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `normalize_gripper(position_rad: float, closed_position_rad: float = 0.865)`；调用者把参数交给它完成“格式常量与夹爪归一化”，后面的缩进代码是具体实现。
def normalize_gripper(position_rad: float, closed_position_rad: float = 0.865) -> float:
# 【L0018】语法拆解：`if` 要求条件 `closed_position_rad <= 0.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `closed_position_rad <= 0.0` 是否成立；`closed_position_rad` 表示位置相关值
    if closed_position_rad <= 0.0:
# 【L0019】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("closed gripper position must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("closed gripper position must be positive")` 并停止当前路径；说明当前输入违反“格式常量与夹爪归一化”要求，不能继续进入仿真、训练或评测。
        raise ValueError("closed gripper position must be positive")
# 【L0020】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.clip(position_rad / closed_position_rad, 0.0, 1.0)`。
# 【项目含义】结束当前函数并把 `float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))` 交回调用者；这个值的含义是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    return float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))
# 【L0021】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0022】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“格式常量与夹爪归一化”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：EpisodeRecorder 的字段与初始化校验（源码第 23-53 行）

### 5.A 数据流位置

- 上游：模块 1“格式常量与夹爪归一化”。
- 本模块：EpisodeRecorder 的字段与初始化校验。
- 下游：处理结果继续交给模块 3“校验并追加一帧状态、动作、物体姿态和图像”。

### 5.B 为什么需要这一组代码

这一组负责“EpisodeRecorder 的字段与初始化校验”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。

### 5.D 本模块首次阅读要认识的调用

- `field(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `__post_init__(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `self.prompt.strip(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `np.isfinite(...)`：圆括号表示真正执行调用；检查是否存在 NaN 或正负无穷。

### 5.E 本模块定义的新函数

### 函数卡：`EpisodeRecorder.__post_init__()`（第 47-52 行）

- 定义了什么：EpisodeRecorder 的字段与初始化校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的调用：本文件内没有直接调用；它是脚本入口、回调，或由其他环境/框架按接口调用。


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0023】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclass
# 【L0024】语法拆解：`class` 定义类 `EpisodeRecorder`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `EpisodeRecorder` 类并继承 `object`；它把“EpisodeRecorder 的字段与初始化校验”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class EpisodeRecorder:
# 【L0025】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Accumulate synchronized state/action frames and save one episode.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Accumulate synchronized state/action frames and save one episode.
# 【L0026】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0027】语法拆解：`Each frame represents the observation immediately before applying the` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `Each frame represents the observation immediately before applying the`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    Each frame represents the observation immediately before applying the
# 【L0028】语法拆解：`action target stored at the same index. Images are optional while bringing` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `action target stored at the same index. Images are optional while bringing`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    action target stored at the same index. Images are optional while bringing
# 【L0029】语法拆解：表达式 `up the low-dimensional recorder, but production training episodes require` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `up the low-dimensional recorder, but production training episodes require`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    up the low-dimensional recorder, but production training episodes require
# 【L0030】语法拆解：`both external and wrist RGB streams.` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `both external and wrist RGB streams.`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    both external and wrist RGB streams.
# 【L0031】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0032】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0033】语法拆解：`output_dir` 是参数/字段名；冒号 `:` 添加类型提示 `Path`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `output_dir`，类型提示为 `Path`；在本项目中它表示输出相关值。
    output_dir: Path
# 【L0034】语法拆解：`prompt` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `prompt`，类型提示为 `str`；在本项目中它表示本功能块中的 `prompt` 值。
    prompt: str
# 【L0035】语法拆解：`control_hz` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `control_hz`，类型提示为 `float`；在本项目中它表示本功能块中的 `control_hz` 值。
    control_hz: float
# 【L0036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata: dict[str, Any]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=dict`。
# 【项目含义】把右侧结果写进 `metadata: dict[str, Any]`（写入 `metadata: dict[str, Any]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=dict)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值。
    metadata: dict[str, Any] = field(default_factory=dict)
# 【L0037】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_timestamps: list[float]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_timestamps: list[float]`（写入 `_timestamps: list[float]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _timestamps: list[float] = field(default_factory=list, init=False)
# 【L0038】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_sim_steps: list[int]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_sim_steps: list[int]`（写入 `_sim_steps: list[int]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _sim_steps: list[int] = field(default_factory=list, init=False)
# 【L0039】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_states: list[np.ndarray]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_states: list[np.ndarray]`（写入 `_states: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _states: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_actions: list[np.ndarray]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_actions: list[np.ndarray]`（写入 `_actions: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _actions: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_cube_poses: list[np.ndarray]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_cube_poses: list[np.ndarray]`（写入 `_cube_poses: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _cube_poses: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0042】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_phases: list[str]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_phases: list[str]`（写入 `_phases: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _phases: list[str] = field(default_factory=list, init=False)
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_external_paths: list[str]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_external_paths: list[str]`（写入 `_external_paths: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _external_paths: list[str] = field(default_factory=list, init=False)
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_wrist_paths: list[str]`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default_factory=list`；第 2 个实参 `init=False`。
# 【项目含义】把右侧结果写进 `_wrist_paths: list[str]`（写入 `_wrist_paths: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _wrist_paths: list[str] = field(default_factory=list, init=False)
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_images_enabled: bool | None`。右侧语法为：`field` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `default=None`；第 2 个实参 `init=False`。
# 【项目含义】得到 `_images_enabled`，它在本项目中表示本功能块中的 `_images_enabled` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `field(default=None, init=False)`；`field` 表示本功能块中的 `field` 值；`default` 表示本功能块中的 `default` 值；`init` 表示本功能块中的 `init` 值。
    _images_enabled: bool | None = field(default=None, init=False)
# 【L0046】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0047】语法拆解：`def` 定义函数 `__post_init__`；第一对圆括号列出形参，逗号负责分隔：`self` 指调用该方法的当前对象；`-> None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `__post_init__(self)`；调用者把参数交给它完成“EpisodeRecorder 的字段与初始化校验”，后面的缩进代码是具体实现。
    def __post_init__(self) -> None:
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.output_dir`。右侧语法为：`Path` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self.output_dir`。
# 【项目含义】把 `self` 对象的 `output_dir` 配置成 `Path(self.output_dir)`。`self` 在这里表示当前类实例；这个设置会影响“EpisodeRecorder 的字段与初始化校验”。
        self.output_dir = Path(self.output_dir)
# 【L0049】语法拆解：`if` 要求条件 `not self.prompt.strip()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not self.prompt.strip()` 是否成立；`prompt` 表示本功能块中的 `prompt` 值；`strip` 表示本功能块中的 `strip` 值
        if not self.prompt.strip():
# 【L0050】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("episode prompt must not be empty")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("episode prompt must not be empty")` 并停止当前路径；说明当前输入违反“EpisodeRecorder 的字段与初始化校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError("episode prompt must not be empty")
# 【L0051】语法拆解：`if` 要求条件 `not np.isfinite(self.control_hz) or self.control_hz <= 0.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
        if not np.isfinite(self.control_hz) or self.control_hz <= 0.0:
# 【L0052】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("control_hz must be positive and finite")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("control_hz must be positive and finite")` 并停止当前路径；说明当前输入违反“EpisodeRecorder 的字段与初始化校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError("control_hz must be positive and finite")
# 【L0053】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“EpisodeRecorder 的字段与初始化校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：校验并追加一帧状态、动作、物体姿态和图像（源码第 54-122 行）

### 5.A 数据流位置

- 上游：模块 2“EpisodeRecorder 的字段与初始化校验”。
- 本模块：校验并追加一帧状态、动作、物体姿态和图像。
- 下游：处理结果继续交给模块 4“RGB 图像格式校验”。

### 5.B 为什么需要这一组代码

这一组负责“校验并追加一帧状态、动作、物体姿态和图像”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.C 本模块主要变量

- `external_rgb`：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
- `wrist_rgb`：随末端移动的腕部相机 RGB 图像。
- `joints`：六个 RM65 关节位置的一维 NumPy 数组。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `action_array`：强制为 float32 后的一帧七维专家动作。

### 5.D 本模块首次阅读要认识的调用

- `add_frame(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `phase.strip(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.concatenate(...)`：圆括号表示真正执行调用；沿一个轴首尾拼接数组。
- `np.isfinite(...)`：圆括号表示真正执行调用；检查是否存在 NaN 或正负无穷。
- `all(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `self._validate_image(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `path.parent.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `Image.fromarray(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `save(...)`：圆括号表示真正执行调用；保存当前数据对象，供训练、验证或之后恢复。
- `self._timestamps.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。

### 5.E 本模块定义的新函数

### 函数卡：`EpisodeRecorder.add_frame()`（第 54-121 行）

- 定义了什么：校验并追加一帧状态、动作、物体姿态和图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`timestamp_s`（仅关键字）：类型 `float`；项目含义是本功能块中的 `timestamp_s` 值；`sim_step`（仅关键字）：类型 `int`；项目含义是仿真、步相关值；`phase`（仅关键字）：类型 `str`；项目含义是本功能块中的 `phase` 值；`joint_position_rad`（仅关键字）：类型 `np.ndarray`；项目含义是关节、位置相关值；`gripper_position`（仅关键字）：类型 `float`；项目含义是夹爪、位置相关值；`action`（仅关键字）：类型 `np.ndarray`；项目含义是动作相关值；`cube_pose_wxyz`（仅关键字）：类型 `np.ndarray`；项目含义是任务方块相关值；`external_rgb`（仅关键字）：类型 `np.ndarray | None`，默认 `None`；项目含义是外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb`（仅关键字）：类型 `np.ndarray | None`，默认 `None`；项目含义是随末端移动的腕部相机 RGB 图像
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:617` 的 `self.recorder.add_frame(`；`convert_expert_episodes_to_lerobot.py:274` 的 `dataset.add_frame(`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0054】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `add_frame(参数在后续行继续)`；调用者把参数交给它完成“校验并追加一帧状态、动作、物体姿态和图像”，后面的缩进代码是具体实现。
    def add_frame(
# 【L0055】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`self` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0056】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“校验并追加一帧状态、动作、物体姿态和图像”。
        *,
# 【L0057】语法拆解：`timestamp_s` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `timestamp_s`，类型提示为 `float`；在本项目中它表示本功能块中的 `timestamp_s` 值。
        timestamp_s: float,
# 【L0058】语法拆解：`sim_step` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `sim_step`，类型提示为 `int`；在本项目中它表示仿真、步相关值。
        sim_step: int,
# 【L0059】语法拆解：`phase` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
        phase: str,
# 【L0060】语法拆解：`joint_position_rad` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `joint_position_rad`，类型提示为 `np.ndarray`；在本项目中它表示关节、位置相关值。
        joint_position_rad: np.ndarray,
# 【L0061】语法拆解：`gripper_position` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `gripper_position`，类型提示为 `float`；在本项目中它表示夹爪、位置相关值。
        gripper_position: float,
# 【L0062】语法拆解：`action` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `action`，类型提示为 `np.ndarray`；在本项目中它表示动作相关值。
        action: np.ndarray,
# 【L0063】语法拆解：`cube_pose_wxyz` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `cube_pose_wxyz`，类型提示为 `np.ndarray`；在本项目中它表示任务方块相关值。
        cube_pose_wxyz: np.ndarray,
# 【L0064】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb: np.ndarray | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        external_rgb: np.ndarray | None = None,
# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_rgb: np.ndarray | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_rgb: np.ndarray | None = None,
# 【L0066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“校验并追加一帧状态、动作、物体姿态和图像”。
    ) -> None:
# 【L0067】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joints`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `joint_position_rad`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `joints`，它在本项目中表示六个 RM65 关节位置的一维 NumPy 数组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `joint_position_rad, dtype=np.float32`（关节、位置相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        joints = np.asarray(joint_position_rad, dtype=np.float32)
# 【L0068】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_array`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `action`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `action_array`，它在本项目中表示强制为 float32 后的一帧七维专家动作；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `action, dtype=np.float32`（本功能块中的 `action, dtype=np.float32` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        action_array = np.asarray(action, dtype=np.float32)
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube_pose_wxyz`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `cube_pose_wxyz, dtype=np.float32`（任务方块相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        cube_pose = np.asarray(cube_pose_wxyz, dtype=np.float32)
# 【L0070】语法拆解：`if` 要求条件 `joints.shape != (6,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `joints.shape` 是否不等于要求的 `(6,)`；若不等，数据维度合同已被破坏，进入错误处理
        if joints.shape != (6,):
# 【L0071】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected six joint positions, got {joints.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected six joint positions, got {joints.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected six joint positions, got {joints.shape}")
# 【L0072】语法拆解：`if` 要求条件 `action_array.shape != (7,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `action_array.shape` 是否不等于要求的 `(7,)`；若不等，数据维度合同已被破坏，进入错误处理
        if action_array.shape != (7,):
# 【L0073】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected seven action values, got {action_array.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected seven action values, got {action_array.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected seven action values, got {action_array.shape}")
# 【L0074】语法拆解：`if` 要求条件 `cube_pose.shape != (7,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `cube_pose.shape` 是否不等于要求的 `(7,)`；若不等，数据维度合同已被破坏，进入错误处理
        if cube_pose.shape != (7,):
# 【L0075】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")
# 【L0076】语法拆解：`if` 要求条件 `not phase.strip()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not phase.strip()` 是否成立；`phase` 表示本功能块中的 `phase` 值；`strip` 表示本功能块中的 `strip` 值
        if not phase.strip():
# 【L0077】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("phase must not be empty")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("phase must not be empty")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("phase must not be empty")
# 【L0078】语法拆解：`if` 要求条件 `sim_step < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `sim_step < 0` 是否成立；`sim_step` 表示仿真、步相关值
        if sim_step < 0:
# 【L0079】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("sim_step must be non-negative")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("sim_step must be non-negative")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("sim_step must be non-negative")
# 【L0080】语法拆解：`if` 要求条件 `not 0.0 <= gripper_position <= 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= gripper_position <= 1.0` 是否成立；`gripper_position` 表示夹爪、位置相关值
        if not 0.0 <= gripper_position <= 1.0:
# 【L0081】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("normalized gripper position must be in [0, 1]")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("normalized gripper position must be in [0, 1]")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("normalized gripper position must be in [0, 1]")
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `numeric`。右侧语法为：`np.concatenate(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `numeric`，它在本项目中表示本功能块中的 `numeric` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把括号中的多个一维数组沿现有轴首尾连接；在本项目中常用于把六关节和一个夹爪值组成七维状态/动作。
        numeric = np.concatenate(
# 【L0083】语法拆解：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[joints, [gripper_position], action_array, cube_pose, [timestamp_s]]`；`joints` 表示六个 RM65 关节位置的一维 NumPy 数组；`gripper_position` 表示夹爪、位置相关值；`action_array` 表示强制为 float32 后的一帧七维专家动作，共同完成“校验并追加一帧状态、动作、物体姿态和图像”。
            [joints, [gripper_position], action_array, cube_pose, [timestamp_s]]
# 【L0084】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“校验并追加一帧状态、动作、物体姿态和图像”。
        )
# 【L0085】语法拆解：`if` 要求条件 `not np.isfinite(numeric).all()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
        if not np.isfinite(numeric).all():
# 【L0086】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("episode frames must contain only finite numeric values")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("episode frames must contain only finite numeric values")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("episode frames must contain only finite numeric values")
# 【L0087】语法拆解：`if` 要求条件 `self._timestamps and timestamp_s <= self._timestamps[-1]` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `self._timestamps and timestamp_s <= self._timestamps[-1]` 是否成立；`_timestamps` 表示本功能块中的 `_timestamps` 值；`timestamp_s` 表示本功能块中的 `timestamp_s` 值
        if self._timestamps and timestamp_s <= self._timestamps[-1]:
# 【L0088】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("timestamps must be strictly increasing")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("timestamps must be strictly increasing")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("timestamps must be strictly increasing")
# 【L0089】语法拆解：`if` 要求条件 `self._sim_steps and sim_step <= self._sim_steps[-1]` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `self._sim_steps and sim_step <= self._sim_steps[-1]` 是否成立；`_sim_steps` 表示仿真、步数相关值；`sim_step` 表示仿真、步相关值
        if self._sim_steps and sim_step <= self._sim_steps[-1]:
# 【L0090】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("simulation steps must be strictly increasing")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("simulation steps must be strictly increasing")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("simulation steps must be strictly increasing")
# 【L0091】语法拆解：`if` 要求条件 `(external_rgb is None) != (wrist_rgb is None)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `(external_rgb is None) != (wrist_rgb is None)`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if (external_rgb is None) != (wrist_rgb is None):
# 【L0092】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("external and wrist images must be supplied together")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("external and wrist images must be supplied together")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("external and wrist images must be supplied together")
# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `frame_has_images`。右侧语法为：`external_rgb is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `frame_has_images`，它在本项目中表示帧相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `external_rgb is not None`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
        frame_has_images = external_rgb is not None
# 【L0094】语法拆解：`if` 要求条件 `self._images_enabled is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `self._images_enabled is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self._images_enabled is None:
# 【L0095】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self._images_enabled`。右侧语法为：`frame_has_images` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `_images_enabled` 配置成 `frame_has_images`。`self` 在这里表示当前类实例；这个设置会影响“校验并追加一帧状态、动作、物体姿态和图像”。
            self._images_enabled = frame_has_images
# 【L0096】语法拆解：`elif` 要求条件 `self._images_enabled != frame_has_images` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】前面的条件未成立时，继续判断 `self._images_enabled != frame_has_images` 是否成立；`_images_enabled` 表示本功能块中的 `_images_enabled` 值；`frame_has_images` 表示帧相关值
        elif self._images_enabled != frame_has_images:
# 【L0097】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("all frames in an episode must use the same image streams")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("all frames in an episode must use the same image streams")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("all frames in an episode must use the same image streams")
# 【L0098】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0099】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `frame_index`。右侧语法为：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._states`。
# 【项目含义】得到 `frame_index`，它在本项目中表示帧、索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(self._states)`；`_states` 表示本功能块中的 `_states` 值。
        frame_index = len(self._states)
# 【L0100】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_path`。右侧语法为：`""` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `external_path`，它在本项目中表示外部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `""` 的结果保存下来，供当前功能块后续使用。
        external_path = ""
# 【L0101】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_path`。右侧语法为：`""` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `wrist_path`，它在本项目中表示腕部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `""` 的结果保存下来，供当前功能块后续使用。
        wrist_path = ""
# 【L0102】语法拆解：`if` 要求条件 `external_rgb is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `external_rgb is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if external_rgb is not None:
# 【L0103】语法拆解：`from PIL` 指定来源模块；`import Image` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
            from PIL import Image
# 【L0104】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0105】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external`。右侧语法为：`self` 是模块/对象，点号 `.` 从中取出 `_validate_image` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_rgb`；第 2 个实参 `"external"`。
# 【项目含义】得到 `external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._validate_image(external_rgb, "external")`；`_validate_image` 表示图像相关值；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`external` 表示外部相机相关值。
            external = self._validate_image(external_rgb, "external")
# 【L0106】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist`。右侧语法为：`self` 是模块/对象，点号 `.` 从中取出 `_validate_image` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_rgb`；第 2 个实参 `"wrist"`。
# 【项目含义】得到 `wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._validate_image(wrist_rgb, "wrist")`；`_validate_image` 表示图像相关值；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像；`wrist` 表示腕部相机相关值。
            wrist = self._validate_image(wrist_rgb, "wrist")
# 【L0107】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_path`。右侧语法为：`f"images/external/{frame_index:06d}.png"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】得到 `external_path`，它在本项目中表示外部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"images/external/{frame_index:06d}.png"`；`f` 表示本功能块中的 `f` 值；`images` 表示本功能块中的 `images` 值；`external` 表示外部相机相关值。
            external_path = f"images/external/{frame_index:06d}.png"
# 【L0108】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_path`。右侧语法为：`f"images/wrist/{frame_index:06d}.png"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】得到 `wrist_path`，它在本项目中表示腕部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"images/wrist/{frame_index:06d}.png"`；`f` 表示本功能块中的 `f` 值；`images` 表示本功能块中的 `images` 值；`wrist` 表示腕部相机相关值。
            wrist_path = f"images/wrist/{frame_index:06d}.png"
# 【L0109】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `((external_path, external), (wrist_path, wrist))`，每次把当前元素放进 `relative_path, image`；这会逐个处理“校验并追加一帧状态、动作、物体姿态和图像”所需的帧、episode、动作或实验 case。
            for relative_path, image in ((external_path, external), (wrist_path, wrist)):
# 【L0110】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `path`。右侧语法为：表达式 `self.output_dir / relative_path` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self.output_dir / relative_path`；`output_dir` 表示输出相关值；`relative_path` 表示路径相关值。
                path = self.output_dir / relative_path
# 【L0111】语法拆解：`path.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `path.parent.mkdir(parents=True, exist_ok=True)`。`path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
                path.parent.mkdir(parents=True, exist_ok=True)
# 【L0112】语法拆解：`Image` 是模块/对象，点号 `.` 从中取出 `fromarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image).save(path`。
# 【项目含义】对 `Image` 调用 `fromarray(image).save(path)`：调用 `Image` 提供的 `fromarray` 操作。本行产生的修改/返回值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
                Image.fromarray(image).save(path)
# 【L0113】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0114】语法拆解：`self._timestamps` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `float(timestamp_s)`。
# 【项目含义】对 `self._timestamps` 执行 `append`，把 `float(timestamp_s)` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._timestamps.append(float(timestamp_s))
# 【L0115】语法拆解：`self._sim_steps` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `int(sim_step)`。
# 【项目含义】对 `self._sim_steps` 执行 `append`，把 `int(sim_step)` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._sim_steps.append(int(sim_step))
# 【L0116】语法拆解：`self._states` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.concatenate([joints, [gripper_position]]).astype(np.float32)`。
# 【项目含义】调用 `np.concatenate`：沿一个轴首尾拼接数组；本行实际操作 `self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))`。`_states` 表示本功能块中的 `_states` 值；`append` 表示本功能块中的 `append` 值。
        self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))
# 【L0117】语法拆解：`self._actions` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `action_array`。
# 【项目含义】对 `self._actions` 执行 `append`，把 `action_array` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._actions.append(action_array)
# 【L0118】语法拆解：`self._cube_poses` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube_pose`。
# 【项目含义】对 `self._cube_poses` 执行 `append`，把 `cube_pose` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._cube_poses.append(cube_pose)
# 【L0119】语法拆解：`self._phases` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `phase`。
# 【项目含义】对 `self._phases` 执行 `append`，把 `phase` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._phases.append(phase)
# 【L0120】语法拆解：`self._external_paths` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_path`。
# 【项目含义】对 `self._external_paths` 执行 `append`，把 `external_path` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._external_paths.append(external_path)
# 【L0121】语法拆解：`self._wrist_paths` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_path`。
# 【项目含义】对 `self._wrist_paths` 执行 `append`，把 `wrist_path` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._wrist_paths.append(wrist_path)
# 【L0122】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“校验并追加一帧状态、动作、物体姿态和图像”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：RGB 图像格式校验（源码第 123-131 行）

### 5.A 数据流位置

- 上游：模块 3“校验并追加一帧状态、动作、物体姿态和图像”。
- 本模块：RGB 图像格式校验。
- 下游：处理结果继续交给模块 5“保存 episode.npz 和 metadata.json”。

### 5.B 为什么需要这一组代码

这一组负责“RGB 图像格式校验”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.D 本模块首次阅读要认识的调用

- `_validate_image(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `shape(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`EpisodeRecorder._validate_image()`（第 124-130 行）

- 定义了什么：RGB 图像格式校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`image`：类型 `np.ndarray`；项目含义是图像相关值；`name`：类型 `str`；项目含义是本功能块中的 `name` 值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`array`
- 项目中的实际调用位置：`expert_episode.py:105` 的 `external = self._validate_image(external_rgb, "external")`；`expert_episode.py:106` 的 `wrist = self._validate_image(wrist_rgb, "wrist")`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0123】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0124】语法拆解：`def` 定义函数 `_validate_image`；第一对圆括号列出形参，逗号负责分隔：`image: np.ndarray` 用冒号给参数加类型提示；`name: str` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `_validate_image(image: np.ndarray, name: str)`；调用者把参数交给它完成“RGB 图像格式校验”，后面的缩进代码是具体实现。
    def _validate_image(image: np.ndarray, name: str) -> np.ndarray:
# 【L0125】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `array`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image`。
# 【项目含义】得到 `array`，它在本项目中表示本功能块中的 `array` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `image`（图像相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        array = np.asarray(image)
# 【L0126】语法拆解：`if` 要求条件 `array.ndim != 3 or array.shape[2] != 3` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `array.ndim != 3 or array.shape[2] != 3` 是否成立；`array` 表示本功能块中的 `array` 值；`ndim` 表示本功能块中的 `ndim` 值；`shape` 表示本功能块中的 `shape` 值
        if array.ndim != 3 or array.shape[2] != 3:
# 【L0127】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")` 并停止当前路径；说明当前输入违反“RGB 图像格式校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")
# 【L0128】语法拆解：`if` 要求条件 `array.dtype != np.uint8` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `array.dtype != np.uint8` 是否成立；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`uint8` 表示本功能块中的 `uint8` 值
        if array.dtype != np.uint8:
# 【L0129】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"{name} image must be uint8, got {array.dtype}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"{name} image must be uint8, got {array.dtype}")` 并停止当前路径；说明当前输入违反“RGB 图像格式校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must be uint8, got {array.dtype}")
# 【L0130】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`array` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `array` 交回调用者；这个值的含义是：计算表达式 `array`；`array` 表示本功能块中的 `array` 值。
        return array
# 【L0131】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RGB 图像格式校验”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“RGB 图像格式校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：保存 episode.npz 和 metadata.json（源码第 132-175 行）

### 5.A 数据流位置

- 上游：模块 4“RGB 图像格式校验”。
- 本模块：保存 episode.npz 和 metadata.json。
- 下游：处理结果继续交给模块 6“重新读取磁盘数据并做独立完整性校验”。

### 5.B 为什么需要这一组代码

这一组负责“保存 episode.npz 和 metadata.json”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.C 本模块主要变量

- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `manifest`：描述磁盘数据含义、数量和路径的元数据清单。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `phase_names`：阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。

### 5.D 本模块首次阅读要认识的调用

- `save(...)`：圆括号表示真正执行调用；保存当前数据对象，供训练、验证或之后恢复。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `self.output_dir.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `dict.fromkeys(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.savez_compressed(...)`：圆括号表示真正执行调用；把多个命名数组压缩保存进一个 NPZ 文件。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `np.stack(...)`：圆括号表示真正执行调用；把多个同形数组堆成新增的一维。
- `write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。

### 5.E 本模块定义的新函数

### 函数卡：`EpisodeRecorder.save()`（第 132-173 行）

- 定义了什么：保存 episode.npz 和 metadata.json。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入
- 返回类型标注：`dict[str, Any]`。
- 函数体实际 return：`manifest`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1006` 的 `manifest = episode_recorder.save()`；`run_pick_place_baseline.py:1019` 的 `Image.fromarray(external_initial).save(external_path)`；`run_pick_place_baseline.py:1020` 的 `Image.fromarray(wrist_initial).save(wrist_path)`；`run_pick_place_baseline.py:2368` 的 `episode_manifest = episode_recorder.save()`；`run_pick_place_baseline.py:2164` 的 `episode_manifest = episode_recorder.save()`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0132】语法拆解：`def` 定义函数 `save`；第一对圆括号列出形参，逗号负责分隔：`self` 指调用该方法的当前对象；`-> dict[str, Any]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `save(self)`；调用者把参数交给它完成“保存 episode.npz 和 metadata.json”，后面的缩进代码是具体实现。
    def save(self) -> dict[str, Any]:
# 【L0133】语法拆解：`if` 要求条件 `not self._states` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not self._states` 是否成立；`_states` 表示本功能块中的 `_states` 值
        if not self._states:
# 【L0134】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("cannot save an empty episode")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("cannot save an empty episode")` 并停止当前路径；说明当前输入违反“保存 episode.npz 和 metadata.json”要求，不能继续进入仿真、训练或评测。
            raise ValueError("cannot save an empty episode")
# 【L0135】语法拆解：`self.output_dir` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `self.output_dir.mkdir(parents=True, exist_ok=True)`。`output_dir` 表示输出相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
        self.output_dir.mkdir(parents=True, exist_ok=True)
# 【L0136】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_names`。右侧语法为：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `dict.fromkeys(self._phases)`。
# 【项目含义】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(dict.fromkeys(self._phases))`；`fromkeys` 表示本功能块中的 `fromkeys` 值；`_phases` 表示本功能块中的 `_phases` 值。
        phase_names = list(dict.fromkeys(self._phases))
# 【L0137】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_to_id`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `phase_to_id`，它在本项目中表示本功能块中的 `phase_to_id` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{name: index for index, name in enumerate(phase_names)}`；`name` 表示本功能块中的 `name` 值；`index` 表示索引相关值；`enumerate` 表示本功能块中的 `enumerate` 值。
        phase_to_id = {name: index for index, name in enumerate(phase_names)}
# 【L0138】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `arrays_path`。右侧语法为：表达式 `self.output_dir / "episode.npz"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `arrays_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self.output_dir / "episode.npz"`；`output_dir` 表示输出相关值；`episode` 表示一条轨迹相关值；`npz` 表示本功能块中的 `npz` 值。
        arrays_path = self.output_dir / "episode.npz"
# 【L0139】语法拆解：`np.savez_compressed(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `np` 调用多行方法 `savez_compressed`：调用 `np` 提供的 `savez_compressed` 操作；具体参数写在随后几行，用于“保存 episode.npz 和 metadata.json”。
        np.savez_compressed(
# 【L0140】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arrays_path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arrays_path`；在本项目中它表示路径相关值。
            arrays_path,
# 【L0141】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timestamp_s`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._timestamps`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `timestamp_s` 传入 `np.asarray(self._timestamps, dtype=np.float64)`；该参数在本项目中表示本功能块中的 `timestamp_s` 值，会参与“保存 episode.npz 和 metadata.json”。
            timestamp_s=np.asarray(self._timestamps, dtype=np.float64),
# 【L0142】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim_step`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._sim_steps`；第 2 个实参 `dtype=np.int64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `sim_step` 传入 `np.asarray(self._sim_steps, dtype=np.int64)`；该参数在本项目中表示仿真、步相关值，会参与“保存 episode.npz 和 metadata.json”。
            sim_step=np.asarray(self._sim_steps, dtype=np.int64),
# 【L0143】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observation_state`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `stack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._states`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `observation_state` 传入 `np.stack(self._states)`；该参数在本项目中表示状态相关值，会参与“保存 episode.npz 和 metadata.json”。
            observation_state=np.stack(self._states),
# 【L0144】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `stack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._actions`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `np.stack(self._actions)`；该参数在本项目中表示动作相关值，会参与“保存 episode.npz 和 metadata.json”。
            action=np.stack(self._actions),
# 【L0145】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose_wxyz`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `stack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._cube_poses`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cube_pose_wxyz` 传入 `np.stack(self._cube_poses)`；该参数在本项目中表示任务方块相关值，会参与“保存 episode.npz 和 metadata.json”。
            cube_pose_wxyz=np.stack(self._cube_poses),
# 【L0146】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_id`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[phase_to_id[item] for item in self._phases]`；第 2 个实参 `dtype=np.int16`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `phase_id` 传入 `np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16)`；该参数在本项目中表示本功能块中的 `phase_id` 值，会参与“保存 episode.npz 和 metadata.json”。
            phase_id=np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16),
# 【L0147】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0148】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `has_images`。右侧语法为：`bool` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._images_enabled`。
# 【项目含义】得到 `has_images`，它在本项目中表示本功能块中的 `has_images` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `bool(self._images_enabled)`；`_images_enabled` 表示本功能块中的 `_images_enabled` 值。
        has_images = bool(self._images_enabled)
# 【L0149】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        manifest = {
# 【L0150】语法拆解：这是字典键值对：`"format"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`FORMAT_NAME` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `format`，它表示“保存 episode.npz 和 metadata.json”中的 `format` 数据；字段值来自 `FORMAT_NAME`，因此保存/传递的是这个表达式当前计算出的结果。
            "format": FORMAT_NAME,
# 【L0151】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`prompt`。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `self.prompt`，因此保存/传递的是这个表达式当前计算出的结果。
            "prompt": self.prompt,
# 【L0152】语法拆解：这是字典键值对：`"control_hz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`control_hz`。
# 【项目含义】定义字典/JSON 字段 `control_hz`，它表示“保存 episode.npz 和 metadata.json”中的 `control_hz` 数据；字段值来自 `self.control_hz`，因此保存/传递的是这个表达式当前计算出的结果。
            "control_hz": self.control_hz,
# 【L0153】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self._states`。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“保存 episode.npz 和 metadata.json”中的 `frame_count` 数据；字段值来自 `len(self._states)`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": len(self._states),
# 【L0154】语法拆解：这是字典键值对：`"joint_names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `JOINT_NAMES`。
# 【项目含义】定义字典/JSON 字段 `joint_names`，它表示“保存 episode.npz 和 metadata.json”中的 `joint_names` 数据；字段值来自 `list(JOINT_NAMES)`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_names": list(JOINT_NAMES),
# 【L0155】语法拆解：这是字典键值对：`"observation_state_semantics"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `observation_state_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `observation_state_semantics` 数据；字段值来自 `[*JOINT_NAMES, "gripper_normalized"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "observation_state_semantics": [*JOINT_NAMES, "gripper_normalized"],
# 【L0156】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `action_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `action_semantics` 数据；字段值来自 `[`，因此保存/传递的是这个表达式当前计算出的结果。
            "action_semantics": [
# 【L0157】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*(f"{name}_absolute_target_rad" for name in JOINT_NAMES)` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*(f"{name}_absolute_target_rad" for name in JOINT_NAMES),` 接到上一行未结束的数学公式；`f` 表示本功能块中的 `f` 值；`name` 表示本功能块中的 `name` 值；`_absolute_target_rad` 表示目标相关值，整条公式用于“保存 episode.npz 和 metadata.json”。
                *(f"{name}_absolute_target_rad" for name in JOINT_NAMES),
# 【L0158】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"gripper_normalized_target"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“保存 episode.npz 和 metadata.json”中的帮助说明、错误原因、任务名称或报告文字。
                "gripper_normalized_target",
# 【L0159】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            ],
# 【L0160】语法拆解：这是字典键值对：`"cube_pose_semantics"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `cube_pose_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `cube_pose_semantics` 数据；字段值来自 `["x", "y", "z", "qw", "qx", "qy", "qz"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "cube_pose_semantics": ["x", "y", "z", "qw", "qx", "qy", "qz"],
# 【L0161】语法拆解：这是字典键值对：`"phase_names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`phase_names` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `phase_names`，它表示“保存 episode.npz 和 metadata.json”中的 `phase_names` 数据；字段值来自 `phase_names`，因此保存/传递的是这个表达式当前计算出的结果。
            "phase_names": phase_names,
# 【L0162】语法拆解：这是字典键值对：`"images_recorded"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`has_images` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `images_recorded`，它表示“保存 episode.npz 和 metadata.json”中的 `images_recorded` 数据；字段值来自 `has_images`，因此保存/传递的是这个表达式当前计算出的结果。
            "images_recorded": has_images,
# 【L0163】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `image_paths`，它表示metadata 中逐帧外部/腕部 PNG 的相对路径列表；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "image_paths": {
# 【L0164】语法拆解：这是字典键值对：`"external"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`_external_paths`。
# 【项目含义】定义字典/JSON 字段 `external`，它表示“保存 episode.npz 和 metadata.json”中的 `external` 数据；字段值来自 `self._external_paths`，因此保存/传递的是这个表达式当前计算出的结果。
                "external": self._external_paths,
# 【L0165】语法拆解：这是字典键值对：`"wrist"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`_wrist_paths`。
# 【项目含义】定义字典/JSON 字段 `wrist`，它表示“保存 episode.npz 和 metadata.json”中的 `wrist` 数据；字段值来自 `self._wrist_paths`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist": self._wrist_paths,
# 【L0166】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            },
# 【L0167】语法拆解：这是字典键值对：`"frame_semantics"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"observation immediately before applying action at the same index"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `frame_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `frame_semantics` 数据；字段值来自 `"observation immediately before applying action at the same index"`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_semantics": "observation immediately before applying action at the same index",
# 【L0168】语法拆解：这是字典键值对：`"metadata"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`metadata`。
# 【项目含义】定义字典/JSON 字段 `metadata`，它表示“保存 episode.npz 和 metadata.json”中的 `metadata` 数据；字段值来自 `self.metadata`，因此保存/传递的是这个表达式当前计算出的结果。
            "metadata": self.metadata,
# 【L0169】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        }
# 【L0170】语法拆解：表达式 `(self.output_dir / "metadata.json").write_text(` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `(self.output_dir / "metadata.json").write_text(`。`output_dir` 表示输出相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息。
        (self.output_dir / "metadata.json").write_text(
# 【L0171】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `json.dumps(manifest, indent=2) + "\n", encoding`。右侧语法为：`"utf-8"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `json.dumps(manifest, indent=2) + "\n", encoding="utf-8"`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
# 【L0172】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0173】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`manifest` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `manifest` 交回调用者；这个值的含义是：计算表达式 `manifest`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单。
        return manifest
# 【L0174】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存 episode.npz 和 metadata.json”中的逻辑段，让结构更容易看清。

# 【L0175】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“保存 episode.npz 和 metadata.json”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“保存 episode.npz 和 metadata.json”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 6：重新读取磁盘数据并做独立完整性校验（源码第 176-254 行）

### 5.A 数据流位置

- 上游：模块 5“保存 episode.npz 和 metadata.json”。
- 本模块：重新读取磁盘数据并做独立完整性校验。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“重新读取磁盘数据并做独立完整性校验”。它服务于本文件要解决的总问题：只保存最终成功/失败无法训练策略，也无法证明图像、状态和动作是否同步或夹爪含义是否一致。 这一组的处理结果会参与：固定字段、shape、单位和归一化规则，并在写盘前后执行完整性检查。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `manifest`：描述磁盘数据含义、数量和路径的元数据清单。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。
- `phase_ids`：每一帧所处专家阶段的整数编号。
- `phase_names`：阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。

### 5.D 本模块首次阅读要认识的调用

- `validate_episode(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `np.load(...)`：圆括号表示真正执行调用；从 NPZ/NPY 文件读取 NumPy 数据。
- `manifest.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `errors.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `expected_shapes.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `all(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.isfinite(...)`：圆括号表示真正执行调用；检查是否存在 NaN 或正负无穷。
- `np.all(...)`：圆括号表示真正执行调用；当所有布尔元素都为 True 时返回 True。
- `np.diff(...)`：圆括号表示真正执行调用；计算相邻元素或相邻帧之差。

### 5.E 本模块定义的新函数

### 函数卡：`validate_episode()`（第 176-254 行）

- 定义了什么：重新读取磁盘数据并做独立完整性校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`directory`：类型 `Path`；项目含义是目录相关值；`require_images`（仅关键字）：类型 `bool`，默认 `False`；项目含义是本功能块中的 `require_images` 值
- 返回类型标注：`dict[str, Any]`。
- 函数体实际 return：`{'status': 'pass' if not errors else 'fail', 'format': manifest.get('format'), 'frame_count': frame_count, 'duration_s': float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0, 'images_recorded': images_recorded, 'phase_names': manifest.get('phase_names', []), 'all_finite': not any(('non-finite' in item for item in errors)), 'errors': errors}`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1007` 的 `validation = validate_episode(episode_recorder.output_dir, require_images=True)`；`run_pick_place_baseline.py:2369` 的 `episode_validation = validate_episode(`；`run_pick_place_baseline.py:2165` 的 `episode_validation = validate_episode(`；`convert_expert_episodes_to_lerobot.py:26` 的 `validation = validate_episode(directory, require_images=True)`；`run_expert_collection_plan.py:26` 的 `validation = validate_episode(directory, require_images=True)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0176】语法拆解：`def` 定义函数 `validate_episode`；第一对圆括号列出形参，逗号负责分隔：`directory: Path` 用冒号给参数加类型提示；`*` 是一个形参；`require_images: bool = False` 用冒号给参数加类型提示；`-> dict[str, Any]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `validate_episode(directory: Path, *, require_images: bool = False)`；调用者把参数交给它完成“重新读取磁盘数据并做独立完整性校验”，后面的缩进代码是具体实现。
def validate_episode(directory: Path, *, require_images: bool = False) -> dict[str, Any]:
# 【L0177】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `directory`。右侧语法为：`Path` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `directory`。
# 【项目含义】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(directory)`；`directory` 表示目录相关值。
    directory = Path(directory)
# 【L0178】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(directory / "metadata.json").read_text(encoding="utf-8")`。
# 【项目含义】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0179】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `np.load(directory / "episode.npz") as arrays`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with np.load(directory / "episode.npz") as arrays:
# 【L0180】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timestamps`。右侧语法为：`arrays["timestamp_s"]` 使用方括号索引；先计算 `"timestamp_s"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `timestamps`，它在本项目中表示本功能块中的 `timestamps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["timestamp_s"]`；`arrays` 表示本功能块中的 `arrays` 值；`timestamp_s` 表示本功能块中的 `timestamp_s` 值。
        timestamps = arrays["timestamp_s"]
# 【L0181】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim_steps`。右侧语法为：`arrays["sim_step"]` 使用方括号索引；先计算 `"sim_step"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `sim_steps`，它在本项目中表示仿真、步数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["sim_step"]`；`arrays` 表示本功能块中的 `arrays` 值；`sim_step` 表示仿真、步相关值。
        sim_steps = arrays["sim_step"]
# 【L0182】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `states`。右侧语法为：`arrays["observation_state"]` 使用方括号索引；先计算 `"observation_state"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `states`，它在本项目中表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["observation_state"]`；`arrays` 表示本功能块中的 `arrays` 值；`observation_state` 表示状态相关值。
        states = arrays["observation_state"]
# 【L0183】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actions`。右侧语法为：`arrays["action"]` 使用方括号索引；先计算 `"action"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `actions`，它在本项目中表示一个动作块；形状通常为 (时间步数, 7)；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["action"]`；`arrays` 表示本功能块中的 `arrays` 值；`action` 表示动作相关值。
        actions = arrays["action"]
# 【L0184】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_poses`。右侧语法为：`arrays["cube_pose_wxyz"]` 使用方括号索引；先计算 `"cube_pose_wxyz"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `cube_poses`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["cube_pose_wxyz"]`；`arrays` 表示本功能块中的 `arrays` 值；`cube_pose_wxyz` 表示任务方块相关值。
        cube_poses = arrays["cube_pose_wxyz"]
# 【L0185】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_ids`。右侧语法为：`arrays["phase_id"]` 使用方括号索引；先计算 `"phase_id"`，再从 `arrays` 取对应字典字段或数组元素。
# 【项目含义】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["phase_id"]`；`arrays` 表示本功能块中的 `arrays` 值；`phase_id` 表示本功能块中的 `phase_id` 值。
        phase_ids = arrays["phase_id"]
# 【L0186】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0187】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `frame_count`。右侧语法为：`int` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `manifest["frame_count"]`；其中 `manifest["frame_count"]` 的方括号表示先从 `manifest` 按键/索引 `"frame_count"` 取值。
# 【项目含义】得到 `frame_count`，它在本项目中表示帧、数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `int(manifest["frame_count"])`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`frame_count` 表示帧、数量相关值。
    frame_count = int(manifest["frame_count"])
# 【L0188】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `errors: list[str]`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】把右侧结果写进 `errors: list[str]`（写入 `errors: list[str]` 指定的字段）；右侧具体做的是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    errors: list[str] = []
# 【L0189】语法拆解：`if` 要求条件 `manifest.get("format") != FORMAT_NAME` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `manifest.get("format") != FORMAT_NAME` 是否成立；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if manifest.get("format") != FORMAT_NAME:
# 【L0190】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"unexpected episode format"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"unexpected episode format"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("unexpected episode format")
# 【L0191】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_shapes`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expected_shapes`，它在本项目中表示本功能块中的 `expected_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    expected_shapes = {
# 【L0192】语法拆解：这是字典键值对：`"timestamps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `timestamps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `timestamps` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "timestamps": (frame_count,),
# 【L0193】语法拆解：这是字典键值对：`"sim_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `sim_steps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `sim_steps` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "sim_steps": (frame_count,),
# 【L0194】语法拆解：这是字典键值对：`"states"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `states`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `states` 数据；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": (frame_count, 7),
# 【L0195】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": (frame_count, 7),
# 【L0196】语法拆解：这是字典键值对：`"cube_poses"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `cube_poses`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `cube_poses` 数据；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "cube_poses": (frame_count, 7),
# 【L0197】语法拆解：这是字典键值对：`"phase_ids"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `phase_ids`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_ids` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": (frame_count,),
# 【L0198】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0199】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actual_shapes`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actual_shapes`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    actual_shapes = {
# 【L0200】语法拆解：这是字典键值对：`"timestamps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`timestamps` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `timestamps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `timestamps` 数据；字段值来自 `timestamps.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "timestamps": timestamps.shape,
# 【L0201】语法拆解：这是字典键值对：`"sim_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`sim_steps` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `sim_steps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `sim_steps` 数据；字段值来自 `sim_steps.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "sim_steps": sim_steps.shape,
# 【L0202】语法拆解：这是字典键值对：`"states"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`states` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `states`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `states` 数据；字段值来自 `states.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": states.shape,
# 【L0203】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actions` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `actions.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": actions.shape,
# 【L0204】语法拆解：这是字典键值对：`"cube_poses"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`cube_poses` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `cube_poses`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `cube_poses` 数据；字段值来自 `cube_poses.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "cube_poses": cube_poses.shape,
# 【L0205】语法拆解：这是字典键值对：`"phase_ids"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`phase_ids` 是起始对象；每个点号 `.` 依次读取属性/成员：`shape`。
# 【项目含义】定义字典/JSON 字段 `phase_ids`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_ids` 数据；字段值来自 `phase_ids.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": phase_ids.shape,
# 【L0206】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0207】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `expected_shapes.items()`，每次把当前元素放进 `name, shape`；这会逐个处理“重新读取磁盘数据并做独立完整性校验”所需的帧、episode、动作或实验 case。
    for name, shape in expected_shapes.items():
# 【L0208】语法拆解：`if` 要求条件 `actual_shapes[name] != shape` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `actual_shapes[name] != shape` 是否成立；`actual_shapes` 表示物理仿真实际值相关值；`name` 表示本功能块中的 `name` 值；`shape` 表示本功能块中的 `shape` 值
        if actual_shapes[name] != shape:
# 【L0209】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"{name} shape {actual_shapes[name]} != {shape}"`。
# 【项目含义】对 `errors` 执行 `append`，把 `f"{name} shape {actual_shapes[name]} != {shape}"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
            errors.append(f"{name} shape {actual_shapes[name]} != {shape}")
# 【L0210】语法拆解：`if` 要求条件 `frame_count < 2` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `frame_count < 2` 是否成立；`frame_count` 表示帧、数量相关值
    if frame_count < 2:
# 【L0211】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"episode must contain at least two frames"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"episode must contain at least two frames"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("episode must contain at least two frames")
# 【L0212】语法拆解：`if` 要求条件 `not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses))` 是否成立；`all` 表示本功能块中的 `all` 值；`isfinite` 表示本功能块中的 `isfinite` 值；`item` 表示本功能块中的 `item` 值
    if not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses)):
# 【L0213】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"episode contains non-finite numeric values"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"episode contains non-finite numeric values"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("episode contains non-finite numeric values")
# 【L0214】语法拆解：`if` 要求条件 `len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0)` 是否成立；`timestamps` 表示本功能块中的 `timestamps` 值；`all` 表示本功能块中的 `all` 值；`diff` 表示本功能块中的 `diff` 值
    if len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0):
# 【L0215】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"timestamps are not strictly increasing"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"timestamps are not strictly increasing"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("timestamps are not strictly increasing")
# 【L0216】语法拆解：`if` 要求条件 `len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0)` 是否成立；`sim_steps` 表示仿真、步数相关值；`all` 表示本功能块中的 `all` 值；`diff` 表示本功能块中的 `diff` 值
    if len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0):
# 【L0217】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"simulation steps are not strictly increasing"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"simulation steps are not strictly increasing"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("simulation steps are not strictly increasing")
# 【L0218】语法拆解：`if` 要求条件 `states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0))` 是否成立；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；`size` 表示本功能块中的 `size` 值；`all` 表示本功能块中的 `all` 值
    if states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0)):
# 【L0219】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"observed gripper values leave [0, 1]"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"observed gripper values leave [0, 1]"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("observed gripper values leave [0, 1]")
# 【L0220】语法拆解：`if` 要求条件 `actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0))` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0))` 是否成立；`actions` 表示一个动作块；形状通常为 (时间步数, 7)；`size` 表示本功能块中的 `size` 值；`all` 表示本功能块中的 `all` 值
    if actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0)):
# 【L0221】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"action gripper values leave [0, 1]"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"action gripper values leave [0, 1]"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("action gripper values leave [0, 1]")
# 【L0222】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase_names`。右侧语法为：`manifest` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"phase_names"`；第 2 个实参 `[]`。
# 【项目含义】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `manifest.get("phase_names", [])`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
    phase_names = manifest.get("phase_names", [])
# 【L0223】语法拆解：`if` 要求条件 `phase_ids.size and (` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `phase_ids.size and (` 是否成立；`phase_ids` 表示每一帧所处专家阶段的整数编号；`size` 表示本功能块中的 `size` 值
    if phase_ids.size and (
# 【L0224】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `min` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `phase_ids) < 0 or np.max(phase_ids) >= len(phase_names`。
# 【项目含义】对 `np` 调用 `min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)`：调用 `np` 提供的 `min` 操作。本行产生的修改/返回值服务于“重新读取磁盘数据并做独立完整性校验”。
        np.min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)
# 【L0225】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“重新读取磁盘数据并做独立完整性校验”。
    ):
# 【L0226】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"phase ids leave the manifest phase-name range"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"phase ids leave the manifest phase-name range"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("phase ids leave the manifest phase-name range")
# 【L0227】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0228】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image_paths`。右侧语法为：`manifest` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"image_paths"`；第 2 个实参 `{}`。
# 【项目含义】得到 `image_paths`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：metadata 中逐帧外部/腕部 PNG 的相对路径列表。
    image_paths = manifest.get("image_paths", {})
# 【L0229】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external`。右侧语法为：`image_paths` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"external"`；第 2 个实参 `[]`。
# 【项目含义】得到 `external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `image_paths.get("external", [])`；`image_paths` 表示图像相关值；`get` 表示本功能块中的 `get` 值；`external` 表示外部相机相关值。
    external = image_paths.get("external", [])
# 【L0230】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist`。右侧语法为：`image_paths` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"wrist"`；第 2 个实参 `[]`。
# 【项目含义】得到 `wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `image_paths.get("wrist", [])`；`image_paths` 表示图像相关值；`get` 表示本功能块中的 `get` 值；`wrist` 表示腕部相机相关值。
    wrist = image_paths.get("wrist", [])
# 【L0231】语法拆解：`if` 要求条件 `len(external) != frame_count or len(wrist) != frame_count` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `len(external) != frame_count or len(wrist) != frame_count` 是否成立；`external` 表示外部相机相关值；`frame_count` 表示帧、数量相关值；`wrist` 表示腕部相机相关值
    if len(external) != frame_count or len(wrist) != frame_count:
# 【L0232】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"image path lists do not match frame count"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"image path lists do not match frame count"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("image path lists do not match frame count")
# 【L0233】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `images_recorded`。右侧语法为：`bool` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `manifest.get("images_recorded")`。
# 【项目含义】得到 `images_recorded`，它在本项目中表示本功能块中的 `images_recorded` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `bool(manifest.get("images_recorded"))`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`images_recorded` 表示本功能块中的 `images_recorded` 值。
    images_recorded = bool(manifest.get("images_recorded"))
# 【L0234】语法拆解：`if` 要求条件 `require_images and not images_recorded` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `require_images and not images_recorded` 是否成立；`require_images` 表示本功能块中的 `require_images` 值；`images_recorded` 表示本功能块中的 `images_recorded` 值
    if require_images and not images_recorded:
# 【L0235】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"images are required but were not recorded"`。
# 【项目含义】对 `errors` 执行 `append`，把 `"images are required but were not recorded"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("images are required but were not recorded")
# 【L0236】语法拆解：`if` 要求条件 `images_recorded` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `images_recorded` 是否成立；`images_recorded` 表示本功能块中的 `images_recorded` 值
    if images_recorded:
# 【L0237】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `missing_images`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `missing_images`，它在本项目中表示本功能块中的 `missing_images` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        missing_images = [
# 【L0238】语法拆解：`relative` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `relative`；在本项目中它表示本功能块中的 `relative` 值。
            relative
# 【L0239】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for relative in [*external, *wrist]` 中给出的序列，逐项完成“重新读取磁盘数据并做独立完整性校验”。
            for relative in [*external, *wrist]
# 【L0240】语法拆解：`if` 要求条件 `not relative or not (directory / relative).is_file()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not relative or not (directory / relative).is_file()` 是否成立；`relative` 表示本功能块中的 `relative` 值；`directory` 表示目录相关值；`is_file` 表示本功能块中的 `is_file` 值
            if not relative or not (directory / relative).is_file()
# 【L0241】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
        ]
# 【L0242】语法拆解：`if` 要求条件 `missing_images` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `missing_images` 是否成立；`missing_images` 表示本功能块中的 `missing_images` 值
        if missing_images:
# 【L0243】语法拆解：`errors` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"missing {len(missing_images)} image files"`。
# 【项目含义】对 `errors` 执行 `append`，把 `f"missing {len(missing_images)} image files"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
            errors.append(f"missing {len(missing_images)} image files")
# 【L0244】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0245】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0246】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass" if not errors else "fail"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if not errors else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if not errors else "fail",
# 【L0247】语法拆解：这是字典键值对：`"format"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"format"`。
# 【项目含义】定义字典/JSON 字段 `format`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `format` 数据；字段值来自 `manifest.get("format")`，因此保存/传递的是这个表达式当前计算出的结果。
        "format": manifest.get("format"),
# 【L0248】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`frame_count` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `frame_count` 数据；字段值来自 `frame_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "frame_count": frame_count,
# 【L0249】语法拆解：这是字典键值对：`"duration_s"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `duration_s`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `duration_s` 数据；字段值来自 `float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0`，因此保存/传递的是这个表达式当前计算出的结果。
        "duration_s": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
# 【L0250】语法拆解：这是字典键值对：`"images_recorded"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`images_recorded` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `images_recorded`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `images_recorded` 数据；字段值来自 `images_recorded`，因此保存/传递的是这个表达式当前计算出的结果。
        "images_recorded": images_recorded,
# 【L0251】语法拆解：这是字典键值对：`"phase_names"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"phase_names"`；第 2 个实参 `[]`。
# 【项目含义】定义字典/JSON 字段 `phase_names`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_names` 数据；字段值来自 `manifest.get("phase_names", [])`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_names": manifest.get("phase_names", []),
# 【L0252】语法拆解：这是字典键值对：`"all_finite"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：表达式 `not any("non-finite" in item for item in errors)` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】定义字典/JSON 字段 `all_finite`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `all_finite` 数据；字段值来自 `not any("non-finite" in item for item in errors)`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_finite": not any("non-finite" in item for item in errors),
# 【L0253】语法拆解：这是字典键值对：`"errors"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`errors` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `errors`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `errors` 数据；字段值来自 `errors`，因此保存/传递的是这个表达式当前计算出的结果。
        "errors": errors,
# 【L0254】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“重新读取磁盘数据并做独立完整性校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。