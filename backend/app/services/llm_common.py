"""LLM 调用公共逻辑 - 供阅读课、听力课等功能共用

原用 GitHub Models（models.github.ai），该服务已进入官方"retirement brownout"下线阶段
（错误码 github_models_retirement_brownout），改用智谱AI GLM（open.bigmodel.cn）作为过渡。

2026-09：纯文本生成（翻译、查词、文章生成）改用阿里云百炼/通义千问（付费，qwen3.7-flash），
免费额度并发太低导致频繁429限流；视觉/OCR（截图识别）暂时保留智谱GLM不动（够用，且OCR调用
频率低，429问题不明显）。所以本文件现在同时对接两个服务商：
- call_llm（纯文本）      → 阿里云百炼 DashScope（OpenAI兼容模式）
- call_vision_llm（视觉） → 智谱GLM

注意：两边都内置了429限流自动重试（指数退避），调用方不需要自己处理限流重试。
"""
import os
import re
import json
import time
import base64
import urllib.request
import urllib.error
from typing import List, Optional
from fastapi import HTTPException

# ── LLM 配置 ─────────────────────────────────────────────────
# 密钥从环境变量读取，配置在 backend/.env.local（不进git，需在本地和服务器上各自创建）

# 智谱GLM（仅视觉/OCR仍在用）
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4.6v-flash")
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 阿里云百炼/通义千问（纯文本生成，OpenAI兼容模式）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3.7-flash")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 429限流重试设置：免费额度并发数很低，简单退避重试几次即可缓解
RATE_LIMIT_MAX_RETRIES = 5
RATE_LIMIT_BACKOFF_SECONDS = 4

# 翻译分批设置：长文章（听力对话常有20-30轮）一次性请求容易导致：
# 1) 输出JSON被max_tokens截断，越到后面的段落越容易丢失或对不齐
# 2) 单次请求体积大、耗时长，更容易撞上免费额度的限流
# 因此按小批次分别翻译，每批独立校验+重试，互不影响
TRANSLATION_BATCH_SIZE = 8
TRANSLATION_BATCH_DELAY_SECONDS = 1.5


def count_words(text: str) -> int:
    return len(re.findall(r"\b[a-zA-Z']+\b", text))


def _call_zhipu_api(payload: dict, timeout: int, error_prefix: str) -> str:
    """向智谱GLM发起请求，内置429限流自动重试（指数退避）"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ZHIPU_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHIPU_API_KEY}",
        },
        method="POST"
    )

    last_error_detail = ""
    for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            if e.code == 429 and attempt < RATE_LIMIT_MAX_RETRIES:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS * (attempt + 1))
                continue
            raise HTTPException(status_code=502, detail=f"{error_prefix}: {e.code} {body}")
        except Exception as e:
            last_error_detail = str(e)
            break

    raise HTTPException(status_code=502, detail=f"{error_prefix}: {last_error_detail}")


def _call_dashscope_api(payload: dict, timeout: int, error_prefix: str) -> str:
    """向阿里云百炼(DashScope, OpenAI兼容模式)发起请求，内置429限流自动重试（指数退避）"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DASHSCOPE_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        },
        method="POST"
    )

    last_error_detail = ""
    for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            if e.code == 429 and attempt < RATE_LIMIT_MAX_RETRIES:
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS * (attempt + 1))
                continue
            raise HTTPException(status_code=502, detail=f"{error_prefix}: {e.code} {body}")
        except Exception as e:
            last_error_detail = str(e)
            break

    raise HTTPException(status_code=502, detail=f"{error_prefix}: {last_error_detail}")


def call_llm(prompt: str, max_tokens: int = 1024, model: Optional[str] = None) -> str:
    """调用通义千问文本模型（同步，供 executor 使用）"""
    if not DASHSCOPE_API_KEY:
        raise HTTPException(status_code=500, detail="DASHSCOPE_API_KEY 未配置，请在 backend/.env.local 中设置")

    payload = {
        "model": model or QWEN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": False,
        # qwen3.7系列是推理模型，默认可能开启思考模式，会把max_tokens耗在思考过程(reasoning_content)上
        # 导致真正需要的content为空——之前智谱GLM踩过同样的坑，这里直接关掉思考模式
        "enable_thinking": False,
    }
    return _call_dashscope_api(payload, timeout=60, error_prefix="LLM API 错误")


def call_vision_llm(prompt: str, image_bytes: bytes, mimetype: str, max_tokens: int = 2048) -> str:
    """调用智谱GLM视觉模型（同步，用于 OCR 图片识别）"""
    if not ZHIPU_API_KEY:
        raise HTTPException(status_code=500, detail="ZHIPU_API_KEY 未配置，请在 backend/.env.local 中设置")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": ZHIPU_VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mimetype};base64,{image_b64}"}}
            ]
        }],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False,
        # GLM-4.6V系列也是推理模型，关掉思考模式避免max_tokens被推理过程占满导致OCR结果被截断
        "thinking": {"type": "disabled"},
    }
    return _call_zhipu_api(payload, timeout=90, error_prefix="视觉模型 API 错误")


def build_translation_prompt(article: str, expected_count: Optional[int] = None) -> str:
    """article 内部段落必须用空行(\\n\\n)分隔，供 LLM 识别段落边界

    输出格式用"带编号的JSON对象"而不是纯数组：{"1": "...", "2": "...", ...}。
    纯数组有个隐患——如果模型偷偷把两段合并翻译成一条、又在末尾补一条凑数，返回的
    数组长度是对的，但内容早就错位了，光靠"数组长度是否等于段落数"根本查不出来。
    换成带编号的对象后，任何一段被漏翻译，都会直接表现为"缺了某个具体编号的key"，
    可以精确定位到是第几段出问题，而不是一个模糊的"数量不对"。
    """
    numbered_keys = ", ".join(str(i) for i in range(1, (expected_count or 1) + 1))
    count_rule = ""
    if expected_count:
        count_rule = f"""
CRITICAL - paragraph count: the passage above has EXACTLY {expected_count} paragraphs (separated by blank lines),
numbered 1 to {expected_count} in order. Your output JSON object MUST contain EXACTLY these keys: {numbered_keys}
— one key per paragraph number, every key as a plain string like "1", "2", etc.
This applies even to short paragraphs that are just a label, heading, or speaker tag (e.g. "Text 1", "Part A", "M:")
— NEVER skip, merge, or combine two paragraphs into one key, even if a paragraph looks untranslatable. If a
paragraph is not a real sentence, just output a reasonable Chinese equivalent (or keep it as-is) as its own
key — do NOT omit any key, since that would make it impossible to tell which paragraph is missing its translation.
"""
    return f"""You are a professional translator. Translate the following English passage into Simplified Chinese (简体中文).

Rules:
1. Translate paragraph by paragraph — each English paragraph must have a complete, accurate Chinese translation of the SAME content.
2. Do NOT summarize, shorten, or skip any sentences. Every sentence must be translated in full.
3. Use Simplified Chinese characters only (NOT Traditional Chinese).
4. CRITICAL: Every single English word must be translated into Chinese. Do NOT leave any English words, phrases, or terms in the output. Not even technical terms, proper nouns, or difficult words — find a Chinese equivalent for everything.
5. Output ONLY a JSON object mapping paragraph number (as a string) to its Chinese translation.
6. No extra explanation, no markdown formatting, just the raw JSON object.
{count_rule}

Example output format: {{"1": "第一段完整翻译", "2": "第二段完整翻译"}}

English passage (paragraph N is the N-th block separated by a blank line, in order):
{article}
"""


def build_lookup_prompt(word: str, article: str) -> str:
    return f"""You are a Chinese English teacher. A student double-clicked the word "{word}" in the following English article.

Determine the SINGLE most accurate part of speech for "{word}" as it is used in this article, then provide its Simplified Chinese meaning.

Rules:
- Choose ONLY ONE part of speech: vt. OR vi. OR n. OR adj. OR adv. OR prep. OR conj.
- Do NOT combine multiple parts of speech (e.g. never write "vt. n.")
- A noun is always n., even if it looks like a verb form
- Use Simplified Chinese only (NOT Traditional Chinese)
- Chinese meaning: 1-5 characters, concise
- Output ONLY the result, nothing else. No labels, no explanations, no "词性:" or "释义:" prefixes.
- Exact format: abbreviation + period + space + Chinese meaning

Examples of correct output:
vt. 注意到
n. 涡轮机
adj. 遥远的

Examples of WRONG output (never do this):
词性: n. 释义: 质量
词性: vt. 简体中文释义: 注意到

Article:
{article}
"""


def _extract_translation_dict(result: str) -> Optional[dict]:
    """从LLM返回文本里解析出翻译JSON对象，不做条数/key校验，纯粹负责"把JSON解析出来"。"""
    cleaned = re.sub(r"```json\s*|\s*```", "", result).strip()

    # 方法1：直接 JSON 解析
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 方法2：找到第一个 { 到最后一个 } 之间的内容（防止前后有多余文字）
    try:
        start = cleaned.index('{')
        end = cleaned.rindex('}') + 1
        parsed = json.loads(cleaned[start:end])
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return None


def _parse_translation_response(result: str, expected_count: int) -> Optional[List[str]]:
    """解析LLM返回的翻译JSON对象（{"1": "...", "2": "...", ...}），
    只有 "1"到str(expected_count) 这些key全部存在且非空，才算解析成功，
    返回按顺序排好的翻译列表。返回None表示缺key/解析失败，调用方应据此重试或走兜底。
    """
    parsed = _extract_translation_dict(result)
    if parsed is None:
        return None

    translations = []
    for i in range(1, expected_count + 1):
        value = parsed.get(str(i))
        if value is None or not str(value).strip():
            return None
        translations.append(str(value))
    return translations


def _missing_translation_keys(result: str, expected_count: int) -> List[str]:
    """找出返回的翻译对象里缺失或为空的段落编号，供重试时精确提示模型。"""
    parsed = _extract_translation_dict(result) or {}
    missing = []
    for i in range(1, expected_count + 1):
        value = parsed.get(str(i))
        if value is None or not str(value).strip():
            missing.append(str(i))
    return missing


def _translate_paragraph_batch(en_paragraphs: List[str]) -> List[str]:
    """翻译一小批段落（数量已经保证足够小，不会撞到输出token上限）。

    用带编号的JSON对象接收翻译结果，只有"1"到str(N)这些key全部存在且非空才算成功；
    缺哪个key就精确告诉模型缺哪个，重试命中率比之前"数量不对，你自己再数一遍"这种
    模糊反馈高得多。重试耗尽后的兜底也是dict-aware的——保留所有已经翻译对的key
    （不管它们在返回结果里的顺序如何，只按编号取值，不会因为部分缺失就整体错位），
    只把真正缺失的编号留空，不会像"拿到几条就按顺序垫几条"那样把内容全部推移错位。
    """
    expected_count = len(en_paragraphs)
    article_for_prompt = "\n\n".join(en_paragraphs)

    max_retries = 3
    result = ""
    for attempt in range(max_retries):
        prompt = build_translation_prompt(article_for_prompt, expected_count)
        if attempt > 0:
            missing = _missing_translation_keys(result, expected_count)
            missing_str = ", ".join(missing) if missing else "（未能解析出合法JSON对象）"
            prompt += (
                f"\n\nIMPORTANT - your previous attempt was missing (or left empty) these paragraph "
                f"numbers: {missing_str}. Make sure this time your output JSON object includes ALL "
                f"{expected_count} keys (1 to {expected_count}), with none skipped, merged, or empty."
            )

        result = call_llm(prompt, max_tokens=4096).strip()

        translations = _parse_translation_response(result, expected_count)
        if translations is not None:
            return translations

    # 重试耗尽仍缺key，走安全兜底：保留所有已经对上号的翻译，只把真正缺失的编号留空
    # （不会像旧的"拉平成数组再按顺序垫"那样，让正确的翻译也被挤到错误的位置上）
    parsed = _extract_translation_dict(result) or {}
    translations = []
    for i in range(1, expected_count + 1):
        value = parsed.get(str(i))
        translations.append(str(value) if value is not None and str(value).strip() else "")
    if any(t for t in translations):
        return translations

    # 连一个key都没解析出来（比如返回的根本不是JSON），走最原始的兜底：按空行/换行切
    cleaned = re.sub(r"```json\s*|\s*```", "", result).strip()
    try:
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', cleaned)
        items = [s.replace('\\"', '"').replace('\\n', '\n') for s in items if len(s) > 5]
        if len(items) >= expected_count:
            return items[:expected_count]
        elif len(items) > 0:
            while len(items) < expected_count:
                items.append("")
            return items[:expected_count]
    except Exception:
        pass

    # fallback：按空行分段（中文翻译段落通常也用空行分隔）
    chunks = [c.strip() for c in re.split(r'\n{2,}', cleaned) if c.strip()]
    if len(chunks) >= expected_count:
        return chunks[:expected_count]

    # 按单换行分割
    lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
    if len(lines) >= expected_count:
        return lines[:expected_count]

    # 最终fallback：有多少用多少，不足则补空字符串
    while len(lines) < expected_count:
        lines.append("")
    return lines[:expected_count]


def generate_translation_sync(article: str, paragraphs: Optional[List[str]] = None) -> List[str]:
    """同步生成按段落翻译（在 executor 中运行）

    paragraphs: 调用方已经按自己的规则分好的段落列表（可选）。
    - 阅读课不传，沿用原有按空行(\\n\\n)分段的行为，不受影响。
    - 听力课传入按单换行分好的段落，避免与阅读课的双换行规则冲突。

    长文章（尤其听力对话，常有20-30轮问答）如果一次性整篇发给LLM翻译，输出JSON容易
    超出单次请求的max_tokens被截断——越靠后的段落越容易丢失或对不齐，且体积大的请求
    也更容易撞上免费额度的限流。这里改为按小批次（TRANSLATION_BATCH_SIZE段/批）分别
    翻译并拼接结果，每批独立校验条数、重试、兜底，互不影响。
    """
    if paragraphs is not None:
        en_paragraphs = [p.strip() for p in paragraphs if p.strip()]
    else:
        en_paragraphs = [p.strip() for p in re.split(r'\n{2,}', article) if p.strip()]

    if not en_paragraphs:
        return []

    all_translations: List[str] = []
    for i in range(0, len(en_paragraphs), TRANSLATION_BATCH_SIZE):
        batch = en_paragraphs[i:i + TRANSLATION_BATCH_SIZE]
        all_translations.extend(_translate_paragraph_batch(batch))
        # 批次之间稍作停顿，避免连续请求密度过高触发免费额度限流
        if i + TRANSLATION_BATCH_SIZE < len(en_paragraphs):
            time.sleep(TRANSLATION_BATCH_DELAY_SECONDS)

    return all_translations
