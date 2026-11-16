# ===== 第488课：缓存设计-缓存一致性 =====
# 知识点：
#   - 缓存与数据库是两份数据，更新时必然存在“不一致窗口”
#   - 错误顺序：先更新缓存再写库 —— 写库失败会留下脏缓存
#   - 推荐顺序：先写库，再删除缓存（Cache-Aside 标准做法）
#   - 仍有竞态：读请求在写之前查到旧值，写之后才回填缓存 → 旧值长期驻留
#   - 缓解：延迟双删、版本号/时间戳、订阅 binlog 异步失效
#   - 目标不是“绝对强一致”，而是“最终一致 + 窗口可控”
import time


class FakeDB:
    def __init__(self, value):
        self.value = value
        self.writes = 0

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        self.writes += 1


# ---------------- 1. 错误顺序：先缓存后库 ----------------
print("== 错误顺序：先更新缓存，再写库（写库失败）==")
db = FakeDB("v1")
cache = {"k": "v1"}
cache["k"] = "v2"                 # 先改缓存
print("  写库前：缓存", cache["k"], "| 库", db.value)
print("  假设此时写库失败（抛异常），缓存已经是 v2 —— 脏缓存")
print("  修复：写库成功后才删除缓存，失败则缓存不动")

# ---------------- 2. 正确顺序：先库后删缓存 ----------------
print("\n== 正确顺序：写库 → 删除缓存 ==")
db2 = FakeDB("v1")
cache2 = {"k": "v1"}


def update_good(db, cache, value):
    db.set(value)
    cache.pop("k", None)          # 删缓存，下次读回填
    print(f"    写库={db.value}，缓存已删除")


update_good(db2, cache2, "v2")
print("  读请求：缓存未命中 → 查库 →", db2.get(), "→ 回填")

# ---------------- 3. 竞态：读-写交错导致旧值回填 ----------------
print("\n== 竞态：旧值回填 ==")
db3 = FakeDB("v1")
cache3 = {}


def read_phase1():
    """读请求发现未命中，查库拿到旧值（还没写缓存）"""
    value = db3.get()
    print(f"    读线程：缓存未命中，查到 {value}")
    return value


def write_phase(db, cache, new_value):
    db.set(new_value)
    cache.pop("k", None)
    print(f"    写线程：写库 {new_value}，删除缓存")


def read_phase2(value):
    cache3["k"] = value
    print(f"    读线程：把 {value} 写回缓存（旧值！）")


old = read_phase1()               # 读线程先查到 v1
write_phase(db3, cache3, "v2")    # 写线程更新为 v2
read_phase2(old)                  # 读线程把 v1 回填
print(f"  结果：库={db3.value}，缓存={cache3['k']} → 不一致")

# ---------------- 4. 延迟双删 ----------------
print("\n== 延迟双删 ==")
db4 = FakeDB("v1")
cache4 = {"k": "v1"}


def update_double_delete(db, cache, value, delay=0.01):
    db.set(value)
    cache.pop("k", None)
    print(f"    第一次删缓存（写库后立即）")
    # 模拟读线程在窗口内把旧值回填
    time.sleep(delay)
    cache.pop("k", None)
    print(f"    第二次删缓存（延迟 {delay * 1000:.0f}ms，清掉竞态回填的旧值）")


# 模拟竞态：写之后读线程回填旧值，然后第二次删除
db4.set("v1")
cache4["k"] = "v1"

db4.set("v2")
cache4.pop("k", None)
cache4["k"] = "v1"                # 读线程回填旧值
cache4.pop("k", None)             # 第二次删除
print(f"  最终：库={db4.value}，缓存={'不存在（下次读回填 v2）' if 'k' not in cache4 else cache4['k']}")

# ---------------- 5. 版本号方案 ----------------
print("\n== 版本号：只接受更新的值回填 ==")
class VersionedCache:
    def __init__(self):
        self.value = None
        self.version = -1

    def set_if_newer(self, value, version):
        if version > self.version:
            self.value, self.version = value, version
            return True
        return False


vc = VersionedCache()
print("  旧读回填 v1(v=1)：", vc.set_if_newer("v1", 1))
print("  写线程写入 v2(v=2)：", vc.set_if_newer("v2", 2))
print("  旧读再回填 v1(v=1)：", vc.set_if_newer("v1", 1), "→ 被拒绝")
print(f"  最终缓存：{vc.value}（v{vc.version}）")

# ---------------- 6. 一致性策略对比 ----------------
print("\n== 策略对比 ==")
rows = [
    ("先库后删缓存", "简单、绝大多数场景够用", "仍有小概率旧值回填"),
    ("延迟双删", "实现成本低", "延迟时间难精确；二次删除也可能失败"),
    ("版本号/时间戳", "能拒绝旧值覆盖", "需要数据带版本，改造较大"),
    ("binlog 订阅", "异步失效、解耦", "链路长、有延迟，需要额外组件"),
]
print(f"  {'策略':<14}{'优点':<22}{'代价'}")
for r in rows:
    print(f"  {r[0]:<14}{r[1]:<22}{r[2]}")

# ---- 结论 ----
print("\n== 结论 ==")
for item in [
    "缓存一致性是“最终一致”，不要追求绝对强一致",
    "先写库再删缓存是底线；不要先删缓存再写库",
    "读多写少 + 允许秒级延迟 → 先库后删 + TTL 兜底",
    "金融/库存等强一致场景 → 缓存只读、以库为准，或加版本号",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 模拟“先删缓存再写库”的竞态，展示旧值长期驻留。
# 2. 给延迟双删加异常处理：第二次删除失败时记录告警。
# 3. 用时间戳替代版本号实现 set_if_newer。
# 4. 思考：为什么“删除缓存”比“更新缓存”更不容易出错？
