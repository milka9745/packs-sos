# Corrections v41z — fiches et courriers (03/11/2026 21:17)

37/37 tests.

- desktop — documents de la fiche onychomycose (courrier compris) : 13 ms
- 375 nuit — documents de la fiche onychomycose (courrier compris) : 22 ms

- OK source : FILLER_RE défini, DOC_FALLBACK (« sont à votre disposition sur simple demande ») retiré
- OK source : « sur simple demande » n'apparaît plus que dans la règle et la consigne IA
- OK source : consigne IA — une information absente ne donne aucune phrase
- OK source : courrier IA — paragraphe de remplissage écarté
- OK source : étiquette de fiche (FICHE_LBL) et « Motif à saisir »
- OK fiche A : « N° INTERVENTION 26110300123 » ignoré, motif = « DL CHEVILLE »
- OK fiche B : « O INTERVENTION » (lecture OCR) ignoré, motif = « ERUPTION »
- OK fiche C : étiquette seule, aucun motif lisible → champ vide, « motif à saisir » dans les vérifications
- OK fiche D : étiquette avant le nom → nom et motif justes
- OK fiches : nom, adresse et téléphone toujours lus
- OK écran : patient sans motif → « Motif à saisir » dans la régulation et dans la liste Express
- OK desktop : catalogue : aucun gabarit de courrier, de consignes ou de certificat ne contient de formule de remplissage
- OK desktop : règle : les formules creuses sont reconnues
- OK desktop : règle : une phrase clinique ou de politesse n'est pas prise pour une formule creuse
- OK desktop : 1241 lignes de courrier du catalogue sans observation (157 renvoyaient au compte rendu) : aucune formule creuse, aucun renvoi, motif conservé, parenthèses fermées
- OK desktop : onychomycose sans observation : le courrier garde le motif, sans « ongles » inventés ni formule creuse ni renvoi au compte rendu
- OK desktop : écran avant impression : « courrier : ajoute le nombre d'ongles atteints, l'extension, l'atteinte matricielle »
- OK desktop : l'alerte est « à documenter » (jamais bloquante) et visible aussi en Express
- OK desktop : onychomycose avec l'examen : « éléments recueillis ce jour : cutané : trois ongles atteints… » dans le courrier, après le motif
- OK desktop : ordre fixe : motif, éléments cliniques, puis traitement prescrit
- OK desktop : l'alerte disparaît une fois les éléments écrits
- OK desktop : courriers assemblés (spécialiste, médecin traitant) : aucune formule creuse
- OK desktop : découpe : motif gardé, éléments attendus extraits (parenthèse, énumération, « avec … détaillé »)
- OK desktop : aucune erreur JavaScript
- OK 375 nuit : catalogue : aucun gabarit de courrier, de consignes ou de certificat ne contient de formule de remplissage
- OK 375 nuit : règle : les formules creuses sont reconnues
- OK 375 nuit : règle : une phrase clinique ou de politesse n'est pas prise pour une formule creuse
- OK 375 nuit : 1241 lignes de courrier du catalogue sans observation (157 renvoyaient au compte rendu) : aucune formule creuse, aucun renvoi, motif conservé, parenthèses fermées
- OK 375 nuit : onychomycose sans observation : le courrier garde le motif, sans « ongles » inventés ni formule creuse ni renvoi au compte rendu
- OK 375 nuit : écran avant impression : « courrier : ajoute le nombre d'ongles atteints, l'extension, l'atteinte matricielle »
- OK 375 nuit : l'alerte est « à documenter » (jamais bloquante) et visible aussi en Express
- OK 375 nuit : onychomycose avec l'examen : « éléments recueillis ce jour : cutané : trois ongles atteints… » dans le courrier, après le motif
- OK 375 nuit : ordre fixe : motif, éléments cliniques, puis traitement prescrit
- OK 375 nuit : l'alerte disparaît une fois les éléments écrits
- OK 375 nuit : courriers assemblés (spécialiste, médecin traitant) : aucune formule creuse
- OK 375 nuit : découpe : motif gardé, éléments attendus extraits (parenthèse, énumération, « avec … détaillé »)
- OK 375 nuit : aucune erreur JavaScript
