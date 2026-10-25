"""Three-year total cost of ownership: stay on-premises vs. migrate to AWS.

Every number comes from a JSON input file with an explanation per line, so a
finance reviewer can challenge an assumption and re-run the model rather
than argue with a spreadsheet nobody can audit.
"""

from __future__ import annotations

import copy
from typing import Any


def _grow(value: float, rate: float, year: int) -> float:
    return value * (1 + rate) ** (year - 1)


def on_prem_year(inp: dict[str, Any], year: int) -> dict[str, float]:
    p = inp["on_prem"]
    storage_tb = _grow(inp["data_tb"], inp["data_growth"], year)
    return {
        "Hardware refresh (amortized)": p["hardware_refresh_capex"] / p["hardware_life_years"],
        "Storage (amortized, grows with data)": storage_tb * p["storage_cost_per_tb"] / p["hardware_life_years"],
        "Data center space & power": p["facilities_per_year"],
        "Network / WAN": p["network_per_year"],
        "Software licenses": p["licenses_per_year"],
        "Operations staff": p["ops_fte"] * p["fte_loaded_cost"],
    }


def cloud_year(inp: dict[str, Any], year: int) -> dict[str, float]:
    c = inp["cloud"]
    instances = c["instances"]
    compute_on_demand = instances * c["avg_instance_monthly"] * 12
    discount = c["savings_plan_discount"] * c["savings_plan_coverage"][year - 1]
    compute = compute_on_demand * (1 - discount)

    storage_tb = _grow(inp["data_tb"], inp["data_growth"], year)
    storage = 0.0
    for tier in c["storage_tiers"]:
        storage += storage_tb * 1024 * tier["share"] * tier["usd_per_gb_month"] * 12

    egress = c["egress_tb_per_month"] * 1024 * c["egress_usd_per_gb"] * 12
    backup = storage_tb * 1024 * c["backup_share"] * c["backup_usd_per_gb_month"] * 12
    base = compute + storage + egress + backup + c["network_per_year"]
    security_ops = base * c["security_ops_share"]
    support = (base + security_ops) * c["support_share"]

    # During migration the data centers keep running (dual running).
    dual_running = sum(on_prem_year(inp, year).values()) * c["dual_running_share"][year - 1]
    dual_running -= inp["on_prem"]["ops_fte"] * inp["on_prem"]["fte_loaded_cost"] * c["dual_running_share"][year - 1]

    return {
        "Compute (after rightsizing, Savings Plans)": compute,
        "Storage (tiered: EBS / S3 / Glacier)": storage,
        "Data transfer out": egress,
        "Backups": backup,
        "Network (Direct Connect, NAT, endpoints)": c["network_per_year"],
        "Security & operations tooling": security_ops,
        "AWS Support": support,
        "SaaS replacing retired apps": c["saas_per_year"],
        "Operations staff": c["ops_fte"] * inp["on_prem"]["fte_loaded_cost"],
        "Migration (one-time: partners, training, tooling)": c["migration_one_time"] if year == 1 else 0.0,
        "Dual running (on-prem not yet retired, excl. staff)": dual_running,
    }


def run(inp: dict[str, Any]) -> dict[str, Any]:
    years = range(1, 4)
    onp = [sum(on_prem_year(inp, y).values()) for y in years]
    cld = [sum(cloud_year(inp, y).values()) for y in years]
    cumulative_saving = []
    running = 0.0
    for o, c in zip(onp, cld, strict=True):
        running += o - c
        cumulative_saving.append(running)
    breakeven = next((y for y, s in zip(years, cumulative_saving, strict=True) if s > 0), None)
    # If not paid back in 3 years, extrapolate at the year-3 run rate.
    monthly_run_rate = (onp[2] - cld[2]) / 12
    if cumulative_saving[-1] > 0:
        breakeven_month = None
    elif monthly_run_rate > 0:
        breakeven_month = 36 + -cumulative_saving[-1] / monthly_run_rate
    else:
        breakeven_month = float("inf")
    return {
        "on_prem": onp,
        "cloud": cld,
        "cumulative_saving": cumulative_saving,
        "breakeven_year": breakeven,
        "breakeven_month": breakeven_month,
        "three_year_saving_pct": (sum(onp) - sum(cld)) / sum(onp),
        "steady_state_saving_pct": (onp[2] - cld[2]) / onp[2],
    }


def sensitivity(inp: dict[str, Any], cases: list[dict[str, Any]]) -> list[tuple[str, float, float]]:
    """Each case: {"label", "path": ["cloud", "ops_fte"], "values": [low, high]} -> 3-yr saving % at each."""
    out = []
    for case in cases:
        results = []
        for v in case["values"]:
            trial = copy.deepcopy(inp)
            node = trial
            for key in case["path"][:-1]:
                node = node[key]
            node[case["path"][-1]] = v
            results.append(run(trial)["three_year_saving_pct"])
        out.append((case["label"], results[0], results[1]))
    return out


def usd(x: float) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x / 1e6:.2f}M" if x >= 1e6 else f"{sign}${x / 1e3:.0f}k"


def cell(x: float | None) -> str:
    if x is None:
        return ""
    return "—" if abs(x) < 0.5 else usd(x)


def markdown(inp: dict[str, Any]) -> str:
    r = run(inp)
    lines = ["| | Year 1 | Year 2 | Year 3 | 3-year total |", "|---|---|---|---|---|"]
    lines.append("| Stay on-premises | " + " | ".join(usd(v) for v in r["on_prem"]) + f" | {usd(sum(r['on_prem']))} |")
    lines.append("| Migrate to AWS | " + " | ".join(usd(v) for v in r["cloud"]) + f" | {usd(sum(r['cloud']))} |")
    lines.append("| Cumulative saving | " + " | ".join(usd(v) for v in r["cumulative_saving"]) + " | |")
    lines.append("")
    if r["breakeven_year"]:
        be = f"year {r['breakeven_year']}"
    elif r["breakeven_month"] == float("inf"):
        be = "never (cloud costs more at steady state)"
    else:
        be = f"about month {r['breakeven_month']:.0f} (at the year-3 run rate)"
    lines.append(
        f"**Break-even:** {be} · "
        f"**3-year saving:** {r['three_year_saving_pct']:.0%} · "
        f"**Steady-state (year 3) saving:** {r['steady_state_saving_pct']:.0%} "
        f"(target: {inp['target_saving_pct']:.0%})"
    )
    lines.append("")
    lines.append("<details><summary>Year-3 cost breakdown</summary>\n")
    lines.append("| Stay on-premises | | Migrate to AWS | |")
    lines.append("|---|---|---|---|")
    onp, cld = list(on_prem_year(inp, 3).items()), list(cloud_year(inp, 3).items())
    for i in range(max(len(onp), len(cld))):
        a = onp[i] if i < len(onp) else ("", None)
        b = cld[i] if i < len(cld) else ("", None)
        lines.append(f"| {a[0]} | {cell(a[1])} | {b[0]} | {cell(b[1])} |")
    lines.append("\n</details>")
    lines.append("")
    lines.append("**Sensitivity**: 3-year saving when one assumption moves (others unchanged):")
    lines.append("")
    lines.append("| Assumption | Low case | High case |")
    lines.append("|---|---|---|")
    for label, lo, hi in sensitivity(inp, inp["sensitivity"]):
        lines.append(f"| {label} | {lo:.0%} | {hi:.0%} |")
    return "\n".join(lines)
