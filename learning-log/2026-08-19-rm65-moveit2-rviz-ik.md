# 2026-08-19 - RM65 MoveIt2 + RViz 输入目标点规划

## 本阶段目标

用 RViz + MoveIt2 做一个最小可展示的小项目：

```text
输入一个目标点
↓
RM65 机械臂规划轨迹
↓
执行到目标点
↓
停住
```

## 做了什么

1. 打开 RM65 官方 MoveIt2 demo：

```bash
ros2 launch rm_65_config demo.launch.py
```

2. 使用自己写的 `plan_pose.cpp` 输入目标点。

3. 通过 launch 参数传入目标坐标：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

4. 在 RViz 里观察机械臂规划、执行、停止。

5. 理解了 RViz 里的残影不是 bug，而是 `Planned Path` 轨迹预览。

## 新增/修改了哪些文件

新增第一个独立小项目目录：

```text
projects/001-rm65-moveit2-rviz-ik/
```

里面包含：

```text
rm_moveit2_examples/
docs/
README.md
```

## 遇到的问题

### 1. 机械臂看起来一直重复动

原因：

RViz 的 `Planned Path` 会显示规划轨迹残影，有时看起来像机械臂一直循环动。

解决：

在 RViz 左侧：

```text
MotionPlanning
  Planned Path
    Show Robot Visual
```

取消勾选可以隐藏残影。

### 2. 输入某些目标点后机械臂不动

例如：

```bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=-0.35 y:=-0.30 z:=0.60
```

出现：

```text
Planning failed.
```

原因：

目标点可能位置偏、姿态固定过死，MoveIt2 在规划时间内找不到可行路径。

解决：

先使用更稳定的测试点：

```bash
x:=0.30 y:=0.20 z:=0.40
x:=0.25 y:=-0.25 z:=0.45
x:=0.35 y:=0.00 z:=0.40
```

## 现在能运行什么命令

第一个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

第二个终端：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

## 下一步是什么

下一步可以做：

```text
002 - RM65 MoveIt2 + Isaac Sim 联动
```

也就是把 MoveIt2 规划出来的关节轨迹发给 Isaac Sim，让 Isaac 里的 RM65 也跟着动。

## 你需要理解的核心概念

- RViz 是可视化工具，不是物理仿真器；
- MoveIt2 是机械臂运动规划框架；
- IK 是从目标位姿反算关节角；
- 运动规划不只是 IK，还要考虑从当前状态到目标状态怎么走；
- 目标点规划失败不等于程序错，可能是机械臂到不了或姿态约束太死。
