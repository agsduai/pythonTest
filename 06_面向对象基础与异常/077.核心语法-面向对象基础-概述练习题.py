# ===== 第077课：核心语法-面向对象基础-概述 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 面向对象：把“数据”和“操作数据的方法”组织在一起
#   - 类：一类事物的模板，例如“学生”“汽车”
#   - 对象：根据类创建出来的具体实例，例如“小明”
#   - 属性：对象保存的数据；方法：对象能执行的操作
#   - 封装：把属性、方法写进类中，通过对象访问

# 先看一个“空类”，它只是一个模板
class Student:
    """学生类：目前只有类名，具体信息创建对象后再添加。"""

# 根据类创建对象（也叫实例化）
student1 = Student()
student2 = Student()

# 给对象添加属性（后面会用 __init__ 统一初始化）
student1.name = "小明"
student1.age = 18
student2.name = "小红"
student2.age = 19

print(student1.name, student1.age)
print(student2.name, student2.age)

# 两个对象互不影响
student1.age = 20
print("修改后：", student1.age, student2.age)

# 查看对象由哪个类创建
print(type(student1))
print(isinstance(student1, Student))

# 生活类比：list 是类，具体列表是对象；字符串也是对象
names = ["小明", "小红"]
print(type(names))
print("大写：", "python".upper())

# ===== 练习题 =====
# 1. 定义一个空类 Car，创建两个对象，分别添加 brand 和 price 属性。
# 2. 修改其中一个对象的属性，验证两个对象互不影响。
# 3. 用 type() 和 isinstance() 查看列表对象与字符串对象。
