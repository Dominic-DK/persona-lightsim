---
name: persona-research
description: Nemotron-Personas 10개국 데이터(data/nemotron-personas-*)로 임의 제품/서비스의 시장·유즈케이스 분석을 실행하는 오케스트레이터. "페르소나 분석 돌려줘", "N명 뽑아서 유즈케이스", "OO 제품을 각국 사용자에 대입", "시장별 지불 의사", "타깃 세그먼트 정량화" 및 후속 요청("다시 실행", "재실행", "한국만 다시", "브리프 바꿔서 업데이트", "이전 결과 보완", "국가 추가") 시 반드시 이 스킬을 사용할 것. 웹앱·시뮬레이션 인프라 없이 에이전트 팬아웃만으로 동작하는 경량 트랙이다.
---

# 페르소나 리서치 오케스트레이터

**실행 모드: 하이브리드** — 샘플링·브리프(결정적 스크립트+서브 에이전트) → 국가 분석(서브 에이전트 병렬 팬아웃; 국가 간 분석은 의도적 블라인드 독립이라 팀 통신이 구조적으로 불필요) → 종합(리드) → 검증(서브 에이전트 QA). 에이전트 호출은 가용한 최상위 모델로 실행한다.

## 데이터 전달

파일 기반 + 반환값 기반. 작업 공간: `_workspace/persona-research/`

```
_workspace/persona-research/
├── brief.md                  # 제품 현실 브리프 (감사 완료본)
├── personas/{country}.jsonl  # 표본
├── reports/{country}.md      # 국가 리포트 (분석가 반환값을 리드가 저장)
└── critic.md                 # QA 발견
```

최종 산출물만 `docs/research/persona-{제품}-{YYYY-MM}.md`에 출력. `_workspace/`는 감사 추적용으로 보존한다.

## Phase 0: 컨텍스트 확인

1. `_workspace/persona-research/` 존재 여부 확인:
   - 있음 + 부분 수정 요청("한국만 다시", "브리프만 갱신") → **부분 재실행**: 해당 단계 에이전트만 재호출, 나머지 산출물 재사용
   - 있음 + 새 제품/새 표본 요청 → 기존을 `_workspace/persona-research_prev/`로 이동 후 **새 실행**
   - 없음 → **초기 실행**
2. 대상 제품 확인 — 브리프를 만들 제품 레포/문서 경로를 사용자 요청에서 확보. 없으면 이것 하나만 질문한다.
3. 분석 축 확인 — 기본은 "유즈케이스+지불의사". 요청이 특정 질문(기능 우선순위, 가격 실험, 포지셔닝)이면 그 축을 분석가 프롬프트에 명시한다.

## Phase 1: 브리프 (생성-검증 패턴)

1. 리드가 제품 레포/문서에서 브리프 초안 작성 — 기능/과금/알려진 실전 약점, 1~2페이지
2. `persona-brief-auditor` 에이전트로 감사 — 코드 근거 없는 문장은 제거 또는 "추정" 표기
3. 감사 완료본을 `_workspace/persona-research/brief.md`에 저장

브리프 품질이 전체 분석 품질의 상한이다. 이 Phase를 건너뛰지 마라.

## Phase 2: 샘플링 (결정적)

```bash
data/.venv-personas/bin/python .claude/skills/persona-research/scripts/sample_personas.py \
  --n 1000 --seed 42 --out _workspace/persona-research/personas [--countries korea,japan,...]
```

- 데이터가 없으면 먼저: `python3 scripts/setup_data.py` (라이트 팩 다운로드 + venv 구성)
- venv가 없으면: `python3 -m venv data/.venv-personas && data/.venv-personas/bin/pip install pyarrow` (또는 즉석 실행: `uv run --with pyarrow python3 ...`)
- 맨 `python3`로 실행하면 pyarrow가 없어 죽는다 — 스크립트가 위 두 대안을 안내하며 종료한다.
- 시드를 바꾸지 않는 한 표본은 재현된다. 재실행 시 기존 표본 재사용이 기본.
- 소규모(N<100)에서는 반올림 배분으로 국가당 수 명이 모자랄 수 있다(정상). N=1000에서는 996~1000명.
- 데이터 위치는 기본 `data/`, `NEMOTRON_PERSONAS_BASE` 환경변수로 오버라이드(라이트 팩/풀 데이터 모두 동작).

## Phase 3: 국가 분석 팬아웃

국가당 `persona-country-analyst` 1개를 **한 메시지에 동시 스폰**한다. 각 프롬프트에 포함:
- 에이전트 정의(`.claude/agents/persona-country-analyst.md`)와 `persona-country-analysis` 스킬을 따를 것
- 입력 2개: `brief.md` + `personas/{country}.jsonl` (절대경로)
- 분석 축 (Phase 0에서 확정한 것)
- 반환: 7섹션 리포트 텍스트

반환값을 리드가 `reports/{country}.md`로 저장한다.

## Phase 4: 교차 종합 (리드)

10개 리포트를 정독하고:
1. **교차 발견 3~5개** — 여러 나라에서 반복되는 패턴. 각 발견에 근거 국가 수를 명시
2. **액션 시사점** — 마케팅/제품/과금 각각, 즉시 실행 가능한 수준으로
3. 국가별 원문은 부록으로 전문 보존
4. 문서 서두에 데이터 출처·표본 방식·한계("방향 가설, 실험으로 검증할 것") 명시

## Phase 5: 검증 (QA)

`persona-synthesis-critic` 에이전트에 종합 초안+국가 리포트+표본 경로를 넘겨 재검한다. REFUTED 발견은 반영하고, 해소 불가 항목은 문서에 한계로 명시한다. 통과 후 `docs/research/`에 최종 저장하고 사용자에게 요약 보고한다.

## Phase 6 (선택): 경량 시뮬레이션 → 카드 증류 → 팩 적재

분석 결과를 넘어 "페르소나들의 제품 반응 판정", "여론 재주입 2-pass", "세그먼트 카드 증류", "로컬 팩 적재"가 필요하면 `persona-lightsim` 스킬로 이어진다. 이 트랙은 본 스킬의 표본·브리프 산출물을 그대로 입력으로 쓴다 (에이전트: `persona-batch-judge`, `persona-distiller`).

## 에러 핸들링

| 상황 | 처리 |
|---|---|
| 국가 분석가 1개 실패 | 1회 재시도 → 재실패 시 해당 국가 제외하고 진행, 종합에 누락 명시 |
| 표본 파일 없음 | Phase 2 재실행 (표본은 언제든 재생성 가능) |
| 데이터셋 미보유 국가 요청 | `python3 scripts/setup_data.py --countries <국가>` 실행 제안 후 사용자 확인 |
| 브리프 감사 불가(레포 접근 불가) | 진행 중단하고 사용자에게 제품 사실 확인 요청 — 감사 없이 팬아웃 금지 |
| 크리틱-분석가 판정 상충 | 삭제하지 않고 양론 병기 + 출처 명시 |

## 테스트 시나리오

1. **정상 흐름**: "제품 X를 10개국 페르소나에 대입해서 유즈케이스 분석해줘" → Phase 0~5 전체, `docs/research/persona-X-YYYY-MM.md` 산출
2. **부분 재실행**: "한국 리포트만 학습 도구 각도로 다시" → Phase 0에서 부분 재실행 판별 → korea 분석가만 재스폰 → 종합의 한국 관련 문장만 갱신 → 크리틱 부분 재검
3. **에러 흐름**: 브라질 분석가가 2회 실패 → 9개국으로 종합 진행, 서두에 "브라질 누락" 명시

## 비용/시간 기대치

실측(원 하네스): 10개국 병렬 분석 전체가 세션 1개, 약 30분. 별도 인프라 기동 불필요 — 이 스킬은 데이터 디렉토리와 에이전트만 쓴다.
