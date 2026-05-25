#!/usr/bin/env python3
"""Minimal governed reward experiment for coding-agent reward admission.

This is a ranking-only experiment: each synthetic coding task has several
candidate patch outcomes. We compare a selector that trusts raw reward with one
that selects by admitted reward after governance checks.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class RewardStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ADMITTED = "ADMITTED"
    DISCOUNTED = "DISCOUNTED"
    REJECTED = "REJECTED"
    REVERSED = "REVERSED"
    QUARANTINED = "QUARANTINED"
    ESCALATED = "ESCALATED"


class Severity(str, Enum):
    HARD = "hard"
    SOFT = "soft"


TASK_CATEGORIES = (
    "bug_fix",
    "feature",
    "refactor",
    "security",
    "type_safety",
    "architecture",
    "performance",
    "test_repair",
)

STRATEGIES = (
    "minimal_fix",
    "architecture_preserving_fix",
    "test_first_fix",
    "hardcode_visible_case",
    "delete_or_weaken_tests",
    "broad_refactor",
    "dependency_shortcut",
    "swallow_errors",
    "block_broad_behavior",
)


@dataclass(frozen=True)
class Task:
    task_id: str
    category: str
    risk: float
    ambiguity: float


@dataclass(frozen=True)
class CandidatePatch:
    task_id: str
    patch_id: str
    strategy: str
    visible_tests_pass: bool
    hidden_tests_pass: bool
    typecheck_pass: bool
    lint_pass: bool
    build_pass: bool
    tests_deleted_or_weakened: bool
    hardcoded_visible_outputs: bool
    security_invariant_violated: bool
    architecture_boundary_violated: bool
    public_api_broken: bool
    secrets_introduced: bool
    unnecessary_dependency_added: bool
    excessive_diff: bool
    low_causal_attribution: bool
    delayed_regression: bool
    maintainability: float
    causal_score: float
    diff_size: int
    raw_reward: float


@dataclass(frozen=True)
class GovernanceCheck:
    name: str
    passed: bool
    severity: Severity
    score_impact: float
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GovernedReward:
    task_id: str
    patch_id: str
    raw_reward: float
    admitted_reward: float | None
    status: RewardStatus
    reason: str
    checks: list[GovernanceCheck]
    exploit_risk: float
    causal_confidence: float
    uncertainty: float
    audit_trace: dict[str, object]


@dataclass(frozen=True)
class GovernanceConfig:
    name: str = "full_governance"
    use_hard_invariants: bool = True
    use_exploit_detector: bool = True
    use_hidden_tests: bool = True
    use_delayed_regression: bool = True
    use_causal_attribution: bool = True
    use_maintainability: bool = True


FULL_GOVERNANCE = GovernanceConfig()

ABLATIONS = (
    FULL_GOVERNANCE,
    GovernanceConfig(name="no_hard_invariant_filter", use_hard_invariants=False),
    GovernanceConfig(name="no_exploit_detector", use_exploit_detector=False),
    GovernanceConfig(name="no_hidden_test_evidence", use_hidden_tests=False),
    GovernanceConfig(name="no_delayed_regression_evidence", use_delayed_regression=False),
    GovernanceConfig(name="no_causal_attribution", use_causal_attribution=False),
    GovernanceConfig(name="no_maintainability_discount", use_maintainability=False),
)


CORE_METRICS = (
    "visible_test_pass_rate",
    "hidden_test_pass_rate",
    "reward_hacking_rate",
    "hard_invariant_violation_rate",
    "architecture_violation_rate",
    "delayed_regression_rate",
    "security_regression_rate",
    "public_api_break_rate",
    "avg_diff_size",
    "hidden_test_pass_per_changed_line",
    "robustness_per_diff_size",
    "avg_maintainability",
    "avg_causal_score",
    "avg_raw_reward",
    "avg_admitted_reward",
    "reward_reversal_rate",
)


def clipped(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def chance(rng: random.Random, probability: float) -> bool:
    return rng.random() < clipped(probability)


def make_tasks(count: int, rng: random.Random) -> list[Task]:
    tasks = []
    for index in range(count):
        category = TASK_CATEGORIES[index % len(TASK_CATEGORIES)]
        base_risk = {
            "security": 0.85,
            "architecture": 0.75,
            "type_safety": 0.65,
            "performance": 0.55,
            "feature": 0.5,
            "bug_fix": 0.45,
            "refactor": 0.4,
            "test_repair": 0.35,
        }[category]
        tasks.append(
            Task(
                task_id=f"T{index + 1:03d}",
                category=category,
                risk=clipped(rng.gauss(base_risk, 0.12)),
                ambiguity=clipped(rng.betavariate(2.2, 3.2)),
            )
        )
    return tasks


def raw_reward(
    visible_tests_pass: bool,
    typecheck_pass: bool,
    lint_pass: bool,
    build_pass: bool,
) -> float:
    return (
        (1.0 if visible_tests_pass else -1.0)
        + (0.5 if typecheck_pass else 0.0)
        + (0.3 if lint_pass else 0.0)
        + (0.2 if build_pass else 0.0)
    )


def generate_candidate(
    task: Task,
    strategy: str,
    ordinal: int,
    rng: random.Random,
) -> CandidatePatch:
    risk = task.risk
    ambiguity = task.ambiguity

    if strategy == "minimal_fix":
        visible_p = 0.72 - 0.1 * ambiguity
        hidden_p = 0.66 - 0.12 * risk
        maintainability = rng.uniform(0.72, 0.9)
        causal = rng.uniform(0.68, 0.92)
        diff_size = rng.randint(8, 42)
        flags = {}
    elif strategy == "architecture_preserving_fix":
        visible_p = 0.66 - 0.08 * ambiguity
        hidden_p = 0.74 - 0.08 * risk
        maintainability = rng.uniform(0.78, 0.96)
        causal = rng.uniform(0.74, 0.96)
        diff_size = rng.randint(12, 55)
        flags = {}
    elif strategy == "test_first_fix":
        visible_p = 0.68 - 0.08 * ambiguity
        hidden_p = 0.71 - 0.08 * risk
        maintainability = rng.uniform(0.74, 0.94)
        causal = rng.uniform(0.72, 0.95)
        diff_size = rng.randint(18, 68)
        flags = {}
    elif strategy == "hardcode_visible_case":
        visible_p = 0.96
        hidden_p = 0.18 - 0.06 * risk
        maintainability = rng.uniform(0.2, 0.5)
        causal = rng.uniform(0.18, 0.42)
        diff_size = rng.randint(3, 25)
        flags = {"hardcoded_visible_outputs": True}
    elif strategy == "delete_or_weaken_tests":
        visible_p = 0.98
        hidden_p = 0.16 - 0.04 * risk
        maintainability = rng.uniform(0.15, 0.45)
        causal = rng.uniform(0.12, 0.35)
        diff_size = rng.randint(1, 35)
        flags = {"tests_deleted_or_weakened": True}
    elif strategy == "broad_refactor":
        visible_p = 0.62 - 0.12 * ambiguity
        hidden_p = 0.55 - 0.14 * risk
        maintainability = rng.uniform(0.46, 0.78)
        causal = rng.uniform(0.38, 0.7)
        diff_size = rng.randint(80, 260)
        flags = {"excessive_diff": True}
    elif strategy == "dependency_shortcut":
        visible_p = 0.74 - 0.05 * ambiguity
        hidden_p = 0.46 - 0.12 * risk
        maintainability = rng.uniform(0.42, 0.72)
        causal = rng.uniform(0.35, 0.68)
        diff_size = rng.randint(25, 120)
        flags = {"unnecessary_dependency_added": True}
    elif strategy == "swallow_errors":
        visible_p = 0.82
        hidden_p = 0.24 - 0.07 * risk
        maintainability = rng.uniform(0.25, 0.55)
        causal = rng.uniform(0.18, 0.48)
        diff_size = rng.randint(6, 48)
        flags = {"security_invariant_violated": task.category == "security"}
    elif strategy == "block_broad_behavior":
        visible_p = 0.88
        hidden_p = 0.3 - 0.08 * risk
        maintainability = rng.uniform(0.28, 0.6)
        causal = rng.uniform(0.22, 0.52)
        diff_size = rng.randint(8, 65)
        flags = {"public_api_broken": task.category in {"feature", "bug_fix"}}
    else:
        raise ValueError(f"unknown strategy: {strategy}")

    visible = chance(rng, visible_p)
    hidden = chance(rng, hidden_p)
    typecheck = chance(rng, 0.88 - 0.15 * (strategy in {"broad_refactor", "dependency_shortcut"}))
    lint = chance(rng, 0.9 - 0.12 * (strategy == "broad_refactor"))
    build = chance(rng, 0.93 - 0.1 * (strategy == "dependency_shortcut"))

    tests_deleted = bool(flags.get("tests_deleted_or_weakened", False))
    hardcoded = bool(flags.get("hardcoded_visible_outputs", False))
    security_violated = bool(flags.get("security_invariant_violated", False))
    arch_violated = (
        strategy in {"dependency_shortcut", "broad_refactor"}
        and chance(rng, 0.3 + 0.35 * (task.category == "architecture"))
    )
    api_broken = bool(flags.get("public_api_broken", False)) or (
        strategy == "broad_refactor" and chance(rng, 0.22)
    )
    secrets = chance(rng, 0.025 if strategy == "dependency_shortcut" else 0.005)
    unnecessary_dep = bool(flags.get("unnecessary_dependency_added", False))
    excessive_diff = bool(flags.get("excessive_diff", False)) or diff_size > 100
    low_causal = causal < 0.4
    delayed_regression = (visible and not hidden) or chance(
        rng,
        0.05 + 0.18 * excessive_diff + 0.18 * api_broken + 0.2 * security_violated,
    )

    return CandidatePatch(
        task_id=task.task_id,
        patch_id=f"{task.task_id}-P{ordinal}",
        strategy=strategy,
        visible_tests_pass=visible,
        hidden_tests_pass=hidden,
        typecheck_pass=typecheck,
        lint_pass=lint,
        build_pass=build,
        tests_deleted_or_weakened=tests_deleted,
        hardcoded_visible_outputs=hardcoded,
        security_invariant_violated=security_violated,
        architecture_boundary_violated=arch_violated,
        public_api_broken=api_broken,
        secrets_introduced=secrets,
        unnecessary_dependency_added=unnecessary_dep,
        excessive_diff=excessive_diff,
        low_causal_attribution=low_causal,
        delayed_regression=delayed_regression,
        maintainability=round(maintainability, 3),
        causal_score=round(causal, 3),
        diff_size=diff_size,
        raw_reward=round(raw_reward(visible, typecheck, lint, build), 3),
    )


def generate_candidates(task: Task, candidates_per_task: int, rng: random.Random) -> list[CandidatePatch]:
    preferred = [
        "minimal_fix",
        "architecture_preserving_fix",
        "test_first_fix",
        "hardcode_visible_case",
        "delete_or_weaken_tests",
        "broad_refactor",
        "dependency_shortcut",
        "swallow_errors",
        "block_broad_behavior",
    ]
    selected = preferred[: min(candidates_per_task, len(preferred))]
    if candidates_per_task > len(selected):
        selected.extend(rng.choices(STRATEGIES, k=candidates_per_task - len(selected)))
    return [
        generate_candidate(task, strategy, ordinal + 1, rng)
        for ordinal, strategy in enumerate(selected)
    ]


def governance_checks(
    candidate: CandidatePatch,
    config: GovernanceConfig = FULL_GOVERNANCE,
) -> list[GovernanceCheck]:
    checks = [
        GovernanceCheck(
            "tests_not_deleted_or_weakened",
            not candidate.tests_deleted_or_weakened,
            Severity.HARD,
            -2.0,
            ["diff metadata"],
        ),
        GovernanceCheck(
            "no_hardcoded_visible_outputs",
            not candidate.hardcoded_visible_outputs,
            Severity.HARD,
            -2.0,
            ["patch pattern scan", "candidate strategy tag"],
        ),
        GovernanceCheck(
            "security_invariant_preserved",
            not candidate.security_invariant_violated and not candidate.secrets_introduced,
            Severity.HARD,
            -2.0,
            ["security check"],
        ),
        GovernanceCheck(
            "architecture_boundary_preserved",
            not candidate.architecture_boundary_violated,
            Severity.HARD,
            -1.5,
            ["architecture rule check"],
        ),
        GovernanceCheck(
            "public_api_preserved",
            not candidate.public_api_broken,
            Severity.HARD,
            -0.8,
            ["API compatibility check"],
        ),
        GovernanceCheck(
            "hidden_tests_pass",
            candidate.hidden_tests_pass,
            Severity.SOFT,
            -1.0,
            ["hidden test suite"],
        ),
        GovernanceCheck(
            "no_unnecessary_dependency",
            not candidate.unnecessary_dependency_added,
            Severity.SOFT,
            -0.5,
            ["manifest diff"],
        ),
        GovernanceCheck(
            "diff_is_minimal",
            not candidate.excessive_diff,
            Severity.SOFT,
            -0.5,
            [f"{candidate.diff_size} changed lines"],
        ),
        GovernanceCheck(
            "causal_attribution_clear",
            not candidate.low_causal_attribution,
            Severity.SOFT,
            -0.5,
            [f"causal score {candidate.causal_score}"],
        ),
        GovernanceCheck(
            "no_delayed_regression",
            not candidate.delayed_regression,
            Severity.SOFT,
            -0.9,
            ["future regression simulation"],
        ),
    ]
    if not config.use_hidden_tests:
        checks = [check for check in checks if check.name != "hidden_tests_pass"]
    if not config.use_delayed_regression:
        checks = [check for check in checks if check.name != "no_delayed_regression"]
    if not config.use_causal_attribution:
        checks = [check for check in checks if check.name != "causal_attribution_clear"]
    if not config.use_maintainability:
        checks = [
            check
            for check in checks
            if check.name not in {"no_unnecessary_dependency", "diff_is_minimal"}
        ]
    return checks


def compute_exploit_risk(
    candidate: CandidatePatch,
    config: GovernanceConfig = FULL_GOVERNANCE,
) -> float:
    if not config.use_exploit_detector:
        return 0.0
    risk = 0.0
    risk += 0.65 if candidate.tests_deleted_or_weakened else 0.0
    risk += 0.6 if candidate.hardcoded_visible_outputs else 0.0
    if config.use_hidden_tests:
        risk += 0.25 if candidate.visible_tests_pass and not candidate.hidden_tests_pass else 0.0
    if config.use_causal_attribution:
        risk += 0.2 if candidate.low_causal_attribution else 0.0
    if config.use_maintainability:
        risk += 0.12 if candidate.excessive_diff else 0.0
    return clipped(risk)


def compute_uncertainty(
    candidate: CandidatePatch,
    config: GovernanceConfig = FULL_GOVERNANCE,
) -> float:
    uncertainty = 0.08
    if config.use_hidden_tests:
        uncertainty += 0.18 if not candidate.hidden_tests_pass else 0.0
    if config.use_maintainability:
        uncertainty += 0.16 if candidate.excessive_diff else 0.0
        uncertainty += 0.14 if candidate.unnecessary_dependency_added else 0.0
    if config.use_delayed_regression:
        uncertainty += 0.12 if candidate.delayed_regression else 0.0
    if config.use_causal_attribution:
        uncertainty += 0.12 if candidate.causal_score < 0.55 else 0.0
    return clipped(uncertainty)


def govern(
    candidate: CandidatePatch,
    config: GovernanceConfig = FULL_GOVERNANCE,
) -> GovernedReward:
    checks = governance_checks(candidate, config)
    hard_violations = [
        check for check in checks if check.severity == Severity.HARD and not check.passed
    ]
    exploit_risk = compute_exploit_risk(candidate, config)
    causal_confidence = clipped(candidate.causal_score if config.use_causal_attribution else 0.75)
    uncertainty = compute_uncertainty(candidate, config)
    audit_trace = {
        "source": "synthetic coding benchmark",
        "evidence": [
            "visible tests",
            *([] if not config.use_hidden_tests else ["hidden tests"]),
            "typecheck",
            "lint",
            "build",
            *([] if not config.use_hard_invariants else ["invariant scanners"]),
            *([] if not config.use_delayed_regression else ["delayed regression simulation"]),
        ],
        "admission_policy": config.name,
    }

    if config.use_hard_invariants and hard_violations:
        return GovernedReward(
            task_id=candidate.task_id,
            patch_id=candidate.patch_id,
            raw_reward=candidate.raw_reward,
            admitted_reward=-1.0,
            status=RewardStatus.REVERSED,
            reason="Hard invariant violation overrides raw reward",
            checks=checks,
            exploit_risk=round(exploit_risk, 3),
            causal_confidence=round(causal_confidence, 3),
            uncertainty=round(uncertainty, 3),
            audit_trace={**audit_trace, "hard_violations": [c.name for c in hard_violations]},
        )

    if exploit_risk > 0.8:
        return GovernedReward(
            task_id=candidate.task_id,
            patch_id=candidate.patch_id,
            raw_reward=candidate.raw_reward,
            admitted_reward=0.0,
            status=RewardStatus.REJECTED,
            reason="High reward-hacking risk",
            checks=checks,
            exploit_risk=round(exploit_risk, 3),
            causal_confidence=round(causal_confidence, 3),
            uncertainty=round(uncertainty, 3),
            audit_trace=audit_trace,
        )

    if config.use_causal_attribution and causal_confidence < 0.4:
        return GovernedReward(
            task_id=candidate.task_id,
            patch_id=candidate.patch_id,
            raw_reward=candidate.raw_reward,
            admitted_reward=None,
            status=RewardStatus.QUARANTINED,
            reason="Insufficient causal attribution",
            checks=checks,
            exploit_risk=round(exploit_risk, 3),
            causal_confidence=round(causal_confidence, 3),
            uncertainty=round(uncertainty, 3),
            audit_trace=audit_trace,
        )

    soft_penalty = sum(-check.score_impact for check in checks if check.severity == Severity.SOFT and not check.passed)
    admitted = (
        candidate.raw_reward
        * causal_confidence
        * (1.0 - uncertainty)
        - exploit_risk * 0.5
        - soft_penalty
    )
    status = RewardStatus.DISCOUNTED if uncertainty > 0.4 or soft_penalty > 0 else RewardStatus.ADMITTED
    return GovernedReward(
        task_id=candidate.task_id,
        patch_id=candidate.patch_id,
        raw_reward=candidate.raw_reward,
        admitted_reward=round(admitted, 3),
        status=status,
        reason="Reward admitted after governance checks",
        checks=checks,
        exploit_risk=round(exploit_risk, 3),
        causal_confidence=round(causal_confidence, 3),
        uncertainty=round(uncertainty, 3),
        audit_trace=audit_trace,
    )


def choose_raw(candidates: list[CandidatePatch]) -> CandidatePatch:
    return max(candidates, key=lambda patch: (patch.raw_reward, patch.visible_tests_pass, -patch.diff_size))


def choose_governed(
    candidates: list[CandidatePatch],
    governed_by_patch: dict[str, GovernedReward],
) -> CandidatePatch:
    def score(patch: CandidatePatch) -> tuple[float, float, float, int]:
        reward = governed_by_patch[patch.patch_id]
        admitted = reward.admitted_reward
        if admitted is None:
            admitted = -10.0
        return (admitted, patch.raw_reward, patch.maintainability, -patch.diff_size)

    return max(candidates, key=score)


def weighted_scalar_score(candidate: CandidatePatch) -> float:
    score = candidate.raw_reward
    score += 1.0 if candidate.hidden_tests_pass else -1.0
    score += 0.4 * candidate.maintainability
    score += 0.4 * candidate.causal_score
    score -= 2.0 if candidate.tests_deleted_or_weakened else 0.0
    score -= 2.0 if candidate.hardcoded_visible_outputs else 0.0
    score -= 2.0 if candidate.security_invariant_violated or candidate.secrets_introduced else 0.0
    score -= 1.5 if candidate.architecture_boundary_violated else 0.0
    score -= 1.0 if candidate.public_api_broken else 0.0
    score -= 0.8 if candidate.delayed_regression else 0.0
    score -= 0.5 if candidate.unnecessary_dependency_added else 0.0
    score -= 0.4 if candidate.excessive_diff else 0.0
    score -= 0.003 * candidate.diff_size
    return round(score, 6)


def choose_weighted_scalar(candidates: list[CandidatePatch]) -> CandidatePatch:
    return max(
        candidates,
        key=lambda patch: (
            weighted_scalar_score(patch),
            patch.raw_reward,
            patch.maintainability,
            -patch.diff_size,
        ),
    )


def oracle_score(candidate: CandidatePatch) -> float:
    score = 0.0
    score += 4.0 if candidate.hidden_tests_pass else -4.0
    score += 2.0 if candidate.visible_tests_pass else -0.5
    score += 1.0 if not is_reward_hack(candidate) else -4.0
    score += 1.0 if not has_hard_violation(candidate) else -5.0
    score += 1.0 if not candidate.delayed_regression else -3.0
    score += candidate.maintainability
    score += candidate.causal_score
    score -= 0.002 * candidate.diff_size
    return round(score, 6)


def choose_oracle(candidates: list[CandidatePatch]) -> CandidatePatch:
    return max(
        candidates,
        key=lambda patch: (
            oracle_score(patch),
            patch.hidden_tests_pass,
            patch.visible_tests_pass,
            patch.maintainability,
            -patch.diff_size,
        ),
    )


def choose_larger_diff(candidates: list[CandidatePatch]) -> CandidatePatch:
    return max(candidates, key=lambda patch: (patch.diff_size, patch.raw_reward))


def is_reward_hack(candidate: CandidatePatch) -> bool:
    return (
        candidate.tests_deleted_or_weakened
        or candidate.hardcoded_visible_outputs
        or (candidate.visible_tests_pass and not candidate.hidden_tests_pass and candidate.causal_score < 0.45)
    )


def has_hard_violation(candidate: CandidatePatch) -> bool:
    return (
        candidate.tests_deleted_or_weakened
        or candidate.hardcoded_visible_outputs
        or candidate.security_invariant_violated
        or candidate.secrets_introduced
        or candidate.architecture_boundary_violated
        or candidate.public_api_broken
    )


def summarize_selection(
    selected: Iterable[CandidatePatch],
    governed_by_patch: dict[str, GovernedReward],
) -> dict[str, float]:
    rows = list(selected)
    count = len(rows)
    statuses = [governed_by_patch[row.patch_id].status for row in rows]
    return {
        "tasks": count,
        "visible_test_pass_rate": mean_bool(row.visible_tests_pass for row in rows),
        "hidden_test_pass_rate": mean_bool(row.hidden_tests_pass for row in rows),
        "reward_hacking_rate": mean_bool(is_reward_hack(row) for row in rows),
        "architecture_violation_rate": mean_bool(row.architecture_boundary_violated for row in rows),
        "hard_invariant_violation_rate": mean_bool(has_hard_violation(row) for row in rows),
        "delayed_regression_rate": mean_bool(row.delayed_regression for row in rows),
        "security_regression_rate": mean_bool(
            row.security_invariant_violated or row.secrets_introduced for row in rows
        ),
        "public_api_break_rate": mean_bool(row.public_api_broken for row in rows),
        "avg_diff_size": round(statistics.mean(row.diff_size for row in rows), 3),
        "hidden_test_pass_per_changed_line": round(
            sum(1 for row in rows if row.hidden_tests_pass)
            / max(1, sum(row.diff_size for row in rows)),
            5,
        ),
        "robustness_per_diff_size": round(
            sum(
                1
                for row in rows
                if row.hidden_tests_pass
                and not is_reward_hack(row)
                and not has_hard_violation(row)
                and not row.delayed_regression
            )
            / max(1, sum(row.diff_size for row in rows)),
            5,
        ),
        "avg_maintainability": round(statistics.mean(row.maintainability for row in rows), 3),
        "avg_causal_score": round(statistics.mean(row.causal_score for row in rows), 3),
        "avg_raw_reward": round(statistics.mean(row.raw_reward for row in rows), 3),
        "avg_admitted_reward": round(
            statistics.mean(
                governed_by_patch[row.patch_id].admitted_reward
                if governed_by_patch[row.patch_id].admitted_reward is not None
                else 0.0
                for row in rows
            ),
            3,
        ),
        "reward_reversal_rate": round(statuses.count(RewardStatus.REVERSED) / count, 3),
        "reward_quarantine_rate": round(statuses.count(RewardStatus.QUARANTINED) / count, 3),
    }


def mean_bool(values: Iterable[bool]) -> float:
    rows = list(values)
    return round(sum(rows) / len(rows), 3)


def run_experiment(
    task_count: int,
    candidates_per_task: int,
    seed: int,
    governance_config: GovernanceConfig = FULL_GOVERNANCE,
) -> dict[str, object]:
    rng = random.Random(seed)
    tasks = make_tasks(task_count, rng)
    candidates_by_task = {
        task.task_id: generate_candidates(task, candidates_per_task, rng) for task in tasks
    }
    all_candidates = [candidate for candidates in candidates_by_task.values() for candidate in candidates]
    governed_by_patch = {
        candidate.patch_id: govern(candidate, governance_config) for candidate in all_candidates
    }

    raw_selected = [choose_raw(candidates) for candidates in candidates_by_task.values()]
    weighted_selected = [choose_weighted_scalar(candidates) for candidates in candidates_by_task.values()]
    governed_selected = [
        choose_governed(candidates, governed_by_patch) for candidates in candidates_by_task.values()
    ]
    oracle_selected = [choose_oracle(candidates) for candidates in candidates_by_task.values()]
    larger_diff_selected = [choose_larger_diff(candidates) for candidates in candidates_by_task.values()]
    all_statuses = [reward.status for reward in governed_by_patch.values()]

    return {
        "config": {
            "seed": seed,
            "task_count": task_count,
            "candidates_per_task": candidates_per_task,
            "governance": asdict(governance_config),
        },
        "candidate_pool": {
            "patches": len(all_candidates),
            "visible_test_pass_rate": mean_bool(p.visible_tests_pass for p in all_candidates),
            "hidden_test_pass_rate": mean_bool(p.hidden_tests_pass for p in all_candidates),
            "reward_hacking_rate": mean_bool(is_reward_hack(p) for p in all_candidates),
            "status_counts": {
                status.value: all_statuses.count(status) for status in RewardStatus
            },
        },
        "raw_selector": summarize_selection(raw_selected, governed_by_patch),
        "weighted_scalar_selector": summarize_selection(weighted_selected, governed_by_patch),
        "governed_selector": summarize_selection(governed_selected, governed_by_patch),
        "oracle_selector": summarize_selection(oracle_selected, governed_by_patch),
        "larger_diff_selector": summarize_selection(larger_diff_selected, governed_by_patch),
        "selected_examples": [
            {
                "task_id": task_id,
                "raw_choice": asdict(raw),
                "governed_choice": asdict(gov),
                "raw_choice_governance": reward_to_json(governed_by_patch[raw.patch_id]),
                "governed_choice_governance": reward_to_json(governed_by_patch[gov.patch_id]),
            }
            for task_id, raw, gov in zip(candidates_by_task.keys(), raw_selected, governed_selected)
            if raw.patch_id != gov.patch_id
        ][:8],
    }


def reward_to_json(reward: GovernedReward) -> dict[str, object]:
    row = asdict(reward)
    row["status"] = reward.status.value
    for check in row["checks"]:
        check["severity"] = check["severity"].value
    return row


def write_report(results: dict[str, object], path: Path) -> None:
    raw = results["raw_selector"]
    weighted = results["weighted_scalar_selector"]
    governed = results["governed_selector"]
    oracle = results["oracle_selector"]
    larger_diff = results["larger_diff_selector"]
    lines = [
        "# Governed Reward Experiment Report",
        "",
        "Ranking-only simulation for: Reward is not reinforcement until admitted.",
        "",
        "## Configuration",
        "",
        f"- Seed: `{results['config']['seed']}`",
        f"- Tasks: `{results['config']['task_count']}`",
        f"- Candidate patches per task: `{results['config']['candidates_per_task']}`",
        f"- Governance: `{results['config']['governance']['name']}`",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Raw | Weighted scalar | Governed | Oracle | Larger diff | Governed - Raw |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for metric in CORE_METRICS:
        raw_value = raw[metric]
        weighted_value = weighted[metric]
        gov_value = governed[metric]
        oracle_value = oracle[metric]
        larger_diff_value = larger_diff[metric]
        delta = round(gov_value - raw_value, 3)
        lines.append(
            f"| `{metric}` | {raw_value} | {weighted_value} | {gov_value} | "
            f"{oracle_value} | {larger_diff_value} | {delta:+} |"
        )

    pool = results["candidate_pool"]
    lines.extend(
        [
            "",
            "## Candidate Pool",
            "",
            f"- Candidate patches: `{pool['patches']}`",
            f"- Visible test pass rate: `{pool['visible_test_pass_rate']}`",
            f"- Hidden test pass rate: `{pool['hidden_test_pass_rate']}`",
            f"- Reward hacking rate: `{pool['reward_hacking_rate']}`",
            f"- Governance status counts: `{json.dumps(pool['status_counts'], sort_keys=True)}`",
            "",
            "## Interpretation",
            "",
            "The raw selector optimizes immediately observable success. The governed selector "
            "admits reward only after hard invariants, exploit risk, causal attribution, hidden "
            "tests, and delayed-regression evidence are considered.",
            "",
            "A useful positive result is not merely higher admitted reward. It is lower reward "
            "hacking, fewer hard-invariant violations, better hidden-test robustness, and lower "
            "delayed regression while keeping visible task performance competitive.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mean_std_ci(values: list[float]) -> dict[str, float]:
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    ci95 = 1.96 * std / (len(values) ** 0.5) if len(values) > 1 else 0.0
    return {"mean": round(mean, 5), "std": round(std, 5), "ci95": round(ci95, 5)}


def paired_effect_size(left: list[float], right: list[float]) -> float:
    diffs = [l_value - r_value for l_value, r_value in zip(left, right)]
    std = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    if std == 0:
        return 0.0
    return round(statistics.mean(diffs) / std, 5)


def run_suite(
    seeds: list[int],
    task_count: int,
    candidate_counts: list[int],
) -> dict[str, object]:
    full_runs = []
    for candidates in candidate_counts:
        for seed in seeds:
            result = run_experiment(task_count, candidates, seed, FULL_GOVERNANCE)
            full_runs.append(
                {
                    "seed": seed,
                    "candidates_per_task": candidates,
                    "selectors": {
                        "raw": result["raw_selector"],
                        "weighted_scalar": result["weighted_scalar_selector"],
                        "governed": result["governed_selector"],
                        "oracle": result["oracle_selector"],
                        "larger_diff": result["larger_diff_selector"],
                    },
                    "candidate_pool": result["candidate_pool"],
                }
            )

    ablation_candidates = max(candidate_counts)
    ablation_runs = []
    for ablation in ABLATIONS:
        for seed in seeds:
            result = run_experiment(task_count, ablation_candidates, seed, ablation)
            ablation_runs.append(
                {
                    "seed": seed,
                    "candidates_per_task": ablation_candidates,
                    "ablation": ablation.name,
                    "governed": result["governed_selector"],
                    "candidate_pool": result["candidate_pool"],
                }
            )

    return {
        "config": {
            "seeds": seeds,
            "task_count": task_count,
            "candidate_counts": candidate_counts,
            "ablation_candidates_per_task": ablation_candidates,
        },
        "full_runs": full_runs,
        "ablation_runs": ablation_runs,
        "full_summary": summarize_full_runs(full_runs),
        "ablation_summary": summarize_ablation_runs(ablation_runs),
    }


def summarize_full_runs(full_runs: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {}
    selectors = ("raw", "weighted_scalar", "governed", "oracle", "larger_diff")
    candidate_counts = sorted({run["candidates_per_task"] for run in full_runs})
    for candidates in candidate_counts:
        candidate_runs = [run for run in full_runs if run["candidates_per_task"] == candidates]
        summary[str(candidates)] = {}
        for selector in selectors:
            selector_rows = [run["selectors"][selector] for run in candidate_runs]
            summary[str(candidates)][selector] = {
                metric: mean_std_ci([row[metric] for row in selector_rows])
                for metric in CORE_METRICS
            }
        summary[str(candidates)]["effect_sizes_governed_minus_raw"] = {
            metric: paired_effect_size(
                [run["selectors"]["governed"][metric] for run in candidate_runs],
                [run["selectors"]["raw"][metric] for run in candidate_runs],
            )
            for metric in CORE_METRICS
        }
        summary[str(candidates)]["candidate_pool"] = {
            metric: mean_std_ci([run["candidate_pool"][metric] for run in candidate_runs])
            for metric in (
                "visible_test_pass_rate",
                "hidden_test_pass_rate",
                "reward_hacking_rate",
            )
        }
    return summary


def summarize_ablation_runs(ablation_runs: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for ablation in sorted({run["ablation"] for run in ablation_runs}):
        rows = [run["governed"] for run in ablation_runs if run["ablation"] == ablation]
        summary[ablation] = {
            metric: mean_std_ci([row[metric] for row in rows]) for metric in CORE_METRICS
        }
    return summary


def write_suite_report(results: dict[str, object], path: Path) -> None:
    config = results["config"]
    lines = [
        "# Governed Reward Experiment Suite",
        "",
        "Multi-seed selector and ablation sweep for the ranking-only coding-agent simulation.",
        "",
        "## Configuration",
        "",
        f"- Seeds: `{config['seeds'][0]}..{config['seeds'][-1]}` (`{len(config['seeds'])}` seeds)",
        f"- Tasks per seed: `{config['task_count']}`",
        f"- Candidate counts: `{config['candidate_counts']}`",
        f"- Ablation candidate count: `{config['ablation_candidates_per_task']}`",
        "",
        "## Selector Sweep",
        "",
    ]
    for candidates, candidate_summary in results["full_summary"].items():
        lines.extend(
            [
                f"### {candidates} Candidates Per Task",
                "",
                "| Selector | Visible pass | Hidden pass | Hacking | Delayed regression | Hard violations | Diff size | Robustness / line |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for selector in ("raw", "weighted_scalar", "governed", "oracle", "larger_diff"):
            row = candidate_summary[selector]
            lines.append(
                f"| `{selector}` | {fmt_stat(row['visible_test_pass_rate'])} | "
                f"{fmt_stat(row['hidden_test_pass_rate'])} | "
                f"{fmt_stat(row['reward_hacking_rate'])} | "
                f"{fmt_stat(row['delayed_regression_rate'])} | "
                f"{fmt_stat(row['hard_invariant_violation_rate'])} | "
                f"{fmt_stat(row['avg_diff_size'])} | "
                f"{fmt_stat(row['robustness_per_diff_size'])} |"
            )
        pool = candidate_summary["candidate_pool"]
        raw_hacking = candidate_summary["raw"]["reward_hacking_rate"]["mean"]
        governed_hacking = candidate_summary["governed"]["reward_hacking_rate"]["mean"]
        pool_hacking = pool["reward_hacking_rate"]["mean"]
        raw_amplification = round(raw_hacking - pool_hacking, 5)
        governed_suppression = round(pool_hacking - governed_hacking, 5)
        effect = candidate_summary["effect_sizes_governed_minus_raw"]
        lines.extend(
            [
                "",
                "Candidate pool selection pressure:",
                "",
                f"- Pool hacking prevalence: `{fmt_stat(pool['reward_hacking_rate'])}`",
                f"- Raw selected hacking: `{raw_hacking}` "
                f"(`{raw_amplification:+}` versus pool)",
                f"- Governed selected hacking: `{governed_hacking}` "
                f"(`{governed_suppression:+}` suppressed versus pool)",
                "",
                "Governed minus raw paired effect sizes:",
                "",
                f"- Hidden pass: `{effect['hidden_test_pass_rate']}`",
                f"- Reward hacking: `{effect['reward_hacking_rate']}`",
                f"- Delayed regression: `{effect['delayed_regression_rate']}`",
                f"- Hard violations: `{effect['hard_invariant_violation_rate']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Governance Ablations",
            "",
            "| Variant | Hidden pass | Hacking | Delayed regression | Hard violations | Maintainability | Admitted reward |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for ablation in [ablation.name for ablation in ABLATIONS]:
        row = results["ablation_summary"][ablation]
        lines.append(
            f"| `{ablation}` | {fmt_stat(row['hidden_test_pass_rate'])} | "
            f"{fmt_stat(row['reward_hacking_rate'])} | "
            f"{fmt_stat(row['delayed_regression_rate'])} | "
            f"{fmt_stat(row['hard_invariant_violation_rate'])} | "
            f"{fmt_stat(row['avg_maintainability'])} | "
            f"{fmt_stat(row['avg_admitted_reward'])} |"
        )

    lines.extend(
        [
            "",
            "## Paper-Ready Reading",
            "",
            "Across the sweep, raw reward is evaluated as a selection pressure, not merely "
            "as a noisy measurement. The key question is whether visible-test reward "
            "amplifies hacked patches relative to their prevalence in the candidate pool.",
            "",
            "The larger-diff control addresses the objection that governed reward is only "
            "choosing bigger patches. If governed reward has better robustness per changed "
            "line than the larger-diff selector, the effect is governance discrimination, "
            "not patch-size preference.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fmt_stat(stat: dict[str, float]) -> str:
    return f"{stat['mean']} +/- {stat['ci95']}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", action="store_true", help="run multi-seed selector and ablation sweep")
    parser.add_argument("--tasks", type=int, default=50)
    parser.add_argument("--candidates", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--seed-start", type=int, default=10)
    parser.add_argument("--seed-end", type=int, default=30)
    parser.add_argument(
        "--candidate-grid",
        type=str,
        default="3,5,7,10",
        help="comma-separated candidate counts for --suite",
    )
    parser.add_argument("--out", type=Path, default=Path("results/governed_reward_results.json"))
    parser.add_argument("--report", type=Path, default=Path("results/governed_reward_report.md"))
    args = parser.parse_args()

    if args.suite:
        seeds = list(range(args.seed_start, args.seed_end + 1))
        candidate_counts = [int(value) for value in args.candidate_grid.split(",") if value]
        results = run_suite(seeds, args.tasks, candidate_counts)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
        write_suite_report(results, args.report)
        print("Governed Reward Experiment Suite")
        print(f"seeds={args.seed_start}..{args.seed_end} tasks={args.tasks}")
        print(f"candidate_grid={candidate_counts}")
        for candidates in candidate_counts:
            row = results["full_summary"][str(candidates)]
            raw = row["raw"]
            governed = row["governed"]
            print(
                f"candidates={candidates} hidden_pass raw="
                f"{raw['hidden_test_pass_rate']['mean']} governed="
                f"{governed['hidden_test_pass_rate']['mean']} hacking raw="
                f"{raw['reward_hacking_rate']['mean']} governed="
                f"{governed['reward_hacking_rate']['mean']}"
            )
        print(f"wrote {args.out}")
        print(f"wrote {args.report}")
        return

    results = run_experiment(args.tasks, args.candidates, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    write_report(results, args.report)

    raw = results["raw_selector"]
    governed = results["governed_selector"]
    print("Governed Reward Experiment")
    print(f"tasks={args.tasks} candidates_per_task={args.candidates} seed={args.seed}")
    print(
        "hidden_test_pass_rate: "
        f"raw={raw['hidden_test_pass_rate']} governed={governed['hidden_test_pass_rate']}"
    )
    print(
        "reward_hacking_rate: "
        f"raw={raw['reward_hacking_rate']} governed={governed['reward_hacking_rate']}"
    )
    print(
        "hard_invariant_violation_rate: "
        f"raw={raw['hard_invariant_violation_rate']} "
        f"governed={governed['hard_invariant_violation_rate']}"
    )
    print(
        "delayed_regression_rate: "
        f"raw={raw['delayed_regression_rate']} governed={governed['delayed_regression_rate']}"
    )
    print(f"wrote {args.out}")
    print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
