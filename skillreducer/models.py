from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    name: str
    path: Path
    description: str
    body: str
    references: dict[str, str] = field(default_factory=dict)
    scripts: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ReferenceModule:
    path: str
    content: str
    when: str
    topics: list[str]
    source_type: str


@dataclass
class OptimizedSkill:
    name: str
    description: str
    core_body: str
    references: list[ReferenceModule]
    restore_log: dict
    compression_stats: dict
    promoted_items: list[str] = field(default_factory=list)


@dataclass
class EvalTask:
    id: str
    skill: str
    prompt: str
    kind: str
    rubric: list[str]
    needs_reference: bool = False
    required_refs: list[str] = field(default_factory=list)
    checker: str | None = None
    expected_keywords: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    skill: str
    task_id: str
    condition: str
    score: float
    tool_calls: list[str] = field(default_factory=list)
    notes: str = ""

