# SkillReducer 使用说明

本文档面向日常使用者，展示如何从零生成自测数据、运行完整复现、查看压缩结果，并把工具用于自己的技能集合。

## 1. 快速跑通

在项目根目录执行：

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

运行完成后打开：

- 报告：[runs/demo/reports/report.md](../runs/demo/reports/report.md)
- 压缩结果目录：`runs/demo/compressed/`
- 逐任务评分：`runs/demo/reports/task_results.jsonl`

## 2. 生成合成数据集

合成数据集用于验证论文中的关键环节，不依赖原始论文数据集。

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer dataset make --out data\synthetic-medium --size medium
python -m skillreducer dataset make --out data\synthetic-large --size large
```

三种规模：

- `small`：约 12 个 skills，适合 smoke test
- `medium`：约 60 个 skills，适合本地完整自测
- `large`：约 200 个 skills，适合观察统计趋势和性能

每个合成 skill 会覆盖一部分论文现象：

- 缺失、过短、冗长、正常 description
- 单文件 skill、多 reference skill、带 scripts skill
- core/background/example/template/redundant 五类正文内容
- example-as-specification 样本，用于验证 feedback promotion

## 3. 扫描技能集合

```powershell
python -m skillreducer scan --skills data\synthetic\skills --out runs\demo\reports\stats.jsonl
```

扫描输出包含：

- description token 数
- body token 数
- reference token 数
- reference/script 数量
- taxonomy 分类统计

这一步对应论文经验研究部分，用于观察技能是否存在 skill bloat。

## 4. 运行压缩

```powershell
python -m skillreducer reduce --skills data\synthetic\skills --out runs\demo\compressed
```

压缩分两阶段：

- Stage 1：生成或压缩 description，保留路由关键词
- Stage 2：把正文拆成 core body 和 on-demand references

每个 skill 的输出形态：

```text
runs/demo/compressed/<skill>/
  SKILL.md
  references/
    examples.md
    templates.md
    background.md
  skillreducer.json
```

其中 `SKILL.md` 是默认注入上下文的精简 core；`references/*.md` 是需要时再读取的补充材料。

## 5. 运行评估

```powershell
python -m skillreducer eval --dataset data\synthetic --compressed runs\demo\compressed --out runs\demo\reports
```

当前实现会输出这些条件：

- `D`：no skill，下限组
- `A`：original skill，基线组
- `C`：SkillReducer compressed，主实验组
- `P`：LLMLingua-compatible mock baseline
- `L`：LLM direct compression mock baseline
- `T`：truncation baseline
- `R`：random removal baseline
- `C1`：description only 消融
- `C2`：body compress no classify 消融
- `C3`：reference dedup only 消融
- `C4`：compress all no classify 消融

核心指标：

- `pass_rate`：`score C >= score A` 的任务比例
- `retention_mean`：压缩后相对原始 skill 的平均保真度
- `improvement_rate`：压缩后优于原始 skill 的比例
- `regression_rate`：压缩后低于原始 skill 的比例

## 6. 一键复现

推荐日常使用这个命令：

```powershell
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

它会依次执行：

1. `scan`
2. `reduce`
3. `eval`
4. 生成 `run_summary.json` 和 `reports/report.md`

## 7. 导入自己的技能集合

如果你已有技能目录：

```text
my-skills/
  skill-a/
    SKILL.md
  skill-b/
    SKILL.md
    references/
```

可以导入：

```powershell
python -m skillreducer dataset import --src my-skills --out data\imported
python -m skillreducer reproduce --dataset data\imported --out runs\imported-demo
```

导入后的 `tasks.jsonl` 默认为空，`eval` 会生成简单 fallback tasks。若要得到更有意义的 Gate 2 结果，建议手工补充任务：

```json
{"id":"skill-a-task-1","skill":"skill-a","prompt":"...","kind":"rubric","needs_reference":false,"required_refs":[],"rubric":["Mentions X"],"expected_keywords":["x"]}
```

## 8. 打包和交付

打包运行结果：

```powershell
python -m skillreducer package --input runs\demo --archive runs\demo.zip
```

打包工具为单文件：

```powershell
python -m zipapp . -m "skillreducer.cli:main" -o skillreducer.pyz
```

目标机器只需要 Python：

```powershell
python skillreducer.pyz --help
```

## 9. 当前边界

当前版本优先实现“可自测、可迁移、少依赖”的完整复现骨架，因此：

- LLM 分类、压缩、评估默认是启发式/mock，可替换为真实 API
- Claude Code/OpenCode trigger adapter 仍是扩展点
- LLMLingua 真基线未内置依赖，当前输出 compatible mock baseline
- 合成数据用于验证工程链路，不能替代论文原始 55,315 skills 全量数据

