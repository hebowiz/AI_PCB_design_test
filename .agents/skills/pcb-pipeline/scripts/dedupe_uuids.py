"""Re-issue duplicated (uuid "...") entries in a .kicad_pcb.

atopile 0.15.8 copies the library pad uuids into every footprint of the same
part. KiCad's DRC resolves violation items by uuid, so shorts and clearance
errors get reported against unrelated parts. Run before DRC (after ato build).

  python3 scripts/dedupe_uuids.py board.kicad_pcb
"""

import re
import sys
import uuid


def main(path: str) -> int:
    text = open(path).read()
    seen = set()
    count = 0

    def repl(m):
        nonlocal count
        if m.group(1) in seen:
            count += 1
            return f'(uuid "{uuid.uuid4()}")'
        seen.add(m.group(1))
        return m.group(0)

    text = re.sub(r'\(uuid "([0-9a-f-]+)"\)', repl, text)
    if count:
        open(path, "w").write(text)
    print(f"re-issued {count} duplicated uuid(s)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
