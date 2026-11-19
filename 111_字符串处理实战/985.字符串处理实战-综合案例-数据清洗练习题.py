# ===== 第985课：字符串处理实战-综合案例-数据清洗 =====
# 知识点：
#   - strip + replace + split 组合使用清理脏数据
#   - 条件判断过滤无效数据
#   - 字符串拼接生成规范格式的输出
#   - 实际场景：从用户提交的表单中提取有效信息

# 模拟用户提交的原始数据（各种不规范）
raw_data = [
    {"name": "  张三  ", "phone": "13812345678", "email": "ZS@Email.COM"},
    {"name": "李四", "phone": "138-1234-5678", "email": "ls@test.com  "},
    {"name": "", "phone": "abc", "email": "not-an-email"},
    {"name": "王五", "phone": "139 8765 4321", "email": "WW@Test.COM  "},
]

print("== 原始数据 ==")
for i, item in enumerate(raw_data):
    print(f"  记录{i + 1}: name={item['name']!r}, phone={item['phone']!r}, "
          f"email={item['email']!r}")

# 清洗流程
print("\n== 清洗结果 ==")
clean_records = []
for i, item in enumerate(raw_data):
    # 1) 清理姓名
    name = item["name"].strip()
    if not name:
        print(f"  记录{i + 1}: 姓名为空，跳过")
        continue

    # 2) 清理手机号（去横线和空格）
    phone = item["phone"].replace("-", "").replace(" ", "")
    if not phone.isdigit() or len(phone) != 11:
        print(f"  记录{i + 1}: 手机号 {item['phone']!r} 不合法，跳过")
        continue

    # 3) 清理邮箱（去空格、统一小写）
    email = item["email"].strip().lower()
    if "@" not in email or "." not in email:
        print(f"  记录{i + 1}: 邮箱 {item['email']!r} 不合法，跳过")
        continue

    clean_records.append({"name": name, "phone": phone, "email": email})
    print(f"  记录{i + 1}: ✓ 清洗通过 -> {name} / {phone} / {email}")

print(f"\n清洗结果: {len(raw_data)} 条原始数据 -> {len(clean_records)} 条有效")

# 打印清洗后的表格
print("\n== 有效数据表 ==")
print(f"{'姓名':<8}{'手机号':>14}{'邮箱':>24}")
print("-" * 46)
for record in clean_records:
    print(f"{record['name']:<8}{record['phone']:>14}{record['email']:>24}")

# ===== 练习题 =====
# 1. 把上面清洗流程封装为一个函数 clean_record(raw)，返回清洗后的字典或 None。
# 2. 增加一个规则：姓名不能超过 10 个字符。
# 3. 增加一个规则：手机号必须以 "1" 开头。
# 4. 思考：清洗和验证有什么区别？清洗是修改数据，验证是判断数据。
