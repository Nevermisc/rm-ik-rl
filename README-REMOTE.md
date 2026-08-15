# RM65-B 传统 IK / 强化学习项目

这是机械臂 manipulation 与抓取规划学习项目。当前已经完成 RM65-B 模型导入和传统完整位姿 IK，下一阶段是可视化演示与 Isaac Lab 强化学习 reaching。

## 已完成

1. Isaac Sim 兼容性检查通过。
2. Franka 官方 IK 示例运行通过。
3. RM65-B URDF 转换为项目本地 USD。
4. Isaac Sim 识别到 `joint_1`～`joint_6` 共 6 个自由度及正确关节限制。
5. Lula 使用 `link_6` 作为末端，完成 RM65-B 完整位置 + 姿态 IK。
6. IK 结果已发送给 articulation controller，机械臂在物理仿真中到达目标。
7. 正式版图形窗口显示 RM65-B 追踪移动目标，可视化连续至少 `1080/1080` 帧 IK 成功。

本次自动验收结果：

- 数值位置误差：约 `0.00000043 m`；
- 数值姿态误差：约 `0.000704 rad`；
- 仿真执行后位置误差：约 `0.000431 m`；
- 仿真执行后姿态误差：约 `0.00502 rad`；
- 最终结果：`PASS: RM65-B traditional full-pose IK solved and moved the robot.`

## 文件说明

- `import_rm65.py`：将 RM65-B URDF 导入为 USD。
- `verify_rm65_asset.py`：验证模型是否为有效的 6 关节 articulation。
- `rm65_robot_description.yaml`：Lula 的 6 关节运动学描述。
- `rm65_ik_headless.py`：无需图形界面的 RM65-B 传统 IK 自动验收。
- `rm65_ik_visual.py`：可视化演示，目标方块沿三维曲线移动，RM65-B 通过 IK 追踪。
- `franka_ik_headless.py`、`franka_ik_visual.py`：前期 Franka 基线。

## Linux 运行命令

在项目目录执行：

```bash
cd ~/robot-learning/rm-ik-rl
```

重新导入模型：

```bash
~/isaac-sim-5.1.0/python.sh import_rm65.py
```

验证六关节模型：

```bash
~/isaac-sim-5.1.0/python.sh verify_rm65_asset.py
```

运行传统 IK 自动验收：

```bash
~/isaac-sim-5.1.0/python.sh rm65_ik_headless.py
```

运行可视化 IK：

```bash
~/isaac-sim-5.1.0/python.sh rm65_ik_visual.py
```

## 下一步

1. 录制 RM65-B 可视化 IK 演示视频。
2. 建立 GitHub 仓库并上传代码（不上传 Isaac Sim、压缩包和大型生成资产）。
3. 创建 Isaac Lab RM65 reaching 环境。
4. 训练强化学习策略，与传统 IK 对比成功率、误差和速度。
