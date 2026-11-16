# ===== 第404课：Web API 与接口测试-REST设计原则 =====
# 知识点：
#   - REST：用“资源 + HTTP 方法 + 状态码”表达操作，而不是把所有动作塞进 URL
#   - URL 用名词复数：/tasks、/tasks/1；动作交给方法：GET/POST/PUT/PATCH/DELETE
#   - 幂等性：GET/PUT/DELETE 重复调用结果一致；POST 通常不幂等
#   - 状态码：200 成功 / 201 已创建 / 204 无内容 / 400 参数错 / 404 不存在 /
#     409 冲突 / 422 校验失败 / 500 服务端错误
#   - 统一响应结构：{code, message, data}，前端好处理，日志好排查
#   - 本章用标准库 http.server 实现，不依赖 FastAPI/Flask

# ---- 设计对照：好接口 vs 坏接口 ----
BAD_GOOD = [
    ("GET  /getAllTasks",              "GET    /tasks"),
    ("POST /createTask",               "POST   /tasks"),
    ("POST /deleteTask?id=1",          "DELETE /tasks/1"),
    ("GET  /getTaskById?id=1",         "GET    /tasks/1"),
    ("POST /updateTaskStatus",         "PATCH  /tasks/1/status"),
]
print("== URL 设计对照 ==")
print(f"  {'不推荐':<32}{'推荐'}")
for bad, good in BAD_GOOD:
    print(f"  {bad:<32}{good}")

# ---- 方法与幂等性 ----
METHODS = {
    "GET":    ("查询", True, 200),
    "POST":   ("创建", False, 201),
    "PUT":    ("整体替换", True, 200),
    "PATCH":  ("局部更新", False, 200),
    "DELETE": ("删除", True, 204),
}
print("\n== 方法与幂等性 ==")
for method, (desc, idempotent, ok_status) in METHODS.items():
    print(f"  {method:7s} {desc:6s} 幂等={'是' if idempotent else '否':2s} 成功码={ok_status}")


# ---- 一个纯函数：根据请求判断应该返回什么状态码 ----
def decide_status(method: str, exists: bool, valid: bool, duplicate: bool = False) -> int:
    if not valid:
        return 422                      # 校验失败优先
    if duplicate:
        return 409                      # 冲突
    if method == "POST":
        return 201
    if not exists:
        return 404
    if method == "DELETE":
        return 204
    return 200


cases = [
    ("GET", True, True, False, 200),
    ("GET", False, True, False, 404),
    ("POST", False, True, False, 201),
    ("POST", False, True, True, 409),
    ("POST", False, False, False, 422),
    ("DELETE", True, True, False, 204),
]
print("\n== 状态码决策表 ==")
for method, exists, valid, dup, expected in cases:
    got = decide_status(method, exists, valid, dup)
    mark = "✓" if got == expected else "✗"
    print(f"  {mark} {method:6s} exists={exists!s:5s} valid={valid!s:5s} "
          f"dup={dup!s:5s} → {got}")

# 统一响应结构示例（后续课程都会用）
def envelope(data=None, message="ok", code=0):
    return {"code": code, "message": message, "data": data}


print("\n成功响应：", envelope({"id": 1, "title": "写周报"}))
print("失败响应：", envelope(None, "标题不能为空", code=422))

# ===== 练习题 =====
# 1. 为“学生 / 课程 / 选课”设计 REST URL 与对应方法。
# 2. 判断 PATCH 为什么不幂等，举一个具体的反例。
# 3. 给 decide_status 增加 403（无权限）场景。
# 4. 思考：什么时候宁可用 RPC 风格（/createTask）而不是 REST？
