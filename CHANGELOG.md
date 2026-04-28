# Changelog

## v0.2.0 (2026-04-28) — Niche-agnostic persona synthesis

### Breaking
- `persona_synth.py` output schema adds new fields: `content_themes`, `_meta.detected_niche`, `_meta.is_mixed_niche`. Existing persona JSON files still work but won't have these fields.

### Added
- **Niche auto-detection**: `detect_niche()` identifies 13 niches (宠物/美食/旅行/穿搭/美妆/健身/母婴/音乐/科技/心理/家居/摄影/职场) from bio keywords + title patterns
- Niche-specific tone palette, constraints, and content theme defaults
- `_detect_content_themes()` for title-based content clustering
- `extract_bio_self_tags()` for clean bio tag extraction (handles emoji prefixes)
- `_parse_count()` in cli.py for Chinese number units (万/亿)

### Changed
- **`persona_synth.py` now niche-agnostic**: 6-stratum psychology lens only applied when `detected_niche == "心理"`. All other niches use generic synthesis with actual bio self-tags as core_tags.
- `extract_topic_focus()` improved: splits on Chinese particles before n-gram extraction
- `xhs.py` rewritten to use MCP JSON-RPC protocol (v2.0.0+) with per-call fresh sessions

### Fixed
- Non-psychology accounts no longer get "反套路心理观察家" as core_tags (was defaulting all accounts to cognitive substratum when 6 scores were 0)
- `int("6.2万")` ValueError — now handled by `_parse_count()`

## v0.1.0 (2026-04-27) — Initial release

### Added
- 6 composable sub-skills:
  - `xhs-viral-pulse` — weekly viral content report
  - `xhs-account-decompose` — single-account deep teardown
  - `xhs-matrix-identify` — multi-account matrix identification
  - `xhs-persona-synth` — auto-generate creator persona from xhs account
  - `xhs-viral-rewrite` — Carol-style persona-aware rewrite of viral titles
  - `xhs-trend-scan` — emerging concept word detection
- Feishu output adapter (complete, validated)
- Slack / Telegram / WhatsApp adapter stubs with implementation guides
- 6-stratum lens for persona auto-synthesis (cognitive / healing / howto / academic / women's growth / lifestyle)
- 5000-word common Chinese lexicon baseline for trend detection
- Detailed setup docs for xhs-mcp + lark-cli dependencies
- 6 example outputs for reference
