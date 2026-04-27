# Slack Adapter — STUB（实现指南）

> **状态**：未实现。`SlackAdapter` 类骨架在 `shared/lib/output_adapter.py`，所有方法 raise `NotImplementedError`。
>
> 欢迎 PR 实现。

## 实现路径

### 1. 装依赖

```bash
pip install slack-sdk
```

### 2. 创建 Slack App

1. 去 [api.slack.com/apps](https://api.slack.com/apps) 创建 app
2. 加 OAuth scopes：
   - `chat:write` （发消息）
   - `files:write` （上传文件）
   - `channels:read` （查 channel id）
3. install 到 workspace，拿 `Bot User OAuth Token`

### 3. 配置 config.yaml

```yaml
slack:
  enabled: true
  bot_token: xoxb-...
  channel: "#content-pulse"   # or channel ID like C0123ABC
```

### 4. 实现 SlackAdapter

```python
# shared/lib/output_adapter.py

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackAdapter(OutputAdapter):
    name = "slack"

    def __init__(self, bot_token, channel, **kwargs):
        self.client = WebClient(token=bot_token)
        self.channel = channel

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        # Strategy: post a summary message + upload full report as a file
        # Use Block Kit for nice formatting

        # Truncate markdown to first ~2000 chars for inline preview
        preview = markdown[:2000] + ("\n\n... (truncated, full file attached)" if len(markdown) > 2000 else "")

        try:
            # 1. Post preview message
            msg_resp = self.client.chat_postMessage(
                channel=self.channel,
                text=title,
                blocks=[
                    {"type": "header", "text": {"type": "plain_text", "text": title[:150]}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": preview}},
                ],
            )

            # 2. Upload full markdown as attachment
            file_resp = self.client.files_upload_v2(
                channel=self.channel,
                content=markdown,
                filename=f"{title}.md",
                title=title,
                initial_comment="Full report attached above.",
                thread_ts=msg_resp["ts"],   # post in thread
            )
            return file_resp["file"]["id"]
        except SlackApiError as e:
            raise LarkError(f"Slack push failed: {e.response['error']}")  # rename or use SlackError

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        with open(xlsx_path, "rb") as f:
            file_resp = self.client.files_upload_v2(
                channel=self.channel,
                file=f,
                filename=f"{title}.xlsx",
                title=title,
            )
        return file_resp["file"]["id"]

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        # Slack messages can be edited via chat.update if we tracked the ts
        # For files, can't edit — recommend posting new file with version suffix
        raise NotImplementedError(
            "Slack files are immutable. Recommend: post new file with _v2 suffix."
        )

    def create_folder(self, name: str, parent: str = None) -> str:
        # Slack uses channels not folders — could create a private channel
        try:
            resp = self.client.conversations_create(name=name, is_private=False)
            return resp["channel"]["id"]
        except SlackApiError as e:
            raise LarkError(f"Slack channel create failed: {e.response['error']}")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True  # channel membership handles this
```

## UX 考量

### Markdown 在 Slack 里显示效果

Slack 不完全支持 markdown：
- ✅ `*bold*` `_italic_` `` `code` `` `> blockquote`
- ❌ `# heading` (Slack 用 Block Kit 的 header 实现)
- ❌ `[link](url)` (Slack 用 `<url|text>`)
- ❌ 表格

**建议**：
- 报告主体用 markdown 文件 attach
- 消息正文给一个 1-2 段的 summary + 用 Block Kit header / divider 美化
- 表格保留在 markdown 文件里

### 长报告处理

viral-pulse 报告 ~25k chars，超过 Slack 单条 message 上限。
**策略**：上面的代码用 attachment + thread reply，主消息只放 preview + summary。

### Channel 选择

让用户在 config 里指定 channel，不要 hardcode。或者每个 sub-skill 可以指定不同 channel（高级功能）。

## 测试

```python
adapter = SlackAdapter(
    bot_token="xoxb-...",
    channel="#test-xhs",
)
token = adapter.push_doc(
    title="Test report",
    markdown="# Hello\n\nThis is a test report.\n\n## Section 1\n- item",
)
print(f"Posted: file id = {token}")
```

## 不要做的事

- ❌ 别在 Slack 里发 plain JSON dump（用户看不懂）
- ❌ 别为每个 sub-skill 创建一个新 channel（用户会被 channel 淹没）
- ❌ 别忽略 Slack rate limit（chat.postMessage = 1/sec/channel）

## 完成后

PR 时请：
1. 在 PR 描述里 attach 截图（在你 workspace 里跑出来的样子）
2. 更新 [adapters/feishu.md](feishu.md) 的「关键设计决策」章节，对比 Slack vs 飞书的取舍
3. 在 [README.md](../README.md) 平台支持表格里把 Slack 状态从「STUB」改为「complete」
