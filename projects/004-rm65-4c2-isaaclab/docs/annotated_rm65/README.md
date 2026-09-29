# RM65 π0.5 核心程序逐行中文注释索引

这些文件由实验室电脑当前提交 `80f6af6743e9fb8a54fac8dd12ee7818828f37f7` 的源码快照生成。共覆盖 20 个核心程序、4659 行生产源码。

逐行注释是**非执行学习副本**。当前为 v3“零基础双层讲解版”：每一行先拆关键字、圆括号、方括号、冒号、点号、等号及求值顺序，再解释“操作的 RM65/4C2/π0.5 对象是什么、数据是什么 shape、从哪里来、接下来去哪里”。生产源码位于 `rm65_source_snapshot/`，实验室电脑中的正式路径为：

```text
/home/chengyu/robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab
```

## 推荐学习顺序

0. [`00_PYTHON_NUMPY_ZERO_BASICS_ZH.md`](00_PYTHON_NUMPY_ZERO_BASICS_ZH.md)：先学习括号、字典、数组、shape、函数、类和完整数据流；
1. [`rm65_policy.py.逐行注释.md`](rm65_policy.py.逐行注释.md)：模型输入输出翻译；
2. [`expert_episode.py.逐行注释.md`](expert_episode.py.逐行注释.md)：一帧专家数据是什么；
3. [`run_expert_collection_plan.py.逐行注释.md`](run_expert_collection_plan.py.逐行注释.md)：45 条轨迹怎样可恢复采集；
4. [`convert_expert_episodes_to_lerobot.py.逐行注释.md`](convert_expert_episodes_to_lerobot.py.逐行注释.md)：训练数据如何构建；
5. [`compute_rm65_norm_stats.py.逐行注释.md`](compute_rm65_norm_stats.py.逐行注释.md)：如何按训练 transform 计算 norm stats；
6. [`rm65_training_config.py.逐行注释.md`](rm65_training_config.py.逐行注释.md)：transform、delta action 和 LoRA；
7. [`train_rm65_pi05.py.逐行注释.md`](train_rm65_pi05.py.逐行注释.md)：怎样调用 OpenPI 官方训练器；
8. [`validate_rm65_checkpoint.py.逐行注释.md`](validate_rm65_checkpoint.py.逐行注释.md)：checkpoint 离线冒烟；
9. [`serve_rm65_policy.py.逐行注释.md`](serve_rm65_policy.py.逐行注释.md)：checkpoint 怎样成为推理服务；
10. [`websocket_compat.py.逐行注释.md`](websocket_compat.py.逐行注释.md)：WebSocket 版本和 keepalive 兼容；
11. [`action_guard.py.逐行注释.md`](action_guard.py.逐行注释.md)：模型动作进入仿真前如何检查；
12. [`run_pick_place_baseline.py.逐行注释.md`](run_pick_place_baseline.py.逐行注释.md)：场景、IK、脚本专家、采集和 π0.5 闭环；
13. [`grasp_geometry.py.逐行注释.md`](grasp_geometry.py.逐行注释.md)：顶部抓取的坐标和旋转几何；
14. [`run_pi05_rm65_closed_loop.sh.逐行注释.md`](run_pi05_rm65_closed_loop.sh.逐行注释.md)：单次实验进程编排；
15. [`run_pi05_rm65_closed_loop_suite.py.逐行注释.md`](run_pi05_rm65_closed_loop_suite.py.逐行注释.md)：20 条可恢复评测；
16. [`closed_loop_report.py.逐行注释.md`](closed_loop_report.py.逐行注释.md)：独立验收逻辑；
17. [`check_closed_loop_task_report.py.逐行注释.md`](check_closed_loop_task_report.py.逐行注释.md)：把验收变成 Shell 退出码；
18. [`run_rm65_post_training_pipeline.sh.逐行注释.md`](run_rm65_post_training_pipeline.sh.逐行注释.md)：训练后完整流水线；
19. [`build_combined_urdf.py.逐行注释.md`](build_combined_urdf.py.逐行注释.md)：合并 RM65 与 4C2；
20. [`import_combined_urdf.py.逐行注释.md`](import_combined_urdf.py.逐行注释.md)：URDF 导入 USD。

## 怎样使用大文件注释

`run_pick_place_baseline.py` 有 2249 行。请按文件顶部的功能块地图跳转，不要第一遍从头顺读。推荐：

1. 第 602-881 行：π0.5 闭环；
2. 第 925-987 行：参数校验；
3. 第 1292-1576 行：场景创建和模式选择；
4. 第 1578-2058 行：脚本专家和成功指标；
5. 第 238-546 行：IK 连续性和数据采集；
6. 最后读报告字段。

## 注释详细程度示例

源码：

```python
actions = np.asarray(data["actions"])
```

语法层会解释：最里面的字符串是字典键；`data[...]` 的方括号按键取值；`np` 是 NumPy 别名，点号取 `asarray`，圆括号表示调用；等号最后保存返回值。项目层会解释：`data["actions"]` 是当前训练样本的未来 RM65 动作序列，每步由六个绝对关节目标和一个归一化 4C2 夹爪目标组成；完整一行把动作块统一为 `ndarray`，随后进行七维 shape 校验，再进入 delta-action 和训练 transform。

这是整套文档采用的标准。对于只有 `)`、`}` 的物理行，只能解释它闭合了哪一个结构；真正的数据语义会写在开始该表达式和各参数所在的行。

## 完整性证据

`manifest.json` 保存每个源文件的：

- 仓库相对路径；
- SHA-256；
- 原始行数；
- 注释文档行数。

Windows 教学工作区中的生成器是 `tools/generate_rm65_line_atlas.py`。它只读取快照并生成 Markdown，不会修改生产源码。
