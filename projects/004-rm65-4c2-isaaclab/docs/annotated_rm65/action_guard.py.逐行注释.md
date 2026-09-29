# `action_guard.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/action_guard.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`9c21f07c778dab893c3b9836698df76b07588e6971806b2d88f571e06f7856e1`
- 总行数：68

## 1. 先把这个程序放进整个项目

- 所处阶段：闭环安全：模型动作进入仿真控制器前的确定性检查。
- 输入：原始 (T,7) 动作块和当前六关节实际位置。
- 输出：限位/限步长/夹爪裁剪后的动作块与裁剪统计。
- 一句话作用：在仿真执行前对 π0.5 动作做形状、有限数、关节限位、单步变化和夹爪范围检查。

### 为什么要写它

- 原先的问题：学习模型可能输出 NaN、越过机械限位或相邻动作跳变过大，直接执行会让仿真失稳且掩盖模型问题。
- 采用的解决办法：拒绝非有限值和错误 shape，逐步按关节限位、0.05 rad 步长与夹爪 0～1 范围裁剪。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **ndarray**：NumPy ndarray：带 shape/dtype 的多维数值数组，用于图像、关节、动作和统计计算。
- **dataclass**：数据类：根据字段声明自动生成初始化方法；适合固定配置或结构化记录。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-15` `64c584a1` **Add RM65 and 4C2 Isaac Lab migration baseline**：建立 RM65+4C2 资产、策略接口和基础仿真迁移骨架。

### 与上一版教学快照的源码差异

- 当前源码与上一版教学快照一致。

## 4. 模块地图

- 模块 1｜第 1-19 行：依赖、关节限位和 guard 参数
- 模块 2｜第 20-37 行：动作/当前状态的结构与数值校验
- 模块 3｜第 38-54 行：逐时间步裁剪关节限位、关节增量和夹爪值
- 模块 4｜第 55-68 行：返回安全动作和裁剪诊断

### 函数/类快速索引

- `class GuardConfig`：第 15-17 行
- `guard_action_chunk()`：第 20-68 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：依赖、关节限位和 guard 参数（源码第 1-19 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：依赖、关节限位和 guard 参数。
- 下游：处理结果继续交给模块 2“动作/当前状态的结构与数值校验”。

### 5.B 为什么需要这一组代码

这一组负责“依赖、关节限位和 guard 参数”。它服务于本文件要解决的总问题：学习模型可能输出 NaN、越过机械限位或相邻动作跳变过大，直接执行会让仿真失稳且掩盖模型问题。 这一组的处理结果会参与：拒绝非有限值和错误 shape，逐步按关节限位、0.05 rad 步长与夹爪 0～1 范围裁剪。

### 5.C 本模块主要变量

- `guard`：action guard 返回的裁剪次数、最大步长等诊断字典。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。

### 5.D 本模块首次阅读要认识的调用

- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `dataclasses.dataclass(...)`：圆括号表示真正执行调用；把带类型标注的类变成数据类，自动生成构造函数等样板方法。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0001】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Deterministic safety guard for a future seven-value RM65 policy action chunk.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Deterministic safety guard for a future seven-value RM65 policy action chunk."""
# 【L0002】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0003】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0005】语法拆解：`import` 加载模块；`dataclasses` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0007】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0008】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0009】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0010】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RM65_LOWER_RAD`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28]`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `RM65_LOWER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float32` 表示本功能块中的 `float32` 值。
RM65_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28], dtype=np.float32)
# 【L0011】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RM65_UPPER_RAD`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[3.106, 2.2689, 2.356, 3.106, 2.234, 6.28]`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `RM65_UPPER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float32` 表示本功能块中的 `float32` 值。
RM65_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28], dtype=np.float32)
# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0014】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclasses.dataclass(frozen=True)
# 【L0015】语法拆解：`class` 定义类 `GuardConfig`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `GuardConfig` 类并继承 `object`；它把“依赖、关节限位和 guard 参数”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class GuardConfig:
# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_limit_margin_rad: float`。右侧语法为：`0.02` 是直接写在源码中的数值常量。
# 【项目含义】得到 `joint_limit_margin_rad`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.02` 的结果保存下来，供当前功能块后续使用。
    joint_limit_margin_rad: float = 0.02
# 【L0017】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_joint_step_rad: float`。右侧语法为：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】得到 `max_joint_step_rad`，它在本项目中表示关节、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.05` 的结果保存下来，供当前功能块后续使用。
    max_joint_step_rad: float = 0.05
# 【L0018】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖、关节限位和 guard 参数”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“依赖、关节限位和 guard 参数”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：动作/当前状态的结构与数值校验（源码第 20-37 行）

### 5.A 数据流位置

- 上游：模块 1“依赖、关节限位和 guard 参数”。
- 本模块：动作/当前状态的结构与数值校验。
- 下游：处理结果继续交给模块 3“逐时间步裁剪关节限位、关节增量和夹爪值”。

### 5.B 为什么需要这一组代码

这一组负责“动作/当前状态的结构与数值校验”。它服务于本文件要解决的总问题：学习模型可能输出 NaN、越过机械限位或相邻动作跳变过大，直接执行会让仿真失稳且掩盖模型问题。 这一组的处理结果会参与：拒绝非有限值和错误 shape，逐步按关节限位、0.05 rad 步长与夹爪 0～1 范围裁剪。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `joints`：六个 RM65 关节位置的一维 NumPy 数组。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `current_joint_position`：动作执行前实际观测到的六个 RM65 关节角。
- `current`：float32 格式的当前六关节角。
- `guard`：action guard 返回的裁剪次数、最大步长等诊断字典。

### 5.D 本模块首次阅读要认识的调用

- `guard_action_chunk(...)`：圆括号表示真正执行调用；验证并裁剪策略动作，阻止越界和过大跳变。
- `GuardConfig(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `shape(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.isfinite(...)`：圆括号表示真正执行调用；检查是否存在 NaN 或正负无穷。
- `all(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`guard_action_chunk()`（第 20-68 行）

- 定义了什么：动作/当前状态的结构与数值校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`actions`：类型 `np.ndarray`；项目含义是一个动作块；形状通常为 (时间步数, 7)；`current_joint_position`：类型 `np.ndarray`；项目含义是动作执行前实际观测到的六个 RM65 关节角；`config`：类型 `GuardConfig`，默认 `GuardConfig()`；项目含义是RM65 π0.5 训练/推理使用的完整 OpenPI 配置
- 返回类型标注：`tuple[np.ndarray, dict]`。
- 函数体实际 return：`(safe, diagnostics)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:832` 的 `safe_actions, guard = guard_action_chunk(raw_actions, current_arm)`；`validate_rm65_checkpoint.py:71` 的 `safe_actions, guard = guard_action_chunk(actions, states[index, :6])`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0020】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `guard_action_chunk(参数在后续行继续)`；调用者把参数交给它完成“动作/当前状态的结构与数值校验”，后面的缩进代码是具体实现。
def guard_action_chunk(
# 【L0021】语法拆解：`actions` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `actions`，类型提示为 `np.ndarray`；在本项目中它表示一个动作块；形状通常为 (时间步数, 7)。
    actions: np.ndarray,
# 【L0022】语法拆解：`current_joint_position` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `current_joint_position`，类型提示为 `np.ndarray`；在本项目中它表示动作执行前实际观测到的六个 RM65 关节角。
    current_joint_position: np.ndarray,
# 【L0023】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config: GuardConfig`。右侧语法为：`GuardConfig` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `GuardConfig()`；`GuardConfig` 表示本功能块中的 `GuardConfig` 值。
    config: GuardConfig = GuardConfig(),
# 【L0024】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> tuple[np.ndarray, dict]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“动作/当前状态的结构与数值校验”。
) -> tuple[np.ndarray, dict]:
# 【L0025】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Validate and clamp RM65 absolute joint targets plus normalized gripper targets.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Validate and clamp RM65 absolute joint targets plus normalized gripper targets."""
# 【L0026】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“动作/当前状态的结构与数值校验”中的逻辑段，让结构更容易看清。

# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `actions`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `source`，它在本项目中表示转换前的原始数组；这里不代表任务里的源物体；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `actions, dtype=np.float32`（本功能块中的 `actions, dtype=np.float32` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    source = np.asarray(actions, dtype=np.float32)
# 【L0028】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `current_joint_position`；第 2 个实参 `dtype=np.float32`。
# 【项目含义】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `current_joint_position, dtype=np.float32`（当前值、关节相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    current = np.asarray(current_joint_position, dtype=np.float32)
# 【L0029】语法拆解：`if` 要求条件 `source.ndim != 2 or source.shape[1] != 7` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `source.ndim != 2 or source.shape[1] != 7` 是否成立；`source` 表示转换前的原始数组；这里不代表任务里的源物体；`ndim` 表示本功能块中的 `ndim` 值；`shape` 表示本功能块中的 `shape` 值
    if source.ndim != 2 or source.shape[1] != 7:
# 【L0030】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected action shape (T, 7), got {source.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected action shape (T, 7), got {source.shape}")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"expected action shape (T, 7), got {source.shape}")
# 【L0031】语法拆解：`if` 要求条件 `current.shape != (6,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `current.shape` 是否不等于要求的 `(6,)`；若不等，数据维度合同已被破坏，进入错误处理
    if current.shape != (6,):
# 【L0032】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected six current joints, got {current.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError(f"expected six current joints, got {current.shape}")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"expected six current joints, got {current.shape}")
# 【L0033】语法拆解：`if` 要求条件 `not np.isfinite(source).all() or not np.isfinite(current).all()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
    if not np.isfinite(source).all() or not np.isfinite(current).all():
# 【L0034】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("action chunk and current joints must contain only finite values")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("action chunk and current joints must contain only finite values")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("action chunk and current joints must contain only finite values")
# 【L0035】语法拆解：`if` 要求条件 `config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0` 是否成立；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值；`max_joint_step_rad` 表示关节、步相关值
    if config.joint_limit_margin_rad < 0 or config.max_joint_step_rad <= 0:
# 【L0036】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("guard margins must be non-negative and step limit must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("guard margins must be non-negative and step limit must be positive")` 并停止当前路径；说明当前输入违反“动作/当前状态的结构与数值校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("guard margins must be non-negative and step limit must be positive")
# 【L0037】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“动作/当前状态的结构与数值校验”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“动作/当前状态的结构与数值校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：逐时间步裁剪关节限位、关节增量和夹爪值（源码第 38-54 行）

### 5.A 数据流位置

- 上游：模块 2“动作/当前状态的结构与数值校验”。
- 本模块：逐时间步裁剪关节限位、关节增量和夹爪值。
- 下游：处理结果继续交给模块 4“返回安全动作和裁剪诊断”。

### 5.B 为什么需要这一组代码

这一组负责“逐时间步裁剪关节限位、关节增量和夹爪值”。它服务于本文件要解决的总问题：学习模型可能输出 NaN、越过机械限位或相邻动作跳变过大，直接执行会让仿真失稳且掩盖模型问题。 这一组的处理结果会参与：拒绝非有限值和错误 shape，逐步按关节限位、0.05 rad 步长与夹爪 0～1 范围裁剪。

### 5.C 本模块主要变量

- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `safe`：即将返回的安全动作副本。
- `current`：float32 格式的当前六关节角。
- `lower`：在机械限位内额外留出 margin 后的六关节安全下界。
- `upper`：在机械限位内额外留出 margin 后的六关节安全上界。
- `previous`：裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角。
- `joint_target`：当前动作时间步中，先按机械关节上下限裁剪后的六关节目标。
- `stepped`：再按相邻动作最大变化量裁剪后的最终六关节目标。

### 5.D 本模块首次阅读要认识的调用

- `source.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `np.clip(...)`：圆括号表示真正执行调用；把数值限制在给定上下界内。
- `np.count_nonzero(...)`：圆括号表示真正执行调用；NumPy 的 `count_nonzero` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0038】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lower`。右侧语法为：表达式 `RM65_LOWER_RAD + config.joint_limit_margin_rad` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `lower`，它在本项目中表示在机械限位内额外留出 margin 后的六关节安全下界；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RM65_LOWER_RAD + config.joint_limit_margin_rad`；`RM65_LOWER_RAD` 表示RM65 机械约束或项目常量；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值。
    lower = RM65_LOWER_RAD + config.joint_limit_margin_rad
# 【L0039】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `upper`。右侧语法为：表达式 `RM65_UPPER_RAD - config.joint_limit_margin_rad` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `upper`，它在本项目中表示在机械限位内额外留出 margin 后的六关节安全上界；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RM65_UPPER_RAD - config.joint_limit_margin_rad`；`RM65_UPPER_RAD` 表示RM65 机械约束或项目常量；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`joint_limit_margin_rad` 表示关节相关值。
    upper = RM65_UPPER_RAD - config.joint_limit_margin_rad
# 【L0040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe`。右侧语法为：`source` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `safe`，它在本项目中表示即将返回的安全动作副本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    safe = source.copy()
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_limit_clamps`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `joint_limit_clamps`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    joint_limit_clamps = 0
# 【L0042】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `step_clamps`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `step_clamps`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    step_clamps = 0
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `current`；第 2 个实参 `lower`；第 3 个实参 `upper`。
# 【项目含义】得到 `previous`，它在本项目中表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    previous = np.clip(current, lower, upper)
# 【L0044】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(len(safe))`，每次把当前元素放进 `index`；这会逐个处理“逐时间步裁剪关节限位、关节增量和夹爪值”所需的帧、episode、动作或实验 case。
    for index in range(len(safe)):
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_target`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe[index, :6]`；第 2 个实参 `lower`；第 3 个实参 `upper`；其中 `safe[index, :6]` 的方括号表示先从 `safe` 按键/索引 `index, :6` 取值。
# 【项目含义】得到 `joint_target`，它在本项目中表示当前动作时间步中，先按机械关节上下限裁剪后的六关节目标；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        joint_target = np.clip(safe[index, :6], lower, upper)
# 【L0046】语法拆解：表达式 `joint_limit_clamps += int(np.count_nonzero(joint_target != safe[index, :6]))` 使用运算符 `!=`, `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `joint_limit_clamps + int(np.count_nonzero(joint_target != safe[index, :6]))` 更新 `joint_limit_clamps` 原值；`joint_limit_clamps` 表示关节相关值，常用于累计步数、距离、损失或成功次数。
        joint_limit_clamps += int(np.count_nonzero(joint_target != safe[index, :6]))
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `step_lower`。右侧语法为：表达式 `previous - config.max_joint_step_rad` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `step_lower`，它在本项目中表示步、下界相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `previous - config.max_joint_step_rad`；`previous` 表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`max_joint_step_rad` 表示关节、步相关值。
        step_lower = previous - config.max_joint_step_rad
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `step_upper`。右侧语法为：表达式 `previous + config.max_joint_step_rad` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `step_upper`，它在本项目中表示步、上界相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `previous + config.max_joint_step_rad`；`previous` 表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`max_joint_step_rad` 表示关节、步相关值。
        step_upper = previous + config.max_joint_step_rad
# 【L0049】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stepped`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `joint_target`；第 2 个实参 `step_lower`；第 3 个实参 `step_upper`。
# 【项目含义】得到 `stepped`，它在本项目中表示再按相邻动作最大变化量裁剪后的最终六关节目标；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        stepped = np.clip(joint_target, step_lower, step_upper)
# 【L0050】语法拆解：表达式 `step_clamps += int(np.count_nonzero(stepped != joint_target))` 使用运算符 `!=`, `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `step_clamps + int(np.count_nonzero(stepped != joint_target))` 更新 `step_clamps` 原值；`step_clamps` 表示步相关值，常用于累计步数、距离、损失或成功次数。
        step_clamps += int(np.count_nonzero(stepped != joint_target))
# 【L0051】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe[index, :6]`。右侧语法为：`stepped` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `safe[index, :6]`（写入 `safe[index, :6]` 指定的字段）；右侧具体做的是：计算表达式 `stepped`；`stepped` 表示再按相邻动作最大变化量裁剪后的最终六关节目标。
        safe[index, :6] = stepped
# 【L0052】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe[index, 6]`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe[index, 6]`；第 2 个实参 `0.0`；第 3 个实参 `1.0`；其中 `safe[index, 6]` 的方括号表示先从 `safe` 按键/索引 `index, 6` 取值。
# 【项目含义】把右侧结果写进 `safe[index, 6]`（写入 `safe[index, 6]` 指定的字段）；右侧具体做的是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
        safe[index, 6] = np.clip(safe[index, 6], 0.0, 1.0)
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous`。右侧语法为：`stepped` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous`，它在本项目中表示裁剪下一步动作时所参考的上一关节目标；首步使用当前实际关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `stepped`；`stepped` 表示再按相邻动作最大变化量裁剪后的最终六关节目标。
        previous = stepped
# 【L0054】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“逐时间步裁剪关节限位、关节增量和夹爪值”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“逐时间步裁剪关节限位、关节增量和夹爪值”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：返回安全动作和裁剪诊断（源码第 55-68 行）

### 5.A 数据流位置

- 上游：模块 3“逐时间步裁剪关节限位、关节增量和夹爪值”。
- 本模块：返回安全动作和裁剪诊断。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“返回安全动作和裁剪诊断”。它服务于本文件要解决的总问题：学习模型可能输出 NaN、越过机械限位或相邻动作跳变过大，直接执行会让仿真失稳且掩盖模型问题。 这一组的处理结果会参与：拒绝非有限值和错误 shape，逐步按关节限位、0.05 rad 步长与夹爪 0～1 范围裁剪。

### 5.C 本模块主要变量

- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `safe`：即将返回的安全动作副本。
- `current`：float32 格式的当前六关节角。

### 5.D 本模块首次阅读要认识的调用

- `np.count_nonzero(...)`：圆括号表示真正执行调用；NumPy 的 `count_nonzero` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `np.max(...)`：圆括号表示真正执行调用；从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。
- `np.abs(...)`：圆括号表示真正执行调用；逐元素取绝对值。
- `np.diff(...)`：圆括号表示真正执行调用；计算相邻元素或相邻帧之差。
- `np.vstack(...)`：圆括号表示真正执行调用；NumPy 的 `vstack` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0055】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `diagnostics`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `diagnostics`，它在本项目中表示本功能块中的 `diagnostics` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    diagnostics = {
# 【L0056】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0057】语法拆解：这是字典键值对：`"input_shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `source.shape`。
# 【项目含义】定义字典/JSON 字段 `input_shape`，它表示“返回安全动作和裁剪诊断”中的 `input_shape` 数据；字段值来自 `list(source.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
        "input_shape": list(source.shape),
# 【L0058】语法拆解：这是字典键值对：`"all_finite"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `all_finite`，它表示“返回安全动作和裁剪诊断”中的 `all_finite` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_finite": True,
# 【L0059】语法拆解：这是字典键值对：`"joint_limit_margin_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`joint_limit_margin_rad`。
# 【项目含义】定义字典/JSON 字段 `joint_limit_margin_rad`，它表示“返回安全动作和裁剪诊断”中的 `joint_limit_margin_rad` 数据；字段值来自 `config.joint_limit_margin_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_limit_margin_rad": config.joint_limit_margin_rad,
# 【L0060】语法拆解：这是字典键值对：`"max_joint_step_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`config` 是起始对象；每个点号 `.` 依次读取属性/成员：`max_joint_step_rad`。
# 【项目含义】定义字典/JSON 字段 `max_joint_step_rad`，它表示“返回安全动作和裁剪诊断”中的 `max_joint_step_rad` 数据；字段值来自 `config.max_joint_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "max_joint_step_rad": config.max_joint_step_rad,
# 【L0061】语法拆解：这是字典键值对：`"joint_limit_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`joint_limit_clamps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `joint_limit_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `joint_limit_clamp_count` 数据；字段值来自 `joint_limit_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_limit_clamp_count": joint_limit_clamps,
# 【L0062】语法拆解：这是字典键值对：`"joint_step_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`step_clamps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `joint_step_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `joint_step_clamp_count` 数据；字段值来自 `step_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_step_clamp_count": step_clamps,
# 【L0063】语法拆解：这是字典键值对：`"gripper_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`int` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.count_nonzero(safe[:, 6] != source[:, 6])`。
# 【项目含义】定义字典/JSON 字段 `gripper_clamp_count`，它表示“返回安全动作和裁剪诊断”中的 `gripper_clamp_count` 数据；字段值来自 `int(np.count_nonzero(safe[:, 6] != source[:, 6]))`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_clamp_count": int(np.count_nonzero(safe[:, 6] != source[:, 6])),
# 【L0064】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `maximum_output_step_rad`，它表示“返回安全动作和裁剪诊断”中的 `maximum_output_step_rad` 数据；字段值来自 `float(`，因此保存/传递的是这个表达式当前计算出的结果。
        "maximum_output_step_rad": float(
# 【L0065】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `max` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0))`。
# 【项目含义】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
            np.max(np.abs(np.diff(np.vstack([current, safe[:, :6]]), axis=0)))
# 【L0066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
        ),
# 【L0067】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“返回安全动作和裁剪诊断”。
    }
# 【L0068】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`safe, diagnostics` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `safe, diagnostics` 交回调用者；这个值的含义是：计算表达式 `safe, diagnostics`；`safe` 表示即将返回的安全动作副本；`diagnostics` 表示本功能块中的 `diagnostics` 值。
    return safe, diagnostics
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“返回安全动作和裁剪诊断”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。