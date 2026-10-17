# Express visite — audit avant codage (17/10/2026)

Principe : « Un choix → tout s'enchaîne ». Un bouton ou un champ n'apparaît que s'il découle du choix précédent.
Mesure : 3 visites fictives en tournée, iPhone 375 px, parcours actuel (v41g) joué par `tests/audit_express.py`.
Captures : `tests/captures/express-avant-*.png`. Rien n'est encore codé.

## 1. Mesure avant / cible

| Visite fictive | Gestes aujourd'hui | Cible proposée |
|---|---|---|
| Rhinopharyngite, adulte de 41 ans | 10 (9 touchers + 1 dictée) | 4 : patient, confirmer, dicter, « Imprimer et valider » |
| Fièvre, enfant de 4 ans (poids) | 10 (8 touchers, 1 saisie, 1 dictée) | 5 : les mêmes + le poids |
| Chute, femme de 88 ans, avec courrier | 9 (8 touchers + 1 dictée) | 4 (courrier prêt d'office) |

Sans compter la fenêtre d'impression de l'iPhone (AirPrint), identique avant et après.

Parcours actuel (visite 1) : Commencer → Naviguer → Je suis arrivé → Dictée → micro → toucher la fiche dans la liste → Imprimer → Envoyer à l'imprimante → Valider le patient → Patient suivant.

| Écran (375 px) | Éléments touchables | Hauteur |
|---|---|---|
| Visite sur place | 32 à 107 | 3,3 écrans |
| Fiche choisie | 81 à 178 | 6 à 10 écrans |
| Aperçu | 5 ou 6 | 1,6 à 4,2 écrans |

## 2. Constats, écran par écran

**Accueil / tournée**
- Bandeaux sans lien avec la visite en haut de l'écran : « SPÉCIMEN · Activer », « Sauvegarder · plus tard », « Déclarer une garde ».
- Onglets « Visite / Consultation » affichés alors que la tournée dit déjà « visite ».
- « Tournée et carte » en double avec la carte de visite.
- Toucher un patient ne lance pas la navigation : il faut « Commencer », puis « Naviguer ».

**En route / sur place**
- Il y a 4 boutons d'appel pour 2 personnes : 📞 en haut, « Appeler », et « Appeler le suivant » deux fois.
- La frise « Tournée · En route · Sur place · Fin » et la ligne « Étape 3 sur 4 » disent la même chose.
- L'encart « Fin de tournée prévue » reste affiché pendant la visite.
- « Je suis arrivé » est un geste en plus, alors que Packs connaît déjà la position.

**Choix de la fiche**
- Le motif remplit la recherche, mais rien n'est proposé : il faut toucher la fiche dans une liste de 25 à 30 résultats.
- **La liste ne tient pas compte de l'âge.** Pour l'enfant de 4 ans, « Pneumopathie aiguë — adulte » arrive en tête et « Fièvre — enfant » en 2e. Pour la chute à 88 ans, « Traumatisme… » suit la bonne fiche.
- Une fois la fiche choisie, les 25 autres restent affichées entre l'identité et la dictée, soit environ 2,5 écrans.

**Consultation (fiche choisie)**
- Le champ « Poids » est toujours visible, même à 41 et 88 ans.
- Grossesse, allergies et traitements sont repliés ensemble, quel que soit le patient.
- Toutes les feuilles sont dépliées ligne à ligne : 6 à 10 écrans, sans résumé « documents prêts ».
- Il y a 3 boutons d'impression : « Imprimer » en haut, « Imprimer · 6 » en bas, « Fin de consultation ».
- La cotation et la durée d'arrêt sont calculées, mais il faut descendre pour les voir.

**Aperçu, puis validation**
- « Imprimer » ouvre un aperçu, puis il faut « Envoyer à l'imprimante », puis « Valider le patient ».
- Un récapitulatif s'ouvre ensuite (« Copier maintenant », « Annuler », « Patient suivant », « Rouvrir »), soit un geste de plus.
- Le patient suivant s'ouvre, mais la navigation n'est pas lancée.

## 3. Proposition, écran par écran

1. **Accueil = liste des patients de la régulation**, avec « 📷 Ajouter des fiches » et « + Patient » en tête.
   - Chaque ligne montre l'initiale, l'âge, le motif et le secteur.
   - **Toucher une ligne ouvre le patient et lance Waze dans le même geste.** Sur iPhone, la navigation doit partir d'un toucher : c'est ce toucher-là.
   - Profil, sauvegarde et garde vont dans ⋯ (une pastille si le profil n'est pas activé).
2. **Patient ouvert** : identité, âge, motif, et la **fiche proposée** (motif + âge + sexe), prête à confirmer.
   - Appeler apparaît seulement si un numéro existe, Naviguer seulement si une adresse existe.
   - L'arrivée est enregistrée seule : par la position, sinon à la confirmation de la fiche. « Je suis arrivé » passe dans « Plus ».
3. **Confirmer la fiche** (un toucher). « Autre fiche » ouvre la liste, filtrée par âge.
   - Pack simple ou à risque selon l'âge et le terrain, doses calculées.
   - Champs montrés seulement s'ils s'appliquent :
     - poids : enfant seulement, avec le clavier numérique ouvert d'office ;
     - grossesse : femme de 15 à 49 ans ;
     - arrêt de travail : adulte ;
     - certificat enfant malade : enfant ;
     - courrier : fiche avec orientation.
   - Documents résumés en une ligne (« 6 documents prêts · Voir »), cotation calculée en une ligne.
4. **Dicter, puis « Imprimer et valider »** (un seul bouton). Il enchaîne :
   - l'impression et le PDF ;
   - le journal ;
   - le compte rendu, copié dans le même geste ;
   - la mise à jour de la tournée ;
   - l'ouverture du patient suivant.
   - L'aperçu reste disponible par « Voir les documents ». Un toast « Annuler » de 10 s remplace le récapitulatif.
5. **Au cabinet** : même enchaînement, sans les étapes de navigation.
6. **Ordinateur** : même logique, les écrans larges gardent le panneau des documents ouvert.

Rien n'est supprimé : tout ce qui est masqué reste derrière « Plus ».

## 4. Décisions à prendre avant de coder

1. Arrivée enregistrée seule (position, sinon confirmation de la fiche), au lieu du bouton « Je suis arrivé » ?
2. Récapitulatif de validation remplacé par un toast « Annuler » de 10 s ?
3. « Imprimer et valider » direct, avec l'aperçu derrière « Voir les documents » ?
4. Bandeaux profil, sauvegarde et garde déplacés dans ⋯ ?

## 5. Après codage (17/10/2026, branche `ia`, non publié)

Décisions retenues : 1 oui (« Je suis arrivé » reste dans Plus) ; 2 oui (liste « Patients validés » gardée 12 h) ; 3 oui sous la condition a ; 4 oui. Ajouts a à g faits.

| Visite fictive | Avant | Après |
|---|---|---|
| Rhinopharyngite, adulte | 10 | **4** : patient (Waze lancé), confirmer, dicter, « Imprimer et valider » |
| Fièvre, enfant de 4 ans | 10 | **5** : Naviguer, confirmer, poids, dicter, « Imprimer et valider » |
| Chute, 88 ans, courrier | 9 | **4** |

Mêmes chiffres à 375 px (jour, nuit, grand texte) et sur ordinateur. Test : `tests/test_express.py` (243 tests). Captures : `tests/captures/express-apres-*.png`.

- a. Résumé d'une ligne par médicament au-dessus du bouton. Une dose au poids sans poids est marquée « poids manquant ». Une alerte, une règle de forme, une dose incomplète ou un document trop long → le bouton ouvre l'aperçu, sans imprimer directement.
- b. Signes de gravité de la fiche sur une ligne (toucher pour la lire en entier), jamais bloquants.
- c. Fiche proposée et listes filtrées par âge (enfant < 15 ans, adulte, sujet âgé ≥ 65 ans) ; les autres âges sont rangés à part. À 4 ans, « fièvre » donne « Fièvre — enfant » en tête.
- d. Arrêt de travail : interrupteur « Arrêt de travail fait » et nombre de jours facultatif. Il est noté au compte rendu et au journal. Supprimés : le bloc amelipro, les durées suggérées et l'ouverture automatique (accident du travail, burn-out).
- e. Poids affiché chez l'adulte quand la fiche contient une dose au poids ou un anticoagulant.
- f. La navigation part du toucher seulement en mode Visite.
- g. Le compte rendu est copié dans le geste « Imprimer et valider ». Toast : « CR copié · prêt à coller dans MCC ». En secours : « Recopier le CR » dans « Patients validés ».

Sur iPhone, les documents sont préparés pendant la dictée : au toucher, le PDF part tout de suite (Safari exige un partage dans le geste). S'ils ne sont pas encore prêts, l'aperçu s'ouvre.

L'Express se coupe dans ⋯ → « Express visite ». L'écran complet reste entier dans « Plus ».

**Défaut trouvé en passant (en service sur main)** : le PDF iPhone mesurait mal la page et sortait toujours en 8,5 pt, même pour une ordonnance de 3 lignes. Corrigé ici : taille normale, réduite seulement si besoin, jamais sous 9 pt ; au-delà, c'est signalé.

## 6. Favoris → Express (point h, 17/10/2026)

- **Étoile** : chaque élément du mode complet porte une ☆. Un toucher l'ajoute à l'Express (★), un autre l'en retire. Éléments concernés :
  - champs : nom, naissance, poids, date, allergies, traitements, options ;
  - documents : chaque feuille et les courriers ;
  - sections : observation, actions faites, cotation, photos, note d'honoraires, arrêt, localisation ;
  - boutons : Fin de consultation, Imprimer.
- **Affichage conditionnel conservé** : un favori n'apparaît que si le mode complet l'affiche à ce moment. Exemples : « Kinésithérapie » seulement si la fiche a cette feuille ; « Grossesse » seulement chez une femme de 15 à 49 ans ; rien sur l'accueil sans patient.
- **Sécurité fixée**, sans étoile, impossible à retirer : ligne de gravité, résumé des doses, alertes (affichées dans l'Express), poids si enfant ou dose au poids.
- **Retirables** : les éléments de départ de l'Express (Naviguer, Appeler, Grossesse, Certificat enfant malade, Arrêt de travail fait, Voir les documents, Cotation, Dictée) portent aussi ★.
- **Par profil, chiffrés** : rangés sur l'appareil, chiffrés, sous le profil activé (ou « spécimen »). Ils partent aussi dans profil.json, chiffrés par la phrase maître, à la prochaine « Publier le profil » : retrouvés sur un autre appareil.
- **⋯ → « Revenir à l'Express par défaut »** rétablit le jeu de départ de l'audit.
- **Test** : `tests/test_favoris.py`, 70 tests à 375 px (jour, nuit, grand texte) et sur ordinateur.
  - Ajout puis retrait d'« Allergies ».
  - Absent de l'accueil, document favori présent ou absent selon la fiche.
  - Persistance après rechargement.
  - Stockage chiffré, profil.json.
