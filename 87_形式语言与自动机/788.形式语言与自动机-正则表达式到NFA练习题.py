# ===== 第788课：形式语言与自动机-正则表达式到NFA =====
# 知识点：
#   - 正则表达式三种基本运算：连接 ab、选择 a|b、星号 a*
#   - Thompson 构造：每个子表达式对应一个小 NFA 片段，按结构拼接
#   - NFA 允许 ε 转移（不读字符就能跳），状态可以有多个后继
#   - 模拟 NFA：维护「当前状态集合」，读字符后做 ε-闭包
#   - ε-闭包：从一组状态出发只走 ε 边能到达的全部状态
#   - 与第15章 re 模块互补：这里看正则引擎的内部构造
# 依赖：无（标准库）


def tokenize(pattern):
    out = []
    for c in pattern:
        if c == "(": out.append(("LP", c))
        elif c == ")": out.append(("RP", c))
        elif c == "|": out.append(("PIPE", c))
        elif c == "*": out.append(("STAR", c))
        elif c == ".": out.append(("DOT", c))
        else: out.append(("CHAR", c))
    out.append(("EOF", ""))
    return out


def parse_regex(pattern):
    """极简递归下降解析：仅支持 字符、. 任意、| 选择、* 星号、() 分组。"""
    toks = tokenize(pattern)
    pos = [0]

    def peek(): return toks[pos[0]]

    def eat(v=None):
        t = toks[pos[0]]
        if v is not None and t[1] != v:
            raise SyntaxError(f"期望 {v!r}，实际 {t[1]!r}")
        pos[0] += 1
        return t

    def primary():
        k, v = peek()
        if k == "CHAR": eat(); return ("char", v)
        if k == "DOT": eat(); return ("any",)
        if k == "LP":
            eat(); n = expr()
            if peek()[0] == "RP": eat()
            else: raise SyntaxError("缺少 )")
            return n
        raise SyntaxError(f"意外字符 {v!r}")

    def star():
        n = primary()
        while peek()[0] == "STAR":
            eat(); n = ("star", n)
        return n

    def concat():
        nodes = [star()]
        while peek()[0] in ("CHAR", "LP", "DOT"):
            nodes.append(star())
        return nodes[0] if len(nodes) == 1 else ("concat", nodes)

    def expr():
        n = concat()
        while peek()[0] == "PIPE":
            eat(); n = ("alt", n, concat())
        return n

    out = expr()
    if peek()[0] != "EOF":
        raise SyntaxError(f"多余输入 {peek()[1]!r}")
    return out


# ---------- Thompson 构造 ----------
class NFA:
    def __init__(self, start, accept):
        self.start, self.accept = start, accept
        self.trans = {}          # (state, symbol) -> set(states)；symbol="" 表示 ε
        self.n_states = 0

    def add(self, src, sym, dst):
        self.trans.setdefault((src, sym), set()).add(dst)

    def epsilon_closure(self, states):
        stack, closure = list(states), set(states)
        while stack:
            s = stack.pop()
            for t in self.trans.get((s, ""), ()):
                if t not in closure:
                    closure.add(t); stack.append(t)
        return closure

    def accepts(self, s):
        cur = self.epsilon_closure({self.start})
        for ch in s:
            nxt = set()
            for q in cur:
                nxt |= self.trans.get((q, ch), set())
            cur = self.epsilon_closure(nxt)
            if not cur:
                return False
        return self.accept in cur


class Builder:
    """递归遍历 AST；每个片段返回 (start, accept)，转移写入共享字典。"""

    def __init__(self):
        self.n = 0

    def new_state(self):
        self.n += 1
        return f"q{self.n}"

    def build(self, node, nfa):
        k = node[0]
        if k == "char":
            s, a = self.new_state(), self.new_state()
            nfa.add(s, node[1], a)
            return s, a
        if k == "any":
            s, a = self.new_state(), self.new_state()
            for c in "ab":
                nfa.add(s, c, a)
            return s, a
        if k == "concat":
            cur_s, cur_a = self.build(node[1][0], nfa)
            for sub in node[1][1:]:
                ns, na = self.build(sub, nfa)
                nfa.add(cur_a, "", ns)
                cur_a = na
            return cur_s, cur_a
        if k == "alt":
            s, a = self.new_state(), self.new_state()
            s1, a1 = self.build(node[1], nfa)
            s2, a2 = self.build(node[2], nfa)
            nfa.add(s, "", s1); nfa.add(s, "", s2)
            nfa.add(a1, "", a); nfa.add(a2, "", a)
            return s, a
        if k == "star":
            inner_s, inner_a = self.build(node[1], nfa)
            s, a = self.new_state(), self.new_state()
            nfa.add(s, "", inner_s); nfa.add(s, "", a)
            nfa.add(inner_a, "", inner_s); nfa.add(inner_a, "", a)
            return s, a
        raise ValueError(k)


def regex_to_nfa(pattern):
    ast = parse_regex(pattern)
    b = Builder()
    nfa = NFA(None, None)
    s, a = b.build(ast, nfa)
    nfa.start, nfa.accept = s, a
    nfa.n_states = b.n
    return nfa


print("== 解析树 ==")
for pat in ("ab", "a|b", "a*b", "(a|b)*"):
    print(f"  {pat:<8} -> {parse_regex(pat)}")

print("\n== Thompson NFA 模拟 ==")
CASES = [
    ("ab",   [("ab", True), ("a", False), ("aab", False), ("ba", False)]),
    ("a|b",  [("a", True), ("b", True), ("c", False)]),
    ("a*b",  [("b", True), ("ab", True), ("aaab", True), ("ba", False)]),
    ("(a|b)*abb", [("abb", True), ("aabb", True), ("babb", True), ("ab", False)]),
]
for pat, tests in CASES:
    nfa = regex_to_nfa(pat)
    print(f"  /{pat}/  状态数={nfa.n_states}")
    for s, expect in tests:
        got = nfa.accepts(s)
        print(f"    accepts({s!r:<8}) = {got!s:<5} 期望={expect} "
              f"{'OK' if got == expect else '不符'}")

print("\n== ε-闭包演示 ==")
nfa = regex_to_nfa("a*b")
before = nfa.epsilon_closure({nfa.start})
after = nfa.epsilon_closure({q for q in before if nfa.trans.get((q, "a"))})
print("  初始 ε-闭包:", sorted(before))
print("  读 'a' 后闭包:", sorted(after))
print("  ε 转移不消耗字符，所以每步读字符前后都要做闭包")

print("\n== 转移表 ==")
nfa = regex_to_nfa("a|b")
for (src, sym), dsts in sorted(nfa.trans.items()):
    print(f"    {src:<5} --{'ε' if sym == '' else sym}--> {sorted(dsts)}")

print("\n== 与 re 模块对照 ==")
import re
for pat, s in (("a*b", "aaab"), ("(a|b)*abb", "babb"), ("a|b", "c")):
    print(f"  /{pat}/ 与 {s!r}: 自研={regex_to_nfa(pat).accepts(s)} "
          f"re.match={bool(re.fullmatch(pat, s))}")

print("\n== 正则语言的层次 ==")
for line in (
    "  正则语言（有限自动机）⊂ 上下文无关（栈）⊂ 可计算（图灵机）",
    "  正则表达式不能「数括号」：a^n b^n 不是正则语言（第791课泵引理说明）",
    "  连接、|、* 三种运算已完备表达所有正则语言（Kleene 定理）",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 扩展语法支持字符类 [abc] 和 + （一次或多次）。
# 2. 实现「最长匹配」：记录每个位置是否可接受，取最后可接受的位置。
# 3. 统计 Thompson 构造的状态数与正则长度的关系。
# 4. 思考：为什么 NFA 需要 ε 转移？能否用「预合并」避免？
