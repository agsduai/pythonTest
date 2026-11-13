# ===== 第159课：Web应用-课程介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Web 应用是运行在浏览器中、通过 HTTP 与服务器交互的程序
#   - B/S 架构：浏览器（Browser）负责展示，服务器（Server）负责业务
#   - 一次请求的流程：浏览器发请求 -> 服务器处理 -> 返回响应
#   - 本阶段学习路线：面向对象高级 -> FastAPI -> AI 汉字谜盒项目
#   - Web 应用通常分为前端页面、后端接口、数据库三层


class Request:
    """模拟浏览器发出的 HTTP 请求。"""

    def __init__(self, method: str, path: str) -> None:
        self.method = method
        self.path = path

    def __str__(self) -> str:
        return f"{self.method} {self.path}"


class Response:
    """模拟服务器返回的 HTTP 响应。"""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body

    def __str__(self) -> str:
        return f"{self.status_code} {self.body}"


class Server:
    """模拟 Web 服务器，根据路径返回不同内容。"""

    def handle(self, request: Request) -> Response:
        if request.path == "/":
            return Response(200, "欢迎来到首页")
        if request.path == "/books":
            return Response(200, "图书列表")
        return Response(404, "页面不存在")


browser_request = Request("GET", "/books")   # 浏览器发起请求
server = Server()                            # 创建服务器对象
result = server.handle(browser_request)      # 服务器处理并返回响应
print("请求：", browser_request)
print("响应：", result)

print("\n本课程学习路线：")
roadmap = ["面向对象高级", "FastAPI 基础", "AI 汉字谜盒项目"]
for index, stage in enumerate(roadmap, start=1):
    print(f"  {index}. {stage}")

# ===== 练习题 =====
# 1. 用自己的话说明浏览器、服务器、数据库三者的分工。
# 2. 给 Server 增加 /members 路径，返回“会员列表”。
# 3. 写一个函数 print_response，格式化输出响应的状态码和正文。
