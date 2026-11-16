# ===== 第562课：类型检查与静态分析-综合案例-给旧代码加类型 =====
# 知识点：
#   - 综合运用：mypy（555/556/557/558）+ TypedDict/dataclass（559）
#     + overload/Callable（560）+ ruff（561）
#   - 流程：先跑 mypy --strict 看问题 → 加注解/建模 → 修复 → 再跑
#   - 旧代码常见问题：无注解、Any 扩散、dict 万能、None 未处理
#   - 用 dataclass 替代裸 dict，用 list[Item] 替代 list
#   - CI 里固定 mypy + ruff，防止类型与风格回退
# 依赖：pip install mypy ruff（已安装）

import subprocess
import sys
import tempfile
from pathlib import Path


def run_tool(code: str, tool: str, args: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "inventory.py"
        path.write_text(code, encoding="utf-8")
        command = [sys.executable, "-m", tool, *args, str(path)]
        if tool == "mypy":
            command = [sys.executable, "-m", "mypy", "--no-incremental",
                       "--cache-dir", str(Path(tmp) / "cache"), *args, str(path)]
        result = subprocess.run(command, capture_output=True, text=True)
        output = (result.stdout + result.stderr).replace(str(path), "inventory.py")
        return f"返回码 {result.returncode}\n{output.strip()}"


UNTYPED = '''
def add_item(cart, name, price):
    cart.append({"name": name, "price": price})
    return cart


def total(cart):
    return sum(item["price"] for item in cart)


def find(cart, name):
    for item in cart:
        if item["name"] == name:
            return item
    return None


cart = []
add_item(cart, "苹果", 3)
add_item(cart, "香蕉", 5)
print(total(cart))
print(find(cart, "苹果")["price"])
'''

TYPED = '''
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price: float


def add_item(cart: list[Item], name: str, price: float) -> list[Item]:
    cart.append(Item(name, price))
    return cart


def total(cart: list[Item]) -> float:
    return sum(item.price for item in cart)


def find(cart: list[Item], name: str) -> Item | None:
    for item in cart:
        if item.name == name:
            return item
    return None


def main() -> None:
    cart: list[Item] = []
    add_item(cart, "苹果", 3.0)
    add_item(cart, "香蕉", 5.0)
    print(total(cart))

    found = find(cart, "苹果")
    if found is not None:                 # 收窄 Optional
        print(found.price)
    else:
        print("未找到")


if __name__ == "__main__":
    main()
'''

print("== 1. 旧代码：mypy --strict ==")
print(run_tool(UNTYPED, "mypy", ["--strict"]))

print("\n== 2. 旧代码：ruff ==")
print(run_tool(UNTYPED, "ruff", ["check", "--no-cache", "--select", "E,F,I"]))

print("\n== 3. 加类型后的代码：mypy --strict ==")
print(run_tool(TYPED, "mypy", ["--strict"]))

print("\n== 4. 加类型后的代码：ruff ==")
print(run_tool(TYPED, "ruff", ["check", "--no-cache", "--select", "E,F,I"]))
print(run_tool(TYPED, "ruff", ["format", "--check"]))

# ---- 改造前后对比 ----
print("\n== 改造要点 ==")
rows = [
    ("裸 dict", "dataclass Item", "字段名拼错在运行前暴露"),
    ("无注解", "list[Item] / str / float", "调用点类型不匹配立刻报错"),
    ("返回 Optional 却直接取属性", "显式判空", "避免线上 NoneType 崩溃"),
    ("无入口结构", "main() + __name__", "可测试、可导入"),
]
print(f"  {'旧代码':<26}{'新代码':<30}{'收益'}")
for r in rows:
    print(f"  {r[0]:<26}{r[1]:<30}{r[2]}")

# ---- 渐进式改造步骤 ----
print("\n== 渐进式改造步骤 ==")
for item in [
    "1. 先跑 mypy --strict，记录错误数量作为基线",
    "2. 从“叶子模块”开始加注解（不依赖别人的）",
    "3. dict 数据用 TypedDict，业务对象用 dataclass",
    "4. 对第三方无类型库用 types-* 包或 stub",
    "5. 存量无法修复处用 # type: ignore[code] 并记录原因",
    "6. CI 固定 mypy + ruff，防止回退",
]:
    print("  ", item)

# ---- 配置建议 ----
print("\n== pyproject 配置 ==")
print("""
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
show_error_codes = true

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
""")

# ---- 边界 ----
print("== 类型检查的边界 ==")
for item in [
    "mypy 不检查运行时数据（JSON/数据库返回值仍要校验）",
    "Any 会绕过检查，要限制使用",
    "类型不能保证业务正确（金额不能为负仍需断言/校验）",
    "动态特性（getattr/exec）会让静态分析失效",
    "类型 + 测试 + 代码评审 + 监控，才是完整质量体系",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给一个旧模块加类型，统计 mypy 错误从 N 到 0 的过程。
# 2. 用 TypedDict 描述外部 API 返回，并在边界处做运行时校验。
# 3. 在 CI 配置里加 mypy + ruff 两步检查。
# 4. 思考：为什么“先加类型再重构”比“边重构边加类型”更稳？
