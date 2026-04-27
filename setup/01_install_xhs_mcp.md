# 安装 xhs-mcp（小红书数据抓取服务）

`xhs-viral-decoder` 所有数据抓取都依赖 [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)。

---

## 1. 下载 binary（macOS arm64）

```bash
mkdir -p ~/tools/xiaohongshu-mcp && cd ~/tools/xiaohongshu-mcp
curl -L -o xhs-mcp.tar.gz \
  https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-darwin-arm64.tar.gz
tar xzf xhs-mcp.tar.gz
chmod +x xiaohongshu-mcp-darwin-arm64 xiaohongshu-login-darwin-arm64
```

如果是其他平台（intel macOS / linux / windows），去 [releases 页](https://github.com/xpzouying/xiaohongshu-mcp/releases/latest) 找对应版本。

## 2. 解决 macOS Gatekeeper 拦截

```bash
xattr -d com.apple.quarantine xiaohongshu-mcp-darwin-arm64
xattr -d com.apple.quarantine xiaohongshu-login-darwin-arm64
```

## 3. 扫码登录

```bash
cd ~/tools/xiaohongshu-mcp
./xiaohongshu-login-darwin-arm64
```

会弹出二维码窗口。**用你的小红书 app 扫码登录**——`xhs-viral-decoder` 后面所有抓取都用这个账号身份。

> ⚠️ 建议用一个**专门的小号**登录，不要用主号。如果主号被风控会很麻烦。

登录成功后，cookies 保存到 `cookies.json`，可以重复用。

## 4. 启动 MCP 服务

```bash
cd ~/tools/xiaohongshu-mcp
./xiaohongshu-mcp-darwin-arm64 &
```

服务会在 `localhost:18060` 监听。验证：

```bash
curl http://localhost:18060/health
# 期望: {"success":true,"data":{"account":"<your account>","service":"xiaohongshu-mcp","status":"healthy"}}
```

## 5. （可选）注册 MCP 到 Claude Code

如果你想在 Claude Code 里直接用 `mcp__xiaohongshu-mcp__*` 工具调试：

```bash
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp
claude mcp list   # 验证
```

> 注意：`xhs-viral-decoder` skill 通过 HTTP 直接调 MCP 服务（绕开 token 截断），**不依赖**这一步注册。这一步只是给你手动调试用。

---

## Cookie 维护

cookies.json 会过期（一般 1-2 周）。每次调用挂超时 / 报登录错误时：

```bash
cd ~/tools/xiaohongshu-mcp
./xiaohongshu-login-darwin-arm64   # 重新扫码
```

服务不需要重启——它会自动 reload cookies.json。

## 验证 xhs-mcp 已就位

```bash
curl -X POST http://localhost:18060/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"keyword":"内耗","filters":{"sort_by":"最多点赞"}}' \
  | python3 -m json.tool | head -20
# 期望返回 feeds 数组
```
