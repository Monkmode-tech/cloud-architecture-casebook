"""Composite availability from published SLAs.

Serial dependencies multiply:     A = a1 * a2 * ... * an
Redundant copies (any one works): A = 1 - (1 - a1) * (1 - a2) * ...

SLAs are service-credit commitments, not guarantees, and real outages are
often correlated (shared control planes, bad deploys to every region). The
numbers here are an upper bound on what the architecture allows, which is
exactly why they are useful in a design review: if the ceiling is below the
target, no amount of operational excellence will meet it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, prod

MINUTES_PER_YEAR = 365.25 * 24 * 60


@dataclass(frozen=True)
class Component:
    name: str
    sla: float  # e.g. 99.99 (percent)

    @property
    def a(self) -> float:
        return self.sla / 100


def serial(components: list[Component]) -> float:
    return prod(c.a for c in components)


def redundant(availabilities: list[float]) -> float:
    return 1 - prod(1 - a for a in availabilities)


def downtime_minutes_per_year(a: float) -> float:
    return (1 - a) * MINUTES_PER_YEAR


def fmt_pct(a: float) -> str:
    """Enough nines to tell designs apart. Truncates, so 99.99995% never shows as 100%."""
    pct = a * 100
    digits = 2
    for threshold in (99.9, 99.99, 99.999, 99.9999):
        if pct >= threshold:
            digits += 1
    # The epsilon absorbs binary floating-point error (0.9993 * 1e5 = 99929.99999...).
    return f"{floor(pct * 10**digits + 1e-6) / 10**digits:.{digits}f}%"


def fmt_downtime(minutes: float) -> str:
    if minutes >= 120:
        return f"{minutes / 60:.1f} h/yr"
    if minutes >= 1:
        return f"{minutes:.0f} min/yr"
    return f"{minutes * 60:.0f} s/yr"


def evaluate(scenario: dict) -> dict:
    """scenario = {"name", "target", "regions": int, "components": [{"name", "sla"}]}"""
    comps = [Component(c["name"], float(c["sla"])) for c in scenario["components"]]
    one_region = serial(comps)
    regions = int(scenario.get("regions", 1))
    total = redundant([one_region] * regions) if regions > 1 else one_region
    target = float(scenario["target"]) / 100
    return {
        "name": scenario["name"],
        "chain": " → ".join(f"{c.name} ({c.sla:g}%)" for c in comps),
        "one_region": one_region,
        "regions": regions,
        "total": total,
        "target": target,
        "meets": total >= target,
        "downtime": downtime_minutes_per_year(total),
    }


def markdown(scenarios: list[dict]) -> str:
    rows = [
        "| Design | Serial chain (per region) | One region | Regions | Composite ceiling "
        "| Downtime ceiling | Target | Meets? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in map(evaluate, scenarios):
        rows.append(
            f"| {s['name']} | {s['chain']} | {fmt_pct(s['one_region'])} | {s['regions']} | "
            f"**{fmt_pct(s['total'])}** | {fmt_downtime(s['downtime'])} | {s['target'] * 100:g}% | "
            f"{'yes' if s['meets'] else '**no**'} |"
        )
    return "\n".join(rows)
