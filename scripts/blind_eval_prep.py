#!/usr/bin/env python3
"""
PSP v2.1 · 盲评测试包准备

用于阶段三 · 测量 A（语言保真度）。
随机混排真人原话和 AI 输出，生成评估表交给熟人盲评。

输入：
  --human-samples: 真人原话样本目录（每个文件是一段真人原话，至少 20 段）
  --ai-samples: AI 输出样本目录（每个文件是一段 AI 输出，至少 20 段）
  --output: 输出目录（生成评估表 + 答案 key）

用法：
    python blind_eval_prep.py \\
        --human-samples people/zhang_san/validation/test_samples/human_samples/ \\
        --ai-samples people/zhang_san/validation/test_samples/ai_outputs/ \\
        --output people/zhang_san/validation/blind_eval/

产出：
  output/blind_eval_form.md          —— 给评估人看的表格
  output/blind_eval_answer_key.json   —— 答案 key（评估完后再公开）
"""

import argparse
import json
import random
import sys
from pathlib import Path


def read_samples(directory: str) -> list:
    """读取目录下所有文本文件作为样本。"""
    p = Path(directory)
    samples = []
    for ext in (".txt", ".md"):
        for f in sorted(p.rglob(f"*{ext}")):
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = f.read_text(encoding="gbk", errors="ignore")
            text = text.strip()
            if text and len(text) >= 30:  # 太短的样本跳过
                samples.append({
                    "filename": f.name,
                    "text": text,
                })
    return samples


def main():
    parser = argparse.ArgumentParser(description="PSP v2.1 盲评测试包准备")
    parser.add_argument("--human-samples", required=True, help="真人原话样本目录")
    parser.add_argument("--ai-samples", required=True, help="AI 输出样本目录")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--n-each", type=int, default=20, help="每类抽取数量（default 20）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    # 读取样本
    print(f"[PSP] 读取真人样本...")
    human = read_samples(args.human_samples)
    print(f"[PSP] 读取 AI 样本...")
    ai = read_samples(args.ai_samples)
    
    if len(human) < args.n_each:
        print(f"[错误] 真人样本仅 {len(human)} 段，需至少 {args.n_each} 段", file=sys.stderr)
        sys.exit(1)
    if len(ai) < args.n_each:
        print(f"[错误] AI 样本仅 {len(ai)} 段，需至少 {args.n_each} 段", file=sys.stderr)
        sys.exit(1)
    
    # 随机抽取并标记
    selected_human = random.sample(human, args.n_each)
    selected_ai = random.sample(ai, args.n_each)
    
    items = []
    for s in selected_human:
        items.append({"text": s["text"], "source": "human", "filename": s["filename"]})
    for s in selected_ai:
        items.append({"text": s["text"], "source": "ai", "filename": s["filename"]})
    
    # 打乱
    random.shuffle(items)
    
    # 编号
    for i, item in enumerate(items):
        item["number"] = i + 1
    
    # 输出
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 评估表（给评估人看）
    form_path = output_dir / "blind_eval_form.md"
    with open(form_path, "w", encoding="utf-8") as f:
        f.write("# 盲评测试表\n\n")
        f.write("## 说明\n\n")
        f.write("以下是 40 段文字。每段可能是真人原话，也可能是 AI 生成。\n\n")
        f.write("请你判断每一段是【真人】还是【AI】，在表格末尾填写。\n\n")
        f.write("**只看文字本身，不要被任何线索误导。**\n\n")
        f.write("---\n\n")
        for item in items:
            f.write(f"### 段落 #{item['number']}\n\n")
            f.write(f"{item['text']}\n\n")
            f.write(f"**判断：** ☐ 真人  ☐ AI\n\n")
            f.write("---\n\n")
        
        f.write("\n\n## 你的答案汇总\n\n")
        f.write("（评估完所有段落后，把判断填在下面这张表里）\n\n")
        f.write("| 段落 | 你的判断（真人/AI） |\n")
        f.write("|------|--------------------|\n")
        for item in items:
            f.write(f"| #{item['number']} |  |\n")
    
    # 答案 key（评估完后再公开）
    key_path = output_dir / "blind_eval_answer_key.json"
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "n_human": args.n_each,
                "n_ai": args.n_each,
                "total": len(items),
                "seed": args.seed,
            },
            "answers": [
                {
                    "number": item["number"],
                    "true_source": item["source"],
                    "filename": item["filename"],
                }
                for item in items
            ],
        }, f, ensure_ascii=False, indent=2)
    
    # 评估结果计算脚本提示
    eval_script_path = output_dir / "compute_score.py"
    eval_script = '''#!/usr/bin/env python3
"""
评估完成后，运行此脚本计算识别准确率。

用法：
  1. 把每个评估人的判断填入 evaluator_responses.json，格式如下：
     {
       "evaluator_1": {"1": "human", "2": "ai", ...},
       "evaluator_2": {...}
     }
  2. python compute_score.py
"""

import json
from pathlib import Path

key = json.loads(Path("blind_eval_answer_key.json").read_text(encoding="utf-8"))
true_answers = {str(a["number"]): a["true_source"] for a in key["answers"]}
total = len(true_answers)

resp_path = Path("evaluator_responses.json")
if not resp_path.exists():
    print("请先创建 evaluator_responses.json，参考脚本顶部说明。")
    exit(1)

responses = json.loads(resp_path.read_text(encoding="utf-8"))

print("\\n=== 盲评测试结果 ===")
print(f"通过阈值：识别准确率 ≤ 60%（即评估人无法可靠区分）\\n")

per_evaluator = []
for name, ans in responses.items():
    correct = sum(1 for n, true in true_answers.items() if ans.get(n) == true)
    acc = correct / total
    per_evaluator.append((name, correct, total, acc))
    status = "✅ 通过" if acc <= 0.6 else ("⚠️ 边界" if acc <= 0.7 else "❌ 不通过")
    print(f"{name:<15} {correct}/{total} = {acc*100:.1f}%  {status}")

avg_acc = sum(x[3] for x in per_evaluator) / len(per_evaluator)
print(f"\\n平均准确率：{avg_acc*100:.1f}%")
print(f"总体状态：{'✅ 语言保真度通过' if avg_acc <= 0.6 else '❌ 语言保真度不通过'}")
'''
    eval_script_path.write_text(eval_script, encoding="utf-8")
    
    print(f"\n=== 盲评测试包已生成 ===")
    print(f"评估表：{form_path}")
    print(f"答案 key（先不要给评估人看）：{key_path}")
    print(f"打分脚本：{eval_script_path}")
    print(f"\n下一步：")
    print(f"  1. 把 blind_eval_form.md 发给至少 5 名熟悉本人的评估人")
    print(f"  2. 收集判断结果，整理到 evaluator_responses.json")
    print(f"  3. 运行 python compute_score.py 计算准确率")
    print(f"  4. 准确率 ≤ 60% 视为语言保真度通过")


if __name__ == "__main__":
    main()
