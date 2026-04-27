# persona/

This directory holds **your own** auto-generated persona JSONs.

## Don't commit these

`persona/*.json` is gitignored. Each persona is yours alone — keep it private if you want.

The only file checked in is this README and `examples/persona_sample.json`.

## How to create one

```bash
python3 shared/lib/cli.py persona-init --nickname "<your-xhs-nickname>"
```

Or via natural language in a Claude chat: 「我账号是 xxx，帮我生成 persona」.

## Manual editing

Auto-synth marks `needs_user_review: true`. Common things to edit:

- **`story_assets`** is often empty for anonymized accounts → add 1-2 personal experience anchors
- **`voice_signature_phrases`** auto-extracted from titles may miss your spoken style
- **`constraints`** may need to be more specific (e.g., add "don't use 教你 / 救你")

## Multiple personas

If you have several xhs accounts (different IPs), create one persona per account:

```bash
vd persona-init --nickname "你的小红书 IP A"
vd persona-init --nickname "你的小红书 IP B"
```

Then specify in workflows:

```bash
vd viral-rewrite --persona "IP A"
```
