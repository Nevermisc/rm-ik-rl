# `run_pick_place_baseline.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_pick_place_baseline.py`
- 快照 SHA-256：`f8fd5df9e3e9083398aaa914bd2260f5f2cec5bbba7a63988a15ae098cc56652`
- 总行数：2249
- 程序作用：RM65 仿真的主程序：创建场景、求 IK、运行脚本专家、记录数据，也可切换为 π0.5 WebSocket 闭环。
- 推荐读法：不要从第 1 行硬读到第 2249 行。先读 925-1576 的场景主流程，再读 602-881 的 π0.5 闭环，最后补数学和诊断细节。

## 功能块地图

- 第 1-19 行：启动说明、项目路径与 AppLauncher
- 第 20-175 行：命令行参数；它们是实验可重复性的外部控制面板
- 第 177-200 行：启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API
- 第 203-235 行：RM65 关节、物体尺寸、接触点和关节限位常量
- 第 238-276 行：旋转、四元数和旋转距离的数学工具
- 第 279-390 行：选择连续 IK 分支并规划不跳变的笛卡尔路径
- 第 393-413 行：把 link 局部点转换到世界坐标
- 第 416-546 行：从仿真同步采样状态、动作、外部/腕部相机图像
- 第 549-600 行：平滑移动和保持姿态的物理步进器
- 第 602-881 行：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环
- 第 884-922 行：接触力统计与平台生成工具
- 第 925-987 行：主函数输入文件和参数范围校验
- 第 988-1290 行：根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK
- 第 1292-1473 行：创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器
- 第 1475-1533 行：reset、关节索引和 episode 记录器初始化
- 第 1535-1576 行：写入初始状态；选择脚本专家或 π0.5 分支
- 第 1578-1773 行：脚本专家的接近、闭合夹爪和接触诊断
- 第 1775-1850 行：恢复重力、抬升以及抬升失败早停
- 第 1852-1915 行：搬运到目标并沿 IK 路点下降
- 第 1916-1991 行：张开夹爪、自然释放、撤退和稳定等待
- 第 1993-2058 行：计算成功指标并保存专家 episode
- 第 2059-2237 行：写出完整机器可读报告
- 第 2240-2249 行：捕获异常、关闭 Isaac Sim、返回退出码

## 函数/类索引

- `rotate_about_z()`：第 238-243 行
- `quaternion_multiply_wxyz()`：第 246-257 行
- `quaternion_to_matrix_wxyz()`：第 260-269 行
- `rotation_distance_rad()`：第 272-276 行
- `closest_equivalent_rm65_solution()`：第 279-330 行
- `require_continuous_joint_step()`：第 333-344 行
- `solve_continuous_cartesian_path()`：第 347-390 行
- `tip_world_position()`：第 393-398 行
- `body_world_position()`：第 401-403 行
- `local_point_world_position()`：第 406-413 行
- `class ExpertEpisodeCapture`：第 416-546 行
  - `ExpertEpisodeCapture.__init__()`：第 419-442 行
  - `ExpertEpisodeCapture._rgb()`：第 445-449 行
  - `ExpertEpisodeCapture._image_ready()`：第 452-460 行
  - `ExpertEpisodeCapture._render_images()`：第 462-506 行
  - `ExpertEpisodeCapture.before_step()`：第 508-546 行
- `smooth_move()`：第 549-577 行
- `hold()`：第 580-599 行
- `run_pi05_closed_loop()`：第 602-881 行
- `contact_force_statistics()`：第 884-898 行
- `spawn_platform()`：第 901-922 行
- `main()`：第 925-2237 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab."""
# 【L0003】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `itertools` 引入 `itertools`。在这份程序里，`itertools` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import itertools
# 【L0008】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0009】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0010】从 `traceback` 引入 `traceback`。在这份程序里，`traceback` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import traceback
# 【L0011】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0012】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0013】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0014】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0015】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“启动说明、项目路径与 AppLauncher”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0016】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0017】从 `isaaclab` 引入 `AppLauncher`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.app import AppLauncher
# 【L0018】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0020】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
parser = argparse.ArgumentParser(description=__doc__)
# 【L0021】声明命令行参数 `--usd`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--usd", type=Path, required=True)
# 【L0022】声明命令行参数 `--urdf`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--urdf", type=Path, required=True)
# 【L0023】声明命令行参数 `--description`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--description", type=Path, required=True)
# 【L0024】声明命令行参数 `--output`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--output", type=Path, required=True)
# 【L0025】声明命令行参数 `--transfer-joint-1-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--transfer-joint-1-rad", type=float, default=0.8)
# 【L0026】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0027】提供文本片段 `"--robot-base-z-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--robot-base-z-m",
# 【L0028】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0029】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0030】给上一层函数/配置构造器的命名参数 `help` 传入 `"World height of the robot mounting plane; Lula targets remain in the robot base frame."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="World height of the robot mounting plane; Lula targets remain in the robot base frame.",
# 【L0031】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0032】声明命令行参数 `--arm-effort-limit-sim`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-effort-limit-sim", type=float, default=300.0)
# 【L0033】声明命令行参数 `--arm-stiffness`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-stiffness", type=float, default=1000.0)
# 【L0034】声明命令行参数 `--arm-damping`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-damping", type=float, default=100.0)
# 【L0035】声明命令行参数 `--gripper-effort-limit-sim`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-effort-limit-sim", type=float, default=20.0)
# 【L0036】声明命令行参数 `--gripper-stiffness`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-stiffness", type=float, default=120.0)
# 【L0037】声明命令行参数 `--gripper-damping`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-damping", type=float, default=12.0)
# 【L0038】声明命令行参数 `--gripper-close-target-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-close-target-rad", type=float, default=0.65)
# 【L0039】声明命令行参数 `--pregrasp-distance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--pregrasp-distance-m", type=float, default=0.10)
# 【L0040】声明命令行参数 `--grasp-world-offset-x-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--grasp-world-offset-x-m", type=float, default=0.0)
# 【L0041】声明命令行参数 `--grasp-world-offset-z-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--grasp-world-offset-z-m", type=float, default=0.0)
# 【L0042】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0043】提供文本片段 `"--source-offset-x-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--source-offset-x-m",
# 【L0044】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0045】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0046】给上一层函数/配置构造器的命名参数 `help` 传入 `"Move the source block and support in world x for demonstration diversity."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world x for demonstration diversity.",
# 【L0047】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0048】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0049】提供文本片段 `"--source-offset-y-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--source-offset-y-m",
# 【L0050】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0051】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0052】给上一层函数/配置构造器的命名参数 `help` 传入 `"Move the source block and support in world y for demonstration diversity."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world y for demonstration diversity.",
# 【L0053】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0054】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0055】提供文本片段 `"--grasp-orientation-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--grasp-orientation-mode",
# 【L0056】给上一层函数/配置构造器的命名参数 `choices` 传入 `("reference", "top_down")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("reference", "top_down"),
# 【L0057】给上一层函数/配置构造器的命名参数 `default` 传入 `"reference"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="reference",
# 【L0058】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0059】声明命令行参数 `--top-down-yaw-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--top-down-yaw-rad", type=float, default=0.0)
# 【L0060】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0061】提供文本片段 `"--top-down-tilt-rad"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-tilt-rad",
# 【L0062】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0063】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0064】给上一层函数/配置构造器的命名参数 `help` 传入 `"Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal.",
# 【L0065】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0066】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0067】提供文本片段 `"--top-down-ik-multistart"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-ik-multistart",
# 【L0068】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0069】给上一层函数/配置构造器的命名参数 `default` 传入 `1`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1,
# 【L0070】给上一层函数/配置构造器的命名参数 `help` 传入 `"Number of deterministic joint-space seeds used to solve the top-down pose."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Number of deterministic joint-space seeds used to solve the top-down pose.",
# 【L0071】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0072】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0073】提供文本片段 `"--top-down-blend"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-blend",
# 【L0074】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0075】给上一层函数/配置构造器的命名参数 `default` 传入 `1.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1.0,
# 【L0076】给上一层函数/配置构造器的命名参数 `help` 传入 `"Interpolate from the calibrated side grasp (0) to the requested above-table pose (1)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Interpolate from the calibrated side grasp (0) to the requested above-table pose (1).",
# 【L0077】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0078】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0079】提供文本片段 `"--lift-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--lift-mode",
# 【L0080】给上一层函数/配置构造器的命名参数 `choices` 传入 `("joint_reference", "cartesian_vertical")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("joint_reference", "cartesian_vertical"),
# 【L0081】给上一层函数/配置构造器的命名参数 `default` 传入 `"joint_reference"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="joint_reference",
# 【L0082】给上一层函数/配置构造器的命名参数 `help` 传入 `"Use the historical fixed joint target or solve a local vertical lift from the current grasp pose."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use the historical fixed joint target or solve a local vertical lift from the current grasp pose.",
# 【L0083】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0084】声明命令行参数 `--cartesian-lift-height-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--cartesian-lift-height-m", type=float, default=0.04)
# 【L0085】声明命令行参数 `--release-clearance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--release-clearance-m", type=float, default=0.08)
# 【L0086】声明命令行参数 `--release-separation-assist-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--release-separation-assist-m", type=float, default=0.05)
# 【L0087】声明命令行参数 `--place-descent`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--place-descent", action="store_true")
# 【L0088】声明命令行参数 `--place-descent-distance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--place-descent-distance-m", type=float, default=0.10)
# 【L0089】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0090】提供文本片段 `"--place-waypoint-steps"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--place-waypoint-steps",
# 【L0091】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0092】给上一层函数/配置构造器的命名参数 `default` 传入 `60`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=60,
# 【L0093】给上一层函数/配置构造器的命名参数 `help` 传入 `"Simulation steps used for each approximately 1 cm place-descent segment."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Simulation steps used for each approximately 1 cm place-descent segment.",
# 【L0094】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0095】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0096】提供文本片段 `"--target-support-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--target-support-mode",
# 【L0097】给上一层函数/配置构造器的命名参数 `choices` 传入 `("wide_platform", "rotated_strip")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("wide_platform", "rotated_strip"),
# 【L0098】给上一层函数/配置构造器的命名参数 `default` 传入 `"wide_platform"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="wide_platform",
# 【L0099】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0100】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0101】提供文本片段 `"--target-collision-enable-stage"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--target-collision-enable-stage",
# 【L0102】给上一层函数/配置构造器的命名参数 `choices` 传入 `("after_transfer", "after_place_descent")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("after_transfer", "after_place_descent"),
# 【L0103】给上一层函数/配置构造器的命名参数 `default` 传入 `"after_transfer"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="after_transfer",
# 【L0104】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0105】声明命令行参数 `--diagnose-approach-only`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--diagnose-approach-only", action="store_true")
# 【L0106】声明命令行参数 `--diagnose-kinematics-only`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--diagnose-kinematics-only", action="store_true")
# 【L0107】声明命令行参数 `--collision-bypass-during-approach`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--collision-bypass-during-approach", action="store_true")
# 【L0108】声明命令行参数 `--initialize-at-grasp`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--initialize-at-grasp", action="store_true")
# 【L0109】声明命令行参数 `--disable-arm-gravity-during-approach`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--disable-arm-gravity-during-approach", action="store_true")
# 【L0110】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0111】提供文本片段 `"--disable-arm-gravity-through-transport"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--disable-arm-gravity-through-transport",
# 【L0112】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0113】给上一层函数/配置构造器的命名参数 `help` 传入 `"Keep arm-link gravity disabled after approach to isolate object grasp/transport physics."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep arm-link gravity disabled after approach to isolate object grasp/transport physics.",
# 【L0114】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0115】声明命令行参数 `--natural-source-gravity`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--natural-source-gravity", action="store_true")
# 【L0116】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0117】提供文本片段 `"--enable-moving-gripper-gravity"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--enable-moving-gripper-gravity",
# 【L0118】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0119】给上一层函数/配置构造器的命名参数 `help` 传入 `"Keep gravity enabled on all six moving 4C2 finger links."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep gravity enabled on all six moving 4C2 finger links.",
# 【L0120】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0121】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0122】提供文本片段 `"--unassisted-release"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--unassisted-release",
# 【L0123】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0124】给上一层函数/配置构造器的命名参数 `help` 传入 `"After opening the gripper, let gravity place the block without pose or velocity injection."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="After opening the gripper, let gravity place the block without pose or velocity injection.",
# 【L0125】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0126】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0127】提供文本片段 `"--record-episode-dir"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-episode-dir",
# 【L0128】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=Path,
# 【L0129】给上一层函数/配置构造器的命名参数 `help` 传入 `"Write a synchronized scripted-expert episode to this directory."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Write a synchronized scripted-expert episode to this directory.",
# 【L0130】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0131】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0132】提供文本片段 `"--record-stride-steps"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-stride-steps",
# 【L0133】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0134】给上一层函数/配置构造器的命名参数 `default` 传入 `12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=12,
# 【L0135】给上一层函数/配置构造器的命名参数 `help` 传入 `"Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics).",
# 【L0136】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0137】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0138】提供文本片段 `"--episode-prompt"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--episode-prompt",
# 【L0139】给上一层函数/配置构造器的命名参数 `default` 传入 `"pick up the block and place it on the target"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="pick up the block and place it on the target",
# 【L0140】给上一层函数/配置构造器的命名参数 `help` 传入 `"Language instruction stored with the expert episode."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Language instruction stored with the expert episode.",
# 【L0141】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0142】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0143】提供文本片段 `"--record-images"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-images",
# 【L0144】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0145】给上一层函数/配置构造器的命名参数 `help` 传入 `"Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras.",
# 【L0146】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0147】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0148】提供文本片段 `"--pi05-closed-loop"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--pi05-closed-loop",
# 【L0149】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0150】给上一层函数/配置构造器的命名参数 `help` 传入 `"Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert.",
# 【L0151】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0152】声明命令行参数 `--policy-host`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-host", default="127.0.0.1")
# 【L0153】声明命令行参数 `--policy-port`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-port", type=int, default=8000)
# 【L0154】声明命令行参数 `--policy-max-action-chunks`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-max-action-chunks", type=int, default=80)
# 【L0155】声明命令行参数 `--policy-execute-actions-per-chunk`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-execute-actions-per-chunk", type=int, default=5)
# 【L0156】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0157】提供文本片段 `"--policy-gripper-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-gripper-open-threshold",
# 【L0158】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0159】给上一层函数/配置构造器的命名参数 `default` 传入 `0.12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.12,
# 【L0160】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    help=(
# 【L0161】提供路径/资源标识 `"Normalized 4C2 target/feedback threshold used to verify a model-selected "`；在“命令行参数；它们是实验可重复性的外部控制面板”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
        "Normalized 4C2 target/feedback threshold used to verify a model-selected "
# 【L0162】提供文本片段 `"release. Values below the threshold are open; calibrate this in simulation."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "release. Values below the threshold are open; calibrate this in simulation."
# 【L0163】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0164】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0165】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0166】提供文本片段 `"--policy-checkpoint-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-checkpoint-id",
# 【L0167】给上一层函数/配置构造器的命名参数 `default` 传入 `"unknown"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="unknown",
# 【L0168】给上一层函数/配置构造器的命名参数 `help` 传入 `"Checkpoint identifier stored in the machine-readable evaluation report."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Checkpoint identifier stored in the machine-readable evaluation report.",
# 【L0169】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0170】把 IsaacLab 通用参数（如 --headless、--device、--enable_cameras）加入解析器。
AppLauncher.add_app_launcher_args(parser)
# 【L0171】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
args = parser.parse_args()
# 【L0172】按表达式 `not 0.0 < args.policy_gripper_open_threshold < 1.0` 检查夹爪阈值或开合状态；该阈值决定 4C2 是否被视为已张开
if not 0.0 < args.policy_gripper_open_threshold < 1.0:
# 【L0173】对 `parser` 调用 `error("--policy-gripper-open-threshold must be between 0 and 1")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--policy-gripper-open-threshold must be between 0 and 1")
# 【L0174】得到 `app_launcher`，它在本项目中表示本功能块中的 `app_launcher` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `AppLauncher(args)`；`AppLauncher` 表示本功能块中的 `AppLauncher` 值。
app_launcher = AppLauncher(args)
# 【L0175】得到 `simulation_app`，它在本项目中表示本功能块中的 `simulation_app` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `app_launcher.app`；`app_launcher` 表示本功能块中的 `app_launcher` 值；`app` 表示本功能块中的 `app` 值。
simulation_app = app_launcher.app
# 【L0176】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0177】从 `numpy` 引入 `numpy as np  # noqa: E402`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np  # noqa: E402
# 【L0178】从 `torch` 引入 `torch  # noqa: E402`。在这份程序里，`torch` 用于PyTorch 张量库；IsaacLab 的 GPU 状态和命令使用 Torch 张量；后续出现这些名字时调用的是这里的外部能力。
import torch  # noqa: E402
# 【L0179】从 `isaaclab` 引入 `isaaclab.sim as sim_utils  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import isaaclab.sim as sim_utils  # noqa: E402
# 【L0180】从 `isaacsim` 引入 `enable_extension  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
# 【L0181】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0182】调用 `enable_extension("isaacsim.robot_motion.motion_generation")`：让 Isaac Sim 加载指定扩展；没有它就无法使用随后导入的 URDF 或 Lula API。它的结果/修改用于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
enable_extension("isaacsim.robot_motion.motion_generation")
# 【L0183】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0184】从 `isaaclab` 引入 `ImplicitActuatorCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
# 【L0185】从 `isaaclab` 引入 `Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
# 【L0186】从 `isaaclab` 引入 `ContactSensor, ContactSensorCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sensors import ContactSensor, ContactSensorCfg  # noqa: E402
# 【L0187】从 `isaaclab` 引入 `Camera, CameraCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
# 【L0188】从 `openpi_extension` 引入 `(  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import (  # noqa: E402
# 【L0189】声明/传入参数 `EpisodeRecorder`；在本项目中它表示本功能块中的 `EpisodeRecorder` 值。
    EpisodeRecorder,
# 【L0190】声明/传入参数 `normalize_gripper`；在本项目中它表示夹爪相关值。
    normalize_gripper,
# 【L0191】声明/传入参数 `validate_episode`；在本项目中它表示一条轨迹相关值。
    validate_episode,
# 【L0192】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0193】从 `openpi_extension` 引入 `guard_action_chunk  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.action_guard import guard_action_chunk  # noqa: E402
# 【L0194】从 `grasp_geometry` 引入 `compute_top_down_link_pose  # noqa: E402`。在这份程序里，`grasp_geometry` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from grasp_geometry import compute_top_down_link_pose  # noqa: E402
# 【L0195】从 `isaaclab` 引入 `SimulationContext  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sim import SimulationContext  # noqa: E402
# 【L0196】从 `isaaclab` 引入 `math as math_utils  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.utils import math as math_utils  # noqa: E402
# 【L0197】从 `isaacsim` 引入 `rot_matrix_to_quat  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
# 【L0198】从 `isaacsim` 引入 `get_current_stage  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
# 【L0199】从 `isaacsim` 引入 `LulaKinematicsSolver  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver  # noqa: E402
# 【L0200】从 `pxr` 引入 `PhysxSchema, UsdPhysics  # noqa: E402`。在这份程序里，`pxr` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from pxr import PhysxSchema, UsdPhysics  # noqa: E402
# 【L0201】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0202】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0203】得到 `ARM_JOINTS`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[f"joint_{index}" for index in range(1, 7)]`；`f` 表示本功能块中的 `f` 值；`joint_` 表示关节相关值；`index` 表示索引相关值。
ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
# 【L0204】得到 `ARM_BODY_PATHS`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{f"/World/Robot/link_{index}" for index in range(1, 7)}`；`f` 表示本功能块中的 `f` 值；`World` 表示本功能块中的 `World` 值；`Robot` 表示本功能块中的 `Robot` 值。
ARM_BODY_PATHS = {f"/World/Robot/link_{index}" for index in range(1, 7)}
# 【L0205】得到 `MOVING_GRIPPER_BODY_PATHS`，它在本项目中表示夹爪、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
MOVING_GRIPPER_BODY_PATHS = {
# 【L0206】提供路径/资源标识 `"/World/Robot/tool_r_1"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_1",
# 【L0207】提供路径/资源标识 `"/World/Robot/tool_l_1"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_1",
# 【L0208】提供路径/资源标识 `"/World/Robot/tool_r_2"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_2",
# 【L0209】提供路径/资源标识 `"/World/Robot/tool_l_2"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_2",
# 【L0210】提供路径/资源标识 `"/World/Robot/tool_r_3"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_3",
# 【L0211】提供路径/资源标识 `"/World/Robot/tool_l_3"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_3",
# 【L0212】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0213】得到 `BLOCK_SIZE`，它在本项目中表示本功能块中的 `BLOCK_SIZE` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.060, 0.040, 0.025)` 的结果保存下来，供当前功能块后续使用。
BLOCK_SIZE = (0.060, 0.040, 0.025)
# 【L0214】得到 `BLOCK_MASS_KG`，它在本项目中表示本功能块中的 `BLOCK_MASS_KG` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.030` 的结果保存下来，供当前功能块后续使用。
BLOCK_MASS_KG = 0.030
# 【L0215】得到 `SOURCE_BLOCK_POSITION`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
SOURCE_BLOCK_POSITION = np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)
# 【L0216】得到 `SOURCE_BLOCK_QUATERNION_WXYZ`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(-0.20872162, -0.00000211, 0.97797507, 0.00002437)` 的结果保存下来，供当前功能块后续使用。
SOURCE_BLOCK_QUATERNION_WXYZ = (-0.20872162, -0.00000211, 0.97797507, 0.00002437)
# 【L0217】得到 `TARGET_PLATFORM_SIZE`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.200, 0.200, 0.040)` 的结果保存下来，供当前功能块后续使用。
TARGET_PLATFORM_SIZE = (0.200, 0.200, 0.040)
# 【L0218】得到 `TARGET_PLATFORM_TOP_Z`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.650` 的结果保存下来，供当前功能块后续使用。
TARGET_PLATFORM_TOP_Z = 0.650
# 【L0219】得到 `SOURCE_PLATFORM_SIZE`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.120, 0.018, 0.020)` 的结果保存下来，供当前功能块后续使用。
SOURCE_PLATFORM_SIZE = (0.120, 0.018, 0.020)
# 【L0220】得到 `TARGET_STRIP_SIZE`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.070, 0.018, 0.020)` 的结果保存下来，供当前功能块后续使用。
TARGET_STRIP_SIZE = (0.070, 0.018, 0.020)
# 【L0221】得到 `SOURCE_PLATFORM_TOP_Z`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.7330` 的结果保存下来，供当前功能块后续使用。
SOURCE_PLATFORM_TOP_Z = 0.7330
# 【L0222】得到 `RELEASE_DOWNWARD_SPEED_M_S`，它在本项目中表示本功能块中的 `RELEASE_DOWNWARD_SPEED_M_S` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.10` 的结果保存下来，供当前功能块后续使用。
RELEASE_DOWNWARD_SPEED_M_S = 0.10
# 【L0223】得到 `RELEASE_SEPARATION_ASSIST_M`，它在本项目中表示本功能块中的 `RELEASE_SEPARATION_ASSIST_M` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.05` 的结果保存下来，供当前功能块后续使用。
RELEASE_SEPARATION_ASSIST_M = 0.05
# 【L0224】得到 `TIP_LOCAL_POINTS`，它在本项目中表示本功能块中的 `TIP_LOCAL_POINTS` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
TIP_LOCAL_POINTS = {
# 【L0225】定义字典/JSON 字段 `tool_r_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_r_2` 数据；字段值来自 `(0.04368, -0.00645, 0.01250)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_r_2": (0.04368, -0.00645, 0.01250),
# 【L0226】定义字典/JSON 字段 `tool_l_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_l_2` 数据；字段值来自 `(0.04368, 0.00645, 0.01257)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_l_2": (0.04368, 0.00645, 0.01257),
# 【L0227】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0228】得到 `PAD_LOCAL_CENTERS`，它在本项目中表示本功能块中的 `PAD_LOCAL_CENTERS` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
PAD_LOCAL_CENTERS = {
# 【L0229】定义字典/JSON 字段 `tool_r_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_r_2` 数据；字段值来自 `(0.028775714, -0.011597111, -0.073257379)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_r_2": (0.028775714, -0.011597111, -0.073257379),
# 【L0230】定义字典/JSON 字段 `tool_l_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_l_2` 数据；字段值来自 `(0.027286683, 0.013343694, -0.072958842)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_l_2": (0.027286683, 0.013343694, -0.072958842),
# 【L0231】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0232】把右侧结果写进 `CONTACT_SENSORS: dict[str, ContactSensor]`（写入 `CONTACT_SENSORS: dict[str, ContactSensor]` 指定的字段）；右侧具体做的是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
CONTACT_SENSORS: dict[str, ContactSensor] = {}
# 【L0233】得到 `GRIPPER_MASTER_JOINT`，它在本项目中表示夹爪、关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"tool_gripper_joint"`；`tool_gripper_joint` 表示夹爪、关节相关值。
GRIPPER_MASTER_JOINT = "tool_gripper_joint"
# 【L0234】得到 `RM65_JOINT_LOWER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])`；`array` 表示本功能块中的 `array` 值。
RM65_JOINT_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
# 【L0235】得到 `RM65_JOINT_UPPER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])`；`array` 表示本功能块中的 `array` 值。
RM65_JOINT_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])
# 【L0236】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0237】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0238】定义函数 `rotate_about_z(position: np.ndarray, angle: float)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def rotate_about_z(position: np.ndarray, angle: float) -> np.ndarray:
# 【L0239】把右侧返回的多个结果按位置拆给 `cosine, sine`；`cosine` 表示本功能块中的 `cosine` 值；`sine` 表示本功能块中的 `sine` 值。右侧的来源是：计算表达式 `np.cos(angle), np.sin(angle)`；`cos` 表示本功能块中的 `cos` 值；`angle` 表示本功能块中的 `angle` 值；`sin` 表示本功能块中的 `sin` 值。
    cosine, sine = np.cos(angle), np.sin(angle)
# 【L0240】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0241】这是上一行尚未闭合的参数、数组或字典内容：`[cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],`；`cosine` 表示本功能块中的 `cosine` 值；`position` 表示位置相关值；`sine` 表示本功能块中的 `sine` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
        [cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],
# 【L0242】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0243】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0244】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0245】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0246】定义函数 `quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray) -> np.ndarray:
# 【L0247】把右侧返回的多个结果按位置拆给 `lw, lx, ly, lz`；`lw` 表示本功能块中的 `lw` 值；`lx` 表示本功能块中的 `lx` 值；`ly` 表示本功能块中的 `ly` 值；`lz` 表示本功能块中的 `lz` 值。右侧的来源是：计算表达式 `left`；`left` 表示本功能块中的 `left` 值。
    lw, lx, ly, lz = left
# 【L0248】把右侧返回的多个结果按位置拆给 `rw, rx, ry, rz`；`rw` 表示本功能块中的 `rw` 值；`rx` 表示本功能块中的 `rx` 值；`ry` 表示本功能块中的 `ry` 值；`rz` 表示本功能块中的 `rz` 值。右侧的来源是：计算表达式 `right`；`right` 表示本功能块中的 `right` 值。
    rw, rx, ry, rz = right
# 【L0249】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0250】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0251】向上一行的函数调用或容器继续传入 `lw * rw - lx * rx - ly * ry - lz * rz`；`lw` 表示本功能块中的 `lw` 值；`rw` 表示本功能块中的 `rw` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rw - lx * rx - ly * ry - lz * rz,
# 【L0252】向上一行的函数调用或容器继续传入 `lw * rx + lx * rw + ly * rz - lz * ry`；`lw` 表示本功能块中的 `lw` 值；`rx` 表示本功能块中的 `rx` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rx + lx * rw + ly * rz - lz * ry,
# 【L0253】向上一行的函数调用或容器继续传入 `lw * ry - lx * rz + ly * rw + lz * rx`；`lw` 表示本功能块中的 `lw` 值；`ry` 表示本功能块中的 `ry` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * ry - lx * rz + ly * rw + lz * rx,
# 【L0254】向上一行的函数调用或容器继续传入 `lw * rz + lx * ry - ly * rx + lz * rw`；`lw` 表示本功能块中的 `lw` 值；`rz` 表示本功能块中的 `rz` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rz + lx * ry - ly * rx + lz * rw,
# 【L0255】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0256】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0257】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0258】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0259】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0260】定义函数 `quaternion_to_matrix_wxyz(quaternion: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def quaternion_to_matrix_wxyz(quaternion: np.ndarray) -> np.ndarray:
# 【L0261】把右侧返回的多个结果按位置拆给 `w, x, y, z`；`w` 表示本功能块中的 `w` 值；`x` 表示本功能块中的 `x` 值；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值。右侧的来源是：计算表达式 `quaternion`；`quaternion` 表示四元数相关值。
    w, x, y, z = quaternion
# 【L0262】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0263】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0264】这是上一行尚未闭合的参数、数组或字典内容：`[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],`；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值；`x` 表示本功能块中的 `x` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
# 【L0265】这是上一行尚未闭合的参数、数组或字典内容：`[2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],`；`x` 表示本功能块中的 `x` 值；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
# 【L0266】这是上一行尚未闭合的参数、数组或字典内容：`[2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],`；`x` 表示本功能块中的 `x` 值；`z` 表示本功能块中的 `z` 值；`y` 表示本功能块中的 `y` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
# 【L0267】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0268】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0269】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0270】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0271】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0272】定义函数 `rotation_distance_rad(left: np.ndarray, right: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def rotation_distance_rad(left: np.ndarray, right: np.ndarray) -> float:
# 【L0273】说明字符串 `Return the geodesic angle between two 3x3 rotation matrices.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Return the geodesic angle between two 3x3 rotation matrices."""
# 【L0274】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0275】得到 `cosine`，它在本项目中表示本功能块中的 `cosine` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `0.5 * (np.trace(left.T @ right) - 1.0)`；`trace` 表示本功能块中的 `trace` 值；`left` 表示本功能块中的 `left` 值；`T` 表示本功能块中的 `T` 值。
    cosine = 0.5 * (np.trace(left.T @ right) - 1.0)
# 【L0276】结束当前函数并把 `float(np.arccos(np.clip(cosine, -1.0, 1.0)))` 交回调用者；这个值的含义是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))
# 【L0277】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0278】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0279】定义函数 `closest_equivalent_rm65_solution(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def closest_equivalent_rm65_solution(
# 【L0280】声明/传入参数 `lula`，类型提示为 `LulaKinematicsSolver`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
    lula: LulaKinematicsSolver,
# 【L0281】声明/传入参数 `solution`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `solution` 值。
    solution: np.ndarray,
# 【L0282】声明/传入参数 `reference`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `reference` 值。
    reference: np.ndarray,
# 【L0283】以 `) -> np.ndarray:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> np.ndarray:
# 【L0284】说明字符串 `Choose an FK-equivalent RM65 wrist branch nearest to ``reference``.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Choose an FK-equivalent RM65 wrist branch nearest to ``reference``.
# 【L0285】继续说明字符串，原文是 ``；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0286】继续说明字符串，原文是 `Lula may return a spherical-wrist equivalent such as`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    Lula may return a spherical-wrist equivalent such as
# 【L0287】继续说明字符串，原文是 ```(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    ``(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating
# 【L0288】继续说明字符串，原文是 `directly between those representations can command a multi-radian jump`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    directly between those representations can command a multi-radian jump
# 【L0289】继续说明字符串，原文是 `even though the Cartesian poses are adjacent.  Enumerate only known`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    even though the Cartesian poses are adjacent.  Enumerate only known
# 【L0290】继续说明字符串，原文是 `equivalent representations, verify each with FK, and keep the one with`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    equivalent representations, verify each with FK, and keep the one with
# 【L0291】继续说明字符串，原文是 `the smallest joint-space jump.`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    the smallest joint-space jump.
# 【L0292】继续说明字符串，原文是 ``；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0293】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0294】得到 `solution`，它在本项目中表示本功能块中的 `solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `solution, dtype=np.float64`（本功能块中的 `solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    solution = np.asarray(solution, dtype=np.float64)
# 【L0295】得到 `reference`，它在本项目中表示本功能块中的 `reference` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `reference, dtype=np.float64`（本功能块中的 `reference, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    reference = np.asarray(reference, dtype=np.float64)
# 【L0296】把右侧返回的多个结果按位置拆给 `target_position, target_rotation`；`target_position` 表示目标、位置相关值；`target_rotation` 表示目标、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    target_position, target_rotation = lula.compute_forward_kinematics("link_6", solution)
# 【L0297】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0298】得到 `bases`，它在本项目中表示本功能块中的 `bases` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    bases = [solution.copy()]
# 【L0299】得到 `wrist_flip`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    wrist_flip = solution.copy()
# 【L0300】用 `wrist_flip[3] + np.pi` 更新 `wrist_flip[3]` 原值；`wrist_flip[3]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[3] += np.pi
# 【L0301】用 `wrist_flip[4] * -1.0` 更新 `wrist_flip[4]` 原值；`wrist_flip[4]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[4] *= -1.0
# 【L0302】用 `wrist_flip[5] + np.pi` 更新 `wrist_flip[5]` 原值；`wrist_flip[5]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[5] += np.pi
# 【L0303】对 `bases` 执行 `append`，把 `wrist_flip` 加入已有结果；该集合表示本功能块中的 `bases` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    bases.append(wrist_flip)
# 【L0304】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0305】得到 `valid`，它在本项目中表示本功能块中的 `valid` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    valid: list[tuple[float, float, np.ndarray]] = []
# 【L0306】遍历 `bases`，每次把当前元素放进 `base`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
    for base in bases:
# 【L0307】得到 `joint_values`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
        joint_values = []
# 【L0308】遍历 `enumerate(base)`，每次把当前元素放进 `index, value`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for index, value in enumerate(base):
# 【L0309】得到 `equivalents`，它在本项目中表示本功能块中的 `equivalents` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            equivalents = [
# 【L0310】把表达式/参数 `value + turns * 2.0 * np.pi` 接入当前完整语句；`value` 表示本功能块中的 `value` 值；`turns` 表示本功能块中的 `turns` 值；`pi` 表示本功能块中的 `pi` 值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                value + turns * 2.0 * np.pi
# 【L0311】开始遍历 `for turns in (-1, 0, 1)` 中给出的序列，逐项完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                for turns in (-1, 0, 1)
# 【L0312】判断 `RM65_JOINT_LOWER_RAD[index] - 1e-9` 是否成立；`RM65_JOINT_LOWER_RAD` 表示RM65 机械约束或项目常量；`index` 表示索引相关值
                if RM65_JOINT_LOWER_RAD[index] - 1e-9
# 【L0313】把表达式/参数 `<= value + turns * 2.0 * np.pi` 接入当前完整语句；`value` 表示本功能块中的 `value` 值；`turns` 表示本功能块中的 `turns` 值；`pi` 表示本功能块中的 `pi` 值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                <= value + turns * 2.0 * np.pi
# 【L0314】把表达式/参数 `<= RM65_JOINT_UPPER_RAD[index] + 1e-9` 接入当前完整语句；`RM65_JOINT_UPPER_RAD` 表示RM65 机械约束或项目常量；`index` 表示索引相关值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                <= RM65_JOINT_UPPER_RAD[index] + 1e-9
# 【L0315】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            ]
# 【L0316】对 `joint_values` 执行 `append`，把 `equivalents` 加入已有结果；该集合表示关节相关值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            joint_values.append(equivalents)
# 【L0317】遍历 `itertools.product(*joint_values)`，每次把当前元素放进 `values`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for values in itertools.product(*joint_values):
# 【L0318】得到 `candidate`，它在本项目中表示本功能块中的 `candidate` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `values, dtype=np.float64`（本功能块中的 `values, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
            candidate = np.asarray(values, dtype=np.float64)
# 【L0319】把右侧返回的多个结果按位置拆给 `position, rotation`；`position` 表示位置相关值；`rotation` 表示旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
            position, rotation = lula.compute_forward_kinematics("link_6", candidate)
# 【L0320】判断 `np.linalg.norm(position - target_position) > 1e-5` 是否成立；`linalg` 表示本功能块中的 `linalg` 值；`norm` 表示本功能块中的 `norm` 值；`position` 表示位置相关值
            if np.linalg.norm(position - target_position) > 1e-5:
# 【L0321】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0322】判断 `rotation_distance_rad(rotation, target_rotation) > 1e-5` 是否成立；`rotation_distance_rad` 表示旋转相关值；`rotation` 表示旋转相关值；`target_rotation` 表示目标、旋转相关值
            if rotation_distance_rad(rotation, target_rotation) > 1e-5:
# 【L0323】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0324】得到 `delta`，它在本项目中表示本功能块中的 `delta` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.abs(candidate - reference)`；`abs` 表示本功能块中的 `abs` 值；`candidate` 表示本功能块中的 `candidate` 值；`reference` 表示本功能块中的 `reference` 值。
            delta = np.abs(candidate - reference)
# 【L0325】调用 `np.linalg.norm`：计算向量长度/欧氏距离；本行实际操作 `valid.append((float(np.max(delta)), float(np.linalg.norm(delta)), candidate))`。`valid` 表示本功能块中的 `valid` 值；`append` 表示本功能块中的 `append` 值。
            valid.append((float(np.max(delta)), float(np.linalg.norm(delta)), candidate))
# 【L0326】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0327】判断 `not valid` 是否成立；`valid` 表示本功能块中的 `valid` 值
    if not valid:
# 【L0328】主动抛出 `RuntimeError("No FK-equivalent RM65 joint representation passed validation")` 并停止当前路径；说明当前输入违反“选择连续 IK 分支并规划不跳变的笛卡尔路径”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("No FK-equivalent RM65 joint representation passed validation")
# 【L0329】把右侧返回的多个结果按位置拆给 `_, _, selected`；`_` 表示本功能块中的 `_` 值；`_` 表示本功能块中的 `_` 值；`selected` 表示本功能块中的 `selected` 值。右侧的来源是：计算表达式 `min(valid, key=lambda item: (item[0], item[1]))`；`valid` 表示本功能块中的 `valid` 值；`key` 表示本功能块中的 `key` 值；`lambda` 表示本功能块中的 `lambda` 值。
    _, _, selected = min(valid, key=lambda item: (item[0], item[1]))
# 【L0330】结束当前函数并把 `selected.copy()` 交回调用者；这个值的含义是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    return selected.copy()
# 【L0331】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0332】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0333】定义函数 `require_continuous_joint_step(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def require_continuous_joint_step(
# 【L0334】声明/传入参数 `start`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `start` 值。
    start: np.ndarray,
# 【L0335】声明/传入参数 `target`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target: np.ndarray,
# 【L0336】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0337】声明/传入参数 `label`，类型提示为 `str`；在本项目中它表示本功能块中的 `label` 值。
    label: str,
# 【L0338】得到 `max_step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.75` 的结果保存下来，供当前功能块后续使用。
    max_step_rad: float = 0.75,
# 【L0339】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> None:
# 【L0340】得到 `max_step`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `target) - np.asarray(start)))`（本功能块中的 `target) - np.asarray(start)))` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    max_step = float(np.max(np.abs(np.asarray(target) - np.asarray(start))))
# 【L0341】判断 `max_step > max_step_rad` 是否成立；`max_step` 表示步相关值；`max_step_rad` 表示步相关值
    if max_step > max_step_rad:
# 【L0342】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“选择连续 IK 分支并规划不跳变的笛卡尔路径”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0343】把比较条件 `f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"` 接到上一行尚未结束的布尔表达式；`f` 表示本功能块中的 `f` 值；`unsafe` 表示本功能块中的 `unsafe` 值；`IK` 表示本功能块中的 `IK` 值。比较结果共同决定“选择连续 IK 分支并规划不跳变的笛卡尔路径”是否通过。
            f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"
# 【L0344】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        )
# 【L0345】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0346】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0347】定义函数 `solve_continuous_cartesian_path(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def solve_continuous_cartesian_path(
# 【L0348】声明/传入参数 `lula`，类型提示为 `LulaKinematicsSolver`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
    lula: LulaKinematicsSolver,
# 【L0349】向上一行的函数调用或容器继续传入 `target_positions: list[np.ndarray]`；`target_positions` 表示目标相关值；`ndarray` 表示本功能块中的 `ndarray` 值，它参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    target_positions: list[np.ndarray],
# 【L0350】声明/传入参数 `target_orientation`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target_orientation: np.ndarray,
# 【L0351】声明/传入参数 `numerical_seed`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `numerical_seed` 值。
    numerical_seed: np.ndarray,
# 【L0352】声明/传入参数 `command_reference`，类型提示为 `np.ndarray`；在本项目中它表示控制命令相关值。
    command_reference: np.ndarray,
# 【L0353】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0354】得到 `max_step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.75` 的结果保存下来，供当前功能块后续使用。
    max_step_rad: float = 0.75,
# 【L0355】以 `) -> tuple[np.ndarray, list[np.ndarray], float] | None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> tuple[np.ndarray, list[np.ndarray], float] | None:
# 【L0356】说明字符串 `Solve a path while keeping Lula's seed and the commanded branch separate.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Solve a path while keeping Lula's seed and the commanded branch separate."""
# 【L0357】得到 `raw_seed`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `numerical_seed, dtype=np.float64).copy(`（本功能块中的 `numerical_seed, dtype=np.float64).copy(` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    raw_seed = np.asarray(numerical_seed, dtype=np.float64).copy()
# 【L0358】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `command_reference, dtype=np.float64).copy(`（控制命令相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    command = np.asarray(command_reference, dtype=np.float64).copy()
# 【L0359】把右侧结果写进 `commands: list[np.ndarray]`（写入 `commands: list[np.ndarray]` 指定的字段）；右侧具体做的是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    commands: list[np.ndarray] = []
# 【L0360】得到 `path_max_step`，它在本项目中表示路径、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
    path_max_step = 0.0
# 【L0361】遍历 `target_positions`，每次把当前元素放进 `target_position`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
    for target_position in target_positions:
# 【L0362】得到 `seeds`，它在本项目中表示本功能块中的 `seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[raw_seed]`；`raw_seed` 表示原始相关值。
        seeds = [raw_seed]
# 【L0363】判断 `not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0)` 是否成立；`allclose` 表示本功能块中的 `allclose` 值；`raw_seed` 表示原始相关值；`command` 表示控制命令相关值
        if not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0):
# 【L0364】对 `seeds` 执行 `append`，把 `command` 加入已有结果；该集合表示本功能块中的 `seeds` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            seeds.append(command)
# 【L0365】得到 `candidates`，它在本项目中表示本功能块中的 `candidates` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
        candidates: list[tuple[float, np.ndarray, np.ndarray]] = []
# 【L0366】遍历 `seeds`，每次把当前元素放进 `seed`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for seed in seeds:
# 【L0367】把右侧返回的多个结果按位置拆给 `raw_solution, success`；`raw_solution` 表示原始相关值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
            raw_solution, success = lula.compute_inverse_kinematics(
# 【L0368】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的帮助说明、错误原因、任务名称或报告文字。
                "link_6",
# 【L0369】声明/传入参数 `target_position`；在本项目中它表示目标、位置相关值。
                target_position,
# 【L0370】声明/传入参数 `target_orientation`；在本项目中它表示目标相关值。
                target_orientation,
# 【L0371】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `seed`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                warm_start=seed,
# 【L0372】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                position_tolerance=1e-4,
# 【L0373】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                orientation_tolerance=1e-3,
# 【L0374】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0375】判断 `not success` 是否成立；`success` 表示成功相关值
            if not success:
# 【L0376】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0377】得到 `raw_solution`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `raw_solution, dtype=np.float64`（原始相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
            raw_solution = np.asarray(raw_solution, dtype=np.float64)
# 【L0378】得到 `command_solution`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
            command_solution = closest_equivalent_rm65_solution(
# 【L0379】把表达式/参数 `lula, raw_solution, command` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`raw_solution` 表示原始相关值；`command` 表示控制命令相关值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                lula, raw_solution, command
# 【L0380】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0381】得到 `step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(np.max(np.abs(command_solution - command)))`；`abs` 表示本功能块中的 `abs` 值；`command_solution` 表示控制命令相关值；`command` 表示控制命令相关值。
            step_rad = float(np.max(np.abs(command_solution - command)))
# 【L0382】对 `candidates` 执行 `append`，把 `(step_rad, raw_solution, command_solution)` 加入已有结果；该集合表示本功能块中的 `candidates` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            candidates.append((step_rad, raw_solution, command_solution))
# 【L0383】判断 `not candidates` 是否成立；`candidates` 表示本功能块中的 `candidates` 值
        if not candidates:
# 【L0384】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            return None
# 【L0385】把右侧返回的多个结果按位置拆给 `step_rad, raw_seed, command`；`step_rad` 表示步相关值；`raw_seed` 表示原始相关值；`command` 表示控制命令相关值。右侧的来源是：计算表达式 `min(candidates, key=lambda item: item[0])`；`candidates` 表示本功能块中的 `candidates` 值；`key` 表示本功能块中的 `key` 值；`lambda` 表示本功能块中的 `lambda` 值。
        step_rad, raw_seed, command = min(candidates, key=lambda item: item[0])
# 【L0386】判断 `step_rad > max_step_rad` 是否成立；`step_rad` 表示步相关值；`max_step_rad` 表示步相关值
        if step_rad > max_step_rad:
# 【L0387】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            return None
# 【L0388】得到 `path_max_step`，它在本项目中表示路径、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(path_max_step, step_rad)`；`path_max_step` 表示路径、步相关值；`step_rad` 表示步相关值。
        path_max_step = max(path_max_step, step_rad)
# 【L0389】对 `commands` 执行 `append`，把 `command.copy()` 加入已有结果；该集合表示本功能块中的 `commands` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        commands.append(command.copy())
# 【L0390】结束当前函数并把 `raw_seed.copy(), commands, path_max_step` 交回调用者；这个值的含义是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    return raw_seed.copy(), commands, path_max_step
# 【L0391】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0392】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0393】定义函数 `tip_world_position(robot: Articulation, body_name: str)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0394】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0395】得到 `local`，它在本项目中表示本功能块中的 `local` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)`；`tensor` 表示本功能块中的 `tensor` 值；`TIP_LOCAL_POINTS` 表示本功能块中的 `TIP_LOCAL_POINTS` 值；`body_name` 表示刚体相关值。
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
# 【L0396】结束当前函数并把 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0397】把表达式/参数 `robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0398】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“把 link 局部点转换到世界坐标”。
    )[0]
# 【L0399】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0400】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0401】定义函数 `body_world_position(robot: Articulation, body_name: str)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def body_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0402】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0403】结束当前函数并把 `robot.data.body_pos_w[0, body_id]` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id]
# 【L0404】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0405】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0406】定义函数 `local_point_world_position(参数在后续行继续)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def local_point_world_position(
# 【L0407】把表达式/参数 `robot: Articulation, body_name: str, local_position: tuple[float, float, float]` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`Articulation` 表示本功能块中的 `Articulation` 值；`body_name` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    robot: Articulation, body_name: str, local_position: tuple[float, float, float]
# 【L0408】以 `) -> torch.Tensor:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“把 link 局部点转换到世界坐标”。
) -> torch.Tensor:
# 【L0409】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0410】得到 `local`，它在本项目中表示本功能块中的 `local` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor(local_position, device=robot.device).unsqueeze(0)`；`tensor` 表示本功能块中的 `tensor` 值；`local_position` 表示位置相关值；`device` 表示本功能块中的 `device` 值。
    local = torch.tensor(local_position, device=robot.device).unsqueeze(0)
# 【L0411】结束当前函数并把 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0412】把表达式/参数 `robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0413】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“把 link 局部点转换到世界坐标”。
    )[0]
# 【L0414】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0415】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0416】定义 `ExpertEpisodeCapture` 类并继承 `object`；它把“从仿真同步采样状态、动作、外部/腕部相机图像”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class ExpertEpisodeCapture:
# 【L0417】说明字符串 `Sample observations and the action targets applied on the next physics step.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Sample observations and the action targets applied on the next physics step."""
# 【L0418】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0419】定义函数 `__init__(参数在后续行继续)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def __init__(
# 【L0420】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0421】声明/传入参数 `recorder`，类型提示为 `EpisodeRecorder`；在本项目中它表示本功能块中的 `recorder` 值。
        recorder: EpisodeRecorder,
# 【L0422】向上一行的函数调用或容器继续传入 `arm_ids: list[int]`；`arm_ids` 表示本功能块中的 `arm_ids` 值，它参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
        arm_ids: list[int],
# 【L0423】声明/传入参数 `gripper_master_id`，类型提示为 `int`；在本项目中它表示夹爪相关值。
        gripper_master_id: int,
# 【L0424】声明/传入参数 `stride_steps`，类型提示为 `int`；在本项目中它表示步数相关值。
        stride_steps: int,
# 【L0425】声明/传入参数 `physics_dt`，类型提示为 `float`；在本项目中它表示本功能块中的 `physics_dt` 值。
        physics_dt: float,
# 【L0426】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim: SimulationContext,
# 【L0427】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        external_camera: Camera | None = None,
# 【L0428】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_camera: Camera | None = None,
# 【L0429】得到 `wrist_tool_body_id`，它在本项目中表示腕部相机、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_tool_body_id: int | None = None,
# 【L0430】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0431】把 `self` 对象的 `recorder` 配置成 `recorder`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.recorder = recorder
# 【L0432】把 `self` 对象的 `arm_ids` 配置成 `arm_ids`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.arm_ids = arm_ids
# 【L0433】把 `self` 对象的 `gripper_master_id` 配置成 `gripper_master_id`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.gripper_master_id = gripper_master_id
# 【L0434】把 `self` 对象的 `stride_steps` 配置成 `stride_steps`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.stride_steps = stride_steps
# 【L0435】把 `self` 对象的 `physics_dt` 配置成 `physics_dt`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.physics_dt = physics_dt
# 【L0436】把 `self` 对象的 `sim` 配置成 `sim`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.sim = sim
# 【L0437】把 `self` 对象的 `external_camera` 配置成 `external_camera`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.external_camera = external_camera
# 【L0438】把 `self` 对象的 `wrist_camera` 配置成 `wrist_camera`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_camera = wrist_camera
# 【L0439】把 `self` 对象的 `wrist_tool_body_id` 配置成 `wrist_tool_body_id`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_tool_body_id = wrist_tool_body_id
# 【L0440】得到 `wrist_local_offset`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.wrist_local_offset: torch.Tensor | None = None
# 【L0441】得到 `wrist_local_forward`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.wrist_local_forward: torch.Tensor | None = None
# 【L0442】把 `self` 对象的 `sim_step` 配置成 `0`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.sim_step = 0
# 【L0443】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0444】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0445】定义函数 `_rgb(camera: Camera)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _rgb(camera: Camera) -> np.ndarray:
# 【L0446】得到 `image`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()`；`camera` 表示本功能块中的 `camera` 值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`output` 表示输出文件路径。
        image = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
# 【L0447】判断 `image.dtype != np.uint8` 是否成立；`image` 表示图像相关值；`dtype` 表示本功能块中的 `dtype` 值；`uint8` 表示本功能块中的 `uint8` 值
        if image.dtype != np.uint8:
# 【L0448】得到 `image`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
            image = np.clip(image, 0, 255).astype(np.uint8)
# 【L0449】结束当前函数并把 `image` 交回调用者；这个值的含义是：计算表达式 `image`；`image` 表示图像相关值。
        return image
# 【L0450】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0451】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0452】定义函数 `_image_ready(image: np.ndarray)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _image_ready(image: np.ndarray) -> bool:
# 【L0453】说明字符串 `Return whether an Isaac camera produced a usable RGB frame.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
        """Return whether an Isaac camera produced a usable RGB frame."""
# 【L0454】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0455】结束当前函数并把 `(` 交回调用者；这个值的含义是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        return (
# 【L0456】把比较条件 `image.ndim == 3` 接到上一行尚未结束的布尔表达式；`image` 表示图像相关值；`ndim` 表示本功能块中的 `ndim` 值。比较结果共同决定“从仿真同步采样状态、动作、外部/腕部相机图像”是否通过。
            image.ndim == 3
# 【L0457】把条件 `image.shape[0] > 0` 用“并且”接到上一行判断中；判断 `image.shape[0] > 0` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[0] > 0
# 【L0458】把条件 `image.shape[1] > 0` 用“并且”接到上一行判断中；判断 `image.shape[1] > 0` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[1] > 0
# 【L0459】把条件 `image.shape[2] == 3` 用“并且”接到上一行判断中；判断 `image.shape[2] == 3` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[2] == 3
# 【L0460】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0461】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0462】定义函数 `_render_images(self, robot: Articulation, cube: RigidObject)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _render_images(self, robot: Articulation, cube: RigidObject) -> tuple[np.ndarray, np.ndarray]:
# 【L0463】检查 `self.external_camera is None or self.wrist_camera is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.external_camera is None or self.wrist_camera is None:
# 【L0464】主动抛出 `RuntimeError("both cameras are required for image recording")` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("both cameras are required for image recording")
# 【L0465】检查 `self.wrist_tool_body_id is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.wrist_tool_body_id is None:
# 【L0466】主动抛出 `RuntimeError("wrist tool body id is required for image recording")` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("wrist tool body id is required for image recording")
# 【L0467】得到 `tool_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.body_pos_w[0, self.wrist_tool_body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
        tool_position = robot.data.body_pos_w[0, self.wrist_tool_body_id]
# 【L0468】得到 `tool_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.body_quat_w[0, self.wrist_tool_body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。
        tool_quaternion = robot.data.body_quat_w[0, self.wrist_tool_body_id]
# 【L0469】检查 `self.wrist_local_offset is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.wrist_local_offset is None:
# 【L0470】得到 `world_offset`，它在本项目中表示本功能块中的 `world_offset` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor([0.0, 0.15, 0.10], device=robot.device)`；`tensor` 表示本功能块中的 `tensor` 值；`device` 表示本功能块中的 `device` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            world_offset = torch.tensor([0.0, 0.15, 0.10], device=robot.device)
# 【L0471】得到 `eye`，它在本项目中表示本功能块中的 `eye` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tool_position + world_offset`；`tool_position` 表示位置相关值；`world_offset` 表示本功能块中的 `world_offset` 值。
            eye = tool_position + world_offset
# 【L0472】得到 `world_forward`，它在本项目中表示本功能块中的 `world_forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
            world_forward = torch.nn.functional.normalize(cube.data.root_pos_w[0] - eye, dim=0)
# 【L0473】得到 `inverse_tool_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]`；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_conjugate` 表示本功能块中的 `quat_conjugate` 值；`tool_quaternion` 表示四元数相关值。
            inverse_tool_quaternion = math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]
# 【L0474】把 `self` 对象的 `wrist_local_offset` 配置成 `math_utils.quat_apply(`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_local_offset = math_utils.quat_apply(
# 【L0475】对 `inverse_tool_quaternion` 调用 `unsqueeze(0), world_offset.unsqueeze(0)`：调用 `inverse_tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                inverse_tool_quaternion.unsqueeze(0), world_offset.unsqueeze(0)
# 【L0476】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )[0]
# 【L0477】把 `self` 对象的 `wrist_local_forward` 配置成 `math_utils.quat_apply(`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_local_forward = math_utils.quat_apply(
# 【L0478】对 `inverse_tool_quaternion` 调用 `unsqueeze(0), world_forward.unsqueeze(0)`：调用 `inverse_tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                inverse_tool_quaternion.unsqueeze(0), world_forward.unsqueeze(0)
# 【L0479】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )[0]
# 【L0480】断言 `self.wrist_local_forward is not None` 必须成立；这是开发期内部一致性检查，失败说明“从仿真同步采样状态、动作、外部/腕部相机图像”此前产生了不可能的状态。
        assert self.wrist_local_forward is not None
# 【L0481】得到 `eye`，它在本项目中表示本功能块中的 `eye` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tool_position + math_utils.quat_apply(`；`tool_position` 表示位置相关值；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_apply` 表示本功能块中的 `quat_apply` 值。
        eye = tool_position + math_utils.quat_apply(
# 【L0482】对 `tool_quaternion` 调用 `unsqueeze(0), self.wrist_local_offset.unsqueeze(0)`：调用 `tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            tool_quaternion.unsqueeze(0), self.wrist_local_offset.unsqueeze(0)
# 【L0483】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )[0]
# 【L0484】得到 `forward`，它在本项目中表示本功能块中的 `forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `math_utils.quat_apply(`；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_apply` 表示本功能块中的 `quat_apply` 值。
        forward = math_utils.quat_apply(
# 【L0485】对 `tool_quaternion` 调用 `unsqueeze(0), self.wrist_local_forward.unsqueeze(0)`：调用 `tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            tool_quaternion.unsqueeze(0), self.wrist_local_forward.unsqueeze(0)
# 【L0486】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )[0]
# 【L0487】开始对 `self.wrist_camera` 调用多行方法 `set_world_poses_from_view`：调用 `self.wrist_camera` 提供的 `set_world_poses_from_view` 操作；具体参数写在随后几行，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_camera.set_world_poses_from_view(
# 【L0488】对 `eye` 调用 `unsqueeze(0), (eye + forward).unsqueeze(0)`：调用 `eye` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            eye.unsqueeze(0), (eye + forward).unsqueeze(0)
# 【L0489】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0490】作者写下的设计说明：Isaac Sim can expose an empty RGB tensor during the first few render
        # Isaac Sim can expose an empty RGB tensor during the first few render
# 【L0491】作者写下的设计说明：ticks after a headless camera starts.  Wait for real sensor frames
        # ticks after a headless camera starts.  Wait for real sensor frames
# 【L0492】作者写下的设计说明：instead of recording a fabricated image or aborting the episode.
        # instead of recording a fabricated image or aborting the episode.
# 【L0493】得到 `last_shapes`，它在本项目中表示本功能块中的 `last_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        last_shapes: tuple[tuple[int, ...], tuple[int, ...]] | None = None
# 【L0494】遍历 `range(30)`，每次把当前元素放进 `_`；这会逐个处理“从仿真同步采样状态、动作、外部/腕部相机图像”所需的帧、episode、动作或实验 case。
        for _ in range(30):
# 【L0495】对 `self.sim` 调用 `render()`：调用 `self.sim` 提供的 `render` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.sim.render()
# 【L0496】对 `self.external_camera` 执行 `update`，把 `self.physics_dt` 加入已有结果；该集合表示当前类实例，随后会用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.external_camera.update(self.physics_dt)
# 【L0497】对 `self.wrist_camera` 执行 `update`，把 `self.physics_dt` 加入已有结果；该集合表示当前类实例，随后会用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_camera.update(self.physics_dt)
# 【L0498】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._rgb(self.external_camera)`；`_rgb` 表示本功能块中的 `_rgb` 值；`external_camera` 表示外部相机相关值。
            external_rgb = self._rgb(self.external_camera)
# 【L0499】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._rgb(self.wrist_camera)`；`_rgb` 表示本功能块中的 `_rgb` 值；`wrist_camera` 表示腕部相机相关值。
            wrist_rgb = self._rgb(self.wrist_camera)
# 【L0500】得到 `last_shapes`，它在本项目中表示本功能块中的 `last_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(external_rgb.shape, wrist_rgb.shape)`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`shape` 表示本功能块中的 `shape` 值；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。
            last_shapes = (external_rgb.shape, wrist_rgb.shape)
# 【L0501】判断 `self._image_ready(external_rgb) and self._image_ready(wrist_rgb)` 是否成立；`_image_ready` 表示图像相关值；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像
            if self._image_ready(external_rgb) and self._image_ready(wrist_rgb):
# 【L0502】结束当前函数并把 `external_rgb, wrist_rgb` 交回调用者；这个值的含义是：计算表达式 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。
                return external_rgb, wrist_rgb
# 【L0503】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0504】提供文本片段 `"Isaac cameras did not produce usable RGB frames after 30 render ticks; "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“从仿真同步采样状态、动作、外部/腕部相机图像”中的帮助说明、错误原因、任务名称或报告文字。
            "Isaac cameras did not produce usable RGB frames after 30 render ticks; "
# 【L0505】把表达式/参数 `f"last shapes were {last_shapes}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`last` 表示本功能块中的 `last` 值；`shapes` 表示本功能块中的 `shapes` 值。在“从仿真同步采样状态、动作、外部/腕部相机图像”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            f"last shapes were {last_shapes}"
# 【L0506】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0507】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0508】定义函数 `before_step(参数在后续行继续)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def before_step(
# 【L0509】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0510】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot: Articulation,
# 【L0511】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube: RigidObject,
# 【L0512】声明/传入参数 `target_state`，类型提示为 `torch.Tensor`；在本项目中它表示目标、状态相关值。
        target_state: torch.Tensor,
# 【L0513】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
        phase: str,
# 【L0514】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0515】作者写下的设计说明：The simulator data buffers are stale immediately after the initial
        # The simulator data buffers are stale immediately after the initial
# 【L0516】作者写下的设计说明：direct state write, so the first valid sample is taken after one
        # direct state write, so the first valid sample is taken after one
# 【L0517】作者写下的设计说明：complete stride of physics updates.
        # complete stride of physics updates.
# 【L0518】判断 `self.sim_step > 0 and self.sim_step % self.stride_steps == 0` 是否成立；`sim_step` 表示仿真、步相关值；`stride_steps` 表示步数相关值
        if self.sim_step > 0 and self.sim_step % self.stride_steps == 0:
# 【L0519】得到 `observed_arm`，它在本项目中表示本功能块中的 `observed_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
            observed_arm = robot.data.joint_pos[0, self.arm_ids].detach().cpu().numpy()
# 【L0520】得到 `observed_gripper`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            observed_gripper = normalize_gripper(
# 【L0521】对 `float(robot.data.joint_pos[0, self.gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, self.gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                float(robot.data.joint_pos[0, self.gripper_master_id].item())
# 【L0522】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0523】得到 `target_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_state[0, self.arm_ids].detach().cpu().numpy()`；`target_state` 表示目标、状态相关值；`arm_ids` 表示本功能块中的 `arm_ids` 值；`detach` 表示本功能块中的 `detach` 值。
            target_arm = target_state[0, self.arm_ids].detach().cpu().numpy()
# 【L0524】得到 `target_gripper`，它在本项目中表示目标、夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            target_gripper = normalize_gripper(
# 【L0525】对 `float(target_state[0, self.gripper_master_id]` 调用 `item())`：调用 `float(target_state[0, self.gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                float(target_state[0, self.gripper_master_id].item())
# 【L0526】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0527】得到 `action`，它在本项目中表示动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把括号中的多个一维数组沿现有轴首尾连接；在本项目中常用于把六关节和一个夹爪值组成七维状态/动作。
            action = np.concatenate([target_arm, [target_gripper]])
# 【L0528】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.cat(`；`cat` 表示本功能块中的 `cat` 值。
            cube_pose = torch.cat(
# 【L0529】这是上一行尚未闭合的参数、数组或字典内容：`[cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_pos_w` 表示本功能块中的 `root_pos_w` 值，共同完成“从仿真同步采样状态、动作、外部/腕部相机图像”。
                [cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0
# 【L0530】对 `)` 调用 `detach().cpu().numpy()`：调用 `)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            ).detach().cpu().numpy()
# 【L0531】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            external_rgb = None
# 【L0532】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            wrist_rgb = None
# 【L0533】检查 `self.external_camera is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if self.external_camera is not None:
# 【L0534】把右侧返回的多个结果按位置拆给 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。右侧的来源是：计算表达式 `self._render_images(robot, cube)`；`_render_images` 表示本功能块中的 `_render_images` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                external_rgb, wrist_rgb = self._render_images(robot, cube)
# 【L0535】开始对 `self.recorder` 调用多行方法 `add_frame`：调用 `self.recorder` 提供的 `add_frame` 操作；具体参数写在随后几行，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.recorder.add_frame(
# 【L0536】给上一层函数/配置构造器的命名参数 `timestamp_s` 传入 `self.sim_step * self.physics_dt`；该参数在本项目中表示本功能块中的 `timestamp_s` 值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                timestamp_s=self.sim_step * self.physics_dt,
# 【L0537】给上一层函数/配置构造器的命名参数 `sim_step` 传入 `self.sim_step`；该参数在本项目中表示仿真、步相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                sim_step=self.sim_step,
# 【L0538】给上一层函数/配置构造器的命名参数 `phase` 传入 `phase`；该参数在本项目中表示本功能块中的 `phase` 值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                phase=phase,
# 【L0539】给上一层函数/配置构造器的命名参数 `joint_position_rad` 传入 `observed_arm`；该参数在本项目中表示关节、位置相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                joint_position_rad=observed_arm,
# 【L0540】给上一层函数/配置构造器的命名参数 `gripper_position` 传入 `observed_gripper`；该参数在本项目中表示夹爪、位置相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                gripper_position=observed_gripper,
# 【L0541】给上一层函数/配置构造器的命名参数 `action` 传入 `action`；该参数在本项目中表示动作相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                action=action,
# 【L0542】给上一层函数/配置构造器的命名参数 `cube_pose_wxyz` 传入 `cube_pose`；该参数在本项目中表示任务方块相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                cube_pose_wxyz=cube_pose,
# 【L0543】给上一层函数/配置构造器的命名参数 `external_rgb` 传入 `external_rgb`；该参数在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                external_rgb=external_rgb,
# 【L0544】给上一层函数/配置构造器的命名参数 `wrist_rgb` 传入 `wrist_rgb`；该参数在本项目中表示随末端移动的腕部相机 RGB 图像，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                wrist_rgb=wrist_rgb,
# 【L0545】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0546】用 `self.sim_step + 1` 更新 `self.sim_step` 原值；`self.sim_step` 表示当前类实例，常用于累计步数、距离、损失或成功次数。
        self.sim_step += 1
# 【L0547】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0548】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0549】定义函数 `smooth_move(参数在后续行继续)`；调用者把参数交给它完成“平滑移动和保持姿态的物理步进器”，后面的缩进代码是具体实现。
def smooth_move(
# 【L0550】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0551】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0552】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0553】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0554】向上一行的函数调用或容器继续传入 `joint_ids: list[int]`；`joint_ids` 表示关节相关值，它参与“平滑移动和保持姿态的物理步进器”。
    joint_ids: list[int],
# 【L0555】声明/传入参数 `start`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `start` 值。
    start: np.ndarray,
# 【L0556】声明/传入参数 `target`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target: np.ndarray,
# 【L0557】声明/传入参数 `steps`，类型提示为 `int`；在本项目中它表示步数相关值。
    steps: int,
# 【L0558】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
    phase: str,
# 【L0559】得到 `capture`，它在本项目中表示本功能块中的 `capture` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    capture: ExpertEpisodeCapture | None = None,
# 【L0560】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0561】把 `f"PICK_PLACE_STAGE={phase}_START", flush=True` 的当前值/文字输出到终端；它用于观察“平滑移动和保持姿态的物理步进器”进度，也给日志留下可搜索证据。
    print(f"PICK_PLACE_STAGE={phase}_START", flush=True)
# 【L0562】遍历 `range(steps)`，每次把当前元素放进 `step`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
    for step in range(steps):
# 【L0563】得到 `progress`，它在本项目中表示本功能块中的 `progress` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(step + 1) / steps`；`step` 表示步相关值；`steps` 表示步数相关值。
        progress = (step + 1) / steps
# 【L0564】得到 `smooth`，它在本项目中表示本功能块中的 `smooth` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `3.0 * progress**2 - 2.0 * progress**3`；`progress` 表示本功能块中的 `progress` 值。
        smooth = 3.0 * progress**2 - 2.0 * progress**3
# 【L0565】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `start + smooth * (target - start)`；`start` 表示本功能块中的 `start` 值；`smooth` 表示本功能块中的 `smooth` 值；`target` 表示目标相关值。
        command = start + smooth * (target - start)
# 【L0566】把右侧结果写进 `state[:, joint_ids]`（写入 `state[:, joint_ids]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(command, device=sim.device, dtype=state.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`command` 表示控制命令相关值；`device` 表示本功能块中的 `device` 值。
        state[:, joint_ids] = torch.as_tensor(command, device=sim.device, dtype=state.dtype)
# 【L0567】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
        robot.set_joint_position_target(state)
# 【L0568】检查 `capture is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if capture is not None:
# 【L0569】对 `capture` 调用 `before_step(robot, cube, state, phase)`：调用 `capture` 提供的 `before_step` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
            capture.before_step(robot, cube, state, phase)
# 【L0570】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
        robot.write_data_to_sim()
# 【L0571】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
        cube.write_data_to_sim()
# 【L0572】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
        sim.step(render=False)
# 【L0573】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
        robot.update(sim.get_physics_dt())
# 【L0574】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
        cube.update(sim.get_physics_dt())
# 【L0575】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0576】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“平滑移动和保持姿态的物理步进器”。
            contact_sensor.update(sim.get_physics_dt())
# 【L0577】把 `f"PICK_PLACE_STAGE={phase}_DONE", flush=True` 的当前值/文字输出到终端；它用于观察“平滑移动和保持姿态的物理步进器”进度，也给日志留下可搜索证据。
    print(f"PICK_PLACE_STAGE={phase}_DONE", flush=True)
# 【L0578】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0579】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0580】定义函数 `hold(参数在后续行继续)`；调用者把参数交给它完成“平滑移动和保持姿态的物理步进器”，后面的缩进代码是具体实现。
def hold(
# 【L0581】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0582】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0583】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0584】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0585】声明/传入参数 `steps`，类型提示为 `int`；在本项目中它表示步数相关值。
    steps: int,
# 【L0586】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
    phase: str,
# 【L0587】得到 `capture`，它在本项目中表示本功能块中的 `capture` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    capture: ExpertEpisodeCapture | None = None,
# 【L0588】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0589】遍历 `range(steps)`，每次把当前元素放进 `_`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
    for _ in range(steps):
# 【L0590】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
        robot.set_joint_position_target(state)
# 【L0591】检查 `capture is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if capture is not None:
# 【L0592】对 `capture` 调用 `before_step(robot, cube, state, phase)`：调用 `capture` 提供的 `before_step` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
            capture.before_step(robot, cube, state, phase)
# 【L0593】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
        robot.write_data_to_sim()
# 【L0594】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
        cube.write_data_to_sim()
# 【L0595】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
        sim.step(render=False)
# 【L0596】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
        robot.update(sim.get_physics_dt())
# 【L0597】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
        cube.update(sim.get_physics_dt())
# 【L0598】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0599】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“平滑移动和保持姿态的物理步进器”。
            contact_sensor.update(sim.get_physics_dt())
# 【L0600】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0601】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0602】定义函数 `run_pi05_closed_loop(参数在后续行继续)`；调用者把参数交给它完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，后面的缩进代码是具体实现。
def run_pi05_closed_loop(
# 【L0603】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0604】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0605】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0606】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0607】向上一行的函数调用或容器继续传入 `arm_ids: list[int]`；`arm_ids` 表示本功能块中的 `arm_ids` 值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    arm_ids: list[int],
# 【L0608】向上一行的函数调用或容器继续传入 `gripper_ids: list[int]`；`gripper_ids` 表示夹爪相关值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    gripper_ids: list[int],
# 【L0609】声明/传入参数 `gripper_master_id`，类型提示为 `int`；在本项目中它表示夹爪相关值。
    gripper_master_id: int,
# 【L0610】声明/传入参数 `target_block_position`，类型提示为 `np.ndarray`；在本项目中它表示目标、位置相关值。
    target_block_position: np.ndarray,
# 【L0611】声明/传入参数 `settled_source_position`，类型提示为 `torch.Tensor`；在本项目中它表示源位置、位置相关值。
    settled_source_position: torch.Tensor,
# 【L0612】声明/传入参数 `target_platform_collision_apis`，类型提示为 `list`；在本项目中它表示目标、支撑平台相关值。
    target_platform_collision_apis: list,
# 【L0613】声明/传入参数 `episode_capture`，类型提示为 `ExpertEpisodeCapture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
    episode_capture: ExpertEpisodeCapture,
# 【L0614】声明/传入参数 `episode_recorder`，类型提示为 `EpisodeRecorder`；在本项目中它表示把同步帧保存在内存并最终写盘的记录器。
    episode_recorder: EpisodeRecorder,
# 【L0615】声明/传入参数 `output`，类型提示为 `Path`；在本项目中它表示输出文件路径。
    output: Path,
# 【L0616】以 `) -> int:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
) -> int:
# 【L0617】说明字符串 `Run receding-horizon π0.5 control and write task-level evidence.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Run receding-horizon π0.5 control and write task-level evidence."""
# 【L0618】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0619】从 `time` 引入 `time`。在这份程序里，`time` 用于计时和短暂等待；后续出现这些名字时调用的是这里的外部能力。
    import time
# 【L0620】从 `websockets` 引入 `websockets.sync.client as ws`。在这份程序里，`websockets` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    import websockets.sync.client as ws
# 【L0621】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0622】从 `openpi_extension` 引入 `call_connect_without_keepalive`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    from openpi_extension.websocket_compat import call_connect_without_keepalive
# 【L0623】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0624】得到 `original_connect`，它在本项目中表示本功能块中的 `original_connect` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ws.connect`；`ws` 表示本功能块中的 `ws` 值；`connect` 表示本功能块中的 `connect` 值。
    original_connect = ws.connect
# 【L0625】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0626】定义函数 `connect_without_keepalive(*connect_args, **connect_kwargs)`；调用者把参数交给它完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，后面的缩进代码是具体实现。
    def connect_without_keepalive(*connect_args, **connect_kwargs):
# 【L0627】结束当前函数并把 `call_connect_without_keepalive(` 交回调用者；这个值的含义是：计算表达式 `call_connect_without_keepalive(`；`call_connect_without_keepalive` 表示本功能块中的 `call_connect_without_keepalive` 值。
        return call_connect_without_keepalive(
# 【L0628】把表达式/参数 `original_connect, *connect_args, **connect_kwargs` 接入当前完整语句；`original_connect` 表示本功能块中的 `original_connect` 值；`connect_args` 表示本功能块中的 `connect_args` 值；`connect_kwargs` 表示本功能块中的 `connect_kwargs` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            original_connect, *connect_args, **connect_kwargs
# 【L0629】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        )
# 【L0630】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0631】把 `ws` 对象的 `connect` 配置成 `connect_without_keepalive`。`ws` 在这里表示本功能块中的 `ws` 值；这个设置会影响“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    ws.connect = connect_without_keepalive
# 【L0632】从 `openpi_client` 引入 `WebsocketClientPolicy`。在这份程序里，`openpi_client` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    from openpi_client.websocket_client_policy import WebsocketClientPolicy
# 【L0633】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0634】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
    for collision_api in target_platform_collision_apis:
# 【L0635】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L0636】把 `"PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print("PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L0637】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0638】得到 `client`，它在本项目中表示本功能块中的 `client` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `WebsocketClientPolicy(args.policy_host, args.policy_port)`；`WebsocketClientPolicy` 表示本功能块中的 `WebsocketClientPolicy` 值；`policy_host` 表示策略相关值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口。
    client = WebsocketClientPolicy(args.policy_host, args.policy_port)
# 【L0639】得到 `inference_latencies`，它在本项目中表示本功能块中的 `inference_latencies` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    inference_latencies = []
# 【L0640】得到 `total_joint_limit_clamps`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_joint_limit_clamps = 0
# 【L0641】得到 `total_joint_step_clamps`，它在本项目中表示关节、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_joint_step_clamps = 0
# 【L0642】得到 `total_gripper_clamps`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_gripper_clamps = 0
# 【L0643】得到 `action_chunks`，它在本项目中表示本 episode 已向 π0.5 请求的动作块数量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    action_chunks = 0
# 【L0644】得到 `executed_actions`，它在本项目中表示实际送进 Isaac 控制器的七维动作步数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    executed_actions = 0
# 【L0645】得到 `max_cube_z`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    max_cube_z = float(cube.data.root_pos_w[0, 2].item())
# 【L0646】得到 `consecutive_candidate_chunks`，它在本项目中表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    consecutive_candidate_chunks = 0
# 【L0647】得到 `last_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    last_executed_gripper_target = None
# 【L0648】得到 `release_postcondition_applied`，它在本项目中表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
    release_postcondition_applied = False
# 【L0649】得到 `release_postcondition_arm_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    release_postcondition_arm_target = None
# 【L0650】得到 `minimum_observed_gripper_normalized`，它在本项目中表示夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float("inf")`；`inf` 表示本功能块中的 `inf` 值。
    minimum_observed_gripper_normalized = float("inf")
# 【L0651】得到 `minimum_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float("inf")`；`inf` 表示本功能块中的 `inf` 值。
    minimum_executed_gripper_target = float("inf")
# 【L0652】开始执行可能抛错的“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0653】遍历 `range(args.policy_max_action_chunks)`，每次把当前元素放进 `chunk_index`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
        for chunk_index in range(args.policy_max_action_chunks):
# 【L0654】把右侧返回的多个结果按位置拆给 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。右侧的来源是：计算表达式 `episode_capture._render_images(robot, cube)`；`episode_capture` 表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；`_render_images` 表示本功能块中的 `_render_images` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            external_rgb, wrist_rgb = episode_capture._render_images(robot, cube)
# 【L0655】得到 `current_arm`，它在本项目中表示当前六个 RM65 关节角，单位 rad；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
            current_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy().astype(np.float32)
# 【L0656】得到 `current_gripper`，它在本项目中表示当前夹爪归一化位置，0 张开、1 闭合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
            current_gripper = np.array(
# 【L0657】这是上一行尚未闭合的参数、数组或字典内容：`[normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],`；`normalize_gripper` 表示夹爪相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request，共同完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                [normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],
# 【L0658】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                dtype=np.float32,
# 【L0659】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0660】开始构造一次在线 π0.5 请求。这个字典的键必须与 RM65Inputs 读取的键完全一致。
            observation = {
# 【L0661】把刚从 IsaacLab `robot.data.joint_pos` 读出的六个实际 RM65 关节角放入请求。
                "observation/joint_position": current_arm,
# 【L0662】把实际 4C2 主关节归一化为 0～1 的单元素数组后放入请求。
                "observation/gripper_position": current_gripper,
# 【L0663】把当前外部相机 RGB 帧放入请求；RM65Inputs 会将它映射到 `base_0_rgb`。
                "observation/external_image": external_rgb,
# 【L0664】把当前腕部相机 RGB 帧放入请求；RM65Inputs 会将它映射到有效腕部图像槽。
                "observation/wrist_image": wrist_rgb,
# 【L0665】把本 episode 的自然语言任务指令放入请求，使视觉和状态动作受语言条件约束。
                "prompt": args.episode_prompt,
# 【L0666】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0667】得到 `started`，它在本项目中表示本功能块中的 `started` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter()`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值。
            started = time.perf_counter()
# 【L0668】通过 WebSocket 调用 RM65 π0.5 policy；取出未来动作块并转成 float32 ndarray。正常形状为 `(10,7)`。
            raw_actions = np.asarray(client.infer(observation)["actions"], dtype=np.float32)
# 【L0669】对 `inference_latencies` 执行 `append`，把 `time.perf_counter() - started` 加入已有结果；该集合表示本功能块中的 `inference_latencies` 值，随后会用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            inference_latencies.append(time.perf_counter() - started)
# 【L0670】把模型原始动作块和当前六关节角交给 action guard；返回逐步限位/步长/夹爪裁剪后的动作与诊断。
            safe_actions, guard = guard_action_chunk(raw_actions, current_arm)
# 【L0671】用 `total_joint_limit_clamps + guard["joint_limit_clamp_count"]` 更新 `total_joint_limit_clamps` 原值；`total_joint_limit_clamps` 表示关节相关值，常用于累计步数、距离、损失或成功次数。
            total_joint_limit_clamps += guard["joint_limit_clamp_count"]
# 【L0672】用 `total_joint_step_clamps + guard["joint_step_clamp_count"]` 更新 `total_joint_step_clamps` 原值；`total_joint_step_clamps` 表示关节、步相关值，常用于累计步数、距离、损失或成功次数。
            total_joint_step_clamps += guard["joint_step_clamp_count"]
# 【L0673】用 `total_gripper_clamps + guard["gripper_clamp_count"]` 更新 `total_gripper_clamps` 原值；`total_gripper_clamps` 表示夹爪相关值，常用于累计步数、距离、损失或成功次数。
            total_gripper_clamps += guard["gripper_clamp_count"]
# 【L0674】用 `action_chunks + 1` 更新 `action_chunks` 原值；`action_chunks` 表示本 episode 已向 π0.5 请求的动作块数量，常用于累计步数、距离、损失或成功次数。
            action_chunks += 1
# 【L0675】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0676】决定本次重规划前最多执行多少个动作：取配置值与模型实际 horizon 的较小者，默认从 10 步中执行前 5 步。
            execute_count = min(args.policy_execute_actions_per_chunk, len(safe_actions))
# 【L0677】遍历 `enumerate(safe_actions[:execute_count])`，每次把当前元素放进 `action_index, action`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
            for action_index, action in enumerate(safe_actions[:execute_count]):
# 【L0678】取当前七维动作的前六维作为 RM65 关节绝对目标，转换到仿真 GPU 与 state 相同 dtype。
                state[:, arm_ids] = torch.as_tensor(
# 【L0679】把表达式/参数 `action[:6], device=sim.device, dtype=state.dtype` 接入当前完整语句；`action` 表示动作相关值；`device` 表示本功能块中的 `device` 值；`sim` 表示IsaacLab SimulationContext，负责物理时间步。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    action[:6], device=sim.device, dtype=state.dtype
# 【L0680】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0681】把策略夹爪归一化目标乘 0.865 rad，恢复为 4C2 主关节在 Isaac 中使用的角度目标。
                gripper_target_rad = float(action[6]) * 0.865
# 【L0682】把右侧结果写进 `state[:, gripper_ids]`（写入 `state[:, gripper_ids]` 指定的字段）；右侧具体做的是：计算表达式 `gripper_target_rad`；`gripper_target_rad` 表示夹爪、目标相关值。
                state[:, gripper_ids] = gripper_target_rad
# 【L0683】得到 `last_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(action[6])`；`action` 表示动作相关值。
                last_executed_gripper_target = float(action[6])
# 【L0684】得到 `minimum_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `min(` 的结果保存下来，供当前功能块后续使用。
                minimum_executed_gripper_target = min(
# 【L0685】把表达式/参数 `minimum_executed_gripper_target, last_executed_gripper_target` 接入当前完整语句；`minimum_executed_gripper_target` 表示夹爪、目标相关值；`last_executed_gripper_target` 表示夹爪、目标相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    minimum_executed_gripper_target, last_executed_gripper_target
# 【L0686】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0687】一个 policy 动作保持 `record_stride_steps` 个 240 Hz 物理步；默认 12 步，即每个动作持续约 0.05 秒。
                for _ in range(args.record_stride_steps):
# 【L0688】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
                    robot.set_joint_position_target(state)
# 【L0689】开始对 `episode_capture` 调用多行方法 `before_step`：调用 `episode_capture` 提供的 `before_step` 操作；具体参数写在随后几行，用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    episode_capture.before_step(
# 【L0690】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                        robot,
# 【L0691】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                        cube,
# 【L0692】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                        state,
# 【L0693】向上一行的函数调用或容器继续传入 `f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}"`；`f` 表示本功能块中的 `f` 值；`PI05_CHUNK_` 表示本功能块中的 `PI05_CHUNK_` 值；`chunk_index` 表示索引相关值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}",
# 【L0694】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    )
# 【L0695】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
                    robot.write_data_to_sim()
# 【L0696】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    cube.write_data_to_sim()
# 【L0697】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
                    sim.step(render=False)
# 【L0698】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
                    robot.update(sim.get_physics_dt())
# 【L0699】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
                    cube.update(sim.get_physics_dt())
# 【L0700】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
                    for contact_sensor in CONTACT_SENSORS.values():
# 【L0701】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        contact_sensor.update(sim.get_physics_dt())
# 【L0702】得到 `max_cube_z`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
                    max_cube_z = max(max_cube_z, float(cube.data.root_pos_w[0, 2].item()))
# 【L0703】用 `executed_actions + 1` 更新 `executed_actions` 原值；`executed_actions` 表示实际送进 Isaac 控制器的七维动作步数，常用于累计步数、距离、损失或成功次数。
                executed_actions += 1
# 【L0704】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0705】动作执行后读取方块在世界坐标中的实际 xyz，用新物理状态判断进展并准备下一轮重规划。
            current_cube = cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L0706】计算当前方块中心到目标中心的三维距离，单位米；小于 0.05 m 是成功候选条件之一。
            target_error = float(np.linalg.norm(current_cube - target_block_position))
# 【L0707】得到 `actual_gripper_normalized`，它在本项目中表示物理仿真实际值、夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            actual_gripper_normalized = normalize_gripper(
# 【L0708】对 `float(robot.data.joint_pos[0, gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0709】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0710】得到 `minimum_observed_gripper_normalized`，它在本项目中表示夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `min(` 的结果保存下来，供当前功能块后续使用。
            minimum_observed_gripper_normalized = min(
# 【L0711】把表达式/参数 `minimum_observed_gripper_normalized, actual_gripper_normalized` 接入当前完整语句；`minimum_observed_gripper_normalized` 表示夹爪、归一化相关值；`actual_gripper_normalized` 表示物理仿真实际值、夹爪、归一化相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                minimum_observed_gripper_normalized, actual_gripper_normalized
# 【L0712】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0713】得到 `gripper_open`，它在本项目中表示实际夹爪反馈是否低于校准张开阈值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            gripper_open = (
# 【L0714】把比较条件 `actual_gripper_normalized < args.policy_gripper_open_threshold` 接到上一行尚未结束的布尔表达式；`actual_gripper_normalized` 表示物理仿真实际值、夹爪、归一化相关值；`policy_gripper_open_threshold` 表示策略、夹爪相关值。比较结果共同决定“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”是否通过。
                actual_gripper_normalized < args.policy_gripper_open_threshold
# 【L0715】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0716】得到 `gripper_command_open`，它在本项目中表示最近一次真正执行的模型夹爪命令是否要求张开；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            gripper_command_open = (
# 【L0717】把表达式/参数 `last_executed_gripper_target is not None` 接入当前完整语句；`last_executed_gripper_target` 表示夹爪、目标相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                last_executed_gripper_target is not None
# 【L0718】把条件 `last_executed_gripper_target < args.policy_gripper_open_threshold` 用“并且”接到上一行判断中；按表达式 `last_executed_gripper_target < args.policy_gripper_open_threshold` 检查夹爪阈值或开合状态；该阈值决定 4C2 是否被视为已张开。所有连接条件共同决定是否进入后续分支。
                and last_executed_gripper_target < args.policy_gripper_open_threshold
# 【L0719】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0720】判断方块在本 episode 中的最高 z 是否比初始稳定 z 高 2 cm 以上，排除仅在桌面滑到目标的假成功。
            lifted = max_cube_z - float(settled_source_position[2].item()) > 0.02
# 【L0721】只有方块被抬起、到达目标、实际夹爪张开且最后执行的模型命令也要求张开，才累计一次成功候选。
            if lifted and target_error < 0.05 and gripper_open and gripper_command_open:
# 【L0722】用 `consecutive_candidate_chunks + 1` 更新 `consecutive_candidate_chunks` 原值；`consecutive_candidate_chunks` 表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数，常用于累计步数、距离、损失或成功次数。
                consecutive_candidate_chunks += 1
# 【L0723】前面的 `if/elif` 都不成立时走这里；在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中处理剩余输入或备用路径。
            else:
# 【L0724】得到 `consecutive_candidate_chunks`，它在本项目中表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
                consecutive_candidate_chunks = 0
# 【L0725】把 `` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
            print(
# 【L0726】提供文本片段 `"PI05_CHUNK="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "PI05_CHUNK="
# 【L0727】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
                + json.dumps(
# 【L0728】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    {
# 【L0729】定义字典/JSON 字段 `index`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `index` 数据；字段值来自 `chunk_index`，因此保存/传递的是这个表达式当前计算出的结果。
                        "index": chunk_index,
# 【L0730】定义字典/JSON 字段 `latency_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `latency_s` 数据；字段值来自 `inference_latencies[-1]`，因此保存/传递的是这个表达式当前计算出的结果。
                        "latency_s": inference_latencies[-1],
# 【L0731】定义字典/JSON 字段 `target_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_error_m` 数据；字段值来自 `target_error`，因此保存/传递的是这个表达式当前计算出的结果。
                        "target_error_m": target_error,
# 【L0732】定义字典/JSON 字段 `lifted`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `lifted` 数据；字段值来自 `lifted`，因此保存/传递的是这个表达式当前计算出的结果。
                        "lifted": lifted,
# 【L0733】定义字典/JSON 字段 `gripper_open`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_open` 数据；字段值来自 `gripper_open`，因此保存/传递的是这个表达式当前计算出的结果。
                        "gripper_open": gripper_open,
# 【L0734】定义字典/JSON 字段 `gripper_command_open`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_command_open` 数据；字段值来自 `gripper_command_open`，因此保存/传递的是这个表达式当前计算出的结果。
                        "gripper_command_open": gripper_command_open,
# 【L0735】定义字典/JSON 字段 `actual_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `actual_gripper_normalized` 数据；字段值来自 `actual_gripper_normalized`，因此保存/传递的是这个表达式当前计算出的结果。
                        "actual_gripper_normalized": actual_gripper_normalized,
# 【L0736】定义字典/JSON 字段 `last_executed_gripper_target`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `last_executed_gripper_target` 数据；字段值来自 `last_executed_gripper_target`，因此保存/传递的是这个表达式当前计算出的结果。
                        "last_executed_gripper_target": last_executed_gripper_target,
# 【L0737】定义字典/JSON 字段 `guard`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `guard` 数据；字段值来自 `guard`，因此保存/传递的是这个表达式当前计算出的结果。
                        "guard": guard,
# 【L0738】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    }
# 【L0739】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                ),
# 【L0740】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                flush=True,
# 【L0741】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0742】要求上述条件连续三个动作块成立，过滤物体瞬间经过目标或夹爪短暂抖动造成的假成功。
            if consecutive_candidate_chunks >= 3:
# 【L0743】把 `"PI05_STAGE=SUCCESS_CANDIDATE", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
                print("PI05_STAGE=SUCCESS_CANDIDATE", flush=True)
# 【L0744】得到 `release_postcondition_arm_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
                release_postcondition_arm_target = (
# 【L0745】对 `robot.data.joint_pos[0, arm_ids]` 调用 `detach().cpu().tolist()`：调用 `robot.data.joint_pos[0, arm_ids]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    robot.data.joint_pos[0, arm_ids].detach().cpu().tolist()
# 【L0746】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0747】把手臂目标锁定为当前实际六关节角，避免释放稳定验证期间继续追逐旧的模型动作。
                state[:, arm_ids] = robot.data.joint_pos[:, arm_ids].detach()
# 【L0748】把所有 4C2 关节目标设为 0，也就是完全张开；只有模型已连续选择释放时才运行到这里。
                state[:, gripper_ids] = 0.0
# 【L0749】得到 `release_postcondition_applied`，它在本项目中表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                release_postcondition_applied = True
# 【L0750】把 `"PI05_STAGE=RELEASE_POSTCONDITION_LATCHED", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
                print("PI05_STAGE=RELEASE_POSTCONDITION_LATCHED", flush=True)
# 【L0751】立即结束最近一层循环；在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L0752】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
    finally:
# 【L0753】对 `client._ws` 调用 `close()`：关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        client._ws.close()
# 【L0754】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0755】调用 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)
# 【L0756】得到 `settle_a`，它在本项目中表示本功能块中的 `settle_a` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    settle_a = cube.data.root_pos_w[0].clone()
# 【L0757】调用 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)
# 【L0758】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    final_position = cube.data.root_pos_w[0].clone()
# 【L0759】得到 `source_np`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `settled_source_position.detach().cpu().numpy()`；`settled_source_position` 表示源位置、位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    source_np = settled_source_position.detach().cpu().numpy()
# 【L0760】得到 `final_np`，它在本项目中表示本功能块中的 `final_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `final_position.detach().cpu().numpy()`；`final_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    final_np = final_position.detach().cpu().numpy()
# 【L0761】得到 `final_target_xy_error`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L0762】得到 `final_target_position_error`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L0763】得到 `source_to_target_distance`，它在本项目中表示源位置、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    source_to_target_distance = float(np.linalg.norm(final_np[:2] - source_np[:2]))
# 【L0764】得到 `lift_height`，它在本项目中表示本功能块中的 `lift_height` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max_cube_z - float(source_np[2])`；`max_cube_z` 表示任务方块相关值；`source_np` 表示源位置相关值。
    lift_height = max_cube_z - float(source_np[2])
# 【L0765】得到 `post_release_drift`，它在本项目中表示本功能块中的 `post_release_drift` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    post_release_drift = float(torch.linalg.vector_norm(final_position - settle_a).item())
# 【L0766】得到 `final_gripper`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
    final_gripper = normalize_gripper(
# 【L0767】对 `float(robot.data.joint_pos[0, gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0768】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0769】得到 `all_states_finite`，它在本项目中表示本功能块中的 `all_states_finite` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    all_states_finite = bool(
# 【L0770】对 `torch` 调用 `isfinite(robot.data.joint_pos).all()`：调用 `torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        torch.isfinite(robot.data.joint_pos).all()
# 【L0771】对 `and torch` 调用 `isfinite(cube.data.root_state_w).all()`：调用 `and torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        and torch.isfinite(cube.data.root_state_w).all()
# 【L0772】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0773】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    passed = bool(
# 【L0774】把比较条件 `action_chunks > 0` 接到上一行尚未结束的布尔表达式；`action_chunks` 表示本 episode 已向 π0.5 请求的动作块数量。比较结果共同决定“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”是否通过。
        action_chunks > 0
# 【L0775】把条件 `source_to_target_distance > 0.12` 用“并且”接到上一行判断中；判断 `source_to_target_distance > 0.12` 是否成立；`source_to_target_distance` 表示源位置、目标相关值。所有连接条件共同决定是否进入后续分支。
        and source_to_target_distance > 0.12
# 【L0776】把条件 `lift_height > 0.02` 用“并且”接到上一行判断中；判断 `lift_height > 0.02` 是否成立；`lift_height` 表示本功能块中的 `lift_height` 值。所有连接条件共同决定是否进入后续分支。
        and lift_height > 0.02
# 【L0777】把条件 `final_target_xy_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_xy_error < 0.05` 是否成立；`final_target_xy_error` 表示目标相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_xy_error < 0.05
# 【L0778】把条件 `final_target_position_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_position_error < 0.05` 是否成立；`final_target_position_error` 表示目标、位置相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_position_error < 0.05
# 【L0779】把条件 `post_release_drift < 0.02` 用“并且”接到上一行判断中；判断 `post_release_drift < 0.02` 是否成立；`post_release_drift` 表示本功能块中的 `post_release_drift` 值。所有连接条件共同决定是否进入后续分支。
        and post_release_drift < 0.02
# 【L0780】把条件 `release_postcondition_applied` 用“并且”接到上一行判断中；判断 `release_postcondition_applied` 是否成立；`release_postcondition_applied` 表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证。所有连接条件共同决定是否进入后续分支。
        and release_postcondition_applied
# 【L0781】把条件 `all_states_finite` 用“并且”接到上一行判断中；判断 `all_states_finite` 是否成立；`all_states_finite` 表示本功能块中的 `all_states_finite` 值。所有连接条件共同决定是否进入后续分支。
        and all_states_finite
# 【L0782】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0783】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0784】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：计算表达式 `passed`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    episode_recorder.metadata["task_success"] = passed
# 【L0785】把右侧结果写进 `episode_recorder.metadata["pi05_used"]`（写入 `episode_recorder.metadata["pi05_used"]` 指定的字段）；右侧具体做的是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["pi05_used"] = True
# 【L0786】把右侧结果写进 `episode_recorder.metadata["training_ready"]`（写入 `episode_recorder.metadata["training_ready"]` 指定的字段）；右侧具体做的是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["training_ready"] = False
# 【L0787】把右侧结果写进 `episode_recorder.metadata["evaluation_only"]`（写入 `episode_recorder.metadata["evaluation_only"]` 指定的字段）；右侧具体做的是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["evaluation_only"] = True
# 【L0788】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
    manifest = episode_recorder.save()
# 【L0789】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(episode_recorder.output_dir, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值。
    validation = validate_episode(episode_recorder.output_dir, require_images=True)
# 【L0790】判断 `validation["status"] != "pass"` 是否成立；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
    if validation["status"] != "pass":
# 【L0791】主动抛出 `RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")` 并停止当前路径；说明当前输入违反“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")
# 【L0792】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0793】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L0794】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L0795】定义字典/JSON 字段 `pi05_used`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `pi05_used` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": True,
# 【L0796】定义字典/JSON 字段 `expert`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `expert` 数据；字段值来自 `None`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": None,
# 【L0797】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L0798】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `args.policy_checkpoint_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_checkpoint_id": args.policy_checkpoint_id,
# 【L0799】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `args.episode_prompt`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": args.episode_prompt,
# 【L0800】定义字典/JSON 字段 `action_chunks`，它表示向 π0.5 发起推理的次数；字段值来自 `action_chunks`，因此保存/传递的是这个表达式当前计算出的结果。
        "action_chunks": action_chunks,
# 【L0801】定义字典/JSON 字段 `executed_actions`，它表示真正送入 Isaac 控制器的动作步数；字段值来自 `executed_actions`，因此保存/传递的是这个表达式当前计算出的结果。
        "executed_actions": executed_actions,
# 【L0802】定义字典/JSON 字段 `policy_action_horizon`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_action_horizon` 数据；字段值来自 `int(len(raw_actions)) if action_chunks else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_action_horizon": int(len(raw_actions)) if action_chunks else None,
# 【L0803】定义字典/JSON 字段 `controller_config`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `controller_config` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "controller_config": {
# 【L0804】定义字典/JSON 字段 `policy_max_action_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_max_action_chunks` 数据；字段值来自 `args.policy_max_action_chunks`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_max_action_chunks": args.policy_max_action_chunks,
# 【L0805】定义字典/JSON 字段 `policy_execute_actions_per_chunk`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_execute_actions_per_chunk` 数据；字段值来自 `args.policy_execute_actions_per_chunk`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_execute_actions_per_chunk": args.policy_execute_actions_per_chunk,
# 【L0806】定义字典/JSON 字段 `record_stride_steps`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `record_stride_steps` 数据；字段值来自 `args.record_stride_steps`，因此保存/传递的是这个表达式当前计算出的结果。
            "record_stride_steps": args.record_stride_steps,
# 【L0807】定义字典/JSON 字段 `physics_dt_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `physics_dt_s` 数据；字段值来自 `sim.get_physics_dt()`，因此保存/传递的是这个表达式当前计算出的结果。
            "physics_dt_s": sim.get_physics_dt(),
# 【L0808】定义字典/JSON 字段 `executed_action_hold_seconds`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `executed_action_hold_seconds` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "executed_action_hold_seconds": (
# 【L0809】对 `args.record_stride_steps * sim` 调用 `get_physics_dt()`：调用 `args.record_stride_steps * sim` 提供的 `get_physics_dt` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                args.record_stride_steps * sim.get_physics_dt()
# 【L0810】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0811】定义字典/JSON 字段 `success_candidate_required_consecutive_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `success_candidate_required_consecutive_chunks` 数据；字段值来自 `3`，因此保存/传递的是这个表达式当前计算出的结果。
            "success_candidate_required_consecutive_chunks": 3,
# 【L0812】定义字典/JSON 字段 `policy_gripper_open_threshold`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_gripper_open_threshold` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_gripper_open_threshold": args.policy_gripper_open_threshold,
# 【L0813】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0814】定义字典/JSON 字段 `inference_latency_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `inference_latency_s` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "inference_latency_s": {
# 【L0815】定义字典/JSON 字段 `first`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `first` 数据；字段值来自 `inference_latencies[0] if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "first": inference_latencies[0] if inference_latencies else None,
# 【L0816】定义字典/JSON 字段 `mean`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `mean` 数据；字段值来自 `float(np.mean(inference_latencies)) if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "mean": float(np.mean(inference_latencies)) if inference_latencies else None,
# 【L0817】定义字典/JSON 字段 `maximum`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `maximum` 数据；字段值来自 `float(np.max(inference_latencies)) if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "maximum": float(np.max(inference_latencies)) if inference_latencies else None,
# 【L0818】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0819】定义字典/JSON 字段 `guard_totals`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `guard_totals` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "guard_totals": {
# 【L0820】定义字典/JSON 字段 `joint_limit_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `joint_limit_clamp_count` 数据；字段值来自 `total_joint_limit_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_limit_clamp_count": total_joint_limit_clamps,
# 【L0821】定义字典/JSON 字段 `joint_step_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `joint_step_clamp_count` 数据；字段值来自 `total_joint_step_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_step_clamp_count": total_joint_step_clamps,
# 【L0822】定义字典/JSON 字段 `gripper_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_clamp_count` 数据；字段值来自 `total_gripper_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_clamp_count": total_gripper_clamps,
# 【L0823】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0824】定义字典/JSON 字段 `low_level_release_postcondition`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `low_level_release_postcondition` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "low_level_release_postcondition": {
# 【L0825】定义字典/JSON 字段 `applied`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `applied` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "applied": release_postcondition_applied,
# 【L0826】定义字典/JSON 字段 `trigger`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `trigger` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "trigger": (
# 【L0827】提供文本片段 `"three consecutive chunks with lift, target error below 0.05 m, "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "three consecutive chunks with lift, target error below 0.05 m, "
# 【L0828】提供文本片段 `"actual gripper and executed gripper target below the calibrated threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "actual gripper and executed gripper target below the calibrated threshold"
# 【L0829】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0830】定义字典/JSON 字段 `open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `open_threshold_normalized` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L0831】定义字典/JSON 字段 `arm_target_latched_to_actual_rad`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `arm_target_latched_to_actual_rad` 数据；字段值来自 `release_postcondition_arm_target`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_target_latched_to_actual_rad": release_postcondition_arm_target,
# 【L0832】定义字典/JSON 字段 `gripper_target_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_target_normalized` 数据；字段值来自 `0.0 if release_postcondition_applied else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_target_normalized": 0.0 if release_postcondition_applied else None,
# 【L0833】定义字典/JSON 字段 `verification_settle_steps`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `verification_settle_steps` 数据；字段值来自 `240`，因此保存/传递的是这个表达式当前计算出的结果。
            "verification_settle_steps": 240,
# 【L0834】定义字典/JSON 字段 `model_selected_release`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_selected_release` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_selected_release": release_postcondition_applied,
# 【L0835】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0836】定义字典/JSON 字段 `release_verification`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `release_verification` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_verification": {
# 【L0837】定义字典/JSON 字段 `verified`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `verified` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "verified": release_postcondition_applied,
# 【L0838】定义字典/JSON 字段 `required_consecutive_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `required_consecutive_chunks` 数据；字段值来自 `3`，因此保存/传递的是这个表达式当前计算出的结果。
            "required_consecutive_chunks": 3,
# 【L0839】定义字典/JSON 字段 `open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `open_threshold_normalized` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L0840】定义字典/JSON 字段 `minimum_observed_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `minimum_observed_gripper_normalized` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_observed_gripper_normalized": (
# 【L0841】声明/传入参数 `minimum_observed_gripper_normalized`；在本项目中它表示夹爪、归一化相关值。
                minimum_observed_gripper_normalized
# 【L0842】判断 `np.isfinite(minimum_observed_gripper_normalized)` 是否成立；`isfinite` 表示本功能块中的 `isfinite` 值；`minimum_observed_gripper_normalized` 表示夹爪、归一化相关值
                if np.isfinite(minimum_observed_gripper_normalized)
# 【L0843】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else None
# 【L0844】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0845】定义字典/JSON 字段 `minimum_executed_gripper_target`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `minimum_executed_gripper_target` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_executed_gripper_target": (
# 【L0846】声明/传入参数 `minimum_executed_gripper_target`；在本项目中它表示夹爪、目标相关值。
                minimum_executed_gripper_target
# 【L0847】判断 `np.isfinite(minimum_executed_gripper_target)` 是否成立；`isfinite` 表示本功能块中的 `isfinite` 值；`minimum_executed_gripper_target` 表示夹爪、目标相关值
                if np.isfinite(minimum_executed_gripper_target)
# 【L0848】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else None
# 【L0849】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0850】定义字典/JSON 字段 `final_gripper_normalized_is_diagnostic_only`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_gripper_normalized_is_diagnostic_only` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_gripper_normalized_is_diagnostic_only": True,
# 【L0851】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0852】定义字典/JSON 字段 `source_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_position_m` 数据；字段值来自 `source_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_position_m": source_np.tolist(),
# 【L0853】定义字典/JSON 字段 `target_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_position_m": target_block_position.tolist(),
# 【L0854】定义字典/JSON 字段 `final_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_position_m` 数据；字段值来自 `final_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_position_m": final_np.tolist(),
# 【L0855】定义字典/JSON 字段 `source_to_target_xy_distance_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_to_target_xy_distance_m` 数据；字段值来自 `source_to_target_distance`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L0856】定义字典/JSON 字段 `block_lift_height_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `block_lift_height_m` 数据；字段值来自 `lift_height`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_lift_height_m": lift_height,
# 【L0857】定义字典/JSON 字段 `final_target_xy_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_xy_error_m` 数据；字段值来自 `final_target_xy_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_xy_error_m": final_target_xy_error,
# 【L0858】定义字典/JSON 字段 `final_target_position_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_position_error_m` 数据；字段值来自 `final_target_position_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_position_error_m": final_target_position_error,
# 【L0859】定义字典/JSON 字段 `post_release_drift_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `post_release_drift_m` 数据；字段值来自 `post_release_drift`，因此保存/传递的是这个表达式当前计算出的结果。
        "post_release_drift_m": post_release_drift,
# 【L0860】定义字典/JSON 字段 `final_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_gripper_normalized` 数据；字段值来自 `final_gripper`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_gripper_normalized": final_gripper,
# 【L0861】定义字典/JSON 字段 `all_states_finite`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `all_states_finite` 数据；字段值来自 `all_states_finite`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_states_finite": all_states_finite,
# 【L0862】定义字典/JSON 字段 `criteria`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `criteria` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "criteria": {
# 【L0863】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_to_target_xy_distance_m_gt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L0864】定义字典/JSON 字段 `block_lift_height_m_gt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `block_lift_height_m_gt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m_gt": 0.02,
# 【L0865】定义字典/JSON 字段 `final_target_xy_error_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_xy_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_xy_error_m_lt": 0.05,
# 【L0866】定义字典/JSON 字段 `final_target_position_error_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_position_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_position_error_m_lt": 0.05,
# 【L0867】定义字典/JSON 字段 `post_release_drift_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `post_release_drift_m_lt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "post_release_drift_m_lt": 0.02,
# 【L0868】定义字典/JSON 字段 `model_selected_release_verified`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_selected_release_verified` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_selected_release_verified": True,
# 【L0869】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0870】定义字典/JSON 字段 `episode`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `episode` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode": {
# 【L0871】定义字典/JSON 字段 `directory`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
            "directory": str(episode_recorder.output_dir),
# 【L0872】定义字典/JSON 字段 `frame_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `frame_count` 数据；字段值来自 `manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": manifest["frame_count"],
# 【L0873】定义字典/JSON 字段 `validation`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `validation` 数据；字段值来自 `validation`，因此保存/传递的是这个表达式当前计算出的结果。
            "validation": validation,
# 【L0874】定义字典/JSON 字段 `evaluation_only`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `evaluation_only` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "evaluation_only": True,
# 【L0875】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0876】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    }
# 【L0877】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L0878】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L0879】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L0880】把 `f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print(f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}", flush=True)
# 【L0881】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L0882】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0883】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0884】定义函数 `contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60)`；调用者把参数交给它完成“接触力统计与平台生成工具”，后面的缩进代码是具体实现。
def contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60) -> dict[str, float]:
# 【L0885】说明字符串 `Return peak, current, and recent sustained cube-contact force magnitudes.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Return peak, current, and recent sustained cube-contact force magnitudes."""
# 【L0886】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0887】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w` 表示力相关值。
    current = contact_sensor.data.force_matrix_w
# 【L0888】得到 `history`，它在本项目中表示本功能块中的 `history` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w_history`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w_history` 表示力相关值。
    history = contact_sensor.data.force_matrix_w_history
# 【L0889】检查 `current is None or history is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if current is None or history is None:
# 【L0890】结束当前函数并把 `{"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}` 交回调用者；这个值的含义是：计算表达式 `{"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}`；`peak_n` 表示本功能块中的 `peak_n` 值；`current_n` 表示当前值相关值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。
        return {"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}
# 【L0891】得到 `current_n`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    current_n = float(torch.linalg.vector_norm(current, dim=-1).max())
# 【L0892】得到 `history_norm`，它在本项目中表示本功能块中的 `history_norm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    history_norm = torch.linalg.vector_norm(history, dim=-1)
# 【L0893】得到 `peak_n`，它在本项目中表示本功能块中的 `peak_n` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(history_norm.max())`；`history_norm` 表示本功能块中的 `history_norm` 值。
    peak_n = float(history_norm.max())
# 【L0894】得到 `recent`，它在本项目中表示本功能块中的 `recent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(`；`history_norm` 表示本功能块中的 `history_norm` 值；`recent_steps` 表示步数相关值；`shape` 表示本功能块中的 `shape` 值。
    recent = history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(
# 【L0895】把表达式/参数 `min(recent_steps, history_norm.shape[1]), -1` 接入当前完整语句；`recent_steps` 表示步数相关值；`history_norm` 表示本功能块中的 `history_norm` 值；`shape` 表示本功能块中的 `shape` 值。在“接触力统计与平台生成工具”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        min(recent_steps, history_norm.shape[1]), -1
# 【L0896】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L0897】得到 `recent_mean_n`，它在本项目中表示本功能块中的 `recent_mean_n` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(recent.max(dim=1).values.mean())`；`recent` 表示本功能块中的 `recent` 值；`dim` 表示本功能块中的 `dim` 值；`values` 表示本功能块中的 `values` 值。
    recent_mean_n = float(recent.max(dim=1).values.mean())
# 【L0898】结束当前函数并把 `{"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}` 交回调用者；这个值的含义是：计算表达式 `{"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}`；`peak_n` 表示本功能块中的 `peak_n` 值；`current_n` 表示当前值相关值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。
    return {"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}
# 【L0899】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0900】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0901】定义函数 `spawn_platform(参数在后续行继续)`；调用者把参数交给它完成“接触力统计与平台生成工具”，后面的缩进代码是具体实现。
def spawn_platform(
# 【L0902】声明/传入参数 `path`，类型提示为 `str`；在本项目中它表示路径相关值。
    path: str,
# 【L0903】声明/传入参数 `position`，类型提示为 `np.ndarray`；在本项目中它表示位置相关值。
    position: np.ndarray,
# 【L0904】向上一行的函数调用或容器继续传入 `size: tuple[float, float, float]`；`size` 表示本功能块中的 `size` 值，它参与“接触力统计与平台生成工具”。
    size: tuple[float, float, float],
# 【L0905】向上一行的函数调用或容器继续传入 `color: tuple[float, float, float]`；`color` 表示本功能块中的 `color` 值，它参与“接触力统计与平台生成工具”。
    color: tuple[float, float, float],
# 【L0906】得到 `orientation`，它在本项目中表示本功能块中的 `orientation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    orientation: tuple[float, float, float, float] | None = None,
# 【L0907】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“接触力统计与平台生成工具”。
) -> None:
# 【L0908】得到 `cfg`，它在本项目中表示本功能块中的 `cfg` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.CuboidCfg(`；`sim_utils` 表示仿真相关值；`CuboidCfg` 表示本功能块中的 `CuboidCfg` 值。
    cfg = sim_utils.CuboidCfg(
# 【L0909】给上一层函数/配置构造器的命名参数 `size` 传入 `size`；该参数在本项目中表示本功能块中的 `size` 值，会参与“接触力统计与平台生成工具”。
        size=size,
# 【L0910】给上一层函数/配置构造器的命名参数 `collision_props` 传入 `sim_utils.CollisionPropertiesCfg()`；该参数在本项目中表示本功能块中的 `collision_props` 值，会参与“接触力统计与平台生成工具”。
        collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L0911】给上一层函数/配置构造器的命名参数 `visual_material` 传入 `sim_utils.PreviewSurfaceCfg(diffuse_color=color)`；该参数在本项目中表示本功能块中的 `visual_material` 值，会参与“接触力统计与平台生成工具”。
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
# 【L0912】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
        physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L0913】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.0`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“接触力统计与平台生成工具”。
            static_friction=1.0,
# 【L0914】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `0.8`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“接触力统计与平台生成工具”。
            dynamic_friction=0.8,
# 【L0915】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“接触力统计与平台生成工具”。
            restitution=0.0,
# 【L0916】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“接触力统计与平台生成工具”。
            friction_combine_mode="max",
# 【L0917】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
        ),
# 【L0918】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L0919】得到 `kwargs`，它在本项目中表示本功能块中的 `kwargs` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{"translation": tuple(position)}`；`translation` 表示本功能块中的 `translation` 值；`position` 表示位置相关值。
    kwargs = {"translation": tuple(position)}
# 【L0920】检查 `orientation is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if orientation is not None:
# 【L0921】把右侧结果写进 `kwargs["orientation"]`（写入 `kwargs["orientation"]` 指定的字段）；右侧具体做的是：计算表达式 `orientation`；`orientation` 表示本功能块中的 `orientation` 值。
        kwargs["orientation"] = orientation
# 【L0922】对 `cfg` 调用 `func(path, cfg, **kwargs)`：调用 `cfg` 提供的 `func` 操作。本行产生的修改/返回值服务于“接触力统计与平台生成工具”。
    cfg.func(path, cfg, **kwargs)
# 【L0923】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0924】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0925】定义函数 `main()`；调用者把参数交给它完成“主函数输入文件和参数范围校验”，后面的缩进代码是具体实现。
def main() -> int:
# 【L0926】得到 `usd`，它在本项目中表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.usd.expanduser().resolve()`；`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    usd = args.usd.expanduser().resolve()
# 【L0927】得到 `urdf`，它在本项目中表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.urdf.expanduser().resolve()`；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    urdf = args.urdf.expanduser().resolve()
# 【L0928】得到 `description`，它在本项目中表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.description.expanduser().resolve()`；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    description = args.description.expanduser().resolve()
# 【L0929】得到 `output`，它在本项目中表示输出文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.output.expanduser().resolve()`；`output` 表示输出文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    output = args.output.expanduser().resolve()
# 【L0930】得到 `missing`，它在本项目中表示本功能块中的 `missing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[str(path) for path in (usd, urdf, description) if not path.is_file()]`；`path` 表示路径相关值；`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径。
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
# 【L0931】判断 `missing` 是否成立；`missing` 表示本功能块中的 `missing` 值
    if missing:
# 【L0932】主动抛出 `FileNotFoundError(f"missing required files: {missing}")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(f"missing required files: {missing}")
# 【L0933】判断 `abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2` 是否成立；`abs` 表示本功能块中的 `abs` 值；`transfer_joint_1_rad` 表示关节相关值
    if abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2:
# 【L0934】主动抛出 `ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")
# 【L0935】判断 `not 0.0 <= args.robot_base_z_m <= 0.8` 是否成立；`robot_base_z_m` 表示本功能块中的 `robot_base_z_m` 值
    if not 0.0 <= args.robot_base_z_m <= 0.8:
# 【L0936】主动抛出 `ValueError("--robot-base-z-m must be between 0 and 0.8")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--robot-base-z-m must be between 0 and 0.8")
# 【L0937】判断 `min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0` 是否成立；`arm_effort_limit_sim` 表示仿真相关值；`arm_stiffness` 表示本功能块中的 `arm_stiffness` 值；`arm_damping` 表示本功能块中的 `arm_damping` 值
    if min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0:
# 【L0938】主动抛出 `ValueError("arm actuator effort, stiffness, and damping must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("arm actuator effort, stiffness, and damping must be positive")
# 【L0939】判断 `min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0` 是否成立；`gripper_effort_limit_sim` 表示夹爪、仿真相关值；`gripper_stiffness` 表示夹爪相关值；`gripper_damping` 表示夹爪相关值
    if min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0:
# 【L0940】主动抛出 `ValueError("gripper actuator effort, stiffness, and damping must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("gripper actuator effort, stiffness, and damping must be positive")
# 【L0941】判断 `not 0.1 <= args.gripper_close_target_rad <= 1.0` 是否成立；`gripper_close_target_rad` 表示夹爪、目标相关值
    if not 0.1 <= args.gripper_close_target_rad <= 1.0:
# 【L0942】主动抛出 `ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")
# 【L0943】判断 `not 0.01 <= args.pregrasp_distance_m <= 0.10` 是否成立；`pregrasp_distance_m` 表示预抓取位姿到实际抓取位姿之间的直线距离，单位米
    if not 0.01 <= args.pregrasp_distance_m <= 0.10:
# 【L0944】主动抛出 `ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")
# 【L0945】判断 `abs(args.grasp_world_offset_x_m) > 0.08` 是否成立；`abs` 表示本功能块中的 `abs` 值；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值
    if abs(args.grasp_world_offset_x_m) > 0.08:
# 【L0946】主动抛出 `ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")
# 【L0947】判断 `abs(args.grasp_world_offset_z_m) > 0.08` 是否成立；`abs` 表示本功能块中的 `abs` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值
    if abs(args.grasp_world_offset_z_m) > 0.08:
# 【L0948】主动抛出 `ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")
# 【L0949】判断 `abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04` 是否成立；`abs` 表示本功能块中的 `abs` 值；`source_offset_x_m` 表示源位置相关值；`source_offset_y_m` 表示源位置相关值
    if abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04:
# 【L0950】主动抛出 `ValueError("source x/y offsets must each be between -0.04 and 0.04 m")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("source x/y offsets must each be between -0.04 and 0.04 m")
# 【L0951】判断 `abs(args.top_down_yaw_rad) > np.pi` 是否成立；`abs` 表示本功能块中的 `abs` 值；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值；`pi` 表示本功能块中的 `pi` 值
    if abs(args.top_down_yaw_rad) > np.pi:
# 【L0952】主动抛出 `ValueError("--top-down-yaw-rad must be between -pi and pi")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-yaw-rad must be between -pi and pi")
# 【L0953】判断 `not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0)` 是否成立；`top_down_tilt_rad` 表示本功能块中的 `top_down_tilt_rad` 值；`deg2rad` 表示本功能块中的 `deg2rad` 值
    if not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0):
# 【L0954】主动抛出 `ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")
# 【L0955】判断 `not 1 <= args.top_down_ik_multistart <= 512` 是否成立；`top_down_ik_multistart` 表示本功能块中的 `top_down_ik_multistart` 值
    if not 1 <= args.top_down_ik_multistart <= 512:
# 【L0956】主动抛出 `ValueError("--top-down-ik-multistart must be between 1 and 512")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-ik-multistart must be between 1 and 512")
# 【L0957】判断 `not 0.0 <= args.top_down_blend <= 1.0` 是否成立；`top_down_blend` 表示本功能块中的 `top_down_blend` 值
    if not 0.0 <= args.top_down_blend <= 1.0:
# 【L0958】主动抛出 `ValueError("--top-down-blend must be between 0 and 1")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-blend must be between 0 and 1")
# 【L0959】判断 `not 0.02 <= args.cartesian_lift_height_m <= 0.15` 是否成立；`cartesian_lift_height_m` 表示本功能块中的 `cartesian_lift_height_m` 值
    if not 0.02 <= args.cartesian_lift_height_m <= 0.15:
# 【L0960】主动抛出 `ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")
# 【L0961】判断 `not 0.03 <= args.release_clearance_m <= 0.20` 是否成立；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值
    if not 0.03 <= args.release_clearance_m <= 0.20:
# 【L0962】主动抛出 `ValueError("--release-clearance-m must be between 0.03 and 0.20")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--release-clearance-m must be between 0.03 and 0.20")
# 【L0963】判断 `not 0.0 <= args.release_separation_assist_m <= 0.20` 是否成立；`release_separation_assist_m` 表示本功能块中的 `release_separation_assist_m` 值
    if not 0.0 <= args.release_separation_assist_m <= 0.20:
# 【L0964】主动抛出 `ValueError("--release-separation-assist-m must be between 0.0 and 0.20")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--release-separation-assist-m must be between 0.0 and 0.20")
# 【L0965】判断 `not 0.03 <= args.place_descent_distance_m <= 0.13` 是否成立；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值
    if not 0.03 <= args.place_descent_distance_m <= 0.13:
# 【L0966】主动抛出 `ValueError("--place-descent-distance-m must be between 0.03 and 0.13")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--place-descent-distance-m must be between 0.03 and 0.13")
# 【L0967】判断 `not 30 <= args.place_waypoint_steps <= 240` 是否成立；`place_waypoint_steps` 表示步数相关值
    if not 30 <= args.place_waypoint_steps <= 240:
# 【L0968】主动抛出 `ValueError("--place-waypoint-steps must be between 30 and 240")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--place-waypoint-steps must be between 30 and 240")
# 【L0969】判断 `not 1 <= args.record_stride_steps <= 240` 是否成立；`record_stride_steps` 表示每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长
    if not 1 <= args.record_stride_steps <= 240:
# 【L0970】主动抛出 `ValueError("--record-stride-steps must be between 1 and 240")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-stride-steps must be between 1 and 240")
# 【L0971】判断 `not args.episode_prompt.strip()` 是否成立；`episode_prompt` 表示当前 episode 发送给 π0.5 的自然语言任务指令；`strip` 表示本功能块中的 `strip` 值
    if not args.episode_prompt.strip():
# 【L0972】主动抛出 `ValueError("--episode-prompt must not be empty")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--episode-prompt must not be empty")
# 【L0973】检查 `args.record_episode_dir is not None and (`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.record_episode_dir is not None and (
# 【L0974】把表达式/参数 `args.diagnose_approach_only or args.diagnose_kinematics_only` 接入当前完整语句；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值。在“主函数输入文件和参数范围校验”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        args.diagnose_approach_only or args.diagnose_kinematics_only
# 【L0975】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“主函数输入文件和参数范围校验”。
    ):
# 【L0976】主动抛出 `ValueError("episode recording is available only for a complete pick-and-place run")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("episode recording is available only for a complete pick-and-place run")
# 【L0977】检查 `args.record_images and args.record_episode_dir is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if args.record_images and args.record_episode_dir is None:
# 【L0978】主动抛出 `ValueError("--record-images requires --record-episode-dir")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-images requires --record-episode-dir")
# 【L0979】判断 `args.record_images and not getattr(args, "enable_cameras", False)` 是否成立；`record_images` 表示本功能块中的 `record_images` 值；`getattr` 表示本功能块中的 `getattr` 值；`enable_cameras` 表示本功能块中的 `enable_cameras` 值
    if args.record_images and not getattr(args, "enable_cameras", False):
# 【L0980】主动抛出 `ValueError("--record-images requires the AppLauncher flag --enable_cameras")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-images requires the AppLauncher flag --enable_cameras")
# 【L0981】检查 `args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None)`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None):
# 【L0982】主动抛出 `ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")
# 【L0983】判断 `args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only)` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值
    if args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only):
# 【L0984】主动抛出 `ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")
# 【L0985】判断 `args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1` 是否成立；`policy_max_action_chunks` 表示策略、动作相关值；`policy_execute_actions_per_chunk` 表示策略、动作序列相关值
    if args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1:
# 【L0986】主动抛出 `ValueError("policy chunk counts must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy chunk counts must be positive")
# 【L0987】空行：分隔“主函数输入文件和参数范围校验”中的逻辑段，让结构更容易看清。

# 【L0988】得到 `requested_pregrasp_distance_m`，它在本项目中表示本功能块中的 `requested_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.pregrasp_distance_m`；`pregrasp_distance_m` 表示预抓取位姿到实际抓取位姿之间的直线距离，单位米。
    requested_pregrasp_distance_m = args.pregrasp_distance_m
# 【L0989】得到 `effective_pregrasp_distance_m`，它在本项目中表示本功能块中的 `effective_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `requested_pregrasp_distance_m`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值。
    effective_pregrasp_distance_m = requested_pregrasp_distance_m
# 【L0990】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
    grasp_arm = np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L0991】得到 `lift_arm`，它在本项目中表示本功能块中的 `lift_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
    lift_arm = np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L0992】得到 `source_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    source_block_position = SOURCE_BLOCK_POSITION.copy()
# 【L0993】得到 `source_block_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64`（源位置方块/平台的任务常量），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    source_block_quaternion = np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L0994】判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值
    if args.natural_source_gravity:
# 【L0995】把右侧结果写进 `source_block_position[2]`（写入 `source_block_position[2]` 指定的字段）；右侧具体做的是：计算表达式 `SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0`；`SOURCE_PLATFORM_TOP_Z` 表示源位置方块/平台的任务常量；`BLOCK_SIZE` 表示本功能块中的 `BLOCK_SIZE` 值。
        source_block_position[2] = SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L0996】得到 `source_block_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
        source_block_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
# 【L0997】得到 `nominal_source_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    nominal_source_block_position = source_block_position.copy()
# 【L0998】调用 `np.array`：创建 NumPy 数组；本行实际操作 `source_block_position[:2] += np.array(`。`source_block_position` 表示源位置、位置相关值；`array` 表示本功能块中的 `array` 值。
    source_block_position[:2] += np.array(
# 【L0999】这是上一行尚未闭合的参数、数组或字典内容：`[args.source_offset_x_m, args.source_offset_y_m], dtype=np.float64`；`source_offset_x_m` 表示源位置相关值；`source_offset_y_m` 表示源位置相关值；`dtype` 表示本功能块中的 `dtype` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [args.source_offset_x_m, args.source_offset_y_m], dtype=np.float64
# 【L1000】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1001】得到 `robot_base_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`robot_base_z_m` 表示本功能块中的 `robot_base_z_m` 值；`dtype` 表示本功能块中的 `dtype` 值。
    robot_base_position = np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)
# 【L1002】得到 `source_block_position_base`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `source_block_position - robot_base_position`；`source_block_position` 表示源位置、位置相关值；`robot_base_position` 表示位置相关值。
    source_block_position_base = source_block_position - robot_base_position
# 【L1003】得到 `lula`，它在本项目中表示NVIDIA Lula 运动学求解器实例；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：用 RM65 URDF 和 robot description 创建 Lula 正/逆运动学求解器。
    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
# 【L1004】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1005】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    grasp_ik_numerical_seed = grasp_arm.copy()
# 【L1006】判断 `args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0` 是否成立；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值
    if args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0:
# 【L1007】得到 `offset_target_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_position + np.array(`；`grasp_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        offset_target_position = grasp_link_position + np.array(
# 【L1008】这是上一行尚未闭合的参数、数组或字典内容：`[args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64`；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值；`dtype` 表示本功能块中的 `dtype` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64
# 【L1009】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1010】把右侧返回的多个结果按位置拆给 `offset_grasp_arm, success`；`offset_grasp_arm` 表示本功能块中的 `offset_grasp_arm` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        offset_grasp_arm, success = lula.compute_inverse_kinematics(
# 【L1011】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1012】声明/传入参数 `offset_target_position`；在本项目中它表示目标、位置相关值。
            offset_target_position,
# 【L1013】给上一层函数/配置构造器的命名参数 `target_orientation` 传入 `None`；该参数在本项目中表示目标相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1014】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `grasp_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1015】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1016】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1017】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1018】主动抛出 `RuntimeError("Lula failed to solve the requested grasp world offset")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the requested grasp world offset")
# 【L1019】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `offset_grasp_arm, dtype=np.float64`（本功能块中的 `offset_grasp_arm, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        grasp_ik_numerical_seed = np.asarray(offset_grasp_arm, dtype=np.float64)
# 【L1020】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
        grasp_arm = closest_equivalent_rm65_solution(
# 【L1021】把表达式/参数 `lula, grasp_ik_numerical_seed, grasp_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`grasp_ik_numerical_seed` 表示本功能块中的 `grasp_ik_numerical_seed` 值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            lula, grasp_ik_numerical_seed, grasp_arm
# 【L1022】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1023】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1024】得到 `reference_block_from_link_local`，它在本项目中表示机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_rotation.T @ (`；`grasp_link_rotation` 表示机器人连杆、旋转相关值；`T` 表示本功能块中的 `T` 值。
    reference_block_from_link_local = grasp_link_rotation.T @ (
# 【L1025】把表达式/参数 `nominal_source_block_position - grasp_link_position` 接入当前完整语句；`nominal_source_block_position` 表示源位置、位置相关值；`grasp_link_position` 表示机器人连杆、位置相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        nominal_source_block_position - grasp_link_position
# 【L1026】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1027】得到 `top_down_ik_seed_index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    top_down_ik_seed_index = None
# 【L1028】得到 `precomputed_retreat_waypoints`，它在本项目中表示本功能块中的 `precomputed_retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    precomputed_retreat_waypoints: list[np.ndarray] | None = None
# 【L1029】判断 `args.grasp_orientation_mode == "top_down"` 是否成立；`grasp_orientation_mode` 表示本功能块中的 `grasp_orientation_mode` 值；`top_down` 表示本功能块中的 `top_down` 值
    if args.grasp_orientation_mode == "top_down":
# 【L1030】得到 `calibrated_reference_link_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        calibrated_reference_link_position = (
# 【L1031】声明/传入参数 `source_block_position_base`；在本项目中它表示源位置、位置相关值。
            source_block_position_base
# 【L1032】把运算项 `- grasp_link_rotation @ reference_block_from_link_local` 接到上一行未结束的数学公式；`grasp_link_rotation` 表示机器人连杆、旋转相关值；`reference_block_from_link_local` 表示机器人连杆相关值，整条公式用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            - grasp_link_rotation @ reference_block_from_link_local
# 【L1033】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1034】把右侧返回的多个结果按位置拆给 `top_down_link_position, top_down_rotation, reference_block_from_link_local`；`top_down_link_position` 表示机器人连杆、位置相关值；`top_down_rotation` 表示旋转相关值；`reference_block_from_link_local` 表示机器人连杆相关值。右侧的来源是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        top_down_link_position, top_down_rotation, reference_block_from_link_local = (
# 【L1035】开始调用多行函数 `compute_top_down_link_pose`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            compute_top_down_link_pose(
# 【L1036】声明/传入参数 `calibrated_reference_link_position`；在本项目中它表示机器人连杆、位置相关值。
                calibrated_reference_link_position,
# 【L1037】声明/传入参数 `grasp_link_rotation`；在本项目中它表示机器人连杆、旋转相关值。
                grasp_link_rotation,
# 【L1038】声明/传入参数 `source_block_position_base`；在本项目中它表示源位置、位置相关值。
                source_block_position_base,
# 【L1039】向上一行的函数调用或容器继续传入 `args.top_down_yaw_rad`；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_yaw_rad,
# 【L1040】向上一行的函数调用或容器继续传入 `args.top_down_tilt_rad`；`top_down_tilt_rad` 表示本功能块中的 `top_down_tilt_rad` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_tilt_rad,
# 【L1041】向上一行的函数调用或容器继续传入 `args.top_down_blend`；`top_down_blend` 表示本功能块中的 `top_down_blend` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_blend,
# 【L1042】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1043】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1044】得到 `ik_seeds`，它在本项目中表示本功能块中的 `ik_seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[grasp_ik_numerical_seed]`；`grasp_ik_numerical_seed` 表示本功能块中的 `grasp_ik_numerical_seed` 值。
        ik_seeds = [grasp_ik_numerical_seed]
# 【L1045】判断 `args.top_down_ik_multistart > 1` 是否成立；`top_down_ik_multistart` 表示本功能块中的 `top_down_ik_multistart` 值
        if args.top_down_ik_multistart > 1:
# 【L1046】得到 `rng`，它在本项目中表示本功能块中的 `rng` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.random.default_rng(20260916)`；`random` 表示本功能块中的 `random` 值；`default_rng` 表示本功能块中的 `default_rng` 值。
            rng = np.random.default_rng(20260916)
# 【L1047】得到 `random_seeds`，它在本项目中表示本功能块中的 `random_seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rng.uniform(`；`rng` 表示本功能块中的 `rng` 值；`uniform` 表示本功能块中的 `uniform` 值。
            random_seeds = rng.uniform(
# 【L1048】声明/传入参数 `RM65_JOINT_LOWER_RAD`；在本项目中它表示RM65 机械约束或项目常量。
                RM65_JOINT_LOWER_RAD,
# 【L1049】声明/传入参数 `RM65_JOINT_UPPER_RAD`；在本项目中它表示RM65 机械约束或项目常量。
                RM65_JOINT_UPPER_RAD,
# 【L1050】给上一层函数/配置构造器的命名参数 `size` 传入 `(args.top_down_ik_multistart - 1, len(ARM_JOINTS))`；该参数在本项目中表示本功能块中的 `size` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                size=(args.top_down_ik_multistart - 1, len(ARM_JOINTS)),
# 【L1051】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1052】对 `ik_seeds` 执行 `extend`，把 `random_seeds` 加入已有结果；该集合表示本功能块中的 `ik_seeds` 值，随后会用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ik_seeds.extend(random_seeds)
# 【L1053】得到 `top_down_solution`，它在本项目中表示本功能块中的 `top_down_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        top_down_solution = None
# 【L1054】得到 `success`，它在本项目中表示成功相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
        success = False
# 【L1055】得到 `top_down_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rot_matrix_to_quat(top_down_rotation)`；`rot_matrix_to_quat` 表示本功能块中的 `rot_matrix_to_quat` 值；`top_down_rotation` 表示旋转相关值。
        top_down_quaternion = rot_matrix_to_quat(top_down_rotation)
# 【L1056】得到 `minimum_pregrasp_distance_m`，它在本项目中表示本功能块中的 `minimum_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `min(requested_pregrasp_distance_m, 0.05)`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值。
        minimum_pregrasp_distance_m = min(requested_pregrasp_distance_m, 0.05)
# 【L1057】得到 `fallback_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `int(` 的结果保存下来，供当前功能块后续使用。
        fallback_count = int(
# 【L1058】开始对 `np` 调用多行方法 `floor`：调用 `np` 提供的 `floor` 操作；具体参数写在随后几行，用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            np.floor(
# 【L1059】这是上一行尚未闭合的参数、数组或字典内容：`(requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值；`minimum_pregrasp_distance_m` 表示本功能块中的 `minimum_pregrasp_distance_m` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                (requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01
# 【L1060】把运算项 `+ 1e-9` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                + 1e-9
# 【L1061】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1062】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1063】得到 `pregrasp_distance_candidates`，它在本项目中表示本功能块中的 `pregrasp_distance_candidates` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        pregrasp_distance_candidates = [
# 【L1064】把表达式/参数 `requested_pregrasp_distance_m - 0.01 * index` 接入当前完整语句；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值；`index` 表示索引相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            requested_pregrasp_distance_m - 0.01 * index
# 【L1065】开始遍历 `for index in range(fallback_count + 1)` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            for index in range(fallback_count + 1)
# 【L1066】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ]
# 【L1067】遍历 `pregrasp_distance_candidates`，每次把当前元素放进 `candidate_pregrasp_distance_m`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
        for candidate_pregrasp_distance_m in pregrasp_distance_candidates:
# 【L1068】得到 `retreat_distances_for_selection`，它在本项目中表示本功能块中的 `retreat_distances_for_selection` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(`；`linspace` 表示本功能块中的 `linspace` 值。
            retreat_distances_for_selection = np.linspace(
# 【L1069】向上一行的函数调用或容器继续传入 `0.01`；逗号说明后面还有同级参数，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                0.01,
# 【L1070】声明/传入参数 `candidate_pregrasp_distance_m`；在本项目中它表示本功能块中的 `candidate_pregrasp_distance_m` 值。
                candidate_pregrasp_distance_m,
# 【L1071】调用 `max(1, int(round(candidate_pregrasp_distance_m / 0.01)))`：从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                max(1, int(round(candidate_pregrasp_distance_m / 0.01))),
# 【L1072】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1073】得到 `retreat_targets_for_selection`，它在本项目中表示本功能块中的 `retreat_targets_for_selection` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            retreat_targets_for_selection = [
# 【L1074】声明/传入参数 `top_down_link_position`；在本项目中它表示机器人连杆、位置相关值。
                top_down_link_position
# 【L1075】调用 `np.array`：创建 NumPy 数组；本行实际操作 `+ np.array([0.0, 0.0, distance], dtype=np.float64)`。`array` 表示本功能块中的 `array` 值；`distance` 表示本功能块中的 `distance` 值。
                + np.array([0.0, 0.0, distance], dtype=np.float64)
# 【L1076】开始遍历 `for distance in retreat_distances_for_selection` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                for distance in retreat_distances_for_selection
# 【L1077】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ]
# 【L1078】遍历 `enumerate(ik_seeds)`，每次把当前元素放进 `seed_index, ik_seed`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
            for seed_index, ik_seed in enumerate(ik_seeds):
# 【L1079】把右侧返回的多个结果按位置拆给 `candidate_solution, candidate_success`；`candidate_solution` 表示本功能块中的 `candidate_solution` 值；`candidate_success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
                candidate_solution, candidate_success = lula.compute_inverse_kinematics(
# 【L1080】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                    "link_6",
# 【L1081】声明/传入参数 `top_down_link_position`；在本项目中它表示机器人连杆、位置相关值。
                    top_down_link_position,
# 【L1082】声明/传入参数 `top_down_quaternion`；在本项目中它表示四元数相关值。
                    top_down_quaternion,
# 【L1083】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `np.asarray(ik_seed, dtype=np.float64)`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    warm_start=np.asarray(ik_seed, dtype=np.float64),
# 【L1084】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    position_tolerance=1e-4,
# 【L1085】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    orientation_tolerance=1e-3,
# 【L1086】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                )
# 【L1087】判断 `not candidate_success` 是否成立；`candidate_success` 表示成功相关值
                if not candidate_success:
# 【L1088】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中不满足继续条件。
                    continue
# 【L1089】得到 `candidate_raw`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `candidate_solution, dtype=np.float64`（本功能块中的 `candidate_solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
                candidate_raw = np.asarray(candidate_solution, dtype=np.float64)
# 【L1090】开始执行可能抛错的“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
                try:
# 【L1091】得到 `candidate_command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
                    candidate_command = closest_equivalent_rm65_solution(
# 【L1092】把表达式/参数 `lula, candidate_raw, grasp_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`candidate_raw` 表示原始相关值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        lula, candidate_raw, grasp_arm
# 【L1093】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1094】得到 `candidate_retreat`，它在本项目中表示本功能块中的 `candidate_retreat` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `solve_continuous_cartesian_path(`；`solve_continuous_cartesian_path` 表示路径相关值。
                    candidate_retreat = solve_continuous_cartesian_path(
# 【L1095】声明/传入参数 `lula`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
                        lula,
# 【L1096】声明/传入参数 `retreat_targets_for_selection`；在本项目中它表示本功能块中的 `retreat_targets_for_selection` 值。
                        retreat_targets_for_selection,
# 【L1097】声明/传入参数 `top_down_quaternion`；在本项目中它表示四元数相关值。
                        top_down_quaternion,
# 【L1098】声明/传入参数 `candidate_raw`；在本项目中它表示原始相关值。
                        candidate_raw,
# 【L1099】声明/传入参数 `candidate_command`；在本项目中它表示控制命令相关值。
                        candidate_command,
# 【L1100】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1101】捕获 `RuntimeError`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
                except RuntimeError:
# 【L1102】得到 `candidate_retreat`，它在本项目中表示本功能块中的 `candidate_retreat` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
                    candidate_retreat = None
# 【L1103】检查 `candidate_retreat is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
                if candidate_retreat is None:
# 【L1104】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中不满足继续条件。
                    continue
# 【L1105】把右侧返回的多个结果按位置拆给 `_, candidate_retreat_waypoints, _`；`_` 表示本功能块中的 `_` 值；`candidate_retreat_waypoints` 表示本功能块中的 `candidate_retreat_waypoints` 值；`_` 表示本功能块中的 `_` 值。右侧的来源是：计算表达式 `candidate_retreat`；`candidate_retreat` 表示本功能块中的 `candidate_retreat` 值。
                _, candidate_retreat_waypoints, _ = candidate_retreat
# 【L1106】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_raw`；`candidate_raw` 表示原始相关值。
                grasp_ik_numerical_seed = candidate_raw
# 【L1107】得到 `top_down_solution`，它在本项目中表示本功能块中的 `top_down_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_command`；`candidate_command` 表示控制命令相关值。
                top_down_solution = candidate_command
# 【L1108】得到 `precomputed_retreat_waypoints`，它在本项目中表示本功能块中的 `precomputed_retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_retreat_waypoints`；`candidate_retreat_waypoints` 表示本功能块中的 `candidate_retreat_waypoints` 值。
                precomputed_retreat_waypoints = candidate_retreat_waypoints
# 【L1109】得到 `top_down_ik_seed_index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `seed_index`；`seed_index` 表示索引相关值。
                top_down_ik_seed_index = seed_index
# 【L1110】得到 `effective_pregrasp_distance_m`，它在本项目中表示本功能块中的 `effective_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_pregrasp_distance_m`；`candidate_pregrasp_distance_m` 表示本功能块中的 `candidate_pregrasp_distance_m` 值。
                effective_pregrasp_distance_m = candidate_pregrasp_distance_m
# 【L1111】得到 `success`，它在本项目中表示成功相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                success = True
# 【L1112】立即结束最近一层循环；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L1113】判断 `success` 是否成立；`success` 表示成功相关值
            if success:
# 【L1114】立即结束最近一层循环；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L1115】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1116】把 `` 的当前值/文字输出到终端；它用于观察“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”进度，也给日志留下可搜索证据。
            print(
# 【L1117】提供文本片段 `"TOP_DOWN_IK_TARGET="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "TOP_DOWN_IK_TARGET="
# 【L1118】把表达式/参数 `f"position={top_down_link_position.tolist()} "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`position` 表示位置相关值；`top_down_link_position` 表示机器人连杆、位置相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"position={top_down_link_position.tolist()} "
# 【L1119】把表达式/参数 `f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`yaw` 表示本功能块中的 `yaw` 值；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "
# 【L1120】向上一行的函数调用或容器继续传入 `f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}"`；`f` 表示本功能块中的 `f` 值；`blend` 表示本功能块中的 `blend` 值；`top_down_blend` 表示本功能块中的 `top_down_blend` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}",
# 【L1121】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                flush=True,
# 【L1122】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1123】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L1124】提供文本片段 `"Lula found no top-down grasp pose with a continuous pregrasp path"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "Lula found no top-down grasp pose with a continuous pregrasp path"
# 【L1125】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1126】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `top_down_solution, dtype=np.float64`（本功能块中的 `top_down_solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        grasp_arm = np.asarray(top_down_solution, dtype=np.float64)
# 【L1127】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1128】判断 `args.lift_mode == "cartesian_vertical"` 是否成立；`lift_mode` 表示本功能块中的 `lift_mode` 值；`cartesian_vertical` 表示本功能块中的 `cartesian_vertical` 值
    if args.lift_mode == "cartesian_vertical":
# 【L1129】得到 `vertical_lift_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_position + np.array(`；`grasp_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        vertical_lift_target = grasp_link_position + np.array(
# 【L1130】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64`；`cartesian_lift_height_m` 表示本功能块中的 `cartesian_lift_height_m` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64
# 【L1131】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1132】把右侧返回的多个结果按位置拆给 `lift_arm_solution, success`；`lift_arm_solution` 表示本功能块中的 `lift_arm_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        lift_arm_solution, success = lula.compute_inverse_kinematics(
# 【L1133】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1134】声明/传入参数 `vertical_lift_target`；在本项目中它表示目标相关值。
            vertical_lift_target,
# 【L1135】调用 `rot_matrix_to_quat(grasp_link_rotation)`：把 3×3 旋转矩阵转换为 wxyz 四元数，供 Lula/Isaac 的姿态接口使用。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            rot_matrix_to_quat(grasp_link_rotation),
# 【L1136】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `grasp_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1137】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1138】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            orientation_tolerance=1e-3,
# 【L1139】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1140】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1141】主动抛出 `RuntimeError("Lula failed to solve the local Cartesian vertical lift")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the local Cartesian vertical lift")
# 【L1142】得到 `lift_arm`，它在本项目中表示本功能块中的 `lift_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值；`lula` 表示NVIDIA Lula 运动学求解器实例；`lift_arm_solution` 表示本功能块中的 `lift_arm_solution` 值。
        lift_arm = closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)
# 【L1143】调用 `require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")`：检查前后两个六关节姿态的最大跳变量，过大时拒绝这条 IK 路径。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")
# 【L1144】把右侧返回的多个结果按位置拆给 `lift_link_position, lift_link_rotation`；`lift_link_position` 表示机器人连杆、位置相关值；`lift_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    lift_link_position, lift_link_rotation = lula.compute_forward_kinematics("link_6", lift_arm)
# 【L1145】得到 `expected_lift_translation`，它在本项目中表示本功能块中的 `expected_lift_translation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lift_link_position - grasp_link_position`；`lift_link_position` 表示机器人连杆、位置相关值；`grasp_link_position` 表示机器人连杆、位置相关值。
    expected_lift_translation = lift_link_position - grasp_link_position
# 【L1146】得到 `expected_source_lift_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `source_block_position + expected_lift_translation`；`source_block_position` 表示源位置、位置相关值；`expected_lift_translation` 表示本功能块中的 `expected_lift_translation` 值。
    expected_source_lift_block_position = source_block_position + expected_lift_translation
# 【L1147】得到 `target_lift_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    target_lift_arm = lift_arm.copy()
# 【L1148】把右侧结果写进 `target_lift_arm[0]`（写入 `target_lift_arm[0]` 指定的字段）；右侧具体做的是：计算表达式 `args.transfer_joint_1_rad`；`transfer_joint_1_rad` 表示关节相关值。
    target_lift_arm[0] = args.transfer_joint_1_rad
# 【L1149】把右侧返回的多个结果按位置拆给 `transferred_link_position, transferred_link_rotation`；`transferred_link_position` 表示机器人连杆、位置相关值；`transferred_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    transferred_link_position, transferred_link_rotation = lula.compute_forward_kinematics(
# 【L1150】提供文本片段 `"link_6", target_lift_arm`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
        "link_6", target_lift_arm
# 【L1151】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1152】得到 `release_clear_arm`，它在本项目中表示本功能块中的 `release_clear_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    release_clear_arm = None
# 【L1153】判断 `args.unassisted_release and not args.place_descent` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值；`place_descent` 表示本功能块中的 `place_descent` 值
    if args.unassisted_release and not args.place_descent:
# 【L1154】得到 `release_clear_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transferred_link_position + np.array(`；`transferred_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        release_clear_target = transferred_link_position + np.array(
# 【L1155】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, args.release_clearance_m], dtype=np.float64`；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.release_clearance_m], dtype=np.float64
# 【L1156】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1157】把右侧返回的多个结果按位置拆给 `release_clear_solution, success`；`release_clear_solution` 表示本功能块中的 `release_clear_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        release_clear_solution, success = lula.compute_inverse_kinematics(
# 【L1158】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1159】声明/传入参数 `release_clear_target`；在本项目中它表示目标相关值。
            release_clear_target,
# 【L1160】给上一层函数/配置构造器的命名参数 `target_orientation` 传入 `None`；该参数在本项目中表示目标相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1161】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `target_lift_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=target_lift_arm,
# 【L1162】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1163】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1164】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1165】主动抛出 `RuntimeError("Lula failed to solve the vertical release-clearance motion")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the vertical release-clearance motion")
# 【L1166】得到 `release_clear_arm`，它在本项目中表示本功能块中的 `release_clear_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
        release_clear_arm = closest_equivalent_rm65_solution(
# 【L1167】把表达式/参数 `lula, release_clear_solution, target_lift_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`release_clear_solution` 表示本功能块中的 `release_clear_solution` 值；`target_lift_arm` 表示目标相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            lula, release_clear_solution, target_lift_arm
# 【L1168】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1169】开始调用多行函数 `require_continuous_joint_step`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        require_continuous_joint_step(
# 【L1170】把右侧返回的多个结果按位置拆给 `target_lift_arm, release_clear_arm, label`；`target_lift_arm` 表示目标相关值；`release_clear_arm` 表示本功能块中的 `release_clear_arm` 值；`label` 表示本功能块中的 `label` 值。右侧的来源是：计算表达式 `"release clearance"`；`release` 表示本功能块中的 `release` 值；`clearance` 表示本功能块中的 `clearance` 值。
            target_lift_arm, release_clear_arm, label="release clearance"
# 【L1171】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1172】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1173】得到 `transfer_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    transfer_quaternion = np.array(
# 【L1174】这是上一行尚未闭合的参数、数组或字典内容：`[np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],`；`cos` 表示本功能块中的 `cos` 值；`transfer_joint_1_rad` 表示关节相关值；`sin` 表示本功能块中的 `sin` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],
# 【L1175】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1176】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1177】得到 `target_release_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)`；`rotate_about_z` 表示本功能块中的 `rotate_about_z` 值；`expected_source_lift_block_position` 表示源位置、位置相关值；`transfer_joint_1_rad` 表示关节相关值。
    target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)
# 【L1178】得到 `target_block_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    target_block_position = target_release_position.copy()
# 【L1179】把右侧结果写进 `target_block_position[2]`（写入 `target_block_position[2]` 指定的字段）；右侧具体做的是：计算表达式 `TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0`；`TARGET_PLATFORM_TOP_Z` 表示目标位置方块/平台的任务常量；`BLOCK_SIZE` 表示本功能块中的 `BLOCK_SIZE` 值。
    target_block_position[2] = TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L1180】得到 `target_block_quaternion`，它在本项目中表示目标、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)`；`quaternion_multiply_wxyz` 表示四元数相关值；`transfer_quaternion` 表示四元数相关值；`source_block_quaternion` 表示源位置、四元数相关值。
    target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)
# 【L1181】得到 `target_platform_size`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    target_platform_size = (
# 【L1182】把比较条件 `TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE` 接到上一行尚未结束的布尔表达式；`TARGET_STRIP_SIZE` 表示目标位置方块/平台的任务常量；`target_support_mode` 表示目标相关值；`rotated_strip` 表示本功能块中的 `rotated_strip` 值。比较结果共同决定“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”是否通过。
        TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE
# 【L1183】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1184】得到 `target_platform_orientation`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    target_platform_orientation = (
# 【L1185】把比较条件 `tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None` 接到上一行尚未结束的布尔表达式；`transfer_quaternion` 表示四元数相关值；`target_support_mode` 表示目标相关值；`rotated_strip` 表示本功能块中的 `rotated_strip` 值。比较结果共同决定“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”是否通过。
        tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None
# 【L1186】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1187】得到 `target_platform_position`，它在本项目中表示目标、支撑平台、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    target_platform_position = np.array(
# 【L1188】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [
# 【L1189】向上一行的函数调用或容器继续传入 `target_block_position[0]`；`target_block_position` 表示目标、位置相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[0],
# 【L1190】向上一行的函数调用或容器继续传入 `target_block_position[1]`；`target_block_position` 表示目标、位置相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[1],
# 【L1191】向上一行的函数调用或容器继续传入 `TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0`；`TARGET_PLATFORM_TOP_Z` 表示目标位置方块/平台的任务常量；`target_platform_size` 表示目标、支撑平台相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0,
# 【L1192】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ],
# 【L1193】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1194】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1195】得到 `place_waypoints`，它在本项目中表示本功能块中的 `place_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    place_waypoints = []
# 【L1196】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
    if args.place_descent:
# 【L1197】得到 `place_waypoint_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(1, int(round(args.place_descent_distance_m / 0.01)))`；`round` 表示本功能块中的 `round` 值；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值。
        place_waypoint_count = max(1, int(round(args.place_descent_distance_m / 0.01)))
# 【L1198】得到 `place_distances`，它在本项目中表示本功能块中的 `place_distances` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)`；`linspace` 表示本功能块中的 `linspace` 值；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值；`place_waypoint_count` 表示数量相关值。
        place_distances = np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)
# 【L1199】得到 `place_warm_start`，它在本项目中表示本功能块中的 `place_warm_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        place_warm_start = lift_arm.copy()
# 【L1200】遍历 `place_distances`，每次把当前元素放进 `distance`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
        for distance in place_distances:
# 【L1201】得到 `place_link_target`，它在本项目中表示机器人连杆、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lift_link_position - np.array(`；`lift_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
            place_link_target = lift_link_position - np.array(
# 【L1202】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, distance], dtype=np.float64`；`distance` 表示本功能块中的 `distance` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                [0.0, 0.0, distance], dtype=np.float64
# 【L1203】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1204】把右侧返回的多个结果按位置拆给 `place_solution, success`；`place_solution` 表示本功能块中的 `place_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
            place_solution, success = lula.compute_inverse_kinematics(
# 【L1205】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "link_6",
# 【L1206】声明/传入参数 `place_link_target`；在本项目中它表示机器人连杆、目标相关值。
                place_link_target,
# 【L1207】调用 `rot_matrix_to_quat(lift_link_rotation)`：把 3×3 旋转矩阵转换为 wxyz 四元数，供 Lula/Isaac 的姿态接口使用。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                rot_matrix_to_quat(lift_link_rotation),
# 【L1208】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `place_warm_start`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                warm_start=place_warm_start,
# 【L1209】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                position_tolerance=1e-4,
# 【L1210】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                orientation_tolerance=1e-3,
# 【L1211】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1212】判断 `not success` 是否成立；`success` 表示成功相关值
            if not success:
# 【L1213】主动抛出 `RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
                raise RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")
# 【L1214】得到 `place_solution`，它在本项目中表示本功能块中的 `place_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
            place_solution = closest_equivalent_rm65_solution(
# 【L1215】把表达式/参数 `lula, place_solution, place_warm_start` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`place_solution` 表示本功能块中的 `place_solution` 值；`place_warm_start` 表示本功能块中的 `place_warm_start` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                lula, place_solution, place_warm_start
# 【L1216】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1217】开始调用多行函数 `require_continuous_joint_step`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            require_continuous_joint_step(
# 【L1218】把右侧返回的多个结果按位置拆给 `place_warm_start, place_solution, label`；`place_warm_start` 表示本功能块中的 `place_warm_start` 值；`place_solution` 表示本功能块中的 `place_solution` 值；`label` 表示本功能块中的 `label` 值。右侧的来源是：计算表达式 `f"place waypoint {distance:.3f} m"`；`f` 表示本功能块中的 `f` 值；`place` 表示本功能块中的 `place` 值；`waypoint` 表示本功能块中的 `waypoint` 值。
                place_warm_start, place_solution, label=f"place waypoint {distance:.3f} m"
# 【L1219】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1220】得到 `place_warm_start`，它在本项目中表示本功能块中的 `place_warm_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `place_solution`；`place_solution` 表示本功能块中的 `place_solution` 值。
            place_warm_start = place_solution
# 【L1221】得到 `rotated_place_solution`，它在本项目中表示本功能块中的 `rotated_place_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
            rotated_place_solution = place_warm_start.copy()
# 【L1222】用 `rotated_place_solution[0] + args.transfer_joint_1_rad - lift_arm[0]` 更新 `rotated_place_solution[0]` 原值；`rotated_place_solution[0]` 表示本功能块中的 `rotated_place_solution[0]` 值，常用于累计步数、距离、损失或成功次数。
            rotated_place_solution[0] += args.transfer_joint_1_rad - lift_arm[0]
# 【L1223】对 `place_waypoints` 执行 `append`，把 `rotated_place_solution` 加入已有结果；该集合表示本功能块中的 `place_waypoints` 值，随后会用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            place_waypoints.append(rotated_place_solution)
# 【L1224】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1225】得到 `grasp_link_quaternion`，它在本项目中表示机器人连杆、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rot_matrix_to_quat(grasp_link_rotation)`；`rot_matrix_to_quat` 表示本功能块中的 `rot_matrix_to_quat` 值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。
    grasp_link_quaternion = rot_matrix_to_quat(grasp_link_rotation)
# 【L1226】得到 `outward_direction`，它在本项目中表示本功能块中的 `outward_direction` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    outward_direction = (
# 【L1227】调用 `np.array`：创建 NumPy 数组；本行实际操作 `np.array([0.0, 0.0, -1.0], dtype=np.float64)`。`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值。
        np.array([0.0, 0.0, -1.0], dtype=np.float64)
# 【L1228】判断 `args.grasp_orientation_mode == "top_down"` 是否成立；`grasp_orientation_mode` 表示本功能块中的 `grasp_orientation_mode` 值；`top_down` 表示本功能块中的 `top_down` 值
        if args.grasp_orientation_mode == "top_down"
# 【L1229】这是上一行条件表达式的备用值：条件不成立时使用 `quaternion_to_matrix_wxyz(`；它让“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”在可选数据缺失时仍有明确结果。
        else quaternion_to_matrix_wxyz(
# 【L1230】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)`。`asarray` 表示本功能块中的 `asarray` 值；`SOURCE_BLOCK_QUATERNION_WXYZ` 表示源位置方块/平台的任务常量。
            np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L1231】闭合上一行开始的函数/容器后继续执行 `)[:, 0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )[:, 0]
# 【L1232】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1233】得到 `waypoint_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(1, int(round(effective_pregrasp_distance_m / 0.01)))`；`round` 表示本功能块中的 `round` 值；`effective_pregrasp_distance_m` 表示本功能块中的 `effective_pregrasp_distance_m` 值。
    waypoint_count = max(1, int(round(effective_pregrasp_distance_m / 0.01)))
# 【L1234】得到 `retreat_distances`，它在本项目中表示本功能块中的 `retreat_distances` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(0.01, effective_pregrasp_distance_m, waypoint_count)`；`linspace` 表示本功能块中的 `linspace` 值；`effective_pregrasp_distance_m` 表示本功能块中的 `effective_pregrasp_distance_m` 值；`waypoint_count` 表示数量相关值。
    retreat_distances = np.linspace(0.01, effective_pregrasp_distance_m, waypoint_count)
# 【L1235】得到 `retreat_targets`，它在本项目中表示本功能块中的 `retreat_targets` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
    retreat_targets = [
# 【L1236】把表达式/参数 `grasp_link_position - distance * outward_direction` 接入当前完整语句；`grasp_link_position` 表示机器人连杆、位置相关值；`distance` 表示本功能块中的 `distance` 值；`outward_direction` 表示本功能块中的 `outward_direction` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        grasp_link_position - distance * outward_direction
# 【L1237】开始遍历 `for distance in retreat_distances` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        for distance in retreat_distances
# 【L1238】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    ]
# 【L1239】检查 `precomputed_retreat_waypoints is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if precomputed_retreat_waypoints is not None:
# 【L1240】得到 `retreat_waypoints`，它在本项目中表示本功能块中的 `retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        retreat_waypoints = [item.copy() for item in precomputed_retreat_waypoints]
# 【L1241】前面的 `if/elif` 都不成立时走这里；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中处理剩余输入或备用路径。
    else:
# 【L1242】得到 `retreat_result`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `solve_continuous_cartesian_path(`；`solve_continuous_cartesian_path` 表示路径相关值。
        retreat_result = solve_continuous_cartesian_path(
# 【L1243】声明/传入参数 `lula`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
            lula,
# 【L1244】声明/传入参数 `retreat_targets`；在本项目中它表示本功能块中的 `retreat_targets` 值。
            retreat_targets,
# 【L1245】声明/传入参数 `grasp_link_quaternion`；在本项目中它表示机器人连杆、四元数相关值。
            grasp_link_quaternion,
# 【L1246】声明/传入参数 `grasp_ik_numerical_seed`；在本项目中它表示本功能块中的 `grasp_ik_numerical_seed` 值。
            grasp_ik_numerical_seed,
# 【L1247】声明/传入参数 `grasp_arm`；在本项目中它表示本功能块中的 `grasp_arm` 值。
            grasp_arm,
# 【L1248】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1249】检查 `retreat_result is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if retreat_result is None:
# 【L1250】主动抛出 `RuntimeError("Lula found no continuous Cartesian pregrasp path")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula found no continuous Cartesian pregrasp path")
# 【L1251】把右侧返回的多个结果按位置拆给 `_, retreat_waypoints, _`；`_` 表示本功能块中的 `_` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值；`_` 表示本功能块中的 `_` 值。右侧的来源是：计算表达式 `retreat_result`；`retreat_result` 表示结果相关值。
        _, retreat_waypoints, _ = retreat_result
# 【L1252】得到 `pregrasp_arm`，它在本项目中表示本功能块中的 `pregrasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    pregrasp_arm = grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]
# 【L1253】得到 `retreat_joint_sequence`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.vstack([grasp_arm, *retreat_waypoints])`；`vstack` 表示本功能块中的 `vstack` 值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。
    retreat_joint_sequence = np.vstack([grasp_arm, *retreat_waypoints])
# 【L1254】得到 `retreat_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    retreat_max_command_step_rad = float(
# 【L1255】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(retreat_joint_sequence, axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
        np.max(np.abs(np.diff(retreat_joint_sequence, axis=0)))
# 【L1256】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1257】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1258】得到 `place_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_max_command_step_rad = None
# 【L1259】判断 `place_waypoints` 是否成立；`place_waypoints` 表示本功能块中的 `place_waypoints` 值
    if place_waypoints:
# 【L1260】得到 `place_joint_sequence`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.vstack([target_lift_arm, *place_waypoints])`；`vstack` 表示本功能块中的 `vstack` 值；`target_lift_arm` 表示目标相关值；`place_waypoints` 表示本功能块中的 `place_waypoints` 值。
        place_joint_sequence = np.vstack([target_lift_arm, *place_waypoints])
# 【L1261】得到 `place_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
        place_max_command_step_rad = float(
# 【L1262】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(place_joint_sequence, axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
            np.max(np.abs(np.diff(place_joint_sequence, axis=0)))
# 【L1263】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1264】判断 `args.diagnose_kinematics_only` 是否成立；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值
    if args.diagnose_kinematics_only:
# 【L1265】得到 `diagnostic`，它在本项目中表示本功能块中的 `diagnostic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        diagnostic = {
# 【L1266】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"diagnostic"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "diagnostic",
# 【L1267】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L1268】定义字典/JSON 字段 `robot_base_position_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L1269】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1270】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L1271】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L1272】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1273】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1274】定义字典/JSON 字段 `grasp_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `grasp_arm_joint_position_rad` 数据；字段值来自 `grasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_arm_joint_position_rad": grasp_arm.tolist(),
# 【L1275】定义字典/JSON 字段 `lift_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `lift_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_arm_joint_position_rad": lift_arm.tolist(),
# 【L1276】定义字典/JSON 字段 `target_lift_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `target_lift_arm_joint_position_rad` 数据；字段值来自 `target_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_lift_arm_joint_position_rad": target_lift_arm.tolist(),
# 【L1277】定义字典/JSON 字段 `retreat_waypoint_count`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_waypoint_count` 数据；字段值来自 `len(retreat_waypoints)`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_waypoint_count": len(retreat_waypoints),
# 【L1278】定义字典/JSON 字段 `retreat_max_command_step_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_max_command_step_rad` 数据；字段值来自 `retreat_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_max_command_step_rad": retreat_max_command_step_rad,
# 【L1279】定义字典/JSON 字段 `retreat_waypoint_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_waypoint_joint_position_rad` 数据；字段值来自 `[`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_waypoint_joint_position_rad": [
# 【L1280】这是生成式/推导式 `item.tolist() for item in retreat_waypoints`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`item` 表示本功能块中的 `item` 值；`tolist` 表示本功能块中的 `tolist` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。产生的序列交给外层列表、字典或函数完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                item.tolist() for item in retreat_waypoints
# 【L1281】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ],
# 【L1282】定义字典/JSON 字段 `place_waypoint_count`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_waypoint_count` 数据；字段值来自 `len(place_waypoints)`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_waypoint_count": len(place_waypoints),
# 【L1283】定义字典/JSON 字段 `place_max_command_step_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_max_command_step_rad` 数据；字段值来自 `place_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_max_command_step_rad": place_max_command_step_rad,
# 【L1284】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_ik_uses_base_rotation_symmetry` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_ik_uses_base_rotation_symmetry": True,
# 【L1285】定义字典/JSON 字段 `place_waypoint_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_waypoint_joint_position_rad` 数据；字段值来自 `[item.tolist() for item in place_waypoints]`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_waypoint_joint_position_rad": [item.tolist() for item in place_waypoints],
# 【L1286】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        }
# 【L1287】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1288】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L1289】把 `json.dumps(diagnostic, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”进度，也给日志留下可搜索证据。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L1290】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
        return 0
# 【L1291】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1292】得到 `sim`，它在本项目中表示IsaacLab SimulationContext，负责物理时间步；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `SimulationContext(`；`SimulationContext` 表示本功能块中的 `SimulationContext` 值。
    sim = SimulationContext(
# 【L1293】开始对 `sim_utils` 调用多行方法 `SimulationCfg`：调用 `sim_utils` 提供的 `SimulationCfg` 操作；具体参数写在随后几行，用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        sim_utils.SimulationCfg(
# 【L1294】给上一层函数/配置构造器的命名参数 `dt` 传入 `1.0 / 240.0`；该参数在本项目中表示本功能块中的 `dt` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dt=1.0 / 240.0,
# 【L1295】给上一层函数/配置构造器的命名参数 `device` 传入 `args.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            device=args.device,
# 【L1296】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
            physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1297】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.5`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                static_friction=1.5,
# 【L1298】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `1.2`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                dynamic_friction=1.2,
# 【L1299】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                restitution=0.0,
# 【L1300】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                friction_combine_mode="max",
# 【L1301】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1302】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1303】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1304】得到 `light_cfg`，它在本项目中表示本功能块中的 `light_cfg` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))`；`sim_utils` 表示仿真相关值；`DomeLightCfg` 表示本功能块中的 `DomeLightCfg` 值；`intensity` 表示本功能块中的 `intensity` 值。
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
# 【L1305】对 `light_cfg` 调用 `func("/World/Light", light_cfg)`：调用 `light_cfg` 提供的 `func` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    light_cfg.func("/World/Light", light_cfg)
# 【L1306】判断 `not args.diagnose_approach_only` 是否成立；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值
    if not args.diagnose_approach_only:
# 【L1307】开始调用多行函数 `spawn_platform`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        spawn_platform(
# 【L1308】提供路径/资源标识 `"/World/TargetPlatform"`；在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "/World/TargetPlatform",
# 【L1309】声明/传入参数 `target_platform_position`；在本项目中它表示目标、支撑平台、位置相关值。
            target_platform_position,
# 【L1310】声明/传入参数 `target_platform_size`；在本项目中它表示目标、支撑平台相关值。
            target_platform_size,
# 【L1311】这是上一行尚未闭合的参数、数组或字典内容：`(0.12, 0.45, 0.20),`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (0.12, 0.45, 0.20),
# 【L1312】声明/传入参数 `target_platform_orientation`；在本项目中它表示目标、支撑平台相关值。
            target_platform_orientation,
# 【L1313】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1314】判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值
    if args.natural_source_gravity:
# 【L1315】得到 `source_platform_position`，它在本项目中表示源位置、支撑平台、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
        source_platform_position = np.array(
# 【L1316】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            [
# 【L1317】向上一行的函数调用或容器继续传入 `source_block_position[0]`；`source_block_position` 表示源位置、位置相关值，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[0],
# 【L1318】向上一行的函数调用或容器继续传入 `source_block_position[1]`；`source_block_position` 表示源位置、位置相关值，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[1],
# 【L1319】向上一行的函数调用或容器继续传入 `SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0`；`SOURCE_PLATFORM_TOP_Z` 表示源位置方块/平台的任务常量；`SOURCE_PLATFORM_SIZE` 表示源位置方块/平台的任务常量，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0,
# 【L1320】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ],
# 【L1321】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dtype=np.float64,
# 【L1322】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1323】开始调用多行函数 `spawn_platform`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        spawn_platform(
# 【L1324】提供路径/资源标识 `"/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)`；在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)
# 【L1325】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1326】得到 `target_platform_collision_apis`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    target_platform_collision_apis = []
# 【L1327】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1328】判断 `str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI)` 是否成立；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值；`startswith` 表示本功能块中的 `startswith` 值
        if str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1329】得到 `collision_api`，它在本项目中表示本功能块中的 `collision_api` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `UsdPhysics.CollisionAPI(prim)`；`UsdPhysics` 表示本功能块中的 `UsdPhysics` 值；`CollisionAPI` 表示本功能块中的 `CollisionAPI` 值；`prim` 表示本功能块中的 `prim` 值。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1330】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(False)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1331】对 `target_platform_collision_apis` 执行 `append`，把 `collision_api` 加入已有结果；该集合表示目标、支撑平台相关值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            target_platform_collision_apis.append(collision_api)
# 【L1332】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1333】得到 `robot`，它在本项目中表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Articulation(`；`Articulation` 表示本功能块中的 `Articulation` 值。
    robot = Articulation(
# 【L1334】开始调用多行函数 `ArticulationCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ArticulationCfg(
# 【L1335】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/Robot"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Robot",
# 【L1336】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.UsdFileCfg(`；`sim_utils` 表示仿真相关值；`UsdFileCfg` 表示本功能块中的 `UsdFileCfg` 值。
            spawn=sim_utils.UsdFileCfg(
# 【L1337】给上一层函数/配置构造器的命名参数 `usd_path` 传入 `str(usd)`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                usd_path=str(usd),
# 【L1338】给上一层函数/配置构造器的命名参数 `activate_contact_sensors` 传入 `True`；该参数在本项目中表示接触相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                activate_contact_sensors=True,
# 【L1339】给上一层函数/配置构造器的命名参数 `rigid_props` 传入 `sim_utils.RigidBodyPropertiesCfg(disable_gravity=False)`；该参数在本项目中表示本功能块中的 `rigid_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
# 【L1340】得到 `articulation_props`，它在本项目中表示本功能块中的 `articulation_props` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.ArticulationRootPropertiesCfg(`；`sim_utils` 表示仿真相关值；`ArticulationRootPropertiesCfg` 表示本功能块中的 `ArticulationRootPropertiesCfg` 值。
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
# 【L1341】给上一层函数/配置构造器的命名参数 `enabled_self_collisions` 传入 `False`；该参数在本项目中表示本功能块中的 `enabled_self_collisions` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    enabled_self_collisions=False,
# 【L1342】给上一层函数/配置构造器的命名参数 `solver_position_iteration_count` 传入 `64`；该参数在本项目中表示位置、数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=64,
# 【L1343】给上一层函数/配置构造器的命名参数 `solver_velocity_iteration_count` 传入 `4`；该参数在本项目中表示数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1344】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1345】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1346】得到 `init_state`，它在本项目中表示状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ArticulationCfg.InitialStateCfg(`；`ArticulationCfg` 表示本功能块中的 `ArticulationCfg` 值；`InitialStateCfg` 表示本功能块中的 `InitialStateCfg` 值。
            init_state=ArticulationCfg.InitialStateCfg(
# 【L1347】给上一层函数/配置构造器的命名参数 `pos` 传入 `tuple(robot_base_position)`；该参数在本项目中表示本功能块中的 `pos` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(robot_base_position),
# 【L1348】给上一层函数/配置构造器的命名参数 `joint_pos` 传入 `{"joint_.*": 0.0, "tool_.*": 0.0}`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                joint_pos={"joint_.*": 0.0, "tool_.*": 0.0},
# 【L1349】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1350】得到 `actuators`，它在本项目中表示本功能块中的 `actuators` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            actuators={
# 【L1351】定义字典/JSON 字段 `arm`，它表示“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的 `arm` 数据；字段值来自 `ImplicitActuatorCfg(`，因此保存/传递的是这个表达式当前计算出的结果。
                "arm": ImplicitActuatorCfg(
# 【L1352】给上一层函数/配置构造器的命名参数 `joint_names_expr` 传入 `["joint_[1-6]"]`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["joint_[1-6]"],
# 【L1353】给上一层函数/配置构造器的命名参数 `effort_limit_sim` 传入 `args.arm_effort_limit_sim`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.arm_effort_limit_sim,
# 【L1354】给上一层函数/配置构造器的命名参数 `velocity_limit_sim` 传入 `1.0`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1355】给上一层函数/配置构造器的命名参数 `stiffness` 传入 `args.arm_stiffness`；该参数在本项目中表示本功能块中的 `stiffness` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.arm_stiffness,
# 【L1356】给上一层函数/配置构造器的命名参数 `damping` 传入 `args.arm_damping`；该参数在本项目中表示本功能块中的 `damping` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.arm_damping,
# 【L1357】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1358】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `ImplicitActuatorCfg(`，因此保存/传递的是这个表达式当前计算出的结果。
                "gripper": ImplicitActuatorCfg(
# 【L1359】给上一层函数/配置构造器的命名参数 `joint_names_expr` 传入 `["tool_.*"]`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["tool_.*"],
# 【L1360】给上一层函数/配置构造器的命名参数 `effort_limit_sim` 传入 `args.gripper_effort_limit_sim`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.gripper_effort_limit_sim,
# 【L1361】给上一层函数/配置构造器的命名参数 `velocity_limit_sim` 传入 `1.0`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1362】给上一层函数/配置构造器的命名参数 `stiffness` 传入 `args.gripper_stiffness`；该参数在本项目中表示本功能块中的 `stiffness` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.gripper_stiffness,
# 【L1363】给上一层函数/配置构造器的命名参数 `damping` 传入 `args.gripper_damping`；该参数在本项目中表示本功能块中的 `damping` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.gripper_damping,
# 【L1364】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1365】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            },
# 【L1366】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1367】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1368】得到 `cube`，它在本项目中表示IsaacLab RigidObject；本任务被抓取和放置的方块；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RigidObject(`；`RigidObject` 表示本功能块中的 `RigidObject` 值。
    cube = RigidObject(
# 【L1369】开始调用多行函数 `RigidObjectCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        RigidObjectCfg(
# 【L1370】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/Cube"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Cube",
# 【L1371】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.CuboidCfg(`；`sim_utils` 表示仿真相关值；`CuboidCfg` 表示本功能块中的 `CuboidCfg` 值。
            spawn=sim_utils.CuboidCfg(
# 【L1372】给上一层函数/配置构造器的命名参数 `size` 传入 `BLOCK_SIZE`；该参数在本项目中表示本功能块中的 `size` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                size=BLOCK_SIZE,
# 【L1373】得到 `rigid_props`，它在本项目中表示本功能块中的 `rigid_props` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyPropertiesCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyPropertiesCfg` 表示本功能块中的 `RigidBodyPropertiesCfg` 值。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
# 【L1374】给上一层函数/配置构造器的命名参数 `disable_gravity` 传入 `not args.natural_source_gravity`；该参数在本项目中表示本功能块中的 `disable_gravity` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    disable_gravity=not args.natural_source_gravity,
# 【L1375】给上一层函数/配置构造器的命名参数 `solver_position_iteration_count` 传入 `32`；该参数在本项目中表示位置、数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=32,
# 【L1376】给上一层函数/配置构造器的命名参数 `solver_velocity_iteration_count` 传入 `4`；该参数在本项目中表示数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1377】给上一层函数/配置构造器的命名参数 `max_depenetration_velocity` 传入 `1.0`；该参数在本项目中表示本功能块中的 `max_depenetration_velocity` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    max_depenetration_velocity=1.0,
# 【L1378】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1379】给上一层函数/配置构造器的命名参数 `mass_props` 传入 `sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG)`；该参数在本项目中表示本功能块中的 `mass_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                mass_props=sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG),
# 【L1380】给上一层函数/配置构造器的命名参数 `collision_props` 传入 `sim_utils.CollisionPropertiesCfg()`；该参数在本项目中表示本功能块中的 `collision_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L1381】给上一层函数/配置构造器的命名参数 `visual_material` 传入 `sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08))`；该参数在本项目中表示本功能块中的 `visual_material` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
# 【L1382】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
                physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1383】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.5`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    static_friction=1.5,
# 【L1384】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `1.2`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    dynamic_friction=1.2,
# 【L1385】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    restitution=0.0,
# 【L1386】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    friction_combine_mode="max",
# 【L1387】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1388】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1389】得到 `init_state`，它在本项目中表示状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RigidObjectCfg.InitialStateCfg(`；`RigidObjectCfg` 表示本功能块中的 `RigidObjectCfg` 值；`InitialStateCfg` 表示本功能块中的 `InitialStateCfg` 值。
            init_state=RigidObjectCfg.InitialStateCfg(
# 【L1390】给上一层函数/配置构造器的命名参数 `pos` 传入 `tuple(source_block_position)`；该参数在本项目中表示本功能块中的 `pos` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(source_block_position),
# 【L1391】给上一层函数/配置构造器的命名参数 `rot` 传入 `tuple(source_block_quaternion)`；该参数在本项目中表示本功能块中的 `rot` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rot=tuple(source_block_quaternion),
# 【L1392】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1393】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1394】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1395】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    external_camera = None
# 【L1396】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    wrist_camera = None
# 【L1397】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
    if args.record_images:
# 【L1398】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Camera(`；`Camera` 表示本功能块中的 `Camera` 值。
        external_camera = Camera(
# 【L1399】开始调用多行函数 `CameraCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            CameraCfg(
# 【L1400】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/ExternalCamera"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/ExternalCamera",
# 【L1401】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1402】给上一层函数/配置构造器的命名参数 `height` 传入 `480`；该参数在本项目中表示本功能块中的 `height` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1403】给上一层函数/配置构造器的命名参数 `width` 传入 `640`；该参数在本项目中表示本功能块中的 `width` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1404】给上一层函数/配置构造器的命名参数 `data_types` 传入 `["rgb"]`；该参数在本项目中表示本功能块中的 `data_types` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1405】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.PinholeCameraCfg(`；`sim_utils` 表示仿真相关值；`PinholeCameraCfg` 表示本功能块中的 `PinholeCameraCfg` 值。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1406】给上一层函数/配置构造器的命名参数 `focal_length` 传入 `24.0`；该参数在本项目中表示本功能块中的 `focal_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=24.0,
# 【L1407】给上一层函数/配置构造器的命名参数 `focus_distance` 传入 `2.0`；该参数在本项目中表示本功能块中的 `focus_distance` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=2.0,
# 【L1408】给上一层函数/配置构造器的命名参数 `horizontal_aperture` 传入 `20.955`；该参数在本项目中表示本功能块中的 `horizontal_aperture` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1409】给上一层函数/配置构造器的命名参数 `clipping_range` 传入 `(0.01, 10.0)`；该参数在本项目中表示本功能块中的 `clipping_range` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1410】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1411】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1412】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1413】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Camera(`；`Camera` 表示本功能块中的 `Camera` 值。
        wrist_camera = Camera(
# 【L1414】开始调用多行函数 `CameraCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            CameraCfg(
# 【L1415】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/WristCamera"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/WristCamera",
# 【L1416】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1417】给上一层函数/配置构造器的命名参数 `height` 传入 `480`；该参数在本项目中表示本功能块中的 `height` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1418】给上一层函数/配置构造器的命名参数 `width` 传入 `640`；该参数在本项目中表示本功能块中的 `width` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1419】给上一层函数/配置构造器的命名参数 `data_types` 传入 `["rgb"]`；该参数在本项目中表示本功能块中的 `data_types` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1420】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.PinholeCameraCfg(`；`sim_utils` 表示仿真相关值；`PinholeCameraCfg` 表示本功能块中的 `PinholeCameraCfg` 值。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1421】给上一层函数/配置构造器的命名参数 `focal_length` 传入 `18.0`；该参数在本项目中表示本功能块中的 `focal_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=18.0,
# 【L1422】给上一层函数/配置构造器的命名参数 `focus_distance` 传入 `1.0`；该参数在本项目中表示本功能块中的 `focus_distance` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=1.0,
# 【L1423】给上一层函数/配置构造器的命名参数 `horizontal_aperture` 传入 `20.955`；该参数在本项目中表示本功能块中的 `horizontal_aperture` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1424】给上一层函数/配置构造器的命名参数 `clipping_range` 传入 `(0.01, 10.0)`；该参数在本项目中表示本功能块中的 `clipping_range` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1425】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1426】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1427】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1428】调用 `Path`：创建路径对象；本行实际操作 `PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))`。`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxContactReportAPI` 表示本功能块中的 `PhysxContactReportAPI` 值。
    PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))
# 【L1429】开始对 `CONTACT_SENSORS` 调用多行方法 `update`：用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态；具体参数写在随后几行，用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    CONTACT_SENSORS.update(
# 【L1430】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        {
# 【L1431】把表达式/参数 `body_path.rsplit("/", 1)[-1]: ContactSensor(` 接入当前完整语句；`body_path` 表示刚体、路径相关值；`rsplit` 表示本功能块中的 `rsplit` 值；`ContactSensor` 表示本功能块中的 `ContactSensor` 值。在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            body_path.rsplit("/", 1)[-1]: ContactSensor(
# 【L1432】开始调用多行函数 `ContactSensorCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ContactSensorCfg(
# 【L1433】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `body_path`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    prim_path=body_path,
# 【L1434】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    update_period=0.0,
# 【L1435】给上一层函数/配置构造器的命名参数 `history_length` 传入 `400`；该参数在本项目中表示本功能块中的 `history_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    history_length=400,
# 【L1436】给上一层函数/配置构造器的命名参数 `filter_prim_paths_expr` 传入 `["/World/Cube"]`；该参数在本项目中表示本功能块中的 `filter_prim_paths_expr` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    filter_prim_paths_expr=["/World/Cube"],
# 【L1437】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                )
# 【L1438】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1439】开始遍历 `for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)` 中给出的序列，逐项完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)
# 【L1440】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        }
# 【L1441】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1442】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1443】得到 `isolated_paths`，它在本项目中表示本功能块中的 `isolated_paths` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    isolated_paths = []
# 【L1444】得到 `approach_arm_gravity_apis`，它在本项目中表示本功能块中的 `approach_arm_gravity_apis` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    approach_arm_gravity_apis = []
# 【L1445】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1446】得到 `path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `str(prim.GetPath())`；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值。
        path = str(prim.GetPath())
# 【L1447】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
        if (
# 【L1448】这是上一行尚未闭合的参数、数组或字典内容：`(args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)`；`disable_arm_gravity_during_approach` 表示本功能块中的 `disable_arm_gravity_during_approach` 值；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)
# 【L1449】把条件 `path in ARM_BODY_PATHS` 用“并且”接到上一行判断中；判断 `path in ARM_BODY_PATHS` 是否成立；`path` 表示路径相关值；`ARM_BODY_PATHS` 表示刚体相关值。所有连接条件共同决定是否进入后续分支。
            and path in ARM_BODY_PATHS
# 【L1450】对 `and prim` 调用 `HasAPI(UsdPhysics.RigidBodyAPI)`：调用 `and prim` 提供的 `HasAPI` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1451】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1452】得到 `rigid_body_api`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PhysxSchema.PhysxRigidBodyAPI.Apply(prim)`；`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxRigidBodyAPI` 表示本功能块中的 `PhysxRigidBodyAPI` 值；`Apply` 表示本功能块中的 `Apply` 值。
            rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
# 【L1453】对 `rigid_body_api` 调用 `CreateDisableGravityAttr().Set(True)`：调用 `rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            rigid_body_api.CreateDisableGravityAttr().Set(True)
# 【L1454】对 `approach_arm_gravity_apis` 执行 `append`，把 `rigid_body_api` 加入已有结果；该集合表示本功能块中的 `approach_arm_gravity_apis` 值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            approach_arm_gravity_apis.append(rigid_body_api)
# 【L1455】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
        if (
# 【L1456】把表达式/参数 `not args.enable_moving_gripper_gravity` 接入当前完整语句；`enable_moving_gripper_gravity` 表示夹爪相关值。在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            not args.enable_moving_gripper_gravity
# 【L1457】把条件 `path in MOVING_GRIPPER_BODY_PATHS` 用“并且”接到上一行判断中；判断 `path in MOVING_GRIPPER_BODY_PATHS` 是否成立；`path` 表示路径相关值；`MOVING_GRIPPER_BODY_PATHS` 表示夹爪、刚体相关值。所有连接条件共同决定是否进入后续分支。
            and path in MOVING_GRIPPER_BODY_PATHS
# 【L1458】对 `and prim` 调用 `HasAPI(UsdPhysics.RigidBodyAPI)`：调用 `and prim` 提供的 `HasAPI` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1459】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1460】对 `PhysxSchema.PhysxRigidBodyAPI` 调用 `Apply(prim).CreateDisableGravityAttr().Set(True)`：调用 `PhysxSchema.PhysxRigidBodyAPI` 提供的 `Apply` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
# 【L1461】对 `isolated_paths` 执行 `append`，把 `path` 加入已有结果；该集合表示本功能块中的 `isolated_paths` 值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            isolated_paths.append(path)
# 【L1462】得到 `cube_prim`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `get_current_stage().GetPrimAtPath("/World/Cube")`；`get_current_stage` 表示当前值相关值；`GetPrimAtPath` 表示本功能块中的 `GetPrimAtPath` 值；`World` 表示本功能块中的 `World` 值。
    cube_prim = get_current_stage().GetPrimAtPath("/World/Cube")
# 【L1463】得到 `cube_rigid_body_api`，它在本项目中表示任务方块、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)`；`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxRigidBodyAPI` 表示本功能块中的 `PhysxRigidBodyAPI` 值；`Apply` 表示本功能块中的 `Apply` 值。
    cube_rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)
# 【L1464】对 `cube_rigid_body_api` 调用 `CreateDisableGravityAttr().Set(not args.natural_source_gravity)`：调用 `cube_rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(not args.natural_source_gravity)
# 【L1465】得到 `cube_collision_apis`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    cube_collision_apis = []
# 【L1466】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1467】判断 `str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI)` 是否成立；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值；`startswith` 表示本功能块中的 `startswith` 值
        if str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1468】得到 `collision_api`，它在本项目中表示本功能块中的 `collision_api` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `UsdPhysics.CollisionAPI(prim)`；`UsdPhysics` 表示本功能块中的 `UsdPhysics` 值；`CollisionAPI` 表示本功能块中的 `CollisionAPI` 值；`prim` 表示本功能块中的 `prim` 值。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1469】对 `cube_collision_apis` 执行 `append`，把 `collision_api` 加入已有结果；该集合表示任务方块相关值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            cube_collision_apis.append(collision_api)
# 【L1470】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
            if args.collision_bypass_during_approach:
# 【L1471】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(False)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1472】判断 `not cube_collision_apis` 是否成立；`cube_collision_apis` 表示任务方块相关值
    if not cube_collision_apis:
# 【L1473】主动抛出 `RuntimeError("no CollisionAPI prim found below /World/Cube")` 并停止当前路径；说明当前输入违反“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("no CollisionAPI prim found below /World/Cube")
# 【L1474】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1475】对 `sim` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    sim.reset()
# 【L1476】对 `robot` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    robot.reset()
# 【L1477】对 `cube` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    cube.reset()
# 【L1478】检查 `external_camera is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if external_camera is not None:
# 【L1479】得到 `scene_center`，它在本项目中表示本功能块中的 `scene_center` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `0.5 * (source_block_position + target_block_position)`；`source_block_position` 表示源位置、位置相关值；`target_block_position` 表示目标、位置相关值。
        scene_center = 0.5 * (source_block_position + target_block_position)
# 【L1480】得到 `external_eye`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
        external_eye = torch.as_tensor(
# 【L1481】调用 `np.array`：创建 NumPy 数组；本行实际操作 `scene_center + np.array([0.70, 0.70, 0.45]),`。`scene_center` 表示本功能块中的 `scene_center` 值；`array` 表示本功能块中的 `array` 值。
            scene_center + np.array([0.70, 0.70, 0.45]),
# 【L1482】给上一层函数/配置构造器的命名参数 `device` 传入 `sim.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1483】给上一层函数/配置构造器的命名参数 `dtype` 传入 `torch.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1484】对 `)` 调用 `unsqueeze(0)`：调用 `)` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        ).unsqueeze(0)
# 【L1485】得到 `external_target`，它在本项目中表示外部相机、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
        external_target = torch.as_tensor(
# 【L1486】声明/传入参数 `scene_center`；在本项目中它表示本功能块中的 `scene_center` 值。
            scene_center,
# 【L1487】给上一层函数/配置构造器的命名参数 `device` 传入 `sim.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1488】给上一层函数/配置构造器的命名参数 `dtype` 传入 `torch.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1489】对 `)` 调用 `unsqueeze(0)`：调用 `)` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        ).unsqueeze(0)
# 【L1490】对 `external_camera` 调用 `set_world_poses_from_view(external_eye, external_target)`：调用 `external_camera` 提供的 `set_world_poses_from_view` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        external_camera.set_world_poses_from_view(external_eye, external_target)
# 【L1491】得到 `joint_names`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.joint_names)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`joint_names` 表示关节相关值。
    joint_names = list(robot.data.joint_names)
# 【L1492】得到 `arm_ids`，它在本项目中表示本功能块中的 `arm_ids` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[joint_names.index(name) for name in ARM_JOINTS]`；`joint_names` 表示关节相关值；`index` 表示索引相关值；`name` 表示本功能块中的 `name` 值。
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
# 【L1493】得到 `gripper_ids`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[index for index, name in enumerate(joint_names) if name.startswith("tool_")]`；`index` 表示索引相关值；`name` 表示本功能块中的 `name` 值；`enumerate` 表示本功能块中的 `enumerate` 值。
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
# 【L1494】判断 `GRIPPER_MASTER_JOINT not in joint_names` 是否成立；`GRIPPER_MASTER_JOINT` 表示夹爪、关节相关值；`joint_names` 表示关节相关值
    if GRIPPER_MASTER_JOINT not in joint_names:
# 【L1495】主动抛出 `RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")` 并停止当前路径；说明当前输入违反“reset、关节索引和 episode 记录器初始化”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")
# 【L1496】得到 `episode_recorder`，它在本项目中表示把同步帧保存在内存并最终写盘的记录器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    episode_recorder = None
# 【L1497】得到 `episode_capture`，它在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    episode_capture = None
# 【L1498】检查 `args.record_episode_dir is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.record_episode_dir is not None:
# 【L1499】得到 `episode_recorder`，它在本项目中表示把同步帧保存在内存并最终写盘的记录器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `EpisodeRecorder(`；`EpisodeRecorder` 表示本功能块中的 `EpisodeRecorder` 值。
        episode_recorder = EpisodeRecorder(
# 【L1500】给上一层函数/配置构造器的命名参数 `output_dir` 传入 `args.record_episode_dir.expanduser().resolve()`；该参数在本项目中表示输出相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            output_dir=args.record_episode_dir.expanduser().resolve(),
# 【L1501】给上一层函数/配置构造器的命名参数 `prompt` 传入 `args.episode_prompt`；该参数在本项目中表示本功能块中的 `prompt` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            prompt=args.episode_prompt,
# 【L1502】给上一层函数/配置构造器的命名参数 `control_hz` 传入 `1.0 / (sim.get_physics_dt() * args.record_stride_steps)`；该参数在本项目中表示本功能块中的 `control_hz` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            control_hz=1.0 / (sim.get_physics_dt() * args.record_stride_steps),
# 【L1503】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            metadata={
# 【L1504】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
                "simulation_only": True,
# 【L1505】定义字典/JSON 字段 `expert`，它表示“reset、关节索引和 episode 记录器初始化”中的 `expert` 数据；字段值来自 `None if args.pi05_closed_loop else "scripted_rm65_pick_place"`，因此保存/传递的是这个表达式当前计算出的结果。
                "expert": None if args.pi05_closed_loop else "scripted_rm65_pick_place",
# 【L1506】定义字典/JSON 字段 `pi05_used`，它表示“reset、关节索引和 episode 记录器初始化”中的 `pi05_used` 数据；字段值来自 `args.pi05_closed_loop`，因此保存/传递的是这个表达式当前计算出的结果。
                "pi05_used": args.pi05_closed_loop,
# 【L1507】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
                "policy_checkpoint_id": (
# 【L1508】把表达式/参数 `args.policy_checkpoint_id if args.pi05_closed_loop else None` 接入当前完整语句；`policy_checkpoint_id` 表示策略、模型检查点相关值；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值。在“reset、关节索引和 episode 记录器初始化”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    args.policy_checkpoint_id if args.pi05_closed_loop else None
# 【L1509】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
                ),
# 【L1510】定义字典/JSON 字段 `images_recorded`，它表示“reset、关节索引和 episode 记录器初始化”中的 `images_recorded` 数据；字段值来自 `args.record_images`，因此保存/传递的是这个表达式当前计算出的结果。
                "images_recorded": args.record_images,
# 【L1511】定义字典/JSON 字段 `robot_base_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "robot_base_position_m": robot_base_position.tolist(),
# 【L1512】定义字典/JSON 字段 `source_block_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `source_block_position_m` 数据；字段值来自 `source_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "source_block_position_m": source_block_position.tolist(),
# 【L1513】定义字典/JSON 字段 `source_offset_xy_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `source_offset_xy_m` 数据；字段值来自 `[args.source_offset_x_m, args.source_offset_y_m]`，因此保存/传递的是这个表达式当前计算出的结果。
                "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L1514】定义字典/JSON 字段 `target_block_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `target_block_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "target_block_position_m": target_block_position.tolist(),
# 【L1515】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“reset、关节索引和 episode 记录器初始化”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1516】定义字典/JSON 字段 `record_stride_steps`，它表示“reset、关节索引和 episode 记录器初始化”中的 `record_stride_steps` 数据；字段值来自 `args.record_stride_steps`，因此保存/传递的是这个表达式当前计算出的结果。
                "record_stride_steps": args.record_stride_steps,
# 【L1517】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            },
# 【L1518】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1519】得到 `episode_capture`，它在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ExpertEpisodeCapture(`；`ExpertEpisodeCapture` 表示本功能块中的 `ExpertEpisodeCapture` 值。
        episode_capture = ExpertEpisodeCapture(
# 【L1520】给上一层函数/配置构造器的命名参数 `recorder` 传入 `episode_recorder`；该参数在本项目中表示本功能块中的 `recorder` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            recorder=episode_recorder,
# 【L1521】给上一层函数/配置构造器的命名参数 `arm_ids` 传入 `arm_ids`；该参数在本项目中表示本功能块中的 `arm_ids` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            arm_ids=arm_ids,
# 【L1522】给上一层函数/配置构造器的命名参数 `gripper_master_id` 传入 `joint_names.index(GRIPPER_MASTER_JOINT)`；该参数在本项目中表示夹爪相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1523】给上一层函数/配置构造器的命名参数 `stride_steps` 传入 `args.record_stride_steps`；该参数在本项目中表示步数相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            stride_steps=args.record_stride_steps,
# 【L1524】给上一层函数/配置构造器的命名参数 `physics_dt` 传入 `sim.get_physics_dt()`；该参数在本项目中表示本功能块中的 `physics_dt` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            physics_dt=sim.get_physics_dt(),
# 【L1525】给上一层函数/配置构造器的命名参数 `sim` 传入 `sim`；该参数在本项目中表示IsaacLab SimulationContext，负责物理时间步，会参与“reset、关节索引和 episode 记录器初始化”。
            sim=sim,
# 【L1526】给上一层函数/配置构造器的命名参数 `external_camera` 传入 `external_camera`；该参数在本项目中表示外部相机相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            external_camera=external_camera,
# 【L1527】给上一层函数/配置构造器的命名参数 `wrist_camera` 传入 `wrist_camera`；该参数在本项目中表示腕部相机相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            wrist_camera=wrist_camera,
# 【L1528】得到 `wrist_tool_body_id`，它在本项目中表示腕部相机、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            wrist_tool_body_id=(
# 【L1529】对 `list(robot.data.body_names)` 调用 `index("tool_base_link")`：调用 `list(robot.data.body_names)` 提供的 `index` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
                list(robot.data.body_names).index("tool_base_link")
# 【L1530】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
                if args.record_images
# 【L1531】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“reset、关节索引和 episode 记录器初始化”在可选数据缺失时仍有明确结果。
                else None
# 【L1532】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            ),
# 【L1533】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1534】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1535】得到 `state`，它在本项目中表示当前要写给 articulation 的全部关节目标张量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.default_joint_pos.clone()`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`default_joint_pos` 表示关节相关值。
    state = robot.data.default_joint_pos.clone()
# 【L1536】把右侧结果写进 `state[:, arm_ids]`（写入 `state[:, arm_ids]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`pregrasp_arm` 表示本功能块中的 `pregrasp_arm` 值；`device` 表示本功能块中的 `device` 值。
    state[:, arm_ids] = torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)
# 【L1537】把右侧结果写进 `state[:, gripper_ids]`（写入 `state[:, gripper_ids]` 指定的字段）；右侧具体做的是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
    state[:, gripper_ids] = 0.0
# 【L1538】对 `robot` 调用 `write_joint_state_to_sim(state, torch.zeros_like(state))`：调用 `robot` 提供的 `write_joint_state_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
# 【L1539】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.default_root_state[:, :7].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`default_root_state` 表示状态相关值。
    cube_pose = cube.data.default_root_state[:, :7].clone()
# 【L1540】把右侧结果写进 `cube_pose[:, :3]`（写入 `cube_pose[:, :3]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`source_block_position` 表示源位置、位置相关值；`device` 表示本功能块中的 `device` 值。
    cube_pose[:, :3] = torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)
# 【L1541】把右侧结果写进 `cube_pose[:, 3:7]`（写入 `cube_pose[:, 3:7]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
    cube_pose[:, 3:7] = torch.as_tensor(
# 【L1542】把右侧返回的多个结果按位置拆给 `source_block_quaternion, device`；`source_block_quaternion` 表示源位置、四元数相关值；`device` 表示本功能块中的 `device` 值。右侧的来源是：计算表达式 `sim.device, dtype=cube_pose.dtype`；`sim` 表示IsaacLab SimulationContext，负责物理时间步；`device` 表示本功能块中的 `device` 值；`dtype` 表示本功能块中的 `dtype` 值。
        source_block_quaternion, device=sim.device, dtype=cube_pose.dtype
# 【L1543】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1544】对 `cube` 调用 `write_root_pose_to_sim(cube_pose)`：调用 `cube` 提供的 `write_root_pose_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube.write_root_pose_to_sim(cube_pose)
# 【L1545】对 `cube` 调用 `write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))`：调用 `cube` 提供的 `write_root_velocity_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube.write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))
# 【L1546】开始调用多行函数 `hold`；随后几行会逐项给它参数，调用结果或副作用用于“写入初始状态；选择脚本专家或 π0.5 分支”。
    hold(
# 【L1547】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1548】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1549】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1550】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1551】向上一行的函数调用或容器继续传入 `60 if args.initialize_at_grasp else 240`；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值，它参与“写入初始状态；选择脚本专家或 π0.5 分支”。
        60 if args.initialize_at_grasp else 240,
# 【L1552】提供文本片段 `"SOURCE_SETTLE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写入初始状态；选择脚本专家或 π0.5 分支”中的帮助说明、错误原因、任务名称或报告文字。
        "SOURCE_SETTLE",
# 【L1553】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1554】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1555】得到 `settled_source_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    settled_source_position = cube.data.root_pos_w[0].clone()
# 【L1556】得到 `settled_source_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.root_quat_w[0].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_quat_w` 表示本功能块中的 `root_quat_w` 值。
    settled_source_quaternion = cube.data.root_quat_w[0].clone()
# 【L1557】把 `"PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True` 的当前值/文字输出到终端；它用于观察“写入初始状态；选择脚本专家或 π0.5 分支”进度，也给日志留下可搜索证据。
    print("PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True)
# 【L1558】空行：分隔“写入初始状态；选择脚本专家或 π0.5 分支”中的逻辑段，让结构更容易看清。

# 【L1559】判断 `args.pi05_closed_loop` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
    if args.pi05_closed_loop:
# 【L1560】断言 `episode_capture is not None` 必须成立；这是开发期内部一致性检查，失败说明“写入初始状态；选择脚本专家或 π0.5 分支”此前产生了不可能的状态。
        assert episode_capture is not None
# 【L1561】断言 `episode_recorder is not None` 必须成立；这是开发期内部一致性检查，失败说明“写入初始状态；选择脚本专家或 π0.5 分支”此前产生了不可能的状态。
        assert episode_recorder is not None
# 【L1562】结束当前函数并把 `run_pi05_closed_loop(` 交回调用者；这个值的含义是：计算表达式 `run_pi05_closed_loop(`；`run_pi05_closed_loop` 表示本功能块中的 `run_pi05_closed_loop` 值。
        return run_pi05_closed_loop(
# 【L1563】给上一层函数/配置构造器的命名参数 `sim` 传入 `sim`；该参数在本项目中表示IsaacLab SimulationContext，负责物理时间步，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            sim=sim,
# 【L1564】给上一层函数/配置构造器的命名参数 `robot` 传入 `robot`；该参数在本项目中表示IsaacLab Articulation；表示有多个关节的 RM65+4C2，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            robot=robot,
# 【L1565】给上一层函数/配置构造器的命名参数 `cube` 传入 `cube`；该参数在本项目中表示IsaacLab RigidObject；本任务被抓取和放置的方块，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            cube=cube,
# 【L1566】给上一层函数/配置构造器的命名参数 `state` 传入 `state`；该参数在本项目中表示当前要写给 articulation 的全部关节目标张量，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            state=state,
# 【L1567】给上一层函数/配置构造器的命名参数 `arm_ids` 传入 `arm_ids`；该参数在本项目中表示本功能块中的 `arm_ids` 值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            arm_ids=arm_ids,
# 【L1568】给上一层函数/配置构造器的命名参数 `gripper_ids` 传入 `gripper_ids`；该参数在本项目中表示夹爪相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_ids=gripper_ids,
# 【L1569】给上一层函数/配置构造器的命名参数 `gripper_master_id` 传入 `joint_names.index(GRIPPER_MASTER_JOINT)`；该参数在本项目中表示夹爪相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1570】给上一层函数/配置构造器的命名参数 `target_block_position` 传入 `target_block_position`；该参数在本项目中表示目标、位置相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_block_position=target_block_position,
# 【L1571】给上一层函数/配置构造器的命名参数 `settled_source_position` 传入 `settled_source_position`；该参数在本项目中表示源位置、位置相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            settled_source_position=settled_source_position,
# 【L1572】给上一层函数/配置构造器的命名参数 `target_platform_collision_apis` 传入 `target_platform_collision_apis`；该参数在本项目中表示目标、支撑平台相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_platform_collision_apis=target_platform_collision_apis,
# 【L1573】给上一层函数/配置构造器的命名参数 `episode_capture` 传入 `episode_capture`；该参数在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            episode_capture=episode_capture,
# 【L1574】给上一层函数/配置构造器的命名参数 `episode_recorder` 传入 `episode_recorder`；该参数在本项目中表示把同步帧保存在内存并最终写盘的记录器，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            episode_recorder=episode_recorder,
# 【L1575】给上一层函数/配置构造器的命名参数 `output` 传入 `output`；该参数在本项目中表示输出文件路径，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            output=output,
# 【L1576】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        )
# 【L1577】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1578】得到 `approach_waypoints`，它在本项目中表示本功能块中的 `approach_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]`；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值；`reversed` 表示本功能块中的 `reversed` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。
    approach_waypoints = [] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]
# 【L1579】得到 `previous_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pregrasp_arm`；`pregrasp_arm` 表示本功能块中的 `pregrasp_arm` 值。
    previous_waypoint = pregrasp_arm
# 【L1580】遍历 `enumerate(approach_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for index, waypoint in enumerate(approach_waypoints, start=1):
# 【L1581】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“脚本专家的接近、闭合夹爪和接触诊断”。
        smooth_move(
# 【L1582】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
            sim,
# 【L1583】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            robot,
# 【L1584】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
            cube,
# 【L1585】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
            state,
# 【L1586】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
            arm_ids,
# 【L1587】声明/传入参数 `previous_waypoint`；在本项目中它表示上一值相关值。
            previous_waypoint,
# 【L1588】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
            waypoint,
# 【L1589】向上一行的函数调用或容器继续传入 `120`；逗号说明后面还有同级参数，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
            120,
# 【L1590】向上一行的函数调用或容器继续传入 `f"APPROACH_{index}"`；`f` 表示本功能块中的 `f` 值；`APPROACH_` 表示本功能块中的 `APPROACH_` 值；`index` 表示索引相关值，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
            f"APPROACH_{index}",
# 【L1591】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
            episode_capture,
# 【L1592】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1593】得到 `previous_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
        previous_waypoint = waypoint
# 【L1594】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
    if args.collision_bypass_during_approach:
# 【L1595】调用 `hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)
# 【L1596】得到 `pre_restore_arm_error`，它在本项目中表示本功能块中的 `pre_restore_arm_error` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
        pre_restore_arm_error = float(
# 【L1597】对 `np` 调用 `max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))`：调用 `np` 提供的 `max` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            np.max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))
# 【L1598】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1599】把 `f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print(f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True)
# 【L1600】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
    if args.collision_bypass_during_approach:
# 【L1601】遍历 `cube_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
        for collision_api in cube_collision_apis:
# 【L1602】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1603】把 `"PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True)
# 【L1604】判断 `not args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值
    if not args.initialize_at_grasp:
# 【L1605】调用 `hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)
# 【L1606】得到 `actual_approach_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    actual_approach_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1607】得到 `open_l2_midpoint`，它在本项目中表示本功能块中的 `open_l2_midpoint` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.5 * (` 的结果保存下来，供当前功能块后续使用。
    open_l2_midpoint = 0.5 * (
# 【L1608】调用 `tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")
# 【L1609】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1610】得到 `open_midpoint_to_block`，它在本项目中表示本功能块中的 `open_midpoint_to_block` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    open_midpoint_to_block = float(
# 【L1611】对 `torch.linalg` 调用 `vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])`：调用 `torch.linalg` 提供的 `vector_norm` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        torch.linalg.vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])
# 【L1612】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1613】得到 `open_midpoint_world`，它在本项目中表示本功能块中的 `open_midpoint_world` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `open_l2_midpoint.detach().cpu().numpy()`；`open_l2_midpoint` 表示本功能块中的 `open_l2_midpoint` 值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    open_midpoint_world = open_l2_midpoint.detach().cpu().numpy()
# 【L1614】得到 `open_midpoint_minus_block`，它在本项目中表示本功能块中的 `open_midpoint_minus_block` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    open_midpoint_minus_block = open_midpoint_world - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1615】得到 `open_pad_center_world_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    open_pad_center_world_by_body = {
# 【L1616】对 `body_name: local_point_world_position(robot, body_name, local_position)` 调用 `detach().cpu().tolist()`：调用 `body_name: local_point_world_position(robot, body_name, local_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1617】开始遍历 `for body_name, local_position in PAD_LOCAL_CENTERS.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1618】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1619】得到 `open_pad_center_minus_block_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    open_pad_center_minus_block_by_body = {
# 【L1620】把表达式/参数 `body_name: (` 接入当前完整语句；`body_name` 表示刚体相关值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: (
# 【L1621】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `np.asarray(world_position, dtype=np.float64)`。`asarray` 表示本功能块中的 `asarray` 值；`world_position` 表示位置相关值。
            np.asarray(world_position, dtype=np.float64)
# 【L1622】对 `- cube.data.root_pos_w[0]` 调用 `detach().cpu().numpy()`：调用 `- cube.data.root_pos_w[0]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1623】对 `)` 调用 `tolist()`：调用 `)` 提供的 `tolist` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        ).tolist()
# 【L1624】开始遍历 `for body_name, world_position in open_pad_center_world_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, world_position in open_pad_center_world_by_body.items()
# 【L1625】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1626】把 `` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
    print(
# 【L1627】提供文本片段 `"PICK_PLACE_APPROACH="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "PICK_PLACE_APPROACH="
# 【L1628】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
        + json.dumps(
# 【L1629】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L1630】定义字典/JSON 字段 `max_arm_joint_error_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
                "max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1631】定义字典/JSON 字段 `l2_midpoint_to_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
                "l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L1632】定义字典/JSON 字段 `l2_midpoint_minus_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1633】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L1634】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L1635】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L1636】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1637】得到 `close_start`，它在本项目中表示本功能块中的 `close_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.zeros(len(gripper_ids), dtype=np.float64)`；`zeros` 表示本功能块中的 `zeros` 值；`gripper_ids` 表示夹爪相关值；`dtype` 表示本功能块中的 `dtype` 值。
    close_start = np.zeros(len(gripper_ids), dtype=np.float64)
# 【L1638】得到 `close_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)`；`full` 表示本功能块中的 `full` 值；`gripper_ids` 表示夹爪相关值；`gripper_close_target_rad` 表示夹爪、目标相关值。
    close_target = np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)
# 【L1639】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“脚本专家的接近、闭合夹爪和接触诊断”。
    smooth_move(
# 【L1640】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1641】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1642】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1643】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1644】声明/传入参数 `gripper_ids`；在本项目中它表示夹爪相关值。
        gripper_ids,
# 【L1645】声明/传入参数 `close_start`；在本项目中它表示本功能块中的 `close_start` 值。
        close_start,
# 【L1646】声明/传入参数 `close_target`；在本项目中它表示目标相关值。
        close_target,
# 【L1647】向上一行的函数调用或容器继续传入 `180`；逗号说明后面还有同级参数，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
        180,
# 【L1648】提供文本片段 `"CLOSE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "CLOSE",
# 【L1649】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1650】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1651】调用 `hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
    hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)
# 【L1652】得到 `closed_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    closed_position = cube.data.root_pos_w[0].clone()
# 【L1653】得到 `closed_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    closed_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1654】得到 `closed_pad_center_world_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    closed_pad_center_world_by_body = {
# 【L1655】对 `body_name: local_point_world_position(robot, body_name, local_position)` 调用 `detach().cpu().tolist()`：调用 `body_name: local_point_world_position(robot, body_name, local_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1656】开始遍历 `for body_name, local_position in PAD_LOCAL_CENTERS.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1657】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1658】得到 `closed_pad_center_minus_block_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    closed_pad_center_minus_block_by_body = {
# 【L1659】得到 `body_name`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.float64) - closed_position.detach().cpu().numpy()).tolist()`；`float64` 表示本功能块中的 `float64` 值；`closed_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值。
        body_name: (np.asarray(world_position, dtype=np.float64) - closed_position.detach().cpu().numpy()).tolist()
# 【L1660】开始遍历 `for body_name, world_position in closed_pad_center_world_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, world_position in closed_pad_center_world_by_body.items()
# 【L1661】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1662】得到 `closed_l2_gap`，它在本项目中表示本功能块中的 `closed_l2_gap` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    closed_l2_gap = float(
# 【L1663】开始对 `torch.linalg` 调用多行方法 `vector_norm`：调用 `torch.linalg` 提供的 `vector_norm` 操作；具体参数写在随后几行，用于“脚本专家的接近、闭合夹爪和接触诊断”。
        torch.linalg.vector_norm(
# 【L1664】调用 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L1665】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1666】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1667】得到 `closed_gripper_joint_position`，它在本项目中表示夹爪、关节、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    closed_gripper_joint_position = robot.data.joint_pos[0, gripper_ids].clone()
# 【L1668】得到 `close_contact_force_statistics_by_body`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    close_contact_force_statistics_by_body = {}
# 【L1669】遍历 `CONTACT_SENSORS.items()`，每次把当前元素放进 `body_name, contact_sensor`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L1670】把右侧结果写进 `close_contact_force_statistics_by_body[body_name]`（写入 `close_contact_force_statistics_by_body[body_name]` 指定的字段）；右侧具体做的是：计算表达式 `contact_force_statistics(contact_sensor)`；`contact_force_statistics` 表示接触、力相关值；`contact_sensor` 表示接触相关值。
        close_contact_force_statistics_by_body[body_name] = contact_force_statistics(contact_sensor)
# 【L1671】得到 `close_contact_force_by_body_n`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_contact_force_by_body_n = {
# 【L1672】把表达式/参数 `body_name: statistics["peak_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`peak_n` 表示本功能块中的 `peak_n` 值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["peak_n"]
# 【L1673】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1674】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1675】得到 `close_current_contact_force_by_body_n`，它在本项目中表示当前值、接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_current_contact_force_by_body_n = {
# 【L1676】把表达式/参数 `body_name: statistics["current_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`current_n` 表示当前值相关值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["current_n"]
# 【L1677】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1678】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1679】得到 `close_recent_mean_contact_force_by_body_n`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_recent_mean_contact_force_by_body_n = {
# 【L1680】把表达式/参数 `body_name: statistics["recent_mean_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["recent_mean_n"]
# 【L1681】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1682】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1683】得到 `close_current_contact_force_vector_by_body_n`，它在本项目中表示当前值、接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    close_current_contact_force_vector_by_body_n = {}
# 【L1684】遍历 `CONTACT_SENSORS.items()`，每次把当前元素放进 `body_name, contact_sensor`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L1685】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w` 表示力相关值。
        current = contact_sensor.data.force_matrix_w
# 【L1686】把右侧结果写进 `close_current_contact_force_vector_by_body_n[body_name]`（写入 `close_current_contact_force_vector_by_body_n[body_name]` 指定的字段）；右侧具体做的是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        close_current_contact_force_vector_by_body_n[body_name] = (
# 【L1687】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, 0.0]`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            [0.0, 0.0, 0.0]
# 【L1688】检查 `current is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
            if current is None
# 【L1689】对 `else current` 调用 `reshape(-1, 3).sum(dim=0).detach().cpu().tolist()`：调用 `else current` 提供的 `reshape` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            else current.reshape(-1, 3).sum(dim=0).detach().cpu().tolist()
# 【L1690】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1691】得到 `close_left_finger_contact_force_n`，它在本项目中表示接触、力相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `max(` 的结果保存下来，供当前功能块后续使用。
    close_left_finger_contact_force_n = max(
# 【L1692】这是生成式/推导式 `close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`close_contact_force_by_body_n` 表示接触、力、刚体相关值；`name` 表示本功能块中的 `name` 值；`tool_l_1` 表示本功能块中的 `tool_l_1` 值。产生的序列交给外层列表、字典或函数完成“脚本专家的接近、闭合夹爪和接触诊断”。
        close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")
# 【L1693】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1694】得到 `close_right_finger_contact_force_n`，它在本项目中表示接触、力相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `max(` 的结果保存下来，供当前功能块后续使用。
    close_right_finger_contact_force_n = max(
# 【L1695】这是生成式/推导式 `close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`close_contact_force_by_body_n` 表示接触、力、刚体相关值；`name` 表示本功能块中的 `name` 值；`tool_r_1` 表示本功能块中的 `tool_r_1` 值。产生的序列交给外层列表、字典或函数完成“脚本专家的接近、闭合夹爪和接触诊断”。
        close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")
# 【L1696】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1697】把 `` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
    print(
# 【L1698】提供文本片段 `"PICK_PLACE_CLOSE_CONTACT="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "PICK_PLACE_CLOSE_CONTACT="
# 【L1699】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
        + json.dumps(
# 【L1700】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L1701】定义字典/JSON 字段 `left_finger_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `left_finger_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "left_finger_force_n": close_left_finger_contact_force_n,
# 【L1702】定义字典/JSON 字段 `right_finger_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `right_finger_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "right_finger_force_n": close_right_finger_contact_force_n,
# 【L1703】定义字典/JSON 字段 `current_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `current_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "current_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1704】定义字典/JSON 字段 `recent_mean_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `recent_mean_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "recent_mean_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1705】定义字典/JSON 字段 `current_force_vector_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `current_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "current_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1706】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L1707】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L1708】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L1709】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1710】空行：分隔“脚本专家的接近、闭合夹爪和接触诊断”中的逻辑段，让结构更容易看清。

# 【L1711】判断 `args.diagnose_approach_only` 是否成立；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值
    if args.diagnose_approach_only:
# 【L1712】得到 `diagnostic`，它在本项目中表示本功能块中的 `diagnostic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        diagnostic = {
# 【L1713】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"diagnostic"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "diagnostic",
# 【L1714】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L1715】定义字典/JSON 字段 `collision_bypass_during_approach`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `collision_bypass_during_approach` 数据；字段值来自 `args.collision_bypass_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L1716】定义字典/JSON 字段 `initialized_at_grasp`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L1717】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L1718】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L1719】定义字典/JSON 字段 `natural_source_gravity`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "natural_source_gravity": args.natural_source_gravity,
# 【L1720】定义字典/JSON 字段 `moving_gripper_gravity_disabled`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `moving_gripper_gravity_disabled` 数据；字段值来自 `not args.enable_moving_gripper_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L1721】定义字典/JSON 字段 `arm_actuator`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_actuator": {
# 【L1722】定义字典/JSON 字段 `effort_limit_sim`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `effort_limit_sim` 数据；字段值来自 `args.arm_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.arm_effort_limit_sim,
# 【L1723】定义字典/JSON 字段 `stiffness`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `stiffness` 数据；字段值来自 `args.arm_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.arm_stiffness,
# 【L1724】定义字典/JSON 字段 `damping`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `damping` 数据；字段值来自 `args.arm_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.arm_damping,
# 【L1725】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L1726】定义字典/JSON 字段 `gripper_actuator`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_actuator": {
# 【L1727】定义字典/JSON 字段 `effort_limit_sim`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L1728】定义字典/JSON 字段 `stiffness`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.gripper_stiffness,
# 【L1729】定义字典/JSON 字段 `damping`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.gripper_damping,
# 【L1730】定义字典/JSON 字段 `close_target_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "close_target_rad": args.gripper_close_target_rad,
# 【L1731】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L1732】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1733】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1734】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L1735】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L1736】定义字典/JSON 字段 `robot_base_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L1737】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L1738】定义字典/JSON 字段 `top_down_yaw_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_yaw_rad` 数据；字段值来自 `args.top_down_yaw_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L1739】定义字典/JSON 字段 `top_down_tilt_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_tilt_rad` 数据；字段值来自 `args.top_down_tilt_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L1740】定义字典/JSON 字段 `top_down_ik_multistart`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_ik_multistart` 数据；字段值来自 `args.top_down_ik_multistart`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L1741】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L1742】定义字典/JSON 字段 `top_down_blend`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_blend` 数据；字段值来自 `args.top_down_blend`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_blend": args.top_down_blend,
# 【L1743】定义字典/JSON 字段 `reference_block_from_link_local_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `reference_block_from_link_local_m` 数据；字段值来自 `reference_block_from_link_local.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L1744】定义字典/JSON 字段 `lift_mode`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_mode": args.lift_mode,
# 【L1745】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L1746】定义字典/JSON 字段 `settled_source_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L1747】定义字典/JSON 字段 `settled_source_quaternion_wxyz`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `settled_source_quaternion_wxyz` 数据；字段值来自 `settled_source_quaternion.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L1748】定义字典/JSON 字段 `closed_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_position_m` 数据；字段值来自 `closed_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L1749】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L1750】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L1751】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L1752】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1753】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1754】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1755】定义字典/JSON 字段 `approach_actual_arm_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_actual_arm_joint_position_rad` 数据；字段值来自 `actual_approach_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_actual_arm_joint_position_rad": actual_approach_arm.tolist(),
# 【L1756】定义字典/JSON 字段 `approach_target_arm_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_target_arm_joint_position_rad` 数据；字段值来自 `grasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_target_arm_joint_position_rad": grasp_arm.tolist(),
# 【L1757】定义字典/JSON 字段 `cartesian_retreat_distances_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_retreat_distances_m` 数据；字段值来自 `retreat_distances.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L1758】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_pregrasp_joint_position_rad` 数据；字段值来自 `pregrasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L1759】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1760】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L1761】定义字典/JSON 字段 `approach_l2_midpoint_world_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_world_m` 数据；字段值来自 `open_midpoint_world.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L1762】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1763】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_pad_center_world_by_body_m` 数据；字段值来自 `open_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L1764】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_pad_center_minus_block_by_body_m` 数据；字段值来自 `open_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L1765】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_pad_center_world_by_body_m` 数据；字段值来自 `closed_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L1766】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L1767】定义字典/JSON 字段 `closed_l2_tip_gap_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_l2_tip_gap_m` 数据；字段值来自 `closed_l2_gap`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_l2_tip_gap_m": closed_l2_gap,
# 【L1768】定义字典/JSON 字段 `closed_gripper_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_gripper_joint_position_rad` 数据；字段值来自 `closed_gripper_joint_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L1769】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        }
# 【L1770】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1771】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L1772】把 `json.dumps(diagnostic, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L1773】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
        return 0
# 【L1774】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1775】判断 `not args.disable_arm_gravity_through_transport` 是否成立；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值
    if not args.disable_arm_gravity_through_transport:
# 【L1776】遍历 `approach_arm_gravity_apis`，每次把当前元素放进 `rigid_body_api`；这会逐个处理“恢复重力、抬升以及抬升失败早停”所需的帧、episode、动作或实验 case。
        for rigid_body_api in approach_arm_gravity_apis:
# 【L1777】对 `rigid_body_api` 调用 `CreateDisableGravityAttr().Set(False)`：调用 `rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“恢复重力、抬升以及抬升失败早停”。
            rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L1778】判断 `approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport` 是否成立；`approach_arm_gravity_apis` 表示本功能块中的 `approach_arm_gravity_apis` 值；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值
    if approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport:
# 【L1779】把 `"PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True)
# 【L1780】对 `cube_rigid_body_api` 调用 `CreateDisableGravityAttr().Set(False)`：调用 `cube_rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“恢复重力、抬升以及抬升失败早停”。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L1781】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“恢复重力、抬升以及抬升失败早停”。
    smooth_move(
# 【L1782】把表达式/参数 `sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture` 接入当前完整语句；`sim` 表示IsaacLab SimulationContext，负责物理时间步；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块。在“恢复重力、抬升以及抬升失败早停”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture
# 【L1783】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
    )
# 【L1784】调用 `hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“恢复重力、抬升以及抬升失败早停”。
    hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)
# 【L1785】得到 `lifted_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    lifted_position = cube.data.root_pos_w[0].clone()
# 【L1786】得到 `lifted_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    lifted_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1787】得到 `actual_lift_link_translation`，它在本项目中表示物理仿真实际值、机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lifted_link_6_position - closed_link_6_position`；`lifted_link_6_position` 表示机器人连杆、位置相关值；`closed_link_6_position` 表示机器人连杆、位置相关值。
    actual_lift_link_translation = lifted_link_6_position - closed_link_6_position
# 【L1788】得到 `actual_lift_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    actual_lift_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1789】得到 `lift_height_after_attempt`，它在本项目中表示本功能块中的 `lift_height_after_attempt` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float((lifted_position[2] - closed_position[2]).item())`；`lifted_position` 表示位置相关值；`closed_position` 表示位置相关值；`item` 表示本功能块中的 `item` 值。
    lift_height_after_attempt = float((lifted_position[2] - closed_position[2]).item())
# 【L1790】判断 `lift_height_after_attempt <= 0.02` 是否成立；`lift_height_after_attempt` 表示本功能块中的 `lift_height_after_attempt` 值
    if lift_height_after_attempt <= 0.02:
# 【L1791】得到 `failed_lift_report`，它在本项目中表示失败、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        failed_lift_report = {
# 【L1792】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"fail"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "fail",
# 【L1793】定义字典/JSON 字段 `failure_stage`，它表示“恢复重力、抬升以及抬升失败早停”中的 `failure_stage` 数据；字段值来自 `"lift"`，因此保存/传递的是这个表达式当前计算出的结果。
            "failure_stage": "lift",
# 【L1794】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L1795】定义字典/JSON 字段 `pi05_used`，它表示“恢复重力、抬升以及抬升失败早停”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
            "pi05_used": False,
# 【L1796】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
            "real_robot_command_sent": False,
# 【L1797】定义字典/JSON 字段 `natural_source_gravity`，它表示“恢复重力、抬升以及抬升失败早停”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "natural_source_gravity": args.natural_source_gravity,
# 【L1798】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“恢复重力、抬升以及抬升失败早停”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L1799】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1800】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1801】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L1802】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L1803】定义字典/JSON 字段 `lift_mode`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_mode": args.lift_mode,
# 【L1804】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L1805】定义字典/JSON 字段 `gripper_actuator`，它表示“恢复重力、抬升以及抬升失败早停”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_actuator": {
# 【L1806】定义字典/JSON 字段 `effort_limit_sim`，它表示“恢复重力、抬升以及抬升失败早停”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L1807】定义字典/JSON 字段 `stiffness`，它表示“恢复重力、抬升以及抬升失败早停”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.gripper_stiffness,
# 【L1808】定义字典/JSON 字段 `damping`，它表示“恢复重力、抬升以及抬升失败早停”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.gripper_damping,
# 【L1809】定义字典/JSON 字段 `close_target_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "close_target_rad": args.gripper_close_target_rad,
# 【L1810】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            },
# 【L1811】定义字典/JSON 字段 `source_platform_size_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `source_platform_size_m` 数据；字段值来自 `list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L1812】定义字典/JSON 字段 `settled_source_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L1813】定义字典/JSON 字段 `closed_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_position_m` 数据；字段值来自 `closed_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L1814】定义字典/JSON 字段 `lifted_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lifted_position_m` 数据；字段值来自 `lifted_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lifted_position_m": lifted_position.detach().cpu().tolist(),
# 【L1815】定义字典/JSON 字段 `block_lift_height_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `block_lift_height_m` 数据；字段值来自 `lift_height_after_attempt`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m": lift_height_after_attempt,
# 【L1816】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L1817】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L1818】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L1819】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1820】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1821】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1822】定义字典/JSON 字段 `closed_link_6_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_link_6_position_m` 数据；字段值来自 `closed_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L1823】定义字典/JSON 字段 `lifted_link_6_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lifted_link_6_position_m` 数据；字段值来自 `lifted_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L1824】定义字典/JSON 字段 `actual_lift_link_translation_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `actual_lift_link_translation_m` 数据；字段值来自 `actual_lift_link_translation.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L1825】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_lift_arm - lift_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L1826】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_actual_arm_joint_position_rad` 数据；字段值来自 `actual_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L1827】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_target_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L1828】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1829】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1830】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L1831】定义字典/JSON 字段 `reason`，它表示“恢复重力、抬升以及抬升失败早停”中的 `reason` 数据；字段值来自 `"The block did not clear the source support after the commanded lift."`，因此保存/传递的是这个表达式当前计算出的结果。
            "reason": "The block did not clear the source support after the commanded lift.",
# 【L1832】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
        }
# 【L1833】检查 `episode_recorder is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if episode_recorder is not None:
# 【L1834】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
            episode_recorder.metadata["task_success"] = False
# 【L1835】把右侧结果写进 `episode_recorder.metadata["failure_stage"]`（写入 `episode_recorder.metadata["failure_stage"]` 指定的字段）；右侧具体做的是：计算表达式 `"lift"`；`lift` 表示本功能块中的 `lift` 值。
            episode_recorder.metadata["failure_stage"] = "lift"
# 【L1836】得到 `episode_manifest`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
            episode_manifest = episode_recorder.save()
# 【L1837】得到 `episode_validation`，它在本项目中表示一条轨迹、校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(`；`validate_episode` 表示一条轨迹相关值。
            episode_validation = validate_episode(
# 【L1838】把表达式/参数 `episode_recorder.output_dir, require_images=args.record_images` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值；`require_images` 表示本功能块中的 `require_images` 值。在“恢复重力、抬升以及抬升失败早停”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                episode_recorder.output_dir, require_images=args.record_images
# 【L1839】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            )
# 【L1840】把右侧结果写进 `failed_lift_report["expert_episode"]`（写入 `failed_lift_report["expert_episode"]` 指定的字段）；右侧具体做的是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            failed_lift_report["expert_episode"] = {
# 【L1841】定义字典/JSON 字段 `directory`，它表示“恢复重力、抬升以及抬升失败早停”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
                "directory": str(episode_recorder.output_dir),
# 【L1842】定义字典/JSON 字段 `frame_count`，它表示“恢复重力、抬升以及抬升失败早停”中的 `frame_count` 数据；字段值来自 `episode_manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "frame_count": episode_manifest["frame_count"],
# 【L1843】定义字典/JSON 字段 `validation`，它表示“恢复重力、抬升以及抬升失败早停”中的 `validation` 数据；字段值来自 `episode_validation`，因此保存/传递的是这个表达式当前计算出的结果。
                "validation": episode_validation,
# 【L1844】定义字典/JSON 字段 `training_ready`，它表示“恢复重力、抬升以及抬升失败早停”中的 `training_ready` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                "training_ready": False,
# 【L1845】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            }
# 【L1846】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1847】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")
# 【L1848】把 `json.dumps(failed_lift_report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print(json.dumps(failed_lift_report, indent=2), flush=True)
# 【L1849】把 `"RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print("RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True)
# 【L1850】结束当前函数并把 `1` 交回调用者；这个值的含义是：把表达式 `1` 的结果保存下来，供当前功能块后续使用。
        return 1
# 【L1851】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1852】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
    smooth_move(
# 【L1853】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1854】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1855】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1856】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1857】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
        arm_ids,
# 【L1858】声明/传入参数 `lift_arm`；在本项目中它表示本功能块中的 `lift_arm` 值。
        lift_arm,
# 【L1859】声明/传入参数 `target_lift_arm`；在本项目中它表示目标相关值。
        target_lift_arm,
# 【L1860】向上一行的函数调用或容器继续传入 `360`；逗号说明后面还有同级参数，它参与“搬运到目标并沿 IK 路点下降”。
        360,
# 【L1861】提供文本片段 `"TRANSFER"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
        "TRANSFER",
# 【L1862】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1863】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
    )
# 【L1864】判断 `args.target_collision_enable_stage == "after_transfer"` 是否成立；`target_collision_enable_stage` 表示目标相关值；`after_transfer` 表示本功能块中的 `after_transfer` 值
    if args.target_collision_enable_stage == "after_transfer":
# 【L1865】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
        for collision_api in target_platform_collision_apis:
# 【L1866】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“搬运到目标并沿 IK 路点下降”。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1867】判断 `target_platform_collision_apis` 是否成立；`target_platform_collision_apis` 表示目标、支撑平台相关值
        if target_platform_collision_apis:
# 【L1868】把 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True` 的当前值/文字输出到终端；它用于观察“搬运到目标并沿 IK 路点下降”进度，也给日志留下可搜索证据。
            print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L1869】调用 `hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“搬运到目标并沿 IK 路点下降”。
            hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)
# 【L1870】得到 `pre_place_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    pre_place_position = cube.data.root_pos_w[0].clone()
# 【L1871】得到 `pre_place_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    pre_place_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1872】得到 `place_actual_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_actual_arm = None
# 【L1873】得到 `place_actual_link_6_position`，它在本项目中表示物理仿真实际值、机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_actual_link_6_position = None
# 【L1874】得到 `place_commanded_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_commanded_link_6_position = None
# 【L1875】得到 `release_start_arm`，它在本项目中表示本功能块中的 `release_start_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_lift_arm`；`target_lift_arm` 表示目标相关值。
    release_start_arm = target_lift_arm
# 【L1876】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
    if args.place_descent:
# 【L1877】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_lift_arm`；`target_lift_arm` 表示目标相关值。
        previous_place_waypoint = target_lift_arm
# 【L1878】遍历 `enumerate(place_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
        for index, waypoint in enumerate(place_waypoints, start=1):
# 【L1879】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
            smooth_move(
# 【L1880】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                sim,
# 【L1881】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                robot,
# 【L1882】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                cube,
# 【L1883】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                state,
# 【L1884】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                arm_ids,
# 【L1885】声明/传入参数 `previous_place_waypoint`；在本项目中它表示上一值相关值。
                previous_place_waypoint,
# 【L1886】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
                waypoint,
# 【L1887】向上一行的函数调用或容器继续传入 `args.place_waypoint_steps`；`place_waypoint_steps` 表示步数相关值，它参与“搬运到目标并沿 IK 路点下降”。
                args.place_waypoint_steps,
# 【L1888】向上一行的函数调用或容器继续传入 `f"PLACE_DESCENT_{index}"`；`f` 表示本功能块中的 `f` 值；`PLACE_DESCENT_` 表示本功能块中的 `PLACE_DESCENT_` 值；`index` 表示索引相关值，它参与“搬运到目标并沿 IK 路点下降”。
                f"PLACE_DESCENT_{index}",
# 【L1889】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                episode_capture,
# 【L1890】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
            )
# 【L1891】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
            previous_place_waypoint = waypoint
# 【L1892】调用 `hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“搬运到目标并沿 IK 路点下降”。
        hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)
# 【L1893】得到 `release_start_arm`，它在本项目中表示本功能块中的 `release_start_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `place_waypoints[-1]`；`place_waypoints` 表示本功能块中的 `place_waypoints` 值。
        release_start_arm = place_waypoints[-1]
# 【L1894】得到 `place_actual_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
        place_actual_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1895】得到 `place_actual_link_6_position`，它在本项目中表示物理仿真实际值、机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
        place_actual_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1896】把右侧返回的多个结果按位置拆给 `place_commanded_link_6_position, _`；`place_commanded_link_6_position` 表示机器人连杆、位置相关值；`_` 表示本功能块中的 `_` 值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        place_commanded_link_6_position, _ = lula.compute_forward_kinematics(
# 【L1897】提供文本片段 `"link_6", place_waypoints[-1]`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6", place_waypoints[-1]
# 【L1898】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
        )
# 【L1899】用 `place_commanded_link_6_position + robot_base_position` 更新 `place_commanded_link_6_position` 原值；`place_commanded_link_6_position` 表示机器人连杆、位置相关值，常用于累计步数、距离、损失或成功次数。
        place_commanded_link_6_position += robot_base_position
# 【L1900】判断 `args.target_collision_enable_stage == "after_place_descent"` 是否成立；`target_collision_enable_stage` 表示目标相关值；`after_place_descent` 表示本功能块中的 `after_place_descent` 值
        if args.target_collision_enable_stage == "after_place_descent":
# 【L1901】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
            for collision_api in target_platform_collision_apis:
# 【L1902】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“搬运到目标并沿 IK 路点下降”。
                collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1903】判断 `target_platform_collision_apis` 是否成立；`target_platform_collision_apis` 表示目标、支撑平台相关值
            if target_platform_collision_apis:
# 【L1904】把 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True` 的当前值/文字输出到终端；它用于观察“搬运到目标并沿 IK 路点下降”进度，也给日志留下可搜索证据。
                print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True)
# 【L1905】开始调用多行函数 `hold`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
                hold(
# 【L1906】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                    sim,
# 【L1907】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                    robot,
# 【L1908】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                    cube,
# 【L1909】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                    state,
# 【L1910】向上一行的函数调用或容器继续传入 `120`；逗号说明后面还有同级参数，它参与“搬运到目标并沿 IK 路点下降”。
                    120,
# 【L1911】提供文本片段 `"TARGET_COLLISION_AFTER_PLACE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
                    "TARGET_COLLISION_AFTER_PLACE_HOLD",
# 【L1912】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                    episode_capture,
# 【L1913】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
                )
# 【L1914】得到 `pre_release_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    pre_release_position = cube.data.root_pos_w[0].clone()
# 【L1915】空行：分隔“搬运到目标并沿 IK 路点下降”中的逻辑段，让结构更容易看清。

# 【L1916】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
    smooth_move(
# 【L1917】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1918】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1919】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1920】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1921】声明/传入参数 `gripper_ids`；在本项目中它表示夹爪相关值。
        gripper_ids,
# 【L1922】声明/传入参数 `close_target`；在本项目中它表示目标相关值。
        close_target,
# 【L1923】声明/传入参数 `close_start`；在本项目中它表示本功能块中的 `close_start` 值。
        close_start,
# 【L1924】向上一行的函数调用或容器继续传入 `180`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
        180,
# 【L1925】提供文本片段 `"OPEN"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
        "OPEN",
# 【L1926】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1927】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
    )
# 【L1928】判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值
    if args.unassisted_release:
# 【L1929】把 `"PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True` 的当前值/文字输出到终端；它用于观察“张开夹爪、自然释放、撤退和稳定等待”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True)
# 【L1930】调用 `hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)
# 【L1931】得到 `released_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        released_position = cube.data.root_pos_w[0].clone()
# 【L1932】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
        if args.place_descent:
# 【L1933】得到 `retreat_place_waypoints`，它在本项目中表示本功能块中的 `retreat_place_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(reversed(place_waypoints[:-1])) + [target_lift_arm]`；`reversed` 表示本功能块中的 `reversed` 值；`place_waypoints` 表示本功能块中的 `place_waypoints` 值；`target_lift_arm` 表示目标相关值。
            retreat_place_waypoints = list(reversed(place_waypoints[:-1])) + [target_lift_arm]
# 【L1934】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `release_start_arm`；`release_start_arm` 表示本功能块中的 `release_start_arm` 值。
            previous_place_waypoint = release_start_arm
# 【L1935】遍历 `enumerate(retreat_place_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“张开夹爪、自然释放、撤退和稳定等待”所需的帧、episode、动作或实验 case。
            for index, waypoint in enumerate(retreat_place_waypoints, start=1):
# 【L1936】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
                smooth_move(
# 【L1937】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                    sim,
# 【L1938】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                    robot,
# 【L1939】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                    cube,
# 【L1940】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                    state,
# 【L1941】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                    arm_ids,
# 【L1942】声明/传入参数 `previous_place_waypoint`；在本项目中它表示上一值相关值。
                    previous_place_waypoint,
# 【L1943】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
                    waypoint,
# 【L1944】向上一行的函数调用或容器继续传入 `60`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                    60,
# 【L1945】向上一行的函数调用或容器继续传入 `f"RETREAT_{index}"`；`f` 表示本功能块中的 `f` 值；`RETREAT_` 表示本功能块中的 `RETREAT_` 值；`index` 表示索引相关值，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                    f"RETREAT_{index}",
# 【L1946】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                    episode_capture,
# 【L1947】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
                )
# 【L1948】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
                previous_place_waypoint = waypoint
# 【L1949】前面的 `if/elif` 都不成立时走这里；在“张开夹爪、自然释放、撤退和稳定等待”中处理剩余输入或备用路径。
        else:
# 【L1950】断言 `release_clear_arm is not None` 必须成立；这是开发期内部一致性检查，失败说明“张开夹爪、自然释放、撤退和稳定等待”此前产生了不可能的状态。
            assert release_clear_arm is not None
# 【L1951】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
            smooth_move(
# 【L1952】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                sim,
# 【L1953】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                robot,
# 【L1954】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                cube,
# 【L1955】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                state,
# 【L1956】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                arm_ids,
# 【L1957】声明/传入参数 `release_start_arm`；在本项目中它表示本功能块中的 `release_start_arm` 值。
                release_start_arm,
# 【L1958】声明/传入参数 `release_clear_arm`；在本项目中它表示本功能块中的 `release_clear_arm` 值。
                release_clear_arm,
# 【L1959】向上一行的函数调用或容器继续传入 `240`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                240,
# 【L1960】提供文本片段 `"RETREAT"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
                "RETREAT",
# 【L1961】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                episode_capture,
# 【L1962】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
            )
# 【L1963】调用 `hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)
# 【L1964】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        final_position = cube.data.root_pos_w[0].clone()
# 【L1965】前面的 `if/elif` 都不成立时走这里；在“张开夹爪、自然释放、撤退和稳定等待”中处理剩余输入或备用路径。
    else:
# 【L1966】得到 `target_clear_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        target_clear_arm = target_lift_arm.copy()
# 【L1967】用 `target_clear_arm[1] - 0.10` 更新 `target_clear_arm[1]` 原值；`target_clear_arm[1]` 表示目标相关值，常用于累计步数、距离、损失或成功次数。
        target_clear_arm[1] -= 0.10
# 【L1968】用 `target_clear_arm[2] - 0.10` 更新 `target_clear_arm[2]` 原值；`target_clear_arm[2]` 表示目标相关值，常用于累计步数、距离、损失或成功次数。
        target_clear_arm[2] -= 0.10
# 【L1969】得到 `release_pose`，它在本项目中表示本功能块中的 `release_pose` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.root_state_w[:, :7].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_state_w` 表示状态相关值。
        release_pose = cube.data.root_state_w[:, :7].clone()
# 【L1970】把表达式/参数 `release_pose[:, 2] -= args.release_separation_assist_m` 接入当前完整语句；`release_pose` 表示本功能块中的 `release_pose` 值；`release_separation_assist_m` 表示本功能块中的 `release_separation_assist_m` 值。在“张开夹爪、自然释放、撤退和稳定等待”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        release_pose[:, 2] -= args.release_separation_assist_m
# 【L1971】对 `cube` 调用 `write_root_pose_to_sim(release_pose)`：调用 `cube` 提供的 `write_root_pose_to_sim` 操作。本行产生的修改/返回值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        cube.write_root_pose_to_sim(release_pose)
# 【L1972】得到 `release_velocity`，它在本项目中表示本功能块中的 `release_velocity` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.zeros_like(cube.data.root_vel_w)`；`zeros_like` 表示本功能块中的 `zeros_like` 值；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
        release_velocity = torch.zeros_like(cube.data.root_vel_w)
# 【L1973】把右侧结果写进 `release_velocity[:, 2]`（写入 `release_velocity[:, 2]` 指定的字段）；右侧具体做的是：计算表达式 `-RELEASE_DOWNWARD_SPEED_M_S`；`RELEASE_DOWNWARD_SPEED_M_S` 表示本功能块中的 `RELEASE_DOWNWARD_SPEED_M_S` 值。
        release_velocity[:, 2] = -RELEASE_DOWNWARD_SPEED_M_S
# 【L1974】对 `cube` 调用 `write_root_velocity_to_sim(release_velocity)`：调用 `cube` 提供的 `write_root_velocity_to_sim` 操作。本行产生的修改/返回值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        cube.write_root_velocity_to_sim(release_velocity)
# 【L1975】把 `"PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True` 的当前值/文字输出到终端；它用于观察“张开夹爪、自然释放、撤退和稳定等待”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True)
# 【L1976】调用 `hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)
# 【L1977】得到 `released_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        released_position = cube.data.root_pos_w[0].clone()
# 【L1978】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
        smooth_move(
# 【L1979】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
            sim,
# 【L1980】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            robot,
# 【L1981】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
            cube,
# 【L1982】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
            state,
# 【L1983】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
            arm_ids,
# 【L1984】声明/传入参数 `target_lift_arm`；在本项目中它表示目标相关值。
            target_lift_arm,
# 【L1985】声明/传入参数 `target_clear_arm`；在本项目中它表示目标相关值。
            target_clear_arm,
# 【L1986】向上一行的函数调用或容器继续传入 `240`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
            240,
# 【L1987】提供文本片段 `"RETREAT"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
            "RETREAT",
# 【L1988】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
            episode_capture,
# 【L1989】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
        )
# 【L1990】调用 `hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)
# 【L1991】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        final_position = cube.data.root_pos_w[0].clone()
# 【L1992】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1993】得到 `settled_source_np`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `settled_source_position.detach().cpu().numpy()`；`settled_source_position` 表示源位置、位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    settled_source_np = settled_source_position.detach().cpu().numpy()
# 【L1994】得到 `closed_np`，它在本项目中表示本功能块中的 `closed_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closed_position.detach().cpu().numpy()`；`closed_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    closed_np = closed_position.detach().cpu().numpy()
# 【L1995】得到 `lifted_np`，它在本项目中表示本功能块中的 `lifted_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lifted_position.detach().cpu().numpy()`；`lifted_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    lifted_np = lifted_position.detach().cpu().numpy()
# 【L1996】得到 `pre_release_np`，它在本项目中表示本功能块中的 `pre_release_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pre_release_position.detach().cpu().numpy()`；`pre_release_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    pre_release_np = pre_release_position.detach().cpu().numpy()
# 【L1997】得到 `released_np`，它在本项目中表示本功能块中的 `released_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `released_position.detach().cpu().numpy()`；`released_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    released_np = released_position.detach().cpu().numpy()
# 【L1998】得到 `final_np`，它在本项目中表示本功能块中的 `final_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `final_position.detach().cpu().numpy()`；`final_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    final_np = final_position.detach().cpu().numpy()
# 【L1999】得到 `source_to_target_distance`，它在本项目中表示源位置、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    source_to_target_distance = float(np.linalg.norm(target_block_position[:2] - source_block_position[:2]))
# 【L2000】得到 `lift_height`，它在本项目中表示本功能块中的 `lift_height` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(lifted_np[2] - closed_np[2])`；`lifted_np` 表示本功能块中的 `lifted_np` 值；`closed_np` 表示本功能块中的 `closed_np` 值。
    lift_height = float(lifted_np[2] - closed_np[2])
# 【L2001】得到 `final_target_xy_error`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L2002】得到 `final_target_position_error`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L2003】得到 `release_drift`，它在本项目中表示本功能块中的 `release_drift` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    release_drift = float(np.linalg.norm(final_np - released_np))
# 【L2004】得到 `final_l2_tip_gap`，它在本项目中表示本功能块中的 `final_l2_tip_gap` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    final_l2_tip_gap = float(
# 【L2005】开始对 `torch.linalg` 调用多行方法 `vector_norm`：调用 `torch.linalg` 提供的 `vector_norm` 操作；具体参数写在随后几行，用于“计算成功指标并保存专家 episode”。
        torch.linalg.vector_norm(
# 【L2006】调用 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“计算成功指标并保存专家 episode”。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L2007】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2008】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2009】得到 `all_states_finite`，它在本项目中表示本功能块中的 `all_states_finite` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    all_states_finite = bool(
# 【L2010】对 `torch` 调用 `isfinite(robot.data.joint_pos).all().item()`：调用 `torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“计算成功指标并保存专家 episode”。
        torch.isfinite(robot.data.joint_pos).all().item()
# 【L2011】对 `and torch` 调用 `isfinite(cube.data.root_state_w).all().item()`：调用 `and torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“计算成功指标并保存专家 episode”。
        and torch.isfinite(cube.data.root_state_w).all().item()
# 【L2012】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2013】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    passed = (
# 【L2014】声明/传入参数 `all_states_finite`；在本项目中它表示本功能块中的 `all_states_finite` 值。
        all_states_finite
# 【L2015】把条件 `source_to_target_distance > 0.12` 用“并且”接到上一行判断中；判断 `source_to_target_distance > 0.12` 是否成立；`source_to_target_distance` 表示源位置、目标相关值。所有连接条件共同决定是否进入后续分支。
        and source_to_target_distance > 0.12
# 【L2016】把条件 `lift_height > 0.02` 用“并且”接到上一行判断中；判断 `lift_height > 0.02` 是否成立；`lift_height` 表示本功能块中的 `lift_height` 值。所有连接条件共同决定是否进入后续分支。
        and lift_height > 0.02
# 【L2017】把条件 `final_target_xy_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_xy_error < 0.05` 是否成立；`final_target_xy_error` 表示目标相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_xy_error < 0.05
# 【L2018】把条件 `final_target_position_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_position_error < 0.05` 是否成立；`final_target_position_error` 表示目标、位置相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_position_error < 0.05
# 【L2019】把条件 `release_drift < 0.02` 用“并且”接到上一行判断中；判断 `release_drift < 0.02` 是否成立；`release_drift` 表示本功能块中的 `release_drift` 值。所有连接条件共同决定是否进入后续分支。
        and release_drift < 0.02
# 【L2020】把条件 `float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12` 用“并且”接到上一行判断中；判断 `float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12` 是否成立；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`joint_pos` 表示关节相关值。所有连接条件共同决定是否进入后续分支。
        and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12
# 【L2021】把条件 `final_l2_tip_gap > 0.06` 用“并且”接到上一行判断中；判断 `final_l2_tip_gap > 0.06` 是否成立；`final_l2_tip_gap` 表示本功能块中的 `final_l2_tip_gap` 值。所有连接条件共同决定是否进入后续分支。
        and final_l2_tip_gap > 0.06
# 【L2022】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2023】得到 `unassisted_full_task_complete`，它在本项目中表示本功能块中的 `unassisted_full_task_complete` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    unassisted_full_task_complete = bool(
# 【L2024】声明/传入参数 `passed`；在本项目中它表示当前单条任务或整套评测是否满足所有硬性门槛。
        passed
# 【L2025】把条件 `args.unassisted_release` 用“并且”接到上一行判断中；判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值。所有连接条件共同决定是否进入后续分支。
        and args.unassisted_release
# 【L2026】把条件 `args.place_descent` 用“并且”接到上一行判断中；判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值。所有连接条件共同决定是否进入后续分支。
        and args.place_descent
# 【L2027】把条件 `args.natural_source_gravity` 用“并且”接到上一行判断中；判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值。所有连接条件共同决定是否进入后续分支。
        and args.natural_source_gravity
# 【L2028】把条件 `args.enable_moving_gripper_gravity` 用“并且”接到上一行判断中；判断 `args.enable_moving_gripper_gravity` 是否成立；`enable_moving_gripper_gravity` 表示夹爪相关值。所有连接条件共同决定是否进入后续分支。
        and args.enable_moving_gripper_gravity
# 【L2029】把条件 `not args.collision_bypass_during_approach` 用“并且”接到上一行判断中；判断 `not args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值。所有连接条件共同决定是否进入后续分支。
        and not args.collision_bypass_during_approach
# 【L2030】把条件 `not args.initialize_at_grasp` 用“并且”接到上一行判断中；判断 `not args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值。所有连接条件共同决定是否进入后续分支。
        and not args.initialize_at_grasp
# 【L2031】把条件 `not args.disable_arm_gravity_during_approach` 用“并且”接到上一行判断中；判断 `not args.disable_arm_gravity_during_approach` 是否成立；`disable_arm_gravity_during_approach` 表示本功能块中的 `disable_arm_gravity_during_approach` 值。所有连接条件共同决定是否进入后续分支。
        and not args.disable_arm_gravity_during_approach
# 【L2032】把条件 `not args.disable_arm_gravity_through_transport` 用“并且”接到上一行判断中；判断 `not args.disable_arm_gravity_through_transport` 是否成立；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值。所有连接条件共同决定是否进入后续分支。
        and not args.disable_arm_gravity_through_transport
# 【L2033】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2034】得到 `expert_episode_report`，它在本项目中表示一条轨迹、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    expert_episode_report = None
# 【L2035】检查 `episode_recorder is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if episode_recorder is not None:
# 【L2036】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：计算表达式 `passed`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
        episode_recorder.metadata["task_success"] = passed
# 【L2037】把表达式/参数 `episode_recorder.metadata[` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息。在“计算成功指标并保存专家 episode”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        episode_recorder.metadata[
# 【L2038】提供文本片段 `"unassisted_full_task_complete"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“计算成功指标并保存专家 episode”中的帮助说明、错误原因、任务名称或报告文字。
            "unassisted_full_task_complete"
# 【L2039】闭合上一行开始的函数/容器后继续执行 `] = unassisted_full_task_complete` 中的索引或转换；`unassisted_full_task_complete` 表示本功能块中的 `unassisted_full_task_complete` 值，用于“计算成功指标并保存专家 episode”。
        ] = unassisted_full_task_complete
# 【L2040】得到 `episode_manifest`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
        episode_manifest = episode_recorder.save()
# 【L2041】得到 `episode_validation`，它在本项目中表示一条轨迹、校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(`；`validate_episode` 表示一条轨迹相关值。
        episode_validation = validate_episode(
# 【L2042】把表达式/参数 `episode_recorder.output_dir, require_images=args.record_images` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值；`require_images` 表示本功能块中的 `require_images` 值。在“计算成功指标并保存专家 episode”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode_recorder.output_dir, require_images=args.record_images
# 【L2043】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2044】判断 `episode_validation["status"] != "pass"` 是否成立；`episode_validation` 表示一条轨迹、校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
        if episode_validation["status"] != "pass":
# 【L2045】主动抛出 `RuntimeError(f"recorded episode failed validation: {episode_validation}")` 并停止当前路径；说明当前输入违反“计算成功指标并保存专家 episode”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed validation: {episode_validation}")
# 【L2046】得到 `expert_episode_report`，它在本项目中表示一条轨迹、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        expert_episode_report = {
# 【L2047】定义字典/JSON 字段 `directory`，它表示“计算成功指标并保存专家 episode”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
            "directory": str(episode_recorder.output_dir),
# 【L2048】定义字典/JSON 字段 `format`，它表示“计算成功指标并保存专家 episode”中的 `format` 数据；字段值来自 `episode_manifest["format"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "format": episode_manifest["format"],
# 【L2049】定义字典/JSON 字段 `frame_count`，它表示“计算成功指标并保存专家 episode”中的 `frame_count` 数据；字段值来自 `episode_manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": episode_manifest["frame_count"],
# 【L2050】定义字典/JSON 字段 `control_hz`，它表示“计算成功指标并保存专家 episode”中的 `control_hz` 数据；字段值来自 `episode_manifest["control_hz"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "control_hz": episode_manifest["control_hz"],
# 【L2051】定义字典/JSON 字段 `validation`，它表示“计算成功指标并保存专家 episode”中的 `validation` 数据；字段值来自 `episode_validation`，因此保存/传递的是这个表达式当前计算出的结果。
            "validation": episode_validation,
# 【L2052】定义字典/JSON 字段 `training_ready`，它表示“计算成功指标并保存专家 episode”中的 `training_ready` 数据；字段值来自 `bool(passed and args.record_images)`，因此保存/传递的是这个表达式当前计算出的结果。
            "training_ready": bool(passed and args.record_images),
# 【L2053】定义字典/JSON 字段 `training_blocker`，它表示“计算成功指标并保存专家 episode”中的 `training_blocker` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "training_blocker": (
# 【L2054】声明/传入参数 `None`；在本项目中它表示本功能块中的 `None` 值。
                None
# 【L2055】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
                if args.record_images
# 【L2056】这是上一行条件表达式的备用值：条件不成立时使用 `"external and wrist RGB streams were not recorded"`；它让“计算成功指标并保存专家 episode”在可选数据缺失时仍有明确结果。
                else "external and wrist RGB streams were not recorded"
# 【L2057】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
            ),
# 【L2058】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        }
# 【L2059】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L2060】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L2061】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L2062】定义字典/JSON 字段 `pi05_used`，它表示“写出完整机器可读报告”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": False,
# 【L2063】定义字典/JSON 字段 `expert`，它表示“写出完整机器可读报告”中的 `expert` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": (
# 【L2064】提供文本片段 `"scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写出完整机器可读报告”中的帮助说明、错误原因、任务名称或报告文字。
            "scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"
# 【L2065】判断 `args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值
            if args.initialize_at_grasp
# 【L2066】这是上一行条件表达式的备用值：条件不成立时使用 `"scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else "scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"
# 【L2067】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2068】定义字典/JSON 字段 `task`，它表示LeRobot 使用的语言任务字段，训练时会成为 prompt；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "task": (
# 【L2069】这是上一行尚未闭合的参数、数组或字典内容：`(`；其数据会并入上一行创建的对象，共同完成“写出完整机器可读报告”。
            (
# 【L2070】提供文本片段 `"approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写出完整机器可读报告”中的帮助说明、错误原因、任务名称或报告文字。
                "approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"
# 【L2071】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
                if args.place_descent
# 【L2072】这是上一行条件表达式的备用值：条件不成立时使用 `"approach, close, lift, transfer, unassisted release, and vertical clearance"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
                else "approach, close, lift, transfer, unassisted release, and vertical clearance"
# 【L2073】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
            )
# 【L2074】判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值
            if args.unassisted_release
# 【L2075】这是上一行条件表达式的备用值：条件不成立时使用 `"approach, close, lift, transfer, assisted release onto a platform, and retreat"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else "approach, close, lift, transfer, assisted release onto a platform, and retreat"
# 【L2076】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2077】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L2078】定义字典/JSON 字段 `expert_episode`，它表示“写出完整机器可读报告”中的 `expert_episode` 数据；字段值来自 `expert_episode_report`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert_episode": expert_episode_report,
# 【L2079】定义字典/JSON 字段 `unassisted_full_task_complete`，它表示“写出完整机器可读报告”中的 `unassisted_full_task_complete` 数据；字段值来自 `unassisted_full_task_complete`，因此保存/传递的是这个表达式当前计算出的结果。
        "unassisted_full_task_complete": unassisted_full_task_complete,
# 【L2080】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“写出完整机器可读报告”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L2081】定义字典/JSON 字段 `collision_bypass_during_approach`，它表示“写出完整机器可读报告”中的 `collision_bypass_during_approach` 数据；字段值来自 `args.collision_bypass_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
        "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L2082】定义字典/JSON 字段 `initialized_at_grasp`，它表示“写出完整机器可读报告”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
        "initialized_at_grasp": args.initialize_at_grasp,
# 【L2083】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2084】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2085】定义字典/JSON 字段 `natural_source_gravity`，它表示“写出完整机器可读报告”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "natural_source_gravity": args.natural_source_gravity,
# 【L2086】定义字典/JSON 字段 `arm_actuator`，它表示“写出完整机器可读报告”中的 `arm_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_actuator": {
# 【L2087】定义字典/JSON 字段 `effort_limit_sim`，它表示“写出完整机器可读报告”中的 `effort_limit_sim` 数据；字段值来自 `args.arm_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
            "effort_limit_sim": args.arm_effort_limit_sim,
# 【L2088】定义字典/JSON 字段 `stiffness`，它表示“写出完整机器可读报告”中的 `stiffness` 数据；字段值来自 `args.arm_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
            "stiffness": args.arm_stiffness,
# 【L2089】定义字典/JSON 字段 `damping`，它表示“写出完整机器可读报告”中的 `damping` 数据；字段值来自 `args.arm_damping`，因此保存/传递的是这个表达式当前计算出的结果。
            "damping": args.arm_damping,
# 【L2090】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2091】定义字典/JSON 字段 `gripper_actuator`，它表示“写出完整机器可读报告”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_actuator": {
# 【L2092】定义字典/JSON 字段 `effort_limit_sim`，它表示“写出完整机器可读报告”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
            "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L2093】定义字典/JSON 字段 `stiffness`，它表示“写出完整机器可读报告”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
            "stiffness": args.gripper_stiffness,
# 【L2094】定义字典/JSON 字段 `damping`，它表示“写出完整机器可读报告”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
            "damping": args.gripper_damping,
# 【L2095】定义字典/JSON 字段 `close_target_rad`，它表示“写出完整机器可读报告”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_target_rad": args.gripper_close_target_rad,
# 【L2096】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2097】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“写出完整机器可读报告”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L2098】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“写出完整机器可读报告”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L2099】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“写出完整机器可读报告”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L2100】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“写出完整机器可读报告”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L2101】定义字典/JSON 字段 `robot_base_position_m`，它表示“写出完整机器可读报告”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "robot_base_position_m": robot_base_position.tolist(),
# 【L2102】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“写出完整机器可读报告”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L2103】定义字典/JSON 字段 `top_down_yaw_rad`，它表示“写出完整机器可读报告”中的 `top_down_yaw_rad` 数据；字段值来自 `args.top_down_yaw_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L2104】定义字典/JSON 字段 `top_down_tilt_rad`，它表示“写出完整机器可读报告”中的 `top_down_tilt_rad` 数据；字段值来自 `args.top_down_tilt_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L2105】定义字典/JSON 字段 `top_down_ik_multistart`，它表示“写出完整机器可读报告”中的 `top_down_ik_multistart` 数据；字段值来自 `args.top_down_ik_multistart`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L2106】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“写出完整机器可读报告”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L2107】定义字典/JSON 字段 `top_down_blend`，它表示“写出完整机器可读报告”中的 `top_down_blend` 数据；字段值来自 `args.top_down_blend`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_blend": args.top_down_blend,
# 【L2108】定义字典/JSON 字段 `reference_block_from_link_local_m`，它表示“写出完整机器可读报告”中的 `reference_block_from_link_local_m` 数据；字段值来自 `reference_block_from_link_local.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L2109】定义字典/JSON 字段 `lift_mode`，它表示“写出完整机器可读报告”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_mode": args.lift_mode,
# 【L2110】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“写出完整机器可读报告”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L2111】定义字典/JSON 字段 `development_assistance`，它表示“写出完整机器可读报告”中的 `development_assistance` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "development_assistance": {
# 【L2112】定义字典/JSON 字段 `initialized_at_grasp`，它表示“写出完整机器可读报告”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L2113】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2114】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2115】定义字典/JSON 字段 `source_block_gravity_disabled_until_close`，它表示“写出完整机器可读报告”中的 `source_block_gravity_disabled_until_close` 数据；字段值来自 `not args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_block_gravity_disabled_until_close": not args.natural_source_gravity,
# 【L2116】定义字典/JSON 字段 `target_platform_collision_enable_stage`，它表示“写出完整机器可读报告”中的 `target_platform_collision_enable_stage` 数据；字段值来自 `args.target_collision_enable_stage`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_platform_collision_enable_stage": args.target_collision_enable_stage,
# 【L2117】定义字典/JSON 字段 `release_separation_assist_m`，它表示“写出完整机器可读报告”中的 `release_separation_assist_m` 数据；字段值来自 `0.0 if args.unassisted_release else args.release_separation_assist_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2118】定义字典/JSON 字段 `release_downward_speed_assist_m_s`，它表示“写出完整机器可读报告”中的 `release_downward_speed_assist_m_s` 数据；字段值来自 `0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S`，因此保存/传递的是这个表达式当前计算出的结果。
            "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2119】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2120】定义字典/JSON 字段 `block_mass_kg`，它表示“写出完整机器可读报告”中的 `block_mass_kg` 数据；字段值来自 `BLOCK_MASS_KG`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_mass_kg": BLOCK_MASS_KG,
# 【L2121】定义字典/JSON 字段 `block_size_m`，它表示“写出完整机器可读报告”中的 `block_size_m` 数据；字段值来自 `list(BLOCK_SIZE)`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_size_m": list(BLOCK_SIZE),
# 【L2122】定义字典/JSON 字段 `moving_gripper_gravity_disabled`，它表示“写出完整机器可读报告”中的 `moving_gripper_gravity_disabled` 数据；字段值来自 `not args.enable_moving_gripper_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L2123】定义字典/JSON 字段 `gravity_disabled_body_paths`，它表示“写出完整机器可读报告”中的 `gravity_disabled_body_paths` 数据；字段值来自 `isolated_paths`，因此保存/传递的是这个表达式当前计算出的结果。
        "gravity_disabled_body_paths": isolated_paths,
# 【L2124】定义字典/JSON 字段 `source_block_position_m`，它表示“写出完整机器可读报告”中的 `source_block_position_m` 数据；字段值来自 `source_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_position_m": source_block_position.tolist(),
# 【L2125】定义字典/JSON 字段 `source_offset_xy_m`，它表示“写出完整机器可读报告”中的 `source_offset_xy_m` 数据；字段值来自 `[args.source_offset_x_m, args.source_offset_y_m]`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L2126】定义字典/JSON 字段 `target_block_position_m`，它表示“写出完整机器可读报告”中的 `target_block_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_block_position_m": target_block_position.tolist(),
# 【L2127】定义字典/JSON 字段 `expected_lift_translation_from_fk_m`，它表示“写出完整机器可读报告”中的 `expected_lift_translation_from_fk_m` 数据；字段值来自 `expected_lift_translation.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_lift_translation_from_fk_m": expected_lift_translation.tolist(),
# 【L2128】定义字典/JSON 字段 `expected_source_lift_block_position_m`，它表示“写出完整机器可读报告”中的 `expected_source_lift_block_position_m` 数据；字段值来自 `expected_source_lift_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_source_lift_block_position_m": expected_source_lift_block_position.tolist(),
# 【L2129】定义字典/JSON 字段 `expected_release_position_before_drop_m`，它表示“写出完整机器可读报告”中的 `expected_release_position_before_drop_m` 数据；字段值来自 `target_release_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_release_position_before_drop_m": target_release_position.tolist(),
# 【L2130】定义字典/JSON 字段 `source_block_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `source_block_quaternion_wxyz` 数据；字段值来自 `source_block_quaternion.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_quaternion_wxyz": source_block_quaternion.tolist(),
# 【L2131】定义字典/JSON 字段 `target_block_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `target_block_quaternion_wxyz` 数据；字段值来自 `target_block_quaternion.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_block_quaternion_wxyz": target_block_quaternion.tolist(),
# 【L2132】定义字典/JSON 字段 `source_block_temporarily_gravity_disabled`，它表示“写出完整机器可读报告”中的 `source_block_temporarily_gravity_disabled` 数据；字段值来自 `not args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_temporarily_gravity_disabled": not args.natural_source_gravity,
# 【L2133】定义字典/JSON 字段 `source_platform_size_m`，它表示“写出完整机器可读报告”中的 `source_platform_size_m` 数据；字段值来自 `list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L2134】定义字典/JSON 字段 `gravity_enabled_after_gripper_close`，它表示“写出完整机器可读报告”中的 `gravity_enabled_after_gripper_close` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "gravity_enabled_after_gripper_close": True,
# 【L2135】定义字典/JSON 字段 `target_platform_position_m`，它表示“写出完整机器可读报告”中的 `target_platform_position_m` 数据；字段值来自 `target_platform_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_position_m": target_platform_position.tolist(),
# 【L2136】定义字典/JSON 字段 `target_platform_size_m`，它表示“写出完整机器可读报告”中的 `target_platform_size_m` 数据；字段值来自 `list(target_platform_size)`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_size_m": list(target_platform_size),
# 【L2137】定义字典/JSON 字段 `target_support_mode`，它表示“写出完整机器可读报告”中的 `target_support_mode` 数据；字段值来自 `args.target_support_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_support_mode": args.target_support_mode,
# 【L2138】定义字典/JSON 字段 `target_platform_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `target_platform_quaternion_wxyz` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_quaternion_wxyz": (
# 【L2139】把表达式/参数 `list(target_platform_orientation) if target_platform_orientation is not None else None` 接入当前完整语句；`target_platform_orientation` 表示目标、支撑平台相关值。在“写出完整机器可读报告”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            list(target_platform_orientation) if target_platform_orientation is not None else None
# 【L2140】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2141】定义字典/JSON 字段 `target_platform_collision_enabled_after_transfer`，它表示“写出完整机器可读报告”中的 `target_platform_collision_enabled_after_transfer` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_collision_enabled_after_transfer": (
# 【L2142】把比较条件 `args.target_collision_enable_stage == "after_transfer"` 接到上一行尚未结束的布尔表达式；`target_collision_enable_stage` 表示目标相关值；`after_transfer` 表示本功能块中的 `after_transfer` 值。比较结果共同决定“写出完整机器可读报告”是否通过。
            args.target_collision_enable_stage == "after_transfer"
# 【L2143】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2144】定义字典/JSON 字段 `target_collision_enable_stage`，它表示“写出完整机器可读报告”中的 `target_collision_enable_stage` 数据；字段值来自 `args.target_collision_enable_stage`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_collision_enable_stage": args.target_collision_enable_stage,
# 【L2145】定义字典/JSON 字段 `release_unassisted`，它表示“写出完整机器可读报告”中的 `release_unassisted` 数据；字段值来自 `args.unassisted_release`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_unassisted": args.unassisted_release,
# 【L2146】定义字典/JSON 字段 `place_descent`，它表示“写出完整机器可读报告”中的 `place_descent` 数据；字段值来自 `args.place_descent`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_descent": args.place_descent,
# 【L2147】定义字典/JSON 字段 `place_descent_distance_m`，它表示“写出完整机器可读报告”中的 `place_descent_distance_m` 数据；字段值来自 `args.place_descent_distance_m if args.place_descent else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_descent_distance_m": args.place_descent_distance_m if args.place_descent else None,
# 【L2148】定义字典/JSON 字段 `place_waypoint_steps`，它表示“写出完整机器可读报告”中的 `place_waypoint_steps` 数据；字段值来自 `args.place_waypoint_steps if args.place_descent else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_waypoint_steps": args.place_waypoint_steps if args.place_descent else None,
# 【L2149】定义字典/JSON 字段 `place_max_command_step_rad`，它表示“写出完整机器可读报告”中的 `place_max_command_step_rad` 数据；字段值来自 `place_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_max_command_step_rad": place_max_command_step_rad,
# 【L2150】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`，它表示“写出完整机器可读报告”中的 `place_ik_uses_base_rotation_symmetry` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_ik_uses_base_rotation_symmetry": True,
# 【L2151】定义字典/JSON 字段 `pre_place_block_position_m`，它表示“写出完整机器可读报告”中的 `pre_place_block_position_m` 数据；字段值来自 `pre_place_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_place_block_position_m": pre_place_position.detach().cpu().tolist(),
# 【L2152】定义字典/JSON 字段 `pre_place_link_6_position_m`，它表示“写出完整机器可读报告”中的 `pre_place_link_6_position_m` 数据；字段值来自 `pre_place_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_place_link_6_position_m": pre_place_link_6_position.detach().cpu().tolist(),
# 【L2153】定义字典/JSON 字段 `place_actual_block_translation_m`，它表示“写出完整机器可读报告”中的 `place_actual_block_translation_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_block_translation_m": (
# 【L2154】对 `(pre_release_position - pre_place_position)` 调用 `detach().cpu().tolist()`：调用 `(pre_release_position - pre_place_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            (pre_release_position - pre_place_position).detach().cpu().tolist()
# 【L2155】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
            if args.place_descent
# 【L2156】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2157】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2158】定义字典/JSON 字段 `place_actual_link_6_position_m`，它表示“写出完整机器可读报告”中的 `place_actual_link_6_position_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_link_6_position_m": (
# 【L2159】对 `place_actual_link_6_position` 调用 `detach().cpu().tolist()`：调用 `place_actual_link_6_position` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            place_actual_link_6_position.detach().cpu().tolist()
# 【L2160】检查 `place_actual_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_link_6_position is not None
# 【L2161】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2162】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2163】定义字典/JSON 字段 `place_commanded_link_6_position_m`，它表示“写出完整机器可读报告”中的 `place_commanded_link_6_position_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_commanded_link_6_position_m": (
# 【L2164】对 `place_commanded_link_6_position` 调用 `tolist()`：调用 `place_commanded_link_6_position` 提供的 `tolist` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            place_commanded_link_6_position.tolist()
# 【L2165】检查 `place_commanded_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_commanded_link_6_position is not None
# 【L2166】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2167】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2168】定义字典/JSON 字段 `place_actual_link_translation_m`，它表示“写出完整机器可读报告”中的 `place_actual_link_translation_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_link_translation_m": (
# 【L2169】对 `(place_actual_link_6_position - pre_place_link_6_position)` 调用 `detach().cpu().tolist()`：调用 `(place_actual_link_6_position - pre_place_link_6_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            (place_actual_link_6_position - pre_place_link_6_position).detach().cpu().tolist()
# 【L2170】检查 `place_actual_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_link_6_position is not None
# 【L2171】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2172】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2173】定义字典/JSON 字段 `place_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `place_max_arm_joint_error_rad` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_max_arm_joint_error_rad": (
# 【L2174】对 `float(np` 调用 `max(np.abs(place_actual_arm - place_waypoints[-1])))`：调用 `float(np` 提供的 `max` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            float(np.max(np.abs(place_actual_arm - place_waypoints[-1])))
# 【L2175】检查 `place_actual_arm is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_arm is not None
# 【L2176】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2177】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2178】定义字典/JSON 字段 `release_clearance_m`，它表示“写出完整机器可读报告”中的 `release_clearance_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_clearance_m": (
# 【L2179】把表达式/参数 `args.release_clearance_m if args.unassisted_release and not args.place_descent else None` 接入当前完整语句；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值；`unassisted_release` 表示本功能块中的 `unassisted_release` 值；`place_descent` 表示本功能块中的 `place_descent` 值。在“写出完整机器可读报告”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            args.release_clearance_m if args.unassisted_release and not args.place_descent else None
# 【L2180】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2181】定义字典/JSON 字段 `release_downward_speed_assist_m_s`，它表示“写出完整机器可读报告”中的 `release_downward_speed_assist_m_s` 数据；字段值来自 `0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2182】定义字典/JSON 字段 `release_separation_assist_m`，它表示“写出完整机器可读报告”中的 `release_separation_assist_m` 数据；字段值来自 `0.0 if args.unassisted_release else args.release_separation_assist_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2183】定义字典/JSON 字段 `cartesian_retreat_distances_m`，它表示“写出完整机器可读报告”中的 `cartesian_retreat_distances_m` 数据；字段值来自 `retreat_distances.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L2184】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`，它表示“写出完整机器可读报告”中的 `cartesian_pregrasp_joint_position_rad` 数据；字段值来自 `pregrasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L2185】定义字典/JSON 字段 `settled_source_position_m`，它表示“写出完整机器可读报告”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "settled_source_position_m": settled_source_np.tolist(),
# 【L2186】定义字典/JSON 字段 `settled_source_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `settled_source_quaternion_wxyz` 数据；字段值来自 `settled_source_quaternion.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L2187】定义字典/JSON 字段 `closed_position_m`，它表示“写出完整机器可读报告”中的 `closed_position_m` 数据；字段值来自 `closed_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_position_m": closed_np.tolist(),
# 【L2188】定义字典/JSON 字段 `lifted_position_m`，它表示“写出完整机器可读报告”中的 `lifted_position_m` 数据；字段值来自 `lifted_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lifted_position_m": lifted_np.tolist(),
# 【L2189】定义字典/JSON 字段 `pre_release_position_m`，它表示“写出完整机器可读报告”中的 `pre_release_position_m` 数据；字段值来自 `pre_release_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_release_position_m": pre_release_np.tolist(),
# 【L2190】定义字典/JSON 字段 `released_position_m`，它表示“写出完整机器可读报告”中的 `released_position_m` 数据；字段值来自 `released_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "released_position_m": released_np.tolist(),
# 【L2191】定义字典/JSON 字段 `final_position_m`，它表示“写出完整机器可读报告”中的 `final_position_m` 数据；字段值来自 `final_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_position_m": final_np.tolist(),
# 【L2192】定义字典/JSON 字段 `source_to_target_xy_distance_m`，它表示“写出完整机器可读报告”中的 `source_to_target_xy_distance_m` 数据；字段值来自 `source_to_target_distance`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L2193】定义字典/JSON 字段 `block_lift_height_m`，它表示“写出完整机器可读报告”中的 `block_lift_height_m` 数据；字段值来自 `lift_height`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_lift_height_m": lift_height,
# 【L2194】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L2195】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L2196】定义字典/JSON 字段 `approach_l2_midpoint_world_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_world_m` 数据；字段值来自 `open_midpoint_world.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L2197】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L2198】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`，它表示“写出完整机器可读报告”中的 `approach_pad_center_world_by_body_m` 数据；字段值来自 `open_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L2199】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`，它表示“写出完整机器可读报告”中的 `approach_pad_center_minus_block_by_body_m` 数据；字段值来自 `open_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L2200】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`，它表示“写出完整机器可读报告”中的 `closed_pad_center_world_by_body_m` 数据；字段值来自 `closed_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L2201】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“写出完整机器可读报告”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L2202】定义字典/JSON 字段 `closed_l2_tip_gap_m`，它表示“写出完整机器可读报告”中的 `closed_l2_tip_gap_m` 数据；字段值来自 `closed_l2_gap`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_l2_tip_gap_m": closed_l2_gap,
# 【L2203】定义字典/JSON 字段 `closed_gripper_joint_position_rad`，它表示“写出完整机器可读报告”中的 `closed_gripper_joint_position_rad` 数据；字段值来自 `closed_gripper_joint_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L2204】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“写出完整机器可读报告”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L2205】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“写出完整机器可读报告”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L2206】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L2207】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2208】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2209】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“写出完整机器可读报告”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2210】定义字典/JSON 字段 `closed_link_6_position_m`，它表示“写出完整机器可读报告”中的 `closed_link_6_position_m` 数据；字段值来自 `closed_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L2211】定义字典/JSON 字段 `lifted_link_6_position_m`，它表示“写出完整机器可读报告”中的 `lifted_link_6_position_m` 数据；字段值来自 `lifted_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L2212】定义字典/JSON 字段 `actual_lift_link_translation_m`，它表示“写出完整机器可读报告”中的 `actual_lift_link_translation_m` 数据；字段值来自 `actual_lift_link_translation.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L2213】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `lift_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_lift_arm - lift_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L2214】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`，它表示“写出完整机器可读报告”中的 `lift_actual_arm_joint_position_rad` 数据；字段值来自 `actual_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L2215】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`，它表示“写出完整机器可读报告”中的 `lift_target_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L2216】定义字典/JSON 字段 `final_target_xy_error_m`，它表示“写出完整机器可读报告”中的 `final_target_xy_error_m` 数据；字段值来自 `final_target_xy_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_xy_error_m": final_target_xy_error,
# 【L2217】定义字典/JSON 字段 `final_target_position_error_m`，它表示“写出完整机器可读报告”中的 `final_target_position_error_m` 数据；字段值来自 `final_target_position_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_position_error_m": final_target_position_error,
# 【L2218】定义字典/JSON 字段 `post_release_drift_m`，它表示“写出完整机器可读报告”中的 `post_release_drift_m` 数据；字段值来自 `release_drift`，因此保存/传递的是这个表达式当前计算出的结果。
        "post_release_drift_m": release_drift,
# 【L2219】定义字典/JSON 字段 `final_l2_tip_gap_m`，它表示“写出完整机器可读报告”中的 `final_l2_tip_gap_m` 数据；字段值来自 `final_l2_tip_gap`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_l2_tip_gap_m": final_l2_tip_gap,
# 【L2220】定义字典/JSON 字段 `final_gripper_joint_position_rad`，它表示“写出完整机器可读报告”中的 `final_gripper_joint_position_rad` 数据；字段值来自 `robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_gripper_joint_position_rad": robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist(),
# 【L2221】定义字典/JSON 字段 `all_states_finite`，它表示“写出完整机器可读报告”中的 `all_states_finite` 数据；字段值来自 `all_states_finite`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_states_finite": all_states_finite,
# 【L2222】定义字典/JSON 字段 `criteria`，它表示“写出完整机器可读报告”中的 `criteria` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "criteria": {
# 【L2223】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`，它表示“写出完整机器可读报告”中的 `source_to_target_xy_distance_m_gt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L2224】定义字典/JSON 字段 `block_lift_height_m_gt`，它表示“写出完整机器可读报告”中的 `block_lift_height_m_gt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m_gt": 0.02,
# 【L2225】定义字典/JSON 字段 `final_target_xy_error_m_lt`，它表示“写出完整机器可读报告”中的 `final_target_xy_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_xy_error_m_lt": 0.05,
# 【L2226】定义字典/JSON 字段 `final_target_position_error_m_lt`，它表示“写出完整机器可读报告”中的 `final_target_position_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_position_error_m_lt": 0.05,
# 【L2227】定义字典/JSON 字段 `post_release_drift_m_lt`，它表示“写出完整机器可读报告”中的 `post_release_drift_m_lt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "post_release_drift_m_lt": 0.02,
# 【L2228】定义字典/JSON 字段 `final_gripper_joint_position_rad_lt`，它表示“写出完整机器可读报告”中的 `final_gripper_joint_position_rad_lt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_gripper_joint_position_rad_lt": 0.12,
# 【L2229】定义字典/JSON 字段 `final_l2_tip_gap_m_gt`，它表示“写出完整机器可读报告”中的 `final_l2_tip_gap_m_gt` 数据；字段值来自 `0.06`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_l2_tip_gap_m_gt": 0.06,
# 【L2230】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2231】定义字典/JSON 字段 `limitation`，它表示“写出完整机器可读报告”中的 `limitation` 数据；字段值来自 `"The collision pads and scripted waypoints still require physical calibration."`，因此保存/传递的是这个表达式当前计算出的结果。
        "limitation": "The collision pads and scripted waypoints still require physical calibration.",
# 【L2232】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
    }
# 【L2233】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L2234】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L2235】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“写出完整机器可读报告”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L2236】把 `f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True` 的当前值/文字输出到终端；它用于观察“写出完整机器可读报告”进度，也给日志留下可搜索证据。
    print(f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
# 【L2237】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L2238】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L2239】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L2240】开始执行可能抛错的“捕获异常、关闭 Isaac Sim、返回退出码”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
try:
# 【L2241】得到 `exit_code`，它在本项目中表示本功能块中的 `exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `main()`；`main` 表示本功能块中的 `main` 值。
    exit_code = main()
# 【L2242】捕获 `BaseException`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
except BaseException:
# 【L2243】把 `"PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True` 的当前值/文字输出到终端；它用于观察“捕获异常、关闭 Isaac Sim、返回退出码”进度，也给日志留下可搜索证据。
    print("PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True)
# 【L2244】对 `traceback` 调用 `print_exc()`：调用 `traceback` 提供的 `print_exc` 操作。本行产生的修改/返回值服务于“捕获异常、关闭 Isaac Sim、返回退出码”。
    traceback.print_exc()
# 【L2245】声明/传入参数 `raise`；在本项目中它表示本功能块中的 `raise` 值。
    raise
# 【L2246】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
finally:
# 【L2247】对 `simulation_app` 调用 `close(skip_cleanup=True)`：关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。本行产生的修改/返回值服务于“捕获异常、关闭 Isaac Sim、返回退出码”。
    simulation_app.close(skip_cleanup=True)
# 【L2248】空行：分隔“捕获异常、关闭 Isaac Sim、返回退出码”中的逻辑段，让结构更容易看清。

# 【L2249】主动抛出 `SystemExit(exit_code)` 并停止当前路径；说明当前输入违反“捕获异常、关闭 Isaac Sim、返回退出码”要求，不能继续进入仿真、训练或评测。
raise SystemExit(exit_code)
```
