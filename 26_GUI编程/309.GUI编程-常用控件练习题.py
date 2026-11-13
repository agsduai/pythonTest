# ===== 第309课：GUI编程-常用控件 =====
# 知识点：
#   - Label 文字 / Button 按钮 / Entry 单行输入框
#   - Button 的 command= 回调：点击时自动调用（不需要括号！）
#   - entry.get() 读输入；label.config(text=...) 更新显示
#   - 演示模式：自动填入并点击一次，1.5 秒后关窗

import tkinter as tk

root = tk.Tk()
root.title("常用控件")
root.geometry("320x200")

tk.Label(root, text="请输入名字：").pack(pady=(10, 0))
entry = tk.Entry(root, width=22)
entry.pack()

result = tk.Label(root, text="（还没有打招呼）", fg="blue")
result.pack(pady=6)


def on_click():
    name = entry.get().strip() or "世界"
    result.config(text=f"你好，{name}！")


tk.Button(root, text="打招呼", command=on_click, width=10).pack()
# 注意：command=on_click 传的是函数本身；写成 on_click() 就变成“立刻执行”

# 演示：0.5 秒后模拟输入并点击
def auto_demo():
    entry.insert(0, "小明")
    on_click()
    print("演示结果：", result.cget("text"))    # 在窗口销毁前取值


root.after(500, auto_demo)
root.after(1500, root.destroy)
root.mainloop()

# ===== 练习题 =====
# 1. 加一个“清空”按钮：点击后 entry.delete(0, tk.END) 并重置提示。
# 2. 给 Entry 加 show="*" 变成密码框，再体验取值。
# 3. 思考：command=on_click 与 command=on_click() 的区别是什么？
