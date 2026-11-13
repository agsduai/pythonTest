# ===== 第175课：Web应用-AI汉字谜盒-开发规范 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 项目分层：接口层、服务层、数据层、配置层职责单一
#   - 命名规范：模块与函数用 snake_case，类用 PascalCase，常量用 UPPER_CASE
#   - 类型注解、文档字符串、统一响应结构
#   - 密钥只从环境变量读取，禁止提交到代码仓库
# 依赖：pip install fastapi uvicorn

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
SESSION_DIR = BASE_DIR / "data" / "sessions"


class SessionCreate(BaseModel):
    """新建会话时提交的数据，title 长度限制为 1～50。"""

    title: str = Field(default="新的谜盒", min_length=1, max_length=50)


class ApiResponse(BaseModel):
    """所有接口统一的响应格式。"""

    code: int = 0
    message: str = "ok"
    data: Any = None


app = FastAPI(title="AI汉字谜盒")


@app.get("/health")
def health_check():
    """健康检查接口：部署后先用它确认服务是否正常。"""
    return ApiResponse(data={"status": "healthy"}).model_dump()


@app.post("/sessions")
def create_session(payload: SessionCreate):
    """接口层只负责接收参数与返回响应，业务逻辑应放到服务层。"""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return ApiResponse(data={"title": payload.title}).model_dump()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 按本章规范写出 AI 汉字谜盒的目录结构（接口、服务、数据、配置）。
# 2. 把 title 为空时的错误信息改成更友好的中文提示。
# 3. 为项目增加统一的 ApiResponse，并说明它带来的好处。
