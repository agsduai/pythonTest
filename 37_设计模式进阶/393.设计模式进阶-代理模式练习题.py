# ===== 第393课：设计模式进阶-代理模式 =====
# 知识点：
#   - 代理：在“真实对象”外面包一层，控制访问方式（缓存、懒加载、权限、日志）
#   - 调用方只依赖共同接口，不需要知道背后是真实对象还是代理
#   - 缓存代理：重复请求命中缓存，避免重复开销
#   - 保护代理：无权限时直接拒绝，真实对象根本不会被创建
#   - 与第262课适配器的区别：适配器改接口，代理不改接口只加控制
import time
from abc import ABC, abstractmethod


class Image(ABC):

    @abstractmethod
    def display(self) -> str: ...


class RealImage(Image):
    """真实对象：加载很慢（模拟磁盘/网络）。"""

    def __init__(self, name: str):
        self.name = name
        print(f"  [磁盘] 正在加载 {name} ...")
        time.sleep(0.05)                  # 模拟耗时

    def display(self) -> str:
        return f"显示图片 {self.name}"


class CachingProxy(Image):
    """缓存代理：同一张图只加载一次。"""

    _cache: dict[str, RealImage] = {}

    def __init__(self, name: str):
        self.name = name

    def display(self) -> str:
        if self.name not in self._cache:
            self._cache[self.name] = RealImage(self.name)
        else:
            print(f"  [缓存] 命中 {self.name}")
        return self._cache[self.name].display()


class LazyProxy(Image):
    """懒加载代理：第一次 display 时才创建真实对象。"""

    def __init__(self, name: str):
        self.name = name
        self._real = None

    def display(self) -> str:
        if self._real is None:
            print("  [懒加载] 首次访问，现在才初始化")
            self._real = RealImage(self.name)
        return self._real.display()


# ---- 缓存代理：三次访问只加载一次 ----
print("== 缓存代理 ==")
start = time.perf_counter()
for _ in range(3):
    proxy = CachingProxy("banner.png")
    print(" ", proxy.display())
print(f"总耗时 {time.perf_counter() - start:.2f} 秒（只有第一次真加载）")

# ---- 懒加载：构造时不加载 ----
print("\n== 懒加载代理 ==")
img = LazyProxy("photo.jpg")
print("对象已创建，但还没加载")
print(" ", img.display())
print(" ", img.display())

# ---- 保护代理：权限校验发生在最外层 ----
print("\n== 保护代理 ==")


class ProtectedImage(Image):

    def __init__(self, name: str, user_role: str):
        self.name, self.role = name, user_role
        self._real = None

    def display(self) -> str:
        if self.role != "admin":
            return f"拒绝访问：{self.role} 无权查看 {self.name}"
        if self._real is None:
            self._real = RealImage(self.name)
        return self._real.display()


print(" ", ProtectedImage("财报.png", "guest").display())
print(" ", ProtectedImage("财报.png", "admin").display())

# ===== 练习题 =====
# 1. 给 CachingProxy 增加“缓存大小上限 + LRU 淘汰”。
# 2. 实现日志代理：每次调用真实对象前打印时间戳。
# 3. 思考：代理与第187课的装饰器是否很像？区别在哪一层？
