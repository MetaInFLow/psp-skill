#!/bin/bash
# PSP v2.1 · 新建人物 PSP 产物目录脚本
#
# 用法：
#   bash init_person.sh <person_id>
#   bash init_person.sh <person_id> --output-root <dir>
#   bash init_person.sh <person_id> --lifeos-root <lifeos_repo>
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PSP_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_ROOT="$PSP_ROOT/people"
CREATE_RAW_MATERIALS="1"

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

PERSON_DIR="$OUTPUT_ROOT/$PERSON_ID"
TS="$(date +%Y%m%d-%H%M%S)"
PSP_VERSION="$PERSON_DIR/PSP-$TS.md"
PSP_CURRENT="$PERSON_DIR/PSP.md"

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
mkdir -p "$PERSON_DIR/analysis"
mkdir -p "$PERSON_DIR/validation/test_samples/human_samples"
mkdir -p "$PERSON_DIR/validation/test_samples/ai_outputs"
mkdir -p "$PERSON_DIR/validation/test_samples/judgment_test"

# 拷贝 PSP 模板作为带时间戳的版本产物，并同步 current 入口。
cp "$PSP_ROOT/templates/PSP_template.md" "$PSP_VERSION"
sed -i "s/{person_name}/$PERSON_ID/g; s/{person_id}/$PERSON_ID/g" "$PSP_VERSION" 2>/dev/null || \
    sed -i '' "s/{person_name}/$PERSON_ID/g; s/{person_id}/$PERSON_ID/g" "$PSP_VERSION"
cp "$PSP_VERSION" "$PSP_CURRENT"

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
echo "  1. 已生成版本产物：$PSP_VERSION"
echo "  2. 已同步 current 入口：$PSP_CURRENT"
if [ "$CREATE_RAW_MATERIALS" = "1" ]; then
echo "  3. 把原始素材放入 $PERSON_DIR/raw_materials/ 对应子目录"
echo "  4. 编辑 $PERSON_DIR/raw_materials/meta.json，标注每份素材的表演系数"
echo "  5. 进入阶段一·建模流程（详见 SKILL.md）"
else
echo "  3. 原始素材不要写入 LifeOS repo；放在授权私有资料源，或临时使用 PSP repo 中已被 gitignore 的 people/ 工作区"
echo "  4. 进入阶段一·建模流程（详见 SKILL.md）"
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
