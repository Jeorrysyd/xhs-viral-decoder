# xhs-viral-rewrite · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--input` | path | `output/<latest_date>/viral-pulse/` | Directory of viral-pulse output |
| `--persona` | string | `config.defaults.persona` | Persona name (file at `persona/<name>.json`) |
| `--top-n` | int | `30` | Rewrite TOP N (≤ TOP available in viral-pulse output) |
| `--update-feishu` | bool | `true` | Also update existing viral-pulse Feishu doc |

## Step-by-step

### Step 1: Load inputs

```python
analysis = json.load(open(f"{input_dir}/analysis.json"))
persona = json.load(open(f"persona/{persona_name}.json"))
stratum_guide = open("shared/reference/xhs_stratum_guide.md").read()
```

### Step 2: Build rewrite prompt (structured template)

```python
prompt = render_rewrite_prompt(
    persona=persona,
    top_notes=analysis["top30"][:top_n],
    stratum_guide=stratum_guide,
    carol_examples=CAROL_REFERENCE_REWRITES,  # 7 hardcoded benchmarks
    output_schema=REWRITE_OUTPUT_SCHEMA
)
# Saves to: output/<date>/viral-rewrite/rewrite_request.md
```

### Step 3: Invoke Claude (the agent running this skill) via the prompt

The prompt is appended to the conversation. Claude is expected to respond with a JSON array of 30 rewrites following the schema.

This is the **key automation point**: instead of asking the user to run a separate "curate" step, the skill creates a self-contained prompt that the in-conversation Claude can fulfill in one turn.

### Step 4: Parse Claude's response

```python
from shared.lib.rewrite import parse_rewrite_response
rewrites = parse_rewrite_response(claude_response)
# rewrites: [{rank, original_title, rewrite, suggested_form, angle, confidence}, ...]
```

Validation:
- Must have exactly `top_n` entries
- Each `rewrite` ≤ 50 chars (xhs title limit)
- Each `confidence` ∈ {high, medium, low}
- No two rewrites are identical (catches template-substitution failure mode)

If validation fails: fall back to "regenerate" (re-prompt with stricter instructions).

### Step 5: Save rewrites JSON

```python
json.dump({
    "_meta": {
        "persona_used": persona_name,
        "input_viral_pulse": input_dir,
        "engine": "prompt-template-driven, Claude-synthesized",
        "high_conf_pct": ...
    },
    "rewrites": rewrites
}, open(f"{output_dir}/rewrites.json", "w"))
```

### Step 6: Re-render the viral-pulse report (with §六 + §四 anchors)

```python
from shared.lib.report import build_full_report_with_rewrites
new_md = build_full_report_with_rewrites(analysis, rewrites)
```

Adds:
- **§六「<persona_name> 人设改写映射 (TOP 30)」** — full 30-row table
- **§四 TOP 10 选题** — each topic gains `原爆款锚点：§六 #N（原标题 · 赞数）` field

### Step 7: Update Feishu doc + sheet

```python
adapter = get_adapter("feishu", config=config)
# Overwrite the doc (stable token, found in viral-pulse output's feishu_artifacts.json)
adapter.update_doc_overwrite(doc_token=viral_pulse_doc_token, new_md=new_md)
# Re-import the sheet with 2 new columns
new_xlsx = build_sheet_with_rewrites(...)
new_sheet_token = adapter.push_sheet(...)
adapter.delete(old_sheet_token)
adapter.move_to_folder(new_sheet_token, folder_token)
```

## Rewrite prompt template (key part)

The prompt (saved to `rewrite_request.md`) contains:

```
You are generating 30 Carol-style title rewrites for a Xiaohongshu creator.

PERSONA:
{persona_json}

KEY CONSTRAINTS (do NOT violate):
{persona.constraints}

VOICE SIGNATURE (use these phrases naturally):
{persona.voice_signature_phrases}

VALIDATED FORMULA (this creator's already-proven hook — double down on it):
{persona.validated_viral_formula}

REFERENCE BENCHMARKS (Carol's 7 rewrites as style anchor):
- Original: 普通人如何展开 2026? → Rewrite: 30+ 女性的年度规划实操版
- Original: 你的弱点更是你的优点!!! → Rewrite: 弱点如何变成差异化优势
- Original: 强女思维｜2026 跟自己的 8 个约定 → Rewrite: Carol 版本的年度约定
- Original: 2024 我找到了我的「自我使用说明书」 → Rewrite: 36 岁的自我说明书
- Original: 要像建设新中国一样建设自己 → Rewrite: 创业 8 年如何「建设自己」
- Original: 分享一个瞬间让我 0 烦躁焦虑的「暴论」 → Rewrite: 反焦虑真话，不是鸡汤
- Original: 人生建议: 尽早解决让你不舒服的生活小事 → Rewrite: 小事背后的大道理

TASK:
For each of the 30 viral notes below, generate ONE bespoke rewrite.
Rules:
1. Take the unique HOOK from the original (key phrase / number / format) — don't substitute templates
2. Apply the persona's voice + identity anchors
3. Stay within constraints (no 卖课, no 大师 tone, etc.)
4. Output ≤ 50 chars per rewrite
5. Each rewrite must be DIFFERENT from the others (no template repetition)

INPUT NOTES:
{top_30_notes_json}

OUTPUT FORMAT (strict JSON array):
[
  {
    "rank": 1,
    "original_title": "...",
    "rewrite": "...",
    "suggested_form": "图文卡片|图文长文|口播|vlog|视频|...",
    "angle": "<one-line transform reasoning>",
    "confidence": "high|medium|low"
  },
  ...
]
```

## Failure modes

| Symptom | Action |
|---|---|
| Claude response has < 30 rewrites | Re-prompt with explicit "must produce N entries" |
| 2+ rewrites identical | Re-prompt with stricter "each must be unique" |
| Rewrites violate constraints (e.g., uses "教你") | Re-prompt with constraint highlighted |
| Validation regenerates 3× and still fails | Save partial result + warn user, suggest manual fixup |

## Tunable

In `shared/lib/rewrite.py`:
- `CAROL_REFERENCE_REWRITES` — the 7 reference benchmarks
- `MAX_RETRIES` — how many regeneration attempts (default 3)
- Validation rules
