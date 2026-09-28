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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Serve an RM65-specific π0.5 checkpoint over OpenPI's WebSocket protocol."""
# 【L0003】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 logging：项目或第三方模块；后面的代码会调用其中的类或函数。
import logging
# 【L0008】导入 socket：TCP 端口探测与主机信息；后面的代码会调用其中的类或函数。
import socket
# 【L0009】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0010】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0011】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0013】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和 OpenPI 服务组件”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0014】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0015】执行“依赖、项目路径和 OpenPI 服务组件”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0016】空行：分隔“依赖、项目路径和 OpenPI 服务组件”中的逻辑段，让结构更容易看清。

# 【L0017】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.policies import policy_config
# 【L0018】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.serving.websocket_policy_server import WebsocketPolicyServer
# 【L0019】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0020】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】定义函数 main；其职责属于“服务参数”，缩进块是函数体。
def main() -> None:
# 【L0023】计算并保存变量 `parser`；该值服务于“服务参数”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0024】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0025】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0026】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--host", default="0.0.0.0")
# 【L0027】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--port", type=int, default=8000)
# 【L0028】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--default-prompt", default="pick up the block and place it on the target")
# 【L0029】计算并保存变量 `args`；该值服务于“服务参数”。
    args = parser.parse_args()
# 【L0030】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0031】给变量 `checkpoint` 赋值：一次训练保存的模型参数目录。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0032】给变量 `config` 赋值：当前函数使用的配置对象。
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
# 【L0033】计算并保存变量 `policy`；该值服务于“用同一 RM65 配置载入训练好的 checkpoint”。
    policy = policy_config.create_trained_policy(
# 【L0034】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“用同一 RM65 配置载入训练好的 checkpoint”。
        config,
# 【L0035】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“用同一 RM65 配置载入训练好的 checkpoint”。
        checkpoint,
# 【L0036】计算并保存变量 `default_prompt`；该值服务于“用同一 RM65 配置载入训练好的 checkpoint”。
        default_prompt=args.default_prompt,
# 【L0037】结束或闭合当前语法结构；它属于“用同一 RM65 配置载入训练好的 checkpoint”。
    )
# 【L0038】计算并保存变量 `metadata`；该值服务于“服务元数据和永久监听”。
    metadata = {
# 【L0039】定义字典/JSON 字段 `robot`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "robot": "RM65-B",
# 【L0040】定义字典/JSON 字段 `gripper`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "gripper": "4C2",
# 【L0041】定义字典/JSON 字段 `model`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "model": "pi0.5",
# 【L0042】定义字典/JSON 字段 `checkpoint`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "checkpoint": str(checkpoint),
# 【L0043】定义字典/JSON 字段 `repo_id`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "repo_id": args.repo_id,
# 【L0044】定义字典/JSON 字段 `action_semantics`；它把“服务元数据和永久监听”中的结果用稳定键名记录下来。
        "action_semantics": "six absolute joint targets plus normalized gripper target",
# 【L0045】结束或闭合当前语法结构；它属于“服务元数据和永久监听”。
    }
# 【L0046】计算并保存变量 `hostname`；该值服务于“服务元数据和永久监听”。
    hostname = socket.gethostname()
# 【L0047】执行“服务元数据和永久监听”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    logging.info("Creating RM65 policy server (host=%s, listen=%s:%d)", hostname, args.host, args.port)
# 【L0048】执行“服务元数据和永久监听”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    WebsocketPolicyServer(
# 【L0049】计算并保存变量 `policy`；该值服务于“服务元数据和永久监听”。
        policy=policy,
# 【L0050】计算并保存变量 `host`；该值服务于“服务元数据和永久监听”。
        host=args.host,
# 【L0051】计算并保存变量 `port`；该值服务于“服务元数据和永久监听”。
        port=args.port,
# 【L0052】计算并保存变量 `metadata`；该值服务于“服务元数据和永久监听”。
        metadata=metadata,
# 【L0053】执行“服务元数据和永久监听”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ).serve_forever()
# 【L0054】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0056】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0057】执行“日志与入口”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    logging.basicConfig(level=logging.INFO, force=True)
# 【L0058】执行“日志与入口”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    main()
```
