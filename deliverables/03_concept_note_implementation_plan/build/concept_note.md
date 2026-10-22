---
title: NudgeWell – Predicting the moments when people want to put their phone down but keep going
team_heading: Team Members (Group 6)
members: Yusuf Ersel Kara · Bahadır Maral · Çağla Eryılmaz · Fatih Mehmet Menteşe · Damla Nur Öcal
doc_title: NudgeWell: Concept Note and Implementation Plan
subject: SIC AI Cohort 18 Digital Addiction Capstone, homework 3
---

## 1. Project Overview

NudgeWell is a machine-learning system that recognizes, during a single phone session, the moment when a person feels they should stop using their phone but is likely to keep going. This moment is called the in-session *intention–behavior gap* (Zheng & Choe, 2026). When the model is confident that such a moment is happening, an opt-in Android app offers one short alternative that the user chose in advance, such as a short walk or getting ready for bed, and says in one line why it appeared. At all other times it stays quiet. Our target group is adults who use their smartphones heavily (about three hours a day or more) and want to cut down.

**The problem.** Current digital-wellbeing tools are built around time: daily limits, app timers and bedtime schedules (Apple, n.d.; Google, n.d.). They interrupt purposeful use, such as navigation or work messages, and stay silent at the moment that matters: when a person has already decided to stop but carries on. Time is also a weak marker of harm. In 10,099 US adults, objectively logged phone use had weak or null associations with mood (Winbush et al., 2025). Loss of control is the better marker, and it is the core of the World Health Organization's definition of gaming disorder (World Health Organization, n.d.). The gap is common. In the AwareMind study, when people said they should stop (answers 1–5 on a 1–10 scale), they still kept using the phone for more than five more minutes in 52.6% of cases. That is almost as often as when they wanted to continue (50.9%), according to our analysis of the study's data (Zheng & Choe, 2026).

**Relevance to the SDGs.** NudgeWell contributes to **SDG 3, Good Health and Well-being**, and specifically to **target 3.4**, which includes promoting mental health and well-being (United Nations, n.d.). Problematic smartphone use is consistently associated with depression and, less strongly, with anxiety (Elhai et al., 2017), and night-time use characterizes the usage profiles with lower well-being (Katevas et al., 2018). NudgeWell works at the prevention end of this target. It is a free, private self-help tool that supports self-control before problems escalate, and it points people to professional help when they need more: Yeşilay's YEDAM counseling centers and the 115 line (YEDAM, n.d.).

**Potential impact.**
- **For users:** fewer unwanted minutes, especially at night, and fewer irrelevant interruptions than a timer, because prompts appear only when the user's own intention is at stake.
- **For Yeşilay:** a low-cost prevention tool that complements its education programs and counseling. Because it runs entirely on the phone, it supports KVKK's data-minimization principle and scales to many users without server costs.
- **For research:** the first benchmark of temporal and personalized models of the gap beyond the published random forest, with negative results reported honestly.

NudgeWell does not diagnose addiction, and we do not claim that its prompts change behavior; testing that would require a separate user study.

## 2. Objectives

**Aim.** To predict, from signals available during a session, when a person is likely to keep using the phone against their own intention, and to turn these predictions into rare, well-timed prompts that the person would endorse.

Table 1. Specific objectives and how we will measure them.
<!-- widths: 0.7,2.6,5.6,5.1 -->
| # | Objective | What we will do | Success criterion |
|---|---|---|---|
| O1 | Leakage-safe data pipeline | Prepare the AwareMind data (5,772 check-ins from 37 adults): remove every column derived from the outcome, build features known at the moment of the check-in, and order each person's history in time | Reproduces the published high-gap share (14.9%, already confirmed) and the paper's random-forest benchmark (MAE 0.794 for new users; 0.599 for the combined model) |
| O2 | Advanced temporal model | Train a compact temporal deep-learning model (a temporal convolutional network, with a GRU for comparison) that reads each person's earlier check-ins in time order, together with the usage history recorded before each one, in global, personal and combined variants | Lower error than the best published model (combined random forest: MAE 0.599, R² 0.208) on the same evaluation splits |
| O3 | Fast personalization | Adapt the model to a new user from their first check-ins, by fine-tuning or re-calibrating it | A learning curve showing after how many check-ins a new user's model beats the global one (R² 0.035 in the paper) |
| O4 | Low-burden prompt policy | Calibrate the predicted probabilities, and fix a decision threshold, a daily prompt budget and a cooldown before testing | At the same alert rate as the combined fixed rule in Table 3, higher precision and recall than that rule (25.1% and 41.9%) |
| O5 | Explainable, private prototype | Run the model on the phone inside an opt-in Android app built on the Eşik prototype from the August 2026 SIC hackathon; show a one-line reason for each prompt (from SHAP values) and the user's own alternatives | Working end-to-end demo at the final showcase; no usage data leaves the phone; every prompt can be dismissed with one tap |
| O6 | Responsible use | Follow KVKK (explicit consent, data minimization, full deletion), use non-stigmatizing language, make no diagnosis, and keep a link to YEDAM and the 115 line one tap away | Written reuse permission from the AwareMind authors before training; privacy and ethics checklist completed before the demo |

**How this addresses the problem.** Together, the objectives move digital-wellbeing support from "How long have you been on your phone?" to "Do you still want to be?" O1–O3 target the two weaknesses of the only existing model of the gap: it ignores the order of events, and it barely works for new users. O4 keeps NudgeWell from becoming one more stream of notifications. O5 and O6 make the result usable, explainable and safe for the people Yeşilay serves.

## 3. Background

### 3.1 Digital addiction as loss of control

Digital addiction is increasingly understood as a loss of control rather than an amount of use. The WHO's ICD-11 definition of gaming disorder rests on three features: impaired control, increasing priority given to the behavior, and continuation despite negative consequences (World Health Organization, n.d.). Smartphone addiction is not a formal diagnosis, but research applies the same lens. A meta-analysis covering 24 countries found that it is increasing worldwide (Olson et al., 2022), and problematic smartphone use is consistently linked with depression and, less strongly, with anxiety (Elhai et al., 2017).

In Türkiye, exposure is close to universal: 92.3% of people aged 16–74 used the internet in 2026, according to TÜİK's household survey (Daily Sabah, 2026). Yeşilay treats technology addiction alongside alcohol, tobacco, substance and gambling addiction. Its primary-prevention education program, TBM, includes technology among its modules (Yeşilay, n.d.), and its YEDAM centers offer free support for technology addiction to anyone aged 12 or older, with appointments through the 115 line (YEDAM, n.d.).

### 3.2 Why screen time is the wrong target

Large studies based on usage logs show that minutes of use say little about harm. Objectively measured use had weak or null links with mood in 10,099 US adults (Winbush et al., 2025). Intense use alone did not predict lower well-being, although night-time use marked the profiles with lower well-being (Katevas et al., 2018). People also describe habitual, passive use as meaningless and as reducing their sense of autonomy (Lukoff et al., 2018). What matters is *unwanted* use: use that continues against the person's own intention.

The AwareMind study measured exactly this (Zheng & Choe, 2026). Thirty-seven US adults who wanted to cut down ran a logging app for at least two weeks. During some sessions it asked them to complete the sentence "I should ___ using my phone now" on a scale from 1 (stop) to 10 (continue), and then recorded how long they kept using the phone. Our earlier analysis of these data, in the group's literature, data and technology review, found the following:
- **High-gap moments** (leaning toward stopping, yet using the phone for more than five more minutes) make up 14.9% of check-ins.
- They peak **at night**: 33.7% of check-ins between midnight and 6 am, against 12.6% from 9 am to 6 pm.
- They are most frequent in **social media** (23.7%).
- They are **strongly person-specific**. Individual shares range from 0% to 97%, and 44% of the variation lies between people (intraclass correlation 0.44).

### 3.3 Existing solutions and initiatives

Table 2. Existing approaches to unwanted smartphone use.
<!-- widths: 2.3,3.3,2.7,2.3,3.4 -->
| Approach | Examples | What triggers support | Adapts to the person? | Limitation for unwanted use |
|---|---|---|---|---|
| Built-in time tools | Apple Screen Time; Google Digital Wellbeing (Apple, n.d.; Google, n.d.) | Daily limits, app timers, schedules | No; the user sets fixed limits | React to minutes, not to intention; interrupt purposeful use |
| Digital self-control apps | Timers, blockers and lock-outs (Lyngs et al., 2019) | Opening an app, or elapsed time | Rarely | Mostly generic; real effectiveness still poorly understood (Monge Roffarello & De Russis, 2023) |
| Friction apps | *one sec* (Haliburton et al., 2024) | Opening a chosen app | No | Fewer and more intentional openings, but users take periodic breaks from it |
| Just-in-time research systems | *TypeOut* (Xu et al., 2022); *Time2Stop* (Orzikulova et al., 2024) | Unlocking the phone; timing learned from usage and feedback | Time2Stop learns from feedback | Decide *when* to interrupt, not whether the person wants to stop |
| Prevention and counseling | Yeşilay's TBM program; YEDAM and the 115 line (Yeşilay, n.d.; YEDAM, n.d.) | Education; self-referral | Counselor-led | Essential, but absent at the moment of use |
| Prediction of the gap | AwareMind models (Zheng & Choe, 2026) | Research only | A personal random forest | Random forests only; R² of 0.035 for new users |

The evidence for lightweight, just-in-time support is encouraging. *TypeOut* cut app usage by more than half (Xu et al., 2022), and the adaptive, explainable interventions of *Time2Stop* reduced app visits by 7.0–8.9% (Orzikulova et al., 2024). However, no deployed tool predicts the user's own wish to stop, and the only model of the gap is a random forest that barely generalizes to new users. NudgeWell addresses this gap.

### 3.4 Why a machine-learning approach

1. **No single signal is enough.** Table 3 tests fixed rules on AwareMind's check-ins. Even a rule that fires on any of the three strongest signals would interrupt a quarter of all check-ins, yet only one in four of those interruptions would land on a high-gap moment, and it would still miss 58% of them. A model can combine many weak, interacting signals into a single estimate.
2. **The problem is personal.** With high-gap shares ranging from 0% to 97% between people, no single rule fits everyone. In the AwareMind benchmark, a model that also learned from each person's own data reached an R² of 0.208, against 0.035 for a model trained only on other people (Zheng & Choe, 2026).
3. **History matters.** The paper's most important features for the gap include the length of the last session and the average length of earlier sessions that day (Zheng & Choe, 2026). Temporal models can learn from the ordered sequence of a person's earlier check-ins, in addition to these hand-made summaries.
4. **Decisions need probabilities.** A calibrated probability lets us choose a threshold and a daily budget, and measure the trade-off between helping and interrupting. A fixed rule offers no such control.
5. **It can stay private.** Compact models run on the phone itself through runtimes such as LiteRT and ONNX Runtime (Google AI Edge, n.d.; ONNX Runtime, n.d.). Behavioral data therefore never has to leave the device, which matters for sensitive data under KVKK.

Table 3. How well fixed rules capture high-gap moments in AwareMind (5,772 check-ins; 14.9% are high-gap moments).
<!-- widths: 6.4,2.6,3.2,3.2 -->
| Fixed rule: alert when… | Check-ins flagged | Precision (flagged that were high-gap) | Recall (high-gap moments caught) |
|---|---|---|---|
| it is night (midnight to 6 am) | 6.8% | 33.7% | 15.5% |
| a social-media app is open | 15.7% | 23.7% | 25.0% |
| the session has lasted more than 10 minutes | 5.7% | 21.6% | 8.3% |
| more than 3 hours of screen time today (the study's threshold for heavy use) | 31.6% | 22.7% | 48.2% |
| **any of the first three (combined fixed rule)** | **24.9%** | **25.1%** | **41.9%** |

Note. Our analysis of the AwareMind data (Zheng & Choe, 2026). Rates are computed over check-in moments, which the study sampled within sessions, not over every minute of use.

Machine learning here is a decision aid, not a diagnosis. People who need more than a prompt are directed to YEDAM's counselors and the 115 line.

## 4. Methodology

NudgeWell is a supervised learning problem on time-ordered data. Each AwareMind check-in is one example: the inputs describe the moment just before the question appeared, and the outputs describe what happened next. Every model is evaluated with the protocol of the AwareMind paper, so our results can be compared directly with its benchmark (Zheng & Choe, 2026).

### 4.1 Targets, inputs and leakage control (O1)

**Targets.** The model has two outputs. The first is the continuous intention–behavior gap released with the data, standardized (z-scored) as in the paper. It is the benchmark target and is scored with MAE and R². The second is the probability of a high-gap moment (an answer of 1–5 followed by more than five more minutes of use; 14.9% of check-ins), which the prompt policy acts on. Reproducing the paper's random-forest results (O1) confirms that our target and splits match theirs.

**Inputs.** We use only information available before the question appeared:
- hour and weekday (cyclically encoded) and a night flag;
- the category of the app in use, with an explicit "not recorded" level and a missingness flag for the 12.4% of check-ins without one;
- how long the session and the current app episode had lasted, taps and scrolls, and physical activity;
- screen time so far that day, the length of the previous session and the average length of earlier sessions that day, which the paper found among the strongest predictors (Zheng & Choe, 2026).

Age and gender, which the paper also used, are optional inputs whose effect we report separately.

**Leakage control.** We remove the answer itself, every remaining-time field, the lock time, an undocumented rescaled copy of the outcome and anything computed after the check-in, and a unit test fails the pipeline if any of them returns. An earlier check-in may contribute its answer and outcome only if its session had ended before the current one began; a check-in from the same session still has an unknown outcome at that moment. Durations are log-transformed, and scaling statistics come only from the training data of each split.

### 4.2 Evaluation protocol

We copy the paper's three settings (Zheng & Choe, 2026):
- **New users (global):** leave-one-participant-out (LOPO) cross-validation. R² is computed against the mean of the other participants.
- **Personal:** for each person, models start after their first seven days and are retrained daily: days 1–7 predict day 8, days 1–8 predict day 9, and so on. R² is computed against the mean of that person's earlier days.
- **Combined:** the same daily schedule, but each person's accumulated data are added to all other participants' data with ten times the weight.

Hyperparameters are tuned only on inner splits that follow the same rules, never on test days. For every comparison we report 95% confidence intervals from a bootstrap over participants and a paired comparison with the random forest on identical test days. We also break errors down by age band (18–29, 30–44, 45–64) and gender, to check that the model does not work only for some groups.

### 4.3 Models (O1, O2)

Table 4. Models compared, all under the protocol in Section 4.2.
<!-- widths: 2.6,6.4,5.0 -->
| Family | Model | Purpose |
|---|---|---|
| Baselines | Mean of the other participants; mean of the person's earlier days | The reference points behind the paper's R² values |
| Tree ensembles | Random forest (Breiman, 2001) with the paper's settings: 100 trees, maximum depth 10, at least 5 samples to split | Reproduces the published benchmark (O1) |
| Tree ensembles | XGBoost (Chen & Guestrin, 2016) | A stronger tabular baseline |
| Temporal networks | **Temporal convolutional network (TCN; Bai et al., 2018)** | Main model (O2) |
| Temporal networks | GRU (Cho et al., 2014) with the same inputs and outputs | Recurrent comparison |

**The temporal model.** For each check-in, the TCN reads the person's previous 16 check-ins in time order, which is about two days of history, since participants answered about nine a day. Each earlier check-in is described by its input features, the time elapsed since it and, if its session had already ended, its answer and outcome. The network combines this history with the current moment's features and predicts both outputs with a shared body and two heads, trained with a Huber loss on the gap and a class-weighted cross-entropy for the high-gap moment. Its dilated causal convolutions see only the past. The paper judged the dataset too small for neural networks (Zheng & Choe, 2026), so we keep the model compact (about 50,000 parameters, with dropout and early stopping) and share its weights across people. Like the random forest, it is trained in global, personal and combined variants. If it does not beat the tree models, we report that result.

### 4.4 Fast personalization (O3)

A random forest has to be retrained from scratch each day, as in the paper; a neural network can be adapted. Starting from the global TCN, we adapt it to each held-out person in two ways: by fine-tuning its output layers on the person's first *n* check-ins, and by re-calibrating its outputs with a per-person offset and scale. We repeat this for *n* = 5, 10, 20, 40 and 80 and test on the person's later days. The resulting learning curve shows after how many check-ins the personalized model beats the global one. Re-calibration is cheap enough to run on the phone, so the prototype can apply it using a few optional check-in questions, like AwareMind's, during the first week of use.

### 4.5 Calibration and prompt policy (O4)

The high-gap probability is calibrated with Platt scaling or isotonic regression on validation data (Niculescu-Mizil & Caruana, 2005), and checked with the Brier score and reliability curves. The decision threshold is fixed on validation data so that the model flags the same share of check-ins as the combined fixed rule in Table 3 (24.9%). On test data we then compare its precision and recall with that rule's 25.1% and 41.9% (O4). Finally, we replay each person's test days in time order under the full policy: at most three prompts a day and a 30-minute cooldown after each prompt. These starting values are fixed before testing, and we report how sensitive the results are to them. The simulation reports prompts per day, the share of high-gap moments reached, and the share of prompts that would have interrupted a person who wanted to continue.

### 4.6 Explanations and on-device inference (O5, O6)

Each prompt carries a one-line reason based on SHAP values (Lundberg & Lee, 2017). For the tree models, SHAP values are computed directly. For the TCN on the phone, a cheap approximation switches off one group of features at a time (about ten extra passes of the model), and we check it offline against SHAP values. The strongest group selects a sentence written in advance, such as "It is late, and this session has been long"; no generative model is involved. The trained network is exported through ONNX to ONNX Runtime Mobile or LiteRT (ONNX Runtime, n.d.; Google AI Edge, n.d.), with targets of under 1 MB and under 50 ms per prediction on a mid-range phone. The phone builds the same features from Android's UsageStatsManager events (Android Developers, n.d.) with code that mirrors the training pipeline, so no usage data has to leave the device. Model training starts only after the AwareMind authors give written permission, and no output is ever presented as a diagnosis.

## 5. Architecture Design Diagram

Figure 1 shows the system in two parts. Part A runs once, before deployment, on a laptop or Google Colab; it turns the AwareMind data into a calibrated model file. Part B runs on the user's phone whenever a session is in progress. Table 5 describes each component.

Figure 1. NudgeWell architecture: offline training (A) and the on-device runtime (B).
<!-- image: ../figures/fig1_architecture.png width=16 -->

Table 5. Components in Figure 1 and their roles.
<!-- widths: 2.9,3.4,7.7 -->
| Component | Role | Main functions |
|---|---|---|
| A. Offline pipeline | Turns AwareMind into a deployable model | Leakage audit and features (O1); training and evaluation under the paper's protocol (O2, O3); calibration and the choice of threshold, budget and cooldown (O4); export to a model file |
| 1. Sensing | Collects usage signals during a session | Reads UsageStatsManager events through a foreground service reused from Eşik; derives the time, app category, session length, taps, scrolls, physical activity and screen time so far today |
| 2. Feature builder | Turns raw events into model inputs | Mirrors the training code; uses only information available before the moment; marks missing app categories; keeps a short history of earlier check-ins |
| 3. On-device model | Estimates the gap and the high-gap probability | Runs the compact TCN through LiteRT or ONNX Runtime; applies the user's personal re-calibration |
| 4. Policy and explanation | Decides whether to prompt, and why | Prompts only above the calibrated threshold, within a budget of three prompts a day and after a cooldown; picks a one-line reason from the strongest feature group; otherwise stays quiet |
| 5. Prompt card | Talks to the user | A small Jetpack Compose card over the current app shows the reason and one alternative the user chose earlier; one tap dismisses it; the Stop or Continue answer is stored as feedback |
| 6. Privacy and safety | Protects the user in every component | Opt-in consent, adults only; all data stored on the phone (Room) and deletable at any time; no accounts and no cloud; a permanent "Get support" link to YEDAM and the 115 line |

## 6. Data Sources

NudgeWell is trained on AwareMind (Zheng & Choe, 2026; data at https://osf.io/x6yzs/), the only public dataset that pairs a person's in-the-moment intention with what they did next. Thirty-seven US adults (aged 18–64, mean 42) who used their Android phones at least three hours a day and wanted to cut down ran a logging app for at least two weeks; during some sessions it asked them to complete "I should ___ using my phone now" on a scale from 1 (stop) to 10 (continue) and then recorded how long they kept going. The public file has one row for each of the 5,772 check-ins, with the time, the app in use and its category, session and app-episode length so far, taps and scrolls, physical activity, screen time so far that day, summaries of earlier sessions, and demographics; the study's other sessions (31,349 sessions in total) appear only in those summaries. The target is the released intention–behavior gap, and 14.9% of check-ins are high-gap moments. Preprocessing removes every column derived from the outcome, keeps the 12.4% of check-ins without an app category as an explicit "not recorded" level, log-transforms skewed durations, orders each person's check-ins in time and splits the data by participant and by day (Section 4.2). The dataset has no licence on OSF, so we are asking the authors for written permission and will train models only after they agree. The one sec dataset (Haliburton et al., 2024; https://osf.io/bmjat/), with app-opening decisions from 1,039 users, has no intention labels; it is not used for training, only, optionally, for a separate analysis of how people respond to prompts. No comparable Turkish dataset exists, so transfer to Turkish users must be tested in a future pilot.

## 7. Literature Review

Recent research defines problematic smartphone use by loss of control rather than by total screen time. Self-reported use agrees only moderately with logged use, and "addiction" scales relate even more weakly to actual behavior (Ellis et al., 2019; Parry et al., 2021). In 10,099 US adults, objectively measured use showed weak or null links with mood (Winbush et al., 2025), whereas night-time use marked the user groups with lower well-being (Katevas et al., 2018). On the intervention side, digital self-control tools have a small-to-medium pooled effect on time spent (0.47), although most evaluations are short and lack control groups (Monge Roffarello & De Russis, 2023). In the one sec app, the option to dismiss the opening attempt had the strongest effect of its components (Grüning et al., 2023), and over months of real use its short frictions kept reducing opening attempts, although users took periodic breaks from it (Haliburton et al., 2024). Just-in-time adaptive interventions, which act when a person both needs support and is receptive to it, address the question of timing (Nahum-Shani et al., 2018). *Time2Stop* applied machine learning to this idea: adaptive timing with explanations made users more receptive and reduced app visits by 7.0–8.9% (Orzikulova et al., 2024), but it does not consider whether the user wants to stop. Only Zheng and Choe (2026) measure this. They show that the gap grows at night, in media apps and in longer sessions, and that combining personal and global data predicts it best, although accuracy remains limited (R² = .208 for the combined model; .035 for new users). NudgeWell builds on this benchmark with temporal models, fast personalization, calibrated prompting under a daily budget, SHAP explanations and on-device inference.

## 1. Technology Stack

Table 6. Technologies and tools.
<!-- widths: 3.0,6.2,4.8 -->
| Layer | Tools | Used for |
|---|---|---|
| Programming and data | Python 3, pandas, NumPy | Leakage audit, features, LOPO and day-forward splits |
| Machine learning | scikit-learn (random forest, calibration, metrics), XGBoost | Benchmark reproduction and tabular baselines (O1) |
| Deep learning | PyTorch | TCN and GRU; fine-tuning and re-calibration (O2, O3) |
| Explanation and analysis | SHAP, matplotlib | Feature attributions, calibration curves, figures (O4, O5) |
| Work environment | Jupyter notebooks, Google Colab (free GPU when needed), Git and GitHub | Experiments, version control, submissions |
| Model export | ONNX, ONNX Runtime Mobile or LiteRT | Running the model on the phone (O5) |
| Android prototype | Kotlin, Jetpack Compose, Android Studio; UsageStatsManager, the Activity Recognition API, a foreground service and an overlay card; Room (SQLite) | The prototype, built on the Eşik app: usage reading, prompt card, on-device storage and deletion |
| Hardware | Team laptops; at least two Android phones | Training the small models (a CPU is enough); device tests |

Eşik already provides the usage reader, the foreground service, an overlay, logging of the user's choices and on-device storage with full deletion. The prototype work can therefore concentrate on the model, the prompt policy and the prompt card.

## 2. Timeline

The plan covers four weeks, from Monday 26 October to Sunday 22 November 2026, in four stages: data preparation, model development, training and evaluation, and deployment (Figure 2). Each week ends with a milestone (see Milestones). If the course sets different dates for the data-preparation and modelling homework, the weeks shift with them and the order stays the same.

Figure 2. Gantt chart of the four-week plan. Bars are colored by the lead member, and "+" marks a shared task; diamonds mark milestones M1–M4.
<!-- image: ../figures/fig2_gantt.png width=16 -->

**Task distribution.** Every member owns one work-stream for the whole project, and shared tasks name both people (Table 7). Bahadır Maral is responsible for the core modelling work: the temporal models, personalization and the prompt policy.

Table 7. Task distribution matrix.
<!-- widths: 2.6,3.1,10.3 -->
| Member | Role | Tasks by week |
|---|---|---|
| Yusuf Ersel Kara | Tree baselines, evaluation and explanations | **Week 1:** target and class-balance analysis<br>**Week 2:** random forest reproduction (O1); XGBoost; TCN and GRU, with Bahadır<br>**Week 3:** bootstrap intervals; fairness by age and gender; calibration, with Bahadır<br>**Week 4:** SHAP reasons (O5) |
| Bahadır Maral | Temporal models, personalization and prompt policy | **Week 1:** licence request to the AwareMind authors; TCN and GRU design; Eşik walkthrough with Damla<br>**Week 2:** TCN and GRU, global variant (O2), with Ersel<br>**Week 3:** personal and combined variants; personalization learning curve (O3); calibration and prompt-budget simulation (O4), with Ersel<br>**Week 4:** export to LiteRT or ONNX; on-device integration with Damla; final report, presentation and delivery check |
| Çağla Eryılmaz | Data pipeline, EDA and features; ethics | **Week 1:** leakage audit, cleaning, time ordering; EDA refresh; feature specification<br>**Week 2:** LOPO and day-forward split pipeline; mean baselines; feature engineering<br>**Week 3:** history inputs from earlier check-ins (finished sessions only)<br>**Week 4:** privacy and ethics checklist (O6); data and ethics sections of the report |
| Fatih Mehmet Menteşe | Content design, secondary analysis and testing | **Week 1:** pool of short alternative activities<br>**Week 2:** prompt and one-line reason templates; consent and onboarding text<br>**Week 3:** optional one sec response analysis<br>**Week 4:** end-to-end scenario tests; demo script |
| Damla Nur Öcal | Android prototype and interface | **Week 1:** Eşik walkthrough with Bahadır; prompt-card and screen design<br>**Week 2:** preference screens; usage reading and on-device storage from Eşik<br>**Week 3:** trigger, cooldown, one-tap dismissal, local logging<br>**Week 4:** on-device model integration, with Bahadır; tests; demo video |

## 3. Milestones

Table 8. Milestones and completion criteria.
<!-- widths: 3.0,1.9,7.4,1.7 -->
| Milestone | Due | Completion criteria | Objectives |
|---|---|---|---|
| M1. Leakage-free dataset | Sun 1 Nov | Outcome-derived columns removed and guarded by a unit test; features limited to information before each check-in; the 14.9% high-gap share reproduced; licence request sent; the Eşik-based prototype skeleton runs on a phone | O1, O6 |
| M2. Benchmark reproduced | Sun 8 Nov | Random forest within 0.02 of the published MAE in all three settings (0.794 global, 0.612 personal, 0.599 combined); XGBoost and a first global TCN evaluated on the same splits | O1, O2 |
| M3. Models and policy evaluated | Sun 15 Nov | TCN and GRU compared with the combined random forest (MAE 0.599, R² 0.208) with 95% intervals; personalization learning curve; calibrated policy compared with the fixed rule at the same alert rate (25.1% precision, 41.9% recall); fairness table. Results are reported whether or not they meet the criteria | O2, O3, O4 |
| M4. On-device demo and delivery | Sun 22 Nov | The model runs on a phone and no usage data leaves it; each prompt shows a one-line reason and can be dismissed with one tap; privacy and ethics checklist complete; final report and demo video submitted | O5, O6 |

## 4. Challenges and Mitigations

Table 9. Anticipated challenges and how we will handle them.
<!-- widths: 2.4,5.4,6.2 -->
| Area | Challenge | Mitigation |
|---|---|---|
| Data access | AwareMind has no licence on OSF, and training needs the authors' consent | Permission is requested in week 1. Until it arrives, the pipeline is built and tested on synthetic data with the same columns. If it is refused, we report descriptive results only and ask the instructor and mentors for an alternative |
| Data quality | 12.4% of check-ins have no app category, and several columns reveal the outcome (the answer, remaining time, lock time, a rescaled copy of the outcome) | An explicit "not recorded" category with a missingness flag instead of dropped rows; a unit test that fails if an outcome-derived column is used; features restricted to information before the check-in |
| Data scope | Only the 5,772 check-ins are public; the study's other sessions appear only as summaries | The temporal model reads the sequence of earlier check-ins plus those summaries, and our claims are limited to that view |
| Model performance | 37 people is a small sample; deep models may overfit and may not beat tree models, as the paper expected (Zheng & Choe, 2026) | A compact TCN with shared weights, dropout and early stopping; participant- and day-based splits; bootstrap intervals; random forest and XGBoost as strong baselines; negative results reported |
| Model performance | Cold start: the global model barely works for new users (R² 0.035) | Personalization is the main experiment (O3); in the app, the prompt threshold stays high until enough personal data exist |
| Model performance and user experience | High-gap moments are rare (14.9%): a low threshold floods users with prompts, and a high one misses moments | Class-weighted loss and PR-AUC; calibration; a threshold fixed before testing; a daily budget and a cooldown; comparison with the fixed rule at the same alert rate |
| Generalization | The data come from 37 US adults (mean age 42); transfer to Turkish users and to younger adults is unknown | Results by age band; the limitation stated in every report; a Turkish pilot with KVKK-compliant consent as future work |
| Technical constraints | Android keeps detailed usage events for only a few days (Android Developers, n.d.), iOS does not expose raw usage logs, and on-device models must be small and fast | Android-first design; the app keeps its own minimal history on the phone; a model under 1 MB and under 50 ms per prediction |
| Engagement | Users of intervention apps take periodic breaks from them (Haliburton et al., 2024) | Prompts only at predicted high-gap moments, with alternatives the user chose; no claim that the app changes behavior without a user study |

## 5. Ethical Considerations

- **Not a diagnosis.** NudgeWell predicts moments, not people. It gives no clinical labels, and its wording is supportive and non-stigmatizing: "Want to take a short break?" rather than any reference to addiction.
- **Privacy and KVKK.** Use is opt-in, with explicit consent (Law No. 6698, 2016, Art. 5). Usage patterns used to infer problematic use may count as health-related, special-category data (Art. 6), one more reason why everything stays on the phone. Only app categories, timing and interaction counts are processed (data minimization, Art. 4); message contents, keystrokes and screen contents are never collected. There are no accounts, no advertising and no data sales. Users can see what is stored and delete all of it at any time (Art. 11), or pause or uninstall the app at once.
- **Data reuse and licensing.** AwareMind has no licence, so models are trained only after the authors grant written permission. Raw data are never uploaded to our public repository, and the one sec data are handled the same way.
- **Bias and fairness.** The training data come from 37 US adults (22 women and 15 men; mean age 42), so the model may work differently for other ages, genders or cultures. We report errors by age band and gender, claim no validity for Turkish users or for people under 18, and restrict the app to adults.
- **Autonomy and transparency.** The user chooses the alternatives, every prompt can be dismissed with one tap, prompts are rare (a daily budget and a cooldown), and each one says why it appeared. The app can be paused at any time.
- **Psychological safety and referral.** NudgeWell is a self-help tool, not therapy. It has no free-text input and generates no messages, and a permanent "Get support" link points to Yeşilay's YEDAM counselors and the 115 line. The wording will be reviewed with the Yeşilay mentors before any pilot.
- **Impact on the community.** A wellbeing tool can itself become a source of pressure or guilt. We therefore keep prompts rare and positive, claim no effect on behavior before a user study, and would seek ethics approval and informed consent for any pilot with real users.

## References

Android Developers. (n.d.). *UsageStatsManager*. Retrieved October 11, 2026, from https://developer.android.com/reference/android/app/usage/UsageStatsManager

Apple. (n.d.). *Use Screen Time on your iPhone and iPad*. Apple Support. Retrieved October 19, 2026, from https://support.apple.com/108806

Bai, S., Kolter, J. Z., & Koltun, V. (2018). *An empirical evaluation of generic convolutional and recurrent networks for sequence modeling* (arXiv:1803.01271). arXiv. https://doi.org/10.48550/arXiv.1803.01271

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). ACM. https://doi.org/10.1145/2939672.2939785

Cho, K., van Merrienboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder–decoder for statistical machine translation. In *Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)* (pp. 1724–1734). Association for Computational Linguistics. https://doi.org/10.3115/v1/D14-1179

Daily Sabah. (2026, August 5). *Internet use in Türkiye rises to 92.3% in 2026: Survey*. https://www.dailysabah.com/turkiye/internet-use-in-turkiye-rises-to-923-in-2026-survey/news

Elhai, J. D., Dvorak, R. D., Levine, J. C., & Hall, B. J. (2017). Problematic smartphone use: A conceptual overview and systematic review of relations with anxiety and depression psychopathology. *Journal of Affective Disorders, 207*, 251–259. https://doi.org/10.1016/j.jad.2016.08.030

Ellis, D. A., Davidson, B. I., Shaw, H., & Geyer, K. (2019). Do smartphone usage scales predict behavior? *International Journal of Human-Computer Studies, 130*, 86–92. https://doi.org/10.1016/j.ijhcs.2019.05.004

Google. (n.d.). *Manage how you spend time on your Android phone with Digital Wellbeing*. Android Help. Retrieved October 11, 2026, from https://support.google.com/android/answer/9346420

Google AI Edge. (n.d.). *LiteRT*. Retrieved October 11, 2026, from https://ai.google.dev/edge/litert

Grüning, D. J., Riedel, F., & Lorenz-Spreen, P. (2023). Directing smartphone use through the self-nudge app one sec. *Proceedings of the National Academy of Sciences, 120*(8), Article e2213114120. https://doi.org/10.1073/pnas.2213114120

Haliburton, L., Grüning, D. J., Riedel, F., Schmidt, A., & Terzimehić, N. (2024). A longitudinal in-the-wild investigation of design frictions to prevent smartphone overuse. In *Proceedings of the CHI Conference on Human Factors in Computing Systems* (pp. 1–16). ACM. https://doi.org/10.1145/3613904.3642370

Katevas, K., Arapakis, I., & Pielot, M. (2018). Typical phone use habits: Intense use does not predict negative well-being. In *Proceedings of the 20th International Conference on Human-Computer Interaction with Mobile Devices and Services* (pp. 1–13). ACM. https://doi.org/10.1145/3229434.3229441

Law No. 6698 on the Protection of Personal Data. (2016). *Official Gazette of the Republic of Türkiye*, No. 29677 (7 April 2016). English translation retrieved October 11, 2026, from https://www.kvkk.gov.tr/Icerik/6649/Personal-Data-Protection-Law

Lukoff, K., Yu, C., Kientz, J., & Hiniker, A. (2018). What makes smartphone use meaningful or meaningless? *Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, 2*(1), 1–26. https://doi.org/10.1145/3191754

Lundberg, S., & Lee, S.-I. (2017). *A unified approach to interpreting model predictions* (arXiv:1705.07874) [Paper presentation, NIPS 2017]. arXiv. https://doi.org/10.48550/arXiv.1705.07874

Lyngs, U., Lukoff, K., Slovak, P., Binns, R., Slack, A., Inzlicht, M., Van Kleek, M., & Shadbolt, N. (2019). Self-control in cyberspace: Applying dual systems theory to a review of digital self-control tools. In *Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems* (pp. 1–18). ACM. https://doi.org/10.1145/3290605.3300361

Monge Roffarello, A., & De Russis, L. (2023). Achieving digital wellbeing through digital self-control tools: A systematic review and meta-analysis. *ACM Transactions on Computer-Human Interaction, 30*(4), 1–66. https://doi.org/10.1145/3571810

Nahum-Shani, I., Smith, S. N., Spring, B. J., Collins, L. M., Witkiewitz, K., Tewari, A., & Murphy, S. A. (2018). Just-in-time adaptive interventions (JITAIs) in mobile health: Key components and design principles for ongoing health behavior support. *Annals of Behavioral Medicine, 52*(6), 446–462. https://doi.org/10.1007/s12160-016-9830-8

Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. In *Proceedings of the 22nd International Conference on Machine Learning* (pp. 625–632). ACM. https://doi.org/10.1145/1102351.1102430

Olson, J. A., Sandra, D. A., Colucci, É. S., Al Bikaii, A., Chmoulevitch, D., Nahas, J., Raz, A., & Veissière, S. P. L. (2022). Smartphone addiction is increasing across the world: A meta-analysis of 24 countries. *Computers in Human Behavior, 129*, Article 107138. https://doi.org/10.1016/j.chb.2021.107138

ONNX Runtime. (n.d.). *Deploy on mobile*. Retrieved October 11, 2026, from https://onnxruntime.ai/docs/tutorials/mobile/

Orzikulova, A., Xiao, H., Li, Z., Yan, Y., Wang, Y., Shi, Y., Ghassemi, M., Lee, S.-J., Dey, A. K., & Xu, X. (2024). Time2Stop: Adaptive and explainable human-AI loop for smartphone overuse intervention. In *Proceedings of the CHI Conference on Human Factors in Computing Systems* (pp. 1–20). ACM. https://doi.org/10.1145/3613904.3642747

Parry, D. A., Davidson, B. I., Sewall, C. J. R., Fisher, J. T., Mieczkowski, H., & Quintana, D. S. (2021). A systematic review and meta-analysis of discrepancies between logged and self-reported digital media use. *Nature Human Behaviour, 5*(11), 1535–1547. https://doi.org/10.1038/s41562-021-01117-5

United Nations. (n.d.). *Goal 3: Ensure healthy lives and promote well-being for all at all ages*. Department of Economic and Social Affairs, Sustainable Development. Retrieved October 19, 2026, from https://sdgs.un.org/goals/goal3

Winbush, A., McDuff, D., Hernandez, J., Barakat, A., Jiang, A., Heneghan, C., Nelson, B. W., & Allen, N. B. (2025). Smartphone use in a large US adult population: Temporal associations between objective measures of usage and mental well-being. *Proceedings of the National Academy of Sciences, 122*(43), Article e2427311122. https://doi.org/10.1073/pnas.2427311122

World Health Organization. (n.d.). *Gaming disorder*. Retrieved October 11, 2026, from https://www.who.int/standards/classifications/frequently-asked-questions/gaming-disorder

Xu, X., Zou, T., Xiao, H., Li, Y., Wang, R., Yuan, T., Wang, Y., Shi, Y., Mankoff, J., & Dey, A. K. (2022). TypeOut: Leveraging just-in-time self-affirmation for smartphone overuse reduction. In *CHI Conference on Human Factors in Computing Systems* (pp. 1–17). ACM. https://doi.org/10.1145/3491102.3517476

YEDAM – Yeşilay Danışmanlık Merkezi. (n.d.). *Teknoloji bağımlılığı* [Technology addiction]. Retrieved October 19, 2026, from https://www.yedam.org.tr/bagimlilik-turleri/teknoloji-bagimliligi

Yeşilay. (n.d.). *Türkiye Bağımlılıkla Mücadele Eğitim Programı (TBM)* [Türkiye addiction prevention education program]. Retrieved October 19, 2026, from https://www.yesilay.org.tr/egitim-calismalari/turkiye-bagimlilikla-mucadele-egitim-programi-tbm/

Zheng, J., & Choe, E. K. (2026). *To stop or not to stop: Exploring the intention-behavior gaps in smartphone usage* (arXiv:2609.08909) [Preprint, MobileHCI 2026]. arXiv. https://doi.org/10.48550/arXiv.2609.08909
