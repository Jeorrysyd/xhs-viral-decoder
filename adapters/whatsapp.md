# WhatsApp Adapter — STUB（实现指南，**需付费 Twilio**）

> **状态**：未实现。门槛高 + 付费——除非你是企业用户，建议优先实现 Slack 或 Telegram。

## 为什么 WhatsApp 这么难

WhatsApp 没有公开免费 API。所有自动化访问必须通过：
1. **WhatsApp Business API**（直连——需要 Facebook Business Verification + 行业审核）
2. **第三方 BSP**（最常用：Twilio / Vonage / Meta Cloud API）

`xhs-viral-decoder` 默认走 **Twilio** 方案——文档完整、上手相对快、有 free trial（受限）。

## 成本预估

| 项 | 价格 |
|---|---|
| Twilio account | free trial（限制：只能发给你预先 verify 过的手机号）|
| WhatsApp Business sender | $5-15 / month |
| Per-message conversation | $0.005-0.10（看国家）|
| Approved templates | 必须的，需提交审核 |

## 实现路径

### 1. 创建 Twilio account

[twilio.com/try-twilio](https://www.twilio.com/try-twilio)

### 2. 启用 WhatsApp sandbox（trial）

[Twilio Console > Messaging > Senders > WhatsApp Senders](https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders)

- Trial 模式只能发给已 verify 的号码
- 生产模式需要 Facebook Business Verification + Meta 审核

### 3. 拿凭证

- `Account SID`
- `Auth Token`
- `from` number（Twilio 给你的 sandbox number）

### 4. 装依赖

```bash
pip install twilio
```

### 5. 配置 config.yaml

```yaml
whatsapp:
  enabled: true
  twilio_sid: ACxxx
  twilio_token: xxx
  to_number: "+8613xxxxxxxxx"   # E.164 format
```

### 6. 实现 WhatsappAdapter

```python
# shared/lib/output_adapter.py
from twilio.rest import Client

class WhatsappAdapter(OutputAdapter):
    name = "whatsapp"

    def __init__(self, twilio_sid, twilio_token, to_number, **kwargs):
        self.client = Client(twilio_sid, twilio_token)
        self.to_number = f"whatsapp:{to_number}"
        self.from_number = "whatsapp:+14155238886"  # Twilio sandbox default

    def push_doc(self, title: str, markdown: str, folder_token: str = None) -> str:
        # WhatsApp message limit: 4096 chars
        # For longer, send media (PDF) or chunk

        if len(markdown) <= 1500:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=self.to_number,
                body=f"*{title}*\n\n{markdown}",
            )
            return msg.sid

        # Long message: send title + truncated preview + ask user to ping for more
        preview = markdown[:1200] + "\n\n... (报告太长，完整内容见同时发送的 PDF 附件)"
        msg1 = self.client.messages.create(
            from_=self.from_number,
            to=self.to_number,
            body=f"*{title}*\n\n{preview}",
        )

        # For attachment: need a PUBLIC HTTPS url for the file
        # Twilio doesn't accept local file upload — file must be hosted somewhere first
        # Recommend: convert markdown → PDF → upload to your S3/cloudflare-r2 → pass URL
        # Skipping that for the stub.
        raise NotImplementedError(
            "WhatsApp media: Twilio requires public HTTPS URL. "
            "Implement: markdown → PDF → upload to S3 → pass media_url to messages.create."
        )

    def push_sheet(self, title: str, xlsx_path: str, folder_token: str = None) -> str:
        # Same problem: requires public URL
        raise NotImplementedError("Same as push_doc — need to host xlsx publicly first.")

    def update_doc(self, doc_token: str, markdown: str) -> bool:
        # WhatsApp messages immutable
        raise NotImplementedError("WhatsApp messages cannot be edited.")

    def create_folder(self, name: str, parent: str = None) -> str:
        raise NotImplementedError("WhatsApp has no folders.")

    def grant_user(self, item_token: str, user_identifier: str = None) -> bool:
        return True
```

## 重要限制

### 24 小时窗口规则

WhatsApp 限制：**用户最后一次给 bot 发消息后 24h 内**才能不受限发消息。
超出 24h 必须用 **pre-approved template**。

实际意义：xhs-viral-decoder 不能完全主动推日报——
- 用户必须先在 WhatsApp 里跟 bot 说一句话「今天爆款」
- bot 在 24h 内回复完整报告

或者 setup pre-approved 模板（需 Meta 审核 1-3 天）。

### 文件附件必须公开 URL

Twilio 不支持本地文件上传。你必须：
1. 自建对象存储（S3 / R2 / OSS）
2. markdown → PDF（用 `markdown2 + weasyprint` 或类似）
3. 上传 PDF
4. 拿到公开 HTTPS URL
5. 把 URL 传给 `messages.create(media_url=[url])`

实现成本明显高于 Slack/Telegram。

### 中国地区

WhatsApp 在中国大陆需 proxy 才能用。如果你的目标用户在中国，**Telegram + 飞书更合适**。

## 推荐替代方案

如果你只是想要「在手机 chat 里收日报」：
- **Telegram**：最低成本（免费 + 简单 API）→ 优先实现 [adapters/telegram.md](telegram.md)
- **Slack**：团队使用最方便 → [adapters/slack.md](slack.md)
- **飞书**：中文场景默认（已实现）

## 完成后

PR 时请：
1. 注明使用的 BSP（Twilio / Vonage / 其他）
2. 文档化哪些场景受 24h 窗口限制
3. 截图（包括接收效果 + 媒体附件展示）
4. 更新 README 平台支持表格
5. 更新 setup/03_config.md 加你新加的字段
