from pathlib import Path
import sqlite3, time
import streamlit as st

from backend.services.wardrobe_pipeline import analyze_and_save
from backend.services.outfit_recommender import recommend_outfits
from backend.services.context_service import get_context
from backend.services.fashn_tryon import fashn_available, generate_outfit_tryon
from ui.styles import apply_styles
from ui.components import pick, piece_card, weather_text, outfit_piece, outfit_signature, abs_path

APP_ROOT=Path(__file__).resolve().parent
DB_PATH=APP_ROOT/"backend/database/wardrobe.db"
UPLOAD_DIR=APP_ROOT/"backend/storage/originals"
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)

st.set_page_config(page_title="APP-Habit",page_icon="✦",layout="wide",initial_sidebar_state="collapsed")
apply_styles()

def load_wardrobe():
    if not DB_PATH.exists(): return []
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    try:
        tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        if not tables:return []
        table=next((t for t in tables if t.lower() in {"wardrobe","clothes","garments","items"}),tables[0])
        return [dict(r) for r in con.execute(f'SELECT * FROM "{table}" ORDER BY rowid DESC')]
    finally: con.close()

@st.cache_data(ttl=300,show_spinner=False)
def current_context():
    return get_context(latitude=43.7102,longitude=7.2620)

def clear_tryon():
    for k in list(st.session_state):
        if str(k).startswith("fashn_tryon_"): del st.session_state[k]

def save_upload(u):
    p=UPLOAD_DIR/f"upload_{time.time_ns()}{Path(u.name).suffix.lower() or '.jpg'}"
    p.write_bytes(u.getbuffer()); return p

if "page" not in st.session_state: st.session_state.page="Looks"
a,b=st.columns([.55,.45],vertical_alignment="center")
with a: st.markdown('<div class="brand">APP•Habit</div>',unsafe_allow_html=True)
with b:
    c1,c2,c3=st.columns(3)
    for col,name in zip((c1,c2,c3),("Looks","Dressing","Ajouter")):
        if col.button(name,use_container_width=True,type="primary" if st.session_state.page==name else "secondary"):
            st.session_state.page=name; st.rerun()
st.divider()
wardrobe=load_wardrobe()

if st.session_state.page=="Looks":
    context=current_context()
    st.markdown('<div class="kicker">Sélection du jour</div><div class="title">Vos looks,<br>avec vos vêtements.</div>',unsafe_allow_html=True)
    st.markdown('<div class="copy">Trois tenues composées automatiquement à partir de votre dressing et du contexte météo.</div>',unsafe_allow_html=True)
    st.markdown(f'<span class="pill">{weather_text(context)}</span>',unsafe_allow_html=True)
    st.write("")
    if not wardrobe: st.info("Ton dressing est vide. Ajoute d’abord quelques vêtements.")
    else:
        try: outfits=list(recommend_outfits(context=context,limit=3) or [])[:3]
        except Exception as e: st.error(f"Impossible de calculer les looks : {e}"); outfits=[]
        for i,outfit in enumerate(outfits,1):
            st.markdown(f'<div class="section">Look {i:02d}</div>',unsafe_allow_html=True)
            visual,details=st.columns([.62,.38],gap="large")
            key=f"fashn_tryon_{outfit_signature(outfit,i)}"
            with visual:
                cached=abs_path(st.session_state.get(key))
                if cached: st.image(str(cached),use_container_width=True)
                elif fashn_available():
                    with st.spinner(f"Génération du look {i}…"):
                        try:
                            generated=generate_outfit_tryon(outfit)
                            gp=abs_path(generated)
                            if gp:
                                st.session_state[key]=str(gp); st.image(str(gp),use_container_width=True)
                            else: st.info("Aperçu IA non disponible.")
                        except Exception as e: st.info(f"Aperçu IA non disponible : {e}")
                else:
                    ref=APP_ROOT/"backend/storage/person/reference.png"
                    if ref.exists(): st.image(str(ref),use_container_width=True)
                    st.caption("Le moteur d’essayage local n’est pas démarré.")
                st.markdown('<div class="meta">Aperçu généré avec vos vêtements · haut + bas</div>',unsafe_allow_html=True)
            with details:
                st.markdown('<div class="kicker">Pièces utilisées</div>',unsafe_allow_html=True)
                for role,title in (("top","Haut"),("bottom","Bas"),("shoes","Chaussures"),("outerwear","Extérieur")):
                    item=outfit_piece(outfit,role)
                    if item:
                        st.caption(title); piece_card(item); st.write("")
            st.divider()
        if outfits and st.button("Régénérer les aperçus"):
            clear_tryon(); st.rerun()

elif st.session_state.page=="Dressing":
    st.markdown('<div class="kicker">Votre collection</div><div class="title">Dressing.</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="copy">{len(wardrobe)} pièce(s) enregistrée(s). Les vêtements déjà analysés restent disponibles sans nouvelle analyse.</div>',unsafe_allow_html=True)
    cats=sorted({str(pick(x,"category","categorie",default="")).strip() for x in wardrobe if pick(x,"category","categorie")})
    selected=st.segmented_control("Catégorie",["Tout"]+cats,default="Tout",label_visibility="collapsed")
    shown=wardrobe if selected in (None,"Tout") else [x for x in wardrobe if str(pick(x,"category","categorie",default=""))==selected]
    cols=st.columns(4,gap="medium")
    for i,item in enumerate(shown):
        with cols[i%4]:
            with st.container(border=True): piece_card(item)

else:
    st.markdown('<div class="kicker">Nouveau vêtement</div><div class="title">Ajouter.</div>',unsafe_allow_html=True)
    st.markdown('<div class="copy">Une photo suffit. APP-Habit détoure, reconnaît et classe automatiquement la pièce.</div>',unsafe_allow_html=True)
    left,right=st.columns([.56,.44],gap="large")
    with left:
        uploaded=st.file_uploader("Photo du vêtement",type=["jpg","jpeg","png","webp"])
        if uploaded: st.image(uploaded,use_container_width=True)
    with right:
        st.markdown('<div class="section">Analyse automatique</div>',unsafe_allow_html=True)
        st.markdown('<div class="copy">Aucune correction manuelle : la pièce est analysée puis mémorisée dans le dressing.</div>',unsafe_allow_html=True)
        if uploaded and st.button("Ajouter au dressing",type="primary",use_container_width=True):
            path=save_upload(uploaded)
            with st.spinner("Détourage et reconnaissance…"):
                try:
                    result=analyze_and_save(str(path))
                    st.cache_data.clear(); clear_tryon()
                    st.success("Vêtement ajouté au dressing.")
                    if result: st.write(result)
                except Exception as e: st.error(f"L’analyse a échoué : {e}")
