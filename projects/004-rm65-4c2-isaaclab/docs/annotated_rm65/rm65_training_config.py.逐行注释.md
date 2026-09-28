# `rm65_training_config.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/openpi_extension/rm65_training_config.py`
- 快照 SHA-256：`c98cf98d04863aeeff386434aab115523f43d332d6371b417f288e37866db0c6`
- 总行数：106
- 程序作用：把 LeRobot 数据字段、RM65 transform、绝对/增量动作语义和 π0.5 LoRA 训练超参数拼成 OpenPI TrainConfig。
- 推荐读法：先读 31-62 的数据路径，再读 73-106 的模型与显存策略。

## 功能块地图

- 第 1-19 行：OpenPI/Flax 训练组件与 RM65 transform
- 第 21-62 行：LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则
- 第 65-82 行：创建 π0.5、10 步动作 horizon 和两组 LoRA
- 第 83-89 行：冻结图像编码器以适配 16 GB GPU 和小数据集
- 第 90-106 行：基础权重、数据集、batch、步数和日志配置

## 函数/类索引

- `class LeRobotRM65DataConfig`：第 22-62 行
  - `LeRobotRM65DataConfig.create()`：第 26-62 行
- `make_pi05_rm65_lora_config()`：第 65-106 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】说明字符串 `OpenPI data and LoRA training configuration for RM65-B + 4C2.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""OpenPI data and LoRA training configuration for RM65-B + 4C2."""
# 【L0002】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0003】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0005】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】从 `pathlib` 引入 `pathlib`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
import pathlib
# 【L0007】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0008】从 `flax` 引入 `flax.nnx as nnx`。在这份程序里，`flax` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import flax.nnx as nnx
# 【L0009】从 `typing_extensions` 引入 `override`。在这份程序里，`typing_extensions` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing_extensions import override
# 【L0010】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0011】从 `openpi` 引入 `model as _model`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import model as _model
# 【L0012】从 `openpi` 引入 `pi0_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import pi0_config
# 【L0013】从 `openpi` 引入 `nnx_utils`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.shared import nnx_utils
# 【L0014】从 `openpi` 引入 `config as training_config`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.training import config as training_config
# 【L0015】从 `openpi` 引入 `weight_loaders`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.training import weight_loaders
# 【L0016】从 `openpi` 引入 `openpi.transforms as transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.transforms as transforms
# 【L0017】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0018】从 `openpi_extension` 引入 `RM65Inputs, RM65Outputs`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_policy import RM65Inputs, RM65Outputs
# 【L0019】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0020】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0021】把下面的类变成数据类，自动生成初始化等方法；若含 `frozen=True`，配置创建后不可修改，可避免实验中途改变合同。
@dataclasses.dataclass(frozen=True)
# 【L0022】定义 `LeRobotRM65DataConfig` 类并继承 `training_config.DataConfigFactory`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class LeRobotRM65DataConfig(training_config.DataConfigFactory):
# 【L0023】说明字符串 `Map the RM65 LeRobot schema to the shared inference-time transform.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Map the RM65 LeRobot schema to the shared inference-time transform."""
# 【L0024】空行：分隔“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的逻辑段，让结构更容易看清。

# 【L0025】装饰器 `@override`：在下面的函数或类创建时附加框架行为；具体行为由这个装饰器名字决定。
    @override
# 【L0026】定义函数 `create(参数在后续行继续)`；调用者把参数交给它完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”，后面的缩进代码是具体实现。
    def create(
# 【L0027】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0028】声明/传入参数 `assets_dirs`，类型提示为 `pathlib.Path`；在本项目中它表示本功能块中的 `assets_dirs` 值。
        assets_dirs: pathlib.Path,
# 【L0029】声明/传入参数 `model_config`，类型提示为 `_model.BaseModelConfig`；在本项目中它表示配置相关值。
        model_config: _model.BaseModelConfig,
# 【L0030】以 `) -> training_config.DataConfig:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
    ) -> training_config.DataConfig:
# 【L0031】得到 `repack`，它在本项目中表示把 LeRobot 字段名重新打包成 RM65Inputs 所需字段名的 transform 组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.Group(`；`transforms` 表示本功能块中的 `transforms` 值；`Group` 表示本功能块中的 `Group` 值。
        repack = transforms.Group(
# 【L0032】得到 `inputs`，它在本项目中表示本功能块中的 `inputs` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            inputs=[
# 【L0033】开始对 `transforms` 调用多行方法 `RepackTransform`：调用 `transforms` 提供的 `RepackTransform` 操作；具体参数写在随后几行，用于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                transforms.RepackTransform(
# 【L0034】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    {
# 【L0035】定义字典/JSON 字段 `observation/external_image`，它表示固定外部相机看到的 RGB 图像；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/external_image": "image",
# 【L0036】定义字典/JSON 字段 `observation/wrist_image`，它表示随 RM65 末端运动的腕部相机 RGB 图像；字段值来自 `"wrist_image"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/wrist_image": "wrist_image",
# 【L0037】定义字典/JSON 字段 `observation/joint_position`，它表示IsaacLab 当前观测到的六个 RM65 关节角，顺序 joint_1 到 joint_6，单位 rad；字段值来自 `"joints"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/joint_position": "joints",
# 【L0038】定义字典/JSON 字段 `observation/gripper_position`，它表示4C2 主关节位置归一化后的单元素数组，0 表示张开、1 表示闭合；字段值来自 `"gripper"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "observation/gripper_position": "gripper",
# 【L0039】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `"actions"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "actions": "actions",
# 【L0040】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `"prompt"`，因此保存/传递的是这个表达式当前计算出的结果。
                        "prompt": "prompt",
# 【L0041】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    }
# 【L0042】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                )
# 【L0043】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            ]
# 【L0044】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0045】得到 `data_transforms`，它在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.Group(`；`transforms` 表示本功能块中的 `transforms` 值；`Group` 表示本功能块中的 `Group` 值。
        data_transforms = transforms.Group(
# 【L0046】给上一层函数/配置构造器的命名参数 `inputs` 传入 `[RM65Inputs(model_type=model_config.model_type)]`；该参数在本项目中表示本功能块中的 `inputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[RM65Inputs(model_type=model_config.model_type)],
# 【L0047】给上一层函数/配置构造器的命名参数 `outputs` 传入 `[RM65Outputs()]`；该参数在本项目中表示本功能块中的 `outputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[RM65Outputs()],
# 【L0048】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0049】作者写下的设计说明：The scripted expert stores absolute joint targets. OpenPI trains joint
        # The scripted expert stores absolute joint targets. OpenPI trains joint
# 【L0050】作者写下的设计说明：dimensions as deltas from the current state and keeps the gripper
        # dimensions as deltas from the current state and keeps the gripper
# 【L0051】作者写下的设计说明：target absolute.
        # target absolute.
# 【L0052】得到 `delta_action_mask`，它在本项目中表示指定前六个关节动作转为相对当前 state 的增量，最后夹爪维保持绝对值的布尔规则；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transforms.make_bool_mask(6, -1)`；`transforms` 表示本功能块中的 `transforms` 值；`make_bool_mask` 表示掩码相关值。
        delta_action_mask = transforms.make_bool_mask(6, -1)
# 【L0053】得到 `data_transforms`，它在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_transforms.push(`；`data_transforms` 表示训练和推理共享的 RM65 输入/输出及动作语义变换链；`push` 表示本功能块中的 `push` 值。
        data_transforms = data_transforms.push(
# 【L0054】给上一层函数/配置构造器的命名参数 `inputs` 传入 `[transforms.DeltaActions(delta_action_mask)]`；该参数在本项目中表示本功能块中的 `inputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[transforms.DeltaActions(delta_action_mask)],
# 【L0055】给上一层函数/配置构造器的命名参数 `outputs` 传入 `[transforms.AbsoluteActions(delta_action_mask)]`；该参数在本项目中表示本功能块中的 `outputs` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[transforms.AbsoluteActions(delta_action_mask)],
# 【L0056】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0057】结束当前函数并把 `dataclasses.replace(` 交回调用者；这个值的含义是：计算表达式 `dataclasses.replace(`；`dataclasses` 表示本功能块中的 `dataclasses` 值；`replace` 表示本功能块中的 `replace` 值。
        return dataclasses.replace(
# 【L0058】对 `self` 调用 `create_base_config(assets_dirs, model_config)`：调用 `self` 提供的 `create_base_config` 操作。本行产生的修改/返回值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            self.create_base_config(assets_dirs, model_config),
# 【L0059】给上一层函数/配置构造器的命名参数 `repack_transforms` 传入 `repack`；该参数在本项目中表示本功能块中的 `repack_transforms` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            repack_transforms=repack,
# 【L0060】给上一层函数/配置构造器的命名参数 `data_transforms` 传入 `data_transforms`；该参数在本项目中表示训练和推理共享的 RM65 输入/输出及动作语义变换链，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            data_transforms=data_transforms,
# 【L0061】给上一层函数/配置构造器的命名参数 `model_transforms` 传入 `training_config.ModelTransformFactory()(model_config)`；该参数在本项目中表示本功能块中的 `model_transforms` 值，会参与“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            model_transforms=training_config.ModelTransformFactory()(model_config),
# 【L0062】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0063】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0064】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0065】定义函数 `make_pi05_rm65_lora_config(参数在后续行继续)`；调用者把参数交给它完成“创建 π0.5、10 步动作 horizon 和两组 LoRA”，后面的缩进代码是具体实现。
def make_pi05_rm65_lora_config(
# 【L0066】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    *,
# 【L0067】得到 `repo_id`，它在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"local/rm65_sim"`；`local` 表示本功能块中的 `local` 值；`rm65_sim` 表示仿真相关值。
    repo_id: str = "local/rm65_sim",
# 【L0068】得到 `batch_size`，它在本项目中表示本功能块中的 `batch_size` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `1` 的结果保存下来，供当前功能块后续使用。
    batch_size: int = 1,
# 【L0069】得到 `num_train_steps`，它在本项目中表示步数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `30_000` 的结果保存下来，供当前功能块后续使用。
    num_train_steps: int = 30_000,
# 【L0070】以 `) -> training_config.TrainConfig:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
) -> training_config.TrainConfig:
# 【L0071】说明字符串 `Build, without globally registering, the RM65 π0.5 LoRA config.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Build, without globally registering, the RM65 π0.5 LoRA config."""
# 【L0072】空行：分隔“创建 π0.5、10 步动作 horizon 和两组 LoRA”中的逻辑段，让结构更容易看清。

# 【L0073】得到 `model`，它在本项目中表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pi0_config.Pi0Config(`；`pi0_config` 表示配置相关值；`Pi0Config` 表示本功能块中的 `Pi0Config` 值。
    model = pi0_config.Pi0Config(
# 【L0074】给上一层函数/配置构造器的命名参数 `pi05` 传入 `True`；该参数在本项目中表示本功能块中的 `pi05` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        pi05=True,
# 【L0075】给上一层函数/配置构造器的命名参数 `action_horizon` 传入 `10`；该参数在本项目中表示动作相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_horizon=10,
# 【L0076】作者写下的设计说明：The RM65 task prompts are short. A 64-token ceiling retains ample
        # The RM65 task prompts are short. A 64-token ceiling retains ample
# 【L0077】作者写下的设计说明：margin while avoiding 136 unused language positions per sample.
        # margin while avoiding 136 unused language positions per sample.
# 【L0078】给上一层函数/配置构造器的命名参数 `max_token_len` 传入 `64`；该参数在本项目中表示本功能块中的 `max_token_len` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        max_token_len=64,
# 【L0079】给上一层函数/配置构造器的命名参数 `discrete_state_input` 传入 `False`；该参数在本项目中表示状态、输入相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        discrete_state_input=False,
# 【L0080】给上一层函数/配置构造器的命名参数 `paligemma_variant` 传入 `"gemma_2b_lora"`；该参数在本项目中表示本功能块中的 `paligemma_variant` 值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        paligemma_variant="gemma_2b_lora",
# 【L0081】给上一层函数/配置构造器的命名参数 `action_expert_variant` 传入 `"gemma_300m_lora"`；该参数在本项目中表示动作相关值，会参与“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_expert_variant="gemma_300m_lora",
# 【L0082】结束或闭合当前语法结构；它属于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    )
# 【L0083】作者写下的设计说明：The 16 GB lab GPU cannot train the SigLIP image tower together with both
    # The 16 GB lab GPU cannot train the SigLIP image tower together with both
# 【L0084】作者写下的设计说明：LoRA adapters. Keeping the pretrained visual encoder fixed is also the
    # LoRA adapters. Keeping the pretrained visual encoder fixed is also the
# 【L0085】作者写下的设计说明：intended transfer-learning regime for this small simulated dataset.
    # intended transfer-learning regime for this small simulated dataset.
# 【L0086】得到 `freeze_filter`，它在本项目中表示指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `nnx.Any(`；`nnx` 表示本功能块中的 `nnx` 值；`Any` 表示本功能块中的 `Any` 值。
    freeze_filter = nnx.Any(
# 【L0087】对 `model` 调用 `get_freeze_filter()`：调用 `model` 提供的 `get_freeze_filter` 操作。本行产生的修改/返回值服务于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
        model.get_freeze_filter(),
# 【L0088】调用 `Path`：创建路径对象；本行实际操作 `nnx_utils.PathRegex(".*img.*"),`。`nnx_utils` 表示本功能块中的 `nnx_utils` 值；`PathRegex` 表示本功能块中的 `PathRegex` 值。
        nnx_utils.PathRegex(".*img.*"),
# 【L0089】结束或闭合当前语法结构；它属于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
    )
# 【L0090】结束当前函数并把 `training_config.TrainConfig(` 交回调用者；这个值的含义是：计算表达式 `training_config.TrainConfig(`；`training_config` 表示配置相关值；`TrainConfig` 表示本功能块中的 `TrainConfig` 值。
    return training_config.TrainConfig(
# 【L0091】给上一层函数/配置构造器的命名参数 `name` 传入 `"pi05_rm65_lora"`；该参数在本项目中表示本功能块中的 `name` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        name="pi05_rm65_lora",
# 【L0092】给上一层函数/配置构造器的命名参数 `model` 传入 `model`；该参数在本项目中表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置，会参与“基础权重、数据集、batch、步数和日志配置”。
        model=model,
# 【L0093】得到 `data`，它在本项目中表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `LeRobotRM65DataConfig(`；`LeRobotRM65DataConfig` 表示本功能块中的 `LeRobotRM65DataConfig` 值。
        data=LeRobotRM65DataConfig(
# 【L0094】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“基础权重、数据集、batch、步数和日志配置”。
            repo_id=repo_id,
# 【L0095】给上一层函数/配置构造器的命名参数 `base_config` 传入 `training_config.DataConfig(prompt_from_task=True)`；该参数在本项目中表示配置相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
            base_config=training_config.DataConfig(prompt_from_task=True),
# 【L0096】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0097】得到 `weight_loader`，它在本项目中表示本功能块中的 `weight_loader` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `weight_loaders.CheckpointWeightLoader(`；`weight_loaders` 表示本功能块中的 `weight_loaders` 值；`CheckpointWeightLoader` 表示本功能块中的 `CheckpointWeightLoader` 值。
        weight_loader=weight_loaders.CheckpointWeightLoader(
# 【L0098】提供路径/资源标识 `"gs://openpi-assets/checkpoints/pi05_base/params"`；在“基础权重、数据集、batch、步数和日志配置”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "gs://openpi-assets/checkpoints/pi05_base/params"
# 【L0099】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0100】给上一层函数/配置构造器的命名参数 `freeze_filter` 传入 `freeze_filter`；该参数在本项目中表示指定训练时不更新哪些参数的过滤器；这里还冻结图像编码器，会参与“基础权重、数据集、batch、步数和日志配置”。
        freeze_filter=freeze_filter,
# 【L0101】给上一层函数/配置构造器的命名参数 `ema_decay` 传入 `None`；该参数在本项目中表示本功能块中的 `ema_decay` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        ema_decay=None,
# 【L0102】给上一层函数/配置构造器的命名参数 `batch_size` 传入 `batch_size`；该参数在本项目中表示本功能块中的 `batch_size` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        batch_size=batch_size,
# 【L0103】给上一层函数/配置构造器的命名参数 `num_workers` 传入 `0`；该参数在本项目中表示本功能块中的 `num_workers` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        num_workers=0,
# 【L0104】给上一层函数/配置构造器的命名参数 `num_train_steps` 传入 `num_train_steps`；该参数在本项目中表示步数相关值，会参与“基础权重、数据集、batch、步数和日志配置”。
        num_train_steps=num_train_steps,
# 【L0105】给上一层函数/配置构造器的命名参数 `wandb_enabled` 传入 `False`；该参数在本项目中表示本功能块中的 `wandb_enabled` 值，会参与“基础权重、数据集、batch、步数和日志配置”。
        wandb_enabled=False,
# 【L0106】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
    )
```
