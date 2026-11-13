# ===== 第219课：测试与工程化-综合案例-TDD计算器 =====
# 知识点：
#   - TDD（测试驱动开发）：先写测试，再写实现，最后重构
#   - 流程：红（测试失败）→ 绿（测试通过）→ 重构
#   - 浮点数比较用 assertAlmostEqual，不要直接 ==
#   - 实际项目中功能代码与测试代码分开存放，本课为演示合在一起

import unittest


# ---- 第一步：先想清楚“计算器应该满足什么行为”，写成测试 ----
class TestCalculator(unittest.TestCase):

    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_sub(self):
        self.assertEqual(sub(5, 2), 3)

    def test_mul(self):
        self.assertEqual(mul(3, 4), 12)

    def test_div(self):
        self.assertEqual(div(8, 2), 4.0)

    def test_div_precision(self):
        self.assertAlmostEqual(div(1, 3), 0.3333, places=4)   # 浮点用近似比较

    def test_div_zero_raises(self):
        with self.assertRaises(ValueError):
            div(1, 0)


# ---- 第二步：写最少的实现让测试全部通过 ----
def add(a, b):
    return a + b


def sub(a, b):
    return a - b


def mul(a, b):
    return a * b


def div(a, b):
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


if __name__ == "__main__":
    # 第三步：运行测试，全部变绿才算完成
    unittest.main(verbosity=2)

# ===== 练习题 =====
# 1. 按 TDD 顺序给计算器新增“求余”功能：先写 test_mod，再实现 mod。
# 2. 增加参数校验测试：add("a", 1) 应抛 TypeError（在 add 里加类型检查）。
# 3. 把功能代码拆到 calculator.py，测试拆到 test_calculator.py，用 pytest 运行。
# 4. 思考：TDD 的“先写测试”为什么能减少返工？
