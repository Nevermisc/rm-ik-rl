# 001-v2 - RM65 MoveIt2 交互式连续目标点 Demo

这个小项目是 `001` 的升级版。

`001` 的一次性 demo 是：

```text
运行一次 launch
给一个目标点
机械臂规划并执行一次
程序退出
```

`001-v2` 的目标是：

```text
启动一次节点
每次通过 ROS2 topic 发一个目标点
机械臂从上一次执行后的姿态继续规划
动到目标点后停住
继续等待下一个目标点
```

这个版本更像真实机器人项目里的控制方式。

## 为什么要做 v2

我之前发现一个现象：

```text
先发 x=0.30 y=0.20 z=0.40
再发 x=0.30 y=0.30 z=0.40
机械臂看起来会先回到初始位置，再绕一圈过去
```

这通常不是 IK 求解器坏了，而是因为一次性 demo 每次都重新启动，MoveIt2 / fake controller 的当前状态同步有时也不够稳定。

所以 v2 做了两件事：

1. 节点持续运行，不再每次重新 launch；
2. 每次执行成功后，程序记住最后一个轨迹点的 6 个关节角，下一次规划时显式把它作为 start state。

## 这个 demo 分成几个小块

### 1. MoveIt2 官方配置

使用睿尔曼官方 `rm_65_config`：

- planning group：`rm_group`
- end effector link：`Link6`
- IK solver：KDL
- controller：fake `rm_group_controller`

### 2. RViz + MoveIt2 后台

先启动官方 demo：

```bash
ros2 launch rm_65_config demo.launch.py
```

这一部分提供：

- RViz 可视化；
- MoveIt2 `move_group`；
- fake controller；
- 当前机械臂状态发布。

### 3. 交互式目标点节点

本项目的核心代码：

```text
rm65_moveit2_interactive/src/interactive_pose_commander.cpp
```

它订阅：

```text
/rm65_target_point
```

消息类型：

```text
geometry_msgs/msg/Point
```

### 4. 目标点 marker

节点会发布：

```text
/interactive_target_marker
```

用于在 RViz 里显示红色目标球。

### 5. 规划起点记忆

每次执行成功后，程序保存轨迹最后一个点：

```text
trajectory.points.back().positions
```

下一次规划时，把它作为新的起点。

这一块是 v2 的关键升级。

## 文件结构

```text
001-v2-rm65-moveit2-interactive-target/
├── README.md
└── rm65_moveit2_interactive/
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── interactive_pose_commander.launch.py
    └── src/
        └── interactive_pose_commander.cpp
```

## 编译

把 `rm65_moveit2_interactive` 放进 ROS2 工作区的 `src` 后：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rm65_moveit2_interactive --symlink-install
source install/setup.bash
```

## 运行

第一个终端，启动 RViz + MoveIt2：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

第二个终端，启动交互节点：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm65_moveit2_interactive interactive_pose_commander.launch.py
```

第三个终端，发送目标点：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic pub --once /rm65_target_point geometry_msgs/msg/Point "{x: 0.30, y: 0.20, z: 0.40}"
```

再发第二个点：

```bash
ros2 topic pub --once /rm65_target_point geometry_msgs/msg/Point "{x: 0.30, y: 0.30, z: 0.40}"
```

## 观察重点

看第二个终端日志：

```text
Using remembered executed joint state as planning start
First trajectory point used by this plan
Final joint target
```

如果第二次规划的 `First trajectory point` 接近第一次的 `Final joint target`，说明它不是从初始位置重新规划。

## 这个 demo 的意义

这个 demo 不是为了炫技，而是为了理解正式机器人控制里的一个核心问题：

```text
下一次运动，必须从当前状态开始规划。
```

如果起点错了，机械臂视觉上就会出现奇怪的回原点、绕圈、跳变。真实机械臂上这个问题更重要。