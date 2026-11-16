# ===== 第918课：持久化数据结构与不可变集合-Rope字符串 =====
# 知识点：
#   - Rope：把长文本组织成一棵树，叶子是短片段，内部节点记录左子树长度
#   - 拼接 = 造一个新根（O(1)）；按位置切分 = 沿权重下降（O(log n)）
#   - 对比：str 拼接/切分都要整串复制 O(n) —— 长文本编辑的痛点
#   - 应用：文本编辑器（VS Code 的 piece table 同族）、日志、DNA 序列
#   - 权重不变式：内部节点 weight = 左子树总长度
# 依赖：无（标准库）
import time


class Rope:
    __slots__ = ("weight", "left", "right", "text")

    def __init__(self, text=""):
        self.text = text
        self.weight = len(text)
        self.left = None
        self.right = None

    def length(self):
        if self.left is None:                      # 叶子：text 直接可读
            return len(self.text)
        return self.weight + self.right.length()

    def index(self, i):
        """第 i 个字符（0 起）。O(log n)。"""
        if self.left is None:
            return self.text[i]
        if i < self.weight:
            return self.left.index(i)
        return self.right.index(i - self.weight)

    def split(self, i):
        """在第 i 个字符处切分 -> (前半, 后半)，两棵新树共享旧结构。"""
        if self.left is None:
            return Rope(self.text[:i]), Rope(self.text[i:])
        if i <= self.weight:
            l1, l2 = self.left.split(i)
            return l1, rope_concat(l2, self.right)
        r1, r2 = self.right.split(i - self.weight)
        return rope_concat(self.left, r1), r2


def rope_concat(a, b):
    """O(1) 拼接：只造一个新根，子树全部共享。"""
    if a.length() == 0:
        return b
    if b.length() == 0:
        return a
    node = Rope("")
    node.weight = a.length()
    node.left, node.right = a, b
    return node


def rope_from_text(text, leaf_size=2000):
    """把长文本构建成平衡 rope：叶子 ≤ leaf_size（关键工程细节！）。"""
    if not text:
        return Rope("")
    level = [Rope(text[i:i + leaf_size])
             for i in range(0, len(text), leaf_size)]
    while len(level) > 1:                       # 两两归并成平衡树
        nxt = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                nxt.append(rope_concat(level[i], level[i + 1]))
            else:
                nxt.append(level[i])
        level = nxt
    return level[0]


def rope_insert(rope, i, text):
    """在位置 i 插入文本 = 切分 + 两次拼接。"""
    left, right = rope.split(i)
    return rope_concat(rope_concat(left, Rope(text)), right)


def rope_depth(rope):
    if rope.left is None:
        return 1
    return 1 + max(rope_depth(rope.left), rope_depth(rope.right))


def rope_to_str(rope):
    if rope.left is None:
        return rope.text
    return rope_to_str(rope.left) + rope_to_str(rope.right)


def collect_leaves(rope, seen=None):
    if seen is None:
        seen = set()
    seen.add(id(rope))
    if rope.left is None:
        return seen
    collect_leaves(rope.left, seen)
    collect_leaves(rope.right, seen)
    return seen


print("== 构建与基本操作 ==")
r = Rope("hello, ")
r = rope_concat(r, Rope("brave "))
r = rope_concat(r, Rope("new world"))
print(f"  长度 = {r.length()}, 深度 = {rope_depth(r)}")
print(f"  内容 = {rope_to_str(r)!r}")
print(f"  index(7) = {r.index(7)!r}, index(17) = {r.index(17)!r}")

print("\n== 切分与插入 ==")
left, right = r.split(7)
print(f"  在 7 处切分: 左 = {rope_to_str(left)!r}  右 = {rope_to_str(right)!r}")
r2 = rope_insert(r, 7, "big ")
print(f"  在 7 处插入 'big ': {rope_to_str(r2)!r}")
print(f"  原串不变: {rope_to_str(r)!r}   （切分/插入都返回新树，旧树完好）")
print(f"  新旧树的共享叶子数 = {len(collect_leaves(r) & collect_leaves(r2))}"
      f"/{len(collect_leaves(r2))}（只新增了少量节点）")

print("\n== 性能对照：高频切分（rope 的主战场）==")
piece = "".join("abcdefghij" for _ in range(200000))    # 2MB 文本
big_str = piece
big_rope = rope_from_text(piece)               # 叶子 2000 字符的平衡 rope
splits = [(i * 6247) % 2000000 for i in range(300)]
print(f"  构建后 rope 深度 = {rope_depth(big_rope)}（叶子 ≤ 2000 字符）")

t0 = time.perf_counter()
for pos in splits:                                     # str 切分：整串复制
    _ = big_str[:pos], big_str[pos:]
t_str = time.perf_counter() - t0

t0 = time.perf_counter()
for pos in splits:                                     # rope 切分：O(log n)
    big_rope.split(pos)
t_rope = time.perf_counter() - t0

print(f"  2MB 文本切分 300 次:")
print(f"    str 切片: {t_str * 1000:.1f} ms（每次 O(n) 拷贝，共 ~600MB 数据移动）")
print(f"    rope 切分: {t_rope * 1000:.1f} ms（每次 O(log n)，只建少量节点）")
print(f"    加速比 ≈ {t_str / max(t_rope, 1e-9):.0f} 倍")
print("  注意：100KB 小文本上 str 的 memcpy 反而更快 —— rope 在大文本上才回本")

print("\n== 纯索引的反向教训 ==")
t0 = time.perf_counter()
for pos in splits:
    _ = big_str[pos]                                   # str 索引 O(1)
t_str2 = time.perf_counter() - t0
t0 = time.perf_counter()
for pos in splits:
    _ = big_rope.index(pos % 2000000)                  # rope 索引 O(log n)
t_rope2 = time.perf_counter() - t0
print(f"  300 次随机索引: str {t_str2 * 1000:.2f} ms vs rope {t_rope2 * 1000:.2f} ms")
print("  纯读场景 str 完胜 —— 数据结构要匹配工作负载，没有银弹")

print("\n== 小结 ==")
for line in (
    "  rope 把『编辑长文本』从 O(n) 拷贝变成 O(log n) 结构操作",
    "  拼接 O(1)、切分/插入 O(log n)、索引 O(log n) —— 各操作按场景选型",
    "  rope 天然持久化：切分/插入返回新树，旧文本仍可读",
    "  919 课：另一个函数式经典 —— zipper（树的『光标』）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 rope 的平衡化（收集所有叶子重建平衡树），在深度 > 2·log n 时自动触发。
# 2. 实现「删除区间 [i, j)」= 两次切分 + 拼接，并统计新旧树共享率。
# 3. 用 rope 实现一个支持撤销的迷你文本编辑器（插入/删除/undo）。
# 4. 思考：VS Code 为什么用 piece table 而不是 rope？两者在「追加为主」的
#    编辑负载下各有什么优势？
