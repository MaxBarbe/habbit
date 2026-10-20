import streamlit as st

def apply_styles():
    st.markdown("""
<style>
:root{--bg:#F5F2EA;--card:#FCFBF7;--ink:#111;--muted:#74716A;--line:#DEDAD1}
.stApp{background:var(--bg);color:var(--ink)}
.block-container{max-width:1380px;padding-top:1.1rem;padding-bottom:3rem}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
.brand{font-size:1.05rem;font-weight:800;letter-spacing:-.04em}
.kicker{color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.12em}
.title{font-size:clamp(2.2rem,5vw,4.8rem);line-height:.94;font-weight:800;letter-spacing:-.065em;margin:.2rem 0 .7rem}
.copy{max-width:660px;color:var(--muted);font-size:.98rem;margin-bottom:1.2rem}
.section{font-size:1.35rem;font-weight:750;letter-spacing:-.035em;margin:.3rem 0 .7rem}
.meta{color:var(--muted);font-size:.82rem}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;background:#ffffff80;padding:.42rem .72rem;font-size:.78rem}
.piece{font-size:.86rem;font-weight:650;margin-top:.35rem}
.piece-meta{font-size:.74rem;color:var(--muted)}
div[data-testid="stImage"] img{border-radius:14px}
div[data-testid="stButton"] button{border-radius:999px;min-height:2.55rem;font-weight:650}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fcfbf7b8;border-radius:18px}
@media(max-width:780px){.block-container{padding-left:1rem;padding-right:1rem}.title{font-size:2.6rem}}
</style>
""", unsafe_allow_html=True)
