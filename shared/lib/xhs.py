"""HTTP client for xhs-mcp service.

Supports MCP JSON-RPC over HTTP (v2.0.0+) — the server exposes a single
/mcp endpoint that speaks JSON-RPC 2.0.

All large responses are auto-saved to disk and the function returns a parsed dict.
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import threading


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

# Thread-safe MCP session manager
_sessions = {}  # base_url → (session_id, id_counter)
_session_lock = threading.Lock()


def _post_json(url: str, body: dict, headers: dict = None, timeout: int = 60) -> dict:
    """POST JSON, return parsed response. Raises on HTTP error."""
    data = json.dumps(body).encode("utf-8")
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            session_id = resp.headers.get("Mcp-Session-Id")
            # Handle 202 / empty body (e.g. MCP notifications)
            if not raw.strip():
                result = {"_status": resp.status}
            else:
                result = json.loads(raw)
            if session_id:
                result["_mcp_session_id"] = session_id
            return result
    except urllib.error.URLError as e:
        raise XhsServiceUnavailable(
            f"Cannot reach xhs-mcp at {url}: {e}. "
            f"Run: cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-mcp-darwin-arm64 &"
        ) from e


def _get(url: str, timeout: int = 10) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise XhsServiceUnavailable(f"Cannot reach xhs-mcp at {url}: {e}") from e


def _ensure_mcp_session(base_url: str = DEFAULT_BASE_URL) -> tuple:
    """Initialize MCP session if needed. Returns (session_id, next_id_func)."""
    with _session_lock:
        if base_url in _sessions:
            return _sessions[base_url]

        mcp_url = f"{base_url}/mcp"

        # Step 1: Initialize
        init_resp = _post_json(mcp_url, {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "vd-cli", "version": "0.1.0"}
            }
        })

        session_id = init_resp.get("_mcp_session_id", "")

        # Step 2: Send initialized notification
        _post_json(mcp_url, {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }, headers={"Mcp-Session-Id": session_id})

        counter = [10]  # mutable counter starting after init IDs

        def next_id():
            counter[0] += 1
            return counter[0]

        _sessions[base_url] = (session_id, next_id)
        return session_id, next_id


def _mcp_call_tool(tool_name: str, arguments: dict,
                   base_url: str = DEFAULT_BASE_URL,
                   timeout: int = 180) -> dict:
    """Call an MCP tool via JSON-RPC and return the parsed content.

    Each call initializes a fresh MCP session to avoid browser state
    conflicts between sequential tool calls (e.g., two search_feeds
    with different keywords on the same browser page).
    """
    mcp_url = f"{base_url}/mcp"
    headers_base = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    # Initialize fresh session
    init_resp = _post_json(mcp_url, {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "vd-cli", "version": "0.1.0"}
        }
    })
    session_id = init_resp.get("_mcp_session_id", "")
    session_headers = {**headers_base, "Mcp-Session-Id": session_id}

    # Send initialized notification
    _post_json(mcp_url, {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }, headers=session_headers)

    # Call the tool
    resp = _post_json(mcp_url, {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 2,
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }, headers=session_headers, timeout=timeout)

    # Handle JSON-RPC error
    if "error" in resp:
        err = resp["error"]
        raise XhsServiceUnavailable(f"MCP tool {tool_name} error: {err.get('message', err)}")

    # Extract content from MCP tool result
    result = resp.get("result", {})
    content_list = result.get("content", [])

    # MCP tools return content as list of {type: "text", text: "..."}
    # Parse the first text content as JSON
    for item in content_list:
        if item.get("type") == "text":
            text = item["text"]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw_text": text}

    return result


# ============== Public API (same signatures as before) ==============

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
    return h["data"]


def search_feeds(
    keyword: str,
    sort_by: str = "最多点赞",
    note_type: str = "不限",
    publish_time: str = "不限",
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 120,
) -> dict:
    """Search xhs feeds by keyword via MCP tool.

    Returns dict with `feeds` key (list of note records).
    """
    arguments = {"keyword": keyword}
    # NOTE: sort_by filter causes the MCP browser automation to hang
    # (clicking the dropdown in xhs UI is slow/unreliable). We skip it
    # and sort results client-side instead (the CLI already does this).
    filters = {}
    if note_type != "不限":
        filters["note_type"] = note_type
    if publish_time != "不限":
        filters["publish_time"] = publish_time
    if filters:
        arguments["filters"] = filters

    result = _mcp_call_tool("search_feeds", arguments, base_url=base_url, timeout=timeout)

    # Normalize: MCP may return the data in different shapes
    if isinstance(result, dict):
        # If result has 'items' or 'feeds' key, use it
        if "feeds" in result:
            return result
        elif "items" in result:
            return {"feeds": result["items"]}
        elif "data" in result and isinstance(result["data"], dict):
            return result["data"]
        elif "data" in result and isinstance(result["data"], list):
            return {"feeds": result["data"]}
        else:
            # Try to find the feeds list
            return {"feeds": result.get("feeds", [])}
    return {"feeds": []}


def user_profile(
    user_id: str,
    xsec_token: str,
    save_to: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 120,
) -> dict:
    """Fetch a user's profile + feeds via MCP tool."""
    result = _mcp_call_tool("user_profile", {
        "user_id": user_id,
        "xsec_token": xsec_token,
    }, base_url=base_url, timeout=timeout)

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
    timeout: int = 120,
) -> dict:
    """Fetch a single note's full detail + top comments via MCP tool.

    Raises XhsBlocked if note returns "Sorry, This Page Isn't Available Right Now."
    """
    arguments = {
        "feed_id": feed_id,
        "xsec_token": xsec_token,
    }
    if load_all_comments:
        arguments["load_all_comments"] = True

    try:
        result = _mcp_call_tool("get_feed_detail", arguments,
                                base_url=base_url, timeout=timeout)
    except XhsServiceUnavailable as e:
        if "blocked" in str(e).lower() or "unavailable" in str(e).lower():
            raise XhsBlocked(f"feed {feed_id} blocked by xhs") from e
        raise

    # Check for blocked messages in result
    if isinstance(result, dict):
        raw_text = result.get("raw_text", "")
        msg = result.get("message", "")
        for check_str in [raw_text, msg, str(result.get("data", ""))]:
            if any(w in check_str for w in ["Page Isn't Available", "页面不可访问", "笔记不可访问"]):
                raise XhsBlocked(f"feed {feed_id} blocked: {check_str[:80]}")

    if save_to:
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        Path(save_to).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return result


def list_homepage_feeds(base_url: str = DEFAULT_BASE_URL, timeout: int = 30) -> dict:
    """Fetch the logged-in user's homepage feeds."""
    return _mcp_call_tool("list_feeds", {}, base_url=base_url, timeout=timeout)


# ---------- Convenience: parse profile URL ----------
def parse_profile_url(url: str) -> tuple[str, Optional[str]]:
    """Extract (user_id, xsec_token) from a xhs profile URL."""
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
    """Extract (feed_id, xsec_token) from a xhs note URL."""
    import urllib.parse as up
    import re

    parsed = up.urlparse(url)
    m = re.match(r"/search_result/([0-9a-f]+)", parsed.path)
    if m:
        feed_id = m.group(1)
    else:
        m = re.match(r"/user/profile/[^/]+/([0-9a-f]+)", parsed.path)
        if m:
            feed_id = m.group(1)
        else:
            raise ValueError(f"Cannot extract feed_id from URL: {url}")

    qs = up.parse_qs(parsed.query)
    xsec_token = qs.get("xsec_token", [None])[0]
    return feed_id, xsec_token
