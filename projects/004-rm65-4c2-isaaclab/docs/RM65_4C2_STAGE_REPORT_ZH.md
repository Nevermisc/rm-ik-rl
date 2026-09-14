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

最终验收让 RM65 承受重力，只对存在非物理闭链约束力的 4C2 刚体关闭重力：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/articulation_smoke_arm_gravity.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --disable-gripper-gravity \
  --headless
```

测试让所有关节执行一段有界正弦运动，再回到零位。通过条件和实测值如下：

| 指标 | 通过条件 | 实测 |
|---|---:|---:|
| 数值包含 NaN/Inf | 必须否 | 否 |
| 六轴最大回零误差 | `< 0.03 rad` | `0.00109 rad` |
| 夹爪最大回零误差 | `< 0.08 rad` | `0.00070 rad` |
| 六轴最小实际运动量 | `> 0.03 rad` | `0.07870 rad` |
| 夹爪最小实际运动量 | `> 0.10 rad` | `0.49209 rad` |

无重力的结构隔离测试也通过，六轴/夹爪最大回零误差分别为 `0.00300 rad` 和 `0.00460 rad`。

组合模型还通过了 Lula 全位姿 IK 一致性测试。求解器确认前六个自由度依次为 `joint_1..joint_6`，后六个 `tool_*` 自由度不参与机械臂 IK。对一个由已知关节角生成的可达目标，求解结果写回组合 USD 后的位置误差为 `1.03×10⁻⁶ m`，旋转误差为 `9.18×10⁻⁴ rad`。这证明加装 4C2 后没有破坏 RM65 的关节顺序和 `link_6` 运动学。

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_combined_ik.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/combined_ik_test.json
```

### 4C2 重力限制是怎样发现的

保留 mimic 约束时，只驱动主关节会让五个 follower 自动运动，无重力测试通过；但开启重力后指节跑到上限。随后执行了三组排查：

1. 把夹爪 effort 从 `50` 提高到 `500`、stiffness 从 `200` 提高到 `2000`；
2. 设置 `parse_mimic=false` 并导入到全新 USD；
3. 在组合 URDF 中直接移除所有 `<mimic>` 标签，使用软件耦合。

高增益时两个仅约 10 克的指节仍请求约 `537 Nm`，证明这不是正常重力负载，而是导入后的约束/关节模型问题。最终方案保留 RM65 重力、4C2 关节和碰撞，只禁用 4C2 各刚体重力。夹爪总质量为 `0.236 kg`；在接触抓取任务前仍要继续校准碰撞体和关节模型。

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

脚本用两个隔离的 Isaac Sim 进程分别采集外部和腕部视图，绕开当前驱动组合下的双相机原生退出问题，再合并为一个 observation。两张图片都是 `480×640×3 uint8`；像素标准差分别为 `50.64` 和 `64.58`。外部图检测到 966 个红色目标像素，腕部图检测到 1260 个，因此不只是“非空”，而是目标物确实可见。客户端随后使用与 OpenPI 相同的补边缩放得到 `224×224`。

这里的腕部视图仍是接口原型：脚本读取 `link_6` 当前位姿，由它计算相机位置，再在隔离进程中拍一张图。相机尚未在连续环境里作为 `link_6` 子节点随机械臂运动。建立闭环任务时必须把相机真正挂到末端，并用实物安装尺寸校准外参。

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

1. 在 Isaac Lab 为 RM65 建立一个明确的单任务场景，例如“抓起红色方块并放入托盘”；
2. 写一个不依赖 π0.5 的专家控制器，先证明 RM65 和 4C2 在物理层可以完成任务；
3. 固定外部和腕部相机的安装参数；
4. 记录每个控制时刻的两张图片、六轴关节角、夹爪状态、七维目标动作和语言指令；
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
