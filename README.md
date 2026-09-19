# Cebuano-English Food Review Annotations

A research dataset of 3,566 Foodpanda reviews selected as likely Cebuano-English code-switched text and labeled by one primary annotator.

This is a **working annotation release**, not the final thesis corpus. A second independent annotation and disagreement resolution are still required before the labels should be treated as final.

## What's here

- `data/jose-annotations.csv` — review text and one annotator's labels
- `filtering/filter_reviews.py` — the candidate selection pipeline
- `filtering/markers.py` — Cebuano, English, and Tagalog marker lists
- `scripts/validate_release.py` — checks the public CSV before release

The public file intentionally excludes reviewer IDs, store IDs, ratings, account IDs, timestamps, and the other annotator's work.

## Dataset summary

| Label | Rows |
|---|---:|
| Complaint | 2,323 |
| Not complaint | 1,240 |
| Not Cebuano-English | 3 |
| **Total** | **3,566** |

Each row contains:

| Column | Meaning |
|---|---|
| `candidate_id` | Stable anonymous review ID |
| `review_text` | Original review text |
| `source_tier` | Candidate-selection tier |
| `label` | This annotator's decision |
| `annotation_number` | Order in which the annotation was completed |

## How the reviews were selected

The source contained 212,005 Philippine Foodpanda reviews. The script reduced it to an annotation queue in two passes:

1. Normalize text for matching while preserving the original review.
2. Look for explicit Cebuano and English words or phrases.
3. Keep likely mixed-language reviews and flag possible Tagalog overlap for review.
4. Remove exact duplicate text using a SHA-256 hash of the normalized review.
5. Keep the strongest Tier A candidates: at least two independent core Cebuano signals and no narrow Tagalog-exclusive signal.

The filter only retrieves candidates. A human makes the language and complaint decisions.

## Run the filter

```bash
python -m pip install -r filtering/requirements.txt
python filtering/filter_reviews.py --input ph_reviews_2025.csv --output-dir output
```

Validate the included release with:

```bash
python scripts/validate_release.py
```

## Source and license

The review text is derived from **Philippine Cities Food Panda Resto Reviews** by [BwandoWando on Kaggle](https://www.kaggle.com/datasets/bwandowando/philippine-cities-food-panda-resto-reviews), which declares a [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) license.

The dataset in `data/` follows the same CC BY-NC-SA 4.0 terms. The filtering code is available under the MIT License. See [DATA_LICENSE.md](DATA_LICENSE.md) and [LICENSE](LICENSE).
