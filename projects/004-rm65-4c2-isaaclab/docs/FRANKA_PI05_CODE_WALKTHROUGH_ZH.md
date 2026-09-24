# Franka + π0.5 + IsaacLab 零基础代码导读

更新时间：2026-09-24  
适用对象：会一点 Python 语法，但第一次接触机器人、仿真、模型服务和闭环控制的人  
对应正式代码：`projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py`  
当前边界：只解释和运行仿真，不控制真实机械臂

## 1. 学完后你应该能够做什么

读完并完成练习后，你应该能独立回答：

1. DROID 数据集、π0.5 checkpoint、sim-evals、IsaacLab、Isaac Sim 分别是什么；
2. 哪些代码是我们写的，哪些是官方或第三方提供的；
3. 为什么模型服务和仿真要分成两个进程；
4. 一张相机图像和一组关节角怎样变成 Franka 的下一步动作；
5. `15×8`、`(1,8)`、`224×224×3` 分别代表什么；
6. `env.step(action)` 最终怎样让仿真机械臂运动；
7. 为什么执行 8 个动作后要重新问模型；
8. 怎样证明任务成功，而不是只看到机械臂动了；
9. 把这套代码迁移到另一台机械臂时，哪些能复用、哪些必须重写；
10. 怎样从日志和证据判断错误在模型、通信、环境、控制还是评测层。

## 2. 先定义最基础的词

### 2.1 程序、进程和容器

**程序**是硬盘上的代码文件，例如：

```text
run_pi05_franka_robustness_suite.py
```

**进程**是程序正在运行时，在内存中的一个实例。这个项目至少有两个主要进程：

```text
进程 A：Docker 容器里的 π0.5 模型服务
进程 B：Linux 主机上的 Isaac Sim / IsaacLab 仿真 runner
```

**Docker 容器**可以理解为隔离的软件运行箱。箱子里有 OpenPI、JAX、CUDA 依赖和模型服务；箱子外运行 Isaac Sim。分开以后，两套复杂依赖不必安装到同一个 Python 环境。

### 2.2 客户端、服务端和端口

**服务端**长期等待别人发请求。本项目的 π0.5 服务监听：

```text
0.0.0.0:8000
```

`8000` 是端口，可以把它想成这台电脑上的一个窗口编号。

**客户端**主动连接服务端并提问。本项目的 runner 使用：

```python
WebsocketClientPolicy("localhost", 8000)
```

`localhost` 表示“当前这台电脑”。虽然模型在 Docker 中，但 Compose 使用 host network，因此主机进程可以通过 `localhost:8000` 找到它。

### 2.3 字典和键

Python 字典用名字保存数据：

```python
person = {
    "name": "Alice",
    "age": 18,
}
```

`name` 和 `age` 是键。机器人观测也是字典：

```python
obs["policy"]["arm_joint_pos"]
obs["policy"]["external_cam"]
```

不同系统使用不同键，所以需要“字段翻译”。数据值相同但键名错误，接收方也找不到它。

### 2.4 数组、张量、shape 和 dtype

相机图像、关节角和动作都是多维数字容器。

- NumPy 中叫 `ndarray`；
- PyTorch/JAX 中常叫 `Tensor` 或 array；
- `shape` 表示各个维度的长度；
- `dtype` 表示每个数字的类型。

例子：

```text
(180, 320, 3)
```

表示图像高 180、宽 320、每像素 RGB 三个通道。

```text
(7,)
```

表示一维数组中有 7 个关节角。

```text
(15, 8)
```

表示模型给出未来 15 步，每步 8 个动作值。

`float32` 表示 32 位浮点数；`uint8` 表示 0～255 的无符号整数，通常用来存 RGB 图像。

### 2.5 batch 维是什么

机器学习和仿真框架通常一次处理多个样本或多个环境，所以会在最前面增加 batch 维。

单个动作：

```text
(8,)
```

一次只运行一个环境，但 IsaacLab 仍要求：

```text
(1, 8)
```

最前面的 `1` 表示只有一个环境。代码用：

```python
action.unsqueeze(0)
```

把 `(8,)` 变成 `(1,8)`。

### 2.6 观测、动作和策略

**观测 observation**：机器人当前能知道的信息，例如图像、关节角、夹爪状态。

**动作 action**：希望机器人下一步执行的命令，例如七个目标关节角和一个夹爪命令。

**策略 policy**：根据观测决定动作的函数：

```text
动作 = 策略(观测, 文字指令)
```

π0.5 就是这里的学习策略。

### 2.7 checkpoint、训练和推理

**训练**：把大量示范数据交给模型，反复调整模型参数。

**checkpoint**：训练完成后保存的模型参数，可以理解为模型已经学到的“记忆”。

**推理 inference**：加载 checkpoint 后，输入当前观测，计算动作；推理不会自动修改模型参数。

Franka 阶段没有重新训练 π0.5，只加载已经训练好的 DROID joint-position checkpoint 做推理。

### 2.8 episode、step 和闭环

**step**：仿真向前运行一次控制动作。

**episode**：从环境 reset 开始，到成功、失败或超时结束的一整个回合。

**闭环 closed loop**：执行动作以后重新读取真实的新观测，再决定后续动作：

```text
观察 → 预测 → 执行 → 再观察 → 再预测
```

与闭环相对的是开环：提前生成整条动作序列，不管后面发生什么都照着执行。

## 3. 数据集到底是什么

### 3.1 DROID 数据集

DROID 是真实机器人操作数据集。可以把其中一个 episode 想成：

```text
任务文字：把杯子拿起来

时间 t0：外部图像、腕部图像、Franka 关节状态、夹爪状态、操作者动作
时间 t1：外部图像、腕部图像、Franka 关节状态、夹爪状态、操作者动作
时间 t2：……
```

大量真实 Franka 操作轨迹让模型学习“看到什么、听到什么指令时，关节下一步应该往哪里走”。

本项目使用的配置显示训练数据混合大致为：

```text
DROID dataset                  权重 0.9
PolaRiS DROID co-train dataset 权重 0.1
动作空间                       JOINT_POSITION
```

这里的 `JOINT_POSITION` 表示标签是目标关节位置，不是末端位姿，也不是关节速度。

### 3.2 我们有没有下载整个 DROID 数据集

没有。Franka 评测只需要已经训练好的 checkpoint 和归一化统计，不需要把完整训练数据下载到本地。

本地真正加载的是：

```text
~/.cache/openpi/openpi-assets/checkpoints/pi05_droid_jointpos
```

其中包含模型参数和 DROID 的 norm stats。checkpoint 是数据训练后的结果，不等于原始数据集。

### 3.3 sim-evals assets 是不是数据集

不是。下面这些是仿真资产：

```text
Franka USD
桌子 USD
三个场景 USD
HDR 背景
```

它们描述“考场长什么样”，不包含模型学习用的大量专家动作标签。

### 3.4 运行时生成的视频是不是训练数据

本阶段生成的 MP4、PNG、NPZ 和 JSON 是评测证据。理论上可以整理成新数据集，但本项目没有用它们重新训练 Franka checkpoint。

必须分清：

```text
DROID 数据集        用来训练原始 checkpoint
checkpoint          训练后保存的模型参数
sim-evals assets    仿真场景和机器人模型
本次 rollout        模型在仿真中的考试过程
评测 JSON           对考试结果的机器可读总结
```

后面迁移 RM65 时，我们才用脚本专家采集自己的 RM65 数据集，并从 `pi05_base` 微调。

## 4. 整套系统由谁负责什么

| 组件 | 类比 | 实际职责 |
|---|---|---|
| Isaac Sim | 物理世界和显卡渲染器 | 计算重力、碰撞、关节运动并生成相机图像 |
| IsaacLab | 机器人实验框架 | 定义观测、动作、环境、reset、step 和回合 |
| sim-evals | 搭好的考试场 | 提供 Franka、Robotiq、DROID 相机和三个任务场景 |
| OpenPI | 模型代码和服务框架 | 加载 π0.5、处理输入、执行推理、返回动作 |
| π0.5 checkpoint | 已学到的控制能力 | 根据图像、状态和语言生成未来动作块 |
| WebSocket | 电话线 | 在仿真进程和模型进程之间传观测与动作 |
| 我们的 runner | 考官兼转接员 | 翻译数据、控制循环、制造扰动、判定成功、保存证据 |

完整结构：

```text
终端 A / Docker
┌────────────────────────────────────────────┐
│ OpenPI                                     │
│   checkpoint → π0.5 policy                 │
│   WebSocket server 0.0.0.0:8000            │
└──────────────────────▲─────────────────────┘
                       │ request / response
                       │
终端 B / Linux 主机    │
┌──────────────────────┴─────────────────────┐
│ 我们的 runner                              │
│  读取 obs → 改字段 → 请求模型 → 得到动作   │
│       ▲                              │     │
│       │ 新观测                       ▼     │
│  sim-evals DROID env ← env.step(action)    │
│       │                                    │
│  IsaacLab managers                         │
│       │                                    │
│  Isaac Sim / PhysX / cameras               │
└────────────────────────────────────────────┘
```

## 5. 哪些代码是我们自己写的

### 5.1 主要自编代码

是的，Franka 上部署 π0.5 时，我们自己写的核心主要是“胶水层、实验层和证据层”，不是从零实现神经网络或物理引擎。

```text
projects/003-pi05-franka-isaaclab/scripts/
├── start_and_warmup_pi05.sh
├── warmup_pi05_droid.py
├── stop_pi05_server.sh
├── probe_droid_scenes.py
├── validate_droid_sim_scene.py
├── run_pi05_droid_scene1.py
├── run_pi05_franka_robustness_suite.py
├── run_all_suites.sh
├── summarize_pi05_franka_suite.py
└── summarize_pi05_franka_audit.py
```

其中最核心的是：

```text
start_and_warmup_pi05.sh              启动模型
warmup_pi05_droid.py                  验证模型接口
run_pi05_franka_robustness_suite.py   完整闭环和评测
run_all_suites.sh                     编排全部实验
```

### 5.2 没有自己写的部分

- π0.5 网络结构和预训练权重来自 OpenPI；
- WebSocket client/server 基础实现来自 OpenPI；
- Franka DROID 环境来自 sim-evals；
- 环境管理、相机、动作 manager 来自 IsaacLab；
- 物理、碰撞和渲染来自 Isaac Sim。

项目贡献不是“发明了 π0.5”，而是把这些组件正确接起来、修复接口和运行问题、定义严格测试并生成证据。

### 5.3 为什么胶水代码很重要

神经网络只会接受特定格式的数据。环境只会输出自己的格式。两边不对齐时，模型再强也不能工作。

胶水层负责：

```text
字段名对齐
shape 对齐
图像尺寸对齐
动作语义对齐
控制频率对齐
夹爪语义对齐
成功标准和证据
```

迁移机器人时，工作量主要就在这里。

## 6. 系统是怎样启动起来的

### 6.1 第一步：Shell 启动 Docker 服务

运行：

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
bash scripts/start_and_warmup_pi05.sh
```

脚本设置：

```text
policy.config = pi05_droid_jointpos_polaris
policy.dir    = gs://openpi-assets/checkpoints/pi05_droid_jointpos
```

然后调用 Docker Compose 启动 `openpi_server`。

### 6.2 第二步：OpenPI 创建 policy

容器中最终运行 `scripts/serve_policy.py`。它依次做：

```text
解析命令行
→ 根据 config 名称找到 TrainConfig
→ 根据 checkpoint 路径恢复参数和 norm stats
→ 创建 Policy 对象
→ 创建 WebsocketPolicyServer
→ 在 8000 端口等待请求
```

配置中的：

```python
Pi0Config(action_horizon=15, pi05=True)
```

表示使用 π0.5，并一次生成未来 15 步动作。

### 6.3 第三步：为什么要 warm-up

模型第一次推理会触发 JAX/XLA 编译。预热脚本发送一份字段正确的假 DROID 观测，等待 `(15,8)` 动作返回。

这一步把“模型加载和编译”与“复杂仿真任务”分开。预热失败时，不需要启动 Isaac Sim 排错。

### 6.4 第四步：启动仿真 runner

运行：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py \
  --scene 1 --suite baseline --device cuda:0 --headless
```

`PYTHONPATH` 告诉 Python 去哪里找 `sim_evals` 包。

`isaaclab.sh -p` 使用 Isaac Sim 自带的 Python 启动脚本。普通系统 Python 没有 Omniverse/Isaac 模块，不能直接运行。

## 7. sim-evals 如何搭建 DROID 环境

### 7.1 import 为什么能创建名为 DROID 的环境

runner 中有：

```python
import sim_evals.environments
```

这个 import 不只是“拿函数”。它执行 `environments/__init__.py` 中的注册：

```python
gym.register(
    id="DROID",
    entry_point=ManagerBasedRLEnv,
    kwargs={"env_cfg_entry_point": DroidEnvCfg},
)
```

注册后，下面这句才知道 `DROID` 是什么：

```python
gym.make("DROID", cfg=cfg)
```

可以把注册理解为在 Gym 的电话簿里写入：

```text
名字 DROID → 用 ManagerBasedRLEnv + DroidEnvCfg 创建
```

### 7.2 机器人从哪里来

`nvidia_droid.py` 定义 `NVIDIA_DROID`，从这个文件加载机器人：

```text
assets/franka_robotiq_2f_85_flattened.usd
```

它还定义：

- 初始七个 Franka 关节角；
- 初始夹爪状态；
- 关节 effort/velocity limit；
- stiffness 和 damping；
- 是否启用自碰撞；
- PhysX solver 迭代次数。

这些不是模型输出，而是仿真机器人本身的物理与执行器配置。

### 7.3 场景物体从哪里来

`droid_environment.py` 的 `dynamic_scene()` 根据 scene id 加载：

```text
assets/scene1.usd
assets/scene2.usd
assets/scene3.usd
```

它遍历 `/World` 下的 prim，把带 `RigidBodyAPI` 的物体注册为 `RigidObjectCfg`。因此 runner 可以按名字访问：

```python
source = env.unwrapped.scene["rubiks_cube"]
target = env.unwrapped.scene["_24_bowl"]
```

### 7.4 三个相机怎么定义

环境定义三个 CameraCfg：

```text
external_cam    一侧外部视角
external_cam_2  另一侧外部视角
wrist_cam       安装在夹爪腕部
```

π0.5 DROID runner 实际送给模型的是：

```text
external_cam
wrist_cam
```

`external_cam_2` 仍在场景中，但这份 checkpoint 输入协议没有使用它。

### 7.5 ObservationCfg 定义模型能读到什么

`ObservationCfg.PolicyCfg` 定义：

```text
arm_joint_pos   七个 panda_joint 的实际位置
gripper_pos     finger_joint 归一化到 0～1
external_cam    RGB
external_cam_2  RGB
wrist_cam       RGB
```

`concatenate_terms=False` 很重要：它让观测保留为带名字的字典，而不是把所有数字强行拼成一个大向量。

### 7.6 ActionCfg 定义八个动作如何控制机器人

动作前七维由：

```python
JointPositionActionCfg(
    joint_names=["panda_joint.*"],
    preserve_order=True,
)
```

解释为七个目标关节位置。

第八维由二值夹爪 action 解释：

```text
<= 0.5 → 张开命令 0
> 0.5  → 闭合命令 π/4
```

因此 `env.step([q1,...,q7,g])` 的含义不是“直接给电机电压”，而是给 IsaacLab action manager 目标位置；action manager 和 actuator 再把目标转成仿真关节控制。

### 7.7 仿真频率怎样得到 15 Hz

环境配置：

```python
decimation = 8
sim.dt = 1 / (15 * 8)
```

物理频率：

```text
15 × 8 = 120 Hz
```

每个 policy step 内部运行 8 个物理小步：

```text
120 Hz / 8 = 15 Hz 控制频率
```

episode 长度为 30 秒，所以最多大约：

```text
30 × 15 = 450 个控制 step
```

## 8. 正式 runner 从头到尾阅读

正式代码：

[`run_pi05_franka_robustness_suite.py`](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py)

### 8.1 参数为什么必须在 AppLauncher 前解析

脚本先定义：

```text
--scene             1、2、3
--suite             baseline、robustness、audit、full
--output-root       输出根目录
--open-loop-horizon 动作块执行多少步后重新规划
```

然后：

```python
args.enable_cameras = True
args.headless = True
app_launcher = AppLauncher(args)
```

Isaac Sim Kit 必须先启动，之后才能 import 很多依赖 Omniverse extension 的模块。

`headless=True` 只表示不显示主窗口，不表示相机停止渲染。相机需要 `enable_cameras=True`。

### 8.2 常量是什么

```python
FPS = 15
CAMERA_HEIGHT = 180
CAMERA_WIDTH = 320
STABLE_STEPS = 15
OPEN_GRIPPER_THRESHOLD = 0.25
STABLE_RADIUS_METERS = 0.015
```

含义：

- 策略控制和视频按 15 Hz；
- 环境相机降到 180×320 节省显存；
- 成功后要稳定约 1 秒；
- 实际夹爪值不高于 0.25 才认为张开；
- 最近 15 步物体移动不超过 1.5 cm 才认为稳定。

### 8.3 Task 和 Case 为什么分开

`Task` 描述任务不变的内容：

```text
拿哪个物体
放到哪个目标
标准指令
同义指令
几何成功阈值
```

`Case` 描述一次试验改变什么：

```text
物体偏移
目标偏移
图像亮度
本次 prompt
```

分开以后，可以对同一任务生成多种测试，而不用复制整段控制代码。

### 8.4 TASKS 怎样把 scene id 变成具体任务

```python
TASKS = {
    1: Task(source="rubiks_cube", target="_24_bowl", ...),
    2: Task(source="_10_potted_meat_can", target="_25_mug", ...),
    3: Task(source="_11_banana", target="small_KLT_visual_collision", ...),
}
```

这些名字必须与 USD 中的 prim 名字一致。拼错以后：

```python
env.unwrapped.scene[task.source]
```

会找不到物体。

### 8.5 DroidJointPosClient 的状态

对象保存：

```text
open_loop_horizon  每个动作块执行几步
client             WebSocket 客户端
action_index       当前执行到动作块第几步
action_chunk       最近一次模型返回的整段动作
```

`reset()` 把后两个清空。新 case 如果不 reset，可能先执行上个 case 剩余动作。

### 8.6 infer() 第一步：从 IsaacLab 拿数据

```python
policy = obs["policy"]
external = policy["external_cam"][0].detach().cpu().numpy()
wrist = policy["wrist_cam"][0].detach().cpu().numpy()
```

每个操作的意义：

- `[0]`：取 batch 中第一个环境；
- `detach()`：不需要梯度；
- `cpu()`：图像原本可能在 GPU；
- `numpy()`：OpenPI client 使用 NumPy 序列化。

### 8.7 infer() 第二步：处理图像

```python
external = resize_with_pad(external, 224, 224)
wrist = resize_with_pad(wrist, 224, 224)
```

原图是 `180×320×3`。`resize_with_pad` 保持比例缩放并用黑边补到 `224×224×3`，避免直接拉伸。

亮度 case 使用：

```python
np.clip(image.astype(np.float32) * brightness, 0, 255).astype(np.uint8)
```

先转 float 避免 uint8 乘法溢出，乘亮度后限制到 0～255，再转回 uint8。

### 8.8 infer() 第三步：判断是否重新问模型

```python
replanned = action_index == 0 or action_index >= open_loop_horizon
```

第一次必须问模型。执行 8 步后再次问模型。中间步骤直接从已有 chunk 取动作，不发网络请求。

### 8.9 infer() 第四步：构造 DROID request

```python
request = {
    "observation/exterior_image_1_left": external,
    "observation/wrist_image_left": wrist,
    "observation/joint_position": arm_joint_pos,
    "observation/gripper_position": gripper_pos,
    "prompt": instruction,
}
```

这一步把 sim-evals 字段翻译成 DROID policy contract。

输入 shape：

```text
external image   (224,224,3) uint8
wrist image      (224,224,3) uint8
joint position   (7,)        float
gripper position (1,)        float
prompt           str
```

### 8.10 infer() 第五步：发送 WebSocket 请求

```python
self.action_chunk = np.asarray(
    self.client.infer(request)["actions"]
)
```

`client.infer()` 内部做：

```text
Python dict
→ msgpack 把数组转换成 bytes
→ WebSocket send
→ 等待服务端 response
→ msgpack 还原 NumPy 数组
```

为什么不用 JSON：图像是大量 uint8 数字，JSON 会变得很大。msgpack 保留 dtype、shape 和连续二进制 data，更适合数组。

### 8.11 服务端收到请求后发生什么

OpenPI `WebsocketPolicyServer`：

```python
obs = unpackb(await websocket.recv())
action = self._policy.infer(obs)
await websocket.send(packer.pack(action))
```

`Policy.infer()` 内部顺序：

```text
DroidInputs transform
→ norm stats / prompt tokenization 等 transform
→ 增加 batch 维
→ π0.5 sample_actions
→ 去掉 batch 维
→ 反归一化等 output transform
→ DroidOutputs
```

### 8.12 DroidInputs 实际怎样转换

它先拼状态：

```python
state = concatenate([7个关节角, 1个夹爪值])
```

得到：

```text
state.shape == (8,)
```

π0.5 架构有三个图像槽位。DROID 只有两张有效图，所以输入 transform 组成：

```text
base_0_rgb        外部相机       mask=True
left_wrist_0_rgb  腕部相机       mask=True
right_wrist_0_rgb 全零占位图     mask=False
```

mask=False 告诉模型第三张图不存在，不要把黑图当成真实视觉信息。

### 8.13 π0.5 为什么有随机性

π0.5 的 flow-matching 动作生成从随机噪声开始。相同观测在不同随机噪声下可能得到略有不同的动作。这也是后续确定性评测需要显式 seed/noise 的原因。

模型内部动作维度可以大于实际机器人维度。`DroidOutputs` 最后执行：

```python
data["actions"][..., :8]
```

只把前 8 维返回给 Franka。

### 8.14 infer() 第六步：取一个动作并处理夹爪

```python
action = action_chunk[action_index]
action_index += 1
action[-1] = 1.0 if action[-1] > 0.5 else 0.0
```

前七维保持连续关节目标；最后一维离散成 0/1，因为 sim-evals 使用二值夹爪 action。

### 8.15 main() 怎样创建环境

```python
cfg = parse_env_cfg("DROID", device="cuda:0", num_envs=1, use_fabric=True)
cfg.set_scene(scene)
env = gym.make("DROID", cfg=cfg)
```

随后两次 reset：

```python
obs, _ = env.reset()
obs, _ = env.reset()
```

第一次加载，第二次让材质和相机渲染完整。

### 8.16 为什么获取机器人关节限位

```python
arm_limits = robot.data.soft_joint_pos_limits[...]
```

后面计算所有实际关节距离上、下限还有多少余量。任务成功但关节长期贴着限位仍然有风险，所以限位是工程审计的一部分。

### 8.17 每个 case 开始前做什么

```text
reset 两次
→ neutral action 5 步
→ 移动物体或目标
→ neutral action 8 步让物理稳定
→ 清空旧 action chunk
→ 记录初始位置
```

neutral action 等于当前实际关节状态，所以它的目的不是运动，而是保持。

### 8.18 最核心的闭环 for step

```python
for step in range(max_steps):
    ret = client.infer(obs, prompt, brightness)
    action = ret["action"]
    obs, _, terminated, truncated, _ = env.step(action)
```

这三行就是核心循环：

```text
旧观测 obs
→ π0.5 动作
→ 仿真执行
→ 新观测 obs
```

后面的代码是在做安全检查、成功判定和记录证据。

### 8.19 env.step(action) 里面发生什么

从 runner 角度只是一行；框架内部大致为：

```text
(1,8) action
→ ActionCfg 拆成 7 轴 + 夹爪
→ JointPositionAction 设置七轴目标位置
→ BinaryJointPositionAction 设置夹爪开/合目标
→ ImplicitActuator 根据 stiffness/damping 产生仿真作用
→ PhysX 连续运行 8 个 120 Hz 物理小步
→ 相机渲染新图像
→ ObservationCfg 采集新状态
→ 返回新的 obs
```

### 8.20 为什么先检查 terminated/truncated

环境到达时间上限后可能自动 reset。reset 后的关节位置属于下一回合，不能记到当前轨迹。

```python
if terminated or truncated:
    break
```

必须位于记录新观测之前，否则会制造假的大关节跳变。

### 8.21 inside、is_open、is_stable

`inside`：

```text
物体 XY 进入目标范围
相对高度合理
物体至少移动 5 cm
```

`is_open`：

```text
实际夹爪观测 <= 0.25
```

`is_stable`：

```text
最近 15 步物体位置都在末位置 1.5 cm 内
```

只有三者同时满足，并连续保持 15 步，才成功。

这比“物体某一帧进入容器”严格，因为还要求真实释放并稳定留下。

### 8.22 为什么同时记录命令和观测

```text
gripper_command   模型要求夹爪做什么
gripper_observed  仿真中夹爪实际在哪里
arm_action        模型要求七轴去哪里
arm_observed      七轴实际到哪里
```

命令和实际状态不同，可以发现跟踪延迟、执行器过慢或碰撞阻挡。

### 8.23 为什么保存 NPZ 和 JSON

`trajectory.npz` 适合保存大量数组，之后可以画曲线和重新分析。

`summary.json` 适合保存少量结论，人和程序都容易读取。

视频回答“画面发生了什么”；NPZ 回答“每一步数值如何变化”；JSON 回答“这一回合是否满足规则”。

## 9. 用一个控制周期理解全部交互

假设当前观测：

```text
外部图像       180×320×3
腕部图像       180×320×3
七轴关节       [q1,q2,q3,q4,q5,q6,q7]
夹爪状态       [g]
指令           put the cube in the bowl
```

runner：

```text
图像 padding 到 224×224
→ 构造 DROID request
→ msgpack 序列化
→ WebSocket 发到 8000
```

OpenPI：

```text
反序列化
→ DroidInputs 拼成 8 维 state 和三个图像槽位
→ 归一化状态
→ 文字分词
→ π0.5 采样 15 步内部动作
→ 反归一化
→ DroidOutputs 取前 8 维
```

runner 收到：

```text
actions.shape = (15,8)
```

取第一行：

```text
[目标q1,...,目标q7,夹爪]
```

然后：

```text
转 torch.float32
→ 增加 batch 维成 (1,8)
→ env.step
→ 8 个物理小步
→ 获得新图像和状态
```

连续执行 chunk 的前 8 行后，再把最新观测发给模型。

## 10. 整个实验流程

```text
1. 准备软件
   OpenPI + Isaac Sim + IsaacLab + sim-evals

2. 准备资产
   Franka USD + scene1/2/3 + checkpoint + norm stats

3. 启动模型服务
   Docker → checkpoint → WebSocket :8000

4. 模型预热
   fake DROID obs → (15,8) finite actions

5. 验证环境
   DROID 注册 → scene → 相机 → 7轴/夹爪 shape

6. 最小闭环
   scene1 → cube into bowl

7. 严格基线
   三场景，每场景三次

8. 鲁棒性
   物体偏移、目标偏移、同义指令、亮度变化

9. 工程审计
   NaN、关节限位、动作跳变、实际跳变、推理延迟

10. 保存证据
    MP4 + PNG + NPZ + case JSON + scene JSON

11. 汇总结论
    baseline 9/9，robustness 17/18
```

## 11. 怎样获得代码迁移能力

### 11.1 不要从“改机器人名字”开始

迁移不是把 `panda_joint1` 改成 `joint1`。先写清新机器人的接口合同。

### 11.2 迁移前必须回答的十个问题

1. 有几个可控机械臂关节？
2. 每个关节的顺序、单位、零位和范围是什么？
3. 动作是位置、速度、力矩还是末端增量？
4. 夹爪是连续值还是开/关？0 和 1 分别是什么？
5. 有几张相机图？相机安装在哪里？
6. 图像 shape、颜色顺序和 dtype 是什么？
7. 状态里包含哪些数字？
8. checkpoint 在什么机器人和动作空间上训练？
9. 新机器人有没有与 checkpoint 匹配的数据？
10. 成功由哪些可计算条件判定？

### 11.3 可以复用的代码

```text
WebSocket client/server 模式
msgpack 数组传输
图像 resize/pad
动作 chunk 缓存
receding horizon
NaN/Inf 检查
推理延迟记录
视频/NPZ/JSON 证据结构
case/suite 实验编排思想
```

### 11.4 必须针对机器人改的代码

```text
机器人 USD/URDF
关节名称、数量、顺序和限位
ActionCfg
ObservationCfg
夹爪归一化和方向
相机位置与视场
策略输入输出 transform
norm stats
checkpoint 或微调数据
成功几何阈值
安全步长和工作空间
```

### 11.5 Franka 到 RM65 的具体变化

| 内容 | Franka | RM65 |
|---|---|---|
| 机械臂 | 7 轴 | 6 轴 |
| 夹爪 | Robotiq 二值接口 | 4C2 归一化接口 |
| 策略 state | 7+1 | 6+1 |
| 策略 action | 15×8 | 10×7 |
| checkpoint | DROID joint-position | RM65 数据微调的 π0.5 |
| 数据 | 已有 DROID 数据 | 自采 45 条脚本专家 episode |
| transform | DroidInputs/Outputs | RM65Inputs/Outputs |
| 环境 | sim-evals DROID | 自建 RM65 + 4C2 场景 |

不能把 Franka 动作前六维直接给 RM65，因为六个数字所代表的关节、零位、范围和训练分布都不一致。

### 11.6 推荐的迁移开发顺序

```text
A. 只加载新机器人，打印关节名称和限位
B. 手工给小幅关节目标，确认方向
C. 验证夹爪 0/1 或连续范围
D. 验证外部/腕部相机
E. 写 ObservationCfg 和 ActionCfg
F. 写脚本专家证明任务可解
G. 记录新机器人数据集
H. 写 Inputs/Outputs transform
I. 计算新 norm stats
J. 微调 checkpoint
K. 单帧推理
L. 离线 validation
M. 单 case 闭环
N. 完整可复现评测
```

## 12. 常见错误怎样定位

| 症状 | 先查什么 | 原因示例 |
|---|---|---|
| 8000 端口拒绝连接 | Docker logs | 模型服务没启动 |
| 第一次推理长时间无响应 | GPU、server logs | JAX 正在编译 |
| KeyError | request 字段 | DROID 键名拼错 |
| shape 错误 | 打印每个输入 shape | batch/图像/关节维度不匹配 |
| 图像是 `(0,)` | 相机初始化 | 还没有有效 render |
| 图像全黑 | 相机位置、灯光、render | 相机未启用或被遮挡 |
| 机器人剧烈跳动 | 动作语义 | 把速度当位置或顺序错 |
| 夹爪方向相反 | 二值/归一化约定 | 0/1 语义相反 |
| 模型一直不动 | norm stats、数据分布 | 状态尺度错误或模型学到等待 |
| 看起来成功但 JSON 失败 | 严格判定 | 未松爪或不稳定 |
| JSON 成功但视频异常 | 判定阈值 | 成功规则过宽，需要回看证据 |
| 关节跳变发生在最后一步 | terminated 顺序 | 自动 reset 被记入轨迹 |

## 13. 逐步练习

### 练习 1：只读代码并定位

```bash
cd ~/robot-learning/rm-ik-rl
less -N projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py
```

在 `less` 中使用：

```text
/TASKS
/class DroidJointPosClient
/def infer
/for step
/inside =
/np.savez_compressed
q
```

### 练习 2：手写一帧 shape 表

不要复制本文。自己写出：

```text
环境外部图：
模型外部图：
关节状态：
夹爪状态：
模型动作块：
单步动作：
env.step 动作：
```

### 练习 3：追踪一帧代码

从：

```python
ret = client.infer(obs, case.prompt, case.brightness)
```

追到：

```python
obs, _, terminated, truncated, _ = env.step(action)
```

解释每个变量的类型、shape 和所在设备。

### 练习 4：添加一个不执行的测试 case

先只在纸面设计：

```text
case 名字
改变哪个变量
为什么这个扰动有意义
保持哪些变量不变
怎样判断成功
```

再修改 `make_cases()` 并做代码审查，不直接运行完整套件。

### 练习 5：迁移接口表

给 RM65 写表：

```text
Franka 字段 → RM65 字段
7 轴 → 6 轴
Robotiq → 4C2
DROID norm stats → RM65 norm stats
DROID checkpoint → RM65 fine-tuned checkpoint
```

如果不能完整填写，就说明还不应该写迁移控制代码。

## 14. 你应该能口头讲出的完整答案

> 我没有重新实现 π0.5 或 Isaac Sim。我使用 OpenPI 提供的 π0.5 DROID joint-position checkpoint，用 sim-evals 在 IsaacLab/Isaac Sim 中创建 Franka + Robotiq 和三个 DROID 风格场景。模型服务运行在 Docker 中，监听本机 8000 端口；仿真 runner 运行在 Isaac Sim Python 中。runner 从环境读取外部相机、腕部相机、七轴关节和夹爪状态，把它们翻译成 DROID policy 的字段，通过 WebSocket 发送给模型。OpenPI 的 DroidInputs 把七轴和夹爪拼成状态，并把两张真实图像放入 π0.5 的图像槽位；模型生成 15 步动作，DroidOutputs 只返回前 8 维。runner 每次执行动作块前 8 步，再用新观测重新规划。env.step 把前七维解释成 Franka 关节位置，把最后一维解释成夹爪开合，并由 Isaac Sim 执行物理和渲染。我另外写了严格成功判定、位置/语言/亮度扰动、关节与延迟审计，以及视频、NPZ、JSON 证据。这个阶段没有训练 Franka 模型，主要工作是环境、接口、闭环和评测。迁移到 RM65 时，WebSocket 和评测框架可以复用，但机器人资产、关节和夹爪接口、相机、transform、norm stats、数据集和 checkpoint 都必须重新适配。

## 15. 源码直达链接

### 我们的正式代码

- [正式 Franka runner](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py)
- [全部 suite 编排](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_all_suites.sh)
- [最小 scene 1 runner](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_droid_scene1.py)
- [场景观测验证](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/validate_droid_sim_scene.py)
- [π0.5 预热](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/warmup_pi05_droid.py)

### sim-evals 环境代码

- [DROID 环境注册](https://github.com/arhanjain/sim-evals/blob/3a6b0e8/src/sim_evals/environments/__init__.py)
- [场景、相机、ObservationCfg、ActionCfg、频率](https://github.com/arhanjain/sim-evals/blob/3a6b0e8/src/sim_evals/environments/droid_environment.py)
- [Franka + Robotiq articulation 和 actuator](https://github.com/arhanjain/sim-evals/blob/3a6b0e8/src/sim_evals/environments/nvidia_droid.py)
- [sim-evals 原始 DROID joint-position client](https://github.com/arhanjain/sim-evals/blob/3a6b0e8/src/sim_evals/inference/droid_jointpos.py)

### OpenPI 代码

- [DroidInputs / DroidOutputs](https://github.com/Physical-Intelligence/openpi/blob/15a9616/src/openpi/policies/droid_policy.py)
- [Policy.infer](https://github.com/Physical-Intelligence/openpi/blob/15a9616/src/openpi/policies/policy.py)
- [WebSocket client](https://github.com/Physical-Intelligence/openpi/blob/15a9616/packages/openpi-client/src/openpi_client/websocket_client_policy.py)
- [WebSocket server](https://github.com/Physical-Intelligence/openpi/blob/15a9616/src/openpi/serving/websocket_policy_server.py)
- [NumPy/msgpack 序列化](https://github.com/Physical-Intelligence/openpi/blob/15a9616/packages/openpi-client/src/openpi_client/msgpack_numpy.py)
- [图像 resize_with_pad](https://github.com/Physical-Intelligence/openpi/blob/15a9616/packages/openpi-client/src/openpi_client/image_tools.py)
- [pi05_droid_jointpos_polaris 配置](https://github.com/Physical-Intelligence/openpi/blob/15a9616/src/openpi/training/misc/polaris_config.py)

## 16. 判断你是否真正读懂

不用看本文，能够独立画出下面链路并解释每个箭头，才算读懂：

```text
DROID 数据
→ checkpoint
→ OpenPI policy server
→ WebSocket
→ runner 字段转换
→ action chunk
→ IsaacLab ActionCfg
→ actuator
→ PhysX
→ camera / joint observation
→ 下一次模型请求
→ success + evidence
```

如果某个箭头解释不清，回到对应章节和源码，不要靠背术语跳过。
