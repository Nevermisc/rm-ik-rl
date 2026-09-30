# 13 Policy 控制 link_6 跟随夹爪 V3

本阶段把前面训练出的局部抓取 policy 接到了 `link_6-follow gripper` 上。

## 本阶段目标

把 V2 中的“按时间表闭合夹爪”替换成：

```text
读取当前 cube / finger observation
        ↓
送入 PPO/BC policy
        ↓
输出 2 维 action
        ↓
控制 link_6-follow gripper 的开合和局部上抬
```

也就是从：

```text
机械臂 bridge + 跟随夹爪 + 定时闭合
```

推进到：

```text
机械臂 bridge + 跟随夹爪 + policy 控制局部抓取动作
```

## 新增文件

```text
isaac_sim/rm65_isaac_bridge_with_policy_gripper_v3.py
```

## V3 做了什么

### 1. 保留 MoveIt2 / Isaac Sim bridge

V3 仍然创建 Isaac ROS2 bridge：

```text
/isaac_joint_states
/isaac_joint_commands
```

这意味着 MoveIt2 和 ros2_control 仍然可以控制 RM65 机械臂运动。

### 2. 保留 link_6-follow gripper

V3 仍然会找到：

```text
/RM65/root_joint/link_6
```

然后让简化夹爪每一帧跟随这个 link 的世界位姿。

### 3. 新增 policy 控制模式

V3 支持三种夹爪控制模式：

```text
policy   ：加载 .pt 模型，用 policy 输出 action
scripted ：不用模型，用手写动作做结构验证
hold     ：保持夹爪不动，只验证 bridge 场景
```

通过环境变量设置：

```bash
ISAAC_GRIPPER_CONTROL_MODE=policy
```

### 4. 保持原来的 8 维 observation

V3 使用的 observation 和之前 `rm65_grasp_ppo_train.py` 中的格式保持一致：

```text
cube_z
cube_z - cube_initial_z
opening
finger_z
cube_relative_to_finger_x
cube_relative_to_finger_y
cube_relative_to_finger_z
episode_progress
```

这样做的原因是：之前的 `.pt` policy 就是按这个输入维度训练出来的。

### 5. 保持原来的 2 维 action

policy 输出：

```text
action[0]：夹爪开合
action[1]：夹爪局部上抬 / 下压
```

V3 中的解释是：

```text
action[0] < 0：闭合
action[0] > 0：张开
action[1] > 0：沿夹爪局部 z 方向上抬
action[1] < 0：沿夹爪局部 z 方向下压
```

## 验证命令

短 smoke test：

```bash
cd ~/robot-learning/rm-ik-rl
source /opt/ros/humble/setup.bash
ISAAC_HEADLESS=1 \
ISAAC_MAX_STEPS=160 \
ISAAC_POLICY_START_STEP=20 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_policy_gripper_v3.py
```

当前验证输出：

```text
RM65 Isaac ROS2 bridge with policy gripper V3 started.
Publishing: /isaac_joint_states
Subscribing: /isaac_joint_commands
FOUND_LINK6 path=/RM65/root_joint/link_6
control_mode=policy
policy_start_step=20
policy_model=/home/iot22/robot-learning/rm-ik-rl/rm65_grasp_ppo_policy.pt
step=00000 policy_step=0000 link6=[-0.000,-0.000,+0.851] action=[+0.000,+0.000] opening=0.0750 local_z=0.0000 cube_z=0.0225 max_cube_z=0.0245 success=False
step=00120 policy_step=0101 link6=[-0.002,-0.000,+0.850] action=[+0.829,+1.000] opening=0.0850 local_z=0.1600 cube_z=0.0225 max_cube_z=0.0245 success=False
FINAL bridge_with_policy_gripper_v3 steps=160 policy_steps=140 max_cube_z=0.0245 success=False
```

这个结果说明：

```text
V3 可以启动
policy 可以加载
observation 可以生成
action 可以输出
action 可以作用到 link_6-follow gripper
```

但它没有抓起方块。

## 为什么 smoke test 没抓起来

这是预期结果，不是 bug。

原因是 smoke test 没有先用 MoveIt2 把 RM65 移动到 cube 附近。

默认状态下：

```text
link_6 z ≈ 0.85 m
cube_z ≈ 0.0225 m
```

也就是说夹爪离方块非常远。policy 看到的是训练分布之外的 observation，所以输出动作没有抓取意义。

这说明下一步必须做：

```text
MoveIt2 先移动到 pre-grasp
        ↓
link_6-follow gripper 到达 cube 附近
        ↓
再启动 policy 控制局部闭合和上抬
```

## 当前限制

V3 已经完成 policy 接入，但还没有完成完整抓取闭环：

```text
没有自动触发 MoveIt2 pre-grasp
policy_start_step 还是手动指定
policy 是从独立夹爪环境迁移过来的，几何分布还没有完全对齐
夹爪仍然是 kinematic functional gripper
没有物体位置随机化
没有相机/点云输入
```

## 下一步

下一步应该做 V4：

```text
写一个 pre-grasp + policy-gripper 的连续运行流程
```

目标是：

```text
1. 启动 Isaac V3 bridge
2. 启动 ros2_control
3. 启动 MoveIt2 move_group
4. 发送 pre-grasp 目标点
5. 等待机械臂到位
6. 启动 policy gripper
7. 输出抓取结果
```

V4 才是真正能作为“完整抓取 demo”的版本。
