# ===== 第539课：元编程与插件系统-动态属性 =====
# 知识点：
#   - Python 对象属性访问的三道钩子：
#     __getattribute__（所有访问都走它）、__getattr__（只有找不到才走）、__setattr__
#   - 动态属性：属性不存在时按需计算/代理，实现懒加载与包装
#   - 代理对象：把读写转发给内部目标，接口不变
#   - 注意：__getattr__ 里访问 self.xxx 可能无限递归，要用 object.__getattribute__
#   - 与第345课 property、第348课描述符的区别：那两者是“类级别”的，这里是“实例级别”
# 依赖：无


class LazyConfig:
    """第一次访问属性时才计算（模拟从远端/文件加载）。"""

    def __init__(self):
        object.__setattr__(self, "_cache", {})

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._cache:
            return self._cache[name]
        print(f"  [懒加载] 计算 {name} ...")
        value = name.upper()
        self._cache[name] = value
        return value

    def __setattr__(self, name, value):
        print(f"  [设置] {name} = {value!r}")
        object.__setattr__(self, name, value)


print("== 懒加载属性 ==")
cfg = LazyConfig()
print("  第一次 cfg.host：", cfg.host)
print("  第二次 cfg.host：", cfg.host)
print("  访问不存在的下划线属性会报错：")
try:
    cfg._secret
except AttributeError as exc:
    print("   ", exc)

# ---------------- 代理对象 ----------------
class LoggingProxy:
    """把读写转发给 target，并记录日志。"""

    def __init__(self, target):
        object.__setattr__(self, "_target", target)

    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        target = object.__getattribute__(self, "_target")
        value = getattr(target, name)
        if not callable(value):
            print(f"  [读代理] {name} → {value!r}")
        return value

    def __setattr__(self, name, value):
        target = object.__getattribute__(self, "_target")
        print(f"  [写代理] {name} = {value!r}")
        setattr(target, name, value)


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age


print("\n== 代理对象 ==")
user = User("小明", 18)
proxy = LoggingProxy(user)
print("  通过代理读：", proxy.name)
proxy.age = 19
print("  目标对象已更新：", user.age)
print("  代理与目标是两个对象：", proxy is not user)

# ---------------- __getattr__ 与 __getattribute__ 的区别 ----------------
print("\n== 三个钩子的触发时机 ==")
class Demo:
    def __getattribute__(self, name):
        print(f"  __getattribute__({name})")
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        print(f"  __getattr__({name})（正常查找失败后）")
        return "默认值"


d = Demo()
d.existing = 1
print("  访问已有属性：", d.existing)
print("  访问不存在属性：", d.missing)

# ---------------- 常见陷阱 ----------------
print("\n== 常见陷阱 ==")
for item in [
    "__getattr__ 里写 self.xxx 可能再次触发自己 → 无限递归",
    "用 object.__getattribute__(self, ...) 或 self.__dict__ 取值",
    "__setattr__ 里写 self.xxx = ... 也会递归",
    "代理/包装会丢失 isinstance 语义，必要时实现 __class__ 或继承",
    "过度使用动态属性会降低可读性和 IDE 补全",
]:
    print("  -", item)

# ---------------- 适用场景 ----------------
print("\n== 适用场景 ==")
for item in [
    "配置/客户端：首次访问才建立连接",
    "ORM：字段在访问时才查询数据库",
    "代理：日志、权限、缓存（第393课）",
    "兼容层：把旧接口动态映射到新对象",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 LazyConfig 增加“失效缓存”方法，验证重新计算。
# 2. 实现只读代理：写操作抛 PermissionError。
# 3. 用 __getattr__ 让对象支持 cfg.db.host 这样的链式访问。
# 4. 思考：动态属性与“显式方法”相比，各有什么优缺点？
