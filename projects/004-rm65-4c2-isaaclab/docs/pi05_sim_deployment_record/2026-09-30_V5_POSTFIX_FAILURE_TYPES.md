# Post-fix flip conditions and incremental archive

Baseline660dcf8; runtime unchanged. Inspected failed reports from independent backups. Run1/case008: lift0.0358968m, final XY error0.0535976m (3.60mm beyond0.05m threshold), drift0,120 chunks, no safety abort. Run2/case013: lift0.006794m (below0.02m threshold), XY error0.193983m,120 chunks, no safety abort. These are respectively near-target placement failure and insufficient lift/transport, not the same failure mode. Do not loosen tolerances to hide either outcome.

Run3 raw archive completed: SHA25610619178d35c6ab50b850c4082befe1aa5930023d552599b7f7a38575d0b571f. Transfer started to RM65_DATA_BACKUP_DO_NOT_GIT/v5_safetyfix_run3_2026_09_30; independent validation pending. Next use these distinctions to scope future correction, while retaining failed current-version repeatability gate. No control/physics changes or real robot commands.
