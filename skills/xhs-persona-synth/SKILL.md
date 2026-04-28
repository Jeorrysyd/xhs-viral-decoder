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
python3 shared/lib/cli.py persona-init \
  --url "https://www.xiaohongshu.com/user/profile/<id>?xsec_token=..."

# Option B: by nickname (skill auto-resolves URL via search)
python3 shared/lib/cli.py persona-init --nickname "真相拆解师"
```

## What it produces

**Primary deliverable**: an editable persona docx in your Feishu folder. This is the source of truth — the user reads it, edits it, and refers back to it.

**Intermediate artifact** (saved locally for debugging): `persona/<nickname>.json` — machine-readable persona consumed by downstream skills (`xhs-viral-rewrite`, `xhs-viral-pulse --persona ...`).

If feishu push fails, the skill stops with an error (see `## Failure modes` below). The local JSON is left behind for inspection but the run is **not** considered successful — there's no "fall back to local-only" path.

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

The Feishu docx is editable. After editing, sync back by manually copying changes to `persona/<nickname>.json`. (Automated sync from Feishu is planned but not yet implemented.)

## Composition with other skills

- **Required by**: `xhs-viral-rewrite` (must have a persona)
- **Required by**: `xhs-viral-pulse --persona X` mode

## Failure modes — feishu output is REQUIRED

The skill **must** end with a Feishu doc URL handed back to the user. If feishu push fails for any reason, **stop and ask the user to fix the configuration**. Do NOT silently degrade to local-only output (that's the bug this section exists to prevent — see commit history).

| Failure | Action |
|---|---|
| `lark-cli` binary not in PATH | STOP. Tell user to install lark-cli per [setup/02_install_lark_cli.md](../../setup/02_install_lark_cli.md). |
| `lark-cli` auth expired (`LarkAuthExpired`) | STOP. Tell user: `lark-cli auth login --as bot` |
| Bot lacks scope (`LarkScopeMissing`) | STOP. Show the `scope_url` from the error; user grants in 1 click in 飞书 console. |
| `config.yaml` missing `feishu.folder_token` | STOP. Tell user to edit `config.yaml`. |

The local `persona/<nickname>.json` is an intermediate artifact for downstream skills — it is **not** a successful deliverable on its own.

For workflow-level failure modes (low note count, empty bio, off-niche), see [workflow.md](workflow.md).

## Examples

See [examples.md](examples.md).
