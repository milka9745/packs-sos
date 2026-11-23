# -*- coding: utf-8 -*-
# Correctif du 23/11/2026 — doses de paracétamol et d'amoxicilline chez l'enfant (erreur signalée en garde).
# Usage : python tools/correctif_doses_enfant.py index.html [test/index.html ...]
# Chaque remplacement doit s'appliquer exactement une fois, sinon le script s'arrête sans écrire.
#
# 1. paracetamol(p) — sachets DOLIPRANE aux tranches du RCP : 200 mg réservé à 11-16 kg à 1 sachet toutes les 6 h (RCP 200 mg,
#    CIS 68794211 : 11 à 25 kg ; 17-20 kg toutes les 4 h, 6 par jour), 300 mg à 16-24 kg toutes les 6 h et 25-30 kg toutes les 4 h,
#    6 par jour (RCP 300 mg, CIS 69002078 : 16 à 48 kg). L'application donnait 200 mg de 13 à 20 kg et 300 mg de 20 à 27 kg
#    toutes les 6 h, 4 par jour : 40 à 48 mg/kg/j de 16 à 20 kg et de 25 à 27 kg au lieu de 60.
# 2. paracetamolSuppo(p) — sous 4 kg la branche « p<12 » donnait un suppositoire de 150 mg (50 mg/kg à 3 kg) ; à 4 kg un
#    (la demi-dose « ½ suppositoire » est reconnue par la clé de dédoublonnage et la garde d'ajout, sinon « DOLIPRANE en double »)
#    suppositoire entier de 100 mg (25 mg/kg). RCP : 100 mg sécable, ½ suppositoire de 3 à 4 kg, 1 suppositoire de 5 à 8 kg
#    (CIS 66057393) ; 150 mg 8-12 kg ; 200 mg 12-16 kg ; 300 mg 15-24 kg ; 1 g adulte et enfant de plus de 50 kg.
# 3. Érythème migrant (lot 1) — « CLAMOXYL 1 g comprimé : 1 comprimé 3 fois par jour » était la seule ligne, y compris pour
#    « enfant de moins de 8 ans » ; chez l'enfant la ligne disparaissait (ctxEdit() retire toute ligne citant « enceinte » ou
#    « grossesse » avant 12 ans et chez l'homme) : aucune amoxicilline proposée. La note ne cite plus la grossesse (HAS 2025 :
#    doxycycline en 1re intention, grossesse comprise ; la note ne peut citer ni « grossesse » ni « enceinte »). Ligne enfant au poids :
#    50 mg/kg/j en 3 prises, 1 g par prise au plus (HAS 02/2025 : 50 mg/kg/j sans dépasser 4 g/j en 3 prises toutes les 8 h,
#    14 jours ; RCP CLAMOXYL : 25 à 50 mg/kg/j en trois prises).
# 4. Morsure de tique (bloc) — amoxicilline enfant en 3 prises (HAS 2025, RCP) au lieu de « matin et soir » ; 1 g par prise au plus.
# 5. Base médicaments — ligne enfant AMOXICILLINE : 80 mg/kg/j réservé à l'otite, la sinusite et la pneumopathie, angine
#    50 mg/kg/j, pneumopathie 5 jours (HAS 2024) et non 10, 1,5 g par prise au plus (3 g/j), « pendant N jours » pour que la
#    durée de la ligne adulte soit reprise.
# 6. Mémos « Fièvre — enfant » et « Grippe — enfant » : tranches des sachets et sources corrigées.
import sys, io

REPL=[
 ("sachet 200 mg 13-16 kg",
  'if(p<20) return "DOLIPRANE 200 mg poudre en sachet : 1 sachet toutes les 6 heures si fièvre ou douleur, sans dépasser 4 prises par jour, pendant 5 jours.";',
  'if(p<16) return "DOLIPRANE 200 mg poudre en sachet : 1 sachet toutes les 6 heures si fièvre ou douleur, sans dépasser 4 prises par jour, pendant 5 jours."; /* RCP DOLIPRANE 200 mg : 11 à 16 kg, 1 sachet toutes les 6 heures (23/11/2026) */'),
 ("sachet 300 mg 16-24 kg puis 25-27 kg",
  'if(p<27) return "DOLIPRANE 300 mg poudre en sachet : 1 sachet toutes les 6 heures si fièvre ou douleur, sans dépasser 4 prises par jour, pendant 5 jours.";',
  'if(p<25) return "DOLIPRANE 300 mg poudre en sachet : 1 sachet toutes les 6 heures si fièvre ou douleur, sans dépasser 4 prises par jour, pendant 5 jours."; /* RCP DOLIPRANE 300 mg : 16 à 24 kg, 1 sachet toutes les 6 heures */\n'
  '  if(p<27) return "DOLIPRANE 300 mg poudre en sachet : 1 sachet toutes les 4 à 6 heures si fièvre ou douleur, sans dépasser 6 sachets par jour, pendant 5 jours."; /* RCP DOLIPRANE 300 mg : 25 à 30 kg, 1 sachet toutes les 4 heures au plus, 6 par jour ; comprimé 500 mg à partir de 27 kg */'),
 ("suppositoire au poids (RCP)",
  'let d=null; if(p>=4&&p<8) d="100 mg"; else if(p<12) d="150 mg"; else if(p<16) d="200 mg"; else if(p<24) d="300 mg"; else if(p>=50) d="1 g"; else return null;',
  'let d=null; if(p<3) return null; else if(p<5) d="½"; else if(p<8) d="100 mg"; else if(p<12) d="150 mg"; else if(p<16) d="200 mg"; else if(p<24) d="300 mg"; else if(p>=50) d="1 g"; else return null; /* 23/11/2026 : tranches du RCP (100 mg sécable : ½ suppositoire de 3 à 4 kg, 1 de 5 à 8 kg ; 150 mg 8-12 ; 200 mg 12-16 ; 300 mg 15-24 ; 1 g > 50 kg) — sous 4 kg l\'ancienne branche donnait 150 mg */\n'
  '  if(d==="½") return "DOLIPRANE 100 mg suppositoire sécable : ½ suppositoire toutes les 6 heures, en remplacement de la forme orale si la prise par la bouche est impossible (vomissements, refus), sans dépasser 4 demi-suppositoires par jour ni cumuler avec la forme orale.";'),
 ("érythème migrant lot 1 : amoxicilline enfant au poids",
  '{t:"CLAMOXYL 1 g comprimé : 1 comprimé 3 fois par jour pendant 14 jours (femme enceinte, enfant de moins de 8 ans).",grp:"atb",alt:[',
  '{t:"{agelt:15|CLAMOXYL 500 mg/5 ml poudre pour suspension buvable : {ml:0.17|10} 3 fois par jour pendant 14 jours|CLAMOXYL 1 g comprimé : 1 comprimé 3 fois par jour pendant 14 jours} (alternative à la doxycycline, 2e intention HAS 2025 ; enfant : amoxicilline 50 mg/kg/j en 3 prises, 1 g par prise au plus, HAS 2025 et RCP ; ligne corrigée le 23/11/2026 : un comprimé de 1 g était proposé quel que soit le poids, et l\'ancienne note faisait disparaître la ligne chez l\'enfant).",grp:"atb",alt:['),
 ("morsure de tique : amoxicilline enfant en 3 prises",
  '{agelt:15|CLAMOXYL 500 mg/5 ml poudre pour suspension buvable : {ml:0.25|20} matin et soir pendant 14 jours|CLAMOXYL 1 g comprimé : 1 comprimé 3 fois par jour pendant 14 jours} (érythème migrant, 2e intention).',
  '{agelt:15|CLAMOXYL 500 mg/5 ml poudre pour suspension buvable : {ml:0.17|10} 3 fois par jour pendant 14 jours|CLAMOXYL 1 g comprimé : 1 comprimé 3 fois par jour pendant 14 jours} (érythème migrant, 2e intention ; enfant : 50 mg/kg/j en 3 prises toutes les 8 heures, 1 g par prise au plus, HAS 02/2025 et RCP).'),
 ("mémo morsure de tique",
  '2e intention amoxicilline 50 mg/kg/j (max 4 g/j) 14 jours',
  '2e intention amoxicilline 50 mg/kg/j en 3 prises toutes les 8 heures (max 4 g/j) 14 jours (ligne enfant corrigée le 23/11/2026 : elle donnait 2 prises)'),
 ("base médicaments : amoxicilline enfant",
  'AMOXICILLINE 500 mg/5 ml poudre pour suspension buvable : {ml:0.4|10} matin et soir (80 mg/kg/j), durée selon l\'indication (angine 6 jours ; otite 5 jours, 10 jours avant 2 ans ; pneumopathie 10 jours).',
  'AMOXICILLINE 500 mg/5 ml poudre pour suspension buvable : {ml:0.4|15} matin et soir pendant 5 jours (indiqué : 80 mg/kg/j en 2 prises pour otite, sinusite et pneumopathie, 1,5 g par prise au plus soit 3 g par jour ; angine 50 mg/kg/j soit 0,25 ml/kg par prise ; durées HAS 2021-2025 : angine 6 jours, otite 5 jours ou 10 jours avant 2 ans, sinusite 10 jours, pneumopathie 5 jours ; érythème migrant 50 mg/kg/j en 3 prises 14 jours).'),
 ("mémo fièvre enfant : tranches des sachets",
  'puis sachet 200 mg (13 à 20 kg), 300 mg (20 à 27 kg), comprimé 500 mg (27 à 40 kg : 4 par jour ; 41 à 50 kg : 6 par jour), suppositoire au poids en remplacement (RCP DOLIPRANE 2,4 % du 05/10/2026)',
  'puis sachet 200 mg (13 à 16 kg, 4 par jour ; RCP : 11 à 16 kg), 300 mg (16 à 24 kg, 4 par jour ; 25 à 27 kg toutes les 4 heures au plus, 6 par jour ; RCP : 16 à 48 kg), comprimé 500 mg (27 à 40 kg : 4 par jour ; 41 à 50 kg : 6 par jour), suppositoire au poids en remplacement (100 mg sécable : ½ de 3 à 4 kg, 1 de 5 à 8 kg ; 150 mg 8 à 12 kg ; 200 mg 12 à 16 kg ; 300 mg 15 à 24 kg) — tranches corrigées le 23/11/2026 après une erreur signalée en garde (200 mg donné jusqu\'à 20 kg et 300 mg jusqu\'à 27 kg à 4 prises : 40 à 48 mg/kg/j ; suppositoire de 150 mg sous 4 kg) (RCP DOLIPRANE 2,4 % du 05/10/2026, RCP sachets 200 mg CIS 68794211 et 300 mg CIS 69002078, RCP suppositoires 100 à 300 mg, lus le 23/11/2026)'),
 ("mémo grippe enfant : sachets",
  'seringue graduée en kg jusqu\'à 13 kg, puis sachets au poids)',
  'seringue graduée en kg jusqu\'à 13 kg, puis sachets 200 mg de 13 à 16 kg et 300 mg de 16 à 27 kg, comprimé 500 mg à partir de 27 kg ; tranches corrigées le 23/11/2026)'),
 ("suppositoire : la demi-dose n'est plus prise pour un doublon de la ligne orale (clé de dédoublonnage et garde d'ajout)",
  "/suppositoire : 1 suppositoire toutes les 6 heures, en remplacement/",
  "/suppositoire(?: sécable)? : (?:1|½) suppositoire toutes les 6 heures, en remplacement/", 2),
]

def apply(path):
    raw=open(path,"rb").read(); nl="\r\n" if b"\r\n" in raw[:20000] else "\n"
    s=raw.decode("utf-8")
    for item in REPL:
        lab,a,b=item[0],item[1],item[2]; want=item[3] if len(item)>3 else 1
        a2=a.replace("\n",nl); b2=b.replace("\n",nl)
        n=s.count(a2)
        if n!=want: sys.exit(f"ÉCHEC {path} : « {lab} » trouvé {n} fois (attendu {want}) — rien n'est écrit")
        s=s.replace(a2,b2)
    open(path,"wb").write(s.encode("utf-8"))
    print(f"{path} : {len(REPL)} remplacements appliqués")

if __name__=="__main__":
    for p in sys.argv[1:]: apply(p)
