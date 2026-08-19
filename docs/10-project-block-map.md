# 项目分块地图

这篇文档用于解释仓库里每一块代码的作用。目标是避免项目变成“文件很多但不知道干什么”的状态。

## 总体链路

```text
传统 IK baseline
        ↓
MoveIt2 运动规划
        ↓
ros2_control 控制接口
        ↓
Isaac Sim 仿真机械臂
        ↓
RL 局部夹爪抓取
        ↓
pre-grasp + grasp 组合流程
```

## Block 0：文档与学习记录

目录：

```text
docs/
```

作用：

```text
记录每个阶段做了什么、为什么这么做、怎么复现。
```

对求职最有价值的文档：

```text
docs/07-moveit2-isaac-ros2-control-integration.md
docs/08-rl-grasping-baseline.md
docs/09-pregrasp-rl-grasp-combo.md
docs/10-project-block-map.md
```

你后面写简历/项目介绍时，主要从这几篇里提炼。

## Block 1：早期 Isaac Sim / IK baseline

位置：

```text
根目录 Python 脚本
```

代表文件：

```text
franka_ik_headless.py
franka_ik_visual.py
import_rm65.py
verify_rm65_asset.py
rm65_robot_description.yaml
rm65_ik_headless.py
rm65_ik_visual.py
rm65_rl_reach_es.py
```

这一块解决的问题：

```text
Isaac Sim 能不能跑？
官方 Franka IK 能不能跑？
RM65-B 模型能不能导入？
Lula IK 能不能算出 RM65 的关节角？
```

面试时不需要重点讲太深，但可以作为项目起点：

```text
先建立传统 IK baseline，再逐步转向 MoveIt2 和 RL。
```

## Block 2：MoveIt2 机械臂运动规划

位置：

```text
moveit2_examples/rm_moveit2_examples/
```

核心文件：

```text
src/plan_pose.cpp
launch/plan_pose.launch.py
```

它做的事情：

```text
读取目标 x/y/z
构造目标末端 pose
调用 MoveGroupInterface
执行 plan
输出轨迹点和最终关节角
可选 execute 到控制器
```

你需要理解的核心概念：

```text
planning group
end effector link
target pose
plan
trajectory
execute
```

这一块是求职展示重点之一，因为它说明你不是只会 Isaac Sim 单机 demo，而是开始进入 ROS2 / MoveIt2 机器人软件栈。

## Block 3：ros2_control 虚拟硬件接口

位置：

```text
ros2_control/rm_isaac_ros2_control/
```

核心文件：

```text
include/rm_isaac_ros2_control/rm_isaac_system.hpp
src/rm_isaac_system.cpp
rm_isaac_ros2_control.xml
```

它做的事情：

```text
实现一个 ros2_control SystemInterface
接收 joint_trajectory_controller 的 position command
发布到 /isaac_joint_commands
订阅 /isaac_joint_states
把 Isaac Sim 里的关节状态反馈给 ros2_control
```

你需要理解的核心概念：

```text
hardware_interface
command_interface
state_interface
controller_manager
joint_trajectory_controller
FollowJointTrajectory action
```

这一块是工程含金量比较高的部分，因为它连接了 MoveIt2 和仿真执行层。

## Block 4：Isaac Sim ROS2 bridge

位置：

```text
isaac_sim/
```

核心文件：

```text
inspect_rm65_articulation.py
rm65_isaac_ros2_bridge.py
```

它做的事情：

```text
加载 RM65-B USD
找到 articulation root
读取 joint positions / velocities / efforts
发布 /isaac_joint_states
订阅 /isaac_joint_commands
把 ROS2 发来的关节命令施加到 Isaac Sim 机械臂
```

这一块解决的是：

```text
MoveIt2 算出来的轨迹，怎么真的让 Isaac Sim 里的机械臂动起来？
```

## Block 5：简化夹爪物理抓取

位置：

```text
isaac_sim/simple_gripper_grasp_physics_test.py
```

它做的事情：

```text
创建桌子
创建动态方块
创建两个高摩擦手指
闭合手指
上抬手指
判断方块是否被抬起
```

为什么先做简化夹爪：

```text
真实夹爪 CAD / URDF / 关节建模很容易拖慢项目。
先用简化功能夹爪验证接触抓取逻辑，收益更高。
```

这不是最终形态，只是为了快速验证物理抓取闭环。

## Block 6：RL 抓取环境

位置：

```text
isaac_sim/rm65_grasp_task_skeleton.py
```

核心对象：

```text
SimpleGraspTask
```

它提供 RL 环境的基本接口：

```text
reset()
step(action)
get_observation()
compute_reward()
success
```

当前 action：

```text
action[0]：夹爪开合
action[1]：夹爪上下移动
```

当前 observation：

```text
cube height
finger opening
finger height
cube relative to finger
episode progress
```

当前 reward：

```text
闭合奖励
上抬奖励
方块抬升奖励
成功奖励
```

这一块是后续 RL 继续扩展的核心。

## Block 7：PPO / BC warm start 训练与评估

位置：

```text
isaac_sim/rm65_grasp_ppo_train.py
isaac_sim/rm65_grasp_policy_eval.py
isaac_sim/rm65_grasp_random_policy_test.py
```

流程：

```text
random policy test：验证环境稳定
behavior cloning warm start：先模仿 scripted policy
PPO update：再进行策略优化
policy eval：加载模型并评估成功率
```

当前结果：

```text
EVAL_FINAL success_count=3/3
```

注意：训练出来的 `.pt` 权重不上传 GitHub，因为它是训练产物，不适合塞进源码仓库。

## Block 8：pre-grasp + RL grasp 组合流程

位置：

```text
scripts/run_pregrasp_then_rl_grasp_v0.sh
```

它做的事情：

```text
先调用 MoveIt2，让 RM65 移动到 pre-grasp 点
再调用 RL policy，执行局部夹爪抓取评估
```

当前 V0 限制：

```text
pre-grasp 和 RL grasp 还是两个阶段式流程
简化夹爪还没有真正挂到 RM65 link_6 上
没有物体位姿随机化
没有相机/点云输入
```

下一步 V1：

```text
把简化夹爪挂到 RM65 link_6 附近
让 pre-grasp 点和 cube 位置绑定
实现真正的 arm approach + local grasp
```

## 什么不该上传

这些内容不要上传到 GitHub：

```text
assets/RM65-B/*.usd
Isaac Sim 安装包
训练权重 .pt / .pth / .ckpt
__pycache__
日志
.env
API key
SSH 私钥
```

`.gitignore` 已经做了防护，但仍然要养成上传前检查的习惯。

## 面试讲法

可以这样讲这个项目：

```text
我从传统 IK baseline 开始，先验证 RM65-B 在 Isaac Sim 中的模型和运动学。
随后我接入 MoveIt2，写了目标位姿规划脚本。
为了让 MoveIt2 的轨迹驱动 Isaac Sim 中的机械臂，我实现了一个 ros2_control hardware plugin 和 Isaac ROS2 bridge。
在抓取阶段，我没有一开始做端到端大规模 RL，而是先拆成 pre-grasp planning + local RL grasping：MoveIt2 负责靠近目标，RL policy 负责接触闭合和上抬。
目前已经完成简化夹爪的物理抓取和 PPO/BC warm start baseline，下一步会把夹爪挂到 RM65 末端并加入物体位姿随机化。
```

这套说法比“我跑了一个 Isaac Sim demo”高级很多。
