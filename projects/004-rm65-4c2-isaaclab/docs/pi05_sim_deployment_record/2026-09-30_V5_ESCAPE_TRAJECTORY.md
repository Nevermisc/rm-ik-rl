# V5 case013 trajectory investigation

Baseline797c7d8; runtime/config unchanged. Read original episode.npz cube poses for case013 across three formal runs and post-fix replay.

Run1 crosses world z=0 at recorded frame334 (16.75s), reaching recorded min z=-11.88998m. Near crossing z values at0.05s intervals:0.4237517,0.2865136,0.1247504,-0.0615377,-0.2723507,-0.5076888. The second difference is approximately-0.024525m, consistent with gravity acceleration -9.81m/s²; this suggests falling after support loss rather than establishing an explosive numerical impulse. The initial loss-of-support mechanism and ground collision configuration still need inspection.

Run2 minimum z0.74210m and run3 minimum z0.74404m: their failures did not include the same fall. Post-fix replay passed, minimum z0.66250m. Thus identical condition IDs have different physical outcomes under rendering/action variation, and the passing replay is not proof that the safety patch corrected the grasp.

Evidence retained in four raw episode roots and independent backup. Next inspect support geometry/collision setup and the first fall frames before any dynamics changes. Original evaluation results remain immutable. No robot commands or code changes.
