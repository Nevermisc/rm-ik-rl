# RM65 MoveIt2 + Isaac Sim + ros2_control 联动记录

本阶段目标是从“RViz / fake hardware 能动”升级到更标准的工程链路：

```text
MoveIt2
↓
FollowJointTrajectory action
↓
JointTrajectoryController
↓
自定义 ros2_control hardware plugin
↓
Isaac Sim ROS2 Bridge
↓
Isaac Sim 中的 RM65-B articulation
```

这条路线比直接向 Isaac Sim 发一个普通 topic 更接近真实机器人项目。MoveIt2 仍然只面对标准 controller；仿真或真实硬件差异被封装在 hardware interface 后面。

## 本次新增内容

### 1. `rm_isaac_ros2_control`

路径：

```text
ros2_control/rm_isaac_ros2_control
```

这是一个 `ros2_control` hardware plugin 包，核心类是：

```cpp
rm_isaac_ros2_control::RMIsaacSystem
```

插件名：

```text
rm_isaac_ros2_control/RMIsaacSystem
```

它实现了 `hardware_interface::SystemInterface`，主要函数包括：

- `on_init()`：初始化关节状态、命令缓存、ROS2 publisher/subscriber。
- `export_state_interfaces()`：导出 position / velocity 状态接口。
- `export_command_interfaces()`：导出 position 命令接口。
- `read()`：处理 `/isaac_joint_states` 订阅，更新 ros2_control 状态。
- `write()`：把 controller 输出的关节命令发布到 `/isaac_joint_commands`。

关节名映射：

```text
MoveIt2 / ros2_control: joint1 ... joint6
Isaac Sim USD:          joint_1 ... joint_6
```

映射在 `RMIsaacSystem` 内部完成。

### 2. MoveIt2 示例包新增配置

路径：

```text
moveit2_examples/rm_moveit2_examples/config/rm_65_isaac.ros2_control.xacro
moveit2_examples/rm_moveit2_examples/config/rm_65_isaac_description.urdf.xacro
moveit2_examples/rm_moveit2_examples/launch/isaac_control_test.launch.py
```

其中 `rm_65_isaac.ros2_control.xacro` 将官方 fake hardware：

```xml
<plugin>mock_components/GenericSystem</plugin>
```

替换为自定义硬件插件：

```xml
<plugin>rm_isaac_ros2_control/RMIsaacSystem</plugin>
```

`isaac_control_test.launch.py` 用于启动：

```text
ros2_control_node
joint_state_broadcaster
rm_group_controller
```

验证 controller 链路：

```bash
ros2 control list_controllers
ros2 action list | grep follow_joint_trajectory
```

期望看到：

```text
joint_state_broadcaster active
rm_group_controller active
/rm_group_controller/follow_joint_trajectory
```

### 3. Isaac Sim 侧 bridge

路径：

```text
isaac_sim/rm65_isaac_ros2_bridge.py
isaac_sim/inspect_rm65_articulation.py
```

`rm65_isaac_ros2_bridge.py` 做的事情：

1. 启用 `isaacsim.ros2.bridge`。
2. 加载本地 RM65-B USD。
3. 创建 ActionGraph。
4. 发布 `/isaac_joint_states`。
5. 订阅 `/isaac_joint_commands`。
6. 用 `IsaacArticulationController` 控制 Isaac Sim 中的 RM65-B。

关键 articulation root：

```text
/RM65/root_joint/root_joint
```

这个路径是通过 `inspect_rm65_articulation.py` 检查出来的。不要误用 `/RM65` 或 `/RM65/root_joint`，它们不是 Isaac PhysX 能识别的 articulation root。

## 启动顺序

### 1. 启动 Isaac Sim bridge

```bash
cd ~/robot-learning/rm-ik-rl
~/isaac-sim-5.1.0/python.sh rm65_isaac_ros2_bridge.py
```

检查 Isaac topic：

```bash
source /opt/ros/humble/setup.bash
ros2 topic list | grep isaac
ros2 topic echo /isaac_joint_states --once
```

期望看到：

```text
/isaac_joint_commands
/isaac_joint_states
```

`/isaac_joint_states` 中应包含：

```text
joint_1
joint_2
joint_3
joint_4
joint_5
joint_6
```

### 2. 启动 ros2_control

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples isaac_control_test.launch.py
```

期望日志包括：

```text
Loading hardware 'RMIsaacSystem'
Initialized RMIsaacSystem with 6 joints.
Activated RMIsaacSystem.
Successfully loaded controller joint_state_broadcaster into state active
Successfully loaded controller rm_group_controller into state active
```

### 3. 启动 MoveIt2 move_group

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config move_group.launch.py
```

### 4. 运行目标位姿规划

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

期望输出：

```text
Planning succeeded.
Executing trajectory...
Execution succeeded.
```

此时 Isaac Sim 中的 RM65-B 应跟随 MoveIt2 规划结果运动。

## 已验证结果

已验证：

- `rm_isaac_ros2_control` 能编译并安装。
- `ros2_control_node` 能加载 `RMIsaacSystem`。
- `joint_state_broadcaster` 和 `rm_group_controller` 能 active。
- `/rm_group_controller/follow_joint_trajectory` action 存在。
- Isaac Sim 能发布 `/isaac_joint_states`。
- Isaac Sim 能订阅 `/isaac_joint_commands`。
- MoveIt2 规划执行后，Isaac Sim 中的 RM65-B 能运动。

## 当前限制

- RM65-B USD asset 仍依赖本地路径：

```text
/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd
```

仓库中暂不上传大体积 USD 资产。

- 目前 bridge 使用 Isaac Sim ActionGraph + ROS2 JointState topic，尚未封装成正式 Isaac extension。
- 当前目标位姿仍以 `Link6` 为末端，后续接夹爪时需要明确 TCP / tool frame。
- 当前 launch 仍是测试版，后续应整理成一个一键启动的集成 launch。

## 下一步

建议后续继续做：

1. 把启动流程整理成一键 launch 或脚本。
2. 明确 RM65 末端 TCP，与夹爪坐标系对齐。
3. 增加 Isaac Sim 中目标点 marker 和末端实际位置可视化。
4. 记录规划目标、轨迹点、Isaac 实际关节状态，做误差验证。
5. 再进入抓取场景或强化学习 reaching baseline。
