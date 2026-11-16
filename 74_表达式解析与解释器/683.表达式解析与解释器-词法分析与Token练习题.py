# ===== 第683课：表达式解析与解释器-词法分析与Token =====
# 知识点：
#   - 词法分析（lexer）：字符流 -> Token 流，是解释器/编译器的第一步
#   - Token = (类型, 字面值, 位置)；NUMBER / IDENT / OP / LPAREN / RPAREN / EOF
#   - 手写扫描器用「指针 + 分类判断」，比一堆正则更可控、能报精确位置
#   - 跳过空白、识别多字符运算符（** / // / >= / ==）、拒绝非法字符
#   - 关键字（and/or/not/true）可在词法层标记，也可留给语法层
#   - 与第660课模板扫描对比：同样是「扫描 + token」，只是语法不同
# 依赖：无（标准库）
from dataclasses import dataclass

NUMBER, IDENT, OP, LPAREN, RPAREN, COMMA, EOF = (
    "NUMBER", "IDENT", "OP", "LPAREN", "RPAREN", "COMMA", "EOF")


@dataclass
class Token:
    kind: str
    value: str
    pos: int

    def __repr__(self):
        return f"{self.kind}({self.value!r})@{self.pos}"


MULTI_OPS = ("**", "//", ">=", "<=", "==", "!=")
SINGLE_OPS = set("+-*/%^<>()=,")


def tokenize(src: str) -> list:
    tokens, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            start = i
            seen_dot = False
            while i < n and (src[i].isdigit() or (src[i] == "." and not seen_dot)):
                if src[i] == ".":
                    seen_dot = True
                i += 1
            tokens.append(Token(NUMBER, src[start:i], start))
            continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (src[i].isalnum() or src[i] == "_"):
                i += 1
            tokens.append(Token(IDENT, src[start:i], start))
            continue
        two = src[i:i + 2]
        if two in MULTI_OPS:
            tokens.append(Token(OP, two, i)); i += 2
            continue
        if c == "(":
            tokens.append(Token(LPAREN, c, i)); i += 1
        elif c == ")":
            tokens.append(Token(RPAREN, c, i)); i += 1
        elif c == ",":
            tokens.append(Token(COMMA, c, i)); i += 1
        elif c in SINGLE_OPS:
            tokens.append(Token(OP, c, i)); i += 1
        else:
            raise ValueError(f"第 {i} 列：非法字符 {c!r}")
    tokens.append(Token(EOF, "", n))
    return tokens


EXPRESSIONS = [
    "1 + 2 * 3",
    "(a + b) ** 2 // 4",
    "max(1, x, 3.14)",
    "x >= 10 and y != 0",
    "  -3.5e2 ",
]

print("== Token 流 ==")
for expr in EXPRESSIONS:
    print(f"\n  {expr!r}")
    for t in tokenize(expr):
        print("   ", t)

print("\n== 多字符运算符优先匹配 ==")
for op in ("**", "//", ">=", "==", "+", "*"):
    toks = tokenize(f"a {op} b")
    print(f"  a {op:<3} b -> {[t.value for t in toks if t.kind == OP]}")

print("\n== 数字字面量 ==")
for lit in ("42", "3.14", "0.5", ".25", "1.2.3"):
    try:
        toks = tokenize(lit)
        print(f"  {lit:<8} -> {toks[:-1]}")
    except ValueError as e:
        print(f"  {lit:<8} -> {type(e).__name__}: {e}")

print("\n== 错误定位 ==")
for bad in ("1 + @", "a $ b", "x # y"):
    try:
        tokenize(bad)
    except ValueError as e:
        print(f"  {bad!r:<10} -> {e}")

print("\n== 标识符与关键字 ==")
KEYWORDS = {"and", "or", "not", "true", "false", "if", "else"}
for name in ("x", "_tmp", "max", "and", "true", "if"):
    t = tokenize(name)[0]
    role = "关键字" if t.value in KEYWORDS else "标识符/函数名"
    print(f"  {name:<8} {t.kind:<6} -> {role}")
print("  本课把关键字识别推迟到语法层，词法层统一给 IDENT")

print("\n== lexer 的职责边界 ==")
for line in [
    "  lexer 不检查括号是否配对、不检查语法（那是 parser 的事）",
    "  lexer 只负责：切分、分类、跳过空白、拒绝非法字符、记录位置",
    "  Token 流可缓存，同一表达式多次求值无需重复扫描",
    "  为后续 Pratt/递归下降解析器提供干净输入",
]:
    print(line)

# ===== 练习题 =====
# 1. 支持科学计数法 1e-3 / 2.5E+4 的数字字面量。
# 2. 增加字符串字面量（单双引号 + 转义）的字符串 Token。
# 3. 给 Token 增加行号/列号，并在错误信息里同时报出行列。
# 4. 思考：为什么 lexer 不该负责检查括号配对？
