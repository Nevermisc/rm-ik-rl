# V5 pre-fall gripper observations

Baseline8be698e; no code changes. Inspected recorded observation/action arrays in original run1 case013. Frame322 cube z0.7630m, gripper observation0.8478 and action0.9223; frame325 z0.7542m, gripper0.8165 and action0.5701; frame328 z0.6883m, gripper0.6608 and action0.7498. Cube y moves from0.00935 to0.02737m during this interval, followed by gravity-like falling.

The command becomes less closed near the loss-of-support interval, but the action does not meet the explicit release threshold0.12. Thus the current evidence suggests loss of grasp/support during variable grip commands, not a confirmed release-supervisor activation. Contact forces are absent from the inspected task report; causality is unproven. Do not fix by silently changing grip thresholds or physics, or claim the recorded near-closed gripper guarantees contact.

Next: inspect policy observation images or add separately versioned contact diagnostics if necessary. Existing v5 result remains a bounded simulation deployment with documented failures; all raw evidence preserved.
