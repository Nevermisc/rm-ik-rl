# RM 机械臂：传统 IK 与强化学习末端到达

这是一个面向机器人 manipulation / 抓取规划求职作品集的入门项目。项目不是为了“堆工具”，而是回答一个清楚的问题：

> 给定机械臂末端目标位姿，传统逆运动学与强化学习策略分别能否到达？它们在成功率、误差、耗时和泛化性上有什么差异？

## 最终交付物

1. Isaac Sim 中的 RM65（或实验室实际 RM 型号）机械臂资产。
2. 传统 IK 基线：输入末端目标位置/姿态，输出关节角并驱动机械臂。
3. Isaac Lab 强化学习 reaching 任务：输入机器人状态与目标，输出关节动作。
4. 固定测试集上的对比表：成功率、末端误差、单次计算时间、碰撞率。
5. 1～2 分钟演示视频、可复现实验命令和项目说明。

## 当前阶段

- [x] 远程 Linux 环境体检
- [x] 跑通 Isaac Sim 官方自带 Franka IK 示例
- [x] 导入 RM65-B URDF 并保存 USD
- [x] 跑通 RM65-B 传统完整位姿 IK（无界面自动验收）
- [x] 在 Isaac Sim 5.1.0 正式版运行 RM65-B 可视化 IK
- [ ] 建立 GitHub 远程仓库并完成首次推送
- [ ] 创建 Isaac Lab reaching 环境
- [ ] 训练和评估强化学习策略
- [ ] 整理简历材料和演示视频

## 传统 IK 当前结果

2026-08-15 在实验室 Ubuntu 22.04 / RTX 4060 Ti 上完成了 RM65-B 闭环测试：

- Isaac Sim 正确识别 `joint_1`～`joint_6` 共 6 个自由度；
- Lula 使用 `link_6` 作为末端坐标系；
- 数值 IK 位置误差约 `0.00000043 m`，姿态误差约 `0.000704 rad`；
- 施加关节指令并运行物理仿真后，位置误差约 `0.000431 m`，姿态误差约 `0.00502 rad`；
- 自动测试结果：`PASS: RM65-B traditional full-pose IK solved and moved the robot.`
- 可视化连续运行至少 1080 帧，IK 成功 `1080/1080`。

核心文件：

- `import_rm65.py`：把项目内 RM65-B URDF 转成 USD；
- `verify_rm65_asset.py`：验证 USD 是否为有效的 6 关节 articulation；
- `rm65_robot_description.yaml`：Lula 运动学描述；
- `rm65_ik_headless.py`：传统完整位姿 IK 自动验收；
- `rm65_ik_visual.py`：目标方块沿曲线移动的可视化 IK 演示。

## 文档入口

- [今天的 IK 执行清单](docs/00-today-ik.md)
- [GitHub 零基础指南](docs/01-github-guide.md)
- [一个月项目与求职路线](docs/02-one-month-roadmap.md)
- [机器人算法知识地图与 LeetCode 建议](docs/03-algorithm-learning.md)

## 建议的仓库边界

这个仓库只放“RM 机械臂 IK 与 RL reaching”相关内容。以后不要把所有学习代码塞进同一个仓库。

- `rm-ik-rl`：本项目的仿真、训练、评估和文档。
- `robotics-notes`：ROS 2、运动学、论文阅读等可公开的学习笔记。
- `leetcode`：只有确实刷题时再建；不要让它抢占项目时间。

第三方大型模型、数据集、训练权重、Isaac Sim 安装文件和密钥不上传。第三方代码优先通过依赖说明或 Git submodule 引用，并保留原许可证。
