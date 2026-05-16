# Learning from Feedback Evaluation Harness

This folder contains lightweight experiment outputs for the AI Verification Copilot evaluation harness.

The harness is designed to test how different fraud-review decision policies behave when synthetic verification cases produce outcome feedback. It treats each synthetic case as an environment state, each review decision as an action, and the downstream outcome as a reward signal.

This is **not** intended to be a frontier reinforcement learning system. It is a small, deterministic, reproducible evaluation harness showing how decision workflows can be evaluated, stress-tested, and adjusted from feedback over time.

---

## What was tested

The experiment compares three decision policies over synthetic fraud and identity verification cases:

1. **Rules baseline**
   - Static threshold-based policy using device risk, behaviour anomaly, document confidence, watchlist match, and velocity score.
   - Represents a simple deterministic operations baseline.

2. **AI-review fallback**
   - Offline AI-review policy interface.
   - In these runs, it uses deterministic fallback logic because no live OpenAI calls or mocked per-case AI decisions were passed into the runner.
   - This keeps the experiment reproducible and avoids relying on external provider credentials.

3. **Feedback-adjusted policy**
   - Starts from deterministic approval and rejection thresholds.
   - Updates thresholds after receiving reward feedback from synthetic outcomes.
   - This is a lightweight policy-improvement loop, not a trained reinforcement learning system.

---

## Dataset assumptions

The dataset is synthetic and stored at:

```text
backend/eval_harness/data/synthetic_cases.jsonl
```

Each synthetic case contains structured verification signals such as:

- device risk
- behaviour anomaly
- document confidence
- watchlist match
- velocity score
- expected review decision

The expected decision is treated as the synthetic reference outcome for evaluation.

This dataset does **not** contain real user data, real fraud labels, real identity verification outcomes, or production risk signals.

---

## Reward function

The harness uses an inspectable reward function designed around fraud-review trade-offs.

At a high level:

- correct decisions receive positive reward
- unsafe approvals are penalised heavily
- incorrect rejections are penalised
- escalation can be useful when uncertainty is high
- unnecessary escalation receives a smaller penalty than unsafe approval

This reflects a common trust and safety trade-off: in suspicious verification workflows, it can be safer to escalate uncertain cases than to approve risky ones automatically.

The reward function is intentionally simple and deterministic. It is used to compare policy behaviour over synthetic cases, not to claim production fraud-model performance.

---

## Single-seed result

Earlier single-seed run:

- episodes: `25`
- seed: `42`
- policies: rules baseline, AI-review fallback, feedback-adjusted policy

| Policy | Accuracy | Avg reward | False approve rate | False reject rate | Escalation rate |
|---|---:|---:|---:|---:|---:|
| Rules baseline | `0.84` | `0.70` | `0.00` | `0.16` | `0.12` |
| AI-review fallback | `0.84` | `0.70` | `0.00` | `0.16` | `0.12` |
| Feedback-adjusted | `0.96` | `0.82` | `0.00` | `0.04` | `0.24` |

The feedback-adjusted policy improved accuracy and average reward in this synthetic run while reducing false rejects. It also escalated more cases, which is an expected trade-off for a more cautious review policy.

---

## Multi-seed aggregate result

The latest multi-seed run evaluates each policy across five deterministic seeds.

- episodes per seed: `50`
- seeds: `1`, `7`, `21`, `42`, `100`
- total evaluated cases per policy: `250`
- output JSON: `backend/experiments/runs/2026-05-16-123246-multi-seed-policy-comparison.json`
- output CSV: `backend/experiments/runs/2026-05-16-123246-multi-seed-policy-comparison.csv`

| Policy | Accuracy mean | Accuracy std | Avg reward mean | Avg reward std | False approve rate | False reject rate | Escalation rate | Failures | Cases |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rules baseline | `0.892` | `0.035` | `0.744` | `0.048` | `0.000` | `0.108` | `0.188` | `0` | `250` |
| AI-review fallback | `0.892` | `0.035` | `0.744` | `0.048` | `0.000` | `0.108` | `0.188` | `0` | `250` |
| Feedback-adjusted | `0.980` | `0.000` | `0.832` | `0.023` | `0.000` | `0.020` | `0.276` | `0` | `250` |

Across five deterministic seeds and 250 synthetic evaluations per policy, the feedback-adjusted threshold policy improved accuracy and average reward while reducing false rejects. This came with a higher escalation rate, which is a reasonable trade-off in a fraud-review setting where uncertain cases may be routed to human review instead of being approved or rejected automatically.

---

## Decision distribution summary

| Policy | Approve count | Escalate count | Reject count | Approve mean rate | Escalate mean rate | Reject mean rate |
|---|---:|---:|---:|---:|---:|---:|
| Rules baseline | `100` | `47` | `103` | `0.400` | `0.188` | `0.412` |
| AI-review fallback | `100` | `47` | `103` | `0.400` | `0.188` | `0.412` |
| Feedback-adjusted | `100` | `69` | `81` | `0.400` | `0.276` | `0.324` |

The feedback-adjusted policy produced fewer rejections and more escalations than the rules baseline. In this synthetic setup, that reduced false rejects while keeping the false approve rate at zero.

---

## How to run the experiments

From the backend directory:

```powershell
cd C:\Users\dkape\ai-verification-copilot\backend
```

Run a single seeded experiment:

```powershell
python -m eval_harness.run_experiment --policy feedback_adjusted --episodes 50 --seed 42
```

Run the multi-seed policy comparison:

```powershell
python -m eval_harness.run_multi_seed_experiment --episodes 50 --seeds 1 7 21 42 100
```

Experiment outputs are written to:

```text
backend/experiments/runs/
```

The multi-seed runner writes:

- one JSON summary containing aggregate metrics and per-policy/per-seed runs
- one CSV file containing one row per policy and seed

---

## How to run the evaluation tests

From the backend directory:

```powershell
python -m pytest tests\eval_harness -q
```

Latest local result:

```text
47 passed, 1 warning
```

The warning comes from a LangChain/Pydantic compatibility warning in the local environment and is not caused by the evaluation harness.

---

## Failure analysis

The latest multi-seed run had:

- `0` failures for the rules baseline
- `0` failures for the AI-review fallback
- `0` failures for the feedback-adjusted policy

This means all policy runs completed successfully across the selected seeds and episodes.

The AI-review fallback and rules baseline currently produce the same aggregate metrics because the offline AI-review fallback is deterministic and intentionally conservative. This avoids live provider dependency during automated evaluation.

---

## Trade-offs observed

The feedback-adjusted policy improved accuracy and average reward over the rules baseline in the synthetic evaluation.

The main trade-off was a higher escalation rate:

- Rules baseline escalation rate: `0.188`
- AI-review fallback escalation rate: `0.188`
- Feedback-adjusted escalation rate: `0.276`

In a fraud-review workflow, this can be a sensible trade-off because more uncertain cases are routed to review instead of being incorrectly rejected or automatically approved.

This does not prove production performance. It shows that the evaluation harness can compare decision policies, measure trade-offs, and produce reproducible evidence.

---

## Known limitations

This evaluation harness is intentionally limited.

- The dataset is synthetic.
- No real fraud labels are used.
- No real user identity data is used.
- No production verification outcomes are used.
- The feedback-adjusted policy is threshold-based.
- The policy is not learned from real production feedback.
- This is not a trained reinforcement learning agent.
- Metrics measure synthetic decision behaviour only.
- The AI-review fallback is deterministic and offline unless connected to saved or live AI outputs.
- Results should not be interpreted as production fraud-model performance.

---

## Next steps

Possible future improvements:

- Add more synthetic cases covering edge cases and ambiguous review scenarios.
- Add saved AI-review outputs for offline comparison against deterministic policies.
- Add confusion-matrix style summaries by expected decision.
- Add policy comparison charts from CSV outputs.
- Add scenario-level slices, such as high device risk, low document confidence, and watchlist matches.
- Add regression checks to detect policy behaviour changes over time.

These would improve evaluation depth without claiming that the system is a production fraud model.