"""通义千问语音识别客户端 - 用于听力课时间戳对齐

替换腾讯云ASR（免费额度不稳定），改用阿里云百炼 qwen-audio-3.0-asr-flash-filetrans：
异步文件转写，支持长音频（最长12小时/2GB），返回词级时间戳。

调用流程（异步任务模式，三步走）：
1. 提交任务：POST .../services/audio/asr/transcription，file_urls 传音频的公网URL
   （这个模型只接受URL提交，不支持像腾讯云那样直接传字节数据——因此 PUBLIC_BASE_URL
   和 listening_api.py 里为腾讯云5MB限制搭建的临时音频公开访问接口，现在是必需的，
   不再是"超过5MB才需要"的可选项）
2. 轮询任务状态：GET .../tasks/{task_id}，直到 task_status 变成 SUCCEEDED/FAILED
3. 任务成功后，results[] 里每一项只是个指针（含 transcription_url），真正带词级
   时间戳的转写内容还需要再请求一次这个 URL 才能拿到——这一步文档的RESTful示例没
   直接给出，是对照SDK示例和返回结果示例拼出来的，实现后需要用真实音频验证。
"""
import os
import time
import json
import urllib.request
import urllib.error
from typing import List, Dict
from fastapi import HTTPException

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_ASR_MODEL = os.getenv("QWEN_ASR_MODEL", "qwen-audio-3.0-asr-flash-filetrans")
DASHSCOPE_SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
DASHSCOPE_TASK_URL_TMPL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

# 轮询设置：查询接口官方文档标注默认20QPS，建议轮询间隔2-5秒。
# 最多等待10分钟（200次 x 3秒）——之前给5分钟预算时，实测有真实的听力音频
# 处理时间超过5分钟导致504超时（用户反馈+服务器日志核实过），加长一倍留足余量
POLL_INTERVAL_SECONDS = 3
MAX_POLL_ATTEMPTS = 200


def _ensure_credentials():
    if not DASHSCOPE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="DASHSCOPE_API_KEY 未配置，请在 backend/.env.local 中设置"
        )


def _http_post_json(url: str, payload: dict, headers: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_json(url: str, headers: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_transcription_result(result: dict) -> List[Dict]:
    """把transcription_url指向的转写结果JSON展开成词级绝对时间戳列表。
    返回格式跟腾讯云那边(_parse_result_detail)保持一致，
    这样 paragraph_alignment.py 完全不用改。
    """
    words = []
    for transcript in result.get("transcripts", []):
        for sentence in transcript.get("sentences", []):
            for w in sentence.get("words", []):
                text = (w.get("text") or "").strip()
                if not text:
                    continue
                words.append({
                    "text": text,
                    "start_ms": int(w.get("begin_time", 0)),
                    "end_ms": int(w.get("end_time", 0)),
                })
    return words


def call_qwen_asr(audio_url: str) -> List[Dict]:
    """调用通义千问录音文件转写（异步任务），返回词级时间戳列表。

    audio_url: 音频的公网可访问地址（必填——这个模型只支持URL提交，不支持内联传字节数据）。

    返回格式: [{"text": str, "start_ms": int, "end_ms": int}, ...]（每项是一个词）
    """
    _ensure_credentials()

    submit_headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    # 1. 提交转写任务
    submit_payload = {
        "model": QWEN_ASR_MODEL,
        "input": {"file_urls": [audio_url]},
        "parameters": {"channel_id": [0]},
    }
    try:
        submit_result = _http_post_json(DASHSCOPE_SUBMIT_URL, submit_payload, submit_headers, timeout=30)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise HTTPException(status_code=502, detail=f"语音识别任务提交失败: {e.code} {body}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"语音识别任务提交失败: {str(e)}")

    task_id = submit_result.get("output", {}).get("task_id")
    if not task_id:
        raise HTTPException(status_code=502, detail=f"语音识别任务提交失败: {submit_result}")

    # 2. 轮询任务状态
    task_url = DASHSCOPE_TASK_URL_TMPL.format(task_id=task_id)
    query_headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}

    for _ in range(MAX_POLL_ATTEMPTS):
        time.sleep(POLL_INTERVAL_SECONDS)

        try:
            query_result = _http_get_json(task_url, query_headers, timeout=30)
        except Exception:
            # 轮询过程中偶发网络抖动不算致命，继续重试
            continue

        status = query_result.get("output", {}).get("task_status")
        if status == "SUCCEEDED":
            results = query_result.get("output", {}).get("results", [])
            if not results:
                raise HTTPException(status_code=502, detail="语音识别任务成功但未返回结果")

            first = results[0]
            if first.get("subtask_status") != "SUCCEEDED":
                raise HTTPException(status_code=502, detail=f"语音识别子任务失败: {first}")

            transcription_url = first.get("transcription_url")
            if not transcription_url:
                raise HTTPException(status_code=502, detail=f"语音识别结果缺少transcription_url: {first}")

            # 3. 结果URL通常是OSS直链，不需要（也不应该）带上我们自己的DashScope鉴权头
            try:
                transcription_result = _http_get_json(transcription_url, {}, timeout=30)
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"获取语音识别结果失败: {str(e)}")

            return _parse_transcription_result(transcription_result)

        elif status == "FAILED":
            raise HTTPException(status_code=502, detail=f"语音识别任务失败: {query_result.get('output', {})}")
        # PENDING/RUNNING 继续轮询

    raise HTTPException(status_code=504, detail="语音识别超时（超过5分钟未完成），请重试")
