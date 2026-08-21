# RM65 机器人学习项目

这是我的机器人 manipulation / 抓取规划学习仓库。

我目前是从机械背景转向机器人算法与工程开发，所以这个仓库不追求一上来做一个“大而全”的系统，而是按小项目一步一步推进：

```text
001    先会用 RViz + MoveIt2 让 RM65 到单个目标点
001-v2 升级成连续目标点交互节点
001-v3 让 RM65 末端在空中画一个圆
002    接入真实 D435i 相机，并在 RViz 中和 RM65 同屏显示
003    再把 MoveIt2 和 Isaac Sim 联动
004    再加入简化夹爪
005    再做强化学习抓取 baseline
006    最后整理成求职作品集
```

每个小项目都尽量做到：

- 文件夹独立；
- README 能单独看懂；
- 有能复现的运行命令；
- 记录我遇到的问题和解决方法；
- 学到的概念和代码能对应起来。

## 项目目录

```text
rm-ik-rl/
├── projects/       # 一个个独立小项目
├── learning-log/   # 按日期/阶段记录我做了什么
├── notes/          # ROS2、MoveIt2、Isaac Sim 等基础笔记
├── docs/           # 早期总文档和阶段总结
├── isaac_sim/      # Isaac Sim 实验脚本
├── ros2_control/   # ros2_control 自定义硬件接口实验
├── scripts/        # 运行脚本
└── README.md       # 总入口
```

## 当前小项目

### 001 - RM65 MoveIt2 + RViz 目标点规划演示

目录：

```text
projects/001-rm65-moveit2-rviz-ik/
```

目标：

```text
在 RViz 中显示 RM65，通过一次性 launch 输入目标点，让 MoveIt2 规划并执行。
```

入口文档：

- [001 小项目 README](projects/001-rm65-moveit2-rviz-ik/README.md)
- [RViz + MoveIt2 新手解释](projects/001-rm65-moveit2-rviz-ik/docs/rviz-moveit2-basic.md)
- [2026-08-19 学习日志](learning-log/2026-08-19-rm65-moveit2-rviz-ik.md)

### 001-v2 - RM65 MoveIt2 交互式连续目标点 Demo

目录：

```text
projects/001-v2-rm65-moveit2-interactive-target/
```

目标：

```text
启动一个常驻 ROS2 节点，通过 /rm65_target_point 连续发送目标点，让机械臂从上一次终点继续规划。
```

入口文档：

- [001-v2 小项目 README](projects/001-v2-rm65-moveit2-interactive-target/README.md)

### 001-v3 - RM65 MoveIt2 空中画圆 Demo

目录：

```text
projects/001-v3-rm65-moveit2-draw-circle/
```

目标：

```text
先移动到圆的起点，再通过 Cartesian Path 让 Link6 在空中沿圆形路径运动。
```

入口文档：

- [001-v3 小项目 README](projects/001-v3-rm65-moveit2-draw-circle/README.md)

### 002 - RM65 + D435i RealSense ROS2 接入

目录：

```text
projects/002-rm65-d435i-realsense-ros2/
```

目标：

```text
在同一个 RViz 中同时显示 RM65 机械臂和 D435i 真实相机图像，并用临时 TF 把 camera_link 挂到 Link6 下。
```

入口文档：

- [002 小项目 README](projects/002-rm65-d435i-realsense-ros2/README.md)
- [RealSense + RViz + TF 新手解释](projects/002-rm65-d435i-realsense-ros2/docs/realsense-rviz-tf-basic.md)
- [2026-08-19 D435i 学习日志](learning-log/2026-08-19-rm65-d435i-realsense-ros2.md)

## 已完成阶段

- [x] 跑通 Isaac Sim 官方 Franka IK 示例
- [x] 导入 RM65-B URDF/USD 并验证 articulation
- [x] 跑通 Isaac Sim 里的 RM65 传统 IK 演示
- [x] 跑通 RM65 官方 MoveIt2 RViz demo
- [x] 写出自己的 MoveIt2 目标点规划程序 `plan_pose.cpp`
- [x] 整理第一个独立小项目：`001-rm65-moveit2-rviz-ik`
- [x] 整理升级项目：`001-v2-rm65-moveit2-interactive-target`
- [x] 整理升级项目：`001-v3-rm65-moveit2-draw-circle`
- [x] 整理第二个独立小项目：`002-rm65-d435i-realsense-ros2`
- [ ] 整理第三个独立小项目：MoveIt2 + Isaac Sim 联动
- [ ] 整理第四个独立小项目：简化夹爪抓取
- [ ] 整理第五个独立小项目：强化学习抓取 baseline

## 为什么要这样分文件夹

因为我是新手阶段，如果所有代码都堆在根目录，会很难知道：

- 哪个文件属于哪个阶段；
- 哪个脚本现在还能跑；
- 哪些是失败实验；
- 哪些可以放进简历项目。

所以这个仓库从现在开始采用“小项目制”：

```text
projects/001-xxx
projects/001-v2-xxx
projects/001-v3-xxx
projects/002-xxx
```

以后每完成一个阶段，就新建一个编号文件夹。

## 旧实验和工程脚本

根目录、`docs/`、`isaac_sim/`、`ros2_control/`、`scripts/` 里还有前面阶段留下的工程脚本和文档。

这些内容暂时不删除、不大规模移动，原因是：

```text
先保证旧代码还能运行
再逐步整理成 projects/003、projects/004、projects/005
最后再把废弃实验归档到 archive/
```

当前旧文档入口包括：

- [GitHub 零基础指南](docs/01-github-guide.md)
- [一个月项目与求职路线](docs/02-one-month-roadmap.md)
- [机器人算法知识地图](docs/03-algorithm-learning.md)
- [MoveIt2 RM65 demo notes](docs/06-moveit2-rm65-demo-notes.md)
- [MoveIt2 + Isaac Sim + ros2_control 联动](docs/07-moveit2-isaac-ros2-control-integration.md)
- [RL grasping baseline](docs/08-rl-grasping-baseline.md)
- [项目分块地图](docs/10-project-block-map.md)

## 不上传的内容

以下内容不放进 GitHub：

- Isaac Sim 安装包；
- 大型 USD/模型资源；
- 训练权重 `.pt` / `.pth` / `.ckpt`；
- API key、token、密码；
- 临时日志、缓存、`__pycache__`；
- 真实设备序列号等不必要公开的硬件标识。

这些内容只保存在实验室电脑或本地环境。