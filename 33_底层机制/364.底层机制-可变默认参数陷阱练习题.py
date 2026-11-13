# ===== 第364课：底层机制-可变默认参数陷阱 =====
# 知识点：
#   - 默认值在“函数定义时”只求值一次，之后所有调用共享同一个对象
#   - 不可变默认值（int/str/None）：共享无害
#   - 可变默认值（list/dict/set）：被历次调用“污染” —— 十大经典 bug 之首
#   - 正解：默认 None 哨兵 + 函数体内新建
def add_item_bad(item, items=[]):          # 反例！默认列表只创建一次
    items.append(item)
    return items


print(add_item_bad(1), end=" ")
print(add_item_bad(2))                     # [1, 2] —— 上次的 1 还在！
print("默认值本体被污染：", add_item_bad.__defaults__)


# ---- 正解：None 哨兵 ----
def add_item_good(item, items=None):
    if items is None:
        items = []                         # 每次调用新建
    items.append(item)
    return items


print(add_item_good(1), add_item_good(2))  # [1] [2] —— 符合直觉

# ---- 可变默认值的正确用途：刻意共享（简易缓存/登记簿）----
def seen(x, registry=set()):               # 明知共享而用之
    already = x in registry
    registry.add(x)
    return not already                     # True = 第一次出现


print(seen("a"), seen("b"), seen("a"))

# 与第347课对照：dataclass 的 field(default_factory=list) 就是本课正解的语法化

# ===== 练习题 =====
# 1. 写函数 record(event, log=[])，故意展示三次调用后 log 的内容。
# 2. 用 __defaults__ 观察“哨兵版”函数的默认值是不是 None。
# 3. 思考：为什么 Python 不在“每次调用”时重新求值默认值？（提示：定义期求值更便宜）
