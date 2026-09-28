# `convert_expert_episodes_to_lerobot.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/convert_expert_episodes_to_lerobot.py`
- 快照 SHA-256：`508752a43b97645d9d83b152ef28f93ba344933827ad589d6ab9e4d0861583f1`
- 总行数：255
- 程序作用：把便于调试的本地 episode 格式转换成 OpenPI 能训练的 LeRobot 数据集。
- 推荐读法：重点跟踪同一帧如何从 episode.npz/images 变成 image、wrist_image、joints、gripper、actions、task。

## 功能块地图

- 第 1-20 行：依赖、项目路径和校验函数
- 第 23-47 行：读取且只接收成功、图像完整的 episode
- 第 50-91 行：可选策略窗口：减少大量静止标签
- 第 94-96 行：读取 RGB PNG
- 第 99-135 行：发现所有 episode 并检查帧率、维度和相机尺寸一致
- 第 138-180 行：命令行、选择 split、定位 LeRobot 输出目录
- 第 182-206 行：声明 LeRobot 数据集 schema
- 第 207-232 行：逐 episode、逐帧写入数据集
- 第 234-255 行：输出转换统计与脚本退出码

## 函数/类索引

- `load_episode()`：第 23-47 行
- `select_policy_window_indices()`：第 50-91 行
- `read_rgb()`：第 94-96 行
- `discover_episodes()`：第 99-135 行
- `main()`：第 138-251 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Convert successful, image-complete RM65 episodes to OpenPI's LeRobot schema."""
# 【L0003】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】从 `shutil` 引入 `shutil`。在这份程序里，`shutil` 用于标准库文件目录操作；后续出现这些名字时调用的是这里的外部能力。
import shutil
# 【L0009】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】从 `typing` 引入 `Any`。在这份程序里，`typing` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from typing import Any
# 【L0012】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0013】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0014】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
from PIL import Image
# 【L0015】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0016】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“依赖、项目路径和校验函数”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】空行：分隔“依赖、项目路径和校验函数”中的逻辑段，让结构更容易看清。

# 【L0020】从 `openpi_extension` 引入 `validate_episode`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import validate_episode
# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】定义函数 `load_episode(directory: Path)`；调用者把参数交给它完成“读取且只接收成功、图像完整的 episode”，后面的缩进代码是具体实现。
def load_episode(directory: Path) -> dict[str, Any]:
# 【L0024】说明字符串 `Load and validate one successful episode without requiring LeRobot.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Load and validate one successful episode without requiring LeRobot."""
# 【L0025】空行：分隔“读取且只接收成功、图像完整的 episode”中的逻辑段，让结构更容易看清。

# 【L0026】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(directory, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`require_images` 表示本功能块中的 `require_images` 值。
    validation = validate_episode(directory, require_images=True)
# 【L0027】判断 `validation["status"] != "pass"` 是否成立；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
    if validation["status"] != "pass":
# 【L0028】主动抛出 `ValueError(f"invalid episode {directory}: {validation['errors']}")` 并停止当前路径；说明当前输入违反“读取且只接收成功、图像完整的 episode”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"invalid episode {directory}: {validation['errors']}")
# 【L0029】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取 JSON 文本并还原成 Python 字典，后续按固定键检查计划、metadata 或报告。
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
# 【L0030】判断 `manifest.get("metadata", {}).get("task_success") is not True` 是否成立；`manifest` 表示描述磁盘数据含义、数量和路径的元数据清单；`get` 表示本功能块中的 `get` 值；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息
    if manifest.get("metadata", {}).get("task_success") is not True:
# 【L0031】主动抛出 `ValueError(f"episode is not marked successful: {directory}")` 并停止当前路径；说明当前输入违反“读取且只接收成功、图像完整的 episode”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episode is not marked successful: {directory}")
# 【L0032】进入资源上下文 `np.load(directory / "episode.npz") as arrays`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with np.load(directory / "episode.npz") as arrays:
# 【L0033】得到 `states`，它在本项目中表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["observation_state"].astype(np.float32, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`observation_state` 表示状态相关值；`astype` 表示本功能块中的 `astype` 值。
        states = arrays["observation_state"].astype(np.float32, copy=True)
# 【L0034】得到 `actions`，它在本项目中表示一个动作块；形状通常为 (时间步数, 7)；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["action"].astype(np.float32, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`action` 表示动作相关值；`astype` 表示本功能块中的 `astype` 值。
        actions = arrays["action"].astype(np.float32, copy=True)
# 【L0035】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arrays["phase_id"].astype(np.int64, copy=True)`；`arrays` 表示本功能块中的 `arrays` 值；`phase_id` 表示本功能块中的 `phase_id` 值；`astype` 表示本功能块中的 `astype` 值。
        phase_ids = arrays["phase_id"].astype(np.int64, copy=True)
# 【L0036】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0037】定义字典/JSON 字段 `directory`，它表示“读取且只接收成功、图像完整的 episode”中的 `directory` 数据；字段值来自 `directory`，因此保存/传递的是这个表达式当前计算出的结果。
        "directory": directory,
# 【L0038】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `manifest["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": manifest["prompt"],
# 【L0039】定义字典/JSON 字段 `fps`，它表示“读取且只接收成功、图像完整的 episode”中的 `fps` 数据；字段值来自 `float(manifest["control_hz"])`，因此保存/传递的是这个表达式当前计算出的结果。
        "fps": float(manifest["control_hz"]),
# 【L0040】定义字典/JSON 字段 `states`，它表示“读取且只接收成功、图像完整的 episode”中的 `states` 数据；字段值来自 `states`，因此保存/传递的是这个表达式当前计算出的结果。
        "states": states,
# 【L0041】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `actions`，因此保存/传递的是这个表达式当前计算出的结果。
        "actions": actions,
# 【L0042】定义字典/JSON 字段 `phase_ids`，它表示“读取且只接收成功、图像完整的 episode”中的 `phase_ids` 数据；字段值来自 `phase_ids`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_ids": phase_ids,
# 【L0043】定义字典/JSON 字段 `phase_names`，它表示“读取且只接收成功、图像完整的 episode”中的 `phase_names` 数据；字段值来自 `manifest["phase_names"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "phase_names": manifest["phase_names"],
# 【L0044】定义字典/JSON 字段 `external_paths`，它表示“读取且只接收成功、图像完整的 episode”中的 `external_paths` 数据；字段值来自 `manifest["image_paths"]["external"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "external_paths": manifest["image_paths"]["external"],
# 【L0045】定义字典/JSON 字段 `wrist_paths`，它表示“读取且只接收成功、图像完整的 episode”中的 `wrist_paths` 数据；字段值来自 `manifest["image_paths"]["wrist"]`，因此保存/传递的是这个表达式当前计算出的结果。
        "wrist_paths": manifest["image_paths"]["wrist"],
# 【L0046】定义字典/JSON 字段 `collection_split`，它表示“读取且只接收成功、图像完整的 episode”中的 `collection_split` 数据；字段值来自 `manifest.get("metadata", {}).get("collection_split")`，因此保存/传递的是这个表达式当前计算出的结果。
        "collection_split": manifest.get("metadata", {}).get("collection_split"),
# 【L0047】结束或闭合当前语法结构；它属于“读取且只接收成功、图像完整的 episode”。
    }
# 【L0048】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0049】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0050】定义函数 `select_policy_window_indices(episode: dict[str, Any])`；调用者把参数交给它完成“可选策略窗口：减少大量静止标签”，后面的缩进代码是具体实现。
def select_policy_window_indices(episode: dict[str, Any]) -> np.ndarray:
# 【L0051】说明字符串 `Keep control-relevant motion while reducing ambiguous stationary labels.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Keep control-relevant motion while reducing ambiguous stationary labels.
# 【L0052】继续说明字符串，原文是 ``；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0053】继续说明字符串，原文是 `The full portable episode remains unchanged. This optional view retains the`；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    The full portable episode remains unchanged. This optional view retains the
# 【L0054】继续说明字符串，原文是 `last two frames of pre-transition holds, the first 15 release-settle frames,`；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    last two frames of pre-transition holds, the first 15 release-settle frames,
# 【L0055】继续说明字符串，原文是 `and every motion frame through release. Retreat and final-settle frames are`；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    and every motion frame through release. Retreat and final-settle frames are
# 【L0056】继续说明字符串，原文是 `omitted because the closed-loop success detector stops after stable release.`；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    omitted because the closed-loop success detector stops after stable release.
# 【L0057】继续说明字符串，原文是 ``；这段文字在解释“可选策略窗口：减少大量静止标签”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0058】空行：分隔“可选策略窗口：减少大量静止标签”中的逻辑段，让结构更容易看清。

# 【L0059】得到 `phase_ids`，它在本项目中表示每一帧所处专家阶段的整数编号；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `episode["phase_ids"], dtype=np.int64`（一条轨迹相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    phase_ids = np.asarray(episode["phase_ids"], dtype=np.int64)
# 【L0060】得到 `phase_names`，它在本项目中表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode["phase_names"]`；`episode` 表示一条轨迹相关值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射。
    phase_names = episode["phase_names"]
# 【L0061】得到 `phases`，它在本项目中表示本功能块中的 `phases` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `[phase_names[int(index)] for index in phase_ids], dtype=object`（本功能块中的 `` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    phases = np.asarray([phase_names[int(index)] for index in phase_ids], dtype=object)
# 【L0062】得到 `motion_mask`，它在本项目中表示掩码相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    motion_mask = np.array(
# 【L0063】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“可选策略窗口：减少大量静止标签”。
        [
# 【L0064】对 `phase` 调用 `startswith("APPROACH_")`：调用 `phase` 提供的 `startswith` 操作。本行产生的修改/返回值服务于“可选策略窗口：减少大量静止标签”。
            phase.startswith("APPROACH_")
# 【L0065】对 `or phase` 调用 `startswith("PLACE_DESCENT_")`：调用 `or phase` 提供的 `startswith` 操作。本行产生的修改/返回值服务于“可选策略窗口：减少大量静止标签”。
            or phase.startswith("PLACE_DESCENT_")
# 【L0066】把条件 `phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}` 用“或者”接到上一行判断中；判断 `phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}` 是否成立；`phase` 表示本功能块中的 `phase` 值；`CLOSE` 表示本功能块中的 `CLOSE` 值；`LIFT` 表示本功能块中的 `LIFT` 值。所有连接条件共同决定是否进入后续分支。
            or phase in {"CLOSE", "LIFT", "TRANSFER", "OPEN"}
# 【L0067】开始遍历 `for phase in phases` 中给出的序列，逐项完成“可选策略窗口：减少大量静止标签”。
            for phase in phases
# 【L0068】结束或闭合当前语法结构；它属于“可选策略窗口：减少大量静止标签”。
        ],
# 【L0069】给上一层函数/配置构造器的命名参数 `dtype` 传入 `bool`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“可选策略窗口：减少大量静止标签”。
        dtype=bool,
# 【L0070】结束或闭合当前语法结构；它属于“可选策略窗口：减少大量静止标签”。
    )
# 【L0071】得到 `selected`，它在本项目中表示本功能块中的 `selected` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `set(np.flatnonzero(motion_mask).tolist())`；`set` 表示本功能块中的 `set` 值；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`motion_mask` 表示掩码相关值。
    selected = set(np.flatnonzero(motion_mask).tolist())
# 【L0072】开始遍历 `for phase in (` 中给出的序列，逐项完成“可选策略窗口：减少大量静止标签”。
    for phase in (
# 【L0073】提供文本片段 `"SOURCE_SETTLE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "SOURCE_SETTLE",
# 【L0074】提供文本片段 `"GRASP_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "GRASP_HOLD",
# 【L0075】提供文本片段 `"CLOSE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "CLOSE_HOLD",
# 【L0076】提供文本片段 `"LIFT_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "LIFT_HOLD",
# 【L0077】提供文本片段 `"TARGET_COLLISION_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "TARGET_COLLISION_HOLD",
# 【L0078】提供文本片段 `"PLACE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“可选策略窗口：减少大量静止标签”中的帮助说明、错误原因、任务名称或报告文字。
        "PLACE_HOLD",
# 【L0079】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“可选策略窗口：减少大量静止标签”。
    ):
# 【L0080】得到 `indices`，它在本项目中表示当前 episode 中会被写入目标数据集的帧索引；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.flatnonzero(phases == phase)`；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`phases` 表示本功能块中的 `phases` 值；`phase` 表示本功能块中的 `phase` 值。
        indices = np.flatnonzero(phases == phase)
# 【L0081】对 `selected` 执行 `update`，把 `indices[-2:].tolist()` 加入已有结果；该集合表示本功能块中的 `selected` 值，随后会用于“可选策略窗口：减少大量静止标签”。
        selected.update(indices[-2:].tolist())
# 【L0082】得到 `release_indices`，它在本项目中表示本功能块中的 `release_indices` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.flatnonzero(phases == "RELEASE_SETTLE")`；`flatnonzero` 表示本功能块中的 `flatnonzero` 值；`phases` 表示本功能块中的 `phases` 值；`RELEASE_SETTLE` 表示本功能块中的 `RELEASE_SETTLE` 值。
    release_indices = np.flatnonzero(phases == "RELEASE_SETTLE")
# 【L0083】对 `selected` 执行 `update`，把 `release_indices[:15].tolist()` 加入已有结果；该集合表示本功能块中的 `selected` 值，随后会用于“可选策略窗口：减少大量静止标签”。
    selected.update(release_indices[:15].tolist())
# 【L0084】得到 `result`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `sorted(selected), dtype=np.int64`（本功能块中的 `sorted(selected), dtype=np.int64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    result = np.asarray(sorted(selected), dtype=np.int64)
# 【L0085】判断 `len(result) == 0` 是否成立；`result` 表示结果相关值
    if len(result) == 0:
# 【L0086】主动抛出 `ValueError(f"episode contains no recognized policy phases: {episode['directory']}")` 并停止当前路径；说明当前输入违反“可选策略窗口：减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episode contains no recognized policy phases: {episode['directory']}")
# 【L0087】判断 `phases[result[0]] != "SOURCE_SETTLE"` 是否成立；`phases` 表示本功能块中的 `phases` 值；`result` 表示结果相关值；`SOURCE_SETTLE` 表示源位置方块/平台的任务常量
    if phases[result[0]] != "SOURCE_SETTLE":
# 【L0088】主动抛出 `ValueError("policy window must begin with a SOURCE_SETTLE transition frame")` 并停止当前路径；说明当前输入违反“可选策略窗口：减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy window must begin with a SOURCE_SETTLE transition frame")
# 【L0089】判断 `"OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]` 是否成立；`OPEN` 表示本功能块中的 `OPEN` 值；`phases` 表示本功能块中的 `phases` 值；`result` 表示结果相关值
    if "OPEN" not in phases[result] or "RELEASE_SETTLE" not in phases[result]:
# 【L0090】主动抛出 `ValueError("policy window must contain OPEN and RELEASE_SETTLE")` 并停止当前路径；说明当前输入违反“可选策略窗口：减少大量静止标签”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy window must contain OPEN and RELEASE_SETTLE")
# 【L0091】结束当前函数并把 `result` 交回调用者；这个值的含义是：计算表达式 `result`；`result` 表示结果相关值。
    return result
# 【L0092】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0093】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0094】定义函数 `read_rgb(path: Path)`；调用者把参数交给它完成“读取 RGB PNG”，后面的缩进代码是具体实现。
def read_rgb(path: Path) -> np.ndarray:
# 【L0095】进入资源上下文 `Image.open(path) as image`；执行完缩进块后自动关闭对应文件、数组映射或网络资源，避免数据未落盘。
    with Image.open(path) as image:
# 【L0096】结束当前函数并把 `np.asarray(image.convert("RGB"), dtype=np.uint8)` 交回调用者；这个值的含义是：读取/计算 `image.convert("RGB"), dtype=np.uint8`（本功能块中的 `image.convert("RGB"), dtype=np.uint8` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
# 【L0097】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0098】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0099】定义函数 `discover_episodes(参数在后续行继续)`；调用者把参数交给它完成“发现所有 episode 并检查帧率、维度和相机尺寸一致”，后面的缩进代码是具体实现。
def discover_episodes(
# 【L0100】得到 `dataset_root`，它在本项目中表示数据集相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    dataset_root: Path, *, collection_split: str | None = None
# 【L0101】以 `) -> list[dict[str, Any]]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
) -> list[dict[str, Any]]:
# 【L0102】得到 `directories`，它在本项目中表示本功能块中的 `directories` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sorted(`；`sorted` 表示本功能块中的 `sorted` 值。
    directories = sorted(
# 【L0103】对 `path.parent for path in dataset_root` 调用 `glob("episode_*/metadata.json")`：调用 `path.parent for path in dataset_root` 提供的 `glob` 操作。本行产生的修改/返回值服务于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        path.parent for path in dataset_root.glob("episode_*/metadata.json")
# 【L0104】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
    )
# 【L0105】判断 `not directories` 是否成立；`directories` 表示本功能块中的 `directories` 值
    if not directories:
# 【L0106】主动抛出 `FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(f"no episode_*/metadata.json found below {dataset_root}")
# 【L0107】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[load_episode(directory) for directory in directories]`；`load_episode` 表示一条轨迹相关值；`directory` 表示目录相关值；`directories` 表示本功能块中的 `directories` 值。
    episodes = [load_episode(directory) for directory in directories]
# 【L0108】检查 `collection_split is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if collection_split is not None:
# 【L0109】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        episodes = [
# 【L0110】声明/传入参数 `episode`；在本项目中它表示一条轨迹相关值。
            episode
# 【L0111】开始遍历 `for episode in episodes` 中给出的序列，逐项完成“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
            for episode in episodes
# 【L0112】判断 `episode["collection_split"] == collection_split` 是否成立；`episode` 表示一条轨迹相关值；`collection_split` 表示本功能块中的 `collection_split` 值
            if episode["collection_split"] == collection_split
# 【L0113】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
        ]
# 【L0114】判断 `not episodes` 是否成立；`episodes` 表示本功能块中的 `episodes` 值
        if not episodes:
# 【L0115】主动抛出 `ValueError(` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(
# 【L0116】把表达式/参数 `f"no episodes use collection split {collection_split!r}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`no` 表示本功能块中的 `no` 值；`episodes` 表示本功能块中的 `episodes` 值。在“发现所有 episode 并检查帧率、维度和相机尺寸一致”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"no episodes use collection split {collection_split!r}"
# 【L0117】结束或闭合当前语法结构；它属于“发现所有 episode 并检查帧率、维度和相机尺寸一致”。
            )
# 【L0118】得到 `fps_values`，它在本项目中表示本功能块中的 `fps_values` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{round(item["fps"], 9) for item in episodes}`；`round` 表示本功能块中的 `round` 值；`item` 表示本功能块中的 `item` 值；`fps` 表示本功能块中的 `fps` 值。
    fps_values = {round(item["fps"], 9) for item in episodes}
# 【L0119】判断 `len(fps_values) != 1` 是否成立；`fps_values` 表示本功能块中的 `fps_values` 值
    if len(fps_values) != 1:
# 【L0120】主动抛出 `ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"episodes use different control frequencies: {sorted(fps_values)}")
# 【L0121】得到 `first`，它在本项目中表示本功能块中的 `first` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]`；`episodes` 表示本功能块中的 `episodes` 值。
    first = episodes[0]
# 【L0122】得到 `first_external`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    first_external = read_rgb(first["directory"] / first["external_paths"][0])
# 【L0123】得到 `first_wrist`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    first_wrist = read_rgb(first["directory"] / first["wrist_paths"][0])
# 【L0124】遍历 `episodes`，每次把当前元素放进 `episode`；这会逐个处理“发现所有 episode 并检查帧率、维度和相机尺寸一致”所需的帧、episode、动作或实验 case。
    for episode in episodes:
# 【L0125】判断 `episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,)` 是否成立；`episode` 表示一条轨迹相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪；`shape` 表示本功能块中的 `shape` 值
        if episode["states"].shape[1:] != (7,) or episode["actions"].shape[1:] != (7,):
# 【L0126】主动抛出 `ValueError(f"unexpected state/action dimensions in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"unexpected state/action dimensions in {episode['directory']}")
# 【L0127】判断 `len(episode["external_paths"]) != len(episode["states"])` 是否成立；`episode` 表示一条轨迹相关值；`external_paths` 表示外部相机相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪
        if len(episode["external_paths"]) != len(episode["states"]):
# 【L0128】主动抛出 `ValueError(f"external image count changed in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"external image count changed in {episode['directory']}")
# 【L0129】判断 `len(episode["wrist_paths"]) != len(episode["states"])` 是否成立；`episode` 表示一条轨迹相关值；`wrist_paths` 表示腕部相机相关值；`states` 表示episode 中全部七维观测状态，列为六关节角加归一化夹爪
        if len(episode["wrist_paths"]) != len(episode["states"]):
# 【L0130】主动抛出 `ValueError(f"wrist image count changed in {episode['directory']}")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"wrist image count changed in {episode['directory']}")
# 【L0131】得到 `external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        external_shape = read_rgb(episode["directory"] / episode["external_paths"][0]).shape
# 【L0132】得到 `wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
        wrist_shape = read_rgb(episode["directory"] / episode["wrist_paths"][0]).shape
# 【L0133】判断 `external_shape != first_external.shape or wrist_shape != first_wrist.shape` 是否成立；`external_shape` 表示外部相机相关值；`first_external` 表示外部相机相关值；`shape` 表示本功能块中的 `shape` 值
        if external_shape != first_external.shape or wrist_shape != first_wrist.shape:
# 【L0134】主动抛出 `ValueError("camera shapes must remain constant across all episodes")` 并停止当前路径；说明当前输入违反“发现所有 episode 并检查帧率、维度和相机尺寸一致”要求，不能继续进入仿真、训练或评测。
            raise ValueError("camera shapes must remain constant across all episodes")
# 【L0135】结束当前函数并把 `episodes` 交回调用者；这个值的含义是：计算表达式 `episodes`；`episodes` 表示本功能块中的 `episodes` 值。
    return episodes
# 【L0136】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0137】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0138】定义函数 `main()`；调用者把参数交给它完成“命令行、选择 split、定位 LeRobot 输出目录”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0139】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0140】声明命令行参数 `parser.add_argument("dataset_root", type=Path)`；启动脚本可用它改变“命令行、选择 split、定位 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("dataset_root", type=Path)
# 【L0141】声明命令行参数 `--repo-id`；启动脚本可用它改变“命令行、选择 split、定位 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", required=True, help="LeRobot repository id, e.g. local/rm65_sim")
# 【L0142】声明命令行参数 `--overwrite`；启动脚本可用它改变“命令行、选择 split、定位 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--overwrite", action="store_true")
# 【L0143】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行、选择 split、定位 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0144】提供文本片段 `"--split"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行、选择 split、定位 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
        "--split",
# 【L0145】给上一层函数/配置构造器的命名参数 `choices` 传入 `("train", "validation")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行、选择 split、定位 LeRobot 输出目录”。
        choices=("train", "validation"),
# 【L0146】给上一层函数/配置构造器的命名参数 `help` 传入 `"Convert only the declared collection split."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行、选择 split、定位 LeRobot 输出目录”。
        help="Convert only the declared collection split.",
# 【L0147】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0148】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行、选择 split、定位 LeRobot 输出目录”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0149】提供文本片段 `"--policy-window"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行、选择 split、定位 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
        "--policy-window",
# 【L0150】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行、选择 split、定位 LeRobot 输出目录”。
        action="store_true",
# 【L0151】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        help=(
# 【L0152】提供路径/资源标识 `"Compress stationary holds and omit post-success retreat/final settle. "`；在“命令行、选择 split、定位 LeRobot 输出目录”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "Compress stationary holds and omit post-success retreat/final settle. "
# 【L0153】提供文本片段 `"Use a new repo id; the source episodes are never modified."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行、选择 split、定位 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
            "Use a new repo id; the source episodes are never modified."
# 【L0154】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
        ),
# 【L0155】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0156】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0157】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0158】得到 `episodes`，它在本项目中表示本功能块中的 `episodes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `discover_episodes(`；`discover_episodes` 表示本功能块中的 `discover_episodes` 值。
    episodes = discover_episodes(
# 【L0159】把表达式/参数 `args.dataset_root.expanduser().resolve(), collection_split=args.split` 接入当前完整语句；`dataset_root` 表示数据集相关值；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。在“命令行、选择 split、定位 LeRobot 输出目录”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        args.dataset_root.expanduser().resolve(), collection_split=args.split
# 【L0160】结束或闭合当前语法结构；它属于“命令行、选择 split、定位 LeRobot 输出目录”。
    )
# 【L0161】得到 `fps`，它在本项目中表示本功能块中的 `fps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]["fps"]`；`episodes` 表示本功能块中的 `episodes` 值；`fps` 表示本功能块中的 `fps` 值。
    fps = episodes[0]["fps"]
# 【L0162】得到 `rounded_fps`，它在本项目中表示本功能块中的 `rounded_fps` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `round(fps)`；`round` 表示本功能块中的 `round` 值；`fps` 表示本功能块中的 `fps` 值。
    rounded_fps = round(fps)
# 【L0163】判断 `not np.isclose(fps, rounded_fps)` 是否成立；`isclose` 表示本功能块中的 `isclose` 值；`fps` 表示本功能块中的 `fps` 值；`rounded_fps` 表示本功能块中的 `rounded_fps` 值
    if not np.isclose(fps, rounded_fps):
# 【L0164】主动抛出 `ValueError(f"LeRobot conversion requires an integer fps, got {fps}")` 并停止当前路径；说明当前输入违反“命令行、选择 split、定位 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"LeRobot conversion requires an integer fps, got {fps}")
# 【L0165】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0166】开始执行可能抛错的“命令行、选择 split、定位 LeRobot 输出目录”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0167】从 `lerobot` 引入 `HF_LEROBOT_HOME, LeRobotDataset`。在这份程序里，`lerobot` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
        from lerobot.common.datasets.lerobot_dataset import HF_LEROBOT_HOME, LeRobotDataset
# 【L0168】捕获 `ImportError as error`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
    except ImportError as error:
# 【L0169】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“命令行、选择 split、定位 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0170】提供文本片段 `"LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行、选择 split、定位 LeRobot 输出目录”中的帮助说明、错误原因、任务名称或报告文字。
            "LeRobot is unavailable. Run this script in the OpenPI environment with `uv run`."
# 【L0171】闭合上一行开始的函数/容器后继续执行 `) from error` 中的索引或转换；`from` 表示本功能块中的 `from` 值；`error` 表示本功能块中的 `error` 值，用于“命令行、选择 split、定位 LeRobot 输出目录”。
        ) from error
# 【L0172】空行：分隔“命令行、选择 split、定位 LeRobot 输出目录”中的逻辑段，让结构更容易看清。

# 【L0173】得到 `output_path`，它在本项目中表示输出、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(HF_LEROBOT_HOME / args.repo_id).resolve()`；`HF_LEROBOT_HOME` 表示本功能块中的 `HF_LEROBOT_HOME` 值；`repo_id` 表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本；`resolve` 表示本功能块中的 `resolve` 值。
    output_path = (HF_LEROBOT_HOME / args.repo_id).resolve()
# 【L0174】得到 `hf_home`，它在本项目中表示本功能块中的 `hf_home` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(HF_LEROBOT_HOME).resolve()`；`HF_LEROBOT_HOME` 表示本功能块中的 `HF_LEROBOT_HOME` 值；`resolve` 表示本功能块中的 `resolve` 值。
    hf_home = Path(HF_LEROBOT_HOME).resolve()
# 【L0175】判断 `hf_home not in output_path.parents` 是否成立；`hf_home` 表示本功能块中的 `hf_home` 值；`output_path` 表示输出、路径相关值；`parents` 表示本功能块中的 `parents` 值
    if hf_home not in output_path.parents:
# 【L0176】主动抛出 `ValueError("repo id resolves outside HF_LEROBOT_HOME")` 并停止当前路径；说明当前输入违反“命令行、选择 split、定位 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
        raise ValueError("repo id resolves outside HF_LEROBOT_HOME")
# 【L0177】判断 `output_path.exists()` 是否成立；`output_path` 表示输出、路径相关值；`exists` 表示本功能块中的 `exists` 值
    if output_path.exists():
# 【L0178】判断 `not args.overwrite` 是否成立；`overwrite` 表示本功能块中的 `overwrite` 值
        if not args.overwrite:
# 【L0179】主动抛出 `FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")` 并停止当前路径；说明当前输入违反“命令行、选择 split、定位 LeRobot 输出目录”要求，不能继续进入仿真、训练或评测。
            raise FileExistsError(f"dataset already exists: {output_path}; pass --overwrite to replace it")
# 【L0180】对 `shutil` 调用 `rmtree(output_path)`：调用 `shutil` 提供的 `rmtree` 操作。本行产生的修改/返回值服务于“命令行、选择 split、定位 LeRobot 输出目录”。
        shutil.rmtree(output_path)
# 【L0181】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0182】得到 `first`，它在本项目中表示本功能块中的 `first` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episodes[0]`；`episodes` 表示本功能块中的 `episodes` 值。
    first = episodes[0]
# 【L0183】得到 `external_shape`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    external_shape = read_rgb(first["directory"] / first["external_paths"][0]).shape
# 【L0184】得到 `wrist_shape`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 episode 的 PNG 路径读取一张图并统一为 H×W×3、uint8 RGB ndarray。
    wrist_shape = read_rgb(first["directory"] / first["wrist_paths"][0]).shape
# 【L0185】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `LeRobotDataset.create(`；`LeRobotDataset` 表示本功能块中的 `LeRobotDataset` 值；`create` 表示本功能块中的 `create` 值。
    dataset = LeRobotDataset.create(
# 【L0186】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `args.repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“声明 LeRobot 数据集 schema”。
        repo_id=args.repo_id,
# 【L0187】给上一层函数/配置构造器的命名参数 `robot_type` 传入 `"rm65_4c2"`；该参数在本项目中表示本功能块中的 `robot_type` 值，会参与“声明 LeRobot 数据集 schema”。
        robot_type="rm65_4c2",
# 【L0188】给上一层函数/配置构造器的命名参数 `fps` 传入 `int(rounded_fps)`；该参数在本项目中表示本功能块中的 `fps` 值，会参与“声明 LeRobot 数据集 schema”。
        fps=int(rounded_fps),
# 【L0189】得到 `features`，它在本项目中表示本功能块中的 `features` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        features={
# 【L0190】定义字典/JSON 字段 `image`，它表示π0.5 按名称索引的三个图像槽位字典；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "image": {
# 【L0191】定义字典/JSON 字段 `dtype`，它表示“声明 LeRobot 数据集 schema”中的 `dtype` 数据；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": "image",
# 【L0192】定义字典/JSON 字段 `shape`，它表示“声明 LeRobot 数据集 schema”中的 `shape` 数据；字段值来自 `external_shape`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": external_shape,
# 【L0193】定义字典/JSON 字段 `names`，它表示“声明 LeRobot 数据集 schema”中的 `names` 数据；字段值来自 `["height", "width", "channel"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "names": ["height", "width", "channel"],
# 【L0194】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
            },
# 【L0195】定义字典/JSON 字段 `wrist_image`，它表示“声明 LeRobot 数据集 schema”中的 `wrist_image` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "wrist_image": {
# 【L0196】定义字典/JSON 字段 `dtype`，它表示“声明 LeRobot 数据集 schema”中的 `dtype` 数据；字段值来自 `"image"`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": "image",
# 【L0197】定义字典/JSON 字段 `shape`，它表示“声明 LeRobot 数据集 schema”中的 `shape` 数据；字段值来自 `wrist_shape`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": wrist_shape,
# 【L0198】定义字典/JSON 字段 `names`，它表示“声明 LeRobot 数据集 schema”中的 `names` 数据；字段值来自 `["height", "width", "channel"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "names": ["height", "width", "channel"],
# 【L0199】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
            },
# 【L0200】定义字典/JSON 字段 `joints`，它表示LeRobot 一帧中的六个 RM65 关节角；字段值来自 `{"dtype": "float32", "shape": (6,), "names": ["joints"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "joints": {"dtype": "float32", "shape": (6,), "names": ["joints"]},
# 【L0201】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `{"dtype": "float32", "shape": (1,), "names": ["gripper"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper": {"dtype": "float32", "shape": (1,), "names": ["gripper"]},
# 【L0202】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `{"dtype": "float32", "shape": (7,), "names": ["actions"]}`，因此保存/传递的是这个表达式当前计算出的结果。
            "actions": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
# 【L0203】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
        },
# 【L0204】给上一层函数/配置构造器的命名参数 `image_writer_threads` 传入 `10`；该参数在本项目中表示图像相关值，会参与“声明 LeRobot 数据集 schema”。
        image_writer_threads=10,
# 【L0205】给上一层函数/配置构造器的命名参数 `image_writer_processes` 传入 `5`；该参数在本项目中表示图像相关值，会参与“声明 LeRobot 数据集 schema”。
        image_writer_processes=5,
# 【L0206】结束或闭合当前语法结构；它属于“声明 LeRobot 数据集 schema”。
    )
# 【L0207】得到 `total_frames`，它在本项目中表示本功能块中的 `total_frames` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_frames = 0
# 【L0208】得到 `source_frames`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    source_frames = 0
# 【L0209】把右侧结果写进 `selected_phase_counts: dict[str, int]`（写入 `selected_phase_counts: dict[str, int]` 指定的字段）；右侧具体做的是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    selected_phase_counts: dict[str, int] = {}
# 【L0210】遍历 `episodes`，每次把当前元素放进 `episode`；这会逐个处理“逐 episode、逐帧写入数据集”所需的帧、episode、动作或实验 case。
    for episode in episodes:
# 【L0211】用 `source_frames + len(episode["states"])` 更新 `source_frames` 原值；`source_frames` 表示源位置相关值，常用于累计步数、距离、损失或成功次数。
        source_frames += len(episode["states"])
# 【L0212】得到 `indices`，它在本项目中表示当前 episode 中会被写入目标数据集的帧索引；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        indices = (
# 【L0213】调用 `select_policy_window_indices(episode)`：按阶段和运动变化挑选训练帧，减少长时间静止 hold 对数据分布的占比。它的结果/修改用于“逐 episode、逐帧写入数据集”。
            select_policy_window_indices(episode)
# 【L0214】判断 `args.policy_window` 是否成立；`policy_window` 表示策略相关值
            if args.policy_window
# 【L0215】对 `else np` 调用 `arange(len(episode["states"]), dtype=np.int64)`：调用 `else np` 提供的 `arange` 操作。本行产生的修改/返回值服务于“逐 episode、逐帧写入数据集”。
            else np.arange(len(episode["states"]), dtype=np.int64)
# 【L0216】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
        )
# 【L0217】遍历 `indices`，每次把当前元素放进 `index`；这会逐个处理“逐 episode、逐帧写入数据集”所需的帧、episode、动作或实验 case。
        for index in indices:
# 【L0218】得到 `index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `int(index)`；`index` 表示索引相关值。
            index = int(index)
# 【L0219】得到 `phase`，它在本项目中表示本功能块中的 `phase` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode["phase_names"][int(episode["phase_ids"][index])]`；`episode` 表示一条轨迹相关值；`phase_names` 表示阶段编号到 SOURCE_SETTLE、APPROACH、CLOSE 等名称的映射；`phase_ids` 表示每一帧所处专家阶段的整数编号。
            phase = episode["phase_names"][int(episode["phase_ids"][index])]
# 【L0220】把右侧结果写进 `selected_phase_counts[phase]`（写入 `selected_phase_counts[phase]` 指定的字段）；右侧具体做的是：计算表达式 `selected_phase_counts.get(phase, 0) + 1`；`selected_phase_counts` 表示本功能块中的 `selected_phase_counts` 值；`get` 表示本功能块中的 `get` 值；`phase` 表示本功能块中的 `phase` 值。
            selected_phase_counts[phase] = selected_phase_counts.get(phase, 0) + 1
# 【L0221】调用 `dataset.add_frame`：把一帧观测、动作和任务文字加入 LeRobot 数据集；本行实际操作 `dataset.add_frame(`。`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`add_frame` 表示帧相关值。
            dataset.add_frame(
# 【L0222】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“逐 episode、逐帧写入数据集”。
                {
# 【L0223】定义字典/JSON 字段 `image`，它表示π0.5 按名称索引的三个图像槽位字典；字段值来自 `read_rgb(episode["directory"] / episode["external_paths"][index])`，因此保存/传递的是这个表达式当前计算出的结果。
                    "image": read_rgb(episode["directory"] / episode["external_paths"][index]),
# 【L0224】定义字典/JSON 字段 `wrist_image`，它表示“逐 episode、逐帧写入数据集”中的 `wrist_image` 数据；字段值来自 `read_rgb(episode["directory"] / episode["wrist_paths"][index])`，因此保存/传递的是这个表达式当前计算出的结果。
                    "wrist_image": read_rgb(episode["directory"] / episode["wrist_paths"][index]),
# 【L0225】定义字典/JSON 字段 `joints`，它表示LeRobot 一帧中的六个 RM65 关节角；字段值来自 `episode["states"][index, :6]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "joints": episode["states"][index, :6],
# 【L0226】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `episode["states"][index, 6:7]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "gripper": episode["states"][index, 6:7],
# 【L0227】定义字典/JSON 字段 `actions`，它表示未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维；字段值来自 `episode["actions"][index]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "actions": episode["actions"][index],
# 【L0228】定义字典/JSON 字段 `task`，它表示LeRobot 使用的语言任务字段，训练时会成为 prompt；字段值来自 `episode["prompt"]`，因此保存/传递的是这个表达式当前计算出的结果。
                    "task": episode["prompt"],
# 【L0229】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
                }
# 【L0230】结束或闭合当前语法结构；它属于“逐 episode、逐帧写入数据集”。
            )
# 【L0231】用 `total_frames + 1` 更新 `total_frames` 原值；`total_frames` 表示本功能块中的 `total_frames` 值，常用于累计步数、距离、损失或成功次数。
            total_frames += 1
# 【L0232】调用 `dataset.save_episode`：结束并保存当前 LeRobot episode；本行实际操作 `dataset.save_episode()`。`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`save_episode` 表示一条轨迹相关值。
        dataset.save_episode()
# 【L0233】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0234】把 `` 的当前值/文字输出到终端；它用于观察“输出转换统计与脚本退出码”进度，也给日志留下可搜索证据。
    print(
# 【L0235】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
        json.dumps(
# 【L0236】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“输出转换统计与脚本退出码”。
            {
# 【L0237】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
                "status": "pass",
# 【L0238】定义字典/JSON 字段 `repo_id`，它表示“输出转换统计与脚本退出码”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
                "repo_id": args.repo_id,
# 【L0239】定义字典/JSON 字段 `output_path`，它表示“输出转换统计与脚本退出码”中的 `output_path` 数据；字段值来自 `str(output_path)`，因此保存/传递的是这个表达式当前计算出的结果。
                "output_path": str(output_path),
# 【L0240】定义字典/JSON 字段 `episode_count`，它表示“输出转换统计与脚本退出码”中的 `episode_count` 数据；字段值来自 `len(episodes)`，因此保存/传递的是这个表达式当前计算出的结果。
                "episode_count": len(episodes),
# 【L0241】定义字典/JSON 字段 `frame_count`，它表示“输出转换统计与脚本退出码”中的 `frame_count` 数据；字段值来自 `total_frames`，因此保存/传递的是这个表达式当前计算出的结果。
                "frame_count": total_frames,
# 【L0242】定义字典/JSON 字段 `source_frame_count`，它表示“输出转换统计与脚本退出码”中的 `source_frame_count` 数据；字段值来自 `source_frames`，因此保存/传递的是这个表达式当前计算出的结果。
                "source_frame_count": source_frames,
# 【L0243】定义字典/JSON 字段 `policy_window`，它表示“输出转换统计与脚本退出码”中的 `policy_window` 数据；字段值来自 `args.policy_window`，因此保存/传递的是这个表达式当前计算出的结果。
                "policy_window": args.policy_window,
# 【L0244】定义字典/JSON 字段 `selected_phase_counts`，它表示“输出转换统计与脚本退出码”中的 `selected_phase_counts` 数据；字段值来自 `dict(sorted(selected_phase_counts.items()))`，因此保存/传递的是这个表达式当前计算出的结果。
                "selected_phase_counts": dict(sorted(selected_phase_counts.items())),
# 【L0245】定义字典/JSON 字段 `fps`，它表示“输出转换统计与脚本退出码”中的 `fps` 数据；字段值来自 `int(rounded_fps)`，因此保存/传递的是这个表达式当前计算出的结果。
                "fps": int(rounded_fps),
# 【L0246】定义字典/JSON 字段 `collection_split`，它表示“输出转换统计与脚本退出码”中的 `collection_split` 数据；字段值来自 `args.split`，因此保存/传递的是这个表达式当前计算出的结果。
                "collection_split": args.split,
# 【L0247】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
            },
# 【L0248】给上一层函数/配置构造器的命名参数 `indent` 传入 `2`；该参数在本项目中表示本功能块中的 `indent` 值，会参与“输出转换统计与脚本退出码”。
            indent=2,
# 【L0249】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
        )
# 【L0250】结束或闭合当前语法结构；它属于“输出转换统计与脚本退出码”。
    )
# 【L0251】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0252】空行：分隔“输出转换统计与脚本退出码”中的逻辑段，让结构更容易看清。

# 【L0253】空行：分隔“输出转换统计与脚本退出码”中的逻辑段，让结构更容易看清。

# 【L0254】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0255】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“输出转换统计与脚本退出码”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```
