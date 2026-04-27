# 安装 lark-cli（飞书 / Lark 操作工具）

`xhs-viral-decoder` 所有飞书产物（folder / sheet / docx）都通过 [@larksuite/cli](https://www.npmjs.com/package/@larksuite/cli) 推送。

---

## 1. 装 lark-cli

```bash
npm install -g @larksuite/cli@latest
lark-cli --version   # 应 ≥ 1.0.19
```

## 2. 创建飞书 app

1. 去 [飞书开放平台](https://open.feishu.cn/app) 创建一个「自建应用」
2. 拿到 `App ID` 和 `App Secret`
3. 应用 → 凭证与基础信息 → 复制这两个值

## 3. 配置 lark-cli

```bash
lark-cli config init
```

按提示填：
- App ID
- App Secret
- 默认身份选 `bot`（最简单）

## 4. 申请最小 scope 集合

`xhs-viral-decoder` 跑全套需要的 scope：

| Scope | 用途 |
|---|---|
| `space:folder:create` | 建知识库 folder |
| `space:document:create` | 创建 docx |
| `space:document:update` | 更新 docx 内容 |
| `space:document:delete` | 清理无用 docx |
| `docs:document:import` | 导入 xlsx 转原生 sheet |
| `drive:drive:upload` | 上传文件 |
| `drive:drive:move` | 移动文件到 folder |
| `drive:permission:write` | 给用户授权（可选——bot 创建时通常自动 grant） |

**一键开通 URL（替换 clientID 为你的 App ID）**：

```
https://open.feishu.cn/page/scope-apply?clientID=<YOUR_APP_ID>&scopes=space%3Afolder%3Acreate%2Cspace%3Adocument%3Acreate%2Cspace%3Adocument%3Aupdate%2Cspace%3Adocument%3Adelete%2Cdocs%3Adocument%3Aimport%2Cdrive%3Adrive%3Aupload%2Cdrive%3Adrive%3Amove
```

> 如果跑某个命令时报 `LarkScopeMissing`，错误信息里会自带「一键开通 URL」，点进去授权即可——比一次性全开方便。

## 5. 创建知识库 folder

```bash
lark-cli drive +create-folder --as bot --name "小红书爆款拆解师"
```

输出里有 `folder_token` 字段，**复制这个 token 填到 config.yaml 的 `feishu.folder_token`**。

## 6. 拿你自己的 open_id

```bash
lark-cli contact +get-self --as user
# 或者用你已知的 email/手机号查找
```

复制 `open_id`，填到 `config.yaml` 的 `feishu.grantee_open_id`。这样 bot 创建的所有产物会自动给你 grant 可管理权限。

## 7. 验证

```bash
lark-cli docs +create --as bot --title "test_xhs_skill" --markdown "# hello"
# 期望: ok=true, 返回 doc_id + permission_grant.status=granted
# 然后删掉这个测试文档:
lark-cli drive +delete --as bot --file-token "<doc_id>" --type docx --yes
```

---

## 常见问题

### `App scope not enabled: required scope X`

→ 应用需要那个 scope 但没开。点错误信息里的 URL 一键开通。

### `Auth expired`

→ user 身份 token 过期。重新登录：`lark-cli auth login`。bot 身份不会过期（除非你删了 app）。

### `unsafe file path: --file must be a relative path`

→ lark-cli 要求 `--file` 是相对路径。`xhs-viral-decoder` 的 `lark.py` wrapper 自动 `cd` 到文件目录处理这个。

### 可以不创建飞书 app 用别的吗？

→ 可以——把 `config.yaml::output.push_to_platform` 设为 `false`，所有产物只生成本地 markdown，不推飞书。
