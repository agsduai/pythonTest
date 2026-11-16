# ===== 第437课：SQLite高级-UPSERT与RETURNING =====
# 知识点：
#   - UPSERT：INSERT ... ON CONFLICT(键) DO UPDATE SET ... —— 存在则更新、不存在则插入
#   - DO NOTHING：冲突时静默跳过（等价 INSERT OR IGNORE）
#   - RETURNING：让 INSERT/UPDATE/DELETE 直接返回受影响的行，省一次 SELECT
#   - 常见用法：计数器累加、版本号自增、幂等写入
#   - 要求：SQLite >= 3.35（本机 3.50.4）
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE counter (
    name TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE stock (
    sku TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL
);
""")

print("== 1. 计数器：冲突时 value+1、version+1，并 RETURNING 返回新值 ==")
for _ in range(3):
    row = conn.execute("""
        INSERT INTO counter (name, value, version) VALUES ('page_view', 1, 1)
        ON CONFLICT(name) DO UPDATE SET
            value = value + 1,
            version = version + 1
        RETURNING name, value, version
    """).fetchone()
    print("  ", dict(row))
conn.commit()

print("\n== 2. 库存：存在则覆盖数量，不存在则插入 ==")
for sku, qty in [("A001", 10), ("A002", 5), ("A001", 8)]:
    row = conn.execute("""
        INSERT INTO stock (sku, quantity) VALUES (?, ?)
        ON CONFLICT(sku) DO UPDATE SET quantity = excluded.quantity
        RETURNING sku, quantity
    """, (sku, qty)).fetchone()
    print(f"  写入 {sku}={qty} → 数据库 {row['sku']}={row['quantity']}")
conn.commit()

print("\n== 3. DO NOTHING：只插入不更新 ==")
row = conn.execute("""
    INSERT INTO stock (sku, quantity) VALUES ('A001', 999)
    ON CONFLICT(sku) DO NOTHING
    RETURNING sku, quantity
""").fetchone()
print("  冲突且 DO NOTHING → RETURNING 无行：", row)
row = conn.execute("SELECT * FROM stock WHERE sku = 'A001'").fetchone()
print("  原值保持不变：", dict(row))

print("\n== 4. UPDATE ... RETURNING：更新后立刻拿结果 ==")
row = conn.execute("""
    UPDATE stock SET quantity = quantity - 3
    WHERE sku = 'A001'
    RETURNING sku, quantity
""").fetchone()
print("  出库 3 件后：", dict(row))

print("\n== 5. DELETE ... RETURNING：删除并返回被删行 ==")
row = conn.execute("DELETE FROM stock WHERE sku = 'A002' RETURNING *").fetchone()
print("  已删除：", dict(row))
print("  剩余库存：", [dict(r) for r in conn.execute("SELECT * FROM stock")])

print("\n== 6. 批量导入中的 UPSERT（幂等写入）==")
conn.execute("CREATE TABLE daily_metric (day TEXT, metric TEXT, value INTEGER, PRIMARY KEY(day, metric))")
conn.executemany("""
    INSERT INTO daily_metric (day, metric, value) VALUES (?, ?, ?)
    ON CONFLICT(day, metric) DO UPDATE SET value = excluded.value
""", [
    ("2026-11-12", "orders", 120),
    ("2026-11-12", "revenue", 9800),
    ("2026-11-13", "orders", 135),
])
conn.commit()
# 重跑同一批数据：值不变、不产生重复
conn.executemany("""
    INSERT INTO daily_metric (day, metric, value) VALUES (?, ?, ?)
    ON CONFLICT(day, metric) DO UPDATE SET value = excluded.value
""", [
    ("2026-11-12", "orders", 120),
    ("2026-11-12", "revenue", 9800),
    ("2026-11-13", "orders", 135),
])
conn.commit()
rows = conn.execute("SELECT * FROM daily_metric ORDER BY day, metric").fetchall()
print("  重跑后行数：", len(rows), "（幂等，不会翻倍）")
for r in rows:
    print("  ", dict(r))

conn.close()

# 对比三种写法：
#   INSERT OR REPLACE：先删后插，会触发外键/触发器，且 id 可能变化
#   INSERT ... ON CONFLICT DO UPDATE：真正的“更新”，推荐
#   INSERT ... ON CONFLICT DO NOTHING：只保证不报错，不更新

# ===== 练习题 =====
# 1. 给 counter 增加 last_updated 字段，冲突更新时写入当前时间。
# 2. 用 UPSERT + RETURNING 实现“点赞数 +1 并返回最新数”。
# 3. 比较 INSERT OR REPLACE 与 UPSERT 在自增主键上的差异。
# 4. 思考：为什么说 UPSERT 是“可重跑任务”的基础？（第45章会用到）
