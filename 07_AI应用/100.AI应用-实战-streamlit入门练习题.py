# ===== 第100课：AI应用-实战-streamlit入门 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - Streamlit 可以把 Python 脚本快速变成网页应用，无需手写 HTML/CSS
#   - 安装：pip install streamlit
#   - 启动：streamlit run 文件名.py，浏览器默认访问 http://localhost:8501
#   - Streamlit 的执行模型：每次交互都会从头到尾重新运行整个脚本
#   - 常用入门函数：st.title、st.write、st.text_input、st.button、st.success
#   - 普通 print 输出在终端，网页内容要用 st.write 等 Streamlit 函数
# 依赖：pip install streamlit

import streamlit as st

# 页面从上到下执行，标题会显示在网页顶部
st.title("我的第一个 AI 应用")
st.write("这是用 Python + Streamlit 搭建的网页，不需要写前端代码。")
st.divider()  # 显示一条分隔线

name = st.text_input("请输入你的名字：", placeholder="例如：小明")

# 按钮被点击时，本次脚本运行的返回值为 True
if st.button("打招呼"):
    if name.strip():
        st.success(f"你好，{name}！欢迎学习 Python + AI 应用开发。")
        st.write("下一步：把大模型 API 接入这个页面，就能变成真正的 AI 助手。")
    else:
        st.warning("名字不能为空，请先输入内容。")

st.caption("提示：在终端按 Ctrl+C 可以停止 Streamlit 服务。")

# ===== 练习题 =====
# 1. 安装 Streamlit，并用 streamlit run 启动本文件，观察浏览器中的页面。
# 2. 修改标题和提示文字，增加一个 st.write 输出你最喜欢的 AI 应用。
# 3. 自测：点击按钮后，为什么页面上的变量会重新计算？普通 print 会显示在哪里？
