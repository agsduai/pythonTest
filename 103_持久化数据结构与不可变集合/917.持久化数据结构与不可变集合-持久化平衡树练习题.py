# ===== 第917课：持久化数据结构与不可变集合-持久化平衡树 =====
# 知识点：
#   - 有序映射的持久化版：AVL 树的节点全部不可变，插入走「路径复制」
#   - 节点用元组 (key, value, left, right, height) 表示 —— 天然不可变
#   - 插入/删除后沿路径重建：只有根到插入点的节点是新对象，其余共享
#   - 多版本树并存：从同一版本分叉出不同未来 —— git 分支的数据结构本质
#   - 版本间 diff：中序遍历对比即可找出增删键
# 依赖：无（标准库）


def height(node):
    return node[4] if node is not None else 0


def mk(key, value, left, right):
    """构造新节点（不可变元组），自动更新高度。"""
    return (key, value, left, right,
            1 + max(height(left), height(right)))


def balance(key, value, left, right):
    """AVL 再平衡（只新建涉及的节点）。"""
    hl, hr = height(left), height(right)
    if hl - hr > 1:                                   # 左重
        if height(left[2]) >= height(left[3]):        # LL：右旋
            new_right = mk(key, value, left[3], right)
            return mk(left[0], left[1], left[2], new_right)
        lchild = left[3]                              # LR：先左旋再右旋
        new_left = mk(left[0], left[1], left[2], lchild[2])
        new_right = mk(key, value, lchild[3], right)
        return mk(lchild[0], lchild[1], new_left, new_right)
    if hr - hl > 1:                                   # 右重（镜像）
        if height(right[3]) >= height(right[2]):      # RR：左旋
            new_left = mk(key, value, left, right[2])
            return mk(right[0], right[1], new_left, right[3])
        rchild = right[2]                             # RL
        new_right = mk(right[0], right[1], rchild[3], right[3])
        new_left = mk(key, value, left, rchild[2])
        return mk(rchild[0], rchild[1], new_left, new_right)
    return mk(key, value, left, right)


def insert(node, key, value):
    if node is None:
        return mk(key, value, None, None)
    k, v, l, r, _ = node
    if key == k:
        return mk(key, value, l, r)                   # 覆盖值
    if key < k:
        return balance(k, v, insert(l, key, value), r)
    return balance(k, v, l, insert(r, key, value))


def get(node, key, default=None):
    while node is not None:
        k, v, l, r, _ = node
        if key == k:
            return v
        node = l if key < k else r
    return default


def inorder(node, out=None):
    if out is None:
        out = []
    if node is not None:
        inorder(node[2], out)
        out.append((node[0], node[1]))
        inorder(node[3], out)
    return out


def collect_ids(node, seen=None):
    if seen is None:
        seen = set()
    if node is None or id(node) in seen:
        return seen
    seen.add(id(node))
    collect_ids(node[2], seen)
    collect_ids(node[3], seen)
    return seen


def diff_versions(node_a, node_b):
    """对比两个版本：返回 (新增键, 删除键, 值变化的键)。"""
    a = dict(inorder(node_a))
    b = dict(inorder(node_b))
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return added, removed, changed


def range_query(node, lo, hi, out=None):
    """剪枝式范围查询：只走可能与 [lo,hi] 相交的子树。"""
    if out is None:
        out = []
    if node is None:
        return out
    k, v, l, r, _ = node
    if k > lo:
        range_query(l, lo, hi, out)
    if lo <= k <= hi:
        out.append((k, v))
    if k < hi:
        range_query(r, lo, hi, out)
    return out


def render(node, indent=0, out=None):
    if out is None:
        out = []
    if node is not None:
        render(node[3], indent + 1, out)
        out.append("  " * indent + f"{node[0]}={node[1]} (h{node[4]})")
        render(node[2], indent + 1, out)
    return out


print("== 插入 1..7（会触发旋转）==")
root = None
for k in range(1, 8):
    root = insert(root, k, k * 10)
for line in render(root):
    print("  " + line)
print(f"  中序 = {inorder(root)}（有序 ✓），高度 = {height(root)}")

print("\n== 持久化分叉：git 分支的数据结构本质 ==")
base = root
v2 = insert(base, 8, 80)                      # 分支 1：加 8
v3 = insert(base, 0, 5)                       # 分支 2：加 0
print(f"  base 中序 = {[k for k, _ in inorder(base)]}")
print(f"  v2 中序   = {[k for k, _ in inorder(v2)]}")
print(f"  v3 中序   = {[k for k, _ in inorder(v3)]}")
shared = len(collect_ids(base) & collect_ids(v2))
print(f"  base 节点 {len(collect_ids(base))} 个，v2 共享其中 {shared} 个"
      f"（{shared / len(collect_ids(v2)):.0%} 结构共享）")
print(f"  v2/v3 互不影响: get(v2, 8)={get(v2, 8)}, get(v3, 8)={get(v3, 8)}")

print("\n== 更新路径的复制比例 ==")
big = None
for k in range(500):
    big = insert(big, k, k)
ids_base = collect_ids(big)
after = insert(big, 250, "更新值")
ids_after = collect_ids(after)
print(f"  500 键 AVL 共 {len(ids_base)} 节点；更新 1 键后 {len(ids_after)} 节点")
print(f"  共享 {len(ids_base & ids_after)} 个 -> 共享率 {len(ids_base & ids_after) / len(ids_after):.1%}")
print("  只有根到更新点（AVL 旋转涉及的兄弟）被重建 —— O(log n) 个新节点")

print("\n== 版本 diff ==")
added, removed, changed = diff_versions(base, v2)
print(f"  base -> v2: 新增 {added}, 删除 {removed}, 修改 {changed}")
added2, removed2, changed2 = diff_versions(v2, v3)
print(f"  v2 -> v3:   新增 {added2}, 删除 {removed2}, 修改 {changed2}")
print("  两个版本的中序对比即可得到精确变更集")

print("\n== 范围查询 ==")
print(f"  [30, 50] 内的键: {range_query(big, 30, 50)}")
print("  剪枝：与范围无交集的子树整棵跳过 —— 有序结构的红利")

print("\n== 覆盖值的高共享 ==")
same = insert(big, 250, 2500)                 # 覆盖已有键的值
print(f"  覆盖 1 个键的值: 新节点 {len(collect_ids(same)) - len(ids_base & collect_ids(same))} 个"
      f"，共享率 {len(collect_ids(same) & ids_base) / len(collect_ids(same)):.1%}")

print("\n== 小结 ==")
for line in (
    "  持久化 AVL = 不可变元组节点 + 递归重建 —— 插入天然返回新根",
    "  路径复制 + 旋转只影响 O(log n) 节点，共享率 >99%",
    "  多版本并存让『分支』像 git 一样便宜：分叉就是再插一次",
    "  有序性带来范围查询与 diff 能力 —— 比 HAMT 多出的能力",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 delete(key)：路径复制的持久化删除（二合一旋转处理），验证与
#    可变 AVL 的中序一致。
# 2. 实现两个版本的「最小公共祖先」树：找出 v2/v3 分叉前的共享子树根。
# 3. 给节点加子树大小字段，实现持久化的 rank/select（第 k 小）。
# 4. 思考：持久化 AVL 与『copy-on-write B 树』（数据库用）的差异？页粒度
#    共享为什么对磁盘更友好？
