#!/usr/bin/env python3
"""Inventory rigid bodies and collision prims in an imported USD asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

from pxr import Usd, UsdPhysics


def inherited_tool_link(path: str) -> str | None:
    for part in path.split("/"):
        if part.startswith("tool_") and part != "tool_":
            return part
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    usd = args.usd.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not usd.is_file():
        raise FileNotFoundError(usd)
    stage = Usd.Stage.Open(str(usd))
    if stage is None:
        raise RuntimeError(f"failed to open USD: {usd}")

    rigid_bodies = []
    collisions = []
    for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
        path = str(prim.GetPath())
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            enabled = UsdPhysics.RigidBodyAPI(prim).GetRigidBodyEnabledAttr().Get()
            rigid_bodies.append({"path": path, "enabled": True if enabled is None else bool(enabled)})
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            enabled = UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()
            approximation = None
            if prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                approximation = UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()
            descendants = [
                {"path": str(child.GetPath()), "type": child.GetTypeName()}
                for child in Usd.PrimRange(prim, Usd.TraverseInstanceProxies())
                if child != prim
            ]
            collisions.append(
                {
                    "path": path,
                    "type": prim.GetTypeName(),
                    "enabled": True if enabled is None else bool(enabled),
                    "tool_link": inherited_tool_link(path),
                    "is_instance_proxy": prim.IsInstanceProxy(),
                    "applied_schemas": list(prim.GetAppliedSchemas()),
                    "mesh_approximation": approximation,
                    "descendants": descendants,
                }
            )

    tool_collision_links = sorted(
        {item["tool_link"] for item in collisions if item["tool_link"] is not None and item["enabled"]}
    )
    report = {
        "status": "pass" if len(rigid_bodies) >= 16 and len(tool_collision_links) >= 9 else "fail",
        "usd": str(usd),
        "rigid_body_count": len(rigid_bodies),
        "collision_prim_count": len(collisions),
        "enabled_collision_prim_count": sum(item["enabled"] for item in collisions),
        "tool_links_with_enabled_collision": tool_collision_links,
        "tool_links_with_enabled_collision_count": len(tool_collision_links),
        "rigid_bodies": rigid_bodies,
        "collisions": collisions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
