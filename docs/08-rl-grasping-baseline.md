# RM65-B 强化学习抓取 Baseline

本阶段目标是为后续“RM65-B 机械臂抓取”建立一个最小可训练的 RL 抓取闭环。

当前版本不是最终的“6 轴机械臂 + 夹爪联合强化学习”，而是一个更稳的 baseline：

```text
RM65-B 场景
+ 简化功能夹爪
+ 方块接触物理
+ observation / action / reward / success
+ PPO 训练与评估
```

这样做的原因是：强化学习抓取最难的不是先把算法名字堆上去，而是先让环境稳定、奖励可解释、成功判定可靠。

## 当前完成内容

### 1. 简化物理夹爪抓方块

文件：

```text
isaac_sim/simple_gripper_grasp_physics_test.py
```

功能：

```text
创建桌面
创建动态方块
创建两个高摩擦可控手指
手指闭合
手指上抬
判断方块是否被抬起
```

验证结果：

```text
FINAL max_cube_z=0.1530 success=True
```

说明简化夹爪具备最基础的接触抓取能力。

### 2. RL 抓取任务骨架

文件：

```text
isaac_sim/rm65_grasp_task_skeleton.py
```

核心类：

```text
SimpleGraspTask
```

它提供了 RL 环境最基本的接口：

```text
reset()
step(action)
get_observation()
compute_reward()
success
```

当前 observation 包含：

```text
cube_pos
left_finger_pos
right_finger_pos
opening
finger_z
cube_z
success
```

当前 action 是二维连续动作：

```text
action[0]：夹爪开合变化
action[1]：夹爪上下移动变化
```

当前 reward 包含：

```text
cube lift reward
close reward
coordinated lift reward
success bonus
```

### 3. 随机策略测试

文件：

```text
isaac_sim/rm65_grasp_random_policy_test.py
```

作用：

```text
不用 PPO
只用随机动作调用 env.step(action)
验证 reset / step / reward / done 是否稳定
```

测试结果：

```text
RANDOM_POLICY_FINAL success_count=0/2 average_return=0.4895
```

随机策略没有成功是正常的，这一步的目的不是抓成功，而是确认环境接口稳定。

### 4. PPO 训练

文件：

```text
isaac_sim/rm65_grasp_ppo_train.py
```

实现内容：

```text
ActorCritic 网络
连续动作分布
GAE advantage
PPO clipped objective
value loss
entropy bonus
模型保存
```

同时加入了 behavior cloning warm start：

```text
先模仿 scripted successful grasp
再进行轻量 PPO 更新
```

这样做是为了避免从纯随机策略开始时探索效率太低。

### 5. 策略评估

文件：

```text
isaac_sim/rm65_grasp_policy_eval.py
```

功能：

```text
加载保存的策略模型
使用 deterministic action 评估抓取成功率
```

当前评估结果：

```text
EVAL_FINAL success_count=3/3
```

说明保存后的策略能够稳定完成当前简化抓取任务。

## 运行命令

### 物理抓取测试

```bash
cd ~/robot-learning/rm-ik-rl
~/isaac-sim-5.1.0/python.sh isaac_sim/simple_gripper_grasp_physics_test.py
```

### RL scripted demo

```bash
cd ~/robot-learning/rm-ik-rl
ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=360 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_grasp_task_skeleton.py
```

### 随机策略测试

```bash
cd ~/robot-learning/rm-ik-rl
ISAAC_HEADLESS=1 ISAAC_NUM_EPISODES=2 ISAAC_EPISODE_STEPS=240 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_grasp_random_policy_test.py
```

### BC + PPO 训练

```bash
cd ~/robot-learning/rm-ik-rl

ISAAC_HEADLESS=1 \
ISAAC_PPO_BC_EPOCHS=300 \
ISAAC_PPO_BC_STEPS=360 \
ISAAC_PPO_UPDATES=1 \
ISAAC_PPO_ROLLOUT_STEPS=128 \
ISAAC_PPO_EPISODE_STEPS=240 \
ISAAC_PPO_TRAIN_EPOCHS=2 \
ISAAC_PPO_POLICY_LR=1e-4 \
ISAAC_PPO_VALUE_LR=5e-4 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_grasp_ppo_train.py
```

### 策略评估

```bash
cd ~/robot-learning/rm-ik-rl

ISAAC_HEADLESS=1 \
ISAAC_EVAL_EPISODES=3 \
ISAAC_EVAL_STEPS=240 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_grasp_policy_eval.py
```

## 当前限制

当前 baseline 还不是完整的 arm + gripper 联合 RL：

```text
机械臂 6 关节没有进入 RL action
夹爪是简化功能模型，不是真实 CAD/URDF 夹爪
抓取对象是单一方块
物体位置还没有随机化
没有相机/点云输入
```

这些限制是有意保留的。当前阶段的目标是先打通训练闭环，而不是一口气做完整工业系统。

## 下一步

下一阶段是组合流程：

```text
MoveIt2 控制 RM65 到 pre-grasp 位姿
RL policy 控制功能夹爪完成抓取
```

这条路线比直接做“6 关节 + 夹爪联合 RL”更稳，也更容易在求职项目里讲清楚：

```text
传统规划负责靠近目标
学习策略负责接触抓取
```
