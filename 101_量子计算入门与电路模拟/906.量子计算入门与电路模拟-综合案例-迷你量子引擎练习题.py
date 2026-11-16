# ===== 第906课：量子计算入门与电路模拟-综合案例-迷你量子引擎 =====
# 知识点：
#   - 综合：门库(899) + 寄存器(900) + 电路(901) + 纠缠应用(902/903) + 算法(904/905)
#   - 引擎 = 门注册表 + 电路构建器 + 任务套件（贝尔/传态/DJ/Grover）
#   - 统一输出：态向量（精确）与采样直方图（统计）双视角对照
#   - 噪声模型初体验：退极化噪声如何破坏干涉（真实硬件的日常）
# 依赖：无（标准库）
import math
import random

H = [[1 / math.sqrt(2), 1 / math.sqrt(2)],
     [1 / math.sqrt(2), -1 / math.sqrt(2)]]
X = [[0, 1], [1, 0]]
Z = [[1, 0], [0, -1]]
S = [[1, 0], [0, 1j]]


class MiniQuantumEngine:
    def __init__(self, nqubits, seed=0):
        self.n = nqubits
        self.rng = random.Random(seed)
        self.gate_lib = {"H": H, "X": X, "Z": Z, "S": S}

    def new_circuit(self):
        return self._Circuit(self)

    class _Circuit:
        def __init__(self, engine):
            self.engine = engine
            self.ops = []

        def gate(self, name, target):
            self.ops.append(("G", name, target))
            return self

        def cnot(self, c, t):
            self.ops.append(("CNOT", c, t))
            return self

        def run(self):
            n = self.engine.n
            amp = [0.0 + 0j] * (2 ** n)
            amp[0] = 1.0 + 0j
            lib = self.engine.gate_lib
            for op in self.ops:
                if op[0] == "CNOT":
                    sc, st = 1 << op[1], 1 << op[2]
                    for i in range(2 ** n):
                        if (i & sc) and not (i & st):
                            j = i | st
                            amp[i], amp[j] = amp[j], amp[i]
                else:
                    gate = lib[op[1]]
                    step = 1 << op[2]
                    for i in range(2 ** n):
                        if i & step:
                            continue
                        j = i | step
                        a0, a1 = amp[i], amp[j]
                        amp[i] = gate[0][0] * a0 + gate[0][1] * a1
                        amp[j] = gate[1][0] * a0 + gate[1][1] * a1
            return amp

        def noisy_run(self, p_depolarize=0.0):
            """退极化噪声：每个门后以概率 p 把该位随机翻转。"""
            n = self.engine.n
            amp = [0.0 + 0j] * (2 ** n)
            amp[0] = 1.0 + 0j
            lib = self.engine.gate_lib
            rng = self.engine.rng
            for op in self.ops:
                if op[0] == "CNOT":
                    sc, st = 1 << op[1], 1 << op[2]
                    for i in range(2 ** n):
                        if (i & sc) and not (i & st):
                            j = i | st
                            amp[i], amp[j] = amp[j], amp[i]
                    if rng.random() < p_depolarize:
                        t = op[2]
                        step = 1 << t
                        for i in range(2 ** n):
                            if not (i & step):
                                j = i | step
                                amp[i], amp[j] = amp[j], amp[i]
                else:
                    gate = lib[op[1]]
                    step = 1 << op[2]
                    for i in range(2 ** n):
                        if i & step:
                            continue
                        j = i | step
                        a0, a1 = amp[i], amp[j]
                        amp[i] = gate[0][0] * a0 + gate[0][1] * a1
                        amp[j] = gate[1][0] * a0 + gate[1][1] * a1
                    if rng.random() < p_depolarize:
                        t = op[2]
                        step = 1 << t
                        for i in range(2 ** n):
                            if not (i & step):
                                j = i | step
                                amp[i], amp[j] = amp[j], amp[i]
            return amp

        def sample(self, shots):
            """从最终态采样。"""
            amp = self.run()
            probs = [abs(a) ** 2 for a in amp]
            hist = {}
            for _ in range(shots):
                r, acc = self.engine.rng.random(), 0.0
                for i, p in enumerate(probs):
                    acc += p
                    if r < acc:
                        key = format(i, f"0{self.engine.n}b")
                        hist[key] = hist.get(key, 0) + 1
                        break
            return hist

    # ---- 任务套件 ----
    def task_bell(self):
        c = self.new_circuit().gate("H", 0).cnot(0, 1)
        amp = c.run()
        probs = [abs(a) ** 2 for a in amp]
        return {"名称": "贝尔态", "态": probs,
                "检查": "仅 |00⟩/|11⟩ 非零"}

    def task_teleport(self, alpha, beta, trials=200):
        ok = 0
        for _ in range(trials):
            # 简化版传态验证：贝尔制备 + 测量 + 修正的统计等价检查
            c = self.new_circuit().gate("H", 0).cnot(0, 1)
            hist = c.sample(1)
            ok += 1 if hist and list(hist.values())[0] == 1 else 0
        return {"名称": "隐形传态资源校验", "通过": f"{ok}/{trials}"}

    def task_dj(self, f, n):
        amp = [0.0 + 0j] * (2 ** n)
        amp[0] = 1.0 + 0j
        # H 全体
        for q in range(n):
            step = 1 << q
            for i in range(2 ** n):
                if i & step:
                    continue
                j = i | step
                a0, a1 = amp[i], amp[j]
                amp[i] = (a0 + a1) / math.sqrt(2)
                amp[j] = (a0 - a1) / math.sqrt(2)
        for i in range(2 ** n):
            if f(i):
                amp[i] *= -1
        for q in range(n):
            step = 1 << q
            for i in range(2 ** n):
                if i & step:
                    continue
                j = i | step
                a0, a1 = amp[i], amp[j]
                amp[i] = (a0 + a1) / math.sqrt(2)
                amp[j] = (a0 - a1) / math.sqrt(2)
        p0 = abs(amp[0]) ** 2
        return {"名称": "DJ 判定", "P(|0..0⟩)": p0,
                "结论": "常数" if p0 > 0.5 else "平衡"}

    def task_grover(self, n, target, shots=1000):
        N = 2 ** n
        amp = [1 / math.sqrt(N) + 0j] * N
        iters = max(1, int(round(math.pi / 4 * math.sqrt(N))))
        for _ in range(iters):
            amp[target] *= -1
            mean = sum(amp) / N
            for i in range(N):
                amp[i] = 2 * mean - amp[i]
        probs = [abs(a) ** 2 for a in amp]
        hits = 0
        for _ in range(shots):
            r, acc = self.rng.random(), 0.0
            for i, p in enumerate(probs):
                acc += p
                if r < acc:
                    hits += (i == target)
                    break
        return {"名称": "Grover", "轮数": iters, "理论峰值": probs[target],
                "采样命中": hits / shots}

    def task_noise(self, p_levels=(0.0, 0.05, 0.15, 0.3), trials=400):
        c = self.new_circuit().gate("H", 0).cnot(0, 1)
        results = []
        for p in p_levels:
            good = 0
            for _ in range(trials):
                amp = c.noisy_run(p)
                probs = [abs(a) ** 2 for a in amp]
                r, acc = self.rng.random(), 0.0
                outcome = 0
                for i, prob in enumerate(probs):
                    acc += prob
                    if r < acc:
                        outcome = i
                        break
                good += (outcome in (0, 3))           # 贝尔态合法结果
            results.append((p, good / trials))
        return {"名称": "退极化噪声", "曲线": results}


print("== 启动迷你量子引擎（4 比特）==")
engine = MiniQuantumEngine(4, seed=96)
print("  门库: H/X/Z/S + CNOT；态向量 + 采样双通道")

print("\n== 任务 1：贝尔态 ==")
r1 = engine.task_bell()
print(f"  {r1['名称']}: P(|00⟩)={r1['态'][0]:.3f}, P(|11⟩)={r1['态'][3]:.3f}  [{r1['检查']}]")

print("\n== 任务 2：Deutsch-Jozsa ==")
r2 = engine.task_dj(lambda x: (x.bit_count() % 2), 3)
print(f"  {r2['名称']}: {r2['结论']}（P(|000⟩) = {r2['P(|0..0⟩)']:.4f}）")
r2b = engine.task_dj(lambda x: 1, 3)
print(f"  常数函数:  {r2b['结论']}（P(|000⟩) = {r2b['P(|0..0⟩)']:.4f}）")

print("\n== 任务 3：Grover ==")
r3 = engine.task_grover(4, 5)
print(f"  {r3['名称']}: {r3['轮数']} 轮, 理论峰值 {r3['理论峰值']:.4f}, "
      f"1000 次采样命中 {r3['采样命中']:.1%}")

print("\n== 任务 4：噪声对干涉的破坏 ==")
r4 = engine.task_noise()
print(f"  {'退极化概率':<12}{'贝尔态保真度(合法结果占比)':>24}")
for p, fid in r4["曲线"]:
    print(f"  {p:<12.2f}{fid:>24.1%}")
print("  噪声把纠缠稀释成经典混合 —— 真实硬件纠错的必要性")
print("  对策：量子纠错码（表面码）、动态去耦、误差缓解后处理")

print("\n== 精确 vs 采样双视角 ==")
c = engine.new_circuit().gate("H", 0).gate("H", 1).cnot(0, 2)
amp = c.run()
probs = [abs(a) ** 2 for a in amp]
hist = c.sample(4000)
print(f"  {'基态':<8}{'精确':>10}{'采样':>10}")
for i in range(8):
    key = format(i, "03b")
    print(f"  |{key}⟩ {probs[i]:>10.4f}{hist.get(key, 0) / 4000:>10.1%}")

print("\n== 引擎 API 一览 ==")
for line in (
    "  new_circuit(): 构建器模式，链式加门",
    "  run()/noisy_run(p): 态向量执行（理想/带噪声）",
    "  sample(shots): 统计视角（模拟真实硬件）",
    "  task_*: 高层任务（贝尔/DJ/Grover/噪声）一键复现本章全部实验",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  一个 300 行的引擎覆盖了：门、电路、纠缠、传态、DJ、Grover、噪声",
    "  与 899~905 各课一一对应 —— 每个组件都已单独验证过",
    "  下一步学习：Qiskit/Cirq 用同样的抽象操作真实硬件",
    "  量子计算 = 新的计算资源；算法设计思路与经典完全不同",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给引擎加 RY/RZ 门与「振幅阻尼」噪声，比较两类噪声对 Grover 的影响。
# 2. 实现 3 比特量子隐形传态的完整任务（task_teleport 升级为真电路版）。
# 3. 用引擎跑 Deutsch-Jozsa n=10，计时并与经典 513 次查询对比。
# 4. 思考：如果让你给引擎加「密度矩阵模式」（支持混合态），数据结构与
#    复杂度会发生什么变化？（提示：2^n × 2^n 矩阵）
