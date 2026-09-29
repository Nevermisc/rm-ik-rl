# `validate_rm65_checkpoint.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/validate_rm65_checkpoint.py`
- 快照 SHA-256：`cd9d1d36deb8729c8fcd4299c0c7d757292e4e2d078fcbceceb4d86e81622f4f`
- 总行数：97
- 程序作用：在不启动 Isaac Sim 的情况下，用一帧真实记录观测检查 checkpoint 能加载、推理、返回 10×7 有限动作并通过 guard。
- 推荐读法：这是训练完成到昂贵闭环评测之间的快速离线冒烟测试。

## 功能块地图

- 第 1-27 行：依赖、项目路径和 RGB 读取
- 第 30-46 行：参数、checkpoint/episode 和帧索引校验
- 第 48-58 行：从记录 episode 复原一次完整 RM65 观测
- 第 59-71 行：载入 checkpoint、计时推理并验证动作形状/有限数/guard
- 第 72-97 行：写出离线 checkpoint 验证报告

## 函数/类索引

- `read_rgb()`：第 25-27 行
- `main()`：第 30-93 行

## 逐行学习副本

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

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
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0029】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0030】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“参数、checkpoint/episode 和帧索引校验”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0031】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0032】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--checkpoint", type`。右侧语法为：`Path, required=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--checkpoint`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0033】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--episode", type`。右侧语法为：`Path, required=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--episode`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--episode", type=Path, required=True)
# 【L0034】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--repo-id", default`。右侧语法为：表达式 `"local/rm65_sim_train")` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】声明命令行参数 `--repo-id`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0035】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--frame-index", type`。右侧语法为：`int, default=0)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--frame-index`；启动脚本可用它改变“参数、checkpoint/episode 和帧索引校验”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--frame-index", type=int, default=0)
# 【L0036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--output", type`。右侧语法为：`Path)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
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
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observation`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `observation`，它在本项目中表示本次发给 π0.5 的图像、状态和文字指令字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    observation = {
# 【L0049】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `observation/joint_position`，它表示IsaacLab 当前观测到的六个 RM65 关节角，顺序 joint_1 到 joint_6，单位 rad；字段值来自 `states[index, :6]`，因此保存/传递的是这个表达式当前计算出的结果。
        "observation/joint_position": states[index, :6],
# 【L0050】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
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
# 【L0057】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `metadata["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": metadata["prompt"],
# 【L0058】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
    }
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
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0073】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0074】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0075】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0076】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `checkpoint`，它表示“写出离线 checkpoint 验证报告”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0077】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `episode`，它表示“写出离线 checkpoint 验证报告”中的 `episode` 数据；字段值来自 `str(episode)`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode": str(episode),
# 【L0078】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `frame_index`，它表示“写出离线 checkpoint 验证报告”中的 `frame_index` 数据；字段值来自 `index`，因此保存/传递的是这个表达式当前计算出的结果。
        "frame_index": index,
# 【L0079】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `metadata["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": metadata["prompt"],
# 【L0080】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `load_seconds`，它表示“写出离线 checkpoint 验证报告”中的 `load_seconds` 数据；字段值来自 `load_seconds`，因此保存/传递的是这个表达式当前计算出的结果。
        "load_seconds": load_seconds,
# 【L0081】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `inference_seconds`，它表示“写出离线 checkpoint 验证报告”中的 `inference_seconds` 数据；字段值来自 `inference_seconds`，因此保存/传递的是这个表达式当前计算出的结果。
        "inference_seconds": inference_seconds,
# 【L0082】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `actions_shape`，它表示“写出离线 checkpoint 验证报告”中的 `actions_shape` 数据；字段值来自 `list(actions.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions_shape": list(actions.shape),
# 【L0083】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `all_actions_finite`，它表示“写出离线 checkpoint 验证报告”中的 `all_actions_finite` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_actions_finite": True,
# 【L0084】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `first_raw_action`，它表示“写出离线 checkpoint 验证报告”中的 `first_raw_action` 数据；字段值来自 `actions[0].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "first_raw_action": actions[0].tolist(),
# 【L0085】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `first_guarded_action`，它表示“写出离线 checkpoint 验证报告”中的 `first_guarded_action` 数据；字段值来自 `safe_actions[0].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "first_guarded_action": safe_actions[0].tolist(),
# 【L0086】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
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
# 【L0090】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args.output.parent.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0091】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args.output.write_text(text, encoding`。右侧语法为：表达式 `"utf-8")` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `args.output.write_text(text, encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        args.output.write_text(text, encoding="utf-8")
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `print(text, end`。右侧语法为：`"")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
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
