from __future__ import annotations

import json
from pathlib import Path

from .util import ensure_dir, slugify, write_jsonl, write_text


DOMAINS = [
    ("jwt-auth-helper", "JWT authentication", "jwt", "token", "HS256", "Bearer"),
    ("sql-migration-planner", "SQL schema migration", "migration", "rollback", "index", "DDL"),
    ("pytest-fixture-smith", "pytest fixture design", "pytest", "fixture", "parametrize", "assert"),
    ("k8s-yaml-auditor", "Kubernetes YAML auditing", "kubernetes", "yaml", "container", "probe"),
    ("fastapi-route-builder", "FastAPI route generation", "fastapi", "router", "pydantic", "endpoint"),
    ("react-accessibility-review", "React accessibility review", "react", "aria", "focus", "keyboard"),
    ("terraform-module-docs", "Terraform module documentation", "terraform", "variable", "output", "provider"),
    ("csv-cleaning-tool", "CSV cleaning", "csv", "delimiter", "header", "dedupe"),
    ("openapi-contract-test", "OpenAPI contract testing", "openapi", "schema", "status", "response"),
    ("logging-redaction-policy", "logging redaction", "pii", "redact", "secret", "audit"),
    ("dockerfile-hardening", "Dockerfile hardening", "dockerfile", "user", "layer", "scan"),
    ("markdown-release-notes", "release note drafting", "changelog", "release", "breaking", "migration"),
]


def _description(kind: str, topic: str, keywords: tuple[str, str, str, str]) -> str:
    if kind == "missing":
        return ""
    if kind == "short":
        return topic
    if kind == "verbose":
        k1, k2, k3, k4 = keywords
        return (
            f"Use this skill for {topic}, including {k1}, {k2}, {k3}, and {k4}. "
            f"Trigger it whenever the user mentions {topic}, asks for examples, wants a plan, "
            f"requests validation, needs implementation advice, or says any related phrase. "
            "This skill contains background, examples, templates, caveats, and workflow notes."
        )
    return f"{topic}. Use when a task needs {keywords[0]}, {keywords[1]}, or {keywords[2]}."


def _body(name: str, topic: str, keywords: tuple[str, str, str, str], example_as_spec: bool) -> str:
    k1, k2, k3, k4 = keywords
    implicit = (
        f"\n\n## Example-As-Spec\nWhen the prompt says strict mode, the output must include `{k4}` exactly once. "
        "This example defines required behavior, not optional illustration."
        if example_as_spec
        else ""
    )
    return f"""# {name}

## Core Rules
- Identify whether the request is about {topic}.
- Preserve user constraints before suggesting implementation.
- Always include checks for {k1} and {k2}.
- When producing code, include a minimal validation path using {k3}.

## Background
{topic} work often mixes planning, examples, and reference material. The agent should avoid loading large notes unless the task asks for deeper context. This paragraph is intentionally explanatory and non-actionable.

## Example
User: create a {topic} helper.
Assistant: return a concise implementation that mentions {k1}, {k2}, and {k3}.{implicit}

## Template
```
name: {name}
topic: {topic}
checks:
  - {k1}
  - {k2}
  - {k3}
```

## Redundant Notes
Always include checks for {k1} and {k2}.
Always include checks for {k1} and {k2}.
"""


def _reference(topic: str, keywords: tuple[str, str, str, str], idx: int) -> str:
    k1, k2, k3, k4 = keywords
    return f"""# Reference {idx}: {topic}

When: load this file when the task needs detailed examples for {topic}.
Topics: {k1}, {k2}, {k3}, {k4}

Detailed background for {topic}. Include {k1} checks, {k2} rollback thinking, {k3} validation, and {k4} naming. This intentionally overlaps with the body so deduplication has work to do.
"""


def _tasks(skill_name: str, topic: str, keywords: tuple[str, str, str, str], example_as_spec: bool) -> list[dict]:
    k1, k2, k3, k4 = keywords
    tasks = []
    for i in range(5):
        needs_ref = i in {2, 4}
        strict = example_as_spec and i == 3
        expected = [k1, k2] + ([k3] if not needs_ref else [k3, k4])
        if strict:
            expected.append(k4)
        tasks.append(
            {
                "id": f"{skill_name}-task-{i+1}",
                "skill": skill_name,
                "prompt": f"Handle a {topic} task with {'reference detail' if needs_ref else 'core guidance'}"
                + (" in strict mode" if strict else ""),
                "kind": "rubric",
                "needs_reference": needs_ref,
                "required_refs": ["references/examples.md"] if needs_ref else [],
                "rubric": [f"Mentions {kw}" for kw in expected],
                "expected_keywords": expected,
            }
        )
    return tasks


def make_dataset(out: Path, size: str) -> dict:
    counts = {"small": 12, "medium": 60, "large": 200}
    if size not in counts:
        raise ValueError("size must be small, medium, or large")
    ensure_dir(out)
    skills_root = ensure_dir(out / "skills")
    manifest = []
    all_tasks = []
    desc_kinds = ["missing", "short", "verbose", "normal"]
    for i in range(counts[size]):
        base = DOMAINS[i % len(DOMAINS)]
        raw_name, topic, *keys = base
        skill_name = slugify(f"{raw_name}-{i+1:03d}" if i >= len(DOMAINS) else raw_name)
        kind = desc_kinds[i % len(desc_kinds)]
        has_refs = i % 3 != 0
        has_scripts = i % 7 == 0
        example_as_spec = i % 5 == 0
        keywords = tuple(keys)  # type: ignore[arg-type]
        skill_dir = ensure_dir(skills_root / skill_name)
        desc = _description(kind, topic, keywords)
        body = _body(skill_name, topic, keywords, example_as_spec)
        front = "---\n" + f"name: {skill_name}\n" + (f"description: {desc}\n" if desc else "") + "---\n\n"
        write_text(skill_dir / "SKILL.md", front + body)
        refs = []
        if has_refs:
            refs_dir = ensure_dir(skill_dir / "references")
            write_text(refs_dir / "examples.md", _reference(topic, keywords, 1))
            refs.append("references/examples.md")
            if i % 4 == 0:
                write_text(refs_dir / "background.md", _reference(topic, keywords, 2) * 3)
                refs.append("references/background.md")
        if has_scripts:
            write_text(skill_dir / "scripts" / "helper.py", "print('script placeholder; scripts are not context tokens')\n")
        tasks = _tasks(skill_name, topic, keywords, example_as_spec)
        all_tasks.extend(tasks)
        manifest.append(
            {
                "name": skill_name,
                "description_kind": kind,
                "has_references": has_refs,
                "has_scripts": has_scripts,
                "example_as_spec": example_as_spec,
                "keywords": list(keywords),
                "references": refs,
                "queries": [f"Need help with {topic}", f"Validate {keys[0]} and {keys[1]}", f"Create {topic} guidance"],
                "tasks": [task["id"] for task in tasks],
            }
        )
    write_jsonl(out / "manifest.jsonl", manifest)
    write_jsonl(out / "tasks.jsonl", all_tasks)
    write_text(out / "README.md", f"# Synthetic SkillReducer dataset\n\nSize: {size}\nSkills: {counts[size]}\n")
    return {"skills": counts[size], "tasks": len(all_tasks), "out": str(out)}


def import_dataset(src: Path, out: Path) -> dict:
    from .util import copy_tree

    ensure_dir(out)
    copy_tree(src, out / "skills")
    write_jsonl(out / "manifest.jsonl", [])
    write_jsonl(out / "tasks.jsonl", [])
    return {"imported": str(src), "out": str(out)}

