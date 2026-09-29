# Source support geometry inspection

Baseline d174a88; no code/config changes. Source platform is 0.120 x 0.018 x 0.020m, top z0.733m; block dimensions0.060 x0.040 x0.025m. spawn_platform enables collision properties. The runner explicitly creates source/target platforms but contains no ground-plane creation. This does not exclude geometry embedded in loaded USD.

Case013 has y offset -0.005m from nominal -0.00000383m, so source platform y extent is approximately[-0.01400383,0.00399617]. During observed fall, cube center y progresses0.04833 to0.08327m and z crosses zero. This supports loss of the narrow support followed by gravity, but cube orientation, contact geometry and initial slip need further examination to establish causality.

Do not enlarge support or add floor to the original evaluation silently: either alters physical conditions and requires separately versioned data/evaluation. Existing safety patch only avoids extra settling after abort. Next inspect pre-fall pose/contact/action sequence and consider earlier diagnostic abort criteria without reclassifying failures as successes. No real robot commands.
