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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Compatibility helpers for websockets versions bundled by OpenPI and Isaac Sim."""
# 【L0002】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0003】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0004】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0005】导入 inspect：项目或第三方模块；后面的代码会调用其中的类或函数。
import inspect
# 【L0006】导入 collections：项目或第三方模块；后面的代码会调用其中的类或函数。
from collections.abc import Callable
# 【L0007】导入 typing：项目或第三方模块；后面的代码会调用其中的类或函数。
from typing import Any
# 【L0008】空行：分隔“反射和类型依赖”中的逻辑段，让结构更容易看清。

# 【L0009】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0010】定义函数 call_connect_without_keepalive；其职责属于“兼容函数接口与版本差异说明”，缩进块是函数体。
def call_connect_without_keepalive(
# 【L0011】执行“兼容函数接口与版本差异说明”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    connect: Callable[..., Any], *args: Any, **kwargs: Any
# 【L0012】开始一个缩进代码块或键值结构；该块负责“兼容函数接口与版本差异说明”。
) -> Any:
# 【L0013】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Disable sync-client keepalive only when the installed API supports it.
# 【L0014】空行：分隔“兼容函数接口与版本差异说明”中的逻辑段，让结构更容易看清。

# 【L0015】执行“兼容函数接口与版本差异说明”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    websockets 12 (bundled with Isaac Sim 5.1) has no sync-client
# 【L0016】执行“兼容函数接口与版本差异说明”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ``ping_interval`` parameter. websockets 15 (used by OpenPI) does. The
# 【L0017】执行“兼容函数接口与版本差异说明”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    version check is based on the callable signature so vendored builds work.
# 【L0018】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】计算并保存变量 `parameters`；该值服务于“检查 connect 签名并安全添加/移除 ping_interval”。
    parameters = inspect.signature(connect).parameters
# 【L0021】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if "ping_interval" in parameters:
# 【L0022】执行“检查 connect 签名并安全添加/移除 ping_interval”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        kwargs["ping_interval"] = None
# 【L0023】否则分支：前面的 if/elif 都不成立时执行。
    else:
# 【L0024】执行“检查 connect 签名并安全添加/移除 ping_interval”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        kwargs.pop("ping_interval", None)
# 【L0025】结束当前函数并把结果交给调用者；这里完成“检查 connect 签名并安全添加/移除 ping_interval”的输出。
    return connect(*args, **kwargs)
```
