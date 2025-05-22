# ---------- IMPORTS ----------
import os, base64, json, time
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

@st.cache_resource
def get_client() -> Groq:
    """Return a singleton Groq client for all calls."""
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Humans design bad forms. Let AI help",
    page_icon="📝",
    layout="wide",
)

# ---------- LIGHT & DARK STYLES ----------
st.markdown(
    """
    <style>
      /* column backgrounds */
      div[data-testid="column"]:nth-of-type(1)  > div:first-child {background:#f4f4f4;padding:24px;border-radius:8px;}
      div[data-testid="column"]:nth-of-type(2)  > div:first-child {background:#ffffff;padding:24px;border-radius:8px;}

      /* blue progress bars */
      .stProgress > div > div > div > div {background:#2f9cf4 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HEADER ----------
st.markdown(
    """
    <div style='width:100%;background:#111;padding:6px 12px'>
      <span style='font-size:15px;color:#bbb'>
        📝 Humans design bad forms. Let AI help (alpha)
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- LAYOUT ----------
left, right = st.columns([2, 1], gap="small")

with left:
    st.subheader("Let AI grade your form ↓")
    uploader  = st.file_uploader("", type=["png", "jpg", "jpeg"])
    img_slot  = st.empty()

with right:
    summary_slot = st.empty()
    score_header = st.empty()
    score_slots  = [st.empty() for _ in range(5)]
    fix_header   = st.empty()
    fix_slot     = st.empty()

# ---------- BEFORE UPLOAD ----------
if uploader is None:
    summary_slot.info("Waiting for you to upload an image…")
    score_header.subheader("🌡️ Form health check")
    for bar in score_slots:
        bar.progress(0)
    fix_header.subheader("🚧 What you should go fix")
    fix_slot.write("")

# ---------- AFTER UPLOAD ----------
if uploader:
    # 1 ▸ preview image
    img_slot.image(uploader, caption="Your form")

    # 2 ▸ encode + prompt
    b64 = base64.b64encode(uploader.getvalue()).decode()
    data_url = f"data:image/jpeg;base64,{b64}"
    user_content = [
        {
            "type": "text",
            "text": (
                "You are a senior UX researcher.\n"
                "Evaluate the web form shown in this screenshot.\n"
                "Return STRICT JSON with:\n"
                '{ "heuristics":[\n'
                '  {"name":"Goal Clarity","score":0,"comment":""},\n'
                '  {"name":"Cognitive Load","score":0,"comment":""},\n'
                '  {"name":"Data Minimalism","score":0,"comment":""},\n'
                '  {"name":"Accessibility","score":0,"comment":""},\n'
                '  {"name":"Trust Cues","score":0,"comment":""}\n'
                '],\n'
                '  "top_fixes":["","",""],\n'
                '  "praise_line":"" }\n'
                "Score 0-5, comments ≤ 50 words."
            ),
        },
        {"type": "image_url", "image_url": {"url": data_url}},
    ]

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    with st.spinner("Asking Llama-4 Vision…"):
        rsp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": user_content}],
            temperature=0.3,
            max_completion_tokens=512,
            response_format={"type": "json_object"},
        )

    data = json.loads(rsp.choices[0].message.content)

        # ---------- DYNAMIC 5-BULLET SUMMARY ----------
    
    def dynamic_summary(data_json: dict) -> str:
        rsp = c.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role":"user","content":prompt}],
            temperature=0.9,
            max_tokens=180,
        )
        prompt = f"""
    You are a senior UX copywriter.
    Write 4-5 short, actionable bullets about this form audit JSON.
    • Mix praise and constructive advice. 
    • Vary word choice every time; avoid templates.
    • Each bullet ≤ 18 words, start with a fitting emoji.
    JSON:
    {json.dumps(data_json, indent=2)}
    """
        c = get_client()                     # cached Groq client we set earlier
        rsp = c.chat.completions.create(
            model="llama3-8b-8192",          # fast & inexpensive
            messages=[{"role":"user","content":prompt}],
            temperature=0.9,                 # more creativity
            max_tokens=180,
        )
        return rsp.choices[0].message.content.strip()
    
    # produce the bullets
    bullets_md = dynamic_summary(data)
    
    # pretty card
    summary_slot.markdown(
        f"""
        <div style="background:#23395d22;padding:18px 22px;
                    border-left:6px solid #2f9cf4;border-radius:6px;margin-bottom:14px;">
            {bullets_md}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 ▸ animated bars
    score_header.subheader("🌡️ Form health check")
    for i, h in enumerate(data["heuristics"]):
        for v in range(h["score"] + 1):
            score_slots[i].progress(
                v / 5,
                text=f"{h['name']} {v}/5 — {h['comment'] if v == h['score'] else ''}",
            )
            time.sleep(0.04)

    # 5 ▸ fixes
    fix_header.subheader("🚧 What you should go fix")
    fix_slot.write(" • ".join(data["top_fixes"]))

    # 6 ▸ JSON copy button & details
    import json as _json
    import streamlit.components.v1 as components

    json_str = _json.dumps(data, indent=2)

    # RE-ENTER the right column so content stays there
      # Copy-to-clipboard button (fills full column width)
    with right:
        # … Top fixes already rendered …
    
        # Copy-to-clipboard button (fills full column width)
        st.markdown(
            f"""
            <button
                style="display:block;width:100%;
                       margin-top:16px;background:#2f9cf4;color:white;
                       border:none;padding:12px 0;border-radius:6px;
                       font-size:15px;cursor:pointer;"
                onclick='navigator.clipboard.writeText({json.dumps(json_str)})'>
                📋 Copy full&nbsp;JSON
            </button>
            """,
            unsafe_allow_html=True,
        )
    
        # Collapsible viewer + download
        with st.expander("See JSON details"):
            st.code(json_str, language="json")
            st.download_button(
                "Download audit.json",
                data=json_str,
                file_name="audit.json",
                mime="application/json",
            )
