# ===== 第308课：GUI编程-第一个窗口 =====
# 知识点：
#   - tkinter：Python 内置 GUI 库，无需安装
#   - 三步走：创建主窗口 → 添加控件 → mainloop() 进入消息循环
#   - geometry("宽x高") 设窗口尺寸；title() 设标题
#   - mainloop 会“阻塞”直到窗口关闭 —— 之后的代码在关窗后才执行
#   - 本课演示模式：1.5 秒后自动关窗；自己练习时删掉 after 那一行

import tkinter as tk

root = tk.Tk()
root.title("我的第一个窗口")
root.geometry("300x160")

label = tk.Label(root, text="你好，GUI！", font=("微软雅黑", 16))
label.pack(expand=True)          # expand=True：居中撑满

root.after(1500, root.destroy)   # 演示用：1.5 秒后自动关闭（练习时删除）
root.mainloop()                  # 消息循环：监听点击/输入等事件

print("窗口已关闭，程序继续执行")   # mainloop 之后的代码

# ===== 练习题 =====
# 1. 删掉 after 那行，手动关闭窗口，观察 mainloop 之后的打印时机。
# 2. 改窗口标题、尺寸和文字内容，加第二个 Label。
# 3. 思考：为什么 GUI 程序需要一个“循环”？它和第280课的定时循环有何不同？
