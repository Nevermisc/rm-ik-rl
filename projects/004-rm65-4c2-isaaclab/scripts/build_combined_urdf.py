#!/usr/bin/env python3
"""Combine the RM65 arm and a gripper URDF without copying mesh assets."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_vector(text: str, expected: int = 3) -> str:
    values = [float(value) for value in text.split()]
    if len(values) != expected:
        raise argparse.ArgumentTypeError(f"expected {expected} numbers, got {text!r}")
    return " ".join(f"{value:.9g}" for value in values)


def rewrite_meshes(robot: ET.Element, mesh_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for mesh in robot.findall(".//mesh"):
        original = mesh.get("filename")
        if not original:
            continue
        filename = Path(original.replace("\\", "/")).name
        resolved = (mesh_dir / filename).resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"mesh referenced by URDF was not found: {resolved}")
        uri = resolved.as_uri()
        mesh.set("filename", uri)
        records.append({"original": original, "resolved": str(resolved), "uri": uri})
    return records


def prefix_gripper_names(robot: ET.Element, prefix: str) -> tuple[dict[str, str], dict[str, str]]:
    link_map = {
        link.get("name"): f"{prefix}{link.get('name')}"
        for link in robot.findall("link")
        if link.get("name")
    }
    joint_map = {
        joint.get("name"): f"{prefix}{joint.get('name')}"
        for joint in robot.findall("joint")
        if joint.get("name")
    }
    for link in robot.findall("link"):
        if link.get("name") in link_map:
            link.set("name", link_map[link.get("name")])
    for joint in robot.findall("joint"):
        if joint.get("name") in joint_map:
            joint.set("name", joint_map[joint.get("name")])
        parent = joint.find("parent")
        child = joint.find("child")
        mimic = joint.find("mimic")
        if parent is not None and parent.get("link") in link_map:
            parent.set("link", link_map[parent.get("link")])
        if child is not None and child.get("link") in link_map:
            child.set("link", link_map[child.get("link")])
        if mimic is not None and mimic.get("joint") in joint_map:
            mimic.set("joint", joint_map[mimic.get("joint")])
    for transmission_joint in robot.findall(".//transmission/joint"):
        if transmission_joint.get("name") in joint_map:
            transmission_joint.set("name", joint_map[transmission_joint.get("name")])
    return link_map, joint_map


def regularize_gripper_inertials(
    robot: ET.Element,
    minimum_mass_kg: float,
    minimum_diagonal_inertia: float,
    zero_cross_inertia: bool,
) -> list[dict[str, object]]:
    """Regularize tiny CAD-exported inertias for an explicitly labeled physics proxy."""

    changes: list[dict[str, object]] = []
    for link in robot.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        mass = inertial.find("mass")
        inertia = inertial.find("inertia")
        if mass is None or inertia is None or mass.get("value") is None:
            continue
        before_mass = float(mass.get("value"))
        after_mass = max(before_mass, minimum_mass_kg)
        before_inertia = {name: float(inertia.get(name, "0")) for name in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz")}
        after_inertia = before_inertia.copy()
        for name in ("ixx", "iyy", "izz"):
            after_inertia[name] = max(after_inertia[name], minimum_diagonal_inertia)
        if zero_cross_inertia:
            for name in ("ixy", "ixz", "iyz"):
                after_inertia[name] = 0.0
        mass.set("value", f"{after_mass:.12g}")
        for name, value in after_inertia.items():
            inertia.set(name, f"{value:.12g}")
        if after_mass != before_mass or after_inertia != before_inertia:
            changes.append(
                {
                    "link": link.get("name"),
                    "mass_before_kg": before_mass,
                    "mass_after_kg": after_mass,
                    "inertia_before_kg_m2": before_inertia,
                    "inertia_after_kg_m2": after_inertia,
                }
            )
    return changes


def add_4c2_contact_pads(
    robot: ET.Element, prefix: str, pad_dimensions_m: tuple[float, float, float]
) -> list[dict[str, str]]:
    """Add thin box colliders at empirically derived left/right grasp surfaces.

    The poses are expressed in each second-finger link frame.  They were
    back-projected from a centered 40 mm block at the validated 0.65 rad
    closing pose, with 2 mm of intended compression per side.
    """

    pad_size = " ".join(f"{value:.9g}" for value in pad_dimensions_m)
    specs = {
        f"{prefix}l_2": {
            "xyz": "0.027286683 0.013343694 -0.072958842",
            "rpy": "0.005034454 0.254940134 0.652909860",
        },
        f"{prefix}r_2": {
            "xyz": "0.028775714 -0.011597111 -0.073257379",
            "rpy": "0.005034429 0.254940104 -0.644663208",
        },
    }
    links = {link.get("name"): link for link in robot.findall("link")}
    records: list[dict[str, str]] = []
    for link_name, pose in specs.items():
        link = links.get(link_name)
        if link is None:
            raise ValueError(f"cannot add 4C2 contact pad: missing link {link_name!r}")
        collision = ET.SubElement(link, "collision", {"name": "contact_pad_box"})
        ET.SubElement(collision, "origin", {"xyz": pose["xyz"], "rpy": pose["rpy"]})
        geometry = ET.SubElement(collision, "geometry")
        ET.SubElement(geometry, "box", {"size": pad_size})
        records.append({"link": link_name, "xyz": pose["xyz"], "rpy": pose["rpy"], "size": pad_size})
    return records


def joint_record(joint: ET.Element) -> dict[str, object]:
    limit = joint.find("limit")
    parent = joint.find("parent")
    child = joint.find("child")
    mimic = joint.find("mimic")
    return {
        "name": joint.get("name"),
        "type": joint.get("type"),
        "parent": None if parent is None else parent.get("link"),
        "child": None if child is None else child.get("link"),
        "lower": None if limit is None or limit.get("lower") is None else float(limit.get("lower")),
        "upper": None if limit is None or limit.get("upper") is None else float(limit.get("upper")),
        "mimic_joint": None if mimic is None else mimic.get("joint"),
        "mimic_multiplier": None if mimic is None else float(mimic.get("multiplier", "1")),
        "mimic_offset": None if mimic is None else float(mimic.get("offset", "0")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rm65-urdf", type=Path, required=True)
    parser.add_argument("--rm65-mesh-dir", type=Path, required=True)
    parser.add_argument("--gripper-urdf", type=Path, required=True)
    parser.add_argument("--gripper-mesh-dir", type=Path, required=True)
    parser.add_argument("--gripper-root-link", default="base_link")
    parser.add_argument("--gripper-name-prefix", default="tool_")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--mount-xyz", type=parse_vector, default="0 0 0")
    parser.add_argument("--mount-rpy", type=parse_vector, default="0 0 0")
    parser.add_argument("--gripper-min-mass-kg", type=float, default=0.0)
    parser.add_argument("--gripper-min-diagonal-inertia", type=float, default=0.0)
    parser.add_argument("--zero-gripper-cross-inertia", action="store_true")
    parser.add_argument(
        "--add-4c2-contact-pads",
        action="store_true",
        help="Add two thin, box-shaped collision pads for bilateral grasp diagnostics.",
    )
    parser.add_argument(
        "--4c2-contact-pad-size-m",
        dest="contact_pad_size_m",
        type=float,
        nargs=3,
        metavar=("X", "Y", "Z"),
        default=(0.025, 0.010, 0.020),
        help="Box dimensions in each second-finger link frame (default: 0.025 0.010 0.020).",
    )
    parser.add_argument(
        "--preserve-mimic",
        action="store_true",
        help="Keep source mimic tags. The default strips them for stable software-coupled drives in PhysX.",
    )
    args = parser.parse_args()

    arm_tree = ET.parse(args.rm65_urdf.expanduser())
    gripper_tree = ET.parse(args.gripper_urdf.expanduser())
    arm = arm_tree.getroot()
    gripper = gripper_tree.getroot()
    if arm.tag != "robot" or gripper.tag != "robot":
        raise ValueError("both input files must have a <robot> root")

    original_gripper_links = {link.get("name") for link in gripper.findall("link")}
    if args.gripper_root_link not in original_gripper_links:
        raise ValueError(f"gripper URDF must contain root link {args.gripper_root_link!r}")
    gripper_meshes = rewrite_meshes(gripper, args.gripper_mesh_dir.expanduser())
    link_map, joint_map = prefix_gripper_names(gripper, args.gripper_name_prefix)
    if args.gripper_min_mass_kg < 0 or args.gripper_min_diagonal_inertia < 0:
        raise ValueError("gripper mass and inertia floors must be non-negative")
    if any(value <= 0.0 for value in args.contact_pad_size_m):
        raise ValueError("4C2 contact-pad dimensions must be positive")
    inertial_changes = regularize_gripper_inertials(
        gripper,
        args.gripper_min_mass_kg,
        args.gripper_min_diagonal_inertia,
        args.zero_gripper_cross_inertia,
    )
    contact_pads = (
        add_4c2_contact_pads(gripper, args.gripper_name_prefix, tuple(args.contact_pad_size_m))
        if args.add_4c2_contact_pads
        else []
    )
    gripper_root_link = link_map[args.gripper_root_link]
    source_mimic_follower_joints = sorted(
        joint.get("name") for joint in gripper.findall("joint") if joint.find("mimic") is not None
    )
    if not args.preserve_mimic:
        for joint in gripper.findall("joint"):
            mimic = joint.find("mimic")
            if mimic is not None:
                joint.remove(mimic)

    arm_links = {link.get("name") for link in arm.findall("link")}
    gripper_links = {link.get("name") for link in gripper.findall("link")}
    arm_joints = {joint.get("name") for joint in arm.findall("joint")}
    gripper_joints = {joint.get("name") for joint in gripper.findall("joint")}
    duplicate_links = sorted(arm_links & gripper_links)
    duplicate_joints = sorted(arm_joints & gripper_joints)
    if duplicate_links or duplicate_joints:
        raise ValueError(f"duplicate names: links={duplicate_links}, joints={duplicate_joints}")
    if "link_6" not in arm_links:
        raise ValueError("RM65 URDF must contain end link 'link_6'")

    arm_meshes = rewrite_meshes(arm, args.rm65_mesh_dir.expanduser())

    for child in list(gripper):
        if child.tag in {"link", "joint", "gazebo", "transmission", "material"}:
            arm.append(copy.deepcopy(child))

    mount = ET.Element("joint", {"name": "rm65_to_4c2", "type": "fixed"})
    ET.SubElement(mount, "origin", {"xyz": args.mount_xyz, "rpy": args.mount_rpy})
    ET.SubElement(mount, "parent", {"link": "link_6"})
    ET.SubElement(mount, "child", {"link": gripper_root_link})
    arm.append(mount)
    arm.set("name", "rm65_4c2")

    ET.indent(arm_tree, space="  ")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    arm_tree.write(output, encoding="utf-8", xml_declaration=True)

    combined_links = [link.get("name") for link in arm.findall("link")]
    combined_joint_elements = arm.findall("joint")
    report = {
        "robot_name": arm.get("name"),
        "output_urdf": str(output),
        "mount": {"parent": "link_6", "child": gripper_root_link, "xyz": args.mount_xyz, "rpy": args.mount_rpy},
        "gripper_name_prefix": args.gripper_name_prefix,
        "gripper_inertial_regularization": {
            "minimum_mass_kg": args.gripper_min_mass_kg,
            "minimum_diagonal_inertia_kg_m2": args.gripper_min_diagonal_inertia,
            "zero_cross_inertia": args.zero_gripper_cross_inertia,
            "changed_links": inertial_changes,
        },
        "gripper_link_name_map": link_map,
        "gripper_contact_pads": contact_pads,
        "gripper_joint_name_map": joint_map,
        "gripper_control": {
            "master_joint": joint_map.get("gripper_joint"),
            "follower_joints": source_mimic_follower_joints,
            "source_uses_mimic": True,
            "output_preserves_mimic": args.preserve_mimic,
            "simulation_mode": "physx_mimic" if args.preserve_mimic else "software_coupled_joint_targets",
            "note": "The source 4C2 has one command joint and five mimic followers.",
        },
        "link_count": len(combined_links),
        "joint_count": len(combined_joint_elements),
        "movable_joint_count": sum(j.get("type") != "fixed" for j in combined_joint_elements),
        "links": combined_links,
        "joints": [joint_record(joint) for joint in combined_joint_elements],
        "mesh_count": len(arm_meshes) + len(gripper_meshes),
        "meshes": arm_meshes + gripper_meshes,
    }
    if args.report:
        report_path = args.report.expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
