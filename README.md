# TEA — Beyond Span Detection

This repository accompanies the paper **"Beyond Span Detection: Comparing NER Approaches for Medieval Patronymics in the Thesaurus Ecclesiae Aquileiensis"**. It provides the gold standard, the extraction prompt, the evaluation scripts, and the model outputs needed to reproduce the experiments described in the article.

## Overview

Named entity recognition on medieval documents is usually framed as span detection: find where names begin and end, then classify them. This framing breaks down on dense feudal registers, where kinship, social status, and origin are encoded implicitly in formulaic structures. Using 53 acts from the Thesaurus Ecclesiae Aquileiensis (TEA), a fourteenth-century feudal register from the Patriarchate of Aquileia, we compare three approaches: a RoBERTa-based token classifier (Torres Aguilar, 2022), a locally deployed LLM (Qwen3.5-9B, Q4_K_M quantisation), and a proprietary LLM used as an annotation tool. The full pipeline runs on consumer hardware without cloud dependencies.

The gold standard contains 212 annotated persons, 50 kinship relations, and 58 places.

## Repository structure

```
gold/            gold_standard_53.json          Reviewed, span-grounded gold standard (persons, kinship relations, places)
                 gold_standard_53_eval.json     Evaluator-format gold (text fields empty) for step2_evaluate_cli.py
                 gold_hard_records.json         The four hard out-of-sample records
                 kinship_gold.json              Kinship-only gold data
prompt/          extraction_prompt.txt          System prompt with the five extraction rules and worked examples
scripts/         step1_roberta_inference.py     RoBERTa inference to generate raw predictions
                 step2_evaluate_cli.py          Evaluation CLI (predictions vs gold standard)
                 postprocess_filter.py          Post-processing filter for RoBERTa raw output
                 rules_only_predict.py          Rule-based extractor
                 bootstrap_ci.py                Bootstrap confidence intervals
                 qwen_parse.py                  Parsing of Qwen raw output
                 relations_eval.py              Evaluation of the relational (kinship) layer
                 prepare_additional_inputs.py   Preparation of the additional out-of-sample records
                 run_qwen_extraction.ps1        PowerShell script to run local Qwen extraction
predictions/     *.json                         Model predictions for each configuration
evaluations/     *.json                         Computed metrics for each configuration
results/         confidence_intervals/          Bootstrap CI outputs
                 relations/                     Relational-layer evaluation outputs
                 qwen_raw/                      Raw Qwen output before parsing
                 ADDITIONAL_TESTS_RESULTS.md    Results on the out-of-sample records
                 RUN_METADATA.json              Run metadata (models, versions, parameters)
README.md
LICENSE
CITATION.cff
```

## Source texts

The transcribed source texts of the test acts are not included in this repository because the critical edition of the TEA is still in preparation (Scarton, 2023). The source texts are available on request. The RoBERTa checkpoint is not distributed here either: the model is the public checkpoint by Torres Aguilar (magistermilitum/roberta-multilingual-medieval-ner).

## Main results

Four configurations were evaluated on the 53-record test set against the same gold standard, using containment-based matching:

| Configuration            | Precision | Recall | F1    | Rector recall |
|--------------------------|-----------|--------|-------|---------------|
| RoBERTa (raw)            | 24.5%     | 73.1%  | 36.7% | 36.0%         |
| RoBERTa + post-processing| 48.1%     | 47.2%  | 47.6% | 22.7%         |
| Rules only               | 58.2%     | 30.2%  | 39.8% | 58.7%         |
| Qwen3.5-9B               | 57.0%     | 84.9%  | 68.2% | 78.7%         |

The token classifier finds feudatories in formulaic positions (95.8% recall) but misses two-thirds of the rectors of mansi embedded in property descriptions (36.0%). The local LLM handles contextual interpretation and leads on both overall F1 and rector recall.

## Two gold formats

The gold standard is published in two serialisations of the same 212 persons, linked by a shared `person_id`.

**Ontology format**, `gold/gold_standard_53.json`. Four normalised tables (`documents`, `persons`, `kinship_relations`, `places`) with decomposed names, grammatical case, kinship components and place identifications. This is the reusable dataset: 53 documents, 212 persons, 50 kinship relations, 58 places.

**Evaluator format**, `gold/gold_standard_53_eval.json`. A flat list under `records`, one per act, each with `text_id`, `text`, `gold_count` and a `gold_persons` array whose entries carry `person_id`, `surface`, `normalized`, `role` and `category`. This is the input `scripts/step2_evaluate_cli.py` reads, and it is the format behind the per-category figures reported in the paper. The `text` field is empty in every record, because the transcriptions are covered by the forthcoming critical edition (see *Source texts*). The evaluator reads the field but does not use it for matching, so the published file reproduces the reported metrics exactly.

### Role categories

Each entry of the evaluator format carries both vocabularies: `role`, identical to `role.function` in the ontology format, and `category`, the label used in the recall analysis. Their correspondence is:

| `role`         | `category`         | Persons |
|----------------|--------------------|--------:|
| `grantor`      | `authority`        |       9 |
| `procurator`   | `procurator`       |      10 |
| `feudatory`    | `feudatory`        |      69 |
| `co-feudatory` | `feudatory`        |       2 |
| `co-feudatory` | `implicit_context` |       5 |
| `tenant`       | `rector_tenant`    |      75 |
| `tenant`       | `other`            |       1 |
| `witness`      | `other`            |      41 |
| **Total**      |                    | **212** |

The two vocabularies diverge for eight persons: the seven co-feudatories are split between `feudatory` (2) and `implicit_context` (5), and one tenant is classified as `other`. The categories were assigned for the purposes of the recall analysis, while the roles record the documentary function. Table 2 of the paper reports the `category` counts: authority 9, feudatory 71, implicit_context 5, other 42, procurator 10, rector_tenant 75.

## Reproducing the evaluation

`scripts/step2_evaluate_cli.py` reads the evaluator-format gold:

```
python scripts/step2_evaluate_cli.py --pred predictions/roberta_53_predictions.json \
                                     --gold gold/gold_standard_53_eval.json \
                                     --out my_roberta_53_evaluation.json
```

Compare the output with `evaluations/roberta_53_evaluation.json` rather than overwriting it: the two match in every field. The same command, with the corresponding file in `predictions/`, reproduces the other three 53-record evaluations (`roberta_53_FILTERED`, `rules_only_53`, `qwen_53`). The control reproduction recorded in `results/RUN_METADATA.json` is overall recall 0.7311 and rector recall 0.36 for the RoBERTa baseline.

The evaluations of the four hard out-of-sample records (`*_hard4_*`) were computed against a rector-only gold derived from `gold/gold_hard_records.json`, which is published in the ontology format only. Those figures can be inspected in `evaluations/` but cannot be re-run with this command.

See `results/RUN_METADATA.json` for the exact model versions and parameters, and `results/ADDITIONAL_TESTS_RESULTS.md` for the out-of-sample tests.

## License

This repository is released under the MIT License. See the `LICENSE` file for details.

## Citation

If you use this dataset or code, please cite the accompanying paper:

> Sbarbaro, Massimo, and Damjan Popič. "Beyond Span Detection: Comparing NER Approaches for Medieval Patronymics in the Thesaurus Ecclesiae Aquileiensis." Paper presented at the 15th Conference on Language Technologies and Digital Humanities (JT-DH-2026), Ljubljana, September 2026. https://doi.org/10.5281/zenodo.22765855.

The code and data in this repository are archived on Zenodo: [https://doi.org/10.5281/zenodo.23136784](https://doi.org/10.5281/zenodo.23136784) (all versions).

## Acknowledgements

This research was carried out at the ALDHI laboratory of ZRS Koper (Science and Research Centre Koper). The authors thank the Biblioteca del Capitolo Metropolitano di Udine for access to ms 51 (C1).
