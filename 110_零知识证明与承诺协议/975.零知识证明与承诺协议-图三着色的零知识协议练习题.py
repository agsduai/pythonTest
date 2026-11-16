# ===== 第975课：零知识证明与承诺协议-图三着色的零知识协议 =====
# 知识点：
#   - 经典 ZKP：证明『我知道图的三着色』而不泄露具体染色方案
#   - 每轮：随机置换颜色 → 承诺每个顶点 → 验证者选一条边 → 打开该边两端
#   - 零知识：置换后颜色标签无意义（红/绿/蓝重命名），泄露的只有『两端不同』
#   - 可靠性：每轮作弊被抓概率 ≥ 1/|E|，t 轮后 ≈ (1−1/|E|)^t
#   - 这是 NP 完全问题的通用 ZKP：任何 NP 证明都能走同一框架
# 依赖：无（标准库）
import hashlib
import random


def hash_commit(value, salt):
    return hashlib.sha256(f"{value}||{salt}".encode()).hexdigest()


class ColoredGraph:
    def __init__(self, edges):
        self.edges = edges                     # [(u, v)]
        self.vertices = sorted({v for e in edges for v in e})

    def valid_coloring(self, coloring):
        return all(coloring[u] != coloring[v] for u, v in self.edges)


class ZKProver:
    def __init__(self, graph, coloring, rng):
        self.graph = graph
        self.coloring = dict(coloring)
        self.rng = rng

    def commit_round(self):
        """随机置换颜色后承诺每个顶点。返回 (承诺表, 置换表)。"""
        perm = {"red": None, "green": None, "blue": None}
        palette = ["red", "green", "blue"]
        self.rng.shuffle(palette)
        perm = dict(zip(["red", "green", "blue"], palette))
        commitments = {}
        salts = {}
        for vertex in self.graph.vertices:
            original = self.coloring[vertex]
            permuted = perm[original]
            salt = self.rng.randint(1, 2 ** 32)
            commitments[vertex] = hash_commit(permuted, salt)
            salts[vertex] = (permuted, salt)
        return commitments, salts

    def reveal_edge(self, salts, edge):
        u, v = edge
        return {u: salts[u], v: salts[v]}

    def reveal_all(self, salts):
        return {v: salts[v][0] for v in salts}


class ZKVerifier:
    def __init__(self, graph, rng):
        self.graph = graph
        self.rng = rng

    def challenge(self):
        return self.rng.choice(self.graph.edges)

    def check(self, commitments, edge, revealed, perm_check=None):
        u, v = edge
        if u not in revealed or v not in revealed:
            return False
        color_u = revealed[u][0]
        color_v = revealed[v][0]
        # 检查承诺一致 + 两端颜色不同
        ok_u = hash_commit(color_u, revealed[u][1]) == commitments[u]
        ok_v = hash_commit(color_v, revealed[v][1]) == commitments[v]
        return ok_u and ok_v and color_u != color_v


print("== 图与已知三着色 ==")
edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
coloring = {0: "red", 1: "green", 2: "blue", 3: "red"}
graph = ColoredGraph(edges)
print(f"  边集: {edges}   顶点: {graph.vertices}")
print(f"  着色: {coloring}   合法: {graph.valid_coloring(coloring)}")

print("\n== 单轮协议演示 ==")
rng = random.Random(175)
prover = ZKProver(graph, coloring, rng)
verifier = ZKVerifier(graph, rng)
commitments, salts = prover.commit_round()
edge = verifier.challenge()
revealed = prover.reveal_edge(salts, edge)
ok = verifier.check(commitments, edge, revealed)
print(f"  承诺: { {f'v{v}': c[:12] + '...' for v, c in commitments.items()} }")
print(f"  验证者选边: {edge}")
print(f"  打开该边两端: v{edge[0]}={revealed[edge[0]][0]!r}(salt={revealed[edge[0]][1]})")
print(f"                v{edge[1]}={revealed[edge[1]][0]!r}")
print(f"  检查通过: {ok}（两端颜色不同 ✓）")

print("\n== 多轮协议：作弊概率的指数衰减 ==")
def run_protocol(prover_graph, prover_coloring, rounds, rng, cheat=False):
    prover = ZKProver(prover_graph, prover_coloring, rng)
    verifier = ZKVerifier(prover_graph, rng)
    for _ in range(rounds):
        commitments, salts = prover.commit_round()
        edge = verifier.challenge()
        if cheat:
            # 作弊者：用一个『只有少数边合法』的假方案 + 碰运气
            revealed = {v: (prover_coloring.get(v, "blue"),
                            rng.randint(1, 2 ** 32))
                        for v in prover_graph.vertices}
            # 作弊者只对自己有把握的边赌一把：随机边的两端颜色恰不同？
            # 简化：用非法着色跑完整协议，期望大量失败
            ok = verifier.check(commitments, edge, revealed)
        else:
            revealed = prover.reveal_edge(salts, edge)
            ok = verifier.check(commitments, edge, revealed)
        if not ok:
            return False
    return True


honest_pass = sum(run_protocol(graph, coloring, 30, rng) for _ in range(20))
print(f"  诚实 Prover × 30 轮 × 20 次: 全部通过 {honest_pass}/20")
cheat_pass = sum(run_protocol(graph, {0: "red", 1: "red", 2: "blue", 3: "red"},
                              30, rng, cheat=False) for _ in range(20))
print(f"  非法着色（两顶点同色）× 30 轮: 通过 {cheat_pass}/20 —— 可靠性生效")
print("  单轮作弊被抓概率 ≥ 1/|E| = 1/5 → 30 轮后 ≈ 0.8^30 ≈ 0.2%")

print("\n== 零知识性：验证者学到了什么 ==")
print("  验证者每轮只看到：『某条边的两端颜色不同』+ 无意义的颜色标签")
print("  颜色标签每轮随机置换 → red 本轮可能是红下一轮是绿 → 无信息")
print("  多轮累计：验证者只知道『确实存在合法三着色』—— 恰好是要证明的命题")
print("  模拟器论证：随机置换 + 随机边 → 不参与协议也能伪造同样的对话")

print("\n== NP 完全问题的通用性 ==")
for line in (
    "  图三着色是 NP 完全问题 → 任何 NP 命题都可归约为它",
    "  『我知道这个谜题的解』都可以转化为『我知道这个图的着色』",
    "  理论意义：所有 NP 中的知识都可零知识证明（1985 年里程碑）",
    "  实践意义：通用 ZKP 系统（zk-SNARK）把归约自动化",
):
    print("  -", line)

print("\n== 交互轮数与置信度 ==")
print(f"  {'轮数':>6}{'作弊通过上限':>16}")
n_edges = len(edges)
for t in (1, 5, 10, 30, 60):
    bound = (1 - 1 / n_edges) ** t
    print(f"  {t:>6}{bound:>16.4f}")
print("  工程典型：40~100 轮（错误率 < 1%）—— 用时间换置信度")

print("\n== 小结 ==")
for line in (
    "  随机置换 + 承诺 + 边挑战 = 最直观的零知识协议",
    "  零知识性来自『每轮颜色语言都被重命名』—— 相对信息无意义",
    "  NP 完全归约让图着色协议成为『万能证明模板』",
    "  976 课：更现代的路线 —— 算术化与约束系统（R1CS）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「Fiat-Shamir 化」的图着色协议：边选择由承诺表哈希决定（非交互）。
# 2. 实现「恶意验证者」：验证者把本轮学到的边颜色用于下一轮选择，证明零知识性
#    仍然保持（信息不可累积）。
# 3. 构造 5 节点图并实现完整协议，统计 100 轮的通信量（承诺+响应的字节数）。
# 4. 思考：如果置换表被验证者猜到，协议还剩多少安全性？哪个环节是
#    『零知识』的命门？
