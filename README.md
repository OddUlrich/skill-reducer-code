# SkillReducer Reproduction Toolkit

Please choose a language:

- [中文 README](README.zh-CN.md)
- [English README](README.en.md)

## Quick Start

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
python -m skillreducer package --input runs\demo --archive runs\demo.zip
python -m unittest discover -s tests
```

This repository provides a dependency-light Python CLI for reproducing the SkillReducer paper pipeline with synthetic datasets, mock evaluation, controls, ablations, reports, and portable packaging.

## Paper Source

This project is an independent reproduction-oriented implementation based on the paper:

- **SkillReducer: Optimizing LLM Agent Skills for Token Efficiency**
- Authors: Yudong Gao, Zongjie Li, Yuanyuanyuan, Zimo Ji, Pingchuan Ma, Shuai Wang
- arXiv: [2603.29919](https://arxiv.org/abs/2603.29919)
- PDF: [https://arxiv.org/pdf/2603.29919](https://arxiv.org/pdf/2603.29919)
- DOI: [10.48550/arXiv.2603.29919](https://doi.org/10.48550/arXiv.2603.29919)

