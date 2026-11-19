# ===== 第1002课：综合小项目实战-通讯录——添加与查询 =====
# 知识点：
#   - 字典做通讯录存储：姓名 -> {电话, 邮箱}
#   - 函数封装功能：add_contact / find_contact
#   - 输入验证：姓名不能为空、电话必须是 11 位数字
#   - 数据持久化：用 JSON 文件保存，下次启动不丢失
# 依赖：无（标准库）
import json
import os

CONTACT_FILE = "contacts.json"


def load_contacts():
    """从文件加载通讯录，文件不存在返回空字典。"""
    if not os.path.exists(CONTACT_FILE):
        return {}
    with open(CONTACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts):
    """保存通讯录到文件。"""
    with open(CONTACT_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def add_contact(contacts, name, phone):
    """添加联系人。返回 (是否成功, 消息)。"""
    if not name.strip():
        return False, "姓名不能为空"
    if not phone.isdigit() or len(phone) != 11:
        return False, "电话必须是 11 位数字"
    if name in contacts:
        return False, f"{name} 已存在"
    contacts[name] = {"phone": phone}
    save_contacts(contacts)
    return True, f"已添加 {name}"


def find_contact(contacts, name):
    """按姓名查找联系人。返回联系人信息或 None。"""
    return contacts.get(name)


# 使用示例
contacts = load_contacts()
print("== 通讯录（添加与查询）==")
print(f"  当前联系人数: {len(contacts)}")

ok, msg = add_contact(contacts, "张三", "13812345678")
print(f"  添加张三: {msg}")
ok, msg = add_contact(contacts, "李四", "13987654321")
print(f"  添加李四: {msg}")
ok, msg = add_contact(contacts, "张三", "13811111111")
print(f"  再次添加张三: {msg}（重复）")

found = find_contact(contacts, "张三")
if found:
    print(f"  查找张三: 电话 {found['phone']}")
not_found = find_contact(contacts, "王五")
print(f"  查找王五: {not_found}")

# ===== 练习题 =====
# 1. 给联系人增加邮箱字段，add_contact 增加邮箱参数和验证。
# 2. 实现 list_contacts(contacts)：按姓名排序打印所有联系人。
# 3. 实现 count_contacts(contacts)：返回联系人总数。
# 4. 思考：为什么要用 JSON 文件保存而不是直接存在内存里？
