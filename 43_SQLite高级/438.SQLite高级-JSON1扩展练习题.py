# ===== 第438课：SQLite高级-JSON1扩展 =====
# 知识点：
#   - SQLite 内置 JSON1：JSON 字段可直接存 TEXT，用函数查询/修改
#   - json_extract(json, '$.key') / -> / ->> 取字段
#   - json_each()：把数组/对象展开成多行（配合 JOIN 做标签过滤）
#   - json_group_array / json_object：聚合回 JSON
#   - json_set / json_patch：局部修改
#   - 适合“半结构化数据”：事件日志、扩展属性、标签
# 依赖：无（sqlite3 内置 JSON1）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE event (
    id INTEGER PRIMARY KEY,
    user TEXT,
    payload TEXT NOT NULL          -- JSON 字符串
);
""")
conn.executemany(
    "INSERT INTO event (user, payload) VALUES (?, ?)",
    [
        ("小明", '{"action": "login", "tags": ["web", "mobile"], "ip": "10.0.0.1"}'),
        ("小红", '{"action": "purchase", "tags": ["web"], "amount": 199}'),
        ("小明", '{"action": "purchase", "tags": ["web", "vip"], "amount": 580}'),
    ],
)
conn.commit()

print("== 1. 提取字段 ==")
rows = conn.execute("""
    SELECT id, user,
           json_extract(payload, '$.action') AS action,
           payload -> '$.amount' AS amount_json,
           payload ->> '$.amount' AS amount_text
    FROM event
""").fetchall()
for r in rows:
    print(f"  #{r['id']} {r['user']:3s} action={r['action']:8s} "
          f"amount_json={r['amount_json']} amount_text={r['amount_text']}")

print("\n== 2. 展开数组：每个标签一行 ==")
rows = conn.execute("""
    SELECT e.id, e.user, json_each.value AS tag
    FROM event e, json_each(e.payload, '$.tags')
    ORDER BY e.id
""").fetchall()
for r in rows:
    print(f"  #{r['id']} {r['user']} → {r['tag']}")

print("\n== 3. 按标签过滤事件 ==")
rows = conn.execute("""
    SELECT DISTINCT e.id, e.user, e.payload ->> '$.action' AS action
    FROM event e, json_each(e.payload, '$.tags')
    WHERE json_each.value = 'vip'
""").fetchall()
print("  带 vip 标签：", [dict(r) for r in rows])

print("\n== 4. 聚合：每个用户的标签集合 ==")
rows = conn.execute("""
    SELECT user, json_group_array(DISTINCT json_each.value) AS tags
    FROM event, json_each(event.payload, '$.tags')
    GROUP BY user
""").fetchall()
for r in rows:
    print(f"  {r['user']}: {r['tags']}")

print("\n== 5. 聚合：每个用户的消费总额（排除非购买事件）==")
rows = conn.execute("""
    SELECT user,
           SUM(CAST(payload ->> '$.amount' AS REAL)) AS total
    FROM event
    WHERE json_extract(payload, '$.action') = 'purchase'
    GROUP BY user
""").fetchall()
for r in rows:
    print(f"  {r['user']}: {r['total']}")

print("\n== 6. 修改 JSON：json_set 与 json_patch ==")
conn.execute("""
    UPDATE event
    SET payload = json_set(payload, '$.channel', 'app', '$.amount', 200)
    WHERE id = 2
""")
conn.commit()
row = conn.execute("SELECT payload FROM event WHERE id = 2").fetchone()
print("  json_set 后：", row["payload"])

conn.execute("""
    UPDATE event
    SET payload = json_patch(payload, '{"channel": "h5", "tags": ["web", "h5"]}')
    WHERE id = 2
""")
conn.commit()
row = conn.execute("SELECT payload FROM event WHERE id = 2").fetchone()
print("  json_patch 后：", row["payload"])

print("\n== 7. 表达式索引：加速按 JSON 字段查询 ==")
conn.execute("CREATE INDEX idx_event_action ON event(json_extract(payload, '$.action'))")
plan = conn.execute("""
    EXPLAIN QUERY PLAN
    SELECT * FROM event WHERE json_extract(payload, '$.action') = 'purchase'
""").fetchall()
for r in plan:
    print("  ", r["detail"])
print("  注意：WHERE 里的表达式必须与索引表达式完全一致，索引才会生效")

conn.close()

# 设计权衡：
#   常用字段 → 拆成普通列（可索引、类型明确）
#   变化频繁/稀疏的扩展信息 → 放 JSON 列
#   既要查 JSON 又怕慢 → 用“生成列 + 索引”或表达式索引

# ===== 练习题 =====
# 1. 统计每个 action 的事件数（json_extract + GROUP BY）。
# 2. 找出 tags 数组长度 >= 2 的事件（json_array_length）。
# 3. 用 json_each 实现“按标签分组统计事件数”。
# 4. 思考：JSON 列和 EAV（键值对表）模型各适合什么场景？
