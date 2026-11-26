# Five-minute showcase

Use the synthetic desktop launcher and the separate keyless Eşik phone prototype. The launcher needs no internet, release data or fitted model. Keep the slides, fallback clip and APK available offline.

| Time | Presenter cue |
|---|---|
| 0:00–0:45 | Define a high-gap check-in as an answer of 5 or lower and more than five minutes of further use. HW5 found no clear new-user ranking gain. The daily offset modestly improved probability accuracy versus a personal base rate. |
| 0:45–2:15 | Run the command below. Point to ready, the version, the two scores and the aggregate counter change. Say that the fixture parameters are hand-set. |
| 2:15–3:00 | Walk through slide 4. Three example deliveries fit the daily budget. The 09:10 candidate is suppressed by cooldown and the 10:30 candidate by the cap. The API outputs a candidate flag. |
| 3:00–4:15 | On the separate Eşik phone, show the threshold overlay, an alternative and one-tap dismissal. Introduce Eşik as the earlier interaction prototype. |
| 4:15–5:00 | Close with desktop evidence and what remains before a pilot. Keep the HW6 benchmark slide handy for questions. |

Run from the repository root with the HW6 requirements installed.

```powershell
$demoPython = Join-Path $env:LOCALAPPDATA 'nudgewell-hw6/Scripts/python.exe'
& $demoPython -B deliverables/06_deployment/code/run_demo.py --rehearse
```

The command opens a temporary loopback server with an ephemeral key and stops it when the preview is complete. Monday is weekday zero. Input `(0, 0, 0)` scores about **0.3100** and stays below **0.35**. Input `(9, 1, 2)` scores about **0.4123** and crosses it. After two predictions the candidate rate is **50% of those two examples**. The separate research export has its own cutoff and performance evidence.

If the data owner clears live use of the research export, the original launcher and key commands are in the [HW6 README](../README.md). Rehearse `(9, 1, 2)` and `(1, 0, 30)` at the fitted cutoff before changing the presentation. For a desktop failure, play the [recorded synthetic responses](NudgeWell_Desktop_Fallback.mp4).

## Eşik preflight

Use the archived **Esik-v0.1.0-ci-debug.apk**, which has no Gemini key. On a suitable Android phone, use airplane mode, grant Usage Access and display-over-other-apps permission, and set a short demo limit for a harmless target app. Have a sample alternative ready. Cross the threshold, choose a scripted context, show the alternative and dismiss. The physical-phone run is pending. The available emulator already had an Eşik installation with a different signing key, so the keyless CI APK could not be rehearsed there. Use a verified offline recording if available on rehearsal day. Until the keyless build passes rehearsal, use the flow drawn on slide 5. [APK provenance](../../../../../esik-proje/Esik_Submission_2026-08-30/01-prototype/PROTOTYPE_README.md)

Run the script twice from a clean start and record the source version, runtime, outputs, phone/APK and offline outcome. Keep personal content off the mirrored screen. A future integrated claim needs a physical-device run of NudgeWell sensing, feature and score/flag parity, policy, reason, dismissal and deletion.

