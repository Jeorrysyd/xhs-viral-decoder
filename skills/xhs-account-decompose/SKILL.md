---
name: xhs-account-decompose
description: Performs deep teardown of a single Xiaohongshu (小红书) creator account — extracts profile, existing tags, audience persona from comment IPs, title formulas, content forms, and concrete improvement directions. Use when the user asks to 拆解这个博主 / 拆这个号 / 分析对标账号 / 这个账号怎么做起来的 / 学这个博主怎么做 / decompose this xhs creator / analyze this xiaohongshu account.
---

# xhs-account-decompose — 单号深度拆解

5-section deep teardown of any Xiaohongshu account, modeled after the 「萧萧Carol-style」 reference report.

## When to use

User pastes a Xiaohongshu profile URL and asks:
- 「深度拆解这个博主：<url>」
- 「<url> 这个号怎么做起来的？」
- 「学一下这个对标账号」
- 「Tell me how this xhs creator does it」

## Quick start

```bash
python3 shared/lib/cli.py account-decompose \
  --url "https://www.xiaohongshu.com/user/profile/<id>?xsec_token=<token>"
```

If URL has no `xsec_token` (e.g., from app share), the skill will:
1. Extract nickname from any of their notes (search by user_id)
2. Re-resolve a fresh token from search results

## What it produces

5-section docx in Feishu folder:

1. **账号基本信息** — nick / fans / IP / bio / total engagement / 爆款率 / 大爆率
2. **现有标签** — bio self-tags + title high-frequency words + title formula distribution
3. **目标人群画像** — comment IP geography + theme distribution + identity self-disclosures + comment length stats
4. **爆款公式与内容框架** — TOP 5 viral notes detail + dominant formula analysis + form distribution
5. **可改进方向** — content direction / formula ROI / form mix / posting cadence / matrix opportunity / **3 specific actions to copy**

## Workflow detail

See [workflow.md](workflow.md).

## Composition with other skills

- **Pair with `xhs-matrix-identify`** if account looks matrix-ready (bio @ other accounts, multiple linked profiles)
- **Pair with `xhs-persona-synth`** to use this account's persona insights for your own rewrite

## Failure modes — feishu output is REQUIRED

The skill **must** end with a Feishu doc URL handed back to the user. If feishu push fails for any reason, **stop and ask the user to fix the configuration**. Do NOT silently degrade to local-only output.

| Failure | Action |
|---|---|
| `lark-cli` binary not in PATH | STOP. Tell user to install lark-cli per [setup/02_install_lark_cli.md](../../setup/02_install_lark_cli.md). |
| `lark-cli` auth expired (`LarkAuthExpired`) | STOP. Tell user: `lark-cli auth login --as bot` |
| Bot lacks scope (`LarkScopeMissing`) | STOP. Show the `scope_url` from the error; user grants in 1 click in 飞书 console. |
| `config.yaml` missing `feishu.folder_token` | STOP. Tell user to edit `config.yaml`. |

Local markdown / JSON files saved during the run are intermediate artifacts — they are **not** the deliverable.

## Examples

See [examples.md](examples.md) and [../../examples/account_decompose_sample.md](../../examples/account_decompose_sample.md).
