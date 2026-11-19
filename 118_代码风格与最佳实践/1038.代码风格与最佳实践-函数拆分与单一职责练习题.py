# ===== 第1038课：代码风格与最佳实践-函数拆分与单一职责 =====
# 知识点：
#   - 一个函数只干一件事：函数名能概括全部逻辑才合格
#   - 函数超过 30 行、缩进超过 3 层，就该考虑拆分
#   - 拆分后主函数变成"目录"：读一行就知道整个流程
#   - 复用点拆成独立函数：校验、计算、格式化输出各管各的

# 案例一：一个大函数的问题 —— 什么都干，改哪都怕崩
# 场景：注册流程混在一起（校验、保存、通知全在一个函数里）
def register_bad(username, password):
    if len(username) < 3:  # 校验
        print("用户名太短")
        return False
    if len(password) < 8:
        print("密码太短")
        return False
    print(f"保存用户 {username}")  # 保存
    print(f"给 {username} 发欢迎邮件")  # 通知
    return True

register_bad("xiaozhang", "12345678")

# 案例二：拆分成单一职责的小函数
def validate_user(username, password):
    """只负责校验，返回 (是否通过, 原因)。"""
    if len(username) < 3:
        return False, "用户名太短"
    if len(password) < 8:
        return False, "密码太短"
    return True, ""

def save_user(username):
    """只负责保存。"""
    print(f"保存用户 {username}")

def send_welcome(username):
    """只负责发通知。"""
    print(f"给 {username} 发欢迎邮件")

def register_good(username, password):
    """主函数变成流程目录：校验 -> 保存 -> 通知。"""
    ok, reason = validate_user(username, password)
    if not ok:
        print(f"注册失败：{reason}")
        return False
    save_user(username)
    send_welcome(username)
    return True

register_good("xiaoli", "12345678")

# 案例三：深层嵌套的拆平 —— 提前返回减少缩进
# 烂：三层嵌套才能看到核心逻辑
def grade_bad(score):
    if score is not None:
        if 0 <= score <= 100:
            if score >= 60:
                return "及格"
            else:
                return "不及格"
        else:
            return "分数非法"
    else:
        return "没有分数"

# 好：先排除异常情况，主逻辑不缩进
def grade_good(score):
    if score is None:
        return "没有分数"
    if not (0 <= score <= 100):
        return "分数非法"
    return "及格" if score >= 60 else "不及格"

print(grade_good(None), grade_good(105), grade_good(88))

# 案例四：拆分后的复用收益
# 校验函数单独拆出来后，注册、改密码两处都能用
def change_password(old_ok, new_password):
    ok, reason = validate_user("x", new_password)  # 复用校验
    if not ok:
        print(f"改密失败：{reason}")
        return False
    print("改密成功")
    return True

change_password(True, "short")  # 密码太短
change_password(True, "newpass123")

# ===== 练习题 =====
# 1. 把"读订单列表 -> 过滤金额>=100 -> 计算总价 -> 打印"拆成 4 个单一职责函数并在主函数里依次调用。
# 2. 将三层嵌套的登录判断（用户存在？密码对？账号未冻结？）改写成"提前返回"风格。
# 3. 写一个超过 30 行的"成绩处理大函数"（故意写长），再拆成 load/validate/analyze/report 四个函数对比可读性。
