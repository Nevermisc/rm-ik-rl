# RM65-B + 4C2 + π0.5 唯一继续入口

更新：2026-09-30，工作版本 **household-generalization.059**。完整读取本文件，再核对实际Git、最新报告与进程。用户已授权交接后持续推进，不恢复旧定时任务。

## 1. 已核实状态与边界

原生块体台架007在源六轴effort上限下，三个尺寸的脚本保持、抬升、搬移及释放通过。真实带纹理记号笔001实际被携带，但持续原平面接触判据FAIL；002只提高物体碰撞分解精度，记号笔在开手静置阶段先倾倒到catch，随后为空手运动，严格FAIL。不能将两次记号笔运行、空手动作或退出0视为π0.5部署完成。

`pi05_used=false`、`training_ready=false`、`deployment_accepted=false`。尚无native日用品训练数据，没有新训练、新checkpoint或策略闭环验收。旧v2–v5 checkpoint全保留。

- 仅仿真、数据、训练、评估；不发送真实机器人命令。
- 保留原修改、失败记录、旧模型与备份，不reset/clean/git add .，不提交raw数据、网格、图片和权重。
- 重大仿真从实验室GNOME可见终端启动，核对真实桌面、RGB、telemetry；已结束运行不为截图重开。窗口暂停、等待Enter与physics正在运行要区分。
- 每批代码/配置更新工作版本和中文日志，说明问题、依据、方法、结果与泛化限制；fresh输出和独立备份。不能靠增力、改质量/尺度、加隐形垫、关闭碰撞或改旧阈值获取通过。
- 旧21:00安排及rm65心跳已取消，不恢复。用户已授权必要的可逆工作，无需逐步再问许可。
- **最新AGENTS已替换此前D盘偏好：**未经明确要求，不迁移到其它磁盘、不改变默认存储盘或缓存位置；遵循现有项目及用户指定路径。清理优先确认可重建的旧下载缓存及本任务不再需要的临时文件，保留成果、训练数据、聊天记录、凭据和有效Git历史；大型备份先核对用途/完整性，不能把删除请求改成转存。此前已在D盘生成的本轮少量报告/图片保留，未迁移任何旧文件，未改缓存配置。

## 2. 路径、Git与现场核验

```text
W = C:/Users/95380/Documents/ChatGPT/robot learning
L = W/remote_work_7baaa1a/project                         Windows小文件镜像，非权威checkout
SSH = chengyu@100.116.242.82
R = /home/chengyu/robot-learning/rm-ik-rl                权威Git main
P = R/projects/004-rm65-4c2-isaaclab
D = P/docs/pi05_sim_deployment_record
O = /home/chengyu/robot-learning/openpi
IsaacLab = /home/chengyu/robot-learning/IsaacLab
IsaacSim = /home/chengyu/isaac-sim-5.1.0
```

R HEAD `d4bbf0e1256711a221a0877ff1eebbf9aa6d87b5`；本轮修改未提交/推送，暂存区空。O HEAD `15a9616a00943ada6c20a0f158e3adb39df2ccac`，原Dockerfile修改及旧未跟踪项保留。W有自己的既有Git脏文件，不stage/push W。

精确初始基线在`P/outputs/native_contact_resume_001/preflight.json`。最新`P/results/native_household_resume_postflight_003.json`确认84个原未跟踪项、旧tracked修改、源USD/URDF/网格和marker包哈希均未变，OpenPI状态未变；无GPU compute、相关物理/训练/服务进程及8016/8017监听。旧GNOME bash仍可能等待Enter，不代表活跃任务。继续工作后必须重新检查，不把上述时点状态当永远成立。

先读`D/ITERATION_STATUS.json`、`D/STATUS.json`和`D/HOUSEHOLD_GENERALIZATION_LOG.md`当前字段；文件内v4/v5历史数值不是本轮native进度。核对`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`、Python命令行、live.json和监听端口。

## 3. 源资产、控制与策略接口

原生候选`P/generated/native_surface_source_limits_001/native.usd`：根SHA `a250f43ad92f878565a40c68b1caf1f2dea51c10f7782a7c05d4cba9c52ee5ce`；URDF SHA `c362f677ee792a5475c293617b6241ca17566b4dbaf87237d459afe2d307ff74`。generated为外部同名目录symlink；源4C2在`/home/chengyu/robot-learning/004-rm65-4c2-isaaclab/external/4C2`。5USD层、16STL、原质量/惯量全保留。

用户9-link夹爪236.2g，1master+5刚性mimic，master[0,.865]rad、followers[0,1]rad；仅4对已审内部接触过滤。全部9原生collider同一凸分解精度：64vertices、128hulls、1e6voxel、1%error、minThickness .0001m、shrinkWrap=True；没有隐形垫。官方同名7links94g资产不能直接替换。源六指节及arm link1 COM/安装/传动仍有未解决来源问题，不用均匀网格重算覆盖。

**仅加载源USD不能重现结果。** 源六臂DriveAPI仍是acceleration；运行时临时改六臂force，并设`solveArticulationContactLast=True`，均有严格属性变化检查且不保存源USD。当前dt1/120、gravity−9.81、TGS32/8、robot/object maxdep .2m/s，六臂gain1000/100、速度.5rad/s、源effort上限60/60/30/10/10/10Nm；master gain2/.1、force1Nm、速度2rad/s，五followers gain0。源上限不是硬件实测。旧006统一300Nm只是保留的对照。

控制合同`config/native_control_contract_v1.json` SHA `acc63a18c3fa25a9b8d2e5aa15c2078821a470d77a22ef5a33bc970f8118c387`。`openpi_extension/native_control_contract.py`按名字读取12实测关节；state为六臂rad+实测master/.865，保留原始残差不clip；action为六臂绝对rad+归一化grip，映射到6+1目标，不写被动followers。需显式正command interval和上个命令名，检查速度。`native_control_mapping_002.json`对007全部10080行通过。旧norm不可继承。

独立`native_state_contract.py`及96tests校验真实文件哈希、轨迹角色、分组、norm与checkpoint身份，但准入全关。新profile `pi05_rm65_native_state_v1_lora` 为state=True、200tokens、7env/32model、horizon10、pi05_base初始化；旧模型state=False，state只用于外部动作转换。旧train/norm/serve入口未修改，新链仍未贯通，绝不偷换旧checkpoint。

## 4. 最新运行与相机证据

| 运行 | 真实结果与范围 |
|---|---|
| contact001–003 | 第31步臂跟踪中止，未进入夹持 |
| contact004 | force臂，三档均提前掉落，原面/cooked侵入已证实 |
| contact005 | 仅contact-last=True，三档4s无支撑保持及自然释放通过 |
| contact006 | 三档脚本主动运动通过；含腕转的实际物体抬升约41.8mm、独立第二段XY约63.8mm |
| contact007 | 仅六臂effort改源上限，同3360步，三档通过；14关键指标与006一致，独立复算 |
| household_marker001 | 默认16hulls；实际抬41.777mm、搬63.743mm、释放约192.588mm；持续flat-inner接触0/720，严格FAIL |
| household_marker002 | 同源物体、控制、相机、路径、阈值，仅临时object精度覆盖；实际127hulls；开手时倾倒，后续空手，严格FAIL |

007完整trace约937MB，SHA `0d4554d897ff80cda9ad10174a553d759baafcd3aeb2b2143aa6e0df694175c3`。复算见`native_contact_006_007_comparison_001.json`。

真实marker源包SHA `685db469b44dc4ce36e63a15622dfbb0a67d9b909582616a5d0df29e513212f3`，8499vertices/16384triangles，保留原.01 mesh坐标转换、spawn1、20g假设质量、原材质.7/.5。其18.834×120.886×19.476mm完整形状未改。初始root是palm[0,0,.14]，不是精确AABB中心；原朝向长轴竖直。30×30×40mm可见支撑依次下40mm、横移150mm、再下60mm，有独立catch避让证据。初始化后不写对象pose/velocity/force。

001坏点法向与实际凸包外斜面及原手指相邻边缘有关，不能统称内部端盖或假接触。源指flat-inner实际为10条平面条带而非填满矩形；7个palm-Z位移静态候选没有稳健改善。001实际cooked外侧顶点距源曲面最远4.499mm，部分接触距原marker曲面2.244–3.206mm，有限证据不足以认证所有原表面接触。

002临时六精度字段+一个API有前后allowlist及reset后typed回读。质量/源几何/材料未变，但自动COM移动1.311mm、惯量随recook变化，不能称所有物理字段不变。002第7步倾角1°、21步5°、38步15°、62步完全脱离Support、69步落Catch；close从241步开始。全3360帧两指有力接触点为0。001前240步Support持续、最大倾角仅.0257°。初始支承和后续失败的详细独立结果见`native_household_marker_001_002_comparison_001.json`及002geometry报告。

当前冻结接触判据要求每个有力点距原内面有限三角≤2.1mm、abs normal alignment≥.95且双侧力足够；主动720帧持续接触且无Support/Catch/其它robot承托。全trace实际object/palm位姿计算抬升、独立搬移、相对滑移和自然释放；外层gravity/完整步数/安全条件均必须通过。保留旧判据，不因真实边缘承载可能成立而追溯改判。

`camera_rig_native_v1.json` SHA `fddd4bb7e77e3afd830ead9fb15b795ac2268b13f24c8f3172d16afefc181a20`，固定外相机与link6腕相机，不跟踪object truth。真实RGB 640×480，每阶段物理暂停后≥8次有效buffer refresh，记录K、实际pose、时间/步数和PNG字节SHA；这不是已认证20Hz或10Hz采样。001持物可见但释放后腕图仅残片；002实际RGB证实落物与空手动作，root直接看8图并核对源SHA。图像存在和metadata正确不等于全场景视野或训练准入。

关键新报告：`native_control_mapping_002.json`、`native_household_marker_001_analysis.json`、`_001_geometry.json`、`_001_contact_planes.json`、`_001_point_conditions.json`、`_001_camera_audit.json`、`native_marker_face_margin_plan_001.json`、`native_marker_precision_schema_001.json`、`native_household_marker_001_002_comparison_001.json`、`native_household_marker_002_visual_review.json`。最新CPU `cpu_tests_058.log`为567passed/1skipped；installed USD独立22tests通过（与全套部分重合，不相加）。本轮raw全部在同名outputs下，不进Git。

## 5. 备份与可恢复性

旧备份001–004全保留。004独立副本473成员、1,611,929,600bytes，tarSHA `0b44d48478efcc0a0588c46da5c2199fa46223a041970d9aa9bef7b63029d12b`，indexSHA `c9b00c83cb145f290a31ffb1b46f6af29910d849ef72addef9df56318f475a83`；Windows逐成员哈希/大小/安全路径/类型全通过，receipt `native_audit_backup_004_independent.json`。旧Windows位置仍`W/RM65_DATA_BACKUP_DO_NOT_GIT/native_audit_2026_09_30`。

**005正在准备，尚未宣称独立完成。** 新005需包括007、marker001/002完整raw、源/配置/脚本/日志快照、真实marker包和本批审计。远端staging仍`/home/chengyu/robot-learning/rm65-backup-staging`；依据最新替换指令，新独立副本沿用项目既有Windows备份目录；先检查空间及重复文件，不默认跨盘转存。具体完成状态看ITERATION_STATUS.latest_native_backup和真实独立receipt，不能以tar存在当验证通过。完整发布包解包重建运行仍未验证。

旧入口和文档在`outputs/native_household_resume_002/before_059`留存；旧.054完整历史还在之前归档。后验receipt及其后状态另存两端，不能自包含自己的后验哈希。

## 6. 接下来优先工作

1. 继续当前优先1：完成002独立几何/相机审计与005独立保全；用真实source、actual cooked和COM检查稳定初始摆姿与整手可接近性，再决定fresh003。不凭成功分数挑姿态，不修饰002失败；不把几何可行等同动态通过。对flat strip与真实source bevel/edge可分开做证据分类，但旧冻结判据保留。
2. 真实物体/相机基础仍未通过；按`D/NATIVE_DATA_CONTRACT_DRAFT_ZH.md`冻结native对象、轨迹分组、实际时间和相机合同。现有五个YCB对象全部已暴露开发资产，不捏造unseen池或split。原20Hz来自dt1/240×stride12；本台架dt1/120不能照搬。删保持帧但不改fps的旧语义不可继承。
3. 在独立state_v1链中贯通norm/train/serve/artifact真实身份、尾批/token截断/时间连续性；所有未满足项fail-closed。仅模型/数据/双备份门禁通过后，才从明确基础权重做新目录显存smoke和训练。保留所有旧权重。最后按预先冻结的纯策略/辅助范围、样本量、重复性和未见对象合同验收，再检验完整解包重建发布包。

继续必须读实际报告、源码快照与manifest；不从旧聊天或某个进程退出码猜测部署状态。
