from __future__ import annotations

import re
from pathlib import Path

from .models import Skill
from .util import read_text


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_skill_md(path: Path) -> tuple[str, str, dict]:
    text = read_text(path)
    metadata: dict[str, str] = {}
    match = FRONTMATTER_RE.match(text)
    if match:
        for line in match.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
        body = text[match.end() :]
    else:
        body = text
    description = metadata.get("description", "")
    return description, body.strip(), metadata


def load_skill(path: Path) -> Skill:
    skill_md = path / "SKILL.md"
    description, body, metadata = parse_skill_md(skill_md)
    references: dict[str, str] = {}
    scripts: list[str] = []
    for child in path.rglob("*"):
        if not child.is_file() or child.name == "SKILL.md":
            continue
        rel = child.relative_to(path).as_posix()
        if rel.startswith("scripts/") or child.suffix.lower() in {".py", ".sh", ".ps1", ".bat"}:
            scripts.append(rel)
        else:
            try:
                references[rel] = read_text(child)
            except UnicodeDecodeError:
                references[rel] = ""
    return Skill(path.name, path, description, body, references, scripts, metadata)


def load_skills(root: Path) -> list[Skill]:
    if (root / "SKILL.md").exists():
        return [load_skill(root)]
    skills = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            skills.append(load_skill(child))
    return skills

