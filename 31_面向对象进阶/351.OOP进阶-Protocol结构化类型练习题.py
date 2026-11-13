# ===== 第351课：OOP进阶-Protocol结构化类型 =====
# 知识点：
#   - ABC（第256课）：显式继承的强约束 —— “你必须是我的子类”
#   - Protocol：结构化子类型 —— “有这些方法就算”，无需继承
#   - 价值：第三方类、内置类型无法继承你的基类时，Protocol 仍能约束
#   - 运行时宽松 + mypy 静态检查严格 = 鸭子类型的工程化
from typing import Protocol


class Closer(Protocol):
    """只要“有 close() 方法”就满足本协议。"""

    def close(self) -> None: ...


class FileLike:                     # 没继承任何基类
    def close(self):
        print("文件已关闭")


class DBLike:
    def close(self):
        print("数据库连接已关闭")


class NoClose:                      # 没有close() —— 不满足协议
    def shutdown(self):
        print("只有 shutdown")


def cleanup(resource: Closer):
    resource.close()


cleanup(FileLike())                 # 运行时：长得像就行
cleanup(DBLike())

# 静态检查器（mypy）会在“这里”报错，而不是等运行时崩：
# cleanup(NoClose())   ← mypy: Argument has incompatible type "NoClose"; expected "Closer"

# 运行时强制校验可用 isinstance + runtime_checkable（只查方法名，不查签名）
from typing import runtime_checkable


@runtime_checkable
class Closer2(Protocol):
    def close(self) -> None: ...


print("isinstance 结构判断：", isinstance(FileLike(), Closer2),
      isinstance(NoClose(), Closer2))

# 选型：自己体系的类 → ABC；跨体系/第三方 → Protocol

# ===== 练习题 =====
# 1. 定义 SupportsArea 协议（有 area()），让圆/矩形/三角形都通过。
# 2. 用 Protocol 替代第258课工厂的产品抽象，验证不需要继承。
# 3. 思考：runtime_checkable 的 isinstance 为什么“只查名字不查签名”？
