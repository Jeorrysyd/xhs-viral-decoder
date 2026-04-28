# 5 分钟上手

> 假设你已经 clone 了 repo 到 `~/.claude/skills/xhs-viral-decoder/`。

---

## 3 步跑通

### Step 1 · 装小红书数据源

```bash
mkdir -p ~/tools/xiaohongshu-mcp && cd ~/tools/xiaohongshu-mcp
curl -L -o xhs-mcp.tar.gz \
  https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64.tar.gz
tar xzf xhs-mcp.tar.gz && chmod +x xiaohongshu-*
xattr -d com.apple.quarantine xiaohongshu-*          # macOS 解锁

./xiaohongshu-login-darwin-arm64                      # 扫码登录小红书
./xiaohongshu-mcp-darwin-arm64 &                      # 后台启动
```

详细说明 → [01_install_xhs_mcp.md](01_install_xhs_mcp.md)

### Step 2 · 配飞书（一键自动）

先做 2 件手动操作：

1. 去 [飞书开放平台](https://open.feishu.cn/app) 创建自建应用，拿到 App ID + App Secret
2. 终端配好 lark-cli：

```bash
npm install -g @larksuite/cli
lark-cli config init        # 填 App ID + App Secret，身份选 bot
```

然后一键搞定：

```bash
bash ~/.claude/skills/xhs-viral-decoder/scripts/setup_feishu.sh
```

> 自动创建飞书文件夹 + 自动检测 open_id + 自动生成 config.yaml。

详细说明 → [02_install_lark_cli.md](02_install_lark_cli.md)

### Step 3 · 验证

```bash
bash ~/.claude/skills/xhs-viral-decoder/tests/verify_install.sh
```

期望输出：
```
✓ xhs-mcp service reachable
✓ lark-cli installed
✓ config.yaml found
✓ feishu.folder_token configured
✓ 6/6 sub-skills detected
```

---

## 跑通第一条 workflow

在 Claude Code 里说：

> 「我账号是『<你的小红书昵称>』，帮我生成 persona」

2 分钟内你的飞书文件夹会出现：
- `[人设档案] <你的昵称>_<日期>.docx`
- 本地 `persona/<你的昵称>.json`

---

## 常见首次错误

| 症状 | 原因 | 解决 |
|---|---|---|
| `XhsLoginRequired` | 还没扫码登录 | `cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-login-darwin-arm64` |
| `LarkScopeMissing` | bot 缺 scope | 错误信息里有「一键开通」URL，点进去授权 |
| `Cannot reach xhs-mcp` | 服务没启动 | `cd ~/tools/xiaohongshu-mcp && ./xiaohongshu-mcp-darwin-arm64 &` |
| Skill 不被触发 | description 关键词不够 | check `skills/<name>/SKILL.md` 的 description |

详细排错 → [troubleshooting.md](troubleshooting.md)
