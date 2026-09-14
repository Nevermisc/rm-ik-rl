# 004 - RM65 + 4C2 夹爪迁移到 Isaac Lab

这个项目把实验室的 RM65-B 机械臂和 4C2 两指夹爪整理成一个可复现的 Isaac Lab 仿真资产，并建立后续接入 π0.5 所需的状态与动作接口。

## 本阶段为什么不能直接接 π0.5

已经验证的 π0.5 checkpoint 针对 DROID 风格的 Franka：输入包含 7 个 Franka 关节角，输出是 7 个 Franka 绝对目标关节角和 1 个夹爪命令。RM65 只有 6 个关节，关节零位、运动学和夹爪定义也不同。因此不能把前 6 个输出直接发送给 RM65。

本项目先完成三个安全前置条件：

1. 组合 RM65 与真实 4C2 模型；
2. 在 Isaac Lab 中验证全部关节可读取、可复位、可受限控制；
3. 明确 π0.5 与 RM65 之间哪些字段兼容、哪些字段必须通过自有数据微调。

## 当前结果

已完成并验证：

- 使用用户提供的 `D:\\d\\4C2` 作为夹爪模型来源；
- 生成 RM65-B + 4C2 组合 URDF：16 个 link、15 个 joint；
- 导入 USD，articulation root 为 `/rm65_4c2/root_joint`；
- 识别 6 个 RM65 关节和 6 个 4C2 物理自由度，并把单一夹爪命令软件耦合到所有指节；
- 有界运动与回零测试通过，所有状态均为有限数值；
- Lula 全位姿 IK 在组合 USD 上通过，正确映射六轴并跳过夹爪自由度；
- 传统 IK 专家控制器完成红方块上方 10 cm 的平滑预抓取到位；
- 12 个随机可达目标的到位鲁棒性评测全部通过；
- 验证 4C2 的正方向为闭合：两组指尖代理距离均单调减小；
- 25×60×25 mm 悬浮测试块周围的静态闭合保持有限数值，测试块被推出 `0.03671 m`；诊断图显示初始摆位有几何穿插且过滤接触力为 0 N，因此该结果不能视为有效夹持；
- USD 物理清单确认 16 个刚体、16 个启用的碰撞体，4C2 的 9 个 link 均保留碰撞；
- 定义外部/腕部 RGB、六轴关节和夹爪状态的 π0.5 观测接口；
- 实现 RM65 专用 OpenPI 输入/输出 transform，并在 OpenPI 容器内通过单元测试；
- 实现关节限位、最大单步变化和非有限数值拒绝的动作安全层；
- DROID checkpoint 的输出只做接口 dry-run，不发送给仿真或真机。

最终验证数据：

| 检查 | 结果 |
|---|---:|
| 无重力结构测试 | PASS |
| RM65 与 4C2 固定部分开启重力、六个活动指节隔离重力 | PASS |
| 组合 USD 的 Lula IK 位置误差 | `0.00000103 m` |
| 组合 USD 的 Lula IK 旋转误差 | `0.000918 rad` |
| 单次预抓取最终位置误差 | `0.00000097 m` |
| 多目标预抓取评测 | `12/12`，100% |
| 多目标最差位置误差 | `0.00002091 m` |
| 多目标最大命令步长 | `0.03909 rad` |
| 4C2 指尖距离趋势 | 正方向单调闭合，PASS |
| 4C2 静态闭合稳定性 | PASS，接触未确认 |
| 悬浮测试块闭合期间位移 | `0.03671 m` |
| USD 刚体 / 启用碰撞体 | `16 / 16` |
| 外部图红色目标像素 | 966 |
| 腕部图红色目标像素 | 1256 |
| 腕部相机随末端移动 | `0.01818 m`，PASS |
| 相机到末端距离变化 | `5.96×10⁻⁸ m` |
| π0.5 输出 | `15×8`，全部有限 |
| π0.5 首次推理 | `152.10 s` |
| π0.5 稳态推理 | `0.316 s` |
| RM65 transform 单元测试 | PASS |
| 动作安全层单元测试 | PASS |
| 策略动作被执行 | 否 |

![外部相机观测](docs/images/external_rgb.png)

![腕部相机观测](docs/images/wrist_rgb.png)

![夹爪闭合测试场景](docs/images/gripper_close_diagnostic.png)

完整过程、概念解释和实测数据见 [阶段报告与复现手册](docs/RM65_4C2_STAGE_REPORT_ZH.md)。

机器可读证据在 `results/`：组合/导入报告、无重力与重力隔离测试、已知重力失败、观测报告以及 π0.5 首次/稳态 dry-run。

腕部相机采用显式工具坐标变换：保存相机相对 `tool_base_link` 的局部位姿，每个仿真步根据末端姿态更新相机。两组机械臂姿态验证了相机移动 `0.01818 m`，相机到末端距离仅变化 `5.96×10⁻⁸ m`，两次位姿命令误差均为 0。当前双相机仍分别在两个 Isaac Sim 进程中采集，闭环任务环境还要把同一更新函数放入每个控制周期，并根据实物安装尺寸校准外参。

## 实验室资产

默认使用以下文件；可以通过命令行参数替换：

```text
RM65 URDF:
~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf

RM65 meshes:
~/robot-learning/rm-ik-rl/assets/RM65-B/meshes

4C2 URDF:
external/4C2/urdf/4C2.urdf

4C2 meshes:
external/4C2/meshes
```

模型文件较大，不上传 GitHub。本项目上传生成脚本、接口说明和小型验证结果。

## 运行顺序

在本项目目录执行：

```bash
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

导入为 USD：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/import_combined_urdf.py \
  --urdf generated/rm65_4c2_software.urdf \
  --usd generated/rm65_4c2_software.usd \
  --report outputs/import_report.json \
  --headless
```

运行受限关节控制测试：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/articulation_smoke.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --disable-moving-gripper-gravity \
  --headless
```

确认组合 USD 的前六轴顺序和 Lula 全位姿 IK 映射：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_combined_ik.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/combined_ik_test.json
```

先用传统 IK 专家控制器验证预抓取到位，再测试多个可达目标：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_reach_baseline.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/reach_baseline.json

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/run_reach_robustness_suite.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/reach_robustness.json \
  --trials 12 --seed 7
```

这两项只完成“移动到预抓取位姿”，没有闭合夹爪、接触方块或搬运方块，因此不能称为抓取成功。

验证夹爪开合方向与默认安全的静态闭合：

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_gripper_aperture.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/gripper_aperture_test.json \
  --headless

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_gripper_close_stability.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/gripper_close_stability.json \
  --headless
```

第二个脚本使用关闭重力的悬浮测试块且不放置桌面，以免把桌面接触力误判为夹爪接触。当前测试块摆位会与复杂 STL 碰撞近似发生穿插，因此只把它用作数值稳定性诊断。默认不会移动机械臂。实验性的 `--attempt-lift` 路径目前会在机械臂开始移动时触发 PhysX 原生退出，只用于复现问题。

生成两张 `480×640` RGB 观测图和关节状态；客户端会补边缩放为模型使用的 `224×224`：

```bash
./scripts/capture_observation.sh
```

启动 π0.5、发送一次非执行式接口请求并停止服务：

```bash
./scripts/start_pi05_droid_server.sh
./scripts/run_pi05_interface_dry_run.sh --prompt "pick up the red cube"
./scripts/stop_pi05_server.sh
```

验证未来 RM65 transform 和动作安全层，并汇总全部阶段证据：

```bash
docker start libero-openpi_server-1
docker exec -e PYTHONPATH=/rm65_project libero-openpi_server-1 \
  /.venv/bin/python3 /rm65_project/scripts/test_rm65_policy_transform.py
docker stop libero-openpi_server-1

PYTHONPATH=. python3 scripts/test_action_guard.py
python3 scripts/summarize_stage_results.py
```

接口的机器可读定义在 [rm65_pi05_interface.json](config/rm65_pi05_interface.json)。

## 安全边界

这些脚本只控制 Isaac Lab 中的仿真 articulation，不包含 ROS2 真机控制接口。π0.5 原始动作只允许记录和分析；在完成 RM65 数据采集、动作定义与微调以前，不允许转成真机命令。

4C2 的六个活动指节在 PhysX 重力下会出现非物理大扭矩，因此最终 USD 移除 mimic 标签，由仿真控制层同步六个夹爪关节，并只对这六个活动指节关闭重力。RM65、夹爪基座和两个固定支座仍启用重力，夹爪碰撞与关节运动仍保留。去除地面、1 kHz 时间步、惯量正则化和只隔离四个远端指节均不能消除失败；详细证据见阶段报告和 `results/diagnostic_*.json`。
