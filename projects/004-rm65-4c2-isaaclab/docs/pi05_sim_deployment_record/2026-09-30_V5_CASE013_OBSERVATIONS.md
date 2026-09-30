# Case013 observation/action sensitivity evidence

Baseline3065b9c; runtime unchanged. Existing analyzer compared post-fix run2 failure to run3 success using exact captured images and actual OpenPI preprocessing. At224x224, external105 pixels(0.209%) and wrist271 pixels(0.540%) differ; maximum channel difference is1 on0–255 scale for each. Initial executed5x7 action maximum difference0.0013545, largest in gripper dimension; maximum arm-dimension difference0.000253886rad.

Terminal reference lift0.006794m and target error0.210011m versus candidate lift0.036436m,error0.007197m. Small initial input/action differences coexist with divergent closed-loop outcomes; this is sensitivity evidence, not proof that those first-frame pixels alone cause the failure. Physical/noise hashes and saved capture checks are verified in results/rm65_v5_case013_observation_comparison.json.

Conclusion for next correction: robustness around grasp acquisition and near-target placement matters more than extending action time or selecting2000 checkpoint, neither of which improved the observed gate. Any training/controller changes require new independent conditions; do not apply unvalidated image quantization just to force hash equality. No code/config changes or real robot commands.
