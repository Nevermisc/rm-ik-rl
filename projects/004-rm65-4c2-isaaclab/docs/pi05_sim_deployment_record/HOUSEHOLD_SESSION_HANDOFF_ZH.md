# RM65-B + pi0.5 真实外观日用品路线：本轮收尾

日期：2026-09-30。开始 14:53（Singapore），本轮约一小时内完成收尾。
工程版本：household-impl.022；基础提交 02e48c8，首批实现提交 665bb9a。后续收尾提交由 Git 历史定位。
约束：仅仿真；不改既有 v2–v5 权重；不提交数据集、资产模型、checkpoint 到普通 Git；之后等待用户确认。

## 一、正式技术说明

### 1. 本轮成果与当前结论

本轮已将开发环境从几何体探针扩展到带原始纹理的四类日用品，并完成资产检查、物理落地验证、RM65 入口接入、现有模型摸底和夹爪控制诊断。

**尚未完成日用品抓取部署验收。** 四件物品“能正常加载和落地”不等于“四件都能抓”。本轮 9 条开发抓取试验（含重复诊断条件）均未通过，4 条空中闭合诊断不计入抓取成绩。未把失败数据用于训练，没有产生 v6 或新的模型能力版本。

最重要的控制层发现：现有夹爪 USD 的六个活动关节使用 acceleration 驱动；在同一低增益数值条件下，空中对照切换为 force 驱动后，最大关节误差从 0.800000 rad 降为 0.00031955 rad。该改善仅在隔离的空中闭合测试中得到验证，尚未推广到接触抓取、旧方块回归或 pi0.5 正式配置。

### 2. 已完成的实现与验证

| 模块 | 本轮改动 | 验证结果与边界 |
|---|---|---|
| 日用品资产 | 官方 Isaac 5.1 YCB 纹理杯、香蕉、汤罐、布丁盒 | 4/4 加载和落地检查通过；实际查看原始渲染图，纹理可见 |
| 物理配置 | 对视觉资产添加刚体、假设质量、摩擦和凸分解碰撞 | 不是实测物理参数；杯口/把手空腔碰撞尚未验收 |
| 资产完整性 | 校验米制、Z-up、尺寸、中心、刚体/碰撞合同、USD 和纹理 SHA | 损坏、缺碰撞、路径逃逸等测试通过 |
| RM65 场景接入 | `--development-object` 与 `--household-manifest` 支持真实纹理 USD | 保留历史方块默认路径；新对象结果均 development-only |
| 抓取标定 | 从实际接触垫 URDF 推导垫中心、近似开口、开发抓位 | 不再把原始指尖采样点误当接触垫中心；仍非视觉抓取规划 |
| 故障测量 | 区分物体接触与静态托台接触，记录夹爪目标/实际关节角 | 修复静态碰撞体过滤路径；旧错误零读数保留并标记不可用 |
| 控制诊断 | 空中闭合、低增益、驱动类型隔离对照 | force 对照显著改善跟踪，未修改原始 USD 或正式控制默认值 |
| 数据保护 | 资产/纹理与全部本轮录制分别归档，复制到本机 | 传输 SHA 一致；资产恢复验证通过，原始运行归档未逐文件恢复复核 |

资产来源沿用本机 Isaac Lab 使用的 NVIDIA 官方资源目录，不将其许可视为本项目代码许可。内置 OmniPBR 材质仍依赖 Isaac 运行时。所有日用品质量均显式标为仿真假设，未声称实测。

### 3. 实际实验结果

| 实验 | 实测 | 结论 |
|---|---|---|
| 四物体独立场景 | 4/4 落地静止检查通过 | 只证明本次环境中的资产与基础物理可运行；杯/罐发生侧倒，不是直立验收 |
| v5 布丁盒 | 120 段、600 动作；最大抬升 17.936 mm；最终目标平面误差 172.911 mm | 失败 |
| v5 香蕉 | 120 段、600 动作；最大抬升 0.650 mm；最终目标平面误差 174.654 mm | 失败 |
| 布丁盒原标准动作 | 提升 0.288 mm | 失败；当前 y 向宽 89.817 mm，明显超过近似最大开口 47.673 mm |
| 香蕉接触垫标定 | 垫中点 x 偏差不到 1 mm，接近关节误差约 0.011 rad；未提起 | 对准几何中心仍不足以稳定夹持 |
| 香蕉下移 15 mm | 托台接触峰值约 12.85/21.27 N；物体接触不足 1 N | 明确存在托台阻挡，继续向下压不可作为修复 |
| 空中原高增益 acceleration | 最大误差 0.167608 rad，两次结果一致 | 无物体/托台接触也有明显跟踪误差；2 秒保持末端仍在移动，不能称稳态误差 |
| 空中低增益 acceleration | 最大误差 0.800000 rad | 降低增益本身未改善 |
| 空中同数值增益 force | 最大误差 0.00031955 rad，末速度约 0.001 rad/s | 控制诊断改善；不是抓取或部署成功 |

以上不是随机抽样的泛化考试，不能将调参重复案例汇总成“日用品成功率”。标准动作提升量是关闭至抬升末端的差值，模型提升量为整段运行最大值，两者不可直接按同一统计量比较。

香蕉零偏移对照没有测到托台接触，但仍失败，因此托台阻挡不能解释全部失败。夹爪驱动、接触位置、联动关系、物体曲面和抓取稳定性仍需分开验证。现有仿真还继承了关闭机器人自碰撞、较高执行器参数及阶段性目标托台碰撞开关等历史假设；不能据此推导真机安全性或真实物理保真度。

### 4. 当前代码结构

工作仓库：`rm-ik-rl`，任务子目录：`projects/004-rm65-4c2-isaaclab`。

```text
projects/004-rm65-4c2-isaaclab/
├── openpi_extension/
│   ├── rm65_policy.py                 # 观测/动作接口适配（既有）
│   ├── rm65_training_config.py        # OpenPI 训练配置（既有）
│   ├── action_guard.py                # 动作约束（既有）
│   ├── expert_episode.py              # 轨迹记录格式（既有）
│   ├── multi_object.py                # 几何对象与开发结果隔离
│   └── household_assets.py            # 新增：真实纹理资产清单/校验/加载
├── scripts/
│   ├── run_pick_place_baseline.py     # 场景、标准动作、模型闭环、诊断入口
│   ├── run_recorded_expert_demo.sh     # 标准动作录制与诊断参数转发
│   ├── run_pi05_rm65_closed_loop.sh    # 模型服务器与仿真运行入口
│   ├── serve_rm65_policy.py           # pi0.5 推理服务（既有）
│   ├── train_rm65_pi05.py             # 训练入口（本轮未运行）
│   ├── convert_expert_episodes_to_lerobot.py # 训练数据转换（本轮未运行）
│   ├── inspect_household_asset_sources.py   # 官方资源目录检查
│   ├── prepare_household_assets.py          # 下载纹理、物理配置、生成清单
│   ├── probe_household_scene.py             # 渲染/落地验证
│   ├── household_grasp_calibration.py       # 接触垫几何推导
│   ├── audit_household_gripper_fit.py       # 开口/物体尺寸审计
│   ├── inspect_gripper_usd_drives.py        # 只读驱动模式审计
│   ├── relocate_household_manifest.py      # 恢复后重定位并验 SHA
│   ├── summarize_household_session.py      # 任务与诊断分别汇总
│   └── test_*                              # 单元、回归测试
├── config/                            # 既有配置
├── assets/ + generated/               # 机器人资源/生成模型；部分为既有链接
├── datasets/rm65_household_dev_*/      # 原始帧、动作和完整报告，不入 Git
├── outputs/household_assets_003/      # 四物体 USD 与纹理，不入 Git
├── outputs/openpi_checkpoints/        # v2–v5 等既有权重，本轮未改
├── results/household_*.json            # 小型资产清单、审计、摘要
└── docs/pi05_sim_deployment_record/
    ├── MULTI_OBJECT_ROADMAP_ZH.md
    ├── HOUSEHOLD_OBJECT_ITERATION_LOG.md
    └── HOUSEHOLD_SESSION_HANDOFF_ZH.md
```

主运行脚本仍偏大：场景、控制、记录、报告集中在同一文件。本轮为保护旧链路只增加受限开发入口，没有进行大规模重构。下一阶段可先把日用品诊断和场景配置拆分成模块，并增加控制模式的接口测试。

### 5. 验证、备份与复现

- 38 项 pytest 通过，原 grasp_geometry 独立脚本 9 项几何不变量通过；修改后的 Python 编译、两个 shell 入口语法检查通过。
- force 诊断开关在非规定诊断模式下被参数校验拒绝，不允许直接用于 pi0.5；原资产文件未覆盖。
- 摘要：`results/household_session_001_summary.json`；驱动审计：`results/household_gripper_drive_audit_001.json`；备份证据：`results/household_backup_001.json`。
- 本机备份目录：`C:/Users/95380/Documents/ChatGPT/robot learning/RM65_DATA_BACKUP_DO_NOT_GIT/household_2026_09_30`。
- 资产归档 40,570,880 字节，SHA `5616acdf49f8382ba4f670dc5882271db1959ac2d23e4d5ad53343b9cf1d082b`。
- 运行归档 385,576,960 字节，SHA `fc61918f404857137e5f6fc8f081eeae9db2e5f08dcdd51bf92d4d2e958d33d4`。
- 资产在全新本机目录实际解包、重定位、验证四份 USD 与全部纹理。原始运行 tar 完成安全成员/数量/字节及传输 SHA 检查，未宣称已完成解包后的逐文件恢复验证。
- 机器人 USD/URDF 快照仍含历史网格引用，不是独立跨机器机器人安装包。

下列命令用于后续复现参考，本轮收尾后不自动运行：

```bash
# 从项目根运行；必须使用全新输出路径。
PYTHONPATH=.:scripts /home/chengyu/robot-learning/openpi/.venv/bin/python -m pytest -q \
  scripts/test_household_assets.py scripts/test_household_grasp_calibration.py \
  scripts/test_relocate_household_manifest.py scripts/test_summarize_household_session.py \
  scripts/test_multi_object.py scripts/test_rm65_abort_settling.py

# 隔离空中驱动对照；不是抓取测试、不是训练示范。
RM65_DEVELOPMENT_OBJECT=ycb_banana \
RM65_HOUSEHOLD_MANIFEST=results/household_assets_003.json \
RM65_PAD_CALIBRATION_URDF=generated/rm65_4c2_wide_pads.urdf \
RM65_FREE_CLOSE_PROBE=1 RM65_FREE_CLOSE_SOFT_GAINS=1 RM65_FREE_CLOSE_FORCE_DRIVE=1 \
bash scripts/run_recorded_expert_demo.sh datasets/NEW_FREE_CLOSE_DIAGNOSTIC \
  0.8 0 0 "diagnose gripper closure above the banana" 930201
```

说明：空中报告的 `status=diagnostic`。当前录制包装器最后仍使用抓取任务门槛，故会显示 TASK=FAIL / 非零退出；须读取诊断报告，不把这个退出码解读为仿真崩溃，更不能将其改写为抓取 PASS。

### 6. 待确认的下一阶段及意义

1. **夹爪控制与联动校核。** 在独立分支/新配置里验证力驱动、合理力矩上限、速度、夹爪联动、自由开合重复性，再做接触测试。意义：先让“手按指令动”，避免把执行误差混进训练。
2. **日用品物理可行抓法。** 香蕉选可靠实体截面和净空；布丁盒测试可夹薄边/不同摆放；杯子研究杯把或局部抓位；汤罐若整径超过开口，明确夹爪能力限制，不能偷偷缩放模型。意义：先证明当前机械结构确实能够完成目标动作。
3. **冻结成功标准和数据划分。** 分开“提起、搬运、释放后稳定”，保留全新实例/条件用于最后考试。当前四个已分析实例均为开发集。意义：防止调好几个已知条件后误称泛化成功。
4. **只采集经过核验的多物体示范。** 多抓位、摆放、相机与光照；混合旧能力回归数据，在新目录训练新权重。意义：让模型学习 RM65 的日用品操作经验，而非继续只看方块。
5. **模型闭环与独立测试。** 每类分别报告结果、重复性、碰撞/掉落等事件；通过后再推进多物体指令选择和干扰物。意义：证明动作来自模型并能在新条件下重现。

这些步骤都有明确验证价值，但不保证每次训练或调参都提高成功率。尤其本轮 force 空中改善还不能保证日用品抓取改善。后续以受控对照和实测决定是否采纳，而不是保证一个尚未完成的结果。

## 二、大白话版

这次确实把方向换过来了：仿真里放进去的是有真实外观的杯子、香蕉、汤罐和布丁盒，不是把球叫苹果、把方块叫杯子。

但我现在不能说“机械臂已经会抓这些东西”。现有模型试了香蕉和布丁盒，都没完成。标准动作也没有抓稳。我把这些失败留下来，是为了分清到底是模型不会，还是“手本身就没按想的方式工作”。

目前查清了几件事：

- 布丁盒这个方向太宽，夹爪张开也不够，不能靠再用力解决。
- 香蕉往下抓会碰托台，手被挡住了；但不是所有失败都来自碰托台。
- 更关键的是，手在空中合拢都存在偏差。检查后发现驱动方式会显著影响效果。在单独的空中实验里换了驱动方式，手能非常接近要求的闭合位置。这一步有用，但还得实际抓东西验证。

所以这轮的成果是：**日用品环境搭起来了，真正的底层问题也抓到了一部分；“模型稳定抓日用品”还没完成。** 我没有为凑成功去缩小物体、改成绩标准，或者把失败数据直接拿去训练。

接下来最值得做的是先把这只“手”校好，再教它抓几种真的能夹住的物品，最后让模型学并用新物品考试。代码和记录已整理，数据没有丢，放在 Git 外的本机与远程备份中。按你的要求，这轮收尾后先停下，等你确认下一步。
