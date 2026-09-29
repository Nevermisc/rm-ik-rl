# `websocket_compat.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/websocket_compat.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`e691766070778e159598ef7bc26039daca43194e5614f006f35c4f6ec95cbb5f`
- 总行数：25

## 1. 先把这个程序放进整个项目

- 所处阶段：运行兼容：协调 Isaac Sim 内置 websockets 与 OpenPI 环境版本差异。
- 输入：不同版本的 connect 函数、连接参数和 ping_interval。
- 输出：两个环境都能调用的 WebSocket 连接对象。
- 一句话作用：兼容 Isaac Sim 自带 websockets 12 与 OpenPI 环境 websockets 15 的 connect 参数差异，并在支持时关闭 keepalive。

### 为什么要写它

- 原先的问题：Isaac Sim 5.1 的 websockets 版本不支持 OpenPI 客户端使用的同步 keepalive 参数，曾造成连接或超时故障。
- 采用的解决办法：检查函数签名；支持时禁用 ping，旧版本则移除不认识的参数。

## 2. 本文件出现的基础概念

- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **WebSocket**：WebSocket：保持连接的双向网络协议；IsaacLab 客户端用它向独立 OpenPI 进程请求动作。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-19` `f18f8ca8` **Fix Isaac websocket compatibility and enforce task reports**：修复 Isaac/OpenPI WebSocket 版本兼容，并要求机器可读任务报告。

### 与上一版教学快照的源码差异

- 当前源码与上一版教学快照一致。

## 4. 模块地图

- 模块 1｜第 1-9 行：反射和类型依赖
- 模块 2｜第 10-19 行：兼容函数接口与版本差异说明
- 模块 3｜第 20-25 行：检查 connect 签名并安全添加/移除 ping_interval

### 函数/类快速索引

- `call_connect_without_keepalive()`：第 10-25 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：反射和类型依赖（源码第 1-9 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：反射和类型依赖。
- 下游：处理结果继续交给模块 2“兼容函数接口与版本差异说明”。

### 5.B 为什么需要这一组代码

这一组负责“反射和类型依赖”。它服务于本文件要解决的总问题：Isaac Sim 5.1 的 websockets 版本不支持 OpenPI 客户端使用的同步 keepalive 参数，曾造成连接或超时故障。 这一组的处理结果会参与：检查函数签名；支持时禁用 ping，旧版本则移除不认识的参数。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0001】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim."""
# 【L0002】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0003】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0005】语法拆解：`import` 加载模块；`inspect` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `inspect` 引入 `inspect`。在这份程序里，`inspect` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import inspect
# 【L0006】语法拆解：`from collections.abc` 指定来源模块；`import Callable` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `collections` 引入 `Callable`。在这份程序里，`collections` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from collections.abc import Callable
# 【L0007】语法拆解：`from typing` 指定来源模块；`import Any` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0008】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0009】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“反射和类型依赖”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：兼容函数接口与版本差异说明（源码第 10-19 行）

### 5.A 数据流位置

- 上游：模块 1“反射和类型依赖”。
- 本模块：兼容函数接口与版本差异说明。
- 下游：处理结果继续交给模块 3“检查 connect 签名并安全添加/移除 ping_interval”。

### 5.B 为什么需要这一组代码

这一组负责“兼容函数接口与版本差异说明”。它服务于本文件要解决的总问题：Isaac Sim 5.1 的 websockets 版本不支持 OpenPI 客户端使用的同步 keepalive 参数，曾造成连接或超时故障。 这一组的处理结果会参与：检查函数签名；支持时禁用 ping，旧版本则移除不认识的参数。

### 5.D 本模块首次阅读要认识的调用

- `call_connect_without_keepalive(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.E 本模块定义的新函数

### 函数卡：`call_connect_without_keepalive()`（第 10-25 行）

- 定义了什么：兼容函数接口与版本差异说明。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`connect`：类型 `Callable[..., Any]`；项目含义是本功能块中的 `connect` 值
- 返回类型标注：`Any`。
- 函数体实际 return：`connect(*args, **kwargs)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:709` 的 `return call_connect_without_keepalive(`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0010】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `call_connect_without_keepalive(参数在后续行继续)`；调用者把参数交给它完成“兼容函数接口与版本差异说明”，后面的缩进代码是具体实现。
def call_connect_without_keepalive(
# 【L0011】语法拆解：`connect` 是参数/字段名；冒号 `:` 添加类型提示 `Callable[..., Any], *args: Any, **kwargs: Any`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `connect: Callable[..., Any], *args: Any, **kwargs: Any` 接入当前完整语句；`connect` 表示本功能块中的 `connect` 值；`Callable` 表示本功能块中的 `Callable` 值；`Any` 表示本功能块中的 `Any` 值。在“兼容函数接口与版本差异说明”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    connect: Callable[..., Any], *args: Any, **kwargs: Any
# 【L0012】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> Any:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“兼容函数接口与版本差异说明”。
) -> Any:
# 【L0013】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Disable sync-client keepalive only when the installed API supports it.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Disable sync-client keepalive only when the installed API supports it.
# 【L0014】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0015】语法拆解：表达式 `websockets 12 (bundled with Isaac Sim 5.1) has no sync-client` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `websockets 12 (bundled with Isaac Sim 5.1) has no sync-client`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    websockets 12 (bundled with Isaac Sim 5.1) has no sync-client
# 【L0016】语法拆解：```ping_interval`` parameter. websockets 15 (used by OpenPI) does. The` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 ```ping_interval`` parameter. websockets 15 (used by OpenPI) does. The`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    ``ping_interval`` parameter. websockets 15 (used by OpenPI) does. The
# 【L0017】语法拆解：`version check is based on the callable signature so vendored builds work.` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `version check is based on the callable signature so vendored builds work.`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    version check is based on the callable signature so vendored builds work.
# 【L0018】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“兼容函数接口与版本差异说明”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“兼容函数接口与版本差异说明”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：检查 connect 签名并安全添加/移除 ping_interval（源码第 20-25 行）

### 5.A 数据流位置

- 上游：模块 2“兼容函数接口与版本差异说明”。
- 本模块：检查 connect 签名并安全添加/移除 ping_interval。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“检查 connect 签名并安全添加/移除 ping_interval”。它服务于本文件要解决的总问题：Isaac Sim 5.1 的 websockets 版本不支持 OpenPI 客户端使用的同步 keepalive 参数，曾造成连接或超时故障。 这一组的处理结果会参与：检查函数签名；支持时禁用 ping，旧版本则移除不认识的参数。

### 5.D 本模块首次阅读要认识的调用

- `inspect.signature(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `kwargs.pop(...)`：圆括号表示真正执行调用；取出并删除指定键；这里常用于去掉旧版本 WebSocket 不认识的参数。
- `connect(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0020】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parameters`。右侧语法为：`inspect.signature(connect).parameters` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `parameters`，它在本项目中表示本功能块中的 `parameters` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `inspect.signature(connect).parameters`；`inspect` 表示本功能块中的 `inspect` 值；`signature` 表示本功能块中的 `signature` 值；`connect` 表示本功能块中的 `connect` 值。
    parameters = inspect.signature(connect).parameters
# 【L0021】语法拆解：`if` 要求条件 `"ping_interval" in parameters` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `"ping_interval" in parameters` 是否成立；`ping_interval` 表示本功能块中的 `ping_interval` 值；`parameters` 表示本功能块中的 `parameters` 值
    if "ping_interval" in parameters:
# 【L0022】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `kwargs["ping_interval"]`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】把右侧结果写进 `kwargs["ping_interval"]`（写入 `kwargs["ping_interval"]` 指定的字段）；右侧具体做的是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        kwargs["ping_interval"] = None
# 【L0023】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“检查 connect 签名并安全添加/移除 ping_interval”中处理剩余输入或备用路径。
    else:
# 【L0024】语法拆解：`kwargs` 是模块/对象，点号 `.` 从中取出 `pop` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"ping_interval"`；第 2 个实参 `None`。
# 【项目含义】对 `kwargs` 调用 `pop("ping_interval", None)`：取出并删除指定键；这里常用于去掉旧版本 WebSocket 不认识的参数。本行产生的修改/返回值服务于“检查 connect 签名并安全添加/移除 ping_interval”。
        kwargs.pop("ping_interval", None)
# 【L0025】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`connect` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `*args`；第 2 个实参 `**kwargs`。
# 【项目含义】结束当前函数并把 `connect(*args, **kwargs)` 交回调用者；这个值的含义是：计算表达式 `connect(*args, **kwargs)`；`connect` 表示本功能块中的 `connect` 值；`kwargs` 表示本功能块中的 `kwargs` 值。
    return connect(*args, **kwargs)
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“检查 connect 签名并安全添加/移除 ping_interval”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。