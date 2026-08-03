#!/usr/bin/env python3
"""
step2_evaluate.py

Compares RoBERTa predictions against the gold standard.
Computes precision, recall, F1 overall and by person category.

Usage:
    python step2_evaluate.py
    
Reads:  roberta_baseline_predictions.json + gold_standard.json
Writes: roberta_baseline_evaluation.json
"""

import argparse
import json
from collections import defaultdict, Counter


def find_in_text(name, text):
    """Check if a name (or close variant) appears in the text."""
    text_lower = text.lower()
    name_lower = name.lower()
    return name_lower in text_lower


def match_prediction_to_gold(pred_surface, gold_persons, text):
    """Try to match a RoBERTa prediction to a gold person."""
    pred_clean = pred_surface.strip().lower()
    
    for i, gp in enumerate(gold_persons):
        g_surface = gp['surface'].strip().lower()
        g_normalized = gp['normalized'].strip().lower()
        
        # Exact match on surface or normalized
        if pred_clean == g_surface or pred_clean == g_normalized:
            return i
        
        # Containment (pred inside gold or gold inside pred)
        if len(pred_clean) > 2 and len(g_surface) > 2:
            if pred_clean in g_surface or g_surface in pred_clean:
                return i
            if pred_clean in g_normalized or g_normalized in pred_clean:
                return i
    
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gold', required=True)
    ap.add_argument('--pred', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    with open(args.gold, 'r', encoding='utf-8') as f:
        gold = json.load(f)
    
    with open(args.pred, 'r', encoding='utf-8') as f:
        preds = json.load(f)
    
    pred_by_id = {r['text_id']: r for r in preds}
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    category_total = Counter()
    category_found = Counter()
    
    per_rec = []
    fn_examples = []
    fp_examples = []
    
    for gold_rec in gold['records']:
        tid = gold_rec['text_id']
        text = gold_rec['text']
        gold_persons = gold_rec['gold_persons']
        pred_rec = pred_by_id.get(tid, {})
        pred_ents = pred_rec.get('predictions', [])
        
        matched_gold = set()
        matched_pred = set()
        
        for pi, pred in enumerate(pred_ents):
            pred_surface = pred.get('surface', '')
            match_idx = match_prediction_to_gold(pred_surface, gold_persons, text)
            if match_idx is not None and match_idx not in matched_gold:
                matched_gold.add(match_idx)
                matched_pred.add(pi)
        
        tp = len(matched_gold)
        fp = len(pred_ents) - len(matched_pred)
        fn = len(gold_persons) - len(matched_gold)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        
        per_rec.append({
            'text_id': tid,
            'gold_count': len(gold_persons),
            'predicted_count': len(pred_ents),
            'tp': tp, 'fp': fp, 'fn': fn,
            'precision': round(p, 3), 'recall': round(r, 3), 'f1': round(f1, 3)
        })
        
        # Per-category
        for gi, gp in enumerate(gold_persons):
            cat = gp['category']
            category_total[cat] += 1
            if gi in matched_gold:
                category_found[cat] += 1
        
        # Error examples
        if len(fn_examples) < 30:
            for gi, gp in enumerate(gold_persons):
                if gi not in matched_gold:
                    fn_examples.append({
                        'text_id': tid,
                        'missed': gp['surface'],
                        'normalized': gp['normalized'],
                        'category': gp['category']
                    })
        
        if len(fp_examples) < 20:
            for pi, pred in enumerate(pred_ents):
                if pi not in matched_pred:
                    fp_examples.append({
                        'text_id': tid,
                        'spurious': pred.get('surface', ''),
                        'score': pred.get('score', 0)
                    })
    
    # Overall
    P = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    R = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    F1 = 2 * P * R / (P + R) if (P + R) > 0 else 0
    
    result = {
        'overall': {
            'precision': round(P, 4), 'recall': round(R, 4), 'f1': round(F1, 4),
            'tp': total_tp, 'fp': total_fp, 'fn': total_fn,
            'gold_total': sum(r['gold_count'] for r in per_rec),
            'predicted_total': sum(r['predicted_count'] for r in per_rec)
        },
        'by_category': {
            cat: {
                'total': category_total[cat],
                'found': category_found[cat],
                'recall': round(category_found[cat] / category_total[cat], 4) if category_total[cat] > 0 else 0
            }
            for cat in sorted(category_total.keys())
        },
        'by_recognitio': sorted(per_rec, key=lambda x: x['text_id']),
        'false_negatives': fn_examples,
        'false_positives': fp_examples
    }
    
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print('=' * 60)
    print('EVALUATION RESULTS')
    print('=' * 60)
    print(f'Gold persons:      {result["overall"]["gold_total"]}')
    print(f'RoBERTa found:     {result["overall"]["predicted_total"]}')
    print(f'True positives:    {total_tp}')
    print(f'False positives:   {total_fp}')
    print(f'False negatives:   {total_fn}')
    print(f'Precision:         {P:.1%}')
    print(f'Recall:            {R:.1%}')
    print(f'F1:                {F1:.1%}')
    print()
    print('Recall by category:')
    for cat in sorted(category_total.keys()):
        t = category_total[cat]
        f = category_found[cat]
        print(f'  {cat:20s}  {f:3d}/{t:3d}  = {f/t:.1%}' if t > 0 else f'  {cat:20s}  0/0')
    print()
    print(f'Saved to {args.out}')


if __name__ == '__main__':
    main()
