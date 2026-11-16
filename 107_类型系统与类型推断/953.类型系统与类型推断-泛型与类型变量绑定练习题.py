# ===== 第953课：类型系统与类型推断-泛型与类型变量绑定 =====
# 知识点：
#   - 泛型 = 类型层面的函数：List[T]、Pair[A, B] 接受类型作为参数
#   - 类型变量 T 的作用域：在声明处绑定，在使用处约束
#   - 实例化：List[T] 应用到 Int → List[Int]（代换一次完成）
#   - 泛型函数的多态性与 950 课 let 多态的关系：显式 vs 推断
#   - 幻影类型（phantom type）：参数只出现在标注中 —— 把约束写进类型
# 依赖：无（标准库）


class TGeneric:
    """参数化类型：name(如 List) + 参数列表（含形式类型变量）。"""

    def __init__(self, name, args=()):
        self.name = name
        self.args = tuple(args)

    def apply(self, args):
        """实例化：实际类型按位置代换形式参数。"""
        if len(args) != len(self.args):
            raise ValueError(f"{self.name} 需要 {len(self.args)} 个类型参数")
        new_args = [args[i] if isinstance(arg, GenericVar) else arg
                    for i, arg in enumerate(self.args)]
        return TGeneric(self.name, new_args)

    def __str__(self):
        if not self.args:
            return self.name
        return f"{self.name}<{', '.join(type_str(a) for a in self.args)}>"


class GenericVar:
    """类型变量：泛型的形式参数（如 List[T] 中的 T）。"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def type_str(t):
    return str(t)


class GenericFunction:
    """泛型函数：声明类型变量 + 签名 + 推导规则。"""

    def __init__(self, name, type_vars, params, result):
        self.name = name
        self.type_vars = type_vars            # ["T"]
        self.params = params                  # [("x", 类型含 T)]
        self.result = result                  # 返回类型（含 T）

    def instantiate(self, args):
        """调用时：用实际类型代换类型变量。"""
        mapping = dict(zip(self.type_vars, args))
        def sub(t):
            if isinstance(t, GenericVar):
                return mapping[t.name]
            if isinstance(t, TGeneric):
                return TGeneric(t.name, [sub(a) for a in t.args])
            return t
        param_types = [(name, sub(t)) for name, t in self.params]
        return param_types, sub(self.result)


T_LIST = TGeneric("List", (GenericVar("T"),))
T_PAIR = TGeneric("Pair", (GenericVar("A"), GenericVar("B")))

print("== 参数化类型的实例化 ==")
list_int = T_LIST.apply([TGeneric("Int")])
print(f"  List<T> 应用 [Int]     -> {list_int}")
list_list = T_LIST.apply([TGeneric("List", (GenericVar("Int"),))])
print(f"  List<T> 应用 [List<Int>] -> {list_list}（嵌套泛型）")
try:
    T_LIST.apply([TGeneric("Int"), TGeneric("Int")])
except ValueError as exc:
    print(f"  多传参数: {exc}")

print("\n== 泛型函数：identity ==")
identity = GenericFunction("identity", ["T"],
                           [("x", GenericVar("T"))], GenericVar("T"))
ptypes, result = identity.instantiate([TGeneric("Int")])
print(f"  identity<Int>: 参数 {[str(t) for _, t in ptypes]} -> {result}")
ptypes2, result2 = identity.instantiate([TGeneric("Bool")])
print(f"  identity<Bool>: 参数 {[str(t) for _, t in ptypes2]} -> {result2}")
print("  同一配方，两种实例化 —— 每次调用各自获得新的绑定")

print("\n== 泛型函数：map 的类型 ==")
map_fn = GenericFunction("map", ["A", "B"],
                         [("f", TGeneric("Fn", (GenericVar("A"),
                                                GenericVar("B")))),
                          ("xs", TGeneric("List", (GenericVar("A"),)))],
                         TGeneric("List", (GenericVar("B"),)))
ptypes, result = map_fn.instantiate([TGeneric("Int"), TGeneric("Bool")])
print(f"  map<Int, Bool>: 参数 {[(n, str(t)) for n, t in ptypes]}")
print(f"  返回 = {result}")
print("  map: (A→B) × List<A> → List<B> —— 类型自然表达『逐元素变换』")

print("\n== 幻影类型：把约束写进类型参数 ==")
class PhantomId:
    """Id<unit> 只能与同 unit 的 Id 比较 —— 单位安全的身份。"""

    def __init__(self, unit, value):
        self.unit = unit
        self.value = value

    def same_unit(self, other):
        return self.unit == other.unit


user_id = PhantomId("user", 42)
order_id = PhantomId("order", 42)
print(f"  Id<user>(42) 与 Id<order>(42)：值相同、单位不同")
print(f"  same_unit(Id<user>, Id<user>) = {user_id.same_unit(PhantomId('user', 7))}")
print(f"  same_unit(Id<user>, Id<order>) = {user_id.same_unit(order_id)}"
      f"（类型层禁止混用 —— 运行时才能发现的事故被提前）")
print("  幻影参数不出现在数据里，只在类型里 —— 零成本的状态机标注")

print("\n== 泛型 + 子类型（952 课）的组合 ==")
print("  List<Dog> ≤ List<Animal>? —— 取决于变型：")
print("    只读容器协变：安全（取出的 Dog 都是 Animal）")
print("    可写容器不变：写入 Animal 会破坏 List<Dog> 的承诺")
print("  952 课的变型规则在泛型容器上全面生效")

print("\n== 与 950 课推断的融合 ==")
for line in (
    "  显式泛型：程序员标注 List[T] —— 编译器检查调用",
    "  HM 推断：编译器推导 —— 两者产物都是『带代换的类型』",
    "  TS 的实践：推断为主 + 泛型标注补强边界（infer 关键字）",
    "  泛型实例化 = 949 课合一的定向版（按声明顺序绑定）",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  泛型 = 类型层面的参数化：一次编写，任意元素类型复用",
    "  实例化 = 类型变量按调用代换 —— 与合一同源但显式",
    "  幻影类型让『单位/状态』成为编译期约束的零成本手段",
    "  954 课：把本章全部机制装进一个完整的迷你类型检查器",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Pair<A, B> 的 swap：Pair<A,B> → Pair<B,A> 的泛型函数。
# 2. 实现「默认类型参数」：Map<K, V=Str> 只给 K 时 V 自动为 Str。
# 3. 用幻影类型实现「已验证/未验证」状态机：parse 只接受未验证输入。
# 4. 思考：泛型的『类型擦除』（Java）与『具化泛型』（C#/Rust）各有什么
#    运行时成本与表达能力差异？
