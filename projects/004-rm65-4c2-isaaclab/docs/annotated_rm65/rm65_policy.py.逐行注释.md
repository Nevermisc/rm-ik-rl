# `rm65_policy.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/rm65_policy.py`
- 快照 SHA-256：`d24c658d7f7b35f84271b80e2bcff6d3548c9a1f9c1e3c24bc439a2095bf4783`
- 总行数：73
- 程序作用：RM65 与 OpenPI 之间最核心的接口翻译器：把自定义键、两张图和 6+1 状态改成 π0.5 通用字段。
- 推荐读法：这是最应该先精读的小文件；它定义模型究竟看见什么，以及模型输出的七维是什么。

## 功能块地图

- 第 1-12 行：依赖
- 第 14-22 行：把输入图像统一成 H×W×3 的 uint8 RGB
- 第 25-64 行：RM65Inputs：仓库字段→π0.5 字段
- 第 67-73 行：RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标

## 函数/类索引

- `_parse_image()`：第 14-22 行
- `class RM65Inputs`：第 26-64 行
  - `RM65Inputs.__call__()`：第 31-64 行
- `class RM65Outputs`：第 68-73 行
  - `RM65Outputs.__call__()`：第 71-73 行

## 逐行学习副本

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```python
# 【L0001】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state."""
# 【L0002】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0003】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0005】语法拆解：`import` 加载模块；`dataclasses` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0007】语法拆解：`import` 加载模块；`einops` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `einops` 引入 `einops`。在这份程序里，`einops` 用于用可读模式重排数组维度；后续出现这些名字时调用的是这里的外部能力。
import einops
# 【L0008】语法拆解：`import` 加载模块；`numpy as np` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0009】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0010】语法拆解：`from openpi` 指定来源模块；`import transforms` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi import transforms
# 【L0011】语法拆解：`from openpi.models` 指定来源模块；`import model as _model` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `model as _model`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import model as _model
# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0014】语法拆解：`def` 定义函数 `_parse_image`；第一对圆括号列出形参，逗号负责分隔：`image: np.ndarray` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义图像标准化函数。RM65 数据可能来自训练集或 Isaac 相机，这个函数保证两条路径得到同一种图像布局。
def _parse_image(image: np.ndarray) -> np.ndarray:
# 【L0015】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image`。
# 【项目含义】把传入图像统一包装为 NumPy ndarray。若本来就是 ndarray 通常不复制；若是列表或其他兼容对象则转换，之后才能稳定使用 dtype、shape 和切片。
    image = np.asarray(image)
# 【L0016】语法拆解：`if` 要求条件 `np.issubdtype(image.dtype, np.floating)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查图像元素类型是不是浮点数。浮点图常用 0～1，而 π0.5 的图像 transform 期望 uint8 0～255。
    if np.issubdtype(image.dtype, np.floating):
# 【L0017】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `255 * image`；第 2 个实参 `0`；第 3 个实参 `255).astype(np.uint8`。
# 【项目含义】把 0～1 浮点图乘 255，超出范围的值裁到 0～255，再转成 uint8；结果成为标准八位 RGB 像素。
        image = np.clip(255 * image, 0, 255).astype(np.uint8)
# 【L0018】语法拆解：`if` 要求条件 `image.shape[0] == 3` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】若第一维长度为 3，就把输入视为通道优先的 C×H×W 图像；这常见于 PyTorch 数据。
    if image.shape[0] == 3:
# 【L0019】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image`。右侧语法为：`einops` 是模块/对象，点号 `.` 从中取出 `rearrange` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image`；第 2 个实参 `"c h w -> h w c"`。
# 【项目含义】把通道优先 C×H×W 重排为图像库/OpenPI 使用的 H×W×C；这里 C 必须是 RGB 三通道。
        image = einops.rearrange(image, "c h w -> h w c")
# 【L0020】语法拆解：`if` 要求条件 `image.ndim != 3 or image.shape[-1] != 3` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】确认最终图像恰好是三维且最后一维为 3。它拒绝灰度图、RGBA 图和维度颠倒的数组。
    if image.ndim != 3 or image.shape[-1] != 3:
# 【L0021】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected an RGB image, got {image.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】图像结构不满足 RGB 合同时立即报错，并把实际 shape 写进错误，避免错误图像静默进入训练或推理。
        raise ValueError(f"expected an RGB image, got {image.shape}")
# 【L0022】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`image` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】返回格式统一后的 H×W×3 RGB ndarray，供 RM65Inputs 填入 π0.5 图像槽位。
    return image
# 【L0023】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】把 RM65Inputs 声明为不可变数据类；实例创建后 model_type 不会被意外修改。
@dataclasses.dataclass(frozen=True)
# 【L0026】语法拆解：`class` 定义类 `RM65Inputs`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 RM65 输入 transform，并继承 OpenPI 的 DataTransformFn 接口，因此训练和推理框架都能调用它。
class RM65Inputs(transforms.DataTransformFn):
# 【L0027】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Convert repository-level RM65 fields to the generic pi0.5 model fields.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Convert repository-level RM65 fields to the generic pi0.5 model fields."""
# 【L0028】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0029】语法拆解：`model_type` 是字段名；冒号 `:` 在这里表示类型标注；`_model` 是导入模块的别名；点号 `.` 表示从模块中取出 `ModelType`；这一行没有等号，所以还没有赋具体值。因为外层类用了 `@dataclass`，Python 会把它自动变成构造参数。
# 【项目含义】保存当前使用的模型类型。后面只接受 PI0/PI05，因为不同模型可能要求不同图像键。
    model_type: _model.ModelType
# 【L0030】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0031】语法拆解：`def` 表示定义函数；`__call__` 是 Python 约定的特殊方法名，使 `对象(data)` 等价于 `对象.__call__(data)`；第一对圆括号放形参，`self` 指当前 RM65Inputs 对象，逗号分隔下一个参数；`data: dict` 中冒号是类型标注，表示 data 应是字典；`-> dict` 是返回值类型提示；末尾冒号表示下一行开始进入函数体，所以后续代码必须缩进。
# 【项目含义】当 OpenPI 处理一条训练样本或一次推理请求时调用此方法；输入 data 是仓库层字段字典，返回 π0.5 通用字段字典。
    def __call__(self, data: dict) -> dict:
# 【L0032】语法拆解：先读最里面：`"observation/joint_position"` 是字符串键；`data[...]` 的方括号表示按这个键从字典取值。再向外读：`np` 是 NumPy 的简称，点号取出其中的 `asarray` 函数，圆括号把刚取出的数据作为实参传入。最后，等号 `=` 把函数返回的 ndarray 绑定到左边变量 `joints`。整行求值顺序是：字典取值 → 转成数组 → 保存变量。
# 【项目含义】从 data 读取 `observation/joint_position`，也就是当前六个 RM65 关节角，并统一为 NumPy 数组；之后用 shape 验证它确实对应六轴。
        joints = np.asarray(data["observation/joint_position"])
# 【L0033】语法拆解：求值顺序与上一行相同：字符串是字典键，方括号从 `data` 取夹爪字段，`np.asarray(...)` 的圆括号调用 NumPy 函数，等号把结果保存为 `gripper`。这里的内外两层括号分别负责“字典索引”和“函数调用”。
# 【项目含义】从 data 读取归一化 4C2 夹爪位置并转为 NumPy 数组；它应该只包含一个值，0 张开、1 闭合。
        gripper = np.asarray(data["observation/gripper_position"])
# 【L0034】语法拆解：`if` 开始条件判断；`joints.shape` 用点号读取数组形状；`!=` 表示“不等于”；`(6,)` 是只有一个元素的元组，末尾逗号用于区分单元素元组和普通括号；行末冒号打开条件为真时执行的缩进块。
# 【项目含义】检查关节数组是不是一维六元素 `(6,)`；这同时保护关节数量和轴顺序合同。
        if joints.shape != (6,):
# 【L0035】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected six RM65 joints, got {joints.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】如果不是六轴形状就停止，并报告实际 shape；不能靠截断或补零把 Franka 七轴动作冒充 RM65 动作。
            raise ValueError(f"expected six RM65 joints, got {joints.shape}")
# 【L0036】语法拆解：`if` 要求条件 `gripper.ndim == 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】兼容调用方传入 Python 浮点或零维 ndarray 的情况；零维还不能与六关节数组直接拼接。
        if gripper.ndim == 0:
# 【L0037】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper`。右侧语法为：`gripper[np.newaxis]` 使用方括号索引；先计算 `np.newaxis`，再从 `gripper` 取对应字典字段或数组元素。
# 【项目含义】用 `np.newaxis` 增加一个维度，把标量形状 `()` 变成单元素向量 `(1,)`。
            gripper = gripper[np.newaxis]
# 【L0038】语法拆解：`if` 要求条件 `gripper.shape != (1,)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】确认夹爪最终形状严格为 `(1,)`，防止把多个 4C2 follower joint 当成多个策略自由度。
        if gripper.shape != (1,):
# 【L0039】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected one gripper value, got {gripper.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】夹爪结构错误时立即报错，并显示实际 shape。
            raise ValueError(f"expected one gripper value, got {gripper.shape}")
# 【L0040】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0041】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `base_image`。右侧语法为：`_parse_image` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `data["observation/external_image"]`；其中 `data["observation/external_image"]` 的方括号表示先从 `data` 按键/索引 `"observation/external_image"` 取值。
# 【项目含义】读取外部相机图像并通过 `_parse_image` 统一为 H×W×3、uint8 RGB。
        base_image = _parse_image(data["observation/external_image"])
# 【L0042】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_image`。右侧语法为：`_parse_image` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `data["observation/wrist_image"]`；其中 `data["observation/wrist_image"]` 的方括号表示先从 `data` 按键/索引 `"observation/wrist_image"` 取值。
# 【项目含义】读取腕部相机图像并执行同样的布局和像素类型标准化。
        wrist_image = _parse_image(data["observation/wrist_image"])
# 【L0043】语法拆解：`match self.model_type:` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】根据 OpenPI 模型类型选择它所认识的图像槽位名称。
        match self.model_type:
# 【L0044】语法拆解：`case _model.ModelType.PI0 | _model.ModelType.PI05:` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】PI0 和 PI0.5 在本项目中共用三个命名图像槽位，因此进入同一分支。
            case _model.ModelType.PI0 | _model.ModelType.PI05:
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `names`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】依次声明外部、左腕部、右腕部三个 π0.5 图像键；顺序必须与 images 和 image_masks 完全一致。
                names = ("base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb")
# 【L0046】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `images`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】把真实外部图、真实腕部图和一张同尺寸零图组成三元组；零图只是填满模型的第三个固定槽位。
                images = (base_image, wrist_image, np.zeros_like(base_image))
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image_masks`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】前两个 mask 为 true，告诉模型这两张是真实观测；第三个为 false，因此零图不会被当成第二台腕部相机。
                image_masks = (np.True_, np.True_, np.False_)
# 【L0048】语法拆解：`case _:` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】捕获 PI0/PI05 之外的模型类型。
            case _:
# 【L0049】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"unsupported model type for RM65: {self.model_type}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】遇到没有定义 RM65 图像布局的模型时拒绝继续，防止字段悄悄错位。
                raise ValueError(f"unsupported model type for RM65: {self.model_type}")
# 【L0050】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0051】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始构造 OpenPI/π0.5 真正接收的通用输入字典。
        result = {
# 【L0052】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】把六关节向量 `(6,)` 和夹爪向量 `(1,)` 首尾拼成七维 `state`；模型据此知道当前 RM65+4C2 状态。
            "state": np.concatenate([joints, gripper]),
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `"image": dict(zip(names, images, strict`。右侧语法为：`True))` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】用 `zip` 将三个槽位名与三张图一一配对并转成字典；`strict=True` 会在数量不一致时报错。
            "image": dict(zip(names, images, strict=True)),
# 【L0054】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `"image_mask": dict(zip(names, image_masks, strict`。右侧语法为：`True))` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】同样把槽位名与三个布尔 mask 配对，明确哪些图像有效。
            "image_mask": dict(zip(names, image_masks, strict=True)),
# 【L0055】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“RM65Inputs：仓库字段→π0.5 字段”。
        }
# 【L0056】语法拆解：`if` 要求条件 `"actions" in data` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】训练样本包含教师动作，而在线推理请求通常不包含；只有存在 actions 时才处理监督标签。
        if "actions" in data:
# 【L0057】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actions`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `data["actions"]`；其中 `data["actions"]` 的方括号表示先从 `data` 按键/索引 `"actions"` 取值。
# 【项目含义】从 data 取出当前训练样本的未来 RM65 动作序列。每步含六个绝对关节目标和一个归一化夹爪目标；`np.asarray` 将列表或其他数组对象统一成 ndarray，便于检查维度并交给后续 delta-action/训练 transform。
            actions = np.asarray(data["actions"])
# 【L0058】语法拆解：`if` 要求条件 `actions.shape[-1] != 7` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查动作最后一维是否为 7。前面的维度可以是单步或时间 horizon，但每步语义必须固定为 6+1。
            if actions.shape[-1] != 7:
# 【L0059】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError(f"expected seven RM65 action values, got {actions.shape}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】动作不是七维就报错；这会捕获误用 Franka `(T,8)` 标签或缺少夹爪列的情况。
                raise ValueError(f"expected seven RM65 action values, got {actions.shape}")
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result["actions"]`。右侧语法为：`actions` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把验证过的动作序列加入通用结果；训练时它随后会经过 DeltaActions 和归一化，推理请求没有这一键。
            result["actions"] = actions
# 【L0061】语法拆解：`if` 要求条件 `"prompt" in data` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】语言指令是可选字段；存在时才交给 π0.5 的 tokenizer。
        if "prompt" in data:
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prompt`。右侧语法为：`data["prompt"]` 使用方括号索引；先计算 `"prompt"`，再从 `data` 取对应字典字段或数组元素。
# 【项目含义】从 data 读取 prompt；它描述本帧所属任务，例如抓起方块并放到目标。
            prompt = data["prompt"]
# 【L0063】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `result["prompt"]`。右侧语法为：表达式 `prompt.decode("utf-8") if isinstance(prompt, bytes) else prompt` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】若数据加载器给出 bytes 就按 UTF-8 解码，否则保留原字符串，保证 tokenizer 最终收到 str。
            result["prompt"] = prompt.decode("utf-8") if isinstance(prompt, bytes) else prompt
# 【L0064】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`result` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】返回已经转换好的 state、image、image_mask，以及可选 actions/prompt，进入 OpenPI 后续归一化和模型处理。
        return result
# 【L0065】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0066】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0067】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】把输出 transform 声明为不可变数据类；它本身没有需要配置的字段。
@dataclasses.dataclass(frozen=True)
# 【L0068】语法拆解：`class` 定义类 `RM65Outputs`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 π0.5 输出到 RM65 动作合同的最后一道 transform。
class RM65Outputs(transforms.DataTransformFn):
# 【L0069】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Expose six absolute joint targets and one normalized gripper target.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Expose six absolute joint targets and one normalized gripper target."""
# 【L0070】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”中的逻辑段，让结构更容易看清。

# 【L0071】语法拆解：`def` 定义函数 `__call__`；第一对圆括号列出形参，逗号负责分隔：`self` 指调用该方法的当前对象；`data: dict` 用冒号给参数加类型提示；`-> dict` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】OpenPI 在反归一化和 absolute-action 恢复之后调用此方法。
    def __call__(self, data: dict) -> dict:
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actions`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `data["actions"]`；其中 `data["actions"]` 的方括号表示先从 `data` 按键/索引 `"actions"` 取值。
# 【项目含义】从 OpenPI 输出字典取出动作块并统一为 ndarray；形状通常是 `(10, action_dim)`。
        actions = np.asarray(data["actions"])
# 【L0073】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】保留每个时间步前七维并以 `actions` 键返回，即六个 RM65 绝对关节目标加一个 4C2 夹爪目标。
        return {"actions": actions[..., :7]}
```
