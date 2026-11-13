# ===== 第061课：核心语法-函数基础-函数嵌套调用 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 函数内部可以调用另一个函数，称为嵌套调用
#   - 执行顺序：遇到内层函数调用时，先完成内层再回到外层
#   - 嵌套调用可以把复杂任务拆分成多个职责单一的小函数
#   - 注意先定义被调用的函数，再定义调用它的函数

def is_even(number):
    return number % 2 == 0

def count_even(numbers):
    count = 0
    for n in numbers:
        if is_even(n):         # 在函数内部调用另一个函数
            count += 1
    return count

def show_even_info(numbers):
    count = count_even(numbers)   # 嵌套调用 count_even
    print(f"列表 {numbers} 中有 {count} 个偶数")

show_even_info([1, 2, 3, 4, 5, 6])

# 三层嵌套：show_report -> get_average -> get_total
def get_total(numbers):
    return sum(numbers)

def get_average(numbers):
    if len(numbers) == 0:
        return 0
    return get_total(numbers) / len(numbers)

def show_report(numbers):
    print("数据：", numbers)
    print("总分：", get_total(numbers))
    print("平均分：", round(get_average(numbers), 2))

show_report([80, 90, 70])

# 执行顺序：show_report 先调用 get_total，
# 再调用 get_average，而 get_average 内部又调用 get_total

# ===== 练习题 =====
# 1. 定义 is_positive(n) 判断正数，再定义 count_positive(numbers) 统计正数个数。
# 2. 定义 get_level(score) 返回等级，再定义 print_level(name, score) 调用它输出。
# 3. 编写三层嵌套：show_summary(numbers) 调用 get_average(numbers)，get_average 调用 get_total(numbers)。
