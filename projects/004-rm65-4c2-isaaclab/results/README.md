# 验证结果说明

这里保存脚本实际生成的机器可读报告。运行：

```bash
python3 scripts/summarize_stage_results.py
```

脚本会重新检查所有关键断言，并生成 `stage_summary.json`。

`articulation_smoke_gravity.json` 的 `status` 有意保留为 `fail`。它记录 4C2 原始物理模型在全部刚体启用重力时的已知失败，用于防止以后误删重力隔离措施。阶段汇总只有在这个诊断仍被识别为已知失败、其余验收项全部通过时，才会输出 `pass_with_known_limitations`。

`diagnostic_*.json` 记录失败原因的隔离实验：移除地面、1 kHz 时间步、惯量正则化以及只隔离四个远端指节都不能通过。正式 `articulation_smoke_arm_gravity.json` 只隔离六个活动指节，保留 RM65、4C2 基座和两个固定支座的重力。

`usd_physics_inventory.json` 检查实例代理内的刚体、碰撞体、应用的 Physics API、子 Mesh 和 `convexHull` 近似；`gripper_aperture_test.json` 验证几何开合方向。`gripper_close_stability.json` 使用外移 10 mm 的安全默认位姿，只证明静态闭合保持有限数值。`diagnostic_gripper_base_contact.json` 记录零偏移时 `tool_base_link` 接触 `0.136 N` 并把测试块推出 `0.04797 m`，左右指尖接触仍为 0 N。两份结果共同说明当前还没有稳定双侧夹持。

`contact_pads_*.json` 和 `gripper_contact_pads_center.json` 记录反算碰撞垫的构建、导入、物理清单、关节/IK/到位回归及五个静态接触位置。`gripper_contact_pad_robustness.json` 汇总为 5/5。`gripper_contact_transport*.json` 在双侧接触后恢复物体重力，记录中心和横向 ±2 mm 的三次抬升；`gripper_transport_robustness.json` 汇总为 3/3。运输测试从已经位于指间的悬浮物体开始，不包含桌面拾取和放置。

`pick_place_robust_0p6.json`、`0p8.json`、`1p0.json` 记录三种底座转角下的辅助搬运与放置状态机，`pick_place_assisted_robustness.json` 汇总为 3/3。每份报告都明确写入 `unassisted_full_task_complete=false`：测试从抓取姿态初始化，闭合前关闭物体重力，转运后才启用平台碰撞，并用 50 mm 向下分离解除释放卡滞。它证明后半程状态机可运行，不证明无辅助完整抓取或 π0.5 闭环。
