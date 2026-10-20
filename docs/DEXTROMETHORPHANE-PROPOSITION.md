# Dextrométhorphane — proposition de lignes d'ordonnance (20/10/2026)

**Statut : proposition, non intégrée dans l'application.** Vérifiée le 20/10/2026 sur la base de données publique des médicaments (BDPM), Légifrance, ANSM, HAS, SPLF, Afssaps/SFP, CRAT. Rien n'est inventé ; les points non trouvés sont listés.

## Ce qui existe aujourd'hui dans l'application
Une seule ligne optionnelle (`DXM_A`, fiche Bronchite aiguë et fiches de toux) : « DEXTROMÉTHORPHANE sirop ou comprimé : 15 à 30 mg par prise … 120 mg par jour au maximum, 5 jours au maximum », bloquée sous 15 ans. Elle mêle deux formes sur une ligne (règle du 18/10 : une forme par ligne) et ne nomme pas de spécialité.

## Cadre réglementaire (vérifié)
- Liste I, **prescription médicale obligatoire quel que soit l'âge** depuis l'arrêté du 12 juillet 2017 (JORF 16/07/2017) ; vente en ligne interdite ; renouvellement interdit sauf mention sur l'ordonnance.
- ANSM 2014 : usage détourné par les adolescents et jeunes adultes — vigilance devant toute demande suspecte, une seule boîte, pas de renouvellement, déclaration au CEIP en cas d'abus. Aucune décision ANSM plus récente trouvée (2018-2026).
- Enfant : Afssaps / SFP 2010, **jamais d'antitussif avant 2 ans** ; aucune recommandation française entre 2 et 15 ans hors RCP ; CHEST 2017 : pas de dextrométhorphane avant 2 ans, miel possible de 1 à 18 ans, preuves d'efficacité faibles à tout âge.
- HAS (avis TUSSIDANE 2018) : SMR modéré ; rechercher la cause avant tout antitussif ; seules les toux non productives gênantes en justifient un.
- CRAT (01/04/2026) : grossesse possible à posologie usuelle quelques jours ; allaitement envisageable à la plus faible dose — **mais le RCP contre-indique l'allaitement** (divergence à trancher, écrite au mémo).

## Produits disponibles (BDPM, 20/10/2026)
| Forme | Spécialité | CIS | RCP | Remboursement | Âge RCP |
|---|---|---|---|---|---|
| Sirop | TUSSIDANE 1,5 mg/ml (1 cuillère-mesure 5 ml = 7,5 mg) ; variante sans sucre CIS 66819541 ; générique BIOGARAN CIS 65799705 | 60940109 | 06/06/2024 | 30 % | > 30 mois |
| Comprimé | TUSSIDANE 30 mg sécable, boîte de 12 | 60133432 | 12/01/2024 | 30 % | > 15 ans |
| Comprimé (alternative) | PULMODEXANE 30 mg, boîte de 12 | 66078868 | 29/06/2020 | 30 % | ≥ 15 ans |
| Gélule | aucune : TUXIUM 30 mg et ERGIX 20 mg ne sont plus commercialisés (absents de la BDPM) | — | — | — | — |
Aucune rupture signalée (liste ANSM 2021-2026).

## Proposition (adulte et adolescent de plus de 15 ans — fiches de toux de l'adulte)
Deux lignes en choix exclusif (`grp:"dxm"`), **décochées par défaut** (`opt:true`), bloquées sous 15 ans (`{agemin:15|dextrométhorphane}`), notes médecin entre parenthèses jamais imprimées :

1. **TUSSIDANE 30 mg comprimé pelliculé sécable (dextrométhorphane)** : ½ à 1 comprimé par prise, 3 à 4 fois par jour aux heures où la toux gêne, en espaçant les prises d'au moins 4 heures, sans dépasser 4 comprimés par jour, pendant 5 jours au maximum ; 1 boîte de 12. Pas d'alcool ; somnolence possible au volant.
   (RCP 12/01/2024 : à partir de 15 ans ; contre-indiqué si asthme, insuffisance respiratoire, IMAO irréversible, cinacalcet, allaitement ; demi-dose initiale si sujet âgé ou insuffisance hépatique ; prudence sédatifs, opioïdes, benzodiazépines, ISRS, linézolide, inhibiteurs du CYP2D6 ; toux grasse : à respecter. ANSM 2014 : une boîte, pas de renouvellement, vigilance chez l'adolescent et le jeune adulte. CRAT 04/2026 : grossesse possible quelques jours. Liste I.)

2. **TUSSIDANE 1,5 mg/ml sirop (dextrométhorphane)** : 2 à 4 cuillères-mesure de 5 ml par prise, 3 à 4 fois par jour aux heures où la toux gêne, en espaçant les prises d'au moins 4 heures, sans dépasser 120 mg par jour (16 cuillères-mesure), pendant 5 jours au maximum ; 1 flacon de 125 ml. Pas d'alcool ; somnolence possible au volant.
   (RCP 06/06/2024 : mêmes contre-indications et précautions ; contient du saccharose, variante sans sucre disponible ; 15 à 30 mg par prise ; le RCP écrit aussi « jusqu'à 6 cuillères à soupe » = 135 mg, incohérent avec le maximum de 120 mg : 120 mg retenu.)

## Enfant de 30 mois à 15 ans : proposition de **ne pas ajouter de ligne**
Le RCP du sirop autorise 1 mg/kg/j dès 30 mois, mais aucune recommandation française ne soutient l'antitussif central chez l'enfant, les preuves sont faibles et le mésusage est documenté chez l'adolescent ; les fiches enfant gardent les mesures non médicamenteuses (lavage de nez, miel après 1 an, hydratation). À confirmer par le médecin ; sinon, ligne enfant possible à partir du RCP (sirop, 1 mg/kg/j en 4 prises, jamais avant 30 mois).

## Décisions attendues avant intégration
1. Valider les deux lignes adulte ci-dessus (ou choisir PULMODEXANE pour le comprimé).
2. Confirmer l'absence de ligne enfant.
3. Allaitement : suivre le RCP (contre-indiqué) ou le CRAT (envisageable) — proposition : RCP, avec l'avis du CRAT au mémo.
4. Fiches concernées (« modifiée — à relire » après intégration) : toutes celles qui utilisent `DXM_A`.
