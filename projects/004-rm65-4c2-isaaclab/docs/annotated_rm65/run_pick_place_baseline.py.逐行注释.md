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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab."""
# 【L0003】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 itertools：项目或第三方模块；后面的代码会调用其中的类或函数。
import itertools
# 【L0008】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0009】导入 sys：项目或第三方模块；后面的代码会调用其中的类或函数。
import sys
# 【L0010】导入 traceback：项目或第三方模块；后面的代码会调用其中的类或函数。
import traceback
# 【L0011】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0012】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0013】调用 `Path`：创建路径对象。本行位于“启动说明、项目路径与 AppLauncher”。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0014】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if str(PROJECT_ROOT) not in sys.path:
# 【L0015】执行“启动说明、项目路径与 AppLauncher”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0016】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0017】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.app import AppLauncher
# 【L0018】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0020】计算并保存变量 `parser`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
parser = argparse.ArgumentParser(description=__doc__)
# 【L0021】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--usd", type=Path, required=True)
# 【L0022】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--urdf", type=Path, required=True)
# 【L0023】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--description", type=Path, required=True)
# 【L0024】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--output", type=Path, required=True)
# 【L0025】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--transfer-joint-1-rad", type=float, default=0.8)
# 【L0026】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0027】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--robot-base-z-m",
# 【L0028】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0029】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0030】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="World height of the robot mounting plane; Lula targets remain in the robot base frame.",
# 【L0031】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0032】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--arm-effort-limit-sim", type=float, default=300.0)
# 【L0033】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--arm-stiffness", type=float, default=1000.0)
# 【L0034】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--arm-damping", type=float, default=100.0)
# 【L0035】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--gripper-effort-limit-sim", type=float, default=20.0)
# 【L0036】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--gripper-stiffness", type=float, default=120.0)
# 【L0037】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--gripper-damping", type=float, default=12.0)
# 【L0038】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--gripper-close-target-rad", type=float, default=0.65)
# 【L0039】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--pregrasp-distance-m", type=float, default=0.10)
# 【L0040】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--grasp-world-offset-x-m", type=float, default=0.0)
# 【L0041】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--grasp-world-offset-z-m", type=float, default=0.0)
# 【L0042】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0043】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--source-offset-x-m",
# 【L0044】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0045】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0046】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world x for demonstration diversity.",
# 【L0047】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0048】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0049】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--source-offset-y-m",
# 【L0050】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0051】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0052】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world y for demonstration diversity.",
# 【L0053】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0054】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0055】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--grasp-orientation-mode",
# 【L0056】计算并保存变量 `choices`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("reference", "top_down"),
# 【L0057】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="reference",
# 【L0058】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0059】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--top-down-yaw-rad", type=float, default=0.0)
# 【L0060】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0061】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--top-down-tilt-rad",
# 【L0062】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0063】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0064】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal.",
# 【L0065】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0066】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0067】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--top-down-ik-multistart",
# 【L0068】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0069】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1,
# 【L0070】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Number of deterministic joint-space seeds used to solve the top-down pose.",
# 【L0071】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0072】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0073】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--top-down-blend",
# 【L0074】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0075】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1.0,
# 【L0076】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Interpolate from the calibrated side grasp (0) to the requested above-table pose (1).",
# 【L0077】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0078】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0079】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--lift-mode",
# 【L0080】计算并保存变量 `choices`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("joint_reference", "cartesian_vertical"),
# 【L0081】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="joint_reference",
# 【L0082】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use the historical fixed joint target or solve a local vertical lift from the current grasp pose.",
# 【L0083】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0084】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--cartesian-lift-height-m", type=float, default=0.04)
# 【L0085】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--release-clearance-m", type=float, default=0.08)
# 【L0086】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--release-separation-assist-m", type=float, default=0.05)
# 【L0087】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--place-descent", action="store_true")
# 【L0088】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--place-descent-distance-m", type=float, default=0.10)
# 【L0089】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0090】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--place-waypoint-steps",
# 【L0091】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0092】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=60,
# 【L0093】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Simulation steps used for each approximately 1 cm place-descent segment.",
# 【L0094】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0095】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0096】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--target-support-mode",
# 【L0097】计算并保存变量 `choices`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("wide_platform", "rotated_strip"),
# 【L0098】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="wide_platform",
# 【L0099】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0100】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0101】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--target-collision-enable-stage",
# 【L0102】计算并保存变量 `choices`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("after_transfer", "after_place_descent"),
# 【L0103】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="after_transfer",
# 【L0104】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0105】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--diagnose-approach-only", action="store_true")
# 【L0106】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--diagnose-kinematics-only", action="store_true")
# 【L0107】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--collision-bypass-during-approach", action="store_true")
# 【L0108】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--initialize-at-grasp", action="store_true")
# 【L0109】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--disable-arm-gravity-during-approach", action="store_true")
# 【L0110】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0111】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--disable-arm-gravity-through-transport",
# 【L0112】计算并保存变量 `action`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0113】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep arm-link gravity disabled after approach to isolate object grasp/transport physics.",
# 【L0114】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0115】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--natural-source-gravity", action="store_true")
# 【L0116】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0117】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--enable-moving-gripper-gravity",
# 【L0118】计算并保存变量 `action`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0119】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep gravity enabled on all six moving 4C2 finger links.",
# 【L0120】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0121】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0122】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--unassisted-release",
# 【L0123】计算并保存变量 `action`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0124】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="After opening the gripper, let gravity place the block without pose or velocity injection.",
# 【L0125】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0126】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0127】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--record-episode-dir",
# 【L0128】调用 `Path`：创建路径对象。本行位于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=Path,
# 【L0129】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Write a synchronized scripted-expert episode to this directory.",
# 【L0130】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0131】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0132】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--record-stride-steps",
# 【L0133】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0134】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=12,
# 【L0135】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics).",
# 【L0136】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0137】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0138】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--episode-prompt",
# 【L0139】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="pick up the block and place it on the target",
# 【L0140】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Language instruction stored with the expert episode.",
# 【L0141】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0142】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0143】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--record-images",
# 【L0144】计算并保存变量 `action`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0145】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras.",
# 【L0146】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0147】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0148】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--pi05-closed-loop",
# 【L0149】计算并保存变量 `action`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0150】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert.",
# 【L0151】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0152】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--policy-host", default="127.0.0.1")
# 【L0153】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--policy-port", type=int, default=8000)
# 【L0154】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--policy-max-action-chunks", type=int, default=80)
# 【L0155】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument("--policy-execute-actions-per-chunk", type=int, default=5)
# 【L0156】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0157】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--policy-gripper-open-threshold",
# 【L0158】计算并保存变量 `type`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0159】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.12,
# 【L0160】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help=(
# 【L0161】执行“命令行参数；它们是实验可重复性的外部控制面板”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "Normalized 4C2 target/feedback threshold used to verify a model-selected "
# 【L0162】执行“命令行参数；它们是实验可重复性的外部控制面板”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "release. Values below the threshold are open; calibrate this in simulation."
# 【L0163】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0164】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0165】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
parser.add_argument(
# 【L0166】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“命令行参数；它们是实验可重复性的外部控制面板”。
    "--policy-checkpoint-id",
# 【L0167】计算并保存变量 `default`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    default="unknown",
# 【L0168】计算并保存变量 `help`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Checkpoint identifier stored in the machine-readable evaluation report.",
# 【L0169】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0170】把 IsaacLab 通用参数（如 --headless、--device、--enable_cameras）加入解析器。
AppLauncher.add_app_launcher_args(parser)
# 【L0171】计算并保存变量 `args`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
args = parser.parse_args()
# 【L0172】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if not 0.0 < args.policy_gripper_open_threshold < 1.0:
# 【L0173】执行“命令行参数；它们是实验可重复性的外部控制面板”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    parser.error("--policy-gripper-open-threshold must be between 0 and 1")
# 【L0174】计算并保存变量 `app_launcher`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
app_launcher = AppLauncher(args)
# 【L0175】计算并保存变量 `simulation_app`；该值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
simulation_app = app_launcher.app
# 【L0176】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0177】导入 numpy：NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后面的代码会调用其中的类或函数。
import numpy as np  # noqa: E402
# 【L0178】导入 torch：PyTorch 张量库；IsaacLab 的 GPU 状态和命令使用 Torch 张量；后面的代码会调用其中的类或函数。
import torch  # noqa: E402
# 【L0179】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
import isaaclab.sim as sim_utils  # noqa: E402
# 【L0180】导入 isaacsim：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
# 【L0181】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0182】执行“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
enable_extension("isaacsim.robot_motion.motion_generation")
# 【L0183】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0184】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
# 【L0185】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
# 【L0186】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.sensors import ContactSensor, ContactSensorCfg  # noqa: E402
# 【L0187】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
# 【L0188】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.expert_episode import (  # noqa: E402
# 【L0189】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
    EpisodeRecorder,
# 【L0190】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
    normalize_gripper,
# 【L0191】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
    validate_episode,
# 【L0192】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0193】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
from openpi_extension.action_guard import guard_action_chunk  # noqa: E402
# 【L0194】导入 grasp_geometry：项目或第三方模块；后面的代码会调用其中的类或函数。
from grasp_geometry import compute_top_down_link_pose  # noqa: E402
# 【L0195】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.sim import SimulationContext  # noqa: E402
# 【L0196】导入 isaaclab：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaaclab.utils import math as math_utils  # noqa: E402
# 【L0197】导入 isaacsim：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
# 【L0198】导入 isaacsim：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
# 【L0199】导入 isaacsim：项目或第三方模块；后面的代码会调用其中的类或函数。
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver  # noqa: E402
# 【L0200】导入 pxr：项目或第三方模块；后面的代码会调用其中的类或函数。
from pxr import PhysxSchema, UsdPhysics  # noqa: E402
# 【L0201】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0202】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0203】计算并保存变量 `ARM_JOINTS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
# 【L0204】计算并保存变量 `ARM_BODY_PATHS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
ARM_BODY_PATHS = {f"/World/Robot/link_{index}" for index in range(1, 7)}
# 【L0205】计算并保存变量 `MOVING_GRIPPER_BODY_PATHS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
MOVING_GRIPPER_BODY_PATHS = {
# 【L0206】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_r_1",
# 【L0207】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_l_1",
# 【L0208】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_r_2",
# 【L0209】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_l_2",
# 【L0210】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_r_3",
# 【L0211】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
    "/World/Robot/tool_l_3",
# 【L0212】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0213】计算并保存变量 `BLOCK_SIZE`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
BLOCK_SIZE = (0.060, 0.040, 0.025)
# 【L0214】计算并保存变量 `BLOCK_MASS_KG`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
BLOCK_MASS_KG = 0.030
# 【L0215】调用 `np.array`：创建 NumPy 数组。本行位于“RM65 关节、物体尺寸、接触点和关节限位常量”。
SOURCE_BLOCK_POSITION = np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)
# 【L0216】计算并保存变量 `SOURCE_BLOCK_QUATERNION_WXYZ`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
SOURCE_BLOCK_QUATERNION_WXYZ = (-0.20872162, -0.00000211, 0.97797507, 0.00002437)
# 【L0217】计算并保存变量 `TARGET_PLATFORM_SIZE`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
TARGET_PLATFORM_SIZE = (0.200, 0.200, 0.040)
# 【L0218】计算并保存变量 `TARGET_PLATFORM_TOP_Z`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
TARGET_PLATFORM_TOP_Z = 0.650
# 【L0219】计算并保存变量 `SOURCE_PLATFORM_SIZE`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
SOURCE_PLATFORM_SIZE = (0.120, 0.018, 0.020)
# 【L0220】计算并保存变量 `TARGET_STRIP_SIZE`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
TARGET_STRIP_SIZE = (0.070, 0.018, 0.020)
# 【L0221】计算并保存变量 `SOURCE_PLATFORM_TOP_Z`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
SOURCE_PLATFORM_TOP_Z = 0.7330
# 【L0222】计算并保存变量 `RELEASE_DOWNWARD_SPEED_M_S`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
RELEASE_DOWNWARD_SPEED_M_S = 0.10
# 【L0223】计算并保存变量 `RELEASE_SEPARATION_ASSIST_M`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
RELEASE_SEPARATION_ASSIST_M = 0.05
# 【L0224】计算并保存变量 `TIP_LOCAL_POINTS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
TIP_LOCAL_POINTS = {
# 【L0225】定义字典/JSON 字段 `tool_r_2`；它把“RM65 关节、物体尺寸、接触点和关节限位常量”中的结果用稳定键名记录下来。
    "tool_r_2": (0.04368, -0.00645, 0.01250),
# 【L0226】定义字典/JSON 字段 `tool_l_2`；它把“RM65 关节、物体尺寸、接触点和关节限位常量”中的结果用稳定键名记录下来。
    "tool_l_2": (0.04368, 0.00645, 0.01257),
# 【L0227】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0228】计算并保存变量 `PAD_LOCAL_CENTERS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
PAD_LOCAL_CENTERS = {
# 【L0229】定义字典/JSON 字段 `tool_r_2`；它把“RM65 关节、物体尺寸、接触点和关节限位常量”中的结果用稳定键名记录下来。
    "tool_r_2": (0.028775714, -0.011597111, -0.073257379),
# 【L0230】定义字典/JSON 字段 `tool_l_2`；它把“RM65 关节、物体尺寸、接触点和关节限位常量”中的结果用稳定键名记录下来。
    "tool_l_2": (0.027286683, 0.013343694, -0.072958842),
# 【L0231】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0232】计算并保存变量 `CONTACT_SENSORS`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
CONTACT_SENSORS: dict[str, ContactSensor] = {}
# 【L0233】计算并保存变量 `GRIPPER_MASTER_JOINT`；该值服务于“RM65 关节、物体尺寸、接触点和关节限位常量”。
GRIPPER_MASTER_JOINT = "tool_gripper_joint"
# 【L0234】调用 `np.array`：创建 NumPy 数组。本行位于“RM65 关节、物体尺寸、接触点和关节限位常量”。
RM65_JOINT_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
# 【L0235】调用 `np.array`：创建 NumPy 数组。本行位于“RM65 关节、物体尺寸、接触点和关节限位常量”。
RM65_JOINT_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])
# 【L0236】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0237】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0238】定义函数 rotate_about_z；其职责属于“旋转、四元数和旋转距离的数学工具”，缩进块是函数体。
def rotate_about_z(position: np.ndarray, angle: float) -> np.ndarray:
# 【L0239】执行“旋转、四元数和旋转距离的数学工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cosine, sine = np.cos(angle), np.sin(angle)
# 【L0240】结束当前函数并把结果交给调用者；这里完成“旋转、四元数和旋转距离的数学工具”的输出。
    return np.array(
# 【L0241】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
        [cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],
# 【L0242】计算并保存变量 `dtype`；该值服务于“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0243】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0244】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0245】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0246】定义函数 quaternion_multiply_wxyz；其职责属于“旋转、四元数和旋转距离的数学工具”，缩进块是函数体。
def quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray) -> np.ndarray:
# 【L0247】执行“旋转、四元数和旋转距离的数学工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    lw, lx, ly, lz = left
# 【L0248】执行“旋转、四元数和旋转距离的数学工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    rw, rx, ry, rz = right
# 【L0249】结束当前函数并把结果交给调用者；这里完成“旋转、四元数和旋转距离的数学工具”的输出。
    return np.array(
# 【L0250】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0251】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“旋转、四元数和旋转距离的数学工具”。
            lw * rw - lx * rx - ly * ry - lz * rz,
# 【L0252】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“旋转、四元数和旋转距离的数学工具”。
            lw * rx + lx * rw + ly * rz - lz * ry,
# 【L0253】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“旋转、四元数和旋转距离的数学工具”。
            lw * ry - lx * rz + ly * rw + lz * rx,
# 【L0254】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“旋转、四元数和旋转距离的数学工具”。
            lw * rz + lx * ry - ly * rx + lz * rw,
# 【L0255】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0256】计算并保存变量 `dtype`；该值服务于“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0257】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0258】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0259】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0260】定义函数 quaternion_to_matrix_wxyz；其职责属于“旋转、四元数和旋转距离的数学工具”，缩进块是函数体。
def quaternion_to_matrix_wxyz(quaternion: np.ndarray) -> np.ndarray:
# 【L0261】执行“旋转、四元数和旋转距离的数学工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    w, x, y, z = quaternion
# 【L0262】结束当前函数并把结果交给调用者；这里完成“旋转、四元数和旋转距离的数学工具”的输出。
    return np.array(
# 【L0263】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0264】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
# 【L0265】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
# 【L0266】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
# 【L0267】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0268】计算并保存变量 `dtype`；该值服务于“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0269】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0270】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0271】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0272】定义函数 rotation_distance_rad；其职责属于“旋转、四元数和旋转距离的数学工具”，缩进块是函数体。
def rotation_distance_rad(left: np.ndarray, right: np.ndarray) -> float:
# 【L0273】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Return the geodesic angle between two 3x3 rotation matrices."""
# 【L0274】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0275】计算并保存变量 `cosine`；该值服务于“旋转、四元数和旋转距离的数学工具”。
    cosine = 0.5 * (np.trace(left.T @ right) - 1.0)
# 【L0276】结束当前函数并把结果交给调用者；这里完成“旋转、四元数和旋转距离的数学工具”的输出。
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))
# 【L0277】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0278】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0279】定义函数 closest_equivalent_rm65_solution；其职责属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”，缩进块是函数体。
def closest_equivalent_rm65_solution(
# 【L0280】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    lula: LulaKinematicsSolver,
# 【L0281】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    solution: np.ndarray,
# 【L0282】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    reference: np.ndarray,
# 【L0283】开始一个缩进代码块或键值结构；该块负责“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> np.ndarray:
# 【L0284】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Choose an FK-equivalent RM65 wrist branch nearest to ``reference``.
# 【L0285】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0286】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    Lula may return a spherical-wrist equivalent such as
# 【L0287】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ``(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating
# 【L0288】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    directly between those representations can command a multi-radian jump
# 【L0289】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    even though the Cartesian poses are adjacent.  Enumerate only known
# 【L0290】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    equivalent representations, verify each with FK, and keep the one with
# 【L0291】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    the smallest joint-space jump.
# 【L0292】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0293】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0294】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    solution = np.asarray(solution, dtype=np.float64)
# 【L0295】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    reference = np.asarray(reference, dtype=np.float64)
# 【L0296】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    target_position, target_rotation = lula.compute_forward_kinematics("link_6", solution)
# 【L0297】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0298】计算并保存变量 `bases`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    bases = [solution.copy()]
# 【L0299】计算并保存变量 `wrist_flip`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    wrist_flip = solution.copy()
# 【L0300】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    wrist_flip[3] += np.pi
# 【L0301】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    wrist_flip[4] *= -1.0
# 【L0302】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    wrist_flip[5] += np.pi
# 【L0303】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    bases.append(wrist_flip)
# 【L0304】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0305】计算并保存变量 `valid`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    valid: list[tuple[float, float, np.ndarray]] = []
# 【L0306】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for base in bases:
# 【L0307】计算并保存变量 `joint_values`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        joint_values = []
# 【L0308】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for index, value in enumerate(base):
# 【L0309】计算并保存变量 `equivalents`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            equivalents = [
# 【L0310】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                value + turns * 2.0 * np.pi
# 【L0311】for 循环：依次处理序列中的每个元素/时间步/episode/case。
                for turns in (-1, 0, 1)
# 【L0312】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if RM65_JOINT_LOWER_RAD[index] - 1e-9
# 【L0313】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                <= value + turns * 2.0 * np.pi
# 【L0314】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                <= RM65_JOINT_UPPER_RAD[index] + 1e-9
# 【L0315】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            ]
# 【L0316】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            joint_values.append(equivalents)
# 【L0317】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for values in itertools.product(*joint_values):
# 【L0318】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            candidate = np.asarray(values, dtype=np.float64)
# 【L0319】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            position, rotation = lula.compute_forward_kinematics("link_6", candidate)
# 【L0320】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if np.linalg.norm(position - target_position) > 1e-5:
# 【L0321】跳过本次循环剩余语句，继续处理下一个候选项。
                continue
# 【L0322】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if rotation_distance_rad(rotation, target_rotation) > 1e-5:
# 【L0323】跳过本次循环剩余语句，继续处理下一个候选项。
                continue
# 【L0324】计算并保存变量 `delta`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            delta = np.abs(candidate - reference)
# 【L0325】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            valid.append((float(np.max(delta)), float(np.linalg.norm(delta)), candidate))
# 【L0326】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0327】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not valid:
# 【L0328】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError("No FK-equivalent RM65 joint representation passed validation")
# 【L0329】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    _, _, selected = min(valid, key=lambda item: (item[0], item[1]))
# 【L0330】结束当前函数并把结果交给调用者；这里完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”的输出。
    return selected.copy()
# 【L0331】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0332】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0333】定义函数 require_continuous_joint_step；其职责属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”，缩进块是函数体。
def require_continuous_joint_step(
# 【L0334】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    start: np.ndarray,
# 【L0335】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    target: np.ndarray,
# 【L0336】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0337】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    label: str,
# 【L0338】计算并保存变量 `max_step_rad`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    max_step_rad: float = 0.75,
# 【L0339】开始一个缩进代码块或键值结构；该块负责“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> None:
# 【L0340】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    max_step = float(np.max(np.abs(np.asarray(target) - np.asarray(start))))
# 【L0341】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if max_step > max_step_rad:
# 【L0342】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0343】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"
# 【L0344】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        )
# 【L0345】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0346】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0347】定义函数 solve_continuous_cartesian_path；其职责属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”，缩进块是函数体。
def solve_continuous_cartesian_path(
# 【L0348】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    lula: LulaKinematicsSolver,
# 【L0349】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    target_positions: list[np.ndarray],
# 【L0350】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    target_orientation: np.ndarray,
# 【L0351】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    numerical_seed: np.ndarray,
# 【L0352】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    command_reference: np.ndarray,
# 【L0353】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0354】计算并保存变量 `max_step_rad`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    max_step_rad: float = 0.75,
# 【L0355】开始一个缩进代码块或键值结构；该块负责“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> tuple[np.ndarray, list[np.ndarray], float] | None:
# 【L0356】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Solve a path while keeping Lula's seed and the commanded branch separate."""
# 【L0357】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    raw_seed = np.asarray(numerical_seed, dtype=np.float64).copy()
# 【L0358】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    command = np.asarray(command_reference, dtype=np.float64).copy()
# 【L0359】计算并保存变量 `commands`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    commands: list[np.ndarray] = []
# 【L0360】计算并保存变量 `path_max_step`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    path_max_step = 0.0
# 【L0361】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for target_position in target_positions:
# 【L0362】计算并保存变量 `seeds`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        seeds = [raw_seed]
# 【L0363】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0):
# 【L0364】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            seeds.append(command)
# 【L0365】计算并保存变量 `candidates`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        candidates: list[tuple[float, np.ndarray, np.ndarray]] = []
# 【L0366】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for seed in seeds:
# 【L0367】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            raw_solution, success = lula.compute_inverse_kinematics(
# 【L0368】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                "link_6",
# 【L0369】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                target_position,
# 【L0370】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                target_orientation,
# 【L0371】计算并保存变量 `warm_start`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                warm_start=seed,
# 【L0372】计算并保存变量 `position_tolerance`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                position_tolerance=1e-4,
# 【L0373】计算并保存变量 `orientation_tolerance`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                orientation_tolerance=1e-3,
# 【L0374】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0375】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if not success:
# 【L0376】跳过本次循环剩余语句，继续处理下一个候选项。
                continue
# 【L0377】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            raw_solution = np.asarray(raw_solution, dtype=np.float64)
# 【L0378】计算并保存变量 `command_solution`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            command_solution = closest_equivalent_rm65_solution(
# 【L0379】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                lula, raw_solution, command
# 【L0380】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0381】计算并保存变量 `step_rad`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            step_rad = float(np.max(np.abs(command_solution - command)))
# 【L0382】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            candidates.append((step_rad, raw_solution, command_solution))
# 【L0383】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not candidates:
# 【L0384】结束当前函数并把结果交给调用者；这里完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”的输出。
            return None
# 【L0385】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        step_rad, raw_seed, command = min(candidates, key=lambda item: item[0])
# 【L0386】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if step_rad > max_step_rad:
# 【L0387】结束当前函数并把结果交给调用者；这里完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”的输出。
            return None
# 【L0388】计算并保存变量 `path_max_step`；该值服务于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        path_max_step = max(path_max_step, step_rad)
# 【L0389】执行“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        commands.append(command.copy())
# 【L0390】结束当前函数并把结果交给调用者；这里完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”的输出。
    return raw_seed.copy(), commands, path_max_step
# 【L0391】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0392】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0393】定义函数 tip_world_position；其职责属于“把 link 局部点转换到世界坐标”，缩进块是函数体。
def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0394】计算并保存变量 `body_id`；该值服务于“把 link 局部点转换到世界坐标”。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0395】计算并保存变量 `local`；该值服务于“把 link 局部点转换到世界坐标”。
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
# 【L0396】结束当前函数并把结果交给调用者；这里完成“把 link 局部点转换到世界坐标”的输出。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0397】执行“把 link 局部点转换到世界坐标”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0398】执行“把 link 局部点转换到世界坐标”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    )[0]
# 【L0399】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0400】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0401】定义函数 body_world_position；其职责属于“把 link 局部点转换到世界坐标”，缩进块是函数体。
def body_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0402】计算并保存变量 `body_id`；该值服务于“把 link 局部点转换到世界坐标”。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0403】结束当前函数并把结果交给调用者；这里完成“把 link 局部点转换到世界坐标”的输出。
    return robot.data.body_pos_w[0, body_id]
# 【L0404】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0405】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0406】定义函数 local_point_world_position；其职责属于“把 link 局部点转换到世界坐标”，缩进块是函数体。
def local_point_world_position(
# 【L0407】执行“把 link 局部点转换到世界坐标”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    robot: Articulation, body_name: str, local_position: tuple[float, float, float]
# 【L0408】开始一个缩进代码块或键值结构；该块负责“把 link 局部点转换到世界坐标”。
) -> torch.Tensor:
# 【L0409】计算并保存变量 `body_id`；该值服务于“把 link 局部点转换到世界坐标”。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0410】计算并保存变量 `local`；该值服务于“把 link 局部点转换到世界坐标”。
    local = torch.tensor(local_position, device=robot.device).unsqueeze(0)
# 【L0411】结束当前函数并把结果交给调用者；这里完成“把 link 局部点转换到世界坐标”的输出。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0412】执行“把 link 局部点转换到世界坐标”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0413】执行“把 link 局部点转换到世界坐标”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    )[0]
# 【L0414】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0415】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0416】定义类 ExpertEpisodeCapture；把相关配置、状态和方法组织成一个可复用对象。
class ExpertEpisodeCapture:
# 【L0417】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Sample observations and the action targets applied on the next physics step."""
# 【L0418】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0419】定义函数 __init__；其职责属于“从仿真同步采样状态、动作、外部/腕部相机图像”，缩进块是函数体。
    def __init__(
# 【L0420】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self,
# 【L0421】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        recorder: EpisodeRecorder,
# 【L0422】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        arm_ids: list[int],
# 【L0423】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        gripper_master_id: int,
# 【L0424】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        stride_steps: int,
# 【L0425】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        physics_dt: float,
# 【L0426】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        sim: SimulationContext,
# 【L0427】计算并保存变量 `external_camera`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        external_camera: Camera | None = None,
# 【L0428】计算并保存变量 `wrist_camera`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        wrist_camera: Camera | None = None,
# 【L0429】计算并保存变量 `wrist_tool_body_id`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        wrist_tool_body_id: int | None = None,
# 【L0430】开始一个缩进代码块或键值结构；该块负责“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0431】保存实例字段 `recorder`，让同一对象的其他方法继续使用这个值。
        self.recorder = recorder
# 【L0432】保存实例字段 `arm_ids`，让同一对象的其他方法继续使用这个值。
        self.arm_ids = arm_ids
# 【L0433】保存实例字段 `gripper_master_id`，让同一对象的其他方法继续使用这个值。
        self.gripper_master_id = gripper_master_id
# 【L0434】保存实例字段 `stride_steps`，让同一对象的其他方法继续使用这个值。
        self.stride_steps = stride_steps
# 【L0435】保存实例字段 `physics_dt`，让同一对象的其他方法继续使用这个值。
        self.physics_dt = physics_dt
# 【L0436】给变量 `sim` 赋值：IsaacLab SimulationContext，负责物理时间步。
        self.sim = sim
# 【L0437】保存实例字段 `external_camera`，让同一对象的其他方法继续使用这个值。
        self.external_camera = external_camera
# 【L0438】保存实例字段 `wrist_camera`，让同一对象的其他方法继续使用这个值。
        self.wrist_camera = wrist_camera
# 【L0439】保存实例字段 `wrist_tool_body_id`，让同一对象的其他方法继续使用这个值。
        self.wrist_tool_body_id = wrist_tool_body_id
# 【L0440】保存实例字段 `wrist_local_offset`，让同一对象的其他方法继续使用这个值。
        self.wrist_local_offset: torch.Tensor | None = None
# 【L0441】保存实例字段 `wrist_local_forward`，让同一对象的其他方法继续使用这个值。
        self.wrist_local_forward: torch.Tensor | None = None
# 【L0442】保存实例字段 `sim_step`，让同一对象的其他方法继续使用这个值。
        self.sim_step = 0
# 【L0443】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0444】静态方法装饰器：这个函数不依赖某个实例的 self 状态。
    @staticmethod
# 【L0445】定义函数 _rgb；其职责属于“从仿真同步采样状态、动作、外部/腕部相机图像”，缩进块是函数体。
    def _rgb(camera: Camera) -> np.ndarray:
# 【L0446】计算并保存变量 `image`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        image = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
# 【L0447】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if image.dtype != np.uint8:
# 【L0448】调用 `np.clip`：把数值限制在给定上下界内。本行位于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            image = np.clip(image, 0, 255).astype(np.uint8)
# 【L0449】结束当前函数并把结果交给调用者；这里完成“从仿真同步采样状态、动作、外部/腕部相机图像”的输出。
        return image
# 【L0450】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0451】静态方法装饰器：这个函数不依赖某个实例的 self 状态。
    @staticmethod
# 【L0452】定义函数 _image_ready；其职责属于“从仿真同步采样状态、动作、外部/腕部相机图像”，缩进块是函数体。
    def _image_ready(image: np.ndarray) -> bool:
# 【L0453】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
        """Return whether an Isaac camera produced a usable RGB frame."""
# 【L0454】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0455】结束当前函数并把结果交给调用者；这里完成“从仿真同步采样状态、动作、外部/腕部相机图像”的输出。
        return (
# 【L0456】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            image.ndim == 3
# 【L0457】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and image.shape[0] > 0
# 【L0458】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and image.shape[1] > 0
# 【L0459】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and image.shape[2] == 3
# 【L0460】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0461】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0462】定义函数 _render_images；其职责属于“从仿真同步采样状态、动作、外部/腕部相机图像”，缩进块是函数体。
    def _render_images(self, robot: Articulation, cube: RigidObject) -> tuple[np.ndarray, np.ndarray]:
# 【L0463】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self.external_camera is None or self.wrist_camera is None:
# 【L0464】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("both cameras are required for image recording")
# 【L0465】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self.wrist_tool_body_id is None:
# 【L0466】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("wrist tool body id is required for image recording")
# 【L0467】计算并保存变量 `tool_position`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        tool_position = robot.data.body_pos_w[0, self.wrist_tool_body_id]
# 【L0468】计算并保存变量 `tool_quaternion`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        tool_quaternion = robot.data.body_quat_w[0, self.wrist_tool_body_id]
# 【L0469】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self.wrist_local_offset is None:
# 【L0470】计算并保存变量 `world_offset`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            world_offset = torch.tensor([0.0, 0.15, 0.10], device=robot.device)
# 【L0471】计算并保存变量 `eye`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            eye = tool_position + world_offset
# 【L0472】计算并保存变量 `world_forward`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            world_forward = torch.nn.functional.normalize(cube.data.root_pos_w[0] - eye, dim=0)
# 【L0473】计算并保存变量 `inverse_tool_quaternion`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            inverse_tool_quaternion = math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]
# 【L0474】保存实例字段 `wrist_local_offset`，让同一对象的其他方法继续使用这个值。
            self.wrist_local_offset = math_utils.quat_apply(
# 【L0475】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                inverse_tool_quaternion.unsqueeze(0), world_offset.unsqueeze(0)
# 【L0476】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            )[0]
# 【L0477】保存实例字段 `wrist_local_forward`，让同一对象的其他方法继续使用这个值。
            self.wrist_local_forward = math_utils.quat_apply(
# 【L0478】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                inverse_tool_quaternion.unsqueeze(0), world_forward.unsqueeze(0)
# 【L0479】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            )[0]
# 【L0480】内部一致性断言：运行到这里时该对象必须已经存在，否则说明程序逻辑有误。
        assert self.wrist_local_forward is not None
# 【L0481】计算并保存变量 `eye`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        eye = tool_position + math_utils.quat_apply(
# 【L0482】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            tool_quaternion.unsqueeze(0), self.wrist_local_offset.unsqueeze(0)
# 【L0483】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        )[0]
# 【L0484】计算并保存变量 `forward`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        forward = math_utils.quat_apply(
# 【L0485】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            tool_quaternion.unsqueeze(0), self.wrist_local_forward.unsqueeze(0)
# 【L0486】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        )[0]
# 【L0487】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self.wrist_camera.set_world_poses_from_view(
# 【L0488】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            eye.unsqueeze(0), (eye + forward).unsqueeze(0)
# 【L0489】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0490】源码注释：Isaac Sim can expose an empty RGB tensor during the first few render
        # Isaac Sim can expose an empty RGB tensor during the first few render
# 【L0491】源码注释：ticks after a headless camera starts.  Wait for real sensor frames
        # ticks after a headless camera starts.  Wait for real sensor frames
# 【L0492】源码注释：instead of recording a fabricated image or aborting the episode.
        # instead of recording a fabricated image or aborting the episode.
# 【L0493】计算并保存变量 `last_shapes`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        last_shapes: tuple[tuple[int, ...], tuple[int, ...]] | None = None
# 【L0494】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for _ in range(30):
# 【L0495】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            self.sim.render()
# 【L0496】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            self.external_camera.update(self.physics_dt)
# 【L0497】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            self.wrist_camera.update(self.physics_dt)
# 【L0498】给变量 `external_rgb` 赋值：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
            external_rgb = self._rgb(self.external_camera)
# 【L0499】给变量 `wrist_rgb` 赋值：随末端移动的腕部相机 RGB 图像。
            wrist_rgb = self._rgb(self.wrist_camera)
# 【L0500】计算并保存变量 `last_shapes`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            last_shapes = (external_rgb.shape, wrist_rgb.shape)
# 【L0501】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if self._image_ready(external_rgb) and self._image_ready(wrist_rgb):
# 【L0502】结束当前函数并把结果交给调用者；这里完成“从仿真同步采样状态、动作、外部/腕部相机图像”的输出。
                return external_rgb, wrist_rgb
# 【L0503】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0504】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "Isaac cameras did not produce usable RGB frames after 30 render ticks; "
# 【L0505】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            f"last shapes were {last_shapes}"
# 【L0506】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0507】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0508】定义函数 before_step；其职责属于“从仿真同步采样状态、动作、外部/腕部相机图像”，缩进块是函数体。
    def before_step(
# 【L0509】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self,
# 【L0510】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        robot: Articulation,
# 【L0511】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        cube: RigidObject,
# 【L0512】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        target_state: torch.Tensor,
# 【L0513】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        phase: str,
# 【L0514】开始一个缩进代码块或键值结构；该块负责“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0515】源码注释：The simulator data buffers are stale immediately after the initial
        # The simulator data buffers are stale immediately after the initial
# 【L0516】源码注释：direct state write, so the first valid sample is taken after one
        # direct state write, so the first valid sample is taken after one
# 【L0517】源码注释：complete stride of physics updates.
        # complete stride of physics updates.
# 【L0518】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if self.sim_step > 0 and self.sim_step % self.stride_steps == 0:
# 【L0519】计算并保存变量 `observed_arm`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            observed_arm = robot.data.joint_pos[0, self.arm_ids].detach().cpu().numpy()
# 【L0520】计算并保存变量 `observed_gripper`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            observed_gripper = normalize_gripper(
# 【L0521】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                float(robot.data.joint_pos[0, self.gripper_master_id].item())
# 【L0522】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0523】计算并保存变量 `target_arm`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            target_arm = target_state[0, self.arm_ids].detach().cpu().numpy()
# 【L0524】计算并保存变量 `target_gripper`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            target_gripper = normalize_gripper(
# 【L0525】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                float(target_state[0, self.gripper_master_id].item())
# 【L0526】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0527】调用 `np.concatenate`：沿一个轴首尾拼接数组。本行位于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            action = np.concatenate([target_arm, [target_gripper]])
# 【L0528】计算并保存变量 `cube_pose`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            cube_pose = torch.cat(
# 【L0529】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                [cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0
# 【L0530】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            ).detach().cpu().numpy()
# 【L0531】给变量 `external_rgb` 赋值：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
            external_rgb = None
# 【L0532】给变量 `wrist_rgb` 赋值：随末端移动的腕部相机 RGB 图像。
            wrist_rgb = None
# 【L0533】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if self.external_camera is not None:
# 【L0534】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                external_rgb, wrist_rgb = self._render_images(robot, cube)
# 【L0535】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            self.recorder.add_frame(
# 【L0536】计算并保存变量 `timestamp_s`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                timestamp_s=self.sim_step * self.physics_dt,
# 【L0537】计算并保存变量 `sim_step`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                sim_step=self.sim_step,
# 【L0538】计算并保存变量 `phase`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                phase=phase,
# 【L0539】计算并保存变量 `joint_position_rad`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                joint_position_rad=observed_arm,
# 【L0540】计算并保存变量 `gripper_position`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                gripper_position=observed_gripper,
# 【L0541】计算并保存变量 `action`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                action=action,
# 【L0542】计算并保存变量 `cube_pose_wxyz`；该值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                cube_pose_wxyz=cube_pose,
# 【L0543】给变量 `external_rgb` 赋值：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
                external_rgb=external_rgb,
# 【L0544】给变量 `wrist_rgb` 赋值：随末端移动的腕部相机 RGB 图像。
                wrist_rgb=wrist_rgb,
# 【L0545】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0546】执行“从仿真同步采样状态、动作、外部/腕部相机图像”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        self.sim_step += 1
# 【L0547】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0548】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0549】定义函数 smooth_move；其职责属于“平滑移动和保持姿态的物理步进器”，缩进块是函数体。
def smooth_move(
# 【L0550】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    sim: SimulationContext,
# 【L0551】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    robot: Articulation,
# 【L0552】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    cube: RigidObject,
# 【L0553】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    state: torch.Tensor,
# 【L0554】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    joint_ids: list[int],
# 【L0555】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    start: np.ndarray,
# 【L0556】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    target: np.ndarray,
# 【L0557】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    steps: int,
# 【L0558】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    phase: str,
# 【L0559】计算并保存变量 `capture`；该值服务于“平滑移动和保持姿态的物理步进器”。
    capture: ExpertEpisodeCapture | None = None,
# 【L0560】开始一个缩进代码块或键值结构；该块负责“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0561】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(f"PICK_PLACE_STAGE={phase}_START", flush=True)
# 【L0562】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for step in range(steps):
# 【L0563】计算并保存变量 `progress`；该值服务于“平滑移动和保持姿态的物理步进器”。
        progress = (step + 1) / steps
# 【L0564】计算并保存变量 `smooth`；该值服务于“平滑移动和保持姿态的物理步进器”。
        smooth = 3.0 * progress**2 - 2.0 * progress**3
# 【L0565】计算并保存变量 `command`；该值服务于“平滑移动和保持姿态的物理步进器”。
        command = start + smooth * (target - start)
# 【L0566】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“平滑移动和保持姿态的物理步进器”。
        state[:, joint_ids] = torch.as_tensor(command, device=sim.device, dtype=state.dtype)
# 【L0567】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.set_joint_position_target(state)
# 【L0568】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if capture is not None:
# 【L0569】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            capture.before_step(robot, cube, state, phase)
# 【L0570】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.write_data_to_sim()
# 【L0571】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        cube.write_data_to_sim()
# 【L0572】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步。本行位于“平滑移动和保持姿态的物理步进器”。
        sim.step(render=False)
# 【L0573】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.update(sim.get_physics_dt())
# 【L0574】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区。本行位于“平滑移动和保持姿态的物理步进器”。
        cube.update(sim.get_physics_dt())
# 【L0575】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0576】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            contact_sensor.update(sim.get_physics_dt())
# 【L0577】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(f"PICK_PLACE_STAGE={phase}_DONE", flush=True)
# 【L0578】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0579】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0580】定义函数 hold；其职责属于“平滑移动和保持姿态的物理步进器”，缩进块是函数体。
def hold(
# 【L0581】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    sim: SimulationContext,
# 【L0582】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    robot: Articulation,
# 【L0583】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    cube: RigidObject,
# 【L0584】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    state: torch.Tensor,
# 【L0585】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    steps: int,
# 【L0586】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“平滑移动和保持姿态的物理步进器”。
    phase: str,
# 【L0587】计算并保存变量 `capture`；该值服务于“平滑移动和保持姿态的物理步进器”。
    capture: ExpertEpisodeCapture | None = None,
# 【L0588】开始一个缩进代码块或键值结构；该块负责“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0589】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for _ in range(steps):
# 【L0590】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.set_joint_position_target(state)
# 【L0591】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if capture is not None:
# 【L0592】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            capture.before_step(robot, cube, state, phase)
# 【L0593】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.write_data_to_sim()
# 【L0594】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        cube.write_data_to_sim()
# 【L0595】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步。本行位于“平滑移动和保持姿态的物理步进器”。
        sim.step(render=False)
# 【L0596】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区。本行位于“平滑移动和保持姿态的物理步进器”。
        robot.update(sim.get_physics_dt())
# 【L0597】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区。本行位于“平滑移动和保持姿态的物理步进器”。
        cube.update(sim.get_physics_dt())
# 【L0598】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0599】执行“平滑移动和保持姿态的物理步进器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            contact_sensor.update(sim.get_physics_dt())
# 【L0600】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0601】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0602】定义函数 run_pi05_closed_loop；其职责属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，缩进块是函数体。
def run_pi05_closed_loop(
# 【L0603】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    sim: SimulationContext,
# 【L0604】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    robot: Articulation,
# 【L0605】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    cube: RigidObject,
# 【L0606】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    state: torch.Tensor,
# 【L0607】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    arm_ids: list[int],
# 【L0608】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    gripper_ids: list[int],
# 【L0609】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    gripper_master_id: int,
# 【L0610】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    target_block_position: np.ndarray,
# 【L0611】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    settled_source_position: torch.Tensor,
# 【L0612】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    target_platform_collision_apis: list,
# 【L0613】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    episode_capture: ExpertEpisodeCapture,
# 【L0614】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    episode_recorder: EpisodeRecorder,
# 【L0615】调用 `Path`：创建路径对象。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    output: Path,
# 【L0616】开始一个缩进代码块或键值结构；该块负责“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
) -> int:
# 【L0617】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Run receding-horizon π0.5 control and write task-level evidence."""
# 【L0618】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0619】导入 time：计时和短暂等待；后面的代码会调用其中的类或函数。
    import time
# 【L0620】导入 websockets：项目或第三方模块；后面的代码会调用其中的类或函数。
    import websockets.sync.client as ws
# 【L0621】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0622】导入 openpi_extension：项目或第三方模块；后面的代码会调用其中的类或函数。
    from openpi_extension.websocket_compat import call_connect_without_keepalive
# 【L0623】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0624】计算并保存变量 `original_connect`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    original_connect = ws.connect
# 【L0625】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0626】定义函数 connect_without_keepalive；其职责属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，缩进块是函数体。
    def connect_without_keepalive(*connect_args, **connect_kwargs):
# 【L0627】结束当前函数并把结果交给调用者；这里完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”的输出。
        return call_connect_without_keepalive(
# 【L0628】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            original_connect, *connect_args, **connect_kwargs
# 【L0629】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        )
# 【L0630】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0631】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ws.connect = connect_without_keepalive
# 【L0632】导入 openpi_client：项目或第三方模块；后面的代码会调用其中的类或函数。
    from openpi_client.websocket_client_policy import WebsocketClientPolicy
# 【L0633】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0634】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for collision_api in target_platform_collision_apis:
# 【L0635】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L0636】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print("PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L0637】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0638】计算并保存变量 `client`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    client = WebsocketClientPolicy(args.policy_host, args.policy_port)
# 【L0639】计算并保存变量 `inference_latencies`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    inference_latencies = []
# 【L0640】计算并保存变量 `total_joint_limit_clamps`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    total_joint_limit_clamps = 0
# 【L0641】计算并保存变量 `total_joint_step_clamps`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    total_joint_step_clamps = 0
# 【L0642】计算并保存变量 `total_gripper_clamps`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    total_gripper_clamps = 0
# 【L0643】计算并保存变量 `action_chunks`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    action_chunks = 0
# 【L0644】计算并保存变量 `executed_actions`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    executed_actions = 0
# 【L0645】计算并保存变量 `max_cube_z`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    max_cube_z = float(cube.data.root_pos_w[0, 2].item())
# 【L0646】计算并保存变量 `consecutive_candidate_chunks`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    consecutive_candidate_chunks = 0
# 【L0647】计算并保存变量 `last_executed_gripper_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    last_executed_gripper_target = None
# 【L0648】计算并保存变量 `release_postcondition_applied`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    release_postcondition_applied = False
# 【L0649】计算并保存变量 `release_postcondition_arm_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    release_postcondition_arm_target = None
# 【L0650】计算并保存变量 `minimum_observed_gripper_normalized`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    minimum_observed_gripper_normalized = float("inf")
# 【L0651】计算并保存变量 `minimum_executed_gripper_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    minimum_executed_gripper_target = float("inf")
# 【L0652】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
    try:
# 【L0653】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for chunk_index in range(args.policy_max_action_chunks):
# 【L0654】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            external_rgb, wrist_rgb = episode_capture._render_images(robot, cube)
# 【L0655】给变量 `current_arm` 赋值：当前六个 RM65 关节角，单位 rad。
            current_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy().astype(np.float32)
# 【L0656】调用 `np.array`：创建 NumPy 数组。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            current_gripper = np.array(
# 【L0657】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                [normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],
# 【L0658】计算并保存变量 `dtype`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                dtype=np.float32,
# 【L0659】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0660】给变量 `observation` 赋值：本次发给 π0.5 的图像、状态和文字指令字典。
            observation = {
# 【L0661】定义字典/JSON 字段 `observation/joint_position`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                "observation/joint_position": current_arm,
# 【L0662】定义字典/JSON 字段 `observation/gripper_position`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                "observation/gripper_position": current_gripper,
# 【L0663】定义字典/JSON 字段 `observation/external_image`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                "observation/external_image": external_rgb,
# 【L0664】定义字典/JSON 字段 `observation/wrist_image`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                "observation/wrist_image": wrist_rgb,
# 【L0665】定义字典/JSON 字段 `prompt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                "prompt": args.episode_prompt,
# 【L0666】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0667】计算并保存变量 `started`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            started = time.perf_counter()
# 【L0668】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            raw_actions = np.asarray(client.infer(observation)["actions"], dtype=np.float32)
# 【L0669】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            inference_latencies.append(time.perf_counter() - started)
# 【L0670】调用 `guard_action_chunk`：验证并裁剪策略动作，阻止越界和过大跳变。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            safe_actions, guard = guard_action_chunk(raw_actions, current_arm)
# 【L0671】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            total_joint_limit_clamps += guard["joint_limit_clamp_count"]
# 【L0672】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            total_joint_step_clamps += guard["joint_step_clamp_count"]
# 【L0673】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            total_gripper_clamps += guard["gripper_clamp_count"]
# 【L0674】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            action_chunks += 1
# 【L0675】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0676】计算并保存变量 `execute_count`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            execute_count = min(args.policy_execute_actions_per_chunk, len(safe_actions))
# 【L0677】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for action_index, action in enumerate(safe_actions[:execute_count]):
# 【L0678】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                state[:, arm_ids] = torch.as_tensor(
# 【L0679】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    action[:6], device=sim.device, dtype=state.dtype
# 【L0680】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0681】计算并保存变量 `gripper_target_rad`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                gripper_target_rad = float(action[6]) * 0.865
# 【L0682】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                state[:, gripper_ids] = gripper_target_rad
# 【L0683】计算并保存变量 `last_executed_gripper_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                last_executed_gripper_target = float(action[6])
# 【L0684】计算并保存变量 `minimum_executed_gripper_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                minimum_executed_gripper_target = min(
# 【L0685】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    minimum_executed_gripper_target, last_executed_gripper_target
# 【L0686】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0687】for 循环：依次处理序列中的每个元素/时间步/episode/case。
                for _ in range(args.record_stride_steps):
# 【L0688】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    robot.set_joint_position_target(state)
# 【L0689】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    episode_capture.before_step(
# 【L0690】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        robot,
# 【L0691】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        cube,
# 【L0692】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        state,
# 【L0693】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}",
# 【L0694】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    )
# 【L0695】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    robot.write_data_to_sim()
# 【L0696】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    cube.write_data_to_sim()
# 【L0697】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    sim.step(render=False)
# 【L0698】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    robot.update(sim.get_physics_dt())
# 【L0699】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    cube.update(sim.get_physics_dt())
# 【L0700】for 循环：依次处理序列中的每个元素/时间步/episode/case。
                    for contact_sensor in CONTACT_SENSORS.values():
# 【L0701】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                        contact_sensor.update(sim.get_physics_dt())
# 【L0702】计算并保存变量 `max_cube_z`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    max_cube_z = max(max_cube_z, float(cube.data.root_pos_w[0, 2].item()))
# 【L0703】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                executed_actions += 1
# 【L0704】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0705】计算并保存变量 `current_cube`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            current_cube = cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L0706】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            target_error = float(np.linalg.norm(current_cube - target_block_position))
# 【L0707】计算并保存变量 `actual_gripper_normalized`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            actual_gripper_normalized = normalize_gripper(
# 【L0708】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0709】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0710】计算并保存变量 `minimum_observed_gripper_normalized`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            minimum_observed_gripper_normalized = min(
# 【L0711】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                minimum_observed_gripper_normalized, actual_gripper_normalized
# 【L0712】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0713】计算并保存变量 `gripper_open`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            gripper_open = (
# 【L0714】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                actual_gripper_normalized < args.policy_gripper_open_threshold
# 【L0715】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0716】计算并保存变量 `gripper_command_open`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            gripper_command_open = (
# 【L0717】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                last_executed_gripper_target is not None
# 【L0718】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                and last_executed_gripper_target < args.policy_gripper_open_threshold
# 【L0719】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0720】计算并保存变量 `lifted`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            lifted = max_cube_z - float(settled_source_position[2].item()) > 0.02
# 【L0721】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if lifted and target_error < 0.05 and gripper_open and gripper_command_open:
# 【L0722】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                consecutive_candidate_chunks += 1
# 【L0723】否则分支：前面的 if/elif 都不成立时执行。
            else:
# 【L0724】计算并保存变量 `consecutive_candidate_chunks`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                consecutive_candidate_chunks = 0
# 【L0725】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
            print(
# 【L0726】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "PI05_CHUNK="
# 【L0727】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                + json.dumps(
# 【L0728】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    {
# 【L0729】定义字典/JSON 字段 `index`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "index": chunk_index,
# 【L0730】定义字典/JSON 字段 `latency_s`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "latency_s": inference_latencies[-1],
# 【L0731】定义字典/JSON 字段 `target_error_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "target_error_m": target_error,
# 【L0732】定义字典/JSON 字段 `lifted`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "lifted": lifted,
# 【L0733】定义字典/JSON 字段 `gripper_open`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "gripper_open": gripper_open,
# 【L0734】定义字典/JSON 字段 `gripper_command_open`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "gripper_command_open": gripper_command_open,
# 【L0735】定义字典/JSON 字段 `actual_gripper_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "actual_gripper_normalized": actual_gripper_normalized,
# 【L0736】定义字典/JSON 字段 `last_executed_gripper_target`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "last_executed_gripper_target": last_executed_gripper_target,
# 【L0737】定义字典/JSON 字段 `guard`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
                        "guard": guard,
# 【L0738】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    }
# 【L0739】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                ),
# 【L0740】计算并保存变量 `flush`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                flush=True,
# 【L0741】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0742】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if consecutive_candidate_chunks >= 3:
# 【L0743】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                print("PI05_STAGE=SUCCESS_CANDIDATE", flush=True)
# 【L0744】计算并保存变量 `release_postcondition_arm_target`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                release_postcondition_arm_target = (
# 【L0745】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    robot.data.joint_pos[0, arm_ids].detach().cpu().tolist()
# 【L0746】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0747】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                state[:, arm_ids] = robot.data.joint_pos[:, arm_ids].detach()
# 【L0748】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                state[:, gripper_ids] = 0.0
# 【L0749】计算并保存变量 `release_postcondition_applied`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                release_postcondition_applied = True
# 【L0750】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                print("PI05_STAGE=RELEASE_POSTCONDITION_LATCHED", flush=True)
# 【L0751】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
                break
# 【L0752】清理块：无论前面成功还是抛错都执行，常用于关闭服务和 Isaac Sim。
    finally:
# 【L0753】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        client._ws.close()
# 【L0754】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0755】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)
# 【L0756】计算并保存变量 `settle_a`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    settle_a = cube.data.root_pos_w[0].clone()
# 【L0757】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)
# 【L0758】计算并保存变量 `final_position`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    final_position = cube.data.root_pos_w[0].clone()
# 【L0759】计算并保存变量 `source_np`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    source_np = settled_source_position.detach().cpu().numpy()
# 【L0760】计算并保存变量 `final_np`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    final_np = final_position.detach().cpu().numpy()
# 【L0761】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L0762】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L0763】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    source_to_target_distance = float(np.linalg.norm(final_np[:2] - source_np[:2]))
# 【L0764】计算并保存变量 `lift_height`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    lift_height = max_cube_z - float(source_np[2])
# 【L0765】计算并保存变量 `post_release_drift`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    post_release_drift = float(torch.linalg.vector_norm(final_position - settle_a).item())
# 【L0766】计算并保存变量 `final_gripper`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    final_gripper = normalize_gripper(
# 【L0767】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0768】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0769】计算并保存变量 `all_states_finite`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    all_states_finite = bool(
# 【L0770】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        torch.isfinite(robot.data.joint_pos).all()
# 【L0771】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and torch.isfinite(cube.data.root_state_w).all()
# 【L0772】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0773】计算并保存变量 `passed`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    passed = bool(
# 【L0774】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        action_chunks > 0
# 【L0775】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and source_to_target_distance > 0.12
# 【L0776】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and lift_height > 0.02
# 【L0777】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and final_target_xy_error < 0.05
# 【L0778】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and final_target_position_error < 0.05
# 【L0779】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and post_release_drift < 0.02
# 【L0780】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and release_postcondition_applied
# 【L0781】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and all_states_finite
# 【L0782】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0783】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0784】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    episode_recorder.metadata["task_success"] = passed
# 【L0785】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    episode_recorder.metadata["pi05_used"] = True
# 【L0786】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    episode_recorder.metadata["training_ready"] = False
# 【L0787】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    episode_recorder.metadata["evaluation_only"] = True
# 【L0788】给变量 `manifest` 赋值：描述磁盘数据含义、数量和路径的元数据清单。
    manifest = episode_recorder.save()
# 【L0789】计算并保存变量 `validation`；该值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    validation = validate_episode(episode_recorder.output_dir, require_images=True)
# 【L0790】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if validation["status"] != "pass":
# 【L0791】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")
# 【L0792】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0793】定义字典/JSON 字段 `status`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "status": "pass" if passed else "fail",
# 【L0794】定义字典/JSON 字段 `simulation_only`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L0795】定义字典/JSON 字段 `pi05_used`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "pi05_used": True,
# 【L0796】定义字典/JSON 字段 `expert`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "expert": None,
# 【L0797】定义字典/JSON 字段 `real_robot_command_sent`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L0798】定义字典/JSON 字段 `policy_checkpoint_id`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "policy_checkpoint_id": args.policy_checkpoint_id,
# 【L0799】定义字典/JSON 字段 `prompt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "prompt": args.episode_prompt,
# 【L0800】定义字典/JSON 字段 `action_chunks`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "action_chunks": action_chunks,
# 【L0801】定义字典/JSON 字段 `executed_actions`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "executed_actions": executed_actions,
# 【L0802】定义字典/JSON 字段 `policy_action_horizon`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "policy_action_horizon": int(len(raw_actions)) if action_chunks else None,
# 【L0803】定义字典/JSON 字段 `controller_config`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "controller_config": {
# 【L0804】定义字典/JSON 字段 `policy_max_action_chunks`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "policy_max_action_chunks": args.policy_max_action_chunks,
# 【L0805】定义字典/JSON 字段 `policy_execute_actions_per_chunk`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "policy_execute_actions_per_chunk": args.policy_execute_actions_per_chunk,
# 【L0806】定义字典/JSON 字段 `record_stride_steps`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "record_stride_steps": args.record_stride_steps,
# 【L0807】定义字典/JSON 字段 `physics_dt_s`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "physics_dt_s": sim.get_physics_dt(),
# 【L0808】定义字典/JSON 字段 `executed_action_hold_seconds`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "executed_action_hold_seconds": (
# 【L0809】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                args.record_stride_steps * sim.get_physics_dt()
# 【L0810】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0811】定义字典/JSON 字段 `success_candidate_required_consecutive_chunks`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "success_candidate_required_consecutive_chunks": 3,
# 【L0812】定义字典/JSON 字段 `policy_gripper_open_threshold`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "policy_gripper_open_threshold": args.policy_gripper_open_threshold,
# 【L0813】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0814】定义字典/JSON 字段 `inference_latency_s`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "inference_latency_s": {
# 【L0815】定义字典/JSON 字段 `first`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "first": inference_latencies[0] if inference_latencies else None,
# 【L0816】定义字典/JSON 字段 `mean`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "mean": float(np.mean(inference_latencies)) if inference_latencies else None,
# 【L0817】定义字典/JSON 字段 `maximum`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "maximum": float(np.max(inference_latencies)) if inference_latencies else None,
# 【L0818】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0819】定义字典/JSON 字段 `guard_totals`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "guard_totals": {
# 【L0820】定义字典/JSON 字段 `joint_limit_clamp_count`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "joint_limit_clamp_count": total_joint_limit_clamps,
# 【L0821】定义字典/JSON 字段 `joint_step_clamp_count`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "joint_step_clamp_count": total_joint_step_clamps,
# 【L0822】定义字典/JSON 字段 `gripper_clamp_count`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "gripper_clamp_count": total_gripper_clamps,
# 【L0823】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0824】定义字典/JSON 字段 `low_level_release_postcondition`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "low_level_release_postcondition": {
# 【L0825】定义字典/JSON 字段 `applied`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "applied": release_postcondition_applied,
# 【L0826】定义字典/JSON 字段 `trigger`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "trigger": (
# 【L0827】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "three consecutive chunks with lift, target error below 0.05 m, "
# 【L0828】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "actual gripper and executed gripper target below the calibrated threshold"
# 【L0829】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0830】定义字典/JSON 字段 `open_threshold_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L0831】定义字典/JSON 字段 `arm_target_latched_to_actual_rad`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "arm_target_latched_to_actual_rad": release_postcondition_arm_target,
# 【L0832】定义字典/JSON 字段 `gripper_target_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "gripper_target_normalized": 0.0 if release_postcondition_applied else None,
# 【L0833】定义字典/JSON 字段 `verification_settle_steps`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "verification_settle_steps": 240,
# 【L0834】定义字典/JSON 字段 `model_selected_release`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "model_selected_release": release_postcondition_applied,
# 【L0835】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0836】定义字典/JSON 字段 `release_verification`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "release_verification": {
# 【L0837】定义字典/JSON 字段 `verified`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "verified": release_postcondition_applied,
# 【L0838】定义字典/JSON 字段 `required_consecutive_chunks`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "required_consecutive_chunks": 3,
# 【L0839】定义字典/JSON 字段 `open_threshold_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L0840】定义字典/JSON 字段 `minimum_observed_gripper_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "minimum_observed_gripper_normalized": (
# 【L0841】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                minimum_observed_gripper_normalized
# 【L0842】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if np.isfinite(minimum_observed_gripper_normalized)
# 【L0843】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                else None
# 【L0844】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0845】定义字典/JSON 字段 `minimum_executed_gripper_target`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "minimum_executed_gripper_target": (
# 【L0846】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                minimum_executed_gripper_target
# 【L0847】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if np.isfinite(minimum_executed_gripper_target)
# 【L0848】执行“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                else None
# 【L0849】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L0850】定义字典/JSON 字段 `final_gripper_normalized_is_diagnostic_only`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "final_gripper_normalized_is_diagnostic_only": True,
# 【L0851】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0852】定义字典/JSON 字段 `source_position_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "source_position_m": source_np.tolist(),
# 【L0853】定义字典/JSON 字段 `target_position_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "target_position_m": target_block_position.tolist(),
# 【L0854】定义字典/JSON 字段 `final_position_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "final_position_m": final_np.tolist(),
# 【L0855】定义字典/JSON 字段 `source_to_target_xy_distance_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L0856】定义字典/JSON 字段 `block_lift_height_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "block_lift_height_m": lift_height,
# 【L0857】定义字典/JSON 字段 `final_target_xy_error_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "final_target_xy_error_m": final_target_xy_error,
# 【L0858】定义字典/JSON 字段 `final_target_position_error_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "final_target_position_error_m": final_target_position_error,
# 【L0859】定义字典/JSON 字段 `post_release_drift_m`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "post_release_drift_m": post_release_drift,
# 【L0860】定义字典/JSON 字段 `final_gripper_normalized`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "final_gripper_normalized": final_gripper,
# 【L0861】定义字典/JSON 字段 `all_states_finite`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "all_states_finite": all_states_finite,
# 【L0862】定义字典/JSON 字段 `criteria`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "criteria": {
# 【L0863】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L0864】定义字典/JSON 字段 `block_lift_height_m_gt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "block_lift_height_m_gt": 0.02,
# 【L0865】定义字典/JSON 字段 `final_target_xy_error_m_lt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "final_target_xy_error_m_lt": 0.05,
# 【L0866】定义字典/JSON 字段 `final_target_position_error_m_lt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "final_target_position_error_m_lt": 0.05,
# 【L0867】定义字典/JSON 字段 `post_release_drift_m_lt`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "post_release_drift_m_lt": 0.02,
# 【L0868】定义字典/JSON 字段 `model_selected_release_verified`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "model_selected_release_verified": True,
# 【L0869】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0870】定义字典/JSON 字段 `episode`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
        "episode": {
# 【L0871】定义字典/JSON 字段 `directory`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "directory": str(episode_recorder.output_dir),
# 【L0872】定义字典/JSON 字段 `frame_count`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "frame_count": manifest["frame_count"],
# 【L0873】定义字典/JSON 字段 `validation`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "validation": validation,
# 【L0874】定义字典/JSON 字段 `evaluation_only`；它把“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的结果用稳定键名记录下来。
            "evaluation_only": True,
# 【L0875】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L0876】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    }
# 【L0877】调用 `mkdir`：创建目录。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L0878】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L0879】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(report, indent=2), flush=True)
# 【L0880】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}", flush=True)
# 【L0881】结束当前函数并把结果交给调用者；这里完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”的输出。
    return 0 if passed else 1
# 【L0882】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0883】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0884】定义函数 contact_force_statistics；其职责属于“接触力统计与平台生成工具”，缩进块是函数体。
def contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60) -> dict[str, float]:
# 【L0885】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Return peak, current, and recent sustained cube-contact force magnitudes."""
# 【L0886】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0887】计算并保存变量 `current`；该值服务于“接触力统计与平台生成工具”。
    current = contact_sensor.data.force_matrix_w
# 【L0888】计算并保存变量 `history`；该值服务于“接触力统计与平台生成工具”。
    history = contact_sensor.data.force_matrix_w_history
# 【L0889】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if current is None or history is None:
# 【L0890】结束当前函数并把结果交给调用者；这里完成“接触力统计与平台生成工具”的输出。
        return {"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}
# 【L0891】计算并保存变量 `current_n`；该值服务于“接触力统计与平台生成工具”。
    current_n = float(torch.linalg.vector_norm(current, dim=-1).max())
# 【L0892】计算并保存变量 `history_norm`；该值服务于“接触力统计与平台生成工具”。
    history_norm = torch.linalg.vector_norm(history, dim=-1)
# 【L0893】计算并保存变量 `peak_n`；该值服务于“接触力统计与平台生成工具”。
    peak_n = float(history_norm.max())
# 【L0894】计算并保存变量 `recent`；该值服务于“接触力统计与平台生成工具”。
    recent = history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(
# 【L0895】执行“接触力统计与平台生成工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        min(recent_steps, history_norm.shape[1]), -1
# 【L0896】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L0897】计算并保存变量 `recent_mean_n`；该值服务于“接触力统计与平台生成工具”。
    recent_mean_n = float(recent.max(dim=1).values.mean())
# 【L0898】结束当前函数并把结果交给调用者；这里完成“接触力统计与平台生成工具”的输出。
    return {"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}
# 【L0899】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0900】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L0901】定义函数 spawn_platform；其职责属于“接触力统计与平台生成工具”，缩进块是函数体。
def spawn_platform(
# 【L0902】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“接触力统计与平台生成工具”。
    path: str,
# 【L0903】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“接触力统计与平台生成工具”。
    position: np.ndarray,
# 【L0904】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“接触力统计与平台生成工具”。
    size: tuple[float, float, float],
# 【L0905】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“接触力统计与平台生成工具”。
    color: tuple[float, float, float],
# 【L0906】计算并保存变量 `orientation`；该值服务于“接触力统计与平台生成工具”。
    orientation: tuple[float, float, float, float] | None = None,
# 【L0907】开始一个缩进代码块或键值结构；该块负责“接触力统计与平台生成工具”。
) -> None:
# 【L0908】计算并保存变量 `cfg`；该值服务于“接触力统计与平台生成工具”。
    cfg = sim_utils.CuboidCfg(
# 【L0909】计算并保存变量 `size`；该值服务于“接触力统计与平台生成工具”。
        size=size,
# 【L0910】计算并保存变量 `collision_props`；该值服务于“接触力统计与平台生成工具”。
        collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L0911】计算并保存变量 `visual_material`；该值服务于“接触力统计与平台生成工具”。
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
# 【L0912】计算并保存变量 `physics_material`；该值服务于“接触力统计与平台生成工具”。
        physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L0913】计算并保存变量 `static_friction`；该值服务于“接触力统计与平台生成工具”。
            static_friction=1.0,
# 【L0914】计算并保存变量 `dynamic_friction`；该值服务于“接触力统计与平台生成工具”。
            dynamic_friction=0.8,
# 【L0915】计算并保存变量 `restitution`；该值服务于“接触力统计与平台生成工具”。
            restitution=0.0,
# 【L0916】计算并保存变量 `friction_combine_mode`；该值服务于“接触力统计与平台生成工具”。
            friction_combine_mode="max",
# 【L0917】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
        ),
# 【L0918】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L0919】计算并保存变量 `kwargs`；该值服务于“接触力统计与平台生成工具”。
    kwargs = {"translation": tuple(position)}
# 【L0920】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if orientation is not None:
# 【L0921】执行“接触力统计与平台生成工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        kwargs["orientation"] = orientation
# 【L0922】执行“接触力统计与平台生成工具”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cfg.func(path, cfg, **kwargs)
# 【L0923】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0924】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0925】定义函数 main；其职责属于“主函数输入文件和参数范围校验”，缩进块是函数体。
def main() -> int:
# 【L0926】计算并保存变量 `usd`；该值服务于“主函数输入文件和参数范围校验”。
    usd = args.usd.expanduser().resolve()
# 【L0927】计算并保存变量 `urdf`；该值服务于“主函数输入文件和参数范围校验”。
    urdf = args.urdf.expanduser().resolve()
# 【L0928】计算并保存变量 `description`；该值服务于“主函数输入文件和参数范围校验”。
    description = args.description.expanduser().resolve()
# 【L0929】给变量 `output` 赋值：输出文件路径。
    output = args.output.expanduser().resolve()
# 【L0930】计算并保存变量 `missing`；该值服务于“主函数输入文件和参数范围校验”。
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
# 【L0931】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if missing:
# 【L0932】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise FileNotFoundError(f"missing required files: {missing}")
# 【L0933】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2:
# 【L0934】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")
# 【L0935】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 <= args.robot_base_z_m <= 0.8:
# 【L0936】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--robot-base-z-m must be between 0 and 0.8")
# 【L0937】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0:
# 【L0938】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("arm actuator effort, stiffness, and damping must be positive")
# 【L0939】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0:
# 【L0940】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("gripper actuator effort, stiffness, and damping must be positive")
# 【L0941】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.1 <= args.gripper_close_target_rad <= 1.0:
# 【L0942】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")
# 【L0943】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.01 <= args.pregrasp_distance_m <= 0.10:
# 【L0944】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")
# 【L0945】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(args.grasp_world_offset_x_m) > 0.08:
# 【L0946】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")
# 【L0947】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(args.grasp_world_offset_z_m) > 0.08:
# 【L0948】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")
# 【L0949】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04:
# 【L0950】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("source x/y offsets must each be between -0.04 and 0.04 m")
# 【L0951】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if abs(args.top_down_yaw_rad) > np.pi:
# 【L0952】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--top-down-yaw-rad must be between -pi and pi")
# 【L0953】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0):
# 【L0954】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")
# 【L0955】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 1 <= args.top_down_ik_multistart <= 512:
# 【L0956】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--top-down-ik-multistart must be between 1 and 512")
# 【L0957】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 <= args.top_down_blend <= 1.0:
# 【L0958】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--top-down-blend must be between 0 and 1")
# 【L0959】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.02 <= args.cartesian_lift_height_m <= 0.15:
# 【L0960】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")
# 【L0961】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.03 <= args.release_clearance_m <= 0.20:
# 【L0962】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--release-clearance-m must be between 0.03 and 0.20")
# 【L0963】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.0 <= args.release_separation_assist_m <= 0.20:
# 【L0964】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--release-separation-assist-m must be between 0.0 and 0.20")
# 【L0965】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 0.03 <= args.place_descent_distance_m <= 0.13:
# 【L0966】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--place-descent-distance-m must be between 0.03 and 0.13")
# 【L0967】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 30 <= args.place_waypoint_steps <= 240:
# 【L0968】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--place-waypoint-steps must be between 30 and 240")
# 【L0969】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not 1 <= args.record_stride_steps <= 240:
# 【L0970】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--record-stride-steps must be between 1 and 240")
# 【L0971】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.episode_prompt.strip():
# 【L0972】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--episode-prompt must not be empty")
# 【L0973】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.record_episode_dir is not None and (
# 【L0974】执行“主函数输入文件和参数范围校验”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        args.diagnose_approach_only or args.diagnose_kinematics_only
# 【L0975】开始一个缩进代码块或键值结构；该块负责“主函数输入文件和参数范围校验”。
    ):
# 【L0976】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("episode recording is available only for a complete pick-and-place run")
# 【L0977】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.record_images and args.record_episode_dir is None:
# 【L0978】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--record-images requires --record-episode-dir")
# 【L0979】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.record_images and not getattr(args, "enable_cameras", False):
# 【L0980】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--record-images requires the AppLauncher flag --enable_cameras")
# 【L0981】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None):
# 【L0982】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")
# 【L0983】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only):
# 【L0984】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")
# 【L0985】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1:
# 【L0986】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("policy chunk counts must be positive")
# 【L0987】空行：分隔“主函数输入文件和参数范围校验”中的逻辑段，让结构更容易看清。

# 【L0988】计算并保存变量 `requested_pregrasp_distance_m`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    requested_pregrasp_distance_m = args.pregrasp_distance_m
# 【L0989】计算并保存变量 `effective_pregrasp_distance_m`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    effective_pregrasp_distance_m = requested_pregrasp_distance_m
# 【L0990】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    grasp_arm = np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L0991】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    lift_arm = np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L0992】计算并保存变量 `source_block_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    source_block_position = SOURCE_BLOCK_POSITION.copy()
# 【L0993】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    source_block_quaternion = np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L0994】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.natural_source_gravity:
# 【L0995】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        source_block_position[2] = SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L0996】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        source_block_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
# 【L0997】计算并保存变量 `nominal_source_block_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    nominal_source_block_position = source_block_position.copy()
# 【L0998】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    source_block_position[:2] += np.array(
# 【L0999】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [args.source_offset_x_m, args.source_offset_y_m], dtype=np.float64
# 【L1000】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1001】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    robot_base_position = np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)
# 【L1002】计算并保存变量 `source_block_position_base`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    source_block_position_base = source_block_position - robot_base_position
# 【L1003】给变量 `lula` 赋值：NVIDIA Lula 运动学求解器实例。
    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
# 【L1004】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1005】计算并保存变量 `grasp_ik_numerical_seed`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    grasp_ik_numerical_seed = grasp_arm.copy()
# 【L1006】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0:
# 【L1007】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        offset_target_position = grasp_link_position + np.array(
# 【L1008】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64
# 【L1009】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1010】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        offset_grasp_arm, success = lula.compute_inverse_kinematics(
# 【L1011】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            "link_6",
# 【L1012】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            offset_target_position,
# 【L1013】计算并保存变量 `target_orientation`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1014】计算并保存变量 `warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1015】计算并保存变量 `position_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1016】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1017】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not success:
# 【L1018】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the requested grasp world offset")
# 【L1019】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        grasp_ik_numerical_seed = np.asarray(offset_grasp_arm, dtype=np.float64)
# 【L1020】计算并保存变量 `grasp_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        grasp_arm = closest_equivalent_rm65_solution(
# 【L1021】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            lula, grasp_ik_numerical_seed, grasp_arm
# 【L1022】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1023】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1024】计算并保存变量 `reference_block_from_link_local`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    reference_block_from_link_local = grasp_link_rotation.T @ (
# 【L1025】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        nominal_source_block_position - grasp_link_position
# 【L1026】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1027】计算并保存变量 `top_down_ik_seed_index`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    top_down_ik_seed_index = None
# 【L1028】计算并保存变量 `precomputed_retreat_waypoints`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    precomputed_retreat_waypoints: list[np.ndarray] | None = None
# 【L1029】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.grasp_orientation_mode == "top_down":
# 【L1030】计算并保存变量 `calibrated_reference_link_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        calibrated_reference_link_position = (
# 【L1031】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            source_block_position_base
# 【L1032】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            - grasp_link_rotation @ reference_block_from_link_local
# 【L1033】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1034】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        top_down_link_position, top_down_rotation, reference_block_from_link_local = (
# 【L1035】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            compute_top_down_link_pose(
# 【L1036】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                calibrated_reference_link_position,
# 【L1037】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                grasp_link_rotation,
# 【L1038】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                source_block_position_base,
# 【L1039】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_yaw_rad,
# 【L1040】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_tilt_rad,
# 【L1041】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_blend,
# 【L1042】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1043】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1044】计算并保存变量 `ik_seeds`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ik_seeds = [grasp_ik_numerical_seed]
# 【L1045】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.top_down_ik_multistart > 1:
# 【L1046】计算并保存变量 `rng`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            rng = np.random.default_rng(20260916)
# 【L1047】计算并保存变量 `random_seeds`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            random_seeds = rng.uniform(
# 【L1048】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                RM65_JOINT_LOWER_RAD,
# 【L1049】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                RM65_JOINT_UPPER_RAD,
# 【L1050】计算并保存变量 `size`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                size=(args.top_down_ik_multistart - 1, len(ARM_JOINTS)),
# 【L1051】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1052】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            ik_seeds.extend(random_seeds)
# 【L1053】计算并保存变量 `top_down_solution`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        top_down_solution = None
# 【L1054】计算并保存变量 `success`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        success = False
# 【L1055】计算并保存变量 `top_down_quaternion`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        top_down_quaternion = rot_matrix_to_quat(top_down_rotation)
# 【L1056】计算并保存变量 `minimum_pregrasp_distance_m`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        minimum_pregrasp_distance_m = min(requested_pregrasp_distance_m, 0.05)
# 【L1057】计算并保存变量 `fallback_count`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        fallback_count = int(
# 【L1058】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            np.floor(
# 【L1059】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                (requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01
# 【L1060】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                + 1e-9
# 【L1061】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1062】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1063】计算并保存变量 `pregrasp_distance_candidates`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        pregrasp_distance_candidates = [
# 【L1064】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            requested_pregrasp_distance_m - 0.01 * index
# 【L1065】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for index in range(fallback_count + 1)
# 【L1066】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ]
# 【L1067】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for candidate_pregrasp_distance_m in pregrasp_distance_candidates:
# 【L1068】计算并保存变量 `retreat_distances_for_selection`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            retreat_distances_for_selection = np.linspace(
# 【L1069】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                0.01,
# 【L1070】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                candidate_pregrasp_distance_m,
# 【L1071】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                max(1, int(round(candidate_pregrasp_distance_m / 0.01))),
# 【L1072】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1073】计算并保存变量 `retreat_targets_for_selection`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            retreat_targets_for_selection = [
# 【L1074】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                top_down_link_position
# 【L1075】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                + np.array([0.0, 0.0, distance], dtype=np.float64)
# 【L1076】for 循环：依次处理序列中的每个元素/时间步/episode/case。
                for distance in retreat_distances_for_selection
# 【L1077】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ]
# 【L1078】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for seed_index, ik_seed in enumerate(ik_seeds):
# 【L1079】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                candidate_solution, candidate_success = lula.compute_inverse_kinematics(
# 【L1080】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    "link_6",
# 【L1081】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    top_down_link_position,
# 【L1082】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    top_down_quaternion,
# 【L1083】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    warm_start=np.asarray(ik_seed, dtype=np.float64),
# 【L1084】计算并保存变量 `position_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    position_tolerance=1e-4,
# 【L1085】计算并保存变量 `orientation_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    orientation_tolerance=1e-3,
# 【L1086】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                )
# 【L1087】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if not candidate_success:
# 【L1088】跳过本次循环剩余语句，继续处理下一个候选项。
                    continue
# 【L1089】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                candidate_raw = np.asarray(candidate_solution, dtype=np.float64)
# 【L1090】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
                try:
# 【L1091】计算并保存变量 `candidate_command`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    candidate_command = closest_equivalent_rm65_solution(
# 【L1092】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                        lula, candidate_raw, grasp_arm
# 【L1093】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1094】计算并保存变量 `candidate_retreat`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    candidate_retreat = solve_continuous_cartesian_path(
# 【L1095】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                        lula,
# 【L1096】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                        retreat_targets_for_selection,
# 【L1097】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                        top_down_quaternion,
# 【L1098】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                        candidate_raw,
# 【L1099】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                        candidate_command,
# 【L1100】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1101】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
                except RuntimeError:
# 【L1102】计算并保存变量 `candidate_retreat`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    candidate_retreat = None
# 【L1103】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if candidate_retreat is None:
# 【L1104】跳过本次循环剩余语句，继续处理下一个候选项。
                    continue
# 【L1105】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                _, candidate_retreat_waypoints, _ = candidate_retreat
# 【L1106】计算并保存变量 `grasp_ik_numerical_seed`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                grasp_ik_numerical_seed = candidate_raw
# 【L1107】计算并保存变量 `top_down_solution`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                top_down_solution = candidate_command
# 【L1108】计算并保存变量 `precomputed_retreat_waypoints`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                precomputed_retreat_waypoints = candidate_retreat_waypoints
# 【L1109】计算并保存变量 `top_down_ik_seed_index`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                top_down_ik_seed_index = seed_index
# 【L1110】计算并保存变量 `effective_pregrasp_distance_m`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                effective_pregrasp_distance_m = candidate_pregrasp_distance_m
# 【L1111】计算并保存变量 `success`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                success = True
# 【L1112】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
                break
# 【L1113】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if success:
# 【L1114】立即结束最近一层循环；通常表示已经找到解或达到成功条件。
                break
# 【L1115】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not success:
# 【L1116】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
            print(
# 【L1117】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "TOP_DOWN_IK_TARGET="
# 【L1118】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                f"position={top_down_link_position.tolist()} "
# 【L1119】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "
# 【L1120】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}",
# 【L1121】计算并保存变量 `flush`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                flush=True,
# 【L1122】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1123】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L1124】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "Lula found no top-down grasp pose with a continuous pregrasp path"
# 【L1125】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1126】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        grasp_arm = np.asarray(top_down_solution, dtype=np.float64)
# 【L1127】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1128】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.lift_mode == "cartesian_vertical":
# 【L1129】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        vertical_lift_target = grasp_link_position + np.array(
# 【L1130】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64
# 【L1131】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1132】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        lift_arm_solution, success = lula.compute_inverse_kinematics(
# 【L1133】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            "link_6",
# 【L1134】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            vertical_lift_target,
# 【L1135】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            rot_matrix_to_quat(grasp_link_rotation),
# 【L1136】计算并保存变量 `warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1137】计算并保存变量 `position_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1138】计算并保存变量 `orientation_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            orientation_tolerance=1e-3,
# 【L1139】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1140】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not success:
# 【L1141】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the local Cartesian vertical lift")
# 【L1142】计算并保存变量 `lift_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        lift_arm = closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)
# 【L1143】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")
# 【L1144】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    lift_link_position, lift_link_rotation = lula.compute_forward_kinematics("link_6", lift_arm)
# 【L1145】计算并保存变量 `expected_lift_translation`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    expected_lift_translation = lift_link_position - grasp_link_position
# 【L1146】计算并保存变量 `expected_source_lift_block_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    expected_source_lift_block_position = source_block_position + expected_lift_translation
# 【L1147】计算并保存变量 `target_lift_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_lift_arm = lift_arm.copy()
# 【L1148】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    target_lift_arm[0] = args.transfer_joint_1_rad
# 【L1149】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    transferred_link_position, transferred_link_rotation = lula.compute_forward_kinematics(
# 【L1150】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "link_6", target_lift_arm
# 【L1151】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1152】计算并保存变量 `release_clear_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    release_clear_arm = None
# 【L1153】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.unassisted_release and not args.place_descent:
# 【L1154】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        release_clear_target = transferred_link_position + np.array(
# 【L1155】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.release_clearance_m], dtype=np.float64
# 【L1156】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1157】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        release_clear_solution, success = lula.compute_inverse_kinematics(
# 【L1158】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            "link_6",
# 【L1159】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            release_clear_target,
# 【L1160】计算并保存变量 `target_orientation`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1161】计算并保存变量 `warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=target_lift_arm,
# 【L1162】计算并保存变量 `position_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1163】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1164】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not success:
# 【L1165】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the vertical release-clearance motion")
# 【L1166】计算并保存变量 `release_clear_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        release_clear_arm = closest_equivalent_rm65_solution(
# 【L1167】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            lula, release_clear_solution, target_lift_arm
# 【L1168】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1169】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        require_continuous_joint_step(
# 【L1170】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            target_lift_arm, release_clear_arm, label="release clearance"
# 【L1171】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1172】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1173】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    transfer_quaternion = np.array(
# 【L1174】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],
# 【L1175】计算并保存变量 `dtype`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1176】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1177】计算并保存变量 `target_release_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)
# 【L1178】计算并保存变量 `target_block_position`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_block_position = target_release_position.copy()
# 【L1179】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    target_block_position[2] = TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L1180】计算并保存变量 `target_block_quaternion`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)
# 【L1181】计算并保存变量 `target_platform_size`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_platform_size = (
# 【L1182】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE
# 【L1183】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1184】计算并保存变量 `target_platform_orientation`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_platform_orientation = (
# 【L1185】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None
# 【L1186】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1187】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    target_platform_position = np.array(
# 【L1188】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [
# 【L1189】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[0],
# 【L1190】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[1],
# 【L1191】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0,
# 【L1192】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ],
# 【L1193】计算并保存变量 `dtype`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1194】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1195】计算并保存变量 `place_waypoints`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    place_waypoints = []
# 【L1196】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.place_descent:
# 【L1197】计算并保存变量 `place_waypoint_count`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        place_waypoint_count = max(1, int(round(args.place_descent_distance_m / 0.01)))
# 【L1198】计算并保存变量 `place_distances`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        place_distances = np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)
# 【L1199】计算并保存变量 `place_warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        place_warm_start = lift_arm.copy()
# 【L1200】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for distance in place_distances:
# 【L1201】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            place_link_target = lift_link_position - np.array(
# 【L1202】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                [0.0, 0.0, distance], dtype=np.float64
# 【L1203】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1204】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            place_solution, success = lula.compute_inverse_kinematics(
# 【L1205】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                "link_6",
# 【L1206】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                place_link_target,
# 【L1207】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                rot_matrix_to_quat(lift_link_rotation),
# 【L1208】计算并保存变量 `warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                warm_start=place_warm_start,
# 【L1209】计算并保存变量 `position_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                position_tolerance=1e-4,
# 【L1210】计算并保存变量 `orientation_tolerance`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                orientation_tolerance=1e-3,
# 【L1211】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1212】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if not success:
# 【L1213】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
                raise RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")
# 【L1214】计算并保存变量 `place_solution`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            place_solution = closest_equivalent_rm65_solution(
# 【L1215】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                lula, place_solution, place_warm_start
# 【L1216】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1217】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            require_continuous_joint_step(
# 【L1218】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                place_warm_start, place_solution, label=f"place waypoint {distance:.3f} m"
# 【L1219】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1220】计算并保存变量 `place_warm_start`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            place_warm_start = place_solution
# 【L1221】计算并保存变量 `rotated_place_solution`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            rotated_place_solution = place_warm_start.copy()
# 【L1222】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            rotated_place_solution[0] += args.transfer_joint_1_rad - lift_arm[0]
# 【L1223】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            place_waypoints.append(rotated_place_solution)
# 【L1224】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1225】计算并保存变量 `grasp_link_quaternion`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    grasp_link_quaternion = rot_matrix_to_quat(grasp_link_rotation)
# 【L1226】计算并保存变量 `outward_direction`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    outward_direction = (
# 【L1227】调用 `np.array`：创建 NumPy 数组。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        np.array([0.0, 0.0, -1.0], dtype=np.float64)
# 【L1228】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.grasp_orientation_mode == "top_down"
# 【L1229】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        else quaternion_to_matrix_wxyz(
# 【L1230】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L1231】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        )[:, 0]
# 【L1232】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1233】计算并保存变量 `waypoint_count`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    waypoint_count = max(1, int(round(effective_pregrasp_distance_m / 0.01)))
# 【L1234】计算并保存变量 `retreat_distances`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    retreat_distances = np.linspace(0.01, effective_pregrasp_distance_m, waypoint_count)
# 【L1235】计算并保存变量 `retreat_targets`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    retreat_targets = [
# 【L1236】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        grasp_link_position - distance * outward_direction
# 【L1237】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for distance in retreat_distances
# 【L1238】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    ]
# 【L1239】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if precomputed_retreat_waypoints is not None:
# 【L1240】计算并保存变量 `retreat_waypoints`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        retreat_waypoints = [item.copy() for item in precomputed_retreat_waypoints]
# 【L1241】否则分支：前面的 if/elif 都不成立时执行。
    else:
# 【L1242】计算并保存变量 `retreat_result`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        retreat_result = solve_continuous_cartesian_path(
# 【L1243】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            lula,
# 【L1244】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            retreat_targets,
# 【L1245】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            grasp_link_quaternion,
# 【L1246】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            grasp_ik_numerical_seed,
# 【L1247】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            grasp_arm,
# 【L1248】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1249】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if retreat_result is None:
# 【L1250】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError("Lula found no continuous Cartesian pregrasp path")
# 【L1251】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        _, retreat_waypoints, _ = retreat_result
# 【L1252】计算并保存变量 `pregrasp_arm`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    pregrasp_arm = grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]
# 【L1253】计算并保存变量 `retreat_joint_sequence`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    retreat_joint_sequence = np.vstack([grasp_arm, *retreat_waypoints])
# 【L1254】计算并保存变量 `retreat_max_command_step_rad`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    retreat_max_command_step_rad = float(
# 【L1255】调用 `np.diff`：计算相邻元素或相邻帧之差。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        np.max(np.abs(np.diff(retreat_joint_sequence, axis=0)))
# 【L1256】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1257】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1258】计算并保存变量 `place_max_command_step_rad`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    place_max_command_step_rad = None
# 【L1259】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if place_waypoints:
# 【L1260】计算并保存变量 `place_joint_sequence`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        place_joint_sequence = np.vstack([target_lift_arm, *place_waypoints])
# 【L1261】计算并保存变量 `place_max_command_step_rad`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        place_max_command_step_rad = float(
# 【L1262】调用 `np.diff`：计算相邻元素或相邻帧之差。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            np.max(np.abs(np.diff(place_joint_sequence, axis=0)))
# 【L1263】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1264】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.diagnose_kinematics_only:
# 【L1265】计算并保存变量 `diagnostic`；该值服务于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        diagnostic = {
# 【L1266】定义字典/JSON 字段 `status`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "status": "diagnostic",
# 【L1267】定义字典/JSON 字段 `simulation_only`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "simulation_only": True,
# 【L1268】定义字典/JSON 字段 `robot_base_position_m`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L1269】定义字典/JSON 字段 `transfer_joint_1_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1270】定义字典/JSON 字段 `grasp_orientation_mode`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L1271】定义字典/JSON 字段 `top_down_ik_seed_index`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L1272】定义字典/JSON 字段 `requested_pregrasp_distance_m`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1273】定义字典/JSON 字段 `pregrasp_distance_m`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1274】定义字典/JSON 字段 `grasp_arm_joint_position_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "grasp_arm_joint_position_rad": grasp_arm.tolist(),
# 【L1275】定义字典/JSON 字段 `lift_arm_joint_position_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "lift_arm_joint_position_rad": lift_arm.tolist(),
# 【L1276】定义字典/JSON 字段 `target_lift_arm_joint_position_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "target_lift_arm_joint_position_rad": target_lift_arm.tolist(),
# 【L1277】定义字典/JSON 字段 `retreat_waypoint_count`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "retreat_waypoint_count": len(retreat_waypoints),
# 【L1278】定义字典/JSON 字段 `retreat_max_command_step_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "retreat_max_command_step_rad": retreat_max_command_step_rad,
# 【L1279】定义字典/JSON 字段 `retreat_waypoint_joint_position_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "retreat_waypoint_joint_position_rad": [
# 【L1280】执行“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                item.tolist() for item in retreat_waypoints
# 【L1281】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ],
# 【L1282】定义字典/JSON 字段 `place_waypoint_count`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "place_waypoint_count": len(place_waypoints),
# 【L1283】定义字典/JSON 字段 `place_max_command_step_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "place_max_command_step_rad": place_max_command_step_rad,
# 【L1284】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "place_ik_uses_base_rotation_symmetry": True,
# 【L1285】定义字典/JSON 字段 `place_waypoint_joint_position_rad`；它把“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的结果用稳定键名记录下来。
            "place_waypoint_joint_position_rad": [item.tolist() for item in place_waypoints],
# 【L1286】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        }
# 【L1287】调用 `mkdir`：创建目录。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1288】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L1289】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L1290】结束当前函数并把结果交给调用者；这里完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”的输出。
        return 0
# 【L1291】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1292】给变量 `sim` 赋值：IsaacLab SimulationContext，负责物理时间步。
    sim = SimulationContext(
# 【L1293】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        sim_utils.SimulationCfg(
# 【L1294】计算并保存变量 `dt`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dt=1.0 / 240.0,
# 【L1295】计算并保存变量 `device`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            device=args.device,
# 【L1296】计算并保存变量 `physics_material`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1297】计算并保存变量 `static_friction`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                static_friction=1.5,
# 【L1298】计算并保存变量 `dynamic_friction`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                dynamic_friction=1.2,
# 【L1299】计算并保存变量 `restitution`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                restitution=0.0,
# 【L1300】计算并保存变量 `friction_combine_mode`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                friction_combine_mode="max",
# 【L1301】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1302】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1303】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1304】计算并保存变量 `light_cfg`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
# 【L1305】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    light_cfg.func("/World/Light", light_cfg)
# 【L1306】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.diagnose_approach_only:
# 【L1307】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        spawn_platform(
# 【L1308】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            "/World/TargetPlatform",
# 【L1309】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            target_platform_position,
# 【L1310】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            target_platform_size,
# 【L1311】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (0.12, 0.45, 0.20),
# 【L1312】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            target_platform_orientation,
# 【L1313】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1314】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.natural_source_gravity:
# 【L1315】调用 `np.array`：创建 NumPy 数组。本行位于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        source_platform_position = np.array(
# 【L1316】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            [
# 【L1317】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[0],
# 【L1318】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[1],
# 【L1319】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0,
# 【L1320】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ],
# 【L1321】计算并保存变量 `dtype`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dtype=np.float64,
# 【L1322】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1323】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        spawn_platform(
# 【L1324】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)
# 【L1325】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1326】计算并保存变量 `target_platform_collision_apis`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    target_platform_collision_apis = []
# 【L1327】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for prim in get_current_stage().Traverse():
# 【L1328】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1329】计算并保存变量 `collision_api`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1330】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1331】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            target_platform_collision_apis.append(collision_api)
# 【L1332】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1333】给变量 `robot` 赋值：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot = Articulation(
# 【L1334】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ArticulationCfg(
# 【L1335】计算并保存变量 `prim_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Robot",
# 【L1336】计算并保存变量 `spawn`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            spawn=sim_utils.UsdFileCfg(
# 【L1337】计算并保存变量 `usd_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                usd_path=str(usd),
# 【L1338】计算并保存变量 `activate_contact_sensors`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                activate_contact_sensors=True,
# 【L1339】计算并保存变量 `rigid_props`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
# 【L1340】计算并保存变量 `articulation_props`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
# 【L1341】计算并保存变量 `enabled_self_collisions`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    enabled_self_collisions=False,
# 【L1342】计算并保存变量 `solver_position_iteration_count`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=64,
# 【L1343】计算并保存变量 `solver_velocity_iteration_count`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1344】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1345】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1346】计算并保存变量 `init_state`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            init_state=ArticulationCfg.InitialStateCfg(
# 【L1347】计算并保存变量 `pos`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(robot_base_position),
# 【L1348】计算并保存变量 `joint_pos`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                joint_pos={"joint_.*": 0.0, "tool_.*": 0.0},
# 【L1349】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1350】计算并保存变量 `actuators`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            actuators={
# 【L1351】定义字典/JSON 字段 `arm`；它把“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的结果用稳定键名记录下来。
                "arm": ImplicitActuatorCfg(
# 【L1352】计算并保存变量 `joint_names_expr`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["joint_[1-6]"],
# 【L1353】计算并保存变量 `effort_limit_sim`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.arm_effort_limit_sim,
# 【L1354】计算并保存变量 `velocity_limit_sim`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1355】计算并保存变量 `stiffness`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.arm_stiffness,
# 【L1356】计算并保存变量 `damping`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.arm_damping,
# 【L1357】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1358】定义字典/JSON 字段 `gripper`；它把“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的结果用稳定键名记录下来。
                "gripper": ImplicitActuatorCfg(
# 【L1359】计算并保存变量 `joint_names_expr`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["tool_.*"],
# 【L1360】计算并保存变量 `effort_limit_sim`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.gripper_effort_limit_sim,
# 【L1361】计算并保存变量 `velocity_limit_sim`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1362】计算并保存变量 `stiffness`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.gripper_stiffness,
# 【L1363】计算并保存变量 `damping`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.gripper_damping,
# 【L1364】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1365】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            },
# 【L1366】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1367】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1368】给变量 `cube` 赋值：IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube = RigidObject(
# 【L1369】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        RigidObjectCfg(
# 【L1370】计算并保存变量 `prim_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Cube",
# 【L1371】计算并保存变量 `spawn`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            spawn=sim_utils.CuboidCfg(
# 【L1372】计算并保存变量 `size`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                size=BLOCK_SIZE,
# 【L1373】计算并保存变量 `rigid_props`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
# 【L1374】计算并保存变量 `disable_gravity`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    disable_gravity=not args.natural_source_gravity,
# 【L1375】计算并保存变量 `solver_position_iteration_count`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=32,
# 【L1376】计算并保存变量 `solver_velocity_iteration_count`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1377】计算并保存变量 `max_depenetration_velocity`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    max_depenetration_velocity=1.0,
# 【L1378】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1379】计算并保存变量 `mass_props`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                mass_props=sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG),
# 【L1380】计算并保存变量 `collision_props`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L1381】计算并保存变量 `visual_material`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
# 【L1382】计算并保存变量 `physics_material`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1383】计算并保存变量 `static_friction`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    static_friction=1.5,
# 【L1384】计算并保存变量 `dynamic_friction`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    dynamic_friction=1.2,
# 【L1385】计算并保存变量 `restitution`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    restitution=0.0,
# 【L1386】计算并保存变量 `friction_combine_mode`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    friction_combine_mode="max",
# 【L1387】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1388】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1389】计算并保存变量 `init_state`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            init_state=RigidObjectCfg.InitialStateCfg(
# 【L1390】计算并保存变量 `pos`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(source_block_position),
# 【L1391】计算并保存变量 `rot`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rot=tuple(source_block_quaternion),
# 【L1392】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1393】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1394】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1395】计算并保存变量 `external_camera`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    external_camera = None
# 【L1396】计算并保存变量 `wrist_camera`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    wrist_camera = None
# 【L1397】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.record_images:
# 【L1398】计算并保存变量 `external_camera`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        external_camera = Camera(
# 【L1399】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            CameraCfg(
# 【L1400】计算并保存变量 `prim_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/ExternalCamera",
# 【L1401】计算并保存变量 `update_period`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1402】计算并保存变量 `height`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1403】计算并保存变量 `width`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1404】计算并保存变量 `data_types`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1405】计算并保存变量 `spawn`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1406】计算并保存变量 `focal_length`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=24.0,
# 【L1407】计算并保存变量 `focus_distance`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=2.0,
# 【L1408】计算并保存变量 `horizontal_aperture`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1409】计算并保存变量 `clipping_range`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1410】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1411】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1412】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1413】计算并保存变量 `wrist_camera`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        wrist_camera = Camera(
# 【L1414】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            CameraCfg(
# 【L1415】计算并保存变量 `prim_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/WristCamera",
# 【L1416】计算并保存变量 `update_period`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1417】计算并保存变量 `height`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1418】计算并保存变量 `width`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1419】计算并保存变量 `data_types`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1420】计算并保存变量 `spawn`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1421】计算并保存变量 `focal_length`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=18.0,
# 【L1422】计算并保存变量 `focus_distance`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=1.0,
# 【L1423】计算并保存变量 `horizontal_aperture`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1424】计算并保存变量 `clipping_range`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1425】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1426】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1427】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1428】调用 `Path`：创建路径对象。本行位于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))
# 【L1429】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    CONTACT_SENSORS.update(
# 【L1430】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        {
# 【L1431】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            body_path.rsplit("/", 1)[-1]: ContactSensor(
# 【L1432】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                ContactSensorCfg(
# 【L1433】计算并保存变量 `prim_path`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    prim_path=body_path,
# 【L1434】计算并保存变量 `update_period`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    update_period=0.0,
# 【L1435】计算并保存变量 `history_length`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    history_length=400,
# 【L1436】计算并保存变量 `filter_prim_paths_expr`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    filter_prim_paths_expr=["/World/Cube"],
# 【L1437】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                )
# 【L1438】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1439】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)
# 【L1440】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        }
# 【L1441】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1442】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1443】计算并保存变量 `isolated_paths`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    isolated_paths = []
# 【L1444】计算并保存变量 `approach_arm_gravity_apis`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    approach_arm_gravity_apis = []
# 【L1445】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for prim in get_current_stage().Traverse():
# 【L1446】调用 `Path`：创建路径对象。本行位于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        path = str(prim.GetPath())
# 【L1447】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if (
# 【L1448】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)
# 【L1449】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and path in ARM_BODY_PATHS
# 【L1450】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1451】开始一个缩进代码块或键值结构；该块负责“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1452】计算并保存变量 `rigid_body_api`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
# 【L1453】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            rigid_body_api.CreateDisableGravityAttr().Set(True)
# 【L1454】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            approach_arm_gravity_apis.append(rigid_body_api)
# 【L1455】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if (
# 【L1456】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            not args.enable_moving_gripper_gravity
# 【L1457】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and path in MOVING_GRIPPER_BODY_PATHS
# 【L1458】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1459】开始一个缩进代码块或键值结构；该块负责“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1460】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
# 【L1461】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            isolated_paths.append(path)
# 【L1462】调用 `Path`：创建路径对象。本行位于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    cube_prim = get_current_stage().GetPrimAtPath("/World/Cube")
# 【L1463】计算并保存变量 `cube_rigid_body_api`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    cube_rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)
# 【L1464】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(not args.natural_source_gravity)
# 【L1465】计算并保存变量 `cube_collision_apis`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    cube_collision_apis = []
# 【L1466】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for prim in get_current_stage().Traverse():
# 【L1467】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1468】计算并保存变量 `collision_api`；该值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1469】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            cube_collision_apis.append(collision_api)
# 【L1470】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if args.collision_bypass_during_approach:
# 【L1471】执行“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1472】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not cube_collision_apis:
# 【L1473】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError("no CollisionAPI prim found below /World/Cube")
# 【L1474】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1475】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    sim.reset()
# 【L1476】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    robot.reset()
# 【L1477】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cube.reset()
# 【L1478】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if external_camera is not None:
# 【L1479】计算并保存变量 `scene_center`；该值服务于“reset、关节索引和 episode 记录器初始化”。
        scene_center = 0.5 * (source_block_position + target_block_position)
# 【L1480】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“reset、关节索引和 episode 记录器初始化”。
        external_eye = torch.as_tensor(
# 【L1481】调用 `np.array`：创建 NumPy 数组。本行位于“reset、关节索引和 episode 记录器初始化”。
            scene_center + np.array([0.70, 0.70, 0.45]),
# 【L1482】计算并保存变量 `device`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1483】计算并保存变量 `dtype`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1484】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ).unsqueeze(0)
# 【L1485】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“reset、关节索引和 episode 记录器初始化”。
        external_target = torch.as_tensor(
# 【L1486】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“reset、关节索引和 episode 记录器初始化”。
            scene_center,
# 【L1487】计算并保存变量 `device`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1488】计算并保存变量 `dtype`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1489】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ).unsqueeze(0)
# 【L1490】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        external_camera.set_world_poses_from_view(external_eye, external_target)
# 【L1491】计算并保存变量 `joint_names`；该值服务于“reset、关节索引和 episode 记录器初始化”。
    joint_names = list(robot.data.joint_names)
# 【L1492】计算并保存变量 `arm_ids`；该值服务于“reset、关节索引和 episode 记录器初始化”。
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
# 【L1493】计算并保存变量 `gripper_ids`；该值服务于“reset、关节索引和 episode 记录器初始化”。
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
# 【L1494】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if GRIPPER_MASTER_JOINT not in joint_names:
# 【L1495】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")
# 【L1496】给变量 `episode_recorder` 赋值：把同步帧保存在内存并最终写盘的记录器。
    episode_recorder = None
# 【L1497】给变量 `episode_capture` 赋值：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
    episode_capture = None
# 【L1498】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.record_episode_dir is not None:
# 【L1499】给变量 `episode_recorder` 赋值：把同步帧保存在内存并最终写盘的记录器。
        episode_recorder = EpisodeRecorder(
# 【L1500】计算并保存变量 `output_dir`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            output_dir=args.record_episode_dir.expanduser().resolve(),
# 【L1501】计算并保存变量 `prompt`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            prompt=args.episode_prompt,
# 【L1502】计算并保存变量 `control_hz`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            control_hz=1.0 / (sim.get_physics_dt() * args.record_stride_steps),
# 【L1503】计算并保存变量 `metadata`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            metadata={
# 【L1504】定义字典/JSON 字段 `simulation_only`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "simulation_only": True,
# 【L1505】定义字典/JSON 字段 `expert`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "expert": None if args.pi05_closed_loop else "scripted_rm65_pick_place",
# 【L1506】定义字典/JSON 字段 `pi05_used`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "pi05_used": args.pi05_closed_loop,
# 【L1507】定义字典/JSON 字段 `policy_checkpoint_id`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "policy_checkpoint_id": (
# 【L1508】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                    args.policy_checkpoint_id if args.pi05_closed_loop else None
# 【L1509】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
                ),
# 【L1510】定义字典/JSON 字段 `images_recorded`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "images_recorded": args.record_images,
# 【L1511】定义字典/JSON 字段 `robot_base_position_m`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "robot_base_position_m": robot_base_position.tolist(),
# 【L1512】定义字典/JSON 字段 `source_block_position_m`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "source_block_position_m": source_block_position.tolist(),
# 【L1513】定义字典/JSON 字段 `source_offset_xy_m`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L1514】定义字典/JSON 字段 `target_block_position_m`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "target_block_position_m": target_block_position.tolist(),
# 【L1515】定义字典/JSON 字段 `transfer_joint_1_rad`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1516】定义字典/JSON 字段 `record_stride_steps`；它把“reset、关节索引和 episode 记录器初始化”中的结果用稳定键名记录下来。
                "record_stride_steps": args.record_stride_steps,
# 【L1517】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            },
# 【L1518】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1519】给变量 `episode_capture` 赋值：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture = ExpertEpisodeCapture(
# 【L1520】计算并保存变量 `recorder`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            recorder=episode_recorder,
# 【L1521】计算并保存变量 `arm_ids`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            arm_ids=arm_ids,
# 【L1522】计算并保存变量 `gripper_master_id`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1523】计算并保存变量 `stride_steps`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            stride_steps=args.record_stride_steps,
# 【L1524】计算并保存变量 `physics_dt`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            physics_dt=sim.get_physics_dt(),
# 【L1525】给变量 `sim` 赋值：IsaacLab SimulationContext，负责物理时间步。
            sim=sim,
# 【L1526】计算并保存变量 `external_camera`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            external_camera=external_camera,
# 【L1527】计算并保存变量 `wrist_camera`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            wrist_camera=wrist_camera,
# 【L1528】计算并保存变量 `wrist_tool_body_id`；该值服务于“reset、关节索引和 episode 记录器初始化”。
            wrist_tool_body_id=(
# 【L1529】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                list(robot.data.body_names).index("tool_base_link")
# 【L1530】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if args.record_images
# 【L1531】执行“reset、关节索引和 episode 记录器初始化”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                else None
# 【L1532】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            ),
# 【L1533】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1534】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1535】给变量 `state` 赋值：当前要写给 articulation 的全部关节目标张量。
    state = robot.data.default_joint_pos.clone()
# 【L1536】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“写入初始状态；选择脚本专家或 π0.5 分支”。
    state[:, arm_ids] = torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)
# 【L1537】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    state[:, gripper_ids] = 0.0
# 【L1538】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
# 【L1539】计算并保存变量 `cube_pose`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube_pose = cube.data.default_root_state[:, :7].clone()
# 【L1540】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube_pose[:, :3] = torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)
# 【L1541】调用 `torch.as_tensor`：把 NumPy/列表转换成指定设备和类型的 Torch 张量。本行位于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube_pose[:, 3:7] = torch.as_tensor(
# 【L1542】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        source_block_quaternion, device=sim.device, dtype=cube_pose.dtype
# 【L1543】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1544】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cube.write_root_pose_to_sim(cube_pose)
# 【L1545】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cube.write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))
# 【L1546】执行“写入初始状态；选择脚本专家或 π0.5 分支”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    hold(
# 【L1547】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        sim,
# 【L1548】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        robot,
# 【L1549】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        cube,
# 【L1550】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        state,
# 【L1551】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        60 if args.initialize_at_grasp else 240,
# 【L1552】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        "SOURCE_SETTLE",
# 【L1553】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        episode_capture,
# 【L1554】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1555】计算并保存变量 `settled_source_position`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    settled_source_position = cube.data.root_pos_w[0].clone()
# 【L1556】计算并保存变量 `settled_source_quaternion`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    settled_source_quaternion = cube.data.root_quat_w[0].clone()
# 【L1557】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print("PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True)
# 【L1558】空行：分隔“写入初始状态；选择脚本专家或 π0.5 分支”中的逻辑段，让结构更容易看清。

# 【L1559】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.pi05_closed_loop:
# 【L1560】内部一致性断言：运行到这里时该对象必须已经存在，否则说明程序逻辑有误。
        assert episode_capture is not None
# 【L1561】内部一致性断言：运行到这里时该对象必须已经存在，否则说明程序逻辑有误。
        assert episode_recorder is not None
# 【L1562】结束当前函数并把结果交给调用者；这里完成“写入初始状态；选择脚本专家或 π0.5 分支”的输出。
        return run_pi05_closed_loop(
# 【L1563】给变量 `sim` 赋值：IsaacLab SimulationContext，负责物理时间步。
            sim=sim,
# 【L1564】给变量 `robot` 赋值：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            robot=robot,
# 【L1565】给变量 `cube` 赋值：IsaacLab RigidObject；本任务被抓取和放置的方块。
            cube=cube,
# 【L1566】给变量 `state` 赋值：当前要写给 articulation 的全部关节目标张量。
            state=state,
# 【L1567】计算并保存变量 `arm_ids`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            arm_ids=arm_ids,
# 【L1568】计算并保存变量 `gripper_ids`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_ids=gripper_ids,
# 【L1569】计算并保存变量 `gripper_master_id`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1570】计算并保存变量 `target_block_position`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_block_position=target_block_position,
# 【L1571】计算并保存变量 `settled_source_position`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            settled_source_position=settled_source_position,
# 【L1572】计算并保存变量 `target_platform_collision_apis`；该值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_platform_collision_apis=target_platform_collision_apis,
# 【L1573】给变量 `episode_capture` 赋值：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
            episode_capture=episode_capture,
# 【L1574】给变量 `episode_recorder` 赋值：把同步帧保存在内存并最终写盘的记录器。
            episode_recorder=episode_recorder,
# 【L1575】给变量 `output` 赋值：输出文件路径。
            output=output,
# 【L1576】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        )
# 【L1577】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1578】计算并保存变量 `approach_waypoints`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    approach_waypoints = [] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]
# 【L1579】计算并保存变量 `previous_waypoint`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    previous_waypoint = pregrasp_arm
# 【L1580】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for index, waypoint in enumerate(approach_waypoints, start=1):
# 【L1581】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        smooth_move(
# 【L1582】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            sim,
# 【L1583】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            robot,
# 【L1584】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            cube,
# 【L1585】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            state,
# 【L1586】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            arm_ids,
# 【L1587】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            previous_waypoint,
# 【L1588】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            waypoint,
# 【L1589】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            120,
# 【L1590】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            f"APPROACH_{index}",
# 【L1591】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
            episode_capture,
# 【L1592】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1593】计算并保存变量 `previous_waypoint`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        previous_waypoint = waypoint
# 【L1594】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.collision_bypass_during_approach:
# 【L1595】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)
# 【L1596】计算并保存变量 `pre_restore_arm_error`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        pre_restore_arm_error = float(
# 【L1597】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            np.max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))
# 【L1598】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1599】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print(f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True)
# 【L1600】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.collision_bypass_during_approach:
# 【L1601】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for collision_api in cube_collision_apis:
# 【L1602】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1603】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print("PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True)
# 【L1604】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.initialize_at_grasp:
# 【L1605】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)
# 【L1606】计算并保存变量 `actual_approach_arm`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    actual_approach_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1607】计算并保存变量 `open_l2_midpoint`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_l2_midpoint = 0.5 * (
# 【L1608】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")
# 【L1609】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1610】计算并保存变量 `open_midpoint_to_block`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_midpoint_to_block = float(
# 【L1611】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        torch.linalg.vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])
# 【L1612】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1613】计算并保存变量 `open_midpoint_world`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_midpoint_world = open_l2_midpoint.detach().cpu().numpy()
# 【L1614】计算并保存变量 `open_midpoint_minus_block`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_midpoint_minus_block = open_midpoint_world - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1615】计算并保存变量 `open_pad_center_world_by_body`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_pad_center_world_by_body = {
# 【L1616】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1617】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1618】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1619】计算并保存变量 `open_pad_center_minus_block_by_body`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    open_pad_center_minus_block_by_body = {
# 【L1620】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: (
# 【L1621】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
            np.asarray(world_position, dtype=np.float64)
# 【L1622】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1623】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ).tolist()
# 【L1624】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, world_position in open_pad_center_world_by_body.items()
# 【L1625】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1626】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(
# 【L1627】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "PICK_PLACE_APPROACH="
# 【L1628】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
        + json.dumps(
# 【L1629】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L1630】定义字典/JSON 字段 `max_arm_joint_error_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1631】定义字典/JSON 字段 `l2_midpoint_to_block_center_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L1632】定义字典/JSON 字段 `l2_midpoint_minus_block_center_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1633】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L1634】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L1635】计算并保存变量 `flush`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L1636】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1637】计算并保存变量 `close_start`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_start = np.zeros(len(gripper_ids), dtype=np.float64)
# 【L1638】计算并保存变量 `close_target`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_target = np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)
# 【L1639】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    smooth_move(
# 【L1640】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        sim,
# 【L1641】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        robot,
# 【L1642】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        cube,
# 【L1643】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        state,
# 【L1644】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        gripper_ids,
# 【L1645】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        close_start,
# 【L1646】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        close_target,
# 【L1647】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        180,
# 【L1648】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        "CLOSE",
# 【L1649】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“脚本专家的接近、闭合夹爪和接触诊断”。
        episode_capture,
# 【L1650】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1651】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)
# 【L1652】计算并保存变量 `closed_position`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_position = cube.data.root_pos_w[0].clone()
# 【L1653】计算并保存变量 `closed_link_6_position`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1654】计算并保存变量 `closed_pad_center_world_by_body`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_pad_center_world_by_body = {
# 【L1655】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1656】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1657】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1658】计算并保存变量 `closed_pad_center_minus_block_by_body`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_pad_center_minus_block_by_body = {
# 【L1659】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
        body_name: (np.asarray(world_position, dtype=np.float64) - closed_position.detach().cpu().numpy()).tolist()
# 【L1660】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, world_position in closed_pad_center_world_by_body.items()
# 【L1661】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1662】计算并保存变量 `closed_l2_gap`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_l2_gap = float(
# 【L1663】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        torch.linalg.vector_norm(
# 【L1664】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L1665】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1666】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1667】计算并保存变量 `closed_gripper_joint_position`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    closed_gripper_joint_position = robot.data.joint_pos[0, gripper_ids].clone()
# 【L1668】计算并保存变量 `close_contact_force_statistics_by_body`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_contact_force_statistics_by_body = {}
# 【L1669】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L1670】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        close_contact_force_statistics_by_body[body_name] = contact_force_statistics(contact_sensor)
# 【L1671】计算并保存变量 `close_contact_force_by_body_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_contact_force_by_body_n = {
# 【L1672】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: statistics["peak_n"]
# 【L1673】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1674】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1675】计算并保存变量 `close_current_contact_force_by_body_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_current_contact_force_by_body_n = {
# 【L1676】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: statistics["current_n"]
# 【L1677】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1678】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1679】计算并保存变量 `close_recent_mean_contact_force_by_body_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_recent_mean_contact_force_by_body_n = {
# 【L1680】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        body_name: statistics["recent_mean_n"]
# 【L1681】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L1682】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1683】计算并保存变量 `close_current_contact_force_vector_by_body_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_current_contact_force_vector_by_body_n = {}
# 【L1684】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L1685】计算并保存变量 `current`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        current = contact_sensor.data.force_matrix_w
# 【L1686】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        close_current_contact_force_vector_by_body_n[body_name] = (
# 【L1687】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“脚本专家的接近、闭合夹爪和接触诊断”。
            [0.0, 0.0, 0.0]
# 【L1688】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if current is None
# 【L1689】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else current.reshape(-1, 3).sum(dim=0).detach().cpu().tolist()
# 【L1690】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1691】计算并保存变量 `close_left_finger_contact_force_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_left_finger_contact_force_n = max(
# 【L1692】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")
# 【L1693】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1694】计算并保存变量 `close_right_finger_contact_force_n`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
    close_right_finger_contact_force_n = max(
# 【L1695】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")
# 【L1696】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1697】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(
# 【L1698】执行“脚本专家的接近、闭合夹爪和接触诊断”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        "PICK_PLACE_CLOSE_CONTACT="
# 【L1699】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
        + json.dumps(
# 【L1700】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L1701】定义字典/JSON 字段 `left_finger_force_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "left_finger_force_n": close_left_finger_contact_force_n,
# 【L1702】定义字典/JSON 字段 `right_finger_force_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "right_finger_force_n": close_right_finger_contact_force_n,
# 【L1703】定义字典/JSON 字段 `current_force_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "current_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1704】定义字典/JSON 字段 `recent_mean_force_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "recent_mean_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1705】定义字典/JSON 字段 `current_force_vector_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "current_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1706】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L1707】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L1708】计算并保存变量 `flush`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L1709】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1710】空行：分隔“脚本专家的接近、闭合夹爪和接触诊断”中的逻辑段，让结构更容易看清。

# 【L1711】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.diagnose_approach_only:
# 【L1712】计算并保存变量 `diagnostic`；该值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        diagnostic = {
# 【L1713】定义字典/JSON 字段 `status`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "status": "diagnostic",
# 【L1714】定义字典/JSON 字段 `simulation_only`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "simulation_only": True,
# 【L1715】定义字典/JSON 字段 `collision_bypass_during_approach`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L1716】定义字典/JSON 字段 `initialized_at_grasp`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L1717】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L1718】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L1719】定义字典/JSON 字段 `natural_source_gravity`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "natural_source_gravity": args.natural_source_gravity,
# 【L1720】定义字典/JSON 字段 `moving_gripper_gravity_disabled`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L1721】定义字典/JSON 字段 `arm_actuator`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "arm_actuator": {
# 【L1722】定义字典/JSON 字段 `effort_limit_sim`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "effort_limit_sim": args.arm_effort_limit_sim,
# 【L1723】定义字典/JSON 字段 `stiffness`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "stiffness": args.arm_stiffness,
# 【L1724】定义字典/JSON 字段 `damping`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "damping": args.arm_damping,
# 【L1725】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L1726】定义字典/JSON 字段 `gripper_actuator`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "gripper_actuator": {
# 【L1727】定义字典/JSON 字段 `effort_limit_sim`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L1728】定义字典/JSON 字段 `stiffness`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "stiffness": args.gripper_stiffness,
# 【L1729】定义字典/JSON 字段 `damping`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "damping": args.gripper_damping,
# 【L1730】定义字典/JSON 字段 `close_target_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
                "close_target_rad": args.gripper_close_target_rad,
# 【L1731】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L1732】定义字典/JSON 字段 `requested_pregrasp_distance_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1733】定义字典/JSON 字段 `pregrasp_distance_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1734】定义字典/JSON 字段 `grasp_world_offset_x_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L1735】定义字典/JSON 字段 `grasp_world_offset_z_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L1736】定义字典/JSON 字段 `robot_base_position_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L1737】定义字典/JSON 字段 `grasp_orientation_mode`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L1738】定义字典/JSON 字段 `top_down_yaw_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L1739】定义字典/JSON 字段 `top_down_tilt_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L1740】定义字典/JSON 字段 `top_down_ik_multistart`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L1741】定义字典/JSON 字段 `top_down_ik_seed_index`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L1742】定义字典/JSON 字段 `top_down_blend`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "top_down_blend": args.top_down_blend,
# 【L1743】定义字典/JSON 字段 `reference_block_from_link_local_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L1744】定义字典/JSON 字段 `lift_mode`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "lift_mode": args.lift_mode,
# 【L1745】定义字典/JSON 字段 `cartesian_lift_height_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L1746】定义字典/JSON 字段 `settled_source_position_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L1747】定义字典/JSON 字段 `settled_source_quaternion_wxyz`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L1748】定义字典/JSON 字段 `closed_position_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L1749】定义字典/JSON 字段 `close_left_finger_contact_force_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L1750】定义字典/JSON 字段 `close_right_finger_contact_force_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L1751】定义字典/JSON 字段 `close_contact_force_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L1752】定义字典/JSON 字段 `close_current_contact_force_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1753】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1754】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1755】定义字典/JSON 字段 `approach_actual_arm_joint_position_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_actual_arm_joint_position_rad": actual_approach_arm.tolist(),
# 【L1756】定义字典/JSON 字段 `approach_target_arm_joint_position_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_target_arm_joint_position_rad": grasp_arm.tolist(),
# 【L1757】定义字典/JSON 字段 `cartesian_retreat_distances_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L1758】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L1759】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1760】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L1761】定义字典/JSON 字段 `approach_l2_midpoint_world_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L1762】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1763】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L1764】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L1765】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L1766】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L1767】定义字典/JSON 字段 `closed_l2_tip_gap_m`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "closed_l2_tip_gap_m": closed_l2_gap,
# 【L1768】定义字典/JSON 字段 `closed_gripper_joint_position_rad`；它把“脚本专家的接近、闭合夹爪和接触诊断”中的结果用稳定键名记录下来。
            "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L1769】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        }
# 【L1770】调用 `mkdir`：创建目录。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1771】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“脚本专家的接近、闭合夹爪和接触诊断”。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L1772】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L1773】结束当前函数并把结果交给调用者；这里完成“脚本专家的接近、闭合夹爪和接触诊断”的输出。
        return 0
# 【L1774】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1775】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.disable_arm_gravity_through_transport:
# 【L1776】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for rigid_body_api in approach_arm_gravity_apis:
# 【L1777】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L1778】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport:
# 【L1779】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print("PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True)
# 【L1780】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L1781】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    smooth_move(
# 【L1782】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture
# 【L1783】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
    )
# 【L1784】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)
# 【L1785】计算并保存变量 `lifted_position`；该值服务于“恢复重力、抬升以及抬升失败早停”。
    lifted_position = cube.data.root_pos_w[0].clone()
# 【L1786】计算并保存变量 `lifted_link_6_position`；该值服务于“恢复重力、抬升以及抬升失败早停”。
    lifted_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1787】计算并保存变量 `actual_lift_link_translation`；该值服务于“恢复重力、抬升以及抬升失败早停”。
    actual_lift_link_translation = lifted_link_6_position - closed_link_6_position
# 【L1788】计算并保存变量 `actual_lift_arm`；该值服务于“恢复重力、抬升以及抬升失败早停”。
    actual_lift_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1789】计算并保存变量 `lift_height_after_attempt`；该值服务于“恢复重力、抬升以及抬升失败早停”。
    lift_height_after_attempt = float((lifted_position[2] - closed_position[2]).item())
# 【L1790】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if lift_height_after_attempt <= 0.02:
# 【L1791】计算并保存变量 `failed_lift_report`；该值服务于“恢复重力、抬升以及抬升失败早停”。
        failed_lift_report = {
# 【L1792】定义字典/JSON 字段 `status`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "status": "fail",
# 【L1793】定义字典/JSON 字段 `failure_stage`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "failure_stage": "lift",
# 【L1794】定义字典/JSON 字段 `simulation_only`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "simulation_only": True,
# 【L1795】定义字典/JSON 字段 `pi05_used`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "pi05_used": False,
# 【L1796】定义字典/JSON 字段 `real_robot_command_sent`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "real_robot_command_sent": False,
# 【L1797】定义字典/JSON 字段 `natural_source_gravity`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "natural_source_gravity": args.natural_source_gravity,
# 【L1798】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L1799】定义字典/JSON 字段 `requested_pregrasp_distance_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1800】定义字典/JSON 字段 `pregrasp_distance_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1801】定义字典/JSON 字段 `grasp_world_offset_x_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L1802】定义字典/JSON 字段 `grasp_world_offset_z_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L1803】定义字典/JSON 字段 `lift_mode`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lift_mode": args.lift_mode,
# 【L1804】定义字典/JSON 字段 `cartesian_lift_height_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L1805】定义字典/JSON 字段 `gripper_actuator`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "gripper_actuator": {
# 【L1806】定义字典/JSON 字段 `effort_limit_sim`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L1807】定义字典/JSON 字段 `stiffness`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "stiffness": args.gripper_stiffness,
# 【L1808】定义字典/JSON 字段 `damping`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "damping": args.gripper_damping,
# 【L1809】定义字典/JSON 字段 `close_target_rad`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "close_target_rad": args.gripper_close_target_rad,
# 【L1810】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            },
# 【L1811】定义字典/JSON 字段 `source_platform_size_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L1812】定义字典/JSON 字段 `settled_source_position_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L1813】定义字典/JSON 字段 `closed_position_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L1814】定义字典/JSON 字段 `lifted_position_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lifted_position_m": lifted_position.detach().cpu().tolist(),
# 【L1815】定义字典/JSON 字段 `block_lift_height_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "block_lift_height_m": lift_height_after_attempt,
# 【L1816】定义字典/JSON 字段 `close_left_finger_contact_force_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L1817】定义字典/JSON 字段 `close_right_finger_contact_force_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L1818】定义字典/JSON 字段 `close_contact_force_by_body_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L1819】定义字典/JSON 字段 `close_current_contact_force_by_body_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L1820】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L1821】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L1822】定义字典/JSON 字段 `closed_link_6_position_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L1823】定义字典/JSON 字段 `lifted_link_6_position_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L1824】定义字典/JSON 字段 `actual_lift_link_translation_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L1825】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L1826】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L1827】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L1828】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1829】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1830】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L1831】定义字典/JSON 字段 `reason`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
            "reason": "The block did not clear the source support after the commanded lift.",
# 【L1832】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
        }
# 【L1833】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if episode_recorder is not None:
# 【L1834】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode_recorder.metadata["task_success"] = False
# 【L1835】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode_recorder.metadata["failure_stage"] = "lift"
# 【L1836】计算并保存变量 `episode_manifest`；该值服务于“恢复重力、抬升以及抬升失败早停”。
            episode_manifest = episode_recorder.save()
# 【L1837】计算并保存变量 `episode_validation`；该值服务于“恢复重力、抬升以及抬升失败早停”。
            episode_validation = validate_episode(
# 【L1838】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                episode_recorder.output_dir, require_images=args.record_images
# 【L1839】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            )
# 【L1840】执行“恢复重力、抬升以及抬升失败早停”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            failed_lift_report["expert_episode"] = {
# 【L1841】定义字典/JSON 字段 `directory`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "directory": str(episode_recorder.output_dir),
# 【L1842】定义字典/JSON 字段 `frame_count`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "frame_count": episode_manifest["frame_count"],
# 【L1843】定义字典/JSON 字段 `validation`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "validation": episode_validation,
# 【L1844】定义字典/JSON 字段 `training_ready`；它把“恢复重力、抬升以及抬升失败早停”中的结果用稳定键名记录下来。
                "training_ready": False,
# 【L1845】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            }
# 【L1846】调用 `mkdir`：创建目录。本行位于“恢复重力、抬升以及抬升失败早停”。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1847】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“恢复重力、抬升以及抬升失败早停”。
        output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")
# 【L1848】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print(json.dumps(failed_lift_report, indent=2), flush=True)
# 【L1849】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print("RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True)
# 【L1850】结束当前函数并把结果交给调用者；这里完成“恢复重力、抬升以及抬升失败早停”的输出。
        return 1
# 【L1851】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1852】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    smooth_move(
# 【L1853】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        sim,
# 【L1854】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        robot,
# 【L1855】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        cube,
# 【L1856】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        state,
# 【L1857】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        arm_ids,
# 【L1858】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        lift_arm,
# 【L1859】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        target_lift_arm,
# 【L1860】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        360,
# 【L1861】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        "TRANSFER",
# 【L1862】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
        episode_capture,
# 【L1863】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
    )
# 【L1864】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.target_collision_enable_stage == "after_transfer":
# 【L1865】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for collision_api in target_platform_collision_apis:
# 【L1866】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1867】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if target_platform_collision_apis:
# 【L1868】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
            print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L1869】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)
# 【L1870】计算并保存变量 `pre_place_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
    pre_place_position = cube.data.root_pos_w[0].clone()
# 【L1871】计算并保存变量 `pre_place_link_6_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
    pre_place_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1872】计算并保存变量 `place_actual_arm`；该值服务于“搬运到目标并沿 IK 路点下降”。
    place_actual_arm = None
# 【L1873】计算并保存变量 `place_actual_link_6_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
    place_actual_link_6_position = None
# 【L1874】计算并保存变量 `place_commanded_link_6_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
    place_commanded_link_6_position = None
# 【L1875】计算并保存变量 `release_start_arm`；该值服务于“搬运到目标并沿 IK 路点下降”。
    release_start_arm = target_lift_arm
# 【L1876】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.place_descent:
# 【L1877】计算并保存变量 `previous_place_waypoint`；该值服务于“搬运到目标并沿 IK 路点下降”。
        previous_place_waypoint = target_lift_arm
# 【L1878】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for index, waypoint in enumerate(place_waypoints, start=1):
# 【L1879】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            smooth_move(
# 【L1880】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                sim,
# 【L1881】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                robot,
# 【L1882】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                cube,
# 【L1883】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                state,
# 【L1884】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                arm_ids,
# 【L1885】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                previous_place_waypoint,
# 【L1886】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                waypoint,
# 【L1887】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                args.place_waypoint_steps,
# 【L1888】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                f"PLACE_DESCENT_{index}",
# 【L1889】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                episode_capture,
# 【L1890】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
            )
# 【L1891】计算并保存变量 `previous_place_waypoint`；该值服务于“搬运到目标并沿 IK 路点下降”。
            previous_place_waypoint = waypoint
# 【L1892】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)
# 【L1893】计算并保存变量 `release_start_arm`；该值服务于“搬运到目标并沿 IK 路点下降”。
        release_start_arm = place_waypoints[-1]
# 【L1894】计算并保存变量 `place_actual_arm`；该值服务于“搬运到目标并沿 IK 路点下降”。
        place_actual_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1895】计算并保存变量 `place_actual_link_6_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
        place_actual_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1896】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        place_commanded_link_6_position, _ = lula.compute_forward_kinematics(
# 【L1897】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "link_6", place_waypoints[-1]
# 【L1898】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
        )
# 【L1899】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        place_commanded_link_6_position += robot_base_position
# 【L1900】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.target_collision_enable_stage == "after_place_descent":
# 【L1901】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for collision_api in target_platform_collision_apis:
# 【L1902】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1903】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if target_platform_collision_apis:
# 【L1904】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
                print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True)
# 【L1905】执行“搬运到目标并沿 IK 路点下降”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                hold(
# 【L1906】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    sim,
# 【L1907】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    robot,
# 【L1908】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    cube,
# 【L1909】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    state,
# 【L1910】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    120,
# 【L1911】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    "TARGET_COLLISION_AFTER_PLACE_HOLD",
# 【L1912】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“搬运到目标并沿 IK 路点下降”。
                    episode_capture,
# 【L1913】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
                )
# 【L1914】计算并保存变量 `pre_release_position`；该值服务于“搬运到目标并沿 IK 路点下降”。
    pre_release_position = cube.data.root_pos_w[0].clone()
# 【L1915】空行：分隔“搬运到目标并沿 IK 路点下降”中的逻辑段，让结构更容易看清。

# 【L1916】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    smooth_move(
# 【L1917】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        sim,
# 【L1918】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        robot,
# 【L1919】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        cube,
# 【L1920】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        state,
# 【L1921】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        gripper_ids,
# 【L1922】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        close_target,
# 【L1923】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        close_start,
# 【L1924】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        180,
# 【L1925】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        "OPEN",
# 【L1926】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
        episode_capture,
# 【L1927】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
    )
# 【L1928】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.unassisted_release:
# 【L1929】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print("PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True)
# 【L1930】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)
# 【L1931】计算并保存变量 `released_position`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        released_position = cube.data.root_pos_w[0].clone()
# 【L1932】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.place_descent:
# 【L1933】计算并保存变量 `retreat_place_waypoints`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
            retreat_place_waypoints = list(reversed(place_waypoints[:-1])) + [target_lift_arm]
# 【L1934】计算并保存变量 `previous_place_waypoint`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
            previous_place_waypoint = release_start_arm
# 【L1935】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for index, waypoint in enumerate(retreat_place_waypoints, start=1):
# 【L1936】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                smooth_move(
# 【L1937】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    sim,
# 【L1938】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    robot,
# 【L1939】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    cube,
# 【L1940】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    state,
# 【L1941】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    arm_ids,
# 【L1942】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    previous_place_waypoint,
# 【L1943】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    waypoint,
# 【L1944】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    60,
# 【L1945】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    f"RETREAT_{index}",
# 【L1946】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                    episode_capture,
# 【L1947】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
                )
# 【L1948】计算并保存变量 `previous_place_waypoint`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
                previous_place_waypoint = waypoint
# 【L1949】否则分支：前面的 if/elif 都不成立时执行。
        else:
# 【L1950】内部一致性断言：运行到这里时该对象必须已经存在，否则说明程序逻辑有误。
            assert release_clear_arm is not None
# 【L1951】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            smooth_move(
# 【L1952】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                sim,
# 【L1953】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                robot,
# 【L1954】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                cube,
# 【L1955】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                state,
# 【L1956】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                arm_ids,
# 【L1957】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                release_start_arm,
# 【L1958】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                release_clear_arm,
# 【L1959】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                240,
# 【L1960】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                "RETREAT",
# 【L1961】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
                episode_capture,
# 【L1962】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
            )
# 【L1963】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)
# 【L1964】计算并保存变量 `final_position`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        final_position = cube.data.root_pos_w[0].clone()
# 【L1965】否则分支：前面的 if/elif 都不成立时执行。
    else:
# 【L1966】计算并保存变量 `target_clear_arm`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        target_clear_arm = target_lift_arm.copy()
# 【L1967】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        target_clear_arm[1] -= 0.10
# 【L1968】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        target_clear_arm[2] -= 0.10
# 【L1969】计算并保存变量 `release_pose`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        release_pose = cube.data.root_state_w[:, :7].clone()
# 【L1970】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        release_pose[:, 2] -= args.release_separation_assist_m
# 【L1971】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        cube.write_root_pose_to_sim(release_pose)
# 【L1972】计算并保存变量 `release_velocity`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        release_velocity = torch.zeros_like(cube.data.root_vel_w)
# 【L1973】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        release_velocity[:, 2] = -RELEASE_DOWNWARD_SPEED_M_S
# 【L1974】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        cube.write_root_velocity_to_sim(release_velocity)
# 【L1975】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
        print("PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True)
# 【L1976】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)
# 【L1977】计算并保存变量 `released_position`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        released_position = cube.data.root_pos_w[0].clone()
# 【L1978】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        smooth_move(
# 【L1979】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            sim,
# 【L1980】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            robot,
# 【L1981】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            cube,
# 【L1982】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            state,
# 【L1983】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            arm_ids,
# 【L1984】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            target_lift_arm,
# 【L1985】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            target_clear_arm,
# 【L1986】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            240,
# 【L1987】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            "RETREAT",
# 【L1988】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“张开夹爪、自然释放、撤退和稳定等待”。
            episode_capture,
# 【L1989】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
        )
# 【L1990】执行“张开夹爪、自然释放、撤退和稳定等待”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)
# 【L1991】计算并保存变量 `final_position`；该值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        final_position = cube.data.root_pos_w[0].clone()
# 【L1992】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L1993】计算并保存变量 `settled_source_np`；该值服务于“计算成功指标并保存专家 episode”。
    settled_source_np = settled_source_position.detach().cpu().numpy()
# 【L1994】计算并保存变量 `closed_np`；该值服务于“计算成功指标并保存专家 episode”。
    closed_np = closed_position.detach().cpu().numpy()
# 【L1995】计算并保存变量 `lifted_np`；该值服务于“计算成功指标并保存专家 episode”。
    lifted_np = lifted_position.detach().cpu().numpy()
# 【L1996】计算并保存变量 `pre_release_np`；该值服务于“计算成功指标并保存专家 episode”。
    pre_release_np = pre_release_position.detach().cpu().numpy()
# 【L1997】计算并保存变量 `released_np`；该值服务于“计算成功指标并保存专家 episode”。
    released_np = released_position.detach().cpu().numpy()
# 【L1998】计算并保存变量 `final_np`；该值服务于“计算成功指标并保存专家 episode”。
    final_np = final_position.detach().cpu().numpy()
# 【L1999】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“计算成功指标并保存专家 episode”。
    source_to_target_distance = float(np.linalg.norm(target_block_position[:2] - source_block_position[:2]))
# 【L2000】计算并保存变量 `lift_height`；该值服务于“计算成功指标并保存专家 episode”。
    lift_height = float(lifted_np[2] - closed_np[2])
# 【L2001】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“计算成功指标并保存专家 episode”。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L2002】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“计算成功指标并保存专家 episode”。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L2003】调用 `np.linalg.norm`：计算向量长度/欧氏距离。本行位于“计算成功指标并保存专家 episode”。
    release_drift = float(np.linalg.norm(final_np - released_np))
# 【L2004】计算并保存变量 `final_l2_tip_gap`；该值服务于“计算成功指标并保存专家 episode”。
    final_l2_tip_gap = float(
# 【L2005】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        torch.linalg.vector_norm(
# 【L2006】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L2007】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2008】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2009】计算并保存变量 `all_states_finite`；该值服务于“计算成功指标并保存专家 episode”。
    all_states_finite = bool(
# 【L2010】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        torch.isfinite(robot.data.joint_pos).all().item()
# 【L2011】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and torch.isfinite(cube.data.root_state_w).all().item()
# 【L2012】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2013】计算并保存变量 `passed`；该值服务于“计算成功指标并保存专家 episode”。
    passed = (
# 【L2014】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        all_states_finite
# 【L2015】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and source_to_target_distance > 0.12
# 【L2016】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and lift_height > 0.02
# 【L2017】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and final_target_xy_error < 0.05
# 【L2018】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and final_target_position_error < 0.05
# 【L2019】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and release_drift < 0.02
# 【L2020】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12
# 【L2021】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and final_l2_tip_gap > 0.06
# 【L2022】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2023】计算并保存变量 `unassisted_full_task_complete`；该值服务于“计算成功指标并保存专家 episode”。
    unassisted_full_task_complete = bool(
# 【L2024】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        passed
# 【L2025】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and args.unassisted_release
# 【L2026】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and args.place_descent
# 【L2027】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and args.natural_source_gravity
# 【L2028】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and args.enable_moving_gripper_gravity
# 【L2029】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and not args.collision_bypass_during_approach
# 【L2030】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and not args.initialize_at_grasp
# 【L2031】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and not args.disable_arm_gravity_during_approach
# 【L2032】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        and not args.disable_arm_gravity_through_transport
# 【L2033】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2034】计算并保存变量 `expert_episode_report`；该值服务于“计算成功指标并保存专家 episode”。
    expert_episode_report = None
# 【L2035】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if episode_recorder is not None:
# 【L2036】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        episode_recorder.metadata["task_success"] = passed
# 【L2037】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        episode_recorder.metadata[
# 【L2038】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "unassisted_full_task_complete"
# 【L2039】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ] = unassisted_full_task_complete
# 【L2040】计算并保存变量 `episode_manifest`；该值服务于“计算成功指标并保存专家 episode”。
        episode_manifest = episode_recorder.save()
# 【L2041】计算并保存变量 `episode_validation`；该值服务于“计算成功指标并保存专家 episode”。
        episode_validation = validate_episode(
# 【L2042】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            episode_recorder.output_dir, require_images=args.record_images
# 【L2043】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2044】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if episode_validation["status"] != "pass":
# 【L2045】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed validation: {episode_validation}")
# 【L2046】计算并保存变量 `expert_episode_report`；该值服务于“计算成功指标并保存专家 episode”。
        expert_episode_report = {
# 【L2047】定义字典/JSON 字段 `directory`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "directory": str(episode_recorder.output_dir),
# 【L2048】定义字典/JSON 字段 `format`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "format": episode_manifest["format"],
# 【L2049】定义字典/JSON 字段 `frame_count`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "frame_count": episode_manifest["frame_count"],
# 【L2050】定义字典/JSON 字段 `control_hz`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "control_hz": episode_manifest["control_hz"],
# 【L2051】定义字典/JSON 字段 `validation`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "validation": episode_validation,
# 【L2052】定义字典/JSON 字段 `training_ready`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "training_ready": bool(passed and args.record_images),
# 【L2053】定义字典/JSON 字段 `training_blocker`；它把“计算成功指标并保存专家 episode”中的结果用稳定键名记录下来。
            "training_blocker": (
# 【L2054】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                None
# 【L2055】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if args.record_images
# 【L2056】执行“计算成功指标并保存专家 episode”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                else "external and wrist RGB streams were not recorded"
# 【L2057】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
            ),
# 【L2058】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        }
# 【L2059】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L2060】定义字典/JSON 字段 `status`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "status": "pass" if passed else "fail",
# 【L2061】定义字典/JSON 字段 `simulation_only`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "simulation_only": True,
# 【L2062】定义字典/JSON 字段 `pi05_used`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "pi05_used": False,
# 【L2063】定义字典/JSON 字段 `expert`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "expert": (
# 【L2064】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            "scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"
# 【L2065】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if args.initialize_at_grasp
# 【L2066】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else "scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"
# 【L2067】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2068】定义字典/JSON 字段 `task`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "task": (
# 【L2069】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“写出完整机器可读报告”。
            (
# 【L2070】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                "approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"
# 【L2071】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
                if args.place_descent
# 【L2072】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                else "approach, close, lift, transfer, unassisted release, and vertical clearance"
# 【L2073】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
            )
# 【L2074】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if args.unassisted_release
# 【L2075】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else "approach, close, lift, transfer, assisted release onto a platform, and retreat"
# 【L2076】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2077】定义字典/JSON 字段 `real_robot_command_sent`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "real_robot_command_sent": False,
# 【L2078】定义字典/JSON 字段 `expert_episode`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "expert_episode": expert_episode_report,
# 【L2079】定义字典/JSON 字段 `unassisted_full_task_complete`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "unassisted_full_task_complete": unassisted_full_task_complete,
# 【L2080】定义字典/JSON 字段 `transfer_joint_1_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L2081】定义字典/JSON 字段 `collision_bypass_during_approach`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L2082】定义字典/JSON 字段 `initialized_at_grasp`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "initialized_at_grasp": args.initialize_at_grasp,
# 【L2083】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2084】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2085】定义字典/JSON 字段 `natural_source_gravity`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "natural_source_gravity": args.natural_source_gravity,
# 【L2086】定义字典/JSON 字段 `arm_actuator`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "arm_actuator": {
# 【L2087】定义字典/JSON 字段 `effort_limit_sim`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "effort_limit_sim": args.arm_effort_limit_sim,
# 【L2088】定义字典/JSON 字段 `stiffness`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "stiffness": args.arm_stiffness,
# 【L2089】定义字典/JSON 字段 `damping`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "damping": args.arm_damping,
# 【L2090】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2091】定义字典/JSON 字段 `gripper_actuator`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "gripper_actuator": {
# 【L2092】定义字典/JSON 字段 `effort_limit_sim`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L2093】定义字典/JSON 字段 `stiffness`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "stiffness": args.gripper_stiffness,
# 【L2094】定义字典/JSON 字段 `damping`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "damping": args.gripper_damping,
# 【L2095】定义字典/JSON 字段 `close_target_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "close_target_rad": args.gripper_close_target_rad,
# 【L2096】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2097】定义字典/JSON 字段 `requested_pregrasp_distance_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L2098】定义字典/JSON 字段 `pregrasp_distance_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L2099】定义字典/JSON 字段 `grasp_world_offset_x_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L2100】定义字典/JSON 字段 `grasp_world_offset_z_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L2101】定义字典/JSON 字段 `robot_base_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "robot_base_position_m": robot_base_position.tolist(),
# 【L2102】定义字典/JSON 字段 `grasp_orientation_mode`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L2103】定义字典/JSON 字段 `top_down_yaw_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L2104】定义字典/JSON 字段 `top_down_tilt_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L2105】定义字典/JSON 字段 `top_down_ik_multistart`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L2106】定义字典/JSON 字段 `top_down_ik_seed_index`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L2107】定义字典/JSON 字段 `top_down_blend`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "top_down_blend": args.top_down_blend,
# 【L2108】定义字典/JSON 字段 `reference_block_from_link_local_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L2109】定义字典/JSON 字段 `lift_mode`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lift_mode": args.lift_mode,
# 【L2110】定义字典/JSON 字段 `cartesian_lift_height_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L2111】定义字典/JSON 字段 `development_assistance`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "development_assistance": {
# 【L2112】定义字典/JSON 字段 `initialized_at_grasp`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L2113】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2114】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2115】定义字典/JSON 字段 `source_block_gravity_disabled_until_close`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "source_block_gravity_disabled_until_close": not args.natural_source_gravity,
# 【L2116】定义字典/JSON 字段 `target_platform_collision_enable_stage`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "target_platform_collision_enable_stage": args.target_collision_enable_stage,
# 【L2117】定义字典/JSON 字段 `release_separation_assist_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2118】定义字典/JSON 字段 `release_downward_speed_assist_m_s`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2119】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2120】定义字典/JSON 字段 `block_mass_kg`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "block_mass_kg": BLOCK_MASS_KG,
# 【L2121】定义字典/JSON 字段 `block_size_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "block_size_m": list(BLOCK_SIZE),
# 【L2122】定义字典/JSON 字段 `moving_gripper_gravity_disabled`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L2123】定义字典/JSON 字段 `gravity_disabled_body_paths`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "gravity_disabled_body_paths": isolated_paths,
# 【L2124】定义字典/JSON 字段 `source_block_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_block_position_m": source_block_position.tolist(),
# 【L2125】定义字典/JSON 字段 `source_offset_xy_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L2126】定义字典/JSON 字段 `target_block_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_block_position_m": target_block_position.tolist(),
# 【L2127】定义字典/JSON 字段 `expected_lift_translation_from_fk_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "expected_lift_translation_from_fk_m": expected_lift_translation.tolist(),
# 【L2128】定义字典/JSON 字段 `expected_source_lift_block_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "expected_source_lift_block_position_m": expected_source_lift_block_position.tolist(),
# 【L2129】定义字典/JSON 字段 `expected_release_position_before_drop_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "expected_release_position_before_drop_m": target_release_position.tolist(),
# 【L2130】定义字典/JSON 字段 `source_block_quaternion_wxyz`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_block_quaternion_wxyz": source_block_quaternion.tolist(),
# 【L2131】定义字典/JSON 字段 `target_block_quaternion_wxyz`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_block_quaternion_wxyz": target_block_quaternion.tolist(),
# 【L2132】定义字典/JSON 字段 `source_block_temporarily_gravity_disabled`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_block_temporarily_gravity_disabled": not args.natural_source_gravity,
# 【L2133】定义字典/JSON 字段 `source_platform_size_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L2134】定义字典/JSON 字段 `gravity_enabled_after_gripper_close`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "gravity_enabled_after_gripper_close": True,
# 【L2135】定义字典/JSON 字段 `target_platform_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_platform_position_m": target_platform_position.tolist(),
# 【L2136】定义字典/JSON 字段 `target_platform_size_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_platform_size_m": list(target_platform_size),
# 【L2137】定义字典/JSON 字段 `target_support_mode`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_support_mode": args.target_support_mode,
# 【L2138】定义字典/JSON 字段 `target_platform_quaternion_wxyz`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_platform_quaternion_wxyz": (
# 【L2139】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            list(target_platform_orientation) if target_platform_orientation is not None else None
# 【L2140】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2141】定义字典/JSON 字段 `target_platform_collision_enabled_after_transfer`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_platform_collision_enabled_after_transfer": (
# 【L2142】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            args.target_collision_enable_stage == "after_transfer"
# 【L2143】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2144】定义字典/JSON 字段 `target_collision_enable_stage`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "target_collision_enable_stage": args.target_collision_enable_stage,
# 【L2145】定义字典/JSON 字段 `release_unassisted`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "release_unassisted": args.unassisted_release,
# 【L2146】定义字典/JSON 字段 `place_descent`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_descent": args.place_descent,
# 【L2147】定义字典/JSON 字段 `place_descent_distance_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_descent_distance_m": args.place_descent_distance_m if args.place_descent else None,
# 【L2148】定义字典/JSON 字段 `place_waypoint_steps`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_waypoint_steps": args.place_waypoint_steps if args.place_descent else None,
# 【L2149】定义字典/JSON 字段 `place_max_command_step_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_max_command_step_rad": place_max_command_step_rad,
# 【L2150】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_ik_uses_base_rotation_symmetry": True,
# 【L2151】定义字典/JSON 字段 `pre_place_block_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "pre_place_block_position_m": pre_place_position.detach().cpu().tolist(),
# 【L2152】定义字典/JSON 字段 `pre_place_link_6_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "pre_place_link_6_position_m": pre_place_link_6_position.detach().cpu().tolist(),
# 【L2153】定义字典/JSON 字段 `place_actual_block_translation_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_actual_block_translation_m": (
# 【L2154】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“写出完整机器可读报告”。
            (pre_release_position - pre_place_position).detach().cpu().tolist()
# 【L2155】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if args.place_descent
# 【L2156】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else None
# 【L2157】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2158】定义字典/JSON 字段 `place_actual_link_6_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_actual_link_6_position_m": (
# 【L2159】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            place_actual_link_6_position.detach().cpu().tolist()
# 【L2160】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if place_actual_link_6_position is not None
# 【L2161】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else None
# 【L2162】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2163】定义字典/JSON 字段 `place_commanded_link_6_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_commanded_link_6_position_m": (
# 【L2164】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            place_commanded_link_6_position.tolist()
# 【L2165】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if place_commanded_link_6_position is not None
# 【L2166】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else None
# 【L2167】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2168】定义字典/JSON 字段 `place_actual_link_translation_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_actual_link_translation_m": (
# 【L2169】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“写出完整机器可读报告”。
            (place_actual_link_6_position - pre_place_link_6_position).detach().cpu().tolist()
# 【L2170】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if place_actual_link_6_position is not None
# 【L2171】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else None
# 【L2172】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2173】定义字典/JSON 字段 `place_max_arm_joint_error_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "place_max_arm_joint_error_rad": (
# 【L2174】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            float(np.max(np.abs(place_actual_arm - place_waypoints[-1])))
# 【L2175】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if place_actual_arm is not None
# 【L2176】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            else None
# 【L2177】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2178】定义字典/JSON 字段 `release_clearance_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "release_clearance_m": (
# 【L2179】执行“写出完整机器可读报告”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            args.release_clearance_m if args.unassisted_release and not args.place_descent else None
# 【L2180】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2181】定义字典/JSON 字段 `release_downward_speed_assist_m_s`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2182】定义字典/JSON 字段 `release_separation_assist_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2183】定义字典/JSON 字段 `cartesian_retreat_distances_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L2184】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L2185】定义字典/JSON 字段 `settled_source_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "settled_source_position_m": settled_source_np.tolist(),
# 【L2186】定义字典/JSON 字段 `settled_source_quaternion_wxyz`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L2187】定义字典/JSON 字段 `closed_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_position_m": closed_np.tolist(),
# 【L2188】定义字典/JSON 字段 `lifted_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lifted_position_m": lifted_np.tolist(),
# 【L2189】定义字典/JSON 字段 `pre_release_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "pre_release_position_m": pre_release_np.tolist(),
# 【L2190】定义字典/JSON 字段 `released_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "released_position_m": released_np.tolist(),
# 【L2191】定义字典/JSON 字段 `final_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "final_position_m": final_np.tolist(),
# 【L2192】定义字典/JSON 字段 `source_to_target_xy_distance_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L2193】定义字典/JSON 字段 `block_lift_height_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "block_lift_height_m": lift_height,
# 【L2194】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L2195】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L2196】定义字典/JSON 字段 `approach_l2_midpoint_world_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L2197】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L2198】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L2199】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L2200】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L2201】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L2202】定义字典/JSON 字段 `closed_l2_tip_gap_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_l2_tip_gap_m": closed_l2_gap,
# 【L2203】定义字典/JSON 字段 `closed_gripper_joint_position_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L2204】定义字典/JSON 字段 `close_left_finger_contact_force_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L2205】定义字典/JSON 字段 `close_right_finger_contact_force_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L2206】定义字典/JSON 字段 `close_contact_force_by_body_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L2207】定义字典/JSON 字段 `close_current_contact_force_by_body_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2208】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2209】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2210】定义字典/JSON 字段 `closed_link_6_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L2211】定义字典/JSON 字段 `lifted_link_6_position_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L2212】定义字典/JSON 字段 `actual_lift_link_translation_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L2213】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L2214】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L2215】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L2216】定义字典/JSON 字段 `final_target_xy_error_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "final_target_xy_error_m": final_target_xy_error,
# 【L2217】定义字典/JSON 字段 `final_target_position_error_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "final_target_position_error_m": final_target_position_error,
# 【L2218】定义字典/JSON 字段 `post_release_drift_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "post_release_drift_m": release_drift,
# 【L2219】定义字典/JSON 字段 `final_l2_tip_gap_m`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "final_l2_tip_gap_m": final_l2_tip_gap,
# 【L2220】定义字典/JSON 字段 `final_gripper_joint_position_rad`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "final_gripper_joint_position_rad": robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist(),
# 【L2221】定义字典/JSON 字段 `all_states_finite`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "all_states_finite": all_states_finite,
# 【L2222】定义字典/JSON 字段 `criteria`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "criteria": {
# 【L2223】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L2224】定义字典/JSON 字段 `block_lift_height_m_gt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "block_lift_height_m_gt": 0.02,
# 【L2225】定义字典/JSON 字段 `final_target_xy_error_m_lt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "final_target_xy_error_m_lt": 0.05,
# 【L2226】定义字典/JSON 字段 `final_target_position_error_m_lt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "final_target_position_error_m_lt": 0.05,
# 【L2227】定义字典/JSON 字段 `post_release_drift_m_lt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "post_release_drift_m_lt": 0.02,
# 【L2228】定义字典/JSON 字段 `final_gripper_joint_position_rad_lt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "final_gripper_joint_position_rad_lt": 0.12,
# 【L2229】定义字典/JSON 字段 `final_l2_tip_gap_m_gt`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
            "final_l2_tip_gap_m_gt": 0.06,
# 【L2230】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2231】定义字典/JSON 字段 `limitation`；它把“写出完整机器可读报告”中的结果用稳定键名记录下来。
        "limitation": "The collision pads and scripted waypoints still require physical calibration.",
# 【L2232】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
    }
# 【L2233】调用 `mkdir`：创建目录。本行位于“写出完整机器可读报告”。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L2234】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“写出完整机器可读报告”。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L2235】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(report, indent=2), flush=True)
# 【L2236】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
# 【L2237】结束当前函数并把结果交给调用者；这里完成“写出完整机器可读报告”的输出。
    return 0 if passed else 1
# 【L2238】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L2239】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L2240】开始可能失败的操作块，后面由 except/finally 负责错误或清理。
try:
# 【L2241】计算并保存变量 `exit_code`；该值服务于“捕获异常、关闭 Isaac Sim、返回退出码”。
    exit_code = main()
# 【L2242】捕获指定异常，把可预期失败转换成清晰错误或重试逻辑。
except BaseException:
# 【L2243】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print("PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True)
# 【L2244】执行“捕获异常、关闭 Isaac Sim、返回退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    traceback.print_exc()
# 【L2245】执行“捕获异常、关闭 Isaac Sim、返回退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    raise
# 【L2246】清理块：无论前面成功还是抛错都执行，常用于关闭服务和 Isaac Sim。
finally:
# 【L2247】执行“捕获异常、关闭 Isaac Sim、返回退出码”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    simulation_app.close(skip_cleanup=True)
# 【L2248】空行：分隔“捕获异常、关闭 Isaac Sim、返回退出码”中的逻辑段，让结构更容易看清。

# 【L2249】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
raise SystemExit(exit_code)
```
