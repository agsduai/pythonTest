# ===== 第1014课：常见错误与调试-KeyError与字典容错 =====
# 知识点：
#   - KeyError：用不存在的键去取字典，直接崩溃
#   - get() 是防 KeyError 的第一工具：键不存在返回默认值而不报错
#   - in 判断键是否存在，适合"存在才处理"的场景
#   - setdefault() ：键不存在就补上默认值，存在则不动

# 案例一：查会员信息 —— 键不存在直接崩溃
member = {"name": "小张", "level": "VIP"}
# print(member["phone"])  # 报 KeyError: 'phone'
# 解读：字典里没有 'phone' 这个键
print(member.get("phone", "未填写"))  # get 带默认值，不崩溃

# 案例二：外卖地址统计 —— get() 累计计数
# 场景：统计订单送往哪些小区
orders = ["幸福小区", "阳光小区", "幸福小区", "绿岛", "幸福小区"]
counts = {}
for order in orders:
    counts[order] = counts.get(order, 0) + 1  # 第一次出现默认 0，再加 1
print(f"小区分布：{counts}")

# 案例三：in 判断 —— 存在才处理
config = {"host": "localhost", "port": 8080}
if "port" in config:
    print(f"端口：{config['port']}")
else:
    print("配置里没写端口，用默认 80")

# 案例四：setdefault —— 补全用户资料
profile = {"name": "小李"}
profile.setdefault("city", "未知城市")  # 没有就补上
profile.setdefault("city", "北京")  # 已经有了，不会覆盖
print(f"资料：{profile}")

# ===== 练习题 =====
# 1. 定义 goods = {"苹果": 5.5, "香蕉": 3.2}，分别用 ["梨"] 和 get("梨", 0) 取价格，观察一个崩溃一个不崩溃。
# 2. 统计字符串 "abracadabra" 中每个字母出现的次数，要求用 get() 完成，输出每个字母的计数。
# 3. 写函数 safe_get(d, key)：键存在返回值，不存在返回默认值 0 且不报错；用 {"a": 1} 测试取 "a" 和 "b"。
