#!/usr/bin/env python3
"""Prepare the revised hard-record gold for the supplied helper scripts."""

import json
from collections import defaultdict


def main():
    with open("new_records_gold_DAMJAN_format.json", encoding="utf-8") as fh:
        source = json.load(fh)

    doc_by_id = {doc["doc_id"]: doc for doc in source["documents"]}
    grouped = defaultdict(list)
    for person in source["persons"]:
        grouped[person["doc_id"]].append(person)

    output = {}
    for doc_id, doc in doc_by_id.items():
        rec = str(doc["recognitio_number"])
        persons = []
        for person in grouped[doc_id]:
            given = person["name"]["given_name"]
            persons.append({
                "surface": given["surface"],
                "normalized": given["normalized"],
                "role": person["role"]["function"],
            })
        output[rec] = {
            "doc_id": doc_id,
            "doc_type": doc["doc_type"],
            "persons": persons,
            "n_persons": len(persons),
        }

    if sum(v["n_persons"] for v in output.values()) != 53:
        raise ValueError("Expected exactly 53 revised gold persons")

    with open("new_records_gold_tools.json", "w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
    print("written: new_records_gold_tools.json (4 records, 53 persons)")


if __name__ == "__main__":
    main()
