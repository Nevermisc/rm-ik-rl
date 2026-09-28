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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""OpenPI data and LoRA training configuration for RM65-B + 4C2."""
# 【L0002】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0003】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0004】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0005】导入 dataclasses：标准库数据类工具，用较少样板代码声明配置/记录对象；后面的代码会调用其中的类或函数。
import dataclasses
# 【L0006】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
import pathlib
# 【L0007】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0008】导入 flax：项目或第三方模块；后面的代码会调用其中的类或函数。
import flax.nnx as nnx
# 【L0009】导入 typing_extensions：项目或第三方模块；后面的代码会调用其中的类或函数。
from typing_extensions import override
# 【L0010】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0011】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.models import model as _model
# 【L0012】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.models import pi0_config
# 【L0013】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.shared import nnx_utils
# 【L0014】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.training import config as training_config
# 【L0015】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.training import weight_loaders
# 【L0016】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
import openpi.transforms as transforms
# 【L0017】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0018】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.rm65_policy import RM65Inputs, RM65Outputs
# 【L0019】空行：分隔“OpenPI/Flax 训练组件与 RM65 transform”中的逻辑段，让结构更容易看清。

# 【L0020】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0021】数据类装饰器：自动生成初始化等方法；frozen=True 表示创建后不允许改字段。
@dataclasses.dataclass(frozen=True)
# 【L0022】定义类 LeRobotRM65DataConfig；把相关配置、状态和方法组织成一个可复用对象。
class LeRobotRM65DataConfig(training_config.DataConfigFactory):
# 【L0023】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Map the RM65 LeRobot schema to the shared inference-time transform."""
# 【L0024】空行：分隔“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的逻辑段，让结构更容易看清。

# 【L0025】装饰器：在函数或类创建时附加框架行为。
    @override
# 【L0026】定义函数 create；其职责属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”，缩进块是函数体。
    def create(
# 【L0027】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        self,
# 【L0028】调用 `Path`：创建路径对象。本行位于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        assets_dirs: pathlib.Path,
# 【L0029】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        model_config: _model.BaseModelConfig,
# 【L0030】开始一个缩进代码块或键值结构；该块负责“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
    ) -> training_config.DataConfig:
# 【L0031】计算并保存变量 `repack`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        repack = transforms.Group(
# 【L0032】计算并保存变量 `inputs`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[
# 【L0033】执行“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                transforms.RepackTransform(
# 【L0034】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    {
# 【L0035】定义字典/JSON 字段 `observation/external_image`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "observation/external_image": "image",
# 【L0036】定义字典/JSON 字段 `observation/wrist_image`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "observation/wrist_image": "wrist_image",
# 【L0037】定义字典/JSON 字段 `observation/joint_position`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "observation/joint_position": "joints",
# 【L0038】定义字典/JSON 字段 `observation/gripper_position`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "observation/gripper_position": "gripper",
# 【L0039】定义字典/JSON 字段 `actions`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "actions": "actions",
# 【L0040】定义字典/JSON 字段 `prompt`；它把“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”中的结果用稳定键名记录下来。
                        "prompt": "prompt",
# 【L0041】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                    }
# 【L0042】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
                )
# 【L0043】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            ]
# 【L0044】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0045】计算并保存变量 `data_transforms`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        data_transforms = transforms.Group(
# 【L0046】计算并保存变量 `inputs`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[RM65Inputs(model_type=model_config.model_type)],
# 【L0047】计算并保存变量 `outputs`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[RM65Outputs()],
# 【L0048】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0049】源码注释：The scripted expert stores absolute joint targets. OpenPI trains joint
        # The scripted expert stores absolute joint targets. OpenPI trains joint
# 【L0050】源码注释：dimensions as deltas from the current state and keeps the gripper
        # dimensions as deltas from the current state and keeps the gripper
# 【L0051】源码注释：target absolute.
        # target absolute.
# 【L0052】计算并保存变量 `delta_action_mask`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        delta_action_mask = transforms.make_bool_mask(6, -1)
# 【L0053】计算并保存变量 `data_transforms`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        data_transforms = data_transforms.push(
# 【L0054】计算并保存变量 `inputs`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            inputs=[transforms.DeltaActions(delta_action_mask)],
# 【L0055】计算并保存变量 `outputs`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            outputs=[transforms.AbsoluteActions(delta_action_mask)],
# 【L0056】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0057】结束当前函数并把结果交给调用者；这里完成“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”的输出。
        return dataclasses.replace(
# 【L0058】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            self.create_base_config(assets_dirs, model_config),
# 【L0059】计算并保存变量 `repack_transforms`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            repack_transforms=repack,
# 【L0060】计算并保存变量 `data_transforms`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            data_transforms=data_transforms,
# 【L0061】计算并保存变量 `model_transforms`；该值服务于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
            model_transforms=training_config.ModelTransformFactory()(model_config),
# 【L0062】结束或闭合当前语法结构；它属于“LeRobot 字段重排、RM65 输入输出变换和动作 delta 规则”。
        )
# 【L0063】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0064】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0065】定义函数 make_pi05_rm65_lora_config；其职责属于“创建 π0.5、10 步动作 horizon 和两组 LoRA”，缩进块是函数体。
def make_pi05_rm65_lora_config(
# 【L0066】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    *,
# 【L0067】计算并保存变量 `repo_id`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    repo_id: str = "local/rm65_sim",
# 【L0068】计算并保存变量 `batch_size`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    batch_size: int = 1,
# 【L0069】计算并保存变量 `num_train_steps`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    num_train_steps: int = 30_000,
# 【L0070】开始一个缩进代码块或键值结构；该块负责“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
) -> training_config.TrainConfig:
# 【L0071】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Build, without globally registering, the RM65 π0.5 LoRA config."""
# 【L0072】空行：分隔“创建 π0.5、10 步动作 horizon 和两组 LoRA”中的逻辑段，让结构更容易看清。

# 【L0073】计算并保存变量 `model`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    model = pi0_config.Pi0Config(
# 【L0074】计算并保存变量 `pi05`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        pi05=True,
# 【L0075】计算并保存变量 `action_horizon`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_horizon=10,
# 【L0076】源码注释：The RM65 task prompts are short. A 64-token ceiling retains ample
        # The RM65 task prompts are short. A 64-token ceiling retains ample
# 【L0077】源码注释：margin while avoiding 136 unused language positions per sample.
        # margin while avoiding 136 unused language positions per sample.
# 【L0078】计算并保存变量 `max_token_len`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        max_token_len=64,
# 【L0079】计算并保存变量 `discrete_state_input`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        discrete_state_input=False,
# 【L0080】计算并保存变量 `paligemma_variant`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        paligemma_variant="gemma_2b_lora",
# 【L0081】计算并保存变量 `action_expert_variant`；该值服务于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
        action_expert_variant="gemma_300m_lora",
# 【L0082】结束或闭合当前语法结构；它属于“创建 π0.5、10 步动作 horizon 和两组 LoRA”。
    )
# 【L0083】源码注释：The 16 GB lab GPU cannot train the SigLIP image tower together with both
    # The 16 GB lab GPU cannot train the SigLIP image tower together with both
# 【L0084】源码注释：LoRA adapters. Keeping the pretrained visual encoder fixed is also the
    # LoRA adapters. Keeping the pretrained visual encoder fixed is also the
# 【L0085】源码注释：intended transfer-learning regime for this small simulated dataset.
    # intended transfer-learning regime for this small simulated dataset.
# 【L0086】计算并保存变量 `freeze_filter`；该值服务于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
    freeze_filter = nnx.Any(
# 【L0087】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
        model.get_freeze_filter(),
# 【L0088】调用 `Path`：创建路径对象。本行位于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
        nnx_utils.PathRegex(".*img.*"),
# 【L0089】结束或闭合当前语法结构；它属于“冻结图像编码器以适配 16 GB GPU 和小数据集”。
    )
# 【L0090】结束当前函数并把结果交给调用者；这里完成“基础权重、数据集、batch、步数和日志配置”的输出。
    return training_config.TrainConfig(
# 【L0091】计算并保存变量 `name`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        name="pi05_rm65_lora",
# 【L0092】计算并保存变量 `model`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        model=model,
# 【L0093】计算并保存变量 `data`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        data=LeRobotRM65DataConfig(
# 【L0094】计算并保存变量 `repo_id`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
            repo_id=repo_id,
# 【L0095】计算并保存变量 `base_config`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
            base_config=training_config.DataConfig(prompt_from_task=True),
# 【L0096】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0097】计算并保存变量 `weight_loader`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        weight_loader=weight_loaders.CheckpointWeightLoader(
# 【L0098】执行“基础权重、数据集、batch、步数和日志配置”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "gs://openpi-assets/checkpoints/pi05_base/params"
# 【L0099】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
        ),
# 【L0100】计算并保存变量 `freeze_filter`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        freeze_filter=freeze_filter,
# 【L0101】计算并保存变量 `ema_decay`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        ema_decay=None,
# 【L0102】计算并保存变量 `batch_size`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        batch_size=batch_size,
# 【L0103】计算并保存变量 `num_workers`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        num_workers=0,
# 【L0104】计算并保存变量 `num_train_steps`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        num_train_steps=num_train_steps,
# 【L0105】计算并保存变量 `wandb_enabled`；该值服务于“基础权重、数据集、batch、步数和日志配置”。
        wandb_enabled=False,
# 【L0106】结束或闭合当前语法结构；它属于“基础权重、数据集、batch、步数和日志配置”。
    )
```
