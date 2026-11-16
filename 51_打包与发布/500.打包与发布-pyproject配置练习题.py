# ===== 第500课：打包与发布-pyproject.toml =====
# 知识点：
#   - pyproject.toml 是现代 Python 项目的统一配置入口（PEP 518/621）
#   - [build-system]：构建后端与依赖（setuptools/hatchling/poetry 等）
#   - [project]：元数据（name/version/description/readme/license/requires-python）
#   - dependencies：运行依赖；optional-dependencies：分组可选依赖
#   - [project.scripts]：命令行入口（安装后生成可执行文件）
#   - [tool.*]：各工具自己的配置（setuptools/pytest/ruff...）
#   - 与第217/218课的关系：依赖清单不再只靠 requirements.txt
# 依赖：无（tomllib 标准库）

import tempfile
import tomllib
from pathlib import Path

PYPROJECT = """
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "text-tools"
version = "1.2.0"
description = "文本处理小工具"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "课程学员", email = "student@example.com"}]
keywords = ["text", "cli", "demo"]
dependencies = [
    "requests>=2.31",
    "click>=8.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.4"]
docs = ["sphinx>=7"]

[project.scripts]
text-tools = "text_tools.cli:main"

[project.urls]
Homepage = "https://example.com/text-tools"
Repository = "https://example.com/text-tools.git"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
"""

data = tomllib.loads(PYPROJECT)
print("== 解析 pyproject.toml ==")
print("  顶层键：", list(data))

project = data["project"]
print("\n== [project] 元数据 ==")
for key in ("name", "version", "description", "requires-python", "license"):
    print(f"  {key}: {project[key]}")

print("\n  运行依赖：")
for dep in project["dependencies"]:
    print("   -", dep)

print("\n  可选依赖组：")
for group, deps in project["optional-dependencies"].items():
    print(f"   {group}: {deps}")

print("\n  命令行入口：", project["scripts"])
print("  构建后端：", data["build-system"]["build-backend"])
print("  pytest 配置：", data["tool"]["pytest"]["ini_options"])

# ---- 校验：name 与 version 是必填 ----
def validate_pyproject(data: dict) -> list[str]:
    errors = []
    if "build-system" not in data:
        errors.append("缺少 [build-system]")
    project = data.get("project", {})
    for field in ("name", "version"):
        if not project.get(field):
            errors.append(f"[project] 缺少 {field}")
    name = project.get("name", "")
    if name and not name.replace("-", "").replace("_", "").isalnum():
        errors.append(f"项目名不合法：{name}")
    return errors


print("\n== 校验 ==")
print("  示例配置错误：", validate_pyproject(data) or "无")

bad = {"project": {"name": "bad name!", "version": ""}}
print("  错误配置：", validate_pyproject(bad))

# ---- 用 tomllib 读取真实文件 ----
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "pyproject.toml"
    path.write_text(PYPROJECT, encoding="utf-8")
    with open(path, "rb") as f:
        loaded = tomllib.load(f)
    print("\n== 从文件读取 ==")
    print("  项目名：", loaded["project"]["name"])
    print("  依赖数量：", len(loaded["project"]["dependencies"]))

# ---- 依赖版本写法 ----
print("\n== 依赖版本约束 ==")
rows = [
    ("requests>=2.31", "至少 2.31"),
    ("click==8.1.7", "精确锁定（少用）"),
    ("pandas~=2.2", "兼容 2.x（>=2.2,<3）"),
    ("numpy>=1.26,<3", "区间约束"),
]
for spec, desc in rows:
    print(f"  {spec:22s} {desc}")

# ---- 构建配置注意 ----
print("\n== 注意 ==")
for item in [
    "requires-python 影响 pip 选择可用版本，不要漏",
    "动态版本可用 [tool.setuptools.dynamic] 或 importlib.metadata",
    "src 布局要配置 packages.find where=['src']",
    "可选依赖用 pip install '包名[dev]' 安装",
    "不要把密钥写进 pyproject.toml（第402课环境变量）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给示例增加 [project.optional-dependencies] 的 test 组。
# 2. 写函数读取 pyproject.toml 并打印所有可选依赖组。
# 3. 故意漏掉 version，验证 validate_pyproject 报错。
# 4. 思考：requirements.txt 与 pyproject.toml 各适合什么场景？
