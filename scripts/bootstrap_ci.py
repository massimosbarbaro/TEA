#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST 4 - Bootstrap confidence intervals.
Reads a per-record evaluation with tp/fp/fn per record (the "by_recognitio"
array your step2_evaluate.py already produces) and computes 95% bootstrap
confidence intervals for overall precision, recall, and F1 by resampling
records with replacement.

Usage:
  python bootstrap_ci.py --eval roberta_53_evaluation.json --n 2000
"""
import argparse, json, random

def prf(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 0.0
    r = tp/(tp+fn) if tp+fn else 0.0
    f = 2*p*r/(p+r) if p+r else 0.0
    return p, r, f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    ev = json.load(open(a.eval, encoding="utf-8"))
    recs = ev["by_recognitio"]
    counts = [(r.get("tp",0), r.get("fp",0), r.get("fn",0)) for r in recs]
    random.seed(a.seed)
    P, R, F = [], [], []
    k = len(counts)
    for _ in range(a.n):
        sample = [counts[random.randrange(k)] for _ in range(k)]
        tp = sum(c[0] for c in sample); fp = sum(c[1] for c in sample); fn = sum(c[2] for c in sample)
        p, r, f = prf(tp, fp, fn)
        P.append(p); R.append(r); F.append(f)
    def ci(v):
        v = sorted(v); lo = v[int(0.025*len(v))]; hi = v[int(0.975*len(v))]
        return lo, hi
    tp = sum(c[0] for c in counts); fp = sum(c[1] for c in counts); fn = sum(c[2] for c in counts)
    p, r, f = prf(tp, fp, fn)
    for name, point, dist in (("precision",p,P),("recall",r,R),("f1",f,F)):
        lo, hi = ci(dist)
        print(f"{name:10} {point:.3f}  95% CI [{lo:.3f}, {hi:.3f}]")

if __name__ == "__main__":
    main()
