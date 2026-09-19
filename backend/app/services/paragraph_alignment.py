"""段落级时间戳对齐 - 把ASR识别出的词/句子序列，匹配到老师人工分好的段落上

场景：老师按\n\n人工分段的原文 vs ASR识别出的词序列(带时间戳)，两者是同一份文本的
不同切分方式，本质是序列对齐问题（不是语义相似度问题），所以用
difflib.SequenceMatcher（最长公共子序列）而不是BLEU/编辑距离。

核心设计：段落是按顺序朗读的，这是一个非常强的先验——第N段一定出现在第N-1段
之后、第N+1段之前。早期实现忽略了这一点，让每个段落独立在"整段音频"范围内自由
匹配，导致短句/常见词段落（比如"Yes."、"M:"这种独立标签或简短应答）容易匹配到
音频里完全不相关、偶然撞上同一个词的位置——比如"yes"这种词，一段对话音频里
可能好几个地方都说过，段落本身信息量不够时，最长公共子序列会被拉到很远的
地方去凑，导致时间戳跨度离谱地宽（复现过的真实案例：一个两词短句被匹配到
横跨45秒，因为两个词分别在互不相关的两个位置各自命中了一次）。

现在改成"顺序游标+窗口"的匹配方式：维护一个游标，记录上一段匹配到的位置，
当前段落只在游标附近的一个窗口内搜索（允许少量回溯，容忍轻微重叠/顺序误差），
不再对整段音频全局搜索。这样从结构上就排除了"匹配到音频里很远地方"的可能性，
比单纯事后过滤离群匹配块更彻底——离群匹配块根本不会出现在候选范围里。
窗口内仍然保留了"取最大匹配块+合并邻近块"的过滤逻辑作为第二道保险，应对
窗口内仍然存在的孤立常见词干扰。
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict


def _normalize_words(text: str) -> List[str]:
    """小写化 + 去标点，按空格切词"""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return [w for w in text.split() if w]


# 窗口回溯容忍度（词数）：允许当前段落匹配到"游标往前退这么多词"的位置，
# 应对上一段落匹配略微超出真实范围、或两段之间有极轻微重叠朗读的情况。
# 数值不大，不足以让搜索重新触及很远之前的内容，不会重新引入"匹配到远处"的风险。
MAX_BACKTRACK = 10

# 窗口最小宽度（词数）：段落再短，也至少给这么大的搜索范围，
# 兜底应对ASR偶尔漏识别整段、导致游标滞后的情况
MIN_WINDOW_SIZE = 100

# 窗口宽度相对段落词数的放大倍数：段落越长，允许的搜索范围也按比例放宽，
# 兼顾ASR识别出的词数和原文词数不完全一一对应的情况
WINDOW_SIZE_MULTIPLIER = 8

# 合并匹配块时允许的最大间隔（按窗口内的相对索引计）。窗口本身已经大幅缩小了
# 搜索范围，这里是第二道保险，应对窗口内仍然存在的孤立常见词匹配
MAX_BLOCK_GAP = 15

# 匹配度低于这个阈值就不采信，按"未匹配"处理（start/end都记0，游标不推进）。
# 原因：如果只凭窗口内偶然撞上一两个常见词就接受一个很弱的匹配，不仅这一段
# 本身的时间戳不可信，还会把游标带到错误位置，连累后面本来能正确匹配的段落
# （连锁反应：弱匹配→游标错位→下一段窗口起点错了→下一段也可能匹配错）。
MIN_MATCH_SCORE = 0.3


def _select_core_blocks(blocks: list) -> list:
    """blocks 已按位置从小到大排序（SequenceMatcher的返回保证这一点）。
    以最大的匹配块为锚点（最可信，大概率是这句话真正所在的位置），向两侧合并
    相邻(间隔在MAX_BLOCK_GAP以内)的块，排除掉真正远离锚点、大概率只是偶然撞上
    同一个常见词/短语的离群匹配块。
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
    paragraphs: 老师人工分好的段落文本列表（已按朗读顺序排列）
    asr_words: [{"text": str, "start_ms": int, "end_ms": int}, ...] ASR的词级时间戳

    返回: [{"index": int, "text": str, "start": float, "end": float, "match_score": float}, ...]
    起止时间单位为秒。
    """
    # 把ASR词序列展开成"归一化词 -> 原始词条"的并行数组（全局，供窗口切片用）
    asr_norm_words: List[str] = []
    asr_word_refs: List[Dict] = []
    for item in asr_words:
        for w in _normalize_words(item.get("text", "")):
            asr_norm_words.append(w)
            asr_word_refs.append(item)

    total_words = len(asr_norm_words)
    results = []
    cursor = 0  # 上一段匹配结束的位置（ASR词序列的绝对索引），下一段从这附近开始找

    for idx, para in enumerate(paragraphs):
        para_norm_words = _normalize_words(para)

        if not para_norm_words or total_words == 0:
            results.append({
                "index": idx, "text": para, "start": 0.0, "end": 0.0, "match_score": 0.0
            })
            continue

        # 窗口范围：游标往前留一点回溯余量，往后按段落长度给足够搜索空间。
        # 只在这个窗口内搜索——这是防止匹配跑到音频里不相关位置的关键。
        window_start = max(0, cursor - MAX_BACKTRACK)
        window_size = max(MIN_WINDOW_SIZE, len(para_norm_words) * WINDOW_SIZE_MULTIPLIER)
        window_end = min(total_words, window_start + window_size)

        window_words = asr_norm_words[window_start:window_end]
        matcher = SequenceMatcher(None, window_words, para_norm_words, autojunk=False)
        blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]

        if not blocks:
            # 窗口内完全没匹配到：可能是ASR漏识别了这段。记为未匹配，游标不动，
            # 让下一段落仍然从这附近开始找，不至于因为这一段失败而整体错位
            results.append({
                "index": idx, "text": para, "start": 0.0, "end": 0.0, "match_score": 0.0
            })
            continue

        core_blocks = _select_core_blocks(blocks)
        first_block = core_blocks[0]
        last_block = core_blocks[-1]
        # 窗口内的相对索引换算回ASR词序列的全局索引
        start_asr_idx = window_start + first_block.a
        end_asr_idx = window_start + last_block.a + last_block.size - 1

        start_ms = asr_word_refs[start_asr_idx]["start_ms"]
        end_ms = asr_word_refs[end_asr_idx]["end_ms"]

        matched_word_count = sum(b.size for b in core_blocks)
        match_score = round(matched_word_count / len(para_norm_words), 2)

        if match_score < MIN_MATCH_SCORE:
            # 匹配度太低，大概率是窗口内偶然撞上一两个常见词的伪匹配，不采信，
            # 也不推进游标——避免这个不可靠的结果连累后面段落的搜索起点
            results.append({
                "index": idx, "text": para, "start": 0.0, "end": 0.0, "match_score": match_score
            })
            continue

        results.append({
            "index": idx,
            "text": para,
            "start": round(start_ms / 1000, 2),
            "end": round(end_ms / 1000, 2),
            "match_score": match_score,
        })

        # 推进游标到这段匹配到的结尾，下一段从这附近继续找——
        # 这一步是保证"顺序"先验能持续生效的关键
        cursor = end_asr_idx + 1

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
