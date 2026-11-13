# ===== 第165课：面向对象高级-多态(鸭子类型) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 鸭子类型：不检查对象类型，只检查它是否具备需要的方法
#   - “走起来像鸭子、叫起来像鸭子，那它就是鸭子”
#   - Python 是动态类型语言，不要求这些类继承同一个父类
#   - 只要对象实现了 quack() 和 swim()，就能传给 duck_show()
#   - 鸭子类型让代码更灵活，但也要求调用前确认方法存在

class RealDuck:
    """真实的鸭子。"""

    def quack(self) -> str:
        return "嘎嘎嘎"

    def swim(self) -> str:
        return "真鸭子在水中游泳"

class ToyDuck:
    """玩具鸭：没有继承 RealDuck，但方法同名。"""

    def quack(self) -> str:
        return "玩具鸭：嘎嘎"

    def swim(self) -> str:
        return "玩具鸭漂在水面上"

class RobotDuck:
    """机器鸭：同样具备 quack 和 swim。"""

    def quack(self) -> str:
        return "机器鸭：嘎嘎（电子音）"

    def swim(self) -> str:
        return "机器鸭用螺旋桨前进"

    def charge(self) -> str:
        return "机器鸭正在充电"

def duck_show(duck: object) -> None:
    """不判断类型，只调用对象身上的方法。"""
    print(duck.quack(), "|", duck.swim())

for duck in (RealDuck(), ToyDuck(), RobotDuck()):
    duck_show(duck)          # 三个类没有共同父类，也能统一处理

print("RobotDuck 有 quack 方法：", hasattr(RobotDuck(), "quack"))
print("RobotDuck 有 fly 方法：", hasattr(RobotDuck(), "fly"))

# 鸭子类型的常见应用：任何实现了 read() 的对象都能当数据源
class FakeFile:
    def read(self) -> str:
        return "模拟文件内容"

def read_all(source: object) -> str:
    return source.read()

print("读取结果：", read_all(FakeFile()))

# ===== 练习题 =====
# 1. 定义 Circle、Square、Triangle 三个类，都实现 area 方法，
#    写 sum_area(shapes) 计算总面积，不要求它们有共同父类。
# 2. 给 RobotDuck 增加 fly 方法后，写一个通用 show 函数调用 fly，
#    再用 hasattr 判断 ToyDuck 是否支持 fly，避免报错。
# 3. 说明鸭子类型的优点和潜在风险（方法不存在时会发生什么）。
