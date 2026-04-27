# Telegram Adapter — STUB（实现指南）

> **状态**：未实现。`TelegramAdapter` 类骨架在 `shared/lib/output_adapter.py`，所有方法 raise `NotImplementedError`。

## 实现路径

### 1. 创建 Telegram Bot

1. 在 Telegram 里找 [@BotFather](https://t.me/BotFather)
2. `/newbot` 创建一个 bot，拿到 `bot_token`
3. 把 bot 加到你想接收报告的 chat 里
4. 拿 `chat_id`：
   ```bash
   # 给 bot 发条消息后:
   curl https://api.telegram.org/bot<bot_token>/getUpdates
   # 找到 message.chat.id
   ```

### 2. 配置 config.yaml

```yaml
telegram:
  enabled: true
  bot_token: "1234567890:ABC..."
  chat_id: "-100123456789"   # group chat id (negative) or personal chat id
```

### 3. 实现 TelegramAdapter

```python
# shared/lib/output_adapter.py
import requests

class TelegramAdapter(OutputAdapter):
    name = "telegram"

    def __init__(self, bot_token, chat_id, **kwargs):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        # Strategy: send title as message + upload markdown as document

        # 1. Send title as Markdown message
        title_resp = requests.post(
            f"{self.api_base}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": f"*{self._escape_md(title)}*",
                "parse_mode": "MarkdownV2",
            },
            timeout=30,
        ).json()

        # 2. Send full markdown as document
        files = {"document": (f"{title}.md", markdown.encode("utf-8"), "text/markdown")}
        doc_resp = requests.post(
            f"{self.api_base}/sendDocument",
            data={"chat_id": self.chat_id, "caption": title[:1024]},
            files=files,
            timeout=60,
        ).json()

        if not doc_resp.get("ok"):
            raise LarkError(f"Telegram push failed: {doc_resp.get('description')}")

        return str(doc_resp["result"]["message_id"])

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        with open(xlsx_path, "rb") as f:
            files = {"document": (f"{title}.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            resp = requests.post(
                f"{self.api_base}/sendDocument",
                data={"chat_id": self.chat_id, "caption": title[:1024]},
                files=files,
                timeout=120,
            ).json()
        return str(resp["result"]["message_id"])

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        # Telegram messages can be edited within 48h via editMessageText
        # But documents (attachments) can't be replaced — only the caption
        # For full update, post new document
        resp = requests.post(
            f"{self.api_base}/editMessageText",
            json={
                "chat_id": self.chat_id,
                "message_id": int(doc_token),
                "text": markdown[:4096],   # Telegram message limit
                "parse_mode": "MarkdownV2",
            },
            timeout=30,
        ).json()
        return resp.get("ok", False)

    def create_folder(self, name: str, parent: str = None) -> str:
        # Telegram has no folders. Could create a topic in a forum group.
        raise NotImplementedError("Telegram has no folders. Use a chat or forum topic.")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True

    def _escape_md(self, text: str) -> str:
        # Escape MarkdownV2 special chars
        for ch in r"_*[]()~`>#+-=|{}.!":
            text = text.replace(ch, f"\\{ch}")
        return text
```

## UX 考量

### Markdown 在 Telegram 里显示效果

Telegram 用 MarkdownV2（严格转义）：
- ✅ `*bold*` `_italic_` `__underline__` `~strike~` `||spoiler||`
- ✅ `[link](url)` `` `code` `` `>quote`
- ✅ ``` ```fenced``` ```
- ❌ 表格（要预处理成 plain text）
- ❌ 嵌套引用

**建议**：
- 完整报告用 `.md` document attachment（用户能下载查看）
- 消息正文只发 title + 1 句 summary

### 长内容

Telegram 单条 message 限制 4096 chars。viral-pulse 报告远超。
**必须用 document attachment**——上面的代码已经按这个模式实现。

### Forum topics（高级）

Telegram supergroup 支持 topics（类似 Slack thread）。可以为每个 sub-skill 开一个 topic：
- `xhs-viral-pulse` → topic「📈 周报」
- `xhs-account-decompose` → topic「🔍 拆号」
- 等等

## 测试

```python
adapter = TelegramAdapter(
    bot_token="xxx",
    chat_id="-100xxx",
)
mid = adapter.push_doc(title="测试报告", markdown="# Hello\n\n测试内容")
print(f"Sent: message {mid}")
```

## 注意事项

- Telegram bot **不能主动加你为联系人**——你必须先给 bot 发条消息或加进 group
- group chat_id 是**负数**（例如 -100123456789），personal chat_id 是正数
- bot 在 group 里默认看不到消息（privacy mode），如果要解析用户 reply，需要 `/setprivacy` → Disable
- 国内用户访问 Telegram 需要 proxy

## 完成后

PR 时请：
1. 测试包含表格的 viral-pulse 报告（验证 markdown 转换不破坏）
2. 截图（chat 里的接收效果）
3. 更新 README 平台支持表格
