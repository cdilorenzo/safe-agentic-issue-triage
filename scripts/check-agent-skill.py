"""Verify the upload artifact has exactly one self-contained text-only skill."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "github-issue-risk-gate"
SCRIPT = ROOT / "skills" / NAME / "scripts" / "issue_risk_gate.py"
PACKAGE = ROOT / "dist" / "skill.zip"


def check():
    assert SCRIPT.exists(), "Missing gate script"
    assert SCRIPT.stat().st_size < 20_000, "Agensi advisory: keep script smaller than 20 KB"
    skill_path = ROOT / "skills" / NAME / "SKILL.md"
    contents = skill_path.read_text(encoding="utf-8")
    assert contents.startswith(f"---\nname: {NAME}\ndescription:"), "Bad frontmatter"
    assert "TODO" not in contents
    if PACKAGE.exists():
        with zipfile.ZipFile(PACKAGE) as archive:
            paths = archive.namelist()
            entrypoints = [path for path in paths if path.endswith("/SKILL.md")]
            assert entrypoints == [f"{NAME}/SKILL.md"], f"Unexpected entrypoints: {entrypoints}"
            banned = {".exe", ".dll", ".png", ".pdf", ".wasm", ".pyc"}
            assert all(Path(name).suffix not in banned for name in paths), "Unsupported binary file in ZIP"
            assert all(name.startswith(NAME + "/") for name in paths), "Unexpected top-level files"
            assert all("__pycache__" not in name for name in paths), "Python cache in ZIP"
            print(f"Agensi package OK: {PACKAGE.stat().st_size} bytes; {len(paths)} entries")
    print(f"Gate script OK: {SCRIPT.stat().st_size} bytes (<20 KB)")


if __name__ == "__main__":
    try:
        check()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
