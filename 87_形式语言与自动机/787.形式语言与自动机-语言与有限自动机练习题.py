# ===== 第787课：形式语言与自动机-语言与有限自动机 =====
# 知识点：
#   - 形式语言三要素：字母表 Σ、字符串、语言（串的集合，可为无限）
#   - 确定性有限自动机 DFA：五元组 (Q, Σ, δ, q0, F)；δ 每步唯一转移
#   - DFA 接受语言 = 从 q0 读完整串后落在接受态的所有串
#   - 正则语言：能用 DFA/正则表达式描述的语言；正则引擎本质就是自动机
#   - 与第747/748课关系：AST/三地址码是「编译器视角」，DFA 是「识别器视角」
#   - 本课手写 DFA 模拟器并构造 4 个经典自动机（奇偶 1、二进制模 3、状态机协议、词法识别）
# 依赖：无（标准库）


class DFA:
    def __init__(self, states, alphabet, delta, start, accepting):
        self.states, self.alphabet = states, alphabet
        self.delta, self.start, self.accepting = delta, start, accepting

    def step(self, state, ch):
        """单步转移；未定义转移进入死态 None。"""
        return self.delta.get((state, ch))

    def accepts(self, s):
        q = self.start
        for ch in s:
            if ch not in self.alphabet:
                return False
            q = self.step(q, ch)
            if q is None:
                return False
        return q in self.accepting

    def trace(self, s):
        q = self.start
        path = [(q, "")]
        for ch in s:
            q = self.step(q, ch)
            if q is None:
                path.append((None, ch)); break
            path.append((q, ch))
        return path


def dfa_even_ones():
    """接受「1 的个数为偶数」的二进制串。"""
    delta = {("even","0"):"even", ("even","1"):"odd",
             ("odd","0"):"odd",  ("odd","1"):"even"}
    return DFA({"even","odd"}, {"0","1"}, delta, "even", {"even"})


def dfa_mod3():
    """接受「二进制值 mod 3 == 0」的串：转移即 (2*状态+位) mod 3。"""
    delta = {}
    for s in range(3):
        for bit in "01":
            delta[(str(s), bit)] = str((2*s + int(bit)) % 3)
    return DFA({"0","1","2"}, {"0","1"}, delta, "0", {"0"})


print("== DFA 1：1 的个数为偶数 ==")
m1 = dfa_even_ones()
for s in ("", "1", "11", "1011", "101", "1110"):
    print(f"  accepts({s!r:<7}) = {m1.accepts(s)}")
print("  轨迹 '1011':", m1.trace("1011"))
print("  死态演示（字母表外的输入）:", m1.accepts("102"))

print("\n== DFA 2：二进制模 3 ==")
m2 = dfa_mod3()
for s in ("0", "11", "110", "1001", "1100", "101"):
    val = int(s, 2) if s else 0
    print(f"  {s:<6} (值={val:>4}) mod3={val%3} -> 接受={m2.accepts(s)}")
print("  读串的过程 = 数字左移一位再加新位，状态就是 mod 3 的余数")

print("\n== DFA 3：简单协议状态机（消息队列） ==")
delta = {
    ("idle","open"):"open_ok", ("idle","close"):"error",
    ("open_ok","put"):"open_ok", ("open_ok","close"):"closed",
    ("open_ok","open"):"error",
    ("closed","open"):"open_ok", ("closed","close"):"error",
}
proto = DFA(dict(delta), set(), delta, "idle", {"closed"})
for seq in ("open put put close", "open close", "open open", "put close"):
    ops = seq.split()
    q, dead = proto.start, False
    for op in ops:
        q = proto.step(q, op)
        if q is None: dead = True; break
    print(f"  {seq:<20} -> 终态={q} 合法={not dead}")

print("\n== DFA 4：识别标识符（词法器的核心） ==")
delta_id = {}
for c in "abcdefghijklmnopqrstuvwxyz_":
    delta_id[("start", c)] = "in_ident"
    delta_id[("in_ident", c)] = "in_ident"
for c in "0123456789":
    delta_id[("in_ident", c)] = "in_ident"
lexer_dfa = DFA(set(delta_id), set(), delta_id, "start", {"in_ident"})
for s in ("x", "count_1", "_tmp", "9abc", "a-b"):
    print(f"  {s!r:<10} 是合法标识符 = {lexer_dfa.accepts(s)}")
print("  真实词法器（第683课）就是几十个这样的 DFA 并行运行")

print("\n== 确定性 vs 非确定性 ==")
for line in (
    "  DFA: 每个 (状态,字符) 恰好一个后继；模拟 O(n)",
    "  NFA: 允许多个后继/ε 转移；模拟需并行跟踪状态集合",
    "  关键定理：NFA 与 DFA 能力等价（子集构造，第789课）",
    "  Kleene 定理：正则表达式 ↔ 有限自动机（第788课）",
):
    print(" ", line)

print("\n== 闭包性质（正则语言对运算封闭） ==")
for line in (
    "  并 ∪ / 连接 · / 星号 *：正则语言经这些运算仍是正则的",
    "  交 ∩、补 ‾：对 DFA 取接受态补集即得补语言，再与另一 DFA 笛卡尔积",
    "  判空、判等、包含问题都可判定（DFA 是有限对象）",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 构造接受「以 ab 结尾」串的 DFA，并给出接受/拒绝轨迹。
# 2. 实现两个 DFA 的笛卡尔积（交运算），验证 L1 ∩ L2。
# 3. 写一个 DFA 最长前缀匹配函数（词法器需要）。
# 4. 思考：为什么 DFA 不能「数任意多个括号」？（提示：状态有限）
