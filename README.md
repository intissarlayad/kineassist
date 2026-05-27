<div align="center">
<img src="assets/logoKine.png" alt="KineAssist Logo" width="180" />
  <h1>KineAssist</h1>
  <p><strong>Plateforme Web de Kinésithérapie Assistée par Intelligence Artificielle</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />
    <img src="https://img.shields.io/badge/MediaPipe-Pose%20Estimation-0097A7?style=flat-square&logo=google&logoColor=white" />
    <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white" />
    <img src="https://img.shields.io/badge/Version-v1.0-58a6ff?style=flat-square" />
    <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" />
    <img src="https://img.shields.io/badge/License-Academic-lightgrey?style=flat-square" />
  </p>

  <p>
    <em>Suivi des exercices de rééducation en temps réel — double interface kiné & patient,<br/>détection de mouvement par webcam, retour vocal et suivi de progression hebdomadaire.</em>
  </p>
</div>

---

## Table des matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Contexte & Motivation](#-contexte--motivation)
3. [Fonctionnalités détaillées](#-fonctionnalités-détaillées)
4. [Comment ça marche — Flow utilisateur](#-comment-ça-marche--flow-utilisateur)
5. [Pages & Interface](#-pages--interface)
6. [Screenshots](#-screenshots)
7. [Architecture du projet](#-architecture-du-projet)
8. [Stack technique](#-stack-technique)
9. [Installation](#-installation)
10. [Configuration](#-configuration)
11. [Sécurité](#-sécurité)
12. [Roadmap](#-roadmap)
13. [Auteures & Contact](#-auteures--contact)

---

## Vue d'ensemble

**KineAssist** est une application web à double interface dédiée au suivi de la rééducation kinésithérapique à distance. Elle permet à un kinésithérapeute de créer des protocoles d'exercices personnalisés pour ses patients, et au patient d'exécuter ces exercices de manière autonome depuis chez lui, guidé par un système de détection de mouvement en temps réel.

L'application repose sur **MediaPipe Pose**, une bibliothèque de Google permettant l'estimation de la posture humaine via webcam. Chaque exercice est évalué automatiquement : le système analyse la qualité du mouvement, compte les répétitions et attribue un score, sans intervention humaine directe.

Ce projet a été réalisé dans le cadre d'un cursus en intelligence artificielle, avec pour objectif de proposer une solution concrète à un problème réel dans le domaine de la santé numérique.

---

## Contexte & Motivation

La rééducation kinésithérapique requiert une pratique régulière entre les séances en cabinet. Or, sans outil de suivi adapté, les kinésithérapeutes font face à plusieurs difficultés :

- **Absence de visibilité** sur l'exécution réelle des exercices à domicile
- **Manque de feedback** pour le patient lors de l'exécution autonome
- **Difficulté de coordination** entre prescription d'exercices et suivi de l'observance
- **Risque de mauvaise exécution** pouvant aggraver une pathologie

KineAssist répond à ces enjeux en proposant un canal numérique bidirectionnel : le kinésithérapeute prescrit et surveille, le patient exécute et progresse, le tout dans une interface unifiée, sécurisée et accessible depuis n'importe quel navigateur.

---

## Fonctionnalités détaillées

### Interface Kinésithérapeute

#### Gestion des patients
- Création de dossiers patients complets : nom, prénom, date de naissance, pathologie, objectifs thérapeutiques et semaine de rééducation en cours
- Consultation et modification des informations à tout moment
- Visualisation de la photo de profil du patient
- Accès à l'historique médical et aux antécédents renseignés par le patient

#### Protocoles d'exercices
- Assignation d'un protocole d'exercices personnalisé par patient
- Sélection parmi un catalogue d'exercices prédéfinis (données stockées dans `data/protocols/`)
- Paramétrage du nombre de répétitions et de séries attendues
- Possibilité d'étendre le catalogue en ajoutant de nouveaux protocoles

#### Système d'invitation
- Envoi d'un email d'invitation au patient depuis l'interface kiné
- Génération automatique d'un lien d'activation sécurisé (token unique, valable 72 heures)
- Le patient reçoit ses identifiants de connexion et active son compte en un clic

#### Suivi et monitoring
- Tableau de bord de suivi par patient : nombre de répétitions effectuées, score moyen, meilleur score, tendance d'évolution
- Visualisation de la progression semaine par semaine
- Système d'alertes en cas d'inactivité ou de score en baisse
- Espace de notes cliniques pour consigner des observations sur chaque patient

---

### Interface Patient

#### Activation du compte
- Réception d'un email contenant un lien d'activation unique
- Création du mot de passe lors de la première connexion
- Accès immédiat au tableau de bord personnel après activation

#### Tableau de bord personnel
- Vue d'ensemble des exercices prescrits pour la semaine en cours
- Historique des sessions passées avec scores et répétitions
- Progression visuelle semaine par semaine
- Accès rapide à la prochaine session d'exercices

#### Exercices guidés par détection de mouvement
C'est la fonctionnalité centrale de KineAssist. Lors d'une session d'exercice :

1. **Initialisation de la webcam** — Le flux vidéo est capturé en temps réel via le navigateur
2. **Détection de pose** — MediaPipe Pose identifie 33 points-clés du corps humain à chaque frame
3. **Analyse du mouvement** — Les angles articulaires sont calculés et comparés aux références de mouvement générées par `generate_references.py`
4. **Comptage des répétitions** — Le système détecte automatiquement chaque répétition valide
5. **Score en temps réel** — Un score de qualité est calculé en fonction de la précision du mouvement
6. **Retour vocal** — Des instructions audio sont générées via synthèse vocale (`sound_tts.py`) pour guider et corriger le patient

#### Gestion du profil
- Renseignement des informations personnelles : poids, taille, date de naissance
- Ajout d'une photo de profil
- Saisie des antécédents médicaux visibles par le kinésithérapeute
- Modification des informations à tout moment

#### Export du bilan
- Génération d'un rapport PDF récapitulatif des sessions
- Contenu : exercices effectués, scores, répétitions, progression temporelle
- Téléchargeable depuis le tableau de bord patient

---

## Comment ça marche — Flow utilisateur

### Côté kinésithérapeute

```
1. Inscription / Connexion
        ↓
2. Création du dossier patient
   (pathologie, objectifs, semaine de rééducation)
        ↓
3. Assignation d'un protocole d'exercices
        ↓
4. Envoi de l'invitation par email
        ↓
5. Suivi de la progression du patient
   (scores, répétitions, alertes, notes)
```

### Côté patient

```
1. Réception de l'email d'invitation
        ↓
2. Activation du compte (lien sécurisé, 72h)
        ↓
3. Connexion au tableau de bord
        ↓
4. Lancement d'une session d'exercice
   → Webcam activée
   → Détection de pose en temps réel
   → Retour vocal + score
        ↓
5. Consultation de l'historique & progression
```

---

## Pages & Interface

### Landing Page (`index.html` — port 8000)
Page d'accueil publique présentant la plateforme. Accessible avant toute connexion. Fournit une introduction au projet, ses fonctionnalités principales et des liens vers les interfaces kiné et patient.

### Page d'authentification (`auth.py`)
Interface de connexion commune aux kinésithérapeutes et aux patients. Le système redirige automatiquement vers le tableau de bord approprié en fonction du rôle de l'utilisateur identifié en base de données.

### Page d'activation du compte patient
Accessible via le lien reçu par email. Permet au patient de définir son mot de passe lors de sa première connexion. Le token d'activation est vérifié et invalidé après utilisation.

### Dashboard Kinésithérapeute
Interface principale du professionnel de santé. Comprend :
- La liste de ses patients avec statut d'activité
- L'accès aux dossiers individuels
- Le suivi des sessions récentes
- Le module de gestion des protocoles

### Dashboard Patient
Interface principale du patient. Comprend :
- Le récapitulatif des exercices prescrits
- L'accès à la session d'exercice en cours
- L'historique des sessions passées
- La progression hebdomadaire sous forme de graphique

### Module d'exercice (webcam + MediaPipe)
Interface dédiée à l'exécution des exercices. Affiche le flux webcam en temps réel avec superposition des points-clés détectés, le compteur de répétitions, le score de qualité et les instructions vocales.

### Page de rapport PDF
Interface permettant la génération et le téléchargement du bilan patient au format PDF.

---

## Screenshots

### Landing page
![Landing page](assets/screenshots/landing.png)

### Authentification
![Authentification](assets/screenshots/auth.png)

### Interface kinésithérapeute
![Interface kinésithérapeute](assets/screenshots/kine_interface.png)

### Activation compte patient
![Activation compte patient](assets/screenshots/activation.png)

### Dashboard patient
![Dashboard patient 1](assets/screenshots/dashboard.png)
![Dashboard patient 2](assets/screenshots/dashboard2.png)

> 📹 Vidéo de démonstration complète : `assets/kine.mp4` *(à venir)*

---

## Architecture du projet

```
KineAssist/
├── app.py                    # Point d'entrée Streamlit — routing multipage
├── run.py                    # Lanceur principal (Streamlit + landing page)
├── auth.py                   # Authentification kiné / patient (sessions, rôles)
├── database.py               # Modèles SQLite & requêtes (bcrypt, ORM léger)
├── mailer.py                 # Envoi des emails d'invitation (SMTP)
├── sound_tts.py              # Synthèse vocale pour le guidage des exercices
├── generate_references.py    # Génération des références de mouvement (angles)
├── fix_css.py                # Surcharge CSS Streamlit (thème personnalisé)
├── config.toml               # Configuration du thème Streamlit
├── index.html                # Landing page statique (port 8000)
├── requirements.txt          # Dépendances Python
│
├── assets/
│   ├── logokine.png          # Logo de l'application
│   ├── sound_good.wav        # Son de validation (répétition réussie)
│   ├── sound_error.wav       # Son d'erreur (mouvement incorrect)
│   └── screenshots/          # Captures d'écran pour le README
│       ├── landing.png
│       ├── auth.png
│       ├── kine_interface.png
│       ├── activation.png
│       ├── dashboard.png
│       └── dashboard2.png
│
├── core/                     # Logique métier — détection et analyse de mouvement
│   └── ...                   # Modules MediaPipe, calcul d'angles, scoring
│
├── data/
│   └── protocols/            # Protocoles d'exercices (JSON)
│       └── exercises.json    # Catalogue des exercices disponibles
│
├── pages/                    # Pages Streamlit (architecture multipage)
│   ├── 1_Dashboard_Ki...     # Dashboard kinésithérapeute
│   └── 2_Rapport_PDF.py      # Génération du rapport PDF patient
│
├── scripts/                  # Scripts utilitaires (initialisation BDD, etc.)
├── .env.example              # Template des variables d'environnement
├── .gitignore                # Exclusions Git (.env, venv, __pycache__, etc.)
└── venv/                     # Environnement virtuel Python (non versionné)
```

---

## Stack technique

| Composant | Technologie | Rôle |
|---|---|---|
| Framework web | Streamlit 1.x | Interface utilisateur multipage |
| Landing page | HTML / CSS | Page d'accueil publique (port 8000) |
| Détection de pose | MediaPipe Pose | Estimation 33 points-clés du corps |
| Capture vidéo | Webcam (navigateur) | Flux vidéo temps réel |
| Base de données | SQLite | Stockage patients, sessions, tokens |
| Hachage mots de passe | bcrypt | Sécurité des credentials |
| Email | SMTP (Gmail) | Envoi des invitations patients |
| Synthèse vocale | TTS Python | Guidage audio des exercices |
| Export documents | PDF (Python) | Rapport bilan patient |
| Langage | Python 3.10+ | Backend complet |

---

## Installation

### Prérequis

- Python **3.10** ou supérieur
- Webcam fonctionnelle (nécessaire pour la détection de mouvement)
- Accès SMTP configuré (Gmail recommandé)
- Navigateur web moderne (Chrome, Firefox, Edge)

### Étapes d'installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/ayaidh123/Kineassist.git
cd Kineassist

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement — Windows
venv\Scripts\activate

# Activer l'environnement — macOS / Linux
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs SMTP (voir section Configuration)

# 5. Lancer l'application
python run.py
```

### URLs d'accès

| Interface | URL |
|---|---|
| Application Streamlit (kiné & patient) | http://localhost:8501 |
| Landing page | http://localhost:8000 |

Pour lancer uniquement la landing page :
```bash
python -m http.server 8000
```

---

## Configuration

Créer un fichier `.env` à la racine du projet en copiant le template fourni :

```bash
cp .env.example .env
```

Contenu du fichier `.env` :

```env
# Configuration SMTP — envoi des emails d'invitation patients
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_application
```

> **Important — Gmail** : N'utilisez pas votre mot de passe Gmail standard. Générez un **mot de passe d'application** dédié via : Compte Google → Sécurité → Vérification en deux étapes → Mots de passe des applications.

> **Important — Sécurité** : Le fichier `.env` est listé dans `.gitignore` et ne doit jamais être versionné ni partagé. Il contient des credentials sensibles.

---

## Sécurité

KineAssist applique plusieurs bonnes pratiques de sécurité :

| Mécanisme | Implémentation |
|---|---|
| Hachage des mots de passe | bcrypt avec salt aléatoire par entrée — aucun mot de passe n'est stocké en clair |
| Tokens d'invitation | Générés avec `secrets.token_urlsafe(32)`, expiration automatique après 72 heures |
| Protection SQL | Requêtes paramétrées (`?`) dans toutes les interactions SQLite — protection contre les injections SQL |
| Variables sensibles | Chargées exclusivement depuis `.env`, jamais codées en dur dans le code source |
| Gestion des sessions | Sessions Streamlit isolées par utilisateur avec contrôle du rôle (kiné / patient) |

---

## Roadmap

### Fonctionnalités implémentées

- [x] Double interface kiné / patient avec gestion des rôles
- [x] Landing page HTML (port 8000)
- [x] Détection de mouvement MediaPipe en temps réel via webcam
- [x] Système d'invitation patient par email avec token sécurisé
- [x] Suivi de progression hebdomadaire (scores, répétitions, tendance)
- [x] Hachage bcrypt des mots de passe
- [x] Export PDF du bilan patient
- [x] Catalogue multi-exercices (protocoles JSON extensibles)
- [x] Tableau de bord analytique pour le kinésithérapeute
- [x] Retour vocal pendant les exercices (synthèse vocale)
- [x] Gestion du profil patient (photo, poids, taille, antécédents)

### Améliorations prévues

- [ ] Déploiement sur Streamlit Community Cloud
- [ ] Notifications email automatiques en cas d'alerte (inactivité, score en baisse)
- [ ] Tableau de bord analytique avancé avec visualisations interactives
- [ ] Ajout de nouveaux exercices au catalogue via l'interface kiné
- [ ] Support multi-langue (français / anglais / arabe)
- [ ] Application mobile (React Native ou Flutter)

---

## Auteures

Ce projet a été développé par deux étudiantes en intelligence artificielle dans le cadre d'un projet académique.

**Aya IDHAMOUCH** — *AI Engineer*
- GitHub : [@ayaidh123](https://github.com/ayaidh123)
- LinkedIn : [aya-idhamouch](https://www.linkedin.com/in/aya-idhamouch-22a996319)

**Intissar LAYAD** — *AI Engineer*
- GitHub : [@intissarlayad](https://github.com/intissarlayad)
- LinkedIn : [intissar-layad](https://www.linkedin.com/in/intissar-layad-07444b377)

> Projet académique réalisé dans le cadre d'un cours de Computer Vision, dont le domaine d'application — la santé numérique et la rééducation à distance — a été entièrement choisi et conçu par l'équipeLe projet combine MediaPipe, OpenCV et un moteur RAG pour créer une plateforme de suivi kinésithérapeutique : analyse du mouvement en temps réel, scoring des exercices et feedback correctif automatisé.

<div align="center">
  <sub>Built with ❤️ for accessible physiotherapy rehabilitation.</sub>
</div>