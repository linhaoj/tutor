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


# 合并匹配块时允许的最大间隔（按ASR词序列的索引数计，不是秒数）。
# 段落内部因为标点/缩写等细微差异被拆成几个相邻小块是正常的，间隔应该很小；
# 真正不相关、偶然撞上同一个常见词的"离群"匹配块，通常隔着几十甚至上百个词，
# 用这个阈值就能把它们排除在外，不让它们把段落的起止时间拉到音频里完全不对的位置
MAX_BLOCK_GAP = 15


def _select_core_blocks(blocks: list) -> list:
    """blocks 已按ASR词序列位置(a)从小到大排序（SequenceMatcher的返回保证这一点）。
    以最大的匹配块为锚点（最可信，大概率是这句话真正所在的位置），向两侧合并
    相邻(间隔在MAX_BLOCK_GAP以内)的块，排除掉真正远离锚点、大概率只是偶然撞上
    同一个常见词/短语的离群匹配块——避免整段的起止时间被这种孤立匹配拉歪。
    """
    if not blocks:
        return []
    anchor_idx = max(range(len(blocks)), key=lambda i: blocks[i].size)

    core = [blocks[anchor_idx]]
    for b in blocks[anchor_idx + 1:]:
        prev_end = core[-1].a + core[-1].size
        if b.a - prev_end > MAX_BLOCK_GAP:
            break
        core.append(b)
    for b in reversed(blocks[:anchor_idx]):
        next_start = core[0].a
        if next_start - (b.a + b.size) > MAX_BLOCK_GAP:
            break
        core.insert(0, b)
    return core


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

        # 只用"核心"匹配块（离最大匹配块不远的那些）算时间范围，排除偶然撞上
        # 常见词导致的离群匹配，否则句子起止时间会被错误地拉到音频里很远的位置
        core_blocks = _select_core_blocks(blocks)
        first_block = core_blocks[0]
        last_block = core_blocks[-1]
        start_asr_idx = first_block.a
        end_asr_idx = last_block.a + last_block.size - 1

        start_ms = asr_word_refs[start_asr_idx]["start_ms"]
        end_ms = asr_word_refs[end_asr_idx]["end_ms"]

        # 匹配度也用核心块统计，不被离群匹配虚高
        matched_word_count = sum(b.size for b in core_blocks)
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
