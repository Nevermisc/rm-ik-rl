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

每个源码行前有两层解释：`【Lxxxx】语法拆解` 解释关键字、圆括号、方括号、冒号、点号、等号和求值顺序；`【项目含义】` 解释这一行操作的 RM65/4C2/π0.5 对象、数据形状、来源和后续去向。空行也保留，因为空行体现程序分段。

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Import the generated RM65 + 4C2 URDF into a standalone USD file.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Import the generated RM65 + 4C2 URDF into a standalone USD file."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0008】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0009】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0010】语法拆解：`from isaaclab.app` 指定来源模块；`import AppLauncher` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `AppLauncher`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.app import AppLauncher
# 【L0011】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0012】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“解析参数并启动 Isaac Sim 应用”中的逻辑段，让结构更容易看清。

# 【L0013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
parser = argparse.ArgumentParser(description=__doc__)
# 【L0014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--urdf", type`。右侧语法为：`Path, required=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--urdf`；启动脚本可用它改变“解析参数并启动 Isaac Sim 应用”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--urdf", type=Path, required=True)
# 【L0015】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--usd", type`。右侧语法为：`Path, required=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--usd`；启动脚本可用它改变“解析参数并启动 Isaac Sim 应用”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--usd", type=Path, required=True)
# 【L0016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser.add_argument("--report", type`。右侧语法为：`Path)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `--report`；启动脚本可用它改变“解析参数并启动 Isaac Sim 应用”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--report", type=Path)
# 【L0017】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“解析参数并启动 Isaac Sim 应用”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0018】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--parse-mimic"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“解析参数并启动 Isaac Sim 应用”中的帮助说明、错误原因、任务名称或报告文字。
    "--parse-mimic",
# 【L0019】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“解析参数并启动 Isaac Sim 应用”。
    action="store_true",
# 【L0020】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Preserve URDF mimic constraints. The default imports independent follower DOFs for stable software coupling."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Preserve URDF mimic constraints. The default imports independent follower DOFs for stable software coupling."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“解析参数并启动 Isaac Sim 应用”。
    help="Preserve URDF mimic constraints. The default imports independent follower DOFs for stable software coupling.",
# 【L0021】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“解析参数并启动 Isaac Sim 应用”。
)
# 【L0022】语法拆解：`AppLauncher` 是模块/对象，点号 `.` 从中取出 `add_app_launcher_args` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parser`。
# 【项目含义】把 IsaacLab 通用参数（如 --headless、--device、--enable_cameras）加入解析器。
AppLauncher.add_app_launcher_args(parser)
# 【L0023】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
args = parser.parse_args()
# 【L0024】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0025】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `app_launcher`。右侧语法为：`AppLauncher` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args`。
# 【项目含义】得到 `app_launcher`，它在本项目中表示本功能块中的 `app_launcher` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `AppLauncher(args)`；`AppLauncher` 表示本功能块中的 `AppLauncher` 值。
app_launcher = AppLauncher(args)
# 【L0026】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_app`。右侧语法为：`app_launcher` 是起始对象；每个点号 `.` 依次读取属性/成员：`app`。
# 【项目含义】得到 `simulation_app`，它在本项目中表示本功能块中的 `simulation_app` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `app_launcher.app`；`app_launcher` 表示本功能块中的 `app_launcher` 值；`app` 表示本功能块中的 `app` 值。
simulation_app = app_launcher.app
# 【L0027】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“应用启动后才能导入的 Isaac/Omniverse 模块”中的逻辑段，让结构更容易看清。

# 【L0028】语法拆解：`import` 加载模块；`omni.kit.commands  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `omni` 引入 `omni.kit.commands  # noqa: E402`。在这份程序里，`omni` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import omni.kit.commands  # noqa: E402
# 【L0029】语法拆解：`import` 加载模块；`omni.kit.app  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `omni` 引入 `omni.kit.app  # noqa: E402`。在这份程序里，`omni` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import omni.kit.app  # noqa: E402
# 【L0030】语法拆解：`from isaacsim.core.utils.extensions` 指定来源模块；`import enable_extension  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaacsim` 引入 `enable_extension  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
# 【L0031】语法拆解：`from pxr` 指定来源模块；`import Usd, UsdPhysics  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pxr` 引入 `Usd, UsdPhysics  # noqa: E402`。在这份程序里，`pxr` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from pxr import Usd, UsdPhysics  # noqa: E402
# 【L0032】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0033】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0034】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> None` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“校验输入并设置 URDF 导入选项”，后面的缩进代码是具体实现。
def main() -> None:
# 【L0035】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `urdf`。右侧语法为：`args.urdf` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `urdf`，它在本项目中表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.urdf.expanduser().resolve()`；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    urdf = args.urdf.expanduser().resolve()
# 【L0036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `usd`。右侧语法为：`args.usd` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `usd`，它在本项目中表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.usd.expanduser().resolve()`；`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    usd = args.usd.expanduser().resolve()
# 【L0037】语法拆解：`if` 要求条件 `not urdf.is_file()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not urdf.is_file()` 是否成立；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；`is_file` 表示本功能块中的 `is_file` 值
    if not urdf.is_file():
# 【L0038】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileNotFoundError(urdf)` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileNotFoundError(urdf)` 并停止当前路径；说明当前输入违反“校验输入并设置 URDF 导入选项”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(urdf)
# 【L0039】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `usd.parent.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `usd.parent.mkdir(parents=True, exist_ok=True)`。`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`parent` 表示本功能块中的 `parent` 值。
    usd.parent.mkdir(parents=True, exist_ok=True)
# 【L0040】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验输入并设置 URDF 导入选项”中的逻辑段，让结构更容易看清。

# 【L0041】语法拆解：`enable_extension` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"isaacsim.asset.importer.urdf"`。
# 【项目含义】调用 `enable_extension("isaacsim.asset.importer.urdf")`：让 Isaac Sim 加载指定扩展；没有它就无法使用随后导入的 URDF 或 Lula API。它的结果/修改用于“校验输入并设置 URDF 导入选项”。
    enable_extension("isaacsim.asset.importer.urdf")
# 【L0042】语法拆解：`simulation_app` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `simulation_app` 执行 `update`，把 `` 加入已有结果；该集合表示本功能块中的 `simulation_app` 值，随后会用于“校验输入并设置 URDF 导入选项”。
    simulation_app.update()
# 【L0043】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“校验输入并设置 URDF 导入选项”中的逻辑段，让结构更容易看清。

# 【L0044】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `status, config`。右侧语法为：`omni.kit.commands` 是模块/对象，点号 `.` 从中取出 `execute` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"URDFCreateImportConfig"`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `status, config`；`status` 表示本功能块中的 `status` 值；`config` 表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置。右侧的来源是：计算表达式 `omni.kit.commands.execute("URDFCreateImportConfig")`；`omni` 表示本功能块中的 `omni` 值；`kit` 表示本功能块中的 `kit` 值；`commands` 表示本功能块中的 `commands` 值。
    status, config = omni.kit.commands.execute("URDFCreateImportConfig")
# 【L0045】语法拆解：`if` 要求条件 `not status` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not status` 是否成立；`status` 表示本功能块中的 `status` 值
    if not status:
# 【L0046】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("URDFCreateImportConfig failed")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("URDFCreateImportConfig failed")` 并停止当前路径；说明当前输入违反“校验输入并设置 URDF 导入选项”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("URDFCreateImportConfig failed")
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.fix_base`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `fix_base` 配置成 `True`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.fix_base = True
# 【L0048】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.merge_fixed_joints`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `merge_fixed_joints` 配置成 `True`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.merge_fixed_joints = True
# 【L0049】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.make_default_prim`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `make_default_prim` 配置成 `True`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.make_default_prim = True
# 【L0050】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.create_physics_scene`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `create_physics_scene` 配置成 `False`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.create_physics_scene = False
# 【L0051】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.import_inertia_tensor`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `import_inertia_tensor` 配置成 `True`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.import_inertia_tensor = True
# 【L0052】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.self_collision`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把 `config` 对象的 `self_collision` 配置成 `False`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.self_collision = False
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `config.parse_mimic`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`parse_mimic`。
# 【项目含义】把 `config` 对象的 `parse_mimic` 配置成 `args.parse_mimic`。`config` 在这里表示RM65 π0.5 训练/推理使用的完整 OpenPI 配置；这个设置会影响“校验输入并设置 URDF 导入选项”。
    config.parse_mimic = args.parse_mimic
# 【L0054】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0055】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `status, imported_path`。右侧语法为：`omni.kit.commands.execute(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `status, imported_path`；`status` 表示本功能块中的 `status` 值；`imported_path` 表示路径相关值。右侧的来源是：计算表达式 `omni.kit.commands.execute(`；`omni` 表示本功能块中的 `omni` 值；`kit` 表示本功能块中的 `kit` 值；`commands` 表示本功能块中的 `commands` 值。
    status, imported_path = omni.kit.commands.execute(
# 【L0056】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"URDFParseAndImportFile"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“执行导入并重新打开 USD 检查物理对象”中的帮助说明、错误原因、任务名称或报告文字。
        "URDFParseAndImportFile",
# 【L0057】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `urdf_path`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `urdf`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `urdf_path` 传入 `str(urdf)`；该参数在本项目中表示路径相关值，会参与“执行导入并重新打开 USD 检查物理对象”。
        urdf_path=str(urdf),
# 【L0058】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `import_config`。右侧语法为：`config` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `import_config` 传入 `config`；该参数在本项目中表示配置相关值，会参与“执行导入并重新打开 USD 检查物理对象”。
        import_config=config,
# 【L0059】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dest_path`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `usd`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dest_path` 传入 `str(usd)`；该参数在本项目中表示路径相关值，会参与“执行导入并重新打开 USD 检查物理对象”。
        dest_path=str(usd),
# 【L0060】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“执行导入并重新打开 USD 检查物理对象”。
    )
# 【L0061】语法拆解：`if` 要求条件 `not status` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not status` 是否成立；`status` 表示本功能块中的 `status` 值
    if not status:
# 【L0062】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("URDFParseAndImportFile failed")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("URDFParseAndImportFile failed")` 并停止当前路径；说明当前输入违反“执行导入并重新打开 USD 检查物理对象”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("URDFParseAndImportFile failed")
# 【L0063】语法拆解：`simulation_app` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `simulation_app` 执行 `update`，把 `` 加入已有结果；该集合表示本功能块中的 `simulation_app` 值，随后会用于“执行导入并重新打开 USD 检查物理对象”。
    simulation_app.update()
# 【L0064】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“执行导入并重新打开 USD 检查物理对象”中的逻辑段，让结构更容易看清。

# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stage`。右侧语法为：`Usd.Stage` 是模块/对象，点号 `.` 从中取出 `Open` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `str(usd)`。
# 【项目含义】得到 `stage`，它在本项目中表示本功能块中的 `stage` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Usd.Stage.Open(str(usd))`；`Usd` 表示本功能块中的 `Usd` 值；`Stage` 表示本功能块中的 `Stage` 值；`Open` 表示本功能块中的 `Open` 值。
    stage = Usd.Stage.Open(str(usd))
# 【L0066】语法拆解：`if` 要求条件 `stage is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `stage is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if stage is None:
# 【L0067】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"could not open generated USD: {usd}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"could not open generated USD: {usd}")` 并停止当前路径；说明当前输入违反“执行导入并重新打开 USD 检查物理对象”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"could not open generated USD: {usd}")
# 【L0068】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joints`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `joints`，它在本项目中表示六个 RM65 关节位置的一维 NumPy 数组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]`；`prim` 表示本功能块中的 `prim` 值；`stage` 表示本功能块中的 `stage` 值；`Traverse` 表示本功能块中的 `Traverse` 值。
    joints = [prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `articulation_roots`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `articulation_roots`，它在本项目中表示本功能块中的 `articulation_roots` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]`；`prim` 表示本功能块中的 `prim` 值；`stage` 表示本功能块中的 `stage` 值；`Traverse` 表示本功能块中的 `Traverse` 值。
    articulation_roots = [prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
# 【L0070】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0071】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass",
# 【L0072】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `urdf`，它表示“写出导入报告”中的 `urdf` 数据；字段值来自 `str(urdf)`，因此保存/传递的是这个表达式当前计算出的结果。
        "urdf": str(urdf),
# 【L0073】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `usd`，它表示“写出导入报告”中的 `usd` 数据；字段值来自 `str(usd)`，因此保存/传递的是这个表达式当前计算出的结果。
        "usd": str(usd),
# 【L0074】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `imported_path`，它表示“写出导入报告”中的 `imported_path` 数据；字段值来自 `str(imported_path)`，因此保存/传递的是这个表达式当前计算出的结果。
        "imported_path": str(imported_path),
# 【L0075】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `usd_joint_count`，它表示“写出导入报告”中的 `usd_joint_count` 数据；字段值来自 `len(joints)`，因此保存/传递的是这个表达式当前计算出的结果。
        "usd_joint_count": len(joints),
# 【L0076】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `parse_mimic`，它表示“写出导入报告”中的 `parse_mimic` 数据；字段值来自 `args.parse_mimic`，因此保存/传递的是这个表达式当前计算出的结果。
        "parse_mimic": args.parse_mimic,
# 【L0077】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_coupling`，它表示“写出导入报告”中的 `gripper_coupling` 数据；字段值来自 `"physx_mimic" if args.parse_mimic else "software_coupled_joint_targets"`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_coupling": "physx_mimic" if args.parse_mimic else "software_coupled_joint_targets",
# 【L0078】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `articulation_roots`，它表示“写出导入报告”中的 `articulation_roots` 数据；字段值来自 `[str(prim.GetPath()) for prim in articulation_roots]`，因此保存/传递的是这个表达式当前计算出的结果。
        "articulation_roots": [str(prim.GetPath()) for prim in articulation_roots],
# 【L0079】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出导入报告”。
    }
# 【L0080】语法拆解：`if` 要求条件 `args.report` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.report` 是否成立；`report` 表示机器可读实验报告字典
    if args.report:
# 【L0081】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_path`。右侧语法为：`args.report` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `report_path`，它在本项目中表示报告、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.report.expanduser().resolve()`；`report` 表示机器可读实验报告字典；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
        report_path = args.report.expanduser().resolve()
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_path.parent.mkdir(parents`。右侧语法为：`True, exist_ok=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `report_path.parent.mkdir(parents=True, exist_ok=True)`。`report_path` 表示报告、路径相关值；`parent` 表示本功能块中的 `parent` 值。
        report_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0083】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report_path.write_text(json.dumps(report, indent`。右侧语法为：表达式 `2) + "\n", encoding="utf-8")` 使用运算符 `+`, `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`report_path` 表示报告、路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L0084】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `print(json.dumps(report, indent`。右侧语法为：`2), flush=True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“写出导入报告”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L0085】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0086】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0087】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“无论成功失败都关闭 Isaac Sim”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
try:
# 【L0088】语法拆解：`main` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】调用本文件的 `main()`，从这里正式进入参数解析、资源创建和主任务流程；上面的函数此时才开始被实际使用。
    main()
# 【L0089】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
finally:
# 【L0090】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_app.close(skip_cleanup`。右侧语法为：`True)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `simulation_app` 调用 `close(skip_cleanup=True)`：关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。本行产生的修改/返回值服务于“无论成功失败都关闭 Isaac Sim”。
    simulation_app.close(skip_cleanup=True)
```
