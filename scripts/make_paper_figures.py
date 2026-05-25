#!/usr/bin/env python3
"""Generate SVG figures for the governed reward paper draft."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"


COLORS = {
    "raw": "#c43b3b",
    "weighted": "#4f6fb5",
    "governed": "#237a57",
    "oracle": "#6d5aa8",
    "larger": "#8a8a8a",
    "grid": "#d8dde6",
    "text": "#1f2933",
    "muted": "#5f6b7a",
}


def svg(width: int, height: int, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {COLORS['text']}; }}
.title {{ font-size: 22px; font-weight: 700; }}
.subtitle {{ font-size: 13px; fill: {COLORS['muted']}; }}
.label {{ font-size: 12px; }}
.small {{ font-size: 11px; fill: {COLORS['muted']}; }}
.axis {{ stroke: {COLORS['text']}; stroke-width: 1; }}
.grid {{ stroke: {COLORS['grid']}; stroke-width: 1; }}
</style>
{body}
</svg>
"""


def text(x: float, y: float, value: str, klass: str = "label", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" text-anchor="{anchor}">{escape(value)}</text>'


def escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(name: str, content: str) -> None:
    (FIGURES / name).write_text(content, encoding="utf-8")


def figure_pipeline() -> None:
    width, height = 980, 300
    boxes = [
        ("state", "State", "s_t"),
        ("action", "Action", "a_t"),
        ("raw", "Raw reward", "claim r_t"),
        ("gov", "Reward governor", "constraints, causal, temporal, epistemic checks"),
        ("admit", "Admitted reward", "r-hat_t, status, audit trace"),
        ("update", "Policy update", "only admitted signals"),
    ]
    x0, y0, bw, bh, gap = 40, 115, 130, 76, 28
    parts = [
        text(40, 38, "Figure 1. Governed reward inserts an admission layer between observation and learning", "title"),
        text(40, 62, "Raw reward is treated as a claim about action quality, not as authoritative reinforcement.", "subtitle"),
    ]
    for i, (_, title, sub) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        fill = "#ffffff"
        stroke = "#8fa2b7"
        if title == "Raw reward":
            fill = "#fff4f4"
            stroke = COLORS["raw"]
        if title == "Reward governor":
            fill = "#effaf4"
            stroke = COLORS["governed"]
        if title == "Admitted reward":
            fill = "#eef6ff"
            stroke = "#3d6fb6"
        parts.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="{bh}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(text(x + bw / 2, y0 + 30, title, "label", "middle"))
        parts.append(text(x + bw / 2, y0 + 53, sub, "small", "middle"))
        if i < len(boxes) - 1:
            ax = x + bw
            bx = x + bw + gap - 8
            y = y0 + bh / 2
            parts.append(f'<line x1="{ax}" y1="{y}" x2="{bx}" y2="{y}" stroke="#66788a" stroke-width="2"/>')
            parts.append(f'<polygon points="{bx},{y} {bx-8},{y-5} {bx-8},{y+5}" fill="#66788a"/>')
    parts.append(text(520, 230, "No raw success may reinforce invariant violation.", "subtitle", "middle"))
    save("fig1_governance_pipeline.svg", svg(width, height, "\n".join(parts)))


def plot_lines(name: str, title: str, subtitle: str, series: dict[str, list[tuple[int, float]]], y_label: str) -> None:
    width, height = 920, 520
    left, right, top, bottom = 80, 40, 80, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    xs = sorted({x for points in series.values() for x, _ in points})
    min_x, max_x = min(xs), max(xs)

    def px(x: float) -> float:
        return left + (x - min_x) / (max_x - min_x) * plot_w

    def py(y: float) -> float:
        return top + (1 - y) * plot_h

    parts = [text(40, 35, title, "title"), text(40, 58, subtitle, "subtitle")]
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = py(tick)
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" class="grid"/>')
        parts.append(text(left - 12, y + 4, f"{tick:.2f}", "small", "end"))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>')
    parts.append(text(18, top + plot_h / 2, y_label, "small", "middle"))
    for x in xs:
        parts.append(text(px(x), height - bottom + 25, str(x), "small", "middle"))
    parts.append(text(left + plot_w / 2, height - 18, "Candidate patches per task", "small", "middle"))

    for label, points in series.items():
        color = COLORS.get(label, "#333")
        coords = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in points:
            parts.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="4" fill="{color}"/>')
        lx, ly = points[-1]
        parts.append(text(px(lx) + 8, py(ly) + 4, label.replace("_", " "), "small"))
    save(name, svg(width, height, "\n".join(parts)))


def figure_candidate_width(suite: dict) -> None:
    summary = suite["full_summary"]
    labels = ["raw", "weighted_scalar", "governed", "oracle"]
    color_keys = {"raw": "raw", "weighted_scalar": "weighted", "governed": "governed", "oracle": "oracle"}
    hidden = {}
    hacking = {}
    regression = {}
    for label in labels:
        key = color_keys[label]
        hidden[key] = [(int(c), summary[c][label]["hidden_test_pass_rate"]["mean"]) for c in sorted(summary, key=int)]
        hacking[key] = [(int(c), summary[c][label]["reward_hacking_rate"]["mean"]) for c in sorted(summary, key=int)]
        regression[key] = [(int(c), summary[c][label]["delayed_regression_rate"]["mean"]) for c in sorted(summary, key=int)]
    plot_lines(
        "fig2_candidate_width_hidden.svg",
        "Figure 2. More candidate search makes raw reward worse and governed reward better",
        "Hidden-test pass rate across 21 seeds and candidate widths.",
        hidden,
        "Hidden pass rate",
    )
    plot_lines(
        "fig3_candidate_width_hacking.svg",
        "Figure 3. Raw reward amplifies reward hacking as candidate width increases",
        "Reward-hacking rate across 21 seeds and candidate widths.",
        hacking,
        "Reward-hacking rate",
    )
    plot_lines(
        "fig4_candidate_width_regression.svg",
        "Figure 4. Governed reward suppresses delayed regression under wider search",
        "Delayed-regression rate across 21 seeds and candidate widths.",
        regression,
        "Delayed-regression rate",
    )


def figure_selection_pressure(suite: dict) -> None:
    row = suite["full_summary"]["10"]
    values = [
        ("Candidate pool", row["candidate_pool"]["reward_hacking_rate"]["mean"], "#95a1ad"),
        ("Raw selected", row["raw"]["reward_hacking_rate"]["mean"], COLORS["raw"]),
        ("Governed selected", row["governed"]["reward_hacking_rate"]["mean"], COLORS["governed"]),
    ]
    save("fig5_selection_pressure.svg", bar_chart(
        "Figure 5. Reward hacking is a selection effect",
        "At 10 candidates, raw reward amplifies hacked patches above base-rate prevalence; governance suppresses them.",
        values,
        "Reward-hacking rate",
    ))


def bar_chart(title: str, subtitle: str, values: list[tuple[str, float, str]], y_label: str) -> str:
    width, height = 820, 460
    left, right, top, bottom = 90, 40, 80, 80
    plot_w, plot_h = width - left - right, height - top - bottom
    parts = [text(40, 35, title, "title"), text(40, 58, subtitle, "subtitle")]
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = top + (1 - tick) * plot_h
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" class="grid"/>')
        parts.append(text(left - 12, y + 4, f"{tick:.2f}", "small", "end"))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>')
    parts.append(text(18, top + plot_h / 2, y_label, "small", "middle"))
    gap = 44
    bw = (plot_w - gap * (len(values) + 1)) / len(values)
    for i, (label, value, color) in enumerate(values):
        x = left + gap + i * (bw + gap)
        h = value * plot_h
        y = top + plot_h - h
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" fill="{color}" rx="4"/>')
        parts.append(text(x + bw / 2, y - 8, f"{value:.3f}", "small", "middle"))
        parts.append(text(x + bw / 2, height - bottom + 25, label, "small", "middle"))
    return svg(width, height, "\n".join(parts))


def figure_ablation(suite: dict) -> None:
    summary = suite["ablation_summary"]
    variants = [
        ("full", "full_governance"),
        ("no hard", "no_hard_invariant_filter"),
        ("no hidden", "no_hidden_test_evidence"),
        ("no delayed", "no_delayed_regression_evidence"),
        ("no causal", "no_causal_attribution"),
    ]
    width, height = 980, 520
    left, right, top, bottom = 90, 40, 85, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    parts = [
        text(40, 35, "Figure 6. Ablations identify the load-bearing checks", "title"),
        text(40, 58, "Removing hard invariants increases hard violations; removing hidden or delayed evidence increases regressions.", "subtitle"),
    ]
    for tick in [0, 0.05, 0.10, 0.15]:
        y = top + (1 - tick / 0.15) * plot_h
        parts.append(f'<line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}" class="grid"/>')
        parts.append(text(left - 12, y + 4, f"{tick:.2f}", "small", "end"))
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>')
    group_w = plot_w / len(variants)
    bw = 28
    for i, (label, key) in enumerate(variants):
        x0 = left + i * group_w + group_w / 2
        metrics = [
            ("hack", summary[key]["reward_hacking_rate"]["mean"], COLORS["raw"], -bw - 4),
            ("reg", summary[key]["delayed_regression_rate"]["mean"], "#d18b2c", 0),
            ("hard", summary[key]["hard_invariant_violation_rate"]["mean"], "#6d5aa8", bw + 4),
        ]
        for _, value, color, offset in metrics:
            h = min(value / 0.15, 1) * plot_h
            y = top + plot_h - h
            parts.append(f'<rect x="{x0 + offset - bw/2}" y="{y}" width="{bw}" height="{h}" fill="{color}" rx="3"/>')
        parts.append(text(x0, height - bottom + 24, label, "small", "middle"))
    parts.append(text(width - 230, 96, "hack", "small"))
    parts.append(f'<rect x="{width-270}" y="86" width="24" height="10" fill="{COLORS["raw"]}"/>')
    parts.append(text(width - 230, 116, "regression", "small"))
    parts.append(f'<rect x="{width-270}" y="106" width="24" height="10" fill="#d18b2c"/>')
    parts.append(text(width - 230, 136, "hard violation", "small"))
    parts.append(f'<rect x="{width-270}" y="126" width="24" height="10" fill="#6d5aa8"/>')
    save("fig6_ablation.svg", svg(width, height, "\n".join(parts)))


def figure_deepseek(deepseek: dict) -> None:
    values = [
        ("Raw hidden", deepseek["raw_selector"]["hidden_pass_rate"], COLORS["raw"]),
        ("Governed hidden", deepseek["governed_selector"]["hidden_pass_rate"], COLORS["governed"]),
        ("Raw hacking", deepseek["raw_selector"]["reward_hacking_rate"], "#d18b2c"),
        ("Governed hacking", deepseek["governed_selector"]["reward_hacking_rate"], "#4f6fb5"),
    ]
    save("figA1_deepseek_appendix.svg", bar_chart(
        "Appendix Figure A1. DeepSeek-generated real-code sanity check",
        "Three executable Python tasks, 12 model-generated candidates per task.",
        values,
        "Rate",
    ))


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    suite = load_json("results/governed_reward_suite.json")
    deepseek = load_json("results/deepseek_real_codebase_results_12.json")
    figure_pipeline()
    figure_candidate_width(suite)
    figure_selection_pressure(suite)
    figure_ablation(suite)
    figure_deepseek(deepseek)
    print(f"wrote figures to {FIGURES}")


if __name__ == "__main__":
    main()
