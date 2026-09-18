"""Build the high-confidence Cebuano-English review queue.

The rules are intentionally explicit: find language markers, keep mixed-language
candidates, remove exact duplicate text, then retain the strongest Cebuano
evidence for human annotation. The script retrieves candidates; it does not
decide the final language or complaint label.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from markers import (
    CEBUANO_DECISIVE_PHRASES,
    CEBUANO_DECISIVE_WORDS,
    CEBUANO_SUPPORTING_WORDS,
    COLLISION_MARKERS,
    ENGLISH_MARKERS,
    TAGALOG_DECISIVE_PHRASES,
    TAGALOG_DECISIVE_WORDS,
    TAGALOG_EXCLUSIVE,
    TOKEN_RE,
    WEAK_ENGLISH_MARKERS,
)

SUPPORTING_MARKERS_REQUIRED = 2

GENERATED_COLUMNS = {
    "candidate_id", "candidate_priority", "candidate_queue",
    "candidate_decision_reason", "tiered_filter_label",
    "tiered_decision_reason", "normalized_text_sha256",
    "exact_duplicate_count", "ceb_decisive_word_count",
    "ceb_decisive_phrase_count", "ceb_supporting_count",
    "tl_decisive_word_count", "tl_decisive_phrase_count", "en_marker_count",
    "en_strong_marker_count", "en_weak_marker_count",
    "ceb_decisive_word_hits", "ceb_decisive_phrase_hits",
    "ceb_supporting_hits", "tl_decisive_word_hits",
    "tl_decisive_phrase_hits", "en_marker_hits", "en_strong_marker_hits",
    "en_weak_marker_hits", "confidence_tier", "confidence_reason",
    "core_ceb_evidence_count", "core_ceb_evidence_hits",
    "demoted_marker_hits", "tagalog_exclusive_hits",
}


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", "" if value is None else str(value)).lower()
    for old, new in (("â€™", "'"), ("â€˜", "'"), ("’", "'"), ("‘", "'"), ("`", "'"), ("\u200b", ""), ("\ufeff", "")):
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def find_phrases(text: str, phrases: set[str]) -> list[str]:
    return sorted(
        phrase for phrase in phrases
        if re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text)
    )


def analyze_language(value: object) -> dict[str, object]:
    text = normalize(value)
    tokens = set(TOKEN_RE.findall(text))

    ceb_words = sorted(tokens & CEBUANO_DECISIVE_WORDS)
    ceb_phrases = find_phrases(text, CEBUANO_DECISIVE_PHRASES)
    ceb_support = sorted(tokens & CEBUANO_SUPPORTING_WORDS)
    tl_words = sorted(tokens & TAGALOG_DECISIVE_WORDS)
    tl_phrases = find_phrases(text, TAGALOG_DECISIVE_PHRASES)
    en_hits = sorted(tokens & ENGLISH_MARKERS)
    en_weak = sorted(set(en_hits) & WEAK_ENGLISH_MARKERS)
    en_strong = sorted(set(en_hits) - WEAK_ENGLISH_MARKERS)

    decisive_ceb = bool(ceb_words or ceb_phrases)
    any_ceb = decisive_ceb or bool(ceb_support)
    qualified_ceb = decisive_ceb or len(ceb_support) >= SUPPORTING_MARKERS_REQUIRED
    has_tagalog = bool(tl_words or tl_phrases)

    if decisive_ceb and en_strong and not has_tagalog:
        priority, queue, label = 1, "HIGH_PRIORITY", "CEB_EN_STRONG_EVIDENCE"
        reason = "Strong Cebuano and English evidence were found."
    elif qualified_ceb and en_hits and has_tagalog:
        priority, queue, label = 2, "REVIEW_PRIORITY", "CEB_EN_WITH_TAGALOG_OVERLAP"
        reason = "Cebuano and English evidence were found with possible Tagalog overlap."
    elif qualified_ceb and en_hits:
        priority, queue, label = 2, "REVIEW_PRIORITY", "CEB_EN_WEAK_ENGLISH_EVIDENCE"
        reason = "Cebuano evidence was found, but the English evidence is weak."
    elif any_ceb and en_hits:
        priority, queue, label = 3, "LANGUAGE_AUDIT", "CEB_EN_WEAK_CEBUANO_EVIDENCE"
        reason = "English and some Cebuano evidence were found; Cebuano evidence needs review."
    elif any_ceb:
        priority, queue, label = 3, "LANGUAGE_AUDIT", "CEBUANO_WITHOUT_RECOGNIZED_ENGLISH"
        reason = "Cebuano evidence was found without a recognized English marker."
    elif has_tagalog and en_hits:
        priority, queue, label = 0, "NOT_CANDIDATE", "TAGALOG_EN"
        reason = "English and Tagalog evidence were found without Cebuano evidence."
    elif en_hits:
        priority, queue, label = 0, "NOT_CANDIDATE", "ENGLISH_OR_UNKNOWN"
        reason = "English evidence was found without Cebuano evidence."
    else:
        priority, queue, label = 0, "NOT_CANDIDATE", "NO_CEBUANO_ENGLISH_EVIDENCE"
        reason = "No usable Cebuano-English evidence combination was found."

    return {
        "candidate_priority": priority,
        "candidate_queue": queue,
        "candidate_decision_reason": reason,
        "tiered_filter_label": label,
        "tiered_decision_reason": reason,
        "ceb_decisive_word_count": len(ceb_words),
        "ceb_decisive_phrase_count": len(ceb_phrases),
        "ceb_supporting_count": len(ceb_support),
        "tl_decisive_word_count": len(tl_words),
        "tl_decisive_phrase_count": len(tl_phrases),
        "en_marker_count": len(en_hits),
        "en_strong_marker_count": len(en_strong),
        "en_weak_marker_count": len(en_weak),
        "ceb_decisive_word_hits": "|".join(ceb_words),
        "ceb_decisive_phrase_hits": "|".join(ceb_phrases),
        "ceb_supporting_hits": "|".join(ceb_support),
        "tl_decisive_word_hits": "|".join(tl_words),
        "tl_decisive_phrase_hits": "|".join(tl_phrases),
        "en_marker_hits": "|".join(en_hits[:20]),
        "en_strong_marker_hits": "|".join(en_strong[:20]),
        "en_weak_marker_hits": "|".join(en_weak),
    }


def add_confidence_tier(row: pd.Series) -> pd.Series:
    tokens = set(TOKEN_RE.findall(normalize(row["text"])))
    tagalog = sorted(tokens & TAGALOG_EXCLUSIVE)
    decisive = set(str(row.get("ceb_decisive_word_hits", "")).split("|")) - {"", "nan"}
    phrases = set(str(row.get("ceb_decisive_phrase_hits", "")).split("|")) - {"", "nan"}
    core = decisive - COLLISION_MARKERS
    demoted = sorted(decisive & COLLISION_MARKERS)
    evidence_count = len(core) + len(phrases)

    if tagalog:
        tier = "TIER_C_RECHECK"
        reason = "A Tagalog-exclusive token is present: " + ", ".join(tagalog) + "."
    elif evidence_count >= 2:
        tier = "TIER_A_CONFIDENT"
        reason = f"{evidence_count} independent core Cebuano markers, no Tagalog-exclusive token."
    elif evidence_count == 1:
        tier = "TIER_B_LIKELY"
        reason = "One core Cebuano marker, no Tagalog-exclusive token."
    else:
        tier = "TIER_C_RECHECK"
        reason = "Qualified only through a collision-prone marker: " + ", ".join(demoted) + "."

    return pd.Series({
        "confidence_tier": tier,
        "confidence_reason": reason,
        "core_ceb_evidence_count": evidence_count,
        "core_ceb_evidence_hits": "|".join(sorted(core | phrases)),
        "demoted_marker_hits": "|".join(demoted),
        "tagalog_exclusive_hits": "|".join(tagalog),
    })


def build_tier_a(input_path: Path, text_column: str) -> tuple[pd.DataFrame, dict[str, int]]:
    raw = pd.read_csv(input_path, low_memory=False)
    if text_column not in raw.columns:
        raise ValueError(f"Missing text column {text_column!r}.")

    if "source_row_index" in raw:
        source_index = pd.to_numeric(raw["source_row_index"], errors="coerce")
        source_index = source_index.fillna(pd.Series(range(len(raw)), index=raw.index)).astype(int)
    else:
        source_index = pd.Series(range(len(raw)), dtype=int)

    payload = raw.drop(columns=["source_row_index", *sorted(GENERATED_COLUMNS)], errors="ignore")
    analysis = pd.DataFrame(analyze_language(value) for value in payload[text_column])
    result = pd.concat([source_index.rename("source_row_index").reset_index(drop=True), payload.reset_index(drop=True), analysis], axis=1)
    result.insert(1, "candidate_id", source_index.map(lambda value: f"REV-{int(value) + 1:07d}").reset_index(drop=True))

    hashes = payload[text_column].map(normalize).map(lambda text: hashlib.sha256(text.encode()).hexdigest())
    result["normalized_text_sha256"] = hashes
    result["exact_duplicate_count"] = hashes.map(hashes.value_counts()).astype(int)

    high_priority = result[result["candidate_priority"] == 1].copy()
    high_priority.drop_duplicates("normalized_text_sha256", keep="first", inplace=True)
    high_priority.sort_values("source_row_index", inplace=True)
    tiered = high_priority.join(high_priority.apply(add_confidence_tier, axis=1))
    tier_a = tiered[tiered["confidence_tier"] == "TIER_A_CONFIDENT"].copy()
    counts = tiered["confidence_tier"].value_counts().sort_index().astype(int).to_dict()
    return tier_a, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("output"), type=Path)
    parser.add_argument("--text-column", default="text")
    args = parser.parse_args()

    tier_a, counts = build_tier_a(args.input, args.text_column)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tier_a.to_csv(args.output_dir / "tier_a_confident.csv", index=False, encoding="utf-8-sig")
    (args.output_dir / "summary.json").write_text(
        json.dumps({"tier_counts": counts, "tier_a_rows": len(tier_a)}, indent=2),
        encoding="utf-8",
    )
    print(f"Tier A candidates: {len(tier_a):,}")


if __name__ == "__main__":
    main()
