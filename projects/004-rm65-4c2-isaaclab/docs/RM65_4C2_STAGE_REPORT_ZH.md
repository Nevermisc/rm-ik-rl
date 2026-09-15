# RM65-B + 4C2 迁移到 Isaac Lab：阶段报告与复现手册

## 1. 这一步在整条路线中的位置

最终目标分成两段：

1. 在 Isaac Lab 中给出文字指令，让 RM65-B + 4C2 通过 π0.5 完成操作任务；
2. 把经过仿真验证的策略安全部署到真实 RM65-B。

项目 003 已经证明 π0.5 的 DROID checkpoint、WebSocket 服务和 Franka 参考环境能够形成闭环。项目 004 负责把机器人侧替换为自己的硬件模型，并把迁移中的不兼容问题逐项显式化。

本阶段完成的是模型、物理关节、相机观测和网络接口。它还不是 RM65 的 π0.5 操作任务闭环，因为现成 checkpoint 输出的是 Franka 的 7 个关节目标，RM65-B 只有 6 个关节。

## 2. 先理解五个对象

### URDF

URDF 是机器人结构说明书。它描述 link、joint、质量、惯量、碰撞模型和网格路径。RM65 与 4C2 原本各有一份 URDF，需要通过一个固定关节组合成一棵完整的机器人树。

### USD

USD 是 Isaac Sim 使用的场景和资产格式。URDF 更适合描述机器人结构，USD 更适合在仿真器中保存材质、物理属性和场景层。这里先生成组合 URDF，再由 Isaac Sim 的 URDF Importer 生成 USD。

### Articulation

Articulation 是物理引擎眼中的关节系统。模型能显示不代表它能正确控制；必须验证自由度名称、数量、限位、驱动器和状态读数。

### Observation

Observation 是策略每次推理看到的内容。本项目渲染两张 `480×640` RGB 图，送入模型前补边缩放为 `224×224`，并附带六个 RM65 关节角、一个夹爪开合量和文字指令。

### Action

Action 是策略输出的控制目标。现有 DROID checkpoint 输出 `15×8`：15 个未来时间步，每步为 7 个 Franka 绝对关节目标和 1 个夹爪命令。RM65 目标接口应是每步 6 个关节目标和 1 个夹爪命令，因此不能直接执行当前输出。

## 3. 使用的模型来源

机械臂模型来自实验室已有目录：

```text
~/robot-learning/rm-ik-rl/assets/RM65-B/
```

夹爪模型以 Windows 电脑上的以下目录为唯一来源：

```text
D:\d\4C2
```

同步到实验室电脑时只复制 `urdf/` 和 `meshes/`，没有复制安装程序和无关文件。模型资源不提交到 GitHub。

4C2 原始 URDF 包含：

- 9 个 link；
- 8 个 joint；
- 1 个主驱动关节 `gripper_joint`；
- 5 个 mimic 随动关节；
- 2 个固定关节。

RM65 和 4C2 都有名为 `base_link` 的 link。为了避免重名，组合脚本把夹爪的所有 link、joint 以及 mimic 引用统一加上 `tool_` 前缀，然后增加：

```text
rm65_to_4c2: link_6 -> tool_base_link
```

当前安装变换使用 `xyz="0 0 0"`、`rpy="0 0 0"`。从渲染图看尺度和方向合理，但在高精度接触仿真前仍要用真实法兰尺寸校准这组变换。

## 4. 实际完成的流水线

```text
RM65 URDF + meshes ─┐
                    ├─ build_combined_urdf.py
4C2 URDF + meshes ──┘          │
                               ▼
                rm65_4c2_software.urdf
                               │
                    import_combined_urdf.py
                               ▼
                 rm65_4c2_software.usd
                         │           │
                         │           └─ capture_observation.sh
                         │                       │
                         ▼                       ▼
              articulation smoke test     两张 RGB + 关节状态
                                                     │
                                                     ▼
                                      pi05_interface_dry_run.py
                                                     │
                                                     ▼
                                      只记录 π0.5 输出，不执行
```

## 5. 组合 URDF

在实验室电脑执行：

```bash
cd ~/robot-learning/004-rm65-4c2-isaaclab

python3 scripts/build_combined_urdf.py \
  --rm65-urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --rm65-mesh-dir ~/robot-learning/rm-ik-rl/assets/RM65-B/meshes \
  --gripper-urdf external/4C2/urdf/4C2.urdf \
  --gripper-mesh-dir external/4C2/meshes \
  --gripper-root-link base_link \
  --gripper-name-prefix tool_ \
  --output generated/rm65_4c2_software.urdf \
  --report outputs/combined_urdf_report.json
```

验证结果：

| 项目 | 结果 |
|---|---:|
| link 数量 | 16 |
| URDF joint 数量 | 15 |
| 可动 joint 数量 | 12 |
| mesh 引用数量 | 32 |
| 4C2 主关节 | `tool_gripper_joint` |
| 4C2 mimic 随动关节 | 5 |

这里的 12 个可动关节不代表真实硬件有 12 个电机。它包括 6 个机械臂关节、1 个夹爪主关节和 5 个夹爪随动关节。原始 URDF 的 mimic 关系会记录在报告中，但最终组合 URDF 移除 mimic 标签，由仿真控制器把一个夹爪标量同步给六个关节；策略状态仍只使用主关节。

## 6. 导入 USD

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/import_combined_urdf.py \
  --urdf generated/rm65_4c2_software.urdf \
  --usd generated/rm65_4c2_software.usd \
  --report outputs/import_report.json \
  --headless
```

验证结果：

```text
imported_path=/rm65_4c2
articulation_root=/rm65_4c2/root_joint
usd_joint_count=16
gripper_coupling=software_coupled_joint_targets
```

USD 比 URDF 多出的一个 joint 是导入器为固定基座生成的 root joint。

## 7. 关节与驱动测试

最终验收让 RM65、夹爪基座和两个固定支座承受重力，只对出现异常响应的六个 4C2 活动指节关闭重力：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/articulation_smoke_arm_gravity.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --disable-moving-gripper-gravity \
  --headless
```

测试让所有关节执行一段有界正弦运动，再回到零位。通过条件和实测值如下：

| 指标 | 通过条件 | 实测 |
|---|---:|---:|
| 数值包含 NaN/Inf | 必须否 | 否 |
| 六轴最大回零误差 | `< 0.03 rad` | `0.00823 rad` |
| 夹爪最大回零误差 | `< 0.08 rad` | `0.00134 rad` |
| 六轴最小实际运动量 | `> 0.03 rad` | `0.07554 rad` |
| 夹爪最小实际运动量 | `> 0.10 rad` | `0.47746 rad` |

无重力的结构隔离测试也通过，六轴/夹爪最大回零误差分别为 `0.00300 rad` 和 `0.00460 rad`。

组合模型还通过了 Lula 全位姿 IK 一致性测试。求解器确认前六个自由度依次为 `joint_1..joint_6`，后六个 `tool_*` 自由度不参与机械臂 IK。对一个由已知关节角生成的可达目标，求解结果写回组合 USD 后的位置误差为 `1.03×10⁻⁶ m`，旋转误差为 `9.18×10⁻⁴ rad`。这证明加装 4C2 后没有破坏 RM65 的关节顺序和 `link_6` 运动学。

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_combined_ik.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/combined_ik_test.json
```

### 从“能动”到“按目标到位”

`run_reach_baseline.py` 把红方块放在一个保证可达的目标正下方，让 Lula 求出 `link_6` 的全位姿 IK，再用三次平滑曲线插值关节目标。末端与预抓取位姿的距离从 `0.10748 m` 降到 `9.69×10⁻⁷ m`，最大单步命令为 `0.00218 rad`。

随后 `run_reach_robustness_suite.py` 用固定种子在安全关节区间采样 12 个不同目标。每个目标都由正运动学生成，所以“目标可达”是已知条件；评测检查的是 IK 收敛、组合 USD 的六轴映射、平滑命令和物理跟踪是否稳定。结果为 `12/12`：

| 指标 | 结果 |
|---|---:|
| 成功率 | `100%` |
| 最差位置误差 | `0.00002091 m` |
| 最差旋转误差 | `0.000996 rad` |
| 最差关节跟踪误差 | `0.00004276 rad` |
| 最大单步命令 | `0.03909 rad` |

这两项是传统 IK 专家基线，并不是 π0.5 结果。它们也只做到红方块上方 10 cm 的预抓取位姿，没有夹爪接触、闭合或搬运。4C2 目前仍使用活动指节重力隔离近似，当前不能把“到位”写成“抓取成功”。

### 夹爪开合方向与静态闭合

只看关节角无法确认正方向到底表示张开还是闭合。`test_gripper_aperture.py` 从 STL 包围盒选取局部指尖代理点，再通过刚体姿态变换到世界坐标。夹爪标量从 `0` 增加到 `0.85 rad` 时：

| 指尖代理对 | `0 rad` 距离 | `0.85 rad` 距离 | 趋势 |
|---|---:|---:|---|
| `l_3/r_3` | `91.40 mm` | `22.57 mm` | 单调减小 |
| `l_2/r_2` | `72.90 mm` | `2.88 mm` | 单调减小 |

因此当前接口明确规定 `gripper=0` 为张开、`gripper=1` 为闭合。这里测的是 STL 代理点，不是经过卡尺标定的真实有效开口。

随后把一个关闭重力的 `60×40×25 mm` 悬浮测试块对齐到二级指尖中心，移除桌面，并用两侧指尖和末端位置构造夹爪局部正交坐标系，使块宽沿实际开合轴。4C2 全部 9 个 link 各有一个按测试块路径过滤的接触传感器，测试块还有一个不过滤的全接触传感器。PhysX 全局接触处理明确开启，所有传感器都成功绑定。

六个夹爪关节缓慢闭合到 `0.65 rad`，过程没有 NaN/Inf；最终两组指尖代理间距为 `17.49 mm` 和 `35.59 mm`。安全默认将块沿末端外向移动 10 mm，此时测试块位移和接触力均为 0。零偏移对照测到 `0.136 N`，测试块被推出 `0.04797 m`；逐 link 过滤结果显示全部力来自 `tool_base_link`，左右三段活动指节都是 0 N，因此这不是夹持。外移 20 mm 同样无接触；把质量从 30 g 增至 300 g 和 1 kg 也不能形成稳定夹持。由此确认当前 `convexHull` 没有提供可用的双侧指面接触区。

实验性地继续移动机械臂时，程序最初在运输第一步退出。补充“关闭应用前先打印 Python traceback”后，确认根因不是 PhysX 原生崩溃，而是 NumPy `float64` 运输命令写入 PyTorch `float32` 关节目标张量。把命令显式转换为目标张量的数据类型后，1% 和完整幅度运动都能执行到底。

USD 物理清单还确认组合资产包含 16 个刚体和 16 个启用碰撞体，4C2 的 9 个 link 均有启用的碰撞几何。每个碰撞 prim 都是包含 Mesh 子节点的 instance-proxy Xform，并使用 `convexHull` 近似。因此问题不是“导入后完全没有碰撞体”，而是凸包没有形成与视觉指面一致的可用抓取区域。

为建立可用的静态接触基线，脚本把安全位置中的测试块姿态反算到 `tool_l_2` 和 `tool_r_2` 局部坐标，并在 URDF 导入前加入两个 `25×10×20 mm` 薄盒碰撞垫。新 USD 有 18 个启用碰撞体；关节/回零、Lula IK 和 12 目标到位回归均保持通过。中心、横向 ±2 mm、末端外向 8 mm 和 12 mm 共 5 个位置全部得到双侧接触：最小左/右力为 `0.07786/0.06647 N`，最大基座力为 0 N，最大物体位移为 `1.370 mm`。

在运输阶段，脚本先完成双侧接触判定，再恢复 30 g 测试块重力，并使用静摩擦 `1.5`、动摩擦 `1.2`、`max` 合并模式和 1 秒平滑关节轨迹。中心、沿开合轴 -2 mm 和 +2 mm 三个位置均通过：最小末端抬升 `60.80 mm`，最小物体抬升 `37.60 mm`，最大物体相对夹爪位置变化 `29.83 mm`，低于 `40 mm` 门槛。

这证明当前碰撞代理能够完成“物体已在指间时闭合并抬升”的物理基线，但还不是完整抓取任务。测试块初始悬浮在指间，没有从桌面接近、接触、提起、放置和松开的完整过程；碰撞垫也来自仿真姿态反算，还没有按真实 4C2 指面尺寸校准。

### 带开发辅助的搬运与放置状态机

`run_pick_place_baseline.py` 在上述接触运输基础上继续验证闭合、抬升、绕底座转运、落台和撤离。最初尝试用 Lula 生成五段保持末端姿态的笛卡尔接近路径，但在移除方块、源支撑和目标平台碰撞后，机械臂仍无法在重力下跟踪到抓取关节角：最大关节误差约 `0.465 rad`。直接初始化在同一抓取关节角后，机械臂也会下垂约 `0.151 rad`。这说明当前动态接近失败的主要问题是 RM65 仿真执行器和重力补偿，而不是路径上的方块或平台碰撞。

为继续隔离后半程，开发基线明确加入四项辅助：

1. 仿真直接初始化在已验证的抓取姿态；
2. 方块在夹爪闭合前关闭重力，闭合后恢复重力；
3. 目标平台在转运完成后才启用碰撞，避免与连杆扫掠区重叠；
4. 打开夹爪后将方块向下分离 `50 mm`，并赋予 `0.10 m/s` 向下初速度，解除碰撞垫的几何卡滞。

在关节 1 转动 `0.6`、`0.8`、`1.0 rad` 三种情况下，状态机均通过：

| 指标 | 三次结果 |
|---|---:|
| 通过次数 | `3/3` |
| 最小物体抬升 | `0.03783 m` |
| 最小横向搬运距离 | `0.15928 m` |
| 最大最终落点误差 | `0.00520 m` |
| 最大落台后漂移 | `3.73×10⁻⁹ m` |
| 最小最终二级指尖开口 | `0.07290 m` |

运行单次 0.8 rad 测试：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_pick_place_baseline.py \
  --usd generated/rm65_4c2_contact_pads.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/pick_place_robust_0p8.json \
  --transfer-joint-1-rad 0.8 \
  --initialize-at-grasp \
  --headless

python3 scripts/summarize_pick_place_assisted.py
```

原始报告将 `unassisted_full_task_complete` 固定为 `false`，汇总状态为 `pass_with_simulation_assistance`。这三次结果证明后半程状态转换和目标落台指标可用，不证明动态接近、自然释放或 π0.5 控制成功，也不能直接作为训练示范数据。

### 动态接近与自然重力抓取边界

后续把预抓取距离参数化为 2、4、6、10 cm，并去掉“直接初始化在抓取位”。四次测试都执行了逐厘米笛卡尔路点、闭合、抬升、转移和辅助放置，结果为 4/4：最小物体抬升 `0.03730 m`，最大最终落点误差 `0.00863 m`，最大抓取位关节误差 `0.14785 rad`。因此动态接近本身已经跑通；这些测试仍在闭合前临时关闭方块重力，所以不能称为自然桌面抓取。

自然重力实验加入 `120×18×20 mm` 条形开发支撑。宽平台会挡住 4C2 手指下探，过窄且过短的平台又会让方块在侧向接近时被推落；条形支撑沿接近方向提供长度，同时在开合方向给手指留出空间。

脚本加入六个活动指节对方块的过滤接触传感器。最初只记录接触历史中的最大值，因此 `tool_l_2/tool_r_2` 的 `0.07181/0.07275 N` 只能证明曾经碰撞，不能证明闭合结束时仍在夹持。加入当前力和最近时间窗口均值后，对原始 `25×10×20 mm` 经验垫扫描 0.45 至 0.75 rad，7 次都没有持续双侧当前接触。

原始 4C2 二级指节 mesh 的包围盒约为 `47.43×20.39×18 mm`。为了验证“接触面过小”这一假设，构建脚本加入 `--4c2-contact-pad-size-m` 参数，并生成独立的 `40×14×18 mm` 宽垫候选资产。0.65 rad 闭合时，左右当前力为 `0.06147/0.03779 N`，最近窗口均值为 `0.05164/0.05132 N`，说明持续双侧接触已经建立。它仍是根据 mesh 和仿真表现选出的经验碰撞体，尚未用实物尺寸和材料标定。

旧抬升命令还有一个运动学问题：抓取姿态加入 −40 mm 世界 x 修正后，固定的参考关节角会让末端水平移动约 177 mm，只上升约 39 mm。脚本现支持 `cartesian_vertical` 模式，由当前抓取位通过 Lula IK 计算世界 z 方向的 40 mm 抬升目标。配合世界 z 方向 −53 mm 抓取修正、宽碰撞垫、更高驱动增益以及运输期间关闭机械臂重力，末端实际上升 `39.64 mm`，方块上升 `39.07 mm`。

在转运角 0.8 rad 的单次实验中，方块从开始就承受重力，机械臂从 10 cm 外接近，随后完成闭合、抬升、约 17 cm 转运和辅助放置；最终位置误差为 `2.918 mm`。三种转运角 0.6、0.8、1.0 rad 的复测中，抓取和抬升均成功，最近窗口双侧力至少为 `0.56856/0.50409 N`，但完整验收仅通过 1/3：0.6 rad 落台后漂移 `43.09 mm`，1.0 rad 最终误差 `52.02 mm`。

去掉向下分离辅助后，方块仍被夹爪夹住；即使夹爪张开后向上撤离 80 mm，方块也被一起带到约 `z=0.839 m`。因此当前准确结论是“自然重力动态抓取、竖直抬升和转运已跑通，释放与落台尚不鲁棒”。通过实验仍包含运输期间关闭机械臂重力、六个活动指节重力隔离、未经实物标定的宽碰撞垫、转运后才启用目标平台碰撞，以及 50 或 80 mm 向下分离和 0.10 m/s 初速度。控制器是脚本专家，`pi05_used=false`，也没有向真机发送命令。

复现宽垫构建与自然重力测试：

```bash
python3 scripts/build_combined_urdf.py \
  --rm65-urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --rm65-mesh-dir ~/robot-learning/rm-ik-rl/assets/RM65-B/meshes \
  --gripper-urdf external/4C2/urdf/4C2.urdf \
  --gripper-mesh-dir external/4C2/meshes \
  --gripper-root-link base_link --gripper-name-prefix tool_ \
  --add-4c2-contact-pads \
  --4c2-contact-pad-size-m 0.040 0.014 0.018 \
  --output generated/rm65_4c2_wide_pads.urdf \
  --report outputs/wide_pads_urdf_report.json

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/import_combined_urdf.py \
  --urdf generated/rm65_4c2_wide_pads.urdf \
  --usd generated/rm65_4c2_wide_pads.usd \
  --report outputs/wide_pads_import_report.json --headless

bash scripts/run_pick_place_natural_suite.sh
```

### 4C2 重力限制是怎样发现的

保留 mimic 约束时，只驱动主关节会让五个 follower 自动运动，无重力测试通过；但开启重力后指节跑到上限。随后逐项排查：

1. 把夹爪 effort 从 `50` 提高到 `500`、stiffness 从 `200` 提高到 `2000`；
2. 设置 `parse_mimic=false` 并导入到全新 USD；
3. 在组合 URDF 中直接移除所有 `<mimic>` 标签，使用软件耦合。
4. 完全移除地面，排除模型与地面穿插；
5. 把物理时间步从 `1/120 s` 缩小到 `1/1000 s`；
6. 把过小的质量提高到 `0.02 kg`、对角惯量提高到 `1×10⁻⁵ kg·m²` 并清零交叉惯量；
7. 只关闭四个远端指节的重力，观察剩余两个一级活动指节。

高增益时两个仅约 10 克的指节仍请求约 `537 Nm`。移除地面、1 kHz 时间步和惯量正则化都失败，说明这不是地面接触、时间步或微小惯量单独造成的。只关闭四个远端指节重力后，那四个关节稳定，但两个一级活动指节停在约 `0.28 rad`，从而把异常范围定位到六个活动刚体。

最终方案只禁用 `tool_r_1`、`tool_l_1`、`tool_r_2`、`tool_l_2`、`tool_r_3`、`tool_l_3` 的重力。夹爪基座与两个固定支座仍传递约 74% 的夹爪质量，RM65 重力也保持开启。该方案通过有界运动和回零测试，但仍是物理近似；接触抓取前必须继续校准碰撞体、传动关系和真实质量参数。

补充诊断命令：

```bash
# 检查 URDF importer 是否会自动执行 mimic 约束
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/gripper_master_only.json \
  --gripper-control-mode master-only \
  --headless

# 不隔离夹爪重力，可复现当前已知失败
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/articulation_smoke_gravity.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --headless
```

## 8. 生成 π0.5 观测

```bash
./scripts/capture_observation.sh
```

输出包括：

```text
outputs/observation/external_rgb.png
outputs/observation/wrist_rgb.png
outputs/observation/observation.json
```

脚本用两个隔离的 Isaac Sim 进程分别采集外部和腕部视图，绕开当前驱动组合下的双相机原生退出问题，再合并为一个 observation。两张图片都是 `480×640×3 uint8`；像素标准差分别为 `50.64` 和 `64.63`。外部图检测到 966 个红色目标像素，腕部图检测到 1256 个，因此不只是“非空”，而是目标物确实可见。客户端随后使用与 OpenPI 相同的补边缩放得到 `224×224`。

腕部相机采用显式工具坐标变换。脚本先保存相机相对 `tool_base_link` 的局部偏移和朝向，再用末端世界位姿更新相机。验证时改变六轴姿态，相机随末端移动了 `0.01818 m`，相机到末端的距离从 `0.180277586 m` 变为 `0.180277526 m`，差值仅 `5.96×10⁻⁸ m`；两次相机位姿命令误差均为 0。第二姿态下方块离开腕部视野，这是固定相机随机械臂转向的正常结果，不作为安装失败。闭环任务中要在每个仿真步调用同样的更新，并用实物安装尺寸校准局部外参。

## 9. 启动 π0.5 并做接口 dry-run

启动 DROID joint-position checkpoint：

```bash
./scripts/start_pi05_droid_server.sh
```

把 RM65 仿真观测发送给 π0.5：

```bash
./scripts/run_pi05_interface_dry_run.sh --prompt "pick up the red cube"
```

最后释放显存：

```bash
./scripts/stop_pi05_server.sh
```

dry-run 会临时在 6 个 RM65 关节后补一个值为零的虚拟关节，只为了验证 DROID 服务的网络和张量接口。返回动作只写入 JSON，`executed` 永远为 `false`。

最终有效图像的实测结果：

| 项目 | 结果 |
|---|---:|
| 输入关节 shape | `(7,)`，六轴加一个虚拟零值 |
| 两张模型输入图 | `(224, 224, 3)` |
| 输出动作 shape | `(15, 8)` |
| 输出是否含 NaN/Inf | 否 |
| 新进程首次推理 | `152.096 s` |
| 同进程稳态推理 | `0.316 s` |
| 是否执行动作 | 否 |

这一做法不能作为控制映射。删除 Franka 第七轴或取前六维，都不能保持末端位姿、碰撞关系或动作分布。

## 10. 当前接口定义

机器人的目标观测：

```text
external_rgb:          uint8[480,640,3] -> padded uint8[224,224,3]
wrist_rgb:             uint8[480,640,3] -> padded uint8[224,224,3]
rm65_joint_position:   float[6], rad
gripper_position:      float[1], 0~1
prompt:                string
```

未来 RM65 checkpoint 的目标动作：

```text
action[t] = [q1, q2, q3, q4, q5, q6, gripper]
```

其中 `q1..q6` 是 RM65 绝对目标关节角，`gripper` 是归一化开合目标。完整机器可读定义见 `config/rm65_pi05_interface.json`。

## 11. RM65 transform 与动作安全层

`openpi_extension/rm65_policy.py` 已经实现未来 RM65 checkpoint 所需的数据变换：输入为六个 RM65 关节角、一个夹爪量、两张图和文字，输出为六个绝对关节目标加一个夹爪目标。它已在 OpenPI 容器中通过合成数据单元测试：

```text
state:         (7,)
action input:  (16, 7)
action output: (16, 7)
两张图:        (480, 640, 3)
```

`openpi_extension/action_guard.py` 为未来输出增加确定性保护：

- 输入 shape 必须是 `(T, 7)`；
- 遇到 NaN 或 Inf 立即拒绝；
- 六轴目标保留 `0.02 rad` 的限位余量；
- 相邻控制目标最大变化为 `0.05 rad`；
- 夹爪量裁剪到 `[0, 1]`。

测试覆盖越界、过大步长、夹爪越界和 NaN，全部通过；实测最大输出步长为 `0.0500000007 rad`（浮点舍入误差范围内）。这些保护还没有接入真机控制，它们是未来闭环执行器的前置组件。

## 12. 为什么现在还不能让 π0.5 控制 RM65

现成 DROID checkpoint 熟悉的是：

```text
Franka 七轴运动学
Robotiq 夹爪
DROID 相机安装与画面分布
DROID 关节位置归一化统计
DROID 任务和环境分布
```

自己的系统是：

```text
RM65 六轴运动学
4C2 夹爪
自己的相机安装位置
自己的零位、限位与控制频率
自己的桌面和物体
```

两者维度不同只是最明显的问题。即使维度碰巧相同，关节值的物理含义和训练分布仍然不匹配。

## 13. 下一阶段怎样形成真正闭环

下一项目应按以下顺序推进：

1. 在目标平台上方加入笛卡尔下降阶段，接近平台后再张开夹爪，消除释放分离辅助并完成三种转运角复测；
2. 用真实夹爪尺寸和材料校准碰撞垫，恢复机械臂重力，并对方块初始位置、质量和摩擦做扰动评测；
3. 校准腕部相机外参，把双相机采集、状态读取和动作执行合并进同一个固定步长 Isaac Lab 环境；
4. 用已经通过的专家控制器记录每个控制时刻的两张图片、六轴关节角、夹爪状态、七维目标动作和语言指令；
5. 转换为 OpenPI 使用的小型 LeRobot 数据集；
6. 新建 RM65 专用输入/输出 transform、归一化统计和训练配置；
7. 从 π0.5 checkpoint 微调；
8. 在多个方块位置、光照和语言表达下做闭环仿真评测；
9. 加入关节限位、单步变化限制、碰撞和工作空间保护；
10. 最后才连接真实 RM65，在有人值守、低速和空工作区条件下测试。

OpenPI 本机说明建议，小型自有数据集使用 LeRobot；完整 DROID 才使用约 1.8 TB 的 RLDS 数据。本项目无需下载完整 DROID。

## 14. 本阶段能写进简历的内容

可以如实描述为：

> 将 RM65-B 六轴机械臂与自有 4C2 夹爪 URDF 组合并导入 Isaac Lab，处理命名冲突、mesh 路径、mimic 关节和驱动配置；建立双相机与关节状态观测接口，完成 articulation 有界运动/回零测试，并实现 π0.5 DROID checkpoint 的非执行式接口验证，为 RM65 专用数据采集与微调建立可复现基线。

还可以补充经过机器可读报告支撑的最新进展：

> 为 RM65 + 4C2 构建自然重力抓取脚本专家，修正笛卡尔抬升轨迹并增加接触力时序诊断，实现从 10 cm 外接近、双侧夹持、39 mm 抬升和约 17 cm 转运；定位释放几何卡滞为当前瓶颈，并建立三转运角复测与失败证据。

暂时不要写“π0.5 已经控制 RM65 完成抓取”，因为当前 checkpoint 的动作还没有在 RM65 上执行。

## 15. 复现环境

| 组件 | 版本或状态 |
|---|---|
| GPU | NVIDIA GeForce RTX 4060 Ti 16 GB |
| NVIDIA Driver | 575.57.08 |
| Isaac Sim | 5.1.0 |
| Isaac Lab commit | `37ddf62` |
| OpenPI commit | `15a9616` |
| Docker | 29.3.1 |
| 系统 Python | 3.10.12 |
