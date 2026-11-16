# ===== 第421课：数据结构进阶-LRU缓存 =====
# 知识点：
#   - LRU（最近最少使用）：容量满时淘汰“最久没被访问”的那条
#   - 两个动作都要 O(1)：get 提升优先级、put 插入/淘汰
#   - 实现组合：哈希表（定位）+ 双向链表（维护顺序）
#   - Python 捷径：collections.OrderedDict（move_to_end / popitem(last=False)）
#   - 应用：浏览器缓存、数据库查询缓存、函数结果缓存（第236课）
from collections import OrderedDict


class LRUCacheOrdered:
    """OrderedDict 版：左端最旧，右端最新。"""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity 必须为正")
        self.capacity = capacity
        self.data: OrderedDict[str, object] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key not in self.data:
            self.misses += 1
            return None
        self.hits += 1
        self.data.move_to_end(key)          # 提到最新
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            self.data.move_to_end(key)
            return
        if len(self.data) >= self.capacity:
            evicted, _ = self.data.popitem(last=False)   # 淘汰最旧
            print(f"    淘汰 {evicted}")
        self.data[key] = value

    def keys(self):
        return list(self.data)


# ---------------- 手写双向链表版（理解原理） ----------------
class Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.map: dict = {}
        self.head = Node()          # 哨兵：head.next 是最新
        self.tail = Node()          # 哨兵：tail.prev 是最旧
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _add_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return None
        self._remove(node)
        self._add_front(node)
        return node.value

    def put(self, key, value):
        if key in self.map:
            node = self.map[key]
            node.value = value
            self._remove(node)
            self._add_front(node)
            return
        if len(self.map) >= self.capacity:
            oldest = self.tail.prev
            self._remove(oldest)
            del self.map[oldest.key]
            print(f"    淘汰 {oldest.key}")
        node = Node(key, value)
        self.map[key] = node
        self._add_front(node)

    def keys(self):
        result, cur = [], self.head.next
        while cur is not self.tail:
            result.append(cur.key)
            cur = cur.next
        return result


def demo(cache):
    print(f"== {type(cache).__name__}（容量 3）==")
    for k, v in [("a", 1), ("b", 2), ("c", 3)]:
        cache.put(k, v)
    print("  当前：", cache.keys())
    print("  get('a') =", cache.get("a"), "→ a 变成最新")
    cache.put("d", 4)               # 淘汰最久未用的 b
    print("  插入 d 后：", cache.keys())
    print("  get('b') =", cache.get("b"), "（已淘汰）")
    if hasattr(cache, "hits"):
        print(f"  命中 {cache.hits} 次 / 未命中 {cache.misses} 次")


demo(LRUCacheOrdered(3))
print()
demo(LRUCache(3))

# ---- 实战：给“慢查询”加缓存 ----
print("\n== 慢函数缓存 ==")
import time

cache = LRUCacheOrdered(2)
calls = [0]

def slow_square(n):
    calls[0] += 1
    time.sleep(0.01)
    return n * n

def cached_square(n):
    value = cache.get(n)
    if value is None:
        value = slow_square(n)
        cache.put(n, value)
    return value

for n in (4, 5, 4, 6, 5):
    start = time.perf_counter()
    result = cached_square(n)
    print(f"  n={n} → {result}（{time.perf_counter() - start:.3f}s）")
print(f"  实际计算次数：{calls[0]} / 请求 5 次")

# ===== 练习题 =====
# 1. 给手写版加命中/未命中计数，和 OrderedDict 版对拍。
# 2. 实现 TTL 缓存：过期条目自动失效（提示：存 (value, expire_at)）。
# 3. 用 LRU 缓存第387课的编辑距离结果。
# 4. 思考：LRU 在“周期性批量扫描”场景为什么命中率会骤降？
