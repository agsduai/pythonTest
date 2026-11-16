# ===== 第540课：元编程与插件系统-__init_subclass__与注册表 =====
# 知识点：
#   - __init_subclass__：子类定义时自动执行，父类可感知“谁继承了我”
#   - 插件注册表：基类维护 {名字: 子类}，子类声明即注册
#   - 比元类更轻量：大多数“自动注册/校验子类”需求用它就够
#   - 可配合类属性（name、version）做声明式配置
#   - 与第258课工厂、第351课 Protocol 的区别：这里是“自动发现实现”
#   - 注册表让新增插件不改核心代码（开闭原则，第256课）
# 依赖：无


class Plugin:
    """所有插件的基类：子类自动注册。"""
    registry: dict[str, type] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        name = getattr(cls, "name", cls.__name__.lower())
        if name in Plugin.registry:
            raise ValueError(f"插件名重复：{name}")
        Plugin.registry[name] = cls
        print(f"  [注册] {name} → {cls.__name__}")

    def run(self, data):
        raise NotImplementedError


class UpperPlugin(Plugin):
    name = "upper"

    def run(self, data):
        return data.upper()


class ReversePlugin(Plugin):
    name = "reverse"

    def run(self, data):
        return data[::-1]


class RepeatPlugin(Plugin):
    name = "repeat"

    def __init__(self, times=2):
        self.times = times

    def run(self, data):
        return data * self.times


print("== 类定义时自动注册 ==")
print("  注册表：", Plugin.registry)

print("\n== 运行时使用 ==")
text = "hello"
for name in ("upper", "reverse", "repeat"):
    plugin_cls = Plugin.registry[name]
    plugin = plugin_cls() if name != "repeat" else plugin_cls(times=3)
    print(f"  {name:8s} → {plugin.run(text)!r}")

# ---- 动态定义子类也会注册 ----
print("\n== 动态创建子类 ==")
ShoutPlugin = type(
    "ShoutPlugin",
    (Plugin,),
    {"name": "shout", "run": lambda self, data: data + "!!!"},
)
print("  注册表新增：", "shout" in Plugin.registry)
print("  调用：", Plugin.registry["shout"]().run("wow"))

# ---- 重名保护 ----
print("\n== 重名保护 ==")
try:
    class DuplicatePlugin(Plugin):
        name = "upper"
        def run(self, data):
            return data
except ValueError as exc:
    print("  拦截：", exc)

# ---- 声明式配置：自动校验 ----
print("\n== 子类校验 ==")


class ValidatedPlugin(Plugin):
    required_attrs = ("name", "version")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        missing = [a for a in cls.required_attrs if not hasattr(cls, a)]
        if missing:
            raise TypeError(f"{cls.__name__} 缺少必需属性：{missing}")


try:
    class BrokenPlugin(ValidatedPlugin):
        name = "broken"
except TypeError as exc:
    print("  拦截：", exc)

class GoodPlugin(ValidatedPlugin):
    name = "good"
    version = "1.0"
    def run(self, data):
        return data

print("  GoodPlugin 注册成功：", "good" in Plugin.registry)

# ---- 注册表模式的价值 ----
print("\n== 注册表模式 ==")
for item in [
    "新增插件只写一个类，核心调度代码不改",
    "名字唯一性、必填属性可在注册时校验",
    "可按名字/配置动态选择实现（第258课工厂的自动化版）",
    "测试时可注册 Fake 插件替换真实实现",
]:
    print("  -", item)

# ---- 与元类的选择 ----
print("\n== __init_subclass__ vs 元类 ==")
print("  子类注册/校验/命名规范 → 优先 __init_subclass__（简单）")
print("  需要控制“类本身怎么创建”（改属性、强制单例）→ 元类（第541课）")

# ===== 练习题 =====
# 1. 给 Plugin 增加 list_plugins() 类方法，返回名字与版本。
# 2. 实现“按配置启用插件”：config 里只写名字，运行时实例化。
# 3. 增加 abstract 方法校验：子类没实现 run 时报错。
# 4. 思考：注册表与第258课工厂函数的区别是什么？
