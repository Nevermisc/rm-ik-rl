# RealSense ROS2 基础笔记

## 一句话理解

```text
D435i 通过 librealsense 被 Linux 读取
realsense-ros 把相机数据发布成 ROS2 topic
RViz 订阅这些 topic 并显示图像
TF 把相机坐标系接进机械臂坐标树
```

## 常用检查命令

检查 USB 是否识别：

```bash
lsusb | grep -i realsense
```

检查 RealSense SDK：

```bash
rs-enumerate-devices
```

启动 ROS2 相机节点：

```bash
ros2 launch realsense2_camera rs_launch.py
```

查看相机话题：

```bash
ros2 topic list | grep camera
```

查看图像 frame：

```bash
ros2 topic echo /camera/camera/color/camera_info --once | grep frame_id
```

## 重要 topic

彩色图像：

```text
/camera/camera/color/image_raw
```

深度图：

```text
/camera/camera/depth/image_rect_raw
```

彩色相机内参：

```text
/camera/camera/color/camera_info
```

深度相机内参：

```text
/camera/camera/depth/camera_info
```

## 重要 frame

本次 D435i 输出：

```text
camera_color_optical_frame
camera_depth_optical_frame
```

临时挂载到机械臂：

```text
Link6 -> camera_link
```

## USB 2.1 提醒

如果 `rs-enumerate-devices` 显示：

```text
Usb Type Descriptor : 2.1
```

说明当前不是 USB 3.0。

可能影响：

- 高分辨率 RGB；
- 高帧率 depth；
- 点云稳定性。

新手阶段可以先继续用，但后面正式做点云/抓取时建议换 USB 3.0。

## 固件提醒

本次相机：

```text
Firmware Version              : 5.15.1.55
Recommended Firmware Version  : 5.17.0.9
```

当前不急着升级固件。只有当驱动不稳定或官方文档明确要求时，再考虑升级。
