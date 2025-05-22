import streamlit as st

st.set_page_config(page_title="Form UX Evaluator", page_icon="📝")

st.title("📝 Find out how good your form is (alpha)")

img = st.file_uploader("Drop a screenshot of your form →", type=["png", "jpg", "jpeg"])

if img:
    st.image(img, caption="Your form")
    st.success("Great! AI analysis will appear here once we add the API call.")
