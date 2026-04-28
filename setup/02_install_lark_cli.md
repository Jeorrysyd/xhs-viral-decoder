# 安装 lark-cli（飞书 / Lark 操作工具）

`xhs-viral-decoder` 所有飞书产物（folder / sheet / docx）都通过 [@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli) 推送。

---

## 你只需要做 2 件事

### 第 1 步：创建飞书自建应用

1. 去 [飞书开放平台](https://open.feishu.cn/app) → 创建应用 → 自建应用
2. 拿到 **App ID** 和 **App Secret**（应用凭证页）

### 第 2 步：装 lark-cli + 配好应用

```bash
npm install -g @larksuite/cli
lark-cli config init
```

按提示填：
- App ID
- App Secret
- 身份选 **bot**（最简单）

---

## 然后一键自动完成

```bash
bash ~/.claude/skills/xhs-viral-decoder/scripts/setup_feishu.sh
```

这个脚本会**自动**帮你：
- ✅ 创建飞书文件夹「小红书爆款拆解师」
- ✅ 从 lark-cli 配置中检测你的 open_id
- ✅ 生成 config.yaml 并自动填好所有值

> 不需要手动运行 `lark-cli drive +create-folder` 复制 token，不需要手动查 open_id。脚本全搞定。

---

## scope 权限

`xhs-viral-decoder` 需要这些飞书 API scope：

| Scope | 用途 |
|---|---|
| `space:folder:create` | 建知识库 folder |
| `space:document:create` | 创建 docx |
| `space:document:update` | 更新 docx 内容 |
| `space:document:delete` | 清理无用 docx |
| `docs:document:import` | 导入 xlsx 转原生 sheet |
| `drive:drive:upload` | 上传文件 |
| `drive:drive:move` | 移动文件到 folder |

> **不用提前全开**——跑某个命令缺 scope 时，错误信息里会带「一键开通」URL，点进去授权就行。

---

## 常见问题

### `App scope not enabled: required scope X`

→ 点错误信息里的 URL 一键开通即可。

### `Auth expired`

→ user 身份 token 过期。重新登录：`lark-cli auth login`。bot 身份不会过期（除非你删了 app）。

### 可以不配飞书吗？

→ 可以——把 `config.yaml` 里 `output.push_to_platform` 设为 `false`，所有产物只生成本地 markdown，不推飞书。
