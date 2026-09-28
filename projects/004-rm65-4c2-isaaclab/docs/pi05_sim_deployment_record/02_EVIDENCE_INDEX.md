# 证据索引

## 当前扩大样本证据

预注册 60-case 鲁棒性评测在修正无关 scripted IK 预计算后，按首次真实策略执行口径为 54 个成功、6 个失败，成功率 **90%**，全部报告齐全。相同 seed 的正式复现运行为 55/60，但有 1 个案例状态翻转，必须与重复性审计一起解读。

- [首次真实策略执行纠正证据（主结果 54/60）](../../results/rm65_pi05_robustness_v3_60_first_policy_execution_corrected_evidence.json)
- [正式复现运行紧凑证据（55/60）](../../results/rm65_pi05_robustness_v3_60_compact_evidence.json)
- [正式复现运行失败分类与分层统计](../../results/rm65_pi05_robustness_v3_60_failure_taxonomy.json)
- [正式复现运行释放/阶段分析](../../results/rm65_pi05_robustness_v3_60_release_analysis.json)
- [4-case 相同 seed 重复性审计](../../results/rm65_pi05_repeatability_audit_outer4_v1.json)
- [`robust_042` 精确首个策略观测对比](../../results/rm65_pi05_exact_initial_observation_repeatability_robust042_v1.json)
- [20 条件 × 3 次重复预注册计划](../../config/rm65_pi05_repeatability_plan_v1_20x3.json)
- [20×3 计划验证](../../results/rm65_pi05_repeatability_plan_v1_20x3_validation.json)
- [20×3 重复性矩阵正式结果（门禁失败）](../../results/rm65_pi05_repeatability_matrix_v1_20x3.json)
- [第 1/2/3 轮失败与安全中止分析](../../results/rm65_pi05_repeatability_v1_run1_failure_analysis.json)、[第 2 轮](../../results/rm65_pi05_repeatability_v1_run2_failure_analysis.json)、[第 3 轮](../../results/rm65_pi05_repeatability_v1_run3_failure_analysis.json)
- [`robust_008` 翻转精确对比](../../results/rm65_pi05_exact_initial_observation_repeatability_robust008_20x3_v1.json)
- [`robust_028` 翻转精确对比](../../results/rm65_pi05_exact_initial_observation_repeatability_robust028_20x3_v1.json)
- [`robust_042` 矩阵翻转精确对比](../../results/rm65_pi05_exact_initial_observation_repeatability_robust042_20x3_v1.json)
- [14 种图像稳定化方案离线筛查](../../results/rm65_pi05_policy_image_stabilization_screen_v1_20x3.json)
- [初始物理状态逐位一致探针](../../results/rm65_pi05_initial_physical_state_probe_v1_robust002.json)
- [renderer accumulation 重置探针](../../results/rm65_pi05_renderer_reset_probe_v1_robust002.json)
- [60-case 计划验证](../../results/rm65_pi05_evaluation_plan_robustness_v3_60_validation.json)

关键审计项：鲁棒性评测和重复性矩阵均为 60/60 报告齐全、`simulation_only=true`、`real_robot_command_sent=false`。20×3 矩阵状态一致率为 85%，3 个翻转；20/20 初始关节、夹爪和 noise 哈希一致，0/20 双相机与首动作哈希一致。重复矩阵复用了相同条件与 seed，只用于重复性审计，不能作为新的独立成功率确认。

## 初始正式证据

正式独立确认集：20 个案例，16 个成功，4 个失败，成功率 **80%**。

- [确认集紧凑证据](../../results/rm65_pi05_release_supervisor_confirmation_20_compact_evidence.json)
- [确认集失败分类](../../results/rm65_pi05_release_supervisor_confirmation_20_failure_taxonomy.json)
- [确认集释放分析](../../results/rm65_pi05_release_supervisor_confirmation_20_release_analysis.json)

关键审计项：

- `diagnostic_only=false`；
- 20/20 报告存在；
- 20/20 为 `simulation_only=true`；
- 没有真实机械臂命令；
- 策略种子与仿真种子和开发集无重叠；
- 4 个失败均为 `never_reached_target`；
- 其中 1 个由 `cube_outside_workspace_envelope` 安全规则中止。

## 开发/诊断证据

开发计划 120 chunk：17/20（85%），仅用于调参和定位，不作为最终独立确认结果。

- [开发集紧凑证据](../../results/rm65_pi05_release_supervisor_dev120_20_compact_evidence.json)
- [开发集失败分类](../../results/rm65_pi05_release_supervisor_dev120_20_failure_taxonomy.json)
- [开发集释放分析](../../results/rm65_pi05_release_supervisor_dev120_20_release_analysis.json)

## 确认集失败分布

### 按初始角度

| 角度（rad） | 成功/总数 |
|---:|---:|
| 0.65 | 5/5 |
| 0.75 | 4/5 |
| 0.85 | 3/5 |
| 0.95 | 4/5 |

### 按提示词

| 提示词类别 | 成功/总数 |
|---|---:|
| `grasp...` | 3/4 |
| `move...` | 4/4 |
| `pick...` | 3/4 |
| `pick up...` | 4/4 |
| `place block on target platform` | 2/4 |

这说明下一阶段应优先改善目标到达、抓取和搬运鲁棒性，特别关注 0.85 rad 附近姿态及 `place block on target platform` 提示词，而不是继续只调释放阈值。

## 关键 Git 提交

- [`203c9b9`](https://github.com/Nevermisc/rm-ik-rl/commit/203c9b9)：策略采样确定性与动作哈希校验。
- [`5d11315`](https://github.com/Nevermisc/rm-ik-rl/commit/5d11315)：仿真种子、观测/动作证据与相机差异诊断。
- [`009b15d`](https://github.com/Nevermisc/rm-ik-rl/commit/009b15d)：释放监督器、工作空间安全中止与 120 chunk 评测配置。
- [`da63c3b`](https://github.com/Nevermisc/rm-ik-rl/commit/da63c3b)：正式确认集和开发集紧凑证据。
- [`98de449`](https://github.com/Nevermisc/rm-ik-rl/commit/98de449)：缺失报告 fail-closed 与结构化预检失败。
- [`c707b7d`](https://github.com/Nevermisc/rm-ik-rl/commit/c707b7d)：pi0.5 模式跳过不会执行的 scripted-only 放置 IK 预计算。

## 复核原则

复核时不要只看汇总成功率，应同时检查：

1. 是否为独立、未用于调参的种子集；
2. 每个案例的报告是否完整；
3. 是否全部为仿真执行；
4. 动作哈希是否通过客户端校验；
5. 失败是未抓取、未到达、未释放、安全中止还是运行错误；
6. 运行参数是否与报告中的门槛和最大 chunk 数一致；
7. 相同 seed 重复时，观测哈希、动作哈希和最终状态是否一致。
