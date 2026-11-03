# Corrections v41z — fiches de régulation et courriers (03/11/2026, branche ia, publié sur /test/)

## 1. Lecture des fiches MccMissionSG
- « N° INTERVENTION », lu « O INTERVENTION » ou « N INTERVENTION » par l'OCR, avec ou sans numéro, est une étiquette de la fiche : jamais un motif, jamais repris dans la note. Même règle pour « INFORMATIONS PATIENT », « DOCUMENTS », « ALLERGIES », « TRAITEMENTS », « ADRESSE PATIENT », « TÉL »…
- Le motif n'est rempli qu'avec le vrai libellé de régulation (« DL CHEVILLE », « ERUPTION »).
- Sans motif lisible, le champ reste vide : l'écran affiche « Motif à saisir » (bloc « Régulation et interrogatoire », liste Express) et la vérification de la fiche le signale (« motif à saisir »).
- Correction associée : une ligne qui suit un numéro d'intervention n'est plus prise pour une commune (seul un code postal isolé compte).
- Test : fiche fictive avec l'étiquette avant le nom, après l'adresse, avec numéro, sans motif (`tests/test_courriers.py`).

## 2. Courriers : aucune phrase de remplissage
- Règle unique `FILLER_RE` : « à votre disposition sur simple demande », « sur simple demande », « non précisé », « non renseigné », « non documenté », « non communiqué », « à compléter », « à préciser », « à renseigner », « à déterminer », « sans précision », « données non disponibles », crochets vides, XXX, ???.
- **Une information absente ne donne aucune phrase.** L'énumération des gabarits « … dont A, B et C figurent dans le compte rendu joint » :
  - devient « éléments recueillis ce jour : constantes, examen, ECG, lésions constatées, diagnostic » quand l'observation les contient ;
  - disparaît sinon, en gardant la phrase du motif (« Je vous adresse X, examiné ce jour pour une onychomycose. ») ;
  - l'ancien repli « sont à votre disposition sur simple demande » est supprimé.
- Ordre fixe : motif, éléments cliniques dictés, traitement prescrit (« J'ai prescrit … », réécrit avec ce qui est réellement coché), question posée au confrère.
- **Signal à l'écran avant d'imprimer** : les éléments que le courrier attend et qui manquent à l'observation sont listés dans « Avant d'imprimer, il manque : courrier : ajoute le nombre d'ongles atteints, l'extension, l'atteinte matricielle » (écran complet) et dans les alertes de l'Express (« ✉ Courrier : ajoute … »). C'est « à documenter », jamais bloquant. L'alerte disparaît dès que l'élément est écrit dans l'examen ou le diagnostic.
- Courriers assemblés (spécialiste, médecin traitant) : déjà construits à partir des seules données saisies ; vérifiés sans formule.
- Courrier IA : un paragraphe contenant une formule de remplissage est écarté (« Paragraphe écarté : phrase de remplissage pour une donnée absente ») ; la consigne envoyée à l'IA interdit ces formules et toute phrase pour une donnée absente.
- « Vous trouverez ci-joint l'ordonnance… » devient « Je joins l'ordonnance… », et la phrase disparaît si rien n'est prescrit.

## 3. Barre du bas en Consultation : plus jamais muette
- État initial : partiel. En Consultation sans patient ouvert, « Scanner » lançait bien la prise de photo, mais « Dicter » et « Choisir la fiche » ne faisaient rien dans l'Express (champs repliés dans « Plus »), et aucun bouton n'ouvrait de dossier.
- Correction : sans patient ouvert, tout bouton de la barre crée d'abord un nouveau patient (dossier vierge, identité et motif affichés), puis fait son action : « Choisir la fiche » ouvre le champ du motif avec le clavier, « Dicter » le champ de dictée avec le clavier, « Scanner » la prise de photo. Le champ visé est déplié s'il était dans « Plus ». Une ligne le dit (« Nouveau patient : … »). Patient déjà ouvert : rien n'est recréé.
- Texte d'aide conforme à la barre : en Consultation il nomme « Choisir la fiche », « Dicter », « Scanner » ; en Visite « Ajouter des fiches ».
- Règle de test : chaque bouton visible de la barre, état par état (Consultation sans patient ; Visite Demande, En route, Sur place, Prise en charge, Sortie), a un effet mesurable (champ ouvert, fichier demandé, vue, état) ; un lien a une destination ; un bouton grisé doit porter sa raison. Aucun bouton grisé n'a été nécessaire.

## 4. Visite et Consultation impossibles à confondre
- État initial : partiel. Une couleur de mode existait (boutons principaux, liseré du bandeau), mais atténuée en affichage Garde, absente de la barre du bas et de l'étiquette d'étape, sélecteur sous l'Express (replié dans « Plus »), onglet actif non plein, aucune confirmation ni pastille.
- Correction : Visite = vert émeraude, Consultation = bleu, jour et nuit, grand texte compris, sur la barre du bas (liseré 5 px), l'étiquette d'étape (pastille pleine « Visite · En route · étape 2 sur 5 », « Consultation · étape 1 sur 3 », « Consultation · Prise en charge · étape 2 sur 3 »), le liseré gauche de la carte patient, de l'Express et de la carte de visite, le bandeau du haut et l'onglet actif.
- Sélecteur Visite / Consultation toujours en haut de l'écran (avant l'Express, jamais dans « Plus » ni dans un menu), deux gros onglets, l'actif plein et coloré.
- Changement de mode : ligne de confirmation (« Passage en Visite : pack à risque et cotation visite par défaut » / « Passage en Consultation : pack simple et cotation consultation par défaut ») ; pour un patient ouvert, chaque passage est noté avec l'heure dans sa ligne du journal (le mode était déjà enregistré).
- Pastille « V » verte ou « C » bleue devant l'initiale : en-tête (patient en cours), liste Express, écran Tournée (arrêts et consultations attendues), patients validés, journal.
- Contraste vérifié ≥ 4,5 (étiquette et onglet actif) en jour, nuit et grand texte.

## Tests (03/11/2026, points 3 et 4)
- Nouveau : `tests/test_modes.py`, 185/185 (Express jour, nuit, grand texte ; mode complet nuit ; 375 px) ; captures `tests/captures/modes-visite-375-*.png` et `modes-consult-375-*.png`.
- Toutes les suites : voir « Résultat des suites » ci-dessous.

## Gabarits repassés
- 1 241 lignes de courrier du catalogue (157 renvoyaient au compte rendu), 383 feuilles de consignes, les certificats et les formules fixes : aucune formule de remplissage ; après réécriture sans observation, aucune formule, aucun renvoi au compte rendu, motif conservé, parenthèses fermées.
- Aucune ligne médicale (doses, variantes, lignes jamais imprimées) modifiée.

## Tests
- Nouveau : `tests/test_courriers.py`, 37/37 (ordinateur et 375 px nuit) ; capture `tests/captures/corr-courrier-manque-375.png`.
- Temps : documents complets de la fiche onychomycose (courrier compris) en 13 à 14 ms.
- Toutes les suites existantes : voir le résultat en fin de rapport (section « Résultat des suites »).

## Non fait
- Les feuilles autres que courrier, consignes et certificat (ordonnances, soins, matériel) ne sont pas balayées par la règle : une seule ligne y contient « à préciser par le podologue » (bilan podologique, fiche validée), laissée telle quelle.
- Rien n'a été essayé sur un vrai iPhone.

## Résultat des suites (03/11/2026)
- 39 suites : toutes passent (`test_courriers` 37/37 ; `test_dossier_test` 25/25 lancé à la publication).
- Une régression trouvée et corrigée par `test_packs` : « TOUX » après « 45000 ORLEANS » était pris pour une commune (motif vide) ; une commune n'est attendue sur la ligne suivante que si la précédente finit par le code postal ou un tiret.
