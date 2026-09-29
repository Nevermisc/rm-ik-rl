# `run_pick_place_baseline.py` 模块化零基础导读与逐行注释

> 这是学习副本，不参与项目运行。它把同一份生产源码按模块重新排版；生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/run_pick_place_baseline.py`
- 对应源码提交：`0cd249e153b43ab880f3571d286013cadaf7331a`
- 生成快照时源码是否有未提交修改：`False`
- 快照 SHA-256：`b13981361fb8f254d94b08f33619ae2bfd0be99d4404c19c1cbeddea59554014`
- 总行数：2609

## 1. 先把这个程序放进整个项目

- 所处阶段：仿真核心：场景、IK、脚本专家、数据采集与 π0.5 闭环共用入口。
- 输入：USD/URDF、Lula 描述、任务参数、相机、可选 policy server 和控制参数。
- 输出：仿真轨迹、图像、task_report、接触/IK/闭环诊断和成功证据。
- 一句话作用：RM65 仿真的主程序：创建场景、求 IK、运行脚本专家、记录数据，也可切换为 π0.5 WebSocket 闭环。

### 为什么要写它

- 原先的问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。
- 采用的解决办法：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

## 2. 本文件出现的基础概念

- **dict**：字典：用键查找值，例如 `data["actions"]`。适合保存一条样本中名称不同的字段。
- **tuple**：元组：有顺序、创建后不修改的一组值，例如六个关节名称。可以混合类型，不等同于 NumPy 数组。
- **list**：列表：有顺序且可增删的一组 Python 对象，常用 `append` 逐帧积累结果。
- **ndarray**：NumPy ndarray：带 shape/dtype 的多维数值数组，用于图像、关节、动作和统计计算。
- **Tensor**：Torch Tensor：可位于 CPU/GPU 的数值张量；IsaacLab 用它保存批量仿真状态和控制目标。
- **Path**：pathlib.Path：把文件路径当对象处理，使用 `/` 拼接目录，并提供 exists/read_text 等方法。
- **argparse**：命令行参数解析：把 `--checkpoint` 等启动选项转换成 `args.checkpoint` 字段。
- **JSON**：JSON：只含通用键值、列表、数字和字符串的文本格式；用于计划、metadata 和报告证据。
- **WebSocket**：WebSocket：保持连接的双向网络协议；IsaacLab 客户端用它向独立 OpenPI 进程请求动作。
- **URDF**：URDF：XML 机器人描述，记录 link、joint、几何、质量、惯量和父子关系。
- **USD**：USD：Isaac Sim 原生场景/资产格式，承载已导入的 articulation 和物理属性。

## 3. 有证据的修订日志

下面只复述 Git 中确实修改过这个文件的提交。某个问题是否完全解决，还要看对应测试/报告，不能只凭提交标题判断。

- `2026-09-19` `f18f8ca8` **Fix Isaac websocket compatibility and enforce task reports**：修复 Isaac/OpenPI WebSocket 版本兼容，并要求机器可读任务报告。
- `2026-09-19` `aff560c8` **Latch verified RM65 release postcondition**：释放条件连续满足后锁存验证状态，减少瞬时抖动造成假成功。
- `2026-09-19` `66429003` **Record RM65 pi0.5 v1 evaluation and harden camera startup**：记录 v1 评测并增强相机启动检查。
- `2026-09-19` `10e444f5` **Record RM65 closed-loop controller settings**：把闭环控制参数写入证据，避免结果无法复现。
- `2026-09-19` `66d5d71b` **Calibrate RM65 simulated release verification**：校准仿真松爪阈值和释放成功判定。
- `2026-09-28` `203c9b9b` **Make RM65 pi0.5 sampling deterministic**：固定随机采样与观测证据，解决相同输入难以复现的问题。
- `2026-09-28` `5d113153` **Seed RM65 simulation and diagnose camera divergence**：固定仿真种子并诊断相机观测分歧。
- `2026-09-28` `009b15d1` **Improve RM65 pi0.5 release supervision**：增强释放阶段监督，针对到位后不可靠松爪。
- `2026-09-28` `98de4494` **Fail closed on incomplete RM65 evaluation reports**：报告不完整时按失败处理，避免缺字段被误判通过。
- `2026-09-28` `c707b7d4` **Skip unused scripted IK in RM65 pi0.5 evaluation**：π0.5 评测时跳过不用的脚本 IK，减少前置故障干扰。
- `2026-09-28` `4427a005` **Capture exact RM65 pi0.5 policy observation evidence**：保存实际送入 policy 的观测证据，便于比较相同输入。
- `2026-09-28` `0264302f` **Record RM65 pi0.5 repeatability gate**：加入重复性 gate，单次偶然成功不再足够。
- `2026-09-28` `41b85834` **Handle scripted expert preflight failures**：显式处理脚本专家预检失败并保留失败阶段。
- `2026-09-29` `79e66ceb` **Complete RM65 v3 training and harden evaluation provenance**：完成 v3 训练并强化评测来源链。
- `2026-09-29` `dd084c3b` **Preserve RM65 formal failure provenance**：正式失败也完整保留 checkpoint、观测和阶段来源。

### 与上一版教学快照的源码差异

- 当前第 9-9 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`import os`
- 当前第 155-155 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`parser.add_argument("--policy-max-action-chunks", type=int, default=80)` 当前代码摘录：`parser.add_argument("--policy-max-action-chunks", type=int, default=120)`
- 当前第 167-176 行相对旧教学快照发生 `insert`：旧版 0 行，当前 10 行。 当前代码摘录：`"--policy-gripper-actual-open-threshold",` / `type=float,` / `default=0.20,` / `help=(`
- 当前第 180-200 行相对旧教学快照发生 `insert`：旧版 0 行，当前 21 行。 当前代码摘录：`)` / `parser.add_argument(` / `"--policy-noise-seed",` / `type=int,`
- 当前第 206-220 行相对旧教学快照发生 `insert`：旧版 0 行，当前 15 行。 当前代码摘录：`if not args.policy_gripper_open_threshold <= args.policy_gripper_actual_open_threshold < 1.0:` / `parser.error(` / `"--policy-gripper-actual-open-threshold must be at least the policy target "` / `"threshold and below 1"`
- 当前第 227-228 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`import omni.usd  # noqa: E402` / `import omni.replicator.core as replicator  # noqa: E402`

## 4. 模块地图

- 模块 1｜第 1-20 行：启动说明、项目路径与 AppLauncher
- 模块 2｜第 21-223 行：命令行参数；它们是实验可重复性的外部控制面板
- 模块 3｜第 224-268 行：启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API
- 模块 4｜第 269-310 行：RM65 关节、物体尺寸、接触点和关节限位常量
- 模块 5｜第 311-351 行：旋转、四元数和旋转距离的数学工具
- 模块 6｜第 352-465 行：选择连续 IK 分支并规划不跳变的笛卡尔路径
- 模块 7｜第 466-488 行：把 link 局部点转换到世界坐标
- 模块 8｜第 489-630 行：从仿真同步采样状态、动作、外部/腕部相机图像
- 模块 9｜第 631-683 行：平滑移动和保持姿态的物理步进器
- 模块 10｜第 684-1185 行：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环
- 模块 11｜第 1186-1226 行：接触力统计与平台生成工具
- 模块 12｜第 1227-1289 行：主函数输入文件和参数范围校验
- 模块 13｜第 1290-1596 行：根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK
- 模块 14｜第 1597-1795 行：创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器
- 模块 15｜第 1796-1862 行：reset、关节索引和 episode 记录器初始化
- 模块 16｜第 1863-1905 行：写入初始状态；选择脚本专家或 π0.5 分支
- 模块 17｜第 1906-2102 行：脚本专家的接近、闭合夹爪和接触诊断
- 模块 18｜第 2103-2179 行：恢复重力、抬升以及抬升失败早停
- 模块 19｜第 2180-2243 行：搬运到目标并沿 IK 路点下降
- 模块 20｜第 2244-2320 行：张开夹爪、自然释放、撤退和稳定等待
- 模块 21｜第 2321-2386 行：计算成功指标并保存专家 episode
- 模块 22｜第 2387-2567 行：写出完整机器可读报告
- 模块 23｜第 2568-2609 行：捕获异常、关闭 Isaac Sim、返回退出码

### 函数/类快速索引

- `class UnsafeIKBranchJumpError`：第 299-300 行
- `rotate_about_z()`：第 311-316 行
- `quaternion_multiply_wxyz()`：第 319-330 行
- `quaternion_to_matrix_wxyz()`：第 333-342 行
- `rotation_distance_rad()`：第 345-349 行
- `closest_equivalent_rm65_solution()`：第 352-403 行
- `require_continuous_joint_step()`：第 406-417 行
- `solve_continuous_cartesian_path()`：第 420-463 行
- `tip_world_position()`：第 466-471 行
- `body_world_position()`：第 474-476 行
- `local_point_world_position()`：第 479-486 行
- `class ExpertEpisodeCapture`：第 489-628 行
  - `ExpertEpisodeCapture.__init__()`：第 492-519 行
  - `ExpertEpisodeCapture._rgb()`：第 522-526 行
  - `ExpertEpisodeCapture._image_ready()`：第 529-537 行
  - `ExpertEpisodeCapture._render_images()`：第 539-588 行
  - `ExpertEpisodeCapture.before_step()`：第 590-628 行
- `smooth_move()`：第 631-659 行
- `hold()`：第 662-681 行
- `run_pi05_closed_loop()`：第 684-1183 行
- `contact_force_statistics()`：第 1186-1200 行
- `spawn_platform()`：第 1203-1224 行
- `main()`：第 1227-2565 行

## 5. 按模块精读源码

阅读顺序固定为：先看模块为什么存在和数据怎样流动，再看新函数/API，最后逐行看语法与项目含义。这样不会把代码读成互不相干的句子。

## 模块 1：启动说明、项目路径与 AppLauncher（源码第 1-20 行）

### 5.A 数据流位置

- 上游：命令行/上游文件或调用者。
- 本模块：启动说明、项目路径与 AppLauncher。
- 下游：处理结果继续交给模块 2“命令行参数；它们是实验可重复性的外部控制面板”。

### 5.B 为什么需要这一组代码

这一组负责“启动说明、项目路径与 AppLauncher”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.D 本模块首次阅读要认识的调用

- `Path(...)`：圆括号表示真正执行调用；创建路径对象。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `sys.path.insert(...)`：圆括号表示真正执行调用；把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。

### 5.F 这一模块的版本变化

- 当前第 9-9 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`import os`

### 5.G 逐行精读

```python
# 【L0001】语法拆解：`#!` 是 Linux 的 shebang 标记；后面的路径指定直接运行脚本时使用哪个解释器。
# 【项目含义】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab."""
# 【L0003】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0004】语法拆解：`from __future__` 指定来源模块；`import annotations` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0006】语法拆解：`import` 加载模块；`argparse` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】语法拆解：`import` 加载模块；`itertools` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `itertools` 引入 `itertools`。在这份程序里，`itertools` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import itertools
# 【L0008】语法拆解：`import` 加载模块；`json` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0009】语法拆解：`import` 加载模块；`os` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `os` 引入 `os`。在这份程序里，`os` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import os
# 【L0010】语法拆解：`import` 加载模块；`sys` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `sys` 引入 `sys`。在这份程序里，`sys` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import sys
# 【L0011】语法拆解：`import` 加载模块；`traceback` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `traceback` 引入 `traceback`。在这份程序里，`traceback` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import traceback
# 【L0012】语法拆解：`from pathlib` 指定来源模块；`import Path` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0013】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PROJECT_ROOT`。右侧语法为：`Path(__file__).resolve().parents[1]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PROJECT_ROOT`，它在本项目中表示004-rm65-4c2-isaaclab 项目根目录；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(__file__).resolve().parents[1]`；`__file__` 表示本功能块中的 `__file__` 值；`resolve` 表示本功能块中的 `resolve` 值；`parents` 表示本功能块中的 `parents` 值。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 【L0015】语法拆解：`if` 要求条件 `str(PROJECT_ROOT) not in sys.path` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(PROJECT_ROOT) not in sys.path` 是否成立；`PROJECT_ROOT` 表示004-rm65-4c2-isaaclab 项目根目录；`sys` 表示本功能块中的 `sys` 值；`path` 表示路径相关值
if str(PROJECT_ROOT) not in sys.path:
# 【L0016】语法拆解：`sys.path` 是模块/对象，点号 `.` 从中取出 `insert` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0`；第 2 个实参 `str(PROJECT_ROOT)`。
# 【项目含义】对 `sys.path` 调用 `insert(0, str(PROJECT_ROOT))`：把元素插入指定位置；对 `sys.path` 而言是让项目模块优先被 Python 找到。本行产生的修改/返回值服务于“启动说明、项目路径与 AppLauncher”。
    sys.path.insert(0, str(PROJECT_ROOT))
# 【L0017】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0018】语法拆解：`from isaaclab.app` 指定来源模块；`import AppLauncher` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `AppLauncher`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.app import AppLauncher
# 【L0019】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

# 【L0020】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动说明、项目路径与 AppLauncher”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“启动说明、项目路径与 AppLauncher”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 2：命令行参数；它们是实验可重复性的外部控制面板（源码第 21-223 行）

### 5.A 数据流位置

- 上游：模块 1“启动说明、项目路径与 AppLauncher”。
- 本模块：命令行参数；它们是实验可重复性的外部控制面板。
- 下游：处理结果继续交给模块 3“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。

### 5.B 为什么需要这一组代码

这一组负责“命令行参数；它们是实验可重复性的外部控制面板”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `report`：机器可读实验报告字典。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `checkpoint`：一次训练保存的模型参数目录。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `output`：输出文件路径。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `current`：float32 格式的当前六关节角。

### 5.D 本模块首次阅读要认识的调用

- `argparse.ArgumentParser(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.add_argument(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `grasp(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `pose(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `steps(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `AppLauncher.add_app_launcher_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.parse_args(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `parser.error(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `AppLauncher(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 155-155 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`parser.add_argument("--policy-max-action-chunks", type=int, default=80)` 当前代码摘录：`parser.add_argument("--policy-max-action-chunks", type=int, default=120)`
- 当前第 167-176 行相对旧教学快照发生 `insert`：旧版 0 行，当前 10 行。 当前代码摘录：`"--policy-gripper-actual-open-threshold",` / `type=float,` / `default=0.20,` / `help=(`
- 当前第 180-200 行相对旧教学快照发生 `insert`：旧版 0 行，当前 21 行。 当前代码摘录：`)` / `parser.add_argument(` / `"--policy-noise-seed",` / `type=int,`
- 当前第 206-220 行相对旧教学快照发生 `insert`：旧版 0 行，当前 15 行。 当前代码摘录：`if not args.policy_gripper_open_threshold <= args.policy_gripper_actual_open_threshold < 1.0:` / `parser.error(` / `"--policy-gripper-actual-open-threshold must be at least the policy target "` / `"threshold and below 1"`

### 5.G 逐行精读

```python
# 【L0021】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `parser`。右侧语法为：`argparse` 是模块/对象，点号 `.` 从中取出 `ArgumentParser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `description=__doc__`。
# 【项目含义】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
parser = argparse.ArgumentParser(description=__doc__)
# 【L0022】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--usd"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--usd`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--usd", type=Path, required=True)
# 【L0023】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--urdf"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--urdf`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--urdf", type=Path, required=True)
# 【L0024】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--description"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--description`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--description", type=Path, required=True)
# 【L0025】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--output"`；第 2 个实参 `type=Path`；第 3 个实参 `required=True`。
# 【项目含义】声明命令行参数 `--output`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--output", type=Path, required=True)
# 【L0026】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--transfer-joint-1-rad"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.8`。
# 【项目含义】声明命令行参数 `--transfer-joint-1-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--transfer-joint-1-rad", type=float, default=0.8)
# 【L0027】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0028】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--robot-base-z-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--robot-base-z-m",
# 【L0029】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0030】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0031】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"World height of the robot mounting plane; Lula targets remain in the robot base frame."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"World height of the robot mounting plane; Lula targets remain in the robot base frame."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="World height of the robot mounting plane; Lula targets remain in the robot base frame.",
# 【L0032】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0033】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--arm-effort-limit-sim"`；第 2 个实参 `type=float`；第 3 个实参 `default=300.0`。
# 【项目含义】声明命令行参数 `--arm-effort-limit-sim`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-effort-limit-sim", type=float, default=300.0)
# 【L0034】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--arm-stiffness"`；第 2 个实参 `type=float`；第 3 个实参 `default=1000.0`。
# 【项目含义】声明命令行参数 `--arm-stiffness`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-stiffness", type=float, default=1000.0)
# 【L0035】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--arm-damping"`；第 2 个实参 `type=float`；第 3 个实参 `default=100.0`。
# 【项目含义】声明命令行参数 `--arm-damping`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--arm-damping", type=float, default=100.0)
# 【L0036】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--gripper-effort-limit-sim"`；第 2 个实参 `type=float`；第 3 个实参 `default=20.0`。
# 【项目含义】声明命令行参数 `--gripper-effort-limit-sim`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-effort-limit-sim", type=float, default=20.0)
# 【L0037】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--gripper-stiffness"`；第 2 个实参 `type=float`；第 3 个实参 `default=120.0`。
# 【项目含义】声明命令行参数 `--gripper-stiffness`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-stiffness", type=float, default=120.0)
# 【L0038】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--gripper-damping"`；第 2 个实参 `type=float`；第 3 个实参 `default=12.0`。
# 【项目含义】声明命令行参数 `--gripper-damping`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-damping", type=float, default=12.0)
# 【L0039】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--gripper-close-target-rad"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.65`。
# 【项目含义】声明命令行参数 `--gripper-close-target-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--gripper-close-target-rad", type=float, default=0.65)
# 【L0040】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--pregrasp-distance-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.10`。
# 【项目含义】声明命令行参数 `--pregrasp-distance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--pregrasp-distance-m", type=float, default=0.10)
# 【L0041】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--grasp-world-offset-x-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.0`。
# 【项目含义】声明命令行参数 `--grasp-world-offset-x-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--grasp-world-offset-x-m", type=float, default=0.0)
# 【L0042】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--grasp-world-offset-z-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.0`。
# 【项目含义】声明命令行参数 `--grasp-world-offset-z-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--grasp-world-offset-z-m", type=float, default=0.0)
# 【L0043】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0044】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--source-offset-x-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--source-offset-x-m",
# 【L0045】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0046】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0047】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Move the source block and support in world x for demonstration diversity."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Move the source block and support in world x for demonstration diversity."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world x for demonstration diversity.",
# 【L0048】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0049】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0050】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--source-offset-y-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--source-offset-y-m",
# 【L0051】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0052】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0053】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Move the source block and support in world y for demonstration diversity."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Move the source block and support in world y for demonstration diversity."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Move the source block and support in world y for demonstration diversity.",
# 【L0054】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0055】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0056】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--grasp-orientation-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--grasp-orientation-mode",
# 【L0057】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `choices`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `choices` 传入 `("reference", "top_down")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("reference", "top_down"),
# 【L0058】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"reference"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"reference"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="reference",
# 【L0059】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0060】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--top-down-yaw-rad"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.0`。
# 【项目含义】声明命令行参数 `--top-down-yaw-rad`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--top-down-yaw-rad", type=float, default=0.0)
# 【L0061】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0062】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--top-down-tilt-rad"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-tilt-rad",
# 【L0063】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0064】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.0,
# 【L0065】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal.",
# 【L0066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0067】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0068】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--top-down-ik-multistart"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-ik-multistart",
# 【L0069】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0070】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`1` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `1`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1,
# 【L0071】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Number of deterministic joint-space seeds used to solve the top-down pose."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Number of deterministic joint-space seeds used to solve the top-down pose."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Number of deterministic joint-space seeds used to solve the top-down pose.",
# 【L0072】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0073】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0074】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--top-down-blend"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--top-down-blend",
# 【L0075】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0076】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `1.0`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=1.0,
# 【L0077】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Interpolate from the calibrated side grasp (0) to the requested above-table pose (1)."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Interpolate from the calibrated side grasp (0) to the requested above-table pose (1)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Interpolate from the calibrated side grasp (0) to the requested above-table pose (1).",
# 【L0078】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0079】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0080】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--lift-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--lift-mode",
# 【L0081】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `choices`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `choices` 传入 `("joint_reference", "cartesian_vertical")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("joint_reference", "cartesian_vertical"),
# 【L0082】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"joint_reference"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"joint_reference"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="joint_reference",
# 【L0083】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Use the historical fixed joint target or solve a local vertical lift from the current grasp pose."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Use the historical fixed joint target or solve a local vertical lift from the current grasp pose."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use the historical fixed joint target or solve a local vertical lift from the current grasp pose.",
# 【L0084】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0085】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--cartesian-lift-height-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.04`。
# 【项目含义】声明命令行参数 `--cartesian-lift-height-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--cartesian-lift-height-m", type=float, default=0.04)
# 【L0086】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--release-clearance-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.08`。
# 【项目含义】声明命令行参数 `--release-clearance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--release-clearance-m", type=float, default=0.08)
# 【L0087】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--release-separation-assist-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.05`。
# 【项目含义】声明命令行参数 `--release-separation-assist-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--release-separation-assist-m", type=float, default=0.05)
# 【L0088】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--place-descent"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--place-descent`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--place-descent", action="store_true")
# 【L0089】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--place-descent-distance-m"`；第 2 个实参 `type=float`；第 3 个实参 `default=0.10`。
# 【项目含义】声明命令行参数 `--place-descent-distance-m`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--place-descent-distance-m", type=float, default=0.10)
# 【L0090】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0091】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--place-waypoint-steps"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--place-waypoint-steps",
# 【L0092】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0093】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`60` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `60`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=60,
# 【L0094】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Simulation steps used for each approximately 1 cm place-descent segment."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Simulation steps used for each approximately 1 cm place-descent segment."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Simulation steps used for each approximately 1 cm place-descent segment.",
# 【L0095】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0096】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0097】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--target-support-mode"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--target-support-mode",
# 【L0098】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `choices`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `choices` 传入 `("wide_platform", "rotated_strip")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("wide_platform", "rotated_strip"),
# 【L0099】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"wide_platform"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"wide_platform"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="wide_platform",
# 【L0100】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0101】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0102】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--target-collision-enable-stage"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--target-collision-enable-stage",
# 【L0103】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `choices`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `choices` 传入 `("after_transfer", "after_place_descent")`；该参数在本项目中表示本功能块中的 `choices` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    choices=("after_transfer", "after_place_descent"),
# 【L0104】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"after_transfer"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"after_transfer"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="after_transfer",
# 【L0105】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0106】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--diagnose-approach-only"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--diagnose-approach-only`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--diagnose-approach-only", action="store_true")
# 【L0107】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--diagnose-kinematics-only"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--diagnose-kinematics-only`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--diagnose-kinematics-only", action="store_true")
# 【L0108】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--collision-bypass-during-approach"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--collision-bypass-during-approach`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--collision-bypass-during-approach", action="store_true")
# 【L0109】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--initialize-at-grasp"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--initialize-at-grasp`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--initialize-at-grasp", action="store_true")
# 【L0110】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--disable-arm-gravity-during-approach"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--disable-arm-gravity-during-approach`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--disable-arm-gravity-during-approach", action="store_true")
# 【L0111】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0112】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--disable-arm-gravity-through-transport"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--disable-arm-gravity-through-transport",
# 【L0113】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0114】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Keep arm-link gravity disabled after approach to isolate object grasp/transport physics."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Keep arm-link gravity disabled after approach to isolate object grasp/transport physics."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep arm-link gravity disabled after approach to isolate object grasp/transport physics.",
# 【L0115】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0116】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--natural-source-gravity"`；第 2 个实参 `action="store_true"`。
# 【项目含义】声明命令行参数 `--natural-source-gravity`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--natural-source-gravity", action="store_true")
# 【L0117】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0118】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--enable-moving-gripper-gravity"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--enable-moving-gripper-gravity",
# 【L0119】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0120】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Keep gravity enabled on all six moving 4C2 finger links."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Keep gravity enabled on all six moving 4C2 finger links."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Keep gravity enabled on all six moving 4C2 finger links.",
# 【L0121】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0122】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0123】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--unassisted-release"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--unassisted-release",
# 【L0124】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0125】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"After opening the gripper, let gravity place the block without pose or velocity injection."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"After opening the gripper, let gravity place the block without pose or velocity injection."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="After opening the gripper, let gravity place the block without pose or velocity injection.",
# 【L0126】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0127】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0128】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--record-episode-dir"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-episode-dir",
# 【L0129】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`Path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `Path`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=Path,
# 【L0130】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Write a synchronized scripted-expert episode to this directory."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Write a synchronized scripted-expert episode to this directory."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Write a synchronized scripted-expert episode to this directory.",
# 【L0131】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0132】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0133】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--record-stride-steps"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-stride-steps",
# 【L0134】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0135】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`12` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=12,
# 【L0136】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics)."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics).",
# 【L0137】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0138】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0139】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--episode-prompt"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--episode-prompt",
# 【L0140】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"pick up the block and place it on the target"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"pick up the block and place it on the target"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="pick up the block and place it on the target",
# 【L0141】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Language instruction stored with the expert episode."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Language instruction stored with the expert episode."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Language instruction stored with the expert episode.",
# 【L0142】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0143】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0144】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--record-images"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--record-images",
# 【L0145】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0146】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras.",
# 【L0147】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0148】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0149】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--pi05-closed-loop"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--pi05-closed-loop",
# 【L0150】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0151】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Use an RM65-specific pi0.5 WebSocket policy instead of the scripted expert.",
# 【L0152】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0153】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-host"`；第 2 个实参 `default="127.0.0.1"`。
# 【项目含义】声明命令行参数 `--policy-host`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-host", default="127.0.0.1")
# 【L0154】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-port"`；第 2 个实参 `type=int`；第 3 个实参 `default=8000`。
# 【项目含义】声明命令行参数 `--policy-port`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-port", type=int, default=8000)
# 【L0155】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-max-action-chunks"`；第 2 个实参 `type=int`；第 3 个实参 `default=120`。
# 【项目含义】声明命令行参数 `--policy-max-action-chunks`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-max-action-chunks", type=int, default=120)
# 【L0156】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-execute-actions-per-chunk"`；第 2 个实参 `type=int`；第 3 个实参 `default=5`。
# 【项目含义】声明命令行参数 `--policy-execute-actions-per-chunk`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-execute-actions-per-chunk", type=int, default=5)
# 【L0157】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0158】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-gripper-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-gripper-open-threshold",
# 【L0159】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0160】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.12`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.12,
# 【L0161】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    help=(
# 【L0162】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"Normalized 4C2 target/feedback threshold used to verify a model-selected "`；在“命令行参数；它们是实验可重复性的外部控制面板”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
        "Normalized 4C2 target/feedback threshold used to verify a model-selected "
# 【L0163】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"release. Values below the threshold are open; calibrate this in simulation."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "release. Values below the threshold are open; calibrate this in simulation."
# 【L0164】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0165】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0166】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0167】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-gripper-actual-open-threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-gripper-actual-open-threshold",
# 【L0168】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`float` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=float,
# 【L0169】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`0.20` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `0.20`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default=0.20,
# 【L0170】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    help=(
# 【L0171】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Actual normalized 4C2 feedback threshold used to detect an opening gripper. "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "Actual normalized 4C2 feedback threshold used to detect an opening gripper. "
# 【L0172】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"The stricter policy target threshold remains --policy-gripper-open-threshold."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "The stricter policy target threshold remains --policy-gripper-open-threshold."
# 【L0173】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0174】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0175】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `add_argument` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-release-required-consecutive-chunks"`；第 2 个实参 `type=int`；第 3 个实参 `default=2`。
# 【项目含义】声明命令行参数 `--policy-release-required-consecutive-chunks`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument("--policy-release-required-consecutive-chunks", type=int, default=2)
# 【L0176】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0177】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-checkpoint-id"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-checkpoint-id",
# 【L0178】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `default`。右侧语法为：`"unknown"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `default` 传入 `"unknown"`；该参数在本项目中表示本功能块中的 `default` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    default="unknown",
# 【L0179】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Checkpoint identifier stored in the machine-readable evaluation report."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Checkpoint identifier stored in the machine-readable evaluation report."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Checkpoint identifier stored in the machine-readable evaluation report.",
# 【L0180】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0181】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0182】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-noise-seed"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--policy-noise-seed",
# 【L0183】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0184】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    help=(
# 【L0185】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Non-negative case-level seed. Chunk N uses seed + N and inference fails "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "Non-negative case-level seed. Chunk N uses seed + N and inference fails "
# 【L0186】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"closed when the server evidence does not match."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "closed when the server evidence does not match."
# 【L0187】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0188】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0189】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0190】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--simulation-seed"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--simulation-seed",
# 【L0191】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `type`。右侧语法为：`int` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `type` 传入 `int`；该参数在本项目中表示本功能块中的 `type` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    type=int,
# 【L0192】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`"Seed shared by Python, NumPy, Torch, CUDA, Warp, Replicator, and the report."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `help` 传入 `"Seed shared by Python, NumPy, Torch, CUDA, Warp, Replicator, and the report."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    help="Seed shared by Python, NumPy, Torch, CUDA, Warp, Replicator, and the report.",
# 【L0193】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0194】语法拆解：`parser.add_argument(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“命令行参数；它们是实验可重复性的外部控制面板”的配置，最终参数也会写入证据便于复现。
parser.add_argument(
# 【L0195】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--reset-renderer-accumulation-before-policy-observation"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
    "--reset-renderer-accumulation-before-policy-observation",
# 【L0196】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`"store_true"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“命令行参数；它们是实验可重复性的外部控制面板”。
    action="store_true",
# 【L0197】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `help`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `help`，它在本项目中表示本功能块中的 `help` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    help=(
# 【L0198】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Experimental diagnostic: reset Isaac Sim renderer accumulation before "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "Experimental diagnostic: reset Isaac Sim renderer accumulation before "
# 【L0199】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"each pi0.5 camera observation. Disabled by default."`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "each pi0.5 camera observation. Disabled by default."
# 【L0200】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    ),
# 【L0201】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
)
# 【L0202】语法拆解：`AppLauncher` 是模块/对象，点号 `.` 从中取出 `add_app_launcher_args` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parser`。
# 【项目含义】把 IsaacLab 通用参数（如 --headless、--device、--enable_cameras）加入解析器。
AppLauncher.add_app_launcher_args(parser)
# 【L0203】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args`。右侧语法为：`parser` 是模块/对象，点号 `.` 从中取出 `parse_args` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
args = parser.parse_args()
# 【L0204】语法拆解：`if` 要求条件 `not 0.0 < args.policy_gripper_open_threshold < 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】按表达式 `not 0.0 < args.policy_gripper_open_threshold < 1.0` 检查夹爪阈值或开合状态；该阈值决定 4C2 是否被视为已张开
if not 0.0 < args.policy_gripper_open_threshold < 1.0:
# 【L0205】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-gripper-open-threshold must be between 0 and 1"`。
# 【项目含义】对 `parser` 调用 `error("--policy-gripper-open-threshold must be between 0 and 1")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--policy-gripper-open-threshold must be between 0 and 1")
# 【L0206】语法拆解：`if` 要求条件 `not args.policy_gripper_open_threshold <= args.policy_gripper_actual_open_threshold < 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】按表达式 `not args.policy_gripper_open_threshold <= args.policy_gripper_actual_open_threshold < 1.0` 检查夹爪阈值或开合状态；该阈值决定 4C2 是否被视为已张开
if not args.policy_gripper_open_threshold <= args.policy_gripper_actual_open_threshold < 1.0:
# 【L0207】语法拆解：`parser.error(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `parser` 调用多行方法 `error`：调用 `parser` 提供的 `error` 操作；具体参数写在随后几行，用于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error(
# 【L0208】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"--policy-gripper-actual-open-threshold must be at least the policy target "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "--policy-gripper-actual-open-threshold must be at least the policy target "
# 【L0209】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"threshold and below 1"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“命令行参数；它们是实验可重复性的外部控制面板”中的帮助说明、错误原因、任务名称或报告文字。
        "threshold and below 1"
# 【L0210】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“命令行参数；它们是实验可重复性的外部控制面板”。
    )
# 【L0211】语法拆解：`if` 要求条件 `args.policy_release_required_consecutive_chunks < 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.policy_release_required_consecutive_chunks < 1` 是否成立；`policy_release_required_consecutive_chunks` 表示策略相关值
if args.policy_release_required_consecutive_chunks < 1:
# 【L0212】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-release-required-consecutive-chunks must be positive"`。
# 【项目含义】对 `parser` 调用 `error("--policy-release-required-consecutive-chunks must be positive")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--policy-release-required-consecutive-chunks must be positive")
# 【L0213】语法拆解：`if` 要求条件 `args.pi05_closed_loop and args.policy_noise_seed is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.pi05_closed_loop and args.policy_noise_seed is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
if args.pi05_closed_loop and args.policy_noise_seed is None:
# 【L0214】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--pi05-closed-loop requires --policy-noise-seed"`。
# 【项目含义】对 `parser` 调用 `error("--pi05-closed-loop requires --policy-noise-seed")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--pi05-closed-loop requires --policy-noise-seed")
# 【L0215】语法拆解：`if` 要求条件 `args.policy_noise_seed is not None and args.policy_noise_seed < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.policy_noise_seed is not None and args.policy_noise_seed < 0`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
if args.policy_noise_seed is not None and args.policy_noise_seed < 0:
# 【L0216】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--policy-noise-seed must be non-negative"`。
# 【项目含义】对 `parser` 调用 `error("--policy-noise-seed must be non-negative")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--policy-noise-seed must be non-negative")
# 【L0217】语法拆解：`if` 要求条件 `args.pi05_closed_loop and args.simulation_seed is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.pi05_closed_loop and args.simulation_seed is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
if args.pi05_closed_loop and args.simulation_seed is None:
# 【L0218】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--pi05-closed-loop requires --simulation-seed"`。
# 【项目含义】对 `parser` 调用 `error("--pi05-closed-loop requires --simulation-seed")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--pi05-closed-loop requires --simulation-seed")
# 【L0219】语法拆解：`if` 要求条件 `args.simulation_seed is not None and args.simulation_seed < 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.simulation_seed is not None and args.simulation_seed < 0`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
if args.simulation_seed is not None and args.simulation_seed < 0:
# 【L0220】语法拆解：`parser` 是模块/对象，点号 `.` 从中取出 `error` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"--simulation-seed must be non-negative"`。
# 【项目含义】对 `parser` 调用 `error("--simulation-seed must be non-negative")`：调用 `parser` 提供的 `error` 操作。本行产生的修改/返回值服务于“命令行参数；它们是实验可重复性的外部控制面板”。
    parser.error("--simulation-seed must be non-negative")
# 【L0221】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `app_launcher`。右侧语法为：`AppLauncher` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args`。
# 【项目含义】得到 `app_launcher`，它在本项目中表示本功能块中的 `app_launcher` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `AppLauncher(args)`；`AppLauncher` 表示本功能块中的 `AppLauncher` 值。
app_launcher = AppLauncher(args)
# 【L0222】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_app`。右侧语法为：`app_launcher` 是起始对象；每个点号 `.` 依次读取属性/成员：`app`。
# 【项目含义】得到 `simulation_app`，它在本项目中表示本功能块中的 `simulation_app` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `app_launcher.app`；`app_launcher` 表示本功能块中的 `app_launcher` 值；`app` 表示本功能块中的 `app` 值。
simulation_app = app_launcher.app
# 【L0223】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“命令行参数；它们是实验可重复性的外部控制面板”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“命令行参数；它们是实验可重复性的外部控制面板”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 3：启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API（源码第 224-268 行）

### 5.A 数据流位置

- 上游：模块 2“命令行参数；它们是实验可重复性的外部控制面板”。
- 本模块：启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API。
- 下游：处理结果继续交给模块 4“RM65 关节、物体尺寸、接触点和关节限位常量”。

### 5.B 为什么需要这一组代码

这一组负责“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `lula`：NVIDIA Lula 运动学求解器实例。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `usd`：Isaac Sim 实际加载的 RM65+4C2 USD 资产路径。

### 5.D 本模块首次阅读要认识的调用

- `enable_extension(...)`：圆括号表示真正执行调用；让 Isaac Sim 加载指定扩展；没有它就无法使用随后导入的 URDF 或 Lula API。
- `configure_seed(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `replicator.set_global_seed(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 227-228 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`import omni.usd  # noqa: E402` / `import omni.replicator.core as replicator  # noqa: E402`
- 当前第 237-237 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`from isaaclab.utils.seed import configure_seed  # noqa: E402`
- 当前第 244-253 行相对旧教学快照发生 `insert`：旧版 0 行，当前 10 行。 当前代码摘录：`from openpi_extension.closed_loop_report import (  # noqa: E402` / `build_preflight_safety_failure_report,` / `)` / `from openpi_extension.deterministic_policy import (  # noqa: E402`
- 当前第 261-266 行相对旧教学快照发生 `insert`：旧版 0 行，当前 6 行。 当前代码摘录：`CONFIGURED_SIMULATION_SEED = configure_seed(` / `args.simulation_seed, torch_deterministic=args.pi05_closed_loop` / `)` / `replicator.set_global_seed(CONFIGURED_SIMULATION_SEED)`

### 5.G 逐行精读

```python
# 【L0224】语法拆解：`import` 加载模块；`numpy as np  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `numpy` 引入 `numpy as np  # noqa: E402`。在这份程序里，`numpy` 用于NumPy 数值数组库；本项目用它表达图像、关节向量和动作矩阵；后续出现这些名字时调用的是这里的外部能力。
import numpy as np  # noqa: E402
# 【L0225】语法拆解：`import` 加载模块；`torch  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `torch` 引入 `torch  # noqa: E402`。在这份程序里，`torch` 用于PyTorch 张量库；IsaacLab 的 GPU 状态和命令使用 Torch 张量；后续出现这些名字时调用的是这里的外部能力。
import torch  # noqa: E402
# 【L0226】语法拆解：`import` 加载模块；`isaaclab.sim as sim_utils  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `isaaclab` 引入 `isaaclab.sim as sim_utils  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import isaaclab.sim as sim_utils  # noqa: E402
# 【L0227】语法拆解：`import` 加载模块；`omni.usd  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `omni` 引入 `omni.usd  # noqa: E402`。在这份程序里，`omni` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import omni.usd  # noqa: E402
# 【L0228】语法拆解：`import` 加载模块；`omni.replicator.core as replicator  # noqa: E402` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `omni` 引入 `omni.replicator.core as replicator  # noqa: E402`。在这份程序里，`omni` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import omni.replicator.core as replicator  # noqa: E402
# 【L0229】语法拆解：`from isaacsim.core.utils.extensions` 指定来源模块；`import enable_extension  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaacsim` 引入 `enable_extension  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
# 【L0230】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0231】语法拆解：`enable_extension` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"isaacsim.robot_motion.motion_generation"`。
# 【项目含义】调用 `enable_extension("isaacsim.robot_motion.motion_generation")`：让 Isaac Sim 加载指定扩展；没有它就无法使用随后导入的 URDF 或 Lula API。它的结果/修改用于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
enable_extension("isaacsim.robot_motion.motion_generation")
# 【L0232】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0233】语法拆解：`from isaaclab.actuators` 指定来源模块；`import ImplicitActuatorCfg  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `ImplicitActuatorCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
# 【L0234】语法拆解：`from isaaclab.assets` 指定来源模块；`import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
# 【L0235】语法拆解：`from isaaclab.sensors` 指定来源模块；`import ContactSensor, ContactSensorCfg  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `ContactSensor, ContactSensorCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sensors import ContactSensor, ContactSensorCfg  # noqa: E402
# 【L0236】语法拆解：`from isaaclab.sensors.camera` 指定来源模块；`import Camera, CameraCfg  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `Camera, CameraCfg  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
# 【L0237】语法拆解：`from isaaclab.utils.seed` 指定来源模块；`import configure_seed  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `configure_seed  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.utils.seed import configure_seed  # noqa: E402
# 【L0238】语法拆解：`from openpi_extension.expert_episode` 指定来源模块；`import (  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `(  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.expert_episode import (  # noqa: E402
# 【L0239】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`EpisodeRecorder` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `EpisodeRecorder`；在本项目中它表示本功能块中的 `EpisodeRecorder` 值。
    EpisodeRecorder,
# 【L0240】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`normalize_gripper` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `normalize_gripper`；在本项目中它表示夹爪相关值。
    normalize_gripper,
# 【L0241】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`validate_episode` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `validate_episode`；在本项目中它表示一条轨迹相关值。
    validate_episode,
# 【L0242】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0243】语法拆解：`from openpi_extension.action_guard` 指定来源模块；`import guard_action_chunk  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `guard_action_chunk  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.action_guard import guard_action_chunk  # noqa: E402
# 【L0244】语法拆解：`from openpi_extension.closed_loop_report` 指定来源模块；`import (  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `(  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.closed_loop_report import (  # noqa: E402
# 【L0245】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`build_preflight_safety_failure_report` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `build_preflight_safety_failure_report`；在本项目中它表示报告相关值。
    build_preflight_safety_failure_report,
# 【L0246】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0247】语法拆解：`from openpi_extension.deterministic_policy` 指定来源模块；`import (  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `(  # noqa: E402`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from openpi_extension.deterministic_policy import (  # noqa: E402
# 【L0248】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`POLICY_NOISE_SEED_KEY` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `POLICY_NOISE_SEED_KEY`；在本项目中它表示策略相关值。
    POLICY_NOISE_SEED_KEY,
# 【L0249】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`POLICY_SAMPLING_MODE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `POLICY_SAMPLING_MODE`；在本项目中它表示策略相关值。
    POLICY_SAMPLING_MODE,
# 【L0250】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`array_sha256` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `array_sha256`；在本项目中它表示本功能块中的 `array_sha256` 值。
    array_sha256,
# 【L0251】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`case_chunk_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `case_chunk_seed`；在本项目中它表示本功能块中的 `case_chunk_seed` 值。
    case_chunk_seed,
# 【L0252】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`validate_policy_sampling_evidence` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `validate_policy_sampling_evidence`；在本项目中它表示策略相关值。
    validate_policy_sampling_evidence,
# 【L0253】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0254】语法拆解：`from grasp_geometry` 指定来源模块；`import compute_top_down_link_pose  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `grasp_geometry` 引入 `compute_top_down_link_pose  # noqa: E402`。在这份程序里，`grasp_geometry` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from grasp_geometry import compute_top_down_link_pose  # noqa: E402
# 【L0255】语法拆解：`from isaaclab.sim` 指定来源模块；`import SimulationContext  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `SimulationContext  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.sim import SimulationContext  # noqa: E402
# 【L0256】语法拆解：`from isaaclab.utils` 指定来源模块；`import math as math_utils  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaaclab` 引入 `math as math_utils  # noqa: E402`。在这份程序里，`isaaclab` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaaclab.utils import math as math_utils  # noqa: E402
# 【L0257】语法拆解：`from isaacsim.core.utils.rotations` 指定来源模块；`import rot_matrix_to_quat  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaacsim` 引入 `rot_matrix_to_quat  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
# 【L0258】语法拆解：`from isaacsim.core.utils.stage` 指定来源模块；`import get_current_stage  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaacsim` 引入 `get_current_stage  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
# 【L0259】语法拆解：`from isaacsim.robot_motion.motion_generation.lula.kinematics` 指定来源模块；`import LulaKinematicsSolver  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `isaacsim` 引入 `LulaKinematicsSolver  # noqa: E402`。在这份程序里，`isaacsim` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver  # noqa: E402
# 【L0260】语法拆解：`from pxr` 指定来源模块；`import PhysxSchema, UsdPhysics  # noqa: E402` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `pxr` 引入 `PhysxSchema, UsdPhysics  # noqa: E402`。在这份程序里，`pxr` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
from pxr import PhysxSchema, UsdPhysics  # noqa: E402
# 【L0261】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0262】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0263】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `CONFIGURED_SIMULATION_SEED`。右侧语法为：`configure_seed(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `CONFIGURED_SIMULATION_SEED`，它在本项目中表示本功能块中的 `CONFIGURED_SIMULATION_SEED` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `configure_seed(`；`configure_seed` 表示本功能块中的 `configure_seed` 值。
CONFIGURED_SIMULATION_SEED = configure_seed(
# 【L0264】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `args.simulation_seed, torch_deterministic`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】把表达式/参数 `args.simulation_seed, torch_deterministic=args.pi05_closed_loop` 接入当前完整语句；`simulation_seed` 表示本功能块中的 `simulation_seed` 值；`torch_deterministic` 表示本功能块中的 `torch_deterministic` 值；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值。在“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    args.simulation_seed, torch_deterministic=args.pi05_closed_loop
# 【L0265】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
)
# 【L0266】语法拆解：`replicator` 是模块/对象，点号 `.` 从中取出 `set_global_seed` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `CONFIGURED_SIMULATION_SEED`。
# 【项目含义】对 `replicator` 调用 `set_global_seed(CONFIGURED_SIMULATION_SEED)`：调用 `replicator` 提供的 `set_global_seed` 操作。本行产生的修改/返回值服务于“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
replicator.set_global_seed(CONFIGURED_SIMULATION_SEED)
# 【L0267】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

# 【L0268】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 4：RM65 关节、物体尺寸、接触点和关节限位常量（源码第 269-310 行）

### 5.A 数据流位置

- 上游：模块 3“启动 Isaac 后加载 NumPy、Torch、IsaacLab、Lula 与 USD API”。
- 本模块：RM65 关节、物体尺寸、接触点和关节限位常量。
- 下游：处理结果继续交给模块 5“旋转、四元数和旋转距离的数学工具”。

### 5.B 为什么需要这一组代码

这一组负责“RM65 关节、物体尺寸、接触点和关节限位常量”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.D 本模块首次阅读要认识的调用

- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `UnsafeIKBranchJumpError(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 当前第 281-283 行相对旧教学快照发生 `insert`：旧版 0 行，当前 3 行。 当前代码摘录：`POLICY_NOISE_ACTION_HORIZON = 10` / `POLICY_NOISE_ACTION_DIM = 32` / `CUBE_WORKSPACE_ESCAPE_RADIUS_M = 1.0`
- 当前第 297-300 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`class UnsafeIKBranchJumpError(RuntimeError):` / `"""A deterministic kinematic preflight rejection, not infrastructure failure."""`

### 5.G 逐行精读

```python
# 【L0269】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `ARM_JOINTS`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `ARM_JOINTS`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[f"joint_{index}" for index in range(1, 7)]`；`f` 表示本功能块中的 `f` 值；`joint_` 表示关节相关值；`index` 表示索引相关值。
ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
# 【L0270】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `ARM_BODY_PATHS`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `ARM_BODY_PATHS`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{f"/World/Robot/link_{index}" for index in range(1, 7)}`；`f` 表示本功能块中的 `f` 值；`World` 表示本功能块中的 `World` 值；`Robot` 表示本功能块中的 `Robot` 值。
ARM_BODY_PATHS = {f"/World/Robot/link_{index}" for index in range(1, 7)}
# 【L0271】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `MOVING_GRIPPER_BODY_PATHS`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `MOVING_GRIPPER_BODY_PATHS`，它在本项目中表示夹爪、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
MOVING_GRIPPER_BODY_PATHS = {
# 【L0272】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_r_1"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_1",
# 【L0273】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_l_1"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_1",
# 【L0274】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_r_2"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_2",
# 【L0275】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_l_2"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_2",
# 【L0276】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_r_3"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_r_3",
# 【L0277】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/Robot/tool_l_3"`；在“RM65 关节、物体尺寸、接触点和关节限位常量”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
    "/World/Robot/tool_l_3",
# 【L0278】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0279】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `BLOCK_SIZE`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `BLOCK_SIZE`，它在本项目中表示本功能块中的 `BLOCK_SIZE` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.060, 0.040, 0.025)` 的结果保存下来，供当前功能块后续使用。
BLOCK_SIZE = (0.060, 0.040, 0.025)
# 【L0280】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `BLOCK_MASS_KG`。右侧语法为：`0.030` 是直接写在源码中的数值常量。
# 【项目含义】得到 `BLOCK_MASS_KG`，它在本项目中表示本功能块中的 `BLOCK_MASS_KG` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.030` 的结果保存下来，供当前功能块后续使用。
BLOCK_MASS_KG = 0.030
# 【L0281】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `POLICY_NOISE_ACTION_HORIZON`。右侧语法为：`10` 是直接写在源码中的数值常量。
# 【项目含义】得到 `POLICY_NOISE_ACTION_HORIZON`，它在本项目中表示策略、动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `10` 的结果保存下来，供当前功能块后续使用。
POLICY_NOISE_ACTION_HORIZON = 10
# 【L0282】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `POLICY_NOISE_ACTION_DIM`。右侧语法为：`32` 是直接写在源码中的数值常量。
# 【项目含义】得到 `POLICY_NOISE_ACTION_DIM`，它在本项目中表示策略、动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `32` 的结果保存下来，供当前功能块后续使用。
POLICY_NOISE_ACTION_DIM = 32
# 【L0283】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `CUBE_WORKSPACE_ESCAPE_RADIUS_M`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `CUBE_WORKSPACE_ESCAPE_RADIUS_M`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `1.0` 的结果保存下来，供当前功能块后续使用。
CUBE_WORKSPACE_ESCAPE_RADIUS_M = 1.0
# 【L0284】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `SOURCE_BLOCK_POSITION`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[-0.22128649, -0.00000383, 0.75670463]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `SOURCE_BLOCK_POSITION`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
SOURCE_BLOCK_POSITION = np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)
# 【L0285】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `SOURCE_BLOCK_QUATERNION_WXYZ`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `SOURCE_BLOCK_QUATERNION_WXYZ`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(-0.20872162, -0.00000211, 0.97797507, 0.00002437)` 的结果保存下来，供当前功能块后续使用。
SOURCE_BLOCK_QUATERNION_WXYZ = (-0.20872162, -0.00000211, 0.97797507, 0.00002437)
# 【L0286】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `TARGET_PLATFORM_SIZE`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `TARGET_PLATFORM_SIZE`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.200, 0.200, 0.040)` 的结果保存下来，供当前功能块后续使用。
TARGET_PLATFORM_SIZE = (0.200, 0.200, 0.040)
# 【L0287】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `TARGET_PLATFORM_TOP_Z`。右侧语法为：`0.650` 是直接写在源码中的数值常量。
# 【项目含义】得到 `TARGET_PLATFORM_TOP_Z`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.650` 的结果保存下来，供当前功能块后续使用。
TARGET_PLATFORM_TOP_Z = 0.650
# 【L0288】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `SOURCE_PLATFORM_SIZE`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `SOURCE_PLATFORM_SIZE`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.120, 0.018, 0.020)` 的结果保存下来，供当前功能块后续使用。
SOURCE_PLATFORM_SIZE = (0.120, 0.018, 0.020)
# 【L0289】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `TARGET_STRIP_SIZE`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `TARGET_STRIP_SIZE`，它在本项目中表示目标位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(0.070, 0.018, 0.020)` 的结果保存下来，供当前功能块后续使用。
TARGET_STRIP_SIZE = (0.070, 0.018, 0.020)
# 【L0290】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `SOURCE_PLATFORM_TOP_Z`。右侧语法为：`0.7330` 是直接写在源码中的数值常量。
# 【项目含义】得到 `SOURCE_PLATFORM_TOP_Z`，它在本项目中表示源位置方块/平台的任务常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.7330` 的结果保存下来，供当前功能块后续使用。
SOURCE_PLATFORM_TOP_Z = 0.7330
# 【L0291】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RELEASE_DOWNWARD_SPEED_M_S`。右侧语法为：`0.10` 是直接写在源码中的数值常量。
# 【项目含义】得到 `RELEASE_DOWNWARD_SPEED_M_S`，它在本项目中表示本功能块中的 `RELEASE_DOWNWARD_SPEED_M_S` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.10` 的结果保存下来，供当前功能块后续使用。
RELEASE_DOWNWARD_SPEED_M_S = 0.10
# 【L0292】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RELEASE_SEPARATION_ASSIST_M`。右侧语法为：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】得到 `RELEASE_SEPARATION_ASSIST_M`，它在本项目中表示本功能块中的 `RELEASE_SEPARATION_ASSIST_M` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.05` 的结果保存下来，供当前功能块后续使用。
RELEASE_SEPARATION_ASSIST_M = 0.05
# 【L0293】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `TIP_LOCAL_POINTS`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `TIP_LOCAL_POINTS`，它在本项目中表示本功能块中的 `TIP_LOCAL_POINTS` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
TIP_LOCAL_POINTS = {
# 【L0294】语法拆解：这是字典键值对：`"tool_r_2"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `tool_r_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_r_2` 数据；字段值来自 `(0.04368, -0.00645, 0.01250)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_r_2": (0.04368, -0.00645, 0.01250),
# 【L0295】语法拆解：这是字典键值对：`"tool_l_2"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `tool_l_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_l_2` 数据；字段值来自 `(0.04368, 0.00645, 0.01257)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_l_2": (0.04368, 0.00645, 0.01257),
# 【L0296】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0297】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65 关节、物体尺寸、接触点和关节限位常量”中的逻辑段，让结构更容易看清。

# 【L0298】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65 关节、物体尺寸、接触点和关节限位常量”中的逻辑段，让结构更容易看清。

# 【L0299】语法拆解：`class` 定义类 `UnsafeIKBranchJumpError`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `UnsafeIKBranchJumpError` 类并继承 `RuntimeError`；它把“RM65 关节、物体尺寸、接触点和关节限位常量”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class UnsafeIKBranchJumpError(RuntimeError):
# 【L0300】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `A deterministic kinematic preflight rejection, not infrastructure failure.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """A deterministic kinematic preflight rejection, not infrastructure failure."""
# 【L0301】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `PAD_LOCAL_CENTERS`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `PAD_LOCAL_CENTERS`，它在本项目中表示本功能块中的 `PAD_LOCAL_CENTERS` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
PAD_LOCAL_CENTERS = {
# 【L0302】语法拆解：这是字典键值对：`"tool_r_2"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `tool_r_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_r_2` 数据；字段值来自 `(0.028775714, -0.011597111, -0.073257379)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_r_2": (0.028775714, -0.011597111, -0.073257379),
# 【L0303】语法拆解：这是字典键值对：`"tool_l_2"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】定义字典/JSON 字段 `tool_l_2`，它表示“RM65 关节、物体尺寸、接触点和关节限位常量”中的 `tool_l_2` 数据；字段值来自 `(0.027286683, 0.013343694, -0.072958842)`，因此保存/传递的是这个表达式当前计算出的结果。
    "tool_l_2": (0.027286683, 0.013343694, -0.072958842),
# 【L0304】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“RM65 关节、物体尺寸、接触点和关节限位常量”。
}
# 【L0305】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `CONTACT_SENSORS: dict[str, ContactSensor]`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】把右侧结果写进 `CONTACT_SENSORS: dict[str, ContactSensor]`（写入 `CONTACT_SENSORS: dict[str, ContactSensor]` 指定的字段）；右侧具体做的是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
CONTACT_SENSORS: dict[str, ContactSensor] = {}
# 【L0306】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `GRIPPER_MASTER_JOINT`。右侧语法为：`"tool_gripper_joint"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `GRIPPER_MASTER_JOINT`，它在本项目中表示夹爪、关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"tool_gripper_joint"`；`tool_gripper_joint` 表示夹爪、关节相关值。
GRIPPER_MASTER_JOINT = "tool_gripper_joint"
# 【L0307】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RM65_JOINT_LOWER_RAD`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28]`。
# 【项目含义】得到 `RM65_JOINT_LOWER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])`；`array` 表示本功能块中的 `array` 值。
RM65_JOINT_LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
# 【L0308】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `RM65_JOINT_UPPER_RAD`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[3.106, 2.2689, 2.356, 3.106, 2.234, 6.28]`。
# 【项目含义】得到 `RM65_JOINT_UPPER_RAD`，它在本项目中表示RM65 机械约束或项目常量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])`；`array` 表示本功能块中的 `array` 值。
RM65_JOINT_UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])
# 【L0309】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65 关节、物体尺寸、接触点和关节限位常量”中的逻辑段，让结构更容易看清。

# 【L0310】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“RM65 关节、物体尺寸、接触点和关节限位常量”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“RM65 关节、物体尺寸、接触点和关节限位常量”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 5：旋转、四元数和旋转距离的数学工具（源码第 311-351 行）

### 5.A 数据流位置

- 上游：模块 4“RM65 关节、物体尺寸、接触点和关节限位常量”。
- 本模块：旋转、四元数和旋转距离的数学工具。
- 下游：处理结果继续交给模块 6“选择连续 IK 分支并规划不跳变的笛卡尔路径”。

### 5.B 为什么需要这一组代码

这一组负责“旋转、四元数和旋转距离的数学工具”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.D 本模块首次阅读要认识的调用

- `rotate_about_z(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.cos(...)`：圆括号表示真正执行调用；NumPy 的 `cos` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `np.sin(...)`：圆括号表示真正执行调用；NumPy 的 `sin` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `quaternion_multiply_wxyz(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `quaternion_to_matrix_wxyz(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `rotation_distance_rad(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.trace(...)`：圆括号表示真正执行调用；NumPy 的 `trace` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `np.arccos(...)`：圆括号表示真正执行调用；NumPy 的 `arccos` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。
- `np.clip(...)`：圆括号表示真正执行调用；把数值限制在给定上下界内。

### 5.E 本模块定义的新函数

### 函数卡：`rotate_about_z()`（第 311-316 行）

- 定义了什么：旋转、四元数和旋转距离的数学工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`position`：类型 `np.ndarray`；项目含义是位置相关值；`angle`：类型 `float`；项目含义是本功能块中的 `angle` 值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`np.array([cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]], dtype=np.float64)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1479` 的 `target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)`

### 函数卡：`quaternion_multiply_wxyz()`（第 319-330 行）

- 定义了什么：旋转、四元数和旋转距离的数学工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`left`：类型 `np.ndarray`；项目含义是本功能块中的 `left` 值；`right`：类型 `np.ndarray`；项目含义是本功能块中的 `right` 值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`np.array([lw * rw - lx * rx - ly * ry - lz * rz, lw * rx + lx * rw + ly * rz - lz * ry, lw * ry - lx * rz + ly * rw + lz * rx, lw * rz + lx * ry - ly * rx + lz * rw], dtype=np.float64)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1482` 的 `target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)`

### 函数卡：`quaternion_to_matrix_wxyz()`（第 333-342 行）

- 定义了什么：旋转、四元数和旋转距离的数学工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`quaternion`：类型 `np.ndarray`；项目含义是四元数相关值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]], dtype=np.float64)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1534` 的 `else quaternion_to_matrix_wxyz(`

### 函数卡：`rotation_distance_rad()`（第 345-349 行）

- 定义了什么：旋转、四元数和旋转距离的数学工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`left`：类型 `np.ndarray`；项目含义是本功能块中的 `left` 值；`right`：类型 `np.ndarray`；项目含义是本功能块中的 `right` 值
- 返回类型标注：`float`。
- 函数体实际 return：`float(np.arccos(np.clip(cosine, -1.0, 1.0)))`
- 项目中的实际调用位置：`run_pick_place_baseline.py:395` 的 `if rotation_distance_rad(rotation, target_rotation) > 1e-5:`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0311】语法拆解：`def` 定义函数 `rotate_about_z`；第一对圆括号列出形参，逗号负责分隔：`position: np.ndarray` 用冒号给参数加类型提示；`angle: float` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `rotate_about_z(position: np.ndarray, angle: float)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def rotate_about_z(position: np.ndarray, angle: float) -> np.ndarray:
# 【L0312】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cosine, sine`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `cos` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `angle)`；第 2 个实参 `np.sin(angle`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `cosine, sine`；`cosine` 表示本功能块中的 `cosine` 值；`sine` 表示本功能块中的 `sine` 值。右侧的来源是：计算表达式 `np.cos(angle), np.sin(angle)`；`cos` 表示本功能块中的 `cos` 值；`angle` 表示本功能块中的 `angle` 值；`sin` 表示本功能块中的 `sin` 值。
    cosine, sine = np.cos(angle), np.sin(angle)
# 【L0313】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0314】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],`；`cosine` 表示本功能块中的 `cosine` 值；`position` 表示位置相关值；`sine` 表示本功能块中的 `sine` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
        [cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],
# 【L0315】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0316】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0317】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0318】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0319】语法拆解：`def` 定义函数 `quaternion_multiply_wxyz`；第一对圆括号列出形参，逗号负责分隔：`left: np.ndarray` 用冒号给参数加类型提示；`right: np.ndarray` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray) -> np.ndarray:
# 【L0320】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lw, lx, ly, lz`。右侧语法为：`left` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `lw, lx, ly, lz`；`lw` 表示本功能块中的 `lw` 值；`lx` 表示本功能块中的 `lx` 值；`ly` 表示本功能块中的 `ly` 值；`lz` 表示本功能块中的 `lz` 值。右侧的来源是：计算表达式 `left`；`left` 表示本功能块中的 `left` 值。
    lw, lx, ly, lz = left
# 【L0321】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rw, rx, ry, rz`。右侧语法为：`right` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `rw, rx, ry, rz`；`rw` 表示本功能块中的 `rw` 值；`rx` 表示本功能块中的 `rx` 值；`ry` 表示本功能块中的 `ry` 值；`rz` 表示本功能块中的 `rz` 值。右侧的来源是：计算表达式 `right`；`right` 表示本功能块中的 `right` 值。
    rw, rx, ry, rz = right
# 【L0322】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0323】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0324】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `lw * rw - lx * rx - ly * ry - lz * rz` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `lw * rw - lx * rx - ly * ry - lz * rz`；`lw` 表示本功能块中的 `lw` 值；`rw` 表示本功能块中的 `rw` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rw - lx * rx - ly * ry - lz * rz,
# 【L0325】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `lw * rx + lx * rw + ly * rz - lz * ry` 使用运算符 `+`, `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `lw * rx + lx * rw + ly * rz - lz * ry`；`lw` 表示本功能块中的 `lw` 值；`rx` 表示本功能块中的 `rx` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rx + lx * rw + ly * rz - lz * ry,
# 【L0326】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `lw * ry - lx * rz + ly * rw + lz * rx` 使用运算符 `+`, `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `lw * ry - lx * rz + ly * rw + lz * rx`；`lw` 表示本功能块中的 `lw` 值；`ry` 表示本功能块中的 `ry` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * ry - lx * rz + ly * rw + lz * rx,
# 【L0327】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `lw * rz + lx * ry - ly * rx + lz * rw` 使用运算符 `+`, `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `lw * rz + lx * ry - ly * rx + lz * rw`；`lw` 表示本功能块中的 `lw` 值；`rz` 表示本功能块中的 `rz` 值；`lx` 表示本功能块中的 `lx` 值，它参与“旋转、四元数和旋转距离的数学工具”。
            lw * rz + lx * ry - ly * rx + lz * rw,
# 【L0328】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0329】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0330】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0331】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0332】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0333】语法拆解：`def` 定义函数 `quaternion_to_matrix_wxyz`；第一对圆括号列出形参，逗号负责分隔：`quaternion: np.ndarray` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `quaternion_to_matrix_wxyz(quaternion: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def quaternion_to_matrix_wxyz(quaternion: np.ndarray) -> np.ndarray:
# 【L0334】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `w, x, y, z`。右侧语法为：`quaternion` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `w, x, y, z`；`w` 表示本功能块中的 `w` 值；`x` 表示本功能块中的 `x` 值；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值。右侧的来源是：计算表达式 `quaternion`；`quaternion` 表示四元数相关值。
    w, x, y, z = quaternion
# 【L0335】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `np.array(` 交回调用者；这个值的含义是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    return np.array(
# 【L0336】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“旋转、四元数和旋转距离的数学工具”。
        [
# 【L0337】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],`；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值；`x` 表示本功能块中的 `x` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
# 【L0338】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],`；`x` 表示本功能块中的 `x` 值；`y` 表示本功能块中的 `y` 值；`z` 表示本功能块中的 `z` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
# 【L0339】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],`；`x` 表示本功能块中的 `x` 值；`z` 表示本功能块中的 `z` 值；`y` 表示本功能块中的 `y` 值，共同完成“旋转、四元数和旋转距离的数学工具”。
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
# 【L0340】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
        ],
# 【L0341】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“旋转、四元数和旋转距离的数学工具”。
        dtype=np.float64,
# 【L0342】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“旋转、四元数和旋转距离的数学工具”。
    )
# 【L0343】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0344】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0345】语法拆解：`def` 定义函数 `rotation_distance_rad`；第一对圆括号列出形参，逗号负责分隔：`left: np.ndarray` 用冒号给参数加类型提示；`right: np.ndarray` 用冒号给参数加类型提示；`-> float` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `rotation_distance_rad(left: np.ndarray, right: np.ndarray)`；调用者把参数交给它完成“旋转、四元数和旋转距离的数学工具”，后面的缩进代码是具体实现。
def rotation_distance_rad(left: np.ndarray, right: np.ndarray) -> float:
# 【L0346】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Return the geodesic angle between two 3x3 rotation matrices.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Return the geodesic angle between two 3x3 rotation matrices."""
# 【L0347】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0348】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cosine`。右侧语法为：表达式 `0.5 * (np.trace(left.T @ right) - 1.0)` 使用运算符 `-`, `*`, `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `cosine`，它在本项目中表示本功能块中的 `cosine` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `0.5 * (np.trace(left.T @ right) - 1.0)`；`trace` 表示本功能块中的 `trace` 值；`left` 表示本功能块中的 `left` 值；`T` 表示本功能块中的 `T` 值。
    cosine = 0.5 * (np.trace(left.T @ right) - 1.0)
# 【L0349】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.arccos(np.clip(cosine, -1.0, 1.0))`。
# 【项目含义】结束当前函数并把 `float(np.arccos(np.clip(cosine, -1.0, 1.0)))` 交回调用者；这个值的含义是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
    return float(np.arccos(np.clip(cosine, -1.0, 1.0)))
# 【L0350】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

# 【L0351】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“旋转、四元数和旋转距离的数学工具”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“旋转、四元数和旋转距离的数学工具”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 6：选择连续 IK 分支并规划不跳变的笛卡尔路径（源码第 352-465 行）

### 5.A 数据流位置

- 上游：模块 5“旋转、四元数和旋转距离的数学工具”。
- 本模块：选择连续 IK 分支并规划不跳变的笛卡尔路径。
- 下游：处理结果继续交给模块 7“把 link 局部点转换到世界坐标”。

### 5.B 为什么需要这一组代码

这一组负责“选择连续 IK 分支并规划不跳变的笛卡尔路径”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `lula`：NVIDIA Lula 运动学求解器实例。
- `passed`：当前单条任务或整套评测是否满足所有硬性门槛。

### 5.D 本模块首次阅读要认识的调用

- `closest_equivalent_rm65_solution(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `lula.compute_forward_kinematics(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `solution.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `bases.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `joint_values.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。
- `itertools.product(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.linalg.norm(...)`：圆括号表示真正执行调用；计算向量长度/欧氏距离。
- `rotation_distance_rad(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.abs(...)`：圆括号表示真正执行调用；逐元素取绝对值。
- `valid.append(...)`：圆括号表示真正执行调用；把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序。

### 5.E 本模块定义的新函数

### 函数卡：`closest_equivalent_rm65_solution()`（第 352-403 行）

- 定义了什么：选择连续 IK 分支并规划不跳变的笛卡尔路径。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`lula`：类型 `LulaKinematicsSolver`；项目含义是NVIDIA Lula 运动学求解器实例；`solution`：类型 `np.ndarray`；项目含义是本功能块中的 `solution` 值；`reference`：类型 `np.ndarray`；项目含义是本功能块中的 `reference` 值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`selected.copy()`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1322` 的 `grasp_arm = closest_equivalent_rm65_solution(`；`run_pick_place_baseline.py:1444` 的 `lift_arm = closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)`；`run_pick_place_baseline.py:1468` 的 `release_clear_arm = closest_equivalent_rm65_solution(`；`run_pick_place_baseline.py:451` 的 `command_solution = closest_equivalent_rm65_solution(`；`run_pick_place_baseline.py:1519` 的 `place_solution = closest_equivalent_rm65_solution(`

### 函数卡：`require_continuous_joint_step()`（第 406-417 行）

- 定义了什么：选择连续 IK 分支并规划不跳变的笛卡尔路径。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`start`：类型 `np.ndarray`；项目含义是本功能块中的 `start` 值；`target`：类型 `np.ndarray`；项目含义是目标相关值；`label`（仅关键字）：类型 `str`；项目含义是本功能块中的 `label` 值；`max_step_rad`（仅关键字）：类型 `float`，默认 `0.75`；项目含义是步相关值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:1445` 的 `require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")`；`run_pick_place_baseline.py:1471` 的 `require_continuous_joint_step(`；`run_pick_place_baseline.py:1522` 的 `require_continuous_joint_step(`

### 函数卡：`solve_continuous_cartesian_path()`（第 420-463 行）

- 定义了什么：选择连续 IK 分支并规划不跳变的笛卡尔路径。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`lula`：类型 `LulaKinematicsSolver`；项目含义是NVIDIA Lula 运动学求解器实例；`target_positions`：类型 `list[np.ndarray]`；项目含义是目标相关值；`target_orientation`：类型 `np.ndarray`；项目含义是目标相关值；`numerical_seed`：类型 `np.ndarray`；项目含义是本功能块中的 `numerical_seed` 值；`command_reference`：类型 `np.ndarray`；项目含义是控制命令相关值；`max_step_rad`（仅关键字）：类型 `float`，默认 `0.75`；项目含义是步相关值
- 返回类型标注：`tuple[np.ndarray, list[np.ndarray], float] | None`。
- 函数体实际 return：`(raw_seed.copy(), commands, path_max_step)`；`None`；`None`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1547` 的 `retreat_result = solve_continuous_cartesian_path(`；`run_pick_place_baseline.py:1396` 的 `candidate_retreat = solve_continuous_cartesian_path(`


### 5.F 这一模块的版本变化

- 当前第 415-415 行相对旧教学快照发生 `replace`：旧版 1 行，当前 1 行。 旧代码摘录：`raise RuntimeError(` 当前代码摘录：`raise UnsafeIKBranchJumpError(`

### 5.G 逐行精读

```python
# 【L0352】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `closest_equivalent_rm65_solution(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def closest_equivalent_rm65_solution(
# 【L0353】语法拆解：`lula` 是参数/字段名；冒号 `:` 添加类型提示 `LulaKinematicsSolver`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `lula`，类型提示为 `LulaKinematicsSolver`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
    lula: LulaKinematicsSolver,
# 【L0354】语法拆解：`solution` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `solution`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `solution` 值。
    solution: np.ndarray,
# 【L0355】语法拆解：`reference` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `reference`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `reference` 值。
    reference: np.ndarray,
# 【L0356】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> np.ndarray:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> np.ndarray:
# 【L0357】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Choose an FK-equivalent RM65 wrist branch nearest to ``reference``.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Choose an FK-equivalent RM65 wrist branch nearest to ``reference``.
# 【L0358】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0359】语法拆解：表达式 `Lula may return a spherical-wrist equivalent such as` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `Lula may return a spherical-wrist equivalent such as`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    Lula may return a spherical-wrist equivalent such as
# 【L0360】语法拆解：表达式 ```(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating` 使用运算符 `+`, `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 ```(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    ``(q4 + pi, -q5, q6 + pi)`` or a q6 value shifted by 2*pi.  Interpolating
# 【L0361】语法拆解：表达式 `directly between those representations can command a multi-radian jump` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `directly between those representations can command a multi-radian jump`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    directly between those representations can command a multi-radian jump
# 【L0362】语法拆解：`even though the Cartesian poses are adjacent.  Enumerate only known` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `even though the Cartesian poses are adjacent.  Enumerate only known`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    even though the Cartesian poses are adjacent.  Enumerate only known
# 【L0363】语法拆解：`equivalent representations, verify each with FK, and keep the one with` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】继续说明字符串，原文是 `equivalent representations, verify each with FK, and keep the one with`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    equivalent representations, verify each with FK, and keep the one with
# 【L0364】语法拆解：表达式 `the smallest joint-space jump.` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】继续说明字符串，原文是 `the smallest joint-space jump.`；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    the smallest joint-space jump.
# 【L0365】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】继续说明字符串，原文是 ``；这段文字在解释“选择连续 IK 分支并规划不跳变的笛卡尔路径”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0366】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0367】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `solution`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `solution`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `solution`，它在本项目中表示本功能块中的 `solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `solution, dtype=np.float64`（本功能块中的 `solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    solution = np.asarray(solution, dtype=np.float64)
# 【L0368】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `reference`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `reference`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `reference`，它在本项目中表示本功能块中的 `reference` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `reference, dtype=np.float64`（本功能块中的 `reference, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    reference = np.asarray(reference, dtype=np.float64)
# 【L0369】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_position, target_rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `solution`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `target_position, target_rotation`；`target_position` 表示目标、位置相关值；`target_rotation` 表示目标、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    target_position, target_rotation = lula.compute_forward_kinematics("link_6", solution)
# 【L0370】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0371】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `bases`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `bases`，它在本项目中表示本功能块中的 `bases` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    bases = [solution.copy()]
# 【L0372】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_flip`。右侧语法为：`solution` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `wrist_flip`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    wrist_flip = solution.copy()
# 【L0373】语法拆解：表达式 `wrist_flip[3] += np.pi` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `wrist_flip[3] + np.pi` 更新 `wrist_flip[3]` 原值；`wrist_flip[3]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[3] += np.pi
# 【L0374】语法拆解：表达式 `wrist_flip[4] *= -1.0` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `wrist_flip[4] * -1.0` 更新 `wrist_flip[4]` 原值；`wrist_flip[4]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[4] *= -1.0
# 【L0375】语法拆解：表达式 `wrist_flip[5] += np.pi` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `wrist_flip[5] + np.pi` 更新 `wrist_flip[5]` 原值；`wrist_flip[5]` 表示腕部相机相关值，常用于累计步数、距离、损失或成功次数。
    wrist_flip[5] += np.pi
# 【L0376】语法拆解：`bases` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_flip`。
# 【项目含义】对 `bases` 执行 `append`，把 `wrist_flip` 加入已有结果；该集合表示本功能块中的 `bases` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    bases.append(wrist_flip)
# 【L0377】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0378】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `valid: list[tuple[float, float, np.ndarray]]`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `valid`，它在本项目中表示本功能块中的 `valid` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    valid: list[tuple[float, float, np.ndarray]] = []
# 【L0379】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `bases`，每次把当前元素放进 `base`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
    for base in bases:
# 【L0380】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_values`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `joint_values`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
        joint_values = []
# 【L0381】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(base)`，每次把当前元素放进 `index, value`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for index, value in enumerate(base):
# 【L0382】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `equivalents`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `equivalents`，它在本项目中表示本功能块中的 `equivalents` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            equivalents = [
# 【L0383】语法拆解：表达式 `value + turns * 2.0 * np.pi` 使用运算符 `+`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `value + turns * 2.0 * np.pi` 接入当前完整语句；`value` 表示本功能块中的 `value` 值；`turns` 表示本功能块中的 `turns` 值；`pi` 表示本功能块中的 `pi` 值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                value + turns * 2.0 * np.pi
# 【L0384】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for turns in (-1, 0, 1)` 中给出的序列，逐项完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                for turns in (-1, 0, 1)
# 【L0385】语法拆解：`if` 要求条件 `RM65_JOINT_LOWER_RAD[index] - 1e-9` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `RM65_JOINT_LOWER_RAD[index] - 1e-9` 是否成立；`RM65_JOINT_LOWER_RAD` 表示RM65 机械约束或项目常量；`index` 表示索引相关值
                if RM65_JOINT_LOWER_RAD[index] - 1e-9
# 【L0386】语法拆解：表达式 `<= value + turns * 2.0 * np.pi` 使用运算符 `<=`, `+`, `*`, `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `<= value + turns * 2.0 * np.pi` 接入当前完整语句；`value` 表示本功能块中的 `value` 值；`turns` 表示本功能块中的 `turns` 值；`pi` 表示本功能块中的 `pi` 值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                <= value + turns * 2.0 * np.pi
# 【L0387】语法拆解：表达式 `<= RM65_JOINT_UPPER_RAD[index] + 1e-9` 使用运算符 `<=`, `+`, `-`, `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `<= RM65_JOINT_UPPER_RAD[index] + 1e-9` 接入当前完整语句；`RM65_JOINT_UPPER_RAD` 表示RM65 机械约束或项目常量；`index` 表示索引相关值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                <= RM65_JOINT_UPPER_RAD[index] + 1e-9
# 【L0388】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            ]
# 【L0389】语法拆解：`joint_values` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `equivalents`。
# 【项目含义】对 `joint_values` 执行 `append`，把 `equivalents` 加入已有结果；该集合表示关节相关值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            joint_values.append(equivalents)
# 【L0390】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `itertools.product(*joint_values)`，每次把当前元素放进 `values`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for values in itertools.product(*joint_values):
# 【L0391】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `values`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `candidate`，它在本项目中表示本功能块中的 `candidate` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `values, dtype=np.float64`（本功能块中的 `values, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
            candidate = np.asarray(values, dtype=np.float64)
# 【L0392】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position, rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `candidate`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `position, rotation`；`position` 表示位置相关值；`rotation` 表示旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
            position, rotation = lula.compute_forward_kinematics("link_6", candidate)
# 【L0393】语法拆解：`if` 要求条件 `np.linalg.norm(position - target_position) > 1e-5` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `np.linalg.norm(position - target_position) > 1e-5` 是否成立；`linalg` 表示本功能块中的 `linalg` 值；`norm` 表示本功能块中的 `norm` 值；`position` 表示位置相关值
            if np.linalg.norm(position - target_position) > 1e-5:
# 【L0394】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0395】语法拆解：`if` 要求条件 `rotation_distance_rad(rotation, target_rotation) > 1e-5` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `rotation_distance_rad(rotation, target_rotation) > 1e-5` 是否成立；`rotation_distance_rad` 表示旋转相关值；`rotation` 表示旋转相关值；`target_rotation` 表示目标、旋转相关值
            if rotation_distance_rad(rotation, target_rotation) > 1e-5:
# 【L0396】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0397】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `delta`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `abs` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `candidate - reference`。
# 【项目含义】得到 `delta`，它在本项目中表示本功能块中的 `delta` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.abs(candidate - reference)`；`abs` 表示本功能块中的 `abs` 值；`candidate` 表示本功能块中的 `candidate` 值；`reference` 表示本功能块中的 `reference` 值。
            delta = np.abs(candidate - reference)
# 【L0398】语法拆解：`valid` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(float(np.max(delta)), float(np.linalg.norm(delta)), candidate)`。
# 【项目含义】调用 `np.linalg.norm`：计算向量长度/欧氏距离；本行实际操作 `valid.append((float(np.max(delta)), float(np.linalg.norm(delta)), candidate))`。`valid` 表示本功能块中的 `valid` 值；`append` 表示本功能块中的 `append` 值。
            valid.append((float(np.max(delta)), float(np.linalg.norm(delta)), candidate))
# 【L0399】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0400】语法拆解：`if` 要求条件 `not valid` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not valid` 是否成立；`valid` 表示本功能块中的 `valid` 值
    if not valid:
# 【L0401】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("No FK-equivalent RM65 joint representation passed validation")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("No FK-equivalent RM65 joint representation passed validation")` 并停止当前路径；说明当前输入违反“选择连续 IK 分支并规划不跳变的笛卡尔路径”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("No FK-equivalent RM65 joint representation passed validation")
# 【L0402】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_, _, selected`。右侧语法为：`min` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `valid`；第 2 个实参 `key=lambda item: (item[0], item[1])`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `_, _, selected`；`_` 表示本功能块中的 `_` 值；`_` 表示本功能块中的 `_` 值；`selected` 表示本功能块中的 `selected` 值。右侧的来源是：计算表达式 `min(valid, key=lambda item: (item[0], item[1]))`；`valid` 表示本功能块中的 `valid` 值；`key` 表示本功能块中的 `key` 值；`lambda` 表示本功能块中的 `lambda` 值。
    _, _, selected = min(valid, key=lambda item: (item[0], item[1]))
# 【L0403】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`selected` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】结束当前函数并把 `selected.copy()` 交回调用者；这个值的含义是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    return selected.copy()
# 【L0404】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0405】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0406】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `require_continuous_joint_step(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def require_continuous_joint_step(
# 【L0407】语法拆解：`start` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `start`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `start` 值。
    start: np.ndarray,
# 【L0408】语法拆解：`target` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target: np.ndarray,
# 【L0409】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0410】语法拆解：`label` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `label`，类型提示为 `str`；在本项目中它表示本功能块中的 `label` 值。
    label: str,
# 【L0411】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_step_rad: float`。右侧语法为：`0.75` 是直接写在源码中的数值常量。
# 【项目含义】得到 `max_step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.75` 的结果保存下来，供当前功能块后续使用。
    max_step_rad: float = 0.75,
# 【L0412】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> None:
# 【L0413】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_step`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(np.asarray(target) - np.asarray(start)))`。
# 【项目含义】得到 `max_step`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `target) - np.asarray(start)))`（本功能块中的 `target) - np.asarray(start)))` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    max_step = float(np.max(np.abs(np.asarray(target) - np.asarray(start))))
# 【L0414】语法拆解：`if` 要求条件 `max_step > max_step_rad` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `max_step > max_step_rad` 是否成立；`max_step` 表示步相关值；`max_step_rad` 表示步相关值
    if max_step > max_step_rad:
# 【L0415】语法拆解：`raise` 主动制造并抛出异常；后面的 `UnsafeIKBranchJumpError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `UnsafeIKBranchJumpError(` 并停止当前路径；说明当前输入违反“选择连续 IK 分支并规划不跳变的笛卡尔路径”要求，不能继续进入仿真、训练或评测。
        raise UnsafeIKBranchJumpError(
# 【L0416】语法拆解：`f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把比较条件 `f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"` 接到上一行尚未结束的布尔表达式；`f` 表示本功能块中的 `f` 值；`unsafe` 表示本功能块中的 `unsafe` 值；`IK` 表示本功能块中的 `IK` 值。比较结果共同决定“选择连续 IK 分支并规划不跳变的笛卡尔路径”是否通过。
            f"unsafe IK branch jump for {label}: {max_step:.6f} rad > {max_step_rad:.6f} rad"
# 【L0417】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        )
# 【L0418】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0419】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0420】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `solve_continuous_cartesian_path(参数在后续行继续)`；调用者把参数交给它完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，后面的缩进代码是具体实现。
def solve_continuous_cartesian_path(
# 【L0421】语法拆解：`lula` 是参数/字段名；冒号 `:` 添加类型提示 `LulaKinematicsSolver`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `lula`，类型提示为 `LulaKinematicsSolver`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
    lula: LulaKinematicsSolver,
# 【L0422】语法拆解：`target_positions` 是参数/字段名；冒号 `:` 添加类型提示 `list[np.ndarray]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `target_positions: list[np.ndarray]`；`target_positions` 表示目标相关值；`ndarray` 表示本功能块中的 `ndarray` 值，它参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    target_positions: list[np.ndarray],
# 【L0423】语法拆解：`target_orientation` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target_orientation`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target_orientation: np.ndarray,
# 【L0424】语法拆解：`numerical_seed` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `numerical_seed`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `numerical_seed` 值。
    numerical_seed: np.ndarray,
# 【L0425】语法拆解：`command_reference` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `command_reference`，类型提示为 `np.ndarray`；在本项目中它表示控制命令相关值。
    command_reference: np.ndarray,
# 【L0426】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `*` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `*,` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
    *,
# 【L0427】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_step_rad: float`。右侧语法为：`0.75` 是直接写在源码中的数值常量。
# 【项目含义】得到 `max_step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.75` 的结果保存下来，供当前功能块后续使用。
    max_step_rad: float = 0.75,
# 【L0428】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> tuple[np.ndarray, list[np.ndarray], float] | None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
) -> tuple[np.ndarray, list[np.ndarray], float] | None:
# 【L0429】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Solve a path while keeping Lula's seed and the commanded branch separate.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Solve a path while keeping Lula's seed and the commanded branch separate."""
# 【L0430】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `raw_seed`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `numerical_seed`；第 2 个实参 `dtype=np.float64).copy(`。
# 【项目含义】得到 `raw_seed`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `numerical_seed, dtype=np.float64).copy(`（本功能块中的 `numerical_seed, dtype=np.float64).copy(` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    raw_seed = np.asarray(numerical_seed, dtype=np.float64).copy()
# 【L0431】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `command_reference`；第 2 个实参 `dtype=np.float64).copy(`。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `command_reference, dtype=np.float64).copy(`（控制命令相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    command = np.asarray(command_reference, dtype=np.float64).copy()
# 【L0432】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `commands: list[np.ndarray]`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】把右侧结果写进 `commands: list[np.ndarray]`（写入 `commands: list[np.ndarray]` 指定的字段）；右侧具体做的是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    commands: list[np.ndarray] = []
# 【L0433】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `path_max_step`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `path_max_step`，它在本项目中表示路径、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
    path_max_step = 0.0
# 【L0434】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `target_positions`，每次把当前元素放进 `target_position`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
    for target_position in target_positions:
# 【L0435】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `seeds`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `seeds`，它在本项目中表示本功能块中的 `seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[raw_seed]`；`raw_seed` 表示原始相关值。
        seeds = [raw_seed]
# 【L0436】语法拆解：`if` 要求条件 `not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0)` 是否成立；`allclose` 表示本功能块中的 `allclose` 值；`raw_seed` 表示原始相关值；`command` 表示控制命令相关值
        if not np.allclose(raw_seed, command, atol=1e-9, rtol=0.0):
# 【L0437】语法拆解：`seeds` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `command`。
# 【项目含义】对 `seeds` 执行 `append`，把 `command` 加入已有结果；该集合表示本功能块中的 `seeds` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            seeds.append(command)
# 【L0438】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidates: list[tuple[float, np.ndarray, np.ndarray]]`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `candidates`，它在本项目中表示本功能块中的 `candidates` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
        candidates: list[tuple[float, np.ndarray, np.ndarray]] = []
# 【L0439】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `seeds`，每次把当前元素放进 `seed`；这会逐个处理“选择连续 IK 分支并规划不跳变的笛卡尔路径”所需的帧、episode、动作或实验 case。
        for seed in seeds:
# 【L0440】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `raw_solution, success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `raw_solution, success`；`raw_solution` 表示原始相关值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
            raw_solution, success = lula.compute_inverse_kinematics(
# 【L0441】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的帮助说明、错误原因、任务名称或报告文字。
                "link_6",
# 【L0442】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_position`；在本项目中它表示目标、位置相关值。
                target_position,
# 【L0443】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_orientation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_orientation`；在本项目中它表示目标相关值。
                target_orientation,
# 【L0444】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `seed`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                warm_start=seed,
# 【L0445】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                position_tolerance=1e-4,
# 【L0446】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `orientation_tolerance`。右侧语法为：`1e-3` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
                orientation_tolerance=1e-3,
# 【L0447】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0448】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
            if not success:
# 【L0449】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中不满足继续条件。
                continue
# 【L0450】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `raw_solution`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `raw_solution`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `raw_solution`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `raw_solution, dtype=np.float64`（原始相关值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
            raw_solution = np.asarray(raw_solution, dtype=np.float64)
# 【L0451】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command_solution`。右侧语法为：`closest_equivalent_rm65_solution(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `command_solution`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
            command_solution = closest_equivalent_rm65_solution(
# 【L0452】语法拆解：`lula, raw_solution, command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `lula, raw_solution, command` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`raw_solution` 表示原始相关值；`command` 表示控制命令相关值。在“选择连续 IK 分支并规划不跳变的笛卡尔路径”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                lula, raw_solution, command
# 【L0453】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            )
# 【L0454】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `step_rad`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(command_solution - command))`。
# 【项目含义】得到 `step_rad`，它在本项目中表示步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(np.max(np.abs(command_solution - command)))`；`abs` 表示本功能块中的 `abs` 值；`command_solution` 表示控制命令相关值；`command` 表示控制命令相关值。
            step_rad = float(np.max(np.abs(command_solution - command)))
# 【L0455】语法拆解：`candidates` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(step_rad, raw_solution, command_solution)`。
# 【项目含义】对 `candidates` 执行 `append`，把 `(step_rad, raw_solution, command_solution)` 加入已有结果；该集合表示本功能块中的 `candidates` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
            candidates.append((step_rad, raw_solution, command_solution))
# 【L0456】语法拆解：`if` 要求条件 `not candidates` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not candidates` 是否成立；`candidates` 表示本功能块中的 `candidates` 值
        if not candidates:
# 【L0457】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            return None
# 【L0458】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `step_rad, raw_seed, command`。右侧语法为：`min` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `candidates`；第 2 个实参 `key=lambda item: item[0]`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `step_rad, raw_seed, command`；`step_rad` 表示步相关值；`raw_seed` 表示原始相关值；`command` 表示控制命令相关值。右侧的来源是：计算表达式 `min(candidates, key=lambda item: item[0])`；`candidates` 表示本功能块中的 `candidates` 值；`key` 表示本功能块中的 `key` 值；`lambda` 表示本功能块中的 `lambda` 值。
        step_rad, raw_seed, command = min(candidates, key=lambda item: item[0])
# 【L0459】语法拆解：`if` 要求条件 `step_rad > max_step_rad` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `step_rad > max_step_rad` 是否成立；`step_rad` 表示步相关值；`max_step_rad` 表示步相关值
        if step_rad > max_step_rad:
# 【L0460】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】结束当前函数并把 `None` 交回调用者；这个值的含义是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            return None
# 【L0461】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `path_max_step`。右侧语法为：`max` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `path_max_step`；第 2 个实参 `step_rad`。
# 【项目含义】得到 `path_max_step`，它在本项目中表示路径、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(path_max_step, step_rad)`；`path_max_step` 表示路径、步相关值；`step_rad` 表示步相关值。
        path_max_step = max(path_max_step, step_rad)
# 【L0462】语法拆解：`commands` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `command.copy()`。
# 【项目含义】对 `commands` 执行 `append`，把 `command.copy()` 加入已有结果；该集合表示本功能块中的 `commands` 值，随后会用于“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
        commands.append(command.copy())
# 【L0463】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`raw_seed.copy(), commands, path_max_step` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `raw_seed.copy(), commands, path_max_step` 交回调用者；这个值的含义是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    return raw_seed.copy(), commands, path_max_step
# 【L0464】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

# 【L0465】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“选择连续 IK 分支并规划不跳变的笛卡尔路径”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“选择连续 IK 分支并规划不跳变的笛卡尔路径”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 7：把 link 局部点转换到世界坐标（源码第 466-488 行）

### 5.A 数据流位置

- 上游：模块 6“选择连续 IK 分支并规划不跳变的笛卡尔路径”。
- 本模块：把 link 局部点转换到世界坐标。
- 下游：处理结果继续交给模块 8“从仿真同步采样状态、动作、外部/腕部相机图像”。

### 5.B 为什么需要这一组代码

这一组负责“把 link 局部点转换到世界坐标”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。

### 5.D 本模块首次阅读要认识的调用

- `tip_world_position(...)`：圆括号表示真正执行调用；读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。
- `index(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `torch.tensor(...)`：圆括号表示真正执行调用；PyTorch 的 `tensor` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `unsqueeze(...)`：圆括号表示真正执行调用；在指定位置增加一个长度为 1 的维度，常把单个样本变成 batch。
- `math_utils.quat_apply(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `body_world_position(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `local_point_world_position(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.E 本模块定义的新函数

### 函数卡：`tip_world_position()`（第 466-471 行）

- 定义了什么：把 link 局部点转换到世界坐标。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`body_name`：类型 `str`；项目含义是刚体相关值
- 返回类型标注：`torch.Tensor`。
- 函数体实际 return：`robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(robot.data.body_quat_w[0, body_id].unsqueeze(0), local)[0]`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1936` 的 `tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")`；`run_pick_place_baseline.py:1936` 的 `tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")`；`run_pick_place_baseline.py:1992` 的 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`；`run_pick_place_baseline.py:1992` 的 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`；`run_pick_place_baseline.py:2334` 的 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`

### 函数卡：`body_world_position()`（第 474-476 行）

- 定义了什么：把 link 局部点转换到世界坐标。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`body_name`：类型 `str`；项目含义是刚体相关值
- 返回类型标注：`torch.Tensor`。
- 函数体实际 return：`robot.data.body_pos_w[0, body_id]`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1981` 的 `closed_link_6_position = body_world_position(robot, "link_6").clone()`；`run_pick_place_baseline.py:2114` 的 `lifted_link_6_position = body_world_position(robot, "link_6").clone()`；`run_pick_place_baseline.py:2199` 的 `pre_place_link_6_position = body_world_position(robot, "link_6").clone()`；`run_pick_place_baseline.py:2223` 的 `place_actual_link_6_position = body_world_position(robot, "link_6").clone()`

### 函数卡：`local_point_world_position()`（第 479-486 行）

- 定义了什么：把 link 局部点转换到世界坐标。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`body_name`：类型 `str`；项目含义是刚体相关值；`local_position`：类型 `tuple[float, float, float]`；项目含义是位置相关值
- 返回类型标注：`torch.Tensor`。
- 函数体实际 return：`robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(robot.data.body_quat_w[0, body_id].unsqueeze(0), local)[0]`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1944` 的 `body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()`；`run_pick_place_baseline.py:1983` 的 `body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0466】语法拆解：`def` 定义函数 `tip_world_position`；第一对圆括号列出形参，逗号负责分隔：`robot: Articulation` 用冒号给参数加类型提示；`body_name: str` 用冒号给参数加类型提示；`-> torch.Tensor` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `tip_world_position(robot: Articulation, body_name: str)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0467】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `body_id`。右侧语法为：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.body_names).index(body_name`。
# 【项目含义】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0468】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `TIP_LOCAL_POINTS[body_name]`；第 2 个实参 `device=robot.device).unsqueeze(0`；其中 `TIP_LOCAL_POINTS[body_name]` 的方括号表示先从 `TIP_LOCAL_POINTS` 按键/索引 `body_name` 取值。
# 【项目含义】得到 `local`，它在本项目中表示本功能块中的 `local` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)`；`tensor` 表示本功能块中的 `tensor` 值；`TIP_LOCAL_POINTS` 表示本功能块中的 `TIP_LOCAL_POINTS` 值；`body_name` 表示刚体相关值。
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
# 【L0469】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】结束当前函数并把 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0470】语法拆解：`robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0471】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“把 link 局部点转换到世界坐标”。
    )[0]
# 【L0472】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0473】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0474】语法拆解：`def` 定义函数 `body_world_position`；第一对圆括号列出形参，逗号负责分隔：`robot: Articulation` 用冒号给参数加类型提示；`body_name: str` 用冒号给参数加类型提示；`-> torch.Tensor` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `body_world_position(robot: Articulation, body_name: str)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def body_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
# 【L0475】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `body_id`。右侧语法为：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.body_names).index(body_name`。
# 【项目含义】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0476】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`robot.data.body_pos_w[0, body_id]` 使用方括号索引；先计算 `0, body_id`，再从 `robot.data.body_pos_w` 取对应字典字段或数组元素。
# 【项目含义】结束当前函数并把 `robot.data.body_pos_w[0, body_id]` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id]
# 【L0477】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0478】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0479】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `local_point_world_position(参数在后续行继续)`；调用者把参数交给它完成“把 link 局部点转换到世界坐标”，后面的缩进代码是具体实现。
def local_point_world_position(
# 【L0480】语法拆解：`robot` 是参数/字段名；冒号 `:` 添加类型提示 `Articulation, body_name: str, local_position: tuple[float, float, float]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `robot: Articulation, body_name: str, local_position: tuple[float, float, float]` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`Articulation` 表示本功能块中的 `Articulation` 值；`body_name` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    robot: Articulation, body_name: str, local_position: tuple[float, float, float]
# 【L0481】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> torch.Tensor:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“把 link 局部点转换到世界坐标”。
) -> torch.Tensor:
# 【L0482】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `body_id`。右侧语法为：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.body_names).index(body_name`。
# 【项目含义】得到 `body_id`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.body_names).index(body_name)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_names` 表示刚体相关值。
    body_id = list(robot.data.body_names).index(body_name)
# 【L0483】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `local`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `local_position`；第 2 个实参 `device=robot.device).unsqueeze(0`。
# 【项目含义】得到 `local`，它在本项目中表示本功能块中的 `local` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor(local_position, device=robot.device).unsqueeze(0)`；`tensor` 表示本功能块中的 `tensor` 值；`local_position` 表示位置相关值；`device` 表示本功能块中的 `device` 值。
    local = torch.tensor(local_position, device=robot.device).unsqueeze(0)
# 【L0484】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】结束当前函数并把 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(` 交回调用者；这个值的含义是：计算表达式 `robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
# 【L0485】语法拆解：`robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `robot.data.body_quat_w[0, body_id].unsqueeze(0), local` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。在“把 link 局部点转换到世界坐标”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
# 【L0486】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“把 link 局部点转换到世界坐标”。
    )[0]
# 【L0487】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

# 【L0488】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“把 link 局部点转换到世界坐标”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“把 link 局部点转换到世界坐标”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 8：从仿真同步采样状态、动作、外部/腕部相机图像（源码第 489-630 行）

### 5.A 数据流位置

- 上游：模块 7“把 link 局部点转换到世界坐标”。
- 本模块：从仿真同步采样状态、动作、外部/腕部相机图像。
- 下游：处理结果继续交给模块 9“平滑移动和保持姿态的物理步进器”。

### 5.B 为什么需要这一组代码

这一组负责“从仿真同步采样状态、动作、外部/腕部相机图像”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `external_rgb`：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
- `wrist_rgb`：随末端移动的腕部相机 RGB 图像。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `output`：输出文件路径。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `usd`：Isaac Sim 实际加载的 RM65+4C2 USD 资产路径。

### 5.D 本模块首次阅读要认识的调用

- `__init__(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `_rgb(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。
- `numpy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `np.clip(...)`：圆括号表示真正执行调用；把数值限制在给定上下界内。
- `astype(...)`：圆括号表示真正执行调用；把 NumPy 数组元素转换到指定 dtype，例如把像素转成 uint8。
- `_image_ready(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `_render_images(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `torch.tensor(...)`：圆括号表示真正执行调用；PyTorch 的 `tensor` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `torch.nn.functional.normalize(...)`：圆括号表示真正执行调用；PyTorch 的 `normalize` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。

### 5.E 本模块定义的新函数

### 函数卡：`ExpertEpisodeCapture.__init__()`（第 492-519 行）

- 定义了什么：从仿真同步采样状态、动作、外部/腕部相机图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`recorder`：类型 `EpisodeRecorder`；项目含义是本功能块中的 `recorder` 值；`arm_ids`：类型 `list[int]`；项目含义是本功能块中的 `arm_ids` 值；`gripper_master_id`：类型 `int`；项目含义是夹爪相关值；`stride_steps`：类型 `int`；项目含义是步数相关值；`physics_dt`：类型 `float`；项目含义是本功能块中的 `physics_dt` 值；`sim`：类型 `SimulationContext`；项目含义是IsaacLab SimulationContext，负责物理时间步；`external_camera`：类型 `Camera | None`，默认 `None`；项目含义是外部相机相关值；`wrist_camera`：类型 `Camera | None`，默认 `None`；项目含义是腕部相机相关值；`wrist_tool_body_id`：类型 `int | None`，默认 `None`；项目含义是腕部相机、刚体相关值；`reset_renderer_accumulation`：类型 `bool`，默认 `False`；项目含义是本功能块中的 `reset_renderer_accumulation` 值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的调用：本文件内没有直接调用；它是脚本入口、回调，或由其他环境/框架按接口调用。

### 函数卡：`ExpertEpisodeCapture._rgb()`（第 522-526 行）

- 定义了什么：从仿真同步采样状态、动作、外部/腕部相机图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`camera`：类型 `Camera`；项目含义是本功能块中的 `camera` 值
- 返回类型标注：`np.ndarray`。
- 函数体实际 return：`image`
- 项目中的实际调用位置：`run_pick_place_baseline.py:580` 的 `external_rgb = self._rgb(self.external_camera)`；`run_pick_place_baseline.py:581` 的 `wrist_rgb = self._rgb(self.wrist_camera)`

### 函数卡：`ExpertEpisodeCapture._image_ready()`（第 529-537 行）

- 定义了什么：从仿真同步采样状态、动作、外部/腕部相机图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`image`：类型 `np.ndarray`；项目含义是图像相关值
- 返回类型标注：`bool`。
- 函数体实际 return：`image.ndim == 3 and image.shape[0] > 0 and (image.shape[1] > 0) and (image.shape[2] == 3)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:583` 的 `if self._image_ready(external_rgb) and self._image_ready(wrist_rgb):`；`run_pick_place_baseline.py:583` 的 `if self._image_ready(external_rgb) and self._image_ready(wrist_rgb):`

### 函数卡：`ExpertEpisodeCapture._render_images()`（第 539-588 行）

- 定义了什么：从仿真同步采样状态、动作、外部/腕部相机图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube`：类型 `RigidObject`；项目含义是IsaacLab RigidObject；本任务被抓取和放置的方块
- 返回类型标注：`tuple[np.ndarray, np.ndarray]`。
- 函数体实际 return：`(external_rgb, wrist_rgb)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:757` 的 `external_rgb, wrist_rgb = episode_capture._render_images(robot, cube)`；`run_pick_place_baseline.py:616` 的 `external_rgb, wrist_rgb = self._render_images(robot, cube)`

### 函数卡：`ExpertEpisodeCapture.before_step()`（第 590-628 行）

- 定义了什么：从仿真同步采样状态、动作、外部/腕部相机图像。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`self`：当前对象，由 Python 自动传入；`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube`：类型 `RigidObject`；项目含义是IsaacLab RigidObject；本任务被抓取和放置的方块；`target_state`：类型 `torch.Tensor`；项目含义是目标、状态相关值；`phase`：类型 `str`；项目含义是本功能块中的 `phase` 值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:651` 的 `capture.before_step(robot, cube, state, phase)`；`run_pick_place_baseline.py:674` 的 `capture.before_step(robot, cube, state, phase)`；`run_pick_place_baseline.py:883` 的 `episode_capture.before_step(`


### 5.F 这一模块的版本变化

- 当前第 503-503 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`reset_renderer_accumulation: bool = False,`
- 当前第 514-514 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`self.reset_renderer_accumulation = reset_renderer_accumulation`
- 当前第 517-518 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`self.last_wrist_eye: torch.Tensor | None = None` / `self.last_wrist_forward: torch.Tensor | None = None`
- 当前第 564-565 行相对旧教学快照发生 `insert`：旧版 0 行，当前 2 行。 当前代码摘录：`self.last_wrist_eye = eye.detach().clone()` / `self.last_wrist_forward = forward.detach().clone()`
- 当前第 569-571 行相对旧教学快照发生 `insert`：旧版 0 行，当前 3 行。 当前代码摘录：`if self.reset_renderer_accumulation:` / `omni.usd.get_context().reset_renderer_accumulation()`

### 5.G 逐行精读

```python
# 【L0489】语法拆解：`class` 定义类 `ExpertEpisodeCapture`；圆括号若存在就写父类；末尾冒号打开类体，下面缩进的字段和方法都属于它。
# 【项目含义】定义 `ExpertEpisodeCapture` 类并继承 `object`；它把“从仿真同步采样状态、动作、外部/腕部相机图像”所需的数据和方法包装成 OpenPI/IsaacLab 能复用的对象。
class ExpertEpisodeCapture:
# 【L0490】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Sample observations and the action targets applied on the next physics step.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Sample observations and the action targets applied on the next physics step."""
# 【L0491】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0492】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `__init__(参数在后续行继续)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def __init__(
# 【L0493】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`self` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0494】语法拆解：`recorder` 是参数/字段名；冒号 `:` 添加类型提示 `EpisodeRecorder`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `recorder`，类型提示为 `EpisodeRecorder`；在本项目中它表示本功能块中的 `recorder` 值。
        recorder: EpisodeRecorder,
# 【L0495】语法拆解：`arm_ids` 是参数/字段名；冒号 `:` 添加类型提示 `list[int]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `arm_ids: list[int]`；`arm_ids` 表示本功能块中的 `arm_ids` 值，它参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
        arm_ids: list[int],
# 【L0496】语法拆解：`gripper_master_id` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `gripper_master_id`，类型提示为 `int`；在本项目中它表示夹爪相关值。
        gripper_master_id: int,
# 【L0497】语法拆解：`stride_steps` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `stride_steps`，类型提示为 `int`；在本项目中它表示步数相关值。
        stride_steps: int,
# 【L0498】语法拆解：`physics_dt` 是参数/字段名；冒号 `:` 添加类型提示 `float`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `physics_dt`，类型提示为 `float`；在本项目中它表示本功能块中的 `physics_dt` 值。
        physics_dt: float,
# 【L0499】语法拆解：`sim` 是参数/字段名；冒号 `:` 添加类型提示 `SimulationContext`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim: SimulationContext,
# 【L0500】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_camera: Camera | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        external_camera: Camera | None = None,
# 【L0501】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_camera: Camera | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_camera: Camera | None = None,
# 【L0502】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_tool_body_id: int | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_tool_body_id`，它在本项目中表示腕部相机、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        wrist_tool_body_id: int | None = None,
# 【L0503】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `reset_renderer_accumulation: bool`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `reset_renderer_accumulation`，它在本项目中表示本功能块中的 `reset_renderer_accumulation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
        reset_renderer_accumulation: bool = False,
# 【L0504】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0505】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.recorder`。右侧语法为：`recorder` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `recorder` 配置成 `recorder`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.recorder = recorder
# 【L0506】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.arm_ids`。右侧语法为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `arm_ids` 配置成 `arm_ids`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.arm_ids = arm_ids
# 【L0507】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.gripper_master_id`。右侧语法为：`gripper_master_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `gripper_master_id` 配置成 `gripper_master_id`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.gripper_master_id = gripper_master_id
# 【L0508】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.stride_steps`。右侧语法为：`stride_steps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `stride_steps` 配置成 `stride_steps`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.stride_steps = stride_steps
# 【L0509】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.physics_dt`。右侧语法为：`physics_dt` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `physics_dt` 配置成 `physics_dt`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.physics_dt = physics_dt
# 【L0510】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.sim`。右侧语法为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `sim` 配置成 `sim`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.sim = sim
# 【L0511】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.external_camera`。右侧语法为：`external_camera` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `external_camera` 配置成 `external_camera`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.external_camera = external_camera
# 【L0512】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_camera`。右侧语法为：`wrist_camera` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `wrist_camera` 配置成 `wrist_camera`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_camera = wrist_camera
# 【L0513】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_tool_body_id`。右侧语法为：`wrist_tool_body_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `wrist_tool_body_id` 配置成 `wrist_tool_body_id`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_tool_body_id = wrist_tool_body_id
# 【L0514】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.reset_renderer_accumulation`。右侧语法为：`reset_renderer_accumulation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `reset_renderer_accumulation` 配置成 `reset_renderer_accumulation`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.reset_renderer_accumulation = reset_renderer_accumulation
# 【L0515】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_local_offset: torch.Tensor | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_local_offset`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.wrist_local_offset: torch.Tensor | None = None
# 【L0516】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_local_forward: torch.Tensor | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_local_forward`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.wrist_local_forward: torch.Tensor | None = None
# 【L0517】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.last_wrist_eye: torch.Tensor | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `last_wrist_eye`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.last_wrist_eye: torch.Tensor | None = None
# 【L0518】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.last_wrist_forward: torch.Tensor | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `last_wrist_forward`，它在本项目中表示腕部相机相关值；保存到当前对象，供该对象的其他方法继续使用。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        self.last_wrist_forward: torch.Tensor | None = None
# 【L0519】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.sim_step`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】把 `self` 对象的 `sim_step` 配置成 `0`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.sim_step = 0
# 【L0520】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0521】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0522】语法拆解：`def` 定义函数 `_rgb`；第一对圆括号列出形参，逗号负责分隔：`camera: Camera` 用冒号给参数加类型提示；`-> np.ndarray` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `_rgb(camera: Camera)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _rgb(camera: Camera) -> np.ndarray:
# 【L0523】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image`。右侧语法为：`camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `image`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()`；`camera` 表示本功能块中的 `camera` 值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`output` 表示输出文件路径。
        image = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
# 【L0524】语法拆解：`if` 要求条件 `image.dtype != np.uint8` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `image.dtype != np.uint8` 是否成立；`image` 表示图像相关值；`dtype` 表示本功能块中的 `dtype` 值；`uint8` 表示本功能块中的 `uint8` 值
        if image.dtype != np.uint8:
# 【L0525】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `image`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `clip` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `image`；第 2 个实参 `0`；第 3 个实参 `255).astype(np.uint8`。
# 【项目含义】得到 `image`，它在本项目中表示图像相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把原值限制在给定下界和上界之间，避免关节、夹爪或像素超出允许范围。
            image = np.clip(image, 0, 255).astype(np.uint8)
# 【L0526】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`image` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `image` 交回调用者；这个值的含义是：计算表达式 `image`；`image` 表示图像相关值。
        return image
# 【L0527】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0528】语法拆解：行首 `@` 表示装饰器；它会在类/函数定义完成时包裹或改造下面那个类/函数。
# 【项目含义】声明下面的方法不读取 `self`；它只是借类名组织一个与实例状态无关的转换工具。
    @staticmethod
# 【L0529】语法拆解：`def` 定义函数 `_image_ready`；第一对圆括号列出形参，逗号负责分隔：`image: np.ndarray` 用冒号给参数加类型提示；`-> bool` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `_image_ready(image: np.ndarray)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _image_ready(image: np.ndarray) -> bool:
# 【L0530】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Return whether an Isaac camera produced a usable RGB frame.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
        """Return whether an Isaac camera produced a usable RGB frame."""
# 【L0531】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0532】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `(` 交回调用者；这个值的含义是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        return (
# 【L0533】语法拆解：表达式 `image.ndim == 3` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `image.ndim == 3` 接到上一行尚未结束的布尔表达式；`image` 表示图像相关值；`ndim` 表示本功能块中的 `ndim` 值。比较结果共同决定“从仿真同步采样状态、动作、外部/腕部相机图像”是否通过。
            image.ndim == 3
# 【L0534】语法拆解：表达式 `and image.shape[0] > 0` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `image.shape[0] > 0` 用“并且”接到上一行判断中；判断 `image.shape[0] > 0` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[0] > 0
# 【L0535】语法拆解：表达式 `and image.shape[1] > 0` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `image.shape[1] > 0` 用“并且”接到上一行判断中；判断 `image.shape[1] > 0` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[1] > 0
# 【L0536】语法拆解：表达式 `and image.shape[2] == 3` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `image.shape[2] == 3` 用“并且”接到上一行判断中；判断 `image.shape[2] == 3` 是否成立；`image` 表示图像相关值；`shape` 表示本功能块中的 `shape` 值。所有连接条件共同决定是否进入后续分支。
            and image.shape[2] == 3
# 【L0537】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0538】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0539】语法拆解：`def` 定义函数 `_render_images`；第一对圆括号列出形参，逗号负责分隔：`self` 指调用该方法的当前对象；`robot: Articulation` 用冒号给参数加类型提示；`cube: RigidObject` 用冒号给参数加类型提示；`-> tuple[np.ndarray, np.ndarray]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `_render_images(self, robot: Articulation, cube: RigidObject)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def _render_images(self, robot: Articulation, cube: RigidObject) -> tuple[np.ndarray, np.ndarray]:
# 【L0540】语法拆解：`if` 要求条件 `self.external_camera is None or self.wrist_camera is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `self.external_camera is None or self.wrist_camera is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.external_camera is None or self.wrist_camera is None:
# 【L0541】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("both cameras are required for image recording")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("both cameras are required for image recording")` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("both cameras are required for image recording")
# 【L0542】语法拆解：`if` 要求条件 `self.wrist_tool_body_id is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `self.wrist_tool_body_id is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.wrist_tool_body_id is None:
# 【L0543】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("wrist tool body id is required for image recording")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("wrist tool body id is required for image recording")` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("wrist tool body id is required for image recording")
# 【L0544】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `tool_position`。右侧语法为：`robot.data.body_pos_w[0, self.wrist_tool_body_id]` 使用方括号索引；先计算 `0, self.wrist_tool_body_id`，再从 `robot.data.body_pos_w` 取对应字典字段或数组元素。
# 【项目含义】得到 `tool_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.body_pos_w[0, self.wrist_tool_body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_pos_w` 表示刚体相关值。
        tool_position = robot.data.body_pos_w[0, self.wrist_tool_body_id]
# 【L0545】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `tool_quaternion`。右侧语法为：`robot.data.body_quat_w[0, self.wrist_tool_body_id]` 使用方括号索引；先计算 `0, self.wrist_tool_body_id`，再从 `robot.data.body_quat_w` 取对应字典字段或数组元素。
# 【项目含义】得到 `tool_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.body_quat_w[0, self.wrist_tool_body_id]`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`body_quat_w` 表示刚体相关值。
        tool_quaternion = robot.data.body_quat_w[0, self.wrist_tool_body_id]
# 【L0546】语法拆解：`if` 要求条件 `self.wrist_local_offset is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `self.wrist_local_offset is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if self.wrist_local_offset is None:
# 【L0547】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_offset`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[0.0, 0.15, 0.10]`；第 2 个实参 `device=robot.device`。
# 【项目含义】得到 `world_offset`，它在本项目中表示本功能块中的 `world_offset` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.tensor([0.0, 0.15, 0.10], device=robot.device)`；`tensor` 表示本功能块中的 `tensor` 值；`device` 表示本功能块中的 `device` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            world_offset = torch.tensor([0.0, 0.15, 0.10], device=robot.device)
# 【L0548】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `eye`。右侧语法为：表达式 `tool_position + world_offset` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `eye`，它在本项目中表示本功能块中的 `eye` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tool_position + world_offset`；`tool_position` 表示位置相关值；`world_offset` 表示本功能块中的 `world_offset` 值。
            eye = tool_position + world_offset
# 【L0549】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `world_forward`。右侧语法为：`torch.nn.functional` 是模块/对象，点号 `.` 从中取出 `normalize` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube.data.root_pos_w[0] - eye`；第 2 个实参 `dim=0`。
# 【项目含义】得到 `world_forward`，它在本项目中表示本功能块中的 `world_forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
            world_forward = torch.nn.functional.normalize(cube.data.root_pos_w[0] - eye, dim=0)
# 【L0550】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inverse_tool_quaternion`。右侧语法为：`math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `inverse_tool_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]`；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_conjugate` 表示本功能块中的 `quat_conjugate` 值；`tool_quaternion` 表示四元数相关值。
            inverse_tool_quaternion = math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]
# 【L0551】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_local_offset`。右侧语法为：`math_utils.quat_apply(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `wrist_local_offset` 配置成 `math_utils.quat_apply(`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_local_offset = math_utils.quat_apply(
# 【L0552】语法拆解：`inverse_tool_quaternion` 是模块/对象，点号 `.` 从中取出 `unsqueeze` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0)`；第 2 个实参 `world_offset.unsqueeze(0`。
# 【项目含义】对 `inverse_tool_quaternion` 调用 `unsqueeze(0), world_offset.unsqueeze(0)`：调用 `inverse_tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                inverse_tool_quaternion.unsqueeze(0), world_offset.unsqueeze(0)
# 【L0553】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )[0]
# 【L0554】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.wrist_local_forward`。右侧语法为：`math_utils.quat_apply(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `self` 对象的 `wrist_local_forward` 配置成 `math_utils.quat_apply(`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_local_forward = math_utils.quat_apply(
# 【L0555】语法拆解：`inverse_tool_quaternion` 是模块/对象，点号 `.` 从中取出 `unsqueeze` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0)`；第 2 个实参 `world_forward.unsqueeze(0`。
# 【项目含义】对 `inverse_tool_quaternion` 调用 `unsqueeze(0), world_forward.unsqueeze(0)`：调用 `inverse_tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                inverse_tool_quaternion.unsqueeze(0), world_forward.unsqueeze(0)
# 【L0556】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )[0]
# 【L0557】语法拆解：`assert self.wrist_local_forward is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】断言 `self.wrist_local_forward is not None` 必须成立；这是开发期内部一致性检查，失败说明“从仿真同步采样状态、动作、外部/腕部相机图像”此前产生了不可能的状态。
        assert self.wrist_local_forward is not None
# 【L0558】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `eye`。右侧语法为：表达式 `tool_position + math_utils.quat_apply(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `eye`，它在本项目中表示本功能块中的 `eye` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `tool_position + math_utils.quat_apply(`；`tool_position` 表示位置相关值；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_apply` 表示本功能块中的 `quat_apply` 值。
        eye = tool_position + math_utils.quat_apply(
# 【L0559】语法拆解：`tool_quaternion` 是模块/对象，点号 `.` 从中取出 `unsqueeze` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0)`；第 2 个实参 `self.wrist_local_offset.unsqueeze(0`。
# 【项目含义】对 `tool_quaternion` 调用 `unsqueeze(0), self.wrist_local_offset.unsqueeze(0)`：调用 `tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            tool_quaternion.unsqueeze(0), self.wrist_local_offset.unsqueeze(0)
# 【L0560】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )[0]
# 【L0561】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `forward`。右侧语法为：`math_utils.quat_apply(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `forward`，它在本项目中表示本功能块中的 `forward` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `math_utils.quat_apply(`；`math_utils` 表示本功能块中的 `math_utils` 值；`quat_apply` 表示本功能块中的 `quat_apply` 值。
        forward = math_utils.quat_apply(
# 【L0562】语法拆解：`tool_quaternion` 是模块/对象，点号 `.` 从中取出 `unsqueeze` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0)`；第 2 个实参 `self.wrist_local_forward.unsqueeze(0`。
# 【项目含义】对 `tool_quaternion` 调用 `unsqueeze(0), self.wrist_local_forward.unsqueeze(0)`：调用 `tool_quaternion` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            tool_quaternion.unsqueeze(0), self.wrist_local_forward.unsqueeze(0)
# 【L0563】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )[0]
# 【L0564】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.last_wrist_eye`。右侧语法为：`eye` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).clone(`。
# 【项目含义】把 `self` 对象的 `last_wrist_eye` 配置成 `eye.detach().clone()`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.last_wrist_eye = eye.detach().clone()
# 【L0565】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `self.last_wrist_forward`。右侧语法为：`forward` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).clone(`。
# 【项目含义】把 `self` 对象的 `last_wrist_forward` 配置成 `forward.detach().clone()`。`self` 在这里表示当前类实例；这个设置会影响“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.last_wrist_forward = forward.detach().clone()
# 【L0566】语法拆解：`self.wrist_camera.set_world_poses_from_view(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `self.wrist_camera` 调用多行方法 `set_world_poses_from_view`：调用 `self.wrist_camera` 提供的 `set_world_poses_from_view` 操作；具体参数写在随后几行，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        self.wrist_camera.set_world_poses_from_view(
# 【L0567】语法拆解：`eye` 是模块/对象，点号 `.` 从中取出 `unsqueeze` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0)`；第 2 个实参 `(eye + forward).unsqueeze(0`。
# 【项目含义】对 `eye` 调用 `unsqueeze(0), (eye + forward).unsqueeze(0)`：调用 `eye` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            eye.unsqueeze(0), (eye + forward).unsqueeze(0)
# 【L0568】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0569】语法拆解：`if` 要求条件 `self.reset_renderer_accumulation` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `self.reset_renderer_accumulation` 是否成立；`reset_renderer_accumulation` 表示本功能块中的 `reset_renderer_accumulation` 值
        if self.reset_renderer_accumulation:
# 【L0570】语法拆解：`omni.usd` 是模块/对象，点号 `.` 从中取出 `get_context` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).reset_renderer_accumulation(`。
# 【项目含义】对 `omni.usd` 调用 `get_context().reset_renderer_accumulation()`：调用 `omni.usd` 提供的 `get_context` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            omni.usd.get_context().reset_renderer_accumulation()
# 【L0571】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0572】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：Isaac Sim can expose an empty RGB tensor during the first few render
        # Isaac Sim can expose an empty RGB tensor during the first few render
# 【L0573】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：ticks after a headless camera starts.  Wait for real sensor frames
        # ticks after a headless camera starts.  Wait for real sensor frames
# 【L0574】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：instead of recording a fabricated image or aborting the episode.
        # instead of recording a fabricated image or aborting the episode.
# 【L0575】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `last_shapes: tuple[tuple[int, ...], tuple[int, ...]] | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `last_shapes`，它在本项目中表示本功能块中的 `last_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        last_shapes: tuple[tuple[int, ...], tuple[int, ...]] | None = None
# 【L0576】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(30)`，每次把当前元素放进 `_`；这会逐个处理“从仿真同步采样状态、动作、外部/腕部相机图像”所需的帧、episode、动作或实验 case。
        for _ in range(30):
# 【L0577】语法拆解：`self.sim` 是模块/对象，点号 `.` 从中取出 `render` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `self.sim` 调用 `render()`：调用 `self.sim` 提供的 `render` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.sim.render()
# 【L0578】语法拆解：`self.external_camera` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self.physics_dt`。
# 【项目含义】对 `self.external_camera` 执行 `update`，把 `self.physics_dt` 加入已有结果；该集合表示当前类实例，随后会用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.external_camera.update(self.physics_dt)
# 【L0579】语法拆解：`self.wrist_camera` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self.physics_dt`。
# 【项目含义】对 `self.wrist_camera` 执行 `update`，把 `self.physics_dt` 加入已有结果；该集合表示当前类实例，随后会用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.wrist_camera.update(self.physics_dt)
# 【L0580】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb`。右侧语法为：`self` 是模块/对象，点号 `.` 从中取出 `_rgb` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self.external_camera`。
# 【项目含义】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._rgb(self.external_camera)`；`_rgb` 表示本功能块中的 `_rgb` 值；`external_camera` 表示外部相机相关值。
            external_rgb = self._rgb(self.external_camera)
# 【L0581】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_rgb`。右侧语法为：`self` 是模块/对象，点号 `.` 从中取出 `_rgb` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `self.wrist_camera`。
# 【项目含义】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `self._rgb(self.wrist_camera)`；`_rgb` 表示本功能块中的 `_rgb` 值；`wrist_camera` 表示腕部相机相关值。
            wrist_rgb = self._rgb(self.wrist_camera)
# 【L0582】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `last_shapes`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】得到 `last_shapes`，它在本项目中表示本功能块中的 `last_shapes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(external_rgb.shape, wrist_rgb.shape)`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`shape` 表示本功能块中的 `shape` 值；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。
            last_shapes = (external_rgb.shape, wrist_rgb.shape)
# 【L0583】语法拆解：`if` 要求条件 `self._image_ready(external_rgb) and self._image_ready(wrist_rgb)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `self._image_ready(external_rgb) and self._image_ready(wrist_rgb)` 是否成立；`_image_ready` 表示图像相关值；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像
            if self._image_ready(external_rgb) and self._image_ready(wrist_rgb):
# 【L0584】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`external_rgb, wrist_rgb` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `external_rgb, wrist_rgb` 交回调用者；这个值的含义是：计算表达式 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。
                return external_rgb, wrist_rgb
# 【L0585】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“从仿真同步采样状态、动作、外部/腕部相机图像”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(
# 【L0586】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Isaac cameras did not produce usable RGB frames after 30 render ticks; "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“从仿真同步采样状态、动作、外部/腕部相机图像”中的帮助说明、错误原因、任务名称或报告文字。
            "Isaac cameras did not produce usable RGB frames after 30 render ticks; "
# 【L0587】语法拆解：`f"last shapes were {last_shapes}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"last shapes were {last_shapes}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`last` 表示本功能块中的 `last` 值；`shapes` 表示本功能块中的 `shapes` 值。在“从仿真同步采样状态、动作、外部/腕部相机图像”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            f"last shapes were {last_shapes}"
# 【L0588】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
        )
# 【L0589】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0590】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `before_step(参数在后续行继续)`；调用者把参数交给它完成“从仿真同步采样状态、动作、外部/腕部相机图像”，后面的缩进代码是具体实现。
    def before_step(
# 【L0591】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`self` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `self`；在本项目中它表示当前类实例。
        self,
# 【L0592】语法拆解：`robot` 是参数/字段名；冒号 `:` 添加类型提示 `Articulation`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot: Articulation,
# 【L0593】语法拆解：`cube` 是参数/字段名；冒号 `:` 添加类型提示 `RigidObject`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube: RigidObject,
# 【L0594】语法拆解：`target_state` 是参数/字段名；冒号 `:` 添加类型提示 `torch.Tensor`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target_state`，类型提示为 `torch.Tensor`；在本项目中它表示目标、状态相关值。
        target_state: torch.Tensor,
# 【L0595】语法拆解：`phase` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
        phase: str,
# 【L0596】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“从仿真同步采样状态、动作、外部/腕部相机图像”。
    ) -> None:
# 【L0597】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：The simulator data buffers are stale immediately after the initial
        # The simulator data buffers are stale immediately after the initial
# 【L0598】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：direct state write, so the first valid sample is taken after one
        # direct state write, so the first valid sample is taken after one
# 【L0599】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：complete stride of physics updates.
        # complete stride of physics updates.
# 【L0600】语法拆解：`if` 要求条件 `self.sim_step > 0 and self.sim_step % self.stride_steps == 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `self.sim_step > 0 and self.sim_step % self.stride_steps == 0` 是否成立；`sim_step` 表示仿真、步相关值；`stride_steps` 表示步数相关值
        if self.sim_step > 0 and self.sim_step % self.stride_steps == 0:
# 【L0601】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observed_arm`。右侧语法为：`robot.data.joint_pos[0, self.arm_ids].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `observed_arm`，它在本项目中表示本功能块中的 `observed_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
            observed_arm = robot.data.joint_pos[0, self.arm_ids].detach().cpu().numpy()
# 【L0602】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observed_gripper`。右侧语法为：`normalize_gripper(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `observed_gripper`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            observed_gripper = normalize_gripper(
# 【L0603】语法拆解：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_pos[0, self.gripper_master_id].item()`。
# 【项目含义】对 `float(robot.data.joint_pos[0, self.gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, self.gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                float(robot.data.joint_pos[0, self.gripper_master_id].item())
# 【L0604】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0605】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_arm`。右侧语法为：`target_state[0, self.arm_ids].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_state[0, self.arm_ids].detach().cpu().numpy()`；`target_state` 表示目标、状态相关值；`arm_ids` 表示本功能块中的 `arm_ids` 值；`detach` 表示本功能块中的 `detach` 值。
            target_arm = target_state[0, self.arm_ids].detach().cpu().numpy()
# 【L0606】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_gripper`。右侧语法为：`normalize_gripper(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_gripper`，它在本项目中表示目标、夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            target_gripper = normalize_gripper(
# 【L0607】语法拆解：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `target_state[0, self.gripper_master_id].item()`。
# 【项目含义】对 `float(target_state[0, self.gripper_master_id]` 调用 `item())`：调用 `float(target_state[0, self.gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
                float(target_state[0, self.gripper_master_id].item())
# 【L0608】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0609】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `concatenate` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[target_arm, [target_gripper]]`。
# 【项目含义】得到 `action`，它在本项目中表示动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把括号中的多个一维数组沿现有轴首尾连接；在本项目中常用于把六关节和一个夹爪值组成七维状态/动作。
            action = np.concatenate([target_arm, [target_gripper]])
# 【L0610】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose`。右侧语法为：`torch.cat(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.cat(`；`cat` 表示本功能块中的 `cat` 值。
            cube_pose = torch.cat(
# 【L0611】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_pos_w` 表示本功能块中的 `root_pos_w` 值，共同完成“从仿真同步采样状态、动作、外部/腕部相机图像”。
                [cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0
# 【L0612】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `detach().cpu().numpy()`：调用 `)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            ).detach().cpu().numpy()
# 【L0613】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `external_rgb`，它在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            external_rgb = None
# 【L0614】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_rgb`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_rgb`，它在本项目中表示随末端移动的腕部相机 RGB 图像；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
            wrist_rgb = None
# 【L0615】语法拆解：`if` 要求条件 `self.external_camera is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `self.external_camera is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if self.external_camera is not None:
# 【L0616】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb, wrist_rgb`。右侧语法为：`self` 是模块/对象，点号 `.` 从中取出 `_render_images` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `cube`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。右侧的来源是：计算表达式 `self._render_images(robot, cube)`；`_render_images` 表示本功能块中的 `_render_images` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                external_rgb, wrist_rgb = self._render_images(robot, cube)
# 【L0617】语法拆解：`self.recorder.add_frame(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `self.recorder` 调用多行方法 `add_frame`：调用 `self.recorder` 提供的 `add_frame` 操作；具体参数写在随后几行，用于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            self.recorder.add_frame(
# 【L0618】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `timestamp_s`。右侧语法为：表达式 `self.sim_step * self.physics_dt` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `timestamp_s` 传入 `self.sim_step * self.physics_dt`；该参数在本项目中表示本功能块中的 `timestamp_s` 值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                timestamp_s=self.sim_step * self.physics_dt,
# 【L0619】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim_step`。右侧语法为：`self` 是起始对象；每个点号 `.` 依次读取属性/成员：`sim_step`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `sim_step` 传入 `self.sim_step`；该参数在本项目中表示仿真、步相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                sim_step=self.sim_step,
# 【L0620】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `phase`。右侧语法为：`phase` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `phase` 传入 `phase`；该参数在本项目中表示本功能块中的 `phase` 值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                phase=phase,
# 【L0621】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_position_rad`。右侧语法为：`observed_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `joint_position_rad` 传入 `observed_arm`；该参数在本项目中表示关节、位置相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                joint_position_rad=observed_arm,
# 【L0622】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_position`。右侧语法为：`observed_gripper` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `gripper_position` 传入 `observed_gripper`；该参数在本项目中表示夹爪、位置相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                gripper_position=observed_gripper,
# 【L0623】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action`。右侧语法为：`action` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action` 传入 `action`；该参数在本项目中表示动作相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                action=action,
# 【L0624】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose_wxyz`。右侧语法为：`cube_pose` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cube_pose_wxyz` 传入 `cube_pose`；该参数在本项目中表示任务方块相关值，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                cube_pose_wxyz=cube_pose,
# 【L0625】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb`。右侧语法为：`external_rgb` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `external_rgb` 传入 `external_rgb`；该参数在本项目中表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                external_rgb=external_rgb,
# 【L0626】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_rgb`。右侧语法为：`wrist_rgb` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `wrist_rgb` 传入 `wrist_rgb`；该参数在本项目中表示随末端移动的腕部相机 RGB 图像，会参与“从仿真同步采样状态、动作、外部/腕部相机图像”。
                wrist_rgb=wrist_rgb,
# 【L0627】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“从仿真同步采样状态、动作、外部/腕部相机图像”。
            )
# 【L0628】语法拆解：表达式 `self.sim_step += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `self.sim_step + 1` 更新 `self.sim_step` 原值；`self.sim_step` 表示当前类实例，常用于累计步数、距离、损失或成功次数。
        self.sim_step += 1
# 【L0629】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

# 【L0630】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“从仿真同步采样状态、动作、外部/腕部相机图像”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“从仿真同步采样状态、动作、外部/腕部相机图像”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 9：平滑移动和保持姿态的物理步进器（源码第 631-683 行）

### 5.A 数据流位置

- 上游：模块 8“从仿真同步采样状态、动作、外部/腕部相机图像”。
- 本模块：平滑移动和保持姿态的物理步进器。
- 下游：处理结果继续交给模块 10“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。

### 5.B 为什么需要这一组代码

这一组负责“平滑移动和保持姿态的物理步进器”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。

### 5.D 本模块首次阅读要认识的调用

- `smooth_move(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `torch.as_tensor(...)`：圆括号表示真正执行调用；把 NumPy/列表转换成指定设备和类型的 Torch 张量。
- `robot.set_joint_position_target(...)`：圆括号表示真正执行调用；设置关节位置控制器的目标值。
- `capture.before_step(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `robot.write_data_to_sim(...)`：圆括号表示真正执行调用；把缓存的机器人命令提交给 PhysX。
- `cube.write_data_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim.step(...)`：圆括号表示真正执行调用；让 Isaac 物理世界向前推进一个时间步。
- `robot.update(...)`：圆括号表示真正执行调用；把仿真后的机器人状态刷新到 IsaacLab 缓冲区。
- `sim.get_physics_dt(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `cube.update(...)`：圆括号表示真正执行调用；把仿真后的方块状态刷新到 IsaacLab 缓冲区。
- `CONTACT_SENSORS.values(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `contact_sensor.update(...)`：圆括号表示真正执行调用；用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态。

### 5.E 本模块定义的新函数

### 函数卡：`smooth_move()`（第 631-659 行）

- 定义了什么：平滑移动和保持姿态的物理步进器。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`sim`：类型 `SimulationContext`；项目含义是IsaacLab SimulationContext，负责物理时间步；`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube`：类型 `RigidObject`；项目含义是IsaacLab RigidObject；本任务被抓取和放置的方块；`state`：类型 `torch.Tensor`；项目含义是当前要写给 articulation 的全部关节目标张量；`joint_ids`：类型 `list[int]`；项目含义是关节相关值；`start`：类型 `np.ndarray`；项目含义是本功能块中的 `start` 值；`target`：类型 `np.ndarray`；项目含义是目标相关值；`steps`：类型 `int`；项目含义是步数相关值；`phase`：类型 `str`；项目含义是本功能块中的 `phase` 值；`capture`：类型 `ExpertEpisodeCapture | None`，默认 `None`；项目含义是本功能块中的 `capture` 值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:1967` 的 `smooth_move(`；`run_pick_place_baseline.py:2109` 的 `smooth_move(`；`run_pick_place_baseline.py:2180` 的 `smooth_move(`；`run_pick_place_baseline.py:2244` 的 `smooth_move(`；`run_pick_place_baseline.py:1909` 的 `smooth_move(`

### 函数卡：`hold()`（第 662-681 行）

- 定义了什么：平滑移动和保持姿态的物理步进器。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`sim`：类型 `SimulationContext`；项目含义是IsaacLab SimulationContext，负责物理时间步；`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube`：类型 `RigidObject`；项目含义是IsaacLab RigidObject；本任务被抓取和放置的方块；`state`：类型 `torch.Tensor`；项目含义是当前要写给 articulation 的全部关节目标张量；`steps`：类型 `int`；项目含义是步数相关值；`phase`：类型 `str`；项目含义是本功能块中的 `phase` 值；`capture`：类型 `ExpertEpisodeCapture | None`，默认 `None`；项目含义是本功能块中的 `capture` 值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:972` 的 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)`；`run_pick_place_baseline.py:974` 的 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)`；`run_pick_place_baseline.py:1874` 的 `hold(`；`run_pick_place_baseline.py:1979` 的 `hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)`；`run_pick_place_baseline.py:2112` 的 `hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L0631】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `smooth_move(参数在后续行继续)`；调用者把参数交给它完成“平滑移动和保持姿态的物理步进器”，后面的缩进代码是具体实现。
def smooth_move(
# 【L0632】语法拆解：`sim` 是参数/字段名；冒号 `:` 添加类型提示 `SimulationContext`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0633】语法拆解：`robot` 是参数/字段名；冒号 `:` 添加类型提示 `Articulation`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0634】语法拆解：`cube` 是参数/字段名；冒号 `:` 添加类型提示 `RigidObject`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0635】语法拆解：`state` 是参数/字段名；冒号 `:` 添加类型提示 `torch.Tensor`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0636】语法拆解：`joint_ids` 是参数/字段名；冒号 `:` 添加类型提示 `list[int]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `joint_ids: list[int]`；`joint_ids` 表示关节相关值，它参与“平滑移动和保持姿态的物理步进器”。
    joint_ids: list[int],
# 【L0637】语法拆解：`start` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `start`，类型提示为 `np.ndarray`；在本项目中它表示本功能块中的 `start` 值。
    start: np.ndarray,
# 【L0638】语法拆解：`target` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target`，类型提示为 `np.ndarray`；在本项目中它表示目标相关值。
    target: np.ndarray,
# 【L0639】语法拆解：`steps` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `steps`，类型提示为 `int`；在本项目中它表示步数相关值。
    steps: int,
# 【L0640】语法拆解：`phase` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
    phase: str,
# 【L0641】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `capture: ExpertEpisodeCapture | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `capture`，它在本项目中表示本功能块中的 `capture` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    capture: ExpertEpisodeCapture | None = None,
# 【L0642】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0643】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"PICK_PLACE_STAGE={phase}_START"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"PICK_PLACE_STAGE={phase}_START", flush=True` 的当前值/文字输出到终端；它用于观察“平滑移动和保持姿态的物理步进器”进度，也给日志留下可搜索证据。
    print(f"PICK_PLACE_STAGE={phase}_START", flush=True)
# 【L0644】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(steps)`，每次把当前元素放进 `step`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
    for step in range(steps):
# 【L0645】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `progress`。右侧语法为：表达式 `(step + 1) / steps` 使用运算符 `+`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `progress`，它在本项目中表示本功能块中的 `progress` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(step + 1) / steps`；`step` 表示步相关值；`steps` 表示步数相关值。
        progress = (step + 1) / steps
# 【L0646】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `smooth`。右侧语法为：表达式 `3.0 * progress**2 - 2.0 * progress**3` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `smooth`，它在本项目中表示本功能块中的 `smooth` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `3.0 * progress**2 - 2.0 * progress**3`；`progress` 表示本功能块中的 `progress` 值。
        smooth = 3.0 * progress**2 - 2.0 * progress**3
# 【L0647】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `command`。右侧语法为：表达式 `start + smooth * (target - start)` 使用运算符 `+`, `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `start + smooth * (target - start)`；`start` 表示本功能块中的 `start` 值；`smooth` 表示本功能块中的 `smooth` 值；`target` 表示目标相关值。
        command = start + smooth * (target - start)
# 【L0648】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, joint_ids]`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `as_tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `command`；第 2 个实参 `device=sim.device`；第 3 个实参 `dtype=state.dtype`。
# 【项目含义】把右侧结果写进 `state[:, joint_ids]`（写入 `state[:, joint_ids]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(command, device=sim.device, dtype=state.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`command` 表示控制命令相关值；`device` 表示本功能块中的 `device` 值。
        state[:, joint_ids] = torch.as_tensor(command, device=sim.device, dtype=state.dtype)
# 【L0649】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `set_joint_position_target` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `state`。
# 【项目含义】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
        robot.set_joint_position_target(state)
# 【L0650】语法拆解：`if` 要求条件 `capture is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `capture is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if capture is not None:
# 【L0651】语法拆解：`capture` 是模块/对象，点号 `.` 从中取出 `before_step` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `cube`；第 3 个实参 `state`；第 4 个实参 `phase`。
# 【项目含义】对 `capture` 调用 `before_step(robot, cube, state, phase)`：调用 `capture` 提供的 `before_step` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
            capture.before_step(robot, cube, state, phase)
# 【L0652】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
        robot.write_data_to_sim()
# 【L0653】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
        cube.write_data_to_sim()
# 【L0654】语法拆解：`sim` 是模块/对象，点号 `.` 从中取出 `step` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `render=False`。
# 【项目含义】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
        sim.step(render=False)
# 【L0655】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
        robot.update(sim.get_physics_dt())
# 【L0656】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
        cube.update(sim.get_physics_dt())
# 【L0657】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0658】语法拆解：`contact_sensor` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“平滑移动和保持姿态的物理步进器”。
            contact_sensor.update(sim.get_physics_dt())
# 【L0659】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"PICK_PLACE_STAGE={phase}_DONE"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"PICK_PLACE_STAGE={phase}_DONE", flush=True` 的当前值/文字输出到终端；它用于观察“平滑移动和保持姿态的物理步进器”进度，也给日志留下可搜索证据。
    print(f"PICK_PLACE_STAGE={phase}_DONE", flush=True)
# 【L0660】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0661】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0662】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `hold(参数在后续行继续)`；调用者把参数交给它完成“平滑移动和保持姿态的物理步进器”，后面的缩进代码是具体实现。
def hold(
# 【L0663】语法拆解：`sim` 是参数/字段名；冒号 `:` 添加类型提示 `SimulationContext`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0664】语法拆解：`robot` 是参数/字段名；冒号 `:` 添加类型提示 `Articulation`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0665】语法拆解：`cube` 是参数/字段名；冒号 `:` 添加类型提示 `RigidObject`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0666】语法拆解：`state` 是参数/字段名；冒号 `:` 添加类型提示 `torch.Tensor`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0667】语法拆解：`steps` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `steps`，类型提示为 `int`；在本项目中它表示步数相关值。
    steps: int,
# 【L0668】语法拆解：`phase` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `phase`，类型提示为 `str`；在本项目中它表示本功能块中的 `phase` 值。
    phase: str,
# 【L0669】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `capture: ExpertEpisodeCapture | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `capture`，它在本项目中表示本功能块中的 `capture` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    capture: ExpertEpisodeCapture | None = None,
# 【L0670】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“平滑移动和保持姿态的物理步进器”。
) -> None:
# 【L0671】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(steps)`，每次把当前元素放进 `_`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
    for _ in range(steps):
# 【L0672】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `set_joint_position_target` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `state`。
# 【项目含义】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
        robot.set_joint_position_target(state)
# 【L0673】语法拆解：`if` 要求条件 `capture is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `capture is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if capture is not None:
# 【L0674】语法拆解：`capture` 是模块/对象，点号 `.` 从中取出 `before_step` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `cube`；第 3 个实参 `state`；第 4 个实参 `phase`。
# 【项目含义】对 `capture` 调用 `before_step(robot, cube, state, phase)`：调用 `capture` 提供的 `before_step` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
            capture.before_step(robot, cube, state, phase)
# 【L0675】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
        robot.write_data_to_sim()
# 【L0676】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“平滑移动和保持姿态的物理步进器”。
        cube.write_data_to_sim()
# 【L0677】语法拆解：`sim` 是模块/对象，点号 `.` 从中取出 `step` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `render=False`。
# 【项目含义】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
        sim.step(render=False)
# 【L0678】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
        robot.update(sim.get_physics_dt())
# 【L0679】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
        cube.update(sim.get_physics_dt())
# 【L0680】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“平滑移动和保持姿态的物理步进器”所需的帧、episode、动作或实验 case。
        for contact_sensor in CONTACT_SENSORS.values():
# 【L0681】语法拆解：`contact_sensor` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“平滑移动和保持姿态的物理步进器”。
            contact_sensor.update(sim.get_physics_dt())
# 【L0682】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

# 【L0683】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“平滑移动和保持姿态的物理步进器”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“平滑移动和保持姿态的物理步进器”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 10：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环（源码第 684-1185 行）

### 5.A 数据流位置

- 上游：模块 9“平滑移动和保持姿态的物理步进器”。
- 本模块：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环。
- 下游：处理结果继续交给模块 11“接触力统计与平台生成工具”。

### 5.B 为什么需要这一组代码

这一组负责“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `actions`：一个动作块；形状通常为 (时间步数, 7)。
- `raw_actions`：模型原始输出，尚未经过安全裁剪。
- `safe_actions`：经过 action guard 后允许进入仿真的动作。
- `current_arm`：当前六个 RM65 关节角，单位 rad。
- `current_gripper`：当前夹爪归一化位置，0 张开、1 闭合。
- `observation`：本次发给 π0.5 的图像、状态和文字指令字典。
- `external_rgb`：外部相机 RGB 图像，数组轴顺序为高度×宽度×通道。
- `wrist_rgb`：随末端移动的腕部相机 RGB 图像。
- `episode_recorder`：把同步帧保存在内存并最终写盘的记录器。

### 5.D 本模块首次阅读要认识的调用

- `run_pi05_closed_loop(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `connect_without_keepalive(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `call_connect_without_keepalive(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `collision_api.CreateCollisionEnabledAttr(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `Set(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `WebsocketClientPolicy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `item(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `client.get_server_metadata(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `server_metadata.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `expected_server_metadata.items(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `case_chunk_seed(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`run_pi05_closed_loop()`（第 684-1183 行）

- 定义了什么：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`sim`：类型 `SimulationContext`；项目含义是IsaacLab SimulationContext，负责物理时间步；`robot`：类型 `Articulation`；项目含义是IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube`：类型 `RigidObject`；项目含义是IsaacLab RigidObject；本任务被抓取和放置的方块；`state`：类型 `torch.Tensor`；项目含义是当前要写给 articulation 的全部关节目标张量；`arm_ids`：类型 `list[int]`；项目含义是本功能块中的 `arm_ids` 值；`gripper_ids`：类型 `list[int]`；项目含义是夹爪相关值；`gripper_master_id`：类型 `int`；项目含义是夹爪相关值；`target_block_position`：类型 `np.ndarray`；项目含义是目标、位置相关值；`settled_source_position`：类型 `torch.Tensor`；项目含义是源位置、位置相关值；`target_platform_collision_apis`：类型 `list`；项目含义是目标、支撑平台相关值；`episode_capture`：类型 `ExpertEpisodeCapture`；项目含义是连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；`episode_recorder`：类型 `EpisodeRecorder`；项目含义是把同步帧保存在内存并最终写盘的记录器；`output`：类型 `Path`；项目含义是输出文件路径
- 返回类型标注：`int`。
- 函数体实际 return：`0 if passed else 1`；`call_connect_without_keepalive(original_connect, *connect_args, **connect_kwargs)`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1890` 的 `return run_pi05_closed_loop(`

### 函数卡：`connect_without_keepalive()`（第 708-711 行）

- 定义了什么：π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`未标注（需要从调用和函数体判断）`。
- 函数体实际 return：`call_connect_without_keepalive(original_connect, *connect_args, **connect_kwargs)`
- 项目中的调用：本文件内没有直接调用；它是脚本入口、回调，或由其他环境/框架按接口调用。


### 5.F 这一模块的版本变化

- 当前第 732-732 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`simulation_safety_abort_reason = None`
- 当前第 735-738 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`policy_sampling_records = []` / `initial_policy_observation_images: tuple[np.ndarray, np.ndarray] | None = None` / `initial_policy_physical_state: dict[str, dict] | None = None` / `server_metadata = client.get_server_metadata()`
- 当前第 740-754 行相对旧教学快照发生 `insert`：旧版 0 行，当前 15 行。 当前代码摘录：`expected_server_metadata = {` / `"sampling_mode": POLICY_SAMPLING_MODE,` / `"deterministic_seed_required": True,` / `"model_action_horizon": POLICY_NOISE_ACTION_HORIZON,`
- 当前第 756-756 行相对旧教学快照发生 `insert`：旧版 0 行，当前 1 行。 当前代码摘录：`chunk_seed = case_chunk_seed(args.policy_noise_seed, chunk_index)`
- 当前第 758-765 行相对旧教学快照发生 `insert`：旧版 0 行，当前 8 行。 当前代码摘录：`if chunk_index == 0:` / `# Keep the exact arrays sent to the policy.  Episode recording` / `# performs another render tick, so its nearest PNG is not` / `# necessarily byte-identical to this observation.`
- 当前第 770-812 行相对旧教学快照发生 `insert`：旧版 0 行，当前 43 行。 当前代码摘录：`)` / `if episode_capture.wrist_tool_body_id is None:` / `raise RuntimeError("wrist tool body id is required for physical-state evidence")` / `if episode_capture.last_wrist_eye is None or episode_capture.last_wrist_forward is None:`

### 5.G 逐行精读

```python
# 【L0684】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `run_pi05_closed_loop(参数在后续行继续)`；调用者把参数交给它完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，后面的缩进代码是具体实现。
def run_pi05_closed_loop(
# 【L0685】语法拆解：`sim` 是参数/字段名；冒号 `:` 添加类型提示 `SimulationContext`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `sim`，类型提示为 `SimulationContext`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
    sim: SimulationContext,
# 【L0686】语法拆解：`robot` 是参数/字段名；冒号 `:` 添加类型提示 `Articulation`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `robot`，类型提示为 `Articulation`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: Articulation,
# 【L0687】语法拆解：`cube` 是参数/字段名；冒号 `:` 添加类型提示 `RigidObject`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `cube`，类型提示为 `RigidObject`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
    cube: RigidObject,
# 【L0688】语法拆解：`state` 是参数/字段名；冒号 `:` 添加类型提示 `torch.Tensor`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `state`，类型提示为 `torch.Tensor`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
    state: torch.Tensor,
# 【L0689】语法拆解：`arm_ids` 是参数/字段名；冒号 `:` 添加类型提示 `list[int]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `arm_ids: list[int]`；`arm_ids` 表示本功能块中的 `arm_ids` 值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    arm_ids: list[int],
# 【L0690】语法拆解：`gripper_ids` 是参数/字段名；冒号 `:` 添加类型提示 `list[int]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `gripper_ids: list[int]`；`gripper_ids` 表示夹爪相关值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    gripper_ids: list[int],
# 【L0691】语法拆解：`gripper_master_id` 是参数/字段名；冒号 `:` 添加类型提示 `int`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `gripper_master_id`，类型提示为 `int`；在本项目中它表示夹爪相关值。
    gripper_master_id: int,
# 【L0692】语法拆解：`target_block_position` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target_block_position`，类型提示为 `np.ndarray`；在本项目中它表示目标、位置相关值。
    target_block_position: np.ndarray,
# 【L0693】语法拆解：`settled_source_position` 是参数/字段名；冒号 `:` 添加类型提示 `torch.Tensor`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `settled_source_position`，类型提示为 `torch.Tensor`；在本项目中它表示源位置、位置相关值。
    settled_source_position: torch.Tensor,
# 【L0694】语法拆解：`target_platform_collision_apis` 是参数/字段名；冒号 `:` 添加类型提示 `list`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `target_platform_collision_apis`，类型提示为 `list`；在本项目中它表示目标、支撑平台相关值。
    target_platform_collision_apis: list,
# 【L0695】语法拆解：`episode_capture` 是参数/字段名；冒号 `:` 添加类型提示 `ExpertEpisodeCapture`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `episode_capture`，类型提示为 `ExpertEpisodeCapture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
    episode_capture: ExpertEpisodeCapture,
# 【L0696】语法拆解：`episode_recorder` 是参数/字段名；冒号 `:` 添加类型提示 `EpisodeRecorder`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `episode_recorder`，类型提示为 `EpisodeRecorder`；在本项目中它表示把同步帧保存在内存并最终写盘的记录器。
    episode_recorder: EpisodeRecorder,
# 【L0697】语法拆解：`output` 是参数/字段名；冒号 `:` 添加类型提示 `Path`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `output`，类型提示为 `Path`；在本项目中它表示输出文件路径。
    output: Path,
# 【L0698】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> int:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
) -> int:
# 【L0699】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Run receding-horizon π0.5 control and write task-level evidence.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Run receding-horizon π0.5 control and write task-level evidence."""
# 【L0700】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0701】语法拆解：`import` 加载模块；`time` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `time` 引入 `time`。在这份程序里，`time` 用于计时和短暂等待；后续出现这些名字时调用的是这里的外部能力。
    import time
# 【L0702】语法拆解：`import` 加载模块；`websockets.sync.client as ws` 是模块名或别名，后续用点号访问其中功能。
# 【项目含义】从 `websockets` 引入 `websockets.sync.client as ws`。在这份程序里，`websockets` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    import websockets.sync.client as ws
# 【L0703】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0704】语法拆解：`from openpi_extension.websocket_compat` 指定来源模块；`import call_connect_without_keepalive` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_extension` 引入 `call_connect_without_keepalive`。在这份程序里，`openpi_extension` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    from openpi_extension.websocket_compat import call_connect_without_keepalive
# 【L0705】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0706】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `original_connect`。右侧语法为：`ws` 是起始对象；每个点号 `.` 依次读取属性/成员：`connect`。
# 【项目含义】得到 `original_connect`，它在本项目中表示本功能块中的 `original_connect` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ws.connect`；`ws` 表示本功能块中的 `ws` 值；`connect` 表示本功能块中的 `connect` 值。
    original_connect = ws.connect
# 【L0707】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0708】语法拆解：`def` 定义函数 `connect_without_keepalive`；第一对圆括号列出形参，逗号负责分隔：`*connect_args` 是一个形参；`**connect_kwargs` 是一个形参；`-> 未标注` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `connect_without_keepalive(*connect_args, **connect_kwargs)`；调用者把参数交给它完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，后面的缩进代码是具体实现。
    def connect_without_keepalive(*connect_args, **connect_kwargs):
# 【L0709】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`call_connect_without_keepalive(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `call_connect_without_keepalive(` 交回调用者；这个值的含义是：计算表达式 `call_connect_without_keepalive(`；`call_connect_without_keepalive` 表示本功能块中的 `call_connect_without_keepalive` 值。
        return call_connect_without_keepalive(
# 【L0710】语法拆解：表达式 `original_connect, *connect_args, **connect_kwargs` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `original_connect, *connect_args, **connect_kwargs` 接入当前完整语句；`original_connect` 表示本功能块中的 `original_connect` 值；`connect_args` 表示本功能块中的 `connect_args` 值；`connect_kwargs` 表示本功能块中的 `connect_kwargs` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            original_connect, *connect_args, **connect_kwargs
# 【L0711】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        )
# 【L0712】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0713】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `ws.connect`。右侧语法为：`connect_without_keepalive` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `ws` 对象的 `connect` 配置成 `connect_without_keepalive`。`ws` 在这里表示本功能块中的 `ws` 值；这个设置会影响“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    ws.connect = connect_without_keepalive
# 【L0714】语法拆解：`from openpi_client.websocket_client_policy` 指定来源模块；`import WebsocketClientPolicy` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `openpi_client` 引入 `WebsocketClientPolicy`。在这份程序里，`openpi_client` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
    from openpi_client.websocket_client_policy import WebsocketClientPolicy
# 【L0715】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0716】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
    for collision_api in target_platform_collision_apis:
# 【L0717】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(True`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L0718】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print("PI05_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L0719】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0720】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `client`。右侧语法为：`WebsocketClientPolicy` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_host`；第 2 个实参 `args.policy_port`。
# 【项目含义】得到 `client`，它在本项目中表示本功能块中的 `client` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `WebsocketClientPolicy(args.policy_host, args.policy_port)`；`WebsocketClientPolicy` 表示本功能块中的 `WebsocketClientPolicy` 值；`policy_host` 表示策略相关值；`policy_port` 表示OpenPI WebSocket policy server 监听的 TCP 端口。
    client = WebsocketClientPolicy(args.policy_host, args.policy_port)
# 【L0721】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `inference_latencies`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `inference_latencies`，它在本项目中表示本功能块中的 `inference_latencies` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    inference_latencies = []
# 【L0722】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `total_joint_limit_clamps`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `total_joint_limit_clamps`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_joint_limit_clamps = 0
# 【L0723】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `total_joint_step_clamps`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `total_joint_step_clamps`，它在本项目中表示关节、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_joint_step_clamps = 0
# 【L0724】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `total_gripper_clamps`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `total_gripper_clamps`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    total_gripper_clamps = 0
# 【L0725】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_chunks`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `action_chunks`，它在本项目中表示本 episode 已向 π0.5 请求的动作块数量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    action_chunks = 0
# 【L0726】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `executed_actions`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `executed_actions`，它在本项目中表示实际送进 Isaac 控制器的七维动作步数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    executed_actions = 0
# 【L0727】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_cube_z`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube.data.root_pos_w[0, 2].item()`。
# 【项目含义】得到 `max_cube_z`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    max_cube_z = float(cube.data.root_pos_w[0, 2].item())
# 【L0728】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `consecutive_candidate_chunks`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `consecutive_candidate_chunks`，它在本项目中表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
    consecutive_candidate_chunks = 0
# 【L0729】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `last_executed_gripper_target`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `last_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    last_executed_gripper_target = None
# 【L0730】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_postcondition_applied`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `release_postcondition_applied`，它在本项目中表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
    release_postcondition_applied = False
# 【L0731】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_postcondition_arm_target`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `release_postcondition_arm_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    release_postcondition_arm_target = None
# 【L0732】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_safety_abort_reason`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `simulation_safety_abort_reason`，它在本项目中表示本功能块中的 `simulation_safety_abort_reason` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    simulation_safety_abort_reason = None
# 【L0733】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_observed_gripper_normalized`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"inf"`。
# 【项目含义】得到 `minimum_observed_gripper_normalized`，它在本项目中表示夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float("inf")`；`inf` 表示本功能块中的 `inf` 值。
    minimum_observed_gripper_normalized = float("inf")
# 【L0734】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_executed_gripper_target`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"inf"`。
# 【项目含义】得到 `minimum_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float("inf")`；`inf` 表示本功能块中的 `inf` 值。
    minimum_executed_gripper_target = float("inf")
# 【L0735】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_sampling_records`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `policy_sampling_records`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    policy_sampling_records = []
# 【L0736】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_observation_images: tuple[np.ndarray, np.ndarray] | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `initial_policy_observation_images`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    initial_policy_observation_images: tuple[np.ndarray, np.ndarray] | None = None
# 【L0737】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_physical_state: dict[str, dict] | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `initial_policy_physical_state`，它在本项目中表示策略、状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    initial_policy_physical_state: dict[str, dict] | None = None
# 【L0738】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `server_metadata`。右侧语法为：`client` 是模块/对象，点号 `.` 从中取出 `get_server_metadata` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `server_metadata`，它在本项目中表示元数据相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `client.get_server_metadata()`；`client` 表示本功能块中的 `client` 值；`get_server_metadata` 表示元数据相关值。
    server_metadata = client.get_server_metadata()
# 【L0739】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
    try:
# 【L0740】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_server_metadata`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expected_server_metadata`，它在本项目中表示元数据相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        expected_server_metadata = {
# 【L0741】语法拆解：这是字典键值对：`"sampling_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`POLICY_SAMPLING_MODE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `sampling_mode`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `sampling_mode` 数据；字段值来自 `POLICY_SAMPLING_MODE`，因此保存/传递的是这个表达式当前计算出的结果。
            "sampling_mode": POLICY_SAMPLING_MODE,
# 【L0742】语法拆解：这是字典键值对：`"deterministic_seed_required"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `deterministic_seed_required`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `deterministic_seed_required` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "deterministic_seed_required": True,
# 【L0743】语法拆解：这是字典键值对：`"model_action_horizon"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`POLICY_NOISE_ACTION_HORIZON` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `model_action_horizon`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_action_horizon` 数据；字段值来自 `POLICY_NOISE_ACTION_HORIZON`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_action_horizon": POLICY_NOISE_ACTION_HORIZON,
# 【L0744】语法拆解：这是字典键值对：`"model_action_dim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`POLICY_NOISE_ACTION_DIM` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `model_action_dim`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_action_dim` 数据；字段值来自 `POLICY_NOISE_ACTION_DIM`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_action_dim": POLICY_NOISE_ACTION_DIM,
# 【L0745】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        }
# 【L0746】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata_mismatches`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `metadata_mismatches`，它在本项目中表示元数据相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        metadata_mismatches = {
# 【L0747】语法拆解：`key` 是参数/字段名；冒号 `:` 添加类型提示 `{"expected": value, "actual": server_metadata.get(key)}`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `key: {"expected": value, "actual": server_metadata.get(key)}` 接入当前完整语句；`key` 表示本功能块中的 `key` 值；`expected` 表示本功能块中的 `expected` 值；`value` 表示本功能块中的 `value` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            key: {"expected": value, "actual": server_metadata.get(key)}
# 【L0748】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for key, value in expected_server_metadata.items()` 中给出的序列，逐项完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            for key, value in expected_server_metadata.items()
# 【L0749】语法拆解：`if` 要求条件 `server_metadata.get(key) != value` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `server_metadata.get(key) != value` 是否成立；`server_metadata` 表示元数据相关值；`get` 表示本功能块中的 `get` 值；`key` 表示本功能块中的 `key` 值
            if server_metadata.get(key) != value
# 【L0750】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        }
# 【L0751】语法拆解：`if` 要求条件 `metadata_mismatches` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `metadata_mismatches` 是否成立；`metadata_mismatches` 表示元数据相关值
        if metadata_mismatches:
# 【L0752】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L0753】语法拆解：`f"policy server deterministic metadata mismatch: {metadata_mismatches}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"policy server deterministic metadata mismatch: {metadata_mismatches}"` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`policy` 表示加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象；`server` 表示本功能块中的 `server` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"policy server deterministic metadata mismatch: {metadata_mismatches}"
# 【L0754】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0755】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `range(args.policy_max_action_chunks)`，每次把当前元素放进 `chunk_index`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
        for chunk_index in range(args.policy_max_action_chunks):
# 【L0756】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `chunk_seed`。右侧语法为：`case_chunk_seed` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `args.policy_noise_seed`；第 2 个实参 `chunk_index`。
# 【项目含义】得到 `chunk_seed`，它在本项目中表示本功能块中的 `chunk_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `case_chunk_seed(args.policy_noise_seed, chunk_index)`；`case_chunk_seed` 表示本功能块中的 `case_chunk_seed` 值；`policy_noise_seed` 表示策略相关值；`chunk_index` 表示索引相关值。
            chunk_seed = case_chunk_seed(args.policy_noise_seed, chunk_index)
# 【L0757】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_rgb, wrist_rgb`。右侧语法为：`episode_capture` 是模块/对象，点号 `.` 从中取出 `_render_images` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `cube`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `external_rgb, wrist_rgb`；`external_rgb` 表示外部相机 RGB 图像，数组轴顺序为高度×宽度×通道；`wrist_rgb` 表示随末端移动的腕部相机 RGB 图像。右侧的来源是：计算表达式 `episode_capture._render_images(robot, cube)`；`episode_capture` 表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；`_render_images` 表示本功能块中的 `_render_images` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            external_rgb, wrist_rgb = episode_capture._render_images(robot, cube)
# 【L0758】语法拆解：`if` 要求条件 `chunk_index == 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `chunk_index == 0` 是否成立；`chunk_index` 表示索引相关值
            if chunk_index == 0:
# 【L0759】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：Keep the exact arrays sent to the policy.  Episode recording
                # Keep the exact arrays sent to the policy.  Episode recording
# 【L0760】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：performs another render tick, so its nearest PNG is not
                # performs another render tick, so its nearest PNG is not
# 【L0761】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：necessarily byte-identical to this observation.
                # necessarily byte-identical to this observation.
# 【L0762】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_observation_images`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `initial_policy_observation_images`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
                initial_policy_observation_images = (
# 【L0763】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`external_rgb` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `external_rgb` 调用 `copy()`：调用 `external_rgb` 提供的 `copy` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    external_rgb.copy(),
# 【L0764】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`wrist_rgb` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `wrist_rgb` 调用 `copy()`：调用 `wrist_rgb` 提供的 `copy` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    wrist_rgb.copy(),
# 【L0765】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0766】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_arm`。右侧语法为：`robot.data.joint_pos[0, arm_ids].detach().cpu().numpy().astype(np.float32)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `current_arm`，它在本项目中表示当前六个 RM65 关节角，单位 rad；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
            current_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy().astype(np.float32)
# 【L0767】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_gripper`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `current_gripper`，它在本项目中表示当前夹爪归一化位置，0 张开、1 闭合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
            current_gripper = np.array(
# 【L0768】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],`；`normalize_gripper` 表示夹爪相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request，共同完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                [normalize_gripper(float(robot.data.joint_pos[0, gripper_master_id].item()))],
# 【L0769】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float32`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                dtype=np.float32,
# 【L0770】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0771】语法拆解：`if` 要求条件 `episode_capture.wrist_tool_body_id is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `episode_capture.wrist_tool_body_id is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
            if episode_capture.wrist_tool_body_id is None:
# 【L0772】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("wrist tool body id is required for physical-state evidence")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("wrist tool body id is required for physical-state evidence")` 并停止当前路径；说明当前输入违反“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”要求，不能继续进入仿真、训练或评测。
                raise RuntimeError("wrist tool body id is required for physical-state evidence")
# 【L0773】语法拆解：`if` 要求条件 `episode_capture.last_wrist_eye is None or episode_capture.last_wrist_forward is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `episode_capture.last_wrist_eye is None or episode_capture.last_wrist_forward is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
            if episode_capture.last_wrist_eye is None or episode_capture.last_wrist_forward is None:
# 【L0774】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("wrist camera pose evidence was not populated by rendering")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("wrist camera pose evidence was not populated by rendering")` 并停止当前路径；说明当前输入违反“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”要求，不能继续进入仿真、训练或评测。
                raise RuntimeError("wrist camera pose evidence was not populated by rendering")
# 【L0775】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physical_arrays`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physical_arrays`，它在本项目中表示本功能块中的 `physical_arrays` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            physical_arrays = {
# 【L0776】语法拆解：这是字典键值对：`"cube_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`cube.data.root_pos_w[0].detach().cpu().numpy().astype(np.float32)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `cube_position`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `cube_position` 数据；字段值来自 `cube.data.root_pos_w[0].detach().cpu().numpy().astype(np.float32)`，因此保存/传递的是这个表达式当前计算出的结果。
                "cube_position": cube.data.root_pos_w[0].detach().cpu().numpy().astype(np.float32),
# 【L0777】语法拆解：这是字典键值对：`"cube_quaternion"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`cube.data.root_quat_w[0].detach().cpu().numpy().astype(np.float32)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `cube_quaternion`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `cube_quaternion` 数据；字段值来自 `cube.data.root_quat_w[0].detach().cpu().numpy().astype(np.float32)`，因此保存/传递的是这个表达式当前计算出的结果。
                "cube_quaternion": cube.data.root_quat_w[0].detach().cpu().numpy().astype(np.float32),
# 【L0778】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_tool_position`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_tool_position` 数据；字段值来自 `robot.data.body_pos_w[`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist_tool_position": robot.data.body_pos_w[
# 【L0779】语法拆解：`0, episode_capture.wrist_tool_body_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `0, episode_capture.wrist_tool_body_id` 接入当前完整语句；`episode_capture` 表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；`wrist_tool_body_id` 表示腕部相机、刚体相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    0, episode_capture.wrist_tool_body_id
# 【L0780】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `]` 调用 `detach().cpu().numpy().astype(np.float32)`：调用 `]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                ].detach().cpu().numpy().astype(np.float32),
# 【L0781】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_tool_quaternion`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_tool_quaternion` 数据；字段值来自 `robot.data.body_quat_w[`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist_tool_quaternion": robot.data.body_quat_w[
# 【L0782】语法拆解：`0, episode_capture.wrist_tool_body_id` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `0, episode_capture.wrist_tool_body_id` 接入当前完整语句；`episode_capture` 表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；`wrist_tool_body_id` 表示腕部相机、刚体相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    0, episode_capture.wrist_tool_body_id
# 【L0783】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `]` 调用 `detach().cpu().numpy().astype(np.float32)`：调用 `]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                ].detach().cpu().numpy().astype(np.float32),
# 【L0784】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_camera_eye`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_camera_eye` 数据；字段值来自 `episode_capture.last_wrist_eye.detach()`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist_camera_eye": episode_capture.last_wrist_eye.detach()
# 【L0785】语法拆解：`.cpu()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `.cpu()` 接入当前完整语句；`cpu` 表示本功能块中的 `cpu` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                .cpu()
# 【L0786】语法拆解：`.numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `.numpy()` 接入当前完整语句；`numpy` 表示本功能块中的 `numpy` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                .numpy()
# 【L0787】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`.astype(np.float32)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】向上一行的函数调用或容器继续传入 `.astype(np.float32)`；`astype` 表示本功能块中的 `astype` 值；`float32` 表示本功能块中的 `float32` 值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                .astype(np.float32),
# 【L0788】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_camera_forward`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_camera_forward` 数据；字段值来自 `episode_capture.last_wrist_forward.detach()`，因此保存/传递的是这个表达式当前计算出的结果。
                "wrist_camera_forward": episode_capture.last_wrist_forward.detach()
# 【L0789】语法拆解：`.cpu()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `.cpu()` 接入当前完整语句；`cpu` 表示本功能块中的 `cpu` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                .cpu()
# 【L0790】语法拆解：`.numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `.numpy()` 接入当前完整语句；`numpy` 表示本功能块中的 `numpy` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                .numpy()
# 【L0791】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`.astype(np.float32)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】向上一行的函数调用或容器继续传入 `.astype(np.float32)`；`astype` 表示本功能块中的 `astype` 值；`float32` 表示本功能块中的 `float32` 值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                .astype(np.float32),
# 【L0792】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0793】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physical_state`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physical_state`，它在本项目中表示状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            physical_state = {
# 【L0794】语法拆解：`name` 是参数/字段名；冒号 `:` 添加类型提示 `{`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `name: {` 接入当前完整语句；`name` 表示本功能块中的 `name` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                name: {
# 【L0795】语法拆解：这是字典键值对：`"values"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`value` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `values`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `values` 数据；字段值来自 `value.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                    "values": value.tolist(),
# 【L0796】语法拆解：这是字典键值对：`"shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `value.shape`。
# 【项目含义】定义字典/JSON 字段 `shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `shape` 数据；字段值来自 `list(value.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "shape": list(value.shape),
# 【L0797】语法拆解：这是字典键值对：`"dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `value.dtype`。
# 【项目含义】定义字典/JSON 字段 `dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `dtype` 数据；字段值来自 `str(value.dtype)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "dtype": str(value.dtype),
# 【L0798】语法拆解：这是字典键值对：`"sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `value`。
# 【项目含义】定义字典/JSON 字段 `sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `sha256` 数据；字段值来自 `array_sha256(value)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "sha256": array_sha256(value),
# 【L0799】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                }
# 【L0800】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for name, value in physical_arrays.items()` 中给出的序列，逐项完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                for name, value in physical_arrays.items()
# 【L0801】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0802】语法拆解：`if` 要求条件 `chunk_index == 0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `chunk_index == 0` 是否成立；`chunk_index` 表示索引相关值
            if chunk_index == 0:
# 【L0803】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_physical_state`。右侧语法为：`physical_state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `initial_policy_physical_state`，它在本项目中表示策略、状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `physical_state`；`physical_state` 表示状态相关值。
                initial_policy_physical_state = physical_state
# 【L0804】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_action_cube`。右侧语法为：`cube.data.root_pos_w[0].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_action_cube`，它在本项目中表示动作、任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
            pre_action_cube = cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L0805】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_action_target_error`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_action_target_error`，它在本项目中表示动作、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
            pre_action_target_error = float(
# 【L0806】语法拆解：`np.linalg` 是模块/对象，点号 `.` 从中取出 `norm` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `pre_action_cube - target_block_position`。
# 【项目含义】调用 `np.linalg.norm`：计算向量长度/欧氏距离；本行实际操作 `np.linalg.norm(pre_action_cube - target_block_position)`。`linalg` 表示本功能块中的 `linalg` 值；`norm` 表示本功能块中的 `norm` 值。
                np.linalg.norm(pre_action_cube - target_block_position)
# 【L0807】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0808】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_action_lifted`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_action_lifted`，它在本项目中表示动作相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            pre_action_lifted = (
# 【L0809】语法拆解：表达式 `max_cube_z - float(settled_source_position[2].item()) > 0.02` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `max_cube_z - float(settled_source_position[2].item()) > 0.02` 接到上一行尚未结束的布尔表达式；`max_cube_z` 表示任务方块相关值；`settled_source_position` 表示源位置、位置相关值；`item` 表示本功能块中的 `item` 值。比较结果共同决定“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”是否通过。
                max_cube_z - float(settled_source_position[2].item()) > 0.02
# 【L0810】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0811】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_zone_arm_hold_active`。右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_zone_arm_hold_active`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
            target_zone_arm_hold_active = bool(
# 【L0812】语法拆解：表达式 `pre_action_lifted and pre_action_target_error < 0.05` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `pre_action_lifted and pre_action_target_error < 0.05` 接到上一行尚未结束的布尔表达式；`pre_action_lifted` 表示动作相关值；`pre_action_target_error` 表示动作、目标相关值。比较结果共同决定“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”是否通过。
                pre_action_lifted and pre_action_target_error < 0.05
# 【L0813】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0814】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observation`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始构造一次在线 π0.5 请求。这个字典的键必须与 RM65Inputs 读取的键完全一致。
            observation = {
# 【L0815】语法拆解：这是字典键值对：`"observation/joint_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`current_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把刚从 IsaacLab `robot.data.joint_pos` 读出的六个实际 RM65 关节角放入请求。
                "observation/joint_position": current_arm,
# 【L0816】语法拆解：这是字典键值对：`"observation/gripper_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`current_gripper` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把实际 4C2 主关节归一化为 0～1 的单元素数组后放入请求。
                "observation/gripper_position": current_gripper,
# 【L0817】语法拆解：这是字典键值对：`"observation/external_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`external_rgb` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把当前外部相机 RGB 帧放入请求；RM65Inputs 会将它映射到 `base_0_rgb`。
                "observation/external_image": external_rgb,
# 【L0818】语法拆解：这是字典键值对：`"observation/wrist_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`wrist_rgb` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把当前腕部相机 RGB 帧放入请求；RM65Inputs 会将它映射到有效腕部图像槽。
                "observation/wrist_image": wrist_rgb,
# 【L0819】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`episode_prompt`。
# 【项目含义】把本 episode 的自然语言任务指令放入请求，使视觉和状态动作受语言条件约束。
                "prompt": args.episode_prompt,
# 【L0820】语法拆解：`POLICY_NOISE_SEED_KEY` 是参数/字段名；冒号 `:` 添加类型提示 `chunk_seed`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `POLICY_NOISE_SEED_KEY`，类型提示为 `chunk_seed`；在本项目中它表示策略相关值。
                POLICY_NOISE_SEED_KEY: chunk_seed,
# 【L0821】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0822】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `started`。右侧语法为：`time` 是模块/对象，点号 `.` 从中取出 `perf_counter` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `started`，它在本项目中表示本功能块中的 `started` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `time.perf_counter()`；`time` 表示时间相关值；`perf_counter` 表示本功能块中的 `perf_counter` 值。
            started = time.perf_counter()
# 【L0823】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `response`。右侧语法为：`client` 是模块/对象，点号 `.` 从中取出 `infer` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `observation`。
# 【项目含义】得到 `response`，它在本项目中表示本功能块中的 `response` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把当前观测交给 π0.5 policy 推理，得到包含未来动作块的返回字典。
            response = client.infer(observation)
# 【L0824】语法拆解：`inference_latencies` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `time.perf_counter() - started`。
# 【项目含义】对 `inference_latencies` 执行 `append`，把 `time.perf_counter() - started` 加入已有结果；该集合表示本功能块中的 `inference_latencies` 值，随后会用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            inference_latencies.append(time.perf_counter() - started)
# 【L0825】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sampling_evidence`。右侧语法为：`validate_policy_sampling_evidence(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `sampling_evidence`，它在本项目中表示本功能块中的 `sampling_evidence` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_policy_sampling_evidence(`；`validate_policy_sampling_evidence` 表示策略相关值。
            sampling_evidence = validate_policy_sampling_evidence(
# 【L0826】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`response` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"policy_sampling"`。
# 【项目含义】对 `response` 调用 `get("policy_sampling")`：按键读取字典/XML 属性；若不存在则使用代码给出的默认值。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                response.get("policy_sampling"),
# 【L0827】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_seed`。右侧语法为：`chunk_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `expected_seed` 传入 `chunk_seed`；该参数在本项目中表示本功能块中的 `expected_seed` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                expected_seed=chunk_seed,
# 【L0828】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_horizon`。右侧语法为：`POLICY_NOISE_ACTION_HORIZON` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_horizon` 传入 `POLICY_NOISE_ACTION_HORIZON`；该参数在本项目中表示动作相关值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                action_horizon=POLICY_NOISE_ACTION_HORIZON,
# 【L0829】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action_dim`。右侧语法为：`POLICY_NOISE_ACTION_DIM` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `action_dim` 传入 `POLICY_NOISE_ACTION_DIM`；该参数在本项目中表示动作相关值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                action_dim=POLICY_NOISE_ACTION_DIM,
# 【L0830】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0831】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `raw_actions`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `response["actions"]`；第 2 个实参 `dtype=np.float32`；其中 `response["actions"]` 的方括号表示先从 `response` 按键/索引 `"actions"` 取值。
# 【项目含义】得到 `raw_actions`，它在本项目中表示模型原始输出，尚未经过安全裁剪；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `response["actions"], dtype=np.float32`（未来动作序列；RM65 每个时间步是六个关节目标加一个夹爪目标，共七维），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
            raw_actions = np.asarray(response["actions"], dtype=np.float32)
# 【L0832】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe_actions, guard`。右侧语法为：`guard_action_chunk` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `raw_actions`；第 2 个实参 `current_arm`。
# 【项目含义】把模型原始动作块和当前六关节角交给 action guard；返回逐步限位/步长/夹爪裁剪后的动作与诊断。
            safe_actions, guard = guard_action_chunk(raw_actions, current_arm)
# 【L0833】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe_actions`。右侧语法为：`safe_actions` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `safe_actions`，它在本项目中表示经过 action guard 后允许进入仿真的动作；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
            safe_actions = safe_actions.copy()
# 【L0834】语法拆解：`if` 要求条件 `target_zone_arm_hold_active` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `target_zone_arm_hold_active` 是否成立；`target_zone_arm_hold_active` 表示目标相关值
            if target_zone_arm_hold_active:
# 【L0835】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `safe_actions[:, :6]`。右侧语法为：`current_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `safe_actions[:, :6]`（写入 `safe_actions[:, :6]` 指定的字段）；右侧具体做的是：计算表达式 `current_arm`；`current_arm` 表示当前六个 RM65 关节角，单位 rad。
                safe_actions[:, :6] = current_arm
# 【L0836】语法拆解：表达式 `total_joint_limit_clamps += guard["joint_limit_clamp_count"]` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `total_joint_limit_clamps + guard["joint_limit_clamp_count"]` 更新 `total_joint_limit_clamps` 原值；`total_joint_limit_clamps` 表示关节相关值，常用于累计步数、距离、损失或成功次数。
            total_joint_limit_clamps += guard["joint_limit_clamp_count"]
# 【L0837】语法拆解：表达式 `total_joint_step_clamps += guard["joint_step_clamp_count"]` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `total_joint_step_clamps + guard["joint_step_clamp_count"]` 更新 `total_joint_step_clamps` 原值；`total_joint_step_clamps` 表示关节、步相关值，常用于累计步数、距离、损失或成功次数。
            total_joint_step_clamps += guard["joint_step_clamp_count"]
# 【L0838】语法拆解：表达式 `total_gripper_clamps += guard["gripper_clamp_count"]` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `total_gripper_clamps + guard["gripper_clamp_count"]` 更新 `total_gripper_clamps` 原值；`total_gripper_clamps` 表示夹爪相关值，常用于累计步数、距离、损失或成功次数。
            total_gripper_clamps += guard["gripper_clamp_count"]
# 【L0839】语法拆解：表达式 `action_chunks += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `action_chunks + 1` 更新 `action_chunks` 原值；`action_chunks` 表示本 episode 已向 π0.5 请求的动作块数量，常用于累计步数、距离、损失或成功次数。
            action_chunks += 1
# 【L0840】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0841】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `execute_count`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `execute_count`，它在本项目中表示本次 10 步模型输出中实际执行的前若干步，本项目默认最多 5；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            execute_count = (
# 【L0842】语法拆解：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe_actions`。
# 【项目含义】调用函数 `len`，传入 `safe_actions`；函数名对应本功能块中的 `len` 值。这一返回值或副作用被外层表达式用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                len(safe_actions)
# 【L0843】语法拆解：`if` 要求条件 `target_zone_arm_hold_active` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `target_zone_arm_hold_active` 是否成立；`target_zone_arm_hold_active` 表示目标相关值
                if target_zone_arm_hold_active
# 【L0844】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `min(args.policy_execute_actions_per_chunk, len(safe_actions))`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else min(args.policy_execute_actions_per_chunk, len(safe_actions))
# 【L0845】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0846】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sampling_record`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `sampling_record`，它在本项目中表示本功能块中的 `sampling_record` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            sampling_record = {
# 【L0847】语法拆解：这是字典键值对：`"chunk_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`chunk_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `chunk_index`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `chunk_index` 数据；字段值来自 `chunk_index`，因此保存/传递的是这个表达式当前计算出的结果。
                "chunk_index": chunk_index,
# 【L0848】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `**sampling_evidence` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `**sampling_evidence,` 接到上一行未结束的数学公式；`sampling_evidence` 表示本功能块中的 `sampling_evidence` 值，整条公式用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                **sampling_evidence,
# 【L0849】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `observation_sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `observation_sha256` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
                "observation_sha256": {
# 【L0850】语法拆解：这是字典键值对：`"joint_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `current_arm`。
# 【项目含义】定义字典/JSON 字段 `joint_position`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `joint_position` 数据；字段值来自 `array_sha256(current_arm)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "joint_position": array_sha256(current_arm),
# 【L0851】语法拆解：这是字典键值对：`"gripper_position"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `current_gripper`。
# 【项目含义】定义字典/JSON 字段 `gripper_position`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_position` 数据；字段值来自 `array_sha256(current_gripper)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "gripper_position": array_sha256(current_gripper),
# 【L0852】语法拆解：这是字典键值对：`"external_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_rgb`。
# 【项目含义】定义字典/JSON 字段 `external_image`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `external_image` 数据；字段值来自 `array_sha256(external_rgb)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "external_image": array_sha256(external_rgb),
# 【L0853】语法拆解：这是字典键值对：`"wrist_image"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_rgb`。
# 【项目含义】定义字典/JSON 字段 `wrist_image`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_image` 数据；字段值来自 `array_sha256(wrist_rgb)`，因此保存/传递的是这个表达式当前计算出的结果。
                    "wrist_image": array_sha256(wrist_rgb),
# 【L0854】语法拆解：表达式 `**{` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `**{` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    **{
# 【L0855】语法拆解：`name` 是参数/字段名；冒号 `:` 添加类型提示 `evidence["sha256"]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `name: evidence["sha256"]` 接入当前完整语句；`name` 表示本功能块中的 `name` 值；`evidence` 表示本功能块中的 `evidence` 值；`sha256` 表示本功能块中的 `sha256` 值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        name: evidence["sha256"]
# 【L0856】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for name, evidence in physical_state.items()` 中给出的序列，逐项完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        for name, evidence in physical_state.items()
# 【L0857】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    },
# 【L0858】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                },
# 【L0859】语法拆解：这是字典键值对：`"raw_action_shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `raw_actions.shape`。
# 【项目含义】定义字典/JSON 字段 `raw_action_shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `raw_action_shape` 数据；字段值来自 `list(raw_actions.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
                "raw_action_shape": list(raw_actions.shape),
# 【L0860】语法拆解：这是字典键值对：`"raw_action_dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `raw_actions.dtype`。
# 【项目含义】定义字典/JSON 字段 `raw_action_dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `raw_action_dtype` 数据；字段值来自 `str(raw_actions.dtype)`，因此保存/传递的是这个表达式当前计算出的结果。
                "raw_action_dtype": str(raw_actions.dtype),
# 【L0861】语法拆解：这是字典键值对：`"raw_action_sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `raw_actions`。
# 【项目含义】定义字典/JSON 字段 `raw_action_sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `raw_action_sha256` 数据；字段值来自 `array_sha256(raw_actions)`，因此保存/传递的是这个表达式当前计算出的结果。
                "raw_action_sha256": array_sha256(raw_actions),
# 【L0862】语法拆解：这是字典键值对：`"raw_gripper_targets"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`raw_actions[:, 6].tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `raw_gripper_targets`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `raw_gripper_targets` 数据；字段值来自 `raw_actions[:, 6].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "raw_gripper_targets": raw_actions[:, 6].tolist(),
# 【L0863】语法拆解：这是字典键值对：`"safe_action_shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe_actions.shape`。
# 【项目含义】定义字典/JSON 字段 `safe_action_shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `safe_action_shape` 数据；字段值来自 `list(safe_actions.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
                "safe_action_shape": list(safe_actions.shape),
# 【L0864】语法拆解：这是字典键值对：`"safe_action_dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe_actions.dtype`。
# 【项目含义】定义字典/JSON 字段 `safe_action_dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `safe_action_dtype` 数据；字段值来自 `str(safe_actions.dtype)`，因此保存/传递的是这个表达式当前计算出的结果。
                "safe_action_dtype": str(safe_actions.dtype),
# 【L0865】语法拆解：这是字典键值对：`"safe_action_sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `safe_actions`。
# 【项目含义】定义字典/JSON 字段 `safe_action_sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `safe_action_sha256` 数据；字段值来自 `array_sha256(safe_actions)`，因此保存/传递的是这个表达式当前计算出的结果。
                "safe_action_sha256": array_sha256(safe_actions),
# 【L0866】语法拆解：这是字典键值对：`"safe_gripper_targets"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`safe_actions[:, 6].tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `safe_gripper_targets`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `safe_gripper_targets` 数据；字段值来自 `safe_actions[:, 6].tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "safe_gripper_targets": safe_actions[:, 6].tolist(),
# 【L0867】语法拆解：这是字典键值对：`"executed_action_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`execute_count` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `executed_action_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `executed_action_count` 数据；字段值来自 `execute_count`，因此保存/传递的是这个表达式当前计算出的结果。
                "executed_action_count": execute_count,
# 【L0868】语法拆解：这是字典键值对：`"target_zone_arm_hold_active"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_zone_arm_hold_active` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `target_zone_arm_hold_active`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_zone_arm_hold_active` 数据；字段值来自 `target_zone_arm_hold_active`，因此保存/传递的是这个表达式当前计算出的结果。
                "target_zone_arm_hold_active": target_zone_arm_hold_active,
# 【L0869】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            }
# 【L0870】语法拆解：`policy_sampling_records` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sampling_record`。
# 【项目含义】对 `policy_sampling_records` 执行 `append`，把 `sampling_record` 加入已有结果；该集合表示策略相关值，随后会用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            policy_sampling_records.append(sampling_record)
# 【L0871】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(safe_actions[:execute_count])`，每次把当前元素放进 `action_index, action`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
            for action_index, action in enumerate(safe_actions[:execute_count]):
# 【L0872】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, arm_ids]`。右侧语法为：`torch.as_tensor(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】取当前七维动作的前六维作为 RM65 关节绝对目标，转换到仿真 GPU 与 state 相同 dtype。
                state[:, arm_ids] = torch.as_tensor(
# 【L0873】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `action[:6], device`。右侧语法为：`sim.device, dtype=state.dtype` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `action[:6], device=sim.device, dtype=state.dtype` 接入当前完整语句；`action` 表示动作相关值；`device` 表示本功能块中的 `device` 值；`sim` 表示IsaacLab SimulationContext，负责物理时间步。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    action[:6], device=sim.device, dtype=state.dtype
# 【L0874】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0875】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_target_rad`。右侧语法为：表达式 `float(action[6]) * 0.865` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把策略夹爪归一化目标乘 0.865 rad，恢复为 4C2 主关节在 Isaac 中使用的角度目标。
                gripper_target_rad = float(action[6]) * 0.865
# 【L0876】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, gripper_ids]`。右侧语法为：`gripper_target_rad` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `state[:, gripper_ids]`（写入 `state[:, gripper_ids]` 指定的字段）；右侧具体做的是：计算表达式 `gripper_target_rad`；`gripper_target_rad` 表示夹爪、目标相关值。
                state[:, gripper_ids] = gripper_target_rad
# 【L0877】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `last_executed_gripper_target`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `action[6]`；其中 `action[6]` 的方括号表示先从 `action` 按键/索引 `6` 取值。
# 【项目含义】得到 `last_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(action[6])`；`action` 表示动作相关值。
                last_executed_gripper_target = float(action[6])
# 【L0878】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_executed_gripper_target`。右侧语法为：`min(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `minimum_executed_gripper_target`，它在本项目中表示夹爪、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `min(` 的结果保存下来，供当前功能块后续使用。
                minimum_executed_gripper_target = min(
# 【L0879】语法拆解：`minimum_executed_gripper_target, last_executed_gripper_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `minimum_executed_gripper_target, last_executed_gripper_target` 接入当前完整语句；`minimum_executed_gripper_target` 表示夹爪、目标相关值；`last_executed_gripper_target` 表示夹爪、目标相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    minimum_executed_gripper_target, last_executed_gripper_target
# 【L0880】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0881】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】一个 policy 动作保持 `record_stride_steps` 个 240 Hz 物理步；默认 12 步，即每个动作持续约 0.05 秒。
                for _ in range(args.record_stride_steps):
# 【L0882】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `set_joint_position_target` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `state`。
# 【项目含义】调用 `robot.set_joint_position_target`：设置关节位置控制器的目标值；本行实际操作 `robot.set_joint_position_target(state)`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`set_joint_position_target` 表示关节、位置、目标相关值。
                    robot.set_joint_position_target(state)
# 【L0883】语法拆解：`episode_capture.before_step(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `episode_capture` 调用多行方法 `before_step`：调用 `episode_capture` 提供的 `before_step` 操作；具体参数写在随后几行，用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    episode_capture.before_step(
# 【L0884】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                        robot,
# 【L0885】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                        cube,
# 【L0886】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                        state,
# 【L0887】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}"`；`f` 表示本功能块中的 `f` 值；`PI05_CHUNK_` 表示本功能块中的 `PI05_CHUNK_` 值；`chunk_index` 表示索引相关值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        f"PI05_CHUNK_{chunk_index:03d}_ACTION_{action_index:02d}",
# 【L0888】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    )
# 【L0889】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】调用 `robot.write_data_to_sim`：把缓存的机器人命令提交给 PhysX；本行实际操作 `robot.write_data_to_sim()`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`write_data_to_sim` 表示仿真相关值。
                    robot.write_data_to_sim()
# 【L0890】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_data_to_sim` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `cube` 调用 `write_data_to_sim()`：调用 `cube` 提供的 `write_data_to_sim` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    cube.write_data_to_sim()
# 【L0891】语法拆解：`sim` 是模块/对象，点号 `.` 从中取出 `step` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `render=False`。
# 【项目含义】调用 `sim.step`：让 Isaac 物理世界向前推进一个时间步；本行实际操作 `sim.step(render=False)`。`sim` 表示IsaacLab SimulationContext，负责物理时间步；`step` 表示步相关值。
                    sim.step(render=False)
# 【L0892】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `robot.update`：把仿真后的机器人状态刷新到 IsaacLab 缓冲区；本行实际操作 `robot.update(sim.get_physics_dt())`。`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`update` 表示本功能块中的 `update` 值。
                    robot.update(sim.get_physics_dt())
# 【L0893】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】调用 `cube.update`：把仿真后的方块状态刷新到 IsaacLab 缓冲区；本行实际操作 `cube.update(sim.get_physics_dt())`。`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`update` 表示本功能块中的 `update` 值。
                    cube.update(sim.get_physics_dt())
# 【L0894】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `CONTACT_SENSORS.values()`，每次把当前元素放进 `contact_sensor`；这会逐个处理“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”所需的帧、episode、动作或实验 case。
                    for contact_sensor in CONTACT_SENSORS.values():
# 【L0895】语法拆解：`contact_sensor` 是模块/对象，点号 `.` 从中取出 `update` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim.get_physics_dt()`。
# 【项目含义】对 `contact_sensor` 执行 `update`，把 `sim.get_physics_dt()` 加入已有结果；该集合表示接触相关值，随后会用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                        contact_sensor.update(sim.get_physics_dt())
# 【L0896】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_cube_z`。右侧语法为：`max` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `max_cube_z`；第 2 个实参 `float(cube.data.root_pos_w[0, 2].item())`。
# 【项目含义】得到 `max_cube_z`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
                    max_cube_z = max(max_cube_z, float(cube.data.root_pos_w[0, 2].item()))
# 【L0897】语法拆解：表达式 `executed_actions += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `executed_actions + 1` 更新 `executed_actions` 原值；`executed_actions` 表示实际送进 Isaac 控制器的七维动作步数，常用于累计步数、距离、损失或成功次数。
                executed_actions += 1
# 【L0898】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0899】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_cube`。右侧语法为：`cube.data.root_pos_w[0].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】动作执行后读取方块在世界坐标中的实际 xyz，用新物理状态判断进展并准备下一轮重规划。
            current_cube = cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L0900】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_error`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(current_cube - target_block_position)`。
# 【项目含义】计算当前方块中心到目标中心的三维距离，单位米；小于 0.05 m 是成功候选条件之一。
            target_error = float(np.linalg.norm(current_cube - target_block_position))
# 【L0901】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_source_displacement`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cube_source_displacement`，它在本项目中表示任务方块、源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
            cube_source_displacement = float(
# 【L0902】语法拆解：`np.linalg.norm(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】调用 `np.linalg.norm`：计算向量长度/欧氏距离；本行实际操作 `np.linalg.norm(`。`linalg` 表示本功能块中的 `linalg` 值；`norm` 表示本功能块中的 `norm` 值。
                np.linalg.norm(
# 【L0903】语法拆解：表达式 `current_cube - settled_source_position.detach().cpu().numpy()` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】对 `current_cube - settled_source_position` 调用 `detach().cpu().numpy()`：调用 `current_cube - settled_source_position` 提供的 `detach` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    current_cube - settled_source_position.detach().cpu().numpy()
# 【L0904】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0905】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0906】语法拆解：`if` 要求条件 `not np.isfinite(current_cube).all()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查数值中是否出现 NaN 或正负无穷；发现任何非有限值就进入错误处理，避免仿真/训练发散
            if not np.isfinite(current_cube).all():
# 【L0907】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_safety_abort_reason`。右侧语法为：`"non_finite_cube_position"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `simulation_safety_abort_reason`，它在本项目中表示本功能块中的 `simulation_safety_abort_reason` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"non_finite_cube_position"`；`non_finite_cube_position` 表示任务方块、位置相关值。
                simulation_safety_abort_reason = "non_finite_cube_position"
# 【L0908】语法拆解：`elif` 要求条件 `cube_source_displacement > CUBE_WORKSPACE_ESCAPE_RADIUS_M` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】前面的条件未成立时，继续判断 `cube_source_displacement > CUBE_WORKSPACE_ESCAPE_RADIUS_M` 是否成立；`cube_source_displacement` 表示任务方块、源位置相关值；`CUBE_WORKSPACE_ESCAPE_RADIUS_M` 表示任务方块相关值
            elif cube_source_displacement > CUBE_WORKSPACE_ESCAPE_RADIUS_M:
# 【L0909】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_safety_abort_reason`。右侧语法为：`"cube_outside_workspace_envelope"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】得到 `simulation_safety_abort_reason`，它在本项目中表示本功能块中的 `simulation_safety_abort_reason` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `"cube_outside_workspace_envelope"`；`cube_outside_workspace_envelope` 表示任务方块相关值。
                simulation_safety_abort_reason = "cube_outside_workspace_envelope"
# 【L0910】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actual_gripper_normalized`。右侧语法为：`normalize_gripper(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actual_gripper_normalized`，它在本项目中表示物理仿真实际值、夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
            actual_gripper_normalized = normalize_gripper(
# 【L0911】语法拆解：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_pos[0, gripper_master_id].item()`。
# 【项目含义】对 `float(robot.data.joint_pos[0, gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0912】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0913】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_observed_gripper_normalized`。右侧语法为：`min(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `minimum_observed_gripper_normalized`，它在本项目中表示夹爪、归一化相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `min(` 的结果保存下来，供当前功能块后续使用。
            minimum_observed_gripper_normalized = min(
# 【L0914】语法拆解：`minimum_observed_gripper_normalized, actual_gripper_normalized` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `minimum_observed_gripper_normalized, actual_gripper_normalized` 接入当前完整语句；`minimum_observed_gripper_normalized` 表示夹爪、归一化相关值；`actual_gripper_normalized` 表示物理仿真实际值、夹爪、归一化相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                minimum_observed_gripper_normalized, actual_gripper_normalized
# 【L0915】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0916】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_open`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `gripper_open`，它在本项目中表示实际夹爪反馈是否低于校准张开阈值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            gripper_open = (
# 【L0917】语法拆解：`actual_gripper_normalized` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `actual_gripper_normalized`；在本项目中它表示物理仿真实际值、夹爪、归一化相关值。
                actual_gripper_normalized
# 【L0918】语法拆解：表达式 `< args.policy_gripper_actual_open_threshold` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `< args.policy_gripper_actual_open_threshold` 接入当前完整语句；`policy_gripper_actual_open_threshold` 表示策略、夹爪、物理仿真实际值相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                < args.policy_gripper_actual_open_threshold
# 【L0919】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0920】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_command_open`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `gripper_command_open`，它在本项目中表示最近一次真正执行的模型夹爪命令是否要求张开；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            gripper_command_open = (
# 【L0921】语法拆解：`last_executed_gripper_target is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `last_executed_gripper_target is not None` 接入当前完整语句；`last_executed_gripper_target` 表示夹爪、目标相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                last_executed_gripper_target is not None
# 【L0922】语法拆解：表达式 `and last_executed_gripper_target < args.policy_gripper_open_threshold` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `last_executed_gripper_target < args.policy_gripper_open_threshold` 用“并且”接到上一行判断中；按表达式 `last_executed_gripper_target < args.policy_gripper_open_threshold` 检查夹爪阈值或开合状态；该阈值决定 4C2 是否被视为已张开。所有连接条件共同决定是否进入后续分支。
                and last_executed_gripper_target < args.policy_gripper_open_threshold
# 【L0923】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0924】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lifted`。右侧语法为：表达式 `max_cube_z - float(settled_source_position[2].item()) > 0.02` 使用运算符 `-`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】判断方块在本 episode 中的最高 z 是否比初始稳定 z 高 2 cm 以上，排除仅在桌面滑到目标的假成功。
            lifted = max_cube_z - float(settled_source_position[2].item()) > 0.02
# 【L0925】语法拆解：`if` 要求条件 `lifted and target_error < 0.05 and gripper_open and gripper_command_open` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】只有方块被抬起、到达目标、实际夹爪张开且最后执行的模型命令也要求张开，才累计一次成功候选。
            if lifted and target_error < 0.05 and gripper_open and gripper_command_open:
# 【L0926】语法拆解：表达式 `consecutive_candidate_chunks += 1` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `consecutive_candidate_chunks + 1` 更新 `consecutive_candidate_chunks` 原值；`consecutive_candidate_chunks` 表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数，常用于累计步数、距离、损失或成功次数。
                consecutive_candidate_chunks += 1
# 【L0927】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中处理剩余输入或备用路径。
            else:
# 【L0928】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `consecutive_candidate_chunks`。右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】得到 `consecutive_candidate_chunks`，它在本项目中表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
                consecutive_candidate_chunks = 0
# 【L0929】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
            print(
# 【L0930】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"PI05_CHUNK="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "PI05_CHUNK="
# 【L0931】语法拆解：表达式 `+ json.dumps(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
                + json.dumps(
# 【L0932】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    {
# 【L0933】语法拆解：这是字典键值对：`"index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`chunk_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `index`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `index` 数据；字段值来自 `chunk_index`，因此保存/传递的是这个表达式当前计算出的结果。
                        "index": chunk_index,
# 【L0934】语法拆解：这是字典键值对：`"latency_s"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`inference_latencies[-1]` 使用方括号索引；先计算 `-1`，再从 `inference_latencies` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `latency_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `latency_s` 数据；字段值来自 `inference_latencies[-1]`，因此保存/传递的是这个表达式当前计算出的结果。
                        "latency_s": inference_latencies[-1],
# 【L0935】语法拆解：这是字典键值对：`"target_error_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_error` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `target_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_error_m` 数据；字段值来自 `target_error`，因此保存/传递的是这个表达式当前计算出的结果。
                        "target_error_m": target_error,
# 【L0936】语法拆解：这是字典键值对：`"lifted"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lifted` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `lifted`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `lifted` 数据；字段值来自 `lifted`，因此保存/传递的是这个表达式当前计算出的结果。
                        "lifted": lifted,
# 【L0937】语法拆解：这是字典键值对：`"gripper_open"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`gripper_open` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gripper_open`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_open` 数据；字段值来自 `gripper_open`，因此保存/传递的是这个表达式当前计算出的结果。
                        "gripper_open": gripper_open,
# 【L0938】语法拆解：这是字典键值对：`"gripper_command_open"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`gripper_command_open` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gripper_command_open`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_command_open` 数据；字段值来自 `gripper_command_open`，因此保存/传递的是这个表达式当前计算出的结果。
                        "gripper_command_open": gripper_command_open,
# 【L0939】语法拆解：这是字典键值对：`"actual_gripper_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_gripper_normalized` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `actual_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `actual_gripper_normalized` 数据；字段值来自 `actual_gripper_normalized`，因此保存/传递的是这个表达式当前计算出的结果。
                        "actual_gripper_normalized": actual_gripper_normalized,
# 【L0940】语法拆解：这是字典键值对：`"last_executed_gripper_target"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`last_executed_gripper_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `last_executed_gripper_target`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `last_executed_gripper_target` 数据；字段值来自 `last_executed_gripper_target`，因此保存/传递的是这个表达式当前计算出的结果。
                        "last_executed_gripper_target": last_executed_gripper_target,
# 【L0941】语法拆解：这是字典键值对：`"cube_source_displacement_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`cube_source_displacement` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `cube_source_displacement_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `cube_source_displacement_m` 数据；字段值来自 `cube_source_displacement`，因此保存/传递的是这个表达式当前计算出的结果。
                        "cube_source_displacement_m": cube_source_displacement,
# 【L0942】语法拆解：这是字典键值对：`"simulation_safety_abort_reason"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`simulation_safety_abort_reason` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_safety_abort_reason`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `simulation_safety_abort_reason` 数据；字段值来自 `simulation_safety_abort_reason`，因此保存/传递的是这个表达式当前计算出的结果。
                        "simulation_safety_abort_reason": simulation_safety_abort_reason,
# 【L0943】语法拆解：这是字典键值对：`"policy_sampling"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`sampling_record` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `policy_sampling`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_sampling` 数据；字段值来自 `sampling_record`，因此保存/传递的是这个表达式当前计算出的结果。
                        "policy_sampling": sampling_record,
# 【L0944】语法拆解：这是字典键值对：`"guard"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`guard` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `guard`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `guard` 数据；字段值来自 `guard`，因此保存/传递的是这个表达式当前计算出的结果。
                        "guard": guard,
# 【L0945】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    }
# 【L0946】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                ),
# 【L0947】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                flush=True,
# 【L0948】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            )
# 【L0949】语法拆解：`if` 要求条件 `simulation_safety_abort_reason is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `simulation_safety_abort_reason is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if simulation_safety_abort_reason is not None:
# 【L0950】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:]`。右侧语法为：`robot.data.joint_pos` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】把右侧结果写进 `state[:]`（写入 `state[:]` 指定的字段）；右侧具体做的是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
                state[:] = robot.data.joint_pos.detach()
# 【L0951】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
                print(
# 【L0952】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"PI05_STAGE=SIMULATION_SAFETY_ABORT:{simulation_safety_abort_reason}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"PI05_STAGE=SIMULATION_SAFETY_ABORT:{simulation_safety_abort_reason}"`；`f` 表示本功能块中的 `f` 值；`PI05_STAGE` 表示本功能块中的 `PI05_STAGE` 值；`SIMULATION_SAFETY_ABORT` 表示本功能块中的 `SIMULATION_SAFETY_ABORT` 值，它参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    f"PI05_STAGE=SIMULATION_SAFETY_ABORT:{simulation_safety_abort_reason}",
# 【L0953】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    flush=True,
# 【L0954】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0955】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L0956】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
            if (
# 【L0957】语法拆解：`consecutive_candidate_chunks` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `consecutive_candidate_chunks`；在本项目中它表示连续满足抬升、到位、实际张开和命令张开条件的动作块计数。
                consecutive_candidate_chunks
# 【L0958】语法拆解：表达式 `>= args.policy_release_required_consecutive_chunks` 使用运算符 `>=`, `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `>= args.policy_release_required_consecutive_chunks` 接入当前完整语句；`policy_release_required_consecutive_chunks` 表示策略相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                >= args.policy_release_required_consecutive_chunks
# 【L0959】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ):
# 【L0960】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PI05_STAGE=SUCCESS_CANDIDATE"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PI05_STAGE=SUCCESS_CANDIDATE", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
                print("PI05_STAGE=SUCCESS_CANDIDATE", flush=True)
# 【L0961】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_postcondition_arm_target`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `release_postcondition_arm_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
                release_postcondition_arm_target = (
# 【L0962】语法拆解：`robot.data.joint_pos[0, arm_ids].detach().cpu().tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `robot.data.joint_pos[0, arm_ids]` 调用 `detach().cpu().tolist()`：调用 `robot.data.joint_pos[0, arm_ids]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                    robot.data.joint_pos[0, arm_ids].detach().cpu().tolist()
# 【L0963】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                )
# 【L0964】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, arm_ids]`。右侧语法为：`robot.data.joint_pos[:, arm_ids].detach()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把手臂目标锁定为当前实际六关节角，避免释放稳定验证期间继续追逐旧的模型动作。
                state[:, arm_ids] = robot.data.joint_pos[:, arm_ids].detach()
# 【L0965】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, gripper_ids]`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】把所有 4C2 关节目标设为 0，也就是完全张开；只有模型已连续选择释放时才运行到这里。
                state[:, gripper_ids] = 0.0
# 【L0966】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_postcondition_applied`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `release_postcondition_applied`，它在本项目中表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                release_postcondition_applied = True
# 【L0967】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PI05_STAGE=RELEASE_POSTCONDITION_LATCHED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PI05_STAGE=RELEASE_POSTCONDITION_LATCHED", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
                print("PI05_STAGE=RELEASE_POSTCONDITION_LATCHED", flush=True)
# 【L0968】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L0969】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
    finally:
# 【L0970】语法拆解：`client._ws` 是模块/对象，点号 `.` 从中取出 `close` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `client._ws` 调用 `close()`：关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        client._ws.close()
# 【L0971】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L0972】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_A", episode_capture)
# 【L0973】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `settle_a`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `settle_a`，它在本项目中表示本功能块中的 `settle_a` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    settle_a = cube.data.root_pos_w[0].clone()
# 【L0974】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    hold(sim, robot, cube, state, 120, "PI05_SETTLE_B", episode_capture)
# 【L0975】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    final_position = cube.data.root_pos_w[0].clone()
# 【L0976】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_np`。右侧语法为：`settled_source_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `source_np`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `settled_source_position.detach().cpu().numpy()`；`settled_source_position` 表示源位置、位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    source_np = settled_source_position.detach().cpu().numpy()
# 【L0977】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_np`。右侧语法为：`final_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `final_np`，它在本项目中表示本功能块中的 `final_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `final_position.detach().cpu().numpy()`；`final_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    final_np = final_position.detach().cpu().numpy()
# 【L0978】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_target_xy_error`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np[:2] - target_block_position[:2])`。
# 【项目含义】得到 `final_target_xy_error`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L0979】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_target_position_error`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np - target_block_position)`。
# 【项目含义】得到 `final_target_position_error`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L0980】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_to_target_distance`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np[:2] - source_np[:2])`。
# 【项目含义】得到 `source_to_target_distance`，它在本项目中表示源位置、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    source_to_target_distance = float(np.linalg.norm(final_np[:2] - source_np[:2]))
# 【L0981】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_height`。右侧语法为：表达式 `max_cube_z - float(source_np[2])` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `lift_height`，它在本项目中表示本功能块中的 `lift_height` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max_cube_z - float(source_np[2])`；`max_cube_z` 表示任务方块相关值；`source_np` 表示源位置相关值。
    lift_height = max_cube_z - float(source_np[2])
# 【L0982】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `post_release_drift`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `torch.linalg.vector_norm(final_position - settle_a).item()`。
# 【项目含义】得到 `post_release_drift`，它在本项目中表示本功能块中的 `post_release_drift` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    post_release_drift = float(torch.linalg.vector_norm(final_position - settle_a).item())
# 【L0983】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_gripper`。右侧语法为：`normalize_gripper(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `final_gripper`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把 4C2 主关节弧度除以 0.865 并裁到 0～1，得到 0 张开、1 闭合的策略值。
    final_gripper = normalize_gripper(
# 【L0984】语法拆解：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_pos[0, gripper_master_id].item()`。
# 【项目含义】对 `float(robot.data.joint_pos[0, gripper_master_id]` 调用 `item())`：调用 `float(robot.data.joint_pos[0, gripper_master_id]` 提供的 `item` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        float(robot.data.joint_pos[0, gripper_master_id].item())
# 【L0985】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0986】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `all_states_finite`。右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `all_states_finite`，它在本项目中表示本功能块中的 `all_states_finite` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    all_states_finite = bool(
# 【L0987】语法拆解：`torch` 是模块/对象，点号 `.` 从中取出 `isfinite` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_pos).all(`。
# 【项目含义】对 `torch` 调用 `isfinite(robot.data.joint_pos).all()`：调用 `torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        torch.isfinite(robot.data.joint_pos).all()
# 【L0988】语法拆解：`and torch.isfinite(cube.data.root_state_w).all()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `and torch` 调用 `isfinite(cube.data.root_state_w).all()`：调用 `and torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        and torch.isfinite(cube.data.root_state_w).all()
# 【L0989】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L0990】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `passed`。右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    passed = bool(
# 【L0991】语法拆解：表达式 `action_chunks > 0` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `action_chunks > 0` 接到上一行尚未结束的布尔表达式；`action_chunks` 表示本 episode 已向 π0.5 请求的动作块数量。比较结果共同决定“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”是否通过。
        action_chunks > 0
# 【L0992】语法拆解：表达式 `and source_to_target_distance > 0.12` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `source_to_target_distance > 0.12` 用“并且”接到上一行判断中；判断 `source_to_target_distance > 0.12` 是否成立；`source_to_target_distance` 表示源位置、目标相关值。所有连接条件共同决定是否进入后续分支。
        and source_to_target_distance > 0.12
# 【L0993】语法拆解：表达式 `and lift_height > 0.02` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `lift_height > 0.02` 用“并且”接到上一行判断中；判断 `lift_height > 0.02` 是否成立；`lift_height` 表示本功能块中的 `lift_height` 值。所有连接条件共同决定是否进入后续分支。
        and lift_height > 0.02
# 【L0994】语法拆解：表达式 `and final_target_xy_error < 0.05` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `final_target_xy_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_xy_error < 0.05` 是否成立；`final_target_xy_error` 表示目标相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_xy_error < 0.05
# 【L0995】语法拆解：表达式 `and final_target_position_error < 0.05` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `final_target_position_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_position_error < 0.05` 是否成立；`final_target_position_error` 表示目标、位置相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_position_error < 0.05
# 【L0996】语法拆解：表达式 `and post_release_drift < 0.02` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `post_release_drift < 0.02` 用“并且”接到上一行判断中；判断 `post_release_drift < 0.02` 是否成立；`post_release_drift` 表示本功能块中的 `post_release_drift` 值。所有连接条件共同决定是否进入后续分支。
        and post_release_drift < 0.02
# 【L0997】语法拆解：`and release_postcondition_applied` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `release_postcondition_applied` 用“并且”接到上一行判断中；判断 `release_postcondition_applied` 是否成立；`release_postcondition_applied` 表示是否已在模型选择释放后锁住手臂并完全张开夹爪进行稳定验证。所有连接条件共同决定是否进入后续分支。
        and release_postcondition_applied
# 【L0998】语法拆解：`and all_states_finite` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `all_states_finite` 用“并且”接到上一行判断中；判断 `all_states_finite` 是否成立；`all_states_finite` 表示本功能块中的 `all_states_finite` 值。所有连接条件共同决定是否进入后续分支。
        and all_states_finite
# 【L0999】语法拆解：`and simulation_safety_abort_reason is None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `simulation_safety_abort_reason is None` 用“并且”接到上一行判断中；检查 `simulation_safety_abort_reason is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理。所有连接条件共同决定是否进入后续分支。
        and simulation_safety_abort_reason is None
# 【L1000】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    )
# 【L1001】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L1002】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["task_success"]`。右侧语法为：`passed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：计算表达式 `passed`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    episode_recorder.metadata["task_success"] = passed
# 【L1003】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["pi05_used"]`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["pi05_used"]`（写入 `episode_recorder.metadata["pi05_used"]` 指定的字段）；右侧具体做的是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["pi05_used"] = True
# 【L1004】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["training_ready"]`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["training_ready"]`（写入 `episode_recorder.metadata["training_ready"]` 指定的字段）；右侧具体做的是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["training_ready"] = False
# 【L1005】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["evaluation_only"]`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["evaluation_only"]`（写入 `episode_recorder.metadata["evaluation_only"]` 指定的字段）；右侧具体做的是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
    episode_recorder.metadata["evaluation_only"] = True
# 【L1006】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `manifest`。右侧语法为：`episode_recorder` 是模块/对象，点号 `.` 从中取出 `save` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `manifest`，它在本项目中表示描述磁盘数据含义、数量和路径的元数据清单；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
    manifest = episode_recorder.save()
# 【L1007】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `validation`。右侧语法为：`validate_episode` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_recorder.output_dir`；第 2 个实参 `require_images=True`。
# 【项目含义】得到 `validation`，它在本项目中表示校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(episode_recorder.output_dir, require_images=True)`；`validate_episode` 表示一条轨迹相关值；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值。
    validation = validate_episode(episode_recorder.output_dir, require_images=True)
# 【L1008】语法拆解：`if` 要求条件 `validation["status"] != "pass"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `validation["status"] != "pass"` 是否成立；`validation` 表示校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
    if validation["status"] != "pass":
# 【L1009】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")` 并停止当前路径；说明当前输入违反“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"pi0.5 evaluation episode failed validation: {validation}")
# 【L1010】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_observation`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `initial_policy_observation`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    initial_policy_observation = None
# 【L1011】语法拆解：`if` 要求条件 `initial_policy_observation_images is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `initial_policy_observation_images is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if initial_policy_observation_images is not None:
# 【L1012】语法拆解：`from PIL` 指定来源模块；`import Image` 把所需名字放进当前文件，之后可直接使用这些名字。
# 【项目含义】从 `PIL` 引入 `Image`。在这份程序里，`PIL` 用于Pillow 图像库，用于 PNG/RGB 读写；后续出现这些名字时调用的是这里的外部能力。
        from PIL import Image
# 【L1013】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L1014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `observation_dir`。右侧语法为：表达式 `episode_recorder.output_dir / "policy_observations"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `observation_dir`，它在本项目中表示本功能块中的 `observation_dir` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.output_dir / "policy_observations"`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值；`policy_observations` 表示策略相关值。
        observation_dir = episode_recorder.output_dir / "policy_observations"
# 【L1015】语法拆解：`observation_dir` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `observation_dir.mkdir(parents=True, exist_ok=True)`。`observation_dir` 表示本功能块中的 `observation_dir` 值；`mkdir` 表示本功能块中的 `mkdir` 值。
        observation_dir.mkdir(parents=True, exist_ok=True)
# 【L1016】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_path`。右侧语法为：表达式 `observation_dir / "chunk_000_external.png"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `external_path`，它在本项目中表示外部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `observation_dir / "chunk_000_external.png"`；`observation_dir` 表示本功能块中的 `observation_dir` 值；`chunk_000_external` 表示外部相机相关值；`png` 表示本功能块中的 `png` 值。
        external_path = observation_dir / "chunk_000_external.png"
# 【L1017】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_path`。右侧语法为：表达式 `observation_dir / "chunk_000_wrist.png"` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `wrist_path`，它在本项目中表示腕部相机、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `observation_dir / "chunk_000_wrist.png"`；`observation_dir` 表示本功能块中的 `observation_dir` 值；`chunk_000_wrist` 表示腕部相机相关值；`png` 表示本功能块中的 `png` 值。
        wrist_path = observation_dir / "chunk_000_wrist.png"
# 【L1018】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_initial, wrist_initial`。右侧语法为：`initial_policy_observation_images` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `external_initial, wrist_initial`；`external_initial` 表示外部相机相关值；`wrist_initial` 表示腕部相机相关值。右侧的来源是：计算表达式 `initial_policy_observation_images`；`initial_policy_observation_images` 表示策略相关值。
        external_initial, wrist_initial = initial_policy_observation_images
# 【L1019】语法拆解：`Image` 是模块/对象，点号 `.` 从中取出 `fromarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_initial).save(external_path`。
# 【项目含义】对 `Image` 调用 `fromarray(external_initial).save(external_path)`：调用 `Image` 提供的 `fromarray` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        Image.fromarray(external_initial).save(external_path)
# 【L1020】语法拆解：`Image` 是模块/对象，点号 `.` 从中取出 `fromarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_initial).save(wrist_path`。
# 【项目含义】对 `Image` 调用 `fromarray(wrist_initial).save(wrist_path)`：调用 `Image` 提供的 `fromarray` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        Image.fromarray(wrist_initial).save(wrist_path)
# 【L1021】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `initial_policy_observation`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `initial_policy_observation`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        initial_policy_observation = {
# 【L1022】语法拆解：这是字典键值对：`"chunk_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `chunk_index`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `chunk_index` 数据；字段值来自 `0`，因此保存/传递的是这个表达式当前计算出的结果。
            "chunk_index": 0,
# 【L1023】语法拆解：这是字典键值对：`"saved_after_control_completed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `saved_after_control_completed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `saved_after_control_completed` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "saved_after_control_completed": True,
# 【L1024】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `external_image`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `external_image` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "external_image": {
# 【L1025】语法拆解：这是字典键值对：`"path"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_path.relative_to(episode_recorder.output_dir)`。
# 【项目含义】定义字典/JSON 字段 `path`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `path` 数据；字段值来自 `str(external_path.relative_to(episode_recorder.output_dir))`，因此保存/传递的是这个表达式当前计算出的结果。
                "path": str(external_path.relative_to(episode_recorder.output_dir)),
# 【L1026】语法拆解：这是字典键值对：`"shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_initial.shape`。
# 【项目含义】定义字典/JSON 字段 `shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `shape` 数据；字段值来自 `list(external_initial.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": list(external_initial.shape),
# 【L1027】语法拆解：这是字典键值对：`"dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_initial.dtype`。
# 【项目含义】定义字典/JSON 字段 `dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `dtype` 数据；字段值来自 `str(external_initial.dtype)`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": str(external_initial.dtype),
# 【L1028】语法拆解：这是字典键值对：`"sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_initial`。
# 【项目含义】定义字典/JSON 字段 `sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `sha256` 数据；字段值来自 `array_sha256(external_initial)`，因此保存/传递的是这个表达式当前计算出的结果。
                "sha256": array_sha256(external_initial),
# 【L1029】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            },
# 【L1030】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `wrist_image`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `wrist_image` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "wrist_image": {
# 【L1031】语法拆解：这是字典键值对：`"path"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_path.relative_to(episode_recorder.output_dir)`。
# 【项目含义】定义字典/JSON 字段 `path`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `path` 数据；字段值来自 `str(wrist_path.relative_to(episode_recorder.output_dir))`，因此保存/传递的是这个表达式当前计算出的结果。
                "path": str(wrist_path.relative_to(episode_recorder.output_dir)),
# 【L1032】语法拆解：这是字典键值对：`"shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_initial.shape`。
# 【项目含义】定义字典/JSON 字段 `shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `shape` 数据；字段值来自 `list(wrist_initial.shape)`，因此保存/传递的是这个表达式当前计算出的结果。
                "shape": list(wrist_initial.shape),
# 【L1033】语法拆解：这是字典键值对：`"dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_initial.dtype`。
# 【项目含义】定义字典/JSON 字段 `dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `dtype` 数据；字段值来自 `str(wrist_initial.dtype)`，因此保存/传递的是这个表达式当前计算出的结果。
                "dtype": str(wrist_initial.dtype),
# 【L1034】语法拆解：这是字典键值对：`"sha256"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`array_sha256` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `wrist_initial`。
# 【项目含义】定义字典/JSON 字段 `sha256`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `sha256` 数据；字段值来自 `array_sha256(wrist_initial)`，因此保存/传递的是这个表达式当前计算出的结果。
                "sha256": array_sha256(wrist_initial),
# 【L1035】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            },
# 【L1036】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        }
# 【L1037】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L1038】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass" if passed else "fail"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L1039】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L1040】语法拆解：这是字典键值对：`"pi05_used"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `pi05_used`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `pi05_used` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": True,
# 【L1041】语法拆解：这是字典键值对：`"expert"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】定义字典/JSON 字段 `expert`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `expert` 数据；字段值来自 `None`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": None,
# 【L1042】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L1043】语法拆解：这是字典键值对：`"policy_checkpoint_id"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_checkpoint_id`。
# 【项目含义】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `args.policy_checkpoint_id`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_checkpoint_id": args.policy_checkpoint_id,
# 【L1044】语法拆解：这是字典键值对：`"policy_noise_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_noise_seed`。
# 【项目含义】定义字典/JSON 字段 `policy_noise_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_noise_seed` 数据；字段值来自 `args.policy_noise_seed`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_noise_seed": args.policy_noise_seed,
# 【L1045】语法拆解：这是字典键值对：`"simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`CONFIGURED_SIMULATION_SEED` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `simulation_seed` 数据；字段值来自 `CONFIGURED_SIMULATION_SEED`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_seed": CONFIGURED_SIMULATION_SEED,
# 【L1046】语法拆解：这是字典键值对：`"prompt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`episode_prompt`。
# 【项目含义】定义字典/JSON 字段 `prompt`，它表示与本帧/episode 配套的自然语言任务指令；字段值来自 `args.episode_prompt`，因此保存/传递的是这个表达式当前计算出的结果。
        "prompt": args.episode_prompt,
# 【L1047】语法拆解：这是字典键值对：`"transfer_joint_1_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1048】语法拆解：这是字典键值对：`"source_offset_xy_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `source_offset_xy_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_offset_xy_m` 数据；字段值来自 `[args.source_offset_x_m, args.source_offset_y_m]`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L1049】语法拆解：这是字典键值对：`"action_chunks"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`action_chunks` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `action_chunks`，它表示向 π0.5 发起推理的次数；字段值来自 `action_chunks`，因此保存/传递的是这个表达式当前计算出的结果。
        "action_chunks": action_chunks,
# 【L1050】语法拆解：这是字典键值对：`"executed_actions"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`executed_actions` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `executed_actions`，它表示真正送入 Isaac 控制器的动作步数；字段值来自 `executed_actions`，因此保存/传递的是这个表达式当前计算出的结果。
        "executed_actions": executed_actions,
# 【L1051】语法拆解：这是字典键值对：`"policy_action_horizon"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`int(len(raw_actions)) if action_chunks else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `policy_action_horizon`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_action_horizon` 数据；字段值来自 `int(len(raw_actions)) if action_chunks else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "policy_action_horizon": int(len(raw_actions)) if action_chunks else None,
# 【L1052】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `controller_config`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `controller_config` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "controller_config": {
# 【L1053】语法拆解：这是字典键值对：`"policy_max_action_chunks"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_max_action_chunks`。
# 【项目含义】定义字典/JSON 字段 `policy_max_action_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_max_action_chunks` 数据；字段值来自 `args.policy_max_action_chunks`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_max_action_chunks": args.policy_max_action_chunks,
# 【L1054】语法拆解：这是字典键值对：`"policy_execute_actions_per_chunk"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_execute_actions_per_chunk`。
# 【项目含义】定义字典/JSON 字段 `policy_execute_actions_per_chunk`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_execute_actions_per_chunk` 数据；字段值来自 `args.policy_execute_actions_per_chunk`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_execute_actions_per_chunk": args.policy_execute_actions_per_chunk,
# 【L1055】语法拆解：这是字典键值对：`"record_stride_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_stride_steps`。
# 【项目含义】定义字典/JSON 字段 `record_stride_steps`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `record_stride_steps` 数据；字段值来自 `args.record_stride_steps`，因此保存/传递的是这个表达式当前计算出的结果。
            "record_stride_steps": args.record_stride_steps,
# 【L1056】语法拆解：这是字典键值对：`"physics_dt_s"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`sim` 是模块/对象，点号 `.` 从中取出 `get_physics_dt` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `physics_dt_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `physics_dt_s` 数据；字段值来自 `sim.get_physics_dt()`，因此保存/传递的是这个表达式当前计算出的结果。
            "physics_dt_s": sim.get_physics_dt(),
# 【L1057】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `executed_action_hold_seconds`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `executed_action_hold_seconds` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "executed_action_hold_seconds": (
# 【L1058】语法拆解：表达式 `args.record_stride_steps * sim.get_physics_dt()` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】对 `args.record_stride_steps * sim` 调用 `get_physics_dt()`：调用 `args.record_stride_steps * sim` 提供的 `get_physics_dt` 操作。本行产生的修改/返回值服务于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
                args.record_stride_steps * sim.get_physics_dt()
# 【L1059】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1060】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `success_candidate_required_consecutive_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `success_candidate_required_consecutive_chunks` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "success_candidate_required_consecutive_chunks": (
# 【L1061】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_release_required_consecutive_chunks`。
# 【项目含义】把表达式/参数 `args.policy_release_required_consecutive_chunks` 接入当前完整语句；`policy_release_required_consecutive_chunks` 表示策略相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.policy_release_required_consecutive_chunks
# 【L1062】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1063】语法拆解：这是字典键值对：`"policy_gripper_open_threshold"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_open_threshold`。
# 【项目含义】定义字典/JSON 字段 `policy_gripper_open_threshold`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_gripper_open_threshold` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_gripper_open_threshold": args.policy_gripper_open_threshold,
# 【L1064】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `policy_gripper_actual_open_threshold`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_gripper_actual_open_threshold` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_gripper_actual_open_threshold": (
# 【L1065】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_actual_open_threshold`。
# 【项目含义】把表达式/参数 `args.policy_gripper_actual_open_threshold` 接入当前完整语句；`policy_gripper_actual_open_threshold` 表示策略、夹爪、物理仿真实际值相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.policy_gripper_actual_open_threshold
# 【L1066】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1067】语法拆解：这是字典键值对：`"target_zone_arm_hold_enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `target_zone_arm_hold_enabled`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_zone_arm_hold_enabled` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_zone_arm_hold_enabled": True,
# 【L1068】语法拆解：这是字典键值对：`"target_zone_arm_hold_error_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `target_zone_arm_hold_error_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_zone_arm_hold_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_zone_arm_hold_error_m_lt": 0.05,
# 【L1069】语法拆解：这是字典键值对：`"target_zone_execute_full_action_chunk"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `target_zone_execute_full_action_chunk`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_zone_execute_full_action_chunk` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_zone_execute_full_action_chunk": True,
# 【L1070】语法拆解：这是字典键值对：`"policy_noise_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_noise_seed`。
# 【项目含义】定义字典/JSON 字段 `policy_noise_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_noise_seed` 数据；字段值来自 `args.policy_noise_seed`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_noise_seed": args.policy_noise_seed,
# 【L1071】语法拆解：这是字典键值对：`"policy_chunk_seed_rule"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"case_seed + chunk_index"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `policy_chunk_seed_rule`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_chunk_seed_rule` 数据；字段值来自 `"case_seed + chunk_index"`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_chunk_seed_rule": "case_seed + chunk_index",
# 【L1072】语法拆解：这是字典键值对：`"simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`CONFIGURED_SIMULATION_SEED` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `simulation_seed` 数据；字段值来自 `CONFIGURED_SIMULATION_SEED`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_seed": CONFIGURED_SIMULATION_SEED,
# 【L1073】语法拆解：这是字典键值对：`"cube_workspace_escape_radius_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`CUBE_WORKSPACE_ESCAPE_RADIUS_M` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `cube_workspace_escape_radius_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `cube_workspace_escape_radius_m` 数据；字段值来自 `CUBE_WORKSPACE_ESCAPE_RADIUS_M`，因此保存/传递的是这个表达式当前计算出的结果。
            "cube_workspace_escape_radius_m": CUBE_WORKSPACE_ESCAPE_RADIUS_M,
# 【L1074】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `reset_renderer_accumulation_before_policy_observation`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `reset_renderer_accumulation_before_policy_observation` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "reset_renderer_accumulation_before_policy_observation": (
# 【L1075】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】把表达式/参数 `args.reset_renderer_accumulation_before_policy_observation` 接入当前完整语句；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.reset_renderer_accumulation_before_policy_observation
# 【L1076】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1077】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1078】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `simulation_determinism`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `simulation_determinism` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_determinism": {
# 【L1079】语法拆解：这是字典键值对：`"seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`CONFIGURED_SIMULATION_SEED` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `seed` 数据；字段值来自 `CONFIGURED_SIMULATION_SEED`，因此保存/传递的是这个表达式当前计算出的结果。
            "seed": CONFIGURED_SIMULATION_SEED,
# 【L1080】语法拆解：这是字典键值对：`"python_hash_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`os.environ` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PYTHONHASHSEED"`。
# 【项目含义】定义字典/JSON 字段 `python_hash_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `python_hash_seed` 数据；字段值来自 `os.environ.get("PYTHONHASHSEED")`，因此保存/传递的是这个表达式当前计算出的结果。
            "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
# 【L1081】语法拆解：这是字典键值对：`"torch_deterministic_algorithms"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】定义字典/JSON 字段 `torch_deterministic_algorithms`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `torch_deterministic_algorithms` 数据；字段值来自 `args.pi05_closed_loop`，因此保存/传递的是这个表达式当前计算出的结果。
            "torch_deterministic_algorithms": args.pi05_closed_loop,
# 【L1082】语法拆解：这是字典键值对：`"replicator_global_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`replicator` 是模块/对象，点号 `.` 从中取出 `get_global_seed` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `replicator_global_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `replicator_global_seed` 数据；字段值来自 `replicator.get_global_seed()`，因此保存/传递的是这个表达式当前计算出的结果。
            "replicator_global_seed": replicator.get_global_seed(),
# 【L1083】语法拆解：这是字典键值对：`"physx_enhanced_determinism"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】定义字典/JSON 字段 `physx_enhanced_determinism`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `physx_enhanced_determinism` 数据；字段值来自 `args.pi05_closed_loop`，因此保存/传递的是这个表达式当前计算出的结果。
            "physx_enhanced_determinism": args.pi05_closed_loop,
# 【L1084】语法拆解：这是字典键值对：`"camera_antialiasing_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"FXAA" if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `camera_antialiasing_mode`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `camera_antialiasing_mode` 数据；字段值来自 `"FXAA" if args.pi05_closed_loop else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "camera_antialiasing_mode": "FXAA" if args.pi05_closed_loop else None,
# 【L1085】语法拆解：这是字典键值对：`"dlss_frame_generation_enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `dlss_frame_generation_enabled`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `dlss_frame_generation_enabled` 数据；字段值来自 `False if args.pi05_closed_loop else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "dlss_frame_generation_enabled": False if args.pi05_closed_loop else None,
# 【L1086】语法拆解：这是字典键值对：`"dl_denoiser_enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `dl_denoiser_enabled`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `dl_denoiser_enabled` 数据；字段值来自 `False if args.pi05_closed_loop else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "dl_denoiser_enabled": False if args.pi05_closed_loop else None,
# 【L1087】语法拆解：这是字典键值对：`"motion_blur_enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `motion_blur_enabled`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `motion_blur_enabled` 数据；字段值来自 `False if args.pi05_closed_loop else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "motion_blur_enabled": False if args.pi05_closed_loop else None,
# 【L1088】语法拆解：这是字典键值对：`"tv_noise_enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `tv_noise_enabled`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `tv_noise_enabled` 数据；字段值来自 `False if args.pi05_closed_loop else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "tv_noise_enabled": False if args.pi05_closed_loop else None,
# 【L1089】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `renderer_accumulation_reset_before_policy_observation`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `renderer_accumulation_reset_before_policy_observation` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "renderer_accumulation_reset_before_policy_observation": (
# 【L1090】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】把表达式/参数 `args.reset_renderer_accumulation_before_policy_observation` 接入当前完整语句；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.reset_renderer_accumulation_before_policy_observation
# 【L1091】语法拆解：`if` 要求条件 `args.pi05_closed_loop` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.pi05_closed_loop` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
                if args.pi05_closed_loop
# 【L1092】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else None
# 【L1093】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1094】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1095】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `deterministic_sampling`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `deterministic_sampling` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "deterministic_sampling": {
# 【L1096】语法拆解：这是字典键值对：`"mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`POLICY_SAMPLING_MODE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `mode`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `mode` 数据；字段值来自 `POLICY_SAMPLING_MODE`，因此保存/传递的是这个表达式当前计算出的结果。
            "mode": POLICY_SAMPLING_MODE,
# 【L1097】语法拆解：这是字典键值对：`"case_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_noise_seed`。
# 【项目含义】定义字典/JSON 字段 `case_seed`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `case_seed` 数据；字段值来自 `args.policy_noise_seed`，因此保存/传递的是这个表达式当前计算出的结果。
            "case_seed": args.policy_noise_seed,
# 【L1098】语法拆解：这是字典键值对：`"chunk_seed_rule"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"case_seed + chunk_index"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `chunk_seed_rule`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `chunk_seed_rule` 数据；字段值来自 `"case_seed + chunk_index"`，因此保存/传递的是这个表达式当前计算出的结果。
            "chunk_seed_rule": "case_seed + chunk_index",
# 【L1099】语法拆解：这是字典键值对：`"noise_shape"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `noise_shape`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `noise_shape` 数据；字段值来自 `[POLICY_NOISE_ACTION_HORIZON, POLICY_NOISE_ACTION_DIM]`，因此保存/传递的是这个表达式当前计算出的结果。
            "noise_shape": [POLICY_NOISE_ACTION_HORIZON, POLICY_NOISE_ACTION_DIM],
# 【L1100】语法拆解：这是字典键值对：`"noise_dtype"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"float32"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `noise_dtype`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `noise_dtype` 数据；字段值来自 `"float32"`，因此保存/传递的是这个表达式当前计算出的结果。
            "noise_dtype": "float32",
# 【L1101】语法拆解：这是字典键值对：`"server_metadata"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`server_metadata` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `server_metadata`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `server_metadata` 数据；字段值来自 `server_metadata`，因此保存/传递的是这个表达式当前计算出的结果。
            "server_metadata": server_metadata,
# 【L1102】语法拆解：这是字典键值对：`"chunks"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`policy_sampling_records` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `chunks` 数据；字段值来自 `policy_sampling_records`，因此保存/传递的是这个表达式当前计算出的结果。
            "chunks": policy_sampling_records,
# 【L1103】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1104】语法拆解：这是字典键值对：`"initial_policy_observation"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`initial_policy_observation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `initial_policy_observation`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `initial_policy_observation` 数据；字段值来自 `initial_policy_observation`，因此保存/传递的是这个表达式当前计算出的结果。
        "initial_policy_observation": initial_policy_observation,
# 【L1105】语法拆解：这是字典键值对：`"initial_policy_physical_state"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`initial_policy_physical_state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `initial_policy_physical_state`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `initial_policy_physical_state` 数据；字段值来自 `initial_policy_physical_state`，因此保存/传递的是这个表达式当前计算出的结果。
        "initial_policy_physical_state": initial_policy_physical_state,
# 【L1106】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `inference_latency_s`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `inference_latency_s` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "inference_latency_s": {
# 【L1107】语法拆解：这是字典键值对：`"first"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`inference_latencies[0] if inference_latencies else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `first`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `first` 数据；字段值来自 `inference_latencies[0] if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "first": inference_latencies[0] if inference_latencies else None,
# 【L1108】语法拆解：这是字典键值对：`"mean"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float(np.mean(inference_latencies)) if inference_latencies else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `mean`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `mean` 数据；字段值来自 `float(np.mean(inference_latencies)) if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "mean": float(np.mean(inference_latencies)) if inference_latencies else None,
# 【L1109】语法拆解：这是字典键值对：`"maximum"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float(np.max(inference_latencies)) if inference_latencies else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `maximum`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `maximum` 数据；字段值来自 `float(np.max(inference_latencies)) if inference_latencies else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "maximum": float(np.max(inference_latencies)) if inference_latencies else None,
# 【L1110】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1111】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `guard_totals`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `guard_totals` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "guard_totals": {
# 【L1112】语法拆解：这是字典键值对：`"joint_limit_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`total_joint_limit_clamps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `joint_limit_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `joint_limit_clamp_count` 数据；字段值来自 `total_joint_limit_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_limit_clamp_count": total_joint_limit_clamps,
# 【L1113】语法拆解：这是字典键值对：`"joint_step_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`total_joint_step_clamps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `joint_step_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `joint_step_clamp_count` 数据；字段值来自 `total_joint_step_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "joint_step_clamp_count": total_joint_step_clamps,
# 【L1114】语法拆解：这是字典键值对：`"gripper_clamp_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`total_gripper_clamps` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gripper_clamp_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_clamp_count` 数据；字段值来自 `total_gripper_clamps`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_clamp_count": total_gripper_clamps,
# 【L1115】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1116】语法拆解：这是字典键值对：`"simulation_safety_abort_reason"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`simulation_safety_abort_reason` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_safety_abort_reason`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `simulation_safety_abort_reason` 数据；字段值来自 `simulation_safety_abort_reason`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_safety_abort_reason": simulation_safety_abort_reason,
# 【L1117】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `low_level_release_postcondition`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `low_level_release_postcondition` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "low_level_release_postcondition": {
# 【L1118】语法拆解：这是字典键值对：`"applied"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`release_postcondition_applied` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `applied`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `applied` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "applied": release_postcondition_applied,
# 【L1119】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `trigger`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `trigger` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "trigger": (
# 【L1120】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"configured consecutive chunks with lift, target error below 0.05 m, "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "configured consecutive chunks with lift, target error below 0.05 m, "
# 【L1121】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"actual gripper below the feedback threshold, and executed gripper "`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "actual gripper below the feedback threshold, and executed gripper "
# 【L1122】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"target below the policy threshold"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的帮助说明、错误原因、任务名称或报告文字。
                "target below the policy threshold"
# 【L1123】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1124】语法拆解：这是字典键值对：`"policy_target_open_threshold_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_open_threshold`。
# 【项目含义】定义字典/JSON 字段 `policy_target_open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_target_open_threshold_normalized` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_target_open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L1125】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `actual_open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `actual_open_threshold_normalized` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "actual_open_threshold_normalized": (
# 【L1126】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_actual_open_threshold`。
# 【项目含义】把表达式/参数 `args.policy_gripper_actual_open_threshold` 接入当前完整语句；`policy_gripper_actual_open_threshold` 表示策略、夹爪、物理仿真实际值相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.policy_gripper_actual_open_threshold
# 【L1127】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1128】语法拆解：这是字典键值对：`"arm_target_latched_to_actual_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`release_postcondition_arm_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `arm_target_latched_to_actual_rad`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `arm_target_latched_to_actual_rad` 数据；字段值来自 `release_postcondition_arm_target`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_target_latched_to_actual_rad": release_postcondition_arm_target,
# 【L1129】语法拆解：这是字典键值对：`"gripper_target_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.0 if release_postcondition_applied else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gripper_target_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `gripper_target_normalized` 数据；字段值来自 `0.0 if release_postcondition_applied else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_target_normalized": 0.0 if release_postcondition_applied else None,
# 【L1130】语法拆解：这是字典键值对：`"verification_settle_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`240` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `verification_settle_steps`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `verification_settle_steps` 数据；字段值来自 `240`，因此保存/传递的是这个表达式当前计算出的结果。
            "verification_settle_steps": 240,
# 【L1131】语法拆解：这是字典键值对：`"model_selected_release"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`release_postcondition_applied` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `model_selected_release`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_selected_release` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_selected_release": release_postcondition_applied,
# 【L1132】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1133】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `release_verification`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `release_verification` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_verification": {
# 【L1134】语法拆解：这是字典键值对：`"verified"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`release_postcondition_applied` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `verified`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `verified` 数据；字段值来自 `release_postcondition_applied`，因此保存/传递的是这个表达式当前计算出的结果。
            "verified": release_postcondition_applied,
# 【L1135】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `required_consecutive_chunks`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `required_consecutive_chunks` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "required_consecutive_chunks": (
# 【L1136】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_release_required_consecutive_chunks`。
# 【项目含义】把表达式/参数 `args.policy_release_required_consecutive_chunks` 接入当前完整语句；`policy_release_required_consecutive_chunks` 表示策略相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.policy_release_required_consecutive_chunks
# 【L1137】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1138】语法拆解：这是字典键值对：`"policy_target_open_threshold_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_open_threshold`。
# 【项目含义】定义字典/JSON 字段 `policy_target_open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `policy_target_open_threshold_normalized` 数据；字段值来自 `args.policy_gripper_open_threshold`，因此保存/传递的是这个表达式当前计算出的结果。
            "policy_target_open_threshold_normalized": args.policy_gripper_open_threshold,
# 【L1139】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `actual_open_threshold_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `actual_open_threshold_normalized` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "actual_open_threshold_normalized": (
# 【L1140】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_actual_open_threshold`。
# 【项目含义】把表达式/参数 `args.policy_gripper_actual_open_threshold` 接入当前完整语句；`policy_gripper_actual_open_threshold` 表示策略、夹爪、物理仿真实际值相关值。在“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.policy_gripper_actual_open_threshold
# 【L1141】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1142】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `minimum_observed_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `minimum_observed_gripper_normalized` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_observed_gripper_normalized": (
# 【L1143】语法拆解：`minimum_observed_gripper_normalized` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `minimum_observed_gripper_normalized`；在本项目中它表示夹爪、归一化相关值。
                minimum_observed_gripper_normalized
# 【L1144】语法拆解：`if` 要求条件 `np.isfinite(minimum_observed_gripper_normalized)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `np.isfinite(minimum_observed_gripper_normalized)` 是否成立；`isfinite` 表示本功能块中的 `isfinite` 值；`minimum_observed_gripper_normalized` 表示夹爪、归一化相关值
                if np.isfinite(minimum_observed_gripper_normalized)
# 【L1145】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else None
# 【L1146】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1147】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `minimum_executed_gripper_target`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `minimum_executed_gripper_target` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_executed_gripper_target": (
# 【L1148】语法拆解：`minimum_executed_gripper_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `minimum_executed_gripper_target`；在本项目中它表示夹爪、目标相关值。
                minimum_executed_gripper_target
# 【L1149】语法拆解：`if` 要求条件 `np.isfinite(minimum_executed_gripper_target)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `np.isfinite(minimum_executed_gripper_target)` 是否成立；`isfinite` 表示本功能块中的 `isfinite` 值；`minimum_executed_gripper_target` 表示夹爪、目标相关值
                if np.isfinite(minimum_executed_gripper_target)
# 【L1150】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”在可选数据缺失时仍有明确结果。
                else None
# 【L1151】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
            ),
# 【L1152】语法拆解：这是字典键值对：`"final_gripper_normalized_is_diagnostic_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `final_gripper_normalized_is_diagnostic_only`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_gripper_normalized_is_diagnostic_only` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_gripper_normalized_is_diagnostic_only": True,
# 【L1153】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1154】语法拆解：这是字典键值对：`"source_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `source_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_position_m` 数据；字段值来自 `source_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_position_m": source_np.tolist(),
# 【L1155】语法拆解：这是字典键值对：`"target_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `target_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_position_m": target_block_position.tolist(),
# 【L1156】语法拆解：这是字典键值对：`"final_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `final_position_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_position_m` 数据；字段值来自 `final_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_position_m": final_np.tolist(),
# 【L1157】语法拆解：这是字典键值对：`"source_to_target_xy_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_to_target_distance` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_to_target_xy_distance_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_to_target_xy_distance_m` 数据；字段值来自 `source_to_target_distance`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L1158】语法拆解：这是字典键值对：`"block_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_height` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `block_lift_height_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `block_lift_height_m` 数据；字段值来自 `lift_height`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_lift_height_m": lift_height,
# 【L1159】语法拆解：这是字典键值对：`"final_target_xy_error_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_target_xy_error` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_target_xy_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_xy_error_m` 数据；字段值来自 `final_target_xy_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_xy_error_m": final_target_xy_error,
# 【L1160】语法拆解：这是字典键值对：`"final_target_position_error_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_target_position_error` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_target_position_error_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_position_error_m` 数据；字段值来自 `final_target_position_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_position_error_m": final_target_position_error,
# 【L1161】语法拆解：这是字典键值对：`"post_release_drift_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`post_release_drift` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `post_release_drift_m`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `post_release_drift_m` 数据；字段值来自 `post_release_drift`，因此保存/传递的是这个表达式当前计算出的结果。
        "post_release_drift_m": post_release_drift,
# 【L1162】语法拆解：这是字典键值对：`"final_gripper_normalized"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_gripper` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_gripper_normalized`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_gripper_normalized` 数据；字段值来自 `final_gripper`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_gripper_normalized": final_gripper,
# 【L1163】语法拆解：这是字典键值对：`"all_states_finite"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`all_states_finite` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `all_states_finite`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `all_states_finite` 数据；字段值来自 `all_states_finite`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_states_finite": all_states_finite,
# 【L1164】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `criteria`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `criteria` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "criteria": {
# 【L1165】语法拆解：这是字典键值对：`"source_to_target_xy_distance_m_gt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `source_to_target_xy_distance_m_gt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L1166】语法拆解：这是字典键值对：`"block_lift_height_m_gt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.02` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `block_lift_height_m_gt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `block_lift_height_m_gt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m_gt": 0.02,
# 【L1167】语法拆解：这是字典键值对：`"final_target_xy_error_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_target_xy_error_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_xy_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_xy_error_m_lt": 0.05,
# 【L1168】语法拆解：这是字典键值对：`"final_target_position_error_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_target_position_error_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `final_target_position_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_position_error_m_lt": 0.05,
# 【L1169】语法拆解：这是字典键值对：`"post_release_drift_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.02` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `post_release_drift_m_lt`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `post_release_drift_m_lt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "post_release_drift_m_lt": 0.02,
# 【L1170】语法拆解：这是字典键值对：`"model_selected_release_verified"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `model_selected_release_verified`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `model_selected_release_verified` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "model_selected_release_verified": True,
# 【L1171】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1172】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `episode`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `episode` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "episode": {
# 【L1173】语法拆解：这是字典键值对：`"directory"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_recorder.output_dir`。
# 【项目含义】定义字典/JSON 字段 `directory`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
            "directory": str(episode_recorder.output_dir),
# 【L1174】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`manifest["frame_count"]` 使用方括号索引；先计算 `"frame_count"`，再从 `manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `frame_count` 数据；字段值来自 `manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": manifest["frame_count"],
# 【L1175】语法拆解：这是字典键值对：`"validation"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`validation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `validation`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `validation` 数据；字段值来自 `validation`，因此保存/传递的是这个表达式当前计算出的结果。
            "validation": validation,
# 【L1176】语法拆解：这是字典键值对：`"evaluation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `evaluation_only`，它表示“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的 `evaluation_only` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "evaluation_only": True,
# 【L1177】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
        },
# 【L1178】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
    }
# 【L1179】语法拆解：`output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L1180】语法拆解：`output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L1181】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L1182】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}", flush=True` 的当前值/文字输出到终端；它用于观察“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”进度，也给日志留下可搜索证据。
    print(f"RM65_PI05_CLOSED_LOOP={'PASS' if passed else 'FAIL'}", flush=True)
# 【L1183】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0 if passed else 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L1184】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

# 【L1185】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 11：接触力统计与平台生成工具（源码第 1186-1226 行）

### 5.A 数据流位置

- 上游：模块 10“π0.5 的观测→WebSocket→动作块→安全裁剪→执行→重规划闭环”。
- 本模块：接触力统计与平台生成工具。
- 下游：处理结果继续交给模块 12“主函数输入文件和参数范围校验”。

### 5.B 为什么需要这一组代码

这一组负责“接触力统计与平台生成工具”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `current`：float32 格式的当前六关节角。

### 5.D 本模块首次阅读要认识的调用

- `contact_force_statistics(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `torch.linalg.vector_norm(...)`：圆括号表示真正执行调用；PyTorch 的 `vector_norm` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `max(...)`：圆括号表示真正执行调用；从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。
- `history_norm.max(...)`：圆括号表示真正执行调用；从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。
- `min(...)`：圆括号表示真正执行调用；从候选值中选择最小者；常用于限制执行步数或选择代价最小的 IK 分支。
- `reshape(...)`：圆括号表示真正执行调用；改变数组形状而不改变元素顺序；新旧元素总数必须一致。
- `recent.max(...)`：圆括号表示真正执行调用；从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。
- `values.mean(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `spawn_platform(...)`：圆括号表示真正执行调用；在 Isaac 世界中创建源/目标支撑平台的刚体和碰撞几何。
- `sim_utils.CuboidCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.CollisionPropertiesCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.PreviewSurfaceCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.E 本模块定义的新函数

### 函数卡：`contact_force_statistics()`（第 1186-1200 行）

- 定义了什么：接触力统计与平台生成工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`contact_sensor`：类型 `ContactSensor`；项目含义是接触相关值；`recent_steps`：类型 `int`，默认 `60`；项目含义是步数相关值
- 返回类型标注：`dict[str, float]`。
- 函数体实际 return：`{'peak_n': peak_n, 'current_n': current_n, 'recent_mean_n': recent_mean_n}`；`{'peak_n': 0.0, 'current_n': 0.0, 'recent_mean_n': 0.0}`
- 项目中的实际调用位置：`run_pick_place_baseline.py:1998` 的 `close_contact_force_statistics_by_body[body_name] = contact_force_statistics(contact_sensor)`

### 函数卡：`spawn_platform()`（第 1203-1224 行）

- 定义了什么：接触力统计与平台生成工具。`def` 只创建函数；实际调用时函数体才执行。
- 输入：`path`：类型 `str`；项目含义是路径相关值；`position`：类型 `np.ndarray`；项目含义是位置相关值；`size`：类型 `tuple[float, float, float]`；项目含义是本功能块中的 `size` 值；`color`：类型 `tuple[float, float, float]`；项目含义是本功能块中的 `color` 值；`orientation`：类型 `tuple[float, float, float, float] | None`，默认 `None`；项目含义是本功能块中的 `orientation` 值
- 返回类型标注：`None`。
- 函数体实际 return：没有显式值，默认返回 None。
- 项目中的实际调用位置：`run_pick_place_baseline.py:1628` 的 `spawn_platform(`；`run_pick_place_baseline.py:1644` 的 `spawn_platform(`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L1186】语法拆解：`def` 定义函数 `contact_force_statistics`；第一对圆括号列出形参，逗号负责分隔：`contact_sensor: ContactSensor` 用冒号给参数加类型提示；`recent_steps: int = 60` 用冒号给参数加类型提示；`-> dict[str, float]` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60)`；调用者把参数交给它完成“接触力统计与平台生成工具”，后面的缩进代码是具体实现。
def contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60) -> dict[str, float]:
# 【L1187】语法拆解：三引号开始或结束说明字符串；它可以跨多行，通常用于解释模块、类或函数。
# 【项目含义】说明字符串 `Return peak, current, and recent sustained cube-contact force magnitudes.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Return peak, current, and recent sustained cube-contact force magnitudes."""
# 【L1188】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L1189】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current`。右侧语法为：`contact_sensor` 是起始对象；每个点号 `.` 依次读取属性/成员：`data` → `force_matrix_w`。
# 【项目含义】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w` 表示力相关值。
    current = contact_sensor.data.force_matrix_w
# 【L1190】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `history`。右侧语法为：`contact_sensor` 是起始对象；每个点号 `.` 依次读取属性/成员：`data` → `force_matrix_w_history`。
# 【项目含义】得到 `history`，它在本项目中表示本功能块中的 `history` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w_history`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w_history` 表示力相关值。
    history = contact_sensor.data.force_matrix_w_history
# 【L1191】语法拆解：`if` 要求条件 `current is None or history is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `current is None or history is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if current is None or history is None:
# 【L1192】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】结束当前函数并把 `{"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}` 交回调用者；这个值的含义是：计算表达式 `{"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}`；`peak_n` 表示本功能块中的 `peak_n` 值；`current_n` 表示当前值相关值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。
        return {"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}
# 【L1193】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current_n`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `torch.linalg.vector_norm(current, dim=-1).max()`。
# 【项目含义】得到 `current_n`，它在本项目中表示当前值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    current_n = float(torch.linalg.vector_norm(current, dim=-1).max())
# 【L1194】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `history_norm`。右侧语法为：`torch.linalg` 是模块/对象，点号 `.` 从中取出 `vector_norm` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `history`；第 2 个实参 `dim=-1`。
# 【项目含义】得到 `history_norm`，它在本项目中表示本功能块中的 `history_norm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    history_norm = torch.linalg.vector_norm(history, dim=-1)
# 【L1195】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `peak_n`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `history_norm.max()`。
# 【项目含义】得到 `peak_n`，它在本项目中表示本功能块中的 `peak_n` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(history_norm.max())`；`history_norm` 表示本功能块中的 `history_norm` 值。
    peak_n = float(history_norm.max())
# 【L1196】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `recent`。右侧语法为：`history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `recent`，它在本项目中表示本功能块中的 `recent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(`；`history_norm` 表示本功能块中的 `history_norm` 值；`recent_steps` 表示步数相关值；`shape` 表示本功能块中的 `shape` 值。
    recent = history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(
# 【L1197】语法拆解：表达式 `min(recent_steps, history_norm.shape[1]), -1` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `min(recent_steps, history_norm.shape[1]), -1` 接入当前完整语句；`recent_steps` 表示步数相关值；`history_norm` 表示本功能块中的 `history_norm` 值；`shape` 表示本功能块中的 `shape` 值。在“接触力统计与平台生成工具”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        min(recent_steps, history_norm.shape[1]), -1
# 【L1198】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L1199】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `recent_mean_n`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `recent.max(dim=1).values.mean()`。
# 【项目含义】得到 `recent_mean_n`，它在本项目中表示本功能块中的 `recent_mean_n` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(recent.max(dim=1).values.mean())`；`recent` 表示本功能块中的 `recent` 值；`dim` 表示本功能块中的 `dim` 值；`values` 表示本功能块中的 `values` 值。
    recent_mean_n = float(recent.max(dim=1).values.mean())
# 【L1200】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】结束当前函数并把 `{"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}` 交回调用者；这个值的含义是：计算表达式 `{"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}`；`peak_n` 表示本功能块中的 `peak_n` 值；`current_n` 表示当前值相关值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。
    return {"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}
# 【L1201】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L1202】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L1203】语法拆解：`def` 开始定义函数；左圆括号打开多行参数列表，参数和返回类型会在后续物理行继续。
# 【项目含义】定义函数 `spawn_platform(参数在后续行继续)`；调用者把参数交给它完成“接触力统计与平台生成工具”，后面的缩进代码是具体实现。
def spawn_platform(
# 【L1204】语法拆解：`path` 是参数/字段名；冒号 `:` 添加类型提示 `str`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `path`，类型提示为 `str`；在本项目中它表示路径相关值。
    path: str,
# 【L1205】语法拆解：`position` 是参数/字段名；冒号 `:` 添加类型提示 `np.ndarray`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】声明/传入参数 `position`，类型提示为 `np.ndarray`；在本项目中它表示位置相关值。
    position: np.ndarray,
# 【L1206】语法拆解：`size` 是参数/字段名；冒号 `:` 添加类型提示 `tuple[float, float, float]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `size: tuple[float, float, float]`；`size` 表示本功能块中的 `size` 值，它参与“接触力统计与平台生成工具”。
    size: tuple[float, float, float],
# 【L1207】语法拆解：`color` 是参数/字段名；冒号 `:` 添加类型提示 `tuple[float, float, float]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】向上一行的函数调用或容器继续传入 `color: tuple[float, float, float]`；`color` 表示本功能块中的 `color` 值，它参与“接触力统计与平台生成工具”。
    color: tuple[float, float, float],
# 【L1208】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `orientation: tuple[float, float, float, float] | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `orientation`，它在本项目中表示本功能块中的 `orientation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    orientation: tuple[float, float, float, float] | None = None,
# 【L1209】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `) -> None:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“接触力统计与平台生成工具”。
) -> None:
# 【L1210】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cfg`。右侧语法为：`sim_utils.CuboidCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cfg`，它在本项目中表示本功能块中的 `cfg` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.CuboidCfg(`；`sim_utils` 表示仿真相关值；`CuboidCfg` 表示本功能块中的 `CuboidCfg` 值。
    cfg = sim_utils.CuboidCfg(
# 【L1211】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `size`。右侧语法为：`size` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `size` 传入 `size`；该参数在本项目中表示本功能块中的 `size` 值，会参与“接触力统计与平台生成工具”。
        size=size,
# 【L1212】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collision_props`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `CollisionPropertiesCfg` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】给上一层函数/配置构造器的命名参数 `collision_props` 传入 `sim_utils.CollisionPropertiesCfg()`；该参数在本项目中表示本功能块中的 `collision_props` 值，会参与“接触力统计与平台生成工具”。
        collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L1213】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `visual_material`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `PreviewSurfaceCfg` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `diffuse_color=color`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `visual_material` 传入 `sim_utils.PreviewSurfaceCfg(diffuse_color=color)`；该参数在本项目中表示本功能块中的 `visual_material` 值，会参与“接触力统计与平台生成工具”。
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
# 【L1214】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physics_material`。右侧语法为：`sim_utils.RigidBodyMaterialCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
        physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1215】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `static_friction`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.0`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“接触力统计与平台生成工具”。
            static_friction=1.0,
# 【L1216】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dynamic_friction`。右侧语法为：`0.8` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `0.8`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“接触力统计与平台生成工具”。
            dynamic_friction=0.8,
# 【L1217】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `restitution`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“接触力统计与平台生成工具”。
            restitution=0.0,
# 【L1218】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `friction_combine_mode`。右侧语法为：`"max"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“接触力统计与平台生成工具”。
            friction_combine_mode="max",
# 【L1219】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
        ),
# 【L1220】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“接触力统计与平台生成工具”。
    )
# 【L1221】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `kwargs`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `kwargs`，它在本项目中表示本功能块中的 `kwargs` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{"translation": tuple(position)}`；`translation` 表示本功能块中的 `translation` 值；`position` 表示位置相关值。
    kwargs = {"translation": tuple(position)}
# 【L1222】语法拆解：`if` 要求条件 `orientation is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `orientation is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if orientation is not None:
# 【L1223】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `kwargs["orientation"]`。右侧语法为：`orientation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `kwargs["orientation"]`（写入 `kwargs["orientation"]` 指定的字段）；右侧具体做的是：计算表达式 `orientation`；`orientation` 表示本功能块中的 `orientation` 值。
        kwargs["orientation"] = orientation
# 【L1224】语法拆解：`cfg` 是模块/对象，点号 `.` 从中取出 `func` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `path`；第 2 个实参 `cfg`；第 3 个实参 `**kwargs`。
# 【项目含义】对 `cfg` 调用 `func(path, cfg, **kwargs)`：调用 `cfg` 提供的 `func` 操作。本行产生的修改/返回值服务于“接触力统计与平台生成工具”。
    cfg.func(path, cfg, **kwargs)
# 【L1225】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

# 【L1226】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“接触力统计与平台生成工具”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“接触力统计与平台生成工具”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 12：主函数输入文件和参数范围校验（源码第 1227-1289 行）

### 5.A 数据流位置

- 上游：模块 11“接触力统计与平台生成工具”。
- 本模块：主函数输入文件和参数范围校验。
- 下游：处理结果继续交给模块 13“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。

### 5.B 为什么需要这一组代码

这一组负责“主函数输入文件和参数范围校验”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `gripper`：一个归一化夹爪值组成的一维数组。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `output`：输出文件路径。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `usd`：Isaac Sim 实际加载的 RM65+4C2 USD 资产路径。
- `urdf`：Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
- `pregrasp_distance_m`：预抓取位姿到实际抓取位姿之间的直线距离，单位米。
- `record_stride_steps`：每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `args.usd.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `resolve(...)`：圆括号表示真正执行调用；把相对路径和 `..` 解析成规范绝对路径。
- `args.urdf.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `args.description.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `args.output.expanduser(...)`：圆括号表示真正执行调用；把路径开头的 `~` 展开成当前用户主目录。
- `path.is_file(...)`：圆括号表示真正执行调用；检查路径是否存在且确实是普通文件。
- `FileNotFoundError(...)`：圆括号表示真正执行调用；创建“需要的文件不存在”的异常。
- `abs(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `ValueError(...)`：圆括号表示真正执行调用；创建“输入值不符合合同”的异常；配合 raise 立即停止当前错误路径。
- `min(...)`：圆括号表示真正执行调用；从候选值中选择最小者；常用于限制执行步数或选择代价最小的 IK 分支。
- `np.deg2rad(...)`：圆括号表示真正执行调用；NumPy 的 `deg2rad` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。

### 5.E 本模块定义的新函数

### 函数卡：`main()`（第 1227-2565 行）

- 定义了什么：主函数输入文件和参数范围校验。`def` 只创建函数；实际调用时函数体才执行。
- 输入：无显式参数。
- 返回类型标注：`int`。
- 函数体实际 return：`0 if passed else 1`；`0`；`run_pi05_closed_loop(sim=sim, robot=robot, cube=cube, state=state, arm_ids=arm_ids, gripper_ids=gripper_ids, gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT), target_block_position=target_block_position, settled_source_position=settled_source_position, target_platform_collision_apis=target_platform_collision_apis, episode_capture=episode_capture, episode_recorder=episode_recorder, output=output)`；`0`；`1`
- 项目中的实际调用位置：`build_combined_urdf.py:305` 的 `main()`；`import_combined_urdf.py:88` 的 `main()`；`run_pick_place_baseline.py:2569` 的 `exit_code = main()`；`convert_expert_episodes_to_lerobot.py:313` 的 `raise SystemExit(main())`；`train_rm65_pi05.py:106` 的 `trainer.main(config)`


### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L1227】语法拆解：`def` 定义函数 `main`；第一对圆括号列出形参，逗号负责分隔：没有形参；`-> int` 表示返回类型提示；行末冒号打开函数体。
# 【项目含义】定义函数 `main()`；调用者把参数交给它完成“主函数输入文件和参数范围校验”，后面的缩进代码是具体实现。
def main() -> int:
# 【L1228】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `usd`。右侧语法为：`args.usd` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `usd`，它在本项目中表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.usd.expanduser().resolve()`；`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    usd = args.usd.expanduser().resolve()
# 【L1229】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `urdf`。右侧语法为：`args.urdf` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `urdf`，它在本项目中表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.urdf.expanduser().resolve()`；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    urdf = args.urdf.expanduser().resolve()
# 【L1230】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `description`。右侧语法为：`args.description` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `description`，它在本项目中表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.description.expanduser().resolve()`；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    description = args.description.expanduser().resolve()
# 【L1231】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output`。右侧语法为：`args.output` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】得到 `output`，它在本项目中表示输出文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.output.expanduser().resolve()`；`output` 表示输出文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    output = args.output.expanduser().resolve()
# 【L1232】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `missing`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `missing`，它在本项目中表示本功能块中的 `missing` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[str(path) for path in (usd, urdf, description) if not path.is_file()]`；`path` 表示路径相关值；`usd` 表示Isaac Sim 实际加载的 RM65+4C2 USD 资产路径；`urdf` 表示Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径。
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
# 【L1233】语法拆解：`if` 要求条件 `missing` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `missing` 是否成立；`missing` 表示本功能块中的 `missing` 值
    if missing:
# 【L1234】语法拆解：`raise` 主动制造并抛出异常；后面的 `FileNotFoundError(f"missing required files: {missing}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `FileNotFoundError(f"missing required files: {missing}")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise FileNotFoundError(f"missing required files: {missing}")
# 【L1235】语法拆解：`if` 要求条件 `abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2` 是否成立；`abs` 表示本功能块中的 `abs` 值；`transfer_joint_1_rad` 表示关节相关值
    if abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2:
# 【L1236】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")
# 【L1237】语法拆解：`if` 要求条件 `not 0.0 <= args.robot_base_z_m <= 0.8` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= args.robot_base_z_m <= 0.8` 是否成立；`robot_base_z_m` 表示本功能块中的 `robot_base_z_m` 值
    if not 0.0 <= args.robot_base_z_m <= 0.8:
# 【L1238】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--robot-base-z-m must be between 0 and 0.8")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--robot-base-z-m must be between 0 and 0.8")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--robot-base-z-m must be between 0 and 0.8")
# 【L1239】语法拆解：`if` 要求条件 `min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0` 是否成立；`arm_effort_limit_sim` 表示仿真相关值；`arm_stiffness` 表示本功能块中的 `arm_stiffness` 值；`arm_damping` 表示本功能块中的 `arm_damping` 值
    if min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0:
# 【L1240】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("arm actuator effort, stiffness, and damping must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("arm actuator effort, stiffness, and damping must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("arm actuator effort, stiffness, and damping must be positive")
# 【L1241】语法拆解：`if` 要求条件 `min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0` 是否成立；`gripper_effort_limit_sim` 表示夹爪、仿真相关值；`gripper_stiffness` 表示夹爪相关值；`gripper_damping` 表示夹爪相关值
    if min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0:
# 【L1242】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("gripper actuator effort, stiffness, and damping must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("gripper actuator effort, stiffness, and damping must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("gripper actuator effort, stiffness, and damping must be positive")
# 【L1243】语法拆解：`if` 要求条件 `not 0.1 <= args.gripper_close_target_rad <= 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.1 <= args.gripper_close_target_rad <= 1.0` 是否成立；`gripper_close_target_rad` 表示夹爪、目标相关值
    if not 0.1 <= args.gripper_close_target_rad <= 1.0:
# 【L1244】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")
# 【L1245】语法拆解：`if` 要求条件 `not 0.01 <= args.pregrasp_distance_m <= 0.10` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.01 <= args.pregrasp_distance_m <= 0.10` 是否成立；`pregrasp_distance_m` 表示预抓取位姿到实际抓取位姿之间的直线距离，单位米
    if not 0.01 <= args.pregrasp_distance_m <= 0.10:
# 【L1246】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")
# 【L1247】语法拆解：`if` 要求条件 `abs(args.grasp_world_offset_x_m) > 0.08` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(args.grasp_world_offset_x_m) > 0.08` 是否成立；`abs` 表示本功能块中的 `abs` 值；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值
    if abs(args.grasp_world_offset_x_m) > 0.08:
# 【L1248】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")
# 【L1249】语法拆解：`if` 要求条件 `abs(args.grasp_world_offset_z_m) > 0.08` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(args.grasp_world_offset_z_m) > 0.08` 是否成立；`abs` 表示本功能块中的 `abs` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值
    if abs(args.grasp_world_offset_z_m) > 0.08:
# 【L1250】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")
# 【L1251】语法拆解：`if` 要求条件 `abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04` 是否成立；`abs` 表示本功能块中的 `abs` 值；`source_offset_x_m` 表示源位置相关值；`source_offset_y_m` 表示源位置相关值
    if abs(args.source_offset_x_m) > 0.04 or abs(args.source_offset_y_m) > 0.04:
# 【L1252】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("source x/y offsets must each be between -0.04 and 0.04 m")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("source x/y offsets must each be between -0.04 and 0.04 m")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("source x/y offsets must each be between -0.04 and 0.04 m")
# 【L1253】语法拆解：`if` 要求条件 `abs(args.top_down_yaw_rad) > np.pi` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `abs(args.top_down_yaw_rad) > np.pi` 是否成立；`abs` 表示本功能块中的 `abs` 值；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值；`pi` 表示本功能块中的 `pi` 值
    if abs(args.top_down_yaw_rad) > np.pi:
# 【L1254】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--top-down-yaw-rad must be between -pi and pi")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--top-down-yaw-rad must be between -pi and pi")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-yaw-rad must be between -pi and pi")
# 【L1255】语法拆解：`if` 要求条件 `not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0)` 是否成立；`top_down_tilt_rad` 表示本功能块中的 `top_down_tilt_rad` 值；`deg2rad` 表示本功能块中的 `deg2rad` 值
    if not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0):
# 【L1256】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")
# 【L1257】语法拆解：`if` 要求条件 `not 1 <= args.top_down_ik_multistart <= 512` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 1 <= args.top_down_ik_multistart <= 512` 是否成立；`top_down_ik_multistart` 表示本功能块中的 `top_down_ik_multistart` 值
    if not 1 <= args.top_down_ik_multistart <= 512:
# 【L1258】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--top-down-ik-multistart must be between 1 and 512")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--top-down-ik-multistart must be between 1 and 512")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-ik-multistart must be between 1 and 512")
# 【L1259】语法拆解：`if` 要求条件 `not 0.0 <= args.top_down_blend <= 1.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= args.top_down_blend <= 1.0` 是否成立；`top_down_blend` 表示本功能块中的 `top_down_blend` 值
    if not 0.0 <= args.top_down_blend <= 1.0:
# 【L1260】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--top-down-blend must be between 0 and 1")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--top-down-blend must be between 0 and 1")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--top-down-blend must be between 0 and 1")
# 【L1261】语法拆解：`if` 要求条件 `not 0.02 <= args.cartesian_lift_height_m <= 0.15` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.02 <= args.cartesian_lift_height_m <= 0.15` 是否成立；`cartesian_lift_height_m` 表示本功能块中的 `cartesian_lift_height_m` 值
    if not 0.02 <= args.cartesian_lift_height_m <= 0.15:
# 【L1262】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")
# 【L1263】语法拆解：`if` 要求条件 `not 0.03 <= args.release_clearance_m <= 0.20` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.03 <= args.release_clearance_m <= 0.20` 是否成立；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值
    if not 0.03 <= args.release_clearance_m <= 0.20:
# 【L1264】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--release-clearance-m must be between 0.03 and 0.20")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--release-clearance-m must be between 0.03 and 0.20")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--release-clearance-m must be between 0.03 and 0.20")
# 【L1265】语法拆解：`if` 要求条件 `not 0.0 <= args.release_separation_assist_m <= 0.20` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.0 <= args.release_separation_assist_m <= 0.20` 是否成立；`release_separation_assist_m` 表示本功能块中的 `release_separation_assist_m` 值
    if not 0.0 <= args.release_separation_assist_m <= 0.20:
# 【L1266】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--release-separation-assist-m must be between 0.0 and 0.20")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--release-separation-assist-m must be between 0.0 and 0.20")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--release-separation-assist-m must be between 0.0 and 0.20")
# 【L1267】语法拆解：`if` 要求条件 `not 0.03 <= args.place_descent_distance_m <= 0.13` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 0.03 <= args.place_descent_distance_m <= 0.13` 是否成立；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值
    if not 0.03 <= args.place_descent_distance_m <= 0.13:
# 【L1268】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--place-descent-distance-m must be between 0.03 and 0.13")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--place-descent-distance-m must be between 0.03 and 0.13")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--place-descent-distance-m must be between 0.03 and 0.13")
# 【L1269】语法拆解：`if` 要求条件 `not 30 <= args.place_waypoint_steps <= 240` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 30 <= args.place_waypoint_steps <= 240` 是否成立；`place_waypoint_steps` 表示步数相关值
    if not 30 <= args.place_waypoint_steps <= 240:
# 【L1270】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--place-waypoint-steps must be between 30 and 240")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--place-waypoint-steps must be between 30 and 240")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--place-waypoint-steps must be between 30 and 240")
# 【L1271】语法拆解：`if` 要求条件 `not 1 <= args.record_stride_steps <= 240` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not 1 <= args.record_stride_steps <= 240` 是否成立；`record_stride_steps` 表示每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长
    if not 1 <= args.record_stride_steps <= 240:
# 【L1272】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--record-stride-steps must be between 1 and 240")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--record-stride-steps must be between 1 and 240")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-stride-steps must be between 1 and 240")
# 【L1273】语法拆解：`if` 要求条件 `not args.episode_prompt.strip()` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.episode_prompt.strip()` 是否成立；`episode_prompt` 表示当前 episode 发送给 π0.5 的自然语言任务指令；`strip` 表示本功能块中的 `strip` 值
    if not args.episode_prompt.strip():
# 【L1274】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--episode-prompt must not be empty")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--episode-prompt must not be empty")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--episode-prompt must not be empty")
# 【L1275】语法拆解：`if` 要求条件 `args.record_episode_dir is not None and (` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.record_episode_dir is not None and (`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.record_episode_dir is not None and (
# 【L1276】语法拆解：`args.diagnose_approach_only or args.diagnose_kinematics_only` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `args.diagnose_approach_only or args.diagnose_kinematics_only` 接入当前完整语句；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值。在“主函数输入文件和参数范围校验”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        args.diagnose_approach_only or args.diagnose_kinematics_only
# 【L1277】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“主函数输入文件和参数范围校验”。
    ):
# 【L1278】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("episode recording is available only for a complete pick-and-place run")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("episode recording is available only for a complete pick-and-place run")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("episode recording is available only for a complete pick-and-place run")
# 【L1279】语法拆解：`if` 要求条件 `args.record_images and args.record_episode_dir is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.record_images and args.record_episode_dir is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if args.record_images and args.record_episode_dir is None:
# 【L1280】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--record-images requires --record-episode-dir")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--record-images requires --record-episode-dir")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-images requires --record-episode-dir")
# 【L1281】语法拆解：`if` 要求条件 `args.record_images and not getattr(args, "enable_cameras", False)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.record_images and not getattr(args, "enable_cameras", False)` 是否成立；`record_images` 表示本功能块中的 `record_images` 值；`getattr` 表示本功能块中的 `getattr` 值；`enable_cameras` 表示本功能块中的 `enable_cameras` 值
    if args.record_images and not getattr(args, "enable_cameras", False):
# 【L1282】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--record-images requires the AppLauncher flag --enable_cameras")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--record-images requires the AppLauncher flag --enable_cameras")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--record-images requires the AppLauncher flag --enable_cameras")
# 【L1283】语法拆解：`if` 要求条件 `args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None)`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
    if args.pi05_closed_loop and (not args.record_images or args.record_episode_dir is None):
# 【L1284】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop requires --record-images and --record-episode-dir")
# 【L1285】语法拆解：`if` 要求条件 `args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only)` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值
    if args.pi05_closed_loop and (args.diagnose_approach_only or args.diagnose_kinematics_only):
# 【L1286】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("--pi05-closed-loop cannot be combined with diagnostic-only modes")
# 【L1287】语法拆解：`if` 要求条件 `args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1` 是否成立；`policy_max_action_chunks` 表示策略、动作相关值；`policy_execute_actions_per_chunk` 表示策略、动作序列相关值
    if args.policy_max_action_chunks < 1 or args.policy_execute_actions_per_chunk < 1:
# 【L1288】语法拆解：`raise` 主动制造并抛出异常；后面的 `ValueError("policy chunk counts must be positive")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `ValueError("policy chunk counts must be positive")` 并停止当前路径；说明当前输入违反“主函数输入文件和参数范围校验”要求，不能继续进入仿真、训练或评测。
        raise ValueError("policy chunk counts must be positive")
# 【L1289】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“主函数输入文件和参数范围校验”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“主函数输入文件和参数范围校验”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 13：根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK（源码第 1290-1596 行）

### 5.A 数据流位置

- 上游：模块 12“主函数输入文件和参数范围校验”。
- 本模块：根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK。
- 下游：处理结果继续交给模块 14“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。

### 5.B 为什么需要这一组代码

这一组负责“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `lula`：NVIDIA Lula 运动学求解器实例。
- `output`：输出文件路径。
- `policy`：加载了 RM65 checkpoint、transform 和 norm stats 的 OpenPI 推理对象。
- `cases`：经过 split/max-cases 过滤后本次要运行的实验条件列表。
- `urdf`：Lula/Isaac 使用的 RM65 关节、link 和几何描述文件路径。
- `description`：Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
- `pregrasp_distance_m`：预抓取位姿到实际抓取位姿之间的直线距离，单位米。

### 5.D 本模块首次阅读要认识的调用

- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `SOURCE_BLOCK_POSITION.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `np.asarray(...)`：圆括号表示真正执行调用；把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制。
- `source_block_position.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `LulaKinematicsSolver(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `lula.compute_forward_kinematics(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `grasp_arm.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `lula.compute_inverse_kinematics(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `closest_equivalent_rm65_solution(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `compute_top_down_link_pose(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `np.random.default_rng(...)`：圆括号表示真正执行调用；NumPy 的 `default_rng` 数值函数；本行的逐行项目含义会说明它对当前数组产生的具体结果。

### 5.F 这一模块的版本变化

- 当前第 1498-1501 行相对旧教学快照发生 `replace`：旧版 1 行，当前 4 行。 旧代码摘录：`if args.place_descent:` 当前代码摘录：`# The pi0.5 branch returns to run_pi05_closed_loop before the scripted` / `# descent below is ever executed. Do not reject policy evaluation cases` / `# because an unused scripted-only trajectory crosses a different IK branch.` / `if args.place_descent and not args.pi05_closed_loop:`

### 5.G 逐行精读

```python
# 【L1290】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `requested_pregrasp_distance_m`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pregrasp_distance_m`。
# 【项目含义】得到 `requested_pregrasp_distance_m`，它在本项目中表示本功能块中的 `requested_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.pregrasp_distance_m`；`pregrasp_distance_m` 表示预抓取位姿到实际抓取位姿之间的直线距离，单位米。
    requested_pregrasp_distance_m = args.pregrasp_distance_m
# 【L1291】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `effective_pregrasp_distance_m`。右侧语法为：`requested_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `effective_pregrasp_distance_m`，它在本项目中表示本功能块中的 `effective_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `requested_pregrasp_distance_m`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值。
    effective_pregrasp_distance_m = requested_pregrasp_distance_m
# 【L1292】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_arm`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[0.0, -0.55, 1.05, 0.0, 0.65, 0.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
    grasp_arm = np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L1293】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_arm`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[0.0, -0.73, 0.87, 0.0, 0.65, 0.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `lift_arm`，它在本项目中表示本功能块中的 `lift_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
    lift_arm = np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)
# 【L1294】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_position`。右侧语法为：`SOURCE_BLOCK_POSITION` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `source_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    source_block_position = SOURCE_BLOCK_POSITION.copy()
# 【L1295】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_quaternion`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `SOURCE_BLOCK_QUATERNION_WXYZ`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `source_block_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64`（源位置方块/平台的任务常量），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
    source_block_quaternion = np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L1296】语法拆解：`if` 要求条件 `args.natural_source_gravity` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值
    if args.natural_source_gravity:
# 【L1297】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_position[2]`。右侧语法为：表达式 `SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0` 使用运算符 `+`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把右侧结果写进 `source_block_position[2]`（写入 `source_block_position[2]` 指定的字段）；右侧具体做的是：计算表达式 `SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0`；`SOURCE_PLATFORM_TOP_Z` 表示源位置方块/平台的任务常量；`BLOCK_SIZE` 表示本功能块中的 `BLOCK_SIZE` 值。
        source_block_position[2] = SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L1298】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_quaternion`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[1.0, 0.0, 0.0, 0.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `source_block_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值。
        source_block_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
# 【L1299】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `nominal_source_block_position`。右侧语法为：`source_block_position` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `nominal_source_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    nominal_source_block_position = source_block_position.copy()
# 【L1300】语法拆解：表达式 `source_block_position[:2] += np.array(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `source_block_position[:2] += np.array(`。`source_block_position` 表示源位置、位置相关值；`array` 表示本功能块中的 `array` 值。
    source_block_position[:2] += np.array(
# 【L1301】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[args.source_offset_x_m, args.source_offset_y_m], dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[args.source_offset_x_m, args.source_offset_y_m], dtype=np.float64`；`source_offset_x_m` 表示源位置相关值；`source_offset_y_m` 表示源位置相关值；`dtype` 表示本功能块中的 `dtype` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [args.source_offset_x_m, args.source_offset_y_m], dtype=np.float64
# 【L1302】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1303】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `robot_base_position`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[0.0, 0.0, args.robot_base_z_m]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `robot_base_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)`；`array` 表示本功能块中的 `array` 值；`robot_base_z_m` 表示本功能块中的 `robot_base_z_m` 值；`dtype` 表示本功能块中的 `dtype` 值。
    robot_base_position = np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)
# 【L1304】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_position_base`。右侧语法为：表达式 `source_block_position - robot_base_position` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `source_block_position_base`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `source_block_position - robot_base_position`；`source_block_position` 表示源位置、位置相关值；`robot_base_position` 表示位置相关值。
    source_block_position_base = source_block_position - robot_base_position
# 【L1305】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lula`。右侧语法为：`LulaKinematicsSolver` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot_description_path=str(description)`；第 2 个实参 `urdf_path=str(urdf)`。
# 【项目含义】得到 `lula`，它在本项目中表示NVIDIA Lula 运动学求解器实例；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：用 RM65 URDF 和 robot description 创建 Lula 正/逆运动学求解器。
    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
# 【L1306】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_link_position, grasp_link_rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `grasp_arm`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1307】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_ik_numerical_seed`。右侧语法为：`grasp_arm` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    grasp_ik_numerical_seed = grasp_arm.copy()
# 【L1308】语法拆解：`if` 要求条件 `args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0` 是否成立；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值
    if args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0:
# 【L1309】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `offset_target_position`。右侧语法为：表达式 `grasp_link_position + np.array(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `offset_target_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_position + np.array(`；`grasp_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        offset_target_position = grasp_link_position + np.array(
# 【L1310】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64`；`grasp_world_offset_x_m` 表示本功能块中的 `grasp_world_offset_x_m` 值；`grasp_world_offset_z_m` 表示本功能块中的 `grasp_world_offset_z_m` 值；`dtype` 表示本功能块中的 `dtype` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64
# 【L1311】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1312】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `offset_grasp_arm, success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `offset_grasp_arm, success`；`offset_grasp_arm` 表示本功能块中的 `offset_grasp_arm` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        offset_grasp_arm, success = lula.compute_inverse_kinematics(
# 【L1313】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1314】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`offset_target_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `offset_target_position`；在本项目中它表示目标、位置相关值。
            offset_target_position,
# 【L1315】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_orientation`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `target_orientation` 传入 `None`；该参数在本项目中表示目标相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1316】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`grasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `grasp_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1317】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1318】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1319】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1320】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("Lula failed to solve the requested grasp world offset")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("Lula failed to solve the requested grasp world offset")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the requested grasp world offset")
# 【L1321】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_ik_numerical_seed`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `offset_grasp_arm`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `offset_grasp_arm, dtype=np.float64`（本功能块中的 `offset_grasp_arm, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        grasp_ik_numerical_seed = np.asarray(offset_grasp_arm, dtype=np.float64)
# 【L1322】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_arm`。右侧语法为：`closest_equivalent_rm65_solution(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
        grasp_arm = closest_equivalent_rm65_solution(
# 【L1323】语法拆解：`lula, grasp_ik_numerical_seed, grasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `lula, grasp_ik_numerical_seed, grasp_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`grasp_ik_numerical_seed` 表示本功能块中的 `grasp_ik_numerical_seed` 值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            lula, grasp_ik_numerical_seed, grasp_arm
# 【L1324】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1325】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_link_position, grasp_link_rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `grasp_arm`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1326】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `reference_block_from_link_local`。右侧语法为：表达式 `grasp_link_rotation.T @ (` 使用运算符 `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `reference_block_from_link_local`，它在本项目中表示机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_rotation.T @ (`；`grasp_link_rotation` 表示机器人连杆、旋转相关值；`T` 表示本功能块中的 `T` 值。
    reference_block_from_link_local = grasp_link_rotation.T @ (
# 【L1327】语法拆解：表达式 `nominal_source_block_position - grasp_link_position` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `nominal_source_block_position - grasp_link_position` 接入当前完整语句；`nominal_source_block_position` 表示源位置、位置相关值；`grasp_link_position` 表示机器人连杆、位置相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        nominal_source_block_position - grasp_link_position
# 【L1328】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1329】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_ik_seed_index`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `top_down_ik_seed_index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    top_down_ik_seed_index = None
# 【L1330】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `precomputed_retreat_waypoints: list[np.ndarray] | None`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `precomputed_retreat_waypoints`，它在本项目中表示本功能块中的 `precomputed_retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    precomputed_retreat_waypoints: list[np.ndarray] | None = None
# 【L1331】语法拆解：`if` 要求条件 `args.grasp_orientation_mode == "top_down"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.grasp_orientation_mode == "top_down"` 是否成立；`grasp_orientation_mode` 表示本功能块中的 `grasp_orientation_mode` 值；`top_down` 表示本功能块中的 `top_down` 值
    if args.grasp_orientation_mode == "top_down":
# 【L1332】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `calibrated_reference_link_position`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `calibrated_reference_link_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        calibrated_reference_link_position = (
# 【L1333】语法拆解：`source_block_position_base` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `source_block_position_base`；在本项目中它表示源位置、位置相关值。
            source_block_position_base
# 【L1334】语法拆解：表达式 `- grasp_link_rotation @ reference_block_from_link_local` 使用运算符 `-`, `@`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `- grasp_link_rotation @ reference_block_from_link_local` 接到上一行未结束的数学公式；`grasp_link_rotation` 表示机器人连杆、旋转相关值；`reference_block_from_link_local` 表示机器人连杆相关值，整条公式用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            - grasp_link_rotation @ reference_block_from_link_local
# 【L1335】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1336】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_link_position, top_down_rotation, reference_block_from_link_local`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `top_down_link_position, top_down_rotation, reference_block_from_link_local`；`top_down_link_position` 表示机器人连杆、位置相关值；`top_down_rotation` 表示旋转相关值；`reference_block_from_link_local` 表示机器人连杆相关值。右侧的来源是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        top_down_link_position, top_down_rotation, reference_block_from_link_local = (
# 【L1337】语法拆解：`compute_top_down_link_pose(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `compute_top_down_link_pose`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            compute_top_down_link_pose(
# 【L1338】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`calibrated_reference_link_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `calibrated_reference_link_position`；在本项目中它表示机器人连杆、位置相关值。
                calibrated_reference_link_position,
# 【L1339】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`grasp_link_rotation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `grasp_link_rotation`；在本项目中它表示机器人连杆、旋转相关值。
                grasp_link_rotation,
# 【L1340】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`source_block_position_base` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `source_block_position_base`；在本项目中它表示源位置、位置相关值。
                source_block_position_base,
# 【L1341】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_yaw_rad`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.top_down_yaw_rad`；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_yaw_rad,
# 【L1342】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_tilt_rad`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.top_down_tilt_rad`；`top_down_tilt_rad` 表示本功能块中的 `top_down_tilt_rad` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_tilt_rad,
# 【L1343】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_blend`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.top_down_blend`；`top_down_blend` 表示本功能块中的 `top_down_blend` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                args.top_down_blend,
# 【L1344】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1345】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1346】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `ik_seeds`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `ik_seeds`，它在本项目中表示本功能块中的 `ik_seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[grasp_ik_numerical_seed]`；`grasp_ik_numerical_seed` 表示本功能块中的 `grasp_ik_numerical_seed` 值。
        ik_seeds = [grasp_ik_numerical_seed]
# 【L1347】语法拆解：`if` 要求条件 `args.top_down_ik_multistart > 1` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.top_down_ik_multistart > 1` 是否成立；`top_down_ik_multistart` 表示本功能块中的 `top_down_ik_multistart` 值
        if args.top_down_ik_multistart > 1:
# 【L1348】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rng`。右侧语法为：`np.random` 是模块/对象，点号 `.` 从中取出 `default_rng` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `20260916`。
# 【项目含义】得到 `rng`，它在本项目中表示本功能块中的 `rng` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.random.default_rng(20260916)`；`random` 表示本功能块中的 `random` 值；`default_rng` 表示本功能块中的 `default_rng` 值。
            rng = np.random.default_rng(20260916)
# 【L1349】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `random_seeds`。右侧语法为：`rng.uniform(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `random_seeds`，它在本项目中表示本功能块中的 `random_seeds` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rng.uniform(`；`rng` 表示本功能块中的 `rng` 值；`uniform` 表示本功能块中的 `uniform` 值。
            random_seeds = rng.uniform(
# 【L1350】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`RM65_JOINT_LOWER_RAD` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `RM65_JOINT_LOWER_RAD`；在本项目中它表示RM65 机械约束或项目常量。
                RM65_JOINT_LOWER_RAD,
# 【L1351】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`RM65_JOINT_UPPER_RAD` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `RM65_JOINT_UPPER_RAD`；在本项目中它表示RM65 机械约束或项目常量。
                RM65_JOINT_UPPER_RAD,
# 【L1352】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `size`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `size` 传入 `(args.top_down_ik_multistart - 1, len(ARM_JOINTS))`；该参数在本项目中表示本功能块中的 `size` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                size=(args.top_down_ik_multistart - 1, len(ARM_JOINTS)),
# 【L1353】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1354】语法拆解：`ik_seeds` 是模块/对象，点号 `.` 从中取出 `extend` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `random_seeds`。
# 【项目含义】对 `ik_seeds` 执行 `extend`，把 `random_seeds` 加入已有结果；该集合表示本功能块中的 `ik_seeds` 值，随后会用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ik_seeds.extend(random_seeds)
# 【L1355】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_solution`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `top_down_solution`，它在本项目中表示本功能块中的 `top_down_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
        top_down_solution = None
# 【L1356】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `success`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `success`，它在本项目中表示成功相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
        success = False
# 【L1357】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_quaternion`。右侧语法为：`rot_matrix_to_quat` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `top_down_rotation`。
# 【项目含义】得到 `top_down_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rot_matrix_to_quat(top_down_rotation)`；`rot_matrix_to_quat` 表示本功能块中的 `rot_matrix_to_quat` 值；`top_down_rotation` 表示旋转相关值。
        top_down_quaternion = rot_matrix_to_quat(top_down_rotation)
# 【L1358】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `minimum_pregrasp_distance_m`。右侧语法为：`min` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `requested_pregrasp_distance_m`；第 2 个实参 `0.05`。
# 【项目含义】得到 `minimum_pregrasp_distance_m`，它在本项目中表示本功能块中的 `minimum_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `min(requested_pregrasp_distance_m, 0.05)`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值。
        minimum_pregrasp_distance_m = min(requested_pregrasp_distance_m, 0.05)
# 【L1359】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `fallback_count`。右侧语法为：`int(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `fallback_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `int(` 的结果保存下来，供当前功能块后续使用。
        fallback_count = int(
# 【L1360】语法拆解：`np.floor(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `np` 调用多行方法 `floor`：调用 `np` 提供的 `floor` 操作；具体参数写在随后几行，用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            np.floor(
# 【L1361】语法拆解：表达式 `(requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`(requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01`；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值；`minimum_pregrasp_distance_m` 表示本功能块中的 `minimum_pregrasp_distance_m` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                (requested_pregrasp_distance_m - minimum_pregrasp_distance_m) / 0.01
# 【L1362】语法拆解：表达式 `+ 1e-9` 使用运算符 `+`, `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把运算项 `+ 1e-9` 接到上一行未结束的数学公式；数字和运算符共同决定上一变量的最终值，整条公式用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                + 1e-9
# 【L1363】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1364】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1365】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pregrasp_distance_candidates`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pregrasp_distance_candidates`，它在本项目中表示本功能块中的 `pregrasp_distance_candidates` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
        pregrasp_distance_candidates = [
# 【L1366】语法拆解：表达式 `requested_pregrasp_distance_m - 0.01 * index` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `requested_pregrasp_distance_m - 0.01 * index` 接入当前完整语句；`requested_pregrasp_distance_m` 表示本功能块中的 `requested_pregrasp_distance_m` 值；`index` 表示索引相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            requested_pregrasp_distance_m - 0.01 * index
# 【L1367】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for index in range(fallback_count + 1)` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            for index in range(fallback_count + 1)
# 【L1368】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ]
# 【L1369】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `pregrasp_distance_candidates`，每次把当前元素放进 `candidate_pregrasp_distance_m`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
        for candidate_pregrasp_distance_m in pregrasp_distance_candidates:
# 【L1370】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_distances_for_selection`。右侧语法为：`np.linspace(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `retreat_distances_for_selection`，它在本项目中表示本功能块中的 `retreat_distances_for_selection` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(`；`linspace` 表示本功能块中的 `linspace` 值。
            retreat_distances_for_selection = np.linspace(
# 【L1371】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`0.01` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `0.01`；逗号说明后面还有同级参数，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                0.01,
# 【L1372】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`candidate_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `candidate_pregrasp_distance_m`；在本项目中它表示本功能块中的 `candidate_pregrasp_distance_m` 值。
                candidate_pregrasp_distance_m,
# 【L1373】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`max` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `1`；第 2 个实参 `int(round(candidate_pregrasp_distance_m / 0.01))`。
# 【项目含义】调用 `max(1, int(round(candidate_pregrasp_distance_m / 0.01)))`：从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                max(1, int(round(candidate_pregrasp_distance_m / 0.01))),
# 【L1374】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1375】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_targets_for_selection`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `retreat_targets_for_selection`，它在本项目中表示本功能块中的 `retreat_targets_for_selection` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
            retreat_targets_for_selection = [
# 【L1376】语法拆解：`top_down_link_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `top_down_link_position`；在本项目中它表示机器人连杆、位置相关值。
                top_down_link_position
# 【L1377】语法拆解：表达式 `+ np.array([0.0, 0.0, distance], dtype=np.float64)` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `+ np.array([0.0, 0.0, distance], dtype=np.float64)`。`array` 表示本功能块中的 `array` 值；`distance` 表示本功能块中的 `distance` 值。
                + np.array([0.0, 0.0, distance], dtype=np.float64)
# 【L1378】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for distance in retreat_distances_for_selection` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                for distance in retreat_distances_for_selection
# 【L1379】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ]
# 【L1380】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(ik_seeds)`，每次把当前元素放进 `seed_index, ik_seed`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
            for seed_index, ik_seed in enumerate(ik_seeds):
# 【L1381】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate_solution, candidate_success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `candidate_solution, candidate_success`；`candidate_solution` 表示本功能块中的 `candidate_solution` 值；`candidate_success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
                candidate_solution, candidate_success = lula.compute_inverse_kinematics(
# 【L1382】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                    "link_6",
# 【L1383】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`top_down_link_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `top_down_link_position`；在本项目中它表示机器人连杆、位置相关值。
                    top_down_link_position,
# 【L1384】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`top_down_quaternion` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `top_down_quaternion`；在本项目中它表示四元数相关值。
                    top_down_quaternion,
# 【L1385】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `ik_seed`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `np.asarray(ik_seed, dtype=np.float64)`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    warm_start=np.asarray(ik_seed, dtype=np.float64),
# 【L1386】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    position_tolerance=1e-4,
# 【L1387】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `orientation_tolerance`。右侧语法为：`1e-3` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    orientation_tolerance=1e-3,
# 【L1388】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                )
# 【L1389】语法拆解：`if` 要求条件 `not candidate_success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not candidate_success` 是否成立；`candidate_success` 表示成功相关值
                if not candidate_success:
# 【L1390】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中不满足继续条件。
                    continue
# 【L1391】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate_raw`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `candidate_solution`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `candidate_raw`，它在本项目中表示原始相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `candidate_solution, dtype=np.float64`（本功能块中的 `candidate_solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
                candidate_raw = np.asarray(candidate_solution, dtype=np.float64)
# 【L1392】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
                try:
# 【L1393】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate_command`。右侧语法为：`closest_equivalent_rm65_solution(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `candidate_command`，它在本项目中表示控制命令相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
                    candidate_command = closest_equivalent_rm65_solution(
# 【L1394】语法拆解：`lula, candidate_raw, grasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `lula, candidate_raw, grasp_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`candidate_raw` 表示原始相关值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                        lula, candidate_raw, grasp_arm
# 【L1395】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1396】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate_retreat`。右侧语法为：`solve_continuous_cartesian_path(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `candidate_retreat`，它在本项目中表示本功能块中的 `candidate_retreat` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `solve_continuous_cartesian_path(`；`solve_continuous_cartesian_path` 表示路径相关值。
                    candidate_retreat = solve_continuous_cartesian_path(
# 【L1397】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`lula` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `lula`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
                        lula,
# 【L1398】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`retreat_targets_for_selection` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `retreat_targets_for_selection`；在本项目中它表示本功能块中的 `retreat_targets_for_selection` 值。
                        retreat_targets_for_selection,
# 【L1399】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`top_down_quaternion` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `top_down_quaternion`；在本项目中它表示四元数相关值。
                        top_down_quaternion,
# 【L1400】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`candidate_raw` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `candidate_raw`；在本项目中它表示原始相关值。
                        candidate_raw,
# 【L1401】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`candidate_command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `candidate_command`；在本项目中它表示控制命令相关值。
                        candidate_command,
# 【L1402】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                    )
# 【L1403】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `RuntimeError`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
                except RuntimeError:
# 【L1404】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `candidate_retreat`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `candidate_retreat`，它在本项目中表示本功能块中的 `candidate_retreat` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
                    candidate_retreat = None
# 【L1405】语法拆解：`if` 要求条件 `candidate_retreat is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `candidate_retreat is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
                if candidate_retreat is None:
# 【L1406】语法拆解：`continue` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中不满足继续条件。
                    continue
# 【L1407】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_, candidate_retreat_waypoints, _`。右侧语法为：`candidate_retreat` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `_, candidate_retreat_waypoints, _`；`_` 表示本功能块中的 `_` 值；`candidate_retreat_waypoints` 表示本功能块中的 `candidate_retreat_waypoints` 值；`_` 表示本功能块中的 `_` 值。右侧的来源是：计算表达式 `candidate_retreat`；`candidate_retreat` 表示本功能块中的 `candidate_retreat` 值。
                _, candidate_retreat_waypoints, _ = candidate_retreat
# 【L1408】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_ik_numerical_seed`。右侧语法为：`candidate_raw` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `grasp_ik_numerical_seed`，它在本项目中表示本功能块中的 `grasp_ik_numerical_seed` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_raw`；`candidate_raw` 表示原始相关值。
                grasp_ik_numerical_seed = candidate_raw
# 【L1409】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_solution`。右侧语法为：`candidate_command` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `top_down_solution`，它在本项目中表示本功能块中的 `top_down_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_command`；`candidate_command` 表示控制命令相关值。
                top_down_solution = candidate_command
# 【L1410】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `precomputed_retreat_waypoints`。右侧语法为：`candidate_retreat_waypoints` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `precomputed_retreat_waypoints`，它在本项目中表示本功能块中的 `precomputed_retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_retreat_waypoints`；`candidate_retreat_waypoints` 表示本功能块中的 `candidate_retreat_waypoints` 值。
                precomputed_retreat_waypoints = candidate_retreat_waypoints
# 【L1411】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `top_down_ik_seed_index`。右侧语法为：`seed_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `top_down_ik_seed_index`，它在本项目中表示索引相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `seed_index`；`seed_index` 表示索引相关值。
                top_down_ik_seed_index = seed_index
# 【L1412】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `effective_pregrasp_distance_m`。右侧语法为：`candidate_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `effective_pregrasp_distance_m`，它在本项目中表示本功能块中的 `effective_pregrasp_distance_m` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `candidate_pregrasp_distance_m`；`candidate_pregrasp_distance_m` 表示本功能块中的 `candidate_pregrasp_distance_m` 值。
                effective_pregrasp_distance_m = candidate_pregrasp_distance_m
# 【L1413】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `success`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】得到 `success`，它在本项目中表示成功相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `True` 的结果保存下来，供当前功能块后续使用。
                success = True
# 【L1414】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L1415】语法拆解：`if` 要求条件 `success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `success` 是否成立；`success` 表示成功相关值
            if success:
# 【L1416】语法拆解：`break` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】立即结束最近一层循环；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中表示已经找到解、完成 episode 或无需再尝试剩余候选。
                break
# 【L1417】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1418】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”进度，也给日志留下可搜索证据。
            print(
# 【L1419】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"TOP_DOWN_IK_TARGET="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "TOP_DOWN_IK_TARGET="
# 【L1420】语法拆解：`f"position={top_down_link_position.tolist()} "` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"position={top_down_link_position.tolist()} "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`position` 表示位置相关值；`top_down_link_position` 表示机器人连杆、位置相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"position={top_down_link_position.tolist()} "
# 【L1421】语法拆解：`f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把表达式/参数 `f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "` 接入当前完整语句；`f` 表示本功能块中的 `f` 值；`yaw` 表示本功能块中的 `yaw` 值；`top_down_yaw_rad` 表示本功能块中的 `top_down_yaw_rad` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "
# 【L1422】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}"`；`f` 表示本功能块中的 `f` 值；`blend` 表示本功能块中的 `blend` 值；`top_down_blend` 表示本功能块中的 `top_down_blend` 值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}",
# 【L1423】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                flush=True,
# 【L1424】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1425】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(
# 【L1426】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"Lula found no top-down grasp pose with a continuous pregrasp path"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "Lula found no top-down grasp pose with a continuous pregrasp path"
# 【L1427】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1428】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_arm`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `top_down_solution`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `grasp_arm`，它在本项目中表示本功能块中的 `grasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：读取/计算 `top_down_solution, dtype=np.float64`（本功能块中的 `top_down_solution, dtype=np.float64` 值），再用 `np.asarray` 统一为 NumPy ndarray；这样后续可稳定检查 shape/dtype、切片和做向量运算。
        grasp_arm = np.asarray(top_down_solution, dtype=np.float64)
# 【L1429】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_link_position, grasp_link_rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `grasp_arm`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `grasp_link_position, grasp_link_rotation`；`grasp_link_position` 表示机器人连杆、位置相关值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
# 【L1430】语法拆解：`if` 要求条件 `args.lift_mode == "cartesian_vertical"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.lift_mode == "cartesian_vertical"` 是否成立；`lift_mode` 表示本功能块中的 `lift_mode` 值；`cartesian_vertical` 表示本功能块中的 `cartesian_vertical` 值
    if args.lift_mode == "cartesian_vertical":
# 【L1431】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `vertical_lift_target`。右侧语法为：表达式 `grasp_link_position + np.array(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `vertical_lift_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `grasp_link_position + np.array(`；`grasp_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        vertical_lift_target = grasp_link_position + np.array(
# 【L1432】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[0.0, 0.0, args.cartesian_lift_height_m], dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64`；`cartesian_lift_height_m` 表示本功能块中的 `cartesian_lift_height_m` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64
# 【L1433】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1434】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_arm_solution, success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `lift_arm_solution, success`；`lift_arm_solution` 表示本功能块中的 `lift_arm_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        lift_arm_solution, success = lula.compute_inverse_kinematics(
# 【L1435】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1436】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`vertical_lift_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `vertical_lift_target`；在本项目中它表示目标相关值。
            vertical_lift_target,
# 【L1437】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`rot_matrix_to_quat` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `grasp_link_rotation`。
# 【项目含义】调用 `rot_matrix_to_quat(grasp_link_rotation)`：把 3×3 旋转矩阵转换为 wxyz 四元数，供 Lula/Isaac 的姿态接口使用。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            rot_matrix_to_quat(grasp_link_rotation),
# 【L1438】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`grasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `grasp_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=grasp_arm,
# 【L1439】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1440】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `orientation_tolerance`。右侧语法为：`1e-3` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            orientation_tolerance=1e-3,
# 【L1441】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1442】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1443】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("Lula failed to solve the local Cartesian vertical lift")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("Lula failed to solve the local Cartesian vertical lift")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the local Cartesian vertical lift")
# 【L1444】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_arm`。右侧语法为：`closest_equivalent_rm65_solution` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `lula`；第 2 个实参 `lift_arm_solution`；第 3 个实参 `grasp_arm`。
# 【项目含义】得到 `lift_arm`，它在本项目中表示本功能块中的 `lift_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值；`lula` 表示NVIDIA Lula 运动学求解器实例；`lift_arm_solution` 表示本功能块中的 `lift_arm_solution` 值。
        lift_arm = closest_equivalent_rm65_solution(lula, lift_arm_solution, grasp_arm)
# 【L1445】语法拆解：`require_continuous_joint_step` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `grasp_arm`；第 2 个实参 `lift_arm`；第 3 个实参 `label="vertical lift"`。
# 【项目含义】调用 `require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")`：检查前后两个六关节姿态的最大跳变量，过大时拒绝这条 IK 路径。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        require_continuous_joint_step(grasp_arm, lift_arm, label="vertical lift")
# 【L1446】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_link_position, lift_link_rotation`。右侧语法为：`lula` 是模块/对象，点号 `.` 从中取出 `compute_forward_kinematics` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"link_6"`；第 2 个实参 `lift_arm`。
# 【项目含义】把右侧返回的多个结果按位置拆给 `lift_link_position, lift_link_rotation`；`lift_link_position` 表示机器人连杆、位置相关值；`lift_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    lift_link_position, lift_link_rotation = lula.compute_forward_kinematics("link_6", lift_arm)
# 【L1447】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_lift_translation`。右侧语法为：表达式 `lift_link_position - grasp_link_position` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `expected_lift_translation`，它在本项目中表示本功能块中的 `expected_lift_translation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lift_link_position - grasp_link_position`；`lift_link_position` 表示机器人连杆、位置相关值；`grasp_link_position` 表示机器人连杆、位置相关值。
    expected_lift_translation = lift_link_position - grasp_link_position
# 【L1448】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expected_source_lift_block_position`。右侧语法为：表达式 `source_block_position + expected_lift_translation` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `expected_source_lift_block_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `source_block_position + expected_lift_translation`；`source_block_position` 表示源位置、位置相关值；`expected_lift_translation` 表示本功能块中的 `expected_lift_translation` 值。
    expected_source_lift_block_position = source_block_position + expected_lift_translation
# 【L1449】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_lift_arm`。右侧语法为：`lift_arm` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `target_lift_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    target_lift_arm = lift_arm.copy()
# 【L1450】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_lift_arm[0]`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】把右侧结果写进 `target_lift_arm[0]`（写入 `target_lift_arm[0]` 指定的字段）；右侧具体做的是：计算表达式 `args.transfer_joint_1_rad`；`transfer_joint_1_rad` 表示关节相关值。
    target_lift_arm[0] = args.transfer_joint_1_rad
# 【L1451】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `transferred_link_position, transferred_link_rotation`。右侧语法为：`lula.compute_forward_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `transferred_link_position, transferred_link_rotation`；`transferred_link_position` 表示机器人连杆、位置相关值；`transferred_link_rotation` 表示机器人连杆、旋转相关值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
    transferred_link_position, transferred_link_rotation = lula.compute_forward_kinematics(
# 【L1452】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6", target_lift_arm`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
        "link_6", target_lift_arm
# 【L1453】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1454】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_clear_arm`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `release_clear_arm`，它在本项目中表示本功能块中的 `release_clear_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    release_clear_arm = None
# 【L1455】语法拆解：`if` 要求条件 `args.unassisted_release and not args.place_descent` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.unassisted_release and not args.place_descent` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值；`place_descent` 表示本功能块中的 `place_descent` 值
    if args.unassisted_release and not args.place_descent:
# 【L1456】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_clear_target`。右侧语法为：表达式 `transferred_link_position + np.array(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `release_clear_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `transferred_link_position + np.array(`；`transferred_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
        release_clear_target = transferred_link_position + np.array(
# 【L1457】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[0.0, 0.0, args.release_clearance_m], dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, args.release_clearance_m], dtype=np.float64`；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            [0.0, 0.0, args.release_clearance_m], dtype=np.float64
# 【L1458】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1459】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_clear_solution, success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `release_clear_solution, success`；`release_clear_solution` 表示本功能块中的 `release_clear_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
        release_clear_solution, success = lula.compute_inverse_kinematics(
# 【L1460】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6",
# 【L1461】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`release_clear_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `release_clear_target`；在本项目中它表示目标相关值。
            release_clear_target,
# 【L1462】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_orientation`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `target_orientation` 传入 `None`；该参数在本项目中表示目标相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_orientation=None,
# 【L1463】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `target_lift_arm`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            warm_start=target_lift_arm,
# 【L1464】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            position_tolerance=1e-4,
# 【L1465】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1466】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
        if not success:
# 【L1467】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("Lula failed to solve the vertical release-clearance motion")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("Lula failed to solve the vertical release-clearance motion")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula failed to solve the vertical release-clearance motion")
# 【L1468】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_clear_arm`。右侧语法为：`closest_equivalent_rm65_solution(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `release_clear_arm`，它在本项目中表示本功能块中的 `release_clear_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
        release_clear_arm = closest_equivalent_rm65_solution(
# 【L1469】语法拆解：`lula, release_clear_solution, target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `lula, release_clear_solution, target_lift_arm` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`release_clear_solution` 表示本功能块中的 `release_clear_solution` 值；`target_lift_arm` 表示目标相关值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            lula, release_clear_solution, target_lift_arm
# 【L1470】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1471】语法拆解：`require_continuous_joint_step(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `require_continuous_joint_step`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        require_continuous_joint_step(
# 【L1472】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_lift_arm, release_clear_arm, label`。右侧语法为：`"release clearance"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】把右侧返回的多个结果按位置拆给 `target_lift_arm, release_clear_arm, label`；`target_lift_arm` 表示目标相关值；`release_clear_arm` 表示本功能块中的 `release_clear_arm` 值；`label` 表示本功能块中的 `label` 值。右侧的来源是：计算表达式 `"release clearance"`；`release` 表示本功能块中的 `release` 值；`clearance` 表示本功能块中的 `clearance` 值。
            target_lift_arm, release_clear_arm, label="release clearance"
# 【L1473】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1474】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1475】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `transfer_quaternion`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `transfer_quaternion`，它在本项目中表示四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    transfer_quaternion = np.array(
# 【L1476】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],`；`cos` 表示本功能块中的 `cos` 值；`transfer_joint_1_rad` 表示关节相关值；`sin` 表示本功能块中的 `sin` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],
# 【L1477】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1478】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1479】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_release_position`。右侧语法为：`rotate_about_z` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `expected_source_lift_block_position`；第 2 个实参 `args.transfer_joint_1_rad`。
# 【项目含义】得到 `target_release_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)`；`rotate_about_z` 表示本功能块中的 `rotate_about_z` 值；`expected_source_lift_block_position` 表示源位置、位置相关值；`transfer_joint_1_rad` 表示关节相关值。
    target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)
# 【L1480】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_block_position`。右侧语法为：`target_release_position` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `target_block_position`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    target_block_position = target_release_position.copy()
# 【L1481】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_block_position[2]`。右侧语法为：表达式 `TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0` 使用运算符 `+`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把右侧结果写进 `target_block_position[2]`（写入 `target_block_position[2]` 指定的字段）；右侧具体做的是：计算表达式 `TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0`；`TARGET_PLATFORM_TOP_Z` 表示目标位置方块/平台的任务常量；`BLOCK_SIZE` 表示本功能块中的 `BLOCK_SIZE` 值。
    target_block_position[2] = TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
# 【L1482】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_block_quaternion`。右侧语法为：`quaternion_multiply_wxyz` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `transfer_quaternion`；第 2 个实参 `source_block_quaternion`。
# 【项目含义】得到 `target_block_quaternion`，它在本项目中表示目标、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)`；`quaternion_multiply_wxyz` 表示四元数相关值；`transfer_quaternion` 表示四元数相关值；`source_block_quaternion` 表示源位置、四元数相关值。
    target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)
# 【L1483】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_platform_size`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_platform_size`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    target_platform_size = (
# 【L1484】语法拆解：表达式 `TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE` 接到上一行尚未结束的布尔表达式；`TARGET_STRIP_SIZE` 表示目标位置方块/平台的任务常量；`target_support_mode` 表示目标相关值；`rotated_strip` 表示本功能块中的 `rotated_strip` 值。比较结果共同决定“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”是否通过。
        TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE
# 【L1485】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1486】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_platform_orientation`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_platform_orientation`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    target_platform_orientation = (
# 【L1487】语法拆解：表达式 `tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None` 接到上一行尚未结束的布尔表达式；`transfer_quaternion` 表示四元数相关值；`target_support_mode` 表示目标相关值；`rotated_strip` 表示本功能块中的 `rotated_strip` 值。比较结果共同决定“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”是否通过。
        tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None
# 【L1488】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1489】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_platform_position`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `target_platform_position`，它在本项目中表示目标、支撑平台、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
    target_platform_position = np.array(
# 【L1490】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        [
# 【L1491】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_block_position[0]` 使用方括号索引；先计算 `0`，再从 `target_block_position` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `target_block_position[0]`；`target_block_position` 表示目标、位置相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[0],
# 【L1492】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_block_position[1]` 使用方括号索引；先计算 `1`，再从 `target_block_position` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `target_block_position[1]`；`target_block_position` 表示目标、位置相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            target_block_position[1],
# 【L1493】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0`；`TARGET_PLATFORM_TOP_Z` 表示目标位置方块/平台的任务常量；`target_platform_size` 表示目标、支撑平台相关值，它参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0,
# 【L1494】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        ],
# 【L1495】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        dtype=np.float64,
# 【L1496】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1497】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_waypoints`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `place_waypoints`，它在本项目中表示本功能块中的 `place_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    place_waypoints = []
# 【L1498】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：The pi0.5 branch returns to run_pi05_closed_loop before the scripted
    # The pi0.5 branch returns to run_pi05_closed_loop before the scripted
# 【L1499】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：descent below is ever executed. Do not reject policy evaluation cases
    # descent below is ever executed. Do not reject policy evaluation cases
# 【L1500】语法拆解：行首 `#` 表示注释；Python/Bash 不执行其后文字。
# 【项目含义】作者写下的设计说明：because an unused scripted-only trajectory crosses a different IK branch.
    # because an unused scripted-only trajectory crosses a different IK branch.
# 【L1501】语法拆解：`if` 要求条件 `args.place_descent and not args.pi05_closed_loop` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.place_descent and not args.pi05_closed_loop` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
    if args.place_descent and not args.pi05_closed_loop:
# 【L1502】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_waypoint_count`。右侧语法为：`max` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `1`；第 2 个实参 `int(round(args.place_descent_distance_m / 0.01))`。
# 【项目含义】得到 `place_waypoint_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(1, int(round(args.place_descent_distance_m / 0.01)))`；`round` 表示本功能块中的 `round` 值；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值。
        place_waypoint_count = max(1, int(round(args.place_descent_distance_m / 0.01)))
# 【L1503】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_distances`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `linspace` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0.01`；第 2 个实参 `args.place_descent_distance_m`；第 3 个实参 `place_waypoint_count`。
# 【项目含义】得到 `place_distances`，它在本项目中表示本功能块中的 `place_distances` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)`；`linspace` 表示本功能块中的 `linspace` 值；`place_descent_distance_m` 表示本功能块中的 `place_descent_distance_m` 值；`place_waypoint_count` 表示数量相关值。
        place_distances = np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)
# 【L1504】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_warm_start`。右侧语法为：`lift_arm` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `place_warm_start`，它在本项目中表示本功能块中的 `place_warm_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        place_warm_start = lift_arm.copy()
# 【L1505】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `place_distances`，每次把当前元素放进 `distance`；这会逐个处理“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”所需的帧、episode、动作或实验 case。
        for distance in place_distances:
# 【L1506】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_link_target`。右侧语法为：表达式 `lift_link_position - np.array(` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `place_link_target`，它在本项目中表示机器人连杆、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lift_link_position - np.array(`；`lift_link_position` 表示机器人连杆、位置相关值；`array` 表示本功能块中的 `array` 值。
            place_link_target = lift_link_position - np.array(
# 【L1507】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `[0.0, 0.0, distance], dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, distance], dtype=np.float64`；`distance` 表示本功能块中的 `distance` 值；`dtype` 表示本功能块中的 `dtype` 值；`float64` 表示本功能块中的 `float64` 值，共同完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                [0.0, 0.0, distance], dtype=np.float64
# 【L1508】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1509】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_solution, success`。右侧语法为：`lula.compute_inverse_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `place_solution, success`；`place_solution` 表示本功能块中的 `place_solution` 值；`success` 表示成功相关值。右侧的来源是：让 Lula 根据末端目标位置/姿态和 warm start 求六个 RM65 关节角。
            place_solution, success = lula.compute_inverse_kinematics(
# 【L1510】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的帮助说明、错误原因、任务名称或报告文字。
                "link_6",
# 【L1511】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`place_link_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `place_link_target`；在本项目中它表示机器人连杆、目标相关值。
                place_link_target,
# 【L1512】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`rot_matrix_to_quat` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `lift_link_rotation`。
# 【项目含义】调用 `rot_matrix_to_quat(lift_link_rotation)`：把 3×3 旋转矩阵转换为 wxyz 四元数，供 Lula/Isaac 的姿态接口使用。它的结果/修改用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                rot_matrix_to_quat(lift_link_rotation),
# 【L1513】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `warm_start`。右侧语法为：`place_warm_start` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `warm_start` 传入 `place_warm_start`；该参数在本项目中表示本功能块中的 `warm_start` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                warm_start=place_warm_start,
# 【L1514】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `position_tolerance`。右侧语法为：`1e-4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `position_tolerance` 传入 `1e-4`；该参数在本项目中表示位置相关值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                position_tolerance=1e-4,
# 【L1515】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `orientation_tolerance`。右侧语法为：`1e-3` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `orientation_tolerance` 传入 `1e-3`；该参数在本项目中表示本功能块中的 `orientation_tolerance` 值，会参与“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                orientation_tolerance=1e-3,
# 【L1516】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1517】语法拆解：`if` 要求条件 `not success` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not success` 是否成立；`success` 表示成功相关值
            if not success:
# 【L1518】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
                raise RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")
# 【L1519】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_solution`。右侧语法为：`closest_equivalent_rm65_solution(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `place_solution`，它在本项目中表示本功能块中的 `place_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closest_equivalent_rm65_solution(`；`closest_equivalent_rm65_solution` 表示本功能块中的 `closest_equivalent_rm65_solution` 值。
            place_solution = closest_equivalent_rm65_solution(
# 【L1520】语法拆解：`lula, place_solution, place_warm_start` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `lula, place_solution, place_warm_start` 接入当前完整语句；`lula` 表示NVIDIA Lula 运动学求解器实例；`place_solution` 表示本功能块中的 `place_solution` 值；`place_warm_start` 表示本功能块中的 `place_warm_start` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                lula, place_solution, place_warm_start
# 【L1521】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1522】语法拆解：`require_continuous_joint_step(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `require_continuous_joint_step`；随后几行会逐项给它参数，调用结果或副作用用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            require_continuous_joint_step(
# 【L1523】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_warm_start, place_solution, label`。右侧语法为：`f"place waypoint {distance:.3f} m"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】把右侧返回的多个结果按位置拆给 `place_warm_start, place_solution, label`；`place_warm_start` 表示本功能块中的 `place_warm_start` 值；`place_solution` 表示本功能块中的 `place_solution` 值；`label` 表示本功能块中的 `label` 值。右侧的来源是：计算表达式 `f"place waypoint {distance:.3f} m"`；`f` 表示本功能块中的 `f` 值；`place` 表示本功能块中的 `place` 值；`waypoint` 表示本功能块中的 `waypoint` 值。
                place_warm_start, place_solution, label=f"place waypoint {distance:.3f} m"
# 【L1524】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            )
# 【L1525】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_warm_start`。右侧语法为：`place_solution` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `place_warm_start`，它在本项目中表示本功能块中的 `place_warm_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `place_solution`；`place_solution` 表示本功能块中的 `place_solution` 值。
            place_warm_start = place_solution
# 【L1526】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rotated_place_solution`。右侧语法为：`place_warm_start` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `rotated_place_solution`，它在本项目中表示本功能块中的 `rotated_place_solution` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
            rotated_place_solution = place_warm_start.copy()
# 【L1527】语法拆解：`rotated_place_solution[0] += args.transfer_joint_1_rad - lift_arm[0]` 使用方括号索引；先计算 `0] += args.transfer_joint_1_rad - lift_arm[0`，再从 `rotated_place_solution` 取对应字典字段或数组元素。
# 【项目含义】用 `rotated_place_solution[0] + args.transfer_joint_1_rad - lift_arm[0]` 更新 `rotated_place_solution[0]` 原值；`rotated_place_solution[0]` 表示本功能块中的 `rotated_place_solution[0]` 值，常用于累计步数、距离、损失或成功次数。
            rotated_place_solution[0] += args.transfer_joint_1_rad - lift_arm[0]
# 【L1528】语法拆解：`place_waypoints` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `rotated_place_solution`。
# 【项目含义】对 `place_waypoints` 执行 `append`，把 `rotated_place_solution` 加入已有结果；该集合表示本功能块中的 `place_waypoints` 值，随后会用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            place_waypoints.append(rotated_place_solution)
# 【L1529】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1530】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `grasp_link_quaternion`。右侧语法为：`rot_matrix_to_quat` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `grasp_link_rotation`。
# 【项目含义】得到 `grasp_link_quaternion`，它在本项目中表示机器人连杆、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rot_matrix_to_quat(grasp_link_rotation)`；`rot_matrix_to_quat` 表示本功能块中的 `rot_matrix_to_quat` 值；`grasp_link_rotation` 表示机器人连杆、旋转相关值。
    grasp_link_quaternion = rot_matrix_to_quat(grasp_link_rotation)
# 【L1531】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `outward_direction`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `outward_direction`，它在本项目中表示本功能块中的 `outward_direction` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    outward_direction = (
# 【L1532】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `array` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[0.0, 0.0, -1.0]`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `np.array([0.0, 0.0, -1.0], dtype=np.float64)`。`array` 表示本功能块中的 `array` 值；`dtype` 表示本功能块中的 `dtype` 值。
        np.array([0.0, 0.0, -1.0], dtype=np.float64)
# 【L1533】语法拆解：`if` 要求条件 `args.grasp_orientation_mode == "top_down"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.grasp_orientation_mode == "top_down"` 是否成立；`grasp_orientation_mode` 表示本功能块中的 `grasp_orientation_mode` 值；`top_down` 表示本功能块中的 `top_down` 值
        if args.grasp_orientation_mode == "top_down"
# 【L1534】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `quaternion_to_matrix_wxyz(`；它让“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”在可选数据缺失时仍有明确结果。
        else quaternion_to_matrix_wxyz(
# 【L1535】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `SOURCE_BLOCK_QUATERNION_WXYZ`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)`。`asarray` 表示本功能块中的 `asarray` 值；`SOURCE_BLOCK_QUATERNION_WXYZ` 表示源位置方块/平台的任务常量。
            np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
# 【L1536】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `)[:, 0]` 中的索引或转换；结果仍属于上一条完整表达式，用于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )[:, 0]
# 【L1537】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1538】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `waypoint_count`。右侧语法为：`max` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `1`；第 2 个实参 `int(round(effective_pregrasp_distance_m / 0.01))`。
# 【项目含义】得到 `waypoint_count`，它在本项目中表示数量相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(1, int(round(effective_pregrasp_distance_m / 0.01)))`；`round` 表示本功能块中的 `round` 值；`effective_pregrasp_distance_m` 表示本功能块中的 `effective_pregrasp_distance_m` 值。
    waypoint_count = max(1, int(round(effective_pregrasp_distance_m / 0.01)))
# 【L1539】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_distances`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `linspace` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `0.01`；第 2 个实参 `effective_pregrasp_distance_m`；第 3 个实参 `waypoint_count`。
# 【项目含义】得到 `retreat_distances`，它在本项目中表示本功能块中的 `retreat_distances` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.linspace(0.01, effective_pregrasp_distance_m, waypoint_count)`；`linspace` 表示本功能块中的 `linspace` 值；`effective_pregrasp_distance_m` 表示本功能块中的 `effective_pregrasp_distance_m` 值；`waypoint_count` 表示数量相关值。
    retreat_distances = np.linspace(0.01, effective_pregrasp_distance_m, waypoint_count)
# 【L1540】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_targets`。右侧语法为：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `retreat_targets`，它在本项目中表示本功能块中的 `retreat_targets` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[` 的结果保存下来，供当前功能块后续使用。
    retreat_targets = [
# 【L1541】语法拆解：表达式 `grasp_link_position - distance * outward_direction` 使用运算符 `-`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `grasp_link_position - distance * outward_direction` 接入当前完整语句；`grasp_link_position` 表示机器人连杆、位置相关值；`distance` 表示本功能块中的 `distance` 值；`outward_direction` 表示本功能块中的 `outward_direction` 值。在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        grasp_link_position - distance * outward_direction
# 【L1542】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for distance in retreat_distances` 中给出的序列，逐项完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        for distance in retreat_distances
# 【L1543】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    ]
# 【L1544】语法拆解：`if` 要求条件 `precomputed_retreat_waypoints is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `precomputed_retreat_waypoints is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if precomputed_retreat_waypoints is not None:
# 【L1545】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_waypoints`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `retreat_waypoints`，它在本项目中表示本功能块中的 `retreat_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        retreat_waypoints = [item.copy() for item in precomputed_retreat_waypoints]
# 【L1546】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中处理剩余输入或备用路径。
    else:
# 【L1547】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_result`。右侧语法为：`solve_continuous_cartesian_path(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `retreat_result`，它在本项目中表示结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `solve_continuous_cartesian_path(`；`solve_continuous_cartesian_path` 表示路径相关值。
        retreat_result = solve_continuous_cartesian_path(
# 【L1548】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`lula` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `lula`；在本项目中它表示NVIDIA Lula 运动学求解器实例。
            lula,
# 【L1549】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`retreat_targets` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `retreat_targets`；在本项目中它表示本功能块中的 `retreat_targets` 值。
            retreat_targets,
# 【L1550】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`grasp_link_quaternion` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `grasp_link_quaternion`；在本项目中它表示机器人连杆、四元数相关值。
            grasp_link_quaternion,
# 【L1551】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`grasp_ik_numerical_seed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `grasp_ik_numerical_seed`；在本项目中它表示本功能块中的 `grasp_ik_numerical_seed` 值。
            grasp_ik_numerical_seed,
# 【L1552】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`grasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `grasp_arm`；在本项目中它表示本功能块中的 `grasp_arm` 值。
            grasp_arm,
# 【L1553】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1554】语法拆解：`if` 要求条件 `retreat_result is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `retreat_result is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if retreat_result is None:
# 【L1555】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("Lula found no continuous Cartesian pregrasp path")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("Lula found no continuous Cartesian pregrasp path")` 并停止当前路径；说明当前输入违反“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError("Lula found no continuous Cartesian pregrasp path")
# 【L1556】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `_, retreat_waypoints, _`。右侧语法为：`retreat_result` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `_, retreat_waypoints, _`；`_` 表示本功能块中的 `_` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值；`_` 表示本功能块中的 `_` 值。右侧的来源是：计算表达式 `retreat_result`；`retreat_result` 表示结果相关值。
        _, retreat_waypoints, _ = retreat_result
# 【L1557】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pregrasp_arm`。右侧语法为：表达式 `grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `pregrasp_arm`，它在本项目中表示本功能块中的 `pregrasp_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
    pregrasp_arm = grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]
# 【L1558】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_joint_sequence`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `vstack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[grasp_arm, *retreat_waypoints]`。
# 【项目含义】得到 `retreat_joint_sequence`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.vstack([grasp_arm, *retreat_waypoints])`；`vstack` 表示本功能块中的 `vstack` 值；`grasp_arm` 表示本功能块中的 `grasp_arm` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。
    retreat_joint_sequence = np.vstack([grasp_arm, *retreat_waypoints])
# 【L1559】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_max_command_step_rad`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `retreat_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    retreat_max_command_step_rad = float(
# 【L1560】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `max` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.abs(np.diff(retreat_joint_sequence, axis=0))`。
# 【项目含义】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(retreat_joint_sequence, axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
        np.max(np.abs(np.diff(retreat_joint_sequence, axis=0)))
# 【L1561】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
    )
# 【L1562】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

# 【L1563】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_max_command_step_rad`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `place_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_max_command_step_rad = None
# 【L1564】语法拆解：`if` 要求条件 `place_waypoints` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `place_waypoints` 是否成立；`place_waypoints` 表示本功能块中的 `place_waypoints` 值
    if place_waypoints:
# 【L1565】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_joint_sequence`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `vstack` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `[target_lift_arm, *place_waypoints]`。
# 【项目含义】得到 `place_joint_sequence`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.vstack([target_lift_arm, *place_waypoints])`；`vstack` 表示本功能块中的 `vstack` 值；`target_lift_arm` 表示目标相关值；`place_waypoints` 表示本功能块中的 `place_waypoints` 值。
        place_joint_sequence = np.vstack([target_lift_arm, *place_waypoints])
# 【L1566】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_max_command_step_rad`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `place_max_command_step_rad`，它在本项目中表示控制命令、步相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
        place_max_command_step_rad = float(
# 【L1567】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `max` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.abs(np.diff(place_joint_sequence, axis=0))`。
# 【项目含义】调用 `np.diff`：计算相邻元素或相邻帧之差；本行实际操作 `np.max(np.abs(np.diff(place_joint_sequence, axis=0)))`。`abs` 表示本功能块中的 `abs` 值；`diff` 表示本功能块中的 `diff` 值。
            np.max(np.abs(np.diff(place_joint_sequence, axis=0)))
# 【L1568】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        )
# 【L1569】语法拆解：`if` 要求条件 `args.diagnose_kinematics_only` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.diagnose_kinematics_only` 是否成立；`diagnose_kinematics_only` 表示本功能块中的 `diagnose_kinematics_only` 值
    if args.diagnose_kinematics_only:
# 【L1570】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `diagnostic`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `diagnostic`，它在本项目中表示本功能块中的 `diagnostic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        diagnostic = {
# 【L1571】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"diagnostic"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"diagnostic"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "diagnostic",
# 【L1572】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L1573】语法拆解：这是字典键值对：`"robot_base_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`robot_base_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `robot_base_position_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L1574】语法拆解：这是字典键值对：`"transfer_joint_1_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1575】语法拆解：这是字典键值对：`"grasp_orientation_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_orientation_mode`。
# 【项目含义】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L1576】语法拆解：这是字典键值对：`"top_down_ik_seed_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`top_down_ik_seed_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L1577】语法拆解：这是字典键值对：`"requested_pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`requested_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L1578】语法拆解：这是字典键值对：`"pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`effective_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L1579】语法拆解：这是字典键值对：`"grasp_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`grasp_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `grasp_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `grasp_arm_joint_position_rad` 数据；字段值来自 `grasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_arm_joint_position_rad": grasp_arm.tolist(),
# 【L1580】语法拆解：这是字典键值对：`"lift_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lift_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `lift_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_arm_joint_position_rad": lift_arm.tolist(),
# 【L1581】语法拆解：这是字典键值对：`"target_lift_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_lift_arm_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `target_lift_arm_joint_position_rad` 数据；字段值来自 `target_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_lift_arm_joint_position_rad": target_lift_arm.tolist(),
# 【L1582】语法拆解：这是字典键值对：`"retreat_waypoint_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `retreat_waypoints`。
# 【项目含义】定义字典/JSON 字段 `retreat_waypoint_count`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_waypoint_count` 数据；字段值来自 `len(retreat_waypoints)`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_waypoint_count": len(retreat_waypoints),
# 【L1583】语法拆解：这是字典键值对：`"retreat_max_command_step_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`retreat_max_command_step_rad` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `retreat_max_command_step_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_max_command_step_rad` 数据；字段值来自 `retreat_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_max_command_step_rad": retreat_max_command_step_rad,
# 【L1584】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `retreat_waypoint_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `retreat_waypoint_joint_position_rad` 数据；字段值来自 `[`，因此保存/传递的是这个表达式当前计算出的结果。
            "retreat_waypoint_joint_position_rad": [
# 【L1585】语法拆解：`item.tolist() for item in retreat_waypoints` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是生成式/推导式 `item.tolist() for item in retreat_waypoints`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`item` 表示本功能块中的 `item` 值；`tolist` 表示本功能块中的 `tolist` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。产生的序列交给外层列表、字典或函数完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
                item.tolist() for item in retreat_waypoints
# 【L1586】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
            ],
# 【L1587】语法拆解：这是字典键值对：`"place_waypoint_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`len` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `place_waypoints`。
# 【项目含义】定义字典/JSON 字段 `place_waypoint_count`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_waypoint_count` 数据；字段值来自 `len(place_waypoints)`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_waypoint_count": len(place_waypoints),
# 【L1588】语法拆解：这是字典键值对：`"place_max_command_step_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`place_max_command_step_rad` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `place_max_command_step_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_max_command_step_rad` 数据；字段值来自 `place_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_max_command_step_rad": place_max_command_step_rad,
# 【L1589】语法拆解：这是字典键值对：`"place_ik_uses_base_rotation_symmetry"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_ik_uses_base_rotation_symmetry` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_ik_uses_base_rotation_symmetry": True,
# 【L1590】语法拆解：这是字典键值对：`"place_waypoint_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `place_waypoint_joint_position_rad`，它表示“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的 `place_waypoint_joint_position_rad` 数据；字段值来自 `[item.tolist() for item in place_waypoints]`，因此保存/传递的是这个表达式当前计算出的结果。
            "place_waypoint_joint_position_rad": [item.tolist() for item in place_waypoints],
# 【L1591】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
        }
# 【L1592】语法拆解：`output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L1593】语法拆解：`output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(diagnostic, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L1594】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(diagnostic, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(diagnostic, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”进度，也给日志留下可搜索证据。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L1595】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
        return 0
# 【L1596】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 14：创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器（源码第 1597-1795 行）

### 5.A 数据流位置

- 上游：模块 13“根据物体、末端姿态和 RM65 限位计算抓取/抬升/放置 IK”。
- 本模块：创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器。
- 下游：处理结果继续交给模块 15“reset、关节索引和 episode 记录器初始化”。

### 5.B 为什么需要这一组代码

这一组负责“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `gripper`：一个归一化夹爪值组成的一维数组。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `usd`：Isaac Sim 实际加载的 RM65+4C2 USD 资产路径。

### 5.D 本模块首次阅读要认识的调用

- `SimulationContext(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.SimulationCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.PhysxCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.RenderCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.RigidBodyMaterialCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `sim_utils.DomeLightCfg(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `light_cfg.func(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `spawn_platform(...)`：圆括号表示真正执行调用；在 Isaac 世界中创建源/目标支撑平台的刚体和碰撞几何。
- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `get_current_stage(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `Traverse(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `prim.GetPath(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 当前第 1601-1616 行相对旧教学快照发生 `insert`：旧版 0 行，当前 16 行。 当前代码摘录：`physx=sim_utils.PhysxCfg(` / `enable_enhanced_determinism=args.pi05_closed_loop,` / `),` / `render=sim_utils.RenderCfg(`

### 5.G 逐行精读

```python
# 【L1597】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim`。右侧语法为：`SimulationContext(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `sim`，它在本项目中表示IsaacLab SimulationContext，负责物理时间步；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `SimulationContext(`；`SimulationContext` 表示本功能块中的 `SimulationContext` 值。
    sim = SimulationContext(
# 【L1598】语法拆解：`sim_utils.SimulationCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `sim_utils` 调用多行方法 `SimulationCfg`：调用 `sim_utils` 提供的 `SimulationCfg` 操作；具体参数写在随后几行，用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        sim_utils.SimulationCfg(
# 【L1599】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dt`。右侧语法为：表达式 `1.0 / 240.0` 使用运算符 `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dt` 传入 `1.0 / 240.0`；该参数在本项目中表示本功能块中的 `dt` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dt=1.0 / 240.0,
# 【L1600】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `device`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`device`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `device` 传入 `args.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            device=args.device,
# 【L1601】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physx`。右侧语法为：`sim_utils.PhysxCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physx`，它在本项目中表示本功能块中的 `physx` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.PhysxCfg(`；`sim_utils` 表示仿真相关值；`PhysxCfg` 表示本功能块中的 `PhysxCfg` 值。
            physx=sim_utils.PhysxCfg(
# 【L1602】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `enable_enhanced_determinism`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `enable_enhanced_determinism` 传入 `args.pi05_closed_loop`；该参数在本项目中表示本功能块中的 `enable_enhanced_determinism` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                enable_enhanced_determinism=args.pi05_closed_loop,
# 【L1603】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1604】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `render`。右侧语法为：`sim_utils.RenderCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `render`，它在本项目中表示本功能块中的 `render` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RenderCfg(`；`sim_utils` 表示仿真相关值；`RenderCfg` 表示本功能块中的 `RenderCfg` 值。
            render=sim_utils.RenderCfg(
# 【L1605】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `antialiasing_mode`。右侧语法为：`"FXAA" if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `antialiasing_mode` 传入 `"FXAA" if args.pi05_closed_loop else None`；该参数在本项目中表示本功能块中的 `antialiasing_mode` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                antialiasing_mode="FXAA" if args.pi05_closed_loop else None,
# 【L1606】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `enable_dlssg`。右侧语法为：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `enable_dlssg` 传入 `False if args.pi05_closed_loop else None`；该参数在本项目中表示本功能块中的 `enable_dlssg` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                enable_dlssg=False if args.pi05_closed_loop else None,
# 【L1607】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `enable_dl_denoiser`。右侧语法为：`False if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `enable_dl_denoiser` 传入 `False if args.pi05_closed_loop else None`；该参数在本项目中表示本功能块中的 `enable_dl_denoiser` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                enable_dl_denoiser=False if args.pi05_closed_loop else None,
# 【L1608】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `carb_settings`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `carb_settings`，它在本项目中表示本功能块中的 `carb_settings` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
                carb_settings=(
# 【L1609】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    {
# 【L1610】语法拆解：这是字典键值对：`"/rtx/post/motionblur/enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `/rtx/post/motionblur/enabled`，它表示“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的 `/rtx/post/motionblur/enabled` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                        "/rtx/post/motionblur/enabled": False,
# 【L1611】语法拆解：这是字典键值对：`"/rtx/post/tvNoise/enabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `/rtx/post/tvNoise/enabled`，它表示“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的 `/rtx/post/tvNoise/enabled` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                        "/rtx/post/tvNoise/enabled": False,
# 【L1612】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    }
# 【L1613】语法拆解：`if` 要求条件 `args.pi05_closed_loop` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.pi05_closed_loop` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
                    if args.pi05_closed_loop
# 【L1614】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”在可选数据缺失时仍有明确结果。
                    else None
# 【L1615】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1616】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1617】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physics_material`。右侧语法为：`sim_utils.RigidBodyMaterialCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
            physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1618】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `static_friction`。右侧语法为：`1.5` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.5`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                static_friction=1.5,
# 【L1619】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dynamic_friction`。右侧语法为：`1.2` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `1.2`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                dynamic_friction=1.2,
# 【L1620】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `restitution`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                restitution=0.0,
# 【L1621】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `friction_combine_mode`。右侧语法为：`"max"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                friction_combine_mode="max",
# 【L1622】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1623】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1624】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1625】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `light_cfg`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `DomeLightCfg` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `intensity=2500.0`；第 2 个实参 `color=(0.8, 0.8, 0.8)`。
# 【项目含义】得到 `light_cfg`，它在本项目中表示本功能块中的 `light_cfg` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))`；`sim_utils` 表示仿真相关值；`DomeLightCfg` 表示本功能块中的 `DomeLightCfg` 值；`intensity` 表示本功能块中的 `intensity` 值。
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
# 【L1626】语法拆解：`light_cfg` 是模块/对象，点号 `.` 从中取出 `func` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"/World/Light"`；第 2 个实参 `light_cfg`。
# 【项目含义】对 `light_cfg` 调用 `func("/World/Light", light_cfg)`：调用 `light_cfg` 提供的 `func` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    light_cfg.func("/World/Light", light_cfg)
# 【L1627】语法拆解：`if` 要求条件 `not args.diagnose_approach_only` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.diagnose_approach_only` 是否成立；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值
    if not args.diagnose_approach_only:
# 【L1628】语法拆解：`spawn_platform(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `spawn_platform`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        spawn_platform(
# 【L1629】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/TargetPlatform"`；在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "/World/TargetPlatform",
# 【L1630】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_platform_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_platform_position`；在本项目中它表示目标、支撑平台、位置相关值。
            target_platform_position,
# 【L1631】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_platform_size` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_platform_size`；在本项目中它表示目标、支撑平台相关值。
            target_platform_size,
# 【L1632】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`(0.12, 0.45, 0.20),`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (0.12, 0.45, 0.20),
# 【L1633】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_platform_orientation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_platform_orientation`；在本项目中它表示目标、支撑平台相关值。
            target_platform_orientation,
# 【L1634】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1635】语法拆解：`if` 要求条件 `args.natural_source_gravity` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值
    if args.natural_source_gravity:
# 【L1636】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_platform_position`。右侧语法为：`np.array(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `source_platform_position`，它在本项目中表示源位置、支撑平台、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.array(`；`array` 表示本功能块中的 `array` 值。
        source_platform_position = np.array(
# 【L1637】语法拆解：`[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            [
# 【L1638】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`source_block_position[0]` 使用方括号索引；先计算 `0`，再从 `source_block_position` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `source_block_position[0]`；`source_block_position` 表示源位置、位置相关值，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[0],
# 【L1639】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`source_block_position[1]` 使用方括号索引；先计算 `1`，再从 `source_block_position` 取对应字典字段或数组元素。
# 【项目含义】向上一行的函数调用或容器继续传入 `source_block_position[1]`；`source_block_position` 表示源位置、位置相关值，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                source_block_position[1],
# 【L1640】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】向上一行的函数调用或容器继续传入 `SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0`；`SOURCE_PLATFORM_TOP_Z` 表示源位置方块/平台的任务常量；`SOURCE_PLATFORM_SIZE` 表示源位置方块/平台的任务常量，它参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0,
# 【L1641】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ],
# 【L1642】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`np` 是起始对象；每个点号 `.` 依次读取属性/成员：`float64`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `np.float64`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            dtype=np.float64,
# 【L1643】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1644】语法拆解：`spawn_platform(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `spawn_platform`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        spawn_platform(
# 【L1645】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供路径/资源标识 `"/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)`；在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，外层配置会沿这个位置加载基础 checkpoint、数据或资产。
            "/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)
# 【L1646】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1647】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_platform_collision_apis`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `target_platform_collision_apis`，它在本项目中表示目标、支撑平台相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    target_platform_collision_apis = []
# 【L1648】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1649】语法拆解：`if` 要求条件 `str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI)` 是否成立；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值；`startswith` 表示本功能块中的 `startswith` 值
        if str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1650】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collision_api`。右侧语法为：`UsdPhysics` 是模块/对象，点号 `.` 从中取出 `CollisionAPI` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prim`。
# 【项目含义】得到 `collision_api`，它在本项目中表示本功能块中的 `collision_api` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `UsdPhysics.CollisionAPI(prim)`；`UsdPhysics` 表示本功能块中的 `UsdPhysics` 值；`CollisionAPI` 表示本功能块中的 `CollisionAPI` 值；`prim` 表示本功能块中的 `prim` 值。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1651】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(False`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(False)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1652】语法拆解：`target_platform_collision_apis` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `collision_api`。
# 【项目含义】对 `target_platform_collision_apis` 执行 `append`，把 `collision_api` 加入已有结果；该集合表示目标、支撑平台相关值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            target_platform_collision_apis.append(collision_api)
# 【L1653】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1654】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `robot`。右侧语法为：`Articulation(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `robot`，它在本项目中表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Articulation(`；`Articulation` 表示本功能块中的 `Articulation` 值。
    robot = Articulation(
# 【L1655】语法拆解：`ArticulationCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `ArticulationCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ArticulationCfg(
# 【L1656】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prim_path`。右侧语法为：`"/World/Robot"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/Robot"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Robot",
# 【L1657】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `spawn`。右侧语法为：`sim_utils.UsdFileCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.UsdFileCfg(`；`sim_utils` 表示仿真相关值；`UsdFileCfg` 表示本功能块中的 `UsdFileCfg` 值。
            spawn=sim_utils.UsdFileCfg(
# 【L1658】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `usd_path`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `usd`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `usd_path` 传入 `str(usd)`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                usd_path=str(usd),
# 【L1659】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `activate_contact_sensors`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `activate_contact_sensors` 传入 `True`；该参数在本项目中表示接触相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                activate_contact_sensors=True,
# 【L1660】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rigid_props`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `RigidBodyPropertiesCfg` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `disable_gravity=False`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `rigid_props` 传入 `sim_utils.RigidBodyPropertiesCfg(disable_gravity=False)`；该参数在本项目中表示本功能块中的 `rigid_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
# 【L1661】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `articulation_props`。右侧语法为：`sim_utils.ArticulationRootPropertiesCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `articulation_props`，它在本项目中表示本功能块中的 `articulation_props` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.ArticulationRootPropertiesCfg(`；`sim_utils` 表示仿真相关值；`ArticulationRootPropertiesCfg` 表示本功能块中的 `ArticulationRootPropertiesCfg` 值。
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
# 【L1662】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `enabled_self_collisions`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `enabled_self_collisions` 传入 `False`；该参数在本项目中表示本功能块中的 `enabled_self_collisions` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    enabled_self_collisions=False,
# 【L1663】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `solver_position_iteration_count`。右侧语法为：`64` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `solver_position_iteration_count` 传入 `64`；该参数在本项目中表示位置、数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=64,
# 【L1664】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `solver_velocity_iteration_count`。右侧语法为：`4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `solver_velocity_iteration_count` 传入 `4`；该参数在本项目中表示数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1665】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1666】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1667】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `init_state`。右侧语法为：`ArticulationCfg.InitialStateCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `init_state`，它在本项目中表示状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ArticulationCfg.InitialStateCfg(`；`ArticulationCfg` 表示本功能块中的 `ArticulationCfg` 值；`InitialStateCfg` 表示本功能块中的 `InitialStateCfg` 值。
            init_state=ArticulationCfg.InitialStateCfg(
# 【L1668】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pos`。右侧语法为：`tuple` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot_base_position`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `pos` 传入 `tuple(robot_base_position)`；该参数在本项目中表示本功能块中的 `pos` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(robot_base_position),
# 【L1669】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_pos`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】给上一层函数/配置构造器的命名参数 `joint_pos` 传入 `{"joint_.*": 0.0, "tool_.*": 0.0}`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                joint_pos={"joint_.*": 0.0, "tool_.*": 0.0},
# 【L1670】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1671】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actuators`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actuators`，它在本项目中表示本功能块中的 `actuators` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            actuators={
# 【L1672】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `arm`，它表示“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的 `arm` 数据；字段值来自 `ImplicitActuatorCfg(`，因此保存/传递的是这个表达式当前计算出的结果。
                "arm": ImplicitActuatorCfg(
# 【L1673】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_names_expr`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `joint_names_expr` 传入 `["joint_[1-6]"]`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["joint_[1-6]"],
# 【L1674】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `effort_limit_sim`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_effort_limit_sim`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `effort_limit_sim` 传入 `args.arm_effort_limit_sim`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.arm_effort_limit_sim,
# 【L1675】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `velocity_limit_sim`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `velocity_limit_sim` 传入 `1.0`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1676】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stiffness`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_stiffness`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stiffness` 传入 `args.arm_stiffness`；该参数在本项目中表示本功能块中的 `stiffness` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.arm_stiffness,
# 【L1677】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `damping`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_damping`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `damping` 传入 `args.arm_damping`；该参数在本项目中表示本功能块中的 `damping` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.arm_damping,
# 【L1678】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1679】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper`，它表示LeRobot 一帧中的单个归一化 4C2 夹爪状态；字段值来自 `ImplicitActuatorCfg(`，因此保存/传递的是这个表达式当前计算出的结果。
                "gripper": ImplicitActuatorCfg(
# 【L1680】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_names_expr`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `joint_names_expr` 传入 `["tool_.*"]`；该参数在本项目中表示关节相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    joint_names_expr=["tool_.*"],
# 【L1681】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `effort_limit_sim`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_effort_limit_sim`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `effort_limit_sim` 传入 `args.gripper_effort_limit_sim`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    effort_limit_sim=args.gripper_effort_limit_sim,
# 【L1682】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `velocity_limit_sim`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `velocity_limit_sim` 传入 `1.0`；该参数在本项目中表示仿真相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    velocity_limit_sim=1.0,
# 【L1683】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stiffness`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_stiffness`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stiffness` 传入 `args.gripper_stiffness`；该参数在本项目中表示本功能块中的 `stiffness` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    stiffness=args.gripper_stiffness,
# 【L1684】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `damping`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_damping`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `damping` 传入 `args.gripper_damping`；该参数在本项目中表示本功能块中的 `damping` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    damping=args.gripper_damping,
# 【L1685】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1686】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            },
# 【L1687】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1688】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1689】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube`。右侧语法为：`RigidObject(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cube`，它在本项目中表示IsaacLab RigidObject；本任务被抓取和放置的方块；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RigidObject(`；`RigidObject` 表示本功能块中的 `RigidObject` 值。
    cube = RigidObject(
# 【L1690】语法拆解：`RigidObjectCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `RigidObjectCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        RigidObjectCfg(
# 【L1691】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prim_path`。右侧语法为：`"/World/Cube"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/Cube"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            prim_path="/World/Cube",
# 【L1692】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `spawn`。右侧语法为：`sim_utils.CuboidCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.CuboidCfg(`；`sim_utils` 表示仿真相关值；`CuboidCfg` 表示本功能块中的 `CuboidCfg` 值。
            spawn=sim_utils.CuboidCfg(
# 【L1693】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `size`。右侧语法为：`BLOCK_SIZE` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `size` 传入 `BLOCK_SIZE`；该参数在本项目中表示本功能块中的 `size` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                size=BLOCK_SIZE,
# 【L1694】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rigid_props`。右侧语法为：`sim_utils.RigidBodyPropertiesCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `rigid_props`，它在本项目中表示本功能块中的 `rigid_props` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyPropertiesCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyPropertiesCfg` 表示本功能块中的 `RigidBodyPropertiesCfg` 值。
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
# 【L1695】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `disable_gravity`。右侧语法为：`not args.natural_source_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `disable_gravity` 传入 `not args.natural_source_gravity`；该参数在本项目中表示本功能块中的 `disable_gravity` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    disable_gravity=not args.natural_source_gravity,
# 【L1696】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `solver_position_iteration_count`。右侧语法为：`32` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `solver_position_iteration_count` 传入 `32`；该参数在本项目中表示位置、数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_position_iteration_count=32,
# 【L1697】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `solver_velocity_iteration_count`。右侧语法为：`4` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `solver_velocity_iteration_count` 传入 `4`；该参数在本项目中表示数量相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    solver_velocity_iteration_count=4,
# 【L1698】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `max_depenetration_velocity`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `max_depenetration_velocity` 传入 `1.0`；该参数在本项目中表示本功能块中的 `max_depenetration_velocity` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    max_depenetration_velocity=1.0,
# 【L1699】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1700】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `mass_props`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `MassPropertiesCfg` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `mass=BLOCK_MASS_KG`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `mass_props` 传入 `sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG)`；该参数在本项目中表示本功能块中的 `mass_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                mass_props=sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG),
# 【L1701】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collision_props`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `CollisionPropertiesCfg` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】给上一层函数/配置构造器的命名参数 `collision_props` 传入 `sim_utils.CollisionPropertiesCfg()`；该参数在本项目中表示本功能块中的 `collision_props` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                collision_props=sim_utils.CollisionPropertiesCfg(),
# 【L1702】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `visual_material`。右侧语法为：`sim_utils` 是模块/对象，点号 `.` 从中取出 `PreviewSurfaceCfg` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `diffuse_color=(0.85, 0.10, 0.08)`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `visual_material` 传入 `sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08))`；该参数在本项目中表示本功能块中的 `visual_material` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
# 【L1703】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physics_material`。右侧语法为：`sim_utils.RigidBodyMaterialCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `physics_material`，它在本项目中表示本功能块中的 `physics_material` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.RigidBodyMaterialCfg(`；`sim_utils` 表示仿真相关值；`RigidBodyMaterialCfg` 表示本功能块中的 `RigidBodyMaterialCfg` 值。
                physics_material=sim_utils.RigidBodyMaterialCfg(
# 【L1704】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `static_friction`。右侧语法为：`1.5` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `static_friction` 传入 `1.5`；该参数在本项目中表示本功能块中的 `static_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    static_friction=1.5,
# 【L1705】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dynamic_friction`。右侧语法为：`1.2` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dynamic_friction` 传入 `1.2`；该参数在本项目中表示本功能块中的 `dynamic_friction` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    dynamic_friction=1.2,
# 【L1706】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `restitution`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `restitution` 传入 `0.0`；该参数在本项目中表示本功能块中的 `restitution` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    restitution=0.0,
# 【L1707】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `friction_combine_mode`。右侧语法为：`"max"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `friction_combine_mode` 传入 `"max"`；该参数在本项目中表示本功能块中的 `friction_combine_mode` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    friction_combine_mode="max",
# 【L1708】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1709】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1710】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `init_state`。右侧语法为：`RigidObjectCfg.InitialStateCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `init_state`，它在本项目中表示状态相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `RigidObjectCfg.InitialStateCfg(`；`RigidObjectCfg` 表示本功能块中的 `RigidObjectCfg` 值；`InitialStateCfg` 表示本功能块中的 `InitialStateCfg` 值。
            init_state=RigidObjectCfg.InitialStateCfg(
# 【L1711】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pos`。右侧语法为：`tuple` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `source_block_position`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `pos` 传入 `tuple(source_block_position)`；该参数在本项目中表示本功能块中的 `pos` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                pos=tuple(source_block_position),
# 【L1712】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rot`。右侧语法为：`tuple` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `source_block_quaternion`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `rot` 传入 `tuple(source_block_quaternion)`；该参数在本项目中表示本功能块中的 `rot` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                rot=tuple(source_block_quaternion),
# 【L1713】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            ),
# 【L1714】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1715】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1716】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_camera`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    external_camera = None
# 【L1717】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_camera`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    wrist_camera = None
# 【L1718】语法拆解：`if` 要求条件 `args.record_images` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
    if args.record_images:
# 【L1719】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_camera`。右侧语法为：`Camera(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `external_camera`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Camera(`；`Camera` 表示本功能块中的 `Camera` 值。
        external_camera = Camera(
# 【L1720】语法拆解：`CameraCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `CameraCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            CameraCfg(
# 【L1721】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prim_path`。右侧语法为：`"/World/ExternalCamera"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/ExternalCamera"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/ExternalCamera",
# 【L1722】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `update_period`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1723】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `height`。右侧语法为：`480` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `height` 传入 `480`；该参数在本项目中表示本功能块中的 `height` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1724】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `width`。右侧语法为：`640` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `width` 传入 `640`；该参数在本项目中表示本功能块中的 `width` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1725】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_types`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `data_types` 传入 `["rgb"]`；该参数在本项目中表示本功能块中的 `data_types` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1726】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `spawn`。右侧语法为：`sim_utils.PinholeCameraCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.PinholeCameraCfg(`；`sim_utils` 表示仿真相关值；`PinholeCameraCfg` 表示本功能块中的 `PinholeCameraCfg` 值。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1727】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `focal_length`。右侧语法为：`24.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `focal_length` 传入 `24.0`；该参数在本项目中表示本功能块中的 `focal_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=24.0,
# 【L1728】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `focus_distance`。右侧语法为：`2.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `focus_distance` 传入 `2.0`；该参数在本项目中表示本功能块中的 `focus_distance` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=2.0,
# 【L1729】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `horizontal_aperture`。右侧语法为：`20.955` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `horizontal_aperture` 传入 `20.955`；该参数在本项目中表示本功能块中的 `horizontal_aperture` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1730】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `clipping_range`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `clipping_range` 传入 `(0.01, 10.0)`；该参数在本项目中表示本功能块中的 `clipping_range` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1731】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1732】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1733】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1734】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_camera`。右侧语法为：`Camera(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `wrist_camera`，它在本项目中表示腕部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Camera(`；`Camera` 表示本功能块中的 `Camera` 值。
        wrist_camera = Camera(
# 【L1735】语法拆解：`CameraCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `CameraCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            CameraCfg(
# 【L1736】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prim_path`。右侧语法为：`"/World/WristCamera"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `"/World/WristCamera"`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                prim_path="/World/WristCamera",
# 【L1737】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `update_period`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                update_period=0.0,
# 【L1738】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `height`。右侧语法为：`480` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `height` 传入 `480`；该参数在本项目中表示本功能块中的 `height` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                height=480,
# 【L1739】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `width`。右侧语法为：`640` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `width` 传入 `640`；该参数在本项目中表示本功能块中的 `width` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                width=640,
# 【L1740】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `data_types`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `data_types` 传入 `["rgb"]`；该参数在本项目中表示本功能块中的 `data_types` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                data_types=["rgb"],
# 【L1741】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `spawn`。右侧语法为：`sim_utils.PinholeCameraCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `spawn`，它在本项目中表示本功能块中的 `spawn` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sim_utils.PinholeCameraCfg(`；`sim_utils` 表示仿真相关值；`PinholeCameraCfg` 表示本功能块中的 `PinholeCameraCfg` 值。
                spawn=sim_utils.PinholeCameraCfg(
# 【L1742】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `focal_length`。右侧语法为：`18.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `focal_length` 传入 `18.0`；该参数在本项目中表示本功能块中的 `focal_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focal_length=18.0,
# 【L1743】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `focus_distance`。右侧语法为：`1.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `focus_distance` 传入 `1.0`；该参数在本项目中表示本功能块中的 `focus_distance` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    focus_distance=1.0,
# 【L1744】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `horizontal_aperture`。右侧语法为：`20.955` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `horizontal_aperture` 传入 `20.955`；该参数在本项目中表示本功能块中的 `horizontal_aperture` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    horizontal_aperture=20.955,
# 【L1745】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `clipping_range`。右侧语法为：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】给上一层函数/配置构造器的命名参数 `clipping_range` 传入 `(0.01, 10.0)`；该参数在本项目中表示本功能块中的 `clipping_range` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    clipping_range=(0.01, 10.0),
# 【L1746】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ),
# 【L1747】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1748】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        )
# 【L1749】语法拆解：`PhysxSchema.PhysxContactReportAPI` 是模块/对象，点号 `.` 从中取出 `Apply` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `get_current_stage().GetPrimAtPath("/World/Cube")`。
# 【项目含义】调用 `Path`：创建路径对象；本行实际操作 `PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))`。`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxContactReportAPI` 表示本功能块中的 `PhysxContactReportAPI` 值。
    PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))
# 【L1750】语法拆解：`CONTACT_SENSORS.update(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `CONTACT_SENSORS` 调用多行方法 `update`：用当前仿真步的新数据刷新对象或字典，保证后续判断读取的是最新状态；具体参数写在随后几行，用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    CONTACT_SENSORS.update(
# 【L1751】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        {
# 【L1752】语法拆解：表达式 `body_path.rsplit("/", 1)[-1]: ContactSensor(` 使用运算符 `-`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `body_path.rsplit("/", 1)[-1]: ContactSensor(` 接入当前完整语句；`body_path` 表示刚体、路径相关值；`rsplit` 表示本功能块中的 `rsplit` 值；`ContactSensor` 表示本功能块中的 `ContactSensor` 值。在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            body_path.rsplit("/", 1)[-1]: ContactSensor(
# 【L1753】语法拆解：`ContactSensorCfg(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `ContactSensorCfg`；随后几行会逐项给它参数，调用结果或副作用用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                ContactSensorCfg(
# 【L1754】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prim_path`。右侧语法为：`body_path` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prim_path` 传入 `body_path`；该参数在本项目中表示路径相关值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    prim_path=body_path,
# 【L1755】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `update_period`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `update_period` 传入 `0.0`；该参数在本项目中表示本功能块中的 `update_period` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    update_period=0.0,
# 【L1756】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `history_length`。右侧语法为：`400` 是直接写在源码中的数值常量。
# 【项目含义】给上一层函数/配置构造器的命名参数 `history_length` 传入 `400`；该参数在本项目中表示本功能块中的 `history_length` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    history_length=400,
# 【L1757】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `filter_prim_paths_expr`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】给上一层函数/配置构造器的命名参数 `filter_prim_paths_expr` 传入 `["/World/Cube"]`；该参数在本项目中表示本功能块中的 `filter_prim_paths_expr` 值，会参与“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                    filter_prim_paths_expr=["/World/Cube"],
# 【L1758】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                )
# 【L1759】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            )
# 【L1760】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)` 中给出的序列，逐项完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)
# 【L1761】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        }
# 【L1762】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    )
# 【L1763】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

# 【L1764】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `isolated_paths`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `isolated_paths`，它在本项目中表示本功能块中的 `isolated_paths` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    isolated_paths = []
# 【L1765】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `approach_arm_gravity_apis`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `approach_arm_gravity_apis`，它在本项目中表示本功能块中的 `approach_arm_gravity_apis` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    approach_arm_gravity_apis = []
# 【L1766】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1767】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `path`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prim.GetPath()`。
# 【项目含义】得到 `path`，它在本项目中表示路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `str(prim.GetPath())`；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值。
        path = str(prim.GetPath())
# 【L1768】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
        if (
# 【L1769】语法拆解：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`(args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)`；`disable_arm_gravity_during_approach` 表示本功能块中的 `disable_arm_gravity_during_approach` 值；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值，共同完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            (args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)
# 【L1770】语法拆解：`and path in ARM_BODY_PATHS` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `path in ARM_BODY_PATHS` 用“并且”接到上一行判断中；判断 `path in ARM_BODY_PATHS` 是否成立；`path` 表示路径相关值；`ARM_BODY_PATHS` 表示刚体相关值。所有连接条件共同决定是否进入后续分支。
            and path in ARM_BODY_PATHS
# 【L1771】语法拆解：`and prim.HasAPI(UsdPhysics.RigidBodyAPI)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `and prim` 调用 `HasAPI(UsdPhysics.RigidBodyAPI)`：调用 `and prim` 提供的 `HasAPI` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1772】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1773】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `rigid_body_api`。右侧语法为：`PhysxSchema.PhysxRigidBodyAPI` 是模块/对象，点号 `.` 从中取出 `Apply` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prim`。
# 【项目含义】得到 `rigid_body_api`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PhysxSchema.PhysxRigidBodyAPI.Apply(prim)`；`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxRigidBodyAPI` 表示本功能块中的 `PhysxRigidBodyAPI` 值；`Apply` 表示本功能块中的 `Apply` 值。
            rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
# 【L1774】语法拆解：`rigid_body_api` 是模块/对象，点号 `.` 从中取出 `CreateDisableGravityAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(True`。
# 【项目含义】对 `rigid_body_api` 调用 `CreateDisableGravityAttr().Set(True)`：调用 `rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            rigid_body_api.CreateDisableGravityAttr().Set(True)
# 【L1775】语法拆解：`approach_arm_gravity_apis` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `rigid_body_api`。
# 【项目含义】对 `approach_arm_gravity_apis` 执行 `append`，把 `rigid_body_api` 加入已有结果；该集合表示本功能块中的 `approach_arm_gravity_apis` 值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            approach_arm_gravity_apis.append(rigid_body_api)
# 【L1776】语法拆解：`if` 要求条件 `(` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `(` 是否成立；成立时执行紧随其后的缩进代码
        if (
# 【L1777】语法拆解：`not args.enable_moving_gripper_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `not args.enable_moving_gripper_gravity` 接入当前完整语句；`enable_moving_gripper_gravity` 表示夹爪相关值。在“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            not args.enable_moving_gripper_gravity
# 【L1778】语法拆解：`and path in MOVING_GRIPPER_BODY_PATHS` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `path in MOVING_GRIPPER_BODY_PATHS` 用“并且”接到上一行判断中；判断 `path in MOVING_GRIPPER_BODY_PATHS` 是否成立；`path` 表示路径相关值；`MOVING_GRIPPER_BODY_PATHS` 表示夹爪、刚体相关值。所有连接条件共同决定是否进入后续分支。
            and path in MOVING_GRIPPER_BODY_PATHS
# 【L1779】语法拆解：`and prim.HasAPI(UsdPhysics.RigidBodyAPI)` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `and prim` 调用 `HasAPI(UsdPhysics.RigidBodyAPI)`：调用 `and prim` 提供的 `HasAPI` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
# 【L1780】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】以 `):` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
        ):
# 【L1781】语法拆解：`PhysxSchema.PhysxRigidBodyAPI` 是模块/对象，点号 `.` 从中取出 `Apply` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prim).CreateDisableGravityAttr().Set(True`。
# 【项目含义】对 `PhysxSchema.PhysxRigidBodyAPI` 调用 `Apply(prim).CreateDisableGravityAttr().Set(True)`：调用 `PhysxSchema.PhysxRigidBodyAPI` 提供的 `Apply` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
# 【L1782】语法拆解：`isolated_paths` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `path`。
# 【项目含义】对 `isolated_paths` 执行 `append`，把 `path` 加入已有结果；该集合表示本功能块中的 `isolated_paths` 值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            isolated_paths.append(path)
# 【L1783】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_prim`。右侧语法为：`get_current_stage` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).GetPrimAtPath("/World/Cube"`。
# 【项目含义】得到 `cube_prim`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `get_current_stage().GetPrimAtPath("/World/Cube")`；`get_current_stage` 表示当前值相关值；`GetPrimAtPath` 表示本功能块中的 `GetPrimAtPath` 值；`World` 表示本功能块中的 `World` 值。
    cube_prim = get_current_stage().GetPrimAtPath("/World/Cube")
# 【L1784】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_rigid_body_api`。右侧语法为：`PhysxSchema.PhysxRigidBodyAPI` 是模块/对象，点号 `.` 从中取出 `Apply` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube_prim`。
# 【项目含义】得到 `cube_rigid_body_api`，它在本项目中表示任务方块、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)`；`PhysxSchema` 表示本功能块中的 `PhysxSchema` 值；`PhysxRigidBodyAPI` 表示本功能块中的 `PhysxRigidBodyAPI` 值；`Apply` 表示本功能块中的 `Apply` 值。
    cube_rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)
# 【L1785】语法拆解：`cube_rigid_body_api` 是模块/对象，点号 `.` 从中取出 `CreateDisableGravityAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(not args.natural_source_gravity`。
# 【项目含义】对 `cube_rigid_body_api` 调用 `CreateDisableGravityAttr().Set(not args.natural_source_gravity)`：调用 `cube_rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(not args.natural_source_gravity)
# 【L1786】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_collision_apis`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `cube_collision_apis`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    cube_collision_apis = []
# 【L1787】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `get_current_stage().Traverse()`，每次把当前元素放进 `prim`；这会逐个处理“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”所需的帧、episode、动作或实验 case。
    for prim in get_current_stage().Traverse():
# 【L1788】语法拆解：`if` 要求条件 `str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI)` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI)` 是否成立；`prim` 表示本功能块中的 `prim` 值；`GetPath` 表示本功能块中的 `GetPath` 值；`startswith` 表示本功能块中的 `startswith` 值
        if str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI):
# 【L1789】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `collision_api`。右侧语法为：`UsdPhysics` 是模块/对象，点号 `.` 从中取出 `CollisionAPI` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `prim`。
# 【项目含义】得到 `collision_api`，它在本项目中表示本功能块中的 `collision_api` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `UsdPhysics.CollisionAPI(prim)`；`UsdPhysics` 表示本功能块中的 `UsdPhysics` 值；`CollisionAPI` 表示本功能块中的 `CollisionAPI` 值；`prim` 表示本功能块中的 `prim` 值。
            collision_api = UsdPhysics.CollisionAPI(prim)
# 【L1790】语法拆解：`cube_collision_apis` 是模块/对象，点号 `.` 从中取出 `append` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `collision_api`。
# 【项目含义】对 `cube_collision_apis` 执行 `append`，把 `collision_api` 加入已有结果；该集合表示任务方块相关值，随后会用于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
            cube_collision_apis.append(collision_api)
# 【L1791】语法拆解：`if` 要求条件 `args.collision_bypass_during_approach` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
            if args.collision_bypass_during_approach:
# 【L1792】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(False`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(False)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
                collision_api.CreateCollisionEnabledAttr().Set(False)
# 【L1793】语法拆解：`if` 要求条件 `not cube_collision_apis` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not cube_collision_apis` 是否成立；`cube_collision_apis` 表示任务方块相关值
    if not cube_collision_apis:
# 【L1794】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError("no CollisionAPI prim found below /World/Cube")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError("no CollisionAPI prim found below /World/Cube")` 并停止当前路径；说明当前输入违反“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError("no CollisionAPI prim found below /World/Cube")
# 【L1795】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 15：reset、关节索引和 episode 记录器初始化（源码第 1796-1862 行）

### 5.A 数据流位置

- 上游：模块 14“创建 IsaacLab 物理世界、机器人、方块、相机和接触传感器”。
- 本模块：reset、关节索引和 episode 记录器初始化。
- 下游：处理结果继续交给模块 16“写入初始状态；选择脚本专家或 π0.5 分支”。

### 5.B 为什么需要这一组代码

这一组负责“reset、关节索引和 episode 记录器初始化”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `episode_recorder`：把同步帧保存在内存并最终写盘的记录器。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `gripper`：一个归一化夹爪值组成的一维数组。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `record_stride_steps`：每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长。
- `episode_prompt`：当前 episode 发送给 π0.5 的自然语言任务指令。

### 5.D 本模块首次阅读要认识的调用

- `sim.reset(...)`：圆括号表示真正执行调用；把仿真对象或缓冲区重置到 episode 初始状态。
- `robot.reset(...)`：圆括号表示真正执行调用；把仿真对象或缓冲区重置到 episode 初始状态。
- `cube.reset(...)`：圆括号表示真正执行调用；把仿真对象或缓冲区重置到 episode 初始状态。
- `torch.as_tensor(...)`：圆括号表示真正执行调用；把 NumPy/列表转换成指定设备和类型的 Torch 张量。
- `np.array(...)`：圆括号表示真正执行调用；创建 NumPy 数组。
- `unsqueeze(...)`：圆括号表示真正执行调用；在指定位置增加一个长度为 1 的维度，常把单个样本变成 batch。
- `external_camera.set_world_poses_from_view(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `joint_names.index(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `name.startswith(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `RuntimeError(...)`：圆括号表示真正执行调用；创建“运行过程无法继续”的异常；配合 raise 把失败原因交给上层。
- `EpisodeRecorder(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。

### 5.F 这一模块的版本变化

- 当前第 1831-1834 行相对旧教学快照发生 `insert`：旧版 0 行，当前 4 行。 当前代码摘录：`"policy_noise_seed": (` / `args.policy_noise_seed if args.pi05_closed_loop else None` / `),` / `"simulation_seed": CONFIGURED_SIMULATION_SEED,`
- 当前第 1857-1859 行相对旧教学快照发生 `insert`：旧版 0 行，当前 3 行。 当前代码摘录：`),` / `reset_renderer_accumulation=(` / `args.reset_renderer_accumulation_before_policy_observation`

### 5.G 逐行精读

```python
# 【L1796】语法拆解：`sim` 是模块/对象，点号 `.` 从中取出 `reset` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `sim` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    sim.reset()
# 【L1797】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `reset` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `robot` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    robot.reset()
# 【L1798】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `reset` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `cube` 调用 `reset()`：把仿真对象或缓冲区重置到 episode 初始状态。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
    cube.reset()
# 【L1799】语法拆解：`if` 要求条件 `external_camera is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `external_camera is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if external_camera is not None:
# 【L1800】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `scene_center`。右侧语法为：表达式 `0.5 * (source_block_position + target_block_position)` 使用运算符 `+`, `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `scene_center`，它在本项目中表示本功能块中的 `scene_center` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `0.5 * (source_block_position + target_block_position)`；`source_block_position` 表示源位置、位置相关值；`target_block_position` 表示目标、位置相关值。
        scene_center = 0.5 * (source_block_position + target_block_position)
# 【L1801】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_eye`。右侧语法为：`torch.as_tensor(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `external_eye`，它在本项目中表示外部相机相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
        external_eye = torch.as_tensor(
# 【L1802】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：表达式 `scene_center + np.array([0.70, 0.70, 0.45])` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `np.array`：创建 NumPy 数组；本行实际操作 `scene_center + np.array([0.70, 0.70, 0.45]),`。`scene_center` 表示本功能块中的 `scene_center` 值；`array` 表示本功能块中的 `array` 值。
            scene_center + np.array([0.70, 0.70, 0.45]),
# 【L1803】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `device`。右侧语法为：`sim` 是起始对象；每个点号 `.` 依次读取属性/成员：`device`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `device` 传入 `sim.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1804】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`torch` 是起始对象；每个点号 `.` 依次读取属性/成员：`float32`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `torch.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1805】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `unsqueeze(0)`：调用 `)` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        ).unsqueeze(0)
# 【L1806】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_target`。右侧语法为：`torch.as_tensor(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `external_target`，它在本项目中表示外部相机、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
        external_target = torch.as_tensor(
# 【L1807】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`scene_center` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `scene_center`；在本项目中它表示本功能块中的 `scene_center` 值。
            scene_center,
# 【L1808】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `device`。右侧语法为：`sim` 是起始对象；每个点号 `.` 依次读取属性/成员：`device`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `device` 传入 `sim.device`；该参数在本项目中表示本功能块中的 `device` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            device=sim.device,
# 【L1809】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `dtype`。右侧语法为：`torch` 是起始对象；每个点号 `.` 依次读取属性/成员：`float32`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `dtype` 传入 `torch.float32`；该参数在本项目中表示本功能块中的 `dtype` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            dtype=torch.float32,
# 【L1810】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `unsqueeze(0)`：调用 `)` 提供的 `unsqueeze` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        ).unsqueeze(0)
# 【L1811】语法拆解：`external_camera` 是模块/对象，点号 `.` 从中取出 `set_world_poses_from_view` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `external_eye`；第 2 个实参 `external_target`。
# 【项目含义】对 `external_camera` 调用 `set_world_poses_from_view(external_eye, external_target)`：调用 `external_camera` 提供的 `set_world_poses_from_view` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
        external_camera.set_world_poses_from_view(external_eye, external_target)
# 【L1812】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `joint_names`。右侧语法为：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_names`。
# 【项目含义】得到 `joint_names`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(robot.data.joint_names)`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`joint_names` 表示关节相关值。
    joint_names = list(robot.data.joint_names)
# 【L1813】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `arm_ids`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `arm_ids`，它在本项目中表示本功能块中的 `arm_ids` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[joint_names.index(name) for name in ARM_JOINTS]`；`joint_names` 表示关节相关值；`index` 表示索引相关值；`name` 表示本功能块中的 `name` 值。
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
# 【L1814】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_ids`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `gripper_ids`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[index for index, name in enumerate(joint_names) if name.startswith("tool_")]`；`index` 表示索引相关值；`name` 表示本功能块中的 `name` 值；`enumerate` 表示本功能块中的 `enumerate` 值。
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
# 【L1815】语法拆解：`if` 要求条件 `GRIPPER_MASTER_JOINT not in joint_names` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `GRIPPER_MASTER_JOINT not in joint_names` 是否成立；`GRIPPER_MASTER_JOINT` 表示夹爪、关节相关值；`joint_names` 表示关节相关值
    if GRIPPER_MASTER_JOINT not in joint_names:
# 【L1816】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")` 并停止当前路径；说明当前输入违反“reset、关节索引和 episode 记录器初始化”要求，不能继续进入仿真、训练或评测。
        raise RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")
# 【L1817】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `episode_recorder`，它在本项目中表示把同步帧保存在内存并最终写盘的记录器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    episode_recorder = None
# 【L1818】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_capture`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `episode_capture`，它在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    episode_capture = None
# 【L1819】语法拆解：`if` 要求条件 `args.record_episode_dir is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `args.record_episode_dir is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if args.record_episode_dir is not None:
# 【L1820】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder`。右侧语法为：`EpisodeRecorder(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episode_recorder`，它在本项目中表示把同步帧保存在内存并最终写盘的记录器；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `EpisodeRecorder(`；`EpisodeRecorder` 表示本功能块中的 `EpisodeRecorder` 值。
        episode_recorder = EpisodeRecorder(
# 【L1821】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output_dir`。右侧语法为：`args.record_episode_dir` 是模块/对象，点号 `.` 从中取出 `expanduser` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).resolve(`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `output_dir` 传入 `args.record_episode_dir.expanduser().resolve()`；该参数在本项目中表示输出相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            output_dir=args.record_episode_dir.expanduser().resolve(),
# 【L1822】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prompt`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`episode_prompt`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prompt` 传入 `args.episode_prompt`；该参数在本项目中表示本功能块中的 `prompt` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            prompt=args.episode_prompt,
# 【L1823】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `control_hz`。右侧语法为：表达式 `1.0 / (sim.get_physics_dt() * args.record_stride_steps)` 使用运算符 `*`, `/`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】给上一层函数/配置构造器的命名参数 `control_hz` 传入 `1.0 / (sim.get_physics_dt() * args.record_stride_steps)`；该参数在本项目中表示本功能块中的 `control_hz` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            control_hz=1.0 / (sim.get_physics_dt() * args.record_stride_steps),
# 【L1824】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `metadata`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `metadata`，它在本项目中表示描述 episode、数据来源或 policy server 的机器可读元信息；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            metadata={
# 【L1825】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
                "simulation_only": True,
# 【L1826】语法拆解：这是字典键值对：`"expert"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`None if args.pi05_closed_loop else "scripted_rm65_pick_place"` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `expert`，它表示“reset、关节索引和 episode 记录器初始化”中的 `expert` 数据；字段值来自 `None if args.pi05_closed_loop else "scripted_rm65_pick_place"`，因此保存/传递的是这个表达式当前计算出的结果。
                "expert": None if args.pi05_closed_loop else "scripted_rm65_pick_place",
# 【L1827】语法拆解：这是字典键值对：`"pi05_used"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】定义字典/JSON 字段 `pi05_used`，它表示“reset、关节索引和 episode 记录器初始化”中的 `pi05_used` 数据；字段值来自 `args.pi05_closed_loop`，因此保存/传递的是这个表达式当前计算出的结果。
                "pi05_used": args.pi05_closed_loop,
# 【L1828】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `policy_checkpoint_id`，它表示生成动作的 checkpoint 标识，用来阻止混用旧报告；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
                "policy_checkpoint_id": (
# 【L1829】语法拆解：`args.policy_checkpoint_id if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `args.policy_checkpoint_id if args.pi05_closed_loop else None` 接入当前完整语句；`policy_checkpoint_id` 表示策略、模型检查点相关值；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值。在“reset、关节索引和 episode 记录器初始化”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    args.policy_checkpoint_id if args.pi05_closed_loop else None
# 【L1830】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
                ),
# 【L1831】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `policy_noise_seed`，它表示“reset、关节索引和 episode 记录器初始化”中的 `policy_noise_seed` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
                "policy_noise_seed": (
# 【L1832】语法拆解：`args.policy_noise_seed if args.pi05_closed_loop else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `args.policy_noise_seed if args.pi05_closed_loop else None` 接入当前完整语句；`policy_noise_seed` 表示策略相关值；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值。在“reset、关节索引和 episode 记录器初始化”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                    args.policy_noise_seed if args.pi05_closed_loop else None
# 【L1833】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
                ),
# 【L1834】语法拆解：这是字典键值对：`"simulation_seed"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`CONFIGURED_SIMULATION_SEED` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `simulation_seed`，它表示“reset、关节索引和 episode 记录器初始化”中的 `simulation_seed` 数据；字段值来自 `CONFIGURED_SIMULATION_SEED`，因此保存/传递的是这个表达式当前计算出的结果。
                "simulation_seed": CONFIGURED_SIMULATION_SEED,
# 【L1835】语法拆解：这是字典键值对：`"images_recorded"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_images`。
# 【项目含义】定义字典/JSON 字段 `images_recorded`，它表示“reset、关节索引和 episode 记录器初始化”中的 `images_recorded` 数据；字段值来自 `args.record_images`，因此保存/传递的是这个表达式当前计算出的结果。
                "images_recorded": args.record_images,
# 【L1836】语法拆解：这是字典键值对：`"robot_base_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`robot_base_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `robot_base_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "robot_base_position_m": robot_base_position.tolist(),
# 【L1837】语法拆解：这是字典键值对：`"source_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `source_block_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `source_block_position_m` 数据；字段值来自 `source_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "source_block_position_m": source_block_position.tolist(),
# 【L1838】语法拆解：这是字典键值对：`"source_offset_xy_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `source_offset_xy_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `source_offset_xy_m` 数据；字段值来自 `[args.source_offset_x_m, args.source_offset_y_m]`，因此保存/传递的是这个表达式当前计算出的结果。
                "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L1839】语法拆解：这是字典键值对：`"target_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_block_position_m`，它表示“reset、关节索引和 episode 记录器初始化”中的 `target_block_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "target_block_position_m": target_block_position.tolist(),
# 【L1840】语法拆解：这是字典键值对：`"transfer_joint_1_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“reset、关节索引和 episode 记录器初始化”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L1841】语法拆解：这是字典键值对：`"record_stride_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_stride_steps`。
# 【项目含义】定义字典/JSON 字段 `record_stride_steps`，它表示“reset、关节索引和 episode 记录器初始化”中的 `record_stride_steps` 数据；字段值来自 `args.record_stride_steps`，因此保存/传递的是这个表达式当前计算出的结果。
                "record_stride_steps": args.record_stride_steps,
# 【L1842】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            },
# 【L1843】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1844】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_capture`。右侧语法为：`ExpertEpisodeCapture(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episode_capture`，它在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ExpertEpisodeCapture(`；`ExpertEpisodeCapture` 表示本功能块中的 `ExpertEpisodeCapture` 值。
        episode_capture = ExpertEpisodeCapture(
# 【L1845】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `recorder`。右侧语法为：`episode_recorder` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `recorder` 传入 `episode_recorder`；该参数在本项目中表示本功能块中的 `recorder` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            recorder=episode_recorder,
# 【L1846】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `arm_ids`。右侧语法为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `arm_ids` 传入 `arm_ids`；该参数在本项目中表示本功能块中的 `arm_ids` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            arm_ids=arm_ids,
# 【L1847】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_master_id`。右侧语法为：`joint_names` 是模块/对象，点号 `.` 从中取出 `index` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `GRIPPER_MASTER_JOINT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `gripper_master_id` 传入 `joint_names.index(GRIPPER_MASTER_JOINT)`；该参数在本项目中表示夹爪相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1848】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `stride_steps`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_stride_steps`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `stride_steps` 传入 `args.record_stride_steps`；该参数在本项目中表示步数相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            stride_steps=args.record_stride_steps,
# 【L1849】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `physics_dt`。右侧语法为：`sim` 是模块/对象，点号 `.` 从中取出 `get_physics_dt` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】给上一层函数/配置构造器的命名参数 `physics_dt` 传入 `sim.get_physics_dt()`；该参数在本项目中表示本功能块中的 `physics_dt` 值，会参与“reset、关节索引和 episode 记录器初始化”。
            physics_dt=sim.get_physics_dt(),
# 【L1850】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim`。右侧语法为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `sim` 传入 `sim`；该参数在本项目中表示IsaacLab SimulationContext，负责物理时间步，会参与“reset、关节索引和 episode 记录器初始化”。
            sim=sim,
# 【L1851】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `external_camera`。右侧语法为：`external_camera` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `external_camera` 传入 `external_camera`；该参数在本项目中表示外部相机相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            external_camera=external_camera,
# 【L1852】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_camera`。右侧语法为：`wrist_camera` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `wrist_camera` 传入 `wrist_camera`；该参数在本项目中表示腕部相机相关值，会参与“reset、关节索引和 episode 记录器初始化”。
            wrist_camera=wrist_camera,
# 【L1853】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `wrist_tool_body_id`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `wrist_tool_body_id`，它在本项目中表示腕部相机、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            wrist_tool_body_id=(
# 【L1854】语法拆解：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.body_names).index("tool_base_link"`。
# 【项目含义】对 `list(robot.data.body_names)` 调用 `index("tool_base_link")`：调用 `list(robot.data.body_names)` 提供的 `index` 操作。本行产生的修改/返回值服务于“reset、关节索引和 episode 记录器初始化”。
                list(robot.data.body_names).index("tool_base_link")
# 【L1855】语法拆解：`if` 要求条件 `args.record_images` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
                if args.record_images
# 【L1856】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“reset、关节索引和 episode 记录器初始化”在可选数据缺失时仍有明确结果。
                else None
# 【L1857】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            ),
# 【L1858】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `reset_renderer_accumulation`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `reset_renderer_accumulation`，它在本项目中表示本功能块中的 `reset_renderer_accumulation` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
            reset_renderer_accumulation=(
# 【L1859】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`reset_renderer_accumulation_before_policy_observation`。
# 【项目含义】把表达式/参数 `args.reset_renderer_accumulation_before_policy_observation` 接入当前完整语句；`reset_renderer_accumulation_before_policy_observation` 表示策略相关值。在“reset、关节索引和 episode 记录器初始化”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                args.reset_renderer_accumulation_before_policy_observation
# 【L1860】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
            ),
# 【L1861】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“reset、关节索引和 episode 记录器初始化”。
        )
# 【L1862】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“reset、关节索引和 episode 记录器初始化”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“reset、关节索引和 episode 记录器初始化”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 16：写入初始状态；选择脚本专家或 π0.5 分支（源码第 1863-1905 行）

### 5.A 数据流位置

- 上游：模块 15“reset、关节索引和 episode 记录器初始化”。
- 本模块：写入初始状态；选择脚本专家或 π0.5 分支。
- 下游：处理结果继续交给模块 17“脚本专家的接近、闭合夹爪和接触诊断”。

### 5.B 为什么需要这一组代码

这一组负责“写入初始状态；选择脚本专家或 π0.5 分支”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `episode_recorder`：把同步帧保存在内存并最终写盘的记录器。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `output`：输出文件路径。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。

### 5.D 本模块首次阅读要认识的调用

- `robot.data.default_joint_pos.clone(...)`：圆括号表示真正执行调用；复制 Torch 张量，避免后续原地修改共享同一块数据。
- `torch.as_tensor(...)`：圆括号表示真正执行调用；把 NumPy/列表转换成指定设备和类型的 Torch 张量。
- `robot.write_joint_state_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `torch.zeros_like(...)`：圆括号表示真正执行调用；PyTorch 的 `zeros_like` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `clone(...)`：圆括号表示真正执行调用；复制 Torch 张量，避免后续原地修改共享同一块数据。
- `cube.write_root_pose_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `cube.write_root_velocity_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `hold(...)`：圆括号表示真正执行调用；保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。
- `run_pi05_closed_loop(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `joint_names.index(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L1863】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state`。右侧语法为：`robot.data.default_joint_pos` 是模块/对象，点号 `.` 从中取出 `clone` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `state`，它在本项目中表示当前要写给 articulation 的全部关节目标张量；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `robot.data.default_joint_pos.clone()`；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`default_joint_pos` 表示关节相关值。
    state = robot.data.default_joint_pos.clone()
# 【L1864】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, arm_ids]`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `as_tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `pregrasp_arm`；第 2 个实参 `device=sim.device`；第 3 个实参 `dtype=state.dtype`。
# 【项目含义】把右侧结果写进 `state[:, arm_ids]`（写入 `state[:, arm_ids]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`pregrasp_arm` 表示本功能块中的 `pregrasp_arm` 值；`device` 表示本功能块中的 `device` 值。
    state[:, arm_ids] = torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)
# 【L1865】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state[:, gripper_ids]`。右侧语法为：`0.0` 是直接写在源码中的数值常量。
# 【项目含义】把右侧结果写进 `state[:, gripper_ids]`（写入 `state[:, gripper_ids]` 指定的字段）；右侧具体做的是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
    state[:, gripper_ids] = 0.0
# 【L1866】语法拆解：`robot` 是模块/对象，点号 `.` 从中取出 `write_joint_state_to_sim` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `state`；第 2 个实参 `torch.zeros_like(state)`。
# 【项目含义】对 `robot` 调用 `write_joint_state_to_sim(state, torch.zeros_like(state))`：调用 `robot` 提供的 `write_joint_state_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
# 【L1867】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose`。右侧语法为：`cube.data.default_root_state[:, :7].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `cube_pose`，它在本项目中表示任务方块相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.default_root_state[:, :7].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`default_root_state` 表示状态相关值。
    cube_pose = cube.data.default_root_state[:, :7].clone()
# 【L1868】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose[:, :3]`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `as_tensor` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `source_block_position`；第 2 个实参 `device=sim.device`；第 3 个实参 `dtype=cube_pose.dtype`。
# 【项目含义】把右侧结果写进 `cube_pose[:, :3]`（写入 `cube_pose[:, :3]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)`；`as_tensor` 表示本功能块中的 `as_tensor` 值；`source_block_position` 表示源位置、位置相关值；`device` 表示本功能块中的 `device` 值。
    cube_pose[:, :3] = torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)
# 【L1869】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube_pose[:, 3:7]`。右侧语法为：`torch.as_tensor(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `cube_pose[:, 3:7]`（写入 `cube_pose[:, 3:7]` 指定的字段）；右侧具体做的是：计算表达式 `torch.as_tensor(`；`as_tensor` 表示本功能块中的 `as_tensor` 值。
    cube_pose[:, 3:7] = torch.as_tensor(
# 【L1870】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_block_quaternion, device`。右侧语法为：`sim.device, dtype=cube_pose.dtype` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `source_block_quaternion, device`；`source_block_quaternion` 表示源位置、四元数相关值；`device` 表示本功能块中的 `device` 值。右侧的来源是：计算表达式 `sim.device, dtype=cube_pose.dtype`；`sim` 表示IsaacLab SimulationContext，负责物理时间步；`device` 表示本功能块中的 `device` 值；`dtype` 表示本功能块中的 `dtype` 值。
        source_block_quaternion, device=sim.device, dtype=cube_pose.dtype
# 【L1871】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1872】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_root_pose_to_sim` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube_pose`。
# 【项目含义】对 `cube` 调用 `write_root_pose_to_sim(cube_pose)`：调用 `cube` 提供的 `write_root_pose_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube.write_root_pose_to_sim(cube_pose)
# 【L1873】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_root_velocity_to_sim` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `torch.zeros_like(cube.data.root_vel_w)`。
# 【项目含义】对 `cube` 调用 `write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))`：调用 `cube` 提供的 `write_root_velocity_to_sim` 操作。本行产生的修改/返回值服务于“写入初始状态；选择脚本专家或 π0.5 分支”。
    cube.write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))
# 【L1874】语法拆解：`hold(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `hold`；随后几行会逐项给它参数，调用结果或副作用用于“写入初始状态；选择脚本专家或 π0.5 分支”。
    hold(
# 【L1875】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1876】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1877】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1878】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1879】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`60 if args.initialize_at_grasp else 240` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】向上一行的函数调用或容器继续传入 `60 if args.initialize_at_grasp else 240`；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值，它参与“写入初始状态；选择脚本专家或 π0.5 分支”。
        60 if args.initialize_at_grasp else 240,
# 【L1880】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"SOURCE_SETTLE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写入初始状态；选择脚本专家或 π0.5 分支”中的帮助说明、错误原因、任务名称或报告文字。
        "SOURCE_SETTLE",
# 【L1881】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1882】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
    )
# 【L1883】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `settled_source_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `settled_source_position`，它在本项目中表示源位置、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    settled_source_position = cube.data.root_pos_w[0].clone()
# 【L1884】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `settled_source_quaternion`。右侧语法为：`cube.data.root_quat_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `settled_source_quaternion`，它在本项目中表示源位置、四元数相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.root_quat_w[0].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_quat_w` 表示本功能块中的 `root_quat_w` 值。
    settled_source_quaternion = cube.data.root_quat_w[0].clone()
# 【L1885】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=SOURCE_SETTLED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True` 的当前值/文字输出到终端；它用于观察“写入初始状态；选择脚本专家或 π0.5 分支”进度，也给日志留下可搜索证据。
    print("PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True)
# 【L1886】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写入初始状态；选择脚本专家或 π0.5 分支”中的逻辑段，让结构更容易看清。

# 【L1887】语法拆解：`if` 要求条件 `args.pi05_closed_loop` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.pi05_closed_loop` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
    if args.pi05_closed_loop:
# 【L1888】语法拆解：`assert episode_capture is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】断言 `episode_capture is not None` 必须成立；这是开发期内部一致性检查，失败说明“写入初始状态；选择脚本专家或 π0.5 分支”此前产生了不可能的状态。
        assert episode_capture is not None
# 【L1889】语法拆解：`assert episode_recorder is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】断言 `episode_recorder is not None` 必须成立；这是开发期内部一致性检查，失败说明“写入初始状态；选择脚本专家或 π0.5 分支”此前产生了不可能的状态。
        assert episode_recorder is not None
# 【L1890】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`run_pi05_closed_loop(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `run_pi05_closed_loop(` 交回调用者；这个值的含义是：计算表达式 `run_pi05_closed_loop(`；`run_pi05_closed_loop` 表示本功能块中的 `run_pi05_closed_loop` 值。
        return run_pi05_closed_loop(
# 【L1891】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `sim`。右侧语法为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `sim` 传入 `sim`；该参数在本项目中表示IsaacLab SimulationContext，负责物理时间步，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            sim=sim,
# 【L1892】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `robot`。右侧语法为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `robot` 传入 `robot`；该参数在本项目中表示IsaacLab Articulation；表示有多个关节的 RM65+4C2，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            robot=robot,
# 【L1893】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `cube`。右侧语法为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `cube` 传入 `cube`；该参数在本项目中表示IsaacLab RigidObject；本任务被抓取和放置的方块，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            cube=cube,
# 【L1894】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `state`。右侧语法为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `state` 传入 `state`；该参数在本项目中表示当前要写给 articulation 的全部关节目标张量，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            state=state,
# 【L1895】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `arm_ids`。右侧语法为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `arm_ids` 传入 `arm_ids`；该参数在本项目中表示本功能块中的 `arm_ids` 值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            arm_ids=arm_ids,
# 【L1896】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_ids`。右侧语法为：`gripper_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `gripper_ids` 传入 `gripper_ids`；该参数在本项目中表示夹爪相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_ids=gripper_ids,
# 【L1897】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `gripper_master_id`。右侧语法为：`joint_names` 是模块/对象，点号 `.` 从中取出 `index` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `GRIPPER_MASTER_JOINT`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `gripper_master_id` 传入 `joint_names.index(GRIPPER_MASTER_JOINT)`；该参数在本项目中表示夹爪相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
# 【L1898】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_block_position`。右侧语法为：`target_block_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `target_block_position` 传入 `target_block_position`；该参数在本项目中表示目标、位置相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_block_position=target_block_position,
# 【L1899】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `settled_source_position`。右侧语法为：`settled_source_position` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `settled_source_position` 传入 `settled_source_position`；该参数在本项目中表示源位置、位置相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            settled_source_position=settled_source_position,
# 【L1900】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_platform_collision_apis`。右侧语法为：`target_platform_collision_apis` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `target_platform_collision_apis` 传入 `target_platform_collision_apis`；该参数在本项目中表示目标、支撑平台相关值，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            target_platform_collision_apis=target_platform_collision_apis,
# 【L1901】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_capture`。右侧语法为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `episode_capture` 传入 `episode_capture`；该参数在本项目中表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            episode_capture=episode_capture,
# 【L1902】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder`。右侧语法为：`episode_recorder` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `episode_recorder` 传入 `episode_recorder`；该参数在本项目中表示把同步帧保存在内存并最终写盘的记录器，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            episode_recorder=episode_recorder,
# 【L1903】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `output`。右侧语法为：`output` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `output` 传入 `output`；该参数在本项目中表示输出文件路径，会参与“写入初始状态；选择脚本专家或 π0.5 分支”。
            output=output,
# 【L1904】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写入初始状态；选择脚本专家或 π0.5 分支”。
        )
# 【L1905】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写入初始状态；选择脚本专家或 π0.5 分支”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“写入初始状态；选择脚本专家或 π0.5 分支”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 17：脚本专家的接近、闭合夹爪和接触诊断（源码第 1906-2102 行）

### 5.A 数据流位置

- 上游：模块 16“写入初始状态；选择脚本专家或 π0.5 分支”。
- 本模块：脚本专家的接近、闭合夹爪和接触诊断。
- 下游：处理结果继续交给模块 18“恢复重力、抬升以及抬升失败早停”。

### 5.B 为什么需要这一组代码

这一组负责“脚本专家的接近、闭合夹爪和接触诊断”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `output`：输出文件路径。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `current`：float32 格式的当前六关节角。
- `pregrasp_distance_m`：预抓取位姿到实际抓取位姿之间的直线距离，单位米。

### 5.D 本模块首次阅读要认识的调用

- `reversed(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `smooth_move(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `hold(...)`：圆括号表示真正执行调用；保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。
- `np.max(...)`：圆括号表示真正执行调用；从候选值中选择最大者；常用于保证步数至少为 1 或累计峰值。
- `np.abs(...)`：圆括号表示真正执行调用；逐元素取绝对值。
- `detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。
- `numpy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `collision_api.CreateCollisionEnabledAttr(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `Set(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `tip_world_position(...)`：圆括号表示真正执行调用；读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L1906】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `approach_waypoints`。右侧语法为：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】得到 `approach_waypoints`，它在本项目中表示本功能块中的 `approach_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]`；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值；`reversed` 表示本功能块中的 `reversed` 值；`retreat_waypoints` 表示本功能块中的 `retreat_waypoints` 值。
    approach_waypoints = [] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]
# 【L1907】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_waypoint`。右侧语法为：`pregrasp_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pregrasp_arm`；`pregrasp_arm` 表示本功能块中的 `pregrasp_arm` 值。
    previous_waypoint = pregrasp_arm
# 【L1908】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(approach_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for index, waypoint in enumerate(approach_waypoints, start=1):
# 【L1909】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“脚本专家的接近、闭合夹爪和接触诊断”。
        smooth_move(
# 【L1910】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
            sim,
# 【L1911】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            robot,
# 【L1912】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
            cube,
# 【L1913】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
            state,
# 【L1914】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
            arm_ids,
# 【L1915】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`previous_waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `previous_waypoint`；在本项目中它表示上一值相关值。
            previous_waypoint,
# 【L1916】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
            waypoint,
# 【L1917】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`120` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `120`；逗号说明后面还有同级参数，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
            120,
# 【L1918】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"APPROACH_{index}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"APPROACH_{index}"`；`f` 表示本功能块中的 `f` 值；`APPROACH_` 表示本功能块中的 `APPROACH_` 值；`index` 表示索引相关值，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
            f"APPROACH_{index}",
# 【L1919】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
            episode_capture,
# 【L1920】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1921】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_waypoint`。右侧语法为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
        previous_waypoint = waypoint
# 【L1922】语法拆解：`if` 要求条件 `args.collision_bypass_during_approach` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
    if args.collision_bypass_during_approach:
# 【L1923】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `240`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)
# 【L1924】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_restore_arm_error`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_restore_arm_error`，它在本项目中表示本功能块中的 `pre_restore_arm_error` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
        pre_restore_arm_error = float(
# 【L1925】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `max` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm)`。
# 【项目含义】对 `np` 调用 `max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))`：调用 `np` 提供的 `max` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            np.max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))
# 【L1926】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1927】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print(f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True)
# 【L1928】语法拆解：`if` 要求条件 `args.collision_bypass_during_approach` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值
    if args.collision_bypass_during_approach:
# 【L1929】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `cube_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
        for collision_api in cube_collision_apis:
# 【L1930】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(True`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L1931】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True)
# 【L1932】语法拆解：`if` 要求条件 `not args.initialize_at_grasp` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值
    if not args.initialize_at_grasp:
# 【L1933】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `240`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)
# 【L1934】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actual_approach_arm`。右侧语法为：`robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actual_approach_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    actual_approach_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L1935】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_l2_midpoint`。右侧语法为：表达式 `0.5 * (` 使用运算符 `*`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `open_l2_midpoint`，它在本项目中表示本功能块中的 `open_l2_midpoint` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `0.5 * (` 的结果保存下来，供当前功能块后续使用。
    open_l2_midpoint = 0.5 * (
# 【L1936】语法拆解：`tip_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"tool_l_2") + tip_world_position(robot, "tool_r_2"`。
# 【项目含义】调用 `tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
        tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")
# 【L1937】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1938】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_midpoint_to_block`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `open_midpoint_to_block`，它在本项目中表示本功能块中的 `open_midpoint_to_block` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    open_midpoint_to_block = float(
# 【L1939】语法拆解：`torch.linalg` 是模块/对象，点号 `.` 从中取出 `vector_norm` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `open_l2_midpoint - cube.data.root_pos_w[0]`。
# 【项目含义】对 `torch.linalg` 调用 `vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])`：调用 `torch.linalg` 提供的 `vector_norm` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        torch.linalg.vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])
# 【L1940】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1941】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_midpoint_world`。右侧语法为：`open_l2_midpoint` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `open_midpoint_world`，它在本项目中表示本功能块中的 `open_midpoint_world` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `open_l2_midpoint.detach().cpu().numpy()`；`open_l2_midpoint` 表示本功能块中的 `open_l2_midpoint` 值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    open_midpoint_world = open_l2_midpoint.detach().cpu().numpy()
# 【L1942】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_midpoint_minus_block`。右侧语法为：表达式 `open_midpoint_world - cube.data.root_pos_w[0].detach().cpu().numpy()` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `open_midpoint_minus_block`，它在本项目中表示本功能块中的 `open_midpoint_minus_block` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    open_midpoint_minus_block = open_midpoint_world - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1943】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_pad_center_world_by_body`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `open_pad_center_world_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    open_pad_center_world_by_body = {
# 【L1944】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】对 `body_name: local_point_world_position(robot, body_name, local_position)` 调用 `detach().cpu().tolist()`：调用 `body_name: local_point_world_position(robot, body_name, local_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1945】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, local_position in PAD_LOCAL_CENTERS.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1946】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1947】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `open_pad_center_minus_block_by_body`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `open_pad_center_minus_block_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    open_pad_center_minus_block_by_body = {
# 【L1948】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `(`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `body_name: (` 接入当前完整语句；`body_name` 表示刚体相关值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: (
# 【L1949】语法拆解：`np` 是模块/对象，点号 `.` 从中取出 `asarray` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `world_position`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】调用 `np.asarray`：把输入统一转换为 NumPy 数组；已有数组通常不会无谓复制；本行实际操作 `np.asarray(world_position, dtype=np.float64)`。`asarray` 表示本功能块中的 `asarray` 值；`world_position` 表示位置相关值。
            np.asarray(world_position, dtype=np.float64)
# 【L1950】语法拆解：表达式 `- cube.data.root_pos_w[0].detach().cpu().numpy()` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】对 `- cube.data.root_pos_w[0]` 调用 `detach().cpu().numpy()`：调用 `- cube.data.root_pos_w[0]` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            - cube.data.root_pos_w[0].detach().cpu().numpy()
# 【L1951】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】对 `)` 调用 `tolist()`：调用 `)` 提供的 `tolist` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        ).tolist()
# 【L1952】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, world_position in open_pad_center_world_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, world_position in open_pad_center_world_by_body.items()
# 【L1953】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1954】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
    print(
# 【L1955】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"PICK_PLACE_APPROACH="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "PICK_PLACE_APPROACH="
# 【L1956】语法拆解：表达式 `+ json.dumps(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
        + json.dumps(
# 【L1957】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L1958】语法拆解：这是字典键值对：`"max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_approach_arm - grasp_arm))`。
# 【项目含义】定义字典/JSON 字段 `max_arm_joint_error_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
                "max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L1959】语法拆解：这是字典键值对：`"l2_midpoint_to_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_to_block` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `l2_midpoint_to_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
                "l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L1960】语法拆解：这是字典键值对：`"l2_midpoint_minus_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_minus_block` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `l2_midpoint_minus_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
                "l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L1961】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L1962】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L1963】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L1964】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1965】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_start`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `zeros` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `len(gripper_ids)`；第 2 个实参 `dtype=np.float64`。
# 【项目含义】得到 `close_start`，它在本项目中表示本功能块中的 `close_start` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.zeros(len(gripper_ids), dtype=np.float64)`；`zeros` 表示本功能块中的 `zeros` 值；`gripper_ids` 表示夹爪相关值；`dtype` 表示本功能块中的 `dtype` 值。
    close_start = np.zeros(len(gripper_ids), dtype=np.float64)
# 【L1966】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_target`。右侧语法为：`np` 是模块/对象，点号 `.` 从中取出 `full` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `len(gripper_ids)`；第 2 个实参 `args.gripper_close_target_rad`；第 3 个实参 `dtype=np.float64`。
# 【项目含义】得到 `close_target`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)`；`full` 表示本功能块中的 `full` 值；`gripper_ids` 表示夹爪相关值；`gripper_close_target_rad` 表示夹爪、目标相关值。
    close_target = np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)
# 【L1967】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“脚本专家的接近、闭合夹爪和接触诊断”。
    smooth_move(
# 【L1968】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L1969】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L1970】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L1971】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L1972】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`gripper_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `gripper_ids`；在本项目中它表示夹爪相关值。
        gripper_ids,
# 【L1973】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`close_start` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `close_start`；在本项目中它表示本功能块中的 `close_start` 值。
        close_start,
# 【L1974】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`close_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `close_target`；在本项目中它表示目标相关值。
        close_target,
# 【L1975】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`180` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `180`；逗号说明后面还有同级参数，它参与“脚本专家的接近、闭合夹爪和接触诊断”。
        180,
# 【L1976】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"CLOSE"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "CLOSE",
# 【L1977】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L1978】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1979】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
    hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)
# 【L1980】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closed_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    closed_position = cube.data.root_pos_w[0].clone()
# 【L1981】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_link_6_position`。右侧语法为：`body_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"link_6").clone(`。
# 【项目含义】得到 `closed_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    closed_link_6_position = body_world_position(robot, "link_6").clone()
# 【L1982】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_pad_center_world_by_body`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closed_pad_center_world_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    closed_pad_center_world_by_body = {
# 【L1983】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】对 `body_name: local_point_world_position(robot, body_name, local_position)` 调用 `detach().cpu().tolist()`：调用 `body_name: local_point_world_position(robot, body_name, local_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
# 【L1984】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, local_position in PAD_LOCAL_CENTERS.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
# 【L1985】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1986】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_pad_center_minus_block_by_body`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closed_pad_center_minus_block_by_body`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    closed_pad_center_minus_block_by_body = {
# 【L1987】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `(np.asarray(world_position, dtype=np.float64) - closed_position.detach().cpu().numpy()).tolist()`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】得到 `body_name`，它在本项目中表示刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `np.float64) - closed_position.detach().cpu().numpy()).tolist()`；`float64` 表示本功能块中的 `float64` 值；`closed_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值。
        body_name: (np.asarray(world_position, dtype=np.float64) - closed_position.detach().cpu().numpy()).tolist()
# 【L1988】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, world_position in closed_pad_center_world_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, world_position in closed_pad_center_world_by_body.items()
# 【L1989】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L1990】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_l2_gap`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closed_l2_gap`，它在本项目中表示本功能块中的 `closed_l2_gap` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    closed_l2_gap = float(
# 【L1991】语法拆解：`torch.linalg.vector_norm(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `torch.linalg` 调用多行方法 `vector_norm`：调用 `torch.linalg` 提供的 `vector_norm` 操作；具体参数写在随后几行，用于“脚本专家的接近、闭合夹爪和接触诊断”。
        torch.linalg.vector_norm(
# 【L1992】语法拆解：`tip_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"tool_l_2") - tip_world_position(robot, "tool_r_2"`。
# 【项目含义】调用 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“脚本专家的接近、闭合夹爪和接触诊断”。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L1993】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L1994】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L1995】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_gripper_joint_position`。右侧语法为：`robot.data.joint_pos[0, gripper_ids].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `closed_gripper_joint_position`，它在本项目中表示夹爪、关节、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    closed_gripper_joint_position = robot.data.joint_pos[0, gripper_ids].clone()
# 【L1996】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_contact_force_statistics_by_body`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `close_contact_force_statistics_by_body`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    close_contact_force_statistics_by_body = {}
# 【L1997】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `CONTACT_SENSORS.items()`，每次把当前元素放进 `body_name, contact_sensor`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L1998】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_contact_force_statistics_by_body[body_name]`。右侧语法为：`contact_force_statistics` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `contact_sensor`。
# 【项目含义】把右侧结果写进 `close_contact_force_statistics_by_body[body_name]`（写入 `close_contact_force_statistics_by_body[body_name]` 指定的字段）；右侧具体做的是：计算表达式 `contact_force_statistics(contact_sensor)`；`contact_force_statistics` 表示接触、力相关值；`contact_sensor` 表示接触相关值。
        close_contact_force_statistics_by_body[body_name] = contact_force_statistics(contact_sensor)
# 【L1999】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_contact_force_by_body_n`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `close_contact_force_by_body_n`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_contact_force_by_body_n = {
# 【L2000】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `statistics["peak_n"]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `body_name: statistics["peak_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`peak_n` 表示本功能块中的 `peak_n` 值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["peak_n"]
# 【L2001】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L2002】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L2003】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_current_contact_force_by_body_n`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `close_current_contact_force_by_body_n`，它在本项目中表示当前值、接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_current_contact_force_by_body_n = {
# 【L2004】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `statistics["current_n"]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `body_name: statistics["current_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`current_n` 表示当前值相关值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["current_n"]
# 【L2005】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L2006】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L2007】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_recent_mean_contact_force_by_body_n`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `close_recent_mean_contact_force_by_body_n`，它在本项目中表示接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    close_recent_mean_contact_force_by_body_n = {
# 【L2008】语法拆解：`body_name` 是参数/字段名；冒号 `:` 添加类型提示 `statistics["recent_mean_n"]`；末尾逗号表示外层参数列表还没结束。
# 【项目含义】把表达式/参数 `body_name: statistics["recent_mean_n"]` 接入当前完整语句；`body_name` 表示刚体相关值；`statistics` 表示本功能块中的 `statistics` 值；`recent_mean_n` 表示本功能块中的 `recent_mean_n` 值。在“脚本专家的接近、闭合夹爪和接触诊断”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        body_name: statistics["recent_mean_n"]
# 【L2009】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】开始遍历 `for body_name, statistics in close_contact_force_statistics_by_body.items()` 中给出的序列，逐项完成“脚本专家的接近、闭合夹爪和接触诊断”。
        for body_name, statistics in close_contact_force_statistics_by_body.items()
# 【L2010】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    }
# 【L2011】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_current_contact_force_vector_by_body_n`。右侧语法为：最外层花括号创建字典；字典中每个 `键: 值` 用冒号连接，不同字段用逗号分隔。
# 【项目含义】得到 `close_current_contact_force_vector_by_body_n`，它在本项目中表示当前值、接触、力、刚体相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{}` 的结果保存下来，供当前功能块后续使用。
    close_current_contact_force_vector_by_body_n = {}
# 【L2012】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `CONTACT_SENSORS.items()`，每次把当前元素放进 `body_name, contact_sensor`；这会逐个处理“脚本专家的接近、闭合夹爪和接触诊断”所需的帧、episode、动作或实验 case。
    for body_name, contact_sensor in CONTACT_SENSORS.items():
# 【L2013】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `current`。右侧语法为：`contact_sensor` 是起始对象；每个点号 `.` 依次读取属性/成员：`data` → `force_matrix_w`。
# 【项目含义】得到 `current`，它在本项目中表示float32 格式的当前六关节角；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `contact_sensor.data.force_matrix_w`；`contact_sensor` 表示接触相关值；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`force_matrix_w` 表示力相关值。
        current = contact_sensor.data.force_matrix_w
# 【L2014】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_current_contact_force_vector_by_body_n[body_name]`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `close_current_contact_force_vector_by_body_n[body_name]`（写入 `close_current_contact_force_vector_by_body_n[body_name]` 指定的字段）；右侧具体做的是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        close_current_contact_force_vector_by_body_n[body_name] = (
# 【L2015】语法拆解：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`[0.0, 0.0, 0.0]`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            [0.0, 0.0, 0.0]
# 【L2016】语法拆解：`if` 要求条件 `current is None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `current is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
            if current is None
# 【L2017】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】对 `else current` 调用 `reshape(-1, 3).sum(dim=0).detach().cpu().tolist()`：调用 `else current` 提供的 `reshape` 操作。本行产生的修改/返回值服务于“脚本专家的接近、闭合夹爪和接触诊断”。
            else current.reshape(-1, 3).sum(dim=0).detach().cpu().tolist()
# 【L2018】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        )
# 【L2019】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_left_finger_contact_force_n`。右侧语法为：`max(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `close_left_finger_contact_force_n`，它在本项目中表示接触、力相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `max(` 的结果保存下来，供当前功能块后续使用。
    close_left_finger_contact_force_n = max(
# 【L2020】语法拆解：`close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是生成式/推导式 `close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`close_contact_force_by_body_n` 表示接触、力、刚体相关值；`name` 表示本功能块中的 `name` 值；`tool_l_1` 表示本功能块中的 `tool_l_1` 值。产生的序列交给外层列表、字典或函数完成“脚本专家的接近、闭合夹爪和接触诊断”。
        close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")
# 【L2021】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L2022】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `close_right_finger_contact_force_n`。右侧语法为：`max(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `close_right_finger_contact_force_n`，它在本项目中表示接触、力相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `max(` 的结果保存下来，供当前功能块后续使用。
    close_right_finger_contact_force_n = max(
# 【L2023】语法拆解：`close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是生成式/推导式 `close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`close_contact_force_by_body_n` 表示接触、力、刚体相关值；`name` 表示本功能块中的 `name` 值；`tool_r_1` 表示本功能块中的 `tool_r_1` 值。产生的序列交给外层列表、字典或函数完成“脚本专家的接近、闭合夹爪和接触诊断”。
        close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")
# 【L2024】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L2025】语法拆解：`print(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把 `` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
    print(
# 【L2026】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"PICK_PLACE_CLOSE_CONTACT="`；Python 会把相邻字符串自动拼接，外层参数会把它用作“脚本专家的接近、闭合夹爪和接触诊断”中的帮助说明、错误原因、任务名称或报告文字。
        "PICK_PLACE_CLOSE_CONTACT="
# 【L2027】语法拆解：表达式 `+ json.dumps(` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `+ json.dumps(`。`json` 表示本功能块中的 `json` 值；`dumps` 表示本功能块中的 `dumps` 值。
        + json.dumps(
# 【L2028】语法拆解：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“脚本专家的接近、闭合夹爪和接触诊断”。
            {
# 【L2029】语法拆解：这是字典键值对：`"left_finger_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_left_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `left_finger_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `left_finger_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "left_finger_force_n": close_left_finger_contact_force_n,
# 【L2030】语法拆解：这是字典键值对：`"right_finger_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_right_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `right_finger_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `right_finger_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "right_finger_force_n": close_right_finger_contact_force_n,
# 【L2031】语法拆解：这是字典键值对：`"current_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `current_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `current_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "current_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2032】语法拆解：这是字典键值对：`"recent_mean_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_recent_mean_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `recent_mean_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `recent_mean_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "recent_mean_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2033】语法拆解：这是字典键值对：`"current_force_vector_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_vector_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `current_force_vector_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `current_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
                "current_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2034】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            }
# 【L2035】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        ),
# 【L2036】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `flush`。右侧语法为：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】给上一层函数/配置构造器的命名参数 `flush` 传入 `True`；该参数在本项目中表示本功能块中的 `flush` 值，会参与“脚本专家的接近、闭合夹爪和接触诊断”。
        flush=True,
# 【L2037】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
    )
# 【L2038】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“脚本专家的接近、闭合夹爪和接触诊断”中的逻辑段，让结构更容易看清。

# 【L2039】语法拆解：`if` 要求条件 `args.diagnose_approach_only` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.diagnose_approach_only` 是否成立；`diagnose_approach_only` 表示本功能块中的 `diagnose_approach_only` 值
    if args.diagnose_approach_only:
# 【L2040】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `diagnostic`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `diagnostic`，它在本项目中表示本功能块中的 `diagnostic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        diagnostic = {
# 【L2041】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"diagnostic"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"diagnostic"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "diagnostic",
# 【L2042】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L2043】语法拆解：这是字典键值对：`"collision_bypass_during_approach"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`collision_bypass_during_approach`。
# 【项目含义】定义字典/JSON 字段 `collision_bypass_during_approach`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `collision_bypass_during_approach` 数据；字段值来自 `args.collision_bypass_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L2044】语法拆解：这是字典键值对：`"initialized_at_grasp"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`initialize_at_grasp`。
# 【项目含义】定义字典/JSON 字段 `initialized_at_grasp`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L2045】语法拆解：这是字典键值对：`"arm_gravity_disabled_during_approach"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_during_approach`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2046】语法拆解：这是字典键值对：`"arm_gravity_disabled_through_transport"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_through_transport`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2047】语法拆解：这是字典键值对：`"natural_source_gravity"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`natural_source_gravity`。
# 【项目含义】定义字典/JSON 字段 `natural_source_gravity`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "natural_source_gravity": args.natural_source_gravity,
# 【L2048】语法拆解：这是字典键值对：`"moving_gripper_gravity_disabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`not args.enable_moving_gripper_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `moving_gripper_gravity_disabled`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `moving_gripper_gravity_disabled` 数据；字段值来自 `not args.enable_moving_gripper_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L2049】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `arm_actuator`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `arm_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_actuator": {
# 【L2050】语法拆解：这是字典键值对：`"effort_limit_sim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_effort_limit_sim`。
# 【项目含义】定义字典/JSON 字段 `effort_limit_sim`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `effort_limit_sim` 数据；字段值来自 `args.arm_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.arm_effort_limit_sim,
# 【L2051】语法拆解：这是字典键值对：`"stiffness"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_stiffness`。
# 【项目含义】定义字典/JSON 字段 `stiffness`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `stiffness` 数据；字段值来自 `args.arm_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.arm_stiffness,
# 【L2052】语法拆解：这是字典键值对：`"damping"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_damping`。
# 【项目含义】定义字典/JSON 字段 `damping`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `damping` 数据；字段值来自 `args.arm_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.arm_damping,
# 【L2053】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L2054】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_actuator`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_actuator": {
# 【L2055】语法拆解：这是字典键值对：`"effort_limit_sim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_effort_limit_sim`。
# 【项目含义】定义字典/JSON 字段 `effort_limit_sim`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L2056】语法拆解：这是字典键值对：`"stiffness"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_stiffness`。
# 【项目含义】定义字典/JSON 字段 `stiffness`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.gripper_stiffness,
# 【L2057】语法拆解：这是字典键值对：`"damping"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_damping`。
# 【项目含义】定义字典/JSON 字段 `damping`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.gripper_damping,
# 【L2058】语法拆解：这是字典键值对：`"close_target_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_close_target_rad`。
# 【项目含义】定义字典/JSON 字段 `close_target_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "close_target_rad": args.gripper_close_target_rad,
# 【L2059】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
            },
# 【L2060】语法拆解：这是字典键值对：`"requested_pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`requested_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L2061】语法拆解：这是字典键值对：`"pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`effective_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L2062】语法拆解：这是字典键值对：`"grasp_world_offset_x_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_x_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L2063】语法拆解：这是字典键值对：`"grasp_world_offset_z_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_z_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L2064】语法拆解：这是字典键值对：`"robot_base_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`robot_base_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `robot_base_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "robot_base_position_m": robot_base_position.tolist(),
# 【L2065】语法拆解：这是字典键值对：`"grasp_orientation_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_orientation_mode`。
# 【项目含义】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L2066】语法拆解：这是字典键值对：`"top_down_yaw_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_yaw_rad`。
# 【项目含义】定义字典/JSON 字段 `top_down_yaw_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_yaw_rad` 数据；字段值来自 `args.top_down_yaw_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L2067】语法拆解：这是字典键值对：`"top_down_tilt_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_tilt_rad`。
# 【项目含义】定义字典/JSON 字段 `top_down_tilt_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_tilt_rad` 数据；字段值来自 `args.top_down_tilt_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L2068】语法拆解：这是字典键值对：`"top_down_ik_multistart"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_ik_multistart`。
# 【项目含义】定义字典/JSON 字段 `top_down_ik_multistart`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_ik_multistart` 数据；字段值来自 `args.top_down_ik_multistart`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L2069】语法拆解：这是字典键值对：`"top_down_ik_seed_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`top_down_ik_seed_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L2070】语法拆解：这是字典键值对：`"top_down_blend"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_blend`。
# 【项目含义】定义字典/JSON 字段 `top_down_blend`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `top_down_blend` 数据；字段值来自 `args.top_down_blend`，因此保存/传递的是这个表达式当前计算出的结果。
            "top_down_blend": args.top_down_blend,
# 【L2071】语法拆解：这是字典键值对：`"reference_block_from_link_local_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`reference_block_from_link_local` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `reference_block_from_link_local_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `reference_block_from_link_local_m` 数据；字段值来自 `reference_block_from_link_local.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L2072】语法拆解：这是字典键值对：`"lift_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`lift_mode`。
# 【项目含义】定义字典/JSON 字段 `lift_mode`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_mode": args.lift_mode,
# 【L2073】语法拆解：这是字典键值对：`"cartesian_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`cartesian_lift_height_m`。
# 【项目含义】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L2074】语法拆解：这是字典键值对：`"settled_source_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`settled_source_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `settled_source_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L2075】语法拆解：这是字典键值对：`"settled_source_quaternion_wxyz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`settled_source_quaternion` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `settled_source_quaternion_wxyz`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `settled_source_quaternion_wxyz` 数据；字段值来自 `settled_source_quaternion.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L2076】语法拆解：这是字典键值对：`"closed_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_position_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_position_m` 数据；字段值来自 `closed_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L2077】语法拆解：这是字典键值对：`"close_left_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_left_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L2078】语法拆解：这是字典键值对：`"close_right_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_right_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L2079】语法拆解：这是字典键值对：`"close_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L2080】语法拆解：这是字典键值对：`"close_current_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2081】语法拆解：这是字典键值对：`"close_recent_mean_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_recent_mean_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2082】语法拆解：这是字典键值对：`"close_current_contact_force_vector_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_vector_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2083】语法拆解：这是字典键值对：`"approach_actual_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_approach_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_actual_arm_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_actual_arm_joint_position_rad` 数据；字段值来自 `actual_approach_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_actual_arm_joint_position_rad": actual_approach_arm.tolist(),
# 【L2084】语法拆解：这是字典键值对：`"approach_target_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`grasp_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_target_arm_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_target_arm_joint_position_rad` 数据；字段值来自 `grasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_target_arm_joint_position_rad": grasp_arm.tolist(),
# 【L2085】语法拆解：这是字典键值对：`"cartesian_retreat_distances_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`retreat_distances` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `cartesian_retreat_distances_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_retreat_distances_m` 数据；字段值来自 `retreat_distances.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L2086】语法拆解：这是字典键值对：`"cartesian_pregrasp_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`pregrasp_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `cartesian_pregrasp_joint_position_rad` 数据；字段值来自 `pregrasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L2087】语法拆解：这是字典键值对：`"approach_max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_approach_arm - grasp_arm))`。
# 【项目含义】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L2088】语法拆解：这是字典键值对：`"approach_l2_midpoint_to_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_to_block` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L2089】语法拆解：这是字典键值对：`"approach_l2_midpoint_world_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_world` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_world_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_world_m` 数据；字段值来自 `open_midpoint_world.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L2090】语法拆解：这是字典键值对：`"approach_l2_midpoint_minus_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_minus_block` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L2091】语法拆解：这是字典键值对：`"approach_pad_center_world_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_pad_center_world_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_pad_center_world_by_body_m` 数据；字段值来自 `open_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L2092】语法拆解：这是字典键值对：`"approach_pad_center_minus_block_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_pad_center_minus_block_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `approach_pad_center_minus_block_by_body_m` 数据；字段值来自 `open_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L2093】语法拆解：这是字典键值对：`"closed_pad_center_world_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_pad_center_world_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_pad_center_world_by_body_m` 数据；字段值来自 `closed_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L2094】语法拆解：这是字典键值对：`"closed_pad_center_minus_block_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_pad_center_minus_block_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L2095】语法拆解：这是字典键值对：`"closed_l2_tip_gap_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_l2_gap` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_l2_tip_gap_m`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_l2_tip_gap_m` 数据；字段值来自 `closed_l2_gap`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_l2_tip_gap_m": closed_l2_gap,
# 【L2096】语法拆解：这是字典键值对：`"closed_gripper_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_gripper_joint_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_gripper_joint_position_rad`，它表示“脚本专家的接近、闭合夹爪和接触诊断”中的 `closed_gripper_joint_position_rad` 数据；字段值来自 `closed_gripper_joint_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L2097】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“脚本专家的接近、闭合夹爪和接触诊断”。
        }
# 【L2098】语法拆解：`output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L2099】语法拆解：`output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(diagnostic, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
# 【L2100】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(diagnostic, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(diagnostic, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“脚本专家的接近、闭合夹爪和接触诊断”进度，也给日志留下可搜索证据。
        print(json.dumps(diagnostic, indent=2), flush=True)
# 【L2101】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `0` 交回调用者；这个值的含义是：把表达式 `0` 的结果保存下来，供当前功能块后续使用。
        return 0
# 【L2102】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“脚本专家的接近、闭合夹爪和接触诊断”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“脚本专家的接近、闭合夹爪和接触诊断”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 18：恢复重力、抬升以及抬升失败早停（源码第 2103-2179 行）

### 5.A 数据流位置

- 上游：模块 17“脚本专家的接近、闭合夹爪和接触诊断”。
- 本模块：恢复重力、抬升以及抬升失败早停。
- 下游：处理结果继续交给模块 19“搬运到目标并沿 IK 路点下降”。

### 5.B 为什么需要这一组代码

这一组负责“恢复重力、抬升以及抬升失败早停”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `episode_recorder`：把同步帧保存在内存并最终写盘的记录器。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `output`：输出文件路径。
- `source`：转换前的原始数组；这里不代表任务里的源物体。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。

### 5.D 本模块首次阅读要认识的调用

- `rigid_body_api.CreateDisableGravityAttr(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `Set(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `cube_rigid_body_api.CreateDisableGravityAttr(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `smooth_move(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `hold(...)`：圆括号表示真正执行调用；保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。
- `clone(...)`：圆括号表示真正执行调用；复制 Torch 张量，避免后续原地修改共享同一块数据。
- `body_world_position(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。
- `numpy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `item(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `settled_source_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L2103】语法拆解：`if` 要求条件 `not args.disable_arm_gravity_through_transport` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `not args.disable_arm_gravity_through_transport` 是否成立；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值
    if not args.disable_arm_gravity_through_transport:
# 【L2104】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `approach_arm_gravity_apis`，每次把当前元素放进 `rigid_body_api`；这会逐个处理“恢复重力、抬升以及抬升失败早停”所需的帧、episode、动作或实验 case。
        for rigid_body_api in approach_arm_gravity_apis:
# 【L2105】语法拆解：`rigid_body_api` 是模块/对象，点号 `.` 从中取出 `CreateDisableGravityAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(False`。
# 【项目含义】对 `rigid_body_api` 调用 `CreateDisableGravityAttr().Set(False)`：调用 `rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“恢复重力、抬升以及抬升失败早停”。
            rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L2106】语法拆解：`if` 要求条件 `approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport` 是否成立；`approach_arm_gravity_apis` 表示本功能块中的 `approach_arm_gravity_apis` 值；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值
    if approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport:
# 【L2107】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True)
# 【L2108】语法拆解：`cube_rigid_body_api` 是模块/对象，点号 `.` 从中取出 `CreateDisableGravityAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(False`。
# 【项目含义】对 `cube_rigid_body_api` 调用 `CreateDisableGravityAttr().Set(False)`：调用 `cube_rigid_body_api` 提供的 `CreateDisableGravityAttr` 操作。本行产生的修改/返回值服务于“恢复重力、抬升以及抬升失败早停”。
    cube_rigid_body_api.CreateDisableGravityAttr().Set(False)
# 【L2109】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“恢复重力、抬升以及抬升失败早停”。
    smooth_move(
# 【L2110】语法拆解：`sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture` 接入当前完整语句；`sim` 表示IsaacLab SimulationContext，负责物理时间步；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块。在“恢复重力、抬升以及抬升失败早停”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture
# 【L2111】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
    )
# 【L2112】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“恢复重力、抬升以及抬升失败早停”。
    hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)
# 【L2113】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lifted_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `lifted_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    lifted_position = cube.data.root_pos_w[0].clone()
# 【L2114】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lifted_link_6_position`。右侧语法为：`body_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"link_6").clone(`。
# 【项目含义】得到 `lifted_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    lifted_link_6_position = body_world_position(robot, "link_6").clone()
# 【L2115】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actual_lift_link_translation`。右侧语法为：表达式 `lifted_link_6_position - closed_link_6_position` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `actual_lift_link_translation`，它在本项目中表示物理仿真实际值、机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lifted_link_6_position - closed_link_6_position`；`lifted_link_6_position` 表示机器人连杆、位置相关值；`closed_link_6_position` 表示机器人连杆、位置相关值。
    actual_lift_link_translation = lifted_link_6_position - closed_link_6_position
# 【L2116】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `actual_lift_arm`。右侧语法为：`robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `actual_lift_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
    actual_lift_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L2117】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_height_after_attempt`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `(lifted_position[2] - closed_position[2]).item()`。
# 【项目含义】得到 `lift_height_after_attempt`，它在本项目中表示本功能块中的 `lift_height_after_attempt` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float((lifted_position[2] - closed_position[2]).item())`；`lifted_position` 表示位置相关值；`closed_position` 表示位置相关值；`item` 表示本功能块中的 `item` 值。
    lift_height_after_attempt = float((lifted_position[2] - closed_position[2]).item())
# 【L2118】语法拆解：`if` 要求条件 `lift_height_after_attempt <= 0.02` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `lift_height_after_attempt <= 0.02` 是否成立；`lift_height_after_attempt` 表示本功能块中的 `lift_height_after_attempt` 值
    if lift_height_after_attempt <= 0.02:
# 【L2119】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `failed_lift_report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `failed_lift_report`，它在本项目中表示失败、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        failed_lift_report = {
# 【L2120】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"fail"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"fail"`，因此保存/传递的是这个表达式当前计算出的结果。
            "status": "fail",
# 【L2121】语法拆解：这是字典键值对：`"failure_stage"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"lift"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `failure_stage`，它表示“恢复重力、抬升以及抬升失败早停”中的 `failure_stage` 数据；字段值来自 `"lift"`，因此保存/传递的是这个表达式当前计算出的结果。
            "failure_stage": "lift",
# 【L2122】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_only": True,
# 【L2123】语法拆解：这是字典键值对：`"pi05_used"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `pi05_used`，它表示“恢复重力、抬升以及抬升失败早停”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
            "pi05_used": False,
# 【L2124】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
            "real_robot_command_sent": False,
# 【L2125】语法拆解：这是字典键值对：`"natural_source_gravity"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`natural_source_gravity`。
# 【项目含义】定义字典/JSON 字段 `natural_source_gravity`，它表示“恢复重力、抬升以及抬升失败早停”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "natural_source_gravity": args.natural_source_gravity,
# 【L2126】语法拆解：这是字典键值对：`"arm_gravity_disabled_through_transport"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_through_transport`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“恢复重力、抬升以及抬升失败早停”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2127】语法拆解：这是字典键值对：`"requested_pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`requested_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L2128】语法拆解：这是字典键值对：`"pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`effective_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L2129】语法拆解：这是字典键值对：`"grasp_world_offset_x_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_x_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L2130】语法拆解：这是字典键值对：`"grasp_world_offset_z_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_z_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L2131】语法拆解：这是字典键值对：`"lift_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`lift_mode`。
# 【项目含义】定义字典/JSON 字段 `lift_mode`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_mode": args.lift_mode,
# 【L2132】语法拆解：这是字典键值对：`"cartesian_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`cartesian_lift_height_m`。
# 【项目含义】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L2133】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_actuator`，它表示“恢复重力、抬升以及抬升失败早停”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
            "gripper_actuator": {
# 【L2134】语法拆解：这是字典键值对：`"effort_limit_sim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_effort_limit_sim`。
# 【项目含义】定义字典/JSON 字段 `effort_limit_sim`，它表示“恢复重力、抬升以及抬升失败早停”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
                "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L2135】语法拆解：这是字典键值对：`"stiffness"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_stiffness`。
# 【项目含义】定义字典/JSON 字段 `stiffness`，它表示“恢复重力、抬升以及抬升失败早停”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
                "stiffness": args.gripper_stiffness,
# 【L2136】语法拆解：这是字典键值对：`"damping"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_damping`。
# 【项目含义】定义字典/JSON 字段 `damping`，它表示“恢复重力、抬升以及抬升失败早停”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
                "damping": args.gripper_damping,
# 【L2137】语法拆解：这是字典键值对：`"close_target_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_close_target_rad`。
# 【项目含义】定义字典/JSON 字段 `close_target_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
                "close_target_rad": args.gripper_close_target_rad,
# 【L2138】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            },
# 【L2139】语法拆解：这是字典键值对：`"source_platform_size_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_platform_size_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `source_platform_size_m` 数据；字段值来自 `list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L2140】语法拆解：这是字典键值对：`"settled_source_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`settled_source_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `settled_source_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
# 【L2141】语法拆解：这是字典键值对：`"closed_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_position_m` 数据；字段值来自 `closed_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_position_m": closed_position.detach().cpu().tolist(),
# 【L2142】语法拆解：这是字典键值对：`"lifted_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lifted_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `lifted_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lifted_position_m` 数据；字段值来自 `lifted_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lifted_position_m": lifted_position.detach().cpu().tolist(),
# 【L2143】语法拆解：这是字典键值对：`"block_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_height_after_attempt` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `block_lift_height_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `block_lift_height_m` 数据；字段值来自 `lift_height_after_attempt`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m": lift_height_after_attempt,
# 【L2144】语法拆解：这是字典键值对：`"close_left_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_left_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L2145】语法拆解：这是字典键值对：`"close_right_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_right_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L2146】语法拆解：这是字典键值对：`"close_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L2147】语法拆解：这是字典键值对：`"close_current_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2148】语法拆解：这是字典键值对：`"close_recent_mean_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_recent_mean_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2149】语法拆解：这是字典键值对：`"close_current_contact_force_vector_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_vector_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“恢复重力、抬升以及抬升失败早停”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2150】语法拆解：这是字典键值对：`"closed_link_6_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_link_6_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_link_6_position_m` 数据；字段值来自 `closed_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L2151】语法拆解：这是字典键值对：`"lifted_link_6_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lifted_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `lifted_link_6_position_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lifted_link_6_position_m` 数据；字段值来自 `lifted_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L2152】语法拆解：这是字典键值对：`"actual_lift_link_translation_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_lift_link_translation` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `actual_lift_link_translation_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `actual_lift_link_translation_m` 数据；字段值来自 `actual_lift_link_translation.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L2153】语法拆解：这是字典键值对：`"lift_max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_lift_arm - lift_arm))`。
# 【项目含义】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_lift_arm - lift_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L2154】语法拆解：这是字典键值对：`"lift_actual_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_actual_arm_joint_position_rad` 数据；字段值来自 `actual_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L2155】语法拆解：这是字典键值对：`"lift_target_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `lift_target_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L2156】语法拆解：这是字典键值对：`"approach_max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_approach_arm - grasp_arm))`。
# 【项目含义】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“恢复重力、抬升以及抬升失败早停”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L2157】语法拆解：这是字典键值对：`"approach_l2_midpoint_minus_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_minus_block` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L2158】语法拆解：这是字典键值对：`"closed_pad_center_minus_block_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_pad_center_minus_block_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“恢复重力、抬升以及抬升失败早停”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L2159】语法拆解：这是字典键值对：`"reason"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"The block did not clear the source support after the commanded lift."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `reason`，它表示“恢复重力、抬升以及抬升失败早停”中的 `reason` 数据；字段值来自 `"The block did not clear the source support after the commanded lift."`，因此保存/传递的是这个表达式当前计算出的结果。
            "reason": "The block did not clear the source support after the commanded lift.",
# 【L2160】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
        }
# 【L2161】语法拆解：`if` 要求条件 `episode_recorder is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `episode_recorder is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if episode_recorder is not None:
# 【L2162】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["task_success"]`。右侧语法为：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：把表达式 `False` 的结果保存下来，供当前功能块后续使用。
            episode_recorder.metadata["task_success"] = False
# 【L2163】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["failure_stage"]`。右侧语法为：`"lift"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["failure_stage"]`（写入 `episode_recorder.metadata["failure_stage"]` 指定的字段）；右侧具体做的是：计算表达式 `"lift"`；`lift` 表示本功能块中的 `lift` 值。
            episode_recorder.metadata["failure_stage"] = "lift"
# 【L2164】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_manifest`。右侧语法为：`episode_recorder` 是模块/对象，点号 `.` 从中取出 `save` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `episode_manifest`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
            episode_manifest = episode_recorder.save()
# 【L2165】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_validation`。右侧语法为：`validate_episode(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episode_validation`，它在本项目中表示一条轨迹、校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(`；`validate_episode` 表示一条轨迹相关值。
            episode_validation = validate_episode(
# 【L2166】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.output_dir, require_images`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_images`。
# 【项目含义】把表达式/参数 `episode_recorder.output_dir, require_images=args.record_images` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值；`require_images` 表示本功能块中的 `require_images` 值。在“恢复重力、抬升以及抬升失败早停”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
                episode_recorder.output_dir, require_images=args.record_images
# 【L2167】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            )
# 【L2168】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `failed_lift_report["expert_episode"]`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `failed_lift_report["expert_episode"]`（写入 `failed_lift_report["expert_episode"]` 指定的字段）；右侧具体做的是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
            failed_lift_report["expert_episode"] = {
# 【L2169】语法拆解：这是字典键值对：`"directory"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_recorder.output_dir`。
# 【项目含义】定义字典/JSON 字段 `directory`，它表示“恢复重力、抬升以及抬升失败早停”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
                "directory": str(episode_recorder.output_dir),
# 【L2170】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_manifest["frame_count"]` 使用方括号索引；先计算 `"frame_count"`，再从 `episode_manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“恢复重力、抬升以及抬升失败早停”中的 `frame_count` 数据；字段值来自 `episode_manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
                "frame_count": episode_manifest["frame_count"],
# 【L2171】语法拆解：这是字典键值对：`"validation"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_validation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `validation`，它表示“恢复重力、抬升以及抬升失败早停”中的 `validation` 数据；字段值来自 `episode_validation`，因此保存/传递的是这个表达式当前计算出的结果。
                "validation": episode_validation,
# 【L2172】语法拆解：这是字典键值对：`"training_ready"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `training_ready`，它表示“恢复重力、抬升以及抬升失败早停”中的 `training_ready` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
                "training_ready": False,
# 【L2173】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“恢复重力、抬升以及抬升失败早停”。
            }
# 【L2174】语法拆解：`output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
        output.parent.mkdir(parents=True, exist_ok=True)
# 【L2175】语法拆解：`output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(failed_lift_report, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
        output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")
# 【L2176】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(failed_lift_report, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(failed_lift_report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print(json.dumps(failed_lift_report, indent=2), flush=True)
# 【L2177】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True` 的当前值/文字输出到终端；它用于观察“恢复重力、抬升以及抬升失败早停”进度，也给日志留下可搜索证据。
        print("RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True)
# 【L2178】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`1` 是直接写在源码中的数值常量。
# 【项目含义】结束当前函数并把 `1` 交回调用者；这个值的含义是：把表达式 `1` 的结果保存下来，供当前功能块后续使用。
        return 1
# 【L2179】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“恢复重力、抬升以及抬升失败早停”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“恢复重力、抬升以及抬升失败早停”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 19：搬运到目标并沿 IK 路点下降（源码第 2180-2243 行）

### 5.A 数据流位置

- 上游：模块 18“恢复重力、抬升以及抬升失败早停”。
- 本模块：搬运到目标并沿 IK 路点下降。
- 下游：处理结果继续交给模块 20“张开夹爪、自然释放、撤退和稳定等待”。

### 5.B 为什么需要这一组代码

这一组负责“搬运到目标并沿 IK 路点下降”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `lula`：NVIDIA Lula 运动学求解器实例。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。

### 5.D 本模块首次阅读要认识的调用

- `smooth_move(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `collision_api.CreateCollisionEnabledAttr(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `Set(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `hold(...)`：圆括号表示真正执行调用；保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。
- `clone(...)`：圆括号表示真正执行调用；复制 Torch 张量，避免后续原地修改共享同一块数据。
- `body_world_position(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。
- `numpy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `lula.compute_forward_kinematics(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L2180】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
    smooth_move(
# 【L2181】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L2182】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L2183】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L2184】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L2185】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
        arm_ids,
# 【L2186】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `lift_arm`；在本项目中它表示本功能块中的 `lift_arm` 值。
        lift_arm,
# 【L2187】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_lift_arm`；在本项目中它表示目标相关值。
        target_lift_arm,
# 【L2188】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`360` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `360`；逗号说明后面还有同级参数，它参与“搬运到目标并沿 IK 路点下降”。
        360,
# 【L2189】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"TRANSFER"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
        "TRANSFER",
# 【L2190】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L2191】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
    )
# 【L2192】语法拆解：`if` 要求条件 `args.target_collision_enable_stage == "after_transfer"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.target_collision_enable_stage == "after_transfer"` 是否成立；`target_collision_enable_stage` 表示目标相关值；`after_transfer` 表示本功能块中的 `after_transfer` 值
    if args.target_collision_enable_stage == "after_transfer":
# 【L2193】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
        for collision_api in target_platform_collision_apis:
# 【L2194】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(True`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“搬运到目标并沿 IK 路点下降”。
            collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L2195】语法拆解：`if` 要求条件 `target_platform_collision_apis` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `target_platform_collision_apis` 是否成立；`target_platform_collision_apis` 表示目标、支撑平台相关值
        if target_platform_collision_apis:
# 【L2196】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True` 的当前值/文字输出到终端；它用于观察“搬运到目标并沿 IK 路点下降”进度，也给日志留下可搜索证据。
            print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
# 【L2197】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“搬运到目标并沿 IK 路点下降”。
            hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)
# 【L2198】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_place_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_place_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    pre_place_position = cube.data.root_pos_w[0].clone()
# 【L2199】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_place_link_6_position`。右侧语法为：`body_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"link_6").clone(`。
# 【项目含义】得到 `pre_place_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
    pre_place_link_6_position = body_world_position(robot, "link_6").clone()
# 【L2200】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_actual_arm`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `place_actual_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_actual_arm = None
# 【L2201】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_actual_link_6_position`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `place_actual_link_6_position`，它在本项目中表示物理仿真实际值、机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_actual_link_6_position = None
# 【L2202】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_commanded_link_6_position`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `place_commanded_link_6_position`，它在本项目中表示机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    place_commanded_link_6_position = None
# 【L2203】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_start_arm`。右侧语法为：`target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `release_start_arm`，它在本项目中表示本功能块中的 `release_start_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_lift_arm`；`target_lift_arm` 表示目标相关值。
    release_start_arm = target_lift_arm
# 【L2204】语法拆解：`if` 要求条件 `args.place_descent` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
    if args.place_descent:
# 【L2205】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_place_waypoint`。右侧语法为：`target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `target_lift_arm`；`target_lift_arm` 表示目标相关值。
        previous_place_waypoint = target_lift_arm
# 【L2206】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(place_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
        for index, waypoint in enumerate(place_waypoints, start=1):
# 【L2207】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
            smooth_move(
# 【L2208】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                sim,
# 【L2209】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                robot,
# 【L2210】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                cube,
# 【L2211】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                state,
# 【L2212】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                arm_ids,
# 【L2213】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`previous_place_waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `previous_place_waypoint`；在本项目中它表示上一值相关值。
                previous_place_waypoint,
# 【L2214】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
                waypoint,
# 【L2215】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`place_waypoint_steps`。
# 【项目含义】向上一行的函数调用或容器继续传入 `args.place_waypoint_steps`；`place_waypoint_steps` 表示步数相关值，它参与“搬运到目标并沿 IK 路点下降”。
                args.place_waypoint_steps,
# 【L2216】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"PLACE_DESCENT_{index}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"PLACE_DESCENT_{index}"`；`f` 表示本功能块中的 `f` 值；`PLACE_DESCENT_` 表示本功能块中的 `PLACE_DESCENT_` 值；`index` 表示索引相关值，它参与“搬运到目标并沿 IK 路点下降”。
                f"PLACE_DESCENT_{index}",
# 【L2217】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                episode_capture,
# 【L2218】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
            )
# 【L2219】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_place_waypoint`。右侧语法为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
            previous_place_waypoint = waypoint
# 【L2220】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“搬运到目标并沿 IK 路点下降”。
        hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)
# 【L2221】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_start_arm`。右侧语法为：`place_waypoints[-1]` 使用方括号索引；先计算 `-1`，再从 `place_waypoints` 取对应字典字段或数组元素。
# 【项目含义】得到 `release_start_arm`，它在本项目中表示本功能块中的 `release_start_arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `place_waypoints[-1]`；`place_waypoints` 表示本功能块中的 `place_waypoints` 值。
        release_start_arm = place_waypoints[-1]
# 【L2222】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_actual_arm`。右侧语法为：`robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `place_actual_arm`，它在本项目中表示物理仿真实际值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取物理仿真后的实际关节位置，而不是控制器目标。
        place_actual_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
# 【L2223】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_actual_link_6_position`。右侧语法为：`body_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"link_6").clone(`。
# 【项目含义】得到 `place_actual_link_6_position`，它在本项目中表示物理仿真实际值、机器人连杆、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `body_world_position(robot, "link_6").clone()`；`body_world_position` 表示刚体、位置相关值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`link_6` 表示机器人连杆相关值。
        place_actual_link_6_position = body_world_position(robot, "link_6").clone()
# 【L2224】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `place_commanded_link_6_position, _`。右侧语法为：`lula.compute_forward_kinematics(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧返回的多个结果按位置拆给 `place_commanded_link_6_position, _`；`place_commanded_link_6_position` 表示机器人连杆、位置相关值；`_` 表示本功能块中的 `_` 值。右侧的来源是：让 Lula 根据六个 RM65 关节角计算 link_6 的位置和旋转，用于校准或验证 IK。
        place_commanded_link_6_position, _ = lula.compute_forward_kinematics(
# 【L2225】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"link_6", place_waypoints[-1]`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
            "link_6", place_waypoints[-1]
# 【L2226】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
        )
# 【L2227】语法拆解：表达式 `place_commanded_link_6_position += robot_base_position` 使用运算符 `+`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `place_commanded_link_6_position + robot_base_position` 更新 `place_commanded_link_6_position` 原值；`place_commanded_link_6_position` 表示机器人连杆、位置相关值，常用于累计步数、距离、损失或成功次数。
        place_commanded_link_6_position += robot_base_position
# 【L2228】语法拆解：`if` 要求条件 `args.target_collision_enable_stage == "after_place_descent"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.target_collision_enable_stage == "after_place_descent"` 是否成立；`target_collision_enable_stage` 表示目标相关值；`after_place_descent` 表示本功能块中的 `after_place_descent` 值
        if args.target_collision_enable_stage == "after_place_descent":
# 【L2229】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `target_platform_collision_apis`，每次把当前元素放进 `collision_api`；这会逐个处理“搬运到目标并沿 IK 路点下降”所需的帧、episode、动作或实验 case。
            for collision_api in target_platform_collision_apis:
# 【L2230】语法拆解：`collision_api` 是模块/对象，点号 `.` 从中取出 `CreateCollisionEnabledAttr` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).Set(True`。
# 【项目含义】对 `collision_api` 调用 `CreateCollisionEnabledAttr().Set(True)`：调用 `collision_api` 提供的 `CreateCollisionEnabledAttr` 操作。本行产生的修改/返回值服务于“搬运到目标并沿 IK 路点下降”。
                collision_api.CreateCollisionEnabledAttr().Set(True)
# 【L2231】语法拆解：`if` 要求条件 `target_platform_collision_apis` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `target_platform_collision_apis` 是否成立；`target_platform_collision_apis` 表示目标、支撑平台相关值
            if target_platform_collision_apis:
# 【L2232】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True` 的当前值/文字输出到终端；它用于观察“搬运到目标并沿 IK 路点下降”进度，也给日志留下可搜索证据。
                print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True)
# 【L2233】语法拆解：`hold(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `hold`；随后几行会逐项给它参数，调用结果或副作用用于“搬运到目标并沿 IK 路点下降”。
                hold(
# 【L2234】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                    sim,
# 【L2235】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                    robot,
# 【L2236】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                    cube,
# 【L2237】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                    state,
# 【L2238】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`120` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `120`；逗号说明后面还有同级参数，它参与“搬运到目标并沿 IK 路点下降”。
                    120,
# 【L2239】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"TARGET_COLLISION_AFTER_PLACE_HOLD"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“搬运到目标并沿 IK 路点下降”中的帮助说明、错误原因、任务名称或报告文字。
                    "TARGET_COLLISION_AFTER_PLACE_HOLD",
# 【L2240】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                    episode_capture,
# 【L2241】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“搬运到目标并沿 IK 路点下降”。
                )
# 【L2242】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_release_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `pre_release_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
    pre_release_position = cube.data.root_pos_w[0].clone()
# 【L2243】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“搬运到目标并沿 IK 路点下降”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“搬运到目标并沿 IK 路点下降”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 20：张开夹爪、自然释放、撤退和稳定等待（源码第 2244-2320 行）

### 5.A 数据流位置

- 上游：模块 19“搬运到目标并沿 IK 路点下降”。
- 本模块：张开夹爪、自然释放、撤退和稳定等待。
- 下游：处理结果继续交给模块 21“计算成功指标并保存专家 episode”。

### 5.B 为什么需要这一组代码

这一组负责“张开夹爪、自然释放、撤退和稳定等待”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `state`：当前要写给 articulation 的全部关节目标张量。
- `episode_capture`：连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `sim`：IsaacLab SimulationContext，负责物理时间步。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。

### 5.D 本模块首次阅读要认识的调用

- `smooth_move(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `hold(...)`：圆括号表示真正执行调用；保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。
- `clone(...)`：圆括号表示真正执行调用；复制 Torch 张量，避免后续原地修改共享同一块数据。
- `reversed(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `enumerate(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `target_lift_arm.copy(...)`：圆括号表示真正执行调用；创建独立副本，后续修改副本时不影响原对象。
- `cube.write_root_pose_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `torch.zeros_like(...)`：圆括号表示真正执行调用；PyTorch 的 `zeros_like` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `cube.write_root_velocity_to_sim(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L2244】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
    smooth_move(
# 【L2245】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
        sim,
# 【L2246】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
        robot,
# 【L2247】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
        cube,
# 【L2248】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
        state,
# 【L2249】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`gripper_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `gripper_ids`；在本项目中它表示夹爪相关值。
        gripper_ids,
# 【L2250】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`close_target` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `close_target`；在本项目中它表示目标相关值。
        close_target,
# 【L2251】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`close_start` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `close_start`；在本项目中它表示本功能块中的 `close_start` 值。
        close_start,
# 【L2252】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`180` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `180`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
        180,
# 【L2253】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"OPEN"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
        "OPEN",
# 【L2254】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
        episode_capture,
# 【L2255】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
    )
# 【L2256】语法拆解：`if` 要求条件 `args.unassisted_release` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值
    if args.unassisted_release:
# 【L2257】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=UNASSISTED_RELEASE"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True` 的当前值/文字输出到终端；它用于观察“张开夹爪、自然释放、撤退和稳定等待”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True)
# 【L2258】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `240`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)
# 【L2259】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `released_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `released_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        released_position = cube.data.root_pos_w[0].clone()
# 【L2260】语法拆解：`if` 要求条件 `args.place_descent` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
        if args.place_descent:
# 【L2261】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `retreat_place_waypoints`。右侧语法为：表达式 `list(reversed(place_waypoints[:-1])) + [target_lift_arm]` 使用运算符 `+`, `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】得到 `retreat_place_waypoints`，它在本项目中表示本功能块中的 `retreat_place_waypoints` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `list(reversed(place_waypoints[:-1])) + [target_lift_arm]`；`reversed` 表示本功能块中的 `reversed` 值；`place_waypoints` 表示本功能块中的 `place_waypoints` 值；`target_lift_arm` 表示目标相关值。
            retreat_place_waypoints = list(reversed(place_waypoints[:-1])) + [target_lift_arm]
# 【L2262】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_place_waypoint`。右侧语法为：`release_start_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `release_start_arm`；`release_start_arm` 表示本功能块中的 `release_start_arm` 值。
            previous_place_waypoint = release_start_arm
# 【L2263】语法拆解：`for` 开始遍历；`in` 左边是每轮变量，右边是被遍历序列；末尾冒号打开循环体。
# 【项目含义】遍历 `enumerate(retreat_place_waypoints, start=1)`，每次把当前元素放进 `index, waypoint`；这会逐个处理“张开夹爪、自然释放、撤退和稳定等待”所需的帧、episode、动作或实验 case。
            for index, waypoint in enumerate(retreat_place_waypoints, start=1):
# 【L2264】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
                smooth_move(
# 【L2265】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                    sim,
# 【L2266】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                    robot,
# 【L2267】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                    cube,
# 【L2268】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                    state,
# 【L2269】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                    arm_ids,
# 【L2270】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`previous_place_waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `previous_place_waypoint`；在本项目中它表示上一值相关值。
                    previous_place_waypoint,
# 【L2271】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `waypoint`；在本项目中它表示本功能块中的 `waypoint` 值。
                    waypoint,
# 【L2272】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`60` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `60`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                    60,
# 【L2273】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`f"RETREAT_{index}"` 是 f-string；引号界定文本，花括号会把变量当前值嵌入文本。
# 【项目含义】向上一行的函数调用或容器继续传入 `f"RETREAT_{index}"`；`f` 表示本功能块中的 `f` 值；`RETREAT_` 表示本功能块中的 `RETREAT_` 值；`index` 表示索引相关值，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                    f"RETREAT_{index}",
# 【L2274】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                    episode_capture,
# 【L2275】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
                )
# 【L2276】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `previous_place_waypoint`。右侧语法为：`waypoint` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `previous_place_waypoint`，它在本项目中表示上一值相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `waypoint`；`waypoint` 表示本功能块中的 `waypoint` 值。
                previous_place_waypoint = waypoint
# 【L2277】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“张开夹爪、自然释放、撤退和稳定等待”中处理剩余输入或备用路径。
        else:
# 【L2278】语法拆解：`assert release_clear_arm is not None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】断言 `release_clear_arm is not None` 必须成立；这是开发期内部一致性检查，失败说明“张开夹爪、自然释放、撤退和稳定等待”此前产生了不可能的状态。
            assert release_clear_arm is not None
# 【L2279】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
            smooth_move(
# 【L2280】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
                sim,
# 【L2281】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
                robot,
# 【L2282】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
                cube,
# 【L2283】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
                state,
# 【L2284】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
                arm_ids,
# 【L2285】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`release_start_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `release_start_arm`；在本项目中它表示本功能块中的 `release_start_arm` 值。
                release_start_arm,
# 【L2286】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`release_clear_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `release_clear_arm`；在本项目中它表示本功能块中的 `release_clear_arm` 值。
                release_clear_arm,
# 【L2287】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`240` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `240`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
                240,
# 【L2288】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"RETREAT"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
                "RETREAT",
# 【L2289】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
                episode_capture,
# 【L2290】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
            )
# 【L2291】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `480`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)
# 【L2292】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        final_position = cube.data.root_pos_w[0].clone()
# 【L2293】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】前面的 `if/elif` 都不成立时走这里；在“张开夹爪、自然释放、撤退和稳定等待”中处理剩余输入或备用路径。
    else:
# 【L2294】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `target_clear_arm`。右侧语法为：`target_lift_arm` 是模块/对象，点号 `.` 从中取出 `copy` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `target_clear_arm`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        target_clear_arm = target_lift_arm.copy()
# 【L2295】语法拆解：表达式 `target_clear_arm[1] -= 0.10` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `target_clear_arm[1] - 0.10` 更新 `target_clear_arm[1]` 原值；`target_clear_arm[1]` 表示目标相关值，常用于累计步数、距离、损失或成功次数。
        target_clear_arm[1] -= 0.10
# 【L2296】语法拆解：表达式 `target_clear_arm[2] -= 0.10` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】用 `target_clear_arm[2] - 0.10` 更新 `target_clear_arm[2]` 原值；`target_clear_arm[2]` 表示目标相关值，常用于累计步数、距离、损失或成功次数。
        target_clear_arm[2] -= 0.10
# 【L2297】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_pose`。右侧语法为：`cube.data.root_state_w[:, :7].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `release_pose`，它在本项目中表示本功能块中的 `release_pose` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `cube.data.root_state_w[:, :7].clone()`；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`root_state_w` 表示状态相关值。
        release_pose = cube.data.root_state_w[:, :7].clone()
# 【L2298】语法拆解：表达式 `release_pose[:, 2] -= args.release_separation_assist_m` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把表达式/参数 `release_pose[:, 2] -= args.release_separation_assist_m` 接入当前完整语句；`release_pose` 表示本功能块中的 `release_pose` 值；`release_separation_assist_m` 表示本功能块中的 `release_separation_assist_m` 值。在“张开夹爪、自然释放、撤退和稳定等待”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        release_pose[:, 2] -= args.release_separation_assist_m
# 【L2299】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_root_pose_to_sim` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `release_pose`。
# 【项目含义】对 `cube` 调用 `write_root_pose_to_sim(release_pose)`：调用 `cube` 提供的 `write_root_pose_to_sim` 操作。本行产生的修改/返回值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        cube.write_root_pose_to_sim(release_pose)
# 【L2300】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_velocity`。右侧语法为：`torch` 是模块/对象，点号 `.` 从中取出 `zeros_like` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `cube.data.root_vel_w`。
# 【项目含义】得到 `release_velocity`，它在本项目中表示本功能块中的 `release_velocity` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `torch.zeros_like(cube.data.root_vel_w)`；`zeros_like` 表示本功能块中的 `zeros_like` 值；`cube` 表示IsaacLab RigidObject；本任务被抓取和放置的方块；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
        release_velocity = torch.zeros_like(cube.data.root_vel_w)
# 【L2301】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_velocity[:, 2]`。右侧语法为：表达式 `-RELEASE_DOWNWARD_SPEED_M_S` 使用运算符 `-`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把右侧结果写进 `release_velocity[:, 2]`（写入 `release_velocity[:, 2]` 指定的字段）；右侧具体做的是：计算表达式 `-RELEASE_DOWNWARD_SPEED_M_S`；`RELEASE_DOWNWARD_SPEED_M_S` 表示本功能块中的 `RELEASE_DOWNWARD_SPEED_M_S` 值。
        release_velocity[:, 2] = -RELEASE_DOWNWARD_SPEED_M_S
# 【L2302】语法拆解：`cube` 是模块/对象，点号 `.` 从中取出 `write_root_velocity_to_sim` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `release_velocity`。
# 【项目含义】对 `cube` 调用 `write_root_velocity_to_sim(release_velocity)`：调用 `cube` 提供的 `write_root_velocity_to_sim` 操作。本行产生的修改/返回值服务于“张开夹爪、自然释放、撤退和稳定等待”。
        cube.write_root_velocity_to_sim(release_velocity)
# 【L2303】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True` 的当前值/文字输出到终端；它用于观察“张开夹爪、自然释放、撤退和稳定等待”进度，也给日志留下可搜索证据。
        print("PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True)
# 【L2304】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `480`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)
# 【L2305】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `released_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `released_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        released_position = cube.data.root_pos_w[0].clone()
# 【L2306】语法拆解：`smooth_move(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始调用多行函数 `smooth_move`；随后几行会逐项给它参数，调用结果或副作用用于“张开夹爪、自然释放、撤退和稳定等待”。
        smooth_move(
# 【L2307】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`sim` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `sim`；在本项目中它表示IsaacLab SimulationContext，负责物理时间步。
            sim,
# 【L2308】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`robot` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `robot`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
            robot,
# 【L2309】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`cube` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `cube`；在本项目中它表示IsaacLab RigidObject；本任务被抓取和放置的方块。
            cube,
# 【L2310】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`state` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `state`；在本项目中它表示当前要写给 articulation 的全部关节目标张量。
            state,
# 【L2311】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`arm_ids` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `arm_ids`；在本项目中它表示本功能块中的 `arm_ids` 值。
            arm_ids,
# 【L2312】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_lift_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_lift_arm`；在本项目中它表示目标相关值。
            target_lift_arm,
# 【L2313】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`target_clear_arm` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `target_clear_arm`；在本项目中它表示目标相关值。
            target_clear_arm,
# 【L2314】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`240` 是直接写在源码中的数值常量。
# 【项目含义】向上一行的函数调用或容器继续传入 `240`；逗号说明后面还有同级参数，它参与“张开夹爪、自然释放、撤退和稳定等待”。
            240,
# 【L2315】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"RETREAT"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“张开夹爪、自然释放、撤退和稳定等待”中的帮助说明、错误原因、任务名称或报告文字。
            "RETREAT",
# 【L2316】语法拆解：这是上一行多行函数调用或容器的一个参数/元素；末尾逗号表示还有同级内容。该表达式自身可读为：`episode_capture` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `episode_capture`；在本项目中它表示连接 IsaacLab 每个物理步和 EpisodeRecorder 的采样桥。
            episode_capture,
# 【L2317】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“张开夹爪、自然释放、撤退和稳定等待”。
        )
# 【L2318】语法拆解：`hold` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `sim`；第 2 个实参 `robot`；第 3 个实参 `cube`；第 4 个实参 `state`；第 5 个实参 `120`；另外还有 2 个实参。
# 【项目含义】调用 `hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)`：保持当前关节目标若干物理步，并同步更新机器人/方块状态和可选 episode 记录。它的结果/修改用于“张开夹爪、自然释放、撤退和稳定等待”。
        hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)
# 【L2319】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_position`。右侧语法为：`cube.data.root_pos_w[0].clone()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `final_position`，它在本项目中表示位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：从 IsaacLab 数据缓冲区读取方块在世界坐标系中的实际 xyz 位置。
        final_position = cube.data.root_pos_w[0].clone()
# 【L2320】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“张开夹爪、自然释放、撤退和稳定等待”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“张开夹爪、自然释放、撤退和稳定等待”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 21：计算成功指标并保存专家 episode（源码第 2321-2386 行）

### 5.A 数据流位置

- 上游：模块 20“张开夹爪、自然释放、撤退和稳定等待”。
- 本模块：计算成功指标并保存专家 episode。
- 下游：处理结果继续交给模块 22“写出完整机器可读报告”。

### 5.B 为什么需要这一组代码

这一组负责“计算成功指标并保存专家 episode”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `episode_recorder`：把同步帧保存在内存并最终写盘的记录器。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `cube`：IsaacLab RigidObject；本任务被抓取和放置的方块。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `metadata`：描述 episode、数据来源或 policy server 的机器可读元信息。
- `passed`：当前单条任务或整套评测是否满足所有硬性门槛。

### 5.D 本模块首次阅读要认识的调用

- `settled_source_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。
- `numpy(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `closed_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `lifted_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `pre_release_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `released_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `final_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `np.linalg.norm(...)`：圆括号表示真正执行调用；计算向量长度/欧氏距离。
- `torch.linalg.vector_norm(...)`：圆括号表示真正执行调用；PyTorch 的 `vector_norm` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。
- `tip_world_position(...)`：圆括号表示真正执行调用；读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。
- `torch.isfinite(...)`：圆括号表示真正执行调用；PyTorch 的 `isfinite` 张量函数；本行的逐行项目含义会说明设备、shape 和结果用途。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L2321】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `settled_source_np`。右侧语法为：`settled_source_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `settled_source_np`，它在本项目中表示源位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `settled_source_position.detach().cpu().numpy()`；`settled_source_position` 表示源位置、位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    settled_source_np = settled_source_position.detach().cpu().numpy()
# 【L2322】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `closed_np`。右侧语法为：`closed_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `closed_np`，它在本项目中表示本功能块中的 `closed_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `closed_position.detach().cpu().numpy()`；`closed_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    closed_np = closed_position.detach().cpu().numpy()
# 【L2323】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lifted_np`。右侧语法为：`lifted_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `lifted_np`，它在本项目中表示本功能块中的 `lifted_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `lifted_position.detach().cpu().numpy()`；`lifted_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    lifted_np = lifted_position.detach().cpu().numpy()
# 【L2324】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pre_release_np`。右侧语法为：`pre_release_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `pre_release_np`，它在本项目中表示本功能块中的 `pre_release_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `pre_release_position.detach().cpu().numpy()`；`pre_release_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    pre_release_np = pre_release_position.detach().cpu().numpy()
# 【L2325】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `released_np`。右侧语法为：`released_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `released_np`，它在本项目中表示本功能块中的 `released_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `released_position.detach().cpu().numpy()`；`released_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    released_np = released_position.detach().cpu().numpy()
# 【L2326】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_np`。右侧语法为：`final_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().numpy(`。
# 【项目含义】得到 `final_np`，它在本项目中表示本功能块中的 `final_np` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `final_position.detach().cpu().numpy()`；`final_position` 表示位置相关值；`detach` 表示本功能块中的 `detach` 值；`cpu` 表示本功能块中的 `cpu` 值。
    final_np = final_position.detach().cpu().numpy()
# 【L2327】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_to_target_distance`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(target_block_position[:2] - source_block_position[:2])`。
# 【项目含义】得到 `source_to_target_distance`，它在本项目中表示源位置、目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    source_to_target_distance = float(np.linalg.norm(target_block_position[:2] - source_block_position[:2]))
# 【L2328】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `lift_height`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `lifted_np[2] - closed_np[2]`；其中 `lifted_np[2] - closed_np[2]` 的方括号表示先从 `lifted_np` 按键/索引 `2] - closed_np[2` 取值。
# 【项目含义】得到 `lift_height`，它在本项目中表示本功能块中的 `lift_height` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(lifted_np[2] - closed_np[2])`；`lifted_np` 表示本功能块中的 `lifted_np` 值；`closed_np` 表示本功能块中的 `closed_np` 值。
    lift_height = float(lifted_np[2] - closed_np[2])
# 【L2329】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_target_xy_error`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np[:2] - target_block_position[:2])`。
# 【项目含义】得到 `final_target_xy_error`，它在本项目中表示目标相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
# 【L2330】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_target_position_error`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np - target_block_position)`。
# 【项目含义】得到 `final_target_position_error`，它在本项目中表示目标、位置相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
# 【L2331】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `release_drift`。右侧语法为：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.linalg.norm(final_np - released_np)`。
# 【项目含义】得到 `release_drift`，它在本项目中表示本功能块中的 `release_drift` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算两个位置之差或向量的欧氏长度，用作距离、漂移、指尖间距或动作变化量。
    release_drift = float(np.linalg.norm(final_np - released_np))
# 【L2332】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `final_l2_tip_gap`。右侧语法为：`float(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `final_l2_tip_gap`，它在本项目中表示本功能块中的 `final_l2_tip_gap` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `float(` 的结果保存下来，供当前功能块后续使用。
    final_l2_tip_gap = float(
# 【L2333】语法拆解：`torch.linalg.vector_norm(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】开始对 `torch.linalg` 调用多行方法 `vector_norm`：调用 `torch.linalg` 提供的 `vector_norm` 操作；具体参数写在随后几行，用于“计算成功指标并保存专家 episode”。
        torch.linalg.vector_norm(
# 【L2334】语法拆解：`tip_world_position` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot`；第 2 个实参 `"tool_l_2") - tip_world_position(robot, "tool_r_2"`。
# 【项目含义】调用 `tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")`：读取指定 4C2 指尖 link 在世界坐标系中的实际位置，用于计算开口或接触几何。它的结果/修改用于“计算成功指标并保存专家 episode”。
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
# 【L2335】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2336】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2337】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `all_states_finite`。右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `all_states_finite`，它在本项目中表示本功能块中的 `all_states_finite` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    all_states_finite = bool(
# 【L2338】语法拆解：`torch` 是模块/对象，点号 `.` 从中取出 `isfinite` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `robot.data.joint_pos).all().item(`。
# 【项目含义】对 `torch` 调用 `isfinite(robot.data.joint_pos).all().item()`：调用 `torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“计算成功指标并保存专家 episode”。
        torch.isfinite(robot.data.joint_pos).all().item()
# 【L2339】语法拆解：`and torch.isfinite(cube.data.root_state_w).all().item()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】对 `and torch` 调用 `isfinite(cube.data.root_state_w).all().item()`：调用 `and torch` 提供的 `isfinite` 操作。本行产生的修改/返回值服务于“计算成功指标并保存专家 episode”。
        and torch.isfinite(cube.data.root_state_w).all().item()
# 【L2340】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2341】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `passed`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `passed`，它在本项目中表示当前单条任务或整套评测是否满足所有硬性门槛；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    passed = (
# 【L2342】语法拆解：`all_states_finite` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `all_states_finite`；在本项目中它表示本功能块中的 `all_states_finite` 值。
        all_states_finite
# 【L2343】语法拆解：表达式 `and source_to_target_distance > 0.12` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `source_to_target_distance > 0.12` 用“并且”接到上一行判断中；判断 `source_to_target_distance > 0.12` 是否成立；`source_to_target_distance` 表示源位置、目标相关值。所有连接条件共同决定是否进入后续分支。
        and source_to_target_distance > 0.12
# 【L2344】语法拆解：表达式 `and lift_height > 0.02` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `lift_height > 0.02` 用“并且”接到上一行判断中；判断 `lift_height > 0.02` 是否成立；`lift_height` 表示本功能块中的 `lift_height` 值。所有连接条件共同决定是否进入后续分支。
        and lift_height > 0.02
# 【L2345】语法拆解：表达式 `and final_target_xy_error < 0.05` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `final_target_xy_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_xy_error < 0.05` 是否成立；`final_target_xy_error` 表示目标相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_xy_error < 0.05
# 【L2346】语法拆解：表达式 `and final_target_position_error < 0.05` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `final_target_position_error < 0.05` 用“并且”接到上一行判断中；判断 `final_target_position_error < 0.05` 是否成立；`final_target_position_error` 表示目标、位置相关值。所有连接条件共同决定是否进入后续分支。
        and final_target_position_error < 0.05
# 【L2347】语法拆解：表达式 `and release_drift < 0.02` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `release_drift < 0.02` 用“并且”接到上一行判断中；判断 `release_drift < 0.02` 是否成立；`release_drift` 表示本功能块中的 `release_drift` 值。所有连接条件共同决定是否进入后续分支。
        and release_drift < 0.02
# 【L2348】语法拆解：表达式 `and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12` 使用运算符 `<`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12` 用“并且”接到上一行判断中；判断 `float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12` 是否成立；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`data` 表示传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request；`joint_pos` 表示关节相关值。所有连接条件共同决定是否进入后续分支。
        and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12
# 【L2349】语法拆解：表达式 `and final_l2_tip_gap > 0.06` 使用运算符 `>`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把条件 `final_l2_tip_gap > 0.06` 用“并且”接到上一行判断中；判断 `final_l2_tip_gap > 0.06` 是否成立；`final_l2_tip_gap` 表示本功能块中的 `final_l2_tip_gap` 值。所有连接条件共同决定是否进入后续分支。
        and final_l2_tip_gap > 0.06
# 【L2350】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2351】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `unassisted_full_task_complete`。右侧语法为：`bool(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `unassisted_full_task_complete`，它在本项目中表示本功能块中的 `unassisted_full_task_complete` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `bool(` 的结果保存下来，供当前功能块后续使用。
    unassisted_full_task_complete = bool(
# 【L2352】语法拆解：`passed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `passed`；在本项目中它表示当前单条任务或整套评测是否满足所有硬性门槛。
        passed
# 【L2353】语法拆解：`and args.unassisted_release` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `args.unassisted_release` 用“并且”接到上一行判断中；判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值。所有连接条件共同决定是否进入后续分支。
        and args.unassisted_release
# 【L2354】语法拆解：`and args.place_descent` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `args.place_descent` 用“并且”接到上一行判断中；判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值。所有连接条件共同决定是否进入后续分支。
        and args.place_descent
# 【L2355】语法拆解：`and args.natural_source_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `args.natural_source_gravity` 用“并且”接到上一行判断中；判断 `args.natural_source_gravity` 是否成立；`natural_source_gravity` 表示源位置相关值。所有连接条件共同决定是否进入后续分支。
        and args.natural_source_gravity
# 【L2356】语法拆解：`and args.enable_moving_gripper_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `args.enable_moving_gripper_gravity` 用“并且”接到上一行判断中；判断 `args.enable_moving_gripper_gravity` 是否成立；`enable_moving_gripper_gravity` 表示夹爪相关值。所有连接条件共同决定是否进入后续分支。
        and args.enable_moving_gripper_gravity
# 【L2357】语法拆解：`and not args.collision_bypass_during_approach` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `not args.collision_bypass_during_approach` 用“并且”接到上一行判断中；判断 `not args.collision_bypass_during_approach` 是否成立；`collision_bypass_during_approach` 表示本功能块中的 `collision_bypass_during_approach` 值。所有连接条件共同决定是否进入后续分支。
        and not args.collision_bypass_during_approach
# 【L2358】语法拆解：`and not args.initialize_at_grasp` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `not args.initialize_at_grasp` 用“并且”接到上一行判断中；判断 `not args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值。所有连接条件共同决定是否进入后续分支。
        and not args.initialize_at_grasp
# 【L2359】语法拆解：`and not args.disable_arm_gravity_during_approach` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `not args.disable_arm_gravity_during_approach` 用“并且”接到上一行判断中；判断 `not args.disable_arm_gravity_during_approach` 是否成立；`disable_arm_gravity_during_approach` 表示本功能块中的 `disable_arm_gravity_during_approach` 值。所有连接条件共同决定是否进入后续分支。
        and not args.disable_arm_gravity_during_approach
# 【L2360】语法拆解：`and not args.disable_arm_gravity_through_transport` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把条件 `not args.disable_arm_gravity_through_transport` 用“并且”接到上一行判断中；判断 `not args.disable_arm_gravity_through_transport` 是否成立；`disable_arm_gravity_through_transport` 表示本功能块中的 `disable_arm_gravity_through_transport` 值。所有连接条件共同决定是否进入后续分支。
        and not args.disable_arm_gravity_through_transport
# 【L2361】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
    )
# 【L2362】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expert_episode_report`。右侧语法为：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】得到 `expert_episode_report`，它在本项目中表示一条轨迹、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `None` 的结果保存下来，供当前功能块后续使用。
    expert_episode_report = None
# 【L2363】语法拆解：`if` 要求条件 `episode_recorder is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `episode_recorder is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
    if episode_recorder is not None:
# 【L2364】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.metadata["task_success"]`。右侧语法为：`passed` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把右侧结果写进 `episode_recorder.metadata["task_success"]`（写入 `episode_recorder.metadata["task_success"]` 指定的字段）；右侧具体做的是：计算表达式 `passed`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
        episode_recorder.metadata["task_success"] = passed
# 【L2365】语法拆解：`episode_recorder.metadata[` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `episode_recorder.metadata[` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`metadata` 表示描述 episode、数据来源或 policy server 的机器可读元信息。在“计算成功指标并保存专家 episode”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        episode_recorder.metadata[
# 【L2366】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"unassisted_full_task_complete"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“计算成功指标并保存专家 episode”中的帮助说明、错误原因、任务名称或报告文字。
            "unassisted_full_task_complete"
# 【L2367】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `]`。右侧语法为：`unassisted_full_task_complete` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】闭合上一行开始的函数/容器后继续执行 `] = unassisted_full_task_complete` 中的索引或转换；`unassisted_full_task_complete` 表示本功能块中的 `unassisted_full_task_complete` 值，用于“计算成功指标并保存专家 episode”。
        ] = unassisted_full_task_complete
# 【L2368】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_manifest`。右侧语法为：`episode_recorder` 是模块/对象，点号 `.` 从中取出 `save` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `episode_manifest`，它在本项目中表示一条轨迹相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `episode_recorder.save()`；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`save` 表示本功能块中的 `save` 值。
        episode_manifest = episode_recorder.save()
# 【L2369】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_validation`。右侧语法为：`validate_episode(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `episode_validation`，它在本项目中表示一条轨迹、校验结果相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `validate_episode(`；`validate_episode` 表示一条轨迹相关值。
        episode_validation = validate_episode(
# 【L2370】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `episode_recorder.output_dir, require_images`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_images`。
# 【项目含义】把表达式/参数 `episode_recorder.output_dir, require_images=args.record_images` 接入当前完整语句；`episode_recorder` 表示把同步帧保存在内存并最终写盘的记录器；`output_dir` 表示输出相关值；`require_images` 表示本功能块中的 `require_images` 值。在“计算成功指标并保存专家 episode”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            episode_recorder.output_dir, require_images=args.record_images
# 【L2371】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        )
# 【L2372】语法拆解：`if` 要求条件 `episode_validation["status"] != "pass"` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `episode_validation["status"] != "pass"` 是否成立；`episode_validation` 表示一条轨迹、校验结果相关值；`status` 表示本功能块中的 `status` 值；`pass` 表示本功能块中的 `pass` 值
        if episode_validation["status"] != "pass":
# 【L2373】语法拆解：`raise` 主动制造并抛出异常；后面的 `RuntimeError(f"recorded episode failed validation: {episode_validation}")` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `RuntimeError(f"recorded episode failed validation: {episode_validation}")` 并停止当前路径；说明当前输入违反“计算成功指标并保存专家 episode”要求，不能继续进入仿真、训练或评测。
            raise RuntimeError(f"recorded episode failed validation: {episode_validation}")
# 【L2374】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expert_episode_report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expert_episode_report`，它在本项目中表示一条轨迹、报告相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
        expert_episode_report = {
# 【L2375】语法拆解：这是字典键值对：`"directory"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `episode_recorder.output_dir`。
# 【项目含义】定义字典/JSON 字段 `directory`，它表示“计算成功指标并保存专家 episode”中的 `directory` 数据；字段值来自 `str(episode_recorder.output_dir)`，因此保存/传递的是这个表达式当前计算出的结果。
            "directory": str(episode_recorder.output_dir),
# 【L2376】语法拆解：这是字典键值对：`"format"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_manifest["format"]` 使用方括号索引；先计算 `"format"`，再从 `episode_manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `format`，它表示“计算成功指标并保存专家 episode”中的 `format` 数据；字段值来自 `episode_manifest["format"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "format": episode_manifest["format"],
# 【L2377】语法拆解：这是字典键值对：`"frame_count"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_manifest["frame_count"]` 使用方括号索引；先计算 `"frame_count"`，再从 `episode_manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `frame_count`，它表示“计算成功指标并保存专家 episode”中的 `frame_count` 数据；字段值来自 `episode_manifest["frame_count"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "frame_count": episode_manifest["frame_count"],
# 【L2378】语法拆解：这是字典键值对：`"control_hz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_manifest["control_hz"]` 使用方括号索引；先计算 `"control_hz"`，再从 `episode_manifest` 取对应字典字段或数组元素。
# 【项目含义】定义字典/JSON 字段 `control_hz`，它表示“计算成功指标并保存专家 episode”中的 `control_hz` 数据；字段值来自 `episode_manifest["control_hz"]`，因此保存/传递的是这个表达式当前计算出的结果。
            "control_hz": episode_manifest["control_hz"],
# 【L2379】语法拆解：这是字典键值对：`"validation"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`episode_validation` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `validation`，它表示“计算成功指标并保存专家 episode”中的 `validation` 数据；字段值来自 `episode_validation`，因此保存/传递的是这个表达式当前计算出的结果。
            "validation": episode_validation,
# 【L2380】语法拆解：这是字典键值对：`"training_ready"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`bool` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `passed and args.record_images`。
# 【项目含义】定义字典/JSON 字段 `training_ready`，它表示“计算成功指标并保存专家 episode”中的 `training_ready` 数据；字段值来自 `bool(passed and args.record_images)`，因此保存/传递的是这个表达式当前计算出的结果。
            "training_ready": bool(passed and args.record_images),
# 【L2381】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `training_blocker`，它表示“计算成功指标并保存专家 episode”中的 `training_blocker` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
            "training_blocker": (
# 【L2382】语法拆解：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】声明/传入参数 `None`；在本项目中它表示本功能块中的 `None` 值。
                None
# 【L2383】语法拆解：`if` 要求条件 `args.record_images` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.record_images` 是否成立；`record_images` 表示本功能块中的 `record_images` 值
                if args.record_images
# 【L2384】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `"external and wrist RGB streams were not recorded"`；它让“计算成功指标并保存专家 episode”在可选数据缺失时仍有明确结果。
                else "external and wrist RGB streams were not recorded"
# 【L2385】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
            ),
# 【L2386】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“计算成功指标并保存专家 episode”。
        }
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“计算成功指标并保存专家 episode”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 22：写出完整机器可读报告（源码第 2387-2567 行）

### 5.A 数据流位置

- 上游：模块 21“计算成功指标并保存专家 episode”。
- 本模块：写出完整机器可读报告。
- 下游：处理结果继续交给模块 23“捕获异常、关闭 Isaac Sim、返回退出码”。

### 5.B 为什么需要这一组代码

这一组负责“写出完整机器可读报告”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `robot`：IsaacLab Articulation；表示有多个关节的 RM65+4C2。
- `output`：输出文件路径。
- `data`：传入 transform 的一条样本字典；训练时来自 LeRobot，推理时来自 IsaacLab request。
- `passed`：当前单条任务或整套评测是否满足所有硬性门槛。
- `pregrasp_distance_m`：预抓取位姿到实际抓取位姿之间的直线距离，单位米。
- `collision`：新增到指尖 link 的接触碰撞体 XML 节点。

### 5.D 本模块首次阅读要认识的调用

- `robot_base_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `reference_block_from_link_local.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `source_block_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `target_block_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `expected_lift_translation.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `expected_source_lift_block_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `target_release_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `source_block_quaternion.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `target_block_quaternion.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `target_platform_position.tolist(...)`：圆括号表示真正执行调用；把 NumPy/Torch 数据转换成普通 Python 列表，便于写入 JSON。
- `pre_place_position.detach(...)`：圆括号表示真正执行调用；让 Torch 张量脱离自动求导图；仿真记录只需要数值。
- `cpu(...)`：圆括号表示真正执行调用；把 Torch 张量移动到 CPU，便于转 NumPy 或写盘。

### 5.F 这一模块的版本变化

- 与上一版教学快照相比，这一模块没有源码变化。

### 5.G 逐行精读

```python
# 【L2387】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`{` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L2388】语法拆解：这是字典键值对：`"status"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"pass" if passed else "fail"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `status`，它表示本阶段的机器可读通过/失败状态；字段值来自 `"pass" if passed else "fail"`，因此保存/传递的是这个表达式当前计算出的结果。
        "status": "pass" if passed else "fail",
# 【L2389】语法拆解：这是字典键值对：`"simulation_only"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `simulation_only`，它表示明确证据只来自仿真；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "simulation_only": True,
# 【L2390】语法拆解：这是字典键值对：`"pi05_used"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `pi05_used`，它表示“写出完整机器可读报告”中的 `pi05_used` 数据；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "pi05_used": False,
# 【L2391】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `expert`，它表示“写出完整机器可读报告”中的 `expert` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert": (
# 【L2392】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写出完整机器可读报告”中的帮助说明、错误原因、任务名称或报告文字。
            "scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"
# 【L2393】语法拆解：`if` 要求条件 `args.initialize_at_grasp` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.initialize_at_grasp` 是否成立；`initialize_at_grasp` 表示本功能块中的 `initialize_at_grasp` 值
            if args.initialize_at_grasp
# 【L2394】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `"scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else "scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"
# 【L2395】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2396】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `task`，它表示LeRobot 使用的语言任务字段，训练时会成为 prompt；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "task": (
# 【L2397】语法拆解：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】这是上一行尚未闭合的参数、数组或字典内容：`(`；其数据会并入上一行创建的对象，共同完成“写出完整机器可读报告”。
            (
# 【L2398】语法拆解：成对引号界定字符串；相邻字符串会被 Python 自动拼接；末尾逗号表示它是外层参数/列表中的一个元素。
# 【项目含义】提供文本片段 `"approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“写出完整机器可读报告”中的帮助说明、错误原因、任务名称或报告文字。
                "approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"
# 【L2399】语法拆解：`if` 要求条件 `args.place_descent` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
                if args.place_descent
# 【L2400】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `"approach, close, lift, transfer, unassisted release, and vertical clearance"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
                else "approach, close, lift, transfer, unassisted release, and vertical clearance"
# 【L2401】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
            )
# 【L2402】语法拆解：`if` 要求条件 `args.unassisted_release` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.unassisted_release` 是否成立；`unassisted_release` 表示本功能块中的 `unassisted_release` 值
            if args.unassisted_release
# 【L2403】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `"approach, close, lift, transfer, assisted release onto a platform, and retreat"`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else "approach, close, lift, transfer, assisted release onto a platform, and retreat"
# 【L2404】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2405】语法拆解：这是字典键值对：`"real_robot_command_sent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`False` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `real_robot_command_sent`，它表示是否向真实机械臂发送过命令；本项目应始终为 false；字段值来自 `False`，因此保存/传递的是这个表达式当前计算出的结果。
        "real_robot_command_sent": False,
# 【L2406】语法拆解：这是字典键值对：`"expert_episode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`expert_episode_report` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `expert_episode`，它表示“写出完整机器可读报告”中的 `expert_episode` 数据；字段值来自 `expert_episode_report`，因此保存/传递的是这个表达式当前计算出的结果。
        "expert_episode": expert_episode_report,
# 【L2407】语法拆解：这是字典键值对：`"unassisted_full_task_complete"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`unassisted_full_task_complete` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `unassisted_full_task_complete`，它表示“写出完整机器可读报告”中的 `unassisted_full_task_complete` 数据；字段值来自 `unassisted_full_task_complete`，因此保存/传递的是这个表达式当前计算出的结果。
        "unassisted_full_task_complete": unassisted_full_task_complete,
# 【L2408】语法拆解：这是字典键值对：`"transfer_joint_1_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】定义字典/JSON 字段 `transfer_joint_1_rad`，它表示“写出完整机器可读报告”中的 `transfer_joint_1_rad` 数据；字段值来自 `args.transfer_joint_1_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
# 【L2409】语法拆解：这是字典键值对：`"collision_bypass_during_approach"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`collision_bypass_during_approach`。
# 【项目含义】定义字典/JSON 字段 `collision_bypass_during_approach`，它表示“写出完整机器可读报告”中的 `collision_bypass_during_approach` 数据；字段值来自 `args.collision_bypass_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
        "collision_bypass_during_approach": args.collision_bypass_during_approach,
# 【L2410】语法拆解：这是字典键值对：`"initialized_at_grasp"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`initialize_at_grasp`。
# 【项目含义】定义字典/JSON 字段 `initialized_at_grasp`，它表示“写出完整机器可读报告”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
        "initialized_at_grasp": args.initialize_at_grasp,
# 【L2411】语法拆解：这是字典键值对：`"arm_gravity_disabled_during_approach"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_during_approach`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2412】语法拆解：这是字典键值对：`"arm_gravity_disabled_through_transport"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_through_transport`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2413】语法拆解：这是字典键值对：`"natural_source_gravity"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`natural_source_gravity`。
# 【项目含义】定义字典/JSON 字段 `natural_source_gravity`，它表示“写出完整机器可读报告”中的 `natural_source_gravity` 数据；字段值来自 `args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "natural_source_gravity": args.natural_source_gravity,
# 【L2414】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `arm_actuator`，它表示“写出完整机器可读报告”中的 `arm_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "arm_actuator": {
# 【L2415】语法拆解：这是字典键值对：`"effort_limit_sim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_effort_limit_sim`。
# 【项目含义】定义字典/JSON 字段 `effort_limit_sim`，它表示“写出完整机器可读报告”中的 `effort_limit_sim` 数据；字段值来自 `args.arm_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
            "effort_limit_sim": args.arm_effort_limit_sim,
# 【L2416】语法拆解：这是字典键值对：`"stiffness"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_stiffness`。
# 【项目含义】定义字典/JSON 字段 `stiffness`，它表示“写出完整机器可读报告”中的 `stiffness` 数据；字段值来自 `args.arm_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
            "stiffness": args.arm_stiffness,
# 【L2417】语法拆解：这是字典键值对：`"damping"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`arm_damping`。
# 【项目含义】定义字典/JSON 字段 `damping`，它表示“写出完整机器可读报告”中的 `damping` 数据；字段值来自 `args.arm_damping`，因此保存/传递的是这个表达式当前计算出的结果。
            "damping": args.arm_damping,
# 【L2418】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2419】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `gripper_actuator`，它表示“写出完整机器可读报告”中的 `gripper_actuator` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_actuator": {
# 【L2420】语法拆解：这是字典键值对：`"effort_limit_sim"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_effort_limit_sim`。
# 【项目含义】定义字典/JSON 字段 `effort_limit_sim`，它表示“写出完整机器可读报告”中的 `effort_limit_sim` 数据；字段值来自 `args.gripper_effort_limit_sim`，因此保存/传递的是这个表达式当前计算出的结果。
            "effort_limit_sim": args.gripper_effort_limit_sim,
# 【L2421】语法拆解：这是字典键值对：`"stiffness"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_stiffness`。
# 【项目含义】定义字典/JSON 字段 `stiffness`，它表示“写出完整机器可读报告”中的 `stiffness` 数据；字段值来自 `args.gripper_stiffness`，因此保存/传递的是这个表达式当前计算出的结果。
            "stiffness": args.gripper_stiffness,
# 【L2422】语法拆解：这是字典键值对：`"damping"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_damping`。
# 【项目含义】定义字典/JSON 字段 `damping`，它表示“写出完整机器可读报告”中的 `damping` 数据；字段值来自 `args.gripper_damping`，因此保存/传递的是这个表达式当前计算出的结果。
            "damping": args.gripper_damping,
# 【L2423】语法拆解：这是字典键值对：`"close_target_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`gripper_close_target_rad`。
# 【项目含义】定义字典/JSON 字段 `close_target_rad`，它表示“写出完整机器可读报告”中的 `close_target_rad` 数据；字段值来自 `args.gripper_close_target_rad`，因此保存/传递的是这个表达式当前计算出的结果。
            "close_target_rad": args.gripper_close_target_rad,
# 【L2424】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2425】语法拆解：这是字典键值对：`"requested_pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`requested_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `requested_pregrasp_distance_m`，它表示“写出完整机器可读报告”中的 `requested_pregrasp_distance_m` 数据；字段值来自 `requested_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "requested_pregrasp_distance_m": requested_pregrasp_distance_m,
# 【L2426】语法拆解：这是字典键值对：`"pregrasp_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`effective_pregrasp_distance_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `pregrasp_distance_m`，它表示“写出完整机器可读报告”中的 `pregrasp_distance_m` 数据；字段值来自 `effective_pregrasp_distance_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "pregrasp_distance_m": effective_pregrasp_distance_m,
# 【L2427】语法拆解：这是字典键值对：`"grasp_world_offset_x_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_x_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_x_m`，它表示“写出完整机器可读报告”中的 `grasp_world_offset_x_m` 数据；字段值来自 `args.grasp_world_offset_x_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
# 【L2428】语法拆解：这是字典键值对：`"grasp_world_offset_z_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_world_offset_z_m`。
# 【项目含义】定义字典/JSON 字段 `grasp_world_offset_z_m`，它表示“写出完整机器可读报告”中的 `grasp_world_offset_z_m` 数据；字段值来自 `args.grasp_world_offset_z_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
# 【L2429】语法拆解：这是字典键值对：`"robot_base_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`robot_base_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `robot_base_position_m`，它表示“写出完整机器可读报告”中的 `robot_base_position_m` 数据；字段值来自 `robot_base_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "robot_base_position_m": robot_base_position.tolist(),
# 【L2430】语法拆解：这是字典键值对：`"grasp_orientation_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`grasp_orientation_mode`。
# 【项目含义】定义字典/JSON 字段 `grasp_orientation_mode`，它表示“写出完整机器可读报告”中的 `grasp_orientation_mode` 数据；字段值来自 `args.grasp_orientation_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "grasp_orientation_mode": args.grasp_orientation_mode,
# 【L2431】语法拆解：这是字典键值对：`"top_down_yaw_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_yaw_rad`。
# 【项目含义】定义字典/JSON 字段 `top_down_yaw_rad`，它表示“写出完整机器可读报告”中的 `top_down_yaw_rad` 数据；字段值来自 `args.top_down_yaw_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_yaw_rad": args.top_down_yaw_rad,
# 【L2432】语法拆解：这是字典键值对：`"top_down_tilt_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_tilt_rad`。
# 【项目含义】定义字典/JSON 字段 `top_down_tilt_rad`，它表示“写出完整机器可读报告”中的 `top_down_tilt_rad` 数据；字段值来自 `args.top_down_tilt_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_tilt_rad": args.top_down_tilt_rad,
# 【L2433】语法拆解：这是字典键值对：`"top_down_ik_multistart"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_ik_multistart`。
# 【项目含义】定义字典/JSON 字段 `top_down_ik_multistart`，它表示“写出完整机器可读报告”中的 `top_down_ik_multistart` 数据；字段值来自 `args.top_down_ik_multistart`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_ik_multistart": args.top_down_ik_multistart,
# 【L2434】语法拆解：这是字典键值对：`"top_down_ik_seed_index"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`top_down_ik_seed_index` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `top_down_ik_seed_index`，它表示“写出完整机器可读报告”中的 `top_down_ik_seed_index` 数据；字段值来自 `top_down_ik_seed_index`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_ik_seed_index": top_down_ik_seed_index,
# 【L2435】语法拆解：这是字典键值对：`"top_down_blend"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`top_down_blend`。
# 【项目含义】定义字典/JSON 字段 `top_down_blend`，它表示“写出完整机器可读报告”中的 `top_down_blend` 数据；字段值来自 `args.top_down_blend`，因此保存/传递的是这个表达式当前计算出的结果。
        "top_down_blend": args.top_down_blend,
# 【L2436】语法拆解：这是字典键值对：`"reference_block_from_link_local_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`reference_block_from_link_local` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `reference_block_from_link_local_m`，它表示“写出完整机器可读报告”中的 `reference_block_from_link_local_m` 数据；字段值来自 `reference_block_from_link_local.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
# 【L2437】语法拆解：这是字典键值对：`"lift_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`lift_mode`。
# 【项目含义】定义字典/JSON 字段 `lift_mode`，它表示“写出完整机器可读报告”中的 `lift_mode` 数据；字段值来自 `args.lift_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_mode": args.lift_mode,
# 【L2438】语法拆解：这是字典键值对：`"cartesian_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`cartesian_lift_height_m`。
# 【项目含义】定义字典/JSON 字段 `cartesian_lift_height_m`，它表示“写出完整机器可读报告”中的 `cartesian_lift_height_m` 数据；字段值来自 `args.cartesian_lift_height_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_lift_height_m": args.cartesian_lift_height_m,
# 【L2439】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `development_assistance`，它表示“写出完整机器可读报告”中的 `development_assistance` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "development_assistance": {
# 【L2440】语法拆解：这是字典键值对：`"initialized_at_grasp"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`initialize_at_grasp`。
# 【项目含义】定义字典/JSON 字段 `initialized_at_grasp`，它表示“写出完整机器可读报告”中的 `initialized_at_grasp` 数据；字段值来自 `args.initialize_at_grasp`，因此保存/传递的是这个表达式当前计算出的结果。
            "initialized_at_grasp": args.initialize_at_grasp,
# 【L2441】语法拆解：这是字典键值对：`"arm_gravity_disabled_during_approach"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_during_approach`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_during_approach`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_during_approach` 数据；字段值来自 `args.disable_arm_gravity_during_approach`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
# 【L2442】语法拆解：这是字典键值对：`"arm_gravity_disabled_through_transport"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`disable_arm_gravity_through_transport`。
# 【项目含义】定义字典/JSON 字段 `arm_gravity_disabled_through_transport`，它表示“写出完整机器可读报告”中的 `arm_gravity_disabled_through_transport` 数据；字段值来自 `args.disable_arm_gravity_through_transport`，因此保存/传递的是这个表达式当前计算出的结果。
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
# 【L2443】语法拆解：这是字典键值对：`"source_block_gravity_disabled_until_close"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`not args.natural_source_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_block_gravity_disabled_until_close`，它表示“写出完整机器可读报告”中的 `source_block_gravity_disabled_until_close` 数据；字段值来自 `not args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_block_gravity_disabled_until_close": not args.natural_source_gravity,
# 【L2444】语法拆解：这是字典键值对：`"target_platform_collision_enable_stage"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`target_collision_enable_stage`。
# 【项目含义】定义字典/JSON 字段 `target_platform_collision_enable_stage`，它表示“写出完整机器可读报告”中的 `target_platform_collision_enable_stage` 数据；字段值来自 `args.target_collision_enable_stage`，因此保存/传递的是这个表达式当前计算出的结果。
            "target_platform_collision_enable_stage": args.target_collision_enable_stage,
# 【L2445】语法拆解：这是字典键值对：`"release_separation_assist_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.0 if args.unassisted_release else args.release_separation_assist_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `release_separation_assist_m`，它表示“写出完整机器可读报告”中的 `release_separation_assist_m` 数据；字段值来自 `0.0 if args.unassisted_release else args.release_separation_assist_m`，因此保存/传递的是这个表达式当前计算出的结果。
            "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2446】语法拆解：这是字典键值对：`"release_downward_speed_assist_m_s"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `release_downward_speed_assist_m_s`，它表示“写出完整机器可读报告”中的 `release_downward_speed_assist_m_s` 数据；字段值来自 `0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S`，因此保存/传递的是这个表达式当前计算出的结果。
            "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2447】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2448】语法拆解：这是字典键值对：`"block_mass_kg"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`BLOCK_MASS_KG` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `block_mass_kg`，它表示“写出完整机器可读报告”中的 `block_mass_kg` 数据；字段值来自 `BLOCK_MASS_KG`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_mass_kg": BLOCK_MASS_KG,
# 【L2449】语法拆解：这是字典键值对：`"block_size_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `BLOCK_SIZE`。
# 【项目含义】定义字典/JSON 字段 `block_size_m`，它表示“写出完整机器可读报告”中的 `block_size_m` 数据；字段值来自 `list(BLOCK_SIZE)`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_size_m": list(BLOCK_SIZE),
# 【L2450】语法拆解：这是字典键值对：`"moving_gripper_gravity_disabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`not args.enable_moving_gripper_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `moving_gripper_gravity_disabled`，它表示“写出完整机器可读报告”中的 `moving_gripper_gravity_disabled` 数据；字段值来自 `not args.enable_moving_gripper_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
# 【L2451】语法拆解：这是字典键值对：`"gravity_disabled_body_paths"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`isolated_paths` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `gravity_disabled_body_paths`，它表示“写出完整机器可读报告”中的 `gravity_disabled_body_paths` 数据；字段值来自 `isolated_paths`，因此保存/传递的是这个表达式当前计算出的结果。
        "gravity_disabled_body_paths": isolated_paths,
# 【L2452】语法拆解：这是字典键值对：`"source_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `source_block_position_m`，它表示“写出完整机器可读报告”中的 `source_block_position_m` 数据；字段值来自 `source_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_position_m": source_block_position.tolist(),
# 【L2453】语法拆解：这是字典键值对：`"source_offset_xy_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：最外层方括号创建列表；逗号分隔列表元素；若内部含 `for`，则是列表推导式。
# 【项目含义】定义字典/JSON 字段 `source_offset_xy_m`，它表示“写出完整机器可读报告”中的 `source_offset_xy_m` 数据；字段值来自 `[args.source_offset_x_m, args.source_offset_y_m]`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_offset_xy_m": [args.source_offset_x_m, args.source_offset_y_m],
# 【L2454】语法拆解：这是字典键值对：`"target_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_block_position_m`，它表示“写出完整机器可读报告”中的 `target_block_position_m` 数据；字段值来自 `target_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_block_position_m": target_block_position.tolist(),
# 【L2455】语法拆解：这是字典键值对：`"expected_lift_translation_from_fk_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`expected_lift_translation` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `expected_lift_translation_from_fk_m`，它表示“写出完整机器可读报告”中的 `expected_lift_translation_from_fk_m` 数据；字段值来自 `expected_lift_translation.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_lift_translation_from_fk_m": expected_lift_translation.tolist(),
# 【L2456】语法拆解：这是字典键值对：`"expected_source_lift_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`expected_source_lift_block_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `expected_source_lift_block_position_m`，它表示“写出完整机器可读报告”中的 `expected_source_lift_block_position_m` 数据；字段值来自 `expected_source_lift_block_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_source_lift_block_position_m": expected_source_lift_block_position.tolist(),
# 【L2457】语法拆解：这是字典键值对：`"expected_release_position_before_drop_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_release_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `expected_release_position_before_drop_m`，它表示“写出完整机器可读报告”中的 `expected_release_position_before_drop_m` 数据；字段值来自 `target_release_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "expected_release_position_before_drop_m": target_release_position.tolist(),
# 【L2458】语法拆解：这是字典键值对：`"source_block_quaternion_wxyz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_block_quaternion` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `source_block_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `source_block_quaternion_wxyz` 数据；字段值来自 `source_block_quaternion.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_quaternion_wxyz": source_block_quaternion.tolist(),
# 【L2459】语法拆解：这是字典键值对：`"target_block_quaternion_wxyz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_block_quaternion` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_block_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `target_block_quaternion_wxyz` 数据；字段值来自 `target_block_quaternion.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_block_quaternion_wxyz": target_block_quaternion.tolist(),
# 【L2460】语法拆解：这是字典键值对：`"source_block_temporarily_gravity_disabled"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`not args.natural_source_gravity` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_block_temporarily_gravity_disabled`，它表示“写出完整机器可读报告”中的 `source_block_temporarily_gravity_disabled` 数据；字段值来自 `not args.natural_source_gravity`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_block_temporarily_gravity_disabled": not args.natural_source_gravity,
# 【L2461】语法拆解：这是字典键值对：`"source_platform_size_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_platform_size_m`，它表示“写出完整机器可读报告”中的 `source_platform_size_m` 数据；字段值来自 `list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
# 【L2462】语法拆解：这是字典键值对：`"gravity_enabled_after_gripper_close"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `gravity_enabled_after_gripper_close`，它表示“写出完整机器可读报告”中的 `gravity_enabled_after_gripper_close` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "gravity_enabled_after_gripper_close": True,
# 【L2463】语法拆解：这是字典键值对：`"target_platform_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`target_platform_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `target_platform_position_m`，它表示“写出完整机器可读报告”中的 `target_platform_position_m` 数据；字段值来自 `target_platform_position.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_position_m": target_platform_position.tolist(),
# 【L2464】语法拆解：这是字典键值对：`"target_platform_size_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`list` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `target_platform_size`。
# 【项目含义】定义字典/JSON 字段 `target_platform_size_m`，它表示“写出完整机器可读报告”中的 `target_platform_size_m` 数据；字段值来自 `list(target_platform_size)`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_size_m": list(target_platform_size),
# 【L2465】语法拆解：这是字典键值对：`"target_support_mode"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`target_support_mode`。
# 【项目含义】定义字典/JSON 字段 `target_support_mode`，它表示“写出完整机器可读报告”中的 `target_support_mode` 数据；字段值来自 `args.target_support_mode`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_support_mode": args.target_support_mode,
# 【L2466】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `target_platform_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `target_platform_quaternion_wxyz` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_quaternion_wxyz": (
# 【L2467】语法拆解：`list(target_platform_orientation) if target_platform_orientation is not None else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `list(target_platform_orientation) if target_platform_orientation is not None else None` 接入当前完整语句；`target_platform_orientation` 表示目标、支撑平台相关值。在“写出完整机器可读报告”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            list(target_platform_orientation) if target_platform_orientation is not None else None
# 【L2468】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2469】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `target_platform_collision_enabled_after_transfer`，它表示“写出完整机器可读报告”中的 `target_platform_collision_enabled_after_transfer` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_platform_collision_enabled_after_transfer": (
# 【L2470】语法拆解：表达式 `args.target_collision_enable_stage == "after_transfer"` 使用运算符 `==`；Python 先计算括号/索引/属性，再按运算符优先级组合结果。
# 【项目含义】把比较条件 `args.target_collision_enable_stage == "after_transfer"` 接到上一行尚未结束的布尔表达式；`target_collision_enable_stage` 表示目标相关值；`after_transfer` 表示本功能块中的 `after_transfer` 值。比较结果共同决定“写出完整机器可读报告”是否通过。
            args.target_collision_enable_stage == "after_transfer"
# 【L2471】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2472】语法拆解：这是字典键值对：`"target_collision_enable_stage"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`target_collision_enable_stage`。
# 【项目含义】定义字典/JSON 字段 `target_collision_enable_stage`，它表示“写出完整机器可读报告”中的 `target_collision_enable_stage` 数据；字段值来自 `args.target_collision_enable_stage`，因此保存/传递的是这个表达式当前计算出的结果。
        "target_collision_enable_stage": args.target_collision_enable_stage,
# 【L2473】语法拆解：这是字典键值对：`"release_unassisted"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`unassisted_release`。
# 【项目含义】定义字典/JSON 字段 `release_unassisted`，它表示“写出完整机器可读报告”中的 `release_unassisted` 数据；字段值来自 `args.unassisted_release`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_unassisted": args.unassisted_release,
# 【L2474】语法拆解：这是字典键值对：`"place_descent"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`place_descent`。
# 【项目含义】定义字典/JSON 字段 `place_descent`，它表示“写出完整机器可读报告”中的 `place_descent` 数据；字段值来自 `args.place_descent`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_descent": args.place_descent,
# 【L2475】语法拆解：这是字典键值对：`"place_descent_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args.place_descent_distance_m if args.place_descent else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `place_descent_distance_m`，它表示“写出完整机器可读报告”中的 `place_descent_distance_m` 数据；字段值来自 `args.place_descent_distance_m if args.place_descent else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_descent_distance_m": args.place_descent_distance_m if args.place_descent else None,
# 【L2476】语法拆解：这是字典键值对：`"place_waypoint_steps"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`args.place_waypoint_steps if args.place_descent else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `place_waypoint_steps`，它表示“写出完整机器可读报告”中的 `place_waypoint_steps` 数据；字段值来自 `args.place_waypoint_steps if args.place_descent else None`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_waypoint_steps": args.place_waypoint_steps if args.place_descent else None,
# 【L2477】语法拆解：这是字典键值对：`"place_max_command_step_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`place_max_command_step_rad` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `place_max_command_step_rad`，它表示“写出完整机器可读报告”中的 `place_max_command_step_rad` 数据；字段值来自 `place_max_command_step_rad`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_max_command_step_rad": place_max_command_step_rad,
# 【L2478】语法拆解：这是字典键值对：`"place_ik_uses_base_rotation_symmetry"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`True` 是布尔常量，分别表示逻辑真或假。
# 【项目含义】定义字典/JSON 字段 `place_ik_uses_base_rotation_symmetry`，它表示“写出完整机器可读报告”中的 `place_ik_uses_base_rotation_symmetry` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_ik_uses_base_rotation_symmetry": True,
# 【L2479】语法拆解：这是字典键值对：`"pre_place_block_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`pre_place_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `pre_place_block_position_m`，它表示“写出完整机器可读报告”中的 `pre_place_block_position_m` 数据；字段值来自 `pre_place_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_place_block_position_m": pre_place_position.detach().cpu().tolist(),
# 【L2480】语法拆解：这是字典键值对：`"pre_place_link_6_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`pre_place_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `pre_place_link_6_position_m`，它表示“写出完整机器可读报告”中的 `pre_place_link_6_position_m` 数据；字段值来自 `pre_place_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_place_link_6_position_m": pre_place_link_6_position.detach().cpu().tolist(),
# 【L2481】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `place_actual_block_translation_m`，它表示“写出完整机器可读报告”中的 `place_actual_block_translation_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_block_translation_m": (
# 【L2482】语法拆解：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】对 `(pre_release_position - pre_place_position)` 调用 `detach().cpu().tolist()`：调用 `(pre_release_position - pre_place_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            (pre_release_position - pre_place_position).detach().cpu().tolist()
# 【L2483】语法拆解：`if` 要求条件 `args.place_descent` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.place_descent` 是否成立；`place_descent` 表示本功能块中的 `place_descent` 值
            if args.place_descent
# 【L2484】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2485】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2486】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `place_actual_link_6_position_m`，它表示“写出完整机器可读报告”中的 `place_actual_link_6_position_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_link_6_position_m": (
# 【L2487】语法拆解：`place_actual_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】对 `place_actual_link_6_position` 调用 `detach().cpu().tolist()`：调用 `place_actual_link_6_position` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            place_actual_link_6_position.detach().cpu().tolist()
# 【L2488】语法拆解：`if` 要求条件 `place_actual_link_6_position is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `place_actual_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_link_6_position is not None
# 【L2489】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2490】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2491】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `place_commanded_link_6_position_m`，它表示“写出完整机器可读报告”中的 `place_commanded_link_6_position_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_commanded_link_6_position_m": (
# 【L2492】语法拆解：`place_commanded_link_6_position` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `place_commanded_link_6_position` 调用 `tolist()`：调用 `place_commanded_link_6_position` 提供的 `tolist` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            place_commanded_link_6_position.tolist()
# 【L2493】语法拆解：`if` 要求条件 `place_commanded_link_6_position is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `place_commanded_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_commanded_link_6_position is not None
# 【L2494】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2495】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2496】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `place_actual_link_translation_m`，它表示“写出完整机器可读报告”中的 `place_actual_link_translation_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_actual_link_translation_m": (
# 【L2497】语法拆解：最外层圆括号用于组合表达式或创建元组；只有逗号存在时才构成元组。
# 【项目含义】对 `(place_actual_link_6_position - pre_place_link_6_position)` 调用 `detach().cpu().tolist()`：调用 `(place_actual_link_6_position - pre_place_link_6_position)` 提供的 `detach` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            (place_actual_link_6_position - pre_place_link_6_position).detach().cpu().tolist()
# 【L2498】语法拆解：`if` 要求条件 `place_actual_link_6_position is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `place_actual_link_6_position is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_link_6_position is not None
# 【L2499】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2500】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2501】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `place_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `place_max_arm_joint_error_rad` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "place_max_arm_joint_error_rad": (
# 【L2502】语法拆解：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(place_actual_arm - place_waypoints[-1]))`。
# 【项目含义】对 `float(np` 调用 `max(np.abs(place_actual_arm - place_waypoints[-1])))`：调用 `float(np` 提供的 `max` 操作。本行产生的修改/返回值服务于“写出完整机器可读报告”。
            float(np.max(np.abs(place_actual_arm - place_waypoints[-1])))
# 【L2503】语法拆解：`if` 要求条件 `place_actual_arm is not None` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】检查 `place_actual_arm is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if place_actual_arm is not None
# 【L2504】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `None`；它让“写出完整机器可读报告”在可选数据缺失时仍有明确结果。
            else None
# 【L2505】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2506】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `release_clearance_m`，它表示“写出完整机器可读报告”中的 `release_clearance_m` 数据；字段值来自 `(`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_clearance_m": (
# 【L2507】语法拆解：`args.release_clearance_m if args.unassisted_release and not args.place_descent else None` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】把表达式/参数 `args.release_clearance_m if args.unassisted_release and not args.place_descent else None` 接入当前完整语句；`release_clearance_m` 表示本功能块中的 `release_clearance_m` 值；`unassisted_release` 表示本功能块中的 `unassisted_release` 值；`place_descent` 表示本功能块中的 `place_descent` 值。在“写出完整机器可读报告”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            args.release_clearance_m if args.unassisted_release and not args.place_descent else None
# 【L2508】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        ),
# 【L2509】语法拆解：这是字典键值对：`"release_downward_speed_assist_m_s"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `release_downward_speed_assist_m_s`，它表示“写出完整机器可读报告”中的 `release_downward_speed_assist_m_s` 数据；字段值来自 `0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
# 【L2510】语法拆解：这是字典键值对：`"release_separation_assist_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.0 if args.unassisted_release else args.release_separation_assist_m` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `release_separation_assist_m`，它表示“写出完整机器可读报告”中的 `release_separation_assist_m` 数据；字段值来自 `0.0 if args.unassisted_release else args.release_separation_assist_m`，因此保存/传递的是这个表达式当前计算出的结果。
        "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
# 【L2511】语法拆解：这是字典键值对：`"cartesian_retreat_distances_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`retreat_distances` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `cartesian_retreat_distances_m`，它表示“写出完整机器可读报告”中的 `cartesian_retreat_distances_m` 数据；字段值来自 `retreat_distances.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_retreat_distances_m": retreat_distances.tolist(),
# 【L2512】语法拆解：这是字典键值对：`"cartesian_pregrasp_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`pregrasp_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `cartesian_pregrasp_joint_position_rad`，它表示“写出完整机器可读报告”中的 `cartesian_pregrasp_joint_position_rad` 数据；字段值来自 `pregrasp_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
# 【L2513】语法拆解：这是字典键值对：`"settled_source_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`settled_source_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `settled_source_position_m`，它表示“写出完整机器可读报告”中的 `settled_source_position_m` 数据；字段值来自 `settled_source_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "settled_source_position_m": settled_source_np.tolist(),
# 【L2514】语法拆解：这是字典键值对：`"settled_source_quaternion_wxyz"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`settled_source_quaternion` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `settled_source_quaternion_wxyz`，它表示“写出完整机器可读报告”中的 `settled_source_quaternion_wxyz` 数据；字段值来自 `settled_source_quaternion.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
# 【L2515】语法拆解：这是字典键值对：`"closed_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `closed_position_m`，它表示“写出完整机器可读报告”中的 `closed_position_m` 数据；字段值来自 `closed_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_position_m": closed_np.tolist(),
# 【L2516】语法拆解：这是字典键值对：`"lifted_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lifted_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lifted_position_m`，它表示“写出完整机器可读报告”中的 `lifted_position_m` 数据；字段值来自 `lifted_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lifted_position_m": lifted_np.tolist(),
# 【L2517】语法拆解：这是字典键值对：`"pre_release_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`pre_release_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `pre_release_position_m`，它表示“写出完整机器可读报告”中的 `pre_release_position_m` 数据；字段值来自 `pre_release_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "pre_release_position_m": pre_release_np.tolist(),
# 【L2518】语法拆解：这是字典键值对：`"released_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`released_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `released_position_m`，它表示“写出完整机器可读报告”中的 `released_position_m` 数据；字段值来自 `released_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "released_position_m": released_np.tolist(),
# 【L2519】语法拆解：这是字典键值对：`"final_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_np` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `final_position_m`，它表示“写出完整机器可读报告”中的 `final_position_m` 数据；字段值来自 `final_np.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_position_m": final_np.tolist(),
# 【L2520】语法拆解：这是字典键值对：`"source_to_target_xy_distance_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`source_to_target_distance` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `source_to_target_xy_distance_m`，它表示“写出完整机器可读报告”中的 `source_to_target_xy_distance_m` 数据；字段值来自 `source_to_target_distance`，因此保存/传递的是这个表达式当前计算出的结果。
        "source_to_target_xy_distance_m": source_to_target_distance,
# 【L2521】语法拆解：这是字典键值对：`"block_lift_height_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_height` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `block_lift_height_m`，它表示“写出完整机器可读报告”中的 `block_lift_height_m` 数据；字段值来自 `lift_height`，因此保存/传递的是这个表达式当前计算出的结果。
        "block_lift_height_m": lift_height,
# 【L2522】语法拆解：这是字典键值对：`"approach_max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_approach_arm - grasp_arm))`。
# 【项目含义】定义字典/JSON 字段 `approach_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `approach_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_approach_arm - grasp_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
# 【L2523】语法拆解：这是字典键值对：`"approach_l2_midpoint_to_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_to_block` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_to_block_center_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_to_block_center_m` 数据；字段值来自 `open_midpoint_to_block`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
# 【L2524】语法拆解：这是字典键值对：`"approach_l2_midpoint_world_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_world` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_world_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_world_m` 数据；字段值来自 `open_midpoint_world.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
# 【L2525】语法拆解：这是字典键值对：`"approach_l2_midpoint_minus_block_center_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_midpoint_minus_block` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `approach_l2_midpoint_minus_block_center_m`，它表示“写出完整机器可读报告”中的 `approach_l2_midpoint_minus_block_center_m` 数据；字段值来自 `open_midpoint_minus_block.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
# 【L2526】语法拆解：这是字典键值对：`"approach_pad_center_world_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_pad_center_world_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_pad_center_world_by_body_m`，它表示“写出完整机器可读报告”中的 `approach_pad_center_world_by_body_m` 数据；字段值来自 `open_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
# 【L2527】语法拆解：这是字典键值对：`"approach_pad_center_minus_block_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`open_pad_center_minus_block_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `approach_pad_center_minus_block_by_body_m`，它表示“写出完整机器可读报告”中的 `approach_pad_center_minus_block_by_body_m` 数据；字段值来自 `open_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
# 【L2528】语法拆解：这是字典键值对：`"closed_pad_center_world_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_pad_center_world_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_pad_center_world_by_body_m`，它表示“写出完整机器可读报告”中的 `closed_pad_center_world_by_body_m` 数据；字段值来自 `closed_pad_center_world_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
# 【L2529】语法拆解：这是字典键值对：`"closed_pad_center_minus_block_by_body_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_pad_center_minus_block_by_body` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_pad_center_minus_block_by_body_m`，它表示“写出完整机器可读报告”中的 `closed_pad_center_minus_block_by_body_m` 数据；字段值来自 `closed_pad_center_minus_block_by_body`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
# 【L2530】语法拆解：这是字典键值对：`"closed_l2_tip_gap_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_l2_gap` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `closed_l2_tip_gap_m`，它表示“写出完整机器可读报告”中的 `closed_l2_tip_gap_m` 数据；字段值来自 `closed_l2_gap`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_l2_tip_gap_m": closed_l2_gap,
# 【L2531】语法拆解：这是字典键值对：`"closed_gripper_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_gripper_joint_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_gripper_joint_position_rad`，它表示“写出完整机器可读报告”中的 `closed_gripper_joint_position_rad` 数据；字段值来自 `closed_gripper_joint_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
# 【L2532】语法拆解：这是字典键值对：`"close_left_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_left_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_left_finger_contact_force_n`，它表示“写出完整机器可读报告”中的 `close_left_finger_contact_force_n` 数据；字段值来自 `close_left_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
# 【L2533】语法拆解：这是字典键值对：`"close_right_finger_contact_force_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_right_finger_contact_force_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_right_finger_contact_force_n`，它表示“写出完整机器可读报告”中的 `close_right_finger_contact_force_n` 数据；字段值来自 `close_right_finger_contact_force_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
# 【L2534】语法拆解：这是字典键值对：`"close_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_contact_force_by_body_n` 数据；字段值来自 `close_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_contact_force_by_body_n": close_contact_force_by_body_n,
# 【L2535】语法拆解：这是字典键值对：`"close_current_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_current_contact_force_by_body_n` 数据；字段值来自 `close_current_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
# 【L2536】语法拆解：这是字典键值对：`"close_recent_mean_contact_force_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_recent_mean_contact_force_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_recent_mean_contact_force_by_body_n`，它表示“写出完整机器可读报告”中的 `close_recent_mean_contact_force_by_body_n` 数据；字段值来自 `close_recent_mean_contact_force_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
# 【L2537】语法拆解：这是字典键值对：`"close_current_contact_force_vector_by_body_n"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`close_current_contact_force_vector_by_body_n` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `close_current_contact_force_vector_by_body_n`，它表示“写出完整机器可读报告”中的 `close_current_contact_force_vector_by_body_n` 数据；字段值来自 `close_current_contact_force_vector_by_body_n`，因此保存/传递的是这个表达式当前计算出的结果。
        "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
# 【L2538】语法拆解：这是字典键值对：`"closed_link_6_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`closed_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `closed_link_6_position_m`，它表示“写出完整机器可读报告”中的 `closed_link_6_position_m` 数据；字段值来自 `closed_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
# 【L2539】语法拆解：这是字典键值对：`"lifted_link_6_position_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lifted_link_6_position` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `lifted_link_6_position_m`，它表示“写出完整机器可读报告”中的 `lifted_link_6_position_m` 数据；字段值来自 `lifted_link_6_position.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
# 【L2540】语法拆解：这是字典键值对：`"actual_lift_link_translation_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_lift_link_translation` 是模块/对象，点号 `.` 从中取出 `detach` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `).cpu().tolist(`。
# 【项目含义】定义字典/JSON 字段 `actual_lift_link_translation_m`，它表示“写出完整机器可读报告”中的 `actual_lift_link_translation_m` 数据；字段值来自 `actual_lift_link_translation.detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
# 【L2541】语法拆解：这是字典键值对：`"lift_max_arm_joint_error_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`float` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `np.max(np.abs(actual_lift_arm - lift_arm))`。
# 【项目含义】定义字典/JSON 字段 `lift_max_arm_joint_error_rad`，它表示“写出完整机器可读报告”中的 `lift_max_arm_joint_error_rad` 数据；字段值来自 `float(np.max(np.abs(actual_lift_arm - lift_arm)))`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
# 【L2542】语法拆解：这是字典键值对：`"lift_actual_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`actual_lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lift_actual_arm_joint_position_rad`，它表示“写出完整机器可读报告”中的 `lift_actual_arm_joint_position_rad` 数据；字段值来自 `actual_lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
# 【L2543】语法拆解：这是字典键值对：`"lift_target_arm_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`lift_arm` 是模块/对象，点号 `.` 从中取出 `tolist` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】定义字典/JSON 字段 `lift_target_arm_joint_position_rad`，它表示“写出完整机器可读报告”中的 `lift_target_arm_joint_position_rad` 数据；字段值来自 `lift_arm.tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "lift_target_arm_joint_position_rad": lift_arm.tolist(),
# 【L2544】语法拆解：这是字典键值对：`"final_target_xy_error_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_target_xy_error` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_target_xy_error_m`，它表示“写出完整机器可读报告”中的 `final_target_xy_error_m` 数据；字段值来自 `final_target_xy_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_xy_error_m": final_target_xy_error,
# 【L2545】语法拆解：这是字典键值对：`"final_target_position_error_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_target_position_error` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_target_position_error_m`，它表示“写出完整机器可读报告”中的 `final_target_position_error_m` 数据；字段值来自 `final_target_position_error`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_target_position_error_m": final_target_position_error,
# 【L2546】语法拆解：这是字典键值对：`"post_release_drift_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`release_drift` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `post_release_drift_m`，它表示“写出完整机器可读报告”中的 `post_release_drift_m` 数据；字段值来自 `release_drift`，因此保存/传递的是这个表达式当前计算出的结果。
        "post_release_drift_m": release_drift,
# 【L2547】语法拆解：这是字典键值对：`"final_l2_tip_gap_m"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`final_l2_tip_gap` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_l2_tip_gap_m`，它表示“写出完整机器可读报告”中的 `final_l2_tip_gap_m` 数据；字段值来自 `final_l2_tip_gap`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_l2_tip_gap_m": final_l2_tip_gap,
# 【L2548】语法拆解：这是字典键值对：`"final_gripper_joint_position_rad"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist()` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `final_gripper_joint_position_rad`，它表示“写出完整机器可读报告”中的 `final_gripper_joint_position_rad` 数据；字段值来自 `robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist()`，因此保存/传递的是这个表达式当前计算出的结果。
        "final_gripper_joint_position_rad": robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist(),
# 【L2549】语法拆解：这是字典键值对：`"all_states_finite"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`all_states_finite` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】定义字典/JSON 字段 `all_states_finite`，它表示“写出完整机器可读报告”中的 `all_states_finite` 数据；字段值来自 `all_states_finite`，因此保存/传递的是这个表达式当前计算出的结果。
        "all_states_finite": all_states_finite,
# 【L2550】语法拆解：引号包住字典键，键后的冒号连接对应值；末尾逗号把这一键值对与下一个字段分开。
# 【项目含义】定义字典/JSON 字段 `criteria`，它表示“写出完整机器可读报告”中的 `criteria` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "criteria": {
# 【L2551】语法拆解：这是字典键值对：`"source_to_target_xy_distance_m_gt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `source_to_target_xy_distance_m_gt`，它表示“写出完整机器可读报告”中的 `source_to_target_xy_distance_m_gt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_to_target_xy_distance_m_gt": 0.12,
# 【L2552】语法拆解：这是字典键值对：`"block_lift_height_m_gt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.02` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `block_lift_height_m_gt`，它表示“写出完整机器可读报告”中的 `block_lift_height_m_gt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "block_lift_height_m_gt": 0.02,
# 【L2553】语法拆解：这是字典键值对：`"final_target_xy_error_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_target_xy_error_m_lt`，它表示“写出完整机器可读报告”中的 `final_target_xy_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_xy_error_m_lt": 0.05,
# 【L2554】语法拆解：这是字典键值对：`"final_target_position_error_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.05` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_target_position_error_m_lt`，它表示“写出完整机器可读报告”中的 `final_target_position_error_m_lt` 数据；字段值来自 `0.05`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_target_position_error_m_lt": 0.05,
# 【L2555】语法拆解：这是字典键值对：`"post_release_drift_m_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.02` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `post_release_drift_m_lt`，它表示“写出完整机器可读报告”中的 `post_release_drift_m_lt` 数据；字段值来自 `0.02`，因此保存/传递的是这个表达式当前计算出的结果。
            "post_release_drift_m_lt": 0.02,
# 【L2556】语法拆解：这是字典键值对：`"final_gripper_joint_position_rad_lt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.12` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_gripper_joint_position_rad_lt`，它表示“写出完整机器可读报告”中的 `final_gripper_joint_position_rad_lt` 数据；字段值来自 `0.12`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_gripper_joint_position_rad_lt": 0.12,
# 【L2557】语法拆解：这是字典键值对：`"final_l2_tip_gap_m_gt"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`0.06` 是直接写在源码中的数值常量。
# 【项目含义】定义字典/JSON 字段 `final_l2_tip_gap_m_gt`，它表示“写出完整机器可读报告”中的 `final_l2_tip_gap_m_gt` 数据；字段值来自 `0.06`，因此保存/传递的是这个表达式当前计算出的结果。
            "final_l2_tip_gap_m_gt": 0.06,
# 【L2558】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
        },
# 【L2559】语法拆解：这是字典键值对：`"limitation"` 是字符串键，键后的冒号 `:` 连接它的值；末尾逗号表示字典还有后续字段。值表达式从内向外执行：`"The collision pads and scripted waypoints still require physical calibration."` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】定义字典/JSON 字段 `limitation`，它表示“写出完整机器可读报告”中的 `limitation` 数据；字段值来自 `"The collision pads and scripted waypoints still require physical calibration."`，因此保存/传递的是这个表达式当前计算出的结果。
        "limitation": "The collision pads and scripted waypoints still require physical calibration.",
# 【L2560】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“写出完整机器可读报告”。
    }
# 【L2561】语法拆解：`output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L2562】语法拆解：`output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L2563】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“写出完整机器可读报告”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L2564】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True` 的当前值/文字输出到终端；它用于观察“写出完整机器可读报告”进度，也给日志留下可搜索证据。
    print(f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
# 【L2565】语法拆解：`return` 立即结束当前函数，并把右侧结果交回调用者；右侧语法为：`0 if passed else 1` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】结束当前函数并把 `0 if passed else 1` 交回调用者；这个值的含义是：计算表达式 `0 if passed else 1`；`passed` 表示当前单条任务或整套评测是否满足所有硬性门槛。
    return 0 if passed else 1
# 【L2566】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写出完整机器可读报告”中的逻辑段，让结构更容易看清。

# 【L2567】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“写出完整机器可读报告”中的逻辑段，让结构更容易看清。

```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“写出完整机器可读报告”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。

## 模块 23：捕获异常、关闭 Isaac Sim、返回退出码（源码第 2568-2609 行）

### 5.A 数据流位置

- 上游：模块 22“写出完整机器可读报告”。
- 本模块：捕获异常、关闭 Isaac Sim、返回退出码。
- 下游：处理结果继续交给磁盘输出、仿真/训练框架或调用者。

### 5.B 为什么需要这一组代码

这一组负责“捕获异常、关闭 Isaac Sim、返回退出码”。它服务于本文件要解决的总问题：RM65 六轴 IK 有等价分支跳变，4C2 抓取受接触和重力影响，π0.5 输出还可能越界；单看程序退出码也不能证明方块完成任务。 这一组的处理结果会参与：加入连续 IK、分阶段专家、同步记录、动作安全门、释放后置条件、确定性观测证据和几何成功判定。

### 5.C 本模块主要变量

- `report`：机器可读实验报告字典。
- `output`：输出文件路径。
- `record_stride_steps`：每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长。
- `episode_prompt`：当前 episode 发送给 π0.5 的自然语言任务指令。

### 5.D 本模块首次阅读要认识的调用

- `main(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `build_preflight_safety_failure_report(...)`：圆括号表示真正执行调用；项目自己定义或包装的函数；请结合本模块的函数卡和实际调用位置理解输入、处理和返回值。
- `os.environ.get(...)`：圆括号表示真正执行调用；按键读取字典/XML 属性；若不存在则使用代码给出的默认值。
- `args.output.parent.mkdir(...)`：圆括号表示真正执行调用；创建目录。
- `args.output.write_text(...)`：圆括号表示真正执行调用；把文本写入磁盘文件。
- `json.dumps(...)`：圆括号表示真正执行调用；把 Python 字典序列化成 JSON 文本。
- `traceback.print_exc(...)`：圆括号表示真正执行调用；来自标准库、第三方库或当前对象的方法；圆括号中的值是传入参数，返回值会交给外层表达式或左侧变量。
- `simulation_app.close(...)`：圆括号表示真正执行调用；关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。
- `SystemExit(...)`：圆括号表示真正执行调用；用指定退出码结束命令行程序。

### 5.F 这一模块的版本变化

- 当前第 2570-2601 行相对旧教学快照发生 `insert`：旧版 0 行，当前 32 行。 当前代码摘录：`except UnsafeIKBranchJumpError as error:` / `print("PICK_PLACE_STAGE=PREFLIGHT_SAFETY_REJECTION", flush=True)` / `report = build_preflight_safety_failure_report(` / `checkpoint_id=args.policy_checkpoint_id,`

### 5.G 逐行精读

```python
# 【L2568】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】开始执行可能抛错的“捕获异常、关闭 Isaac Sim、返回退出码”操作；后面的 `except/finally` 会记录失败或释放仿真、文件、网络资源。
try:
# 【L2569】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `exit_code`。右侧语法为：`main` 是被调用的函数/类名；圆括号为空，表示调用时不传实参。
# 【项目含义】得到 `exit_code`，它在本项目中表示本功能块中的 `exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `main()`；`main` 表示本功能块中的 `main` 值。
    exit_code = main()
# 【L2570】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `UnsafeIKBranchJumpError as error`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
except UnsafeIKBranchJumpError as error:
# 【L2571】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=PREFLIGHT_SAFETY_REJECTION"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=PREFLIGHT_SAFETY_REJECTION", flush=True` 的当前值/文字输出到终端；它用于观察“捕获异常、关闭 Isaac Sim、返回退出码”进度，也给日志留下可搜索证据。
    print("PICK_PLACE_STAGE=PREFLIGHT_SAFETY_REJECTION", flush=True)
# 【L2572】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `report`。右侧语法为：`build_preflight_safety_failure_report(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `build_preflight_safety_failure_report(`；`build_preflight_safety_failure_report` 表示报告相关值。
    report = build_preflight_safety_failure_report(
# 【L2573】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `checkpoint_id`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_checkpoint_id`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `checkpoint_id` 传入 `args.policy_checkpoint_id`；该参数在本项目中表示模型检查点相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        checkpoint_id=args.policy_checkpoint_id,
# 【L2574】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_noise_seed`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_noise_seed`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy_noise_seed` 传入 `args.policy_noise_seed`；该参数在本项目中表示策略相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        policy_noise_seed=args.policy_noise_seed,
# 【L2575】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `simulation_seed`。右侧语法为：`CONFIGURED_SIMULATION_SEED` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】给上一层函数/配置构造器的命名参数 `simulation_seed` 传入 `CONFIGURED_SIMULATION_SEED`；该参数在本项目中表示本功能块中的 `simulation_seed` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        simulation_seed=CONFIGURED_SIMULATION_SEED,
# 【L2576】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `prompt`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`episode_prompt`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `prompt` 传入 `args.episode_prompt`；该参数在本项目中表示本功能块中的 `prompt` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        prompt=args.episode_prompt,
# 【L2577】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `transfer_joint_1_rad`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`transfer_joint_1_rad`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `transfer_joint_1_rad` 传入 `args.transfer_joint_1_rad`；该参数在本项目中表示关节相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        transfer_joint_1_rad=args.transfer_joint_1_rad,
# 【L2578】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_offset_x_m`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`source_offset_x_m`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `source_offset_x_m` 传入 `args.source_offset_x_m`；该参数在本项目中表示源位置相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        source_offset_x_m=args.source_offset_x_m,
# 【L2579】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `source_offset_y_m`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`source_offset_y_m`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `source_offset_y_m` 传入 `args.source_offset_y_m`；该参数在本项目中表示源位置相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        source_offset_y_m=args.source_offset_y_m,
# 【L2580】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_max_action_chunks`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_max_action_chunks`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy_max_action_chunks` 传入 `args.policy_max_action_chunks`；该参数在本项目中表示策略、动作相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        policy_max_action_chunks=args.policy_max_action_chunks,
# 【L2581】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_execute_actions_per_chunk`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_execute_actions_per_chunk`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy_execute_actions_per_chunk` 传入 `args.policy_execute_actions_per_chunk`；该参数在本项目中表示策略、动作序列相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        policy_execute_actions_per_chunk=args.policy_execute_actions_per_chunk,
# 【L2582】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `record_stride_steps`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`record_stride_steps`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `record_stride_steps` 传入 `args.record_stride_steps`；该参数在本项目中表示每隔多少个 240 Hz 物理步保存一帧数据，也决定策略动作保持时长，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        record_stride_steps=args.record_stride_steps,
# 【L2583】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_release_required_consecutive_chunks`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `policy_release_required_consecutive_chunks`，它在本项目中表示策略相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        policy_release_required_consecutive_chunks=(
# 【L2584】语法拆解：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_release_required_consecutive_chunks`。
# 【项目含义】把表达式/参数 `args.policy_release_required_consecutive_chunks` 接入当前完整语句；`policy_release_required_consecutive_chunks` 表示策略相关值。在“捕获异常、关闭 Isaac Sim、返回退出码”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
            args.policy_release_required_consecutive_chunks
# 【L2585】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“捕获异常、关闭 Isaac Sim、返回退出码”。
        ),
# 【L2586】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_gripper_open_threshold`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_open_threshold`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy_gripper_open_threshold` 传入 `args.policy_gripper_open_threshold`；该参数在本项目中表示策略、夹爪相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        policy_gripper_open_threshold=args.policy_gripper_open_threshold,
# 【L2587】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `policy_gripper_actual_open_threshold`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`policy_gripper_actual_open_threshold`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `policy_gripper_actual_open_threshold` 传入 `args.policy_gripper_actual_open_threshold`；该参数在本项目中表示策略、夹爪、物理仿真实际值相关值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        policy_gripper_actual_open_threshold=args.policy_gripper_actual_open_threshold,
# 【L2588】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `python_hash_seed`。右侧语法为：`os.environ` 是模块/对象，点号 `.` 从中取出 `get` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PYTHONHASHSEED"`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `python_hash_seed` 传入 `os.environ.get("PYTHONHASHSEED")`；该参数在本项目中表示本功能块中的 `python_hash_seed` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        python_hash_seed=os.environ.get("PYTHONHASHSEED"),
# 【L2589】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `failure_reason`。右侧语法为：`"unsafe_ik_branch_jump"` 是字符串；成对引号界定文字内容，本身不代表变量名。
# 【项目含义】给上一层函数/配置构造器的命名参数 `failure_reason` 传入 `"unsafe_ik_branch_jump"`；该参数在本项目中表示本功能块中的 `failure_reason` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        failure_reason="unsafe_ik_branch_jump",
# 【L2590】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `failure_message`。右侧语法为：`str` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `error`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `failure_message` 传入 `str(error)`；该参数在本项目中表示本功能块中的 `failure_message` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        failure_message=str(error),
# 【L2591】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `pi05_used`。右侧语法为：`args` 是起始对象；每个点号 `.` 依次读取属性/成员：`pi05_closed_loop`。
# 【项目含义】给上一层函数/配置构造器的命名参数 `pi05_used` 传入 `args.pi05_closed_loop`；该参数在本项目中表示本功能块中的 `pi05_used` 值，会参与“捕获异常、关闭 Isaac Sim、返回退出码”。
        pi05_used=args.pi05_closed_loop,
# 【L2592】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `expert`。右侧语法为：`(` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】得到 `expert`，它在本项目中表示本功能块中的 `expert` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
        expert=(
# 【L2593】语法拆解：`None` 表示当前没有对象或没有可用结果。
# 【项目含义】声明/传入参数 `None`；在本项目中它表示本功能块中的 `None` 值。
            None
# 【L2594】语法拆解：`if` 要求条件 `args.pi05_closed_loop` 得到 True 才进入下面缩进块；末尾冒号打开分支，比较符和布尔连接词组成判断。
# 【项目含义】判断 `args.pi05_closed_loop` 是否成立；`pi05_closed_loop` 表示本功能块中的 `pi05_closed_loop` 值
            if args.pi05_closed_loop
# 【L2595】语法拆解：`else` 没有新条件；前面的 `if/elif` 全为 False 时进入这里；末尾冒号打开缩进块。
# 【项目含义】这是上一行条件表达式的备用值：条件不成立时使用 `"scripted Cartesian-approach and joint-space transport baseline"`；它让“捕获异常、关闭 Isaac Sim、返回退出码”在可选数据缺失时仍有明确结果。
            else "scripted Cartesian-approach and joint-space transport baseline"
# 【L2596】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“捕获异常、关闭 Isaac Sim、返回退出码”。
        ),
# 【L2597】语法拆解：右括号/花括号关闭前面某一行打开的函数调用、列表、字典或代码块；后面的逗号表示它仍是外层容器中的一个元素。
# 【项目含义】结束或闭合当前语法结构；它属于“捕获异常、关闭 Isaac Sim、返回退出码”。
    )
# 【L2598】语法拆解：`args.output.parent` 是模块/对象，点号 `.` 从中取出 `mkdir` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `parents=True`；第 2 个实参 `exist_ok=True`。
# 【项目含义】调用 `mkdir`：创建目录；本行实际操作 `args.output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    args.output.parent.mkdir(parents=True, exist_ok=True)
# 【L2599】语法拆解：`args.output` 是模块/对象，点号 `.` 从中取出 `write_text` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2) + "\n"`；第 2 个实参 `encoding="utf-8"`。
# 【项目含义】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")`。`output` 表示输出文件路径；`write_text` 表示本功能块中的 `write_text` 值。
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
# 【L2600】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `json.dumps(report, indent=2)`；第 2 个实参 `flush=True`。
# 【项目含义】把 `json.dumps(report, indent=2), flush=True` 的当前值/文字输出到终端；它用于观察“捕获异常、关闭 Isaac Sim、返回退出码”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2), flush=True)
# 【L2601】语法拆解：等号 `=` 是赋值：先完整计算右边，再把结果绑定/写入左边 `exit_code`。右侧语法为：`2` 是直接写在源码中的数值常量。
# 【项目含义】得到 `exit_code`，它在本项目中表示本功能块中的 `exit_code` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `2` 的结果保存下来，供当前功能块后续使用。
    exit_code = 2
# 【L2602】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】捕获 `BaseException`；把这一类可预期故障转换为本项目的错误记录、失败 case 或清理路径。
except BaseException:
# 【L2603】语法拆解：`print` 是被调用的函数/类名；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `"PICK_PLACE_STAGE=PYTHON_EXCEPTION"`；第 2 个实参 `flush=True`。
# 【项目含义】把 `"PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True` 的当前值/文字输出到终端；它用于观察“捕获异常、关闭 Isaac Sim、返回退出码”进度，也给日志留下可搜索证据。
    print("PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True)
# 【L2604】语法拆解：`traceback` 是模块/对象，点号 `.` 从中取出 `print_exc` 函数或方法；圆括号为空，表示调用时不传实参。
# 【项目含义】对 `traceback` 调用 `print_exc()`：调用 `traceback` 提供的 `print_exc` 操作。本行产生的修改/返回值服务于“捕获异常、关闭 Isaac Sim、返回退出码”。
    traceback.print_exc()
# 【L2605】语法拆解：`raise` 是当前表达式或参数；Python 会先求出其中更内层的括号、索引和函数调用，再把结果交给外层语句。
# 【项目含义】声明/传入参数 `raise`；在本项目中它表示本功能块中的 `raise` 值。
    raise
# 【L2606】语法拆解：这是异常处理结构：`try` 包住可能失败的代码，`except` 接住错误，`finally` 无论成功失败都执行；冒号打开对应缩进块。
# 【项目含义】无论前面的仿真/服务调用成功还是抛错都运行这里，确保 Isaac Sim、WebSocket 或临时文件被正确收尾。
finally:
# 【L2607】语法拆解：`simulation_app` 是模块/对象，点号 `.` 从中取出 `close` 函数或方法；圆括号表示执行调用，逗号把参数分开：第 1 个实参 `skip_cleanup=True`。
# 【项目含义】对 `simulation_app` 调用 `close(skip_cleanup=True)`：关闭仿真应用、文件或连接，释放 GPU、文件句柄或网络资源。本行产生的修改/返回值服务于“捕获异常、关闭 Isaac Sim、返回退出码”。
    simulation_app.close(skip_cleanup=True)
# 【L2608】语法拆解：这是空行，不执行任何运算；它只把相邻逻辑分段。
# 【项目含义】空行：分隔“捕获异常、关闭 Isaac Sim、返回退出码”中的逻辑段，让结构更容易看清。

# 【L2609】语法拆解：`raise` 主动制造并抛出异常；后面的 `SystemExit(exit_code)` 创建错误对象，当前正常流程随即停止。
# 【项目含义】主动抛出 `SystemExit(exit_code)` 并停止当前路径；说明当前输入违反“捕获异常、关闭 Isaac Sim、返回退出码”要求，不能继续进入仿真、训练或评测。
raise SystemExit(exit_code)
```

### 5.H 模块小结

读完后你应能回答：这一组怎样完成“捕获异常、关闭 Isaac Sim、返回退出码”，它从哪里拿数据，又把什么交给下一模块。若不能回答，先回看 5.A 的三段数据流，再回到具体行。