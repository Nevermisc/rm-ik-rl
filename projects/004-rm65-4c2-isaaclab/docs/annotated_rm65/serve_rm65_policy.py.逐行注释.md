# `serve_rm65_policy.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/serve_rm65_policy.py`
- 快照 SHA-256：`32da7661073bff57741f51666778d3bf7bef5a3b858ded4b0c4083d2bb497513`
- 总行数：58
- 程序作用：载入 RM65 微调 checkpoint，并通过 OpenPI 官方 WebSocket 协议持续提供 infer 服务。
- 推荐读法：重点看 31-37 的 checkpoint→policy，以及 48-53 的 policy→WebSocket server。

## 功能块地图

- 第 1-19 行：依赖、项目路径和 OpenPI 服务组件
- 第 22-29 行：服务参数
- 第 31-37 行：用同一 RM65 配置载入训练好的 checkpoint
- 第 38-53 行：服务元数据和永久监听
- 第 56-58 行：日志与入口

## 函数/类索引

- `main()`：第 22-53 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol."""
# 【L0003】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `logging` 引入 `logging`。在这份程序里，`logging` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import logging
# 【L0008】从 `socket` 引入 `socket`。在这份程序里，`socket` 用于TCP 端口探测与主机信息；后续出现这些名字时调用的是这里的外部能力。
import socket
# 【L0009】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0013】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0014】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0015】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和 OpenPI 服务组件”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0016】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0017】从 `openpi` 引入 `policy_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.policies import policy_config
# 【L0018】从 `openpi` 引入 `WebsocketPolicyServer`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.serving.websocket_policy_server import WebsocketPolicyServer
# 【L0019】从 `openpi_extension` 引入 `make_pi05_rm65_lora_config`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0020】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】定义函数 `main()`；调用者把参数交给它完成“服务参数”，后面的缩进代码是具体实现。
def main() -> None:
# 【L0023】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0024】声明命令行参数 `--checkpoint`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0025】声明命令行参数 `--repo-id`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0026】声明命令行参数 `--host`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--host", default="0.0.0.0")
# 【L0027】声明命令行参数 `--port`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--port", type=int, default=8000)
# 【L0028】声明命令行参数 `--default-prompt`；启动脚本可用它改变“服务参数”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--default-prompt", default="pick up the block and place it on the target")
# 【L0029】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0030】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0031】得到 `checkpoint`，它在本项目中表示一次训练保存的模型参数目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.checkpoint.expanduser().resolve()`；`checkpoint` 表示一次训练保存的模型参数目录；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0032】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建训练与推理共用的 RM65 π0.5/LoRA、数据 transform 和基础权重配置。
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
# 【L0033】得到 `policy`，它在本项目中表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：用 RM65 配置、checkpoint 和配套 norm stats 重建可调用 infer() 的 π0.5 policy。
    policy = policy_config.create_trained_policy(
# 【L0034】声明/传入参数 `config`；在本项目中它表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
        config,
# 【L0035】声明/传入参数 `checkpoint`；在本项目中它表示一次训练保存的模型参数目录。
        checkpoint,
# 【L0036】给上一层函数/配置构造器的命名参数 `default_prompt` 传入 `args.default_prompt`；该参数在本项目中表示本功能块中的 `default_prompt` 值，会参与“用同一 RM65 配置载入训练好的 checkpoint”。
        default_prompt=args.default_prompt,
# 【L0037】结束或闭合当前语法结构；它属于“用同一 RM65 配置载入训练好的 checkpoint”。
    )
# 【L0038】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    metadata = {
# 【L0039】定义字典/JSON 字段 `robot`，它表示“服务元数据和永久监听”中的 `robot` 数据；字段值来自 `"RM65-B"`，因此保存/传递的是这个表达式当前计算出的结果。
        "robot": "RM65-B",
# 【L0040】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `"4C2"`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper": "4C2",
# 【L0041】定义字典/JSON 字段 `model`，它表示“服务元数据和永久监听”中的 `model` 数据；字段值来自 `"pi0.5"`，因此保存/传递的是这个表达式当前计算出的结果。
        "model": "pi0.5",
# 【L0042】定义字典/JSON 字段 `checkpoint`，它表示“服务元数据和永久监听”中的 `checkpoint` 数据；字段值来自 `str(checkpoint)`，因此保存/传递的是这个表达式当前计算出的结果。
        "checkpoint": str(checkpoint),
# 【L0043】定义字典/JSON 字段 `repo_id`，它表示“服务元数据和永久监听”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0044】定义字典/JSON 字段 `action_semantics`，它表示“服务元数据和永久监听”中的 `action_semantics` 数据；字段值来自 `"six absolute joint targets plus normalized gripper target"`，因此保存/传递的是这个表达式当前计算出的结果。
        "action_semantics": "six absolute joint targets plus normalized gripper target",
# 【L0045】结束或闭合当前语法结构；它属于“服务元数据和永久监听”。
    }
# 【L0046】得到 `hostname`，它在本项目中表示本功能块中的 `hostname` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `socket.gethostname()`；`socket` 表示本功能块中的 `socket` 值；`gethostname` 表示本功能块中的 `gethostname` 值。
    hostname = socket.gethostname()
# 【L0047】对 `logging` 调用 `info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)`：调用 `logging` 提供的 `info` 操作。本行产生的修改/返回值服务于“服务元数据和永久监听”。
    logging.info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)
# 【L0048】开始调用多行函数 `WebsocketPolicyServer`；随后几行会逐项给它参数，调用结果或副作用用于“服务元数据和永久监听”。
    WebsocketPolicyServer(
# 【L0049】给上一层函数/配置构造器的命名参数 `policy` 传入 `policy`；该参数在本项目中表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象，会参与“服务元数据和永久监听”。
        policy=policy,
# 【L0050】给上一层函数/配置构造器的命名参数 `host` 传入 `args.host`；该参数在本项目中表示本功能块中的 `host` 值，会参与“服务元数据和永久监听”。
        host=args.host,
# 【L0051】给上一层函数/配置构造器的命名参数 `port` 传入 `args.port`；该参数在本项目中表示本功能块中的 `port` 值，会参与“服务元数据和永久监听”。
        port=args.port,
# 【L0052】给上一层函数/配置构造器的命名参数 `metadata` 传入 `metadata`；该参数在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息，会参与“服务元数据和永久监听”。
        metadata=metadata,
# 【L0053】对 `)` 调用 `serve_forever()`：调用 `)` 提供的 `serve_forever` 操作。本行产生的修改/返回值服务于“服务元数据和永久监听”。
    ).serve_forever()
# 【L0054】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0056】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0057】对 `logging` 调用 `basicConfig(level=logging.INFO, force=True)`：调用 `logging` 提供的 `basicConfig` 操作。本行产生的修改/返回值服务于“日志与入口”。
    logging.basicConfig(level=logging.INFO, force=True)
# 【L0058】调用本文件的 `main()`，从这里正式进入参数解析、资源创建和主任务流程；上面的函数此时才开始被实际使用。
    main()
```
