# RM65 MoveIt2 Examples

这个包用于学习如何使用 MoveIt2 控制 RM65 机械臂。

当前包含两个层次的示例：

- `plan_pose.cpp`：给 RM65 的末端 `Link6` 一个目标位姿，让 MoveIt2 规划轨迹并执行。
- `isaac_control_test.launch.py`：启动使用自定义 `RMIsaacSystem` hardware plugin 的 `ros2_control` 控制链路。

## 1. 编译

在工作空间根目录运行：

```bash
cd ~/robot-learning/rm_moveit2_ws
colcon build --packages-select rm_moveit2_examples rm_isaac_ros2_control --symlink-install
source install/setup.bash
```

## 2. 单独运行 MoveIt2 目标位姿程序

先启动官方 RM65 MoveIt2 demo：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

再开第二个终端运行：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

如果成功，会看到类似输出：

```text
Planning succeeded.
Executing trajectory...
Execution succeeded.
```

## 3. MoveIt2 + ros2_control + Isaac Sim 联动

启动顺序：

1. 启动 Isaac Sim 侧 ROS2 bridge：

```bash
cd ~/robot-learning/rm-ik-rl
~/isaac-sim-5.1.0/python.sh rm65_isaac_ros2_bridge.py
```

2. 启动自定义 ros2_control 链路：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples isaac_control_test.launch.py
```

3. 启动 MoveIt2 `move_group`：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config move_group.launch.py
```

4. 运行目标位姿规划：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

最终链路：

```text
MoveIt2
↓
/rm_group_controller/follow_joint_trajectory
↓
JointTrajectoryController
↓
RMIsaacSystem hardware plugin
↓
/isaac_joint_commands
↓
Isaac Sim ROS2 Bridge
↓
Isaac Sim RM65-B articulation
```

## 4. 目标点参数

`plan_pose.launch.py` 支持运行时传目标点：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

单位是米，参考坐标系是 `base_link`。

## 5. 注意事项

- 当前 MoveIt2 规划末端 link 是 `Link6`。
- Isaac Sim USD 中的 articulation root 是 `/RM65/root_joint/root_joint`。
- Isaac Sim USD 的关节名是 `joint_1` 到 `joint_6`，MoveIt2 / ros2_control 使用 `joint1` 到 `joint6`，映射在 `RMIsaacSystem` 中完成。
- 当前示例依赖本地 RM65-B USD asset，不把大体积 USD 资产上传到仓库。
