# ===== 第793课：形式语言与自动机-词法分析器生成 =====
# 知识点：
#   - 词法分析器生成器：给一组「规则 -> 匹配长度」的规则表，自动生成分词器
#   - 冲突消解规则：最长匹配优先；同长时规则表靠前的优先（关键字优先于标识符）
#   - 规则表驱动的价值：改一条规则只改数据；手写 lexer 改规则要改代码
#   - 空匹配规则必须拒绝，否则分词器死循环
#   - 生产工具（flex/re2c）会把规则表合并成一个 DFA 再生成代码（第789课）
#   - 本课实现一个约 80 行的迷你 lex：关键字/标识符/数字/字符串字面量
# 依赖：无（标准库）
import string

KEYWORDS = ("if", "else", "while", "true", "false")


class Rule:
    """规则 = 名字 + 匹配函数（返回最长匹配长度）+ 优先级。"""

    def __init__(self, name, match_fn, priority):
        self.name, self.match_fn, self.priority = name, match_fn, priority

    def match_len(self, text, pos):
        return self.match_fn(text, pos)


def keyword_rule(name, kw):
    def match(text, pos):
        if text.startswith(kw, pos):
            end = pos + len(kw)
            # 关键字后不能直接跟字母/数字/下划线，否则是标识符前缀
            if end < len(text) and (text[end].isalnum() or text[end] == "_"):
                return 0
            return len(kw)
        return 0
    return Rule(name, match, priority=1)


def ident_rule():
    def match(text, pos):
        i = pos
        while i < len(text) and (text[i].isalnum() or text[i] == "_"):
            i += 1
        return i - pos
    return Rule("IDENT", match, priority=9)


def number_rule():
    def match(text, pos):
        i = pos
        while i < len(text) and text[i].isdigit():
            i += 1
        return i - pos
    return Rule("NUMBER", match, priority=5)


def string_rule():
    def match(text, pos):
        if pos >= len(text) or text[pos] != '"':
            return 0
        i = pos + 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == '"':
                return i - pos + 1
            i += 1
        return 0                        # 未闭合
    return Rule("STRING", match, priority=5)


def op_rule():
    OPS = ("==", "!=", "<=", ">=", "**", "//", "+", "-", "*", "/", "%",
           "<", ">", "=", "(", ")", "{", "}", ",", ";", ":", ".")
    def match(text, pos):
        for op in OPS:                  # 双字符运算符排在前面优先尝试
            if text.startswith(op, pos):
                return len(op)
        return 0
    return Rule("OP", match, priority=3)


def ws_rule():
    def match(text, pos):
        i = pos
        while i < len(text) and text[i].isspace():
            i += 1
        return i - pos
    return Rule("WS", match, priority=0)


RULES = [
    *[keyword_rule(n, k) for n, k in
      (("IF", "if"), ("ELSE", "else"), ("WHILE", "while"),
       ("TRUE", "true"), ("FALSE", "false"))],
    number_rule(), string_rule(), op_rule(), ident_rule(), ws_rule(),
]
RULES.sort(key=lambda r: r.priority)


def tokenize(text, rules=None, max_pos=None):
    rules = rules or RULES
    end = len(text) if max_pos is None else max_pos
    out, pos = [], 0
    line, col = 1, 1
    while pos < end:
        best, best_len = None, 0
        for r in rules:
            L = r.match_len(text, pos)
            if L > best_len:            # 最长匹配优先（规则已按 priority 排序）
                best, best_len = r, L
        if best is None or best_len == 0:
            raise ValueError(f"第 {line}:{col} 无法识别 {text[pos]!r}")
        value = text[pos:pos+best_len]
        if best.name == "STRING":
            # 字符串可能跨行
            line += value.count("\n")
        out.append((best.name, value, line, col))
        if best.name == "WS":
            if "\n" in value:
                line += value.count("\n")
                col = len(value.rsplit("\n", 1)[-1]) + 1
            else:
                col += best_len
        else:
            col += best_len
        pos += best_len
    return out


src = 'while count_1 <= 42 and flag == true:\n    msg = "hi\\n" + name(3)'
print("== 源码 ==")
print(" ", src)
print("\n== token 流 ==")
for tok in tokenize(src):
    print(f"  {tok[0]:<8} {tok[1]!r:<18} L{tok[2]}:{tok[3]}")

print("\n== 冲突消解：最长匹配优先 ==")
for s in ("ifx", "if", "iffy"):
    toks = [(t[0], t[1]) for t in tokenize(s)]
    print(f"  {s!r:<8} -> {toks}")
print("  'ifx' 是一个 IDENT（最长匹配），'if' 是 IF（关键字优先）")

print("\n== 错误恢复：跳过非法字符继续分词 ==")
def tokenize_lenient(text):
    """非法字符处跳过 1 个字符并记录错误，其余正常分词（IDE 常用策略）。"""
    out, errors = [], []
    pos = 0
    while pos < len(text):
        best, best_len = None, 0
        for r in RULES:
            L = r.match_len(text, pos)
            if L > best_len:
                best, best_len = r, L
        if best is None or best_len == 0:
            errors.append((pos, text[pos]))
            pos += 1                                    # 跳过非法字符
            continue
        out.append((best.name, text[pos:pos+best_len]))
        pos += best_len
    return out, errors

toks, errs = tokenize_lenient("x = 1 @ y = 2")
print("  宽松分词结果:", toks)
print("  错误记录:", errs)
print("  严格模式会直接抛异常；IDE 场景需要宽松模式继续收集后续 token")

print("\n== 规则表驱动 vs 手写 ==")
for line in (
    "  手写 lexer（第683课）: 快、可控，但规则改动要重写代码",
    "  规则表驱动: 增删规则只动数据，代价是每个位置都要试所有规则",
    "  生产方案: 构建期把规则合并成单个 DFA（第789课），运行时 O(n) 且无回溯",
    "  flex/re2c/tree-sitter 都是「规则表 → 生成代码」的工具",
):
    print(" ", line)

print("\n== 词法规则的顺序陷阱 ==")
for line in [
    "  双字符运算符必须排在单字符之前（== vs =）",
    "  关键字用 priority=1 排在 IDENT(9) 之前，靠优先级而不是顺序碰运气",
    "  注释通常在 lexer 里直接吞掉，不产生 token",
    "  行号/列号要按「原始文本位置」记录，跳过空白时也要累计",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给规则表加「注释规则」（// 到行尾），验证注释不出现在 token 流里。
# 2. 把规则表的匹配函数换成真正的 NFA（第788课），并用最长匹配消解冲突。
# 3. 实现「缩进感知」：记录 INDENT/DEDENT token（Python 语法需要）。
# 4. 思考：为什么词法分析用「最长匹配」而语法分析用「向前看符号集合」？
