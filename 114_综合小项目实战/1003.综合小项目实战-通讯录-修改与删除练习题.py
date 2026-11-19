# ===== 第1003课：综合小项目实战-通讯录——修改与删除 =====
# 知识点：
#   - 修改：先检查存在，再更新字段
#   - 删除：先确认存在，再从字典中移除并保存
#   - 部分更新：只修改传入的字段，其他字段保持不变
#   - 数据安全：修改前先备份旧数据
# 依赖：无（标准库）
import json
import os

CONTACT_FILE = "contacts.json"


def load_contacts():
    if not os.path.exists(CONTACT_FILE):
        return {}
    with open(CONTACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts):
    with open(CONTACT_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def update_contact(contacts, name, **fields):
    """部分更新：只更新传入的字段。返回 (是否成功, 消息)。"""
    if name not in contacts:
        return False, f"{name} 不存在"
    old_data = dict(contacts[name])         # 备份旧数据
    for field, value in fields.items():
        if field == "phone" and (not value.isdigit() or len(value) != 11):
            return False, "电话格式不正确"
        contacts[name][field] = value
    save_contacts(contacts)
    return True, f"已更新 {name}: {old_data} -> {contacts[name]}"


def delete_contact(contacts, name):
    """删除联系人。返回 (是否成功, 消息)。"""
    if name not in contacts:
        return False, f"{name} 不存在"
    removed = contacts.pop(name)
    save_contacts(contacts)
    return True, f"已删除 {name}（电话 {removed.get('phone', '未知')}）"


# 使用示例
contacts = load_contacts()
if "张三" not in contacts:
    contacts["张三"] = {"phone": "13812345678"}
    save_contacts(contacts)

print("== 通讯录（修改与删除）==")
print(f"  当前联系人: {sorted(contacts)}")

# 修改电话
ok, msg = update_contact(contacts, "张三", phone="13999999999")
print(f"\n  修改张三的电话: {msg}")

# 修改不存在的联系人
ok, msg = update_contact(contacts, "不存在的人", phone="123")
print(f"  修改不存在的人: {msg}")

# 删除联系人
ok, msg = delete_contact(contacts, "张三")
print(f"\n  删除张三: {msg}")
print(f"  删除后联系人: {sorted(contacts)}")

# 删除不存在的
ok, msg = delete_contact(contacts, "张三")
print(f"  再次删除张三: {msg}")

# ===== 练习题 =====
# 1. 实现「恢复已删除」：删除前备份到 deleted_contacts 字典，支持恢复。
# 2. 实现「搜索」：按姓名模糊搜索（姓名包含关键词即匹配）。
# 3. 增加删除确认：删除前检查是否是最后一个联系人，是则警告。
# 4. 思考：为什么 update_contact 要先备份旧数据？
