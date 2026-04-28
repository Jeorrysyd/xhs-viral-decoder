# config.yaml 字段说明

## 自动配置（推荐）

```bash
bash scripts/setup_feishu.sh
```

脚本会自动从 lark-cli 读取你的 open_id，创建飞书文件夹获取 folder_token，然后生成填好的 config.yaml。**大多数情况下你不需要手动编辑任何字段。**

## 手动配置

如果你需要手动调整：

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml
```

### 必填字段（自动配置已帮你填好）

| 字段 | 说明 |
|---|---|
| `feishu.folder_token` | 飞书文件夹 token（`setup_feishu.sh` 自动创建并填入） |
| `feishu.grantee_open_id` | 你的飞书 open_id（`setup_feishu.sh` 自动检测并填入） |

### 可选字段

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

## 跨账号场景

如果你有多个小红书账号要分别拆解：

```yaml
defaults:
  persona: ""   # 留空，每次跑命令时显式指定 --persona <name>
```

然后每个 persona 用 `vd persona-init --nickname X` 各生成一份，存到 `persona/` 目录。
