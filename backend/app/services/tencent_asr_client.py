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

# 腾讯云ASR "Data"字段（内联提交音频）硬性上限是 5,242,880 字节(5MB)，超过会直接报错
# InvalidParameter: Data length should in range [0, 5242880]。留一点余量，
# 到这个阈值就改用"URL提交"模式（SourceType=0），这种模式没有这个大小限制。
INLINE_DATA_SIZE_LIMIT = 5_000_000


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


def call_tencent_asr(audio_path: str, audio_url: str = None) -> List[Dict]:
    """调用腾讯云录音文件识别（异步任务），返回词级时间戳列表。

    audio_path: 本地音频文件路径，用于读取文件大小、以及文件较小时直接内联提交。
    audio_url: 音频的公网可访问地址（可选）。当文件超过腾讯云"内联提交"的5MB上限时，
        必须提供这个参数，改走"URL提交"模式，否则会抛出明确的报错而不是让腾讯云返回
        一个难以理解的 InvalidParameter 错误。

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

    file_size = os.path.getsize(audio_path)
    use_url_mode = file_size >= INLINE_DATA_SIZE_LIMIT

    if use_url_mode and not audio_url:
        raise HTTPException(
            status_code=400,
            detail=(
                f"音频文件较大（{file_size / 1024 / 1024:.1f}MB），超过腾讯云语音识别5MB的直接上传上限，"
                "需要配置 PUBLIC_BASE_URL（服务器的公网访问地址）才能识别，请联系管理员在 .env.local 中设置"
            ),
        )

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

        if use_url_mode:
            # URL提交模式：没有5MB限制，但要求腾讯云服务器能从公网抓取这个地址
            req.SourceType = 0
            req.Url = audio_url
        else:
            # 内联提交模式：文件较小，直接把字节数据塞进请求体，省去腾讯云再来抓取一次的等待时间
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            req.SourceType = 1
            req.Data = base64.b64encode(audio_bytes).decode("utf-8")
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
