# ===== 第993课：数据验证与转换-综合案例-表单验证器 =====
# 知识点：
#   - 验证器封装成函数：接收数据，返回 (是否通过, 错误列表)
#   - 多字段验证：每个字段有自己的验证规则
#   - 一次返回全部错误 —— 用户可以一次性修改所有问题
#   - 实际场景：用户注册表单验证

import re


# ---------- 验证规则函数 ----------
def validate_name(name):
    """验证姓名：非空、长度 2-10、不含特殊字符。"""
    errors = []
    if not name or not name.strip():
        errors.append("姓名不能为空")
        return errors
    name = name.strip()
    if len(name) < 2:
        errors.append("姓名至少 2 个字符")
    if len(name) > 10:
        errors.append("姓名不能超过 10 个字符")
    if re.search(r'[<>@#$%]', name):
        errors.append("姓名不能包含特殊字符 < > @ # $ %")
    return errors


def validate_email(email):
    """验证邮箱：非空、包含 @ 和 .、@ 在 . 之前。"""
    errors = []
    if not email or not email.strip():
        errors.append("邮箱不能为空")
        return errors
    email = email.strip()
    if "@" not in email:
        errors.append("邮箱缺少 @ 符号")
        return errors
    at_pos = email.index("@")
    dot_pos = email.rfind(".")
    if at_pos == 0:
        errors.append("@ 不能在开头")
    if dot_pos < at_pos + 1:
        errors.append("@ 后面缺少域名")
    if dot_pos == len(email) - 1:
        errors.append(". 不能在结尾")
    return errors


def validate_phone(phone):
    """验证手机号：11 位、纯数字、以 1 开头。"""
    errors = []
    if not phone or not phone.strip():
        errors.append("手机号不能为空")
        return errors
    phone = phone.strip()
    if len(phone) != 11:
        errors.append(f"手机号应为 11 位，当前 {len(phone)} 位")
    if not phone.isdigit():
        errors.append("手机号只能包含数字")
    if phone and not phone.startswith("1"):
        errors.append("手机号应以 1 开头")
    return errors


def validate_age(age_text):
    """验证年龄：纯数字、范围 1-150。"""
    errors = []
    if not age_text or not age_text.strip():
        errors.append("年龄不能为空")
        return errors
    if not age_text.strip().isdigit():
        errors.append("年龄必须是正整数")
        return errors
    age = int(age_text)
    if age < 1 or age > 150:
        errors.append(f"年龄 {age} 超出范围 (1-150)")
    return errors


# ---------- 表单验证器 ----------
def validate_form(form):
    """验证整个表单，返回所有错误。"""
    all_errors = {}
    name_errors = validate_name(form.get("name", ""))
    if name_errors:
        all_errors["name"] = name_errors
    email_errors = validate_email(form.get("email", ""))
    if email_errors:
        all_errors["email"] = email_errors
    phone_errors = validate_phone(form.get("phone", ""))
    if phone_errors:
        all_errors["phone"] = phone_errors
    age_errors = validate_age(form.get("age", ""))
    if age_errors:
        all_errors["age"] = age_errors
    return all_errors


print("== 表单验证器 ==")

# 测试用例
test_forms = [
    {"name": "张三", "email": "zs@test.com", "phone": "13812345678", "age": "25"},
    {"name": "", "email": "bad-email", "phone": "123", "age": "300"},
    {"name": "李四", "email": "", "phone": "", "age": ""},
]

for i, form in enumerate(test_forms):
    errors = validate_form(form)
    print(f"\n  表单 {i + 1}: {form}")
    if not errors:
        print(f"    ✓ 验证通过")
    else:
        print(f"    ✗ {len(errors)} 个字段有问题:")
        for field, field_errors in errors.items():
            for err in field_errors:
                print(f"      [{field}] {err}")

# ===== 练习题 =====
# 1. 增加密码验证规则：≥ 8 位、含大小写和数字。
# 2. 增加确认密码字段：必须与密码一致。
# 3. 实现验证器「通过后返回清洗后的数据」（如 strip 后的 name）。
# 4. 思考：为什么验证器返回错误列表而不是抛异常？什么场景应该抛异常？
