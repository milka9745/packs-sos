# Registre des corrections et améliorations — 16 octobre 2026

Rédigé par le Docteur Mickaël DEIE après une garde réelle (environ deux heures de retard sur les visites). Texte reçu le 16/10/2026, enregistré tel quel ci-dessous ; la table de suivi en fin de document indique l'état de chaque point (corrigé / partiel / impossible et pourquoi) et le test associé.

## Consignes de traitement (Docteur DEIE)

- Traiter tous les points sans rien supprimer de ce qui fonctionne, avec un test pour chacun et un état.
- **Lot 1, urgent, publié dès qu'il est prêt** : n° 10 (aucune perte de dictée ni d'observation : sauvegarde chiffrée à chaque frappe, restauration automatique), n° 5, n° 9, n° 7, n° 8. **Lot 2** : n° 1 à 4. **Lot 3** : n° 6 et n° 11.
- n° 5 : sur iPhone, fiabiliser la dictée par le micro du clavier dans un grand champ toujours visible ; n'utiliser une reconnaissance vocale intégrée que si elle est fiable en application installée sur iPhone, et le dire franchement sinon.
- n° 6 : l'IA ne peut pas fonctionner hors ligne ; aucune perte de données ; les demandes IA sont mises en file d'attente et, au retour du réseau, Packs propose l'écran « Ce qui part » pour validation, jamais d'envoi automatique. Indiquer clairement à l'écran ce qui marche hors ligne et ce qui attend le réseau.
- n° 7 : trouver la cause (taille, nombre, stockage), compresser les images sur l'appareil, les garder chiffrées, afficher une confirmation ou la limite exacte.
- n° 11 : ranger la clé API chiffrée dans profil.json, comme la signature, pour qu'elle soit disponible sur tout appareil après la phrase maître ; jamais affichée en clair, remplaçable d'un geste ; prévenir que la sécurité dépend de la solidité de la phrase.
- Tester à 375 px (jour, nuit, grand texte) et sur ordinateur, lancer toutes les suites, publier chaque lot et dire ce qui a changé.

---

## REGISTRE COMPLET DES CORRECTIONS ET AMÉLIORATIONS — APPLICATION WEB MÉDICALE

Date : 16 octobre 2026
Destinataire : Claude AI — Développement de mon application médicale
Objet : Corrections des bugs, optimisation ergonomique, fiabilisation de l'intelligence artificielle et amélioration de la gestion des visites et consultations.

### Contexte général — retour d'expérience sur le terrain

Je développe une application web médicale destinée à mon activité de médecin généraliste, aussi bien pour les consultations au cabinet que pour les visites à domicile. Je teste actuellement cette application en conditions réelles. Aujourd'hui, j'ai accumulé environ deux heures de retard sur mes visites, notamment à cause de bugs, de manipulations inutiles et du temps perdu à rechercher des boutons qui devraient être accessibles naturellement. Cette situation est extrêmement frustrante. Je souhaite une application rapide, intuitive et fiable, qui s'adapte à mon activité médicale et non l'inverse.

Mes exigences principales :
- Minimiser le nombre de clics.
- Afficher uniquement les fonctionnalités pertinentes à chaque étape.
- Rendre immédiatement accessibles les appels et la navigation.
- Simplifier l'organisation des tournées.
- Fiabiliser les dictées médicales et les comptes rendus générés par l'intelligence artificielle.
- Éviter toute perte de données.
- Permettre le travail avec une connexion Internet faible ou inexistante.
- Garantir la cohérence des informations médicales.
- Assurer le fonctionnement de l'impression et des PDF.
- Permettre d'utiliser l'API Claude sur tous mes appareils autorisés.

Je souhaite que les 11 problèmes ci-dessous soient analysés et corrigés, sans suppression des fonctionnalités existantes qui fonctionnent correctement.

### Problème n° 1 — Trop de boutons et navigation non intuitive
Type : amélioration ergonomique majeure. Priorité : CRITIQUE.

**Problème constaté.** L'application présente trop de boutons ou de pages simultanément. Je suis régulièrement obligé de rechercher une fonction alors que celle-ci devrait apparaître naturellement selon l'étape de la visite. Cela me fait perdre du temps.

**Comportement attendu.** Une navigation progressive, avec idéalement trois ou quatre boutons principaux visibles à chaque étape. Les autres fonctionnalités apparaissent uniquement lorsqu'elles deviennent nécessaires.

Exemple de parcours pour une visite :
- Étape 1 — Tournée organisée : lorsque je sélectionne une visite, les commandes principales sont : appeler le patient, lancer l'itinéraire, activer le mode voiture.
- Étape 2 — Pendant le déplacement : appeler le patient, ouvrir Waze, indiquer mon arrivée, accéder éventuellement à la dictée de l'observation.
- Étape 3 — Après « Je suis arrivé » : observation médicale, dictée du compte rendu avec l'intelligence artificielle, prescriptions, autres actions nécessaires à la visite.
- Étape 4 — Fin de visite : pouvoir finaliser la visite et passer naturellement au patient suivant.

**Correction demandée.** Revoir la logique d'affichage des fonctionnalités pour obtenir une interface progressive. Appliquer cette même philosophie aux consultations réalisées au cabinet. Je ne souhaite plus naviguer dans de nombreuses pages qui me font perdre le fil de mon travail.

### Problème n° 2 — Difficulté à appeler rapidement les patients
Type : problème ergonomique. Priorité : CRITIQUE.

**Problème constaté.** Lorsque je réalise une visite à domicile, je dois pouvoir appeler le patient rapidement. Aujourd'hui, cette fonctionnalité n'est pas suffisamment visible ou accessible. Même lorsque le numéro est présent, il faut parfois effectuer des manipulations supplémentaires pour lancer l'appel.

**Comportement attendu.** Afficher une icône téléphone bien visible ; pouvoir appeler le patient en un clic ; rendre cette fonction accessible directement depuis la fiche patient ; la rendre également accessible depuis la liste des visites ; la conserver dans le mode voiture ; pouvoir appeler facilement le patient suivant.

**Correction demandée.** Placer l'appel téléphonique parmi les actions prioritaires de l'interface. Je ne veux pas chercher comment appeler un patient. Le bouton doit être immédiatement identifiable.

### Problème n° 3 — Amélioration du mode voiture
Type : amélioration ergonomique. Priorité : CRITIQUE.

**Problème constaté.** Lorsque je suis en déplacement, je souhaite accéder immédiatement aux fonctions nécessaires pour gérer la visite actuelle et préparer la suivante. Actuellement, le mode voiture n'est pas suffisamment pratique.

**Comportement attendu.** Le mode voiture doit distinguer deux espaces principaux.
- Patient actuel : nom et identification du patient ; adresse du domicile ; bouton Appeler ; bouton Waze / Navigation ; bouton Je suis arrivé.
- Patient suivant : nom et identification du prochain patient ; adresse ; bouton Appeler ; bouton Itinéraire.

Exigences ergonomiques : gros boutons clairement visibles ; peu de manipulations ; informations essentielles affichées directement ; possibilité de contacter le patient suivant facilement ; accès rapide à la navigation.

**Correction demandée.** Transformer le mode voiture en une interface simple et efficace, adaptée à la gestion des déplacements médicaux. Les manipulations doivent rester limitées et être réalisées lorsque le véhicule est à l'arrêt.

### Problème n° 4 — Intégration des nouvelles visites pendant la tournée
Type : amélioration fonctionnelle et organisationnelle. Priorité : CRITIQUE.

**Problème constaté.** De nouvelles demandes de visites peuvent arriver pendant que je suis déjà en tournée. Je dois pouvoir les intégrer rapidement, sans être obligé d'ouvrir plusieurs menus. Je souhaite aussi que les nouvelles visites soient regroupées géographiquement avec celles déjà prévues.

**Comportement attendu.** Lorsqu'une nouvelle visite apparaît : 1. elle est immédiatement visible dans l'interface de tournée ; 2. je peux identifier sa localisation ; 3. je peux l'intégrer facilement dans la tournée ; 4. l'application prend en compte sa proximité avec les autres visites ; 5. les visites d'un même secteur peuvent être regroupées ; 6. l'intégration préserve une organisation cohérente du parcours. Je souhaite conserver une vision claire de la visite actuelle, des prochaines visites et des nouvelles demandes.

**Correction demandée.** Simplifier fortement l'intégration des nouvelles visites et améliorer l'organisation géographique des déplacements. Les nouvelles demandes doivent apparaître dans mon champ de vision, sans nécessiter une succession de clics.

### Problème n° 5 — Dictée médicale par IA qui ne démarre pas
Type : bug fonctionnel potentiel. Priorité : CRITIQUE.

**Problème constaté.** Lors de ma première visite à domicile, j'ai voulu générer un compte rendu médical en dictant directement mon observation dans l'application. J'ai appuyé sur la fonction d'enregistrement vocal. Cependant, aucun enregistrement ne s'est lancé. J'ai donc été obligé de passer directement par l'application Claude AI. Comme je me trouvais dans une zone avec une mauvaise connexion Internet, je n'ai finalement pas pu obtenir mon compte rendu. Je ne sais pas encore si le problème vient d'un bug de programmation ou d'une difficulté d'utilisation.

**Comportement attendu.** Démarrage immédiat de l'enregistrement vocal ; indication visuelle lorsque le microphone enregistre ; possibilité de dicter une observation complète ; possibilité d'interrompre puis de reprendre la dictée ; conservation du contenu enregistré ; génération d'un compte rendu médical structuré ; aucun besoin de passer par une application extérieure.

**Correction demandée.** Vérifier et fiabiliser entièrement le fonctionnement de la dictée médicale intégrée.

### Problème n° 6 — Fonctionnement hors connexion insuffisant
Type : amélioration fonctionnelle majeure. Priorité : CRITIQUE.

**Problème constaté.** Lors de mes visites à domicile, je me trouve régulièrement dans des endroits où la connexion Internet est faible ou inexistante. Dans ces conditions, certaines fonctionnalités reposant sur l'intelligence artificielle sont difficiles, voire impossibles à utiliser : la dictée médicale ; la génération des comptes rendus ; l'analyse rapide des dossiers ; la description et l'analyse de photographies médicales. Ces limitations peuvent m'empêcher de terminer mon travail.

**Comportement attendu.** Un véritable fonctionnement hors connexion : l'enregistrement des dictées vocales sans réseau ; la sauvegarde locale des observations ; la conservation des photographies prises ; l'absence de perte de données lors d'une interruption Internet ; la synchronisation automatique lorsque le réseau revient ; la production de comptes rendus médicaux structurés hors connexion, si cela est techniquement possible.

**Correction demandée.** Étudier et mettre en place les fonctionnalités nécessaires pour travailler hors connexion. Distinguer clairement les fonctions réalisables localement de celles nécessitant obligatoirement une connexion Internet. Dans tous les cas, les données saisies ou dictées ne doivent pas être perdues.

### Problème n° 7 — Impossibilité d'intégrer les photographies du dossier patient
Type : bug fonctionnel. Priorité : HAUTE.

**Problème constaté.** Lors d'une visite, j'ai souhaité photographier plusieurs documents médicaux du patient. J'ai pu ouvrir l'appareil photo depuis l'application, prendre plusieurs photographies, sélectionner les photographies. Cependant, impossible de les intégrer au dossier patient. Je ne sais pas s'il existe une limitation concernant le nombre de photographies, leur poids ou une autre difficulté technique.

**Comportement attendu.** Pouvoir photographier directement les documents ; sélectionner plusieurs photographies ; les intégrer facilement au dossier patient ; pouvoir importer un grand nombre d'images ; être informé si une limitation existe ; obtenir une confirmation lorsque les documents sont correctement intégrés.

**Correction demandée.** Identifier la cause de l'échec d'importation et corriger le dysfonctionnement. Éviter les limites bloquantes inutiles. Si des restrictions techniques existent, elles doivent être clairement expliquées dans l'interface.

### Problème n° 8 — Observations médicales inadaptées à l'âge du patient
Type : bug fonctionnel / cohérence médicale. Priorité : CRITIQUE.

**Problème constaté.** Lors d'une consultation pédiatrique, j'ai sélectionné accidentellement un diagnostic ou un pack destiné aux adultes. Les calculs des doses thérapeutiques étaient corrects et adaptés à l'enfant. En revanche, l'application a ajouté dans les observations médicales des informations correspondant à un adulte. Cela ne doit pas arriver. Il faut également prévoir le cas où je sélectionne accidentellement plusieurs fois le même diagnostic.

**Comportement attendu.** Les observations respectent toujours l'âge réel du patient ; les informations spécifiques à l'adulte ne sont pas ajoutées automatiquement dans une observation pédiatrique ; les calculs des doses restent adaptés ; le choix accidentel d'un pack adulte n'entraîne pas l'apparition d'informations médicales inadaptées ; la sélection répétée d'un diagnostic ne crée pas de doublons.

**Correction demandée.** Vérifier la cohérence entre l'âge du patient, son profil médical, les diagnostics sélectionnés, les packs de prescriptions et les observations générées. Le profil réel du patient doit prévaloir sur une sélection accidentelle d'un pack adulte. Préserver le bon fonctionnement des calculs de posologie.

### Problème n° 9 — Impression et enregistrement PDF non fonctionnels
Type : bug fonctionnel. Priorité : HAUTE.

**Problème constaté.** Lors d'une consultation, lorsque j'appuie sur « Imprimer », aucune action ne se produit. Le bouton « Enregistrer en PDF » ne fonctionne pas non plus. Je suis obligé d'utiliser manuellement le raccourci clavier Ctrl + P.

**Comportement attendu.** Bouton Imprimer : ouvrir directement la fenêtre d'impression du document concerné. Bouton Enregistrer en PDF : générer et permettre l'enregistrement du document au format PDF.

**Correction demandée.** Vérifier et corriger les actions associées à ces deux boutons. Les fonctions doivent être directement accessibles et utilisables, sans recours à Ctrl + P.

### Problème n° 10 — Perte complète d'une dictée lors d'un changement de zone
Type : bug critique / perte de données médicales. Priorité : CRITIQUE — URGENT.

**Problème constaté.** Lors de la dictée d'un compte rendu médical destiné à être traité par l'intelligence artificielle, j'ai changé de zone dans l'application. À la suite de ce changement, tout le contenu que je venais de dicter a disparu. J'ai donc perdu l'intégralité de mon travail. Il m'a fallu recommencer. Cette situation est particulièrement problématique lors des visites à domicile, lorsque je suis pressé.

**Comportement attendu.** Toute dictée médicale est automatiquement sauvegardée : lors d'un changement de page ; lors d'un changement d'onglet ; lorsqu'on accède à une autre fonctionnalité ; en cas de perte de connexion ; en cas de fermeture accidentelle de l'application. Je souhaite pouvoir reprendre une dictée interrompue sans perdre ce qui a déjà été enregistré. Il faut conserver le texte déjà transcrit ainsi que les données vocales en attente de traitement lorsqu'elles existent.

**Correction demandée.** Mettre en place un système fiable de sauvegarde automatique et de récupération des dictées. Éviter tout effacement sans action volontaire de l'utilisateur. Règle absolue : une dictée ou une observation médicale ne doit jamais disparaître simplement parce que je change de zone dans l'application.

### Problème n° 11 — API Claude non synchronisée entre les appareils
Type : amélioration fonctionnelle / configuration et synchronisation. Priorité : HAUTE.

**Problème constaté.** J'ai intégré et configuré l'API Claude sur mon téléphone. Je souhaite pouvoir retrouver cette configuration automatiquement sur les autres appareils depuis lesquels j'utilise mon application médicale, sans renseigner manuellement la clé API à chaque changement d'appareil : mon téléphone, mes autres téléphones éventuels, mon ordinateur, ma tablette, tout autre appareil sur lequel je me connecte à mon application.

**Comportement attendu.** Lorsqu'une clé API Claude a été correctement configurée, cette configuration peut être utilisée sur mes autres appareils autorisés : 1. la configuration de l'API est conservée ; 2. l'API Claude est automatiquement disponible après authentification ; 3. lorsque je saisis mon code maître correct, l'application retrouve l'accès aux fonctionnalités d'intelligence artificielle ; 4. je n'ai pas besoin de saisir à nouveau la clé API sur chaque appareil ; 5. le fonctionnement est identique sur téléphone, tablette et ordinateur ; 6. la clé API reste protégée et n'est jamais affichée en clair.

**Correction demandée.** Mettre en place une configuration centralisée et sécurisée de l'accès à l'API Claude. La validation du code maître doit permettre à un appareil autorisé d'utiliser la configuration déjà existante. Ne pas exposer directement la clé API sur les différents appareils. Objectif : configurer l'API Claude une seule fois et retrouver automatiquement son fonctionnement sur tous mes appareils autorisés.

### 12. Exigences transversales
- **A. Navigation progressive** : un nombre limité de commandes principales à chaque étape ; les autres fonctions apparaissent selon le contexte.
- **B. Parcours de visite logique** : organisation de la tournée → patient sélectionné → appel → déplacement → arrivée → observation → dictée IA → compte rendu → prescriptions → fin de visite → patient suivant.
- **C. Rapidité** : toutes les actions répétitives nécessitent le minimum de manipulations possible.
- **D. Sauvegarde automatique** : toute dictée, observation ou saisie en cours est conservée ; la navigation entre les écrans n'entraîne pas de perte de travail.
- **E. Fonctionnement hors connexion** : l'application conserve localement les informations lorsqu'Internet est indisponible.
- **F. Cohérence médicale** : les observations et les prescriptions restent cohérentes avec le profil du patient, notamment son âge.
- **G. Organisation dynamique des tournées** : les nouvelles visites peuvent être ajoutées facilement et regroupées géographiquement.
- **H. Autonomie** : réaliser la majorité des tâches directement dans l'application, sans passer systématiquement par Claude ou un autre outil externe.
- **I. Synchronisation entre appareils** : les fonctionnalités configurées sont retrouvées automatiquement après authentification sur les appareils autorisés.
- **J. Préservation des fonctionnalités** : ne pas supprimer ou dégrader les fonctions déjà opérationnelles.

### 13. Tableau récapitulatif

| N° | Problème ou amélioration | Priorité |
|---|---|---|
| 1 | Navigation trop complexe et trop de boutons | CRITIQUE |
| 2 | Appel téléphonique du patient difficile d'accès | CRITIQUE |
| 3 | Mode voiture insuffisamment pratique | CRITIQUE |
| 4 | Intégration des nouvelles visites en cours de tournée | CRITIQUE |
| 5 | Dictée médicale IA qui ne démarre pas | CRITIQUE |
| 6 | Fonctionnement hors connexion insuffisant | CRITIQUE |
| 7 | Importation des photographies du dossier patient impossible | HAUTE |
| 8 | Observations pédiatriques contenant des informations d'adulte | CRITIQUE |
| 9 | Impression et enregistrement PDF non fonctionnels | HAUTE |
| 10 | Dictée médicale effacée lors d'un changement de zone | CRITIQUE |
| 11 | API Claude non synchronisée sur tous les appareils | HAUTE |

### 14. Contraintes
Ne pas supprimer les fonctionnalités existantes qui fonctionnent ; ne pas dégrader les calculs des posologies ; ne pas modifier sans nécessité la logique médicale des packs ; conserver toutes les demandes d'amélioration précédemment transmises ; vérifier chaque correction afin d'éviter les régressions ; privilégier la fluidité et la rapidité d'utilisation ; protéger les données médicales et les clés API.

Objectif final : une application qui me permette d'enchaîner efficacement mes consultations et mes visites à domicile — identifier rapidement mon patient, l'appeler immédiatement, lancer son itinéraire, réaliser ma visite, dicter une observation sans risque de perte, obtenir un compte rendu médical structuré, intégrer les photographies de son dossier, générer et imprimer ses documents, passer naturellement au patient suivant, intégrer de nouvelles demandes dans ma tournée, retrouver toutes mes fonctionnalités d'intelligence artificielle sur mes différents appareils.

---

## Suivi (rempli au fil des lots)

| N° | Lot | État initial (constaté) | Correction | État | Limites | Test |
|---|---|---|---|---|---|---|
| 10 | 1 | Non corrigé. **Cause** : choisir, ajouter ou retirer une fiche remettait l'observation à zéro (`state.obs={}`), dictée comprise ; la sauvegarde chiffrée n'avait lieu qu'au rafraîchissement de l'écran (pas à chaque frappe) ; le texte du panneau IA n'était pas gardé ; les photos dans le brouillon pouvaient faire échouer toute la sauvegarde (n° 7). | Sauvegarde chiffrée 250 ms après chaque frappe, à la mise en arrière-plan et à la fermeture ; changer de fiche, d'écran ou d'onglet IA ne vide plus rien ; restauration automatique à la réouverture (12 h) ; « Dictées récentes » : chaque dictée gardée chiffrée 48 h, même effacée ou remplacée, reprise d'un geste ; indicateur « ✓ enregistrée hh:mm:ss ». | **Corrigé** | Pas de données vocales en attente : la dictée du clavier iPhone produit directement du texte. « Nouveau patient » reste un effacement volontaire (le patient précédent est mis de côté dans « Patients validés »). | test_lot1.py (n°10, 10 tests) |
| 5 | 1 | Non corrigé. **Causes** : il n'existe pas d'enregistrement audio dans Packs ; le bouton « 🎙 Dicter le résumé de l'appel » de la tournée ne fait qu'ouvrir une zone de texte — inexistante quand la visite n'a ni téléphone ni motif (rien ne se passait) ; ailleurs le focus était donné hors du geste, et l'iPhone n'ouvre alors pas le clavier. | Carte « Dictée » toujours visible sous la fiche patient, avec ou sans fiche choisie : grand champ (≥ 6 lignes, texte 16 px), mode d'emploi du micro du clavier, interruption et reprise libres, enregistrée à chaque mot (n° 10), « Répartir dans l'observation », bouton IA. « 🎙 Dicter » donne le focus dans le geste, à défaut dans le grand champ. | **Corrigé** (dictée par le clavier) | **Reconnaissance vocale intégrée non retenue** : la reconnaissance vocale du navigateur (Web Speech) n'est pas fiable dans une application installée sur l'écran d'accueil de l'iPhone (indisponible ou interrompue selon les versions, dépend du réseau) ; la dictée du clavier iPhone est la voie fiable (traitée sur l'appareil sur les iPhone récents : à vérifier en mode Avion). Le compte rendu structuré reste local (« Répartir », compte rendu Packs) ou IA en ligne. | test_lot1.py (n°5, 3 tests) |
| 9 | 1 | Non corrigé. **Causes** : sur ordinateur, les deux barres de l'aperçu étaient fixées en bas et se superposaient : la moitié basse des boutons « Imprimer » et « Valider » du haut ne réagissait pas ; l'impression automatique était lancée hors du geste (ignorée par Safari et les apps installées, notamment sur iPad) ; « Imprimer / enregistrer en PDF » dépendait de la fenêtre d'impression ; sur iPhone l'impression n'existait qu'en secours caché. | Barre du haut collée en haut ; boutons « 🖨 Imprimer » (fenêtre d'impression dans le geste) et « ⬇ Enregistrer en PDF » (vrai fichier PDF A4 généré sur l'appareil, téléchargé ou partagé) sur ordinateur, tablette et iPhone ; tablette : PDF préparé d'avance ; iPhone : « Envoyer à l'imprimante », « Enregistrer le PDF » et « Impression » visibles. | **Corrigé** | Non vérifié sur l'appareil exact où le problème est apparu : à confirmer en garde. | test_lot1.py (n°9, 4 tests par écran) |
| 7 | 1 | Non corrigé. **Cause** : les photos étaient lues toutes à la fois en pleine résolution (pic de mémoire pouvant faire recharger la page sur iPhone) puis gardées dans le brouillon, dans le stockage local limité à environ 5 Mo : au-delà de quelques photos la sauvegarde échouait sans message (et emportait la dictée). | Compression une par une sur l'appareil (1 600 px, JPEG ≈ 150 à 400 Ko), coffre photos chiffré AES-GCM (IndexedDB, hors du brouillon), progression « Photo 3 / 12 », confirmation « ✓ 12 photos ajoutées (x Mo, chiffrées) · espace libre », refus expliqué avec la limite exacte (Mo libres), photos rechargées après fermeture, patient rouvert ou brouillon restauré ; purge des photos non rattachées après 14 jours. | **Corrigé** | Limite = espace de stockage du navigateur (affiché) ; marge de 8 Mo gardée. Photos imprimées 4 par page en fin de pack, comme avant. | test_lot1.py (n°7, 8 tests, 12 photos de 12 Mpx) |
| 8 | 1 | Non corrigé. **Cause** : le compte rendu reprenait le nom de la fiche tel quel (« Consultation pour gastro-entérite — adulte », « Diagnostic retenu : Gastro-entérite — adulte » chez un enfant de 3 ans ; « adulte + enfant » si les deux étaient choisies) ; les doses, elles, suivaient déjà l'âge et le poids. | Diagnostic du compte rendu sans variante d'âge et sans doublon ; alerte « Fiche adulte pour un patient de 3 ans » (et l'inverse) avec bascule en un geste vers la fiche de l'âge réel, observation conservée ; doses inchangées. | **Corrigé** | Les modèles d'observation sont neutres vis-à-vis de l'âge (vérifiés) ; la logique médicale des fiches n'est pas modifiée. | test_lot1.py (n°8, 5 tests) |

## Test PDF du 16/10/2026 (patient fictif, fiches « Chute du sujet âgé » + « Douleur en fin de vie »)

| N° | Constat | Correction | État | Test |
|---|---|---|---|---|
| PDF 1 | Le cadre du document coupait le texte qui dépassait (masqué à l'impression) et le texte pouvait passer sous le cachet. | Après affichage, chaque page est mesurée au format A4 : aucune ligne ne doit descendre dans la zone du cachet ou de la signature ; sinon la police est réduite par paliers jusqu'à 9 pt ; au-delà, le document est signalé à l'écran (« À raccourcir avant d'imprimer »), une confirmation est demandée avant l'impression, et le texte n'est jamais masqué. Le PDF reprend exactement les pages ajustées. | Corrigé | test_pdf16.py (contrôle sur tous les documents, police réduite, alerte) |
| PDF 2 | Deux courriers fusionnés sur une page (le second sans formule ni signature) ; consignes de deux fiches mêlées sans titre. | Un courrier = un destinataire = une page, chacun avec formule d'appel, formule finale et une seule ligne de signature ; consignes : un titre par fiche, et un document par fiche si la page ne suffit pas même en petite police. | Corrigé | test_pdf16.py |
| PDF 3 | « J'ai prescrit le bilan biologique, un ECG, une rééducation… et revu les médicaments » imprimé quoi qu'il soit coché ; « médicaments revus » dans les consignes ; 159 renvois au « compte rendu joint » (non imprimé) dans les fiches. | Phrases d'action vérifiées au moment d'imprimer (courriers, consignes, certificats, courriers assemblés) : « J'ai prescrit » réécrit avec la liste exacte des examens, soins et traitements cochés ; « médicaments revus » seulement si la case « Médicaments revus » est cochée (proposée quand une fiche en parle) ou si la dictée le dit ; « ont été prescrits » vérifié ; résultats d'examens annoncés seulement si des examens sont prescrits ; renvoi au compte rendu remplacé par les éléments dictés (« Éléments recueillis ce jour : … ») ou, à défaut, par « sont à votre disposition sur simple demande ». | Corrigé | test_pdf16.py (dont contrôle de toutes les fiches du catalogue) |
| PDF 4 | Fiche « Chute du sujet âgé — bilan » : HbA1c cochée d'office. Pas d'alerte si le patient a moins de 65 ans. | HbA1c en option non cochée (« diabète connu »), glycémie conservée ; alerte « Fiche « sujet âgé » pour un patient de 52 ans ». **Fiche modifiée : à relire** (ligne biologie uniquement). | Corrigé | test_pdf16.py |

## Garde du 16/10/2026 : « Packs conseille, le médecin décide »

**Constat.** Renouvellement d'un traitement psychiatrique ancien signalé « contre-indiqué » (ex. ESCITALOPRAM + HALOPÉRIDOL, thésaurus ANSM : torsades de pointes) : l'impression passait par une fenêtre système « Imprimer quand même ? » chargée du texte brut de l'ANSM, sans motif ni traçabilité (sur iPhone, facile à refermer par erreur).

**Correction (état : corrigé).**
1. Aucune contre-indication, interaction, dose ou durée ne bloque l'impression. Écran « Avant d'imprimer » : niveau (contre-indication, déconseillé, à vérifier), motif, source (thésaurus ANSM et sa version, RCP, critères du sujet âgé, allergie déclarée, contrôle de saisie), alternative proposée ; une même alerte venue de deux entrées du thésaurus n'apparaît qu'une fois.
2. « Je maintiens la prescription » (un geste), puis motif en une ligne, avec trois suggestions d'un toucher (« traitement ancien prescrit par le spécialiste, renouvellement à l'identique », « bénéfice supérieur au risque, patient informé », « avis spécialisé pris ») ; modifiable, dictable au micro du clavier ; vide → « motif non précisé » (jamais de blocage).
3. Motif et alerte au journal et au compte rendu (rubrique « Décisions de prescription ») ; jamais sur l'ordonnance ni sur aucun document imprimé. La décision vaut pour la consultation (pas de nouvel écran à la réimpression) ; « Nouveau patient » la remet à zéro.
4. Conseils liés à l'alerte proposés et cochables (torsades : appeler le 15 en cas de malaise ; sédation : conduite et alcool ; saignement ; chute), ajoutés aux consignes imprimées s'ils sont cochés.
5. Règles légales de forme : stupéfiant → « ordonnance sécurisée à rédiger à la main » affiché, le reste s'imprime ; ligne incomplète → « non imprimé faute de donnée : compléter le champ » affiché (aucune ligne ne disparaît sans le dire).
6. Test : tests/test_ciover.py (37 tests, 375 px et ordinateur).

**Blocages silencieux recherchés dans tout le code** (alertes suivies d'un abandon, boutons grisés, retours sans message) :

| Endroit | Avant | Maintenant |
|---|---|---|
| Impression avec alerte (interaction, contre-indication, sujet âgé, poids, allergie) | « Imprimer quand même ? » sans motif ni traçabilité | Écran d'alerte, maintien motivé, traçabilité au journal et au compte rendu |
| Ajout d'une injection intramusculaire sous anticoagulant (suggestions de la feuille) | Refusé (alerte puis rien) | Ligne ajoutée avec avertissement ; décision à l'impression |
| Lignes avec un champ manquant (`{f:…}` non rempli) | Retirées de l'impression sans aucun message | Liste « Non imprimé faute de donnée » affichée dans l'aperçu et l'écran d'alerte |
| Bouton « Imprimer » du haut sur iPhone sans fiche choisie | Grisé sans explication | Actif : « Choisissez d'abord une fiche (motif) » |
| « ＋ Ajouter cette lésion » (certificat de lésions) | Grisé, explication seulement dans le texte voisin | Explication au toucher (« Choisissez d'abord le type et le siège ») |
| « Régénérer » (courrier assemblé) | Grisé sans explication | « Rien à régénérer : le texte n'a pas été modifié » |

Restent volontairement grisés, avec leur explication à l'écran : « Signature et cachet » sans profil activé (« profil non activé »), « Continuer » de la clé de secours (case « Je l'ai notée » à cocher), « Envoyer » de l'IA (motif du blocage affiché : fuite d'identité, hors connexion, plafond), « Voir ce qui part » d'un document (« Recadrage ou masquage obligatoire »), entrées du petit choix IA (raison sous chaque entrée), « Optimiser » pendant un calcul (état affiché), boutons de déchiffrement ou de chiffrement pendant l'opération (état affiché). « Renseigne le nom du patient avant d'imprimer » reste une règle de forme (nom obligatoire sur une ordonnance) : le message dit quoi faire et place le curseur dans le champ.
