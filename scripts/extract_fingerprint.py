#!/usr/bin/env python3
"""
PSP v2.1 · 12 维度语言指纹提取

输入：一个文本文件或目录（包含此人的真实语料）
输出：JSON 文件，含可量化的语言指纹特征

用法：
    python extract_fingerprint.py --input <file_or_dir> --output <output.json>
    python extract_fingerprint.py --input people/zhang_san/raw_materials/ \
        --output people/zhang_san/analysis/linguistic_fingerprint.json
    python extract_fingerprint.py --input <authorized_raw_materials_dir> \
        --output identity/psp/zhang_san/analysis/linguistic_fingerprint.json

支持中文与英文混合语料。
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


# ============================================================
# 文本读取与预处理
# ============================================================

def read_text(path: Path) -> str:
    """读取一个文件的文本内容。支持 .txt .md。"""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="ignore")


def collect_corpus(input_path: str) -> str:
    """从一个文件或目录收集所有文本。"""
    p = Path(input_path)
    if p.is_file():
        return read_text(p)
    
    texts = []
    for ext in (".txt", ".md"):
        for f in p.rglob(f"*{ext}"):
            texts.append(read_text(f))
    return "\n\n".join(texts)


# ============================================================
# 中文友好的句子切分
# ============================================================

SENT_END = re.compile(r"[。！？!?]+|\n\n+")

def split_sentences(text: str) -> list:
    """切分为句子。"""
    # 先按段落切，再按句末标点切
    sentences = []
    for para in re.split(r"\n\n+", text):
        para = para.strip()
        if not para:
            continue
        # 按句末标点切
        parts = re.split(r"([。！？!?]+)", para)
        buf = ""
        for i, part in enumerate(parts):
            if not part:
                continue
            if re.match(r"[。！？!?]+", part):
                buf += part
                if buf.strip():
                    sentences.append(buf.strip())
                buf = ""
            else:
                buf += part
        if buf.strip():
            sentences.append(buf.strip())
    return [s for s in sentences if s]


def char_count(text: str) -> int:
    """统计中文字符数 + 英文单词数（粗略）"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = len(re.findall(r"\b[a-zA-Z]+\b", text))
    return chinese_chars + english_words


# ============================================================
# 12 维度提取
# ============================================================

def dim_1_information_density(sentences: list) -> dict:
    """维度 1：信息密度（平均句长）"""
    if not sentences:
        return {"avg_sentence_length": 0, "median": 0}
    lengths = [char_count(s) for s in sentences]
    lengths.sort()
    n = len(lengths)
    median = lengths[n // 2] if n else 0
    return {
        "avg_sentence_length": round(sum(lengths) / n, 2),
        "median": median,
        "total_sentences": n,
    }


def dim_2_sentence_length_distribution(sentences: list) -> dict:
    """维度 2：句长分布"""
    if not sentences:
        return {}
    short = sum(1 for s in sentences if char_count(s) < 10)
    medium = sum(1 for s in sentences if 10 <= char_count(s) < 30)
    long_ = sum(1 for s in sentences if char_count(s) >= 30)
    total = len(sentences)
    return {
        "short_pct": round(100 * short / total, 1),
        "medium_pct": round(100 * medium / total, 1),
        "long_pct": round(100 * long_ / total, 1),
        "describe": _describe_distribution(short, medium, long_, total),
    }


def _describe_distribution(s, m, l, t):
    if t == 0:
        return "样本不足"
    if s / t > 0.5:
        return "偏短句"
    if l / t > 0.4:
        return "偏长句"
    return "短长交替"


def dim_3_logic_unfold(sentences: list) -> dict:
    """维度 3：逻辑展开（先结论后论据 vs 先铺陈后结论）"""
    # 启发式：检查段落首句是否含有判断词/结论性表达
    conclusion_starters = [
        "我认为", "我看", "我觉得", "我说",
        "应该", "必须", "不行", "可以",
        "对", "不对", "是的", "不是",
        "结论是", "答案是", "关键是",
    ]
    background_starters = [
        "在当前", "考虑到", "首先", "从某种意义",
        "在我们", "随着", "由于", "因为",
        "众所周知", "我们都知道",
    ]
    
    conclusion_count = 0
    background_count = 0
    for s in sentences[:200]:  # 取前 200 句采样
        s_strip = s.strip()
        for w in conclusion_starters:
            if s_strip.startswith(w):
                conclusion_count += 1
                break
        for w in background_starters:
            if s_strip.startswith(w):
                background_count += 1
                break
    
    if conclusion_count + background_count == 0:
        return {"pattern": "未明显特征", "samples": 0}
    
    if conclusion_count > background_count * 1.5:
        pattern = "先结论后论据"
    elif background_count > conclusion_count * 1.5:
        pattern = "先铺陈后结论"
    else:
        pattern = "混合"
    
    return {
        "pattern": pattern,
        "conclusion_starters_count": conclusion_count,
        "background_starters_count": background_count,
    }


def dim_4_abstraction_level(text: str) -> dict:
    """维度 4：抽象程度（类比/数据频率比）"""
    analogy_markers = ["就像", "好比", "相当于", "如同", "犹如", "打个比方"]
    data_markers = re.findall(r"\d+(?:\.\d+)?(?:%|百分|万|亿|千|个|倍)", text)
    
    analogy_count = sum(text.count(m) for m in analogy_markers)
    data_count = len(data_markers)
    
    total_chars = char_count(text)
    norm = max(total_chars / 10000, 1)
    
    return {
        "analogy_freq_per_10k_char": round(analogy_count / norm, 2),
        "data_freq_per_10k_char": round(data_count / norm, 2),
        "ratio_analogy_to_data": round(analogy_count / max(data_count, 1), 2),
    }


def dim_5_emotional_intensity(text: str) -> dict:
    """维度 5：情绪表达强度"""
    strong_negative = ["不行", "不对", "胡扯", "扯淡", "屁话", "差远了", "毛病"]
    soft_negative = ["可能不太", "也许", "我觉得不太", "不一定"]
    strong_positive = ["对", "好", "可以", "棒"]
    soft_positive = ["还行", "还可以", "差不多"]
    
    norm = max(char_count(text) / 10000, 1)
    
    return {
        "strong_negative_per_10k": round(sum(text.count(w) for w in strong_negative) / norm, 2),
        "soft_negative_per_10k": round(sum(text.count(w) for w in soft_negative) / norm, 2),
        "strong_positive_per_10k": round(sum(text.count(w) for w in strong_positive) / norm, 2),
        "soft_positive_per_10k": round(sum(text.count(w) for w in soft_positive) / norm, 2),
    }


def dim_6_transition_markers(text: str) -> dict:
    """维度 6：转折与停顿标记"""
    markers = [
        "但是", "不过", "其实", "说白了", "换句话说", "也就是说",
        "我说", "你听我说", "话说回来", "反过来说",
        "事实上", "实际上", "本质上",
    ]
    norm = max(char_count(text) / 10000, 1)
    return {
        m: round(text.count(m) / norm, 2)
        for m in markers
    }


def dim_7_negation_preference(text: str) -> dict:
    """维度 7：否定与让步偏好"""
    direct_negation = ["这不对", "不行", "不是这样", "错了"]
    concessive = ["有道理但是", "可以理解但是", "我能理解但是"]
    softened = ["我不是说", "也不是不行", "倒不是说"]
    
    norm = max(char_count(text) / 10000, 1)
    return {
        "direct_negation_per_10k": round(sum(text.count(w) for w in direct_negation) / norm, 2),
        "concessive_per_10k": round(sum(text.count(w) for w in concessive) / norm, 2),
        "softened_per_10k": round(sum(text.count(w) for w in softened) / norm, 2),
    }


def dim_8_function_words(text: str) -> dict:
    """维度 8：高频功能词偏好"""
    # 功能词组：每组里此人最常用哪个？
    groups = {
        "我_认为": ["我觉得", "我认为", "我看", "依我说", "我的看法"],
        "重要": ["重要", "关键", "核心", "要紧"],
        "问题": ["问题", "毛病", "麻烦", "事儿"],
        "做得好": ["很好", "非常好", "对", "可以", "棒", "牛"],
    }
    
    result = {}
    for group_name, words in groups.items():
        counts = {w: text.count(w) for w in words}
        total = sum(counts.values()) or 1
        # 找最高频
        top = max(counts.items(), key=lambda x: x[1])
        result[group_name] = {
            "preferred": top[0] if top[1] > 0 else "未观察到",
            "counts": counts,
            "preference_ratio": round(top[1] / total, 2),
        }
    return result


def dim_9_signature_phrases(text: str, top_k: int = 20) -> dict:
    """维度 9：标志性用语（高频 n-gram）"""
    # 抽取 3-5 字的中文 n-gram
    text_clean = re.sub(r"[^\u4e00-\u9fff]", "", text)
    
    ngram_counts = Counter()
    for n in (3, 4, 5):
        for i in range(len(text_clean) - n + 1):
            gram = text_clean[i:i+n]
            ngram_counts[gram] += 1
    
    # 自适应阈值：语料越大要求频次越高，避免噪声 n-gram
    text_size = len(text_clean)
    if text_size < 1000:
        min_freq = 2
    elif text_size < 10000:
        min_freq = 3
    else:
        min_freq = max(3, text_size // 5000)
    
    common = [(g, c) for g, c in ngram_counts.most_common(top_k * 3) if c >= min_freq]
    return {
        "top_ngrams": [{"phrase": g, "count": c} for g, c in common[:top_k]],
        "min_freq_threshold": min_freq,
    }


def dim_10_humor_markers(text: str) -> dict:
    """维度 10：幽默风格（粗略检测）"""
    self_mockery = ["我这个人", "我这种", "我也是", "也就我"]
    sarcasm = ["可不是吗", "可不", "嘿嘿", "呵呵"]
    exaggeration = ["简直", "完全", "彻底", "压根"]
    
    norm = max(char_count(text) / 10000, 1)
    return {
        "self_mockery_per_10k": round(sum(text.count(w) for w in self_mockery) / norm, 2),
        "sarcasm_per_10k": round(sum(text.count(w) for w in sarcasm) / norm, 2),
        "exaggeration_per_10k": round(sum(text.count(w) for w in exaggeration) / norm, 2),
    }


def dim_11_register_switching(text: str) -> dict:
    """维度 11：语域切换（粗略检测正式度）"""
    formal_markers = ["此外", "由此", "从而", "据此", "鉴于", "综上"]
    informal_markers = ["嘛", "呗", "哈", "哦", "嘿", "啊", "呀"]
    
    norm = max(char_count(text) / 10000, 1)
    formal = sum(text.count(w) for w in formal_markers) / norm
    informal = sum(text.count(w) for w in informal_markers) / norm
    
    if formal + informal == 0:
        register = "中性"
    elif informal > formal * 2:
        register = "偏非正式"
    elif formal > informal * 2:
        register = "偏正式"
    else:
        register = "混合"
    
    return {
        "formal_markers_per_10k": round(formal, 2),
        "informal_markers_per_10k": round(informal, 2),
        "register_describe": register,
    }


def dim_12_rhythm_markers(text: str) -> dict:
    """维度 12：节奏标记（停顿用词、强调位置）"""
    pause_markers = ["对", "嗯", "你看", "这样", "这么说"]
    emphasis_end = ["对不对", "是不是", "你说呢", "明白吗"]
    
    norm = max(char_count(text) / 10000, 1)
    return {
        "pause_markers_per_10k": round(sum(text.count(w) for w in pause_markers) / norm, 2),
        "emphasis_end_per_10k": round(sum(text.count(w) for w in emphasis_end) / norm, 2),
    }


# ============================================================
# 主流程
# ============================================================

def extract_all_dimensions(text: str) -> dict:
    """提取全部 12 维度。"""
    sentences = split_sentences(text)
    
    return {
        "metadata": {
            "total_chars": char_count(text),
            "total_sentences": len(sentences),
        },
        "dim_1_information_density": dim_1_information_density(sentences),
        "dim_2_sentence_length_distribution": dim_2_sentence_length_distribution(sentences),
        "dim_3_logic_unfold": dim_3_logic_unfold(sentences),
        "dim_4_abstraction_level": dim_4_abstraction_level(text),
        "dim_5_emotional_intensity": dim_5_emotional_intensity(text),
        "dim_6_transition_markers": dim_6_transition_markers(text),
        "dim_7_negation_preference": dim_7_negation_preference(text),
        "dim_8_function_words": dim_8_function_words(text),
        "dim_9_signature_phrases": dim_9_signature_phrases(text),
        "dim_10_humor_markers": dim_10_humor_markers(text),
        "dim_11_register_switching": dim_11_register_switching(text),
        "dim_12_rhythm_markers": dim_12_rhythm_markers(text),
    }


def main():
    parser = argparse.ArgumentParser(description="PSP v2.1 12 维度语言指纹提取")
    parser.add_argument("--input", required=True, help="输入文件或目录")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    args = parser.parse_args()
    
    print(f"[PSP] 读取语料：{args.input}")
    text = collect_corpus(args.input)
    if not text.strip():
        print("[PSP] 错误：未找到任何文本内容", file=sys.stderr)
        sys.exit(1)
    
    print(f"[PSP] 总字符数：{char_count(text)}")
    print(f"[PSP] 提取 12 维度语言指纹...")
    result = extract_all_dimensions(text)
    
    # 写出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"[PSP] 完成。结果写入：{args.output}")
    
    # 打印关键指标
    print("\n=== 关键指标摘要 ===")
    print(f"平均句长：{result['dim_1_information_density']['avg_sentence_length']} 字")
    print(f"句长分布：{result['dim_2_sentence_length_distribution']['describe']}")
    print(f"逻辑展开：{result['dim_3_logic_unfold']['pattern']}")
    print(f"语域：{result['dim_11_register_switching']['register_describe']}")
    print(f"\n标志性用语 Top 10：")
    for item in result['dim_9_signature_phrases']['top_ngrams'][:10]:
        print(f"  {item['phrase']:<10} ({item['count']} 次)")


if __name__ == "__main__":
    main()
