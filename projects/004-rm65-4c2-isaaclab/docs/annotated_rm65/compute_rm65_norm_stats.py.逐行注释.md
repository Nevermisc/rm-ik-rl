# `compute_rm65_norm_stats.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/compute_rm65_norm_stats.py`
- 快照 SHA-256：`0945a17105f8419b8b11cf79bf5008ef6262c88bf0251417636ea600a855da68`
- 总行数：100
- 程序作用：让 RM65 训练数据经过与训练相同的输入 transform，再统计 state/actions 的归一化参数并保存哈希证据。
- 推荐读法：注意它统计的是 transform 之后的数值，而不是随便对 episode.npz 做均值。

## 功能块地图

- 第 1-24 行：OpenPI 数据加载、归一化组件和 RM65 配置
- 第 27-35 行：去掉不能参与数值统计的 prompt 字符串
- 第 38-62 行：创建与训练一致的数据集和 transform 链
- 第 63-79 行：不打乱数据，逐 batch 更新 state/actions RunningStats
- 第 80-100 行：保存 norm_stats.json、SHA-256 和统计报告

## 函数/类索引

- `class RemoveStrings`：第 27-35 行
  - `RemoveStrings.__call__()`：第 30-35 行
- `main()`：第 38-96 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Compute OpenPI normalization statistics for the RM65 LeRobot dataset.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Compute OpenPI normalization statistics for the RM65 LeRobot dataset."""
# 【L0003】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `hashlib` 引入 `hashlib`。在这份程序里，`hashlib` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import hashlib
# 【L0008】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0009】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0011】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0012】从 `numpy` 引入 `numpy as np`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np
# 【L0013】从 `tqdm` 引入 `tqdm`。在这份程序里，`tqdm` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import tqdm
# 【L0014】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0015】从 `openpi` 引入 `openpi.shared.normalize as normalize`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.shared.normalize as normalize
# 【L0016】从 `openpi` 引入 `openpi.training.data_loader as data_loader`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.training.data_loader as data_loader
# 【L0017】从 `openpi` 引入 `openpi.transforms as transforms`。在这份程序里，`openpi` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import openpi.transforms as transforms
# 【L0018】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0020】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0021】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0022】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“OpenPI 数据加载、归一化组件和 RM65 配置”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0023】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0024】从 `openpi_extension` 引入 `make_pi05_rm65_lora_config`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0025】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0026】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0027】定义 `RemoveStrings` 类并继承 `transforms.DataTransformFn`；它把“去掉不能参与数值统计的 prompt 字符串”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class RemoveStrings(transforms.DataTransformFn):
# 【L0028】说明字符串 `Drop prompt strings, which are irrelevant to numeric normalization.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Drop prompt strings, which are irrelevant to numeric normalization."""
# 【L0029】空行：分隔“去掉不能参与数值统计的 prompt 字符串”中的逻辑段，让结构更容易看清。

# 【L0030】定义函数 `__call__(self, sample: dict)`；调用者把参数交给它完成“去掉不能参与数值统计的 prompt 字符串”，后面的缩进代码是具体实现。
    def __call__(self, sample: dict) -> dict:
# 【L0031】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        return {
# 【L0032】声明/传入参数 `key`，类型提示为 `value`；在本项目中它表示本功能块中的 `key` 值。
            key: value
# 【L0033】开始遍历 `for key, value in sample.items()` 中给出的序列，逐项完成“去掉不能参与数值统计的 prompt 字符串”。
            for key, value in sample.items()
# 【L0034】判断 `not np.issubdtype(np.asarray(value).dtype, np.str_)` 是否成立；`issubdtype` 表示本功能块中的 `issubdtype` 值；`asarray` 表示本功能块中的 `asarray` 值；`value` 表示本功能块中的 `value` 值
            if not np.issubdtype(np.asarray(value).dtype, np.str_)
# 【L0035】结束或闭合当前语法结构；它属于“去掉不能参与数值统计的 prompt 字符串”。
        }
# 【L0036】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0037】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0038】定义函数 `main()`；调用者把参数交给它完成“创建与训练一致的数据集和 transform 链”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0039】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0040】声明命令行参数 `--repo-id`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0041】声明命令行参数 `--batch-size`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--batch-size", type=int, default=64)
# 【L0042】声明命令行参数 `--output`；启动脚本可用它改变“创建与训练一致的数据集和 transform 链”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--output", type=Path)
# 【L0043】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0044】空行：分隔“创建与训练一致的数据集和 transform 链”中的逻辑段，让结构更容易看清。

# 【L0045】得到 `config`，它在本项目中表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建训练与推理共用的 RM65 π0.5/LoRA、数据 transform 和基础权重配置。
    config = make_pi05_rm65_lora_config(
# 【L0046】给上一层函数/配置构造器的命名参数 `repo_id` 传入 `args.repo_id`；该参数在本项目中表示LeRobot 数据集仓库标识；配置据此找到 RM65 训练样本，会参与“创建与训练一致的数据集和 transform 链”。
        repo_id=args.repo_id,
# 【L0047】给上一层函数/配置构造器的命名参数 `batch_size` 传入 `args.batch_size`；该参数在本项目中表示本功能块中的 `batch_size` 值，会参与“创建与训练一致的数据集和 transform 链”。
        batch_size=args.batch_size,
# 【L0048】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0049】得到 `data_config`，它在本项目中表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `config.data.create(config.assets_dirs, config.model)`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`create` 表示本功能块中的 `create` 值。
    data_config = config.data.create(config.assets_dirs, config.model)
# 【L0050】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.create_torch_dataset(`；`data_loader` 表示本功能块中的 `data_loader` 值；`create_torch_dataset` 表示数据集相关值。
    dataset = data_loader.create_torch_dataset(
# 【L0051】声明/传入参数 `data_config`；在本项目中它表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
        data_config,
# 【L0052】向上一行的函数调用或容器继续传入 `config.model.action_horizon`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`model` 表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置；`action_horizon` 表示动作相关值，它参与“创建与训练一致的数据集和 transform 链”。
        config.model.action_horizon,
# 【L0053】向上一行的函数调用或容器继续传入 `config.model`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`model` 表示配置为 π0.5、10 步动作 horizon 和 LoRA 变体的 OpenPI 模型配置，它参与“创建与训练一致的数据集和 transform 链”。
        config.model,
# 【L0054】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0055】得到 `dataset`，它在本项目中表示LeRobotDataset 对象，用于逐帧构造训练集；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.TransformedDataset(`；`data_loader` 表示本功能块中的 `data_loader` 值；`TransformedDataset` 表示本功能块中的 `TransformedDataset` 值。
    dataset = data_loader.TransformedDataset(
# 【L0056】声明/传入参数 `dataset`；在本项目中它表示LeRobotDataset 对象，用于逐帧构造训练集。
        dataset,
# 【L0057】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“创建与训练一致的数据集和 transform 链”。
        [
# 【L0058】把运算项 `*data_config.repack_transforms.inputs,` 接到上一行未结束的数学公式；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；`repack_transforms` 表示本功能块中的 `repack_transforms` 值；`inputs` 表示本功能块中的 `inputs` 值，整条公式用于“创建与训练一致的数据集和 transform 链”。
            *data_config.repack_transforms.inputs,
# 【L0059】把运算项 `*data_config.data_transforms.inputs,` 接到上一行未结束的数学公式；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置；`data_transforms` 表示训练和推理共享的 RM65 输入/输出及动作语义变换链；`inputs` 表示本功能块中的 `inputs` 值，整条公式用于“创建与训练一致的数据集和 transform 链”。
            *data_config.data_transforms.inputs,
# 【L0060】调用 `RemoveStrings()`：创建一个 transform，移除模型张量计算不需要的字符串字段。它的结果/修改用于“创建与训练一致的数据集和 transform 链”。
            RemoveStrings(),
# 【L0061】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
        ],
# 【L0062】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0063】得到 `num_batches`，它在本项目中表示本功能块中的 `num_batches` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `len(dataset) // args.batch_size`；`dataset` 表示LeRobotDataset 对象，用于逐帧构造训练集；`batch_size` 表示本功能块中的 `batch_size` 值。
    num_batches = len(dataset) // args.batch_size
# 【L0064】得到 `loader`，它在本项目中表示本功能块中的 `loader` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `data_loader.TorchDataLoader(`；`data_loader` 表示本功能块中的 `data_loader` 值；`TorchDataLoader` 表示本功能块中的 `TorchDataLoader` 值。
    loader = data_loader.TorchDataLoader(
# 【L0065】声明/传入参数 `dataset`；在本项目中它表示LeRobotDataset 对象，用于逐帧构造训练集。
        dataset,
# 【L0066】给上一层函数/配置构造器的命名参数 `local_batch_size` 传入 `args.batch_size`；该参数在本项目中表示本功能块中的 `local_batch_size` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        local_batch_size=args.batch_size,
# 【L0067】给上一层函数/配置构造器的命名参数 `num_workers` 传入 `config.num_workers`；该参数在本项目中表示本功能块中的 `num_workers` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_workers=config.num_workers,
# 【L0068】给上一层函数/配置构造器的命名参数 `shuffle` 传入 `False`；该参数在本项目中表示本功能块中的 `shuffle` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        shuffle=False,
# 【L0069】给上一层函数/配置构造器的命名参数 `num_batches` 传入 `num_batches`；该参数在本项目中表示本功能块中的 `num_batches` 值，会参与“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_batches=num_batches,
# 【L0070】结束或闭合当前语法结构；它属于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    )
# 【L0071】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0072】得到 `running`，它在本项目中表示分别为 state 和 actions 在线累计均值、方差与分位数的 RunningStats；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：取得或构造该字段：送入 π0.5 的七维机器人状态：六个 RM65 关节角加一个夹爪状态。
    running = {key: normalize.RunningStats() for key in ("state", "actions")}
# 【L0073】遍历 `tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats")`，每次把当前元素放进 `batch`；这会逐个处理“不打乱数据，逐 batch 更新 state/actions RunningStats”所需的帧、episode、动作或实验 case。
    for batch in tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats"):
# 【L0074】遍历 `running.items()`，每次把当前元素放进 `key, stats`；这会逐个处理“不打乱数据，逐 batch 更新 state/actions RunningStats”所需的帧、episode、动作或实验 case。
        for key, stats in running.items():
# 【L0075】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `stats.update(np.asarray(batch[key]))`。`stats` 表示本功能块中的 `stats` 值；`update` 表示本功能块中的 `update` 值。
            stats.update(np.asarray(batch[key]))
# 【L0076】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0077】得到 `norm_stats`，它在本项目中表示最终得到的 state/actions 归一化统计；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{key: stats.get_statistics() for key, stats in running.items()}`；`key` 表示本功能块中的 `key` 值；`stats` 表示本功能块中的 `stats` 值；`get_statistics` 表示本功能块中的 `get_statistics` 值。
    norm_stats = {key: stats.get_statistics() for key, stats in running.items()}
# 【L0078】得到 `output_dir`，它在本项目中表示输出相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `config.assets_dirs / data_config.repo_id`；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；`assets_dirs` 表示本功能块中的 `assets_dirs` 值；`data_config` 表示从 TrainConfig 展开得到的字段重排、transform、数据集位置等数据配置。
    output_dir = config.assets_dirs / data_config.repo_id
# 【L0079】对 `normalize` 调用 `save(output_dir, norm_stats)`：保存当前数据对象，供训练、验证或之后恢复。本行产生的修改/返回值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    normalize.save(output_dir, norm_stats)
# 【L0080】得到 `stats_path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `output_dir / "norm_stats.json"`；`output_dir` 表示输出相关值；`norm_stats` 表示最终得到的 state/actions 归一化统计；`json` 表示本功能块中的 `json` 值。
    stats_path = output_dir / "norm_stats.json"
# 【L0081】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0082】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0083】定义字典/JSON 字段 `repo_id`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `repo_id` 数据；字段值来自 `args.repo_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "repo_id": args.repo_id,
# 【L0084】定义字典/JSON 字段 `dataset_frames`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `dataset_frames` 数据；字段值来自 `len(dataset)`，因此保存/传递的是这个表达式当前计算出的结果。
        "dataset_frames": len(dataset),
# 【L0085】定义字典/JSON 字段 `processed_frames`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `processed_frames` 数据；字段值来自 `num_batches * args.batch_size`，因此保存/传递的是这个表达式当前计算出的结果。
        "processed_frames": num_batches * args.batch_size,
# 【L0086】定义字典/JSON 字段 `batch_size`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `batch_size` 数据；字段值来自 `args.batch_size`，因此保存/传递的是这个表达式当前计算出的结果。
        "batch_size": args.batch_size,
# 【L0087】定义字典/JSON 字段 `output_path`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `output_path` 数据；字段值来自 `str(stats_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "output_path": str(stats_path),
# 【L0088】定义字典/JSON 字段 `sha256`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `sha256` 数据；字段值来自 `hashlib.sha256(stats_path.read_bytes()).hexdigest()`，因此保存/传递的是这个表达式当前计算出的结果。
        "sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
# 【L0089】定义字典/JSON 字段 `keys`，它表示“保存 norm_stats.json、SHA-256 和统计报告”中的 `keys` 数据；字段值来自 `sorted(norm_stats)`，因此保存/传递的是这个表达式当前计算出的结果。
        "keys": sorted(norm_stats),
# 【L0090】结束或闭合当前语法结构；它属于“保存 norm_stats.json、SHA-256 和统计报告”。
    }
# 【L0091】得到 `text`，它在本项目中表示本功能块中的 `text` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 Python 字典序列化为 JSON 文本，供日志、报告或下游程序读取。
    text = json.dumps(report, indent=2) + "\n"
# 【L0092】检查 `args.output is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.output is not None:
# 【L0093】调用 `mkdir`：创建目录；本行实际操作 `args.output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0094】调用 `write_text`：把文本写入磁盘文件；本行实际操作 `args.output.write_text(text, encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        args.output.write_text(text, encoding="utf-8")
# 【L0095】把 `text, end=""` 的当前值/文字输出到终端；它用于观察“保存 norm_stats.json、SHA-256 和统计报告”进度，也给日志留下可搜索证据。
    print(text, end="")
# 【L0096】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    return 0
# 【L0097】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0098】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0099】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0100】主动抛出 `SystemExit(main())` 并停止当前路径；说明当前输入违反“保存 norm_stats.json、SHA-256 和统计报告”要求，不能继续进入仿真、训练或评测。
    raise SystemExit(main())
```
