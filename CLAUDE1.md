# CLAUDE.md — MH-CyberScore : Plateforme Souveraine de Cyber Scoring & VRM
# Malakoff Humanis — Direction RSSI/DPO
# Version 1.0 — Février 2026

---

## TABLE DES MATIÈRES

1. [Vision & Objectif du Projet](#1-vision--objectif-du-projet)
2. [Contexte Organisationnel & Réglementaire](#2-contexte-organisationnel--réglementaire)
3. [Architecture Technique Cible](#3-architecture-technique-cible)
4. [Modules Fonctionnels Détaillés](#4-modules-fonctionnels-détaillés)
5. [Pipeline Agentic AI](#5-pipeline-agentic-ai)
6. [Méthodologie de Scoring](#6-méthodologie-de-scoring)
7. [Data Visualisation & UX](#7-data-visualisation--ux)
8. [Sécurité, Conformité & Souveraineté](#8-sécurité-conformité--souveraineté)
9. [Stack Technique & Dépendances](#9-stack-technique--dépendances)
10. [Structure du Monorepo](#10-structure-du-monorepo)
11. [Standards de Code & Conventions](#11-standards-de-code--conventions)
12. [Plan de Développement par Sprints](#12-plan-de-développement-par-sprints)
13. [Tests & Qualité](#13-tests--qualité)
14. [Déploiement & Infrastructure](#14-déploiement--infrastructure)
15. [Glossaire & Références](#15-glossaire--références)

---

## 1. VISION & OBJECTIF DU PROJET

### 1.1 Mission

Concevoir et développer **MH-CyberScore**, une plateforme souveraine de cyber scoring et de gestion des risques fournisseurs (Vendor Risk Management), 100% développée en interne par la RSSI de Malakoff Humanis, hébergée sur infrastructure française, et pilotée par des agents IA autonomes.

### 1.2 Pourquoi un développement interne ?

Après évaluation approfondie de SecurityScorecard (USA) et Board of Cyber (France), le RSSI a conclu que :

- **SecurityScorecard** : leader mondial (12M+ entreprises, IA avancée, 50+ intégrations) mais soumis au Cloud Act et FISA 702, ce qui crée un risque juridique structurel incompatible avec le traitement de données HDS et les exigences DORA art. 28-30 pour une mutuelle de santé.
- **Board of Cyber** : souverain et pertinent (France Cybersecurity 2025, Gartner TPRM mai 2025) mais couverture mondiale limitée, maturité IA insuffisante, écosystème d'intégrations restreint.
- **Ni l'un ni l'autre ne couvre l'ensemble des besoins** spécifiques de Malakoff Humanis : souveraineté totale, scoring interne + externe, conformité DORA native, intégration profonde avec l'écosystème SI existant, et contrôle complet de la méthodologie.

### 1.3 Ce que MH-CyberScore prend du meilleur des deux

| Capacité | Inspiré de SSC | Inspiré de BoC | Innovation MH |
|----------|----------------|-----------------|---------------|
| Scoring A-F multi-facteurs | ✅ 10 facteurs SSC | | Adapté au contexte mutuelle santé |
| Scoring 0-1000 par domaine | | ✅ 7 domaines BoC | 8 domaines enrichis |
| SCDR (Supply Chain Detection & Response) | ✅ SSC | | Intégré nativement |
| Suite interne (AD + M365 + GRC) | | ✅ AD Rating + 365 Rating + TrustHQ | Agents IA pour chaque |
| Nth-party detection | ✅ SSC | | Pipeline agentic OSINT |
| Dark web monitoring | ✅ STRIKE Intelligence | | Agent spécialisé légal |
| Rapports COMEX brandés | | ✅ PPT/PDF avec logo | Génération IA + templates |
| ChatBot IA (ChatSSC) | ✅ SSC | | Claude API intégré nativement |
| Questionnaires IA (Smart Answer) | ✅ SSC 83% réduction | ✅ RGPD/NIST templates | Auto-complétion + validation IA |
| Benchmark sectoriel | ✅ SSC industrie | ✅ BoC 22 secteurs | Benchmark mutuelle/assurance/santé |
| Souveraineté totale | ❌ Cloud Act | ✅ FR natif | Hébergement SecNumCloud |
| Conformité DORA native | ⚠️ Mapping partiel | ⚠️ TrustHQ séparé | Intégré dans le scoring |
| Power BI / SIEM natif | ✅ SSC 2024 | ❌ | API + connecteurs natifs |

### 1.4 Objectifs mesurables

- **T0+3 mois** : MVP — scoring externe de 50 fournisseurs critiques avec dashboard RSSI
- **T0+6 mois** : V1 — scoring complet + questionnaires + rapports COMEX + alerting
- **T0+9 mois** : V2 — agents IA agentic (OSINT, dark web, Nth-party) + intégrations SIEM/ITSM
- **T0+12 mois** : V3 — scoring interne AD/M365 + module GRC/PSSI + benchmark sectoriel

---

## 2. CONTEXTE ORGANISATIONNEL & RÉGLEMENTAIRE

### 2.1 Malakoff Humanis

- **Activité** : mutuelle de protection sociale (santé, prévoyance, retraite, épargne)
- **Données traitées** : données de santé (HDS), données personnelles (RGPD), données financières (DORA)
- **Écosystème fournisseurs** : ~500 tiers IT et métiers, de la PME française au GAFAM
- **SI existant** : ServiceNow (ITSM/VRM), Splunk (SIEM), Active Directory, Microsoft 365, Power BI
- **Décideurs** : RSSI/DPO (pilote), DSI, Direction Achats, Comité des Risques, COMEX

### 2.2 Cadre réglementaire applicable

| Réglementation | Impact sur MH-CyberScore | Articles clés |
|----------------|--------------------------|---------------|
| **DORA** | Cartographie prestataires TIC, monitoring continu, risque concentration, registre d'informations, tests résilience | Art. 5-16, 17-23, 24-27, **28-30** |
| **RGPD** | Protection données personnelles des fournisseurs évalués, base légale intérêt légitime, minimisation | Art. 5, 6, 25, 28, 35, 44-49 |
| **NIS2** | Sécurité chaîne d'approvisionnement, notification incidents | Art. 21, 23 |
| **AI Act** | Transparence scoring IA, non-discrimination, droit à l'explication | Art. 6, 9, 13, 14 (si système à haut risque) |
| **HDS** | Hébergement données de santé sur infrastructure certifiée | Décret 2018-137 |
| **SecNumCloud** | Qualification ANSSI pour l'hébergement cloud souverain | Référentiel ANSSI v3.2 |

### 2.3 Contraintes de souveraineté (NON NÉGOCIABLES)

```
RÈGLE ABSOLUE : Aucune donnée ne doit transiter par un serveur ou service
contrôlé par une entité soumise au Cloud Act, FISA 702, ou toute loi
d'accès extraterritoriale non-européenne.

Concrètement :
- Pas d'AWS, GCP, Azure pour les données de scoring → OVHcloud SecNumCloud ou Scaleway
- Pas d'API OpenAI/Anthropic US directes → LLM self-hosted ou API via passerelle souveraine
- Pas de CDN Cloudflare US → alternatives européennes
- Chiffrement E2E avec clés gérées par Malakoff Humanis (HSM on-premise ou souverain)
- Logs et traces sur sol français exclusivement
```

---

## 3. ARCHITECTURE TECHNIQUE CIBLE

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                        │
│  Dashboard RSSI │ Vue COMEX │ Portail Fournisseurs │ Admin Console  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS / API Gateway (Kong)
┌───────────────────────────┴─────────────────────────────────────────┐
│                      API BACKEND (FastAPI / Python)                  │
│  Auth (Keycloak)  │  Scoring Engine  │  VRM Workflows  │  Reports   │
└──┬────────┬───────────┬──────────┬───────────┬──────────┬───────────┘
   │        │           │          │           │          │
┌──┴──┐ ┌──┴──┐   ┌───┴───┐  ┌──┴──┐   ┌───┴───┐  ┌──┴──────────┐
│ DB  │ │Redis│   │Vector │  │Queue│   │Object │  │  LLM Engine │
│Postgr│ │Cache│   │  DB   │  │Celery│  │Storage│  │  (Mistral/  │
│SQL  │ │     │   │Qdrant │  │+Redis│  │MinIO  │  │  LLaMA self │
│     │ │     │   │       │  │     │   │       │  │  -hosted)   │
└─────┘ └─────┘   └───────┘  └─────┘   └───────┘  └─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌───────┴───────┐
     │ AGENT OSINT │   │ AGENT DARK  │   │ AGENT Nth     │
     │ (Collecte   │   │ WEB MONITOR │   │ PARTY DETECT  │
     │ publique)   │   │ (légal)     │   │ (cartographie)│
     └─────────────┘   └─────────────┘   └───────────────┘
```

### 3.2 Principes architecturaux

1. **Microservices découplés** : chaque module est un service indépendant communiquant via message queue (Celery/Redis) et API REST
2. **Event-driven** : tout changement de score déclenche un événement propagé aux consumers (alerting, reporting, SIEM)
3. **Multi-tenant ready** : isolation des données par organisation pour future ouverture filiales/partenaires
4. **API-first** : chaque fonctionnalité est exposée via API REST documentée OpenAPI 3.1 avant d'avoir une UI
5. **Agentic-native** : les agents IA sont des citoyens de première classe, pas des add-ons

### 3.3 Composants d'infrastructure

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Compute** | Kubernetes (K3s ou OpenShift) sur OVHcloud SecNumCloud | Souveraineté + scalabilité |
| **Base de données** | PostgreSQL 16 + TimescaleDB (time series scores) | Performance + historique temporel |
| **Cache** | Redis 7 Cluster | Sessions, rate limiting, cache scoring |
| **Queue** | Celery + Redis Broker | Jobs asynchrones (scans, rapports, agents) |
| **Vector DB** | Qdrant (self-hosted) | RAG pour chatbot IA, recherche sémantique docs |
| **Object Storage** | MinIO (self-hosted) ou OVH Object Storage | Rapports PDF/PPT, scans archivés |
| **LLM** | Mistral Large / LLaMA 3.1 70B via vLLM | IA souveraine, pas de dépendance US |
| **API Gateway** | Kong OSS ou Traefik | Rate limiting, auth, routing, observabilité |
| **Auth** | Keycloak 24 (OIDC/SAML) | SSO entreprise, RBAC granulaire |
| **Monitoring** | Prometheus + Grafana + Loki | Observabilité complète stack |
| **CI/CD** | GitLab CI (self-hosted) | Pipeline sécurisé, SAST/DAST intégrés |

---

## 4. MODULES FONCTIONNELS DÉTAILLÉS

### 4.1 MODULE A — Scoring Externe (Security Rating)

**Objectif** : Évaluer automatiquement la posture cybersécurité de tout fournisseur à partir de données publiques uniquement accessibles légalement.

#### 4.1.1 Domaines d'analyse (8 domaines — fusion SSC + BoC enrichi)

| # | Domaine | Sources OSINT légales | Poids par défaut |
|---|---------|----------------------|------------------|
| D1 | **Sécurité Réseau** | Shodan API, Censys, nmap (passif), certificats CT logs | 15% |
| D2 | **Sécurité DNS** | DNS passif (DNSDB), SPF/DKIM/DMARC vérification, DNSSEC | 10% |
| D3 | **Sécurité Web** | Headers HTTP, TLS/SSL Labs API, CSP, HSTS, cookies | 15% |
| D4 | **Sécurité Email** | SPF, DKIM, DMARC, MTA-STS, BIMI, DANE, blacklists | 10% |
| D5 | **Cadence de Patching** | CVE matching via NVD/EUVD, version fingerprinting passif | 15% |
| D6 | **Réputation IP** | AbuseIPDB, VirusTotal (API gratuite), blacklists publiques, sinkhole feeds | 10% |
| D7 | **Fuites & Exposition** | Have I Been Pwned API, Dehashed (API légale), paste sites monitoring | 15% |
| D8 | **Présence Réglementaire** | Mentions légales, politique de confidentialité, certifications publiées | 10% |

#### 4.1.2 Collecte de données — Règles légales strictes

```python
"""
RÈGLES DE COLLECTE OSINT — CADRE LÉGAL STRICT
Toute collecte doit respecter :
1. Données PUBLIQUEMENT accessibles (pas de scraping derrière login)
2. Respect du robots.txt de chaque site
3. Rate limiting respectueux (max 1 req/sec par domaine)
4. Pas de scan actif intrusif (pas de nmap -sV agressif)
5. Utilisation d'APIs officielles avec clés enregistrées
6. Pas de collecte de données personnelles (emails individuels, etc.)
7. Base légale : intérêt légitime (art. 6.1.f RGPD) pour la sécurité
   de la chaîne d'approvisionnement (DORA art. 28)
8. Registre des traitements mis à jour pour chaque source OSINT
9. Durée de conservation : données brutes 90 jours, scores agrégés 3 ans
10. Droit d'opposition des fournisseurs évalués (processus documenté)
"""
```

#### 4.1.3 Modèle de scoring

```python
"""
ALGORITHME DE SCORING MH-CYBERSCORE

Score global : 0-1000 + grade A-F
Score par domaine : 0-100 + grade A-E

Formule de scoring global :
  score_global = Σ (score_domaine_i × poids_i × facteur_criticite_i)

Où :
  - score_domaine_i ∈ [0, 100] : score normalisé du domaine i
  - poids_i ∈ [0, 1] : pondération configurable (défauts ci-dessus)
  - facteur_criticite_i : multiplicateur basé sur la criticité des findings
    - Critique (CVSS ≥ 9.0) : ×2.0
    - Haute (CVSS 7.0-8.9) : ×1.5
    - Moyenne (CVSS 4.0-6.9) : ×1.0
    - Basse (CVSS < 4.0) : ×0.5

Mapping grade :
  A : 800-1000 (Excellent)
  B : 600-799  (Bon)
  C : 400-599  (Acceptable)
  D : 200-399  (Faible)
  F : 0-199    (Critique)

Normalisation par taille d'organisation :
  - Micro (< 10 salariés) : tolérance +15%
  - PME (10-250) : tolérance +10%
  - ETI (250-5000) : standard
  - Grand groupe (> 5000) : exigence +10%

Scoring IA prédictif (V2) :
  - breach_susceptibility = model.predict(features) → probabilité de breach
  - Entraîné sur données historiques CVE + incidents publics
  - Explicabilité : SHAP values pour chaque facteur contributif
"""
```

### 4.2 MODULE B — Vendor Risk Management (VRM)

#### 4.2.1 Workflow de gestion fournisseur

```
Onboarding → Tiering → Scoring initial → Monitoring continu → Alerting
     ↓                                         ↓
Questionnaire  ←→  Validation IA  →  Score combiné (outside-in + inside-out)
     ↓                                         ↓
Plan de remédiation → Suivi → Re-scoring → Rapport COMEX/Achats
     ↓
Dispute/Contestation → Arbitrage → Correction
```

#### 4.2.2 Fonctionnalités VRM

- **Portfolio management** : création de portfolios par criticité (Tier 1/2/3), secteur, type de prestation
- **Tiering automatique** : classification automatique basée sur le type de données accédées, la criticité métier, et le volume financier
- **Monitoring continu** : re-scan configurable (quotidien pour Tier 1, hebdo pour Tier 2, mensuel pour Tier 3)
- **Alerting multi-canal** : email, Slack, Teams (webhooks), ServiceNow ticket auto-créé, SIEM event
- **Dispute resolution** : workflow de contestation avec SLA configurable (défaut 48h), preuves uploadables, arbitrage documenté
- **Questionnaires** :
  - Templates pré-construits : RGPD, DORA, ISO 27001, NIST CSF, HDS, personnalisé
  - **IA Smart Answer** : auto-complétion basée sur les réponses passées et les documents du fournisseur (inspiré SSC Smart Answer avec 83% gain temps)
  - Scoring combiné outside-in (scan technique) + inside-out (questionnaire) avec pondération configurable
- **Plans de remédiation** : génération IA de recommandations prioritisées, suivi d'avancement, deadlines
- **Registre DORA** : registre d'informations des prestataires TIC conforme art. 28 DORA, exportable pour régulateur (ACPR)

### 4.3 MODULE C — Scoring Interne

#### 4.3.1 AD Rating (Active Directory)

- Agent léger déployé sur les DC Malakoff Humanis
- Analyse : comptes à privilèges, GPO, Kerberoasting exposure, délégations dangereuses, trusts, mots de passe faibles (via audit hash), comptes dormants
- Score 0-1000 par domaine AD + recommandations priorisées
- Comparateur temporel (timeshift) comme BoC AD Rating

#### 4.3.2 M365 Rating (Microsoft 365)

- Connecteur Graph API + Security & Compliance API
- Analyse : EntraID configuration, Conditional Access, MFA coverage, SharePoint/OneDrive permissions, Exchange Online protection, Defender configuration, Teams settings
- Score 0-1000 + grade + recommandations

#### 4.3.3 GRC/PSSI Rating (Gouvernance)

- Digitalisation de la PSSI Malakoff Humanis
- Tracking de conformité par contrôle (implémenté/partiel/non implémenté)
- Mapping multi-référentiel : ISO 27001, DORA, NIS2, HDS, RGPD
- Dashboard de maturité globale avec heat map par domaine

### 4.4 MODULE D — Reporting & Data Visualisation

**C'est le module différenciant.** Il doit combiner :
- La puissance analytique de SSC (drill-down profond, Power BI, ChatSSC)
- La lisibilité COMEX de BoC (rapports PPT brandés, note 0-1000 immédiate)

#### 4.4.1 Types de rapports

| Rapport | Audience | Format | Contenu |
|---------|----------|--------|---------|
| **Rapport Exécutif** | COMEX, Comité des Risques | PDF + PPT (auto-généré, brandé Malakoff Humanis) | Score global, top 5 risques, tendances, benchmark sectoriel |
| **Rapport RSSI** | RSSI, équipe SSI | Dashboard interactif + PDF détaillé | Tous les domaines, findings, recommandations, métriques SLA |
| **Rapport Fournisseur** | Direction Achats | PDF | Scorecard fournisseur, historique, plan de remédiation |
| **Rapport DORA** | Régulateur (ACPR) | Excel + PDF structuré | Registre prestataires TIC, incidents, tests résilience |
| **Rapport Benchmark** | RSSI, COMEX | Dashboard interactif | Position vs secteur assurance/mutuelle/santé |

#### 4.4.2 Spécifications Data Visualisation

```
DASHBOARD PRINCIPAL — VUE RSSI
├── Score global portfolio (gauge chart 0-1000 avec zones couleur)
├── Distribution des grades (bar chart A-F, comparaison M-1)
├── Top 10 fournisseurs à risque (table triable + sparklines tendance)
├── Heatmap par domaine × fournisseur (matrice colorée interactive)
├── Timeline des alertes (chronologie scrollable avec filtres)
├── Carte géographique des fournisseurs (mapping risque × localisation)
└── KPIs : score moyen, % améliorés, % dégradés, Tier 1 coverage

DASHBOARD COMEX — VUE EXÉCUTIVE
├── Score global unique (gros chiffre 0-1000 + grade A-F + tendance ↑↓)
├── Risque financier estimé (basé sur scoring × valeur contrat)
├── Top 3 actions requises (langage métier, pas technique)
├── Comparaison sectorielle (graphique radar vs benchmark)
└── Statut conformité DORA (% de couverture du registre)

DRILL-DOWN (inspiré SSC — du global à la preuve en 4 clics max)
Portfolio → Fournisseur → Domaine de risque → Finding → Preuve technique
  ↓            ↓              ↓                ↓           ↓
[Liste]    [Scorecard]    [Score + items]  [Description]  [IP/URL/Evidence]
```

### 4.5 MODULE E — Intégrations

| Système | Type d'intégration | Priorité | Description |
|---------|-------------------|----------|-------------|
| **ServiceNow** | API REST bidirectionnelle | P0 (MVP) | Création auto ticket incident/remédiation depuis alerte, sync CMDB fournisseurs |
| **Splunk** | Syslog + HEC (HTTP Event Collector) | P0 (MVP) | Push événements scoring vers SIEM, corrélation alertes |
| **Power BI** | API REST + connecteur custom | P1 (V1) | Export données pour tableaux de bord BI existants |
| **Active Directory** | Agent + LDAP/Graph | P1 (V1) | Scoring interne AD |
| **Microsoft 365** | Graph API + Security API | P2 (V2) | Scoring interne M365 |
| **Slack / Teams** | Webhooks | P1 (V1) | Alertes temps réel dans canaux dédiés |
| **JIRA** | API REST | P2 (V2) | Création tickets remédiation pour équipes projets |
| **Email (SMTP)** | Natif | P0 (MVP) | Notifications, rapports programmés |

---

## 5. PIPELINE AGENTIC AI

### 5.1 Architecture des Agents

MH-CyberScore utilise un système multi-agents orchestré, où chaque agent est un worker Celery spécialisé piloté par un LLM (Mistral/LLaMA self-hosted).

```
┌─────────────────────────────────────────────────────┐
│              ORCHESTRATOR AGENT (Chef d'orchestre)    │
│  Reçoit les missions, planifie, délègue, consolide   │
└──────┬──────────┬───────────┬──────────┬────────────┘
       │          │           │          │
┌──────┴───┐ ┌───┴────┐ ┌───┴────┐ ┌───┴──────────┐
│  OSINT   │ │ DARK   │ │  Nth   │ │  QUESTIONNAIRE│
│  AGENT   │ │ WEB    │ │ PARTY  │ │  AGENT        │
│          │ │ AGENT  │ │ AGENT  │ │               │
│ Scans    │ │ Monit. │ │ Supply │ │ Smart Answer  │
│ publics  │ │ légal  │ │ chain  │ │ + Validation  │
└──────────┘ └────────┘ └────────┘ └───────────────┘
       │          │           │          │
┌──────┴───┐ ┌───┴────┐ ┌───┴────┐ ┌───┴──────────┐
│  REPORT  │ │ CHAT   │ │ ALERT  │ │  COMPLIANCE   │
│  AGENT   │ │ AGENT  │ │ AGENT  │ │  AGENT        │
│          │ │        │ │        │ │               │
│ Génère   │ │ChatBot │ │ Détecte│ │ Mapping auto  │
│ PDF/PPT  │ │ Q&A IA │ │ anomal.│ │ DORA/NIS2     │
└──────────┘ └────────┘ └────────┘ └───────────────┘
```

### 5.2 Agent OSINT (Collecteur Public)

```python
"""
AGENT OSINT — Spécification

Mission : Collecter légalement toutes les données publiques disponibles
sur un fournisseur cible pour alimenter le scoring.

Outils disponibles (MCP tools) :
  - shodan_search(domain) → ports ouverts, services, banners
  - censys_search(domain) → certificats, services exposés
  - dns_resolve(domain) → A, AAAA, MX, NS, TXT, SPF, DKIM, DMARC, DNSSEC
  - ssl_check(domain) → grade TLS, certificat, chain, expiration
  - http_headers(url) → security headers (CSP, HSTS, X-Frame, etc.)
  - cve_search(cpe_string) → vulnérabilités connues (NVD + EUVD)
  - hibp_check(domain) → breaches associées au domaine
  - whois_lookup(domain) → registrant, dates, registrar
  - reputation_check(ip) → AbuseIPDB, VirusTotal, blacklists
  - ct_logs_search(domain) → certificats émis (Certificate Transparency)

Contraintes :
  - Max 1 requête/seconde par API externe
  - Respecter les quotas API (Shodan: 100 queries/mois gratuit, etc.)
  - Logger chaque requête avec timestamp, source, résultat
  - Timeout 30 secondes par requête
  - Retry 3 fois avec backoff exponentiel
  - Pas de scan actif intrusif (TCP connect scan uniquement via Shodan/Censys)

Output : JSON structuré par domaine de scoring, avec confidence score
et source attribution pour chaque finding.
"""
```

### 5.3 Agent Dark Web Monitor (Surveillance légale)

```python
"""
AGENT DARK WEB MONITOR — Spécification

Mission : Surveiller les fuites de données et mentions liées aux
fournisseurs évalués sur des sources publiques et semi-publiques.

Sources LÉGALES uniquement :
  - Have I Been Pwned API (breaches par domaine)
  - Dehashed API (credentials leaks — API payante légitime)
  - IntelX API (paste sites indexés)
  - GitHub/GitLab public repos (secrets exposés via regex patterns)
  - Google Dorks automatisés (documents exposés publiquement)
  - CERT-FR / ANSSI bulletins d'alertes
  - Flux RSS sécurité (BleepingComputer, SecurityWeek, etc.)

CE QUI EST INTERDIT :
  - Accès direct au dark web (.onion) sans autorisation légale
  - Achat de données volées
  - Utilisation de credentials fuités pour tests
  - Tout accès nécessitant un bypass d'authentification

Output : Alertes catégorisées (critique/haute/moyenne/info) avec
date de détection, source, description, et recommandation.
"""
```

### 5.4 Agent Nth-Party Detection

```python
"""
AGENT NTH-PARTY — Spécification (inspiré SSC SCDR)

Mission : Cartographier la chaîne de sous-traitance des fournisseurs
pour identifier les risques de concentration (DORA art. 28).

Méthode :
1. Analyse DNS/MX/headers pour identifier les providers cloud (AWS, Azure,
   GCP, OVH, etc.) utilisés par chaque fournisseur
2. Analyse des certificats TLS pour identifier les CDN et hébergeurs
3. Analyse des mentions légales et sous-traitants déclarés (scraping légal
   pages publiques "politique confidentialité" / "sous-traitants")
4. Croisement avec base de données interne des fournisseurs MH
5. Construction du graphe de dépendances N-1, N-2, N-3

Output :
  - Graphe de dépendances (format NetworkX exportable D3.js)
  - Concentration risk score : % du portfolio dépendant de chaque
    provider de rang N-2 (alerte si > 30%)
  - Visualisation : treemap ou sankey diagram des dépendances
"""
```

### 5.5 Agent Chat (ChatMH — inspiré ChatSSC)

```python
"""
AGENT CHAT — Spécification (ChatMH)

Mission : Chatbot IA permettant aux utilisateurs de poser des questions
en langage naturel sur les scores, fournisseurs et risques.

Architecture :
  - RAG (Retrieval Augmented Generation) sur la base Qdrant
  - Indexation de : scores, findings, rapports, questionnaires, PSSI,
    référentiels réglementaires (DORA, RGPD, NIS2)
  - LLM : Mistral Large self-hosted via vLLM

Exemples de questions supportées :
  - "Quels sont nos 5 fournisseurs les plus risqués ce mois-ci ?"
  - "Le fournisseur X est-il conforme DORA art. 28 ?"
  - "Montre-moi l'évolution du score de [fournisseur] sur 6 mois"
  - "Génère un rapport exécutif pour le prochain Comité des Risques"
  - "Quel est notre risque de concentration sur AWS ?"
  - "Combien de fournisseurs Tier 1 ont un score inférieur à C ?"

Contraintes :
  - Réponses sourcées avec lien vers le finding/score source
  - Pas d'hallucination : si l'info n'existe pas, dire "non disponible"
  - Traçabilité : chaque interaction loggée pour audit
  - Langue : français natif, anglais supporté
"""
```

### 5.6 Agent Report (Générateur de rapports)

```python
"""
AGENT REPORT — Spécification

Mission : Générer automatiquement des rapports professionnels brandés
Malakoff Humanis dans les formats demandés.

Capacités :
  - Génération PDF via WeasyPrint (templates HTML → PDF)
  - Génération PPTX via python-pptx (templates PowerPoint brandés)
  - Génération Excel via openpyxl (données tabulaires)
  - Personnalisation : logo MH, charte graphique, templates par audience

Templates pré-construits :
  1. Rapport Exécutif COMEX (5 slides max, scores, top risques, tendances)
  2. Rapport RSSI détaillé (PDF 20-50 pages, tous les findings)
  3. Scorecard Fournisseur (1 page, score + domaines + recommandations)
  4. Rapport DORA Registre (Excel structuré pour ACPR)
  5. Rapport Benchmark Sectoriel (comparaison anonymisée)

Automatisation :
  - Rapports programmables (cron) : hebdo RSSI, mensuel COMEX
  - Génération on-demand via ChatMH ou UI
  - Envoi automatique par email ou dépôt SharePoint
"""
```

---

## 6. MÉTHODOLOGIE DE SCORING

### 6.1 Principes fondamentaux

1. **Transparence totale** : chaque point de scoring est traçable jusqu'à la donnée source (AI Act art. 13)
2. **Explicabilité** : l'utilisateur peut comprendre pourquoi un score est tel qu'il est
3. **Contestabilité** : processus de dispute documenté avec SLA (AI Act art. 14)
4. **Non-discrimination** : pas de biais basé sur la taille, le secteur ou la nationalité
5. **Évolutivité** : les poids et facteurs sont configurables par l'administrateur

### 6.2 Cycle de scoring

```
Collecte (Agents OSINT) → Normalisation → Scoring par domaine
    → Agrégation pondérée → Score global → Grade → Stockage TimescaleDB
    → Événement (Celery) → Alerting si seuil dépassé
    → Comparaison M-1 → Tendance → Dashboard temps réel
```

### 6.3 Gestion des faux positifs

- Chaque finding a un statut : `open`, `acknowledged`, `disputed`, `resolved`, `false_positive`
- Le fournisseur peut uploader des preuves de contestation via le portail
- SLA de traitement : 48h ouvrées (configurable)
- Historique complet des disputes conservé 3 ans pour audit

---

## 7. DATA VISUALISATION & UX

### 7.1 Design System

```
Framework UI : Next.js 15 + React 19 + TypeScript strict
Composants : shadcn/ui (base) + composants custom MH-CyberScore
Charts : Recharts (principal) + D3.js (visualisations avancées)
Style : Tailwind CSS 4 avec design tokens Malakoff Humanis
Icons : Lucide React
Maps : Leaflet (open source, pas Google Maps)

Charte couleur (palette MH-CyberScore) :
  - Score A/Excellent : #27AE60 (vert)
  - Score B/Bon : #2ECC71 (vert clair)
  - Score C/Acceptable : #F39C12 (orange)
  - Score D/Faible : #E67E22 (orange foncé)
  - Score F/Critique : #C0392B (rouge)
  - Navy MH : #1B3A5C
  - Blue MH : #2E75B6
  - Background : #F7F9FA
  - Text : #2C3E50

Accessibilité : WCAG 2.2 AA minimum
Responsive : Desktop-first, tablet supporté, mobile read-only
Internationalisation : FR natif, EN supporté (i18next)
```

### 7.2 Pages principales

| Page | Route | Description | Rôle |
|------|-------|-------------|------|
| Dashboard RSSI | `/dashboard` | Vue d'ensemble portfolio complète | RSSI, SSI |
| Dashboard COMEX | `/executive` | Vue simplifiée exécutive | COMEX, Dir. |
| Liste fournisseurs | `/vendors` | Tableau triable/filtrable de tous les fournisseurs | Tous |
| Scorecard fournisseur | `/vendors/:id` | Vue détaillée d'un fournisseur | RSSI, Achats |
| Scoring détaillé | `/vendors/:id/scoring` | Drill-down par domaine → finding → preuve | SSI |
| Questionnaires | `/questionnaires` | Gestion des questionnaires envoyés/reçus | VRM |
| Rapports | `/reports` | Centre de reporting (génération + historique) | Tous |
| Alertes | `/alerts` | Flux d'alertes temps réel avec filtres | RSSI, SSI |
| Nth-Party Map | `/supply-chain` | Visualisation graphe de dépendances | RSSI |
| Registre DORA | `/compliance/dora` | Registre prestataires TIC DORA | DPO, Compliance |
| Chat IA | `/chat` | ChatMH — assistant IA cyber scoring | Tous |
| Admin | `/admin` | Configuration, utilisateurs, poids scoring | Admin |
| Portail Fournisseur | `/portal` | Accès fournisseur pour contestation/questionnaire | Externe |

---

## 8. SÉCURITÉ, CONFORMITÉ & SOUVERAINETÉ

### 8.1 Sécurité de l'application

```
AUTHENTIFICATION :
  - SSO via Keycloak (OIDC/SAML intégré AD Malakoff Humanis)
  - MFA obligatoire pour tous les comptes
  - Session timeout : 30 min inactivité, 8h max
  - API : JWT signé RS256, rotation clés 90 jours

AUTORISATION (RBAC) :
  - Admin : configuration complète, gestion utilisateurs
  - RSSI : lecture/écriture tous modules, validation disputes
  - Analyste SSI : lecture/écriture scoring + VRM
  - Direction Achats : lecture portfolios + rapports + questionnaires
  - COMEX : lecture dashboard exécutif + rapports
  - Fournisseur : accès portail limité (sa scorecard + contestation)

CHIFFREMENT :
  - Transport : TLS 1.3 exclusif (pas de fallback TLS 1.2)
  - Repos : AES-256-GCM pour toutes les données en base
  - Clés : gérées via HSM (Thales Luna ou équivalent souverain)
  - Secrets : HashiCorp Vault (self-hosted)

LOGGING & AUDIT :
  - Tous les accès authentifiés loggés (qui, quoi, quand, d'où)
  - Logs centralisés dans Loki, rétention 1 an minimum
  - Alertes SIEM automatiques sur comportements anormaux
  - Piste d'audit complète pour chaque modification de score

SÉCURITÉ DU CODE :
  - SAST : Semgrep dans pipeline CI
  - DAST : OWASP ZAP automatisé sur chaque déploiement staging
  - SCA : Trivy pour les dépendances et images Docker
  - Secret scanning : gitleaks dans pre-commit hooks
  - Code review obligatoire (2 reviewers dont 1 senior)
```

### 8.2 Conformité RGPD

- **AIPD** (Analyse d'Impact) réalisée avant mise en production
- **Base légale** : intérêt légitime (art. 6.1.f) pour la sécurité supply chain
- **Minimisation** : collecte uniquement données publiques nécessaires au scoring
- **Droit d'opposition** : processus documenté pour les fournisseurs évalués
- **Conservation** : données brutes 90 jours, scores agrégés 3 ans
- **Registre des traitements** : mis à jour à chaque nouvelle source OSINT

### 8.3 Conformité AI Act

- **Classification** : système IA à risque limité (scoring fournisseurs, pas RH ni crédit)
- **Transparence** : les fournisseurs sont informés qu'ils sont évalués par un système IA
- **Explicabilité** : SHAP values disponibles pour chaque facteur de scoring
- **Supervision humaine** : toute décision business (rejet fournisseur) nécessite validation humaine
- **Registre IA** : documentation technique de la méthodologie accessible

---

## 9. STACK TECHNIQUE & DÉPENDANCES

### 9.1 Backend

```toml
# pyproject.toml — dépendances principales
[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115"
uvicorn = {version = "^0.34", extras = ["standard"]}
sqlalchemy = "^2.0"
alembic = "^1.14"
psycopg = {version = "^3.2", extras = ["binary"]}
celery = {version = "^5.4", extras = ["redis"]}
redis = "^5.2"
pydantic = "^2.10"
pydantic-settings = "^2.7"
httpx = "^0.28"
python-jose = {version = "^3.3", extras = ["cryptography"]}
passlib = {version = "^1.7", extras = ["bcrypt"]}
python-multipart = "^0.0.18"
jinja2 = "^3.1"
weasyprint = "^63"       # Génération PDF
python-pptx = "^1.0"     # Génération PPTX
openpyxl = "^3.1"        # Génération Excel
qdrant-client = "^1.12"  # Vector DB
vllm = "^0.6"            # LLM inference
langchain = "^0.3"       # Orchestration agents
dnspython = "^2.7"       # DNS resolution
cryptography = "^44"     # TLS/crypto operations
```

### 9.2 Frontend

```json
// package.json — dépendances principales
{
  "dependencies": {
    "next": "^15.1",
    "react": "^19.0",
    "react-dom": "^19.0",
    "typescript": "^5.7",
    "@tanstack/react-query": "^5.62",
    "recharts": "^2.15",
    "d3": "^7.9",
    "zustand": "^5.0",
    "next-auth": "^5.0",
    "tailwindcss": "^4.0",
    "lucide-react": "^0.468",
    "i18next": "^24.2",
    "react-i18next": "^15.2",
    "leaflet": "^1.9",
    "react-leaflet": "^5.0",
    "zod": "^3.24",
    "@tanstack/react-table": "^8.20",
    "date-fns": "^4.1"
  }
}
```

### 9.3 Versionnement

- **Node.js** : ≥ 20 LTS
- **Python** : ≥ 3.12
- **PostgreSQL** : ≥ 16
- **Redis** : ≥ 7
- **Docker** : ≥ 27
- **Kubernetes** : ≥ 1.31

---

## 10. STRUCTURE DU MONOREPO

```
mh-cyberscore/
├── CLAUDE.md                          # CE FICHIER — contexte principal
├── README.md                          # Documentation publique
├── docker-compose.yml                 # Orchestration dev local
├── docker-compose.prod.yml            # Orchestration production
├── .env.example                       # Variables d'environnement template
├── .gitignore
├── .pre-commit-config.yaml
│
├── backend/                           # API Python FastAPI
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/                       # Migrations DB
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   ├── database.py                # SQLAlchemy engine + session
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   │   ├── vendor.py              # Fournisseur
│   │   │   ├── scoring.py             # Scores + findings
│   │   │   ├── questionnaire.py       # Questionnaires + réponses
│   │   │   ├── alert.py               # Alertes
│   │   │   ├── report.py              # Rapports générés
│   │   │   ├── user.py                # Utilisateurs + rôles
│   │   │   ├── audit.py               # Piste d'audit
│   │   │   └── dora_register.py       # Registre DORA
│   │   │
│   │   ├── schemas/                   # Pydantic schemas (API contracts)
│   │   │   ├── vendor.py
│   │   │   ├── scoring.py
│   │   │   ├── questionnaire.py
│   │   │   └── ...
│   │   │
│   │   ├── api/                       # Routes FastAPI
│   │   │   ├── v1/
│   │   │   │   ├── vendors.py
│   │   │   │   ├── scoring.py
│   │   │   │   ├── questionnaires.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── alerts.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── compliance.py
│   │   │   │   ├── integrations.py
│   │   │   │   └── admin.py
│   │   │   └── deps.py                # Dépendances (auth, db session)
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── scoring_engine.py      # Moteur de scoring
│   │   │   ├── vrm_service.py         # Workflow VRM
│   │   │   ├── report_generator.py    # Génération rapports
│   │   │   ├── alert_service.py       # Service d'alerting
│   │   │   └── compliance_service.py  # Conformité DORA/RGPD
│   │   │
│   │   ├── agents/                    # Agents IA (Celery workers)
│   │   │   ├── orchestrator.py        # Chef d'orchestre
│   │   │   ├── osint_agent.py         # Collecteur OSINT
│   │   │   ├── darkweb_agent.py       # Monitoring fuites
│   │   │   ├── nthparty_agent.py      # Détection Nth-party
│   │   │   ├── questionnaire_agent.py # Smart Answer IA
│   │   │   ├── report_agent.py        # Générateur rapports
│   │   │   ├── chat_agent.py          # ChatMH RAG
│   │   │   ├── alert_agent.py         # Détection anomalies
│   │   │   └── compliance_agent.py    # Mapping conformité
│   │   │
│   │   ├── tools/                     # Outils MCP pour agents
│   │   │   ├── shodan_tool.py
│   │   │   ├── censys_tool.py
│   │   │   ├── dns_tool.py
│   │   │   ├── ssl_tool.py
│   │   │   ├── cve_tool.py
│   │   │   ├── hibp_tool.py
│   │   │   ├── reputation_tool.py
│   │   │   └── ct_logs_tool.py
│   │   │
│   │   ├── templates/                 # Templates rapports
│   │   │   ├── reports/
│   │   │   │   ├── executive_report.html
│   │   │   │   ├── rssi_report.html
│   │   │   │   ├── vendor_scorecard.html
│   │   │   │   └── dora_register.html
│   │   │   └── emails/
│   │   │       ├── alert.html
│   │   │       └── report_ready.html
│   │   │
│   │   └── utils/
│   │       ├── crypto.py              # Chiffrement
│   │       ├── validators.py          # Validations métier
│   │       └── constants.py           # Constantes applicatives
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_scoring_engine.py
│   │   ├── test_agents/
│   │   ├── test_api/
│   │   └── test_services/
│   │
│   └── Dockerfile
│
├── frontend/                          # Next.js 15 App
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/                       # App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Redirect → /dashboard
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx           # Dashboard RSSI
│   │   │   ├── executive/
│   │   │   │   └── page.tsx           # Dashboard COMEX
│   │   │   ├── vendors/
│   │   │   │   ├── page.tsx           # Liste fournisseurs
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx       # Scorecard
│   │   │   │       └── scoring/
│   │   │   │           └── page.tsx   # Drill-down détaillé
│   │   │   ├── questionnaires/
│   │   │   ├── reports/
│   │   │   ├── alerts/
│   │   │   ├── supply-chain/
│   │   │   │   └── page.tsx           # Nth-party visualization
│   │   │   ├── compliance/
│   │   │   │   └── dora/
│   │   │   ├── chat/
│   │   │   │   └── page.tsx           # ChatMH
│   │   │   ├── admin/
│   │   │   └── portal/                # Portail fournisseur
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── charts/                # Composants graphiques custom
│   │   │   │   ├── ScoreGauge.tsx     # Jauge 0-1000
│   │   │   │   ├── GradeDistribution.tsx
│   │   │   │   ├── DomainHeatmap.tsx
│   │   │   │   ├── TrendSparkline.tsx
│   │   │   │   ├── RiskRadar.tsx
│   │   │   │   ├── SupplyChainGraph.tsx  # D3.js force graph
│   │   │   │   └── ConcentrationSankey.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Footer.tsx
│   │   │   └── shared/
│   │   │       ├── ScoreCard.tsx
│   │   │       ├── FindingRow.tsx
│   │   │       ├── AlertBanner.tsx
│   │   │       └── ChatWidget.tsx
│   │   │
│   │   ├── hooks/                     # Custom React hooks
│   │   │   ├── useScoring.ts
│   │   │   ├── useVendors.ts
│   │   │   ├── useAlerts.ts
│   │   │   └── useChat.ts
│   │   │
│   │   ├── lib/                       # Utilitaires
│   │   │   ├── api.ts                 # Client API (fetch wrapper)
│   │   │   ├── scoring-utils.ts       # Helpers scoring (grade → couleur, etc.)
│   │   │   └── constants.ts
│   │   │
│   │   ├── stores/                    # Zustand stores
│   │   │   ├── auth-store.ts
│   │   │   ├── vendor-store.ts
│   │   │   └── filter-store.ts
│   │   │
│   │   └── types/                     # TypeScript types
│   │       ├── vendor.ts
│   │       ├── scoring.ts
│   │       ├── api.ts
│   │       └── chart.ts
│   │
│   └── Dockerfile
│
├── agents/                            # Configuration agents autonome
│   ├── prompts/                       # System prompts des agents
│   │   ├── orchestrator.md
│   │   ├── osint_agent.md
│   │   ├── darkweb_agent.md
│   │   ├── nthparty_agent.md
│   │   ├── chat_agent.md
│   │   └── report_agent.md
│   └── config/
│       ├── agent_config.yaml          # Configuration des agents
│       └── tools_config.yaml          # Configuration des outils MCP
│
├── infra/                             # Infrastructure as Code
│   ├── kubernetes/
│   │   ├── base/
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── helm/
│   ├── terraform/                     # Provisioning OVHcloud
│   └── ansible/                       # Configuration serveurs
│
├── docs/                              # Documentation
│   ├── architecture/
│   │   ├── ADR/                       # Architecture Decision Records
│   │   ├── C4-diagrams/
│   │   └── data-model.md
│   ├── api/
│   │   └── openapi.yaml               # Spec OpenAPI 3.1
│   ├── compliance/
│   │   ├── AIPD.md                    # Analyse d'Impact RGPD
│   │   ├── AI_ACT_compliance.md
│   │   └── DORA_mapping.md
│   ├── runbooks/                      # Procédures opérationnelles
│   └── onboarding.md
│
└── scripts/                           # Scripts utilitaires
    ├── seed_db.py                     # Données de test
    ├── import_vendors.py              # Import CSV fournisseurs
    └── benchmark_scoring.py           # Benchmark performances scoring
```

---

## 11. STANDARDS DE CODE & CONVENTIONS

### 11.1 Python (Backend)

```python
# Conventions Python — MH-CyberScore
"""
- Python 3.12+ avec type hints PARTOUT
- Formatter : ruff format (line-length = 100)
- Linter : ruff check (règles : ALL sauf D203, D213)
- Type checker : mypy --strict
- Docstrings : Google style
- Tests : pytest avec coverage > 80%
- Nommage :
  - Classes : PascalCase (VendorScoring, OsintAgent)
  - Fonctions/méthodes : snake_case (calculate_score, fetch_dns_records)
  - Constantes : UPPER_SNAKE_CASE (MAX_RETRY_COUNT, SCORING_WEIGHTS)
  - Modules : snake_case (scoring_engine.py, osint_agent.py)
- Imports : ordonnés (stdlib, third-party, local) par isort
- Async : utiliser async/await pour toutes les I/O (httpx, DB queries)
- Error handling : exceptions custom héritant de MHCyberScoreError
"""
```

### 11.2 TypeScript (Frontend)

```typescript
// Conventions TypeScript — MH-CyberScore
/*
- TypeScript strict mode (noImplicitAny, strictNullChecks, etc.)
- ESLint + Prettier (semi: false, singleQuote: true, trailingComma: all)
- Composants : React Server Components par défaut, Client uniquement si interactif
- State management : Zustand (global), React Query (server state)
- Nommage :
  - Composants : PascalCase (ScoreGauge.tsx, VendorList.tsx)
  - Hooks : useCamelCase (useScoring, useVendors)
  - Types/Interfaces : PascalCase avec suffixe si nécessaire (VendorScore, ApiResponse)
  - Utils : camelCase (calculateGrade, formatScore)
- Props : toujours typées avec interface dédiée
- Pas de `any` sauf cas exceptionnel documenté
- Tests : Vitest + Testing Library
*/
```

### 11.3 Git Conventions

```
Branches :
  main          → production (protégée, merge via MR uniquement)
  develop       → intégration continue
  feature/*     → nouvelles fonctionnalités
  fix/*         → corrections de bugs
  hotfix/*      → corrections urgentes production

Commits (Conventional Commits) :
  feat(scoring): add DNS domain analysis
  fix(api): correct vendor tiering logic
  docs(agents): document OSINT collection rules
  test(scoring): add unit tests for grade calculation
  chore(deps): update FastAPI to 0.115.6
  refactor(frontend): extract ScoreGauge component
  security(auth): enforce MFA on admin routes

Merge Requests :
  - Template obligatoire avec description, screenshots, tests ajoutés
  - 2 reviewers minimum dont 1 senior
  - CI/CD passant (tests + lint + security scan)
  - Squash merge sur develop, merge commit sur main
```

---

## 12. PLAN DE DÉVELOPPEMENT PAR SPRINTS

### Phase 1 — MVP (Sprints 1-6, T0+3 mois)

| Sprint | Durée | Livrables |
|--------|-------|-----------|
| S1 | 2 sem | Infra : monorepo, Docker Compose, DB schema, auth Keycloak, CI/CD |
| S2 | 2 sem | Backend : API CRUD vendors + scoring models + migrations Alembic |
| S3 | 2 sem | Agent OSINT v1 : DNS, SSL, HTTP headers, CVE check (5 outils) |
| S4 | 2 sem | Scoring Engine v1 : calcul 8 domaines, grade, stockage TimescaleDB |
| S5 | 2 sem | Frontend : Dashboard RSSI, liste vendors, scorecard vendor, drill-down |
| S6 | 2 sem | Intégrations P0 : alerting email, ServiceNow ticket, Splunk event push |

### Phase 2 — V1 (Sprints 7-12, T0+6 mois)

| Sprint | Durée | Livrables |
|--------|-------|-----------|
| S7 | 2 sem | VRM workflows : onboarding, tiering, monitoring continu, dispute |
| S8 | 2 sem | Questionnaires : templates RGPD/DORA, envoi/réception, scoring combiné |
| S9 | 2 sem | Agent Report : PDF/PPTX génération, templates brandés MH |
| S10 | 2 sem | Dashboard COMEX + benchmark sectoriel + rapports programmés |
| S11 | 2 sem | Agent Dark Web Monitor + alerting enrichi (Slack/Teams webhooks) |
| S12 | 2 sem | Portail fournisseur + contestation + DORA registre v1 |

### Phase 3 — V2 (Sprints 13-18, T0+9 mois)

| Sprint | Durée | Livrables |
|--------|-------|-----------|
| S13-14 | 4 sem | Agent Nth-Party : cartographie supply chain, graphe D3.js, concentration risk |
| S15-16 | 4 sem | ChatMH : RAG Qdrant + Mistral, interface chat, requêtes naturelles |
| S17-18 | 4 sem | Smart Answer IA questionnaires + Power BI connecteur + API bulk |

### Phase 4 — V3 (Sprints 19-24, T0+12 mois)

| Sprint | Durée | Livrables |
|--------|-------|-----------|
| S19-20 | 4 sem | AD Rating : agent interne, scoring AD, dashboard |
| S21-22 | 4 sem | M365 Rating : Graph API, scoring EntraID/Exchange/Teams/SharePoint |
| S23-24 | 4 sem | GRC/PSSI : digitalisation PSSI, mapping multi-référentiel, heat map maturité |

---

## 13. TESTS & QUALITÉ

```
STRATÉGIE DE TEST :

Unit Tests (>80% coverage) :
  - Scoring engine : chaque domaine, chaque formule, edge cases
  - Agents : mock des APIs externes, validation parsing
  - API : chaque endpoint, validation schemas, permissions RBAC
  - Frontend : composants critiques (ScoreGauge, charts)

Integration Tests :
  - API → DB : CRUD complet avec transactions
  - Agents → Scoring → Alerting : pipeline complet
  - Auth flow : Keycloak → JWT → route protégée

E2E Tests (Playwright) :
  - Parcours RSSI : login → dashboard → vendor → drill-down → export rapport
  - Parcours Achats : login → vendor → questionnaire → rapport
  - Parcours Fournisseur : portail → contestation → upload preuve

Performance Tests (Locust) :
  - 100 utilisateurs simultanés sur dashboard
  - Scoring de 500 fournisseurs en parallèle < 10 min
  - Génération rapport PPTX < 15 secondes

Security Tests :
  - OWASP Top 10 : automatisé via ZAP
  - RBAC : vérification exhaustive des permissions
  - Injection : SQL, XSS, SSRF (fuzzing automatisé)
  - API : rate limiting, auth bypass, IDOR
```

---

## 14. DÉPLOIEMENT & INFRASTRUCTURE

```yaml
# Environnements
dev:        Local Docker Compose (poste développeur)
staging:    OVHcloud SecNumCloud (réplique production 1:1)
production: OVHcloud SecNumCloud (HA, backup, monitoring)

# Stratégie de déploiement
- Blue/Green deployment via Kubernetes
- Rollback automatique si health check échoue
- Migrations DB : Alembic avec pré-vérification backward compatibility
- Feature flags : pour déploiement progressif des agents IA
- Backup : PostgreSQL WAL archiving + daily snapshot MinIO
- RTO : 4 heures | RPO : 1 heure
- Monitoring : Prometheus + Grafana + PagerDuty (astreinte RSSI)
```

---

## 15. GLOSSAIRE & RÉFÉRENCES

### Glossaire

| Terme | Définition |
|-------|-----------|
| **OSINT** | Open Source Intelligence — renseignement en sources ouvertes |
| **VRM** | Vendor Risk Management — gestion des risques fournisseurs |
| **SCDR** | Supply Chain Detection & Response (concept SSC) |
| **Nth-Party** | Sous-traitant de rang N (N-1 = direct, N-2 = sous-traitant du sous-traitant) |
| **Finding** | Constat technique individuel contribuant au scoring |
| **Scorecard** | Fiche de notation d'un fournisseur |
| **Tiering** | Classification des fournisseurs par niveau de criticité |
| **RAG** | Retrieval Augmented Generation — IA avec recherche documentaire |
| **HSM** | Hardware Security Module — module matériel de gestion des clés |
| **HDS** | Hébergement de Données de Santé (certification française) |

### Références documentaires

- DORA Regulation : [Règlement (UE) 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554)
- RGPD : [Règlement (UE) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679)
- AI Act : [Règlement (UE) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689)
- NIS2 : [Directive (UE) 2022/2555](https://eur-lex.europa.eu/eli/dir/2022/2555)
- SecurityScorecard Methodology Deep Dive 3.0 : [securityscorecard.com](https://securityscorecard.com/wp-content/uploads/2025/06/MethodologyDeepDive-3.0-Ebook_14.pdf)
- Board of Cyber Documentation : [boardofcyber.io](https://www.boardofcyber.io/fr)
- OWASP Top 10 2024 : [owasp.org](https://owasp.org/Top10/)
- Shodan API : [developer.shodan.io](https://developer.shodan.io)
- Censys API : [search.censys.io/api](https://search.censys.io/api)
- NVD API : [nvd.nist.gov](https://nvd.nist.gov/developers)
- EUVD : [euvd.enisa.europa.eu](https://euvd.enisa.europa.eu)

---

## INSTRUCTIONS POUR CLAUDE CODE

```
QUAND TU TRAVAILLES SUR CE PROJET :

1. LIS CE FICHIER EN ENTIER avant de commencer tout développement
2. Respecte STRICTEMENT les conventions de code (section 11)
3. Respecte STRICTEMENT les contraintes de souveraineté (section 8)
4. Chaque fichier créé doit avoir des docstrings/commentaires expliquant son rôle
5. Chaque endpoint API doit avoir sa spec OpenAPI documentée
6. Chaque agent doit avoir des tests unitaires avec mocks des APIs externes
7. JAMAIS de secrets en dur dans le code — utilise les variables d'environnement
8. JAMAIS d'import direct d'un service US non autorisé (voir section 2.3)
9. Pour le frontend : Server Components par défaut, Client Component uniquement si interactif
10. Pour les agents : chaque tool MCP doit avoir un timeout, retry et logging
11. Quand tu crées un nouvel agent, crée aussi son system prompt dans agents/prompts/
12. Documente chaque ADR (Architecture Decision Record) dans docs/architecture/ADR/
13. En cas de doute sur un choix technique, priorise : souveraineté > sécurité > performance > fonctionnalité
```

---

*Document rédigé par la RSSI/DPO Malakoff Humanis — Février 2026*
*Classification : Confidentiel — Usage interne — Projet MH-CyberScore*
