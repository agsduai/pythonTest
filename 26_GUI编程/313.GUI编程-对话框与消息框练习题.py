# ===== 第313课：GUI编程-对话框与消息框 =====
# 知识点：
#   - messagebox：提示框/警告框/确认框（会阻塞等用户点确定）
#   - filedialog：选文件/选目录/选保存路径
#   - 这些对话框都是“模态”的：弹出期间程序停住等结果
#   - 本课默认演示模式跳过弹窗（会阻塞自动演示）；把 AUTO_DEMO 改成 False
#     再运行，就能真实体验所有弹窗

import tkinter as tk
from tkinter import filedialog, messagebox

AUTO_DEMO = True          # 改成 False 可真实弹窗体验

root = tk.Tk()
root.title("对话框与消息框")
root.geometry("360x150")

info = tk.Label(root, text="", fg="blue", justify="left")
info.pack(expand=True)


def ask_and_report():
    if messagebox.askyesno("确认", "要选择一个文件吗？"):     # 弹确认框
        path = filedialog.askopenfilename(title="选择文件")
        info.config(text=f"你选了：{path or '（取消）'}")
    else:
        info.config(text="你点了“否”")
    messagebox.showinfo("完成", "演示结束！")                 # 弹提示框


tk.Button(root, text="点我体验对话框", command=ask_and_report).pack(pady=20)

if AUTO_DEMO:
    # 演示模式：不真弹窗（弹窗会阻塞自动化），只打印“会发生什么”
    info.config(text="演示模式：跳过弹窗。\n真实体验请把 AUTO_DEMO 改成 False")
    print("演示模式：askyesno → askopenfilename → showinfo 的流程已跳过")
    root.after(1200, root.destroy)
else:
    root.after(300, ask_and_report)
    root.after(60000, root.destroy)      # 手动体验时限 60 秒自动退出

root.mainloop()

# ===== 练习题 =====
# 1. 把 AUTO_DEMO 改成 False，逐个体验 askyesno/showinfo/showwarning/showerror。
# 2. 用 asksaveasfilename 实现“另存为”。
# 3. 思考：模态对话框阻塞期间，主窗口为什么点不动？（对比第278课轮询思路）
