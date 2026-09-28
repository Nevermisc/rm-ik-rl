#!/usr/bin/env python3
"""Probe Isaac Sim's Python API for renderer accumulation controls."""

from isaaclab.app import AppLauncher


def main() -> None:
    app_launcher = AppLauncher(headless=True)
    try:
        import omni.usd

        context = omni.usd.get_context()
        methods = sorted(name for name in dir(context) if "accum" in name.lower())
        print(f"RENDERER_ACCUMULATION_METHODS={methods}", flush=True)
    finally:
        app_launcher.app.close()


if __name__ == "__main__":
    main()
