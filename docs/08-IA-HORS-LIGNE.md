# IA hors ligne sur iPhone — ce qui est faisable (étude du 15/10/2026)

Cahier de corrections, point 5. Avis franc, sources en fin de document. Rien n'a été testé sur un iPhone réel : à confirmer sur l'appareil du Docteur DEIE.

## En bref
- **Dans Packs tel qu'il est (page web installée sur l'écran d'accueil)** : pas d'IA générative hors ligne fiable aujourd'hui.
- **Avec une vraie application iPhone (native)** : faisable avec le modèle d'Apple sur l'appareil, mais limité (textes courts) et c'est un projet à part.
- **Faisable tout de suite, sans IA et hors ligne** : la relecture « manques » du § 7 par règles, à partir des fiches. C'est ce que je recommande en premier.

## 1. Le modèle d'Apple (Apple Intelligence, « Foundation Models »)
- **Accessible seulement depuis une app native (Swift)**. Je n'ai trouvé aucun accès depuis Safari ni depuis une page web installée. Packs ne peut donc pas l'utiliser sans devenir une app.
- Modèle d'environ 3 milliards de paramètres. **Fenêtre de 4 096 jetons, entrée et sortie comprises** : assez pour ranger une dictée courte ou reformuler un paragraphe ; trop court pour relire un compte rendu complet avec les consignes et la fiche.
- Français pris en charge par Apple Intelligence depuis iOS 18.4. Entrée **texte seul** sous iOS 26 ; une version avec vision est annoncée pour iOS 27, non vérifiée.
- iPhone 15 Pro ou plus récent, 7 Go libres.
- Les conditions d'Apple interdisent les sorties dangereuses et les décisions **sans supervision humaine** en médecine. Notre usage (proposition relue et validée par le médecin) paraît compatible, mais c'est à faire lire, comme la question du dispositif médical.
- Prix à payer : application native (compte développeur Apple, TestFlight ou App Store), maintien de deux versions, qualité médicale d'un petit modèle à évaluer sur de vraies dictées.

## 2. Un modèle dans Safari (WebGPU, WebLLM)
- WebGPU est livré dans Safari 26 sur iOS. Je n'ai pas trouvé de confirmation qu'il fonctionne dans une page web installée sur l'écran d'accueil.
- Le plus petit modèle utilisable (Llama 3.2 1B, 4 bits) pèse environ 700 Mo et occupe près de 900 Mo de mémoire graphique. **Safari sur iPhone est la plateforme la plus limitée en mémoire, avec des plantages documentés** (WebLLM, bug WebKit 311598).
- Aucune mesure publiée de vitesse sur iPhone dans Safari.
- Un modèle de 1 milliard de paramètres invente trop pour un compte rendu médical en français. Un modèle de 3 à 4 milliards ferait 2 à 3 Go et risquerait de faire planter Safari en pleine garde.
- **Verdict : non pour la garde.** Au mieux une expérience de laboratoire.

## 3. Applications de modèles locaux existantes
Private LLM, PocketPal, MLC Chat font tourner des modèles de 2 à 8 milliards de paramètres sur iPhone récent (environ 10 à 20 jetons par seconde rapportés, sources peu fiables). Elles prouvent que c'est possible en natif, mais elles sont séparées de Packs : copier-coller, sans anonymisation ni garde-fous.

## 4. Ce qui fonctionne déjà hors ligne dans Packs
- **Dictée du clavier** : Apple traite la dictée sur l'appareil « dans de nombreuses langues », sans confirmation officielle pour le français. **Test simple : mode Avion, puis dicter dans Packs.**
- **« Répartir dans les rubriques »** : rangement local de la dictée (règles), sans IA.
- **Lecture de documents (OCR)** : Tesseract tourne dans le téléphone ; c'est lui qui trouve et masque l'identité avant l'envoi d'un document.
- Pack, doses, documents, journal : hors ligne, comme avant.

## 5. Ce que je recommande
1. **Relecture hors ligne par règles (§ 7, « signale les manques »)**, sans IA : à partir des listes de vérification et des points de traçabilité de chaque fiche, Packs signale avant validation les signes de gravité non notés, les consignes de reconsultation absentes, le refus non tracé, le choix hors recommandation non justifié. Fiable, gratuit, instantané, sans aucun envoi. C'est la partie du § 7 qui protège le plus.
2. **Tester la dictée en mode Avion** sur votre iPhone.
3. **IA générative hors ligne** : seulement en application native avec le modèle d'Apple, sur iPhone 15 Pro ou plus récent, en projet séparé, d'abord en prototype évalué sur des dictées fictives. Pas dans Packs web.
4. En ligne, l'IA actuelle reste coupée hors connexion, sans file d'attente.

## Sources (consultées le 15/10/2026)
- Apple, Foundation Models framework : https://developer.apple.com/foundation-models-framework/
- Apple, rapport technique des modèles 2025 : https://machinelearning.apple.com/research/apple-foundation-models-tech-report-2025
- Apple, TN3193, fenêtre de contexte du modèle sur l'appareil : https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window
- Apple, conditions d'usage du framework : https://developer.apple.com/apple-intelligence/acceptable-use-requirements-for-the-foundation-models-framework/
- Apple, WWDC26 « What's new in the Foundation Models framework » : https://developer.apple.com/videos/play/wwdc2026/241/
- Apple, appareils compatibles Apple Intelligence : https://support.apple.com/121115
- WebKit, Safari 26.0 (WebGPU) : https://webkit.org/blog/17333/webkit-features-in-safari-26-0/
- WebKit, politique de stockage : https://webkit.org/blog/14403/updates-to-storage-policy/
- Bug WebKit 311598 (mémoire, inférence) : https://bugs.webkit.org/show_bug.cgi?id=311598
- « Llamas on the Web » (mai 2026) : https://www.alphaxiv.org/abs/2605.20706
- Taille de Llama 3.2 1B dans le navigateur : https://pinggy.io/blog/run_llm_in_browser_webgpu/
- Apple, dictée et confidentialité : https://www.apple.com/legal/privacy/data/en/ask-siri-dictation/
- Private LLM (App Store) : https://apps.apple.com/app/id6448106860
