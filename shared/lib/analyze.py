"""Data analysis: TOP 30 ranking, title formulas, pain quotes, hot topics, stats.

Refactored from viral-decode/analysis/analyze.py — de-personalized + parameterized.
"""
import json
import re
import statistics
from collections import Counter, defaultdict
from typing import Optional


# ---------- Title formula classifier (P1-P10) ----------
def title_pattern(title: str) -> str:
    """Classify a Xiaohongshu title into one of P1-P10 patterns.

    See shared/reference/title_formulas.md for full pattern definitions.
    """
    if not title:
        return "无标题"
    if title.count("，") >= 2:
        parts = [p for p in re.split(r"[，。！]", title) if p.strip()]
        if len(parts) >= 3 and len(set(parts[:3])) == 1:
            return "P1·重复强调式（X，X，X）"
    if re.search(r"^\d+[个种条招]", title):
        return "P2·数字清单式（N个/N招）"
    if any(w in title for w in ["如何", "怎么", "怎样"]):
        return "P3·How-to 提问式"
    if any(w in title for w in ["治愈", "被治愈", "拯救了我", "救了我"]):
        return "P4·治愈叙事式"
    if any(w in title for w in ["请", "一定要", "必须", "千万", "永远不要", "不要"]):
        return "P5·祈使/告诫式"
    if "?" in title or "？" in title:
        return "P6·开放疑问式"
    if any(w in title for w in ["顿悟", "突然", "终于", "原来"]):
        return "P7·顿悟瞬间式"
    if re.search(r"[A-Za-z]{2,}", title):
        return "P8·中英混排/概念词式"
    if any(w in title for w in ["我", "自己"]):
        return "P9·第一人称自述式"
    return "P10·其他"


# ---------- Opinion classifier (lightweight rule) ----------
DEFAULT_CATEGORIES = [
    ("自我接纳", ["接纳", "允许", "不完美", "自己", "真实的我", "自我"]),
    ("情绪调节方法", ["方法", "技巧", "步骤", "练习", "训练", "做法", "建议", "如何"]),
    ("关系/课题分离", ["他人", "关系", "课题分离", "讨好", "界限", "边界", "别人怎么"]),
    ("能量/状态低谷", ["能量", "无力", "崩溃", "抑郁", "丧", "emo", "低谷", "黑暗", "想哭"]),
    ("反内耗/思维改写", ["内耗", "钝感", "想开", "中计", "思维", "认知", "反刍", "焦虑"]),
    ("疗愈叙事/治愈感", ["治愈", "疗愈", "温柔", "被治愈", "感动", "暖", "拯救"]),
    ("人生哲学/金句", ["哲学", "活着", "人生", "意义", "命运", "尼采", "顿悟"]),
]


def classify_opinion(title: str, excerpt: str = "", categories=None) -> str:
    text = (title or "") + " " + (excerpt or "")[:200]
    cats = categories or DEFAULT_CATEGORIES
    for cat, kws in cats:
        if any(k in text for k in kws):
            return cat
    return "其他"


# ---------- Pain point bucket classifier ----------
DEFAULT_PAIN_BUCKETS = [
    ("不被理解 / 孤独", ["没人懂", "理解", "孤独", "一个人", "陪我", "倾诉", "说话"]),
    ("反复内耗 / 想太多", ["内耗", "想太多", "反刍", "纠结", "犹豫", "焦虑"]),
    ("自我否定 / 配不上", ["配不上", "不配", "自卑", "没用", "差劲", "废物", "没能力"]),
    ("关系受伤 / 情感", ["出轨", "分手", "前任", "婆婆", "妈妈", "爸爸", "老公", "老婆", "男朋友", "女朋友", "前夫"]),
    ("工作/经济压力", ["工作", "上班", "失业", "钱", "房贷", "穷", "辞职", "卷", "加班"]),
    ("无力感 / 想躺平", ["躺平", "没动力", "起不来", "无力", "崩溃", "撑不下去", "想死", "活着"]),
    ("情绪化 / 易哭", ["想哭", "眼泪", "破防", "瞬间", "戳中", "看哭"]),
    ("被治愈 / 共鸣", ["治愈", "救了我", "刚好", "需要", "及时", "感谢", "谢谢"]),
]


def classify_pain(text: str, buckets=None) -> Optional[str]:
    bs = buckets or DEFAULT_PAIN_BUCKETS
    for label, kws in bs:
        if any(k in text for k in kws):
            return label
    return None


# ---------- Numeric helpers ----------
def safe_int(v) -> int:
    try:
        return int(v) if v else 0
    except (TypeError, ValueError):
        return 0


# ---------- Main analysis ----------
def build_analysis(
    notes: list,
    keywords: list = None,
    top_n: int = 30,
    low_fan_threshold: tuple = (50000, 10000),  # (max_fans, min_likes)
    pain_buckets=None,
    categories=None,
) -> dict:
    """Run full analysis on a list of note dicts.

    Each note dict must have:
      - feed_id, title, note_type, url, likes, collects, comments_count, follower_count
      - top_comments (optional, list of {content, likeCount, ipLocation})
      - content_excerpt (optional)
      - keywords_matched (optional, list)
      - publish_ts (optional, ms epoch)

    Returns the canonical analysis dict consumed by report.py.
    """
    # Annotate
    for n in notes:
        n["likes_n"] = safe_int(n.get("likes"))
        n["collects_n"] = safe_int(n.get("collects"))
        n["comments_n"] = safe_int(n.get("comments_count"))
        n["fans_n"] = safe_int(n.get("follower_count"))
        n["category"] = classify_opinion(
            n.get("title", ""), n.get("content_excerpt", ""), categories
        )
        n["pattern"] = title_pattern(n.get("title", ""))

    ranked = sorted(notes, key=lambda x: x["likes_n"], reverse=True)
    top = ranked[:top_n]

    # Pattern distributions
    pattern_counter_all = Counter(n["pattern"] for n in notes)
    pattern_counter_top = Counter(n["pattern"] for n in top)

    # Note type distribution
    type_counter = Counter(n.get("note_type", "unknown") for n in notes)

    # Low-fan viral
    max_fans, min_likes = low_fan_threshold
    low_fan_viral = [
        n for n in notes if n["fans_n"] < max_fans and n["likes_n"] > min_likes
    ]
    low_fan_viral.sort(
        key=lambda x: x["likes_n"] / max(x["fans_n"], 1), reverse=True
    )

    # Pain quotes
    pain_quotes = defaultdict(list)
    for n in notes:
        for c in (n.get("top_comments") or []):
            content = (c.get("content") or "").strip()
            if not content or len(content) < 10:
                continue
            label = classify_pain(content, pain_buckets)
            if label:
                pain_quotes[label].append({
                    "quote": content,
                    "likes": safe_int(c.get("likeCount")),
                    "ip": c.get("ipLocation", ""),
                    "from_note": n.get("title", ""),
                    "note_likes": n["likes_n"],
                })
    pain_top = {}
    for b, lst in pain_quotes.items():
        lst.sort(key=lambda x: x["likes"], reverse=True)
        pain_top[b] = lst[:4]

    # Hot topic words
    all_titles = " ".join(n.get("title", "") for n in notes)
    title_words = re.findall(r"[一-鿿]{2,4}", all_titles)
    skip_words = {
        "自己", "我们", "什么", "可以", "为什么", "一个", "这个", "那个",
        "时候", "因为", "所以", "但是", "已经", "现在",
    }
    word_counter = Counter(w for w in title_words if w not in skip_words)
    hot_topics = word_counter.most_common(20)

    # Stats
    likes_list = [n["likes_n"] for n in notes if n["likes_n"] > 0]
    collects_list = [n["collects_n"] for n in notes if n["collects_n"] > 0]
    comments_list = [n["comments_n"] for n in notes if n["comments_n"] > 0]

    stats = {
        "total_notes": len(notes),
        "median_likes": int(statistics.median(likes_list)) if likes_list else 0,
        "mean_likes": int(statistics.mean(likes_list)) if likes_list else 0,
        "max_likes": max(likes_list) if likes_list else 0,
        "median_collects": int(statistics.median(collects_list)) if collects_list else 0,
        "median_comments": int(statistics.median(comments_list)) if comments_list else 0,
        "low_fan_viral_count": len(low_fan_viral),
        "low_fan_viral_pct": round(100 * len(low_fan_viral) / max(len(notes), 1), 1),
        "type_distribution": dict(type_counter),
        "pattern_distribution_all": dict(pattern_counter_all),
        "pattern_distribution_top": dict(pattern_counter_top),
        "category_distribution_top": dict(Counter(n["category"] for n in top)),
        "collect_like_ratio_median": round(
            statistics.median(
                [n["collects_n"] / n["likes_n"] for n in notes if n["likes_n"] > 0]
            ), 3,
        ) if likes_list else 0,
        "comment_like_ratio_median": round(
            statistics.median(
                [n["comments_n"] / n["likes_n"] for n in notes if n["likes_n"] > 0]
            ), 4,
        ) if likes_list else 0,
    }

    return {
        "_meta": {
            "keywords": keywords or [],
            "total_unique_notes": len(notes),
            "top_n": top_n,
            "low_fan_definition": f"follower_count<{max_fans} AND likes>{min_likes}",
        },
        "top": [
            {
                "rank": i + 1,
                "title": n.get("title", ""),
                "likes": n["likes_n"],
                "collects": n["collects_n"],
                "comments": n["comments_n"],
                "author": n.get("author_nickname", ""),
                "fans": n["fans_n"],
                "category": n["category"],
                "pattern": n["pattern"],
                "note_type": n.get("note_type", ""),
                "url": n.get("url", ""),
                "feed_id": n.get("feed_id", ""),
            }
            for i, n in enumerate(top)
        ],
        "low_fan_viral": [
            {
                "title": n.get("title", ""),
                "author": n.get("author_nickname", ""),
                "fans": n["fans_n"],
                "likes": n["likes_n"],
                "leverage": round(n["likes_n"] / max(n["fans_n"], 1), 1),
                "url": n.get("url", ""),
            }
            for n in low_fan_viral
        ],
        "pattern_examples": {
            p: [
                {
                    "title": n["title"],
                    "likes": n["likes_n"],
                    "author": n.get("author_nickname", ""),
                }
                for n in sorted(
                    [x for x in notes if x["pattern"] == p],
                    key=lambda x: x["likes_n"],
                    reverse=True,
                )[:3]
            ]
            for p in pattern_counter_all
        },
        "pain_quotes": {
            b: [
                {
                    "quote": q["quote"][:200],
                    "likes": q["likes"],
                    "ip": q["ip"],
                    "from_note": q["from_note"],
                }
                for q in lst
            ]
            for b, lst in pain_top.items()
        },
        "hot_topics": hot_topics,
        "stats": stats,
    }
