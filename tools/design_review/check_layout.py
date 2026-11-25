"""Read-only check for newly added A-2 review artifact paths (Python 3 stdlib)."""
import argparse
import json
import subprocess
from pathlib import Path

OUTPUTS = frozenset({
    "README.md", "manifest.json", "erc.json", "drc.json", "connectivity.json",
    "preservation.json", "metrics.json", "netlist.xml", "schematic.pdf",
    "schematic.png", "pcb_front.png", "pcb_back.png", "details.png",
    "comparison.png", "model.png",
})
REPORTS = "01_New_Design/kicad_direct/reports/"


def run_git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def violations(repo, base):
    # Explicit baseline; never guess which branch or old artifact should be removed.
    revision = run_git(repo, "rev-parse", "--verify", base + "^{commit}").decode().strip()
    added = run_git(repo, "diff", "--name-only", "--diff-filter=A", "-z", revision, "--")
    untracked = run_git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    paths = sorted({p.decode("utf-8") for p in (added + untracked).split(b"\0") if p})
    errors = []
    for path in paths:
        reason = None
        if path.startswith(".review-tmp/"):
            reason = "Trial outputs must remain untracked and ignored."
        elif path.startswith(REPORTS):
            if path[len(REPORTS):] not in {"current/" + name for name in OUTPUTS}:
                reason = "Use the fixed reports/current filenames; put trials outside Git."
        elif path.startswith(("docs/reviews/details/", "docs/reviews/batches/", "docs/reviews/evidence/")):
            reason = "Append technical history to docs/reviews/history.md; use design-branch fixed artifacts."
        if reason:
            errors.append({"path": path, "reason": reason})
    return {"base_commit": revision, "new_paths_checked": len(paths), "violations": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Explicit target worktree")
    parser.add_argument("--base", required=True, help="Commit before this review or policy change")
    args = parser.parse_args()
    try:
        result = violations(args.repo.resolve(), args.base)
    except (OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Cannot inspect repository: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
