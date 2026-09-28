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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】说明字符串 `Deterministic safety guard for a future seven-value RM65 policy action chunk.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Deterministic safety guard for a future seven-value RM65 policy action chunk."""
# 【L0002】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0003】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0005】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0007】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0008】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0009】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0010】得到 `RM65_LOWER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float32` 表示本功能块中的 `float32` 值。
RM65_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)
# 【L0011】得到 `RM65_UPPER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float32` 表示本功能块中的 `float32` 值。
RM65_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)
# 【L0012】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0013】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0014】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclasses.dataclass(frozen=True)
# 【L0015】定义 `GuardConfig` 类并继承 `object`；它把“依赖、关节限位和 guard 参数”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class GuardConfig:
# 【L0016】得到 `joint_limit_margin_rad`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.02` 的结果保存下来，供当前功能块后续使用。
    joint_limit_margin_rad: float = 0.02
# 【L0017】得到 `max_joint_step_rad`，它在本项目中表示关节、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.05` 的结果保存下来，供当前功能块后续使用。
    max_joint_step_rad: float = 0.05
# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】定义函数 `guard_action_chunk(参数在后续行继续)`；调用者把参数交给它完成“动作/当前状态的结构与数值校验”，后面的缩进代码是具体实现。
def guard_action_chunk(
# 【L0021】声明/传入参数 `actions`，类型提示为 `np.ndarray`；在本项目中它表示一个动作块；形状通常为 (时间步数, 7)。
    actions: np.ndarray,
# 【L0022】声明/传入参数 `current_joint_position`，类型提示为 `np.ndarray`；在本项目中它表示动作执行前实际观测到的六个 RM65 关节角。
    current_joint_position: np.ndarray,
# 【L0023】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `GuardConfig()`；`GuardConfig` 表示本功能块中的 `GuardConfig` 值。
    config: GuardConfig = GuardConfig(),
# 【L0024】以 `) -> tuple[np.ndarray, dict]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“动作/当前状态的结构与数值校验”。
) -> tuple[np.ndarray, dict]:
# 【L0025】说明字符串 `Validate and clamp RM65 absolute joint targets plus normalized gripper targets.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Validate and clamp RM65 absolute joint targets plus normalized gripper targets."""
# 【L0026】空行：分隔“动作/当前状态的结构与数值校验”中的逻辑段，让结构更容易看清。

# 【L0027】得到 `source`，它在本项目中表示转换前的原始数组；这里不代表任务里的源物体；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `actions, dtype=np.float32`（本功能块中的 `actions, dtype=np.float32` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    source = np.asarray(actions, dtype=np.float32)
# 【L0028】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `current_joint_position, dtype=np.float32`（当前值、关节相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    current = np.asarray(current_joint_position, dtype=np.float32)
# 【L0029】判断 `source.ndim != 2 or source.shape[1] != 7` 是否成立；`source` 表示转换前的原始数组；这里不代表任务里的源物体；`ndim` 表示本功能块中的 `ndim` 值；`shape` 表示本功能块中的 `shape` 值
    if source.ndim != 2 or source.shape[1] != 7:
# 【L0030】主动抛出 `ValueError(f"expected action shape (T, 7), got {source.shape}")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"expected action shape (T, 7), got {source.shape}")
# 【L0031】检查 `current.shape` 是否不等于要求的 `(6,)`；若不等，数据维度合同已被破坏，进入错误处理
    if current.shape != (6,):
# 【L0032】主动抛出 `ValueError(f"expected six current joints, got {current.shape}")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"expected six current joints, got {current.shape}")
# 【L0033】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
    if not np.isfinite(source).all() or not np.isfinite(current).all():
# 【L0034】主动抛出 `ValueError("action chunk and current joints must contain only finite values")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("action chunk and current joints must contain only finite values")
# 【L0035】判断 `config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0` 是否成立；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值；`max_joint_step_rad` 表示关节、步相关值
    if config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0:
# 【L0036】主动抛出 `ValueError("guard margins must be non-negative and step limit must be positive")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("guard margins must be non-negative and step limit must be positive")
# 【L0037】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0038】得到 `lower`，它在本项目中表示在机械限位内额外留出 margin 后的六关节安全下界；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RM65_LOWER_RAD + config.joint_limit_margin_rad`；`RM65_LOWER_RAD` 表示RM65 机械约束或项目常量；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值。
    lower = RM65_LOWER_RAD + config.joint_limit_margin_rad
# 【L0039】得到 `upper`，它在本项目中表示在机械限位内额外留出 margin 后的六关节安全上界；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RM65_UPPER_RAD - config.joint_limit_margin_rad`；`RM65_UPPER_RAD` 表示RM65 机械约束或项目常量；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值。
    upper = RM65_UPPER_RAD - config.joint_limit_margin_rad
# 【L0040】得到 `safe`，它在本项目中表示即将返回的安全动作副本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    safe = source.copy()
# 【L0041】得到 `joint_limit_clamps`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    joint_limit_clamps = 0
# 【L0042】得到 `step_clamps`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    step_clamps = 0
# 【L0043】得到 `previous`，它在本项目中表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    previous = np.clip(current, lower, upper)
# 【L0044】遍历 `range(len(safe))`，每次把当前元素放进 `index`；这会逐个处理“逐时间步裁剪关节限位、关节增量和夹爪值”所需的帧、episode、动作或实验 case。
    for index in range(len(safe)):
# 【L0045】得到 `joint_target`，它在本项目中表示当前动作时间步中，先按机械关节上下限裁剪后的六关节目标；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        joint_target = np.clip(safe[index, :6], lower, upper)
# 【L0046】用 `joint_limit_clamps + int(np.count_nonzero(joint_target != safe[index, :6]))` 更新 `joint_limit_clamps` 原值；`joint_limit_clamps` 表示关节相关值，常用于累计步数、距离、损失或成功次数。
        joint_limit_clamps += int(np.count_nonzero(joint_target != safe[index, :6]))
# 【L0047】得到 `step_lower`，它在本项目中表示步、下界相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `previous - config.max_joint_step_rad`；`previous` 表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`max_joint_step_rad` 表示关节、步相关值。
        step_lower = previous - config.max_joint_step_rad
# 【L0048】得到 `step_upper`，它在本项目中表示步、上界相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `previous + config.max_joint_step_rad`；`previous` 表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`max_joint_step_rad` 表示关节、步相关值。
        step_upper = previous + config.max_joint_step_rad
# 【L0049】得到 `stepped`，它在本项目中表示再按相邻动作最大变化量裁剪后的最终六关节目标；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        stepped = np.clip(joint_target, step_lower, step_upper)
# 【L0050】用 `step_clamps + int(np.count_nonzero(stepped != joint_target))` 更新 `step_clamps` 原值；`step_clamps` 表示步相关值，常用于累计步数、距离、损失或成功次数。
        step_clamps += int(np.count_nonzero(stepped != joint_target))
# 【L0051】把右侧结果写进 `safe[index, :6]`（写入 `safe[index, :6]` 指定的字段）；右侧具体做的是：计算表达式 `stepped`；`stepped` 表示再按相邻动作最大变化量裁剪后的最终六关节目标。
        safe[index, :6] = stepped
# 【L0052】把右侧结果写进 `safe[index, 6]`（写入 `safe[index, 6]` 指定的字段）；右侧具体做的是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        safe[index, 6] = np.clip(safe[index, 6], 0.0, 1.0)
# 【L0053】得到 `previous`，它在本项目中表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `stepped`；`stepped` 表示再按相邻动作最大变化量裁剪后的最终六关节目标。
        previous = stepped
# 【L0054】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】得到 `diagnostics`，它在本项目中表示本功能块中的 `diagnostics` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    diagnostics = {
# 【L0056】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0057】定义字典/JSON 字段 `input_shape`，它表示“返回安全动作和裁剪诊断”中的 `input_shape` 数据；字段值来自 `list(source.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
        "input_shape": list(source.shape),
# 【L0058】定义字典/JSON 字段 `all_finite`，它表示“返回安全动作和裁剪诊断”中的 `all_finite` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_finite": True,
# 【L0059】定义字典/JSON 字段 `joint_limit_margin_rad`，它表示“返回安全动作和裁剪诊断”中的 `joint_limit_margin_rad` 数据；字段值来自 `config.joint_limit_margin_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_limit_margin_rad": config.joint_limit_margin_rad,
# 【L0060】定义字典/JSON 字段 `max_joint_step_rad`，它表示“返回安全动作和裁剪诊断”中的 `max_joint_step_rad` 数据；字段值来自 `config.max_joint_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "max_joint_step_rad": config.max_joint_step_rad,
# 【L0061】定义字典/JSON 字段 `joint_limit_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `joint_limit_clamp_count` 数据；字段值来自 `joint_limit_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_limit_clamp_count": joint_limit_clamps,
# 【L0062】定义字典/JSON 字段 `joint_step_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `joint_step_clamp_count` 数据；字段值来自 `step_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_step_clamp_count": step_clamps,
# 【L0063】定义字典/JSON 字段 `gripper_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `gripper_clamp_count` 数据；字段值来自 `int(np.count_nonzero(safe[:, 6] != source[:, 6]))`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_clamp_count": int(np.count_nonzero(safe[:, 6] != source[:, 6])),
# 【L0064】定义字典/JSON 字段 `maximum_output_step_rad`，它表示“返回安全动作和裁剪诊断”中的 `maximum_output_step_rad` 数据；字段值来自 `float(`，因此保存/传递的是这个表达式当前计算出的结果。
        "maximum_output_step_rad": float(
# 【L0065】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
            np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))
# 【L0066】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
        ),
# 【L0067】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
    }
# 【L0068】结束当前函数并把 `safe, diagnostics` 交回调用者；这个值的含义是：计算表达式 `safe, diagnostics`；`safe` 表示即将返回的安全动作副本；`diagnostics` 表示本功能块中的 `diagnostics` 值。
    return safe, diagnostics
```
