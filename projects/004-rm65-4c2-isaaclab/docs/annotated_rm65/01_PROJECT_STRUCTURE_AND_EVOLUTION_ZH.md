# RM65-B + 4C2 + π0.5：项目结构、问题与演进路线

> 范围：只讲 Isaac Sim / IsaacLab 仿真，不控制真实机械臂。
>
> 当前源码基线：`0cd249e153b43ab880f3571d286013cadaf7331a`。
>
> 证据原则：本文件把“Git 中确有修改”和“实验结果已经通过”分开。提交存在只能证明代码发生了变化；成功率、任务成功等结论必须再看 task report、suite summary 或训练报告。

## 1. 先建立整套系统的骨架

整个项目不是一个程序，而是一条有先后依赖的链：

```text
RM65 URDF + 4C2 URDF
        │
        ▼
合并机器人资产 ──> 导入 USD ──> IsaacLab 场景与脚本专家
                                      │
                                      ▼
                              专家 episode（NPZ+PNG）
                                      │
                                      ▼
                         LeRobot 数据集 + norm stats
                                      │
                                      ▼
                      OpenPI 官方训练器 + RM65 LoRA 配置
                                      │
                                      ▼
                              RM65 π0.5 checkpoint
                                      │
                                      ▼
                     WebSocket policy server（模型进程）
                                      │
                                      ▼
外部图像+腕部图像+6关节+夹爪+文字 ─> RM65Inputs ─> π0.5
                                                           │
                                                           ▼
                          IsaacLab <─ action guard <─ 10×7 动作块
                              │
                              ▼
                 task_report ─> 独立验收 ─> 多 case suite/gate
```

你以后迁移到另一种机械臂时，核心思路就是逐层替换这条链中的“机器人专属部分”，同时尽量保留 OpenPI、LeRobot、WebSocket 和评测框架。

## 2. 哪些是外部开源能力，哪些是本项目自己写的

### 外部开源/机构提供

- **OpenPI / π0.5**：模型结构、基础 checkpoint、transform 框架、官方 JAX 训练器和 WebSocket 协议。
- **Isaac Sim**：物理、渲染、USD、PhysX 和应用运行时。
- **IsaacLab**：机器人 articulation、刚体、相机、接触传感器和仿真循环的 Python 接口。
- **LeRobot**：训练数据集的统一存储形式。
- **NVIDIA Lula**：RM65 的正逆运动学求解。
- **NumPy / Torch / Pillow / einops**：数组、GPU 张量、图像和维度变换工具。
- **RM65 与 4C2 模型文件**：机器人几何和关节定义的原始来源。

### 本项目自己写的 20 个核心程序

| 阶段 | 自己写的程序 | 它补上的缺口 |
|---|---|---|
| 资产 | `build_combined_urdf.py`、`import_combined_urdf.py` | 官方 OpenPI 不知道你的 RM65 与 4C2 怎样安装，也不会替你修 CAD 惯量和接触几何 |
| 抓取几何与仿真 | `grasp_geometry.py`、`run_pick_place_baseline.py` | 创建 RM65 场景、连续 IK、脚本专家、物理执行、相机和结果判定 |
| 原始轨迹 | `expert_episode.py`、`run_expert_collection_plan.py` | 定义一帧是什么、怎样同步记录、怎样可恢复地采多条轨迹 |
| 训练数据 | `convert_expert_episodes_to_lerobot.py`、`compute_rm65_norm_stats.py` | 把自定义轨迹变成 OpenPI 能训练的数据，并计算 RM65 自己的数值分布 |
| 模型适配与训练 | `rm65_policy.py`、`rm65_training_config.py`、`train_rm65_pi05.py` | 把六轴 RM65+夹爪映射到 π0.5 字段，定义动作语义和低显存 LoRA 训练 |
| 推理与兼容 | `serve_rm65_policy.py`、`websocket_compat.py`、`action_guard.py` | 模型独立服务、WebSocket 版本兼容、模型动作的 shape/限位/步长防线 |
| 验收与批量实验 | `closed_loop_report.py`、`check_closed_loop_task_report.py`、`run_pi05_rm65_closed_loop.sh`、`run_pi05_rm65_closed_loop_suite.py` | 防止“程序没报错”被误当成“任务成功”，并运行可恢复多条件评测 |
| 训练后流水线 | `validate_rm65_checkpoint.py`、`run_rm65_post_training_pipeline.sh` | 先做便宜离线验证，再进入昂贵闭环，最后保留失败阶段和证据 |

## 3. 从参考 Franka 到 RM65 的迁移逻辑

### 第一步：先理解参考链路

Franka 阶段的价值不是得到 RM65 结果，而是验证五件通用的事：

1. checkpoint 能否加载；
2. 相机、机器人状态和文字怎样组成 observation；
3. WebSocket 怎样把仿真进程和模型进程隔离；
4. 模型怎样返回动作块；
5. 仿真怎样执行少量动作后重新观察，形成闭环。

这一步里能复用的是**系统连接方式**，不能直接复用的是 Franka 的 7 个手臂关节、夹爪语义、相机布局、动作统计和任务几何。

### 第二步：换机器人资产

**原问题**：RM65 与 4C2 是两份独立 URDF；名字、根节点、安装关系、mesh 路径和惯量不一定满足 Isaac 的要求。

**修改**：`build_combined_urdf.py` 给夹爪节点加前缀，用固定关节接到 `link_6`，重写 mesh URI，修正质量/惯量并加指尖接触片。`import_combined_urdf.py` 再导入 USD 并重新打开检查 articulation。

**为什么分成两个程序**：XML 合并可在普通 Python 中快速测试；URDF→USD 必须在 Isaac Sim 应用启动后运行。分开以后资产错误和 Isaac 运行时错误更容易定位。

**Git 证据**：`64c584a1` 建立迁移骨架；`b1c1a72a` 扩展仿真验证；`06b44e2a` 验证接触运输；`4a4794a5` 推进自然重力抓取。

### 第三步：先写脚本专家，再谈模型

**原问题**：若几何、IK、摩擦或夹爪都没调通，π0.5 失败时无法知道是模型错还是仿真错，也没有自己的训练数据。

**修改**：`run_pick_place_baseline.py` 把任务分成稳定、接近、闭合、抬升、搬运、下降、松爪和等待。`grasp_geometry.py` 计算顶部抓取姿态；连续 IK 选择避免腕部在等价解之间突然翻转。

**为什么先有辅助基线再去掉辅助**：辅助条件先证明阶段顺序和坐标正确，然后逐渐恢复动力学、自然重力和真实接触，每次只增加一类不确定性，方便判断故障来源。

**Git 证据**：`651886ee`、`820e3009` 是辅助 pick-place；`340abde8` 推进动态抓取；`073a3184` 完成顶部全重力基线；`c3411703` 约束连续腕部分支。

### 第四步：把专家运动变成可训练数据

**原问题**：最终“成功”标签不能教模型每个时刻该怎样动；图像、状态和动作若错一帧也会形成错误监督。

**修改**：`expert_episode.py` 定义同步帧合同和磁盘格式；`run_expert_collection_plan.py` 按预注册 case 采集且只复用验证完整的 episode；转换程序写成 LeRobot schema；norm-stats 程序在与训练相同的 transform 后统计。

**为什么不能直接使用 DROID 的统计量**：DROID/Franka 的关节数量、范围、相机和动作分布不同。错误统计量会让相同数值在模型眼中代表完全不同的尺度。

**Git 证据**：`c6a87c23` 建立 episode 管线；`82b3846f` 加入可恢复采集；`1b21e1d1` 增加 policy-window 数据以减少长静止段。

### 第五步：建立 RM65 与 π0.5 的接口合同

**原问题**：官方 checkpoint 认识通用/DROID 风格键，不认识 `observation/joint_position` 等 RM65 自定义键；模型也不会自动知道“前六维是手臂、最后一维是夹爪”。

**修改**：`rm65_policy.py` 把六关节和一个夹爪拼成七维 state，把两路图像映射到三个模型槽并用 mask 表示缺失图像；训练时再把七维教师 actions 送入。输出只保留每步前七维。

**动作语义选择**：训练 transform 将前六个关节动作转成相对当前状态的 delta，夹爪仍用绝对 0～1。关节 delta 更容易学习局部运动；夹爪若做 delta 会让开/合语义随历史累积而漂移。

**Git 证据**：`2b2df452` 准备 LoRA 数据配置；`0f92fcd8` 加入低内存训练；`28aef624` 贯穿 norm-stats repo id，防止加载错统计量。

### 第六步：微调而不是从零训练

**原问题**：π0.5 参数量大，RM65 数据量和 16 GB GPU 不适合从零或全量训练。

**修改**：`rm65_training_config.py` 选 π0.5 基础权重、10 步 horizon、LoRA，并冻结视觉编码器；`train_rm65_pi05.py` 校验数据来源、恢复/覆盖规则后调用 OpenPI 官方 trainer。

**关键边界**：我们自己写的是 RM65 配置与前置门禁；梯度、优化器、checkpoint 保存等核心训练循环来自 OpenPI 官方代码。

### 第七步：把 checkpoint 放入闭环

**原问题**：OpenPI/JAX 与 Isaac Sim 的 Python 依赖不同；模型一次输出全部轨迹又无法根据物体实际运动纠错。

**修改**：模型进程用 `serve_rm65_policy.py` 提供 WebSocket 服务；Isaac 进程观察一次、请求 10 步、经过 `action_guard.py`、执行前若干步，再重新拍图请求。

**为什么需要 `websocket_compat.py`**：早期实际出现 keepalive ping timeout，Isaac 与 OpenPI 环境的 websockets 版本接口不同。兼容层检查 `connect` 签名，支持时禁用 ping，旧版本则移除不认识的参数。

**为什么需要 action guard**：神经网络输出可能有 NaN、越过机械限位或动作突跳。guard 让这些问题变成可记录的裁剪/拒绝，而不是仿真失稳。

**Git 证据**：`82258522` 建立闭环评测；`f18f8ca8` 修复 WebSocket 并强制 task report；`be75d24` 加入可恢复仿真 gate。

### 第八步：把“看起来成功”变成可复核成功

**原问题**：方块短暂经过目标、夹爪视觉张开但命令未张开、程序正常退出、复用了旧 checkpoint 报告，都可能是假成功。

**修改**：独立 validator 要求真实动作数、抬升、到位、模型释放命令、实际夹爪张开和稳定后置条件；suite 绑定 checkpoint、case、场景和观测证据，并保留基础设施故障与任务失败的区别。

**演进**：`66d5d71b` 校准释放验证；`10e444f5` 记录控制器设置；`98de4494` 对不完整报告 fail-closed；`4427a005` 保存精确 policy observation；`0264302f` 增加重复性 gate；`aff560c8` 锁存释放后置条件。

### 第九步：根据失败继续迭代 v3/v4

**原问题**：早期版本已能闭环，但未达到项目预设鲁棒性门槛；释放监督、相机观测一致性、数据来源和失败证据仍需加强。

**修改**：固定采样与仿真种子、保存观测指纹、跳过 π0.5 模式不用的脚本 IK、准备失败修正数据、审计 v3 数据 provenance，并为 v4 修正/确认数据预注册门禁。

**Git 证据**：`203c9b9b` 确定性采样；`5d113153` 仿真种子与相机分歧诊断；`c707b7d4` 跳过未使用 IK；`a2f7ace3` 准备 v3 修正；`79e66ceb` 完成 v3 训练并增强 provenance；`a2167ed7`、`d17358ad` 预注册并门禁 v4。

这里必须保持准确：这些提交证明代码和训练准备发生过，不自动证明 v3/v4 已通过最终仿真成功率门槛。最终结论应以对应 suite summary 为准。

## 4. 怎样把单个文件读成结构化知识

打开任一 `*.逐行注释.md`，按固定顺序学习：

1. 看“本程序在整个项目中的位置”，先知道上游和下游；
2. 看“原先的问题”和“解决办法”，知道为什么存在；
3. 看基础数据结构，先分清 dict、tuple、list、ndarray、Tensor；
4. 看模块地图，只形成 5～20 个逻辑块，不背几千行；
5. 进入一个模块，先看数据流，再看变量和函数卡；
6. 最后读逐行注释，回答“这行拿到什么，改变什么，交给谁”；
7. 看模块版本变化，区分新增、删除、替换以及它针对的问题；
8. 合上文档，用自己的话画出输入→处理→输出。如果画不出来，回看模块数据流，而不是继续背下一行。

## 5. 你真正掌握后的自测问题

- 为什么 RM65 不能直接套 Franka/DROID 的 state、action 和 norm stats？
- 为什么训练样本里有 `actions`，在线 infer 请求通常没有？
- 为什么图像槽有三个但 RM65 只有两路真实相机？
- 为什么前六维 action 做 delta，夹爪维保持 absolute？
- 为什么模型服务与 Isaac 仿真分进程？
- 为什么 10 步动作只执行前几步就重新观察？
- 为什么程序退出码为 0 仍不能证明任务成功？
- 为什么需要脚本专家、训练集、验证集和未见条件 suite 四种不同角色？
- 怎样从一次失败追到：资产、IK、接触、相机、transform、checkpoint、动作安全或释放判定？

能独立回答这些问题，再去修改动作维度、相机键、任务几何或数据 schema，你就开始具备把同一框架迁到新机械臂/新任务的能力。
