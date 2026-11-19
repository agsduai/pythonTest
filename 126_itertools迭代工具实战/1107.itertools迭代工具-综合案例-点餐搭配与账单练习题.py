# ===== 第1107课：itertools迭代工具-综合案例-点餐搭配与账单 =====
# 知识点：
#   - 综合运用：product（搭配）/ combinations（凑单）/ accumulate（累计）/ groupby
#   - 点餐系统套路：菜单 -> 套餐搭配 -> 凑单推荐 -> 小票输出
#   - 枚举工具只用于小规模候选，先估算数量再生成
#   - 小票分阶段输出：明细、小计、累计、推荐

# 案例一：菜单与套餐搭配（product）
import itertools

menu = {"主食": {"米饭": 3, "面条": 5}, "饮料": {"可乐": 3, "酸奶": 4}}
combos = list(itertools.product(menu["主食"].items(), menu["饮料"].items()))
print("--- 可选套餐 ---")
for (staple, sp), (drink, dp) in combos:
    print(f"{staple}+{drink}：{sp + dp} 元")

# 案例二：选好套餐后的账单累计（accumulate）
my_order = ["米饭", "面条", "可乐", "酸奶"]
prices = {**menu["主食"], **menu["饮料"]}
order_prices = [prices[g] for g in my_order]
running = list(itertools.accumulate(order_prices))
print("--- 点单累计 ---")
for goods, cum in zip(my_order, running):
    print(f"{goods}（{prices[goods]} 元）累计 {cum} 元")
print(f"合计：{running[-1]} 元")

# 案例三：凑单推荐（combinations）
# 场景：满 15 减 4，还差几元，找出"再加一件刚好够"的商品
current_total = running[-1]
discount_line = 15
if current_total < discount_line:
    gap = discount_line - current_total
    print(f"距满 15 还差 {gap} 元，推荐加购：")
    candidates = ["茶叶蛋2", "卤味拼盘", "煎蛋1", "肉丸汤"]
    candidate_prices = {"茶叶蛋2": 2, "卤味拼盘": 6, "煎蛋1": 2, "肉丸汤": 5}
    for goods, price in candidate_prices.items():
        if price >= gap:
            print(f"  {goods}（{price} 元）可解锁满减")
else:
    print(f"已满 {discount_line} 减 4，实付 {current_total - 4} 元")

# 案例四：多人拼单分组（groupby）
# 场景：4 人各点各的，按人分组出小票
order_rows = [
    ("小张", "米饭", 3), ("小张", "可乐", 3),
    ("小李", "面条", 5), ("小李", "酸奶", 4), ("小李", "煎蛋", 2),
    ("小王", "米饭", 3),
]
order_rows.sort(key=lambda r: r[0])
print("--- 拼单小票 ---")
grand_total = 0
for user, group in itertools.groupby(order_rows, key=lambda r: r[0]):
    items = list(group)
    subtotal = sum(p for _, _, p in items)
    grand_total += subtotal
    detail = "、".join(f"{g}{p}" for _, g, p in items)
    print(f"{user}：{detail}，小计 {subtotal} 元")
print(f"整单合计：{grand_total} 元")

# 案例五：AA 均摊（衔接 123 章）
per_person = round(grand_total / 3, 2)
print(f"AA 每人约 {per_person} 元（3 人均摊）")

# ===== 练习题 =====
# 1. 给菜单加"小食"组（2 种），用三层 product 生成主食 x 饮料 x 小食的全部套餐并打印数量。
# 2. 写函数 best_add(current, candidates, threshold)：用 combinations 找"加购总价最接近凑单线且不超过 10 元"的单品组合，返回该组合。
# 3. 综合挑战：把案例三、四合并成函数 checkout(order_rows, discount_line, discount_amount)：输出每人小票、整单合计、满减后实付，用样例数据跑通。
