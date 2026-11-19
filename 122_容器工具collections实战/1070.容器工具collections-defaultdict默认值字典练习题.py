# ===== 第1070课：容器工具collections-defaultdict默认值字典 =====
# 知识点：
#   - defaultdict(list)：取不存在的键时自动创建默认值，不再 KeyError
#   - 常用工厂：list（分组）、int（计数）、set（去重收集）
#   - 和 dict.get 的区别：defaultdict 真的会"创建并写入"，get 只临时返回
#   - 实际场景：按班级分组学生、按首字母归档单词

# 案例一：分组 —— defaultdict(list)
from collections import defaultdict

students = [
    ("一班", "小张"), ("二班", "小李"),
    ("一班", "小王"), ("三班", "小赵"), ("二班", "小周"),
]
groups = defaultdict(list)
for cls, name in students:
    groups[cls].append(name)  # 键不存在时自动给个空列表
print(f"分组结果：{dict(groups)}")

# 案例二：计数 —— defaultdict(int)
# 场景：统计每类商品销量
orders = ["苹果", "牛奶", "苹果", "面包", "苹果"]
sales = defaultdict(int)
for o in orders:
    sales[o] += 1  # 键不存在时默认 0，直接 +1
print(f"销量：{dict(sales)}")

# 案例三：去重收集 —— defaultdict(set)
# 场景：统计每个用户买过哪些商品（自动去重）
purchases = [
    ("小张", "苹果"), ("小张", "牛奶"), ("小张", "苹果"),
    ("小李", "面包"),
]
bought = defaultdict(set)
for user, goods in purchases:
    bought[user].add(goods)
print(f"购买记录：{dict(bought)}")

# 案例四：对比普通 dict 的写法繁琐度
# 普通 dict 写法：
normal = {}
for cls, name in students:
    if cls not in normal:
        normal[cls] = []
    normal[cls].append(name)
print(f"普通写法：{normal}")
# defaultdict 少了"判断键存在"这一步，代码更干净

# 案例五：嵌套分组 —— 两级归类
# 场景：按 城市->品类 汇总金额
records = [
    ("北京", "食品", 100), ("北京", "数码", 500),
    ("上海", "食品", 80), ("北京", "食品", 60),
]
city_goods = defaultdict(lambda: defaultdict(float))  # 工厂也能是 lambda
for city, category, amount in records:
    city_goods[city][category] += amount
for city, goods in city_goods.items():
    print(f"{city}：{dict(goods)}")

# ===== 练习题 =====
# 1. 用 defaultdict(int) 统计 "banana" 每个字母出现次数，打印 dict。
# 2. 单词列表 ["apple","avocado","banana","blueberry","cherry"]，用 defaultdict(list) 按首字母分组。
# 3. 订单记录 [("周一","外卖"),("周一","打车"),("周二","外卖")]，用 defaultdict(list) 按"星期"分组输出，再统计每个星期订单数。
