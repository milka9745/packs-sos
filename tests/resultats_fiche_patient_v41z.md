# Fiche patient (08/11/2026) — 260/260 tests OK

Bloc identité, allergies et traitements, options, fiche de régulation, en-tête ordinateur. Patients fictifs.

| Résultat | Point | Détail |
|---|---|---|
| OK | ordinateur 1280 · complet : bloc identité présent, tout en haut de la carte patient (premier élément après le titre) |  |
| OK | ordinateur 1280 · complet : ordre fixe : Nom · Prénom · Date de naissance · Sexe · Poids |  |
| OK | ordinateur 1280 · complet : ordinateur : une seule ligne |  |
| OK | ordinateur 1280 · complet : encadré de la couleur du mode (Consultation), bordure ≥ 2 px |  |
| OK | ordinateur 1280 · complet : gros caractères (≥ 18 px iPhone, ≥ 20 px ordinateur), sexe F / M |  |
| OK | ordinateur 1280 · complet : « dupont marie » puis Entrée : NOM en capitales, prénom séparé (« DUPONT Marie »), focus sur la date de naissance |  |
| OK | ordinateur 1280 · complet : sexe déduit du prénom (Marie → F), marqué comme déduit |  |
| OK | ordinateur 1280 · complet : « 03041958 » puis Entrée : date normalisée, âge calculé affiché, focus sur le poids (sexe déjà déduit) |  |
| OK | ordinateur 1280 · complet : sexe déduit affiché en pointillé avec la mention « prénom ? » (à confirmer d'un toucher) |  |
| OK | ordinateur 1280 · complet : « 72 » puis Entrée : poids enregistré, focus sur le motif (recherche de fiche) |  |
| OK | ordinateur 1280 · complet : Tab passe aussi du nom au prénom |  |
| OK | ordinateur 1280 · complet : toucher M : sexe homme confirmé (plus de pointillé), « né le », accords au masculin sur les documents |  |
| OK | ordinateur 1280 · complet : toucher F : « née le », accords au féminin |  |
| OK | ordinateur 1280 · complet : sexe obligatoire : sans sexe, le champ est signalé en rouge (« Sexe ? ») et les documents restent neutres (« date de naissance : ») |  |
| OK | ordinateur 1280 · complet : doses au poids : les lignes de médicaments changent avec le poids (18 → 24 kg) sur une fiche enfant, âge affiché |  |
| OK | ordinateur 1280 · complet : Allergies (champ + case « Allergie aux pénicillines ») puis Traitements en cours, juste sous l'identité, visibles sans dépliage |  |
| OK | ordinateur 1280 · complet : Traitements : « metf » propose METFORMINE depuis la base médicaments, Entrée l'ajoute |  |
| OK | ordinateur 1280 · complet : Allergies : « Iode » ajouté, case pénicillines cochée → allergie pénicillines retenue, pastilles visibles |  |
| OK | ordinateur 1280 · complet : Traitements : AVK saisi + fiche avec AINS → alerte d'interaction affichée avant l'ordonnance |  |
| OK | ordinateur 1280 · complet : documents : traitement et allergie lus apparaissent en proposition (pastille pointillée « proposé · source ») dans chaque ligne, sans être repris |  |
| OK | ordinateur 1280 · complet : ✓ reprend le traitement (posologie lue gardée), ✕ écarte l'allergie ; plus aucune proposition affichée |  |
| OK | ordinateur 1280 · complet : options secondaires (date, cachet, grossesse, allaitement, 2 par A4) sous les lignes allergies et traitements, en plus petit que l'identité |  |
| OK | ordinateur 1280 · complet : « Signature et cachet » coché par défaut ; grossesse et allaitement masqués pour une patiente de 68 ans |  |
| OK | ordinateur 1280 · complet : visite · fiche « Née le » : NOM / Prénom (« DUBOIS » / « Claire »), naissance, sexe F lu sur la fiche, téléphone et adresse repris dans le bloc identité |  |
| OK | ordinateur 1280 · complet : visite · fiche « Né(e) le » (ambiguë) : sexe déduit du prénom (PAUL → M), signalé comme déduit |  |
| OK | ordinateur 1280 · complet : visite · fiche « Sexe : M » avec prénom mixte (Dominique) : sexe lu sur la fiche |  |
| OK | ordinateur 1280 · complet : visite · prénom inconnu et « Né(e) » : sexe laissé vide et signalé (obligatoire), rien d'inventé |  |
| OK | ordinateur 1280 · complet : visite : un toucher sur F fixe le sexe |  |
| OK | ordinateur 1280 · complet : consultation attendue (fiche « Chez Consultation ») : identité et sexe déduit du prénom (ANNE → F) à l'ouverture du dossier |  |
| OK | ordinateur 1280 · complet : aucune erreur JavaScript |  |
| OK | ordinateur 1280 · Express : bloc identité présent, tout en haut de la carte patient (premier élément après le titre) |  |
| OK | ordinateur 1280 · Express : ordre fixe : Nom · Prénom · Date de naissance · Sexe · Poids |  |
| OK | ordinateur 1280 · Express : ordinateur : une seule ligne |  |
| OK | ordinateur 1280 · Express : encadré de la couleur du mode (Consultation), bordure ≥ 2 px |  |
| OK | ordinateur 1280 · Express : gros caractères (≥ 18 px iPhone, ≥ 20 px ordinateur), sexe F / M |  |
| OK | ordinateur 1280 · Express : « dupont marie » puis Entrée : NOM en capitales, prénom séparé (« DUPONT Marie »), focus sur la date de naissance |  |
| OK | ordinateur 1280 · Express : sexe déduit du prénom (Marie → F), marqué comme déduit |  |
| OK | ordinateur 1280 · Express : « 03041958 » puis Entrée : date normalisée, âge calculé affiché, focus sur le poids (sexe déjà déduit) |  |
| OK | ordinateur 1280 · Express : sexe déduit affiché en pointillé avec la mention « prénom ? » (à confirmer d'un toucher) |  |
| OK | ordinateur 1280 · Express : « 72 » puis Entrée : poids enregistré, focus sur le motif (recherche de fiche) |  |
| OK | ordinateur 1280 · Express : Tab passe aussi du nom au prénom |  |
| OK | ordinateur 1280 · Express : toucher M : sexe homme confirmé (plus de pointillé), « né le », accords au masculin sur les documents |  |
| OK | ordinateur 1280 · Express : toucher F : « née le », accords au féminin |  |
| OK | ordinateur 1280 · Express : sexe obligatoire : sans sexe, le champ est signalé en rouge (« Sexe ? ») et les documents restent neutres (« date de naissance : ») |  |
| OK | ordinateur 1280 · Express : doses au poids : les lignes de médicaments changent avec le poids (18 → 24 kg) sur une fiche enfant, âge affiché |  |
| OK | ordinateur 1280 · Express : Allergies (champ + case « Allergie aux pénicillines ») puis Traitements en cours, juste sous l'identité, visibles sans dépliage |  |
| OK | ordinateur 1280 · Express : Traitements : « metf » propose METFORMINE depuis la base médicaments, Entrée l'ajoute |  |
| OK | ordinateur 1280 · Express : Allergies : « Iode » ajouté, case pénicillines cochée → allergie pénicillines retenue, pastilles visibles |  |
| OK | ordinateur 1280 · Express : Traitements : AVK saisi + fiche avec AINS → alerte d'interaction affichée avant l'ordonnance |  |
| OK | ordinateur 1280 · Express : documents : traitement et allergie lus apparaissent en proposition (pastille pointillée « proposé · source ») dans chaque ligne, sans être repris |  |
| OK | ordinateur 1280 · Express : ✓ reprend le traitement (posologie lue gardée), ✕ écarte l'allergie ; plus aucune proposition affichée |  |
| OK | ordinateur 1280 · Express : options secondaires (date, cachet, grossesse, allaitement, 2 par A4) sous les lignes allergies et traitements, en plus petit que l'identité |  |
| OK | ordinateur 1280 · Express : « Signature et cachet » coché par défaut ; grossesse et allaitement masqués pour une patiente de 68 ans |  |
| OK | ordinateur 1280 · Express : visite · fiche « Née le » : NOM / Prénom (« DUBOIS » / « Claire »), naissance, sexe F lu sur la fiche, téléphone et adresse repris dans le bloc identité |  |
| OK | ordinateur 1280 · Express : Express ordinateur : résumé en tête de l'Express et bloc modifiable dans la carte Patient (un clic sur le résumé y conduit) |  |
| OK | ordinateur 1280 · Express : Express ordinateur : le clic place le curseur sur le nom de la carte Patient |  |
| OK | ordinateur 1280 · Express : visite · fiche « Né(e) le » (ambiguë) : sexe déduit du prénom (PAUL → M), signalé comme déduit |  |
| OK | ordinateur 1280 · Express : visite · fiche « Sexe : M » avec prénom mixte (Dominique) : sexe lu sur la fiche |  |
| OK | ordinateur 1280 · Express : visite · prénom inconnu et « Né(e) » : sexe laissé vide et signalé (obligatoire), rien d'inventé |  |
| OK | ordinateur 1280 · Express : visite : un toucher sur F fixe le sexe |  |
| OK | ordinateur 1280 · Express : consultation attendue (fiche « Chez Consultation ») : identité et sexe déduit du prénom (ANNE → F) à l'ouverture du dossier |  |
| OK | ordinateur 1280 · Express : aucune erreur JavaScript |  |
| OK | iPhone 375 · complet : bloc identité présent, tout en haut de la carte patient (premier élément après le titre) |  |
| OK | iPhone 375 · complet : ordre fixe : Nom · Prénom · Date de naissance · Sexe · Poids |  |
| OK | iPhone 375 · complet : iPhone : deux lignes (Nom et Prénom ; Naissance, Sexe, Poids) |  |
| OK | iPhone 375 · complet : encadré de la couleur du mode (Consultation), bordure ≥ 2 px |  |
| OK | iPhone 375 · complet : gros caractères (≥ 18 px iPhone, ≥ 20 px ordinateur), sexe F / M |  |
| OK | iPhone 375 · complet : « dupont marie » puis Entrée : NOM en capitales, prénom séparé (« DUPONT Marie »), focus sur la date de naissance |  |
| OK | iPhone 375 · complet : sexe déduit du prénom (Marie → F), marqué comme déduit |  |
| OK | iPhone 375 · complet : « 03041958 » puis Entrée : date normalisée, âge calculé affiché, focus sur le poids (sexe déjà déduit) |  |
| OK | iPhone 375 · complet : sexe déduit affiché en pointillé avec la mention « prénom ? » (à confirmer d'un toucher) |  |
| OK | iPhone 375 · complet : « 72 » puis Entrée : poids enregistré, focus sur le motif (recherche de fiche) |  |
| OK | iPhone 375 · complet : Tab passe aussi du nom au prénom |  |
| OK | iPhone 375 · complet : toucher M : sexe homme confirmé (plus de pointillé), « né le », accords au masculin sur les documents |  |
| OK | iPhone 375 · complet : toucher F : « née le », accords au féminin |  |
| OK | iPhone 375 · complet : sexe obligatoire : sans sexe, le champ est signalé en rouge (« Sexe ? ») et les documents restent neutres (« date de naissance : ») |  |
| OK | iPhone 375 · complet : doses au poids : les lignes de médicaments changent avec le poids (18 → 24 kg) sur une fiche enfant, âge affiché |  |
| OK | iPhone 375 · complet : Allergies (champ + case « Allergie aux pénicillines ») puis Traitements en cours, juste sous l'identité, visibles sans dépliage |  |
| OK | iPhone 375 · complet : Traitements : « metf » propose METFORMINE depuis la base médicaments, Entrée l'ajoute |  |
| OK | iPhone 375 · complet : Allergies : « Iode » ajouté, case pénicillines cochée → allergie pénicillines retenue, pastilles visibles |  |
| OK | iPhone 375 · complet : Traitements : AVK saisi + fiche avec AINS → alerte d'interaction affichée avant l'ordonnance |  |
| OK | iPhone 375 · complet : documents : traitement et allergie lus apparaissent en proposition (pastille pointillée « proposé · source ») dans chaque ligne, sans être repris |  |
| OK | iPhone 375 · complet : ✓ reprend le traitement (posologie lue gardée), ✕ écarte l'allergie ; plus aucune proposition affichée |  |
| OK | iPhone 375 · complet : options secondaires (date, cachet, grossesse, allaitement, 2 par A4) sous les lignes allergies et traitements, en plus petit que l'identité |  |
| OK | iPhone 375 · complet : « Signature et cachet » coché par défaut ; grossesse et allaitement masqués pour une patiente de 68 ans |  |
| OK | iPhone 375 · complet : iPhone : options repliées sous « Options » (allergies et traitements restent visibles) |  |
| OK | iPhone 375 · complet : visite · fiche « Née le » : NOM / Prénom (« DUBOIS » / « Claire »), naissance, sexe F lu sur la fiche, téléphone et adresse repris dans le bloc identité |  |
| OK | iPhone 375 · complet : visite · fiche « Né(e) le » (ambiguë) : sexe déduit du prénom (PAUL → M), signalé comme déduit |  |
| OK | iPhone 375 · complet : visite · fiche « Sexe : M » avec prénom mixte (Dominique) : sexe lu sur la fiche |  |
| OK | iPhone 375 · complet : visite · prénom inconnu et « Né(e) » : sexe laissé vide et signalé (obligatoire), rien d'inventé |  |
| OK | iPhone 375 · complet : visite : un toucher sur F fixe le sexe |  |
| OK | iPhone 375 · complet : consultation attendue (fiche « Chez Consultation ») : identité et sexe déduit du prénom (ANNE → F) à l'ouverture du dossier |  |
| OK | iPhone 375 · complet : aucune erreur JavaScript |  |
| OK | iPhone 375 · Express : bloc identité présent, tout en haut de la carte patient (premier élément après le titre) |  |
| OK | iPhone 375 · Express : ordre fixe : Nom · Prénom · Date de naissance · Sexe · Poids |  |
| OK | iPhone 375 · Express : iPhone : deux lignes (Nom et Prénom ; Naissance, Sexe, Poids) |  |
| OK | iPhone 375 · Express : encadré de la couleur du mode (Consultation), bordure ≥ 2 px |  |
| OK | iPhone 375 · Express : gros caractères (≥ 18 px iPhone, ≥ 20 px ordinateur), sexe F / M |  |
| OK | iPhone 375 · Express : « dupont marie » puis Entrée : NOM en capitales, prénom séparé (« DUPONT Marie »), focus sur la date de naissance |  |
| OK | iPhone 375 · Express : sexe déduit du prénom (Marie → F), marqué comme déduit |  |
| OK | iPhone 375 · Express : « 03041958 » puis Entrée : date normalisée, âge calculé affiché, focus sur le poids (sexe déjà déduit) |  |
| OK | iPhone 375 · Express : sexe déduit affiché en pointillé avec la mention « prénom ? » (à confirmer d'un toucher) |  |
| OK | iPhone 375 · Express : « 72 » puis Entrée : poids enregistré, focus sur le motif (recherche de fiche) |  |
| OK | iPhone 375 · Express : Tab passe aussi du nom au prénom |  |
| OK | iPhone 375 · Express : toucher M : sexe homme confirmé (plus de pointillé), « né le », accords au masculin sur les documents |  |
| OK | iPhone 375 · Express : toucher F : « née le », accords au féminin |  |
| OK | iPhone 375 · Express : sexe obligatoire : sans sexe, le champ est signalé en rouge (« Sexe ? ») et les documents restent neutres (« date de naissance : ») |  |
| OK | iPhone 375 · Express : doses au poids : les lignes de médicaments changent avec le poids (18 → 24 kg) sur une fiche enfant, âge affiché |  |
| OK | iPhone 375 · Express : Allergies (champ + case « Allergie aux pénicillines ») puis Traitements en cours, juste sous l'identité, visibles sans dépliage |  |
| OK | iPhone 375 · Express : Traitements : « metf » propose METFORMINE depuis la base médicaments, Entrée l'ajoute |  |
| OK | iPhone 375 · Express : Allergies : « Iode » ajouté, case pénicillines cochée → allergie pénicillines retenue, pastilles visibles |  |
| OK | iPhone 375 · Express : Traitements : AVK saisi + fiche avec AINS → alerte d'interaction affichée avant l'ordonnance |  |
| OK | iPhone 375 · Express : documents : traitement et allergie lus apparaissent en proposition (pastille pointillée « proposé · source ») dans chaque ligne, sans être repris |  |
| OK | iPhone 375 · Express : ✓ reprend le traitement (posologie lue gardée), ✕ écarte l'allergie ; plus aucune proposition affichée |  |
| OK | iPhone 375 · Express : options secondaires (date, cachet, grossesse, allaitement, 2 par A4) sous les lignes allergies et traitements, en plus petit que l'identité |  |
| OK | iPhone 375 · Express : « Signature et cachet » coché par défaut ; grossesse et allaitement masqués pour une patiente de 68 ans |  |
| OK | iPhone 375 · Express : iPhone : options repliées sous « Options » (allergies et traitements restent visibles) |  |
| OK | iPhone 375 · Express : visite · fiche « Née le » : NOM / Prénom (« DUBOIS » / « Claire »), naissance, sexe F lu sur la fiche, téléphone et adresse repris dans le bloc identité |  |
| OK | iPhone 375 · Express : Express iPhone : identité complète → résumé d'une ligne (nom, née le, âge, F) encadré, un toucher pour modifier |  |
| OK | iPhone 375 · Express : Express iPhone : après le toucher, champs modifiables (nom, téléphone…), focus sur le nom |  |
| OK | iPhone 375 · Express : Express iPhone : prénom corrigé d'un toucher → patient « DUBOIS Claire-Marie » |  |
| OK | iPhone 375 · Express : Express iPhone : « ✓ OK » replie le bloc en résumé |  |
| OK | iPhone 375 · Express : visite · fiche « Né(e) le » (ambiguë) : sexe déduit du prénom (PAUL → M), signalé comme déduit |  |
| OK | iPhone 375 · Express : visite · fiche « Sexe : M » avec prénom mixte (Dominique) : sexe lu sur la fiche |  |
| OK | iPhone 375 · Express : visite · prénom inconnu et « Né(e) » : sexe laissé vide et signalé (obligatoire), rien d'inventé |  |
| OK | iPhone 375 · Express : visite : un toucher sur F fixe le sexe |  |
| OK | iPhone 375 · Express : consultation attendue (fiche « Chez Consultation ») : identité et sexe déduit du prénom (ANNE → F) à l'ouverture du dossier |  |
| OK | iPhone 375 · Express : aucune erreur JavaScript |  |
| OK | en-tête 1280 px Express : visite · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : visite · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : visite · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : visite · day · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : visite · day · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : visite · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : visite · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : visite · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : visite · day · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : visite · day · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : visite · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : visite · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : visite · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : visite · night · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : visite · night · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : visite · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : visite · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : visite · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : visite · night · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : visite · night · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : cabinet · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : cabinet · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : cabinet · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : cabinet · day · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : cabinet · day · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : cabinet · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : cabinet · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : cabinet · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : cabinet · day · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : cabinet · day · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : cabinet · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : cabinet · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : cabinet · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : cabinet · night · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : cabinet · night · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : cabinet · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px Express : cabinet · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px Express : cabinet · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px Express : cabinet · night · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px Express : cabinet · night · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px Express : aucune erreur JavaScript |  |
| OK | en-tête 1280 px complet : visite · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : visite · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : visite · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : visite · day · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : visite · day · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : visite · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : visite · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : visite · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : visite · day · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : visite · day · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : visite · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : visite · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : visite · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : visite · night · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : visite · night · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : visite · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : visite · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : visite · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : visite · night · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : visite · night · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : cabinet · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : cabinet · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : cabinet · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : cabinet · day · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : cabinet · day · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : cabinet · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : cabinet · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : cabinet · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : cabinet · day · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : cabinet · day · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : cabinet · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : cabinet · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : cabinet · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : cabinet · night · texte normal : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : cabinet · night · texte normal : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : cabinet · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1280 px complet : cabinet · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1280 px complet : cabinet · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1280 px complet : cabinet · night · grand texte : ⋯ ouvre version, mode test, base médicaments, tournée sous la barre |  |
| OK | en-tête 1280 px complet : cabinet · night · grand texte : Échap (ou un clic ailleurs) referme ⋯ |  |
| OK | en-tête 1280 px complet : aucune erreur JavaScript |  |
| OK | en-tête 1920 px Express : visite · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : visite · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : visite · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : visite · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : visite · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : visite · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : visite · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : visite · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : visite · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : visite · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : visite · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : visite · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : cabinet · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : cabinet · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : cabinet · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : cabinet · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : cabinet · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : cabinet · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : cabinet · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : cabinet · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : cabinet · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : cabinet · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px Express : cabinet · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px Express : cabinet · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px Express : aucune erreur JavaScript |  |
| OK | en-tête 1920 px complet : visite · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : visite · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : visite · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : visite · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : visite · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : visite · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : visite · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : visite · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : visite · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : visite · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : visite · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : visite · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : cabinet · day · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : cabinet · day · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : cabinet · day · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : cabinet · day · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : cabinet · day · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : cabinet · day · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : cabinet · night · texte normal : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : cabinet · night · texte normal : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : cabinet · night · texte normal : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : cabinet · night · grand texte : une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne |  |
| OK | en-tête 1920 px complet : cabinet · night · grand texte : onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte |  |
| OK | en-tête 1920 px complet : cabinet · night · grand texte : « Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque |  |
| OK | en-tête 1920 px complet : aucune erreur JavaScript |  |
