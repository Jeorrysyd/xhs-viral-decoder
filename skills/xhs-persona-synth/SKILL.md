---
name: xhs-persona-synth
description: Auto-generates a Xiaohongshu (小红书) creator persona JSON from the account's bio + recent posts using a 6-stratum classification lens (cognitive / healing / how-to / academic / women's growth / lifestyle). Produces ready-to-use persona file driving downstream rewrite + content workflows. Use when the user says 我账号是 X / 帮我生成 persona / 自动建人设档案 / 我的小红书是 X / persona init / generate persona for my xiaohongshu account.
---

# xhs-persona-synth — 人设档案自生成

Reads a Xiaohongshu creator account's public data and synthesizes a structured persona JSON, ready to be consumed by `xhs-viral-rewrite` and other content workflows.

## When to use

User wants to bootstrap a persona from their own (or someone else's) xhs account:
- 「我账号是 https://xhs.com/user/profile/X，帮我生成 persona」
- 「我昵称叫『真相拆解师』，自动建一份人设档案」
- 「Generate persona for this xhs creator」

## Quick start

```bash
# Option A: by URL
python3 shared/lib/cli.py persona-synth \
  --url "https://www.xiaohongshu.com/user/profile/<id>?xsec_token=..."

# Option B: by nickname (skill auto-resolves URL via search)
python3 shared/lib/cli.py persona-synth --nickname "真相拆解师"
```

## What it produces

Two artifacts:

1. **`persona/<nickname>.json`** — machine-readable persona consumed by other skills
2. **Feishu docx** — human-readable + editable persona file for ongoing tuning

Persona schema (key fields):
- `core_tags` (1-3) — primary IP labels
- `secondary_tags` (0-3) — supporting labels
- `story_assets` — concrete experience anchors (may be empty for anonymous accounts)
- `topic_focus` — 5-8 main themes
- `tone_palette` — voice register (3-5 words)
- `voice_signature_phrases` — recurring linguistic patterns
- `persona_anchors_for_rewrite` — 4 fields used by rewrite engine
- `form_capability` — 图文/口播/vlog/视频 preferences
- `form_routing` — pattern → form mapping for rewrite
- `constraints` — red lines (e.g., "no 卖课, no 大师 tone")
- `validated_viral_formula` — already-proven hooks from this account's TOP notes
- `_synthesis_notes` — markdown explaining sub-stratum classification

See [../../examples/persona_sample.json](../../examples/persona_sample.json) for a full example.

## Workflow detail

See [workflow.md](workflow.md) — uses [../../shared/reference/xhs_stratum_guide.md](../../shared/reference/xhs_stratum_guide.md) as the classification lens.

## When to manually edit the persona

The auto-synth marks `needs_user_review: true` because:
- `story_assets` may be empty for anonymous accounts → user should add 1-2 personal experience anchors
- `voice_signature_phrases` based on title patterns may miss spoken-style phrases
- `constraints` may need refinement after running first rewrite

The Feishu docx is editable. After editing, sync back: `python3 shared/lib/cli.py persona-sync --from-feishu --nickname X`.

## Composition with other skills

- **Required by**: `xhs-viral-rewrite` (must have a persona)
- **Required by**: `xhs-viral-pulse --persona X` mode

## Examples

See [examples.md](examples.md).
