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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Compute OpenPI normalization statistics for the RM65 LeRobot dataset."""
# 【L0003】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 hashlib：项目或第三方模块；后面的代码会调用其中的类或函数。
import hashlib
# 【L0008】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0009】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0010】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0011】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0012】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np
# 【L0013】导入 tqdm：项目或第三方模块；后面的代码会调用其中的类或函数。
import tqdm
# 【L0014】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0015】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
import openpi.shared.normalize as normalize
# 【L0016】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
import openpi.training.data_loader as data_loader
# 【L0017】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
import openpi.transforms as transforms
# 【L0018】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0020】调用 `Path`：创建路径对象。本行位于“OpenPI 数据加载、归一化组件和 RM65 配置”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0021】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0022】执行“OpenPI 数据加载、归一化组件和 RM65 配置”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0023】空行：分隔“OpenPI 数据加载、归一化组件和 RM65 配置”中的逻辑段，让结构更容易看清。

# 【L0024】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0025】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0026】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0027】定义类 RemoveStrings；把相关配置、状态和方法组织成一个可复用对象。
class RemoveStrings(transforms.DataTransformFn):
# 【L0028】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Drop prompt strings, which are irrelevant to numeric normalization."""
# 【L0029】空行：分隔“去掉不能参与数值统计的 prompt 字符串”中的逻辑段，让结构更容易看清。

# 【L0030】定义函数 __call__；其职责属于“去掉不能参与数值统计的 prompt 字符串”，缩进块是函数体。
    def __call__(self, sample: dict) -> dict:
# 【L0031】结束当前函数并把结果交给调用者；这里完成“去掉不能参与数值统计的 prompt 字符串”的输出。
        return {
# 【L0032】执行“去掉不能参与数值统计的 prompt 字符串”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            key: value
# 【L0033】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for key, value in sample.items()
# 【L0034】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if not np.issubdtype(np.asarray(value).dtype, np.str_)
# 【L0035】结束或闭合当前语法结构；它属于“去掉不能参与数值统计的 prompt 字符串”。
        }
# 【L0036】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0037】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0038】定义函数 main；其职责属于“创建与训练一致的数据集和 transform 链”，缩进块是函数体。
def main() -> int:
# 【L0039】计算并保存变量 `parser`；该值服务于“创建与训练一致的数据集和 transform 链”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0040】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0041】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--batch-size", type=int, default=64)
# 【L0042】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--output", type=Path)
# 【L0043】计算并保存变量 `args`；该值服务于“创建与训练一致的数据集和 transform 链”。
    args = parser.parse_args()
# 【L0044】空行：分隔“创建与训练一致的数据集和 transform 链”中的逻辑段，让结构更容易看清。

# 【L0045】给变量 `config` 赋值：当前函数使用的配置对象。
    config = make_pi05_rm65_lora_config(
# 【L0046】计算并保存变量 `repo_id`；该值服务于“创建与训练一致的数据集和 transform 链”。
        repo_id=args.repo_id,
# 【L0047】计算并保存变量 `batch_size`；该值服务于“创建与训练一致的数据集和 transform 链”。
        batch_size=args.batch_size,
# 【L0048】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0049】计算并保存变量 `data_config`；该值服务于“创建与训练一致的数据集和 transform 链”。
    data_config = config.data.create(config.assets_dirs, config.model)
# 【L0050】给变量 `dataset` 赋值：LeRobotDataset 对象，用于逐帧构造训练集。
    dataset = data_loader.create_torch_dataset(
# 【L0051】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建与训练一致的数据集和 transform 链”。
        data_config,
# 【L0052】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建与训练一致的数据集和 transform 链”。
        config.model.action_horizon,
# 【L0053】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建与训练一致的数据集和 transform 链”。
        config.model,
# 【L0054】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0055】给变量 `dataset` 赋值：LeRobotDataset 对象，用于逐帧构造训练集。
    dataset = data_loader.TransformedDataset(
# 【L0056】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建与训练一致的数据集和 transform 链”。
        dataset,
# 【L0057】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建与训练一致的数据集和 transform 链”。
        [
# 【L0058】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建与训练一致的数据集和 transform 链”。
            *data_config.repack_transforms.inputs,
# 【L0059】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建与训练一致的数据集和 transform 链”。
            *data_config.data_transforms.inputs,
# 【L0060】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建与训练一致的数据集和 transform 链”。
            RemoveStrings(),
# 【L0061】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
        ],
# 【L0062】结束或闭合当前语法结构；它属于“创建与训练一致的数据集和 transform 链”。
    )
# 【L0063】计算并保存变量 `num_batches`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    num_batches = len(dataset) // args.batch_size
# 【L0064】计算并保存变量 `loader`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    loader = data_loader.TorchDataLoader(
# 【L0065】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        dataset,
# 【L0066】计算并保存变量 `local_batch_size`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        local_batch_size=args.batch_size,
# 【L0067】计算并保存变量 `num_workers`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_workers=config.num_workers,
# 【L0068】计算并保存变量 `shuffle`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        shuffle=False,
# 【L0069】计算并保存变量 `num_batches`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
        num_batches=num_batches,
# 【L0070】结束或闭合当前语法结构；它属于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    )
# 【L0071】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0072】计算并保存变量 `running`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    running = {key: normalize.RunningStats() for key in ("state", "actions")}
# 【L0073】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for batch in tqdm.tqdm(loader, total=num_batches, desc="Computing RM65 stats"):
# 【L0074】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for key, stats in running.items():
# 【L0075】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
            stats.update(np.asarray(batch[key]))
# 【L0076】空行：分隔“不打乱数据，逐 batch 更新 state/actions RunningStats”中的逻辑段，让结构更容易看清。

# 【L0077】计算并保存变量 `norm_stats`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    norm_stats = {key: stats.get_statistics() for key, stats in running.items()}
# 【L0078】计算并保存变量 `output_dir`；该值服务于“不打乱数据，逐 batch 更新 state/actions RunningStats”。
    output_dir = config.assets_dirs / data_config.repo_id
# 【L0079】执行“不打乱数据，逐 batch 更新 state/actions RunningStats”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    normalize.save(output_dir, norm_stats)
# 【L0080】计算并保存变量 `stats_path`；该值服务于“保存 norm_stats.json、SHA-256 和统计报告”。
    stats_path = output_dir / "norm_stats.json"
# 【L0081】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0082】定义字典/JSON 字段 `status`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0083】定义字典/JSON 字段 `repo_id`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "repo_id": args.repo_id,
# 【L0084】定义字典/JSON 字段 `dataset_frames`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "dataset_frames": len(dataset),
# 【L0085】定义字典/JSON 字段 `processed_frames`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "processed_frames": num_batches * args.batch_size,
# 【L0086】定义字典/JSON 字段 `batch_size`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "batch_size": args.batch_size,
# 【L0087】定义字典/JSON 字段 `output_path`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "output_path": str(stats_path),
# 【L0088】定义字典/JSON 字段 `sha256`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
# 【L0089】定义字典/JSON 字段 `keys`；它把“保存 norm_stats.json、SHA-256 和统计报告”中的结果用稳定键名记录下来。
        "keys": sorted(norm_stats),
# 【L0090】结束或闭合当前语法结构；它属于“保存 norm_stats.json、SHA-256 和统计报告”。
    }
# 【L0091】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“保存 norm_stats.json、SHA-256 和统计报告”。
    text = json.dumps(report, indent=2) + "\n"
# 【L0092】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.output is not None:
# 【L0093】调用 `mkdir`：创建目录。本行位于“保存 norm_stats.json、SHA-256 和统计报告”。
        args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L0094】调用 `write_text`：把文本写入磁盘文件。本行位于“保存 norm_stats.json、SHA-256 和统计报告”。
        args.output.write_text(text, encoding="utf-8")
# 【L0095】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(text, end="")
# 【L0096】结束当前函数并把结果交给调用者；这里完成“保存 norm_stats.json、SHA-256 和统计报告”的输出。
    return 0
# 【L0097】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0098】空行：分隔“保存 norm_stats.json、SHA-256 和统计报告”中的逻辑段，让结构更容易看清。

# 【L0099】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0100】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
