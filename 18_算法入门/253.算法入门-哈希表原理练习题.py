# ===== 第253课：算法入门-哈希表原理 =====
# 知识点：
#   - 哈希表：key 经哈希函数映射到桶下标，平均 O(1) 查询
#   - 冲突：不同 key 落进同一个桶 → 拉链法（桶里存列表）
#   - dict/set 的底层就是哈希表：key 必须可哈希（不可变）
#   - hash 与 == 的约定：两个对象 == 相等，hash 必须相同


def simple_hash(key, buckets=8):
    """演示用哈希函数：字符编码求和取模。"""
    return sum(ord(ch) for ch in str(key)) % buckets


class SimpleHashMap:
    """拉链法哈希表：每个桶是一个 (key, value) 列表。"""

    def __init__(self, buckets=8):
        self.buckets = [[] for _ in range(buckets)]

    def _bucket_of(self, key):
        return self.buckets[simple_hash(key, len(self.buckets))]

    def put(self, key, value):
        bucket = self._bucket_of(key)
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)     # 同 key 覆盖旧值
                return
        bucket.append((key, value))

    def get(self, key, default=None):
        for k, v in self._bucket_of(key):
            if k == key:
                return v
        return default

    def __repr__(self):
        return repr(self.buckets)


m = SimpleHashMap()
m.put("name", "小明")
m.put("age", 15)
m.put("name", "小红")       # 同 key 覆盖
print(m.get("name"), m.get("age"), m.get("city", "无"))

# 冲突演示：三个 key 落进同一个桶
m2 = SimpleHashMap(buckets=4)
for k in ("ab", "ba", "a"):
    print(f"hash({k}) % 4 = {simple_hash(k, 4)}")
    m2.put(k, 1)
print("内部结构（同一个桶里挂了多条）：", m2)

# 内置类型的可哈希性
print(hash("abc") == hash("abc"), hash((1, 2)) == hash((1, 2)))
try:
    hash([1, 2])
except TypeError as exc:
    print("列表不可哈希：", exc)

# 实用结论：dict 查找 O(1)，list 查找 O(n) —— 大数据量用 set/dict 判重
import time

big_list = list(range(200_000))
big_set = set(big_list)
target = 199_999

start = time.perf_counter()
print("list 查找：", target in big_list, f"{time.perf_counter() - start:.4f}s")
start = time.perf_counter()
print("set  查找：", target in big_set, f"{time.perf_counter() - start:.6f}s")

# ===== 练习题 =====
# 1. 给 SimpleHashMap 增加 delete(key) 方法。
# 2. 观察 simple_hash("ab") 与 simple_hash("ba")，解释冲突是怎么发生的。
# 3. 用 set 重写第196课/248课里的 has_duplicate，对比 O(n²) 的差距。
# 4. 思考：为什么 dict 的 key 必须不可变，value 却无所谓？
