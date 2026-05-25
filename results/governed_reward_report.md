# Governed Reward Experiment Report

Ranking-only simulation for: Reward is not reinforcement until admitted.

## Configuration

- Seed: `7`
- Tasks: `50`
- Candidate patches per task: `5`

## Headline Metrics

| Metric | Raw selector | Governed selector | Delta |
| --- | ---: | ---: | ---: |
| `visible_test_pass_rate` | 1.0 | 0.88 | -0.12 |
| `hidden_test_pass_rate` | 0.24 | 1.0 | +0.76 |
| `reward_hacking_rate` | 0.76 | 0.0 | -0.76 |
| `hard_invariant_violation_rate` | 0.76 | 0.0 | -0.76 |
| `architecture_violation_rate` | 0.0 | 0.0 | +0.0 |
| `delayed_regression_rate` | 0.78 | 0.0 | -0.78 |
| `security_regression_rate` | 0.0 | 0.0 | +0.0 |
| `public_api_break_rate` | 0.0 | 0.0 | +0.0 |
| `avg_diff_size` | 12.58 | 32.86 | +20.28 |
| `avg_maintainability` | 0.432 | 0.846 | +0.414 |
| `avg_causal_score` | 0.403 | 0.85 | +0.447 |
| `avg_raw_reward` | 1.994 | 1.678 | -0.316 |
| `avg_admitted_reward` | -0.621 | 1.325 | +1.946 |
| `reward_reversal_rate` | 0.76 | 0.0 | -0.76 |

## Candidate Pool

- Candidate patches: `250`
- Visible test pass rate: `0.812`
- Hidden test pass rate: `0.488`
- Reward hacking rate: `0.4`
- Governance status counts: `{"ADMITTED": 104, "DISCOUNTED": 46, "ESCALATED": 0, "PROPOSED": 0, "QUARANTINED": 0, "REJECTED": 0, "REVERSED": 100}`

## Interpretation

The raw selector optimizes immediately observable success. The governed selector admits reward only after hard invariants, exploit risk, causal attribution, hidden tests, and delayed-regression evidence are considered.

A useful positive result is not merely higher admitted reward. It is lower reward hacking, fewer hard-invariant violations, better hidden-test robustness, and lower delayed regression while keeping visible task performance competitive.
