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

`pick_place_contact_reference.json` 保存悬空辅助姿态的 `tool_l_2/tool_r_2` 接触参考。`pick_place_natural_contact_xminus4cm.json` 记录自然重力、条形支撑和 −40 mm 世界 x 修正下的双侧接触，左右峰值为 `0.05346/0.05835 N`。`pick_place_natural_lift_failure.json` 保存当时更强夹爪参数仍在抬升阶段失败的结果，`pick_place_natural_bridge.json` 汇总这段历史边界。后续实验已经发现这些峰值不是持续接触，并用下面的新证据推进到自然重力抬升；旧失败文件继续保留用于记录诊断过程。

`natural_close_sweep.json` 用当前力和最近窗口均值重新检查原始 `25×10×20 mm` 经验垫；0.45 至 0.75 rad 共 7 次都没有持续双侧当前接触。`wide_pads_urdf_report.json` 与 `wide_pads_import_report.json` 记录独立的 `40×14×18 mm` 候选碰撞垫资产，`natural_wide_pads_close_065.json` 记录该资产的持续双侧接触。

`natural_pick_place_single_pass.json` 是 0.8 rad 的单次自然重力辅助通过证据：方块抬升 `0.03907 m`，最终误差 `0.002918 m`。`natural_pick_place_0p6.json`、`0p8.json`、`1p0.json` 与 `natural_pick_place_robustness.json` 是 80 mm 释放分离辅助下的三角度复测；抓取和抬升 3/3，但完整任务仅 1/3，所以汇总有意保留 `status=fail`。`natural_unassisted_release_failure.json` 记录夹爪张开并向上撤离后仍带走方块的失败。所有这些实验都为仿真脚本专家，`pi05_used=false`、`real_robot_command_sent=false`，并保留报告中列出的开发辅助。

`natural_place_descent_collision_failure.json` 记录目标支座在下降前启用碰撞时的路径受阻：末端未完成 100 mm 下降，放置关节误差升高，方块被挤离目标。`natural_place_descent_0p6.json`、`0p8.json`、`1p0.json` 在下降完成后才启用旋转窄支座碰撞，再张开夹爪并自然沉降；`natural_place_descent_robustness.json` 汇总为 3/3，最大最终误差 `9.48 mm`。该阶段没有直接改写释放时的方块位姿或速度，但仍包含机械臂/活动指节重力隔离、经验宽碰撞垫、专用窄支座和延迟碰撞，因此状态是 `pass_with_simulation_assistance`，不是无辅助完整任务。

`top_down_reachability_diagnosis.json` 记录顶部抓取最初不可达的原因：机器人基座错误地位于世界 `z=0`，严格顶部腕部目标达到 `z=0.873 m`；修正为 `z=0.65 m` 安装面并进行世界/基座坐标换算后，严格顶部 IK、10 段接近和持续双侧接触通过。

`top_down_kin_*.json` 记录修复前的下降 IK 路点。0.7 rad 的关节 3 和 1.0 rad 的关节 5 出现超过 3 rad 的等价分支跳变；`top_down_kin_fixed_*.json` 验证“在未旋转基座坐标求下降，再只旋转关节 1”的修复把最大相邻路点变化降到 `0.04031 rad`。`top_down_1p0_failure_diagnosis.json` 汇总失败、根因和修复结果，原始 0.7/1.0 物理失败报告继续保留。

`top_down_full_gravity_0p6.json`、`0p8.json`、`1p0.json` 使用严格顶部抓取、宽目标平台和全重力物理。机械臂、六个活动夹指和方块都没有关闭重力，释放时不注入方块位姿或速度。`top_down_full_gravity_robustness.json` 汇总为 3/3：最小抬升 `39.57 mm`，最大最终误差 `17.56 mm`，最大释放漂移 `2.35 mm`，三次均有 `unassisted_full_task_complete=true`。它仍使用脚本专家、假设的 0.65 m 安装高度和未经实物标定的宽碰撞垫，`pi05_used=false`。
