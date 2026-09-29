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

### v4-fc-wip.041：v4 纠正集开始采集，首个同状态多渲染组通过自动门禁

- Git 基线：`4ecbe40`（v3 两副本备份证明已推送）；状态：36 条 v4 scripted-expert 采集运行中，本次代码与首组紧凑证据准备提交。
- 准备做：执行预注册的 9 个物理组 × 4 次 RTX 重复；每完成一个组，不只检查任务 PASS，还必须证明四次共享物理条件和 simulation seed、动作/物理轨迹一致，同时两路对应帧确实来自不同渲染结果。
- 做了什么：在备份 gate、36 条计划门禁、目标数据目录为空且没有残留仿真进程的前提下，启动 `rm65_pi05_failure_correction_v4_expert_v1` 采集；最近一次只读检查为 6/36 条完整 metadata，采集主进程仍健康运行。
- 新增自动审计：`analyze_rm65_v4_render_groups.py` 按 `physical_group_id` 分组，核对 4 个重复索引、共享显式 seed、计划 provenance、episode/task 健康、固定 prompt/角度/偏移、动作数组、初始观测/方块姿态、完整观测/方块轨迹，以及 external/wrist 对应帧 SHA-256 多样性；支持 `--group` 在长采集期间先审计完整组。
- 为什么做：目录数量和四个不同图片文件名不能证明“同一物理轨迹的不同 RTX 渲染”；反之，若动作或物理轨迹已经漂移，图像差异也不能归因于 renderer。该门禁把训练纠正集的核心实验变量显式化并 fail-closed。
- 回归：新增合成 4-repeat 测试，健康组必须 PASS；篡改一个动作值后必须返回非零并明确使 action consistency FAIL。本地与远端 Python 编译和回归均 PASS。
- 首组真实结果：`confirm_v3_000_angle_minus_0p0125` 的 4 条均为 569 帧并通过任务/episode 门禁；seed 均为 `891029000`，repeat index 为 0–3。动作、初始状态、初始方块姿态、完整 observation state 与 cube pose 轨迹的最大差异全部精确为 `0.0`。
- RTX 差异：external 和 wrist 的 569/569 个对应帧均在四次运行间存在内容差异，两个视角各有 4 个唯一序列，diverse-frame ratio 都是 `1.0`。因此首组满足“物理轨迹相同、RTX 图像不同”的设计意图，默认 `1e-5` 轨迹容差没有掩盖实际漂移。
- 遇到的问题：首次临时进度检查的 heredoc 结尾被 SSH/PowerShell 引号组合误解析，统计本身已输出但命令以 `NameError` 退出；没有修改远端文件。后续改用无 heredoc 的只读统计，采集未受影响。
- 证据边界：提交审计代码、测试和小型 JSON；36 条原始 episode/PNG/NPZ 仍只保存在数据目录和后续独立备份中，不进入 Git。全程 Isaac Lab 仿真，`real_robot_command_sent=false`。
- 下一步：让采集连续完成，结束后运行全量 dataset summary 与 9/9 group audit；若任一组失败，保留原始数据并先诊断，不用选择性重采覆盖。全部 PASS 后再把 36+30+36 条转换为新的 102-episode LeRobot repo 并重算 norm stats。

### v4-fc-wip.042：冻结 102 条数据准备与低学习率续训合同

- Git 基线：`37d36da`（首组多渲染审计已推送）；状态：采集最近只读检查为 13/36，前三个完整物理组均独立审计 PASS；转换与训练尚未启动。
- 准备做：利用采集等待时间把 collection → preparation → training 三阶段入口做成可重复、fail-closed 的工程流程，避免采完后靠手工命令临时拼接数据或误用旧 norm/checkpoint。
- 新增分阶段门禁：`check_rm65_v4_pipeline_gate.py` 在 collection 阶段要求 v3 两副本 gate 和 v4 预注册计划 PASS；prepare 阶段再要求 36/36 episode、计划覆盖完整和 9/9 同状态多渲染组 PASS；train 阶段再要求新 repo、102 条来源精确为基础 train 36 + v3 纠正 30 + v4 纠正 36、policy window、norm SHA 与 OpenPI 7 维 state/action 合同。
- 可复现入口：新增 `collect_rm65_failure_correction_v4.sh`、`prepare_rm65_failure_correction_v4.sh` 和 `train_rm65_pi05_failure_correction_v4.sh`。默认模式均只做 preflight；显式 `run/start` 才会产生数据转换或训练副作用。采集恢复仍复用已经完整通过的 episode，不覆盖原始成功数据。
- 训练合同：冻结 repo `local/rm65_sim_failure_correction_v4_train`；从 v3 `rm65_failure_correction_v3_lora_10k/9999/params` 初始化，正式实验写入独立 `rm65_failure_correction_v4_lora_6k`，6000 步、batch 1、warmup 300、学习率 `2e-6→5e-7`，预期最终 checkpoint `5999`。这不会覆盖 v2/v3。
- 为什么降低学习率/步数：v4 是在已达到 85–90% 的 v3 上对三个证据驱动缺陷及邻域做增量纠正，不是从 v2 重新学习全任务；更小更新幅度降低 36 条定向样本反复训练导致遗忘原有稳定条件的风险。是否足够仍必须由全新 v4 确认集决定，不能由训练 loss 推断。
- Checkpoint 改进：`train_rm65_pi05.py` 新增通用 `--keep-period`；v4 正式训练设置 4000，因此除最新最终点外保留 step 4000 恢复点。smoke 不永久保留中间点，避免无价值磁盘占用。
- 回归与动态验证：合成门禁测试覆盖三阶段 PASS，并证明把 v3 纠正来源从 30 改成 29 会使 train gate FAIL；本地/远端 Python 编译、单测、三个 shell 的 `bash -n`、实际 collection preflight 和训练器 `--keep-period` 参数加载全部 PASS。
- 真实采集进展：`confirm_v3_000` 的 minus/exact/plus 三个角度组均通过相同 seed、动作一致、物理轨迹一致和双相机 RTX 差异门禁；三个组双相机 diverse corresponding frame ratio 都是 `1.0`。
- 安全与数据边界：collection preflight 重新计算 v3 backup gate；prepare/train 每次也重新核验或消费同一 gate。代码和紧凑 gate JSON 进入 Git，102 条转换数据、原始图像与 checkpoint 不进入 Git。没有真实机械臂命令。
- 下一步：继续完成剩余 23 条；全量 summary/render gate 通过后先为新增 v4 原始纠正数据建立独立可校验副本，再执行 102 条转换、norm 统计和 OpenPI batch 门禁，最后只放行 2-step smoke。

### v4-fc-wip.043：把新纠正集备份和全新确认评测纳入训练前合同

- Git 基线：`d17358a`（v4 分阶段准备/训练入口已推送）；状态：采集最近只读检查为 19/36，4/9 个完整物理组已审计 PASS；本条实现备份/评测合同，但尚未生成最终 v4 源 manifest，也未启动评测。
- 准备做：补齐“新产生的数据也必须跨机器保存”和“训练后只能跑预注册新条件”两端，防止 v4 原始纠正集仍是单盘风险，或训练完成后临时手拼评测命令造成计划漂移。
- v4 保存范围：新增 `rm65_pi05_v4_collection_preservation_assets.json`，把 36 条同状态多 RTX 原始纠正 episode 单独定义为 critical source-of-truth；不重复复制已经通过 v3 两副本门禁的旧资产，降低冗余传输。
- 两副本门禁：新增 `check_rm65_v4_collection_backup_gate.py`，要求源/备份 manifest 使用冻结 spec、唯一正确 asset id、逐文件聚合 tree hash 比较 PASS、总字节非零且相等、source manifest SHA 一致和仿真 provenance。回归证明 `matches_reference=false` 会把 verified copy count 从 2 降为 1。
- 流程加固：v4 pipeline 的 prepare/train 阶段现在额外强制要求上述 v4 collection backup gate PASS 且 `verified_copy_count=2`；因此即使 36/36 数据健康，未完成跨机器校验也不能执行派生数据覆盖或训练。
- 全新确认入口：新增 `evaluate_rm65_pi05_failure_correction_v4.sh`，模式为 `preflight/offline/run1/run2/run3/analyze`。preflight 精确核对训练 6000 步、低学习率、keep-period、训练输入 gate、norm SHA、checkpoint `...v4_lora_6k/5999`、新 repo 和预注册 20 条计划。
- 评测统计边界：run1 是唯一独立成功确认，要求至少 18/20；run2/run3 只提供重复性证据，最终另需 60/60 报告有效、状态一致率至少 95%、最多 1 条 outcome flip。v3 的旧 20 条仍为 development-only，禁止回升为最终成绩。
- 验证：本地/远端备份 gate 单测与 pipeline gate 单测 PASS；prepare/train shell 及 v4 evaluate shell 的远端 `bash -n` PASS。训练报告、checkpoint 和 norm 尚不存在，因此没有伪造动态 evaluation preflight 成功。
- 实时组审计：新增完成的 `confirm_v3_015_angle_minus_0p0125` 组共享 seed `891029003`，动作/完整物理轨迹一致性和双相机 RTX 差异均 PASS；累计 4/9 组通过。
- 安全边界：全部变更是配置、验证代码和仍在运行的 Isaac Lab scripted collection；没有转换、训练、评测或真实机械臂命令。v4 原始数据不会提交 Git。
- 下一步：完成剩余 17 条并运行全量 36/36 + 9/9 门禁；数据停止写入后生成源 manifest，打包传到本机独立备份根，解包并重算 tree hash。两副本 PASS 后才运行 preparation。

### v4-fc-wip.044：36 条 v4 纠正集与跨机器第二副本全部通过

- Git 基线：`a4ba3ca`（v4 保存/评测合同已推送）；状态：scripted collection、全量数据门禁和两副本门禁均 PASS，preparation preflight PASS 且明确未启动转换。
- 采集完成：主进程自然 exit 0，36/36 条一次成功，`newly_completed_count=36`、无复用、无选择性重试；总计 20,484 帧，summary 的 episode 健康、任务成功和 collection-plan coverage 全部 PASS。
- 九组审计：9/9 `physical_group_id` 通过；每组四条共享各自显式 seed，动作、初始关节/夹爪、初始方块姿态和完整 observation/cube trajectory 都在冻结容差内，实际最大差均为 `0.0`。这证明脚本专家轨迹没有随着 RTX 重复漂移。
- RTX 结果：8 个组的 external/wrist 对应帧差异率均为 `1.0`；`confirm_v3_015_angle_exact` 的 external 为 568/569=`0.9982425`，wrist 为 1.0。门禁按真实逐帧内容报告，而不是强行假定每一帧必不同。
- 源 manifest：数据停止写入后逐文件哈希，得到 41,076 个文件、`2,027,380,849` bytes、tree SHA-256 `51daeaef93c24a3501e2923ef9ca5d0c45d1a6be1cde0a13741a914e273ba52d`；source manifest SHA-256 为 `508ef6c6dde2d6d05a1ae989b19ec609c79133ea668c720f548fcd3e4ffc4efe`。
- 归档传输：远端不压缩 tar 为 `2,058,997,760` bytes，SHA-256 `e8df4afc839155b218c439a8033b20ef118dc04a711b63ffca2610447ff78d04`。zstd-1 只能缩到原始 tar 的 98.69%，因此未切换压缩格式。
- 遇到的问题：首次 legacy SCP 在 656,474,112 bytes 处连接重置并报 `Broken pipe`；该部分文件未计为副本。改用 SFTP `reget` 从精确断点继续，最终 exit 0，并下载归档校验和源 manifest。
- 安全解包：解包前检查 41,221 个 tar entry，全部位于预期数据前缀且无绝对路径/`..` 穿越，目标目录原先不存在；随后核对归档 SHA，再对解包文件重新计算 compact tree hash。
- 第二副本：本机 `RM65_DATA_BACKUP_DO_NOT_GIT/v4_collection_2026_09_29` 的文件数、总字节和 tree SHA 与源端完全一致，`comparison_status=pass`、`matches_reference=true`，backup gate 为 PASS，`verified_copy_count=2`。远端源数据和 staging 均保留。
- 回归：expert episode/collection/summary、LeRobot conversion input、v4 plan、manifest、backup gate、render-group gate、pipeline gate 共九项 PASS；训练配置测试首次因 OpenPI venv 启动时漏传 `PYTHONPATH=.` 而 import 失败，按实际训练环境补上后 PASS，不涉及代码/模型错误。
- 准备门禁：`prepare_rm65_failure_correction_v4.sh preflight` 同时验证 v3 两副本、v4 两副本、36/36 与 9/9，输出 `PREPARATION_INPUTS=PASS` 和 `CONVERSION_NOT_STARTED=true`。
- Git/安全边界：只提交约百 KB 的 summary、group audit、manifest/gate 与日志；约 2.03 GB 原始纠正数据和 2.06 GB tar 不进入 Git。全程仿真，未发送真实机械臂命令。
- 下一步：精确提交本条小型证据，然后显式运行 preparation `run`，生成新的 102-episode policy-window LeRobot repo、独立 norm stats 和 OpenPI batch validation；三者 PASS 后才运行 2-step smoke。

### v4-fc-wip.045：102 条新训练集、norm stats 与训练 preflight 全部通过

- Git 基线：`c585d3f`（36/36 纠正数据与两副本证据已推送）；状态：preparation `run` 完成并 exit 0，正式训练仍未启动。
- 启动前检查：新目标 `/home/chengyu/.cache/huggingface/lerobot/local/rm65_sim_failure_correction_v4_train` 原先不存在，且没有并发 conversion、norm 或 `train_rm65_pi05.py` 进程；因此 `--overwrite` 只作用于新的派生目标，不可能覆盖 v3 repo。
- 转换结果：repo id 为 `local/rm65_sim_failure_correction_v4_train`，102 episode 来源精确为基础 train 36 + v3 纠正 30 + v4 纠正 36；53,733 个原始同步帧经冻结 policy window 保留 35,734 个训练帧，conversion report 为 PASS。
- 为什么仍保留三份原始根：policy-window repo 是可重建派生物；原始 episode 保存完整 hold/retreat/图像/物理轨迹，不能用转换后数据替代。新 v4 原始根已通过两副本门禁，旧两根在 v3 核心备份中也有第二副本。
- Norm 结果：558 个 batch 全部处理完成，吞吐约 2 batch/s；dataset frames 35,734、实际统计 35,712、batch 64，keys 恰为 `actions/state`。新 asset 写入 OpenPI v4 repo 专属路径，SHA-256 为 `d21982d3a9235e54326901052d5b7288814c9bbe2699f9c16beae34bbe8c6708`。
- OpenPI 数据门禁：实际加载一个 batch，model type 为 PI0.5、action horizon 10；三相机张量均为 `[1,224,224,3]`，padding 后 state `[1,32]`、actions `[1,10,32]`，RM65 padding 前 state/action 都是 7 维，报告 PASS。
- 训练输入 gate：再次同时验证 v3 两副本、v4 原始两副本、36/36、9/9、102 条来源、policy window、norm 文件路径/内容 SHA 和 OpenPI 合同，所有 checks 为 true。
- 训练 preflight：冻结 v3 `rm65_failure_correction_v3_lora_10k/9999/params` 存在；新 repo/norm/validation/gate 全部匹配；输出 `TRAINING_PREFLIGHT=PASS` 与 `TRAINING_NOT_STARTED=true`，因此本版本没有进行模型更新或写 checkpoint。
- 安全/隔离：转换只生成新派生 repo 和 v4 专属 norm asset；未改原始 episode，未覆盖 v2/v3 checkpoint，未发送真实机械臂命令。
- 下一步：提交 conversion/norm/OpenPI/training-gate 小型 JSON 与本条日志；随后运行独立 `rm65_failure_correction_v4_incremental_smoke` 两步训练，实际验证从 v3 恢复、前反向、数值有限和 checkpoint 保存。smoke PASS 后才允许正式 6000 步。

### v4-fc-wip.046：从 v3 恢复的两步增量训练 smoke 通过

- Git 基线：`53ec2c0`（102 条转换、norm 和训练输入 gate 已推送）；状态：独立 smoke exit 0，正式 `rm65_failure_correction_v4_lora_6k` 目录仍不存在，6000 步尚未启动。
- 隔离检查：启动前 smoke 路径与正式 v4 路径都不存在，GPU 无计算进程；smoke 使用独立 `rm65_failure_correction_v4_incremental_smoke`，即使失败也不会写正式目录或覆盖 v2/v3。
- 实际恢复：从冻结 v3 `rm65_failure_correction_v3_lora_10k/9999/params` 读取约 6.4 GiB，49.29 秒完成；加载新 repo/norm 后 batch 为三相机 `[1,224,224,3]`、state `[1,32]`、actions `[1,10,32]`。
- 数值结果：step 0 为 `loss=0.0060, grad_norm=0.3236, param_norm=1803.9016`；step 1 为 `loss=0.0039, grad_norm=0.2259, param_norm=1803.9016`。loss、梯度和参数范数全部有限，无 OOM/NaN/爆炸。
- Checkpoint：step 1 的约 5.4 GiB checkpoint 完成 params/train_state/assets 写入、metadata commit 和临时目录原子重命名；异步完整保存 65.24 秒，后台无错误。最终 `1/params` 存在且没有残留 `*.orbax-checkpoint-tmp-*`。
- 报告合同：`pi05_rm65_failure_correction_v4_smoke.json` 为 PASS，repo id、v3 initial params、2 步、batch 1、`2e-6→5e-7` 和独立 checkpoint 路径均正确，`real_robot_command_sent=false`。
- 已知信息：ROCm/TPU backend 不可用提示与 XLA rematerialization 警告是当前 NVIDIA 单卡配置的已知日志；CUDA 训练、两次更新和完整保存均已成功，不能据这些提示误判失败。
- 保留策略：smoke 的 `keep_period=null`，只验证一次完整保存；正式训练使用 `keep_period=4000`，从而保留 step 4000 与最终 5999 两个恢复点，而不是让 smoke 占用更多长期磁盘。
- 安全边界：只进行了仿真数据上的离线模型训练，没有启动 Isaac 控制或真实机械臂；v2/v3 checkpoint 未修改。
- 下一步：提交 smoke 小型报告与日志；再次确认正式目录不存在、无训练进程和训练 preflight PASS，然后启动 6000 步正式 v4 微调。监控有限数值、GPU/RAM、step 2000/4000/5999 保存和 step 4000 保留语义。

### v4-fc-wip.047：6000 步 v4 正式增量训练完成并通过产物审计

- Git 基线：`6176dbc`（v4 两步 smoke 证据已推送）；状态：正式训练自然 exit 0，`pi05_rm65_failure_correction_v4_6k.json` 为 PASS，尚未启动 v4 正式确认评测。
- 准备做：从冻结 v3 `rm65_failure_correction_v3_lora_10k/9999/params` 启动独立 v4 生产目录的 6000 步微调；持续检查 loss/grad/param 有限性、2000/4000/5999 保存、4000 的永久保留语义和 v2/v3 不覆盖边界。
- 实际合同：repo `local/rm65_sim_failure_correction_v4_train`，batch 1，warmup 300，学习率 `2e-6→5e-7`，`keep_period=4000`；最终候选为 `rm65_failure_correction_v4_lora_6k/5999`。训练报告中的 repo、初始参数、步数、学习率、保留周期和路径全部与冻结合同一致。
- 数值稳定性：从 step 0 到 step 5999 的已观察 loss、梯度范数和参数范数全部为有限值；参数范数从约 `1803.9016` 平稳变化到 `1803.9023`。个别困难批次梯度约 2，但下一批立即恢复，没有持续梯度爆炸、NaN、OOM 或进程重启。
- 中间保存：step 2000 首次完整保存后具有 params/metadata 且无临时目录；step 4000 保存完成后，Orbax 按 `max_to_keep` 删除 2000，并明确以 `keep_period=4000` 保留 4000。最终目录精确只含 4000 和 5999。
- 遇到的问题：step 4000 的约 6.4 GiB 主状态与约 397.9 MiB 附加状态写盘降至约 29.8/1.8 MiB/s，异步保存耗时 `225.28 s`；进程一度处于 `folio_wait_bit_common`，但磁盘剩余约 2.2 TiB、无 OOM，随后原子改名成功并由后台线程报告无错误。没有把正常 I/O 等待误判成训练失败，也没有强杀正在提交的检查点。
- 最终保存：step 5999 同步阻塞约 2.30 秒，异步完整保存 `73.13 s`；临时目录原子改名为 5999，后台线程无错误，训练器等待 finalize 完成后写出 PASS 报告并自然 exit 0。
- 产物审计：4000 和 5999 均包含 params、train_state、assets 与 `_CHECKPOINT_METADATA`；全树 `orbax-checkpoint-tmp` 数量为 0，训练进程不存在。v2 `rm65_policy_window_v2_lora_30k/29999` 时间戳仍为 2026-09-19，v3 `rm65_failure_correction_v3_lora_10k/9999` 时间戳仍早于 v4，本次没有覆盖旧 checkpoint。
- 可优化点：训练计算稳定在约 4.2–4.5 step/s，主要工程瓶颈不是 GPU 训练而是多 GiB checkpoint 的主机内存转移、写盘和保存后设备同步。后续可评估更快的 checkpoint 盘、减少 train_state 保存体积或降低非关键保存频率，但不能为了速度删除 step 4000 恢复点或跳过最终原子提交验证。
- Git/数据边界：只提交 898-byte 训练报告、状态和日志；约 14 GiB 的 4000/5999 checkpoint 不提交 Git。报告明确 `simulation_only=true`、`real_robot_command_sent=false`，没有执行 Isaac 控制回路或真实机械臂命令。
- 下一步：提交本条紧凑证据；执行冻结的 v4 evaluation preflight 与 offline 检查。二者 PASS 后只运行预注册全新 20 条的 run1，至少 18/20 才进入 run2/run3 重复性验证，不能用训练 loss 宣称部署完成。

### v4-fc-wip.048：v4 评测预检与离线推理门禁通过

- Git 基线：`7810048`（v4 正式训练报告已推送）；状态：evaluation preflight 和 offline 均 exit 0/PASS，闭环 run1 尚未启动。
- 准备做：在启动新 Isaac Lab 闭环前重新验证 checkpoint、repo、norm SHA、训练输入 gate、预注册计划和控制器阈值没有漂移；随后只在已存 validation 数据上检查模型可加载、动作维度/有限性和安全 guard。
- 预检结果：训练报告仍精确匹配 6000 步、batch 1、warmup 300、`2e-6→5e-7`、`keep_period=4000`；最终 checkpoint id 为 `rm65_failure_correction_v4_lora_6k/5999`。norm 文件存在且 SHA 与冻结报告一致，20 条确认计划仍有 exactly 20 cases，成功门槛 18/20、重复次数 3、60/60 报告和最多 1 条翻转合同均未漂移。
- 单帧 checkpoint 推理：从 5999 加载耗时 35.48 秒，首次推理 11.01 秒；输出 shape `[10,7]`、全部有限。guard 后无 joint-limit clamp、无 joint-step clamp，最大输出关节步长 `0.008745 rad`；有 1 次 gripper clamp，属于归一化动作到执行边界的预期保护。
- Held-out 离线结果：validation 共 9 episode × 5 帧 = 45 样本，全部输出有限且维度正确。手臂 horizon MAE `0.005625 rad`、P95 绝对误差 `0.021963 rad`；夹爪 horizon MAE `0.004215`、P95 `0.008658`；首动作手臂平均 L2 误差 `0.012094 rad`。
- 推理性能解释：第一样本包含约 9.54 秒 JIT/冷启动，之后大多数样本约 0.1 秒，因此总 mean `0.3085 s` 而 P95 `0.0992 s`；不能把首次编译耗时当成稳态闭环延迟，也不能忽略部署启动时需要 warm-up。
- Guard 解释：45 样本全 horizon 累计 54 次 joint-step clamp 和 170 次 gripper clamp，说明 guard 在离线轨迹上确实参与约束；这不是任务失败，但闭环评测必须保留 guard，不得为了贴近标签而绕过安全限制。
- 证据边界：offline 报告明确 `simulation_action_executed=false`、`task_success_claimed=false`、`real_robot_command_sent=false`。PASS 只证明模型/数据接口和数值健康，不证明抓取放置闭环成功。
- Git/数据边界：提交两份小型 JSON 和日志/状态，不提交 validation 图像、数据集或 checkpoint。
- 下一步：精确提交本条证据，然后启动预注册 v4 run1 的 20 条全新仿真条件。正常模型失败不重试；只有缺失有效报告的基础设施失败才允许按 suite 恢复。

### v4-fc-wip.049：首轮全新 20 条闭环确认完成但 17/20 未过门禁

- Git 基线：`ce1952d`（v4 offline 证据已推送）；状态：run1 的 20/20 task report 完整，无基础设施缺失，suite 因成功率门禁未过而按设计 exit 1。
- 准备做：以训练前冻结的 checkpoint `rm65_failure_correction_v4_lora_6k/5999`、repo、控制阈值、20 条计划和每条显式双种子运行唯一独立成功确认；普通模型失败不得重试。
- 总结果：17/20=`85%`，低于预注册的 18/20=`90%`；gate 的 episode 数和全部报告存在性两项 PASS，只有 minimum success rate FAIL。失败为 `confirm_v4_010`、`011`、`015`，全部保留，未重试、未改阈值、未修改模型。
- 失败分布：角度 `0.6875/0.7625 rad` 均 5/5；`0.8375 rad` 为 3/5，`0.9625 rad` 为 4/5。提示词 `place the block on the target platform` 为 2/4，`grasp the block and set it on the target` 为 3/4，其余三个 prompt 均 4/4。样本量很小，只用于定位，不把 prompt 相关性当因果结论。
- `confirm_v4_010`：角度 0.8375、offset `(-0.011,0.001)`；最大抬升仅 `0.00594 m`，最大源点 XY 位移约 `0.0781 m`，未接近目标且未验证释放。末段方块跌出工作台，最终 z 约 `-5.607 m`，target position error `6.274 m`。
- `confirm_v4_011`：角度 0.8375、offset `(-0.006,0.007)`；最大抬升 `0.01960 m`，未验证释放，随后触发 `cube_outside_workspace_envelope`，最终 z 约 `-10.590 m`，target position error `11.255 m`。
- `confirm_v4_015`：角度 0.9625、offset `(-0.011,0.001)`；没有越界，方块移动约 `0.1534 m`，但最大抬升 `0.01969 m` 略低于 0.02 m，最小 target XY error 约 `0.0661 m`，终止时夹爪仍关闭且未满足连续两 chunk 释放条件。因此属于近目标但未收敛/未释放，不是全局物理崩溃。
- 共同失败分类：三条均 `insufficient_lift + target_xy_error + target_position_error + release_not_verified`；010/011 另有 `simulation_out_of_bounds + post_release_drift`，010 还未达到最小位移。
- 遇到的问题：010 最终位置已越界但 `simulation_safety_abort_reason=null`，而 011 正确标记 workspace abort。轨迹显示 010 在最后约 0.85 秒从目标高度以下 0.10 m 跌到 z<0，推测越界发生在 max-chunk 后 settle/报告窗口，当前在线 abort 只覆盖动作循环。这是诊断覆盖缺口，不能据此抹去任务失败；应在三次冻结评测完成后为最终 settle 增加相同越界标记。
- 结论边界：run1 已确定 FAIL，v4 不能标记仿真部署完成。run2/run3 若执行，只用于判断相同条件在不同 RTX 渲染下是否翻转，不能取代或“择优覆盖”17/20 的首轮成绩。
- Git/数据边界：提交 run1 summary、失败 taxonomy 和日志/状态；20 条原始图像、NPZ、runner log 与大 task report 保留在远端数据目录但不进 Git。全程仿真，`real_robot_command_sent=false`。
- 下一步：先提交本条证据；不修改任何评测/控制代码，按同一计划执行 run2、run3。获得 60/60 报告后做 outcome matrix，再把 v4 全部条件永久降级为开发集，生成证据驱动 v5 纠正计划与另一组全新 held-out 最终确认条件。

### v4-fc-wip.050：第二轮重复性诊断精确复现 17/20

- Git 基线：`648302c`（run1 完整失败证据已推送）；状态：run2 的 20/20 报告完整，17/20=`85%`，失败仍为 `confirm_v4_010/011/015`，与 run1 的 20 个 outcome 全部一致。
- 实验边界：run2 复用同一个 v4/5999 checkpoint、repo、控制阈值、20 条计划、policy noise seed、simulation seed 和确定性 chunk seed 规则；没有修改代码、模型或评测条件。允许变化的目标变量是 RTX 渲染随机性。
- 重复性中间结果：40/40 有效报告，run1/run2 成功数都是 17；当前 status consistency `100%`、outcome flip case `0`。这说明失败并非一次性渲染偶然，但仍不能把“一致”误写成“成功”。
- 稳定失败：010 两轮均低抬升后跌出工作台；011 两轮均跌出工作台；015 两轮均停在目标边缘且未完成释放。run2 中 010/011/015 的 target position error 分别约 `11.892/11.730/0.0551 m`，三条 `release_not_verified` 均继续存在。
- 轨迹幅度变化：虽然 PASS/FAIL 未翻转，细指标受 RTX 闭环路径影响。015 的 lift 从 run1 `0.01969 m` 变为 run2 `0.02219 m`，跨过 0.02 m 子条件；最终误差从 `0.06835 m` 改善到 `0.05509 m`，但仍高于 0.05 m 且未释放。011 的 run2 最终夹爪为打开状态，但未在“已抬升且接近目标”的连续两 chunk 窗口内完成验证，随后方块越界。
- 结论：010/011 是稳定的抓取/搬运失稳，015 是接近门槛的稳定未收敛；v5 应分别采集跌落前恢复/稳定抬升轨迹和目标边缘连续释放轨迹，而不是笼统增加图像增强。
- Git 优化：suite 的 full summary 含逐条完整 task report，单份约 12 万行；run1 已保留一份完整结构化证据。run2 不再重复提交 full summary，只提交 compact failure taxonomy，完整 summary、task report、PNG、NPZ 和 runner log 保留远端且不进 Git。
- 安全边界：run2 全程 Isaac Lab 仿真，`real_robot_command_sent=false`；普通失败未重试，run1 成绩仍固定为 17/20。
- 下一步：提交本条 compact 证据；继续无改动运行 run3，随后用预注册分析器生成 20×3 matrix，要求 60/60 报告、至少 95% status consistency 且最多 1 个 flip。该重复性门禁即使 PASS，也不会覆盖 run1 成功门禁 FAIL。

### v4-fc-wip.051：60/60 重复性门禁压线通过，但独立成功门禁仍失败

- Git 基线：`75c4c3e`（run2 compact 证据已推送）；状态：run3 为 16/20，最终 20×3 自动矩阵生成成功，重复性 gate PASS，整体仿真部署 gate 仍 FAIL。
- 三轮成绩：run1 `17/20=85%`、run2 `17/20=85%`、run3 `16/20=80%`；60/60 task report 有效，无缺失或无效报告。首轮低于预注册 18/20，因此无论后两轮如何，v4 都不能标记为部署完成。
- 重复性结果：19/20 case 三轮状态一致，status consistency `95%`；outcome flip 恰为 1，满足“至少 95%、最多 1 flip”的冻结门槛。结果模式为 16 条 `PASS/PASS/PASS`、3 条 `FAIL/FAIL/FAIL`、1 条 `PASS/PASS/FAIL`。
- 变量控制证据：20/20 case 的初始 joint、gripper、cube position/quaternion、wrist tool pose、wrist camera pose 和 chunk-zero noise hash 三轮匹配；external/wrist 图像 0/20 匹配，raw action 0/20 匹配。物理状态与随机噪声相同而图像/动作不同，符合隔离 RTX 渲染随机性的设计。
- 三条稳定失败：`010/011/015` 均为 `FAIL/FAIL/FAIL`。010 三轮平均 lift 仅 `0.00688 m`，稳定未抓稳；011 平均 lift 约 `0.02034 m`，但目标/释放阶段不稳定；015 三轮 target XY error 范围 `0.05096–0.06608 m`，始终略高于 0.05 m 且未验证释放，是明确的目标边缘未收敛样本。
- 唯一翻转：`017` 为 `PASS/PASS/FAIL`，角度 0.9625、offset `(0.001,-0.011)`、prompt 为 `pick up the block and place it on the target`。第三轮 lift 正常约 `0.04554 m`，但随后方块跌出工作区，最终 position error `11.979 m`、post-release drift `6.428 m`；同物理初态/同 noise 下仅 RTX 图像变化导致动作序列分叉。
- 结论：v4 已把 v3 的随机翻转问题收敛到 1/20 并通过重复性上限，但成功率没有提升，仍有三条稳定失败和一条渲染敏感失败。下一版价值最高的是针对这四条构造不同类型纠正：010/011 强化安全抓稳/抬升与防跌落，015 强化目标边缘连续释放，017 增加同物理状态跨 RTX 一致性样本。
- 数据泄漏边界：v4 的 20 条确认条件从现在起永久降级为 development-only，后续可用于 v5 纠正，但不得再次作为独立最终成绩；v5 必须在训练前冻结另一组与 v3/v4 训练和确认条件均不重合的 held-out 计划。
- Git 优化：提交 run3 compact failure taxonomy 和 20×3 matrix；run2/run3 full summary、60 条 PNG/NPZ/大 task report/runner log 只保存在数据目录与待建独立备份，不进入 Git。
- 安全边界：三轮全部为 Isaac Lab 仿真，自动报告 `simulation_only=true`、`real_robot_command_sent=false`；没有启动真实机械臂命令。
- 下一步：精确提交本条最终 v4 证据；在开始 v5 纠正采集前，为 v4/5999 checkpoint、norm 和三轮原始评测建立第二份校验副本。随后冻结 v5 的纠正采集计划、低学习率续训合同与全新 held-out 最终确认计划。

### v4-fc-wip.052：冻结 v4 模型与三轮评测的六资产保存合同

- Git 基线：`134ff26`（最终 v4 20×3 证据已推送）；状态：备份 spec、两副本 gate 和损坏副本测试已实现，尚未开始源哈希或传输。
- 准备做：在把 v4 评测条件用于 v5 纠正之前，先保存能完整复盘“训练得到什么、三次实际发生什么”的关键资产；避免只在 Git 中留下摘要，而原始 checkpoint/trajectory 因后续清理丢失。
- 六项范围：v4 recovery checkpoint 4000、final checkpoint 5999、冻结 norm stats、confirmation run1/run2/run3 原始目录。精确预盘点为 66,585 个文件、`14,081,286,311` bytes。
- 为什么保留 4000：最终 5999 未过独立成功门禁，4000 是唯一冻结的中间恢复点，后续可用于离线比较或从更早增量状态继续；仅保留 5999 会丢失低成本回退能力。
- 为什么不再复制 102-episode LeRobot repo：它约 3GB，但可由已经有两份验证副本的 base/v3/v4 原始训练数据和 Git 中的转换代码重建；norm stats 和 checkpoint 则属于冻结训练合同，必须直接保存。
- 新 spec：`rm65_pi05_v4_release_preservation_assets.json` 为每项定义 source/backup 相对路径、优先级和可重建性；backup 根将使用本机 `RM65_DATA_BACKUP_DO_NOT_GIT/v4_release_2026_09_29`，不会进入 Git。
- 新 gate：`check_rm65_v4_release_backup_gate.py` 要求固定 spec id、固定六个 asset id、精确 66,585 文件与 14,081,286,311 bytes、每项 tree hash 匹配、source manifest SHA 匹配和仿真 provenance；任一项损坏则 verified copy count 从 2 降为 1。
- 回归：合成健康 manifest 必须 PASS；将任一资产 `matches_reference=false` 必须 FAIL。下一步还要在远端真实 source manifest 上动态验证精确盘点，静态预盘点不能代替逐文件 SHA。
- 数据/Git 边界：只提交 spec、gate、test 与日志；约 14.08GB 资产、归档和本机副本均不进入 Git。没有真实机械臂命令。
- 下一步：远端编译和单测 PASS 后提交本版本；随后生成 source manifest 和 source-manifest SHA，逐项归档并传到本机，安全解包后从本机文件重新计算 backup manifest，最后 gate PASS 才开始 v5 规划。

### v4-fc-wip.053：v4 release 六资产跨机器第二副本验证完成

- Git 基线：`58e544e`（v4 release 保存合同已推送）；状态：source manifest、归档传输、安全解包、本机独立 rehash 和两副本 gate 全部 PASS，v5 规划门禁解除。
- 源清单：6 项合计 66,585 文件、`14,081,286,311` bytes；source manifest SHA-256 为 `68bee34eb7c14130c9d2d0cb5c4d059892b3bc05dbbecffc04d9235010c41a06`。
- 逐资产 tree hash：checkpoint 4000 为 `0d03f572...419e5c8a`，checkpoint 5999 为 `86f89b33...cecbf07`，norm 为 `353dbe9c...f0398764`；run1/run2/run3 分别为 `0d029664...657a0ad`、`67b135a5...cef967e`、`e0ab63b2...e942e9`。
- 归档方法：在远端 staging 建立六个只读 symlink，使用 `tar --dereference` 按 backup spec 路径打包；没有复制、改名或覆盖源资产。未压缩归档为 `14,200,432,640` bytes，SHA-256 `979c2f554aba3be5b27061addf51bc8367b13a025bfe05ae63c0cb1ccc1db2a0`。
- 传输：直接使用 SFTP `reget` 到本机 `RM65_DATA_BACKUP_DO_NOT_GIT/v4_release_2026_09_29`，约 14.2GB 一次完成并 exit 0；本机文件大小和整包 SHA 与远端精确一致。批处理文件保留，可在未来中断时断点续传。
- 安全解包：tar 共 66,922 entries，其中 66,585 个普通文件；非法绝对/`..` 路径 0、链接或设备等特殊 entry 0，顶层只含 `checkpoints/evaluations/openpi_assets`。目标三个目录原先均不存在，审计 PASS 后才解包。
- 独立文件级复核：本机从解包后的 66,585 文件重新计算每项 SHA 聚合 tree hash；backup manifest 的 `comparison_status=pass`，六项全部 `matches_reference=true`，总文件数和字节数与源端一致。
- 最终 gate：所有 14 个 fail-closed checks 为 true，`status=pass`、`verified_copy_count=2`。源端数据、远端 staging、归档、本机归档和解包副本均暂时保留，没有清理。
- Git/数据边界：只提交 source/backup manifest、gate 和日志/状态；14.2GB tar、14.08GB 解包内容、checkpoint、PNG、NPZ、task report 与 runner log 均不进入 Git。
- 安全边界：所有操作是只读哈希、归档、传输和解包，`real_robot_command_sent=false`。
- 下一步：提交本条 compact 证据；从三条稳定失败和一条翻转生成 v5 纠正采集计划，同时在训练前冻结又一套与既有条件不重合的 held-out 确认计划。修复 010 最终 settle 越界漏标记，但不改变已冻结 v4 结果。

### v4-fc-wip.054：冻结证据驱动的 v5 纠正与全新确认计划

- Git 基线：`0cd249e`（v4 release 两副本证据已推送）；状态：v5 plan generator、回归测试、48 条纠正计划、20 条全新确认计划和 validation report 均 PASS，尚未开始采集。
- 选择规则：从 v4 20×3 matrix 自动选择所有非 `PASS/PASS/PASS` 条件，必须精确得到三个 `FAIL/FAIL/FAIL`（010/011/015）和一个 `PASS/PASS/FAIL`（017）；pattern 或 case id 漂移即 fail-closed。
- 纠正规模：4 个源 case × `-0.0125/0/+0.0125 rad` 三个角度邻域 × 4 个同 seed RTX 重复 = 48 条；共 12 个物理组，每组动作与物理初态应相同、图像允许不同，simulation seed 从 `892029000` 独立分配。
- 故障分工：010 标记 `grasp_lift_stability`，011 标记 `transport_workspace_retention`，015 标记 `target_edge_release_convergence`，017 标记 `cross_render_action_consistency`。这些标签进入每条 metadata，后续可按故障目标分别审计，而不是只看总 episode 数。
- 数据泄漏边界：v4 的 20 条确认 case 全部 development-only，禁止再次作为独立成绩。v5 纠正仅消费其中 4 条非稳定成功条件及其角度邻域。
- v5 全新确认：20 条由四个角度 `0.70625/0.79375/0.86875/0.9875` × 五个新 offset 组成，五种 prompt 各 4 次；policy seed 从 `692029000`、simulation seed 从 `792029000` 开始。
- 隔离验证：新 20 条与 base/v3/v4/v5 correction 的 159 个计划 case 条件和角度不重合，五个 offset 也不出现在既有训练或 v3/v4 确认中；与 v3/v4 共 40 条确认条件及其双种子完全隔离。
- 冻结控制合同：目标 repo `local/rm65_sim_failure_correction_v5_train`，目标 checkpoint `rm65_failure_correction_v5_lora_4k/3999`；控制器仍为 120 chunks、policy open threshold 0.12、actual open threshold 0.20、连续两 chunk release verification。
- 评测门槛：首次全新 20 条仍须至少 18/20；run2/run3 只作重复性证据，要求 60/60 报告、至少 95% case 状态一致、最多 1 个 flip。普通失败不重试，基础设施重试必须以缺失有效报告为前提。
- 回归：本地 Python 编译和 `RM65_V5_PLAN_TEST=PASS`；实际生成 validation 的 correction/confirmation 所有 checks 为 true。远端仍需复跑后才提交。
- 安全边界：本版本只生成计划和验证代码，未采集、转换、训练、评测或发送真实机械臂命令。
- 下一步：提交生成器、测试和冻结计划；修复最终 settle 越界漏标记，并在采集前实现 v5 collection→backup→150-episode preparation→4000-step low-LR training→fresh evaluation 的完整 fail-closed 入口。

### v4-fc-wip.055：补齐动作结束后 settle 阶段的工作区安全诊断

- Git 基线：`c888de0`（v5 纠正与全新确认计划已推送）；状态：纯函数安全规则、在线/settle 共用调用和回归测试本地 PASS，待远端复跑与提交。
- 准备做：修复 v4 `confirm_v4_010` 暴露的诊断缺口——方块在最后动作 chunk 后的 240 physics-step 验证窗口跌出工作区，旧报告的 `simulation_safety_abort_reason` 仍可能为 null。此变更只补证据，不改变策略输入、动作、阈值、hold 步数或成功标准。
- 原因：旧代码只在每个动作 chunk 后检查非有限位置与相对源点 1.0 m 的逃逸半径；`PI05_SETTLE_A/B` 后直接计算最终指标。因此越界若恰好发生在 max-chunk 后，结果虽然因巨大 target error 失败，却缺少统一安全原因，降低失败分类与后续纠正集审计质量。
- 方法：把同一判定抽为不依赖 Isaac Lab 的 `evaluate_cube_workspace_safety`；在线 chunk、settle A、settle B/final 均调用它。保留首个 violation，不让后续更远的跌落覆盖原始发生阶段。
- 新证据：报告增加 `simulation_safety_first_violation_stage` 和 `post_control_simulation_safety_checks`，后者分别记录 settle A 与最终位置的 reason/相对源点位移。若 settle 才首次越界，既有 `simulation_safety_abort_reason` 将明确写为 `cube_outside_workspace_envelope`；非有限位置写为 `non_finite_cube_position`。
- 回归边界：测试覆盖工作区内、超过半径、NaN 位置、错误维度、非正半径和非有限源点；原有 checkpoint/双种子/采样哈希/安全中止 fail-closed 验证继续通过。
- 兼容性：既有 v3/v4 报告保持冻结，不回写历史结果；v5 以后生成的新报告才包含新增字段。v4 的 17/20 首轮成绩与 60/60 重复性矩阵不变。
- 安全边界：无 Isaac Lab 动作执行、无训练、无数据变更、无真实机械臂命令。
- 下一步：远端 Python 编译和回归 PASS 后精确提交本版本；随后在开始 48 条 v5 采集前，冻结 collection→raw backup→150-episode preparation→4000-step low-LR training→全新 20×3 evaluation 的完整 fail-closed 入口。

### v4-fc-wip.056：采集前冻结 v5 全流程 fail-closed 合同

- Git 基线：`ba50e76`（post-settle 安全诊断已推送）；状态：v5 collection/backup/preparation/training/evaluation 入口、单元回归、远端 shell 语法和真实资产采集预检全部 PASS，48 条采集尚未开始。
- 准备做：在新增任何训练数据前，把“何时允许采、何时允许转、用什么模型续训、怎样判最终成绩”固化为代码；避免采集完成后再临时改变 episode 数、学习率、checkpoint 或评测条件。
- 采集门禁：`collect_rm65_failure_correction_v5.sh` 必须先重算 v4 release 六资产的两副本 gate，再验证 v5 plans。支持 `first-group` 只采最前 4 条同物理 seed RTX 重复；该组通过动作/初态/物理轨迹一致性和双相机图像多样性审计后，才恢复余下 44 条。
- 原始数据保存：新增 v5 单资产 preservation spec、source manifest/backup manifest 生成入口和独立 gate。转换前必须达到 `verified_copy_count=2`、逐树哈希一致、source-manifest SHA 一致；数据集和备份不进入 Git。
- 准备合同：合并 base 36 + v3 correction 30 + v4 correction 36 + v5 correction 48 = 150 episodes，repo 固定为 `local/rm65_sim_failure_correction_v5_train`；必须启用 policy-window，重新计算专属 norm 并核对 norm 文件路径与 SHA。
- 训练合同：只从冻结的 v4 final `rm65_failure_correction_v4_lora_6k/5999/params` 初始化；新输出目录为 `rm65_failure_correction_v5_lora_4k`，不得覆盖 v2/v3/v4。正式训练 4000 steps、batch 1、warmup 200、LR `1e-6→2.5e-7`、save interval 2000、keep period 2000，预期保留 2000 与 3999；先执行独立 2-step smoke。
- 为什么进一步降学习率：v4 已有 85% 首轮成功率且重复性 95%，v5 的目标是修复 4 个证据驱动局部失效，不是重新学习整项任务。峰值从 `2e-6` 降到 `1e-6`、末值从 `5e-7` 降到 `2.5e-7`，降低 48 条定向纠正覆盖既有 102 条能力的风险。
- 评测合同：训练前冻结的 v5 20 条条件仍要求 run1 至少 18/20；三轮共 60/60 报告、至少 95% 状态一致、最多 1 个 flip。评测预检额外要求 `.055` 的 settle A/B 工作区安全诊断合同，不允许新结果回到“最终越界但 reason 为 null”。
- 故障注入回归：健康的 collection/prepare/train/evaluation fixture 全部 PASS；v5 source count 从 48 改为 47 会阻断训练；关闭 post-control safety requirement 会阻断评测；损坏备份的 `matches_reference` 会把两副本 gate 降为 FAIL。
- 兼容性：same-state/multi-RTX 分析器新增显式 `--report-format`，默认仍保持 v4 schema，v5 调用产生 `rm65_v5_render_group_analysis_v1`，既有 v4 测试继续 PASS。
- 安全/Git 边界：所有入口仅指向 Isaac Lab、数据、OpenPI 训练和离线/仿真评测；没有真实机械臂命令。只提交配置、脚本、小型 validation 和日志，不提交 dataset、norm 资产或 checkpoint。
- 远端验证：Python 编译通过；v4 render-group 兼容回归、v5 plan、collection backup、pipeline gate、evaluation preflight、entrypoint 静态合同测试全部 PASS；五个 shell 入口 `bash -n` PASS。随后从 Git 中冻结的 v4 release source/backup manifest 重新计算两副本 gate，实际 v5 collection preflight PASS，并输出 `COLLECTION_NOT_STARTED=true`。
- 下一步：精确提交本版本和实际 collection gate；随后运行 first-group 4 条而不是直接吞下 48 条。

### v4-fc-wip.057：v5 首个同状态四 RTX 组通过审计

- Git 基线：`4293f0f`（v5 fail-closed 流水线已推送）；状态：首组 4/4 scripted-expert 仿真 episode 采集成功，独立 same-state/multi-RTX 分析 PASS，剩余 44 条尚未启动。
- 准备做：先只采计划最前四条 `confirm_v4_010_angle_minus_0p0125`，验证新 v5 元数据、同 seed 重复和 RTX 多样性实际成立；避免计划或 recorder 接口若有问题时一次生成 48 条错误数据。
- 采集结果：episode 000000–000003 全部 `task status=pass`、`unassisted_full_task_complete=true`、episode validation PASS、training-ready；每条 569 帧、28.4 秒，进程 exit 0。四条共享 simulation seed `892029000`，全程 `pi05_used=false`、`real_robot_command_sent=false`。
- 物理一致性：四条 command action 最大绝对差为精确 `0.0`；初始 joint/cube 状态 gate PASS，完整 observation-state 与 cube-pose 轨迹在冻结容差内 PASS；说明重复采的是同一物理专家轨迹，不是四条不同动作。
- 渲染差异：external 和 wrist 两路在 569/569 个对应帧上均出现不同哈希，diverse ratio 都为 `1.0`；因此同物理状态确实产生了不同 RTX 渲染，而不是复制同一批 PNG。
- 计划覆盖：组内四个 case id、render index 0–3、repeat count 4 和共享 seed 与预注册计划逐项匹配，group coverage PASS；只有这一个组选入审计，因此没有把尚未采集的 44 条误判为缺失。
- 遇到的非阻断信息：headless 环境持续输出 GLFW/X Server 警告、CPU powersave 警告和低分辨率 DLSS 提示；Vulkan RTX 相机正常产生图像，四条任务和数据验证均通过，故不把这些基础设施警告误分类为 episode 失败。
- 数据/Git 边界：原始 NPZ/PNG/task report 只留远端数据目录，不提交 Git；提交小型首组分析 JSON 与日志/状态。原始数据尚未达到两副本，禁止开始转换。
- 下一步：提交本条证据；collection runner 将识别已经完成的 4 条并只采剩余 44 条。全部完成后必须做 12/12 组审计和 raw source manifest，再复制到第二存储并通过 backup gate。

### v4-fc-wip.058：把 v5 备份归档的解包前安全审计变成代码

- Git 基线：`b5ffd9b`（首个 v5 四重复组证据已推送）；状态：剩余 44 条后台采集已启动，新增 tar audit 与故障注入测试本地 PASS，不读取或修改正在写入的 episode。
- 准备做：在原始数据采完并跨机器传输后，先验证 tar 内部结构再解包。v4 曾做过一次人工+临时脚本审计；v5 把相同原则固化为可重复、可回归的项目工具。
- 检查范围：拒绝绝对路径、任何 `..`、required dataset prefix 之外的 entry、symlink/hardlink/device 等非普通文件与非目录 entry、重复规范化路径；普通文件数量和 tar payload 总字节必须与 source manifest 中指定 asset 精确一致。
- 为什么在解包前检查：归档自身 SHA 一致只能证明传输无误，不能证明归档成员安全或范围正确；source tree hash 一致则需要解包后重算。顺序应为“整包 SHA→成员安全/盘点→解包到新目录→逐文件 rehash→两副本 gate”，不能跳步。
- 测试：健康的双文件归档 PASS；含 `../escape.bin` 的 traversal 归档 FAIL；含绝对目标 symlink 的归档 FAIL；健康归档但期望文件数改错也 FAIL。审计器本身只读 tar、不会解包。
- 采集并发边界：新增脚本不影响当前 Isaac Lab 进程，不改 expert、plan 或 recorder；当前后台采集沿用已提交的 `b5ffd9b` 数据合同。
- 安全/Git 边界：提交审计代码、测试和日志；将来的 tar、解包数据和 manifest 中的大资产仍不进入 Git。无真实机械臂命令。
- 下一步：远端复跑审计单测并提交；继续监控采集。48/48 完成后先做 12/12 组审计和 source manifest，再创建静态归档，绝不对仍在写入的数据目录打包。

### v4-fc-wip.059：scripted expert 的 0.85 rad 边界失败被显式重规划

- Git 基线：`e1d91a3`（tar 解包前审计已推送）；状态：formal v5 已完成 8 条。episode 000008 在 expert post-run gate 被正确阻断，失败数据已保留到 rejected 目录；同条件 0.845 rad 诊断 PASS，待更新计划后恢复。
- 遇到的问题：原计划 `confirm_v4_010_angle_plus_0p0125` 为 0.85 rad。该条所有数组/图像格式和有限性验证 PASS，抬升 `0.039591 m`、release drift `0.008222 m` 均正常，但最终 target XY error `0.0502217 m`，比 expert 的 0.05 m 成功阈值高 `0.0002217 m`，因此 task report 正确为 FAIL，runner 没有把它计入训练。
- 分类：这是 scripted expert 在该角度/offset 的几何边界不可行，不是 RTX 随机失败，也不是基础设施中断。相同 seed 下重复 0.85 只会复现不合格标签，所以不允许用重试掩盖。
- 证据保留：失败目录从 formal dataset 移到 `rm65_pi05_failure_correction_v5_rejected_attempts/episode_000008_angle_0p85`，没有删除；它明确 `included_in_training=false`。formal dataset 仍只有 episode 000000–000007 八条健康数据。
- 诊断方法：保持 offset `(-0.011,0.001)`、prompt 和 simulation seed `892029002` 不变，只把角度从 0.85 降到 0.845 rad。诊断结果 PASS，final target XY error `0.0092462 m`、drift `0.0070659 m`、lift 不变为 `0.039591 m`，有充足阈值余量。
- 计划修正：只把 010 的正向邻域从 `+0.0125` 改为 `+0.0075 rad`，四个 render repeat 仍使用 episode index 8–11 和同一个 seed；其他 11 个物理组不变。generator 现在显式声明 case-specific deltas 与 probe evidence，回归要求新组精确为四条 0.845 且不得残留 0.85。
- 数据泄漏边界：v5 全新 20 条 confirmation 没有改变；0.85 rejected attempt 和 0.845 probe 都不作为训练 episode，正式四重复会在计划提交后重新采。因修改发生在训练和最终确认之前，不构成用 held-out v5 结果调参。
- 安全/Git 边界：提交 generator、重新生成的 correction plan/validation、小型 probe JSON 与日志；rejected/probe 原始数据不进 Git。全程 scripted Isaac Lab，`pi05_used=false`、`real_robot_command_sent=false`。
- 下一步：远端重生成计划并通过全部 disjointness/pipeline tests，精确提交；随后 runner 从 episode 8 恢复，已完成 0–7 不重采。

## 已识别的优化方向

- OpenPI 训练时已经默认启用非腕部相机的随机裁剪/缩放/小角度旋转，并对所有相机使用较强 ColorJitter。因此“再加一点普通图像增强”不是当前缺失功能。
- 当前更有价值的改进是失败定向纠正、同一物理状态的多 RTX 渲染、较低学习率增量微调，以及严格隔离的新确认集。
- 图像量化、轻度模糊和 renderer accumulation reset 已经实测不能消除不确定性，不应直接进入正式控制基线。
- 若 v3 仍在相同条件下翻转，下一优先级是训练阶段显式构造同状态跨渲染配对/一致性目标，而不是继续堆叠通用 ColorJitter。

