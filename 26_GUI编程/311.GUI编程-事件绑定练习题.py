# ===== 第311课：GUI编程-事件绑定 =====
# 知识点：
#   - bind(事件串, 处理函数)：把控件和“用户动作”连起来
#   - 常用事件：<Return> 回车 / <Button-1> 左键 / <Double-Button-1> 双击
#   - 处理函数必须接收一个 event 参数（坐标、按键名都在里面）
#   - command= 适合“点击按钮”；bind 适合“任意控件上的任意事件”

import tkinter as tk

root = tk.Tk()
root.title("事件绑定")
root.geometry("360x180")

entry = tk.Entry(root, width=24)
entry.pack(pady=8)
log = tk.Label(root, text="事件日志：", justify="left")
log.pack()


def show(text):
    log.config(text=log.cget("text") + f"\n{text}")


def on_return(event):
    show(f"回车：输入了「{entry.get()}」")


def on_double(event):
    show(f"双击：位置 ({event.x}, {event.y})")


entry.bind("<Return>", on_return)          # 输入框里按回车
log.bind("<Double-Button-1>", on_double)   # 双击日志区

# 演示：程序化触发一次回车事件（等效于用户按键）
root.after(500, lambda: on_return(type("E", (), {"x": 0, "y": 0})()))
root.after(1500, root.destroy)
root.mainloop()

# ===== 练习题 =====
# 1. 给 Entry 绑定 <Key>：每敲一个键就打印 e.keysym（按键名）。
# 2. 绑定 <Button-3>（右键），在点击位置弹一个 Label。
# 3. 思考：event 对象里还有什么信息？（x/y/keysym/char/widget...）
