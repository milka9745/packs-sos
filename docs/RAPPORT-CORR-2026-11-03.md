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
