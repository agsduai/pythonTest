# ===== 第213课：测试与工程化-unittest夹具 =====
# 知识点：
#   - setUp / tearDown：每个测试方法前后各执行一次（准备/清理）
#   - setUpClass / tearDownClass：整个类前后各执行一次（@classmethod）
#   - assertRaises：断言“应当抛出异常”
#   - @unittest.skip：临时跳过某些测试
#   - 测试要相互独立：每个测试都拿到全新状态，互不影响

import unittest


class Stack:
    """一个极简栈实现。"""

    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("栈为空")
        return self._items.pop()

    def size(self):
        return len(self._items)


class TestStack(unittest.TestCase):

    def setUp(self):
        # 每个测试方法都会拿到一个全新的栈
        self.stack = Stack()
        self.stack.push(1)
        self.stack.push(2)
        print("  setUp：准备栈")

    def tearDown(self):
        print("  tearDown：清理")

    def test_size(self):
        self.assertEqual(self.stack.size(), 2)

    def test_pop(self):
        self.assertEqual(self.stack.pop(), 2)
        self.assertEqual(self.stack.size(), 1)

    def test_pop_empty_raises(self):
        empty = Stack()
        with self.assertRaises(IndexError):
            empty.pop()


class TestStackClassLevel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(">> 整个类只执行一次的资源准备（如临时文件、数据库）")

    def test_demo(self):
        self.assertTrue(True)

    @unittest.skip("功能开发中，先跳过")
    def test_future(self):
        self.fail("不应被执行")


if __name__ == "__main__":
    unittest.main(verbosity=2)      # verbosity=2 显示每个用例的名字

# ===== 练习题 =====
# 1. 给 Stack 增加 peek()（查看栈顶但不弹出），先写测试再实现。
# 2. 验证独立性：在 test_pop 里修改 self.stack，看 test_size 是否受影响。
# 3. 用 setUpClass + 临时文件演示“整个类共享一份资源”的写法。
# 4. 思考：夹具里“准备”和“清理”各负责什么？清理为什么重要？
