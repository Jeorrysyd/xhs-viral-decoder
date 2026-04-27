# xhs-viral-rewrite · examples

See [../../examples/viral_rewrite_sample.md](../../examples/viral_rewrite_sample.md) for a full sample (a TOP 30 mapping for the 真相拆解师 persona).

## Sample invocation

```
User: 把刚才那份本周爆款，用我「真相拆解师」人设改写一遍

Claude: [invokes xhs-viral-rewrite --input output/2026-04-27/viral-pulse/ --persona 真相拆解师]

Step 1/7: Loaded viral-pulse output (TOP 30) + persona「真相拆解师」
Step 2/7: Built rewrite prompt — 4,800 chars
Step 3/7: [In-conversation Claude] generates 30 bespoke rewrites...
Step 4/7: Parsing response... 30/30 valid, all unique, all within constraints
Step 5/7: Saved rewrites.json
Step 6/7: Re-rendered viral-pulse report with §六 (30-row table) + §四 anchors (10 selected topics now linked)
Step 7/7: Updated Feishu doc (overwrite mode) + reimported sheet with 2 new columns

Done. Open the updated report:
https://www.feishu.cn/docx/<viral-pulse-doc-token>

Sample rewrites:
  Rank 1 (95k 赞 / 不要中计 ×3) → 拆解一下：你以为的「中计」，永远不是事实判断
  Rank 4 (52k 赞 / 这段话平复了我所有焦虑) → 焦虑的根因，不是你想的那种思维方式
  Rank 9 (26k 赞 / 缺乏主体性的你) → 「主体性缺失」的真相：永远不是变得更努力
```

## Sample rewrite quality (good vs bad)

### Good (uses the 真相拆解师 validated formula)

| Rank | Original | Rewrite |
|---|---|---|
| 1 | 不要中计，不要中计，不要中计。 | **拆解一下：你以为的「中计」，永远不是事实判断** |
| 4 | 这段话平复了我所有的焦虑 | **焦虑的根因，不是你想的那种思维方式** |
| 9 | 缺乏主体性的你，应该很累吧。 | **「主体性缺失」的真相：永远不是变得更努力** |

These work because:
- Use the validated formula「永远不是 X」
- Speak in the persona's voice (拆解一下 / 真相是)
- Preserve the original hook (中计 / 焦虑 / 主体性)
- Don't anesthetize / use 治愈 tone (matches constraint)

### Bad (would fail validation)

```
Rank 1: 「治愈一下：先接住自己」          ← uses 治愈 tone (violates constraint)
Rank 2: 「不要中计的 3 个方法」              ← uses N 步格式 (violates constraint "no 干货清单")
Rank 3 == Rank 4: same template substitution ← duplicates fail uniqueness check
```

## What good output looks like

- All 30 rewrites are bespoke (not template-substituted)
- Persona's `validated_viral_formula` appears in 30-50% of rewrites (double-down on what works)
- Confidence distribution: ≥ 70% high, ≤ 10% low
- All rewrites pass the persona's constraints (auto-checked)
- §四 TOP 10 选题 each anchors to a specific TOP 30 viral note
