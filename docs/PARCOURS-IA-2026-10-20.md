# Parcours automatisé avec l'IA (v41u, 20/10/2026) — branche ia, /test/ seulement

## Ce qui existait et a été réutilisé
- Dictée : grand champ toujours visible, brouillon chiffré à chaque frappe, « Dictées récentes » (48 h).
- Tournée : champ « interrogatoire téléphonique » sur chaque arrêt (`s.interro`), appel depuis l'arrêt.
- IA : dictée → observation, relecture du compte rendu, courrier ; pseudonymisation sur l'appareil (DPO, 15/10/2026), garde-fous (nombres absents de l'envoi écartés, posologies jamais appliquées), file d'attente hors ligne, plafond mensuel.
- Courriers générés (spécialiste, médecin traitant), compte rendu, impression PDF, validation en deux touchers, journal.
- Pack SOS Médecins = catalogue `PACKS` : l'IA en reçoit la liste ; l'ordonnance vient toujours de la fiche.

## Ce qui a été ajouté
1. **Contre-appel dicté** (tournée étape 1 et 2, Express) : champ `data-interro` sur l'arrêt, gardé dans `s.interro` et dans `state.obs.tel` (éléments rapportés, jamais mêlés à l'histoire ni à l'examen). Fin de dictée → analyse automatique (`aiAutoFlow("tel")`) ; bouton « ✦ Analyser le contre-appel ». Résultat gardé sur l'arrêt (`s.ai`).
2. **Continuité** : au démarrage de la visite, `stopPrefill` reprend `s.interro` → `obs.tel` et la synthèse du contre-appel ; la dictée en visite envoie les deux parties (« CONTRE-APPEL TÉLÉPHONIQUE » rapporté, « EN PRÉSENCE DU PATIENT » constaté). Compte rendu : section « contre-appel téléphonique … patient non examiné » distincte de « EXAMEN CLINIQUE ».
3. **Une seule dictée** : à la sortie du champ (ou « ✦ Préparer »), une seule requête `plan` (prompt `AI_SYS_PLAN`) → observation, fiche(s) avec justification, examens, courriers (MT, spécialiste + question), aide sociale (fiche complémentaire du Pack), suivi, manques, alertes. Jamais deux envois du même texte ; une requête à la fois.
4. **Réglages persistants** (Journal → Assistant IA) : « Après une dictée : préparer automatiquement / à la demande » ; « Envoi : automatique après pseudonymisation / écran Ce qui part à chaque fois ». L'écran reste forcé si un fragment d'identité subsiste, hors connexion ou au plafond.
5. **Écran de synthèse** (`aiSynthHTML`) : chaque élément cochable, justification visible, « ce qui est parti » consultable, « ✓ Appliquer la synthèse » (fiche confirmée, courriers activés, examens cochés ou ajoutés, fiche sociale ajoutée), « Ignorer ». Rien n'est imprimé ni validé par l'IA.
6. **Protection** : champ de dictée touché repris dans l'état avant tout rendu (`dictSyncFromDOM`), dictée versée aux « Dictées récentes » avant tout changement de patient ; erreur IA → message, rien modifié ; hors ligne → demande gardée sur l'appareil.
7. **Verrous** : réponse appliquée seulement à la consultation qui l'a demandée (clé `state.ck` + nom) ; champs corrigés à la main (`obsEdited`) jamais écrasés, ni par l'IA ni par « Répartir » ; mode téléphone : appareils et constantes renvoyés par l'IA écartés.

## Tests (tests/test_auto19.py, API simulée, 120 contrôles)
iPhone Express, iPhone mode complet, tablette Express, PC mode complet : contre-appel, continuité, consultation, Pack transmis et ordonnance issue de la fiche, correction manuelle, hors ligne puis retour du réseau, changement de patient pendant une requête, validation explicite, impression, réglage « écran à chaque fois », dictée jamais perdue.

## Non vérifié ici
- Conformité d'hébergement des données de santé (HDS) du fournisseur d'IA : non vérifiable depuis l'application. Seul un texte pseudonymisé sur l'appareil part (validation DPO du 15/10/2026 pour cette pseudonymisation) ; la clé API reste dans le navigateur (chiffrée).
- Les réponses réelles du modèle : testées avec des réponses simulées ; les garde-fous (nombres, posologies, jetons) s'appliquent de la même façon aux vraies réponses.
- Micro de l'iPhone en conditions réelles (dictée vocale) : testé par simulation du champ.
