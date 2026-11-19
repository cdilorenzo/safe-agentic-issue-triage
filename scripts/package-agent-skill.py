"""Reproducibly package a single Agensi Agent Skill as dist/skill.zip."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "github-issue-risk-gate"
SOURCE = ROOT / "skills" / NAME
OUTPUT = ROOT / "dist" / "skill.zip"
ALLOWED = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}


def build():
    files = sorted(
        p for p in SOURCE.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in ALLOWED
    )
    assert sum(path.name == "SKILL.md" for path in files) == 1, "Exactly one SKILL.md required"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = Path(NAME) / path.relative_to(SOURCE)
            info = zipfile.ZipInfo(relative.as_posix(), (2026, 11, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"Built {OUTPUT}: {len(files)} files, {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    build()
