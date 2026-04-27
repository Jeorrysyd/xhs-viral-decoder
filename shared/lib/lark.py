"""Subprocess wrapper for lark-cli (@larksuite/cli).

Wraps the most-used lark-cli commands with structured error handling
so callers don't need to parse JSON responses or shell errors.
"""
import json
import subprocess
import re
import shlex
from pathlib import Path
from typing import Optional


class LarkError(Exception):
    """Base for lark-cli errors."""

    def __init__(self, message: str, scope_url: Optional[str] = None):
        super().__init__(message)
        self.scope_url = scope_url


class LarkScopeMissing(LarkError):
    """Bot lacks a required scope. `scope_url` is the one-click grant URL."""
    pass


class LarkAuthExpired(LarkError):
    """User token expired. Caller should run `lark-cli auth login`."""
    pass


def _run(args: list, input_data: Optional[str] = None, cwd: Optional[str] = None) -> dict:
    """Run lark-cli command, parse JSON response.

    Raises LarkScopeMissing / LarkAuthExpired with hints.
    """
    cmd = ["lark-cli"] + args
    proc = subprocess.run(
        cmd,
        input=input_data,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = proc.stdout
    # lark-cli prints proxy warnings to stderr; we only care about stdout for JSON
    # but also need stderr for error context
    err = proc.stderr

    # Try to extract JSON from stdout (lark-cli sometimes prepends warnings/notes)
    json_match = re.search(r"\{[\s\S]+\}\s*$", out)
    if not json_match:
        raise LarkError(
            f"lark-cli {' '.join(args[:2])} returned non-JSON: stdout={out[:300]!r} stderr={err[:300]!r}"
        )

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        raise LarkError(f"Could not parse lark-cli JSON: {e}\nRaw: {json_match.group(0)[:500]}") from e

    if not data.get("ok"):
        error = data.get("error", {})
        msg = error.get("message", "unknown lark error")
        scope_url = None
        if "scope" in msg.lower() or "scope" in error.get("type", "").lower():
            # look for hint URL
            hint = error.get("hint", "") + " " + error.get("console_url", "")
            url_match = re.search(r"https://open\.feishu\.cn/[^\s\"]+", hint)
            scope_url = url_match.group(0) if url_match else None
            raise LarkScopeMissing(
                f"Missing scope: {msg}. Grant: {scope_url or 'see lark-cli output'}",
                scope_url=scope_url,
            )
        if "auth" in msg.lower() or "token" in msg.lower():
            raise LarkAuthExpired(f"Auth expired: {msg}")
        raise LarkError(f"lark-cli error: {msg} | full: {error}")

    return data.get("data", {})


# ---------- Drive operations ----------
def create_folder(name: str, parent_folder_token: str = None, identity: str = "bot") -> str:
    """Create a folder. Returns folder_token."""
    args = ["drive", "+create-folder", "--as", identity, "--name", name]
    if parent_folder_token:
        args += ["--folder-token", parent_folder_token]
    data = _run(args)
    return data["folder_token"]


def upload_file(file_path: str, folder_token: str = None, identity: str = "bot") -> str:
    """Upload local file to drive. Returns file_token.

    NOTE: lark-cli requires --file as relative path. Caller should cd or pre-cwd.
    """
    p = Path(file_path)
    args = ["drive", "+upload", "--as", identity, "--file", f"./{p.name}"]
    if folder_token:
        args += ["--folder-token", folder_token]
    data = _run(args, cwd=str(p.parent))
    return data["file_token"]


def import_xlsx_as_sheet(
    xlsx_path: str,
    name: str,
    folder_token: str = None,
    identity: str = "bot",
) -> str:
    """Import .xlsx as native feishu sheet. Returns sheet token."""
    p = Path(xlsx_path)
    args = [
        "drive",
        "+import",
        "--as",
        identity,
        "--file",
        f"./{p.name}",
        "--type",
        "sheet",
        "--name",
        name,
    ]
    if folder_token:
        args += ["--folder-token", folder_token]
    data = _run(args, cwd=str(p.parent))
    return data["token"]


def delete(file_token: str, file_type: str, identity: str = "bot") -> bool:
    """Delete a drive file/folder/doc. Returns True on success."""
    args = [
        "drive",
        "+delete",
        "--as",
        identity,
        "--file-token",
        file_token,
        "--type",
        file_type,
        "--yes",
    ]
    _run(args)
    return True


def move(file_token: str, file_type: str, folder_token: str, identity: str = "bot") -> bool:
    """Move a drive file/folder to another folder."""
    args = [
        "drive",
        "+move",
        "--as",
        identity,
        "--file-token",
        file_token,
        "--type",
        file_type,
        "--folder-token",
        folder_token,
    ]
    _run(args)
    return True


# ---------- Docs operations ----------
def create_doc(
    title: str,
    markdown: str,
    folder_token: str = None,
    identity: str = "bot",
) -> str:
    """Create a feishu docx from markdown content. Returns doc_id (token)."""
    # lark-cli docs +create accepts --markdown @file syntax
    # Write markdown to a temp file
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(markdown)
        md_path = f.name

    p = Path(md_path)
    args = [
        "docs",
        "+create",
        "--as",
        identity,
        "--title",
        title,
        "--markdown",
        f"@./{p.name}",
    ]
    if folder_token:
        args += ["--folder-token", folder_token]
    try:
        data = _run(args, cwd=str(p.parent))
        return data["doc_id"]
    finally:
        try:
            Path(md_path).unlink()
        except OSError:
            pass


def update_doc_overwrite(doc_token: str, markdown: str, identity: str = "bot") -> bool:
    """Overwrite full content of an existing docx."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(markdown)
        md_path = f.name

    p = Path(md_path)
    args = [
        "docs",
        "+update",
        "--as",
        identity,
        "--doc",
        doc_token,
        "--markdown",
        f"@./{p.name}",
        "--mode",
        "overwrite",
    ]
    try:
        _run(args, cwd=str(p.parent))
        return True
    finally:
        try:
            Path(md_path).unlink()
        except OSError:
            pass


def fetch_doc_outline(doc_token: str, identity: str = "bot") -> str:
    """Return doc outline (just headings, for verification)."""
    args = [
        "docs",
        "+fetch",
        "--as",
        identity,
        "--doc",
        doc_token,
        "--scope",
        "outline",
        "--format",
        "pretty",
    ]
    proc = subprocess.run(
        ["lark-cli"] + args, capture_output=True, text=True, encoding="utf-8"
    )
    return proc.stdout
