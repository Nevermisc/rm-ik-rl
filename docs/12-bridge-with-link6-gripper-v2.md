# 12 MoveIt2 + Isaac bridge + link_6 跟随夹爪 V2

本阶段把前面几块能力进一步接起来：

```text
MoveIt2 / ros2_control 关节命令
        ↓
Isaac Sim ROS2 bridge
        ↓
RM65-B 仿真机械臂
        ↓
link_6 跟随功能夹爪
        ↓
桌面方块抓取场景
```

它还不是最终的完整抓取系统，但已经比单独的“夹爪 demo”更接近真实工程链路：机械臂由 ROS2 / MoveIt2 控制，夹爪每一帧跟随 RM65 的 `link_6` 末端位姿。

## 本阶段目标

把以下内容放在同一个 Isaac Sim 场景里：

```text
RM65-B USD
ROS2 joint state / joint command bridge
桌子
目标方块
跟随 link_6 的简化功能夹爪
```

这样后面就可以继续做：

```text
MoveIt2 移动到 pre-grasp 点
→ link_6 夹爪跟着机械臂运动
→ RL policy 控制夹爪局部闭合和上抬
```

## 新增文件

```text
isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py
```

配套运行说明：

```text
scripts/run_moveit2_isaac_link6_gripper_v2.sh
```

## V2 做了什么

### 1. 加载 RM65-B

脚本会从本机实验室电脑的路径加载 RM65-B USD：

```text
/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd
```

注意：这个 USD 模型文件体积较大，且属于资产文件，不上传 GitHub。

### 2. 创建 Isaac ROS2 ActionGraph

脚本创建以下 ROS2 bridge 节点：

```text
ROS2Context
ROS2PublishJointState
ROS2SubscribeJointState
IsaacArticulationController
ROS2PublishClock
```

它发布：

```text
/isaac_joint_states
```

它订阅：

```text
/isaac_joint_commands
```

这和前面的 `rm_isaac_ros2_control` 插件正好对上：

```text
MoveIt2 trajectory
→ joint_trajectory_controller
→ rm_isaac_ros2_control
→ /isaac_joint_commands
→ Isaac Sim ArticulationController
```

### 3. 找到 RM65 的 link_6

实际导入 Isaac Sim 后，RM65 的末端 link 路径不是我们一开始猜的简单 `/RM65/root_joint`，而是：

```text
/RM65/root_joint/link_6
```

V2 脚本会在几个候选路径中查找 `link_6`，找到后打印：

```text
FOUND_LINK6 path=/RM65/root_joint/link_6
```

这个检查很重要，因为功能夹爪要跟随的不是 base，也不是 articulation root，而是末端 link。

### 4. 创建 link_6 跟随夹爪

夹爪由三个 kinematic cuboid 组成：

```text
palm
left_finger
right_finger
```

每一帧都会：

```text
读取 link_6 世界位姿
计算 palm / fingers 在 link_6 局部坐标系下的偏移
转换成世界坐标
设置三个夹爪部件的新位姿
```

也就是说，夹爪虽然暂时不是 RM65 USD 内部的真实关节模型，但它已经能在空间上绑定到机械臂末端。

### 5. 创建桌子和目标方块

V2 脚本会额外创建：

```text
/World/table
/World/target_cube
```

目标方块是 dynamic cuboid，后面会作为 RL grasp 的抓取对象。

### 6. 夹爪闭合计划

当前 V2 先用一个时间表控制夹爪闭合：

```text
GRIPPER_CLOSE_START_STEP
GRIPPER_CLOSE_DURATION_STEPS
```

默认含义：

```text
先保持张开
到指定 step 后开始逐渐闭合
闭合完成后保持闭合
```

这一步不是最终 RL policy，只是为了验证“link_6-follow gripper 可以在 bridge 场景里稳定存在并动作”。

## 验证命令

在实验室 Linux 电脑上运行：

```bash
cd ~/robot-learning/rm-ik-rl
source /opt/ros/humble/setup.bash
ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=80 \
GRIPPER_CLOSE_START_STEP=20 \
GRIPPER_CLOSE_DURATION_STEPS=40 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py
```

验证输出示例：

```text
RM65 Isaac ROS2 bridge with link_6 gripper V2 started.
Publishing: /isaac_joint_states
Subscribing: /isaac_joint_commands
FOUND_LINK6 path=/RM65/root_joint/link_6
Gripper schedule: close_start_step=20, close_duration_steps=40
FINAL bridge_with_link6_gripper_v2 steps=80 max_cube_z=0.0322
```

## 遇到的问题

### 问题 1：没有 source ROS2，ROS2 bridge 起不来

第一次直接用 Isaac Sim Python 跑时，出现：

```text
AMENT_PREFIX_PATH is not set or empty
ROS2 Bridge startup failed
Could not create node using unrecognized type 'isaacsim.ros2.bridge.ROS2Context'
```

原因是当前 shell 没有加载 ROS2 Humble 环境。

解决方式：

```bash
source /opt/ros/humble/setup.bash
```

以后只要跑 Isaac ROS2 bridge，都先 source ROS2。

### 问题 2：articulation 路径容易猜错

之前已经踩过这个坑：

```text
/RM65/root_joint
```

不是最终可用的 articulation / link 路径。

现在 V2 里使用：

```text
RM65 articulation: /RM65/root_joint/root_joint
link_6: /RM65/root_joint/link_6
```

后面如果换模型，第一步仍然应该先用 inspect 脚本查真实 prim 路径。

## 当前限制

V2 仍然有几个限制：

```text
夹爪还是 functional gripper，不是真实夹爪 URDF/USD articulation
夹爪闭合暂时是时间表，不是 RL policy 输出
方块位置还没有随机化
还没有相机/点云 observation
还没有把 MoveIt2 pre-grasp 和 RL grasp 放进一个自动总控脚本
```

这不是失败，而是正常工程拆分。现在 V2 的任务是把“机械臂 bridge 场景”和“末端功能夹爪”接起来。

## 下一步

下一步更有价值的是：

```text
把 PPO/BC warm start 得到的夹爪 policy 接到 link_6-follow gripper 上
```

也就是让 policy 输出：

```text
夹爪开合 action
局部上抬 action
```

并且这些 action 作用在跟随 RM65 `link_6` 的夹爪上。

这会把项目从：

```text
独立 RL grasp demo
```

推进到：

```text
RM65 arm + link_6 gripper + local RL grasp
```

这是更适合放到作品集和面试里讲的一步。
