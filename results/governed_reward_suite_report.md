# Governed Reward Experiment Suite

Multi-seed selector and ablation sweep for the ranking-only coding-agent simulation.

## Configuration

- Seeds: `10..30` (`21` seeds)
- Tasks per seed: `100`
- Candidate counts: `[3, 5, 7, 10]`
- Ablation candidate count: `10`

## Selector Sweep

### 3 Candidates Per Task

| Selector | Visible pass | Hidden pass | Hacking | Delayed regression | Hard violations | Diff size | Robustness / line |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 0.96048 +/- 0.00771 | 0.61714 +/- 0.0178 | 0.0 +/- 0.0 | 0.39762 +/- 0.01634 | 0.00476 +/- 0.00219 | 28.61952 +/- 0.60267 | 0.02049 +/- 0.00073 |
| `weighted_scalar` | 0.8519 +/- 0.01259 | 0.95286 +/- 0.00592 | 0.0 +/- 0.0 | 0.06333 +/- 0.0088 | 0.00333 +/- 0.00247 | 32.27048 +/- 0.65406 | 0.02894 +/- 0.00067 |
| `governed` | 0.83571 +/- 0.01287 | 0.95476 +/- 0.00643 | 0.0 +/- 0.0 | 0.05095 +/- 0.0081 | 0.00095 +/- 0.00129 | 34.53143 +/- 0.6786 | 0.02715 +/- 0.00065 |
| `oracle` | 0.80571 +/- 0.01144 | 0.95714 +/- 0.00576 | 0.0 +/- 0.0 | 0.02095 +/- 0.00556 | 0.00286 +/- 0.00198 | 33.45714 +/- 0.51722 | 0.02833 +/- 0.00047 |
| `larger_diff` | 0.66476 +/- 0.01853 | 0.66571 +/- 0.02063 | 0.0 +/- 0.0 | 0.26286 +/- 0.01875 | 0.00476 +/- 0.00257 | 47.75143 +/- 0.54524 | 0.01325 +/- 0.00047 |

Candidate pool selection pressure:

- Pool hacking prevalence: `0.0 +/- 0.0`
- Raw selected hacking: `0.0` (`+0.0` versus pool)
- Governed selected hacking: `0.0` (`+0.0` suppressed versus pool)

Governed minus raw paired effect sizes:

- Hidden pass: `7.31702`
- Reward hacking: `0.0`
- Delayed regression: `-7.48802`
- Hard violations: `-0.64613`

### 5 Candidates Per Task

| Selector | Visible pass | Hidden pass | Hacking | Delayed regression | Hard violations | Diff size | Robustness / line |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 1.0 +/- 0.0 | 0.2319 +/- 0.02041 | 0.80048 +/- 0.01335 | 0.78048 +/- 0.02044 | 0.80381 +/- 0.01213 | 13.3781 +/- 0.37501 | 0.00827 +/- 0.00083 |
| `weighted_scalar` | 0.85667 +/- 0.0155 | 0.9719 +/- 0.00883 | 0.00952 +/- 0.00438 | 0.05 +/- 0.01003 | 0.01095 +/- 0.00467 | 32.37667 +/- 0.52652 | 0.02906 +/- 0.0006 |
| `governed` | 0.85333 +/- 0.01642 | 0.96524 +/- 0.00953 | 0.01619 +/- 0.00612 | 0.05714 +/- 0.01013 | 0.01714 +/- 0.00651 | 34.17381 +/- 0.60462 | 0.02761 +/- 0.00057 |
| `oracle` | 0.81762 +/- 0.01964 | 0.96714 +/- 0.00857 | 0.00048 +/- 0.00093 | 0.0219 +/- 0.00499 | 0.00238 +/- 0.003 | 33.96429 +/- 0.64062 | 0.02808 +/- 0.00063 |
| `larger_diff` | 0.66143 +/- 0.01465 | 0.64952 +/- 0.01962 | 0.02524 +/- 0.00629 | 0.27762 +/- 0.01462 | 0.02905 +/- 0.00714 | 47.83762 +/- 0.46389 | 0.0127 +/- 0.0004 |

Candidate pool selection pressure:

- Pool hacking prevalence: `0.4 +/- 0.0`
- Raw selected hacking: `0.80048` (`+0.40048` versus pool)
- Governed selected hacking: `0.01619` (`+0.38381` suppressed versus pool)

Governed minus raw paired effect sizes:

- Hidden pass: `12.51536`
- Reward hacking: `-20.0788`
- Delayed regression: `-12.11742`
- Hard violations: `-20.99957`

### 7 Candidates Per Task

| Selector | Visible pass | Hidden pass | Hacking | Delayed regression | Hard violations | Diff size | Robustness / line |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 1.0 +/- 0.0 | 0.23286 +/- 0.0186 | 0.79667 +/- 0.01647 | 0.77286 +/- 0.0183 | 0.8 +/- 0.01612 | 13.71667 +/- 0.44981 | 0.00912 +/- 0.00085 |
| `weighted_scalar` | 0.9 +/- 0.01339 | 0.97619 +/- 0.00722 | 0.00905 +/- 0.0038 | 0.05 +/- 0.00917 | 0.01286 +/- 0.00409 | 36.25381 +/- 0.97175 | 0.02594 +/- 0.0007 |
| `governed` | 0.87476 +/- 0.01435 | 0.97429 +/- 0.00735 | 0.00762 +/- 0.0038 | 0.04952 +/- 0.01007 | 0.0119 +/- 0.00419 | 38.54143 +/- 1.08249 | 0.0247 +/- 0.00072 |
| `oracle` | 0.86 +/- 0.01606 | 0.98524 +/- 0.00568 | 0.00048 +/- 0.00093 | 0.01286 +/- 0.00592 | 0.01095 +/- 0.00355 | 40.04905 +/- 1.38455 | 0.02422 +/- 0.00093 |
| `larger_diff` | 0.59476 +/- 0.01787 | 0.45952 +/- 0.01497 | 0.07714 +/- 0.01108 | 0.50143 +/- 0.01924 | 0.46048 +/- 0.02187 | 170.79048 +/- 2.36987 | 0.00117 +/- 0.00011 |

Candidate pool selection pressure:

- Pool hacking prevalence: `0.31595 +/- 0.00228`
- Raw selected hacking: `0.79667` (`+0.48072` versus pool)
- Governed selected hacking: `0.00762` (`+0.30833` suppressed versus pool)

Governed minus raw paired effect sizes:

- Hidden pass: `16.44432`
- Reward hacking: `-20.58663`
- Delayed regression: `-16.28314`
- Hard violations: `-20.51198`

### 10 Candidates Per Task

| Selector | Visible pass | Hidden pass | Hacking | Delayed regression | Hard violations | Diff size | Robustness / line |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw` | 1.0 +/- 0.0 | 0.21048 +/- 0.01719 | 0.8119 +/- 0.01649 | 0.8 +/- 0.01524 | 0.73238 +/- 0.02046 | 11.38238 +/- 0.3459 | 0.00958 +/- 0.001 |
| `weighted_scalar` | 0.94 +/- 0.00866 | 0.99095 +/- 0.0038 | 0.00381 +/- 0.00286 | 0.02952 +/- 0.00515 | 0.01095 +/- 0.00447 | 34.59619 +/- 1.13847 | 0.02789 +/- 0.00091 |
| `governed` | 0.89429 +/- 0.00999 | 0.98524 +/- 0.00461 | 0.00286 +/- 0.0024 | 0.03571 +/- 0.00697 | 0.00619 +/- 0.00252 | 37.00762 +/- 1.13614 | 0.02616 +/- 0.00084 |
| `oracle` | 0.91238 +/- 0.0102 | 0.99524 +/- 0.00291 | 0.0 +/- 0.0 | 0.00571 +/- 0.00418 | 0.00476 +/- 0.00219 | 37.74286 +/- 1.23046 | 0.02628 +/- 0.0009 |
| `larger_diff` | 0.58333 +/- 0.02232 | 0.46286 +/- 0.02531 | 0.06667 +/- 0.01076 | 0.47905 +/- 0.01742 | 0.47952 +/- 0.02536 | 174.0519 +/- 2.41185 | 0.00108 +/- 8e-05 |

Candidate pool selection pressure:

- Pool hacking prevalence: `0.36376 +/- 0.00454`
- Raw selected hacking: `0.8119` (`+0.44814` versus pool)
- Governed selected hacking: `0.00286` (`+0.3609` suppressed versus pool)

Governed minus raw paired effect sizes:

- Hidden pass: `17.47252`
- Reward hacking: `-20.10686`
- Delayed regression: `-19.13278`
- Hard violations: `-14.87058`

## Governance Ablations

| Variant | Hidden pass | Hacking | Delayed regression | Hard violations | Maintainability | Admitted reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_governance` | 0.98524 +/- 0.00461 | 0.00286 +/- 0.0024 | 0.03571 +/- 0.00697 | 0.00619 +/- 0.00252 | 0.82495 +/- 0.00383 | 1.224 +/- 0.02164 |
| `no_hard_invariant_filter` | 0.89952 +/- 0.0106 | 0.10429 +/- 0.01053 | 0.11905 +/- 0.01147 | 0.12905 +/- 0.01239 | 0.77067 +/- 0.00543 | 1.25729 +/- 0.01912 |
| `no_exploit_detector` | 0.98381 +/- 0.00438 | 0.00048 +/- 0.00093 | 0.03667 +/- 0.00707 | 0.00143 +/- 0.00153 | 0.82652 +/- 0.0034 | 1.22638 +/- 0.02125 |
| `no_hidden_test_evidence` | 0.87286 +/- 0.01218 | 0.0 +/- 0.0 | 0.13048 +/- 0.01265 | 0.0 +/- 0.0 | 0.83205 +/- 0.00355 | 1.292 +/- 0.01617 |
| `no_delayed_regression_evidence` | 0.91905 +/- 0.01304 | 0.0 +/- 0.0 | 0.13333 +/- 0.01508 | 0.0 +/- 0.0 | 0.82976 +/- 0.00352 | 1.28743 +/- 0.01734 |
| `no_causal_attribution` | 0.9919 +/- 0.00397 | 0.00571 +/- 0.00319 | 0.02429 +/- 0.00628 | 0.01095 +/- 0.0038 | 0.80243 +/- 0.00661 | 1.17048 +/- 0.01645 |
| `no_maintainability_discount` | 0.98667 +/- 0.00435 | 0.00238 +/- 0.00187 | 0.03143 +/- 0.00609 | 0.00571 +/- 0.00217 | 0.82162 +/- 0.00405 | 1.25648 +/- 0.0202 |

## Paper-Ready Reading

Across the sweep, raw reward is evaluated as a selection pressure, not merely as a noisy measurement. The key question is whether visible-test reward amplifies hacked patches relative to their prevalence in the candidate pool.

The larger-diff control addresses the objection that governed reward is only choosing bigger patches. If governed reward has better robustness per changed line than the larger-diff selector, the effect is governance discrimination, not patch-size preference.
