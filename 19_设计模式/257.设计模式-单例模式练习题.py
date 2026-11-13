# ===== 第257课：设计模式-单例模式 =====
# 知识点：
#   - 单例：一个类全局只有一个实例（配置、连接池、日志器）
#   - 实现①：__new__ 拦截实例创建
#   - 实现②：模块级变量 —— Python 最惯用的“模块即单例”
#   - 实现③：装饰器包一层
#   - 坑：__init__ 每次都会执行，重复初始化要自己防


# ---- 实现①：__new__ 版 ----
class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "settings"):    # 防 __init__ 重复执行
            self.settings = {}


c1 = Config()
c2 = Config()
c1.settings["theme"] = "dark"
print(c2.settings)     # {'theme': 'dark'} —— 拿到的是同一个对象
print(c1 is c2)        # True


# ---- 实现②：模块单例（最 Pythonic） ----
# 建一个 settings.py，里面直接写 SETTINGS = {...}
# 任何文件 import SETTINGS 拿到的都是同一份 —— 模块天然只导入一次
SETTINGS = {"app": "课程项目", "debug": True}
print(SETTINGS)


# ---- 实现③：装饰器版 ----
def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Logger:

    def __init__(self):
        self.logs = []


l1 = Logger()
l2 = Logger()
l1.logs.append("第一条日志")
print(l2.logs, "| 同一实例：", l1 is l2)

# ===== 练习题 =====
# 1. 创建 settings.py 模块单例，在两个文件里 import 并验证 is 为 True。
# 2. 给 Config 加 load(path) 方法，思考为什么必须防重复初始化。
# 3. 多线程下单例有竞态风险：用第196课的 Lock 包住“判断+创建”。
# 4. 思考：什么情况下单例反而是坏设计？（提示：全局状态难测试）
