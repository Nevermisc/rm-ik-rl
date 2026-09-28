# `action_guard.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/action_guard.py`
- 快照 SHA-256：`9c21f07c778dab893c3b9836698df76b07588e6971806b2d88f571e06f7856e1`
- 总行数：68
- 程序作用：在仿真执行前对 π0.5 动作做形状、有限数、关节限位、单步变化和夹爪范围检查。
- 推荐读法：这是策略输出和仿真执行器之间的确定性防线。

## 功能块地图

- 第 1-17 行：依赖、关节限位和 guard 参数
- 第 20-36 行：动作/当前状态的结构与数值校验
- 第 38-53 行：逐时间步裁剪关节限位、关节增量和夹爪值
- 第 55-68 行：返回安全动作和裁剪诊断

## 函数/类索引

- `class GuardConfig`：第 15-17 行
- `guard_action_chunk()`：第 20-68 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Deterministic safety guard for a future seven-value RM65 policy action chunk."""
# 【L0002】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0003】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0004】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0005】导入 dataclasses：标准库数据类工具，用较少样板代码声明配置/记录对象；后面的代码会调用其中的类或函数。
import dataclasses
# 【L0006】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0007】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0008】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0009】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0010】调用 `np.array`：创建 NumPy 数组。本行位于“依赖、关节限位和 guard 参数”。
RM65_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)
# 【L0011】调用 `np.array`：创建 NumPy 数组。本行位于“依赖、关节限位和 guard 参数”。
RM65_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)
# 【L0012】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0013】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0014】数据类装饰器：自动生成初始化等方法；frozen=True 表示创建后不允许改字段。
@dataclasses.dataclass(frozen=True)
# 【L0015】定义类 GuardConfig；把相关配置、状态和方法组织成一个可复用对象。
class GuardConfig:
# 【L0016】计算并保存变量 `joint_limit_margin_rad`；该值服务于“依赖、关节限位和 guard 参数”。
    joint_limit_margin_rad: float = 0.02
# 【L0017】计算并保存变量 `max_joint_step_rad`；该值服务于“依赖、关节限位和 guard 参数”。
    max_joint_step_rad: float = 0.05
# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】定义函数 guard_action_chunk；其职责属于“动作/当前状态的结构与数值校验”，缩进块是函数体。
def guard_action_chunk(
# 【L0021】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“动作/当前状态的结构与数值校验”。
    actions: np.ndarray,
# 【L0022】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“动作/当前状态的结构与数值校验”。
    current_joint_position: np.ndarray,
# 【L0023】给变量 `config` 赋值：当前函数使用的配置对象。
    config: GuardConfig = GuardConfig(),
# 【L0024】开始一个缩进代码块或键值结构；该块负责“动作/当前状态的结构与数值校验”。
) -> tuple[np.ndarray, dict]:
# 【L0025】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Validate and clamp RM65 absolute joint targets plus normalized gripper targets."""
# 【L0026】空行：分隔“动作/当前状态的结构与数值校验”中的逻辑段，让结构更容易看清。

# 【L0027】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“动作/当前状态的结构与数值校验”。
    source = np.asarray(actions, dtype=np.float32)
# 【L0028】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“动作/当前状态的结构与数值校验”。
    current = np.asarray(current_joint_position, dtype=np.float32)
# 【L0029】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if source.ndim != 2 or source.shape[1] != 7:
# 【L0030】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"expected action shape (T, 7), got {source.shape}")
# 【L0031】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if current.shape != (6,):
# 【L0032】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"expected six current joints, got {current.shape}")
# 【L0033】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not np.isfinite(source).all() or not np.isfinite(current).all():
# 【L0034】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("action chunk and current joints must contain only finite values")
# 【L0035】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0:
# 【L0036】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("guard margins must be non-negative and step limit must be positive")
# 【L0037】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0038】计算并保存变量 `lower`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
    lower = RM65_LOWER_RAD + config.joint_limit_margin_rad
# 【L0039】计算并保存变量 `upper`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
    upper = RM65_UPPER_RAD - config.joint_limit_margin_rad
# 【L0040】给变量 `safe` 赋值：即将返回的安全动作副本。
    safe = source.copy()
# 【L0041】计算并保存变量 `joint_limit_clamps`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
    joint_limit_clamps = 0
# 【L0042】计算并保存变量 `step_clamps`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
    step_clamps = 0
# 【L0043】调用 `np.clip`：把数值限制在给定上下界内。本行位于“逐时间步裁剪关节限位、关节增量和夹爪值”。
    previous = np.clip(current, lower, upper)
# 【L0044】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for index in range(len(safe)):
# 【L0045】调用 `np.clip`：把数值限制在给定上下界内。本行位于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        joint_target = np.clip(safe[index, :6], lower, upper)
# 【L0046】执行“逐时间步裁剪关节限位、关节增量和夹爪值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        joint_limit_clamps += int(np.count_nonzero(joint_target != safe[index, :6]))
# 【L0047】计算并保存变量 `step_lower`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        step_lower = previous - config.max_joint_step_rad
# 【L0048】计算并保存变量 `step_upper`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        step_upper = previous + config.max_joint_step_rad
# 【L0049】调用 `np.clip`：把数值限制在给定上下界内。本行位于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        stepped = np.clip(joint_target, step_lower, step_upper)
# 【L0050】执行“逐时间步裁剪关节限位、关节增量和夹爪值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        step_clamps += int(np.count_nonzero(stepped != joint_target))
# 【L0051】执行“逐时间步裁剪关节限位、关节增量和夹爪值”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        safe[index, :6] = stepped
# 【L0052】调用 `np.clip`：把数值限制在给定上下界内。本行位于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        safe[index, 6] = np.clip(safe[index, 6], 0.0, 1.0)
# 【L0053】计算并保存变量 `previous`；该值服务于“逐时间步裁剪关节限位、关节增量和夹爪值”。
        previous = stepped
# 【L0054】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】计算并保存变量 `diagnostics`；该值服务于“返回安全动作和裁剪诊断”。
    diagnostics = {
# 【L0056】定义字典/JSON 字段 `status`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0057】定义字典/JSON 字段 `input_shape`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "input_shape": list(source.shape),
# 【L0058】定义字典/JSON 字段 `all_finite`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "all_finite": True,
# 【L0059】定义字典/JSON 字段 `joint_limit_margin_rad`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "joint_limit_margin_rad": config.joint_limit_margin_rad,
# 【L0060】定义字典/JSON 字段 `max_joint_step_rad`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "max_joint_step_rad": config.max_joint_step_rad,
# 【L0061】定义字典/JSON 字段 `joint_limit_clamp_count`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "joint_limit_clamp_count": joint_limit_clamps,
# 【L0062】定义字典/JSON 字段 `joint_step_clamp_count`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "joint_step_clamp_count": step_clamps,
# 【L0063】定义字典/JSON 字段 `gripper_clamp_count`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "gripper_clamp_count": int(np.count_nonzero(safe[:, 6] != source[:, 6])),
# 【L0064】定义字典/JSON 字段 `maximum_output_step_rad`；它把“返回安全动作和裁剪诊断”中的结果用稳定键名记录下来。
        "maximum_output_step_rad": float(
# 【L0065】调用 `np.diff`：计算相邻元素或相邻帧之差。本行位于“返回安全动作和裁剪诊断”。
            np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))
# 【L0066】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
        ),
# 【L0067】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
    }
# 【L0068】结束当前函数并把结果交给调用者；这里完成“返回安全动作和裁剪诊断”的输出。
    return safe, diagnostics
```
