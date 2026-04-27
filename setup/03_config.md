# config.yaml 字段说明

```bash
cp config.example.yaml config.yaml
# 然后编辑 config.yaml
```

## 必填字段

| 字段 | 说明 |
|---|---|
| `feishu.folder_token` | 跑 `lark-cli drive +create-folder` 拿到的 token |
| `feishu.grantee_open_id` | 你的飞书 open_id（bot 产物自动给你授权用） |

## 可选字段

| 字段 | 默认 | 说明 |
|---|---|---|
| `xhs_mcp.url` | `http://localhost:18060` | xhs-mcp HTTP 地址 |
| `feishu.identity` | `bot` | `bot` / `user` |
| `defaults.keywords` | `[情绪管理, 内耗, 自我疗愈]` | viral-pulse / trend-scan 不指定关键词时用 |
| `defaults.niche` | `心理` | 报告标题里的赛道名 |
| `defaults.persona` | 空 | 默认 persona 名（文件 `persona/<name>.json`） |
| `output.base_dir` | `./output` | 本地产物根目录 |
| `output.push_to_platform` | `true` | 设 false 只生成本地 markdown，不推飞书 |

## Slack / Telegram / WhatsApp（STUB）

这三个 adapter 默认 `enabled: false`。要启用看 [adapters/](../adapters/) 下对应文档。

## 在飞书 AI Agent 里调用 skill

skill 在飞书里被调用时，跑的依然是本地的 `xhs-viral-decoder/` —— 飞书 Agent 通过 Claude Code 触发 skill，所以 `config.yaml` 在你的本机上配置即可。

## 跨账号场景

如果你有多个小红书账号要分别拆解：

```yaml
defaults:
  persona: ""   # 留空，每次跑命令时显式指定 --persona <name>
```

然后每个 persona 用 `xhs-persona-synth --nickname X` 各生成一份，存到 `persona/` 目录。

调用时指定：
```
「按 persona X 改写本周爆款」
「按 persona Y 改写本周爆款」
```
