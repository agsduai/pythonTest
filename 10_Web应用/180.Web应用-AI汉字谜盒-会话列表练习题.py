# ===== 第180课：Web应用-AI汉字谜盒-会话列表 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 遍历会话目录，用 glob("*.json") 找到所有会话文件
#   - 列表接口只返回摘要，不返回完整消息，减少数据量
#   - 按 updated_at 倒序排列，最近的会话显示在最前
#   - 跳过损坏的 JSON 文件，保证接口整体可用
# 依赖：pip install fastapi uvicorn

import json
from pathlib import Path

from fastapi import FastAPI
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI汉字谜盒")


@app.get("/sessions")
def list_sessions():
    """返回会话摘要列表，供前端侧边栏展示。"""
    items = []
    for path in SESSION_DIR.glob("*.json"):
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # 单个文件损坏不影响其他会话
        items.append({
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": len(session["messages"]),
        })
    # 最近更新的会话排在前面
    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return {"total": len(items), "items": items}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 为列表接口增加 keyword 查询参数，按标题模糊过滤会话。
# 2. 在返回结果中增加 last_message 字段，显示最后一条消息的前 20 个字。
# 3. 思考：为什么列表接口不直接返回每个会话的完整 messages？
