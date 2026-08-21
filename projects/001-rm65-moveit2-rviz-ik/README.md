# 001 - RM65 MoveIt2 + RViz 目标点规划演示

这个小项目是我的第一个 RM65 机械臂 MoveIt2 入门项目。

目标很简单：

> 在 RViz 里显示 RM65 机械臂，然后通过终端发送目标点坐标，让 MoveIt2 规划轨迹并执行。机械臂动到目标点后停住，等待下一个目标点。

它不是强化学习，也不是 Isaac Sim 物理仿真。它是后面所有抓取、仿真、真实机械臂控制的前置基础。

## 这个项目解决什么问题

我一开始看到机械臂一直循环动，不知道它是在真的执行，还是 RViz 在播放轨迹预览。

这个小项目专门解决这些入门问题：

- RViz 里不同颜色/残影的机械臂分别是什么意思；
- MoveIt2 里的 `Plan`、`Execute`、`Plan & Execute` 有什么区别；
- 为什么输入某些目标点会规划失败；
- 怎么用终端发送目标点，让机械臂动一次后停住；
- 为什么一次性 demo 重新运行时，机械臂可能像是先回到原点再去新目标；
- MoveIt2 在这个阶段到底帮我做了什么。

## 这个 demo 分成几个小块

这个项目可以分成 6 个小块。理解这 6 块，就能理解整个 demo 是怎么串起来的。

### 1. 官方 RM65 模型与 MoveIt2 配置

来源：睿尔曼官方 ROS2 仓库 `ros2_rm_robot`。

主要提供：

- RM65 的 link / joint / mesh；
- 关节角限制；
- MoveIt2 planning group：`rm_group`；
- 末端 link：`Link6`；
- IK 配置：`kdl_kinematics_plugin/KDLKinematicsPlugin`。

这一块回答的是：

```text
MoveIt2 怎么知道 RM65 长什么样、有哪些关节、末端在哪里？
```

### 2. RViz + MoveIt2 官方 demo

启动命令：

```bash
ros2 launch rm_65_config demo.launch.py
```

它负责启动：

- RViz；
- MoveIt2 `move_group`；
- fake controller；
- robot_state_publisher；
- 当前机械臂状态显示。

这一块回答的是：

```text
我在哪里看到机械臂？MoveIt2 的规划服务在哪里运行？
```

### 3. 一次性目标点 demo：`plan_pose.cpp`

启动命令示例：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

它的特点是：

```text
启动一次
读取一个目标点
规划一次
执行一次
退出
```

这个版本适合学习“最基本的 MoveIt2 调用流程”。

### 4. 交互式连续目标 demo：`interactive_pose_commander.cpp`

启动命令：

```bash
ros2 launch rm_moveit2_examples interactive_pose_commander.launch.py
```

它的特点是：

```text
启动一次
一直等待 /rm65_target_point 目标点话题
每收到一个 x y z
就从当前机械臂姿态规划到新目标
执行完停住
继续等待下一个目标
```

这个版本更接近真实 ROS2 项目里的控制逻辑。它不是靠反复重新 launch 程序，而是让一个节点持续运行，然后通过 ROS2 topic 给它发命令。

### 5. 目标点可视化 marker

两个 demo 都会发布目标点 marker。

作用是：

```text
在 RViz 里显示目标点在哪里，避免只看终端坐标没有感觉。
```

交互式版本使用的话题是：

```text
interactive_target_marker
```

如果 RViz 里想看到红色目标球，可以手动添加 Marker 显示。

### 6. 轨迹规划与执行

每次收到目标点后，程序会调用 MoveIt2：

```text
接收 /rm65_target_point
↓
设置目标位姿
↓
从当前状态开始规划
↓
生成关节轨迹
↓
发送给 fake controller 执行
↓
RViz 中机械臂移动
```

其中交互式版本的关键代码是：

```cpp
move_group.setStartStateToCurrentState();
```

它的作用是告诉 MoveIt2：

```text
这一次不要从默认初始状态规划，要从机械臂当前姿态开始规划。
```

## 文件结构

```text
001-rm65-moveit2-rviz-ik/
├── README.md
├── rm_moveit2_examples/
│   ├── CMakeLists.txt
│   ├── package.xml
│   ├── launch/
│   │   ├── plan_pose.launch.py
│   │   └── interactive_pose_commander.launch.py
│   └── src/
│       ├── plan_pose.cpp
│       └── interactive_pose_commander.cpp
└── docs/
    └── rviz-moveit2-basic.md
```

其中：

- `rm_moveit2_examples/src/plan_pose.cpp`：一次性目标点规划程序，适合理解最小流程。
- `rm_moveit2_examples/src/interactive_pose_commander.cpp`：交互式连续目标程序，适合演示“发一个点，动一次，再等下一个点”。
- `rm_moveit2_examples/launch/plan_pose.launch.py`：一次性 demo 的启动文件。
- `rm_moveit2_examples/launch/interactive_pose_commander.launch.py`：交互式 demo 的启动文件。
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

## 第二步 A：运行一次性目标点 demo

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

这个版本适合第一次验证 MoveIt2 能不能规划成功。

## 第二步 B：运行交互式连续目标 demo

更推荐平时演示用这个版本。

先开第二个终端，启动交互式节点：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_moveit2_examples interactive_pose_commander.launch.py
```

这个终端不要关。它会一直等待目标点。

再开第三个终端，每次发一个目标点：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic pub --once /rm65_target_point geometry_msgs/msg/Point "{x: 0.30, y: 0.20, z: 0.40}"
```

等机械臂执行完，再发下一个目标点：

```bash
ros2 topic pub --once /rm65_target_point geometry_msgs/msg/Point "{x: 0.30, y: 0.30, z: 0.40}"
```

这时节点不会退出，也不会重新启动。它会从当前姿态继续规划到下一个目标。

## 为什么旧版本换目标点时可能先回原点再绕一圈

比如我先运行：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

然后再运行：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.30 z:=0.40
```

可能看到机械臂好像先回到原点，再绕一圈去新位置。

这通常不是 IK 坏了，而是因为：

1. `plan_pose.cpp` 是一次性程序，每次 launch 都是重新启动一个节点；
2. fake controller / RViz 里的当前状态不一定按我直觉保存成上一次执行后的状态；
3. 同一个末端位置可能有多组 IK 解，机械臂可能选择不同的肘部/手腕姿态；
4. OMPL / RRTConnect 更关注“找到可行路径”，不保证路径一定是人眼看起来最短、最顺的。

交互式版本通过持续运行节点，并在每次规划前执行：

```cpp
move_group.setStartStateToCurrentState();
```

来尽量让下一次规划从当前姿态开始。

## 推荐测试点

这些点相对容易成功：

```text
0.30 0.20 0.40
0.30 0.30 0.40
0.25 -0.25 0.45
0.35 0.00 0.40
```

这些点不一定成功：

```text
-0.35 -0.30 0.60
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
5. 不是所有输入点都能成功，机械臂有工作空间、姿态、关节限制和规划时间限制；
6. 一次性 demo 和持续运行 demo 的行为不同；
7. 真正项目里要尽量从当前状态规划，而不是每次都像重新启动一样规划；
8. ROS2 里更标准的交互方式是让节点长期运行，然后通过 topic/service/action 给节点发任务。

## 下一步

下一阶段会在这个基础上继续做：

```text
002 - RM65 + D435i RealSense + RViz 可视化
```

再之后继续做：

```text
003 - RM65 MoveIt2 + Isaac Sim 联动
```

也就是：

```text
MoveIt2 负责规划
Isaac Sim 负责物理仿真显示
机械臂在 Isaac Sim 里跟着 MoveIt2 的轨迹动
```
