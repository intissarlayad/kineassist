"""
database.py — Gestion SQLite (local) & PostgreSQL (cloud) pour KineAssist
=========================================================================
En production : définir DATABASE_URL dans les variables d'environnement.
En local : utilise kineassist.db (SQLite) si DATABASE_URL n'est pas défini.

Tables :
  - kines     : comptes kinésithérapeutes
  - patients  : comptes patients (liés à un kiné)
  - invitations : tokens d'invitation envoyés par email
"""

import os
import secrets
import hashlib
import hmac
from pathlib import Path
from datetime import datetime, timedelta

# Charger .env en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Lire DATABASE_URL : priorité aux variables d'env, sinon st.secrets (Streamlit Cloud)
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    try:
        import streamlit as st
        DATABASE_URL = st.secrets.get("DATABASE_URL", "")
    except Exception:
        pass

# Lire GMAIL & APP_URL depuis st.secrets si variables d'env non définies
try:
    import streamlit as st
    if not os.getenv("GMAIL_USER"):
        os.environ["GMAIL_USER"] = st.secrets.get("GMAIL_USER", "")
    if not os.getenv("GMAIL_PASS"):
        os.environ["GMAIL_PASS"] = st.secrets.get("GMAIL_PASS", "")
    if not os.getenv("APP_URL"):
        os.environ["APP_URL"] = st.secrets.get("APP_URL", "http://localhost:8501")
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# Détection du mode (PostgreSQL ou SQLite)
# ─────────────────────────────────────────────────────────────────────────────

USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgresql"))

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    DB_PH = "%s"  # placeholder PostgreSQL
else:
    import sqlite3
    DB_PATH = Path("kineassist.db")
    DB_PH = "?"   # placeholder SQLite


# ─────────────────────────────────────────────────────────────────────────────
# Connexion
# ─────────────────────────────────────────────────────────────────────────────

def get_conn():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def _adapt_sql(sql: str) -> str:
    """Adapte une requête SQLite vers PostgreSQL si nécessaire."""
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql = sql.replace("datetime('now')", "CURRENT_TIMESTAMP")
    return sql


def _exec(conn, sql: str, params=()):
    sql = _adapt_sql(sql)
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def _executescript(conn, script: str):
    """Exécute un script SQL (plusieurs statements)."""
    if USE_POSTGRES:
        cur = conn.cursor()
        # Découper par ; et exécuter statement par statement
        for stmt in script.strip().split(";"):
            stmt = _adapt_sql(stmt.strip())
            if stmt:
                cur.execute(stmt)
        conn.commit()
    else:
        conn.cursor().executescript(script)
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = get_conn()

    _executescript(conn, """
    CREATE TABLE IF NOT EXISTS kines (
        id          SERIAL PRIMARY KEY,
        email       TEXT    UNIQUE NOT NULL,
        nom         TEXT    NOT NULL,
        password_hash TEXT  NOT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS patients (
        id          SERIAL PRIMARY KEY,
        email       TEXT    UNIQUE NOT NULL,
        nom         TEXT    NOT NULL,
        age         INTEGER DEFAULT 0,
        pathologie  TEXT    DEFAULT '',
        exercice    TEXT    DEFAULT 'Flexion du genou',
        semaine     INTEGER DEFAULT 1,
        objectif_semaine INTEGER DEFAULT 8,
        password_hash TEXT  DEFAULT NULL,
        activated   INTEGER DEFAULT 0,
        kine_id     INTEGER NOT NULL,
        notes       TEXT    DEFAULT '',
        alerte      INTEGER DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS invitations (
        id          SERIAL PRIMARY KEY,
        token       TEXT    UNIQUE NOT NULL,
        patient_id  INTEGER NOT NULL,
        email       TEXT    NOT NULL,
        expires_at  TEXT    NOT NULL,
        used        INTEGER DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions_kine (
        id          SERIAL PRIMARY KEY,
        patient_id  INTEGER NOT NULL,
        date        TEXT    NOT NULL,
        exercice    TEXT    DEFAULT '',
        reps        INTEGER DEFAULT 0,
        score_mean  REAL    DEFAULT 0,
        score_best  REAL    DEFAULT 0,
        trend       TEXT    DEFAULT 'stable',
        semaine     INTEGER DEFAULT 1
    )
    """)

    # Migrations (ajout de colonnes si manquantes)
    conn2 = get_conn()
    for col_def in [
        ("protocol",     "TEXT DEFAULT ''"),
        ("photo_b64",    "TEXT DEFAULT ''"),
        ("poids",        "REAL DEFAULT 0"),
        ("taille",       "INTEGER DEFAULT 0"),
        ("telephone",    "TEXT DEFAULT ''"),
        ("antecedents",  "TEXT DEFAULT ''"),
        ("genre",        "TEXT DEFAULT ''"),
    ]:
        col, default = col_def
        try:
            _exec(conn2, f"ALTER TABLE patients ADD COLUMN {col} {default}")
            conn2.commit()
        except Exception:
            try:
                conn2.rollback()
            except Exception:
                pass

    conn2.close()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _check_pwd(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(_hash(plain), hashed)


def _row_to_dict(row):
    """Convertit une ligne SQLite (Row) ou psycopg2 (RealDictRow) en dict."""
    if row is None:
        return None
    if isinstance(row, dict):
        return dict(row)
    return dict(row)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Kinés
# ─────────────────────────────────────────────────────────────────────────────

def register_kine(email: str, nom: str, password: str) -> tuple:
    conn = get_conn()
    try:
        _exec(conn,
            "INSERT INTO kines (email, nom, password_hash) VALUES (?, ?, ?)",
            (email.lower().strip(), nom.strip(), _hash(password))
        )
        conn.commit()
        return True, "ok"
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "Un compte kiné existe déjà avec cet email."
        return False, str(e)
    finally:
        conn.close()


def login_kine(email: str, password: str):
    """Retourne le dict kiné ou None."""
    conn = get_conn()
    try:
        cur = _exec(conn,
            "SELECT * FROM kines WHERE email = ?",
            (email.lower().strip(),)
        )
        row = cur.fetchone()
        if row and _check_pwd(password, _row_to_dict(row)["password_hash"]):
            return _row_to_dict(row)
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Patients
# ─────────────────────────────────────────────────────────────────────────────

def login_patient(email: str, password: str):
    """Retourne le dict patient ou None."""
    conn = get_conn()
    try:
        cur = _exec(conn,
            "SELECT * FROM patients WHERE email = ? AND activated = 1",
            (email.lower().strip(),)
        )
        row = cur.fetchone()
        if row:
            d = _row_to_dict(row)
            if d.get("password_hash") and _check_pwd(password, d["password_hash"]):
                return d
        return None
    finally:
        conn.close()


def activate_patient(token: str, password: str) -> tuple:
    """Active le compte patient via token d'invitation."""
    conn = get_conn()
    try:
        cur = _exec(conn,
            "SELECT * FROM invitations WHERE token = ? AND used = 0",
            (token,)
        )
        inv = cur.fetchone()
        if not inv:
            return False, "Lien invalide ou déjà utilisé."
        inv = _row_to_dict(inv)
        if datetime.fromisoformat(inv["expires_at"]) < datetime.now():
            return False, "Lien expiré. Demandez un nouvel email à votre kiné."

        _exec(conn,
            "UPDATE patients SET password_hash = ?, activated = 1 WHERE id = ?",
            (_hash(password), inv["patient_id"])
        )
        _exec(conn,
            "UPDATE invitations SET used = 1 WHERE token = ?",
            (token,)
        )
        conn.commit()
        return True, "ok"
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(e)
    finally:
        conn.close()


def get_patient_by_token(token: str):
    """Retourne le patient lié au token, ou None."""
    conn = get_conn()
    try:
        cur = _exec(conn, """
            SELECT p.* FROM patients p
            JOIN invitations i ON i.patient_id = p.id
            WHERE i.token = ? AND i.used = 0
        """, (token,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# CRUD — Patients (côté kiné)
# ─────────────────────────────────────────────────────────────────────────────

def get_patients_by_kine(kine_id: int) -> list:
    conn = get_conn()
    try:
        cur = _exec(conn,
            "SELECT * FROM patients WHERE kine_id = ? ORDER BY created_at DESC",
            (kine_id,)
        )
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def create_patient(kine_id: int, email: str, nom: str,
                   age: int = 0, pathologie: str = "",
                   exercice: str = "Flexion du genou",
                   semaine: int = 1, objectif_semaine: int = 8) -> tuple:
    """
    Crée un patient. Retourne (success, message, patient_id).
    """
    conn = get_conn()
    try:
        if USE_POSTGRES:
            cur = _exec(conn,
                """INSERT INTO patients
                   (email, nom, age, pathologie, exercice, semaine, objectif_semaine, kine_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                (email.lower().strip(), nom.strip(), age, pathologie, exercice,
                 semaine, objectif_semaine, kine_id)
            )
            row = cur.fetchone()
            patient_id = _row_to_dict(row)["id"]
        else:
            cur = _exec(conn,
                """INSERT INTO patients
                   (email, nom, age, pathologie, exercice, semaine, objectif_semaine, kine_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (email.lower().strip(), nom.strip(), age, pathologie, exercice,
                 semaine, objectif_semaine, kine_id)
            )
            patient_id = cur.lastrowid
        conn.commit()
        return True, "ok", patient_id
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "Un patient avec cet email existe déjà.", -1
        return False, str(e), -1
    finally:
        conn.close()


def update_patient(patient_id: int, nom: str, age: int, pathologie: str,
                   exercice: str, semaine: int, objectif_semaine: int,
                   notes: str, alerte: bool):
    conn = get_conn()
    try:
        _exec(conn, """
            UPDATE patients SET
                nom=?, age=?, pathologie=?, exercice=?,
                semaine=?, objectif_semaine=?, notes=?, alerte=?
            WHERE id=?
        """, (nom, age, pathologie, exercice, semaine, objectif_semaine,
              notes, int(alerte), patient_id))
        conn.commit()
    finally:
        conn.close()


def delete_patient(patient_id: int):
    conn = get_conn()
    try:
        _exec(conn, "DELETE FROM invitations WHERE patient_id = ?", (patient_id,))
        _exec(conn, "DELETE FROM sessions_kine WHERE patient_id = ?", (patient_id,))
        _exec(conn, "DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invitations
# ─────────────────────────────────────────────────────────────────────────────

def create_invitation(patient_id: int, email: str) -> str:
    """Crée un token d'invitation valable 72h. Retourne le token."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(hours=72)).isoformat()
    conn = get_conn()
    try:
        _exec(conn,
            "UPDATE invitations SET used = 1 WHERE patient_id = ? AND used = 0",
            (patient_id,)
        )
        _exec(conn,
            "INSERT INTO invitations (token, patient_id, email, expires_at) VALUES (?, ?, ?, ?)",
            (token, patient_id, email, expires)
        )
        conn.commit()
        return token
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────────────────────────────────────

def add_session(patient_id: int, exercice: str, reps: int,
                score_mean: float, score_best: float,
                trend: str, semaine: int):
    conn = get_conn()
    try:
        _exec(conn, """
            INSERT INTO sessions_kine
            (patient_id, date, exercice, reps, score_mean, score_best, trend, semaine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, datetime.now().strftime("%d/%m/%Y"),
              exercice, reps, score_mean, score_best, trend, semaine))
        conn.commit()
    finally:
        conn.close()


def get_sessions(patient_id: int) -> list:
    conn = get_conn()
    try:
        cur = _exec(conn,
            "SELECT * FROM sessions_kine WHERE patient_id = ? ORDER BY date ASC",
            (patient_id,)
        )
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def update_patient_protocol(patient_id: int, protocol: str):
    """Met à jour le protocole assigné au patient par le kiné."""
    conn = get_conn()
    try:
        _exec(conn,
            "UPDATE patients SET protocol=? WHERE id=?",
            (protocol, patient_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_patient_profile(patient_id: int, poids: float, taille: int,
                           telephone: str, antecedents: str, genre: str,
                           photo_b64: str = ""):
    """Met à jour les informations de profil du patient."""
    conn = get_conn()
    try:
        if photo_b64:
            _exec(conn,
                """UPDATE patients SET poids=?, taille=?, telephone=?,
                   antecedents=?, genre=?, photo_b64=? WHERE id=?""",
                (poids, taille, telephone, antecedents, genre, photo_b64, patient_id)
            )
        else:
            _exec(conn,
                """UPDATE patients SET poids=?, taille=?, telephone=?,
                   antecedents=?, genre=? WHERE id=?""",
                (poids, taille, telephone, antecedents, genre, patient_id)
            )
        conn.commit()
    finally:
        conn.close()


def get_patient_by_id(patient_id: int) -> dict:
    conn = get_conn()
    try:
        cur = _exec(conn, "SELECT * FROM patients WHERE id=?", (patient_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else {}
    finally:
        conn.close()


# Init automatique au démarrage
init_db()