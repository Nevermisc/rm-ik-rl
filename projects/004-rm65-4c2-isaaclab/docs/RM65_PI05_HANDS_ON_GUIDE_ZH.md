# RM65-B + 4C2 + π0.5 手把手复现与理解教程

更新时间：2026-09-24  
适用对象：有 Python 基础、第一次系统做具身智能项目的人  
当前执行边界：只做 IsaacLab/Isaac Sim 仿真，不连接或控制真实机械臂

## 1. 这份教程怎么使用

这不是一组“复制后看到机械臂动起来”的命令。你的目标是每一步都能回答：

1. 输入是什么？
2. 输出是什么？
3. 数据的 shape、单位和坐标系是什么？
4. 成功由哪份机器可读证据证明？
5. 失败时应该先检查哪一层？
6. 这一步能证明什么，不能证明什么？

建议每次只完成一个小节。你亲自在终端输入命令，把输出写进学习日志；我根据输出解释，再进入下一步。不要跳过失败结果，因为排错过程正是这个项目最有价值的能力。

所有正式操作都在新实验室电脑执行：

```text
主机：chengyu-Z790-AORUS-ELITE-AX
系统：Ubuntu 24.04
GPU：RTX 4080 SUPER 16 GB
项目仓库：~/robot-learning/rm-ik-rl
RM65 项目：~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
OpenPI：~/robot-learning/openpi
IsaacLab：~/robot-learning/IsaacLab
Isaac Sim：~/isaac-sim-5.1.0
```

密码、令牌和 SSH 私钥不得写入代码、文档或 Git。

## 2. 先看清整个系统

```text
文字指令 + 外部相机 + 腕部相机 + 6 轴状态 + 夹爪状态
                         │
                         ▼
                  RM65Inputs transform
                         │
                         ▼
              π0.5 预测未来 10×7 动作块
                         │
                         ▼
                  RM65Outputs transform
                         │
                         ▼
        有限值检查、关节限位、最大步长、夹爪范围
                         │
                         ▼
          IsaacLab 只执行前 5 步，再重新观察和推理
                         │
                         ▼
       物体抬升、搬运、落点、释放、稳定性任务报告
```

### 2.1 核心概念

| 名称 | 本项目中的作用 | 常用场景 |
|---|---|---|
| π0.5 | 视觉-语言-动作策略，相当于控制“大脑” | 根据图像、状态和文字预测机器人动作 |
| Isaac Sim | USD、渲染、PhysX 物理和传感器运行时 | 搭场景、碰撞、相机、物理仿真 |
| IsaacLab | Isaac Sim 上的机器人学习框架 | 环境、批量实验、控制与评测 |
| URDF | link、joint、惯量、碰撞与网格结构说明 | ROS、运动学、机器人资产交换 |
| USD | Isaac 使用的场景与资产格式 | 保存仿真材质、物理属性和场景层 |
| Lula IK | 从末端位姿求六轴关节角 | 脚本专家、可达性和轨迹生成 |
| LeRobot | 机器人轨迹数据格式 | 组织视频、状态、动作和 episode |
| LoRA | 只训练少量适配参数 | 显存有限时微调大模型 |
| WebSocket | 仿真进程与模型进程通信 | GPU 模型服务、跨环境推理 |
| receding horizon | 每次预测一段，只执行前几步再重规划 | 用新观测修正累积误差 |
| Docker | 隔离依赖和运行环境 | 官方 LIBERO/OpenPI 示例和可复现环境 |

### 2.2 三种成功必须分开

| 类型 | 控制者 | 当前结果 | 能否证明 π0.5 已部署成功 |
|---|---|---:|---|
| 脚本专家仿真 | IK + 状态机 | 45/45 数据 episode 成功 | 不能 |
| π0.5 RM65 仿真闭环 v1 | 微调模型 | 12/20，60% | 证明部分成功，未过门禁 |
| π0.5 RM65 仿真闭环 v2 | policy-window 微调模型 | 11/20，55% | 未优于 v1，未过门禁 |
| 真机闭环 | π0.5 + 真机安全层 | 未执行 | 尚无结果 |

## 3. 第 0 课：确认你在正确电脑、正确仓库

### 目标

学会在运行任何实验前检查主机、路径、Git、GPU、内存和磁盘。这个习惯能避免在错误电脑、错误分支或错误环境中运行数小时。

### 你亲手执行

```bash
hostname
cat /etc/os-release | head
nvidia-smi
free -h
df -h ~

cd ~/robot-learning/rm-ik-rl
git branch --show-current
git rev-parse --short HEAD
git status --short
```

### 当前预期

```text
hostname：chengyu-Z790-AORUS-ELITE-AX
系统：Ubuntu 24.04
GPU：RTX 4080 SUPER
分支：main
当前已验证提交：86a1446 或其后续提交
```

`git status --short` 可能显示历史遗留的未跟踪文件。不要使用 `git add .`，只添加自己确认过的文件。

### 常见问题

- `nvidia-smi` 不存在：驱动未安装或 PATH 错误。
- 显存被占满：先用 `nvidia-smi` 看 PID，不要盲目重启。
- Git 出现大量意外修改：停止实验，先确认是不是进入了错误仓库。
- SSH 可达但 NoMachine 不可用：SSH 是命令行链路，NoMachine 是图形桌面链路，它们相互独立。

### 常用场景

训练、仿真、服务器部署、远程排障之前都应执行这组 preflight。

## 3.5 第 0.5 课：从一台全新 Ubuntu 电脑重建环境

这一节回答“如果没有现在已经配置好的实验室电脑，怎样从零走到可以运行 Franka”。当前新电脑已经完成这些安装，学习时先理解和验收，不要为了练习而重装已通过验证的驱动和系统软件。真正换电脑或环境损坏时，再按本节执行。

### 3.5.1 先冻结项目版本

本项目验证过的组合是：

| 组件 | 当前新电脑上的版本或提交 |
|---|---|
| Ubuntu | 24.04 |
| GPU | RTX 4080 SUPER 16 GB |
| NVIDIA 驱动 | 580.173.02 |
| Docker / Compose | 29.8.1 / v5.5.1 |
| Isaac Sim | 5.1.0 二进制版 |
| IsaacLab | v2.3.2，提交 `37ddf62` |
| OpenPI | 提交 `15a9616`，另有本机实验文件 |
| sim-evals | 提交 `3a6b0e8` |
| 本项目仓库 | `https://github.com/Nevermisc/rm-ik-rl.git` |

版本表的意义是建立“可复现实验环境”。不要把“最新版”自动理解为“最兼容版”。升级其中任何一项后，都应从空场景、相机、Franka 基线开始重新验收。

OpenPI 在该提交的上游 README 中写明主要测试平台是 Ubuntu 22.04。本项目已经在新电脑的 Ubuntu 24.04 上完成迁移验收，这是本项目自己的验证结果，不代表上游对所有 Ubuntu 24.04 组合提供兼容保证。因此重建时要保留版本和日志，不能只记录“Ubuntu + CUDA”。

### 3.5.2 安装基础工具和 SSH

```bash
sudo apt update
sudo apt install -y git git-lfs curl ca-certificates gnupg \
  build-essential cmake unzip ffmpeg openssh-server
sudo systemctl enable --now ssh

mkdir -p ~/robot-learning
```

验收：

```bash
git --version
ssh -V
systemctl is-active ssh
```

常见问题：`apt update` 如果出现 `Segmentation fault`，先不要继续安装。检查 `dmesg`、内存和磁盘，并重新运行 `sudo apt clean && sudo apt update`；软件索引没有正常生成时，后续会出现“Unable to locate package”。

### 3.5.3 安装并验证 NVIDIA 驱动

优先让 Ubuntu 为当前 GPU 选择推荐驱动，不复制旧电脑的 `/usr`、CUDA 或驱动文件：

```bash
sudo apt install -y ubuntu-drivers-common
ubuntu-drivers devices
sudo ubuntu-drivers install
sudo reboot
```

重启后：

```bash
nvidia-smi
```

通过条件：能看到正确 GPU、驱动版本、显存总量，并且没有 `NVIDIA-SMI has failed`。`nvidia-smi` 右上角的 CUDA 版本是驱动支持上限，不等于你的 Python 环境安装了同版本 CUDA。

### 3.5.4 安装 Docker Engine

下面是 Docker 官方 apt 仓库方式。不要使用 snap 版 Docker；它曾与 NVIDIA 容器运行时产生兼容问题。

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

退出 Linux 会话并重新登录，让 `docker` 用户组生效，然后验收：

```bash
docker version
docker compose version
docker run --rm hello-world
```

### 3.5.5 让 Docker 能使用 GPU

按 NVIDIA Container Toolkit 官方仓库安装：

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

验收：

```bash
docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubuntu22.04 nvidia-smi
```

宿主机 `nvidia-smi` 成功但容器失败时，优先检查 Container Toolkit 和 Docker runtime，不要重装 OpenPI。

### 3.5.6 克隆并固定四个仓库

```bash
cd ~/robot-learning

git clone https://github.com/Nevermisc/rm-ik-rl.git

git clone --recurse-submodules https://github.com/Physical-Intelligence/openpi.git
cd openpi
git checkout 15a9616
git submodule update --init --recursive

cd ~/robot-learning
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
git checkout v2.3.2

cd ~/robot-learning
git clone --recurse-submodules https://github.com/arhanjain/sim-evals.git
cd sim-evals
git checkout 3a6b0e8
```

如果 GitHub 主仓库尚未包含某些大文件，必须从经过哈希校验的备份恢复：Isaac Sim 二进制、`~/.cache/openpi` checkpoint、sim-evals assets、RM65/4C2 网格和本项目训练 checkpoint 都不应假设在 Git 中。

### 3.5.7 安装 OpenPI 主机环境并构建模型服务镜像

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

cd ~/robot-learning/openpi
GIT_LFS_SKIP_SMUDGE=1 uv sync
GIT_LFS_SKIP_SMUDGE=1 uv pip install -e .

docker compose -f examples/libero/compose.yml build openpi_server
```

Franka 复现只需要 `openpi_server` 镜像。官方 LIBERO 环境还需要构建 `runtime` 镜像：

```bash
docker compose -f examples/libero/compose.yml build runtime
```

本项目历史上构建 LIBERO runtime 时遇到旧依赖不能配合新版 setuptools 的问题，在 `examples/libero/Dockerfile` 中加入了 `setuptools<75` 的构建约束。这个修改只影响 LIBERO 镜像的依赖构建，不改变 π0.5 权重。遇到同类错误时先保存完整 build log，再核对仓库当前 Dockerfile；不要盲目降级宿主系统 Python。

### 3.5.8 安装 Isaac Sim 5.1.0 和 IsaacLab v2.3.2

从 NVIDIA 官方下载 Isaac Sim 5.1.0 Linux 二进制压缩包。假设下载文件位于 `~/Downloads`，解压到固定目录：

```bash
mkdir -p ~/isaac-sim-5.1.0
unzip ~/Downloads/isaac-sim-standalone-5.1.0-linux-x86_64.zip \
  -d ~/isaac-sim-5.1.0

cd ~/robot-learning/IsaacLab
ln -s ~/isaac-sim-5.1.0 _isaac_sim
./isaaclab.sh --install none
```

压缩包真实文件名可能带 build 编号，以下载页面为准；目录名保持本项目约定即可。若 `_isaac_sim` 已存在，先用 `readlink -f _isaac_sim` 检查，不要直接覆盖。

空场景验收：

```bash
cd ~/robot-learning/IsaacLab
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --headless
```

首次启动如果受到旧 Omniverse 缓存影响，应先把旧缓存移到备份目录再验证；不要把 Ubuntu 22.04 的二进制缓存原样复制到 Ubuntu 24.04。

### 3.5.9 安装 Franka 客户端依赖和场景资产

Franka runner 使用 Isaac Sim 自带的 Python，因此 `openpi-client` 必须安装到这个 Python 中：

```bash
cd ~/robot-learning/IsaacLab
./isaaclab.sh -p -m pip install -e \
  ~/robot-learning/openpi/packages/openpi-client
./isaaclab.sh -p -m pip install imageio-ffmpeg
```

验证导入路径不能指向已经不存在的旧用户名：

```bash
./isaaclab.sh -p -c \
  'import openpi_client; print(openpi_client.__file__)'
```

下载 sim-evals 的三套 DROID 场景：

```bash
cd ~/robot-learning/sim-evals
uvx hf download owhan/DROID-sim-environments \
  --repo-type dataset --local-dir assets
```

最后记录目录和提交：

```bash
git -C ~/robot-learning/openpi rev-parse --short HEAD
git -C ~/robot-learning/IsaacLab describe --tags --always
git -C ~/robot-learning/sim-evals rev-parse --short HEAD
find ~/robot-learning/sim-evals/assets -maxdepth 1 -type f | sort
```

### 3.5.10 环境层的验收顺序

严格按下面顺序排错：

```text
宿主机 nvidia-smi
→ Docker hello-world
→ Docker 内 nvidia-smi
→ Isaac Sim 空场景
→ IsaacLab Python 导入 openpi_client
→ DROID 场景和双相机
→ π0.5 服务与预热
→ Franka 单回合
→ Franka 完整评测
```

前一层失败时不要跳到后一层。这样可以把驱动、容器、仿真、场景、模型和策略接口问题分开。

## 4. 第 1 课：先验证官方链路，再迁移机器人

### 目标

把“模型与 CUDA 问题”和“RM65 资产问题”分开。若官方 Franka 场景也失败，先查 OpenPI、checkpoint、CUDA、相机和 WebSocket；若 Franka 成功而 RM65 失败，再查 RM65 关节与动作语义。

### 我们实际完成了什么

- LIBERO 示例观测能让 π0.5 返回有限动作张量。
- 第一次 JAX 编译曾超过 WebSocket keepalive 时间，出现 `ping timeout`；关闭本地 keepalive 并预热后，稳态推理约 0.32 秒。
- Franka 参考项目的严格基线为 9/9；鲁棒性矩阵为 17/18，总计 26/27。
- 这证明新电脑可以同时运行 π0.5 服务、双相机观测和 IsaacLab 闭环，但不证明 Franka checkpoint 可以控制 RM65。

### 4.1 先区分 LIBERO、DROID 和 Isaac

`LIBERO` 是一套机器人操作 benchmark 和任务数据，不是 Isaac Sim。官方 `pi05_libero` checkpoint 可以在 LIBERO/MuJoCo 环境中验证 OpenPI 的官方完整示例；本项目后来使用的 Franka 参考链路则是：

```text
DROID 风格的 Franka 数据接口
        +
pi05_droid_jointpos_polaris checkpoint
        +
sim-evals 在 Isaac Sim 中搭建的 DROID 场景
```

因此，“LIBERO 推理成功”只证明 OpenPI 模型服务能工作；“Franka + IsaacLab 闭环成功”才证明 OpenPI、双相机、关节状态、动作接口和 Isaac 物理形成了闭环。

### 4.2 阅读 Franka 项目，不急着运行

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
less README.md
less docs/FRANKA_STAGE_REPORT_ZH.md
```

先回答这些问题：

- 输入为什么是外部相机、腕部相机、7 个 Franka 关节和夹爪状态？
- 输出 `15×8` 的 15 和 8 分别代表什么？
- 为什么只执行前 8 步就重新观察？
- 为什么 DROID joint-position checkpoint 不能直接控制 RM65？

### 4.2.1 我们实际下载了什么，分别放在哪里

先把“代码”“场景资产”“模型权重”“运行环境”“实验结果”分开。它们不能全塞进一个 Git 仓库：模型和 USD 资产很大，运行结果会不断生成，而自己写的代码和小型证据适合由 Git 管理。

| 内容 | 来源 | 新电脑实际位置 | 当前规模或版本 | 为什么放这里 |
|---|---|---|---|---|
| 主项目代码 | `Nevermisc/rm-ik-rl` | `~/robot-learning/rm-ik-rl` | HEAD 至少为本教程提交 | 保存我们写的 runner、文档和小型 JSON 证据 |
| OpenPI | Physical Intelligence 官方仓库 | `~/robot-learning/openpi` | `15a9616` | 模型定义、策略服务、WebSocket client 和 checkpoint 下载器 |
| IsaacLab | NVIDIA 官方仓库 | `~/robot-learning/IsaacLab` | v2.3.2 / `37ddf62` | 运行环境、传感器、action manager 和 Isaac Python 入口 |
| Isaac Sim | NVIDIA 5.1.0 二进制包 | `~/isaac-sim-5.1.0` | 约 19 GB | 物理、RTX 渲染和 USD 运行时，不适合放 Git |
| sim-evals | `arhanjain/sim-evals` | `~/robot-learning/sim-evals` | `3a6b0e8` | 提供 DROID 风格 Franka 环境和三个场景 |
| DROID 场景资产 | Hugging Face `owhan/DROID-sim-environments` | `~/robot-learning/sim-evals/assets` | 约 88 MB | sim-evals 用相对路径读取，放仓库根目录的 `assets` 最直接 |
| π0.5 DROID joint-position 权重 | `gs://openpi-assets/checkpoints/pi05_droid_jointpos` | `~/.cache/openpi/openpi-assets/checkpoints/pi05_droid_jointpos` | 磁盘约 12 GB | OpenPI 下载器的标准缓存，可跨容器复用 |
| PaliGemma tokenizer | OpenPI 自动下载 | `~/.cache/openpi/big_vision` | tokenizer model 约 4.3 MB | π0.5 文字指令分词所需 |
| OpenPI 服务镜像 | 本机从 OpenPI Dockerfile 构建 | Docker image `openpi_server:latest` | image ID 前缀 `c9036656`，约 19.36 GB | 隔离 JAX/CUDA/模型依赖 |
| LIBERO runtime 镜像 | 本机从 LIBERO Dockerfile 构建 | Docker image `libero:latest` | image ID 前缀 `25beb997`，约 21.05 GB | 只在 LIBERO benchmark 使用，Franka Isaac 闭环不依赖它 |
| Franka 完整运行结果 | runner 自动生成 | `~/robot-learning/sim-evals/runs/pi05_franka_suite` | 视频、PNG、NPZ、JSON | 大文件且会重复生成，由 `.gitignore` 排除 |
| Franka 摘要证据 | 从正式运行提炼 | `projects/003-pi05-franka-isaaclab/results` | 小型 JSON | 可以提交 Git，便于审阅结论而不搬运全部视频 |

实际历史要分两段讲清楚：第一次在旧实验室电脑建立环境时，OpenPI、IsaacLab、sim-evals、DROID assets 和官方 checkpoint 分别从上游仓库、Hugging Face 与 OpenPI 资产服务器取得；换成当前 Ubuntu 24.04 新电脑时，没有把几十 GB 内容全部重新下载，而是复制 `~/robot-learning`、`~/.cache/openpi`、Isaac Sim 二进制和两个 Docker image，并用文件清单、镜像 ID 和分层测试验收。驱动、Docker、NVIDIA Container Toolkit 和 Python 虚拟环境则在新系统重装。教程里的下载命令描述“干净重建”，迁移文档描述“本项目实际上怎样搬到新电脑”，两者都是真实路线，但发生时间不同。

场景资产目录中的关键文件是：

```text
assets/
├── franka_robotiq_2f_85_flattened.usd   # Franka + Robotiq 机器人 USD
├── scene1.usd                            # 魔方与红碗
├── scene2.usd                            # 肉罐头与红杯
├── scene3.usd                            # 香蕉与紫色收纳盒
├── table.usd                             # 桌面
└── backgrounds/
    ├── billiard_hall_4k.hdr
    ├── brown_photostudio_01_4k.hdr
    └── empty_warehouse_01_4k.hdr
```

这批资产使用以下命令下载到 sim-evals 期望的位置：

```bash
cd ~/robot-learning/sim-evals
uvx hf download owhan/DROID-sim-environments \
  --repo-type dataset \
  --local-dir assets
```

π0.5 权重不需要手工复制到 OpenPI 源码目录。服务收到：

```text
--policy.dir=gs://openpi-assets/checkpoints/pi05_droid_jointpos
```

以后，OpenPI 下载器会检查 `~/.cache/openpi`；没有就下载，有就复用。Docker Compose 把宿主机路径映射成容器内路径：

```text
宿主机 ~/robot-learning/openpi  → 容器 /app
宿主机 ~/.cache/openpi          → 容器 /openpi_assets
```

因此模型日志中会显示从 `/openpi_assets/...` 加载，而你在宿主机上看到的是 `~/.cache/openpi/...`。两者是同一份文件的两种路径，不是下载了两遍。

### 4.2.2 为什么目录要这样分层

```text
~/robot-learning/
├── rm-ik-rl/              我们自己的代码、教程、配置、小型证据
├── openpi/                上游模型仓库，尽量少改
├── IsaacLab/              上游仿真框架，尽量少改
└── sim-evals/             上游 Franka/DROID 环境和本地大运行结果

~/isaac-sim-5.1.0/         NVIDIA 二进制运行时
~/.cache/openpi/           可重新下载但很大的模型权重和 tokenizer
```

这种结构解决三个问题：

1. **上游更新和自己的代码分离。** 可以明确说出修改发生在自己的项目，还是第三方仓库。
2. **Git 不保存大文件。** checkpoint、视频、USD 和 Docker layer 不会把仓库撑到几十 GB。
3. **迁移时有优先级。** 代码可从 Git 恢复；权重可从缓存或网络恢复；自己训练的 checkpoint 和机器人资产必须额外备份。

### 4.2.3 哪些文件是我们自己写的

Franka 项目在 Git 提交 `54b9785` 中首次完整加入。项目目录如下：

```text
projects/003-pi05-franka-isaaclab/
├── README.md
├── .gitignore
├── .gitattributes
├── config/
│   └── openpi-gpu-memory.override.yml
├── docs/
│   └── FRANKA_STAGE_REPORT_ZH.md
├── results/
│   └── pi05_franka_summary_20260914.json
└── scripts/
    ├── probe_droid_scenes.py
    ├── validate_droid_sim_scene.py
    ├── warmup_pi05_droid.py
    ├── start_and_warmup_pi05.sh
    ├── stop_pi05_server.sh
    ├── run_pi05_droid_scene1.py
    ├── run_pi05_franka_robustness_suite.py
    ├── run_all_suites.sh
    ├── summarize_pi05_franka_suite.py
    └── summarize_pi05_franka_audit.py
```

逐文件说明：

| 文件 | 输入 | 输出 | 解决的问题 |
|---|---|---|---|
| `README.md` | 无 | 项目入口说明 | 让别人知道目标、依赖、结果和快速入口 |
| `.gitignore` | Git 工作树 | 忽略规则 | 排除 `runs/`、视频、NPZ、USD、checkpoint 和缓存 |
| `.gitattributes` | 文本文件 | LF 规则 | 防止 Windows/Ubuntu 换行差异破坏 Shell 脚本 |
| `openpi-gpu-memory.override.yml` | Compose 服务配置 | 两个 JAX 环境变量 | 让 π0.5 和 Isaac Sim 共用一张 16 GB GPU |
| `probe_droid_scenes.py` | 三个 scene USD | `/tmp/droid_scene_prims.json` | 在启动复杂策略前，先确认 prim、位置和刚体是否存在 |
| `validate_droid_sim_scene.py` | scene 1 | 两张 PNG 和 shape 日志 | 检查环境注册、相机、7 轴状态、夹爪状态 |
| `warmup_pi05_droid.py` | 官方假 DROID 观测 | 动作 shape、耗时、PASS | 触发 JAX 编译并检查 `(15,8)` 和有限值 |
| `start_and_warmup_pi05.sh` | OpenPI、Compose、checkpoint | 8000 端口策略服务 | 把启动、等待、报错日志和预热变成一次可复现操作 |
| `stop_pi05_server.sh` | 容器名 | 停止后的容器 | 可靠释放显存，不删除 checkpoint |
| `run_pi05_droid_scene1.py` | scene 1 + π0.5 | 3 回合视频/轨迹/JSON | 最早的最小闭环，用来证明端到端链路能跑 |
| `run_pi05_franka_robustness_suite.py` | 场景、suite、策略服务 | 严格多场景证据 | 修复宽松成功判定，增加扰动和工程审计 |
| `run_all_suites.sh` | 正式 runner | 30 回合 | 固定执行顺序，避免手工漏场景或漏 suite |
| `summarize_pi05_franka_suite.py` | 2026-09-14 固定运行目录 | 汇总 JSON | 提炼 9/9、17/18 和失败案例 |
| `summarize_pi05_franka_audit.py` | 三个 audit 目录 | 安全/性能 JSON | 汇总 NaN、限位、跳变和推理延迟 |
| `FRANKA_STAGE_REPORT_ZH.md` | 代码与实验结果 | 人类可读报告 | 解释路线、结果、限制和排错经验 |
| `pi05_franka_summary_20260914.json` | 完整运行证据 | 小型机器可读摘要 | 让 Git 中保留可核对结论 |

`sim-evals` 根目录目前还有三份未跟踪的早期副本：

```text
run_pi05_droid_scene1.py
run_pi05_franka_robustness_suite.py
validate_droid_sim_scene.py
```

正式版本是主仓库 `projects/003-pi05-franka-isaaclab/scripts/` 中的文件。运行命令使用绝对路径指向正式版本，避免同名文件造成混淆。不要把这些未跟踪副本当作另一套实现。

### 4.2.4 实际改了哪些上游文件

Franka 正式控制逻辑没有直接改 IsaacLab 或 sim-evals 的 tracked source，而是通过：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p 我们自己的_runner.py
```

把官方环境作为库导入。这种做法的优点是上游仓库保持可比较，自己的实验逻辑有独立 Git 历史。

OpenPI 仓库存在一项与 LIBERO runtime 构建有关的修改：

```dockerfile
RUN printf 'setuptools<75\n' > /tmp/build-constraints.txt
RUN uv pip sync ... --build-constraint /tmp/build-constraints.txt
```

原因是 LIBERO 的旧 Python 依赖在新版 setuptools 下构建失败。它影响 `libero:latest` runtime 镜像的构建，不是 Franka runner 的控制算法，也没有改 π0.5 权重。

OpenPI 工作树还保留了一些早期探针和 warm-up 草稿。正式复现不要依赖这些散落文件；对应的稳定版本已经放进 `projects/003-pi05-franka-isaaclab/scripts/` 并由主仓库 Git 管理。判断“正式代码”时看主项目提交，不要根据文件修改时间猜测。

新电脑迁移提交 `20ca660` 对 Franka 项目只改了 `start_and_warmup_pi05.sh` 两处：

```text
等待次数：24 × 5 秒 → 60 × 5 秒
提示文字：删除“RTX 4060 Ti 约需 2～3 分钟”的硬编码
```

原因是新电脑、冷缓存和模型下载时间不同。启动器应该按“服务是否开始监听”判断，而不是假设某张显卡必然在固定时间内完成。

本次教程补全时还修复了 IsaacLab Python 中 `openpi-client` 的 editable metadata：旧记录指向 `/home/iot22/...`，虽然兼容符号链接还能工作，但不适合长期维护。重新执行：

```bash
cd ~/robot-learning/IsaacLab
./isaaclab.sh -p -m pip install --no-deps -e \
  /home/chengyu/robot-learning/openpi/packages/openpi-client
```

现在 import 来自 `/home/chengyu/robot-learning/openpi/...`。这是 Python 环境登记修复，不是策略算法修改。

### 4.2.5 服务启动代码到底做了什么

`start_and_warmup_pi05.sh` 开头使用：

```bash
set -euo pipefail
```

含义是：命令失败就停止、使用未定义变量就报错、管道中任一命令失败都算失败。自动化脚本如果忽略错误，可能在模型服务没启动时继续跑数小时仿真。

它把三个路径做成变量：

```text
SCRIPT_DIR     当前脚本所在目录
PROJECT_DIR    Franka 项目根目录
OPENPI_DIR     默认 ~/robot-learning/openpi，可由环境变量覆盖
CONTAINER_NAME 默认 libero-openpi_server-1
```

随后设置策略参数：

```text
policy.config = pi05_droid_jointpos_polaris
policy.dir    = gs://openpi-assets/checkpoints/pi05_droid_jointpos
```

为什么选 `jointpos`：sim-evals 的 action manager 期望“7 个 Franka 目标关节角 + 1 个夹爪值”。若使用 joint velocity checkpoint，即使都是 8 个数，物理含义也不同。

Compose override 设置：

```yaml
XLA_PYTHON_CLIENT_MEM_FRACTION=0.50
XLA_FLAGS=--xla_gpu_enable_command_buffer=
```

第一个变量限制 JAX 预占约一半显存，为 Isaac Sim 留空间；第二个变量避免首次推理为了 GPU command buffer 再申请一大块显存。这里解决的是同 GPU 双进程资源竞争。

启动后脚本每 5 秒读取一次容器日志，最多检查 60 次。只有看到：

```text
server listening
```

才执行预热；否则打印最后 100 行日志并失败退出。

### 4.2.6 为什么要单独写预热程序

`warmup_pi05_droid.py` 使用官方 `make_droid_example()` 产生字段和 shape 正确的假观测，通过 `WebsocketClientPolicy` 发到 `127.0.0.1:8000`。

第一次推理同时发生：

```text
恢复 checkpoint
→ 初始化 JAX/XLA
→ 编译计算图
→ 分配 GPU buffer
→ 执行 flow-matching 推理
```

它可能超过 WebSocket 默认 20 秒心跳。程序只关闭 keepalive ping：

```python
kwargs["ping_interval"] = None
```

`infer()` 本身仍然阻塞等待真实结果，不是跳过超时后伪造成功。返回后检查：

```python
actions.ndim == 2
actions.shape[1] == 8
np.isfinite(actions).all()
```

这只能证明模型服务能产生格式正确的有限动作，不能证明它完成了抓取。

### 4.2.7 正式 runner 的数据流

正式文件是：

```text
scripts/run_pi05_franka_robustness_suite.py
```

先看一帧数据怎样流动：

```text
IsaacLab obs["policy"]
├── external_cam:  (1,180,320,3)
├── wrist_cam:     (1,180,320,3)
├── arm_joint_pos: (7,)
└── gripper_pos:   (1,)
        │
        ├── 去掉 batch 维
        ├── 两张图 resize_with_pad 到 224×224
        └── 改成 DROID checkpoint 认识的键
                │
                ▼
WebSocket request
├── observation/exterior_image_1_left: (224,224,3)
├── observation/wrist_image_left:      (224,224,3)
├── observation/joint_position:        (7,)
├── observation/gripper_position:      (1,)
└── prompt:                             str
                │
                ▼
π0.5 response["actions"]: (15,8)
                │
                ├── 取当前 action
                ├── 前 7 维保持目标关节角
                └── 第 8 维以 0.5 阈值二值化夹爪
                │
                ▼
torch.float32 action: (1,8) → env.step(action)
```

为什么图像先保持 `180×320`：这是 16:9 视场，渲染显存低于直接 224×224 多相机；送入模型时再用 padding 保持纵横比变成 `224×224`，避免直接拉伸目标形状。

为什么一次预测 15 步却只执行 8 步：完整执行 15 步推理次数少，但更容易盲目执行旧计划；每步都重新推理反馈快，但推理开销大。执行 8 步约为 `8/15 ≈ 0.53` 秒，是当时在 15 Hz 控制和约 0.32 秒稳态推理之间采用的折中。这是 receding horizon。

`DroidJointPosClient.reset()` 在每个 case 开始时清空旧 action chunk。没有这一步，新回合可能先执行上个任务剩余的动作。

### 4.2.8 为什么必须先启动 AppLauncher 再 import Isaac 模块

runner 的导入顺序看起来反常：先解析参数并创建 `AppLauncher`，再 import `gymnasium`、`torch`、`isaaclab_tasks`。这是 Isaac Sim standalone 程序的要求：Kit 应用必须先初始化，之后依赖 Omniverse extension 的模块才有完整运行时。

```python
args.enable_cameras = True
args.headless = True
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app
```

`headless=True` 表示不创建主要可视窗口，不表示不渲染相机；所以还要显式 `enable_cameras=True`。

### 4.2.9 环境创建和两次 reset 的原因

```python
cfg = parse_env_cfg("DROID", device=args.device, num_envs=1, use_fabric=True)
cfg.set_scene(args.scene)
env = gym.make("DROID", cfg=cfg)
obs, _ = env.reset()
obs, _ = env.reset()
```

- `parse_env_cfg("DROID")` 取 sim-evals 注册的 DROID 环境；
- `set_scene(1/2/3)` 选择具体 USD；
- `num_envs=1` 让真实视频和任务证据对应一个环境；
- 第二次 reset 是因为第一次渲染后材质和纹理才完整，否则早期图像可能不完整。

每个扰动 case reset 后还先执行 5 步 neutral action，再移动物体和目标，随后再执行 8 步 neutral action，让物理状态稳定。`neutral_action()` 直接返回当前关节与夹爪状态，因此不会故意移动机器人。

### 4.2.10 三类评测用例怎么生成

`Task` 保存每个场景不变的内容：源物体名称、目标名称、标准指令、同义指令和成功几何阈值。

`Case` 保存一次实验的变化：

```text
source_dx/source_dy  源物体 XY 偏移
target_dx/target_dy  目标容器 XY 偏移
brightness           只改变送给策略的图像亮度
prompt               标准或同义文字指令
```

`make_cases()` 生成：

```text
baseline_1 / 2 / 3           同一场景重复三次
source_plus                  源物体 +3.5 cm, +2 cm
source_minus                 源物体 -3.5 cm, -2 cm
target_shift                 目标 +2.5 cm, -2 cm
paraphrase                   同义英文指令
darker_input                 图像亮度 ×0.75
brighter_input               图像亮度 ×1.25
engineering_audit            标准条件下保存完整安全指标
```

亮度扰动只改送入模型的 numpy 图像，不修改 Isaac 场景灯光。这样测的是策略对视觉输入变化的敏感性，不会同时引入物理和渲染场景变化。

### 4.2.11 为什么早期“放进容器”判定不够

最早的 `run_pi05_droid_scene1.py` 主要检查方块是否连续位于碗的几何范围。它能做端到端 smoke test，但可能在夹爪仍抓着物体时提前报告成功。

正式 runner 增加五个条件：

```text
1. 源物体至少移动 0.05 m
2. XY 距离低于该目标的阈值
3. 相对高度位于合理范围
4. 实际夹爪观测值 <= 0.25，证明已经张开
5. 最近 15 步位置变化半径 <= 0.015 m，证明稳定
```

代码不是检查“命令要求张开”，而是检查 `gripper_pos` 的实际观测。因为发出 OPEN 命令不等于夹爪已经完成张开。

`entered_target_while_closed` 额外记录物体是否在夹爪闭合时进入目标。这帮助识别“拿到了目标上方，但没有释放”的失败。

### 4.2.12 为什么在 env.step 后立刻检查 terminated/truncated

IsaacLab 在 time-out 后可能自动 reset。如果先记录 reset 后的关节，再判断回合结束，就会把“上一帧任务末态 → 下一回合初态”误认为一次巨大关节跳变。

正式代码顺序是：

```python
obs, _, terminated, truncated, _ = env.step(action)
if terminated or truncated:
    break
# 只有没有自动 reset 时，才把 obs 记入当前回合轨迹
```

历史审计中曾看到约 `1.2966 rad` 的表面跳变，定位后证明是 terminal reset 样本。修正记录顺序后，最大实际单步关节变化约 `0.080 rad`。

### 4.2.13 每个 case 保存哪些证据

每个用例目录包含：

```text
policy_views.mp4             外部相机和腕部相机并排视频
final_policy_view.png        模型最后看到的组合画面
final_external_camera.png    原始外部相机末帧
final_wrist_camera.png       原始腕部相机末帧
trajectory.npz               物体、目标、关节、夹爪和推理延迟数组
summary.json                 成功结果和安全/性能指标
```

`trajectory.npz` 中记录：

```text
source_position
target_position
gripper_command
gripper_observed
arm_action
arm_observed
inference_latency_seconds
```

`summary.json` 额外计算：

```text
action_all_finite
observation_all_finite
minimum_observed_joint_limit_margin_rad
maximum_command_step_jump_rad
maximum_observed_joint_step_jump_rad
replan_count
inference_latency median / p95 / max
```

所以“成功”不是终端里的一行文字，而是可以用视频、轨迹数组和 JSON 交叉核对。

### 4.2.14 从最小版本迭代到正式版本

开发顺序可以概括为：

```text
官方 LIBERO 假观测推理
→ 确认 π0.5 服务能返回有限动作
→ 改用 DROID joint-position checkpoint
→ 下载 sim-evals DROID 场景资产
→ validate_droid_sim_scene 检查双相机和状态
→ run_pi05_droid_scene1 跑通魔方进碗
→ 发现几何成功判定可能过早
→ 正式 runner 加入实际松爪和稳定条件
→ 扩展三个场景
→ 增加位置、语言和亮度扰动
→ 增加关节限位、NaN、跳变和延迟审计
→ 修复终止自动 reset 造成的假跳变
→ 固定成 run_all_suites 和机器可读摘要
```

Git 在 `54b9785` 才一次性加入整理后的项目，因此上述中间探索并没有“一问题一提交”的完整历史。不能声称 Git 精确记录了每次尝试；问题和解决过程来自阶段报告、最终代码和运行证据。

### 4.2.15 你应该怎样读这段代码

正式 runner 的 GitHub 完整文件：

- [`run_pi05_franka_robustness_suite.py` 全文](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py)
- [`run_all_suites.sh` 全文](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_all_suites.sh)

按阅读顺序使用这些直达链接：

1. [`TASKS`：三个任务、物体名称、指令和成功几何](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L69-L97)
2. [`make_cases()`：基线、位置、语言和亮度扰动](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L146-L166)
3. [`DroidJointPosClient.infer()`：观测转换、WebSocket 与动作块](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L100-L143)
4. [`main()` 环境创建：DROID、场景、相机、reset 和关节限位](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L198-L228)
5. [内层 `for step`：调用模型、执行动作、读取新观测](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L265-L328)
6. [`inside/is_open/is_stable`：严格成功判定](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L293-L328)
7. [`np.savez_compressed` 和 case summary：保存轨迹与审计证据](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L342-L405)
8. [`scene_summary.json`：汇总一个场景的全部 case](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py#L414-L434)
9. [`run_all_suites.sh`：三种 suite × 三个场景的实验编排](https://github.com/Nevermisc/rm-ik-rl/blob/main/projects/003-pi05-franka-isaaclab/scripts/run_all_suites.sh#L1-L24)

第一次不要从第一行看到最后一行。按下面顺序读：

1. `TASKS`：理解任务对象、指令和成功几何；
2. `make_cases()`：理解实验变量；
3. `DroidJointPosClient.infer()`：理解模型输入输出；
4. `main()` 中环境创建：理解 IsaacLab 初始化；
5. 内层 `for step`：理解闭环；
6. `inside/is_open/is_stable`：理解成功判定；
7. `np.savez_compressed` 和 summary：理解证据；
8. `run_all_suites.sh`：理解实验编排。

配套检索命令：

```bash
cd ~/robot-learning/rm-ik-rl

rg -n "class DroidJointPosClient|def infer" \
  projects/003-pi05-franka-isaaclab/scripts

rg -n "request =|action_chunk|env.step" \
  projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py

rg -n "inside =|is_open|is_stable|success =" \
  projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py

rg -n "np.savez|summary.json|scene_summary" \
  projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py
```

### 4.2.16 别人问你时，你应该能这样回答

**问：你在 Franka 阶段做了什么？**

答：我先用 OpenPI 的 π0.5 DROID joint-position checkpoint 建立模型服务，再用 sim-evals 在 Isaac Sim/IsaacLab 中提供 Franka + Robotiq、双相机和三个 DROID 风格场景。我写了客户端把两路 RGB、7 个关节角、夹爪状态和文字指令转换成模型请求，模型每次输出 `15×8` 动作块；仿真执行前 8 步后重新观察。随后我把单场景 smoke test 扩展为三场景严格基线、六类扰动和工程审计，并保存视频、轨迹和 JSON 证据。

**问：你为什么没有直接使用 LIBERO？**

答：LIBERO 用来验证 OpenPI 官方示例，但不是 Isaac Sim，也不是本项目的 Franka 环境。Franka 阶段选择 DROID joint-position checkpoint 和针对 DROID 策略调过的 sim-evals，使相机、关节状态和动作语义尽量对齐。

**问：你改了模型吗？**

答：Franka 阶段没有训练或修改 π0.5 权重。我改的是运行和评测层：显存分配、预热、观测字段转换、receding-horizon 执行、严格成功判定、扰动测试和证据记录。

**问：最关键的 bug 是什么？**

答：一类是首次 JAX 编译超过 WebSocket 心跳导致假超时，通过关闭 keepalive 并单独预热解决；一类是旧成功判定只看物体进入目标，可能没松爪，因此加入实际夹爪张开和稳定 15 步；另一类是环境超时自动 reset 被误记为关节跳变，因此在记录观测前先判断 terminated/truncated。

**问：Franka 成功证明了什么？**

答：证明模型服务、双相机、DROID 状态/动作接口和 IsaacLab 物理闭环在固定测试矩阵中可以工作。它不证明模型能直接控制 RM65，也不代表任意 Franka 场景有 96.3% 成功率。

**问：你怎么证明结果不是只看动画？**

答：每个 case 同时保存双视角视频、末帧、物体与目标位置、关节命令与观测、夹爪命令与观测、推理延迟和 JSON 成功判定。正式结果是 baseline `9/9`、robustness `17/18`，并保留唯一失败的任务条件。

### 4.3 终端 A：启动 π0.5 并完成冷启动预热

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
bash scripts/start_and_warmup_pi05.sh
```

该脚本会：

1. 在 `~/robot-learning/openpi` 启动 `openpi_server` 容器；
2. 使用 `pi05_droid_jointpos_polaris` 配置；
3. 加载 `gs://openpi-assets/checkpoints/pi05_droid_jointpos`；
4. 把 JAX 显存预占比例限制为 0.50，为 Isaac Sim 留显存；
5. 等待 WebSocket 8000 端口；
6. 发送一次假观测触发 JAX 编译。

验收：

```bash
docker ps --filter name=libero-openpi_server-1
docker logs --tail 80 libero-openpi_server-1
nvidia-smi
```

预热成功应看到：

```text
DROID_ACTION_SHAPE=(15, 8)
PI05_DROID_WARMUP=PASS
```

首次预热可能需要数分钟；之后稳态推理约 0.32 秒。曾出现的 `keepalive ping timeout` 是客户端在 JAX 首次编译期间误以为连接失活，不代表模型一定加载失败。先看服务器日志和 GPU 进程，再处理 WebSocket keepalive。

### 4.4 终端 B：只验证 DROID 场景和观测

这一步不调用 π0.5，只检查场景、机器人、三路相机中的策略两路相机，以及关节 shape：

```bash
cd ~/robot-learning/sim-evals

PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab/scripts/validate_droid_sim_scene.py
```

通过条件：

```text
arm_joint_pos=(7,)
gripper_pos=(1,)
external_cam=(180, 320, 3)
wrist_cam=(180, 320, 3)
DROID_SIM_SCENE_VALIDATION=PASS
```

输出图片位于：

```text
~/robot-learning/sim-evals/runs/scene_validation/
```

如果图像 shape 是 `(0,)`，这是相机还未完成渲染初始化，不能用黑图代替。应增加 reset/render 等待并重新读取，直到得到非空 `H×W×3` 图像。

### 4.5 先跑一个 Franka 场景

```bash
cd ~/robot-learning/sim-evals

PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab/scripts/run_pi05_franka_robustness_suite.py \
  --scene 1 \
  --suite baseline \
  --device cuda:0 \
  --headless
```

场景 1 的指令是 `put the cube in the bowl`。`baseline` 会运行 3 个回合。每个回合都应保存视频、末帧、轨迹和 JSON，而不是只凭 NoMachine 画面判断。

严格成功条件是：

1. 方块确实移动；
2. 方块中心进入碗的 XY 范围和合理高度；
3. 观测到夹爪已经张开；
4. 上述状态稳定保持 15 个控制步。

### 4.6 再跑三场景完整矩阵

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
bash scripts/run_all_suites.sh
```

脚本依次运行：

- `baseline`：3 个场景 × 每场景 3 回合，共 9 回合；
- `robustness`：3 个场景 × 6 种扰动，共 18 回合；
- `audit`：3 个场景 × 1 回合，共 3 回合。

合计 30 回合。任务成功率只统计前 27 个任务回合，audit 用于动作有限性、关节限位、跳变和推理延迟审计。

当前历史证据是：

```text
baseline：9/9
robustness：17/18
任务合计：26/27
```

结果目录：

```text
~/robot-learning/sim-evals/runs/pi05_franka_suite/
```

不要直接运行仓库中的两个 `summarize_pi05_franka_*.py` 来汇总新实验，因为它们保存的是 2026-09-14 历史运行的固定时间戳。学习阶段应先打开本次新生成的 `scene_summary.json`，核对 `scene`、`suite`、`cases_total`、`cases_successful` 和每个 case 的 `success`。之后再把汇总脚本改造成接受 `--run-root` 参数，这是一个合适的 Python 练习。

### 4.7 结束实验并释放显存

```bash
cd ~/robot-learning/rm-ik-rl/projects/003-pi05-franka-isaaclab
bash scripts/stop_pi05_server.sh
nvidia-smi
```

停止容器不会删除镜像、checkpoint 或实验结果。

### 4.8 从 Franka 迁移到 RM65 时，究竟改什么

| 层 | Franka 参考链路 | RM65-B + 4C2 链路 | 为什么必须改 |
|---|---|---|---|
| 机器人 | Franka 7 轴 + Robotiq | RM65 6 轴 + 4C2 | 自由度、限位和运动学不同 |
| checkpoint | DROID joint-position | `pi05_base` 经 RM65 数据 LoRA | DROID 动作分布不属于 RM65 |
| 状态 | 7 关节 + 夹爪 | 6 关节 + 归一化夹爪 | shape 和数值范围不同 |
| 动作 | `15×8` 绝对关节目标 | `10×7`，六轴目标 + 夹爪 | 动作宽度、chunk 长度和语义不同 |
| 相机 | sim-evals DROID 位姿 | RM65 外部相机 + 腕部相机 | 视角属于训练分布的一部分 |
| 环境 | 官方 DROID 三场景 | 自建 RM65 方块抓放场景 | 资产、接触和成功条件不同 |
| 数据 | DROID 预训练数据 | 45 条 RM65 脚本专家轨迹 | 新机器人需要自己的示教分布 |
| transform | DROID 字段映射 | `rm65_policy.py` | 模型字段、padding、归一化需适配 |

错误做法是把 Franka `15×8` 的前 6 个数直接发送给 RM65。即使 shape 勉强匹配，关节意义、零位、尺度、工作空间、动作统计和夹爪语义都不匹配。

正确迁移顺序是：

```text
组合 RM65 + 4C2 资产
→ 验证 articulation、限位、IK、碰撞和夹爪方向
→ 用 IK 状态机证明任务可解
→ 记录 RM65 双相机专家轨迹
→ 转换 LeRobot 数据并只用 train split 算 norm stats
→ 定义 RM65Inputs / RM65Outputs
→ 从 pi05_base 做 LoRA 微调
→ 单帧、离线 validation、IsaacLab 闭环三级验证
→ 固定随机采样后做可复现成功率评测
```

后续第 2～8 课逐项实现这条迁移路线。

### 这一步的意义

这是软件工程中的“已知良好基线”。它让排错从“所有东西都可能错”缩小为“RM65 迁移层可能错”。

## 5. 第 2 课：把 RM65 与 4C2 组合成机器人资产

### 目标

把 RM65 URDF 和用户提供的 4C2 URDF/STL 合成一棵无重名的机器人树，再导入 USD。

### 你亲手执行

```bash
cd ~/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab

python3 scripts/build_combined_urdf.py \
  --rm65-urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --rm65-mesh-dir ~/robot-learning/rm-ik-rl/assets/RM65-B/meshes \
  --gripper-urdf external/4C2/urdf/4C2.urdf \
  --gripper-mesh-dir external/4C2/meshes \
  --gripper-root-link base_link \
  --gripper-name-prefix tool_ \
  --output generated/learning_rm65_4c2.urdf \
  --report outputs/learning_combined_urdf_report.json

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/import_combined_urdf.py \
  --urdf generated/learning_rm65_4c2.urdf \
  --usd generated/learning_rm65_4c2.usd \
  --report outputs/learning_import_report.json \
  --headless
```

使用 `learning_` 前缀，避免覆盖正式资产。

### 你应检查的证据

```bash
python3 -m json.tool outputs/learning_combined_urdf_report.json | less
python3 -m json.tool outputs/learning_import_report.json | less
```

当前正式资产应包含 16 个 link、15 个 URDF joint、12 个可动 joint。12 个自由度由 6 个 RM65 关节、1 个夹爪主关节和 5 个软件耦合随动关节组成，并不代表有 12 个电机。

### 常见问题与解决思路

- RM65 和夹爪都有 `base_link`：给夹爪所有 link/joint 加 `tool_` 前缀。
- mesh 找不到：URDF 中的 package URI 必须解析成正确路径。
- 模型能显示但不能控制：显示成功不等于 articulation、drive、limit 和 collision 正确。
- 安装方向不对：修改固定关节变换，但最终要以真实法兰测量为准。

### 常用场景

换夹爪、换相机支架、把多个机器人部件组合成一个可控制资产时都会用到。

## 6. 第 3 课：验证关节、运动学和夹爪物理

### 目标

证明组合资产不是“只有外观”，而是关节顺序、限位、IK、开合方向和碰撞都正确。

### 关节与 IK

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/smoke_test_articulation.py \
  --usd generated/rm65_4c2_software.usd \
  --output outputs/learning_articulation_smoke.json \
  --gripper-control-mode software-coupled \
  --enable-gravity \
  --disable-moving-gripper-gravity \
  --headless

~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_combined_ik.py \
  --usd generated/rm65_4c2_software.usd \
  --urdf ~/robot-learning/rm-ik-rl/assets/RM65-B/urdf/RM65-B.urdf \
  --description ~/robot-learning/rm-ik-rl/rm65_robot_description.yaml \
  --output outputs/learning_combined_ik.json
```

正式结果中 Lula 位置误差约 `1.03e-6 m`、旋转误差约 `9.18e-4 rad`；12 个可达目标回归为 12/12。

### 夹爪方向和开口

```bash
~/robot-learning/IsaacLab/isaaclab.sh -p scripts/test_gripper_aperture.py \
  --usd generated/rm65_4c2_wide_pads.usd \
  --output outputs/learning_gripper_aperture.json \
  --headless
```

本项目约定：归一化 `0=张开`、`1=闭合`。几何校准显示归一化 0.20 时接触垫净空约 52.6 mm，能让 40 mm 方块通过并保留 5 mm 以上余量。

### 我们遇到的关键问题

- 原始凸包的接触主要来自夹爪基座，不是双侧指面。
- 加入独立薄碰撞垫后才形成可测量的双侧接触。
- NumPy `float64` 命令写入 PyTorch `float32` 张量会报错；写入前要匹配 device 与 dtype。
- 仿真碰撞垫是工程代理，不能冒充真实夹爪尺寸。

### 常用场景

任何涉及抓取、接触、末端工具或运动学求解的仿真项目都需要这一层验证。

## 7. 第 4 课：先让脚本专家完成任务

### 目标

用可解释的 IK 和状态机证明任务在当前场景中物理可完成，并产生训练示教。

### 状态机

```text
SOURCE_SETTLE → APPROACH → CLOSE → LIFT → TRANSFER
→ PLACE_DESCENT → OPEN → RETREAT → FINAL_SETTLE
```

### 运行小规模全重力套件

```bash
bash scripts/run_top_down_full_gravity_suite.sh
```

正式三角度结果为 3/3。注意这仍是脚本专家，且使用假定的 0.65 m 安装高度和未按实物标定的宽碰撞垫。

### 我们解决过的问题

| 问题 | 根因 | 解决方法 |
|---|---|---|
| 顶部抓取不可达 | 机器人安装面和世界桌面高度混淆 | 加 `robot_base_z_m=0.65` 并显式变换坐标系 |
| 下降途中腕部跳变 | IK 切换到等价但遥远的关节分支 | 用上一解 warm start，约束连续路径 |
| 边界样本无 IK | 固定预抓取距离越出工作空间 | 从安全距离向内搜索可解路点 |
| 释放后漂移 22.65 mm | 放置跟踪时间不足 | 每个约 1 cm 路点增加到 180 物理步 |

### 这一步的意义

专家成功证明“任务和场景可解”，并提供模型学习的目标行为。专家成功绝不能写成 π0.5 成功。

## 8. 第 5 课：采集可恢复的专家数据集

### 目标

用位置、转运角和同义指令的组合覆盖任务，而不是只录一条轨迹。

### 先小规模体验

```bash
python3 scripts/run_expert_collection_plan.py \
  --plan config/rm65_expert_collection_plan_v1.json \
  --dataset-root datasets/rm65_scripted_learning \
  --split train \
  --max-cases 1
```

确认一个 episode 后，再决定是否完整采集。正式数据集已经完成，不要覆盖它：

```text
datasets/rm65_scripted_v1
45/45 episode 通过
36 train，9 validation
20,175 帧
```

### 一帧数据

```text
observation_state：6 个实际关节角 + 1 个夹爪状态
external_image：外部 RGB
wrist_image：腕部 RGB
prompt：任务文字
action：6 个绝对关节目标 + 1 个夹爪目标
phase：脚本专家阶段，仅用于分析
cube_pose：任务验证信息，不作为策略输入
```

物理频率 240 Hz，每 12 步采样一次，数据频率为 20 Hz。必须先保存当前观测，再保存即将执行的动作，避免错一帧。

### 常用场景

示教学习、行为克隆、VLA 微调、失败回放和数据质量审计。

## 9. 第 6 课：转换 LeRobot 数据并计算归一化统计

### 目标

把项目 episode 转成 OpenPI 的数据契约，并只用训练集计算 state/action 统计。

### 练习命令

```bash
python3 scripts/convert_expert_episodes_to_lerobot.py \
  datasets/rm65_scripted_v1 \
  --repo-id local/rm65_sim_learning

python3 scripts/compute_rm65_norm_stats.py \
  --repo-id local/rm65_sim_learning \
  --output outputs/learning_norm_stats_report.json
```

不要在不理解 `--overwrite` 的情况下覆盖正式数据。正式 repo id 是：

```text
v1：local/rm65_sim_train / local/rm65_sim_validation
v2：local/rm65_sim_policy_train / local/rm65_sim_policy_validation
```

### 为什么 repo id 很重要

OpenPI 根据 repo id 查找归一化统计。训练与推理 repo id 不一致时，模型可能仍能运行，却会把动作反归一化到错误尺度，这是很隐蔽的错误。

### policy-window v2 的目的

v1 开头有大量静止帧，只有约 31.6% 的起始 10 步窗口包含运动。v2 缩短等待段，使保留的 90/90 个起始窗口都包含开始运动。它是一次有证据的假设实验；最终闭环从 60% 降到 55%，说明这个改动单独使用没有提升总体任务成功率。

## 10. 第 7 课：在 16 GB 显存上微调 π0.5

### 目标

理解 LoRA、显存预算、训练 smoke test、checkpoint 和 loss 证据。

### 当前配置

```text
基础模型：pi05_base
动作 horizon：10
模型内部动作宽度：32，RM65 有效语义为前 7 维
PaliGemma LoRA rank：16
action expert LoRA rank：32
batch size：1
最大 token：64
冻结 SigLIP 视觉编码器
```

默认配置曾需要额外约 5.36 GiB，导致 16 GB GPU OOM。缩短 token 并冻结视觉塔后，估计训练显存约 7.35 GiB。

### 正确的学习顺序

```bash
# 1. 只做前置检查，不训练
bash scripts/train_rm65_pi05_policy_window.sh preflight

# 2. 阅读配置
less openpi_extension/rm65_training_config.py
less scripts/train_rm65_pi05.py

# 3. 真正重训前先确认没有别的训练进程
pgrep -af train_rm65_pi05.py || true
nvidia-smi
```

正式 v1、v2 都训练了 30,000 步。v2 训练日志有 300 个记录点，loss 从 0.2278 降至 0.0022，数值全部有限。loss 下降只代表优化正常，不代表任务成功。

### 常用场景

低显存微调、检查 OOM、比较不同数据视图、恢复中断训练。

## 11. 第 8 课：理解三层验证

### 11.1 checkpoint 单帧验证

检查权重能加载、输出 `(10,7)`、数值有限和动作安全层可处理。它不运行完整任务。

### 11.2 validation 离线误差

比较模型动作与未参与训练的专家动作。v1 六轴动作 MAE 约 0.00470 rad；v2 policy-window 六轴 horizon MAE 约 0.00534 rad。低 MAE 仍不能替代闭环。

### 11.3 IsaacLab 闭环评测

```text
观察 → 推理 10 步 → 安全层 → 执行前 5 步 → 重新观察
```

20 个评测条件使用训练范围内的新角度 `0.65/0.75/0.85/0.95`、新位置组合和多种同义指令。通过门槛：至少 20 个有效 episode 且成功率至少 80%。

正式结果：

```text
v1：12/20 = 60%，FAIL
v2：11/20 = 55%，FAIL
v2 相对 v1：4 改善、5 退步、7 稳定成功、4 稳定失败
```

运行单例或全套前必须先解决第 12 节的确定性采样问题。

## 12. 当前正在解决的问题：可复现的 π0.5 采样

π0.5 的 flow-matching 推理会从随机高斯噪声开始。OpenPI 默认在服务器内维护一个不断推进的 JAX RNG。如果评测从中途续跑，已经完成的案例被跳过，新服务器却从 RNG 0 重新开始，后续案例会拿到与原完整运行不同的噪声。

我们通过同一 checkpoint 的复测发现明显翻转，甚至某案例最终误差从 5.7 cm 变成 38.8 m。已完成 16 个开发复测，8/16 通过；这个结果只用于暴露问题，不能作为新的正式模型成功率。

正确修复目标是：

1. 每个 case 有固定 `policy_noise_seed`；
2. 每个 action chunk 使用 `case_seed + chunk_index`；
3. 客户端把 seed 发给策略服务；
4. 服务显式生成 `10×32 float32` 高斯噪声并传给 `Policy.infer(noise=...)`；
5. 报告记录 seed 和 noise SHA-256；
6. 单例运行、完整运行和断点续跑的相同 case 必须得到相同噪声哈希与动作。

截至本文生成时，这个修复只有 Windows 临时草稿，尚未同步、测试或提交，不能写成已完成。

## 13. 安全层和门禁

`action_guard.py` 检查：

- NaN/Inf；
- 六轴关节限位与余量；
- 单步最大关节变化 0.05 rad；
- 夹爪范围 `[0,1]`。

仿真报告必须明确：

```json
{
  "simulation_only": true,
  "real_robot_command_sent": false
}
```

当前机器可读进度中：脚本专家、数据集、微调和离线验证已完成；π0.5 仿真闭环未过 80%；真机阶段按用户要求延期。因此不能执行真机动作。

## 14. 如何读代码并开始自己修改

按下面顺序，每个文件只回答输入、输出、单位、失败行为：

```text
openpi_extension/expert_episode.py       数据帧与 episode
openpi_extension/rm65_policy.py          RM65 ↔ π0.5 字段变换
openpi_extension/action_guard.py         动作安全层
openpi_extension/rm65_training_config.py 训练配置
scripts/run_pick_place_baseline.py        场景、专家与模型闭环
scripts/convert_expert_episodes_to_lerobot.py
scripts/train_rm65_pi05.py
scripts/serve_rm65_policy.py
scripts/run_pi05_rm65_closed_loop_suite.py
scripts/analyze_rm65_closed_loop_failures.py
```

推荐练习：

1. 用 `rg -n "policy_execute_actions_per_chunk"` 找到动作块执行数量；
2. 解释从 5 改成 3 对响应速度、推理频率和稳定性的影响；
3. 在单元测试中加入 NaN 动作，观察 fail-closed；
4. 画一条 episode 的六轴 state/action 曲线并标出 CLOSE、LIFT、OPEN；
5. 为确定性 seed 先写测试，再修改服务器和运行器。

## 15. 你何时算真正掌握了这一阶段

你能独立完成以下任务时，才算能力已经迁移给你：

- 从 URDF 解释 link、joint、limit、mimic 和固定安装关节；
- 通过报告证明 USD articulation 与 IK 正确；
- 分清脚本专家、离线模型和 π0.5 闭环结果；
- 解释 7 维真实动作为什么在模型内部填充到 32 维；
- 从一个 episode 追踪图像、状态、动作和时间对齐；
- 解释 norm stats 与 repo id 的关系；
- 独立运行 preflight、单帧验证、离线验证和闭环单例；
- 根据机器报告定位物理、数据、模型、控制器或基础设施问题；
- 不用“机械臂动了”代替严格任务成功；
- 能让相同随机种子的评测重复得到同一动作序列。

## 16. 配套权威资料

```text
docs/FULL_PROJECT_TUTORIAL_ZH.md
docs/CODE_ARCHITECTURE_GUIDE_ZH.md
docs/RM65_4C2_STAGE_REPORT_ZH.md
docs/RM65_EXPERT_DATASET_ZH.md
results/project_progress.json
results/rm65_pi05_eval_v1_summary.json
results/rm65_pi05_eval_v2_summary.json
results/pi05_rm65_policy_window_v2_comparison_to_v1.json
```

安装步骤对应的上游入口：

- Docker Ubuntu 安装：`https://docs.docker.com/engine/install/ubuntu/`
- NVIDIA Container Toolkit：`https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html`
- IsaacLab 二进制安装：`https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/binaries_installation.html`
- OpenPI：`https://github.com/Physical-Intelligence/openpi`
- DROID sim-evals：`https://github.com/arhanjain/sim-evals`

任何结论都优先以当前 Git 提交和 `results/*.json` 为准，而不是以聊天记忆为准。
