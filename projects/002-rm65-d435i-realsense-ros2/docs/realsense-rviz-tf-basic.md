# RealSense + RViz + TF 新手解释

## 1. 为什么我一开始只看到相机，没有机械臂？

因为相机节点和机械臂节点是两套东西。

启动 D435i：

```bash
ros2 launch realsense2_camera rs_launch.py
```

只会发布相机图像、深度图和相机坐标系。

启动 RM65：

```bash
ros2 launch rm_65_config demo.launch.py
```

才会显示机械臂模型和 MoveIt2 面板。

如果想在同一个 RViz 里同时看到两者，需要两套节点都启动。

## 2. ROS2 topic 是什么？

topic 可以理解成 ROS2 系统里的数据频道。

D435i 发布的图像 topic：

```text
/camera/camera/color/image_raw
```

深度图 topic：

```text
/camera/camera/depth/image_rect_raw
```

RViz 订阅这些 topic，就能显示图像。

## 3. camera_info 是什么？

例如：

```text
/camera/camera/color/camera_info
```

里面包含相机内参，比如焦距、主点、图像宽高等。

后面如果要从图像像素反推空间点，会用到 camera_info。

## 4. TF 是什么？

TF 是 ROS 里管理坐标系关系的工具。

比如机械臂里有：

```text
base_link
Link1
Link2
...
Link6
```

相机里有：

```text
camera_link
camera_color_optical_frame
camera_depth_optical_frame
```

如果没有 TF 连接，系统不知道：

```text
相机在机械臂哪里？
```

## 5. 为什么要发布 Link6 -> camera_link？

因为当前假设 D435i 装在机械臂末端附近。

所以先临时发布：

```text
Link6 -> camera_link
```

这样相机坐标系就进入机械臂坐标树了。

## 6. 当前临时 TF 是什么意思？

命令：

```bash
ros2 run tf2_ros static_transform_publisher 0.05 0 0.08 0 0 0 Link6 camera_link
```

意思是：

```text
camera_link 相对 Link6：
前方 0.05 m
左右 0 m
上方 0.08 m
旋转先设为 0
```

这只是为了让系统先连起来，不代表真实安装位置。

## 7. 什么是 optical frame？

RealSense 图像一般绑定在 optical frame 上，例如：

```text
camera_color_optical_frame
camera_depth_optical_frame
```

图像中的像素坐标、深度值，通常都和 optical frame 有关。

后面做视觉定位时，要特别注意使用哪个 frame。

## 8. 现在距离真正抓取还差什么？

当前完成的是：

```text
相机能看
机械臂能显示
TF 临时连上
```

真正抓取还需要：

```text
检测物体
得到物体在相机坐标系的位置
通过 TF 转到 base_link
MoveIt2 规划到抓取点
夹爪闭合
```
