# RM65-B + pi0.5 仿真部署记录

本目录用于持续记录 **pi0.5 在 RM65-B 机械臂 Isaac Lab 仿真环境中的部署、验证与优化**。这里保存的是可审计的工程结论和证据索引，不保存大型数据集、模型权重或完整运行日志。

## 当前结论

> **收尾 .044（覆盖下文所有待执行表述）**：源限位恢复后的 `native_surface_source_limits_001` 在 close_005 完整空手开合 PASS；不是夹物或 pi0.5 成功。217 CPU 测试通过，新 89 文件证据已异机 SHA 校验备份。用户要求立即交接，已停止新增实验、删除 rm65 自动推进；下次以根目录 `RM65_PI05_NEW_CHAT_HANDOFF_ZH.md` 为统一入口。详见[最新审计](MODEL_SOURCE_AND_PIPELINE_AUDIT_ZH.md)及[状态](ITERATION_STATUS.json)。

> **当前 .041（覆盖以下旧状态）**：官方 RM65-B 源 URDF/STL 已匹配；13 USD 关节帧与采样轴方向通过，原生随动限位差异仍待修。三次原生开合失败后，经源孔面证据处理内部连接，再直接查到碰撞凸包的虚假重叠；统一精度候选消除了所测连杆重叠，close_004 正在可见动态验证。207 项 CPU 测试通过。新 checkpoint 尚未训练，不能宣称日用品部署成功。详见[最新审计](MODEL_SOURCE_AND_PIPELINE_AUDIT_ZH.md)与[逐次日志](HOUSEHOLD_GENERALIZATION_LOG.md)。今日 21:00 截止，20:40 起收尾；不使用下面历史版本的等待/完成表述判断当前状态。

> **当前 .032**：[从源 URDF/USD 到训练/推理的正式流程审计及大白话](MODEL_SOURCE_AND_PIPELINE_AUDIT_ZH.md)。已确认方块反推隐形垫、旧数值状态未进入 pi0.5 网络两项根本问题；新原生碰撞候选已建、两次动态开合 FAIL，新独立状态输入配置通过测试但未训练。176 项 CPU 回归通过，新原生资产/失败试验已有异机校验备份。用户授权工作至今日 21:00，20:40 起收尾；下列版本均是历史，不覆盖此结论。

> 当前主动推进 `household-generalization.020`：[全链路审计与正式/通俗说明](HOUSEHOLD_GENERALIZATION_AUDIT_ZH.md)，[逐次日志](HOUSEHOLD_GENERALIZATION_LOG.md)。审计不仅确认旧数据全是方块，还发现按方块反推的附加碰撞垫与原手指可见表面分离约 6 cm，导入 USD 也确认隐藏碰撞盒仍开启，已默认阻止继续用它采集日用品。香蕉、记号笔脚本通过只代表旧代理模型，不证明原生夹爪能力。下一优先级是另建/验证正确夹爪碰撞模型；固定相机已实测，两批原始证据已独立校验备份，149 项 CPU 测试通过，尚未训练新 pi0.5。用户授权持续推进；下列旧阶段等待状态及旧成绩不代表当前目标已完成。

> 最新可见阶段 `household-visible.012` 已收尾：[正式版 + 大白话 + 代码结构](HOUSEHOLD_VISIBLE_HANDOFF_ZH.md)，[逐步日志](HOUSEHOLD_VISIBLE_ITERATION_LOG.md)。托台外移 8 cm；香蕉脚本抓放有 3 次开发通过，其中 1 次目标托台从初始即有碰撞。不是 pi0.5 推理或日用品部署验收。41 项测试、9 项几何检查通过，原始数据已有独立校验备份。用户要求同类型工作只做一次可见验证，避免重复开窗；本轮结果窗口暂时保留，物理已暂停，等待下一阶段确认。

> 2026-09-30 真实外观日用品阶段已限时收尾：[正式版 + 大白话交接](HOUSEHOLD_SESSION_HANDOFF_ZH.md)，[逐步迭代日志](HOUSEHOLD_OBJECT_ITERATION_LOG.md)。四类纹理资产加载/落地通过，但日用品抓取未通过；空中驱动模式对照改善了夹爪闭合跟踪，尚未用于正式抓取或模型部署。按用户要求等待确认，不自动继续。

> 2026-09-30 路线已调整：以[多物体仿真路线](MULTI_OBJECT_ROADMAP_ZH.md)为后续主线；已实现开发入口并运行几何体/机械臂测试，实际结果与未解决项见[多物体迭代日志](MULTI_OBJECT_ITERATION_LOG.md)。尚未通过新物体抓取验收。v5 最新方块结果见 [V5_SIMULATION_DEPLOYMENT.md](V5_SIMULATION_DEPLOYMENT.md)，下列早期结果保留为历史证据，不代表当前版本或新目标完成度。

- 按“每个受影响案例第一次真正进入 pi0.5”的审计口径，纠正后的主结果为 **54/60（90%）**，95% Wilson 区间约为 **79.9%–95.3%**。
- 同一 checkpoint 和双 seed 的正式复现运行得到 **55/60（91.7%）**，但 `robust_042` 从失败翻转为成功，因此不能把 55/60 当作无条件更优的新独立结果。
- 60/60 报告齐全，全部为 `simulation_only=true`，没有向真实机械臂发送命令。
- 主结果的内圈/中圈/外圈分别为 **19/20、18/20、17/20**；6 个失败分为 5 个未到达目标和 1 个抬升不足。
- 4 个原 `unsafe_ik_branch_jump` 来自 pi0.5 模式不会执行的 scripted-only 放置轨迹，属于假安全拒绝；修复只跳过无关预计算，保留 scripted 模式的 0.75 rad 安全上限。
- 重复性审计中，4/4 初始关节、夹爪和显式噪声哈希一致，但 0/4 双相机首帧与首动作哈希一致，1/4 最终状态翻转。当前只证明了采样 seed 可复核，**没有证明端到端确定性**。
- 预注册的 **20 条件 × 3 次**重复性矩阵已完成：60/60 报告有效，三轮分别为 17/20、16/20、16/20；只有 17/20 条件状态一致（85%，门槛 95%），`robust_008/028/042` 共 3 例翻转（门槛最多 1 例），因此重复性门禁明确失败。
- 20/20 条件的初始关节、夹爪和显式噪声哈希一致，但双相机首帧与首动作均为 0/20 一致。额外的单 chunk 探针进一步确认方块、腕部和腕部相机六组初始位姿数组逐位一致而图像仍变化，问题已定位到 RTX 渲染输出。
- 14 种轻量量化/模糊方案均未使双相机首帧完全一致；显式重置 renderer accumulation 也未消除差异，所以两者都不进入正式控制基线。

## 目录说明

- [01_IMPLEMENTATION_SUMMARY.md](01_IMPLEMENTATION_SUMMARY.md)：已经完成的技术工作及关键设计。
- [02_EVIDENCE_INDEX.md](02_EVIDENCE_INDEX.md)：正式结果、诊断结果、Git 提交和复核方法。
- [03_OPTIMIZATION_BACKLOG.md](03_OPTIMIZATION_BACKLOG.md)：按优先级整理的改进路线和验收标准。
- [04_SYSTEM_ARCHITECTURE.md](04_SYSTEM_ARCHITECTURE.md)：策略、仿真、控制与证据链的整体结构。
- [05_REPRODUCTION_RUNBOOK.md](05_REPRODUCTION_RUNBOOK.md)：从环境检查到正式评测和报告生成的操作手册。
- [06_EVALUATION_PROTOCOL.md](06_EVALUATION_PROTOCOL.md)：开发集、确认集、成功条件和防止数据泄漏的规范。
- [07_REAL_ROBOT_GATE_CHECKLIST.md](07_REAL_ROBOT_GATE_CHECKLIST.md)：真机前置条件和当前阻塞项。
- [08_NEXT_EXPERIMENT_PLAN.md](08_NEXT_EXPERIMENT_PLAN.md)：下一阶段 60 条新种子评测和失败数据闭环计划。
- [09_ROBUSTNESS_RESULTS.md](09_ROBUSTNESS_RESULTS.md)：60-case 正式结果、置信区间和失败解释。
- [10_ENGINEERING_ITERATION_LOG.md](10_ENGINEERING_ITERATION_LOG.md)：逐个代码更新记录版本、计划、问题、原因、实现与验证。
- [DECISIONS.md](DECISIONS.md)：关键工程决策及其理由。
- [STATUS.json](STATUS.json)：便于程序读取的当前状态快照。
- [ITERATION_STATUS.json](ITERATION_STATUS.json)：便于程序读取的当前工作版本和下一步。
- [CHANGELOG.md](CHANGELOG.md)：从本目录建立后持续追加的变更记录。

当前机器可读状态以 `ITERATION_STATUS.json` 和 `STATUS.json` 的 `current_generalization_audit` 为准；`current_visible_session`、`current_household_snapshot` 及旧方块评测是历史快照。历史运行中途数字只用于监控，不作为正式结论。

## 记录规则

此后每次影响仿真结果的改动，都应在 `CHANGELOG.md` 追加一条记录，并至少包含：

1. 日期与 Git 提交；
2. 改动目的和假设；
3. 改动内容；
4. 使用的策略种子、仿真种子和评测规模；
5. 结果与失败分类；
6. 对应证据文件；
7. 是否能进入下一阶段。

历史结果只追加、不覆盖。开发/诊断集与正式确认集必须分开标记，禁止用调参过程中反复查看过的样例冒充最终独立验证。

## 阶段边界

```text
策略服务确定性
      ↓
仿真场景可复现性
      ↓
闭环执行与安全监督
      ↓
独立种子仿真门槛
      ↓
60-case 鲁棒性评测（点估计通过）
      ↓
20×3 重复性门禁（失败：85%，3 个翻转）
      ↓
视觉鲁棒性训练/渲染诊断 + 策略失败数据闭环 + 全新确认
      ↓
真实机械臂影子模式/限速验证（尚未开始）
```
