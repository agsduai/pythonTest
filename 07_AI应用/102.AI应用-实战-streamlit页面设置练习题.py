# ===== 第102课：AI应用-实战-streamlit页面设置 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - st.set_page_config 用于设置页面标题、图标、布局和侧边栏初始状态
#   - 必须放在所有 Streamlit 命令之前，且一个脚本只能调用一次
#   - page_title 设置浏览器标签页标题，page_icon 支持 emoji 或图片
#   - layout="centered" 为居中窄布局，layout="wide" 为宽屏布局
#   - initial_sidebar_state 控制侧边栏：auto / expanded / collapsed
#   - st.sidebar 创建侧边栏；st.columns 分栏；st.tabs 选项卡；st.expander 折叠面板
#   - 聊天类应用通常使用 wide 布局，把设置项放在侧边栏
# 依赖：pip install streamlit

import streamlit as st

# 页面配置必须最先调用，负责浏览器标题、图标与整体布局
st.set_page_config(
    page_title="AI 学习助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AI 学习助手")
st.caption("演示 Streamlit 页面设置与常用布局组件")

with st.sidebar:
    st.header("导航")
    page = st.radio("选择页面：", ["对话", "设置"])
    st.divider()
    st.write("侧边栏适合放导航、参数和会话列表。")

left, right = st.columns([2, 1])  # 2:1 的宽度比例
with left:
    st.subheader(f"当前页面：{page}")
    if page == "对话":
        st.info("这里将来放置聊天输入框和消息列表。")
    else:
        st.info("这里将来放置模型选择和参数设置。")
with right:
    st.metric("已保存会话", "3")
    st.metric("今日消息数", "26")

tab1, tab2 = st.tabs(["功能介绍", "使用说明"])
with tab1:
    st.write("本应用将支持多轮对话、会话保存和流式输出。")
with tab2:
    with st.expander("如何开始？"):
        st.write("在左侧选择“对话”，然后输入你的问题。")
    with st.expander("常见问题"):
        st.write("如果页面空白，请检查终端中的 Streamlit 启动日志。")

# ===== 练习题 =====
# 1. 把 layout 改为 "centered"，重启应用，比较页面宽度的变化。
# 2. 在侧边栏增加一个 selectbox 选择模型，并在主区域显示当前选择。
# 3. 自测：为什么 st.set_page_config 必须放在文件最前面？重复调用会怎样？
