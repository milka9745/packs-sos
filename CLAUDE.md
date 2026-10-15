# Packs SOS — instructions pour Claude Code

Tu travailles pour le Docteur Mickaël DEIE, médecin généraliste et urgentiste, SOS Médecins Orléans (visites et consultations de garde). Il signe toujours « Docteur Mickaël DEIE ». Il lit sur iPhone : réponses courtes, en français, directives.

**Mission** : rédiger tout le catalogue de fiches du fichier `docs/SOMMAIRE-CATALOGUE.md` (264 fiches, lot 1 déjà fait) et l'intégrer dans `index.html`, bloc par bloc, jusqu'à la fin. Quand il écrit « suivant » ou « continue », tu reprends au bloc suivant sans rien redemander.

## Règles de sécurité du dépôt (absolues)
- Travaille **uniquement sur la branche `catalogue`**. Ne pousse **jamais** sur `main` : `main` est l'outil en service pendant les gardes. Il fusionne lui-même, ou te demande explicitement « publie ».
- Ne touche jamais aux dossiers `v38/`, `v39/`, `ocr/`, ni à `profil.json`. Ne remets jamais de signature, de cachet, de nom ou d'Adeli en clair dans un fichier.
- Change le moins de choses possible en dehors des fiches. Ne modifie jamais une fiche validée (lot 1, `PACKS_V40`) sans le signaler.
- Avant chaque commit : `node --check` sur chaque bloc `<script>` d'`index.html`, puis `python tests/test_packs.py` (tous les tests doivent passer ; ajoute 2 à 4 tests par bloc).
- Un commit par bloc, message en français : « Bloc N — appareil — X fiches ». Renomme le cache dans `sw.js` (`packs-sos-v40`, puis `packs-sos-v40b`, `v40c`…) et `APP_VERSION` reste « 40 ».

## Philosophie médicale (appliquée sans redemander)
- Recommandations françaises à jour (HAS, SPILF, GPIP, SFP, SFMU, SPLF, SFD, CRAT, ANSM, RCP de la base de données publique des médicaments). Vérifie chaque posologie sur sa source (recherche web). Ne jamais inventer une dose ; si une donnée manque, la ligne n'est pas créée et le point est listé dans le rapport.
- Réécrire, ne jamais recopier les sources. Pas de renvoi à Antibioclic : écrire les alternatives.
- Quand une recommandation diverge de sa pratique, **sa convention s'applique** et l'écart est écrit dans le mémo de la fiche.
- Antibiotiques : jusqu'à **5 alternatives** explicites (choix exclusif `grp:"atb"`), adaptées à l'âge, aux antécédents, aux allergies, à la grossesse, au rein et aux traitements.
- AINS : BI-PROFÉNID LP 100 mg matin et soir en premier, ibuprofène 400 mg en option. Palier 2 : ACUPAN 30 mg toutes les 6 h, IZALGI 1 à 2 gélules toutes les 6 h. **Pas de tramadol.** Palier 3 (sujet âgé, douleur intense) : ACTISKENAN 5 mg toutes les 4 h + SKENAN LP 10 mg matin et soir, ou ORAMORPH si troubles de la déglutition : ligne `jr:true` (jamais imprimée, journal et compte rendu si cochée).
- Disponibilité : pour chaque médicament, vérifier sur la base des médicaments qu'il est commercialisé en France, disponible en pharmacie de ville et prescriptible par un généraliste (pas de réserve hospitalière, de prescription hospitalière, de prescription initiale hospitalière ou de spécialiste, de médicament d'exception non signalé, ni de rupture connue). Sinon, le retirer ou écrire la restriction dans le mémo, et le lister dans le rapport.
- **Jamais de lopéramide.** Infection urinaire de l'adulte à risque : recommandation des sociétés savantes en première intention, OROKEN 200 mg matin et soir en option décochée (convention, écart écrit au mémo). Vomissements de l'enfant : ondansétron hors AMM option 1, VOGALÈNE option 2. Myorelaxant et corticoïde oral en option dans le rachis.
- Conventions : DOLIPRANE 1 g toutes les 6 h ; SPASFON LYOC 160 mg adulte / 80 mg enfant ; SERESTA 10 mg ; VOGALÈNE selon le RCP (lyoc 7,5 mg ou suppositoire 5 mg) ; FORTRANS 1 sachet dans 1 L (fécalome) ; ADIARIL.
- SpO2 d'appel du 15 : 90 %. Durées d'arrêt : gastro 3 j, angine 2 à 3 j, lombalgie 5 à 7 j selon le métier ; sinon référentiel CNAM ; ajouter le motif à `AT_DUREES`.
- Pédiatrie : dose au poids avec les gabarits existants, arrondie à une valeur pratique, dose maximale indiquée.
- Toujours prévoir : enfant, grossesse, allaitement, allergie, insuffisance rénale, sujet âgé.
- Cotation (convention SOS Médecins Orléans) : VG + MU (ou VG + MD), G + CRN / VG + VRN ou G + CRM / VG + VRM selon l'heure, MEG / MOP selon l'âge, ECG DEQP003 (+ YYYY090 en visite) ; jamais MDN, MDI, MM ni F. Sutures : orientation vers les urgences le soir et le week-end.
- Documents imprimés : une page par document, aucun trou (pas de « à compléter », de crochet ni de champ vide).
- Aucune donnée de patient réel, nulle part.

## Format d'intégration (modèle : `PACKS_V40` dans `index.html`)
- Chaque bloc ajoute un tableau `PACKS_V40_Bn` juste après le précédent, puis la même boucle : un pack existant de même nom est remplacé, sinon ajouté.
- Pack : `{n:"Nom — variante", k:"mots-clés du patient et de la régulation", s:[feuilles]}`. Feuilles : `med`, `bio`, `img`, `kine`, `ide`, `dm`, `podo`, `para`, `cert`, `let`, `cons`, `memo`.
- Ligne : texte simple, ou objet `{t, grp, opt, alt, sr, jr}` : `grp` = choix exclusif ; `opt:true` = décochée par défaut ; `sr:"s"` pack simple seulement, `sr:"r"` pack à risque seulement ; `jr:true` = jamais imprimée.
- Gabarits : `{ml:x|max}`, `{mg:x|max|pas}`, `{mgpk:x|max|cp}`, `{agelt:ans|bas|haut}`, `{wlt:kg|bas|haut}`, `{agemin:ans|nom}`, `{tiorfan}`, `{vog}`, `{patient}`, `{f:champ}`. Les notes entre parenthèses commençant par « si », « indiqué », « alternative », « sauf », « allergie »… sont affichées à l'écran mais retirées à l'impression (`DNOTE_RE`).
- Feuille `memo` (lignes `opt:true`) : gravité et orientation, critères simple / à risque, variantes, liste de vérification (bloquant / à documenter / facultatif), traçabilité, fiches voisines et durée de visite, sources avec année, et la ligne de statut : « Statut : fiche non relue (bloc N, version 1). »
- Feuille `cons` : langage simple, consignes de reconsultation et d'appel du 15.

## Ordre des blocs (25 à 30 fiches chacun, un appareil à la fois)
ORL et ophtalmologie restants → respiratoire → digestif → uro-néphrologie → rhumatologie et traumatologie → dermatologie → pédiatrie → neurologie → psychiatrie → cardio-vasculaire → gynécologie-obstétrique → infectiologie et endocrinologie → gériatrie, intoxications, soins palliatifs → administratif et renouvellement → fiches ◇ premier recours. Dans chaque bloc : ★★★, puis ★★, puis ★.

## Rapport en fin de bloc (court, pour iPhone)
1. Fiches faites (numéros).
2. Fiches à fort risque (anticoagulants, insuline, pédiatrie au poids, intoxications, soins palliatifs) : 2 lignes chacune pour relecture rapide.
3. Points non trouvés ou divergences vraies : une question par point, sinon rien.
4. Résultat des tests.
5. Bloc suivant.

## Garde-fous
- Chaque nouvelle fiche est « non relue » ; elle devient « validée » quand il l'a utilisée en garde sans la corriger (il donne les numéros : mets à jour la ligne de statut).
- Aucune fiche « non relue » ne part aux collègues.
