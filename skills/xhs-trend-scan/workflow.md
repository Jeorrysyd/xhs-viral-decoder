# xhs-trend-scan · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--keywords` | comma-sep | `config.defaults.keywords` | 3-5 keywords recommended |
| `--window-days` | int | `14` | Time window for "recent" |
| `--top-n` | int | `10` | Output TOP N emerging concepts |
| `--reuse-pulse-data` | path | auto-detect latest viral-pulse | If provided, skip API calls and reuse |
| `--output` | path | `output/<date>/trend-scan/` | Local artifacts |

## Step-by-step

### Step 1: Load or fetch data

If `--reuse-pulse-data` (or auto-detect finds recent viral-pulse output): use that directly.
Otherwise: run keyword searches + fetch detail (same as viral-pulse step 2).

### Step 2: Extract n-grams

```python
from shared.lib.trend import extract_ngrams
all_text = "\n".join(
    n["title"] + " " + (n.get("content_excerpt", ""))[:300]
    for n in notes
)
ngrams = extract_ngrams(
    text=all_text,
    min_len=2, max_len=4,
    chinese_only=True
)
# Returns: [(word, freq, source_note_ids), ...]
```

### Step 3: Filter against common lexicon

```python
from shared.lib.trend import load_common_lexicon
common = load_common_lexicon("shared/data/common_lexicon.txt")
candidates = [
    (w, f, src) for w, f, src in ngrams
    if w not in common
    and not is_likely_brand(w)  # filter @-mentions, brand names
    and not is_user_handle(w)
]
```

### Step 4: Score candidates

```python
from shared.lib.trend import score_emerging
scored = []
for word, freq, source_note_ids in candidates:
    source_notes = [n for n in notes if n["feed_id"] in source_note_ids]

    # Recency: how concentrated in last `window_days`
    publish_dates = [n["publish_ts"] for n in source_notes]
    recency_score = compute_time_concentration(publish_dates, window_days)

    # Viral signal: appears in TOP 30 viral notes
    in_viral = sum(1 for n in source_notes if n["likes"] >= 1000)
    viral_score = math.log(in_viral + 1) * 3

    # Cross-keyword: appears in notes from multiple keyword searches
    keywords_hit = set()
    for n in source_notes:
        keywords_hit.update(n.get("keywords_matched", []))
    cross_score = len(keywords_hit) * 2

    total = recency_score * 2 + viral_score + cross_score
    scored.append((word, total, freq, source_note_ids))

scored.sort(key=lambda x: -x[1])
top_n = scored[:top_n_param]
```

### Step 5: Render report (`shared/lib/report.py::render_trend_scan`)

Template `trend_scan_template.md`:
1. TOP N table
2. Per-concept context (3 source notes per concept showing usage)
3. Trend trajectory (text-based; chart optional in later versions)
4. Action 推荐 (3 most worth adopting next week, with reasoning)

### Step 6: Push to Feishu

```python
adapter.push_doc(
    title=f"[趋势] {niche}_新概念词_{date}",
    md=report_md,
    folder_token=config.feishu.folder_token
)
```

## Failure modes

| Symptom | Action |
|---|---|
| Too few notes (< 30) | Suggest more keywords + larger window |
| All TOP candidates are common words | Common lexicon may need updating; report still generates with warning |
| No clear trend (flat scores) | Report says "no strong emerging concepts this batch" — useful negative finding |
| Brand/handle pollution | Improve `is_likely_brand` heuristic (currently regex on all-caps + @-prefix) |

## Tunable parameters

In `shared/lib/trend.py`:
- `MIN_FREQ` — minimum freq to be a candidate (default 3)
- `WINDOW_DAYS` — recency window (default 14, configurable per call)
- Scoring weights (recency × viral × cross)
- `is_likely_brand` regex
- Common lexicon path

## Common lexicon

Building the baseline (`shared/data/common_lexicon.txt`):
- Source: combine THUOCL list + Baidu top 5000 + xhs hot-topic alumni from past pulses
- Format: one word per line, UTF-8
- Update cadence: quarterly (manual)
- Initial v0.1 ships ~5000 words; users can extend per local file

## Why this matters

The reference video creator pointed out 「奥德赛时期」 as an example: a Western psychology concept that quietly appeared in Chinese xhs feeds 2 weeks before becoming a mainstream meme. Catching such words early lets creators ride the trend at low competition. This skill operationalizes that detection.
