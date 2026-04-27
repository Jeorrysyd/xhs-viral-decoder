# xhs-persona-synth · examples

See [../../examples/persona_sample.json](../../examples/persona_sample.json) for a full sample persona.

## Sample invocation

```
User: 我账号是「真相拆解师」，帮我生成 persona

Claude: [invokes xhs-persona-synth --nickname "真相拆解师"]

Step 1/7: Resolved user_id 67ff1829... via search ✓
Step 2/7: Fetched profile — 173粉, 9475 总赞藏, 30 笔记, 100% 图文
Step 3/7: Skipped TOP detail fetch (low fan count, 信号已足)
Step 4/7: Applying 6-stratum lens...
Step 5/7: Sub-stratum vote results:
  cognitive: +57 (bio +12: 拆解/逻辑/真相/不合时宜/深度 | titles +45: "永远不是 X" × 15 / 30)
  womens_growth: +0
  healing: +0
  howto: +3
  academic: +0
  lifestyle: +0
  → CLASSIFIED: cognitive (反共识派)

Step 6/7: Synthesized persona...
  core_tags: ["反套路心理观察家", "认知拆解者"]
  voice_phrases: ["X 的方法/秘诀/路径，永远不是 Y", "不是 A，是 B", ...]
  validated_formula: ["建立亲密关系的秘诀，永远不是坦诚和沟通 (3433赞)", ...]
  story_assets: []  ← (匿名账号 → 待用户补充)
  needs_user_review: true

Step 7/7: Pushed to Feishu folder ✓

Saved: persona/真相拆解师.json
Feishu doc: https://www.feishu.cn/docx/<token>

Now tune the docx in Feishu (especially story_assets), then run:
  xhs-viral-rewrite --persona 真相拆解师 --input <viral-pulse-output>
```

## What good output looks like

- `_synthesis_notes` clearly shows the substratum vote (which signals tipped the decision)
- `validated_viral_formula` only fills if account has ≥1 viral note (likes ≥ 5× median)
- `needs_user_review: true` honestly flagged when story_assets empty or bio thin
- Persona JSON is consumable by `xhs-viral-rewrite` directly (no manual reshaping needed)
- Feishu docx is editable and visually organized (not just JSON dump)
