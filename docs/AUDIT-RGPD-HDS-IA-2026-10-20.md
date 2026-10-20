# Audit RGPD, HDS et IA médicale — Packs SOS (20/10/2026)

**Périmètre** : application telle qu'elle existe sur la branche `ia` (v41w) et en production (v41k, même architecture). Audit sans modification de code, sans envoi de donnée réelle. Aucun secret, aucune clé, aucune donnée patient dans ce rapport.
**Lecture** : ✅ vérifié dans le code · ⚠ point de vigilance vérifié dans le code · ❓ à vérifier contractuellement ou réglementairement (hors code).

---

## Mission 1 — Audit de l'application actuelle

### 1.1 Où sont les données patients
| Donnée | Où | Protection | Constat |
|---|---|---|---|
| Journal de garde (nom, naissance, âge, fiche, lieu, heures, cotation, notes dont alertes « maintien » et décisions) | `localStorage` du navigateur, clé `sos_journal_enc` | AES-256-GCM, clé dérivée du code personnel (PBKDF2-SHA-256, 120 000 itérations) | ✅ chiffré ; ⚠ purge seulement sur action (bouton de purge par ancienneté) : pas de durée de conservation automatique |
| Brouillon de la consultation en cours (observation, dictée, documents, photos par identifiant) | `sos_draft_enc` | idem | ✅ chiffré, 12 h |
| Dictées récentes | `sos_dicthist_enc` | idem | ✅ chiffré, 48 h, 30 au plus |
| Patients validés / mis de côté (instantané complet du dossier, compte rendu) | `sos_validhist_enc` | idem | ✅ chiffré, 12 h |
| Tournée (adresses, noms, naissance, téléphone, motif, contre-appel, analyse IA du contre-appel) | `sos_tour_enc` | idem | ✅ chiffré ; ⚠ aucune purge automatique des arrêts faits (à vérifier à l'usage) |
| Photos et captures de fiches de régulation | IndexedDB `packs-sos-photos` | chiffrées image par image avec la même clé | ✅ chiffré, purge à 14 jours |
| Demandes IA en attente (hors ligne) | `sos_aiq_enc` | idem | ✅ chiffré, 48 h |
| Consommation IA (dates, modèle, jetons, coût, clé de garde) | `sos_ai_use_enc` | idem | ✅ sans contenu, 400 jours |
| Clé API Anthropic | `sos_ai_enc` ; copie dans `profil.json` publié sur le site | AES-256-GCM par le code personnel ; profil : AES-256-GCM, PBKDF2 600 000 itérations, phrase maître de 6 mots (~48 bits) | ✅ jamais en clair ; ⚠ le profil chiffré est public (dépôt GitHub public) : la sécurité repose sur la phrase maître |
| Clé de session | `localStorage` `sos_sess` (clé AES exportée, base64) pendant 20 min d'inactivité au plus | — | ⚠ clé de chiffrement **en clair** sur l'appareil pendant la session (pour ne pas redemander le code au rechargement) ; protégée seulement par le verrouillage de l'iPhone et l'isolement du navigateur |
| Réglages non sensibles (thème, Express, cotations, tarifs, plannings, base des médicaments) | `localStorage` en clair | — | ✅ pas de donnée patient ; `sos_uid_hint` = identifiant du médecin en clair |
| Sauvegarde manuelle (fichier) | fichier exporté par le médecin | AES-256-GCM, PBKDF2, mot de passe de sauvegarde | ✅ chiffré ; ❓ lieu où le médecin dépose ce fichier (iCloud, ordinateur) = hébergement de données de santé chiffrées, à qualifier avec le DPO |
| Documents imprimés (PDF) | produits en mémoire, partagés via la feuille de partage iOS (AirPrint, Fichiers) | — | ✅ rien n'est conservé par l'application ; ⚠ ce que le médecin fait du PDF (Fichiers, Mail) sort du périmètre |
| Serveur | **aucun** : site statique GitHub Pages, aucune base de données distante | — | ✅ |

Code personnel : 4 à 6 chiffres. Avec 120 000 itérations, un code de 4 chiffres se force en quelques secondes **si l'attaquant obtient le stockage du navigateur** (iPhone déverrouillé ou extraction) : la sécurité réelle repose sur le verrouillage de l'iPhone. ⚠ Recommandation : 6 chiffres au minimum, ou phrase.

### 1.2 Données envoyées automatiquement sur Internet (vérifié dans le code : hôtes réellement appelés)
| Service | Quand | Ce qui part | Constat |
|---|---|---|---|
| `api.anthropic.com` (Claude) | après une dictée ou un contre-appel, **seulement après « Envoyer »** sur l'écran « Ce qui part » (v41w) ; relecture du compte rendu et courrier à la demande | texte **pseudonymisé** sur l'appareil + contexte clinique (âge, sexe, poids, grossesse, allergies, traitements, lieu), consignes fixes, liste des noms de fiches | ⚠ hors UE, voir Mission 3 |
| `api-adresse.data.gouv.fr` (BAN, État français) | import d'une fiche de régulation, ajout d'une adresse | **adresse du patient** (texte) | ⚠ service public sans contrat ; journaux possibles côté serveur |
| `router.project-osrm.org` (serveur de démonstration OSRM, tiers) | ordre de tournée, trajets | **coordonnées GPS** des adresses des patients et du cabinet ; pas de nom | ⚠ tiers sans contrat ni engagement, usage « démo » ; les coordonnées permettent de retrouver les adresses |
| `tile.openstreetmap.org` | affichage de la carte de tournée | tuiles de carte (zone), adresse IP | ⚠ faible |
| Google Maps, Waze, Apple Plans (liens) | quand le médecin touche « Naviguer » | **adresse du patient** transmise à l'application de navigation choisie | ⚠ inévitable pour naviguer ; choix du médecin |
| Google Sheets (Apps Script) — **synchronisation facultative, désactivée par défaut** | si configurée | lignes du journal : numéro, code patient, heures, lieu, cotation, **nom de la fiche (= motif médical)** ; nom et naissance chiffrés par une phrase secrète | ⚠ hors périmètre HDS ; ne pas activer avec des données réelles sans DPA et avis du DPO |
| Dictée du clavier iPhone (Apple) | à chaque dictée vocale | audio ou texte selon le réglage iOS (« dictée sur l'appareil » disponible en français sur les iPhone récents) | ❓ hors application : à régler et vérifier dans iOS (Réglages → Général → Clavier → Dictée) |
| GitHub Pages | chargement de l'application et du profil chiffré | adresse IP, agent utilisateur | ✅ aucune donnée patient |
| Aucun script tiers, aucun outil d'analyse d'audience, aucune police externe | — | — | ✅ |

### 1.3 Ce qui est transmis à l'API Claude (vérifié)
- Le texte envoyé est produit par `anonymize()` : nom, prénom, personnes citées, adresses, téléphones, NIR, courriels, dates exactes (remplacées par des dates relatives), date de naissance (remplacée par l'âge), noms propres et lieux précis sont remplacés par des jetons ; les villes de l'agglomération d'Orléans restent en clair (choix du 15/10/2026). Contrôle `anonLeaks` avant envoi ; en cas de reste d'identité, l'envoi est bloqué.
- Partent en clair : âge, sexe, poids, grossesse, allaitement, allergies, traitements habituels, lieu (visite/cabinet), le texte clinique (symptômes, antécédents, examen, diagnostic), le motif de régulation, les noms de fiches du Pack.
- Ne partent jamais : images, photos, PDF, documents produits, journal, clé API dans le corps (en-tête HTTP seulement).
- **Statut RGPD** : un texte clinique pseudonymisé reste une donnée de santé à caractère personnel (le médecin peut réidentifier ; l'ensemble âge + ville + tableau clinique rare peut suffire). La pseudonymisation réduit le risque, elle ne crée pas de donnée anonyme.

### 1.4 Clé API Claude
Stockée chiffrée (code personnel) sur l'appareil, et chiffrée (phrase maître) dans `profil.json` publié sur le site pour les autres appareils ; jamais dans la sauvegarde ni dans la synchronisation. L'appel est fait **directement depuis le navigateur** avec l'en-tête `anthropic-dangerous-direct-browser-access`, c'est-à-dire que la clé est présente en mémoire du navigateur à chaque appel et qu'aucun serveur du médecin ne la protège. ⚠ Acceptable pour un usage strictement personnel sur un appareil verrouillé ; **non adapté à plusieurs médecins** (voir `docs/RELAIS-API-PROPOSITION.md`).

### 1.5 Journaux, caches, outils d'analyse, sauvegardes
- Console du navigateur : seuls des messages techniques (`console.warn("brouillon", e)`…), jamais de contenu patient. ✅
- Cache du service worker : fichiers de l'application seulement (html, js, images, OCR) ; aucune donnée patient. ✅
- Historique de navigation : l'application est une page unique sans paramètre d'URL contenant des données. ✅
- Sauvegarde iCloud de l'iPhone : le stockage de Safari (localStorage, IndexedDB) **peut être inclus dans la sauvegarde iCloud du téléphone** (données chiffrées par l'application, mais hébergées chez Apple). ❓ à qualifier (sauvegarde iCloud chiffrée de bout en bout activée ou non).
- Sauvegarde manuelle de l'application : fichier chiffré, voir 1.1.

### 1.6 Dictée, captures, IA (fonctionnement vérifié)
- Dictée : micro du clavier iOS dans un champ texte ; l'application ne capte jamais l'audio (aucun `getUserMedia`, aucun `SpeechRecognition`) ; le texte est enregistré chiffré à chaque frappe. Le traitement de la voix dépend d'Apple (voir 1.2).
- Captures de fiches de régulation : lecture OCR **sur l'appareil** (Tesseract servi par le site, exécuté dans le navigateur) ; l'image chiffrée reste locale 14 jours ; seules l'adresse (BAN) puis les coordonnées (OSRM) sortent.
- IA : préparation locale (pseudonymisation, contrôle de fuite), écran « Ce qui part », envoi après geste du médecin (v41w), réponse réintégrée localement avec garde-fous (nombres absents de l'envoi écartés, posologies jamais appliquées, jetons inconnus refusés), synthèse à valider, journal des modifications acceptées.

### 1.7 Services tiers et réutilisation possible des données
| Tiers | Rôle | Réutilisation / conservation | Statut |
|---|---|---|---|
| Anthropic | IA | conditions de l'API (conservation, entraînement, ZDR, localisation) | ❓ Mission 3 |
| Apple | dictée vocale, sauvegarde iCloud, feuille de partage | selon réglages iOS et conditions Apple | ❓ |
| Etalab (BAN) | géocodage | journaux de service public | ❓ |
| OSRM (serveur de démonstration) | itinéraires | aucun engagement | ⚠ à remplacer |
| OpenStreetMap | tuiles | politique OSMF | ⚠ faible |
| Google / Waze / Apple | navigation | conditions des applications | ⚠ choix du médecin |
| Google (Apps Script) | synchronisation facultative | conditions Google | ⚠ désactivée par défaut |
| GitHub | hébergement du site et du profil chiffré | journaux d'accès | ✅ pas de donnée patient |

### 1.8 Risques classés
1. **Flux hors UE vers l'IA sans cadre contractuel vérifié** (données de santé pseudonymisées) — à traiter avant toute donnée nominative : Mission 3.
2. **Clé de session en clair 20 minutes** et code à 4 chiffres possible — dépend du verrouillage de l'iPhone ; à durcir (6 chiffres, session plus courte, ou authentification biométrique WebAuthn).
3. **Adresses et coordonnées des patients vers des services sans contrat** (BAN, OSRM démo) — remplacer OSRM par un service sous contrat (ou calcul local), documenter BAN.
4. **Synchronisation Google Sheets** — à laisser désactivée ou à supprimer tant qu'aucun DPA n'existe.
5. **Sauvegarde iCloud du téléphone** et fichier de sauvegarde — hébergement de données chiffrées à qualifier.
6. **Dictée Apple** — activer la dictée sur l'appareil et le vérifier.
7. Absence de purge automatique du journal et des arrêts de tournée — définir des durées.
8. Profil chiffré public — acceptable avec une phrase maître forte ; proposer une phrase plus longue.


---

## Mission 2 — Architecture cible conforme (données locales, IA sécurisée)

### 2.1 Principes
1. **Le dossier reste sur l'appareil du médecin**, chiffré comme aujourd'hui (AES-256-GCM, clé dérivée d'un secret du médecin) ; rien n'est hébergé « pour le compte d'un tiers » tant qu'aucun serveur ne conserve de donnée patient.
2. **Tout ce qui sort passe par un relais sous contrat** (voir `docs/RELAIS-API-PROPOSITION.md`), hébergé en France ou dans l'EEE, qui ne conserve rien : il authentifie le médecin, garde les clés des fournisseurs, journalise des métadonnées, applique les quotas.
3. **Pseudonymisation sur l'appareil avant tout envoi** (déjà en place) ; elle réduit le risque mais **ne dispense pas** du cadre RGPD : la donnée reste une donnée de santé.
4. **Fournisseurs d'IA et de transcription** : contrat de sous-traitance (article 28), engagement de non-entraînement, conservation nulle ou minimale documentée, traitement dans l'EEE ou transfert encadré ; pour un stockage, certification HDS ; pour un simple transit sans conservation, l'HDS n'est pas exigée mais reste un gage (voir Mission 3 et avis du DPO).
5. **Sauvegarde** : fichier chiffré par le médecin (déjà) déposé sur un espace sous contrat (HDS si données de santé stockées durablement chez un tiers) ou conservé hors ligne ; récupération par la phrase de sauvegarde ; test de restauration périodique.
6. **Hors ligne** : tout ce qui n'exige pas l'IA fonctionne déjà sans réseau (fiches, documents, impression, journal, tournée avec estimation locale) ; les demandes IA attendent le réseau.
7. **Suppression** : durées définies et appliquées automatiquement (brouillon 12 h, dictées 48 h, patients validés 12 h, photos 14 jours existent ; à ajouter : journal de garde, arrêts de tournée, enregistrements audio temporaires).

### 2.2 Schéma
```
iPhone / iPad / PC (navigateur, données chiffrées localement)
  ├─ Packs (fiches, documents, journal, tournée)            — hors ligne
  ├─ Pseudonymisation + contrôle de fuite                     — sur l'appareil
  ├─ Dictée clavier (Apple, réglage « sur l'appareil ») ou, à terme, capture audio locale
  └─ HTTPS + jeton du médecin ─► RELAIS (France/EEE, sans stockage, journal de métadonnées, quotas)
                                   ├─► IA de rédaction (contrat 28, non-entraînement, ZDR, EEE ou transfert encadré)
                                   └─► transcription vocale (idem), audio supprimé après transcription
Sauvegarde : fichier chiffré → espace sous contrat (HDS si conservation chez un tiers) ou support local.
```

### 2.3 Obligations à prévoir (à confirmer par le DPO, voir Mission 3 et questions en Mission 6)
- Information des patients (affichage au cabinet, mention sur les documents remis, information orale en visite) sur le traitement informatique, l'usage d'une IA d'aide à la rédaction et, le cas échéant, l'enregistrement de la consultation ; droit d'opposition et possibilité de consulter sans IA ni enregistrement.
- Registre des traitements de l'association ou du cabinet : finalités, catégories, destinataires (fournisseurs d'IA, de transcription, relais), transferts, durées.
- Analyse d'impact (AIPD) : probable pour un traitement de données de santé avec IA et enregistrement vocal ; l'exemption « professionnel de santé exerçant à titre individuel » doit être vérifiée au regard du recours à l'IA et à l'enregistrement.
- Contrats : sous-traitance avec chaque fournisseur (relais, IA, transcription, hébergeur de sauvegarde) ; clauses de transfert hors EEE si nécessaire.
- Sécurité : PGSSI-S (authentification, journalisation, chiffrement, sauvegarde, effacement), politique de durées, procédure en cas de perte du téléphone (verrouillage, révocation du jeton, restauration).

---

## Mission 5 — Assistant vocal de consultation (étude, rien développé)

### 5.1 Parcours
1. Le médecin informe le patient (formule courte, affichage) ; le patient peut refuser : la consultation se fait alors sans enregistrement, la dictée actuelle reste disponible. Le choix est tracé (« enregistrement : oui / refusé »).
2. Un seul geste « ● Écouter » ; capture audio locale dans le navigateur (API MediaRecorder, disponible sur Safari iOS récent) par segments courts gardés **en mémoire chiffrée**, jamais écrits en clair.
3. Transcription : soit sur l'appareil (reconnaissance iOS « sur l'appareil » quand disponible, ou un modèle Whisper allégé dans le navigateur — lourd sur iPhone, à évaluer), soit par le relais vers un service de transcription sous contrat (EEE, non-conservation) ; retour du texte seul.
4. Le texte transcrit alimente le même champ que la dictée actuelle (`state.obs.dict`) : la chaîne existante (pseudonymisation, « Ce qui part », synthèse, garde-fous, validation) est inchangée. L'IA distingue les propos du patient (rapportés) et ceux du médecin (constatés) : le prompt « plan » sait déjà séparer rapporté et constaté.
5. Le médecin vérifie, corrige (champs protégés contre l'écrasement) et valide ; le compte rendu est enregistré localement comme aujourd'hui.
6. **Audio** : supprimé dès la transcription réussie (ou après un délai court documenté, par exemple 10 minutes en cas d'échec réseau, puis suppression) ; jamais inclus dans le brouillon, la sauvegarde ni la synchronisation ; aucune écoute différée.
7. Journal : horodatage de l'enregistrement, durée, consentement/information, suppression.

### 5.2 Conditions avant de développer
- Avis DPO/CNOM sur l'enregistrement de la consultation (base légale, information, opposition), AIPD.
- Fournisseur de transcription sous contrat (EEE, non-conservation) ou transcription locale validée en qualité (français médical, bruit de domicile).
- Essai sur appareil réel : qualité micro en visite, autonomie, coupures réseau.
- Coût : Mission 4.
