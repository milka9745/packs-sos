# Lot 1 — parcours patient en 6 états (02/11/2026, branche ia, publié sur /test/)

## Fait
- **Une seule machine à états** (`filState`) : Demande → En route → Sur place → Prise en charge → Sortie, plus « Entre deux » (nouvelle demande, prioritaire sur Demande et En route, jamais pendant la consultation). En consultation au cabinet : « Consultation · étape 1 sur 3 ».
- **Barre fixe en bas, 3 actions aux mêmes places** ; la 3e (à droite) fait avancer et porte la mise en avant (en route : « Naviguer » tant que la navigation n'est pas lancée, puis « Je suis arrivé »).
  - Demande : Ajouter des fiches · Appel masqué · Lancer la tournée
  - En route : Naviguer · Appeler · Je suis arrivé (Naviguer ouvre aussi l'écran conduite)
  - Sur place : Scanner · Dicter · Choisir la fiche
  - Prise en charge : Examen complet · Pack simple ⇄ à risque · Imprimer (+ compte rendu copié) ; Express : son « Imprimer et valider » est déplacé dans la barre
  - Sortie : Courrier · Réimprimer · Valider · patient suivant (confirmation au 2e toucher, inchangée)
  - Entre deux : Rendre à la régulation (2 touchers, tracé) · En fin de tournée · Insérer au mieux, avec l'impact affiché au-dessus
- **Doublons retirés** : Imprimer et Appeler de la barre du haut, « Fin de consultation » et « Imprimer · n » du bas, boutons d'action de la carte patient (Commencer, Je suis arrivé, Dictée, Prescriptions, IA, Valider, Réimprimer, Appeler ×3), Valider en double dans « Plus », bascule Simple / À risque du titre, bandeau d'étapes du téléphone, « IA » de l'accueil, « Ajouter des fiches » de l'accueil Express, « Scanner » de la carte Documents à l'étape Sur place, « + » doublant chaque fiche du catalogue.
- **Catalogue** : sans motif, 12 fiches fréquentes et « Tout le catalogue (n fiches) » au lieu des 399 fiches d'un coup.
- **« Plus »** (carte patient) : appels secondaires (masqué, appeler le suivant, mémo d'appel), Mode voiture, Tournée, **Ordre manuel**, Libérer, autre appli, ajouter une visite.
- **Ordre automatique** (points 10 et 11) : « Optimiser l'ordre » supprimé ; recalcul seul à chaque événement (fiches ajoutées, tournée lancée, patient validé, demande rendue), depuis la position lue une seule fois à ce moment (jamais de suivi), message d'une ligne « Ordre automatique · depuis ma position · recalculé à HH h MM ». « Ordre manuel » fige l'ordre (▲ ▼ sur chaque visite, trajets et heures mis à jour).
- **Code mort retiré** : `renderDriveV40`, branches inatteignables de l'ancienne carte v39 (5,2 Ko).
- **Batterie** : aucun nouveau minuteur ; la géolocalisation continue reste limitée à l'option « Tu es arrivé ? » pendant le trajet (inchangé) ; l'ordre automatique ne fait qu'une lecture ponctuelle.

## Boutons visibles (iPhone 375 px)
| État | Avant | Après |
|---|---|---|
| Demande | 817 | 24 |
| En route | 33 | 23 |
| Sur place | 33 | 22 |
| Prise en charge | 72 | 60 |
| Sortie | 72 | 59 |
| Entre deux | — | 22 |

Express : 7 / 17 / 16 / 27. Ordinateur : 32 / 31 / 30 / 69 / 68 / 31. Objectif < 120 atteint partout.
Restent en prise en charge des commandes par élément (✎ par ligne, Tout cocher / Tout décocher par feuille, Retirer par appareil de l'examen) : à regrouper au lot 3 (documents dans le flux).

## Temps mesurés (changement d'état, au toucher)
- 375 px jour / nuit / grand texte et ordinateur : 8 à 155 ms par changement d'état (objectif < 2 s).
- Ouverture de l'aperçu d'impression : 111 à 136 ms.
- Page scannée : 0,19 s (scan) ; OCR + analyse de 2 pages : 0,71 s (objectif < 3 s par page).

## Taille
- index.html : 3 906 963 octets (+7,6 Ko) ; boutons dans le code : 369 → 355.

## Impossible ou reporté (et pourquoi)
- IndexedDB pour les grosses données et jauge de stockage : lot 2 (avec la fusion du catalogue).
- Fusion PACKS → PACKS_V40 : lot 2 (touche aux fiches, demande ses propres tests de non-régression médicale).
- « Patient suivant » reste sur l'écran « Patient validé » (avec Annuler 8 s et Rouvrir) : un 3e bouton de validation dans la barre aurait doublé la fonction.

## Tests
- Nouveau : `tests/test_fil6.py` — parcours complet au toucher, 375 px jour, nuit, grand texte, Express, ordinateur, ordre automatique et manuel : 200/200.
- Toutes les suites existantes relancées : OK (anciens tests adaptés aux nouveaux emplacements des boutons : lot1, lot2, ciover, pdf16, packs, parcours20, favoris, express, voiture). Aucune modification des packs, doses, lignes jamais imprimées, journal ni compte rendu.
