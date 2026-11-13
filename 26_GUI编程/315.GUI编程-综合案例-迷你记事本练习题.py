# ===== 第315课：GUI编程-综合案例-迷你记事本 =====
# 知识点：
#   - 综合运用：Menu 菜单 + Text 多行文本 + filedialog 保存（第313课）
#   - Text：insert(索引, 文本) / get("1.0", tk.END)（“1.0”=第1行第0列）
#   - 菜单：Menu(root) 作主菜单，add_cascade 挂子菜单，add_command 加项
#   - 业务函数带 path 参数：传路径直接读写，不传则弹对话框 —— 好测试！

import os
import tkinter as tk
from tkinter import filedialog, messagebox

AUTO_DEMO = True          # 改成 False 体验真实“另存为”对话框
DEMO_FILE = "note_315.txt"

root = tk.Tk()
root.title("迷你记事本")
root.geometry("420x260")

text = tk.Text(root, font=("微软雅黑", 12))
text.pack(fill="both", expand=True)

status = tk.Label(root, text="就绪", anchor="w", bg="#eee")
status.pack(side="bottom", fill="x")


def do_open(path=None):
    if path is None:
        path = filedialog.askopenfilename(filetypes=[("文本", "*.txt")])
    if path:
        with open(path, encoding="utf-8") as f:
            text.delete("1.0", tk.END)
            text.insert("1.0", f.read())
        status.config(text=f"已打开：{path}")


def do_save(path=None):
    if path is None:
        path = filedialog.asksaveasfilename(defaultextension=".txt")
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.get("1.0", tk.END).rstrip("\n"))
        status.config(text=f"已保存：{path}")


# ---- 菜单栏 ----
menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)      # tearoff=0 去掉虚线
file_menu.add_command(label="打开", command=do_open)
file_menu.add_command(label="保存", command=do_save)
file_menu.add_separator()
file_menu.add_command(label="退出", command=root.destroy)
menubar.add_cascade(label="文件", menu=file_menu)
root.config(menu=menubar)


def auto_demo():
    text.insert("1.0", "这是自动演示写入的内容。\n第二行：迷你记事本 OK。")
    do_save(DEMO_FILE)                       # 传路径 → 不弹对话框
    print("保存内容：", open(DEMO_FILE, encoding="utf-8").read())
    text.delete("1.0", tk.END)
    do_open(DEMO_FILE)                       # 再读回来验证


if AUTO_DEMO:
    root.after(400, auto_demo)
    root.after(1400, root.destroy)
else:
    root.after(60000, root.destroy)          # 手动体验限时 60 秒

root.mainloop()

if os.path.exists(DEMO_FILE):
    os.remove(DEMO_FILE)

# ===== 练习题 =====
# 1. 给菜单加“编辑”项：全选（text.tag_add("sel", "1.0", "end")）与清空。
# 2. 统计字数：Text 绑定 <Key>，每次按键更新状态栏“共 N 字”。
# 3. 思考：把记事本换成语义化版本（v1.0）发布，还差哪些功能？（提示：撤销/重做）
