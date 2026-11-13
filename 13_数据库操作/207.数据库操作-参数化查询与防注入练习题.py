# ===== 第207课：数据库操作-参数化查询与防注入 =====
# 知识点：
#   - SQL 注入：把用户输入拼进 SQL 字符串，攻击者可篡改语句含义
#   - 参数化查询：SQL 与数据分离，占位符 ? 交给 sqlite3 安全处理
#   - 任何“拼接用户输入”的 SQL 都是高危写法
#   - 这是 Web 安全第一课：永远不要信任用户输入

import sqlite3

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT, password TEXT)")
cursor.executemany(
    "INSERT INTO user (name, password) VALUES (?, ?)",
    [("admin", "admin123"), ("zhangsan", "zs@2024")],
)
conn.commit()


def login_unsafe(name, password):
    """危险写法：字符串拼接 SQL。"""
    sql = f"SELECT * FROM user WHERE name='{name}' AND password='{password}'"
    print("拼接出的 SQL：", sql)
    return cursor.execute(sql).fetchone() is not None


def login_safe(name, password):
    """正确写法：参数化查询。"""
    sql = "SELECT * FROM user WHERE name=? AND password=?"
    return cursor.execute(sql, (name, password)).fetchone() is not None


# 正常登录
print("正常登录（不安全版）：", login_unsafe("admin", "admin123"))

# 注入攻击：密码框输入 ' OR '1'='1 即可绕过校验
hacker_input = "' OR '1'='1"
print("注入攻击（不安全版）：", login_unsafe("admin", hacker_input))   # True，被绕过！
print("注入攻击（安全版）　：", login_safe("admin", hacker_input))     # False，防御成功

# 说明：参数化查询里 ? 只能当“值”，不能替代表名/列名。
# 表名、列名等结构信息必须来自代码内部的白名单，不能来自用户输入。

# ===== 练习题 =====
# 1. 自己构造一个注入字符串，验证 login_safe 无法被绕过。
# 2. 编写参数化版本的模糊查询 search_user(name)，
#    （提示：LIKE 的 % 也要放在参数里：pattern = f"%{name}%"）
# 3. 思考：除了注入，拼接 SQL 还会带来什么问题？（提示：引号转义）
