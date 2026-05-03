from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .dataset import import_dataset, make_dataset
from .eval import evaluate
from .packager import package_output
from .reducer import reduce_skills
from .reproduce import reproduce
from .scan import scan_skills


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skillreducer", description="SkillReducer reproduction toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    dataset = sub.add_parser("dataset", help="Dataset utilities")
    dataset_sub = dataset.add_subparsers(dest="dataset_command", required=True)
    dataset_make = dataset_sub.add_parser("make", help="Generate synthetic skills and tasks")
    dataset_make.add_argument("--out", required=True, type=Path)
    dataset_make.add_argument("--size", choices=["small", "medium", "large"], default="small")
    dataset_import = dataset_sub.add_parser("import", help="Import an existing skill directory as a dataset")
    dataset_import.add_argument("--src", required=True, type=Path)
    dataset_import.add_argument("--out", required=True, type=Path)

    scan = sub.add_parser("scan", help="Scan skill corpus statistics")
    scan.add_argument("--skills", required=True, type=Path)
    scan.add_argument("--out", required=True, type=Path)

    reduce_cmd = sub.add_parser("reduce", help="Reduce skills")
    reduce_cmd.add_argument("--skills", required=True, type=Path)
    reduce_cmd.add_argument("--out", required=True, type=Path)
    reduce_cmd.add_argument("--config", type=Path)

    eval_cmd = sub.add_parser("eval", help="Evaluate compressed skills")
    eval_cmd.add_argument("--dataset", required=True, type=Path)
    eval_cmd.add_argument("--compressed", required=True, type=Path)
    eval_cmd.add_argument("--out", required=True, type=Path)

    repro = sub.add_parser("reproduce", help="Run scan, reduce, and eval")
    repro.add_argument("--dataset", required=True, type=Path)
    repro.add_argument("--out", required=True, type=Path)
    repro.add_argument("--config", type=Path)

    package = sub.add_parser("package", help="Zip a run directory")
    package.add_argument("--input", required=True, type=Path)
    package.add_argument("--archive", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "dataset" and args.dataset_command == "make":
            result = make_dataset(args.out, args.size)
        elif args.command == "dataset" and args.dataset_command == "import":
            result = import_dataset(args.src, args.out)
        elif args.command == "scan":
            result = scan_skills(args.skills, args.out)
        elif args.command == "reduce":
            dataset_dir = args.skills.parent if (args.skills.parent / "manifest.jsonl").exists() else None
            result = reduce_skills(args.skills, args.out, dataset_dir)
        elif args.command == "eval":
            result = evaluate(args.dataset, args.compressed, args.out)
        elif args.command == "reproduce":
            result = reproduce(args.dataset, args.out, args.config)
        elif args.command == "package":
            result = package_output(args.input, args.archive)
        else:
            parser.error("unknown command")
            return 2
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

