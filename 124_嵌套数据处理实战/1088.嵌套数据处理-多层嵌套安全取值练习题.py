# ===== 第1088课：嵌套数据处理-多层嵌套安全取值 =====
# 知识点：
#   - 多层取值 data["a"]["b"] 任何一层缺键就 KeyError，越往深越脆弱
#   - 安全取值链：每层都用 .get()，任何一层缺失返回默认值不崩溃
#   - try/except KeyError：适合"正常路径该有，偶发缺失"的情况
#   - 深层默认值用 or 简写：data.get("tags") or []（防 None）

# 案例一：直接多层取值的崩溃风险
profile = {"name": "小张", "contact": {"phone": "13800000000"}}
print(f"手机号：{profile['contact']['phone']}")
# print(profile["contact"]["email"])  # KeyError：contact 里没有 email

# 案例二：get 链安全取值
email = profile.get("contact", {}).get("email", "未填写")
print(f"邮箱（安全取值）：{email}")  # 中间层缺失也只会得到默认值

# 嵌套更深也一样
config = {"db": {"master": {"host": "localhost"}}}
host = config.get("db", {}).get("slave", {}).get("host", "未配置从库")
print(f"从库地址：{host}")

# 案例三：or 防御 None / 空值
# get 返回 None 时（键存在但值是 None），默认值参数不会生效，要用 or
user = {"name": "小李", "tags": None}
tags = user.get("tags") or ["无标签"]  # None 或空列表都回退到默认
print(f"标签：{tags}")
count = user.get("login_count") or 0
print(f"登录次数：{count}")

# 案例四：try/except 取值 —— 报错信息更明确
def get_city(data):
    try:
        return data["address"]["city"]
    except KeyError as e:
        return f"缺少字段 {e}，请补全资料"

print(get_city({"address": {"city": "深圳"}}))
print(get_city({"address": {}}))
print(get_city({}))

# 案例五：批量安全提取 —— 脏数据不中断
raw_users = [
    {"name": "小张", "score": 88},
    {"name": "小李"},               # 缺 score
    {"name": "小王", "score": None},  # score 是 None
]
for u in raw_users:
    score = u.get("score") or 0
    print(f"{u.get('name', '匿名')}：{score} 分")

# ===== 练习题 =====
# 1. 数据 {"a": {"b": {"c": 1}}}：用 get 链取 "a.b.c" 的值；再取 "a.x.c" 验证不崩溃返回默认 -1。
# 2. 写函数 deep_get(data, keys, default)：keys 是字段名列表如 ["a", "b", "c"]，逐层 get 实现通用安全取值，用上面数据测试 3 组。
# 3. 商品列表里部分商品缺 price 字段，循环用 get 取 price 默认 0，最后统计"缺价格的商品名列表"。
