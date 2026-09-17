# 更换实验室 Linux 电脑：迁移与验收清单

更换的是运行 Isaac Sim、IsaacLab、OpenPI、Docker 并连接 RM65 的实验室 Linux 电脑。旧电脑必须至少再开机一次完成清点和数据迁移。在迁移验收结束前，不要格式化、重装、交还或清空旧电脑。

## 为什么不能只依赖 GitHub

GitHub 已保存源代码、中文文档和小型结果，但有意排除了大文件与机器配置。旧实验室电脑可能独有：

- Isaac Sim 5.1.0 与 IsaacLab 安装；
- OpenPI 源码环境和 Python/uv 依赖；
- Docker 镜像、compose 配置和容器挂载关系；
- π0.5 checkpoint 与归一化资产；
- RM65、4C2 mesh、生成 URDF/USD；
- 尚未提交的日志、相机图像和 episode；
- NVIDIA 驱动、CUDA、NVIDIA Container Toolkit 配置；
- Tailscale、SSH、NoMachine 服务；
- RM65 网络、ROS/SDK、串口或 udev 配置。

系统软件可以重装，但模型、checkpoint、原始机器人资产、实验数据和未提交改动必须先备份。

## 推荐迁移方法

不直接克隆整个系统盘。先做可审计的分层迁移：

1. 清点旧电脑硬件、系统、磁盘、Git、Docker和关键目录；
2. 把可复现源代码推送 GitHub；
3. 把不可替代的大文件复制到移动硬盘或新电脑；
4. 在新电脑干净安装驱动、Docker、Isaac Sim、IsaacLab 与 OpenPI；
5. 恢复资产和 checkpoint；
6. 从低层到高层逐项复测；
7. 仿真完全恢复以后再连接 RM65，且先做空载低速测试。

这样能避免把旧系统中未知的驱动冲突、缓存和损坏环境原样复制过去。

## 明天需要的条件

- 旧实验室电脑能开机并本地登录；
- 新实验室电脑能开机并安装 Linux；
- 两台电脑位于同一局域网，或者准备容量足够的移动硬盘；
- 新电脑硬件信息，尤其是 GPU 型号与显存、内存、系统盘和数据盘容量；
- 暂时不要把 RM65 控制权交给新电脑。

Windows 电脑上的 `D:\\d\\4C2` 是原始夹爪模型的额外副本。仓库中的
`results/4c2_original_source_manifest.json` 记录了它的文件数量、总字节数和
逐文件 SHA-256；恢复到新实验室电脑后可用同一脚本重新生成清单并比较。

## 旧电脑第一步：只读清点

进入当前项目后运行：

```bash
cd ~/robot-learning/004-rm65-4c2-isaaclab
bash scripts/audit_lab_migration.sh
```

报告默认写入：

```text
outputs/migration_audit/
```

该脚本不读取环境变量值、密码、SSH 私钥或 token，也不修改系统。
报告位于被 Git 忽略的 `outputs/` 中；检查内容后再决定是否复制，不直接上传。

需要重点确认的目录：

```text
~/robot-learning/004-rm65-4c2-isaaclab
~/robot-learning/openpi
~/robot-learning/IsaacLab
~/robot-learning/rm-ik-rl
~/robot-learning/004-rm65-4c2-isaaclab/external/4C2
```

还要根据 Docker inspect 找到 `/openpi_assets` 在宿主机的真实挂载来源。π0.5 参数恢复日志显示 checkpoint 约 6.2 GiB，不能假设它已经在 GitHub。

## 必须备份的内容

### 第一优先级：不可替代

- 4C2 原始模型及纹理；
- RM65 原始模型、SDK 和自定义配置；
- 所有尚未上传的 episode、相机图像和实验输出；
- 自己生成的 checkpoint、norm stats；
- 机器人标定参数、相机内外参、网络和驱动配置。

### 第二优先级：可以下载，但复制更省时间

- `pi05_base`、`pi05_libero` 等官方 checkpoint；
- Hugging Face/Google Storage 模型缓存；
- Isaac Sim 安装包或离线包；
- Docker 镜像。

### 第三优先级：重新安装

- NVIDIA 驱动与 CUDA 运行时；
- Docker Engine 与 NVIDIA Container Toolkit；
- Tailscale、NoMachine、Git；
- Python/uv 虚拟环境。

驱动和系统级库优先在新电脑重新安装，不复制旧 `/usr`、`/lib` 或整个根分区。

## 复制方式

两台机器同时在线时，优先从新电脑使用 `rsync` 拉取，并保留断点续传：

```bash
rsync -aHAX --numeric-ids --info=progress2 --partial \
  iot22@OLD_IP:/home/iot22/robot-learning/ \
  /home/iot22/robot-learning/
```

在真正执行前必须先用 `--dry-run` 检查来源和目标。等清点出 checkpoint 的宿主机路径后，再单独复制该目录。不要在尚未确认路径时执行带 `--delete` 的 rsync。

如果使用移动硬盘，建议使用 ext4；NTFS/exFAT 可能丢失 Linux 权限和符号链接。使用非 Linux 文件系统时，把目录先归档为 tar，再复制归档文件。

## 新电脑安装顺序

1. Ubuntu 与系统更新；
2. 与新 GPU 匹配的 NVIDIA 驱动；
3. Docker Engine 与 NVIDIA Container Toolkit；
4. Tailscale、OpenSSH Server、NoMachine；
5. Isaac Sim 5.1.0；
6. 与当前版本匹配的 IsaacLab；
7. OpenPI 与 uv 环境；
8. 恢复 RM65、4C2、checkpoint 和项目数据；
9. 重建 Docker 服务；
10. 更新 Windows 端 SSH/NoMachine 中的 Tailscale 地址。

## 分层验收

验收必须按顺序进行，前一层失败时不继续连接真机。

1. `nvidia-smi` 与 Docker GPU 测试；
2. Isaac Sim 空场景启动；
3. 组合 USD articulation 冒烟测试；
4. Lula IK 与 12 个目标测试；
5. 4C2 接触、抬升和转运测试；
6. 顶部抓取全重力 0.6/0.8/1.0 rad 三次回归；
7. 双相机专家 episode 记录；
8. OpenPI π0.5 推理服务与 RM65 数据 contract；
9. π0.5 在 IsaacLab 中闭环评测；
10. 急停、限速、工作空间和空载真机测试；
11. 最后才允许带物体真机任务。

## 旧电脑何时可以停用

同时满足以下条件后才可以停用旧电脑：

- GitHub 工作区干净且最新提交已推送；
- 不可替代资产至少有两份副本；
- checkpoint 与数据集的文件数量、总大小和 SHA-256 清单一致；
- 新电脑通过顶部抓取全重力回归；
- 新电脑能启动 π0.5 服务并完成非执行式推理；
- Tailscale、SSH 和 NoMachine 均可从 Windows 访问；
- RM65 仍未接收未经验证的策略动作。
