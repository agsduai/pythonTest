# ===== 第104课：AI应用-实战-界面基本布局 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - streamlit 页面的基本结构：标题、说明文字、主区域
#   - st.columns 列布局与 st.container 容器
#   - st.chat_message 消息气泡、st.chat_input 底部输入框
#   - use_container_width 让组件占满容器宽度
# 依赖：pip install streamlit

import streamlit as st

# 页面基础设置：标题、图标、宽屏布局
st.set_page_config(page_title="AI 智能助手", page_icon="🤖", layout="wide")

st.title("AI 智能助手")
st.caption("第 104 课：界面基本布局")

# 用两列划分主区域：左侧对话区，右侧说明区
left, right = st.columns([3, 1])

with left:
    st.subheader("对话区")
    # 容器用于集中放置对话内容，后续可把消息渲染进来
    chat_area = st.container()
    with chat_area:
        with st.chat_message("assistant"):
            st.markdown("你好，我是 AI 助手，有什么可以帮你？")

with right:
    st.subheader("功能说明")
    st.info("这里是右侧信息区")
    st.markdown("- 支持多轮对话\n- 支持流式输出")
    st.button("示例按钮", use_container_width=True)

# 聊天输入框放在主区域，会自动固定在页面底部
prompt = st.chat_input("请输入你的问题")

if prompt:
    # 用户输入后先回显一条用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

# ===== 练习题 =====
# 1. 把左右两列宽度比例改为 [2, 1]，观察对话区和说明区的变化。
# 2. 在右侧信息区用 st.tabs 增加“使用说明”和“关于”两个标签页。
# 3. 用 st.expander 包裹一段“常见问题”，默认折叠显示。
