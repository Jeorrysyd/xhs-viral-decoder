# xhs-account-decompose · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--url` | string | — | Required. Xhs profile URL with `xsec_token` preferred |
| `--nickname` | string | — | Alternative to URL — looks up via `search_feeds` |
| `--top-detail` | int | `5` | Number of top notes to fetch full detail (subject to xhs 风控) |
| `--output` | path | `output/<date>/account-decompose/` | Local artifacts |

## Step-by-step

### Step 1: Resolve user_id + xsec_token

If `--url` has `xsec_token`: use directly.
If `--url` has only user_id (e.g., `?m_source=pwa`):
- Use `--nickname` if provided, else fail with hint.
- `search_feeds(nickname)` → find any of their notes → grab `xsecToken` from that note → use for `user_profile`.

### Step 2: Fetch profile + feed list

```python
from shared.lib.xhs import user_profile
data = user_profile(user_id, xsec_token)
# Returns: userBasicInfo, interactions [follow/fans/total_engagement], feeds (up to 32)
```

### Step 3: Fetch TOP 5 details + comments

```python
for note in top_5_by_likes:
    detail = get_feed_detail(note.feed_id, note.xsec_token)
    # Some may fail with "Sorry, This Page Isn't Available Right Now." — record and continue
```

### Step 4: Analyze (5 dimensions)

1. **Basic info**: parse `userBasicInfo` + `interactions`. Compute 爆款率 (likes ≥ 1k), 大爆率 (likes ≥ 10k).
2. **Tags extraction**:
   - bio split by `|` `/` `\n` → self-tags
   - all titles → 2-4 char Chinese n-gram frequency (TOP 15)
   - title pattern classifier (P1-P10)
3. **Audience**:
   - all top_comments → IP frequency (TOP 10 regions)
   - keyword-rule theme classification (职场/婚育/心理状态/学业/经济)
   - regex extract identity self-disclosures (`(\d+岁|\d{2}年|宝妈|学生|创业)`)
   - comment length median + long-comment %
4. **Viral formulas**: TOP 5 likes notes + dominant pattern + collect/like ratio
5. **Improvement directions**: rule-based recommendations comparing this account to:
   - Form gap (e.g., 100% video → recommend adding 图文 cards)
   - Formula concentration (single formula or diversified?)
   - Matrix signals from bio (@-mentions of other accounts → suggest xhs-matrix-identify)
   - 3 concrete actions ("本周可抄") — formatted as 标题 + 角度 + 形式 + 触达痛点

### Step 5: Render report (`shared/lib/report.py::render_account_decompose`)

5-section markdown using template `account_decompose_template.md`.

### Step 6: Push to Feishu

```python
adapter = get_adapter("feishu", config=config)
doc_token = adapter.push_doc(
    title=f"[拆解] {nickname}_{date}",
    md=report_md,
    folder_token=config.feishu.folder_token
)
```

## Failure modes & fallbacks

| Symptom | Cause | Action |
|---|---|---|
| TOP 1/2 notes blocked (风控) | xhs anti-scrape | use TOP 3-5 detail; mark `data_limitation` in report |
| Account < 100 fans + < 5 notes | sample too thin | warn user; report still generated but with `low_confidence: true` |
| Profile fetch returns empty feeds | account hidden / restricted | abort with clear error |
| Comments empty across all notes | new account / bot account | skip §三 (audience), generate §一/二/四/五 only |

## Output schema

```json
{
  "_meta": {
    "fetched_at": "<ISO>",
    "data_limitations": ["TOP 1/2 blocked by anti-scrape", "..."]
  },
  "profile": {...},
  "tags": {"self": [...], "title_freq": [[...]], "pattern_dist": {...}},
  "audience": {"ip_top10": [...], "themes": {...}, "self_disclosures": [...], "comment_stats": {...}},
  "formulas": {"top5": [...], "dominant_pattern": "...", "collect_like_ratio": 0.x},
  "improvements": [...],
  "actions_to_copy": [{"title": "...", "angle": "...", "form": "...", "pain": "..."}, ...]
}
```
