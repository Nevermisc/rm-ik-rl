# 证据索引

## 当前正式证据

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

## 复核原则

复核时不要只看汇总成功率，应同时检查：

1. 是否为独立、未用于调参的种子集；
2. 每个案例的报告是否完整；
3. 是否全部为仿真执行；
4. 动作哈希是否通过客户端校验；
5. 失败是未抓取、未到达、未释放、安全中止还是运行错误；
6. 运行参数是否与报告中的门槛和最大 chunk 数一致。
