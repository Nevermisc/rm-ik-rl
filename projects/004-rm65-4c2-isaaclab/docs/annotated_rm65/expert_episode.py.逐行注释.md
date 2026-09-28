# `expert_episode.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/expert_episode.py`
- 快照 SHA-256：`a2223a61169c0a1e22a66ab3d760a42c39110532fc2ff01e6f63bf058c150b1f`
- 总行数：254
- 程序作用：定义 RM65 专家轨迹的中间格式；确保每帧观测与同索引动作严格同步，并负责保存和校验。
- 推荐读法：先读 add_frame() 理解一帧是什么，再读 save() 看磁盘结构，最后读 validate_episode()。

## 功能块地图

- 第 1-20 行：格式常量与夹爪归一化
- 第 23-52 行：EpisodeRecorder 的字段与初始化校验
- 第 54-121 行：校验并追加一帧状态、动作、物体姿态和图像
- 第 123-130 行：RGB 图像格式校验
- 第 132-173 行：保存 episode.npz 和 metadata.json
- 第 176-254 行：重新读取磁盘数据并做独立完整性校验

## 函数/类索引

- `normalize_gripper()`：第 17-20 行
- `class EpisodeRecorder`：第 24-173 行
  - `EpisodeRecorder.__post_init__()`：第 47-52 行
  - `EpisodeRecorder.add_frame()`：第 54-121 行
  - `EpisodeRecorder._validate_image()`：第 124-130 行
  - `EpisodeRecorder.save()`：第 132-173 行
- `validate_episode()`：第 176-254 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Portable intermediate format for RM65 expert demonstration episodes."""
# 【L0002】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0003】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0004】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0005】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0006】导入 dataclasses：标准库数据类工具，用较少样板代码声明配置/记录对象；后面的代码会调用其中的类或函数。
from dataclasses import dataclass, field
# 【L0007】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0008】导入 typing：项目或第三方模块；后面的代码会调用其中的类或函数。
from typing import Any
# 【L0009】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0010】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0011】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0013】计算并保存变量 `FORMAT_NAME`；该值服务于“格式常量与夹爪归一化”。
FORMAT_NAME = "rm65_expert_episode_v1"
# 【L0014】计算并保存变量 `JOINT_NAMES`；该值服务于“格式常量与夹爪归一化”。
JOINT_NAMES = tuple(f"joint_{index}" for index in range(1, 7))
# 【L0015】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0016】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0017】定义函数 normalize_gripper；其职责属于“格式常量与夹爪归一化”，缩进块是函数体。
def normalize_gripper(position_rad: float, closed_position_rad: float = 0.865) -> float:
# 【L0018】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if closed_position_rad <= 0.0:
# 【L0019】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("closed gripper position must be positive")
# 【L0020】结束当前函数并把结果交给调用者；这里完成“格式常量与夹爪归一化”的输出。
    return float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))
# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】数据类装饰器：自动生成初始化等方法；frozen=True 表示创建后不允许改字段。
@dataclass
# 【L0024】定义类 EpisodeRecorder；把相关配置、状态和方法组织成一个可复用对象。
class EpisodeRecorder:
# 【L0025】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Accumulate synchronized state/action frames and save one episode.
# 【L0026】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0027】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    Each frame represents the observation immediately before applying the
# 【L0028】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    action target stored at the same index. Images are optional while bringing
# 【L0029】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    up the low-dimensional recorder, but production training episodes require
# 【L0030】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    both external and wrist RGB streams.
# 【L0031】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0032】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0033】调用 `Path`：创建路径对象。本行位于“EpisodeRecorder 的字段与初始化校验”。
    output_dir: Path
# 【L0034】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    prompt: str
# 【L0035】执行“EpisodeRecorder 的字段与初始化校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    control_hz: float
# 【L0036】计算并保存变量 `metadata`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    metadata: dict[str, Any] = field(default_factory=dict)
# 【L0037】计算并保存变量 `_timestamps`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _timestamps: list[float] = field(default_factory=list, init=False)
# 【L0038】计算并保存变量 `_sim_steps`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _sim_steps: list[int] = field(default_factory=list, init=False)
# 【L0039】计算并保存变量 `_states`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _states: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0040】计算并保存变量 `_actions`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _actions: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0041】计算并保存变量 `_cube_poses`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _cube_poses: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0042】计算并保存变量 `_phases`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _phases: list[str] = field(default_factory=list, init=False)
# 【L0043】计算并保存变量 `_external_paths`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _external_paths: list[str] = field(default_factory=list, init=False)
# 【L0044】计算并保存变量 `_wrist_paths`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _wrist_paths: list[str] = field(default_factory=list, init=False)
# 【L0045】计算并保存变量 `_images_enabled`；该值服务于“EpisodeRecorder 的字段与初始化校验”。
    _images_enabled: bool | None = field(default=None, init=False)
# 【L0046】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0047】定义函数 __post_init__；其职责属于“EpisodeRecorder 的字段与初始化校验”，缩进块是函数体。
    def __post_init__(self) -> None:
# 【L0048】调用 `Path`：创建路径对象。本行位于“EpisodeRecorder 的字段与初始化校验”。
        self.output_dir = Path(self.output_dir)
# 【L0049】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not self.prompt.strip():
# 【L0050】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("episode prompt must not be empty")
# 【L0051】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not np.isfinite(self.control_hz) or self.control_hz <= 0.0:
# 【L0052】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("control_hz must be positive and finite")
# 【L0053】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0054】定义函数 add_frame；其职责属于“校验并追加一帧状态、动作、物体姿态和图像”，缩进块是函数体。
    def add_frame(
# 【L0055】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        self,
# 【L0056】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“校验并追加一帧状态、动作、物体姿态和图像”。
        *,
# 【L0057】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        timestamp_s: float,
# 【L0058】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        sim_step: int,
# 【L0059】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        phase: str,
# 【L0060】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        joint_position_rad: np.ndarray,
# 【L0061】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        gripper_position: float,
# 【L0062】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        action: np.ndarray,
# 【L0063】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“校验并追加一帧状态、动作、物体姿态和图像”。
        cube_pose_wxyz: np.ndarray,
# 【L0064】给变量 `external_rgb` 赋值：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
        external_rgb: np.ndarray | None = None,
# 【L0065】给变量 `wrist_rgb` 赋值：随末端移动的腕部相机 RGB 图像。
        wrist_rgb: np.ndarray | None = None,
# 【L0066】开始一个缩进代码块或键值结构；该块负责“校验并追加一帧状态、动作、物体姿态和图像”。
    ) -> None:
# 【L0067】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
        joints = np.asarray(joint_position_rad, dtype=np.float32)
# 【L0068】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
        action_array = np.asarray(action, dtype=np.float32)
# 【L0069】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
        cube_pose = np.asarray(cube_pose_wxyz, dtype=np.float32)
# 【L0070】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if joints.shape != (6,):
# 【L0071】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"expected six joint positions, got {joints.shape}")
# 【L0072】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if action_array.shape != (7,):
# 【L0073】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"expected seven action values, got {action_array.shape}")
# 【L0074】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if cube_pose.shape != (7,):
# 【L0075】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")
# 【L0076】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not phase.strip():
# 【L0077】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("phase must not be empty")
# 【L0078】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if sim_step < 0:
# 【L0079】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("sim_step must be non-negative")
# 【L0080】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not 0.0 <= gripper_position <= 1.0:
# 【L0081】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("normalized gripper position must be in [0, 1]")
# 【L0082】调用 `np.concatenate`：沿一个轴首尾拼接数组。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
        numeric = np.concatenate(
# 【L0083】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“校验并追加一帧状态、动作、物体姿态和图像”。
            [joints, [gripper_position], action_array, cube_pose, [timestamp_s]]
# 【L0084】结束或闭合当前语法结构；它属于“校验并追加一帧状态、动作、物体姿态和图像”。
        )
# 【L0085】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not np.isfinite(numeric).all():
# 【L0086】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("episode frames must contain only finite numeric values")
# 【L0087】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self._timestamps and timestamp_s <= self._timestamps[-1]:
# 【L0088】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("timestamps must be strictly increasing")
# 【L0089】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self._sim_steps and sim_step <= self._sim_steps[-1]:
# 【L0090】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("simulation steps must be strictly increasing")
# 【L0091】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if (external_rgb is None) != (wrist_rgb is None):
# 【L0092】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("external and wrist images must be supplied together")
# 【L0093】计算并保存变量 `frame_has_images`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
        frame_has_images = external_rgb is not None
# 【L0094】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self._images_enabled is None:
# 【L0095】保存实例字段 `_images_enabled`，让同一对象的其他方法继续使用这个值。
            self._images_enabled = frame_has_images
# 【L0096】追加条件分支：前面的条件不成立时再检查这一条件。
        elif self._images_enabled != frame_has_images:
# 【L0097】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("all frames in an episode must use the same image streams")
# 【L0098】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0099】计算并保存变量 `frame_index`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
        frame_index = len(self._states)
# 【L0100】计算并保存变量 `external_path`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
        external_path = ""
# 【L0101】计算并保存变量 `wrist_path`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
        wrist_path = ""
# 【L0102】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if external_rgb is not None:
# 【L0103】导入 PIL：Pillow 图像库，用于 PNG/RGB 读写；后面的代码会调用其中的类或函数。
            from PIL import Image
# 【L0104】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0105】计算并保存变量 `external`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
            external = self._validate_image(external_rgb, "external")
# 【L0106】计算并保存变量 `wrist`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
            wrist = self._validate_image(wrist_rgb, "wrist")
# 【L0107】计算并保存变量 `external_path`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
            external_path = f"images/external/{frame_index:06d}.png"
# 【L0108】计算并保存变量 `wrist_path`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
            wrist_path = f"images/wrist/{frame_index:06d}.png"
# 【L0109】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for relative_path, image in ((external_path, external), (wrist_path, wrist)):
# 【L0110】计算并保存变量 `path`；该值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
                path = self.output_dir / relative_path
# 【L0111】调用 `mkdir`：创建目录。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
                path.parent.mkdir(parents=True, exist_ok=True)
# 【L0112】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                Image.fromarray(image).save(path)
# 【L0113】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0114】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._timestamps.append(float(timestamp_s))
# 【L0115】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._sim_steps.append(int(sim_step))
# 【L0116】调用 `np.concatenate`：沿一个轴首尾拼接数组。本行位于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))
# 【L0117】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._actions.append(action_array)
# 【L0118】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._cube_poses.append(cube_pose)
# 【L0119】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._phases.append(phase)
# 【L0120】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._external_paths.append(external_path)
# 【L0121】执行“校验并追加一帧状态、动作、物体姿态和图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self._wrist_paths.append(wrist_path)
# 【L0122】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0123】静态方法装饰器：这个函数不依赖某个实例的 self 状态。
    @staticmethod
# 【L0124】定义函数 _validate_image；其职责属于“RGB 图像格式校验”，缩进块是函数体。
    def _validate_image(image: np.ndarray, name: str) -> np.ndarray:
# 【L0125】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“RGB 图像格式校验”。
        array = np.asarray(image)
# 【L0126】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if array.ndim != 3 or array.shape[2] != 3:
# 【L0127】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")
# 【L0128】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if array.dtype != np.uint8:
# 【L0129】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must be uint8, got {array.dtype}")
# 【L0130】结束当前函数并把结果交给调用者；这里完成“RGB 图像格式校验”的输出。
        return array
# 【L0131】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0132】定义函数 save；其职责属于“保存 episode.npz 和 metadata.json”，缩进块是函数体。
    def save(self) -> dict[str, Any]:
# 【L0133】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not self._states:
# 【L0134】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError("cannot save an empty episode")
# 【L0135】调用 `mkdir`：创建目录。本行位于“保存 episode.npz 和 metadata.json”。
        self.output_dir.mkdir(parents=True, exist_ok=True)
# 【L0136】计算并保存变量 `phase_names`；该值服务于“保存 episode.npz 和 metadata.json”。
        phase_names = list(dict.fromkeys(self._phases))
# 【L0137】计算并保存变量 `phase_to_id`；该值服务于“保存 episode.npz 和 metadata.json”。
        phase_to_id = {name: index for index, name in enumerate(phase_names)}
# 【L0138】计算并保存变量 `arrays_path`；该值服务于“保存 episode.npz 和 metadata.json”。
        arrays_path = self.output_dir / "episode.npz"
# 【L0139】执行“保存 episode.npz 和 metadata.json”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        np.savez_compressed(
# 【L0140】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“保存 episode.npz 和 metadata.json”。
            arrays_path,
# 【L0141】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“保存 episode.npz 和 metadata.json”。
            timestamp_s=np.asarray(self._timestamps, dtype=np.float64),
# 【L0142】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“保存 episode.npz 和 metadata.json”。
            sim_step=np.asarray(self._sim_steps, dtype=np.int64),
# 【L0143】调用 `np.stack`：把多个同形数组堆成新增的一维。本行位于“保存 episode.npz 和 metadata.json”。
            observation_state=np.stack(self._states),
# 【L0144】调用 `np.stack`：把多个同形数组堆成新增的一维。本行位于“保存 episode.npz 和 metadata.json”。
            action=np.stack(self._actions),
# 【L0145】调用 `np.stack`：把多个同形数组堆成新增的一维。本行位于“保存 episode.npz 和 metadata.json”。
            cube_pose_wxyz=np.stack(self._cube_poses),
# 【L0146】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“保存 episode.npz 和 metadata.json”。
            phase_id=np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16),
# 【L0147】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0148】计算并保存变量 `has_images`；该值服务于“保存 episode.npz 和 metadata.json”。
        has_images = bool(self._images_enabled)
# 【L0149】给变量 `manifest` 赋值：描述磁盘数据含义、数量和路径的元数据清单。
        manifest = {
# 【L0150】定义字典/JSON 字段 `format`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "format": FORMAT_NAME,
# 【L0151】定义字典/JSON 字段 `prompt`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "prompt": self.prompt,
# 【L0152】定义字典/JSON 字段 `control_hz`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "control_hz": self.control_hz,
# 【L0153】定义字典/JSON 字段 `frame_count`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "frame_count": len(self._states),
# 【L0154】定义字典/JSON 字段 `joint_names`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "joint_names": list(JOINT_NAMES),
# 【L0155】定义字典/JSON 字段 `observation_state_semantics`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "observation_state_semantics": [*JOINT_NAMES, "gripper_normalized"],
# 【L0156】定义字典/JSON 字段 `action_semantics`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "action_semantics": [
# 【L0157】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“保存 episode.npz 和 metadata.json”。
                *(f"{name}_absolute_target_rad" for name in JOINT_NAMES),
# 【L0158】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“保存 episode.npz 和 metadata.json”。
                "gripper_normalized_target",
# 【L0159】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            ],
# 【L0160】定义字典/JSON 字段 `cube_pose_semantics`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "cube_pose_semantics": ["x", "y", "z", "qw", "qx", "qy", "qz"],
# 【L0161】定义字典/JSON 字段 `phase_names`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "phase_names": phase_names,
# 【L0162】定义字典/JSON 字段 `images_recorded`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "images_recorded": has_images,
# 【L0163】定义字典/JSON 字段 `image_paths`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "image_paths": {
# 【L0164】定义字典/JSON 字段 `external`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
                "external": self._external_paths,
# 【L0165】定义字典/JSON 字段 `wrist`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
                "wrist": self._wrist_paths,
# 【L0166】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            },
# 【L0167】定义字典/JSON 字段 `frame_semantics`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "frame_semantics": "observation immediately before applying action at the same index",
# 【L0168】定义字典/JSON 字段 `metadata`；它把“保存 episode.npz 和 metadata.json”中的结果用稳定键名记录下来。
            "metadata": self.metadata,
# 【L0169】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        }
# 【L0170】调用 `write_text`：把文本写入磁盘文件。本行位于“保存 episode.npz 和 metadata.json”。
        (self.output_dir / "metadata.json").write_text(
# 【L0171】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“保存 episode.npz 和 metadata.json”。
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
# 【L0172】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0173】结束当前函数并把结果交给调用者；这里完成“保存 episode.npz 和 metadata.json”的输出。
        return manifest
# 【L0174】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0175】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0176】定义函数 validate_episode；其职责属于“重新读取磁盘数据并做独立完整性校验”，缩进块是函数体。
def validate_episode(directory: Path, *, require_images: bool = False) -> dict[str, Any]:
# 【L0177】调用 `Path`：创建路径对象。本行位于“重新读取磁盘数据并做独立完整性校验”。
    directory = Path(directory)
# 【L0178】调用 `read_text`：从磁盘读取文本。本行位于“重新读取磁盘数据并做独立完整性校验”。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0179】上下文管理块：进入时打开资源，离开时自动关闭文件、数组或 socket。
    with np.load(directory / "episode.npz") as arrays:
# 【L0180】计算并保存变量 `timestamps`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        timestamps = arrays["timestamp_s"]
# 【L0181】计算并保存变量 `sim_steps`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        sim_steps = arrays["sim_step"]
# 【L0182】计算并保存变量 `states`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        states = arrays["observation_state"]
# 【L0183】给变量 `actions` 赋值：一个动作块；形状通常为 (时间步数, 7)。
        actions = arrays["action"]
# 【L0184】计算并保存变量 `cube_poses`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        cube_poses = arrays["cube_pose_wxyz"]
# 【L0185】计算并保存变量 `phase_ids`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        phase_ids = arrays["phase_id"]
# 【L0186】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0187】计算并保存变量 `frame_count`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    frame_count = int(manifest["frame_count"])
# 【L0188】计算并保存变量 `errors`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    errors: list[str] = []
# 【L0189】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if manifest.get("format") != FORMAT_NAME:
# 【L0190】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("unexpected episode format")
# 【L0191】计算并保存变量 `expected_shapes`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    expected_shapes = {
# 【L0192】定义字典/JSON 字段 `timestamps`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "timestamps": (frame_count,),
# 【L0193】定义字典/JSON 字段 `sim_steps`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "sim_steps": (frame_count,),
# 【L0194】定义字典/JSON 字段 `states`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "states": (frame_count, 7),
# 【L0195】定义字典/JSON 字段 `actions`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "actions": (frame_count, 7),
# 【L0196】定义字典/JSON 字段 `cube_poses`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "cube_poses": (frame_count, 7),
# 【L0197】定义字典/JSON 字段 `phase_ids`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "phase_ids": (frame_count,),
# 【L0198】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0199】计算并保存变量 `actual_shapes`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    actual_shapes = {
# 【L0200】定义字典/JSON 字段 `timestamps`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "timestamps": timestamps.shape,
# 【L0201】定义字典/JSON 字段 `sim_steps`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "sim_steps": sim_steps.shape,
# 【L0202】定义字典/JSON 字段 `states`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "states": states.shape,
# 【L0203】定义字典/JSON 字段 `actions`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "actions": actions.shape,
# 【L0204】定义字典/JSON 字段 `cube_poses`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "cube_poses": cube_poses.shape,
# 【L0205】定义字典/JSON 字段 `phase_ids`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "phase_ids": phase_ids.shape,
# 【L0206】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0207】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for name, shape in expected_shapes.items():
# 【L0208】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if actual_shapes[name] != shape:
# 【L0209】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            errors.append(f"{name} shape {actual_shapes[name]} != {shape}")
# 【L0210】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if frame_count < 2:
# 【L0211】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("episode must contain at least two frames")
# 【L0212】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses)):
# 【L0213】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("episode contains non-finite numeric values")
# 【L0214】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0):
# 【L0215】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("timestamps are not strictly increasing")
# 【L0216】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0):
# 【L0217】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("simulation steps are not strictly increasing")
# 【L0218】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0)):
# 【L0219】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("observed gripper values leave [0, 1]")
# 【L0220】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0)):
# 【L0221】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("action gripper values leave [0, 1]")
# 【L0222】计算并保存变量 `phase_names`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    phase_names = manifest.get("phase_names", [])
# 【L0223】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if phase_ids.size and (
# 【L0224】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        np.min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)
# 【L0225】开始一个缩进代码块或键值结构；该块负责“重新读取磁盘数据并做独立完整性校验”。
    ):
# 【L0226】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("phase ids leave the manifest phase-name range")
# 【L0227】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0228】计算并保存变量 `image_paths`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    image_paths = manifest.get("image_paths", {})
# 【L0229】计算并保存变量 `external`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    external = image_paths.get("external", [])
# 【L0230】计算并保存变量 `wrist`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    wrist = image_paths.get("wrist", [])
# 【L0231】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(external) != frame_count or len(wrist) != frame_count:
# 【L0232】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("image path lists do not match frame count")
# 【L0233】计算并保存变量 `images_recorded`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
    images_recorded = bool(manifest.get("images_recorded"))
# 【L0234】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if require_images and not images_recorded:
# 【L0235】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        errors.append("images are required but were not recorded")
# 【L0236】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if images_recorded:
# 【L0237】计算并保存变量 `missing_images`；该值服务于“重新读取磁盘数据并做独立完整性校验”。
        missing_images = [
# 【L0238】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            relative
# 【L0239】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for relative in [*external, *wrist]
# 【L0240】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if not relative or not (directory / relative).is_file()
# 【L0241】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
        ]
# 【L0242】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if missing_images:
# 【L0243】执行“重新读取磁盘数据并做独立完整性校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            errors.append(f"missing {len(missing_images)} image files")
# 【L0244】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0245】结束当前函数并把结果交给调用者；这里完成“重新读取磁盘数据并做独立完整性校验”的输出。
    return {
# 【L0246】定义字典/JSON 字段 `status`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "status": "pass" if not errors else "fail",
# 【L0247】定义字典/JSON 字段 `format`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "format": manifest.get("format"),
# 【L0248】定义字典/JSON 字段 `frame_count`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "frame_count": frame_count,
# 【L0249】定义字典/JSON 字段 `duration_s`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "duration_s": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
# 【L0250】定义字典/JSON 字段 `images_recorded`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "images_recorded": images_recorded,
# 【L0251】定义字典/JSON 字段 `phase_names`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "phase_names": manifest.get("phase_names", []),
# 【L0252】定义字典/JSON 字段 `all_finite`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "all_finite": not any("non-finite" in item for item in errors),
# 【L0253】定义字典/JSON 字段 `errors`；它把“重新读取磁盘数据并做独立完整性校验”中的结果用稳定键名记录下来。
        "errors": errors,
# 【L0254】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
```
