"""腾讯云语音识别（ASR）客户端封装 - 用于听力课时间戳对齐

密钥从环境变量读取，配置在 backend/.env.local（不进git，需在本地和服务器上各自创建）：
    TENCENT_SECRET_ID=xxx
    TENCENT_SECRET_KEY=xxx

腾讯云暂不支持"强制对齐"（给定准确文本只对齐时间戳），只能走真实的语音识别流程，
拿到识别结果的词级时间戳后，交给 paragraph_alignment.py 做文本相似度匹配。

用的是"录音文件识别"异步接口（CreateRecTask + DescribeTaskStatus），不是"一句话识别"
（SentenceRecognition，官方限制约60秒音频）——因为听力课的音频通常是几分钟的整篇材料。

ResTextFormat=1 时返回 ResultDetail，每个识别片段(可能包含多句话)下有 Words 数组，
每个词有自己的 OffsetStartMs/OffsetEndMs（相对片段起点的偏移），需要加上片段的 StartMs
换算成整段音频的绝对时间戳，这样才能拿到真正的词级精度（而不是整个片段共用一个时间戳）。
"""
import os
import time
import base64
import json
from typing import List, Dict
from fastapi import HTTPException

TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
TENCENT_ASR_REGION = os.getenv("TENCENT_ASR_REGION", "ap-guangzhou")

# 轮询设置：最多等待5分钟（150次 x 2秒），超过视为异常
POLL_INTERVAL_SECONDS = 2
MAX_POLL_ATTEMPTS = 150


def _ensure_credentials():
    if not TENCENT_SECRET_ID or not TENCENT_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="请先配置腾讯云密钥（TENCENT_SECRET_ID / TENCENT_SECRET_KEY），在 backend/.env.local 中设置"
        )


def _parse_result_detail(result_detail: List[Dict]) -> List[Dict]:
    """把 ResultDetail（按片段分组、每个片段内是词级偏移量）展开成词级绝对时间戳列表。
    返回 [{"text": str, "start_ms": int, "end_ms": int}, ...]，每一项是一个词。
    """
    words = []
    for segment in result_detail or []:
        segment_start_ms = int(segment.get("StartMs", 0))
        for w in segment.get("Words", []):
            word_text = w.get("Word", "")
            if not word_text:
                continue
            words.append({
                "text": word_text,
                "start_ms": segment_start_ms + int(w.get("OffsetStartMs", 0)),
                "end_ms": segment_start_ms + int(w.get("OffsetEndMs", 0)),
            })
    return words


def call_tencent_asr(audio_path: str) -> List[Dict]:
    """调用腾讯云录音文件识别（异步任务），返回词级时间戳列表。

    返回格式: [{"text": str, "start_ms": int, "end_ms": int}, ...]（每项是一个词）
    """
    _ensure_credentials()

    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.asr.v20190614 import asr_client, models
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="腾讯云SDK未安装，请运行: pip install tencentcloud-sdk-python-asr"
        )

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    try:
        cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
        http_profile = HttpProfile()
        http_profile.endpoint = "asr.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        client = asr_client.AsrClient(cred, TENCENT_ASR_REGION, client_profile)

        # 1. 提交录音文件识别任务（ResTextFormat=1 才会返回带词级时间戳的 ResultDetail）
        req = models.CreateRecTaskRequest()
        req.EngineModelType = "16k_en"
        req.ChannelNum = 1
        req.ResTextFormat = 1
        req.SourceType = 1
        req.Data = audio_b64
        req.DataLen = len(audio_bytes)

        resp = client.CreateRecTask(req)
        data = json.loads(resp.to_json_string())
        task_id = data["Data"]["TaskId"]

        # 2. 轮询任务状态（异步接口，长音频需要一定处理时间）
        for _ in range(MAX_POLL_ATTEMPTS):
            time.sleep(POLL_INTERVAL_SECONDS)

            query_req = models.DescribeTaskStatusRequest()
            query_req.TaskId = task_id
            query_resp = client.DescribeTaskStatus(query_req)
            query_data = json.loads(query_resp.to_json_string())

            status = query_data.get("Data", {}).get("Status")
            if status == 2:  # 成功
                result_detail = query_data["Data"].get("ResultDetail") or []
                return _parse_result_detail(result_detail)
            elif status == 3:  # 失败
                error_msg = query_data["Data"].get("ErrorMsg", "未知错误")
                raise HTTPException(status_code=502, detail=f"腾讯云语音识别任务失败: {error_msg}")
            # status 0/1 是等待中/处理中，继续轮询

        raise HTTPException(status_code=504, detail="腾讯云语音识别超时（超过5分钟未完成），请重试")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用腾讯云语音识别失败: {str(e)}")
