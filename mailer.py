"""
mailer.py — Envoi d'emails d'invitation via l'API Brevo (Sendinblue)
=====================================================================
Ce module utilise les secrets de Streamlit Cloud (ou les variables d'environnement) :
  - BREVO_API_KEY : clé API Brevo (requise)
  - GMAIL_USER   : adresse "expéditeur" affichée dans l'email (ex: noreply@votre-domaine.com)
  - APP_URL      : URL de l'application (pour le lien d'activation)

En local, les valeurs sont lues depuis le fichier .env.
"""

import os
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------------------------------------------------------
# Helper : lecture des secrets (Streamlit Cloud > env)
# ---------------------------------------------------------------------------
def _get_secret(key: str, default: str = "") -> str:
    """Retourne la valeur d'un secret.
    1️⃣ Essaie `st.secrets[key]` (Streamlit Cloud)
    2️⃣ Sinon, variable d'environnement
    3️⃣ Sinon, valeur par défaut.
    """
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

# ---------------------------------------------------------------------------
# Envoi d'email via Brevo
# ---------------------------------------------------------------------------
def _send_via_brevo(
    to_email: str,
    subject: str,
    html_content: str,
    sender_email: str,
    api_key: str,
) -> tuple[bool, str]:
    """Envoie l'email avec l'API Brevo.
    Retourne (True, "OK") en cas de succès, sinon (False, message d'erreur).
    """
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"email": sender_email, "name": "KineAssist"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        if resp.status_code == 201:
            return True, "Email envoyé avec succès via Brevo."
        # Brevo renvoie souvent 400 avec détail dans le JSON
        try:
            err = resp.json().get("message", resp.text)
        except Exception:
            err = resp.text
        return False, f"Erreur Brevo ({resp.status_code}) : {err}"
    except Exception as e:
        return False, f"Exception lors de l'appel à Brevo : {e}"

# ---------------------------------------------------------------------------
# Fonction publique appelée depuis l'application
# ---------------------------------------------------------------------------
def send_invitation_email(
    patient_email: str,
    patient_nom: str,
    kine_nom: str,
    token: str,
) -> tuple[bool, str]:
    """Construit le message d'invitation et l'envoie via Brevo.
    Retourne (True, message) si l'email a bien été transmis.
    """
    # Secrets
    sender_email = _get_secret("GMAIL_USER")  # utilisé comme expéditeur
    api_key = _get_secret("BREVO_API_KEY")
    app_url = _get_secret("APP_URL", "http://localhost:8501")

    if not sender_email or not api_key:
        return (
            False,
            "GMAIL_USER ou BREVO_API_KEY non configuré dans st.secrets ou les variables d'environnement.",
        )

    activation_link = f"{app_url}?token={token}"
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
        msg["From"]    = gmail_user
        msg["To"]      = patient_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, patient_email, msg.as_string())

        return True, "Email envoyé avec succès."

    except smtplib.SMTPAuthenticationError:
        return False, (
            "Erreur d'authentification Gmail. "
            "Vérifiez GMAIL_USER et GMAIL_PASS (mot de passe d'application)."
        )
    except Exception as e:
        return False, f"Erreur lors de l'envoi de l'email : {e}"