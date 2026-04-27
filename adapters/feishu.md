# 飞书 / Lark Adapter（完整实现）

`FeishuAdapter` 是 6 个 sub-skill 的默认输出后端。已经在生产环境验证。

## 架构

```
shared/lib/output_adapter.py::FeishuAdapter
       │
       ▼
shared/lib/lark.py (subprocess wrapper)
       │
       ▼
lark-cli (npm @larksuite/cli)
       │
       ▼
飞书 OpenAPI
```

## 支持的操作

| 方法 | 实现 |
|---|---|
| `push_doc(title, markdown)` | `lark-cli docs +create --markdown @file` |
| `push_sheet(title, xlsx_path)` | `lark-cli drive +import --type sheet` |
| `update_doc(doc_token, markdown)` | `lark-cli docs +update --mode overwrite` |
| `create_folder(name)` | `lark-cli drive +create-folder` |
| `delete(token, type)` | `lark-cli drive +delete --yes` |
| `move(token, type, folder)` | `lark-cli drive +move` |
| `grant_user(...)` | bot 创建时**自动 grant**，无需显式调用 |

## 必需的 scope

见 [setup/02_install_lark_cli.md](../setup/02_install_lark_cli.md) 完整列表。最小集合：

- `space:folder:create`
- `space:document:create`
- `space:document:update`
- `space:document:delete`
- `docs:document:import`
- `drive:drive:upload`
- `drive:drive:move`

## 关键设计决策

### 1. 为什么用 subprocess 包 lark-cli 而不是直接调 OpenAPI？

- lark-cli 已经处理 token 刷新 / scope 报错 / 限流
- 用户已经为 lark-cli 配过凭证，不需要再配第二份
- markdown → 飞书 docx blocks 的转换由 lark-cli 处理（不用我们重新实现）

### 2. 为什么用 `--mode overwrite` 而不是增量更新？

- 增量更新（append / replace_range）需要 block_id 定位，逻辑复杂
- viral-rewrite 修改 viral-pulse 报告时，整体 overwrite 最简单可靠
- 如果用户改过文档内容，会被 overwrite 覆盖——是已知 trade-off

### 3. 为什么 bot 创建的 doc 自动 grant 给 user？

`lark-cli docs +create` 内置逻辑：返回值里有 `permission_grant.status=granted`，
表示创建后自动给配置里的 user open_id 授可管理权。这避免了每次都要手动跑 permission.members create。

如果想关掉这个行为：在 `config.yaml` 里设 `feishu.identity: user`（用 user 身份创建，无需 grant）。

## 已知限制

| 限制 | 说明 |
|---|---|
| docx markdown 渲染 | 飞书 docx 不完全支持所有 markdown 语法。表格 / 标题 / 代码 / 链接都 OK；嵌套引用 / 复杂列表可能差异 |
| sheet 导入 | xlsx 列宽信息会丢失，需要打开 sheet 后手动调整 |
| 文件名重复 | 飞书允许同名文件共存——viral-rewrite 会找到老的 sheet 删除再重新导入 |

## 验证 adapter 可用

```python
from shared.lib.config import load_config
from shared.lib.output_adapter import get_adapter

cfg = load_config()
adapter = get_adapter("feishu", cfg)
token = adapter.push_doc(title="test", markdown="# hello\n\ntest content")
print(f"Created: https://www.feishu.cn/docx/{token}")

# clean up
adapter.delete(token, "docx")
```

## Troubleshooting

见 [setup/troubleshooting.md](../setup/troubleshooting.md) 「lark-cli 相关」段。
