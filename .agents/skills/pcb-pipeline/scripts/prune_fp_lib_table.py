"""Drop footprint-library entries whose directory is gone.

`ato build` only ever adds rows to the layout's fp-lib-table, so libraries for
parts that are no longer selected stay behind and KiCad complains about them
when the project is opened. Removing a row is safe: the board carries its own
copy of every footprint it uses.

  python3 scripts/prune_fp_lib_table.py board/layouts/default/fp-lib-table
"""

import os
import re
import sys


def main(path: str) -> int:
    text = open(path).read()
    base = os.path.dirname(os.path.abspath(path))
    kept, dropped = [], []

    def resolves(uri: str) -> bool:
        return os.path.isdir(uri.replace("${KIPRJMOD}", base))

    def handle(match: re.Match) -> str:
        block = match.group(0)
        name = re.search(r'\(name "([^"]+)"\)', block)
        uri = re.search(r'\(uri "([^"]+)"\)', block)
        if uri and not resolves(uri.group(1)):
            dropped.append(name.group(1) if name else "?")
            return ""
        kept.append(name.group(1) if name else "?")
        return block

    cleaned = re.sub(r"\t\(lib\n(?:\t\t.*\n)*?\t\)\n", handle, text)
    if dropped:
        open(path, "w").write(cleaned)
    print(f"{path}: kept {len(kept)} librar(ies), dropped {len(dropped)}")
    for d in dropped:
        print(f"  dropped {d}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
