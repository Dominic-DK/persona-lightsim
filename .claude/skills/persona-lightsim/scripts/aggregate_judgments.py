#!/usr/bin/env python3
"""배치 판정 결과의 검증 + 결정적 집계.

경량 2-pass 시뮬레이션의 중간 단계:
- 판정 JSONL의 스키마 유효성 검증 (M1 게이트: 유효율 리포트)
- 여론 분포 집계 (adoption/payment/segment/objection)
- 2차 패스 재주입용 여론 요약(markdown) 생성

사용:
  python3 aggregate_judgments.py --judgments <dir|glob prefix> --pass-name pass1 \
      --out <출력 디렉토리>
표준 라이브러리만 사용.
"""
import argparse
import glob
import json
import os
from collections import Counter

VALID_ADOPTION = {"yes", "maybe", "no"}
VALID_PAYMENT = {"lifetime", "monthly", "free_ads", "none"}
REQUIRED = ["idx", "adoption", "payment", "reason", "segment"]


def load_judgments(judgments_dir, pass_name):
    rows, errors = [], []
    files = sorted(glob.glob(os.path.join(judgments_dir, f"{pass_name}_*.jsonl")))
    for path in files:
        for ln, line in enumerate(open(path, encoding='utf-8'), 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{os.path.basename(path)}:{ln} JSON 파싱 실패: {e}")
                continue
            problems = [f for f in REQUIRED if f not in r]
            if r.get("adoption") not in VALID_ADOPTION:
                problems.append(f"adoption={r.get('adoption')}")
            if r.get("payment") not in VALID_PAYMENT:
                problems.append(f"payment={r.get('payment')}")
            if r.get("adoption") == "no" and r.get("payment") != "none":
                problems.append("no인데 payment!=none")
            if problems:
                errors.append(f"{os.path.basename(path)}:{ln} {problems}")
                continue
            rows.append(r)
    return rows, errors, files


def aggregate(rows):
    n = len(rows)
    adoption = Counter(r["adoption"] for r in rows)
    payment = Counter(r["payment"] for r in rows)
    segment = Counter(r["segment"] for r in rows)
    objections = Counter(
        r["objection"].strip() for r in rows
        if r.get("objection") and str(r.get("objection")).lower() != "null"
    )
    result = {
        "n": n,
        "adoption": dict(adoption.most_common()),
        "payment": dict(payment.most_common()),
        "segments_top": segment.most_common(12),
        "objections_top": objections.most_common(10),
    }
    # 2차 패스면 여론 재주입에 의한 의견 변화 분포도 집계한다
    shifts = Counter(r["opinion_shift"] for r in rows if "opinion_shift" in r)
    if shifts:
        result["opinion_shift"] = dict(shifts.most_common())
        changed = sum(c for k, c in shifts.items() if k != "none")
        result["shift_rate"] = round(changed / max(n, 1), 4)
    return result


def opinion_summary_md(agg):
    """2차 패스 재주입용 여론 요약 — 개인 식별 없이 분포와 논거만."""
    n = agg["n"]
    def pct(c):
        return f"{c} ({c / max(n,1) * 100:.0f}%)"
    lines = [
        "## 1차 반응 여론 요약 (동료 시민 %d명의 반응 분포)" % n,
        "",
        "채택 의향: " + ", ".join(f"{k}={pct(v)}" for k, v in agg["adoption"].items()),
        "지불 의향: " + ", ".join(f"{k}={pct(v)}" for k, v in agg["payment"].items()),
        "",
        "가장 흔한 반대 논거:",
    ]
    for obj, c in agg["objections_top"][:5]:
        lines.append(f"- ({c}명) {obj}")
    lines += ["", "주요 세그먼트:"]
    for seg, c in agg["segments_top"][:6]:
        lines.append(f"- {seg}: {c}명")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--judgments', required=True)
    ap.add_argument('--pass-name', default='pass1')
    ap.add_argument('--out', required=True)
    ap.add_argument('--expected-n', type=int, default=None,
                    help='기대 판정 수 (표본 크기). 지정 시 게이트 판정에 사용')
    args = ap.parse_args()

    rows, errors, files = load_judgments(args.judgments, args.pass_name)
    total_lines = len(rows) + len(errors)
    validity = len(rows) / max(total_lines, 1)

    os.makedirs(args.out, exist_ok=True)
    agg = aggregate(rows)
    agg["validity_rate"] = round(validity, 4)
    agg["error_count"] = len(errors)
    agg["source_files"] = [os.path.basename(f) for f in files]

    with open(os.path.join(args.out, f"{args.pass_name}_aggregate.json"), 'w', encoding='utf-8') as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.out, f"{args.pass_name}_opinion_summary.md"), 'w', encoding='utf-8') as f:
        f.write(opinion_summary_md(agg))
    if errors:
        with open(os.path.join(args.out, f"{args.pass_name}_errors.txt"), 'w', encoding='utf-8') as f:
            f.write("\n".join(errors))

    gate_ok = validity >= 0.95 and (args.expected_n is None or len(rows) >= args.expected_n * 0.95)
    print(f"{args.pass_name}: valid={len(rows)}/{total_lines} ({validity*100:.1f}%), "
          f"errors={len(errors)}, gate={'PASS' if gate_ok else 'FAIL'}")
    print(f"adoption: {agg['adoption']}")
    print(f"payment: {agg['payment']}")
    raise SystemExit(0 if gate_ok else 1)


if __name__ == '__main__':
    main()
