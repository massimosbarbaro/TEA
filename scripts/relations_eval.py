#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST 6 - Kinship relation evaluation.
Scores predicted relations against kinship_gold.json. A gold relation is matched
if a predicted relation has the same subject (lenient name match), the same
relation_type, and (optionally) the same living/deceased status.

Usage:
  python relations_eval.py --pred qwen_relations.json --gold kinship_gold.json
"""
import argparse, json, unicodedata, re

def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()

def name_match(a, b):
    a, b = fold(a), fold(b)
    if not a or not b: return False
    at, bt = a.split(), b.split()
    return bool(set(x for x in at if len(x) >= 4) & set(y for y in bt if len(y) >= 4)) or a == b

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--gold", required=True)
    a = ap.parse_args()
    P = json.load(open(a.pred, encoding="utf-8"))["relations"]
    G = json.load(open(a.gold, encoding="utf-8"))["relations"]
    def matched(g, require_status):
        for p in P:
            if p.get("doc_id") and g.get("doc_id") and p["doc_id"] != g["doc_id"]:
                continue
            if (name_match(p["subject"], g["subject"])
                    and p["relation_type"] == g["relation_type"]
                    and (not require_status or p.get("status") == g.get("status"))):
                return True
        return False
    for require_status in (False, True):
        tp = sum(1 for g in G if matched(g, require_status))
        r = tp/len(G) if G else 0
        tag = "type+subject+status" if require_status else "type+subject"
        print(f"relation recall ({tag}): {tp}/{len(G)} = {r:.1%}")
    # status accuracy on the deceased/living distinction alone
    dec_g = [g for g in G if g["status"] == "deceased"]
    dec_hit = sum(1 for g in dec_g if any(
        name_match(p["subject"], g["subject"]) and p.get("status") == "deceased" for p in P))
    print(f"deceased-status recall: {dec_hit}/{len(dec_g)} = {dec_hit/len(dec_g):.1%}" if dec_g else "n/a")

if __name__ == "__main__":
    main()
