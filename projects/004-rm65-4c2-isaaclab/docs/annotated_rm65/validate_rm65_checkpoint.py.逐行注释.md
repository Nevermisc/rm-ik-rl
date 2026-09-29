# `validate_rm65_checkpoint.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/validate_rm65_checkpoint.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`cd9d1d36deb8729c8fcd4299c0c7d757292e4e2d078fcbceceb4d86e81622f4f`
- 总行数：97

## 1. 先把这个程序放进整个项目

- 所处阶段：训练后离线验证：在启动 Isaac 前检查 checkpoint 能否加载并产生合法动作。
- 输入：checkpoint、norm stats 来源和一条合成/数据集观测。
- 输出：加载耗时、推理耗时、动作 shape/有限值和验证报告。
- 一句话作用：在不启动 Isaac Sim 的情况下，用一帧真实记录观测检查 checkpoint 能加载、推理、返回 10×7 有限动作并通过 guard。

### 为什么要写它

- 原先的问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。
- 采用的解决办法：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

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

- `2026-09-19` `82258522` **Add RM65 pi0.5 closed-loop evaluation**：建立 checkpoint 到 IsaacLab 的 π0.5 闭环评测。

### 与上一版教学快照的源码差异

- 当前源码与上一版教学快照一致。

## 4. 模块地图

- 模块 1｜第 1-29 行：依赖、项目路径和 RGB 读取
- 模块 2｜第 30-47 行：参数、checkpoint/episode 和帧索引校验
- 模块 3｜第 48-58 行：从记录 episode 复原一次完整 RM65 观测
- 模块 4｜第 59-71 行：载入 checkpoint、计时推理并验证动作形状/有限数/guard
- 模块 5｜第 72-97 行：写出离线 checkpoint 验证报告

### 函数/类快速索引

- `read_rgb()`：第 25-27 行
- `main()`：第 30-93 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、项目路径和 RGB 读取（源码第 1-29 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、项目路径和 RGB 读取。
- 下游：处理结果继续交给模块 2“参数、checkpoint/episode 和帧索引校验”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、项目路径和 RGB 读取”。它服务于本文件要解决的总问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。 这一组的处理结果会参与：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

### 5.C 本模块主要变量

- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `checkpoint`：一次训练保存的模型参数目录。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `sys.path.insert(...)`：圆括号表示真正执行调用；把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。
- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `Image.open(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `image.convert(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`read_rgb()`（第 25-27 行）

- 定义了什么：依赖、项目路径和 RGB 读取。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`path`：类型 `Path`；项目含义是路径相关值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`np.asarray(image.convert('RGB'), dtype=np.uint8)`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:122` 的 `first_external = read_rgb(first["directory"] / first["external_paths"][0])`；`convert_expert_episodes_to_lerobot.py:123` 的 `first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])`；`convert_expert_episodes_to_lerobot.py:163` 的 `expected_external_shape = read_rgb(`；`convert_expert_episodes_to_lerobot.py:166` 的 `expected_wrist_shape = read_rgb(`；`convert_expert_episodes_to_lerobot.py:236` 的 `external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run one recorded RM65 observation through a trained π0.5 checkpoint.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run one recorded RM65 observation through a trained π0.5 checkpoint."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0009】语法拆解：`import` 加载模块；`time` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `time` 引入 `time`。在这份程序里，`time` 用于计时和短暂等待；后续出现这些名字时调用的是这里的外部能力。
import time
# 【L0010】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0012】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0013】语法拆解：`from PIL` 指定来源模块；`import Image` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
from PIL import Image
# 【L0014】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 RGB 读取”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0020】语法拆解：`from openpi.policies` 指定来源模块；`import policy_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `policy_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.policies import policy_config
# 【L0021】语法拆解：`from openpi_extension.action_guard` 指定来源模块；`import guard_action_chunk` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `guard_action_chunk`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.action_guard import guard_action_chunk
# 【L0022】语法拆解：`from openpi_extension.rm65_training_config` 指定来源模块；`import make_pi05_rm65_lora_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `make_pi05_rm65_lora_config`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0023】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：`def` 定义函数 `read_rgb`；第一对圆括号列出形参，逗号负责分隔：`path: Path` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `read_rgb(path: Path)`；调用者把参数交给它完成“依赖、项目路径和 RGB 读取”，后面的缩进代码是具体实现。
def read_rgb(path: Path) -> np.ndarray:
# 【L0026】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `Image.open(path) as image`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with Image.open(path) as image:
# 【L0027】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image.convert("RGB")`；第 2 个实参 `dtype=np.uint8`。
# 【项目含义】结束当前函数并把 `np.asarray(image.convert("RGB"), dtype=np.uint8)` 交回调用者；这个值的含义是：读取/计算 `image.convert("RGB"), dtype=np.uint8`（本功能块中的 `image.convert("RGB"), dtype=np.uint8` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
# 【L0028】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0029】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、项目路径和 RGB 读取”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：参数、checkpoint/episode 和帧索引校验（源码第 30-47 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、项目路径和 RGB 读取”。
- 本模块：参数、checkpoint/episode 和帧索引校验。
- 下游：处理结果继续交给模块 3“从记录 episode 复原一次完整 RM65 观测”。

### 5.B 为什么需要这一组代码

这一组负责“参数、checkpoint/episode 和帧索引校验”。它服务于本文件要解决的总问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。 这一组的处理结果会参与：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

### 5.C 本模块主要变量

- `checkpoint`：一次训练保存的模型参数目录。
- `output`：输出文件路径。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `args.checkpoint.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `args.episode.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `json.loads(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `read_text(...)`：圆括号表示真正执行调用；从磁盘读取文本。
- `np.load(...)`：圆括号表示真正执行调用；从 NPZ/NPY 文件读取 NumPy 数据。
- `astype(...)`：圆括号表示真正执行调用；把 NumPy 数组元素转换到指定 dtype，例如把像素转成 uint8。
- `IndexError(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 30-93 行）

- 定义了什么：参数、checkpoint/episode 和帧索引校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0030】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“参数、checkpoint/episode 和帧索引校验”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0031】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0032】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--checkpoint"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--checkpoint`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0033】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--episode"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--episode`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--episode", type=Path, required=True)
# 【L0034】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--repo-id"`；第 2 个实参 `default="local/rm65_sim_train"`。
# 【项目含义】声明命令行参数 `--repo-id`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0035】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--frame-index"`；第 2 个实参 `type=int`；第 3 个实参 `default=0`。
# 【项目含义】声明命令行参数 `--frame-index`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--frame-index", type=int, default=0)
# 【L0036】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--output"`；第 2 个实参 `type=Path`。
# 【项目含义】声明命令行参数 `--output`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--output", type=Path)
# 【L0037】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0038】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“参数、checkpoint/episode 和帧索引校验”中的逻辑段，让结构更容易看清。

# 【L0039】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`args.checkpoint` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.checkpoint.expanduser().resolve()`；`checkpoint` 表示一次训练保存的模型参数目录；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode`。右侧语法为：`args.episode` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `episode`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.episode.expanduser().resolve()`；`episode` 表示一条轨迹相关值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    episode = args.episode.expanduser().resolve()
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata`。右侧语法为：`json` 是模块/对象，点号 `.` 从中取出 `loads` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(episode / "metadata.json").read_text(encoding="utf-8")`。
# 【项目含义】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    metadata = json.loads((episode / "metadata.json").read_text(encoding="utf-8"))
# 【L0042】语法拆解：`with` 进入上下文管理器；`as` 若存在就给资源命名；末尾冒号打开使用资源的代码，离开时会自动清理。
# 【项目含义】进入资源上下文 `np.load(episode / "episode.npz") as arrays`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with np.load(episode / "episode.npz") as arrays:
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `states`。右侧语法为：`arrays["observation_state"].astype(np.float32, copy=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `states`，它在本项目中表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["observation_state"].astype(np.float32, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`observation_state` 表示状态相关值；`astype` 表示本功能块中的 `astype` 值。
        states = arrays["observation_state"].astype(np.float32, copy=True)
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `index`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`frame_index`。
# 【项目含义】得到 `index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.frame_index`；`frame_index` 表示帧、索引相关值。
    index = args.frame_index
# 【L0045】语法拆解：`if` 要求条件 `not 0 <= index < len(states)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0 <= index < len(states)` 是否成立；`index` 表示索引相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪
    if not 0 <= index < len(states):
# 【L0046】语法拆解：`raise` 主动制造并抛出异常；后面的 `IndexError(f"frame index {index} outside [0, {len(states)})")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `IndexError(f"frame index {index} outside [0, {len(states)})")` 并停止当前路径；说明当前输入违反“参数、checkpoint/episode 和帧索引校验”要求，不能继续进入仿真、训练或评测。
        raise IndexError(f"frame index {index} outside [0, {len(states)})")
# 【L0047】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“参数、checkpoint/episode 和帧索引校验”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“参数、checkpoint/episode 和帧索引校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：从记录 episode 复原一次完整 RM65 观测（源码第 48-58 行）

### 5.A 数据流位置

- 上游：模块 2“参数、checkpoint/episode 和帧索引校验”。
- 本模块：从记录 episode 复原一次完整 RM65 观测。
- 下游：处理结果继续交给模块 4“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。

### 5.B 为什么需要这一组代码

这一组负责“从记录 episode 复原一次完整 RM65 观测”。它服务于本文件要解决的总问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。 这一组的处理结果会参与：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

### 5.C 本模块主要变量

- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。

### 5.D 本模块首次阅读要认识的调用

- `read_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observation`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `observation`，它在本项目中表示本次发给 π0.5 的图像、状态和文字指令字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    observation = {
# 【L0049】语法拆解：这是字典键值对：`"observation/joint_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`states[index, :6]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】定义字典/JSON 字段 `observation/joint_position`，它表示IsaacLab 当前观测到的六个 RM65 关节角，顺序 joint_1 到 joint_6，单位 rad；字段值来自 `states[index, :6]`，因此保存/传递的是这个表达式当前计算出的结果。
        "observation/joint_position": states[index, :6],
# 【L0050】语法拆解：这是字典键值对：`"observation/gripper_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`states[index, 6:7]` 使用方括号切片；冒号把开始、结束或步长分开，用来选择数组的一部分。
# 【项目含义】定义字典/JSON 字段 `observation/gripper_position`，它表示4C2 主关节位置归一化后的单元素数组，0 表示张开、1 表示闭合；字段值来自 `states[index, 6:7]`，因此保存/传递的是这个表达式当前计算出的结果。
        "observation/gripper_position": states[index, 6:7],
# 【L0051】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `observation/external_image`，它表示固定外部相机看到的 RGB 图像；字段值来自 `read_rgb(`，因此保存/传递的是这个表达式当前计算出的结果。
        "observation/external_image": read_rgb(
# 【L0052】语法拆解：表达式 `episode / metadata["image_paths"]["external"][index]` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `episode / metadata["image_paths"]["external"][index]` 接入当前完整语句；`episode` 表示一条轨迹相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`image_paths` 表示图像相关值。在“从记录 episode 复原一次完整 RM65 观测”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode / metadata["image_paths"]["external"][index]
# 【L0053】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
        ),
# 【L0054】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `observation/wrist_image`，它表示随 RM65 末端运动的腕部相机 RGB 图像；字段值来自 `read_rgb(`，因此保存/传递的是这个表达式当前计算出的结果。
        "observation/wrist_image": read_rgb(
# 【L0055】语法拆解：表达式 `episode / metadata["image_paths"]["wrist"][index]` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `episode / metadata["image_paths"]["wrist"][index]` 接入当前完整语句；`episode` 表示一条轨迹相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息；`image_paths` 表示图像相关值。在“从记录 episode 复原一次完整 RM65 观测”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode / metadata["image_paths"]["wrist"][index]
# 【L0056】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
        ),
# 【L0057】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`metadata["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `metadata` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `metadata["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": metadata["prompt"],
# 【L0058】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
    }
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“从记录 episode 复原一次完整 RM65 观测”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：载入 checkpoint、计时推理并验证动作形状/有限数/guard（源码第 59-71 行）

### 5.A 数据流位置

- 上游：模块 3“从记录 episode 复原一次完整 RM65 观测”。
- 本模块：载入 checkpoint、计时推理并验证动作形状/有限数/guard。
- 下游：处理结果继续交给模块 5“写出离线 checkpoint 验证报告”。

### 5.B 为什么需要这一组代码

这一组负责“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。它服务于本文件要解决的总问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。 这一组的处理结果会参与：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `safe_actions`：经过 action guard 后允许进入仿真的动作。
- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `checkpoint`：一次训练保存的模型参数目录。
- `guard`：action guard 返回的裁剪次数、最大步长等诊断字典。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `states`：episode 中全部七维观测状态，列为六关节角加归一化夹爪。
- `load_seconds`：从磁盘和基础权重重建训练后 policy 所用时间。

### 5.D 本模块首次阅读要认识的调用

- `make_pi05_rm65_lora_config(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `time.perf_counter(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `policy_config.create_trained_policy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `policy.infer(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `np.isfinite(...)`：圆括号表示真正执行调用；检查是否存在 NaN 或正负无穷。
- `all(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `guard_action_chunk(...)`：圆括号表示真正执行调用；验证并裁剪策略动作，阻止越界和过大跳变。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config`。右侧语法为：`make_pi05_rm65_lora_config` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `repo_id=args.repo_id`；第 2 个实参 `batch_size=1`。
# 【项目含义】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建训练与推理共用的 RM65 π0.5/LoRA、数据 transform 和基础权重配置。
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `start`。右侧语法为：`time` 是模块/对象，点号 `.` 从中取出 `perf_counter` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `start`，它在本项目中表示本功能块中的 `start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter()`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值。
    start = time.perf_counter()
# 【L0061】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy`。右侧语法为：`policy_config` 是模块/对象，点号 `.` 从中取出 `create_trained_policy` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `config`；第 2 个实参 `checkpoint`。
# 【项目含义】得到 `policy`，它在本项目中表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：用 RM65 配置、checkpoint 和配套 norm stats 重建可调用 infer() 的 π0.5 policy。
    policy = policy_config.create_trained_policy(config, checkpoint)
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `load_seconds`。右侧语法为：表达式 `time.perf_counter() - start` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `load_seconds`，它在本项目中表示从磁盘和基础权重重建训练后 policy 所用时间；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter() - start`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值；`start` 表示本功能块中的 `start` 值。
    load_seconds = time.perf_counter() - start
# 【L0063】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `start`。右侧语法为：`time` 是模块/对象，点号 `.` 从中取出 `perf_counter` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `start`，它在本项目中表示本功能块中的 `start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter()`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值。
    start = time.perf_counter()
# 【L0064】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result`。右侧语法为：`policy` 是模块/对象，点号 `.` 从中取出 `infer` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `observation`。
# 【项目含义】得到 `result`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把当前观测交给 π0.5 policy 推理，得到包含未来动作块的返回字典。
    result = policy.infer(observation)
# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inference_seconds`。右侧语法为：表达式 `time.perf_counter() - start` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `inference_seconds`，它在本项目中表示单次离线 policy.infer 所用时间；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter() - start`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值；`start` 表示本功能块中的 `start` 值。
    inference_seconds = time.perf_counter() - start
# 【L0066】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actions`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `result["actions"]`；第 2 个实参 `dtype=np.float32`；其中 `result["actions"]` 的方括号表示先从 `result` 按键/索引 `"actions"` 取值。
# 【项目含义】得到 `actions`，它在本项目中表示一个动作块；形状通常为 (时间步数, 7)；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `result["actions"], dtype=np.float32`（未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    actions = np.asarray(result["actions"], dtype=np.float32)
# 【L0067】语法拆解：`if` 要求条件 `actions.shape != (config.model.action_horizon, 7)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `actions.shape` 是否不等于要求的 `(config.model.action_horizon, 7)`；若不等，数据维度合同已被破坏，进入错误处理
    if actions.shape != (config.model.action_horizon, 7):
# 【L0068】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected actions {(config.model.action_horizon, 7)}, got {actions.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected actions {(config.model.action_horizon, 7)}, got {actions.shape}")` 并停止当前路径；说明当前输入违反“载入 checkpoint、计时推理并验证动作形状/有限数/guard”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"expected actions {(config.model.action_horizon, 7)}, got {actions.shape}")
# 【L0069】语法拆解：`if` 要求条件 `not np.isfinite(actions).all()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
    if not np.isfinite(actions).all():
# 【L0070】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("checkpoint returned non-finite actions")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("checkpoint returned non-finite actions")` 并停止当前路径；说明当前输入违反“载入 checkpoint、计时推理并验证动作形状/有限数/guard”要求，不能继续进入仿真、训练或评测。
        raise ValueError("checkpoint returned non-finite actions")
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe_actions, guard`。右侧语法为：`guard_action_chunk` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `actions`；第 2 个实参 `states[index, :6]`；其中 `states[index, :6]` 的方括号表示先从 `states` 按键/索引 `index, :6` 取值。
# 【项目含义】把右侧返回的多个结果按位置拆给 `safe_actions, guard`；`safe_actions` 表示经过 action guard 后允许进入仿真的动作；`guard` 表示action guard 返回的裁剪次数、最大步长等诊断字典。右侧的来源是：把模型动作与当前六关节角交给确定性 guard，得到安全动作块和裁剪诊断。
    safe_actions, guard = guard_action_chunk(actions, states[index, :6])
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“载入 checkpoint、计时推理并验证动作形状/有限数/guard”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：写出离线 checkpoint 验证报告（源码第 72-97 行）

### 5.A 数据流位置

- 上游：模块 4“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
- 本模块：写出离线 checkpoint 验证报告。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“写出离线 checkpoint 验证报告”。它服务于本文件要解决的总问题：训练目录存在不代表参数完整可用；把坏 checkpoint 直接带进昂贵仿真会浪费时间且难定位。 这一组的处理结果会参与：独立重建 policy，做一次 infer，并检查动作维度、数值与资产来源。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `safe_actions`：经过 action guard 后允许进入仿真的动作。
- `report`：机器可读实验报告字典。
- `checkpoint`：一次训练保存的模型参数目录。
- `output`：输出文件路径。
- `guard`：action guard 返回的裁剪次数、最大步长等诊断字典。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `load_seconds`：从磁盘和基础权重重建训练后 policy 所用时间。
- `inference_seconds`：单次离线 policy.infer 所用时间。

### 5.D 本模块首次阅读要认识的调用

- `tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `args.output.parent.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `args.output.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0073】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0074】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0075】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0076】语法拆解：这是字典键值对：`"checkpoint"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】定义字典/JSON 字段 `checkpoint`，它表示“写出离线 checkpoint 验证报告”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0077】语法拆解：这是字典键值对：`"episode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode`。
# 【项目含义】定义字典/JSON 字段 `episode`，它表示“写出离线 checkpoint 验证报告”中的 `episode` 数据；字段值来自 `str(episode)`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode": str(episode),
# 【L0078】语法拆解：这是字典键值对：`"frame_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `frame_index`，它表示“写出离线 checkpoint 验证报告”中的 `frame_index` 数据；字段值来自 `index`，因此保存/传递的是这个表达式当前计算出的结果。
        "frame_index": index,
# 【L0079】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`metadata["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `metadata` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `metadata["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": metadata["prompt"],
# 【L0080】语法拆解：这是字典键值对：`"load_seconds"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`load_seconds` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `load_seconds`，它表示“写出离线 checkpoint 验证报告”中的 `load_seconds` 数据；字段值来自 `load_seconds`，因此保存/传递的是这个表达式当前计算出的结果。
        "load_seconds": load_seconds,
# 【L0081】语法拆解：这是字典键值对：`"inference_seconds"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`inference_seconds` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `inference_seconds`，它表示“写出离线 checkpoint 验证报告”中的 `inference_seconds` 数据；字段值来自 `inference_seconds`，因此保存/传递的是这个表达式当前计算出的结果。
        "inference_seconds": inference_seconds,
# 【L0082】语法拆解：这是字典键值对：`"actions_shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `actions.shape`。
# 【项目含义】定义字典/JSON 字段 `actions_shape`，它表示“写出离线 checkpoint 验证报告”中的 `actions_shape` 数据；字段值来自 `list(actions.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions_shape": list(actions.shape),
# 【L0083】语法拆解：这是字典键值对：`"all_actions_finite"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `all_actions_finite`，它表示“写出离线 checkpoint 验证报告”中的 `all_actions_finite` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_actions_finite": True,
# 【L0084】语法拆解：这是字典键值对：`"first_raw_action"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actions[0].tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `first_raw_action`，它表示“写出离线 checkpoint 验证报告”中的 `first_raw_action` 数据；字段值来自 `actions[0].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "first_raw_action": actions[0].tolist(),
# 【L0085】语法拆解：这是字典键值对：`"first_guarded_action"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`safe_actions[0].tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `first_guarded_action`，它表示“写出离线 checkpoint 验证报告”中的 `first_guarded_action` 数据；字段值来自 `safe_actions[0].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "first_guarded_action": safe_actions[0].tolist(),
# 【L0086】语法拆解：这是字典键值对：`"guard"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`guard` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `guard`，它表示“写出离线 checkpoint 验证报告”中的 `guard` 数据；字段值来自 `guard`，因此保存/传递的是这个表达式当前计算出的结果。
        "guard": guard,
# 【L0087】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出离线 checkpoint 验证报告”。
    }
# 【L0088】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `text`。右侧语法为：表达式 `json.dumps(report, indent=2) + "\n"` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `text`，它在本项目中表示本功能块中的 `text` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 Python 字典序列化为 JSON 文本，供日志、报告或下游程序读取。
    text = json.dumps(report, indent=2) + "\n"
# 【L0089】语法拆解：`if` 要求条件 `args.output is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.output is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.output is not None:
# 【L0090】语法拆解：`args.output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0091】语法拆解：`args.output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `args.output.write_text(text, encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        args.output.write_text(text, encoding="utf-8")
# 【L0092】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `text`；第 2 个实参 `end=""`。
# 【项目含义】把 `text, end=""` 的当前值/文字输出到终端；它用于观察“写出离线 checkpoint 验证报告”进度，也给日志留下可搜索证据。
    print(text, end="")
# 【L0093】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0094】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写出离线 checkpoint 验证报告”中的逻辑段，让结构更容易看清。

# 【L0095】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写出离线 checkpoint 验证报告”中的逻辑段，让结构更容易看清。

# 【L0096】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0097】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(main())` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“写出离线 checkpoint 验证报告”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“写出离线 checkpoint 验证报告”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。