# ---------- IMPORTS ----------
import streamlit as st, os, base64, json, time           #  add 'time' for animations
from groq import Groq

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Humans design bad forms. Let AI help", page_icon="📝", layout="wide")

# ---------- TOP-LEVEL PLACEHOLDERS ----------
col1, col2 = st.columns([1, 1])          # 50-50 split; tweak to taste

with col1:
    st.subheader("Drop a screenshot of your form →")
    uploader = st.file_uploader("", type=["png", "jpg", "jpeg"])

# Reserve empty containers so we can update later
img_slot       = col1.empty()
score_header   = col2.empty()
score_slots    = [col2.empty() for _ in range(5)]
fix_header     = col2.empty()
fix_slot       = col2.empty()
praise_slot    = col2.empty()

# ---------- DUMMY RIGHT PANE BEFORE UPLOAD ----------
if uploader is None:
    score_header.subheader("📊 Scores of your form")
    for s in score_slots:
        s.progress(0)
    fix_header.subheader("🛠️ Top fixes")
    fix_slot.write("• _none yet_")
    praise_slot.info("Upload a screenshot to see if your form deserved praise.")

# ---------- MAIN FLOW AFTER UPLOAD ----------
if uploader:
    # 1. show the image immediately
    img_slot.image(uploader, caption="Your form")


    # 1. base64-encode for the API
    import base64, io, json
    b64 = base64.b64encode(uploader.getvalue()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

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
              "Score 0-5, comments <=20 words, no keys beyond the schema."
          )},
        { "type": "image_url", "image_url": { "url": data_url } }
    ]

    
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    with st.spinner("Asking Llama-4 Vision…"):
            rsp = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[{"role": "user", "content": user_content}],
    temperature=0.3,
    max_completion_tokens=512,          # ← NEW
    response_format={"type": "json_object"},   # ← comment out if 500 persists
    )
        
    data = json.loads(rsp.choices[0].message.content)

    # 3. animate the scores
    score_header.subheader("📊 Heuristic scores")
    for i, h in enumerate(data["heuristics"]):
        target = h["score"]
        # simple numeric ramp 0→target
        for val in range(target + 1):
            score_slots[i].progress(val / 5, text=f"{h['name']} {val}/5 — {h['comment'] if val==target else ''}")
            time.sleep(0.05)

    # 4. fixes & praise
    fix_header.subheader("🛠️ Top fixes")
    fixes_md = "\n".join("• " + f for f in data["top_fixes"])
    fix_slot.write(fixes_md)
    praise_slot.success(data["praise_line"])
