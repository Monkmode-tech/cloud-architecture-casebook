"""Render model outputs into the Markdown docs between generated-block markers.

    <!-- BEGIN GENERATED: tco:models/medtech-tco.json -->
    ...
    <!-- END GENERATED -->

    python3 -m tools.build          # rewrite the docs
    python3 -m tools.build --check  # CI: fail if any doc is stale
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from tools import availability, security_roi, tco

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"(<!-- BEGIN GENERATED: (\w+):([\w./-]+) -->\n)(.*?)(<!-- END GENERATED -->)", re.DOTALL)

RENDERERS = {
    "availability": lambda data: availability.markdown(data["scenarios"]),
    "tco": tco.markdown,
    "rosi": security_roi.markdown,
}


def assumptions_table(data: dict) -> str:
    rows = ["| Input | Why this value |", "|---|---|"]
    rows += [f"| `{k}` | {v} |" for k, v in data.get("assumptions", [])]
    return "\n".join(rows)


RENDERERS["assumptions"] = assumptions_table


def render(text: str) -> str:
    def replace(m: re.Match) -> str:
        kind, model = m.group(2), m.group(3)
        data = json.loads((ROOT / model).read_text())
        body = RENDERERS[kind](data)
        return f"{m.group(1)}{body}\n{m.group(5)}"

    return BLOCK.sub(replace, text)


def main(check: bool) -> int:
    stale = []
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        text = md.read_text()
        if "BEGIN GENERATED" not in text:
            continue
        new = render(text)
        if new != text:
            stale.append(md.relative_to(ROOT))
            if not check:
                md.write_text(new)
    if check and stale:
        for path in stale:
            print(f"::error file={path}::generated tables are stale - run `python3 -m tools.build`")
        return 1
    print(("stale: " if check else "updated: ") + (", ".join(map(str, stale)) or "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
