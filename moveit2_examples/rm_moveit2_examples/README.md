# RM65 MoveIt2 Examples

这个包用于学习如何使用 MoveIt2 控制 RM65 机械臂。

当前示例：

- `plan_pose.cpp`：给 RM65 的末端 `Link6` 一个目标位姿，让 MoveIt2 规划轨迹，并通过 fake controller 在 RViz 中执行。

## 1. 编译

在工作空间根目录运行：

```bash
cd ~/robot-learning/rm_moveit2_ws
colcon build --packages-select rm_moveit2_examples --symlink-install
source install/setup.bash
```

## 2. 启动官方 RM65 MoveIt2 demo

打开第一个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

等待 RViz 打开，并看到 RM65 机械臂。

## 3. 运行自己的目标位姿规划程序

打开第二个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py
```

如果成功，会看到类似输出：

```text
Planning succeeded.
Trajectory point count: ...
Executing trajectory...
Execution succeeded.
```

RViz 中灰色的 RM65 机械臂会移动到新的姿态。

## 4. 修改目标点

目标点在：

```cpp
target_pose.position.x = 0.25;
target_pose.position.y = -0.25;
target_pose.position.z = 0.45;
```

单位是米，参考坐标系是 `base_link`。

修改代码后，需要重新编译：

```bash
cd ~/robot-learning/rm_moveit2_ws
colcon build --packages-select rm_moveit2_examples --symlink-install
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py
```

## 5. 当前理解

这个示例完成了：

```text
目标位姿
↓
MoveIt2 / KDL 求 IK
↓
MoveIt2 / OMPL 规划轨迹
↓
fake controller 执行
↓
RViz 中机械臂运动
```

注意：当前只是仿真/可视化 demo，没有连接真实机械臂。
