# 新实验室电脑迁移、验收与日常使用

这份文档记录 2026-09-18 从旧实验室电脑迁移到新电脑的实际结果。新电脑是后续唯一的实验主机；旧电脑只用于本次一次性传输，迁移完成后不再依赖。

## 1. 新电脑身份和访问方式

```text
主机名：chengyu-Z790-AORUS-ELITE-AX
系统：Ubuntu 24.04
用户：chengyu
Tailscale 地址：100.116.242.82
GPU：NVIDIA GeForce RTX 4080 SUPER，16 GB 显存
内存：31 GiB RAM，8 GiB swap
```

Windows 端 SSH：

```powershell
ssh chengyu@100.116.242.82
```

SSH 已启用并设置为开机启动，密钥登录已验证。NoMachine 服务监听 TCP 4000，并由用户在 Windows 端管理图形连接。

## 2. 项目路径

```text
主 Git 仓库：~/robot-learning/rm-ik-rl
OpenPI：~/robot-learning/openpi
IsaacLab：~/robot-learning/IsaacLab
Isaac Sim 5.1.0：~/isaac-sim-5.1.0
ROS 2 Jazzy 工作区：~/robot-learning/rm65_project_jazzy_ws
RM65 + 4C2 仿真资产：~/robot-learning/004-rm65-4c2-isaaclab
π0.5 权重：~/.cache/openpi
Hugging Face 缓存：~/.cache/huggingface
迁移证据与机器日志：~/migration_logs
```

打开新终端后可以使用：

```bash
use_rm65   # 加载 ROS 2 Jazzy 和 RM65 工作区，并进入主仓库
use_openpi # 进入 OpenPI 仓库
rm65-status
```

这些命令定义在 `~/.bash_aliases`。

## 3. 哪些内容被复制，哪些内容被重建

从旧电脑逐文件复制并校验：

- `~/robot-learning`，包括主仓库、OpenPI、IsaacLab、RM65/4C2 源模型、生成的 URDF/USD 和实验结果；
- `~/.cache/openpi`，约 35 GB，包含 π0.5 checkpoint 与资产；
- `~/.cache/huggingface`，约 2 GB；
- `~/isaac-sim-5.1.0`，约 19 GB；
- `openpi_server:latest` 与 `libero:latest` 两个 Docker 镜像，迁移后比较完整镜像 ID；
- 旧电脑系统、Git、Docker 和项目路径的只读清单。

以下部分在 Ubuntu 24.04 上重新安装或重新生成：

- NVIDIA 580 驱动、Docker Engine、NVIDIA Container Toolkit；
- ROS 2 Jazzy、MoveIt 2、ros2_control、RealSense 包；
- `rm65_project_jazzy_ws`，使用官方 RM Jazzy 分支重新干净编译；
- OpenPI `.venv`，使用仓库的 `uv.lock` 重建，避免旧用户名的绝对路径失效；
- Omniverse 缓存。旧 Ubuntu 22.04 的二进制缓存会让 Isaac Sim 5.1.0 在 `omni.platforminfo` 中崩溃，因此旧缓存只保留为备份，不再加载。

没有复制旧电脑的 `/usr`、驱动或整个根文件系统，避免把 Ubuntu 22.04 的系统库带入 Ubuntu 24.04。

## 4. 已执行的验收

### ROS 2

- ROS 2 Jazzy 发布/订阅测试通过；
- canonical 工作区干净构建，25/25 包通过；
- RM65 Xacro、launch 文件和包发现通过；
- MoveIt 2 API 已从旧字段 `trajectory_` 适配到 Jazzy 的 `trajectory`。

### Isaac Sim / IsaacLab

- RTX 4080 SUPER 上执行 10 个 CUDA 物理步通过；
- RM65 + 4C2 组合 articulation：12 DOF，运动和回零阈值通过；
- 4C2 开合几何：两组指尖距离随闭合命令单调减小；
- Lula 全位姿 IK：位置误差约 `1e-6 m`，旋转误差约 `9.18e-4 rad`；
- 4C2 闭合接触：左右指尖都检测到接触，所有状态有限。

这些都是仿真验证，没有连接或命令真实 RM65。

### OpenPI / Docker

- Docker GPU 能在 `openpi_server` 容器内看到 RTX 4080 SUPER；
- `openpi_server` 与 `libero` 镜像 ID 和旧电脑一致；
- π0.5 服务从迁移后的 checkpoint 启动；
- LIBERO 示例观测推理返回有限动作张量；
- DROID joint-position 推理返回 `15×8` 有限动作，稳态约 `0.10 s`；
- Franka 场景 1 在 IsaacLab 中重新闭环评测，3/3 次严格成功，证明新电脑上的相机观测、π0.5、动作执行和物理仿真能连成完整链路；
- RM65 输入/输出 transform 在新建的 OpenPI 虚拟环境中通过。

最终机器可读总报告：

```text
projects/004-rm65-4c2-isaaclab/results/new_lab_pc_migration_audit.json
```

重新运行只读验收：

```bash
cd ~/robot-learning/rm-ik-rl
python3 scripts/validate_new_lab_pc.py
```

只有输出顶层 `status` 为 `pass`，才表示主机迁移验收完整通过。

## 5. 启动 π0.5

启动 DROID checkpoint 服务：

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
bash scripts/start_pi05_droid_server.sh
```

查看日志：

```bash
docker logs -f libero-openpi_server-1
```

停止服务：

```bash
bash scripts/stop_pi05_server.sh
```

这一步只启动策略服务器。未经仿真闭环验证的动作仍不能发送给真机。

## 6. RM65 有线网络交接

新电脑已保存一个名为 `rm65-robot` 的 NetworkManager 配置：

```text
接口：enp4s0
本机地址：192.168.1.100/24、192.168.1.10/24、192.168.1.5/24
机器人地址：192.168.1.19
默认路由：禁用，不影响 Wi-Fi/Tailscale
```

迁移期间该配置保持未激活，网口使用临时地址 `192.168.1.200` 连接旧电脑。文件与 Docker 镜像全部完成后：

1. 拔掉新旧电脑之间的网线；
2. 把原来连接旧电脑和 RM65 的网线接到新电脑 `enp4s0`；
3. 执行 `sudo nmcli connection up rm65-robot`；
4. 先运行 `ping -c 3 192.168.1.19`；
5. 只验证可达性，不发送运动命令。

在确认接线后可以开启该配置的自动连接：

```bash
sudo nmcli connection modify rm65-robot connection.autoconnect yes
```

## 7. 当前硬件稳定性处理

迁移初期三个用户态程序的崩溃都指向同一个逻辑 CPU。已启用可逆的临时服务：

```text
disable-suspected-pcore.service
```

它在开机时暂时下线 CPU 10/11。单核压力测试和 4 GB 内存测试通过，之后 IsaacLab 也完成了多项验证。建议以后用主板 Q-Flash 人工升级最新稳定 BIOS；升级并复测后再取消这个临时措施。不要在远程会话中自动刷 BIOS。

## 8. 迁移边界

本次“迁移完成”表示新电脑能继续全部后续开发：写代码、ROS 2/MoveIt 2、Isaac Sim/IsaacLab、Docker、π0.5 推理与数据管线均恢复。它不表示 π0.5 已经在 RM65 真机上安全闭环运行。

后续仍按以下顺序推进：专家轨迹记录 → RM65 数据集 → π0.5 微调 → IsaacLab 闭环评测 → 急停/限速/工作空间保护 → 真机空载低速验证 → 带物体任务。
