# ===== 第174课：Web应用-FastAPI基础-入门程序 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - FastAPI 的安装与最小应用
#   - 使用 @app.get / @app.post 定义接口
#   - 路径参数与查询参数
#   - 使用 BaseModel 接收 JSON 请求体
#   - 使用 uvicorn 启动服务并访问 /docs 自动文档
# 依赖：pip install fastapi uvicorn

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="FastAPI 入门程序")


class Riddle(BaseModel):
    """谜语请求体：question 与 answer 均为必填字符串。"""

    question: str
    answer: str


@app.get("/")
def read_root():
    # 返回字典时，FastAPI 会自动序列化为 JSON
    return {"message": "欢迎来到 FastAPI"}


@app.get("/hello/{name}")
def say_hello(name: str, city: str = "北京"):
    # name 是路径参数；city 是带默认值的查询参数
    return {"message": f"你好，{name}！来自{city}"}


@app.post("/riddles")
def create_riddle(riddle: Riddle):
    # 请求体 JSON 会自动校验并转换为 Riddle 对象
    return {"message": "谜语已收到", "data": riddle.model_dump()}


if __name__ == "__main__":
    # 启动后访问 http://127.0.0.1:8000/docs 查看自动接口文档
    uvicorn.run(app, host="127.0.0.1", port=8000)

# ===== 练习题 =====
# 1. 新增 GET 接口 /square/{number}，返回该数字的平方。
# 2. 修改 /hello/{name}，增加查询参数 times，返回重复的问候语。
# 3. 新增 POST 接口 /guess，接收用户答案并返回是否正确。
