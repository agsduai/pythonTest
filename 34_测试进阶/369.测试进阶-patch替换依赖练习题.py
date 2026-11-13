# ===== 第369课：测试进阶-patch替换依赖 =====
# 知识点：
#   - patch("路径")：测试期间把某个名字换成 Mock，退出自动还原
#   - 黄金法则：patch“被使用的地方”，而不是“被定义的地方”
#   - 三种形态：with patch(...) / @patch 装饰器 / patcher.start/stop
#   - 路径怎么写：从被测函数所在模块出发，到那个名字的完整点路径
import os
from unittest.mock import patch


def read_config():
    return os.getenv("APP_MODE", "dev")        # 使用了 os.getenv


# ---- with 形态：块内替换，块外还原 ----
print("原始值：", read_config())
with patch("os.getenv", return_value="prod"):
    print("替换后：", read_config())
print("退出 with 自动还原：", read_config())

# ---- @patch 装饰器：mock 作为参数注入（从下往上）----
@patch("os.getenv", return_value="stage")
def run(fake_getenv):                          # 参数名随意，但位置固定在最后
    return read_config(), (fake_getenv is os.getenv)


result, same_object = run()
print("装饰器形式：", result, "| 注入的就是同一个 Mock：", same_object)

# ---- patcher 对象：手动 start/stop（setUp/tearDown 里常用）----
patcher = patch("os.getenv", return_value="test")
patcher.start()
print("start 后：", read_config())
patcher.stop()
print("stop 后：", read_config())

# ---- 路径法则演示：替换“自己模块里的名字” ----
APP_MODE = "dev"


def read_own():
    return APP_MODE                            # 用的是本模块全局名


with patch("__main__.APP_MODE", "prod"):       # 脚本运行时本模块叫 __main__
    print("替换本模块全局：", read_own())
print("还原：", read_own())

# ===== 练习题 =====
# 1. 把 patch 目标写成 "os.putenv"（没用到的名字），验证 read_config 不受影响。
# 2. 用 patch 模拟 time.time 返回固定值，测试“有效期判断”函数。
# 3. 思考：为什么 patch 定义处（os.getenv 定义在标准库源码里）没有意义？
