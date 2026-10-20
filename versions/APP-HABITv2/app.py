from pathlib import Path
import sqlite3, time
import threading
import streamlit as st

from backend.services.wardrobe_pipeline import analyze_and_save
from backend.services.outfit_recommender import recommend_outfits
from backend.services.context_service import get_context
from backend.services.fashn_tryon import fashn_available, generate_outfit_tryon
from ui.styles import apply_styles
from ui.geolocation import request_location
from ui.components import (
    pick,
    piece_card,
    weather_text,
    outfit_piece,
    outfit_signature,
    abs_path,
)

APP_ROOT = Path(__file__).resolve().parent
DB_PATH = APP_ROOT / "backend/database/wardrobe.db"
UPLOAD_DIR = APP_ROOT / "backend/storage/originals"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="APP-Habit",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_styles()


# =========================================================
# DRESSING
# =========================================================

def load_wardrobe():
    if not DB_PATH.exists():
        return []

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]

        if not tables:
            return []

        table = next(
            (
                t
                for t in tables
                if t.lower() in {"wardrobe", "clothes", "garments", "items"}
            ),
            tables[0],
        )

        return [
            dict(r)
            for r in con.execute(
                f'SELECT * FROM "{table}" ORDER BY rowid DESC'
            )
        ]

    finally:
        con.close()


# =========================================================
# CONTEXTE
# =========================================================

@st.cache_data(ttl=300, show_spinner=False)
def current_context(latitude, longitude):
    return get_context(
        latitude=latitude,
        longitude=longitude,
    )


# =========================================================
# TRY-ON
# =========================================================

@st.cache_resource
def get_tryon_lock():
    # Un seul appel FASHN peut être lancé par Streamlit à la fois.
    return threading.Lock()


def clear_tryon():
    for k in list(st.session_state):
        if str(k).startswith("fashn_tryon_"):
            del st.session_state[k]


# =========================================================
# UPLOAD
# =========================================================

def save_upload(u):
    p = (
        UPLOAD_DIR
        / f"upload_{time.time_ns()}"
          f"{Path(u.name).suffix.lower() or '.jpg'}"
    )

    p.write_bytes(u.getbuffer())
    return p


# =========================================================
# SUPPRESSION VÊTEMENT
# =========================================================

def delete_clothing(item):
    """Supprime un vêtement de la base et ses images locales."""

    clothing_id = item.get("id")

    if clothing_id is None:
        raise ValueError("Identifiant du vêtement introuvable.")

    con = sqlite3.connect(DB_PATH)

    try:
        con.execute(
            "DELETE FROM clothes WHERE id = ?",
            (clothing_id,),
        )
        con.commit()

    finally:
        con.close()

    # Supprime les fichiers associés.
    for field in ("original_path", "cutout_path"):
        raw_path = item.get(field)

        if not raw_path:
            continue

        file_path = Path(str(raw_path))

        if not file_path.is_absolute():
            file_path = APP_ROOT / file_path

        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()

        except OSError:
            pass

    # Invalidation immédiate.
    st.cache_data.clear()
    clear_tryon()

    # Supprime également la signature du look actuel.
    st.session_state.pop(
        "current_outfit_signature",
        None,
    )

    st.session_state["wardrobe_changed"] = True


# =========================================================
# NAVIGATION
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Looks"

brand_col, looks_col, dressing_col, add_col = st.columns(
    [1.7, 1, 1, 1],
    vertical_alignment="center",
    gap="small",
)

with brand_col:
    st.markdown(
        '<div class="brand">APP•Habit</div>',
        unsafe_allow_html=True,
    )

for col, name in zip(
    (looks_col, dressing_col, add_col),
    ("Looks", "Dressing", "Ajouter"),
):
    with col:
        if st.button(
            name,
            key=f"nav_{name.lower()}",
            use_container_width=True,
            type="primary" if name == "Looks" else "secondary",
        ):
            st.session_state.page = name
            st.rerun()

st.divider()


# =========================================================
# INVALIDATION APRÈS MODIFICATION DU DRESSING
# =========================================================

if st.session_state.pop("wardrobe_changed", False):
    st.cache_data.clear()
    clear_tryon()

    st.session_state.pop(
        "current_outfit_signature",
        None,
    )


wardrobe = load_wardrobe()


# =========================================================
# PAGE LOOKS
# =========================================================

if st.session_state.page == "Looks":

    location = st.session_state.get("user_location")

    if not location:
        geo = request_location()

        if geo and geo.get("status") == "success":
            st.session_state.user_location = {
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
            }

            st.rerun()

    location = st.session_state.get("user_location")

    # -----------------------------------------------------
    # MÉTÉO
    # -----------------------------------------------------

    if location:

        context = current_context(
            location["latitude"],
            location["longitude"],
        )

    else:

        # Mode sans localisation.
        from datetime import datetime

        month = datetime.now().month

        if month in (12, 1, 2):
            fallback_season = "hiver"

        elif month in (3, 4, 5):
            fallback_season = "printemps"

        elif month in (6, 7, 8):
            fallback_season = "été"

        else:
            fallback_season = "automne"

        context = {
            "saison": fallback_season,
            "meteo": {
                "temperature": 20.0,
                "temperature_ressentie": 20.0,
                "weather_code": 0,
                "pluie": 0.0,
                "precipitations": 0.0,
                "vent": 0.0,
            },
        }

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    st.markdown(
        '<div class="title">'
        'Vos looks, avec vos vêtements.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-copy">'
        'Une tenue composée automatiquement à partir '
        'de votre dressing et du contexte météo.'
        '</div>',
        unsafe_allow_html=True,
    )

    season = pick(
        context,
        "season",
        "saison",
        default="Automne",
    )

    meteo = (
        context.get("meteo", {})
        if isinstance(context, dict)
        else {}
    )

    temperature = meteo.get("temperature")
    temperature_ressentie = meteo.get(
        "temperature_ressentie"
    )
    weather_code = meteo.get("weather_code")

    WEATHER_LABELS = {
        0: "Ciel dégagé",
        1: "Plutôt dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine",
        55: "Bruine forte",
        61: "Pluie légère",
        63: "Pluie",
        65: "Forte pluie",
        71: "Neige légère",
        73: "Neige",
        75: "Forte neige",
        80: "Averses légères",
        81: "Averses",
        82: "Fortes averses",
        95: "Orage",
        96: "Orage avec grêle",
        99: "Fort orage avec grêle",
    }

    if temperature is not None:

        condition = WEATHER_LABELS.get(
            weather_code,
            "Météo locale",
        )

        weather_label = (
            f"{float(temperature):.0f}°C · "
            f"{condition}"
        )

    elif location:

        weather_label = "Météo indisponible"

    else:

        weather_label = "Localisation requise"

    st.markdown(
        f"""
        <div class="context-row">
            <span class="pill season-pill">
                {season}
            </span>
            <span class="weather-pill">
                {weather_label}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # -----------------------------------------------------
    # RECOMMANDATION
    # -----------------------------------------------------

    if not wardrobe:

        st.info(
            "Ton dressing est vide. "
            "Ajoute d’abord quelques vêtements."
        )

        outfits = []

    else:

        try:

            outfits = list(
                recommend_outfits(
                    context=context,
                    limit=1,
                )
                or []
            )[:1]

        except Exception as e:

            st.error(
                f"Impossible de calculer les looks : {e}"
            )

            outfits = []

    # -----------------------------------------------------
    # AFFICHAGE LOOK
    # -----------------------------------------------------

    for i, outfit in enumerate(outfits, 1):

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:.65rem;margin:.3rem 0 .7rem;">'
            f'<span class="section" style="margin:0;">Look {i:02d}</span>'
            f'<span style="font-size:.68rem;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;color:#74716A;border:1px solid #DEDAD1;'
            f'border-radius:999px;padding:.30rem .55rem;">Sélection du jour</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        visual, details = st.columns(
            [.62, .38],
            gap="large",
        )

        # =================================================
        # SIGNATURE DU LOOK
        # =================================================

        signature = outfit_signature(
            outfit,
            i,
        )

        key = f"fashn_tryon_{signature}"

        previous_signature = st.session_state.get(
            "current_outfit_signature"
        )

        # Si le look recommandé change :
        # suppression automatique de l'ancien try-on.
        if previous_signature != signature:

            clear_tryon()

            st.session_state[
                "current_outfit_signature"
            ] = signature

        # =================================================
        # GÉNÉRATION FASHN
        # =================================================

        with visual:

            cached = abs_path(
                st.session_state.get(key)
            )

            if cached:

                st.image(
                    str(cached),
                    use_container_width=True,
                )

            elif fashn_available():

                with st.spinner(
                    f"Génération du look {i}…"
                ):

                    try:
                        tryon_lock = get_tryon_lock()

                        with tryon_lock:

                            # Un rerun Streamlit peut avoir attendu ici.
                            # On vérifie donc une seconde fois si le look
                            # vient d'être généré.
                            cached_after_wait = abs_path(
                                st.session_state.get(key)
                            )

                            if cached_after_wait:
                                gp = cached_after_wait

                            else:
                                generated = generate_outfit_tryon(
                                    outfit
                                )

                                gp = abs_path(generated)

                                if gp:
                                    st.session_state[key] = str(gp)

                        if gp:
                            st.image(
                                str(gp),
                                use_container_width=True,
                            )
                        else:
                            st.info(
                                "Aperçu IA non disponible."
                            )

                    except Exception as e:

                        st.info(
                            "Aperçu IA non disponible : "
                            f"{e}"
                        )

            else:

                ref = (
                    APP_ROOT
                    / "backend/storage/person/reference.png"
                )

                if ref.exists():

                    st.image(
                        str(ref),
                        use_container_width=True,
                    )

                st.caption(
                    "Le moteur d’essayage local "
                    "n’est pas démarré."
                )

        # =================================================
        # PIÈCES DU LOOK
        # =================================================

        with details:

            st.markdown(
                '<div class="kicker">'
                'Pièces utilisées'
                '</div>',
                unsafe_allow_html=True,
            )

            top = outfit_piece(
                outfit,
                "top",
            )

            bottom = outfit_piece(
                outfit,
                "bottom",
            )

            shoes = outfit_piece(
                outfit,
                "shoes",
            )

            pieces = [
                ("Haut", top),
                ("Bas", bottom),
                ("Chaussures", shoes),
            ]

            pieces = [
                (title, item)
                for title, item in pieces
                if item
            ]

            if pieces:

                cols = st.columns(
                    len(pieces),
                    gap="small",
                )

                for col, (title, item) in zip(
                    cols,
                    pieces,
                ):

                    with col:

                        st.caption(title)
                        piece_card(item)

            outerwear = outfit_piece(
                outfit,
                "outerwear",
            )

            if outerwear:

                st.caption("Extérieur")
                piece_card(outerwear)

        st.divider()


# =========================================================
# PAGE DRESSING
# =========================================================

elif st.session_state.page == "Dressing":

    st.markdown(
        '<div class="kicker">'
        'Votre collection'
        '</div>'
        '<div class="title">'
        'Dressing.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="copy">'
        f'{len(wardrobe)} pièce(s) enregistrée(s). '
        'Les vêtements déjà analysés restent '
        'disponibles sans nouvelle analyse.'
        '</div>',
        unsafe_allow_html=True,
    )

    cats = sorted(
        {
            str(
                pick(
                    x,
                    "category",
                    "categorie",
                    default="",
                )
            ).strip()
            for x in wardrobe
            if pick(
                x,
                "category",
                "categorie",
            )
        }
    )

    selected = st.segmented_control(
        "Catégorie",
        ["Tout"] + cats,
        default="Tout",
        label_visibility="collapsed",
    )

    shown = (
        wardrobe
        if selected in (None, "Tout")
        else [
            x
            for x in wardrobe
            if str(
                pick(
                    x,
                    "category",
                    "categorie",
                    default="",
                )
            )
            == selected
        ]
    )

    cols = st.columns(
        4,
        gap="medium",
    )

    for i, item in enumerate(shown):

        with cols[i % 4]:

            with st.container(border=True):

                piece_card(item)

                clothing_id = item.get("id")

                if st.button(
                    "Supprimer",
                    key=f"delete_clothing_{clothing_id}",
                    use_container_width=True,
                ):

                    try:

                        delete_clothing(item)
                        st.rerun()

                    except Exception:

                        st.error(
                            "Impossible de supprimer "
                            "ce vêtement."
                        )


# =========================================================
# PAGE AJOUTER
# =========================================================

else:

    st.markdown(
        '<div class="title add-title">'
        'Ajouter un vêtement.'
        '</div>'
        '<div class="copy add-copy">'
        'Importez une ou plusieurs photos. '
        'APP-Habit détoure, reconnaît et classe '
        'automatiquement chaque pièce.'
        '</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [.56, .44],
        gap="large",
    )

    # -----------------------------------------------------
    # UPLOAD
    # -----------------------------------------------------

    with left:

        uploaded_files = st.file_uploader(
            "Photo du vêtement",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files:

            if len(uploaded_files) == 1:

                st.image(
                    uploaded_files[0],
                    use_container_width=True,
                )

            else:

                preview_cols = st.columns(3)

                for i, uploaded in enumerate(
                    uploaded_files
                ):

                    with preview_cols[i % 3]:

                        st.image(
                            uploaded,
                            use_container_width=True,
                        )

    # -----------------------------------------------------
    # ANALYSE
    # -----------------------------------------------------

    with right:

        st.markdown(
            '<div class="section">'
            'Analyse automatique'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="copy">'
            'Aucune correction manuelle : '
            'chaque pièce est analysée puis '
            'mémorisée dans le dressing.'
            '</div>',
            unsafe_allow_html=True,
        )

        if uploaded_files:

            count = len(uploaded_files)

            button_text = (
                "Ajouter au dressing"
                if count == 1
                else f"Ajouter les {count} vêtements"
            )

            if st.button(
                button_text,
                type="primary",
                use_container_width=True,
            ):

                progress = st.progress(0)
                status = st.empty()

                success_count = 0
                errors = []

                # =========================================
                # TRAITEMENT DE CHAQUE IMAGE
                # =========================================

                for i, uploaded in enumerate(
                    uploaded_files,
                    start=1,
                ):

                    status.write(
                        f"Analyse du vêtement "
                        f"{i}/{count} : "
                        f"{uploaded.name}"
                    )

                    try:

                        path = save_upload(
                            uploaded
                        )

                        analyze_and_save(
                            str(path)
                        )

                        success_count += 1

                    except Exception as e:

                        errors.append(
                            f"{uploaded.name} : {e}"
                        )

                    progress.progress(
                        i / count
                    )

                # =========================================
                # INVALIDATION APRÈS AJOUT
                # =========================================

                st.cache_data.clear()

                clear_tryon()

                st.session_state[
                    "wardrobe_changed"
                ] = True

                st.session_state.pop(
                    "current_outfit_signature",
                    None,
                )

                status.empty()
                progress.empty()

                # =========================================
                # RÉSULTAT
                # =========================================

                if success_count:

                    st.success(
                        f"{success_count} vêtement(s) "
                        "ajouté(s) au dressing."
                    )

                for error in errors:

                    st.error(error)