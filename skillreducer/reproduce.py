from __future__ import annotations

import json
import shutil
from pathlib import Path

from .eval import evaluate
from .reducer import reduce_skills
from .scan import scan_skills
from .util import ensure_dir, write_text


def reproduce(dataset_dir: Path, out: Path, config: Path | None = None) -> dict:
    ensure_dir(out)
    compressed = out / "compressed"
    reports = out / "reports"
    scan_summary = scan_skills(dataset_dir / "skills", reports / "stats.jsonl")
    reduction_summary = reduce_skills(dataset_dir / "skills", compressed, dataset_dir)
    eval_summary = evaluate(dataset_dir, compressed, reports)
    if config and config.exists():
        shutil.copy2(config, out / "config.snapshot.toml")
    else:
        write_text(out / "config.snapshot.toml", "# Default mock configuration\nmode = \"mock\"\n")
    summary = {"scan": scan_summary, "reduction": reduction_summary, "eval": eval_summary}
    write_text(out / "run_summary.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary

