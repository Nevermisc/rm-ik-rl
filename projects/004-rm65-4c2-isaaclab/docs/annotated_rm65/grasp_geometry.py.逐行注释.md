# `grasp_geometry.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/grasp_geometry.py`
- 快照 SHA-256：`24d3e1733bbfa879e4c07ef0f3fecdb76f6a010d5e994154b5a06776922f43d0`
- 总行数：105
- 程序作用：用纯 NumPy 从已校准的侧抓姿态推导顶部抓取姿态，并可在两种旋转之间按轴角插值。
- 推荐读法：先理解输入输出都是 3D 位置/3×3 旋转矩阵，再看基向量怎样从局部坐标映射到世界坐标。

## 功能块地图

- 第 1-6 行：依赖
- 第 9-49 行：沿相对轴角在两个旋转矩阵之间插值
- 第 52-80 行：顶部抓取函数接口、输入转换和 shape 校验
- 第 81-90 行：从参考姿态求 link→block、闭合轴和切向轴局部基
- 第 91-105 行：构造世界顶部抓取基、计算目标旋转和 link 位置

## 函数/类索引

- `interpolate_rotation_matrix()`：第 9-49 行
- `compute_top_down_link_pose()`：第 52-105 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Pure NumPy helpers for deriving RM65 grasp poses."""
# 【L0003】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0006】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0007】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0008】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0009】定义函数 interpolate_rotation_matrix；其职责属于“沿相对轴角在两个旋转矩阵之间插值”，缩进块是函数体。
def interpolate_rotation_matrix(
# 【L0010】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
    start_rotation: np.ndarray,
# 【L0011】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
    target_rotation: np.ndarray,
# 【L0012】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
    fraction: float,
# 【L0013】开始一个缩进代码块或键值结构；该块负责“沿相对轴角在两个旋转矩阵之间插值”。
) -> np.ndarray:
# 【L0014】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Interpolate two rotation matrices along their relative axis-angle."""
# 【L0015】空行：分隔“沿相对轴角在两个旋转矩阵之间插值”中的逻辑段，让结构更容易看清。

# 【L0016】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 <= fraction <= 1.0:
# 【L0017】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("rotation interpolation fraction must be between 0 and 1")
# 【L0018】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“沿相对轴角在两个旋转矩阵之间插值”。
    start = np.asarray(start_rotation, dtype=np.float64)
# 【L0019】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“沿相对轴角在两个旋转矩阵之间插值”。
    target = np.asarray(target_rotation, dtype=np.float64)
# 【L0020】计算并保存变量 `relative`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
    relative = target @ start.T
# 【L0021】调用 `np.clip`：把数值限制在给定上下界内。本行位于“沿相对轴角在两个旋转矩阵之间插值”。
    cosine = np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)
# 【L0022】计算并保存变量 `angle`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
    angle = float(np.arccos(cosine))
# 【L0023】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if angle < 1e-10:
# 【L0024】结束当前函数并把结果交给调用者；这里完成“沿相对轴角在两个旋转矩阵之间插值”的输出。
        return start.copy()
# 【L0025】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(np.sin(angle)) < 1e-8:
# 【L0026】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("rotation interpolation is ambiguous at 180 degrees")
# 【L0027】调用 `np.array`：创建 NumPy 数组。本行位于“沿相对轴角在两个旋转矩阵之间插值”。
    axis = np.array(
# 【L0028】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“沿相对轴角在两个旋转矩阵之间插值”。
        [
# 【L0029】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
            relative[2, 1] - relative[1, 2],
# 【L0030】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
            relative[0, 2] - relative[2, 0],
# 【L0031】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“沿相对轴角在两个旋转矩阵之间插值”。
            relative[1, 0] - relative[0, 1],
# 【L0032】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
        ],
# 【L0033】计算并保存变量 `dtype`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
        dtype=np.float64,
# 【L0034】执行“沿相对轴角在两个旋转矩阵之间插值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ) / (2.0 * np.sin(angle))
# 【L0035】调用 `np.array`：创建 NumPy 数组。本行位于“沿相对轴角在两个旋转矩阵之间插值”。
    skew = np.array(
# 【L0036】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“沿相对轴角在两个旋转矩阵之间插值”。
        [
# 【L0037】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“沿相对轴角在两个旋转矩阵之间插值”。
            [0.0, -axis[2], axis[1]],
# 【L0038】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“沿相对轴角在两个旋转矩阵之间插值”。
            [axis[2], 0.0, -axis[0]],
# 【L0039】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“沿相对轴角在两个旋转矩阵之间插值”。
            [-axis[1], axis[0], 0.0],
# 【L0040】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
        ],
# 【L0041】计算并保存变量 `dtype`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
        dtype=np.float64,
# 【L0042】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
    )
# 【L0043】计算并保存变量 `partial_angle`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
    partial_angle = fraction * angle
# 【L0044】计算并保存变量 `partial`；该值服务于“沿相对轴角在两个旋转矩阵之间插值”。
    partial = (
# 【L0045】执行“沿相对轴角在两个旋转矩阵之间插值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        np.eye(3)
# 【L0046】执行“沿相对轴角在两个旋转矩阵之间插值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        + np.sin(partial_angle) * skew
# 【L0047】执行“沿相对轴角在两个旋转矩阵之间插值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        + (1.0 - np.cos(partial_angle)) * (skew @ skew)
# 【L0048】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
    )
# 【L0049】结束当前函数并把结果交给调用者；这里完成“沿相对轴角在两个旋转矩阵之间插值”的输出。
    return partial @ start
# 【L0050】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0051】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0052】定义函数 compute_top_down_link_pose；其职责属于“顶部抓取函数接口、输入转换和 shape 校验”，缩进块是函数体。
def compute_top_down_link_pose(
# 【L0053】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“顶部抓取函数接口、输入转换和 shape 校验”。
    reference_link_position: np.ndarray,
# 【L0054】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“顶部抓取函数接口、输入转换和 shape 校验”。
    reference_link_rotation: np.ndarray,
# 【L0055】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“顶部抓取函数接口、输入转换和 shape 校验”。
    block_position: np.ndarray,
# 【L0056】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“顶部抓取函数接口、输入转换和 shape 校验”。
    yaw_rad: float,
# 【L0057】计算并保存变量 `tilt_rad`；该值服务于“顶部抓取函数接口、输入转换和 shape 校验”。
    tilt_rad: float = 0.0,
# 【L0058】计算并保存变量 `blend_fraction`；该值服务于“顶部抓取函数接口、输入转换和 shape 校验”。
    blend_fraction: float = 1.0,
# 【L0059】计算并保存变量 `reference_closing_axis_world`；该值服务于“顶部抓取函数接口、输入转换和 shape 校验”。
    reference_closing_axis_world: np.ndarray | None = None,
# 【L0060】开始一个缩进代码块或键值结构；该块负责“顶部抓取函数接口、输入转换和 shape 校验”。
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
# 【L0061】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Rotate a calibrated link-to-block transform into an above-table grasp.
# 【L0062】空行：分隔“顶部抓取函数接口、输入转换和 shape 校验”中的逻辑段，让结构更容易看清。

# 【L0063】执行“顶部抓取函数接口、输入转换和 shape 校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    The reference pose already aligns the gripper pads with the block. This
# 【L0064】执行“顶部抓取函数接口、输入转换和 shape 校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    function preserves that local link-to-block vector while mapping it to
# 【L0065】执行“顶部抓取函数接口、输入转换和 shape 校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    world -z. The gripper closing axis remains horizontal and follows yaw.
# 【L0066】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0067】空行：分隔“顶部抓取函数接口、输入转换和 shape 校验”中的逻辑段，让结构更容易看清。

# 【L0068】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“顶部抓取函数接口、输入转换和 shape 校验”。
    link_position = np.asarray(reference_link_position, dtype=np.float64)
# 【L0069】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“顶部抓取函数接口、输入转换和 shape 校验”。
    link_rotation = np.asarray(reference_link_rotation, dtype=np.float64)
# 【L0070】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“顶部抓取函数接口、输入转换和 shape 校验”。
    block = np.asarray(block_position, dtype=np.float64)
# 【L0071】计算并保存变量 `closing_world`；该值服务于“顶部抓取函数接口、输入转换和 shape 校验”。
    closing_world = (
# 【L0072】调用 `np.array`：创建 NumPy 数组。本行位于“顶部抓取函数接口、输入转换和 shape 校验”。
        np.array([0.0, 1.0, 0.0], dtype=np.float64)
# 【L0073】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if reference_closing_axis_world is None
# 【L0074】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“顶部抓取函数接口、输入转换和 shape 校验”。
        else np.asarray(reference_closing_axis_world, dtype=np.float64)
# 【L0075】结束或闭合当前语法结构；它属于“顶部抓取函数接口、输入转换和 shape 校验”。
    )
# 【L0076】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if link_position.shape != (3,) or block.shape != (3,):
# 【L0077】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("link and block positions must each have shape (3,)")
# 【L0078】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if link_rotation.shape != (3, 3):
# 【L0079】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("link rotation must have shape (3, 3)")
# 【L0080】空行：分隔“顶部抓取函数接口、输入转换和 shape 校验”中的逻辑段，让结构更容易看清。

# 【L0081】计算并保存变量 `block_from_link_local`；该值服务于“从参考姿态求 link→block、闭合轴和切向轴局部基”。
    block_from_link_local = link_rotation.T @ (block - link_position)
# 【L0082】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“从参考姿态求 link→block、闭合轴和切向轴局部基”。
    local_forward = block_from_link_local / np.linalg.norm(block_from_link_local)
# 【L0083】计算并保存变量 `local_closing`；该值服务于“从参考姿态求 link→block、闭合轴和切向轴局部基”。
    local_closing = link_rotation.T @ closing_world
# 【L0084】执行“从参考姿态求 link→block、闭合轴和切向轴局部基”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    local_closing -= np.dot(local_closing, local_forward) * local_forward
# 【L0085】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“从参考姿态求 link→block、闭合轴和切向轴局部基”。
    local_closing_norm = np.linalg.norm(local_closing)
# 【L0086】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if local_closing_norm < 1e-8:
# 【L0087】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("reference closing axis cannot be parallel to the block direction")
# 【L0088】执行“从参考姿态求 link→block、闭合轴和切向轴局部基”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    local_closing /= local_closing_norm
# 【L0089】计算并保存变量 `local_tangent`；该值服务于“从参考姿态求 link→block、闭合轴和切向轴局部基”。
    local_tangent = np.cross(local_forward, local_closing)
# 【L0090】空行：分隔“从参考姿态求 link→block、闭合轴和切向轴局部基”中的逻辑段，让结构更容易看清。

# 【L0091】调用 `np.array`：创建 NumPy 数组。本行位于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    world_closing = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0], dtype=np.float64)
# 【L0092】调用 `np.array`：创建 NumPy 数组。本行位于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    horizontal_forward = np.array([-np.cos(yaw_rad), -np.sin(yaw_rad), 0.0], dtype=np.float64)
# 【L0093】计算并保存变量 `world_forward`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    world_forward = (
# 【L0094】调用 `np.array`：创建 NumPy 数组。本行位于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
        np.cos(tilt_rad) * np.array([0.0, 0.0, -1.0], dtype=np.float64)
# 【L0095】执行“构造世界顶部抓取基、计算目标旋转和 link 位置”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        + np.sin(tilt_rad) * horizontal_forward
# 【L0096】结束或闭合当前语法结构；它属于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    )
# 【L0097】计算并保存变量 `world_tangent`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    world_tangent = np.cross(world_forward, world_closing)
# 【L0098】计算并保存变量 `local_basis`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    local_basis = np.column_stack((local_closing, local_tangent, local_forward))
# 【L0099】计算并保存变量 `world_basis`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    world_basis = np.column_stack((world_closing, world_tangent, world_forward))
# 【L0100】计算并保存变量 `target_rotation`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    target_rotation = world_basis @ local_basis.T
# 【L0101】计算并保存变量 `blended_rotation`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    blended_rotation = interpolate_rotation_matrix(
# 【L0102】执行“构造世界顶部抓取基、计算目标旋转和 link 位置”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        link_rotation, target_rotation, blend_fraction
# 【L0103】结束或闭合当前语法结构；它属于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    )
# 【L0104】计算并保存变量 `blended_link_position`；该值服务于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    blended_link_position = block - blended_rotation @ block_from_link_local
# 【L0105】结束当前函数并把结果交给调用者；这里完成“构造世界顶部抓取基、计算目标旋转和 link 位置”的输出。
    return blended_link_position, blended_rotation, block_from_link_local
```
