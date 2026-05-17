# 人物目录模板

这是一个空的人物目录示例。每个目标人物建一个独立子目录，复制本结构。

## 目录结构

- `PSP.md` —— 阶段一产出（用 templates/PSP_template.md 填充）
- `system_prompt.txt` —— 阶段二产出（用 templates/system_prompt_template.md 填充）
- `raw_materials/` —— 原始素材
  - `chat_logs/` —— 聊天记录
  - `speeches/` —— 演讲、对外发言
  - `emails/` —— 邮件
  - `interviews/` —— 访谈记录
  - `meta.json` —— 素材元数据（每份素材的来源类型、表演系数）
- `analysis/` —— 分析中间产物
  - `linguistic_fingerprint.json` —— scripts/extract_fingerprint.py 自动产出
  - `conflict_stories.md` —— 冲突故事集（人工整理）
  - `pattern_observations.md` —— 经验模式观察记录（人工整理）
- `validation/` —— 阶段三产出
  - `validation_report.md`
  - `test_samples/`
    - `human_samples/` —— 真人原话样本（盲评用）
    - `ai_outputs/` —— AI 输出样本（盲评 + 一致性扫描用）
    - `judgment_test/` —— 决策案例对比测试

## meta.json 示例

```json
{
  "files": [
    {
      "path": "chat_logs/2024_micchat.txt",
      "source_type": "self",
      "performance_coefficient": 1.0,
      "time_range": "2024-01 ~ 2024-12",
      "note": "私下微信"
    },
    {
      "path": "speeches/2024_annual.md",
      "source_type": "self",
      "performance_coefficient": 0.3,
      "time_range": "2024-12",
      "note": "年会演讲"
    }
  ]
}
```

## 命名规范

person_id 用拼音或代号，避免空格和特殊字符。例：zhang_san、ceo_z、boss_w
