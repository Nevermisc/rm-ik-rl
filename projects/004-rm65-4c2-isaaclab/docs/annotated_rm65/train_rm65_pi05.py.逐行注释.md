# `train_rm65_pi05.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/train_rm65_pi05.py`
- 快照 SHA-256：`865d163b72ad78ea01616e20cbec5b9f6655656f07cfe5224598a08b2964c50d`
- 总行数：99
- 程序作用：包装 OpenPI 官方 JAX trainer，使它接收 RM65 本地配置并输出可追踪 checkpoint 报告。
- 推荐读法：它没有重写训练算法；它做的是配置注入、路径管理、参数校验和结果记录。

## 功能块地图

- 第 1-20 行：依赖、项目根目录和 RM65 配置导入
- 第 23-31 行：从已安装 OpenPI 定位并动态载入官方 train.py
- 第 34-49 行：命令行参数与互斥/正数校验
- 第 51-69 行：构造并覆盖 TrainConfig 后调用官方 trainer
- 第 70-95 行：确认 checkpoint 存在并写训练报告
- 第 98-99 行：脚本入口

## 函数/类索引

- `load_openpi_trainer()`：第 23-31 行
- `main()`：第 34-95 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Launch OpenPI's JAX trainer with the RM65-B + 4C2 π0.5 LoRA config."""
# 【L0003】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 dataclasses：标准库数据类工具，用较少样板代码声明配置/记录对象；后面的代码会调用其中的类或函数。
import dataclasses
# 【L0008】导入 importlib：项目或第三方模块；后面的代码会调用其中的类或函数。
import importlib.util
# 【L0009】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0010】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0011】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0012】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0013】导入 openpi：项目或第三方模块；后面的代码会调用其中的类或函数。
import openpi
# 【L0014】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0015】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0016】调用 `Path`：创建路径对象。本行位于“依赖、项目根目录和 RM65 配置导入”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0017】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0018】执行“依赖、项目根目录和 RM65 配置导入”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0019】空行：分隔“依赖、项目根目录和 RM65 配置导入”中的逻辑段，让结构更容易看清。

# 【L0020】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config
# 【L0021】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0022】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0023】定义函数 load_openpi_trainer；其职责属于“从已安装 OpenPI 定位并动态载入官方 train.py”，缩进块是函数体。
def load_openpi_trainer():
# 【L0024】调用 `Path`：创建路径对象。本行位于“从已安装 OpenPI 定位并动态载入官方 train.py”。
    openpi_root = Path(openpi.__file__).resolve().parents[2]
# 【L0025】计算并保存变量 `trainer_path`；该值服务于“从已安装 OpenPI 定位并动态载入官方 train.py”。
    trainer_path = openpi_root / "scripts" / "train.py"
# 【L0026】计算并保存变量 `spec`；该值服务于“从已安装 OpenPI 定位并动态载入官方 train.py”。
    spec = importlib.util.spec_from_file_location("openpi_jax_train", trainer_path)
# 【L0027】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if spec is None or spec.loader is None:
# 【L0028】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ImportError(f"cannot load OpenPI trainer from {trainer_path}")
# 【L0029】计算并保存变量 `module`；该值服务于“从已安装 OpenPI 定位并动态载入官方 train.py”。
    module = importlib.util.module_from_spec(spec)
# 【L0030】执行“从已安装 OpenPI 定位并动态载入官方 train.py”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    spec.loader.exec_module(module)
# 【L0031】结束当前函数并把结果交给调用者；这里完成“从已安装 OpenPI 定位并动态载入官方 train.py”的输出。
    return module, openpi_root
# 【L0032】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0033】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0034】定义函数 main；其职责属于“命令行参数与互斥/正数校验”，缩进块是函数体。
def main() -> int:
# 【L0035】计算并保存变量 `parser`；该值服务于“命令行参数与互斥/正数校验”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0036】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--repo-id", default="local/rm65_sim_train")
# 【L0037】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--exp-name", required=True)
# 【L0038】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--num-train-steps", type=int, default=30_000)
# 【L0039】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--batch-size", type=int, default=1)
# 【L0040】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--save-interval", type=int, default=1_000)
# 【L0041】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--log-interval", type=int, default=10)
# 【L0042】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--overwrite", action="store_true")
# 【L0043】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--resume", action="store_true")
# 【L0044】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--report", type=Path)
# 【L0045】计算并保存变量 `args`；该值服务于“命令行参数与互斥/正数校验”。
    args = parser.parse_args()
# 【L0046】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.overwrite and args.resume:
# 【L0047】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--overwrite and --resume are mutually exclusive")
# 【L0048】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if min(args.num_train_steps, args.batch_size, args.save_interval, args.log_interval) < 1:
# 【L0049】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("step counts, batch size, and intervals must be positive")
# 【L0050】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0051】执行“构造并覆盖 TrainConfig 后调用官方 trainer”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    trainer, openpi_root = load_openpi_trainer()
# 【L0052】计算并保存变量 `checkpoint_base`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
    checkpoint_base = PROJECT_ROOT / "outputs" / "openpi_checkpoints"
# 【L0053】给变量 `config` 赋值：当前函数使用的配置对象。
    config = make_pi05_rm65_lora_config(
# 【L0054】计算并保存变量 `repo_id`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        repo_id=args.repo_id,
# 【L0055】计算并保存变量 `batch_size`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        batch_size=args.batch_size,
# 【L0056】计算并保存变量 `num_train_steps`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        num_train_steps=args.num_train_steps,
# 【L0057】结束或闭合当前语法结构；它属于“构造并覆盖 TrainConfig 后调用官方 trainer”。
    )
# 【L0058】给变量 `config` 赋值：当前函数使用的配置对象。
    config = dataclasses.replace(
# 【L0059】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        config,
# 【L0060】计算并保存变量 `exp_name`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        exp_name=args.exp_name,
# 【L0061】计算并保存变量 `assets_base_dir`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        assets_base_dir=str(openpi_root / "assets"),
# 【L0062】计算并保存变量 `checkpoint_base_dir`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        checkpoint_base_dir=str(checkpoint_base),
# 【L0063】计算并保存变量 `save_interval`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        save_interval=args.save_interval,
# 【L0064】计算并保存变量 `keep_period`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        keep_period=None,
# 【L0065】计算并保存变量 `log_interval`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        log_interval=args.log_interval,
# 【L0066】计算并保存变量 `overwrite`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        overwrite=args.overwrite,
# 【L0067】计算并保存变量 `resume`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        resume=args.resume,
# 【L0068】计算并保存变量 `wandb_enabled`；该值服务于“构造并覆盖 TrainConfig 后调用官方 trainer”。
        wandb_enabled=False,
# 【L0069】结束或闭合当前语法结构；它属于“构造并覆盖 TrainConfig 后调用官方 trainer”。
    )
# 【L0070】执行“确认 checkpoint 存在并写训练报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    trainer.main(config)
# 【L0071】空行：分隔“确认 checkpoint 存在并写训练报告”中的逻辑段，让结构更容易看清。

# 【L0072】计算并保存变量 `numeric_checkpoints`；该值服务于“确认 checkpoint 存在并写训练报告”。
    numeric_checkpoints = sorted(
# 【L0073】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“确认 checkpoint 存在并写训练报告”。
        (path for path in config.checkpoint_dir.iterdir() if path.name.isdigit()),
# 【L0074】计算并保存变量 `key`；该值服务于“确认 checkpoint 存在并写训练报告”。
        key=lambda path: int(path.name),
# 【L0075】结束或闭合当前语法结构；它属于“确认 checkpoint 存在并写训练报告”。
    )
# 【L0076】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not numeric_checkpoints:
# 【L0077】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(f"training completed without a numeric checkpoint in {config.checkpoint_dir}")
# 【L0078】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0079】定义字典/JSON 字段 `status`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0080】定义字典/JSON 字段 `simulation_only`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L0081】定义字典/JSON 字段 `real_robot_command_sent`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L0082】定义字典/JSON 字段 `config_name`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "config_name": config.name,
# 【L0083】定义字典/JSON 字段 `repo_id`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "repo_id": args.repo_id,
# 【L0084】定义字典/JSON 字段 `exp_name`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "exp_name": args.exp_name,
# 【L0085】定义字典/JSON 字段 `batch_size`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "batch_size": args.batch_size,
# 【L0086】定义字典/JSON 字段 `num_train_steps`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "num_train_steps": args.num_train_steps,
# 【L0087】定义字典/JSON 字段 `checkpoint_dir`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "checkpoint_dir": str(config.checkpoint_dir),
# 【L0088】定义字典/JSON 字段 `latest_checkpoint`；它把“确认 checkpoint 存在并写训练报告”中的结果用稳定键名记录下来。
        "latest_checkpoint": str(numeric_checkpoints[-1]),
# 【L0089】结束或闭合当前语法结构；它属于“确认 checkpoint 存在并写训练报告”。
    }
# 【L0090】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“确认 checkpoint 存在并写训练报告”。
    text = json.dumps(report, indent=2) + "\n"
# 【L0091】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.report is not None:
# 【L0092】调用 `mkdir`：创建目录。本行位于“确认 checkpoint 存在并写训练报告”。
        args.report.parent.mkdir(parents=True, exist_ok=True)
# 【L0093】调用 `write_text`：把文本写入磁盘文件。本行位于“确认 checkpoint 存在并写训练报告”。
        args.report.write_text(text, encoding="utf-8")
# 【L0094】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(text, end="")
# 【L0095】结束当前函数并把结果交给调用者；这里完成“确认 checkpoint 存在并写训练报告”的输出。
    return 0
# 【L0096】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0097】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0098】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0099】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
    raise SystemExit(main())
```
