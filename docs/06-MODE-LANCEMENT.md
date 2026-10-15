# Mode lancement du catalogue (décidé le 15/10/2026)

Quand j'écris **« suivant »** dans une nouvelle conversation de ce projet, Claude enchaîne sans me redemander mes règles.

## Ce que Claude fait à chaque « suivant »
1. Récupère `index.html` à jour sur https://github.com/milka9745/packs-sos (dépôt public), et le doc « Packs SOS — Lot 1 » comme modèle.
2. Prend le prochain bloc du `SOMMAIRE-CATALOGUE.md` : 25 à 30 fiches, un appareil à la fois, les plus fréquentes d'abord (★★★, puis ★★, puis ★, les ◇ premier recours en dernier).
3. Rédige chaque fiche au format du cahier des charges, vérifie chaque posologie sur sa source (RCP, HAS, sociétés savantes, CRAT), sans renvoi à Antibioclic.
4. Intègre les fiches dans Packs (format des packs v40 : simple / à risque, alternatives, lignes « journal + CR », mémo « Pour le médecin »), teste (iPhone 375 px et PC, jour et nuit, grand texte), renomme le cache du service worker, livre un zip `index.html` + `sw.js`, les tests et les captures.
5. Termine par : fiches faites, fiches à fort risque à relire en 2 lignes, prochain bloc prévu.

## Ma philosophie (appliquée sans me redemander)
- Recommandations françaises à jour ; quand elles divergent de ma pratique, ma convention est appliquée et l'écart est écrit dans la fiche.
- Antibiotiques : jusqu'à 5 alternatives explicites, adaptées à l'âge, aux antécédents, aux allergies, à la grossesse, au rein et aux traitements.
- AINS : kétoprofène LP 100 mg matin et soir (ibuprofène 400 mg en option). Palier 2 : ACUPAN 30 mg toutes les 6 h ; IZALGI 1 gélule toutes les 4 à 6 h, 4 par jour au maximum (RCP). Pas de tramadol. Palier 3 (sujet âgé, douleur intense) : ACTISKENAN 5 mg toutes les 4 h + SKENAN LP 10 mg matin et soir, ou ORAMORPH si troubles de la déglutition — jamais imprimé, inscrit au journal et au compte rendu si coché.
- Jamais de lopéramide. Infection urinaire de l'adulte à risque : OROKEN 200 mg matin et soir. Vomissements de l'enfant : ondansétron hors AMM en option 1, VOGALÈNE en option 2. Myorelaxant et corticoïde oral en option dans le rachis.
- SpO2 d'appel du 15 : 90 %. Durées d'arrêt : gastro 3 j, angine 2 à 3 j, lombalgie 5 à 7 j selon le métier ; durée d'arrêt inscrite au journal.
- Cotation : VG + MU (ou VG + MD), G + CRN / VG + VRN ou G + CRM / VG + VRM selon l'heure, MEG / MOP selon l'âge, ECG DEQP003 (+ YYYY090 en visite) ; jamais MDN, MDI, MM ni F. Sutures : orientation aux urgences le soir et le week-end.
- Questions seulement si les recommandations divergent vraiment ou s'il manque une information locale.

## Garde-fous
- Chaque nouvelle fiche porte dans Packs le statut « non relue » ; elle passe « validée » quand je l'ai utilisée en garde sans la corriger (je donne les numéros).
- Aucune fiche « non relue » ne part aux collègues ; avant leur essai : passe de validation rapide et avis réglementaire de l'association (dispositif médical).
- Fiches à fort risque (anticoagulants, insuline, pédiatrie au poids, intoxications, soins palliatifs) : résumé en 2 lignes pour relecture rapide à la fin de chaque bloc.

## État
- Lot 1 (15 fiches) : validé le 15/10/2026, intégré dans Packs v40.
- Prochain bloc : ORL, ophtalmologie et respiratoire restants (★★★ et ★★ d'abord).
