"""Fail if a relative Markdown link points at a file that does not exist."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def main() -> int:
    broken = []
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        for target in LINK.findall(md.read_text()):
            if re.match(r"^[a-z]+:", target):  # http:, https:, mailto:
                continue
            if not (md.parent / target).resolve().exists():
                broken.append((md.relative_to(ROOT), target))
    for md, target in broken:
        print(f"::error file={md}::broken link {target}")
    print(f"{len(broken)} broken relative links")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
