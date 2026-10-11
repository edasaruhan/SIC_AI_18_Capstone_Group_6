# NudgeWell: speaker notes

**Group 6 · Idea proposal · 24 September 2026**

Total script: **531 words**, about **3:48** at a steady 140 words per minute (3:32 at 150 wpm, 4:05 at 130 wpm). That leaves about a minute of the five-minute slot as buffer.

The same notes are embedded in each slide of `NudgeWell_Group6_Pitch_Deck_EN.pptx` (Presenter View).

---

## Slide 1: Title and one-sentence idea

*Target ~30 s · 75 words*

Hi everyone, we're Group 6, and our idea is NudgeWell, an opt-in digital well-being coach. It focuses on one specific moment: when you feel you should put your phone down, but you keep going anyway. NudgeWell would estimate when that moment is likely and, only when it's confident, offer a short alternative you picked yourself, like a five-minute walk. To be clear from the start: this is a proposed prototype, not a treatment for addiction.

---

## Slide 2: The problem

*Target ~55 s · 116 words*

Many phone warnings are based on time: after, say, thirty minutes, you get an alert. But time alone can't tell purposeful use from use you regret. In the top example, someone is doing something they value, like a group-project chat, and the timer interrupts them anyway. In the bottom example, someone thinks, "I should stop," but keeps scrolling. They're still under the limit, so no alert comes. That second case is called the intention-behavior gap, and it can be measured. In the AwareMind study, 14.9 percent of sampled moments leaned toward "stop", yet phone use went on for more than five minutes. So our target isn't total screen time. It's that gap, inside a single session.

Sources (not read aloud):

- Zheng, J. & Choe, E. K. (2026). To Stop or Not to Stop: Exploring the Intention-Behavior Gaps in Smartphone Usage. https://arxiv.org/html/2609.08909v1 (DOI 10.1145/3821659).
- 14.9% is the paper's own example (Results, Fig. 4): intention to continue below 5.5 on the 1-10 scale AND remaining session length above 5 minutes. It is a descriptive figure, not a model result.

---

## Slide 3: Our proposed solution

*Target ~60 s · 133 words*

Our proposed solution works in four steps. First, you opt in and choose alternatives you'd actually enjoy: a short walk, a stretch, calling a friend. Second, during a session, NudgeWell reads only what's known so far: the time of day, the type of app, how long this session has lasted, taps and scrolls, and earlier phone use. Third, a model estimates the gap: how likely is it that you want to stop, but will keep going? Fourth, only if that estimate is confident, it offers one brief suggestion from your own list, which you can dismiss with one tap. Otherwise, it stays quiet. We would build this as an Android research prototype. It is not a diagnosis, and we are not claiming the suggestions work. Testing that would need a separate user study.

Sources (not read aloud):

- Design motivation (user control, adaptive timing): Orzikulova, A., et al. (2024). Time2Stop. https://doi.org/10.1145/3613904.3642747. It does not validate NudgeWell's predictions or suggestions.

---

## Slide 4: Dataset and research approach

*Target ~85 s · 207 words*

Our primary dataset is AwareMind, published with Zheng and Choe's 2026 study: 5,772 sampled responses from 37 adult Android users, each followed for at least two weeks. Why does it fit our question? Because it records both halves of the gap. What people said: in the middle of a session, a short pop-up asked them to complete "I should ... using my phone now", from 1, stop, to 10, continue. And what they did: how long they actually kept using the phone after answering, until it locked. Together, those give the session-level gap we want to predict. For the research, we'll use only information available before the outcome, so there is no leakage. We'll start with simple baselines, including a random forest like the paper's benchmark, and then test a small temporal model if the timestamps allow. We'll evaluate on people the model has never seen, and if the simpler model wins, we'll report that. Two limits: 37 people is a small group, so results may not generalize, and we still need to confirm permission to reuse the data. And to avoid confusion: we are not training on the Child Mind Institute dataset. It measures person-level risk and has no phone-session records of intention and outcome. Thank you.

Sources (not read aloud):

- Paper: https://arxiv.org/html/2609.08909v1 (DOI 10.1145/3821659). Data: https://osf.io/x6yzs/ (no dataset licence attached on OSF as of 23 Sep 2026, so reuse terms must be confirmed with the authors).
- Gap definition in the paper: standardized remaining session length minus standardized intention; positive = wanted to stop but continued.
- Not used for training: Child Mind Institute Problematic Internet Use data (https://www.kaggle.com/competitions/child-mind-institute-problematic-internet-use/data), which is person-level risk data without phone-session intention/outcome records.

