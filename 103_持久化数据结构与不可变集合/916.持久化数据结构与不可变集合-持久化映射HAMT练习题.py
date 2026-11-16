# ===== 第916课：持久化数据结构与不可变集合-持久化映射（HAMT） =====
# 知识点：
#   - 持久化映射：dict 的不可变版 —— assoc 返回新映射，旧映射不变
#   - HAMT（Hash Array Mapped Trie）：按 key 哈希逐层分支的树
#   - 本课实现简化版：每层取哈希的 5 位做分支（32 叉），同哈希碰撞存节点表
#   - 更新 = 路径复制：只复制从根到叶的 O(log₃₂ n) 个节点，其余共享
#   - Clojure/Scala 的核心 Map、JavaScript 的 Immutable.js 都基于此
# 依赖：无（标准库）
import time


_BITS = 5
_MASK = (1 << _BITS) - 1


class _Node:
    __slots__ = ("entries", "children")

    def __init__(self):
        self.entries = {}                # key -> value（节点直接存放）
        self.children = {}               # 分支索引 -> 子节点

    def copy(self):
        node = _Node()
        node.entries = dict(self.entries)
        node.children = dict(self.children)
        return node


class HAMT:
    """持久化哈希映射。assoc 返回新映射；旧映射保持不变。"""

    def __init__(self, root=None, size=0):
        self._root = root if root is not None else _Node()
        self._size = size

    def _idx(self, key_hash, level):
        return (key_hash >> (level * _BITS)) & _MASK

    def get(self, key, default=None):
        h = hash(key)
        node, level = self._root, 0
        while True:
            if key in node.entries:
                return node.entries[key]
            idx = self._idx(h, level)
            if idx in node.children:
                node, level = node.children[idx], level + 1
            else:
                return default

    def assoc(self, key, value):
        """返回设置了 key=value 的新映射（路径复制）。"""
        new_root, added = self._insert(self._root, key, value, hash(key), 0)
        return HAMT(new_root, self._size + (1 if added else 0))

    def _insert(self, node, key, value, h, level):
        node_new = node.copy()
        if key in node.entries:                     # 覆盖已有键
            node_new.entries[key] = value
            return node_new, False
        idx = self._idx(h, level)
        if idx in node.children:                    # 沿既有分支继续向下
            child_new, added = self._insert(node.children[idx], key, value,
                                             h, level + 1)
            node_new.children[idx] = child_new
            return node_new, added
        node_new.entries[key] = value               # 该分支为空：直接存放
        return node_new, True

    def size(self):
        return self._size

    def keys(self):
        out = []

        def walk(node):
            out.extend(node.entries)
            for child in node.children.values():
                walk(child)

        walk(self._root)
        return sorted(out, key=repr)


def collect_node_ids(root):
    seen = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        stack.extend(node.children.values())
    return seen


print("== 基本操作 ==")
m0 = HAMT()
m1 = m0.assoc("apple", 3)
m2 = m1.assoc("banana", 7)
m3 = m2.assoc("apple", 9)                     # 覆盖：不增加 size
print(f"  m3.get('apple') = {m3.get('apple')}, get('banana') = {m3.get('banana')}")
print(f"  m1.get('apple') = {m1.get('apple')}   （旧版本完全不受影响）")
print(f"  sizes: m0={m0.size()}, m1={m1.size()}, m2={m2.size()}, m3={m3.size()}")

print("\n== 路径复制：更新只动一条路径 ==")
m_big = HAMT()
for i in range(1000):
    m_big = m_big.assoc(f"key{i}", i)
before = collect_node_ids(m_big._root)
m_upd = m_big.assoc("key500", "新值")
after = collect_node_ids(m_upd._root)
shared = len(before & after)
print(f"  1000 键的映射共 {len(before)} 个节点")
print(f"  更新 1 个键后新树节点 {len(after)} 个，与旧树共享 {shared} 个")
print(f"  共享率 = {shared / len(after):.1%} —— 新建节点只是根到目标的一条路径")

print("\n== 时间旅行：多版本同时可用 ==")
v1 = m_big
v2 = v1.assoc("key500", "版本2")
v3 = v1.assoc("key500", "版本3")              # 从同一 v1 分叉
print(f"  v2.get('key500') = {v2.get('key500')!r}")
print(f"  v3.get('key500') = {v3.get('key500')!r}")
print(f"  v1.get('key500') = {v1.get('key500')!r}   （三个版本并存）")
print(f"  v2/v3 分叉前节点共享 = "
      f"{len(collect_node_ids(v2._root) & collect_node_ids(v3._root))}")

print("\n== 性能对照：get 成本 ==")
plain = {f"key{i}": i for i in range(1000)}
t0 = time.perf_counter()
for _ in range(200):
    for i in range(0, 1000, 100):
        plain.get(f"key{i}")
t_dict = time.perf_counter() - t0
t0 = time.perf_counter()
for _ in range(200):
    for i in range(0, 1000, 100):
        m_big.get(f"key{i}")
t_hamt = time.perf_counter() - t0
print(f"  dict 10000 次 get:  {t_dict * 1000:.1f} ms")
print(f"  HAMT 10000 次 get: {t_hamt * 1000:.1f} ms（指针追踪开销，约 "
      f"{t_hamt / max(t_dict, 1e-9):.0f} 倍）")
print("  付出常数倍的读代价，换来 O(1) 快照与不可变保证 —— 工程上常值得")

print("\n== 与 dict.copy() 的对比 ==")
t0 = time.perf_counter()
for _ in range(200):
    snapshot = dict(plain)                    # O(n) 复制
t_copy = time.perf_counter() - t0
t0 = time.perf_counter()
snap = m_big.assoc("key500", 0)               # O(log₃₂ n) 路径复制
t_assoc = time.perf_counter() - t0
print(f"  dict.copy()（1000 键）: {t_copy * 1000:.1f} ms × 200 次")
print(f"  HAMT.assoc（同样产生新版本）: {t_assoc * 1000:.1f} ms")
print("  键越多差距越大：dict.copy 是 O(n)，HAMT 更新是 O(log₃₂ n)")

print("\n== 小结 ==")
for line in (
    "  HAMT = 哈希分桶 + 树形结构 + 路径复制，持久化映射的工业标准",
    "  读慢一点、快照 O(1)、旧版本永生 —— 交换的是可变性的风险",
    "  插入/更新/查找都是 O(log₃₂ n)：100 万键也只有 ~4 层",
    "  917 课：持久化到平衡树 —— 有序映射的持久化版本",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 dissoc(key)（删除键）：路径复制 + 子树收缩（空节点回收）。
# 2. 实现 __iter__ 与 items()，验证遍历结果与 dict 版本一致。
# 3. 实现 transient 模式：批量插入时先在可变副本上累积，最后一次 path-copy。
# 4. 思考：为什么 HAMT 用「哈希路径」而不是「键比较」来分支？与 917 课的
#    平衡树相比各有什么优劣（无序 vs 有序、分支因子）？
