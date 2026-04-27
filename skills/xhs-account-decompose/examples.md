# xhs-account-decompose · examples

See [../../examples/account_decompose_sample.md](../../examples/account_decompose_sample.md) for a full sample (decomposing 「来都来了播客」).

## Sample invocation

```
User: 拆解这个博主：https://www.xiaohongshu.com/user/profile/63d5eca800000000260129bc?xsec_token=ABVV4UY-Co0nHyjDzefQ2Oe5pbe_9nXiXpvlmQD0OBdaM=

Claude: [invokes xhs-account-decompose]

Step 1/6: Resolved user_id + xsec_token ✓
Step 2/6: Fetched profile — 「来都来了播客」12,384 粉, 22,100 总赞藏, 32 笔记
Step 3/6: Fetching TOP 5 details... 3/5 succeeded (TOP 1+2 blocked by 风控)
Step 4/6: Analyzing 5 dimensions...
  - 100% 视频 (zero 图文)
  - Dominant pattern: 视频播客丨X (机械前缀)
  - Audience: 上海 + 美国 + 北京 + 香港 (一线 + 海外华人)
  - Single viral driver: TOP 1 4963 / TOP 2 2228 (cliff drop)
Step 5/6: Rendering 5-section report... 13,500 chars
Step 6/6: Pushing to Feishu folder... done

Open: https://www.feishu.cn/docx/<token>

Key insight: 「视频播客丨」prefix is killing 60% of titles (TOP 1/2/3 don't use it).
3 specific actions to copy → see report §5.7.
```

## What good output looks like

- All 5 sections populated
- §三 (audience) has actual IP names + theme counts (not generic descriptions)
- §四 has TOP 5 with likes/收藏/评论 + the one dominant formula explicitly named
- §五 ends with 3 numbered concrete actions (each has 标题 + 角度 + 形式 + 触达痛点)
- §六 is a 1-sentence summary
- Data limitations section (if any 风控 happened) is at the bottom
