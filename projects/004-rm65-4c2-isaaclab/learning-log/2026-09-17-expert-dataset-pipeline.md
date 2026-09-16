# 2026-09-17：从脚本专家到 π0.5 数据管线

## 起点

RM65 + 4C2 已经能在 Isaac Lab 中以脚本专家完成严格顶部抓取、抬升、转运、下降、自然释放和撤离，0.6、0.8、1.0 rad 三种转运角全部通过。这个结果证明任务动力学链路可以工作，但它没有形成 π0.5 微调需要的时间序列数据。

## 本轮完成

新增 `rm65_expert_episode_v1` 中间格式和严格校验器。每帧保存：

- 六个 RM65 实际关节角；
- 归一化 4C2 主关节；
- 六个绝对目标关节角与夹爪目标；
- 方块世界位姿；
- 仿真时间、物理步编号和状态机阶段；
- 语言指令；
- 可选的外部与腕部 RGB。

记录器嵌入现有控制循环，物理频率保持 240 Hz，默认每 12 步采一帧，得到 20 Hz 策略数据。样本语义固定为“先读取当前观测，再保存紧接着要执行的目标动作”。初始直接写入仿真状态后，跳过第 0 步的陈旧数据缓冲区，从第一个完整采样周期开始记录。

双相机代码已接到同一采样点。腕部相机使用 `tool_base_link` 局部坐标外参，每次采样根据当前工具位姿更新。外部相机固定观察源与目标的中点。脚本只在 `--record-images --enable_cameras` 同时给出时启用渲染。

新增转换器，把成功且图像完整的 episode 转为 OpenPI 使用的 LeRobot 数据集。字段为：

```text
image, wrist_image, joints, gripper, actions, task
```

`joints` 与 `gripper` 分开保存，以便训练与推理直接共用现有 RM65 transform。转换器拒绝任务失败、缺图、不同帧率、不同相机尺寸和已有输出目录的隐式覆盖。

## 本地验证

以下检查通过：

```text
test_expert_episode.py: PASS
test_lerobot_conversion_input.py: PASS
py_compile: PASS
git diff --check: PASS
```

单元测试覆盖带双图像 episode、无图像低维 episode、状态与动作形状、阶段编号、时间顺序、夹爪范围和 LeRobot 转换器的输入发现。

## 尚未通过的门槛

实验室主机 `100.93.102.19` 在本轮工作期间 SSH 超时，因此还没有在真实 IsaacLab 进程中验证两个 Camera 对象、逐帧渲染和完整状态机同时运行。当前只允许写成“实现完成、本地格式测试通过”，不能写成“双相机示教采集已实测通过”。

主机恢复后第一条命令：

```bash
bash scripts/run_recorded_expert_demo.sh
```

验收条件：

1. 完整任务报告为 `status=pass`；
2. `unassisted_full_task_complete=true`；
3. episode 校验为 `status=pass`；
4. `images_recorded=true`；
5. `training_ready=true`；
6. 人工检查外部和腕部图像序列没有黑帧、陈旧帧或明显错位。

通过后才能开始多扰动示教收集、LeRobot 转换、归一化统计与 π0.5 RM65 LoRA 微调。
