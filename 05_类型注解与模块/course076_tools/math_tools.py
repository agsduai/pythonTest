"""math_tools.py：course076_tools 包中的数学工具子模块。"""


def add(a: float, b: float) -> float:
    """返回两个数之和。"""
    return a + b


def average(numbers: list[float]) -> float:
    """返回平均值，空列表返回 0。"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
