# ===== 第182课：Web应用-AI汉字谜盒-删除会话 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 使用 DELETE 方法删除资源
#   - 删除前先检查文件是否存在，不存在返回 404
#   - 使用 Path.unlink() 删除会话文件
#   - 删除成功返回被删除的会话 id，便于前端同步列表
# 依赖：pip install fastapi uvicorn

from pathlib import Path

from fastapi import FastAPI, HTTPException
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI汉字谜盒")


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """删除指定会话文件。"""
    if not session_id.isalnum():
        raise HTTPException(status_code=400, detail="会话 id 格式不正确")
    file_path = SESSION_DIR / f"{session_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="会话不存在")
    file_path.unlink()  # 只删除文件，不删除目录
    return {"message": "会话已删除", "session_id": session_id}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 创建一个临时会话，再调用 DELETE 接口删除它，确认文件消失。
# 2. 重复删除同一个会话，观察第二次请求返回什么状态码。
# 3. 给删除接口增加确认参数 confirm=true，未确认时拒绝删除。
