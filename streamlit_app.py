import streamlit as st, os, base64, json
from groq import Groq                   # make sure groq is in requirements.txt


st.set_page_config(page_title="Form UX Evaluator", page_icon="📝")

st.title("📝 Find out how good your form is (alpha)")

img = st.file_uploader("Drop a screenshot of your form →", type=["png", "jpg", "jpeg"])

# if img:
#    st.image(img, caption="Your form")
#    st.success("Great! AI analysis will appear here once we add the API call.")


# ------------------------------------------
# 🖼️  Vision path with Llama-4 Scout
# ------------------------------------------
if img:
    # read the uploaded file into bytes
    image_bytes = img.getvalue()

    # 1. base64-encode for the API
    import base64, io, json
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64_img}"

    # 2. craft the prompt
    user_content = [
        { "type": "text",
          "text": (
              "You are a senior UX researcher.\n"
              "Evaluate the web form shown in this screenshot.\n"
              "Return STRICT JSON with:\n"
              "{\n"
              '  "heuristics":[\n'
              '    {"name":"Clarity","score":0,"comment":""},\n'
              '    {"name":"Grouping","score":0,"comment":""},\n'
              '    {"name":"ErrorHandling","score":0,"comment":""},\n'
              '    {"name":"Efficiency","score":0,"comment":""},\n'
              '    {"name":"Accessibility","score":0,"comment":""}\n'
              '  ],\n'
              '  "top_fixes":["","",""],\n'
              '  "praise_line":""\n'
              "}\n"
              "Score 0-5, comments ≤20 words, no keys beyond the schema."
          )},
        { "type": "image_url", "image_url": { "url": data_url } }
    ]

    # 3. call Groq
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    with st.spinner("Asking Llama-4 Scout…"):
        rsp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{ "role": "user", "content": user_content }],
            temperature=0.3,
            response_format={ "type": "json_object" }   # 💡 forces valid JSON
        )
    data = json.loads(rsp.choices[0].message.content)

    # 4. display
    st.image(img, caption="Your form")
    st.header("📊 Heuristic scores")
    for h in data["heuristics"]:
        st.write(f"**{h['name']}**: {h['score']}  — {h['comment']}")
        st.progress(h["score"] / 5)
    st.header("🛠️ Top fixes")
    for fix in data["top_fixes"]:
        st.write("• " + fix)
    st.success(data["praise_line"])
