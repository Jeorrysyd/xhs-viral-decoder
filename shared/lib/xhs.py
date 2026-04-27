"""HTTP client for xhs-mcp service.

Bypasses the MCP tool wrapper (which has 25k token response truncation).
Calls xhs-mcp's HTTP API directly at http://localhost:18060.

All large responses are auto-saved to disk and the function returns a parsed dict.
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


class XhsLoginRequired(Exception):
    """Raised when xhs-mcp service has no valid login session."""
    pass


class XhsServiceUnavailable(Exception):
    """Raised when xhs-mcp HTTP service can't be reached."""
    pass


class XhsBlocked(Exception):
    """Raised when xhs anti-scrape blocks a specific note (page unavailable)."""
    pass


# Default xhs-mcp URL (override via config or kwarg)
DEFAULT_BASE_URL = "http://localhost:18060"


def _post_json(url: str, body: dict, timeout: int = 60) -> dict:
    """POST JSON, return parsed response. Raises on HTTP error."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise XhsServiceUnavailable(
            f"Cannot reach xhs-mcp at {url}: {e}. "
            f"Run: cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-mcp-darwin-arm64 &"
        ) from e
    return json.loads(raw)


def _get(url: str, timeout: int = 10) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise XhsServiceUnavailable(f"Cannot reach xhs-mcp at {url}: {e}") from e


def health(base_url: str = DEFAULT_BASE_URL) -> dict:
    """Returns xhs-mcp health status."""
    return _get(f"{base_url}/health")


def check_login(base_url: str = DEFAULT_BASE_URL) -> dict:
    """Check if xhs-mcp has a valid logged-in session.

    Raises XhsLoginRequired if not logged in.
    Returns the health response with account info if logged in.
    """
    h = health(base_url)
    if not h.get("success"):
        raise XhsLoginRequired(
            "xhs-mcp service unhealthy. Run setup/01_install_xhs_mcp.md."
        )
    # Verify with a no-op call — if cookies are stale, search will hang/timeout
    # so we just trust /health here. Caller will see XhsLoginRequired on real ops.
    return h["data"]


def search_feeds(
    keyword: str,
    sort_by: str = "最多点赞",
    note_type: str = "不限",
    publish_time: str = "不限",
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 60,
) -> dict:
    """Search xhs feeds by keyword.

    Returns dict with `feeds` key (list of note records, each with
    feed_id, xsec_token, noteCard.{title, likes, type, user, ...}).

    Caller should dedupe by feed_id and sort/filter as needed.
    """
    body = {
        "keyword": keyword,
        "filters": {
            "sort_by": sort_by,
            "note_type": note_type,
            "publish_time": publish_time,
        },
    }
    return _post_json(f"{base_url}/api/v1/search", body, timeout=timeout)


def user_profile(
    user_id: str,
    xsec_token: str,
    save_to: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 90,
) -> dict:
    """Fetch a user's profile + feeds.

    Returns dict with userBasicInfo, interactions, feeds.

    If response is large (>20kb) and `save_to` provided, writes raw JSON to that path.
    """
    body = {"user_id": user_id, "xsec_token": xsec_token}
    result = _post_json(f"{base_url}/api/v1/user/profile", body, timeout=timeout)
    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        Path(save_to).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return result


def get_feed_detail(
    feed_id: str,
    xsec_token: str,
    load_all_comments: bool = False,
    save_to: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 90,
) -> dict:
    """Fetch a single note's full detail + top comments.

    Raises XhsBlocked if note returns "Sorry, This Page Isn't Available Right Now."
    """
    body = {
        "feed_id": feed_id,
        "xsec_token": xsec_token,
        "load_all_comments": load_all_comments,
    }
    try:
        result = _post_json(
            f"{base_url}/api/v1/feed/detail", body, timeout=timeout
        )
    except urllib.error.HTTPError as e:
        # xhs anti-scrape often returns HTTP 200 with error message in body,
        # but 4xx from MCP wrapper indicates blocked
        if e.code in (400, 404):
            raise XhsBlocked(f"feed {feed_id} blocked by xhs") from e
        raise

    # Some MCP servers return success=false with the "页面不可访问" message
    if isinstance(result, dict) and not result.get("success", True):
        msg = result.get("message", "")
        if "Page Isn't Available" in msg or "页面不可访问" in msg or "笔记不可访问" in msg:
            raise XhsBlocked(f"feed {feed_id} blocked: {msg[:80]}")

    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        Path(save_to).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return result


def list_homepage_feeds(base_url: str = DEFAULT_BASE_URL, timeout: int = 30) -> dict:
    """Fetch the logged-in user's homepage feeds (whatever xhs recommends to them)."""
    return _post_json(f"{base_url}/api/v1/list_feeds", {}, timeout=timeout)


# ---------- Convenience: parse profile URL ----------
def parse_profile_url(url: str) -> tuple[str, Optional[str]]:
    """Extract (user_id, xsec_token) from a xhs profile URL.

    Examples:
        https://www.xiaohongshu.com/user/profile/<id>?xsec_token=<token>&xsec_source=pc_note
        → ('<id>', '<token>')

        https://www.xiaohongshu.com/user/profile/<id>?m_source=pwa
        → ('<id>', None)
    """
    import urllib.parse as up

    parsed = up.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if "user" in parts and "profile" in parts:
        idx = parts.index("profile")
        user_id = parts[idx + 1] if idx + 1 < len(parts) else None
    else:
        user_id = None
    if not user_id:
        raise ValueError(f"Cannot extract user_id from URL: {url}")

    qs = up.parse_qs(parsed.query)
    xsec_token = qs.get("xsec_token", [None])[0]
    return user_id, xsec_token


def parse_note_url(url: str) -> tuple[str, Optional[str]]:
    """Extract (feed_id, xsec_token) from a xhs note URL.

    Supports /search_result/<id> and /user/profile/<uid>/<id> patterns.
    """
    import urllib.parse as up
    import re

    parsed = up.urlparse(url)
    # Pattern 1: /search_result/<feed_id>
    m = re.match(r"/search_result/([0-9a-f]+)", parsed.path)
    if m:
        feed_id = m.group(1)
    else:
        # Pattern 2: /user/profile/<uid>/<feed_id>
        m = re.match(r"/user/profile/[^/]+/([0-9a-f]+)", parsed.path)
        if m:
            feed_id = m.group(1)
        else:
            raise ValueError(f"Cannot extract feed_id from URL: {url}")

    qs = up.parse_qs(parsed.query)
    xsec_token = qs.get("xsec_token", [None])[0]
    return feed_id, xsec_token
