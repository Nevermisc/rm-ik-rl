# RM65-B + pi0.5 仿真部署记录

本目录用于持续记录 **pi0.5 在 RM65-B 机械臂 Isaac Lab 仿真环境中的部署、验证与优化**。这里保存的是可审计的工程结论和证据索引，不保存大型数据集、模型权重或完整运行日志。

## 当前结论

- 按“每个受影响案例第一次真正进入 pi0.5”的审计口径，纠正后的主结果为 **54/60（90%）**，95% Wilson 区间约为 **79.9%–95.3%**。
- 同一 checkpoint 和双 seed 的正式复现运行得到 **55/60（91.7%）**，但 `robust_042` 从失败翻转为成功，因此不能把 55/60 当作无条件更优的新独立结果。
- 60/60 报告齐全，全部为 `simulation_only=true`，没有向真实机械臂发送命令。
- 主结果的内圈/中圈/外圈分别为 **19/20、18/20、17/20**；6 个失败分为 5 个未到达目标和 1 个抬升不足。
- 4 个原 `unsafe_ik_branch_jump` 来自 pi0.5 模式不会执行的 scripted-only 放置轨迹，属于假安全拒绝；修复只跳过无关预计算，保留 scripted 模式的 0.75 rad 安全上限。
- 重复性审计中，4/4 初始关节、夹爪和显式噪声哈希一致，但 0/4 双相机首帧与首动作哈希一致，1/4 最终状态翻转。当前只证明了采样 seed 可复核，**没有证明端到端确定性**。

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
- [DECISIONS.md](DECISIONS.md)：关键工程决策及其理由。
- [STATUS.json](STATUS.json)：便于程序读取的当前状态快照。
- [CHANGELOG.md](CHANGELOG.md)：从本目录建立后持续追加的变更记录。

当前机器可读状态以 `STATUS.json` 为准；历史运行中途数字只用于监控，不作为正式结论。

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
视觉渲染重复性修复 + 策略失败数据闭环 + 全新确认
      ↓
真实机械臂影子模式/限速验证（尚未开始）
```
