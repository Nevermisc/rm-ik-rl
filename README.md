# RM65-B Manipulation：MoveIt2 + Isaac Sim + RL Grasping

这是一个面向机器人 manipulation / 抓取规划求职展示的学习项目。项目主线不是单纯“跑一个 demo”，而是逐步搭出一条可解释、可复现的机器人抓取工程链路：

```text
RM65-B 模型导入
→ 传统 IK / MoveIt2 运动规划
→ ros2_control 控制接口
→ Isaac Sim 联动仿真
→ 简化夹爪物理抓取
→ RL policy 完成局部抓取
```

当前更推荐的工程路线是：

```text
MoveIt2 负责机械臂移动到 pre-grasp 点
RL policy 负责接触阶段的夹爪闭合和上抬
```

这比一开始就做“6 轴机械臂 + 夹爪联合端到端 RL”更稳定，也更容易在面试中讲清楚。

## 当前能力状态

- [x] Isaac Sim / Ubuntu / RTX 环境验证
- [x] Franka 官方 IK 示例跑通
- [x] RM65-B URDF/USD 导入与资产验证
- [x] RM65-B 传统 IK baseline
- [x] RM65-B MoveIt2 官方 demo 跑通
- [x] 自定义 MoveIt2 pose planning 示例
- [x] 自定义 ros2_control hardware plugin
- [x] MoveIt2 → ros2_control → Isaac Sim 联动
- [x] 简化功能夹爪物理抓取
- [x] PPO/BC warm start RL 抓取 baseline
- [x] MoveIt2 pre-grasp + RL grasp V0 组合脚本
- [x] 简化夹爪跟随 RM65 link_6 V1
- [x] MoveIt2 + Isaac bridge + link_6 跟随夹爪 V2
- [ ] 将 RL policy 接到 link_6 跟随夹爪
- [ ] 物体位姿随机化与更完整 observation
- [ ] 真夹爪模型/真实机械臂接口

## 项目分块

### 1. Isaac Sim 传统 IK 与资产验证

根目录中的早期脚本用于验证 Isaac Sim、RM65-B USD、Lula IK 和基础可视化：

```text
import_rm65.py
verify_rm65_asset.py
rm65_robot_description.yaml
rm65_ik_headless.py
rm65_ik_visual.py
franka_ik_headless.py
franka_ik_visual.py
```

这些文件保留为早期 baseline 和调试记录。

### 2. MoveIt2 示例

目录：

```text
moveit2_examples/rm_moveit2_examples/
```

作用：

```text
给定目标位姿
调用 MoveIt2 plan / execute
输出规划结果、轨迹点、关节角
```

### 3. ros2_control 接口

目录：

```text
ros2_control/rm_isaac_ros2_control/
```

作用：

```text
提供一个自定义 ros2_control hardware plugin
把 MoveIt2 的 JointTrajectoryController 指令转成 /isaac_joint_commands
再从 /isaac_joint_states 读回 Isaac Sim 中的关节状态
```

### 4. Isaac Sim ROS2 bridge

目录：

```text
isaac_sim/
```

核心文件：

```text
inspect_rm65_articulation.py
rm65_isaac_ros2_bridge.py
```

作用：

```text
在 Isaac Sim 中加载 RM65-B
读取 articulation joint states
订阅 /isaac_joint_commands
驱动仿真机械臂运动
```

### 5. RL 抓取 baseline

目录：

```text
isaac_sim/
```

核心文件：

```text
simple_gripper_grasp_physics_test.py
rm65_grasp_task_skeleton.py
rm65_grasp_random_policy_test.py
rm65_grasp_ppo_train.py
rm65_grasp_policy_eval.py
```

当前版本使用简化功能夹爪和方块，重点验证：

```text
接触物理是否稳定
action / observation / reward / success 是否闭环
策略是否能通过 PPO/BC warm start 完成抓取
```

### 6. link_6 跟随夹爪 V1

目录：

```text
isaac_sim/
```

核心文件：

```text
rm65_link6_follow_gripper_v1.py
```

作用：

```text
读取 RM65 link_6 世界位姿
让简化功能夹爪 palm / fingers 跟随 link_6
验证夹爪在空间上属于机械臂末端
```

### 7. MoveIt2 + Isaac bridge + link_6 跟随夹爪 V2

目录：

```text
isaac_sim/
scripts/
```

核心文件：

```text
isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py
scripts/run_moveit2_isaac_link6_gripper_v2.sh
```

作用：

```text
在同一个 Isaac Sim 场景里加载 RM65-B、ROS2 bridge、桌子、方块和 link_6-follow gripper。
MoveIt2 / ros2_control 仍负责机械臂关节命令，简化夹爪每帧跟随 link_6。
```

这是把“机械臂执行”和“末端夹爪”接到同一个场景中的过渡版本。

### 8. 组合流程脚本

目录：

```text
scripts/
```

核心文件：

```text
run_pregrasp_then_rl_grasp_v0.sh
```

作用：

```text
先调用 MoveIt2 移动到 pre-grasp 点
再调用 RL policy 完成局部抓取评估
```

## 快速运行路线

### 运行 MoveIt2 pose planning

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

### 运行 Isaac Sim bridge

```bash
cd ~/robot-learning/rm-ik-rl
source /opt/ros/humble/setup.bash
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_ros2_bridge.py
```

### 运行 ros2_control

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples isaac_control_test.launch.py
```

### 运行 move_group

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config move_group.launch.py
```

### 运行 link_6 跟随夹爪 V1

```bash
cd ~/robot-learning/rm-ik-rl
ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=60 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_link6_follow_gripper_v1.py
```

### 运行 MoveIt2 + Isaac bridge + link_6 跟随夹爪 V2 smoke test

```bash
cd ~/robot-learning/rm-ik-rl
source /opt/ros/humble/setup.bash
ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=80 \
GRIPPER_CLOSE_START_STEP=20 \
GRIPPER_CLOSE_DURATION_STEPS=40 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py
```

### 查看 V2 四终端运行说明

```bash
cd ~/robot-learning/rm-ik-rl
bash scripts/run_moveit2_isaac_link6_gripper_v2.sh
```

### 运行 pre-grasp + RL grasp V0

```bash
cd ~/robot-learning/rm-ik-rl
bash scripts/run_pregrasp_then_rl_grasp_v0.sh
```

## 文档入口

- [00 今日 IK 执行清单](docs/00-today-ik.md)
- [01 GitHub 零基础指南](docs/01-github-guide.md)
- [02 一个月项目与求职路线](docs/02-one-month-roadmap.md)
- [03 机器人算法知识地图](docs/03-algorithm-learning.md)
- [04 RL reaching baseline](docs/04-rl-reaching-baseline.md)
- [06 MoveIt2 RM65 demo notes](docs/06-moveit2-rm65-demo-notes.md)
- [07 MoveIt2 + Isaac Sim + ros2_control 联动](docs/07-moveit2-isaac-ros2-control-integration.md)
- [08 RL grasping baseline](docs/08-rl-grasping-baseline.md)
- [09 Pre-grasp + RL grasp 组合流程](docs/09-pregrasp-rl-grasp-combo.md)
- [10 项目分块地图](docs/10-project-block-map.md)
- [11 RM65 link_6 跟随夹爪 V1](docs/11-link6-follow-gripper-v1.md)
- [12 MoveIt2 + Isaac bridge + link_6 跟随夹爪 V2](docs/12-bridge-with-link6-gripper-v2.md)

## 不上传的内容

为了安全和仓库体积，本仓库不上传：

```text
Isaac Sim 安装包
USD 大模型资产
训练权重 .pt / .pth / .ckpt
__pycache__
日志文件
.env / API key / SSH 私钥
```

`.gitignore` 已经配置了这些规则。

## 当前项目定位

这个仓库目前是一个从机械臂 IK 到 MoveIt2 工程控制，再到 RL 局部抓取的学习型作品集项目。它还不是完整工业抓取系统，但已经具备清晰的工程链路和可继续扩展的结构。
