#!/bin/bash
# PSP v2.1 · 新建人物目录脚本
#
# 用法：
#   bash init_person.sh <person_id>
#
# 例：
#   bash init_person.sh zhang_san

set -e

if [ -z "$1" ]; then
    echo "用法：bash init_person.sh <person_id>"
    echo "例：  bash init_person.sh zhang_san"
    exit 1
fi

PERSON_ID="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PSP_ROOT="$(dirname "$SCRIPT_DIR")"
PERSON_DIR="$PSP_ROOT/people/$PERSON_ID"

if [ -d "$PERSON_DIR" ]; then
    echo "[错误] 目录已存在：$PERSON_DIR"
    echo "如需重建，请先删除现有目录。"
    exit 1
fi

echo "[PSP] 创建人物目录：$PERSON_DIR"

mkdir -p "$PERSON_DIR/raw_materials/chat_logs"
mkdir -p "$PERSON_DIR/raw_materials/speeches"
mkdir -p "$PERSON_DIR/raw_materials/emails"
mkdir -p "$PERSON_DIR/raw_materials/interviews"
mkdir -p "$PERSON_DIR/analysis"
mkdir -p "$PERSON_DIR/validation/test_samples/human_samples"
mkdir -p "$PERSON_DIR/validation/test_samples/ai_outputs"
mkdir -p "$PERSON_DIR/validation/test_samples/judgment_test"

# 拷贝 PSP 模板作为初始 PSP.md
cp "$PSP_ROOT/templates/PSP_template.md" "$PERSON_DIR/PSP.md"
sed -i "s/{person_name}/$PERSON_ID/g; s/{person_id}/$PERSON_ID/g" "$PERSON_DIR/PSP.md" 2>/dev/null || \
    sed -i '' "s/{person_name}/$PERSON_ID/g; s/{person_id}/$PERSON_ID/g" "$PERSON_DIR/PSP.md"

# 创建空的 meta.json
cat > "$PERSON_DIR/raw_materials/meta.json" << EOF
{
  "person_id": "$PERSON_ID",
  "files": []
}
EOF

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
echo "  1. 把原始素材放入 $PERSON_DIR/raw_materials/ 对应子目录"
echo "  2. 编辑 $PERSON_DIR/raw_materials/meta.json，标注每份素材的表演系数"
echo "  3. 进入阶段一·建模流程（详见 SKILL.md）"
echo ""
echo "  抽取语言指纹（在素材就位后）："
echo "    python3 scripts/extract_fingerprint.py \\"
echo "        --input $PERSON_DIR/raw_materials/ \\"
echo "        --output $PERSON_DIR/analysis/linguistic_fingerprint.json"
