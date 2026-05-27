"""
mailer.py — Envoi d'emails d'invitation via Gmail SMTP
=======================================================
Configuration via variables d'environnement :
  GMAIL_USER = votre.email@gmail.com
  GMAIL_PASS = votre_mot_de_passe_application

Pour générer un mot de passe d'application Gmail :
  1. Accédez à myaccount.google.com
  2. Sécurité > Validation en deux étapes (à activer)
  3. Sécurité > Mots de passe des applications
  4. Générez un mot de passe pour « Autre (nom personnalisé) »
  5. Copiez le code à 16 caractères — c'est votre GMAIL_PASS
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")
APP_URL     = os.getenv("APP_URL", "http://localhost:8501")


def send_invitation_email(
    patient_email: str,
    patient_nom: str,
    kine_nom: str,
    token: str,
) -> tuple[bool, str]:
    """
    Envoie un email d'invitation au patient.
    Retourne (success: bool, message: str).
    """
    if not GMAIL_USER or not GMAIL_PASS:
        return False, (
            "GMAIL_USER ou GMAIL_PASS non configuré "
            "dans les variables d'environnement."
        )

    activation_link = f"{APP_URL}?token={token}"
    subject = f"KineAssist — {kine_nom} vous invite à rejoindre votre espace de rééducation"

    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Invitation KineAssist</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      background-color: #F0F2F5;
      padding: 40px 16px;
      -webkit-font-smoothing: antialiased;
    }}

    .wrapper {{
      max-width: 520px;
      margin: 0 auto;
    }}

    /* ── Header ── */
    .header {{
      background-color: #0C2340;
      border-radius: 8px 8px 0 0;
      padding: 36px 40px 32px;
    }}

    .header-eyebrow {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }}

    .header-eyebrow span {{
      color: #7DA8D0;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-weight: 500;
    }}

    .header h1 {{
      color: #FFFFFF;
      font-size: 22px;
      font-weight: 500;
      line-height: 1.3;
      margin-bottom: 6px;
    }}

    .header p {{
      color: #7DA8D0;
      font-size: 13px;
    }}

    /* ── Body ── */
    .body {{
      background-color: #FFFFFF;
      padding: 36px 40px;
    }}

    .body p {{
      font-size: 15px;
      line-height: 1.75;
      color: #4B5563;
      margin-bottom: 16px;
    }}

    .body p strong {{
      font-weight: 500;
      color: #111827;
    }}

    /* ── CTA ── */
    .btn-wrapper {{
      margin: 28px 0;
    }}

    .btn {{
      display: inline-block;
      background-color: #0C2340;
      color: #FFFFFF;
      text-decoration: none;
      padding: 13px 32px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      letter-spacing: 0.02em;
    }}

    /* ── Note ── */
    .note {{
      border-left: 2px solid #D1D5DB;
      padding: 14px 16px;
      margin-top: 8px;
    }}

    .note p {{
      font-size: 13px;
      line-height: 1.65;
      color: #6B7280;
      margin-bottom: 6px;
    }}

    .note p:last-child {{
      margin-bottom: 0;
    }}

    .note strong {{
      font-weight: 500;
      color: #374151;
    }}

    /* ── Footer ── */
    .footer {{
      background-color: #FFFFFF;
      border-top: 1px solid #F3F4F6;
      border-radius: 0 0 8px 8px;
      padding: 18px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .footer span {{
      font-size: 12px;
      color: #9CA3AF;
    }}
  </style>
</head>
<body>
  <div class="wrapper">

    <div class="header">
      <div class="header-eyebrow">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="#7DA8D0" stroke-width="1.5" stroke-linecap="round"
             stroke-linejoin="round" aria-hidden="true">
          <path d="M18 20a6 6 0 0 0-12 0"/>
          <circle cx="12" cy="10" r="4"/>
        </svg>
        <span>KineAssist</span>
      </div>
      <h1>Votre espace de rééducation personnalisé</h1>
      <p>Plateforme de suivi kinésithérapique</p>
    </div>

    <div class="body">
      <p>Bonjour <strong>{patient_nom}</strong>,</p>
      <p>
        Votre kinésithérapeute, <strong>{kine_nom}</strong>, vous a créé un compte
        sur KineAssist afin d'assurer le suivi de votre rééducation.
      </p>
      <p>
        Cliquez sur le bouton ci-dessous pour définir votre mot de passe
        et accéder à votre espace personnel.
      </p>

      <div class="btn-wrapper">
        <a href="{activation_link}" class="btn">Activer mon compte</a>
      </div>

      <div class="note">
        <p>
          Ce lien est valable <strong>72 heures</strong>. Passé ce délai,
          veuillez contacter votre praticien pour un nouvel envoi.
        </p>
        <p>
          Pour votre sécurité, votre mot de passe ne sera jamais
          communiqué à votre praticien.
        </p>
      </div>
    </div>

    <div class="footer">
      <span>KineAssist — Suivi de rééducation</span>
      <span>Ne pas répondre à cet email</span>
    </div>

  </div>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = patient_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, patient_email, msg.as_string())

        return True, "Email envoyé avec succès."

    except smtplib.SMTPAuthenticationError:
        return False, (
            "Erreur d'authentification Gmail. "
            "Vérifiez GMAIL_USER et GMAIL_PASS (mot de passe d'application)."
        )
    except Exception as e:
        return False, f"Erreur lors de l'envoi de l'email : {e}"