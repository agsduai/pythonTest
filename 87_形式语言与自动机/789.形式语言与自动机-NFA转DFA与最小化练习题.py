# ===== 第789课：形式语言与自动机-NFA转DFA与最小化 =====
# 知识点：
#   - 子集构造法 subset construction：NFA 的「状态集合」就是 DFA 的一个状态
#   - DFA 状态数最坏 2^n（指数爆炸），但实践中通常远小于此
#   - DFA 模拟 O(n) 且无 ε 处理，编译器后端/高性能匹配都用 DFA
#   - 等价状态：对任意输入串都转移到「同为接受/同为拒绝」的两个状态可合并
#   - 最小化：先去掉不可达状态，再迭代细分等价类（Hopcroft/Moore 算法）
#   - 最小 DFA 唯一（除状态命名），这是 DFA 最重要的理论性质
# 依赖：无（标准库）


def epsilon_closure(nfa, states):
    stack, closure = list(states), set(states)
    while stack:
        s = stack.pop()
        for t in nfa.trans.get((s, ""), ()):
            if t not in closure:
                closure.add(t); stack.append(t)
    return closure


def nfa_to_dfa(nfa, alphabet="ab"):
    """子集构造：DFA 状态 = NFA 状态集合（frozenset 便于比较）。"""
    start = frozenset(nfa.epsilon_closure({nfa.start}))
    dfa_states = {start: 0}                  # frozenset -> 编号
    order = [start]
    delta = {}
    i = 0
    while i < len(order):
        subset = order[i]
        i += 1
        for ch in alphabet:
            nxt = set()
            for q in subset:
                nxt |= nfa.trans.get((q, ch), set())
            if not nxt:
                continue                      # 无后继 -> 死态（省略）
            closure = frozenset(nfa.epsilon_closure(nxt))
            if closure not in dfa_states:
                dfa_states[closure] = len(order)
                order.append(closure)
            delta[(dfa_states[subset], ch)] = dfa_states[closure]
    accepting = {idx for subset, idx in dfa_states.items()
                 if nfa.accept in subset}
    return dfa_states, delta, accepting, alphabet


class DFA:
    def __init__(self, n_states, delta, accepting, alphabet):
        self.n, self.delta, self.accepting, self.alphabet = n_states, delta, accepting, alphabet

    def accepts(self, s):
        q = 0
        for ch in s:
            q = self.delta.get((q, ch))
            if q is None: return False
        return q in self.accepting

    def reachable_states(self):
        seen, stack = {0}, [0]
        while stack:
            q = stack.pop()
            for ch in self.alphabet:
                t = self.delta.get((q, ch))
                if t is not None and t not in seen:
                    seen.add(t); stack.append(t)
        return seen


def minimize(dfa):
    """Moore 算法：迭代细分等价类。"""
    reachable = dfa.reachable_states()
    # 初始划分：接受 vs 非接受
    part = {q: (1 if q in dfa.accepting else 0) for q in reachable}
    while True:
        signature = {}
        for q in sorted(reachable):
            sig = (part[q], tuple(part.get(dfa.delta.get((q, ch)), -1)
                                  for ch in dfa.alphabet))
            signature.setdefault(sig, []).append(q)
        if len(signature) == len(set(part[q] for q in reachable)):
            break
        for new_id, (sig, qs) in enumerate(sorted(signature.items())):
            for q in qs:
                part[q] = new_id
    # 按等价类重建最小 DFA
    classes = sorted(set(part[q] for q in reachable))
    remap = {c: i for i, c in enumerate(classes)}
    delta_m, acc_m = {}, set()
    for q in reachable:
        for ch in dfa.alphabet:
            t = dfa.delta.get((q, ch))
            if t is not None:
                delta_m[(remap[part[q]], ch)] = remap[part[t]]
    for q in reachable:
        if q in dfa.accepting:
            acc_m.add(remap[part[q]])
    n_min = len(classes)
    # 起始状态所在类重编号为 0
    start_class = part[0]
    if start_class != 0:
        swap = {start_class: 0, 0: start_class}
        delta_m = {(swap.get(a, a), ch): swap.get(t, t) for (a, ch), t in delta_m.items()}
        acc_m = {swap.get(a, a) for a in acc_m}
    return DFA(n_min, delta_m, acc_m, dfa.alphabet)


def show_dfa(dfa, title):
    print(f"\n== {title}（{dfa.n} 个状态）==")
    for (q, ch), t in sorted(dfa.delta.items()):
        acc = "*" if q in dfa.accepting else " "
        print(f"    {acc}{q} --{ch}--> {t}")
    print("    接受态:", sorted(dfa.accepting))


# ---- 复用第788课的 Thompson 构造 ----
def tokenize(pattern):
    out = []
    for c in pattern:
        if c == "(": out.append(("LP", c))
        elif c == ")": out.append(("RP", c))
        elif c == "|": out.append(("PIPE", c))
        elif c == "*": out.append(("STAR", c))
        else: out.append(("CHAR", c))
    out.append(("EOF", ""))
    return out


def parse_regex(pattern):
    toks, pos = tokenize(pattern), [0]
    def peek(): return toks[pos[0]]
    def eat(): t = toks[pos[0]]; pos[0] += 1; return t
    def primary():
        k, v = peek()
        if k == "CHAR": eat(); return ("char", v)
        if k == "LP":
            eat(); n = expr()
            if peek()[0] == "RP": eat()
            return n
        raise SyntaxError(v)
    def star():
        n = primary()
        while peek()[0] == "STAR": eat(); n = ("star", n)
        return n
    def concat():
        nodes = [star()]
        while peek()[0] in ("CHAR", "LP"): nodes.append(star())
        return nodes[0] if len(nodes) == 1 else ("concat", nodes)
    def expr():
        n = concat()
        while peek()[0] == "PIPE": eat(); n = ("alt", n, concat())
        return n
    out = expr()
    if peek()[0] != "EOF": raise SyntaxError("多余输入")
    return out


class NFA:
    def __init__(self): self.trans = {}
    def add(self, src, sym, dst): self.trans.setdefault((src, sym), set()).add(dst)
    def epsilon_closure(self, states):
        stack, cl = list(states), set(states)
        while stack:
            s = stack.pop()
            for t in self.trans.get((s, ""), ()):
                if t not in cl: cl.add(t); stack.append(t)
        return cl


class Builder:
    def __init__(self): self.n = 0
    def new(self): self.n += 1; return f"q{self.n}"
    def build(self, node, nfa):
        k = node[0]
        if k == "char":
            s, a = self.new(), self.new(); nfa.add(s, node[1], a); return s, a
        if k == "concat":
            cs, ca = self.build(node[1][0], nfa)
            for sub in node[1][1:]:
                ns, na = self.build(sub, nfa); nfa.add(ca, "", ns); ca = na
            return cs, ca
        if k == "alt":
            s, a = self.new(), self.new()
            s1, a1 = self.build(node[1], nfa); s2, a2 = self.build(node[2], nfa)
            nfa.add(s, "", s1); nfa.add(s, "", s2)
            nfa.add(a1, "", a); nfa.add(a2, "", a)
            return s, a
        if k == "star":
            is_, ia = self.build(node[1], nfa)
            s, a = self.new(), self.new()
            nfa.add(s, "", is_); nfa.add(s, "", a)
            nfa.add(ia, "", is_); nfa.add(ia, "", a)
            return s, a
        raise ValueError(k)


def regex_to_nfa(pattern):
    nfa = NFA()
    b = Builder()
    s, a = b.build(parse_regex(pattern), nfa)
    nfa.start, nfa.accept, nfa.n = s, a, b.n
    return nfa


print("== NFA -> DFA -> 最小 DFA ==")
patterns = ["a*b", "(a|b)*abb", "(a|b)*a(a|b)", "a(a|b)*b"]
import random
rng = random.Random(3)
for pat in patterns:
    nfa = regex_to_nfa(pat)
    subsets, delta, acc, alpha = nfa_to_dfa(nfa)
    dfa = DFA(len(subsets), delta, acc, alpha)
    dmin = minimize(dfa)
    show_dfa(dfa, f"/{pat}/ 的子集构造 DFA")
    show_dfa(dmin, f"/{pat}/ 的最小 DFA")

    # 随机串等价性验证
    ok = True
    for _ in range(500):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 10)))
        if dfa.accepts(s) != dmin.accepts(s):
            ok = False; break
    print(f"    随机 500 串 DFA/最小DFA 等价={ok}")
    print(f"    状态数: NFA={nfa.n} DFA={dfa.n} 最小={dmin.n}")

print("\n== 指数爆炸与等价性 ==")
print("  (a|b)*a(a|b) 的最小 DFA 只有 3 个状态（记录「上一个字符是否 a」）")
print("  但存在正则使最小 DFA 状态数达到 2^n（如校验第 n 位）")

print("\n== 最小 DFA 唯一性 ==")
for line in (
    "  除状态命名外，语言对应的最小 DFA 是唯一的",
    "  因此可以「缓存最小 DFA」做匹配：同正则两次编译结果同构",
    "  mypy/ruff 等工具用 DFA 做静态检查，正则引擎也常预编译成 DFA",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  DFA 模拟 O(n) 无回溯，golang 的 regexp 就是 RE2→DFA 路线",
    "  Python re 是回溯式 NFA，支持反向引用但可能指数回溯（ReDoS）",
    "  子集构造按需（lazy DFA）可避免一次性 2^n 状态",
    "  与第787课 DFA 模拟、第788课 Thompson 构造构成完整正则引擎",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Hopcroft 算法（用待分裂集合驱动），对比 Moore 的迭代次数。
# 2. 给最小 DFA 增加「死态」显式表示，处理含有死态的输入。
# 3. 用「第 n 位为 1」的正则验证最小 DFA 指数爆炸。
# 4. 思考：为什么最小 DFA 对一个语言是唯一的，而 NFA 不唯一？
