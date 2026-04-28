"""vd CLI — entry point for all 6 sub-skills.

Usage:
    python3 shared/lib/cli.py <subcommand> [options]

Subcommands:
    setup           — check dependencies
    login-check     — verify xhs-mcp logged in
    persona-init    — auto-generate persona from xhs account
    viral-pulse     — weekly viral content report (Workflow A)
    account-decompose — single-account deep teardown (Workflow B)
    matrix-identify — multi-account matrix analysis (Workflow C)
    viral-rewrite   — persona-aware rewrite of TOP 30 (Workflow E)
    trend-scan      — emerging concept word detection (Workflow F)
"""
import argparse
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure shared/lib is importable when called directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.lib import xhs, lark, analyze, report, persona_synth, rewrite, trend
from shared.lib.config import load_config, SKILL_ROOT
from shared.lib.output_adapter import get_adapter


def _today() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")


def _parse_count(val) -> int:
    """Parse XHS count values that may contain Chinese units (e.g. '6.2万')."""
    if isinstance(val, (int, float)):
        return int(val)
    if not val:
        return 0
    s = str(val).strip()
    if s.endswith("万"):
        try:
            return int(float(s[:-1]) * 10000)
        except ValueError:
            return 0
    if s.endswith("亿"):
        try:
            return int(float(s[:-1]) * 100000000)
        except ValueError:
            return 0
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return 0


def _ensure_dir(p: str) -> Path:
    pp = Path(p)
    pp.mkdir(parents=True, exist_ok=True)
    return pp


def _push_to_feishu_or_exit(cfg, push_fn, *args, local_path_hint=None, **kwargs):
    """Mandatory Feishu push. Exits with code 2/3 on failure (no silent fallback).

    Joyce's policy: all skill outputs MUST land in Feishu. If lark-cli is missing,
    auth expired, scope insufficient, or config wrong, this exits — it does NOT
    quietly fall back to local-only output.

    Exit codes:
        2 — config error (push_to_platform=false, or missing folder_token)
        3 — push attempted but failed at runtime
    """
    if not cfg.output.push_to_platform:
        print(
            "\n✗ Feishu output is required but config.yaml has output.push_to_platform=false.\n"
            "  Set output.push_to_platform=true in config.yaml, or this skill cannot complete.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        return push_fn(*args, **kwargs)
    except lark.LarkScopeMissing as e:
        print(f"\n✗ Bot lacks required Feishu scope: {e}", file=sys.stderr)
        if e.scope_url:
            print(f"  Grant scope at: {e.scope_url}", file=sys.stderr)
        sys.exit(3)
    except lark.LarkAuthExpired as e:
        print(
            f"\n✗ Feishu auth expired: {e}\n"
            f"  Re-login: lark-cli auth login --as <identity>",
            file=sys.stderr,
        )
        sys.exit(3)
    except FileNotFoundError as e:
        print(
            f"\n✗ lark-cli not in PATH: {e}\n"
            f"  Install: see setup/02_install_lark_cli.md",
            file=sys.stderr,
        )
        sys.exit(3)
    except lark.LarkError as e:
        print(f"\n✗ Feishu push failed (mandatory output): {e}", file=sys.stderr)
        if local_path_hint:
            print(
                f"  Local file kept at: {local_path_hint} for inspection (NOT a successful run)",
                file=sys.stderr,
            )
        sys.exit(3)


# ============== Subcommand: setup ==============
def cmd_setup(args):
    """Check all dependencies."""
    import shutil

    print("== xhs-viral-decoder setup check ==\n")

    # Python
    py_ver = sys.version_info
    print(f"Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro}", end=" ")
    if py_ver >= (3, 9):
        print("✓")
    else:
        print("✗ (need ≥ 3.9)")

    # openpyxl
    try:
        import openpyxl
        print(f"openpyxl: {openpyxl.__version__} ✓")
    except ImportError:
        print("openpyxl: ✗  → pip install openpyxl")

    # xhs-mcp
    cfg = load_config()
    try:
        h = xhs.health(cfg.xhs_mcp.url)
        print(f"xhs-mcp: ✓ at {cfg.xhs_mcp.url} (account: {h.get('data', {}).get('account', '?')})")
    except xhs.XhsServiceUnavailable as e:
        print(f"xhs-mcp: ✗ {e}")

    # lark-cli
    if shutil.which("lark-cli"):
        try:
            import subprocess
            result = subprocess.run(["lark-cli", "--version"], capture_output=True, text=True)
            print(f"lark-cli: {result.stdout.strip()} ✓")
        except Exception as e:
            print(f"lark-cli: ✗ {e}")
    else:
        print("lark-cli: ✗ not in PATH → npm install -g @larksuite/cli")

    # config.yaml
    cfg_path = SKILL_ROOT / "config.yaml"
    if cfg_path.exists():
        print(f"config.yaml: ✓ at {cfg_path}")
        if cfg.feishu.folder_token == "REPLACE_WITH_YOUR_FOLDER_TOKEN":
            print("  ⚠️  feishu.folder_token still has placeholder — edit config.yaml")
    else:
        print(f"config.yaml: ✗ not found → cp config.example.yaml config.yaml")

    # 6 sub-skills
    skills_dir = SKILL_ROOT / "skills"
    found = sorted([p.name for p in skills_dir.glob("xhs-*") if (p / "SKILL.md").exists()])
    print(f"\nSub-skills detected: {len(found)}/6")
    for s in found:
        print(f"  - {s}")


# ============== Subcommand: login-check ==============
def cmd_login_check(args):
    cfg = load_config()
    try:
        info = xhs.check_login(cfg.xhs_mcp.url)
        print(f"✓ xhs-mcp logged in: account={info.get('account', '?')}")
    except xhs.XhsLoginRequired as e:
        print(f"✗ {e}")
        sys.exit(1)


# ============== Subcommand: persona-init ==============
def cmd_persona_init(args):
    cfg = load_config()

    if args.url:
        user_id, xsec_token = xhs.parse_profile_url(args.url)
    elif args.nickname:
        # search by nickname to find user_id + token
        result = xhs.search_feeds(args.nickname, base_url=cfg.xhs_mcp.url)
        feeds = [
            f for f in result.get("feeds", [])
            if f.get("noteCard", {}).get("user", {}).get("nickname") == args.nickname
        ]
        if not feeds:
            # Try fuzzy match
            feeds = [
                f for f in result.get("feeds", [])
                if args.nickname in (f.get("noteCard", {}).get("user", {}).get("nickname", ""))
            ]
        if not feeds:
            print(f"✗ No notes found for nickname '{args.nickname}'", file=sys.stderr)
            sys.exit(1)
        user_id = feeds[0]["noteCard"]["user"]["userId"]
        xsec_token = feeds[0]["xsecToken"]
        print(f"✓ Resolved {args.nickname} → user_id={user_id}")
    else:
        print("✗ Need --url or --nickname", file=sys.stderr)
        sys.exit(1)

    if not xsec_token:
        print("✗ Could not get xsec_token. Try --nickname instead of --url.", file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    out_dir = _ensure_dir(SKILL_ROOT / "raw")
    raw_path = out_dir / f"profile_{user_id}_{_today()}.json"

    print(f"\nFetching profile for user_id {user_id}...")
    raw = xhs.user_profile(user_id, xsec_token, save_to=str(raw_path), base_url=cfg.xhs_mcp.url)
    print(f"  Saved raw → {raw_path}")

    # Extract profile + feeds for synth
    ub = raw.get("userBasicInfo", {})
    profile = {
        "user_id": user_id,
        "url": f"https://www.xiaohongshu.com/user/profile/{user_id}",
        "nickname": ub.get("nickname", "未知"),
        "redId": ub.get("redId"),
        "ip": ub.get("ipLocation", ""),
        "gender": ub.get("gender"),
        "desc": ub.get("desc", ""),
    }
    interactions = raw.get("interactions", [])
    for i in interactions:
        if i.get("type") == "follows":
            profile["follow_count"] = _parse_count(i.get("count", 0))
        elif i.get("type") == "fans":
            profile["follower_count"] = _parse_count(i.get("count", 0))
        elif i.get("type") == "interaction":
            profile["total_engagement"] = _parse_count(i.get("count", 0))

    feeds = []
    for f in raw.get("feeds", []):
        nc = f.get("noteCard", {})
        likes = nc.get("interactInfo", {}).get("likedCount", "0")
        feeds.append({
            "feed_id": f.get("id"),
            "xsec_token": f.get("xsecToken"),
            "note_type": nc.get("type"),
            "title": nc.get("displayTitle", ""),
            "likes": _parse_count(likes),
        })

    nickname = profile["nickname"]

    print(f"  {nickname} | {profile.get('follower_count', 0)} 粉 | {len(feeds)} 笔记")
    print("\nSynthesizing persona...")

    persona = persona_synth.synthesize_persona(
        profile=profile,
        feeds=feeds,
        nickname=nickname,
        fetched_at=fetched_at,
        raw_path=str(raw_path.relative_to(SKILL_ROOT)),
    )

    persona_dir = _ensure_dir(SKILL_ROOT / "persona")
    persona_path = persona_dir / f"{nickname}.json"
    persona_path.write_text(json.dumps(persona, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ Persona JSON → {persona_path}")

    # Render docx markdown
    doc_md = persona_synth.render_persona_doc(persona, nickname)
    doc_md_path = persona_dir / f"{nickname}_doc.md"
    doc_md_path.write_text(doc_md, encoding="utf-8")
    print(f"  ✓ Persona docx markdown → {doc_md_path}")

    # Push to Feishu (REQUIRED — fail loudly, do NOT silently fall back to local)
    print("\nPushing to Feishu...")
    adapter = get_adapter("feishu", cfg)
    doc_token = _push_to_feishu_or_exit(
        cfg, adapter.push_doc,
        title=f"[人设档案] {nickname}_{_today()}",
        markdown=doc_md,
        local_path_hint=str(doc_md_path),
    )
    print(f"  ✓ Feishu doc: https://www.feishu.cn/docx/{doc_token}")

    print(f"\n=== Done ===")
    print(f"Persona ready. Next: try `python3 -m shared.lib.cli viral-pulse --persona {nickname}`")


# ============== Subcommand: viral-pulse ==============
def cmd_viral_pulse(args):
    cfg = load_config()
    keywords = args.keywords.split(",") if args.keywords else cfg.defaults.keywords
    niche = args.niche or cfg.defaults.niche

    print(f"== viral-pulse ==")
    print(f"Niche: {niche} | Keywords: {keywords}\n")

    out_dir = _ensure_dir(SKILL_ROOT / cfg.output.base_dir.lstrip("./") / _today() / "viral-pulse")

    # Step 1: login check
    try:
        xhs.check_login(cfg.xhs_mcp.url)
    except xhs.XhsLoginRequired as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: fetch
    print("Fetching data...")
    all_notes = {}
    for kw in keywords:
        print(f"  searching {kw}...")
        result = xhs.search_feeds(kw, sort_by="最多点赞", base_url=cfg.xhs_mcp.url)
        for f in result.get("feeds", []):
            if f.get("modelType") != "note":
                continue
            fid = f.get("id")
            if not fid or fid in all_notes:
                continue
            nc = f["noteCard"]
            likes = nc.get("interactInfo", {}).get("likedCount", "0")
            all_notes[fid] = {
                "feed_id": fid,
                "xsec_token": f["xsecToken"],
                "title": nc.get("displayTitle", ""),
                "note_type": nc.get("type"),
                "likes": _parse_count(likes),
                "author_id": nc.get("user", {}).get("userId"),
                "author_nickname": nc.get("user", {}).get("nickname", ""),
                "url": f"https://www.xiaohongshu.com/search_result/{fid}?xsec_token={f['xsecToken']}&xsec_source=pc_search",
                "keywords_matched": [kw],
            }

    notes = list(all_notes.values())
    print(f"  Total unique: {len(notes)} notes from {len(keywords)} keywords")

    # Step 3: fetch detail + comments for top likes
    print("\nFetching details for TOP 30...")
    notes.sort(key=lambda x: x.get("likes", 0), reverse=True)
    top_for_detail = notes[: args.top_n]
    blocked = []
    for n in top_for_detail:
        try:
            d = xhs.get_feed_detail(n["feed_id"], n["xsec_token"], base_url=cfg.xhs_mcp.url)
            note = d.get("data", {}).get("note", {}) if isinstance(d, dict) else {}
            n["collects"] = _parse_count(note.get("interactInfo", {}).get("collectedCount", "0"))
            n["comments_count"] = _parse_count(note.get("interactInfo", {}).get("commentCount", "0"))
            n["shares"] = _parse_count(note.get("interactInfo", {}).get("sharedCount", "0"))
            n["author_ip"] = note.get("ipLocation", "")
            n["content_excerpt"] = note.get("desc", "")[:500]
            n["publish_ts"] = note.get("time")
            comments = d.get("data", {}).get("comments", {}).get("list", []) if isinstance(d, dict) else []
            n["top_comments"] = [
                {
                    "content": c.get("content", ""),
                    "likeCount": c.get("likeCount", "0"),
                    "ipLocation": c.get("ipLocation", ""),
                }
                for c in comments
            ]
        except xhs.XhsBlocked:
            blocked.append(n["feed_id"])
            n["blocked"] = True

    print(f"  Detail fetched: {len(top_for_detail) - len(blocked)} OK, {len(blocked)} blocked")

    # Step 4: fetch follower_count for unique authors (TOP only, save calls)
    print("\nFetching author profiles for TOP authors...")
    seen_authors = {}
    for n in top_for_detail:
        aid = n.get("author_id")
        if aid and aid not in seen_authors:
            try:
                p = xhs.user_profile(aid, n["xsec_token"], base_url=cfg.xhs_mcp.url)
                interactions = p.get("interactions", [])
                fans = next((_parse_count(i.get("count", 0)) for i in interactions if i.get("type") == "fans"), 0)
                seen_authors[aid] = fans
            except Exception:
                seen_authors[aid] = 0
    for n in notes:
        n["follower_count"] = seen_authors.get(n.get("author_id"), 0)

    # Save raw
    raw_path = out_dir / "merged_raw.json"
    raw_path.write_text(json.dumps({
        "_meta": {"keywords": keywords, "fetched_at": _today(), "blocked": blocked},
        "notes": notes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Raw saved → {raw_path}")

    # Step 5: analyze
    print("\nAnalyzing...")
    analysis = analyze.build_analysis(notes, keywords=keywords, top_n=args.top_n)
    analysis_path = out_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Analysis → {analysis_path}")

    # Step 6: render
    print("\nRendering report...")
    md = report.render_viral_pulse(analysis, niche=niche, date=_today(), keywords=keywords)
    md_path = out_dir / f"{niche}赛道_本周爆款选题报告_{_today()}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"✓ Report markdown → {md_path}")

    # Step 7: build sheet
    csv_text = report.build_sheet_csv(notes)
    xlsx_path = out_dir / f"{niche}赛道_原始数据_{_today()}.xlsx"
    report.write_xlsx(csv_text, str(xlsx_path), widths=[5, 38, 8, 8, 8, 8, 8, 14, 9, 8, 16, 16, 22, 12, 50, 26])
    print(f"✓ Sheet xlsx → {xlsx_path}")

    # Step 8: push to Feishu (REQUIRED — both sheet and doc must succeed, exit on failure)
    print("\nPushing to Feishu...")
    adapter = get_adapter("feishu", cfg)
    sheet_token = _push_to_feishu_or_exit(
        cfg, adapter.push_sheet,
        title=f"{niche}赛道_原始数据_{_today()}",
        xlsx_path=str(xlsx_path),
        local_path_hint=str(xlsx_path),
    )
    print(f"  ✓ Sheet: https://my.feishu.cn/sheets/{sheet_token}")
    doc_token = _push_to_feishu_or_exit(
        cfg, adapter.push_doc,
        title=f"{niche}赛道_本周爆款选题报告_{_today()}",
        markdown=md,
        local_path_hint=str(md_path),
    )
    print(f"  ✓ Doc: https://www.feishu.cn/docx/{doc_token}")
    artifacts = {"sheet_token": sheet_token, "doc_token": doc_token}
    (out_dir / "feishu_artifacts.json").write_text(
        json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n=== Done ===")
    print(f"Output: {out_dir}")


# ============== Subcommand: trend-scan ==============
def cmd_trend_scan(args):
    cfg = load_config()
    keywords = args.keywords.split(",") if args.keywords else cfg.defaults.keywords
    niche = args.niche or cfg.defaults.niche

    out_dir = _ensure_dir(SKILL_ROOT / cfg.output.base_dir.lstrip("./") / _today() / "trend-scan")

    # Reuse latest viral-pulse data if available
    notes = []
    if args.reuse_pulse_data:
        pulse_raw = Path(args.reuse_pulse_data) / "merged_raw.json"
        if pulse_raw.exists():
            data = json.loads(pulse_raw.read_text(encoding="utf-8"))
            notes = data["notes"]
            print(f"Reusing {len(notes)} notes from {pulse_raw}")

    if not notes:
        # Fetch fresh (same as viral-pulse step 2-3)
        print("Fetching data fresh...")
        all_notes = {}
        for kw in keywords:
            print(f"  searching {kw}...")
            result = xhs.search_feeds(kw, sort_by="最多点赞", base_url=cfg.xhs_mcp.url)
            for f in result.get("feeds", []):
                if f.get("modelType") != "note":
                    continue
                fid = f.get("id")
                if not fid or fid in all_notes:
                    continue
                nc = f["noteCard"]
                likes = nc.get("interactInfo", {}).get("likedCount", "0")
                all_notes[fid] = {
                    "feed_id": fid,
                    "xsec_token": f["xsecToken"],
                    "title": nc.get("displayTitle", ""),
                    "likes": _parse_count(likes),
                    "url": f"https://www.xiaohongshu.com/search_result/{fid}?xsec_token={f['xsecToken']}",
                    "keywords_matched": [kw],
                    "publish_ts": None,  # need detail call to get this
                    "content_excerpt": "",
                }
        notes = list(all_notes.values())

    # Detect
    print(f"\nDetecting emerging concepts (window={args.window_days} days, top={args.top_n})...")
    common_lex_path = SKILL_ROOT / "shared" / "data" / "common_lexicon.txt"
    result = trend.detect_emerging_concepts(
        notes,
        common_lexicon_path=str(common_lex_path),
        window_days=args.window_days,
        top_n=args.top_n,
    )
    print(f"  Found {len(result['top_concepts'])} candidates from {result['source_notes_count']} notes")

    # Render
    md = report.render_trend_scan(result, niche=niche, date=_today())
    md_path = out_dir / f"trend_{niche}_{_today()}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"✓ Report → {md_path}")

    # Push to Feishu (REQUIRED — fail loudly)
    print("\nPushing to Feishu...")
    adapter = get_adapter("feishu", cfg)
    doc_token = _push_to_feishu_or_exit(
        cfg, adapter.push_doc,
        title=f"[趋势] {niche}_新概念词_{_today()}",
        markdown=md,
        local_path_hint=str(md_path),
    )
    print(f"  ✓ Doc: https://www.feishu.cn/docx/{doc_token}")

    print(f"\n=== Done ===\nOutput: {out_dir}")


# ============== Subcommand: viral-rewrite ==============
def cmd_viral_rewrite(args):
    cfg = load_config()
    persona_name = args.persona or cfg.defaults.persona
    if not persona_name:
        print("✗ Need --persona <name>", file=sys.stderr)
        sys.exit(1)

    persona_path = SKILL_ROOT / "persona" / f"{persona_name}.json"
    if not persona_path.exists():
        print(f"✗ Persona not found: {persona_path}", file=sys.stderr)
        print(f"   Run: vd persona-init --nickname '{persona_name}'", file=sys.stderr)
        sys.exit(1)
    persona = json.loads(persona_path.read_text(encoding="utf-8"))

    # Find input dir (latest viral-pulse if not specified)
    if args.input:
        input_dir = Path(args.input)
    else:
        base = SKILL_ROOT / cfg.output.base_dir.lstrip("./")
        candidates = sorted(base.glob("*/viral-pulse"), reverse=True)
        if not candidates:
            print("✗ No viral-pulse output found. Run viral-pulse first.", file=sys.stderr)
            sys.exit(1)
        input_dir = candidates[0]
    print(f"Input dir: {input_dir}")

    analysis = json.loads((input_dir / "analysis.json").read_text(encoding="utf-8"))

    # Build prompt
    stratum_path = SKILL_ROOT / "shared" / "reference" / "xhs_stratum_guide.md"
    stratum_excerpt = stratum_path.read_text(encoding="utf-8")[:1500] if stratum_path.exists() else ""

    prompt_md = rewrite.build_rewrite_prompt(
        persona=persona,
        top_notes=analysis["top"][: args.top_n],
        stratum_guide_excerpt=stratum_excerpt,
        top_n=args.top_n,
    )

    out_dir = _ensure_dir(SKILL_ROOT / cfg.output.base_dir.lstrip("./") / _today() / "viral-rewrite")
    prompt_path = out_dir / "rewrite_request.md"
    prompt_path.write_text(prompt_md, encoding="utf-8")

    print(f"\n✓ Rewrite prompt written → {prompt_path}")
    print(f"\nNext: paste the prompt to Claude (or copy from above) and ask Claude to fill in 30 bespoke rewrites.")
    print(f"Then save Claude's JSON response to: {out_dir}/rewrite_response.json")
    print(f"And run: python3 -m shared.lib.cli viral-rewrite-merge --input {out_dir}")
    print(f"\n--- Or for in-conversation Claude ---")
    print(f"Tell Claude: 「请按 {prompt_path} 的 prompt 生成 30 条改写，输出 JSON 后我会接着跑 viral-rewrite-merge」")


def cmd_viral_rewrite_merge(args):
    """Merge Claude's rewrite response with original analysis + push to feishu."""
    cfg = load_config()
    in_dir = Path(args.input)

    response_path = in_dir / "rewrite_response.json"
    if not response_path.exists():
        # Maybe user gave the response inline as text
        if args.response_text:
            response_text = args.response_text
        else:
            print(f"✗ No response file at {response_path}", file=sys.stderr)
            print(f"  Save Claude's JSON response there, or use --response-text", file=sys.stderr)
            sys.exit(1)
    else:
        response_text = response_path.read_text(encoding="utf-8")

    rewrites = rewrite.parse_rewrite_response(response_text, expected_count=args.top_n)

    # Find viral-pulse analysis to merge with
    pulse_dir = sorted(
        (SKILL_ROOT / cfg.output.base_dir.lstrip("./")).glob("*/viral-pulse"),
        reverse=True,
    )[0]
    analysis = json.loads((pulse_dir / "analysis.json").read_text(encoding="utf-8"))
    merged = rewrite.merge_rewrites_with_top(analysis["top"][: args.top_n], rewrites)

    out_path = in_dir / "rewrites.json"
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Merged rewrites → {out_path}")

    # Append §六 to viral-pulse report + push update
    persona_name = args.persona or "persona"
    section_six = report.render_section_six_rewrite(merged, persona_name)
    pulse_md_path = list(pulse_dir.glob("*报告*.md"))[0]
    new_md = pulse_md_path.read_text(encoding="utf-8") + section_six
    pulse_md_path.write_text(new_md, encoding="utf-8")
    print(f"✓ Updated report → {pulse_md_path}")

    # Update the original viral-pulse Feishu doc with §六 (REQUIRED — must succeed)
    if not cfg.output.push_to_platform:
        print(
            "\n✗ Feishu output is required but config.yaml has output.push_to_platform=false.\n"
            "  Set output.push_to_platform=true in config.yaml.",
            file=sys.stderr,
        )
        sys.exit(2)
    artifacts_path = pulse_dir / "feishu_artifacts.json"
    if not artifacts_path.exists():
        print(
            f"\n✗ Cannot find {artifacts_path} — viral-pulse must run first to create the original Feishu doc.\n"
            f"  Re-run viral-pulse, then retry this merge.",
            file=sys.stderr,
        )
        sys.exit(2)
    artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    doc_token = artifacts.get("doc_token")
    if not doc_token:
        print(f"\n✗ doc_token missing from {artifacts_path}.", file=sys.stderr)
        sys.exit(2)
    print(f"\nUpdating Feishu doc {doc_token}...")
    adapter = get_adapter("feishu", cfg)
    _push_to_feishu_or_exit(cfg, adapter.update_doc, doc_token, new_md, local_path_hint=str(pulse_md_path))
    print(f"  ✓ Doc updated: https://www.feishu.cn/docx/{doc_token}")


# ============== Subcommand: account-decompose / matrix-identify ==============
def cmd_account_decompose(args):
    cfg = load_config()

    if args.url:
        user_id, xsec_token = xhs.parse_profile_url(args.url)
    else:
        print("✗ Need --url", file=sys.stderr)
        sys.exit(1)

    if not xsec_token and args.nickname:
        result = xhs.search_feeds(args.nickname, base_url=cfg.xhs_mcp.url)
        for f in result.get("feeds", []):
            if f.get("noteCard", {}).get("user", {}).get("userId") == user_id:
                xsec_token = f["xsecToken"]
                break

    if not xsec_token:
        print("✗ No xsec_token. Pass --nickname so we can search.", file=sys.stderr)
        sys.exit(1)

    out_dir = _ensure_dir(SKILL_ROOT / cfg.output.base_dir.lstrip("./") / _today() / "account-decompose")

    # Fetch profile + feeds
    print(f"Fetching profile for user_id {user_id}...")
    raw = xhs.user_profile(user_id, xsec_token, base_url=cfg.xhs_mcp.url)
    ub = raw.get("userBasicInfo", {})
    profile = {
        "user_id": user_id,
        "url": f"https://www.xiaohongshu.com/user/profile/{user_id}",
        "nickname": ub.get("nickname", "?"),
        "ip": ub.get("ipLocation", ""),
        "desc": ub.get("desc", ""),
    }
    for i in raw.get("interactions", []):
        if i["type"] == "follows":
            profile["follow_count"] = _parse_count(i["count"])
        elif i["type"] == "fans":
            profile["follower_count"] = _parse_count(i["count"])
        elif i["type"] == "interaction":
            profile["total_engagement"] = _parse_count(i["count"])

    notes_summary = []
    for f in raw.get("feeds", []):
        nc = f.get("noteCard", {})
        likes = nc.get("interactInfo", {}).get("likedCount", "0")
        notes_summary.append({
            "feed_id": f.get("id"),
            "xsec_token": f.get("xsecToken"),
            "note_type": nc.get("type"),
            "title": nc.get("displayTitle", ""),
            "likes": _parse_count(likes),
            "url": f"https://www.xiaohongshu.com/user/profile/{user_id}/{f.get('id')}",
        })
    notes_summary.sort(key=lambda x: x["likes"], reverse=True)

    print(f"  {profile['nickname']} | {profile.get('follower_count', 0)} 粉 | {len(notes_summary)} 笔记")

    # Build account_data shape for renderer
    from collections import Counter
    title_text = " ".join(n["title"] for n in notes_summary)
    import re
    words = re.findall(r"[一-鿿]{2,4}", title_text)
    skip = {"自己", "我们", "什么", "可以", "为什么", "一个", "这个", "那个"}
    title_freq = [(w, c) for w, c in Counter(w for w in words if w not in skip).most_common(15)]

    pattern_dist = dict(Counter(analyze.title_pattern(n["title"]) for n in notes_summary))

    account_data = {
        "profile": profile,
        "notes_summary": notes_summary,
        "title_freq": title_freq,
        "pattern_dist": pattern_dist,
        "audience": {},  # would need TOP detail comments
    }

    # Render + push
    md = report.render_account_decompose(account_data, date=_today())
    md_path = out_dir / f"account_{profile['nickname']}_{_today()}.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"✓ Report → {md_path}")

    # Push to Feishu (REQUIRED — fail loudly)
    print("\nPushing to Feishu...")
    adapter = get_adapter("feishu", cfg)
    doc_token = _push_to_feishu_or_exit(
        cfg, adapter.push_doc,
        title=f"[拆解] {profile['nickname']}_{_today()}",
        markdown=md,
        local_path_hint=str(md_path),
    )
    print(f"  ✓ Doc: https://www.feishu.cn/docx/{doc_token}")


def cmd_matrix_identify(args):
    """Stub — full impl follows same pattern as account_decompose."""
    print("matrix-identify: 完整实现见 skills/xhs-matrix-identify/workflow.md")
    print("当前先做最小骨架——下个版本完善。")


# ============== Main ==============
def main():
    parser = argparse.ArgumentParser(prog="vd", description="xhs-viral-decoder CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("setup", help="check dependencies").set_defaults(func=cmd_setup)

    sub.add_parser("login-check", help="verify xhs-mcp logged in").set_defaults(func=cmd_login_check)

    p = sub.add_parser("persona-init", help="auto-generate persona from xhs account")
    p.add_argument("--nickname", help="xhs account nickname (resolves via search)")
    p.add_argument("--url", help="xhs profile URL (alternative to --nickname)")
    p.set_defaults(func=cmd_persona_init)

    p = sub.add_parser("viral-pulse", help="weekly viral content report")
    p.add_argument("--keywords", help="comma-separated keywords (default: from config)")
    p.add_argument("--niche", help="niche label (default: from config)")
    p.add_argument("--top-n", type=int, default=30)
    p.set_defaults(func=cmd_viral_pulse)

    p = sub.add_parser("account-decompose", help="single account deep teardown")
    p.add_argument("--url", required=True)
    p.add_argument("--nickname", help="for fallback xsec_token resolution")
    p.set_defaults(func=cmd_account_decompose)

    p = sub.add_parser("matrix-identify", help="multi-account matrix analysis")
    p.add_argument("--target-url", required=True)
    p.add_argument("--peer", default="auto")
    p.set_defaults(func=cmd_matrix_identify)

    p = sub.add_parser("viral-rewrite", help="generate rewrite prompt for Claude")
    p.add_argument("--input", help="viral-pulse output dir (default: latest)")
    p.add_argument("--persona", help="persona name (default: from config)")
    p.add_argument("--top-n", type=int, default=30)
    p.set_defaults(func=cmd_viral_rewrite)

    p = sub.add_parser("viral-rewrite-merge", help="merge Claude's rewrite response")
    p.add_argument("--input", required=True, help="dir with rewrite_response.json")
    p.add_argument("--response-text", help="alternative: paste response as string")
    p.add_argument("--persona", help="persona name for §六 title")
    p.add_argument("--top-n", type=int, default=30)
    p.set_defaults(func=cmd_viral_rewrite_merge)

    p = sub.add_parser("trend-scan", help="emerging concept word detection")
    p.add_argument("--keywords", help="comma-separated (default: from config)")
    p.add_argument("--niche", help="niche label")
    p.add_argument("--window-days", type=int, default=14)
    p.add_argument("--top-n", type=int, default=10)
    p.add_argument("--reuse-pulse-data", help="path to existing viral-pulse output dir")
    p.set_defaults(func=cmd_trend_scan)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
