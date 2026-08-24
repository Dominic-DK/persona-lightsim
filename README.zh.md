# persona-lightsim

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **中文**

面向 [Claude Code](https://claude.com/claude-code) 的轻量级用户画像市场调研与仿真框架。将任意产品映射到**10个国家的合成人口**(NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia))上,产出用例分析、付费意愿判读、批量判定的反应仿真,以及可复用的画像卡片 — **无需 Web 应用、无需仿真服务器,数据仅 63MB。**

## 让 AI 帮你完成安装

把下面的内容直接粘贴给 Claude Code(或任何编码智能体):

```
帮我安装 https://github.com/Dongkyu-ES/persona-lightsim:
1. git clone https://github.com/Dongkyu-ES/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # 从 HuggingFace 下载 63MB 精简数据集 + 创建 pyarrow venv
3. 运行安装脚本输出的冒烟测试命令,并把结果给我看。
技能文档切换语言: python3 scripts/set_language.py ko (默认为英文)。
```

就这样。用 Claude Code 打开仓库后即可提出请求:

- *"把产品 X 映射到 10 国画像上,分析用例和付费意愿"* → `persona-research` 技能(按国家并行扇出分析)
- *"用这份产品简报对 100 个韩国画像跑一次轻量仿真并生成 pack"* → `persona-lightsim` 技能(批量判定 → mean-field 二次遍历 → 卡片蒸馏 → sqlite pack)

## 组成

| 组件 | 作用 |
|---|---|
| `.claude/skills/persona-research` | 编排器: 简报审计 → 采样 → 按国家扇出分析 → 综合 → QA |
| `.claude/skills/persona-country-analysis` | 单元方法论: 实计数筛查 → 精读 → 7 节结构化报告 |
| `.claude/skills/persona-lightsim` | 无对话仿真: 批量判定(1 次调用=25 人) → 确定性聚合 → 舆论再注入二次遍历 → 分群卡片 → 本地 pack |
| `.claude/agents/persona-*` (5 个) | brief-auditor / country-analyst / synthesis-critic / batch-judge / distiller |
| `scripts/setup_data.py` | 下载精简数据集(sha256 固定清单) + 构建 venv |
| `scripts/set_language.py` | 在 `en`/`ko` 之间切换当前生效的技能/智能体文档 |

原框架对整条流水线的实测数据: 批量判定 schema 有效率 99/99,二次遍历意见变化率 24.2%(既非 0% 也非 100% — 证明 mean-field 再注入确实生效),卡片证据引用 39/39 与样本原文逐字核验。

## 数据

`scripts/setup_data.py` 获取的是**精简包** — [`__HF_DATASET_ID__`](https://huggingface.co/datasets/__HF_DATASET_ID__) — NVIDIA Nemotron-Personas(CC-BY-4.0)的衍生再分发版:

- 10 个国家: 比利时、巴西、萨尔瓦多、法国、印度、日本、韩国、新加坡、美国、越南
- 每国 10,000 人,从 0.1M~1.2M 原始数据以固定种子 42 抽样
- 仅保留 26 列中本框架实际读取的 15 列,长叙事字段截断至 300~400 字符
- 保留原始分片结构(比利时语言配额、印度仅英语) — 采样器在精简/完整数据上无需修改即可运行
- **总计 ~63MB**(原始数据 ~24GB)

如需未截断的完整数据,请从 HuggingFace 下载 NVIDIA 原始数据集并用环境变量指定:

```bash
export NEMOTRON_PERSONAS_BASE=/path/to/full-data   # nemotron-personas-*/ 的父目录
```

## 注意与局限

- 画像是合成的人口构成,不是行为日志。所有技能都强制将结论写成**"方向性假设"**,需以实验验证。
- 轻量仿真是 **mean-field 近似**: 能捕捉从众、硬化等一阶社会效应;回音室、传播动力学等结构效应不在范围内。
- 智能体定义默认 `model: opus` — 可在 `.claude/agents/*.md` 中修改。

## 许可

代码: [MIT](LICENSE)。精简数据集: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/),衍生自 NVIDIA Nemotron-Personas(© NVIDIA, CC-BY-4.0) — 署名细节见数据集卡片。
