# -*- coding: utf-8 -*-
"""Index compact de la Base de données publique des médicaments (ANSM) pour la fiche « Renouvellement d'ordonnance » (11/11/2026).

Usage : python -I tools/build_bdpm.py <dossier des fichiers BDPM>
Fichiers lus (https://base-donnees-publique.medicaments.gouv.fr/telechargement, encodage ISO-8859-1) :
  CIS_bdpm.txt (spécialités), CIS_COMPO_bdpm.txt (substances), CIS_CPD_bdpm.txt (conditions de prescription et de délivrance).
Sortie : bdpm/specialites.txt (UTF-8, une ligne par spécialité : CIS|nom|DCI|règles|durée maximale en jours) et bdpm/LISEZ-MOI.txt.
Retenu : autorisation active et commercialisée ; exclus : homéopathie (« Enreg homéo »), importations parallèles (doublons de marques).
Règles (lettres) : S = ordonnance sécurisée (stupéfiants et assimilés : « prescription en toutes lettres sur ordonnance sécurisée »,
« prescription sur ordonnance sécurisée », « stupéfiants ») ; H = hospitalier (réservé à l'usage hospitalier, prescription hospitalière,
pharmacie à usage intérieur, structure d'assistance médicale mobile, usage professionnel) ; R = prescription ou renouvellement réservé
aux spécialistes (non prescriptible en ville) ; I = prescription initiale hospitalière ou spécialisée (renouvellement possible par tout
médecin dans la durée de validité) ; durée = « prescription limitée à N semaines / mois / jours » convertie en jours (0 = aucune)."""
import sys, os, re, collections, datetime
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv)<2: sys.exit("dossier des fichiers BDPM attendu")
D=sys.argv[1]
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"bdpm")
def rows(name):
    with open(os.path.join(D,name),encoding="latin-1",newline="") as f:
        for l in f:
            l=l.rstrip("\r\n")
            if l: yield l.split("\t")
SALT_PRE=r"(?:CHLORHYDRATE|DICHLORHYDRATE|TRICHLORHYDRATE|BROMHYDRATE|TARTRATE|BITARTRATE|HÉMITARTRATE|SULFATE|HÉMISULFATE|PHOSPHATE|DIPHOSPHATE|MALÉATE|MALEATE|FUMARATE|HÉMIFUMARATE|BÉSILATE|BESILATE|MÉSILATE|MESILATE|TOSILATE|CITRATE|ACÉTATE|ACETATE|SUCCINATE|HÉMISUCCINATE|BROMURE|CHLORURE|NITRATE|LACTATE|GLUCONATE|OXALATE|PAMOATE|PALMITATE|VALÉRATE|PROPIONATE|DIPROPIONATE|BUTYRATE|BENZOATE|SALICYLATE|STÉARATE|CARBONATE|BICARBONATE|HYDROGÉNOTARTRATE|HYDROGÉNOFUMARATE|DIHYDROGÉNOPHOSPHATE|EMBONATE|ÉNANTATE|DÉCANOATE|CYPIONATE|UNDÉCANOATE|TRIFLUOROACÉTATE|MÉSYLATE|TRIHYDRATE|NAPSYLATE|THÉOCLATE|ÉTABONATE|PIVALATE|ORTHOPHOSPHATE|SODIUM|POTASSIUM|CALCIUM|MAGNÉSIUM|ZINC)"
SALT_SUF=r"(?:SODIQUE|DISODIQUE|TRISODIQUE|POTASSIQUE|DIPOTASSIQUE|CALCIQUE|MAGNÉSIEN|MAGNESIEN|MAGNÉSIQUE|BASE|ANHYDRE|MONOHYDRATÉE?|HÉMIHYDRATÉE?|DIHYDRATÉE?|TRIHYDRATÉE?|SESQUIHYDRATÉE?|HYDRATÉE?|MICRONISÉE?|LYOPHILISÉE?|CRISTALLISÉE?|MICRONISÉ|ACIDE|RACÉMIQUE|DEXTROGYRE|LÉVOGYRE|MÉSILATE|MÉSYLATE)"
def clean_dci(s):
    t=s.strip()
    t=re.sub(r"\s*\((?:[^()]*\b(?:DE|D')\s*)\)","",t)  # « MORPHINE (SULFATE DE) », « OXYCODONE (CHLORHYDRATE D') »
    t=re.sub(r"\s*\([^()]*\)","",t)
    for _ in range(3):
        t2=re.sub(r"^"+SALT_PRE+r"(?:\s+(?:ACIDE|MONO|DI|TRI|HYDROGÉNO)\w*)?\s+(?:DE\s+|D')","",t)
        t2=re.sub(r"\s+"+SALT_SUF+r"$","",t2)
        t2=re.sub(r"^(?:DL-|L-|D-)(?=LYSINE)","",t2)
        if t2==t: break
        t=t2
    t=re.sub(r"\s{2,}"," ",t).strip(" ,;")
    return t
def group_dci(comp):
    """comp : lignes COMPO d'un CIS → DCI par numéro de liaison, FT (fraction thérapeutique) prioritaire sur SA."""
    by=collections.OrderedDict()
    for c in comp:
        if len(c)<7: continue
        liaison=c[7] if len(c)>7 else "1"
        g=by.setdefault(liaison,{"FT":[],"SA":[]})
        g[c[6]].append(c[3])
    out=[]
    for g in by.values():
        names=g["FT"] or g["SA"]
        for n in names:
            d=clean_dci(n)
            if d and d.lower() not in [x.lower() for x in out]: out.append(d)
    return out
def flags_of(cpd):
    f=set(); mx=0
    for c in cpd:
        u=c.lower()
        if "ordonnance sécurisée" in u or "stupéfiant" in u: f.add("S")
        if ("réservé à l'usage hospitalier" in u or re.search(r"^prescription hospitali",u) or "pharmacies à usage intérieur" in u
            or "assistance médicale mobile" in u or "réservé à l'usage professionnel" in u or "usage professionnel selon" in u): f.add("H")
        if re.search(r"prescription initiale (?:hospitali|réservée|annuelle|semestrielle|trimestrielle)",u) or "prescription initiale" in u: f.add("I")
        if re.search(r"prescription réservée aux (?:spécialistes|médecins)",u) or re.search(r"renouvellement de la prescription réservé",u): f.add("R")
        m=re.search(r"prescription limitée à (\d+)\s*(semaine|mois|jour)",u)
        if m:
            n=int(m.group(1)); d=n*7 if m.group(2).startswith("semaine") else n*30 if m.group(2)=="mois" else n
            mx=d if not mx else min(mx,d)
    # une prescription initiale réservée n'est pas « réservée » pour le renouvellement : I prime sur R quand le renouvellement n'est pas restreint
    if "I" in f and "R" in f and not any("renouvellement de la prescription réservé" in c.lower() for c in cpd) and any("renouvellement non restreint" in c.lower() or "prescription initiale" in c.lower() for c in cpd):
        f.discard("R")
    return "".join(sorted(f)),mx
def main():
    cis=list(rows("CIS_bdpm.txt"))
    compo=collections.defaultdict(list)
    for r in rows("CIS_COMPO_bdpm.txt"): compo[r[0]].append(r)
    cpd=collections.defaultdict(list)
    for r in rows("CIS_CPD_bdpm.txt"):
        if len(r)>=2: cpd[r[0]].append(r[1])
    out=[]; nS=nH=nR=nI=0; skipped=collections.Counter()
    for r in cis:
        if len(r)<7: continue
        code,nom,statut,proc,etat=r[0],r[1].strip(),r[4],r[5],r[6]
        if statut!="Autorisation active": skipped["autorisation non active"]+=1; continue
        if etat!="Commercialisée": skipped["non commercialisée"]+=1; continue
        if "homéo" in proc.lower(): skipped["homéopathie"]+=1; continue
        if "importation parallèle" in proc.lower(): skipped["importation parallèle"]+=1; continue
        d=group_dci(compo.get(code,[]))
        if len(d)>3: d=d[:3]+["…"]
        dci=" + ".join(x.lower() for x in d)
        f,mx=flags_of(cpd.get(code,[]))
        nS+="S" in f; nH+="H" in f; nR+="R" in f; nI+="I" in f
        nom=nom.replace("|","/").replace("\t"," ")
        out.append((nom,code,dci,f,mx))
    out.sort(key=lambda x:(x[0].lower(),x[1]))
    os.makedirs(OUT,exist_ok=True)
    today=datetime.date.today().strftime("%d/%m/%Y")
    head="# Packs SOS — index BDPM (Base de données publique des médicaments, ANSM), généré le "+today+" par tools/build_bdpm.py ; CIS|nom|DCI|règles (S sécurisée, H hospitalier, R spécialistes, I initiale hospitalière ou spécialisée)|durée maximale en jours\n"
    body="".join(f"{c}|{n}|{d}|{f}|{mx}\n" for n,c,d,f,mx in out)
    p=os.path.join(OUT,"specialites.txt")
    with open(p,"w",encoding="utf-8",newline="\n") as fh: fh.write(head+body)
    size=os.path.getsize(p)
    lisez=f"""Packs SOS — dossier bdpm/ (11/11/2026)

specialites.txt : index compact de la Base de données publique des médicaments (ANSM, https://base-donnees-publique.medicaments.gouv.fr),
généré le {today} par tools/build_bdpm.py à partir de CIS_bdpm.txt, CIS_COMPO_bdpm.txt et CIS_CPD_bdpm.txt.
Il sert à la fiche « Renouvellement d'ordonnance » : recherche hors ligne par nom commercial ou DCI, choix de la présentation (dosage, forme),
repérage des médicaments à ordonnance sécurisée (stupéfiants et assimilés), réservés à l'hôpital ou aux spécialistes, et des durées de prescription limitées.
Une ligne par spécialité : code CIS | nom de la spécialité (dosage, forme) | DCI (substances actives, sels retirés) | règles | durée maximale (jours, 0 = aucune).
Règles : S = prescription sur ordonnance sécurisée ; H = réservé à l'hôpital ou prescription hospitalière ; R = prescription (ou renouvellement) réservée aux spécialistes ;
I = prescription initiale hospitalière ou spécialisée (renouvellement possible par tout médecin dans la durée de validité).
Retenues : {len(out)} spécialités (autorisation active, commercialisées) ; exclues : homéopathie ({skipped['homéopathie']}), importations parallèles ({skipped['importation parallèle']}),
autorisations non actives ({skipped['autorisation non active']}), non commercialisées ({skipped['non commercialisée']}).
Repères : {nS} spécialités S, {nH} H, {nR} R, {nI} I. Taille : {size} octets ({size/1024/1024:.2f} Mo).
Le fichier est mis en cache par le service worker (sw.js) : il reste disponible hors connexion. Mise à jour : télécharger les trois fichiers, puis
python -I tools/build_bdpm.py <dossier>. Données publiques ANSM (licence de réutilisation de la BDPM) ; aucune donnée de patient.
"""
    with open(os.path.join(OUT,"LISEZ-MOI.txt"),"w",encoding="utf-8",newline="\n") as fh: fh.write(lisez)
    print(f"{len(out)} spécialités → {p} ({size} octets, {size/1024/1024:.2f} Mo) ; S {nS}, H {nH}, R {nR}, I {nI} ; exclues : {dict(skipped)}")
    # contrôles
    for probe in ["DOLIPRANE 1000 mg, comprimé","SKENAN L.P. 10","TRAMADOL ARROW 50","STILNOX","LYRICA 75","AMLOR 5","LEVOTHYROX 50","KARDEGIC 75","AUGMENTIN 1 g/125 mg ADULTES","SYMBICORT RAPIHALER","RITALINE 10","METHADONE","LANTUS 100","COVERSYL 5","INEXIUM 20","ELIQUIS 5","DAFALGAN CODEINE","FREESTYLE","INSULATARD","TAHOR 10"]:
        hit=[x for x in out if x[0].startswith(probe)]
        print("  ",probe,"→",(hit[0][0][:60],hit[0][2],hit[0][3],hit[0][4]) if hit else "ABSENT")
if __name__=="__main__": main()
