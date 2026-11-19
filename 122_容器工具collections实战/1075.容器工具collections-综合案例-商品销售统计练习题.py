# ===== 第1075课：容器工具collections-综合案例-商品销售统计 =====
# 知识点：
#   - 综合运用：Counter / defaultdict / namedtuple / most_common / 排序
#   - 统计流程：原始流水 -> 结构化记录 -> 分组聚合 -> 排行输出
#   - 排行榜三件套：Counter.most_common、sorted + key、并列处理
#   - 输出格式友好：对齐、千分位、Top N 截取

# 案例一：原始流水结构化
from collections import Counter, defaultdict, namedtuple

Sale = namedtuple("Sale", ["order", "goods", "category", "qty", "price"])
raw = [
    ("S001", "苹果", "水果", 3, 5.5),
    ("S002", "牛奶", "饮品", 2, 8.0),
    ("S003", "苹果", "水果", 1, 5.5),
    ("S004", "酸奶", "饮品", 4, 6.5),
    ("S005", "面包", "烘焙", 2, 12.0),
    ("S006", "苹果", "水果", 5, 5.5),
    ("S007", "牛奶", "饮品", 1, 8.0),
    ("S008", "蛋糕", "烘焙", 1, 25.0),
]
sales = [Sale(*row) for row in raw]
print(f"共 {len(sales)} 笔流水")

# 案例二：商品销量排行（件数）
qty_counter = Counter()
for s in sales:
    qty_counter[s.goods] += s.qty
print("--- 件数排行 ---")
for rank, (goods, qty) in enumerate(qty_counter.most_common(), start=1):
    print(f"第 {rank} 名：{goods}（{qty} 件）")

# 案例三：品类销售额汇总（金额）
category_revenue = defaultdict(float)
for s in sales:
    category_revenue[s.category] += s.qty * s.price
print("--- 品类销售额 ---")
for cat, revenue in sorted(category_revenue.items(), key=lambda kv: kv[1], reverse=True):
    print(f"{cat}：￥{revenue:,.1f}")

# 案例四：冠军商品 + 并列处理
top_qty = max(qty_counter.values())
champions = [g for g, q in qty_counter.items() if q == top_qty]
print(f"销量冠军（{top_qty} 件）：{'、'.join(champions)}")

# 案例五：客单价与总览
total_revenue = sum(s.qty * s.price for s in sales)
avg_price = total_revenue / len(sales)
print(f"总销售额：￥{total_revenue:,.2f}，平均单笔：￥{avg_price:.2f}")

# 单笔最大订单
biggest = max(sales, key=lambda s: s.qty * s.price)
print(f"最大单笔：{biggest.order}（{biggest.goods} x{biggest.qty}，￥{biggest.qty * biggest.price:.1f}）")

# 案例六：组合报表输出
print("====== 销售日报 ======")
print(f"{'商品':<6}{'品类':<6}{'件数':>4}{'金额':>10}")
goods_summary = defaultdict(lambda: [0, 0.0])  # 商品 -> [件数, 金额]
for s in sales:
    goods_summary[s.goods][0] += s.qty
    goods_summary[s.goods][1] += s.qty * s.price
cat_of = {s.goods: s.category for s in sales}
for goods, (qty, money) in sorted(goods_summary.items(), key=lambda kv: kv[1][1], reverse=True):
    print(f"{goods:<6}{cat_of[goods]:<6}{qty:>4}{money:>10.1f}")

# ===== 练习题 =====
# 1. 给 Sale 增加 discount 字段，重算各类销售额（金额按 qty*price*discount），输出修正后排行。
# 2. 用 Counter 统计"哪个品类出现的订单笔数最多"（不是金额），输出 Top1。
# 3. 综合挑战：写函数 daily_report(sales) 返回一个 dict，包含 total_revenue / best_goods / category_rank 三个键，并用本课数据调用打印三项内容。
