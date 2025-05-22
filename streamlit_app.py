# ---------- IMPORTS ----------
import streamlit as st, os, base64, json, time
from groq import Groq

# ---------- PAGE CONFIG (must be 1st!) ----------
st.set_page_config(page_title="Humans design bad forms. Let AI help",
                   page_icon="📝", layout="wide")
st.markdown("""
<style>
/* first column (left)  */
div[data-testid="column"]:nth-of-type(1)  > div:first-child {
    background:#f4f4f4 !important;   /* light grey */
    padding:20px; border-radius:8px;
}
/* second column (right) */
div[data-testid="column"]:nth-of-type(2)  > div:first-child {
    background:#ffffff !important;   /* white */
    padding:20px; border-radius:8px;
}
/* colour for progress bars */
.stProgress > div > div > div > div {
    background-color:#2f9cf4 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown(
    """
    <div style='width:100%; background:#111; padding:6px 12px;'>
        <span style='font-size:15px; color:#bbb;'>
            📝 Humans design bad forms. Let AI help (alpha)
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- LAYOUT: 2/3 – 1/3 ----------
left, right = st.columns([2, 1], gap="small")   # 2-third / 1-third

with left:
    st.subheader("Drop a screenshot of your form →")
    uploader = st.file_uploader("", type=["png", "jpg", "jpeg"])
    img_slot = st.empty()

with right:
    summary_slot = st.empty()
    score_header = st.empty()
    score_slots  = [st.empty() for _ in range(5)]
    fix_header   = st.empty()
    fix_slot     = st.empty()
    praise_slot  = st.empty()
  

# ---------- BEFORE UPLOAD ----------
if uploader is None:
    summary_slot.info("Awaiting an image…")
    score_header.subheader("📊 Scores of your form")
    for s in score_slots:
        s.progress(0)
    fix_header.subheader("🛠️ What you should go fix")
    fix_slot.write("—")

# ---------- AFTER UPLOAD ----------
if uploader:
    img_slot.image(uploader, caption="Your form")

    # encode image
    b64 = base64.b64encode(uploader.getvalue()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"

    # prompt
    user_content = [
        {"type":"text","text":(
            "You are a senior UX researcher.\n"
            "Evaluate the web form shown in this screenshot.\n"
            "Return STRICT JSON with:\n"
            '{"heuristics":[{"name":"Clarity","score":0,"comment":""},'
            '{"name":"Grouping","score":0,"comment":""},'
            '{"name":"ErrorHandling","score":0,"comment":""},'
            '{"name":"Efficiency","score":0,"comment":""},'
            '{"name":"Accessibility","score":0,"comment":""}],'
            '"top_fixes":["","",""],"praise_line":""}\n'
            "Score 0-5, comments <=20 words."
        )},
        {"type":"image_url","image_url":{"url":data_url}}
    ]

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    with st.spinner("Asking Llama-4 Vision…"):
        rsp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":user_content}],
            temperature=0.3,
            max_completion_tokens=512,
            response_format={"type":"json_object"}      # remove if it 500-errors
        )

    data = json.loads(rsp.choices[0].message.content)

    # summary / praise at top
    high = max(data["heuristics"], key=lambda h: h["score"])
    low  = min(data["heuristics"], key=lambda h: h["score"])
    summary_slot.markdown(
        f"**{data['praise_line']}**  \n"
        f"Highest area: **{high['name']}** ({high['score']}/5). "
        f"Biggest opportunity: **{low['name']}** ({low['score']}/5)."
    )

    # ---------- Copy-JSON button ----------
    import json as _json

    json_str = _json.dumps(data, indent=2)

    with summary_slot.expander("⬇ Click to copy full JSON", expanded=False):
    st.code(json_str, language="json")            # copy-icon appears top-right
  
    # optional download button (uncomment if you like)
    # st.download_button(
    #     "Download as audit.json",
    #     data=json_str,
    #     file_name="audit.json",
    #     mime="application/json",
    )

    # animate scores
    score_header.subheader("📊 Heuristic scores")
    for i, h in enumerate(data["heuristics"]):
        for val in range(h["score"] + 1):
            score_slots[i].progress(val/5,
                text=f"{h['name']} {val}/5 — {h['comment'] if val==h['score'] else ''}")
            time.sleep(0.05)

    # fixes
    fix_header.subheader("🛠️ Top fixes")
    fix_slot.write("\n".join("• "+f for f in data["top_fixes"]))
