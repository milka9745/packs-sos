# Lot 2 — un seul catalogue, stockage sans perte (03/11/2026, branche ia, publié sur /test/)

## Fait
### Catalogue
- **Ancienne génération retirée du fichier** : 90 anciennes fiches remplacées par leur version v40 ne gardent que leur nom, pour garder leur place. Les numéros de fiche enregistrés dans un brouillon ou un patient validé restent donc justes. Gain : 128,6 Ko.
- **Une seule fusion** : `catAdd()` remplace les 16 boucles de fusion et les 12 boucles de champs.
- **Aucun changement médical** : le catalogue chargé est identique à l'octet près avant et après (399 fiches, même contenu, même ordre).
- **Fiches jumelles** : 12 anciennes fiches couvrent le même motif qu'une fiche v40. Dans la recherche, chacune apparaît sous sa fiche v40, en « Autre version », au lieu d'une deuxième ligne. Une recherche précise (« insomnie chronique ») l'affiche normalement. En Express, elle passe après sa fiche v40. **Rien n'est supprimé.**
- Les « 518 entrées » de l'audit comptaient les anciennes versions déjà remplacées au chargement : seules 399 fiches étaient réellement en service.

### Stockage
- **IndexedDB chiffré** (AES-256-GCM, base « packs-sos-data ») pour : journal, patient en cours, tournée, identité, synchronisation, patients validés, dictées récentes, archive.
- **Bases médicaments (BDPM, ANSM)** en IndexedDB, plus en localStorage. Elles sont migrées au premier lancement.
- **Copie de secours** chiffrée en localStorage pour le journal, la tournée, le brouillon, l'identité et la synchronisation. Les versions de repli /v38/ à /v40/ continuent ainsi de les lire.
- **Règle de lecture** : chaque écriture porte son heure et la plus récente gagne. Une donnée écrite par une version précédente est reprise, puis migrée.
- **Zéro perte** :
  - si IndexedDB est en panne, l'écriture passe en localStorage ;
  - si tout est plein, un message « Non enregistré » s'affiche, avec un bandeau rouge « Voir » sur l'écran principal (jamais silencieux, alors qu'avant l'erreur était avalée) ;
  - écran masqué, application fermée ou verrouillage : tout ce qui attend est écrit tout de suite, avec la clé du moment (avant, une saisie faite juste avant le verrouillage pouvait se perdre).
- **Jauge** (Réglages, au-dessus de « Sauvegarde ») :
  - barre et espace utilisé sur l'espace disponible ;
  - détail par catégorie (journal, patient en cours, validés, archive, photos, pages scannées, bases médicaments) ;
  - occupation de localStorage sur 5 Mo ;
  - protection contre l'effacement automatique.
- **Bandeau d'alerte** au-delà de 80 % (orange) ou de 90 % (rouge), ou après un échec. Mesure à l'ouverture et après les écritures, au plus une fois toutes les 2 minutes : aucun minuteur.
- **Archive** : un patient validé depuis plus de 12 h quitte « Rouvrir » et entre dans l'archive chiffrée, sans photo ni image de page. Elle est gardée 30 jours et incluse dans la sauvegarde chiffrée. Tant que l'archivage n'a pas réussi, le patient reste dans l'historique.
- **Version /test/** : base séparée « packs-sos-test-data », sans partage avec l'outil de garde.

## Temps mesurés
- Écriture chiffrée d'un journal de 1 000 patients : 12 ms ; relecture complète : 38 ms.
- Changements d'état du parcours (suite fil6) : inchangés, sous 2 s.

## Boutons
- Inchangés, sauf « Autre version » sous une fiche jumelle et « Voir » dans le bandeau d'alerte (affichés seulement dans ces cas).
- Boutons dans le code : 355 → 356.

## Taille
- index.html : 3 906 963 → 3 810 525 octets (−96 Ko).

## Impossible ou reporté (et pourquoi)
- **Suppression des 12 fiches jumelles** : non faite, car leur contenu diffère de la fiche v40 (biologie, consignes, variantes enfant ou adolescente). C'est une décision médicale (question au rapport).
- **Consultation de l'archive depuis l'écran** : lot 3 (documents et résumé dans le fil). L'archive est restaurée avec la sauvegarde.
- **Mode sans chiffrement** (navigateur sans WebCrypto) : reste en localStorage, comme avant.

## Tests
- Nouveau : `tests/test_stock.py`, 28/28 : catalogue, jumelles, IndexedDB, copie de secours, migration, la plus récente gagne, panne, stockage plein, verrouillage, bases médicaments, archive, jauge à 375 px (jour, nuit, grand texte) et sur ordinateur.
- Toutes les suites existantes passent (38 suites). Le test du dossier test/ est lancé à la publication.
