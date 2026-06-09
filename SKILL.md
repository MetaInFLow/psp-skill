---
name: psp
description: "Personal Soul Protocol v2.1 工作流。当用户要为一个真实的人构建 AI 替身/数字分身/扮演 prompt 时使用。涵盖三个阶段：建模（从原始素材产出 PSP_REPORT.xml 人物模型）、扮演（从 PSP XML 产出可运行 system prompt）、测量（自动化验证 AI 输出的语言保真度与风格一致性）。触发关键词包括：PSP、建模某人、给某人做替身、复刻某人、AI 扮演某人、数字分身、风格保真测试、语言指纹提取、最佳态对齐、反钝化指令。不要用于：通用人格测试、心理画像、虚构角色塑造、单纯的写作风格模仿（这些是浅层任务，PSP 是深度工程协议）。"
---

# Personal Soul Protocol（PSP）v2.1 工作流

## 这个 skill 是什么

把一个真实的人转化为可运行 AI 替身的工程协议。**不是人格测试，不是角色扮演脚本，不是写作风格模仿。** 这是从原始素材到可投产 system prompt 的完整工程链路。

## 设计目标（必须始终对齐）

> **风格保真 + 能力增强**：让 LLM 在风格层（语言、思路、判断习惯、做事方式）忠实于真人，在能力层（知识广度、状态稳定、规模吞吐）超越真人。

**忠实层**（不可超越，必须严格还原）：终极价值排序、世界假设、判断风格、语言指纹、关系姿态。

**增强层**（必须超越，AI 的存在意义）：知识广度、状态稳定、吞吐速度、可重现性。

**明确不做**：不重塑内核（那是改造）、不替本人完成成长（违反"判断成熟来自经历"这一基本事实）、不"让此人变得更好"（"更好"由谁定义都站不住）。

## 三阶段工作流总览

```
[阶段一 · 建模]  原始素材 ─┐
                          ├─→  current/PSP_REPORT.xml
[阶段一 · 建模]  访谈/对话─┘     + versions/PSP_REPORT.<timestamp>.xml
                                 │
                                 ↓
[阶段二 · 扮演]               system_prompt-<timestamp>.txt
                                 │
                                 ↓
[阶段三 · 测量]               validation_report-<timestamp>.md
                                 │
                                 ↓
                              迭代回阶段一/二
```

每一阶段都有自己的入口规则、产出物、验收标准。**不允许跳过阶段或合并阶段**——这是 v1.0 失败的根本原因（v1.0 只有阶段一）。

---

## 入口判断

### Stage 0 · 输出语言契约

任何 PSP 任务开始前，先确认 `output_language`，只允许 `zh-CN` 或 `en-US`。如果目标是 openLifeOS / LifeOS 实例，默认读取该实例的 `matrix.yml` / `replicateme.yml` 中的 `language`；如果没有配置，默认 `zh-CN`。

语言契约必须写在 PSP XML 最前面：

- `psp_report/@language`
- `psp_report/language_contract/output_language`
- `psp_report/metadata/output_language`
- `evidence_maturity_report/@language`
- `evidence_maturity_report/language_contract/output_language`
- `evidence_maturity_report/metadata/output_language`

这些字段必须一致。报告正文、缺失信息、确认问题、派生 Markdown/HTML、system prompt、validation report 和最终披露都必须使用 `output_language`；只有原始引用、文件路径、XML tag、schema、产品名和协议固定术语可以保留原文。发现产物语言漂移时，先翻译/重生再通过 doctor，不要继续分析。

收到任务时，先识别用户处于哪个阶段：

**阶段一 · 建模**——用户给了原始素材（聊天记录、邮件、访谈、文档），目标是产出带生成时间的 PSP XML 主报告和 current 入口。**关键词**：建模某人、整理某人的特征、提炼经验模式、构建 PSP。

**阶段二 · 扮演**——用户已有 `current/PSP_REPORT.xml` 或 `versions/PSP_REPORT.<timestamp>.xml`，目标是生成带生成时间的可运行 system prompt。**关键词**：生成 prompt、做成 Claude 项目、让 AI 扮演、output system prompt。

**阶段三 · 测量**——用户已有 system prompt 和 AI 输出样本，目标是验证保真度。**关键词**：测试效果、保真度、跑验证、风格一致性。

**判断不清时**：直接问用户当前处于哪个阶段，不要瞎猜。这三个阶段需要的输入和产出物完全不同。

---

## 产物位置约定

PSP 是 MetaInFlow 的独立 Skill repo。默认产物位置是本 repo 下的 `people/{person_id}/`，但 `people/` 必须被 `.gitignore` 忽略，不能把具体人物产物提交进 Skill 包。

```
people/
  └── {person_id}/                    ← 用人名拼音或代号，避免空格
      ├── ARTIFACTS.xml               ← PSP artifact manifest
      ├── current/
      │   ├── PSP_REPORT.xml          ← 阶段一 current 入口，唯一 canonical PSP 报告
      │   └── EVIDENCE_MATURITY.xml   ← evidence maturity current 入口
      ├── versions/
      │   ├── PSP_REPORT.YYYYMMDD-HHMMSS.xml
      │   └── EVIDENCE_MATURITY.YYYYMMDD-HHMMSS.xml
      ├── derived/
      │   └── PSP.md                  ← 可选派生读物；不是 source of truth
      ├── system_prompt-YYYYMMDD-HHMMSS.txt ← 阶段二产物，可投产 prompt
      ├── raw_materials/              ← 原始素材，本地工作区，默认不提交
      │   ├── chat_logs/              ← 聊天记录
      │   ├── speeches/               ← 演讲稿
      │   ├── emails/                 ← 邮件
      │   ├── interviews/             ← 访谈记录
      │   └── meta.json               ← 素材元数据（来源、表演系数）
      ├── analysis/                   ← 分析中间产物
      │   ├── linguistic_fingerprint.json   ← 12 维语言指纹提取结果
      │   ├── conflict_stories.md           ← 冲突故事集（用于推导 1.1）
      │   └── pattern_observations.md       ← 经验模式观察记录
      └── validation/                 ← 阶段三产出
          ├── validation_report.md
          └── test_samples/           ← 盲评测试样本
```

openLifeOS / LifeOS 实例调用 PSP Skill 时，可以把产物根目录改到 LifeOS repo：

```bash
bash scripts/init_person.sh <person_id> --lifeos-root /path/to/Target.LifeOS
bash scripts/init_person.sh <person_id> --lifeos-root /path/to/Target.LifeOS --language zh-CN
```

此时 canonical PSP 产物会写入 `identity/psp/<person_id>/current/PSP_REPORT.xml` 和 `identity/psp/<person_id>/versions/PSP_REPORT.<timestamp>.xml`。`EVIDENCE_MATURITY.xml` 同样写入 `current/` 和 `versions/`。如果未显式传入 `--language`，脚本默认 `zh-CN`；openLifeOS 初始化链路必须把实例语言传入。原始素材默认不进入公开 LifeOS repo；应留在授权私有资料源，或临时放在 PSP repo 中已被 gitignore 的 `people/{person_id}/raw_materials/` 工作区。

**新建人物目录时**：默认运行 `scripts/init_person.sh <person_id> --language zh-CN`，产出到 `people/<person_id>/`；如需指定目录，用 `--output-root <dir>`；如需 openLifeOS 产物，用 `--lifeos-root <lifeos_repo>`。如果用户要求英文产物，显式传 `--language en-US`。

**SOUL 暂停规则**：本 skill 不生成 `SOUL.md`，也不把 PSP 映射成独立 Soul 产物。PSP XML 同时承载人物模型、行为边界、最佳态和 runtime 指令；若某个 runtime 仍需要 `SOUL.md`，只能作为目标 runtime 的临时投影，不得作为 PSP 源产物或 LifeOS 初始化必备产物。

---

## 阶段一 · 建模

### 入口检查

开始前必须确认：

1. 素材覆盖度：至少包含**正式语料**（演讲、文件、对外发言）和**非正式语料**（微信、私下谈话、内部会议）两类
2. 时间跨度：素材至少覆盖 1 年，最好 3 年以上
3. 数据量：文本素材至少 50,000 字，否则置信度不足
4. 冲突故事：至少能识别出 5 个以上"两难选择"故事

**不满足时**：直接告诉用户"素材不足以建模出可信的 PSP，建议先补充 X 类素材"，不要勉强建模。**勉强建模出来的 PSP 会成为后续所有问题的根源**——错误一旦写进去，后续 system prompt 和测量都跟着错。

### 标准执行流程

按顺序执行，不得跳步：

**Step 1 · 素材分类与表演系数标注**

读取 `raw_materials/` 下所有素材，为每份素材标注表演系数（参见 `references/scoring_rules.md`）。私下微信 ×1.0，年会演讲 ×0.3。结果写入 `raw_materials/meta.json`。

**Step 2 · 链路压缩识别**

通读素材，识别每段表达属于哪种链路：完整链路 / 直觉反应 / 社交性回应 / 情绪劫持。**社交性回应里提取的"价值观陈述"必须打折使用**——这是 v1.0 失真的主因之一。

**Step 3 · XML 必备模块填充**

按 `templates/PSP_REPORT.template.xml` 的结构，逐模块填充。完整字段契约见 `references/psp_output_schema_design.md`。XML 是唯一原始报告格式；Markdown 只允许作为派生读物。**严格遵守提炼协议**（参见 `references/extraction_protocol.md`）：

- 多源一致取共识
- 三场景一致升级为模式（少于三场景标"单次观察"）
- 矛盾保留不选边（每子项最多 2 组矛盾）
- 时间衰减（交互层尤其）
- 行为优于言语
- 表演加权
- 单源标假设
- 不可萃取标注

**核心子项重点**：1.1 终极排序、3.2 经验模式库、3.3 情境-动作序列、4.1 关系图谱、4.3 语言指纹——这五项决定 PSP 质量上限。

**必备 XML 模块**：`language_contract`、`metadata`、`evidence_maturity`、`source_inventory`、`evidence_boundary`、`ontology_map`、`kernel`、`cognition`、`decision_model`、`interaction_model`、`business_domain_model`、`language_fingerprint`、`best_state`、`delegation_boundary`、`runtime_instructions`、`validation_plan`、`confirmation_checklist`、`acceptance_criteria`、`confidence_by_section`、`missing_information`、`iteration_log`。每个非空结论字段必须带 `status`、`confidence`、`evidence` 和 `missing_evidence`；不能判断时显式标 `unassessed` / `not_extractable`，不能用空白伪装完成。

**本体九维输出点**：`ontology_map` 必须固定输出 worldview、lifeview、values_and_bottom_lines、role_and_mission、methodology_and_fact_view、decision_and_tradeoff_view、human_and_talent_view、business_and_customer_view、expression_and_organization_view。它回答“这个人的判断系统是什么”，不是行业知识库、制度合集或金句摘抄。

**运行与授权输出点**：`decision_model` 必须包含 pre-answer checks 和 forced downgrade rules；`delegation_boundary` 必须写清 can/cannot represent、private information policy、external translation policy；`confirmation_checklist` 必须列出需要 owner 二次确认的高影响结论；`acceptance_criteria` 必须定义如何判断分身像这个人的判断顺序和追问方式，而不是像通用助手。

**4.3 语言指纹的特殊要求**：必须运行 `scripts/extract_fingerprint.py` 自动提取 12 维度的可量化部分（句长分布、转折标记词频、高频功能词等），结果存入 `analysis/linguistic_fingerprint.json`。手工提取剩余维度（幽默风格、语域切换条件等）。

**Step 4 · 最佳态画像构建**

收集 10-20 个事后被验证为"判断很对"的决策案例，提取这些案例发生时此人的状态特征（精力、情绪、信息储备、时间压力），找共同点，固化为最佳态画像。**这是 AI 输出的对齐目标，不是可选项。**

**Step 5 · 自检与置信度标注**

填完后，逐子项检查：

- 是否每个核心子项都有 ≥3 条原话证据？
- 是否每条经验模式都有 ≥3 个支撑场景？
- 矛盾是否超过每子项 2 组上限？
- 不可萃取的维度是否显式声明？

不通过的部分**必须降级置信度或删除**，不要为了"完整"而填假内容。

### 阶段一产出物

默认 current：`people/{person_id}/current/PSP_REPORT.xml`——按 v2.1 完整结构填充的 canonical PSP 源报告。

默认版本：`people/{person_id}/versions/PSP_REPORT.YYYYMMDD-HHMMSS.xml`——同名不同版本的不可覆盖记录。

Evidence maturity：`current/EVIDENCE_MATURITY.xml` + `versions/EVIDENCE_MATURITY.YYYYMMDD-HHMMSS.xml`。

LifeOS 模式：`identity/psp/{person_id}/current/PSP_REPORT.xml` + `identity/psp/{person_id}/versions/PSP_REPORT.<timestamp>.xml`，并同步 evidence maturity XML。

### 阶段一验收标准

- `scripts/psp_doctor.py` 通过，所有必备 XML 模块存在，并返回 `content_maturity`；结构通过不等于内容达到 research/avatar-grade
- 16 子项全部填充或显式标注"不可萃取"
- 5 个核心子项置信度 ≥ 中
- 最佳态画像已构建
- 至少 50 条经验模式（资深管理者预期 50-100 条）

---

## 阶段二 · 扮演

### 入口检查

开始前必须确认：

1. `current/PSP_REPORT.xml` 已通过阶段一验收
2. 阶段三测试如果以前跑过，最近一次的失败模式分析已读取（避免重复犯错）

### 标准执行流程

**Step 1 · 五段结构生成**

按 `references/system_prompt_structure.md` 的五段标准结构生成 system prompt：

```
[1] 身份与最佳态对齐
[2] 内核约束（来自 1.1, 1.2, 1.3, 1.4）
[3] 思考方式（来自第二段、第三段）
[4] 表达方式（来自第四段）
[5] 反钝化指令（来自工程对抗层）
```

**Step 2 · 反钝化指令推导**

这是 v1.0 完全缺失、决定"风格保真度"上限的关键。按 `references/anti_blunting_rules.md` 从 PSP 子项推导禁令。**所有指令必须是禁令格式**（"禁止 XX"），不能是建议格式（"应该 XX"）——禁令对 LLM 的约束力强一个量级。

每条指令格式（详见 `templates/anti_blunting_template.md`）：

```
【来源子项】[子项编号]
【LLM 默认偏向】[不加指令时 LLM 会怎么做]
【失败案例】[会输出什么样的失真内容]
【指令文本】"禁止 XX。具体要求：YY。"
```

**Step 3 · 情境激活路径生成**

为此人的常见情境（人事决策、战略选择、危机响应、公开表态等 8-12 类），定义子项激活路径。每条路径写进 system prompt 的第 3 段。

**Step 4 · 知识接入流水线指令**

明确告诉 AI：任何外部知识必须走"认知层过滤 → 决策层框架化 → 风格层包装 → 冲突标注"四步流水线，禁止短路输出。冲突标注三级（软/中/硬冲突）的处理方式按 v2.1 协议。

**Step 5 · 输出与试运行**

默认产出物写入 `people/{person_id}/system_prompt-YYYYMMDD-HHMMSS.txt`。LifeOS 模式写入 `identity/psp/{person_id}/system_prompt-YYYYMMDD-HHMMSS.txt`。生成前必须从 PSP XML 读取 `ontology_map`、`kernel`、`cognition`、`decision_model`、`interaction_model`、`business_domain_model`、`language_fingerprint`、`best_state`、`delegation_boundary`、`runtime_instructions`、`validation_plan` 和 `acceptance_criteria`，不得从派生 Markdown 反推。建议附一段试运行说明：用 5-10 个典型问题在 Claude 项目里跑一遍，肉眼检查是否明显失真，再进入阶段三的自动化测试。

### 阶段二产出物

`people/{person_id}/system_prompt-YYYYMMDD-HHMMSS.txt` 或 `identity/psp/{person_id}/system_prompt-YYYYMMDD-HHMMSS.txt`——可直接贴到 Claude 项目或 API system prompt 字段使用。

### 阶段二验收标准

- 五段结构完整
- 反钝化指令至少 8 条（少于 8 条意味着工程对抗层做得不够）
- 情境激活路径覆盖 ≥ 8 类常见情境
- 试运行 5-10 个典型问题，明显失真案例 ≤ 1 个

---

## 阶段三 · 测量

### 入口检查

开始前必须确认：

1. system_prompt.txt 已生成
2. 已用 system_prompt 在 Claude 项目里跑过至少 100 个问题，输出结果保存在 `validation/test_samples/ai_outputs/`
3. 真人原话样本至少 20 条，保存在 `validation/test_samples/human_samples/`

### 三类测量

**测量 A · 语言保真度（半自动）**

使用 `scripts/blind_eval_prep.py` 准备盲评测试包：随机混排 20 段真人原话和 20 段 AI 输出，生成评估表交给熟人评估。返回率 ≤ 60% 视为通过。**这一项必须有真人评估，AI 自评无效**——AI 评估自己的输出有系统性偏向。

**测量 B · 判断保真度（人工）**

使用 `templates/judgment_test_template.md`：选 ≥20 个本人历史决策案例（建模时已留出，未输入 PSP），把决策前的情境喂给 AI，对比 AI 输出与本人实际决策。本人或熟悉本人的人按四级评估（完全一致 / 方向一致 / 方向不一致但本人认可 / 方向不一致且本人不认可），合格率 ≥ 70% 通过。

**测量 C · 风格一致性（全自动）**

运行 `scripts/consistency_scan.py`：

```bash
python scripts/consistency_scan.py \
  --ai-outputs people/{person_id}/validation/test_samples/ai_outputs/ \
  --human-baseline people/{person_id}/analysis/linguistic_fingerprint.json \
  --output people/{person_id}/validation/consistency_report.json
```

脚本会：
1. 对 AI 输出做 12 维度语言指纹提取
2. 计算每维度的方差
3. 与真人原始语料的同维度方差对比
4. 输出每维度的 ratio（AI 方差 / 真人方差），通过阈值 ≤ 1.5

### 失败模式与修复

测量结果写入 `validation/validation_report.md`，按 `templates/validation_report_template.md` 格式。失败时按下表迭代：

| 不通过类型 | 修复方向 |
|-----------|---------|
| 语言保真度低 | 4.3 语言指纹细化 + 反钝化指令强化 |
| 判断保真度低 | 3.2 经验模式库扩充 + 5.1 子项激活路径校正 |
| 风格一致性低 | 5.2 子项冲突仲裁规则细化 + 子项间冗余审计 |

修复后**必须重新跑全部三类测量**，不能只跑失败的那一类——单维度修复经常引入其他维度的回归。

### 阶段三产出物

`people/{person_id}/validation/validation_report-YYYYMMDD-HHMMSS.md` 或 `identity/psp/{person_id}/validation/validation_report-YYYYMMDD-HHMMSS.md`——含三类测量结果、失败模式分析、下一轮迭代建议。

### 阶段三验收标准

- 三类测量全部通过
- 验证报告写明下次复检日期（参见 v2.1 演化系统的分层有效期）

---

## 关键纪律

### 不可妥协的原则

1. **行为优于言语**——自述与行为矛盾时，永远以行为为准
2. **三场景一致升级为模式**——少于三场景的判断逻辑标"单次观察"，永不升级
3. **矛盾不选边**——但每子项不超过 2 组矛盾
4. **不可萃取必须显式声明**——气场、即兴创造力、深层潜意识等维度，宁可承认无能也不假装有能
5. **禁止"持续进化为本人未来版本"的承诺**——AI 无法替本人经历未来。任何宣称这一点的设计都是不诚实的

### 常见陷阱（必须主动规避）

**陷阱 1：把社交性回应当成价值观陈述。** 一个老板在年会上说"我最看重诚信"和他在内部会议上的实际选择可能完全不一致。年会素材的表演系数是 ×0.3，权重应当远低于内部素材。

**陷阱 2：把自述当真。** "我是一个很有耐心的人"——他说自己有耐心不代表他真的有。看他实际怎么对待第三次解释同一件事的下属。

**陷阱 3：用 LLM 自己的偏好钝化此人特色。** LLM 训练偏好"温和、平衡、面面俱到"。一个有棱角的真人套上 PSP 后，AI 跑出来是圆润版的他——熟人一秒识破。这就是反钝化指令必须存在的原因。

**陷阱 4：合并子项时稀释独立洞察。** v2.1 把 v1.0 的世界假设+归因模式合并为认知地基、压力响应+矛盾合并为 3.4，但合并后必须依然保留"自他归因不对称""矛盾不被解决只动态偏向"等关键洞察。在填充模板时显式分两层/两面，不要混在一起写。

**陷阱 5：跳过最佳态画像。** v1.0 没有这一项，导致 AI 输出对齐到"平均态"——平均态包含此人状态不佳时的判断，会拖垮 AI 质量。**最佳态是 AI 比真人稳定的真正实现路径**，不是装饰性步骤。

---

## 文件参考索引

完整 v2.1 方法论：`references/PSP_v2.1_full.md`

模板：
- `templates/PSP_REPORT.template.xml`——英文 canonical PSP XML 主报告模板
- `templates/EVIDENCE_MATURITY.template.xml`——英文 evidence maturity XML 模板
- `templates/zh-CN/PSP_REPORT.template.xml`——中文 canonical PSP XML 主报告模板
- `templates/zh-CN/EVIDENCE_MATURITY.template.xml`——中文 evidence maturity XML 模板
- `templates/PSP_template.md`——legacy/derived Markdown 读物模板，不是源报告
- `templates/anti_blunting_template.md`——反钝化指令模板
- `templates/system_prompt_template.md`——五段 system prompt 模板
- `templates/judgment_test_template.md`——判断保真度测试模板
- `templates/validation_report_template.md`——验证报告模板

参考资料：
- `references/scoring_rules.md`——表演系数表与置信度规则
- `references/extraction_protocol.md`——提炼协议详解
- `references/anti_blunting_rules.md`——反钝化指令推导规则
- `references/system_prompt_structure.md`——五段标准结构详解

脚本：
- `scripts/psp_doctor.py`——PSP XML 结构和内容成熟度 doctor
- `scripts/extract_fingerprint.py`——12 维度语言指纹提取
- `scripts/consistency_scan.py`——风格一致性自动扫描
- `scripts/blind_eval_prep.py`——盲评测试包准备
