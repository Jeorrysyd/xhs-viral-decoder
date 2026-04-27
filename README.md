# 小红书爆款拆解师 · xhs-viral-decoder

> **Claude Skill 工具包** — 6 个组合式 sub-skill，把"看大博主拆爆款 → 做选题 → 落地飞书文档"这条路径自动化。
>
> 给小红书自媒体、内容创业者、社交媒体运营者用。在飞书 / Slack / Telegram 里跟 AI Agent 自然语言聊，结果直接落到你的飞书云盘。

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

> 「先跑本周心理赛道爆款，再用我人设改写一遍，最后告诉我哪些是新概念词」
>
> → Claude 自动按序触发 viral-pulse → viral-rewrite → trend-scan

---

## 5 分钟上手

### 1. 安装

```bash
# clone 到 Claude Code 的 skills 目录
git clone https://github.com/<your>/xhs-viral-decoder ~/.claude/skills/xhs-viral-decoder

# 或者本地链接
ln -s /path/to/xhs-viral-decoder ~/.claude/skills/xhs-viral-decoder
```

### 2. 装依赖（一次性）

需要两个外部工具：
- **xhs-mcp** — 抓小红书数据（[setup/01_install_xhs_mcp.md](setup/01_install_xhs_mcp.md)）
- **lark-cli** — 推飞书（[setup/02_install_lark_cli.md](setup/02_install_lark_cli.md)）

5 分钟跑通：[setup/00_quickstart.md](setup/00_quickstart.md)

### 3. 配置

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml — 主要填 feishu.folder_token + grantee_open_id
```

字段说明：[setup/03_config.md](setup/03_config.md)

### 4. 验证安装

```bash
bash ~/.claude/skills/xhs-viral-decoder/tests/verify_install.sh
# 期望输出：6/6 sub-skills detected | xhs-mcp: ✓ | lark-cli: ✓ | config.yaml: ✓
```

### 5. 跑第一个 workflow

在 Claude Code（或飞书 AI agent）里说：

> 「我账号是『真相拆解师』，帮我生成 persona」

Claude 应该自动触发 `xhs-persona-synth`，产出落到你的飞书 folder。

---

## 调用范例（在飞书 AI agent 里复制即用）

```
帮我生成 persona — 我昵称叫「<你的昵称>」

跑下本周「情绪管理 / 内耗 / 自我疗愈」三个关键词的爆款周报

把刚才那份爆款用我人设改写一遍

深度拆解这个博主：https://www.xiaohongshu.com/user/profile/<id>?xsec_token=<token>

找下心理赛道有哪些矩阵号 — 用 <url> 这个博主做对照

本周冒出哪些新概念词，按心理赛道
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
5. **6-stratum lens** — persona 不是简单 NLP，是按"小红书圈层视角"理解（认知派/治愈派/干货派/心理学派/女性成长派/生活感叙事派）

---

## 当前赛道支持

主航道：**心理 / 成长 / 职场 / 内耗** 类账号。

扩展点（在 `shared/reference/xhs_stratum_guide.md` 里新增子圈层）：
- 美食（粉丝调性 / 探店派 / 烹饪派）— 待社区贡献
- 穿搭（OOTD / 通勤穿搭 / 学院风）— 待社区贡献
- AI 工具 / 编程（已有部分笔记，待形成圈层 lens）

---

## 贡献

- 提 issue 报问题或建议
- 实现一个 adapter（Slack / Telegram / WhatsApp）
- 加一个新赛道的 stratum guide
- 增强 `xhs_stratum_guide.md` 的子圈层判定准确度

---

## License

MIT — see [LICENSE](LICENSE).

---

## 致谢

灵感来源：原视频博主拆解小红书爆款的 AI 工作流；萧萧 Carol 的「推荐改编方向」列；谢胜子 13 号矩阵识别范式。技术栈：[xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) + [@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli)。
