# ===== 第794课：形式语言与自动机-综合案例-迷你正则引擎 =====
# 知识点：
#   - 综合串起本章：parse(788) -> Thompson NFA -> 子集构造 DFA(789) -> 最小化 -> 匹配
#   - 两条匹配路径可选：NFA 模拟（边编译边跑、支持惰性）与 DFA 模拟（编译一次跑多次）
#   - 对 re 模块做正确性与性能对照：小规模一致、大规模 DFA 线性完胜
#   - 功能子集：字符、. 任意、| 、*、+、?、() 分组；不支持反向引用/前后断言
#   - 全部标准库 + 固定 seed，纯内存、离线可运行
#   - 与第683课手写 lexer、第15章 re、第793课规则驱动形成完整光谱
# 依赖：无（标准库）


# ---------- 1) 词法 ----------
def tokenize(pattern):
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\":                          # 转义：\. \* \\ 等
            if i + 1 < len(pattern):
                out.append(("CHAR", pattern[i+1])); i += 2; continue
            raise ValueError("悬空转义符")
        if c == "(": out.append(("LP", c))
        elif c == ")": out.append(("RP", c))
        elif c == "|": out.append(("PIPE", c))
        elif c == "*": out.append(("STAR", c))
        elif c == "+": out.append(("PLUS", c))
        elif c == "?": out.append(("OPT", c))
        elif c == ".": out.append(("DOT", c))
        else: out.append(("CHAR", c))
        i += 1
    out.append(("EOF", ""))
    return out


# ---------- 2) 语法：递归下降 ----------
def parse(pattern):
    toks, pos = tokenize(pattern), [0]

    def peek(): return toks[pos[0]]
    def eat(v=None):
        t = toks[pos[0]]
        if v is not None and t[1] != v: raise SyntaxError(f"期望 {v!r}")
        pos[0] += 1; return t

    def postfix(n):
        while peek()[0] in ("STAR", "PLUS", "OPT"):
            k = eat()[0]
            n = ("star", n) if k == "STAR" else ("plus", n) if k == "PLUS" else ("opt", n)
        return n

    def primary():
        k, v = peek()
        if k == "CHAR": eat(); return ("char", v)
        if k == "DOT": eat(); return ("any",)
        if k == "LP":
            eat(); n = expr()
            if peek()[0] != "RP": raise SyntaxError("缺少 )")
            eat(); return n
        raise SyntaxError(f"意外 {v!r}")

    def concat():
        nodes = [postfix(primary())]
        while peek()[0] in ("CHAR", "LP", "DOT"):
            nodes.append(postfix(primary()))
        return nodes[0] if len(nodes) == 1 else ("concat", nodes)

    def expr():
        n = concat()
        while peek()[0] == "PIPE":
            eat(); n = ("alt", n, concat())
        return n

    out = expr()
    if peek()[0] != "EOF": raise SyntaxError("多余输入")
    return out


# ---------- 3) NFA ----------
class NFA:
    def __init__(self):
        self.trans = {}
        self.count = 0

    def new(self):
        self.count += 1
        return self.count - 1

    def add(self, s, sym, d): self.trans.setdefault((s, sym), set()).add(d)

    def closure(self, states):
        stack, cl = list(states), set(states)
        while stack:
            s = stack.pop()
            for t in self.trans.get((s, ""), ()):
                if t not in cl: cl.add(t); stack.append(t)
        return cl

    def accepts(self, s):
        cur = self.closure({self.start})
        for ch in s:
            cur = self.closure({d for q in cur for d in self.trans.get((q, ch), ())})
            if not cur: return False
        return self.accept in cur


def build_nfa(node, nfa):
    k = node[0]
    if k == "char":
        s, a = nfa.new(), nfa.new(); nfa.add(s, node[1], a); return s, a
    if k == "any":
        # 简化：任意 = a|b（本引擎字母表只演示 a/b/c）
        s, a = nfa.new(), nfa.new()
        for c in "abc": nfa.add(s, c, a)
        return s, a
    if k == "concat":
        cs, ca = build_nfa(node[1][0], nfa)
        for sub in node[1][1:]:
            ns, na = build_nfa(sub, nfa); nfa.add(ca, "", ns); ca = na
        return cs, ca
    if k == "alt":
        s, a = nfa.new(), nfa.new()
        s1, a1 = build_nfa(node[1], nfa); s2, a2 = build_nfa(node[2], nfa)
        nfa.add(s, "", s1); nfa.add(s, "", s2)
        nfa.add(a1, "", a); nfa.add(a2, "", a)
        return s, a
    if k == "star":
        is_, ia = build_nfa(node[1], nfa)
        s, a = nfa.new(), nfa.new()
        nfa.add(s, "", is_); nfa.add(s, "", a)
        nfa.add(ia, "", is_); nfa.add(ia, "", a)
        return s, a
    if k == "plus":                          # a+ = a·a*
        s1, a1 = build_nfa(node[1], nfa)
        s2, a2 = build_nfa(("star", node[1]), nfa)
        nfa.add(a1, "", s2)
        return s1, a2
    if k == "opt":                           # a? = a|ε
        s1, a1 = build_nfa(node[1], nfa)
        s, a = nfa.new(), nfa.new()
        nfa.add(s, "", s1); nfa.add(s, "", a)
        nfa.add(a1, "", a)
        return s, a
    raise ValueError(k)


def compile_nfa(pattern):
    nfa = NFA()
    s, a = build_nfa(parse(pattern), nfa)
    nfa.start, nfa.accept = s, a
    return nfa


# ---------- 4) DFA ----------
def compile_dfa(nfa, alphabet="abc"):
    start = frozenset(nfa.closure({nfa.start}))
    states, order, delta = {start: 0}, [start], {}
    i = 0
    while i < len(order):
        sub = order[i]; i += 1
        for ch in alphabet:
            nxt = {d for q in sub for d in nfa.trans.get((q, ch), ())}
            cl = frozenset(nfa.closure(nxt)) if nxt else frozenset()
            if not cl: continue
            if cl not in states:
                states[cl] = len(order); order.append(cl)
            delta[(states[sub], ch)] = states[cl]
    accepting = {idx for sub, idx in states.items() if nfa.accept in sub}
    return delta, accepting, len(states)


class Regex:
    """编译一次，多种方式匹配。"""

    def __init__(self, pattern):
        self.pattern = pattern
        self.nfa = compile_nfa(pattern)
        self.delta, self.accepting, self.n_dfa = compile_dfa(self.nfa)

    def match_nfa(self, s):
        return self.nfa.accepts(s)

    def match_dfa(self, s):
        q = 0
        for ch in s:
            q = self.delta.get((q, ch))
            if q is None: return False
        return q in self.accepting

    def match_re(self, s):
        import re
        # 把本引擎的语法子集翻译给 re 验证等价性
        return bool(re.fullmatch(self.pattern.replace(".", "."), s))


print("== 编译产物 ==")
r = Regex("(a|b)*abb")
print(f"  模式: {r.pattern!r}")
print(f"  NFA 状态 {r.nfa.count} -> DFA 状态 {r.n_dfa}")

print("\n== 三种匹配方式等价 ==")
tests = ["abb", "aabb", "babb", "ab", "aababb", "b", "abbabb", ""]
for s in tests:
    n = r.match_nfa(s)
    d = r.match_dfa(s)
    re_ok = __import__("re").fullmatch(r.pattern, s) is not None
    print(f"  {s!r:<10} NFA={n!s:<5} DFA={d!s:<5} re={re_ok!s:<5} 一致={n==d==re_ok}")

print("\n== 更多模式与用例 ==")
CASES = [
    ("a*b*c*", ["", "abc", "aabbcc", "cba"]),
    ("(a|b)+", ["a", "ab", "bba", ""]),
    ("a?b?c?", ["", "abc", "ac", "aabb"]),
    ("(ab)*", ["", "ab", "abab", "aba"]),
    ("a|b*c", ["c", "bc", "bbc", "ab"]),
]
rng_ok = True
for pat, strs in CASES:
    rx = Regex(pat)
    for s in strs:
        n, d = rx.match_nfa(s), rx.match_dfa(s)
        import re as _re
        ref = _re.fullmatch(pat, s) is not None
        if not (n == d == ref):
            rng_ok = False
            print(f"  不一致: /{pat}/ 与 {s!r}: NFA={n} DFA={d} re={ref}")
print(f"  5 个模式 × 共 {sum(len(x[1]) for x in CASES)} 个用例 全部三种方式一致: {rng_ok}")

print("\n== 性能：NFA 模拟 vs DFA vs 回溯 re ==")
import time
import re as _re
n = 300
long_a = "a" * n + "b"          # (a|b)*abb 需要看结尾
for label, fn in (("NFA 模拟", lambda: r.match_nfa(long_a)),
                  ("DFA 模拟", lambda: r.match_dfa(long_a)),
                  ("re 回溯", lambda: bool(_re.fullmatch(r.pattern, long_a)))):
    t0 = time.perf_counter()
    for _ in range(20): fn()
    dt = (time.perf_counter()-t0)/20*1000
    print(f"  {label:<10} 长度 {len(long_a)}: {dt:>7.3f} ms/次")
print("  回溯式 re 在此模式上还好；换成 (a+)+b 这类就会指数爆炸（第792课）")

print("\n== 分层回顾 ==")
for line in [
    "  词法    : 字符流 -> token（第683课 / 第793课规则驱动）",
    "  语法    : token -> AST（第684课递归下降 / 第794课本课）",
    "  自动机  : AST -> Thompson NFA -> 子集 DFA -> 最小化（第788/789课）",
    "  匹配    : NFA 集合模拟 或 DFA 逐字符（两者等价）",
    "  验证    : 与 re 模块对照，全部一致才可信",
    "  层级    : 正则 ⊂ 上下文无关（第790课）⊂ 图灵可计算（第791课）",
]:
    print("  -", line)

print("\n== 局限 ==")
for line in [
    "  不支持反向引用 \\1（那是「非正则」能力，DFA 表达不了）",
    "  不支持环视 (?=...)（需带回溯或带前瞻的扩展自动机）",
    "  字母表固定为 a/b/c；通用引擎在编译期收集字母表",
    "  Rust regex / golang regexp 与本引擎同路线：DFA、线性、无回溯",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 支持字符类 [abc0-9]：解析成「任选其一」的 alt 子树。
# 2. 记录 DFA 的匹配位置：实现 fullmatch 与 search（任意起点开始）。
# 3. 实现惰性 DFA：按需构造状态而非一次性全建，统计实际用到的状态数。
# 4. 思考：为什么正则引擎选 DFA 路线就不能支持反向引用？
