"""Translate a KiCad 10 board back into what atopile 0.15.8 can parse.

Two format changes in KiCad 10 stop `ato build` from reading a board that
pcbnew has re-saved:

  * via-protection settings became nested forms, e.g.
    `(tenting (front yes) (back yes))`. They are cosmetic defaults that KiCad
    restores on load, so they are simply dropped.
  * nets lost their numbers, and every reference became `(net "name")`.
    atopile still wants the KiCad 9 spelling, which differs by context:
    `(net N "name")` on a pad, `(net N)` plus `(net_name "name")` on a zone,
    plain `(net N)` on a track, via or arc, and a board-level net table.
    Rule areas, which KiCad 10 writes with no net at all, get `(net 0)` back.

Run it before `ato build` whenever pcbnew has touched the layout.

  python3 scripts/sanitize_pcb.py board/layouts/default/default.kicad_pcb
"""

import sys

DROP = ("tenting", "covering", "plugging", "filling", "capping")


class Atom(str):
    """A bare token; plain str means a quoted string."""


def parse(text: str) -> list:
    pos = 0
    n = len(text)

    def read_list() -> list:
        nonlocal pos
        pos += 1  # '('
        items = []
        while pos < n:
            c = text[pos]
            if c == ")":
                pos += 1
                return items
            if c == "(":
                items.append(read_list())
            elif c == '"':
                items.append(read_string())
            elif c.isspace():
                pos += 1
            else:
                items.append(read_atom())
        raise ValueError("unbalanced board file")

    def read_string() -> str:
        nonlocal pos
        pos += 1
        buf = []
        while pos < n:
            c = text[pos]
            if c == "\\":
                buf.append(text[pos : pos + 2])
                pos += 2
                continue
            if c == '"':
                pos += 1
                return "".join(buf)
            buf.append(c)
            pos += 1
        raise ValueError("unterminated string")

    def read_atom() -> Atom:
        nonlocal pos
        start = pos
        while pos < n and text[pos] not in ' \t\r\n()"':
            pos += 1
        return Atom(text[start:pos])

    while pos < n and text[pos].isspace():
        pos += 1
    return read_list()


def dump(node, depth: int = 0) -> str:
    if isinstance(node, Atom):
        return str(node)
    if isinstance(node, str):
        return '"' + node + '"'
    head = node[0] if node else Atom("")
    body = node[1:]
    simple = all(not isinstance(c, list) for c in body)
    pad = "\t" * depth
    if simple:
        return "(" + " ".join(dump(c) for c in node) + ")"
    parts = ["(" + dump(head)]
    for child in body:
        parts.append("\n" + pad + "\t" + dump(child, depth + 1))
    parts.append("\n" + pad + ")")
    return "".join(parts)


def transform(node, parent: str, numbers: dict, stats: dict):
    """Rewrite one form, returning a list of replacement forms (often one)."""
    if not isinstance(node, list) or not node:
        return [node]
    head = str(node[0])

    if head in DROP:
        stats["dropped"] += 1
        return []

    if head == "net" and parent != "kicad_pcb":
        name = next((c for c in node[1:] if not isinstance(c, Atom)), None)
        number = next((c for c in node[1:] if isinstance(c, Atom)), None)
        if name is None and number is not None:
            return [node]  # already a bare `(net N)`
        if name is None:
            return [node]
        num = numbers.setdefault(name, len(numbers))
        stats["nets"] += 1
        if parent == "pad":
            return [[Atom("net"), Atom(str(num)), name]]
        if parent == "zone":
            return [[Atom("net"), Atom(str(num))], [Atom("net_name"), name]]
        return [[Atom("net"), Atom(str(num))]]

    out = [node[0]]
    for child in node[1:]:
        out.extend(transform(child, head, numbers, stats))

    # rule areas carry no net in KiCad 10; atopile still requires the field
    if head == "zone" and not any(
        isinstance(c, list) and str(c[0]) == "net" for c in out[1:]
    ):
        out[1:1] = [[Atom("net"), Atom("0")], [Atom("net_name"), ""]]
        stats["nets"] += 1

    return [out]


def main(path: str) -> int:
    tree = parse(open(path).read())
    numbers: dict = {"": 0}
    stats = {"dropped": 0, "nets": 0}
    tree = transform(tree, "", numbers, stats)[0]

    # a board-level net table, inserted ahead of the first footprint
    existing = {
        str(c[2]) if len(c) > 2 else None for c in tree if isinstance(c, list) and str(c[0]) == "net"
    }
    if not existing or existing == {None}:
        table = [
            [Atom("net"), Atom(str(num)), name]
            for name, num in sorted(numbers.items(), key=lambda kv: kv[1])
        ]
        at = next(
            (i for i, c in enumerate(tree) if isinstance(c, list) and str(c[0]) == "footprint"),
            len(tree),
        )
        tree = tree[:at] + table + tree[at:]

    open(path, "w").write(dump(tree) + "\n")
    print(
        f"{path}: dropped {stats['dropped']} KiCad-10-only form(s), "
        f"rewrote {stats['nets']} net reference(s) across {len(numbers)} net(s)"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
