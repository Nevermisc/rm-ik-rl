# RViz + MoveIt2 新手解释

## 1. RViz 是仿真平台吗？

不是。

RViz 更像“机器人系统的可视化界面”。它可以显示：

- 机械臂模型；
- 当前关节状态；
- 目标姿态；
- MoveIt2 规划出来的轨迹；
- 坐标系；
- 点云、相机、传感器数据。

但 RViz 本身不是物理仿真器。它不会真实计算碰撞后的物体运动，也不会模拟夹爪抓住方块。

如果要物理仿真，后面会用 Isaac Sim。

## 2. MoveIt2 是什么？

MoveIt2 是 ROS2 里的机械臂运动规划框架。

在这个小项目里，我把它先理解成：

> 我给机械臂末端一个目标点，MoveIt2 帮我算出一条机械臂可以走过去的关节轨迹。

它背后会涉及：

- 机械臂模型 URDF；
- 语义模型 SRDF；
- IK 求解器；
- 运动规划器；
- 控制器接口；
- 碰撞检测。

但新手阶段先不用全都吃透。

## 3. IK 是什么？

IK 是 Inverse Kinematics，中文叫逆运动学。

通俗说：

```text
我想让机械臂末端到某个位置
↓
IK 计算每个关节应该转多少角度
```

比如我输入：

```text
x = 0.30
y = 0.20
z = 0.40
```

IK 要回答：

```text
joint1 转多少？
joint2 转多少？
joint3 转多少？
...
joint6 转多少？
```

## 4. MoveIt2 里的 IK 和规划是什么关系？

这两个不是完全一样的东西。

IK 更像是：

```text
目标点 → 一个可能的关节姿态
```

运动规划更像是：

```text
当前关节姿态 → 目标关节姿态 → 中间怎么安全走过去
```

所以 MoveIt2 做的是一整套流程：

```text
目标末端位姿
↓
求一个目标关节姿态
↓
检查关节限制和碰撞
↓
规划从当前状态到目标状态的路径
↓
发送轨迹给控制器执行
```

## 5. 为什么有些目标点不能到？

常见原因：

1. 目标超出机械臂工作空间；
2. 目标位置能到，但末端姿态不能满足；
3. 某些关节会超过限制；
4. 中间路径可能碰撞；
5. 规划时间太短，规划器没找到路径。

这个项目里的 `plan_pose.cpp` 目前固定了末端姿态：

```cpp
target_pose.orientation.w = 1.0;
```

所以它不是“只要位置到就行”，而是要求位置和姿态一起满足。

这会让某些点规划失败。

## 6. Plan、Execute、Plan & Execute 区别

在 RViz 的 MotionPlanning 面板里：

```text
Plan
```

只规划，不真正执行。你会看到残影或轨迹预览。

```text
Execute
```

执行刚才规划好的路径。

```text
Plan & Execute
```

先规划，再执行。新手阶段最推荐用这个。

## 7. 残影是什么？

残影是 MoveIt2 规划出来的中间轨迹显示。

它表示：

```text
机械臂从当前位置去目标点，中间大概会经过这些姿态。
```

它不是真的有很多机械臂，也不是机械臂坏了。

## 8. 为什么我看到机械臂一直动？

可能有两种情况。

第一种：

```text
Planned Path 在循环播放轨迹预览
```

这不是机械臂真的一直执行。

第二种：

```text
后台有旧脚本还在跑
```

比如 Isaac Sim 的循环 IK 演示脚本。

如果要重新开始，最稳的方式是：

```bash
Ctrl + C
```

关掉所有正在刷日志的终端，然后重新启动 RViz。

## 9. 当前项目的标准演示方式

第一个终端打开 RViz：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

第二个终端输入目标点：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40
```

成功标志：

```text
Planning succeeded.
Execution succeeded.
```
