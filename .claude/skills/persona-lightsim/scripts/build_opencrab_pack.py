#!/usr/bin/env python3
"""증류된 페르소나 카드 → 로컬 오픈크랩 팩(sqlite + nodes.json) 적재/질의.

opencrab_data/ 시드 팩과 같은 노드 문법(space/node_type/node_id/properties)을 따른다.
불변(PersonaCard/Evidence)과 가변(Judgment — 특정 브리프에 결합)을 분리 적재해,
제품이 바뀌면 Judgment 노드만 재생성하면 된다.

적재:
  python3 build_opencrab_pack.py build --cards cards.json --brief brief.md \
      --brief-id readlate --pack persona_pack.sqlite3
질의(골 검증 3종):
  python3 build_opencrab_pack.py query --pack persona_pack.sqlite3 --q payment_segments
  python3 build_opencrab_pack.py query --pack persona_pack.sqlite3 --q top_objections
  python3 build_opencrab_pack.py query --pack persona_pack.sqlite3 --q card_evidence --card <card_id>
표준 라이브러리만 사용.
"""
import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    space TEXT NOT NULL,
    node_type TEXT NOT NULL,
    node_id TEXT NOT NULL UNIQUE,
    properties_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relation TEXT NOT NULL,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(relation, from_node, to_node)
);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def upsert_node(cur, space, node_type, node_id, props):
    cur.execute(
        "INSERT INTO nodes(space, node_type, node_id, properties_json, created_at) "
        "VALUES(?,?,?,?,?) ON CONFLICT(node_id) DO UPDATE SET "
        "properties_json=excluded.properties_json",
        (space, node_type, node_id, json.dumps(props, ensure_ascii=False), now()),
    )


def add_edge(cur, relation, from_node, to_node):
    cur.execute(
        "INSERT OR IGNORE INTO edges(relation, from_node, to_node, created_at) "
        "VALUES(?,?,?,?)",
        (relation, from_node, to_node, now()),
    )


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")[:48]


def build(args):
    cards_doc = json.load(open(args.cards, encoding='utf-8'))
    cards = cards_doc["cards"] if isinstance(cards_doc, dict) else cards_doc

    conn = sqlite3.connect(args.pack)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    brief_node = f"pp:brief:{args.brief_id}"
    upsert_node(cur, "resource", "ProductBrief", brief_node, {
        "name": args.brief_id,
        "source_path": os.path.abspath(args.brief),
        "loaded_at": now(),
    })

    n_cards = n_evi = 0
    for card in cards:
        card_id = card.get("card_id") or slug(card["segment"])
        card_node = f"pp:card:{card_id}"
        seg_node = f"pp:segment:{slug(card['segment'])}"

        upsert_node(cur, "concept", "Segment", seg_node, {
            "label": card["segment"],
            "country": card.get("country", ""),
            "size_pct": card.get("size_pct"),
        })
        # 불변: 인구·서사
        upsert_node(cur, "concept", "PersonaCard", card_node, {
            "label": card["immutable"].get("label", card_id),
            "country": card.get("country", ""),
            "demographics": card["immutable"].get("demographics", ""),
            "narrative": card["immutable"].get("narrative", ""),
        })
        add_edge(cur, "represents", card_node, seg_node)
        n_cards += 1

        for i, ev in enumerate(card.get("evidence", [])):
            ev_node = f"pp:evidence:{card_id}:{i}"
            upsert_node(cur, "resource", "Evidence", ev_node, {
                "quote": ev.get("quote", ""),
                "persona_idx": ev.get("persona_idx"),
                "field": ev.get("field", ""),
            })
            add_edge(cur, "supported_by", card_node, ev_node)
            n_evi += 1

        # 가변: 이 브리프에 대한 판정 (브리프 교체 시 이 노드만 재생성)
        j = card.get("judgment", {})
        j_node = f"pp:judgment:{args.brief_id}:{card_id}"
        upsert_node(cur, "concept", "Judgment", j_node, {
            "adoption": j.get("adoption"),
            "payment": j.get("payment"),
            "key_reason": j.get("key_reason", ""),
            "key_objection": j.get("key_objection", ""),
            "opinion_shift": j.get("opinion_shift", "none"),
        })
        add_edge(cur, "judged_for", j_node, brief_node)
        add_edge(cur, "judged_by", j_node, card_node)

    conn.commit()

    # nodes.json 내보내기 (opencrab_data/docs/nodes.json과 동일 문법)
    export = {}
    for space, node_type, node_id, props, created in cur.execute(
        "SELECT space, node_type, node_id, properties_json, created_at FROM nodes"
    ):
        export[f"{space}::{node_id}"] = {
            "space": space, "node_type": node_type, "node_id": node_id,
            "properties": json.loads(props), "updated_at": created,
        }
    export_path = os.path.splitext(args.pack)[0] + "_nodes.json"
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    print(f"pack built: cards={n_cards}, evidence={n_evi}, "
          f"nodes={len(export)}, db={args.pack}, export={export_path}")
    conn.close()


def query(args):
    conn = sqlite3.connect(args.pack)
    cur = conn.cursor()

    def props(node_id):
        row = cur.execute("SELECT properties_json FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        return json.loads(row[0]) if row else {}

    if args.q == "payment_segments":
        # 지불 의사가 있는 판정 → 카드 → 세그먼트 (근거: 판정의 key_reason)
        rows = cur.execute("""
            SELECT j.node_id, j.properties_json, e2.to_node
            FROM nodes j
            JOIN edges e2 ON e2.from_node = j.node_id AND e2.relation = 'judged_by'
            WHERE j.node_type = 'Judgment'
        """).fetchall()
        out = []
        for j_id, j_props, card_id in rows:
            jp = json.loads(j_props)
            if jp.get("payment") in ("lifetime", "monthly"):
                cp = props(card_id)
                seg = cur.execute(
                    "SELECT to_node FROM edges WHERE from_node=? AND relation='represents'",
                    (card_id,)).fetchone()
                out.append({
                    "segment": props(seg[0]).get("label") if seg else None,
                    "card": cp.get("label"),
                    "payment": jp.get("payment"),
                    "근거": jp.get("key_reason"),
                })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return len(out)

    if args.q == "top_objections":
        rows = cur.execute(
            "SELECT properties_json FROM nodes WHERE node_type='Judgment'").fetchall()
        objections = [json.loads(r[0]).get("key_objection") for r in rows]
        objections = [o for o in objections if o]
        print(json.dumps(objections, ensure_ascii=False, indent=2))
        return len(objections)

    if args.q == "card_evidence":
        card_node = f"pp:card:{args.card}"
        evs = cur.execute(
            "SELECT to_node FROM edges WHERE from_node=? AND relation='supported_by'",
            (card_node,)).fetchall()
        out = {"card": props(card_node), "evidence": [props(e[0]) for e in evs]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return len(evs)

    raise SystemExit(f"unknown query: {args.q}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--cards', required=True)
    b.add_argument('--brief', required=True)
    b.add_argument('--brief-id', required=True)
    b.add_argument('--pack', required=True)
    q = sub.add_parser('query')
    q.add_argument('--pack', required=True)
    q.add_argument('--q', required=True)
    q.add_argument('--card', default=None)
    args = ap.parse_args()
    if args.cmd == 'build':
        build(args)
    else:
        n = query(args)
        raise SystemExit(0 if n else 1)


if __name__ == '__main__':
    main()
