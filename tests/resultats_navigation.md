# Navigation et tournée — 12/11/2026

Touchers de tournée sur le parcours iPhone (5 patients fictifs, hors acte médical : fiche, impression) :

| Geste | Touchers |
|---|---|
| ▶ Lancer la tournée | 1 |
| ✓ Valider (1er toucher : confirmer) | 5 |
| ✓ Valider (2e toucher : validé) | 5 |
| ✓ Je suis arrivé (adresse non géocodée) | 3 |
| **Total** | **14** — soit 2.8 par patient ; aucun toucher « Naviguer » ni « Patient suivant » |

Résultat : 62/62 tests OK

| Test | Résultat |
|---|---|
| source : plus de « Localiser l'adresse » ni de lien de navigation target=_blank ; ouverture par window.location.href | OK |
| source : géocodeur Géoplateforme (IGN) en premier, ancienne adresse en secours, délai borné (AbortController) | OK |
| source : communes d'Orléans Métropole (23 couples) pour compléter les adresses | OK |
| iPhone écran d'accueil : étape Demande : « ▶ Lancer la tournée » en action principale | OK |
| iPhone écran d'accueil : ▶ : visite en cours et guidage lancé en un toucher (moins de 1 s), patient le plus proche du cabinet (coordonnées connues) | OK |
| iPhone écran d'accueil : ▶ : URL Waze avec les coordonnées (ll=LAT,LON&navigate=yes), identique à navUrl | OK |
| iPhone écran d'accueil : En route : « Naviguer » en bas à gauche, libellé fixe, bouton (pas de lien), sans nom d'appli, puis Appeler, puis Je suis arrivé | OK |
| iPhone écran d'accueil : En route : « Appeler » = lien tel: du patient en cours | OK |
| iPhone écran d'accueil : aucun menu de choix d'appli dans la tournée (seulement dans ⋯) | OK |
| iPhone écran d'accueil : retour dans Packs loin de l'adresse (5 km) : rien ne change, « Je suis arrivé » reste | OK |
| iPhone écran d'accueil : retour dans Packs à moins de 150 m (60 m) : passage seul à « Sur place », message « arrivée enregistrée » | OK |
| iPhone écran d'accueil : Sortie : « ✓ Valider · patient suivant » en action principale | OK |
| iPhone écran d'accueil : validation 1 : confirmée (« Confirmer » au 1er toucher), patient précédent fait, visite suivante p1 en cours et guidage lancé, en route (pas d'écran intermédiaire), annulation 8 s | OK |
| iPhone écran d'accueil : p1 : guidage par les coordonnées | OK |
| iPhone écran d'accueil : p1 : arrivée automatique (55 m) | OK |
| iPhone écran d'accueil : validation 2 : confirmée (« Confirmer » au 1er toucher), patient précédent fait, visite suivante p2 en cours et guidage lancé, en route (pas d'écran intermédiaire), annulation 8 s | OK |
| iPhone écran d'accueil : p2 sans coordonnées : guidage par l'adresse en clair normalisée « 25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS » (Waze ?q=…) | OK |
| iPhone écran d'accueil : p2 sans coordonnées : pas d'arrivée automatique possible, « Je suis arrivé » reste | OK |
| iPhone écran d'accueil : p2 : « Je suis arrivé » → Sur place | OK |
| iPhone écran d'accueil : validation 3 : confirmée (« Confirmer » au 1er toucher), patient précédent fait, visite suivante p3 en cours et guidage lancé, en route (pas d'écran intermédiaire), annulation 8 s | OK |
| iPhone écran d'accueil : p3 sans coordonnées : guidage par l'adresse en clair normalisée « 8 RUE CHARLES BEAUHAIRE 45140 SAINT-JEAN-DE-LA-RUELLE » (Waze ?q=…) | OK |
| iPhone écran d'accueil : p3 sans coordonnées : pas d'arrivée automatique possible, « Je suis arrivé » reste | OK |
| iPhone écran d'accueil : p3 : « Je suis arrivé » → Sur place | OK |
| iPhone écran d'accueil : validation 4 : confirmée (« Confirmer » au 1er toucher), patient précédent fait, visite suivante p4 en cours et guidage lancé, en route (pas d'écran intermédiaire), annulation 8 s | OK |
| iPhone écran d'accueil : p4 sans coordonnées : guidage par l'adresse en clair normalisée « 12 ter RUE DE LA GARE 45000 Orléans » (Waze ?q=…) | OK |
| iPhone écran d'accueil : p4 sans coordonnées : pas d'arrivée automatique possible, « Je suis arrivé » reste | OK |
| iPhone écran d'accueil : p4 : « Je suis arrivé » → Sur place | OK |
| iPhone écran d'accueil : dernière validation : écran « Patient validé », tournée terminée, aucun guidage lancé | OK |
| iPhone écran d'accueil : ordre réel de la tournée après le premier patient : p1 (géocodé, le plus proche), puis p2, p3, p4 dans l'ordre des demandes | OK |
| iPhone écran d'accueil : recalcul silencieux après chaque validation (horodatage de l'ordre automatique posé, sans fenêtre ni question) | OK |
| iPhone écran d'accueil : window.open jamais appelé (écran d'accueil iOS : tout passe par window.location.href) | OK |
| iPhone écran d'accueil : aucune erreur JavaScript | OK |
| iPhone boutons : menu ⋯ : « Navigation » avec Waze, Plans, Google Maps ; Waze activé par défaut | OK |
| iPhone boutons : Plans choisi : mémorisé (sos_nav), message « Guidage avec Plans » | OK |
| iPhone boutons : menu ⋯ rouvert : Plans marqué activé | OK |
| iPhone boutons : écran Tournée : un bouton « Naviguer » par arrêt (coordonnées ou non), plus de liens Waze / Maps / Plans, « Patient en cours » et « Appeler » conservés | OK |
| iPhone boutons : écran Tournée : « Naviguer » sur un arrêt non géocodé lance l'adresse normalisée (code postal ajouté) | OK |
| iPhone boutons : écran Tournée : « Trajet complet (Google Maps) » ouvert par location.href | OK |
| iPhone boutons : carte : fenêtre d'un arrêt → bouton « Naviguer » (plus de lien), guidage lancé | OK |
| iPhone boutons : vue conduite : patient actuel et suivant avec « Naviguer » (bouton), Appeler, « Je suis arrivé » sur l'actuel | OK |
| iPhone boutons : vue conduite : « Naviguer » lance le guidage et reste en vue conduite | OK |
| iPhone boutons : vue conduite : « Je suis arrivé » → Sur place | OK |
| iPhone boutons : écran Patient validé : prochain arrêt annoncé avec un bouton « Naviguer » | OK |
| iPhone boutons : « Patient suivant » : visite suivante en cours, étape En route, guidage lancé | OK |
| iPhone boutons : Express : chaque patient de la liste lance le guidage d'un toucher (bouton, pas de lien), avec ou sans coordonnées | OK |
| iPhone boutons : window.open jamais appelé | OK |
| iPhone boutons : aucune erreur JavaScript | OK |
| formats iPhone : Waze : ll=LAT,LON&navigate=yes avec coordonnées, sinon ?q=ADRESSE&navigate=yes | OK |
| formats iPhone : Plans : maps://?daddr=…&dirflg=d (coordonnées ou adresse) | OK |
| formats iPhone : Google Maps : comgooglemaps://?daddr=…&directionsmode=driving, repli https://www.google.com/maps/dir/?api=1&destination=… (Waze : pas de repli) | OK |
| formats iPhone : adresse normalisée : « 25BIS » → « 25 bis », « TER », « quater » ; code postal et commune ajoutés s'ils manquent (commune reconnue, commune du géocodage, sinon Orléans) ; code postal partagé sans commune imposée | OK |
| formats iPhone : Google Maps : le schéma comgooglemaps:// part aussitôt ; la page restant visible, repli web après 1,5 s | OK |
| formats iPhone : aucune erreur JavaScript | OK |
| ordinateur : hors iPhone : Plans et Google Maps par leurs adresses web, Waze inchangé | OK |
| ordinateur : Tournée › Réglages : Navigation Waze / Plans / Google Maps, Waze activé ; rien dans l'en-tête (une seule ligne) | OK |
| ordinateur : choix Google Maps mémorisé | OK |
| ordinateur : aucune erreur JavaScript | OK |
| réseau lent (4 s par appel) : ▶ : guidage lancé en moins de 1 s sans attendre le géocodage ni l'ordre OSRM | OK |
| réseau lent (4 s par appel) : recalcul en arrière-plan terminé seul (délais bornés), patient en cours inchangé, étape En route | OK |
| réseau lent (4 s par appel) : aucune erreur JavaScript | OK |
| hors connexion : ▶ sans réseau ni coordonnées : guidage par l'adresse en clair, aussitôt, « Naviguer » présent, aucun calcul bloqué | OK |
| hors connexion : aucune erreur JavaScript | OK |
