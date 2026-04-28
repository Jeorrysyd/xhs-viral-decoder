---
name: xhs-viral-rewrite
description: Rewrites Xiaohongshu (小红书) TOP 30 viral note titles into bespoke versions matching a creator's persona — 「萧萧Carol-style」 distillation of 「validated viral hook + my own identity angle = a title I can actually shoot」. Replaces TOP 10 generic topic suggestions with persona-anchored variants. Use when the user asks to 按我人设改写爆款 / 套我人设 / 把爆款翻译成我能拍的版本 / persona rewrite / bespoke viral title rewrite.
---

# xhs-viral-rewrite — 爆款人设改写

Takes a viral-pulse report's TOP 30 notes + a persona JSON, produces 30 bespoke Carol-style rewrites where each preserves the validated viral hook but speaks in the creator's own voice.

## When to use

User has run `xhs-viral-pulse` and wants persona-aware rewrites:
- 「把刚才那份爆款用我人设改写一遍」
- 「按我人设把这 30 条改成我能拍的标题」
- 「Rewrite these viral hooks for my persona」

## Quick start

```bash
python3 shared/lib/cli.py viral-rewrite \
  --input output/2026-04-27/viral-pulse/ \
  --persona 真相拆解师
```

If `--input` omitted, uses the most recent viral-pulse output. If `--persona` omitted, uses `config.yaml::defaults.persona`.

## What it produces

Updates the existing viral-pulse report in Feishu by:
1. **Adding §六「Joyce 人设改写映射 (TOP 30)」** — 30-row table mapping original viral title → recommended form + persona-adapted rewrite + transformation angle
2. **Updating §四 TOP 10 选题** — each topic gains an `原爆款锚点` field linking to specific TOP 30 notes
3. **Updating the sheet** — adds 2 columns: `推荐改编形式` + `<persona_name> 改写标题`

## How the rewrite engine works (key design decision)

**Not pure rules** (v0.1/v0.2 produced repetitive, non-fluent output).
**Not manual curation** (v0.3 wasn't automatable).
**Instead: prompt-template-driven.**

The skill writes a structured prompt to `output/<date>/viral-rewrite/rewrite_request.md` containing:
- Full persona JSON (core_tags, voice_signature_phrases, constraints, etc.)
- All 30 TOP viral notes (title + likes + pattern + content excerpt)
- The 6-stratum guide as context
- Carol's 7 reference rewrites as style anchor
- Output format schema

Then the skill **invokes Claude (the agent running this skill)** to fill in 30 bespoke rewrites following the prompt. The skill parses Claude's response and merges back into a structured `rewrites.json`.

This pattern matches Anthropic best practice for high-degrees-of-freedom tasks: the skill provides constrained guidance + reference data, the LLM provides synthesis.

See [workflow.md](workflow.md) for the full prompt template.

## Workflow detail

See [workflow.md](workflow.md).

## Composition with other skills

- **Required input**: `xhs-viral-pulse` output (directory with analysis.json + report.md)
- **Required input**: `xhs-persona-synth` output (persona JSON)

## Failure modes — feishu output is REQUIRED

The skill **must** end with a Feishu doc URL handed back to the user (the updated viral-pulse doc with §六 appended). If feishu push fails for any reason, **stop and ask the user to fix the configuration**. Do NOT silently degrade to local-only output.

| Failure | Action |
|---|---|
| `lark-cli` binary not in PATH | STOP. Tell user to install lark-cli per [setup/02_install_lark_cli.md](../../setup/02_install_lark_cli.md). |
| `lark-cli` auth expired (`LarkAuthExpired`) | STOP. Tell user: `lark-cli auth login --as bot` |
| Bot lacks scope (`LarkScopeMissing`) | STOP. Show the `scope_url` from the error; user grants in 1 click in 飞书 console. |
| `feishu_artifacts.json` missing in viral-pulse output | STOP. Tell user to re-run viral-pulse first so the original Feishu doc exists. |
| `config.yaml` missing `feishu.folder_token` | STOP. Tell user to edit `config.yaml`. |

Local markdown / JSON files saved during the run are intermediate artifacts — they are **not** the deliverable.

## Examples

See [examples.md](examples.md) and [../../examples/viral_rewrite_sample.md](../../examples/viral_rewrite_sample.md).
