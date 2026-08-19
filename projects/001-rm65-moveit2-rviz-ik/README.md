# 001 - RM65 MoveIt2 + RViz 目标点规划演示

这个小项目是我的第一个 RM65 机械臂 MoveIt2 入门项目。

目标很简单：

> 在 RViz 里显示 RM65 机械臂，然后通过终端输入目标点坐标，让 MoveIt2 规划轨迹并执行。机械臂动到目标点后停住。

它不是强化学习，也不是 Isaac Sim 物理仿真。它是后面所有抓取、仿真、真实机械臂控制的前置基础。

## 这个项目解决什么问题

我一开始看到机械臂一直循环动，不知道它是在真的执行，还是 RViz 在播放轨迹预览。

这个小项目专门解决这些入门问题：

- RViz 里不同颜色/残影的机械臂分别是什么意思；
- MoveIt2 里的 `Plan`、`Execute`、`Plan & Execute` 有什么区别；
- 为什么输入某些目标点会规划失败；
- 怎么用终端输入目标点，让机械臂动一次后停住；
- MoveIt2 在这个阶段到底帮我做了什么。

## 文件结构

```text
001-rm65-moveit2-rviz-ik/
├── README.md
├── rm_moveit2_examples/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── launch/
│   │   └── plan_pose.launch.py
│   └── src/
│       └── plan_pose.cpp
└── docs/
    └── rviz-moveit2-basic.md
```

其中：

- `rm_moveit2_examples/src/plan_pose.cpp`：核心 C++ 程序，负责接收目标点、调用 MoveIt2 规划、执行轨迹。
- `rm_moveit2_examples/launch/plan_pose.launch.py`：启动文件，允许我在终端输入 `x y z`。
- `docs/rviz-moveit2-basic.md`：新手解释文档。

## 依赖环境

这个小项目依赖：

- Ubuntu 22.04
- ROS2 Humble
- MoveIt2
- RealMan 官方 ROS2 包：`ros2_rm_robot`

我当前实验室电脑上的工作区是：

```bash
~/robot-learning/rm_moveit2_ws
```

官方 RM65 MoveIt2 配置来自：

```bash
~/robot-learning/third_party/ros2_rm_robot
```

## 如何放进 ROS2 工作区

如果只下载这个小项目文件夹，需要把里面的 ROS2 package 放进工作区的 `src` 目录。

示例：

```bash
cd ~/robot-learning/rm_moveit2_ws/src
cp -r /path/to/001-rm65-moveit2-rviz-ik/rm_moveit2_examples .
```

同时工作区里还需要有 RealMan 官方包，例如：

```bash
cd ~/robot-learning/rm_moveit2_ws/src
git clone -b humble https://github.com/RealManRobot/ros2_rm_robot.git
```

如果已经通过软链接接入官方包，也可以不用重复克隆。

## 编译

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rm_moveit2_examples --symlink-install
source install/setup.bash
```

如果编译成功，会看到类似：

```text
Summary: 1 package finished
```

## 第一步：打开 RViz + MoveIt2 官方 demo

先开第一个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

这个终端不要关。

它负责启动：

- RViz
- MoveIt2 `move_group`
- fake controller
- robot_state_publisher

## 第二步：用终端输入目标点

再开第二个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

如果成功，终端会出现：

```text
Planning succeeded.
Execution succeeded.
```

这表示：

```text
终端输入目标点
↓
MoveIt2 接收目标
↓
KDL/MoveIt2 求解目标姿态
↓
OMPL 规划关节轨迹
↓
fake controller 执行轨迹
↓
RViz 里的机械臂移动到目标点并停住
```

## 推荐测试点

这些点相对容易成功：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.25 y:=-0.25 z:=0.45
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.35 y:=0.00 z:=0.40
```

这些点不一定成功：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=-0.35 y:=-0.30 z:=0.60
```

原因不是命令错了，而是目标位置和固定末端姿态一起约束时，MoveIt2 可能找不到可行轨迹。

## RViz 里看到的东西是什么意思

- 白色/灰色机械臂：当前真实状态。
- 橙色机械臂：目标状态或规划目标。
- 半透明残影：MoveIt2 规划出来的中间路径。
- 彩色坐标球：可以手动拖动的目标姿态交互器。

如果不想看残影：

```text
Displays
  MotionPlanning
    Planned Path
      Show Robot Visual
```

把 `Show Robot Visual` 取消勾选。

如果不想循环播放规划动画：

```text
Displays
  MotionPlanning
    Planned Path
      Loop Animation
```

把 `Loop Animation` 取消勾选。

## 我学到了什么

这个小项目让我第一次把下面几件事连起来：

1. ROS2 package 的基本结构；
2. MoveIt2 的 planning group；
3. RViz 不是仿真器，而是可视化和交互工具；
4. MoveIt2 可以接收目标位姿并规划机械臂关节轨迹；
5. 不是所有输入点都能成功，机械臂有工作空间、姿态、关节限制和规划时间限制。

## 下一步

下一阶段会在这个基础上继续做：

```text
002 - RM65 MoveIt2 + Isaac Sim 联动
```

也就是：

```text
MoveIt2 负责规划
Isaac Sim 负责物理仿真显示
机械臂在 Isaac Sim 里真实跟着 MoveIt2 的轨迹动
```
