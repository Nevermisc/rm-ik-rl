# RM65-B + 4C2 + π0.5 真机部署门禁

这份文档只描述仿真通过以后如何进入真机阶段。当前没有向真实机械臂发送 π0.5 动作。

## 已经确认的真机软件基础

新实验室电脑已经迁移并编译 RealMan ROS2 Jazzy 驱动：

```text
~/robot-learning/third_party/ros2_rm_robot_jazzy
~/robot-learning/rm_moveit2_jazzy_ws/install/rm_driver
```

驱动 C++ 源码的通用默认机械臂地址是 `192.168.1.18`，但当前 RM65 Jazzy 配置文件 `rm_driver/config/rm_65_config.yaml` 明确覆盖为 `192.168.1.19`；电脑 UDP 地址配置为 `192.168.1.10`。实际连接时必须再与机械臂示教器显示的地址核对，不能只采用源码默认值。新电脑的有线接口 `enp4s0` 当前处于 UP，但还没有 IPv4 地址；在实际连接机械臂网线后，需要给这个接口配置与机械臂同网段且不冲突的静态地址。

关节实时跟随话题是：

```text
/rm_driver/movej_canfd_cmd
rm_ros_interfaces/msg/Jointpos
```

字段是六个关节弧度、follow、expand 和 dof。官方驱动源码会把收到的弧度转换为控制器使用的角度，因此 π0.5 的六轴输出单位与 ROS2 消息一致，但仍必须经过关节限位、单步限幅和频率门禁。

驱动还提供：

```text
/rm_driver/move_stop_cmd
/rm_driver/emergency_stop_cmd
/rm_driver/set_gripper_position_cmd
```

其中 `Gripperset.position` 的驱动定义是 1～1000，对应开口 0～70 mm。这个接口能否直接控制当前实物 4C2，尚未由模型文件证明。

## 先做只读审计与反馈验证

项目提供了两项不会发布控制命令的检查。第一项不启动 ROS2 驱动，只检查电脑当前准备情况：

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
python3 scripts/audit_real_robot_readiness.py \
  --output results/rm65_real_robot_readiness.json
```

没有接线、标定时它会以退出码 `2` 和 `status=blocked` 结束，这是安全门正常工作。报告同时固定写入 `read_only=true` 与 `real_robot_command_sent=false`。

机械臂网线、电脑静态地址、控制器地址和急停都由现场人员确认后，才能在一个终端启动驱动：

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot-learning/rm_moveit2_jazzy_ws/install/setup.bash
ros2 launch rm_driver rm_65_driver.launch.py
```

另开终端运行只读反馈探针：

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot-learning/rm_moveit2_jazzy_ws/install/setup.bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
python3 scripts/probe_rm65_joint_feedback.py \
  --timeout-seconds 10 \
  --minimum-samples 20 \
  --minimum-rate-hz 20 \
  --output results/rm65_joint_feedback_probe.json
```

探针只订阅 `/joint_states`，不会创建任何发布器。它检查关节名称严格为 `joint1` 到 `joint6`、位置为弧度有限值、没有超出 RM65 关节范围、到达时间单调且反馈频率至少 20 Hz。通过这一步仍然不等于允许运动，只满足真机门禁中的“只读反馈已验证”。

## 模型文件不能回答的内容

用户提供的 4C2 包包含 URDF、STL 网格、关节范围和惯性参数。它说明仿真几何中主关节范围是 `0～0.865 rad`，不能说明实物通过什么总线、寄存器或 ROS2 话题控制，也不能证明 1～1000 与实际开口宽度之间是线性关系。

进入真机夹取前必须实际确认：

1. 4C2 是否接在 RM65 控制器的原生夹爪口；
2. 若不是，夹爪控制器型号、通信方式、波特率或 IP/端口；
3. 张开和闭合命令方向；
4. 最小、最大安全命令与实际开口宽度；
5. 是否有位置、力或电流反馈；
6. 方块所需的低速夹持力。

这些数据要通过厂家说明或低速、空载、人工监护的标定得到，不能由 URDF 猜测。

## 相机现状

ROS2 Jazzy 已安装 `realsense2_camera`，旧电脑曾经识别并显示 D435i。当前新电脑的 USB 列表中没有 D435i，所以还不能做真实视觉闭环。旧记录中的 `Link6 → camera_link` 变换只是临时值 `(0.05, 0, 0.08)`，不是手眼标定结果。

真实数据和真实执行至少需要：

- D435i 连接 USB 3.x 并稳定输出 RGB；
- 明确外部相机和腕部相机各自来源；若只有一台 D435i，需要决定第二视角；
- 标定相机内参；
- 标定相机相对 `base_link` 或夹爪 TCP 的外参；
- 将真实图像裁剪/缩放为训练接口的 `224×224×3`，并检查颜色顺序为 RGB。

## 三层执行门

### 第一层：策略文件门

`build_rm65_policy_artifact.py` 把训练报告、checkpoint 目录哈希和归一化统计哈希写入同一份 manifest。缺少任一项，仿真执行门返回 `blocked`。

### 第二层：IsaacLab 闭环门

必须完成至少 20 条 π0.5 仿真闭环 episode，成功率不低于 80%。每条报告必须明确：

```text
pi05_used=true
simulation_only=true
real_robot_command_sent=false
expert=null
```

脚本专家 45/45 成功只证明数据生成器可靠，不能代替这一层。

### 第三层：真机门

以下证据必须全部为真：

- 实体急停按钮由现场人员测试；
- 软件停止话题测试；
- 低速度、低加速度限制已配置；
- 机械臂周围工作区清空；
- 关节顺序和当前反馈与仿真一致；
- 夹爪开合方向和范围已标定；
- 相机图像与状态时间同步；
- 人员在机械臂旁监护；
- 先做空载小步关节测试，再做无物体视觉闭环，最后才夹取物体。

## 真机控制器应采用的结构

```text
ROS2 相机 + 关节反馈 + 夹爪反馈
  → 观测时间戳与完整性检查
  → π0.5 WebSocket 推理
  → 关节限位 / 初次真机单步 0.01 rad 上限 / 夹爪限幅
  → 更严格的真机速度、加速度和工作空间检查
  → 把 20 Hz 策略目标线性插值为 50 Hz 驱动目标
  → 50 Hz 关节跟随命令，并在每次发送前核对最新反馈
  → watchdog：超时、丢帧、反馈异常立即 move_stop
```

`openpi_extension/real_robot_adapter.py` 中的 `interpolate_arm_targets()` 只处理已经通过限位的六轴目标，不会创建 ROS 发布器。以 10 个策略点为例，测试会把 0.5 秒轨迹转换为 25 个驱动点，并验证终点不变；对于策略层每步 `0.01 rad` 的测试轨迹，50 Hz 相邻点最大约为 `0.004 rad`。可运行 `python3 scripts/test_real_robot_adapter.py` 复查这项纯数学证据。真正的 ROS 桥仍必须加入新鲜反馈检查和 watchdog，不能因为插值测试通过就解锁真机。

### 只读策略影子模式

机械臂反馈、两个相机和 RM65 专用策略服务都可用以后，先运行 `scripts/run_rm65_policy_shadow.py`。这个节点只订阅 `/joint_states` 和两个用户指定的 RGB topic；源代码不导入 RealMan 控制消息，也没有 ROS 发布器。它检查三路时间戳、关节顺序和图像格式，运行 π0.5，再把建议动作经过真机限幅和 50 Hz 插值后写入 JSONL，但不发送这些动作。

```bash
python3 scripts/run_rm65_policy_shadow.py \
  --external-image-topic <外部相机的RGB话题> \
  --wrist-image-topic <腕部相机的RGB话题> \
  --gripper-normalized <现场确认的当前开度，0开1闭> \
  --prompt "pick up the block and place it on the target" \
  --max-samples 20 \
  --output results/rm65_policy_shadow.jsonl
```

当前 RealMan ROS2 驱动没有连续发布夹爪位置，因此参数中的夹爪状态必须由现场确认，并会被记录为 `operator_confirmed_static_value`；不能把命令返回值误当作位置反馈。连续传感器拒绝达到上限时节点自动退出。只有检查 JSONL 中 20 个新鲜同步样本均为有限值、限幅统计合理，而且确认 `real_robot_command_sent=false` 和 `ros_publishers_created=0` 后，才能把门禁字段 `policy_shadow_passed` 设为 `true`。`human_supervisor_present` 只能在每次准备实际运动时由现场人员确认。

不要手工修改这一结论。让验证器从原始 JSONL 生成机器可读证据：

```bash
python3 scripts/validate_rm65_policy_shadow.py \
  --input results/rm65_policy_shadow.jsonl \
  --output results/rm65_policy_shadow_validation.json
```

验证器要求至少 20 个连续编号的合格样本、零拒绝、动作形状为 `10×7`、图像哈希完整、时间新鲜且同步、全程零发布和零真机命令，并检查 25 点/0.5 秒的驱动插值约束。任一条件不满足就输出 `policy_shadow_passed=false`。

真机初次验证不会直接运行完整抓放。正确顺序是：

1. 只读机械臂状态和相机；
2. 策略推理但只记录建议动作；
3. 空工作区内执行单关节极小步长；
4. 六轴空载低速跟随一小段已知轨迹；
5. π0.5 空载闭环，夹爪保持张开；
6. 单独标定夹爪；
7. 低速抓取软质或轻质测试物；
8. 完整抓放并做多次统计。

任何阶段出现超时、非有限值、关节顺序不一致、相机中断或现场人员离开，控制器都必须停止发布并触发停止命令。
