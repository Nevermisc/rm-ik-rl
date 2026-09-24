# RM65-B + 4C2 + π0.5 新对话交接上下文

更新时间：2026-09-24  
用途：把本文件全文粘贴到新的 Codex 对话，继续当前项目  
注意：这是工程上下文，不是“项目已经成功”的声明

---

## 可直接复制给新对话的内容

我正在做一个 RM65-B 六轴机械臂、用户提供的 4C2 夹爪模型与 π0.5 的具身智能项目。我是新手，希望你自主推进，但必须解释每一步，让我最终能独立复现、读懂和修改代码。

### 当前执行范围

- 现在只做 IsaacLab/Isaac Sim 仿真、数据、微调和评测。
- 不连接、不控制、不向真实 RM65 或真实夹爪发送动作。
- 不把脚本专家成功、离线 MAE、单帧推理或部分案例成功冒充 π0.5 闭环成功。
- 所有重要结论必须有代码、测试或机器可读 JSON 证据。

### 机器与路径

```text
实验室新电脑：chengyu-Z790-AORUS-ELITE-AX
Tailscale 地址：100.116.242.82
SSH 用户：chengyu
Ubuntu：24.04
GPU：RTX 4080 SUPER 16 GB
内存：约 31 GB

Git 仓库：/home/chengyu/robot-learning/rm-ik-rl
项目目录：/home/chengyu/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
OpenPI：/home/chengyu/robot-learning/openpi
IsaacLab：/home/chengyu/robot-learning/IsaacLab
Isaac Sim：/home/chengyu/isaac-sim-5.1.0
```

不要把密码、令牌或私钥写入文档或 Git。SSH 使用已有授权；若 Tailscale 要求重新认证，先报告给用户。

### 权威状态检查

开始任何工作前执行：

```bash
ssh chengyu@100.116.242.82
cd ~/robot-learning/rm-ik-rl
git branch --show-current
git rev-parse --short HEAD
git status --short

cd projects/004-rm65-4c2-isaaclab
python3 -m json.tool results/project_progress.json | less
```

文档生成前的权威基线提交是 `2130709`，其后应存在本交接文档和刷新后的 `project_progress.json` 提交。以实际 Git HEAD 为准，不要依赖聊天记忆。

远端仓库长期存在一些与当前主线无关的未跟踪文件，例如根目录的旧 PPO、ROS bridge 和 `docs/13-policy-gripper-v3.md`。不要使用 `git add .`，不要删除它们，只精确 stage 本次确认过的文件。

### 已验证完成的内容

1. 新 Ubuntu 24.04 电脑迁移验收 PASS，旧电脑不再是依赖。
2. SSH、NoMachine、NVIDIA GPU、Docker GPU、OpenPI、Isaac Sim 5.1、IsaacLab 和 ROS2 Jazzy 已安装并有机器证据。
3. Franka + π0.5 参考闭环已验证：严格基线 9/9，鲁棒性 17/18，总计 26/27。
4. RM65-B 与 4C2 已组合为 URDF/USD：16 links、15 URDF joints、12 movable joints。
5. 组合资产 articulation、关节顺序、Lula IK、相机、夹爪方向和碰撞诊断已完成。
6. 顶部抓取全重力脚本专家三角度 3/3。
7. 专家数据集 `datasets/rm65_scripted_v1` 完成：45/45 episode，36 train、9 validation、20,175 frames。
8. 数据已转换为 LeRobot；v1/v2 都有独立 repo id 与 norm stats。
9. RM65 OpenPI transform 输出为 10×7：6 个绝对关节目标 + 1 个归一化夹爪目标。
10. 动作安全层可拒绝 NaN/Inf，限制关节范围、最大步长 0.05 rad 和夹爪 `[0,1]`。
11. π0.5 v1 LoRA 30k 完成，离线验证通过；正式闭环 12/20=60%，低于 80% 门禁。
12. π0.5 v2 policy-window LoRA 30k 完成，训练数值有限，loss 0.2278→0.0022；正式闭环 11/20=55%，低于门禁并比 v1 低 5 个百分点。
13. 夹爪释放几何校准完成：归一化 0.20 对应接触垫净空约 52.6 mm，能释放 40 mm 方块并保留余量。
14. 全程没有发送真机命令，正式报告均记录 `simulation_only=true`、`real_robot_command_sent=false`。

### 权威结果文件

```text
results/new_lab_pc_migration_audit.json
results/stage_summary.json
results/rm65_scripted_v1_summary.json
results/rm65_sim_train_openpi_contract.json
results/rm65_sim_train_norm_stats.json
results/pi05_rm65_formal_30k.json
results/pi05_rm65_formal_offline_validation.json
results/rm65_pi05_eval_v1_summary.json
results/rm65_pi05_eval_v1_failure_taxonomy.json
results/pi05_rm65_policy_window_v2_30k.json
results/pi05_rm65_policy_window_v2_training_log_summary.json
results/pi05_rm65_policy_window_v2_offline_validation.json
results/rm65_pi05_eval_v2_summary.json
results/pi05_rm65_policy_window_v2_failure_taxonomy.json
results/pi05_rm65_policy_window_v2_comparison_to_v1.json
results/gripper_release_threshold_calibration.json
results/project_progress.json
```

### 已知失败与准确解释

- v1 正式闭环：12/20，60%，FAIL。
- v2 正式闭环：11/20，55%，FAIL。
- policy-window 假设没有带来总体提升，不能选择性报告某些 prompt 的改善。
- v2 失败包含夹爪未开、目标误差、释放漂移与仿真越界。
- 把夹爪开度判据从最终值改为“模型命令 + 实际反馈连续验证释放”是合理的评测语义修复，但不能事后改写历史 v2 分数。
- 使用阈值 0.20 做过开发复测，完成 16 个案例，8/16 通过；这不是正式评测，因为随后发现随机采样与断点续跑语义不一致。

### 当前最重要的未完成问题：确定性 π0.5 采样

OpenPI JAX `Policy` 默认从 RNG key 0 开始，每次 `infer()` 后推进。评测套件中断后重新启动服务器时，已完成案例会被跳过，但 RNG 又从 0 开始，因此后续 case 获得了与完整顺序运行不同的 flow-matching 噪声。同一 checkpoint/条件出现成功失败翻转，不能据此继续训练迭代。

正确方案：

1. 每个评测 case 分配固定 `policy_noise_seed`；
2. 每个动作块使用 `case_seed + chunk_index`；
3. 客户端在 observation 中发送 seed；
4. 策略服务器包装 OpenPI Policy，显式生成 shape `(10,32)`、dtype `float32` 的 NumPy 高斯噪声；
5. 调用 `policy.infer(obs, noise=noise)`；
6. 返回并记录 seed、shape、dtype 和 noise SHA-256；
7. 相同 case 单独运行、完整顺序运行和断点续跑时，采样哈希与动作必须一致；
8. 只有验证通过后才重新跑 20-case 正式评测。

Windows 工作区曾留下未同步草稿：

```text
C:\Users\95380\Documents\ChatGPT\robot learning\deterministic_policy.py
C:\Users\95380\Documents\ChatGPT\robot learning\test_deterministic_policy.py
C:\Users\95380\Documents\ChatGPT\robot learning\serve_rm65_policy.py
```

这些文件尚未进入远端权威仓库、尚未完成客户端/套件改动、尚未在 OpenPI 环境测试。先审查内容，再决定是否采用，不能把它们写成已完成。

### 建议下一步顺序

1. 检查远端没有残留 `serve_rm65_policy`、Isaac Sim 或评测进程。
2. 在 `openpi_extension/deterministic_policy.py` 实现轻量包装器及纯单元测试。
3. 修改 `scripts/serve_rm65_policy.py`，用训练配置的 `action_horizon=10`、`action_dim=32` 包装策略。
4. 修改 `scripts/run_pick_place_baseline.py`，为每个 chunk 发送 seed，并验证服务器返回的采样证据。
5. 修改 `scripts/run_pi05_rm65_closed_loop.sh` 与 `scripts/run_pi05_rm65_closed_loop_suite.py`，给每个 case 固定 seed；resume 复用报告时同时校验 checkpoint、夹爪阈值和 seed。
6. 写测试证明相同 seed 噪声完全相同、不同 seed 不同、缺 seed fail closed、resume 不混用 seed。
7. 先用不启动 Isaac 的测试验证噪声哈希。
8. 再用同一案例做两次仿真复现；比较每个 chunk 的 noise hash、动作和任务指标。
9. 若动作一致而物理结果仍不同，再固定 NumPy/PyTorch/Isaac/PhysX seed，量化仿真非确定性。
10. 在评测可重复之后，用独立输出目录重新跑 20 case。达到至少 16/20 才通过。
11. 若仍低于 80%，根据确定性失败分类设计 v3；一次只改变一个主要因素。

### 重要代码入口

```text
openpi_extension/expert_episode.py
openpi_extension/rm65_policy.py
openpi_extension/action_guard.py
openpi_extension/rm65_training_config.py
scripts/run_pick_place_baseline.py
scripts/convert_expert_episodes_to_lerobot.py
scripts/train_rm65_pi05.py
scripts/serve_rm65_policy.py
scripts/run_pi05_rm65_closed_loop.sh
scripts/run_pi05_rm65_closed_loop_suite.py
scripts/analyze_rm65_closed_loop_failures.py
scripts/compare_rm65_closed_loop_runs.py
scripts/build_project_progress.py
```

### 面向新手的沟通要求

- 使用中文，先说结论，再解释原理。
- 每次运行前说明要做什么、为什么、会生成什么证据。
- 把命令拆成小步骤，让用户有机会亲手执行和观察。
- 解释输入、输出、shape、单位、坐标系和失败行为。
- 不因用户是新手而降低验证标准。
- 区分事实、推断、假设和待验证项。
- 长任务每个重要里程碑汇报，不用空泛进度占用上下文。
- 有意义的改动精确 stage、测试后提交；GitHub 未授权时保留本地 Git 提交。

### 配套教学文件

```text
docs/RM65_PI05_HANDS_ON_GUIDE_ZH.md
docs/RM65_PI05_LEARNING_JOURNEY_ZH.md
docs/FULL_PROJECT_TUTORIAL_ZH.md
docs/CODE_ARCHITECTURE_GUIDE_ZH.md
```

请先从权威仓库和 JSON 重新核对状态，然后继续“确定性采样”任务。不要控制真机。

---

## 使用说明

新对话开始时，把“可直接复制给新对话的内容”整段发送。若上下文预算有限，至少保留：当前执行范围、路径、正式结果、确定性采样问题、下一步顺序和安全边界。
