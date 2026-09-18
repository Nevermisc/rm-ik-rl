# 001-v3 - RM65 MoveIt2 空中画圆 Demo

这个小项目是 `001-v2` 的下一步。

`001-v2` 做的是：

```text
给一个目标点
机械臂移动到这个点
停住
等待下一个点
```

`001-v3` 做的是：

```text
给一个圆心和半径
机械臂末端先移动到圆的起点
然后沿着一串圆形路径点运动
在空中画一个圆
```

它依然只用于 RViz / MoveIt2 / fake controller 演示，不控制真实机械臂。

## 这个 demo 的目标

让机械臂末端 `Link6` 在空中画一个竖直平面里的圆。

默认圆参数：

```text
圆心：x=0.30, y=0.00, z=0.45
半径：0.05 m
平面：YZ 平面
```

也就是说，x 基本固定，y 和 z 按圆形变化。

## 这个 demo 分成几个小块

### 1. MoveIt2 官方模型与配置

仍然使用睿尔曼官方 RM65 MoveIt2 配置：

- `rm_65_config`
- planning group：`rm_group`
- end effector link：`Link6`

### 2. 圆参数

程序读取 launch 参数：

```text
center_x
center_y
center_z
radius
samples
eef_step
```

这些参数决定圆在哪里、半径多大、分成多少个路径点。

### 3. 生成圆形路径点

代码会生成一串末端位姿：

```text
x = center_x
y = center_y + radius * cos(theta)
z = center_z + radius * sin(theta)
```

这就是一个竖直平面中的圆。

### 4. 先移动到圆起点

机械臂不会直接开始画圆，而是先规划到圆的第一个点。

这样做更稳，也更符合真实项目逻辑：

```text
先到起笔点
再开始画圆
```

### 5. Cartesian Path 画圆

到达起点后，程序调用 MoveIt2 的 Cartesian Path：

```cpp
move_group.computeCartesianPath(...)
```

它的目标不是只到一个终点，而是尽量让末端沿着给定路径点走。

### 6. RViz 可视化

程序会发布一个绿色圆形线框 marker：

```text
/circle_path_marker
```

用于显示理论上的圆路径。

## 文件结构

```text
001-v3-rm65-moveit2-draw-circle/
├── README.md
└── rm65_moveit2_draw_circle/
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── draw_circle.launch.py
    └── src/
        └── draw_circle.cpp
```

## 编译

把 `rm65_moveit2_draw_circle` 放进 ROS2 工作区的 `src` 后：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rm65_moveit2_draw_circle --symlink-install
source install/setup.bash
```

## 运行

第一个终端，启动 RViz + MoveIt2：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

第二个终端，启动画圆 demo：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm65_moveit2_draw_circle draw_circle.launch.py
```

也可以改参数：

```bash
ros2 launch rm65_moveit2_draw_circle draw_circle.launch.py center_x:=0.30 center_y:=0.00 center_z:=0.45 radius:=0.05 samples:=36
```

## 如果规划失败

常见原因：

1. 圆心太远，超出工作空间；
2. 半径太大；
3. 固定末端姿态 `orientation.w = 1.0` 时某些点不可达；
4. Cartesian Path 要求末端沿路径走，比单点 IK 更严格。

可以先尝试：

```text
radius = 0.03
center_x = 0.30
center_y = 0.00
center_z = 0.45
```

## 这个 demo 的意义

`001-v3` 比 `001-v2` 更接近轨迹任务。

它让我从：

```text
点到点运动
```

进入到：

```text
末端沿指定轨迹运动
```

这对后面的抓取、擦拭、画线、扫描、视觉伺服都很重要。