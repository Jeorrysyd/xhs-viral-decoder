---
name: xhs-matrix-identify
description: Identifies whether a Xiaohongshu (小红书) creator runs a multi-account distribution matrix and surfaces 3-15 candidate matrix accounts with role-based分工分析. Distinguishes light matrix (3 accounts, natural formation) vs heavy matrix (10+ accounts, intentional buildup like 谢胜子). Use when the user asks to 找矩阵号 / 这博主有几个分号 / 矩阵分发拆解 / 分号联动 / matrix account analysis / find xhs sub-accounts.
---

# xhs-matrix-identify — 矩阵账号识别

Detects multi-account distribution matrices on Xiaohongshu (主号 + 主播号 + 切片号 + 助理号 patterns) and proposes a realistic single-person 2-account variant for the user.

## When to use

User asks:
- 「<url> 这个号背后有几个分号？」
- 「找下心理赛道有哪些矩阵号」
- 「我能不能学这个矩阵玩法」
- 「Find sub-accounts for this xhs creator」

## Quick start

```bash
python3 shared/lib/cli.py matrix-identify \
  --target-url "https://www.xiaohongshu.com/user/profile/<id>?xsec_token=..." \
  --peer 谢胜子   # optional: include a known heavy-matrix benchmark for comparison
```

If `--peer` omitted, the skill picks a default heavy-matrix benchmark from same niche (e.g., 谢胜子 for 心理/成长 niche).

## What it produces

Single comparison docx in Feishu folder with 4 sections:

1. **矩阵主体识别** — main account + candidate sub-accounts (table with user_id / form / positioning / TOP likes)
2. **内容分发逻辑** — same-source-different-angle distribution rules (核心增值)
3. **矩阵杠杆量化** — total exposure × N estimation
4. **可借鉴 / 不可借鉴 + Joyce 单人现实方案** — explicit 「don't try to copy heavy matrix if you don't have a team; here's a realistic 2-account light matrix design」

## Workflow detail

See [workflow.md](workflow.md).

## Composition with other skills

- After this skill runs, often follow with `xhs-account-decompose` on each candidate sub-account for deeper analysis
- Share findings with `xhs-persona-synth` to design a副号 persona

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

See [examples.md](examples.md) and [../../examples/matrix_identify_sample.md](../../examples/matrix_identify_sample.md).
