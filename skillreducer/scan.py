from __future__ import annotations

from pathlib import Path

from .io import load_skills
from .markdown import split_items
from .stage2 import classify_item
from .tokenizer import count_tokens
from .util import write_jsonl


def scan_skills(skills_dir: Path, out: Path) -> dict:
    rows = []
    totals = {"skills": 0, "missing_desc": 0, "short_desc": 0, "with_refs": 0, "with_scripts": 0}
    taxonomy_counts: dict[str, int] = {}
    for skill in load_skills(skills_dir):
        totals["skills"] += 1
        desc_tokens = count_tokens(skill.description)
        if not skill.description:
            totals["missing_desc"] += 1
        if desc_tokens <= 40:
            totals["short_desc"] += 1
        if skill.references:
            totals["with_refs"] += 1
        if skill.scripts:
            totals["with_scripts"] += 1
        labels = [classify_item(item) for item in split_items(skill.body)]
        for label in labels:
            taxonomy_counts[label] = taxonomy_counts.get(label, 0) + 1
        rows.append(
            {
                "name": skill.name,
                "description_tokens": desc_tokens,
                "body_tokens": count_tokens(skill.body),
                "reference_tokens": sum(count_tokens(r) for r in skill.references.values()),
                "reference_count": len(skill.references),
                "script_count": len(skill.scripts),
                "taxonomy": {label: labels.count(label) for label in sorted(set(labels))},
            }
        )
    write_jsonl(out, rows)
    summary = dict(totals)
    summary["taxonomy_counts"] = taxonomy_counts
    return summary

