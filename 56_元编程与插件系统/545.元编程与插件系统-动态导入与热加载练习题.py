# ===== 第545课：元编程与插件系统-动态导入与热加载 =====
# 知识点：
#   - importlib.import_module：按字符串导入，等价于 import 语句
#   - importlib.util.spec_from_file_location：从文件路径加载模块（第544课）
#   - importlib.reload：重新执行模块代码，开发时热更新
#   - reload 的限制：已导入的旧引用不会自动更新；模块级状态会保留一部分
#   - 生产不建议依赖 reload：用进程重启/滚动发布更可靠
#   - 与第25/51章包结构、第403课配置热加载的区别：那是配置，这是代码
# 依赖：无（importlib 标准库）

import importlib
import importlib.util
import sys
import tempfile
from pathlib import Path

# ---------------- 1. 按名字导入 ----------------
print("== import_module ==")
json_module = importlib.import_module("json")
print("  模块：", json_module.__name__)
print("  dumps：", json_module.dumps({"ok": True}))

# 按名字导入自己写的临时模块
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    sys.path.insert(0, str(tmp))

    module_path = tmp / "greet_mod.py"
    module_path.write_text(
        'VERSION = "1.0"\n'
        'def greet(name):\n'
        '    return f"你好，{name}（v{VERSION}）"\n',
        encoding="utf-8",
    )

    print("\n== 首次导入 ==")
    mod = importlib.import_module("greet_mod")
    print("  版本：", mod.VERSION)
    print("  调用：", mod.greet("小明"))

    # ---------------- 2. 热加载 ----------------
    print("\n== 修改文件后 reload ==")
    module_path.write_text(
        'VERSION = "2.0"\n'
        'def greet(name):\n'
        '    return f"欢迎回来，{name}（v{VERSION}）"\n',
        encoding="utf-8",
    )
    # 直接调用旧引用仍是旧行为
    print("  未 reload：", mod.greet("小红"))
    importlib.reload(mod)
    print("  reload 后：", mod.greet("小红"))
    print("  版本：", mod.VERSION)

    # ---------------- 3. reload 的引用陷阱 ----------------
    print("\n== 旧引用陷阱 ==")
    old_greet = mod.greet                  # 保存旧函数引用
    importlib.reload(mod)                  # 再次 reload（文件未变）
    print("  模块内新引用：", mod.greet("小刚"))
    print("  保存的旧引用：", old_greet("小刚"), "（仍指向旧函数对象）")

    # ---------------- 4. 从文件路径加载（不依赖 sys.path） ----------------
    print("\n== 从路径加载 ==")
    other = tmp / "other_mod.py"
    other.write_text("def value():\n    return 42\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("other_mod", other)
    other_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(other_mod)
    print("  other_mod.value() =", other_mod.value())
    print("  是否进入 sys.modules：", "other_mod" in sys.modules,
          "（默认不进入，需要手动注册）")

    sys.path.remove(str(tmp))
    for name in ("greet_mod", "other_mod"):
        sys.modules.pop(name, None)

# ---------------- 5. 什么时候用 ----------------
print("\n== 适用场景 ==")
for item in [
    "按配置加载不同实现（数据库驱动/支付渠道）",
    "插件系统扫描目录（第544课）",
    "开发期热更新（reload）",
    "测试时替换模块（unittest.mock.patch 内部也依赖导入机制）",
]:
    print("  -", item)

print("\n== reload 的限制 ==")
for item in [
    "已 from module import func 的引用不会更新",
    "类的实例不会重建，旧实例仍属于旧类",
    "模块级全局变量部分保留，可能造成状态不一致",
    "C 扩展模块通常不支持 reload",
    "生产用滚动重启/蓝绿发布，不要靠 reload",
]:
    print("  -", item)

# ---------------- 6. 安全提醒 ----------------
print("\n== 安全提醒 ==")
print("  动态导入的模块名如果来自用户输入，必须白名单校验")
print("  例如只允许 importlib.import_module(f'plugins.{name}') 且 name 在允许列表")

# ===== 练习题 =====
# 1. 用 import_module 按配置加载 json 或 csv 模块并调用。
# 2. 写 hot_reload(path) 函数：按路径加载并在文件变化时 reload。
# 3. 模拟“from greet_mod import greet”的旧引用，验证 reload 不更新。
# 4. 思考：为什么很多框架选择“重启进程”而不是热加载代码？
