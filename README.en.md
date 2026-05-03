# SkillReducer Reproduction Toolkit

SkillReducer Reproduction Toolkit is a `Python 3.11+` command-line project for reproducing the main pipeline described in the SkillReducer paper: dataset construction, skill scanning, routing-description optimization, progressive disclosure for skill bodies, gate-based evaluation, feedback repair, control baselines, ablations, and report generation.

The project uses only the Python standard library by default, so it can run offline without the original paper dataset or external APIs. If `tiktoken` is installed, token counting automatically switches to the paper-compatible `cl100k_base` encoding.

## Paper Source

This project is an independent reproduction-oriented implementation based on the following paper:

- **SkillReducer: Optimizing LLM Agent Skills for Token Efficiency**
- Authors: Yudong Gao, Zongjie Li, Yuanyuanyuan, Zimo Ji, Pingchuan Ma, Shuai Wang
- arXiv: [2603.29919](https://arxiv.org/abs/2603.29919)
- PDF: [https://arxiv.org/pdf/2603.29919](https://arxiv.org/pdf/2603.29919)
- DOI: [10.48550/arXiv.2603.29919](https://doi.org/10.48550/arXiv.2603.29919)

Note: this repository is not the official code release from the paper authors. It is a reproduction and engineering implementation built around the paper's method, experiment structure, and tooling goals.

## Features

- Generate synthetic skill datasets at small, medium, and large scales
- Import existing skill directories into the reproduction dataset layout
- Scan descriptions, bodies, references, scripts, and taxonomy distributions
- Run Stage 1: description generation, compression, DDMIN, and simulated routing validation
- Run Stage 2: body classification, core/reference splitting, reference deduplication, and `when/topics` annotations
- Run mock Gate 2 evaluation with D/A/C, P/L/T/R control baselines, and C1-C4 ablations
- Generate Markdown, JSON, and JSONL reports
- Package run outputs as zip archives
- Package the tool itself as a portable `skillreducer.pyz`

## Quick Start

Run from the repository root:

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
python -m skillreducer package --input runs\demo --archive runs\demo.zip
python -m unittest discover -s tests
```

After the run, inspect:

- Reproduction report: `runs/demo/reports/report.md`
- Compressed skills: `runs/demo/compressed/`
- Per-task scores: `runs/demo/reports/task_results.jsonl`
- Run summary: `runs/demo/run_summary.json`

## Commands

### Generate a Synthetic Dataset

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
```

Supported sizes:

- `small`: about 12 skills, suitable for smoke tests
- `medium`: about 60 skills, suitable for local end-to-end validation
- `large`: about 200 skills, suitable for scalability checks

### Import Real Skills

```powershell
python -m skillreducer dataset import --src my-skills --out data\imported
```

The source directory should contain one subdirectory per skill, each with a `SKILL.md` file.

### Scan Skill Statistics

```powershell
python -m skillreducer scan --skills data\synthetic\skills --out runs\demo\reports\stats.jsonl
```

The scan reports description tokens, body tokens, reference tokens, reference counts, script counts, and taxonomy labels.

### Reduce Skills

```powershell
python -m skillreducer reduce --skills data\synthetic\skills --out runs\demo\compressed
```

Each compressed skill directory contains:

```text
SKILL.md
references/
skillreducer.json
```

### Evaluate Compressed Skills

```powershell
python -m skillreducer eval --dataset data\synthetic --compressed runs\demo\compressed --out runs\demo\reports
```

Evaluation conditions:

- `D`: no skill, lower-bound condition
- `A`: original skill baseline
- `C`: SkillReducer compressed condition
- `P`: LLMLingua-compatible mock baseline
- `L`: LLM direct-compression mock baseline
- `T`: truncation baseline
- `R`: random-removal baseline
- `C1-C4`: ablation conditions

### Run the Full Reproduction Pipeline

```powershell
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

This command runs `scan`, `reduce`, and `eval` in sequence.

### Package a Run

```powershell
python -m skillreducer package --input runs\demo --archive runs\demo.zip
```

## Package the Tool

Create a portable single-file app:

```powershell
python -m zipapp . -m "skillreducer.cli:main" -o skillreducer.pyz
```

Run it on another machine:

```powershell
python skillreducer.pyz --help
python skillreducer.pyz dataset make --out data\synthetic --size small
```

## Project Layout

```text
skillreducer/
  cli.py          # CLI entry point
  dataset.py      # Synthetic dataset generation and import
  scan.py         # Empirical statistics scan
  stage1.py       # Routing-description optimization
  stage2.py       # Progressive disclosure for skill bodies
  reducer.py      # Reduction pipeline
  eval.py         # Evaluation, controls, and ablations
  reproduce.py    # End-to-end reproduction command
  packager.py     # Output packaging
  llm.py          # Standard-library LLM client extension point
docs/
  configuration.md
  usage.md
  blog-reproduction-design.md
tests/
  test_core.py
```

## Documentation

- [Configuration and operations guide](docs/configuration.md)
- [Usage guide](docs/usage.md)
- [Reproduction and implementation design blog](docs/blog-reproduction-design.md)

## Current Scope

This version is a runnable reproduction scaffold with mock self-testing. Its goal is to make the full engineering pipeline executable first. Real LLM classification/compression, Claude Code/OpenCode trigger validation, the real LLMLingua baseline, real SkillsBench checks, and the paper-scale dataset remain extension points.

## Verification

```powershell
python -m unittest discover -s tests
python -m compileall -q skillreducer tests
```
