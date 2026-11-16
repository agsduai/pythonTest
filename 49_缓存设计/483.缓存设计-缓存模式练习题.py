# ===== 第483课：缓存设计-缓存模式 =====
# 知识点：
#   - Cache-Aside（旁路缓存）：读时先查缓存，未命中查库并回填；写时改库再删缓存
#   - Write-Through（写穿透）：写库的同时更新缓存，缓存与库强一致
#   - Write-Behind（写回）：先写缓存，异步批量刷库，吞吐高但可能丢数据
#   - 读多写少 → Cache-Aside；写少但要强一致 → Write-Through；高写入吞吐 → Write-Behind
#   - 无论哪种模式，都要处理：过期、穿透、击穿、雪崩（后续课）
#   - 与第421课 LRU 的区别：那课讲“淘汰算法”，本课讲“缓存与数据库的配合”
import copy
import time


class FakeDB:
    def __init__(self):
        self.data = {"p1": {"name": "键盘", "price": 199}}
        self.reads = 0
        self.writes = 0

    def get(self, key):
        self.reads += 1
        return copy.deepcopy(self.data.get(key))

    def set(self, key, value):
        self.writes += 1
        self.data[key] = copy.deepcopy(value)


# ---------------- 1. Cache-Aside ----------------
class CacheAside:

    def __init__(self, db: FakeDB):
        self.db = db
        self.cache = {}
        self.hits = self.misses = 0

    def get(self, key):
        if key in self.cache:
            self.hits += 1
            print(f"    [缓存命中] {key}")
            return copy.deepcopy(self.cache[key])
        self.misses += 1
        print(f"    [缓存未命中] {key} → 查库")
        value = self.db.get(key)
        if value is not None:
            self.cache[key] = copy.deepcopy(value)
        return value

    def update(self, key, value):
        self.db.set(key, value)          # 先写库
        self.cache.pop(key, None)        # 再删缓存（不是更新缓存）
        print(f"    [写库并失效缓存] {key}")


print("== Cache-Aside ==")
db = FakeDB()
ca = CacheAside(db)
ca.get("p1")
ca.get("p1")
ca.get("p1")
print(f"    数据库读取次数：{db.reads}（3 次请求只查了 1 次）")

ca.update("p1", {"name": "键盘", "price": 179})
ca.get("p1")
print(f"    更新后：{ca.cache['p1']}")

# ---------------- 2. Write-Through ----------------
class WriteThrough:

    def __init__(self, db: FakeDB):
        self.db = db
        self.cache = {}

    def get(self, key):
        return self.cache.get(key) or self.db.get(key)

    def update(self, key, value):
        print(f"    [写库 + 同步写缓存] {key}")
        self.db.set(key, value)
        self.cache[key] = copy.deepcopy(value)


print("\n== Write-Through ==")
db2 = FakeDB()
wt = WriteThrough(db2)
wt.update("p1", {"name": "键盘", "price": 189})
print("    缓存与库一致：", wt.cache["p1"] == db2.data["p1"])
print(f"    写次数：库 {db2.writes} / 缓存 1")

# ---------------- 3. Write-Behind ----------------
class WriteBehind:

    def __init__(self, db: FakeDB):
        self.db = db
        self.cache = {}
        self.pending = []

    def update(self, key, value):
        print(f"    [只写缓存，稍后刷库] {key}")
        self.cache[key] = copy.deepcopy(value)
        self.pending.append((key, copy.deepcopy(value)))

    def flush(self):
        for key, value in self.pending:
            self.db.set(key, value)
        print(f"    [批量刷库] {len(self.pending)} 条")
        self.pending.clear()


print("\n== Write-Behind ==")
db3 = FakeDB()
wb = WriteBehind(db3)
for i in range(3):
    wb.update("p1", {"name": "键盘", "price": 199 - i * 10})
print(f"    刷库前：缓存 {wb.cache['p1']['price']}，库 {db3.data['p1']['price']}")
wb.flush()
print(f"    刷库后：库 {db3.data['p1']['price']}，写库次数 {db3.writes}（3 次写合并成 1 次）")

# ---------------- 4. 模式对比 ----------------
print("\n== 模式对比 ==")
rows = [
    ("Cache-Aside", "读多写少", "实现简单、缓存挂了不影响写", "首次读慢、可能短暂不一致"),
    ("Write-Through", "写后要立刻读到", "强一致", "写放大、缓存写失败要处理"),
    ("Write-Behind", "高写入吞吐", "写快、可合并", "宕机可能丢未刷数据"),
]
print(f"  {'模式':<14}{'适用':<12}{'优点':<20}{'代价'}")
for r in rows:
    print(f"  {r[0]:<14}{r[1]:<12}{r[2]:<20}{r[3]}")

# ---- 为什么“更新缓存”不如“删除缓存” ----
print("\n== 为什么写时删缓存而不是改缓存？==")
for item in [
    "并发写：两个请求先后写库，缓存可能被旧值覆盖",
    "计算复杂：缓存值可能是聚合结果，更新时代价高",
    "懒加载：删除后下次读自然回填最新值",
    "例外：读多写极少、缓存值简单时，更新缓存也可接受",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 Cache-Aside 增加命中率统计，跑 100 次随机读。
# 2. 实现“先更新缓存再写库”（错误顺序），模拟写库失败后的脏缓存。
# 3. 给 Write-Behind 增加定时刷库（每 5 秒或 100 条）。
# 4. 思考：三种模式分别适合商品详情、库存、点赞数中的哪一个？
