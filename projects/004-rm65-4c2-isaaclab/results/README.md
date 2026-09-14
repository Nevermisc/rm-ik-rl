# 验证结果说明

这里保存脚本实际生成的机器可读报告。运行：

```bash
python3 scripts/summarize_stage_results.py
```

脚本会重新检查所有关键断言，并生成 `stage_summary.json`。

`articulation_smoke_gravity.json` 的 `status` 有意保留为 `fail`。它记录 4C2 原始物理模型在全部刚体启用重力时的已知失败，用于防止以后误删重力隔离措施。阶段汇总只有在这个诊断仍被识别为已知失败、其余验收项全部通过时，才会输出 `pass_with_known_limitations`。
