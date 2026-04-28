# 小红书爆款拆解师 · xhs-viral-decoder

> **6 个组合式 Claude Skill**，把"看大博主拆爆款 → 做选题 → 出飞书文档"这条路径自动化。
>
> 给做品牌营销的、小红书自媒体创作者、内容运营者用。兼容 Claude Code / Codex CLI / Cursor / Windsurf 等支持 Agent Skills 规范的 AI 工具。配好飞书 CLI 后，**结果通过 lark-cli 直接出到你的飞书云盘**（不配也能跑，但只能拿到本地 JSON）。

作者：Joyce ([@真相拆解师](https://www.xiaohongshu.com/user/profile/67ff1829000000000d008a98)，173 粉 / 100% 图文实验)

---

## 一图看懂

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   你说话 ──→  AI Agent (Claude)  ──→  xhs-viral-decoder 6 子 skill │
│                                              │                      │
│                                              ▼                      │
│                                       ┌──────────────┐              │
│                                       │  飞书云盘    │              │
│                                       │  自动产出文档│              │
│                                       └──────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6 个子 Skill

| Skill | 你这样说，它就触发 | 产出（飞书 docx + sheet） |
|---|---|---|
| 🔥 **[xhs-viral-pulse](skills/xhs-viral-pulse/SKILL.md)** | 「跑下本周 X/Y/Z 关键词的爆款周报」 | 5 节爆款周报 + 58 行数据表 |
| 🔍 **[xhs-account-decompose](skills/xhs-account-decompose/SKILL.md)** | 「深度拆解这个博主：<url>」 | 5 节单号深度拆解 |
| 🕸️ **[xhs-matrix-identify](skills/xhs-matrix-identify/SKILL.md)** | 「找下这赛道有哪些矩阵号」 | 轻矩阵 vs 重矩阵对照 + 你的 2 号方案 |
| 👤 **[xhs-persona-synth](skills/xhs-persona-synth/SKILL.md)** | 「我账号是 X，自动生成 persona」 | 人设档案 JSON + 飞书可编辑 docx |
| ✍️ **[xhs-viral-rewrite](skills/xhs-viral-rewrite/SKILL.md)** | 「把刚才的爆款用我人设改写一遍」 | 30 条 Carol-style bespoke 改写 |
| 🌱 **[xhs-trend-scan](skills/xhs-trend-scan/SKILL.md)** | 「本周冒出哪些新概念词」 | TOP 10 新概念词 + 趋势 + 行动建议 |

每个 sub-skill **独立可触发**，也可以**在自然语言里串起来**：

> 「先跑本周宠物赛道爆款，再用我人设改写一遍，最后告诉我哪些是新概念词」
>
> → Claude 自动按序触发 viral-pulse → viral-rewrite → trend-scan
>
> 适用于任何赛道：心理 / 美妆 / 穿搭 / 宠物 / 旅行 / 职场 / 母婴 / 科技 …

---

## 在你的 AI Agent 里装

### Claude Code（推荐）
```bash
git clone https://github.com/Jeorrysyd/xhs-viral-decoder \
  ~/.claude/skills/xhs-viral-decoder
```

### Codex CLI
```bash
git clone https://github.com/Jeorrysyd/xhs-viral-decoder \
  ~/.codex/skills/xhs-viral-decoder
```

### Cursor / Windsurf / Cline（MCP-aware Agent）
暂未做 MCP wrapper——当前用下面的 paste-prompt 方式即可。

### 国内 AI Agent（豆包 / Floatboat / WorkBuddy 等）
把这段话粘给 AI:

> 帮我装这个 skill，里面有 6 个小红书爆款拆解的子能力。装在标准 skills 目录，并按它的 setup/ 文档帮我装好两个依赖（xhs-mcp + lark-cli）：
> https://github.com/Jeorrysyd/xhs-viral-decoder

### 前置依赖
本 skill 需要两个外部工具，**首次安装按下面「5 分钟上手」走一遍即可**：
- **xhs-mcp**（数据抓取）→ [setup/01_install_xhs_mcp.md](setup/01_install_xhs_mcp.md)
- **lark-cli**（飞书输出）→ 只需 `npm install -g @larksuite/cli` + `lark-cli config init`，然后跑 `scripts/setup_feishu.sh` 一键完成

---

## 5 分钟上手

### Step 1 · Clone + 装数据源

```bash
# clone skill
git clone https://github.com/Jeorrysyd/xhs-viral-decoder ~/.claude/skills/xhs-viral-decoder

# 装 Python 依赖
pip install openpyxl

# 装 xhs-mcp（小红书数据抓取），详见 setup/01
# macOS arm64 一行搞定：
mkdir -p ~/tools/xiaohongshu-mcp && cd ~/tools/xiaohongshu-mcp
curl -L -o xhs-mcp.tar.gz \
  https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64.tar.gz
tar xzf xhs-mcp.tar.gz && chmod +x xiaohongshu-*
xattr -d com.apple.quarantine xiaohongshu-*          # macOS 解锁
./xiaohongshu-login-darwin-arm64                      # 扫码登录小红书
./xiaohongshu-mcp-darwin-arm64 &                      # 后台启动
```

### Step 2 · 飞书一键配置

只需要**两个前置操作**（[详细说明](setup/02_install_lark_cli.md)）：

1. 去 [飞书开放平台](https://open.feishu.cn/app) 创建自建应用，拿到 **App ID** + **App Secret**
2. 终端里配好 lark-cli：

```bash
npm install -g @larksuite/cli
lark-cli config init        # 填 App ID + App Secret，身份选 bot
```

然后**一键搞定剩下所有**（自动创建飞书文件夹 + 自动检测 open_id + 自动生成 config.yaml）：

```bash
bash ~/.claude/skills/xhs-viral-decoder/scripts/setup_feishu.sh
```

> 不需要手动复制 folder_token，不需要手动查 open_id，脚本全部自动完成。

### Step 3 · 验证 & 开跑

```bash
bash ~/.claude/skills/xhs-viral-decoder/tests/verify_install.sh
# 期望：6/6 sub-skills ✓ | xhs-mcp ✓ | lark-cli ✓ | config.yaml ✓
```

在 Claude Code（或飞书 AI agent）里说：

> 「我账号是『真相拆解师』，帮我生成 persona」

Claude 自动触发 `xhs-persona-synth`，产出落到你的飞书文件夹。

---

## 调用范例（在飞书 AI agent 里复制即用）

```
帮我生成 persona — 我昵称叫「<你的昵称>」

跑下本周「美妆 / 护肤 / 成分党」三个关键词的爆款周报

把刚才那份爆款用我人设改写一遍

深度拆解我家品牌赛道这个对标号：https://www.xiaohongshu.com/user/profile/<id>?xsec_token=<token>

找下母婴赛道有哪些矩阵号 — 用 <url> 这个博主做对照

本周冒出哪些新概念词，按知识付费赛道
```

---

## 多平台输出

| 平台 | 状态 | 文档 |
|---|---|---|
| 飞书 | ✅ 完整 | [adapters/feishu.md](adapters/feishu.md) |
| Slack | 🚧 STUB（接口 + 实现指南） | [adapters/slack.md](adapters/slack.md) |
| Telegram | 🚧 STUB | [adapters/telegram.md](adapters/telegram.md) |
| WhatsApp | 🚧 STUB（需 Twilio 付费） | [adapters/whatsapp.md](adapters/whatsapp.md) |

---

## 架构

```
xhs-viral-decoder/
├── skills/                        ← 6 个独立 sub-skill（每个自己有 SKILL.md）
├── shared/                        ← 共享 lib + reference + data
│   ├── lib/                       ← Python 模块（xhs / lark / analyze / persona / rewrite / trend / report）
│   ├── reference/                 ← 6-stratum lens / 标题公式库 / 痛点桶
│   └── data/                      ← 5000 高频中文词 baseline
├── setup/                         ← 用户首次配置文档
├── adapters/                      ← 输出平台 adapter 文档（飞书完整 + 3 stub）
├── examples/                      ← 6 套示例产物
├── tests/                         ← 安装验证脚本
└── config.example.yaml
```

---

## 设计原则

1. **6 个 sub-skill 独立 + 互可调** — 每个独立触发，关键词不冲突；可以串起来
2. **飞书 first-class** — 默认推飞书，因为这是中文创作者的主要协作面
3. **用户主动触发** — 不内置 cron，Claude Code 用户可以用 `/schedule` 单独配
4. **prompt-template + LLM 协同** — rewrite 等高自由度任务，不用规则代码（输出会重复），靠 prompt 让 in-conversation Claude 出 bespoke 内容
5. **6-stratum lens** — persona 不是简单 NLP，是按"小红书圈层视角"理解。reference 里附了一份心理 / 成长 / 职场赛道的 6 子圈层 showcase，其他赛道用同样方法换名即可。

---

## 贡献

- 提 issue 报问题或建议
- 实现一个 adapter（Slack / Telegram / WhatsApp）
- 提交你赛道的 stratum guide showcase 给 reference 库

---

## License

MIT — see [LICENSE](LICENSE).

---

## 致谢

灵感来源：原视频博主拆解小红书爆款的 AI 工作流；萧萧 Carol 的「推荐改编方向」列；谢胜子 13 号矩阵识别范式。技术栈：[xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) + [@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli)。
