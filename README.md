# TEA — Beyond Span Detection

This repository accompanies the paper **"Beyond Span Detection: Comparing NER Approaches for Medieval Patronymics in the Thesaurus Ecclesiae Aquileiensis"**. It provides the gold standard, the extraction prompt, the evaluation scripts, and the model outputs needed to reproduce the experiments described in the article.

## Overview

Named entity recognition on medieval documents is usually framed as span detection: find where names begin and end, then classify them. This framing breaks down on dense feudal registers, where kinship, social status, and origin are encoded implicitly in formulaic structures. Using 53 acts from the Thesaurus Ecclesiae Aquileiensis (TEA), a fourteenth-century feudal register from the Patriarchate of Aquileia, we compare three approaches: a RoBERTa-based token classifier (Torres Aguilar, 2022), a locally deployed LLM (Qwen3.5-9B, Q4_K_M quantisation), and a proprietary LLM used as an annotation tool. The full pipeline runs on consumer hardware without cloud dependencies.

The gold standard contains 212 annotated persons, 50 kinship relations, and 58 places.

## Repository structure

```
gold/            gold_standard_53.json          Reviewed, span-grounded gold standard (persons, kinship relations, places)
prompt/          extraction_prompt.txt          System prompt with the five extraction rules and worked examples
scripts/         step2_evaluate_cli.py          Evaluation CLI (predictions vs gold standard)
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
                 qwen_raw/                       Raw Qwen output before parsing
                 ADDITIONAL_TESTS_RESULTS.md     Results on the out-of-sample records
                 RUN_METADATA.json               Run metadata (models, versions, parameters)
texts/           test_53_texts.json             Source texts of the 53 test acts
README.md
LICENSE
```

## Main results

Four configurations were evaluated on the 53-record test set against the same gold standard, using containment-based matching:

| Configuration            | Precision | Recall | F1    | Rector recall |
|--------------------------|-----------|--------|-------|---------------|
| RoBERTa (raw)            | 24.5%     | 73.1%  | 36.7% | 36.0%         |
| RoBERTa + post-processing| 48.1%     | 47.2%  | 47.6% | 22.7%         |
| Rules only               | 58.2%     | 30.2%  | 39.8% | 58.7%         |
| Qwen3.5-9B               | 57.0%     | 84.9%  | 68.2% | 78.7%         |

The token classifier finds feudatories in formulaic positions (95.8% recall) but misses two-thirds of the rectors of mansi embedded in property descriptions (36.0%). The local LLM handles contextual interpretation and leads on both overall F1 and rector recall.

## Reproducing the evaluation

The evaluation scripts read a predictions JSON file and the gold standard, and write metrics to `evaluations/`. As a starting point:

```
python scripts/step2_evaluate_cli.py --pred predictions/<file>.json --gold gold/gold_standard_53.json
```

See `results/RUN_METADATA.json` for the exact model versions and parameters, and `results/ADDITIONAL_TESTS_RESULTS.md` for the out-of-sample tests.

## License

The code in this repository is released under the MIT License (see `LICENSE`). The accompanying paper and the annotated data are distributed under the Creative Commons Attribution-ShareAlike 4.0 International license (CC BY-SA 4.0).

## Citation

If you use this dataset or code, please cite the accompanying paper:

> Beyond Span Detection: Comparing NER Approaches for Medieval Patronymics in the Thesaurus Ecclesiae Aquileiensis.
>
> ## Acknowledgements
>
> This research was carried out at the ALDHI laboratory of ZRS Koper (Science and Research Centre Koper). The authors thank the Biblioteca del Capitolo Metropolitano di Udine for access to ms 51 (C1).
> 
