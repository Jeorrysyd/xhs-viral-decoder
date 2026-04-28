#!/usr/bin/env bash
# setup_feishu.sh — 一键配置飞书连接
# 自动创建飞书文件夹 + 自动检测 open_id + 自动生成 config.yaml
# 用户只需要提前做两件事：
#   1. npm install -g @larksuite/cli
#   2. lark-cli config init（填 App ID + App Secret）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_EXAMPLE="$SKILL_ROOT/config.example.yaml"
CONFIG_FILE="$SKILL_ROOT/config.yaml"

# ── 颜色 ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo ""
echo "🚀 xhs-viral-decoder — 飞书一键配置"
echo "────────────────────────────────────"
echo ""

# ── 1. 检查 lark-cli ──
if ! command -v lark-cli &>/dev/null; then
  fail "lark-cli 未安装。请先运行：npm install -g @larksuite/cli"
fi
ok "lark-cli 已安装 ($(lark-cli --version 2>/dev/null || echo '?'))"

# ── 2. 检查 lark-cli 是否已配置 App ──
CONFIG_JSON=$(lark-cli config show 2>/dev/null || echo "")
if [ -z "$CONFIG_JSON" ] || echo "$CONFIG_JSON" | grep -q '"appId": ""'; then
  fail "lark-cli 未配置飞书应用。请先运行：lark-cli config init"
fi
ok "lark-cli 已配置飞书应用"

# ── 3. 自动检测 open_id ──
OPEN_ID=$(echo "$CONFIG_JSON" | grep -o 'ou_[a-f0-9]\{20,40\}' | head -1 || echo "")
if [ -z "$OPEN_ID" ]; then
  warn "无法从 lark-cli config 自动检测 open_id"
  echo "   请手动输入你的飞书 open_id（格式：ou_xxxxxxxx）："
  read -r OPEN_ID
  if [ -z "$OPEN_ID" ]; then
    fail "open_id 不能为空"
  fi
else
  ok "自动检测到 open_id: $OPEN_ID"
fi

# ── 4. 创建飞书文件夹（幂等：如果已存在则跳过） ──
FOLDER_NAME="小红书爆款拆解师"
echo ""
echo "📁 正在创建飞书文件夹「$FOLDER_NAME」..."

FOLDER_RESULT=$(lark-cli drive +create-folder --as bot --name "$FOLDER_NAME" 2>&1 || echo "")
FOLDER_TOKEN=$(echo "$FOLDER_RESULT" | grep -o '"folder_token": "[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$FOLDER_TOKEN" ]; then
  # 可能已存在，尝试从错误信息中获取
  warn "创建文件夹时遇到问题，可能已存在"
  echo "   请手动输入 folder_token（可从飞书云盘 URL 获取）："
  read -r FOLDER_TOKEN
  if [ -z "$FOLDER_TOKEN" ]; then
    fail "folder_token 不能为空"
  fi
else
  ok "飞书文件夹已创建，folder_token: $FOLDER_TOKEN"
fi

# ── 5. 生成 config.yaml ──
echo ""
if [ -f "$CONFIG_FILE" ]; then
  BACKUP="$CONFIG_FILE.bak.$(date +%Y%m%d_%H%M%S)"
  cp "$CONFIG_FILE" "$BACKUP"
  warn "已有 config.yaml，备份到 $(basename "$BACKUP")"
fi

cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"

# 替换 folder_token
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s|REPLACE_WITH_YOUR_FOLDER_TOKEN|$FOLDER_TOKEN|g" "$CONFIG_FILE"
  sed -i '' "s|REPLACE_WITH_YOUR_OPEN_ID|$OPEN_ID|g" "$CONFIG_FILE"
else
  sed -i "s|REPLACE_WITH_YOUR_FOLDER_TOKEN|$FOLDER_TOKEN|g" "$CONFIG_FILE"
  sed -i "s|REPLACE_WITH_YOUR_OPEN_ID|$OPEN_ID|g" "$CONFIG_FILE"
fi

ok "config.yaml 已生成并自动填好"

# ── 6. 验证 ──
echo ""
echo "📋 最终配置："
echo "   folder_token:    $FOLDER_TOKEN"
echo "   grantee_open_id: $OPEN_ID"
echo "   飞书输出:        ✅ 已启用"
echo ""

# 提取飞书 URL（如果有）
FOLDER_URL=$(echo "$FOLDER_RESULT" | grep -o '"url": "[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$FOLDER_URL" ]; then
  echo "   飞书文件夹: $FOLDER_URL"
  echo ""
fi

echo -e "${GREEN}🎉 飞书配置完成！${NC}"
echo ""
echo "下一步：在 Claude Code 里说「跑下本周情绪管理的爆款周报」试试看"
echo ""
