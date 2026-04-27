# Troubleshooting FAQ

## xhs-mcp 相关

### `XhsLoginRequired`
**症状**：跑任何抓取命令报 login required。
**原因**：cookies.json 过期。
**解决**：
```bash
cd ~/tools/xiaohongshu-mcp
./xiaohongshu-login-darwin-arm64
```

### `Cannot reach xhs-mcp at http://localhost:18060`
**原因**：服务没启动。
**解决**：
```bash
cd ~/tools/xiaohongshu-mcp
./xiaohongshu-mcp-darwin-arm64 &
# 等几秒后:
curl http://localhost:18060/health
```

### `XhsBlocked: feed XXX blocked`
**症状**：拉某条笔记 detail 时返回「Sorry, This Page Isn't Available Right Now.」
**原因**：xhs 风控。这条笔记被标记，临时不可访问。
**解决**：
- 这是正常的，不影响整体。`xhs-viral-pulse` 会跳过失败的笔记继续跑
- 如果 TOP 1/2 都被屏蔽，`xhs-account-decompose` 会自动降级用 TOP 3-5
- 如果一大半都被屏蔽，可能是你的小号触发了风控——换个账号扫码

### MCP 工具响应被截断
**症状**：直接调 `mcp__xiaohongshu-mcp__user_profile` 报「result exceeds maximum allowed tokens」。
**原因**：MCP 工具有 25k token 响应限制。
**解决**：`xhs-viral-decoder` 的 `xhs.py` 自动绕开这个，直接 HTTP 调用 + 落盘到本地文件。所以 skill 内部跑没问题；只在你手动调 MCP 工具时会遇到。

## lark-cli 相关

### `LarkScopeMissing: required scope X`
**原因**：bot 缺 scope。
**解决**：错误里有「一键开通 URL」，点进去授权即可。常见缺失 scope：
- `space:folder:create`
- `docs:document:import`
- `space:document:delete`

可以一次性全开：见 [02_install_lark_cli.md](02_install_lark_cli.md)。

### `LarkAuthExpired`
**原因**：user 身份 token 过期。
**解决**：
```bash
lark-cli auth login   # 在交互终端运行
```
Bot 身份不会过期，可以全程用 `--as bot` 避免这个问题。

### `unsafe file path: --file must be a relative path`
**原因**：lark-cli 要求 `--file` 是相对路径。
**解决**：`xhs.py` 和 `lark.py` 已自动处理（`cd` 到文件目录）。如果你直接调 lark-cli 报这个，先 `cd` 到文件所在目录再用 `./文件名`。

### `permission denied`
**原因**：bot 创建的 doc 没自动给你授权（极少见）。
**解决**：
```bash
lark-cli drive permission.members create \
  --as bot \
  --params '{"token":"<doc_token>","type":"docx","need_notification":false}' \
  --data '{"member_type":"openid","member_id":"<your_open_id>","perm":"edit","perm_type":"container","type":"user"}'
```

## Skill 触发相关

### Claude 不自动触发某个 skill
**原因**：description 关键词没覆盖你说话的方式。
**解决**：
1. 用更明确的关键词（用 SKILL.md 描述里的触发词）
2. 直接说「用 xhs-viral-pulse 帮我跑下…」显式调用
3. 修改对应 SKILL.md 的 description，加你常用的说法

### Claude 触发了错误的 skill
**原因**：多个 sub-skill 关键词重叠。
**解决**：
- 不应该常发生（每个 SKILL.md 关键词设计已尽量正交）
- 如果某个用法反复触错，调整关键词
- 显式说「用 xhs-X 跑」可以强制指定

## Persona 相关

### `needs_user_review: true` 标志
**这是设计**：自动 synth 出来的 persona 必须人工核对一遍——它根据公开 bio + 笔记标题猜的，可能漏关键身份信息（特别是 story_assets）。

**修复方式**：
- 直接编辑 `persona/<name>.json`
- 或在飞书里编辑 `[人设档案] <name>` docx 然后跑 `vd persona-sync --from-feishu --nickname <name>`

### Persona 自动归到错误的子圈层
**原因**：bio 信号弱 + 你的内容混合多种类型。
**解决**：手动改 `persona/<name>.json` 的 `_synthesis_notes` 顶部，强制 substratum，然后 rerun。

## Rewrite 相关

### Rewrite 输出 < 30 条
**原因**：Claude 响应被截断或没按格式输出。
**解决**：在 chat 里说「rewrite 只给了 N 条，请补全到 30 条 + JSON 格式」。

### Rewrite 输出有重复
**原因**：Claude 用了模板替换而非 bespoke 生成。
**解决**：Skill 自动检测重复 + 提示重跑。手动告知 Claude「每条改写必须不一样，不能模板替换」。

### Rewrite 违反 persona 约束（用了「教你」「拯救」）
**原因**：constraints 不明显。
**解决**：在 `persona/<name>.json` 的 `constraints` 里把红线写得更具体：
- ❌「不要俯视语气」 → ✅「禁止使用：教你 / 救你 / 必须 / 一定要」

## Trend 相关

### TOP 10 都是常见词（焦虑、内耗）
**原因**：common_lexicon.txt 没收录这些词。
**解决**：
1. 编辑 `shared/data/common_lexicon.txt`，加上这些词
2. 重跑命令

### 一条 emerging concept 都没找出来
**原因**：当周数据样本不够 / 没有真的新词。
**解决**：
- 加大 `--window-days`
- 增加 `--keywords` 数量
- 或者就是真的没有——这是有效的负面信号

## 跨平台

### 我能不能不用飞书？
能。设 `config.yaml::output.push_to_platform: false`，所有产物只生成本地 markdown。

### Slack / Telegram 怎么用？
看 [adapters/slack.md](../adapters/slack.md) 或 [adapters/telegram.md](../adapters/telegram.md)。**目前只是 STUB**——需要你或社区贡献者实现。
