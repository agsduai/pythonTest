# ===== 第101课：AI应用-实战-streamlit基础用法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 文本展示：st.title / st.header / st.write / st.markdown / st.code
#   - 数据展示：st.dataframe 表格、st.metric 指标卡、st.json 展示 JSON
#   - 输入组件：st.text_input、st.text_area、st.number_input、
#               st.slider、st.selectbox、st.checkbox、st.button
#   - st.write 会自动识别字符串、数字、列表、字典等常见类型
#   - st.session_state 用于跨多次运行保存状态（如计数器）
#   - 组件有返回值：文本框返回字符串，滑块返回数字，按钮返回 True/False
# 依赖：pip install streamlit

import streamlit as st

st.title("Streamlit 基础用法")
st.header("1. 文本展示")
st.write("st.write 可以输出文本、数字、列表等：", [1, 2, 3])
st.markdown("这是 **Markdown** 文本，支持 *斜体* 和 `行内代码`。")
st.code("print('Hello, Streamlit!')", language="python")

st.header("2. 数据展示")
st.dataframe(
    [
        {"课程": "088", "主题": "AI应用概述"},
        {"课程": "101", "主题": "Streamlit 基础用法"},
    ],
    use_container_width=True,
)
st.metric(label="今日 API 调用次数", value=128, delta=12)
st.json({"model": "deepseek-chat", "stream": False})

st.header("3. 输入组件")
name = st.text_input("你的名字：")
age = st.number_input("你的年龄：", min_value=0, max_value=120, value=18)
level = st.selectbox("你的 Python 水平：", ["零基础", "入门", "进阶"])
score = st.slider("给本课打分（1-5）：", min_value=1, max_value=5, value=5)
agree = st.checkbox("我已阅读课程说明")

if st.button("提交信息"):
    if agree and name.strip():
        st.success(f"{name}，{age} 岁，水平：{level}，评分：{score}")
    else:
        st.warning("请填写名字并勾选“已阅读课程说明”。")

st.header("4. 会话状态 session_state")
if "count" not in st.session_state:
    st.session_state.count = 0  # 第一次运行时初始化
if st.button("点击 +1"):
    st.session_state.count += 1  # 脚本重跑后状态仍然保留
st.metric("累计点击次数", st.session_state.count)

# ===== 练习题 =====
# 1. 增加一个 st.text_area 输入框，并实时显示输入内容的字符数。
# 2. 修改计数器，使其支持“+1”和“清零”两个按钮，并保持状态。
# 3. 自测：st.write 和 st.text 的区别是什么？组件返回值分别是什么类型？
