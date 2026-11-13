# ===== 第179课：Web应用-AI汉字谜盒-与AI交互(实现) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - FastAPI 接口中调用大模型，完成一轮问答
#   - 把用户消息与 AI 回复追加到会话历史
#   - 每次对话后更新 updated_at 并写回 JSON 文件
#   - 大模型调用较慢，接口设计要考虑超时与失败情况
# 依赖：pip install fastapi uvicorn openai

import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "你是“AI汉字谜盒”的猜字谜助手。先出谜面，不要直接公布谜底；"
    "用户回答后再判断对错，并解释原因。"
)
# 占位密钥：真实密钥应从环境变量读取，严禁提交到代码仓库
client = OpenAI(api_key="sk-请替换为你的密钥", base_url="https://api.deepseek.com")

app = FastAPI(title="AI汉字谜盒")


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def ask_ai(history: list[dict[str, str]]) -> str:
    """携带最近 20 条历史消息调用 DeepSeek，返回助手文本。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


@app.post("/sessions/{session_id}/messages")
def send_message(session_id: str, payload: MessageCreate):
    """发送一条消息，保存 AI 回复并返回结果。"""
    path = SESSION_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="会话不存在")
    session = json.loads(path.read_text(encoding="utf-8"))
    session["messages"].append({"role": "user", "content": payload.content})
    reply = ask_ai(session["messages"])
    session["messages"].append({"role": "assistant", "content": reply})
    session["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"reply": reply, "updated_at": session["updated_at"]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 先创建一个会话，再向 /sessions/{id}/messages 发送“开始出题”，观察回复。
# 2. 让接口额外返回 message_count，表示会话当前消息总数。
# 3. 给 ask_ai 增加异常捕获，调用失败时返回友好的错误提示。
