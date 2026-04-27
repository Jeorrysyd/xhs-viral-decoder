# xhs-trend-scan · examples

See [../../examples/trend_scan_sample.md](../../examples/trend_scan_sample.md) for a full sample.

## Sample invocation

```
User: 本周有什么新冒出来的概念词？心理赛道

Claude: [invokes xhs-trend-scan --keywords 情绪管理,内耗,自我疗愈 --niche 心理]

Step 1/6: Auto-detected recent viral-pulse output → reusing 58 notes (saves API calls)
Step 2/6: Extracted 2-4 char Chinese n-grams... 1,420 unique candidates
Step 3/6: Filtered against 5000-word common lexicon... 87 candidates remain
Step 4/6: Scoring (recency × viral × cross-keyword)...
Step 5/6: Rendering report — TOP 10 emerging concepts
Step 6/6: Pushed to Feishu

TOP 5 emerging concepts (excerpt):
  1. 主体性 (score 18.4) — appears in 6 notes, 3 viral, all in last 9 days
  2. 顿感力 (score 14.2) — appears in 4 notes, 2 viral
  3. 反内耗 (score 12.8) — already trending but accelerating
  4. 钝感力 (score 11.5) — overlap with 顿感力 — likely same meme
  5. 内核稳定 (score 10.3) — appears in podcast切片 cluster

Action: try「主体性」+「顿感力」in your next 2 posts — both have viral correlation + recency window.

Open: https://www.feishu.cn/docx/<token>
```

## What good output looks like

- TOP 10 has actual新词 (not common 心理 jargon like 「焦虑」 「内耗」 — those should be filtered out)
- Each concept has ≥ 3 source notes shown for context
- Trend trajectory cites actual publish dates (not hand-waved)
- Action section recommends 2-3 concepts with explicit reasoning
- "No emerging trends this batch" is an acceptable output if data shows that — better than fabricating
