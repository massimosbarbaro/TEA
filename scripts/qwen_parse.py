#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse Qwen raw outputs into (a) person predictions in the pipeline format and
(b) kinship relations, so both can be scored the same way as the other methods.

Input: qwen_raw.json  =  {"<text_id>": "<raw model output string>", ...}
       texts file     =  {record_or_docid: {"text": ...}} OR {docid:{text}}
Output: qwen_predictions.json (persons, pipeline format) and qwen_relations.json

Usage:
  python qwen_parse.py --raw qwen_raw.json --texts test_53_texts.json \
      --gold test_53_gold.json --out-pred qwen_predictions.json \
      --out-rel qwen_relations.json
"""
import argparse, json, re

def extract_json(s):
    s = re.sub(r"```json|```", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0: return {}
    try: return json.loads(s[i:j+1])
    except Exception: return {}

def find_offsets(name, text, used):
    for m in re.finditer(re.escape(name.split()[0]), text):
        if m.start() not in used:
            used.add(m.start()); return m.start(), m.start()+len(name)
    return 0, len(name)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out-pred", required=True)
    ap.add_argument("--out-rel", required=True)
    a = ap.parse_args()
    raw = json.load(open(a.raw, encoding="utf-8"))
    texts = json.load(open(a.texts, encoding="utf-8"))
    gold = json.load(open(a.gold, encoding="utf-8"))
    docid = {str(k): v.get("doc_id", f"rec_{k}") for k, v in gold.items()}
    txt_by_rec = {str(k): (v["text"] if isinstance(v, dict) else v) for k, v in texts.items()}

    preds, rels = [], []
    for tid, out in raw.items():
        rec = str(int(re.search(r"(\d+)$", tid).group(1)))
        did = docid.get(rec, tid)
        text = txt_by_rec.get(rec, "")
        obj = extract_json(out)
        used = set()
        plist = []
        for p in obj.get("persons", []):
            nm = (p.get("name") or "").strip()
            if not nm: continue
            s, e = find_offsets(nm, text, used)
            plist.append({"surface": nm, "label": "PERS", "start": s, "end": e, "score": 1.0})
        preds.append({"text_id": did, "predictions": plist})
        for k in obj.get("kinship", []):
            rels.append({"doc_id": did,
                         "subject": (k.get("subject") or "").strip(),
                         "relation_type": (k.get("relation_type") or "").strip(),
                         "related_person": (k.get("related_person") or "[unnamed]").strip(),
                         "status": (k.get("status") or "").strip()})
    json.dump(preds, open(a.out_pred, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"relations": rels}, open(a.out_rel, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"persons -> {a.out_pred} ({sum(len(b['predictions']) for b in preds)} spans)")
    print(f"kinship -> {a.out_rel} ({len(rels)} relations)")

if __name__ == "__main__":
    main()
