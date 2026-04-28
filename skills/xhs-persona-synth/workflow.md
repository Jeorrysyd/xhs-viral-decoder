# xhs-persona-synth · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--url` OR `--nickname` | string | — | One of these required |
| `--niche` | string | `心理` | Used as fallback for sub-stratum classification when signals are weak |
| `--output` | path | `persona/<nickname>.json` | Where to save persona JSON |
| `--push-feishu` | bool | `true` | Also create editable docx in Feishu folder |

## Step-by-step

### Step 1: Resolve user_id + xsec_token

If `--nickname`: `search_feeds(nickname)` → first hit's user_id + xsec_token. If `--url`: parse directly (or look up token via search if missing).

### Step 2: Fetch full profile + 30 feeds

```python
data = user_profile(user_id, xsec_token)
# Save raw to: raw/account_<nickname>_<date>.json
```

### Step 3 (optional): Fetch TOP 5 details

For richer voice signal extraction. Fail-tolerant (xhs 风控 may block top notes).

### Step 4: Apply stratum lens

Reference: [../../shared/reference/xhs_stratum_guide.md](../../shared/reference/xhs_stratum_guide.md)

```python
from shared.lib.persona_synth import classify_substratum, synthesize

substratum, scores = classify_substratum(profile, feeds, top_details)
# substratum ∈ {cognitive, healing, howto, academic, womens_growth, lifestyle}
# scores: dict showing votes per substratum (for transparency)

persona = synthesize(profile, feeds, top_details, substratum)
```

### Step 5: Voting rules (sub-stratum classification)

From `xhs_stratum_guide.md`:

```python
# Weights per signal:
score = (bio_voice_words * 4) + (title_pattern_freq * 3) + (form_distribution * 2) + (theme_distribution * 1)

# Bio voice keywords (per substratum):
SUBSTRATUM_BIO_WORDS = {
    "cognitive": ["拆解", "逻辑", "真相", "不合时宜", "深度", "认知"],
    "healing": ["治愈", "疗愈", "陪伴", "温柔", "慢慢来"],
    "howto": ["步骤", "方法", "教你", "亲测", "保姆级"],
    "academic": ["心理学", "依恋", "原生家庭", "依恋理论"],
    "womens_growth": ["30+", "创业", "主体性", "向内求", "她"],
    "lifestyle": ["日常", "vlog", "记录", "散步", "生活"],
}

# Title pattern markers:
SUBSTRATUM_TITLE_PATTERNS = {
    "cognitive": [r"永远不是", r"真相是", r"不是.*?是", r"打破"],
    "healing": [r"治愈", r"接住", r"允许"],
    "howto": [r"^\d+[个种条招]", r"如何", r"怎么"],
    ...
}
```

### Step 6: Synthesize persona JSON

For the chosen substratum, fill the persona schema using:
- `core_tags` ← top 1-3 self-tags from bio (split by `|` `/` newline)
- `voice_signature_phrases` ← title regex matches with freq ≥ 3 + substratum default fallbacks
- `topic_focus` ← top 5-8 title n-gram words minus common-stopwords
- `tone_palette` ← substratum default
- `persona_anchors_for_rewrite` ← substratum default (overridable)
- `form_capability` ← derived from `note_type` distribution (100% normal → 图文 only)
- `constraints` ← substratum default red lines
- `validated_viral_formula` ← extract from TOP 2-3 notes if their likes >= 5× median

Set `needs_user_review: true`. Add `_synthesis_notes` with markdown explaining the classification.

### Step 7: Render + push Feishu docx

```python
md = render_persona_doc(persona)  # human-readable from JSON
adapter.push_doc(
    title=f"[人设档案] {nickname}_{date}",
    md=md,
    folder_token=config.feishu.folder_token
)
```

## Failure modes

| Symptom | Action |
|---|---|
| Account has < 5 notes | Use bio + niche default → low-confidence persona, `needs_user_review` urgent |
| Bio is empty | Use niche default substratum → flag user to fill bio first |
| Multi-substratum tied (top 2 within 5 points) | Output 2 candidate personas, ask user to pick |
| Off-niche (food, fashion, AI) | Run with default substratum lens; flag `needs_user_review` so the user can rename sub-stratum to fit their vertical. (The 6 sub-strata are showcase/reference, not a hard taxonomy — see SKILL.md) |
| **Feishu push failed** (lark-cli missing / auth expired / scope insufficient / folder_token wrong) | **STOP. Surface error to user with config fix instructions. Do NOT silently fall back to local JSON.** See `SKILL.md` `## Failure modes` for the full table. |

## Tunable parameters

In `shared/lib/persona_synth.py`:
- Sub-stratum weights (bio_voice × 4 / title_pattern × 3 / etc.)
- Substratum bio keyword lists
- Title pattern regexes per substratum
- Default `tone_palette` / `constraints` / `persona_anchors_for_rewrite` per substratum
