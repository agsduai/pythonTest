# ===== 第212课：测试与工程化-unittest入门 =====
# 知识点：
#   - unittest：Python 标准库的单元测试框架，无需安装
#   - 测试类继承 unittest.TestCase，测试方法以 test_ 开头
#   - 常用断言：assertEqual / assertTrue / assertFalse / assertIn
#   - 运行方式：python 文件名.py 或 python -m unittest 文件名

import unittest


def is_palindrome(text):
    """判断回文：忽略大小写与非字母数字。"""
    cleaned = [ch.lower() for ch in text if ch.isalnum()]
    return cleaned == cleaned[::-1]


class TestIsPalindrome(unittest.TestCase):

    def test_normal_word(self):
        self.assertTrue(is_palindrome("level"))

    def test_not_palindrome(self):
        self.assertFalse(is_palindrome("python"))

    def test_ignores_case_and_symbols(self):
        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))

    def test_empty_string(self):
        self.assertTrue(is_palindrome(""))


if __name__ == "__main__":
    unittest.main()     # 运行当前文件中所有 test_ 开头的方法

# 运行效果（每个点代表一个通过的用例）：
#   ....
#   --------------------------------------------------------------
#   Ran 4 tests in 0.001s
#   OK

# ===== 练习题 =====
# 1. 给 is_palindrome 增加“中文字符串”用例，如 "上海自来水来自海上"。
# 2. 编写函数 add(a, b)，用 assertEqual 写 3 个用例（正数/负数/零）。
# 3. 故意写一个失败的用例，观察 unittest 输出如何指出错误位置。
# 4. 思考：为什么测试方法必须以 test_ 开头？
