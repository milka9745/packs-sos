# Cahier des charges — fiches Packs SOS

Version 3 du 14/10/2026 (version initiale du 13/10/2026), à compléter au fil du projet (sections « À compléter »).

## 1. Modèle de fiche

Chaque fiche suit toujours le même plan, dans cet ordre :

1. **Titre et appareil** — ex. « Pyélonéphrite aiguë simple — Uro-néphrologie ».
2. **Statut** — validée / à relire, date de validation, version.
3. **Signes de gravité et orientation** — ce qui fait appeler le 15, adresser aux urgences ou en consultation spécialisée.
4. **Critères diagnostiques** — courts, utilisables en visite.
5. **Profil et pack par défaut** — critères qui font passer du pack **simple** au pack **à risque** (voir § 1 bis).
6. **Ordonnance médicaments** — pour chaque pack (simple / à risque) : NOM COMMERCIAL en majuscules, dosage, forme, posologie, durée ; variantes enfant au poids (dose arrondie à une valeur pratique, dose maximale), grossesse, allaitement, allergie, insuffisance rénale, sujet âgé ; prudence de conduite quand pertinent.
7. **Biologie** — si utile, avec le délai, par pack.
8. **Imagerie** — si utile, avec l'indication rédigée.
9. **Paramédical** — kiné, IDE, orthophonie, etc., avec nombre de séances et objectif.
10. **Conseils patient** — en langage simple, une page.
11. **Consignes de reconsultation** — signes qui doivent faire reconsulter ou appeler le 15.
12. **Courrier type** — si un avis spécialisé est pertinent (voir § 4).
13. **Certificat / arrêt de travail** — certificat si pertinent ; arrêt de travail : **durée indicative seulement** (référentiel ameli par motif), affichée à l'écran ; l'arrêt lui-même est rédigé hors Packs.
14. **Cotation** — actes et majorations habituels.
15. **Liste de vérification** — ce que Packs contrôle dans la dictée avant validation, chaque point avec son niveau (voir § 1 ter).
16. **Éléments de compte rendu** — la trame que doit contenir le compte rendu pour ce motif, dans l'ordre.
17. **Traçabilité médico-légale** — les points propres au motif à toujours tracer (négatifs pertinents, information donnée, refus éventuel) ; voir § 7.
18. **Navigation** — **mots-clés** (mots du patient, motifs de régulation, synonymes), **fiches voisines** (bascule d'un geste si la fiche n'est pas la bonne), **durée habituelle de visite** (utilisée pour planifier la tournée).
19. **Sources** — société savante ou référentiel, année, lien ; divergences signalées.

### 1 bis. Deux packs par défaut : simple / à risque

- Chaque fiche prévoit, quand c'est pertinent, un pack **simple** et un pack **à risque de complication**.
- **C'est le risque du patient qui décide, pas le lieu.** Les critères de risque (âge, antécédents, terrain, grossesse, insuffisance rénale, immunodépression…) sont écrits dans la fiche.
- Le mode **Consultation** propose par défaut le pack simple, le mode **Visite** le pack à risque (patients plus souvent âgés ou polypathologiques). Le choix est modifiable d'un geste, et un critère de risque présent bascule toujours vers le pack à risque.
- La **gravité** n'est pas un troisième pack : c'est une sortie (15, urgences, avis), toujours en tête de fiche.
- **Enfant, grossesse, allaitement, allergie, insuffisance rénale** restent des variantes de chaque pack, pas un « mode risque ».
- Quand la distinction n'a pas de sens (gale, piqûre, tique…), la fiche n'a qu'un pack et la rubrique 5 porte « sans objet ».

### 1 ter. Niveaux de la liste de vérification

- **Bloquant** : signes de gravité et critères qui changent la prise en charge. Packs insiste avant validation.
- **À documenter** : allergie, récidive, traitement en cours… Rappel discret, une réponse d'un mot suffit.
- **Facultatif** : examen non systématique (ex. BU en consultation). Si fait, le résultat va au compte rendu ; sinon rien n'est signalé.
- La liste ne contrôle que ce qui est écrit dans la fiche validée : jamais de diagnostic ni de dose proposés hors fiche.

## 2. Catalogue par appareil

Cardio-vasculaire · Respiratoire · ORL · Ophtalmologie · Digestif · Uro-néphrologie · Gynécologie-obstétrique · Neurologie · Psychiatrie · Rhumatologie et traumatologie · Dermatologie · Infectiologie · Endocrinologie · Pédiatrie · Gériatrie · Intoxications · Soins palliatifs · Administratif (certificats, arrêts, décès) · **Renouvellement** (maladies chroniques, bizone ALD).

Catalogue détaillé : `SOMMAIRE-CATALOGUE.md` (264 fiches, dont les fiches **◇ premier recours** : suivis pris en charge en garde faute de médecin traitant, désert médical ; prescription de dépannage puis orientation, y compris premier bilan et suivi de grossesse).

**Trouver la bonne fiche** : proposition à partir du motif de régulation lu sur la capture, recherche par les mots du patient, Fréquents, fiches voisines ; l'IA n'intervient que si le résultat est ambigu.

Rangée **« Fréquents »** en tête : calculée sur l'appareil à partir du journal (90 derniers jours, poids plus fort aux usages récents, fiche épinglable) ; ordre de départ type SOS Médecins tant qu'il n'y a pas d'historique. Plus tard, en option : compteurs anonymes d'équipe (fiche et nombre, sans patient).

## 3. Mes conventions de prescription

**Packs figés** : quand je dis « pack + nom » (gastro, vertiges, cystite, dentaire, gale, asthme aigu, piqûres, tique…), le pack s'applique tel quel, puis seuls l'âge, le poids et les allergies l'adaptent.

**Conventions** : SPASFON LYOC 160 mg adulte / 80 mg enfant ; DOLIPRANE 1 g toutes les 6 h ; SERESTA 10 mg ; ACUPAN 30 mg comprimé ; VOGALÈNE 5 mg suppositoire sécable ; FORTRANS 1 sachet dans 1 L (fécalome) ; ADIARIL en soluté de réhydratation.

**Pratique selon le contexte** :
- **Cystite** : en consultation, femme jeune sans signe de gravité → diagnostic clinique et sémiologique, pas d'ECBU, BU seulement si doute diagnostique. En visite ou si risque de complication (sujet âgé, antécédents nombreux) → BU au domicile, ECBU, antibiotique probabiliste d'emblée, adaptation secondaire à l'antibiogramme. Écart avec les recommandations : BU non systématique en consultation chez la femme jeune typique.

**À compléter par moi** : ce que je prescris autrement que les recommandations et pourquoi ; mes choix d'antibiotiques de première intention ; mes durées habituelles d'arrêt de travail.

## 4. Documents et rédaction

- **Mise en page** : modèle papier SOS Médecins Orléans (logo à gauche ; à droite « Docteur Mickaël DEIE », n° Adeli, « En association avec : » et les associés ; corps dans un cadre avec « Date : » et « Patient : » ; pied : signature et cachet). Une page par document, jamais scindée ; les documents d'un patient regroupés à la suite dans un seul PDF.
- **Identité patient** : nom, prénom et date de naissance réels dans les documents ; jamais de jeton du type [NOM].
- **Aucun trou** : pas de « à préciser », « à compléter », « ? », crochet, champ vide ou équivalent dans un document imprimable ; si une donnée manque, la ligne est retirée et le manque est signalé seulement à l'écran avant impression. Le compte rendu ne mentionne jamais une ligne non prescrite faute de donnée.
- **Pas de page imprimée « pour le dossier »** : SOS Médecins Orléans n'a pas de dossier papier.
- **Plusieurs patients vus ensemble** (fratrie, couple) : ajout d'autres patients sans repartir de zéro, chacun inscrit au journal.
- **Signature et cachet** : case cochable conservée ; signature et cachet chargés depuis le profil chiffré.
- **Courriers aux confrères** : mise en page de courrier classique, sans signe de génération par IA (paragraphes courts, liste numérotée simple si besoin, pas de titres colorés ni de puces), points importants en gras ; motifs formulés comme des questions, le confrère reste juge de la stratégie et des explorations ; sobre, sans plaidoyer, au plus une phrase discrète pour demander un rendez-vous rapide.
- **Certificat descriptif de lésions** : description précise (siège, taille, aspect), ITT laissée en blanc.
- **Certificats psychiatriques (soins sans consentement)** : formules légales reprises mot pour mot du modèle ; je ne rédige que les deux parties cliniques descriptives, sans terme diagnostique ni mention de traitement.
- **Compte rendu de prise en charge** : titre « COMPTE RENDU DE PRISE EN CHARGE » (jamais « médico-légal »), factuel, daté, horodaté ; résumé en tête, puis chronologie, antécédents, traitements, examen, examens complémentaires, interprétation, évolution, conduite à tenir, traçabilité des échanges, consignes. Règles de sécurité : § 7.
- **ECG** : lecture structurée et experte à partir du tracé, conclusion de l'appareil seulement comme comparaison, désaccord signalé.

## 5. Grille de validation d'une fiche (pour moi)

1. Les signes de gravité sont-ils complets et en tête ?
2. Les critères simple / à risque sont-ils justes, et chaque pack correspond-il à ma pratique ?
3. Les posologies, durées et variantes (enfant, grossesse, allaitement, rein, allergie) sont-elles justes ?
4. La source est-elle la bonne et à jour ? La divergence éventuelle est-elle tranchée ?
5. L'ordonnance tient-elle sur une page ?
6. La liste de vérification est-elle utile sans me ralentir (bons niveaux) ? La trame de compte rendu et les points de traçabilité sont-ils complets ?
7. Les mots-clés retrouvent-ils la fiche avec mes mots et ceux de la régulation ? Les fiches voisines sont-elles les bonnes ?
8. Les conseils patient sont-ils compréhensibles par un patient ?
→ Si oui : « validée » avec la date. Sinon : corrections, puis nouvelle relecture.

## 6. Ressources locales — à compléter

Deux listes séparées :

- **Liste patient** (imprimable dans Packs, « Numéros utiles — Orléans ») : uniquement des numéros publics (urgences et gardes, CHU d'Orléans par service, laboratoires, imagerie, violences, addictions, santé mentale, social). Rédigée par Claude à partir des sources officielles (CHU d'Orléans, Santé.fr, Annuaire santé ameli, ARS Centre-Val de Loire, numéros nationaux), chaque numéro avec sa source et sa date, statut « à relire ».
- **Liste pro** (courriers et orientations, jamais remise au patient) : à compléter par moi, dictée en vrac au fil des gardes — avis spécialisés et lignes directes du CHU, astreintes, imagerie de garde, kinés, IDE, SSIAD, HAD, régulation, pharmacie de garde.

## 7. Sécurité médico-légale du compte rendu (et place de l'IA)

**Principe** : ce qui protège, c'est ce qui est écrit. Le compte rendu est complet, factuel, horodaté et sans contradiction ; on ne retire jamais un fait pour se protéger.

**Ce que l'IA fait (v41)** :
- Signale avant validation les manques : signes de gravité recherchés non notés comme négatifs, consignes de reconsultation non tracées, refus du patient non écrit, choix hors recommandation sans justification.
- Neutralise la formulation : pas de jugement ni de terme subjectif, pas de certitude non étayée, pas d'abréviation ambiguë ; des faits, des horaires, des constats.
- Trace le raisonnement (éléments qui ont conduit à la décision) et l'information donnée (consignes remises, signes devant faire rappeler le 15, compréhension, présence d'un proche).
- Suit la trame « Éléments de compte rendu » et les points de traçabilité de la fiche.

**Ce que l'IA ne fait jamais** :
- Écrire un examen, un geste ou un résultat non dicté.
- Retirer ou modifier un fait clinique, un horaire ou une décision rapportés.
- Modifier un compte rendu validé sans trace de la modification.

**Niveaux d'utilisation de l'IA** (menu ⋯, un geste) :
- **Complet** : tout automatique (suggestion de fiche à la capture de régulation, observation à la fin de la dictée, compte rendu, courrier et conseils à la fin de consultation, synthèse de garde).
- **Partiel** : fonction par fonction, automatique / à la demande / coupée.
- **Aucun** : Packs sans IA, zéro envoi, zéro coût.
- Passage automatique en **Aucun** hors connexion ou au plafond mensuel atteint.

**Optimisation du coût** : local d'abord (mots-clés, motif de régulation, IA seulement si ambigu) ; Haiku pour trier et suggérer, Sonnet pour rédiger ; mise en cache des consignes fixes ; un seul appel par étape (observation, compte rendu et courrier ensemble) ; synthèse de garde en lot différé à demi-tarif ; réponses courtes et structurées. Cible : moins de 10 € par mois en mode Complet.

**Suivi de la consommation** : écran « Consommation IA » (coût du jour, de la garde, du mois, par usage et par modèle, coût moyen par patient), plafond mensuel fixé par moi avec alerte avant d'être atteint. Calculé sur l'appareil, sans donnée identifiante.

**Place de l'IA dans Packs** :
- Jamais sur le chemin critique : pack, doses et documents restent instantanés et hors ligne ; l'IA est un bouton facultatif avec repli manuel.
- Posologies et durées viennent toujours des fiches validées, jamais de l'IA.
- Avant tout envoi : nom, date de naissance, adresse et téléphone retirés, remis localement ensuite. Clé API rangée chiffrée dans le profil, jamais dans un fichier publié.
- À faire valider avant usage sur de vrais patients : DPO de l'association (hébergement des données de santé, consentement si transcription) et réglementation des dispositifs médicaux.
