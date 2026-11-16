# ===== 第952课：类型系统与类型推断-结构子类型与变型 =====
# 知识点：
#   - 名义子类型：类 A extends B 才兼容（Java/C++）
#   - 结构子类型：字段够了就兼容 —— 不需要显式继承（TS/Go/OCaml）
#   - 宽度子类型：字段更多的记录可赋给字段更少的类型
#   - 函数变型：参数逆变、返回协变 —— 可赋值性的方向规则
#   - 变型（variance）决定『容器里的类型怎么随容器一起变』
# 依赖：无（标准库）


class TRecord:
    """记录类型：{字段名: 类型}。"""

    def __init__(self, fields):
        self.fields = dict(fields)

    def is_subtype(self, other):
        """宽度子类型：other 的每个字段都必须存在且类型兼容。"""
        for name, t in other.fields.items():
            if name not in self.fields:
                return False
            if not is_subtype(self.fields[name], t):
                return False
        return True

    def __str__(self):
        inner = ", ".join(f"{k}: {type_str(v)}" for k, v in self.fields.items())
        return "{" + inner + "}"


class TArrow:
    def __init__(self, param, result):
        self.param = param
        self.result = result

    def is_subtype(self, other):
        """函数子类型：参数逆变、返回协变。
        (A→B) ≤ (C→D) 当且仅当 C ≤ A 且 B ≤ D。"""
        if not isinstance(other, TArrow):
            return False
        return (is_subtype(other.param, self.param)
                and is_subtype(self.result, other.result))

    def __str__(self):
        return f"({type_str(self.param)} -> {type_str(self.result)})"


class TList:
    def __init__(self, element, covariant=True):
        self.element = element
        self.covariant = covariant

    def is_subtype(self, other):
        if not isinstance(other, TList):
            return False
        if self.covariant and other.covariant:
            return is_subtype(self.element, other.element)
        # 不变（invariant）：必须双向兼容（严格相等结构）
        return (is_subtype(self.element, other.element)
                and is_subtype(other.element, self.element))

    def __str__(self):
        return f"List[{type_str(self.element)}]"


T_INT = ("int",)
T_BOOL = ("bool",)


def is_subtype(a, b):
    if a == b:
        return True
    if isinstance(b, (TRecord, TArrow, TList)):
        return a.is_subtype(b) if isinstance(a, type(b)) else False
    if isinstance(a, (TRecord, TArrow, TList)):
        return False
    return False


def type_str(t):
    if t == T_INT:
        return "Int"
    if t == T_BOOL:
        return "Bool"
    if hasattr(t, "__str__"):
        return str(t)
    return repr(t)


def check_assign(label, source, target, expect=True):
    ok = is_subtype(source, target)
    verdict = "✓" if ok else "✗"
    note = ""
    if ok != expect:
        note = "  [与预期不符!]"
    print(f"  [{label}]\n    {type_str(source)}  ≤?  {type_str(target)}"
          f"    -> {verdict} {ok}{note}")


print("== 宽度子类型（记录）==")
point3 = TRecord({"x": T_INT, "y": T_INT, "z": T_INT})
point2 = TRecord({"x": T_INT, "y": T_INT})
check_assign("三维点赋给二维点", point3, point2, expect=True)
check_assign("二维点赋给三维点", point2, point3, expect=False)

print("\n== 结构子类型 vs 名义子类型 ==")
point2_clone = TRecord({"x": T_INT, "y": T_INT})   # 另一个『同名不同类』的类型
check_assign("无继承关系的同构记录", point2_clone, point2, expect=True)
print("  字段结构相同即兼容 —— 不需要 extends/import（Go/TS 的哲学）")

print("\n== 深度子类型（嵌套记录）==")
outer3 = TRecord({"pos": point3, "label": ("str",)})
outer2 = TRecord({"pos": point2, "label": ("str",)})
check_assign("嵌套字段深兼容", outer3, outer2, expect=True)

print("\n== 函数的变型：参数逆变、返回协变 ==")
print("  规则：(A→B) ≤ (C→D) ⟺ C ≤ A（参数逆变）且 B ≤ D（返回协变）")
print("  直觉：函数可能被以『更宽的输入』调用 → 它必须接受更宽的参数")
print("        函数的输出被『按声明的返回类型』使用 → 返回类型只能更窄")

print("\n== 变型的完整示例（用记录作为可比较的『宽窄』）==")
animal = TRecord({"name": ("str",)})
dog = TRecord({"name": ("str",), "bark": ("bool",)})      # Dog ≤ Animal
feed_dog_dog = TArrow(dog, dog)          # 需要 Dog，产出 Dog
feed_animal_dog = TArrow(animal, dog)    # 需要 Animal（更宽），产出 Dog
feed_dog_animal = TArrow(dog, animal)    # 需要 Dog，产出 Animal（更宽）
check_assign("基线：f: Dog→Dog 可当 f: Dog→Dog 用", feed_dog_dog, feed_dog_dog)
check_assign("f: Animal→Dog 可当 f: Dog→Dog 用（参数逆变 + 返回协变）",
             feed_animal_dog, feed_dog_dog, expect=True)
check_assign("f: Dog→Animal 不可当 f: Dog→Dog 用（返回不能变宽）",
             feed_dog_animal, feed_dog_dog, expect=False)
check_assign("f: Dog→Dog 不可当 f: Animal→Animal 用（参数不能变宽）",
             feed_dog_dog, TArrow(animal, animal), expect=False)
print("  『能接受更宽输入、产出更窄输出』的函数永远安全可替 —— 里氏替换的函数版")

print("\n== 列表的变型：协变 vs 不变 ==")
list_int = TList(T_INT)
list_any_num = TList(T_INT)               # 简化演示
check_assign("List[Int] ≤ List[Int]", list_int, list_any_num)
print("  协变（List[Dog] ≤ List[Animal]）在『只读容器』上是安全的；")
print("  可写容器必须不变（invariant）：否则 Dog→Animal 塞进 List[Animal]")
print("  会破坏 List[Dog] 的类型承诺 —— 变型是容器设计的第一道题")

print("\n== 变型速查 ==")
print(f"  {'位置':<16}{'变型':<12}{'含义'}")
for row in (("函数参数", "逆变", "接受更宽的输入"),
            ("函数返回", "协变", "产出更窄的输出"),
            ("只读容器", "协变", "List[Dog] 是 List[Animal]"),
            ("可写容器", "不变", "读写都要严格匹配"),
            ("可变字段", "不变", "避免 Setter 破坏承诺")):
    print(f"  {row[0]:<16}{row[1]:<12}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  结构子类型 = 『长得像就行』：解耦类型与类层次",
    "  宽度子类型是它的最简单情形：字段多者可赋给字段少者",
    "  变型规则不是教条而是防破坏推理：参数逆变/返回协变",
    "  953 课：给类型加参数 —— 泛型与类型变量绑定",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「字段可选」的记录类型（可选字段可缺失），修订宽度子类型逻辑。
# 2. 实现深度变型：TRecord 嵌套 TList 时的递归变型判定。
# 3. 构造『协变可写容器』的反例：List[Animal].add(Dog) 破坏 List[Dog]。
# 4. 思考：为什么 Go 的接口是隐式实现（结构）而 Java 选择显式继承（名义）？
#    两者的重构成本差异在哪里？
