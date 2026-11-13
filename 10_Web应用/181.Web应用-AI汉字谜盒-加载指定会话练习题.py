# ===== 第181课：Web应用-AI汉字谜盒-加载指定会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 用路径参数接收会话 id
#   - 根据 id 拼出文件路径并读取 JSON
#   - 会话不存在时返回 404，而不是让程序崩溃
#   - 加载接口返回完整消息，供前端恢复聊天记录
# 依赖：pip install fastapi uvicorn

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI汉字谜盒")


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """读取并返回指定会话的完整内容。"""
    # 只允许使用生成的十六进制 id，避免路径穿越
    if not session_id.isalnum():
        raise HTTPException(status_code=400, detail="会话 id 格式不正确")
    file_path = SESSION_DIR / f"{session_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="会话不存在")
    try:
        session = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="会话文件已损坏")
    return {"message": "加载成功", "data": session}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 用浏览器访问 /sessions/不存在的id，观察 404 响应体。
# 2. 给接口增加参数 limit，只返回最近 limit 条消息。
# 3. 思考：为什么返回完整 messages 前要确认会话文件存在？
