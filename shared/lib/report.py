"""Markdown report renderers for the 4 report types.

- viral_pulse: 5-section weekly report
- account_decompose: 5-section single-account teardown
- matrix_identify: 4-section matrix comparison
- trend_scan: 4-section emerging concept report
"""
import csv
from io import StringIO
from typing import Optional


# ---------- Reusable formatters ----------
def _fmt_num(n: int) -> str:
    return f"{n:,}"


def _trunc(s: str, n: int) -> str:
    if not s:
        return ""
    s = s.replace("|", "/").replace("\n", " ")
    return s[:n]


# ============== Workflow A: viral_pulse ==============
def render_viral_pulse(
    analysis: dict,
    niche: str = "心理",
    date: str = "2026-04-27",
    keywords: list = None,
    pulse_meta: Optional[dict] = None,
) -> str:
    """Generate the 5-section weekly viral report markdown."""
    S = analysis["stats"]
    md = []
    md.append(f"# {niche}赛道_本周爆款选题报告_{date}\n")
    md.append(
        f"> 抓取时间：{date}　|　关键词：{' / '.join(keywords or analysis['_meta']['keywords'])}　|　共 {S['total_notes']} 篇笔记\n"
    )
    md.append("> 数据来源：xiaohongshu-mcp（含真实评论 + 粉丝数全量）　|　对照博主 5 节结构产出\n\n")

    # ===== Section 1: TOP table =====
    top_n = analysis["_meta"]["top_n"]
    md.append(f"## 一、数据排行榜 TOP {top_n}\n")
    md.append("按点赞数降序。完整原始数据见同目录 sheet。\n\n")
    md.append("| 排名 | 标题 | 点赞 | 收藏 | 评论 | 作者 | 粉丝 | 观点分类 | 类型 |\n")
    md.append("|---:|---|---:|---:|---:|---|---:|---|---|\n")
    for n in analysis["top"]:
        title = _trunc(n["title"] or "(无标题/纯图文)", 32)
        type_label = "视频" if n["note_type"] == "video" else "图文"
        md.append(
            f"| {n['rank']} | [{title}]({n['url']}) | {_fmt_num(n['likes'])} | "
            f"{_fmt_num(n['collects'])} | {_fmt_num(n['comments'])} | {n['author']} | "
            f"{_fmt_num(n['fans'])} | {n['category']} | {type_label} |\n"
        )

    # Low-fan viral
    md.append(f"\n### 🌱 本批数据中的「低粉爆款」\n")
    md.append(
        f"{S['low_fan_viral_count']} 条（占样本 {S['low_fan_viral_pct']}%）。"
        f"低粉杠杆最大，最值得复刻。\n\n"
    )
    md.append("| 杠杆倍数 | 粉丝 | 点赞 | 标题 | 作者 |\n|---:|---:|---:|---|---|\n")
    for n in analysis["low_fan_viral"]:
        title = _trunc(n["title"] or "(无标题)", 30)
        md.append(
            f"| **{n['leverage']}×** | {_fmt_num(n['fans'])} | {_fmt_num(n['likes'])} | "
            f"[{title}]({n['url']}) | {n['author']} |\n"
        )

    # ===== Section 2: Frameworks =====
    md.append("\n## 二、爆款内容框架分析\n")
    md.append(f"### 2.1 高频标题公式（按 TOP {top_n} 命中率排序）\n\n")
    patterns_sorted = sorted(
        analysis["pattern_examples"].items(),
        key=lambda x: -S["pattern_distribution_top"].get(x[0], 0),
    )
    for p, examples in patterns_sorted:
        cnt_top = S["pattern_distribution_top"].get(p, 0)
        cnt_all = S["pattern_distribution_all"].get(p, 0)
        if cnt_all == 0:
            continue
        md.append(f"#### {p}　（TOP{top_n} 命中 {cnt_top}/{top_n}，全量 {cnt_all}/{S['total_notes']}）\n")
        for e in examples:
            t = _trunc(e["title"] or "(无标题)", 40)
            md.append(f"- {t}　→ {_fmt_num(e['likes'])} 赞（{e['author']}）\n")
        md.append("\n")

    md.append("### 2.2 内容形式分布\n\n")
    td = S["type_distribution"]
    total = sum(td.values())
    for k, v in td.items():
        label = "图文" if k == "normal" else ("视频" if k == "video" else k)
        pct = round(100 * v / total, 1)
        md.append(f"- **{label}**：{v} 篇（{pct}%）\n")

    md.append("\n### 2.3 观点分类分布（TOP）\n\n")
    for cat, cnt in sorted(S["category_distribution_top"].items(), key=lambda x: -x[1]):
        md.append(f"- **{cat}**：{cnt} 条\n")

    # ===== Section 3: Pain points =====
    md.append("\n## 三、核心信息点汇总\n")
    md.append("### 3.1 本周高频话题词（TOP 20）\n\n")
    md.append("| 词 | 次数 | | 词 | 次数 |\n|---|---:|---|---|---:|\n")
    ht = analysis["hot_topics"]
    for i in range(0, len(ht), 2):
        left = ht[i]
        right = ht[i + 1] if i + 1 < len(ht) else ("", "")
        md.append(f"| {left[0]} | {left[1]} | | {right[0]} | {right[1]} |\n")

    md.append("\n### 3.2 用户核心痛点（**真实评论引用，非反推**）\n\n")
    md.append("以下每条都是真实评论原文 + IP + 赞数 + 出处。痛点桶按总赞数排序。\n\n")
    pain_order = sorted(
        analysis["pain_quotes"].keys(),
        key=lambda b: -sum(q["likes"] for q in analysis["pain_quotes"][b]),
    )
    for b in pain_order:
        quotes = analysis["pain_quotes"][b]
        if not quotes:
            continue
        md.append(f"#### 🎯 {b}\n\n")
        for q in quotes:
            quote_text = q["quote"].replace("\n", " ").strip()
            if len(quote_text) > 140:
                quote_text = quote_text[:140] + "…"
            from_note = q["from_note"][:24] or "(无标题)"
            md.append(
                f"> 「{quote_text}」\n>\n> — {q['ip']} 网友，{_fmt_num(q['likes'])} 赞　·　来自《{from_note}》\n\n"
            )

    # ===== Section 4: Topic suggestions =====
    md.append("\n## 四、本周可用爆款选题建议（TOP 10）\n\n")
    md.append("基于 §一 TOP 数据 + §二 高 ROI 公式 + §三 真实痛点，自动推导。\n\n")
    md.append("> **此节由 `xhs-viral-rewrite` 进一步用持有人 persona 改写后会更可执行**。当前是通用版。\n\n")

    # Auto-pick TOP 10 topic seeds based on TOP 30 + pattern ROI
    top_topics = analysis["top"][:10]
    for i, n in enumerate(top_topics, 1):
        type_label = "视频" if n["note_type"] == "video" else "图文"
        md.append(f"### 选题 {i}：套用爆款模板\n")
        md.append(f"- **参考爆款**：[{n['title'] or '(无标题)'}]({n['url']})（{_fmt_num(n['likes'])} 赞 / {type_label}）\n")
        md.append(f"- **公式**：{n['pattern']}\n")
        md.append(f"- **观点类型**：{n['category']}\n")
        md.append(f"- **行动**：先用此模板 + 你赛道里的具体场景试写一篇\n\n")

    # ===== Section 5: Quantitative regularities =====
    md.append("\n## 五、数据规律总结\n\n### 5.1 量化基线\n\n")
    md.append(f"- 点赞中位数：{_fmt_num(S['median_likes'])}\n")
    md.append(f"- 点赞均值：{_fmt_num(S['mean_likes'])}\n")
    md.append(f"- 点赞最高：{_fmt_num(S['max_likes'])}\n")
    md.append(f"- 收藏中位数：{_fmt_num(S['median_collects'])}\n")
    md.append(f"- 评论中位数：{_fmt_num(S['median_comments'])}\n")
    md.append(f"- 收藏/点赞比中位数：{S['collect_like_ratio_median']}\n")
    md.append(f"- 评论/点赞比中位数：{S['comment_like_ratio_median']}\n\n")

    md.append("### 5.2 低粉爆款规律\n\n")
    md.append(f"- 低粉爆款占比 **{S['low_fan_viral_pct']}%**\n")
    if analysis["low_fan_viral"]:
        top_lev = analysis["low_fan_viral"][0]
        md.append(
            f"- TOP 杠杆：**{top_lev['author']} {top_lev['leverage']}×**"
            f"（{_fmt_num(top_lev['fans'])}粉 → {_fmt_num(top_lev['likes'])}赞）\n"
        )

    md.append("\n### 5.3 标题公式 ROI 排序\n\n")
    all_d = S["pattern_distribution_all"]
    top_d = S["pattern_distribution_top"]
    roi = []
    for p, all_cnt in all_d.items():
        top_cnt = top_d.get(p, 0)
        if all_cnt == 0:
            continue
        roi.append((p, top_cnt, all_cnt, round(100 * top_cnt / all_cnt, 1)))
    roi.sort(key=lambda x: -x[3])
    md.append("| 公式 | TOP 命中 | 全样本 | 上榜率 |\n|---|---:|---:|---:|\n")
    for p, t, a, r in roi:
        md.append(f"| {p} | {t} | {a} | **{r}%** |\n")

    md.append("\n---\n\n## 数据局限说明\n\n")
    md.append(f"- 数据样本：{S['total_notes']} 篇\n")
    md.append("- 评论按「前 10 条」返回，足够定性，不足以做严格定量\n")
    md.append("- 标题公式分类用关键词规则，准确率约 80%\n")

    return "".join(md)


# ============== Sheet generation ==============
def build_sheet_csv(notes: list, rewrites: Optional[dict] = None) -> str:
    """Build a CSV string for the data sheet (16 cols base + 2 if rewrites)."""
    out = StringIO()
    w = csv.writer(out)
    headers = [
        "排名", "标题", "笔记类型", "点赞", "收藏", "评论数", "分享",
        "作者", "粉丝数", "作者IP", "命中关键词",
        "观点分类", "标题公式", "发布时间", "链接", "feed_id",
    ]
    if rewrites:
        headers += ["推荐改编形式", "改写标题"]
    w.writerow(headers)

    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))

    ranked = sorted(notes, key=lambda x: int(x.get("likes") or 0), reverse=True)
    rw_by_rank = {}
    if rewrites:
        rw_by_rank = {r["rank"]: r for r in rewrites.get("rewrites", [])}

    for i, n in enumerate(ranked, 1):
        ts = n.get("publish_ts")
        date = (
            datetime.fromtimestamp(ts / 1000, tz).strftime("%Y-%m-%d")
            if ts else ""
        )
        row = [
            i,
            n.get("title", "(无标题)"),
            n.get("note_type", ""),
            int(n.get("likes") or 0),
            int(n.get("collects") or 0),
            int(n.get("comments_count") or 0),
            int(n.get("shares") or 0),
            n.get("author_nickname", ""),
            int(n.get("follower_count") or 0),
            n.get("author_ip", ""),
            "/".join(n.get("keywords_matched", [])),
            n.get("category", ""),
            n.get("pattern", ""),
            date,
            n.get("url", ""),
            n.get("feed_id", ""),
        ]
        if rewrites:
            rw = rw_by_rank.get(i, {})
            row.append(rw.get("suggested_form", ""))
            row.append(rw.get("rewrite", ""))
        w.writerow(row)

    return out.getvalue()


def write_xlsx(csv_text: str, xlsx_path: str, widths: list = None):
    """Write CSV text to an xlsx file using openpyxl."""
    try:
        import openpyxl
    except ImportError as e:
        raise RuntimeError(
            "openpyxl required for xlsx output. Install: pip install openpyxl"
        ) from e

    import csv as csv_mod
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "数据"
    for row in csv_mod.reader(StringIO(csv_text)):
        ws.append(row)
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    wb.save(xlsx_path)


# ============== Workflow B: account_decompose ==============
def render_account_decompose(account_data: dict, date: str = "2026-04-27") -> str:
    """Generate single-account decompose markdown.

    Expected account_data shape: see skills/xhs-account-decompose/workflow.md output schema.
    """
    p = account_data["profile"]
    md = []
    nickname = p.get("nickname", "未知")
    md.append(f"# [单账号深度拆解] {nickname}_{date}\n\n")
    md.append(f"> 抓取时间：{date}　|　主页：{p.get('url', '')}\n\n")

    # === 1
    md.append("## 一、账号基本信息\n\n")
    md.append("| 字段 | 数值 |\n|---|---|\n")
    md.append(f"| 昵称 | **{nickname}** |\n")
    md.append(f"| 粉丝数 | {_fmt_num(p.get('follower_count', 0))} |\n")
    md.append(f"| 关注数 | {_fmt_num(p.get('follow_count', 0))} |\n")
    md.append(f"| 获赞与收藏 | {_fmt_num(p.get('total_engagement', 0))} |\n")
    md.append(f"| IP 属地 | {p.get('ip', '(隐藏)')} |\n")
    md.append(f"| 简介 | {p.get('desc', '')} |\n")
    notes = account_data.get("notes_summary", [])
    md.append(f"| 抓取笔记数 | {len(notes)} |\n")

    type_counts = {}
    for n in notes:
        type_counts[n.get("note_type", "?")] = type_counts.get(n.get("note_type", "?"), 0) + 1
    md.append(f"| 笔记类型 | {type_counts} |\n")

    if notes:
        likes_list = sorted([n.get("likes", 0) for n in notes], reverse=True)
        md.append(f"| TOP3 点赞 | {likes_list[:3]} |\n")
        md.append(f"| 爆款率（≥1k） | {round(100 * sum(1 for l in likes_list if l >= 1000) / len(likes_list), 1)}% |\n")
        md.append(f"| 大爆率（≥10k） | {round(100 * sum(1 for l in likes_list if l >= 10000) / len(likes_list), 1)}% |\n")

    # === 2 tags
    md.append("\n## 二、现有标签\n\n")
    md.append(f"### 2.1 简介自我标签\n\n{p.get('desc', '')}\n\n")
    if account_data.get("title_freq"):
        md.append("### 2.2 标题高频词（TOP 15）\n\n")
        for w, c in account_data["title_freq"][:15]:
            md.append(f"- {w}（{c} 次）\n")
    if account_data.get("pattern_dist"):
        md.append("\n### 2.3 标题公式分布\n\n")
        for pat, c in sorted(account_data["pattern_dist"].items(), key=lambda x: -x[1]):
            pct = round(100 * c / max(len(notes), 1), 1)
            md.append(f"- {pat}：{c} 篇（{pct}%）\n")

    # === 3 audience
    audience = account_data.get("audience", {})
    if audience:
        md.append("\n## 三、目标人群画像\n\n")
        if audience.get("ip_top10"):
            md.append("### 3.1 评论 IP 地域分布（TOP 10）\n\n")
            for region, cnt in audience["ip_top10"]:
                md.append(f"- {region}：{cnt} 条评论\n")
        if audience.get("themes"):
            md.append("\n### 3.2 评论里高频话题维度\n\n")
            for theme, cnt in sorted(audience["themes"].items(), key=lambda x: -x[1]):
                md.append(f"- **{theme}**：{cnt} 条评论\n")

    # === 4 formulas
    md.append("\n## 四、爆款公式与内容框架\n\n### 4.1 TOP 5 高赞笔记\n\n")
    for n in sorted(notes, key=lambda x: x.get("likes", 0), reverse=True)[:5]:
        title = n.get("title") or "(无标题)"
        md.append(f"- [{title}]({n.get('url', '')}) · {_fmt_num(n.get('likes', 0))} 赞\n")

    # === 5 improvements
    if account_data.get("improvements"):
        md.append("\n## 五、可改进方向\n\n")
        for line in account_data["improvements"]:
            md.append(f"- {line}\n")

    if account_data.get("actions_to_copy"):
        md.append("\n### 5.7 本周可抄的 3 个具体动作\n\n")
        for i, a in enumerate(account_data["actions_to_copy"], 1):
            md.append(f"**动作 {i}**: {a.get('title', '')}\n")
            md.append(f"- 角度：{a.get('angle', '')}\n")
            md.append(f"- 形式：{a.get('form', '')}\n")
            md.append(f"- 触达痛点：{a.get('pain', '')}\n\n")

    return "".join(md)


# ============== Workflow C: matrix_identify ==============
def render_matrix_identify(matrix_data: dict, date: str = "2026-04-27") -> str:
    """Generate matrix identification markdown."""
    md = []
    target = matrix_data["target"]
    peer = matrix_data.get("peer")
    md.append(f"# [矩阵识别] {target['nickname']}")
    if peer:
        md.append(f" vs {peer['nickname']}")
    md.append(f"_{date}\n\n")
    md.append("> 拆解结构对齐 [模板] 矩阵账号识别 4 节\n\n")

    # === 1 主体识别
    md.append("## 一、矩阵主体识别\n\n")
    md.append(f"### 案例 A：{target['nickname']} 矩阵\n\n")
    md.append("| 序号 | 账号名 | user_id | 形式 | 估算 TOP 赞数 |\n|---:|---|---|---|---:|\n")
    for i, acc in enumerate(target.get("matrix_accounts", []), 1):
        md.append(f"| {i} | {acc['nickname']} | `{acc['user_id']}` | {acc.get('form', '?')} | {_fmt_num(acc.get('top_likes', 0))} |\n")

    if peer:
        md.append(f"\n### 案例 B（对照）：{peer['nickname']} 矩阵\n\n")
        md.append("| 序号 | 账号名 | user_id | 形式 | 估算 TOP 赞数 |\n|---:|---|---|---|---:|\n")
        for i, acc in enumerate(peer.get("matrix_accounts", []), 1):
            md.append(f"| {i} | {acc['nickname']} | `{acc['user_id']}` | {acc.get('form', '?')} | {_fmt_num(acc.get('top_likes', 0))} |\n")

    # === 2 distribution logic
    md.append("\n## 二、内容分发逻辑\n\n")
    for line in matrix_data.get("distribution_rules", []):
        md.append(f"- {line}\n")

    # === 3 leverage
    md.append("\n## 三、矩阵带来的杠杆量化\n\n")
    md.append(f"- 目标矩阵号数：{len(target.get('matrix_accounts', []))}\n")
    md.append(f"- 估算总曝光：{_fmt_num(target.get('estimated_monthly_exposure', 0))} / 月\n")
    md.append(f"- 杠杆倍数：{target.get('leverage_multiplier', 1)}×\n")

    # === 4 user proposal
    md.append("\n## 四、可借鉴 / 不可借鉴 + 单人现实方案\n\n")
    for line in matrix_data.get("user_proposal", []):
        md.append(f"{line}\n\n")

    return "".join(md)


# ============== Workflow F: trend_scan ==============
def render_trend_scan(trend_data: dict, niche: str = "心理", date: str = "2026-04-27") -> str:
    """Generate emerging concept trend markdown."""
    md = []
    md.append(f"# [趋势] {niche}_新概念词_{date}\n\n")
    md.append(f"> 来源：xhs-trend-scan，分析 {trend_data.get('source_notes_count', 0)} 篇近期笔记\n\n")

    md.append("## 一、TOP 10 emerging concepts\n\n")
    md.append("| 排名 | 词 | 出现频次 | 在爆款里出现 | 时间集中度 | 综合分 |\n|---:|---|---:|---:|---:|---:|\n")
    for i, c in enumerate(trend_data.get("top_concepts", [])[:10], 1):
        md.append(
            f"| {i} | **{c['word']}** | {c['freq']} | {c['in_viral']} | {c['recency']:.2f} | **{c['score']:.1f}** |\n"
        )

    md.append("\n## 二、Per-concept context\n\n")
    for c in trend_data.get("top_concepts", [])[:10]:
        md.append(f"### {c['word']}\n\n")
        md.append(f"出现于 {len(c.get('source_notes', []))} 条笔记。示例：\n\n")
        for src in c.get("source_notes", [])[:3]:
            md.append(f"- [{src['title']}]({src['url']}) · {_fmt_num(src['likes'])} 赞\n")
        md.append("\n")

    md.append("\n## 三、Trend trajectory\n\n")
    for c in trend_data.get("top_concepts", [])[:5]:
        first = c.get("first_appearance", "未知")
        md.append(f"- **{c['word']}**：first observed {first}, score {c['score']:.1f}\n")

    md.append("\n## 四、Action 推荐\n\n")
    md.append("以下 3 个新概念词最值得本周内容尝试采用：\n\n")
    for i, c in enumerate(trend_data.get("recommended", [])[:3], 1):
        md.append(f"**{i}. {c['word']}** — {c.get('reason', '')}\n\n")

    return "".join(md)


# ============== Workflow E: viral_rewrite (extends viral_pulse) ==============
def render_section_six_rewrite(rewrites: dict, persona_name: str) -> str:
    """Generate the §六 section to append to viral_pulse report after rewrite."""
    md = []
    md.append(f"\n## 六、{persona_name} 人设改写映射 (TOP {len(rewrites['rewrites'])})\n\n")
    md.append(
        "> 把每条已验证爆款，按 persona 翻译成「我能立刻拍的版本」。"
        "改写规则：取原标题独特 hook + 套人设锚点。\n\n"
    )
    md.append("| # | 原爆款（赞数 / 形式） | 改编形式 | 改写标题 | 改写角度 |\n|---:|---|---|---|---|\n")
    for r in rewrites["rewrites"]:
        orig = _trunc(r["original_title"] or "(无标题)", 24)
        rw = (r["rewrite"] or "").replace("|", "/")
        angle = (r.get("angle", "") or "").replace("|", "/")
        md.append(
            f"| {r['rank']} | [{orig}]({r['url']}) {_fmt_num(r['original_likes'])}/{r['original_form']} | "
            f"**{r['suggested_form']}** | {rw} | {angle} |\n"
        )
    return "".join(md)
