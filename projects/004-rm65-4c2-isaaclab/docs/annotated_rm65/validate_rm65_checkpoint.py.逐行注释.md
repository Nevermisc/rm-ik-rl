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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Run one recorded RM65 observation through a trained π0.5 checkpoint."""
# 【L0003】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0009】导入 time：计时和短暂等待；后面的代码会调用其中的类或函数。
import time
# 【L0010】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0011】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0012】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0013】导入 PIL：Pillow 图像库，用于 PNG/RGB 读写；后面的代码会调用其中的类或函数。
from PIL import Image
# 【L0014】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0015】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0016】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和 RGB 读取”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】执行“依赖、项目路径和 RGB 读取”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0020】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.policies import policy_config
# 【L0021】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.action_guard import guard_action_chunk
# 【L0022】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0023】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0024】空行：分隔“依赖、项目路径和 RGB 读取”中的逻辑段，让结构更容易看清。

# 【L0025】定义函数 read_rgb；其职责属于“依赖、项目路径和 RGB 读取”，缩进块是函数体。
def read_rgb(path: Path) -> np.ndarray:
# 【L0026】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with Image.open(path) as image:
# 【L0027】结束当前函数并把结果交给调用者；这里完成“依赖、项目路径和 RGB 读取”的输出。
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
# 【L0028】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0029】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0030】定义函数 main；其职责属于“参数、checkpoint/episode 和帧索引校验”，缩进块是函数体。
def main() -> int:
# 【L0031】计算并保存变量 `parser`；该值服务于“参数、checkpoint/episode 和帧索引校验”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0032】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--checkpoint", type=Path, required=True)
# 【L0033】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--episode", type=Path, required=True)
# 【L0034】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0035】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--frame-index", type=int, default=0)
# 【L0036】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--output", type=Path)
# 【L0037】计算并保存变量 `args`；该值服务于“参数、checkpoint/episode 和帧索引校验”。
    args = parser.parse_args()
# 【L0038】空行：分隔“参数、checkpoint/episode 和帧索引校验”中的逻辑段，让结构更容易看清。

# 【L0039】给变量 `checkpoint` 赋值：一次训练保存的模型参数目录。
    checkpoint = args.checkpoint.expanduser().resolve()
# 【L0040】计算并保存变量 `episode`；该值服务于“参数、checkpoint/episode 和帧索引校验”。
    episode = args.episode.expanduser().resolve()
# 【L0041】调用 `read_text`：从磁盘读取文本。本行位于“参数、checkpoint/episode 和帧索引校验”。
    metadata = json.loads((episode / "metadata.json").read_text(encoding="utf-8"))
# 【L0042】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with np.load(episode / "episode.npz") as arrays:
# 【L0043】计算并保存变量 `states`；该值服务于“参数、checkpoint/episode 和帧索引校验”。
        states = arrays["observation_state"].astype(np.float32, copy=True)
# 【L0044】计算并保存变量 `index`；该值服务于“参数、checkpoint/episode 和帧索引校验”。
    index = args.frame_index
# 【L0045】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0 <= index < len(states):
# 【L0046】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise IndexError(f"frame index {index} outside [0, {len(states)})")
# 【L0047】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0048】给变量 `observation` 赋值：本次发给 π0.5 的图像、状态和文字指令字典。
    observation = {
# 【L0049】定义字典/JSON 字段 `observation/joint_position`；它把“从记录 episode 复原一次完整 RM65 观测”中的结果用稳定键名记录下来。
        "observation/joint_position": states[index, :6],
# 【L0050】定义字典/JSON 字段 `observation/gripper_position`；它把“从记录 episode 复原一次完整 RM65 观测”中的结果用稳定键名记录下来。
        "observation/gripper_position": states[index, 6:7],
# 【L0051】定义字典/JSON 字段 `observation/external_image`；它把“从记录 episode 复原一次完整 RM65 观测”中的结果用稳定键名记录下来。
        "observation/external_image": read_rgb(
# 【L0052】执行“从记录 episode 复原一次完整 RM65 观测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode / metadata["image_paths"]["external"][index]
# 【L0053】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
        ),
# 【L0054】定义字典/JSON 字段 `observation/wrist_image`；它把“从记录 episode 复原一次完整 RM65 观测”中的结果用稳定键名记录下来。
        "observation/wrist_image": read_rgb(
# 【L0055】执行“从记录 episode 复原一次完整 RM65 观测”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode / metadata["image_paths"]["wrist"][index]
# 【L0056】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
        ),
# 【L0057】定义字典/JSON 字段 `prompt`；它把“从记录 episode 复原一次完整 RM65 观测”中的结果用稳定键名记录下来。
        "prompt": metadata["prompt"],
# 【L0058】结束或闭合当前语法结构；它属于“从记录 episode 复原一次完整 RM65 观测”。
    }
# 【L0059】给变量 `config` 赋值：当前函数使用的配置对象。
    config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)
# 【L0060】计算并保存变量 `start`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    start = time.perf_counter()
# 【L0061】计算并保存变量 `policy`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    policy = policy_config.create_trained_policy(config, checkpoint)
# 【L0062】计算并保存变量 `load_seconds`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    load_seconds = time.perf_counter() - start
# 【L0063】计算并保存变量 `start`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    start = time.perf_counter()
# 【L0064】计算并保存变量 `result`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    result = policy.infer(observation)
# 【L0065】计算并保存变量 `inference_seconds`；该值服务于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    inference_seconds = time.perf_counter() - start
# 【L0066】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    actions = np.asarray(result["actions"], dtype=np.float32)
# 【L0067】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if actions.shape != (config.model.action_horizon, 7):
# 【L0068】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"expected actions {(config.model.action_horizon, 7)}, got {actions.shape}")
# 【L0069】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not np.isfinite(actions).all():
# 【L0070】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("checkpoint returned non-finite actions")
# 【L0071】调用 `guard_action_chunk`：验证并裁剪策略动作，阻止越界和过大跳变。本行位于“载入 checkpoint、计时推理并验证动作形状/有限数/guard”。
    safe_actions, guard = guard_action_chunk(actions, states[index, :6])
# 【L0072】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0073】定义字典/JSON 字段 `status`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0074】定义字典/JSON 字段 `simulation_only`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L0075】定义字典/JSON 字段 `real_robot_command_sent`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L0076】定义字典/JSON 字段 `checkpoint`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "checkpoint": str(checkpoint),
# 【L0077】定义字典/JSON 字段 `episode`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "episode": str(episode),
# 【L0078】定义字典/JSON 字段 `frame_index`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "frame_index": index,
# 【L0079】定义字典/JSON 字段 `prompt`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "prompt": metadata["prompt"],
# 【L0080】定义字典/JSON 字段 `load_seconds`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "load_seconds": load_seconds,
# 【L0081】定义字典/JSON 字段 `inference_seconds`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "inference_seconds": inference_seconds,
# 【L0082】定义字典/JSON 字段 `actions_shape`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "actions_shape": list(actions.shape),
# 【L0083】定义字典/JSON 字段 `all_actions_finite`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "all_actions_finite": True,
# 【L0084】定义字典/JSON 字段 `first_raw_action`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "first_raw_action": actions[0].tolist(),
# 【L0085】定义字典/JSON 字段 `first_guarded_action`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "first_guarded_action": safe_actions[0].tolist(),
# 【L0086】定义字典/JSON 字段 `guard`；它把“写出离线 checkpoint 验证报告”中的结果用稳定键名记录下来。
        "guard": guard,
# 【L0087】结束或闭合当前语法结构；它属于“写出离线 checkpoint 验证报告”。
    }
# 【L0088】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“写出离线 checkpoint 验证报告”。
    text = json.dumps(report, indent=2) + "\n"
# 【L0089】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.output is not None:
# 【L0090】调用 `mkdir`：创建目录。本行位于“写出离线 checkpoint 验证报告”。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0091】调用 `write_text`：把文本写入磁盘文件。本行位于“写出离线 checkpoint 验证报告”。
        args.output.write_text(text, encoding="utf-8")
# 【L0092】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(text, end="")
# 【L0093】结束当前函数并把结果交给调用者；这里完成“写出离线 checkpoint 验证报告”的输出。
    return 0
# 【L0094】空行：分隔“写出离线 checkpoint 验证报告”中的逻辑段，让结构更容易看清。

# 【L0095】空行：分隔“写出离线 checkpoint 验证报告”中的逻辑段，让结构更容易看清。

# 【L0096】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0097】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
