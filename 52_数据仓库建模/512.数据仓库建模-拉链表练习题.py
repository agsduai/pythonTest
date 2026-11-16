# ===== 第512课：数据仓库建模-拉链表 =====
# 知识点：
#   - 拉链表：记录每条记录“从什么时候到什么时候有效”的历史表
#   - 字段：业务键、状态、start_date、end_date（开区间，NULL=至今）
#   - 更新：关闭旧记录（end_date=变更日），插入新记录（start_date=变更日）
#   - 查询某天快照：start_date <= d AND (end_date > d OR end_date IS NULL)
#   - 与 SCD2 的区别：SCD2 是维度表的版本化，拉链表更通用（状态/余额/等级）
#   - 优点：只存变化点，比“每天全量快照”省空间
#   - 与第509课 SCD2 的表结构几乎一致，重点在查询模式
# 依赖：无（sqlite3 内置）

import sqlite3

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE user_status_history (
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,          -- 普通 / 白银 / 黄金 / 黑铁
    start_date TEXT NOT NULL,
    end_date TEXT,                 -- 开区间；NULL 表示当前
    PRIMARY KEY (user_id, start_date)
);
""")

# ---- 写入初始状态 ----
def append_status(conn, user_id, status, changed_date):
    """关闭旧记录并插入新记录；同一天多次变更则覆盖当天。"""
    current = conn.execute("""
        SELECT * FROM user_status_history
        WHERE user_id = ? AND end_date IS NULL
    """, (user_id,)).fetchone()

    if current:
        if current["status"] == status:
            return False
        conn.execute(
            "UPDATE user_status_history SET end_date = ? WHERE user_id = ? AND start_date = ?",
            (changed_date, user_id, current["start_date"]),
        )
    conn.execute(
        "INSERT INTO user_status_history (user_id, status, start_date, end_date) "
        "VALUES (?, ?, ?, NULL)",
        (user_id, status, changed_date),
    )
    conn.commit()
    return True


def status_as_of(conn, user_id, date):
    return conn.execute("""
        SELECT * FROM user_status_history
        WHERE user_id = ? AND start_date <= ?
          AND (end_date IS NULL OR end_date > ?)
    """, (user_id, date, date)).fetchone()


append_status(conn, "U1", "普通", "2026-01-01")
append_status(conn, "U1", "白银", "2026-03-15")
append_status(conn, "U1", "黄金", "2026-07-01")
append_status(conn, "U2", "普通", "2026-02-01")
append_status(conn, "U2", "黑铁", "2026-09-01")     # 降级

print("== 拉链表全量 ==")
for r in conn.execute("SELECT * FROM user_status_history ORDER BY user_id, start_date"):
    print(f"  {r['user_id']} {r['status']:3s} {r['start_date']} ~ {r['end_date'] or '至今'}")

print("\n== 历史时点查询 ==")
for user, date in [("U1", "2026-02-01"), ("U1", "2026-05-01"),
                   ("U1", "2026-08-01"), ("U2", "2026-10-01")]:
    row = status_as_of(conn, user, date)
    print(f"  {user} 在 {date} 的状态：{row['status']}")

# ---- 某天的全量快照 ----
print("\n== 某天用户状态分布 ==")
def snapshot_distribution(conn, date):
    rows = conn.execute("""
        SELECT status, COUNT(*) AS cnt
        FROM user_status_history
        WHERE start_date <= ? AND (end_date IS NULL OR end_date > ?)
        GROUP BY status ORDER BY cnt DESC
    """, (date, date)).fetchall()
    return {r["status"]: r["cnt"] for r in rows}


for date in ("2026-02-01", "2026-04-01", "2026-08-01", "2026-10-01"):
    print(f"  {date}: {snapshot_distribution(conn, date)}")

# ---- 变化次数与当前状态 ----
print("\n== 每个用户的变更次数 ==")
rows = conn.execute("""
    SELECT user_id, COUNT(*) AS changes
    FROM user_status_history GROUP BY user_id
""").fetchall()
for r in rows:
    print(f"  {r['user_id']}: {r['changes']} 个版本")

print("\n== 当前状态 ==")
for r in conn.execute("SELECT * FROM user_status_history WHERE end_date IS NULL"):
    print(f"  {r['user_id']}: {r['status']}（自 {r['start_date']}）")

# ---- 拉链表 vs 每日快照 ----
print("\n== 拉链表 vs 每日全量快照 ==")
rows = [
    ("拉链表", "只存变化点", "省空间、可查任意时点", "更新逻辑复杂"),
    ("每日快照", "每天一行", "查询最简单", "空间大、只能查已有日期"),
]
print(f"  {'方式':<10}{'存储':<12}{'优点':<24}{'代价'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<12}{r[2]:<24}{r[3]}")

# ---- 实现要点 ----
print("\n== 实现要点 ==")
for item in [
    "end_date 用开区间：查询条件 end_date > d，不是 >=",
    "同一天多次变更：合并或按时间戳细化，避免 start_date 冲突",
    "当前记录用 end_date IS NULL 标记，加部分索引加速",
    "补数据（迟到变更）要重算受影响的区间",
    "与事实表关联时用“事件发生日期”找对应版本",
]:
    print("  -", item)

conn.close()

# ===== 练习题 =====
# 1. 给 U1 增加一次“同一天内先升后降”的变更，处理主键冲突。
# 2. 写函数 history_of(user_id)，输出某用户的完整状态时间线。
# 3. 统计每个状态的平均持续天数。
# 4. 思考：迟到数据（昨天的变更今天才到）如何修正拉链表？
