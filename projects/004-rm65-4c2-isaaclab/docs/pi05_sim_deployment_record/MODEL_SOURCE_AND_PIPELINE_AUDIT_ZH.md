# 当前原生控制、真实物体与策略链审计（household-generalization.059）

007使用源六轴effort上限三档脚本带物运动通过；marker001实际携带但不满足冻结flat-inner持续接触；marker002精度对照在开手阶段倾倒，随后空手。两次真实marker均FAIL。所有旧源、失败和checkpoint保留，无π0.5/训练准入。

控制映射与独立state_v1身份检查已具备CPU证据；真实相机与完整trace已保存。继续先解释初始支承、评估稳定放置和原生可接近性，完成D盘独立备份，再按真实时间/相机/数据合同贯通新策略链。以唯一根交接和ITERATION_STATUS最新字段为准。下方历史按版本保留，不把旧的待办或代理模型分数当当前native结论。

---

# 当前原生接触与策略链审计（household-generalization.054）

2026-09-30，权威Git HEAD仍d4bbf0e；本轮.045–.054未提交。原生加载失败的有限对照已推进到实际带物抬升、横移和释放通过，π0.5部署仍未完成。

- 004：三宽全部在撤支撑前掉落；原面及保存cooked实体进入物体得到证实。
- 005：只把临时场景solveArticulationContactLast设True，其余物理保持，三宽无支撑4s和自然释放全通过；所选实际姿态原面无三角交叠。
- 006：相同源/物理，实际物体抬41.78–41.85mm、第二段搬63.75–63.84mm、开手下落约192mm，全720帧原双面接触且无外部承托；不是空手运动，不是π0.5策略。
- 独立审计绑定完整trace、执行源码、manifest与报告；427 CPU tests通过，所有失败记录保留。质量/惯量/几何与旧checkpoint未改变。
- 300Nm臂与1Nm夹爪仍诊断设定，源COM/安装/传动未硬件校准；单路径每宽一次，不提供跨物体或真实机器人成功率。
- 下一阶段详见NATIVE_DATA_CONTRACT_DRAFT_ZH.md；所有训练准入仍关闭，旧相机/时间语义/旧checkpoint不能直接偷换为native state_v1。

具体证据：results/native_contact_004_005_comparison_001.json、native_contact_005_geometry.json、native_contact_006_analysis.json、native_contact_resume_postflight_002.json。最新原始备份receipt见ITERATION_STATUS.json。

以下历史审计按版本保留；“尚无原生保持/搬运”等旧表述仅适用于当时版本，以本节和唯一根交接入口为准。

---

# 原始模型、历史改动与正式部署流程审计

日期：2026-09-30；工作版本：household-generalization.044；前序已推送基线：6d5a1c7（.021–.032）。
本文件是阶段审计，不是项目成功验收。用户已要求立即收尾交接，替代此前 21:00 自主工作安排；停止新增实验，rm65 心跳已删除。

**收尾有效结论**：最终候选 `generated/native_surface_source_limits_001` 已恢复五随动源限位，close_005 空手开合全部检查 PASS：2460 步、最大保持误差 0.004850857 rad、随动差 0.000036570 rad、六活动指自接触峰值为 0。前三次失败与第四次通过均保留。没有进行原生夹爪外部夹物测试、没有新日用品训练；217 CPU 测试通过。最新 89 文件/49,684,480-byte 归档已逐成员核验并有 Windows 独立 SHA 一致副本，完整解包重建仍未验证。

## 一、当前结论

1. **有从方块结果反推结构的历史改动**，且进入了正式方块采集/评测入口：附加的隐形碰撞垫，不是原生手指表面。
2. **当前 RM65-B URDF 及 7 份网格已与睿尔曼官方固定版本逐字节匹配**；未发现通过改手臂尺寸凑结果。夹爪来源不同，不能把相同型号名当作坐标/惯量完全一致。
3. 新原生候选去除了附加垫、保留原网格/惯量和五个随动关节，修复碰撞 API 层级。前三次失败，第四次统一精度候选已通过 2460 步空手开合；**仍不能用于抓取教材或部署验收**，需要恢复源限位再检查实际夹物接触。
4. 官方流程对照还发现独立的模型接口问题：旧配置关闭了 π0.5 的离散状态输入，数值关节状态没有作为条件进入网络。新配置候选恢复此通路，旧 checkpoint 的输入语义未偷换。
5. 当前瓶颈是可信仿真身体与输入合同，而非单纯再训若干步。没有新的日用品策略 checkpoint，也没有原生夹爪日用品抓取成功结论。

## 二、模型从哪里发生了变化

已检查当前两份源 URDF、16 份源 STL、11 份派生 URDF 和 13 份 USD。结果见 results/model_lineage_audit_002.json、model_usd_lineage_audit_001.json；检查器只读，USD 执行 0 物理步。

| 层/版本 | 已核实事实 | 判断及影响 |
|---|---|---|
| 当前 RM65-B 源 | 7 link；派生版本中机械臂结构无语义差异；源 mesh SHA 一致 | 未发现通过改手臂尺寸凑抓取结果；没有硬件尺寸/装配标定证据 |
| 当前 4C2 源 | 9 link，6 个活动关节；1 主动、5 个 1:1 mimic，轴方向承载正负关系 | 源定义不能直接等同于真实传动已正确模拟 |
| software 版本 | 删除 5 个 mimic | 将机械传动变成六路独立目标驱动，不能等同一个真实电机 |
| physics_proxy 版本 | 单独把 9 个夹爪部件惯量/质量正规化 | 是历史诊断版本；不可误称所有 wide_pads 版本都用了此质量下限 |
| contact_pads / tip_collision / wide_pads | 额外碰撞盒附着 l_2/r_2，无对应 visual；wide_pads 为 40×14×18 mm | Git 06b44e2 明文按 40 mm 方块、q=0.65、每侧 2 mm 压缩反投影；4a4794a 扩大尺寸。不是 CAD 接触面 |
| 原生新候选 URDF | 与当前源合并结构相同、16 个原网格碰撞、5 mimic，无额外垫 | 源一致是必要条件，不足以证明动力学正确 |
| 原生新候选 USD v3 | 16 个碰撞 API 从 Xform 移到实际子 Mesh；原几何未移动/缩放；自碰撞开、仅主关节驱动 | 静态审计通过，接触和重力运行证据存在；空手闭合仍失败 |
| rigid_001 | 仅将 importer 添加的 mimic 柔性参数 25 Hz/0.005 改为 0/0 的理想刚性关系 | 跟随误差改善但仍卡滞；这是源运动学假设的对照，不是已标定真实传动 |
| linkage_001 | 四对内部连接过滤，经 19 姿态固定枢轴与实际同轴孔面双重核对；其余/外部碰撞保留 | 四对异常反力消失，右 r_1–r_2 仍卡住，不自动继续加过滤 |
| precision_001 | 九份原生夹爪网格统一提高凸分解精度，源 STL/惯量/驱动/过滤不变 | 所测左右连杆在七姿态均无凸包相交；close_004 空手开合通过，未夹物 |

### 官方来源与装配边界

已固定 [RealManRobot/rm_models b63dddb](https://github.com/RealManRobot/rm_models/tree/b63dddb20b7620d14cfff32678de60bb3a201ebc)，下载 17 份源码/网格/许可，逐项核对 Git blob 与 SHA，并在 Windows 保存独立副本。当前 RM65-B URDF 和 7 STL 全部与官方一致，link_1 质心疑点也存在于官方源。

该库 EG2-4C2 参考只有 7 links、总质量 0.0942992 kg；用户原夹爪源 9 links、0.236207349 kg。因时当前[产品页](https://www.inspire-robots.com/dexterous%20hands/eg2-4c-series/)标称 231 g、70 mm 行程、0–20 N 力，故不能因参考文件来自官方库就把明显不同的质量/结构直接覆盖。RM65 末端法兰孔位 PDF 已渲染读图，但不包含本项目完整夹爪转接件堆叠尺寸，不能据此证明夹爪安装位姿已标定。

对 13 个 USD 的关节变换，数值检查 T0·R(q)·T1⁻¹ 与源 FK：已找到关节的父子、零位、轴向/方向及采样运动一致。五份新 native 资产的五个随动关节限位由源 0–1 rad 变成导入约 -0.173–1.038 rad，**严格限位一致检查失败**，仍未修复，也未认定它是卡滞主因；不可把运动学帧通过写成全部源一致。

### 原始文件自身的疑点

- 六个活动指节的源质心超出自身可见网格包围盒 y 范围约 1.374、1.934、6.754 mm（左右各一）。数个质心的 y 符号与均匀密度网格质心相反。
- RM65 link_1 质心在可见网格 z 范围外约 5.44 mm。
- l_3/r_3 网格按 1e-8 顶点去重后各有 23 条非二流形边；这是网格质量线索，不自动证明整份 CAD 损坏。
- 没有把均匀密度网格质心当真值。电机、材料不同会导致不均匀密度；需要原始 CAD/零件质量和坐标定义复核，不能为通过仿真直接移动质心。

### USD 检查范围及限制

所有检查资产 metersPerUnit=1，零姿态可见网格相对源 FK/STL 的最大包围盒差约 1.38 微米，没有发现整体毫米/米误缩放。**这只检验零姿态可见几何，不证明所有关节姿态、接触凸包或惯量正确。**

旧导入原网格 CollisionAPI 挂在 Xform，真正 Mesh 没有该 API；旧检查器按属性节点个数就报 PASS，证据不足。含附加垫的旧 USD 另有两个真实 box collider。不能仅凭 Xform 属性就声称已验证原指面碰撞，也不能未经 cooked-shape 检查就断言所有旧原网格完全不参与碰撞。

参考：[OpenUSD MeshCollisionAPI](https://openusd.org/25.11/api/class_usd_physics_mesh_collision_a_p_i.html)、[NVIDIA 碰撞模型](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/collision.html)。

## 三、运行结果，不能用 PASS 标签掩盖边界

前三次均从实验室 GNOME 终端启动可见窗口，每次 2460 步；运行截图与 telemetry 分别验证。完成后窗口标注 PHYSICS PAUSED，等待结束退出，不把静止的完成画面当持续运行。

| 检查 | close_001（导入柔性 mimic） | close_002（理想刚性 mimic） |
|---|---|---|
| 重力、实际原质量、源表面碰撞、单主动驱动 | 通过 | 通过 |
| 独立自由落体加速度 | -9.810000658 m/s² | -9.810000658 m/s² |
| 最大 mimic 跟随差 | 0.724786 rad，失败 | 0.019815 rad，通过当前诊断阈值 |
| 最大保持误差 | 0.778020 rad，失败 | 0.130483 rad，失败 |
| 空手闭合/返回张开验收 | 失败 | 失败 |
| 能否用于训练 / pi0.5 成功证据 | 否 / 否 | 否 / 否 |

主要内部接触在 r_2–r_3、r_2–base、l_2–l_3 等对上。峰值是仿真内部反力，不能当真实夹持力。源面 FK 开口约 70 mm 到 0.093 mm，仅为理想几何，旧附加垫的 16.8–47.7 mm 限制废止为原生结论。

close_003：四对机械连接局部过滤的运行时合同通过；原质量、重力、单主动驱动及其余碰撞保留。随动最大差 0.002459 rad，保持误差 0.135099 rad，**闭合仍失败**；剩余右 r_1–r_2 反力峰值 38.885 N，左侧为零。没有过滤这对来凑成功。

进一步直接导出 PhysX cooked hull（不是视觉网格）：源左右 1/2 连杆在七姿态无三角面交叉，而旧凸包右 q=0.70、左 q=0.75 开始重叠，到 q=0.865 达右约 1.024 mm、左 0.948 mm 的分离轴穿透。三角面测试不是包含/精确间隙测试，证据支持优先查碰撞近似，但不等于全部根因证明。precision_001 对所有夹爪网格统一设 128 hull 上限、1% 误差、0.1 mm 最小厚度、shrink-wrap；只改变近似精度，保存前后严格核对其余属性不变。新 cooked 对照七姿态全部无左右 1/2 连杆凸包重叠，最大闭合时分离轴间隙下界约 0.694/0.705 mm；尚需动态证据。

NVIDIA 明确提示，关节附近相交的碰撞形状可能引起自碰撞不稳定；其不同示例可采用不同 self-collision 选项。这不支持“为了抓成功就全局关闭”。本项目下一步先检查关节帧、闭链连接部位与实际凸包；只有有几何/机械依据时才考虑局部过滤，并保持手指对外部物体、桌面和非连接部件的碰撞。[Isaac Sim 5.1 URDF 导入选项](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)

## 四、正式部署链路复核

**close_004 更新**：2460 步全部诊断检查通过，最大保持误差 0.004850857 rad，随动差 0.000005063 rad，全部六个活动夹指记录自接触峰值为 0。重力/原质量/单驱动/四对内部过滤/其余碰撞保持。尚未夹物；不能由空手成功推出夹持力、搬运或 pi0.5 成功。源限位恢复代码已有 5 项测试，动态复测待进行。

按官方 OpenPI 的自定义机器人数据转换、输入/输出适配、归一化、微调及策略服务路径对照；下面的验收门禁是本项目补充，不冒称官方为 RM65 提供认证流程。[OpenPI README](https://github.com/Physical-Intelligence/openpi)、[远程推理说明](https://github.com/Physical-Intelligence/openpi/blob/main/docs/remote_inference.md)

| 顺序 | 必须具备 | 现状与剩余项 | 不完成会导致 |
|---|---|---|---|
| A 身体可信 | 源/装配/轴/限位/惯量/碰撞/传动，重力下可开合 | precision_001 空手开合 PASS；源限位恢复待复测，质心/安装/外物接触待核实 | 模型学到不存在的夹持方式 |
| B 输入输出一致 | 固定双相机、实际关节反馈、7 维动作、时间单位及同一转换 | 差分6轴/绝对夹爪往返通过；新离散状态通路测试通过；新 profile 未接入完整入口 | 看不到自身姿态、训练推理语义错配 |
| C 有效多物体数据 | 原生实际接触的完整任务、来源/失败保留、按物体/物理轨迹分组留出 | 150 train+9 validation 均同尺寸方块；新诊断数据禁止训练 | 无法据旧分数证明日用品泛化 |
| D 时间和标签正确 | 固定采样节奏、先观测后动作、horizon 对应实际时间 | 历史 policy-window 删除保持帧但保留名义 fps；需要新协议不跨被删时间段构造未来动作 | 多步动作的时间跨度混杂 |
| E 归一化和微调 | 新数据计算统计、明确基础权重、独立输出、显存 smoke | 旧流程已跑通；新 state_v1 从 pi05_base，尚未训练 | 沿用方块习惯/错误尺度；OOM 也可能阻塞 |
| F 策略闭环 | 分离模型动作、通用安全限制和任务辅助；超时与限位 | 旧 pi05 分支含目标真值释放监督；新纯策略评测尚未完成 | 脚本帮忙得到的成绩被误报成模型能力 |
| G 独立验收 | 未见条件，多次重复，接触/搬运/释放/视野证据 | 旧方块成绩保留为代理模型历史结果；新原生没有任务验收 | 不能宣称部署成功或泛化比例 |
| H 可复现交付 | 版本、参数、资产/数据/权重哈希、双备份、运行指南 | 老数据保留；本轮新原生资产/失败试验双备份通过；新部署包未形成 | 出错后无法定位/回滚 |

### 新发现：接口接到了不等于模型用到了

本地 OpenPI commit=15a9616a00943ada6c20a0f158e3adb39df2ccac。
旧 RM65 配置 pi05=True、discrete_state_input=False。已读源码确认 pi05 不走 pi0 的连续状态投影。两组归一化状态 -0.75/+0.75，保持同指令时，旧输入 token/mask 不变；候选改为 True 后不同（本例有效长度 42/49）。关节状态仍用于外部差分标签和绝对动作重建，因此不能笼统说“系统完全没用关节状态”。

新 make_pi05_rm65_native_lora_config 使用独立 name、200-token、官方基础权重；旧 train/serve 入口仍保持旧配置以复现 v2–v5。**不能直接把旧 checkpoint 配上新输入就称修复。** 新训练/服务/profile manifest 绑定和全数据 token 长度验证待完成。增加序列预算的 16 GB 显存成本仍待 smoke；没有自动升级环境或改动外部 OpenPI dirty 文件。

### 历史代码还有哪些特殊处理

- 早期诊断曾关闭机器人/手指或物体重力，使用辅助释放下移；后期方块训练入口已启用自然重力及无辅助释放，不能把全部历史数据都说成无重力。
- 但当前 run_recorded_expert_demo.sh / run_pi05_rm65_closed_loop.sh 仍指定 wide_pads、六路独立高增益夹爪、目标托台 after_transfer 才启用碰撞，抓位有固定偏移。它们是旧实验复现入口，不是新的通用抓取入口。
- 旧相机自动朝向与任务真值释放监督已在日志揭示；固定新相机已有开发画面，尚未完成原生模型全摆放覆盖。
- 审计覆盖关键链路及结构扫描，**不表示所有 223 个文件逐行无缺陷认证**。

## 五、本轮代码结构与证据

```text
scripts/build_native_gripper_candidate.py     独立保留源几何/传动的候选生成
scripts/import_native_gripper_candidate.py    新 USD 导入与真实 Mesh 层碰撞核验
scripts/derive_native_rigid_mimic.py           单因素刚性随动对照（不覆盖）
scripts/run_native_gripper_diagnostic.py      可见空手开合、重力、质量、接触 telemetry
scripts/audit_native_aperture.py              源末端面开口，只读几何
scripts/audit_robot_model_lineage.py          源/派生 URDF/STL/惯量差异
scripts/audit_robot_usd_lineage.py            全部 USD 实际层/碰撞/关节信息
scripts/audit_pi05_state_path.py              不加载权重的状态条件输入反例
scripts/audit_official_model_reference.py     固定官方版本与原源字节校验
scripts/audit_imported_joint_frames.py        父子/局部关节帧/轴/限位数值核对
scripts/audit_native_linkage_closure.py       源连杆枢轴与实际同轴孔面
scripts/derive_native_linkage_filter.py       四组有证据的内部连接诊断
scripts/audit_native_cooked_shapes.py         实际碰撞凸包与参数来源导出
scripts/audit_native_collision_fidelity.py    源三角面/凸包的左右数值对照
scripts/derive_native_collision_precision.py 全夹爪统一精度，不改源几何
openpi_extension/rm65_training_config.py      冻结旧工厂 + 新独立状态输入候选
scripts/restore_native_follower_limits.py    只恢复源五个随动关节限位
scripts/backup_native_audit_batch.py          限定诊断资产/原始证据的哈希归档
scripts/test_*                               当前完整 CPU 回归 217 passed
results/*audit*.json, native_surface*.json    小型证据，可入 Git
generated/native_surface_*                   新/失败资产，禁止入 Git
outputs/native_surface_close_00*             原始 telemetry/截图，禁止入 Git
```

本轮原生归档 79 文件、tar 33,945,600 bytes，SHA256=6df0ea0ec5fc677eb75665ced84057b1bef9b9aff480a86564881290c04c75cc；逐成员与源 SHA 校验及 Windows 独立副本一致。含失败 v1/v2/v4、有效静态候选 v3/rigid、两次失败 dynamics 和源 URDF/STL。尚未完成完整解包重建运行测试。

## 六、大白话

你担心的事情确实发生过：以前为了夹住方块，在真正手指外面加了两块看不见的“手指”。所以录像数字成功，不等于原来那只夹爪真的抓住了。现在这条捷径已被挡住；新模型让能碰东西的表面和画面里的手指对齐。

同时又找到一个与任何物体都有关的问题：程序把关节角交过来了，但旧模型配置没把它送进模型的“大脑”。我已做好一个独立的新输入配置，并用测试证明这条线接通了，不过还没训练出新本领。

通过查原始连接孔、实际碰撞形状，现在夹爪已第一次不再空手卡住。下一步把导入时放宽的关节范围还原，再看真实手指表面能不能夹住和托住物体。没有加大力气、关重力或把物体缩小凑结果。今晚清单会据实写清“修好了什么、还卡在哪里”，不会把排查或空手测试完成当作部署完成。

## .049 接续更新：已观察原生外接触，但加载接触验收失败

此段覆盖早期“尚未外部夹物检查”的当前状态描述；历史失败和源资产结论保留。可见native_contact_004在临时6臂force模式下完成2640步，20/35/50mm均有短暂合格l3/r3原面接触，却在撤支撑前掉落，保持/自然释放0/3。此前001–003的手臂姿态漂移已用驱动语义对照缓解：继承USD是acceleration，ImplicitActuator估算torque不能当实测驱动力。源USD未写，300Nm臂上限仍是诊断参数。

新results/native_external_contact_geometry_001.json从保存的同帧世界/链接点对恢复实际指体姿态，证明三档选定帧原始内面三角进入实际物体OBB；不是仅靠负separation认定穿透。尚未分离碰撞凸包、求解器、刚性mimic/闭链和加载驱动原因，当前不能准入日用品训练。保留2.1mm面距离/.95法向、连续2秒保持等冻结阈值，不靠缩物/加垫/增力/关碰撞过关。完整分析见results/native_contact_004_analysis.json；302 CPU tests passed。

下一步首先围绕已保存失败姿态进行cooked/接触/约束审计，随后才可设计有限单因素复查。身体接触、有效多日用品数据、state_v1全入口和新π0.5留出验收仍未完成。
