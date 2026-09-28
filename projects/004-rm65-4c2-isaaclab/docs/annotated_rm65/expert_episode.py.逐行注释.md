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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】说明字符串 `Portable intermediate format for RM65 expert demonstration episodes.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Portable intermediate format for RM65 expert demonstration episodes."""
# 【L0002】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0003】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0005】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0006】从 `dataclasses` 引入 `dataclass, field`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
from dataclasses import dataclass, field
# 【L0007】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0008】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0009】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0010】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0011】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0013】得到 `FORMAT_NAME`，它在本项目中表示本功能块中的 `FORMAT_NAME` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"rm65_expert_episode_v1"`；`rm65_expert_episode_v1` 表示一条轨迹相关值。
FORMAT_NAME = "rm65_expert_episode_v1"
# 【L0014】得到 `JOINT_NAMES`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tuple(f"joint_{index}" for index in range(1, 7))`；`f` 表示本功能块中的 `f` 值；`joint_` 表示关节相关值；`index` 表示索引相关值。
JOINT_NAMES = tuple(f"joint_{index}" for index in range(1, 7))
# 【L0015】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0016】空行：分隔“格式常量与夹爪归一化”中的逻辑段，让结构更容易看清。

# 【L0017】定义函数 `normalize_gripper(position_rad: float, closed_position_rad: float = 0.865)`；调用者把参数交给它完成“格式常量与夹爪归一化”，后面的缩进代码是具体实现。
def normalize_gripper(position_rad: float, closed_position_rad: float = 0.865) -> float:
# 【L0018】判断 `closed_position_rad <= 0.0` 是否成立；`closed_position_rad` 表示位置相关值
    if closed_position_rad <= 0.0:
# 【L0019】主动抛出 `ValueError("closed gripper position must be positive")` 并停止当前路径；说明当前输入违反“格式常量与夹爪归一化”要求，不能继续进入仿真、训练或评测。
        raise ValueError("closed gripper position must be positive")
# 【L0020】结束当前函数并把 `float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))` 交回调用者；这个值的含义是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    return float(np.clip(position_rad / closed_position_rad, 0.0, 1.0))
# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclass
# 【L0024】定义 `EpisodeRecorder` 类并继承 `object`；它把“EpisodeRecorder 的字段与初始化校验”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class EpisodeRecorder:
# 【L0025】说明字符串 `Accumulate synchronized state/action frames and save one episode.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Accumulate synchronized state/action frames and save one episode.
# 【L0026】继续说明字符串，原文是 ``；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0027】继续说明字符串，原文是 `Each frame represents the observation immediately before applying the`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    Each frame represents the observation immediately before applying the
# 【L0028】继续说明字符串，原文是 `action target stored at the same index. Images are optional while bringing`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    action target stored at the same index. Images are optional while bringing
# 【L0029】继续说明字符串，原文是 `up the low-dimensional recorder, but production training episodes require`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    up the low-dimensional recorder, but production training episodes require
# 【L0030】继续说明字符串，原文是 `both external and wrist RGB streams.`；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    both external and wrist RGB streams.
# 【L0031】继续说明字符串，原文是 ``；这段文字在解释“EpisodeRecorder 的字段与初始化校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0032】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0033】声明/传入参数 `output_dir`，类型提示为 `Path`；在本项目中它表示输出相关值。
    output_dir: Path
# 【L0034】声明/传入参数 `prompt`，类型提示为 `str`；在本项目中它表示本功能块中的 `prompt` 值。
    prompt: str
# 【L0035】声明/传入参数 `control_hz`，类型提示为 `float`；在本项目中它表示本功能块中的 `control_hz` 值。
    control_hz: float
# 【L0036】把右侧结果写进 `metadata: dict[str, Any]`（写入 `metadata: dict[str, Any]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=dict)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值。
    metadata: dict[str, Any] = field(default_factory=dict)
# 【L0037】把右侧结果写进 `_timestamps: list[float]`（写入 `_timestamps: list[float]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _timestamps: list[float] = field(default_factory=list, init=False)
# 【L0038】把右侧结果写进 `_sim_steps: list[int]`（写入 `_sim_steps: list[int]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _sim_steps: list[int] = field(default_factory=list, init=False)
# 【L0039】把右侧结果写进 `_states: list[np.ndarray]`（写入 `_states: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _states: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0040】把右侧结果写进 `_actions: list[np.ndarray]`（写入 `_actions: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _actions: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0041】把右侧结果写进 `_cube_poses: list[np.ndarray]`（写入 `_cube_poses: list[np.ndarray]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _cube_poses: list[np.ndarray] = field(default_factory=list, init=False)
# 【L0042】把右侧结果写进 `_phases: list[str]`（写入 `_phases: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _phases: list[str] = field(default_factory=list, init=False)
# 【L0043】把右侧结果写进 `_external_paths: list[str]`（写入 `_external_paths: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _external_paths: list[str] = field(default_factory=list, init=False)
# 【L0044】把右侧结果写进 `_wrist_paths: list[str]`（写入 `_wrist_paths: list[str]` 指定的字段）；右侧具体做的是：计算表达式 `field(default_factory=list, init=False)`；`field` 表示本功能块中的 `field` 值；`default_factory` 表示本功能块中的 `default_factory` 值；`init` 表示本功能块中的 `init` 值。
    _wrist_paths: list[str] = field(default_factory=list, init=False)
# 【L0045】得到 `_images_enabled`，它在本项目中表示本功能块中的 `_images_enabled` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `field(default=None, init=False)`；`field` 表示本功能块中的 `field` 值；`default` 表示本功能块中的 `default` 值；`init` 表示本功能块中的 `init` 值。
    _images_enabled: bool | None = field(default=None, init=False)
# 【L0046】空行：分隔“EpisodeRecorder 的字段与初始化校验”中的逻辑段，让结构更容易看清。

# 【L0047】定义函数 `__post_init__(self)`；调用者把参数交给它完成“EpisodeRecorder 的字段与初始化校验”，后面的缩进代码是具体实现。
    def __post_init__(self) -> None:
# 【L0048】把 `self` 对象的 `output_dir` 配置成 `Path(self.output_dir)`。`self` 在这里表示当前类实例；这个设置会影响“EpisodeRecorder 的字段与初始化校验”。
        self.output_dir = Path(self.output_dir)
# 【L0049】判断 `not self.prompt.strip()` 是否成立；`prompt` 表示本功能块中的 `prompt` 值；`strip` 表示本功能块中的 `strip` 值
        if not self.prompt.strip():
# 【L0050】主动抛出 `ValueError("episode prompt must not be empty")` 并停止当前路径；说明当前输入违反“EpisodeRecorder 的字段与初始化校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError("episode prompt must not be empty")
# 【L0051】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
        if not np.isfinite(self.control_hz) or self.control_hz <= 0.0:
# 【L0052】主动抛出 `ValueError("control_hz must be positive and finite")` 并停止当前路径；说明当前输入违反“EpisodeRecorder 的字段与初始化校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError("control_hz must be positive and finite")
# 【L0053】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0054】定义函数 `add_frame(参数在后续行继续)`；调用者把参数交给它完成“校验并追加一帧状态、动作、物体姿态和图像”，后面的缩进代码是具体实现。
    def add_frame(
# 【L0055】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0056】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“校验并追加一帧状态、动作、物体姿态和图像”。
        *,
# 【L0057】声明/传入参数 `timestamp_s`，类型提示为 `float`；在本项目中它表示本功能块中的 `timestamp_s` 值。
        timestamp_s: float,
# 【L0058】声明/传入参数 `sim_step`，类型提示为 `int`；在本项目中它表示仿真、步相关值。
        sim_step: int,
# 【L0059】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
        phase: str,
# 【L0060】声明/传入参数 `joint_position_rad`，类型提示为 `np.ndarray`；在本项目中它表示关节、位置相关值。
        joint_position_rad: np.ndarray,
# 【L0061】声明/传入参数 `gripper_position`，类型提示为 `float`；在本项目中它表示夹爪、位置相关值。
        gripper_position: float,
# 【L0062】声明/传入参数 `action`，类型提示为 `np.ndarray`；在本项目中它表示动作相关值。
        action: np.ndarray,
# 【L0063】声明/传入参数 `cube_pose_wxyz`，类型提示为 `np.ndarray`；在本项目中它表示任务方块相关值。
        cube_pose_wxyz: np.ndarray,
# 【L0064】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        external_rgb: np.ndarray | None = None,
# 【L0065】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_rgb: np.ndarray | None = None,
# 【L0066】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“校验并追加一帧状态、动作、物体姿态和图像”。
    ) -> None:
# 【L0067】得到 `joints`，它在本项目中表示六个 RM65 关节位置的一维 NumPy 数组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `joint_position_rad, dtype=np.float32`（关节、位置相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        joints = np.asarray(joint_position_rad, dtype=np.float32)
# 【L0068】得到 `action_array`，它在本项目中表示强制为 float32 后的一帧七维专家动作；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `action, dtype=np.float32`（本功能块中的 `action, dtype=np.float32` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        action_array = np.asarray(action, dtype=np.float32)
# 【L0069】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `cube_pose_wxyz, dtype=np.float32`（任务方块相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        cube_pose = np.asarray(cube_pose_wxyz, dtype=np.float32)
# 【L0070】检查 `joints.shape` 是否不等于要求的 `(6,)`；若不等，数据维度合同已被破坏，进入错误处理
        if joints.shape != (6,):
# 【L0071】主动抛出 `ValueError(f"expected six joint positions, got {joints.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected six joint positions, got {joints.shape}")
# 【L0072】检查 `action_array.shape` 是否不等于要求的 `(7,)`；若不等，数据维度合同已被破坏，进入错误处理
        if action_array.shape != (7,):
# 【L0073】主动抛出 `ValueError(f"expected seven action values, got {action_array.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected seven action values, got {action_array.shape}")
# 【L0074】检查 `cube_pose.shape` 是否不等于要求的 `(7,)`；若不等，数据维度合同已被破坏，进入错误处理
        if cube_pose.shape != (7,):
# 【L0075】主动抛出 `ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"expected cube pose [xyz,wxyz], got {cube_pose.shape}")
# 【L0076】判断 `not phase.strip()` 是否成立；`phase` 表示本功能块中的 `phase` 值；`strip` 表示本功能块中的 `strip` 值
        if not phase.strip():
# 【L0077】主动抛出 `ValueError("phase must not be empty")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("phase must not be empty")
# 【L0078】判断 `sim_step < 0` 是否成立；`sim_step` 表示仿真、步相关值
        if sim_step < 0:
# 【L0079】主动抛出 `ValueError("sim_step must be non-negative")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("sim_step must be non-negative")
# 【L0080】判断 `not 0.0 <= gripper_position <= 1.0` 是否成立；`gripper_position` 表示夹爪、位置相关值
        if not 0.0 <= gripper_position <= 1.0:
# 【L0081】主动抛出 `ValueError("normalized gripper position must be in [0, 1]")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("normalized gripper position must be in [0, 1]")
# 【L0082】得到 `numeric`，它在本项目中表示本功能块中的 `numeric` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把括号中的多个一维数组沿现有轴首尾连接；在本项目中常用于把六关节和一个夹爪值组成七维状态/动作。
        numeric = np.concatenate(
# 【L0083】这是上一行尚未闭合的参数、数组或字典内容：`[joints, [gripper_position], action_array, cube_pose, [timestamp_s]]`；`joints` 表示六个 RM65 关节位置的一维 NumPy 数组；`gripper_position` 表示夹爪、位置相关值；`action_array` 表示强制为 float32 后的一帧七维专家动作，共同完成“校验并追加一帧状态、动作、物体姿态和图像”。
            [joints, [gripper_position], action_array, cube_pose, [timestamp_s]]
# 【L0084】结束或闭合当前语法结构；它属于“校验并追加一帧状态、动作、物体姿态和图像”。
        )
# 【L0085】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
        if not np.isfinite(numeric).all():
# 【L0086】主动抛出 `ValueError("episode frames must contain only finite numeric values")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("episode frames must contain only finite numeric values")
# 【L0087】判断 `self._timestamps and timestamp_s <= self._timestamps[-1]` 是否成立；`_timestamps` 表示本功能块中的 `_timestamps` 值；`timestamp_s` 表示本功能块中的 `timestamp_s` 值
        if self._timestamps and timestamp_s <= self._timestamps[-1]:
# 【L0088】主动抛出 `ValueError("timestamps must be strictly increasing")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("timestamps must be strictly increasing")
# 【L0089】判断 `self._sim_steps and sim_step <= self._sim_steps[-1]` 是否成立；`_sim_steps` 表示仿真、步数相关值；`sim_step` 表示仿真、步相关值
        if self._sim_steps and sim_step <= self._sim_steps[-1]:
# 【L0090】主动抛出 `ValueError("simulation steps must be strictly increasing")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("simulation steps must be strictly increasing")
# 【L0091】检查 `(external_rgb is None) != (wrist_rgb is None)`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if (external_rgb is None) != (wrist_rgb is None):
# 【L0092】主动抛出 `ValueError("external and wrist images must be supplied together")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("external and wrist images must be supplied together")
# 【L0093】得到 `frame_has_images`，它在本项目中表示帧相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `external_rgb is not None`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
        frame_has_images = external_rgb is not None
# 【L0094】检查 `self._images_enabled is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self._images_enabled is None:
# 【L0095】把 `self` 对象的 `_images_enabled` 配置成 `frame_has_images`。`self` 在这里表示当前类实例；这个设置会影响“校验并追加一帧状态、动作、物体姿态和图像”。
            self._images_enabled = frame_has_images
# 【L0096】前面的条件未成立时，继续判断 `self._images_enabled != frame_has_images` 是否成立；`_images_enabled` 表示本功能块中的 `_images_enabled` 值；`frame_has_images` 表示帧相关值
        elif self._images_enabled != frame_has_images:
# 【L0097】主动抛出 `ValueError("all frames in an episode must use the same image streams")` 并停止当前路径；说明当前输入违反“校验并追加一帧状态、动作、物体姿态和图像”要求，不能继续进入仿真、训练或评测。
            raise ValueError("all frames in an episode must use the same image streams")
# 【L0098】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0099】得到 `frame_index`，它在本项目中表示帧、索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(self._states)`；`_states` 表示本功能块中的 `_states` 值。
        frame_index = len(self._states)
# 【L0100】得到 `external_path`，它在本项目中表示外部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `""` 的结果保存下来，供当前功能块后续使用。
        external_path = ""
# 【L0101】得到 `wrist_path`，它在本项目中表示腕部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `""` 的结果保存下来，供当前功能块后续使用。
        wrist_path = ""
# 【L0102】检查 `external_rgb is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if external_rgb is not None:
# 【L0103】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
            from PIL import Image
# 【L0104】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0105】得到 `external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._validate_image(external_rgb, "external")`；`_validate_image` 表示图像相关值；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`external` 表示外部相机相关值。
            external = self._validate_image(external_rgb, "external")
# 【L0106】得到 `wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._validate_image(wrist_rgb, "wrist")`；`_validate_image` 表示图像相关值；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像；`wrist` 表示腕部相机相关值。
            wrist = self._validate_image(wrist_rgb, "wrist")
# 【L0107】得到 `external_path`，它在本项目中表示外部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"images/external/{frame_index:06d}.png"`；`f` 表示本功能块中的 `f` 值；`images` 表示本功能块中的 `images` 值；`external` 表示外部相机相关值。
            external_path = f"images/external/{frame_index:06d}.png"
# 【L0108】得到 `wrist_path`，它在本项目中表示腕部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `f"images/wrist/{frame_index:06d}.png"`；`f` 表示本功能块中的 `f` 值；`images` 表示本功能块中的 `images` 值；`wrist` 表示腕部相机相关值。
            wrist_path = f"images/wrist/{frame_index:06d}.png"
# 【L0109】遍历 `((external_path, external), (wrist_path, wrist))`，每次把当前元素放进 `relative_path, image`；这会逐个处理“校验并追加一帧状态、动作、物体姿态和图像”所需的帧、episode、动作或实验 case。
            for relative_path, image in ((external_path, external), (wrist_path, wrist)):
# 【L0110】得到 `path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self.output_dir / relative_path`；`output_dir` 表示输出相关值；`relative_path` 表示路径相关值。
                path = self.output_dir / relative_path
# 【L0111】调用 `mkdir`：创建目录；本行实际操作 `path.parent.mkdir(parents=True, exist_ok=True)`。`path` 表示路径相关值；`parent` 表示本功能块中的 `parent` 值。
                path.parent.mkdir(parents=True, exist_ok=True)
# 【L0112】对 `Image` 调用 `fromarray(image).save(path)`：调用 `Image` 提供的 `fromarray` 操作。本行产生的修改/返回值服务于“校验并追加一帧状态、动作、物体姿态和图像”。
                Image.fromarray(image).save(path)
# 【L0113】空行：分隔“校验并追加一帧状态、动作、物体姿态和图像”中的逻辑段，让结构更容易看清。

# 【L0114】对 `self._timestamps` 执行 `append`，把 `float(timestamp_s)` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._timestamps.append(float(timestamp_s))
# 【L0115】对 `self._sim_steps` 执行 `append`，把 `int(sim_step)` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._sim_steps.append(int(sim_step))
# 【L0116】调用 `np.concatenate`：沿一个轴首尾拼接数组；本行实际操作 `self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))`。`_states` 表示本功能块中的 `_states` 值；`append` 表示本功能块中的 `append` 值。
        self._states.append(np.concatenate([joints, [gripper_position]]).astype(np.float32))
# 【L0117】对 `self._actions` 执行 `append`，把 `action_array` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._actions.append(action_array)
# 【L0118】对 `self._cube_poses` 执行 `append`，把 `cube_pose` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._cube_poses.append(cube_pose)
# 【L0119】对 `self._phases` 执行 `append`，把 `phase` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._phases.append(phase)
# 【L0120】对 `self._external_paths` 执行 `append`，把 `external_path` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._external_paths.append(external_path)
# 【L0121】对 `self._wrist_paths` 执行 `append`，把 `wrist_path` 加入已有结果；该集合表示当前类实例，随后会用于“校验并追加一帧状态、动作、物体姿态和图像”。
        self._wrist_paths.append(wrist_path)
# 【L0122】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0123】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0124】定义函数 `_validate_image(image: np.ndarray, name: str)`；调用者把参数交给它完成“RGB 图像格式校验”，后面的缩进代码是具体实现。
    def _validate_image(image: np.ndarray, name: str) -> np.ndarray:
# 【L0125】得到 `array`，它在本项目中表示本功能块中的 `array` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `image`（图像相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        array = np.asarray(image)
# 【L0126】判断 `array.ndim != 3 or array.shape[2] != 3` 是否成立；`array` 表示本功能块中的 `array` 值；`ndim` 表示本功能块中的 `ndim` 值；`shape` 表示本功能块中的 `shape` 值
        if array.ndim != 3 or array.shape[2] != 3:
# 【L0127】主动抛出 `ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")` 并停止当前路径；说明当前输入违反“RGB 图像格式校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must have shape (H, W, 3), got {array.shape}")
# 【L0128】判断 `array.dtype != np.uint8` 是否成立；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`uint8` 表示本功能块中的 `uint8` 值
        if array.dtype != np.uint8:
# 【L0129】主动抛出 `ValueError(f"{name} image must be uint8, got {array.dtype}")` 并停止当前路径；说明当前输入违反“RGB 图像格式校验”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"{name} image must be uint8, got {array.dtype}")
# 【L0130】结束当前函数并把 `array` 交回调用者；这个值的含义是：计算表达式 `array`；`array` 表示本功能块中的 `array` 值。
        return array
# 【L0131】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0132】定义函数 `save(self)`；调用者把参数交给它完成“保存 episode.npz 和 metadata.json”，后面的缩进代码是具体实现。
    def save(self) -> dict[str, Any]:
# 【L0133】判断 `not self._states` 是否成立；`_states` 表示本功能块中的 `_states` 值
        if not self._states:
# 【L0134】主动抛出 `ValueError("cannot save an empty episode")` 并停止当前路径；说明当前输入违反“保存 episode.npz 和 metadata.json”要求，不能继续进入仿真、训练或评测。
            raise ValueError("cannot save an empty episode")
# 【L0135】调用 `mkdir`：创建目录；本行实际操作 `self.output_dir.mkdir(parents=True, exist_ok=True)`。`output_dir` 表示输出相关值；`mkdir` 表示本功能块中的 `mkdir` 值。
        self.output_dir.mkdir(parents=True, exist_ok=True)
# 【L0136】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(dict.fromkeys(self._phases))`；`fromkeys` 表示本功能块中的 `fromkeys` 值；`_phases` 表示本功能块中的 `_phases` 值。
        phase_names = list(dict.fromkeys(self._phases))
# 【L0137】得到 `phase_to_id`，它在本项目中表示本功能块中的 `phase_to_id` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{name: index for index, name in enumerate(phase_names)}`；`name` 表示本功能块中的 `name` 值；`index` 表示索引相关值；`enumerate` 表示本功能块中的 `enumerate` 值。
        phase_to_id = {name: index for index, name in enumerate(phase_names)}
# 【L0138】得到 `arrays_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self.output_dir / "episode.npz"`；`output_dir` 表示输出相关值；`episode` 表示一条轨迹相关值；`npz` 表示本功能块中的 `npz` 值。
        arrays_path = self.output_dir / "episode.npz"
# 【L0139】开始对 `np` 调用多行方法 `savez_compressed`：调用 `np` 提供的 `savez_compressed` 操作；具体参数写在随后几行，用于“保存 episode.npz 和 metadata.json”。
        np.savez_compressed(
# 【L0140】声明/传入参数 `arrays_path`；在本项目中它表示路径相关值。
            arrays_path,
# 【L0141】给上一层函数/配置构造器的命名参数 `timestamp_s` 传入 `np.asarray(self._timestamps, dtype=np.float64)`；该参数在本项目中表示本功能块中的 `timestamp_s` 值，会参与“保存 episode.npz 和 metadata.json”。
            timestamp_s=np.asarray(self._timestamps, dtype=np.float64),
# 【L0142】给上一层函数/配置构造器的命名参数 `sim_step` 传入 `np.asarray(self._sim_steps, dtype=np.int64)`；该参数在本项目中表示仿真、步相关值，会参与“保存 episode.npz 和 metadata.json”。
            sim_step=np.asarray(self._sim_steps, dtype=np.int64),
# 【L0143】给上一层函数/配置构造器的命名参数 `observation_state` 传入 `np.stack(self._states)`；该参数在本项目中表示状态相关值，会参与“保存 episode.npz 和 metadata.json”。
            observation_state=np.stack(self._states),
# 【L0144】给上一层函数/配置构造器的命名参数 `action` 传入 `np.stack(self._actions)`；该参数在本项目中表示动作相关值，会参与“保存 episode.npz 和 metadata.json”。
            action=np.stack(self._actions),
# 【L0145】给上一层函数/配置构造器的命名参数 `cube_pose_wxyz` 传入 `np.stack(self._cube_poses)`；该参数在本项目中表示任务方块相关值，会参与“保存 episode.npz 和 metadata.json”。
            cube_pose_wxyz=np.stack(self._cube_poses),
# 【L0146】给上一层函数/配置构造器的命名参数 `phase_id` 传入 `np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16)`；该参数在本项目中表示本功能块中的 `phase_id` 值，会参与“保存 episode.npz 和 metadata.json”。
            phase_id=np.asarray([phase_to_id[item] for item in self._phases], dtype=np.int16),
# 【L0147】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0148】得到 `has_images`，它在本项目中表示本功能块中的 `has_images` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `bool(self._images_enabled)`；`_images_enabled` 表示本功能块中的 `_images_enabled` 值。
        has_images = bool(self._images_enabled)
# 【L0149】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        manifest = {
# 【L0150】定义字典/JSON 字段 `format`，它表示“保存 episode.npz 和 metadata.json”中的 `format` 数据；字段值来自 `FORMAT_NAME`，因此保存/传递的是这个表达式当前计算出的结果。
            "format": FORMAT_NAME,
# 【L0151】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `self.prompt`，因此保存/传递的是这个表达式当前计算出的结果。
            "prompt": self.prompt,
# 【L0152】定义字典/JSON 字段 `control_hz`，它表示“保存 episode.npz 和 metadata.json”中的 `control_hz` 数据；字段值来自 `self.control_hz`，因此保存/传递的是这个表达式当前计算出的结果。
            "control_hz": self.control_hz,
# 【L0153】定义字典/JSON 字段 `frame_count`，它表示“保存 episode.npz 和 metadata.json”中的 `frame_count` 数据；字段值来自 `len(self._states)`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": len(self._states),
# 【L0154】定义字典/JSON 字段 `joint_names`，它表示“保存 episode.npz 和 metadata.json”中的 `joint_names` 数据；字段值来自 `list(JOINT_NAMES)`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_names": list(JOINT_NAMES),
# 【L0155】定义字典/JSON 字段 `observation_state_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `observation_state_semantics` 数据；字段值来自 `[*JOINT_NAMES, "gripper_normalized"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "observation_state_semantics": [*JOINT_NAMES, "gripper_normalized"],
# 【L0156】定义字典/JSON 字段 `action_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `action_semantics` 数据；字段值来自 `[`，因此保存/传递的是这个表达式当前计算出的结果。
            "action_semantics": [
# 【L0157】把运算项 `*(f"{name}_absolute_target_rad" for name in JOINT_NAMES),` 接到上一行未结束的数学公式；`f` 表示本功能块中的 `f` 值；`name` 表示本功能块中的 `name` 值；`_absolute_target_rad` 表示目标相关值，整条公式用于“保存 episode.npz 和 metadata.json”。
                *(f"{name}_absolute_target_rad" for name in JOINT_NAMES),
# 【L0158】提供文本片段 `"gripper_normalized_target"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“保存 episode.npz 和 metadata.json”中的帮助说明、错误原因、任务名称或报告文字。
                "gripper_normalized_target",
# 【L0159】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            ],
# 【L0160】定义字典/JSON 字段 `cube_pose_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `cube_pose_semantics` 数据；字段值来自 `["x", "y", "z", "qw", "qx", "qy", "qz"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "cube_pose_semantics": ["x", "y", "z", "qw", "qx", "qy", "qz"],
# 【L0161】定义字典/JSON 字段 `phase_names`，它表示“保存 episode.npz 和 metadata.json”中的 `phase_names` 数据；字段值来自 `phase_names`，因此保存/传递的是这个表达式当前计算出的结果。
            "phase_names": phase_names,
# 【L0162】定义字典/JSON 字段 `images_recorded`，它表示“保存 episode.npz 和 metadata.json”中的 `images_recorded` 数据；字段值来自 `has_images`，因此保存/传递的是这个表达式当前计算出的结果。
            "images_recorded": has_images,
# 【L0163】定义字典/JSON 字段 `image_paths`，它表示metadata 中逐帧外部/腕部 PNG 的相对路径列表；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "image_paths": {
# 【L0164】定义字典/JSON 字段 `external`，它表示“保存 episode.npz 和 metadata.json”中的 `external` 数据；字段值来自 `self._external_paths`，因此保存/传递的是这个表达式当前计算出的结果。
                "external": self._external_paths,
# 【L0165】定义字典/JSON 字段 `wrist`，它表示“保存 episode.npz 和 metadata.json”中的 `wrist` 数据；字段值来自 `self._wrist_paths`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist": self._wrist_paths,
# 【L0166】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
            },
# 【L0167】定义字典/JSON 字段 `frame_semantics`，它表示“保存 episode.npz 和 metadata.json”中的 `frame_semantics` 数据；字段值来自 `"observation immediately before applying action at the same index"`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_semantics": "observation immediately before applying action at the same index",
# 【L0168】定义字典/JSON 字段 `metadata`，它表示“保存 episode.npz 和 metadata.json”中的 `metadata` 数据；字段值来自 `self.metadata`，因此保存/传递的是这个表达式当前计算出的结果。
            "metadata": self.metadata,
# 【L0169】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        }
# 【L0170】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `(self.output_dir / "metadata.json").write_text(`。`output_dir` 表示输出相关值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息。
        (self.output_dir / "metadata.json").write_text(
# 【L0171】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `json.dumps(manifest, indent=2) + "\n", encoding="utf-8"`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
# 【L0172】结束或闭合当前语法结构；它属于“保存 episode.npz 和 metadata.json”。
        )
# 【L0173】结束当前函数并把 `manifest` 交回调用者；这个值的含义是：计算表达式 `manifest`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单。
        return manifest
# 【L0174】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0175】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0176】定义函数 `validate_episode(directory: Path, *, require_images: bool = False)`；调用者把参数交给它完成“重新读取磁盘数据并做独立完整性校验”，后面的缩进代码是具体实现。
def validate_episode(directory: Path, *, require_images: bool = False) -> dict[str, Any]:
# 【L0177】得到 `directory`，它在本项目中表示目录相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(directory)`；`directory` 表示目录相关值。
    directory = Path(directory)
# 【L0178】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0179】进入资源上下文 `np.load(directory / "episode.npz") as arrays`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with np.load(directory / "episode.npz") as arrays:
# 【L0180】得到 `timestamps`，它在本项目中表示本功能块中的 `timestamps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["timestamp_s"]`；`arrays` 表示本功能块中的 `arrays` 值；`timestamp_s` 表示本功能块中的 `timestamp_s` 值。
        timestamps = arrays["timestamp_s"]
# 【L0181】得到 `sim_steps`，它在本项目中表示仿真、步数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["sim_step"]`；`arrays` 表示本功能块中的 `arrays` 值；`sim_step` 表示仿真、步相关值。
        sim_steps = arrays["sim_step"]
# 【L0182】得到 `states`，它在本项目中表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["observation_state"]`；`arrays` 表示本功能块中的 `arrays` 值；`observation_state` 表示状态相关值。
        states = arrays["observation_state"]
# 【L0183】得到 `actions`，它在本项目中表示一个动作块；形状通常为 (时间步数, 7)；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["action"]`；`arrays` 表示本功能块中的 `arrays` 值；`action` 表示动作相关值。
        actions = arrays["action"]
# 【L0184】得到 `cube_poses`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["cube_pose_wxyz"]`；`arrays` 表示本功能块中的 `arrays` 值；`cube_pose_wxyz` 表示任务方块相关值。
        cube_poses = arrays["cube_pose_wxyz"]
# 【L0185】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["phase_id"]`；`arrays` 表示本功能块中的 `arrays` 值；`phase_id` 表示本功能块中的 `phase_id` 值。
        phase_ids = arrays["phase_id"]
# 【L0186】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0187】得到 `frame_count`，它在本项目中表示帧、数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `int(manifest["frame_count"])`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`frame_count` 表示帧、数量相关值。
    frame_count = int(manifest["frame_count"])
# 【L0188】把右侧结果写进 `errors: list[str]`（写入 `errors: list[str]` 指定的字段）；右侧具体做的是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    errors: list[str] = []
# 【L0189】判断 `manifest.get("format") != FORMAT_NAME` 是否成立；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`format` 表示本功能块中的 `format` 值
    if manifest.get("format") != FORMAT_NAME:
# 【L0190】对 `errors` 执行 `append`，把 `"unexpected episode format"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("unexpected episode format")
# 【L0191】得到 `expected_shapes`，它在本项目中表示本功能块中的 `expected_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    expected_shapes = {
# 【L0192】定义字典/JSON 字段 `timestamps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `timestamps` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "timestamps": (frame_count,),
# 【L0193】定义字典/JSON 字段 `sim_steps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `sim_steps` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "sim_steps": (frame_count,),
# 【L0194】定义字典/JSON 字段 `states`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `states` 数据；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": (frame_count, 7),
# 【L0195】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": (frame_count, 7),
# 【L0196】定义字典/JSON 字段 `cube_poses`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `cube_poses` 数据；字段值来自 `(frame_count, 7)`，因此保存/传递的是这个表达式当前计算出的结果。
        "cube_poses": (frame_count, 7),
# 【L0197】定义字典/JSON 字段 `phase_ids`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_ids` 数据；字段值来自 `(frame_count,)`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": (frame_count,),
# 【L0198】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0199】得到 `actual_shapes`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    actual_shapes = {
# 【L0200】定义字典/JSON 字段 `timestamps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `timestamps` 数据；字段值来自 `timestamps.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "timestamps": timestamps.shape,
# 【L0201】定义字典/JSON 字段 `sim_steps`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `sim_steps` 数据；字段值来自 `sim_steps.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "sim_steps": sim_steps.shape,
# 【L0202】定义字典/JSON 字段 `states`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `states` 数据；字段值来自 `states.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": states.shape,
# 【L0203】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `actions.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": actions.shape,
# 【L0204】定义字典/JSON 字段 `cube_poses`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `cube_poses` 数据；字段值来自 `cube_poses.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "cube_poses": cube_poses.shape,
# 【L0205】定义字典/JSON 字段 `phase_ids`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_ids` 数据；字段值来自 `phase_ids.shape`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": phase_ids.shape,
# 【L0206】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
# 【L0207】遍历 `expected_shapes.items()`，每次把当前元素放进 `name, shape`；这会逐个处理“重新读取磁盘数据并做独立完整性校验”所需的帧、episode、动作或实验 case。
    for name, shape in expected_shapes.items():
# 【L0208】判断 `actual_shapes[name] != shape` 是否成立；`actual_shapes` 表示物理仿真实际值相关值；`name` 表示本功能块中的 `name` 值；`shape` 表示本功能块中的 `shape` 值
        if actual_shapes[name] != shape:
# 【L0209】对 `errors` 执行 `append`，把 `f"{name} shape {actual_shapes[name]} != {shape}"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
            errors.append(f"{name} shape {actual_shapes[name]} != {shape}")
# 【L0210】判断 `frame_count < 2` 是否成立；`frame_count` 表示帧、数量相关值
    if frame_count < 2:
# 【L0211】对 `errors` 执行 `append`，把 `"episode must contain at least two frames"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("episode must contain at least two frames")
# 【L0212】判断 `not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses))` 是否成立；`all` 表示本功能块中的 `all` 值；`isfinite` 表示本功能块中的 `isfinite` 值；`item` 表示本功能块中的 `item` 值
    if not all(np.isfinite(item).all() for item in (timestamps, states, actions, cube_poses)):
# 【L0213】对 `errors` 执行 `append`，把 `"episode contains non-finite numeric values"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("episode contains non-finite numeric values")
# 【L0214】判断 `len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0)` 是否成立；`timestamps` 表示本功能块中的 `timestamps` 值；`all` 表示本功能块中的 `all` 值；`diff` 表示本功能块中的 `diff` 值
    if len(timestamps) > 1 and not np.all(np.diff(timestamps) > 0.0):
# 【L0215】对 `errors` 执行 `append`，把 `"timestamps are not strictly increasing"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("timestamps are not strictly increasing")
# 【L0216】判断 `len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0)` 是否成立；`sim_steps` 表示仿真、步数相关值；`all` 表示本功能块中的 `all` 值；`diff` 表示本功能块中的 `diff` 值
    if len(sim_steps) > 1 and not np.all(np.diff(sim_steps) > 0):
# 【L0217】对 `errors` 执行 `append`，把 `"simulation steps are not strictly increasing"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("simulation steps are not strictly increasing")
# 【L0218】判断 `states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0))` 是否成立；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；`size` 表示本功能块中的 `size` 值；`all` 表示本功能块中的 `all` 值
    if states.size and not np.all((states[:, 6] >= 0.0) & (states[:, 6] <= 1.0)):
# 【L0219】对 `errors` 执行 `append`，把 `"observed gripper values leave [0, 1]"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("observed gripper values leave [0, 1]")
# 【L0220】判断 `actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0))` 是否成立；`actions` 表示一个动作块；形状通常为 (时间步数, 7)；`size` 表示本功能块中的 `size` 值；`all` 表示本功能块中的 `all` 值
    if actions.size and not np.all((actions[:, 6] >= 0.0) & (actions[:, 6] <= 1.0)):
# 【L0221】对 `errors` 执行 `append`，把 `"action gripper values leave [0, 1]"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("action gripper values leave [0, 1]")
# 【L0222】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `manifest.get("phase_names", [])`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
    phase_names = manifest.get("phase_names", [])
# 【L0223】判断 `phase_ids.size and (` 是否成立；`phase_ids` 表示每一帧所处专家阶段的整数编号；`size` 表示本功能块中的 `size` 值
    if phase_ids.size and (
# 【L0224】对 `np` 调用 `min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)`：调用 `np` 提供的 `min` 操作。本行产生的修改/返回值服务于“重新读取磁盘数据并做独立完整性校验”。
        np.min(phase_ids) < 0 or np.max(phase_ids) >= len(phase_names)
# 【L0225】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“重新读取磁盘数据并做独立完整性校验”。
    ):
# 【L0226】对 `errors` 执行 `append`，把 `"phase ids leave the manifest phase-name range"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("phase ids leave the manifest phase-name range")
# 【L0227】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0228】得到 `image_paths`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：metadata 中逐帧外部/腕部 PNG 的相对路径列表。
    image_paths = manifest.get("image_paths", {})
# 【L0229】得到 `external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `image_paths.get("external", [])`；`image_paths` 表示图像相关值；`get` 表示本功能块中的 `get` 值；`external` 表示外部相机相关值。
    external = image_paths.get("external", [])
# 【L0230】得到 `wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `image_paths.get("wrist", [])`；`image_paths` 表示图像相关值；`get` 表示本功能块中的 `get` 值；`wrist` 表示腕部相机相关值。
    wrist = image_paths.get("wrist", [])
# 【L0231】判断 `len(external) != frame_count or len(wrist) != frame_count` 是否成立；`external` 表示外部相机相关值；`frame_count` 表示帧、数量相关值；`wrist` 表示腕部相机相关值
    if len(external) != frame_count or len(wrist) != frame_count:
# 【L0232】对 `errors` 执行 `append`，把 `"image path lists do not match frame count"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("image path lists do not match frame count")
# 【L0233】得到 `images_recorded`，它在本项目中表示本功能块中的 `images_recorded` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `bool(manifest.get("images_recorded"))`；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`images_recorded` 表示本功能块中的 `images_recorded` 值。
    images_recorded = bool(manifest.get("images_recorded"))
# 【L0234】判断 `require_images and not images_recorded` 是否成立；`require_images` 表示本功能块中的 `require_images` 值；`images_recorded` 表示本功能块中的 `images_recorded` 值
    if require_images and not images_recorded:
# 【L0235】对 `errors` 执行 `append`，把 `"images are required but were not recorded"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
        errors.append("images are required but were not recorded")
# 【L0236】判断 `images_recorded` 是否成立；`images_recorded` 表示本功能块中的 `images_recorded` 值
    if images_recorded:
# 【L0237】得到 `missing_images`，它在本项目中表示本功能块中的 `missing_images` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        missing_images = [
# 【L0238】声明/传入参数 `relative`；在本项目中它表示本功能块中的 `relative` 值。
            relative
# 【L0239】开始遍历 `for relative in [*external, *wrist]` 中给出的序列，逐项完成“重新读取磁盘数据并做独立完整性校验”。
            for relative in [*external, *wrist]
# 【L0240】判断 `not relative or not (directory / relative).is_file()` 是否成立；`relative` 表示本功能块中的 `relative` 值；`directory` 表示目录相关值；`is_file` 表示本功能块中的 `is_file` 值
            if not relative or not (directory / relative).is_file()
# 【L0241】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
        ]
# 【L0242】判断 `missing_images` 是否成立；`missing_images` 表示本功能块中的 `missing_images` 值
        if missing_images:
# 【L0243】对 `errors` 执行 `append`，把 `f"missing {len(missing_images)} image files"` 加入已有结果；该集合表示本功能块中的 `errors` 值，随后会用于“重新读取磁盘数据并做独立完整性校验”。
            errors.append(f"missing {len(missing_images)} image files")
# 【L0244】空行：分隔“重新读取磁盘数据并做独立完整性校验”中的逻辑段，让结构更容易看清。

# 【L0245】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0246】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if not errors else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if not errors else "fail",
# 【L0247】定义字典/JSON 字段 `format`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `format` 数据；字段值来自 `manifest.get("format")`，因此保存/传递的是这个表达式当前计算出的结果。
        "format": manifest.get("format"),
# 【L0248】定义字典/JSON 字段 `frame_count`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `frame_count` 数据；字段值来自 `frame_count`，因此保存/传递的是这个表达式当前计算出的结果。
        "frame_count": frame_count,
# 【L0249】定义字典/JSON 字段 `duration_s`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `duration_s` 数据；字段值来自 `float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0`，因此保存/传递的是这个表达式当前计算出的结果。
        "duration_s": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
# 【L0250】定义字典/JSON 字段 `images_recorded`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `images_recorded` 数据；字段值来自 `images_recorded`，因此保存/传递的是这个表达式当前计算出的结果。
        "images_recorded": images_recorded,
# 【L0251】定义字典/JSON 字段 `phase_names`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `phase_names` 数据；字段值来自 `manifest.get("phase_names", [])`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_names": manifest.get("phase_names", []),
# 【L0252】定义字典/JSON 字段 `all_finite`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `all_finite` 数据；字段值来自 `not any("non-finite" in item for item in errors)`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_finite": not any("non-finite" in item for item in errors),
# 【L0253】定义字典/JSON 字段 `errors`，它表示“重新读取磁盘数据并做独立完整性校验”中的 `errors` 数据；字段值来自 `errors`，因此保存/传递的是这个表达式当前计算出的结果。
        "errors": errors,
# 【L0254】结束或闭合当前语法结构；它属于“重新读取磁盘数据并做独立完整性校验”。
    }
```
