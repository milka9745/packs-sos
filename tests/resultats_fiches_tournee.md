# Fiches MccMissionSG et tournée sans question (09/11/2026)

34/34 tests OK

- OK source : « Intégrer au mieux » et « En fin de tournée » retirés des nouvelles demandes
- OK source : état « Entre deux » retiré du fil, intégration automatique et lecture par intitulés présentes
- OK fiches : nouvelle présentation : le nom est la ligne sous « INFORMATIONS PATIENT » (« DUPONT-MARTIN » / « Jean-Pierre Marie »), jamais « CH G » de l'en-tête
- OK fiches : n1 : naissance, âge affiché, téléphone, adresse (« Etg / Por » vides ignorés)
- OK fiches : n1 : motif en gras « DL TETE / FIEVRE », texte libre en note ; « PARTICULIER », la date d'appel et « 2h7m » jamais repris
- OK fiches : n1 : heure d'appel lue (il y a 2 h 07) → regTs à l'heure de l'appel, attente 127 min, aucune alerte « nom non lu »
- OK fiches : n2 : nom composé à particule en capitales « LE GOFF » / « LOUIS GABRIEL », téléphone sur la ligne suivante, accès Bât/Étage/Porte
- OK fiches : n2 : attente « 0h45m » sur la ligne sous la date → 45 min ; motif OTITE ; note = texte libre
- OK fiches : n3 : ligne du nom illisible → nom vide et « nom non lu » signalé ; rien n'est pris ailleurs (ni OPJ, ni POLICE, ni le motif)
- OK fiches : n4 : icône de sexe lue comme un caractère isolé après le nom → ignorée (« DUPONT » / « Jean »)
- OK fiches : ancienne présentation (texte collé, nom en tête) : « DUPONT » / « MARIE », « Née le » → F, motif après « N° INTERVENTION », note
- OK fiches : ancienne présentation Android (intitulés en minuscules) : « DUBOIS » / « CLAIRE », téléphone patient, motif, accès
- OK fiches : fiche d'un autre jour : « MARTIN » / « PAUL », motif « GARDE A VUE », mention « repositionnée par » ignorée, heure d'appel trop ancienne → attente affichée (1h40m) utilisée
- OK tournée 375 : départ : visite en cours, barre « En route »
- OK tournée 375 : 1re demande (fiche collée) : intégrée d'elle-même, sans question — dans l'ordre, plus « nouvelle », information d'intégration
- OK tournée 375 : 1re demande : carte « Nouvelle demande » = une ligne « intégrée en Ne position, + N min sur la fin de tournée », rang conforme à l'ordre
- OK tournée 375 : 1re demande : deux boutons discrets (📞 Appeler, ★ Priorité), aucun « Intégrer au mieux » ni « En fin de tournée », barre inchangée « En route », rien dans la barre du bas
- OK tournée 375 : 1re demande : nom lu sur la fiche (« LE GOFF LOUIS GABRIEL »), km du cabinet calculés pour la cotation
- OK tournée 375 : 2e demande : intégrée, deux lignes dans la carte, chaque rang écrit = rang réel
- OK tournée 375 : 2e demande : les deux lignes d'information suivent l'ordre recalculé
- OK tournée 375 : 3e demande (appel il y a 2 h 07) : patient qui attend déjà plus de 2 h → placé devant les autres (après les priorités), ligne « attend depuis 2 h 07 »
- OK tournée 375 : 3e demande : alerte « 1 patient attend depuis plus de 2 h » dans le bandeau, 3 lignes « Nouvelle demande », pas de défilement horizontal
- OK tournée 375 : ★ Priorité sur une demande : passe devant tout, ordre recalculé sans question, ligne « prioritaire, intégrée en 1re position », bouton marqué
- OK tournée 375 : à priorité égale, l'attente puis le trajet décident : le patient qui attend depuis plus de 2 h vient juste après la priorité
- OK tournée 375 : 4e demande (adresse tapée, arrivée au cabinet réglée) : « + N min sur l'arrivée au cabinet », 4 lignes
- OK tournée 375 : adresse introuvable : placée en fin de tournée sans question, ligne « adresse introuvable … corrige l'adresse »
- OK tournée 375 : « Rendre à la régulation » : une entrée par demande dans le tiroir « Plus » de la carte, rien dans la barre du bas
- OK tournée 375 : « Rendre à la régulation » : confirmée au 2e toucher, demande retirée et tracée, 3 lignes restantes, barre inchangée
- OK tournée 375 : « Retirer » une visite : ordre recalculé aussitôt, sans question ni message
- OK tournée 375 : ordre modifié → une ligne discrète « Ordre mis à jour à HH h MM · prochaine visite : … »
- OK tournée 375 : écran principal : la même ligne discrète sous la carte de visite
- OK tournée 375 : patient validé : visite faite, ordre recalculé de lui-même (mode test : journal intact)
- OK tournée 375 : écran Tournée : l'heure d'appel de la fiche est écrite sur la ligne du patient (« appel HH h MM »)
- OK tournée 375 : aucune erreur JavaScript
