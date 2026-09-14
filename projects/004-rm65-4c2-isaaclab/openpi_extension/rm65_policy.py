"""OpenPI input/output transforms for RM65-B with a scalar 4C2 gripper state."""

from __future__ import annotations

import dataclasses

import einops
import numpy as np

from openpi import transforms
from openpi.models import model as _model


def _parse_image(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if np.issubdtype(image.dtype, np.floating):
        image = np.clip(255 * image, 0, 255).astype(np.uint8)
    if image.shape[0] == 3:
        image = einops.rearrange(image, "c h w -> h w c")
    if image.ndim != 3 or image.shape[-1] != 3:
        raise ValueError(f"expected an RGB image, got {image.shape}")
    return image


@dataclasses.dataclass(frozen=True)
class RM65Inputs(transforms.DataTransformFn):
    """Convert repository-level RM65 fields to the generic pi0.5 model fields."""

    model_type: _model.ModelType

    def __call__(self, data: dict) -> dict:
        joints = np.asarray(data["observation/joint_position"])
        gripper = np.asarray(data["observation/gripper_position"])
        if joints.shape != (6,):
            raise ValueError(f"expected six RM65 joints, got {joints.shape}")
        if gripper.ndim == 0:
            gripper = gripper[np.newaxis]
        if gripper.shape != (1,):
            raise ValueError(f"expected one gripper value, got {gripper.shape}")

        base_image = _parse_image(data["observation/external_image"])
        wrist_image = _parse_image(data["observation/wrist_image"])
        match self.model_type:
            case _model.ModelType.PI0 | _model.ModelType.PI05:
                names = ("base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb")
                images = (base_image, wrist_image, np.zeros_like(base_image))
                image_masks = (np.True_, np.True_, np.False_)
            case _:
                raise ValueError(f"unsupported model type for RM65: {self.model_type}")

        result = {
            "state": np.concatenate([joints, gripper]),
            "image": dict(zip(names, images, strict=True)),
            "image_mask": dict(zip(names, image_masks, strict=True)),
        }
        if "actions" in data:
            actions = np.asarray(data["actions"])
            if actions.shape[-1] != 7:
                raise ValueError(f"expected seven RM65 action values, got {actions.shape}")
            result["actions"] = actions
        if "prompt" in data:
            prompt = data["prompt"]
            result["prompt"] = prompt.decode("utf-8") if isinstance(prompt, bytes) else prompt
        return result


@dataclasses.dataclass(frozen=True)
class RM65Outputs(transforms.DataTransformFn):
    """Expose six absolute joint targets and one normalized gripper target."""

    def __call__(self, data: dict) -> dict:
        actions = np.asarray(data["actions"])
        return {"actions": actions[..., :7]}
