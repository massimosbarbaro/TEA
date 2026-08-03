#!/usr/bin/env python3
"""
step1_roberta_inference.py

Runs magistermilitum/roberta-multilingual-medieval-ner on the TEA test set.
No fine-tuning — this is the baseline test.

Requirements:
    pip install transformers torch

Usage:
    python step1_roberta_inference.py

Input:  test_set_texts.jsonl  (provided in this package)
Output: roberta_baseline_predictions.json
"""

import json
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

MODEL_NAME = "magistermilitum/roberta-multilingual-medieval-ner"
INPUT_FILE = "test_set_texts.jsonl"
OUTPUT_FILE = "roberta_baseline_predictions.json"


def merge_entities(entities):
    """Merge adjacent sub-word tokens into full entity spans."""
    if not entities:
        return []
    
    merged = []
    current = None
    
    for ent in entities:
        if ent["entity"].startswith("B-") or current is None:
            if current is not None:
                merged.append(current)
            current = {
                "surface": ent["word"],
                "label": ent["entity"].replace("B-", "").replace("I-", ""),
                "start": ent["start"],
                "end": ent["end"],
                "score": ent["score"]
            }
        elif ent["entity"].startswith("I-") and current is not None:
            # Continue current entity
            current["surface"] += ent["word"].replace("▁", " ").replace("##", "")
            current["end"] = ent["end"]
            current["score"] = min(current["score"], ent["score"])
        else:
            if current is not None:
                merged.append(current)
            current = None
    
    if current is not None:
        merged.append(current)
    
    return merged


def clean_surface(surface, source_text, start, end):
    """Use the original text to get the exact surface form."""
    if start is not None and end is not None and end <= len(source_text):
        return source_text[start:end]
    return surface


def main():
    print(f"Loading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    
    # Use pipeline for simplicity
    ner_pipe = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="none",  # we merge manually for control
        device=0 if torch.cuda.is_available() else -1
    )
    
    device_name = "GPU" if torch.cuda.is_available() else "CPU"
    print(f"Running on: {device_name}")
    
    # Load test set
    records = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    
    print(f"Loaded {len(records)} recognitiones from {INPUT_FILE}")
    
    results = []
    total_predictions = 0
    
    for i, rec in enumerate(records):
        text_id = rec["text_id"]
        text = rec["text"]
        
        # Run NER
        try:
            raw_entities = ner_pipe(text)
        except Exception as e:
            print(f"  ERROR on {text_id}: {e}")
            results.append({"text_id": text_id, "predictions": [], "error": str(e)})
            continue
        
        # Filter to PER entities only and merge sub-tokens
        per_entities = [e for e in raw_entities 
                        if "PER" in e.get("entity", "")]
        merged = merge_entities(per_entities)
        
        # Clean surface forms using original text
        for ent in merged:
            ent["surface"] = clean_surface(
                ent["surface"], text, ent["start"], ent["end"])
        
        # Filter low-confidence (keep > 0.3)
        merged = [e for e in merged if e["score"] > 0.3]
        
        results.append({
            "text_id": text_id,
            "predictions": merged
        })
        
        total_predictions += len(merged)
        print(f"  [{i+1}/{len(records)}] {text_id}: {len(merged)} PER entities found")
    
    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone. {total_predictions} total predictions saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
