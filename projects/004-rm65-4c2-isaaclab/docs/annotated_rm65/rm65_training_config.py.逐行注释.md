# `rm65_training_config.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/rm65_training_config.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`604abbc01a0178beb92bb6aace6f946221688219e871383e4f12553d0c202036`
- 总行数：117

## 1. 先把这个程序放进整个项目

- 所处阶段：模型微调配置：组合字段重排、RM65 transform、动作语义、LoRA 和资源参数。
- 输入：数据集 repo id、基础 π0.5 权重、动作 horizon、batch/step 和内存选项。
- 输出：OpenPI TrainConfig/DataConfig。
- 一句话作用：把 LeRobot 数据字段、RM65 transform、绝对/增量动作语义和 π0.5 LoRA 训练超参数拼成 OpenPI TrainConfig。

### 为什么要写它

- 原先的问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。
- 采用的解决办法：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **dataclass**：数据类：根据字段声明自动生成初始化方法；适合固定配置或结构化记录。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-17` `2b2df452` **Prepare RM65 pi0.5 LoRA data config**：增加 RM65 数据重排、动作语义和 LoRA 训练配置。
- `2026-09-19` `0f92fcd8` **Prepare RM65 data and low-memory pi0.5 training**：针对显存限制补充低内存训练与 RM65 统计量配置。
- `2026-09-28` `a2f7ace3` **Prepare RM65 pi0.5 failure-correction v3**：根据闭环失败准备 v3 修正数据与训练配置。

### 与上一版教学快照的源码差异

- 当前第 15-15 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`from openpi.training import optimizer as training_optimizer`
- 当前第 71-74 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`initial_params_path: str = "gs://openpi-assets/checkpoints/pi05_base/params",` / `warmup_steps: int = 1_000,` / `peak_lr: float = 2.5e-5,` / `decay_lr: float = 2.5e-6,`
- 当前第 103-109 行相对旧教学快照发生 `replace`：旧版 1 行，当前 7 行。 旧代码摘录：`"gs://openpi-assets/checkpoints/pi05_base/params"` 当前代码摘录：`initial_params_path` / `),` / `lr_schedule=training_optimizer.CosineDecaySchedule(` / `warmup_steps=warmup_steps,`

## 4. 模块地图

- 模块 1｜第 1-21 行：OpenPI/Flax 训练组件与 RM65 transform
- 模块 2｜第 22-65 行：LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则
- 模块 3｜第 66-87 行：创建 π0.5、10 步动作 horizon 和两组 LoRA
- 模块 4｜第 88-94 行：冻结图像编码器以适配 16 GB GPU 和小数据集
- 模块 5｜第 95-117 行：基础权重、数据集、batch、步数和日志配置

### 函数/类快速索引

- `class LeRobotRM65DataConfig`：第 23-63 行
  - `LeRobotRM65DataConfig.create()`：第 27-63 行
- `make_pi05_rm65_lora_config()`：第 66-117 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：OpenPI/Flax 训练组件与 RM65 transform（源码第 1-21 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：OpenPI/Flax 训练组件与 RM65 transform。
- 下游：处理结果继续交给模块 2“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。

### 5.B 为什么需要这一组代码

这一组负责“OpenPI/Flax 训练组件与 RM65 transform”。它服务于本文件要解决的总问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。 这一组的处理结果会参与：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

### 5.C 本模块主要变量

- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。

### 5.F 这一模块的版本变化

- 当前第 15-15 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`from openpi.training import optimizer as training_optimizer`

### 5.G 逐行精读

```python
# 【L0001】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `OpenPI data and LoRA training configuration for RM65-B + 4C2.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""OpenPI data and LoRA training configuration for RM65-B + 4C2."""
# 【L0002】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0003】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0005】语法拆解：`import` 加载模块；`dataclasses` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】语法拆解：`import` 加载模块；`pathlib` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `pathlib` 引入 `pathlib`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
import pathlib
# 【L0007】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0008】语法拆解：`import` 加载模块；`flax.nnx as nnx` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `flax` 引入 `flax.nnx as nnx`。在这份程序里，`flax` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import flax.nnx as nnx
# 【L0009】语法拆解：`from typing_extensions` 指定来源模块；`import override` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `typing_extensions` 引入 `override`。在这份程序里，`typing_extensions` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing_extensions import override
# 【L0010】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0011】语法拆解：`from openpi.models` 指定来源模块；`import model as _model` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `model as _model`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import model as _model
# 【L0012】语法拆解：`from openpi.models` 指定来源模块；`import pi0_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `pi0_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import pi0_config
# 【L0013】语法拆解：`from openpi.shared` 指定来源模块；`import nnx_utils` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `nnx_utils`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.shared import nnx_utils
# 【L0014】语法拆解：`from openpi.training` 指定来源模块；`import config as training_config` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `config as training_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.training import config as training_config
# 【L0015】语法拆解：`from openpi.training` 指定来源模块；`import optimizer as training_optimizer` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `optimizer as training_optimizer`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.training import optimizer as training_optimizer
# 【L0016】语法拆解：`from openpi.training` 指定来源模块；`import weight_loaders` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi` 引入 `weight_loaders`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.training import weight_loaders
# 【L0017】语法拆解：`import` 加载模块；`openpi.transforms as transforms` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `openpi` 引入 `openpi.transforms as transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.transforms as transforms
# 【L0018】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0019】语法拆解：`from openpi_extension.rm65_policy` 指定来源模块；`import RM65Inputs, RM65Outputs` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `RM65Inputs, RM65Outputs`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_policy import RM65Inputs, RM65Outputs
# 【L0020】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0021】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“OpenPI/Flax 训练组件与 RM65 transform”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则（源码第 22-65 行）

### 5.A 数据流位置

- 上游：模块 1“OpenPI/Flax 训练组件与 RM65 transform”。
- 本模块：LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则。
- 下游：处理结果继续交给模块 3“创建 π0.5、10 步动作 horizon 和两组 LoRA”。

### 5.B 为什么需要这一组代码

这一组负责“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。它服务于本文件要解决的总问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。 这一组的处理结果会参与：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `joints`：六个 RM65 关节位置的一维 NumPy 数组。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `current`：float32 格式的当前六关节角。
- `model_type`：OpenPI 模型类型；本项目接受 PI0 或 PI05。
- `repack`：把 LeRobot 字段名重新打包成 RM65Inputs 所需字段名的 transform 组。
- `data_transforms`：训练和推理共享的 RM65 输入/输出及动作语义变换链。
- `delta_action_mask`：指定前六个关节动作转为相对当前 state 的增量，最后夹爪维保持绝对值的布尔规则。

### 5.D 本模块首次阅读要认识的调用

- `dataclasses.dataclass(...)`：圆括号表示真正执行调用；把带类型标注的类变成数据类，自动生成构造函数等样板方法。
- `LeRobotRM65DataConfig(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `create(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `transforms.Group(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `transforms.RepackTransform(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `RM65Inputs(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `RM65Outputs(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `transforms.make_bool_mask(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `data_transforms.push(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `transforms.DeltaActions(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `transforms.AbsoluteActions(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `dataclasses.replace(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`LeRobotRM65DataConfig.create()`（第 27-63 行）

- 定义了什么：LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`assets_dirs`：类型 `pathlib.Path`；项目含义是本功能块中的 `assets_dirs` 值；`model_config`：类型 `_model.BaseModelConfig`；项目含义是配置相关值
- 返回类型标注：`training_config.DataConfig`。
- 函数体实际 return：`dataclasses.replace(self.create_base_config(assets_dirs, model_config), repack_transforms=repack, data_transforms=data_transforms, model_transforms=training_config.ModelTransformFactory()(model_config))`
- 项目中的实际调用位置：`convert_expert_episodes_to_lerobot.py:238` 的 `dataset = LeRobotDataset.create(`；`compute_rm65_norm_stats.py:60` 的 `data_config = config.data.create(config.assets_dirs, config.model)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0022】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclasses.dataclass(frozen=True)
# 【L0023】语法拆解：`class` 定义类 `LeRobotRM65DataConfig`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `LeRobotRM65DataConfig` 类并继承 `training_config.DataConfigFactory`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class LeRobotRM65DataConfig(training_config.DataConfigFactory):
# 【L0024】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Map the RM65 LeRobot schema to the shared inference-time transform.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Map the RM65 LeRobot schema to the shared inference-time transform."""
# 【L0025】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的逻辑段，让结构更容易看清。

# 【L0026】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】装饰器 `@override`：在下面的函数或类创建时附加框架行为；具体行为由这个装饰器名字决定。
    @override
# 【L0027】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `create(参数在后续行继续)`；调用者把参数交给它完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”，后面的缩进代码是具体实现。
    def create(
# 【L0028】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`self` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0029】语法拆解：`assets_dirs` 是参数/字段名；冒号 `:` 添加类型提示 `pathlib.Path`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `assets_dirs`，类型提示为 `pathlib.Path`；在本项目中它表示本功能块中的 `assets_dirs` 值。
        assets_dirs: pathlib.Path,
# 【L0030】语法拆解：`model_config` 是参数/字段名；冒号 `:` 添加类型提示 `_model.BaseModelConfig`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `model_config`，类型提示为 `_model.BaseModelConfig`；在本项目中它表示配置相关值。
        model_config: _model.BaseModelConfig,
# 【L0031】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> training_config.DataConfig:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
    ) -> training_config.DataConfig:
# 【L0032】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repack`。右侧语法为：`transforms.Group(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `repack`，它在本项目中表示把 LeRobot 字段名重新打包成 RM65Inputs 所需字段名的 transform 组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.Group(`；`transforms` 表示本功能块中的 `transforms` 值；`Group` 表示本功能块中的 `Group` 值。
        repack = transforms.Group(
# 【L0033】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inputs`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `inputs`，它在本项目中表示本功能块中的 `inputs` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            inputs=[
# 【L0034】语法拆解：`transforms.RepackTransform(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `transforms` 调用多行方法 `RepackTransform`：调用 `transforms` 提供的 `RepackTransform` 操作；具体参数写在随后几行，用于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                transforms.RepackTransform(
# 【L0035】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    {
# 【L0036】语法拆解：这是字典键值对：`"observation/external_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"image"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `observation/external_image`，它表示固定外部相机看到的 RGB 图像；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/external_image": "image",
# 【L0037】语法拆解：这是字典键值对：`"observation/wrist_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"wrist_image"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `observation/wrist_image`，它表示随 RM65 末端运动的腕部相机 RGB 图像；字段值来自 `"wrist_image"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/wrist_image": "wrist_image",
# 【L0038】语法拆解：这是字典键值对：`"observation/joint_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"joints"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `observation/joint_position`，它表示IsaacLab 当前观测到的六个 RM65 关节角，顺序 joint_1 到 joint_6，单位 rad；字段值来自 `"joints"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/joint_position": "joints",
# 【L0039】语法拆解：这是字典键值对：`"observation/gripper_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"gripper"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `observation/gripper_position`，它表示4C2 主关节位置归一化后的单元素数组，0 表示张开、1 表示闭合；字段值来自 `"gripper"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/gripper_position": "gripper",
# 【L0040】语法拆解：这是字典键值对：`"actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"actions"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `"actions"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "actions": "actions",
# 【L0041】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"prompt"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `"prompt"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "prompt": "prompt",
# 【L0042】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    }
# 【L0043】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                )
# 【L0044】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            ]
# 【L0045】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0046】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_transforms`。右侧语法为：`transforms.Group(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `data_transforms`，它在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.Group(`；`transforms` 表示本功能块中的 `transforms` 值；`Group` 表示本功能块中的 `Group` 值。
        data_transforms = transforms.Group(
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inputs`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `inputs` 传入 `[RM65Inputs(model_type=model_config.model_type)]`；该参数在本项目中表示本功能块中的 `inputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[RM65Inputs(model_type=model_config.model_type)],
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `outputs`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `outputs` 传入 `[RM65Outputs()]`；该参数在本项目中表示本功能块中的 `outputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[RM65Outputs()],
# 【L0049】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0050】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：The scripted expert stores absolute joint targets. OpenPI trains joint
        # The scripted expert stores absolute joint targets. OpenPI trains joint
# 【L0051】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：dimensions as deltas from the current state and keeps the gripper
        # dimensions as deltas from the current state and keeps the gripper
# 【L0052】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：target absolute.
        # target absolute.
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `delta_action_mask`。右侧语法为：`transforms` 是模块/对象，点号 `.` 从中取出 `make_bool_mask` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `6`；第 2 个实参 `-1`。
# 【项目含义】得到 `delta_action_mask`，它在本项目中表示指定前六个关节动作转为相对当前 state 的增量，最后夹爪维保持绝对值的布尔规则；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.make_bool_mask(6, -1)`；`transforms` 表示本功能块中的 `transforms` 值；`make_bool_mask` 表示掩码相关值。
        delta_action_mask = transforms.make_bool_mask(6, -1)
# 【L0054】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_transforms`。右侧语法为：`data_transforms.push(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `data_transforms`，它在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_transforms.push(`；`data_transforms` 表示训练和推理共享的 RM65 输入/输出及动作语义变换链；`push` 表示本功能块中的 `push` 值。
        data_transforms = data_transforms.push(
# 【L0055】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inputs`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `inputs` 传入 `[transforms.DeltaActions(delta_action_mask)]`；该参数在本项目中表示本功能块中的 `inputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[transforms.DeltaActions(delta_action_mask)],
# 【L0056】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `outputs`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `outputs` 传入 `[transforms.AbsoluteActions(delta_action_mask)]`；该参数在本项目中表示本功能块中的 `outputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[transforms.AbsoluteActions(delta_action_mask)],
# 【L0057】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0058】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`dataclasses.replace(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `dataclasses.replace(` 交回调用者；这个值的含义是：计算表达式 `dataclasses.replace(`；`dataclasses` 表示本功能块中的 `dataclasses` 值；`replace` 表示本功能块中的 `replace` 值。
        return dataclasses.replace(
# 【L0059】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`self` 是模块/对象，点号 `.` 从中取出 `create_base_config` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `assets_dirs`；第 2 个实参 `model_config`。
# 【项目含义】对 `self` 调用 `create_base_config(assets_dirs, model_config)`：调用 `self` 提供的 `create_base_config` 操作。本行产生的修改/返回值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            self.create_base_config(assets_dirs, model_config),
# 【L0060】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repack_transforms`。右侧语法为：`repack` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `repack_transforms` 传入 `repack`；该参数在本项目中表示本功能块中的 `repack_transforms` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            repack_transforms=repack,
# 【L0061】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_transforms`。右侧语法为：`data_transforms` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `data_transforms` 传入 `data_transforms`；该参数在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            data_transforms=data_transforms,
# 【L0062】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `model_transforms`。右侧语法为：`training_config` 是模块/对象，点号 `.` 从中取出 `ModelTransformFactory` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `)(model_config`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `model_transforms` 传入 `training_config.ModelTransformFactory()(model_config)`；该参数在本项目中表示本功能块中的 `model_transforms` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            model_transforms=training_config.ModelTransformFactory()(model_config),
# 【L0063】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0064】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的逻辑段，让结构更容易看清。

# 【L0065】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：创建 π0.5、10 步动作 horizon 和两组 LoRA（源码第 66-87 行）

### 5.A 数据流位置

- 上游：模块 2“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
- 本模块：创建 π0.5、10 步动作 horizon 和两组 LoRA。
- 下游：处理结果继续交给模块 4“冻结图像编码器以适配 16 GB GPU 和小数据集”。

### 5.B 为什么需要这一组代码

这一组负责“创建 π0.5、10 步动作 horizon 和两组 LoRA”。它服务于本文件要解决的总问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。 这一组的处理结果会参与：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

### 5.C 本模块主要变量

- `config`：RM65 π0.5 训练/推理使用的完整 OpenPI 配置。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `make_pi05_rm65_lora_config(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `pi0_config.Pi0Config(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`make_pi05_rm65_lora_config()`（第 66-117 行）

- 定义了什么：创建 π0.5、10 步动作 horizon 和两组 LoRA。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`repo_id`（仅关键字）：类型 `str`，默认 `'local/rm65_sim'`；项目含义是LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；`batch_size`（仅关键字）：类型 `int`，默认 `1`；项目含义是本功能块中的 `batch_size` 值；`num_train_steps`（仅关键字）：类型 `int`，默认 `30000`；项目含义是步数相关值；`initial_params_path`（仅关键字）：类型 `str`，默认 `'gs://openpi-assets/checkpoints/pi05_base/params'`；项目含义是路径相关值；`warmup_steps`（仅关键字）：类型 `int`，默认 `1000`；项目含义是步数相关值；`peak_lr`（仅关键字）：类型 `float`，默认 `2.5e-05`；项目含义是本功能块中的 `peak_lr` 值；`decay_lr`（仅关键字）：类型 `float`，默认 `2.5e-06`；项目含义是本功能块中的 `decay_lr` 值
- 返回类型标注：`training_config.TrainConfig`。
- 函数体实际 return：`training_config.TrainConfig(name='pi05_rm65_lora', model=model, data=LeRobotRM65DataConfig(repo_id=repo_id, base_config=training_config.DataConfig(prompt_from_task=True)), weight_loader=weight_loaders.CheckpointWeightLoader(initial_params_path), lr_schedule=training_optimizer.CosineDecaySchedule(warmup_steps=warmup_steps, peak_lr=peak_lr, decay_steps=num_train_steps, decay_lr=decay_lr), freeze_filter=freeze_filter, ema_decay=None, batch_size=batch_size, num_workers=0, num_train_steps=num_train_steps, wandb_enabled=False)`
- 项目中的实际调用位置：`train_rm65_pi05.py:85` 的 `config = make_pi05_rm65_lora_config(`；`serve_rm65_policy.py:36` 的 `config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)`；`compute_rm65_norm_stats.py:51` 的 `config = make_pi05_rm65_lora_config(`；`validate_rm65_checkpoint.py:59` 的 `config = make_pi05_rm65_lora_config(repo_id=args.repo_id, batch_size=1)`


### 5.F 这一模块的版本变化

- 当前第 71-74 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`initial_params_path: str = "gs://openpi-assets/checkpoints/pi05_base/params",` / `warmup_steps: int = 1_000,` / `peak_lr: float = 2.5e-5,` / `decay_lr: float = 2.5e-6,`

### 5.G 逐行精读

```python
# 【L0066】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `make_pi05_rm65_lora_config(参数在后续行继续)`；调用者把参数交给它完成“创建 π0.5、10 步动作 horizon 和两组 LoRA”，后面的缩进代码是具体实现。
def make_pi05_rm65_lora_config(
# 【L0067】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    *,
# 【L0068】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id: str`。右侧语法为：`"local/rm65_sim"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `repo_id`，它在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"local/rm65_sim"`；`local` 表示本功能块中的 `local` 值；`rm65_sim` 表示仿真相关值。
    repo_id: str = "local/rm65_sim",
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `batch_size: int`。右侧语法为：`1` 是直接写在源码中的数值常量。
# 【项目含义】得到 `batch_size`，它在本项目中表示本功能块中的 `batch_size` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `1` 的结果保存下来，供当前功能块后续使用。
    batch_size: int = 1,
# 【L0070】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_train_steps: int`。右侧语法为：`30_000` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `num_train_steps`，它在本项目中表示步数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `30_000` 的结果保存下来，供当前功能块后续使用。
    num_train_steps: int = 30_000,
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_params_path: str`。右侧语法为：`"gs://openpi-assets/checkpoints/pi05_base/params"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `initial_params_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"gs://openpi-assets/checkpoints/pi05_base/params"`；`gs` 表示本功能块中的 `gs` 值；`openpi` 表示本功能块中的 `openpi` 值；`assets` 表示本功能块中的 `assets` 值。
    initial_params_path: str = "gs://openpi-assets/checkpoints/pi05_base/params",
# 【L0072】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warmup_steps: int`。右侧语法为：`1_000` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `warmup_steps`，它在本项目中表示步数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `1_000` 的结果保存下来，供当前功能块后续使用。
    warmup_steps: int = 1_000,
# 【L0073】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `peak_lr: float`。右侧语法为：`2.5e-5` 是直接写在源码中的数值常量。
# 【项目含义】得到 `peak_lr`，它在本项目中表示本功能块中的 `peak_lr` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `2.5e-5` 的结果保存下来，供当前功能块后续使用。
    peak_lr: float = 2.5e-5,
# 【L0074】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `decay_lr: float`。右侧语法为：`2.5e-6` 是直接写在源码中的数值常量。
# 【项目含义】得到 `decay_lr`，它在本项目中表示本功能块中的 `decay_lr` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `2.5e-6` 的结果保存下来，供当前功能块后续使用。
    decay_lr: float = 2.5e-6,
# 【L0075】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> training_config.TrainConfig:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
) -> training_config.TrainConfig:
# 【L0076】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Build, without globally registering, the RM65 π0.5 LoRA config.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Build, without globally registering, the RM65 π0.5 LoRA config."""
# 【L0077】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“创建 π0.5、10 步动作 horizon 和两组 LoRA”中的逻辑段，让结构更容易看清。

# 【L0078】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `model`。右侧语法为：`pi0_config.Pi0Config(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `model`，它在本项目中表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pi0_config.Pi0Config(`；`pi0_config` 表示配置相关值；`Pi0Config` 表示本功能块中的 `Pi0Config` 值。
    model = pi0_config.Pi0Config(
# 【L0079】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pi05`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `pi05` 传入 `True`；该参数在本项目中表示本功能块中的 `pi05` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        pi05=True,
# 【L0080】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_horizon`。右侧语法为：`10` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_horizon` 传入 `10`；该参数在本项目中表示动作相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_horizon=10,
# 【L0081】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：The RM65 task prompts are short. A 64-token ceiling retains ample
        # The RM65 task prompts are short. A 64-token ceiling retains ample
# 【L0082】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：margin while avoiding 136 unused language positions per sample.
        # margin while avoiding 136 unused language positions per sample.
# 【L0083】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_token_len`。右侧语法为：`64` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `max_token_len` 传入 `64`；该参数在本项目中表示本功能块中的 `max_token_len` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        max_token_len=64,
# 【L0084】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `discrete_state_input`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `discrete_state_input` 传入 `False`；该参数在本项目中表示状态、输入相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        discrete_state_input=False,
# 【L0085】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `paligemma_variant`。右侧语法为：`"gemma_2b_lora"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `paligemma_variant` 传入 `"gemma_2b_lora"`；该参数在本项目中表示本功能块中的 `paligemma_variant` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        paligemma_variant="gemma_2b_lora",
# 【L0086】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_expert_variant`。右侧语法为：`"gemma_300m_lora"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_expert_variant` 传入 `"gemma_300m_lora"`；该参数在本项目中表示动作相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_expert_variant="gemma_300m_lora",
# 【L0087】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“创建 π0.5、10 步动作 horizon 和两组 LoRA”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：冻结图像编码器以适配 16 GB GPU 和小数据集（源码第 88-94 行）

### 5.A 数据流位置

- 上游：模块 3“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
- 本模块：冻结图像编码器以适配 16 GB GPU 和小数据集。
- 下游：处理结果继续交给模块 5“基础权重、数据集、batch、步数和日志配置”。

### 5.B 为什么需要这一组代码

这一组负责“冻结图像编码器以适配 16 GB GPU 和小数据集”。它服务于本文件要解决的总问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。 这一组的处理结果会参与：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

### 5.C 本模块主要变量

- `dataset`：LeRobotDataset 对象，用于逐帧构造训练集。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `freeze_filter`：指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器。

### 5.D 本模块首次阅读要认识的调用

- `nnx.Any(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `model.get_freeze_filter(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `nnx_utils.PathRegex(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0088】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：The 16 GB lab GPU cannot train the SigLIP image tower together with both
    # The 16 GB lab GPU cannot train the SigLIP image tower together with both
# 【L0089】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：LoRA adapters. Keeping the pretrained visual encoder fixed is also the
    # LoRA adapters. Keeping the pretrained visual encoder fixed is also the
# 【L0090】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：intended transfer-learning regime for this small simulated dataset.
    # intended transfer-learning regime for this small simulated dataset.
# 【L0091】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `freeze_filter`。右侧语法为：`nnx.Any(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `freeze_filter`，它在本项目中表示指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `nnx.Any(`；`nnx` 表示本功能块中的 `nnx` 值；`Any` 表示本功能块中的 `Any` 值。
    freeze_filter = nnx.Any(
# 【L0092】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`model` 是模块/对象，点号 `.` 从中取出 `get_freeze_filter` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `model` 调用 `get_freeze_filter()`：调用 `model` 提供的 `get_freeze_filter` 操作。本行产生的修改/返回值服务于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
        model.get_freeze_filter(),
# 【L0093】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`nnx_utils` 是模块/对象，点号 `.` 从中取出 `PathRegex` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `".*img.*"`。
# 【项目含义】调用 `Path`：创建路径对象；本行实际操作 `nnx_utils.PathRegex(".*img.*"),`。`nnx_utils` 表示本功能块中的 `nnx_utils` 值；`PathRegex` 表示本功能块中的 `PathRegex` 值。
        nnx_utils.PathRegex(".*img.*"),
# 【L0094】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“冻结图像编码器以适配 16 GB GPU 和小数据集”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：基础权重、数据集、batch、步数和日志配置（源码第 95-117 行）

### 5.A 数据流位置

- 上游：模块 4“冻结图像编码器以适配 16 GB GPU 和小数据集”。
- 本模块：基础权重、数据集、batch、步数和日志配置。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“基础权重、数据集、batch、步数和日志配置”。它服务于本文件要解决的总问题：RM65 与 DROID 的关节数、动作分布和统计量不同，16 GB GPU 也不能直接全量训练大模型。 这一组的处理结果会参与：前六维使用 delta action、夹爪保持绝对语义，加载 RM65 norm stats，并用 LoRA/冻结视觉编码器降低显存。

### 5.C 本模块主要变量

- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `model`：配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置。
- `freeze_filter`：指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器。
- `repo_id`：LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本。

### 5.D 本模块首次阅读要认识的调用

- `training_config.TrainConfig(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `LeRobotRM65DataConfig(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `training_config.DataConfig(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `weight_loaders.CheckpointWeightLoader(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `training_optimizer.CosineDecaySchedule(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 103-109 行相对旧教学快照发生 `replace`：旧版 1 行，当前 7 行。 旧代码摘录：`"gs://openpi-assets/checkpoints/pi05_base/params"` 当前代码摘录：`initial_params_path` / `),` / `lr_schedule=training_optimizer.CosineDecaySchedule(` / `warmup_steps=warmup_steps,`

### 5.G 逐行精读

```python
# 【L0095】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`training_config.TrainConfig(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `training_config.TrainConfig(` 交回调用者；这个值的含义是：计算表达式 `training_config.TrainConfig(`；`training_config` 表示配置相关值；`TrainConfig` 表示本功能块中的 `TrainConfig` 值。
    return training_config.TrainConfig(
# 【L0096】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `name`。右侧语法为：`"pi05_rm65_lora"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `name` 传入 `"pi05_rm65_lora"`；该参数在本项目中表示本功能块中的 `name` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        name="pi05_rm65_lora",
# 【L0097】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `model`。右侧语法为：`model` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `model` 传入 `model`；该参数在本项目中表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置，会参与“基础权重、数据集、batch、步数和日志配置”。
        model=model,
# 【L0098】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data`。右侧语法为：`LeRobotRM65DataConfig(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `data`，它在本项目中表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `LeRobotRM65DataConfig(`；`LeRobotRM65DataConfig` 表示本功能块中的 `LeRobotRM65DataConfig` 值。
        data=LeRobotRM65DataConfig(
# 【L0099】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `repo_id`。右侧语法为：`repo_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“基础权重、数据集、batch、步数和日志配置”。
            repo_id=repo_id,
# 【L0100】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `base_config`。右侧语法为：`training_config` 是模块/对象，点号 `.` 从中取出 `DataConfig` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prompt_from_task=True`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `base_config` 传入 `training_config.DataConfig(prompt_from_task=True)`；该参数在本项目中表示配置相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
            base_config=training_config.DataConfig(prompt_from_task=True),
# 【L0101】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0102】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `weight_loader`。右侧语法为：`weight_loaders.CheckpointWeightLoader(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `weight_loader`，它在本项目中表示本功能块中的 `weight_loader` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `weight_loaders.CheckpointWeightLoader(`；`weight_loaders` 表示本功能块中的 `weight_loaders` 值；`CheckpointWeightLoader` 表示本功能块中的 `CheckpointWeightLoader` 值。
        weight_loader=weight_loaders.CheckpointWeightLoader(
# 【L0103】语法拆解：`initial_params_path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `initial_params_path`；在本项目中它表示路径相关值。
            initial_params_path
# 【L0104】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0105】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lr_schedule`。右侧语法为：`training_optimizer.CosineDecaySchedule(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `lr_schedule`，它在本项目中表示本功能块中的 `lr_schedule` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `training_optimizer.CosineDecaySchedule(`；`training_optimizer` 表示本功能块中的 `training_optimizer` 值；`CosineDecaySchedule` 表示本功能块中的 `CosineDecaySchedule` 值。
        lr_schedule=training_optimizer.CosineDecaySchedule(
# 【L0106】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warmup_steps`。右侧语法为：`warmup_steps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warmup_steps` 传入 `warmup_steps`；该参数在本项目中表示步数相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
            warmup_steps=warmup_steps,
# 【L0107】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `peak_lr`。右侧语法为：`peak_lr` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `peak_lr` 传入 `peak_lr`；该参数在本项目中表示本功能块中的 `peak_lr` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
            peak_lr=peak_lr,
# 【L0108】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `decay_steps`。右侧语法为：`num_train_steps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `decay_steps` 传入 `num_train_steps`；该参数在本项目中表示步数相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
            decay_steps=num_train_steps,
# 【L0109】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `decay_lr`。右侧语法为：`decay_lr` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `decay_lr` 传入 `decay_lr`；该参数在本项目中表示本功能块中的 `decay_lr` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
            decay_lr=decay_lr,
# 【L0110】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0111】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `freeze_filter`。右侧语法为：`freeze_filter` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `freeze_filter` 传入 `freeze_filter`；该参数在本项目中表示指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器，会参与“基础权重、数据集、batch、步数和日志配置”。
        freeze_filter=freeze_filter,
# 【L0112】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `ema_decay`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `ema_decay` 传入 `None`；该参数在本项目中表示本功能块中的 `ema_decay` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        ema_decay=None,
# 【L0113】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `batch_size`。右侧语法为：`batch_size` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `batch_size` 传入 `batch_size`；该参数在本项目中表示本功能块中的 `batch_size` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        batch_size=batch_size,
# 【L0114】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_workers`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `num_workers` 传入 `0`；该参数在本项目中表示本功能块中的 `num_workers` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        num_workers=0,
# 【L0115】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `num_train_steps`。右侧语法为：`num_train_steps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `num_train_steps` 传入 `num_train_steps`；该参数在本项目中表示步数相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
        num_train_steps=num_train_steps,
# 【L0116】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wandb_enabled`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `wandb_enabled` 传入 `False`；该参数在本项目中表示本功能块中的 `wandb_enabled` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        wandb_enabled=False,
# 【L0117】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
    )
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“基础权重、数据集、batch、步数和日志配置”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。