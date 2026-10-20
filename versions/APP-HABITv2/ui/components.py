from pathlib import Path
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]

def pick(obj, *keys, default=None):
    if obj is None: return default
    if isinstance(obj, dict):
        for k in keys:
            if obj.get(k) not in (None, ""): return obj[k]
    for k in keys:
        try:
            v = getattr(obj, k)
            if v not in (None, ""): return v
        except Exception: pass
    return default

def abs_path(value):
    if not value: return None
    p = Path(str(value))
    if not p.is_absolute(): p = APP_ROOT / p
    p = p.resolve()
    return p if p.exists() else None

def garment_id(x): return pick(x, "id", "garment_id", default="x")
def garment_name(x): return str(pick(x, "type", "label", "name", "clothing_type", default="Vêtement"))

def piece_card(x):
    p = abs_path(pick(x, "cutout_path", "processed_path", "image_path", "path", "original_path"))
    if p: st.image(str(p), use_container_width=True)
    st.markdown(f'<div class="piece">{garment_name(x)}</div>', unsafe_allow_html=True)
    cat = str(pick(x, "category", "categorie", default=""))
    col = str(pick(x, "color", "couleur", default=""))
    meta = " · ".join(v for v in (cat, col) if v)
    if meta: st.markdown(f'<div class="piece-meta">{meta}</div>', unsafe_allow_html=True)

def outfit_piece(outfit, role):
    aliases = {"top":("top","haut"),"bottom":("bottom","bas"),
               "shoes":("shoes","chaussures","shoe"),
               "outerwear":("outerwear","exterieur","exterior","jacket")}
    return pick(outfit, *aliases[role])

def outfit_signature(outfit, n):
    return "_".join(map(str,[n]+[garment_id(outfit_piece(outfit,r)) if outfit_piece(outfit,r) else "-" for r in ("top","bottom","shoes","outerwear")]))

def weather_text(c):
    if not c: return "Contexte météo indisponible"
    t=pick(c,"temperature","temperature_c","temp")
    w=pick(c,"weather","condition","description",default="")
    s=pick(c,"season","saison",default="")
    bits=[]
    if t is not None:
        try: bits.append(f"{float(t):.0f}°C")
        except: bits.append(str(t))
    if w: bits.append(str(w))
    if s: bits.append(str(s))
    return " · ".join(bits) or "Météo actualisée"
