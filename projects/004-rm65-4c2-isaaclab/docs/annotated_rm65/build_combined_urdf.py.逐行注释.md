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

每个 `【Lxxxx】` 注释解释紧随其后的原始行。空行也保留并说明，因为空行体现程序分段。

```python
# 【L0001】shebang：在 Linux 直接执行文件时，选择后面的 Python 或 Bash 解释器。
#!/usr/bin/env python3
# 【L0002】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
"""Combine the RM65 arm and a gripper URDF without copying mesh assets."""
# 【L0003】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0004】延迟解析类型标注，允许在类型提示里更自由地引用尚未定义的类型。
from __future__ import annotations
# 【L0005】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0006】导入 argparse：标准库命令行解析器，让实验参数不必写死在代码里；后面的代码会调用其中的类或函数。
import argparse
# 【L0007】导入 copy：项目或第三方模块；后面的代码会调用其中的类或函数。
import copy
# 【L0008】导入 json：读写人和程序都容易检查的 JSON 证据文件；后面的代码会调用其中的类或函数。
import json
# 【L0009】导入 pathlib：使用 Path 对象处理跨平台文件路径；后面的代码会调用其中的类或函数。
from pathlib import Path
# 【L0010】导入 xml：项目或第三方模块；后面的代码会调用其中的类或函数。
import xml.etree.ElementTree as ET
# 【L0011】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0012】空行：分隔“解释器、模块说明与 XML/路径工具导入”中的逻辑段，让结构更容易看清。

# 【L0013】定义函数 parse_vector；其职责属于“把命令行里的 xyz/rpy 文本校验成三个浮点数”，缩进块是函数体。
def parse_vector(text: str, expected: int = 3) -> str:
# 【L0014】计算并保存变量 `values`；该值服务于“把命令行里的 xyz/rpy 文本校验成三个浮点数”。
    values = [float(value) for value in text.split()]
# 【L0015】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if len(values) != expected:
# 【L0016】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise argparse.ArgumentTypeError(f"expected {expected} numbers, got {text!r}")
# 【L0017】结束当前函数并把结果交给调用者；这里完成“把命令行里的 xyz/rpy 文本校验成三个浮点数”的输出。
    return " ".join(f"{value:.9g}" for value in values)
# 【L0018】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0019】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0020】定义函数 rewrite_meshes；其职责属于“把 URDF 中的 mesh 路径改成绝对 file URI”，缩进块是函数体。
def rewrite_meshes(robot: ET.Element, mesh_dir: Path) -> list[dict[str, str]]:
# 【L0021】计算并保存变量 `records`；该值服务于“把 URDF 中的 mesh 路径改成绝对 file URI”。
    records: list[dict[str, str]] = []
# 【L0022】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for mesh in robot.findall(".//mesh"):
# 【L0023】计算并保存变量 `original`；该值服务于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        original = mesh.get("filename")
# 【L0024】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not original:
# 【L0025】跳过本次循环剩余语句，继续处理下一个候选项。
            continue
# 【L0026】调用 `Path`：创建路径对象。本行位于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        filename = Path(original.replace("\\", "/")).name
# 【L0027】计算并保存变量 `resolved`；该值服务于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        resolved = (mesh_dir / filename).resolve()
# 【L0028】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if not resolved.is_file():
# 【L0029】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise FileNotFoundError(f"mesh referenced by URDF was not found: {resolved}")
# 【L0030】计算并保存变量 `uri`；该值服务于“把 URDF 中的 mesh 路径改成绝对 file URI”。
        uri = resolved.as_uri()
# 【L0031】执行“把 URDF 中的 mesh 路径改成绝对 file URI”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        mesh.set("filename", uri)
# 【L0032】执行“把 URDF 中的 mesh 路径改成绝对 file URI”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        records.append({"original": original, "resolved": str(resolved), "uri": uri})
# 【L0033】结束当前函数并把结果交给调用者；这里完成“把 URDF 中的 mesh 路径改成绝对 file URI”的输出。
    return records
# 【L0034】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0035】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0036】定义函数 prefix_gripper_names；其职责属于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”，缩进块是函数体。
def prefix_gripper_names(robot: ET.Element, prefix: str) -> tuple[dict[str, str], dict[str, str]]:
# 【L0037】计算并保存变量 `link_map`；该值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    link_map = {
# 【L0038】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        link.get("name"): f"{prefix}{link.get('name')}"
# 【L0039】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for link in robot.findall("link")
# 【L0040】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if link.get("name")
# 【L0041】结束或闭合当前语法结构；它属于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    }
# 【L0042】计算并保存变量 `joint_map`；该值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    joint_map = {
# 【L0043】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        joint.get("name"): f"{prefix}{joint.get('name')}"
# 【L0044】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for joint in robot.findall("joint")
# 【L0045】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if joint.get("name")
# 【L0046】结束或闭合当前语法结构；它属于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
    }
# 【L0047】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for link in robot.findall("link"):
# 【L0048】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if link.get("name") in link_map:
# 【L0049】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            link.set("name", link_map[link.get("name")])
# 【L0050】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for joint in robot.findall("joint"):
# 【L0051】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if joint.get("name") in joint_map:
# 【L0052】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            joint.set("name", joint_map[joint.get("name")])
# 【L0053】计算并保存变量 `parent`；该值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
        parent = joint.find("parent")
# 【L0054】计算并保存变量 `child`；该值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
        child = joint.find("child")
# 【L0055】计算并保存变量 `mimic`；该值服务于“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”。
        mimic = joint.find("mimic")
# 【L0056】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if parent is not None and parent.get("link") in link_map:
# 【L0057】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            parent.set("link", link_map[parent.get("link")])
# 【L0058】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if child is not None and child.get("link") in link_map:
# 【L0059】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            child.set("link", link_map[child.get("link")])
# 【L0060】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if mimic is not None and mimic.get("joint") in joint_map:
# 【L0061】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            mimic.set("joint", joint_map[mimic.get("joint")])
# 【L0062】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for transmission_joint in robot.findall(".//transmission/joint"):
# 【L0063】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if transmission_joint.get("name") in joint_map:
# 【L0064】执行“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            transmission_joint.set("name", joint_map[transmission_joint.get("name")])
# 【L0065】结束当前函数并把结果交给调用者；这里完成“给夹爪 link/joint 加 tool_ 前缀，防止与机械臂重名”的输出。
    return link_map, joint_map
# 【L0066】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0067】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0068】定义函数 regularize_gripper_inertials；其职责属于“修正 CAD 导出中过小或不稳定的质量和惯量”，缩进块是函数体。
def regularize_gripper_inertials(
# 【L0069】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
    robot: ET.Element,
# 【L0070】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
    minimum_mass_kg: float,
# 【L0071】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
    minimum_diagonal_inertia: float,
# 【L0072】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
    zero_cross_inertia: bool,
# 【L0073】开始一个缩进代码块或键值结构；该块负责“修正 CAD 导出中过小或不稳定的质量和惯量”。
) -> list[dict[str, object]]:
# 【L0074】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Regularize tiny CAD-exported inertias for an explicitly labeled physics proxy."""
# 【L0075】空行：分隔“修正 CAD 导出中过小或不稳定的质量和惯量”中的逻辑段，让结构更容易看清。

# 【L0076】计算并保存变量 `changes`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
    changes: list[dict[str, object]] = []
# 【L0077】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for link in robot.findall("link"):
# 【L0078】计算并保存变量 `inertial`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        inertial = link.find("inertial")
# 【L0079】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if inertial is None:
# 【L0080】跳过本次循环剩余语句，继续处理下一个候选项。
            continue
# 【L0081】计算并保存变量 `mass`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        mass = inertial.find("mass")
# 【L0082】计算并保存变量 `inertia`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        inertia = inertial.find("inertia")
# 【L0083】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if mass is None or inertia is None or mass.get("value") is None:
# 【L0084】跳过本次循环剩余语句，继续处理下一个候选项。
            continue
# 【L0085】计算并保存变量 `before_mass`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        before_mass = float(mass.get("value"))
# 【L0086】计算并保存变量 `after_mass`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        after_mass = max(before_mass, minimum_mass_kg)
# 【L0087】计算并保存变量 `before_inertia`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        before_inertia = {name: float(inertia.get(name, "0")) for name in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")}
# 【L0088】计算并保存变量 `after_inertia`；该值服务于“修正 CAD 导出中过小或不稳定的质量和惯量”。
        after_inertia = before_inertia.copy()
# 【L0089】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for name in ("ixx", "iyy", "izz"):
# 【L0090】执行“修正 CAD 导出中过小或不稳定的质量和惯量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            after_inertia[name] = max(after_inertia[name], minimum_diagonal_inertia)
# 【L0091】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if zero_cross_inertia:
# 【L0092】for 循环：依次处理序列中的每个元素/时间步/episode/case。
            for name in ("ixy", "ixz", "iyz"):
# 【L0093】执行“修正 CAD 导出中过小或不稳定的质量和惯量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                after_inertia[name] = 0.0
# 【L0094】执行“修正 CAD 导出中过小或不稳定的质量和惯量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        mass.set("value", f"{after_mass:.12g}")
# 【L0095】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for name, value in after_inertia.items():
# 【L0096】执行“修正 CAD 导出中过小或不稳定的质量和惯量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            inertia.set(name, f"{value:.12g}")
# 【L0097】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if after_mass != before_mass or after_inertia != before_inertia:
# 【L0098】执行“修正 CAD 导出中过小或不稳定的质量和惯量”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            changes.append(
# 【L0099】继续构造上一行开始的列表、元组、字典、参数或表达式；语义属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
                {
# 【L0100】定义字典/JSON 字段 `link`；它把“修正 CAD 导出中过小或不稳定的质量和惯量”中的结果用稳定键名记录下来。
                    "link": link.get("name"),
# 【L0101】定义字典/JSON 字段 `mass_before_kg`；它把“修正 CAD 导出中过小或不稳定的质量和惯量”中的结果用稳定键名记录下来。
                    "mass_before_kg": before_mass,
# 【L0102】定义字典/JSON 字段 `mass_after_kg`；它把“修正 CAD 导出中过小或不稳定的质量和惯量”中的结果用稳定键名记录下来。
                    "mass_after_kg": after_mass,
# 【L0103】定义字典/JSON 字段 `inertia_before_kg_m2`；它把“修正 CAD 导出中过小或不稳定的质量和惯量”中的结果用稳定键名记录下来。
                    "inertia_before_kg_m2": before_inertia,
# 【L0104】定义字典/JSON 字段 `inertia_after_kg_m2`；它把“修正 CAD 导出中过小或不稳定的质量和惯量”中的结果用稳定键名记录下来。
                    "inertia_after_kg_m2": after_inertia,
# 【L0105】结束或闭合当前语法结构；它属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
                }
# 【L0106】结束或闭合当前语法结构；它属于“修正 CAD 导出中过小或不稳定的质量和惯量”。
            )
# 【L0107】结束当前函数并把结果交给调用者；这里完成“修正 CAD 导出中过小或不稳定的质量和惯量”的输出。
    return changes
# 【L0108】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0109】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0110】定义函数 add_4c2_contact_pads；其职责属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”，缩进块是函数体。
def add_4c2_contact_pads(
# 【L0111】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    robot: ET.Element, prefix: str, pad_dimensions_m: tuple[float, float, float]
# 【L0112】开始一个缩进代码块或键值结构；该块负责“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
) -> list[dict[str, str]]:
# 【L0113】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """Add thin box colliders at empirically derived left/right grasp surfaces.
# 【L0114】空行：分隔“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的逻辑段，让结构更容易看清。

# 【L0115】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    The poses are expressed in each second-finger link frame.  They were
# 【L0116】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    back-projected from a centered 40 mm block at the validated 0.65 rad
# 【L0117】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    closing pose, with 2 mm of intended compression per side.
# 【L0118】模块、类或函数说明字符串；运行时可由 help() 读取，也告诉读者这一块负责什么。
    """
# 【L0119】空行：分隔“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的逻辑段，让结构更容易看清。

# 【L0120】计算并保存变量 `pad_size`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    pad_size = " ".join(f"{value:.9g}" for value in pad_dimensions_m)
# 【L0121】计算并保存变量 `specs`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    specs = {
# 【L0122】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        f"{prefix}l_2": {
# 【L0123】定义字典/JSON 字段 `xyz`；它把“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的结果用稳定键名记录下来。
            "xyz": "0.027286683 0.013343694 -0.072958842",
# 【L0124】定义字典/JSON 字段 `rpy`；它把“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的结果用稳定键名记录下来。
            "rpy": "0.005034454 0.254940134 0.652909860",
# 【L0125】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        },
# 【L0126】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        f"{prefix}r_2": {
# 【L0127】定义字典/JSON 字段 `xyz`；它把“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的结果用稳定键名记录下来。
            "xyz": "0.028775714 -0.011597111 -0.073257379",
# 【L0128】定义字典/JSON 字段 `rpy`；它把“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的结果用稳定键名记录下来。
            "rpy": "0.005034429 0.254940104 -0.644663208",
# 【L0129】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        },
# 【L0130】结束或闭合当前语法结构；它属于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    }
# 【L0131】计算并保存变量 `links`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    links = {link.get("name"): link for link in robot.findall("link")}
# 【L0132】计算并保存变量 `records`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
    records: list[dict[str, str]] = []
# 【L0133】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for link_name, pose in specs.items():
# 【L0134】计算并保存变量 `link`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        link = links.get(link_name)
# 【L0135】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if link is None:
# 【L0136】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
            raise ValueError(f"cannot add 4C2 contact pad: missing link {link_name!r}")
# 【L0137】计算并保存变量 `collision`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        collision = ET.SubElement(link, "collision", {"name": "contact_pad_box"})
# 【L0138】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ET.SubElement(collision, "origin", {"xyz": pose["xyz"], "rpy": pose["rpy"]})
# 【L0139】计算并保存变量 `geometry`；该值服务于“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”。
        geometry = ET.SubElement(collision, "geometry")
# 【L0140】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        ET.SubElement(geometry, "box", {"size": pad_size})
# 【L0141】执行“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        records.append({"link": link_name, "xyz": pose["xyz"], "rpy": pose["rpy"], "size": pad_size})
# 【L0142】结束当前函数并把结果交给调用者；这里完成“为 4C2 指尖增加用于稳定接触的薄盒碰撞片”的输出。
    return records
# 【L0143】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0144】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0145】定义函数 joint_record；其职责属于“把 joint 的父子关系、限位和 mimic 信息整理进报告”，缩进块是函数体。
def joint_record(joint: ET.Element) -> dict[str, object]:
# 【L0146】计算并保存变量 `limit`；该值服务于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    limit = joint.find("limit")
# 【L0147】计算并保存变量 `parent`；该值服务于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    parent = joint.find("parent")
# 【L0148】计算并保存变量 `child`；该值服务于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    child = joint.find("child")
# 【L0149】计算并保存变量 `mimic`；该值服务于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    mimic = joint.find("mimic")
# 【L0150】结束当前函数并把结果交给调用者；这里完成“把 joint 的父子关系、限位和 mimic 信息整理进报告”的输出。
    return {
# 【L0151】定义字典/JSON 字段 `name`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "name": joint.get("name"),
# 【L0152】定义字典/JSON 字段 `type`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "type": joint.get("type"),
# 【L0153】定义字典/JSON 字段 `parent`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "parent": None if parent is None else parent.get("link"),
# 【L0154】定义字典/JSON 字段 `child`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "child": None if child is None else child.get("link"),
# 【L0155】定义字典/JSON 字段 `lower`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "lower": None if limit is None or limit.get("lower") is None else float(limit.get("lower")),
# 【L0156】定义字典/JSON 字段 `upper`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "upper": None if limit is None or limit.get("upper") is None else float(limit.get("upper")),
# 【L0157】定义字典/JSON 字段 `mimic_joint`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "mimic_joint": None if mimic is None else mimic.get("joint"),
# 【L0158】定义字典/JSON 字段 `mimic_multiplier`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "mimic_multiplier": None if mimic is None else float(mimic.get("multiplier", "1")),
# 【L0159】定义字典/JSON 字段 `mimic_offset`；它把“把 joint 的父子关系、限位和 mimic 信息整理进报告”中的结果用稳定键名记录下来。
        "mimic_offset": None if mimic is None else float(mimic.get("offset", "0")),
# 【L0160】结束或闭合当前语法结构；它属于“把 joint 的父子关系、限位和 mimic 信息整理进报告”。
    }
# 【L0161】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0162】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0163】定义函数 main；其职责属于“定义命令行接口”，缩进块是函数体。
def main() -> None:
# 【L0164】计算并保存变量 `parser`；该值服务于“定义命令行接口”。
    parser = argparse.ArgumentParser(description=__doc__)
# 【L0165】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--rm65-urdf", type=Path, required=True)
# 【L0166】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--rm65-mesh-dir", type=Path, required=True)
# 【L0167】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-urdf", type=Path, required=True)
# 【L0168】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-mesh-dir", type=Path, required=True)
# 【L0169】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-root-link", default="base_link")
# 【L0170】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-name-prefix", default="tool_")
# 【L0171】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--output", type=Path, required=True)
# 【L0172】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--report", type=Path)
# 【L0173】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--mount-xyz", type=parse_vector, default="0 0 0")
# 【L0174】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--mount-rpy", type=parse_vector, default="0 0 0")
# 【L0175】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-min-mass-kg", type=float, default=0.0)
# 【L0176】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--gripper-min-diagonal-inertia", type=float, default=0.0)
# 【L0177】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument("--zero-gripper-cross-inertia", action="store_true")
# 【L0178】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0179】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“定义命令行接口”。
        "--add-4c2-contact-pads",
# 【L0180】计算并保存变量 `action`；该值服务于“定义命令行接口”。
        action="store_true",
# 【L0181】计算并保存变量 `help`；该值服务于“定义命令行接口”。
        help="Add two thin, box-shaped collision pads for bilateral grasp diagnostics.",
# 【L0182】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0183】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0184】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“定义命令行接口”。
        "--4c2-contact-pad-size-m",
# 【L0185】计算并保存变量 `dest`；该值服务于“定义命令行接口”。
        dest="contact_pad_size_m",
# 【L0186】计算并保存变量 `type`；该值服务于“定义命令行接口”。
        type=float,
# 【L0187】计算并保存变量 `nargs`；该值服务于“定义命令行接口”。
        nargs=3,
# 【L0188】计算并保存变量 `metavar`；该值服务于“定义命令行接口”。
        metavar=("X", "Y", "Z"),
# 【L0189】计算并保存变量 `default`；该值服务于“定义命令行接口”。
        default=(0.025, 0.010, 0.020),
# 【L0190】计算并保存变量 `help`；该值服务于“定义命令行接口”。
        help="Box dimensions in each second-finger link frame (default: 0.025 0.010 0.020).",
# 【L0191】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0192】声明一个命令行参数，使这项实验设置能在启动时指定并被日志复现。
    parser.add_argument(
# 【L0193】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“定义命令行接口”。
        "--preserve-mimic",
# 【L0194】计算并保存变量 `action`；该值服务于“定义命令行接口”。
        action="store_true",
# 【L0195】计算并保存变量 `help`；该值服务于“定义命令行接口”。
        help="Keep source mimic tags. The default strips them for stable software-coupled drives in PhysX.",
# 【L0196】结束或闭合当前语法结构；它属于“定义命令行接口”。
    )
# 【L0197】计算并保存变量 `args`；该值服务于“定义命令行接口”。
    args = parser.parse_args()
# 【L0198】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0199】计算并保存变量 `arm_tree`；该值服务于“加载、校验和预处理两份 URDF”。
    arm_tree = ET.parse(args.rm65_urdf.expanduser())
# 【L0200】计算并保存变量 `gripper_tree`；该值服务于“加载、校验和预处理两份 URDF”。
    gripper_tree = ET.parse(args.gripper_urdf.expanduser())
# 【L0201】计算并保存变量 `arm`；该值服务于“加载、校验和预处理两份 URDF”。
    arm = arm_tree.getroot()
# 【L0202】给变量 `gripper` 赋值：一个归一化夹爪值组成的一维数组。
    gripper = gripper_tree.getroot()
# 【L0203】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if arm.tag != "robot" or gripper.tag != "robot":
# 【L0204】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("both input files must have a <robot> root")
# 【L0205】空行：分隔“加载、校验和预处理两份 URDF”中的逻辑段，让结构更容易看清。

# 【L0206】计算并保存变量 `original_gripper_links`；该值服务于“加载、校验和预处理两份 URDF”。
    original_gripper_links = {link.get("name") for link in gripper.findall("link")}
# 【L0207】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.gripper_root_link not in original_gripper_links:
# 【L0208】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"gripper URDF must contain root link {args.gripper_root_link!r}")
# 【L0209】计算并保存变量 `gripper_meshes`；该值服务于“加载、校验和预处理两份 URDF”。
    gripper_meshes = rewrite_meshes(gripper, args.gripper_mesh_dir.expanduser())
# 【L0210】执行“加载、校验和预处理两份 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    link_map, joint_map = prefix_gripper_names(gripper, args.gripper_name_prefix)
# 【L0211】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.gripper_min_mass_kg < 0 or args.gripper_min_diagonal_inertia < 0:
# 【L0212】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("gripper mass and inertia floors must be non-negative")
# 【L0213】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if any(value <= 0.0 for value in args.contact_pad_size_m):
# 【L0214】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("4C2 contact-pad dimensions must be positive")
# 【L0215】计算并保存变量 `inertial_changes`；该值服务于“加载、校验和预处理两份 URDF”。
    inertial_changes = regularize_gripper_inertials(
# 【L0216】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“加载、校验和预处理两份 URDF”。
        gripper,
# 【L0217】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“加载、校验和预处理两份 URDF”。
        args.gripper_min_mass_kg,
# 【L0218】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“加载、校验和预处理两份 URDF”。
        args.gripper_min_diagonal_inertia,
# 【L0219】这是跨多行参数/容器中的一个元素，逗号表示后面还有内容；属于“加载、校验和预处理两份 URDF”。
        args.zero_gripper_cross_inertia,
# 【L0220】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0221】计算并保存变量 `contact_pads`；该值服务于“加载、校验和预处理两份 URDF”。
    contact_pads = (
# 【L0222】执行“加载、校验和预处理两份 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        add_4c2_contact_pads(gripper, args.gripper_name_prefix, tuple(args.contact_pad_size_m))
# 【L0223】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if args.add_4c2_contact_pads
# 【L0224】执行“加载、校验和预处理两份 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        else []
# 【L0225】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0226】计算并保存变量 `gripper_root_link`；该值服务于“加载、校验和预处理两份 URDF”。
    gripper_root_link = link_map[args.gripper_root_link]
# 【L0227】计算并保存变量 `source_mimic_follower_joints`；该值服务于“加载、校验和预处理两份 URDF”。
    source_mimic_follower_joints = sorted(
# 【L0228】执行“加载、校验和预处理两份 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
        joint.get("name") for joint in gripper.findall("joint") if joint.find("mimic") is not None
# 【L0229】结束或闭合当前语法结构；它属于“加载、校验和预处理两份 URDF”。
    )
# 【L0230】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if not args.preserve_mimic:
# 【L0231】for 循环：依次处理序列中的每个元素/时间步/episode/case。
        for joint in gripper.findall("joint"):
# 【L0232】计算并保存变量 `mimic`；该值服务于“加载、校验和预处理两份 URDF”。
            mimic = joint.find("mimic")
# 【L0233】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
            if mimic is not None:
# 【L0234】执行“加载、校验和预处理两份 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
                joint.remove(mimic)
# 【L0235】空行：分隔“加载、校验和预处理两份 URDF”中的逻辑段，让结构更容易看清。

# 【L0236】计算并保存变量 `arm_links`；该值服务于“加载、校验和预处理两份 URDF”。
    arm_links = {link.get("name") for link in arm.findall("link")}
# 【L0237】计算并保存变量 `gripper_links`；该值服务于“加载、校验和预处理两份 URDF”。
    gripper_links = {link.get("name") for link in gripper.findall("link")}
# 【L0238】计算并保存变量 `arm_joints`；该值服务于“加载、校验和预处理两份 URDF”。
    arm_joints = {joint.get("name") for joint in arm.findall("joint")}
# 【L0239】计算并保存变量 `gripper_joints`；该值服务于“加载、校验和预处理两份 URDF”。
    gripper_joints = {joint.get("name") for joint in gripper.findall("joint")}
# 【L0240】计算并保存变量 `duplicate_links`；该值服务于“加载、校验和预处理两份 URDF”。
    duplicate_links = sorted(arm_links & gripper_links)
# 【L0241】计算并保存变量 `duplicate_joints`；该值服务于“加载、校验和预处理两份 URDF”。
    duplicate_joints = sorted(arm_joints & gripper_joints)
# 【L0242】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if duplicate_links or duplicate_joints:
# 【L0243】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError(f"duplicate names: links={duplicate_links}, joints={duplicate_joints}")
# 【L0244】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if "link_6" not in arm_links:
# 【L0245】主动抛出异常并停止当前路径，防止错误数据继续进入仿真、训练或评测。
        raise ValueError("RM65 URDF must contain end link 'link_6'")
# 【L0246】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0247】计算并保存变量 `arm_meshes`；该值服务于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    arm_meshes = rewrite_meshes(arm, args.rm65_mesh_dir.expanduser())
# 【L0248】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0249】for 循环：依次处理序列中的每个元素/时间步/episode/case。
    for child in list(gripper):
# 【L0250】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
        if child.tag in {"link", "joint", "gazebo", "transmission", "material"}:
# 【L0251】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
            arm.append(copy.deepcopy(child))
# 【L0252】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0253】计算并保存变量 `mount`；该值服务于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    mount = ET.Element("joint", {"name": "rm65_to_4c2", "type": "fixed"})
# 【L0254】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ET.SubElement(mount, "origin", {"xyz": args.mount_xyz, "rpy": args.mount_rpy})
# 【L0255】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ET.SubElement(mount, "parent", {"link": "link_6"})
# 【L0256】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ET.SubElement(mount, "child", {"link": gripper_root_link})
# 【L0257】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    arm.append(mount)
# 【L0258】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    arm.set("name", "rm65_4c2")
# 【L0259】空行：分隔“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的逻辑段，让结构更容易看清。

# 【L0260】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    ET.indent(arm_tree, space="  ")
# 【L0261】给变量 `output` 赋值：输出文件路径。
    output = args.output.expanduser().resolve()
# 【L0262】调用 `mkdir`：创建目录。本行位于“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”。
    output.parent.mkdir(parents=True, exist_ok=True)
# 【L0263】执行“合并模型、添加 link_6 到夹爪的固定关节并写出 URDF”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    arm_tree.write(output, encoding="utf-8", xml_declaration=True)
# 【L0264】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0265】计算并保存变量 `combined_links`；该值服务于“生成机器可读的模型合并证据”。
    combined_links = [link.get("name") for link in arm.findall("link")]
# 【L0266】计算并保存变量 `combined_joint_elements`；该值服务于“生成机器可读的模型合并证据”。
    combined_joint_elements = arm.findall("joint")
# 【L0267】给变量 `report` 赋值：机器可读实验报告字典。
    report = {
# 【L0268】定义字典/JSON 字段 `robot_name`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "robot_name": arm.get("name"),
# 【L0269】定义字典/JSON 字段 `output_urdf`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "output_urdf": str(output),
# 【L0270】定义字典/JSON 字段 `mount`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "mount": {"parent": "link_6", "child": gripper_root_link, "xyz": args.mount_xyz, "rpy": args.mount_rpy},
# 【L0271】定义字典/JSON 字段 `gripper_name_prefix`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_name_prefix": args.gripper_name_prefix,
# 【L0272】定义字典/JSON 字段 `gripper_inertial_regularization`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_inertial_regularization": {
# 【L0273】定义字典/JSON 字段 `minimum_mass_kg`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "minimum_mass_kg": args.gripper_min_mass_kg,
# 【L0274】定义字典/JSON 字段 `minimum_diagonal_inertia_kg_m2`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "minimum_diagonal_inertia_kg_m2": args.gripper_min_diagonal_inertia,
# 【L0275】定义字典/JSON 字段 `zero_cross_inertia`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "zero_cross_inertia": args.zero_gripper_cross_inertia,
# 【L0276】定义字典/JSON 字段 `changed_links`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "changed_links": inertial_changes,
# 【L0277】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
        },
# 【L0278】定义字典/JSON 字段 `gripper_link_name_map`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_link_name_map": link_map,
# 【L0279】定义字典/JSON 字段 `gripper_contact_pads`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_contact_pads": contact_pads,
# 【L0280】定义字典/JSON 字段 `gripper_joint_name_map`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_joint_name_map": joint_map,
# 【L0281】定义字典/JSON 字段 `gripper_control`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "gripper_control": {
# 【L0282】定义字典/JSON 字段 `master_joint`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "master_joint": joint_map.get("gripper_joint"),
# 【L0283】定义字典/JSON 字段 `follower_joints`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "follower_joints": source_mimic_follower_joints,
# 【L0284】定义字典/JSON 字段 `source_uses_mimic`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "source_uses_mimic": True,
# 【L0285】定义字典/JSON 字段 `output_preserves_mimic`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "output_preserves_mimic": args.preserve_mimic,
# 【L0286】定义字典/JSON 字段 `simulation_mode`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "simulation_mode": "physx_mimic" if args.preserve_mimic else "software_coupled_joint_targets",
# 【L0287】定义字典/JSON 字段 `note`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
            "note": "The source 4C2 has one command joint and five mimic followers.",
# 【L0288】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
        },
# 【L0289】定义字典/JSON 字段 `link_count`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "link_count": len(combined_links),
# 【L0290】定义字典/JSON 字段 `joint_count`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "joint_count": len(combined_joint_elements),
# 【L0291】定义字典/JSON 字段 `movable_joint_count`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "movable_joint_count": sum(j.get("type") != "fixed" for j in combined_joint_elements),
# 【L0292】定义字典/JSON 字段 `links`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "links": combined_links,
# 【L0293】定义字典/JSON 字段 `joints`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "joints": [joint_record(joint) for joint in combined_joint_elements],
# 【L0294】定义字典/JSON 字段 `mesh_count`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "mesh_count": len(arm_meshes) + len(gripper_meshes),
# 【L0295】定义字典/JSON 字段 `meshes`；它把“生成机器可读的模型合并证据”中的结果用稳定键名记录下来。
        "meshes": arm_meshes + gripper_meshes,
# 【L0296】结束或闭合当前语法结构；它属于“生成机器可读的模型合并证据”。
    }
# 【L0297】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
    if args.report:
# 【L0298】计算并保存变量 `report_path`；该值服务于“生成机器可读的模型合并证据”。
        report_path = args.report.expanduser().resolve()
# 【L0299】调用 `mkdir`：创建目录。本行位于“生成机器可读的模型合并证据”。
        report_path.parent.mkdir(parents=True, exist_ok=True)
# 【L0300】调用 `json.dumps`：把 Python 字典序列化成 JSON 文本。本行位于“生成机器可读的模型合并证据”。
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
# 【L0301】向终端输出人可读进度或机器可搜索标记，便于定位阶段和失败。
    print(json.dumps(report, indent=2, ensure_ascii=False))
# 【L0302】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0303】空行：分隔“文件级连接或空白区域”中的逻辑段，让结构更容易看清。

# 【L0304】条件分支：只有条件为真才执行后面的缩进代码；这里用于校验或选择运行路径。
if __name__ == "__main__":
# 【L0305】执行“脚本入口”中的这一步；具体对象名和参数决定本行读取、计算或提交的值。
    main()
```
