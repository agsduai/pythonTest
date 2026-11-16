# ===== 第542课：元编程与插件系统-描述符进阶与字段校验 =====
# 知识点：
#   - 描述符：实现 __get__/__set__/__set_name__ 的类，接管属性读写（第348课）
#   - 可复用字段：IntegerField、StringField、EmailField 各写一次，多处复用
#   - __set_name__ 自动拿到字段名；__set__ 做类型/范围/格式校验
#   - 这是 ORM/表单库/配置库的核心机制（SQLAlchemy、Django ORM）
#   - 与 property 的区别：property 一个字段写一套；描述符一次定义、到处挂载
#   - 与第347课 dataclass 的分工：dataclass 适合简单数据，描述符适合复杂校验
# 依赖：无


class Field:
    """字段基类：负责存取与错误信息。"""

    def __set_name__(self, owner, name):
        self.name = name
        self.private = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private, None)

    def __set__(self, instance, value):
        value = self.validate(value)
        setattr(instance, self.private, value)

    def validate(self, value):
        return value


class IntegerField(Field):
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{self.name} 必须是整数，收到 {value!r}")
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} 不能小于 {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} 不能大于 {self.max_value}")
        return value


class StringField(Field):
    def __init__(self, min_length=0, max_length=None):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f"{self.name} 必须是字符串")
        if len(value) < self.min_length:
            raise ValueError(f"{self.name} 长度不能小于 {self.min_length}")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"{self.name} 长度不能超过 {self.max_length}")
        return value


class EmailField(StringField):
    def validate(self, value):
        value = super().validate(value)
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"{self.name} 不是合法邮箱：{value!r}")
        return value


class Model:
    """极简模型基类：按字段名收集参数。"""

    def __init__(self, **kwargs):
        for cls in reversed(type(self).__mro__):
            for name, attr in vars(cls).items():
                if isinstance(attr, Field) and name in kwargs:
                    setattr(self, name, kwargs.pop(name))
        if kwargs:
            raise TypeError(f"未知字段：{list(kwargs)}")

    def to_dict(self):
        result = {}
        for cls in reversed(type(self).__mro__):
            for name, attr in vars(cls).items():
                if isinstance(attr, Field):
                    result[name] = getattr(self, name)
        return result

    def __repr__(self):
        return f"{type(self).__name__}({self.to_dict()})"


class User(Model):
    name = StringField(min_length=2, max_length=20)
    age = IntegerField(min_value=0, max_value=150)
    email = EmailField(max_length=50)


print("== 正常创建 ==")
u = User(name="小明", age=18, email="ming@example.com")
print("  ", u)
print("  属性访问：", u.name, u.age, u.email)

print("\n== 校验拦截 ==")
cases = [
    {"name": "小", "age": 18, "email": "a@b.com"},
    {"name": "小红", "age": 200, "email": "a@b.com"},
    {"name": "小红", "age": 18, "email": "bad-email"},
    {"name": "小红", "age": "18", "email": "a@b.com"},
    {"name": "小红", "age": 18, "email": "a@b.com", "unknown": 1},
]
for kwargs in cases:
    try:
        User(**kwargs)
        print("  ✗ 竟然通过：", kwargs)
    except (TypeError, ValueError) as exc:
        print("  ✓ 拦截：", exc)

print("\n== 修改属性同样校验 ==")
try:
    u.age = 999
except ValueError as exc:
    print("  ", exc)
u.age = 19
print("  修改成功：", u.age)

# ---- 字段复用 ----
print("\n== 字段复用 ==")


class Product(Model):
    name = StringField(min_length=1, max_length=50)
    price = IntegerField(min_value=1)
    stock = IntegerField(min_value=0)


p = Product(name="键盘", price=199, stock=10)
print("  ", p)
print("  同一套 Field 类复用到不同模型，不需要重复写校验")

# ---- 与 property / dataclass 对比 ----
print("\n== 三种方案对比 ==")
rows = [
    ("property", "单字段定制逻辑", "直观", "每个字段写一遍"),
    ("dataclass", "简单数据载体", "代码最少", "复杂校验要 __post_init__"),
    ("描述符", "大量字段统一校验", "一次定义多处复用", "理解成本高"),
]
print(f"  {'方案':<10}{'适用':<20}{'优点':<16}{'代价'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<20}{r[2]:<16}{r[3]}")

# ---- 进阶方向 ----
print("\n== 进阶 ==")
for item in [
    "字段级默认值与可选字段",
    "嵌套 Model 校验",
    "错误聚合：一次收集所有字段错误，而不是遇到第一个就抛",
    "序列化/反序列化（to_dict/from_dict）",
    "与元类配合：创建类时自动收集字段（第541课练习）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加 DateField（YYYY-MM-DD 格式校验）。
# 2. 给 Model 增加 from_dict 类方法。
# 3. 实现错误聚合：收集所有字段错误后一次性抛出。
# 4. 思考：为什么 ORM 的字段校验放在描述符里，而不是在 __init__ 里？
