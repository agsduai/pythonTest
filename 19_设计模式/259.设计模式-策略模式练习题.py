# ===== 第259课：设计模式-策略模式 =====
# 知识点：
#   - 策略：把“一组可互换的算法”各自封装，运行时按需切换
#   - 两种 Python 实现：类策略（ABC，逻辑复杂时用）与函数策略（字典映射，轻量首选）
#   - 典型收益：消灭 if/elif 长链，新增策略不改旧代码

from abc import ABC, abstractmethod


# ---- 类策略版 ----
class Promo(ABC):

    @abstractmethod
    def price(self, original: float) -> float: ...


class NoPromo(Promo):

    def price(self, original):
        return original


class HalfPromo(Promo):

    def price(self, original):
        return original * 0.5


class Over100Minus30(Promo):

    def price(self, original):
        return original - 30 if original >= 100 else original


def checkout(promo: Promo, original: float) -> float:
    return round(promo.price(original), 2)


print(checkout(NoPromo(), 120), checkout(HalfPromo(), 120), checkout(Over100Minus30(), 120))


# ---- 函数策略版：字典映射，简洁常用 ----
STRATEGIES = {
    "none": lambda p: p,
    "half": lambda p: p * 0.5,
    "minus30": lambda p: max(0, p - 30),
}


def checkout_by_name(kind: str, original: float) -> float:
    strategy = STRATEGIES.get(kind)
    if strategy is None:
        raise ValueError(f"未知促销：{kind}（可选 {'/'.join(STRATEGIES)}）")
    return round(strategy(original), 2)


for kind in ("none", "half", "minus30"):
    print(kind, "→", checkout_by_name(kind, 120))

# 对照反例：if/elif 链每加一种促销都要改函数体，违背开闭原则
# def bad_checkout(kind, p):
#     if kind == "none": return p
#     elif kind == "half": return p * 0.5
#     elif kind == "minus30": ...
#     # 越写越长……

# ===== 练习题 =====
# 1. 新增“满200减50”策略，两种实现各加一遍。
# 2. 策略 + 第258课工厂结合：create_promo(kind) 返回策略对象。
# 3. 把第099课的提示词模板做成策略字典（正式/简洁/幽默三种风格）。
# 4. 思考：函数策略和类策略各适合什么复杂度？
