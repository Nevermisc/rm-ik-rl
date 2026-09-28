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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state."""
# 【L0002】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0003】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0004】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0005】导入 dataclasses：标准库数据类工具，用较少样板代码声明配置/记录对象；后面的代码会调用其中的类或函数。
import dataclasses
# 【L0006】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0007】导入 einops：用可读模式重排数组维度；后面的代码会调用其中的类或函数。
import einops
# 【L0008】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0009】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0010】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi import transforms
# 【L0011】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi.models import model as _model
# 【L0012】空行：分隔“依赖”中的逻辑段，让结构更容易看清。

# 【L0013】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0014】定义函数 _parse_image；其职责属于“把输入图像统一成 H×W×3 的 uint8 RGB”，缩进块是函数体。
def _parse_image(image: np.ndarray) -> np.ndarray:
# 【L0015】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“把输入图像统一成 H×W×3 的 uint8 RGB”。
    image = np.asarray(image)
# 【L0016】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if np.issubdtype(image.dtype, np.floating):
# 【L0017】调用 `np.clip`：把数值限制在给定上下界内。本行位于“把输入图像统一成 H×W×3 的 uint8 RGB”。
        image = np.clip(255 * image, 0, 255).astype(np.uint8)
# 【L0018】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if image.shape[0] == 3:
# 【L0019】计算并保存变量 `image`；该值服务于“把输入图像统一成 H×W×3 的 uint8 RGB”。
        image = einops.rearrange(image, "c h w -> h w c")
# 【L0020】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if image.ndim != 3 or image.shape[-1] != 3:
# 【L0021】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"expected an RGB image, got {image.shape}")
# 【L0022】结束当前函数并把结果交给调用者；这里完成“把输入图像统一成 H×W×3 的 uint8 RGB”的输出。
    return image
# 【L0023】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0024】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】数据类装饰器：自动生成初始化等方法；frozen=True 表示创建后不允许改字段。
@dataclasses.dataclass(frozen=True)
# 【L0026】定义类 RM65Inputs；把相关配置、状态和方法组织成一个可复用对象。
class RM65Inputs(transforms.DataTransformFn):
# 【L0027】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Convert repository-level RM65 fields to the generic pi0.5 model fields."""
# 【L0028】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0029】执行“RM65Inputs：仓库字段→π0.5 字段”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    model_type: _model.ModelType
# 【L0030】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0031】定义函数 __call__；其职责属于“RM65Inputs：仓库字段→π0.5 字段”，缩进块是函数体。
    def __call__(self, data: dict) -> dict:
# 【L0032】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“RM65Inputs：仓库字段→π0.5 字段”。
        joints = np.asarray(data["observation/joint_position"])
# 【L0033】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“RM65Inputs：仓库字段→π0.5 字段”。
        gripper = np.asarray(data["observation/gripper_position"])
# 【L0034】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if joints.shape != (6,):
# 【L0035】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"expected six RM65 joints, got {joints.shape}")
# 【L0036】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if gripper.ndim == 0:
# 【L0037】给变量 `gripper` 赋值：一个归一化夹爪值组成的一维数组。
            gripper = gripper[np.newaxis]
# 【L0038】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if gripper.shape != (1,):
# 【L0039】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"expected one gripper value, got {gripper.shape}")
# 【L0040】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0041】计算并保存变量 `base_image`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
        base_image = _parse_image(data["observation/external_image"])
# 【L0042】计算并保存变量 `wrist_image`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
        wrist_image = _parse_image(data["observation/wrist_image"])
# 【L0043】开始按值进行结构化模式匹配。
        match self.model_type:
# 【L0044】结构化模式匹配分支；根据模型类型选择对应字段布局。
            case _model.ModelType.PI0 | _model.ModelType.PI05:
# 【L0045】计算并保存变量 `names`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
                names = ("base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb")
# 【L0046】计算并保存变量 `images`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
                images = (base_image, wrist_image, np.zeros_like(base_image))
# 【L0047】计算并保存变量 `image_masks`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
                image_masks = (np.True_, np.True_, np.False_)
# 【L0048】结构化模式匹配分支；根据模型类型选择对应字段布局。
            case _:
# 【L0049】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
                raise ValueError(f"unsupported model type for RM65: {self.model_type}")
# 【L0050】空行：分隔“RM65Inputs：仓库字段→π0.5 字段”中的逻辑段，让结构更容易看清。

# 【L0051】计算并保存变量 `result`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
        result = {
# 【L0052】调用 `np.concatenate`：沿一个轴首尾拼接数组。本行位于“RM65Inputs：仓库字段→π0.5 字段”。
            "state": np.concatenate([joints, gripper]),
# 【L0053】定义字典/JSON 字段 `image`；它把“RM65Inputs：仓库字段→π0.5 字段”中的结果用稳定键名记录下来。
            "image": dict(zip(names, images, strict=True)),
# 【L0054】定义字典/JSON 字段 `image_mask`；它把“RM65Inputs：仓库字段→π0.5 字段”中的结果用稳定键名记录下来。
            "image_mask": dict(zip(names, image_masks, strict=True)),
# 【L0055】结束或闭合当前语法结构；它属于“RM65Inputs：仓库字段→π0.5 字段”。
        }
# 【L0056】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if "actions" in data:
# 【L0057】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“RM65Inputs：仓库字段→π0.5 字段”。
            actions = np.asarray(data["actions"])
# 【L0058】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if actions.shape[-1] != 7:
# 【L0059】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
                raise ValueError(f"expected seven RM65 action values, got {actions.shape}")
# 【L0060】执行“RM65Inputs：仓库字段→π0.5 字段”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            result["actions"] = actions
# 【L0061】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if "prompt" in data:
# 【L0062】计算并保存变量 `prompt`；该值服务于“RM65Inputs：仓库字段→π0.5 字段”。
            prompt = data["prompt"]
# 【L0063】执行“RM65Inputs：仓库字段→π0.5 字段”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            result["prompt"] = prompt.decode("utf-8") if isinstance(prompt, bytes) else prompt
# 【L0064】结束当前函数并把结果交给调用者；这里完成“RM65Inputs：仓库字段→π0.5 字段”的输出。
        return result
# 【L0065】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0066】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0067】数据类装饰器：自动生成初始化等方法；frozen=True 表示创建后不允许改字段。
@dataclasses.dataclass(frozen=True)
# 【L0068】定义类 RM65Outputs；把相关配置、状态和方法组织成一个可复用对象。
class RM65Outputs(transforms.DataTransformFn):
# 【L0069】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Expose six absolute joint targets and one normalized gripper target."""
# 【L0070】空行：分隔“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”中的逻辑段，让结构更容易看清。

# 【L0071】定义函数 __call__；其职责属于“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”，缩进块是函数体。
    def __call__(self, data: dict) -> dict:
# 【L0072】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”。
        actions = np.asarray(data["actions"])
# 【L0073】结束当前函数并把结果交给调用者；这里完成“RM65Outputs：只暴露 6 个关节目标加 1 个夹爪目标”的输出。
        return {"actions": actions[..., :7]}
```
