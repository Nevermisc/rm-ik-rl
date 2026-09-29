# RM65 pi0.5 数据保存与恢复合同

## 结论

数据集和 checkpoint 不直接提交普通 Git，但必须至少保留两份经过 SHA-256 验证的副本。Git 只保存代码、配置、实验日志、紧凑 manifest 和备份验证结果。

## v3 核心资产

资产范围由 `config/rm65_pi05_v3_preservation_assets.json` 冻结，包括：

- 36 条基础专家数据和 30 条失败纠正专家数据；
- 由两份原始数据转换出的 66 episode LeRobot 数据；
- v2 `29999` 起始 checkpoint、v3 `9999` 最终 checkpoint 和冻结 norm stats；
- v3 首次正式确认 run1，以及 repeatability run2/run3 的原始报告、图像和 episode 数据。

原始训练数据和 checkpoint 是 critical；转换数据可由原始数据和 Git 代码重建，但保留副本能显著缩短恢复时间；正式评测的 RTX 图像和动作轨迹不能假定可逐位重建。

## Manifest 与验证

`scripts/build_data_preservation_manifest.py` 对每个资产逐文件计算 SHA-256，再用相对路径、字节数和文件摘要计算紧凑 tree hash。它不把文件内容或完整文件列表写进 Git，因此适合审计数 GB 资产。

源端示例：

```bash
python3 scripts/build_data_preservation_manifest.py \
  --spec config/rm65_pi05_v3_preservation_assets.json \
  --location source \
  --root project=/home/chengyu/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab \
  --root home=/home/chengyu \
  --root openpi=/home/chengyu/robot-learning/openpi \
  --output results/rm65_pi05_v3_source_preservation_manifest.json
```

复制到另一台机器或存储设备后，在备份端使用 `--location backup --root backup=<备份根目录>`，并通过 `--reference` 指向源 manifest。只有 `comparison_status=pass` 才算一份已验证副本。

## 恢复优先级

1. 恢复原始训练数据、v2/v3 checkpoint 和 norm stats。
2. 用 Git commit、转换报告和冻结配置重建/核对 LeRobot 数据。
3. 恢复正式评测原始数据，用紧凑 summary 和 failure taxonomy 交叉验证结果。
4. 运行 manifest 比较；任一 tree hash 不一致时不得把备份标记为有效。

## 禁止事项

- 不把 datasets、checkpoint、视频或批量 PNG 暂存到 Git。
- 不用“文件数量相同”代替内容哈希验证。
- 不在仿真仍写入某个目录时为该目录生成最终 manifest。
- 不覆盖现有 v2/v3 checkpoint；新版本使用新目录和新 manifest。
