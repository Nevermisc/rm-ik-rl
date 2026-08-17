# RM65 MoveIt2 Examples

这个包用于学习如何使用 MoveIt2 控制 RM65 机械臂。

当前示例：

- `plan_pose.cpp`：给 RM65 的末端 `Link6` 一个目标位姿，让 MoveIt2 规划轨迹，并通过 fake controller 在 RViz 中执行。

## 1. 编译

在工作空间根目录运行：

```bash
cd ~/robot-learning/rm_moveit2_ws
colcon build --packages-select rm_moveit2_examples --symlink-install
source install/setup.bash
