# Feuille de route — évolutions futures (20/10/2026)

Aucune de ces évolutions n'est développée. Rien n'a été ajouté à l'application pour les préparer (ni module, ni dépendance). Cette page note seulement les limites actuelles et ce qu'il faudrait adapter.

## 1. Plusieurs médecins (P1 — à anticiper, pas à développer)
État actuel : application statique (GitHub Pages), un profil par appareil (`profil.json` chiffré par une phrase maître : identité, cachet, clé API), données chiffrées sur l'appareil (journal, brouillon, patients validés, tournée), synchronisation facultative.
Limites : pas de compte, pas d'authentification serveur, pas de séparation des données entre médecins sur un même appareil, Pack commun non personnalisable par médecin, coûts API par clé.
Adaptations nécessaires plus tard : un service d'authentification (un compte par médecin), un espace de données par médecin (ou chiffrement par médecin), paramètres individuels (identité, signature, préférences de prescription, favoris Express déjà séparés par profil), Pack commun + surcouche personnelle, relais API côté serveur avec compteur de coûts par médecin, journal des accès et des validations, exigences réglementaires d'un service multi-utilisateurs (hébergement HDS, DPO, registre des traitements).
Décision de conception déjà compatible : identité et réglages sont lus par des fonctions (`IDENT`, `favProf()`, `AI.cfg`), le Pack est une donnée (`PACKS`), les documents sont produits à partir de l'état d'une consultation.

## 2. Clé API côté serveur (sécurité — à faire avant tout partage)
État actuel : clé Anthropic dans le navigateur (chiffrée), appel direct à l'API (`anthropic-dangerous-direct-browser-access`), texte pseudonymisé sur l'appareil (DPO 15/10/2026). Adapté à un usage personnel ; la pseudonymisation seule ne vaut pas conformité HDS.
À faire plus tard : un relais (ex. fonction serveur) qui garde la clé, authentifie le médecin, journalise et plafonne ; l'application n'enverrait plus qu'un jeton de session. Hébergement à choisir avec le DPO.

## 3. Apple Watch (P2 — futur uniquement)
Idées : dictée au poignet, « Je suis arrivé », patient suivant, synthèse courte, notifications. Prérequis : application iOS compagnon (watchOS) et un canal de synchronisation sécurisé ; impossible depuis une application web seule. Rien n'est prévu dans le code.

## 4. Dispositifs médicaux connectés (P2 — futur uniquement)
Idées : tensiomètre, saturomètre, ECG, thermomètre, glycémie, débit de pointe → mesures horodatées, unités, tracé ECG original, identification fiable du patient, puis intégration à l'observation et à la synthèse IA. Prérequis : Web Bluetooth (non disponible sur iPhone Safari) ou application compagnon ; API constructeur. Rien n'est prévu dans le code.

## 5. Commercialisation (P2)
Prérequis : hébergement HDS, comptes, contrat et conformité RGPD multi-structures, support, mise à jour contrôlée des fiches (Pack) avec relecture médicale. Hors périmètre actuel.
