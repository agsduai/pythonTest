# ===== 第370课：测试进阶-MagicMock进阶 =====
# 知识点：
#   - MagicMock：连魔法方法（iter/len/with）都替你支持
#   - 配置复杂行为：__iter__ 迭代、with 上下文、链式调用
#   - side_effect=函数：按入参动态决定返回
#   - spec=真类：替身只能有真类存在的方法 —— 防拼写错误假通过
from unittest.mock import MagicMock

# ---- 模拟可迭代的数据库游标 ----
cursor = MagicMock()
cursor.__iter__.return_value = iter([("小明", 92), ("小红", 88)])
print("迭代游标：", list(cursor))

# ---- 模拟连接对象：支持 with + 链式调用 ----
conn = MagicMock()
conn.cursor().fetchall.return_value = [(1, "A001"), (2, "A002")]
with conn:                                     # __enter__/__exit__ 自动支持
    rows = conn.cursor().fetchall()
print("查询结果：", rows)
print("链式调用自动创建中间 Mock：", conn.cursor().execute.called or "尚未调用 execute")

# ---- side_effect=函数：按参数动态返回 ----
def fake_get(key):
    data = {"name": "小明", "city": "北京"}
    return data.get(key, "<未配置>")


store = MagicMock(side_effect=fake_get)
print("动态返回：", store("name"), store("city"), store("missing"))

# ---- spec：给替身戴上“紧箍咒” ----
class RealAPI:
    def fetch(self, url): ...


strict = MagicMock(spec=RealAPI)
strict.fetch("https://a.com")                  # 真类有的方法 → 放行
try:
    strict.fetchh("https://a.com")             # 拼写错误 → 立刻暴露
except AttributeError as exc:
    print("spec 拦截拼写错误：", exc)

# ===== 练习题 =====
# 1. 用 MagicMock 模拟“数据库连接池”：acquire() 返回可 with 的连接。
# 2. 给 fetch 的 mock 加 side_effect：第一次抛超时、第二次成功。
# 3. 思考：什么情况下该用 spec？什么时候连 spec 都不要？（提示：协议未定）
