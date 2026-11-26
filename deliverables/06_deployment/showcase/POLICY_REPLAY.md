# Prompt delivery replay and pilot decision

## Retrospective replay

Use the frozen HW5 new-user flags and the fixed rule on the same 5,627 unique check-ins. For each participant, sort by prompt time and use the first observed reference timezone. The cooldown starts at actual simulated delivery and continues across midnight. The day cap takes precedence when both checks would suppress a candidate. The report includes all observed participant-days, including zero-delivery days. [Aggregate replay](../build/results/hw6_policy_replay.json)

```powershell
$demoPython = Join-Path $env:LOCALAPPDATA 'nudgewell-hw6/Scripts/python.exe'
& $demoPython -B deliverables/06_deployment/build/replay_policy.py --csv ../Capstone_Digital_Addiction/data/raw/awaremind/full_data_all_feature.csv
```

The output includes candidate counts, simulated deliveries, cap and cooldown suppressions, positives reached and missed, and negative-label deliveries. A separate count records deliveries for answers of at least 6. Negative-label delivery and that narrower count are label-based proxies for unwanted interruption. The release does not contain participant responses to NudgeWell nudges. Age-band and release-coded gender summaries are written to the ignored `run/` directory for internal denominator review.

On **638 observed participant-days**, the replay produced the following counts. The refined policy simulated 162 fewer deliveries and reached 50 fewer positive check-ins. The rule reached more positives per simulated delivery in this replay.

| Outcome | HW5 refined | Fixed rule |
|---|---:|---:|
| Candidate flags | 939 | 1,375 |
| Simulated deliveries | 740 | 902 |
| Deliveries per observed participant-day | 1.16 | 1.41 |
| Cooldown suppressions | 68 | 91 |
| Cap suppressions | 131 | 382 |
| Positive labels reached | 148 | 198 |
| Positive labels missed | 570 | 520 |
| Negative-label deliveries | 592 | 704 |
| Deliveries when the answer was 6 or higher | 533 | 596 |

## Prospective design before a pilot

1. Verify sensing and privacy on an approved adult-only device cohort in silent mode. Check features against a scripted reference, feedback and label availability, observed hours of coverage, candidate burden by subgroup, pause, withdrawal and deletion. Record permissions for all fitted artifacts and obtain institutional and participant approval before enrollment.
2. At eligible moments after the cap and cooldown, compare a short, dismissible offer with a quiet condition using 1:1 within-person random assignment. Fix eligibility and apply the same scheduling limits to randomized opportunities in both conditions. Record assignment separately from whether an offer appeared. Use the same sampling schedule in both conditions for any research questions.
3. Prespecify three outcomes. Measure **helpfulness** from an optional post-offer rating and report its response denominator. Measure **unwanted interruption** using a separately sampled burden rating and report dismissals separately. Compare **subsequent phone behavior** using remaining session time in both randomized conditions, clustered by participant. Report missingness and subgroup denominators. Review burden and withdrawal before expanding enrollment.

Replay outcomes describe sampled historical check-ins. A pilot decision requires verified device controls, sufficient coverage, and a prospective comparison.

