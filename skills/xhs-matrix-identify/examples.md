# xhs-matrix-identify · examples

See [../../examples/matrix_identify_sample.md](../../examples/matrix_identify_sample.md) for a full sample (来都来了播客 light matrix vs 谢胜子 heavy matrix).

## Sample invocation

```
User: 找下心理赛道有哪些矩阵号 — 用 <url> 这个博主做对照

Claude: [invokes xhs-matrix-identify --target-url <url> --peer 谢胜子]

Step 1/8: Fetched target profile (12k 粉)
Step 2/8: Detected 2 @-mentions in bio (light matrix signal: @丸籽本丸 @NicoleDeng)
Step 3/8: Searched name roots → found 2 sub-accounts (主播个人号)
Step 4/8: Fetched peer benchmark 谢胜子 → 13 sub-accounts identified
Step 5/8: Analyzing distribution logic...
  - Target: 3 accounts, 自然形成 (主号 + 主播1 + 主播2)
  - Peer: 13 accounts, 主动建号铺量 (主号 + N 切片 + 助理)
Step 6/8: Generated single-person 2-account proposal
Step 7/8: Rendering 4-section report...
Step 8/8: Pushed to Feishu

Bottom line: target = 轻矩阵 (single-person可学), peer = 重矩阵 (need team, 不要学).
你的现实方案：「主号: 创始人/工具」 + 「副号: 用户故事/生活」 — 同素材切 2 角度。
```

## What good output looks like

- §一 has both target's matrix table and peer's matrix table side-by-side
- §二 explains the **distribution rule** explicitly (不是简单列表，是 "同一段素材怎么切给不同号")
- §三 has actual leverage numbers (e.g., 「3× exposure for light, 6-7× for heavy」)
- §四 has Joyce-actionable design (specific 主号/副号 angle + cadence + which-素材-切-哪个号 mapping)
