# ===== 第064课：核心语法-函数进阶-传参方式 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 位置参数：按参数定义的顺序依次传入，位置必须对应
#   - 关键字参数：用“参数名=值”的方式传入，顺序可以不同
#   - 混合使用：位置参数必须写在关键字参数前面
#   - 关键字参数让调用处的含义更清楚，减少传错位置的问题

def enroll(name, age, city):
    print(f"{name}，{age} 岁，来自 {city}")

# 方式一：全部使用位置参数
enroll("小明", 18, "北京")

# 方式二：全部使用关键字参数，顺序可以与定义不同
enroll(city="上海", age=20, name="小红")

# 方式三：混合使用，位置参数在前，关键字参数在后
enroll("小刚", city="广州", age=19)

# 错误示范：位置参数不能放在关键字参数后面
# enroll(age=18, "小李", "深圳")  # 取消注释会报 SyntaxError

# 关键字参数也可以和默认参数配合使用（下一课学习默认参数）
def book_ticket(name, train_no):
    print(f"{name} 预订了 {train_no} 次列车")

book_ticket("小明", "G101")
book_ticket(train_no="G102", name="小红")

# ===== 练习题 =====
# 1. 定义函数 register(name, age, city)，分别用位置参数、关键字参数、混合方式调用。
# 2. 下面的调用为什么错误？改正后运行：enroll(age=18, "小李", "深圳")
# 3. 定义函数 order(food, count, price)，用关键字参数调用并输出总价。
