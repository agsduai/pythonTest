# ===== 第890课：概率图模型与结构化推断-综合案例-医疗诊断专家系统 =====
# 知识点：
#   - 综合本章：贝叶斯网络(883) + 变量消元(884) + 采样推断(889)
#   - 专家系统骨架：疾病-症状网络 + CPT -> 后验诊断 + 信息增益问诊建议
#   - 信息增益：问哪个症状能让诊断「熵」下降最多 —— 主动问诊
#   - 解释掉现象的落地版：确诊流感会降低「肺炎」的相对嫌疑
#   - 输出报告：嫌疑排序、关键证据、下一步检查建议
# 依赖：无（标准库）
import math
from itertools import product as iproduct


class DiagNet:
    """疾病/症状二值网络。结构：疾病 -> 症状（症状还可能互相独立）。"""

    def __init__(self):
        self.parents = {}
        self.cpt = {}

    def add(self, node, parents, cpt):
        self.parents[node] = list(parents)
        self.cpt[node] = cpt

    def node_prob(self, node, value, a):
        return self.cpt[node][tuple(a[p] for p in self.parents[node])][value]

    def joint_prob(self, a):
        p = 1.0
        for v in self.topo():
            p *= self.node_prob(v, a[v], a)
        return p

    def topo(self):
        order, done = [], set()
        pending = set(self.parents)
        while pending:
            for v in sorted(pending):
                if all(p in done for p in self.parents[v]):
                    order.append(v)
                    done.add(v)
            pending -= done
        return order


def build_medical_net():
    net = DiagNet()
    # 疾病层：先验
    net.add("流感", [], {(): {"T": 0.10, "F": 0.90}})
    net.add("肺炎", [], {(): {"T": 0.03, "F": 0.97}})
    net.add("阑尾炎", [], {(): {"T": 0.01, "F": 0.99}})
    # 症状层
    net.add("发烧", ["流感", "肺炎"],
            {("T", "T"): {"T": 0.98, "F": 0.02}, ("T", "F"): {"T": 0.90, "F": 0.10},
             ("F", "T"): {"T": 0.92, "F": 0.08}, ("F", "F"): {"T": 0.05, "F": 0.95}})
    net.add("咳嗽", ["流感", "肺炎"],
            {("T", "T"): {"T": 0.80, "F": 0.20}, ("T", "F"): {"T": 0.85, "F": 0.15},
             ("F", "T"): {"T": 0.60, "F": 0.40}, ("F", "F"): {"T": 0.10, "F": 0.90}})
    net.add("腹痛", ["阑尾炎"],
            {("T",): {"T": 0.85, "F": 0.15}, ("F",): {"T": 0.08, "F": 0.92}})
    net.add("呼吸困难", ["肺炎"],
            {("T",): {"T": 0.70, "F": 0.30}, ("F",): {"T": 0.05, "F": 0.95}})
    return net


def ve_posterior(net, query, evidence):
    """小型网络的变量消元（按证据裁剪后枚举求和）。"""
    den = {"T": 0.0, "F": 0.0}
    nodes = net.topo()
    for combo in iproduct(("T", "F"), repeat=len(nodes)):
        a = dict(zip(nodes, combo))
        if any(a[e] != v for e, v in evidence.items()):
            continue
        p = net.joint_prob(a)
        den[a[query]] += p
    total = den["T"] + den["F"]
    return {"T": den["T"] / total, "F": den["F"] / total}


def entropy(dist):
    return -sum(p * math.log(max(p, 1e-12)) for p in dist.values())


def diagnose(net, evidence, diseases=("流感", "肺炎", "阑尾炎")):
    """对每个疾病计算后验并归一化为诊断分布。"""
    scores = {}
    for d in diseases:
        scores[d] = ve_posterior(net, d, evidence)["T"]
    total = sum(scores.values())
    norm = {d: s / total for d, s in scores.items()}
    return norm


def best_question(net, evidence, candidates):
    """选期望熵下降最大的症状作为下一个问题。"""
    base_h = entropy(diagnose(net, evidence))
    best, best_gain = None, -1.0
    for sym in candidates:
        if sym in evidence:
            continue
        gain = 0.0
        for ans in ("T", "F"):
            pe = dict(evidence)
            pe[sym] = ans
            pw = ve_posterior(net, sym, evidence)[ans]
            if pw < 1e-9:
                continue
            gain += pw * entropy(diagnose(net, pe))
        reduction = base_h - gain
        if reduction > best_gain:
            best_gain, best = reduction, sym
    return best, best_gain


net = build_medical_net()
print("== 医疗诊断网络 ==")
print("  疾病: 流感(0.10) 肺炎(0.03) 阑尾炎(0.01)")
print("  症状: 发烧<-流感+肺炎, 咳嗽<-流感+肺炎, 腹痛<-阑尾炎, 呼吸困难<-肺炎")

print("\n== 场景1：患者发热 + 咳嗽 ==")
ev1 = {"发烧": "T", "咳嗽": "T"}
diag1 = diagnose(net, ev1)
print(f"  证据: {ev1}")
for d, p in sorted(diag1.items(), key=lambda x: -x[1]):
    print(f"    {d:<6} 后验概率 = {p:.3f}")
raw = {d: ve_posterior(net, d, ev1)["T"] for d in diag1}
print(f"  （归一化前独立后验: {dict((k, round(v, 3)) for k, v in raw.items())}）")

print("\n== 场景2：解释掉 —— 再确诊流感 ==")
ev2 = dict(ev1)
ev2["流感确诊"] = "T"
# 把「流感」作为证据加入
ev2b = {"发烧": "T", "咳嗽": "T", "流感": "T"}
diag2 = diagnose(net, ev2b)
print(f"  证据: {ev2b}")
for d, p in sorted(diag2.items(), key=lambda x: -x[1]):
    print(f"    {d:<6} 后验概率 = {p:.3f}")
print(f"  流感自身 = {ve_posterior(net, '流感', ev2b)['T']:.3f}（必为 1）")
print(f"  肺炎嫌疑从 {diag1['肺炎']:.3f} 降到 {diag2['肺炎']:.3f} —— 同一症状被流感解释掉")

print("\n== 场景3：主动问诊（信息增益）==")
evidence = {"发烧": "T"}
candidates = ["咳嗽", "腹痛", "呼吸困难"]
sym, gain = best_question(net, evidence, candidates)
print(f"  已知: {evidence}")
print(f"  当前诊断分布: {diagnose(net, evidence)}")
print(f"  下一个最值得问的症状 = {sym}（期望熵下降 {gain:.3f} bit）")
evidence[sym] = "T"
diag3 = diagnose(net, evidence)
print(f"  假设回答为 T -> 新分布: {diag3}")

print("\n== 场景4：阴性证据也有信息量 ==")
ev4 = {"发烧": "T", "腹痛": "F", "呼吸困难": "F"}
diag4 = diagnose(net, ev4)
print(f"  证据: {ev4}")
for d, p in sorted(diag4.items(), key=lambda x: -x[1]):
    print(f"    {d:<6} 后验概率 = {p:.3f}")
print("  两个关键症状阴性 -> 阑尾炎/肺炎被大幅排除 —— 阴性证据同值钱")

print("\n== 采样对照（889 课的似然加权）==")
import random
rng = random.Random(71)
num, den = 0.0, 0.0
for _ in range(20000):
    a = {"发烧": "T", "咳嗽": "T"}
    w = 1.0
    for v in net.topo():
        if v in a:
            w *= net.cpt[v][tuple(a[p] for p in net.parents[v])][a[v]]
        else:
            p = net.cpt[v][tuple(a[p] for p in net.parents[v])]["T"]
            a[v] = "T" if rng.random() < p else "F"
    den += w
    if a["肺炎"] == "T":
        num += w
print(f"  似然加权 P(肺炎 | 发烧,咳嗽) = {num / den:.4f}")
print(f"  变量消元结果               = {raw['肺炎']:.4f}")

print("\n== 专家系统架构 ==")
for line in (
    "  知识层：疾病先验 + 症状条件表（领域专家填写）",
    "  推断层：变量消元/采样给出后验（本章全部方法）",
    "  交互层：信息增益选问题，解释掉提供可读的推理链",
    "  真实系统（如 Mycin/QSKY）再加决策成本、检查费用与风险偏好",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给网络加「检查项目」节点（如血检），成本不同：实现「每 bit 信息成本」
#    最优的问诊策略。
# 2. 实现多病症并发诊断：不归一化，直接输出各疾病独立后验，讨论解释掉与
#    共病的关系。
# 3. 用 883 课的 d-分离分析：哪些症状间在「无观测」时独立？给观测发烧后呢？
# 4. 思考：CPT 的数字从哪来？临床试验数据 + 专家校准各扮演什么角色？
