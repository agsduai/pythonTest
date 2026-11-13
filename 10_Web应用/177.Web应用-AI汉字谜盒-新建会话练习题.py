# ===== 第177课：Web应用-AI汉字谜盒-新建会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 会话的数据结构：id、title、created_at、updated_at、messages
#   - 使用 uuid4().hex 生成唯一会话标识
#   - 把会话保存为 data/sessions/<id>.json
#   - 使用 POST 接口创建资源，成功时返回 201
# 依赖：pip install fastapi uvicorn

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI汉字谜盒")


class SessionCreate(BaseModel):
    """新建会话的请求体；不传 title 时使用默认值。"""

    title: str = Field(default="新的谜盒", min_length=1, max_length=50)


def now_text() -> str:
    """返回可读的时间字符串，便于排序和展示。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.post("/sessions", status_code=201)
def create_session(payload: SessionCreate):
    """创建新会话并写入 JSON 文件。"""
    session_id = uuid4().hex  # 32 位十六进制字符串，重复概率极低
    session = {
        "id": session_id,
        "title": payload.title,
        "created_at": now_text(),
        "updated_at": now_text(),
        "messages": [],
    }
    file_path = SESSION_DIR / f"{session_id}.json"
    # ensure_ascii=False 让中文原样保存；encoding 必须显式指定
    file_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"message": "会话创建成功", "data": session}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 调用 POST /sessions 创建一个标题为“猜字谜”的会话，并记录返回的 id。
# 2. 打开 data/sessions 目录，找到新生成的 JSON 文件并解释各字段含义。
# 3. 修改接口，让返回结果同时包含文件路径 file_path。
