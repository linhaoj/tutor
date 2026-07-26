"""GitHub Models LLM 调用公共逻辑 - 供阅读课、听力课等功能共用"""
import os
import re
import json
import base64
import urllib.request
import urllib.error
from typing import List, Optional
from fastapi import HTTPException

# ── LLM 配置 ─────────────────────────────────────────────────
# GITHUB_TOKEN 从环境变量读取，配置在 backend/.env.local（不进git，需在本地和服务器上各自创建）
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = "meta/llama-3.3-70b-instruct"
GITHUB_VISION_MODEL = os.getenv("GITHUB_VISION_MODEL", "meta/llama-4-scout-17b-16e-instruct")
GITHUB_API_URL = "https://models.github.ai/inference/chat/completions"


def count_words(text: str) -> int:
    return len(re.findall(r"\b[a-zA-Z']+\b", text))


def call_llm(prompt: str, max_tokens: int = 1024, model: Optional[str] = None) -> str:
    """调用 GitHub Models（同步，供 executor 使用）"""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN 未配置，请在 backend/.env.local 中设置")

    payload = json.dumps({
        "model": model or GITHUB_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        GITHUB_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise HTTPException(status_code=502, detail=f"LLM API 错误: {e.code} {body}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用 LLM 失败: {str(e)}")


def call_vision_llm(prompt: str, image_bytes: bytes, mimetype: str, max_tokens: int = 2048) -> str:
    """调用支持视觉的 GitHub Models（同步，用于 OCR 图片识别）"""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN 未配置，请在 backend/.env.local 中设置")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = json.dumps({
        "model": GITHUB_VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mimetype};base64,{image_b64}"}}
            ]
        }],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        GITHUB_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise HTTPException(status_code=502, detail=f"视觉模型 API 错误: {e.code} {body}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用视觉模型失败: {str(e)}")


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
