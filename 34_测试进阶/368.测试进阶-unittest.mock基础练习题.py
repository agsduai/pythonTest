# ===== 第368课：测试进阶-unittest.mock基础 =====
# 知识点：
#   - Mock()：替身对象 —— 怎么调都行，行为由你设定
#   - return_value：规定“调用后返回什么”
#   - 断言调用方式：assert_called_once_with / call_args / call_count
#   - side_effect：依次返回多个值，或抛异常
#   - 经典坑：mock.name 不是“调用后的名字”，而是 mock 自身的 name 属性！
from unittest.mock import Mock

# ---- return_value：规定返回 ----
fetch = Mock(return_value={"active": True})
print("随便怎么调：", fetch(1), fetch("任意", 参数="都行"))
print("不是函数调用：", fetch.name)          # ← 坑：这是 Mock 的 name 属性

# ---- 断言“怎么被调用”（换一个干净的 Mock，避免上面的演示调用混入）----
check = Mock(return_value=None)
check(1, 2, key="v")
check.assert_called_once()
check.assert_called_with(1, 2, key="v")      # 参数不符会抛 AssertionError
print("调用次数：", check.call_count, "| 最近一次参数：", check.call_args)

# ---- side_effect：依次返回 / 抛异常 ----
seq = Mock(side_effect=[1, 2, 3])
print("依次返回：", seq(), seq(), seq())

err = Mock(side_effect=ConnectionError("网络断了"))
try:
    err()
except ConnectionError as exc:
    print("side_effect 抛异常：", exc)

# ---- 用 Mock 替换依赖，测试业务逻辑（对照第367课）----
def is_valid_user(user_id, fetch_user):
    user = fetch_user(user_id)
    return user is not None and user.get("active", False)


good = Mock(return_value={"active": True})
bad = Mock(return_value=None)
assert is_valid_user(1, good)
assert not is_valid_user(1, bad)
print("用 Mock 当 fetch_user：业务断言通过")

# ===== 练习题 =====
# 1. 断言一个 Mock 恰好被调用 3 次且第二次参数是 ("b",)。
# 2. 用 side_effect 模拟“前两次失败第三次成功”的重试场景。
# 3. 思考：assert_called_with 失败时输出里有什么？（故意写错试一次）
