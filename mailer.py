"""
mailer.py — Envoi d'emails via l'API Brevo (ex-Sendinblue)
============================================================
Secrets requis (Streamlit Cloud ou .env local) :
  BREVO_API_KEY  = xkeysib-...   (clé API Brevo)
  GMAIL_USER     = votre@email.com  (adresse expéditeur)
  APP_URL        = https://votre-app.streamlit.app
"""

import os
import json
import requests


# ─── helpers ──────────────────────────────────────────────────────────────────

def _get_secret(key: str, default: str = "") -> str:
    """Lit un secret depuis st.secrets (Streamlit Cloud) puis os.getenv."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


# ─── envoi Brevo ──────────────────────────────────────────────────────────────

def send_invitation_email(
    patient_email: str,
    patient_nom: str,
    kine_nom: str,
    token: str,
) -> tuple[bool, str]:
    """
    Envoie un email d'invitation via l'API Brevo.
    Retourne (True, message_ok) ou (False, message_erreur).
    """
    api_key      = _get_secret("BREVO_API_KEY")
    sender_email = _get_secret("GMAIL_USER")
    app_url      = _get_secret("APP_URL", "http://localhost:8501")

    if not api_key:
        return False, "BREVO_API_KEY non configuré dans st.secrets ou les variables d'environnement."
    if not sender_email:
        return False, "GMAIL_USER (adresse expéditeur) non configuré."

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
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background-color: #F0F2F5; padding: 40px 16px; }}
    .wrapper {{ max-width: 520px; margin: 0 auto; }}
    .header {{ background-color: #0C2340; border-radius: 8px 8px 0 0; padding: 36px 40px 32px; }}
    .header h1 {{ color: #FFFFFF; font-size: 22px; font-weight: 500; line-height: 1.3; margin-bottom: 6px; }}
    .header p  {{ color: #7DA8D0; font-size: 13px; }}
    .body {{ background-color: #FFFFFF; padding: 36px 40px; }}
    .body p {{ font-size: 15px; line-height: 1.75; color: #4B5563; margin-bottom: 16px; }}
    .body p strong {{ font-weight: 600; color: #111827; }}
    .btn {{ display: inline-block; background-color: #0C2340; color: #FFFFFF !important;
             text-decoration: none; padding: 13px 32px; border-radius: 6px;
             font-size: 14px; font-weight: 500; margin: 24px 0; }}
    .note {{ border-left: 2px solid #D1D5DB; padding: 14px 16px; margin-top: 8px; }}
    .note p {{ font-size: 13px; color: #6B7280; margin-bottom: 6px; }}
    .footer {{ background-color: #FFFFFF; border-top: 1px solid #F3F4F6;
               border-radius: 0 0 8px 8px; padding: 18px 40px;
               display: flex; justify-content: space-between; }}
    .footer span {{ font-size: 12px; color: #9CA3AF; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>Votre espace de rééducation personnalisé</h1>
      <p>Plateforme de suivi kinésithérapique — KineAssist</p>
    </div>
    <div class="body">
      <p>Bonjour <strong>{patient_nom}</strong>,</p>
      <p>
        Votre kinésithérapeute, <strong>{kine_nom}</strong>, vous a créé un compte
        sur KineAssist afin d'assurer le suivi de votre rééducation.
      </p>
      <p>Cliquez sur le bouton ci-dessous pour définir votre mot de passe et accéder à votre espace personnel.</p>
      <a href="{activation_link}" class="btn">Activer mon compte</a>
      <div class="note">
        <p>Ce lien est valable <strong>72 heures</strong>. Passé ce délai, contactez votre praticien.</p>
        <p>Votre mot de passe ne sera jamais communiqué à votre praticien.</p>
      </div>
    </div>
    <div class="footer">
      <span>KineAssist — Suivi de rééducation</span>
      <span>Ne pas répondre à cet email</span>
    </div>
  </div>
</body>
</html>"""

    payload = {
        "sender":      {"email": sender_email, "name": "KineAssist"},
        "to":          [{"email": patient_email}],
        "subject":     subject,
        "htmlContent": html_body,
    }
    headers = {
        "api-key":      api_key,
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload),
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 201:
            return True, "Email d'invitation envoyé avec succès via Brevo."
        try:
            err_msg = resp.json().get("message", resp.text)
        except Exception:
            err_msg = resp.text
        return False, f"Erreur Brevo ({resp.status_code}) : {err_msg}"
    except requests.exceptions.Timeout:
        return False, "Délai d'attente dépassé lors de la connexion à Brevo."
    except Exception as exc:
        return False, f"Erreur lors de l'envoi via Brevo : {exc}"