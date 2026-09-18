# RM65 link_6 跟随夹爪 V1

本阶段目标是把“简化功能夹爪”从一个独立抓取 demo，升级成一个会跟随 RM65 末端的工具。

## 为什么要做这一步

之前的 RL 抓取 baseline 中，简化夹爪是直接放在方块附近的。它能验证抓取接触和 RL 环境，但还不能说明“夹爪属于机械臂末端”。

V1 要解决的问题是：

```text
RM65 link_6 动到哪里
简化夹爪就跟到哪里
```

这一步不是为了追求夹爪外观，而是为了建立 arm + gripper 组合任务的空间关系。

## 新增文件

```text
isaac_sim/rm65_link6_follow_gripper_v1.py
```

## 脚本做了什么

```text
1. 启动 Isaac Sim
2. 加载 RM65-B USD
3. 自动查找 RM65 的 link_6 prim
4. 创建桌面和目标方块
5. 创建一个简化功能夹爪：
   - palm
   - left_finger
   - right_finger
6. 每一帧读取 link_6 的世界坐标
7. 根据 link_6 位姿重新计算 palm / fingers 的世界坐标
8. 执行 open → close 的夹爪动作测试
```

## 当前验证结果

远程 Linux headless 测试命令：

```bash
cd ~/robot-learning/rm-ik-rl
ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=60 \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_link6_follow_gripper_v1.py
```

关键输出：

```text
FOUND_LINK6 path=/RM65/root_joint/link_6
RM65 link_6 follow gripper V1 started.
Goal: keep a simplified gripper spatially attached to RM65 link_6.
step=0000 link6_pos=[-0.000,-0.000,+0.851] opening=0.0550
FINAL link6_follow_gripper_v1_done=True
```

说明：

```text
脚本可以找到 RM65 的 link_6
简化夹爪可以根据 link_6 的位姿更新
基础运行链路没有报错
```

## 当前限制

V1 仍然是一个工程中间版本：

```text
夹爪还不是真正的 USD articulation 子关节
夹爪是 kinematic cuboid，不是真实 CAD/URDF 夹爪
当前测试只验证跟随和开合逻辑
还没有接入 MoveIt2 pre-grasp 后的闭环抓取
```

这些限制是有意保留的，因为当前目标是先建立“末端工具跟随 link_6”的基础能力。

## 下一步

下一步可以升级成 V2：

```text
1. 让 MoveIt2 控制 RM65 移动到 pre-grasp 点
2. Isaac Sim bridge 驱动 RM65 真实运动
3. link_6 follow gripper 跟随末端
4. RL policy 控制 gripper opening
5. 判断 cube 是否被抬起
```

也就是：

```text
MoveIt2 arm approach
+ link_6-attached functional gripper
+ RL local grasp policy
```

这才是更接近完整 manipulation pipeline 的版本。
