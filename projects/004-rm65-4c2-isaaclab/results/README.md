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

`pick_place_dynamic_2cm.json`、`4cm.json`、`6cm.json`、`10cm.json` 去掉了“初始化在抓取位”，让机械臂从四个距离执行笛卡尔接近。`pick_place_dynamic_robustness.json` 汇总为 4/4，最小抬升 `0.03730 m`，最大落点误差 `0.00863 m`。这些测试仍在闭合前暂时关闭方块重力，放置时仍使用延迟平台碰撞和 50 mm 分离辅助。

`pick_place_contact_reference.json` 保存悬空辅助姿态的 `tool_l_2/tool_r_2` 接触参考。`pick_place_natural_contact_xminus4cm.json` 记录自然重力、条形支撑和 −40 mm 世界 x 修正下的双侧接触，左右力为 `0.05346/0.05835 N`。`pick_place_natural_lift_failure.json` 使用更强的夹爪参数后仍在抬升阶段失败，脚本在 `failure_stage=lift` 立即停止。`pick_place_natural_bridge.json` 将当前阶段明确汇总为 `bilateral_contact_pass_lift_fail`；它是需要继续解决的边界，不是通过项。
