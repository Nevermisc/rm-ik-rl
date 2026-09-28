# `import_combined_urdf.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/import_combined_urdf.py`
- 快照 SHA-256：`b61ed2e1eacffed6ec6dfe249376e762483307bcea1207470b1e2edf4cda844c`
- 总行数：90
- 程序作用：在 Isaac Sim 进程中把合成 URDF 导入为 USD，并检查关节和 articulation root。
- 推荐读法：重点理解为什么必须先启动 AppLauncher，再导入 omni/pxr 模块。

## 功能块地图

- 第 1-23 行：解析参数并启动 Isaac Sim 应用
- 第 25-31 行：应用启动后才能导入的 Isaac/Omniverse 模块
- 第 34-53 行：校验输入并设置 URDF 导入选项
- 第 55-69 行：执行导入并重新打开 USD 检查物理对象
- 第 70-84 行：写出导入报告
- 第 87-90 行：无论成功失败都关闭 Isaac Sim

## 函数/类索引

- `main()`：第 34-84 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Import the generated RM65 + 4C2 URDF into a standalone USD file."""
# 【L0003】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0008】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0009】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0010】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.app import AppLauncher
# 【L0011】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0013】计算并保存变量 `parser`；该值服务于“解析参数并启动 Isaac Sim 应用”。
parser = argparse.ArgumentParser(description=__doc__)
# 【L0014】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--urdf", type=Path, required=True)
# 【L0015】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--usd", type=Path, required=True)
# 【L0016】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--report", type=Path)
# 【L0017】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0018】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“解析参数并启动 Isaac Sim 应用”。
    "--parse-mimic",
# 【L0019】计算并保存变量 `action`；该值服务于“解析参数并启动 Isaac Sim 应用”。
    action="store_true",
# 【L0020】计算并保存变量 `help`；该值服务于“解析参数并启动 Isaac Sim 应用”。
    help="Preserve URDF mimic constraints. The default imports independent follower DOFs for stable software coupling.",
# 【L0021】结束或闭合当前语法结构；它属于“解析参数并启动 Isaac Sim 应用”。
)
# 【L0022】把 IsaacLab 通用参数（如 --headless、--device、--enable_cameras）加入解析器。
AppLauncher.add_app_launcher_args(parser)
# 【L0023】计算并保存变量 `args`；该值服务于“解析参数并启动 Isaac Sim 应用”。
args = parser.parse_args()
# 【L0024】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】计算并保存变量 `app_launcher`；该值服务于“应用启动后才能导入的 Isaac/Omniverse 模块”。
app_launcher = AppLauncher(args)
# 【L0026】计算并保存变量 `simulation_app`；该值服务于“应用启动后才能导入的 Isaac/Omniverse 模块”。
simulation_app = app_launcher.app
# 【L0027】空行：分隔“应用启动后才能导入的 Isaac/Omniverse 模块”中的逻辑段，让结构更容易看清。

# 【L0028】导入 omni：项目或第三方模块；后面的代码会调用其中的类或函数。
import omni.kit.commands  # noqa: E402
# 【L0029】导入 omni：项目或第三方模块；后面的代码会调用其中的类或函数。
import omni.kit.app  # noqa: E402
# 【L0030】导入 isaacsim：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
# 【L0031】导入 pxr：项目或第三方模块；后面的代码会调用其中的类或函数。
from pxr import Usd, UsdPhysics  # noqa: E402
# 【L0032】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0033】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0034】定义函数 main；其职责属于“校验输入并设置 URDF 导入选项”，缩进块是函数体。
def main() -> None:
# 【L0035】计算并保存变量 `urdf`；该值服务于“校验输入并设置 URDF 导入选项”。
    urdf = args.urdf.expanduser().resolve()
# 【L0036】计算并保存变量 `usd`；该值服务于“校验输入并设置 URDF 导入选项”。
    usd = args.usd.expanduser().resolve()
# 【L0037】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not urdf.is_file():
# 【L0038】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise FileNotFoundError(urdf)
# 【L0039】调用 `mkdir`：创建目录。本行位于“校验输入并设置 URDF 导入选项”。
    usd.parent.mkdir(parents=True, exist_ok=True)
# 【L0040】空行：分隔“校验输入并设置 URDF 导入选项”中的逻辑段，让结构更容易看清。

# 【L0041】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    enable_extension("isaacsim.asset.importer.urdf")
# 【L0042】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    simulation_app.update()
# 【L0043】空行：分隔“校验输入并设置 URDF 导入选项”中的逻辑段，让结构更容易看清。

# 【L0044】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    status, config = omni.kit.commands.execute("URDFCreateImportConfig")
# 【L0045】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not status:
# 【L0046】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError("URDFCreateImportConfig failed")
# 【L0047】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.fix_base = True
# 【L0048】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.merge_fixed_joints = True
# 【L0049】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.make_default_prim = True
# 【L0050】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.create_physics_scene = False
# 【L0051】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.import_inertia_tensor = True
# 【L0052】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.self_collision = False
# 【L0053】执行“校验输入并设置 URDF 导入选项”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    config.parse_mimic = args.parse_mimic
# 【L0054】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】执行“执行导入并重新打开 USD 检查物理对象”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    status, imported_path = omni.kit.commands.execute(
# 【L0056】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“执行导入并重新打开 USD 检查物理对象”。
        "URDFParseAndImportFile",
# 【L0057】计算并保存变量 `urdf_path`；该值服务于“执行导入并重新打开 USD 检查物理对象”。
        urdf_path=str(urdf),
# 【L0058】计算并保存变量 `import_config`；该值服务于“执行导入并重新打开 USD 检查物理对象”。
        import_config=config,
# 【L0059】计算并保存变量 `dest_path`；该值服务于“执行导入并重新打开 USD 检查物理对象”。
        dest_path=str(usd),
# 【L0060】结束或闭合当前语法结构；它属于“执行导入并重新打开 USD 检查物理对象”。
    )
# 【L0061】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not status:
# 【L0062】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError("URDFParseAndImportFile failed")
# 【L0063】执行“执行导入并重新打开 USD 检查物理对象”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    simulation_app.update()
# 【L0064】空行：分隔“执行导入并重新打开 USD 检查物理对象”中的逻辑段，让结构更容易看清。

# 【L0065】计算并保存变量 `stage`；该值服务于“执行导入并重新打开 USD 检查物理对象”。
    stage = Usd.Stage.Open(str(usd))
# 【L0066】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if stage is None:
# 【L0067】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(f"could not open generated USD: {usd}")
# 【L0068】给变量 `joints` 赋值：六个 RM65 关节位置的一维 NumPy 数组。
    joints = [prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]
# 【L0069】计算并保存变量 `articulation_roots`；该值服务于“执行导入并重新打开 USD 检查物理对象”。
    articulation_roots = [prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
# 【L0070】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0071】定义字典/JSON 字段 `status`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "status": "pass",
# 【L0072】定义字典/JSON 字段 `urdf`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "urdf": str(urdf),
# 【L0073】定义字典/JSON 字段 `usd`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "usd": str(usd),
# 【L0074】定义字典/JSON 字段 `imported_path`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "imported_path": str(imported_path),
# 【L0075】定义字典/JSON 字段 `usd_joint_count`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "usd_joint_count": len(joints),
# 【L0076】定义字典/JSON 字段 `parse_mimic`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "parse_mimic": args.parse_mimic,
# 【L0077】定义字典/JSON 字段 `gripper_coupling`；它把“写出导入报告”中的结果用稳定键名记录下来。
        "gripper_coupling": "physx_mimic" if args.parse_mimic else "software_coupled_joint_targets",
# 【L0078】调用 `Path`：创建路径对象。本行位于“写出导入报告”。
        "articulation_roots": [str(prim.GetPath()) for prim in articulation_roots],
# 【L0079】结束或闭合当前语法结构；它属于“写出导入报告”。
    }
# 【L0080】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.report:
# 【L0081】计算并保存变量 `report_path`；该值服务于“写出导入报告”。
        report_path = args.report.expanduser().resolve()
# 【L0082】调用 `mkdir`：创建目录。本行位于“写出导入报告”。
        report_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0083】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“写出导入报告”。
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L0084】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(report, indent=2), flush=True)
# 【L0085】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0086】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0087】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
try:
# 【L0088】执行“无论成功失败都关闭 Isaac Sim”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    main()
# 【L0089】清理块：无论前面成功还是抛错都执行，常用于关闭服务和 Isaac Sim。
finally:
# 【L0090】执行“无论成功失败都关闭 Isaac Sim”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    simulation_app.close(skip_cleanup=True)
```
