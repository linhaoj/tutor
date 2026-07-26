"""段落级时间戳对齐 - 把ASR识别出的词/句子序列，匹配到老师人工分好的段落上

场景：老师按\n\n人工分段的原文 vs 腾讯云ASR识别出的词序列(带时间戳)，
两者是同一份文本的不同切分方式，本质是序列对齐问题（不是语义相似度问题），
所以用 difflib.SequenceMatcher（最长公共子序列）而不是BLEU/编辑距离。
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict


def _normalize_words(text: str) -> List[str]:
    """小写化 + 去标点，按空格切词"""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return [w for w in text.split() if w]


def align_paragraphs_to_asr(paragraphs: List[str], asr_words: List[Dict]) -> List[Dict]:
    """
    paragraphs: 老师人工分好的段落文本列表
    asr_words: [{"text": str, "start_ms": int, "end_ms": int}, ...] 腾讯云ASR的词级时间戳

    返回: [{"index": int, "text": str, "start": float, "end": float, "match_score": float}, ...]
    起止时间单位为秒。
    """
    # 把ASR词序列展开成"归一化词 -> 原始词条"的并行数组
    asr_norm_words: List[str] = []
    asr_word_refs: List[Dict] = []
    for item in asr_words:
        for w in _normalize_words(item.get("text", "")):
            asr_norm_words.append(w)
            asr_word_refs.append(item)

    results = []
    for idx, para in enumerate(paragraphs):
        para_norm_words = _normalize_words(para)

        if not para_norm_words or not asr_norm_words:
            results.append({
                "index": idx, "text": para, "start": 0.0, "end": 0.0, "match_score": 0.0
            })
            continue

        matcher = SequenceMatcher(None, asr_norm_words, para_norm_words, autojunk=False)
        blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]

        if not blocks:
            results.append({
                "index": idx, "text": para, "start": 0.0, "end": 0.0, "match_score": 0.0
            })
            continue

        # 匹配块在asr_norm_words里的位置范围，取第一个块的起点、最后一个块的终点
        first_block = blocks[0]
        last_block = blocks[-1]
        start_asr_idx = first_block.a
        end_asr_idx = last_block.a + last_block.size - 1

        start_ms = asr_word_refs[start_asr_idx]["start_ms"]
        end_ms = asr_word_refs[end_asr_idx]["end_ms"]

        matched_word_count = sum(b.size for b in blocks)
        match_score = round(matched_word_count / len(para_norm_words), 2)

        results.append({
            "index": idx,
            "text": para,
            "start": round(start_ms / 1000, 2),
            "end": round(end_ms / 1000, 2),
            "match_score": match_score,
        })

    _bridge_gaps(results)
    return results


def _bridge_gaps(results: List[Dict]) -> None:
    """把第x段的开头对齐为第x-1段的结尾，消除段落间的空隙，
    避免播放到段落末尾时因为提前截断而漏掉最后一个词的尾音。

    跳过未匹配到的段落（start/end 都是 0）：既不能作为拼接锚点，
    自身也没有真实时间戳可言，强行拼接反而会引入错误的时间范围。
    """
    for i in range(1, len(results)):
        prev = results[i - 1]
        curr = results[i]

        prev_valid = prev["end"] > 0 or prev["start"] > 0
        curr_valid = curr["end"] > 0 or curr["start"] > 0
        if not prev_valid or not curr_valid:
            continue

        # 有空隙（curr比prev晚开始）时，把curr的开头拉到prev的结尾，消除间隙。
        # 只在不会导致start > end的情况下才拼接，避免乱序重叠时产生无效区间。
        if curr["start"] > prev["end"] and prev["end"] <= curr["end"]:
            curr["start"] = prev["end"]
