# ===== 第208课：数据库操作-事务与回滚 =====
# 知识点：
#   - 事务：一组操作要么全部成功（commit），要么全部撤销（rollback）
#   - 典型场景：转账 = 扣款 + 到账，两步必须同时成功
#   - sqlite3 默认开启隐式事务，commit 之前可以整体回滚
#   - with conn: 语句块正常结束自动提交，异常自动回滚

import sqlite3

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE account (name TEXT PRIMARY KEY, balance REAL)")
cursor.executemany(
    "INSERT INTO account (name, balance) VALUES (?, ?)",
    [("张三", 1000), ("李四", 500)],
)
conn.commit()


def transfer(from_name, to_name, amount):
    """转账：扣款和到账放在同一个事务里。"""
    try:
        cursor.execute(
            "UPDATE account SET balance = balance - ? WHERE name = ?",
            (amount, from_name),
        )
        cursor.execute(
            "UPDATE account SET balance = balance + ? WHERE name = ?",
            (amount, to_name),
        )
        # 业务校验：余额不能为负
        balance = cursor.execute(
            "SELECT balance FROM account WHERE name = ?", (from_name,)
        ).fetchone()[0]
        if balance < 0:
            raise ValueError(f"{from_name} 余额不足")
        conn.commit()
        print(f"转账成功：{from_name} → {to_name}，金额 {amount}")
    except Exception as exc:
        conn.rollback()      # 撤销本事务内的全部修改
        print(f"转账失败已回滚：{exc}")


transfer("张三", "李四", 300)      # 正常转账
transfer("张三", "李四", 9999)     # 余额不足，整体回滚

print("当前余额：")
for row in cursor.execute("SELECT * FROM account"):
    print(" ", tuple(row))

# 更 Python 的写法：with conn 自动提交/回滚
try:
    with conn:
        cursor.execute("UPDATE account SET balance = balance - 50 WHERE name='张三'")
        cursor.execute("UPDATE account SET balance = balance + 50 WHERE name='李四'")
        raise RuntimeError("故意出错，验证自动回滚")
except RuntimeError as exc:
    print(f"with conn 捕获：{exc}（两条 UPDATE 已被自动撤销）")

print("回滚后的余额：")
for row in cursor.execute("SELECT * FROM account"):
    print(" ", tuple(row))

conn.close()

# ===== 练习题 =====
# 1. 把 transfer 里的 conn.rollback() 注释掉，看失败后余额变成什么样。
# 2. 用 with conn 改写 transfer 函数。
# 3. 思考：批量插入 10 万条数据时，为什么建议每 1 万条 commit 一次？
