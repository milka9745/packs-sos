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
| 1 | Partiel (« Commencer » ouvrait l'arrêt mais gardait le patient, le pack et l'observation précédents ; téléphone et adresse non reportés ; pas de défilement vers la fiche) | « Commencer » ou « Patient en cours » : le patient affiché est mis de côté (récupérable dans « Patients validés »), dossier vierge, nom, naissance, motif (observation et recherche de pack), téléphone et adresse (note d'honoraires) préremplis, défilement vers la fiche patient. | Le pack n'est pas sélectionné automatiquement : le motif est proposé dans la recherche (choix du médecin). Sexe et poids non lus sur la fiche de régulation. | « correctif 1 » |
| 2 | Partiel (assistant IA v40 : dictée, courrier et question, nom et date de naissance seulement retirés ; posologies possibles de l'IA ; aucun import de document) | v41 : IA facultative (Aucun / Partiel / Complet), anonymisation sur l'appareil validée par le DPO (identité, naissance → âge, adresse, téléphone, NIR, lieux précis, dates → J-x ; hôpital et ville en clair), écran « Ce qui part » obligatoire, identité remise au retour, posologies jamais issues de l'IA. Import d'une photo ou capture (biologie, ordonnance, ECG, compte rendu) : identité repérée et noircie par la lecture locale, recadrage ou masquage et vérification obligatoires, dernière lecture bloquante, envoi du texte anonymisé ou de l'image ré-encodée sans métadonnées. | PDF non lus (capture d'écran). La lecture locale peut manquer un nom manuscrit : la vérification du médecin reste obligatoire. Valeurs lues sur une image à contrôler sur le document. | tests/test_anon.js, test_ia.py, test_doc.py, test_dictees.py |
| 3 | Non corrigé (cotation calculée sur l'heure de première impression ; aucune heure modifiable) | Trois heures distinctes : arrivée et acte (modifiables dans la cotation avant impression ; par défaut arrivée = début de saisie, acte = arrivée) et validation (impression). La cotation (tranches N, M, D) suit l'heure de l'acte ; dans le journal, l'heure de l'acte est cliquable et modifiable ; le récapitulatif de garde affiche l'heure de l'acte. | Le rattachement d'une ligne à une garde reste fondé sur l'heure de validation. L'heure d'appel de la régulation n'est pas lue sur les fiches. | « correctif 3 » |
| 4 | Partiel (lien d'appel caché dans « Régulation et interrogatoire », replié ; absent avant « Commencer » et dans l'écran Tournée ; aucun champ téléphone pour un arrêt saisi à la main) | Bouton 📞 visible dans la carte « Visite en cours », dans « Prochain arrêt » (« Appeler avant de partir »), dans l'écran Tournée et dans la barre du haut sur iPhone (patient en cours) ; champ Téléphone dans « Modifier » un arrêt. | Le numéro masqué dépend du réglage iPhone (un lien d'appel ne peut pas ajouter #31#). | « correctif 4 » |
| 5 | Partiel (pack, doses, documents et journal hors ligne ; IA en ligne seulement) | Hors connexion : IA coupée automatiquement, aucun envoi ni file d'attente ; lecture locale des documents hors ligne. Étude de l'IA hors ligne sur iPhone : docs/08-IA-HORS-LIGNE.md (pas fiable dans Safari ; possible en application native avec le modèle d'Apple, textes courts ; relecture des manques par règles recommandée). | IA générative hors ligne non intégrée. Dictée du clavier hors ligne en français à vérifier en mode Avion. | test_ia.py (« hors connexion ») |
| 6 | Partiel (initiale seule : « D. ») | Libellé « initiale du nom · âge · rue » (ex. « D. · 76 ans · Rue de Bourgogne ») dans la carte de visite, la liste et l'écran Tournée, la carte (bulle), les patients validés et les messages ; âge en mois avant 2 ans. Affichage local uniquement : seules les coordonnées partent vers la cartographie. | Sans date de naissance ou sans adresse géocodée, le libellé est raccourci (initiale · rue, ou repère saisi). | « correctif 6 » |
| 7 | Non corrigé (reproduit : « Lombosciatique aiguë » → « Tique retirée ce jour », « Morsure de tique » au diagnostic, histoire et examen d'un autre motif ; co-patients héritant des antécédents, traitements, allergies, grossesse du patient principal) | Modèles d'observation : un seul modèle, le plus spécifique, sur mots entiers ; modèle lombosciatique séparé, en liste à compléter ; regex resserrées (toux, alcool, tique, brûlure, grippe). Co-patient : observation, constantes, traitements, allergies, grossesse et allaitement remis à vide. | Les modèles restent des suggestions grisées ; certains textes « Proposé » décrivent des gestes (ECG, TROD) que le médecin doit vérifier avant de cliquer. La sélection d'un nouveau pack efface toujours l'observation déjà saisie. | « correctif 7 » (2 tests) |
| 8 | Non corrigé (examen normal détaillé, « Reste de l'examen normal », « État stable », « accord obtenu », histoire et diagnostic types insérés au compte rendu sans action du médecin) | Le compte rendu ne reprend que les appareils saisis, dictés ou validés (« Normal », « Proposé », nouveau bouton « Normal sur les appareils non saisis ») ; sinon « Examen clinique non renseigné » ; plus d'évolution, de traçabilité ni d'histoire par défaut ; textes types affichés en suggestion grisée. | Le texte « normal » du système Général affirme « apyrétique » : à ne valider qu'après prise de température (corrigé automatiquement si T ≥ 38 °C saisie). | « correctif 8 » (2 tests) |
| 9 | Partiel (ordre optimisé, prioritaires d'abord, mais aucun point d'arrivée ni créneau horaire) | Choix de l'arrivée dans l'écran Tournée : aucune, cabinet, ou autre adresse (consultation suivante, domicile, point choisi, avec suggestions d'adresses) ; le trajet se termine au plus près de ce point. Champ « à voir avant HH:MM » par arrêt : ordre prioritaires → arrêts à heure (dans l'ordre des heures) → autres ; heure d'arrivée estimée (trajet + 20 min par visite) et alerte « risque de dépassement ». | Pas d'optimisation globale sous contrainte horaire (le service d'itinéraire ne le permet pas) : les arrêts à heure sont pris dans l'ordre des heures. Durée de visite fixe (20 min). | « correctif 9 » (itinéraires simulés) |
| 10 | Non corrigé (une page A4 par document) | Option « 2 documents par feuille A4 (hors ordonnances) », décochée par défaut, mémorisée : certificats, courriers et consignes consécutifs regroupés en deux demi-pages (impression et PDF iPhone) ; signature et cachet suivent le texte. Contrôle après affichage : un document qui ne tient pas est remis en pleine page, jamais tronqué. Ordonnances, note d'honoraires et photos toujours en pleine page. | Un courrier long repasse en général en pleine page. Les documents ne sont regroupés que s'ils se suivent. | « correctif 10 » (2 tests) |
