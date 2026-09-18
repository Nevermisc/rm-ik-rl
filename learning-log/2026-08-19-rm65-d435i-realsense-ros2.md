# 2026-08-19 - RM65 + D435i RealSense ROS2 接入

## 本阶段目标

把真实 D435i 相机接入 ROS2，并在同一个 RViz 中同时看到：

```text
RM65 机械臂模型
+
D435i 真实相机图像
+
相机 TF 坐标系
```

## 做了什么

1. 检查 Linux 是否识别 D435i：

```bash
lsusb | grep -i realsense
```

2. 检查 `librealsense` 是否能读相机：

```bash
rs-enumerate-devices
```

3. 启动 D435i ROS2 驱动：

```bash
cd ~/realsense_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

4. 查看相机 topic：

```bash
ros2 topic list | grep camera
```

5. 在 RViz 中添加 RGB Image：

```text
Add
→ By topic
→ /camera/camera/color/image_raw
→ Image
```

6. 启动 RM65 MoveIt2 demo：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

7. 检查相机 frame：

```bash
ros2 topic echo /camera/camera/color/camera_info --once | grep frame_id
ros2 topic echo /camera/camera/depth/camera_info --once | grep frame_id
```

8. 发布临时 TF：

```bash
ros2 run tf2_ros static_transform_publisher 0.05 0 0.08 0 0 0 Link6 camera_link
```

9. 在 RViz 中添加 TF，并确认 `camera_link` 的 parent 是 `Link6`。

## 新增/修改了哪些文件

新增：

```text
projects/002-rm65-d435i-realsense-ros2/
projects/002-rm65-d435i-realsense-ros2/docs/realsense-rviz-tf-basic.md
learning-log/2026-08-19-rm65-d435i-realsense-ros2.md
notes/realsense-ros2-basic.md
```

## 遇到的问题

### 1. 一开始只看到相机，没有机械臂

原因：

只启动了 `realsense2_camera`，没有启动 RM65 MoveIt2 demo。

解决：

同时启动：

```bash
ros2 launch rm_65_config demo.launch.py
```

### 2. 在 RM65 RViz 里 Add 后看不到相机

原因：

需要添加的是 Image display，不是 TF 或 MotionPlanning。

解决：

```text
Add
→ By topic
→ /camera/camera/color/image_raw
→ Image
```

### 3. 出现 Orbbec 旧路径提示

提示：

```text
not found: "/home/iot22/Ros2Workspaces/orbbec_ws/install/local_setup.bash"
```

原因：

系统里残留了旧 Orbbec 工作区 source 路径。

暂时不影响 D435i。

### 4. D435i 是 USB 2.1

`rs-enumerate-devices` 显示：

```text
Usb Type Descriptor : 2.1
```

说明当前连接不是理想 USB 3.0。后面如果图像/点云卡顿，优先检查 USB 口和线。

## 现在能运行什么命令

启动 RM65：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

启动 D435i：

```bash
cd ~/realsense_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

发布临时 TF：

```bash
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher 0.05 0 0.08 0 0 0 Link6 camera_link
```

## 下一步是什么

下一步可以做：

```text
003 - 相机看到物体，并把物体位置转换到 RM65 base_link 坐标系
```

或者继续完善 002：

```text
测量真实 D435i 安装位姿
把临时 TF 改成更接近真实安装的 TF
显示 depth image / pointcloud
```

## 你需要理解的核心概念

- 相机节点和机械臂节点是两套 ROS2 系统；
- RViz 可以同时显示多个 topic 和多个 TF；
- 图像能显示不代表坐标已经对齐；
- TF 是让相机坐标和机械臂坐标发生关系的关键；
- 临时 TF 只是工程占位，后面要靠测量或标定改准。
