num1 = float(input("请输入第一个数字"))
yun = input("请输入运算符")
num2 = float(input("请输入第二个数字"))

match yun:
    case "+":
        print(f"{num1}+{num2}=",num1+num2)
    case "-":
        print(f"{num1}-{num2}=", num1 - num2)
    case "*":
        print(f"{num1}*{num2}=", num1 * num2)
    case "/":
        print(f"{num1}/{num2}=", num1 / num2)
    case _:
        print("符合输入有误")