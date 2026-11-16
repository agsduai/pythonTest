# ===== 第657课：数值计算与误差分析-向量与矩阵运算 =====
# 知识点：
#   - 纯 Python 实现向量/矩阵基础运算（不依赖 NumPy，理解底层代价）
#   - 点积用 math.fsum 补偿求和，比 sum 更稳；范数用 math.hypot 防溢出
#   - 矩阵乘法三重循环 O(n³)；行优先遍历缓存更友好
#   - 高斯消元解线性方程组：必须选主元（pivoting），否则除零/误差放大
#   - 条件数大的矩阵（病态）用小扰动测试解的敏感度
#   - 与第27章 NumPy 对比：同样的运算，纯 Python 慢但便于理解原理
# 依赖：无（标准库）
import math
import time

Vector = list
Matrix = list


def dot(a: Vector, b: Vector) -> float:
    return math.fsum(x * y for x, y in zip(a, b))


def norm(v: Vector) -> float:
    return math.sqrt(math.fsum(x * x for x in v))


def normalize(v: Vector) -> Vector:
    n = norm(v)
    if n == 0:
        raise ValueError("零向量无法归一化")
    return [x / n for x in v]


def mat_vec(A: Matrix, x: Vector) -> Vector:
    return [dot(row, x) for row in A]


def mat_mul(A: Matrix, B: Matrix) -> Matrix:
    n, m, p = len(A), len(B), len(B[0])
    if len(A[0]) != m:
        raise ValueError("维度不匹配")
    BT = list(zip(*B))                 # 转置后按列取，缓存更友好
    return [[math.fsum(a * b for a, b in zip(row, col)) for col in BT] for row in A]


def transpose(A: Matrix) -> Matrix:
    return [list(col) for col in zip(*A)]


def identity(n: int) -> Matrix:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def solve(A: Matrix, b: Vector) -> Vector:
    """高斯消元 + 部分选主元，返回 Ax=b 的解。"""
    n = len(A)
    M = [list(map(float, row)) + [float(bb)] for row, bb in zip(A, b)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-15:
            raise ValueError("矩阵奇异或接近奇异")
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(col + 1, n):
            factor = M[r][col] / pv
            for c in range(col, n + 1):
                M[r][c] -= factor * M[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - math.fsum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


print("== 向量运算 ==")
a, b = [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]
print(f"  a={a} b={b}")
print(f"  点积 = {dot(a, b)}  范数|a| = {norm(a):.6f}")
print(f"  归一化 a = {[round(v, 4) for v in normalize(a)]}")
print(f"  验证 |normalize(a)| = {norm(normalize(a)):.12f}")
print(f"  hypot 防溢出: hypot(3e308, 4e308) = {math.hypot(3e308, 4e308):.3e}")

print("\n== 矩阵乘法 ==")
A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]
print(f"  A={A}")
print(f"  B={B}")
print(f"  A@B = {mat_mul(A, B)}")
print(f"  A 的转置 = {transpose(A)}")
I = identity(2)
print(f"  A@I = {mat_mul(A, I)}（单位元验证）")

print("\n== 高斯消元解方程 ==")
# 2x + y = 5 ; x + 3y = 10  -> x=1, y=3
A2, b2 = [[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0]
x = solve(A2, b2)
print(f"  A={A2} b={b2}")
print(f"  解 = {[round(v, 10) for v in x]}（期望 [1, 3]）")
print(f"  残差 A@x-b = {[round(v, 12) for v in [r - t for r, t in zip(mat_vec(A2, x), b2)]]}")

print("\n== 不选主元的危险 ==")
singular = [[0.0, 1.0], [1.0, 0.0]]
try:
    # 朴素实现会在第一个主元 0 处崩；带选主元的 solve 能正常交换行
    print(f"  带选主元 solve 结果: {solve(singular, [2.0, 1.0])}")
except ValueError as e:
    print("  报错:", e)

print("\n== 病态矩阵：希尔伯特矩阵 ==")
def hilbert(n):
    return [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]

for n in (3, 5, 7):
    H = hilbert(n)
    x_true = [1.0] * n
    rhs = mat_vec(H, x_true)
    try:
        x_hat = solve(H, rhs)
        err = max(abs(u - v) for u, v in zip(x_hat, x_true))
        print(f"  n={n}: 无扰动解最大误差={err:.3e}")
        # 给右端加 1e-10 扰动
        rhs2 = [v + 1e-10 for v in rhs]
        x2 = solve(H, rhs2)
        amp = max(abs(u - v) for u, v in zip(x2, x_hat)) / 1e-10
        print(f"       右端 1e-10 扰动被放大 ≈ {amp:.2e} 倍（条件数大）")
    except ValueError as e:
        print(f"  n={n}: {e}")

print("\n== 纯 Python vs NumPy 的定位 ==")
n = 80
M = [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]
v = [1.0] * n
t0 = time.perf_counter()
mat_vec(M, v)
dt = time.perf_counter() - t0
print(f"  纯 Python 80×80 矩阵乘向量: {dt * 1000:.2f} ms（O(n²)={n*n} 次乘加）")
print("  NumPy 用 C/BLAS + SIMD，通常快 1~2 个数量级（第27章）")
print("  本课目的是理解原理与数值风险，不是替代 NumPy")

print("\n== 数值要点 ==")
for line in [
    "  点积/求和用 math.fsum，避免累加误差",
    "  范数/距离用 math.hypot，避免平方溢出",
    "  消元必须选主元，否则小主元会把误差放大",
    "  病态问题先估计条件数，必要时正则化或换更高精度",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 LU 分解（带主元置换），复用分解结果解多个右端向量。
# 2. 用幂迭代法求矩阵的主特征值，观察收敛速度与特征值间隔的关系。
# 3. 实现矩阵的条件数估计（用 ||A||·||A⁻¹|| 近似），验证希尔伯特矩阵。
# 4. 思考：为什么「残差小」不等于「解准确」？病态矩阵里会发生什么？
