"""
Sprint 4 - Generateur de rapport PDF hebdomadaire
Utilise reportlab pour produire un rapport professionnel.
"""

from pathlib import Path
from datetime import datetime
import numpy as np

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


# ── Palette ───────────────────────────────────────────────────────────────────


if HAS_REPORTLAB:
    C_PRIMARY   = colors.HexColor("#6366F1")
    C_SUCCESS   = colors.HexColor("#10B981")
    C_WARNING   = colors.HexColor("#F59E0B")
    C_DANGER    = colors.HexColor("#EF4444")
    C_DARK      = colors.HexColor("#111827")
    C_GRAY      = colors.HexColor("#6B7280")
    C_LIGHT     = colors.HexColor("#F9FAFB")
    C_BORDER    = colors.HexColor("#E5E7EB")
    C_BG        = colors.HexColor("#F3F4F6")


def _score_color(score):
    if score >= 75: return C_SUCCESS
    if score >= 50: return C_WARNING
    return C_DANGER


def _score_label(score):
    if score >= 75: return "Excellent"
    if score >= 50: return "A ameliorer"
    return "Insuffisant"


def generate_pdf_report(patient_name, exercise_name, week_number,
                        sessions, scores_history, output_path="rapport_hebdomadaire.pdf"):
    """
    Genere un rapport PDF hebdomadaire.

    patient_name   : str
    exercise_name  : str
    week_number    : int
    sessions       : list de dicts (historique all_sessions)
    scores_history : list de floats (scores de la derniere session)
    output_path    : str, chemin du fichier PDF
    """
    if not HAS_REPORTLAB:
        return None, "reportlab non installe. Lancez : pip install reportlab"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()

    S_TITLE = ParagraphStyle("title",
        fontSize=22, fontName="Helvetica-Bold",
        textColor=C_DARK, spaceAfter=4, leading=26)
    S_SUBTITLE = ParagraphStyle("subtitle",
        fontSize=12, fontName="Helvetica",
        textColor=C_GRAY, spaceAfter=16)
    S_SECTION = ParagraphStyle("section",
        fontSize=13, fontName="Helvetica-Bold",
        textColor=C_PRIMARY, spaceBefore=16, spaceAfter=8)
    S_BODY = ParagraphStyle("body",
        fontSize=10, fontName="Helvetica",
        textColor=C_DARK, leading=16, spaceAfter=4)
    S_SMALL = ParagraphStyle("small",
        fontSize=9, fontName="Helvetica",
        textColor=C_GRAY, spaceAfter=2)
    S_CENTER = ParagraphStyle("center",
        fontSize=10, fontName="Helvetica",
        textColor=C_DARK, alignment=TA_CENTER)

    story = []

    # ── En-tete ──────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("🦴 Kine Assistant", ParagraphStyle("h",
            fontSize=16, fontName="Helvetica-Bold", textColor=C_PRIMARY)),
        Paragraph(f"Rapport hebdomadaire — Semaine {week_number}<br/>"
                  f"<font size=9 color='#6B7280'>{datetime.now().strftime('%d/%m/%Y')}</font>",
                  ParagraphStyle("hr", fontSize=12, fontName="Helvetica",
                                 textColor=C_DARK, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[9*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 1.5, C_PRIMARY),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Info patient ─────────────────────────────────────────────────────────
    story.append(Paragraph("Informations patient", S_SECTION))
    info_data = [
        ["Patient",    patient_name,  "Exercice",  exercise_name],
        ["Semaine",    f"Semaine {week_number}", "Date",  datetime.now().strftime("%d/%m/%Y")],
    ]
    info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("TEXTCOLOR", (0,0), (0,-1), C_GRAY),
        ("TEXTCOLOR", (2,0), (2,-1), C_GRAY),
        ("BACKGROUND",(0,0), (-1,-1), C_BG),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_BG, C_LIGHT]),
        ("GRID",      (0,0), (-1,-1), 0.5, C_BORDER),
        ("PADDING",   (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(info_table)

    # ── Stats session ────────────────────────────────────────────────────────
    story.append(Paragraph("Resume de la derniere session", S_SECTION))

    if scores_history:
        arr  = np.array(scores_history)
        mean = float(np.mean(arr))
        best = float(np.max(arr))
        worst= float(np.min(arr))
        trend= "Amelioration" if len(arr) > 2 and arr[-1] > arr[0] else "Stable"
        n    = len(arr)

        kpi_data = [[
            Paragraph(f"<b>{n}</b><br/><font size=9 color='#6B7280'>Repetitions</font>", S_CENTER),
            Paragraph(f"<b>{mean:.0f}/100</b><br/><font size=9 color='#6B7280'>Score moyen</font>", S_CENTER),
            Paragraph(f"<b>{best:.0f}/100</b><br/><font size=9 color='#6B7280'>Meilleur</font>", S_CENTER),
            Paragraph(f"<b>{worst:.0f}/100</b><br/><font size=9 color='#6B7280'>Pire</font>", S_CENTER),
            Paragraph(f"<b>{trend}</b><br/><font size=9 color='#6B7280'>Tendance</font>", S_CENTER),
        ]]
        kpi_table = Table(kpi_data, colWidths=[3.4*cm]*5)
        kpi_table.setStyle(TableStyle([
            ("BOX",       (0,0), (-1,-1), 0.5, C_BORDER),
            ("INNERGRID", (0,0), (-1,-1), 0.5, C_BORDER),
            ("BACKGROUND",(0,0), (-1,-1), C_BG),
            ("PADDING",   (0,0), (-1,-1), 12),
            ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
            ("ALIGN",     (0,0), (-1,-1), "CENTER"),
            ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 0.4*cm))

        # Scores par rep
        story.append(Paragraph("Detail des repetitions", S_SECTION))
        rep_rows = [["Rep", "Score", "Evaluation", "Ecart cible"]]
        for i, s in enumerate(scores_history, 1):
            ecart = abs(s - 100)
            rep_rows.append([
                str(i),
                f"{s:.0f}/100",
                _score_label(s),
                f"-{ecart:.0f} pts",
            ])

        rep_table = Table(rep_rows, colWidths=[2*cm, 3.5*cm, 5*cm, 4.5*cm])
        ts = [
            ("FONTNAME",   (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",   (0,0), (-1,-1), 10),
            ("BACKGROUND", (0,0), (-1,0),  C_PRIMARY),
            ("TEXTCOLOR",  (0,0), (-1,0),  colors.white),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_LIGHT, C_BG]),
            ("GRID",       (0,0), (-1,-1), 0.5, C_BORDER),
            ("PADDING",    (0,0), (-1,-1), 8),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ]
        for i, s in enumerate(scores_history, 1):
            col = _score_color(s)
            ts.append(("TEXTCOLOR", (1,i), (2,i), col))
        rep_table.setStyle(TableStyle(ts))
        story.append(rep_table)

    else:
        story.append(Paragraph("Aucune repetition enregistree pour cette session.", S_BODY))

    # ── Historique sessions ──────────────────────────────────────────────────
    if sessions:
        story.append(Paragraph("Historique des sessions", S_SECTION))
        hist_rows = [["Session", "Exercice", "Semaine", "Score moy.", "Meilleur", "Tendance"]]
        for i, sess in enumerate(sessions[-8:], 1):
            hist_rows.append([
                str(i),
                sess.get("exercise", "--")[:20],
                f"S{sess.get('week','-')}",
                f"{sess.get('mean',0):.0f}/100",
                f"{sess.get('best',0):.0f}/100",
                sess.get("trend", "--").capitalize(),
            ])
        hist_table = Table(hist_rows, colWidths=[1.5*cm, 5*cm, 2*cm, 3*cm, 3*cm, 3.5*cm])
        hist_table.setStyle(TableStyle([
            ("FONTNAME",   (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("BACKGROUND", (0,0), (-1,0),  C_PRIMARY),
            ("TEXTCOLOR",  (0,0), (-1,0),  colors.white),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_LIGHT, C_BG]),
            ("GRID",       (0,0), (-1,-1), 0.5, C_BORDER),
            ("PADDING",    (0,0), (-1,-1), 7),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(hist_table)

    # ── Recommandations ──────────────────────────────────────────────────────
    story.append(Paragraph("Recommandations pour la semaine suivante", S_SECTION))

    if scores_history:
        mean = float(np.mean(scores_history))
        if mean >= 75:
            reco = [
                "Progression excellente. Augmentez progressivement le nombre de repetitions (+2).",
                "Vous pouvez passer a la semaine suivante du protocole si votre kinesitherapeute valide.",
                "Continuez la seance quotidienne en maintenant cette qualite d'execution.",
            ]
        elif mean >= 50:
            reco = [
                "Progression correcte. Maintenez le meme nombre de repetitions cette semaine.",
                "Concentrez-vous sur la qualite du mouvement plutot que la quantite.",
                "Revoyez le protocole de la semaine en cours avec votre kinesitherapeute.",
            ]
        else:
            reco = [
                "Des difficultes ont ete detectees. Reduisez l'amplitude des mouvements.",
                "Consultez votre kinesitherapeute avant de poursuivre.",
                "Appliquez de la glace 15 minutes apres chaque seance si douleur.",
            ]
        for r in reco:
            story.append(Paragraph(f"• {r}", S_BODY))
    else:
        story.append(Paragraph("Completez une session pour recevoir des recommandations.", S_BODY))

    # ── Pied de page ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Ce rapport est un outil d'accompagnement et ne remplace pas l'avis medical de votre kinesitherapeute. "
        "Genere automatiquement par Kine Assistant.",
        S_SMALL
    ))

    doc.build(story)
    return output_path, None