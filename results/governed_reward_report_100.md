# Governed Reward Experiment Report

Ranking-only simulation for: Reward is not reinforcement until admitted.

## Configuration

- Seed: `11`
- Tasks: `100`
- Candidate patches per task: `7`

## Headline Metrics

| Metric | Raw selector | Governed selector | Delta |
| --- | ---: | ---: | ---: |
| `visible_test_pass_rate` | 1.0 | 0.93 | -0.07 |
| `hidden_test_pass_rate` | 0.17 | 0.98 | +0.81 |
| `reward_hacking_rate` | 0.84 | 0.02 | -0.82 |
| `hard_invariant_violation_rate` | 0.84 | 0.02 | -0.82 |
| `architecture_violation_rate` | 0.0 | 0.0 | +0.0 |
| `delayed_regression_rate` | 0.84 | 0.05 | -0.79 |
| `security_regression_rate` | 0.0 | 0.0 | +0.0 |
| `public_api_break_rate` | 0.0 | 0.0 | +0.0 |
| `avg_diff_size` | 12.77 | 34.54 | +21.77 |
| `avg_maintainability` | 0.425 | 0.839 | +0.414 |
| `avg_causal_score` | 0.363 | 0.83 | +0.467 |
| `avg_raw_reward` | 2.0 | 1.805 | -0.195 |
| `avg_admitted_reward` | -0.761 | 1.316 | +2.077 |
| `reward_reversal_rate` | 0.84 | 0.02 | -0.82 |

## Candidate Pool

- Candidate patches: `700`
- Visible test pass rate: `0.756`
- Hidden test pass rate: `0.43`
- Reward hacking rate: `0.324`
- Governance status counts: `{"ADMITTED": 188, "DISCOUNTED": 217, "ESCALATED": 0, "PROPOSED": 0, "QUARANTINED": 10, "REJECTED": 0, "REVERSED": 285}`

## Interpretation

The raw selector optimizes immediately observable success. The governed selector admits reward only after hard invariants, exploit risk, causal attribution, hidden tests, and delayed-regression evidence are considered.

A useful positive result is not merely higher admitted reward. It is lower reward hacking, fewer hard-invariant violations, better hidden-test robustness, and lower delayed regression while keeping visible task performance competitive.
