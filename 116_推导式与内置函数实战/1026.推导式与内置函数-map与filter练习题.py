# ===== 第1026课：推导式与内置函数-map与filter =====
# 知识点：
#   - map(函数, 列表)：对每个元素套用函数，惰性返回，需要 list() 展开看到结果
#   - filter(函数, 列表)：函数返回 True 的元素才留下
#   - map/filter 常配 lambda 一起用：一行完成"转换 + 过滤"
#   - 现代 Python 更推荐推导式，但读别人的代码必须会这两个

# 案例一：map 转换 —— 字符串列表转数字
# 场景：CSV 读出来全是字符串，要批量转 int
raw = ["10", "25", "8", "32"]
nums = list(map(int, raw))  # int 直接当函数传，比 lambda 更简洁
print(f"转成数字：{nums}，总和：{sum(nums)}")

# 案例二：map + lambda —— 给所有价格打折
prices = [100, 80, 200]
discounted = list(map(lambda p: p * 0.8, prices))
print(f"8 折价：{discounted}")  # [80.0, 64.0, 160.0]
# 等价的推导式写法：[p * 0.8 for p in prices]

# 案例三：filter 过滤 —— 挑出大额订单
orders = [120, 45, 200, 80, 350]
big_orders = list(filter(lambda o: o >= 100, orders))
print(f"满 100 的订单：{big_orders}")  # [120, 200, 350]
# 等价的推导式：[o for o in orders if o >= 100]

# 案例四：map + filter 组合 —— 先过滤再转换
# 场景：从脏数据里挑出合法数字并转成 float
data = ["12.5", "abc", "", "8", "  ", "20.5"]
valid = list(map(float, filter(lambda x: x.strip().replace(".", "", 1).isdigit(), data)))
print(f"合法数字：{valid}")  # [12.5, 8.0, 20.5]

# 案例五：结合字符串方法 —— 批量清洗用户名
names = ["  小张 ", "小李", "  小王"]
clean_names = list(map(str.strip, names))
print(f"清洗后：{clean_names}")  # ['小张', '小李', '小王']

# ===== 练习题 =====
# 1. 用 map 把 ["1", "2", "3", "4"] 转成数字列表并求和，输出总和 10。
# 2. 用 filter + lambda 从 [15, -3, 22, 0, -8, 7] 中过滤出偶数，输出 [22, 0, -8]。
# 3. 先 filter 挑出列表 ["apple", "", "avocado", "banana"] 中以 "a" 开头的，再用 map 全部转大写，输出 ["APPLE", "AVOCADO"]。
