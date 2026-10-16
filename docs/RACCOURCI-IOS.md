# Raccourci iOS « Fiches Packs »

Objectif : à partir de captures d'écran des fiches de régulation (MccMissionSG), partagées depuis Photos, extraire le texte avec la reconnaissance d'Apple **sur l'iPhone**, le copier, puis créer tous les arrêts d'un coup dans Packs avec « 📋 Coller les fiches ». Rien n'est envoyé hors de l'iPhone par le raccourci.

## Pourquoi un mode d'emploi et pas un fichier à installer

Depuis iOS 15, un raccourci partagé sous forme de fichier doit être signé par Apple (signature faite par l'appareil, ou via un lien iCloud). Je ne peux pas produire ce fichier signé depuis le dépôt. Le raccourci se crée en 2 minutes avec les étapes ci-dessous ; une fois créé, tu peux le partager à un collègue par un lien iCloud (Raccourcis → appui long → Partager → Copier le lien iCloud).

## Création (iOS 16 ou plus)

1. Ouvrir l'app **Raccourcis** → **＋** (en haut à droite) → nommer le raccourci **Fiches Packs**.
2. Toucher **ⓘ** (en bas) → activer **Afficher dans la feuille de partage** → dans « Types de partage », ne garder que **Images**.
3. Ajouter l'action **Répéter avec chaque élément** ; elle porte sur **Entrée du raccourci**.
4. Dans la boucle, ajouter **Extraire le texte de l'image** (entrée : **Élément de répétition**).
5. Toujours dans la boucle, ajouter **Texte** et y mettre :
   - la variable **Texte de l'image** ;
   - puis, sur une nouvelle ligne, `-----` (cinq tirets).
6. Après **Fin de la répétition**, ajouter **Combiner le texte** (entrée : **Résultats de la répétition**, séparateur : **Nouvelles lignes**).
7. Ajouter **Copier dans le presse-papiers** (entrée : **Texte combiné**).
8. Facultatif : ajouter **Ouvrir les URL** avec `https://milka9745.github.io/packs-sos/#coller` (Packs s'ouvre directement sur la tournée).

## Utilisation en garde

1. Dans **Photos**, sélectionner une ou plusieurs captures de fiches → **Partager** → **Fiches Packs**.
2. Dans Packs (écran principal ou Tournée) → **📋 Coller les fiches** → autoriser le collage si iOS le demande.
3. Packs crée un arrêt par fiche, refuse les doublons (« Déjà dans la tournée ») et signale ce qui ne colle pas (code postal, téléphone, âge et date de naissance).

## Android

Pas de raccourci nécessaire : ouvrir la capture, sélectionner le texte (Google Lens ou « Sélectionner le texte » de la galerie), **Copier**, puis **📋 Coller les fiches** dans Packs. Plusieurs fiches : les séparer par une ligne `-----`. On peut aussi importer directement les captures avec **📷** : la lecture se fait dans le téléphone (Tesseract), zone par zone.

## Confidentialité

- Le raccourci n'utilise que des actions locales (reconnaissance de texte d'Apple sur l'appareil, presse-papiers).
- Packs lit les captures dans le téléphone ; seule l'adresse part au géocodeur (Base Adresse Nationale) et seules des coordonnées partent au calcul d'itinéraire.
- Effacer les captures de la photothèque après la garde.
