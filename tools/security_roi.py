"""Return on security investment (ROSI) using annualized loss expectancy.

    ALE      = ARO x SLE            (expected yearly loss from major breaches)
    ALE'     = ARO x (1 - e) x SLE  (after controls with effectiveness e)
    ROSI     = (years x (ALE - ALE') - investment) / investment

Unlike "one avoided breach pays for everything", this treats a breach as a
probability, so the answer comes with the condition under which it holds:
the break-even annual breach probability.
"""

from __future__ import annotations

from typing import Any


def ale(aro: float, sle: float) -> float:
    return aro * sle


def rosi(inp: dict[str, Any], aro: float | None = None, effectiveness: float | None = None) -> float:
    aro = inp["aro"] if aro is None else aro
    e = inp["effectiveness"] if effectiveness is None else effectiveness
    reduction = ale(aro, inp["sle"]) * e * inp["years"]
    return (reduction - inp["investment"]) / inp["investment"]


def breakeven_aro(inp: dict[str, Any]) -> float:
    return inp["investment"] / (inp["years"] * inp["sle"] * inp["effectiveness"])


def markdown(inp: dict[str, Any]) -> str:
    before = ale(inp["aro"], inp["sle"])
    after = before * (1 - inp["effectiveness"])
    lines = [
        "| Measure | Value |",
        "|---|---|",
        f"| Single loss expectancy (SLE): {inp['sle_source']} | ${inp['sle'] / 1e6:.2f}M |",
        f"| Annual rate of a major breach before controls (ARO, assumption) | {inp['aro']:.0%} |",
        f"| Control effectiveness (assumption) | {inp['effectiveness']:.0%} |",
        f"| Expected yearly loss before → after | ${before / 1e6:.2f}M → ${after / 1e6:.2f}M |",
        f"| {inp['years']}-year investment | ${inp['investment'] / 1e3:.0f}k |",
        f"| **ROSI over {inp['years']} years** | **{rosi(inp):.0%}** |",
        f"| **Break-even annual breach probability** | **{breakeven_aro(inp):.1%}** |",
        "",
        "ROSI across assumptions (rows: annual breach probability; columns: control effectiveness):",
        "",
        "| ARO \\ effectiveness | " + " | ".join(f"{e:.0%}" for e in inp["grid_effectiveness"]) + " |",
        "|---|" + "---|" * len(inp["grid_effectiveness"]),
    ]
    for aro in inp["grid_aro"]:
        cells = []
        for e in inp["grid_effectiveness"]:
            value = rosi(inp, aro, e)
            cells.append(f"**{value:.0%}**" if value < 0 else f"{value:.0%}")
        lines.append(f"| {aro:.0%} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
