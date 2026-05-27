"""
RAG Engine - Version finale avec vrais documents medicaux.

Mode AUTO :
  - Si index FAISS existe (data/rag_index/) => RAG reel sur documents medicaux
  - Sinon => base de regles enrichie (fallback sans GPU ni API)

Documents indexes :
  - protocole_flexion_genou.txt    (HAS + Beynnon 2005)
  - protocole_elevation_bras.txt   (HAS + Ludewig 2009)
  - protocole_rotation_tronc.txt   (HAS + McGill 2010)
  - erreurs_biomecaniques.txt      (guide detection/correction)
  - post_avc_protocole.txt         (HAS 2022 + SOFMER)
"""

import pickle
import json
import numpy as np
from pathlib import Path

# ── Tentative import librairies vectorielles (optionnel) ──────────────────────
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_VECTOR = True
except ImportError:
    HAS_VECTOR = False

INDEX_DIR = Path("data/rag_index")


# ── Base de regles enrichies (fallback) ───────────────────────────────────────
RULES = {
    "knee_flexion": {
        "genou_gauche": {
            "insuffisante": (
                "Flechissez davantage le genou gauche. Objectif : 90 degres. "
                "Selon le protocole HAS : contractez les ischio-jambiers, "
                "gardez le talon au sol et poussez lentement. "
                "Evitez de pencher le tronc en avant (compensation lombaire)."
            ),
            "excessive": (
                "Reduisez la flexion du genou gauche. "
                "Au-dela de 90 degres sans preparation, risque de surcharge condylienne. "
                "Arretez-vous quand vous sentez la tension articulaire."
            ),
        },
        "genou_droit": {
            "insuffisante": (
                "Flechissez davantage le genou droit. "
                "Poussez le talon vers le sol, activez les ischio-jambiers. "
                "Veillez a garder le genou dans l'axe de votre 2eme orteil."
            ),
            "excessive": "Reduisez la flexion du genou droit pour proteger le cartilage articulaire.",
        },
        "hanche_gauche": {
            "insuffisante": "Hanche insuffisamment stable. Gardez le bassin en position neutre. Evitez de vous incliner vers l'avant.",
            "excessive": "Hanche trop flechie : risque de compensation lombaire detecte. Redressez le tronc et verrouillez les abdominaux.",
        },
        "hanche_droite": {
            "insuffisante": "Stabilisez la hanche droite. Evitez le balancement lateral du bassin.",
            "excessive": "Hanche droite en flexion excessive. Contractez les abdominaux pour fixer le bassin.",
        },
    },
    "arm_raise": {
        "epaule_gauche": {
            "insuffisante": (
                "Montez le bras gauche plus haut. Objectif : 160 degres. "
                "Selon le protocole HAS coiffe des rotateurs : "
                "initiez le mouvement par le deltoid anterieur, "
                "tournez legerement la paume vers le haut au-dela de 90 degres "
                "pour eviter le conflit sous-acromial."
            ),
            "excessive": (
                "Ne forcez pas au-dela de la verticale. "
                "Le conflit sous-acromial survient typiquement au-dela de 160 degres. "
                "Protegez la coiffe des rotateurs."
            ),
        },
        "epaule_droite": {
            "insuffisante": "Montez le bras droit davantage. Gardez le coude tendu et la paume vers l'avant.",
            "excessive": "Bras droit trop haut. Risque de conflit sous-acromial. Limitez a 160 degres.",
        },
        "coude_gauche": {
            "insuffisante": "Tendez le coude gauche. Le bras doit etre rectiligne pour isoler correctement l'epaule.",
            "excessive": "Coude gauche trop flechis lors de l'elevation. Verrouillez l'articulation.",
        },
        "coude_droit": {
            "insuffisante": "Tendez le coude droit pour un mouvement optimal.",
            "excessive": "Reduisez la flexion du coude droit lors de l'elevation.",
        },
    },
    "trunk_rotation": {
        "hanche_gauche": {
            "insuffisante": "Stabilisez la hanche gauche. Elle ne doit pas participer a la rotation. Imaginez etre assis sur un tabouret fixe.",
            "excessive": (
                "Hanche gauche trop mobile : substitution lombaire detectee. "
                "Selon les recommandations HAS lombalgie : "
                "la rotation doit venir exclusivement du segment thoracique T1-T12. "
                "Bloquez le bassin et pivotez uniquement le haut du corps."
            ),
        },
        "hanche_droite": {
            "insuffisante": "Verrouillez la hanche droite. Contractez les fessiers pour fixer le bassin.",
            "excessive": "Hanche droite en compensation. Reduisez l'amplitude et recentrez le mouvement sur le thorax.",
        },
        "epaule_gauche": {
            "insuffisante": (
                "Augmentez la rotation vers la gauche. "
                "Regardez loin derriere vous. "
                "Selon le protocole : amplitude cible 40-45 degres chaque cote. "
                "Le mouvement doit venir du thorax, pas de la taille."
            ),
            "excessive": "Rotation gauche excessive. Limitez a 45 degres pour proteger les facettes articulaires vertebrales.",
        },
        "epaule_droite": {
            "insuffisante": "Pivotez davantage vers la droite. Expirez en tournant pour faciliter le mouvement.",
            "excessive": "Rotation droite trop importante. Controlez l'amplitude, evitez les torsions lombaires forcees.",
        },
    },
}

PROTOCOLS = {
    "knee_flexion": {
        "titre":       "Protocole reeducation flexion genou (HAS)",
        "indication":  "Gonarthrose, post-LCA, fracture rotule, syndrome femoropatellaire",
        "objectif":    "Recuperer une flexion active de 0 a 90 degres en 4 semaines, puis 135 degres en 8 semaines",
        "semaines": [
            "S1-S2 : Flexion passive assistee 0-45 degres, 3x10 reps. Glace 15 min apres.",
            "S3-S4 : Flexion active contre gravite 0-70 degres, 3x12 reps. Debut proprioception.",
            "S5-S6 : Flexion complete 0-90 degres avec resistance legere, 3x15 reps.",
            "S7-S8 : Flexion fonctionnelle 0-135 degres, squat, montee escaliers.",
        ],
        "precautions": "Stopper si douleur > 3/10. Valgus dynamique = STOP. Surveiller compensation lombaire.",
        "source": "HAS 2008 + Beynnon BD et al. 2005",
    },
    "arm_raise": {
        "titre":       "Protocole elevation membre superieur (HAS)",
        "indication":  "Post-AVC, chirurgie coiffe des rotateurs, conflit sous-acromial, capsulite",
        "objectif":    "Elevation active jusqu'a 160 degres sans compensation en 8 semaines",
        "semaines": [
            "S1-S2 : Elevation passive 0-60 degres. Exercices Codman 5 min 2x/jour.",
            "S3-S4 : Elevation active aidee 0-120 degres. Renforcement coiffe en rotation externe.",
            "S5-S6 : Elevation active complete 0-140 degres. Controle excentrique (4 secondes descente).",
            "S7-S8 : Elevation fonctionnelle 160 degres. Exercices AVQ, sport progressif.",
        ],
        "precautions": "Eviter rotation interne forcee > 90 degres. Surveiller haussement d'epaule. Arc douloureux 60-120 degres = STOP.",
        "source": "HAS 2012 + Ludewig PM, Reynolds JF 2009",
    },
    "trunk_rotation": {
        "titre":       "Protocole mobilisation rachis thoracique (HAS)",
        "indication":  "Lombalgie chronique, raideur thoracique, post-AVC, scoliose fonctionnelle",
        "objectif":    "Restaurer une rotation thoracique de 45 degres de chaque cote en 8 semaines",
        "semaines": [
            "S1-S2 : Rotation passive assistee 15-20 degres. Activation transverse abdominal.",
            "S3-S4 : Rotation active 30-35 degres. Gainage antirotation (Pallof press).",
            "S5-S6 : Rotation complete 40-45 degres avec maintien 2 secondes.",
            "S7-S8 : Exercices fonctionnels, sport progressif, prevention rechutes.",
        ],
        "precautions": "Bassin FIXE durant tout le mouvement. Contre-indique si hernie discale aigue. Jamais de rotation forcee douloureuse.",
        "source": "HAS 2019 + McGill SM 2010",
    },
}


# ── Classe principale ─────────────────────────────────────────────────────────

class RAGEngine:

    def __init__(self, index_dir=INDEX_DIR):
        self.index_dir  = Path(index_dir)
        self.index      = None
        self.chunks     = []
        self.embedder   = None
        self._mode      = "regles"
        self.ready      = False
        self._load()

    def _load(self):
        """Charge l'index FAISS si disponible, sinon mode regles."""
        if not HAS_VECTOR:
            self._mode = "regles"
            self.ready = True
            return

        idx_path   = self.index_dir / "medical.index"
        chunk_path = self.index_dir / "chunks.pkl"

        if idx_path.exists() and chunk_path.exists():
            try:
                self.index    = faiss.read_index(str(idx_path))
                with open(chunk_path, "rb") as f:
                    self.chunks = pickle.load(f)
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                self._mode    = "rag_reel"
                self.ready    = True
                return
            except Exception:
                pass

        self._mode = "regles"
        self.ready = True

    @property
    def mode(self):
        return "RAG Medical (FAISS)" if self._mode == "rag_reel" else "Base de regles medicales"

    def _retrieve(self, query, k=3):
        """Recupere les k chunks les plus pertinents via FAISS."""
        if self._mode != "rag_reel" or self.index is None:
            return []
        try:
            vec = self.embedder.encode([query]).astype(np.float32)
            faiss.normalize_L2(vec)
            D, I = self.index.search(vec, k)
            results = []
            for score, idx in zip(D[0], I[0]):
                if idx >= 0 and score > 0.3:
                    chunk = self.chunks[idx]
                    results.append({
                        "text":   chunk["text"],
                        "source": chunk["source"],
                        "score":  round(float(score), 3),
                    })
            return results
        except Exception:
            return []

    def get_correction(self, exercise_id, errors):
        """
        Genere les corrections en combinant les regles et le RAG si disponible.
        """
        if not errors:
            return ["Excellent ! Position correcte selon le protocole. Continuez ainsi."]

        messages = []
        exercise_rules = RULES.get(exercise_id, {})

        for err in errors:
            joint     = err["joint"]
            direction = err["direction"]
            severity  = err["severity"]
            prefix    = "🔴" if severity == "critique" else "⚠️"

            # Message de base depuis les regles
            rule_msg = exercise_rules.get(joint, {}).get(direction)
            if rule_msg:
                messages.append(f"{prefix} {rule_msg}")
            else:
                label = joint.replace("_gauche", " G").replace("_droit", " D").replace("_", " ").title()
                messages.append(f"{prefix} {label} : ecart de {abs(err['diff']):.0f}° (actuel {err['current']:.0f}° → cible {err['target']}°)")

        # Enrichissement RAG si disponible
        if self._mode == "rag_reel" and errors:
            critical = [e for e in errors if e["severity"] == "critique"]
            query_err = critical[0] if critical else errors[0]
            query = (
                f"correction exercice {exercise_id} "
                f"erreur {query_err['joint']} amplitude {query_err['direction']} "
                f"angle {query_err['current']:.0f} degres cible {query_err['target']} degres"
            )
            retrieved = self._retrieve(query, k=2)
            for chunk in retrieved[:1]:
                # Extraire la phrase la plus pertinente du chunk
                sentences = [s.strip() for s in chunk["text"].split(".") if len(s.strip()) > 30]
                if sentences:
                    src = chunk["source"].replace(".txt","").replace("_"," ").title()
                    messages.append(f"📄 Source ({src}) : {sentences[0]}.")

        return messages if messages else ["Continuez l'exercice en controlant votre posture."]

    def get_protocol_info(self, exercise_id):
        p = PROTOCOLS.get(exercise_id, {})
        return f"{p.get('titre','')} — {p.get('indication','')}"

    def get_protocol_detail(self, exercise_id):
        return PROTOCOLS.get(exercise_id, {})

    def get_weekly_tip(self, week_number=1):
        tips = [
            "Respirez calmement : expirez a l'effort, inspirez au retour. Ne bloquez jamais la respiration.",
            "Progressez lentement. L'amplitude s'ameliore sur plusieurs semaines. Ne forcez jamais.",
            "La regularite prime sur l'intensite : 10 repetitions correctes valent mieux que 20 bâclees.",
            "Appliquez de la glace 15 minutes apres chaque seance si vous ressentez une douleur.",
            "Evaluez votre douleur sur 10. Au-dela de 3/10, reduisez l'amplitude. Au-dela de 5/10, STOP.",
            "La fatigue musculaire est normale. La douleur articulaire ne l'est pas.",
        ]
        return tips[min(week_number - 1, len(tips) - 1)]

    def search_protocol(self, query):
        """Recherche libre dans les protocoles medicaux."""
        if self._mode == "rag_reel":
            results = self._retrieve(query, k=3)
            if results:
                return [
                    f"[{r['source']}] {r['text'][:250]}..."
                    for r in results
                ]
        return ["Index RAG non disponible. Lancez scripts/build_rag_index.py d'abord."]