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

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Pure NumPy helpers for deriving RM65 grasp poses.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Pure NumPy helpers for deriving RM65 grasp poses."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0007】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0008】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0009】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `interpolate_rotation_matrix(参数在后续行继续)`；调用者把参数交给它完成“沿相对轴角在两个旋转矩阵之间插值”，后面的缩进代码是具体实现。
def interpolate_rotation_matrix(
# 【L0010】语法拆解：`start_rotation` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `start_rotation`，类型提示为 `np.ndarray`；在本项目中它表示旋转相关值。
    start_rotation: np.ndarray,
# 【L0011】语法拆解：`target_rotation` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target_rotation`，类型提示为 `np.ndarray`；在本项目中它表示目标、旋转相关值。
    target_rotation: np.ndarray,
# 【L0012】语法拆解：`fraction` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `fraction`，类型提示为 `float`；在本项目中它表示本功能块中的 `fraction` 值。
    fraction: float,
# 【L0013】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> np.ndarray:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“沿相对轴角在两个旋转矩阵之间插值”。
) -> np.ndarray:
# 【L0014】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Interpolate two rotation matrices along their relative axis-angle.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Interpolate two rotation matrices along their relative axis-angle."""
# 【L0015】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“沿相对轴角在两个旋转矩阵之间插值”中的逻辑段，让结构更容易看清。

# 【L0016】语法拆解：`if` 要求条件 `not 0.0 <= fraction <= 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= fraction <= 1.0` 是否成立；`fraction` 表示本功能块中的 `fraction` 值
    if not 0.0 <= fraction <= 1.0:
# 【L0017】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("rotation interpolation fraction must be between 0 and 1")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("rotation interpolation fraction must be between 0 and 1")` 并停止当前路径；说明当前输入违反“沿相对轴角在两个旋转矩阵之间插值”要求，不能继续进入仿真、训练或评测。
        raise ValueError("rotation interpolation fraction must be between 0 and 1")
# 【L0018】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `start`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `start_rotation`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `start`，它在本项目中表示本功能块中的 `start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `start_rotation, dtype=np.float64`（本功能块中的 `start_rotation, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    start = np.asarray(start_rotation, dtype=np.float64)
# 【L0019】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `target_rotation`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `target_rotation, dtype=np.float64`（目标相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    target = np.asarray(target_rotation, dtype=np.float64)
# 【L0020】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `relative`。右侧语法为：表达式 `target @ start.T` 使用运算符 `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `relative`，它在本项目中表示本功能块中的 `relative` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target @ start.T`；`target` 表示目标相关值；`start` 表示本功能块中的 `start` 值；`T` 表示本功能块中的 `T` 值。
    relative = target @ start.T
# 【L0021】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cosine`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(np.trace(relative) - 1.0) / 2.0`；第 2 个实参 `-1.0`；第 3 个实参 `1.0`。
# 【项目含义】得到 `cosine`，它在本项目中表示本功能块中的 `cosine` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    cosine = np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)
# 【L0022】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `angle`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.arccos(cosine)`。
# 【项目含义】得到 `angle`，它在本项目中表示本功能块中的 `angle` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(np.arccos(cosine))`；`arccos` 表示本功能块中的 `arccos` 值；`cosine` 表示本功能块中的 `cosine` 值。
    angle = float(np.arccos(cosine))
# 【L0023】语法拆解：`if` 要求条件 `angle < 1e-10` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `angle < 1e-10` 是否成立；`angle` 表示本功能块中的 `angle` 值
    if angle < 1e-10:
# 【L0024】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`start` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】结束当前函数并把 `start.copy()` 交回调用者；这个值的含义是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        return start.copy()
# 【L0025】语法拆解：`if` 要求条件 `abs(np.sin(angle)) < 1e-8` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(np.sin(angle)) < 1e-8` 是否成立；`abs` 表示本功能块中的 `abs` 值；`sin` 表示本功能块中的 `sin` 值；`angle` 表示本功能块中的 `angle` 值
    if abs(np.sin(angle)) < 1e-8:
# 【L0026】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("rotation interpolation is ambiguous at 180 degrees")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("rotation interpolation is ambiguous at 180 degrees")` 并停止当前路径；说明当前输入违反“沿相对轴角在两个旋转矩阵之间插值”要求，不能继续进入仿真、训练或评测。
        raise ValueError("rotation interpolation is ambiguous at 180 degrees")
# 【L0027】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `axis`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `axis`，它在本项目中表示本功能块中的 `axis` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    axis = np.array(
# 【L0028】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“沿相对轴角在两个旋转矩阵之间插值”。
        [
# 【L0029】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`relative[2, 1] - relative[1, 2]` 使用方括号索引；先计算 `2, 1] - relative[1, 2`，再从 `relative` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `relative[2, 1] - relative[1, 2]`；`relative` 表示本功能块中的 `relative` 值，它参与“沿相对轴角在两个旋转矩阵之间插值”。
            relative[2, 1] - relative[1, 2],
# 【L0030】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`relative[0, 2] - relative[2, 0]` 使用方括号索引；先计算 `0, 2] - relative[2, 0`，再从 `relative` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `relative[0, 2] - relative[2, 0]`；`relative` 表示本功能块中的 `relative` 值，它参与“沿相对轴角在两个旋转矩阵之间插值”。
            relative[0, 2] - relative[2, 0],
# 【L0031】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`relative[1, 0] - relative[0, 1]` 使用方括号索引；先计算 `1, 0] - relative[0, 1`，再从 `relative` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `relative[1, 0] - relative[0, 1]`；`relative` 表示本功能块中的 `relative` 值，它参与“沿相对轴角在两个旋转矩阵之间插值”。
            relative[1, 0] - relative[0, 1],
# 【L0032】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
        ],
# 【L0033】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“沿相对轴角在两个旋转矩阵之间插值”。
        dtype=np.float64,
# 【L0034】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `) / (2.0 * np` 调用 `sin(angle))`：调用 `) / (2.0 * np` 提供的 `sin` 操作。本行产生的修改/返回值服务于“沿相对轴角在两个旋转矩阵之间插值”。
    ) / (2.0 * np.sin(angle))
# 【L0035】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `skew`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `skew`，它在本项目中表示本功能块中的 `skew` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    skew = np.array(
# 【L0036】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“沿相对轴角在两个旋转矩阵之间插值”。
        [
# 【L0037】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, -axis[2], axis[1]],`；`axis` 表示本功能块中的 `axis` 值，共同完成“沿相对轴角在两个旋转矩阵之间插值”。
            [0.0, -axis[2], axis[1]],
# 【L0038】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[axis[2], 0.0, -axis[0]],`；`axis` 表示本功能块中的 `axis` 值，共同完成“沿相对轴角在两个旋转矩阵之间插值”。
            [axis[2], 0.0, -axis[0]],
# 【L0039】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[-axis[1], axis[0], 0.0],`；`axis` 表示本功能块中的 `axis` 值，共同完成“沿相对轴角在两个旋转矩阵之间插值”。
            [-axis[1], axis[0], 0.0],
# 【L0040】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
        ],
# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“沿相对轴角在两个旋转矩阵之间插值”。
        dtype=np.float64,
# 【L0042】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
    )
# 【L0043】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `partial_angle`。右侧语法为：表达式 `fraction * angle` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `partial_angle`，它在本项目中表示本功能块中的 `partial_angle` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `fraction * angle`；`fraction` 表示本功能块中的 `fraction` 值；`angle` 表示本功能块中的 `angle` 值。
    partial_angle = fraction * angle
# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `partial`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `partial`，它在本项目中表示本功能块中的 `partial` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    partial = (
# 【L0045】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `eye` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `3`。
# 【项目含义】对 `np` 调用 `eye(3)`：调用 `np` 提供的 `eye` 操作。本行产生的修改/返回值服务于“沿相对轴角在两个旋转矩阵之间插值”。
        np.eye(3)
# 【L0046】语法拆解：表达式 `+ np.sin(partial_angle) * skew` 使用运算符 `+`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `+ np.sin(partial_angle) * skew` 接到上一行未结束的数学公式；`sin` 表示本功能块中的 `sin` 值；`partial_angle` 表示本功能块中的 `partial_angle` 值；`skew` 表示本功能块中的 `skew` 值，整条公式用于“沿相对轴角在两个旋转矩阵之间插值”。
        + np.sin(partial_angle) * skew
# 【L0047】语法拆解：表达式 `+ (1.0 - np.cos(partial_angle)) * (skew @ skew)` 使用运算符 `+`, `-`, `*`, `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】对 `+ (1.0 - np` 调用 `cos(partial_angle)) * (skew @ skew)`：调用 `+ (1.0 - np` 提供的 `cos` 操作。本行产生的修改/返回值服务于“沿相对轴角在两个旋转矩阵之间插值”。
        + (1.0 - np.cos(partial_angle)) * (skew @ skew)
# 【L0048】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“沿相对轴角在两个旋转矩阵之间插值”。
    )
# 【L0049】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：表达式 `partial @ start` 使用运算符 `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】结束当前函数并把 `partial @ start` 交回调用者；这个值的含义是：计算表达式 `partial @ start`；`partial` 表示本功能块中的 `partial` 值；`start` 表示本功能块中的 `start` 值。
    return partial @ start
# 【L0050】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0051】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0052】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `compute_top_down_link_pose(参数在后续行继续)`；调用者把参数交给它完成“顶部抓取函数接口、输入转换和 shape 校验”，后面的缩进代码是具体实现。
def compute_top_down_link_pose(
# 【L0053】语法拆解：`reference_link_position` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `reference_link_position`，类型提示为 `np.ndarray`；在本项目中它表示机器人连杆、位置相关值。
    reference_link_position: np.ndarray,
# 【L0054】语法拆解：`reference_link_rotation` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `reference_link_rotation`，类型提示为 `np.ndarray`；在本项目中它表示机器人连杆、旋转相关值。
    reference_link_rotation: np.ndarray,
# 【L0055】语法拆解：`block_position` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `block_position`，类型提示为 `np.ndarray`；在本项目中它表示位置相关值。
    block_position: np.ndarray,
# 【L0056】语法拆解：`yaw_rad` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `yaw_rad`，类型提示为 `float`；在本项目中它表示本功能块中的 `yaw_rad` 值。
    yaw_rad: float,
# 【L0057】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `tilt_rad: float`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `tilt_rad`，它在本项目中表示本功能块中的 `tilt_rad` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
    tilt_rad: float = 0.0,
# 【L0058】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `blend_fraction: float`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `blend_fraction`，它在本项目中表示本功能块中的 `blend_fraction` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `1.0` 的结果保存下来，供当前功能块后续使用。
    blend_fraction: float = 1.0,
# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `reference_closing_axis_world: np.ndarray | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `reference_closing_axis_world`，它在本项目中表示本功能块中的 `reference_closing_axis_world` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    reference_closing_axis_world: np.ndarray | None = None,
# 【L0060】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> tuple[np.ndarray, np.ndarray, np.ndarray]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“顶部抓取函数接口、输入转换和 shape 校验”。
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
# 【L0061】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Rotate a calibrated link-to-block transform into an above-table grasp.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Rotate a calibrated link-to-block transform into an above-table grasp.
# 【L0062】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“顶部抓取函数接口、输入转换和 shape 校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0063】语法拆解：`The reference pose already aligns the gripper pads with the block. This` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `The reference pose already aligns the gripper pads with the block. This`；这段文字在解释“顶部抓取函数接口、输入转换和 shape 校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    The reference pose already aligns the gripper pads with the block. This
# 【L0064】语法拆解：表达式 `function preserves that local link-to-block vector while mapping it to` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `function preserves that local link-to-block vector while mapping it to`；这段文字在解释“顶部抓取函数接口、输入转换和 shape 校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    function preserves that local link-to-block vector while mapping it to
# 【L0065】语法拆解：表达式 `world -z. The gripper closing axis remains horizontal and follows yaw.` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `world -z. The gripper closing axis remains horizontal and follows yaw.`；这段文字在解释“顶部抓取函数接口、输入转换和 shape 校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    world -z. The gripper closing axis remains horizontal and follows yaw.
# 【L0066】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“顶部抓取函数接口、输入转换和 shape 校验”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0067】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“顶部抓取函数接口、输入转换和 shape 校验”中的逻辑段，让结构更容易看清。

# 【L0068】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `link_position`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `reference_link_position`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `link_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `reference_link_position, dtype=np.float64`（机器人连杆相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    link_position = np.asarray(reference_link_position, dtype=np.float64)
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `link_rotation`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `reference_link_rotation`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `link_rotation`，它在本项目中表示机器人连杆、旋转相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `reference_link_rotation, dtype=np.float64`（机器人连杆相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    link_rotation = np.asarray(reference_link_rotation, dtype=np.float64)
# 【L0070】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `block`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `block_position`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `block`，它在本项目中表示本功能块中的 `block` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `block_position, dtype=np.float64`（本功能块中的 `block_position, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    block = np.asarray(block_position, dtype=np.float64)
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closing_world`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closing_world`，它在本项目中表示本功能块中的 `closing_world` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    closing_world = (
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `np.array([0.0, 1.0, 0.0], dtype`。右侧语法为：`np.float64)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `np.array([0.0, 1.0, 0.0], dtype=np.float64)`。`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值。
        np.array([0.0, 1.0, 0.0], dtype=np.float64)
# 【L0073】语法拆解：`if` 要求条件 `reference_closing_axis_world is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `reference_closing_axis_world is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if reference_closing_axis_world is None
# 【L0074】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `else np.asarray(reference_closing_axis_world, dtype=np.float64)`。`asarray` 表示本功能块中的 `asarray` 值；`reference_closing_axis_world` 表示本功能块中的 `reference_closing_axis_world` 值。
        else np.asarray(reference_closing_axis_world, dtype=np.float64)
# 【L0075】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“顶部抓取函数接口、输入转换和 shape 校验”。
    )
# 【L0076】语法拆解：`if` 要求条件 `link_position.shape != (3,) or block.shape != (3,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `link_position.shape` 是否不等于要求的 `(3,) or block.shape != (3,)`；若不等，数据维度合同已被破坏，进入错误处理
    if link_position.shape != (3,) or block.shape != (3,):
# 【L0077】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("link and block positions must each have shape (3,)")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("link and block positions must each have shape (3,)")` 并停止当前路径；说明当前输入违反“顶部抓取函数接口、输入转换和 shape 校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("link and block positions must each have shape (3,)")
# 【L0078】语法拆解：`if` 要求条件 `link_rotation.shape != (3, 3)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `link_rotation.shape` 是否不等于要求的 `(3, 3)`；若不等，数据维度合同已被破坏，进入错误处理
    if link_rotation.shape != (3, 3):
# 【L0079】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("link rotation must have shape (3, 3)")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("link rotation must have shape (3, 3)")` 并停止当前路径；说明当前输入违反“顶部抓取函数接口、输入转换和 shape 校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("link rotation must have shape (3, 3)")
# 【L0080】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“顶部抓取函数接口、输入转换和 shape 校验”中的逻辑段，让结构更容易看清。

# 【L0081】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `block_from_link_local`。右侧语法为：表达式 `link_rotation.T @ (block - link_position)` 使用运算符 `-`, `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `block_from_link_local`，它在本项目中表示机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `link_rotation.T @ (block - link_position)`；`link_rotation` 表示机器人连杆、旋转相关值；`T` 表示本功能块中的 `T` 值；`block` 表示本功能块中的 `block` 值。
    block_from_link_local = link_rotation.T @ (block - link_position)
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_forward`。右侧语法为：表达式 `block_from_link_local / np.linalg.norm(block_from_link_local)` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `local_forward`，它在本项目中表示本功能块中的 `local_forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    local_forward = block_from_link_local / np.linalg.norm(block_from_link_local)
# 【L0083】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_closing`。右侧语法为：表达式 `link_rotation.T @ closing_world` 使用运算符 `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `local_closing`，它在本项目中表示本功能块中的 `local_closing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `link_rotation.T @ closing_world`；`link_rotation` 表示机器人连杆、旋转相关值；`T` 表示本功能块中的 `T` 值；`closing_world` 表示本功能块中的 `closing_world` 值。
    local_closing = link_rotation.T @ closing_world
# 【L0084】语法拆解：表达式 `local_closing -= np.dot(local_closing, local_forward) * local_forward` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `local_closing - np.dot(local_closing, local_forward) * local_forward` 更新 `local_closing` 原值；`local_closing` 表示本功能块中的 `local_closing` 值，常用于累计步数、距离、损失或成功次数。
    local_closing -= np.dot(local_closing, local_forward) * local_forward
# 【L0085】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_closing_norm`。右侧语法为：`np.linalg` 是模块/对象，点号 `.` 从中取出 `norm` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `local_closing`。
# 【项目含义】得到 `local_closing_norm`，它在本项目中表示本功能块中的 `local_closing_norm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    local_closing_norm = np.linalg.norm(local_closing)
# 【L0086】语法拆解：`if` 要求条件 `local_closing_norm < 1e-8` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `local_closing_norm < 1e-8` 是否成立；`local_closing_norm` 表示本功能块中的 `local_closing_norm` 值
    if local_closing_norm < 1e-8:
# 【L0087】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("reference closing axis cannot be parallel to the block direction")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("reference closing axis cannot be parallel to the block direction")` 并停止当前路径；说明当前输入违反“从参考姿态求 link→block、闭合轴和切向轴局部基”要求，不能继续进入仿真、训练或评测。
        raise ValueError("reference closing axis cannot be parallel to the block direction")
# 【L0088】语法拆解：表达式 `local_closing /= local_closing_norm` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `local_closing / local_closing_norm` 更新 `local_closing` 原值；`local_closing` 表示本功能块中的 `local_closing` 值，常用于累计步数、距离、损失或成功次数。
    local_closing /= local_closing_norm
# 【L0089】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_tangent`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `cross` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `local_forward`；第 2 个实参 `local_closing`。
# 【项目含义】得到 `local_tangent`，它在本项目中表示本功能块中的 `local_tangent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.cross(local_forward, local_closing)`；`cross` 表示本功能块中的 `cross` 值；`local_forward` 表示本功能块中的 `local_forward` 值；`local_closing` 表示本功能块中的 `local_closing` 值。
    local_tangent = np.cross(local_forward, local_closing)
# 【L0090】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从参考姿态求 link→block、闭合轴和切向轴局部基”中的逻辑段，让结构更容易看清。

# 【L0091】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_closing`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[-np.sin(yaw_rad), np.cos(yaw_rad), 0.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `world_closing`，它在本项目中表示本功能块中的 `world_closing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`sin` 表示本功能块中的 `sin` 值；`yaw_rad` 表示本功能块中的 `yaw_rad` 值。
    world_closing = np.array([-np.sin(yaw_rad), np.cos(yaw_rad), 0.0], dtype=np.float64)
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `horizontal_forward`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[-np.cos(yaw_rad), -np.sin(yaw_rad), 0.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `horizontal_forward`，它在本项目中表示本功能块中的 `horizontal_forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-np.cos(yaw_rad), -np.sin(yaw_rad), 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`cos` 表示本功能块中的 `cos` 值；`yaw_rad` 表示本功能块中的 `yaw_rad` 值。
    horizontal_forward = np.array([-np.cos(yaw_rad), -np.sin(yaw_rad), 0.0], dtype=np.float64)
# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_forward`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `world_forward`，它在本项目中表示本功能块中的 `world_forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    world_forward = (
# 【L0094】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `np.cos(tilt_rad) * np.array([0.0, 0.0, -1.0], dtype`。右侧语法为：`np.float64)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `np.cos(tilt_rad) * np.array([0.0, 0.0, -1.0], dtype=np.float64)`。`cos` 表示本功能块中的 `cos` 值；`tilt_rad` 表示本功能块中的 `tilt_rad` 值。
        np.cos(tilt_rad) * np.array([0.0, 0.0, -1.0], dtype=np.float64)
# 【L0095】语法拆解：表达式 `+ np.sin(tilt_rad) * horizontal_forward` 使用运算符 `+`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `+ np.sin(tilt_rad) * horizontal_forward` 接到上一行未结束的数学公式；`sin` 表示本功能块中的 `sin` 值；`tilt_rad` 表示本功能块中的 `tilt_rad` 值；`horizontal_forward` 表示本功能块中的 `horizontal_forward` 值，整条公式用于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
        + np.sin(tilt_rad) * horizontal_forward
# 【L0096】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    )
# 【L0097】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_tangent`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `cross` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `world_forward`；第 2 个实参 `world_closing`。
# 【项目含义】得到 `world_tangent`，它在本项目中表示本功能块中的 `world_tangent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.cross(world_forward, world_closing)`；`cross` 表示本功能块中的 `cross` 值；`world_forward` 表示本功能块中的 `world_forward` 值；`world_closing` 表示本功能块中的 `world_closing` 值。
    world_tangent = np.cross(world_forward, world_closing)
# 【L0098】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local_basis`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `column_stack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(local_closing, local_tangent, local_forward)`。
# 【项目含义】得到 `local_basis`，它在本项目中表示本功能块中的 `local_basis` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.column_stack((local_closing, local_tangent, local_forward))`；`column_stack` 表示本功能块中的 `column_stack` 值；`local_closing` 表示本功能块中的 `local_closing` 值；`local_tangent` 表示本功能块中的 `local_tangent` 值。
    local_basis = np.column_stack((local_closing, local_tangent, local_forward))
# 【L0099】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_basis`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `column_stack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(world_closing, world_tangent, world_forward)`。
# 【项目含义】得到 `world_basis`，它在本项目中表示本功能块中的 `world_basis` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.column_stack((world_closing, world_tangent, world_forward))`；`column_stack` 表示本功能块中的 `column_stack` 值；`world_closing` 表示本功能块中的 `world_closing` 值；`world_tangent` 表示本功能块中的 `world_tangent` 值。
    world_basis = np.column_stack((world_closing, world_tangent, world_forward))
# 【L0100】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_rotation`。右侧语法为：表达式 `world_basis @ local_basis.T` 使用运算符 `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `target_rotation`，它在本项目中表示目标、旋转相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `world_basis @ local_basis.T`；`world_basis` 表示本功能块中的 `world_basis` 值；`local_basis` 表示本功能块中的 `local_basis` 值；`T` 表示本功能块中的 `T` 值。
    target_rotation = world_basis @ local_basis.T
# 【L0101】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `blended_rotation`。右侧语法为：`interpolate_rotation_matrix(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `blended_rotation`，它在本项目中表示旋转相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `interpolate_rotation_matrix(`；`interpolate_rotation_matrix` 表示旋转相关值。
    blended_rotation = interpolate_rotation_matrix(
# 【L0102】语法拆解：`link_rotation, target_rotation, blend_fraction` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `link_rotation, target_rotation, blend_fraction` 接入当前完整语句；`link_rotation` 表示机器人连杆、旋转相关值；`target_rotation` 表示目标、旋转相关值；`blend_fraction` 表示本功能块中的 `blend_fraction` 值。在“构造世界顶部抓取基、计算目标旋转和 link 位置”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        link_rotation, target_rotation, blend_fraction
# 【L0103】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“构造世界顶部抓取基、计算目标旋转和 link 位置”。
    )
# 【L0104】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `blended_link_position`。右侧语法为：表达式 `block - blended_rotation @ block_from_link_local` 使用运算符 `-`, `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `blended_link_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `block - blended_rotation @ block_from_link_local`；`block` 表示本功能块中的 `block` 值；`blended_rotation` 表示旋转相关值；`block_from_link_local` 表示机器人连杆相关值。
    blended_link_position = block - blended_rotation @ block_from_link_local
# 【L0105】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`blended_link_position, blended_rotation, block_from_link_local` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `blended_link_position, blended_rotation, block_from_link_local` 交回调用者；这个值的含义是：计算表达式 `blended_link_position, blended_rotation, block_from_link_local`；`blended_link_position` 表示机器人连杆、位置相关值；`blended_rotation` 表示旋转相关值；`block_from_link_local` 表示机器人连杆相关值。
    return blended_link_position, blended_rotation, block_from_link_local
```
