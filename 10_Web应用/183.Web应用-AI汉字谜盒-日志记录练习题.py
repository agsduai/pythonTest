# ===== 第183课：Web应用-AI汉字谜盒-日志记录 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 使用 logging 模块记录程序运行信息
#   - 用 RotatingFileHandler 按大小轮转日志文件
#   - 用 FastAPI 中间件统一记录请求方法、路径、状态码和耗时
#   - 日志中禁止输出完整密钥等敏感信息
# 依赖：pip install fastapi uvicorn

import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("hanzi_mihe")
logger.setLevel(logging.INFO)
if not logger.handlers:  # 避免重复导入时添加多个处理器
    handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=1024 * 1024,  # 单个文件最大 1 MB
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)

app = FastAPI(title="AI汉字谜盒")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """每个请求前后各记录一次，便于排查慢接口。"""
    start = time.perf_counter()
    response = await call_next(request)
    cost_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s | %.1f ms",
        request.method,
        request.url.path,
        response.status_code,
        cost_ms,
    )
    return response


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """读取会话时记录关键业务日志。"""
    logger.info("加载会话：session_id=%s", session_id)
    return {"message": "加载成功", "session_id": session_id}


if __name__ == "__main__":
    logger.info("服务启动：http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 访问一次接口后打开 logs/app.log，说出日志中每一列的含义。
# 2. 在调用 AI 的位置记录开始时间与耗时，并写入日志。
# 3. 把日志级别改为 WARNING，观察 INFO 日志是否还会写入文件。
