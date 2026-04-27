"""Persona-aware viral title rewrite engine — prompt-template-driven.

The skill itself does NOT call any LLM API. Instead it:
1. Builds a structured prompt containing persona + TOP N notes + Carol benchmarks + schema
2. Writes that prompt to a `.md` file in output/
3. Caller (the in-conversation Claude in Claude Code) reads the prompt and
   responds with a JSON array of bespoke rewrites
4. `parse_rewrite_response()` validates and merges Claude's JSON back

This pattern matches Anthropic skill best practice for high-degrees-of-freedom tasks:
the skill provides constrained guidance + reference data, the LLM provides synthesis.
"""
import json
import re
from typing import Optional


# Carol's 7 reference rewrites — used as style anchor in every prompt
CAROL_REFERENCE_REWRITES = [
    ("普通人如何展开2026?(实操喂饭版)", "30+ 女性的年度规划实操版", "口播"),
    ("你的弱点更是你的优点!!!", "弱点如何变成差异化优势", "口播"),
    ("强女思维｜2026 跟自己的 8 个约定", "Carol 版本的年度约定", "vlog"),
    ("2024 我找到了我的「自我使用说明书」", "36 岁的自我说明书", "vlog"),
    ("要像建设新中国一样建设自己", "创业 8 年如何「建设自己」", "口播"),
    ("分享一个瞬间让我 0 烦躁焦虑的「暴论」", "反焦虑真话，不是鸡汤", "口播"),
    ("人生建议: 尽早解决让你不舒服的生活小事", "小事背后的大道理", "vlog"),
]


def build_rewrite_prompt(
    persona: dict,
    top_notes: list,
    stratum_guide_excerpt: str = "",
    top_n: int = 30,
) -> str:
    """Build the structured prompt to ask Claude for bespoke rewrites."""
    persona_summary = {
        "core_tags": persona.get("core_tags"),
        "voice_signature_phrases": persona.get("voice_signature_phrases"),
        "tone_palette": persona.get("tone_palette"),
        "persona_anchors_for_rewrite": persona.get("persona_anchors_for_rewrite"),
        "constraints": persona.get("constraints"),
        "validated_viral_formula": persona.get("validated_viral_formula"),
    }

    md = []
    md.append("# Rewrite request — please respond with JSON array")
    md.append("")
    md.append("You are generating **30 Carol-style title rewrites** for a Xiaohongshu creator.\n")

    md.append("## PERSONA")
    md.append("```json")
    md.append(json.dumps(persona_summary, ensure_ascii=False, indent=2))
    md.append("```")
    md.append("")

    md.append("## KEY CONSTRAINTS (do NOT violate)")
    for c in persona.get("constraints", []):
        md.append(f"- {c}")
    md.append("")

    md.append("## VOICE SIGNATURE")
    md.append("Use these phrases naturally where appropriate:\n")
    for v in persona.get("voice_signature_phrases", []):
        md.append(f"- 「{v}」")
    md.append("")

    if persona.get("validated_viral_formula"):
        vf = persona["validated_viral_formula"]
        md.append("## VALIDATED FORMULA (this creator's already-proven hook — double down)")
        md.append(f"- {vf.get('primary', '')}")
        md.append("- Examples (your own viral notes):")
        for ex in vf.get("examples", []):
            md.append(f"  - {ex}")
        md.append("")

    md.append("## REFERENCE BENCHMARKS (Carol's rewrites — this is the style/quality target)")
    for orig, rewrite, form in CAROL_REFERENCE_REWRITES:
        md.append(f"- Original: {orig}")
        md.append(f"  → Rewrite: **{rewrite}** (form: {form})")
    md.append("")

    md.append("## TASK")
    md.append(f"For each of the {top_n} viral notes below, generate ONE bespoke rewrite.")
    md.append("")
    md.append("**Rules:**")
    md.append("1. Take the unique HOOK from the original (key phrase / number / format) — don't substitute templates")
    md.append("2. Apply the persona's voice + identity anchors")
    md.append("3. Stay within constraints (no 卖课, no 大师 tone, etc.)")
    md.append("4. Output ≤ 50 chars per rewrite")
    md.append("5. Each rewrite must be DIFFERENT from the others (no template repetition)")
    md.append("6. If persona has `validated_viral_formula`, use it as default for ≥30% of rewrites")
    md.append("")

    md.append("## INPUT NOTES (TOP N viral notes to rewrite)")
    md.append("```json")
    md.append(json.dumps(top_notes, ensure_ascii=False, indent=2))
    md.append("```")
    md.append("")

    if stratum_guide_excerpt:
        md.append("## STRATUM CONTEXT")
        md.append(stratum_guide_excerpt[:1500])  # truncate to keep prompt manageable
        md.append("")

    md.append("## OUTPUT FORMAT (strict JSON array — wrap in ```json fences)")
    md.append("```json")
    md.append("""[
  {
    "rank": 1,
    "original_title": "...",
    "rewrite": "...",
    "suggested_form": "图文卡片|图文长文|口播|vlog|视频",
    "angle": "<one-line transform reasoning>",
    "confidence": "high|medium|low"
  }
  // ... 30 entries total
]""")
    md.append("```")
    md.append("")
    md.append("Begin your response with the JSON array. Add no other commentary.")

    return "\n".join(md)


def parse_rewrite_response(response_text: str, expected_count: int = 30) -> list:
    """Parse Claude's response — extract JSON array, validate.

    Raises ValueError on validation failure.
    """
    # Find the first JSON array in response (between ```json fences or raw)
    fence_match = re.search(r"```json\s*(\[[\s\S]+?\])\s*```", response_text)
    if fence_match:
        json_text = fence_match.group(1)
    else:
        # Fallback: find first [ ... ] block
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start < 0 or end <= start:
            raise ValueError("No JSON array found in response")
        json_text = response_text[start:end]

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    if len(data) != expected_count:
        raise ValueError(
            f"Expected {expected_count} rewrites, got {len(data)}. "
            f"Re-prompt with explicit count requirement."
        )

    rewrites = set()
    required_fields = {"rank", "original_title", "rewrite", "suggested_form", "angle", "confidence"}

    for i, r in enumerate(data):
        missing = required_fields - r.keys()
        if missing:
            raise ValueError(f"Entry {i} missing fields: {missing}")
        if len(r["rewrite"]) > 50:
            raise ValueError(f"Entry {i} rewrite too long ({len(r['rewrite'])} > 50 chars)")
        if r["confidence"] not in ("high", "medium", "low"):
            raise ValueError(f"Entry {i} invalid confidence: {r['confidence']}")
        if r["rewrite"] in rewrites:
            raise ValueError(f"Entry {i} duplicate rewrite: {r['rewrite'][:30]}")
        rewrites.add(r["rewrite"])

    return data


def merge_rewrites_with_top(top_notes: list, rewrites: list) -> dict:
    """Merge parsed rewrites with original metadata into final shape."""
    rw_by_rank = {r["rank"]: r for r in rewrites}
    merged = []
    for n in top_notes:
        rw = rw_by_rank.get(n["rank"], {})
        merged.append({
            "rank": n["rank"],
            "feed_id": n.get("feed_id", ""),
            "url": n.get("url", ""),
            "original_title": n.get("title", "(无标题)"),
            "original_likes": n.get("likes", 0),
            "original_form": "视频" if n.get("note_type") == "video" else "图文",
            "original_pattern": n.get("pattern", ""),
            "category": n.get("category", ""),
            "suggested_form": rw.get("suggested_form", ""),
            "rewrite": rw.get("rewrite", ""),
            "angle": rw.get("angle", ""),
            "rewrite_confidence": rw.get("confidence", "low"),
        })
    return {"rewrites": merged}
