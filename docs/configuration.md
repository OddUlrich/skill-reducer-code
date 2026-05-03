# SkillReducer 配置与操作文档

本文档说明如何配置、运行和迁移 SkillReducer 复现工具。当前实现默认采用标准库和 mock 流程，适合离线自测；真实 LLM、真实 agent trigger 和第三方基线可通过后续适配器接入。

## 环境要求

- Python `3.11+`
- 默认无需第三方依赖
- 可选依赖：
  - `tiktoken`：启用论文一致的 `cl100k_base` token 计数
  - 真实 LLM API key：启用 OpenAI-compatible `/chat/completions` 调用

验证环境：

```powershell
python --version
python -m skillreducer --help
```

如果没有安装为包，也可以在项目根目录直接运行：

```powershell
python -m skillreducer --help
```

## 推荐目录布局

```text
skill-reducer-code/
  data/
    synthetic/          # dataset make 生成的合成数据集
    imported/           # dataset import 导入的真实技能集
  runs/
    demo/               # reproduce 输出
  skillreducer/         # 工具源码
  docs/                 # 文档
```

一个数据集目录应包含：

```text
dataset/
  skills/
    some-skill/
      SKILL.md
      references/
      scripts/
  manifest.jsonl
  tasks.jsonl
```

`manifest.jsonl` 和 `tasks.jsonl` 对导入数据不是强制要求；缺失时工具会使用默认任务生成逻辑。

## 配置文件

当前 CLI 接受 `--config config.toml`，并会把配置快照保存到运行目录。第一版实现使用 mock 默认值，不强依赖配置文件。建议使用如下模板，为后续真实模型/agent 适配保留字段：

```toml
mode = "mock"

[tokenizer]
prefer_tiktoken = true

[llm.compressor]
mode = "mock"
base_url = ""
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-chat"
timeout = 60

[llm.evaluator]
mode = "mock"
base_url = ""
api_key_env = "QWEN_API_KEY"
model = "qwen-evaluator"
timeout = 60

[agent]
trigger_adapter = "mock"
max_restore_steps = 3
max_reference_calls = 6

[gate2]
tasks_per_skill = 5
feedback_iterations = 2
```

真实 API 模式的环境变量示例：

```powershell
$env:DEEPSEEK_API_KEY="..."
$env:QWEN_API_KEY="..."
```

注意：工具不会把 API key 写入运行产物，只保存配置快照和结果日志。

## 常用操作

生成 small 合成数据集：

```powershell
python -m skillreducer dataset make --out data\synthetic --size small
```

运行完整复现链路：

```powershell
python -m skillreducer reproduce --dataset data\synthetic --out runs\demo
```

仅扫描技能统计：

```powershell
python -m skillreducer scan --skills data\synthetic\skills --out runs\demo\reports\stats.jsonl
```

仅执行压缩：

```powershell
python -m skillreducer reduce --skills data\synthetic\skills --out runs\demo\compressed
```

仅执行评估：

```powershell
python -m skillreducer eval --dataset data\synthetic --compressed runs\demo\compressed --out runs\demo\reports
```

打包运行产物：

```powershell
python -m skillreducer package --input runs\demo --archive runs\demo.zip
```

## 迁移到其他机器

打包工具本体：

```powershell
python -m zipapp . -m "skillreducer.cli:main" -o skillreducer.pyz
```

在目标机器运行：

```powershell
python skillreducer.pyz dataset make --out data\synthetic --size small
python skillreducer.pyz reproduce --dataset data\synthetic --out runs\demo
```

打包实验产物：

```powershell
python -m skillreducer package --input runs\demo --archive runs\demo.zip
```

## 输出文件说明

`reproduce` 会生成：

```text
runs/demo/
  compressed/
    reduction.jsonl
    <skill>/
      SKILL.md
      references/*.md
      skillreducer.json
  reports/
    stats.jsonl
    task_results.jsonl
    summary.json
    report.md
  config.snapshot.toml
  run_summary.json
```

关键文件：

- `compressed/<skill>/SKILL.md`：压缩后的 core skill
- `compressed/<skill>/references/*.md`：按需加载 reference modules
- `compressed/<skill>/skillreducer.json`：单个 skill 的压缩日志
- `reports/report.md`：论文式复现实验报告
- `reports/task_results.jsonl`：逐任务逐条件评分
- `reports/stats.jsonl`：扫描统计

## 故障排查

- `No module named skillreducer`：请在项目根目录运行，或先执行 `pip install -e .`
- token 计数与论文不完全一致：默认是标准库近似计数；安装 `tiktoken` 后会自动使用 `cl100k_base`
- 导入真实数据后没有任务：可以先运行 `scan` 和 `reduce`；`eval` 会生成简单 fallback tasks，但要复现实验质量建议补充 `tasks.jsonl`
- P/LLMLingua 条件显示为 mock：当前实现提供 LLMLingua-compatible mock baseline，真实 LLMLingua 可作为后续可选适配器接入

