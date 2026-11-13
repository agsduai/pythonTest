# ===== 第347课：OOP进阶-dataclass数据类 =====
# 知识点：
#   - @dataclass：自动生成 __init__ / __repr__ / __eq__
#   - field(default_factory=list)：可变默认值的安全写法（对照第364课陷阱）
#   - frozen=True：不可变对象 → 可哈希、可作字典键、线程友好
#   - 数据类适合“主要装数据的类”：配置、记录、消息
from dataclasses import dataclass, field


@dataclass
class Student:
    name: str
    age: int = 18
    scores: list = field(default_factory=list)     # 每个实例独立列表

    def average(self):
        return sum(self.scores) / len(self.scores) if self.scores else 0.0


s1 = Student("小明")
s1.scores.append(92)
s2 = Student("小红")
print(s1, s2)
print("默认值互不影响：", s2.scores == [])
print("自动 __eq__：", Student("小明", 18) == Student("小明", 18))
print("平均分：", s1.average())


@dataclass(frozen=True)
class Config:
    host: str
    port: int = 8080
    tags: tuple = ()                # 不可变容器可做默认值


c = Config("localhost")
print(c, "| 可哈希：", isinstance(hash(c), int))
try:
    c.port = 9999                   # frozen 拦截修改
except Exception as exc:
    print(type(exc).__name__, "—— frozen 拦截修改")

print("作字典键：", {c: "ok"}[Config("localhost")])

# 字段顺序规则：有默认值的字段必须在无默认值之后（和函数参数一致）

# ===== 练习题 =====
# 1. 给 Student 加 __post_init__：创建时自动把 age 校验为 6~60。
# 2. 用 frozen dataclass 重写第264课的用户密码记录（用户名+密码哈希）。
# 3. 思考：dataclass 与第346课 __slots__ 能一起用吗？（dataclass(slots=True)）
