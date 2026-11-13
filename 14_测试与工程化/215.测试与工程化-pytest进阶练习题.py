# ===== 第215课：测试与工程化-pytest进阶 =====
# 知识点：
#   - @pytest.mark.parametrize：一套逻辑跑多组数据
#   - fixture：给测试提供“准备好的资源”，测试函数按参数名自动接收
#   - fixture 天然隔离：每个测试函数拿到独立的一份
#   - conftest.py：存放共享 fixture，同目录测试无需 import 自动生效
# 依赖：pip install pytest

import pytest


def grade(score):
    if score >= 90:
        return "优秀"
    if score >= 80:
        return "良好"
    if score >= 60:
        return "及格"
    return "不及格"


@pytest.mark.parametrize(
    "score, expected",
    [(95, "优秀"), (85, "良好"), (70, "及格"), (50, "不及格")],
)
def test_grade(score, expected):
    assert grade(score) == expected


@pytest.fixture
def sample_students():
    """给每个测试函数准备一份数据，测试结束后清理。"""
    data = {"小明": 92, "小红": 78}
    yield data
    print("fixture 清理（测试之后执行）")


def test_existing(sample_students):
    assert sample_students["小明"] == 92


def test_add_student(sample_students):
    sample_students["小刚"] = 66
    assert len(sample_students) == 3


def test_fixture_isolation(sample_students):
    # 上一个测试添加的“小刚”不会影响这里 —— 每个测试拿到全新数据
    assert "小刚" not in sample_students


# 运行：pytest "215.测试与工程化-pytest进阶练习题.py" --import-mode=importlib -v -s
# （-s 显示 print；--import-mode=importlib 是因为文件名以数字开头）

# ===== 练习题 =====
# 1. 把 grade 的参数化用例扩到 8 组，覆盖每个分支的边界值（90/80/60）。
# 2. 用内置 fixture tmp_path 建临时文件测试读写，测试后验证清理。
# 3. 把 fixture 移到 conftest.py 里，再写第二个测试文件使用它。
# 4. 思考：fixture 与 unittest 的 setUp 相比灵活在哪里？
