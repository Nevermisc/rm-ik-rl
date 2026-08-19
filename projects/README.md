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
在 RViz 中显示 RM65，通过终端输入目标点，让 MoveIt2 规划并执行，机械臂到达后停住。
```

入口：

- [001 项目 README](001-rm65-moveit2-rviz-ik/README.md)
- [RViz + MoveIt2 新手解释](001-rm65-moveit2-rviz-ik/docs/rviz-moveit2-basic.md)

## 后续计划

```text
002 - RM65 MoveIt2 + Isaac Sim 联动
003 - RM65 简化夹爪抓取
004 - RM65 强化学习抓取 baseline
```

旧实验代码暂时保留在仓库根目录和原有目录中，后续会逐步整理进对应的 `projects/00x-*` 文件夹。