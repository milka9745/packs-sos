# Mode lancement du catalogue (décidé le 15/10/2026, mis à jour le 20/10/2026)

Quand j'écris **« suivant »** dans une nouvelle conversation de ce projet, Claude enchaîne sans me redemander mes règles.

## Ce que Claude fait à chaque « suivant »
1. Travaille sur la branche `ia` du dépôt https://github.com/milka9745/packs-sos (worktree local), à partir d'`index.html` à jour ; le modèle de fiche est le lot 1 (`PACKS_V40`).
2. Avant tout nouveau bloc, fournit le tableau récapitulatif de l'existant et du travail restant (`docs/ETAT-CATALOGUE-<date>.md`) et attend la validation du périmètre.
3. Prend le prochain bloc du `SOMMAIRE-CATALOGUE.md` parmi les fiches réellement manquantes ou incomplètes (voir « État »), sans recréer une fiche existante ; ★★★, puis ★★, puis ★ ; les ◇ premier recours en dernier.
4. Rédige chaque fiche au format du cahier des charges, vérifie chaque posologie sur sa source (RCP de la base de données publique des médicaments, HAS, sociétés savantes, CRAT), sans renvoi à Antibioclic ; le RCP fixe âges, doses maximales et contre-indications (décision du 18/10/2026 : le RCP prime, l'écart avec une recommandation est écrit au mémo).
5. Intègre les fiches dans Packs (bloc `PACKS_V40_Bn` : simple / à risque, alternatives, lignes « journal + CR », mémo « Pour le médecin » avec ligne de statut), teste (`node --check`, suites Playwright iPhone 375 px et PC, jour et nuit, grand texte, PDF WebKit), tamponne la version (`tools/stamp_version.py 41x` : `APP_BUILD`, cache `packs-sos-v41x`, `version.json`), un commit par bloc « Bloc N — appareil — X fiches » sur `ia`.
6. Publie **sur /test/ seulement** (`tools/build_test.py` depuis `ia`, poussé dans `test/` de main) ; jamais à la racine de main sans « publie ». Plus de zip.
7. Termine par : fiches faites, fiches à fort risque à relire en 2 lignes, résultat des tests, prochain bloc prévu.

## Ma philosophie (appliquée sans me redemander)
- Recommandations françaises à jour ; quand elles divergent de ma pratique, ma convention est appliquée et l'écart est écrit dans la fiche.
- Antibiotiques : jusqu'à 5 alternatives explicites, adaptées à l'âge, aux antécédents, aux allergies, à la grossesse, au rein et aux traitements.
- AINS : kétoprofène LP 100 mg matin et soir (ibuprofène 400 mg en option). Palier 2 : ACUPAN 30 mg toutes les 6 h ; IZALGI 1 gélule toutes les 4 à 6 h, 4 par jour au maximum (RCP). Pas de tramadol. Palier 3 (sujet âgé, douleur intense) : ACTISKENAN 5 mg toutes les 4 h + SKENAN LP 10 mg matin et soir, ou ORAMORPH si troubles de la déglutition — jamais imprimé, inscrit au journal et au compte rendu si coché.
- Jamais de lopéramide. Infection urinaire de l'adulte à risque : OROKEN 200 mg matin et soir. Vomissements de l'enfant : ondansétron hors AMM en option 1, VOGALÈNE en option 2. Myorelaxant et corticoïde oral en option dans le rachis.
- Suspensions avec pipette dose-poids : « dose-poids » seulement dans l'étendue de la pipette, sinon ml et mg ; toujours ml et mg (18/10/2026).
- SpO2 d'appel du 15 : 90 %. Durées d'arrêt : gastro 3 j, angine 2 à 3 j, lombalgie 5 à 7 j selon le métier ; durée d'arrêt inscrite au journal.
- Cotation : VG + MU (ou VG + MD), G + CRN / VG + VRN ou G + CRM / VG + VRM selon l'heure, MEG / MOP selon l'âge, ECG DEQP003 (+ YYYY490 en visite) ; jamais MDN, MDI, MM ni F. Sutures : orientation aux urgences le soir et le week-end.
- Mémo médecin (indications, critères, scores) entre parenthèses : affiché à l'écran, jamais imprimé ; règles de décision (Ottawa, Centor, CRB-65…) dans les scores de l'application, au compte rendu seulement.
- Questions seulement si les recommandations divergent vraiment ou s'il manque une information locale.

## Garde-fous
- Chaque nouvelle fiche porte dans Packs le statut « non relue » ; elle passe « validée » quand je l'ai utilisée en garde sans la corriger (je donne les numéros). Une fiche validée puis modifiée porte « modifiée le <date> — à relire ».
- Aucune fiche « non relue » ne part aux collègues ; avant leur essai : passe de validation rapide et avis réglementaire de l'association (dispositif médical).
- Fiches à fort risque (anticoagulants, insuline, pédiatrie au poids, intoxications, soins palliatifs) : résumé en 2 lignes pour relecture rapide à la fin de chaque bloc.
- Envoi automatique vers l'IA désactivé tant que la validation du DPO et l'hébergement du fournisseur restent ouverts : chaque envoi est validé à l'écran « Ce qui part ».

## État (20/10/2026 — détail dans `docs/ETAT-CATALOGUE-2026-10-20.md`)
- Lot 1 (15 fiches) : validé le 15/10/2026 ; 7 d'entre elles modifiées depuis (pipettes, otite, sexe…) et marquées « à relire ».
- Blocs 2 à 15 : intégrés dans Packs (`PACKS_V40_B2` à `B15`), statut « non relue ».
- Couverture du sommaire (264 fiches) : **258 complètes**, 5 incomplètes (4 anciennes fiches de base sans mémo ni statut : apnées du sommeil, parasitose digestive, épicondylite, dysthyroïdie ; 1 aide-mémoire : décès à domicile), **1 absente : érythème fessier**. L'application compte 398 fiches (variantes adulte / enfant, fiches « à la carte », anciennes fiches de base).
- Le développement du catalogue est donc presque terminé ; **le travail restant est surtout la relecture en garde** (240 fiches « non relues », dont 9 ★★★ : malaise-syncope, COVID-19, pneumopathie, douleur dentaire, conjonctivite, douleur abdominale, anxiété, contusion, renouvellement).
- Prochain bloc proposé (sous réserve de validation du périmètre) : **bloc 16 — complément**, 6 fiches : érythème fessier (nouvelle) ; apnées du sommeil, parasitose digestive, épicondylite, dysthyroïdie (mise au format catalogue : mémo, statut, consignes) ; décès à domicile (aide-mémoire → consignes à l'entourage et courrier, si souhaité). Ensuite : campagne de validation des fiches ★★★ en garde.
