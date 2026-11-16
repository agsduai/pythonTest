# ===== 第765课：信息论与编码-信道容量与噪声 =====
# 知识点：
#   - 信道：输入 X 经转移概率 P(Y|X) 得到输出 Y；噪声由条件分布刻画
#   - 互信息 I(X;Y) = H(Y) - H(Y|X)：输出里保留了多少关于输入的信息
#   - 信道容量 C = max_{P(X)} I(X;Y)：可靠传输的极限速率（bit/符号）
#   - 二元对称信道 BSC(p)：以概率 p 翻转，C = 1 - H(p)
#   - 香农有噪信道编码定理：R < C 时存在编码使错误率任意小；R > C 则不可能
#   - 用重复码/汉明码可在低速率下降低误码，但代价是速率
# 依赖：无（标准库）
import math
from itertools import product


def log2(p): return math.log2(p) if p > 0 else 0.0
def H(*ps): return -sum(p*log2(p) for p in ps if p > 0)


def bsc_capacity(p):
    """二元对称信道容量 C = 1 - H(p)。"""
    return 1 - H(p, 1-p)


def bsc_mutual_information(q, p):
    """输入 P(X=1)=q，翻转概率 p 时的 I(X;Y)。"""
    # P(Y=1) = q(1-p) + (1-q)p
    py1 = q*(1-p) + (1-q)*p
    py0 = 1-py1
    hy = H(py0, py1)
    hyx = H(1-p, p)                # 条件熵与输入分布无关（BSC 对称）
    return hy - hyx


print("== 二元对称信道 BSC(p) 的容量 ==")
print(f"  {'p(翻转率)':<12}{'H(p)':<10}{'C=1-H(p)':<12}")
for p in (0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5):
    print(f"  {p:<12.2f}{H(p,1-p):<10.4f}{bsc_capacity(p):<12.4f}")
print("  p=0 无噪声 C=1；p=0.5 输出与输入独立 C=0；p>0.5 可「反着猜」恢复")

print("\n== 输入分布 q 对互信息的影响（p=0.1）==")
p = 0.1
for q in (0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0):
    mi = bsc_mutual_information(q, p)
    print(f"  P(X=1)={q:<5.2f}: I(X;Y)={mi:.4f} bit")
print(f"  q=0.5 时达到最大 = 容量 {bsc_capacity(p):.4f}")
print("  对称信道的最优输入分布是均匀分布")

print("\n== 通用离散信道的容量（Blahut-Arimoto 迭代）==")
def channel_capacity(P, iterations=500):
    """P[y][x] = P(Y=y|X=x)；返回 (容量, 最优输入分布)。"""
    m, n = len(P), len(P[0])
    r = [1/n]*n                      # 初始输入均匀分布
    for _ in range(iterations):
        # q[x][y] = P(X=x|Y=y) ∝ r[x]·P[y][x]
        q = [[0.0]*m for _ in range(n)]
        for y in range(m):
            s = sum(r[x]*P[y][x] for x in range(n))
            if s > 0:
                for x in range(n):
                    q[x][y] = r[x]*P[y][x]/s
        # r 反比于 exp(-Σ P·log q)
        new = []
        for x in range(n):
            d = sum(P[y][x]*log2(q[x][y]) for y in range(m) if q[x][y] > 0)
            new.append(2**d)
        s = sum(new)
        r = [v/s for v in new]
    # 计算 I(X;Y)
    I = 0.0
    for x in range(n):
        for y in range(m):
            if r[x] > 0 and P[y][x] > 0 and q[x][y] > 0:
                I += r[x]*P[y][x]*log2(P[y][x]/(sum(r[xx]*P[y][xx] for xx in range(n))))
    return I, r

# BSC(0.1) 用通用算法验证
PBSC = [[0.9, 0.1], [0.1, 0.9]]     # P[y][x]
C, r = channel_capacity(PBSC)
print(f"  BSC(0.1) 迭代求容量 C={C:.6f}, 最优输入分布={[round(v,4) for v in r]}")
print(f"  解析解 1-H(0.1)={bsc_capacity(0.1):.6f} 一致={abs(C-bsc_capacity(0.1))<1e-6}")

# 一个非对称信道：Z 信道（0 永不翻，1 以 p 翻成 0）
print("\n== Z 信道（非对称）==")
for pz in (0.1, 0.3, 0.5):
    PZ = [[1.0, pz], [0.0, 1.0-pz]]   # y=0/1 ; x=0/1
    Cz, rz = channel_capacity(PZ)
    print(f"  p={pz}: C={Cz:.4f} bit, 最优 P(X=1)={rz[1]:.3f}（不再是 0.5）")

print("\n== 重复码：用速率换可靠性 ==")
def repetition_error(p, n):
    """n 次重复 + 多数表决的误码率（n 为奇数）。"""
    return sum(math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(n//2+1, n+1))

p = 0.1
print(f"  原始 BSC 误码率 p={p}")
for n in (1, 3, 5, 7, 11, 21):
    e = repetition_error(p, n)
    print(f"    重复 {n:>2} 次: 速率=1/{n}={1/n:.3f} 误码率={e:.6f}")
print("  误码率随 n 指数下降，但速率 1/n 也线性下降 -> R→0 才能Pe→0")

print("\n== 香农限：速率与可靠性的权衡 ==")
print(f"  p={p} 时容量 C={bsc_capacity(p):.4f} bit/符号")
for R in (0.1, 0.3, 0.5, 0.53, 0.7, 0.9):
    status = "理论可达（需足够长的码字）" if R < bsc_capacity(p) else "不可能可靠传输"
    print(f"  R={R:.2f}: {status}")

print("\n== 汉明码对比（概念） ==")
for line in (
    "  Hamming(7,4): 4 位数据 + 3 位校验，速率 4/7≈0.57，可纠 1 位错",
    "  相比重复码，同样的冗余能纠更多错 / 更高码率",
    "  LDPC / Turbo / Polar 码是接近香农限的现代编码（5G 用 Polar/LDPC）",
    "  香农定理只证明「存在」，具体构造用了数十年",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  通信：调制阶数、编码率、SNR 与可达速率的换算",
    "  存储：磁盘/SSD 的 ECC 与误码率预算",
    "  ML：信息瓶颈、表示学习与互信息估计",
    "  与第764课信源编码对应：信源去冗余，信道加可控冗余",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 Blahut-Arimoto 求三元对称信道的容量并验证均匀分布最优。
# 2. 实现 Hamming(7,4) 编解码，实测 BSC(0.1) 下的误码率改善。
# 3. 绘制「码率 R vs 最小可达误码率」的示意曲线。
# 4. 思考：为什么 p=0.5 的 BSC 容量为 0，而 p>0.5 反而又能传信息？
