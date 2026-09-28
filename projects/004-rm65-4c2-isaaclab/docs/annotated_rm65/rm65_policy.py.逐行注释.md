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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】说明字符串 `OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state."""
# 【L0002】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0003】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0004】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0005】从 `dataclasses` 引入 `dataclasses`。在这份程序里，`dataclasses` 用于标准库数据类工具，用较少样板代码声明配置/记录对象；后续出现这些名字时调用的是这里的外部能力。
import dataclasses
# 【L0006】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0007】从 `einops` 引入 `einops`。在这份程序里，`einops` 用于用可读模式重排数组维度；后续出现这些名字时调用的是这里的外部能力。
import einops
# 【L0008】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0009】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0010】从 `openpi` 引入 `transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi import transforms
# 【L0011】从 `openpi` 引入 `model as _model`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi.models import model as _model
# 【L0012】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0013】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0014】定义图像标准化函数。RM65 数据可能来自训练集或 Isaac 相机，这个函数保证两条路径得到同一种图像布局。
def _parse_image(image: np.ndarray) -> np.ndarray:
# 【L0015】把传入图像统一包装为 NumPy ndarray。若本来就是 ndarray 通常不复制；若是列表或其他兼容对象则转换，之后才能稳定使用 dtype、shape 和切片。
    image = np.asarray(image)
# 【L0016】检查图像元素类型是不是浮点数。浮点图常用 0～1，而 π0.5 的图像 transform 期望 uint8 0～255。
    if np.issubdtype(image.dtype, np.floating):
# 【L0017】把 0～1 浮点图乘 255，超出范围的值裁到 0～255，再转成 uint8；结果成为标准八位 RGB 像素。
        image = np.clip(255 * image, 0, 255).astype(np.uint8)
# 【L0018】若第一维长度为 3，就把输入视为通道优先的 C×H×W 图像；这常见于 PyTorch 数据。
    if image.shape[0] == 3:
# 【L0019】把通道优先 C×H×W 重排为图像库/OpenPI 使用的 H×W×C；这里 C 必须是 RGB 三通道。
        image = einops.rearrange(image, "c h w -> h w c")
# 【L0020】确认最终图像恰好是三维且最后一维为 3。它拒绝灰度图、RGBA 图和维度颠倒的数组。
    if image.ndim != 3 or image.shape[-1] != 3:
# 【L0021】图像结构不满足 RGB 合同时立即报错，并把实际 shape 写进错误，避免错误图像静默进入训练或推理。
        raise ValueError(f"expected an RGB image, got {image.shape}")
# 【L0022】返回格式统一后的 H×W×3 RGB ndarray，供 RM65Inputs 填入 π0.5 图像槽位。
    return image
# 【L0023】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0024】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】把 RM65Inputs 声明为不可变数据类；实例创建后 model_type 不会被意外修改。
@dataclasses.dataclass(frozen=True)
# 【L0026】定义 RM65 输入 transform，并继承 OpenPI 的 DataTransformFn 接口，因此训练和推理框架都能调用它。
class RM65Inputs(transforms.DataTransformFn):
# 【L0027】说明字符串 `Convert repository-level RM65 fields to the generic pi0.5 model fields.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Convert repository-level RM65 fields to the generic pi0.5 model fields."""
# 【L0028】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0029】保存当前使用的模型类型。后面只接受 PI0/PI05，因为不同模型可能要求不同图像键。
    model_type: _model.ModelType
# 【L0030】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0031】当 OpenPI 处理一条训练样本或一次推理请求时调用此方法；输入 data 是仓库层字段字典，返回 π0.5 通用字段字典。
    def __call__(self, data: dict) -> dict:
# 【L0032】从 data 读取 `observation/joint_position`，也就是当前六个 RM65 关节角，并统一为 NumPy 数组；之后用 shape 验证它确实对应六轴。
        joints = np.asarray(data["observation/joint_position"])
# 【L0033】从 data 读取归一化 4C2 夹爪位置并转为 NumPy 数组；它应该只包含一个值，0 张开、1 闭合。
        gripper = np.asarray(data["observation/gripper_position"])
# 【L0034】检查关节数组是不是一维六元素 `(6,)`；这同时保护关节数量和轴顺序合同。
        if joints.shape != (6,):
# 【L0035】如果不是六轴形状就停止，并报告实际 shape；不能靠截断或补零把 Franka 七轴动作冒充 RM65 动作。
            raise ValueError(f"expected six RM65 joints, got {joints.shape}")
# 【L0036】兼容调用方传入 Python 浮点或零维 ndarray 的情况；零维还不能与六关节数组直接拼接。
        if gripper.ndim == 0:
# 【L0037】用 `np.newaxis` 增加一个维度，把标量形状 `()` 变成单元素向量 `(1,)`。
            gripper = gripper[np.newaxis]
# 【L0038】确认夹爪最终形状严格为 `(1,)`，防止把多个 4C2 follower joint 当成多个策略自由度。
        if gripper.shape != (1,):
# 【L0039】夹爪结构错误时立即报错，并显示实际 shape。
            raise ValueError(f"expected one gripper value, got {gripper.shape}")
# 【L0040】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0041】读取外部相机图像并通过 `_parse_image` 统一为 H×W×3、uint8 RGB。
        base_image = _parse_image(data["observation/external_image"])
# 【L0042】读取腕部相机图像并执行同样的布局和像素类型标准化。
        wrist_image = _parse_image(data["observation/wrist_image"])
# 【L0043】根据 OpenPI 模型类型选择它所认识的图像槽位名称。
        match self.model_type:
# 【L0044】PI0 和 PI0.5 在本项目中共用三个命名图像槽位，因此进入同一分支。
            case _model.ModelType.PI0 | _model.ModelType.PI05:
# 【L0045】依次声明外部、左腕部、右腕部三个 π0.5 图像键；顺序必须与 images 和 image_masks 完全一致。
                names = ("base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb")
# 【L0046】把真实外部图、真实腕部图和一张同尺寸零图组成三元组；零图只是填满模型的第三个固定槽位。
                images = (base_image, wrist_image, np.zeros_like(base_image))
# 【L0047】前两个 mask 为 true，告诉模型这两张是真实观测；第三个为 false，因此零图不会被当成第二台腕部相机。
                image_masks = (np.True_, np.True_, np.False_)
# 【L0048】捕获 PI0/PI05 之外的模型类型。
            case _:
# 【L0049】遇到没有定义 RM65 图像布局的模型时拒绝继续，防止字段悄悄错位。
                raise ValueError(f"unsupported model type for RM65: {self.model_type}")
# 【L0050】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0051】开始构造 OpenPI/π0.5 真正接收的通用输入字典。
        result = {
# 【L0052】把六关节向量 `(6,)` 和夹爪向量 `(1,)` 首尾拼成七维 `state`；模型据此知道当前 RM65+4C2 状态。
            "state": np.concatenate([joints, gripper]),
# 【L0053】用 `zip` 将三个槽位名与三张图一一配对并转成字典；`strict=True` 会在数量不一致时报错。
            "image": dict(zip(names, images, strict=True)),
# 【L0054】同样把槽位名与三个布尔 mask 配对，明确哪些图像有效。
            "image_mask": dict(zip(names, image_masks, strict=True)),
# 【L0055】结束或闭合当前语法结构；它属于“RM65Inputs：仓库字段→π0.5 字段”。
        }
# 【L0056】训练样本包含教师动作，而在线推理请求通常不包含；只有存在 actions 时才处理监督标签。
        if "actions" in data:
# 【L0057】从 data 取出当前训练样本的未来 RM65 动作序列。每步含六个绝对关节目标和一个归一化夹爪目标；`np.asarray` 将列表或其他数组对象统一成 ndarray，便于检查维度并交给后续 delta-action/训练 transform。
            actions = np.asarray(data["actions"])
# 【L0058】检查动作最后一维是否为 7。前面的维度可以是单步或时间 horizon，但每步语义必须固定为 6+1。
            if actions.shape[-1] != 7:
# 【L0059】动作不是七维就报错；这会捕获误用 Franka `(T,8)` 标签或缺少夹爪列的情况。
                raise ValueError(f"expected seven RM65 action values, got {actions.shape}")
# 【L0060】把验证过的动作序列加入通用结果；训练时它随后会经过 DeltaActions 和归一化，推理请求没有这一键。
            result["actions"] = actions
# 【L0061】语言指令是可选字段；存在时才交给 π0.5 的 tokenizer。
        if "prompt" in data:
# 【L0062】从 data 读取 prompt；它描述本帧所属任务，例如抓起方块并放到目标。
            prompt = data["prompt"]
# 【L0063】若数据加载器给出 bytes 就按 UTF-8 解码，否则保留原字符串，保证 tokenizer 最终收到 str。
            result["prompt"] = prompt.decode("utf-8") if isinstance(prompt, bytes) else prompt
# 【L0064】返回已经转换好的 state、image、image_mask，以及可选 actions/prompt，进入 OpenPI 后续归一化和模型处理。
        return result
# 【L0065】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0066】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0067】把输出 transform 声明为不可变数据类；它本身没有需要配置的字段。
@dataclasses.dataclass(frozen=True)
# 【L0068】定义 π0.5 输出到 RM65 动作合同的最后一道 transform。
class RM65Outputs(transforms.DataTransformFn):
# 【L0069】说明字符串 `Expose six absolute joint targets and one normalized gripper target.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Expose six absolute joint targets and one normalized gripper target."""
# 【L0070】空行：分隔“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”中的逻辑段，让结构更容易看清。

# 【L0071】OpenPI 在反归一化和 absolute-action 恢复之后调用此方法。
    def __call__(self, data: dict) -> dict:
# 【L0072】从 OpenPI 输出字典取出动作块并统一为 ndarray；形状通常是 `(10, action_dim)`。
        actions = np.asarray(data["actions"])
# 【L0073】保留每个时间步前七维并以 `actions` 键返回，即六个 RM65 绝对关节目标加一个 4C2 夹爪目标。
        return {"actions": actions[..., :7]}
```
