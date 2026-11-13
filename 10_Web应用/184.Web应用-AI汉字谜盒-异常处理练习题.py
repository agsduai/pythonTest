# ===== 第184课：Web应用-AI汉字谜盒-异常处理 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用 HTTPException 处理可预期的业务错误（如 404、400）
#   - 用 @app.exception_handler 注册全局异常处理器
#   - 自定义 AIServiceError 区分“AI 服务故障”和普通错误
#   - 统一错误响应格式，避免把堆栈信息暴露给用户
# 依赖：pip install fastapi uvicorn

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("hanzi_mihe")

SESSION_DIR = Path(__file__).resolve().parent / "data" / "sessions"

app = FastAPI(title="AI汉字谜盒")

class AIServiceError(Exception):
    """AI 服务调用失败时抛出的自定义异常。"""

@app.exception_handler(AIServiceError)
async def ai_error_handler(request: Request, exc: AIServiceError):
    """AI 故障返回 503，提示用户稍后重试。"""
    logger.exception("AI 服务异常：%s", exc)
    return JSONResponse(status_code=503, content={"code": 503, "message": "AI 服务暂不可用，请稍后重试"})

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """兜底处理未捕获异常，返回统一格式的 500。"""
    logger.exception("未处理异常：%s", exc)
    return JSONResponse(status_code=500, content={"code": 500, "message": "服务器内部错误"})

def call_ai(question: str) -> str:
    """模拟 AI 调用：真实项目在这里使用 OpenAI 客户端请求模型。"""
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise AIServiceError("未配置 DEEPSEEK_API_KEY")
    return f"AI 回答：{question}"


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """会话不存在属于可预期错误，用 HTTPException 返回 404。"""
    path = SESSION_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "加载成功", "session_id": session_id}


@app.get("/ask")
def ask(question: str = ""):
    """参数为空返回 400；AI 故障由全局处理器统一转换。"""
    if not question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    return {"reply": call_ai(question)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 请求一个不存在的会话，观察 404 的响应结构。
# 2. 为参数校验错误 RequestValidationError 增加处理器，返回 422 和中文提示。
# 3. 思考：为什么自定义异常比直接返回字符串错误更利于维护？
