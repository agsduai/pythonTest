# ===== 第011课：核心语法-数据存储与运算-标识符 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 标识符：给变量、函数、类等起的名字
#   - 组成：字母、数字、下划线、中文（不推荐）
#   - 规则：不能以数字开头，不能包含空格，不能是关键字，区分大小写
#   - 规范：见名知意、小写下划线、常量全大写

# 合法的标识符
user_name = "小明"      # 下划线命名（推荐）
userName = "小红"       # 小驼峰命名
_name = "以下划线开头也是合法的"
age2 = 18               # 数字可以出现在中间或末尾
MAX_COUNT = 100         # 全大写通常表示常量
中文名字 = "中文也可以，但实际开发不推荐"
print(user_name, userName, _name, age2, MAX_COUNT, 中文名字)

# 以下写法都是不合法的（仅作说明，取消注释会报错）
# 2age = 18          # 不能以数字开头
# user name = "小明"  # 不能包含空格
# user-name = "小明"  # 不能包含减号
# class = "班级"      # class 是 Python 关键字

# 关键字是 Python 内部已经使用的名字，不能再拿来当标识符
# 常见关键字：if、else、for、while、def、class、True、False、None

# 标识符区分大小写
name = "小写 name"
Name = "大写 Name"
print(name)
print(Name)

# 好的命名让人一眼看懂含义
student_name = "李四"
student_age = 20
print(student_name, student_age)

# ===== 练习题 =====
# 1. 判断下列哪些是合法标识符，并在注释里写明原因：
#    my_name、2name、user-name、_count、class、StudentName、my name
# 2. 定义三个变量保存书名、作者、价格，变量名要见名知意。
# 3. 定义变量 Name 和 name 并分别赋值，输出它们，体会大小写敏感。
# 4. 把不规范的名字 a1、b2 改写成有含义的变量名，并保存同样的数据。
