# ===== 第218课：测试与工程化-代码规范与项目结构 =====
# 知识点：
#   - PEP 8 要点：蛇形命名、4 空格缩进、运算符两侧空格、导入置顶
#   - 命名：变量/函数用 snake_case，类用 PascalCase，常量用 UPPER_CASE
#   - 可运行文件的入口写 if __name__ == "__main__":
#   - 典型项目结构：源码包 + tests + requirements.txt + README
#   - 工具：black 自动格式化，ruff / flake8 静态检查


# ---- 规范示例：对比不规范与规范的写法 ----

# 不规范：
# def AddNum(A,B):return A+B

# 规范：
def add_num(a, b):
    """返回两数之和。"""
    return a + b


# 类名 PascalCase，属性 snake_case，常量全大写
class OrderService:
    MAX_LIMIT = 1000        # 常量：UPPER_CASE

    def __init__(self):
        self.order_count = 0

    def create_order(self, price):
        if price > self.MAX_LIMIT:
            raise ValueError("超出单笔限额")
        self.order_count += 1
        return self.order_count


# ---- __main__ 入口：被 import 时不执行，被 python 直接运行时才执行 ----
def demo():
    service = OrderService()
    service.create_order(99)
    print("当前订单数：", service.order_count)


if __name__ == "__main__":      # 别的文件 import 本模块时，下面不会执行
    demo()

# ---- 推荐的项目结构（注释示意）----
# pyproject01/
# ├── 01_数据存储与运算/        # 按主题分章的练习
# ├── mypackage/                # 可复用的源码包
# │   ├── __init__.py
# │   └── core.py
# ├── tests/                    # 测试代码与源码分离
# │   └── test_core.py
# ├── requirements.txt          # 依赖清单
# └── README.md                 # 项目说明

# ===== 练习题 =====
# 1. 安装 black，格式化本章任意一个旧文件，对比格式化前后的差异。
# 2. 把第209课的工具改造成标准结构：mydb.py + tests/test_mydb.py。
# 3. 写一个模块 both.py，验证被 import 时 __name__ 是模块名、直接运行时是 __main__。
# 4. 思考：为什么“测试与源码分离”比混在一起好？
