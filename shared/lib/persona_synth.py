"""Auto-synthesize a creator persona from xhs profile + recent feeds.

v0.2 — niche-agnostic: auto-detects the account's actual niche (pet, travel,
music, psychology, etc.) and only applies the 6-stratum psychology lens when the
account IS in the psychology niche. For all other niches, synthesizes a generic
but accurate persona from actual bio + title + content signals.

See shared/reference/xhs_stratum_guide.md for the psychology lens design.
"""
import json
import re
from collections import Counter
from typing import Optional


# ═══════════════════════════════════════════════════════════
# Niche auto-detection (NEW in v0.2)
# ═══════════════════════════════════════════════════════════

NICHE_KEYWORDS = {
    "宠物": {
        "bio": ["柴犬", "狗", "猫", "宠物", "铲屎官", "毛孩子", "猫咪", "汪", "喵", "萌宠",
                "布偶", "金毛", "泰迪", "边牧", "柯基", "中华田园", "流浪猫", "领养"],
        "title": [r"柴犬", r"狗[子狗]?", r"猫[咪猫]?", r"宠物", r"铲屎", r"毛孩",
                  r"汪星人", r"喵星人", r"遛[狗猫]", r"狗粮", r"猫粮"],
    },
    "美食": {
        "bio": ["美食", "吃货", "烘焙", "烹饪", "厨房", "咖啡", "甜品", "料理", "菜谱"],
        "title": [r"美食", r"好吃", r"食谱", r"做法", r"烘焙", r"咖啡", r"甜品", r"餐厅"],
    },
    "旅行": {
        "bio": ["旅行", "旅游", "环球", "背包", "自驾", "探店", "city walk", "citywalk"],
        "title": [r"旅[行游]", r"自驾", r"攻略", r"打卡", r"机票", r"民宿", r"酒店"],
    },
    "穿搭": {
        "bio": ["穿搭", "时尚", "OOTD", "搭配", "潮流", "衣橱"],
        "title": [r"穿搭", r"OOTD", r"搭配", r"显[瘦白高]", r"氛围感"],
    },
    "美妆": {
        "bio": ["美妆", "护肤", "化妆", "成分", "彩妆", "底妆", "口红", "防晒"],
        "title": [r"美妆", r"护肤", r"化妆", r"成分", r"防晒", r"口红", r"眼影"],
    },
    "健身": {
        "bio": ["健身", "运动", "瑜伽", "跑步", "减脂", "增肌", "体态"],
        "title": [r"健身", r"减[脂肥]", r"增肌", r"瑜伽", r"跑步", r"体态"],
    },
    "母婴": {
        "bio": ["妈妈", "宝宝", "育儿", "母婴", "孕", "带娃", "亲子"],
        "title": [r"宝宝", r"育儿", r"母婴", r"辅食", r"带娃", r"亲子"],
    },
    "音乐": {
        "bio": ["音乐", "乐队", "live", "演唱会", "爵士", "吉他", "独立音乐"],
        "title": [r"演唱会", r"[Ll]ive", r"乐队", r"爵士", r"音乐节", r"吉他"],
    },
    "科技": {
        "bio": ["科技", "数码", "AI", "编程", "程序员", "产品经理", "互联网"],
        "title": [r"AI", r"数码", r"编程", r"科技", r"App", r"效率"],
    },
    "心理": {
        "bio": ["心理", "疗愈", "治愈", "情绪", "内耗", "认知", "拆解", "咨询师",
                "原生家庭", "依恋", "自我"],
        "title": [r"心理", r"疗愈", r"治愈", r"情绪", r"内耗", r"认知", r"拆解",
                  r"原生家庭", r"依恋", r"自我"],
    },
    "家居": {
        "bio": ["家居", "装修", "收纳", "好物", "改造", "租房"],
        "title": [r"家居", r"装修", r"收纳", r"好物", r"改造"],
    },
    "摄影": {
        "bio": ["摄影", "胶卷", "胶片", "拍照", "相机", "写真", "人像"],
        "title": [r"摄影", r"胶[卷片]", r"拍照", r"相机", r"柯达", r"富士"],
    },
    "职场": {
        "bio": ["职场", "求职", "面试", "简历", "跳槽", "外企", "副业"],
        "title": [r"职场", r"面试", r"简历", r"跳槽", r"外企", r"公司", r"副业"],
    },
}


def detect_niche(profile: dict, feeds: list) -> tuple:
    """Auto-detect account niche from bio + titles.

    Returns:
        (primary_niche: str, scores: dict, is_mixed: bool)
        primary_niche = highest scoring niche, or "综合" if mixed/unclear.
        is_mixed = True if top 2 niches are close (within 30% of each other).
    """
    bio = profile.get("desc", "") or ""
    titles = [f.get("title", "") for f in feeds if f.get("title")]
    all_titles = " ".join(titles)

    scores = {}
    for niche, kw in NICHE_KEYWORDS.items():
        score = 0
        # Bio keywords (weight 5 — bio is the strongest self-declaration signal)
        for w in kw["bio"]:
            if w.lower() in bio.lower():
                score += 5
        # Title pattern matches (weight 2 per match)
        for pat in kw["title"]:
            matches = len(re.findall(pat, all_titles, re.IGNORECASE))
            score += matches * 2
        scores[niche] = score

    sorted_niches = sorted(scores.items(), key=lambda x: -x[1])
    top_niche, top_score = sorted_niches[0]
    second_score = sorted_niches[1][1] if len(sorted_niches) > 1 else 0

    if top_score == 0:
        return "综合", scores, True

    is_mixed = (second_score > 0 and second_score >= top_score * 0.7)
    return top_niche, scores, is_mixed


# ═══════════════════════════════════════════════════════════
# 6 sub-strata (心理赛道 only — kept for backwards compat)
# ═══════════════════════════════════════════════════════════

SUBSTRATA = [
    "cognitive",      # 认知派 / 反共识
    "healing",        # 治愈共情派
    "howto",          # 干货实操派
    "academic",       # 心理学权威派
    "womens_growth",  # 女性成长派
    "lifestyle",      # 生活感叙事派
]


# ---------- Bio voice keywords per substratum (weight: x4) ----------
SUBSTRATUM_BIO_WORDS = {
    "cognitive": ["拆解", "逻辑", "真相", "不合时宜", "深度", "认知", "解构", "反共识", "探索"],
    "healing": ["治愈", "疗愈", "陪伴", "温柔", "慢慢来", "接住", "允许", "安抚"],
    "howto": ["步骤", "方法", "教你", "亲测", "保姆级", "实操", "技巧", "干货"],
    "academic": ["心理学", "依恋", "原生家庭", "依恋理论", "咨询师", "来访者", "治疗", "精神分析"],
    "womens_growth": ["30+", "创业", "主体性", "向内求", "她", "女性", "成长", "蜕变", "独立"],
    "lifestyle": ["日常", "vlog", "记录", "散步", "生活", "早晨", "周末"],
}


# ---------- Title pattern markers per substratum (weight: x3 per match) ----------
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


# ═══════════════════════════════════════════════════════════
# Niche-agnostic defaults (NEW in v0.2)
# ═══════════════════════════════════════════════════════════

NICHE_TONE_DEFAULTS = {
    "宠物": ["幽默", "生活化", "温暖", "萌系"],
    "美食": ["真诚分享", "生活化", "食欲感"],
    "旅行": ["随性", "探索", "真实记录"],
    "穿搭": ["自信", "生活化", "氛围感"],
    "美妆": ["真诚分享", "干货", "对比测评"],
    "健身": ["激励", "实操", "真实记录"],
    "母婴": ["真诚", "温暖", "过来人视角"],
    "音乐": ["热烈", "感性", "分享型"],
    "科技": ["理性", "干货", "体验分享"],
    "心理": ["冷静", "解构", "真诚"],
    "家居": ["实用", "审美", "分享型"],
    "摄影": ["审美", "感性", "记录"],
    "职场": ["真实", "干货", "过来人视角"],
    "综合": ["真实", "生活化", "随性"],
}

NICHE_CONSTRAINT_DEFAULTS = {
    "宠物": [
        "不编造宠物行为做流量钩子",
        "不推荐未验证的宠物产品",
        "保持真实的宠物日常，不过度拟人化",
    ],
    "美食": [
        "不虚假推荐 / 恰饭不声明",
        "食谱数据要真实可复现",
    ],
    "旅行": [
        "不虚假滤镜美化 / 景点要真实",
        "攻略信息要准确可用",
    ],
    "音乐": [
        "不蹭乐队/艺人负面新闻做流量",
        "尊重版权，标注来源",
    ],
    "摄影": [
        "标注器材和后期参数",
        "不盗图 / 不冒充原创",
    ],
    "综合": [
        "保持真实，不为流量伪造内容",
        "推荐产品要真实体验过",
    ],
}


# ═══════════════════════════════════════════════════════════
# Substratum scoring (psychology niche only)
# ═══════════════════════════════════════════════════════════

def score_substratum(profile: dict, feeds: list) -> dict:
    """Return scores per substratum. Higher = stronger signal.

    NOTE: only meaningful for 心理赛道 accounts. For other niches,
    use detect_niche() instead.
    """
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


# ═══════════════════════════════════════════════════════════
# Signal extraction helpers
# ═══════════════════════════════════════════════════════════

def extract_bio_self_tags(bio: str) -> list:
    """Extract self-tags from bio (split by common separators like | / newline emoji)."""
    if not bio:
        return []
    # Split by newline, |, /, or emoji-as-separator patterns
    lines = re.split(r"[\n|/、]", bio)
    tags = []
    for line in lines:
        cleaned = line.strip()
        # Remove leading emoji
        cleaned_no_emoji = re.sub(r"^[\U0001F300-\U0001FAD6\U00002702-\U000027B0\U0000FE00-\U0000FE0F\U0000200D]+\s*", "", cleaned)
        if cleaned_no_emoji and len(cleaned_no_emoji) >= 2:
            tags.append(cleaned_no_emoji)
        elif cleaned and len(cleaned) >= 2:
            tags.append(cleaned)
    return tags


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
                if all("\u4e00" <= c <= "\u9fff" for c in window):
                    candidates[window] += 1
    common_skip = {
        "为什么", "怎么样", "如何让", "你应该", "我们的",
    }
    return [
        (w, c) for w, c in candidates.most_common(20)
        if c >= min_freq and w not in common_skip
    ]


def extract_topic_focus(feeds: list, top_n: int = 8) -> list:
    """Extract top N meaningful topic words from titles.

    v0.2: splits on common Chinese particles (的/了/在/是/和/...) before
    extracting 2-4 char n-grams, to avoid cross-particle garbage like
    "延迟的首" or "尔爵士节".
    """
    titles = [f.get("title", "") for f in feeds if f.get("title")]
    # Split each title by common particles and punctuation
    particle_pattern = r"[的了在是和与有也都把被让给从到过得着不会能要就这那我你他她它们]"
    segments = []
    for t in titles:
        # First strip non-Chinese chars (emoji, english, punctuation)
        chinese_only = re.sub(r"[^\u4e00-\u9fff]+", " ", t)
        # Split on particles
        parts = re.split(particle_pattern, chinese_only)
        segments.extend(p.strip() for p in parts if p.strip())

    # Extract 2-4 char Chinese words from segments
    words = []
    for seg in segments:
        words.extend(re.findall(r"[\u4e00-\u9fff]{2,4}", seg))

    # Expanded skip list
    skip = {
        "自己", "什么", "可以", "为什", "一个", "这个", "那个",
        "时候", "因为", "所以", "但是", "还是", "就是", "不是", "这样",
        "怎么", "如何", "一下", "今天", "明天", "昨天", "突然", "终于",
        "居然", "好的", "没有", "已经", "真的", "回来", "出来",
        "上面", "下面", "里面", "外面", "后面", "前面", "上海",
        "抽象", "真的", "居然",
    }
    counter = Counter(w for w in words if w not in skip and len(w) >= 2)
    return [w for w, _ in counter.most_common(top_n)]


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


def extract_validated_viral_formula(feeds: list, median_likes: int) -> Optional[dict]:
    """If account has >=1 viral note (likes >= 5x median), extract its formula."""
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
        "why_it_works": "已被该账号自身数据验证（>=5x median ROI）",
    }


def _detect_content_themes(feeds: list) -> list:
    """Analyze feeds to detect 3-5 major content themes from titles."""
    titles = [f.get("title", "") for f in feeds if f.get("title")]
    # Simple theme detection via keyword clustering
    theme_keywords = {
        "宠物日常": ["柴犬", "狗", "猫", "宠物", "毛", "汪", "喵", "遛", "带病"],
        "旅行探索": ["旅行", "自驾", "清迈", "首尔", "东京", "澳洲", "新疆", "济州", "台北", "公路"],
        "演唱会/现场": ["演唱会", "Live", "live", "LIVE", "乐队", "爵士", "现场", "后遗症", "JANNABI", "Jannabi", "Apink"],
        "咖啡/美食": ["咖啡", "甜品", "餐厅", "吧", "清吧", "酒吧", "买菜"],
        "摄影/视觉": ["胶卷", "胶片", "像素", "照片", "拍", "柯达", "Photo"],
        "职场/生活": ["外企", "团队", "公司", "上海", "日常", "生活"],
    }
    theme_scores = {}
    all_text = " ".join(titles)
    for theme, kws in theme_keywords.items():
        score = sum(1 for kw in kws if kw in all_text)
        if score > 0:
            theme_scores[theme] = score
    return sorted(theme_scores, key=theme_scores.get, reverse=True)[:5]


# ═══════════════════════════════════════════════════════════
# Main synthesis — niche-agnostic (v0.2)
# ═══════════════════════════════════════════════════════════

def synthesize_persona(
    profile: dict,
    feeds: list,
    nickname: str,
    fetched_at: str,
    raw_path: str = None,
) -> dict:
    """Build a persona JSON dict from raw xhs profile + feeds.

    v0.2: niche-agnostic. Detects actual niche first; only applies 6-stratum
    psychology lens when niche == 心理. For all other niches, synthesizes from
    actual bio self-tags + content signals.
    """
    # Step 1: Detect niche
    primary_niche, niche_scores, is_mixed = detect_niche(profile, feeds)

    # Step 2: Extract real bio self-tags (always — these are ground truth)
    bio = profile.get("desc", "") or ""
    real_self_tags = extract_bio_self_tags(bio)

    # Step 3: Branch based on niche
    if primary_niche == "心理":
        # Psychology niche — use existing 6-stratum lens
        return _synthesize_psychology(
            profile, feeds, nickname, fetched_at, raw_path,
            real_self_tags, niche_scores,
        )
    else:
        # Any other niche — use niche-agnostic synthesis
        return _synthesize_generic(
            profile, feeds, nickname, fetched_at, raw_path,
            primary_niche, niche_scores, is_mixed, real_self_tags,
        )


def _synthesize_psychology(
    profile, feeds, nickname, fetched_at, raw_path,
    real_self_tags, niche_scores,
) -> dict:
    """Original 6-stratum synthesis for psychology niche accounts."""
    scores = score_substratum(profile, feeds)
    sorted_subs = sorted(scores.items(), key=lambda x: -x[1])
    top_sub = sorted_subs[0][0]
    top_score = sorted_subs[0][1]
    second_score = sorted_subs[1][1] if len(sorted_subs) > 1 else 0

    if top_score == 0:
        substratum = "cognitive"
        confidence_note = "WEAK SIGNAL — bio + titles too sparse. Defaulting to cognitive substratum."
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

    voice_phrases = [p for p, _ in extract_voice_phrases(feeds)]
    if not voice_phrases:
        voice_phrases = defaults["voice_signature_phrases"][:5]
    topic_focus = extract_topic_focus(feeds)
    form_cap = derive_form_capability(feeds)

    likes = [f.get("likes", 0) for f in feeds if f.get("likes")]
    median_likes = sorted(likes)[len(likes) // 2] if likes else 0
    validated_formula = extract_validated_viral_formula(feeds, median_likes)

    # Use real self-tags as core_tags if they exist; else fallback to template
    core_tags = real_self_tags if real_self_tags else defaults["core_tags_template"][:]

    persona = {
        "_meta": {
            "version": "0.2-auto",
            "synthesized_at": fetched_at[:10],
            "source": f"xhs auto-extracted from user_id {profile.get('user_id', '?')}",
            "lens_version": "xhs_stratum_guide v1 (心理赛道 6-stratum)",
            "detected_niche": "心理",
            "needs_user_review": True,
            "raw_data": raw_path,
        },
        "core_tags": core_tags,
        "secondary_tags": [],
        "story_assets": [],
        "story_assets_note": (
            "If account is anonymized or bio is short, story_assets may be empty. "
            "Please add 1-2 personal experience anchors to improve voice depth."
        ),
        "topic_focus": topic_focus,
        "tone_palette": defaults["tone_palette"][:],
        "voice_signature_phrases": voice_phrases[:8],
        "persona_anchors_for_rewrite": dict(defaults["persona_anchor"]),
        "form_capability": form_cap,
        "constraints": defaults["constraints"][:],
        "validated_viral_formula": validated_formula,
        "_synthesis_notes": (
            f"## Detected niche: 心理\n\n"
            f"## Sub-stratum classification: **{substratum}**\n\n"
            f"### Vote scores\n"
            + "\n".join(f"- {s}: {sc}" for s, sc in sorted_subs)
            + f"\n\n### Confidence\n{confidence_note}\n\n"
            f"### Self tags from bio\n{real_self_tags}\n\n"
            f"### Form distribution\n{form_cap}\n"
        ),
    }
    return persona


def _synthesize_generic(
    profile, feeds, nickname, fetched_at, raw_path,
    primary_niche, niche_scores, is_mixed, real_self_tags,
) -> dict:
    """Niche-agnostic synthesis for non-psychology accounts.

    Uses actual bio self-tags, detected content themes, and niche-appropriate
    defaults instead of psychology-specific templates.
    """
    # Core tags: use real bio self-tags (the user's own self-declaration)
    core_tags = real_self_tags if real_self_tags else [f"{primary_niche}创作者"]

    # Detect secondary niches for mixed accounts
    sorted_niches = sorted(niche_scores.items(), key=lambda x: -x[1])
    active_niches = [n for n, s in sorted_niches if s > 0]
    secondary_tags = active_niches[:3] if is_mixed else [primary_niche]

    # Content themes from actual titles
    content_themes = _detect_content_themes(feeds)

    # Topic focus from real titles (improved extraction)
    topic_focus = extract_topic_focus(feeds)
    # Supplement with content themes if topic_focus is sparse
    if len(topic_focus) < 5 and content_themes:
        for theme in content_themes:
            theme_short = theme.split("/")[0]  # "演唱会/现场" → "演唱会"
            if theme_short not in topic_focus:
                topic_focus.append(theme_short)

    # Tone palette: niche-specific defaults
    tone = NICHE_TONE_DEFAULTS.get(primary_niche, NICHE_TONE_DEFAULTS["综合"])

    # Voice phrases from actual titles
    voice_phrases = [p for p, _ in extract_voice_phrases(feeds, min_freq=2)]
    if not voice_phrases:
        voice_phrases = ["(内容多元，无固定口头禅 — 建议手动补充)"]

    # Form capability
    form_cap = derive_form_capability(feeds)

    # Stats
    likes = [f.get("likes", 0) for f in feeds if f.get("likes")]
    median_likes = sorted(likes)[len(likes) // 2] if likes else 0
    validated_formula = extract_validated_viral_formula(feeds, median_likes)

    # Persona anchors — derived from actual account, not templates
    follower_count = profile.get("follower_count", 0)
    total_engagement = profile.get("total_engagement", 0)
    niche_label = " + ".join(active_niches[:3]) if is_mixed else primary_niche

    persona_anchor = {
        "professional_id": " / ".join(core_tags[:2]),
        "career_stage": f"活跃创作中 ({len(feeds)} 笔记 / {follower_count} 粉 / {total_engagement} 获赞与收藏)",
        "audience_match": f"{niche_label}爱好者 / 同好社区",
        "differentiator": "（待用户补充 — 自动抓取的数据不足以推断差异化定位）",
    }

    # Constraints — niche defaults, not psychology defaults
    constraints = NICHE_CONSTRAINT_DEFAULTS.get(
        primary_niche,
        NICHE_CONSTRAINT_DEFAULTS["综合"],
    )

    niche_details = "\n".join(f"- {n}: {s}" for n, s in sorted_niches if s > 0)

    persona = {
        "_meta": {
            "version": "0.2-auto",
            "synthesized_at": fetched_at[:10],
            "source": f"xhs auto-extracted from user_id {profile.get('user_id', '?')}",
            "lens_version": "niche-agnostic v0.2",
            "detected_niche": primary_niche,
            "is_mixed_niche": is_mixed,
            "needs_user_review": True,
            "raw_data": raw_path,
        },
        "core_tags": core_tags,
        "secondary_tags": secondary_tags,
        "content_themes": content_themes,
        "story_assets": [],
        "story_assets_note": (
            "story_assets 需要用户手动补充。建议添加 1-2 个个人经历锚点 "
            "（如：养柴犬 N 年经历 / 在 XX 公司工作 / 某次旅行转折点等）。"
        ),
        "topic_focus": topic_focus[:8],
        "tone_palette": tone,
        "voice_signature_phrases": voice_phrases[:8],
        "persona_anchors_for_rewrite": persona_anchor,
        "form_capability": form_cap,
        "constraints": constraints,
        "validated_viral_formula": validated_formula,
        "_synthesis_notes": (
            f"## Detected niche: **{primary_niche}**"
            + (f" (mixed: {', '.join(active_niches[:3])})" if is_mixed else "")
            + f"\n\n### Niche scores\n{niche_details}\n\n"
            f"### Bio self-tags (used as core_tags)\n{real_self_tags}\n\n"
            f"### Content themes\n{content_themes}\n\n"
            f"### Form distribution\n{form_cap}\n\n"
            f"### Note: niche != 心理, skipped 6-stratum psychology lens.\n"
            f"Used niche-agnostic synthesis with actual bio + title signals.\n"
        ),
    }
    return persona


def render_persona_doc(persona: dict, nickname: str) -> str:
    """Render persona JSON into human-readable Markdown for the editable Feishu docx."""
    md = []
    niche = persona.get("_meta", {}).get("detected_niche", "未知")
    md.append(f"# [人设档案] {nickname}_{persona['_meta']['synthesized_at']}\n\n")
    md.append(f"> **赛道**: {niche}\n")
    md.append(
        "> 这份档案是 xhs-viral-decoder 工作流的**人设根**——爆款改写引擎要套这些标签生成符合调性的标题。\n"
        "> **下次跑工作流前请检查更新**。\n\n"
    )

    md.append("## 一、核心人设标签\n\n")
    for t in persona["core_tags"]:
        md.append(f"- {t}\n")

    md.append("\n## 二、辅助标签 / 赛道标签\n\n")
    for t in persona.get("secondary_tags", []) or ["(待补充)"]:
        md.append(f"- {t}\n")

    if persona.get("content_themes"):
        md.append("\n## 二·五、内容主题分布\n\n")
        for t in persona["content_themes"]:
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

    md.append("\n## 十一、Synthesis Notes（判定依据）\n\n")
    md.append(persona.get("_synthesis_notes", ""))

    md.append("\n---\n\n## 怎么更新这份档案\n\n")
    md.append(
        "如果改写结果反复出现「不像我」的标题 → 增补 voice_signature_phrases；\n"
        "如果新加身份信号 → 改 core_tags / story_assets；\n"
        "改完之后跟 Claude 说「重跑 rewrite」即可，不需要重新抓数据。\n"
    )

    return "".join(md)
