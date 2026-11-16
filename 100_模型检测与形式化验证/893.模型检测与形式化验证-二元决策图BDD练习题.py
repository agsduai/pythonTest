# ===== 第893课：模型检测与形式化验证-二元决策图BDD =====
# 知识点：
#   - BDD：布尔函数的规范有向无环图 —— 每个函数对应唯一的既约图
#   - 节点 = 变量 + 低/高分支；终端 0/1；香农展开逐变量分解
#   - 构建时合并同构子图（unique 表）+ 删除冗余节点（low == high）-> 既约
#   - 规范性带来强能力：等价检查 = 根节点相同；计数/枚举高效
#   - 变量顺序决定图大小：顺序差可导致指数级爆炸
# 依赖：无（标准库）
from itertools import product as iproduct


class BDD:
    """既约有序二元决策图（ROBDD）。节点 = (var_index, low, high)，终端 0/1。"""

    def __init__(self):
        self.unique = {}                      # (var, low, high) -> node_id
        self.nodes = {0: ("TERMINAL", 0), 1: ("TERMINAL", 1)}

    def mk(self, var, low, high):
        if low == high:
            return low                        # 冗余节点删除
        key = (var, low, high)
        if key not in self.unique:
            self.unique[key] = len(self.nodes)
            self.nodes[len(self.nodes)] = key
        return self.unique[key]

    def build(self, func, order):
        """func: dict{赋值元组: 0/1}，order: 变量下标顺序。递归香农展开。"""
        memo = {}

        def rec(idx, restriction):
            key = idx
            if key in memo:
                return memo[key]
            if idx == len(order):
                values = tuple(restriction.get(v, 0) for v in range(max(order) + 1))
                node = 1 if func[values] else 0
            else:
                var = order[idx]
                low = rec(idx + 1, {**restriction, var: 0})
                high = rec(idx + 1, {**restriction, var: 1})
                node = self.mk(var, low, high)
            memo[key] = node
            return node

        return rec(0, {})

    def size(self, root):
        seen = set()
        stack = [root]
        while stack:
            node = stack.pop()
            if node in (0, 1) or node in seen:
                continue
            seen.add(node)
            var, low, high = self.nodes[node]
            stack.extend((low, high))
        return len(seen)

    def count_solutions(self, root, order):
        """从根计数满足赋值数（考虑跳过的变量：系数 2^跳过数）。"""
        memo = {}
        nvars = max(order) + 1

        def rec(node, idx):
            key = (node, idx)
            if key in memo:
                return memo[key]
            if node == 0:
                result = 0
            elif node == 1:
                result = 2 ** (nvars - idx)     # 剩余变量自由
            else:
                var, low, high = self.nodes[node]
                nxt = idx + 1
                while nxt < len(order) and order[nxt] != var:
                    nxt += 1
                result = rec(low, nxt) + rec(high, nxt)
            memo[key] = result
            return result

        return rec(root, 0)

    def dump(self, root):
        lines = []
        seen = set()
        stack = [root]
        while stack:
            node = stack.pop()
            if node in (0, 1) or node in seen:
                continue
            seen.add(node)
            var, low, high = self.nodes[node]
            lines.append(f"  节点{node}: x{var} -> 低{low} / 高{high}")
            stack.extend((low, high))
        return sorted(lines)


print("== 构建第一个 BDD：f = x1 ∧ x2 ==")
bdd = BDD()
order = [0, 1]
table = {}
for combo in iproduct((0, 1), repeat=2):
    table[combo] = combo[0] & combo[1]
root_and = bdd.build(table, order)
print(f"  根节点 = {root_and}, 节点数 = {bdd.size(root_and)}")
for line in bdd.dump(root_and):
    print(line)
print(f"  满足赋值数 = {bdd.count_solutions(root_and, order)}（4 个赋值中 1 个为真）")

print("\n== 规范性：等价函数 -> 相同根节点 ==")
table2 = {}
for combo in iproduct((0, 1), repeat=2):
    a, b = combo
    table2[combo] = (a & b) | (a & b)          # 冗余写法但同一函数
root_same = BDD().build(table2, order)
print(f"  (x1∧x2) 与 (x1∧x2)∨(x1∧x2) 的根: {root_and} vs {root_same} -> "
      f"等价: {root_and == root_same}")
table_or = {}
for combo in iproduct((0, 1), repeat=2):
    table_or[combo] = combo[0] | combo[1]
root_or = bdd.build(table_or, order)
print(f"  (x1∧x2) vs (x1∨x2) 的根: {root_and} vs {root_or} -> 等价: {root_and == root_or}")

print("\n== 变量顺序对大小的影响 ==")
# f = (x0∧x1) ∨ (x2∧x3)
table_f = {}
for combo in iproduct((0, 1), repeat=4):
    x0, x1, x2, x3 = combo
    table_f[combo] = int((x0 & x1) | (x2 & x3))
for label, order in (("顺序 [0,1,2,3]", [0, 1, 2, 3]),
                     ("交错 [0,2,1,3]", [0, 2, 1, 3])):
    b = BDD()
    root = b.build(table_f, order)
    print(f"  {label}: 节点数 = {b.size(root)}, 满足数 = {b.count_solutions(root, order)}")
print("  同一函数在不同变量顺序下大小不同 —— 顺序是 BDD 工程的核心问题")

print("\n== 更实际的函数：奇偶校验 ==")
table_par = {}
for combo in iproduct((0, 1), repeat=4):
    table_par[combo] = sum(combo) % 2
b = BDD()
root_par = b.build(table_par, [0, 1, 2, 3])
print(f"  4 位奇偶函数: 节点数 = {b.size(root_par)}, 满足数 = {b.count_solutions(root_par, [0,1,2,3])}（8 个偶/8 个奇）")
root_xor2 = b.build({(a, b2): a ^ b2 for a in (0, 1) for b2 in (0, 1)}, [0, 1])
print(f"  2 位异或: 节点数 = {b.size(root_xor2)}")
print("  奇偶函数的 BDD 是『链状』的 —— 这正是硬件奇偶校验电路的形状")

print("\n== BDD 的等价检查应用 ==")


def half_adder_sum(a, b):
    return a ^ b


table_ha = {}
for combo in iproduct((0, 1), repeat=2):
    table_ha[combo] = half_adder_sum(*combo)
root_ha = b.build(table_ha, [0, 1])
print(f"  半加器和 (a^b) 与 x1∨x2 的根比较: {root_ha} vs {root_or} -> 等价 {root_ha == root_or}")
print(f"  半加器和 (a^b) 与 2位异或的根比较: {root_ha} vs {root_xor2} -> 等价 {root_ha == root_xor2}")
print("  电路验证的核心操作 = BDD 根节点比较 —— O(1)！")

print("\n== 小结 ==")
for line in (
    "  BDD = 布尔函数的规范压缩：合并等价子图、剪除冗余节点",
    "  规范性使等价检查、可满足计数变成图操作",
    "  变量顺序敏感：最坏指数级，好顺序下多项式（如奇偶、加法器）",
    "  894 课：BDD 管布尔，SMT 管算术 —— 一起处理混合约束",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 BDD 的 apply 操作（ITE 算子直接在图上算 AND/OR），无需真值表。
# 2. 用 BDD 验证「全加器 = 半加器组合」的电路等价。
# 3. 尝试 8 位乘法的中间位函数，观察变量顺序对节点数的爆炸影响。
# 4. 思考：BDD 与 SAT 的分工 —— 前者适合「反复查询同一函数」，后者适合
#    「一次性求解」，为什么？
