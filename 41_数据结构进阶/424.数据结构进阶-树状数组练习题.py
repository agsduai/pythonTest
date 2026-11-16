# ===== 第424课：数据结构进阶-树状数组 =====
# 知识点：
#   - 树状数组（Fenwick/BIT）：支持“单点修改 + 前缀和查询”都是 O(log n)
#   - 核心技巧：lowbit(i) = i & -i，树节点 i 管理区间 (i-lowbit(i), i]
#   - 查询前缀和：i 不断减去 lowbit；更新：i 不断增加 lowbit
#   - 区间和 = prefix(r) - prefix(l-1)；建树 O(n log n) 或 O(n)
#   - 与第319课 NumPy 的对比：静态数据用 cumsum；频繁更新用树状数组
#   - 应用：实时排行榜、区间统计、逆序对计数


class Fenwick:

    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (n + 1)          # 1-based

    @classmethod
    def from_array(cls, arr: list[int]) -> "Fenwick":
        fw = cls(len(arr))
        for i, v in enumerate(arr):
            fw.add(i, v)
        return fw

    def add(self, index: int, delta: int):
        """把下标 index（0-based）的值增加 delta。"""
        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i                    # 跳到覆盖自己的下一个节点

    def prefix_sum(self, count: int) -> int:
        """前 count 个元素之和（即 [0, count)）。"""
        total = 0
        i = count
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total

    def range_sum(self, left: int, right: int) -> int:
        """闭区间 [left, right] 的和。"""
        return self.prefix_sum(right + 1) - self.prefix_sum(left)


arr = [5, 2, 8, 1, 9, 3]
fw = Fenwick.from_array(arr)
print("原数组：", arr)
print("内部树：", fw.tree)

print("\n== 前缀和 ==")
for i in range(1, len(arr) + 1):
    print(f"  前 {i} 项和 = {fw.prefix_sum(i)}（暴力 {sum(arr[:i])}）")

print("\n== 区间和 ==")
for left, right in [(0, 2), (2, 4), (1, 5)]:
    brute = sum(arr[left:right + 1])
    print(f"  [{left},{right}] = {fw.range_sum(left, right)}（暴力 {brute}）")

# ---- 单点更新后仍正确 ----
print("\n== 单点更新 ==")
fw.add(2, 10)                  # arr[2] 从 8 改成 18
arr[2] += 10
print("  更新后数组：", arr)
print("  区间 [0,3] =", fw.range_sum(0, 3), "（暴力", sum(arr[:4]), "）")
print("  区间 [2,5] =", fw.range_sum(2, 5), "（暴力", sum(arr[2:6]), "）")

# ---- 与暴力对拍：随机更新 + 随机查询 ----
import random
random.seed(42)
n = 20
values = [random.randint(1, 9) for _ in range(n)]
fw2 = Fenwick.from_array(values)
for _ in range(200):
    if random.random() < 0.5:
        idx = random.randrange(n)
        delta = random.randint(-5, 5)
        values[idx] += delta
        fw2.add(idx, delta)
    else:
        l = random.randrange(n)
        r = random.randrange(l, n)
        assert fw2.range_sum(l, r) == sum(values[l:r + 1])
print("\n== 200 次随机操作对拍 ==")
print("  全部通过")

# ---- 复杂度对照 ----
print("\n== 复杂度 ==")
print("  树状数组：更新 O(log n) / 查询 O(log n)")
print("  暴力数组：更新 O(1) / 查询 O(n)")
print("  NumPy cumsum：更新 O(n) / 查询 O(1)")
print("  数据更新频繁且要查区间和 → 树状数组")

# ===== 练习题 =====
# 1. 用树状数组统计“区间内有多少个数 >= x”（提示：按值域建树）。
# 2. 用树状数组求数组的逆序对数量。
# 3. 实现 lower_bound：找前缀和首次 >= target 的下标。
# 4. 思考：什么时候该用线段树而不是树状数组？
