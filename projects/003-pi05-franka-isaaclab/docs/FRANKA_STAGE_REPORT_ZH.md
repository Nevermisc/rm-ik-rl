# π0.5 + Franka + Isaac Lab 阶段完整报告与复现手册

## 一、这一阶段的目标和结论

这一阶段的目标，是先在 π0.5 熟悉的 Franka + Robotiq 机器人和 DROID 风格环境中，把完整闭环跑通并建立可重复的评测基线，然后再迁移到 RM65。

截至 2026-09-14，已经完成：

1. π0.5 joint-position checkpoint 在 RTX 4060 Ti 16 GB 上加载和推理；
2. Isaac Sim 5.1.0 和 Isaac Lab 2.3.2 与 π0.5 同时运行；
3. 外部相机、腕部相机、7 关节状态和夹爪状态组成闭环观测；
4. 三个官方 DROID 仿真任务均完整完成抓取、搬运、松爪和稳定放置；
5. 对物体位置、目标位置、语言表达和画面亮度做了 18 个扰动测试；
6. 记录并检查了关节限位、动作跳变、NaN/Inf 和推理延迟；
7. 所有回合均保存输入视频、末帧、物体轨迹和 JSON 结果。

任务层评测共 27 回合：

| 评测组 | 成功数 | 总数 | 说明 |
|---|---:|---:|---|
| 三场景严格基线 | 9 | 9 | 每个场景重复 3 次 |
| 三场景鲁棒性 | 17 | 18 | 每个场景 6 种变化 |
| 合计 | 26 | 27 | 96.3%，仅代表本测试矩阵 |

另做 3 个工程审计回合。其中场景 1、2 完成任务，场景 3 的一次随机采样未完成；但三个回合的关节和延迟数据都有效。

这个结论支持“Franka 参考链路已经跑通，可以作为 RM65 迁移基线”。它不支持“π0.5 在所有 Franka 场景中成功率为 96.3%”，因为样本量小、场景固定，而且 sim-evals 本身就是针对 DROID 策略调整过的环境。

## 二、什么叫完整闭环

完整数据流如下：

```text
英文任务指令
外部相机 RGB
腕部相机 RGB
Franka 7 个实际关节角
Robotiq 实际夹爪位置
        │
        ▼
π0.5 DROID joint-position 策略
        │
        ├── 预测 15×8 动作块
        │   7 个绝对目标关节角 + 1 个夹爪命令
        │
        └── 执行前 8 步后重新观察和规划
                        │
                        ▼
Isaac Lab Action Manager
                        │
                        ▼
Isaac Sim 物理、碰撞与相机渲染
                        │
                        └── 新观测反馈给 π0.5
```

控制频率是 15 Hz。每执行 8 步，也就是大约 0.53 秒，就使用最新画面和状态重新调用一次 π0.5。它不是提前生成整段固定轨迹后盲目播放，因此第一次抓取失败后有机会再次观察并恢复。

## 三、为什么使用 DROID 和 sim-evals

DROID 在这里不是仿真器。它定义了一套 π0.5 熟悉的机器人数据分布：Franka 机械臂、Robotiq 夹爪、外部/腕部相机、关节位置状态以及对应动作。

Isaac Sim 是物理与渲染引擎；Isaac Lab 是组织机器人、传感器、动作和回合的 Python 框架；sim-evals 则在 Isaac Sim 中搭建接近 DROID 数据分布的三个场景。

前面通用 Isaac 方块场景虽然能让机械臂运动，但它的相机、状态含义和动作坐标与模型训练格式不一致。换成 DROID joint-position checkpoint 和 sim-evals 后，模型输入输出与环境接口才真正对齐。

## 四、软硬件版本

| 项目 | 本次使用内容 |
|---|---|
| GPU | NVIDIA RTX 4060 Ti 16 GB |
| 内存 | 32 GB |
| Linux | Ubuntu 22.04 |
| Isaac Sim | 5.1.0 |
| Isaac Lab | 2.3.2 |
| OpenPI commit | `15a9616` |
| sim-evals commit | `3a6b0e8` |
| 策略配置 | `pi05_droid_jointpos_polaris` |
| checkpoint | `gs://openpi-assets/checkpoints/pi05_droid_jointpos` |
| 服务端口 | WebSocket `8000` |
| 仿真控制频率 | 15 Hz |
| 策略执行长度 | 每次预测 15 步，执行 8 步后重新规划 |
| 相机渲染 | 180×320，再补边缩放为 224×224 输入模型 |

## 五、从零启动的操作步骤

以下命令均在实验室 Linux 电脑上运行。建议开两个 SSH 终端：终端 A 管模型服务，终端 B 管 Isaac Lab。

### 1. 检查电脑资源

```bash
free -h
nvidia-smi
df -h ~
```

你要看三个地方：

- `free -h` 的 `available` 是 Linux 真正还能分配的内存；
- `nvidia-smi` 的 `Memory-Usage` 是显存，不是系统内存；
- `df -h ~` 是硬盘空间。

### 2. 检查 Docker 容器

```bash
docker ps -a
```

π0.5 服务容器名称是：

```text
libero-openpi_server-1
```

Docker 容器可以理解成一个隔离的软件运行箱。π0.5 和它的 Python/JAX/CUDA 依赖装在箱子里，Isaac Lab 运行在 Linux 主机上，两者通过本机 8000 端口通信。

### 3. 启动 π0.5 joint-position 服务

```bash
cd ~/robot-learning/openpi

SERVER_ARGS="policy:checkpoint \
  --policy.config=pi05_droid_jointpos_polaris \
  --policy.dir=gs://openpi-assets/checkpoints/pi05_droid_jointpos" \
docker compose \
  -f examples/libero/compose.yml \
  -f openpi-gpu-memory.override.yml \
  up -d --no-build --force-recreate openpi_server
```

查看服务日志：

```bash
docker logs -f libero-openpi_server-1
```

看到下面内容表示模型加载完成并开始监听：

```text
server listening on 0.0.0.0:8000
```

`openpi-gpu-memory.override.yml` 把 JAX 的显存预占比例限制为 0.50。否则 π0.5 可能抢占绝大部分 16 GB 显存，让 Isaac Sim 无法启动。

### 4. 做第一次推理预热

第一次推理会让 JAX 编译计算图。本机实测约 158 秒。预热命令：

```bash
cd ~/robot-learning/openpi

docker exec -i libero-openpi_server-1 \
  /.venv/bin/python3 -u - \
  < warmup_pi05_droid.py
```

成功输出：

```text
DROID_WARMUP_SECONDS=158.106
DROID_ACTION_SHAPE=(15, 8)
PI05_DROID_WARMUP=PASS
```

`(15, 8)` 的含义是一次产生 15 个动作，每个动作有 8 个数：7 个关节位置和 1 个夹爪命令。

### 5. 跑严格基线

进入仿真项目：

```bash
cd ~/robot-learning/sim-evals
```

场景 1，魔方进碗：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  run_pi05_franka_robustness_suite.py \
  --scene 1 --suite baseline --device cuda:0 --headless
```

场景 2，罐头进杯：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  run_pi05_franka_robustness_suite.py \
  --scene 2 --suite baseline --device cuda:0 --headless
```

场景 3，香蕉进收纳盒：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  run_pi05_franka_robustness_suite.py \
  --scene 3 --suite baseline --device cuda:0 --headless
```

每条命令会重复 3 个回合。

### 6. 跑鲁棒性评测

把 `baseline` 改成 `robustness`：

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  run_pi05_franka_robustness_suite.py \
  --scene 1 --suite robustness --device cuda:0 --headless
```

分别把 `--scene` 改为 1、2、3。每个场景执行：

| 用例 | 变化 |
|---|---|
| `source_plus` | 操作物移动 +3.5 cm、+2 cm |
| `source_minus` | 操作物移动 -3.5 cm、-2 cm |
| `target_shift` | 目标容器移动 +2.5 cm、-2 cm |
| `paraphrase` | 使用意思相同的更长英文指令 |
| `darker_input` | 送给模型的两路图像亮度乘 0.75 |
| `brighter_input` | 送给模型的两路图像亮度乘 1.25 |

这些扰动不是训练，也不会修改模型权重。它们是在检查预训练策略遇到轻微变化时是否还能完成任务。

### 7. 跑工程审计

```bash
PYTHONPATH=~/robot-learning/sim-evals/src \
~/robot-learning/IsaacLab/isaaclab.sh -p \
  run_pi05_franka_robustness_suite.py \
  --scene 1 --suite audit --device cuda:0 --headless
```

同样将场景改为 1、2、3。审计会额外保存：

- π0.5 输出的完整 7 关节目标；
- 仿真实际 7 关节状态；
- 每次重新规划的网络与模型推理时间；
- 关节限位余量；
- 动作和观测是否含 NaN/Inf；
- 最大指令跳变与最大实际关节跳变。

### 8. 停止模型并释放显存

```bash
docker stop libero-openpi_server-1
```

checkpoint 和容器不会被删除。下次使用 `docker start libero-openpi_server-1` 即可重新启动，但新进程的第一次推理仍需重新编译预热。

## 六、成功判定为什么比“看见它动了”严格

旧判定只要求物体进入容器区域，因此可能在夹爪仍抓着物体时提前停止。新版必须同时满足：

1. 操作物至少移动 5 cm；
2. 操作物 XY 中心进入目标容器范围；
3. 操作物高度处于容器合理范围；
4. 仿真反馈的实际夹爪位置小于 0.25，即已经张开；
5. 操作物在最近 15 步、约 1 秒内的移动范围不超过 1.5 cm；
6. 上述“已进入、已松爪、已稳定”状态连续保持 15 步。

因此日志中的：

```text
严格成功：已松爪，物体稳定留在目标中。
```

代表完成了完整放置，不只是抓住或搬到目标上方。

## 七、27 回合任务评测结果

### 严格基线

| 场景 | 指令 | 结果 |
|---|---|---:|
| 1 | `put the cube in the bowl` | 3/3 |
| 2 | `put the can in the mug` | 3/3 |
| 3 | `put banana in the bin` | 3/3 |
| 合计 |  | 9/9 |

### 鲁棒性矩阵

| 测试 | 魔方进碗 | 罐头进杯 | 香蕉进盒 |
|---|---:|---:|---:|
| 操作物正向偏移 | 成功 | 成功 | 成功 |
| 操作物反向偏移 | 成功 | 成功 | 成功 |
| 目标容器偏移 | 成功 | **失败** | 成功 |
| 同义指令 | 成功 | 成功 | 成功 |
| 图像变暗 25% | 成功 | 成功 | 成功 |
| 图像变亮 25% | 成功 | 成功 | 成功 |
| 合计 | 6/6 | 5/6 | 6/6 |

唯一失败是场景 2 的移动杯子用例。罐头曾到达杯口区域，但释放后没有稳定留在杯中；之后策略长期保持停止，直至 30 秒回合超时。窄口容器对目标位姿误差更敏感，这是合理但需要记录的模型边界。

香蕉的变亮用例用了 409 步才成功。前两次操作未稳定完成，第三次重新抓取后才将香蕉放入盒内。这是闭环恢复能力的实际样本，也说明只统计是否成功会隐藏执行效率差异。

## 八、工程审计结果

| 指标 | 场景 1 | 场景 2 | 场景 3 |
|---|---:|---:|---:|
| 动作全部有限数值 | 是 | 是 | 是 |
| 观测全部有限数值 | 是 | 是 | 是 |
| 最小关节限位余量 | 0.301 rad | 0.397 rad | 0.267 rad |
| 最大目标关节单步跳变 | 0.234 rad | 0.227 rad | 0.332 rad |
| 最大实际关节单步跳变 | 0.061 rad | 0.066 rad | 0.080 rad |
| 重新规划次数 | 17 | 28 | 55 |
| 推理延迟中位数 | 0.318 s | 0.318 s | 0.318 s |
| 推理延迟 P95 | 0.326 s | 0.326 s | 0.327 s |
| 推理延迟最大值 | 0.331 s | 0.327 s | 0.329 s |

三场景最小关节限位余量是 0.267 rad，约 15.3°。策略目标最大单步变化是 0.332 rad，但仿真控制器把实际最大单步变化平滑到了 0.080 rad，约 4.6°。

场景 3 审计回合结束时曾显示 1.2966 rad 跳变。检查轨迹后确认这是 Isaac Lab 在 time-out 时自动重置机械臂，重置后的第一帧被错误记进上一回合。剔除该自动回零样本后，真实最大跳变为 0.0800 rad；记录器已经修复，后续不会混入终止后的重置状态。

约 0.318 秒的推理时间不会让仿真暂停 0.318 秒后只执行一步，因为一次推理产生动作块，随后连续执行 8 步。平均到 8 个控制步约为每步 40 ms，能够支持本实验的 15 Hz 控制节奏。

## 九、结果文件在哪里

Linux 总目录：

```text
~/robot-learning/sim-evals/runs/pi05_franka_suite/
```

每个用例目录包含：

```text
policy_views.mp4
final_policy_view.png
final_external_camera.png
final_wrist_camera.png
trajectory.npz
summary.json
```

其中：

- `policy_views.mp4` 是模型实际接收的外部与腕部画面拼接；
- `trajectory.npz` 保存操作物、目标、夹爪、关节和推理延迟；
- `summary.json` 保存该用例是否成功以及量化指标；
- `scene_summary.json` 汇总当前场景；
- `pi05_franka_robustness_report_20260914.json` 汇总 27 个任务回合；
- `pi05_franka_engineering_audit_20260914.json` 汇总三个审计回合。

## 十、常见日志怎么判断

### 可以暂时忽略的警告

```text
GLFW initialization failed
failed to open the default display
```

使用 `--headless` 时没有图形桌面，仍可在 GPU 中离屏渲染。

```text
Could not open asset ... my_droid.usdz
```

场景 USD 中有一个未使用的重复机器人引用。实际 Franka+Robotiq 由 Isaac Lab 配置单独加载；关节、夹爪和相机均已通过测试。

```text
table ... material:binding ... Ignoring
```

部分桌腿材质引用路径不完整，影响局部外观，不影响物理任务。

### 需要处理的错误

```text
CUDA out of memory
```

先确认 `XLA_PYTHON_CLIENT_MEM_FRACTION=0.5` 生效，关闭其他 GPU 程序，并保持 180×320 相机分辨率。

```text
keepalive ping timeout
```

通常发生在第一次 JAX 编译。先运行预热脚本，并在预热客户端中关闭 WebSocket ping。

```text
Connection refused: 127.0.0.1:8000
```

π0.5 容器没有启动或还没加载完成。检查：

```bash
docker ps
docker logs --tail 50 libero-openpi_server-1
```

## 十一、你应该能解释的技术点

完成这一阶段后，建议你能不看资料解释以下问题：

1. Docker 容器和 Linux 主机各运行什么；
2. 为什么 π0.5 和 Isaac Sim 可以通过 WebSocket 解耦；
3. 为什么 joint-position checkpoint 比 velocity checkpoint 更适合当前环境；
4. 模型输入的五项内容分别是什么；
5. `(15, 8)` 动作块的两个维度各表示什么；
6. 为什么只执行 8 步就重新规划；
7. 为什么“物体进入目标区域”还不能直接算完整成功；
8. 为什么 sim-evals 中高成功率不能直接代表 RM65 或真实实验室成功率；
9. 域差异包括机器人关节、相机、背景、动作定义和物理参数中的哪些部分；
10. 迁移到真机前为什么必须有动作限位、速度限制、工作空间边界和急停。

## 十二、现在处于项目路线的哪一步

| 阶段 | 状态 |
|---|---|
| π0.5 单次推理 | 完成 |
| Franka 三个完整仿真任务 | 完成 |
| 严格松爪与稳定放置判定 | 完成 |
| 轻量位置/语言/亮度鲁棒性 | 完成，17/18 |
| 关节和推理工程审计 | 完成 |
| RM65 模型导入 Isaac Lab | 下一步 |
| RM65 确定性控制 | 未开始 |
| RM65 的 π0.5 动作/状态适配 | 未开始 |
| RM65 数据采集与微调 | 未开始 |
| RM65 真机安全部署 | 未开始 |

Franka 阶段已经形成可用的参考基线。下一步迁移 RM65 时，不会直接把 Franka USD 换成 RM65 外观，而是先检查 RM65 的 6 个关节、坐标轴、限位、碰撞体、末端坐标系和夹爪，再建立与本报告相同的观测、动作、成功判定和安全审计接口。
