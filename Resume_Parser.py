# -------------------------------------------------
# ✨ Stylish Resume Parser App (Final Popup Version - Enhanced Upload Section)
# -------------------------------------------------
# Run: streamlit run Resume_Parser.py

import os
import json
import html
import re
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.prompts import PromptTemplate


# -------------------------------
# Config / LLM
# -------------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.warning("⚠️ GOOGLE_API_KEY not found in environment. Set it in a .env file or environment variables.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GOOGLE_API_KEY
)

PROMPT_TEMPLATE = """
You are an expert resume parser. Given the resume text, extract the following fields and return a single valid JSON object:

{{
  "Name": "...",
  "Email": "...",
  "Phone": "...",
  "LinkedIn": "...",
  "Skills": [...],
  "Education": [...],
  "Experience": [...],
  "Projects": [...],
  "Certifications": [...]
}}

Rules:
- If a field cannot be found, set its value to "No idea".
- Return ONLY valid JSON (no extra commentary).
- Keep lists as arrays, and keep Experience/Projects as arrays of short strings.

Resume text:
{text}
"""
prompt_template = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["text"])


# -------------------------------
# Helpers
# -------------------------------
def load_resume_docs(uploaded_file):
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            loader = PyPDFLoader(temp_path)
        elif uploaded_file.name.lower().endswith(".docx"):
            loader = Docx2txtLoader(temp_path)
        elif uploaded_file.name.lower().endswith(".txt"):
            loader = TextLoader(temp_path)
        else:
            return None
        docs = loader.load()
        return docs
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


def clean_model_json(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned


def make_list_html(items, item_limit=50):
    if items is None:
        return "<p>No idea</p>"
    if isinstance(items, list):
        if len(items) == 0:
            return "<p>No idea</p>"
        items_to_show = items[:item_limit]
        list_items = "".join(f"<li>{html.escape(str(i))}</li>" for i in items_to_show)
        more_note = ""
        if len(items) > item_limit:
            more_note = f"<p style='font-size:12px; color:#bfc7d6;'>...and {len(items)-item_limit} more</p>"
        return f"<ul>{list_items}</ul>{more_note}"
    return f"<p>{html.escape(str(items))}</p>"


def make_card_html(title: str, value) -> str:
    if isinstance(value, list):
        content = make_list_html(value)
    elif isinstance(value, dict):
        dumped = json.dumps(value, indent=2)
        content = f"<pre style='white-space:pre-wrap; word-break:break-word;'>{html.escape(dumped)}</pre>"
    else:
        safe_value = html.escape(str(value))
        content = f"<p>{safe_value}</p>"
    return (
        "<div class=\"info-card\">"
        f"<h3>{html.escape(str(title))}</h3>"
        f"{content}"
        "</div>"
    )


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Resume Parser", page_icon="📄", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap');
    [data-testid="stAppViewContainer"] {
        background-image: url("https://i.ibb.co/VWJYWczR/stylized-illustrat.png");
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
        color: #eaf2ff;
    }
    h1 { color: #eaf2ff; text-shadow: 0 0 12px rgba(0,188,212,0.6); }
    .stButton>button {
        background: linear-gradient(90deg,#00bcd4,#3f51b5);
        color: white; border-radius:10px;
        padding:8px 14px; font-weight:600;
    }
    .stButton>button:hover { transform: scale(1.03); }

    /* --- Upload section enhancement --- */
    [data-testid="stFileUploader"] label div {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: 0 0 10px rgba(0,188,212,0.8);
    }
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.95);
        border-radius: 14px;
        color: #000000;
        box-shadow: 0 0 15px rgba(0,188,212,0.3);
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
        background: rgba(255,255,255,1);
        transform: scale(1.01);
    }
    [data-testid="stFileUploader"] section button {
        background: linear-gradient(90deg,#00bcd4,#3f51b5) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploaderFileName"] {
        color: #00e6ff !important;
        font-weight: 700 !important;
        text-shadow: 0 0 12px rgba(0,230,255,0.8);
    }
    [data-testid="stFileUploaderFileName"]:hover {
        color: #7ffcff !important;
    }
    [data-testid="stFileUploaderFileDetails"] {
        color: #d4e7ff !important;
        opacity: 0.9;
    }

    /* Modal Styling */
    .modal-overlay {
        position: fixed; top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(6px);
        display: flex; align-items: center; justify-content: center;
        z-index: 9999;
    }
    .modal-content {
        background: rgba(15, 25, 40, 0.95);
        border-radius: 16px;
        padding: 25px;
        width: 85%;
        max-width: 900px;
        max-height: 86vh;
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        color: #eaf2ff;
        animation: fadeIn 0.4s ease;
    }
    .info-card {
        background: rgba(255,255,255,0.05);
        border-radius:10px; padding:12px 14px;
        margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);
    }
    .info-card h3 { margin:0 0 8px 0; color:#00d0ff; }
    .info-card p, .info-card li { color:#dfe9f7; font-size:14px; }
    @keyframes fadeIn {
        from {opacity:0; transform:scale(0.95);}
        to {opacity:1; transform:scale(1);}
    }
    [data-testid="stTextArea"] textarea {
    background-color: white !important;  /* Make background white */
    color: #000000 !important;            /* Black text for contrast */
    font-weight: 500;
    border-radius: 12px !important;
    border: 1px solid #ddd !important;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.1);
    }

    /* Label (Preview) color and style */
    [data-testid="stTextArea"] label {
        color: #ffffff !important;            /* Keep label white to match your theme */
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 style='text-align:center;'>📄 Resume Parser</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; margin-top:-12px; color:#cfeffb;'>Powered by LangChain & Google Gemini</p>", unsafe_allow_html=True)
st.write("")

uploaded_file = st.file_uploader("Upload resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False

if uploaded_file:
    with st.spinner("📂 Extracting text..."):
        docs = load_resume_docs(uploaded_file)
        if not docs:
            st.error("Unsupported file type or loader failed.")
            st.stop()

    full_text = "\n\n".join([d.page_content for d in docs])
    st.subheader("🧾 Extracted Text (Preview)")
    st.text_area("Preview", value=full_text[:5000], height=260)

    if not st.session_state.show_popup:
        if st.button("🚀 Parse with LLM"):
            with st.spinner("🤖 Sending to Gemini for parsing..."):
                formatted = prompt_template.format(text=full_text)
                response = llm.invoke(formatted)
                raw = getattr(response, "content", "") if response else ""
                cleaned = clean_model_json(raw)
                try:
                    parsed = json.loads(cleaned)
                except Exception:
                    parsed = {"Raw Output": cleaned}

                st.session_state.parsed_data = parsed
                st.session_state.show_popup = True
                st.rerun()


# -------------------------------
# Show Popup
# -------------------------------
if st.session_state.show_popup and st.session_state.parsed_data:
    parsed = st.session_state.parsed_data
    preferred_keys = ["Name", "Email", "Phone", "LinkedIn", "Skills", "Education",
                      "Experience", "Projects", "Certifications", "Languages"]

    cards = ""
    for k in preferred_keys:
        if k in parsed:
            cards += make_card_html(k, parsed[k])
    for k in parsed:
        if k not in preferred_keys:
            cards += make_card_html(k, parsed[k])

    cards = re.sub(r'(?m)^\s*</div>\s*$', '', cards)

    st.markdown(
        f"""
        <div class="modal-overlay">
            <div class="modal-content">
                <h2>📊 Parsed Resume Details</h2>
                {cards}
                <div style="text-align:center; margin-top:25px;">
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔁 Try Another Resume"):
        st.session_state.show_popup = False
        st.session_state.parsed_data = None
        st.rerun()

    st.markdown("</div></div></div>", unsafe_allow_html=True)
