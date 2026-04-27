# xhs-viral-pulse · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--keywords` | comma-sep | from `config.yaml::defaults.keywords` | 3-5 keywords recommended (each search returns ~22 notes) |
| `--niche` | string | `心理` | used in report title + report context line |
| `--persona` | path | none | if provided, also runs `xhs-viral-rewrite` automatically as §6 |
| `--top-n` | int | `30` | TOP N for ranking section |
| `--output` | path | `output/<date>/viral-pulse/` | local artifacts directory |

## Step-by-step

### Step 1: Verify xhs-mcp login
```python
from shared.lib.xhs import check_login, XhsLoginRequired
try:
    check_login()
except XhsLoginRequired:
    print("⚠️ Please scan QR: cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-login-darwin-arm64")
    sys.exit(1)
```

### Step 2: Fetch data (parallel per keyword)

For each keyword:
1. `search_feeds(keyword, sort="最多点赞")` → returns ~22 notes with feed_id + xsec_token
2. For each unique feed_id: `get_feed_detail(feed_id, xsec_token)` → full content + top 10 comments
3. For each unique author: `user_profile(user_id, xsec_token)` → follower_count

**Failure handling**: Some notes return `Sorry, This Page Isn't Available Right Now.` (xhs 风控). Record in `failures.json`, continue with rest. Need ≥40 valid notes to proceed.

### Step 3: Analyze (`shared/lib/analyze.py`)

Produces structured `analysis_<date>.json`:
- TOP 30 sorted by likes
- Title pattern classification (P1-P10) — see `shared/reference/title_formulas.md`
- Opinion category for each note (uses keyword-rule classifier)
- Pain-point quotes bucketed (8 buckets) — see `shared/reference/pain_point_buckets.md`
- Hot topic word frequency
- Quantitative stats (median, low-fan viral count, form distribution, etc.)
- Low-fan viral list (粉丝<5万 & 赞>1万)

### Step 4: Render report (`shared/lib/report.py`)

Generates 5-section markdown using template `viral_pulse_template.md`:
1. 数据排行榜 TOP 30 (table)
2. 爆款内容框架分析 (formulas + distribution)
3. 核心信息点汇总 (hot words + 8 pain buckets with verbatim quotes)
4. 本周可用爆款选题建议 TOP 10 (each anchored to specific viral notes)
5. 数据规律总结 (quantitative baselines)

### Step 5: Generate sheet CSV/XLSX

`shared/lib/report.py::build_sheet()` outputs 16-column XLSX:
排名/标题/笔记类型/点赞/收藏/评论/分享/作者/粉丝数/IP/命中关键词/观点分类/标题公式/发布时间/链接/feed_id

If `--persona` provided, also adds 2 columns: 推荐改编形式 / Joyce 改写标题 (filled by xhs-viral-rewrite).

### Step 6: Push to Feishu

```python
from shared.lib.output_adapter import get_adapter
adapter = get_adapter("feishu", config=config)
sheet_token = adapter.push_sheet(title=f"心理赛道_原始数据_{date}", xlsx_path=...)
doc_token = adapter.push_doc(title=f"心理赛道_本周爆款选题报告_{date}", md=report_md)
adapter.move_to_folder(folder_token=config.feishu.folder_token, items=[sheet_token, doc_token])
```

Tokens recorded to `output/<date>/viral-pulse/feishu_artifacts.json`.

### Step 7 (optional): Run rewrite

If `--persona` provided, automatically invoke `xhs-viral-rewrite` with the just-generated TOP 30. See [../xhs-viral-rewrite/SKILL.md](../xhs-viral-rewrite/SKILL.md).

## Failure modes & fallbacks

| Symptom | Likely cause | Action |
|---|---|---|
| `XhsLoginRequired` | cookie 过期 | scan QR via xhs-mcp login binary |
| `<40 valid notes` | 关键词太冷门 / 风控严 | suggest more keywords or different sort |
| `lark-cli` error: `space:folder:create` | scope 不足 | open the URL in error message to grant scope |
| `MCP token truncation` | response > 25k tokens | already handled by `xhs.py` HTTP wrapper |
| Empty pain quotes | comments empty / blocked | report still works; pain section warns |

## Tunable parameters

In `shared/lib/analyze.py`:
- Pain bucket keywords (8 buckets) — modify `PAIN_BUCKETS` to add/rename buckets
- Title pattern rules (10 patterns) — modify `title_pattern()` for new formula types
- Low-fan viral threshold — currently `fans<50000 AND likes>10000`

## Output schema (analysis JSON)

See `shared/lib/analyze.py::build_analysis()` docstring for the full schema.
