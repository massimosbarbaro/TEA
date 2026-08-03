#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST 5 - Rules-only baseline.
Extracts person spans from the record texts using explicit diplomatic rules,
no model, and writes predictions in the pipeline format so your
step2_evaluate.py can score them the same way as RoBERTa and Qwen.

Rules:
  - feudatory: the first proper-name sequence in the body (opening formula).
  - collective co-parties: names after "pro se et", "et fratribus suis" chains.
  - rectors: proper names after a tenure/cultivation verb or property head + per,
    with chains joined by et / commas.

Usage:
  python rules_only_predict.py --texts test_53_texts.json --gold test_53_gold.json \
      --out rules_only_predictions.json
"""
import argparse, json, re, unicodedata

VERB = r"(?:rect[aeiou]m?|recta|recti|laboratur|laborat[ae]m?|colitur|regitur|habitatur|habitatum|possidetur|tenetur)"
HEAD = r"(?:mansus|mansum|manso|pecia|peciam|decima|decimam|vassalaticum|bonum|dimidius|dimidium)"
PER = re.compile(rf"(?:{VERB}\s+per\s+|{HEAD}\s+per\s+)", re.I)
NAME = re.compile(r"[A-Z][A-Za-zçäöü]+")

def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()

def grab_chain(text, pos):
    seg = re.split(r"\bitem\b|;|\.\s|In\s+[A-Z]", text[pos:pos+90], 1)[0]
    out = []
    for part in re.split(r"\s+et\s+(?:per\s+)?|\s*,\s*", seg):
        part = part.strip()
        if not part: continue
        if re.match(r"(dominum|dominos|dictos|supradictum|eum|eundem|eos|ipsum|se|socios?|uxorem|filium|heredes|nepotem)\b", part, re.I):
            continue
        m = NAME.match(part)
        if m:
            a = pos + seg.find(m.group(0))
            out.append((m.group(0), a, a+len(m.group(0))))
    return out

FORMULA = {"recognitio", "recognitiones", "investitio", "investitura", "investitione",
           "item", "imprimis", "de", "recognovit", "confessus", "confessi", "dominus",
           "domini", "domino", "dominum", "bona", "data", "eodem", "anno", "qualiter"}

def extract(text):
    spans = []
    # feudatory: first proper name that is not a formula word (skip rubric words)
    for m in NAME.finditer(text):
        if m.group(0).lower() not in FORMULA:
            spans.append({"surface": m.group(0), "label": "PERS",
                          "start": m.start(), "end": m.end(), "score": 1.0})
            break
    # collective co-parties
    for mm in re.finditer(r"(?:pro se et|et fratribus suis|et consanguineis)\s+", text, re.I):
        for nm, a, b in grab_chain(text, mm.end()):
            spans.append({"surface": nm, "label": "PERS", "start": a, "end": b, "score": 1.0})
    # rectors
    for mm in PER.finditer(text):
        for nm, a, b in grab_chain(text, mm.end()):
            spans.append({"surface": nm, "label": "PERS", "start": a, "end": b, "score": 1.0})
    # dedup by offset
    seen, uniq = set(), []
    for s in sorted(spans, key=lambda x: x["start"]):
        k = (s["start"], s["end"])
        if k not in seen: seen.add(k); uniq.append(s)
    return uniq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texts", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    texts = json.load(open(a.texts, encoding="utf-8"))
    gold = json.load(open(a.gold, encoding="utf-8"))
    # map record -> doc_id from gold
    docid = {str(k): v.get("doc_id", f"rec_{k}") for k, v in gold.items()}
    out = []
    for rec, v in texts.items():
        out.append({"text_id": docid.get(str(rec), f"rec_{rec}"),
                    "predictions": extract(v["text"])})
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # quick self-eval (lenient stem match), real numbers come from step2_evaluate.py
    def lenient(gsurf, spans):
        gt = [fold(t) for t in gsurf.split() if len(t) >= 4]
        for s in spans:
            p = fold(s["surface"])
            for g in gt:
                if len(p) >= 4 and (g.startswith(p) or p.startswith(g)): return True
        return False
    tot = found = 0
    by_role = {}
    pred_by_rec = {b["text_id"]: b["predictions"] for b in out}
    for rec, v in gold.items():
        did = v["doc_id"]; sp = pred_by_rec.get(did, [])
        for p in v["persons"]:
            tot += 1
            hit = lenient(p["surface"], sp)
            found += hit
            r = p["role"]; by_role.setdefault(r, [0,0]); by_role[r][1]+=1; by_role[r][0]+=hit
    print(f"written: {a.out}")
    print(f"[approx self-eval, lenient] overall recall {found}/{tot} = {found/tot:.1%}")
    for r,(f,t) in sorted(by_role.items()):
        print(f"   {r:14} {f}/{t} = {f/t:.1%}")
    print("(authoritative numbers: run your step2_evaluate.py on the output)")

if __name__ == "__main__":
    main()
