# ===== 第414课：架构与重构-依赖倒置与端口适配器 =====
# 知识点：
#   - 端口（Port）：业务定义的抽象接口，表达“我需要什么能力”
#   - 适配器（Adapter）：针对某个具体技术实现该接口（sqlite/redis/HTTP）
#   - 依赖方向：业务 → 端口 ← 适配器（箭头都指向抽象）
#   - 组合根（Composition Root）：程序入口负责选适配器并注入
#   - 收益：换数据库不改业务；测试用内存适配器，毫秒级
import sqlite3
from dataclasses import dataclass
from typing import Protocol


@dataclass
class User:
    id: int
    email: str
    active: bool = True


# ---------------- 端口：业务需要的能力 ----------------
class UserRepository(Protocol):
    def add(self, email: str) -> User: ...
    def find_by_email(self, email: str) -> User | None: ...
    def deactivate(self, user_id: int) -> None: ...


# ---------------- 适配器 1：内存 ----------------
class InMemoryUserRepo:

    def __init__(self):
        self._users: dict[int, User] = {}
        self._next = 1

    def add(self, email: str) -> User:
        user = User(self._next, email)
        self._users[user.id] = user
        self._next += 1
        return user

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    def deactivate(self, user_id: int) -> None:
        if user_id in self._users:
            self._users[user_id].active = False


# ---------------- 适配器 2：SQLite ----------------
class SqliteUserRepo:

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT UNIQUE, active INTEGER DEFAULT 1)"
        )
        self.conn.commit()

    def add(self, email: str) -> User:
        cur = self.conn.execute("INSERT INTO users (email) VALUES (?)", (email,))
        self.conn.commit()
        return User(cur.lastrowid, email)

    def find_by_email(self, email: str) -> User | None:
        row = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return User(row["id"], row["email"], bool(row["active"])) if row else None

    def deactivate(self, user_id: int) -> None:
        self.conn.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
        self.conn.commit()


# ---------------- 业务用例：只依赖端口 ----------------
class RegisterUser:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, email: str) -> User:
        email = email.strip().lower()
        if "@" not in email:
            raise ValueError("邮箱格式不正确")
        if self.repo.find_by_email(email):
            raise ValueError("邮箱已注册")
        return self.repo.add(email)

    def deactivate(self, email: str):
        user = self.repo.find_by_email(email)
        if user is None:
            raise LookupError("用户不存在")
        self.repo.deactivate(user.id)


def run(use_case: RegisterUser, label: str):
    print(f"\n== {label} ==")
    u = use_case.execute("Ming@Example.com")
    print("  注册：", u)
    try:
        use_case.execute("ming@example.com")      # 规范化后重复
    except ValueError as exc:
        print("  拦截：", exc)
    use_case.deactivate("ming@example.com")
    print("  已停用：", use_case.repo.find_by_email("ming@example.com"))


# ---------------- 组合根：入口决定用哪个适配器 ----------------
USE_SQLITE = True
repo = SqliteUserRepo() if USE_SQLITE else InMemoryUserRepo()
run(RegisterUser(repo), "SQLite 适配器" if USE_SQLITE else "内存适配器")

# ---- 测试场景：内存适配器无需任何清理 ----
run(RegisterUser(InMemoryUserRepo()), "内存适配器（测试用）")

# 检查依赖方向：
#   RegisterUser 的 import 列表里没有 sqlite3 —— 业务不认识数据库
#   SqliteUserRepo 才 import sqlite3 —— 细节被关在适配器里

# ===== 练习题 =====
# 1. 增加第三个适配器 FileUserRepo：把用户存到 JSON 文件（第232课）。
# 2. 给端口增加 list_active()，两个适配器各实现一遍。
# 3. 写一个 FakeRepo 统计 add 被调用了几次，用于单元测试。
# 4. 思考：端口由业务定义还是由适配器定义？为什么？
