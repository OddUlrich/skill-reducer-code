from __future__ import annotations

import json
from pathlib import Path

from .io import load_skills
from .stage2 import optimize_skill
from .util import ensure_dir, read_jsonl, write_jsonl, write_text


def reduce_skills(skills_dir: Path, out: Path, dataset_dir: Path | None = None) -> dict:
    skills = load_skills(skills_dir)
    manifest_rows = read_jsonl(dataset_dir / "manifest.jsonl") if dataset_dir else []
    manifest = {row.get("name"): row for row in manifest_rows}
    ensure_dir(out)
    rows = []
    for skill in skills:
        optimized = optimize_skill(skill, skills, manifest.get(skill.name))
        skill_out = ensure_dir(out / skill.name)
        front = "---\n" + f"name: {skill.name}\n" + f"description: {optimized.description}\n---\n\n"
        ref_lines = ""
        if optimized.references:
            ref_lines = "\n\n## On-Demand References\n" + "\n".join(
                f"- `{ref.path}`: {ref.when} Topics: {', '.join(ref.topics)}" for ref in optimized.references
            )
        write_text(skill_out / "SKILL.md", front + "# Core Rules\n\n" + optimized.core_body + ref_lines + "\n")
        for ref in optimized.references:
            write_text(skill_out / ref.path, ref.content)
        log = {
            "name": skill.name,
            "restore_log": optimized.restore_log,
            "compression_stats": optimized.compression_stats,
            "promoted_items": len(optimized.promoted_items),
        }
        write_text(skill_out / "skillreducer.json", json.dumps(log, ensure_ascii=False, indent=2, sort_keys=True))
        rows.append(log)
    write_jsonl(out / "reduction.jsonl", rows)
    return {"skills": len(skills), "out": str(out)}

