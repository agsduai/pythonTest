# ===== 第1004课：综合小项目实战-通讯录——完整菜单程序 =====
# 知识点：
#   - while True + input() 实现菜单循环
#   - 多个功能函数 + 分发调用 = 典型的交互程序架构
#   - 输入 "q" 退出循环
#   - 异常处理防止用户输入非法选项导致崩溃
# 依赖：无（标准库）
import json
import os

CONTACT_FILE = "contacts_menu.json"


def load_contacts():
    if not os.path.exists(CONTACT_FILE):
        return {}
    with open(CONTACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_contacts(contacts):
    with open(CONTACT_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def do_add(contacts):
    name = input("  姓名: ").strip()
    phone = input("  电话: ").strip()
    if not name:
        print("  ✗ 姓名不能为空")
        return
    if name in contacts:
        print(f"  ✗ {name} 已存在")
        return
    contacts[name] = {"phone": phone}
    save_contacts(contacts)
    print(f"  ✓ 已添加 {name}")


def do_list(contacts):
    if not contacts:
        print("  通讯录为空")
        return
    print(f"  共 {len(contacts)} 位联系人:")
    for name in sorted(contacts):
        print(f"    {name}: {contacts[name].get('phone', '无电话')}")


def do_find(contacts):
    name = input("  输入要查找的姓名: ").strip()
    if name in contacts:
        print(f"  找到 {name}: {contacts[name].get('phone', '')}")
    else:
        print(f"  未找到 {name}")


def do_delete(contacts):
    name = input("  输入要删除的姓名: ").strip()
    if name not in contacts:
        print(f"  ✗ {name} 不存在")
        return
    del contacts[name]
    save_contacts(contacts)
    print(f"  ✓ 已删除 {name}")


MENU = """
======== 通讯录管理 ========
  1. 添加联系人
  2. 列出全部
  3. 查找联系人
  4. 删除联系人
  q. 退出
============================"""


def run_menu():
    contacts = load_contacts()
    print("通讯录已加载")
    while True:
        print(MENU)
        choice = input("请选择: ").strip()
        if choice == "q":
            print("再见！")
            break
        elif choice == "1":
            do_add(contacts)
        elif choice == "2":
            do_list(contacts)
        elif choice == "3":
            do_find(contacts)
        elif choice == "4":
            do_delete(contacts)
        else:
            print("  无效选项，请重新选择")


print("== 通讯录菜单程序 ==")
print("（菜单程序需要终端交互运行，此处演示代码结构）")
print(f"当前通讯录文件: {CONTACT_FILE} -> "
      f"{'存在' if os.path.exists(CONTACT_FILE) else '不存在'}")
print(f"菜单选项: 1=添加, 2=列出, 3=查找, 4=删除, q=退出")
print("完整运行请在终端中执行本文件")

# 演示：直接调用功能函数（不通过菜单）
contacts = load_contacts()
contacts["演示用户"] = {"phone": "13800000000"}
save_contacts(contacts)
print(f"\n  代码方式添加演示用户 -> {sorted(contacts)}")
os.remove(CONTACT_FILE)                 # 清理
print("  清理完成")

# ===== 练习题 =====
# 1. 运行本文件的 run_menu() 函数，实际体验菜单交互。
# 2. 增加选项「5. 修改联系人电话」。
# 3. 增加「统计」功能：显示联系人数、最多电话的人。
# 4. 思考：为什么用函数封装每个功能，而不是把代码全写在 while 循环里？
