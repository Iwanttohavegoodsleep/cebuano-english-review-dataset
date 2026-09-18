"""Run basic privacy and integrity checks on the public annotation CSV."""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).parents[1] / "data" / "jose-annotations.csv"
EXPECTED_COLUMNS = {
    "candidate_id", "review_text", "source_tier", "label", "annotation_number"
}
ALLOWED_LABELS = {"complaint", "not_complaint", "not_cebuano_english"}
PRIVATE_COLUMNS = {
    "reviewerId", "StoreId", "uuid", "annotator_id", "updated_at", "created_at"
}


def main() -> None:
    frame = pd.read_csv(DATA)
    assert set(frame.columns) == EXPECTED_COLUMNS, "Unexpected public columns"
    assert not (set(frame.columns) & PRIVATE_COLUMNS), "Private metadata found"
    assert len(frame) == 3566, "Unexpected row count"
    assert frame["candidate_id"].is_unique, "Duplicate candidate IDs"
    assert not frame["review_text"].isna().any(), "Blank review text"
    assert set(frame["label"]) <= ALLOWED_LABELS, "Unknown label"
    assert sorted(frame["annotation_number"]) == list(range(1, 3567)), "Annotation order is incomplete"
    print("Validated 3,566 privacy-minimized annotation rows.")


if __name__ == "__main__":
    main()
