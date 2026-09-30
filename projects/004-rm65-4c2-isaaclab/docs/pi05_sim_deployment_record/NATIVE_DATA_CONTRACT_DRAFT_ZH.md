# 原生日用品数据合同草案：现有资产与待验证字段

状态：**draft / training_allowed=false / household_collection_admitted=false / unseen_object_holdout_ready=false**。

本文件是 2026-09-30 对权威远端代码、配置、资产与旧记录的只读核查结果，以及下一步接口草案。只新增本文；未改模型、归一化、训练/服务入口、资产或旧数据，未启动仿真或策略进程。本稿不冻结新对象切分、采样周期、样本量或验收通过率，不把正在运行的 006 预判为通过。版本日志由主线统一维护。

`P=/home/chengyu/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab`，`O=/home/chengyu/robot-learning/openpi`。下列相对路径均以 P 为根，标注 O 的除外。核查时仓库 HEAD 为 `d4bbf0e1256711a221a0877ff1eebbf9aa6d87b5`，OpenPI HEAD 为 `15a9616a00943ada6c20a0f158e3adb39df2ccac`；工作区有主线未提交修改，不能用 HEAD 代替文件身份。

## 1. 已有五个本地资产；全部只能列入已暴露开发池

注册表为 `openpi_extension/household_assets.py` 的 `HOUSEHOLD_CATALOG`。前四个资产来自 `results/household_assets_003.json`，记号笔来自 `results/household_marker_assets_001.json`。本次重新计算五个 `model.usd` 和五张贴图的 SHA256，全部与 manifest 一致；没有下载新资产。

| object_id | 源文件 | 已有包的轴对齐全尺寸 X×Y×Z（mm） | 现有仿真假设质量（kg） | 当前开发筛选结论 |
|---|---|---:|---:|---|
| ycb_large_marker | 040_large_marker.usd | 18.834 × 120.886 × 19.476 | 0.020 | 细横截面约19mm，小于原生理想开口70mm，可先做开发适配核查；不等于可稳夹 |
| ycb_pudding_box | 008_pudding_box.usd | 113.654 × 89.817 × 38.471 | 0.190 | 仅38.471mm薄轴符合开口初筛；需要真实摆姿、可接近性及整手碰撞检查 |
| ycb_banana | 011_banana.usd | 197.174 × 38.649 × 74.066 | 0.066 | 38.649mm轴有开发可能；弯曲、局部横截面和指面接触不能由AABB替代 |
| ycb_soup_can | 005_tomato_soup_can.usd | 67.659 × 101.855 × 67.714 | 0.350 | 约67.7mm截面只比理想开口小约2.3mm，属于边界候选，不能宣称已适配 |
| ycb_mug | 025_mug.usd | 116.990 × 81.303 × 93.088 | 0.120 | 整体最小AABB仍>70mm，不作为已适配候选；把手局部需要源网格和空腔核验，不能假设可抓 |

尺寸是现有完整 USD 的世界包围盒差值，非厂家实物尺寸，也非任一摆姿的有效夹持宽度。质量来自项目注册表，源码明确 `mass_is_simulation_assumption=true`；不得当成实测质量。筛选只决定开发检查顺序和问题范围，不允许缩放物体、减重或添加隐形接触垫以获得通过。

源 URL 前缀均记录为 `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/Props/YCB/Axis_Aligned/`。原始下载字节 SHA 由旧 manifest 记录；本次仅重验本地加工后的包与纹理，未重新核验远端原始字节。包是 USD 内嵌 Mesh，不是独立 STL；未声称另有可用原始 CAD。

本地包路径：前四个为 `P/outputs/household_assets_003/<object_id>/model.usd`，记号笔为 `P/outputs/household_marker_assets_001/ycb_large_marker/model.usd`；每个包有一张 `textures/<源文件去掉.usd>_COLOR.png`，可视材质依赖 Isaac 内置 `OmniPBR.mdl`。

### 已经暴露过的证据

五个对象都已进入旧开发流程，不能给它们贴上“全新未见对象”标签。具体暴露程度不同，不把“未查到抓取记录”误写成“从未见过”：

| 对象 | 已确认的旧暴露 | 本次核查证据 |
|---|---|---|
| banana | 多轮 legacy scripted、probe、固定相机实验；已有失败和旧pad通过记录 | `datasets/*household*/metadata.json` 范围内18份banana记录；代表 `datasets/rm65_household_visible_fixedcam_banana_002/metadata.json` |
| pudding_box | legacy expert和v5开发尝试，均记录失败 | 同一范围2份；`datasets/rm65_household_dev_pudding_expert_001/metadata.json`、`datasets/rm65_household_dev_pudding_v5_001/metadata.json` |
| large_marker | legacy scripted多轮、固定相机实验 | 同一范围5份；代表 `datasets/rm65_household_visible_fixedcam_marker_001/metadata.json` |
| mug | 资产导入、源尺寸/碰撞检查、可见场景及自由落体settling probe | `results/household_assets_003.json`、`results/household_scene_001.json`；上述metadata扫描范围未见mug抓取episode |
| soup_can | 资产导入、源尺寸/碰撞检查、可见场景及自由落体settling probe | 同上；上述metadata扫描范围未见soup_can抓取episode |

这25份metadata均无 `collection_split`。其中固定相机banana/marker旧审计即使 `candidate_checks_passed=true`，仍明确 `training_ready=false`、`formal_acceptance_passed=false`。当前没有可直接晋升的native日用品演示。

`results/household_asset_inventory_001.json` 中列出的其他远端文件名只是历史目录清单，不构成本地可用资产证据，本文不据此扩充推荐对象。

## 2. 可静态核验的物理字段，与必须重新实测的字段

本次用只读 USD API 打开五个本地包，未启动 SimulationApp。各包均 metersPerUnit=1、Z-up、一个动态刚体 `/Root`、一个 Mesh collider，CollisionAPI 开启、近似 `convexDecomposition`。实际 authored 质量与上表相符（float32表示误差）；`ProbePhysicsMaterial` authored 静摩擦约0.7、动摩擦0.5、回弹0。源码 `prepare_household_assets.py` 把物理材质绑定到Mesh。

全部 Mesh 保留已有 `xformOp:scale=(0.01,0.01,0.01)`；这是包内原有坐标转换，不能为了“scale=1”直接重写，也不能再追加缩放。新的spawn级scale应完整记录，并拒绝任何未在资产合同中声明的几何变换。

| 对象 | Mesh prim | 顶点数 / 面数 |
|---|---|---:|
| mug | /Root/_25_mug | 10518 / 16378 |
| banana | /Root/_11_banana | 8369 / 16384 |
| soup_can | /Root/_05_tomato_soup_can | 8565 / 16382 |
| pudding_box | /Root/_08_pudding_box | 8442 / 16384 |
| large_marker | /Root/_40_large_marker | 8499 / 16384 |

这些包未显式author COM、惯量或 `physxConvexDecomposition` 精度参数；不能把引擎回退值、运行时计算惯量或cooked hull当作已知。旧 `household_spawn_config` 写的是对象solver position32/velocity4、max_depenetration_velocity=1.0；这是旧spawn设置，不是当前native台架的已验证对象合同。

新native采集之前必须形成独立检查报告，至少记录实际加载的网格变换/材质绑定、质量/COM/惯量、每个cooked hull及参数、源外表面与碰撞表面的误差/空腔保真、原生指面接触、整手碰撞、载荷下持物及自然释放。005/006是块体台架，不能为上述五个对象代签。旧块体OBB穿透审计不能直接套到凹形mug或曲面banana上；应保留原始对象表面与cooked几何的对应证据。

## 3. 切分只定义字段和规则，尚无可宣称的unseen池

现有 `config/rm65_expert_collection_plan_v1.json` 为单block的45条计划：36 train、9 validation，变化是关节角、源位置和prompt。`scripts/build_expert_collection_plan.py` 用 `(angle_index + position_index) % 5` 切分。当前 `config/*.json` 的case未发现 `object_id` / `family_id` 家族切分合同。旧v5数据审计仅150条同类block训练演示；换指令不产生对象泛化。

草案字段：

```json
{
  "schema": "rm65_native_data_contract_draft_v1",
  "status": "draft",
  "simulation_only": true,
  "training_allowed": false,
  "collection_admitted": false,
  "new_unseen_object_ids": [],
  "object_family_split_frozen": false,
  "split_manifest_sha256": null,
  "camera_contract_sha256": null,
  "time_contract_sha256": null,
  "native_object_physics_report_sha256": null,
  "model_profile": "pi05_rm65_native_state_v1_lora",
  "checkpoint_created": false
}
```

实现时每个对象需 `object_id`、资产包/纹理哈希、`family_id`（经审阅的几何/功能家族，不从文件名自动决定）、`exposure_history`、`split_role`。现有五个只能先置 `split_role=development_pool`，不在本文分配train/dev/unseen。若以后用其新native演示训练，必须另立数据身份，明确“新的native采集，但对象曾被开发见过”。目前没有已证明未参与开发的对象池；该缺口阻止unseen验收承诺，不能用改名或新随机种子填补。

物理轨迹是最小分组单元：`physical_trajectory_group_id` 绑定对象身份、初始场景/摆姿、完整实际动作序列与reset lineage。同轨迹的重渲染、语言改写、裁剪和复制必须同组同split，不能按帧或文件夹名拆分。`simulation_seed`、`render_seed`、`policy_noise_seed`、`repeat_index` 分开记录；重跑不是独立新对象。norm只允许train组；dev用于选模型，最终留出不得反复用于参数调整。

样本量、各对象摆姿范围、重复次数、成功阈值和固定留出清单仍为null/未冻结；应该在首次正式采集或评测前形成带哈希的计划，不能看成绩后删除难对象或改分母。资产可抓适配检查与策略评分分别记录，无法适配也保留原因与失败原始数据。

## 4. 相机：旧v2可复用代码结构，不能继承native视野通过

已有 `config/household_camera_rig_v2.json`：external eye `[0.65,-1.0,1.1]`、target `[-0.22,-0.03,0.76]`；wrist parent `link_6`、local offset `[-0.03,0.18,-0.06]`、forward `[-0.0556,-0.18,0.1697]`、up `[0,0,1]`。光学配置640×480、外相机焦距24mm、腕相机18mm、水平光圈20.955mm、裁剪0.01–10m，全部是仿真配置，非硬件标定。

`openpi_extension/camera_rig.py` 已能验证几何配置并返回配置SHA，`uses_object_pose_for_camera_initialization=false`、`uses_task_target_for_camera_initialization=false`。固定腕相机由实际parent link姿态组合变换，算法可复用。旧 `legacy_object_aimed` 分支则使用对象/目标真值朝向相机，native策略采集不得默默回退。

旧v2的见证是pad夹爪场景下banana/marker的单次画面与轨迹，不覆盖最终native夹爪、不同初始摆姿、抬升/搬运、释放后的对象/目标可见性。当前台架桌面截图不是external/wrist传感器数据。新相机合同保持未冻结，需新native可见preview及逐阶段传感器帧后才认可；若要调整，新增配置身份，不覆盖v1/v2。

每帧应存两张真实RGB、采样sim_step/physics_time、传感器frame id及时间、实际camera-to-world（四元数顺序/坐标约定明确）、K与分辨率、原始图像SHA、rig SHA、渲染器/累积重置策略。不能只验证数组shape就当已排除黑帧/遮挡/过期帧。传给策略的数组应与保存数组逐字节对应；policy额外render与记录器render不同的旧风险要单独消除。图像统一到模型224×224的步骤及版本也要绑定。

## 5. 时间合同：先记录真实时钟，再选择控制周期

旧 `run_pick_place_baseline.py` 的physics dt是1/240s，12步采样对应20Hz；本次扫描的25个旧日用品metadata也写20Hz。当前native台架dt为1/120s，若机械复制stride12将变成10Hz。二者不等价；本稿不选择新的stride或fps，不把原20Hz沿用为既定值。

新合同必填 `physics_dt_s`、`control_stride_steps`、`control_period_s`、`control_hz`、动作保持方式、每次执行chunk长度、重新观察时点和推理等待时是否推进仿真。先确认native控制/相机负载，再冻结数值。离线审计强制 `control_period_s=physics_dt_s*control_stride_steps`，相邻保存行的实际 `sim_step` 和 `physics_time_s` 与之对应；墙钟、渲染次数不能冒充物理时间。

每个控制边界先取同步的实际state和图像，标签action表示接下来明确区间的绝对关节目标；必须保存 `action_valid_from_sim_step` / `action_valid_to_sim_step`，防止把已执行动作或未来state错配成输入。末尾不足完整chunk的padding/mask策略需显式声明。模型action_horizon=10是10个控制采样点；其秒数只有冻结周期后才有意义。

旧 `convert_expert_episodes_to_lerobot.py --policy-window` 删除中间保持帧却沿用原fps，旧 `validate_episode` 仅检查时间递增。新native默认应拒绝这一转换模式：保持完整等间隔序列，或者另立支持真实时间的转换/模型合同；不能把删帧后的相邻行当作等时距。现有OpenPI `create_torch_dataset` 按 `t / dataset_meta.fps` 取未来动作，需要连续一致的时间网格。新合同检查缺帧、跨episode、复用同一图像和时间差，而不只检查总帧数。

## 6. 与state_v1接线所需的最小记录字段

| 类别 | 现在已有且可复用 | 新native必须补齐/验证 |
|---|---|---|
| 模型身份 | 独立工厂 `make_pi05_rm65_native_lora_config`；200-token、离散state、环境7维/模型32维、10步horizon | profile全合同SHA、明确基础权重哈希、native train/norm/serve/manifest统一选择；旧入口仍legacy |
| state | `RM65Inputs` 接收六关节rad + 一维夹爪；已有Delta/Absolute transforms | 按joint名称取实际反馈；原始夹爪q保留；规范化映射身份和越界门禁，不能用命令代反馈 |
| gripper映射 | 旧helper `clip(q/0.865,0,1)`，旧执行映射`u*0.865`；源master上限0.865rad | 新native映射需显式确认与source SHA绑定；clip不能隐藏限位/反馈异常；0.82rad诊断目标不能冒充规范化1 |
| action | 六轴绝对target rad + 夹爪规范化target；训练转换六轴为delta、夹爪保留绝对值 | native单主动+五随动：只给master写命令，不复制旧全夹指PD控制；保存raw policy、执行target及过滤/辅助原因 |
| norm/token | 七维state及action在pad前处理；π0.5用quantile norm后tokenize，再pad32 | train-only全帧stats、实际checkpoint内norm哈希、同输入train/serve token一致、全prompt/state token预算；尾批不能丢弃 |
| provenance | expert_episode已有timestamp、sim_step、images、phase、object pose可作审计 | object/family/split/trajectory group；资产与运行物理合同；实际相机帧；全过程native接触与carry/release证据 |
| 特权信息 | 旧record可保存对象真值和阶段用于审计 | 模型输入白名单只有两RGB、语言、实际七维state；对象位姿/目标误差/phase/专家状态不传纯策略；任何辅助单独标记 |
| 准入 | `training_admission.py`仅legacy_reproduction且拒绝object_probe | 新native明确admission schema；所有draft/diagnostic/failure/evaluation_only拒绝；没有有效数据前仍training_allowed=false |

接线可先实现独立CPU合同校验器及合成fixture，覆盖缺身份、跨split轨迹、错norm、状态未进token、时间错配、缺图像、诊断晋升等拒绝路径。合成fixture不是训练集；不得为测试方便把当前台架telemetry或旧pad数据标记为已准入。模型/入口代码不在本文件创建时改动。

## 7. 下一次native开发采集的可执行前置链

1. 先保全005/006实际报告、源码快照和独立备份。对象检查只使用上表已存在资产及实际字节；记录单独开发输出目录，继续 `training_allowed=false`。
2. 对通过尺寸初筛的对象检查实际源网格局部夹持面和整手可接近性，保存新的对象cooked形状/质量/惯量/材质检查；几何或动力学失败不靠缩小/减重/隐形pad修分数。
3. 用native最终机器人和新摆姿验证固定相机，保存真实external/wrist见证。相机和时间参数确定后才发布新合同SHA；本稿不代填未知数值。
4. 冻结新的对象资格清单、切分/轨迹组、样本量和验收规则。现有五个都已暴露；无新的合格unseen池时，明确只做已见开发/训练准备，不能宣布泛化留出已齐备。
5. 新采集先逐episode输出完整物理/图像/时间/准入审计，再转换到全新repo_id；norm、模型smoke、正式训练依次受合同约束。旧v2–v5和旧norm不覆盖。

## 8. 本次核查的身份摘要

以下哈希均为本次从权威远端重新读取的文件SHA256，不含本文自哈希；资产来源哈希另存于原manifest，未在本次重新下载验证。

### 本地资产包与纹理

| object_id | model.usd SHA256 | COLOR.png SHA256 |
|---|---|---|
| ycb_mug | 275a0971082c55c7ca013a303f4fb96e133c0d2fae6fd91754821992506be5da | c0cd34ec9a0eb023173e0a8adbaa3e24dc9129780592e134adbc811e08a20a9f |
| ycb_banana | b7fc1ee88c2c05fab0ed3bc5633c2c9a8ec5b594c61fbc1009e71a1a40a6ef48 | 841dd1e67d23815cfaac3a14019c4dd8712d956664dab853a4d558353eba3795 |
| ycb_soup_can | ea971e30aa6c28a92dde5e3c3a190c747fd719bf8faee282d3d6a77bda9c1616 | c6e19d89d60c65f702ed789742e488bc15125db3ee2c4bcbb6a7e3c433a3abf1 |
| ycb_pudding_box | 1078e06a6aaa4869e0d19aff7018d974c1c2366c804bb42de73efaea6bb8a8fa | 19bbe4971d72cb11c36ea74a924224f6cae7e0da08b4d50bf9b438ff3c31143d |
| ycb_large_marker | 685db469b44dc4ce36e63a15622dfbb0a67d9b909582616a5d0df29e513212f3 | 36bd303d1c71003df8118ff9095178b943cdf2b102cbfe5e70ee676a454dfc8a |

### 配置、源代码、旧证据

| 相对P路径 | SHA256 |
|---|---|
| results/household_assets_003.json | de169cae8b2411f9bb6eb567a15e1bcef56bb764f7665cec750656e86fe522ff |
| results/household_marker_assets_001.json | 74d99183fb0618612b5db46936170a6f9f95eb5721983cbccb1784f99144e477 |
| openpi_extension/household_assets.py | 66c14fa21de53cd927e82ace6f8090e602c3ce2e3f3188620405a35c4d6ac39b |
| scripts/prepare_household_assets.py | d3b7bc23353bfc4d283a81fe35dab9646f498fc88843c3058d1e6c0bf7e5e7ff |
| config/household_camera_rig_v1.json | 48b2b9659d25ae5a83a989360a4720a330e5a3fcea2caa6bfc9fb9a90d38b756 |
| config/household_camera_rig_v2.json | e6b83c1672239501fdea717a2826a539900c34fa6afea5f7da622acfbd48e98a |
| openpi_extension/camera_rig.py | 33cce0cc6f662337aac27d618c28c1f320d0f5fb6ba3f852d92496934d8b5272 |
| config/rm65_expert_collection_plan_v1.json | adf7c945044e2206b08a970a2a01d4bbd5f620ad070dc464b5f2dda686503c3e |
| scripts/build_expert_collection_plan.py | c0de6be0ad1f564c4c1c342cfe734bd04b5373d618bfccde893eb94b198a8d89 |
| scripts/run_expert_collection_plan.py | 503180aebc738113da16391541c93f1da4fb2b4f30579464d264f30060b56361 |
| openpi_extension/expert_episode.py | a2223a61169c0a1e22a66ab3d760a42c39110532fc2ff01e6f63bf058c150b1f |
| scripts/convert_expert_episodes_to_lerobot.py | 28addeaa45134b23acda29a92da956f4571e92f8786b3a05fc006128f2cad2a0 |
| openpi_extension/training_admission.py | a7baf575916a32671757de7b8fd2d4580e9cc0972325979271619658fb070044 |
| openpi_extension/rm65_training_config.py | 4856cf8e5dc0d9a34344fae89789b57d56ae3862029af029f0ced300e970c8e1 |
| openpi_extension/rm65_policy.py | d24c658d7f7b35f84271b80e2bcff6d3548c9a1f9c1e3c24bc439a2095bf4783 |
| scripts/run_pick_place_baseline.py | f6f915e108871aabe71add5abfd8fa762ce0f629ca6111373c686c6cd025a92d |
| results/household_generalization_audit_001.json | e5a21688588ff383601463ab59345e60a66622aaf4f6d25a8fcd28e4c26bfd57 |
| results/household_scene_001.json | 3cc04b0474b80795e10f73a1dd3f9b48fc51cf92dad9c3102108755d05b91341 |
| results/household_fixedcam_banana_002_trajectory_audit.json | a38ac2c25e9e615d4e8de0c64c8d3d7f85a144e6ff9345c202a3a520d6d6a53d |
| results/household_fixedcam_marker_001_trajectory_audit.json | 577f575c5d6b649a63855c22436a52d70b9469f86dd5c0dfb864ba0e3ab6d350 |
| datasets/rm65_household_visible_fixedcam_banana_002/metadata.json | 6d87747e1bdc6f1c16d851952f689aebeeb5fab96004b73f8c93bb2351f39131 |
| datasets/rm65_household_visible_fixedcam_marker_001/metadata.json | eac521e3d2f0f3ac682bf9c030566660beb40accf28a945b58f22c625efb6287 |
| datasets/rm65_household_dev_pudding_expert_001/metadata.json | d318958841b46a59c020aaeaff477bc0bfdde95fb9dcb00c4d5cc2c98d9a7eea |
| datasets/rm65_household_dev_pudding_v5_001/metadata.json | 39956be8699774325d143ee60e5ef26b48e7853fffe17ae71aa69723b72534f9 |

后续任何asset、相机、时间语义、动作语义或split改变都要生成新身份并保留旧版本；本稿不授予训练准入。
