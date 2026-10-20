# Relais serveur pour l'API Claude — proposition technique (20/10/2026)

**Statut : proposition. Rien n'est développé, rien n'est déployé, l'application fonctionne comme aujourd'hui.**
Le relais ne sera envisagé qu'après la stabilisation des fonctions médicales, et avant tout partage avec des collègues.

## 1. Architecture actuelle (constatée dans le code, v41v)

| Élément | Aujourd'hui |
|---|---|
| Application | Un fichier `index.html` servi par GitHub Pages, service worker pour le hors ligne. Aucun serveur applicatif. |
| Appel à l'IA | `fetch("https://api.anthropic.com/v1/messages")` depuis le navigateur, en-têtes `x-api-key`, `anthropic-version: 2023-06-01`, `anthropic-dangerous-direct-browser-access: true` (fonction `aiCall`). |
| Contenu envoyé | Consignes fixes (prompt système : règles, appareils, liste des ~400 noms de fiches du Pack) mises en cache côté API (`cache_control: ephemeral`) + texte de la consultation **pseudonymisé sur l'appareil** (`anonymize`, jetons `[[…]]`, contrôle `anonLeaks`, réidentification au retour `reidentify`). Jamais d'image. |
| Modèles | `claude-sonnet-5-5` pour rédiger, `claude-haiku-5-5` pour le test de clé ; `max_tokens` 1 500 à 2 600 ; `output_config.effort: low`. |
| Clé API | Chiffrée sur l'appareil (AES, code personnel) ; copie chiffrée par la phrase maître dans `profil.json` publié, pour les autres appareils. Jamais en clair, jamais dans la sauvegarde. |
| Coûts | Comptés sur l'appareil à partir de `usage` de chaque réponse (grille `AI_PRICE`), plafond mensuel et alerte (`AI.cfg.cap`, `AI.cfg.alert`). |
| Hors ligne | Demandes mises en attente chiffrées sur l'appareil (`AIQ`), reproposées au retour du réseau. |
| Décision du médecin | Écran « Ce qui part » (forcé si fragment d'identité, hors ligne ou plafond), synthèse à valider, aucune impression ni validation automatique. |

Limites de ce montage : la clé Anthropic est présente dans chaque navigateur qui l'utilise (donc exposable par toute personne ayant le code de l'appareil ou la phrase maître), elle est unique pour tous les appareils, aucun journal central des appels, aucune révocation fine, aucun plafond par médecin ; l'application appelle directement un fournisseur hors Union européenne depuis le poste du médecin.

## 2. Objectif du relais

Un petit service HTTPS, entre l'application et l'API Anthropic, qui :
1. garde seul la clé Anthropic (secret serveur) ;
2. authentifie chaque appel (jeton par médecin) ;
3. applique des règles : modèles autorisés, `max_tokens` maximal, taille maximale de la requête, quota et plafond de coût par médecin, limitation de débit ;
4. journalise des **métadonnées seulement** (qui, quand, jetons consommés, coût, modèle, code de réponse), jamais le contenu ;
5. transmet la réponse telle quelle.

La pseudonymisation reste sur l'appareil : le relais ne voit que ce que l'API voit aujourd'hui. L'écran « Ce qui part », la synthèse, les garde-fous (nombres, posologies, jetons) et la file hors ligne ne changent pas.

## 3. Modifications nécessaires dans l'application (quand ce sera décidé ; petites)

1. `aiCall` : URL de base configurable (`AI.cfg.relay`), en-tête `Authorization: Bearer <jeton>` à la place de `x-api-key` ; retrait de l'en-tête `anthropic-dangerous-direct-browser-access`. Le corps JSON (modèle, système avec cache, messages) est inchangé.
2. Réglages (Journal → Assistant IA) : « Mode direct (clé personnelle) » / « Mode relais (jeton) » ; le jeton est rangé exactement comme la clé aujourd'hui (chiffré sur l'appareil, et dans `profil.json` par la phrase maître pour les autres appareils). Bouton « Tester » → point `/sante` du relais.
3. Comptage des coûts : le compteur local reste (il lit `usage` de la réponse) ; le relais tient le compte de référence par médecin et renvoie dans un en-tête le reste du quota (`X-Quota-Restant`) pour l'afficher.
4. Service worker : rien (les origines externes ne sont déjà jamais mises en cache).
5. Tests : les suites `test_ia`, `test_auto19`, `test_prepub`, `test_ui41` simulent déjà l'API ; il suffira de simuler l'URL du relais.

Taille estimée : quelques dizaines de lignes, avec un interrupteur qui conserve le mode direct comme solution de repli (retour arrière immédiat).

## 4. Le relais lui-même

### Esquisse (non déployée)
```
POST /v1/ia                     Authorization: Bearer <jeton médecin>
  → vérifie le jeton (révocable), l'origine (CORS : https://milka9745.github.io seulement),
    la taille (< 200 Ko), le modèle (liste blanche), max_tokens (≤ 3000), le quota du mois
  → transmet à https://api.anthropic.com/v1/messages avec la clé serveur
  → journalise : horodatage, id médecin, modèle, jetons entrée/sortie/cache, coût, statut
  → renvoie la réponse JSON telle quelle (+ en-tête de quota)
GET  /sante                     → "OK" (test de connexion depuis l'application)
```
Pas de stockage du corps des requêtes ni des réponses, pas de cache, journaux sans contenu, secret dans le coffre de la plateforme, jetons longs et aléatoires (ou signés avec expiration), rotation possible sans toucher aux appareils (le relais seul connaît la clé Anthropic).

### Où l'héberger (à décider avec le DPO)
| Option | Pour | Contre | Ordre de grandeur de coût (2026, à vérifier) |
|---|---|---|---|
| Fonction « edge » (Cloudflare Workers, Vercel, Netlify) | Mise en place en quelques heures, latence minimale, pas de serveur à entretenir, HTTPS inclus | Hébergeur hors certification HDS ; localisation du traitement à vérifier (règles de région) | 0 à 5 € / mois |
| Petit serveur en France (OVHcloud, Scaleway, Clever Cloud) | Localisation en France, contrat de sous-traitance simple | Serveur à entretenir (mises à jour, certificats) | 5 à 15 € / mois |
| Hébergeur certifié HDS (OVHcloud HDS, Scaleway HDS, Outscale…) | Conforme à l'hébergement de données de santé si le relais venait à en conserver | Contrat, engagement, coût élevé pour un seul service | 100 à 300 € / mois et plus |

Lecture : tant que le relais **ne conserve rien** (transit seulement) et ne voit que du texte pseudonymisé, l'option France non HDS est défendable ; c'est au DPO de trancher, car un texte pseudonymisé reste une donnée personnelle (le médecin peut réidentifier sur son appareil).

### Côté Anthropic (à vérifier avant tout partage)
Accord de traitement des données (DPA), option de non-conservation des échanges (« zero data retention »), localisation du traitement, et mention de ce sous-traitant dans le registre des traitements. Sans ces garanties, l'usage doit rester personnel, comme aujourd'hui.

## 5. Conséquences

**Performances** : un saut réseau de plus, en pratique 30 à 150 ms (fonction edge) contre 3 à 8 s de génération par le modèle : imperceptible. Le cache des consignes fixes fonctionne à travers le relais (même texte système, même clé). Pas de flux en continu (streaming) aujourd'hui : rien à adapter.

**Coûts** : le coût API ne change pas (mêmes jetons ; aujourd'hui environ 1 à 2 centimes d'euro par synthèse d'après la grille de l'application : Sonnet 2 $ / 10 $ par million de jetons, lecture du cache 0,20 $). S'ajoute l'hébergement du relais (tableau ci-dessus). Avec plusieurs médecins, une seule clé Anthropic et un plafond par médecin.

**Disponibilité** : si le relais tombe, l'IA est indisponible mais l'application continue (fiche par le motif, observation locale, dictée gardée, file d'attente) : c'est déjà le comportement hors ligne. Le mode direct peut rester en secours pour le médecin administrateur.

**Sécurité** : la clé Anthropic quitte les navigateurs ; un jeton volé ne donne accès qu'au relais, limité, révocable ; CORS verrouillé sur l'origine de l'application ; journal des appels par médecin ; coupure immédiate possible (interrupteur serveur).

## 6. Préparation du multi-médecins (sans le développer maintenant)

Le relais est le bon endroit pour : un jeton par médecin, un quota et un plafond de coût par médecin, le journal des appels, la liste des modèles autorisés, la rotation de la clé. Plus tard, le jeton statique pourra être remplacé par une identification professionnelle (Pro Santé Connect ou un fournisseur OpenID) donnant une session courte ; l'application n'a alors que la session à ranger, jamais la clé. Les identités, cachets, favoris et réglages sont déjà par profil dans l'application ; le Pack est une donnée commune.

## 7. Étapes proposées, quand ce sera le moment

| Étape | Contenu | Retour arrière |
|---|---|---|
| 0 (maintenant) | Rien. Usage personnel en mode direct. | — |
| 1 | Décision du DPO (hébergeur, DPA Anthropic), choix de l'hébergeur. | — |
| 2 | Déploiement du relais seul, test avec `/sante`, jeton du Dr DEIE. | Supprimer le service. |
| 3 | Interrupteur « Mode relais » dans l'application (branche `ia`, /test/ seulement), tests simulés, essai réel sur /test/. | Repasser en mode direct d'un réglage. |
| 4 | Bascule de l'outil de garde (main) après essai, clé Anthropic retirée des appareils. | Mode direct en secours. |
| 5 | Jetons pour les collègues, quotas, journal ; puis identification professionnelle. | Révocation des jetons. |

## 8. Ce que ce document ne fait pas
Il ne modifie pas l'application, ne crée aucun serveur, ne change pas le fonctionnement actuel de l'API, ne développe pas le multi-utilisateurs, et laisse Apple Watch et dispositifs connectés à la feuille de route (`docs/FEUILLE-DE-ROUTE.md`).
