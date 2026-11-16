# ===== 第435课：SQLite高级-窗口函数 =====
# 知识点：
#   - 窗口函数：在“不合并行”的前提下做分组排名/累计/前后行比较
#   - OVER(PARTITION BY ... ORDER BY ...) 定义窗口
#   - ROW_NUMBER 行号、RANK 并列跳号、DENSE_RANK 并列不跳号
#   - SUM/AVG OVER：累计与移动平均；LAG/LEAD 取前后行
#   - 与 GROUP BY 的区别：GROUP BY 一行变一行，窗口函数保留明细
#   - “每组 TopN”是窗口函数最经典的用法
# 依赖：无（sqlite3 内置，要求 SQLite >= 3.25）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    product TEXT,
    month TEXT,
    amount REAL
);
""")
conn.executemany(
    "INSERT INTO sales (product, month, amount) VALUES (?, ?, ?)",
    [
        ("键盘", "2026-09", 800), ("键盘", "2026-10", 1200), ("键盘", "2026-11", 900),
        ("鼠标", "2026-09", 300), ("鼠标", "2026-10", 500), ("鼠标", "2026-11", 700),
        ("显示器", "2026-09", 1500), ("显示器", "2026-10", 1500), ("显示器", "2026-11", 2000),
    ],
)
conn.commit()

print("== 排名：每商品按销售额排名 ==")
rows = conn.execute("""
    SELECT product, month, amount,
           ROW_NUMBER() OVER (PARTITION BY product ORDER BY amount DESC) AS rn,
           RANK()       OVER (PARTITION BY product ORDER BY amount DESC) AS rk,
           DENSE_RANK() OVER (PARTITION BY product ORDER BY amount DESC) AS drk
    FROM sales
    ORDER BY product, amount DESC
""").fetchall()
for r in rows:
    print(f"  {r['product']:4s} {r['month']} {r['amount']:7.0f} | "
          f"row_number={r['rn']} rank={r['rk']} dense={r['drk']}")

print("\n== 每组 Top1（经典用法）==")
rows = conn.execute("""
    SELECT * FROM (
        SELECT product, month, amount,
               ROW_NUMBER() OVER (PARTITION BY product ORDER BY amount DESC) AS rn
        FROM sales
    ) WHERE rn = 1
""").fetchall()
for r in rows:
    print(f"  {r['product']}: {r['month']} 最高 {r['amount']:.0f}")

print("\n== 累计销售额（按商品、按月）==")
rows = conn.execute("""
    SELECT product, month, amount,
           SUM(amount) OVER (
               PARTITION BY product ORDER BY month
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS running_total
    FROM sales
    ORDER BY product, month
""").fetchall()
for r in rows:
    print(f"  {r['product']:4s} {r['month']} 当月 {r['amount']:6.0f} | 累计 {r['running_total']:7.0f}")

print("\n== 环比：LAG 取上月销售额 ==")
rows = conn.execute("""
    SELECT product, month, amount,
           LAG(amount) OVER (PARTITION BY product ORDER BY month) AS prev_amount,
           ROUND(amount - LAG(amount) OVER (PARTITION BY product ORDER BY month), 1) AS diff
    FROM sales
    ORDER BY product, month
""").fetchall()
for r in rows:
    prev = "-" if r["prev_amount"] is None else f"{r['prev_amount']:.0f}"
    diff = "-" if r["diff"] is None else f"{r['diff']:+.0f}"
    print(f"  {r['product']:4s} {r['month']} {r['amount']:6.0f} | 上月 {prev:>5s} | 变化 {diff}")

print("\n== 移动平均（最近 2 个月）==")
rows = conn.execute("""
    SELECT product, month, amount,
           ROUND(AVG(amount) OVER (
               PARTITION BY product ORDER BY month
               ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
           ), 1) AS ma2
    FROM sales ORDER BY product, month
""").fetchall()
for r in rows:
    print(f"  {r['product']:4s} {r['month']} {r['amount']:6.0f} | 2月均线 {r['ma2']:7.1f}")

conn.close()

# 使用提醒：
#   窗口函数在 SELECT 阶段最后计算，所以 WHERE 里不能直接用 rn
#   需要过滤排名时，套一层子查询（如上“每组 Top1”）

# ===== 练习题 =====
# 1. 求每个商品“占全品类销售额的比例”（SUM OVER () 不带 PARTITION）。
# 2. 用 NTILE(4) 把每月销售额分成四档。
# 3. 用 LEAD 计算“距下月的变化率”。
# 4. 思考：为什么 GROUP BY 做不了“保留明细 + 加排名”？
