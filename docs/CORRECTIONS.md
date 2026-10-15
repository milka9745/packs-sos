# Cahier des corrections et améliorations — application Packs SOS

Date : 15 octobre 2026 · Rédigé par le Docteur Mickaël DEIE à partir de l'usage réel en visite.

## Consignes générales

1. Vérifier pour chaque problème si une correction a déjà été implémentée.
2. Identifier les fonctionnalités absentes, incomplètes ou défaillantes.
3. Corriger les bugs existants en priorité, en particulier ceux qui peuvent générer des erreurs médicales.
4. Implémenter les améliorations en respectant le fonctionnement actuel de l'application.
5. Préserver les fonctionnalités déjà opérationnelles.
6. Ne considérer aucun problème comme résolu sans vérification (test).

Règle absolue : aucune donnée médicale ne doit être ajoutée au dossier comme un fait clinique sans provenir d'une information réelle ou d'une validation du médecin.

## Registre des problèmes

| N° | Problème | Périmètre |
|---|---|---|
| 1 | Démarrage des visites : le bouton « Commencer » doit réellement lancer la visite et ouvrir directement le dossier du patient. | catalogue |
| 2 | Intégration de l'IA médicale : importation et analyse de documents, ordonnances, ECG, images et observations, avec anonymisation maximale. | **session v41** |
| 3 | Cotations horaires : distinguer et modifier les heures d'arrivée, de réalisation de l'acte et de validation, pour appliquer la bonne cotation. | catalogue |
| 4 | Appel patient : bouton d'appel immédiatement visible et utilisable depuis la fiche patient, notamment sur iPhone. | catalogue |
| 5 | Mode hors connexion : fonctions essentielles sans Internet ; étudier certaines fonctions IA hors ligne. | **session v41** |
| 6 | Identification des patients : remplacer l'initiale seule par une présentation qui distingue les patients — **initiale du nom + âge + rue**. | catalogue |
| 7 | Erreurs dans les packs : supprimer les informations venant d'autres motifs ou champs (ex. : « Lombosciatique aiguë » introduit une morsure de tique non sélectionnée et des antécédents inadéquats). | catalogue, **priorité 1** |
| 8 | Examens cliniques personnalisés : adapter les propositions au contexte, à la dictée et aux observations ; ne jamais présenter un examen standard comme réalisé sans validation. | catalogue, **priorité 1** |
| 9 | Optimisation des tournées : ordonner les visites selon adresses et horaires pour finir près du prochain lieu de consultation, à défaut du domicile ou d'un point choisi. | catalogue |
| 10 | Impression : deux documents distincts sur une même feuille A4 quand contenu et lisibilité le permettent — **en option, jamais pour l'ordonnance**. | catalogue |

Ordre de traitement décidé : 7 et 8 d'abord (risque médical), puis 1, 3, 4, 6, 9, 10. Les points 2 et 5 sont réservés à la session v41.

## Suivi

Pour chaque point : état initial (déjà corrigé / partiel / non corrigé / à vérifier), correction réalisée, limites restantes, test associé dans `tests/test_packs.py`.

| N° | État initial | Correction | Limites | Test |
|---|---|---|---|---|
| 1 | | | | |
| 3 | | | | |
| 4 | | | | |
| 6 | | | | |
| 7 | Non corrigé (reproduit : « Lombosciatique aiguë » → « Tique retirée ce jour », « Morsure de tique » au diagnostic, histoire et examen d'un autre motif ; co-patients héritant des antécédents, traitements, allergies, grossesse du patient principal) | Modèles d'observation : un seul modèle, le plus spécifique, sur mots entiers ; modèle lombosciatique séparé, en liste à compléter ; regex resserrées (toux, alcool, tique, brûlure, grippe). Co-patient : observation, constantes, traitements, allergies, grossesse et allaitement remis à vide. | Les modèles restent des suggestions grisées ; certains textes « Proposé » décrivent des gestes (ECG, TROD) que le médecin doit vérifier avant de cliquer. La sélection d'un nouveau pack efface toujours l'observation déjà saisie. | « correctif 7 » (2 tests) |
| 8 | Non corrigé (examen normal détaillé, « Reste de l'examen normal », « État stable », « accord obtenu », histoire et diagnostic types insérés au compte rendu sans action du médecin) | Le compte rendu ne reprend que les appareils saisis, dictés ou validés (« Normal », « Proposé », nouveau bouton « Normal sur les appareils non saisis ») ; sinon « Examen clinique non renseigné » ; plus d'évolution, de traçabilité ni d'histoire par défaut ; textes types affichés en suggestion grisée. | Le texte « normal » du système Général affirme « apyrétique » : à ne valider qu'après prise de température (corrigé automatiquement si T ≥ 38 °C saisie). | « correctif 8 » (2 tests) |
| 9 | | | | |
| 10 | | | | |
