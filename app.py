"""
EPORTH Blog Generator — Interface v7 (Adobe Dark Tool)
"""

import base64
import os
import re
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from blog_generator import (
    PRODUCT_WIKI_MAP,
    fetch_new_pexels_image,
    fetch_url_content,
    generate_blog_with_claude,
    insert_images_into_html,
    load_brand_context,
    load_product_wiki,
    post_to_shopify,
)

# ---------------------------------------------------------------------------
# Logo — load from local assets (transparent PNG)
# ---------------------------------------------------------------------------

_LOGO_PATH = Path(__file__).parent / "assets" / "logo_small.png"
_LOGO_B64 = ""
if _LOGO_PATH.exists():
    _LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode()
_LOGO_SRC = f"data:image/png;base64,{_LOGO_B64}" if _LOGO_B64 else ""

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EPORTH · Blog Generator",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Design System — Adobe Dark Tool
# ---------------------------------------------------------------------------

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">

<style>
/* ── DESIGN TOKENS ── */
:root {
  --accent:      #B7F231;
  --accent-ink:  #152003;
  --bg:          #0B0D08;
  --panel:       #11140C;
  --panel-2:     #161A10;
  --raise:       #1C2114;
  --border:      #252B1B;
  --border-soft: #1D2214;
  --text:        #EAEEDF;
  --text-2:      #A9B19A;
  --text-3:      #6E7660;
  --danger:      #f17777;
  --radius:      10px;
  --font-ui:      "Manrope", system-ui, sans-serif;
  --font-display: "Space Grotesk", system-ui, sans-serif;
  /* legacy aliases used in Python strings */
  --accent-green: var(--accent);
  --bg-app:       var(--bg);
  --bg-panel:     var(--panel);
  --bg-panel-alt: var(--panel-2);
  --bg-input:     var(--bg);
  --bg-hover:     var(--raise);
  --border-subtle:var(--border-soft);
  --border-focus: var(--accent);
  --text-primary: var(--text);
  --text-secondary:var(--text-2);
  --text-tertiary: var(--text-3);
  --text-disabled: var(--text-3);
  --accent-blue:  var(--text-3);
  --accent-teal:  var(--accent);
  --radius-sm: 5px;
  --radius-md: var(--radius);
  --size-xs: 10px;
  --size-sm: 11px;
  --size-md: 12px;
  --size-body: 13px;
}

/* ── BASE ── */
html, body, .stApp { background: var(--bg) !important; font-family: var(--font-ui) !important; }
* { box-sizing: border-box; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--panel) !important;
    border-right: 1px solid var(--border-soft) !important;
    min-width: 296px !important;
    max-width: 296px !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* ── MAIN ── */
[data-testid="stMainBlockContainer"] {
    padding: 0 32px 96px !important;
    max-width: 820px !important;
}

/* ── ARTICLE TYPOGRAPHY ── */
.stMarkdown p {
    color: var(--text-2) !important;
    font-family: var(--font-ui) !important;
    font-size: 15.5px !important;
    line-height: 1.75 !important;
}
.stMarkdown h2 {
    color: var(--text) !important;
    font-family: var(--font-display) !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    margin: 22px 0 2px !important;
    padding-bottom: 0 !important;
    border-bottom: none !important;
}
.stMarkdown h3 {
    color: var(--text) !important;
    font-family: var(--font-display) !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    margin: 18px 0 2px !important;
}
.stMarkdown strong { color: var(--text) !important; }
.stMarkdown a { color: var(--accent) !important; font-weight: 700 !important; text-decoration: none !important; }
.stMarkdown a:hover { text-decoration: underline !important; }
.stMarkdown ul li, .stMarkdown ol li {
    color: var(--text-2) !important;
    font-family: var(--font-ui) !important;
    font-size: 15.5px !important;
    line-height: 1.75 !important;
}

/* ── SIDEBAR LABELS ── */
.side-label {
    font-size: 10.5px; font-weight: 800; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--text-3);
    display: flex; align-items: center; gap: 8px;
    padding: 0 4px; font-family: var(--font-ui);
}
.side-label::after {
    content: ""; flex: 1; height: 1px; background: var(--border-soft);
}
/* legacy alias */
.panel-label { display: flex; align-items: center; gap: 6px;
    font-family: var(--font-ui); font-size: 10.5px; font-weight: 800;
    letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-3);
    padding: 10px 12px 6px; }
.panel-label::after { content: ""; flex: 1; height: 1px; background: var(--border-soft); }
.panel-label i { display: none; }

/* ── RADIO → ref-option style ── */
[data-testid="stSidebar"] [data-testid="stRadio"] { padding: 0 20px !important; }
[data-testid="stRadio"] > div {
    gap: 4px !important;
    flex-direction: column !important;
    padding: 0 !important;
}
[data-testid="stRadio"] label {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius) !important;
    padding: 9px 11px !important;
    color: var(--text-2) !important;
    font-family: var(--font-ui) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: background 0.12s, border-color 0.12s, color 0.12s !important;
    width: 100% !important;
}
[data-testid="stRadio"] label:hover {
    background: var(--panel-2) !important;
    color: var(--text) !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: var(--panel-2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
[data-testid="stRadio"] input[type="radio"] { display: none !important; }
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 13px !important;
    color: inherit !important;
    line-height: 1.2 !important;
    font-family: var(--font-ui) !important;
}
/* caption below each radio option */
[data-testid="stRadio"] [data-testid="stCaptionContainer"] p {
    font-size: 11px !important;
    color: var(--text-3) !important;
    margin-top: 1px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}

/* ── INPUTS ── */
.stTextInput input, .stTextArea textarea {
    background: var(--bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-ui) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 12px !important;
    transition: border-color 0.12s, box-shadow 0.12s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label {
    font-family: var(--font-ui) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    color: var(--text-2) !important;
    margin-bottom: 3px !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
    font-size: 14px !important;
    padding: 6px 12px !important;
}
[data-testid="stSelectbox"] label {
    font-family: var(--font-ui) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    color: var(--text-2) !important;
}

/* ── BUTTONS ── */
[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: var(--accent-ink) !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 16px !important;
    transition: background 0.12s, border-color 0.12s !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: color-mix(in srgb, var(--accent) 88%, white) !important;
    border-color: color-mix(in srgb, var(--accent) 88%, white) !important;
}
[data-testid="stBaseButton-secondary"] {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    transition: background 0.12s, border-color 0.12s !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: var(--raise) !important;
    border-color: #333b26 !important;
    color: var(--text) !important;
}
button:disabled { opacity: 0.45 !important; cursor: default !important; pointer-events: none !important; }

/* ── TABS ── */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border-soft) !important;
    padding: 0 !important;
    gap: 0 !important;
}
[data-baseweb="tab"] {
    color: var(--text-3) !important;
    font-family: var(--font-ui) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 11px 14px !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: color 0.12s !important;
}
[data-baseweb="tab"]:hover { color: var(--text-2) !important; }
[aria-selected="true"][data-baseweb="tab"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}
[data-testid="stTabsContent"] { padding-top: 34px !important; }

/* ── ALERTS ── */
div[data-baseweb="notification"] {
    border-radius: var(--radius) !important;
    font-family: var(--font-ui) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
div[data-baseweb="notification"][kind="positive"] * { color: var(--accent) !important; }
div[data-baseweb="notification"][kind="positive"] {
    background: color-mix(in srgb, var(--accent) 7%, transparent) !important;
    border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent) !important;
}
div[data-baseweb="notification"][kind="info"] * { color: var(--accent) !important; }
div[data-baseweb="notification"][kind="info"] {
    background: color-mix(in srgb, var(--accent) 5%, transparent) !important;
    border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent) !important;
}
div[data-baseweb="notification"][kind="warning"] * { color: #D9B54A !important; }
div[data-baseweb="notification"][kind="warning"] {
    background: rgba(217,181,74,0.05) !important;
    border: 1px solid rgba(217,181,74,0.25) !important;
}

hr {
    border: none !important;
    border-top: 1px solid var(--border-soft) !important;
    margin: 10px 0 !important;
}
[data-testid="stCaptionContainer"] p {
    font-family: var(--font-ui) !important;
    font-size: 11px !important;
    color: var(--text-3) !important;
}
img { border-radius: var(--radius) !important; }

/* ── IMAGE CARDS ── */
.img-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 16px;
    display: flex; flex-direction: column;
}
.img-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: transparent;
    border-bottom: 1px solid var(--border-soft);
}
.badge-capa {
    display: inline-flex; align-items: center; gap: 4px;
    font-family: var(--font-ui);
    font-size: 10px; font-weight: 800; letter-spacing: 0.12em;
    text-transform: uppercase;
    background: var(--accent); color: var(--accent-ink);
    padding: 2px 7px; border-radius: 5px;
}
.badge-body {
    display: inline-flex; align-items: center; gap: 4px;
    font-family: var(--font-ui);
    font-size: 11.5px; font-weight: 700;
    color: var(--text-2);
}
.img-meta {
    font-family: var(--font-ui); font-size: 11px; font-weight: 500;
    color: var(--text-3); padding: 8px 14px;
    display: flex; align-items: center; gap: 6px;
    border-top: 1px solid var(--border-soft);
}
.img-meta .credit { color: var(--text-2); font-weight: 700; }
.img-keyword { font-family: var(--font-ui); font-size: 11px; color: var(--text-3); }
/* ── STATUS CHIPS ── */
.status-row {
    display: flex; align-items: center; gap: 14px;
    padding: 12px 4px 0; border-top: 1px solid var(--border-soft);
    font-family: var(--font-ui); font-size: 11.5px; font-weight: 600;
    color: var(--text-3); margin-top: auto;
}
.status-chip { display: inline-flex; align-items: center; gap: 6px; }
.status-chip i { width: 7px; height: 7px; border-radius: 50%; background: var(--text-3); flex: none; display: inline-block; }
.status-ok { color: var(--text-2); }
.status-ok i { background: var(--accent); box-shadow: 0 0 6px color-mix(in srgb, var(--accent) 60%, transparent); }
.status-err { color: var(--text-3); }

/* ── EXPANDER + FILE UPLOADER ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border-soft) !important;
    border-radius: var(--radius) !important;
    background: var(--panel) !important;
    margin-top: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-ui) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    color: var(--text-2) !important;
    padding: 9px 12px !important;
    background: transparent !important;
}
[data-testid="stExpander"] summary:hover { color: var(--text) !important; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 12px !important;
    border-top: 1px solid var(--border-soft) !important;
}
[data-testid="stFileUploader"] {
    background: var(--bg) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 14px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
[data-testid="stFileUploader"] label { font-family: var(--font-ui) !important; font-size: 12px !important; color: var(--text-2) !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] * { font-family: var(--font-ui) !important; font-size: 12px !important; color: var(--text-2) !important; }

/* ── TOPBAR ── */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 0 0 0;
    height: 56px;
    border-bottom: 1px solid var(--border-soft);
    margin-bottom: 48px;
    font-family: var(--font-ui);
}
.crumbs { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--text-3); }
.crumbs .sep { color: var(--border); }
.crumbs .here { color: var(--text-2); }
.topbar-right { display: flex; align-items: center; gap: 10px; }
.pub-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11.5px; font-weight: 800; letter-spacing: 0.04em;
    padding: 4px 10px; border-radius: 99px;
    border: 1px solid var(--border); color: var(--text-3);
    font-family: var(--font-ui);
}
.pub-badge i { width: 6px; height: 6px; border-radius: 50%; background: var(--text-3); display:inline-block; }
.pub-badge[data-kind="published"] {
    color: var(--accent); border-color: color-mix(in srgb, var(--accent) 35%, transparent);
    background: color-mix(in srgb, var(--accent) 8%, transparent);
}
.pub-badge[data-kind="published"] i { background: var(--accent); }
.pub-badge[data-kind="draft"] { color: var(--text-2); }
.pub-badge[data-kind="draft"] i { background: #d9b54a; }

/* ── POST HEAD ── */
.post-head { display: flex; flex-direction: column; gap: 14px; margin-bottom: 28px; }
.accent-bar { width: 44px; height: 4px; border-radius: 2px; background: var(--accent); }
.post-title {
    margin: 0; font-family: var(--font-display);
    font-size: 33px; line-height: 1.22; font-weight: 700;
    letter-spacing: -0.01em; color: var(--text);
}
.post-meta { display: flex; align-items: center; gap: 14px; font-size: 12.5px; font-weight: 600; color: var(--text-3); font-family: var(--font-ui); }
.post-meta .dot { width: 3px; height: 3px; border-radius: 50%; background: var(--text-3); display:inline-block; }

/* ── EMPTY STATE ── */
.empty {
    margin-top: 9vh;
    display: flex; flex-direction: column; align-items: center; text-align: center; gap: 6px;
    font-family: var(--font-ui);
}
.empty-mark {
    width: 64px; height: 64px; border-radius: 18px;
    background: var(--panel-2); border: 1px solid var(--border);
    display: grid; place-items: center; margin-bottom: 14px;
}
.empty-mark span {
    width: 22px; height: 22px; border-radius: 6px;
    background: color-mix(in srgb, var(--accent) 18%, transparent);
    border: 1.5px solid var(--accent);
    display: block;
}
.empty h2 { margin: 0; font-family: var(--font-display); font-size: 20px; font-weight: 600; color: var(--text); }
.empty p { margin: 0; color: var(--text-3); max-width: 380px; font-weight: 500; }
.hint-steps { display: flex; gap: 8px; margin-top: 22px; flex-wrap: wrap; justify-content: center; }
.hint-step {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px; font-weight: 700; color: var(--text-3);
    border: 1px solid var(--border-soft); border-radius: 99px;
    padding: 6px 13px 6px 7px; background: var(--panel);
}
.hint-step b {
    width: 20px; height: 20px; border-radius: 50%; flex: none;
    background: var(--panel-2); border: 1px solid var(--border);
    display: grid; place-items: center;
    font-size: 10.5px; color: var(--text-2);
}
/* ── OPEN BLOG LINK ── */
.open-blog {
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
    border: 1px dashed var(--border);
    border-radius: var(--radius); padding: 10px 13px;
    color: var(--text-3); font-weight: 700; font-size: 13px;
    text-decoration: none; font-family: var(--font-ui);
    transition: color 0.12s, border-color 0.12s, background 0.12s;
}
.open-blog.ready {
    color: var(--accent); border-style: solid;
    border-color: color-mix(in srgb, var(--accent) 35%, transparent);
    background: color-mix(in srgb, var(--accent) 7%, transparent);
}
.open-blog.ready:hover { background: color-mix(in srgb, var(--accent) 13%, transparent); }

/* ── STREAMLIT CHROME — hide decoration, keep sidebar toggle intact ── */
[data-testid="stDeployButton"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"] { display: none !important; }
/* Make header transparent so it doesn't show the grey bar but toggle button still works */
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; }

/* ── STREAMLIT RADIO — hide native circle indicator only ── */
[data-testid="stRadio"] input[type="radio"] { display: none !important; }

/* ── SPINNER / PROGRESS ── */
[data-testid="stSpinner"] > div { border-color: var(--border) !important; border-top-color: var(--accent) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-thumb { background: var(--raise); border-radius: 5px; border: 2px solid var(--bg); }
::-webkit-scrollbar-track { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

for key, val in [("article", None), ("published_url", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

missing = [v for v in ["GOOGLE_API_KEY", "SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN", "SHOPIFY_BLOG_ID"]
           if not os.environ.get(v)]
if missing:
    st.error(f"Variáveis faltando no .env: `{'`, `'.join(missing)}`")
    st.stop()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _show_image(img: dict, **kwargs):
    if img.get("_bytes"):
        st.image(BytesIO(img["_bytes"]), **kwargs)
    elif img.get("src"):
        st.image(img["src"], **kwargs)


def _current_article() -> dict:
    if not st.session_state.article:
        return {}
    art = dict(st.session_state.article)
    for field, key in [
        ("title", "e_title"), ("meta_description", "e_meta"),
        ("tags", "e_tags"), ("summary_html", "e_summary"), ("body_html", "e_body"),
    ]:
        if key in st.session_state:
            art[field] = st.session_state[key]
    return art


def _rebuild_body_html(art: dict) -> str:
    """Strip existing figure tags and re-insert current images[1:] into body_html."""
    clean = re.sub(r'<figure[^>]*>.*?</figure>', '', art.get("body_html", ""), flags=re.DOTALL)
    return insert_images_into_html(clean.strip(), art.get("_images", []))


def _bytes_to_data_uri(raw: bytes, mime: str = "jpeg") -> str:
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"


def _apply_cover_overlay(img_bytes: bytes) -> bytes:
    """Composite EPORTH logo + black-to-transparent gradient onto cover image."""
    if not img_bytes or not _LOGO_PATH.exists():
        return img_bytes
    try:
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
        w, h = img.size

        # Black → transparent gradient covering top 45% of image
        grad_h = int(h * 0.45)
        strip = Image.new("L", (1, grad_h))
        for y in range(grad_h):
            strip.putpixel((0, y), int(210 * (1 - y / grad_h)))
        strip = strip.resize((w, grad_h), Image.BILINEAR)
        black_band = Image.new("RGBA", (w, grad_h), (0, 0, 0, 255))
        black_band.putalpha(strip)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay.paste(black_band, (0, 0))
        img = Image.alpha_composite(img, overlay)

        # EPORTH logo centered horizontally, 24px from top
        logo = Image.open(str(_LOGO_PATH)).convert("RGBA")
        logo_w = min(int(w * 0.22), 200)
        logo_h = int(logo.height * logo_w / logo.width)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo, ((w - logo_w) // 2, 24), logo)

        out = BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=90)
        return out.getvalue()
    except Exception:
        return img_bytes


# ---------------------------------------------------------------------------
# SIDEBAR — Tool Panel
# ---------------------------------------------------------------------------

with st.sidebar:
    # ── Brand header ─────────────────────────────────────────────────────
    logo_html = (
        f'<img src="{_LOGO_SRC}" style="width:118px;display:block;filter:brightness(0) saturate(100%) '
        f'invert(86%) sepia(35%) saturate(700%) hue-rotate(40deg) brightness(105%);" />'
        if _LOGO_SRC else
        '<span style="font-family:var(--font-display);font-size:20px;font-weight:700;color:var(--accent);">EPORTH</span>'
    )
    st.markdown(f"""
<div style="padding:24px 20px 12px;">
    {logo_html}
    <div style="font-family:var(--font-display);font-size:10px;font-weight:600;letter-spacing:0.28em;
                color:var(--text-3);text-transform:uppercase;margin-top:7px;">
        Blog Generator
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Reference section ────────────────────────────────────────────────
    st.markdown("""
<div style="padding:0 20px 8px;">
<div class="side-label">Referência</div>
</div>
""", unsafe_allow_html=True)

    ref_type = st.radio(
        "ref",
        ["Tema livre", "URL", "Produto", "Evento"],
        label_visibility="collapsed",
        captions=["Escreva o assunto do post", "Gerar a partir de um link", "Baseado em um produto seu", "Datas e campanhas sazonais"],
    )

    st.markdown("<div style='padding:0 20px 8px;'>", unsafe_allow_html=True)

    reference = ref_key = None

    if ref_type == "Tema livre":
        ref_key = "topic"
        reference = st.text_area(
            "Tema do post",
            placeholder="backup residencial, energia solar para camping...",
            height=76,
        )
    elif ref_type == "URL":
        ref_key = "url"
        reference = st.text_input("Endereço da página", placeholder="https://...")
    elif ref_type == "Produto":
        ref_key = "produto"
        reference = st.selectbox(
            "Produto",
            list(PRODUCT_WIKI_MAP.keys()),
            format_func=lambda x: x.replace("-", " ").title(),
        )
    else:
        ref_key = "evento"
        reference = st.text_input(
            "Evento ou data", placeholder="Copa do Mundo, Green November..."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Generate button ──────────────────────────────────────────────────
    st.markdown("<div style='padding:0 20px 4px;'>", unsafe_allow_html=True)
    btn_label = "Gerar novamente" if st.session_state.article else "Gerar Blog"
    if st.button(btn_label, type="primary", use_container_width=True, disabled=not reference):
        with st.spinner("Processando..."):
            brand = load_brand_context()
            if ref_key == "url":
                try:
                    content = fetch_url_content(reference)
                except Exception as e:
                    st.error(f"Erro URL: {e}")
                    st.stop()
            elif ref_key == "produto":
                content = load_product_wiki(reference)
            else:
                content = reference
            try:
                art = generate_blog_with_claude(ref_key, content, brand)
                # Apply logo + gradient overlay to cover image
                images = art.get("_images", [])
                if images and images[0].get("_bytes"):
                    new_bytes = _apply_cover_overlay(images[0]["_bytes"])
                    images[0]["_bytes"] = new_bytes
                    images[0]["src"] = _bytes_to_data_uri(new_bytes)
                st.session_state.article = art
                st.session_state.published_url = None
                for k in ["e_title", "e_meta", "e_tags", "e_summary", "e_body"]:
                    st.session_state.pop(k, None)
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Publish section (conditional) ────────────────────────────────────
    if st.session_state.article:
        images_sb = st.session_state.article.get("_images", [])
        cover_ok = bool(images_sb and (images_sb[0].get("_bytes") or images_sb[0].get("src")))

        st.markdown("""
<div style="padding:0 20px 8px;">
<div class="side-label">Publicar</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='padding:0 20px 6px;'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Rascunho", use_container_width=True, key="btn_draft"):
                with st.spinner("..."):
                    try:
                        r = post_to_shopify(_current_article(), published=False)
                        st.session_state.published_url = (
                            "rascunho",
                            f"https://{os.environ['SHOPIFY_STORE_URL']}/admin/articles/{r['id']}",
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        with c2:
            if st.button("Publicar", type="primary", use_container_width=True, key="btn_publish"):
                with st.spinner("..."):
                    try:
                        r = post_to_shopify(_current_article(), published=True)
                        st.session_state.published_url = (
                            "publicado",
                            f"https://energiaportatil.com.br/blogs/novidades/{r['handle']}",
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        # ── Open blog link ────────────────────────────────────────────────
        if st.session_state.published_url:
            status_pub, url_pub = st.session_state.published_url
            ready_cls = "ready" if status_pub == "publicado" else ""
            label = "Abrir no blog" if status_pub == "publicado" else "Ver rascunho no Shopify"
            st.markdown(
                f'<a class="open-blog {ready_cls}" href="{url_pub}" target="_blank">'
                f'<span>{label}</span><span>→</span></a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="open-blog"><span>Abrir no blog</span><span>→</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        n_imgs = len(images_sb)
        capa_cls = "status-ok" if cover_ok else "status-err"
        img_cls = "status-ok" if n_imgs >= 3 else "status-err"
        st.markdown(f"""
<div style="padding:0 20px;">
<div class="status-row">
    <span class="status-chip {img_cls}"><i></i>{n_imgs} img</span>
    <span class="status-chip {capa_cls}"><i></i>{'capa pronta' if cover_ok else 'sem capa'}</span>
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MAIN — empty state
# ---------------------------------------------------------------------------

if not st.session_state.article:
    st.markdown("""
<div class="empty">
    <div class="empty-mark"><span></span></div>
    <h2>Comece um novo post</h2>
    <p>Escolha uma referência na barra lateral, descreva o tema e clique em Gerar Blog.</p>
    <div class="hint-steps">
        <span class="hint-step"><b>1</b>Referência</span>
        <span class="hint-step"><b>2</b>Tema</span>
        <span class="hint-step"><b>3</b>Gerar</span>
    </div>
</div>""", unsafe_allow_html=True)
    st.stop()

art = st.session_state.article
images = art.get("_images", [])
body = art.get("body_html", "")

# ---------------------------------------------------------------------------
# TOPBAR
# ---------------------------------------------------------------------------

pub_state = st.session_state.get("published_url")
if pub_state:
    badge_kind = "published" if pub_state[0] == "publicado" else "draft"
    badge_text = "Publicado" if pub_state[0] == "publicado" else "Rascunho salvo"
    badge_html = f'<span class="pub-badge" data-kind="{badge_kind}"><i></i>{badge_text}</span>'
else:
    badge_html = '<span class="pub-badge" data-kind="draft"><i></i>Não publicado</span>'

title_crumb = (art.get("title", "Novo post")[:48] + "…") if len(art.get("title", "")) > 48 else art.get("title", "Novo post")

st.markdown(f"""
<div class="topbar">
    <nav class="crumbs">
        <span>Blogs</span>
        <span class="sep">/</span>
        <span class="here">{title_crumb}</span>
    </nav>
    <div class="topbar-right">
        {badge_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# POST HEAD
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="post-head">
    <div class="accent-bar"></div>
    <h1 class="post-title">{art.get('title','')}</h1>
    <div class="post-meta">
        <span>11 de junho de 2026</span>
        <span class="dot"></span>
        <span>5 min de leitura</span>
        <span class="dot"></span>
        <span>energiaportatil.com.br</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tab_text, tab_imgs, tab_edit = st.tabs([
    "Texto",
    f"Imagens  {len(images)}",
    "Editar",
])

# ── TEXTO ─────────────────────────────────────────────────────────────────
with tab_text:
    clean_body = re.sub(r'<figure[^>]*>.*?</figure>', '', body, flags=re.DOTALL)
    st.markdown(clean_body, unsafe_allow_html=True)

# ── IMAGENS ───────────────────────────────────────────────────────────────
with tab_imgs:
    def _apply_upload(idx: int, uploaded_file) -> None:
        """Replace image slot with uploaded file."""
        raw = uploaded_file.read()
        ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
        b64 = base64.b64encode(raw).decode()
        data_uri = f"data:image/{mime};base64,{b64}"

        old_src = st.session_state.article["_images"][idx].get("src", "")
        # Apply cover overlay for idx=0
        if idx == 0:
            raw = _apply_cover_overlay(raw)
            data_uri = _bytes_to_data_uri(raw)
        st.session_state.article["_images"][idx].update({
            "src": data_uri,
            "_bytes": raw,
            "alt": uploaded_file.name,
            "photographer": "Upload manual",
            "_custom": True,
        })
        # idx=0 is cover only — not in body_html; only body images (idx>0) need replace
        if idx > 0 and old_src:
            st.session_state.article["body_html"] = (
                st.session_state.article["body_html"].replace(old_src, data_uri)
            )
        st.session_state.pop("e_body", None)  # invalidate stale editor HTML

    st.markdown("""
<div style="font-family:var(--font-ui);font-size:12px;font-weight:600;color:var(--text-3);
            margin-bottom:20px;">
    Imagem 1 é a capa do post (enviada para o Shopify). As demais são inseridas no corpo do artigo.
</div>""", unsafe_allow_html=True)

    # Ensure 3 slots always exist (even if Pexels returned fewer)
    while len(st.session_state.article["_images"]) < 3:
        st.session_state.article["_images"].append({
            "src": "", "_bytes": None, "alt": "", "photographer": "", "_keyword": "",
        })
    images = st.session_state.article["_images"]

    for idx, img in enumerate(images):
        has_image = bool(img.get("_bytes") or img.get("src"))
        is_custom = img.get("_custom", False)

        badge = (
            '<span class="badge-capa">CAPA</span>'
            if idx == 0 else
            f'<span class="badge-body">Corpo {idx}</span>'
        )
        source_tag = (
            f'<span class="img-keyword" style="color:var(--text-2);font-weight:700;font-size:11px;">Upload manual</span>'
            if is_custom else
            f'<span class="img-keyword">{img.get("_keyword", "")}</span>'
        )

        st.markdown(f"""
<div class="img-card">
    <div class="img-card-header">
        {badge}
        {source_tag}
    </div>
</div>""", unsafe_allow_html=True)

        if has_image:
            _show_image(img, use_container_width=True)
            col_meta, col_pexels = st.columns([5, 1])
            with col_meta:
                credit = img.get("photographer", "")
                if credit and not is_custom:
                    st.markdown(
                        f'<div class="img-meta">'
                        f'<span class="credit">{credit}</span>'
                        f'<span style="color:var(--border);">·</span>'
                        f'Pexels'
                        f'<span style="color:var(--border);">·</span>'
                        f'{img.get("alt", "")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="img-meta">{img.get("alt","Imagem manual")}</div>',
                        unsafe_allow_html=True,
                    )
            with col_pexels:
                if not is_custom and img.get("_keyword"):
                    if st.button("Trocar", key=f"regen_{idx}", use_container_width=True,
                                 help="Buscar nova imagem no Pexels"):
                        with st.spinner("Buscando..."):
                            new_img = fetch_new_pexels_image(
                                img.get("_keyword", "portable power station"),
                                exclude_url=img["src"],
                            )
                        if new_img:
                            old_src = img["src"]
                            # Apply cover overlay for idx=0
                            if idx == 0 and new_img.get("_bytes"):
                                new_bytes = _apply_cover_overlay(new_img["_bytes"])
                                new_img["_bytes"] = new_bytes
                                new_img["src"] = _bytes_to_data_uri(new_bytes)
                            st.session_state.article["_images"][idx] = new_img
                            # idx=0 is cover only — not in body_html
                            if idx > 0 and old_src:
                                st.session_state.article["body_html"] = (
                                    st.session_state.article["body_html"].replace(old_src, new_img["src"])
                                )
                            st.session_state.pop("e_body", None)
                            st.rerun()
                        else:
                            st.warning("Nenhuma alternativa encontrada.")
        else:
            st.markdown("""
<div style="aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;
            background:repeating-linear-gradient(-45deg,var(--panel-2) 0 10px,var(--panel) 10px 20px);
            font-family:var(--font-ui);font-size:11.5px;color:var(--text-3);letter-spacing:0.02em;">
    Sem imagem — faça upload abaixo
</div>""", unsafe_allow_html=True)

        # ── Upload section ────────────────────────────────────────────
        with st.expander(
            f"{'Substituir' if has_image else 'Adicionar'} imagem {idx + 1}",
            expanded=not has_image,
        ):
            uploaded = st.file_uploader(
                "upload",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"upload_{idx}",
                label_visibility="collapsed",
                help="PNG, JPG ou WEBP. Recomendado: 1200×800px ou maior.",
            )
            if uploaded is not None:
                _apply_upload(idx, uploaded)
                st.rerun()

        if idx < len(images) - 1:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    st.markdown("""
<div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border-subtle);">
</div>""", unsafe_allow_html=True)
    if st.button(
        "Aplicar imagens ao artigo",
        type="primary",
        use_container_width=True,
        key="apply_imgs",
        help="Reconstrói o HTML do artigo com as imagens atuais e descarta rascunho do editor",
    ):
        new_body = _rebuild_body_html(st.session_state.article)
        st.session_state.article["body_html"] = new_body
        st.session_state.pop("e_body", None)
        st.success("Imagens aplicadas. Artigo pronto para publicar.")

# ── EDITAR ────────────────────────────────────────────────────────────────
with tab_edit:
    st.text_input("Título", value=art.get("title", ""), key="e_title")
    st.text_input(
        "Meta description",
        value=art.get("meta_description", ""),
        help="Ideal: 150–160 caracteres",
        key="e_meta",
    )
    cc = len(st.session_state.get("e_meta", ""))
    ok = 140 <= cc <= 160
    st.markdown(
        f'<div style="font-family:var(--font-ui);font-size:10px;margin:-6px 0 8px;'
        f'display:flex;align-items:center;gap:5px;'
        f'color:{"var(--accent-green)" if ok else "var(--accent-gold)"};">'
        f'<i class="bi bi-{"check-circle-fill" if ok else "exclamation-circle"}"></i>'
        f'&nbsp;{cc} chars {"— dentro do ideal" if ok else "— ideal 150–160"}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.text_input("Tags", value=art.get("tags", ""), key="e_tags")
    st.text_area("Resumo", value=art.get("summary_html", ""), height=76, key="e_summary")
    st.text_area("Corpo HTML", value=body, height=440, key="e_body")
