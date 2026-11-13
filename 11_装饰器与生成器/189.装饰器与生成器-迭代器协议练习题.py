# ===== 第189课：装饰器与生成器-迭代器协议 =====
# 知识点：
#   - 可迭代对象（Iterable）：实现了 __iter__，可以被 for 遍历
#   - 迭代器（Iterator）：实现了 __iter__ 和 __next__，记录遍历位置
#   - iter() 把可迭代对象变成迭代器，next() 逐个取值，取完抛 StopIteration
#   - for 循环的本质：自动调用 iter/next，并捕获 StopIteration 结束

nums = [10, 20, 30]
it = iter(nums)          # 列表是可迭代对象，转成迭代器
print(next(it))          # 10
print(next(it))          # 20
print(next(it))          # 30
# print(next(it))        # 再取就抛 StopIteration，注释打开可观察

# for 循环在底层的等价写法
it2 = iter(nums)
while True:
    try:
        value = next(it2)
        print("for本质：", value)
    except StopIteration:
        break            # for 循环就是这样优雅退出的


# 自定义迭代器：同时实现 __iter__ 和 __next__
class Countdown:
    """从 n 递减到 1 的迭代器。"""

    def __init__(self, n):
        self.current = n

    def __iter__(self):
        return self             # 迭代器的 __iter__ 返回自身

    def __next__(self):
        if self.current <= 0:
            raise StopIteration     # 报告遍历结束
        value = self.current
        self.current -= 1
        return value


for num in Countdown(3):
    print(num)               # 3 2 1

cd = Countdown(2)
print(list(cd))              # [2, 1]
print(list(cd))              # []：迭代器是一次性的，耗尽即空


# 可迭代对象与迭代器分离：每次遍历都从头开始
class NumberBox:
    """可迭代对象：每次 __iter__ 都返回一个全新的迭代器。"""

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter(self.data)   # 交给 list 自带的迭代器


box = NumberBox([1, 2, 3])
print(list(box))    # [1, 2, 3]
print(list(box))    # [1, 2, 3]，可重复遍历

# isinstance 判断：列表是 Iterable 但不是 Iterator
from collections.abc import Iterable, Iterator

print(isinstance(nums, Iterable), isinstance(nums, Iterator))     # True False
print(isinstance(Countdown(3), Iterable), isinstance(Countdown(3), Iterator))

# ===== 练习题 =====
# 1. 编写迭代器类 EvenIterator，实现“无限偶数”序列 2,4,6,...，
#    用 next() 配合循环取前 5 个值后 break。
# 2. 编写可迭代类 Sentence，接收一段文字，遍历时逐个返回单词。
# 3. 观察文件对象：open() 返回的对象是迭代器还是可迭代对象？
#    为什么读大文件要逐行 for line in f？
# 4. 思考：列表可以反复遍历，迭代器为什么不行？设计上各有什么好处？
