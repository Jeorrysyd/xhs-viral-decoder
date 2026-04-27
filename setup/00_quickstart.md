# 5 分钟上手

> 假设你已经 clone 了 repo 到 `~/.claude/skills/xhs-viral-decoder/`。

---

## Checklist

- [ ] Python 3.9+ + `openpyxl` 包装好（`pip install openpyxl`）
- [ ] `xhs-mcp` 装好 + 扫码登录 → see [01_install_xhs_mcp.md](01_install_xhs_mcp.md)
- [ ] `lark-cli` 装好 + 飞书 app 配好 → see [02_install_lark_cli.md](02_install_lark_cli.md)
- [ ] `config.yaml` 配好 → see [03_config.md](03_config.md)
- [ ] 一键体检通过：

```bash
bash ~/.claude/skills/xhs-viral-decoder/tests/verify_install.sh
```

期望输出：
```
✓ Python ≥ 3.9
✓ openpyxl installed
✓ xhs-mcp service reachable at http://localhost:18060
✓ xhs-mcp logged in (account: <your-account>)
✓ lark-cli installed (version 1.0.x)
✓ config.yaml found
✓ feishu.folder_token configured
✓ 6/6 sub-skills detected:
  - xhs-viral-pulse
  - xhs-account-decompose
  - xhs-matrix-identify
  - xhs-persona-synth
  - xhs-viral-rewrite
  - xhs-trend-scan
```

---

## 跑通第一条 workflow

```
打开 Claude Code，跟它说：

「我账号是『<你的小红书昵称>』，帮我生成 persona」
```

如果 skill 都装对了，Claude 应该自动触发 `xhs-persona-synth`，2 分钟内你的飞书 folder 会出现：
- `[人设档案] <你的昵称>_<日期>.docx`
- 本地 `persona/<你的昵称>.json`

接着可以跑：

```
「跑下『情绪管理 / 内耗 / 自我疗愈』三个关键词的本周爆款周报」

「把刚才的爆款用我人设改写一遍」

「本周冒出哪些新概念词」
```

---

## 常见首次错误

| 症状 | 原因 | 解决 |
|---|---|---|
| `XhsLoginRequired` | 还没扫码登录 | `cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-login-darwin-arm64` |
| `LarkScopeMissing` | bot 缺 scope | 错误信息里有「一键开通」URL，点进去授权 |
| `Cannot reach xhs-mcp at http://localhost:18060` | 服务没启动 | `cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-mcp-darwin-arm64 &` |
| `folder_token configured value is REPLACE_WITH_...` | config.yaml 没改 | `cp config.example.yaml config.yaml` 然后填真实值 |
| Skill 不被自然语言触发 | description 里关键词不够 | check `~/.claude/skills/xhs-viral-decoder/skills/<name>/SKILL.md` 的 description |

详细排错：[troubleshooting.md](troubleshooting.md)
