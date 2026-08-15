# 今天：远程 Linux + Isaac Sim + 传统 IK

今天的完成标准按层级划分。做到 B 就已经有明确成果，做到 C 才算 RM 传统 IK 完成。

- A：从 Windows 稳定 SSH 登录实验室 Linux，拿到环境信息。
- B：运行 Isaac Sim 官方自带机械臂 IK 示例。
- C：导入 RM URDF、配置运动学求解器，并让末端到达一个目标。
- D：把自己的脚本、配置与说明提交到本地 Git。

今天先不训练强化学习。强化学习需要 Isaac Lab、环境设计和数小时训练，把它混进今天会导致每一层都难以定位错误。

## 0. 你需要知道的四个占位符

- `<USER>`：Linux 用户名，例如 `zhangsan`
- `<IP>`：实验室电脑 IP，例如 `10.10.2.35`
- `<ISAAC_ROOT>`：Isaac Sim 安装目录，例如 `/home/zhangsan/isaacsim`
- `<RM_MODEL>`：机械臂型号，优先确认是 `RM65`、`RM75` 还是其他型号

尖括号只是提示，实际输入命令时要替换，不能原样复制。

## 1. Windows 远程登录 Linux

在 Windows Terminal 或 PowerShell 中运行：

```powershell
ssh <USER>@<IP>
```

第一次连接看到主机指纹，向实验室管理员核对 IP 后输入 `yes`。随后输入 Linux 密码；密码输入时屏幕不显示字符，这是正常的。

如果实验室电脑只允许校园网访问，需要先连学校 VPN，或使用学校提供的跳板机。不要为了省事把 SSH 的 22 端口直接暴露到公网。

退出远程电脑：

```bash
exit
```

## 2. 环境体检：先运行，不安装、不升级

SSH 登录后，逐条运行并保存输出：

```bash
hostnamectl
```

```bash
nvidia-smi
```

```bash
free -h
```

```bash
df -h / /home
```

```bash
echo "$DISPLAY"
```

```bash
ls -ld ~/isaacsim ~/isaac_sim 2>/dev/null
```

如果已知 Isaac Sim 目录，进入目录后运行：

```bash
cd <ISAAC_ROOT>
./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window
```

把上述输出发回给协作者再决定下一步。此时不要随意更新显卡驱动、CUDA、ROS 或系统 Python；Isaac Sim 对版本组合敏感，盲目升级很容易破坏实验室现有环境。

## 3. 图形界面怎么远程看

优先顺序：

1. 实验室已有 NoMachine / Sunshine / RustDesk / VNC：使用现成方案。
2. 如果只有 SSH：先用 headless 命令验证脚本；GUI 配置 RM 时再请管理员提供远程桌面。
3. 不建议用普通 `ssh -X` 跑 Isaac Sim。3D 渲染延迟、OpenGL/Vulkan 和显卡转发问题会增加无关排错。

远程桌面负责“看画面和操作 GUI”，SSH 负责“运行命令、看日志、Git 操作”。二者可以同时使用。

## 4. 先跑官方 IK 基线

以下路径针对当前官方文档中的 Isaac Sim 6.0.x。若本机版本不同，先列出实际示例路径：

```bash
cd <ISAAC_ROOT>
find standalone_examples -path '*follow_target*ik*.py' -print
```

找到 Franka 或 Universal Robots 示例后，用 Isaac Sim 自带 Python 启动；不要直接使用系统 `python`：

```bash
cd <ISAAC_ROOT>
./python.sh standalone_examples/api/isaacsim.robot.manipulators/franka/follow_target_with_ik.py
```

验收：

- Isaac Sim 能启动或 headless 脚本能进入仿真循环。
- 机械臂末端跟随目标方块。
- 终端没有持续出现 IK 不收敛、关节找不到或扩展加载失败。

如果文件名不同，以 `find` 的实际输出为准，不要通过复制网络旧教程强行改包名。

## 5. 下载 RM 官方模型

`git clone` 的含义是把一个远程 Git 仓库完整复制到本机，并保留版本历史。第一次下载公开仓库使用 HTTPS 最简单，不需要 SSH key：

```bash
mkdir -p ~/robot-learning/third_party
cd ~/robot-learning/third_party
git clone https://github.com/RealManRobot/rm_models.git
```

更新已下载的仓库：

```bash
cd ~/robot-learning/third_party/rm_models
git pull --ff-only
```

先确认型号和 URDF 入口：

```bash
cd ~/robot-learning/third_party/rm_models
find RM65 RM75 -type f \( -name '*.urdf' -o -name '*.xacro' \) -print 2>/dev/null
```

## 6. 在 Isaac Sim 导入 RM

使用远程桌面打开 Isaac Sim：

1. `Window > Extensions`，确认 URDF Importer 已启用。
2. `File > Import`，选择 RM 的主 `.urdf` 文件。
3. Robot Type 选择 `Manipulator`，Base Type 选择 `Fixed`。
4. USD 输出到本项目的 `assets/rm65/`，不要写回第三方模型目录。
5. 导入后检查关节数量、关节轴、上下限、碰撞体和单位。
6. 保存 Stage，重新打开一次，确认 USD 不依赖临时路径。

如果入口是 `.xacro` 而非 `.urdf`，先用与该模型匹配的 ROS/xacro 环境展开。不要手工复制粘贴 XML 来“修好”模型。

## 7. 给 RM 配置传统 IK

最稳妥的首版使用 Isaac Sim 的 Lula Kinematics Solver：

1. 打开 `Tools > Robotics > Lula Robot Description Editor`（不同小版本菜单文字可能略有差异）。
2. 载入 RM 的 URDF。
3. 确认活动关节；固定底座；指定末端 frame。
4. 生成 `robot_descriptor.yaml`。
5. 用官方 `follow_target_with_ik.py` 作为最小参考，只替换：USD 路径、URDF 路径、descriptor 路径、机器人 prim path、末端 frame 名。
6. 目标先只控制位置，放在机械臂正前方、工作空间中部；跑通后再加入姿态。

为什么不直接把关节角瞬间写进去：IK 只给出一个关节构型，不保证中间路径安全。首版可以用于验证；后续抓取项目要增加 RMPflow、RRT 或 cuRobo 做无碰撞运动规划。

验收时至少记录：

- 目标位置与姿态
- IK 是否收敛
- 末端位置误差（米）
- 姿态误差（度）
- 求解耗时（毫秒）
- 是否越过关节限制或发生碰撞

## 8. 今天的 Git 收尾

在项目目录执行：

```bash
git status
git add README.md docs src configs
git diff --cached
git commit -m "feat: establish RM arm IK baseline"
```

如果某些目录尚不存在，从 `git add` 中删掉对应名字。提交前一定看 `git diff --cached`，确认没有密码、IP、用户名、大型 USD/纹理、日志和训练权重。

## 常见卡点的判断顺序

1. `nvidia-smi` 失败：显卡驱动/权限层，不是 IK 问题。
2. 官方 IK 示例失败：Isaac 安装/API 层，不要开始改 RM。
3. RM 导入后模型散架：URDF、关节、单位或物理配置层。
4. 模型正常但 IK 不收敛：末端 frame、descriptor、目标可达性或初始姿态层。
5. IK 收敛但运动撞障碍：这不是 IK bug，而是缺少运动规划。
