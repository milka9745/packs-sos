# Tests anonymisation v41z — corpus piégé, fuzzing, faux positifs, vitesse, doutes, strict, listes, worker

- OK — corpus : 100 dictées piégées (100) → 88 entièrement masquées, 12 bloquées (second contrôle ou mot à confirmer), 0 fuites
- OK — fuzzing : 1000 variantes → 829 masquées, 171 bloquées (second contrôle ou mot à confirmer), 0 fuites (zéro exigé)
- OK — faux positifs : 3 mots masqués à tort sur 578 (0.5 %) dans 30 dictées sans identité (objectif < 3 %)
- OK — vitesse (cet ordinateur, Chromium) : 20 dictées de 2081 caractères → médiane 1 ms, maximum 2 ms (objectif iPhone < 100 ms, non mesuré ici)
- OK — année seule → relative, numéro de dossier et RPPS masqués
- OK — établissements connus masqués (Lycée Pothier, Auchan)
- OK — second contrôle : « Rousselon » (une lettre) masqué, bloqué ou à confirmer — jamais en clair sans contrôle
- OK — second contrôle : « rousselon » en minuscules (une lettre) repéré comme forme approchée ou doute
- OK — second contrôle : nom coupé en deux repéré (« ROUSSE LIN »)
- OK — doutes : mot inconnu avec majuscule à confirmer, médicament et mot courant non signalés
- OK — listes personnelles : « Oréliance » toujours masqué, « Zxqvu » toujours gardé et non douteux
- OK — mode strict : plus de mots masqués, numéros d'au moins 4 chiffres masqués, médicament gardé
- OK — âge regroupé au-delà de 89 ans
- OK — worker d'anonymisation : réponse hors fil principal, éléments masqués, aucune fuite, temps mesuré
- OK — aucune erreur JS

15/15 tests OK
