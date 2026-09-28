# `websocket_compat.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/websocket_compat.py`
- 快照 SHA-256：`e691766070778e159598ef7bc26039daca43194e5614f006f35c4f6ec95cbb5f`
- 总行数：25
- 程序作用：兼容 Isaac Sim 自带 websockets 12 与 OpenPI 环境 websockets 15 的 connect 参数差异，并在支持时关闭 keepalive。
- 推荐读法：这个小文件正是早期 keepalive ping timeout 问题的工程化修复。

## 功能块地图

- 第 1-8 行：反射和类型依赖
- 第 10-18 行：兼容函数接口与版本差异说明
- 第 20-25 行：检查 connect 签名并安全添加/移除 ping_interval

## 函数/类索引

- `call_connect_without_keepalive()`：第 10-25 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】说明字符串 `Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim."""
# 【L0002】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0003】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0005】从 `inspect` 引入 `inspect`。在这份程序里，`inspect` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import inspect
# 【L0006】从 `collections` 引入 `Callable`。在这份程序里，`collections` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from collections.abc import Callable
# 【L0007】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0008】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0009】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0010】定义函数 `call_connect_without_keepalive(参数在后续行继续)`；调用者把参数交给它完成“兼容函数接口与版本差异说明”，后面的缩进代码是具体实现。
def call_connect_without_keepalive(
# 【L0011】把表达式/参数 `connect: Callable[..., Any], *args: Any, **kwargs: Any` 接入当前完整语句；`connect` 表示本功能块中的 `connect` 值；`Callable` 表示本功能块中的 `Callable` 值；`Any` 表示本功能块中的 `Any` 值。在“兼容函数接口与版本差异说明”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    connect: Callable[..., Any], *args: Any, **kwargs: Any
# 【L0012】以 `) -> Any:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“兼容函数接口与版本差异说明”。
) -> Any:
# 【L0013】说明字符串 `Disable sync-client keepalive only when the installed API supports it.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Disable sync-client keepalive only when the installed API supports it.
# 【L0014】继续说明字符串，原文是 ``；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0015】继续说明字符串，原文是 `websockets 12 (bundled with Isaac Sim 5.1) has no sync-client`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    websockets 12 (bundled with Isaac Sim 5.1) has no sync-client
# 【L0016】继续说明字符串，原文是 ```ping_interval`` parameter. websockets 15 (used by OpenPI) does. The`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    ``ping_interval`` parameter. websockets 15 (used by OpenPI) does. The
# 【L0017】继续说明字符串，原文是 `version check is based on the callable signature so vendored builds work.`；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    version check is based on the callable signature so vendored builds work.
# 【L0018】继续说明字符串，原文是 ``；这段文字在解释“兼容函数接口与版本差异说明”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】得到 `parameters`，它在本项目中表示本功能块中的 `parameters` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `inspect.signature(connect).parameters`；`inspect` 表示本功能块中的 `inspect` 值；`signature` 表示本功能块中的 `signature` 值；`connect` 表示本功能块中的 `connect` 值。
    parameters = inspect.signature(connect).parameters
# 【L0021】判断 `"ping_interval" in parameters` 是否成立；`ping_interval` 表示本功能块中的 `ping_interval` 值；`parameters` 表示本功能块中的 `parameters` 值
    if "ping_interval" in parameters:
# 【L0022】把右侧结果写进 `kwargs["ping_interval"]`（写入 `kwargs["ping_interval"]` 指定的字段）；右侧具体做的是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        kwargs["ping_interval"] = None
# 【L0023】前面的 `if/elif` 都不成立时走这里；在“检查 connect 签名并安全添加/移除 ping_interval”中处理剩余输入或备用路径。
    else:
# 【L0024】对 `kwargs` 调用 `pop("ping_interval", None)`：取出并删除指定键；这里常用于去掉旧版本 WebSocket 不认识的参数。本行产生的修改/返回值服务于“检查 connect 签名并安全添加/移除 ping_interval”。
        kwargs.pop("ping_interval", None)
# 【L0025】结束当前函数并把 `connect(*args, **kwargs)` 交回调用者；这个值的含义是：计算表达式 `connect(*args, **kwargs)`；`connect` 表示本功能块中的 `connect` 值；`kwargs` 表示本功能块中的 `kwargs` 值。
    return connect(*args, **kwargs)
```
