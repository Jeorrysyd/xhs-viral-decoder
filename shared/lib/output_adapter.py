"""Output adapters for different platforms.

Abstract base + concrete implementations:
- FeishuAdapter: complete (uses lark.py wrapper)
- SlackAdapter: STUB
- TelegramAdapter: STUB
- WhatsappAdapter: STUB

Each adapter has same interface so workflows are platform-agnostic.
"""
from typing import Optional


class OutputAdapter:
    """Abstract base. Concrete adapters implement these methods."""

    name = "abstract"

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        """Create a doc/page with markdown content. Returns identifier (token/id/url)."""
        raise NotImplementedError

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        """Upload xlsx as a native sheet. Returns identifier."""
        raise NotImplementedError

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        """Overwrite an existing doc with new markdown. Returns success."""
        raise NotImplementedError

    def create_folder(self, name: str, parent: str = None) -> str:
        """Create a folder/channel/etc. Returns identifier."""
        raise NotImplementedError

    def grant_user(self, item_token: str, user_identifier: str) -> bool:
        """Grant a user access to an item. Returns success."""
        raise NotImplementedError


# ============== Feishu (complete) ==============
class FeishuAdapter(OutputAdapter):
    """Feishu / Lark adapter using lark-cli subprocess wrapper."""

    name = "feishu"

    def __init__(self, identity: str = "bot", folder_token: str = None, grantee_open_id: str = None):
        self.identity = identity
        self.folder_token = folder_token
        self.grantee_open_id = grantee_open_id

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        from . import lark
        return lark.create_doc(
            title=title,
            markdown=markdown,
            folder_token=folder_token or self.folder_token,
            identity=self.identity,
        )

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        from . import lark
        return lark.import_xlsx_as_sheet(
            xlsx_path=xlsx_path,
            name=title,
            folder_token=folder_token or self.folder_token,
            identity=self.identity,
        )

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        from . import lark
        return lark.update_doc_overwrite(doc_token=doc_token, markdown=markdown, identity=self.identity)

    def create_folder(self, name: str, parent: str = None) -> str:
        from . import lark
        return lark.create_folder(name=name, parent_folder_token=parent, identity=self.identity)

    def delete(self, file_token: str, file_type: str) -> bool:
        from . import lark
        return lark.delete(file_token=file_token, file_type=file_type, identity=self.identity)

    def move(self, file_token: str, file_type: str, folder_token: str = None) -> bool:
        from . import lark
        return lark.move(
            file_token=file_token,
            file_type=file_type,
            folder_token=folder_token or self.folder_token,
            identity=self.identity,
        )

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        # lark-cli auto-grants on bot-created docs (returns permission_grant in response).
        # For explicit grant on existing items, would call drive permission.members create.
        # No-op here since the create flow handles it.
        return True


# ============== Slack (STUB) ==============
class SlackAdapter(OutputAdapter):
    """Slack adapter — STUB. See adapters/slack.md for implementation guide."""

    name = "slack"

    def __init__(self, webhook_url: str = None, channel: str = None, **kwargs):
        self.webhook_url = webhook_url
        self.channel = channel

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        raise NotImplementedError(
            "SlackAdapter is a stub. See adapters/slack.md for implementation guide. "
            "Recommended: post markdown summary as Slack Block Kit message + upload full report as file."
        )

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        raise NotImplementedError("Slack: upload xlsx via files.upload API. See adapters/slack.md.")

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        raise NotImplementedError("Slack messages are immutable. Post a new message instead.")

    def create_folder(self, name: str, parent: str = None) -> str:
        raise NotImplementedError("Slack uses channels not folders. Map name → channel.")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True  # channels handle access


# ============== Telegram (STUB) ==============
class TelegramAdapter(OutputAdapter):
    """Telegram adapter — STUB. See adapters/telegram.md."""

    name = "telegram"

    def __init__(self, bot_token: str = None, chat_id: str = None, **kwargs):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        raise NotImplementedError(
            "TelegramAdapter is a stub. See adapters/telegram.md. "
            "Recommended: send title as message + upload markdown as document attachment."
        )

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        raise NotImplementedError("Telegram: send xlsx via sendDocument API.")

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        raise NotImplementedError("Telegram messages can be edited within 48h. Use editMessageText.")

    def create_folder(self, name: str, parent: str = None) -> str:
        raise NotImplementedError("Telegram has no folders. Use a chat or channel.")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True


# ============== WhatsApp (STUB, requires Twilio) ==============
class WhatsappAdapter(OutputAdapter):
    """WhatsApp adapter — STUB. Requires Twilio Business account ($). See adapters/whatsapp.md."""

    name = "whatsapp"

    def __init__(self, twilio_sid: str = None, twilio_token: str = None, to_number: str = None, **kwargs):
        self.twilio_sid = twilio_sid
        self.twilio_token = twilio_token
        self.to_number = to_number

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        raise NotImplementedError(
            "WhatsappAdapter is a stub. Requires Twilio Business account (paid). "
            "See adapters/whatsapp.md for setup."
        )

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        raise NotImplementedError("WhatsApp via Twilio: media upload requires public URL.")

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        raise NotImplementedError("WhatsApp messages are immutable.")

    def create_folder(self, name: str, parent: str = None) -> str:
        raise NotImplementedError("WhatsApp has no folders.")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True


# ---------- Factory ----------
ADAPTERS = {
    "feishu": FeishuAdapter,
    "slack": SlackAdapter,
    "telegram": TelegramAdapter,
    "whatsapp": WhatsappAdapter,
}


def get_adapter(name: str, config) -> OutputAdapter:
    """Return adapter instance configured from a Config object."""
    if name not in ADAPTERS:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(ADAPTERS)}")

    cls = ADAPTERS[name]
    section = getattr(config, name, None)

    if name == "feishu":
        return cls(
            identity=getattr(section, "identity", "bot") if section else "bot",
            folder_token=getattr(section, "folder_token", None) if section else None,
            grantee_open_id=getattr(section, "grantee_open_id", None) if section else None,
        )
    elif name == "slack":
        return cls(
            webhook_url=getattr(section, "webhook_url", None) if section else None,
            channel=getattr(section, "channel", None) if section else None,
        )
    elif name == "telegram":
        return cls(
            bot_token=getattr(section, "bot_token", None) if section else None,
            chat_id=getattr(section, "chat_id", None) if section else None,
        )
    elif name == "whatsapp":
        return cls(
            twilio_sid=getattr(section, "twilio_sid", None) if section else None,
            twilio_token=getattr(section, "twilio_token", None) if section else None,
            to_number=getattr(section, "to_number", None) if section else None,
        )
    return cls()
