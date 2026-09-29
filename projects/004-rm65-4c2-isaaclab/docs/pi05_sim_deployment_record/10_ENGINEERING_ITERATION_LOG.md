# RM65-B + pi0.5 工程迭代逐步日志

本文件从 Git 基线 `0264302` 开始，按代码变更逐条追加。它回答六个问题：**当前版本是什么、下一步是什么、改了什么、遇到什么问题、为什么这样做、怎样验证与解决**。

## 记录协议

1. 每次代码变更与对应日志条目放在同一批修改中，使用递增工作版本 `v3-fc-wip.NNN`。
2. 提交 GitHub 后，在后续条目中补记真实 commit；提交前不把工作版本冒充 Git commit。
3. 运行时里程碑即使不改代码也追加记录，包括数据规模、通过率、失败原因和证据路径。
4. 被用于诊断、调参或训练的旧评测条件永久标记为开发条件，不再作为独立最终成绩。
5. 大型图像、轨迹和模型权重不进 Git；Git 只保存计划、代码、紧凑报告和可复现说明。

## 迭代记录

### v3-fc-wip.001：失败纠正计划与多数据根转换

- Git 基线：`0264302`；状态：尚未提交。
- 准备做：把正式 60-case 中 6 个失败转成训练纠正数据，并保持原训练集不可变。
- 做了什么：新增 `build_rm65_failure_correction_plan.py` 及 8 项测试；每个失败条件采集 3 次相同物理条件的不同 RTX 渲染，再加角度 `±0.025 rad` 邻域，共 30 条。转换器改为可合并多个独立数据根，并新增转换输入测试和 JSON 报告。
- 遇到的问题：若直接把数据追加到旧目录，会破坏旧数据集的可追溯性；若只采一次，无法让模型看到同状态下的 RTX 微小渲染变化。
- 为什么做：6 个失败是当前最直接的策略薄弱区。重复同条件比继续添加普通增强更贴近已经观测到的根因。
- 怎么解决：原始数据保留在 `datasets/rm65_scripted_v1`，纠正数据写入独立的 `datasets/rm65_pi05_failure_correction_expert_v1`，只在生成新的 LeRobot repo 时合并。
- 验证：计划 13 项验证通过，生成 6 个源失败、30 个训练条件；生成器 8 项测试和多根转换测试通过。
- 数据边界：这 6 个失败条件及其邻域从此属于开发/训练条件，不能再用于独立最终确认。

### v3-fc-wip.002：从 v2 检查点做保守增量微调

- Git 基线：`0264302`；状态：尚未提交。
- 准备做：避免从 pi0.5 base 重头训练，先验证能否从 v2 已训练参数继续微调。
- 做了什么：训练配置和入口新增 `initial_params_path`、warmup、峰值/衰减学习率参数；新增 8 项配置测试。
- 遇到的问题：原脚本的学习率和初始化路径固定，不能明确表达“从 v2 继续训练”，也难以审计这次训练到底加载了什么。
- 为什么做：新数据只有 30 条，直接用原先较大学习率训练 30k 步更容易遗忘已有能力；保守增量微调风险更低。
- 怎么解决：冻结视觉编码器的既有策略不变，计划从 `rm65_policy_window_v2_lora_30k/29999/params` 初始化，正式训练 10k 步，warmup 500，峰值学习率 `5e-6`、末端 `1e-6`。
- 验证：远程 8 项配置测试通过；v2 参数目录存在且约 5.1 GB；当时没有冲突训练进程。

### v3-fc-wip.003：可重复的数据准备与训练入口

- Git 基线：`0264302`；状态：尚未提交。
- 准备做：把 30 条纠正轨迹完成后的“汇总→合并→归一化→OpenPI 批次验证→训练”变成 fail-closed 流程。
- 做了什么：新增 `prepare_rm65_failure_correction_v3.sh` 和 `train_rm65_pi05_failure_correction_v3.sh`。
- 遇到的问题：手工运行多条命令容易混错 repo id、归一化资产或初始化 checkpoint；训练进程也可能互相冲突。
- 为什么做：本阶段最重要的是可复现和不覆盖旧成果，而不仅是能启动一次训练。
- 怎么解决：数据准备要求纠正集 30/30 通过、合并后必须恰好 66 条训练 episode；训练前验证 conversion、norm、OpenPI contract、norm SHA-256 和 v2 参数目录，并拒绝并发训练。先提供 2-step smoke，再允许 10k 正式训练/断点续训。
- 验证：两个 shell 脚本语法检查通过；正式数据门禁会在 30 条采集完成后执行。

### v3-fc-wip.004：训练前冻结全新确认集与严格门槛

- Git 基线：`0264302`；状态：尚未提交。
- 准备做：在看到 v3 结果之前就固定最终确认条件，避免事后挑选容易样例。
- 做了什么：新增 `build_rm65_v3_confirmation_plan.py` 及 10 项测试；闭环套件支持由计划声明成功率门槛，默认旧门槛仍为 80%，v3 确认计划使用 90%。
- 遇到的问题：旧套件把 80% 写死；已有训练/评测和失败纠正已经消费了大量角度、位姿组合和 seed，不能复用。
- 为什么做：训练纠正有效与否必须由真正未见条件判断，旧失败条件只能衡量开发集回归。
- 怎么解决：预注册 20 条新连续插值条件，角度为 `0.6625/0.7375/0.8125/0.9125 rad`，使用新偏移与新策略/仿真 seed；同时对原始 45 条训练、30 条纠正和 100 条历史评测条件做不相交验证。
- 验证：确认计划 12 项约束全部通过；考虑了 75 条训练条件和 100 条历史评测条件；闭环套件 24 项回归测试通过。
- 验收：必须 20/20 报告齐全且至少 18/20 成功。正常模型失败不得选择性重试。

### v3-fc-wip.005：建立“代码变更即记账”机制

- Git 基线：`0264302`；状态：尚未提交。
- 准备做：继续完成纠正数据采集、构建 v3 数据集并先跑 2-step 增量训练冒烟。
- 做了什么：新增本逐步日志和机器可读的 `ITERATION_STATUS.json`；之后每次代码修改都必须同时更新二者。
- 遇到的问题：原 `CHANGELOG.md` 适合阶段汇总，但粒度不足以还原每一步为何发生，也没有明确标示提交前的工作版本。
- 为什么做：当前工作包含数据、训练、仿真确定性与评测隔离，多条线并行时若只在最后总结，容易丢失决策依据和失败尝试。
- 怎么解决：把 Git 基线、WIP 版本、当前动作、下一动作、验证和数据泄漏边界都固定为日志字段；commit 后再回填真实提交标识。
- 当前运行状态：30 条失败纠正专家轨迹正在远程串行采集；记录本条时已确认至少 8 条完整 episode，采集进程仍正常运行。
- 下一步：完成 30/30 健康检查，生成 66 条合并训练集与新归一化统计，做 2-step smoke；只有 smoke 通过才启动 10k 正式微调。

### v3-fc-wip.006：长任务资源审计与准备版本封存

- Git 基线：`0264302`；状态：准备提交本阶段代码与计划。
- 准备做：在继续长时间采集和训练前确认磁盘/GPU余量，并把可复现入口先推送 GitHub。
- 做了什么：检查远程资源、精确核对本阶段待提交文件并执行 `git diff --check`；未把大型轨迹、LeRobot 数据或权重加入 Git。
- 遇到的问题：采集、转换和检查点可能占用较多磁盘；若等正式训练完成后才提交代码，中途异常会失去一个清晰的可恢复版本。
- 为什么做：长任务应在启动前证明资源充足，并把运行它所依赖的代码与预注册计划冻结。
- 怎么解决：确认根分区约 2.3 TB 可用，9 条纠正轨迹约 556 MB，采集时 GPU 约 4.7/16.4 GB、60% 利用率、38°C；只精确暂存列出的 21 个项目文件。
- 验证：相关 Python 单元测试、shell 语法检查、计划验证和空白检查均通过。
- 下一步：推送准备版本，继续完成 30 条采集；只在健康汇总 30/30 通过后运行数据准备脚本。

### v3-fc-wip.007：GitHub 准备版本已落盘

- 上一工作版本提交：`a2f7ace32af167a1c3269a98ace8133218a5c034`（`Prepare RM65 pi0.5 failure-correction v3`）。
- 远程状态：本地 `main` 与 `origin/main` 均指向 `a2f7ace`，GitHub 推送已核对。
- 做了什么：提交并推送 20 个精确选择的项目文件，共新增约 1603 行、删除 12 行；未暂存仓库中的其他用户文件，也未提交轨迹或权重。
- 遇到的问题：提交前工作日志只能写 Git 基线，不能预先知道自身 commit hash。
- 为什么做：需要在长时间采集结束前拥有一个可恢复、可复核的代码版本。
- 怎么解决：先冻结并推送准备版本，再用本条记录实际 commit；后续结果提交将包含本条。
- 当前运行状态：推送核对时纠正采集已完成 11/30，后台进程正常。
- 下一步：继续采集至 30/30，运行专家健康门禁；在此之前不转换、不训练。

### v3-fc-wip.008：合并训练集增加来源数量门禁

- Git 基线：`a2f7ace`；状态：尚未提交。
- 准备做：在纠正采集完成后证明新训练集不只是总数为 66，而且来源恰好为旧训练 36 + 纠正 30。
- 做了什么：转换器为每个 episode 标注解析后的源数据根，并在报告中增加 `episode_count_by_dataset_root`；数据准备脚本对 `[30, 36]` 做 fail-closed 检查；转换输入测试增加来源标注断言。
- 遇到的问题：原门禁只验证 `episode_count == 66`，若 split 或路径配置错误，理论上可能出现错误的来源比例但总数碰巧正确。
- 为什么做：失败纠正训练需要保留旧能力，36:30 的组成是训练假设的一部分，必须成为机器可审计证据。
- 怎么解决：在不可变源根被加载时记录 provenance，不修改 episode 内容；最终 JSON 同时保存绝对源路径和各自数量。
- 验证计划：远程重跑转换输入测试与 shell 语法检查；完整 36/30 门禁在采集完成后的真实转换中验证。
- 当前运行状态：更新前已确认 12/30 个 task report 均为 `pass`。

### v3-fc-wip.009：预注册“独立确认 + 三轮重复性”双门禁

- Git 基线：`67d26c2`（`Audit RM65 v3 training data provenance` 已推送）；状态：尚未提交。
- 准备做：让 v3 不仅在全新条件上达到成功率，还必须证明同 seed 条件的结果足够一致。
- 做了什么：确认计划增加预注册的 3 次重复、预期 checkpoint/repo/controller 合同，以及 60 份报告、95% 状态一致率、最多 1 个结果翻转的重复性门禁。
- 遇到的问题：原确认计划只定义单轮 20-case 的 90% 成功率，不能直接被现有重复性分析器使用，也可能把后两轮误当成新的独立成功率样本。
- 为什么做：第一次运行可以作为未见条件的独立确认；后两次只用于估计重复性，不能扩大独立样本数。两类证据必须在训练前明确分开。
- 怎么解决：冻结预期最终 checkpoint `rm65_failure_correction_v3_lora_10k/9999`，第一轮要求至少 18/20；相同计划共运行三次后另行要求至少 19/20 条件状态一致且翻转不超过 1 条。
- 验证计划：重新生成计划/验证报告，运行 13 项生成器测试；正式训练结束后按同一计划保存三个独立输出根。
- 当前运行状态：上一轮查询时 14/30 个已完成 task report 全部为 `pass`。

### v3-fc-wip.010：v3 训练后评测入口

- Git 基线：`cf9cc5f`（双门禁预注册已推送）；状态：尚未提交。
- 准备做：把训练后的离线检查、首轮独立确认、两轮重复运行和最终一致性分析固定成不会混淆的入口。
- 做了什么：新增 `evaluate_rm65_pi05_failure_correction_v3.sh`，提供 `preflight/offline/run1/run2/run3/analyze` 六种明确模式。
- 遇到的问题：若手工拼接命令，容易把 checkpoint、归一化 repo、输出根或单轮/重复性证据混在一起；三轮结果也可能被错误相加成 60 个独立成功率样本。
- 为什么做：评测证据的独立性与模型结果同样重要。训练前固定入口能减少看到结果后的自由度。
- 怎么解决：评测前强制检查训练报告、实际 checkpoint id、repo id、20 条计划、90% 单轮门槛、3 次重复和 95% 一致性门槛；run1 是独立确认，run2/run3 仅提供重复性证据，最后单独分析 20×3。
- 验证计划：当前先执行 shell 语法检查；正式 checkpoint 产生后再运行 preflight 和 offline，之后按 run1→run2→run3→analyze 顺序执行。
- 当前运行状态：最近确认 16/30 条纠正轨迹全部通过。

### v3-fc-wip.011：纠正专家轨迹失败的保留式恢复

- Git 基线：`20758ae`（分阶段评测入口已推送）；状态：运行时恢复进行中。
- 准备做：处理 `episode_000019` 的 fail-closed 停止，不丢失失败证据，也不让失败轨迹进入训练。
- 做了什么：读取 task report、episode 验证和 collection case 元数据，逐项对照成功标准。
- 遇到的问题：第 20 次采集对应 `correction_robust_041_angle_plus_0p025`；文件、569 帧、双相机图像和数值有限性全部健康，但无辅助任务判定失败，采集器因此按设计退出。
- 根因：方块抬升 `0.03952 m`、最终目标位置误差 `0.00870 m`、夹爪开度均通过；唯一失败项是释放后漂移 `0.02517 m`，高于 `<0.02 m` 门槛。这是专家物理执行失败，不是文件损坏或基础设施缺报。
- 为什么仍可重采：这是训练数据生成阶段，不是冻结策略的正式成功率评测；失败样本不得冒充专家标签，但可以保留失败证据后重新获取合格示范。最终确认计划仍禁止正常模型失败的选择性重试。
- 怎么解决：把失败目录移动到独立 rejected 根并保留为 `attempt_001`，在原数据根释放 `episode_000019` 槽位，再用原计划恢复；采集器会跳过前 19 条已通过轨迹并重采相同 case。
- 恢复门禁：重采结果仍必须逐项通过，不降低 `post_release_drift_m < 0.02` 标准；若同条件持续失败，则停止并修改专家/数据计划，而不是反复刷结果。
- 当前可用数据：19/30 条通过，1 条失败待隔离。

### v3-fc-wip.012：用可行的源位姿邻域替换不可行目标角度邻域

- Git 基线：`20758ae`；状态：尚未提交。
- 准备做：停止重复不可行的 `robust_041 + 0.025 rad` 专家条件，保持 30 条总规模并继续采集。
- 做了什么：计划生成器新增一条显式、可审计的专家不可行替换；`correction_robust_041_angle_plus_0p025` 改为同一源失败的 `source_x_inward_0p001875`，episode index 仍为 19。新增 5 项替换测试和紧凑证据 JSON。
- 遇到的问题：`0.675 rad` 两次正式采集得到逐值相同的 `0.025172 m` 释放漂移；`0.670 rad` 最近邻探针仍失败，漂移 `0.025225 m`。继续改角度会消耗时间且可能污染已冻结的最终确认角度。
- 为什么做：这里要生成合格专家标签，不应降低成功门槛或把确定失败轨迹标成成功；同时需要保留对 `robust_041` 源抓取位姿的局部覆盖。
- 怎么解决：保留可行的 `0.65 rad` 目标侧运动，只把源 x 从 `-0.01125` 调到 `-0.009375 m`。探针以漂移 `0.009954 m`、最终误差 `0.016895 m`、抬升 `0.039528 m` 通过全部原判据。
- 数据治理：两次计划失败和两个诊断探针都保留在 rejected 根，不进入训练；正式槽位必须按修订后的计划重新采集并写入正确 case id。
- 验证计划：重跑 13 项计划生成测试、重新生成 30-case 计划/验证，并重新验证最终确认计划仍与所有 75 条训练条件不相交。

### v3-fc-wip.013：修正 scripted 预检失败的报告语义

- Git 基线：`7e038b1`（不可行 `robust_041` 替换已推送）；状态：尚未提交。
- 准备做：在继续处理 `robust_042` 专家不可行问题前，先保证预检失败报告不会混淆 scripted expert 与 pi0.5。
- 做了什么：`build_preflight_safety_failure_report` 新增显式 `pi05_used`/`expert` 模式；scripted 失败现在清空 checkpoint/noise，移除策略采样证据，标记 `execution_mode=scripted_expert`，并说明没有可训练 episode。调用方和单元测试同步更新。
- 遇到的问题：episode 20 在 scripted 放置 IK 安全预检时以 `3.364869 rad > 0.75 rad` 被拒绝，实际没有策略推理或机械臂运动，但旧通用报告硬编码成 `pi05_used=true`、`policy_checkpoint_id=unknown`，导致根因看起来像策略评测失败。
- 为什么做：训练数据失败与策略失败必须严格区分；错误模式标签会污染失败统计和后续自动审计。
- 怎么解决：保留同一结构化 preflight 原因，但根据真实执行模式生成字段；pi0.5 默认行为保持兼容，原闭环验证逻辑不变。
- 验证计划：远程运行闭环报告测试与 Python 编译；之后再执行 scripted 诊断，确认新报告为 `pi05_used=false`。
- 当前状态：替代 episode 19 已以正确 case id 通过；可用纠正数据 20/30。episode 20 的原条件和首次向内偏移都在运动前触发 IK 分支跳变，正在寻找不污染确认集的可行邻域。

### v3-fc-wip.014：替换 `robust_042` 全组不可行源位姿

- Git 基线：`7e038b1`；状态：尚未提交，与 v3-fc-wip.013 一并验证。
- 准备做：保留 `robust_042` 的 3 次重复和 `±0.025 rad` 角度结构，同时移出导致 scripted place IK 分支跳变的源位姿。
- 做了什么：计划生成器把 `robust_042` 的五个变体统一加后缀 `source_x_inward_0p00375`，源 x 从 `0.01125` 改为 `0.0075 m`，各自角度仍为 `0.65/0.65/0.65/0.625/0.675`。新增 3 项单元断言和独立紧凑证据。
- 遇到的问题：原位姿在 `0.110 m` 放置 waypoint 跳变 `3.364869 rad`；向内 `1.875 mm` 后仍为 `3.343472 rad`；仅改 transfer angle 到 `0.625 rad` 不改变源侧放置路径，仍失败。
- 为什么做：所有五个变体共享同一源抓取/垂直放置路径，因此只替换一个 exact case 不够；降低 0.75 rad 安全阈值或跳过预检都不可接受。
- 怎么解决：继续单调向内搜索到 `x=0.0075 m`。完整任务通过，最大关节步长仅 `0.040799 rad`，释放漂移 `0.002308 m`，最终误差 `0.009459 m`，抬升 `0.039593 m`。
- 额外改进：专家启动脚本在未生成 `metadata.json` 时现在给出明确的“预检前停止、不可训练”错误，不再让验证器抛出误导性的缺文件 traceback。
- 验证计划：运行 16 项计划测试、报告回归测试、shell 语法检查；重建纠正计划并再次检查 20 条最终确认条件不相交。
- 测试修正：首次回归暴露测试仍用“计划最后一条”定位 `robust_041`；增加 `robust_042` 后该假设失效。现改为按源 case id 与被替换 variant 精确定位，生产逻辑未因此放宽。

### v3-fc-wip.015：移除 `robust_042` 的物理不稳定角度邻域

- Git 基线：`41b8583`（scripted 报告与第一阶段 `robust_042` 替换已推送）；状态：尚未提交。
- 准备做：处理 episode 23 的严重物理逃逸，同时保留 5 条局部纠正覆盖。
- 做了什么：三次 exact repeat 继续使用已通过的 `angle=0.65, x=0.0075, y=-0.01125`；原 `-0.025/+0.025 rad` 两条分别替换为 `x=0.006, y=-0.01125` 和 `x=0.0075, y=-0.009375`，角度均为稳定的 `0.65 rad`。测试改为精确断言五条坐标。
- 遇到的问题：修复源 x 后，`0.625 rad` 通过 IK，但方块在放置阶段从正常预放置位置逸出到 `z=-5.19 m`，最终到 `z=-320.54 m`；这是物理爆炸，不是普通失败，不能进入训练。`all_states_finite=true` 说明“仅检查 finite”不足以拦截这种大幅逃逸。
- 为什么做：重复不稳定角度或降低物理/安全门槛会生成错误专家标签；继续使用两个正交源位姿扰动更符合“源失败邻域纠正”的目的。
- 怎么解决：两个新探针均完整通过。`x=0.006` 的漂移/最终误差为 `0.011138/0.009195 m`；`y=-0.009375` 为 `0.007444/0.010343 m`，最大关节步长均约 `0.041 rad`。
- 后续改进：给 scripted expert 增加与闭环相同的 cube workspace envelope 运行时中止，避免物理爆炸仍跑到 episode 末尾；本轮先用严格任务结果排除该数据。
- 验证计划：运行 17 项计划测试、重建计划、重新验证确认集隔离，然后从 episode 23 恢复。
- 测试修正：首次回归保留了旧的“5 条 x 均为 0.0075”断言，与新加入的 `x=0.006` 邻域冲突。已删除过期断言，仍保留五条 `(x,y)` 的完整顺序精确比较，因此验证强度没有降低。

### v3-fc-wip.016：完成 30/30 纠正专家集并恢复中断占位目录

- Git 基线：`f6ab8e5`（稳定化 `robust_042` 纠正数据计划已推送）；状态：运行里程碑待提交。
- 准备做：先把 30 条失败纠正专家轨迹全部闭合，再运行健康汇总、36+30 来源门禁和 OpenPI 数据批次验证。
- 做了什么：从已验证的 28/30 状态恢复采集；保全并隔离中断留下的空 `episode_000028`，随后重采 episode 28、29。采集器跳过原有 28 条，只新增最后 2 条。
- 遇到的问题：第一次恢复被 fail-closed 检查拒绝，提示 `episode_000028` 不完整或属于其他 case。只读检查确认目录内为 0 个文件，没有 metadata、图像或动作，属于进程在建目录后中断留下的占位符。
- 为什么做：直接删除会丢失中断证据；忽略该目录会阻塞恢复；把空目录视为 episode 又会污染训练集数量和来源统计。
- 怎么解决：核对精确源路径与未占用的目标路径后，将空目录移动到 rejected 根并命名为 `episode_000028_interrupted_empty`，随后按同一冻结计划恢复。失败/中断证据保留，但不进入训练。
- 结果：30/30 条正式纠正 episode 全部通过，最后两条均为 569 帧、28.4 秒；episode 28 的最终位置误差/释放后漂移为 `0.005305/0.007827 m`，episode 29 为 `0.005213/0.010789 m`，均满足原始门槛。
- 下一步：运行 `prepare_rm65_failure_correction_v3.sh`；必须同时证明纠正汇总 30/30、合并总数 66、来源恰为旧训练 36 + 纠正 30、归一化统计成功且 OpenPI 批次可读，之后才允许训练 smoke。

### v3-fc-wip.017：通过 36+30 合并数据与 OpenPI 输入合同门禁

- Git 基线：`f6ab8e5`；状态：数据准备结果待提交。
- 准备做：在加载 v2 权重前证明 v3 数据不仅能转换，而且来源、归一化和模型输入张量均符合冻结合同。
- 做了什么：运行 `prepare_rm65_failure_correction_v3.sh`，依次完成 30 条纠正健康汇总、双源 LeRobot policy-window 转换、归一化统计计算和 OpenPI 单批次读取。
- 遇到的问题：没有新的数据错误；转换阶段逐 episode 编码耗时较长，归一化统计需遍历 337 个 batch。长进程保持在同一会话中监控，未并行启动训练占用 GPU。
- 为什么做：只检查 episode 目录数量不足以证明训练可用；还必须排除来源比例错误、旧 norm stats 误用、相机键/张量维度与 pi0.5 配置不一致等静默问题。
- 怎么解决：门禁逐层 fail-closed。健康汇总为 30/30、17,070 帧且计划覆盖无缺失/重复/错配；合并集为 66 个 episode，来源精确为旧训练 36 + 纠正 30；33,249 个源帧经 policy-window 得到 21,622 帧。
- 归一化结果：成功处理 21,568 帧，输出 `actions/state` 两组统计，SHA-256 为 `0cd9f8ca8bb6772f57062d3f9ea7cf1d1922e8cad4a9a65a2b9e4487335a45bb`。
- OpenPI 合同：三路相机均为 `[1,224,224,3]`，token 长度 64，输入状态填充为 `[1,32]`，动作 batch 为 `[1,10,32]`；RM65 填充前状态/动作维度均为 7。数据准备总门禁 `PASS`。
- 下一步：运行训练 preflight，确认 v2 初始权重、数据 repo、norm stats、10k/500 warmup/`5e-6→1e-6` 学习率与独立输出目录；通过后只跑 2-step smoke。

### v3-fc-wip.018：统一归一化统计的生成路径与训练读取路径

- Git 基线：`f6ab8e5`；状态：修复待验证。
- 准备做：修复训练 preflight 暴露的 normalization asset 路径合同错误，重新通过数据准备门禁后再尝试 smoke。
- 做了什么：`compute_rm65_norm_stats.py` 新增显式 `--assets-base-dir`，准备脚本固定传入实际 OpenPI 根的 `assets` 目录；最终准备门禁新增“报告路径等于训练读取路径、文件存在、SHA-256 一致”三项检查。
- 遇到的问题：首次训练 preflight 正确拒绝启动，因为统计报告指向项目内 `assets/pi05_rm65_lora/...`，而训练器把 `assets_base_dir` 设为 OpenPI 仓库的 `assets`，实际查找 `/home/chengyu/robot-learning/openpi/assets/pi05_rm65_lora/...`。
- 根因：统计脚本使用 TrainConfig 的相对默认 `assets_base_dir`，其解析结果依赖当前工作目录；训练脚本则显式覆盖到 OpenPI 根。两个入口各自都合理，但没有共享同一个显式路径参数。
- 为什么做：手工复制现有 `norm_stats.json` 虽能暂时通过，却无法保证重跑可复现，也可能让报告中的输出路径与实际训练资产不一致。
- 怎么解决：让生成端接收训练端的真实 assets root，并把路径与内容哈希纳入准备门禁。这样未来修改 `OPENPI_ROOT` 时两端仍由同一环境变量派生，不依赖运行目录。
- 验证计划：Python 编译、shell 语法、完整准备脚本重跑、训练 preflight；只有四项全部通过才进入 2-step smoke。

### v3-fc-wip.019：归一化路径修复与训练 preflight 通过

- Git 基线：`f6ab8e5`；状态：修复已验证，待与结果提交。
- 准备做：在独立 smoke 实验目录中实际加载 v2 权重和新数据，运行 2 个训练 step，验证反向传播与 checkpoint 保存。
- 做了什么：通过 Python 编译、shell 语法、状态 JSON 和 `git diff --check`；随后完整重跑数据准备并重跑训练 preflight。
- 结果：统计直接写入 `/home/chengyu/robot-learning/openpi/assets/pi05_rm65_lora/local/rm65_sim_failure_correction_v3_train/norm_stats.json`，报告路径与训练期望路径一致，SHA-256 仍为 `0cd9f8ca8bb6772f57062d3f9ea7cf1d1922e8cad4a9a65a2b9e4487335a45bb`。
- Preflight：v2 初始参数目录、新 66-episode 数据报告、OpenPI batch 报告、norm asset 文件及哈希全部通过；脚本明确返回 `TRAINING_NOT_STARTED=true`，因此该验证没有消耗正式训练步数。
- 为什么下一步只跑 2-step：preflight 只能验证静态合同，不能证明 JAX 模型、LoRA 参数、优化器和新数据能完成反向更新及序列化；先用独立实验名冒烟可避免 10k 正式目录出现半初始化状态。
- 下一步门禁：smoke 必须产出数值 checkpoint 和 `status=pass` 报告；失败则保留 smoke 诊断并修复，成功后才启动 `rm65_failure_correction_v3_lora_10k`。

### v3-fc-wip.020：2-step v3 增量训练 smoke 通过

- Git 基线：`f6ab8e5`；状态：smoke 结果待提交。
- 准备做：封存本轮代码、数据准备证据和 smoke 报告；确认 smoke 进程完全退出后启动独立目录的 10k 正式微调。
- 做了什么：从冻结 v2 `29999/params` 恢复约 6.4 GiB 参数，实际加载新 norm stats 与三相机 batch，完成 2 次 LoRA 训练更新并保存数值 checkpoint `rm65_failure_correction_v3_incremental_smoke/1`。
- 训练数值：step 0 的 `loss=0.0004, grad_norm=0.0424`；step 1 的 `loss=0.0198, grad_norm=0.9365`；参数范数均为 `1803.8978`。数值有限且没有 OOM、NaN 或梯度爆炸。
- 验证：smoke 报告为 `status=pass`、`num_train_steps=2`、`batch_size=1`；报告 JSON 可解析且 checkpoint 的 `params` 目录存在。训练和报告均声明 `real_robot_command_sent=false`。
- 遇到的问题：训练本身约 39 秒完成，但 Orbax 保存约 6.8 GiB 参数/训练状态用了约 125 秒；之后 Python 在 `folio_wait_bit_common` 等待页回写，观测到约 1.09 GiB swap，退出明显慢于计算。
- 为什么不能立即并行启动正式训练：smoke 主进程虽已生成报告，仍持有约数 GiB RSS/换出页；并行加载第二份模型会放大内存和 I/O 压力，也会触发脚本的单实例保护。
- 怎么解决：不强杀已完成进程，等待内核自然回收；正式训练只保留每 2,000 step 保存一次，避免 smoke 的每 step 保存开销代表常规吞吐。正式运行后依据无保存区间的实际 step rate 更新完成时间判断。
- 下一步：精确暂存并推送代码、日志和小型 JSON 报告，不提交数据集或 checkpoint；待进程退出后运行 `start`。

### v3-fc-wip.021：封存 smoke 版本并放行 10k 正式微调

- 上一工作版本提交：`a7c7b3d2ddf7b9be2fb4703af21288bb90ac34a6`（`Validate RM65 v3 correction training data`），已推送且本地/`origin/main` 指针一致。
- 准备做：启动 `rm65_failure_correction_v3_lora_10k`，先用无 checkpoint 保存区间的实际吞吐估计训练时长，再持续监控 loss、grad norm、GPU/RAM 和 checkpoint。
- 启动前门禁：没有残留 `train_rm65_pi05.py` 进程；正式输出目录不存在；根分区可用约 2.3 TiB；RAM 可用约 28 GiB、swap 仅 1.2 MiB；RTX 4080 SUPER 空闲，显存占用 140 MiB、温度 33°C。
- Git 边界：项目中仍有多份历史结果和 `scripts_sync_staging/` 未跟踪，它们不属于本轮提交，继续保持原样；本轮只提交了 9 个精确选择的代码、日志及小型证据文件，未提交数据集或 checkpoint。
- 为什么现在放行：30/30 纠正数据、36+30 来源、OpenPI batch、norm asset 路径/哈希、v2 恢复、两步前反向和 checkpoint 保存均已分别通过；不存在尚未解释的训练阻断项。
- 正式训练合同：10,000 step、batch size 1、从 v2 `29999/params` 初始化、warmup 500、峰值学习率 `5e-6`、余弦衰减到 `1e-6`、每 2,000 step 保存一次，独立实验目录且禁用真实机械臂命令。
- 下一步：启动后确认首批 loss/grad 有限并记录实际 step rate；只有正式报告和最终 `9999/params` 均存在，才进入离线验证与全新条件 run1。

### v3-fc-wip.022：10k 正式微调进入稳定计算区间

- Git 基线：`756cbe4`（正式训练启动门禁已推送）；状态：训练运行中。
- 做了什么：启动 `rm65_failure_correction_v3_lora_10k`，preflight 再次通过；训练器确认从冻结 v2 `29999/params` 恢复，并从 OpenPI assets 根加载哈希已核对的新 norm stats。
- 初始运行状态：JAX 编译后进度从 42/10,000 增长到 86/10,000，稳定吞吐约 `4.4 step/s`，纯计算剩余时间估计约 37 分钟；该估计不含每 2,000 step 的约 6.8 GiB checkpoint I/O。
- 资源采样：训练 PID 259194 为正常可中断睡眠/运行状态，RSS 约 6.6 GiB；系统可用 RAM 约 22 GiB，swap 仅 1.2 MiB；GPU 显存约 12,387/16,376 MiB、利用率 52%、60°C、约 258 W。
- 遇到的问题：CheckpointManager 初始化日志显示内部 `save_interval_steps=1`，表面上像每步保存。
- 怎么确认：检查 OpenPI `train.py`，真正的调用门禁是 `step % config.save_interval == 0` 或最后一步；本次 config 的 `save_interval=2000`，因此不会每步写 6.8 GiB。内部 manager 的 1 只是允许每次显式 save 调用生效。
- 下一步：持续监控到 step 2,000，确认首个 checkpoint 原子提交；同时观察进度恢复后实际吞吐和是否出现 NaN/OOM。完成 9,999 后核验正式 PASS 报告与最终 params。

### v3-fc-wip.023：首个正式 checkpoint 原子提交并恢复训练

- Git 基线：`e48994e`（正式训练运行记录已推送）；状态：训练运行中，本条待后续同步。
- 做了什么：持续读取逐 step 指标至 step 2,000；确认 checkpoint 进入临时目录、写入 params/train_state/assets、完成跨处理器验证并原子重命名为正式 `2000` 目录。
- 训练健康：step 0–2,000 可见 loss/grad norm 全部有限；warmup 后参数范数缓慢从 `1803.8978` 到约 `1803.8989`，没有 NaN、OOM 或突然跳变。checkpoint 完成后训练已恢复至至少 step 2,130，指标仍有限。
- Checkpoint 性能：主线程阻塞传输 6.87 秒；6.4 GiB params 加约 397.9 MiB train state 的异步完整保存耗时 107.83 秒；Orbax 报告 `No errors found in background save thread` 并完成原子提交。
- 遇到的问题：尝试另开只读 SSH 连接检查目录时，Tailscale 要求额外网页登录认证；当前已经认证且承载训练的长连接仍正常，不影响计算与保存。
- 怎么处理：不中断主训练连接，不为并行状态查询冒险重启；继续通过该连接的训练日志验证 4,000/6,000/8,000/9,999 里程碑。若主连接意外断开，再把 Tailscale 认证作为明确外部阻断处理。
- 下一步：继续到 step 4,000；检查第二次保存是否自动清理/替换旧 checkpoint，避免磁盘无界增长，并继续审计有限数值。

### v3-fc-wip.024：第二个 checkpoint 通过并暴露单恢复点风险

- Git 基线：`e48994e`；状态：训练运行中，本条待 Tailscale 新连接恢复后同步。
- 做了什么：监控 step 2,000–4,000 的连续训练及第二次 checkpoint；step 4,000 前 loss/grad norm 持续有限，参数范数约 `1803.9000`。
- 结果：step 4,000 checkpoint 的主线程阻塞传输约 4.14 秒，后台写盘约 1 分钟后完成 params/train_state/assets 验证和原子目录提交；训练同时继续并至少到 step 4,207，指标正常。
- 遇到的问题：`max_to_keep=1` 使 CheckpointManager 在 4,000 临时目录尚未原子提交时开始删除旧 2,000 checkpoint。正常运行可控制磁盘，但断电窗口内可能暂时没有完整恢复点。
- 为什么本轮不改：当前 TrainConfig 已在进程内冻结，修改磁盘脚本不会影响正在运行的 manager；中断重启只为改变保留数反而制造更大风险。
- 后续怎么改：下一次正式训练把 checkpoint 保留数显式设为至少 2，并加测试/日志断言；本轮继续紧盯每次原子提交，不把临时目录当成可恢复 checkpoint。
- 下一步：继续至 step 6,000 并确认第三次原子提交；完成前不启动评测或第二训练进程。

### v3-fc-wip.025：step 6,000 checkpoint 通过，训练进入后 40%

- Git 基线：`e48994e`；状态：训练运行中，本条待同步。
- 做了什么：继续监控 step 4,000–6,000 的全部进度和抽样逐步指标；确认 step 6,000 checkpoint 的临时写入、handler commit、数组元数据验证及原子重命名。
- 训练健康：step 6,000 前 loss/grad norm 仍全部有限，参数范数约 `1803.9009`；checkpoint 后至少恢复至 step 6,172，吞吐重新达到约 4.4 step/s。
- Checkpoint 性能：主线程阻塞约 1.22 秒，后台写完约 6.8 GiB 数据约 53–54 秒，较 step 2,000 的 107.83 秒明显改善；保存期间训练短暂降到 1–3 step/s，完成后恢复。
- 下一步：继续至 step 8,000 并完成倒数第二个周期 checkpoint；然后只剩最终 9,999 保存与 PASS 报告。

### v3-fc-wip.026：step 8,000 checkpoint 通过，进入最终训练区间

- Git 基线：`e48994e`；状态：训练运行中，本条待同步。
- 做了什么：监控 step 6,000–8,000；确认一次约 74 秒的 checkpoint 后延迟页回写停顿会自行恢复，随后完成 step 8,000 checkpoint 全流程。
- 训练健康：8,000 前逐步 loss/grad norm 均有限；参数范数约 `1803.9014`。checkpoint 后训练已恢复到至少 step 8,210，吞吐约 4.4 step/s。
- Checkpoint 结果：step 8,000 异步完整保存耗时 54.56 秒，params/train_state/assets 原子提交完成且后台无错误；旧 step 6,000 删除完成。
- 遇到的问题：step 6,890 附近出现约 74 秒无 checkpoint 进度停顿，随后恢复到 4.5 step/s；结合主机曾出现的 `folio_wait_bit_common`，判断为大 checkpoint 后延迟页回写/内存回收，而非数值或 GPU 故障。
- 后续优化：除了保留两个 checkpoint，还应评估只保存可训练 LoRA/optimizer 子树或降低完整 checkpoint 频率，减少每次约 6.8 GiB 写盘和后续页回写抖动；任何格式变化都必须先验证 OpenPI restore 兼容性。
- 下一步：完成剩余约 1,790 step，核验最终 `9999/params` 与正式 PASS 报告；训练进程完全退出前不启动模型加载评测。

### v3-fc-wip.027：10k 正式纠正微调完成并通过产物门禁

- Git 基线：`e48994e`；状态：训练已完成，本条与正式训练报告待同步提交。
- 准备做：把最终 checkpoint 与结构化报告封存为可审计证据；随后按冻结顺序运行评测 preflight、offline 和全新条件 run1，不把训练集/旧评测集结果冒充最终成绩。
- 做了什么：持续监控至 step 9,999，等待最终完整 checkpoint 原子提交、正式报告生成和训练进程自然退出；没有并行启动模型加载或仿真评测。
- 最终训练数值：step 9,999 的 `loss=0.0018`、`grad_norm=0.1399`、`param_norm=1803.9016`，均为有限值；10,000 步计算用时约 42 分 55 秒。
- Checkpoint 结果：最终约 6.8 GiB 完整 checkpoint 用时 52.20 秒完成后台保存和原子提交，最终参数目录为 `outputs/openpi_checkpoints/pi05_rm65_lora/rm65_failure_correction_v3_lora_10k/9999/params`；训练进程清理后以 exit code 0 退出。
- 报告门禁：`results/pi05_rm65_failure_correction_v3_10k.json` 为 `status=pass`，并记录 `num_train_steps=10000`、`batch_size=1`、warmup 500、峰值学习率 `5e-6`、衰减到 `1e-6`、最终 checkpoint `/9999`。
- 安全边界：本阶段只有仿真训练与文件读写，`simulation_only=true`、`real_robot_command_sent=false`，没有连接或控制真实 RM65-B。
- 遇到的问题：完整保存仍产生 52–108 秒 I/O 开销及偶发页回写停顿；`max_to_keep=1` 还会在新临时 checkpoint 提交前删除上一恢复点，存在单恢复点风险。
- 后续优化：未来正式训练默认至少保留 2 个完整 checkpoint；是否改成 LoRA/optimizer 子树保存，必须先用独立 smoke 验证 OpenPI 恢复兼容性，不能直接改变当前可恢复格式。
- 下一步：先只读核验正式 JSON 和 `9999/params`，精确提交小型报告与日志；之后执行 `evaluate_rm65_pi05_failure_correction_v3.sh preflight`、`offline`、`run1`。只有全新 20 条达到至少 18/20，且三次重复的一致率至少 95%、翻转不超过 1 条，才允许宣称通过最终确认门禁。

### v3-fc-wip.028：把物理条件纳入正式评测断点复用合同

- Git 基线：`e48994e`；状态：本地修复待远端测试与提交。
- 准备做：在运行全新条件 run1 前静态审计断点续跑和三次重复分析，排除错误复用旧报告的可能性。
- 遇到的问题：`load_existing_report` 已核对 checkpoint、控制阈值、策略种子和仿真种子，但没有核对 prompt、转移角和源 `(x,y)` 偏移；若计划文件意外漂移而 case id/种子不变，同名目录中的旧报告可能被复用。重复性分析也没有独立检查这三项物理条件。
- 为什么做：正式确认集禁止选择性重试，但也不能把不同物理条件的报告当成同一试验。只冻结种子不足以完整定义一个评测 case。
- 怎么解决：任务报告在正常结束和 IK 预检失败两条路径都显式保存 `prompt`、`transfer_joint_1_rad`、`source_offset_xy_m`；suite 恢复门禁要求状态为 pass/fail、仿真-only、未发真机指令，并逐值匹配这三个条件；三次重复矩阵也把它们列为每份报告的有效性检查。
- 测试：扩展断点恢复测试，分别扰动 prompt、角度、x、y 并要求拒绝；扩展预检报告与重复矩阵测试，确保正常/失败报告都具备完整条件来源。
- 安全边界：不改变冻结的 20 条条件、checkpoint、动作控制、门槛或随机种子，仅增强证据身份校验；仍为仿真-only。
- 下一步：认证恢复后先在远端运行 Python 编译与三组回归测试，再同步正式训练证据并开始 staged evaluation。

### v3-fc-wip.029：把正式训练与确认计划完整合同纳入评测 preflight

- Git 基线：`e48994e`；状态：本地静态验证完成，待远端动态 preflight。
- 准备做：继续审计 `evaluate_rm65_pi05_failure_correction_v3.sh preflight`，确保它验证的不只是“有 checkpoint 和 20 条 case”，而是训练、归一化资产和预注册门槛的完整冻结合同。
- 遇到的问题：原 preflight 只检查训练报告 PASS、checkpoint id/repo id、20 条 case、90% 成功率、3 次重复和 95% 一致率；没有拒绝训练超参数漂移、norm asset 路径/内容漂移、确认计划验证报告失败、最大翻转数或控制器阈值变化。
- 为什么做：正式 run1 一旦开始，其失败不能选择性重试。应在加载模型和创建第一个评测目录前，尽可能把可静态发现的配置错误全部 fail-closed。
- 怎么解决：新增精确训练合同（config、实验名、10k、batch 1、warmup 500、`5e-6→1e-6`、simulation-only）、norm report/路径/SHA-256、确认计划验证报告全部 checks、首次独立确认语义、正常失败禁止重试、20/20 与 18/20 门槛、60 份报告、95% 一致率、最多 1 条翻转，以及冻结的控制阈值和哈希要求。
- 验证：脚本结构保持先取得并核对最终 checkpoint，再执行静态合同门禁；本地将运行 shell 语法检查和差异检查，动态资产校验必须在 Tailscale 认证恢复后于远端执行。
- 安全边界：只增强启动前只读校验，不改模型、计划内容、控制动作或结果判定，也不会触发真实机械臂。
- 下一步：远端执行新增 preflight；任何一项漂移都停止，不创建 run1 数据目录。全部 PASS 后再做 offline inference。

### v3-fc-wip.030：远端回归与完整评测 preflight 通过

- Git 基线：`e48994e`；状态：代码与正式训练证据准备提交。
- 准备做：先封存正式 10k 报告、评测来源加固和 preflight 结果，再加载 5.4 GiB 最终 checkpoint 做离线推理；不让尚未提交的代码与长时间评测混在同一不可追溯状态。
- 做了什么：SSH 认证恢复后，只读核验正式训练报告 JSON、`rm65_failure_correction_v3_lora_10k/9999/params` 目录及 checkpoint 总体积约 5.4 GiB；同步 v3-fc-wip.028/.029 代码和日志到远端。
- 回归结果：7 个相关 Python 文件编译通过；断点恢复 28 项、闭环任务报告回归、三次重复矩阵测试全部 PASS；评测 shell 语法、状态/训练 JSON 解析和 `git diff --check` 均通过。
- 动态 preflight：`evaluate_rm65_pi05_failure_correction_v3.sh preflight` 返回 `RM65_FAILURE_CORRECTION_V3_EVALUATION_PREFLIGHT=PASS`。这同时证明训练合同、最终 checkpoint id、norm asset 路径/SHA、20 条预注册计划验证、18/20 成功门槛、60 份重复报告、95% 一致率、最多 1 条翻转和控制阈值均未漂移。
- 遇到的问题：此前 Tailscale 要求额外网页登录，导致新 SSH 会话阻断数小时；认证恢复后无需接触或保存用户密码即可重新连接。
- 怎么解决：把认证保留为用户亲自完成的一次性安全步骤；连接恢复后重新从只读产物检查开始，没有假定等待期间远端状态不变。
- Git 边界：只提交 8 个代码/测试文件、2 个日志文件和正式训练小型 JSON；不暂存数据集、checkpoint、缓存或其他历史未跟踪结果。
- 安全边界：所有检查均为仿真、文件和模型合同验证，`real_robot_command_sent=false`。
- 下一步：运行 `offline`，要求单观测推理与 held-out imitation 全部生成有限、形状正确的动作；offline 只能证明模型可加载和推理，不能替代全新条件闭环 run1。

### v3-fc-wip.031：最终 checkpoint 离线推理与 held-out imitation 通过

- Git 基线：`79e66ce`（训练完成与评测来源加固已推送）；状态：offline 证据准备提交。
- 准备做：在启动 Isaac Sim 全新条件 run1 前，实际加载最终 `9999` checkpoint，验证单帧推理、动作形状/有限性、安全 guard 和 held-out validation policy-window 误差。
- 单帧结果：checkpoint 首次加载 `17.59 s`、首次推理 `10.97 s`，动作形状 `[10,7]` 且全部有限；关节限位和步长裁剪均为 0，夹爪范围裁剪 1 次，最大输出关节步长 `0.00875 rad`。
- Held-out 结果：9 个 validation episode × 5 帧，共 45 个样本全部完成并返回 PASS；首次 JAX 推理 `9.59 s`，含编译后的平均推理 `0.310 s`，p95 `0.100 s`。
- 误差：horizon arm MAE `0.00560 rad`、p95 `0.02060 rad`；gripper MAE `0.00615`、p95 `0.00809`；首动作手臂平均 L2 `0.01214 rad`、最大 `0.08006 rad`。
- 安全 guard：45×10 个预测动作中累计 53 次关节步长裁剪和 173 次夹爪范围裁剪，无关节限位裁剪。offline PASS 只证明安全整形可用和输出数值健康；较多 gripper clamp 必须在闭环 run1 中观察是否影响释放时序。
- 语义边界：`simulation_action_executed=false`、`real_robot_command_sent=false`、`task_success_claimed=false`。离线模仿误差不等于任务成功率，不能用来提前宣称部署完成。
- 遇到的问题：首次下载证据时把脚本实际的 `rm65_pi05_...` 文件名前缀误写为 `pi05_rm65_...`，scp 因源文件不存在而失败；核对评测脚本变量后用正确文件名下载，没有改动或丢失远端结果。
- 下一步：提交两个小型 offline JSON 和本条日志，然后启动冻结 20 条计划的 run1。run1 正常模型失败不得重试；只有缺少有效 task report 的基础设施失败可按脚本最多重试一次。

### v3-fc-wip.032：中止错误重试并修复正式报告来源合同

- Git 基线：`775ea82`（offline 证据已推送）；状态：run1 已中止，修复与首结果恢复待验证。
- 准备做：启动 20 条全新条件 run1，确保正常模型失败原样计入、只有真正缺失有效报告时才允许一次基础设施重试。
- 首次正式结果：`confirm_v3_000` 第一次执行生成了完整 task report，模型结果为 FAIL；主要失败项为最终目标误差、最终夹爪未保持打开，仿真状态有限且未触发安全中止。该失败必须作为正式 outcome 保留。
- 遇到的问题一：pi0.5 正常完成路径的 task report 没有 `transfer_joint_1_rad` 和 `source_offset_xy_m`；v3-fc-wip.028 只把字段加入了 IK 预检失败路径。suite 因此把有效 FAIL 错判为 missing report，并运行了唯一一次 infrastructure retry。
- 后果：错误重试得到 PASS 并覆盖同目录 task report/episode 文件；该 PASS 违反“正常模型失败不得重试”，必须完整隔离且永不进入正式统计。suite 随后开始 case 1，已在其生成有效报告前中止；所有策略/Isaac Sim 进程均已退出。
- 遇到的问题二：`_deterministic_sampling_valid` 要求 observation hash 键恰好等于四个图像/关节字段，但运行时已合法增加 cube、tool 和 camera pose 物理状态哈希，导致正常报告的 sampling 校验恒为 false。
- 怎么解决代码：在 pi0.5 正常报告路径写入冻结物理条件；哈希验证改为“四个必需键必须为子集，且所有附加键也必须是合法 SHA-256”；测试加入物理状态扩展哈希并保持验证 PASS。
- 怎么恢复证据：新增 fail-closed 恢复工具，只允许从首次 `runner.log` 中 `RM65_PI05_CLOSED_LOOP` 标记前提取原始 FAIL；核对 checkpoint、双种子、prompt 和冻结计划，记录 runner log/原报告 SHA，只补入缺失的角度/偏移字段且声明 `outcome_changed=false`。原 episode 已被错误重试覆盖的限制会显式写入报告。
- 数据处置：包含第二次 PASS 和被覆盖 episode 的整个目录将移动到独立 excluded-retry 根；case 1 的无报告中断目录也移动保留。正式 run1 目录重建 case 0 的恢复 FAIL，并从 case 1 继续。
- 监控脚本问题：首次状态查询因 PowerShell 先解释远端 `$()` 和 `/dev/null` 而出现本地路径错误，未影响仿真；后续改用单引号包裹远端命令。
- 安全边界：无真实机械臂命令；中止是为了防止污染正式统计，不改变模型、计划、seed 或成功门槛。
- 下一步：远端编译和回归通过后，隔离错误重试、恢复首个 FAIL、验证 suite 会复用该 FAIL 而不再运行 case 0，然后从 case 1 恢复。

### v3-fc-wip.033：首个正式 FAIL 已恢复，错误重试 PASS 已隔离

- Git 基线：`775ea82`；状态：修复与恢复已验证，准备提交后恢复 run1。
- 远端验证：相关 Python 编译、闭环报告回归、28 项 resume 合同和 9 项恢复工具测试全部 PASS；`git diff --check` 通过。
- 正式 case 0：从首次 `runner.log` 恢复的 outcome 为 FAIL，执行满 120 chunks；方块抬升 `0.04421 m`，最终 XY/三维目标误差均约 `0.06355 m`，释放后漂移 `0.0 m`，最终夹爪归一化值 `0.52718`，无仿真安全中止。它将作为 run1 的第 1 个失败计入 20 条成功率。
- 恢复完整性：runner log SHA-256 为 `07706014de510e45da6b04a3219b2650e3d2a9e85457831bed7422d7d1561831`；提取的原始 report SHA-256 为 `5c4488a1a500c597598f4d80958be13343a2171bcb20ba8af0ae345b0fd309c3`。只从冻结 plan 补入角度和源偏移，`outcome_changed=false`。
- 数据隔离：错误第二次 PASS 及其覆盖后的 episode 文件完整移动到 `datasets/rm65_pi05_failure_correction_v3_confirmation_run1_excluded/confirm_v3_000_invalid_retry_attempt_2`；case 1 的中断且无报告目录移动为 `confirm_v3_001_interrupted_no_report`。没有删除任何证据。
- 恢复门禁：suite 的 `load_existing_report` 已实际接受正式恢复 FAIL；正式 run1 根只有这一个 task report，excluded 根只有错误重试 PASS，二者不会混淆。
- 限制：首次 FAIL 对应的 episode 文件被错误重试覆盖，已无法恢复；报告和全部 chunk 哈希仍完整保存在首次 runner log 中。该限制显式写入 `formal_outcome_recovery`，不能声称首 episode 文件仍可复现。
- 下一步：精确提交/推送 5 个代码测试文件与日志，不提交 run 数据；重新启动 run1 时 case 0 必须显示 `reuse fail`，case 1 才允许重新执行。

### v3-fc-wip.034：全新条件 run1 完成，17/20 未通过 90% 门槛

- Git 基线：`dd084c3`（报告修复与首失败恢复已推送）；状态：run1 结果与失败分析准备提交。
- 恢复验证：重新启动后明确输出 `confirm_v3_000: reuse fail`，没有再次执行首条件；case 1 从无报告中断状态重新运行。case 1–19 均一次生成合同有效报告，没有额外 infrastructure retry。
- 正式结果：20/20 报告齐全，17 PASS、3 FAIL，成功率 `0.85`；episode 数和全部报告门禁通过，最低成功率 `0.90` 未通过，因此 run1 总状态为 FAIL。95% Wilson 区间为 `[0.6396, 0.9476]`。
- 失败条件：`confirm_v3_000` 位于 `0.6625 rad, (-0.009,-0.002) m`；`confirm_v3_015`、`016` 均位于最高角度 `0.9125 rad`，源偏移分别为 `(-0.009,-0.002)` 和 `(-0.004,0.009) m`。
- 共同失败模式：三条均为 `target_xy_error + target_position_error + release_not_verified`。最终位置误差分别约 `0.06355/0.07955/0.05985 m`；高角度两条抬升仅 `0.02151/0.02031 m`，接近 `>0.02 m` 门槛。
- 释放诊断：三条都曾执行 `gripper target=0` 且观测到最小实际夹爪约 `0.040–0.042`，但没有连续两个 chunk 满足完整释放候选；episode 末夹爪又回到 `0.527/0.895/0.871`。这说明问题不是“策略从未发出打开命令”，而是释放状态没有稳定保持，同时位置误差仍超 5 cm。
- 分组结果：`0.7375` 和 `0.8125 rad` 均 5/5；`0.6625 rad` 为 4/5；`0.9125 rad` 为 3/5。两个 prompt 为 4/4，另外三个各 3/4；样本小，prompt 差异不能独立归因。
- 证据策略：不提交 4.7 MiB、内嵌完整 task reports 的 full summary；提交 21 KiB compact summary 和 24 KiB failure taxonomy。原始 task reports、图像和 run 数据保留远端但不进入 Git。
- 结论边界：v3 checkpoint 已证明可加载、可离线推理并在新条件达到 85%，但没有通过部署门禁，不能宣称“仿真部署完成”。run2/run3 只能度量相同条件的 outcome 稳定性，不能把 17/20 改写为更多独立试验。
- 后续数据治理：如果把这三条失败用于下一轮纠正训练，则本 run1 的 20 条条件全部永久降级为开发/纠正集；v4 最终成绩必须重新预注册另一组从未训练、从未调参的新条件。
- 下一步：先提交紧凑证据；继续 run2/run3 获得稳定性矩阵。随后根据重复结果区分“固定高角度/释放缺陷”与“RTX 渲染触发的 outcome flip”，再设计 v4 纠正集和全新确认计划。

### v3-fc-wip.035：同计划 repeatability run2 完成，18/20 且出现 1 条翻转

- Git 基线：`f74f877`（run1 紧凑证据与失败分析已推送）；状态：run2 紧凑证据准备提交。
- 准备做：在完全相同的 20 条冻结物理条件、checkpoint、双种子、prompt 和控制阈值下执行第二次 RTX 闭环渲染，只衡量 outcome 稳定性，不把它当成新的独立成功试验。
- 结果：20/20 报告齐全，18 PASS、2 FAIL，单次成功率 `0.90`，刚好达到该 run 自身的 90% 门槛；95% Wilson 区间为 `[0.6990, 0.9721]`。这不改变 run1 的正式 17/20 FAIL，也不能据此宣称 v3 已通过部署门禁。
- outcome 变化：`confirm_v3_000` 从 run1 的 FAIL 翻转为 run2 的 PASS；`confirm_v3_015` 和 `confirm_v3_016` 连续两次 FAIL。当前已出现 1 条翻转，正好占满预注册的“最多 1 条 outcome flip”预算，run3 任何新增翻转都会使重复性门禁失败。
- 稳定失败：两条均位于最高角度 `0.9125 rad`。case 15 的最终位置误差约 `0.04834 m`，但仍未连续两个 chunk 验证释放；case 16 抬升仅 `0.01808 m`，并同时触发抬升不足、目标 XY/三维误差和释放未验证，最终位置误差约 `0.07682 m`。
- 释放诊断：两条都执行过 `gripper target=0`，也分别看到最小实际夹爪约 `0.0393/0.0425`，但未稳定保持两个连续 chunk；episode 末又回到 `0.610/0.893`。这进一步支持“释放保持/时序不稳定”而非“从未发出打开命令”。
- 分组结果：`0.9125 rad` 仍为 3/5，其他三个角度均为 5/5。run2 失败 taxonomy 为 `release_not_verified=2`、`insufficient_lift=1`、目标位置/XY 误差各 1。
- 证据策略：提交约 21 KiB compact summary 和 23 KiB failure analysis；不提交内嵌完整报告的大型 summary、episode 图像、数据集或 checkpoint。
- 安全边界：全程仅执行 Isaac Lab 仿真，`real_robot_command_sent=false`；没有覆盖 v2/v3 checkpoint。
- 下一步：提交并推送 run2 小型证据，然后执行相同计划的 run3；三次全部完成后运行 `analyze`，要求 60/60 报告有效、状态一致率至少 95%、翻转 case 不超过 1 条。之后才能据重复性结果设计 v4 定向纠正集和全新预注册确认计划。

### v3-fc-wip.036：建立数据集与 checkpoint 的跨机器保存合同

- Git 基线：`9e2b7e1`（run2 紧凑证据已推送）；状态：保存工具与资产范围准备提交，run3 同时继续执行。
- 准备做：解决“原始数据不应进入普通 Git，但只留在远端单盘又无法抗误删/磁盘故障”的恢复风险；在不干扰正在写入的 run3 前提下，先冻结 v3 核心资产范围和跨机器校验算法。
- 资产盘点：基础专家数据约 `2.0 GiB`、失败纠正专家数据约 `1.7 GiB`、66 episode LeRobot 转换数据约 `2.0 GiB`；v2 起始 checkpoint 与 v3 最终 checkpoint 各约 `5.4 GiB`。run1/run2 原始评测分别约 `716/776 MiB`，run3 尚在写入，因此不能提前生成最终哈希。
- 做了什么：新增 `build_data_preservation_manifest.py`，逐文件计算 SHA-256，再按相对路径、字节数和文件摘要生成紧凑 tree hash；新增跨目录复制一致、单文件内容变化必失败的回归测试。
- 冻结范围：新增 v3 preservation spec，纳入两份原始训练集、转换数据、v2/v3 checkpoint、norm stats 和 run1/run2/run3 原始评测。每项同时声明优先级、可重建性、源路径和备份相对路径。
- 文档合同：明确 Git 只保存代码、配置、日志和紧凑 manifest；原始数据/checkpoint 至少保留两份且第二份必须与源 manifest 比较为 PASS。文件数相同不等于备份有效。
- 遇到的问题：现有 `hash_asset_tree.py` 会输出逐文件清单，数 GB 数据可能产生不适合 Git 的大型 JSON；而只记录目录大小又不能检测同大小内容损坏。
- 怎么解决：新工具保留逐文件内容校验强度，但最终 JSON 每个资产只写文件数、总字节数和一个聚合 tree hash，避免把海量文件表提交 Git。
- 验证：Python 编译、JSON 解析、`git diff --check` 和“相同副本 PASS/修改一个文件 FAIL”回归均通过。正式源 manifest 必须等 run3 完成并停止写入后再生成。
- 安全边界：该更新只读取文件并计算哈希，不触发仿真动作或真实机械臂；不会覆盖 v2/v3 checkpoint，也不会把数据集/checkpoint 暂存进 Git。
- 下一步：同步并提交保存工具；run3 完成后生成源 manifest，再把约 19 GiB v3 核心资产复制到独立本地备份根并逐项对照验证。

### v3-fc-wip.037：run3 与冻结 20×3 重复性门禁通过，但 v3 正式成功率仍失败

- Git 基线：`8e763a5`（数据保存合同与工具已推送）；状态：run3/重复性小型证据准备提交。
- run3 结果：20/20 报告齐全，18 PASS、2 FAIL，成功率 `0.90`；只失败 `confirm_v3_015/016`，均位于 `0.9125 rad`。case 15 最终位置误差约 `0.07410 m`；case 16 最终位置误差约 `0.09781 m`，并出现位移不足；两条都未连续两个 chunk 验证释放。
- 三次矩阵：60/60 报告有效；17 条为 `PASS/PASS/PASS`，2 条为 `FAIL/FAIL/FAIL`，case 0 为 `FAIL/PASS/PASS`。状态一致 19/20=`95%`，outcome flip 1 条，刚好满足预注册下限 `95%` 和上限 1 条，因此 repeatability gate 为 PASS。
- 稳定失败：case 15/16 连续三次失败，说明最高角度下的目标定位与释放保持是可重复缺陷；它们应成为 v4 纠正集核心，而不是用重复运行稀释失败。
- 渲染敏感：case 0 三次初始关节、夹爪、方块/工具/相机物理状态和 policy noise 哈希都一致，但外部/腕部图像与首动作哈希不一致，且 outcome 翻转。这支持 RTX 渲染差异沿视觉策略传播到动作，而非物理初始条件或采样 seed 漂移。
- 结论边界：重复性门禁通过只说明同计划结果达到预注册稳定性要求；首次独立 run1 仍为 17/20=`85%`，没有达到 90% 正式成功率。因此 v3 仍不能宣称仿真部署完成，run2/run3 不能重算成新的独立成功试验。
- 证据策略：提交 run3 compact summary、failure analysis 和约束后的 20×3 matrix；大型 full summary 与全部 episode/图像继续保留在远端数据目录，不进入 Git。
- 安全边界：全部 60 次为 Isaac Lab 仿真，矩阵确认 `real_robot_command_sent=false`；没有覆盖 v2/v3 checkpoint。
- 下一步：先提交紧凑证据；run3 已停止写入，可以生成九项 v3 核心资产的源 manifest，随后建立第二份副本并逐项比对。备份完成后再冻结 v4 纠正与全新确认计划。

### v3-fc-wip.038：v3 九项核心资产源清单完成，第二副本传输开始

- Git 基线：`b3ef34a`（run3 与 20×3 重复性证据已推送）；状态：源 manifest 完成，独立本机副本尚未完成验证。
- 准备做：在 run3 停止写入后，为两份原始训练集、LeRobot 转换数据、v2/v3 checkpoint、norm stats 和三次正式评测原始数据生成不可变源清单，然后复制到另一台机器。
- 源清单结果：9/9 资产存在，合计 `19,561,366,749` bytes；逐文件读取后生成每项 compact tree SHA-256。源清单本身适合提交 Git，原始文件仍不进入 Git。
- 打包结果：约 13 万个小文件直接逐个 SSH 复制开销过大，因此在远端独立 staging 生成 9 个不压缩 tar；归档合计约 19 GiB，并为每个 tar 生成单独 SHA-256。源目录没有符号链接，解包后可以用相同相对路径 tree hash 核对。
- 遇到的问题：首次用 OpenSSH 默认 SFTP 递归复制时，本机目标文件长时间显示 0 bytes，实际只断续写入约 271 MiB 后停滞；该文件绝不计为有效备份。
- 怎么解决：中止停滞会话，先用两个小文件验证 legacy SCP（`-O`）路径可用，再改为逐个归档复制。每个归档完成后立即核对 SHA-256；中断时只重传当前归档，不影响已验证项。
- 当前进度：本机备份根为 `RM65_DATA_BACKUP_DO_NOT_GIT/v3_core_2026_09_29`，不属于远端 Git 提交内容；首个大归档仍在传输，尚未宣称第二副本有效。
- 安全边界：源数据和 v2/v3 checkpoint 只读；远端 staging 新增 tar 但不覆盖源文件；没有执行真实机械臂命令。
- 下一步：完成 9 个归档传输、归档 SHA 校验、解包和 9 项 tree-hash 比较；只有全部 PASS 后才把第二副本状态写为 verified。

### v4-fc-wip.039：按 20×3 证据生成 v4 纠正集与全新确认计划

- Git 基线：`742122b`（v3 源资产 manifest 已推送）；状态：v4 计划本地生成/回归通过，待远端验证提交；v3 第二副本仍在传输。
- 准备做：把 run1–run3 证据转成明确训练纠正，而不是再堆普通 ColorJitter；同时在 v4 数据采集和训练前冻结一组全新的 held-out 条件，防止调参后挑选评测集。
- 自动选择规则：从 20×3 matrix 选择所有非 `PASS/PASS/PASS` 条件，得到渲染敏感的 `confirm_v3_000`（`FAIL/PASS/PASS`）和稳定失败的 `015/016`（均 `FAIL/FAIL/FAIL`）。规则不靠手工挑结果。
- v4 纠正计划：每个源条件取 `-0.0125/0/+0.0125 rad` 三个物理角度，共 9 个物理组；每组采集 4 个 RTX 重复，总计 36 条 scripted-expert 训练 episode。每组四条共享一个显式 simulation seed，确保方块、机械臂和相机物理初态一致，同时保留独立 RTX 渲染带来的视觉差异。
- 采集链更新：`run_recorded_expert_demo.sh` 新增可选 simulation seed；collection runner 只在计划声明时传入，并把 physical group、render index、seed 和来源 outcome pattern 写入 metadata。旧计划未声明 seed 时命令保持兼容。
- 数据治理：v3 的 20 条正式确认条件全部永久标记为 development-only，禁止再次用作独立最终成绩；v4 纠正训练只实际选取其中三条非稳定成功条件及邻域。
- v4 全新确认：训练前预注册 20 条条件，角度为 `0.6875/0.7625/0.8375/0.9625 rad`，配 5 个新 offset、5 个均衡 prompt 和全新双种子；与 45 条基础计划、30 条 v3 纠正计划、36 条 v4 纠正计划以及旧 20 条确认条件均不重合，确认角度也从全部训练角度中 held out。
- 冻结训练/评测合同：目标 checkpoint 为 `rm65_failure_correction_v4_lora_6k/5999`，repo 为 `local/rm65_sim_failure_correction_v4_train`；首次 20 条需至少 18/20，后两次只作重复性证据，仍要求 60/60 报告、95% 一致率、最多 1 条翻转。
- 验证：Python 编译、旧 expert plan 兼容/seed 命令回归、v4 生成器测试、36 条纠正计划全部结构门禁和 20 条确认隔离门禁均 PASS。本机 Bash 入口不可用，因此 shell `bash -n` 必须在远端补做后才提交。
- 安全边界：本步只生成代码和计划，不启动训练、仿真采集或真实机械臂；不修改 v2/v3 checkpoint。
- 下一步：远端执行 shell/Python 回归并精确提交；先完成和验证 v3 独立备份，再开始 v4 36 条 expert collection，并对每个 physical group 核对相同 seed/物理状态与不同 RTX 图像。

### v4-fc-wip.040：v3 核心数据第二副本完成并通过两层校验

- Git 基线：`a2167ed`（v4 纠正与全新确认计划已推送）；状态：第二副本 gate PASS，v4 数据采集门禁解除。
- 归档传输：9 个 tar 全部复制到本机独立目录，逐项 SHA-256 与远端 `archives.sha256` 一致。首次默认 SFTP 的不完整文件已被 legacy SCP 的完整文件覆盖，没有把部分文件计入成功。
- 解包验证：九项全部解包后，重新逐文件计算相对路径、字节数和文件 SHA-256 聚合 tree hash；`inventory_status=pass`、`comparison_status=pass`，9/9 与源端一致，总字节数精确为 `19,561,366,749`。
- 副本位置：本机 `RM65_DATA_BACKUP_DO_NOT_GIT/v3_core_2026_09_29` 保存结构化恢复副本、原始归档、源 manifest、backup manifest 和 gate 报告；该目录不加入 Git。远端源数据和 staging 暂时保留，未执行删除。
- 新增 gate：backup manifest 现在记录源 manifest SHA-256；`check_rm65_v3_backup_gate.py` 要求固定 9 个资产、固定总字节数、全部 `matches_reference=true`、源 manifest hash 一致和仿真来源声明。通过后 `verified_copy_count=2`，任一项损坏则回退为 1。
- 最终 gate：`status=pass`，源 manifest SHA-256 为 `03ad9c2ebeecd8f2e651555c799f026d29c5d80de24defae4b4627a6059febf8`，两份可验证副本已建立。
- Git 边界：只提交 compact source/backup manifest、gate JSON、校验代码和日志；约 19.56 GB 原始数据、约 19 GB tar 与 checkpoint 均不提交。
- 安全边界：所有操作是文件复制、解包和哈希；没有执行真实机械臂命令，也没有覆盖 v2/v3 checkpoint。
- 下一步：提交备份证明与 gate 代码，然后按已冻结 v4 计划启动 36 条 scripted expert 仿真采集；每组必须保持同 simulation seed，采集后核对物理状态一致和 RTX 图像差异。

## 已识别的优化方向

- OpenPI 训练时已经默认启用非腕部相机的随机裁剪/缩放/小角度旋转，并对所有相机使用较强 ColorJitter。因此“再加一点普通图像增强”不是当前缺失功能。
- 当前更有价值的改进是失败定向纠正、同一物理状态的多 RTX 渲染、较低学习率增量微调，以及严格隔离的新确认集。
- 图像量化、轻度模糊和 renderer accumulation reset 已经实测不能消除不确定性，不应直接进入正式控制基线。
- 若 v3 仍在相同条件下翻转，下一优先级是训练阶段显式构造同状态跨渲染配对/一致性目标，而不是继续堆叠通用 ColorJitter。

