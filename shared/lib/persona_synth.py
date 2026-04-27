"""Auto-synthesize a creator persona from xhs profile + recent feeds.

Uses the 6-stratum lens (cognitive / healing / howto / academic / women's growth / lifestyle).
See shared/reference/xhs_stratum_guide.md for the lens design.
"""
import json
import re
from collections import Counter
from typing import Optional


# ---------- 6 sub-strata ----------
SUBSTRATA = [
    "cognitive",      # 认知派 / 反共识
    "healing",        # 治愈共情派
    "howto",          # 干货实操派
    "academic",       # 心理学权威派
    "womens_growth",  # 女性成长派
    "lifestyle",      # 生活感叙事派
]


# ---------- Bio voice keywords per substratum (weight: ×4) ----------
SUBSTRATUM_BIO_WORDS = {
    "cognitive": ["拆解", "逻辑", "真相", "不合时宜", "深度", "认知", "解构", "反共识", "探索"],
    "healing": ["治愈", "疗愈", "陪伴", "温柔", "慢慢来", "接住", "允许", "安抚"],
    "howto": ["步骤", "方法", "教你", "亲测", "保姆级", "实操", "技巧", "干货"],
    "academic": ["心理学", "依恋", "原生家庭", "依恋理论", "咨询师", "来访者", "治疗", "精神分析"],
    "womens_growth": ["30+", "创业", "主体性", "向内求", "她", "女性", "成长", "蜕变", "独立"],
    "lifestyle": ["日常", "vlog", "记录", "散步", "生活", "早晨", "周末"],
}


# ---------- Title pattern markers per substratum (weight: ×3 per match) ----------
SUBSTRATUM_TITLE_PATTERNS = {
    "cognitive": [r"永远不是", r"真相是", r"不是.{1,5}是", r"打破", r"拆解", r"反共识"],
    "healing": [r"治愈", r"接住", r"允许", r"陪你", r"被.{1,3}治愈"],
    "howto": [r"^\d+[个种条招步]", r"如何", r"怎么", r"教你", r"亲测", r"步骤"],
    "academic": [r"心理学", r"依恋", r"原生家庭", r"个案", r"咨询"],
    "womens_growth": [r"30\+", r"创业", r"主体性", r"向内求", r"她力量", r"\d+岁的"],
    "lifestyle": [r"vlog", r"记录", r"日常", r"早晨", r"散步"],
}


# ---------- Substratum defaults (used when synthesizing persona) ----------
SUBSTRATUM_DEFAULTS = {
    "cognitive": {
        "core_tags_template": ["反套路心理观察家", "认知拆解者"],
        "tone_palette": ["冷静", "解构", "反共识"],
        "voice_signature_phrases": ["X 的方法/秘诀/路径，永远不是 Y", "不是 A，是 B", "真相是", "拆解一下", "其实你"],
        "persona_anchor": {
            "professional_id": "反套路心理观察家 / 认知拆解者",
            "career_stage": "持续输出中",
            "audience_match": "25-35 岁城市职场，反思关系/自我/认知边界的人",
            "differentiator": "不安抚 / 不给标准答案 / 解构主流叙事",
        },
        "constraints": [
            "不要追热点 / 不写快餐内容",
            "不卖课、不立大师人设",
            "不用「教你 / 救你 / 一定要」俯视语气",
            "不要写常规鸡汤 / N 步搞定型干货",
            "不要安抚用户情绪——保持解构姿态",
        ],
    },
    "healing": {
        "core_tags_template": ["心理疗愈者", "情绪陪伴者"],
        "tone_palette": ["真诚自述", "治愈共情", "温柔"],
        "voice_signature_phrases": ["先接住自己", "允许", "可以的", "慢慢来", "我也曾"],
        "persona_anchor": {
            "professional_id": "心理疗愈者 / 情绪陪伴者",
            "career_stage": "持续输出中",
            "audience_match": "25-30 高敏感女性，需要被看见",
            "differentiator": "让人松弛 / 被接住 / 不评价",
        },
        "constraints": [
            "不卖课、不冒充心理咨询师",
            "不给出明确诊断或治疗建议",
            "保持温柔不说教",
            "不追猎奇热点",
        ],
    },
    "howto": {
        "core_tags_template": ["心理学方法论传播者", "实操派内容创作者"],
        "tone_palette": ["工具实操", "清单化", "可操作"],
        "voice_signature_phrases": ["亲测有效", "保姆级", "N 个步骤", "直接抄作业", "今天就能用"],
        "persona_anchor": {
            "professional_id": "心理学方法论传播者",
            "career_stage": "持续输出中",
            "audience_match": "25-40 找方法的人，要立刻可用",
            "differentiator": "给具体步骤 / 立刻可用 / 实证背书",
        },
        "constraints": [
            "不卖课不带货除非声明",
            "方法必须可验证 / 给出来源",
            "不抄袭其他创作者方法",
        ],
    },
    "academic": {
        "core_tags_template": ["心理学知识传播者"],
        "tone_palette": ["权威", "专业", "引用研究"],
        "voice_signature_phrases": ["依恋理论说", "来访者教我", "我们在做的", "研究显示"],
        "persona_anchor": {
            "professional_id": "心理学知识传播者",
            "career_stage": "持续输出中",
            "audience_match": "25-35 心理学爱好者 / 心理学学生",
            "differentiator": "学术背书 / 概念清晰 / 不夸大",
        },
        "constraints": [
            "引用必须可查证",
            "不替代专业咨询",
            "保持学术严谨",
        ],
    },
    "womens_growth": {
        "core_tags_template": ["30+ 女性 IP", "成长记录者"],
        "tone_palette": ["真诚自述", "过来人视角", "姐姐感"],
        "voice_signature_phrases": ["30+", "向内求", "主体性", "她力量", "我走过的"],
        "persona_anchor": {
            "professional_id": "30+ 女性创业者 IP",
            "career_stage": "创业 N 年（待用户填）",
            "audience_match": "28-40 同行 / 同温层女性",
            "differentiator": "我走过你正在走的路 / 真实经历背书",
        },
        "constraints": [
            "不立完美人设",
            "不评判其他女性选择",
            "不卖虚假女性焦虑",
        ],
    },
    "lifestyle": {
        "core_tags_template": ["生活感记录者"],
        "tone_palette": ["散文式", "日常", "慢节奏"],
        "voice_signature_phrases": ["最近", "有时候", "就这样", "散步的时候"],
        "persona_anchor": {
            "professional_id": "生活感记录者",
            "career_stage": "持续记录中",
            "audience_match": "25-35 文艺女性 / 慢生活同好",
            "differentiator": "真实日常 / 散文式叙述 / 不强情绪钩子",
        },
        "constraints": [
            "不强行制造情绪冲突",
            "不为流量伪造场景",
        ],
    },
}


# ---------- Substratum scoring ----------
def score_substratum(profile: dict, feeds: list) -> dict:
    """Return scores per substratum. Higher = stronger signal."""
    bio = profile.get("desc", "") or ""
    titles = [f.get("title", "") for f in feeds]

    scores = {s: 0 for s in SUBSTRATA}

    # Bio voice (weight 4)
    for sub, words in SUBSTRATUM_BIO_WORDS.items():
        for w in words:
            if w in bio:
                scores[sub] += 4

    # Title patterns (weight 3 per match)
    all_titles = " ".join(titles)
    for sub, patterns in SUBSTRATUM_TITLE_PATTERNS.items():
        for pat in patterns:
            matches = len(re.findall(pat, all_titles))
            scores[sub] += matches * 3

    return scores


# ---------- Voice signature extraction ----------
def extract_voice_phrases(feeds: list, min_freq: int = 3) -> list:
    """Extract recurring phrases from titles (3-8 char Chinese substrings)."""
    titles = [f.get("title", "") for f in feeds if f.get("title")]
    candidates = Counter()
    for t in titles:
        # extract 3-8 char windows
        for n in range(3, 9):
            for i in range(len(t) - n + 1):
                window = t[i : i + n]
                # only if all Chinese
                if all("一" <= c <= "鿿" for c in window):
                    candidates[window] += 1
    common_skip = {
        "为什么", "怎么样", "如何让", "你应该", "我们的",
    }
    return [
        (w, c) for w, c in candidates.most_common(20)
        if c >= min_freq and w not in common_skip
    ]


# ---------- Topic focus extraction ----------
def extract_topic_focus(feeds: list, top_n: int = 8) -> list:
    """Extract top N 2-4 char Chinese topic words from titles."""
    all_titles = " ".join(f.get("title", "") for f in feeds)
    words = re.findall(r"[一-鿿]{2,4}", all_titles)
    skip = {"自己", "我们", "什么", "可以", "为什么", "一个", "这个", "那个", "时候", "因为", "所以", "但是"}
    counter = Counter(w for w in words if w not in skip)
    return [w for w, _ in counter.most_common(top_n)]


# ---------- Form capability ----------
def derive_form_capability(feeds: list) -> dict:
    """Infer form_capability from note_type distribution."""
    types = Counter(f.get("note_type", "?") for f in feeds)
    total = sum(types.values()) or 1
    normal_pct = types.get("normal", 0) / total
    video_pct = types.get("video", 0) / total

    return {
        "图文卡片": normal_pct >= 0.3,
        "图文长文": normal_pct >= 0.3,
        "口播": video_pct >= 0.3,
        "vlog": video_pct >= 0.5,
        "视频": video_pct >= 0.3,
    }


# ---------- Validated viral formula ----------
def extract_validated_viral_formula(feeds: list, median_likes: int) -> Optional[dict]:
    """If account has ≥1 viral note (likes ≥ 5× median), extract its formula."""
    if median_likes <= 0:
        return None
    threshold = max(median_likes * 5, 1000)
    viral_notes = [f for f in feeds if (f.get("likes") or 0) >= threshold]
    if not viral_notes:
        return None

    examples = []
    for n in viral_notes[:5]:
        examples.append(f"{n.get('title', '')} ({n.get('likes', 0)} 赞)")

    return {
        "primary": "[derived from titles — see examples for pattern]",
        "examples": examples,
        "next_steps_after_hook": "double down on this formula in future content",
        "why_it_works": "已被该账号自身数据验证（≥5× median ROI）",
    }


# ---------- Main synthesis ----------
def synthesize_persona(
    profile: dict,
    feeds: list,
    nickname: str,
    fetched_at: str,
    raw_path: str = None,
) -> dict:
    """Build a persona JSON dict from raw xhs profile + feeds.

    Returns the canonical persona schema. Marks needs_user_review=True.
    """
    scores = score_substratum(profile, feeds)
    sorted_subs = sorted(scores.items(), key=lambda x: -x[1])
    top_sub = sorted_subs[0][0]
    top_score = sorted_subs[0][1]
    second_score = sorted_subs[1][1] if len(sorted_subs) > 1 else 0

    # Edge case: no signal
    if top_score == 0:
        substratum = "cognitive"  # default fallback
        confidence_note = "WEAK SIGNAL — bio + titles too sparse. Defaulting to cognitive substratum. Strongly recommend manual editing."
    elif top_score - second_score < 5:
        substratum = top_sub
        confidence_note = (
            f"BORDERLINE — top 2 substrata too close ({sorted_subs[0]} vs {sorted_subs[1]}). "
            f"Defaulted to top scorer; consider manual review."
        )
    else:
        substratum = top_sub
        confidence_note = f"Clear signal — {top_sub} (score {top_score})"

    defaults = SUBSTRATUM_DEFAULTS[substratum]

    # Bio self-tags (split bio by separators)
    bio = profile.get("desc", "") or ""
    self_tags = [t.strip() for t in re.split(r"[|/\n、]", bio) if t.strip()]

    # Feed-derived
    voice_phrases = [p for p, _ in extract_voice_phrases(feeds)]
    if not voice_phrases:
        voice_phrases = defaults["voice_signature_phrases"][:5]
    topic_focus = extract_topic_focus(feeds)
    form_cap = derive_form_capability(feeds)

    # Stats for validated formula detection
    likes = [f.get("likes", 0) for f in feeds if f.get("likes")]
    median_likes = (
        sorted(likes)[len(likes) // 2] if likes else 0
    )
    validated_formula = extract_validated_viral_formula(feeds, median_likes)

    # Synthesize
    persona = {
        "_meta": {
            "version": "0.1-auto",
            "synthesized_at": fetched_at[:10],
            "source": f"xhs auto-extracted from user_id {profile.get('user_id', '?')}",
            "lens_version": "xhs_stratum_guide v1",
            "needs_user_review": True,
            "raw_data": raw_path,
        },
        "core_tags": defaults["core_tags_template"][:],
        "secondary_tags": [],
        "story_assets": [],
        "story_assets_note": (
            "If account is anonymized or bio is short, story_assets may be empty. "
            "Please add 1-2 personal experience anchors (e.g., career story, formative experience) to improve voice depth."
        ),
        "topic_focus": topic_focus,
        "tone_palette": defaults["tone_palette"][:],
        "voice_signature_phrases": voice_phrases[:8],
        "persona_anchors_for_rewrite": dict(defaults["persona_anchor"]),
        "form_capability": form_cap,
        "constraints": defaults["constraints"][:],
        "validated_viral_formula": validated_formula,
        "_synthesis_notes": (
            f"## Sub-stratum classification: **{substratum}**\n\n"
            f"### Vote scores\n"
            + "\n".join(f"- {s}: {sc}" for s, sc in sorted_subs)
            + f"\n\n### Confidence\n{confidence_note}\n\n"
            f"### Self tags from bio\n{self_tags}\n\n"
            f"### Form distribution\n{form_cap}\n"
        ),
    }
    return persona


def render_persona_doc(persona: dict, nickname: str) -> str:
    """Render persona JSON into human-readable Markdown for the editable Feishu docx."""
    md = []
    md.append(f"# [人设档案] {nickname}_{persona['_meta']['synthesized_at']}\n\n")
    md.append(
        "> 这份档案是 xhs-viral-decoder 工作流的**人设根**——爆款改写引擎要套这些标签生成符合调性的标题。\n"
        "> **下次跑工作流前请检查更新**。\n\n"
    )

    md.append("## 一、核心人设标签\n\n")
    for t in persona["core_tags"]:
        md.append(f"- {t}\n")

    md.append("\n## 二、辅助标签\n\n")
    for t in persona.get("secondary_tags", []) or ["(待补充)"]:
        md.append(f"- {t}\n")

    md.append("\n## 三、可挪用的故事素材\n\n")
    if persona.get("story_assets"):
        for s in persona["story_assets"]:
            md.append(f"- {s}\n")
    else:
        md.append(f"_(空 — {persona.get('story_assets_note', '')})_\n")

    md.append("\n## 四、主话题清单\n\n")
    md.append(" / ".join(persona.get("topic_focus", [])))

    md.append("\n\n## 五、语气调色板\n\n")
    for t in persona.get("tone_palette", []):
        md.append(f"- {t}\n")

    md.append("\n## 六、Voice 标志短语\n\n")
    for p in persona.get("voice_signature_phrases", []):
        md.append(f"- 「{p}」\n")

    md.append("\n## 七、人设锚点（rewrite 用）\n\n")
    for k, v in persona.get("persona_anchors_for_rewrite", {}).items():
        md.append(f"- **{k}**: {v}\n")

    md.append("\n## 八、内容形式能力\n\n")
    for k, v in persona.get("form_capability", {}).items():
        md.append(f"- {k}: {'✓' if v else '✗'}\n")

    md.append("\n## 九、改写硬约束（红线）\n\n")
    for c in persona.get("constraints", []):
        md.append(f"- {c}\n")

    if persona.get("validated_viral_formula"):
        md.append("\n## 十、已验证爆款公式\n\n")
        vf = persona["validated_viral_formula"]
        md.append(f"**主要公式**：{vf.get('primary', '')}\n\n")
        md.append("**已验证示例**：\n")
        for ex in vf.get("examples", []):
            md.append(f"- {ex}\n")

    md.append("\n## 十一、Synthesis Notes（lens 判定依据）\n\n")
    md.append(persona.get("_synthesis_notes", ""))

    md.append("\n---\n\n## 怎么更新这份档案\n\n")
    md.append(
        "如果改写结果反复出现「不像我」的标题 → 增补 voice_signature_phrases；\n"
        "如果新加身份信号 → 改 core_tags / story_assets；\n"
        "改完之后跟 Claude 说「重跑 rewrite」即可，不需要重新抓数据。\n"
    )

    return "".join(md)
