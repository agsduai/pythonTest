# ===== 第485课：缓存设计-缓存穿透 =====
# 知识点：
#   - 缓存穿透：查询“根本不存在的数据”，缓存永远不命中，请求全打到数据库
#   - 典型来源：恶意扫描（id=-1、超大 id）、业务删除了但缓存没记录
#   - 方案 1：缓存空值（短 TTL），让“不存在”也占一个缓存坑
#   - 方案 2：布隆过滤器（第425课）先挡一层，“一定不存在”直接返回
#   - 方案 3：接口层参数校验（id 必须为正整数）
#   - 注意：空值缓存 TTL 要短，避免数据后来创建了却一直读到空
import hashlib
import time


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class UserDB:
    def __init__(self):
        self.users = {1: {"name": "小明"}, 2: {"name": "小红"}}
        self.calls = 0

    def get(self, uid):
        self.calls += 1
        return self.users.get(uid)


# ---------------- 1. 反面：无空值缓存 ----------------
def get_user_naive(db: UserDB, uid):
    return db.get(uid)             # 不存在也不缓存 → 每次都查库


print("== 无防护：查询不存在的 id ==")
db = UserDB()
for _ in range(50):
    get_user_naive(db, 999)
print(f"  50 次请求 → 数据库调用 {db.calls} 次（全部穿透）")


# ---------------- 2. 缓存空值 ----------------
class NegativeCache:
    def __init__(self, db: UserDB, clock, ttl=5.0):
        self.db = db
        self.clock = clock
        self.ttl = ttl
        self.cache = {}                    # uid -> (value, expire_at)
        self.db_calls = 0

    def get(self, uid):
        item = self.cache.get(uid)
        if item and self.clock() < item[1]:
            return item[0]
        value = self.db.get(uid)
        self.db_calls += 1
        ttl = self.ttl if value is None else 60.0
        self.cache[uid] = (value, self.clock() + ttl)
        return value


print("\n== 缓存空值（TTL=5s）==")
db2 = UserDB()
clock = FakeClock()
nc = NegativeCache(db2, clock)
for _ in range(50):
    nc.get(999)
print(f"  50 次请求 → 数据库调用 {db2.calls} 次（只穿透一次）")

# 数据后来创建了：空值 TTL 到期后能读到
db2.users[999] = {"name": "新用户"}
print("  数据刚创建时读到：", nc.get(999))
clock.advance(6)
print("  空值 TTL 到期后读到：", nc.get(999))

# ---------------- 3. 布隆过滤器前置 ----------------
class SimpleBloom:
    def __init__(self, size=1000, hashes=3):
        self.size = size
        self.hashes = hashes
        self.bits = bytearray(size // 8 + 1)

    def _positions(self, key):
        for seed in range(self.hashes):
            digest = hashlib.sha256(f"{seed}:{key}".encode()).digest()
            yield int.from_bytes(digest[:8], "big") % self.size

    def add(self, key):
        for p in self._positions(key):
            self.bits[p // 8] |= 1 << (p % 8)

    def __contains__(self, key):
        return all(self.bits[p // 8] & (1 << (p % 8)) for p in self._positions(key))


print("\n== 布隆过滤器前置 ==")
db3 = UserDB()
bloom = SimpleBloom()
for uid in db3.users:
    bloom.add(uid)

rejected = 0
for uid in [999, 1000, 1001, 1002, 1003]:
    if uid not in bloom:
        rejected += 1
    else:
        db3.get(uid)
print(f"  5 个不存在的 id：布隆过滤器直接拒绝 {rejected} 个，数据库调用 {db3.calls} 次")

# ---------------- 4. 参数校验 ----------------
print("\n== 参数校验 ==")
def get_user_api(db, uid):
    if not isinstance(uid, int) or uid <= 0:
        return "400：id 必须是正整数"
    return db.get(uid)


print("  id=-1 →", get_user_api(db3, -1))
print("  id='abc' →", get_user_api(db3, "abc"))
print("  id=1 →", get_user_api(db3, 1))

# ---- 三种方案对比 ----
print("\n== 方案对比 ==")
rows = [
    ("缓存空值", "实现简单", "占缓存空间、可能短暂读到空"),
    ("布隆过滤器", "内存极省、拦截率高", "有假阳性、删除麻烦"),
    ("参数校验", "零成本", "只能挡明显非法的请求"),
]
print(f"  {'方案':<12}{'优点':<18}{'代价'}")
for r in rows:
    print(f"  {r[0]:<12}{r[1]:<18}{r[2]}")
print("\n  生产建议：参数校验 + 布隆过滤器 + 空值缓存，三层一起用")

# ===== 练习题 =====
# 1. 给 NegativeCache 增加命中统计，计算 1000 次请求的命中率。
# 2. 模拟“空值缓存 TTL 太长，新用户注册后一直 404”的问题并修复。
# 3. 用第425课的布隆过滤器替换 SimpleBloom，统计假阳性。
# 4. 思考：为什么空值缓存的 TTL 通常比正常值短很多？
