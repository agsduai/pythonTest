# ===== 第976课：零知识证明与承诺协议-算术化与R1CS约束系统 =====
# 知识点：
#   - zk-SNARK 的第一步：把计算『算术化』成约束系统
#   - R1CS：Rank-1 约束系统 —— 每条约束形如 A·w ∘ B·w = C·w
#   - witness w：包含秘密输入与全部中间量的向量
#   - 满足性检查：验证者只需要检查矩阵向量乘 —— 无需重跑计算
#   - 经典例子：证明『我知道 x 使 x³ + x + 5 = 35』（Vitalik 的入门例）
# 依赖：无（标准库）


P = 97                                   # 教学素数域（所有运算 mod 97）


def mod(a):
    return a % P


class R1CS:
    """Rank-1 约束系统：一组 A/B/C 线性形式。"""

    def __init__(self, num_variables):
        self.num_vars = num_variables
        self.constraints = []                # [(A, B, C)] 每项是系数列表

    def add_constraint(self, a_terms, b_terms, c_terms):
        """terms: [(系数, 变量下标)] -> 稠密系数列表。"""
        self.constraints.append(
            (self._dense(a_terms), self._dense(b_terms), self._dense(c_terms)))

    def _dense(self, terms):
        row = [0] * self.num_vars
        for coef, idx in terms:
            row[idx] = (row[idx] + coef) % P
        return row

    def matvec(self, row, w):
        """模域点积。"""
        return sum(coef * w[i] for i, coef in enumerate(row)) % P

    def is_satisfied(self, w):
        """witness 满足所有约束？"""
        for a, b, c in self.constraints:
            av = self.matvec(a, w)
            bv = self.matvec(b, w)
            cv = self.matvec(c, w)
            if (av * bv - cv) % P != 0:
                return False, (av, bv, cv)
        return True, None


def build_cubic_constraints():
    """构造 x³ + x + 5 = 35 的 R1CS。
    变量表: w = [1(常数), x, x², x³, y] 其中 y = x³ + x"""
    r1cs = R1CS(num_variables=5)
    ONE, X, X2, X3, Y = 0, 1, 2, 3, 4
    # 约束 1: x · x = x²
    r1cs.add_constraint([(1, X)], [(1, X)], [(1, X2)])
    # 约束 2: x · x² = x³
    r1cs.add_constraint([(1, X)], [(1, X2)], [(1, X3)])
    # 约束 3: (x + x²) · 1 = y   （线性约束：B 全 1）
    r1cs.add_constraint([(1, X), (1, X2)], [(1, ONE)], [(1, Y)])
    # 约束 4: (y + 5) · 1 = 35   （常数 5 放进 A 的常数项）
    r1cs.add_constraint([(1, Y), (5, ONE)], [(1, ONE)], [(35, ONE)])
    return r1cs


def witness_for(x):
    """由 x 计算 witness：[1, x, x², x³, y]。"""
    x2 = (x * x) % P
    x3 = (x2 * x) % P
    y = (x3 + x) % P
    return [1, x % P, x2, x3, y]


print("== 目标计算 ==")
print("  证明：我知道 x 使 x³ + x + 5 = 35（x = 3）")
x = 3
print(f"  x = {x}: {x}³ + {x} + 5 = {x**3 + x + 5} ✓")

print("\n== R1CS 约束系统 ==")
r1cs = build_cubic_constraints()
print(f"  变量向量 w = [1, x, x², x³, y]（5 个变量）")
print(f"  约束数 = {len(r1cs.constraints)}（每条 Rank-1: A·w ∘ B·w = C·w）")
for i, (a, b, c) in enumerate(r1cs.constraints):
    print(f"    约束{i + 1}: A{a} ∘ B{b} = C{c}")

print("\n== witness 满足性检查 ==")
w = witness_for(x)
print(f"  witness = {w}")
satisfied, detail = r1cs.is_satisfied(w)
print(f"  满足所有约束: {satisfied}")

print("\n== 伪造 witness 会被抓住 ==")
for bad_x in (2, 4, 5):
    bad_w = witness_for(bad_x)
    sat, detail = r1cs.is_satisfied(bad_w)
    # x³+x+5 = 35 只有 x=3 满足
    real_check = (bad_x ** 3 + bad_x + 5) == 35
    print(f"  x={bad_x}: 数学上 {bad_x}³+{bad_x}+5 = "
          f"{bad_x**3 + bad_x + 5} ≠ 35 -> 满足: {sat}"
          f"{'（碰巧一致）' if sat == real_check else ''}")

print("\n== 约束系统的『可验证性』杠杆 ==")
print(f"  {'角色':<12}{'做的事':<34}{'成本'}")
for row in (("证明者", "算 witness + 检查全部约束", "O(约束数)"),
            ("验证者", "同样的矩阵检查", "O(约束数) —— SNARK 压缩到 O(log)"),
            ("朴素方案", "重跑整段计算", "与原计算同价")):
    print(f"  {row[0]:<12}{row[1]:<34}{row[2]}")
print("  SNARK 的魔法：验证比计算便宜 —— 本章只做到『结构化』这一步")

print("\n== 从 R1CS 到零知识的路线图 ==")
for line in (
    "  1. 算术化：计算 → R1CS（本课）",
    "  2. 多项式化：约束 → 多项式恒等式（QAP）",
    "  3. 承诺：对 witness 多项式做多项式承诺",
    "  4. 零知识：witness 加随机盲化因子",
    "  5. 简洁验证：验证者只查多项式在随机点的取值",
):
    print("  -", line)

print("\n== 线性约束与乘法约束的分工 ==")
print("  R1CS 一条约束只支持一次乘法：A·w ∘ B·w = C·w")
print("  加法『免费』（线性组合进 A 或 C）；乘法『昂贵』（占一条约束）")
print(f"  本例：2 次乘法（x²、x³）+ 2 条线性 = {len(r1cs.constraints)} 条约束")
print("  电路复杂度 = 约束数 —— SNARK 优化的核心指标")

print("\n== 小结 ==")
for line in (
    "  R1CS 把任意计算变成『有限个乘法约束』的满足问题",
    "  witness 包含全部中间量：验证者检查的是『关系』不是『过程』",
    "  算术化是通用 ZKP 的第一步 —— 之后交给多项式承诺",
    "  977 课：门限签名 —— 秘密被拆分后的签名协作",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 把「x 是否为完全平方数」写成 R1CS（提示：需要布尔辅助变量控制查表）。
# 2. 实现「约束计数」：对给定多项式计算需要的乘法约束数。
# 3. 加一个布尔约束模板：x·(1−x)=0 强制 x∈{0,1}。
# 4. 思考：为什么『布尔化』约束在电路中极其常见？零知识证明的变量为什么
#    需要显式的取值范围控制？
