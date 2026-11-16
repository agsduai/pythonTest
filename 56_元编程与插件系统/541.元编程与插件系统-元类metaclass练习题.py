# ===== 第541课：元编程与插件系统-元类metaclass =====
# 知识点：
#   - 类也是对象，类的“类”就是元类；默认元类是 type
#   - type(name, bases, namespace) 可以在运行时动态创建类
#   - 自定义元类：继承 type，重写 __new__/__init__ 控制类的创建
#   - 典型用途：强制命名规范、自动注册、单例、接口校验、ORM 字段收集
#   - 元类冲突：父类元类不同会报错；优先用 __init_subclass__（第540课）
#   - 与第360课“一切皆对象”直接呼应
# 依赖：无

# ---------------- 1. 用 type 动态创建类 ----------------
print("== type 动态创建类 ==")
User = type("User", (), {
    "category": "person",
    "__init__": lambda self, name: setattr(self, "name", name),
    "greet": lambda self: f"你好，{self.name}",
})
u = User("小明")
print("  ", u.greet(), "| 类型：", type(u).__name__, "| 类是 type 的实例：", isinstance(User, type))

# ---------------- 2. 命名规范元类 ----------------
print("\n== 元类强制命名规范 ==")


class PascalMeta(type):
    def __new__(mcls, name, bases, namespace):
        if not name[0].isupper():
            raise TypeError(f"类名必须以大写字母开头：{name}")
        return super().__new__(mcls, name, bases, namespace)


class GoodClass(metaclass=PascalMeta):
    pass

try:
    class bad_class(metaclass=PascalMeta):     # noqa: N801（故意演示）
        pass
except TypeError as exc:
    print("  拦截：", exc)

# ---------------- 3. 自动注册元类 ----------------
print("\n== 元类自动注册 ==")


class RegistryMeta(type):
    registry = {}

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if namespace.get("register", True) and name != "Base":
            key = namespace.get("key", name.lower())
            mcls.registry[key] = cls
            print(f"  [注册] {key} → {name}")
        return cls


class Base(metaclass=RegistryMeta):
    register = False


class JsonParser(Base):
    key = "json"
    def parse(self, text):
        return f"解析 JSON: {text}"


class XmlParser(Base):
    key = "xml"
    def parse(self, text):
        return f"解析 XML: {text}"


print("  注册表：", RegistryMeta.registry)
print("  按 key 创建：", RegistryMeta.registry["json"]().parse("{}"))

# ---------------- 4. 单例元类 ----------------
print("\n== 单例元类 ==")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self):
        self.values = {}


a, b = Config(), Config()
a.values["debug"] = True
print("  同一实例：", a is b, "| 共享值：", b.values)

# ---------------- 5. 元类与继承 ----------------
print("\n== 元类冲突 ==")
class OtherMeta(type):
    pass

try:
    class Mixed(GoodClass, metaclass=OtherMeta):
        pass
except TypeError as exc:
    print("  拦截：", exc)
print("  规则：子类元类必须是所有父类元类的子类")

# ---------------- 6. 使用建议 ----------------
print("\n== 使用建议 ==")
for item in [
    "90% 的“自动注册/校验子类”需求用 __init_subclass__ 就够",
    "元类适合“控制类怎么创建”：单例、字段收集、接口强制",
    "元类会让代码更难懂，团队要有共识",
    "不要用元类做本可以用装饰器/描述符解决的事",
    "调试时注意：类的创建发生在 import 阶段，错误会提前暴露",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 用元类实现“所有方法名必须小写”的校验。
# 2. 用元类收集类中定义的 Field 字段（配合第542课描述符）。
# 3. 比较 __init_subclass__ 与元类实现自动注册的代码量。
# 4. 思考：为什么 ORM 框架喜欢用元类？
