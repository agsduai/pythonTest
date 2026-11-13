"""course075_myutils.py：第075课配套的自定义模块。"""

__all__ = ["add", "average", "shout", "square"]

PI = 3.14159


def add(a: float, b: float) -> float:
    """返回两个数之和。"""
    return a + b


def average(numbers: list[float]) -> float:
    """返回平均值，空列表返回 0。"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def shout(text: str) -> str:
    """把文本转成大写并加上感叹号。"""
    return text.upper() + "!"


def square(n: float) -> float:
    """返回 n 的平方。"""
    return n * n


if __name__ == "__main__":
    # 只有直接运行本模块时才会执行，被其他文件导入时不执行
    print("模块自测开始")
    print("add(1, 2) =", add(1, 2))
    print("average([1, 2, 3]) =", average([1, 2, 3]))
    print("模块自测结束")
