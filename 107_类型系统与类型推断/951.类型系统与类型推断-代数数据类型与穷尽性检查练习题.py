# ===== 第951课：类型系统与类型推断-代数数据类型与穷尽性检查 =====
# 知识点：
#   - 代数数据类型（ADT）：和类型（几个选一）× 积类型（字段组合）
#   - Option[T] = Some(T) | None —— 用类型消灭『空指针』
#   - 模式匹配解构 ADT；编译器的穷尽性检查保证所有构造器都被处理
#   - 不可达分支检查：写了一个永远匹配不到的模式 = 死代码
#   -穷尽性判据：分支构造器集合 ⊇ 该类型的全部构造器
# 依赖：无（标准库）


# ---------- ADT 定义 ----------
class ADT:
    """代数数据类型：构造器 -> 字段类型列表。"""

    def __init__(self, name, constructors):
        self.name = name
        self.constructors = constructors        # {ctor_name: [field_type]}


OPTION = ADT("Option", {"Some": [("param",)], "None": []})
RESULT = ADT("Result", {"Ok": [("param",)], "Err": [("param",)]})
SHAPE = ADT("Shape", {"Circle": [("float",)], "Rect": [("float", "float")],
                      "Triangle": [("float", "float", "float")]})


def check_exhaustive(adt_name, adt, arms):
    """穷尽性检查：分支覆盖的构造器是否覆盖全部。
    arms: [(ctor 或 '_' 或 (ctor, guard描述), 是否不可达)]"""
    covered = set()
    has_wildcard = False
    unreachable = []
    seen = []
    for pattern, _body in arms:
        if pattern == "_":
            has_wildcard = True
        else:
            if pattern in seen:
                unreachable.append(pattern)
            seen.append(pattern)
            covered.add(pattern)
    missing = sorted(set(adt.constructors) - covered)
    exhaustive = has_wildcard or not missing
    return exhaustive, missing, has_wildcard, sorted(set(unreachable))


def check_unreachable(arms):
    """不可达分支：更宽的模式出现在更窄模式之前会遮蔽后者。"""
    unreachable = []
    seen_wildcard = False
    seen_exact = set()
    for pattern, _body in arms:
        if pattern == "_":
            if seen_exact:
                pass                            # '_' 在后：作为兜底正常
            seen_wildcard = True
        else:
            if seen_wildcard:
                unreachable.append(pattern)     # 被通配符遮蔽
            if pattern in seen_exact:
                unreachable.append(pattern)     # 重复
            seen_exact.add(pattern)
    return sorted(set(unreachable))


print("== Option[Int] 的模式匹配 ==")
print(f"  构造器: {list(OPTION.constructors)}")

print("\n== 穷尽性检查案例 ==")
cases = [
    ("Some + None（完整）", [("Some", "返回值"), ("None", "返回空")]),
    ("只有 Some（缺 None）", [("Some", "返回值")]),
    ("Some + 通配（完整但含混）", [("Some", "返回值"), ("_", "兜底")]),
    ("通配在前（遮蔽一切）", [("_", "兜底"), ("Some", "永不到达")]),
    ("Some + Some + None（重复）", [("Some", "a"), ("Some", "b"), ("None", "空")]),
]
print(f"  {'分支组合':<26}{'穷尽':>6}{'缺失':>16}{'不可达':>14}")
for label, arms in cases:
    exhaustive, missing, has_wild, unreach = check_exhaustive("Option", OPTION, arms)
    print(f"  {label:<26}{str(exhaustive):>6}{str(missing or '-')!s:>16}"
          f"{str(unreach or '-')!s:>14}")

print("\n== 多构造器 ADT（Shape）的覆盖矩阵 ==")
for arms, label in (
    ([("Circle", ""), ("Rect", ""), ("Triangle", "")], "三个全覆盖"),
    ([("Circle", ""), ("Rect", "")], "缺 Triangle"),
    ([("_", "")], "纯通配"),
    ([("Circle", ""), ("Circle", ""), ("_", "")], "Circle 重复"),
):
    exhaustive, missing, has_wild, unreach = check_exhaustive("Shape", SHAPE, arms)
    unreach2 = check_unreachable(arms)
    print(f"  {label:<14} 穷尽={exhaustive}, 缺={missing or '-'}, "
          f"不可达={unreach2 or '-'}")

print("\n== 不可达分支演示（顺序敏感）==")
print("  模式按书写顺序匹配：'_ 在 Some 之前' 会让 Some 分支永远不被选中")
print("  这类 bug 在运行时无异常、只在逻辑上悄悄失效 —— 静态检查的价值")

print("\n== ADT 消灭空指针的机制 ==")
for line in (
    "  Option[T] 让『可能没有值』成为类型的一部分",
    "  没有 None 分支 → 编译不过 → 忘记判空在编译期被拦下",
    "  Python 的 Optional 注解只是文档，穷尽性检查才是 enforcement",
    "  Result[E] 同理：错误处理路径被类型强制覆盖",
):
    print("  -", line)

print("\n== 模式匹配的解构力 ==")
print("  Circle(r) -> 直接绑定半径 r；Rect(w,h) -> 绑定宽高")
print("  检查器同时验证：构造器存在 + 字段数量匹配 + 穷尽性")
print("  三者合起来 = 『解析数据而不验证数据』的错误被消灭")

print("\n== 与 100 章模型检测的联系 ==")
for line in (
    "  穷尽性检查本质是『构造器空间上的覆盖检查』",
    "  模型检测验证『状态空间全覆盖』，模式检查验证『构造器空间全覆盖』",
    "  二者都是把遗漏从运行期提前到静态期",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  ADT = 和类型 + 积类型；模式匹配是它们的唯一合法解构方式",
    "  穷尽性检查让『忘处理一种情况』成为编译错误",
    "  不可达分支检查清理死代码与顺序错误",
    "  952 课：结构子类型 —— 不用继承也能定义『兼容』",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Result[E] 的穷尽性检查，并加入「Err 必须绑定错误信息」的字段数校验。
# 2. 实现嵌套 ADT 的穷尽性：Option[Option[Int]] 的双层模式覆盖检查。
# 3. 加「守卫感知」：带 when 条件的分支不计入穷尽性覆盖（条件可能为假）。
# 4. 思考：为什么运行时的 default 分支在静态检查里是『双刃剑』？
