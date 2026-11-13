# ===== 第312课：GUI编程-变量绑定 =====
# 知识点：
#   - StringVar / IntVar / BooleanVar：与控件“双向绑定”的特殊变量
#   - textvariable=：变量变 → 控件变；用户输入 → 变量也变
#   - trace_add("write", 回调)：监听变量变化，实时响应
#   - 好处：业务逻辑只操作变量，不用手动 get/set 控件

import tkinter as tk

root = tk.Tk()
root.title("变量绑定")
root.geometry("360x190")

text_var = tk.StringVar(value="")
changes = []


def on_change(*_):
    changes.append(text_var.get())
    print(f"变量变化 → {text_var.get()!r}")


text_var.trace_add("write", on_change)      # 监听写入

tk.Label(root, text="输入框与下方文字实时同步：").pack(pady=(10, 0))
tk.Entry(root, textvariable=text_var, width=24).pack()
tk.Label(root, textvariable=text_var, fg="blue", font=("微软雅黑", 12)).pack(pady=8)

# IntVar + Spinbox 演示
count_var = tk.IntVar(value=1)
tk.Spinbox(root, from_=1, to=5, textvariable=count_var, width=6).pack()

root.after(300, lambda: text_var.set("自动输入一"))
root.after(600, lambda: text_var.set("自动输入二"))
root.after(900, lambda: count_var.set(3))


def finish():
    print("最终 count_var：", count_var.get())   # 在窗口销毁前取值
    root.destroy()


root.after(1200, finish)
root.mainloop()
print("全程变化记录：", changes)

# ===== 练习题 =====
# 1. 加一个 Checkbutton + BooleanVar，勾选时把文字变红（fg 绑定）。
# 2. 用 trace_add 实现“字数统计”：超过 10 字时提示变红。
# 3. 思考：StringVar 和普通 str 变量相比，多了哪些能力？
