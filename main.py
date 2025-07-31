import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

from config import settings

app = FastAPI()

# 设置超时时间（秒）
TIMEOUT = 10.0

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy-service")


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
)
async def proxy_request(request: Request, path: str):
    """处理所有请求的路由"""
    # 1. 准备请求数据
    client = httpx.AsyncClient()
    headers = dict(request.headers)
    headers.pop("host", None)  # 移除原始host头

    query_params = str(request.url.query)
    target_url = (
        f"{settings.MAIN_SYSTEM_URL}/{path}{'?' + query_params if query_params else ''}"
    )
    backup_url = f"{settings.BACKUP_SYSTEM_URL}/{path}{'?' + query_params if query_params else ''}"

    # 2. 尝试主系统
    try:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
            timeout=settings.TIMEOUT,
        )
        logger.info(f"Forwarded to MAIN system: {target_url}")
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.error(f"Main system failed: {e}")
        data = {"mobile": settings.ADMIN_MOBILE, "code": "ADE主机服务异常，紧急处理。"}
        send_res = await client.post(f"{settings.SMS_HOST}/content/sms", data=data)
        logger.info(f"Forwarded to MAIN system send_res: {send_res}， send_res text: {send_res.text}")

    # 3. 主系统失败时尝试备用系统
    try:
        response = await client.request(
            method=request.method,
            url=backup_url,
            headers=headers,
            content=await request.body(),
            timeout=TIMEOUT,
        )
        logger.warning(f"Using BACKUP system: {backup_url}")
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.critical(f"Both systems failed: {e}")
        data = {"mobile": settings.ADMIN_MOBILE, "code": "ADE备机服务异常，紧急处理。"}
        send_res = await client.post(f"{settings.SMS_HOST}/content/sms", data=data)
        logger.info(f"Forwarded to MAIN system send_res: {send_res}， send_res text: {send_res.text}")
        return Response(
            content="Service unavailable: All backend systems are down", status_code=503
        )
    finally:
        await client.aclose()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
