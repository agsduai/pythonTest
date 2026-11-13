# ===== 第250课：算法入门-栈的实现与应用 =====
# 知识点：
#   - 栈：后进先出 LIFO，只有 push/pop/peek 三个动作
#   - 应用：括号匹配、撤销操作、函数调用栈、进制转换
#   - 括号匹配的思路：左括号入栈，右括号找栈顶配对
#   - 用 list 的 append/pop 就能实现栈（都是尾部操作，O(1)）


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("栈为空")
        return self._items.pop()

    def peek(self):
        return self._items[-1] if self._items else None

    def is_empty(self):
        return not self._items

    def __len__(self):
        return len(self._items)


# 应用1：括号匹配
def is_balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = Stack()
    for ch in s:
        if ch in "([{":
            stack.push(ch)
        elif ch in ")]}":
            if stack.is_empty() or stack.pop() != pairs[ch]:
                return False
    return stack.is_empty()


print(is_balanced("a(b[c]d)e"))      # True
print(is_balanced("a(b[c)d]"))       # False：交叉嵌套
print(is_balanced("((()))"), is_balanced("(()"))


# 应用2：进制转换（余数逆序输出 —— 正好用栈）
def to_base(n, base=2):
    digits = "0123456789ABCDEF"
    s = Stack()
    while n > 0:
        s.push(digits[n % base])
        n //= base
    result = ""
    while not s.is_empty():
        result += s.pop()
    return result or "0"


print(to_base(255), to_base(255, 16), to_base(255, 2))

# 应用3：撤销操作模拟
history = Stack()
history.push("输入第一行")
history.push("输入第二行")
print("撤销：", history.pop())
print("当前栈顶：", history.peek())
print("剩余操作数：", len(history))

# ===== 练习题 =====
# 1. 给 is_balanced 增加“非括号字符夹杂”的更多测试用例。
# 2. 用栈实现字符串逆序："python" → "nohtyp"。
# 3. 编写函数 is_palindrome(s)：用栈判断回文（对比第211课写法）。
# 4. 思考：浏览器的前进/后退为什么用两个栈实现？
