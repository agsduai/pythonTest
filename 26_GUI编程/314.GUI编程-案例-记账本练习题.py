# ===== 第314课：GUI编程-案例-记账本 =====
# 知识点：
#   - 综合运用：Entry 输入 + Listbox 展示 + Button 操作 + JSON 持久化（第232课）
#   - Listbox：insert(k END, 行) / delete(0, tk.END) 清空 / curselection 选中项
#   - 业务与界面分离：add_record/save/load 不依赖控件细节
#   - 演示模式：自动记两笔、保存、展示，然后关闭

import json
import os
import tkinter as tk

DATA_FILE = "account_book_314.json"
records = []            # 业务数据：[{"desc":..., "amount":...}, ...]

root = tk.Tk()
root.title("迷你记账本")
root.geometry("380x260")

form = tk.Frame(root)
form.pack(pady=6)
tk.Label(form, text="事项：").grid(row=0, column=0)
desc_var = tk.StringVar()
tk.Entry(form, textvariable=desc_var, width=16).grid(row=0, column=1)
tk.Label(form, text="金额：").grid(row=0, column=2)
amount_var = tk.StringVar()
tk.Entry(form, textvariable=amount_var, width=8).grid(row=0, column=3)

listbox = tk.Listbox(root, height=7)
listbox.pack(fill="both", expand=True, padx=10)


def refresh_list():
    listbox.delete(0, tk.END)
    total = 0
    for r in records:
        listbox.insert(tk.END, f"{r['desc']}：{r['amount']} 元")
        total += r["amount"]
    listbox.insert(tk.END, f"—— 合计：{total} 元 ——")


def add_record(desc=None, amount=None):
    desc = desc if desc is not None else desc_var.get().strip()
    amount = amount if amount is not None else amount_var.get().strip()
    if not desc or not amount:
        return False
    records.append({"desc": desc, "amount": float(amount)})
    desc_var.set("")
    amount_var.set("")
    refresh_list()
    return True


def save_records():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


btns = tk.Frame(root)
btns.pack(pady=6)
tk.Button(btns, text="记一笔", command=add_record).pack(side="left", padx=4)
tk.Button(btns, text="保存", command=save_records).pack(side="left", padx=4)


# 演示：自动记两笔并保存
def auto_demo():
    add_record("早饭", 12)
    add_record("地铁", 4)
    save_records()
    print("已保存：", open(DATA_FILE, encoding="utf-8").read())


root.after(400, auto_demo)
root.after(1400, root.destroy)
root.mainloop()

os.remove(DATA_FILE)

# ===== 练习题 =====
# 1. 加“删除选中一笔”按钮：listbox.curselection() 取下标，records.pop。
# 2. 程序启动时若 DATA_FILE 存在则自动 load 恢复。
# 3. 思考：records 是全局列表，按第257课思路怎么封装成 BookKeeper 类？
