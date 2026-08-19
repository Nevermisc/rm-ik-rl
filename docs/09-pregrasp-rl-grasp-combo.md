# MoveIt2 Pre-grasp + RL Grasp 组合流程

本阶段目标是把前面的两个能力组合起来：

```text
MoveIt2：负责把 RM65-B 移动到 pre-grasp 位姿
RL policy：负责夹爪闭合与上抬，完成局部抓取
```

这不是最终的“机械臂 6 关节 + 夹爪联合 RL”，而是一个更工程化、更稳的组合路线。

## 为什么这样做

直接做联合 RL 的 action 会变成：

```text
joint1 ~ joint6 + gripper action
```

这会显著增加探索难度。对当前项目来说，更合理的第一版是：

```text
传统规划解决大范围运动
RL 解决接触阶段的局部抓取
```

这也是机器人抓取里常见的工程拆分方式。

## V0 流程

V0 组合流程分两段：

```text
阶段 A：MoveIt2 pre-grasp
  输入目标位姿
  RM65-B 规划并移动到物体附近

阶段 B：RL gripper grasp
  加载训练好的策略
  控制简化夹爪闭合并上抬
  判断 cube 是否被抬起
```

当前 V0 还没有把 RL 简化夹爪刚性挂接到 Isaac 中的 RM65 真实末端 articulation 上。

原因是 RM65-B 当前 USD 资产只有 6 个机械臂关节，没有真实夹爪关节。我们先验证组合流程，再逐步做完整挂接。

## 运行前提

### 终端 1：Isaac Sim ROS2 bridge

```bash
cd ~/robot-learning/rm-ik-rl
~/isaac-sim-5.1.0/python.sh rm65_isaac_ros2_bridge.py
```

### 终端 2：ros2_control

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_moveit2_examples isaac_control_test.launch.py
```

### 终端 3：move_group

```bash
cd ~/robot-learning/rm_moveit2_ws
source install/setup.bash
ros2 launch rm_65_config move_group.launch.py
```

### 终端 4：执行组合流程

```bash
cd ~/robot-learning/rm-ik-rl
bash scripts/run_pregrasp_then_rl_grasp_v0.sh
```

## 当前组合脚本做什么

文件：

```text
scripts/run_pregrasp_then_rl_grasp_v0.sh
```

它会先执行：

```text
MoveIt2 目标位姿规划
```

再执行：

```text
RL policy 抓取评估
```

## 当前限制

V0 的限制要说清楚：

```text
pre-grasp 和 RL grasp 还是两个阶段式流程
RL 夹爪还不是 RM65 USD articulation 的真实子关节
没有物体位姿感知闭环
没有真实夹爪模型
```

但 V0 的价值是：

```text
把传统规划和学习抓取放进同一个工程流程里
后续可以逐步替换成更真实的夹爪和更完整的任务
```

## 下一步升级

下一步可以做：

```text
1. 把简化夹爪挂接到 RM65 link_6 附近
2. 让 pre-grasp 的目标点与 cube 位置一致
3. 把 cube 位置随机化
4. 将 observation 扩展为 arm state + gripper state + object pose
5. 再考虑 joint1~joint6 + gripper 的联合 RL
```

