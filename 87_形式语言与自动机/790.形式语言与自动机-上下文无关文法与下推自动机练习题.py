# ===== 第790课：形式语言与自动机-上下文无关文法与下推自动机 =====
# 知识点：
#   - 上下文无关文法 CFG：产生式 A -> α|β|...；左侧单个非终结符
#   - 正则语言数不了括号：a^n b^n 需要「栈」——下推自动机 PDA
#   - 推导 derivation：从开始符号不断替换非终结符；最左推导对应解析顺序
#   - 自顶向下解析：从开始符号出发按产生式展开（递归下降第684课的本源）
#   - LL(1) 文法：向前看 1 个符号即可唯一选择产生式；冲突产生歧义文法
#   - Chomsky 层级：正则 ⊂ CFG ⊂ 上下文相关 ⊂ 递归可枚举
# 依赖：无（标准库）
from collections import defaultdict

# ---- 文法定义 ----
BALANCED = {
    "S": ["aSb", ""],                    # L = { a^n b^n }
    }
EXPR_GRAMMAR = {
    "expr": ["expr + term", "expr - term", "term"],
    "term": ["term * factor", "term / factor", "factor"],
    "factor": ["number", "( expr )"],
    }


def generate(cfg, symbol="S", depth=6, rng=None):
    """随机展开产生式，演示语言成员串的形状。"""
    import random
    rng = rng or random.Random(4)
    if depth <= 0:
        return ""
    prods = cfg[symbol]
    prod = rng.choice(prods)
    out = []
    for tok in prod.split():
        if tok in cfg:
            out.append(generate(cfg, tok, depth-1, rng))
        else:
            out.append(tok)
    return "".join(out)


def leftmost_derivation(cfg, target, symbol="S", max_steps=50):
    """尝试做最左推导生成 target（带回溯；成功返回步骤列表）。"""
    steps = []

    def inner(tokens):
        if len(steps) >= max_steps:
            return False
        # 找第一个非终结符
        i = next((i for i, t in enumerate(tokens) if t in cfg), None)
        if i is None:
            if "".join(tokens) == target:
                steps.append(list(tokens))
                return True
            return False
        for prod in cfg[tokens[i]]:
            new_tokens = tokens[:i] + prod.split() + tokens[i+1:]
            # 剪枝：已生成的字符前缀必须匹配 target 前缀
            prefix = "".join(t for t in new_tokens if t not in cfg)
            if not target.startswith(prefix):
                continue
            steps.append(list(new_tokens))
            if inner(new_tokens):
                return True
            steps.pop()
        return False

    ok = inner([symbol])
    return steps if ok else None


print("== 文法 L = { a^n b^n | n>=0 } ==")
print("  产生式: S -> aSb | ε（空串）")
import random
rng = random.Random(4)
for _ in range(6):
    print("  示例:", repr(generate(BALANCED) or "ε"))

print("\n== 最左推导：aabb ==")
steps = leftmost_derivation(BALANCED, "aabb")
if steps:
    for i, s in enumerate(steps):
        print(f"  {' ⇒ '.join(['S'] + [' '.join(x) for x in steps[:i+1]])}")
    print(f"  共 {len(steps)} 步推导")
else:
    print("  无法推导")

print("\n== 非成员串：aab（n 不相等）==")
steps_bad = leftmost_derivation(BALANCED, "aab")
print("  推导成功:", steps_bad is not None, "-> aab 不属于该语言")

print("\n== 泵引理直觉：为什么 a^n b^n 不是正则语言 ==")
for line in (
    "  假设有 DFA 接受它，状态数 k 有限",
    "  串 a^k 的读取必然重复经过某个状态（鸽巢）→ 出现环",
    "  沿环多泵几个 a 仍被接受，但此时 a 数量 > b 数量 → 矛盾",
    "  结论：有限状态「数不了无界的数量」，需要栈 → PDA",
):
    print(" ", line)

print("\n== 下推自动机 PDA 模拟：平衡括号 ==")
def pda_balanced(s):
    """栈式识别：'(' 压栈，')' 弹栈，结束时空栈且未中途弹空则接受。"""
    stack, i = [], 0
    steps = []
    for ch in s:
        if ch == "(":
            stack.append("("); steps.append((i, ch, "push", len(stack)))
        elif ch == ")":
            if not stack:
                steps.append((i, ch, "REJECT-pop-empty", 0))
                return False, steps
            stack.pop(); steps.append((i, ch, "pop", len(stack)))
        else:
            return None, steps                 # 非法字符
        i += 1
    return (len(stack) == 0), steps

for s in ("", "()", "(())", "(()", "())", "(()())", ")("):
    ok, st = pda_balanced(s)
    print(f"  {s!r:<10} -> 接受={ok}  最后几步={st[-2:]}")

print("\n== 表达式文法与 LL(1) 冲突 ==")
print("  expr -> expr + term | term   是左递归文法，递归下降会死循环")
print("  改写为右递归/提取左因子后可解析；或用运算符优先级（第684课）")
print("  LL(1) 判定：对每个非终结符，各产生式的 FIRST 集互不相交")

def first_sets(cfg):
    """计算 FIRST 集（简化：不考虑 ε 的传递闭包，两次迭代近似）。"""
    first = defaultdict(set)
    changed = True
    while changed:
        changed = False
        for sym, prods in cfg.items():
            for prod in prods:
                for tok in prod.split():
                    if tok not in cfg:          # 终结符
                        if tok not in first[sym]:
                            first[sym].add(tok); changed = True
                        break
                    else:
                        new = first[tok] - {""}
                        before = len(first[sym])
                        first[sym] |= new
                        if len(first[sym]) != before: changed = True
                        if "" not in first[tok]:
                            break
                else:
                    if "" not in first[sym]:
                        first[sym].add(""); changed = True
    return first

fs = first_sets(EXPR_GRAMMAR)
print("\n== 表达式文法的 FIRST 集 ==")
for sym in ("expr", "term", "factor"):
    print(f"  FIRST({sym}) = {sorted(fs[sym])}")
print("  expr 的两个产生式 FIRST 都含 number/( -> 存在 LL(1) 冲突（左递归所致）")

print("\n== Chomsky 层级 ==")
print(f"  {'类型':<22}{'自动机':<20}{'示例语言'}")
for row in (("3 型 正则", "有限自动机 DFA/NFA", "a*b"),
            ("2 型 上下文无关", "下推自动机 PDA", "a^n b^n、括号配对"),
            ("1 型 上下文相关", "线性有界自动机", "a^n b^n c^n"),
            ("0 型 递归可枚举", "图灵机", "一切可计算语言")):
    print(f"  {row[0]:<22}{row[1]:<20}{row[2]}")

print("\n== 与编译器的对应 ==")
for line in [
    "  词法分析用正则/DFA（第787~789课）",
    "  语法分析用 CFG：递归下降(第684课)、LL、LR/Yacc",
    "  语义分析与中间表示超出 CFG 的表达力，靠属性/动作补充",
    "  Python 的语法是 CFG，但缩进需要预处理成 INDENT/DEDENT 标记",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 写出「回文串」的 CFG，并用最左推导生成 abba。
# 2. 实现 CYK 算法（乔姆斯基范式 + 动态规划），判定任意串是否属于 CFG。
# 3. 把表达式文法改写成 LL(1) 形式（消除左递归），并重新计算 FIRST。
# 4. 思考：为什么 PDA 需要栈而 DFA 不需要？栈给了它什么能力？
