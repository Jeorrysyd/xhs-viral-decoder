---
name: xhs-viral-pulse
description: Generates a 5-section weekly viral content report for Xiaohongshu (小红书) — searches keywords, ranks TOP 30 viral notes, extracts title formulas, mines pain points from real comments, and recommends TOP 10 content topics. Output goes to a Feishu folder. Use when the user asks to 拆解本周爆款 / 跑爆款周报 / 看 X 赛道爆款 / 做内容选题 / 这周 X 关键词热门 / weekly viral report / xiaohongshu trending content / decompose viral notes for content planning.
---

# xhs-viral-pulse — 小红书爆款周报

Pulls TOP 30 viral notes for given keywords, mines real-comment pain points, and outputs a 5-section actionable weekly report to Feishu.

## When to use

User asks (in any language):
- 「拆解本周心理赛道的同款爆款」
- 「跑下本周关键词 X/Y/Z 的爆款周报」
- 「我这周该写什么选题？」
- 「Generate this week's viral pulse for [niche]」

## Quick start

```bash
# 1. Check dependencies (only first time)
bash skills/../tests/verify_install.sh

# 2. Run the workflow
python3 shared/lib/cli.py viral-pulse \
  --keywords 情绪管理,内耗,自我疗愈 \
  --persona path/to/persona.json    # optional, omit to skip rewrite section
```

## What it produces (in Feishu folder)

1. **数据排行榜 TOP 30** — table with likes / collects / comments / author / fans / category
2. **爆款内容框架分析** — high-frequency title formulas (P1-P10) + form distribution + opinion category breakdown
3. **核心信息点汇总** — TOP 20 hot topic words + 8 pain-point buckets with **real verbatim comment quotes** (IP + likes + source attribution)
4. **本周可用爆款选题建议 TOP 10** — each topic anchored to specific TOP 30 viral notes
5. **数据规律总结** — quantitative baselines (median likes, low-fan viral %, form ROI, formula upvote rate)

Plus a 58-row CSV of full data, importable as a native Feishu sheet.

## Workflow detail

See [workflow.md](workflow.md) for the full step-by-step (data fetch → analyze → render → push).

## Composition with other skills

Common chains:
- `xhs-viral-pulse` → `xhs-viral-rewrite` (uses TOP 30 as input for persona-based rewrites)
- `xhs-viral-pulse` → `xhs-trend-scan` (mines emerging concepts from same dataset)

## Examples

See [examples.md](examples.md) for a full sample report.
