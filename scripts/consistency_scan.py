#!/usr/bin/env python3
"""
PSP v2.1 · 风格一致性扫描

用于阶段三 · 测量 C。
对比 AI 输出的语言指纹方差与真人语料同维度方差，判断风格一致性是否通过。

输入：
  --ai-outputs: AI 输出样本目录（每个文件是一段 AI 回答）
  --human-baseline: 真人语料的语言指纹 JSON（来自 extract_fingerprint.py）
  --output: 输出报告 JSON

通过条件：所有维度的 AI/真人方差比 ≤ 1.5

用法：
    python consistency_scan.py \\
        --ai-outputs people/zhang_san/validation/test_samples/ai_outputs/ \\
        --human-baseline people/zhang_san/analysis/linguistic_fingerprint.json \\
        --output people/zhang_san/validation/consistency_report.json
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

# 复用 extract_fingerprint.py 的提取函数
sys.path.insert(0, str(Path(__file__).parent))
from extract_fingerprint import extract_all_dimensions, read_text


# ============================================================
# 可量化维度提取（用于方差计算）
# ============================================================

def extract_quantitative_features(fingerprint: dict) -> dict:
    """从一个 fingerprint JSON 中抽取所有可量化的标量特征。"""
    features = {}
    
    # 维度 1
    d1 = fingerprint.get("dim_1_information_density", {})
    features["avg_sentence_length"] = d1.get("avg_sentence_length", 0)
    features["sentence_median"] = d1.get("median", 0)
    
    # 维度 2
    d2 = fingerprint.get("dim_2_sentence_length_distribution", {})
    features["short_pct"] = d2.get("short_pct", 0)
    features["medium_pct"] = d2.get("medium_pct", 0)
    features["long_pct"] = d2.get("long_pct", 0)
    
    # 维度 4
    d4 = fingerprint.get("dim_4_abstraction_level", {})
    features["analogy_freq"] = d4.get("analogy_freq_per_10k_char", 0)
    features["data_freq"] = d4.get("data_freq_per_10k_char", 0)
    
    # 维度 5
    d5 = fingerprint.get("dim_5_emotional_intensity", {})
    features["strong_negative"] = d5.get("strong_negative_per_10k", 0)
    features["soft_negative"] = d5.get("soft_negative_per_10k", 0)
    features["strong_positive"] = d5.get("strong_positive_per_10k", 0)
    
    # 维度 6（前几个高频转折标记）
    d6 = fingerprint.get("dim_6_transition_markers", {})
    for key in ["但是", "其实", "说白了", "实际上"]:
        features[f"transition_{key}"] = d6.get(key, 0)
    
    # 维度 7
    d7 = fingerprint.get("dim_7_negation_preference", {})
    features["direct_negation"] = d7.get("direct_negation_per_10k", 0)
    features["concessive"] = d7.get("concessive_per_10k", 0)
    
    # 维度 10
    d10 = fingerprint.get("dim_10_humor_markers", {})
    features["self_mockery"] = d10.get("self_mockery_per_10k", 0)
    features["sarcasm"] = d10.get("sarcasm_per_10k", 0)
    
    # 维度 11
    d11 = fingerprint.get("dim_11_register_switching", {})
    features["formal"] = d11.get("formal_markers_per_10k", 0)
    features["informal"] = d11.get("informal_markers_per_10k", 0)
    
    # 维度 12
    d12 = fingerprint.get("dim_12_rhythm_markers", {})
    features["pause"] = d12.get("pause_markers_per_10k", 0)
    features["emphasis_end"] = d12.get("emphasis_end_per_10k", 0)
    
    return features


# ============================================================
# 方差计算
# ============================================================

def compute_variance(values: list) -> float:
    """计算方差。少于 2 个样本返回 0。"""
    if len(values) < 2:
        return 0.0
    return statistics.variance(values)


def compute_per_feature_variance(samples: list) -> dict:
    """对一组样本（每个样本是一个 fingerprint）计算每个特征的方差。"""
    if not samples:
        return {}
    
    # 收集每个特征的值列表
    feature_values = {}
    for sample in samples:
        features = extract_quantitative_features(sample)
        for k, v in features.items():
            feature_values.setdefault(k, []).append(v)
    
    # 计算方差
    return {k: round(compute_variance(v), 4) for k, v in feature_values.items()}


# ============================================================
# 真人语料的"伪方差"估计
# ============================================================

def estimate_human_variance_from_chunks(text: str, chunk_size: int = 5000) -> dict:
    """
    把真人语料切成多个块，每块独立提取指纹，计算块间方差。
    这是真人"内部一致性"的代理。
    """
    # 切块
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= chunk_size // 2:  # 太短的块跳过
            chunks.append(chunk)
    
    if len(chunks) < 3:
        print(f"[警告] 真人语料块数仅 {len(chunks)}，方差估计不稳定。建议增加语料。", file=sys.stderr)
    
    fingerprints = [extract_all_dimensions(c) for c in chunks]
    return compute_per_feature_variance(fingerprints)


# ============================================================
# 主流程
# ============================================================

def collect_ai_outputs(directory: str) -> list:
    """读取 AI 输出目录下所有文件，每个文件作为一个样本。"""
    p = Path(directory)
    samples = []
    for ext in (".txt", ".md"):
        for f in sorted(p.rglob(f"*{ext}")):
            text = read_text(f)
            if text.strip():
                samples.append(extract_all_dimensions(text))
    return samples


def main():
    parser = argparse.ArgumentParser(description="PSP v2.1 风格一致性扫描")
    parser.add_argument("--ai-outputs", required=True, help="AI 输出样本目录")
    parser.add_argument("--human-baseline", required=True, help="真人语料的指纹 JSON")
    parser.add_argument("--human-corpus", help="真人语料目录或文件（用于估计真人方差）")
    parser.add_argument("--output", required=True, help="输出报告 JSON")
    parser.add_argument("--threshold", type=float, default=1.5, help="通过阈值 ratio (default 1.5)")
    args = parser.parse_args()
    
    # 读取 AI 输出样本
    print(f"[PSP] 读取 AI 输出：{args.ai_outputs}")
    ai_samples = collect_ai_outputs(args.ai_outputs)
    if len(ai_samples) < 10:
        print(f"[警告] AI 样本仅 {len(ai_samples)} 个，建议至少 30 个。", file=sys.stderr)
    print(f"[PSP] AI 样本数：{len(ai_samples)}")
    
    # 计算 AI 方差
    ai_variance = compute_per_feature_variance(ai_samples)
    
    # 估计真人方差
    if args.human_corpus:
        print(f"[PSP] 从真人语料估计方差：{args.human_corpus}")
        from extract_fingerprint import collect_corpus
        human_text = collect_corpus(args.human_corpus)
        human_variance = estimate_human_variance_from_chunks(human_text)
    else:
        # 没有 corpus，从 baseline JSON 中估计（粗略）
        print(f"[PSP] 警告：未提供 --human-corpus，方差估计不准。建议提供原始语料。")
        baseline = json.loads(Path(args.human_baseline).read_text(encoding="utf-8"))
        # 用 baseline 的特征值作为单点，方差为 0——这种情况下 ratio 会爆炸
        human_features = extract_quantitative_features(baseline)
        # 为避免除零，给一个最小方差
        human_variance = {k: max(abs(v) * 0.1, 0.01) for k, v in human_features.items()}
    
    # 计算 ratio
    print(f"[PSP] 计算每维度方差比...")
    report = {
        "metadata": {
            "ai_sample_count": len(ai_samples),
            "threshold": args.threshold,
        },
        "feature_analysis": [],
    }
    
    pass_count = 0
    fail_count = 0
    
    for feature_name, ai_var in ai_variance.items():
        human_var = human_variance.get(feature_name, 0)
        if human_var == 0:
            ratio = float("inf") if ai_var > 0 else 0.0
        else:
            ratio = ai_var / human_var
        
        passed = ratio <= args.threshold
        if passed:
            pass_count += 1
        else:
            fail_count += 1
        
        report["feature_analysis"].append({
            "feature": feature_name,
            "ai_variance": ai_var,
            "human_variance": round(human_var, 4),
            "ratio": round(ratio, 2) if ratio != float("inf") else "inf",
            "passed": passed,
        })
    
    report["summary"] = {
        "passed_features": pass_count,
        "failed_features": fail_count,
        "total_features": pass_count + fail_count,
        "overall_pass": fail_count == 0,
    }
    
    # 写出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 打印摘要
    print(f"\n=== 一致性测试报告 ===")
    print(f"通过维度：{pass_count} / {pass_count + fail_count}")
    print(f"总体状态：{'✅ 通过' if report['summary']['overall_pass'] else '❌ 不通过'}")
    
    if fail_count > 0:
        print(f"\n失败维度（ratio > {args.threshold}）：")
        for item in report["feature_analysis"]:
            if not item["passed"]:
                print(f"  {item['feature']:<25} ratio={item['ratio']}")
    
    print(f"\n详细报告已写入：{args.output}")


if __name__ == "__main__":
    main()
