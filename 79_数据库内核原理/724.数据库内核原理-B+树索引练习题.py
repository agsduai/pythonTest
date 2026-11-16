# ===== 第724课：数据库内核原理-B+树索引 =====
# 知识点：
#   - B+树：多路平衡搜索树，所有数据都在叶子，内部节点只存分隔键与子指针
#   - 叶子用双向链表串起来，范围扫描 O(log n + k)，不必回到父节点
#   - 阶数 order：一个节点最多 order 个孩子；插入满了要分裂并向上提升分隔键
#   - 分裂是「自底向上」的；根分裂会让树高 +1（B+树因此始终平衡）
#   - 与二叉搜索树对比：树高极低、每节点一页、磁盘 IO 次数 ≈ 树高
#   - 本课用 Python 对象模拟节点，实现查找/范围查询/插入分裂/删除借位思路
# 依赖：无（标准库）
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field


@dataclass
class Node:
    leaf: bool = True
    keys: list = field(default_factory=list)
    children: list = field(default_factory=list)   # 叶子时存 values
    next: object = None


class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.root = Node(leaf=True)
        self.height = 1
        self.splits = 0

    def _find_leaf(self, key):
        node = self.root
        while not node.leaf:
            i = bisect_right(node.keys, key)
            node = node.children[i]
        return node

    def search(self, key):
        leaf = self._find_leaf(key)
        i = bisect_left(leaf.keys, key)
        if i < len(leaf.keys) and leaf.keys[i] == key:
            return leaf.children[i]
        return None

    def range_query(self, lo, hi):
        """利用叶子链表顺序扫，避免逐键 log n 查找。"""
        node = self._find_leaf(lo)
        out = []
        while node:
            for k, v in zip(node.keys, node.children):
                if k > hi:
                    return out
                if k >= lo:
                    out.append((k, v))
            node = node.next
        return out

    def insert(self, key, value):
        path = []                     # 记录 (父节点, 子节点索引)
        node = self.root
        while not node.leaf:
            i = bisect_right(node.keys, key)
            path.append((node, i))
            node = node.children[i]
        i = bisect_left(node.keys, key)
        if i < len(node.keys) and node.keys[i] == key:
            node.children[i] = value          # 更新
            return
        node.keys.insert(i, key)
        node.children.insert(i, value)
        self._split_if_needed(node, path)

    def _split_if_needed(self, node, path):
        while len(node.keys) > self.order - 1:
            self.splits += 1
            mid = len(node.keys) // 2
            right = Node(leaf=node.leaf)
            if node.leaf:
                right.keys = node.keys[mid:]
                right.children = node.children[mid:]
                node.keys = node.keys[:mid]
                node.children = node.children[:mid]
                right.next = node.next
                node.next = right
                promote = right.keys[0]
            else:
                promote = node.keys[mid]
                right.keys = node.keys[mid + 1:]
                right.children = node.children[mid + 1:]
                node.keys = node.keys[:mid]
                node.children = node.children[:mid + 1]
            if not path:
                new_root = Node(leaf=False, keys=[promote],
                                children=[node, right])
                self.root = new_root
                self.height += 1
                return
            parent, idx = path.pop()
            parent.keys.insert(idx, promote)
            parent.children.insert(idx + 1, right)
            node = parent

    def __repr__(self):
        lines, q = [], [(self.root, 0)]
        while q:
            node, depth = q.pop(0)
            tag = "L" if node.leaf else "I"
            lines.append("  " * depth + f"{tag}{node.keys}")
            if not node.leaf:
                q.extend((c, depth + 1) for c in node.children)
        return "\n".join(lines)


print("== 构建 B+树（order=4）==")
t = BPlusTree(order=4)
for k in (10, 20, 5, 6, 12, 30, 7, 17, 3, 4, 2, 1, 25, 28, 35):
    t.insert(k, f"v{k}")
print(f"  插入 15 个键: 树高={t.height} 分裂次数={t.splits}")
print(t)

print("\n== 点查 ==")
for k in (7, 17, 99, 1):
    print(f"  search({k:>2}) = {t.search(k)!r}")

print("\n== 范围查询（叶子链表）==")
for lo, hi in ((5, 12), (20, 30), (1, 40)):
    got = t.range_query(lo, hi)
    print(f"  [{lo},{hi}]: {len(got)} 条 -> {[k for k, _ in got]}")

print("\n== 全部键有序性 ==")
all_keys = [k for k, _ in t.range_query(-10**9, 10**9)]
print("  ", all_keys)
print("  有序:", all_keys == sorted(all_keys), " 无重复:", len(all_keys) == len(set(all_keys)))

print("\n== 树高与磁盘 IO ==")
for n in (10**3, 10**6, 10**9):
    # order=100 时每节点约 100 路，树高 ≈ log_100(n)
    import math
    h = math.ceil(math.log(n, 100))
    print(f"  {n:>12} 行, order=100 -> 树高≈{h}，点查最多 {h} 次页 IO")
print("  对比二叉搜索树：10^9 行需约 30 层，B+树仅 5 层")

print("\n== 分裂过程追踪（order=3）==")
t2 = BPlusTree(order=3)
for k in (1, 2, 3, 4, 5):
    t2.insert(k, k)
    print(f"  插入 {k} 后（分裂 {t2.splits} 次，高 {t2.height}）")
    print(t2)

print("\n== B 树 vs B+树 ==")
for line in (
    "  B 树 : 内部节点也存数据，命中即可返回，范围扫描需中序遍历",
    "  B+树: 数据全在叶子且链表相连，范围/排序/全表扫描极高效",
    "  数据库索引、文件系统（NTFS/ext4）普遍用 B+树或其变体",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  节点大小 ≈ 一个页，扇出由 (页大小 / 键大小) 决定",
    "  填充因子（如 70%）预留空间，减少插入时的分裂频率",
    "  删除可借位/合并，也可只标墓碑靠后台重整",
    "  聚簇索引叶存整行，二级索引叶存主键（回表）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现删除：先借位兄弟，都不足时合并，并更新父节点分隔键。
# 2. 给叶子节点加 prev 指针，支持逆序范围扫描。
# 3. 模拟「页 IO 计数」，对比 B+树点查与全表扫描的成本。
# 4. 思考：为什么数据库索引不用哈希表做范围查询？
