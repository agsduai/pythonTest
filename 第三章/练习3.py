# a1 = int(input("1"))
# b = input("计算")
# a2 = int(input("2"))
#
# match b:
#     case "+":
#         print(a1 + a2)
#     case "-":
#         print(a1 - a2)
#     case "*":
#         print(a1 * a2)
#     case "/":
#         print(a1 / a2)
#     case _:
#         print("这不是在计算")
ml = input("输入指令")
match ml:
    case "1" | "W" | "w":
        print("角色向上移动")
    case "2" | "A" | "a":
        print("角色向1移动")
    case "3" | "S" | "s":
        print("角色向2移动")
    case " ":
        print("角色跳")
    case "J" | "j":
        print("角色向攻击")
    case "6" | "esc" | "ESC":
        print("推出游戏")
    case "7" | "D" | "d":
        print("角色向3移动")
    case _:
        print("meiyou")