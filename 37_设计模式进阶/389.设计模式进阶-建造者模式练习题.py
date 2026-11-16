# ===== 第389课：设计模式进阶-建造者模式 =====
# 知识点：
#   - 建造者：把“复杂对象的组装过程”从构造函数里拆出来，链式分步构建
#   - 适用：参数多、可选参数多、需要多种“配方”的对象（SQL、HTTP 请求、配置单）
#   - Python 实现：方法返回 self 即可链式调用；build() 做最终校验
#   - 与工厂的区别：工厂关注“造哪种”，建造者关注“怎么一步步造”


class QueryBuilder:
    """安全地拼 SQL：值走参数列表，绝不字符串拼接。"""

    def __init__(self):
        self._columns = ["*"]
        self._table = None
        self._conditions: list[str] = []
        self._params: list = []
        self._order: list[str] = []
        self._limit = None

    def select(self, *columns):
        if columns:
            self._columns = list(columns)
        return self

    def from_table(self, table: str):
        self._table = table
        return self

    def where(self, condition: str, *params):
        self._conditions.append(condition)       # 如 "age >= ?"
        self._params.extend(params)
        return self

    def order_by(self, column: str, desc: bool = False):
        self._order.append(f"{column} {'DESC' if desc else 'ASC'}")
        return self

    def limit(self, n: int):
        if n <= 0:
            raise ValueError("limit 必须为正数")
        self._limit = n
        return self

    def build(self) -> tuple[str, list]:
        if not self._table:
            raise ValueError("必须指定表名")
        sql = f"SELECT {', '.join(self._columns)} FROM {self._table}"
        if self._conditions:
            sql += " WHERE " + " AND ".join(self._conditions)
        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)
        if self._limit:
            sql += f" LIMIT {self._limit}"
        return sql, list(self._params)


# ---- 链式构建 ----
sql, params = (
    QueryBuilder()
    .select("id", "name", "score")
    .from_table("student")
    .where("score >= ?", 60)
    .where("class_id = ?", 1)
    .order_by("score", desc=True)
    .limit(10)
    .build()
)
print("SQL：", sql)
print("参数：", params)

# ---- 不同“配方”复用同一个建造者 ----
base = QueryBuilder().from_table("orders")
q1, p1 = base.where("status = ?", "paid").build()
q2, p2 = base.where("amount > ?", 1000).order_by("created_at", desc=True).build()
print("\n简单查询：", q1, p1)
print("大额查询：", q2, p2)

# ---- 校验：缺表名直接报错 ----
try:
    QueryBuilder().select("id").build()
except ValueError as exc:
    print("\n建造校验：", exc)

# ===== 练习题 =====
# 1. 给 QueryBuilder 增加 group_by / having。
# 2. 用建造者实现 HTTP 请求构造器（method/url/headers/body/timeout）。
# 3. 思考：为什么 where 的“条件字符串”可以拼，而“值”必须走参数？
