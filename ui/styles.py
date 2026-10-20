import streamlit as st


def apply_styles():
    st.markdown("""
<style>

/* =========================================================
   APP-HABIT — CHARTE GRAPHIQUE
   ========================================================= */

:root {
    --bg: #F5F2EA;
    --card: #FCFBF7;
    --ink: #111111;
    --muted: #74716A;
    --line: #DEDAD1;
}

/* TYPO GLOBALE */

html,
body,
.stApp,
.stApp button,
.stApp input,
.stApp textarea,
.stApp select,
.stApp p,
.stApp span,
.stApp div {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important;
}

.stApp {
    background: var(--bg);
    color: var(--ink);
}

.block-container {
    max-width: 1380px;
    padding-top: 1.1rem;
    padding-bottom: 3rem;
}


/* =========================================================
   MASQUER L'INTERFACE STREAMLIT
   ========================================================= */

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"],
[data-testid="stDeployButton"],
.stDeployButton,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
button[title="Deploy"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}


/* =========================================================
   MARQUE
   ========================================================= */

.brand {
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -.04em;
    color: var(--ink);
}


/* =========================================================
   NAVIGATION
   ========================================================= */

/* On ne touche PAS aux colonnes ni au layout */

div[data-testid="stButton"] button {
    border-radius: 999px !important;
    min-height: 2.55rem !important;
    font-weight: 650 !important;
}

/* Texte blanc, y compris les boutons secondaires */

div[data-testid="stButton"] button,
div[data-testid="stButton"] button *,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
div[data-testid="stButton"] button div {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}


/* =========================================================
   TYPOGRAPHIE CONTENU
   ========================================================= */

.kicker {
    color: var(--muted);
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .12em;
}

.title {
    font-size: clamp(2.2rem, 5vw, 4.8rem);
    line-height: .94;
    font-weight: 800;
    letter-spacing: -.065em;
    margin: .2rem 0 .7rem;
}

.hero-copy,
.copy {
    max-width: 760px;
    color: var(--ink);
    font-size: .98rem;
    margin-bottom: 1.2rem;
}

.section {
    font-size: 1.35rem;
    font-weight: 750;
    letter-spacing: -.035em;
    margin: .3rem 0 .7rem;
}

.meta {
    color: var(--muted);
    font-size: .82rem;
}


/* =========================================================
   CONTEXTE / MÉTÉO
   ========================================================= */

.context-row {
    display: flex;
    align-items: center;
    gap: .55rem;
    flex-wrap: wrap;
}

.pill,
.weather-pill {
    display: inline-flex;
    align-items: center;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: rgba(255,255,255,.5);
    padding: .42rem .72rem;
    font-size: .78rem;
}


/* =========================================================
   VÊTEMENTS
   ========================================================= */

.piece {
    font-size: .86rem;
    font-weight: 650;
    margin-top: .35rem;
}

.piece-meta {
    font-size: .74rem;
    color: var(--muted);
}

div[data-testid="stImage"] img {
    border-radius: 14px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(252,251,247,.72);
    border-radius: 18px;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 780px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .title {
        font-size: 2.6rem;
    }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# APP-HABIT — TITRE LARGE + NAVIGATION ACTIVE
# =========================================================

st.markdown("""
<style>

/* ---------------------------------------------------------
   TITRE : exploite toute la largeur disponible
   --------------------------------------------------------- */

.title {
    width: 100% !important;
    max-width: none !important;

    font-size: clamp(3.8rem, 6.2vw, 6.7rem) !important;
    line-height: .90 !important;
    letter-spacing: -.07em !important;

    white-space: nowrap !important;
}

/* Le <br> présent dans app.py ne coupe plus le titre */
.title br {
    display: none !important;
}


/* ---------------------------------------------------------
   NAVIGATION

   - bouton actif Looks = rouge
   - Dressing = noir
   - Ajouter = noir
   - texte toujours blanc
   --------------------------------------------------------- */

/* Tous les boutons navigation en noir par défaut */

div[data-testid="stButton"] button {
    background: #12151D !important;
    border-color: #12151D !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button *,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}


/* Uniquement Looks actif en rouge */

div[data-testid="stButton"]:has(
    button[kind="primary"][aria-label="Looks"]
) button {
    background: #FF4D52 !important;
    border-color: #FF4D52 !important;
}


/* Fallback Streamlit : premier bouton de navigation actif */

div[data-testid="stHorizontalBlock"]
> div:nth-child(2)
div[data-testid="stButton"]
button[kind="primary"] {
    background: #FF4D52 !important;
    border-color: #FF4D52 !important;
}


/* Dressing/Ajouter actifs restent noirs */

div[data-testid="stHorizontalBlock"]
> div:nth-child(3)
div[data-testid="stButton"]
button[kind="primary"],

div[data-testid="stHorizontalBlock"]
> div:nth-child(4)
div[data-testid="stButton"]
button[kind="primary"] {
    background: #12151D !important;
    border-color: #12151D !important;
}


/* Mobile : autoriser le titre à revenir sur plusieurs lignes */

@media (max-width: 900px) {
    .title {
        white-space: normal !important;
        font-size: clamp(3rem, 10vw, 5rem) !important;
    }

    .title br {
        display: initial !important;
    }
}

</style>
""", unsafe_allow_html=True)


# Navigation APP-Habit : Looks rouge, autres noirs
st.markdown("""
<style>

/* Dressing + Ajouter : toujours noirs */
div[data-testid="stButton"] button[kind="secondary"] {
    background: #12151D !important;
    background-color: #12151D !important;
    border-color: #12151D !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stButton"] button[kind="secondary"]:focus,
div[data-testid="stButton"] button[kind="secondary"]:active {
    background: #12151D !important;
    background-color: #12151D !important;
    border-color: #12151D !important;
    color: #FFFFFF !important;
}

div[data-testid="stButton"] button[kind="secondary"] *,
div[data-testid="stButton"] button[kind="secondary"] p,
div[data-testid="stButton"] button[kind="secondary"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# NAVIGATION — SUPPRESSION DU HOVER BLANC STREAMLIT
# =========================================================

st.markdown("""
<style>

/* Boutons secondaires : noir dans TOUS les états */
div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stButton"] button[kind="secondary"]:focus,
div[data-testid="stButton"] button[kind="secondary"]:focus-visible,
div[data-testid="stButton"] button[kind="secondary"]:active,
div[data-testid="stButton"] button[kind="secondary"][aria-pressed="true"] {
    background: #12151D !important;
    background-color: #12151D !important;
    border: 1px solid #12151D !important;
    box-shadow: none !important;
    color: #FFFFFF !important;
}

/* Streamlit applique parfois le fond sur l'élément interne */
div[data-testid="stButton"] button[kind="secondary"] > div,
div[data-testid="stButton"] button[kind="secondary"]:hover > div,
div[data-testid="stButton"] button[kind="secondary"]:focus > div,
div[data-testid="stButton"] button[kind="secondary"]:active > div {
    background: transparent !important;
    background-color: transparent !important;
}

/* Texte toujours blanc */
div[data-testid="stButton"] button[kind="secondary"] *,
div[data-testid="stButton"] button[kind="secondary"]:hover *,
div[data-testid="stButton"] button[kind="secondary"]:focus *,
div[data-testid="stButton"] button[kind="secondary"]:active * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Désactive aussi l'effet de survol Streamlit */
div[data-testid="stButton"] button[kind="secondary"]:hover {
    filter: none !important;
    opacity: 1 !important;
    transform: none !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# NAVIGATION — SUPPRESSION DU HOVER BLANC STREAMLIT
# =========================================================

st.markdown("""
<style>

/* Boutons secondaires : noir dans TOUS les états */
div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stButton"] button[kind="secondary"]:focus,
div[data-testid="stButton"] button[kind="secondary"]:focus-visible,
div[data-testid="stButton"] button[kind="secondary"]:active,
div[data-testid="stButton"] button[kind="secondary"][aria-pressed="true"] {
    background: #12151D !important;
    background-color: #12151D !important;
    border: 1px solid #12151D !important;
    box-shadow: none !important;
    color: #FFFFFF !important;
}

/* Streamlit applique parfois le fond sur l'élément interne */
div[data-testid="stButton"] button[kind="secondary"] > div,
div[data-testid="stButton"] button[kind="secondary"]:hover > div,
div[data-testid="stButton"] button[kind="secondary"]:focus > div,
div[data-testid="stButton"] button[kind="secondary"]:active > div {
    background: transparent !important;
    background-color: transparent !important;
}

/* Texte toujours blanc */
div[data-testid="stButton"] button[kind="secondary"] *,
div[data-testid="stButton"] button[kind="secondary"]:hover *,
div[data-testid="stButton"] button[kind="secondary"]:focus *,
div[data-testid="stButton"] button[kind="secondary"]:active * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Désactive aussi l'effet de survol Streamlit */
div[data-testid="stButton"] button[kind="secondary"]:hover {
    filter: none !important;
    opacity: 1 !important;
    transform: none !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# AJOUTER — UPLOAD MINIMAL
# =========================================================

st.markdown("""
<style>

/* Masque le texte "Photo du vêtement" */
div[data-testid="stFileUploader"] label {
    display: none !important;
}

/* Zone upload compacte */
div[data-testid="stFileUploader"] section {
    min-height: 46px !important;
    height: 46px !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

/* Masque instructions, nom du fichier, taille, etc. */
div[data-testid="stFileUploader"] section > div {
    display: none !important;
}

div[data-testid="stFileUploaderFile"] {
    display: none !important;
}

/* Le bouton natif devient notre bouton Ajouter */
div[data-testid="stFileUploader"] button {
    width: 100% !important;
    min-height: 46px !important;

    background: #12151D !important;
    border: 1px solid #12151D !important;
    border-radius: 999px !important;

    color: white !important;
    font-weight: 650 !important;
}

/* Texte du bouton */
div[data-testid="stFileUploader"] button *,
div[data-testid="stFileUploader"] button:hover *,
div[data-testid="stFileUploader"] button:focus * {
    color: white !important;
    -webkit-text-fill-color: white !important;
}

/* Aucun changement au survol */
div[data-testid="stFileUploader"] button:hover,
div[data-testid="stFileUploader"] button:focus,
div[data-testid="stFileUploader"] button:active {
    background: #12151D !important;
    border-color: #12151D !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# FILE UPLOADER — bouton "Ajouter"
# =========================================================
st.markdown("""
<style>

/* Bouton du sélecteur de fichier */
div[data-testid="stFileUploader"] button {
    font-size: 0 !important;
    background: #12151D !important;
    background-color: #12151D !important;
    border: 1px solid #12151D !important;
    color: transparent !important;
    min-width: 105px !important;
}

/* Nouveau texte */
div[data-testid="stFileUploader"] button::after {
    content: "Ajouter";
    font-size: 14px !important;
    font-weight: 650 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Hover */
div[data-testid="stFileUploader"] button:hover,
div[data-testid="stFileUploader"] button:focus,
div[data-testid="stFileUploader"] button:active {
    background: #12151D !important;
    background-color: #12151D !important;
    border-color: #12151D !important;
}

/* Masque "200MB per file • JPG, PNG, WEBP" */
div[data-testid="stFileUploader"] small {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# PAGE AJOUTER — TITRE COMPACT
# =========================================================
st.markdown("""
<style>

.add-title {
    font-size: clamp(3rem, 5vw, 4.6rem) !important;
    line-height: .95 !important;
    margin: 0 0 .7rem 0 !important;
}

.add-copy {
    font-size: 1rem !important;
    margin-bottom: 1.6rem !important;
    max-width: 760px !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# FILE UPLOADER — fichier gauche / Ajouter droite
# =========================================================
st.markdown("""
<style>

/* Barre de l'upload */
div[data-testid="stFileUploaderDropzone"] {
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    min-height: 66px !important;
    padding: 10px 14px !important;
}

/* Zone contenant le fichier sélectionné */
div[data-testid="stFileUploader"] ul {
    flex: 1 1 auto !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Bouton de sélection : complètement à droite */
div[data-testid="stFileUploaderDropzone"] button {
    position: absolute !important;
    right: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;

    width: 110px !important;
    min-width: 110px !important;

    background: #12151D !important;
    border: 1px solid #12151D !important;
    border-radius: 999px !important;

    font-size: 0 !important;
    color: transparent !important;
}

/* Texte du bouton */
div[data-testid="stFileUploaderDropzone"] button::after {
    content: "Ajouter" !important;
    font-size: 14px !important;
    font-weight: 650 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Garde de la place à droite pour le bouton */
div[data-testid="stFileUploaderDropzone"] > div {
    padding-right: 125px !important;
    width: 100% !important;
}

/* Pas de changement au hover */
div[data-testid="stFileUploaderDropzone"] button:hover,
div[data-testid="stFileUploaderDropzone"] button:focus,
div[data-testid="stFileUploaderDropzone"] button:active {
    background: #12151D !important;
    border-color: #12151D !important;
    transform: translateY(-50%) !important;
}

</style>
""", unsafe_allow_html=True)

