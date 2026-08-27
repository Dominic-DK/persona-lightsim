# persona-lightsim

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **中文**

面向 [Claude Code](https://claude.com/claude-code) 的轻量级用户画像市场调研与仿真框架。将任意产品映射到**10个国家的合成人口**(NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia))上,产出用例分析、付费意愿判读、批量判定的反应仿真,以及可复用的画像卡片 — **无需 Web 应用、无需仿真服务器,数据仅 63MB。**

## 让 AI 帮你完成安装

把下面的内容直接粘贴给 Claude Code(或任何编码智能体):

```
帮我安装 https://github.com/Dominic-DK/persona-lightsim:
1. git clone https://github.com/Dominic-DK/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # 从 HuggingFace 下载 63MB 精简数据集 + 创建 pyarrow venv
3. 运行安装脚本输出的冒烟测试命令,并把结果给我看。
技能文档切换语言: python3 scripts/set_language.py ko (默认为英文)。
```

就这样。用 Claude Code 打开仓库后即可提出请求:

- *"把产品 X 映射到 10 国画像上,分析用例和付费意愿"* → `persona-research` 技能(按国家并行扇出分析)
- *"用这份产品简报对 100 个韩国画像跑一次轻量仿真并生成 pack"* → `persona-lightsim` 技能(批量判定 → mean-field 二次遍历 → 卡片蒸馏 → sqlite pack)

## 使用方法

用 Claude Code 打开仓库,一句话说清要跑什么。一次请求由四个槽位组成:

> **{产品 — 以及它的代码或文档在哪}** → **{哪些国家}** → **{每国多少人}** → **{你真正想问的问题}**

必填的只有产品。国家默认全部 10 个,样本默认每国 n=1000,分析轴默认是"用例 + 付费意愿"。留空的槽位要么走默认值,要么只追问一次。

### 全市场扫描

生成 [`examples/quest15/`](examples/quest15/) 的那次请求:

```
Projects/Quest15 是一个 iOS 应用,在你当前所在的位置给出一个 10~15 分钟的
小冒险。读一下仓库,从真实代码构建产品简报,然后映射到全部 10 个国家,
n=1000,分析用例和付费意愿。
```

框架会从代码库起草简报,由 `persona-brief-auditor` 剔除所有没有代码级证据的陈述,每国抽样约 1,000 人,让 10 位国别分析师彼此不可见地并行工作,做跨市场综合,再把草稿交给对抗式评审,最后才写出终稿。全程约 30 分钟。

### 收窄国家,磨利问题

```
用 TripRoll 简报只跑韩国、日本、越南,每国 1000 人。不要泛泛的用例 —
我要知道在这三个市场里,每次旅行一次性收 9,900 韩元和按月订阅哪个更行得通。
```

指定分析轴会改变所有分析师的检索方向。好用的轴包括:价格结构对比、功能优先级、定位与信息传达、流失风险、某个细分人群的真实规模。

### 聚焦某个细分人群

```
同一份 TripRoll 简报,韩国 + 新加坡,n=1000。聚焦结伴出行的人 —
朋友、情侣、大家庭。在下任何结论之前,先量化这个人群在各自样本中
到底占多少。
```

### 轻量仿真与可复用 pack

```
用审核过的 Quest15 简报对 100 个韩国画像跑轻量仿真:批量判定、意见再注入
的二次遍历、蒸馏细分卡片、构建 sqlite pack。把两次遍历各自的接受度和
付费分布给我看。
```

100 人意味着每次遍历 4 次智能体调用(一次判定 25 人),两次遍历共 8 次,中间夹一步确定性聚合。产出包括逐人的接受/付费/异议判定、把首轮意见摘要再注入的二次结果、带样本原文引用的细分卡片,以及一个可查询的 sqlite pack。

### 还没有仓库时

```
还没有代码,只是个想法。[用 3~4 句具体事实说明:它做什么、给谁用、
打算怎么收费。] 用这些构建简报,凡是无法核实的都标为假设,然后跑
法国和比利时,n=1000,分析用例和定价。
```

这种情况下审核者没有可对照的代码,于是把这些陈述标为假设,分析师也按假设处理。简报是整个分析的天花板 — 输入含糊,输出也含糊。

### 后续请求

两个技能都会检测已有的 `_workspace/`,只重跑发生变化的部分:

- *"只重做韩国报告,这次从独自旅行者的视角。"*
- *"给现有的这次运行加上印度。"*
- *"简报变了 — 现在是广告免费模式。只刷新判定,样本和卡片的不变部分保留。"*
- *"重新蒸馏卡片,每张至少 3 条证据引用。"*
- *"查询 pack 里的付费细分。"* — pack 支持的查询是 `payment_segments`、`top_objections`、`card_evidence --card <card_id>`

### "条件"实际是怎么生效的

采样器只接受 `--countries`、`--n`、`--seed`,没有任何人口统计过滤器。因此"只要 30 多岁女性""结伴出行的人"这类条件是在**下游**生效的:在分析阶段用关键词与人口统计做筛查,报告会给出该人群在代表性样本中的真实计数。这通常正是你想要的 — 是在人口中的占比,而不是在预先过滤后的池子里的占比。

如果你确实需要硬过滤,明确说出来即可("只保留 30~39 岁的画像再分析"),智能体会对样本 JSONL 做后置过滤。但那份报告里的百分比是过滤后池子的占比,不能再和全样本的运行直接比较。

### 会留在磁盘上的东西

| 路径 | 内容 |
|---|---|
| `_workspace/persona-research/` | 简报、各国样本、各国报告、评审意见 — 审计线索 |
| `docs/research/persona-{product}-{YYYY-MM}.md` | 最终的跨市场文档 |
| `_workspace/persona-lightsim/` | 切片、两轮判定、聚合结果、`cards.json` |
| `_workspace/persona-lightsim/persona_pack.sqlite3` | 可查询的 pack(外加 `_nodes.json` 导出) |

样本可由种子复现,所以重跑时默认复用已有样本,而不是重新抽取。

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

`scripts/setup_data.py` 获取的是**精简包** — [`dominicDK94/nemotron-personas-lite`](https://huggingface.co/datasets/dominicDK94/nemotron-personas-lite) — NVIDIA Nemotron-Personas(CC-BY-4.0)的衍生再分发版:

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
