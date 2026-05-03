from __future__ import annotations

import math
import re
from collections import Counter

from .models import Skill
from .tokenizer import count_tokens


def segment_description(description: str) -> list[str]:
    parts = re.split(r"[.;]\s+|,\s+| and | or ", description)
    return [p.strip(" .;") for p in parts if p.strip(" .;")]


def generate_description(skill: Skill) -> str:
    words = _keywords(skill.body, 8)
    capability = " ".join(words[:3]) or skill.name.replace("-", " ")
    triggers = ", ".join(words[3:6]) or skill.name
    unique = ", ".join(words[6:8]) or "validation"
    return f"{capability}. Use when tasks need {triggers}. Unique identifiers: {unique}."


def _keywords(text: str, limit: int) -> list[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "when",
        "this",
        "that",
        "from",
        "user",
        "assistant",
        "include",
        "always",
        "skill",
    }
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)]
    counts = Counter(w for w in words if w not in stop)
    return [w for w, _ in counts.most_common(limit)]


def tfidf_distractors(target: Skill, skills: list[Skill], limit: int = 4) -> list[str]:
    docs = {s.name: f"{s.name} {s.description}" for s in skills}
    vocab = {term for doc in docs.values() for term in set(_keywords(doc, 100))}
    idf = {}
    for term in vocab:
        df = sum(1 for doc in docs.values() if term in _keywords(doc, 100))
        idf[term] = math.log((len(docs) + 1) / (df + 1)) + 1

    def vector(doc: str) -> dict[str, float]:
        counts = Counter(_keywords(doc, 100))
        return {term: counts[term] * idf.get(term, 0.0) for term in counts}

    target_vec = vector(docs[target.name])
    scores = []
    for skill in skills:
        if skill.name == target.name:
            continue
        vec = vector(docs[skill.name])
        dot = sum(target_vec.get(k, 0.0) * vec.get(k, 0.0) for k in set(target_vec) | set(vec))
        norm = math.sqrt(sum(v * v for v in target_vec.values())) * math.sqrt(sum(v * v for v in vec.values()))
        scores.append((dot / norm if norm else 0.0, skill.name))
    return [name for _, name in sorted(scores, reverse=True)[:limit]]


def simulated_oracle(units: list[str], queries: list[str]) -> bool:
    text = " ".join(units).lower()
    if not text.strip():
        return False
    query_terms = set(_keywords(" ".join(queries), 20))
    unit_terms = set(_keywords(text, 40))
    if not query_terms:
        return True
    return len(query_terms & unit_terms) >= max(1, min(2, len(query_terms)))


def ddmin(units: list[str], queries: list[str]) -> list[str]:
    if not units or not simulated_oracle(units, queries):
        return units
    current = units[:]
    n = 2
    while len(current) >= 2:
        subset_size = max(1, math.ceil(len(current) / n))
        changed = False
        for start in range(0, len(current), subset_size):
            candidate = current[start : start + subset_size]
            if simulated_oracle(candidate, queries):
                current = candidate
                n = 2
                changed = True
                break
            complement = current[:start] + current[start + subset_size :]
            if complement and simulated_oracle(complement, queries):
                current = complement
                n = max(n - 1, 2)
                changed = True
                break
        if not changed:
            if n >= len(current):
                break
            n = min(len(current), n * 2)
    return current


def compress_description(skill: Skill, skills: list[Skill], manifest_entry: dict | None = None) -> tuple[str, dict]:
    queries = (manifest_entry or {}).get("queries", [skill.name.replace("-", " ")])
    original = skill.description
    generated = False
    if count_tokens(original) <= 40:
        original = generate_description(skill)
        generated = True
    units = segment_description(original)
    kept = ddmin(units, queries)
    polished = ". ".join(dict.fromkeys(u.strip() for u in kept if u.strip()))
    if polished and not polished.endswith("."):
        polished += "."
    deleted = [u for u in units if u not in kept]
    status = "direct_pass" if simulated_oracle(kept, queries) else "fallback"
    if status == "fallback":
        polished = skill.description or original
    return polished, {
        "generated": generated,
        "status": status,
        "working_description": original,
        "original_tokens": count_tokens(skill.description),
        "working_original_tokens": count_tokens(original),
        "compressed_tokens": count_tokens(polished),
        "deleted_units": deleted,
        "distractors": tfidf_distractors(skill, skills),
        "adversarial": f"{skill.name}-shadow",
    }
