# Projects

这个目录用来按阶段整理我的 RM65 机器人学习项目。

每个子目录都是一个尽量独立的小项目，目标是让新手也能看懂：

```text
这个阶段做了什么
需要什么环境
怎么运行
成功时应该看到什么
遇到了什么问题
学到了什么概念
```

## 当前项目列表

### 001 - RM65 MoveIt2 + RViz 目标点规划演示

目录：

```text
projects/001-rm65-moveit2-rviz-ik/
```

目标：

```text
在 RViz 中显示 RM65，通过一次性 launch 输入目标点，让 MoveIt2 规划并执行。
```

入口：

- [001 项目 README](001-rm65-moveit2-rviz-ik/README.md)
- [RViz + MoveIt2 新手解释](001-rm65-moveit2-rviz-ik/docs/rviz-moveit2-basic.md)

### 001-v2 - RM65 MoveIt2 交互式连续目标点 Demo

目录：

```text
projects/001-v2-rm65-moveit2-interactive-target/
```

目标：

```text
启动一个常驻 ROS2 节点，通过 /rm65_target_point 连续发送目标点，让机械臂从上一次终点继续规划。
```

入口：

- [001-v2 项目 README](001-v2-rm65-moveit2-interactive-target/README.md)

### 001-v3 - RM65 MoveIt2 空中画圆 Demo

目录：

```text
projects/001-v3-rm65-moveit2-draw-circle/
```

目标：

```text
先移动到圆的起点，再通过 Cartesian Path 让 Link6 在空中沿圆形路径运动。
```

入口：

- [001-v3 项目 README](001-v3-rm65-moveit2-draw-circle/README.md)

## 后续计划

```text
002 - RM65 + D435i RealSense + RViz 可视化
003 - RM65 MoveIt2 + Isaac Sim 联动
004 - RM65 简化夹爪抓取
005 - RM65 强化学习抓取 baseline
```

旧实验代码暂时保留在仓库根目录和原有目录中，后续会逐步整理进对应的 `projects/00x-*` 文件夹。