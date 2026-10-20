# Audit RGPD, HDS et IA médicale — Packs SOS (20/10/2026)

**Périmètre** : application telle qu'elle existe sur la branche `ia` (v41w ; v41x n'ajoute que des fiches, sans changement d'architecture) et en production (v41k, même architecture). Audit sans modification de code, sans envoi de donnée réelle. Aucun secret, aucune clé, aucune donnée patient dans ce rapport.
**Méthode** : lecture du code (Mission 1), puis trois recherches documentaires du 20/10/2026 (conditions Anthropic et clouds ; cadre RGPD, HDS, CNIL, HAS, AI Act, règlement DM ; offres d'IA et de transcription hébergées en France ou dans l'EEE, tarifs publics). Chaque fait porte sa source et sa date ; « non trouvé » signifie qu'aucun texte officiel n'a été localisé.
**Classement** : *conforme* / *non conforme* / *à vérifier* (contrat, DPO, autorité), repris dans le tableau de la Mission 6.
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

### 2.3 Certifications et contrats exigibles, intervenant par intervenant (recherche du 20/10/2026, à confirmer par le DPO)
| Intervenant | HDS exigée ? | Fondement | Contrat |
|---|---|---|---|
| Appareils du médecin (iPhone, PC) : dossier chiffré, aucun prestataire | **Non** (hébergement pour son propre compte) | L.1111-8 I, R.1111-8-8 CSP ; FAQ ANS (auto-hébergement) | — ; PGSSI-S, registre, information des patients |
| Relais (passerelle) qui ne conserve rien (ni journal de contenu, ni cache) | Non exigée a priori (pas d'activité des 1° à 6° de R.1111-9 ; prise en charge de courte durée exclue par R.1111-8-8) ; **aucune position ANS trouvée** → à faire qualifier | R.1111-8-8, R.1111-9 | sous-traitance art. 28 avec l'hébergeur du relais ; hébergeur certifié HDS recommandé par prudence |
| Fournisseur d'IA qui conserve les requêtes (30 jours par défaut chez Anthropic) | **À trancher** : conservation de données de santé pour le compte du médecin ; si qualifiée d'hébergement, stockage hors EEE exclu (R.1111-9-1, décret 2026-209) et certificat HDS obligatoire | L.1111-8, R.1111-9-1 ; ANS : la pseudonymisation « n'a pas d'impact sur l'obligation de certification » | art. 28 + clauses de transfert (CCT) + clause de secret professionnel (guide HAS/CNIL, p. 20) |
| Fournisseur d'IA ou de transcription en conservation nulle (ZDR) | Non exigée si rien n'est conservé (même raisonnement que le relais) ; position officielle **non trouvée** | idem | art. 28, engagement écrit de non-conservation et de non-entraînement |
| Transcription vocale : audio = donnée de santé identifiante (voix) | Traitement local recommandé ; tout stockage distant de l'audio → HDS | CNIL, recommandation applications mobiles (27/03/2025) ; guide HAS/CNIL (projet 02/2026) | consentement du patient à la captation de la voix (code civil), suppression tracée |
| Sauvegarde chez un tiers (iCloud, Google Drive, dépôt Git, serveur) | **Oui**, activité 6° « sauvegarde » : prestataire sur la liste ANS ; cas du chiffrement de bout en bout sans clé chez le prestataire : **aucune position ANS/CNIL trouvée** | R.1111-9 6° ; ANS | contrat HDS de l'hébergeur ; sinon sauvegarde hors ligne (fichier chiffré sur support local) |
| Éditeur « clé en main » (assistant de consultation) | Oui pour l'éditeur (Doctolib SAS : certifié 1 à 6, V2.0, BSI, liste ANS 20/10/2026 ; Nabla : revendiqué, **absent de la liste ANS**) | liste ANS | contrat art. 28 de l'éditeur |

### 2.4 Obligations à prévoir (à confirmer par le DPO, voir Mission 3 et questions en Mission 6)
- Information des patients (affichage au cabinet, mention sur les documents remis, information orale en visite) sur le traitement informatique, l'usage d'une IA d'aide à la rédaction et, le cas échéant, l'enregistrement de la consultation ; droit d'opposition et possibilité de consulter sans IA ni enregistrement.
- Registre des traitements de l'association ou du cabinet : finalités, catégories, destinataires (fournisseurs d'IA, de transcription, relais), transferts, durées.
- Analyse d'impact (AIPD) : probable pour un traitement de données de santé avec IA et enregistrement vocal ; l'exemption « professionnel de santé exerçant à titre individuel » doit être vérifiée au regard du recours à l'IA et à l'enregistrement.
- Contrats : sous-traitance avec chaque fournisseur (relais, IA, transcription, hébergeur de sauvegarde) ; clauses de transfert hors EEE si nécessaire.
- Sécurité : PGSSI-S (authentification, journalisation, chiffrement, sauvegarde, effacement), politique de durées, procédure en cas de perte du téléphone (verrouillage, révocation du jeton, restauration).

---

## Mission 3 — Vérifier Claude AI (API Anthropic) pour des consultations réelles en France

### 3.1 Conditions contractuelles et techniques (pages publiques consultées le 20/10/2026)
| Point | Constat | Source | Classement |
|---|---|---|---|
| Entraînement des modèles sur les données de l'API | Non : « Anthropic may not train models on Customer Content from Services » ; les données conservées ne servent jamais à l'entraînement sans permission expresse | Commercial Terms (17/06/2025, section B) ; doc « API and data retention » | conforme |
| Rôle contractuel, cocontractant | Anthropic = sous-traitant ; pour un client de l'EEE : Anthropic Ireland, Limited, droit irlandais | Commercial Terms (M.7) ; Privacy Center | conforme |
| Contrat de sous-traitance (DPA) | DPA du 24/02/2025 : clauses contractuelles types UE modules 2 et 3, addenda UK et Suisse, sous-traitants ultérieurs listés (Google Cloud, AWS, Microsoft Azure, « Worldwide »), suppression sous 30 jours après la fin du contrat, AES-256 au repos, TLS 1.2+, notification de violation sous 48 h, SOC 2 annuel. **Annexe 1 : « Special categories of personal data : None »** : le contrat ne décrit pas un traitement de données de santé ; aucune clause de secret professionnel | DPA ; trust.anthropic.com (15/10/2026) | à vérifier (à compléter contractuellement) |
| Durée de conservation par défaut | Entrées et sorties supprimées sous **30 jours** ; contenu signalé par les classifieurs conservé jusqu'à **2 ans**, scores de classification 7 ans, retours 5 ans | Privacy Center « How long do you store… » (01/07/2026) | non conforme à l'objectif « aucune conservation » |
| Zero Data Retention (ZDR) | Sur demande commerciale, « subject to Anthropic's approval », par organisation ; pas d'éligibilité publiée ; exclu pour les « Covered Models » (Fable 5/5.1, Mythos : 30 jours obligatoires) ; Sonnet 5.5 et Haiku 5.5 éligibles ; **« CORS is not supported for organizations with ZDR arrangements… route requests through a backend proxy server »** : incompatible avec l'appel direct depuis le navigateur | doc « API and data retention » ; Privacy Center ZDR | à vérifier (demande à faire) ; impossible dans l'architecture actuelle |
| Localisation du traitement | `inference_geo` : « global » (défaut) ou « us » (+10 %) ; stockage au repos : « us » seul ; « Inference geo : only "us" and "global" are available » ; aucune option EEE sur l'API directe ; page « Regional compliance » : Europe = Bedrock et Vertex « Included », Foundry « Coming soon », API directe absente | doc « Data residency » ; claude.com/regional-compliance ; Privacy Policy (10/09/2026) | non conforme (traitement hors EEE systématique) |
| Transfert hors EEE | Anthropic **absent de la liste du Data Privacy Framework** (recherche du 20/10/2026 : « Query returned no results ») → le transfert ne peut reposer que sur les CCT du DPA, avec analyse d'impact de transfert (TIA) et mesures supplémentaires (la pseudonymisation sur l'appareil relève du cas d'usage 2 des recommandations CEPD 01/2020, sous conditions strictes). Contexte : DPF maintenu par le Tribunal de l'UE (Latombe, 03/09/2025, pourvoi en cours) mais contesté (lettre du CEPD à la Commission du 31/07/2026) | dataprivacyframework.gov ; CNIL questions-réponses (17/07/2024) ; CEPD 01/2020 | à vérifier (CCT + TIA à documenter avec le DPO) |
| Données de santé dans les conditions | Aucune clause santé dans les Commercial Terms ; Usage Policy (version affichée « effective 12/11/2026 »), domaine « Medical » à haut risque : revue par un professionnel qualifié pouvant modifier la recommandation, et **information de la personne qu'une IA a été utilisée** ; données de santé citées parmi les informations à ne pas collecter sans autorisation | anthropic.com/legal/aup | à vérifier (information du patient à organiser ; la relecture par le médecin existe déjà) |
| HIPAA / BAA | BAA signable en libre-service dans la Console ; **sans valeur en France** : HIPAA n'équivaut pas à l'HDS et n'est pas retenu dans ce rapport | doc retention ; Privacy Center | sans objet |
| Certifications | SOC 2 Type 2 (2025 + lettre de pont 10/2026), ISO 27001 (2025), ISO 42001 (2025), CSA STAR ; **HDS : Anthropic absent de la liste ANS des hébergeurs certifiés** (20/10/2026) | trust.anthropic.com ; esante.gouv.fr | sécurité : conforme ; HDS : non certifié |
| Clé API dans le navigateur | L'application appelle l'API avec l'en-tête `anthropic-dangerous-direct-browser-access` ; le SDK qualifie l'option de dangereuse (« risks exposing your secret API credentials ») ; recommandation de l'éditeur : proxy serveur, jamais de clé dans le code | SDK TypeScript (README, client.ts) ; support « API key best practices » | non conforme aux bonnes pratiques de l'éditeur (acceptable pour un seul médecin sur appareil verrouillé, voir 1.4) |

### 3.2 Cadre français applicable (textes consultés le 20/10/2026)
- **Un texte pseudonymisé reste une donnée de santé à caractère personnel** pour le médecin qui l'envoie : CNIL, « Identifier les données personnelles » (27/01/2020) ; CJUE, 04/09/2025, C-413/23 P (le caractère identifiable s'apprécie du point de vue de l'émetteur) ; Conseil d'État, 13/02/2026, n° 498628 (Cegedim) ; CNIL, IQVIA, SAN-2026-008 du 26/05/2026 (5 M€) ; ANS : « la pseudonymisation n'a pas d'impact sur l'obligation de certification ». Le chapitre V du RGPD (transferts), l'article 28 et l'information des patients s'appliquent donc entièrement.
- **HDS** : art. L.1111-8 CSP (loi SREN 2024), R.1111-8-8 et R.1111-9 (six activités) ; décret n° 2026-209 du 24/03/2026 : stockage exclusivement dans l'UE/EEE et accès distants depuis un pays tiers encadrés (applicable six mois après publication) ; référentiel v2 (arrêté du 26/04/2024, échéance 16/05/2026) ; v2.1 annoncée (publication 10/2026, application 12/2026 : « un accès distant est considéré comme un transfert »). Transit par une API sans stockage : **aucune position ANS trouvée** ; conservation 30 jours des requêtes par le fournisseur = conservation de données de santé pour le compte du médecin, qualification à faire trancher (DPO, ANS) ; si l'HDS est retenue, un fournisseur stockant hors EEE ne peut pas être conforme.
- **Secret médical et déontologie** : L.1110-4 CSP, art. 226-13 du code pénal ; décret n° 2026-691 du 27/07/2026, nouvel art. R.4127-13-1 : le médecin qui utilise l'IA « met en œuvre les précautions indispensables » pour la sécurité et la confidentialité des données, en tenant compte des référentiels des autorités, du CNP et du CNOM ; R.4127-73 ; L.4001-3 (information du patient en cas de dispositif à traitement algorithmique, textes d'application en cours).
- **AIPD** : la dispense de 2019 vise le professionnel de santé individuel pour la gestion des dossiers, des ordonnances et des rendez-vous ; l'envoi à une IA générative hors UE et l'enregistrement vocal cumulent données sensibles, patients vulnérables, usage innovant et transfert : **AIPD présumée requise** (CNIL, fiche IA du 08/04/2024 ; guide HAS/CNIL, projet du 16/02/2026, p. 16).
- **Information et opposition** : art. 13 RGPD ; référentiel CNIL des cabinets (délibération 2020-081) : information par affichage ou document ; guide HAS/CNIL (projet 2026, recommandation 7.1) : pas de consentement spécifique pour une IA dans le soin courant, information loyale et droit d'opposition, modalités tracées au dossier ; **consentement du patient (code civil) pour toute captation de la voix** ; registre des traitements obligatoire (données sensibles), rubrique transferts (guide CNOM/CNIL 2018).
- **AI Act** (règlement 2024/1689 modifié par 2026/1744, en vigueur le 27/07/2026) : un assistant de rédaction ou de transcription n'est pas « à haut risque » ; le devient un logiciel qui est un dispositif médical de classe IIa ou plus (annexe I, obligations au 02/08/2028) ou un outil de triage d'urgence (annexe III, 02/12/2027) ; transparence de l'art. 50 applicable depuis le 02/08/2026 ; le médecin est « déployeur », et deviendrait « fournisseur » en mettant l'outil à disposition de confrères.
- **Règlement DM 2017/745** : les gabarits d'ordonnance sans calcul ne sont pas des DM ; **les calculs de dose au poids, les doses maximales, les alertes et les règles d'aide à la décision appliqués aux données d'un patient sont probablement des logiciels DM de classe IIa** (règle 11 ; MDCG 2019-11 rev. 1, 06/2025 ; CJUE Snitem 2017 ; ANSM) ; usage strictement personnel = pas de « mise à disposition » ; exemption des « établissements de santé » (art. 5.5) pour un cabinet individuel à vérifier (MDCG 2023-1 non consultable) ; **partage entre confrères, même gratuit : à qualifier avant tout partage**.
- **Sécurité** : PGSSI-S (identification électronique de niveau « substantiel » : CPS, e-CPS ; authentification multifacteur pour tout accès interne depuis janvier 2026 selon la lecture CNIL du projet DPI) ; CNIL, recommandation MFA (délibération 2025-019 : MFA recommandée pour les données de santé) ; guide de la sécurité des données personnelles (édition 2024 : chiffrement, journalisation, sauvegarde 3-2-1, applications mobiles : secrets dans l'enclave sécurisée, sauvegardes OS désactivées ou chiffrées sans la clé) ; recommandation applications mobiles (2025-024 : audio traité en local, jamais conservé sur un serveur distant sans justification).

### 3.3 Verdict
| Exigence | Configuration actuelle (appel direct depuis le navigateur, texte pseudonymisé, « Envoyer » à l'écran) | Classement |
|---|---|---|
| Non-entraînement | garanti par les conditions commerciales | conforme |
| Contrat de sous-traitance | DPA incorporé, mais sans données de santé ni clause de secret | à vérifier |
| Traitement dans l'EEE | impossible sur l'API directe (US / global) | non conforme |
| Transfert hors EEE encadré | CCT du DPA ; pas de DPF ; TIA et mesures supplémentaires non documentées | à vérifier |
| Conservation | 30 jours (2 ans si signalement) ; ZDR impossible sans relais | non conforme |
| HDS | non certifié ; exigible seulement si l'envoi est qualifié d'hébergement | à vérifier (non certifié) |
| Clé API | dans le navigateur, option « dangereuse » de l'éditeur | non conforme (toléré 1 médecin) |
| Information du patient (Usage Policy, RGPD) | absente | non conforme |

**Conclusion** : dans sa configuration actuelle, l'API Claude **ne convient pas** à des consultations avec des données nominatives. Elle reste **défendable, sous validation écrite du DPO**, pour le texte pseudonymisé tel qu'il est envoyé aujourd'hui (validation du 15/10/2026 sur la pseudonymisation), à condition de documenter le transfert (CCT + TIA + mesures supplémentaires), le registre, l'AIPD et l'information des patients. Pour aller plus loin (ZDR, résidence européenne), il faut un relais serveur et un déploiement de Claude par un cloud certifié HDS (3.4).

### 3.4 Alternatives concrètes et vérifiables
| Voie | Ce qui est vérifié | Ce qui reste à confirmer |
|---|---|---|
| **Claude via Amazon Bedrock, région eu-west-3 (Paris), profil géographique UE** (`eu.anthropic.claude-sonnet-5-5`, `eu.anthropic.claude-haiku-5-5`) | AWS certifié **HDS v2.0, activités 1 à 6** (Bureau Veritas ; obtenu le 21/04/2026 ; Paris et Francfort dans le périmètre) ; mode de rétention `none` configurable par l'utilisateur (zéro conservation sans négociation ; sauf Fable/Mythos : 30 jours) ; « zero operator access », les fournisseurs de modèles n'ont pas accès aux requêtes ; données maintenues dans la géographie UE (Francfort, Stockholm, Milan, Espagne, Irlande, Paris) ; surcoût régional +10 % | périmètre : la liste ISO 27001 d'AWS mentionne « Amazon Bedrock [excludes Amazon Bedrock Marketplace] » alors que Claude 5.x est « offered and billed through AWS Marketplace » → confirmation écrite d'AWS ; clauses HDS contractuelles ; tarif Claude dans la grille Paris (non publié) |
| **Claude via Google Vertex AI, multi-région « eu »** | Google LLC GCP certifié HDS 1 à 5 (EY CertifyPoint ; pas d'activité 6) ; « IA générative sur Vertex AI » nommément dans le périmètre ; pas d'entraînement sans accord ; journaux désactivés par défaut | pas de région unique française pour Sonnet 5.5 / Haiku 5.5 (multi-région UE seulement) ; traitement des activités 3 à 5 possible hors EEE « tant que le stockage au repos reste dans l'EEE » ; modèles partenaires explicitement dans le périmètre HDS : non confirmé |
| Claude via Microsoft Foundry | Global / US Data Zone seulement ; SOC 2 et ISO « en cours » (Q4 2026) | **non utilisable en Europe aujourd'hui** |
| Anthropic direct + ZDR + relais serveur | le plus simple ; ZDR demandé à Anthropic ; aucune résidence UE, pas d'HDS | seulement pour du texte pseudonymisé validé par le DPO, jamais nominatif |
| Fournisseurs européens ou clouds HDS avec d'autres modèles | voir Mission 4 (Mistral, OVHcloud, Scaleway, Azure France Central, Gemini Paris, Nova Paris) | HDS des services d'inférence rarement nommés dans les périmètres publics |

---

## Mission 4 — Comparer trois solutions

Hypothèses de chiffrage (tarifs publics HT relevés le 20/10/2026 ; 1 $ = 0,90 € ; 22 jours par mois ; 20, 40 ou 60 consultations par jour = 440, 880 ou 1 320 par mois ; par consultation : 10 minutes d'audio, 4 000 jetons en entrée et 1 000 en sortie, un seul appel, sans cache ni traitement par lots ; remises de volume non comptées ; coûts linéaires avec le nombre de médecins). Les coûts de développement sont des **estimations de l'auditeur** (jours de travail), pas des devis.

### 4.1 Les trois solutions
| | **A — stockage local + API IA externe sécurisée** | **B — stockage local + passerelle (relais) sur infrastructure HDS** | **C — stockage local + IA hébergée dans un environnement adapté aux données de santé, avec transcription vocale** |
|---|---|---|---|
| Description | Architecture actuelle améliorée : pseudonymisation locale, écran « Ce qui part », API Anthropic directe (ou via un relais minimal hors HDS pour obtenir le ZDR) | Relais hébergé chez un hébergeur certifié HDS (France), qui garde les clés, authentifie, applique quotas et journal de métadonnées, et appelle **Claude via Bedrock Paris (profil UE, rétention nulle)** ou Vertex UE | B, plus un service de transcription hébergé dans l'EEE sous contrat (ou transcription locale) et un modèle de rédaction dans un cloud HDS en France (Bedrock Paris, Azure France Central, Vertex Paris, Scaleway ou OVHcloud sous contrat HDS) |
| Avantages | aucune infrastructure ; coût le plus bas ; déjà en place et testé | résidence UE, ZDR par configuration, HDS de l'infrastructure, clé API jamais dans le navigateur, plusieurs médecins, quotas | assistant vocal complet, un seul cadre contractuel européen, pseudonymisation toujours locale |
| Inconvénients | traitement hors EEE, conservation 30 jours, pas de ZDR sans relais, clé dans le navigateur, un seul médecin | serveur à exploiter (mises à jour, certificats, sauvegardes de configuration), contrat et support HDS, confirmations contractuelles (périmètre Marketplace) | le plus complexe : capture audio, consentement, AIPD, deux fournisseurs, qualité de transcription à valider en conditions réelles |
| Niveau de sécurité | correct pour un usage personnel pseudonymisé ; insuffisant pour du nominatif | élevé (chiffrement local + relais HDS + cloud HDS, rétention nulle) | élevé, mais l'audio est la donnée la plus sensible : traitement local recommandé, suppression immédiate |
| Obligations réglementaires | art. 28 à compléter, CCT + TIA, registre, AIPD, information des patients ; pas de donnée nominative | idem + contrat HDS/sous-traitance du relais et du cloud, clauses de transfert si accès distant hors EEE, journalisation PGSSI-S | idem + consentement à la captation de la voix, politique de suppression de l'audio documentée, AIPD impérative, avis CNOM/DPO |
| Complexité de développement | nulle (statu quo) ; relais minimal : 2 à 3 jours | 5 à 10 jours (relais : authentification, quotas, journal, appel Bedrock ; application : URL du relais et jeton à la place de la clé) + démarches contractuelles | 10 à 20 jours de plus (capture audio, consentement tracé, transcription, parcours de validation) + essais terrain |
| Coût de mise en place | 0 € (statu quo) à 2-3 jours | 5 à 10 jours + frais d'ouverture du contrat HDS (devis) | 15 à 30 jours + AIPD (DPO) + devis fournisseurs |
| Transcription | dictée du clavier iOS (traitement sur l'appareil en français, gratuit) | idem | service EEE (tableau 4.3) ou locale |

### 4.2 Coût de l'analyse IA par médecin et par mois (€ HT), selon le modèle
| Modèle (lieu) | c€ / consultation | 20 / j | 40 / j | 60 / j | Source |
|---|---|---|---|---|---|
| Claude Sonnet 5.5, Anthropic direct (US/global) | 1,62 | 7,13 | 14,26 | 21,38 | platform.claude.com/docs/en/about-claude/pricing (2 $ / 10 $ par million de jetons) |
| Claude Sonnet 5.5 via Bedrock ou Vertex UE (+10 %) | 1,78 | 7,84 | 15,68 | 23,52 | doc Anthropic (surcoût régional) ; grille Paris non publiée |
| Claude Haiku 5.5, Anthropic direct | 0,08 | 0,36 | 0,71 | 1,07 | idem (0,10 $ / 0,50 $) |
| Claude Haiku 5.5 via cloud UE (+10 %) | 0,09 | 0,39 | 0,78 | 1,18 | idem |
| Mistral Small 4 (La Plateforme : Azure Suède/Norvège, Mistral Compute France) | 0,11 | 0,48 | 0,95 | 1,43 | mistral.ai/pricing |
| Mistral Large (La Plateforme) | 0,32 | 1,39 | 2,77 | 4,16 | mistral.ai/pricing |
| Scaleway mistral-small-3.2 (Paris, ZDR par défaut) | 0,10 | 0,42 | 0,84 | 1,25 | scaleway.com/en/pricing/model-as-a-service |
| OVHcloud gpt-oss-120b (UE) | 0,07 | 0,32 | 0,63 | 0,95 | ovhcloud.com, catalogue AI Endpoints |
| Azure GPT-5 mini, Data Zone UE | 0,30 | 1,31 | 2,61 | 3,92 | API Azure Retail Prices, francecentral |
| Google Gemini 2.5 Flash, europe-west9 (Paris) | 0,33 | 1,47 | 2,93 | 4,40 | cloud.google.com/vertex-ai/generative-ai/pricing |
| AWS Nova Lite / Nova Pro, eu-west-3 (Paris) | 0,06 / 0,85 | 0,28 / 3,74 | 0,56 / 7,48 | 0,84 / 11,21 | AWS Price List eu-west-3 (16/10/2026) |

### 4.3 Coût de la transcription par médecin et par mois (€ HT)
| Service (lieu) | 20 / j | 40 / j | 60 / j | HDS du service | Source |
|---|---|---|---|---|---|
| OVHcloud whisper-large-v3-turbo (UE) | 3,37 | 6,75 | 10,12 | OVH certifié 1-6 ; AI Endpoints hors du tableau HDS public | catalogue AI Endpoints (20/10/2026) |
| OVHcloud whisper-large-v3 | 10,78 | 21,56 | 32,34 | idem | idem |
| Mistral Voxtral Mini Transcribe 2 (batch) | 11,88 | 23,76 | 35,64 | non certifié | mistral.ai (04/02/2026) : 0,003 $/min |
| Azure AI Speech, France Central, transcription par lots | 11,88 | 23,76 | 35,64 | Microsoft certifié 1-6 (services ISO 27001) | Azure Retail Prices (0,18 $/h) |
| Google Speech-to-Text V2, lots dynamiques, multi-région « eu » | 11,88 | 23,76 | 35,64 | Google certifié 1-5, Speech-to-Text nommé | cloud.google.com/speech-to-text/pricing (0,003 $/min) |
| Scaleway whisper-large-v3 (Paris) | 13,20 | 26,40 | 39,60 | Scaleway certifié 1-4 ; Generative APIs hors liste HDS publique | scaleway.com (0,003 €/min) |
| AWS Transcribe, eu-west-3 (Paris) | 23,76 | 47,52 | 71,28 | AWS certifié 1-6, Transcribe dans le périmètre ISO | AWS Price List (0,006 $/min) |
| Temps réel (Voxtral Realtime, Azure fast) | 23,76 | 47,52 | 71,28 | selon fournisseur | idem |
| Azure Speech temps réel | 66,00 | 132,00 | 198,00 | idem | 1 $/h |
| Dictée iOS sur l'appareil (clavier) | 0 | 0 | 0 | hors périmètre (Apple) | Apple, disponibilité des fonctionnalités (français : dictée sur l'appareil) |

### 4.4 Coût mensuel total (€ HT, hors développement)
Relais : fonction « edge » 0 à 5 €, petit serveur en France 5 à 15 €, **hébergeur certifié HDS 100 à 300 € et plus** (voir `docs/RELAIS-API-PROPOSITION.md`) ; l'option HDS exige en plus un support Business ou Enterprise et un contrat HDS **sur devis** (OVHcloud, Scaleway, Outscale, Clever Cloud). Un relais est partagé par tous les médecins.

| Solution (exemple de configuration) | 1 médecin, 20 / 40 / 60 par jour | 10 médecins (40 / j) | 50 médecins (40 / j) | Postes sur devis |
|---|---|---|---|---|
| **A** — Sonnet 5.5 direct, dictée iOS, relais minimal hors HDS (0 à 15 €) | 7 à 22 / 14 à 29 / 21 à 36 | ≈ 145 à 160 | ≈ 715 à 730 | ZDR (accord Anthropic) |
| **A bis** — Haiku 5.5 direct | 0,4 à 15 / 0,7 à 16 / 1 à 16 | ≈ 7 à 22 | ≈ 36 à 51 | idem |
| **B** — Sonnet 5.5 via Bedrock Paris (profil UE, rétention nulle) + relais HDS (100 à 300 €), dictée iOS | 108 à 308 / 116 à 316 / 124 à 324 | ≈ 257 à 457 | ≈ 884 à 1 084 | contrat HDS et support de l'hébergeur ; clauses HDS AWS ; tarif Claude Paris |
| **B bis** — Haiku 5.5 via Bedrock Paris + relais HDS | 100 à 300 / 101 à 301 / 101 à 301 | ≈ 108 à 308 | ≈ 139 à 339 | idem |
| **C** — Azure France Central : GPT-5 mini + Speech par lots, relais HDS | 113 à 313 / 126 à 326 / 140 à 340 | ≈ 364 à 564 | ≈ 1 418 à 1 618 | conditions HDS Microsoft ; Azure OpenAI nommément dans le périmètre ISO (à confirmer) |
| **C bis** — Scaleway Paris : mistral-small + whisper, contrat HDS, relais HDS | 114 à 314 / 127 à 327 / 141 à 341 | ≈ 372 à 572 | ≈ 1 462 à 1 662 | contrat HDS Scaleway (Generative APIs hors liste publique) |
| **C ter** — OVHcloud : gpt-oss-120b + whisper turbo, option HDS, relais HDS | 104 à 304 / 107 à 307 / 111 à 311 | ≈ 174 à 374 | ≈ 469 à 669 | option HDS et support OVHcloud (AI Endpoints hors tableau HDS) |
| **C quater** — Bedrock Paris : Sonnet 5.5 UE + AWS Transcribe, relais HDS | 132 à 332 / 163 à 363 / 195 à 395 | ≈ 732 à 932 | ≈ 3 260 à 3 460 | idem B |
| Repère : éditeur clé en main (Doctolib assistant, HDS 1-6) | 79 / médecin / mois (après 1 mois d'essai ; réservé aux utilisateurs de Doctolib Médecin) | 790 | 3 950 | Nabla : 69 € (2023) puis devis, absent de la liste ANS ; marché : 60 à 80 € |

Lecture : hors relais, l'IA et la transcription coûtent de ≈ 8 € (OVHcloud) à ≈ 40 € (Azure) par médecin et par mois à 40 consultations par jour ; le poste principal est le **relais HDS et son contrat**, fixe et partagé, qui devient marginal à partir de 10 médecins. La transcription en temps réel coûte 2 à 6 fois plus cher que la transcription par lots.

### 4.5 Ce qui n'a pas de tarif public (devis)
Contrat et option HDS (OVHcloud, Scaleway, Outscale, Clever Cloud) et support associé ; clauses HDS AWS, Microsoft (conditions contractuelles spécifiques), Google (support Advanced ou Premium) ; Claude dans la grille Bedrock Paris ; Mistral Medium 3.5 (page officielle en erreur) et déploiement privé Mistral ; inscription explicite d'AI Endpoints (OVHcloud) et de Generative APIs (Scaleway) dans les périmètres HDS ; preuve HDS de Gladia, Nabla, Praxy, Markus, Scribe Médical ; Vocapia (lieu d'hébergement, grille) ; LinTO (position HDS).

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

---

## Mission 6 — Conclusion et recommandation chiffrée

### 6.1 État réel de sécurité de l'application
- **Ce qui est solide (vérifié dans le code)** : aucune donnée patient sur un serveur de l'application ; tout le dossier est chiffré sur l'appareil (AES-256-GCM, clé dérivée du code personnel) ; photos chiffrées ; sauvegarde chiffrée ; pseudonymisation locale avec contrôle de fuite avant tout envoi ; envoi à l'IA seulement après le geste « Envoyer » sur l'écran « Ce qui part » (v41w) ; garde-fous sur les réponses (aucune posologie appliquée, nombres inconnus écartés) ; aucun script tiers, aucune analyse d'audience, OCR sur l'appareil ; durées de purge pour le brouillon, les dictées, les validés et les photos.
- **Ce qui est fragile** : clé de session en clair 20 minutes et code à 4 chiffres possible (sécurité réelle = verrouillage de l'iPhone) ; clé API dans le navigateur ; adresses et coordonnées des patients envoyées à des services sans contrat (BAN, serveur de démonstration OSRM) ; pas de purge automatique du journal de garde ni des arrêts de tournée ; sauvegarde iCloud du téléphone et fichier de sauvegarde = hébergement de données chiffrées non qualifié ; dictée Apple selon le réglage iOS.

### 6.2 Problèmes prioritaires (ordre de traitement)
1. Flux vers l'IA : transfert hors EEE non documenté (CCT + TIA), DPA sans données de santé, conservation 30 jours, pas d'information des patients → **aucune donnée nominative vers l'IA tant que ce point n'est pas réglé**.
2. Coordonnées et adresses vers OSRM (démo) et BAN sans contrat → remplacer OSRM (service sous contrat ou calcul local), documenter BAN au registre.
3. Clé de session et code court → 6 chiffres au minimum, session plus courte, ou authentification biométrique.
4. Journal de garde et tournée sans purge automatique → durées à fixer (dossier : 20 ans selon R.1112-7 si le journal tient lieu de dossier ; sinon durée courte documentée) ; purge automatique.
5. Sauvegardes (iCloud, fichier) → qualifier avec le DPO ; à défaut, sauvegarde hors ligne seulement.
6. Dictée iOS → vérifier « dictée sur l'appareil » et « Améliorer Siri et Dictée » désactivé.
7. Synchronisation Google Sheets → laisser désactivée ou retirer.
8. Qualification « dispositif médical » des calculs de dose et des aides à la décision → avant tout partage avec des confrères.

### 6.3 Services externes auxquels les données sont envoyées aujourd'hui
Anthropic (texte clinique pseudonymisé, après validation à l'écran) ; Etalab/BAN (adresses) ; serveur de démonstration OSRM (coordonnées GPS) ; OpenStreetMap (tuiles) ; Google Maps, Waze ou Apple Plans (adresse, au choix du médecin) ; Apple (dictée, sauvegarde iCloud selon réglages) ; Google Sheets si la synchronisation facultative est activée (désactivée par défaut) ; GitHub Pages (chargement du site, aucune donnée patient).

### 6.4 Garanties et certifications restant à vérifier
- Anthropic : avenant ou DPA couvrant des données de santé avec clause de secret professionnel ; ZDR (éligibilité d'un cabinet, modèles autorisés) ; lieu exact de stockage des requêtes et des journaux ; accès humain (trust and safety) ; sous-traitants et pays ; procédure en cas de demande d'une autorité étrangère ; statut AI Act du modèle (fournisseur de modèle à usage général, marquage art. 50).
- AWS : inclusion de Claude (facturé via Marketplace) dans le périmètre HDS de Bedrock ; clauses HDS contractuelles ; tarif Claude à Paris. Google : modèles partenaires dans le périmètre HDS ; multi-région UE acceptable ? Microsoft : Azure OpenAI nommément dans le périmètre ISO/HDS.
- Hébergeur du relais : certificat HDS (liste ANS), activités couvertes, contrat et support.
- Position de l'ANS sur le transit par API sans stockage et sur les sauvegardes chiffrées de bout en bout (non trouvées).
- Version finale du guide HAS/CNIL sur l'IA en contexte de soins et des lignes directrices CEPD 01/2025 sur la pseudonymisation (non publiées au 20/10/2026) ; suite donnée à la lettre du CEPD du 31/07/2026 sur le DPF.

### 6.5 Meilleure architecture envisageable
**Solution B, puis C par étapes** : dossier sur l'appareil (inchangé) → pseudonymisation locale (inchangée) → relais hébergé chez un hébergeur certifié HDS en France, sans stockage de contenu, qui garde les clés et journalise des métadonnées → **Claude via Amazon Bedrock, région Paris, profil UE, rétention nulle** (ou Vertex multi-région UE en second choix) → plus tard, transcription vocale par un service de l'EEE sous contrat (lots) ou sur l'appareil, audio supprimé dès la transcription. Microsoft Foundry n'est pas utilisable en Europe aujourd'hui. La voie « Anthropic direct + ZDR » reste la solution de repli pour du texte pseudonymisé seulement.

### 6.6 Budget réaliste (€ HT)
| Phase | Contenu | Coût de mise en place (estimation, hors devis) | Coût mensuel |
|---|---|---|---|
| 0 — immédiat (sans code) | validation DPO (CCT + TIA, registre, AIPD, information des patients), réglages iOS, désactivation OSRM/Sheets avec données réelles | temps du DPO et du médecin | 7 à 22 € (Sonnet) ou 0,4 à 1 € (Haiku) pour 1 médecin |
| 1 — relais et Claude en Europe (B) | relais HDS, Bedrock Paris en ZDR, clé hors navigateur, quotas | 5 à 10 jours de développement + ouverture du contrat HDS (devis) | 1 médecin : 108 à 316 € ; 10 médecins : ≈ 260 à 460 € ; 50 : ≈ 880 à 1 100 € (Sonnet) ; avec Haiku, le relais représente presque tout le coût |
| 2 — assistant vocal (C) | capture audio locale, consentement tracé, transcription EEE par lots, suppression de l'audio | 10 à 20 jours de plus + AIPD + essais terrain | + 7 à 48 € par médecin selon le service (OVHcloud turbo 6,75 € ; Azure/Google/Mistral ≈ 24 € ; AWS 47,52 € à 40 consultations par jour) |
| Repère | éditeur clé en main (Doctolib) | 0 | 79 € par médecin |

### 6.7 Adaptations nécessaires du code (à faire plus tard, aucune dans cet audit)
1. Appel de l'IA via le relais : adresse du relais et jeton du médecin à la place de la clé API ; suppression de l'en-tête d'accès direct ; conservation de l'écran « Ce qui part » et du verrou d'envoi automatique tant que le DPO n'a pas validé.
2. Modèle paramétrable (Sonnet/Haiku via Bedrock UE) ; comptage des coûts lu depuis le relais.
3. Remplacement du serveur de démonstration OSRM (service sous contrat ou estimation locale) ; mention de la BAN au registre.
4. Code personnel à 6 chiffres au minimum ; durée de session réduite ; option biométrique (WebAuthn) à étudier.
5. Purge automatique du journal de garde et des arrêts de tournée selon des durées documentées ; export chiffré avant purge.
6. Écran d'information du patient (texte court) et trace « information faite / opposition » dans le dossier et le compte rendu ; mention « document préparé avec une aide à la rédaction, relu et validé par le médecin » si le DPO le demande.
7. Assistant vocal (phase 2) : capture audio locale, consentement tracé, suppression de l'audio, parcours décrit en Mission 5 ; la dictée actuelle reste.
8. Synchronisation Google Sheets : retrait ou verrou tant qu'aucun DPA n'existe.

### 6.8 Étapes de mise en conformité
1. **Semaine 1** : DPO saisi avec ce rapport ; registre des traitements mis à jour (IA, transfert, relais à venir) ; réglages iOS vérifiés ; OSRM et Sheets non utilisés avec des données réelles.
2. **Semaines 2 à 4** : AIPD rédigée avec le DPO ; TIA et CCT documentées pour Anthropic ; demande à Anthropic (avenant santé, ZDR) ; demandes de devis HDS (hébergeur du relais) et questions à AWS (périmètre Marketplace, clauses HDS) ; affichage et notice d'information des patients.
3. **Mois 2** : relais HDS en service, Claude via Bedrock Paris en rétention nulle, clé hors navigateur ; tests sur données fictives ; revue de sécurité (PGSSI-S : MFA, journalisation, sauvegarde testée, procédure de perte du téléphone).
4. **Mois 3** : décision écrite du DPO autorisant les données nominatives vers l'IA via le relais (ou maintien de la pseudonymisation) ; mise en production progressive.
5. **Ensuite** : étude de l'assistant vocal (consentement, transcription EEE, essais terrain, AIPD mise à jour) ; qualification DM et statut AI Act avant tout partage avec des confrères.

### 6.9 Questions à soumettre au DPO (ou à un juriste santé) et au fournisseur
**DPO** : qui est responsable de traitement (médecin seul, association pour le journal) et dans quel registre inscrire l'application ? L'envoi de texte pseudonymisé à une API hors UE, puis l'enregistrement vocal, relèvent-ils de la dispense d'AIPD de 2019 ou faut-il une AIPD, par qui, revue quand ? Sur quel outil repose le transfert vers Anthropic (CCT modules 2/3, pas de DPF) et où est la TIA ; la pseudonymisation telle que mise en œuvre répond-elle au cas d'usage 2 du CEPD (clé hors d'atteinte du fournisseur, absence de réidentification par contexte clinique rare) ; la validation du 15/10/2026 couvre-t-elle ce point ? La conservation 30 jours des requêtes chez le fournisseur hors EEE est-elle un hébergement au sens de L.1111-8 ; faut-il interroger l'ANS ? Quelle information des patients (affiche, notice, mention au dossier) et quel traitement du droit d'opposition à l'IA et à l'enregistrement ? Quelle base légale et quelle preuve de consentement pour la voix ; durée de conservation de l'audio et de la transcription brute ? Quel service de sauvegarde est autorisé (HDS, ou chiffrement local seulement ; interdiction d'iCloud et de Drive non HDS) ? Quelles mesures PGSSI-S minimales (e-CPS ou MFA, journalisation, chiffrement, effacement à distance) et qui déclare une violation (72 h) ? Avant tout partage avec des confrères : qualification DM des calculs de dose, statut de fournisseur au sens de l'AI Act, responsabilité et assurance.
**Fournisseur d'IA (Anthropic, puis AWS)** : le DPA et les CCT couvrent-ils expressément des données de santé (annexe « special categories : None » à corriger) ? ZDR disponible pour l'organisation et le modèle retenu ; sinon lieu de stockage, durée, accès humain, sous-traitants et pays ? Engagement écrit de non-réutilisation (entraînement, évaluation), clause de secret professionnel pour le personnel, notification de violation, attestations de sécurité, chiffrement au repos et en transit ? Région de traitement dans l'EEE ou point d'entrée européen ; lois extra-européennes applicables (art. 48 RGPD, Cloud Act) et procédure en cas de demande d'autorité ? Statut AI Act du modèle et documentation pour le déployeur ; conditions d'usage « santé » ? Documentation technique transmissible pour l'AIPD ? Pour AWS : Claude facturé via Marketplace dans le périmètre HDS de Bedrock ; clauses HDS ; tarif Paris.

### 6.10 Éléments bloquants avant toute donnée réelle avec l'IA
| Élément | État | Bloquant pour |
|---|---|---|
| Validation écrite du DPO sur le transfert (CCT + TIA + mesures) et sur la pseudonymisation | à obtenir | texte pseudonymisé (maintien) et a fortiori nominatif |
| AIPD | non faite | nominatif et enregistrement vocal |
| Contrat de sous-traitance couvrant des données de santé (avenant Anthropic ou contrat cloud HDS) | DPA sans données de santé | nominatif |
| Information des patients et droit d'opposition (affiche, notice, trace) | absente | tout usage de l'IA avec données réelles |
| Registre des traitements à jour | à vérifier | tout usage |
| Traitement dans l'EEE et rétention nulle (relais + Bedrock Paris) | non en place | nominatif |
| Clé API hors du navigateur | non en place | plusieurs médecins ; nominatif |
| Consentement à la captation de la voix, suppression documentée de l'audio | sans objet aujourd'hui | assistant vocal |

### 6.11 Tableau récapitulatif conforme / non conforme / à vérifier
| Élément | Classement | Justification |
|---|---|---|
| Dossiers chiffrés sur l'appareil, sans prestataire | conforme (pas d'HDS exigée) | L.1111-8, R.1111-8-8 ; ANS |
| Pseudonymisation locale et contrôle de fuite | conforme comme mesure technique ; ne rend pas la donnée anonyme | CNIL 2020, CJUE 2025, CE 2026, CNIL IQVIA 2026 |
| Envoi à l'IA après validation à l'écran, pas d'envoi automatique | conforme à la décision du 20/10/2026 | code vérifié (v41w) |
| Non-entraînement par Anthropic | conforme | Commercial Terms 2025 |
| Contrat de sous-traitance Anthropic | à vérifier | DPA sans données de santé ni clause de secret |
| Transfert hors EEE | à vérifier | CCT du DPA ; pas de DPF ; TIA à documenter |
| Localisation du traitement (API directe) | non conforme à l'objectif EEE | US / global seulement |
| Conservation chez Anthropic | non conforme (30 jours, jusqu'à 2 ans) | ZDR impossible sans relais |
| HDS du fournisseur d'IA | à vérifier (non certifié ; exigible seulement si hébergement) | ANS, L.1111-8 |
| Clé API dans le navigateur | non conforme aux recommandations de l'éditeur (toléré 1 médecin) | SDK Anthropic |
| Information des patients, registre, AIPD | non conforme tant que non faits | art. 13, 30, 35 ; CNIL ; guide HAS/CNIL |
| Adresses et coordonnées vers BAN et OSRM démo | non conforme (OSRM) / à vérifier (BAN) | aucun contrat |
| Synchronisation Google Sheets | non conforme si activée avec des données réelles | aucun DPA |
| Sauvegarde iCloud / fichier chez un tiers | à vérifier | R.1111-9 6° ; position ANS non trouvée |
| Dictée Apple | à vérifier (réglage iOS) | Apple |
| Code personnel, session, MFA | à renforcer | PGSSI-S, CNIL MFA 2025 |
| Purge du journal et de la tournée | non conforme (pas de durée) | art. 5.1.e |
| Qualification DM des calculs de dose | à vérifier avant partage | MDR, MDCG 2019-11 |
| AI Act | conforme pour l'usage actuel (hors haut risque) | 2024/1689 modifié 2026 |
| Déontologie (R.4127-13-1) | à documenter (précautions prises) | décret 2026-691 |

### 6.12 Points non trouvés
Position ANS sur un transit par API sans stockage ; position ANS/CNIL sur les sauvegardes chiffrées de bout en bout ; texte CNIL ou CNOM spécifique aux assistants de consultation (programme CNIL 2026 annoncé) ; version finale du guide HAS/CNIL ; version finale des lignes directrices CEPD 01/2025 ; réponse de la Commission à la lettre du CEPD du 31/07/2026 ; applicabilité de l'art. 5(5) du règlement DM à un cabinet individuel ; qualification d'« activité commerciale » d'un partage gratuit entre confrères ; tarif de Claude dans la grille Bedrock Paris ; inscription des services d'inférence d'OVHcloud et de Scaleway dans leurs périmètres HDS.

### 6.13 Sources principales (consultées le 20/10/2026)
Légifrance : L.1111-8, R.1111-8-8, R.1111-9 et R.1111-9-1 CSP (décret 2026-209), L.1110-4 CSP, art. 226-13 CP, décret 2026-691 (R.4127-13-1), arrêté du 26/04/2024 (HDS v2), délibérations CNIL 2018-327, 2019-118, 2020-081, 2025-019, 2025-024 ; ANS (FAQ HDS, liste des hébergeurs certifiés, PGSSI-S, mémento libéral 2021, v2.1) ; CNIL (données pseudonymisées 2020, AIPD, fiche IA 2024, questions-réponses IA générative 2024, IQVIA 2026, guide sécurité 2024, projet de recommandation DPI 2025) ; HAS (dysthyroïdies, IA générative 2025, guide HAS/CNIL projet 2026) ; CNOM (textes IA) ; EUR-Lex (RGPD, AI Act 2024/1689 et 2026/1744, MDR 2017/745), MDCG 2019-11 rev. 1 ; CJUE C-413/23 P, T-553/23 ; Conseil d'État n° 498628 ; EDPB (01/2020, 01/2025, lettre du 31/07/2026) ; Anthropic (Commercial Terms, DPA, Privacy Policy, Usage Policy, Trust Center, docs retention, data residency, Bedrock, Vertex, Foundry, pricing, SDK) ; dataprivacyframework.gov ; AWS (HDS, ISO, Bedrock, Price List eu-west-3) ; Google Cloud (HDS, Vertex, Speech-to-Text) ; Microsoft Learn (HDS, Azure OpenAI, Speech, Retail Prices) ; Mistral AI (pricing, trust center, ZDR, Voxtral) ; OVHcloud (AI Endpoints, certification HDS) ; Scaleway (Generative APIs, HDS) ; Doctolib et Nabla (pages publiques et presse citée en Mission 4).

*Rapport établi le 20/10/2026 sans modification du code, à partir de la branche `ia` ; aucune donnée réelle utilisée.*
