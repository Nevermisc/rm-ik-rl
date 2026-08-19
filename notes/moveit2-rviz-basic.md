# MoveIt2 + RViz 基础笔记

这份笔记服务于第一个小项目：

```text
projects/001-rm65-moveit2-rviz-ik
```

## 一句话理解

```text
RViz 负责看见机器人
MoveIt2 负责规划机器人怎么动
ros2_control / controller 负责执行轨迹
```

## 当前 RM65 配置

MoveIt2 planning group：

```text
rm_group
```

末端 link：

```text
Link6
```

当前使用的 IK solver：

```text
kdl_kinematics_plugin/KDLKinematicsPlugin
```

常见规划器：

```text
OMPL / RRTConnect
```

## 新手最容易混淆的点

### 1. IK 不是完整运动规划

IK 只回答：

```text
末端到目标点时，关节应该是什么角度？
```

完整运动规划还要回答：

```text
从现在的角度怎么走到目标角度？
```

### 2. RViz 里的残影不是 bug

残影是规划轨迹预览。

### 3. `source install/setup.bash` 很重要

如果不执行：

```bash
source install/setup.bash
```

ROS2 可能找不到自己写的包：

```text
Package 'rm_moveit2_examples' not found
```

### 4. 目标点不是随便输都能成功

因为机械臂有：

- 工作空间限制；
- 关节角限制；
- 姿态限制；
- 碰撞约束；
- 规划时间限制。
