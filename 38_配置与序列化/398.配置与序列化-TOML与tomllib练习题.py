# ===== 第398课：配置与序列化-TOML与tomllib =====
# 知识点：
#   - TOML：现代配置文件格式，支持字符串/数字/布尔/数组/嵌套表/日期
#   - Python 3.11+ 内置 tomllib（只读）；写 TOML 需手工拼或第三方库
#   - 语法：[project] 建表、[[items]] 建数组表、key = value 赋值
#   - pyproject.toml 就是 TOML：依赖、构建、工具配置都放这里
#   - 与 JSON 对比：允许注释、可读性更好、天然支持日期
import tempfile
import tomllib
from datetime import date
from pathlib import Path

TOML_TEXT = """
# 应用配置示例
[project]
name = "demo-app"
version = "0.1.0"
dependencies = ["numpy", "pandas"]

[server]
host = "127.0.0.1"
port = 8080
debug = true
timeout = 30.5

[meta]
created = 2026-11-13          # TOML 原生日期
tags = ["dev", "course"]

[[plugins]]
name = "logger"
enabled = true

[[plugins]]
name = "cache"
enabled = false
"""

# ---- 解析字符串 ----
data = tomllib.loads(TOML_TEXT)
print("顶层键：", list(data))
print("项目名：", data["project"]["name"])
print("依赖：", data["project"]["dependencies"])
print("端口类型：", type(data["server"]["port"]).__name__)
print("debug 类型：", type(data["server"]["debug"]).__name__)
print("日期类型：", type(data["meta"]["created"]).__name__, "→", data["meta"]["created"])
print("插件数量：", len(data["plugins"]))

# ---- 数组表（[[plugins]]）解析成 list[dict] ----
for plugin in data["plugins"]:
    status = "启用" if plugin["enabled"] else "禁用"
    print(f"  插件 {plugin['name']}: {status}")

# ---- 从文件读取 ----
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "config.toml"
    path.write_text(TOML_TEXT, encoding="utf-8")
    with open(path, "rb") as f:                 # 注意：tomllib 要求二进制模式
        from_file = tomllib.load(f)
    print("\n文件读取一致：", from_file == data)

# ---- 读取本项目的 pyproject.toml（如果存在）----
project_file = Path("pyproject.toml")
if project_file.exists():
    with open(project_file, "rb") as f:
        pyproject = tomllib.load(f)
    print("\n本项目 pyproject.toml 顶层键：", list(pyproject))
else:
    print("\n当前目录没有 pyproject.toml（第 218 课讲过项目结构）")

# ---- 关键限制 ----
print("\n注意：tomllib 只读，没有 dump/write 接口")
print("写 TOML：手工拼字符串，或使用第三方库 toml/tomli-w")

# ===== 练习题 =====
# 1. 在 TOML 里增加 [database] 表，读取并打印 url 与 pool 大小。
# 2. 用 Python 字符串拼一份最小 pyproject.toml 并写入临时文件。
# 3. 验证 TOML 的日期 2026-11-13 与 datetime.date(2026,11,13) 是否相等。
# 4. 思考：什么时候用 TOML，什么时候用 JSON？（提示：人写 vs 机器交换）
