# ===== 第1090课：嵌套数据处理-分组汇总与透视 =====
# 知识点：
#   - 分组汇总三步：按字段分组（defaultdict）-> 组内聚合（求和/计数/均值）-> 排行输出
#   - "透视"就是二维分组：行字段 x 列字段 各算一个值
#   - 聚合字段可以是"数量、金额、平均、最大"多种混合
#   - 实际场景：按部门汇总工资、按月份汇总销售额

# 案例一：单维分组计数
from collections import defaultdict, Counter

employees = [
    {"name": "小张", "dept": "技术", "salary": 15000},
    {"name": "小李", "dept": "技术", "salary": 12000},
    {"name": "小王", "dept": "销售", "salary": 9000},
    {"name": "小赵", "dept": "销售", "salary": 11000},
    {"name": "小周", "dept": "人事", "salary": 8000},
]
dept_count = Counter(e["dept"] for e in employees)
print(f"各部门人数：{dict(dept_count)}")

# 案例二：单维分组求和与均值
dept_stats = defaultdict(lambda: [0, 0.0])  # [人数, 工资总额]
for e in employees:
    dept_stats[e["dept"]][0] += 1
    dept_stats[e["dept"]][1] += e["salary"]
for dept, (cnt, total) in sorted(dept_stats.items(), key=lambda kv: -kv[1][1]):
    print(f"{dept}：{cnt} 人，总额 {total:.0f}，平均 {total / cnt:.0f}")

# 案例三：二维透视 —— 城市 x 品类 销售额
sales = [
    {"city": "北京", "goods": "水果", "amount": 100},
    {"city": "北京", "goods": "数码", "amount": 500},
    {"city": "上海", "goods": "水果", "amount": 80},
    {"city": "上海", "goods": "数码", "amount": 300},
    {"city": "北京", "goods": "水果", "amount": 60},
]
pivot = defaultdict(lambda: defaultdict(float))
cities, goods_types = set(), set()
for s in sales:
    pivot[s["city"]][s["goods"]] += s["amount"]
    cities.add(s["city"])
    goods_types.add(s["goods"])
print("     " + "".join(f"{g:>8}" for g in sorted(goods_types)))
for city in sorted(cities):
    row = "".join(f"{pivot[city].get(g, 0):>8.0f}" for g in sorted(goods_types))
    print(f"{city:<5}{row}")

# 案例四：组内找最大值
# 场景：每个部门工资最高的人
dept_top = {}
for e in employees:
    if e["dept"] not in dept_top or e["salary"] > dept_top[e["dept"]]["salary"]:
        dept_top[e["dept"]] = e
for dept, e in dept_top.items():
    print(f"{dept} 最高：{e['name']}（{e['salary']}）")

# ===== 练习题 =====
# 1. 订单列表含 user/amount：按 user 汇总总金额并降序打印排行榜。
# 2. 用案例三数据给透视表加"行合计"列和"列合计"行，输出带合计的完整报表。
# 3. 写函数 group_by(items, key_field)：通用分组函数返回 {字段值: [记录列表]}，用 employees 按部门测试并打印各组人数。
