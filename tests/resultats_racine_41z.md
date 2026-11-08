# Publication en racine (06/11/2026) : conservation des données de la v41k

- OK — 41z : version en service chargée (version.json)
- OK — 41k : pas d'Express (code de la racine actuelle)
- OK — 41k : trois patients au journal, trois demandes à la tournée (fictifs)
- OK — 41k : journal, tournée et identité écrits chiffrés (localStorage, clés _enc)
- OK — 41k : identité (fictive) chargée : nom, Adeli, association
- OK — racine : version.json de la nouvelle version (42)
- OK — racine : numéro de version lisible dans version.json (label « 41z · JJ/MM HH:MM »)
- OK — racine : 2 ou 3 lignes « Ce qui change »
- OK — racine : nouveau cache du service worker (packs-sos-v42, plus v41k)
- OK — nouvelle version : pas d'écran de création de code (l'utilisateur et son code sont reconnus)
- OK — nouvelle version : code de la branche ia (Express présent)
- OK — nouvelle version : « v41z · main · JJ/MM HH:MM » affiché
- OK — profil (identité) identique : nom, Adeli, association, cachet, profil actif
- OK — profil (stockage chiffré) identique, champ par champ
- OK — journal identique (3 entrées, mêmes champs, mêmes valeurs)
- OK — tournée identique (stockage) : 3 demandes, ordre, base, origine
- OK — tournée identique (en mémoire)
- OK — réglages conservés (thème nuit, grand texte)
- OK — stockage : aucune clé de la v41k supprimée
- OK — secours /v41k/ : s'ouvre avec le même code, sans création
- OK — secours /v41k/ : titre « Packs SOS v41k », code de la v41k (pas d'Express)
- OK — secours /v41k/ : profil.json et OCR lus à la racine du site (siteBase)
- OK — secours /v41k/ : cache propre (packs-sos-sub-v41k), ne supprime aucun autre cache
- OK — secours /v41k/ : manifeste propre (Packs SOS v41k)
- OK — secours /v41k/ : identité, tournée et les 3 patients d'avant la bascule retrouvés
- OK — aucune erreur JavaScript

26/26 tests OK
