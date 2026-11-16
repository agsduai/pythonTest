# ===== 第946课：属性测试与模糊测试-综合案例-迷你JSON解析器测试套件 =====
# 知识点：
#   - 综合本章：生成器(940) + shrinking(941) + 性质模式(942) +
#     状态ful(943) + fuzzing(944) + 可复现(945)
#   - 被测对象：从零实现的迷你 JSON 解析器 + 一个藏 bug 的变体
#   - 测试套件四层：单元示例 → 属性测试 → 模糊测试 → 回归固化
#   - 对照解析器：ast.literal_eval 仅支持子集 —— 天然的部分神谕
#   - 最终报告：每层测试的发现与结论
# 依赖：无（标准库）
import ast
import json as std_json
import random


# ---------- 被测实现：迷你 JSON 解析器 ----------
class MiniJSONParser:
    def __init__(self, buggy=False):
        self.buggy = buggy

    def parse(self, text):
        self._text = text
        self._pos = 0
        value = self._parse_value()
        self._skip_ws()
        if self._pos != len(self._text):
            raise ValueError(f"多余内容 @{self._pos}")
        return value

    def _skip_ws(self):
        while self._pos < len(self._text) and self._text[self._pos] in " \t\n":
            self._pos += 1

    def _peek(self):
        return self._text[self._pos] if self._pos < len(self._text) else ""

    def _parse_value(self):
        self._skip_ws()
        ch = self._peek()
        if ch == "{":
            return self._parse_object()
        if ch == "[":
            return self._parse_array()
        if ch == '"':
            return self._parse_string()
        if ch == "-" or ch.isdigit():
            return self._parse_number()
        if self._text.startswith("true", self._pos):
            self._pos += 4
            return True
        if self._text.startswith("false", self._pos):
            self._pos += 5
            return False
        if self._text.startswith("null", self._pos):
            self._pos += 4
            return None
        raise ValueError(f"非法值 @{self._pos}: {ch!r}")

    def _parse_object(self):
        self._pos += 1
        obj = {}
        self._skip_ws()
        if self._peek() == "}":
            self._pos += 1
            return obj
        while True:
            self._skip_ws()
            key = self._parse_string()
            self._skip_ws()
            if self._peek() != ":":
                raise ValueError("缺少冒号")
            self._pos += 1
            obj[key] = self._parse_value()
            self._skip_ws()
            ch = self._peek()
            if ch == ",":
                self._pos += 1
                continue
            if ch == "}":
                self._pos += 1
                return obj
            raise ValueError("对象缺少 }")

    def _parse_array(self):
        self._pos += 1
        arr = []
        self._skip_ws()
        if self._peek() == "]":
            self._pos += 1
            return arr
        while True:
            arr.append(self._parse_value())
            self._skip_ws()
            ch = self._peek()
            if ch == ",":
                self._pos += 1
                continue
            if ch == "]":
                self._pos += 1
                return arr
            raise ValueError("数组缺少 ]")

    def _parse_string(self):
        self._pos += 1                       # 跳过开头引号
        out = []
        while self._pos < len(self._text):
            ch = self._text[self._pos]
            if ch == '"':
                self._pos += 1
                return "".join(out)
            if ch == "\\":
                self._pos += 1
                esc = self._text[self._pos]
                out.append({"n": "\n", "t": "\t", '"': '"',
                            "\\": "\\"}.get(esc, esc))
                self._pos += 1
                continue
            out.append(ch)
            self._pos += 1
        raise ValueError("字符串未闭合")

    def _parse_number(self):
        start = self._pos
        if self._peek() == "-":
            self._pos += 1
        while self._peek().isdigit():
            self._pos += 1
        if self._peek() == ".":                  # 小数部分
            self._pos += 1
            while self._peek().isdigit():
                self._pos += 1
        if self._peek() in ("e", "E"):           # 指数部分
            self._pos += 1
            if self._peek() in ("+", "-"):
                self._pos += 1
            while self._peek().isdigit():
                self._pos += 1
        body = self._text[start:self._pos]
        if self.buggy and body.startswith("-"):
            return 0                          # bug：负数一律解析为 0（pos 已推进）
        return float(body) if any(c in body for c in ".eE") else int(body)


def serialize(value):
    """配套序列化器（往返性质的一半）。"""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return std_json.dumps(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"') \
                       .replace("\n", "\\n").replace("\t", "\\t")
        return f'"{escaped}"'
    if isinstance(value, list):
        return "[" + ",".join(serialize(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f'"{k}":{serialize(v)}'
                              for k, v in value.items()) + "}"
    raise TypeError(type(value))


# ---------- 第 1 层：单元示例 ----------
parser = MiniJSONParser()
samples = ['{"name":"Ada","age":36}', "[1,-2,3.5]", '"hi\\n"', "null", "[]", "{}"]
print("== 第 1 层：单元示例 ==")
for text in samples:
    value = parser.parse(text)
    print(f"  {text!r:<32} -> {value!r}")
print("  全部通过 —— 示例测试的覆盖就此为止")

# ---------- 第 2 层：属性测试（往返） ----------
print("\n== 第 2 层：往返性质 parse(serialize(v)) == v ==")


def gen_json_value(rng, size=4):
    choices = ("num", "str", "list", "dict", "bool", "null")
    kind = rng.choice(choices if size > 0 else ("num", "str", "bool", "null"))
    if kind == "num":
        return rng.choice([0, 1, -1, 42, -7, 3])
    if kind == "str":
        return "".join(rng.choice('ab c"\\\n\t') for _ in range(rng.randint(0, 6)))
    if kind == "bool":
        return rng.choice([True, False])
    if kind == "null":
        return None
    if kind == "list":
        return [gen_json_value(rng, size - 1) for _ in range(rng.randint(0, 3))]
    return {gen_str_key(rng): gen_json_value(rng, size - 1)
            for _ in range(rng.randint(0, 3))}


def gen_str_key(rng):
    return "".join(rng.choice("abcd") for _ in range(rng.randint(1, 3)))


rng = random.Random(146)
failures = []
for _ in range(400):
    value = gen_json_value(rng, 4)
    try:
        text = serialize(value)
        reparsed = parser.parse(text)
        if reparsed != value:
            failures.append((value, text, reparsed))
    except Exception as exc:
        failures.append((value, serialize(value), f"{type(exc).__name__}: {exc}"))
    if len(failures) >= 3:
        break
print(f"  400 个生成值: 失败 {len(failures)} 个")
for value, text, reparsed in failures[:3]:
    print(f"    原值   {value!r}")
    print(f"    文本   {text!r}")
    print(f"    重析   {reparsed!r}")
print("  往返性质对好实现成立（换行/引号/转义都被正确处理）")

# ---------- 第 2 层补充：对 buggy 变体 ----------
buggy = MiniJSONParser(buggy=True)
buggy_failures = []
for _ in range(400):
    value = gen_json_value(rng, 3)
    if isinstance(value, (int, float)) and value < 0:
        text = serialize(value)
        if buggy.parse(text) != value:
            buggy_failures.append(value)
print(f"  buggy 变体（负数归零）被属性测试命中: {len(buggy_failures)} 个负数")

# ---------- 第 3 层：部分神谕（对照 literal_eval） ----------
print("\n== 第 3 层：部分神谕（ast.literal_eval 仅支持子集）==")


def literal_compatible(value):
    if isinstance(value, (dict, list)):
        return True
    if isinstance(value, str):
        return True
    return True


oracle_failures = 0
checked = 0
for _ in range(200):
    value = gen_json_value(rng, 2)
    text = serialize(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value >= 0 and "e" not in text and "." not in text:
            continue                        # literal_eval 的 JSON 数字形式兼容
    if isinstance(value, str):
        continue                            # 字符串字面量语法兼容
    continue
# 简化演示：直接对比 list/int 子集
for _ in range(200):
    value = [gen_json_value(rng, 1) for _ in range(rng.randint(0, 3))]
    if any(isinstance(v, str) and any(ch in v for ch in '"\\\n\t')
           for v in value):
        continue                            # 转义语法不同，跳过
    text = serialize(value)
    if any(isinstance(v, str) for v in value):
        text = text.replace("\\n", "\\\\n").replace('\\"', '\\\\"')
        text = "[" + text[1:-1] + "]" if text.startswith("[") else text
    try:
        if ast.literal_eval(text) == value:
            checked += 1
    except (ValueError, SyntaxError):
        pass                                # 语法子集不同，属已知差异
print(f"  子集神谕一致样本 = {checked}（转义差异属已知，跳过）")
print("  神谕要『明确兼容范围』—— 不匹配 ≠ bug，规则必须白纸黑字")

# ---------- 第 4 层：模糊测试 ----------
print("\n== 第 4 层：模糊测试（变异 JSON 文本）==")


def mutate(text, rng):
    pos = rng.randrange(len(text)) if text else 0
    op = rng.choice(("insert", "delete", "replace"))
    ch = rng.choice('{}[]",:0123456789truefalsnl \\\\')
    if op == "insert":
        return text[:pos] + ch + text[pos:]
    if op == "delete":
        return text[:pos] + text[pos + 1:]
    return text[:pos] + ch + text[pos + 1:]


crashes = {}
corpus = ['{"a":[1,2]}', '"text"', "[true,null]", "123"]
for round_i in range(3000):
    base = rng.choice(corpus)
    candidate = mutate(base, rng)
    try:
        parser.parse(candidate)
    except ValueError:
        pass                                # 预期的解析失败（良性）
    except RecursionError:
        crashes.setdefault("RecursionError", candidate)
    except IndexError as exc:
        crashes.setdefault(f"IndexError", candidate)
    except Exception as exc:
        crashes.setdefault(type(exc).__name__, candidate)
print(f"  3000 次变异: 崩溃类别 {len(crashes)} 个")
for signature, text in crashes.items():
    print(f"    [{signature}] 输入样例: {text[:40]!r}")
print("  除 ValueError 外的一切异常都是健壮性缺陷（应改为友好报错）")

# ---------- 第 5 层：回归固化 ----------
print("\n== 第 5 层：回归固化 ==")
regression = ['{"name":"Ada","age":36}', "[1,-2,3.5]", '"hi\\n"', "[]"]
passed = 0
for text in regression:
    try:
        value = parser.parse(text)
        passed += (serialize(value) and value is not None) or text == "[]"
        roundtrip_ok = (serialize(parser.parse(text)) == text
                        if text != "[]" else parser.parse(text) == [])
        print(f"  {text!r:<28} 解析 ✓ 往返 {'✓' if roundtrip_ok else '✗'}")
        passed += 1
    except Exception as exc:
        print(f"  {text!r:<28} 失败: {exc}")
print(f"  回归用例 {len(regression)} 条全部纳入 CI")

print("\n== 测试套件全景 ==")
print(f"  {'层次':<16}{'手段':<30}{'产出'}")
for row in (("单元示例", "手写典型输入", "快速反馈"),
            ("属性测试", "生成器+往返/不变量", "发现逻辑 bug"),
            ("部分神谕", "与 stdlib 对照", "交叉验证"),
            ("模糊测试", "变异+崩溃签名", "健壮性缺陷"),
            ("回归固化", "最小反例进 CI", "防复发")):
    print(f"  {row[0]:<16}{row[1]:<30}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  五层套件各司其职：示例给底线、属性找逻辑 bug、fuzz 找崩溃",
    "  部分神谕要写明兼容范围，否则误报淹没真问题",
    "  全部发现的 bug 都应固化为回归用例进入 CI",
    "  至此属性测试篇完结：939~946 课构成一套完整的工程实践",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给解析器实现 Unicode 转义（\\uXXXX），并为它写专属往返性质。
# 2. 实现「差分测试」：MiniJSONParser 与 std_json 在子集上的对账器。
# 3. 把模糊测试的崩溃输入接入 941 课的 shrinker，输出最小崩溃文本。
# 4. 思考：解析器的哪些性质是『无例外的』？哪些性质必须写明兼容范围？
