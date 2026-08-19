# 002 - RM65 + D435i RealSense ROS2 接入

这个小项目是在 `001-rm65-moveit2-rviz-ik` 的基础上，加入真实 D435i 相机。

目标不是马上做识别和抓取，而是先完成最基础、最重要的一步：

> 在同一个 RViz 里同时看到 RM65 机械臂模型和 D435i 相机图像，并用临时 TF 把相机坐标系挂到机械臂末端 `Link6` 下。

## 当前完成状态

- [x] Linux 能识别 D435i 硬件；
- [x] `librealsense` 能读取 D435i 信息；
- [x] `realsense-ros` 能发布 RGB / Depth 话题；
- [x] RViz 能显示 D435i 彩色图像；
- [x] RViz 能同时显示 RM65 机械臂和 D435i 图像；
- [x] 临时发布 `Link6 -> camera_link` TF；
- [x] 在 RViz 的 TF Frames 中看到 `camera_link`、`camera_color_optical_frame`、`camera_depth_optical_frame`。

还没完成：

- [ ] 精确测量真实相机相对机械臂的安装外参；
- [ ] 手眼标定；
- [ ] 用图像或点云定位物体；
- [ ] 把物体坐标转成机械臂抓取目标。

## 为什么要做这个小项目

后面如果要让机械臂根据相机抓东西，需要先打通这条链路：

```text
真实 D435i 相机
↓
ROS2 图像/深度话题
↓
RViz 显示
↓
相机坐标系进入 TF 树
↓
相机坐标能转换到机械臂坐标
```

这一步完成后，后续才能继续做：

```text
相机看物体
↓
估计物体位置
↓
转换到 RM65 base_link 坐标系
↓
MoveIt2 规划到抓取点
```

## 本项目用到的硬件和环境

硬件：

- RealSense D435i
- RM65 机械臂模型 / MoveIt2 配置
- 实验室 Ubuntu 电脑

软件：

- Ubuntu 22.04
- ROS2 Humble
- MoveIt2
- Intel RealSense SDK / `librealsense`
- `realsense-ros`
- RViz2

## 1. 检查 Linux 是否识别 D435i

```bash
lsusb | grep -i realsense
```

成功输出示例：

```text
Bus 001 Device 006: ID 8086:0b3a Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i
```

这说明电脑通过 USB 识别到了 D435i。

## 2. 检查 RealSense SDK 是否能读到相机

```bash
rs-enumerate-devices
```

本次测试读到的信息：

```text
Name                          : Intel RealSense D435I
Serial Number                 : <hidden>
Firmware Version              : 5.15.1.55
Recommended Firmware Version  : 5.17.0.9
Usb Type Descriptor           : 2.1
Product Line                  : D400
```

说明：

- 相机硬件连接成功；
- `librealsense` 能正常读取相机；
- 当前连接是 USB 2.1，不是理想的 USB 3.0；
- 固件版本低于推荐版本，但当前阶段先不升级。

## 3. 启动 D435i ROS2 驱动

终端 1：

```bash
cd ~/realsense_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

这个终端不要关。

它会启动 `realsense2_camera` 节点，把相机数据发布成 ROS2 topic。

## 4. 检查相机 ROS2 话题

新开终端：

```bash
source /opt/ros/humble/setup.bash
source ~/realsense_ws/install/setup.bash
ros2 topic list | grep camera
```

本次成功看到：

```text
/camera/camera/color/camera_info
/camera/camera/color/image_raw
/camera/camera/depth/camera_info
/camera/camera/depth/image_rect_raw
/camera/camera/extrinsics/depth_to_color
```

这些分别表示：

- 彩色图像；
- 彩色相机内参；
- 深度图；
- 深度相机内参；
- depth 到 color 的外参。

## 5. 在 RViz 中显示相机图像

打开 RViz：

```bash
rviz2
```

在 RViz 里：

```text
Add
→ By topic
→ /camera/camera/color/image_raw
→ Image
→ OK
```

成功后，可以在 RViz 左侧或下方看到真实 D435i 彩色图像。

## 6. 同时启动 RM65 MoveIt2 RViz

如果要在同一个 RViz 里看到 RM65 机械臂，启动：

```bash
cd ~/robot-learning/rm_moveit2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch rm_65_config demo.launch.py
```

然后在这个 RViz 里继续 Add 相机图像：

```text
Add
→ By topic
→ /camera/camera/color/image_raw
→ Image
```

成功后，同一个 RViz 里会同时显示：

```text
RM65 机械臂模型
+
D435i 真实相机图像
```

## 7. 查看相机 frame 名字

```bash
source /opt/ros/humble/setup.bash
source ~/realsense_ws/install/setup.bash
ros2 topic echo /camera/camera/color/camera_info --once | grep frame_id
ros2 topic echo /camera/camera/depth/camera_info --once | grep frame_id
```

本次输出：

```text
frame_id: camera_color_optical_frame
frame_id: camera_depth_optical_frame
```

## 8. 发布临时 TF：Link6 -> camera_link

当前为了先把坐标树连起来，临时假设相机装在 `Link6` 附近：

```bash
source /opt/ros/humble/setup.bash
ros2 run tf2_ros static_transform_publisher 0.05 0 0.08 0 0 0 Link6 camera_link
```

含义：

```text
camera_link 相对 Link6：
x = 0.05 m
y = 0
z = 0.08 m
roll/pitch/yaw = 0
```

注意：这只是临时外参，不是真实标定结果。

## 9. 在 RViz 中添加 TF

在 RViz 里：

```text
Add
→ By display type
→ rviz_default_plugins
→ TF
→ OK
```

然后展开：

```text
TF
→ Frames
```

本次成功看到：

```text
Link6
camera_link
camera_color_frame
camera_color_optical_frame
camera_depth_frame
camera_depth_optical_frame
```

并且：

```text
camera_link
  Parent: Link6
  Relative Position: 0.05; 0; 0.08
```

这说明：

```text
RM65 坐标树和 D435i 相机坐标树已经临时连接成功。
```

## 遇到的问题

### 1. RViz 里只有相机，没有机械臂

原因：

只启动了 RealSense 驱动，没有启动 RM65 MoveIt2 demo。

解决：

同时启动：

```bash
ros2 launch rm_65_config demo.launch.py
```

### 2. RViz 里只有机械臂，没有相机图像

原因：

没有在 RViz 里添加 Image 显示项。

解决：

```text
Add
→ By topic
→ /camera/camera/color/image_raw
→ Image
```

### 3. 出现 Orbbec 路径提示

提示：

```text
not found: "/home/iot22/Ros2Workspaces/orbbec_ws/install/local_setup.bash"
```

原因：

当前 shell 配置里残留了旧的 Orbbec 相机工作区路径。

它不影响 D435i，这个问题后面可以单独清理。

### 4. 图像方向看起来旋转了

这是因为相机实际摆放方向、RViz Image 面板显示方向和 optical frame 定义可能不同。

当前阶段只验证图像能显示，不处理图像方向。

## 当前结论

这个小项目已经完成了从真实 D435i 到 ROS2/RViz 的基础接入，并把相机坐标系临时挂到了 RM65 的 `Link6` 下。

但目前还不是精确标定。后面如果要真的根据图像抓取，需要做：

```text
相机安装外参测量 / 手眼标定
点云或图像目标检测
目标点从 camera frame 转到 base_link
MoveIt2 规划抓取动作
```
