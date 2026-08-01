"""LLM 调用公共逻辑 - 供阅读课、听力课等功能共用

原用 GitHub Models（models.github.ai），该服务已进入官方"retirement brownout"下线阶段
（错误码 github_models_retirement_brownout），改用智谱AI GLM（open.bigmodel.cn）：
永久免费、国内直连稳定、同时支持文本(GLM-4.7-Flash)和视觉(GLM-4.6V-Flash)。

注意：免费额度并发限制较低，容易触发429限流，call_llm/call_vision_llm内置了
简单的429自动重试（指数退避），调用方不需要自己处理限流重试。
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
# ZHIPU_API_KEY 从环境变量读取，配置在 backend/.env.local（不进git，需在本地和服务器上各自创建）
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4.7-flash")
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4.6v-flash")
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 429限流重试设置：免费额度并发数很低，简单退避重试几次即可缓解
RATE_LIMIT_MAX_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 3


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


def call_llm(prompt: str, max_tokens: int = 1024, model: Optional[str] = None) -> str:
    """调用智谱GLM文本模型（同步，供 executor 使用）"""
    if not ZHIPU_API_KEY:
        raise HTTPException(status_code=500, detail="ZHIPU_API_KEY 未配置，请在 backend/.env.local 中设置")

    payload = {
        "model": model or ZHIPU_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": False,
        # GLM-4.7系列是推理模型，默认会把大量token耗在思考过程(reasoning_content)上，
        # 关掉思考模式：既省token，也保证max_tokens都用在真正需要的输出内容上
        "thinking": {"type": "disabled"},
    }
    return _call_zhipu_api(payload, timeout=60, error_prefix="LLM API 错误")


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


def build_translation_prompt(article: str) -> str:
    """article 内部段落必须用空行(\\n\\n)分隔，供 LLM 识别段落边界"""
    return f"""You are a professional translator. Translate the following English passage into Simplified Chinese (简体中文).

Rules:
1. Translate paragraph by paragraph — each English paragraph must have a complete, accurate Chinese translation of the SAME content.
2. Do NOT summarize, shorten, or skip any sentences. Every sentence must be translated in full.
3. Use Simplified Chinese characters only (NOT Traditional Chinese).
4. CRITICAL: Every single English word must be translated into Chinese. Do NOT leave any English words, phrases, or terms in the output. Not even technical terms, proper nouns, or difficult words — find a Chinese equivalent for everything.
5. Output ONLY a JSON array of strings, one string per paragraph, in the same order.
6. No extra explanation, no markdown formatting, just the raw JSON array.

Example output format: ["第一段完整翻译", "第二段完整翻译"]

English passage:
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


def generate_translation_sync(article: str, paragraphs: Optional[List[str]] = None) -> List[str]:
    """同步生成按段落翻译（在 executor 中运行）

    paragraphs: 调用方已经按自己的规则分好的段落列表（可选）。
    - 阅读课不传，沿用原有按空行(\\n\\n)分段的行为，不受影响。
    - 听力课传入按单换行分好的段落，避免与阅读课的双换行规则冲突。
    传入时会用这份段落列表重新拼出以空行分隔的文本喂给 LLM（保证 LLM 稳定识别段落边界），
    而不依赖原始文本本身的换行风格。
    """
    if paragraphs is not None:
        en_paragraphs = [p.strip() for p in paragraphs if p.strip()]
        article_for_prompt = "\n\n".join(en_paragraphs)
    else:
        en_paragraphs = [p.strip() for p in re.split(r'\n{2,}', article) if p.strip()]
        article_for_prompt = article

    expected_count = len(en_paragraphs)

    prompt = build_translation_prompt(article_for_prompt)
    # 翻译用最大输出 token，防止长文章被截断（API 上限 4096）
    result = call_llm(prompt, max_tokens=4096).strip()

    # 尝试多种方式解析 JSON 数组
    cleaned = re.sub(r"```json\s*|\s*```", "", result).strip()

    # 方法1：直接 JSON 解析
    try:
        translations = json.loads(cleaned)
        if isinstance(translations, list) and len(translations) > 0:
            return [str(t) for t in translations]
    except Exception:
        pass

    # 方法2：找到第一个 [ 到最后一个 ] 之间的内容
    try:
        start = cleaned.index('[')
        end = cleaned.rindex(']') + 1
        translations = json.loads(cleaned[start:end])
        if isinstance(translations, list) and len(translations) > 0:
            return [str(t) for t in translations]
    except Exception:
        pass

    # 方法3：用正则提取 JSON 字符串数组中的各项（处理截断情况）
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
