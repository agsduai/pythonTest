# ===== 第310课：GUI编程-布局管理 =====
# 知识点：
#   - pack：按顺序堆叠（上/下/左/右），简单场景够用
#   - grid：表格行列布局，表单类界面首选
#   - place：绝对坐标定位（窗口缩放易错位，少用）
#   - 同一个容器里 pack 与 grid 不能混用！
#   - 演示模式：自动关闭

import tkinter as tk

root = tk.Tk()
root.title("grid 表单布局")
root.geometry("340x170")

# 表单放进 Frame：Frame 内部用 grid，Frame 本身用 pack 放进窗口
# 注意：pack 与 grid 不能在“同一个容器”里混用，不同容器则完全可以
form = tk.Frame(root)
form.pack(pady=8)

tk.Label(form, text="用户名：").grid(row=0, column=0, padx=10, pady=8, sticky="e")
tk.Entry(form).grid(row=0, column=1, pady=8)

tk.Label(form, text="密码：").grid(row=1, column=0, padx=10, sticky="e")
tk.Entry(form, show="*").grid(row=1, column=1, pady=8)

tk.Button(form, text="登录").grid(row=2, column=0, columnspan=2, pady=10)
# columnspan=2：横跨两列，按钮居中

status = tk.Label(root, text="底部状态栏（pack 放在窗口边缘）", bg="#eee")
status.pack(side="bottom", fill="x")

root.after(1500, root.destroy)
root.mainloop()

# ===== 练习题 =====
# 1. 给登录表单加“记住我”复选框（Checkbutton），用 grid 放在按钮上方。
# 2. 用 place 把一个“调试中”小红字放到 (200, 100)，缩放窗口观察问题。
# 3. 思考：sticky="e" 是让控件贴哪个方向？
