# ===== 第367课：测试进阶-为什么要Mock =====
# 知识点：
#   - 单元测试要“隔离”：网络/数据库/时间 —— 慢、不稳定、有副作用
#   - Mock = 假对象替身：只测当前单元的逻辑，依赖先假装
#   - 判断标准：被测单元要为“依赖的行为”负责吗？不负责 → mock 掉
#   - 依赖注入：把依赖做成参数 —— 不用 mock 库也能替身（本课写法）
def is_valid_user(user_id, fetch_user):
    """fetch_user 是注入进来的“取数函数”：生产环境接真库，测试接假库。"""
    user = fetch_user(user_id)
    return user is not None and user.get("active", False)


# ---- 测试：用字典当假数据库（快、稳定、无副作用）----
fake_db = {
    1: {"active": True},
    2: {"active": False},
}
assert is_valid_user(1, lambda uid: fake_db.get(uid))       # 存在且激活
assert not is_valid_user(2, lambda uid: fake_db.get(uid))   # 存在但未激活
assert not is_valid_user(3, lambda uid: fake_db.get(uid))   # 不存在
print("依赖注入版：3 个用例全部通过，没碰任何真实数据库")

# ---- 三条“什么时候 mock”的判断 ----
# 1. 慢（网络/磁盘） → mock
# 2. 不确定（第三方接口今天挂了） → mock
# 3. 有副作用（发邮件、扣款） → mock
# 反例：纯计算函数（grade(score)）mock 依赖毫无意义 —— 测它自己就行

# ===== 练习题 =====
# 1. 给 is_valid_user 增加“管理员跳过激活检查”规则，用假库验证。
# 2. 思考：本课的 lambda 替身与下一课 unittest.mock 的区别是什么？
# 3. 列出你写过的函数，标出哪些依赖该 mock、哪些不该。
