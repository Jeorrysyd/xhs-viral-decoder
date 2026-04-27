# xhs-matrix-identify · workflow

## Inputs

| Param | Type | Default | Notes |
|---|---|---|---|
| `--target-url` | string | — | Required. Main account URL |
| `--peer` | string | `auto` | Heavy-matrix benchmark account (defaults to niche-appropriate) |
| `--niche` | string | `心理` | Used to pick default `--peer` |
| `--output` | path | `output/<date>/matrix-identify/` | Local artifacts |

## Step-by-step

### Step 1: Fetch target account profile
```python
target_profile = user_profile(target_user_id, xsec_token)
target_bio = target_profile["userBasicInfo"]["desc"]
```

### Step 2: Detect matrix signals in bio

Regex patterns:
- `@(\w+)` → @-mentions of other accounts (light matrix indicator)
- `主号|分号|矩阵|联动|@.+@` → explicit matrix language
- Multiple `@` mentions → likely natural light matrix

If 0 signals: still proceed to step 3 (some heavy matrices don't bio-link).

### Step 3: Search-based sub-account discovery

```python
# Search for accounts whose nickname starts with the target's name root
name_root = extract_name_root(target_nickname)  # e.g., "谢胜子" from "谢胜子会客厅"
results = search_feeds(name_root)
candidates = [r for r in results if r["nickname"].startswith(name_root) or name_root in r["nickname"]]
```

Deduplicate by user_id, sort by TOP note likes.

### Step 4: Fetch peer benchmark (if `--peer` provided or default)

Same as step 3 but for the peer (e.g., 谢胜子 → discovers 13+ sub-accounts).

### Step 5: Analyze distribution logic

For each matrix (target + peer):
- Count accounts
- Classify role per account by name pattern + content sample:
  - 主号 (no suffix)
  - 「会客厅」型 → 对谈类
  - 「思维笔记」型 → 直播金句切片
  - 「每日一更/分享」型 → 日更号
  - 主题切片型 (高能量场 / 进化学 / 职场法则) → 内容切片
  - 「助理 / 小助手」型 → 反向引流号
  - 主播个人名 → IP 个人号
- Estimate total monthly exposure ≈ Σ (TOP likes × 100) per account
- Compute leverage multiplier ≈ matrix_total / target_alone_estimate

### Step 6: Generate light-matrix proposal for user

Hard-coded design pattern (single-person realistic):
- **主号**：creator angle (产品幕后 / 工具 / 专业)
- **副号**：personal angle (情绪 / 生活 / 用户故事)
- One素材切两套：specialist version + relatable version
- Cadence recommendation: 主号 2-3 图文/周 + 1 视频/2周; 副号 1-2 图文/周 (no video pressure)

### Step 7: Render report (`shared/lib/report.py::render_matrix_identify`)

4-section markdown using template `matrix_identify_template.md`.

### Step 8: Push to Feishu

```python
adapter.push_doc(
    title=f"[矩阵识别] {target_nickname}_vs_{peer_nickname}_{date}",
    md=report_md
)
```

## Failure modes

| Symptom | Action |
|---|---|
| Target has 0 matrix signals + 0 search hits for name root | Report with §四「该账号无矩阵信号」 + still propose user's 2-account variant |
| Peer benchmark has < 5 accounts found | Mark as 「mid-matrix」 not 「heavy matrix」 |
| All candidate accounts are < 100 fans | Likely dead matrix; warn user |

## Tunable parameters

In `shared/lib/matrix_classifier.py`:
- Role naming patterns (regex list)
- Default peer benchmarks per niche (心理 → 谢胜子; AI → ?; 美食 → ?)
- Leverage multiplier formula (currently `Σlikes × 100` for monthly est.)
