"""OpenPI data and LoRA training configuration for RM65-B + 4C2."""

from __future__ import annotations

import dataclasses
import pathlib

from typing_extensions import override

from openpi.models import model as _model
from openpi.models import pi0_config
from openpi.training import config as training_config
from openpi.training import weight_loaders
import openpi.transforms as transforms

from openpi_extension.rm65_policy import RM65Inputs, RM65Outputs


@dataclasses.dataclass(frozen=True)
class LeRobotRM65DataConfig(training_config.DataConfigFactory):
    """Map the RM65 LeRobot schema to the shared inference-time transform."""

    @override
    def create(
        self,
        assets_dirs: pathlib.Path,
        model_config: _model.BaseModelConfig,
    ) -> training_config.DataConfig:
        repack = transforms.Group(
            inputs=[
                transforms.RepackTransform(
                    {
                        "observation/external_image": "image",
                        "observation/wrist_image": "wrist_image",
                        "observation/joint_position": "joints",
                        "observation/gripper_position": "gripper",
                        "actions": "actions",
                        "prompt": "prompt",
                    }
                )
            ]
        )
        data_transforms = transforms.Group(
            inputs=[RM65Inputs(model_type=model_config.model_type)],
            outputs=[RM65Outputs()],
        )
        # The scripted expert stores absolute joint targets. OpenPI trains joint
        # dimensions as deltas from the current state and keeps the gripper
        # target absolute.
        delta_action_mask = transforms.make_bool_mask(6, -1)
        data_transforms = data_transforms.push(
            inputs=[transforms.DeltaActions(delta_action_mask)],
            outputs=[transforms.AbsoluteActions(delta_action_mask)],
        )
        return dataclasses.replace(
            self.create_base_config(assets_dirs, model_config),
            repack_transforms=repack,
            data_transforms=data_transforms,
            model_transforms=training_config.ModelTransformFactory()(model_config),
        )


def make_pi05_rm65_lora_config(
    *,
    repo_id: str = "local/rm65_sim",
    batch_size: int = 1,
    num_train_steps: int = 30_000,
) -> training_config.TrainConfig:
    """Build, without globally registering, the RM65 π0.5 LoRA config."""

    model = pi0_config.Pi0Config(
        pi05=True,
        action_horizon=10,
        discrete_state_input=False,
        paligemma_variant="gemma_2b_lora",
        action_expert_variant="gemma_300m_lora",
    )
    return training_config.TrainConfig(
        name="pi05_rm65_lora",
        model=model,
        data=LeRobotRM65DataConfig(
            repo_id=repo_id,
            base_config=training_config.DataConfig(prompt_from_task=True),
        ),
        weight_loader=weight_loaders.CheckpointWeightLoader(
            "gs://openpi-assets/checkpoints/pi05_base/params"
        ),
        freeze_filter=model.get_freeze_filter(),
        ema_decay=None,
        batch_size=batch_size,
        num_workers=0,
        num_train_steps=num_train_steps,
        wandb_enabled=False,
    )
