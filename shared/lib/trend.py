"""Emerging concept word detection.

Algorithm:
1. Extract 2-4 char Chinese n-grams from titles + content_excerpts of recent notes
2. Filter against a 5000-word common Chinese lexicon baseline
3. Score by: log(viral_appearances) × 3 + recency_concentration × 2 + cross_keyword × 2
4. Penalize brand/handle pollution
5. Return TOP N by score, with source notes for context
"""
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


# ---------- N-gram extraction ----------
def extract_ngrams(text: str, min_len: int = 2, max_len: int = 4) -> list:
    """Extract all Chinese n-grams of length [min_len, max_len].

    Returns list of n-gram strings (with duplicates — caller dedupes via Counter).
    """
    # Strip punctuation / English / numbers, keep Chinese only
    chinese_only = re.findall(r"[一-鿿]+", text)
    out = []
    for run in chinese_only:
        for n in range(min_len, max_len + 1):
            for i in range(len(run) - n + 1):
                out.append(run[i : i + n])
    return out


def load_common_lexicon(path: str) -> set:
    """Load common-word baseline from text file (one word per line)."""
    p = Path(path)
    if not p.exists():
        return set()
    return {
        line.strip() for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


# ---------- Brand / handle detection ----------
def is_likely_brand_or_handle(word: str) -> bool:
    """Heuristic to filter out brand names, user handles."""
    # All-uppercase English embedded → brand
    if re.search(r"[A-Z]{2,}", word):
        return True
    # @-prefix or starting with common handle markers
    if word.startswith("@") or word.startswith("#"):
        return True
    return False


# ---------- Scoring ----------
def compute_recency_concentration(
    publish_dates: list,
    window_days: int = 14,
    now: Optional[datetime] = None,
) -> float:
    """Returns 0-1 score: higher means most appearances are within window."""
    if not publish_dates:
        return 0.0
    now = now or datetime.now(timezone(timedelta(hours=8)))
    cutoff = now - timedelta(days=window_days)
    recent = sum(1 for d in publish_dates if d and d >= cutoff)
    return recent / len(publish_dates)


def score_emerging(
    word: str,
    appearances: list,  # list of dicts: {note_id, likes, publish_ts, keywords_matched}
    window_days: int = 14,
) -> dict:
    """Compute emerging score for a word given its source appearances."""
    freq = len(appearances)

    # Viral signal
    in_viral = sum(1 for a in appearances if a.get("likes", 0) >= 1000)
    viral_score = math.log(in_viral + 1) * 3

    # Recency
    publish_dates = []
    for a in appearances:
        ts = a.get("publish_ts")
        if ts:
            publish_dates.append(datetime.fromtimestamp(ts / 1000, tz=timezone(timedelta(hours=8))))
    recency_score = compute_recency_concentration(publish_dates, window_days)

    # Cross-keyword
    keywords_hit = set()
    for a in appearances:
        keywords_hit.update(a.get("keywords_matched", []))
    cross_score = len(keywords_hit) * 2

    total = recency_score * 2 + viral_score + cross_score

    return {
        "word": word,
        "freq": freq,
        "in_viral": in_viral,
        "recency": recency_score,
        "cross_keywords": len(keywords_hit),
        "score": total,
        "first_appearance": (
            min(publish_dates).strftime("%Y-%m-%d") if publish_dates else "未知"
        ),
        "source_notes": [
            {"feed_id": a.get("note_id"), "title": a.get("title", ""), "url": a.get("url", ""), "likes": a.get("likes", 0)}
            for a in sorted(appearances, key=lambda x: -x.get("likes", 0))[:5]
        ],
    }


# ---------- Main ----------
def detect_emerging_concepts(
    notes: list,
    common_lexicon_path: str = None,
    window_days: int = 14,
    top_n: int = 10,
    min_freq: int = 3,
) -> dict:
    """Detect emerging concept words from a list of recent xhs notes.

    Each note dict needs: feed_id, title, content_excerpt (optional),
    likes, publish_ts (ms), keywords_matched (optional list), url

    Returns: {top_concepts: [...], source_notes_count: N, recommended: [...]}
    """
    common = load_common_lexicon(common_lexicon_path) if common_lexicon_path else set()

    # Map word → list of appearance records
    word_appearances = defaultdict(list)

    for n in notes:
        text = (n.get("title", "") or "") + " " + (n.get("content_excerpt", "") or "")[:300]
        seen_in_note = set()
        for w in extract_ngrams(text):
            if w in seen_in_note:
                continue  # only count once per note
            seen_in_note.add(w)
            word_appearances[w].append({
                "note_id": n.get("feed_id"),
                "title": n.get("title", ""),
                "url": n.get("url", ""),
                "likes": int(n.get("likes") or 0),
                "publish_ts": n.get("publish_ts"),
                "keywords_matched": n.get("keywords_matched", []),
            })

    # Filter
    candidates = []
    for word, appearances in word_appearances.items():
        if len(appearances) < min_freq:
            continue
        if word in common:
            continue
        if is_likely_brand_or_handle(word):
            continue
        candidates.append(score_emerging(word, appearances, window_days))

    # Sort + take TOP N
    candidates.sort(key=lambda x: -x["score"])
    top_concepts = candidates[:top_n]

    # Recommended: top 3 with score > threshold AND recency > 0.5 (concentrated recent)
    recommended = []
    for c in top_concepts[:3]:
        if c["score"] > 5 and c["recency"] > 0.5:
            c["reason"] = (
                f"{c['freq']} 次出现，{c['in_viral']} 次出现在爆款里，"
                f"{int(c['recency']*100)}% 的提及集中在近 {window_days} 天 — 时间窗口正好"
            )
            recommended.append(c)

    return {
        "top_concepts": top_concepts,
        "source_notes_count": len(notes),
        "window_days": window_days,
        "recommended": recommended,
    }
