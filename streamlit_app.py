import streamlit as st

st.set_page_config(page_title="Form Auditor", page_icon="📝")

st.title("📝 Form-Friendliness Auditor (beta)")

img = st.file_uploader("Drop a form screenshot →", type=["png", "jpg", "jpeg"])

if img:
    st.image(img, caption="Your form")
    st.success("Great! AI analysis will appear here once we add the API call.")
