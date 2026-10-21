# Résultats — documents du patient (v41z, demande globale IV–IX)

2026-10-21

49/49 OK — tous les tests passent

Temps mesurés : {"scan page": 0.16, "OCR + analyse (2 pages)": 0.59, "OCR page (ms)": 468, "traitement page (ms)": 92, "import 3 images + PDF": 1.78}

- OK fixtures : 8 images et 1 PDF fictifs générés sur place (aucune donnée réelle)
- OK IV.15 / IX.38 : « Scanner » et « Documents » à côté de la dictée, mêmes boutons au même endroit en consultation, en visite et sur une fiche
- OK IV.16 : page scannée recadrée et redressée, noir et blanc, réduite (≤ 230 Ko), chiffrée, lue sur l'appareil ; bilan du 12/09/2026 reconnu
- OK IV.16 : compteur de pages, « Page suivante », « Reprendre la dernière », « Terminer (2) » ; page floue signalée, reprise proposée, jamais de devinette
- OK IV.16 : page vide ou trop claire détectée (« page vide ou trop claire »), signalée sans invention de texte
- OK IV.16 : document regroupé (2 pages, 1 illisible signalée dans le statut), bilan du 12/10/2026
- OK V.21 : valeurs, unités et classement lus sur la page scannée (Hb basse légère, plaquettes et kaliémie à surveiller, créatinine haute, glycémie 1,45 g/L convertie en mmol/L, CRP « < 5 », INR sous AVK)
- OK V.21 : DFG calculé automatiquement — CKD-EPI 2021 39 ± 1 et Cockcroft 40 ± 1 (âge, sexe, poids de la fiche), stade G3b
- OK IV.17 : mode « écran de téléphone » (texte clair sur fond sombre, pas de recadrage feuille) : texte lu, ELIQUIS reconnu
- OK IV.18 : 4 fichiers importés d'un coup (3 photos + 1 PDF de 2 pages), nombre confirmé, liste avec type et intitulé ; PDF lu par le lecteur embarqué (texte natif, sans OCR)
- OK V.20 : types reconnus par mots-clés et mise en page — bilan, bilan, ordonnance (écran), courrier, compte rendu d'hospitalisation, carte de vaccination, ordonnance (PDF)
- OK IV.18 : miniatures des pages (déchiffrées à la demande) et texte lu affichés
- OK IV.18 : stockage presque plein → avertissement clair (40 Mo libres), puis refus expliqué sous 8 Mo, jamais de blocage silencieux
- OK V.22 : ordonnance PDF → 5 médicaments reconnus via la base intégrée, anticoagulant et antiagrégant signalés
- OK V.22 : courrier → spécialité cardiologie, date 15/09/2026, conclusion extraite après « en conclusion »
- OK V.23 : antécédents du courrier datés et rattachés aux critères de risque (FA, HTA, diabète, BPCO, PTH 2019) ; négation « pas d'antécédent familial d'infarctus » ignorée
- OK V.22 : compte rendu d'hospitalisation → allergie aux pénicillines relevée, antécédents (BPCO, tabac, FA, cholécystectomie 2015), conclusion « au total », pneumologie
- OK V.20 : carte de vaccination → 4 vaccins datés (dTP 12/03/2015, grippe, pneumocoque, covid-19)
- OK VII.26 : dès l'import, propositions en attente (traitements, allergie, antécédents, biologie, suivi, vaccins, pack à risque), chacune cochée, avec « Pourquoi ? » et un geste « Tout accepter »
- OK V.21 : tendance entre deux bilans (12/09 → 12/10) : créatinine 110 → 130 en hausse, plaquettes 160 → 92 en baisse
- OK VII.26 : avant accord, ni le compte rendu ni la fiche ne contiennent les éléments des documents
- OK VII.26 : « Tout accepter » reprend les lignes cochées (COVERSYL décoché non repris) : traitements, allergie (pénicillines), antécédents, biologie et DFG, suivi, vaccins, pack à risque
- OK VII.26 / IV.19 : « Ce que disent les documents » en tête de l'observation (documents consultés, antécédents retenus, biologie, suivi, liens avec « Pourquoi ? »)
- OK IV.19 : compte rendu — « DOCUMENTS ET RÉSULTATS CONSULTÉS » liste chaque document (nature, date, pages) puis les résultats retenus après accord
- OK V.24 : alertes croisées sans IA (anticoagulant + plaquettes 92, metformine + DFG 30–44, AINS + DFG < 60, AINS + diurétique) ; pas d'alerte kaliémie + IEC puisque COVERSYL n'a pas été repris
- OK V.24 : ces alertes sont visibles à l'écran au-dessus des feuilles
- OK V.24 : DFG < 30 → metformine et AINS prescrit contre-indiqués (⛔), décision du prescripteur demandée avant impression
- OK VIII.33 : liens entre les faits avec renvoi à la règle (DFG → AINS et doses, anticoagulant → pas d'IM, kaliémie, FA → scores, BPCO, allergie → alternatives)
- OK VIII.30 : CHA2DS2-VASc pré-rempli d'après les documents (HTA, diabète, âge 65–74, sexe), HAS-BLED (antiagrégant), avec « Pourquoi ? » ; critères de Fried ajoutés
- OK VII.27 : courrier au médecin traitant — documents consultés, biologie retenue avec DFG, suivi spécialisé, antécédents à risque, synthèse en annexe
- OK VII.27 : courrier au spécialiste — éléments des documents (biologie, suivi) sans le détail
- OK VIII.34 : rappels de suivi issus des documents proposés au médecin traitant (contrôle de la kaliémie, fonction rénale, suivi cardiologique, rappel dTP, grippe)
- OK VI.25 : synthèse en une page, ordre fixe (points d'attention ≤ 3, antécédents par appareil, traitements, allergies, biologie, suivi, vaccins), phrases naturelles, source sur chaque ligne
- OK VI.25 : chaque ligne corrigeable d'un toucher (texte corrigé, ligne vide = retirée), corrections conservées et chiffrées avec le dossier
- OK VI.25 / VII.27 : résumé imprimable sur une page (en-tête habituel, lignes retirées absentes, sources et dates)
- OK VII.28 : avec l'IA activée, « Synthèse IA complémentaire » sur le texte extrait et anonymisé (jamais l'image), écran « Ce qui part », rien d'envoyé sans accord
- OK VII.28 : IA coupée → pas de bouton de synthèse IA
- OK VIII.29 : dictée structurée — allergie, traitement habituel, taille (IMC calculé), constantes rangés en direct
- OK VIII.31 : questions restantes filtrées par ce qui est connu (pas d'allergie à redemander), bloquant d'abord
- OK VIII.32 : « Avant d'imprimer, il manque : poids (…) » en une ligne avec la raison, disparaît une fois le poids et la température saisis
- OK VIII.35 : fiche utilisée 3 fois en 90 jours signalée « souvent » et proposée en premier
- OK VIII.37 : chaque proposition porte un « Pourquoi ? » (source et règle) et se refuse d'un toucher (« Ignorer » : rien n'est repris)
- OK IX.40 : vitesse mesurée et affichée (ouverture d'un patient, scan d'une page, lecture, analyse, affichage d'une fiche) ; scan + analyse d'une page sous 3 s
- OK IX.41 : après fermeture et réouverture, documents, analyses et propositions restaurés ; page scannée relue depuis la base chiffrée
- OK sécurité : aucune erreur JavaScript, aucun appel réseau externe pendant toute la suite
- OK IX.39 (iPhone jour) : parcours tournée → patient → scan → documents → accord → dictée → fiche → impression → validation → patient suivant, sans erreur
- OK IX.39 (iPhone nuit) : parcours tournée → patient → scan → documents → accord → dictée → fiche → impression → validation → patient suivant, sans erreur
- OK IX.39 (iPhone grand texte) : parcours tournée → patient → scan → documents → accord → dictée → fiche → impression → validation → patient suivant, sans erreur
- OK IX.39 (ordinateur) : parcours tournée → patient → scan → documents → accord → dictée → fiche → impression → validation → patient suivant, sans erreur
