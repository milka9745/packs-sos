# Lot 2 (03/11/2026) — un seul catalogue, stockage sans perte

- OK — catalogue : aucune fiche définie deux fois en entier dans le fichier (anciennes versions remplacées retirées)
- OK — catalogue : 90 anciennes fiches réduites à leur nom (leur place est gardée)
- OK — catalogue : une seule fusion (catAdd) au lieu de 16 boucles
- OK — catalogue : 400 fiches, toutes avec contenu, noms uniques
- OK — catalogue : les 12 fiches jumelles retrouvent leur fiche v40
- OK — recherche « insomnie » : une ligne « Insomnie », l'ancienne fiche en « Autre version » dessous (plus de doublon)
- OK — « Autre version » sélectionne l'ancienne fiche (rien n'est perdu)
- OK — recherche précise « insomnie chronique » : l'ancienne fiche en ligne normale
- OK — Express : la fiche v40 passe avant sa jumelle
- OK — journal : écrit chiffré dans IndexedDB, copie de secours identique en localStorage, aucun nom en clair
- OK — journal de 1 000 patients : écrit en moins de 1 s et relu en entier
- OK — patients validés : IndexedDB seulement (plus en localStorage)
- OK — migration : ancienne donnée de localStorage lue, copiée dans IndexedDB, puis retirée de localStorage
- OK — lecture : la copie la plus récente gagne ; une écriture de /v40/ (sans heure) est reprise
- OK — IndexedDB indisponible : la donnée part en localStorage et se relit (aucune perte)
- OK — stockage plein : l'appel échoue, message « Non enregistré », bandeau rouge sur l'écran principal
- OK — verrouillage immédiat après une saisie : rien n'est perdu
- OK — base médicaments : déplacée dans IndexedDB, relue au démarrage, incluse dans la sauvegarde
- OK — validé depuis plus de 12 h : quitte « Rouvrir », entre dans l'archive chiffrée (IndexedDB) sans photo ni image de page
- OK — archive incluse dans la sauvegarde chiffrée
- OK — iPhone jour : jauge de stockage dans Réglages : barre, total utilisé, détail par catégorie, sans débordement
- OK — iPhone jour : aucune erreur JavaScript
- OK — iPhone nuit : jauge de stockage dans Réglages : barre, total utilisé, détail par catégorie, sans débordement
- OK — iPhone nuit : aucune erreur JavaScript
- OK — iPhone grand texte : jauge de stockage dans Réglages : barre, total utilisé, détail par catégorie, sans débordement
- OK — iPhone grand texte : aucune erreur JavaScript
- OK — ordinateur : jauge de stockage dans Réglages : barre, total utilisé, détail par catégorie, sans débordement
- OK — ordinateur : aucune erreur JavaScript

28/28 tests OK

## Temps mesurés (ms)

- écriture chiffrée du journal : 1
- journal de 1 000 patients : écriture chiffrée : 13
- journal de 1 000 patients : lecture : 41
