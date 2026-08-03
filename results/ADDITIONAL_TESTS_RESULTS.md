# JT-DH revision — additional test results

Run date: 2026-07-22

All person methods were scored with the supplied original `step2_evaluate.py`
matching logic. A control rescore exactly reproduced RoBERTa's published
53-record results (73.1% overall recall; 36.0% rector-tenant recall).

Qwen used `qwen3.5:9b-q4_K_M` through Ollama on the NVIDIA RTX 2000 Ada GPU,
with the supplied extraction prompt, temperature 0, seed 42, thinking disabled,
and an 8192-token context. All 57 raw responses parsed successfully.

## Tests 1, 3, and 5 — 53-record person extraction

| Method | Precision | Recall | F1 | Rector-tenant recall |
|---|---:|---:|---:|---:|
| RoBERTa raw | 24.5% | 73.1% | 36.7% | 27/75 = 36.0% |
| RoBERTa filtered | 48.1% | 47.2% | 47.6% | 17/75 = 22.7% |
| Rules only | 58.2% | 30.2% | 39.8% | 44/75 = 58.7% |
| Qwen3.5-9B Q4_K_M | 57.0% | 84.9% | 68.2% | 59/75 = 78.7% |

Qwen gives the best overall F1 and recall, including rector recall. The
rules-only method has the expected inverted profile: rector recall is much
higher than RoBERTa's, while feudatory recall is only 13/71 = 18.3% versus
68/71 = 95.8% for raw RoBERTa.

Post-processing raises RoBERTa precision from 24.5% to 48.1% and F1 from
36.7% to 47.6%, but lowers overall recall from 73.1% to 47.2% and rector recall
from 36.0% to 22.7%. It therefore does not rescue the rector failure.

## Test 2 — four hard records

The hard-record gold is rector-only, so recall is the substantive metric;
precision and F1 should not be interpreted.

| Record | Gold | RoBERTa raw | RoBERTa filtered | Qwen3.5 |
|---:|---:|---:|---:|---:|
| 1277 | 28 | 7/28 = 25.0% | 5/28 = 17.9% | 26/28 = 92.9% |
| 443 | 15 | 11/15 = 73.3% | 3/15 = 20.0% | 15/15 = 100.0% |
| 97 | 3 | 3/3 = 100.0% | 2/3 = 66.7% | 3/3 = 100.0% |
| 101 | 7 | 4/7 = 57.1% | 1/7 = 14.3% | 6/7 = 85.7% |
| **Overall** | **53** | **25/53 = 47.2%** | **11/53 = 20.8%** | **50/53 = 94.3%** |

Qwen recovers 26 of 28 rectors in record 1277, compared with seven for raw
RoBERTa. Its three hard-set misses are duplicate-name instances: Leonardum and
Iohannem in record 1277, and Iohannem in record 101.

## Test 4 — record-level bootstrap confidence intervals

RoBERTa raw, 2,000 bootstrap resamples, seed 42:

| Metric | Point | 95% CI |
|---|---:|---:|
| Precision | 0.245 | [0.209, 0.284] |
| Recall | 0.731 | [0.551, 0.932] |
| F1 | 0.367 | [0.334, 0.399] |

## Test 6 — kinship relation extraction

Qwen predicted 93 relations against 50 gold relations:

- type + subject recall: 25/50 = 50.0%
- type + subject + status recall: 23/50 = 46.0%
- deceased-status recall: 18/28 = 64.3%

## Tests not runnable from the supplied materials

- Test 7 requires Massimo's Claude output from before manual review.
- Test 8 requires annotated TEA training records outside the 53-record test set.
- Test 9 requires a newly annotated sample of rotuli investitures.
