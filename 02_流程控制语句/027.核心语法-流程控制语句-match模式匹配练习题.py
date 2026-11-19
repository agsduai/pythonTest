# ===== 第027课：核心语法-流程控制语句-match模式匹配 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - match 语句按值进行模式匹配（Python 3.10 及以上）
#   - case 后面写具体值，匹配成功后执行对应代码块
#   - case 值1 | 值2 可以一次匹配多个值
#   - case _ 是通配符分支，通常放在最后兜底

# 示例一：简单的菜单选择
choice = "2"
match choice:
    case "1":
        print("开始新游戏")
    case "2":
        print("加载存档")  # choice 为 "2"，命中这一分支
    case "3":
        print("退出游戏")
    case _:
        print("输入无效")

# 示例二：用 | 匹配多个值
day = 6
match day:
    case 6 | 7:
        print("周末，休息一下")
    case 1 | 2 | 3 | 4 | 5:
        print("工作日，认真上课")
    case _:
        print("日期不合法")

# 示例三：匹配 HTTP 状态码
status = 404
match status:
    case 200:
        print("请求成功")
    case 404:
        print("页面不存在")
    case 500:
        print("服务器错误")
    case _:
        print("其他状态码")

# ===== 练习题 =====
# 1. 定义变量 command = "start"，用 match 判断："start" 输出“启动”，"stop" 输出“停止”，其他输出“未知命令”。
command = "start"
match command:
    case "start":
        print("启动")
    case "stop":
        print("停止")
    case _:
        print("未知命令")
# 2. 定义变量 month = 12，用 match 判断季节：3/4/5 春季，6/7/8 夏季，9/10/11 秋季，12/1/2 冬季。
month =12
match month:
    case 3 | 4 | 5:
        print("春节")
    case 6 | 7 | 8:
        print("夏季")
    case 9 | 10 | 11:
        print("秋天")
    case 12 | 1 | 2:
        print("冬天")
    case _:
        print("错误")
# 3. 定义变量 grade = "A"，用 match 判断："A" 输出“优秀”，"B" 输出“良好”，"C" 或 "D" 输出“继续加油”，其他输出“成绩无效”。
grade = "A"
match grade:
    case "A":
        print("优秀")
    case "B":
        print("良好")
    case "C" | "D":
        print("加油")
    case _:
        print("成绩无效")
