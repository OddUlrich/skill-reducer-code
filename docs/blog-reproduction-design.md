# 从论文到可运行工具：SkillReducer 复现工具的设计与实现

SkillReducer 论文的核心问题很朴素：LLM agent 的 skill 本来应该节省提示词成本，但现实里的很多 skill 反而把大量不必要的说明、例子、模板和 reference 一股脑塞进上下文。SkillReducer 的答案不是简单“压短文本”，而是把 skill 当成一种有结构的软件制品来优化。

这份工具实现的目标，是把论文里的完整实验链路做成一个能在本地跑通、能打包迁移、默认少依赖的复现项目。

## 论文方法拆解

论文把 skill 分成几个部分：

- `description`：路由层，agent 用它判断是否调用 skill
- `body`：调用后默认注入上下文的主体内容
- `references`：额外文档、模板、规范等补充材料
- `scripts`：可执行工具，不按普通上下文 token 处理

论文观察到三个主要问题：

1. 很多 description 缺失或过短，导致路由失效；另一些 description 又太长，包含大量非路由信息。
2. body 中只有一部分是真正必须遵守的 core rules，大量内容是背景、例子、模板或重复说明。
3. reference 往往被整体加载，哪怕当前任务只需要其中很小一部分。

于是 SkillReducer 设计成两阶段：

- Stage 1 优化 description，让它“足够路由，但尽量短”。
- Stage 2 重构 body，把核心规则留在默认上下文，把 examples/templates/background 移到按需 reference。

再用 Gate 1/Gate 2 检查压缩是否伤害功能。如果压缩后任务失败，就把相关非核心内容提升回 core，这就是 feedback loop。

## 为什么实现成 Python CLI

复现工具的第一约束是可运行，而不是追求某个库生态的复杂度。因此项目采用 Python `3.11+`：

- 默认只用标准库，目标机器装 Python 即可运行
- 文件解析、JSONL、ZIP 打包、HTTP API 调用都能用标准库完成
- 后续需要真实模型时，可以接 OpenAI-compatible endpoint
- 需要精确 token 时，再可选安装 `tiktoken`

项目入口是：

```powershell
python -m skillreducer --help
```

也可以打成单文件：

```powershell
python -m zipapp . -m "skillreducer.cli:main" -o skillreducer.pyz
```

## 模块设计

项目按论文环节拆成几个模块：

- `dataset.py`：生成合成数据集，覆盖缺失描述、冗长描述、多 reference、example-as-spec 等现象
- `scan.py`：复现经验分析，统计 description/body/reference/scripts 和 taxonomy 分布
- `stage1.py`：描述生成、语义片段切分、TF-IDF distractor、DDMIN、模拟路由 oracle
- `stage2.py`：正文切分、taxonomy 分类、类型特定压缩、reference 去重和注释
- `reducer.py`：把 Stage 1/2 串起来，写出压缩后的 skill 目录
- `eval.py`：跑 D/A/C、控制组、消融组，计算 retention 和 pass rate
- `reproduce.py`：一键执行 scan、reduce、eval
- `packager.py`：把运行结果打包成 zip
- `llm.py`：标准库 OpenAI-compatible 客户端和 mock 客户端

这种拆法的好处是每个论文概念都有对应实现位置，后续替换真实 LLM 或真实 agent trigger 时，不需要推翻 CLI 和数据流。

## 合成数据集的作用

论文原始数据集和多模型 API 并没有随 PDF 提供，所以工具不能假装自己能直接复现论文全量数值。这里采用的是更工程化的策略：内置合成数据集，先验证每个环节是否真的能工作。

合成数据集分三档：

- `small`：12 个 skills，给 smoke test 和 CI 用
- `medium`：60 个 skills，用来观察控制组趋势
- `large`：200 个 skills，用来测试扩展性和日志完整性

每个合成 skill 会带：

- `SKILL.md`
- 可选 `references/*.md`
- 可选 `scripts/helper.py`
- manifest metadata
- 5 个 Gate 2 任务
- expected keywords 和 reference loading 期望

其中最重要的样本之一是 `example-as-specification`。这类样本故意把关键规则藏在例子里，用来验证 feedback loop 是否能把被误分到 reference 的关键 example 提升回 core。

## Stage 1 的实现策略

论文里的 Stage 1 使用 LLM 做 semantic clause segmentation，再用 simulated oracle + DDMIN 找到最小可路由描述，并通过真实 Claude Code CLI 验证。

当前实现采用 dependency-free 版本：

- 缺失或短 description：从 body 中抽取关键词生成描述
- 长 description：按标点和连接词切分 semantic-ish units
- oracle：检查 query 关键词和候选描述关键词是否有足够交集
- distractor：用标准库 TF-IDF 近似检索相似 skill
- adversarial shadow skill：记录占位，用于保持论文接口形态

这不是论文真实模型 oracle 的等价替代，但它保留了工程接口和算法骨架：后续把 `simulated_oracle` 换成真实 LLM router，并接入 Claude Code trigger adapter 即可升级。

## Stage 2 的实现策略

论文 Stage 2 的关键不是“缩写”，而是“分层”：

- core rules 始终加载
- examples/templates/background 按需加载
- redundant 删除
- 原始 references 做 overlap 去重

当前实现用启发式分类器覆盖五类 taxonomy：

- `core_rule`
- `background`
- `example`
- `template`
- `redundant`

压缩后的目录形态接近真实 skill：

```text
compressed/<skill>/
  SKILL.md
  references/
    examples.md
    templates.md
    background.md
  skillreducer.json
```

`SKILL.md` 中会列出 on-demand references 的 `when` 和 `topics`，模拟论文里的 progressive disclosure。

## Gate 2 与控制组

为了验证“压缩后是否还能完成任务”，工具实现了 mock Gate 2 评分。每个任务有 expected keywords，评估器检查不同条件下可见内容是否覆盖这些关键词。

条件包括：

- `D`：no skill
- `A`：original skill
- `C`：SkillReducer compressed
- `P`：LLMLingua-compatible mock baseline
- `L`：LLM direct compression mock baseline
- `T`：truncation baseline
- `R`：random removal baseline
- `C1-C4`：消融组

报告会输出：

- mean score
- pass rate
- retention
- improvement/regression rate
- compression ratios
- feedback promotions
- routing statuses

这能帮助开发者快速判断：主链路是否跑通，压缩是否保留任务信息，控制组是否明显弱于结构化压缩。

## 一次本地运行

完整复现命令：

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

报告位置：

```text
runs/demo/reports/report.md
```

示例报告会包含 RQ1-RQ4 结构：

- RQ1：token reduction
- RQ2：functional quality
- control groups
- RQ3：components
- RQ4：generalization hooks

## 当前实现与论文的距离

这版工具是“可运行复现骨架”，不是声称已经复刻论文全部实验数值。

已经实现：

- 数据集生成和导入
- 技能扫描和 taxonomy 统计
- Stage 1/Stage 2 压缩产物生成
- D/A/C、控制组、消融组评估
- feedback promotion mock
- 报告和打包
- 标准库 LLM 客户端扩展点

尚待接入：

- 真实 LLM semantic segmentation/classification/compression
- 真实 Claude Code/OpenCode trigger validation
- 真实 LLMLingua baseline
- 真实 SkillsBench deterministic verifier
- 论文规模的 55,315 skills 数据集
- 多模型跨框架实验

## 设计原则

这个实现有三个原则：

1. 先让链路完整跑通，再逐步替换真实组件。
2. 默认少依赖，真实模型和第三方工具作为可选增强。
3. 每个输出都可审计：压缩结果、任务评分、配置快照、报告都落盘。

这样做的价值是清晰的：即使没有论文数据和昂贵 API，也能在本地验证 SkillReducer 的核心工程思想；一旦有真实数据和模型配置，同一套 CLI 和报告结构可以继续承载更接近论文的复现实验。

