#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST 3 - Post-processing baseline.
Reads a predictions file in the pipeline format
  [{"text_id":..., "predictions":[{"surface","label","start","end","score"}]}]
and a texts file {record_or_docid: {"text": ...}}, and writes a FILTERED
predictions file with subword fragments removed and adjacent BIO pieces merged.

Then score BOTH files with your own step2_evaluate.py to get precision/recall
before and after. The expected finding: precision rises, rector recall does not.

Usage:
  python postprocess_filter.py --pred roberta_53_predictions.json \
      --texts test_53_texts.json --out roberta_53_predictions_FILTERED.json
"""
import argparse, json, re

def load_texts(path):
    d = json.load(open(path, encoding="utf-8"))
    # accept {rec:{text}} or {docid:{text}}; index by text_id we will see in preds
    out = {}
    for k, v in d.items():
        out[str(k)] = v["text"] if isinstance(v, dict) else v
    return out

def text_for(text_id, texts):
    # text_id like tea_c12_0174 -> record 174; also allow bare record number keys
    m = re.search(r"(\d+)$", text_id)
    rec = str(int(m.group(1))) if m else text_id
    return texts.get(rec) or texts.get(text_id) or ""

def is_fragment(span, text, min_chars=4):
    s = span["surface"].strip()
    if len(s) < min_chars:
        return True
    a, b = span["start"], span["end"]
    before = text[a-1] if a-1 >= 0 else " "
    after = text[b] if b < len(text) else " "
    return before.isalpha() or after.isalpha()

def merge_adjacent(spans):
    # merge spans separated by <=1 char (BIO pieces split by the tokenizer)
    spans = sorted(spans, key=lambda x: x["start"])
    merged, cur = [], None
    for s in spans:
        if cur and s["start"] - cur["end"] <= 1:
            cur = {**cur, "end": s["end"],
                   "surface": cur["surface"] + s["surface"],
                   "score": min(cur["score"], s["score"])}
        else:
            if cur: merged.append(cur)
            cur = dict(s)
    if cur: merged.append(cur)
    return merged

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-chars", type=int, default=4)
    a = ap.parse_args()
    preds = json.load(open(a.pred, encoding="utf-8"))
    texts = load_texts(a.texts)
    n_raw = n_kept = 0
    for block in preds:
        t = text_for(block["text_id"], texts)
        merged = merge_adjacent(block["predictions"])
        kept = [s for s in merged if not is_fragment(s, t, a.min_chars)]
        n_raw += len(block["predictions"]); n_kept += len(kept)
        block["predictions"] = kept
    json.dump(preds, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"raw spans: {n_raw}  ->  kept after post-processing: {n_kept}")
    print(f"written: {a.out}")

if __name__ == "__main__":
    main()
