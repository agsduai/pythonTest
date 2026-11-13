# ===== 第214课：测试与工程化-pytest入门 =====
# 知识点：
#   - pytest：第三方测试框架（pip install pytest），写法比 unittest 更简洁
#   - 不用写类：普通 test_ 开头的函数即可
#   - 直接用 assert 断言，失败时会展示详细差异
#   - 运行：pytest 文件名 -v；无参数则自动发现所有测试文件
# 依赖：pip install pytest


def add(a, b):
    return a + b


def test_add_positive():
    assert add(1, 2) == 3


def test_add_negative():
    assert add(-1, -2) == -3


def test_add_zero():
    assert add(5, 0) == 5


# pytest 对异常的断言用 pytest.raises
def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


def test_divide_raises():
    import pytest
    with pytest.raises(ValueError):
        divide(1, 0)


# 运行方式（在终端执行，不是用 python 运行本文件）：
#   pytest "214.测试与工程化-pytest入门练习题.py" --import-mode=importlib -v
# 说明：本课程文件名以数字开头，pytest 默认导入模式不识别，需加 --import-mode=importlib

# ===== 练习题 =====
# 1. 给第210课的学生管理系统写 5 个 pytest 用例（增/查/改/删/列表）。
# 2. 故意把 add 改成 a - b，运行 pytest 看失败信息如何定位问题。
# 3. 使用 pytest -k add 只运行名字含 add 的用例。
# 4. 思考：pytest 和 unittest 你更愿意用哪个？为什么？
