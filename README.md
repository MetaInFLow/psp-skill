# PSP · Personal Soul Protocol v2.1

> 把一个真实的人转化为可运行 AI 替身的工程协议。**不是人格测试、不是角色扮演脚本、不是写作风格模仿。**

## 核心目标

**风格保真 + 能力增强**：让 LLM 在风格层（语言、思路、判断习惯、做事方式）忠实于真人，在能力层（知识广度、状态稳定、规模吞吐）超越真人。

## 三阶段工作流

```
[阶段一 · 建模]   原始素材  ─→  PSP-YYYYMMDD-HHMMSS.md + PSP.md
[阶段二 · 扮演]   PSP.md    ─→  system_prompt-YYYYMMDD-HHMMSS.txt
[阶段三 · 测量]   AI 输出   ─→  validation_report.md
                              │
                              ↓
                          迭代回阶段一/二
```

## 文件索引

### 主控文件
- `SKILL.md` —— 三阶段工作流总纲，先读这个

### 模板（templates/）
- `PSP_template.md` —— 16 子项 PSP 主文档
- `system_prompt_template.md` —— 五段 system prompt
- `anti_blunting_template.md` —— 反钝化指令
- `judgment_test_template.md` —— 判断保真度测试
- `validation_report_template.md` —— 验证报告

### 参考资料（references/）
- `PSP_v2.1_full.md` —— 完整方法论
- `scoring_rules.md` —— 表演系数与置信度规则
- `extraction_protocol.md` —— 提炼协议详解（八条核心原则）
- `anti_blunting_rules.md` —— 反钝化指令推导规则（含矩阵表）
- `system_prompt_structure.md` —— 五段标准结构详解

### 脚本（scripts/）
- `extract_fingerprint.py` —— 12 维度语言指纹自动提取
- `consistency_scan.py` —— 风格一致性自动扫描（阶段三测量 C）
- `blind_eval_prep.py` —— 盲评测试包准备（阶段三测量 A）
- `init_person.sh` —— 新建人物目录

### 人物产物（people/）
- 默认写入 `people/<person_id>/`。
- `people/` 已被 `.gitignore` 忽略，不提交具体人物产物。
- openLifeOS / LifeOS 调用时可用 `--lifeos-root <repo>` 写入对应 LifeOS 的 `identity/psp/<person_id>/`。

## 快速开始

### 1. 新建人物

```bash
cd /path/to/psp/
bash scripts/init_person.sh zhang_san
# 或写入 LifeOS canonical PSP 产物目录：
bash scripts/init_person.sh zhang_san --lifeos-root /path/to/Target.LifeOS
```

### 2. 准备素材

```bash
cp ~/chat_export.txt people/zhang_san/raw_materials/chat_logs/
cp ~/2024_speech.md people/zhang_san/raw_materials/speeches/
# 编辑 meta.json 标注每份素材的表演系数
```

### 3. 抽取语言指纹（自动）

```bash
python3 scripts/extract_fingerprint.py \
    --input people/zhang_san/raw_materials/ \
    --output people/zhang_san/analysis/linguistic_fingerprint.json
```

### 4. 填充 PSP.md（人工）

按 `templates/PSP_template.md` 的结构填充 `people/zhang_san/PSP-YYYYMMDD-HHMMSS.md`，并同步 `people/zhang_san/PSP.md` current 入口。
严格遵守 `references/extraction_protocol.md` 的八条核心原则。

### 5. 生成 system prompt（人工）

按 `templates/system_prompt_template.md` 的五段结构生成 `people/zhang_san/system_prompt-YYYYMMDD-HHMMSS.txt`。
反钝化指令至少 8 条。

### 6. 验证（半自动）

```bash
# 把 system_prompt 贴到 Claude 项目，跑 100 个测试问题
# 把 AI 输出保存到 validation/test_samples/ai_outputs/
# 把真人原话保存到 validation/test_samples/human_samples/

# 风格一致性自动扫描
python3 scripts/consistency_scan.py \
    --ai-outputs people/zhang_san/validation/test_samples/ai_outputs/ \
    --human-baseline people/zhang_san/analysis/linguistic_fingerprint.json \
    --human-corpus people/zhang_san/raw_materials/ \
    --output people/zhang_san/validation/consistency_report.json

# 盲评测试包
python3 scripts/blind_eval_prep.py \
    --human-samples people/zhang_san/validation/test_samples/human_samples/ \
    --ai-samples people/zhang_san/validation/test_samples/ai_outputs/ \
    --output people/zhang_san/validation/blind_eval/
```

## 核心纪律（必读）

1. **行为优于言语** —— 自述与行为矛盾，永远以行为为准
2. **三场景一致才升级为模式** —— 少于三场景标"单次观察"
3. **矛盾保留不选边，但每子项 ≤ 2 组** —— 超过即重新定义子项
4. **不可萃取必须显式声明** —— 气场、即兴创造力、深层潜意识
5. **禁止"持续进化为本人未来版本"** —— AI 无法替本人经历未来
6. **反钝化指令必须为禁令格式** —— "禁止 XX"，不是"应该 XX"
7. **AI 输出对齐最佳态，不对齐平均态** —— 这是 AI 比真人稳定的真正实现路径

## License

This project is source-available under the PolyForm Noncommercial License 1.0.0. Noncommercial use is allowed; commercial use requires separate permission.
