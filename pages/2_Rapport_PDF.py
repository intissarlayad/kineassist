"""
Page 3 : Generation du rapport PDF hebdomadaire
"""

import streamlit as st
import numpy as np
from pathlib import Path
from auth import require_auth
require_auth(allowed_roles=["kine", "patient"])  # ← accessible aux deux
st.set_page_config(page_title="Rapport PDF", page_icon="📄", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.info-box { background:#1A1D27; border:1px solid #2A2D3A; border-radius:10px; padding:14px 16px; margin:8px 0; font-size:13px; color:#D1D5DB; }
.section-title { font-size:12px; font-weight:500; color:#6B7280; text-transform:uppercase; letter-spacing:.06em; margin:16px 0 8px; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📄 Rapport PDF hebdomadaire")
st.markdown("<div style='color:#6B7280;font-size:13px;margin-bottom:20px'>Generez et telechargez le rapport de suivi pour votre kinesitherapeute</div>", unsafe_allow_html=True)

# ── Verif reportlab ────────────────────────────────────────────────────────────
try:
    from core.report_generator import generate_pdf_report
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

if not HAS_PDF:
    st.warning("reportlab n'est pas installe. Lancez : `pip install reportlab`")

# ── Formulaire ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Informations du rapport</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    patient_name  = st.text_input("Nom du patient", value="Mon Nom")
    week_number   = st.number_input("Semaine de reeducation", min_value=1, max_value=12, value=1)
with col2:
    exercise_name = st.selectbox("Exercice", ["Flexion du genou", "Elevation du bras", "Rotation du tronc"])
    output_name   = st.text_input("Nom du fichier", value="rapport_hebdomadaire.pdf")

st.markdown('<div class="section-title">Donnees de session</div>', unsafe_allow_html=True)

# Recuperer depuis session state si disponible
scores_from_session = st.session_state.get("scores_history", [])
sessions_from_state = st.session_state.get("all_sessions", [])

if scores_from_session:
    st.success(f"{len(scores_from_session)} repetitions chargees depuis la session en cours.")
    scores_display = scores_from_session
else:
    st.info("Aucune session en cours. Utilisation de donnees de demonstration.")
    scores_display = [72, 68, 75, 71, 78, 80, 74, 77, 82, 79]

# Apercu scores
st.markdown('<div class="section-title">Apercu des scores</div>', unsafe_allow_html=True)
arr = np.array(scores_display)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Repetitions",    len(arr))
c2.metric("Score moyen",    f"{np.mean(arr):.0f}/100")
c3.metric("Meilleur score", f"{np.max(arr):.0f}/100")
c4.metric("Pire score",     f"{np.min(arr):.0f}/100")

st.line_chart(
    {"Rep": list(range(1, len(arr)+1)), "Score": arr.tolist()},
    x="Rep", y="Score", use_container_width=True
)

st.markdown("---")

# ── Generation PDF ──────────────────────────────────────────────────────────────
if st.button("Generer le rapport PDF", type="primary", use_container_width=True):
    if not HAS_PDF:
        st.error("Installez reportlab d'abord : pip install reportlab")
    else:
        with st.spinner("Generation du rapport en cours..."):
            out_path = f"data/{output_name}"
            Path("data").mkdir(exist_ok=True)
            pdf_path, err = generate_pdf_report(
                patient_name  = patient_name,
                exercise_name = exercise_name,
                week_number   = week_number,
                sessions      = sessions_from_state,
                scores_history= scores_display,
                output_path   = out_path,
            )

        if err:
            st.error(f"Erreur : {err}")
        elif pdf_path and Path(pdf_path).exists():
            st.success("Rapport genere avec succes !")
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=f.read(),
                    file_name=output_name,
                    mime="application/pdf",
                    use_container_width=True,
                )

st.markdown("---")
st.markdown('<div class="info-box">Ce rapport est genere automatiquement a partir des donnees de session. Il est destine a etre partage avec votre kinesitherapeute. Il ne remplace pas un suivi medical.</div>', unsafe_allow_html=True)