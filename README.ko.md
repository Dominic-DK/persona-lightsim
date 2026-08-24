# persona-lightsim

[English](README.md) | **한국어** | [日本語](README.ja.md) | [中文](README.zh.md)

[Claude Code](https://claude.com/claude-code)용 경량 페르소나 시장조사·시뮬레이션 하네스. 임의 제품을 **10개국 합성 인구**(NVIDIA [Nemotron-Personas](https://huggingface.co/nvidia))에 대입해 유즈케이스 분석, 지불 의사 판독, 배치 판정 반응 시뮬레이션, 재사용 가능한 페르소나 카드를 산출한다 — **웹앱도, 시뮬레이션 서버도 없이, 데이터 63MB로.**

## AI한테 시키기

Claude Code(또는 아무 코딩 에이전트)에 이대로 붙여넣으면 된다:

```
https://github.com/Dongkyu-ES/persona-lightsim 셋업해줘:
1. git clone https://github.com/Dongkyu-ES/persona-lightsim && cd persona-lightsim
2. python3 scripts/setup_data.py        # 허깅페이스에서 63MB 라이트 데이터 다운로드 + pyarrow venv 생성
3. 셋업이 출력하는 스모크 테스트 명령을 실행하고 결과를 보여줘.
스킬 문서를 한국어로: python3 scripts/set_language.py ko (기본은 영어).
```

끝. 레포를 Claude Code로 열고 이렇게 요청하면 된다:

- *"제품 X를 10개국 페르소나에 대입해서 유즈케이스랑 지불 의사 분석해줘"* → `persona-research` 스킬 (국가별 분석가 병렬 팬아웃)
- *"이 브리프로 한국 100명 경량 시뮬 돌리고 팩 만들어줘"* → `persona-lightsim` 스킬 (배치 판정 → mean-field 2차 패스 → 카드 증류 → sqlite 팩)

## 구성

| 구성요소 | 역할 |
|---|---|
| `.claude/skills/persona-research` | 오케스트레이터: 브리프 감사 → 샘플링 → 국가별 분석 팬아웃 → 종합 → QA |
| `.claude/skills/persona-country-analysis` | 단위 방법론: 실카운트 스크리닝 → 정독 → 7섹션 리포트 |
| `.claude/skills/persona-lightsim` | 대화 없는 시뮬: 배치 판정(1호출=25명) → 결정적 집계 → 여론 재주입 2차 패스 → 세그먼트 카드 → 로컬 팩 |
| `.claude/agents/persona-*` (5종) | brief-auditor / country-analyst / synthesis-critic / batch-judge / distiller |
| `scripts/setup_data.py` | 라이트 데이터 다운로드(sha256 고정 매니페스트) + venv 구성 |
| `scripts/set_language.py` | 활성 스킬·에이전트 문서를 `en`/`ko`로 전환 |

원 하네스에서 파이프라인 전체를 실측한 수치: 배치 판정 스키마 유효 99/99, 2차 패스 의견 변화율 24.2%(0%도 100%도 아님 — mean-field 재주입이 실제로 작동함을 실증), 카드 근거 인용 39/39 표본 원문 대조 검증.

## 데이터

`scripts/setup_data.py`가 받는 것은 **라이트 팩** — [`dominicDK94/nemotron-personas-lite`](https://huggingface.co/datasets/dominicDK94/nemotron-personas-lite) — NVIDIA Nemotron-Personas(CC-BY-4.0)의 파생 재배포판이다:

- 10개국: 벨기에·브라질·엘살바도르·프랑스·인도·일본·한국·싱가포르·미국·베트남
- 국가당 10,000명, 원본 0.1M~1.2M에서 시드 42 고정 추출
- 26개 컬럼 중 하네스가 읽는 15개만 유지, 긴 서사 필드는 300~400자 트림
- 원본 샤드 구조 보존(벨기에 언어 쿼터, 인도 영어 전용) — 샘플러가 라이트/풀 데이터에서 무수정 동작
- **총 ~63MB** (원본은 ~24GB)

무트림 풀 데이터가 필요하면 NVIDIA 원본을 허깅페이스에서 받아 환경변수로 지정한다:

```bash
export NEMOTRON_PERSONAS_BASE=/path/to/full-data   # nemotron-personas-*/ 들의 부모 디렉토리
```

## 주의와 한계

- 페르소나는 합성 인구 구성이지 행동 로그가 아니다. 모든 스킬이 결론을 **"방향 가설"**로 쓰고 실험으로 검증하도록 강제한다.
- 경량 시뮬레이션은 **mean-field 근사**다: 동조·경화 같은 1차 사회효과는 잡히고, 에코챔버·전파 역학 같은 구조 효과는 범위 밖이다.
- 에이전트 정의 기본값은 `model: opus` — `.claude/agents/*.md`에서 수정.

## 라이선스

코드: [MIT](LICENSE). 라이트 데이터셋: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), NVIDIA Nemotron-Personas(© NVIDIA, CC-BY-4.0) 파생 — 출처표기 상세는 데이터셋 카드 참조.
