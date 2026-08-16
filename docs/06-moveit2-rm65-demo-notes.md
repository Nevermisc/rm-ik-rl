# RM65 MoveIt2 官方 demo 记录

这篇文档记录 2026-08-16 跑通 RealMan 官方 RM65 MoveIt2 demo 的过程，以及从配置文件里读出的关键结论。

## 本次目标

先不接真实机械臂，也先不接 Isaac Sim。第一阶段只跑通：

```text
ROS2 Humble + MoveIt2 + RViz2 + RM65 官方配置
```

目标是在 RViz2 的 MotionPlanning 面板中选择 `rm_group`，点击 `Plan`，让 MoveIt2 为 RM65 规划一条轨迹。

## 环境检查结果

实验室电脑环境：

```text
Ubuntu 22.04.5 LTS
ROS2 Humble
MoveIt2 installed
RViz2 installed
```

关键命令：

```bash
echo $ROS_DISTRO
which ros2
ros2 pkg list | grep -E "moveit|rviz2|rm_"
```

结果显示 `humble`、`/opt/ros/humble/bin/ros2`，并且 MoveIt2 与 RViz2 包均存在。

## 官方仓库

下载官方 ROS2 仓库：

```bash
mkdir -p ~/robot-learning/third_party
cd ~/robot-learning/third_party
git clone -b humble https://github.com/RealManRobot/ros2_rm_robot.git
```

仓库中的关键包：

```text
rm_description       RM 机器人模型、URDF、mesh
rm_moveit2_config    MoveIt2 配置
rm_moveit2           MoveIt2 相关启动/功能包
rm_bringup           真实或仿真机械臂 bringup
rm_gazebo            Gazebo 仿真
```

为了不污染已有 `realsense_ws`，单独建立工作空间：

```bash
cd ~/robot-learning
mkdir -p rm_moveit2_ws/src
ln -s ~/robot-learning/third_party/ros2_rm_robot ~/robot-learning/rm_moveit2_ws/src/ros2_rm_robot
cd ~/robot-learning/rm_moveit2_ws
```

最小编译：

```bash
colcon build --packages-select rm_description rm_65_config --symlink-install
```

结果：

```text
Summary: 2 packages finished
```

## 启动 demo

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

启动成功日志中的关键行：

```text
Loaded robot model 'rm_65_description'
Ready to take commands for planning group rm_group.
You can start planning now!
```

在 RViz2 中点击 `Plan` 后，终端输出：

```text
Using planning pipeline 'ompl'
Planner configuration 'rm_group' will use planner 'geometric::RRTConnect'
Motion plan was computed successfully.
time taken to generate plan: 0.0177724 seconds
```

这说明 MoveIt2 已成功为 RM65 的 `rm_group` 规划轨迹。

## SRDF：规划哪条机械臂

文件：

```text
src/ros2_rm_robot/rm_moveit2_config/rm_65_config/config/rm_65_description.srdf
```

核心内容：

```xml
<group name="rm_group">
    <chain base_link="base_link" tip_link="Link6"/>
</group>
```

含义：

```text
MoveIt2 中的规划组叫 rm_group。
这条机械臂链从 base_link 开始，到 Link6 结束。
base_link 到 Link6 中间的关节，就是 MoveIt2 要规划的 6 轴机械臂。
```

SRDF 还定义了 `zero` 姿态：

```xml
<group_state name="zero" group="rm_group">
    <joint name="joint1" value="0"/>
    ...
    <joint name="joint6" value="0"/>
</group_state>
```

以及一批 `disable_collisions`，用于告诉 MoveIt2 某些相邻或永不碰撞的 link pair 不需要做碰撞检测。

## kinematics.yaml：IK 用哪个求解器

文件：

```text
src/ros2_rm_robot/rm_moveit2_config/rm_65_config/config/kinematics.yaml
```

内容：

```yaml
rm_group:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.0050000000000000001
  kinematics_solver_timeout: 0.0050000000000000001
```

含义：

```text
rm_group 使用 KDLKinematicsPlugin 解 IK。
KDL 是 ROS 生态中常用的传统运动学库。
IK 超时时间是 0.005 秒，也就是 5 ms。
```

所以官方 RM65 MoveIt2 demo 的 IK 不是 Lula，而是 KDL。

## RRTConnect：路径规划，不是 IK

日志中出现：

```text
geometric::RRTConnect
```

它不是 IK 求解器，而是运动规划算法。关系是：

```text
KDL：给目标位姿，求目标关节状态
OMPL / RRTConnect：从当前关节状态规划到目标关节状态
```

更完整的 MoveIt2 流程是：

```text
目标位姿
→ KDL 做 IK
→ OMPL / RRTConnect 做路径规划
→ 生成轨迹
→ fake controller / 真实控制器执行
```

RRT 本身不是抓取算法。它是抓取系统中的运动规划模块，负责“怎么无碰撞地走过去”。

## URDF：link 和 joint 怎么连接

MoveIt2 demo 的顶层 xacro：

```text
rm_65_config/config/rm_65_description.urdf.xacro
```

它 include 的是固定 URDF：

```xml
<xacro:include filename="$(find rm_description)/urdf/rm_65.urdf" />
```

也就是说当前 demo 用的是：

```text
rm_description/urdf/rm_65.urdf
```

不是动态选择 6F / 6FB 末端版本的 xacro。

`joint1` 片段说明：

```text
joint1: base_link -> Link1
origin: xyz="0 0 0.2405"
axis: z axis
limit: -3.1 to 3.1 rad
```

`joint6` 片段说明：

```text
joint6: Link5 -> Link6
origin: xyz="0 -0.144 0", rpy="1.5708 0 0"
axis: z axis
limit: -6.28 to 6.28 rad
mesh: rm_65_arm/link6.STL
```

因此 MoveIt2 官方 demo 规划的是：

```text
base_link
→ joint1 → Link1
→ joint2 → Link2
→ joint3 → Link3
→ joint4 → Link4
→ joint5 → Link5
→ joint6 → Link6
```

注意：`Link6` 是机械臂法兰/末端 link，不一定是夹爪尖端。后续做抓取时，可能还要定义 `tool0`、`tcp` 或 `gripper_center` 这样的工具坐标系。

## demo.launch.py 做了什么

文件：

```text
rm_65_config/launch/demo.launch.py
```

内容：

```python
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_demo_launch


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("rm_65_description", package_name="rm_65_config").to_moveit_configs()
    return generate_demo_launch(moveit_config)
```

含义：

```text
MoveItConfigsBuilder 根据机器人名 rm_65_description 和包名 rm_65_config，
自动读取 URDF、SRDF、kinematics.yaml、controller 配置和 RViz 配置。
generate_demo_launch 使用 MoveIt2 官方 demo 模板启动 robot_state_publisher、move_group、rviz2 和 fake controller。
```

完整链路：

```text
ros2 launch rm_65_config demo.launch.py
→ MoveItConfigsBuilder 读取 rm_65_config
→ rm_65_description.urdf.xacro include rm_description/urdf/rm_65.urdf
→ SRDF 定义 rm_group: base_link 到 Link6
→ kinematics.yaml 指定 KDL IK solver
→ move_group 启动
→ RViz MotionPlanning 面板发送规划请求
→ OMPL/RRTConnect 规划成功
```

## 当前结论

本阶段已经跑通：

```text
官方 RM65 MoveIt2 demo
RViz2 可视化
rm_group 规划组
KDL IK
OMPL / RRTConnect 路径规划
fake controller 轨迹预览/执行
```

下一步建议：

```text
给定目标位姿
→ 通过 MoveIt2 编程接口调用 plan
→ 输出是否成功、规划耗时、轨迹点数量
```

这一步会把“会点 RViz 按钮”推进到“能写脚本调用 MoveIt2 规划”。
