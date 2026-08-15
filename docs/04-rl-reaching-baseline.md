# RM65 强化学习 reaching 原型

这个文件记录第一版“用强化学习方式做 IK / reaching”的设计。它不是最终 Isaac Lab 版本，而是为了让初学者先看懂强化学习在机械臂 reaching 里的最小闭环。

## 传统 IK 与 RL reaching 的区别

传统 IK 的输入是末端目标位姿，输出是一组关节角。它通常使用几何推导、雅可比迭代或数值优化，目标是直接求解：

```text
target pose -> IK solver -> joint angles
```

RL reaching 不直接调用 IK solver。它把机械臂看成一个环境，让策略根据当前状态一步步输出动作，通过 reward 学会靠近目标：

```text
current joints + target -> policy -> joint delta -> new pose -> reward
```

所以第一版 RL 的核心不是“比 IK 更好”，而是建立可训练、可评估、可对比的基线。

## 当前脚本

`rm65_rl_reach_es.py` 使用 Isaac Sim 的 Lula 正运动学作为环境模型：

- 目标：让 RM65-B 末端靠近随机采样的可达目标点；
- 状态：当前 6 个关节角、末端到目标的三维误差、距离；
- 动作：6 个关节的增量；
- 奖励：距离越小越好，动作越平滑越好，到达阈值内给成功奖励；
- 训练算法：Evolution Strategies，一种基于 rollout reward 的无梯度策略搜索方法。

选择 Evolution Strategies 是因为它依赖少、代码短、适合先理解 RL 闭环。后续正式版再迁移到 Isaac Lab + PPO/SAC。

## 运行命令

在实验室 Linux 的项目目录运行：

```bash
cd ~/robot-learning/rm-ik-rl
~/isaac-sim-5.1.0/python.sh rm65_rl_reach_es.py --iterations 40
```

如果只想快速冒烟测试：

```bash
~/isaac-sim-5.1.0/python.sh rm65_rl_reach_es.py --iterations 5 --population 4 --eval-episodes 10
```

脚本会输出：

- 每隔几轮的 success rate；
- 平均末端误差；
- 中位数末端误差；
- 训练耗时。

结果文件默认保存在 `outputs/`，这个目录不会上传 GitHub。

## 为什么结果不一定立刻很好

这个版本的策略很小，只是一个线性策略，并且只控制位置，不控制完整姿态。它的意义是把 RL reaching 的五件事跑通：

1. 状态是什么；
2. 动作是什么；
3. reward 怎么设计；
4. rollout 怎么评估；
5. 如何和传统 IK 比较成功率和误差。

后续升级方向：

- 用 Isaac Lab 创建真正的并行仿真环境；
- 用 PPO 训练神经网络策略；
- 加入姿态误差、关节限位和碰撞惩罚；
- 与传统 IK 在同一批目标上比较成功率、误差和耗时。
