---
name: persona-lightsim
description: 노드 간 대화 없는 경량 페르소나 시뮬레이션 — 배치 판정(에이전트 1회가 25명 판정) → 결정적 집계 → 여론 재주입 2차 패스(mean-field) → 세그먼트 대표 카드 증류 → 로컬 팩(sqlite) 적재까지의 실행 방법론. "경량 시뮬레이션", "대화 없이 시뮬", "페르소나 반응/수용성 판정", "페르소나 카드 만들어", "팩으로 적재", "팩 질의", 및 후속 요청("2차 패스만 다시", "카드 다시 증류", "팩 재적재", "다른 브리프로 판정 갱신") 시 반드시 이 스킬을 사용할 것. 에이전트 간 실시간 상호작용 시뮬레이션(전파·개입 역학)이 필요한 질문은 이 스킬의 범위 밖이다(OASIS류 멀티에이전트 시뮬 트랙).
---

# 경량 페르소나 시뮬레이션 (persona-lightsim)

**실행 모드: 서브 에이전트** (배치 판정·증류는 독립 팬아웃 — 팀 통신 불필요. 집계·적재는 결정적 스크립트).

핵심 아이디어 2개:
1. **호출 단위는 배치다.** 페르소나당 LLM 1회가 아니라 `persona-batch-judge` 1회가 25명을 판정한다 — 표본 100명 = 패스당 4호출.
2. **상호작용은 mean-field 근사다.** 노드끼리 대화시키는 대신, 1차 판정을 결정적으로 집계해 "여론 요약"으로 2차 패스에 재주입한다. 동조·경화 같은 1차 사회효과는 잡히고, 에코챔버 같은 구조 효과는 포기한다(그건 상호작용 시뮬 트랙의 몫).

## 파이프라인

작업 공간: `_workspace/persona-lightsim/` (또는 실행별 디렉토리). 산출물 계약:

```
brief.md                      # 제품 사실 브리프 (persona-brief-auditor 감사 필수)
personas/{country}.jsonl      # 표본 (persona-research 샘플러)
slices/batch{i}.jsonl         # 25명 단위 슬라이스 (idx 필드 부여)
judgments/pass1_batch{i}.jsonl
aggregate/pass1_aggregate.json / pass1_opinion_summary.md
judgments/pass2_batch{i}.jsonl
aggregate/pass2_aggregate.json
cards.json                    # 증류된 페르소나 카드
persona_pack.sqlite3 (+ _nodes.json)
```

### 1단: 표본 + 슬라이스
`persona-research` 스킬의 샘플러로 표본 추출 후 25명 단위로 분할하며 각 행에 `idx`를 부여한다. idx는 판정·근거 인용의 조인 키다.

```bash
# 샘플러는 pyarrow가 필요하다 — 반드시 전용 venv로 실행 (맨 python3는 ModuleNotFoundError)
data/.venv-personas/bin/python .claude/skills/persona-research/scripts/sample_personas.py \
  --countries korea --n 100 --seed <시드> --out <run dir>/personas
# venv가 없으면 대안: uv run --with pyarrow python3 <같은 인자>
# 데이터가 아예 없으면 먼저: python3 scripts/setup_data.py
```

슬라이스 분할은 표본 JSONL을 라인 순서대로 읽어 25명씩 자르고, 각 행에 `idx`(0부터 전체 연번)를 넣어 `slices/batch{i}.jsonl`로 쓴다. 원본 표본 파일에는 idx가 없다 — 라인 순서가 곧 idx다.

### 2단: 배치 판정 (1-pass)
슬라이스당 `persona-batch-judge` 에이전트 1개를 동시 스폰. 판정 스키마:

```json
{"idx": int, "adoption": "yes|maybe|no", "payment": "lifetime|monthly|free_ads|none",
 "reason": "페르소나 원문 요소를 인용한 1문장", "objection": "1문장 또는 null", "segment": "짧은 라벨"}
```

규율: 브리프 밖 기능 가정 금지, no면 payment=none, 무관심 다수가 현실적(억지 yes 금지), 인원 누락 금지.

### 3단: 집계 (결정적, LLM 0회)
```bash
python3 .claude/skills/persona-lightsim/scripts/aggregate_judgments.py \
  --judgments <judgments dir> --pass-name pass1 --out <aggregate dir> --expected-n <표본수>
```
스키마 유효율 ≥95% 게이트를 겸한다(FAIL 시 해당 배치 재실행). 산출물 중 `pass1_opinion_summary.md`가 재주입 페이로드다.

### 4단: 여론 재주입 (2-pass)
같은 슬라이스에 `pass1_opinion_summary.md`를 추가로 주고 재판정한다. 2차 스키마는 1차 + `"opinion_shift": "none|softened|hardened"` + `"shift_reason"`(변화 시). 검증: 변화율이 0%도 100%도 아니어야 한다 — 0%는 요약을 안 읽은 신호, 100%는 과잉 동조 신호.

### 5단: 증류
`persona-distiller` 에이전트 1개가 2-pass 판정 + 원본 표본을 읽고 세그먼트 대표 카드를 만든다. **불변/가변 분리**가 스키마의 핵심이다:

```json
{"cards": [{"card_id": "kr-학습열망-중년", "segment": "...", "size_pct": 13.0, "country": "korea",
  "immutable": {"label": "...", "demographics": "...", "narrative": "..."},
  "evidence": [{"persona_idx": 12, "quote": "원문 인용", "field": "persona"}],
  "judgment": {"adoption": "...", "payment": "...", "key_reason": "...", "key_objection": "...", "opinion_shift": "..."}}]}
```

불변(immutable/evidence)은 인구·서사 — 제품과 무관하게 재사용. 가변(judgment)은 이 브리프에 결합 — 제품이 바뀌면 2~5단만 재실행해 judgment를 갱신한다.

### 6단: 팩 적재 + 질의
```bash
python3 .claude/skills/persona-lightsim/scripts/build_opencrab_pack.py build \
  --cards cards.json --brief brief.md --brief-id <제품슬러그> --pack persona_pack.sqlite3
python3 ...build_opencrab_pack.py query --pack ... --q payment_segments   # 검증 질의 3종
```
노드 문법은 space/node_type/node_id/properties 그래프 팩 형식 — sqlite와 `_nodes.json` 내보내기를 함께 산출하므로 외부 지식그래프 시스템에 반입할 수 있다. 반입 여부는 이 파이프라인 밖의 수동 결정이다.

## 에러 핸들링

| 상황 | 처리 |
|---|---|
| 배치 판정 스키마 유효율 <95% | 해당 배치만 재스폰 1회, 재실패 시 그 배치 제외하고 진행(집계에 결손 명시) |
| 2차 변화율 0% 또는 100% | 재주입 프롬프트 점검 후 해당 패스 1회 재실행, 반복 시 결과에 경고 명시 |
| 카드 근거 인용 <2개 | distiller에 부족 카드만 보강 재요청 |
| 팩 질의 빈 결과 | cards.json ↔ pack 스키마 정합 확인 (build 재실행) |

## 테스트 시나리오

1. **정상**: "브리프 X로 한국 100명 경량 시뮬 돌리고 팩 만들어" → 1~6단, 팩 질의 3종 통과 (원 하네스 실측: 99/99 유효, 2차 변화율 24.2%, 카드 8장·근거 인용 39/39 실물 검증)
2. **판정 갱신**: "브리프가 바뀌었어, 판정만 갱신해" → 기존 표본·카드 불변부 재사용, 2~5단 재실행 후 `build`가 Judgment 노드만 갱신
3. **에러**: batch2 유효율 80% → batch2만 재스폰 → 통과 후 집계 재실행
