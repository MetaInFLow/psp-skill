#!/bin/bash
# PSP v2.1 · 新建人物 PSP 产物目录脚本
#
# 用法：
#   bash init_person.sh <person_id>
#   bash init_person.sh <person_id> --output-root <dir>
#   bash init_person.sh <person_id> --lifeos-root <lifeos_repo>
#   bash init_person.sh <person_id> --person-name "Display Name"
#   bash init_person.sh <person_id> --language zh-CN
#
# 例：
#   bash init_person.sh zhang_san
#   bash init_person.sh zhang_san --lifeos-root /path/to/AnthonyHF.LifeOS

set -e

if [ -z "$1" ]; then
    echo "用法：bash init_person.sh <person_id>"
    echo "      bash init_person.sh <person_id> --output-root <dir>"
    echo "      bash init_person.sh <person_id> --lifeos-root <lifeos_repo>"
    echo "例：  bash init_person.sh zhang_san"
    exit 1
fi

PERSON_ID="$1"
shift
PERSON_NAME="$PERSON_ID"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PSP_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_ROOT="$PSP_ROOT/people"
CREATE_RAW_MATERIALS="1"
OUTPUT_LANGUAGE="zh-CN"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --output-root)
            if [ -z "$2" ]; then
                echo "[错误] --output-root 需要目录参数"
                exit 1
            fi
            OUTPUT_ROOT="$2"
            shift 2
            ;;
        --lifeos-root)
            if [ -z "$2" ]; then
                echo "[错误] --lifeos-root 需要 LifeOS repo 目录参数"
                exit 1
            fi
            OUTPUT_ROOT="$2/identity/psp"
            CREATE_RAW_MATERIALS="0"
            shift 2
            ;;
        --person-name)
            if [ -z "$2" ]; then
                echo "[错误] --person-name 需要名称参数"
                exit 1
            fi
            PERSON_NAME="$2"
            shift 2
            ;;
        --language|--output-language)
            if [ -z "$2" ]; then
                echo "[错误] $1 需要语言参数：zh-CN 或 en-US"
                exit 1
            fi
            OUTPUT_LANGUAGE="$2"
            shift 2
            ;;
        --no-raw-materials)
            CREATE_RAW_MATERIALS="0"
            shift
            ;;
        *)
            echo "[错误] 未知参数：$1"
            exit 1
            ;;
    esac
done

case "$OUTPUT_LANGUAGE" in
    zh-CN|en-US)
        ;;
    *)
        echo "[错误] 不支持的 PSP 输出语言：$OUTPUT_LANGUAGE"
        echo "支持值：zh-CN, en-US"
        exit 1
        ;;
esac

TEMPLATE_ROOT="$PSP_ROOT/templates"
if [ -d "$PSP_ROOT/templates/$OUTPUT_LANGUAGE" ]; then
    TEMPLATE_ROOT="$PSP_ROOT/templates/$OUTPUT_LANGUAGE"
fi

PERSON_DIR="$OUTPUT_ROOT/$PERSON_ID"
TS="$(date +%Y%m%d-%H%M%S)"
GENERATED_AT="$(date +"%Y-%m-%dT%H:%M:%S%z")"
PSP_VERSION="$PERSON_DIR/versions/PSP_REPORT.$TS.xml"
PSP_CURRENT="$PERSON_DIR/current/PSP_REPORT.xml"
EVIDENCE_VERSION="$PERSON_DIR/versions/EVIDENCE_MATURITY.$TS.xml"
EVIDENCE_CURRENT="$PERSON_DIR/current/EVIDENCE_MATURITY.xml"

if [ -d "$PERSON_DIR" ]; then
    echo "[错误] 目录已存在：$PERSON_DIR"
    echo "如需重建，请先删除现有目录。"
    exit 1
fi

echo "[PSP] 创建人物目录：$PERSON_DIR"

if [ "$CREATE_RAW_MATERIALS" = "1" ]; then
    mkdir -p "$PERSON_DIR/raw_materials/chat_logs"
    mkdir -p "$PERSON_DIR/raw_materials/speeches"
    mkdir -p "$PERSON_DIR/raw_materials/emails"
    mkdir -p "$PERSON_DIR/raw_materials/interviews"
fi
mkdir -p "$PERSON_DIR/current"
mkdir -p "$PERSON_DIR/versions"
mkdir -p "$PERSON_DIR/derived"
mkdir -p "$PERSON_DIR/analysis"
mkdir -p "$PERSON_DIR/validation/test_samples/human_samples"
mkdir -p "$PERSON_DIR/validation/test_samples/ai_outputs"
mkdir -p "$PERSON_DIR/validation/test_samples/judgment_test"

escape_sed_replacement() {
    printf '%s' "$1" | sed 's/[\/&|]/\\&/g'
}

render_template() {
    local template="$1"
    local output="$2"
    local person_id_escaped
    local person_name_escaped
    local generated_at_escaped
    local ts_escaped
    local output_language_escaped
    person_id_escaped="$(escape_sed_replacement "$PERSON_ID")"
    person_name_escaped="$(escape_sed_replacement "$PERSON_NAME")"
    generated_at_escaped="$(escape_sed_replacement "$GENERATED_AT")"
    ts_escaped="$(escape_sed_replacement "$TS")"
    output_language_escaped="$(escape_sed_replacement "$OUTPUT_LANGUAGE")"
    cp "$template" "$output"
    sed -i.bak \
        -e "s|{person_id}|$person_id_escaped|g" \
        -e "s|{person_name}|$person_name_escaped|g" \
        -e "s|{generated_at}|$generated_at_escaped|g" \
        -e "s|{artifact_timestamp}|$ts_escaped|g" \
        -e "s|{output_language}|$output_language_escaped|g" \
        "$output"
    rm -f "$output.bak"
}

# 拷贝 XML 模板作为带时间戳的版本产物，并同步 current 入口。
render_template "$TEMPLATE_ROOT/PSP_REPORT.template.xml" "$PSP_VERSION"
cp "$PSP_VERSION" "$PSP_CURRENT"
render_template "$TEMPLATE_ROOT/EVIDENCE_MATURITY.template.xml" "$EVIDENCE_VERSION"
cp "$EVIDENCE_VERSION" "$EVIDENCE_CURRENT"

cat > "$PERSON_DIR/ARTIFACTS.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<psp_artifacts schema="psp.artifacts.v1" person_id="$PERSON_ID" generated_at="$GENERATED_AT" language="$OUTPUT_LANGUAGE">
  <language_contract output_language="$OUTPUT_LANGUAGE">All PSP report prose, missing-information prompts, derived readables, runtime prompts, validation reports, and final disclosures must use this language unless preserving source quotes, file paths, XML tag names, or canonical protocol terms.</language_contract>
  <canonical_report current="current/PSP_REPORT.xml" version="versions/PSP_REPORT.$TS.xml"/>
  <evidence_maturity current="current/EVIDENCE_MATURITY.xml" version="versions/EVIDENCE_MATURITY.$TS.xml"/>
  <derived_artifacts root="derived/" source_of_truth="false"/>
  <soul_policy produced="false">SOUL.md is paused; PSP_REPORT.xml carries the person model and runtime constraints.</soul_policy>
</psp_artifacts>
EOF

if [ "$OUTPUT_LANGUAGE" = "zh-CN" ]; then
cat > "$PERSON_DIR/ARTIFACTS.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<psp_artifacts schema="psp.artifacts.v1" person_id="$PERSON_ID" generated_at="$GENERATED_AT" language="$OUTPUT_LANGUAGE">
  <language_contract output_language="$OUTPUT_LANGUAGE">所有 PSP 报告正文、缺失信息提示、派生读物、runtime prompt、验证报告和最终披露都必须使用该语言；原始引用、文件路径、XML 标签名、schema 名、产品名和协议固定术语可以保留原文。</language_contract>
  <canonical_report current="current/PSP_REPORT.xml" version="versions/PSP_REPORT.$TS.xml"/>
  <evidence_maturity current="current/EVIDENCE_MATURITY.xml" version="versions/EVIDENCE_MATURITY.$TS.xml"/>
  <derived_artifacts root="derived/" source_of_truth="false"/>
  <soul_policy produced="false">SOUL.md 暂停；PSP_REPORT.xml 承载人物模型和 runtime 约束。</soul_policy>
</psp_artifacts>
EOF
fi

cat > "$PERSON_DIR/derived/README.md" << 'EOF'
# Derived PSP Readables

Optional Markdown or HTML renderings can live here, but `../current/PSP_REPORT.xml` remains the source of truth.
EOF

if [ "$OUTPUT_LANGUAGE" = "zh-CN" ]; then
cat > "$PERSON_DIR/derived/README.md" << 'EOF'
# PSP 派生可读版本

这里可以放 Markdown 或 HTML 可读版本，但 `../current/PSP_REPORT.xml` 始终是唯一 source of truth。派生读物必须遵守 PSP XML 的 `language_contract`。
EOF
fi

if [ "$CREATE_RAW_MATERIALS" = "1" ]; then
cat > "$PERSON_DIR/raw_materials/meta.json" << EOF
{
  "person_id": "$PERSON_ID",
  "files": []
}
EOF
fi

# 创建分析中间产物的占位文件
cat > "$PERSON_DIR/analysis/conflict_stories.md" << EOF
# $PERSON_ID 冲突故事集

> 整理 ≥ 5 个 "两难选择"故事，作为 1.1 终极排序的输入。

## 故事 1
- 情境：
- 选了什么：
- 放弃了什么：
- 事后是否后悔：
- 来源：
- 表演系数：

EOF

cat > "$PERSON_DIR/analysis/pattern_observations.md" << EOF
# $PERSON_ID 经验模式观察记录

> 三场景一致才升级为模式。少于三场景标"单次观察"。

## 候选模式

| 候选模式 | 出现场景 1 | 场景 2 | 场景 3 | 状态 |
|---------|---------|--------|--------|------|

EOF

echo "[PSP] 完成。下一步："
echo ""
echo "  1. 已生成 PSP XML 版本产物：$PSP_VERSION"
echo "  2. 已同步 PSP XML current 入口：$PSP_CURRENT"
echo "  3. 已生成 evidence maturity XML：$EVIDENCE_CURRENT"
if [ "$CREATE_RAW_MATERIALS" = "1" ]; then
echo "  4. 把原始素材放入 $PERSON_DIR/raw_materials/ 对应子目录"
echo "  5. 编辑 $PERSON_DIR/raw_materials/meta.json，标注每份素材的表演系数"
echo "  6. 运行 doctor：python3 scripts/psp_doctor.py $PERSON_DIR"
echo "  7. 进入阶段一·建模流程（详见 SKILL.md）"
else
echo "  4. 原始素材不要写入 LifeOS repo；放在授权私有资料源，或临时使用 PSP repo 中已被 gitignore 的 people/ 工作区"
echo "  5. 运行 doctor：python3 scripts/psp_doctor.py $PERSON_DIR"
echo "  6. 进入阶段一·建模流程（详见 SKILL.md）"
fi
echo ""
echo "  抽取语言指纹（在素材就位后）："
echo "    python3 scripts/extract_fingerprint.py \\"
if [ "$CREATE_RAW_MATERIALS" = "1" ]; then
echo "        --input $PERSON_DIR/raw_materials/ \\"
else
echo "        --input <authorized_raw_materials_dir> \\"
fi
echo "        --output $PERSON_DIR/analysis/linguistic_fingerprint.json"
