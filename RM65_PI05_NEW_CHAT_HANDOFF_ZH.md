# RM65-B + 4C2 + π0.5：统一交接入口

更新：2026-09-30 19:20（Asia/Singapore，收尾核验窗口）。工作版本：**household-generalization.044**。

**当前阶段：最终原生候选已通过空手开合；原生夹物、多日用品 π0.5 闭环尚未完成。** 不把历史方块分数当成当前验收，不提供无依据的完成百分比。

用户最新要求立即收尾，覆盖此前“自主工作到 21:00”。已停止新增实验、删除 `rm65` 心跳；新对话不要自动继承旧截止或恢复定时任务。

## 1. 最终目标与验收边界

让 π0.5 根据图像、语言和关节状态，控制 RM65-B + 4C2 在 Isaac Lab 中抓取、搬运、稳定放置**真实外观的多种日常用品**；不是要求这只机械臂无条件复现 π0.5 的全部预训练技能。

必要验收：

- 身体可信：源几何、安装、轴/限位、传动、惯量、碰撞可追溯；重力和实际质量有效，无隐藏加长手指、缩物体或吸附捷径。
- 任务完整：原生指面实际接触、持续离地、搬运、自然释放和放稳；失败/碰撞/越界如实计入。
- 模型确实控制：checkpoint、输入/输出、归一化、时间语义一致；纯策略、脚本专家和任务真值辅助分开统计。
- 泛化独立验收：按物体/物理轨迹分组，使用未参与训练/调参的物体与摆放，多次重复、逐类报告。**新日用品对象清单、样本量及数值通过阈值尚未冻结**；旧方块 80%/90% 不能直接套用，必须先定协议再看成绩。
- 可复现：代码/配置/数据/资产/权重身份绑定，失败保留，独立备份且发布包可恢复。完整恢复运行尚待验证。

仅仿真、数据、训练、评测；**不执行真机命令，不覆盖 v2–v5 checkpoint，不将原始数据/纹理/网格/权重提交 Git**。真机部署需另行授权和安全验收。

## 2. 权威位置与版本

```text
W = C:/Users/95380/Documents/ChatGPT/robot learning
L = W/remote_work_7baaa1a/project                         Windows 同步镜像
SSH = chengyu@100.116.242.82
R = /home/chengyu/robot-learning/rm-ik-rl                权威 Git 仓库
P = R/projects/004-rm65-4c2-isaaclab
D = P/docs/pi05_sim_deployment_record
OpenPI = /home/chengyu/robot-learning/openpi
IsaacLab = /home/chengyu/robot-learning/IsaacLab
Isaac Sim = /home/chengyu/isaac-sim-5.1.0
GitHub = https://github.com/Nevermisc/rm-ik-rl （main）
```

代码/证据已推送 **ff9aefdbbd3102c95e75e38f520197438894f305**（.033–.044，43 文件）；前序 `6d5a1c7` 为 .021–.032。本入口另作纯文档提交，最新 HEAD 必须现场读取，不把代码提交号当永久最新 HEAD。
OpenPI HEAD：`15a9616a00943ada6c20a0f158e3adb39df2ccac`；RTX 4080 SUPER 16 GB。

`P/generated` 指向 `/home/chengyu/robot-learning/004-rm65-4c2-isaaclab/generated`。
夹爪源在 `/home/chengyu/robot-learning/004-rm65-4c2-isaaclab/external/4C2`，**不是 P/external**；手臂源在 `R/assets/RM65-B`。

## 3. 已完成且有证据的工作

表内结果路径相对 P；原始运行/资产不进 Git。

| 工作 | 当前有效结论 | 关键证据 |
|---|---|---|
| 来源/历史审计 | RM65-B URDF 和 7 STL 与固定版官方库逐字节一致；检查 11 派生 URDF、13 USD，未发现派生手臂尺寸被改来凑成功 | `results/official_model_reference_001.json`、`results/model_lineage_audit_002.json`、`results/model_usd_lineage_audit_001.json` |
| 关节和原生碰撞 | 13 资产采样关节帧/轴核对；真实 Mesh 碰撞、1 主动+5 mimic。四对内部过滤有源枢轴/同轴孔证据，其余自碰撞和外部碰撞保留；统一精度修正凸包虚假重叠 | `results/imported_joint_frames_002.json`、`results/native_linkage_pivots_002.json`、`results/native_collision_fidelity_002.json` |
| 空手动态 | close_001–003 失败；精度候选 close_004、恢复源随动限位的 close_005 通过。最终 2460 步，保持误差 0.004850857 rad，随动差 0.000036570 rad，重力/原质量/单驱动检查通过 | `results/native_surface_close_005.json`、`results/native_surface_source_limits_001_import_audit.json` |
| 状态输入 | 证实旧数值关节状态未作为条件进入 π0.5 网络；新增独立 state_v1 配置开启离散状态、200 token，输入/转换测试通过。**未贯通完整入口、未训练** | `results/pi05_state_path_audit_001.json`、`openpi_extension/rm65_training_config.py` |
| 测试/保全 | 217 CPU pytest 通过；原生备份 001/002 的异机 SHA 一致。不是完整恢复运行证明 | `results/cpu_tests_043.log`（未入 Git）、`results/native_audit_backup_001_independent.json`、`results/native_audit_backup_002_independent.json` |

最终候选：`P/generated/native_surface_source_limits_001/native.usd`。
源 URDF SHA256：`c362f677ee792a5475c293617b6241ca17566b4dbaf87237d459afe2d307ff74`。
**只验证了一种固定手臂姿态下的空手动作；报告仍为 pi05_used=false、training_ready=false。没有原生外部夹物/搬运或新日用品策略成功证据。**

## 4. 历史结论、已推翻内容与失败重试边界

- **旧方块/香蕉/记号笔通过不等于原生夹爪通过**：附加隐形碰撞垫按 40 mm 方块和闭合角反投影，与可见手指分离约 6–7 cm。旧 v2–v5 分数保留为代理模型历史，不删改、不作为当前验收；旧垫日用品入口已默认阻止，勿绕过继续采集。
- **旧数据不具备多物体覆盖**：审计的 150 train + 9 validation 都是同尺寸方块；换指令措辞不是泛化。新增通用图像增强也不是缺失功能。
- **state 字段存在不等于网络用了它**：旧 `pi05=True, discrete_state_input=False` 未将状态送入网络；外部差分/绝对动作转换仍使用状态，不能说系统完全没用。不得给旧 checkpoint 直接偷换新输入语义。
- **失败候选勿盲重跑**：soft mimic 的 close_001 跟随失配；rigid close_002 仍卡；四对连接过滤的 close_003 仍被右 r1–r2 卡住。实际凸包审计和全夹爪统一精度修正后才通过，不能凭反力再加过滤、加力或关重力。重跑仅限有新依据的单因素对照/回归。
- `native_surface_v1/v2/v4` 是导入/检查工具失败产物，不用于新抓取。`imported_joint_frames_001` 有检查范围误判，采用修正后的 `_002`；`native_cooked_shapes_001` 的 null 参数不能当已知有效参数。
- 旧开口 16.8–47.7 mm 属于附加垫；原生理想几何约 70 mm→0.093 mm，**不是动态可抓尺寸认证**。
- 官方参考 EG2-4C2 为 7 links、约 94.3 g，用户源为 9 links、236.2 g，厂家标称约 231 g。未经匹配 CAD/传动证据，不因“同名/官方”就直接替换质量、坐标或结构。
- 历史确定性噪声已在 `203c9b9` 等实现并有代码，不要照旧交接文件重复开发；旧释放监督仍含任务真值辅助，不能报纯策略能力。

详细证据和版本历史见 `D/HOUSEHOLD_GENERALIZATION_LOG.md`、`D/MODEL_SOURCE_AND_PIPELINE_AUDIT_ZH.md`。更早 v2–v5 记录仍在 D。详细文档中的旧待执行表述由其 .044 收尾段及本入口覆盖。

## 5. 未完成/待核实

1. 原生指面外物接触、夹持/自然释放、不同腕姿及搬运未验证；当前 1 Nm 驱动和刚性 mimic 是诊断设定，不是厂家传动/夹持力标定。
2. 源六指节与手臂 link_1 的质心超出可见网格包围盒线索未解；不凭均匀网格质心直接改惯量。法兰 PDF 不含完整转接件，夹爪安装变换待核实。四对内部过滤是有几何依据的闭链抽象，非硬件动力学认证。
3. `config/household_camera_rig_v2.json` 有旧场景画面，最终原生多摆放视野待验证；有效多日用品数据、分组留出协议和新 checkpoint 均未完成。
4. 独立 state_v1 的 train/norm/serve/manifest 绑定、token 预算和 16 GB 显存 smoke 未完成；旧 policy-window 删保持帧但沿用 fps 的时间语义风险待新协议解决。
5. 新的纯策略留出验收和完整恢复发布包未完成。不能保证后续每次调整必然提高成功率。

## 6. 关键文件、备份、未提交改动

核心代码均在 P：

```text
scripts/build_native_gripper_candidate.py / import_native_gripper_candidate.py
scripts/derive_native_rigid_mimic.py / derive_native_linkage_filter.py
scripts/derive_native_collision_precision.py / restore_native_follower_limits.py
scripts/run_native_gripper_diagnostic.py                    可见空手检查
scripts/audit_robot_model_lineage.py / audit_robot_usd_lineage.py
scripts/audit_imported_joint_frames.py / audit_native_linkage_closure.py
scripts/audit_native_cooked_shapes.py / audit_native_collision_fidelity.py
scripts/audit_pi05_state_path.py / backup_native_audit_batch.py
openpi_extension/rm65_training_config.py / rm65_policy.py   新旧配置分离
scripts/convert_expert_episodes_to_lerobot.py               训练准入
D/ITERATION_STATUS.json / STATUS.json / HOUSEHOLD_GENERALIZATION_LOG.md
```

原始证据：`P/outputs/native_surface_close_001` 至 `_005`（report、telemetry、部分截图）；凸包 `P/outputs/native_cooked_shapes_001` 至 `_003`；官方参考 `P/outputs/official_model_reference_001`。

两批原生 tar/index 在 `/home/chengyu/robot-learning/rm65-backup-staging` 和 `W/RM65_DATA_BACKUP_DO_NOT_GIT/native_audit_2026_09_30`。
最新 `rm65_native_20260930_002.tar`：89 文件、49,684,480 bytes；SHA256 `36d52032552b287de31baff173c862bffd3a172f2a78ff135e6c494c5b05ef34`。老数据/权重备份仍保留，本轮未重新证明全部可恢复。

收尾 Git 状态：

- R：本轮代码/证据已提交推送；原有 **`P/results/rm65_pi05_v3_backup_gate.json` 未提交修改保留**。另有 84 个既有未跟踪文件（旧 results、scripts_sync_staging 等），未清理或纳入本轮；交接文档提交前暂存区为空。
- OpenPI：既有 `examples/libero/Dockerfile` 修改及旧未跟踪工具/override 保留，未动。准确全清单下次用 `git status --short` 复核。
- Windows W 另有 Git 和大量既有脏文件，本轮未 stage/push 此仓库；L 是同步镜像，不是权威 checkout。本入口在 Windows Git 仍未跟踪，远端同名入口另受版本管理。勿使用 `git add .`、reset/clean 或覆盖用户修改。
- 原入口全文已保存在 `W/RM65_DATA_BACKUP_DO_NOT_GIT/handoff_archive/RM65_PI05_NEW_CHAT_HANDOFF_ZH.before_20260930_wrap.md`，仅历史档案，不是第二个继续入口。

## 7. 进程与定时任务

2026-09-30 19:15 左右核验：GPU compute 列表为空；无本任务 Isaac Python、训练或策略服务进程，8016/8017 无监听。旧 GNOME 终端 bash PID `531863/533482/537553/540139/541291` 等待 Enter，**不是仍在仿真**；未强关桌面，PID 下次可能变化。

`rm65` 10 分钟心跳已删除；本地未发现剩余 rm65/rm65-pi0-5 automation.toml。其他无关任务未变更，不会继续执行旧 21:00 安排。

新重大动作需从实验室桌面终端打开可见窗口并核验 telemetry：`DISPLAY=:1`，`XAUTHORITY=/run/user/1000/gdm/Xauthority`。同类型只需一次可见验证，不为截图重开；活跃实验每几分钟核验，区分完成暂停。只读审计不需动作窗口。每次代码/配置更新同步工作版本、问题/原因/方法/结果和泛化风险。

## 8. 下一步优先三件事

1. **原生真实接触验收**：核对最终资产哈希、runtime 限位/重力/质量，再以跨尺寸、统一条件的有限夹持/自然释放检查确认 l3/r3 原面接触；失败先分几何/碰撞/传动原因。再选物理上可行的真实日用品，不无限纠缠明显不适配夹爪的物体。
2. **冻结通用数据/接口合同**：固定相机、多摆放、按物体/轨迹分组留出，保持采样时间真实；贯通独立 state_v1 的训练、归一化、服务与 manifest，做小型显存验证。模型/数据/备份门禁通过后才采有效训练集，诊断数据不可混入。
3. **独立新训练与留出验收**：从明确基础权重训练新 checkpoint、不覆盖旧版；提前冻结对象/样本量/成功率/重复性标准，分别报告纯策略与有辅助结果。通过后形成可恢复发布包，失败保留分类，不偷换目标或分数。

## 可直接发到新对话的启动提示词

请完整读取 `C:/Users/95380/Documents/ChatGPT/robot learning/RM65_PI05_NEW_CHAT_HANDOFF_ZH.md`，作为唯一交接入口，再核对实验室 Git、ITERATION_STATUS.json、最新报告和进程。当前 .044，代码/证据已推送 ff9aefd；最终原生 source_limits_001 仅空手开合通过，尚无原生夹物或新日用品 π0.5 成功，旧方块分数是代理模型历史。请先简述核实后的现状，再从文末优先第 1 项安全推进，保持可见仿真和逐次中文日志。只做仿真/数据/训练/评测，不执行真机、不覆盖 v2–v5、不提交原始资源，保留既有脏文件。不沿用旧 21:00 截止、不自行恢复定时任务；无法确认的标待核实，不把脚本或空手 PASS 当部署完成。
