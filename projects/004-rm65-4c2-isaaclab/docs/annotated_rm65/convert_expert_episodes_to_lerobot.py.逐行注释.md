# `convert_expert_episodes_to_lerobot.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/convert_expert_episodes_to_lerobot.py`
- 快照 SHA-256：`508752a43b97645d9d83b152ef28f93ba344933827ad589d6ab9e4d0861583f1`
- 总行数：255
- 程序作用：把便于调试的本地 episode 格式转换成 OpenPI 能训练的 LeRobot 数据集。
- 推荐读法：重点跟踪同一帧如何从 episode.npz/images 变成 image、wrist_image、joints、gripper、actions、task。

## 功能块地图

- 第 1-20 行：依赖、项目路径和校验函数
- 第 23-47 行：读取且只接收成功、图像完整的 episode
- 第 50-91 行：可选策略窗口：减少大量静止标签
- 第 94-96 行：读取 RGB PNG
- 第 99-135 行：发现所有 episode 并检查帧率、维度和相机尺寸一致
- 第 138-180 行：命令行、选择 split、定位 LeRobot 输出目录
- 第 182-206 行：声明 LeRobot 数据集 schema
- 第 207-232 行：逐 episode、逐帧写入数据集
- 第 234-255 行：输出转换统计与脚本退出码

## 函数/类索引

- `load_episode()`：第 23-47 行
- `select_policy_window_indices()`：第 50-91 行
- `read_rgb()`：第 94-96 行
- `discover_episodes()`：第 99-135 行
- `main()`：第 138-251 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema."""
# 【L0003】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 shutil：标准库文件目录操作；后面的代码会调用其中的类或函数。
import shutil
# 【L0009】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0010】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0011】导入 typing：项目或第三方模块；后面的代码会调用其中的类或函数。
from typing import Any
# 【L0012】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0013】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0014】导入 PIL：Pillow 图像库，用于 PNG/RGB 读写；后面的代码会调用其中的类或函数。
from PIL import Image
# 【L0015】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0016】调用 `Path`：创建路径对象。本行位于“依赖、项目路径和校验函数”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】执行“依赖、项目路径和校验函数”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0020】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.expert_episode import validate_episode
# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】定义函数 load_episode；其职责属于“读取且只接收成功、图像完整的 episode”，缩进块是函数体。
def load_episode(directory: Path) -> dict[str, Any]:
# 【L0024】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Load and validate one successful episode without requiring LeRobot."""
# 【L0025】空行：分隔“读取且只接收成功、图像完整的 episode”中的逻辑段，让结构更容易看清。

# 【L0026】计算并保存变量 `validation`；该值服务于“读取且只接收成功、图像完整的 episode”。
    validation = validate_episode(directory, require_images=True)
# 【L0027】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if validation["status"] != "pass":
# 【L0028】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"invalid episode {directory}: {validation['errors']}")
# 【L0029】调用 `read_text`：从磁盘读取文本。本行位于“读取且只接收成功、图像完整的 episode”。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0030】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if manifest.get("metadata", {}).get("task_success") is not True:
# 【L0031】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"episode is not marked successful: {directory}")
# 【L0032】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with np.load(directory / "episode.npz") as arrays:
# 【L0033】计算并保存变量 `states`；该值服务于“读取且只接收成功、图像完整的 episode”。
        states = arrays["observation_state"].astype(np.float32, copy=True)
# 【L0034】给变量 `actions` 赋值：一个动作块；形状通常为 (时间步数, 7)。
        actions = arrays["action"].astype(np.float32, copy=True)
# 【L0035】计算并保存变量 `phase_ids`；该值服务于“读取且只接收成功、图像完整的 episode”。
        phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
# 【L0036】结束当前函数并把结果交给调用者；这里完成“读取且只接收成功、图像完整的 episode”的输出。
    return {
# 【L0037】定义字典/JSON 字段 `directory`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "directory": directory,
# 【L0038】定义字典/JSON 字段 `prompt`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "prompt": manifest["prompt"],
# 【L0039】定义字典/JSON 字段 `fps`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "fps": float(manifest["control_hz"]),
# 【L0040】定义字典/JSON 字段 `states`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "states": states,
# 【L0041】定义字典/JSON 字段 `actions`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "actions": actions,
# 【L0042】定义字典/JSON 字段 `phase_ids`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "phase_ids": phase_ids,
# 【L0043】定义字典/JSON 字段 `phase_names`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "phase_names": manifest["phase_names"],
# 【L0044】定义字典/JSON 字段 `external_paths`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "external_paths": manifest["image_paths"]["external"],
# 【L0045】定义字典/JSON 字段 `wrist_paths`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "wrist_paths": manifest["image_paths"]["wrist"],
# 【L0046】定义字典/JSON 字段 `collection_split`；它把“读取且只接收成功、图像完整的 episode”中的结果用稳定键名记录下来。
        "collection_split": manifest.get("metadata", {}).get("collection_split"),
# 【L0047】结束或闭合当前语法结构；它属于“读取且只接收成功、图像完整的 episode”。
    }
# 【L0048】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0049】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0050】定义函数 select_policy_window_indices；其职责属于“可选策略窗口：减少大量静止标签”，缩进块是函数体。
def select_policy_window_indices(episode: dict[str, Any]) -> np.ndarray:
# 【L0051】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Keep control-relevant motion while reducing ambiguous stationary labels.
# 【L0052】空行：分隔“可选策略窗口：减少大量静止标签”中的逻辑段，让结构更容易看清。

# 【L0053】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    The full portable episode remains unchanged. This optional view retains the
# 【L0054】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
    last two frames of pre-transition holds, the first 15 release-settle frames,
# 【L0055】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    and every motion frame through release. Retreat and final-settle frames are
# 【L0056】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    omitted because the closed-loop success detector stops after stable release.
# 【L0057】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0058】空行：分隔“可选策略窗口：减少大量静止标签”中的逻辑段，让结构更容易看清。

# 【L0059】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“可选策略窗口：减少大量静止标签”。
    phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
# 【L0060】计算并保存变量 `phase_names`；该值服务于“可选策略窗口：减少大量静止标签”。
    phase_names = episode["phase_names"]
# 【L0061】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“可选策略窗口：减少大量静止标签”。
    phases = np.asarray([phase_names[int(index)] for index in phase_ids], dtype=object)
# 【L0062】调用 `np.array`：创建 NumPy 数组。本行位于“可选策略窗口：减少大量静止标签”。
    motion_mask = np.array(
# 【L0063】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“可选策略窗口：减少大量静止标签”。
        [
# 【L0064】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            phase.startswith("APPROACH_")
# 【L0065】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            or phase.startswith("PLACE_DESCENT_")
# 【L0066】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            or phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}
# 【L0067】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for phase in phases
# 【L0068】结束或闭合当前语法结构；它属于“可选策略窗口：减少大量静止标签”。
        ],
# 【L0069】计算并保存变量 `dtype`；该值服务于“可选策略窗口：减少大量静止标签”。
        dtype=bool,
# 【L0070】结束或闭合当前语法结构；它属于“可选策略窗口：减少大量静止标签”。
    )
# 【L0071】调用 `np.flatnonzero`：返回布尔条件为真的扁平索引。本行位于“可选策略窗口：减少大量静止标签”。
    selected = set(np.flatnonzero(motion_mask).tolist())
# 【L0072】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for phase in (
# 【L0073】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "SOURCE_SETTLE",
# 【L0074】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "GRASP_HOLD",
# 【L0075】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "CLOSE_HOLD",
# 【L0076】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "LIFT_HOLD",
# 【L0077】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "TARGET_COLLISION_HOLD",
# 【L0078】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“可选策略窗口：减少大量静止标签”。
        "PLACE_HOLD",
# 【L0079】开始一个缩进代码块或键值结构；该块负责“可选策略窗口：减少大量静止标签”。
    ):
# 【L0080】调用 `np.flatnonzero`：返回布尔条件为真的扁平索引。本行位于“可选策略窗口：减少大量静止标签”。
        indices = np.flatnonzero(phases == phase)
# 【L0081】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        selected.update(indices[-2:].tolist())
# 【L0082】调用 `np.flatnonzero`：返回布尔条件为真的扁平索引。本行位于“可选策略窗口：减少大量静止标签”。
    release_indices = np.flatnonzero(phases == "RELEASE_SETTLE")
# 【L0083】执行“可选策略窗口：减少大量静止标签”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    selected.update(release_indices[:15].tolist())
# 【L0084】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“可选策略窗口：减少大量静止标签”。
    result = np.asarray(sorted(selected), dtype=np.int64)
# 【L0085】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(result) == 0:
# 【L0086】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"episode contains no recognized policy phases: {episode['directory']}")
# 【L0087】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if phases[result[0]] != "SOURCE_SETTLE":
# 【L0088】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("policy window must begin with a SOURCE_SETTLE transition frame")
# 【L0089】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if "OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]:
# 【L0090】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("policy window must contain OPEN and RELEASE_SETTLE")
# 【L0091】结束当前函数并把结果交给调用者；这里完成“可选策略窗口：减少大量静止标签”的输出。
    return result
# 【L0092】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0093】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0094】定义函数 read_rgb；其职责属于“读取 RGB PNG”，缩进块是函数体。
def read_rgb(path: Path) -> np.ndarray:
# 【L0095】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with Image.open(path) as image:
# 【L0096】结束当前函数并把结果交给调用者；这里完成“读取 RGB PNG”的输出。
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
# 【L0097】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0098】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0099】定义函数 discover_episodes；其职责属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”，缩进块是函数体。
def discover_episodes(
# 【L0100】调用 `Path`：创建路径对象。本行位于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    dataset_root: Path, *, collection_split: str | None = None
# 【L0101】开始一个缩进代码块或键值结构；该块负责“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
) -> list[dict[str, Any]]:
# 【L0102】计算并保存变量 `directories`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    directories = sorted(
# 【L0103】执行“发现所有 episode 并检查帧率、维度和相机尺寸一致”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        path.parent for path in dataset_root.glob("episode_*/metadata.json")
# 【L0104】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    )
# 【L0105】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not directories:
# 【L0106】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")
# 【L0107】计算并保存变量 `episodes`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    episodes = [load_episode(directory) for directory in directories]
# 【L0108】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if collection_split is not None:
# 【L0109】计算并保存变量 `episodes`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        episodes = [
# 【L0110】执行“发现所有 episode 并检查帧率、维度和相机尺寸一致”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode
# 【L0111】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for episode in episodes
# 【L0112】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if episode["collection_split"] == collection_split
# 【L0113】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        ]
# 【L0114】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not episodes:
# 【L0115】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(
# 【L0116】执行“发现所有 episode 并检查帧率、维度和相机尺寸一致”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                f"no episodes use collection split {collection_split!r}"
# 【L0117】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
            )
# 【L0118】计算并保存变量 `fps_values`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    fps_values = {round(item["fps"], 9) for item in episodes}
# 【L0119】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(fps_values) != 1:
# 【L0120】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")
# 【L0121】计算并保存变量 `first`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    first = episodes[0]
# 【L0122】计算并保存变量 `first_external`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    first_external = read_rgb(first["directory"] / first["external_paths"][0])
# 【L0123】计算并保存变量 `first_wrist`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])
# 【L0124】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for episode in episodes:
# 【L0125】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,):
# 【L0126】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"unexpected state/action dimensions in {episode['directory']}")
# 【L0127】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if len(episode["external_paths"]) != len(episode["states"]):
# 【L0128】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"external image count changed in {episode['directory']}")
# 【L0129】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if len(episode["wrist_paths"]) != len(episode["states"]):
# 【L0130】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"wrist image count changed in {episode['directory']}")
# 【L0131】计算并保存变量 `external_shape`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        external_shape = read_rgb(episode["directory"] / episode["external_paths"][0]).shape
# 【L0132】计算并保存变量 `wrist_shape`；该值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        wrist_shape = read_rgb(episode["directory"] / episode["wrist_paths"][0]).shape
# 【L0133】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if external_shape != first_external.shape or wrist_shape != first_wrist.shape:
# 【L0134】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("camera shapes must remain constant across all episodes")
# 【L0135】结束当前函数并把结果交给调用者；这里完成“发现所有 episode 并检查帧率、维度和相机尺寸一致”的输出。
    return episodes
# 【L0136】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0137】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0138】定义函数 main；其职责属于“命令行、选择 split、定位 LeRobot 输出目录”，缩进块是函数体。
def main() -> int:
# 【L0139】计算并保存变量 `parser`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0140】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("dataset_root", type=Path)
# 【L0141】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--repo-id", required=True, help="LeRobot repository id, e.g. local/rm65_sim")
# 【L0142】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--overwrite", action="store_true")
# 【L0143】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0144】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行、选择 split、定位 LeRobot 输出目录”。
        "--split",
# 【L0145】计算并保存变量 `choices`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
        choices=("train", "validation"),
# 【L0146】计算并保存变量 `help`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
        help="Convert only the declared collection split.",
# 【L0147】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0148】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0149】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行、选择 split、定位 LeRobot 输出目录”。
        "--policy-window",
# 【L0150】计算并保存变量 `action`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
        action="store_true",
# 【L0151】计算并保存变量 `help`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
        help=(
# 【L0152】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "Compress stationary holds and omit post-success retreat/final settle. "
# 【L0153】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "Use a new repo id; the source episodes are never modified."
# 【L0154】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
        ),
# 【L0155】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0156】计算并保存变量 `args`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    args = parser.parse_args()
# 【L0157】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0158】计算并保存变量 `episodes`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    episodes = discover_episodes(
# 【L0159】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        args.dataset_root.expanduser().resolve(), collection_split=args.split
# 【L0160】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0161】计算并保存变量 `fps`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    fps = episodes[0]["fps"]
# 【L0162】计算并保存变量 `rounded_fps`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    rounded_fps = round(fps)
# 【L0163】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not np.isclose(fps, rounded_fps):
# 【L0164】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"LeRobot conversion requires an integer fps, got {fps}")
# 【L0165】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0166】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
    try:
# 【L0167】导入 lerobot：项目或第三方模块；后面的代码会调用其中的类或函数。
        from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset
# 【L0168】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
    except ImportError as error:
# 【L0169】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0170】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."
# 【L0171】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ) from error
# 【L0172】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0173】计算并保存变量 `output_path`；该值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
    output_path = (HF_LEROBOT_HOME / args.repo_id).resolve()
# 【L0174】调用 `Path`：创建路径对象。本行位于“命令行、选择 split、定位 LeRobot 输出目录”。
    hf_home = Path(HF_LEROBOT_HOME).resolve()
# 【L0175】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if hf_home not in output_path.parents:
# 【L0176】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("repo id resolves outside HF_LEROBOT_HOME")
# 【L0177】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if output_path.exists():
# 【L0178】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not args.overwrite:
# 【L0179】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")
# 【L0180】执行“命令行、选择 split、定位 LeRobot 输出目录”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        shutil.rmtree(output_path)
# 【L0181】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0182】计算并保存变量 `first`；该值服务于“声明 LeRobot 数据集 schema”。
    first = episodes[0]
# 【L0183】计算并保存变量 `external_shape`；该值服务于“声明 LeRobot 数据集 schema”。
    external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape
# 【L0184】计算并保存变量 `wrist_shape`；该值服务于“声明 LeRobot 数据集 schema”。
    wrist_shape = read_rgb(first["directory"] / first["wrist_paths"][0]).shape
# 【L0185】给变量 `dataset` 赋值：LeRobotDataset 对象，用于逐帧构造训练集。
    dataset = LeRobotDataset.create(
# 【L0186】计算并保存变量 `repo_id`；该值服务于“声明 LeRobot 数据集 schema”。
        repo_id=args.repo_id,
# 【L0187】计算并保存变量 `robot_type`；该值服务于“声明 LeRobot 数据集 schema”。
        robot_type="rm65_4c2",
# 【L0188】计算并保存变量 `fps`；该值服务于“声明 LeRobot 数据集 schema”。
        fps=int(rounded_fps),
# 【L0189】计算并保存变量 `features`；该值服务于“声明 LeRobot 数据集 schema”。
        features={
# 【L0190】定义字典/JSON 字段 `image`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
            "image": {
# 【L0191】定义字典/JSON 字段 `dtype`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "dtype": "image",
# 【L0192】定义字典/JSON 字段 `shape`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "shape": external_shape,
# 【L0193】定义字典/JSON 字段 `names`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "names": ["height", "width", "channel"],
# 【L0194】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
            },
# 【L0195】定义字典/JSON 字段 `wrist_image`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
            "wrist_image": {
# 【L0196】定义字典/JSON 字段 `dtype`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "dtype": "image",
# 【L0197】定义字典/JSON 字段 `shape`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "shape": wrist_shape,
# 【L0198】定义字典/JSON 字段 `names`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
                "names": ["height", "width", "channel"],
# 【L0199】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
            },
# 【L0200】定义字典/JSON 字段 `joints`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
            "joints": {"dtype": "float32", "shape": (6,), "names": ["joints"]},
# 【L0201】定义字典/JSON 字段 `gripper`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
            "gripper": {"dtype": "float32", "shape": (1,), "names": ["gripper"]},
# 【L0202】定义字典/JSON 字段 `actions`；它把“声明 LeRobot 数据集 schema”中的结果用稳定键名记录下来。
            "actions": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
# 【L0203】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
        },
# 【L0204】计算并保存变量 `image_writer_threads`；该值服务于“声明 LeRobot 数据集 schema”。
        image_writer_threads=10,
# 【L0205】计算并保存变量 `image_writer_processes`；该值服务于“声明 LeRobot 数据集 schema”。
        image_writer_processes=5,
# 【L0206】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
    )
# 【L0207】计算并保存变量 `total_frames`；该值服务于“逐 episode、逐帧写入数据集”。
    total_frames = 0
# 【L0208】计算并保存变量 `source_frames`；该值服务于“逐 episode、逐帧写入数据集”。
    source_frames = 0
# 【L0209】计算并保存变量 `selected_phase_counts`；该值服务于“逐 episode、逐帧写入数据集”。
    selected_phase_counts: dict[str, int] = {}
# 【L0210】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for episode in episodes:
# 【L0211】执行“逐 episode、逐帧写入数据集”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        source_frames += len(episode["states"])
# 【L0212】计算并保存变量 `indices`；该值服务于“逐 episode、逐帧写入数据集”。
        indices = (
# 【L0213】执行“逐 episode、逐帧写入数据集”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            select_policy_window_indices(episode)
# 【L0214】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if args.policy_window
# 【L0215】执行“逐 episode、逐帧写入数据集”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else np.arange(len(episode["states"]), dtype=np.int64)
# 【L0216】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
        )
# 【L0217】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for index in indices:
# 【L0218】计算并保存变量 `index`；该值服务于“逐 episode、逐帧写入数据集”。
            index = int(index)
# 【L0219】计算并保存变量 `phase`；该值服务于“逐 episode、逐帧写入数据集”。
            phase = episode["phase_names"][int(episode["phase_ids"][index])]
# 【L0220】执行“逐 episode、逐帧写入数据集”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            selected_phase_counts[phase] = selected_phase_counts.get(phase, 0) + 1
# 【L0221】调用 `dataset.add_frame`：把一帧观测、动作和任务文字加入 LeRobot 数据集。本行位于“逐 episode、逐帧写入数据集”。
            dataset.add_frame(
# 【L0222】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“逐 episode、逐帧写入数据集”。
                {
# 【L0223】定义字典/JSON 字段 `image`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "image": read_rgb(episode["directory"] / episode["external_paths"][index]),
# 【L0224】定义字典/JSON 字段 `wrist_image`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "wrist_image": read_rgb(episode["directory"] / episode["wrist_paths"][index]),
# 【L0225】定义字典/JSON 字段 `joints`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "joints": episode["states"][index, :6],
# 【L0226】定义字典/JSON 字段 `gripper`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "gripper": episode["states"][index, 6:7],
# 【L0227】定义字典/JSON 字段 `actions`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "actions": episode["actions"][index],
# 【L0228】定义字典/JSON 字段 `task`；它把“逐 episode、逐帧写入数据集”中的结果用稳定键名记录下来。
                    "task": episode["prompt"],
# 【L0229】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
                }
# 【L0230】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
            )
# 【L0231】执行“逐 episode、逐帧写入数据集”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            total_frames += 1
# 【L0232】调用 `dataset.save_episode`：结束并保存当前 LeRobot episode。本行位于“逐 episode、逐帧写入数据集”。
        dataset.save_episode()
# 【L0233】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0234】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(
# 【L0235】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“输出转换统计与脚本退出码”。
        json.dumps(
# 【L0236】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“输出转换统计与脚本退出码”。
            {
# 【L0237】定义字典/JSON 字段 `status`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "status": "pass",
# 【L0238】定义字典/JSON 字段 `repo_id`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "repo_id": args.repo_id,
# 【L0239】定义字典/JSON 字段 `output_path`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "output_path": str(output_path),
# 【L0240】定义字典/JSON 字段 `episode_count`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "episode_count": len(episodes),
# 【L0241】定义字典/JSON 字段 `frame_count`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "frame_count": total_frames,
# 【L0242】定义字典/JSON 字段 `source_frame_count`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "source_frame_count": source_frames,
# 【L0243】定义字典/JSON 字段 `policy_window`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "policy_window": args.policy_window,
# 【L0244】定义字典/JSON 字段 `selected_phase_counts`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "selected_phase_counts": dict(sorted(selected_phase_counts.items())),
# 【L0245】定义字典/JSON 字段 `fps`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "fps": int(rounded_fps),
# 【L0246】定义字典/JSON 字段 `collection_split`；它把“输出转换统计与脚本退出码”中的结果用稳定键名记录下来。
                "collection_split": args.split,
# 【L0247】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
            },
# 【L0248】计算并保存变量 `indent`；该值服务于“输出转换统计与脚本退出码”。
            indent=2,
# 【L0249】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
        )
# 【L0250】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
    )
# 【L0251】结束当前函数并把结果交给调用者；这里完成“输出转换统计与脚本退出码”的输出。
    return 0
# 【L0252】空行：分隔“输出转换统计与脚本退出码”中的逻辑段，让结构更容易看清。

# 【L0253】空行：分隔“输出转换统计与脚本退出码”中的逻辑段，让结构更容易看清。

# 【L0254】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0255】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
