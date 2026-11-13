# ===== 第345课：OOP进阶-property属性 =====
# 知识点：
#   - @property：把方法伪装成属性 —— 调用像字段，内部可加逻辑
#   - @x.setter：拦截赋值做校验，替代 get_x/set_x 样板代码
#   - 只读属性：只定义 getter，赋值会抛 AttributeError
#   - 内部约定：真实数据存 self._xxx，property 名义上对外

class Circle:

    def __init__(self, radius):
        self.radius = radius          # 这一步赋值会走 setter

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value <= 0:
            raise ValueError("半径必须为正数")
        self._radius = value

    @property
    def area(self):                   # 派生属性：只读
        return 3.14159 * self._radius ** 2


c = Circle(2)
print("半径：", c.radius, "| 面积：", round(c.area, 2))

c.radius = 3                        # 看起来像改字段，实际走了校验
print("改半径后面积：", round(c.area, 2))

try:
    c.radius = -1
except ValueError as exc:
    print("setter 校验拦截：", exc)

try:
    c.area = 100                    # 只读属性不可赋值
except AttributeError as exc:
    print("只读拦截：", exc)

# 对照第218课：外部仍然写 c.radius = 3，接口自然；
# 但内部多了“校验 + 派生”两层逻辑 —— 封装的正确姿势

# ===== 练习题 =====
# 1. 给 Circle 加 diameter 属性：读取返回直径，赋值时同步修改半径。
# 2. 写 Temperature 类：celsius 可读写校验，fahrenheit 只读换算。
# 3. 思考：property 与“直接暴露字段”的取舍？（简单场景直接暴露没问题）
