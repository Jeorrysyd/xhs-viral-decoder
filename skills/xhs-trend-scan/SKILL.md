---
name: xhs-trend-scan
description: Detects emerging concept words on Xiaohongshu (小红书) before they go mainstream — extracts 2-4 char Chinese n-grams from recent viral notes, filters against a 5000-word common lexicon baseline, and ranks by recency × viral note appearance × time concentration. Surfaces words like 「奥德赛时期」 1-2 weeks before mainstream pickup. Use when the user asks to 找新概念词 / 流行新词 / 哪些词刚开始火 / 新冒出来的词 / 早期热词识别 / trend scan / emerging concepts.
---

# xhs-trend-scan — 流行新概念词识别

Mines TOP 60-90 recent viral notes for emerging vocabulary that hasn't yet gone mainstream — the 「2 weeks before everyone uses it」 advantage.

## When to use

User asks:
- 「本周有哪些新冒出来的概念词？」
- 「找出近 14 天才开始火的词」
- 「哪些词我应该早点用？」
- 「Find emerging concepts on xhs this week」

## Quick start

```bash
python3 shared/lib/cli.py trend-scan \
  --keywords 情绪管理,内耗,自我疗愈 \
  --window-days 14
```

If `--keywords` omitted, uses `config.yaml::defaults.keywords`.
If you've recently run `xhs-viral-pulse`, this skill auto-reuses that data (saves API calls).

## What it produces

Single docx in Feishu folder with 4 sections:

1. **TOP 10 emerging concepts** — table with 词 / first appearance date / freq / appearing in viral notes / score
2. **For each concept**: source note examples (showing how the word is used in context)
3. **Trend trajectory** — likes growth curve per concept
4. **Action推荐** — 3 concepts most worth Joyce adopting in next-week content

## Detection algorithm (key design)

```
score = (
    log(frequency_in_top_viral) * 3        # appears in viral notes = strong signal
  + recency_concentration * 2              # most appearances within last N days
  + cross_keyword_appearance * 2           # appears across multiple keyword searches
  - in_common_lexicon * 10                 # heavy penalty if it's a common Chinese word
  - in_existing_brand_lexicon * 5          # penalty if it's a brand/proper noun
)
```

Ranked descending; take TOP 10 with score > threshold.

## Common lexicon

5000-word Chinese baseline at `shared/data/common_lexicon.txt` — ensures we surface NEW words, not just common ones. Built from public Chinese frequency tables.

## Workflow detail

See [workflow.md](workflow.md).

## Composition with other skills

- **Pair with `xhs-viral-pulse`** to immediately incorporate trend words into the content plan
- **Pair with `xhs-viral-rewrite`** to use trend words as voice signature additions

## Examples

See [examples.md](examples.md) and [../../examples/trend_scan_sample.md](../../examples/trend_scan_sample.md).
