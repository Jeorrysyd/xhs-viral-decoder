# xhs-viral-pulse · examples

See [../../examples/viral_pulse_sample.md](../../examples/viral_pulse_sample.md) for a full sample report.

## Sample invocation transcript

```
User: 帮我跑下心理赛道本周爆款，关键词：情绪管理 / 内耗 / 自我疗愈

Claude: I'll run xhs-viral-pulse for those 3 keywords.

[Skill invokes: python3 shared/lib/cli.py viral-pulse --keywords 情绪管理,内耗,自我疗愈 --niche 心理]

Step 1/7: Checking xhs-mcp login... ✓
Step 2/7: Fetching data for 3 keywords... fetched 58 notes (5 failed due to xhs 风控)
Step 3/7: Analyzing... TOP 30 ranked, 8 pain buckets, 10 title patterns identified
Step 4/7: Rendering report... 19,093 chars
Step 5/7: Building sheet... 58 rows × 16 columns
Step 6/7: Pushing to Feishu folder...
  ✓ Sheet uploaded: token PoxXsD9SDhHUQQt1HM4cJn8Dnhe
  ✓ Doc created: token Gk4JdIptuo9OgzxyM51clIm7nDg
  ✓ Both moved to folder「小红书爆款拆解师」

Done. Open the report:
https://www.feishu.cn/docx/Gk4JdIptuo9OgzxyM51clIm7nDg

Top finding: 10 低粉爆款 (17.2% of sample). Best leverage: 橙子成长记 487粉/2.6w赞 (53× ratio).
```

## What good output looks like

- **5 sections all populated** (no empty placeholders)
- **TOP 30 table** has every column filled
- **痛点 section** has verbatim quotes with IP + likes + source — NOT generic descriptions
- **TOP 10 选题** each has anchor link to a specific TOP 30 viral note
- **Stats section** has actual numbers from this batch (not placeholder X/Y/Z)
