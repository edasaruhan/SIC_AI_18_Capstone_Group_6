# Final showcase demo: "Deniz'in bir günü"

A phone-shaped page that plays one invented weekday for an illustrative user. Every check-in is scored through the unchanged HW6 `POST /v1/predict` route, using a separately versioned **illustrative, hand-set** model (`fixture_v2.py`, `showcase-illustrative-v2`). Its weights follow only the published direction: higher at night and as a session goes on. The cap of 3 a day and the 30-minute cooldown come from the tested `delivery_decisions` in `../../build/replay_policy.py`. No research data, fitted model or internet connection is used, and the HW6 code, fixture v1 and its 16 tests are unchanged.

| File | Purpose |
|---|---|
| `serve_showcase.py` | Serves the page and the HW6 API from `127.0.0.1` with an ephemeral key. `--record` refreshes `day.js`. |
| `index.html` | The page, in Turkish, with no external assets. |
| `scripted_day.json` | The invented day. App names are shown on screen only; they are never sent to the model. |
| `day.js` | Recorded API responses. The page falls back to these when no server is reachable, e.g. when `index.html` is opened from disk. |
| `fixture_v2.py` | The illustrative model. |
| `tests/` | 7 checks: model shape, a separate version, each policy outcome, that the recording matches the live API, endpoints, offline assets. |

## Run

From the repository root, with the HW6 environment ([setup](../../README.md)):

```powershell
& "$env:LOCALAPPDATA\nudgewell-hw6\Scripts\python.exe" -B deliverables/06_deployment/showcase/demo_web/serve_showcase.py
```

```zsh
~/.venvs/nudgewell-hw6/bin/python -B deliverables/06_deployment/showcase/demo_web/serve_showcase.py
```

The browser opens at `http://127.0.0.1:8767/`.

| Key | Action |
|---|---|
| Space | Play / pause |
| R | Restart |
| 1 / 2 | Answer the card ("Evet, devam" / "Hayır, bırakıyorum") |

The day stops at the third question (23:10) until the card is answered. The chip at the top right shows **Canlı yerel API** or **Kayıtlı yanıtlar**.

Tests:

```powershell
& "$env:LOCALAPPDATA\nudgewell-hw6\Scripts\python.exe" -B -m unittest discover -s deliverables/06_deployment/showcase/demo_web/tests -v
```

After any change to `scripted_day.json` or `fixture_v2.py`, run `serve_showcase.py --record`, then the tests.

## Fallback video and deck

1. Record one run of the page (Windows: Win+Alt+R; macOS: Cmd+Shift+5).
2. Save it as `deliverables/06_deployment/showcase/NudgeWell_Demo_Yedek.mp4`.
3. Rebuild the Turkish deck, which embeds the video on hidden slide 5:

```powershell
$env:NODE_PATH = (npm root -g); node deliverables/06_deployment/build/build_showcase_tr.js
```

The numbers on slides 2 and 6 come from `../../build/results/showcase_headline_checks.json`, which `../../build/showcase_headline_checks.py` writes on the data machine. That file holds aggregates only. The fixed-rule row in it is a descriptive check outside the frozen HW5 protocol.
