# `serve_rm65_policy.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/serve_rm65_policy.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`d61a16101e6f58b032f269702aaf6337702cba5e1c51404903bb22c768939556`
- 总行数：71

## 1. 先把这个程序放进整个项目

- 所处阶段：在线推理：把训练后的 checkpoint 包装成 WebSocket policy server。
- 输入：checkpoint、数据集/norm-stats repo id、端口与确定性采样参数。
- 输出：可由 IsaacLab 客户端请求的 π0.5 infer 服务和元数据。
- 一句话作用：载入 RM65 微调 checkpoint，并通过 OpenPI 官方 WebSocket 协议持续提供 infer 服务。

### 为什么要写它

- 原先的问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。
- 采用的解决办法：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **argparse**：命令行参数解析：把 `--checkpoint` 等启动选项转换成 `args.checkpoint` 字段。
- **WebSocket**：WebSocket：保持连接的双向网络协议；IsaacLab 客户端用它向独立 OpenPI 进程请求动作。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-19` `82258522` **Add RM65 pi0.5 closed-loop evaluation**：建立 checkpoint 到 IsaacLab 的 π0.5 闭环评测。
- `2026-09-19` `28aef624` **Propagate RM65 policy normalization repo id**：把 norm-stats 数据集标识贯穿训练、服务和评测，避免加载错统计量。
- `2026-09-28` `203c9b9b` **Make RM65 pi0.5 sampling deterministic**：固定随机采样与观测证据，解决相同输入难以复现的问题。

### 与上一版教学快照的源码差异

- 当前第 19-22 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`from openpi_extension.deterministic_policy import (` / `DeterministicRequestPolicy,` / `POLICY_SAMPLING_MODE,` / `)`
- 当前第 37-37 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`policy = policy_config.create_trained_policy(` 当前代码摘录：`trained_policy = policy_config.create_trained_policy(`
- 当前第 41-45 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`)` / `policy = DeterministicRequestPolicy(` / `trained_policy,` / `action_horizon=config.model.action_horizon,`
- 当前第 54-57 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`"sampling_mode": POLICY_SAMPLING_MODE,` / `"deterministic_seed_required": True,` / `"model_action_horizon": config.model.action_horizon,` / `"model_action_dim": config.model.action_dim,`

## 4. 模块地图

- 模块 1｜第 1-25 行：依赖、项目路径和 OpenPI 服务组件
- 模块 2｜第 26-34 行：服务参数
- 模块 3｜第 35-46 行：用同一 RM65 配置载入训练好的 checkpoint
- 模块 4｜第 47-68 行：服务元数据和永久监听
- 模块 5｜第 69-71 行：日志与入口

### 函数/类快速索引

- `main()`：第 26-66 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、项目路径和 OpenPI 服务组件（源码第 1-25 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、项目路径和 OpenPI 服务组件。
- 下游：处理结果继续交给模块 2“服务参数”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、项目路径和 OpenPI 服务组件”。它服务于本文件要解决的总问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。 这一组的处理结果会参与：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

### 5.C 本模块主要变量

- `checkpoint`：一次训练保存的模型参数目录。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `sys.path.insert(...)`：圆括号表示真正执行调用；把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。

### 5.F 这一模块的版本变化

- 当前第 19-22 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`from openpi_extension.deterministic_policy import (` / `DeterministicRequestPolicy,` / `POLICY_SAMPLING_MODE,` / `)`

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`logging` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `logging` 引入 `logging`。在这份程序里，`logging` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import logging
# 【L0008】语法拆解：`import` 加载模块；`socket` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `socket` 引入 `socket`。在这份程序里，`socket` 用于TCP 端口探测与主机信息；后续出现这些名字时调用的是这里的外部能力。
import socket
# 【L0009】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0014】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0015】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 OpenPI 服务组件”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0016】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0017】语法拆解：`from openpi.policies` 指定来源模块；`import policy_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `policy_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.policies import policy_config
# 【L0018】语法拆解：`from openpi.serving.websocket_policy_server` 指定来源模块；`import WebsocketPolicyServer` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `WebsocketPolicyServer`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.serving.websocket_policy_server import WebsocketPolicyServer
# 【L0019】语法拆解：`from openpi_extension.deterministic_policy` 指定来源模块；`import (` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `(`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.deterministic_policy import (
# 【L0020】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`DeterministicRequestPolicy` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `DeterministicRequestPolicy`；在本项目中它表示本功能块中的 `DeterministicRequestPolicy` 值。
    DeterministicRequestPolicy,
# 【L0021】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`POLICY_SAMPLING_MODE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `POLICY_SAMPLING_MODE`；在本项目中它表示策略相关值。
    POLICY_SAMPLING_MODE,
# 【L0022】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“依赖、项目路径和 OpenPI 服务组件”。
)
# 【L0023】语法拆解：`from openpi_extension.rm65_training_config` 指定来源模块；`import make_pi05_rm65_lora_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `make_pi05_rm65_lora_config`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、项目路径和 OpenPI 服务组件”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：服务参数（源码第 26-34 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、项目路径和 OpenPI 服务组件”。
- 本模块：服务参数。
- 下游：处理结果继续交给模块 3“用同一 RM65 配置载入训练好的 checkpoint”。

### 5.B 为什么需要这一组代码

这一组负责“服务参数”。它服务于本文件要解决的总问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。 这一组的处理结果会参与：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

### 5.C 本模块主要变量

- `checkpoint`：一次训练保存的模型参数目录。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 26-66 行）

- 定义了什么：服务参数。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0026】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“服务参数”，后面的缩进代码是具体实现。
def main() -> None:
# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0028】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--checkpoint"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--checkpoint`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0029】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--repo-id"`；第 2 个实参 `default="local/rm65_sim_train"`。
# 【项目含义】声明命令行参数 `--repo-id`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0030】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--host"`；第 2 个实参 `default="0.0.0.0"`。
# 【项目含义】声明命令行参数 `--host`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--host", default="0.0.0.0")
# 【L0031】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--port"`；第 2 个实参 `type=int`；第 3 个实参 `default=8000`。
# 【项目含义】声明命令行参数 `--port`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--port", type=int, default=8000)
# 【L0032】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--default-prompt"`；第 2 个实参 `default="pick up the block and place it on the target"`。
# 【项目含义】声明命令行参数 `--default-prompt`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--default-prompt", default="pick up the block and place it on the target")
# 【L0033】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0034】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“服务参数”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“服务参数”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：用同一 RM65 配置载入训练好的 checkpoint（源码第 35-46 行）

### 5.A 数据流位置

- 上游：模块 2“服务参数”。
- 本模块：用同一 RM65 配置载入训练好的 checkpoint。
- 下游：处理结果继续交给模块 4“服务元数据和永久监听”。

### 5.B 为什么需要这一组代码

这一组负责“用同一 RM65 配置载入训练好的 checkpoint”。它服务于本文件要解决的总问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。 这一组的处理结果会参与：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

### 5.C 本模块主要变量

- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `checkpoint`：一次训练保存的模型参数目录。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `args.checkpoint.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `make_pi05_rm65_lora_config(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `policy_config.create_trained_policy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `DeterministicRequestPolicy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 37-37 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`policy = policy_config.create_trained_policy(` 当前代码摘录：`trained_policy = policy_config.create_trained_policy(`
- 当前第 41-45 行相对旧教学快照发生 `insert`：旧版 0 行，当前 5 行。 当前代码摘录：`)` / `policy = DeterministicRequestPolicy(` / `trained_policy,` / `action_horizon=config.model.action_horizon,`

### 5.G 逐行精读

```python
# 【L0035】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint`。右侧语法为：`args.checkpoint` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.checkpoint.expanduser().resolve()`；`checkpoint` 表示一次训练保存的模型参数目录；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config`。右侧语法为：`make_pi05_rm65_lora_config` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `repo_id=args.repo_id`；第 2 个实参 `batch_size=1`。
# 【项目含义】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建训练与推理共用的 RM65 π0.5/LoRA、数据 transform 和基础权重配置。
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
# 【L0037】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `trained_policy`。右侧语法为：`policy_config.create_trained_policy(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `trained_policy`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：用 RM65 配置、checkpoint 和配套 norm stats 重建可调用 infer() 的 π0.5 policy。
    trained_policy = policy_config.create_trained_policy(
# 【L0038】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`config` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `config`；在本项目中它表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
        config,
# 【L0039】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`checkpoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `checkpoint`；在本项目中它表示一次训练保存的模型参数目录。
        checkpoint,
# 【L0040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default_prompt`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`default_prompt`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default_prompt` 传入 `args.default_prompt`；该参数在本项目中表示本功能块中的 `default_prompt` 值，会参与“用同一 RM65 配置载入训练好的 checkpoint”。
        default_prompt=args.default_prompt,
# 【L0041】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“用同一 RM65 配置载入训练好的 checkpoint”。
    )
# 【L0042】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy`。右侧语法为：`DeterministicRequestPolicy(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `policy`，它在本项目中表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `DeterministicRequestPolicy(`；`DeterministicRequestPolicy` 表示本功能块中的 `DeterministicRequestPolicy` 值。
    policy = DeterministicRequestPolicy(
# 【L0043】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`trained_policy` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `trained_policy`；在本项目中它表示策略相关值。
        trained_policy,
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_horizon`。右侧语法为：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model` → `action_horizon`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_horizon` 传入 `config.model.action_horizon`；该参数在本项目中表示动作相关值，会参与“用同一 RM65 配置载入训练好的 checkpoint”。
        action_horizon=config.model.action_horizon,
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_dim`。右侧语法为：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model` → `action_dim`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_dim` 传入 `config.model.action_dim`；该参数在本项目中表示动作相关值，会参与“用同一 RM65 配置载入训练好的 checkpoint”。
        action_dim=config.model.action_dim,
# 【L0046】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“用同一 RM65 配置载入训练好的 checkpoint”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“用同一 RM65 配置载入训练好的 checkpoint”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：服务元数据和永久监听（源码第 47-68 行）

### 5.A 数据流位置

- 上游：模块 3“用同一 RM65 配置载入训练好的 checkpoint”。
- 本模块：服务元数据和永久监听。
- 下游：处理结果继续交给模块 5“日志与入口”。

### 5.B 为什么需要这一组代码

这一组负责“服务元数据和永久监听”。它服务于本文件要解决的总问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。 这一组的处理结果会参与：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

### 5.C 本模块主要变量

- `gripper`：一个归一化夹爪值组成的一维数组。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `checkpoint`：一次训练保存的模型参数目录。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `socket.gethostname(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `logging.info(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `server(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `WebsocketPolicyServer(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `serve_forever(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 54-57 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`"sampling_mode": POLICY_SAMPLING_MODE,` / `"deterministic_seed_required": True,` / `"model_action_horizon": config.model.action_horizon,` / `"model_action_dim": config.model.action_dim,`

### 5.G 逐行精读

```python
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    metadata = {
# 【L0048】语法拆解：这是字典键值对：`"robot"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"RM65-B"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `robot`，它表示“服务元数据和永久监听”中的 `robot` 数据；字段值来自 `"RM65-B"`，因此保存/传递的是这个表达式当前计算出的结果。
        "robot": "RM65-B",
# 【L0049】语法拆解：这是字典键值对：`"gripper"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"4C2"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `"4C2"`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper": "4C2",
# 【L0050】语法拆解：这是字典键值对：`"model"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pi0.5"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `model`，它表示“服务元数据和永久监听”中的 `model` 数据；字段值来自 `"pi0.5"`，因此保存/传递的是这个表达式当前计算出的结果。
        "model": "pi0.5",
# 【L0051】语法拆解：这是字典键值对：`"checkpoint"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `checkpoint`。
# 【项目含义】定义字典/JSON 字段 `checkpoint`，它表示“服务元数据和永久监听”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0052】语法拆解：这是字典键值对：`"repo_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`repo_id`。
# 【项目含义】定义字典/JSON 字段 `repo_id`，它表示“服务元数据和永久监听”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0053】语法拆解：这是字典键值对：`"action_semantics"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"six absolute joint targets plus normalized gripper target"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `action_semantics`，它表示“服务元数据和永久监听”中的 `action_semantics` 数据；字段值来自 `"six absolute joint targets plus normalized gripper target"`，因此保存/传递的是这个表达式当前计算出的结果。
        "action_semantics": "six absolute joint targets plus normalized gripper target",
# 【L0054】语法拆解：这是字典键值对：`"sampling_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`POLICY_SAMPLING_MODE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `sampling_mode`，它表示“服务元数据和永久监听”中的 `sampling_mode` 数据；字段值来自 `POLICY_SAMPLING_MODE`，因此保存/传递的是这个表达式当前计算出的结果。
        "sampling_mode": POLICY_SAMPLING_MODE,
# 【L0055】语法拆解：这是字典键值对：`"deterministic_seed_required"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `deterministic_seed_required`，它表示“服务元数据和永久监听”中的 `deterministic_seed_required` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "deterministic_seed_required": True,
# 【L0056】语法拆解：这是字典键值对：`"model_action_horizon"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model` → `action_horizon`。
# 【项目含义】定义字典/JSON 字段 `model_action_horizon`，它表示“服务元数据和永久监听”中的 `model_action_horizon` 数据；字段值来自 `config.model.action_horizon`，因此保存/传递的是这个表达式当前计算出的结果。
        "model_action_horizon": config.model.action_horizon,
# 【L0057】语法拆解：这是字典键值对：`"model_action_dim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`model` → `action_dim`。
# 【项目含义】定义字典/JSON 字段 `model_action_dim`，它表示“服务元数据和永久监听”中的 `model_action_dim` 数据；字段值来自 `config.model.action_dim`，因此保存/传递的是这个表达式当前计算出的结果。
        "model_action_dim": config.model.action_dim,
# 【L0058】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“服务元数据和永久监听”。
    }
# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `hostname`。右侧语法为：`socket` 是模块/对象，点号 `.` 从中取出 `gethostname` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `hostname`，它在本项目中表示本功能块中的 `hostname` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `socket.gethostname()`；`socket` 表示本功能块中的 `socket` 值；`gethostname` 表示本功能块中的 `gethostname` 值。
    hostname = socket.gethostname()
# 【L0060】语法拆解：`logging` 是模块/对象，点号 `.` 从中取出 `info` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"Creating RM65 policy server (host=%s, listen=%s:%d)"`；第 2 个实参 `hostname`；第 3 个实参 `args.host`；第 4 个实参 `args.port`。
# 【项目含义】对 `logging` 调用 `info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)`：调用 `logging` 提供的 `info` 操作。本行产生的修改/返回值服务于“服务元数据和永久监听”。
    logging.info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)
# 【L0061】语法拆解：`WebsocketPolicyServer(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `WebsocketPolicyServer`；随后几行会逐项给它参数，调用结果或副作用用于“服务元数据和永久监听”。
    WebsocketPolicyServer(
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy`。右侧语法为：`policy` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy` 传入 `policy`；该参数在本项目中表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象，会参与“服务元数据和永久监听”。
        policy=policy,
# 【L0063】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `host`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`host`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `host` 传入 `args.host`；该参数在本项目中表示本功能块中的 `host` 值，会参与“服务元数据和永久监听”。
        host=args.host,
# 【L0064】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `port`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`port`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `port` 传入 `args.port`；该参数在本项目中表示本功能块中的 `port` 值，会参与“服务元数据和永久监听”。
        port=args.port,
# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata`。右侧语法为：`metadata` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `metadata` 传入 `metadata`；该参数在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息，会参与“服务元数据和永久监听”。
        metadata=metadata,
# 【L0066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `serve_forever()`：调用 `)` 提供的 `serve_forever` 操作。本行产生的修改/返回值服务于“服务元数据和永久监听”。
    ).serve_forever()
# 【L0067】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“服务元数据和永久监听”中的逻辑段，让结构更容易看清。

# 【L0068】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“服务元数据和永久监听”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“服务元数据和永久监听”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：日志与入口（源码第 69-71 行）

### 5.A 数据流位置

- 上游：模块 4“服务元数据和永久监听”。
- 本模块：日志与入口。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“日志与入口”。它服务于本文件要解决的总问题：Isaac Sim 与 OpenPI/JAX 依赖和进程环境不同，直接放在同一进程容易冲突；随机采样还妨碍复现实验。 这一组的处理结果会参与：独立加载 policy 并通过 WebSocket 暴露，显式记录归一化来源和采样种子。

### 5.D 本模块首次阅读要认识的调用

- `logging.basicConfig(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0069】语法拆解：`if` 要求条件 `__name__ == "__main__"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0070】语法拆解：`logging` 是模块/对象，点号 `.` 从中取出 `basicConfig` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `level=logging.INFO`；第 2 个实参 `force=True`。
# 【项目含义】对 `logging` 调用 `basicConfig(level=logging.INFO, force=True)`：调用 `logging` 提供的 `basicConfig` 操作。本行产生的修改/返回值服务于“日志与入口”。
    logging.basicConfig(level=logging.INFO, force=True)
# 【L0071】语法拆解：`main` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】调用本文件的 `main()`，从这里正式进入参数解析、资源创建和主任务流程；上面的函数此时才开始被实际使用。
    main()
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“日志与入口”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。