# `build_combined_urdf.py` 逐行中文注释

> 这是学习副本，不参与项目运行。生产源码没有被插入注释或改写。

- 仓库路径：`projects/004-rm65-4c2-isaaclab/scripts/build_combined_urdf.py`
- 快照 SHA-256：`26f85a801b78ef9caa9df59510fe8fabe987feb822a09a675a1aaf679bf2317a`
- 总行数：305
- 程序作用：把原始 RM65 URDF 和用户提供的 4C2 URDF 合成一个机器人，修正网格路径、名字冲突、惯量和接触片，并输出可审计报告。
- 推荐读法：先读 main() 的 163-263 行掌握主流程，再回看前面的 XML 辅助函数。

## 功能块地图

- 第 1-12 行：解释器、模块说明与 XML/路径工具导入
- 第 13-17 行：把命令行里的 xyz/rpy 文本校验成三个浮点数
- 第 20-33 行：把 URDF 中的 mesh 路径改成绝对 file URI
- 第 36-65 行：给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名
- 第 68-107 行：修正 CAD 导出中过小或不稳定的质量和惯量
- 第 110-142 行：为 4C2 指尖增加用于稳定接触的薄盒碰撞片
- 第 145-160 行：把 joint 的父子关系、限位和 mimic 信息整理进报告
- 第 163-197 行：定义命令行接口
- 第 199-245 行：加载、校验和预处理两份 URDF
- 第 247-263 行：合并模型、添加 link_6 到夹爪的固定关节并写出 URDF
- 第 265-301 行：生成机器可读的模型合并证据
- 第 304-305 行：脚本入口

## 函数/类索引

- `parse_vector()`：第 13-17 行
- `rewrite_meshes()`：第 20-33 行
- `prefix_gripper_names()`：第 36-65 行
- `regularize_gripper_inertials()`：第 68-107 行
- `add_4c2_contact_pads()`：第 110-142 行
- `joint_record()`：第 145-160 行
- `main()`：第 163-301 行

## 逐行学习副本

每个 `【Lxxxx】` 注释解释紧随其后的原始行。解释会回答三个问题：这一行操作的项目对象是什么；Python/NumPy/Isaac/OpenPI 具体做了什么；结果流向哪个后续步骤。空行也保留，因为空行体现程序分段。

```python
# 【L0001】Linux 直接执行这个文件时，请操作系统用 `/usr/bin/env python3` 解释后面的源码；它决定这是 Python 还是 Bash 入口。
#!/usr/bin/env python3
# 【L0002】说明字符串 `Combine the RM65 arm and a gripper URDF without copying mesh assets.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
"""Combine the RM65 arm and a gripper URDF without copying mesh assets."""
# 【L0003】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0004】让 Python 暂缓解析类型标注；本项目中的 `Path | None`、自定义类等提示不会在模块导入时过早求值。
from __future__ import annotations
# 【L0005】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0006】从 `argparse` 引入 `argparse`。在这份程序里，`argparse` 用于标准库命令行解析器，让实验参数不必写死在代码里；后续出现这些名字时调用的是这里的外部能力。
import argparse
# 【L0007】从 `copy` 引入 `copy`。在这份程序里，`copy` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import copy
# 【L0008】从 `json` 引入 `json`。在这份程序里，`json` 用于读写人和程序都容易检查的 JSON 证据文件；后续出现这些名字时调用的是这里的外部能力。
import json
# 【L0009】从 `pathlib` 引入 `Path`。在这份程序里，`pathlib` 用于使用 Path 对象处理跨平台文件路径；后续出现这些名字时调用的是这里的外部能力。
from pathlib import Path
# 【L0010】从 `xml` 引入 `xml.etree.ElementTree as ET`。在这份程序里，`xml` 用于项目或第三方模块；后续出现这些名字时调用的是这里的外部能力。
import xml.etree.ElementTree as ET
# 【L0011】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0013】定义函数 `parse_vector(text: str, expected: int = 3)`；调用者把参数交给它完成“把命令行里的 xyz/rpy 文本校验成三个浮点数”，后面的缩进代码是具体实现。
def parse_vector(text: str, expected: int = 3) -> str:
# 【L0014】得到 `values`，它在本项目中表示本功能块中的 `values` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[float(value) for value in text.split()]`；`value` 表示本功能块中的 `value` 值；`text` 表示本功能块中的 `text` 值；`split` 表示本功能块中的 `split` 值。
    values = [float(value) for value in text.split()]
# 【L0015】判断 `len(values) != expected` 是否成立；`values` 表示本功能块中的 `values` 值；`expected` 表示本功能块中的 `expected` 值
    if len(values) != expected:
# 【L0016】主动抛出 `argparse.ArgumentTypeError(f"expected {expected} numbers, got {text!r}")` 并停止当前路径；说明当前输入违反“把命令行里的 xyz/rpy 文本校验成三个浮点数”要求，不能继续进入仿真、训练或评测。
        raise argparse.ArgumentTypeError(f"expected {expected} numbers, got {text!r}")
# 【L0017】结束当前函数并把 `" ".join(f"{value:.9g}" for value in values)` 交回调用者；这个值的含义是：计算表达式 `" ".join(f"{value:.9g}" for value in values)`；`join` 表示本功能块中的 `join` 值；`f` 表示本功能块中的 `f` 值；`value` 表示本功能块中的 `value` 值。
    return " ".join(f"{value:.9g}" for value in values)
# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】定义函数 `rewrite_meshes(robot: ET.Element, mesh_dir: Path)`；调用者把参数交给它完成“把 URDF 中的 mesh 路径改成绝对 file URI”，后面的缩进代码是具体实现。
def rewrite_meshes(robot: ET.Element, mesh_dir: Path) -> list[dict[str, str]]:
# 【L0021】得到 `records`，它在本项目中表示本功能块中的 `records` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    records: list[dict[str, str]] = []
# 【L0022】遍历 `robot.findall(".//mesh")`，每次把当前元素放进 `mesh`；这会逐个处理“把 URDF 中的 mesh 路径改成绝对 file URI”所需的帧、episode、动作或实验 case。
    for mesh in robot.findall(".//mesh"):
# 【L0023】得到 `original`，它在本项目中表示本功能块中的 `original` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `mesh.get("filename")`；`mesh` 表示本功能块中的 `mesh` 值；`get` 表示本功能块中的 `get` 值；`filename` 表示本功能块中的 `filename` 值。
        original = mesh.get("filename")
# 【L0024】判断 `not original` 是否成立；`original` 表示本功能块中的 `original` 值
        if not original:
# 【L0025】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“把 URDF 中的 mesh 路径改成绝对 file URI”中不满足继续条件。
            continue
# 【L0026】得到 `filename`，它在本项目中表示本功能块中的 `filename` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `Path(original.replace("\\", "/")).name`；`original` 表示本功能块中的 `original` 值；`replace` 表示本功能块中的 `replace` 值；`name` 表示本功能块中的 `name` 值。
        filename = Path(original.replace("\\", "/")).name
# 【L0027】得到 `resolved`，它在本项目中表示本功能块中的 `resolved` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `(mesh_dir / filename).resolve()`；`mesh_dir` 表示本功能块中的 `mesh_dir` 值；`filename` 表示本功能块中的 `filename` 值；`resolve` 表示本功能块中的 `resolve` 值。
        resolved = (mesh_dir / filename).resolve()
# 【L0028】判断 `not resolved.is_file()` 是否成立；`resolved` 表示本功能块中的 `resolved` 值；`is_file` 表示本功能块中的 `is_file` 值
        if not resolved.is_file():
# 【L0029】主动抛出 `FileNotFoundError(f"mesh referenced by URDF was not found: {resolved}")` 并停止当前路径；说明当前输入违反“把 URDF 中的 mesh 路径改成绝对 file URI”要求，不能继续进入仿真、训练或评测。
            raise FileNotFoundError(f"mesh referenced by URDF was not found: {resolved}")
# 【L0030】得到 `uri`，它在本项目中表示本功能块中的 `uri` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `resolved.as_uri()`；`resolved` 表示本功能块中的 `resolved` 值；`as_uri` 表示本功能块中的 `as_uri` 值。
        uri = resolved.as_uri()
# 【L0031】对 `mesh` 调用 `set("filename", uri)`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        mesh.set("filename", uri)
# 【L0032】对 `records` 执行 `append`，把 `{"original": original, "resolved": str(resolved), "uri": uri}` 加入已有结果；该集合表示本功能块中的 `records` 值，随后会用于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        records.append({"original": original, "resolved": str(resolved), "uri": uri})
# 【L0033】结束当前函数并把 `records` 交回调用者；这个值的含义是：计算表达式 `records`；`records` 表示本功能块中的 `records` 值。
    return records
# 【L0034】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0035】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0036】定义函数 `prefix_gripper_names(robot: ET.Element, prefix: str)`；调用者把参数交给它完成“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”，后面的缩进代码是具体实现。
def prefix_gripper_names(robot: ET.Element, prefix: str) -> tuple[dict[str, str], dict[str, str]]:
# 【L0037】得到 `link_map`，它在本项目中表示机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    link_map = {
# 【L0038】把表达式/参数 `link.get("name"): f"{prefix}{link.get('name')}"` 接入当前完整语句；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。在“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        link.get("name"): f"{prefix}{link.get('name')}"
# 【L0039】开始遍历 `for link in robot.findall("link")` 中给出的序列，逐项完成“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
        for link in robot.findall("link")
# 【L0040】判断 `link.get("name")` 是否成立；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值
        if link.get("name")
# 【L0041】结束或闭合当前语法结构；它属于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    }
# 【L0042】得到 `joint_map`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    joint_map = {
# 【L0043】把表达式/参数 `joint.get("name"): f"{prefix}{joint.get('name')}"` 接入当前完整语句；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。在“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
        joint.get("name"): f"{prefix}{joint.get('name')}"
# 【L0044】开始遍历 `for joint in robot.findall("joint")` 中给出的序列，逐项完成“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
        for joint in robot.findall("joint")
# 【L0045】判断 `joint.get("name")` 是否成立；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值
        if joint.get("name")
# 【L0046】结束或闭合当前语法结构；它属于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    }
# 【L0047】遍历 `robot.findall("link")`，每次把当前元素放进 `link`；这会逐个处理“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”所需的帧、episode、动作或实验 case。
    for link in robot.findall("link"):
# 【L0048】判断 `link.get("name") in link_map` 是否成立；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值
        if link.get("name") in link_map:
# 【L0049】对 `link` 调用 `set("name", link_map[link.get("name")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            link.set("name", link_map[link.get("name")])
# 【L0050】遍历 `robot.findall("joint")`，每次把当前元素放进 `joint`；这会逐个处理“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”所需的帧、episode、动作或实验 case。
    for joint in robot.findall("joint"):
# 【L0051】判断 `joint.get("name") in joint_map` 是否成立；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值
        if joint.get("name") in joint_map:
# 【L0052】对 `joint` 调用 `set("name", joint_map[joint.get("name")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            joint.set("name", joint_map[joint.get("name")])
# 【L0053】得到 `parent`，它在本项目中表示本功能块中的 `parent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("parent")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`parent` 表示本功能块中的 `parent` 值。
        parent = joint.find("parent")
# 【L0054】得到 `child`，它在本项目中表示本功能块中的 `child` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("child")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`child` 表示本功能块中的 `child` 值。
        child = joint.find("child")
# 【L0055】得到 `mimic`，它在本项目中表示本功能块中的 `mimic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("mimic")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`mimic` 表示本功能块中的 `mimic` 值。
        mimic = joint.find("mimic")
# 【L0056】检查 `parent is not None and parent.get("link") in link_map`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if parent is not None and parent.get("link") in link_map:
# 【L0057】对 `parent` 调用 `set("link", link_map[parent.get("link")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            parent.set("link", link_map[parent.get("link")])
# 【L0058】检查 `child is not None and child.get("link") in link_map`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if child is not None and child.get("link") in link_map:
# 【L0059】对 `child` 调用 `set("link", link_map[child.get("link")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            child.set("link", link_map[child.get("link")])
# 【L0060】检查 `mimic is not None and mimic.get("joint") in joint_map`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
        if mimic is not None and mimic.get("joint") in joint_map:
# 【L0061】对 `mimic` 调用 `set("joint", joint_map[mimic.get("joint")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            mimic.set("joint", joint_map[mimic.get("joint")])
# 【L0062】遍历 `robot.findall(".//transmission/joint")`，每次把当前元素放进 `transmission_joint`；这会逐个处理“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”所需的帧、episode、动作或实验 case。
    for transmission_joint in robot.findall(".//transmission/joint"):
# 【L0063】判断 `transmission_joint.get("name") in joint_map` 是否成立；`transmission_joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值
        if transmission_joint.get("name") in joint_map:
# 【L0064】对 `transmission_joint` 调用 `set("name", joint_map[transmission_joint.get("name")])`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
            transmission_joint.set("name", joint_map[transmission_joint.get("name")])
# 【L0065】结束当前函数并把 `link_map, joint_map` 交回调用者；这个值的含义是：计算表达式 `link_map, joint_map`；`link_map` 表示机器人连杆相关值；`joint_map` 表示关节相关值。
    return link_map, joint_map
# 【L0066】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0067】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0068】定义函数 `regularize_gripper_inertials(参数在后续行继续)`；调用者把参数交给它完成“修正 CAD 导出中过小或不稳定的质量和惯量”，后面的缩进代码是具体实现。
def regularize_gripper_inertials(
# 【L0069】声明/传入参数 `robot`，类型提示为 `ET.Element`；在本项目中它表示IsaacLab Articulation；表示有多个关节的 RM65+4C2。
    robot: ET.Element,
# 【L0070】声明/传入参数 `minimum_mass_kg`，类型提示为 `float`；在本项目中它表示本功能块中的 `minimum_mass_kg` 值。
    minimum_mass_kg: float,
# 【L0071】声明/传入参数 `minimum_diagonal_inertia`，类型提示为 `float`；在本项目中它表示为了 PhysX 稳定而允许的最小主对角惯量。
    minimum_diagonal_inertia: float,
# 【L0072】声明/传入参数 `zero_cross_inertia`，类型提示为 `bool`；在本项目中它表示本功能块中的 `zero_cross_inertia` 值。
    zero_cross_inertia: bool,
# 【L0073】以 `) -> list[dict[str, object]]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“修正 CAD 导出中过小或不稳定的质量和惯量”。
) -> list[dict[str, object]]:
# 【L0074】说明字符串 `Regularize tiny CAD-exported inertias for an explicitly labeled physics proxy.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Regularize tiny CAD-exported inertias for an explicitly labeled physics proxy."""
# 【L0075】空行：分隔“修正 CAD 导出中过小或不稳定的质量和惯量”中的逻辑段，让结构更容易看清。

# 【L0076】得到 `changes`，它在本项目中表示本功能块中的 `changes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    changes: list[dict[str, object]] = []
# 【L0077】遍历 `robot.findall("link")`，每次把当前元素放进 `link`；这会逐个处理“修正 CAD 导出中过小或不稳定的质量和惯量”所需的帧、episode、动作或实验 case。
    for link in robot.findall("link"):
# 【L0078】得到 `inertial`，它在本项目中表示本功能块中的 `inertial` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `link.find("inertial")`；`link` 表示机器人连杆相关值；`find` 表示本功能块中的 `find` 值；`inertial` 表示本功能块中的 `inertial` 值。
        inertial = link.find("inertial")
# 【L0079】检查 `inertial is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if inertial is None:
# 【L0080】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“修正 CAD 导出中过小或不稳定的质量和惯量”中不满足继续条件。
            continue
# 【L0081】得到 `mass`，它在本项目中表示本功能块中的 `mass` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `inertial.find("mass")`；`inertial` 表示本功能块中的 `inertial` 值；`find` 表示本功能块中的 `find` 值；`mass` 表示本功能块中的 `mass` 值。
        mass = inertial.find("mass")
# 【L0082】得到 `inertia`，它在本项目中表示本功能块中的 `inertia` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `inertial.find("inertia")`；`inertial` 表示本功能块中的 `inertial` 值；`find` 表示本功能块中的 `find` 值；`inertia` 表示本功能块中的 `inertia` 值。
        inertia = inertial.find("inertia")
# 【L0083】检查 `mass is None or inertia is None or mass.get("value") is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if mass is None or inertia is None or mass.get("value") is None:
# 【L0084】放弃当前元素剩余步骤，直接处理下一个候选/帧/episode；当前项在“修正 CAD 导出中过小或不稳定的质量和惯量”中不满足继续条件。
            continue
# 【L0085】得到 `before_mass`，它在本项目中表示本功能块中的 `before_mass` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `float(mass.get("value"))`；`mass` 表示本功能块中的 `mass` 值；`get` 表示本功能块中的 `get` 值；`value` 表示本功能块中的 `value` 值。
        before_mass = float(mass.get("value"))
# 【L0086】得到 `after_mass`，它在本项目中表示本功能块中的 `after_mass` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `max(before_mass, minimum_mass_kg)`；`before_mass` 表示本功能块中的 `before_mass` 值；`minimum_mass_kg` 表示本功能块中的 `minimum_mass_kg` 值。
        after_mass = max(before_mass, minimum_mass_kg)
# 【L0087】得到 `before_inertia`，它在本项目中表示本功能块中的 `before_inertia` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{name: float(inertia.get(name, "0")) for name in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")}`；`name` 表示本功能块中的 `name` 值；`inertia` 表示本功能块中的 `inertia` 值；`get` 表示本功能块中的 `get` 值。
        before_inertia = {name: float(inertia.get(name, "0")) for name in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")}
# 【L0088】得到 `after_inertia`，它在本项目中表示修正后的 URDF 惯量张量六个分量，最终会写回 XML；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：创建独立副本，避免后续原地修改同时改变作为参考的原数组/状态。
        after_inertia = before_inertia.copy()
# 【L0089】遍历 `("ixx", "iyy", "izz")`，每次把当前元素放进 `name`；这会逐个处理“修正 CAD 导出中过小或不稳定的质量和惯量”所需的帧、episode、动作或实验 case。
        for name in ("ixx", "iyy", "izz"):
# 【L0090】把右侧结果写进 `after_inertia[name]`（写入 `after_inertia[name]` 指定的字段）；右侧具体做的是：计算表达式 `max(after_inertia[name], minimum_diagonal_inertia)`；`after_inertia` 表示修正后的 URDF 惯量张量六个分量，最终会写回 XML；`name` 表示本功能块中的 `name` 值；`minimum_diagonal_inertia` 表示为了 PhysX 稳定而允许的最小主对角惯量。
            after_inertia[name] = max(after_inertia[name], minimum_diagonal_inertia)
# 【L0091】判断 `zero_cross_inertia` 是否成立；`zero_cross_inertia` 表示本功能块中的 `zero_cross_inertia` 值
        if zero_cross_inertia:
# 【L0092】遍历 `("ixy", "ixz", "iyz")`，每次把当前元素放进 `name`；这会逐个处理“修正 CAD 导出中过小或不稳定的质量和惯量”所需的帧、episode、动作或实验 case。
            for name in ("ixy", "ixz", "iyz"):
# 【L0093】把右侧结果写进 `after_inertia[name]`（写入 `after_inertia[name]` 指定的字段）；右侧具体做的是：把表达式 `0.0` 的结果保存下来，供当前功能块后续使用。
                after_inertia[name] = 0.0
# 【L0094】对 `mass` 调用 `set("value", f"{after_mass:.12g}")`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        mass.set("value", f"{after_mass:.12g}")
# 【L0095】遍历 `after_inertia.items()`，每次把当前元素放进 `name, value`；这会逐个处理“修正 CAD 导出中过小或不稳定的质量和惯量”所需的帧、episode、动作或实验 case。
        for name, value in after_inertia.items():
# 【L0096】对 `inertia` 调用 `set(name, f"{value:.12g}")`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
            inertia.set(name, f"{value:.12g}")
# 【L0097】判断 `after_mass != before_mass or after_inertia != before_inertia` 是否成立；`after_mass` 表示本功能块中的 `after_mass` 值；`before_mass` 表示本功能块中的 `before_mass` 值；`after_inertia` 表示修正后的 URDF 惯量张量六个分量，最终会写回 XML
        if after_mass != before_mass or after_inertia != before_inertia:
# 【L0098】开始对 `changes` 调用多行方法 `append`：把当前结果追加到已有列表末尾，保留后续汇总、筛选或落盘所需的顺序；具体参数写在随后几行，用于“修正 CAD 导出中过小或不稳定的质量和惯量”。
            changes.append(
# 【L0099】这是上一行尚未闭合的参数、数组或字典内容：`{`；其数据会并入上一行创建的对象，共同完成“修正 CAD 导出中过小或不稳定的质量和惯量”。
                {
# 【L0100】定义字典/JSON 字段 `link`，它表示“修正 CAD 导出中过小或不稳定的质量和惯量”中的 `link` 数据；字段值来自 `link.get("name")`，因此保存/传递的是这个表达式当前计算出的结果。
                    "link": link.get("name"),
# 【L0101】定义字典/JSON 字段 `mass_before_kg`，它表示“修正 CAD 导出中过小或不稳定的质量和惯量”中的 `mass_before_kg` 数据；字段值来自 `before_mass`，因此保存/传递的是这个表达式当前计算出的结果。
                    "mass_before_kg": before_mass,
# 【L0102】定义字典/JSON 字段 `mass_after_kg`，它表示“修正 CAD 导出中过小或不稳定的质量和惯量”中的 `mass_after_kg` 数据；字段值来自 `after_mass`，因此保存/传递的是这个表达式当前计算出的结果。
                    "mass_after_kg": after_mass,
# 【L0103】定义字典/JSON 字段 `inertia_before_kg_m2`，它表示“修正 CAD 导出中过小或不稳定的质量和惯量”中的 `inertia_before_kg_m2` 数据；字段值来自 `before_inertia`，因此保存/传递的是这个表达式当前计算出的结果。
                    "inertia_before_kg_m2": before_inertia,
# 【L0104】定义字典/JSON 字段 `inertia_after_kg_m2`，它表示“修正 CAD 导出中过小或不稳定的质量和惯量”中的 `inertia_after_kg_m2` 数据；字段值来自 `after_inertia`，因此保存/传递的是这个表达式当前计算出的结果。
                    "inertia_after_kg_m2": after_inertia,
# 【L0105】结束或闭合当前语法结构；它属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
                }
# 【L0106】结束或闭合当前语法结构；它属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
            )
# 【L0107】结束当前函数并把 `changes` 交回调用者；这个值的含义是：计算表达式 `changes`；`changes` 表示本功能块中的 `changes` 值。
    return changes
# 【L0108】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0109】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0110】定义函数 `add_4c2_contact_pads(参数在后续行继续)`；调用者把参数交给它完成“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”，后面的缩进代码是具体实现。
def add_4c2_contact_pads(
# 【L0111】把表达式/参数 `robot: ET.Element, prefix: str, pad_dimensions_m: tuple[float, float, float]` 接入当前完整语句；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2；`ET` 表示本功能块中的 `ET` 值；`Element` 表示本功能块中的 `Element` 值。在“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中，这些值会被外层函数、公式或容器继续消费，而不是单独成为一次控制命令。
    robot: ET.Element, prefix: str, pad_dimensions_m: tuple[float, float, float]
# 【L0112】以 `) -> list[dict[str, str]]:` 开始一个新的缩进代码块或键值结构；接下来的缩进行共同实现“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
) -> list[dict[str, str]]:
# 【L0113】说明字符串 `Add thin box colliders at empirically derived left/right grasp surfaces.`：记录当前模块、类或函数在 RM65 流程里的公开职责，`help()` 也能读取它。
    """Add thin box colliders at empirically derived left/right grasp surfaces.
# 【L0114】继续说明字符串，原文是 ``；这段文字在解释“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。

# 【L0115】继续说明字符串，原文是 `The poses are expressed in each second-finger link frame.  They were`；这段文字在解释“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    The poses are expressed in each second-finger link frame.  They were
# 【L0116】继续说明字符串，原文是 `back-projected from a centered 40 mm block at the validated 0.65 rad`；这段文字在解释“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    back-projected from a centered 40 mm block at the validated 0.65 rad
# 【L0117】继续说明字符串，原文是 `closing pose, with 2 mm of intended compression per side.`；这段文字在解释“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    closing pose, with 2 mm of intended compression per side.
# 【L0118】继续说明字符串，原文是 ``；这段文字在解释“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的设计原因、输入合同或限制，它只帮助读者和 `help()`，不会在运行时控制机械臂。
    """
# 【L0119】空行：分隔“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的逻辑段，让结构更容易看清。

# 【L0120】得到 `pad_size`，它在本项目中表示本功能块中的 `pad_size` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `" ".join(f"{value:.9g}" for value in pad_dimensions_m)`；`join` 表示本功能块中的 `join` 值；`f` 表示本功能块中的 `f` 值；`value` 表示本功能块中的 `value` 值。
    pad_size = " ".join(f"{value:.9g}" for value in pad_dimensions_m)
# 【L0121】得到 `specs`，它在本项目中表示本功能块中的 `specs` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    specs = {
# 【L0122】定义字典/JSON 字段 `f"{prefix}l_2`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `f"{prefix}l_2` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        f"{prefix}l_2": {
# 【L0123】定义字典/JSON 字段 `xyz`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `xyz` 数据；字段值来自 `"0.027286683 0.013343694 -0.072958842"`，因此保存/传递的是这个表达式当前计算出的结果。
            "xyz": "0.027286683 0.013343694 -0.072958842",
# 【L0124】定义字典/JSON 字段 `rpy`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `rpy` 数据；字段值来自 `"0.005034454 0.254940134 0.652909860"`，因此保存/传递的是这个表达式当前计算出的结果。
            "rpy": "0.005034454 0.254940134 0.652909860",
# 【L0125】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        },
# 【L0126】定义字典/JSON 字段 `f"{prefix}r_2`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `f"{prefix}r_2` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        f"{prefix}r_2": {
# 【L0127】定义字典/JSON 字段 `xyz`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `xyz` 数据；字段值来自 `"0.028775714 -0.011597111 -0.073257379"`，因此保存/传递的是这个表达式当前计算出的结果。
            "xyz": "0.028775714 -0.011597111 -0.073257379",
# 【L0128】定义字典/JSON 字段 `rpy`，它表示“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的 `rpy` 数据；字段值来自 `"0.005034429 0.254940104 -0.644663208"`，因此保存/传递的是这个表达式当前计算出的结果。
            "rpy": "0.005034429 0.254940104 -0.644663208",
# 【L0129】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        },
# 【L0130】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    }
# 【L0131】得到 `links`，它在本项目中表示本功能块中的 `links` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{link.get("name"): link for link in robot.findall("link")}`；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    links = {link.get("name"): link for link in robot.findall("link")}
# 【L0132】得到 `records`，它在本项目中表示本功能块中的 `records` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `[]` 的结果保存下来，供当前功能块后续使用。
    records: list[dict[str, str]] = []
# 【L0133】遍历 `specs.items()`，每次把当前元素放进 `link_name, pose`；这会逐个处理“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”所需的帧、episode、动作或实验 case。
    for link_name, pose in specs.items():
# 【L0134】得到 `link`，它在本项目中表示机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `links.get(link_name)`；`links` 表示本功能块中的 `links` 值；`get` 表示本功能块中的 `get` 值；`link_name` 表示机器人连杆相关值。
        link = links.get(link_name)
# 【L0135】检查 `link is None`，也就是所需对象/结果是否还没有创建或求解失败；成立时进入缺失处理
        if link is None:
# 【L0136】主动抛出 `ValueError(f"cannot add 4C2 contact pad: missing link {link_name!r}")` 并停止当前路径；说明当前输入违反“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”要求，不能继续进入仿真、训练或评测。
            raise ValueError(f"cannot add 4C2 contact pad: missing link {link_name!r}")
# 【L0137】得到 `collision`，它在本项目中表示新增到指尖 link 的接触碰撞体 XML 节点；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ET.SubElement(link, "collision", {"name": "contact_pad_box"})`；`ET` 表示本功能块中的 `ET` 值；`SubElement` 表示本功能块中的 `SubElement` 值；`link` 表示机器人连杆相关值。
        collision = ET.SubElement(link, "collision", {"name": "contact_pad_box"})
# 【L0138】用 `xml.etree.ElementTree.SubElement` 在父 XML 节点下新建 `origin` 子节点；参数 `collision, "origin", {"xyz": pose["xyz"], "rpy": pose["rpy"]}` 同时写入它的属性。该节点会进入最终 RM65+4C2 URDF，用于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        ET.SubElement(collision, "origin", {"xyz": pose["xyz"], "rpy": pose["rpy"]})
# 【L0139】得到 `geometry`，它在本项目中表示碰撞体所使用的 box 几何 XML 节点；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ET.SubElement(collision, "geometry")`；`ET` 表示本功能块中的 `ET` 值；`SubElement` 表示本功能块中的 `SubElement` 值；`collision` 表示新增到指尖 link 的接触碰撞体 XML 节点。
        geometry = ET.SubElement(collision, "geometry")
# 【L0140】用 `xml.etree.ElementTree.SubElement` 在父 XML 节点下新建 `box` 子节点；参数 `geometry, "box", {"size": pad_size}` 同时写入它的属性。该节点会进入最终 RM65+4C2 URDF，用于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        ET.SubElement(geometry, "box", {"size": pad_size})
# 【L0141】对 `records` 执行 `append`，把 `{"link": link_name, "xyz": pose["xyz"], "rpy": pose["rpy"], "size": pad_size}` 加入已有结果；该集合表示本功能块中的 `records` 值，随后会用于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        records.append({"link": link_name, "xyz": pose["xyz"], "rpy": pose["rpy"], "size": pad_size})
# 【L0142】结束当前函数并把 `records` 交回调用者；这个值的含义是：计算表达式 `records`；`records` 表示本功能块中的 `records` 值。
    return records
# 【L0143】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0144】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0145】定义函数 `joint_record(joint: ET.Element)`；调用者把参数交给它完成“把 joint 的父子关系、限位和 mimic 信息整理进报告”，后面的缩进代码是具体实现。
def joint_record(joint: ET.Element) -> dict[str, object]:
# 【L0146】得到 `limit`，它在本项目中表示本功能块中的 `limit` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("limit")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`limit` 表示本功能块中的 `limit` 值。
    limit = joint.find("limit")
# 【L0147】得到 `parent`，它在本项目中表示本功能块中的 `parent` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("parent")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`parent` 表示本功能块中的 `parent` 值。
    parent = joint.find("parent")
# 【L0148】得到 `child`，它在本项目中表示本功能块中的 `child` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("child")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`child` 表示本功能块中的 `child` 值。
    child = joint.find("child")
# 【L0149】得到 `mimic`，它在本项目中表示本功能块中的 `mimic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("mimic")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`mimic` 表示本功能块中的 `mimic` 值。
    mimic = joint.find("mimic")
# 【L0150】结束当前函数并把 `{` 交回调用者；这个值的含义是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    return {
# 【L0151】定义字典/JSON 字段 `name`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `name` 数据；字段值来自 `joint.get("name")`，因此保存/传递的是这个表达式当前计算出的结果。
        "name": joint.get("name"),
# 【L0152】定义字典/JSON 字段 `type`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `type` 数据；字段值来自 `joint.get("type")`，因此保存/传递的是这个表达式当前计算出的结果。
        "type": joint.get("type"),
# 【L0153】定义字典/JSON 字段 `parent`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `parent` 数据；字段值来自 `None if parent is None else parent.get("link")`，因此保存/传递的是这个表达式当前计算出的结果。
        "parent": None if parent is None else parent.get("link"),
# 【L0154】定义字典/JSON 字段 `child`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `child` 数据；字段值来自 `None if child is None else child.get("link")`，因此保存/传递的是这个表达式当前计算出的结果。
        "child": None if child is None else child.get("link"),
# 【L0155】定义字典/JSON 字段 `lower`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `lower` 数据；字段值来自 `None if limit is None or limit.get("lower") is None else float(limit.get("lower"))`，因此保存/传递的是这个表达式当前计算出的结果。
        "lower": None if limit is None or limit.get("lower") is None else float(limit.get("lower")),
# 【L0156】定义字典/JSON 字段 `upper`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `upper` 数据；字段值来自 `None if limit is None or limit.get("upper") is None else float(limit.get("upper"))`，因此保存/传递的是这个表达式当前计算出的结果。
        "upper": None if limit is None or limit.get("upper") is None else float(limit.get("upper")),
# 【L0157】定义字典/JSON 字段 `mimic_joint`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `mimic_joint` 数据；字段值来自 `None if mimic is None else mimic.get("joint")`，因此保存/传递的是这个表达式当前计算出的结果。
        "mimic_joint": None if mimic is None else mimic.get("joint"),
# 【L0158】定义字典/JSON 字段 `mimic_multiplier`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `mimic_multiplier` 数据；字段值来自 `None if mimic is None else float(mimic.get("multiplier", "1"))`，因此保存/传递的是这个表达式当前计算出的结果。
        "mimic_multiplier": None if mimic is None else float(mimic.get("multiplier", "1")),
# 【L0159】定义字典/JSON 字段 `mimic_offset`，它表示“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的 `mimic_offset` 数据；字段值来自 `None if mimic is None else float(mimic.get("offset", "0"))`，因此保存/传递的是这个表达式当前计算出的结果。
        "mimic_offset": None if mimic is None else float(mimic.get("offset", "0")),
# 【L0160】结束或闭合当前语法结构；它属于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    }
# 【L0161】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0162】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0163】定义函数 `main()`；调用者把参数交给它完成“定义命令行接口”，后面的缩进代码是具体实现。
def main() -> None:
# 【L0164】得到 `parser`，它在本项目中表示本功能块中的 `parser` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `argparse.ArgumentParser(description=__doc__)`；`argparse` 表示本功能块中的 `argparse` 值；`ArgumentParser` 表示本功能块中的 `ArgumentParser` 值；`description` 表示Lula 将规划关节组和末端 link 映射到 URDF 的 robot description YAML。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0165】声明命令行参数 `--rm65-urdf`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--rm65-urdf", type=Path, required=True)
# 【L0166】声明命令行参数 `--rm65-mesh-dir`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--rm65-mesh-dir", type=Path, required=True)
# 【L0167】声明命令行参数 `--gripper-urdf`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-urdf", type=Path, required=True)
# 【L0168】声明命令行参数 `--gripper-mesh-dir`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-mesh-dir", type=Path, required=True)
# 【L0169】声明命令行参数 `--gripper-root-link`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-root-link", default="base_link")
# 【L0170】声明命令行参数 `--gripper-name-prefix`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-name-prefix", default="tool_")
# 【L0171】声明命令行参数 `--output`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--output", type=Path, required=True)
# 【L0172】声明命令行参数 `--report`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--report", type=Path)
# 【L0173】声明命令行参数 `--mount-xyz`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--mount-xyz", type=parse_vector, default="0 0 0")
# 【L0174】声明命令行参数 `--mount-rpy`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--mount-rpy", type=parse_vector, default="0 0 0")
# 【L0175】声明命令行参数 `--gripper-min-mass-kg`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-min-mass-kg", type=float, default=0.0)
# 【L0176】声明命令行参数 `--gripper-min-diagonal-inertia`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--gripper-min-diagonal-inertia", type=float, default=0.0)
# 【L0177】声明命令行参数 `--zero-gripper-cross-inertia`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument("--zero-gripper-cross-inertia", action="store_true")
# 【L0178】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0179】提供文本片段 `"--add-4c2-contact-pads"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“定义命令行接口”中的帮助说明、错误原因、任务名称或报告文字。
        "--add-4c2-contact-pads",
# 【L0180】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“定义命令行接口”。
        action="store_true",
# 【L0181】给上一层函数/配置构造器的命名参数 `help` 传入 `"Add two thin, box-shaped collision pads for bilateral grasp diagnostics."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“定义命令行接口”。
        help="Add two thin, box-shaped collision pads for bilateral grasp diagnostics.",
# 【L0182】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0183】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0184】提供文本片段 `"--4c2-contact-pad-size-m"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“定义命令行接口”中的帮助说明、错误原因、任务名称或报告文字。
        "--4c2-contact-pad-size-m",
# 【L0185】给上一层函数/配置构造器的命名参数 `dest` 传入 `"contact_pad_size_m"`；该参数在本项目中表示本功能块中的 `dest` 值，会参与“定义命令行接口”。
        dest="contact_pad_size_m",
# 【L0186】给上一层函数/配置构造器的命名参数 `type` 传入 `float`；该参数在本项目中表示本功能块中的 `type` 值，会参与“定义命令行接口”。
        type=float,
# 【L0187】给上一层函数/配置构造器的命名参数 `nargs` 传入 `3`；该参数在本项目中表示本功能块中的 `nargs` 值，会参与“定义命令行接口”。
        nargs=3,
# 【L0188】给上一层函数/配置构造器的命名参数 `metavar` 传入 `("X", "Y", "Z")`；该参数在本项目中表示本功能块中的 `metavar` 值，会参与“定义命令行接口”。
        metavar=("X", "Y", "Z"),
# 【L0189】给上一层函数/配置构造器的命名参数 `default` 传入 `(0.025, 0.010, 0.020)`；该参数在本项目中表示本功能块中的 `default` 值，会参与“定义命令行接口”。
        default=(0.025, 0.010, 0.020),
# 【L0190】给上一层函数/配置构造器的命名参数 `help` 传入 `"Box dimensions in each second-finger link frame (default: 0.025 0.010 0.020)."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“定义命令行接口”。
        help="Box dimensions in each second-finger link frame (default: 0.025 0.010 0.020).",
# 【L0191】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0192】声明命令行参数 `parser.add_argument(`；启动脚本可用它改变“定义命令行接口”的配置，最终参数也会写入证据便于复现。
    parser.add_argument(
# 【L0193】提供文本片段 `"--preserve-mimic"`；Python 会把相邻字符串自动拼接，外层参数会把它用作“定义命令行接口”中的帮助说明、错误原因、任务名称或报告文字。
        "--preserve-mimic",
# 【L0194】给上一层函数/配置构造器的命名参数 `action` 传入 `"store_true"`；该参数在本项目中表示动作相关值，会参与“定义命令行接口”。
        action="store_true",
# 【L0195】给上一层函数/配置构造器的命名参数 `help` 传入 `"Keep source mimic tags. The default strips them for stable software-coupled drives in PhysX."`；该参数在本项目中表示本功能块中的 `help` 值，会参与“定义命令行接口”。
        help="Keep source mimic tags. The default strips them for stable software-coupled drives in PhysX.",
# 【L0196】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0197】得到 `args`，它在本项目中表示解析后的命令行参数集合；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `parser.parse_args()`；`parser` 表示本功能块中的 `parser` 值；`parse_args` 表示本功能块中的 `parse_args` 值。
    args = parser.parse_args()
# 【L0198】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0199】得到 `arm_tree`，它在本项目中表示合并并修正后的整棵 RM65+4C2 URDF XML 树；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ET.parse(args.rm65_urdf.expanduser())`；`ET` 表示本功能块中的 `ET` 值；`parse` 表示本功能块中的 `parse` 值；`rm65_urdf` 表示本功能块中的 `rm65_urdf` 值。
    arm_tree = ET.parse(args.rm65_urdf.expanduser())
# 【L0200】得到 `gripper_tree`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ET.parse(args.gripper_urdf.expanduser())`；`ET` 表示本功能块中的 `ET` 值；`parse` 表示本功能块中的 `parse` 值；`gripper_urdf` 表示夹爪相关值。
    gripper_tree = ET.parse(args.gripper_urdf.expanduser())
# 【L0201】得到 `arm`，它在本项目中表示本功能块中的 `arm` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arm_tree.getroot()`；`arm_tree` 表示合并并修正后的整棵 RM65+4C2 URDF XML 树；`getroot` 表示本功能块中的 `getroot` 值。
    arm = arm_tree.getroot()
# 【L0202】得到 `gripper`，它在本项目中表示一个归一化夹爪值组成的一维数组；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `gripper_tree.getroot()`；`gripper_tree` 表示夹爪相关值；`getroot` 表示本功能块中的 `getroot` 值。
    gripper = gripper_tree.getroot()
# 【L0203】判断 `arm.tag != "robot" or gripper.tag != "robot"` 是否成立；`arm` 表示本功能块中的 `arm` 值；`tag` 表示本功能块中的 `tag` 值；`robot` 表示IsaacLab Articulation；表示有多个关节的 RM65+4C2
    if arm.tag != "robot" or gripper.tag != "robot":
# 【L0204】主动抛出 `ValueError("both input files must have a <robot> root")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError("both input files must have a <robot> root")
# 【L0205】空行：分隔“加载、校验和预处理两份 URDF”中的逻辑段，让结构更容易看清。

# 【L0206】得到 `original_gripper_links`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{link.get("name") for link in gripper.findall("link")}`；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    original_gripper_links = {link.get("name") for link in gripper.findall("link")}
# 【L0207】判断 `args.gripper_root_link not in original_gripper_links` 是否成立；`gripper_root_link` 表示夹爪、机器人连杆相关值；`original_gripper_links` 表示夹爪相关值
    if args.gripper_root_link not in original_gripper_links:
# 【L0208】主动抛出 `ValueError(f"gripper URDF must contain root link {args.gripper_root_link!r}")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"gripper URDF must contain root link {args.gripper_root_link!r}")
# 【L0209】得到 `gripper_meshes`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rewrite_meshes(gripper, args.gripper_mesh_dir.expanduser())`；`rewrite_meshes` 表示本功能块中的 `rewrite_meshes` 值；`gripper` 表示一个归一化夹爪值组成的一维数组；`gripper_mesh_dir` 表示夹爪相关值。
    gripper_meshes = rewrite_meshes(gripper, args.gripper_mesh_dir.expanduser())
# 【L0210】把右侧返回的多个结果按位置拆给 `link_map, joint_map`；`link_map` 表示机器人连杆相关值；`joint_map` 表示关节相关值。右侧的来源是：计算表达式 `prefix_gripper_names(gripper, args.gripper_name_prefix)`；`prefix_gripper_names` 表示夹爪相关值；`gripper` 表示一个归一化夹爪值组成的一维数组；`gripper_name_prefix` 表示夹爪相关值。
    link_map, joint_map = prefix_gripper_names(gripper, args.gripper_name_prefix)
# 【L0211】判断 `args.gripper_min_mass_kg < 0 or args.gripper_min_diagonal_inertia < 0` 是否成立；`gripper_min_mass_kg` 表示夹爪相关值；`gripper_min_diagonal_inertia` 表示夹爪相关值
    if args.gripper_min_mass_kg < 0 or args.gripper_min_diagonal_inertia < 0:
# 【L0212】主动抛出 `ValueError("gripper mass and inertia floors must be non-negative")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError("gripper mass and inertia floors must be non-negative")
# 【L0213】判断 `any(value <= 0.0 for value in args.contact_pad_size_m)` 是否成立；`any` 表示本功能块中的 `any` 值；`value` 表示本功能块中的 `value` 值；`contact_pad_size_m` 表示接触相关值
    if any(value <= 0.0 for value in args.contact_pad_size_m):
# 【L0214】主动抛出 `ValueError("4C2 contact-pad dimensions must be positive")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError("4C2 contact-pad dimensions must be positive")
# 【L0215】得到 `inertial_changes`，它在本项目中表示本功能块中的 `inertial_changes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `regularize_gripper_inertials(`；`regularize_gripper_inertials` 表示夹爪相关值。
    inertial_changes = regularize_gripper_inertials(
# 【L0216】声明/传入参数 `gripper`；在本项目中它表示一个归一化夹爪值组成的一维数组。
        gripper,
# 【L0217】向上一行的函数调用或容器继续传入 `args.gripper_min_mass_kg`；`gripper_min_mass_kg` 表示夹爪相关值，它参与“加载、校验和预处理两份 URDF”。
        args.gripper_min_mass_kg,
# 【L0218】向上一行的函数调用或容器继续传入 `args.gripper_min_diagonal_inertia`；`gripper_min_diagonal_inertia` 表示夹爪相关值，它参与“加载、校验和预处理两份 URDF”。
        args.gripper_min_diagonal_inertia,
# 【L0219】向上一行的函数调用或容器继续传入 `args.zero_gripper_cross_inertia`；`zero_gripper_cross_inertia` 表示夹爪相关值，它参与“加载、校验和预处理两份 URDF”。
        args.zero_gripper_cross_inertia,
# 【L0220】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0221】得到 `contact_pads`，它在本项目中表示接触相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `(` 的结果保存下来，供当前功能块后续使用。
    contact_pads = (
# 【L0222】调用 `add_4c2_contact_pads(gripper, args.gripper_name_prefix, tuple(args.contact_pad_size_m))`：在 4C2 指尖 link 中加入薄盒碰撞片，使闭合后能稳定夹住 40 mm 方块。它的结果/修改用于“加载、校验和预处理两份 URDF”。
        add_4c2_contact_pads(gripper, args.gripper_name_prefix, tuple(args.contact_pad_size_m))
# 【L0223】判断 `args.add_4c2_contact_pads` 是否成立；`add_4c2_contact_pads` 表示接触相关值
        if args.add_4c2_contact_pads
# 【L0224】这是上一行条件表达式的备用值：条件不成立时使用 `[]`；它让“加载、校验和预处理两份 URDF”在可选数据缺失时仍有明确结果。
        else []
# 【L0225】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0226】得到 `gripper_root_link`，它在本项目中表示夹爪、机器人连杆相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `link_map[args.gripper_root_link]`；`link_map` 表示机器人连杆相关值；`gripper_root_link` 表示夹爪、机器人连杆相关值。
    gripper_root_link = link_map[args.gripper_root_link]
# 【L0227】得到 `source_mimic_follower_joints`，它在本项目中表示源位置、关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sorted(`；`sorted` 表示本功能块中的 `sorted` 值。
    source_mimic_follower_joints = sorted(
# 【L0228】这是生成式/推导式 `joint.get("name") for joint in gripper.findall("joint") if joint.find("mimic") is not None`：逐个遍历 `in` 后的集合，只产生符合条件的元素；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。产生的序列交给外层列表、字典或函数完成“加载、校验和预处理两份 URDF”。
        joint.get("name") for joint in gripper.findall("joint") if joint.find("mimic") is not None
# 【L0229】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0230】判断 `not args.preserve_mimic` 是否成立；`preserve_mimic` 表示本功能块中的 `preserve_mimic` 值
    if not args.preserve_mimic:
# 【L0231】遍历 `gripper.findall("joint")`，每次把当前元素放进 `joint`；这会逐个处理“加载、校验和预处理两份 URDF”所需的帧、episode、动作或实验 case。
        for joint in gripper.findall("joint"):
# 【L0232】得到 `mimic`，它在本项目中表示本功能块中的 `mimic` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `joint.find("mimic")`；`joint` 表示关节相关值；`find` 表示本功能块中的 `find` 值；`mimic` 表示本功能块中的 `mimic` 值。
            mimic = joint.find("mimic")
# 【L0233】检查 `mimic is not None`；只有该可选对象已经存在时才执行对应采集、保存或处理逻辑
            if mimic is not None:
# 【L0234】对 `joint` 调用 `remove(mimic)`：从 XML/列表移除指定对象；生成的 URDF 或数据将不再包含它。本行产生的修改/返回值服务于“加载、校验和预处理两份 URDF”。
                joint.remove(mimic)
# 【L0235】空行：分隔“加载、校验和预处理两份 URDF”中的逻辑段，让结构更容易看清。

# 【L0236】得到 `arm_links`，它在本项目中表示本功能块中的 `arm_links` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{link.get("name") for link in arm.findall("link")}`；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    arm_links = {link.get("name") for link in arm.findall("link")}
# 【L0237】得到 `gripper_links`，它在本项目中表示夹爪相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{link.get("name") for link in gripper.findall("link")}`；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    gripper_links = {link.get("name") for link in gripper.findall("link")}
# 【L0238】得到 `arm_joints`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{joint.get("name") for joint in arm.findall("joint")}`；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    arm_joints = {joint.get("name") for joint in arm.findall("joint")}
# 【L0239】得到 `gripper_joints`，它在本项目中表示夹爪、关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `{joint.get("name") for joint in gripper.findall("joint")}`；`joint` 表示关节相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    gripper_joints = {joint.get("name") for joint in gripper.findall("joint")}
# 【L0240】得到 `duplicate_links`，它在本项目中表示本功能块中的 `duplicate_links` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sorted(arm_links & gripper_links)`；`sorted` 表示本功能块中的 `sorted` 值；`arm_links` 表示本功能块中的 `arm_links` 值；`gripper_links` 表示夹爪相关值。
    duplicate_links = sorted(arm_links & gripper_links)
# 【L0241】得到 `duplicate_joints`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `sorted(arm_joints & gripper_joints)`；`sorted` 表示本功能块中的 `sorted` 值；`arm_joints` 表示关节相关值；`gripper_joints` 表示夹爪、关节相关值。
    duplicate_joints = sorted(arm_joints & gripper_joints)
# 【L0242】判断 `duplicate_links or duplicate_joints` 是否成立；`duplicate_links` 表示本功能块中的 `duplicate_links` 值；`duplicate_joints` 表示关节相关值
    if duplicate_links or duplicate_joints:
# 【L0243】主动抛出 `ValueError(f"duplicate names: links={duplicate_links}, joints={duplicate_joints}")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError(f"duplicate names: links={duplicate_links}, joints={duplicate_joints}")
# 【L0244】判断 `"link_6" not in arm_links` 是否成立；`link_6` 表示机器人连杆相关值；`arm_links` 表示本功能块中的 `arm_links` 值
    if "link_6" not in arm_links:
# 【L0245】主动抛出 `ValueError("RM65 URDF must contain end link 'link_6'")` 并停止当前路径；说明当前输入违反“加载、校验和预处理两份 URDF”要求，不能继续进入仿真、训练或评测。
        raise ValueError("RM65 URDF must contain end link 'link_6'")
# 【L0246】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0247】得到 `arm_meshes`，它在本项目中表示本功能块中的 `arm_meshes` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `rewrite_meshes(arm, args.rm65_mesh_dir.expanduser())`；`rewrite_meshes` 表示本功能块中的 `rewrite_meshes` 值；`arm` 表示本功能块中的 `arm` 值；`rm65_mesh_dir` 表示本功能块中的 `rm65_mesh_dir` 值。
    arm_meshes = rewrite_meshes(arm, args.rm65_mesh_dir.expanduser())
# 【L0248】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0249】遍历 `list(gripper)`，每次把当前元素放进 `child`；这会逐个处理“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”所需的帧、episode、动作或实验 case。
    for child in list(gripper):
# 【L0250】判断 `child.tag in {"link", "joint", "gazebo", "transmission", "material"}` 是否成立；`child` 表示本功能块中的 `child` 值；`tag` 表示本功能块中的 `tag` 值；`link` 表示机器人连杆相关值
        if child.tag in {"link", "joint", "gazebo", "transmission", "material"}:
# 【L0251】对 `arm` 执行 `append`，把 `copy.deepcopy(child)` 加入已有结果；该集合表示本功能块中的 `arm` 值，随后会用于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
            arm.append(copy.deepcopy(child))
# 【L0252】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0253】得到 `mount`，它在本项目中表示连接 RM65 link_6 与 4C2 根 link 的固定关节 XML 节点；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `ET.Element("joint", {"name": "rm65_to_4c2", "type": "fixed"})`；`ET` 表示本功能块中的 `ET` 值；`Element` 表示本功能块中的 `Element` 值；`joint` 表示关节相关值。
    mount = ET.Element("joint", {"name": "rm65_to_4c2", "type": "fixed"})
# 【L0254】用 `xml.etree.ElementTree.SubElement` 在父 XML 节点下新建 `origin` 子节点；参数 `mount, "origin", {"xyz": args.mount_xyz, "rpy": args.mount_rpy}` 同时写入它的属性。该节点会进入最终 RM65+4C2 URDF，用于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    ET.SubElement(mount, "origin", {"xyz": args.mount_xyz, "rpy": args.mount_rpy})
# 【L0255】用 `xml.etree.ElementTree.SubElement` 在父 XML 节点下新建 `parent` 子节点；参数 `mount, "parent", {"link": "link_6"}` 同时写入它的属性。该节点会进入最终 RM65+4C2 URDF，用于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    ET.SubElement(mount, "parent", {"link": "link_6"})
# 【L0256】用 `xml.etree.ElementTree.SubElement` 在父 XML 节点下新建 `child` 子节点；参数 `mount, "child", {"link": gripper_root_link}` 同时写入它的属性。该节点会进入最终 RM65+4C2 URDF，用于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    ET.SubElement(mount, "child", {"link": gripper_root_link})
# 【L0257】对 `arm` 执行 `append`，把 `mount` 加入已有结果；该集合表示本功能块中的 `arm` 值，随后会用于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    arm.append(mount)
# 【L0258】对 `arm` 调用 `set("name", "rm65_4c2")`：修改 XML/配置对象的指定属性；在 URDF 构建中会直接改变最终写出的机器人描述。本行产生的修改/返回值服务于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    arm.set("name", "rm65_4c2")
# 【L0259】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0260】对 `ET` 调用 `indent(arm_tree, space="  ")`：调用 `ET` 提供的 `indent` 操作。本行产生的修改/返回值服务于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    ET.indent(arm_tree, space="  ")
# 【L0261】得到 `output`，它在本项目中表示输出文件路径；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.output.expanduser().resolve()`；`output` 表示输出文件路径；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
    output = args.output.expanduser().resolve()
# 【L0262】调用 `mkdir`：创建目录；本行实际操作 `output.parent.mkdir(parents=True, exist_ok=True)`。`output` 表示输出文件路径；`parent` 表示本功能块中的 `parent` 值。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L0263】对 `arm_tree` 调用 `write(output, encoding="utf-8", xml_declaration=True)`：把内存中的 XML/数据写到磁盘，形成下游可以加载的文件。本行产生的修改/返回值服务于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    arm_tree.write(output, encoding="utf-8", xml_declaration=True)
# 【L0264】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0265】得到 `combined_links`，它在本项目中表示本功能块中的 `combined_links` 值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `[link.get("name") for link in arm.findall("link")]`；`link` 表示机器人连杆相关值；`get` 表示本功能块中的 `get` 值；`name` 表示本功能块中的 `name` 值。
    combined_links = [link.get("name") for link in arm.findall("link")]
# 【L0266】得到 `combined_joint_elements`，它在本项目中表示关节相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `arm.findall("joint")`；`arm` 表示本功能块中的 `arm` 值；`findall` 表示本功能块中的 `findall` 值；`joint` 表示关节相关值。
    combined_joint_elements = arm.findall("joint")
# 【L0267】得到 `report`，它在本项目中表示机器可读实验报告字典；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：把表达式 `{` 的结果保存下来，供当前功能块后续使用。
    report = {
# 【L0268】定义字典/JSON 字段 `robot_name`，它表示“生成机器可读的模型合并证据”中的 `robot_name` 数据；字段值来自 `arm.get("name")`，因此保存/传递的是这个表达式当前计算出的结果。
        "robot_name": arm.get("name"),
# 【L0269】定义字典/JSON 字段 `output_urdf`，它表示“生成机器可读的模型合并证据”中的 `output_urdf` 数据；字段值来自 `str(output)`，因此保存/传递的是这个表达式当前计算出的结果。
        "output_urdf": str(output),
# 【L0270】定义字典/JSON 字段 `mount`，它表示“生成机器可读的模型合并证据”中的 `mount` 数据；字段值来自 `{"parent": "link_6", "child": gripper_root_link, "xyz": args.mount_xyz, "rpy": args.mount_rpy}`，因此保存/传递的是这个表达式当前计算出的结果。
        "mount": {"parent": "link_6", "child": gripper_root_link, "xyz": args.mount_xyz, "rpy": args.mount_rpy},
# 【L0271】定义字典/JSON 字段 `gripper_name_prefix`，它表示“生成机器可读的模型合并证据”中的 `gripper_name_prefix` 数据；字段值来自 `args.gripper_name_prefix`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_name_prefix": args.gripper_name_prefix,
# 【L0272】定义字典/JSON 字段 `gripper_inertial_regularization`，它表示“生成机器可读的模型合并证据”中的 `gripper_inertial_regularization` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_inertial_regularization": {
# 【L0273】定义字典/JSON 字段 `minimum_mass_kg`，它表示“生成机器可读的模型合并证据”中的 `minimum_mass_kg` 数据；字段值来自 `args.gripper_min_mass_kg`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_mass_kg": args.gripper_min_mass_kg,
# 【L0274】定义字典/JSON 字段 `minimum_diagonal_inertia_kg_m2`，它表示“生成机器可读的模型合并证据”中的 `minimum_diagonal_inertia_kg_m2` 数据；字段值来自 `args.gripper_min_diagonal_inertia`，因此保存/传递的是这个表达式当前计算出的结果。
            "minimum_diagonal_inertia_kg_m2": args.gripper_min_diagonal_inertia,
# 【L0275】定义字典/JSON 字段 `zero_cross_inertia`，它表示“生成机器可读的模型合并证据”中的 `zero_cross_inertia` 数据；字段值来自 `args.zero_gripper_cross_inertia`，因此保存/传递的是这个表达式当前计算出的结果。
            "zero_cross_inertia": args.zero_gripper_cross_inertia,
# 【L0276】定义字典/JSON 字段 `changed_links`，它表示“生成机器可读的模型合并证据”中的 `changed_links` 数据；字段值来自 `inertial_changes`，因此保存/传递的是这个表达式当前计算出的结果。
            "changed_links": inertial_changes,
# 【L0277】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
        },
# 【L0278】定义字典/JSON 字段 `gripper_link_name_map`，它表示“生成机器可读的模型合并证据”中的 `gripper_link_name_map` 数据；字段值来自 `link_map`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_link_name_map": link_map,
# 【L0279】定义字典/JSON 字段 `gripper_contact_pads`，它表示“生成机器可读的模型合并证据”中的 `gripper_contact_pads` 数据；字段值来自 `contact_pads`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_contact_pads": contact_pads,
# 【L0280】定义字典/JSON 字段 `gripper_joint_name_map`，它表示“生成机器可读的模型合并证据”中的 `gripper_joint_name_map` 数据；字段值来自 `joint_map`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_joint_name_map": joint_map,
# 【L0281】定义字典/JSON 字段 `gripper_control`，它表示“生成机器可读的模型合并证据”中的 `gripper_control` 数据；字段值来自 `{`，因此保存/传递的是这个表达式当前计算出的结果。
        "gripper_control": {
# 【L0282】定义字典/JSON 字段 `master_joint`，它表示“生成机器可读的模型合并证据”中的 `master_joint` 数据；字段值来自 `joint_map.get("gripper_joint")`，因此保存/传递的是这个表达式当前计算出的结果。
            "master_joint": joint_map.get("gripper_joint"),
# 【L0283】定义字典/JSON 字段 `follower_joints`，它表示“生成机器可读的模型合并证据”中的 `follower_joints` 数据；字段值来自 `source_mimic_follower_joints`，因此保存/传递的是这个表达式当前计算出的结果。
            "follower_joints": source_mimic_follower_joints,
# 【L0284】定义字典/JSON 字段 `source_uses_mimic`，它表示“生成机器可读的模型合并证据”中的 `source_uses_mimic` 数据；字段值来自 `True`，因此保存/传递的是这个表达式当前计算出的结果。
            "source_uses_mimic": True,
# 【L0285】定义字典/JSON 字段 `output_preserves_mimic`，它表示“生成机器可读的模型合并证据”中的 `output_preserves_mimic` 数据；字段值来自 `args.preserve_mimic`，因此保存/传递的是这个表达式当前计算出的结果。
            "output_preserves_mimic": args.preserve_mimic,
# 【L0286】定义字典/JSON 字段 `simulation_mode`，它表示“生成机器可读的模型合并证据”中的 `simulation_mode` 数据；字段值来自 `"physx_mimic" if args.preserve_mimic else "software_coupled_joint_targets"`，因此保存/传递的是这个表达式当前计算出的结果。
            "simulation_mode": "physx_mimic" if args.preserve_mimic else "software_coupled_joint_targets",
# 【L0287】定义字典/JSON 字段 `note`，它表示“生成机器可读的模型合并证据”中的 `note` 数据；字段值来自 `"The source 4C2 has one command joint and five mimic followers."`，因此保存/传递的是这个表达式当前计算出的结果。
            "note": "The source 4C2 has one command joint and five mimic followers.",
# 【L0288】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
        },
# 【L0289】定义字典/JSON 字段 `link_count`，它表示“生成机器可读的模型合并证据”中的 `link_count` 数据；字段值来自 `len(combined_links)`，因此保存/传递的是这个表达式当前计算出的结果。
        "link_count": len(combined_links),
# 【L0290】定义字典/JSON 字段 `joint_count`，它表示“生成机器可读的模型合并证据”中的 `joint_count` 数据；字段值来自 `len(combined_joint_elements)`，因此保存/传递的是这个表达式当前计算出的结果。
        "joint_count": len(combined_joint_elements),
# 【L0291】定义字典/JSON 字段 `movable_joint_count`，它表示“生成机器可读的模型合并证据”中的 `movable_joint_count` 数据；字段值来自 `sum(j.get("type") != "fixed" for j in combined_joint_elements)`，因此保存/传递的是这个表达式当前计算出的结果。
        "movable_joint_count": sum(j.get("type") != "fixed" for j in combined_joint_elements),
# 【L0292】定义字典/JSON 字段 `links`，它表示“生成机器可读的模型合并证据”中的 `links` 数据；字段值来自 `combined_links`，因此保存/传递的是这个表达式当前计算出的结果。
        "links": combined_links,
# 【L0293】定义字典/JSON 字段 `joints`，它表示LeRobot 一帧中的六个 RM65 关节角；字段值来自 `[joint_record(joint) for joint in combined_joint_elements]`，因此保存/传递的是这个表达式当前计算出的结果。
        "joints": [joint_record(joint) for joint in combined_joint_elements],
# 【L0294】定义字典/JSON 字段 `mesh_count`，它表示“生成机器可读的模型合并证据”中的 `mesh_count` 数据；字段值来自 `len(arm_meshes) + len(gripper_meshes)`，因此保存/传递的是这个表达式当前计算出的结果。
        "mesh_count": len(arm_meshes) + len(gripper_meshes),
# 【L0295】定义字典/JSON 字段 `meshes`，它表示“生成机器可读的模型合并证据”中的 `meshes` 数据；字段值来自 `arm_meshes + gripper_meshes`，因此保存/传递的是这个表达式当前计算出的结果。
        "meshes": arm_meshes + gripper_meshes,
# 【L0296】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
    }
# 【L0297】判断 `args.report` 是否成立；`report` 表示机器可读实验报告字典
    if args.report:
# 【L0298】得到 `report_path`，它在本项目中表示报告、路径相关值；保存为当前作用域变量，供下面的步骤读取。这一行右侧的工作是：计算表达式 `args.report.expanduser().resolve()`；`report` 表示机器可读实验报告字典；`expanduser` 表示本功能块中的 `expanduser` 值；`resolve` 表示本功能块中的 `resolve` 值。
        report_path = args.report.expanduser().resolve()
# 【L0299】调用 `mkdir`：创建目录；本行实际操作 `report_path.parent.mkdir(parents=True, exist_ok=True)`。`report_path` 表示报告、路径相关值；`parent` 表示本功能块中的 `parent` 值。
        report_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0300】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本；本行实际操作 `report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")`。`report_path` 表示报告、路径相关值；`write_text` 表示本功能块中的 `write_text` 值。
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
# 【L0301】把 `json.dumps(report, indent=2, ensure_ascii=False)` 的当前值/文字输出到终端；它用于观察“生成机器可读的模型合并证据”进度，也给日志留下可搜索证据。
    print(json.dumps(report, indent=2, ensure_ascii=False))
# 【L0302】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0303】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0304】判断 `__name__ == "__main__"` 是否成立；`__name__` 表示本功能块中的 `__name__` 值；`__main__` 表示本功能块中的 `__main__` 值
if __name__ == "__main__":
# 【L0305】调用本文件的 `main()`，从这里正式进入参数解析、资源创建和主任务流程；上面的函数此时才开始被实际使用。
    main()
```
