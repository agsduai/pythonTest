# ===== 第544课：元编程与插件系统-插件发现与加载 =====
# 知识点：
#   - 插件系统 = 稳定接口（Protocol/ABC）+ 注册表 + 动态发现
#   - 发现方式：扫描目录（本课）、入口点 entry_points（安装包）、配置指定
#   - importlib.util.spec_from_file_location：从任意 .py 文件加载模块
#   - 插件文件暴露统一约定（如 PLUGIN 对象），核心不依赖具体类
#   - 隔离：插件异常不能拖垮主程序；加载失败要记录并跳过
#   - 与第540课注册表、第262课适配器、第51章打包入口点的关系
# 依赖：无（importlib 标准库）

import importlib.util
import tempfile
from pathlib import Path
from typing import Protocol


class Plugin(Protocol):
    name: str

    def run(self, text: str) -> str: ...


def load_plugins(directory: Path) -> dict[str, object]:
    """扫描目录，加载每个 .py 里的 PLUGIN 对象。"""
    plugins = {}
    for path in sorted(Path(directory).glob("*.py")):
        module_name = f"plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError("无法创建模块 spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)          # 执行插件文件
        except Exception as exc:
            print(f"  [跳过] {path.name}: {type(exc).__name__}: {exc}")
            continue

        plugin = getattr(module, "PLUGIN", None)
        if plugin is None:
            print(f"  [跳过] {path.name}: 没有 PLUGIN 对象")
            continue
        if not hasattr(plugin, "run") or not getattr(plugin, "name", None):
            print(f"  [跳过] {path.name}: PLUGIN 缺少 name/run")
            continue
        plugins[plugin.name] = plugin
        print(f"  [加载] {plugin.name} ← {path.name}")
    return plugins


# ---------------- 准备插件目录 ----------------
with tempfile.TemporaryDirectory() as tmp:
    plugin_dir = Path(tmp) / "plugins"
    plugin_dir.mkdir()

    (plugin_dir / "upper_plugin.py").write_text(
        "class Upper:\n"
        "    name = 'upper'\n"
        "    def run(self, text):\n"
        "        return text.upper()\n\n"
        "PLUGIN = Upper()\n",
        encoding="utf-8",
    )
    (plugin_dir / "reverse_plugin.py").write_text(
        "class Reverse:\n"
        "    name = 'reverse'\n"
        "    def run(self, text):\n"
        "        return text[::-1]\n\n"
        "PLUGIN = Reverse()\n",
        encoding="utf-8",
    )
    # 一个坏插件：加载时抛异常
    (plugin_dir / "broken_plugin.py").write_text(
        "raise RuntimeError('插件初始化失败')\n",
        encoding="utf-8",
    )
    # 一个缺少约定的插件
    (plugin_dir / "bad_contract.py").write_text(
        "class NotAPlugin:\n"
        "    pass\n\n"
        "PLUGIN = NotAPlugin()\n",
        encoding="utf-8",
    )

    print("== 扫描插件 ==")
    plugins = load_plugins(plugin_dir)
    print("\n  可用插件：", sorted(plugins))

    print("\n== 使用插件 ==")
    text = "Hello Plugin"
    for name, plugin in plugins.items():
        try:
            print(f"  {name:8s} → {plugin.run(text)!r}")
        except Exception as exc:
            print(f"  {name:8s} 执行失败：{exc}")

    # ---- 运行时新增插件：重新扫描即可 ----
    print("\n== 新增插件后重新扫描 ==")
    (plugin_dir / "shout_plugin.py").write_text(
        "class Shout:\n"
        "    name = 'shout'\n"
        "    def run(self, text):\n"
        "        return text + '!!!'\n\n"
        "PLUGIN = Shout()\n",
        encoding="utf-8",
    )
    plugins = load_plugins(plugin_dir)
    print("  可用插件：", sorted(plugins))
    print("  调用 shout：", plugins["shout"].run(text))

# ---- 安全与工程注意 ----
print("\n== 插件系统注意 ==")
for item in [
    "插件是代码：只加载可信来源，动态执行 = 任意代码执行",
    "接口要小而稳（name/run），版本不兼容要有约定",
    "单个插件异常要捕获，不能拖垮主流程",
    "加载顺序/依赖关系要可控（按 order 字段排序）",
    "生产可用 entry_points 发现已安装包里的插件（第51章）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给插件增加 order 字段，按顺序执行。
# 2. 实现“插件配置”：只启用 config 里列出的插件。
# 3. 把 PLUGIN 支持为“类”而不是实例，由加载器实例化。
# 4. 思考：为什么插件接口要用 Protocol/ABC，而不是约定一个基类？
