# ===== 第792课：形式语言与自动机-DFA最小化的实战应用 =====
# 知识点：
#   - 把 DFA 思想用到真实工程：输入校验、状态机协议、文本扫描
#   - 三个实战场景：表单校验器、支付流程状态机、敏感词扫描
#   - 与第72课工作流/状态机的区别：那里是「业务流程」，这里是「语言识别」
#   - 与第750课数据流分析：编译器用 DFA 做词法，用数据流做优化
#   - DFA 与回溯引擎对比：DFA 无 ReDoS（指数回溯）风险
#   - 本课把 DFA 包装成可复用的校验器类，并演示 ReDoS 场景差异
# 依赖：无（标准库）
import re
import time

EPS = 1e-9


class DFAValidator:
    """把 DFA 包装成「输入校验器」：接受/拒绝 + 最长合法前缀。"""

    def __init__(self, delta, start, accepting, alphabet):
        self.delta, self.start = delta, start
        self.accepting, self.alphabet = accepting, alphabet

    def validate(self, s):
        q, last_ok = self.start, 0
        if self.start in self.accepting:
            last_ok = 0
        for i, ch in enumerate(s, 1):
            q = self.delta.get((q, ch))
            if q is None:
                return False, last_ok, f"第 {i} 个字符 {ch!r} 非法"
            if q in self.accepting:
                last_ok = i
        return q in self.accepting, last_ok, "完整匹配" if q in self.accepting else "未达接受态"

    def longest_prefix(self, s):
        """返回最长合法前缀长度（词法器分词用）。"""
        q, best = self.start, 0
        if self.start in self.accepting:
            best = 0
        for i, ch in enumerate(s, 1):
            q = self.delta.get((q, ch))
            if q is None:
                break
            if q in self.accepting:
                best = i
        return best


# ---- 场景 1：密码强度状态机（规则序列化） ----
def password_dfa(require_upper=True, require_digit=True, require_special=True):
    """状态编码：2 位 = (是否已有大写, 是否已有数字)；特殊字符独立检查。"""
    # 简化：只用「字母走过、数字走过、特殊走过」三计数状态组合
    states = []
    for up in (0, 1):
        for dig in (0, 1):
            for spc in (0, 1):
                states.append((up, dig, spc))
    delta = {}
    import string
    for st in states:
        for c in (string.ascii_letters + string.digits + "!@#$%^&*"):
            up, dig, spc = st
            if c.isupper(): up = 1
            if c.isdigit(): dig = 1
            if c in "!@#$%^&*": spc = 1
            delta[(st, c)] = (up, dig, spc)
    accepting = {(1, 1, 1)}
    start = (0, 0, 0)
    alphabet = set(string.ascii_letters + string.digits + "!@#$%^&*")
    return DFAValidator(delta, start, accepting, alphabet)


pv = password_dfa()
print("== 场景 1：密码强度（3 项要求的状态机编码）==")
for pw in ("abc", "aB1", "Abcdef1!", "AB1!", "aB1!"):
    ok, prefix, msg = pv.validate(pw)
    print(f"  {pw!r:<14} 合法={ok}  最长合法前缀={prefix}  {msg}")
print("  把「满足 3 条要求」编码成 2^3 状态组合，比一堆 if 更可审计")

# ---- 场景 2：支付流程状态机（拒绝非法序列） ----
PAY_DELTA = {
    ("INIT", "create"): "PENDING",
    ("PENDING", "pay"): "PAID",
    ("PENDING", "cancel"): "CANCELLED",
    ("PENDING", "expire"): "EXPIRED",
    ("PAID", "ship"): "SHIPPED",
    ("PAID", "refund"): "REFUNDED",
    ("SHIPPED", "deliver"): "DONE",
    ("REFUNDED", "ship"): "SHIPPED",
}
pay_dfa = DFAValidator(PAY_DELTA, "INIT", {"DONE"}, set())
print("\n== 场景 2：订单状态机（非法转移直接拒绝）==")
for seq in ("create pay ship deliver", "create ship deliver",
            "create pay refund ship deliver", "create cancel", "create"):
    ok, prefix, msg = pay_dfa.validate(seq)
    print(f"  {seq!r:<34} -> 合法={ok} {msg}")
print("  状态机让「非法操作」在规则层就被拒绝，而不是散落在业务代码里")

# ---- 场景 3：敏感词扫描（最长前缀分词思路） ----
WORDS = ["bad", "worse", "word", "worsest"]
delta_w, accepting_w = {}, set()
for w in WORDS:
    for i, c in enumerate(w):
        prefix = w[:i+1]
        if prefix == w:
            accepting_w.add(prefix)
        # 状态 = 当前已匹配前缀
        if i == 0:
            delta_w[("start", c)] = prefix
        else:
            delta_w[(w[:i], c)] = prefix
scanner = DFAValidator(delta_w, "start", accepting_w, set())
print("\n== 场景 3：敏感词扫描（最长前缀）==")
for s in ("this is bad", "worsest case", "no issue here", "worst case"):
    found = []
    i = 0
    while i < len(s):
        lp = scanner.longest_prefix(s[i:])
        if lp > 0:
            found.append(s[i:i+lp])
            i += lp
        else:
            i += 1
    print(f"  {s!r:<18} -> 命中={found}")

print("\n== ReDoS：回溯引擎 vs DFA ==")
def dfa_match_a_plus_b(s):
    """DFA：接受 a+ 后跟一个 b（与 (a+)+b 语言等价的最小 DFA）。"""
    delta = {(0, "a"): 1, (1, "a"): 1, (1, "b"): 2}
    q = 0
    for ch in s:
        q = delta.get((q, ch), 3)      # 3 = 死态
    return q == 2

evil_pattern = r"(a+)+$"            # 指数回溯的经典陷阱
# 用小规模输入实测（更大的输入会指数增长卡死，切勿在生产环境尝试）
print(f"  {'输入 a 个数':<12}{'回溯引擎耗时':>14}{'DFA 扫描耗时':>14}")
for n in (16, 18, 20, 22):
    s = "a" * n + "b"
    t0 = time.perf_counter()
    re.match(evil_pattern, s)
    t_backtrack = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    dfa_match_a_plus_b(s)
    t_dfa = (time.perf_counter() - t0) * 1000
    print(f"  {n:<12}{t_backtrack:>12.1f}ms{t_dfa:>12.2f}ms")
print("  输入每 +2 个 a，回溯耗时约 ×4~6（指数级）；DFA 始终线性")
print("  输入到 30 个 a 就要数分钟，到 50 个 a 等于拒绝服务——ReDoS 攻击本质")
print("  缓解：避免嵌套量词；或用 RE2/golang regexp 这类 DFA 引擎")

print("\n== DFA 工程化小结 ==")
for line in [
    "  DFA = 「校验规则」的可执行表示，比 if/else 链更可审计",
    "  状态机协议在分布式系统里防止非法转移（第732课 Raft 三态）",
    "  词法扫描 = 最长前缀 DFA（第683课手写 lexer 的理论根基）",
    "  性能：DFA 无回溯，安全；表达能力受限是它的边界",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给密码状态机增加「长度至少 8 位」的终止判定。
# 2. 把订单状态机导出成 Mermaid 状态图，用于文档。
# 3. 构造一个会让 Python re 跑超过 5 秒的 ReDoS 输入（小规模演示，勿滥用）。
# 4. 思考：为什么「最长前缀匹配」需要记录每个可达状态是否为接受态？
