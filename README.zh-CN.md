# SkillReducer 复现工具

SkillReducer 复现工具是一个 `Python 3.11+` 命令行项目，用于复现 SkillReducer 论文中的主要流程：数据集构造、技能扫描、路由描述优化、技能正文渐进披露、Gate 评估、反馈修复、控制组对比、消融实验和报告生成。

项目默认只依赖 Python 标准库，适合在没有论文原始数据集和外部 API 的环境中先完成离线自测；如果安装了 `tiktoken`，token 计数会自动切换为论文使用的 `cl100k_base`。

## 论文来源

本项目是基于以下论文实现的独立复现工程：

- **SkillReducer: Optimizing LLM Agent Skills for Token Efficiency**
- 作者：Yudong Gao, Zongjie Li, Yuanyuanyuan, Zimo Ji, Pingchuan Ma, Shuai Wang
- arXiv：[2603.29919](https://arxiv.org/abs/2603.29919)
- PDF：[https://arxiv.org/pdf/2603.29919](https://arxiv.org/pdf/2603.29919)
- DOI：[10.48550/arXiv.2603.29919](https://doi.org/10.48550/arXiv.2603.29919)

说明：本仓库不是论文官方发布代码，而是围绕论文方法、实验结构和工具化目标构建的复现与工程化实现。

## 功能概览

- 生成 small/medium/large 三档合成技能数据集
- 导入现有技能目录并转换为复现实验数据集
- 扫描技能的 description、body、references、scripts 和 taxonomy 分布
- 执行 Stage 1：description 生成、压缩、DDMIN、模拟路由验证
- 执行 Stage 2：正文分类、core/reference 拆分、reference 去重、`when/topics` 注释
- 执行 mock Gate 2 评估，输出 D/A/C、P/L/T/R 控制组和 C1-C4 消融组
- 生成 Markdown、JSON、JSONL 报告
- 将运行结果打包为 zip
- 可将工具打包为单文件 `skillreducer.pyz` 迁移使用

## 快速开始

在项目根目录运行：

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
python -m skillreducer package --input runs\demo --archive runs\demo.zip
python -m unittest discover -s tests
```

运行完成后查看：

- 复现实验报告：`runs/demo/reports/report.md`
- 压缩后的技能：`runs/demo/compressed/`
- 逐任务评分：`runs/demo/reports/task_results.jsonl`
- 运行汇总：`runs/demo/run_summary.json`

## 命令说明

### 生成合成数据集

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
```

`--size` 可选：

- `small`：约 12 个 skills，适合 smoke test
- `medium`：约 60 个 skills，适合本地完整自测
- `large`：约 200 个 skills，适合扩展性验证

### 导入真实技能集合

```powershell
python -m skillreducer dataset import --src my-skills --out data\imported
```

导入目录应包含若干子目录，每个子目录中有 `SKILL.md`。

### 扫描技能统计

```powershell
python -m skillreducer scan --skills data\synthetic\skills --out runs\demo\reports\stats.jsonl
```

扫描会统计 description token、body token、reference token、reference 数量、script 数量和 taxonomy 分类。

### 执行压缩

```powershell
python -m skillreducer reduce --skills data\synthetic\skills --out runs\demo\compressed
```

输出目录中每个 skill 会包含：

```text
SKILL.md
references/
skillreducer.json
```

### 执行评估

```powershell
python -m skillreducer eval --dataset data\synthetic --compressed runs\demo\compressed --out runs\demo\reports
```

评估条件：

- `D`：no skill，下限组
- `A`：original skill，原始基线组
- `C`：SkillReducer compressed，主实验组
- `P`：LLMLingua-compatible mock baseline
- `L`：LLM direct compression mock baseline
- `T`：truncation baseline
- `R`：random removal baseline
- `C1-C4`：消融组

### 一键复现

```powershell
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

该命令会依次执行 `scan`、`reduce` 和 `eval`。

### 打包运行结果

```powershell
python -m skillreducer package --input runs\demo --archive runs\demo.zip
```

## 打包工具本体

生成可迁移的单文件工具：

```powershell
python -m zipapp . -m "skillreducer.cli:main" -o skillreducer.pyz
```

在目标机器运行：

```powershell
python skillreducer.pyz --help
python skillreducer.pyz dataset make --out data\synthetic --size small
```

## 项目结构

```text
skillreducer/
  cli.py          # CLI 入口
  dataset.py      # 合成数据集与导入
  scan.py         # 经验统计扫描
  stage1.py       # 路由描述优化
  stage2.py       # 正文渐进披露
  reducer.py      # 压缩流水线
  eval.py         # 评估、控制组、消融
  reproduce.py    # 一键复现
  packager.py     # 运行产物打包
  llm.py          # 标准库 LLM 客户端扩展点
docs/
  configuration.md
  usage.md
  blog-reproduction-design.md
tests/
  test_core.py
```

## 文档

- [配置与操作文档](docs/configuration.md)
- [使用说明文档](docs/usage.md)
- [工具复现与设计实现博文](docs/blog-reproduction-design.md)

## 当前边界

当前版本是可运行的复现骨架和 mock 自测实现，重点是让完整工程链路先跑通。真实 LLM 分类/压缩、Claude Code/OpenCode trigger、真实 LLMLingua baseline、真实 SkillsBench 和论文规模数据集仍作为后续适配项。

## 验证

```powershell
python -m unittest discover -s tests
python -m compileall -q skillreducer tests
```
