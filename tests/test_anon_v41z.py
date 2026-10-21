# v41z (21/10/2026, demande globale I-II) — anonymisation : corpus de 100 dictées fictives piégées, fuzzing 1 000 variantes (zéro fuite),
# taux de faux positifs, chronométrage (20 dictées ≈ 2 000 caractères), doutes à confirmer, mode strict, listes personnelles, worker.
# Identités entièrement fictives. Aucun envoi : seules les fonctions locales sont appelées.
import asyncio, os, random, re, subprocess, sys, time, json, unicodedata, statistics
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8786
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page):
    await page.add_init_script("try{localStorage.setItem('sos_xp','false');}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testanon"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(600)

def strip(s):
    return "".join(c for c in unicodedata.normalize("NFD",s.lower()) if unicodedata.category(c)!="Mn")
def digits(s): return re.sub(r"\D","",s)

IDS=[
 {"nom":"DURAND","prenom":"Martine","ddn":"03/04/1958","tel":"06 11 22 33 44","nir":"2 58 04 45 234 567 89","adr":"12 rue des Carmes, 45000 Orléans","voie":"Carmes","proche":"Bernard Durand"},
 {"nom":"LEFÈVRE","prenom":"Jean-Pierre","ddn":"17/11/1947","tel":"06 22 33 44 55","nir":"1 47 11 45 123 456 78","adr":"5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle","voie":"Verdun","proche":"Hélène Lefèvre"},
 {"nom":"ROUSSELIN","prenom":"Marc","ddn":"09/02/1975","tel":"07 33 44 55 66","nir":"1 75 02 45 234 111 22","adr":"3 allée des Tilleuls, 45160 Olivet","voie":"Tilleuls","proche":"Chloé Rousselin"},
 {"nom":"PETIT","prenom":"Louise","ddn":"28/06/2019","tel":"06 44 55 66 77","nir":"2 19 06 45 234 999 88","adr":"8 impasse du Moulin, 45400 Fleury-les-Aubrais","voie":"Moulin","proche":"Rose Petit"},
 {"nom":"BLANC","prenom":"Noël","ddn":"25/12/1935","tel":"02 38 11 22 33","nir":"1 35 12 45 123 222 33","adr":"21 rue de la Gare, 45800 Saint-Jean-de-Braye","voie":"Gare","proche":"Camille Blanc"},
 {"nom":"D'ANGELO","prenom":"Sofia","ddn":"02/09/1990","tel":"06 55 66 77 88","nir":"2 90 09 45 234 333 44","adr":"14 boulevard Alexandre-Martin, 45000 Orléans","voie":"Alexandre-Martin","proche":"Luca D'Angelo"},
 {"nom":"NGUYEN","prenom":"Thi Mai","ddn":"11/05/1983","tel":"07 66 77 88 99","nir":"2 83 05 45 234 444 55","adr":"2 chemin des Vignes, 45770 Saran","voie":"Vignes","proche":"Anh Nguyen"},
 {"nom":"MOREAU-FONTAINE","prenom":"Émilie","ddn":"30/01/2001","tel":"06 77 88 99 00","nir":"2 01 01 45 234 555 66","adr":"9 place du Martroi, 45000 Orléans","voie":"Martroi","proche":"Patrick Moreau"},
 {"nom":"GARCIA","prenom":"Antoine","ddn":"14/07/1968","tel":"06 88 99 00 11","nir":"1 68 07 45 234 666 77","adr":"33 rue Marcel-Proust, 45100 Orléans","voie":"Marcel-Proust","proche":"Nadia Garcia"},
 {"nom":"KOWALSKI","prenom":"Agnès","ddn":"05/10/1942","tel":"02 38 22 33 44","nir":"2 42 10 45 234 777 88","adr":"6 lotissement des Bleuets, 45650 Saint-Jean-le-Blanc","voie":"Bleuets","proche":"Stanislas Kowalski"},
]
TEMPLATES=[
 "Visite chez {CIV} {NOM} {PRENOM}, née le {DDN}, pour douleur lombaire depuis trois jours sans fièvre. Habite {ADR}. Joignable au {TEL}. Pas de déficit moteur, Lasègue négatif. Examen abdominal normal.",
 "{PRENOM} {NOM}, {AGE}, consulte pour toux et fièvre à 38,5 depuis deux jours. Son {LIEN} {PROCHE} est présent. Auscultation : foyer de crépitants en base droite, SpO2 95 %. Numéro de sécurité sociale {NIR}.",
 "Appel de la régulation : {NOM} {PRENOM} au {TEL}, {ADR}, chute ce matin. Patient né le {DDN}. Douleur de hanche droite, impossibilité d'appui, pas de traumatisme crânien. Dossier n° 2024-00{N}.",
 "Contre-appel : {PROCHE} rapporte que {CIV} {NOM} vomit depuis hier soir, diarrhée, pas de sang. Dernier repas au restaurant. Antécédent d'appendicectomie en {ANNEE}. TA 12/7, pouls 88.",
 "{CIV} {NOM} ({PRENOM}), {AGE}, {ADR}. Dyspnée d'effort progressive, œdèmes des membres inférieurs, prise de 3 kg. Sous Lasilix et Kardégic. Courriel {MAIL}. RPPS du médecin traitant 10001234567.",
 "Enfant {PRENOM} {NOM} ({AGE}), amené par sa mère {PROCHE}. Fièvre à 39, otalgie droite, tympan rouge et bombé. Poids 14 kg. Né le {DDN}. Pas d'allergie connue. Scolarisé à l'école du quartier.",
 "Monsieur {NOM}, {PRENOM}, joint au {TEL}. Plaie de la main gauche sur verre, saigne peu, vaccination tétanos à jour. Suture à faire. Habite près de la gare, {ADR}.",
 "Patiente {PRENOM} {NOM} vue au cabinet. Céphalée brutale ce matin, vomissements, raideur de nuque absente, pas de fièvre. Glasgow 15. Née le {DDN}. Contact : {PROCHE} au {TEL}.",
 "Visite en EHPAD : {CIV} {NOM} {PRENOM}, {AGE}, confusion depuis 48 heures, BU positive, fièvre 38,2. Traitement : Eliquis, Levothyrox. Famille prévenue ({PROCHE}). Adresse de la résidence : {ADR}.",
 "{PRENOM} {NOM}, {AGE}, lombalgie aiguë après port de charge, pas de signe neurologique, EVA 7. Travaille comme livreur. Antécédent de hernie discale opérée en {ANNEE}. Tél. {TEL}.",
]
def age_of(ddn):
    d,m,y=[int(x) for x in ddn.split("/")]
    a=2026-y-(1 if (10,21)<(m,d) else 0)
    return f"{a} ans"
def build(ident,tpl,variant):
    nom=ident["nom"]; prenom=ident["prenom"]; ddn=ident["ddn"]; tel=ident["tel"]; nir=ident["nir"]; adr=ident["adr"]; proche=ident["proche"]
    civ="Madame" if ident["nir"].startswith("2") else "Monsieur"; lien="mari" if civ=="Madame" else "épouse"
    traps=[]
    if "lower" in variant: nom=nom.lower(); prenom=prenom.lower(); proche=proche.lower(); traps.append("minuscules")
    if "noacc" in variant: nom=strip(nom).upper(); prenom=strip(prenom).capitalize(); proche=" ".join(w.capitalize() for w in strip(proche).split()); traps.append("sans accents")
    if "typo" in variant and len(nom)>=5:
        i=2; nom=nom[:i]+("X" if nom[i]!="X" else "Y")+nom[i+1:]; traps.append("faute d'une lettre")
    if "split" in variant and len(nom)>=6: nom=nom[:3]+" "+nom[3:]; traps.append("mot coupé")
    if "joined" in variant: prenom=prenom.replace(" ","")+nom.capitalize(); nom=""; traps.append("mots collés")
    if "digits_space" in variant: ddn=" ".join(digits(ddn)[i:i+2] for i in range(0,8,2)); traps.append("date chiffres espacés")
    if "digits_dot" in variant: tel=".".join(digits(tel)[i:i+2] for i in range(0,10,2)); nir=".".join(digits(nir)[i:i+3] for i in range(0,13,3)); traps.append("chiffres à points")
    if "digits_glue" in variant: tel=digits(tel); ddn=digits(ddn); traps.append("chiffres collés")
    if "letters_date" in variant:
        d,m,y=ddn.split("/") if "/" in ddn else (ddn[:2],ddn[2:4],ddn[4:]); mois=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"][int(m)-1]; ddn=f"{int(d)} {mois} {y}"; traps.append("date en lettres")
    if "upper" in variant: prenom=prenom.upper(); proche=proche.upper(); traps.append("capitales")
    t=tpl.format(CIV=civ,NOM=nom,PRENOM=prenom,DDN=ddn,TEL=tel,NIR=nir,ADR=adr,PROCHE=proche,LIEN=lien,AGE=age_of(ident["ddn"]),ANNEE=random.choice(["2019","2021","2012"]),N=random.randint(100,999),MAIL=strip(prenom.split()[0] if prenom else "x")+"."+strip(ident["nom"]).replace("'","")+"@exemple.fr")
    return t,traps
def frags(ident):
    f=[]
    for w in re.split(r"[\s\-']+",ident["nom"]):
        if len(w)>=4: f.append(("nom",strip(w)))
    for w in re.split(r"[\s\-]+",ident["prenom"]):
        if len(w)>=4: f.append(("prénom",strip(w)))
    for w in ident["proche"].split():
        if len(w)>=4 and strip(w) not in [x[1] for x in f]: f.append(("proche",strip(w)))
    f.append(("naissance",digits(ident["ddn"]))); f.append(("naissance2",digits(ident["ddn"])[0:1].lstrip("0")+digits(ident["ddn"])[2:]))
    f.append(("téléphone",digits(ident["tel"]))); f.append(("NIR",digits(ident["nir"])[:13]))
    f.append(("adresse",strip(ident["voie"]).replace("-","")))
    return f
def check_out(text,ident,extra_frags=()):
    t=text; t=re.sub(r"\[\[[^\]]*\]\]"," ",t)
    nt=" "+re.sub(r"[^a-z0-9]+"," ",strip(t))+" "; nd=digits(t)
    bad=[]
    for cat,fr in frags(ident)+list(extra_frags):
        if cat in ("naissance","naissance2","téléphone","NIR"):
            if fr and fr in nd: bad.append((cat,fr))
        else:
            if fr and (" "+fr+" ") in nt: bad.append((cat,fr))
    return bad

CLEAN=[
 "Douleur thoracique constrictive depuis une heure, irradiant au bras gauche, sueurs. ECG : sus-décalage en D2 D3 aVF. Appel du 15, Kardégic 250 mg donné. Transfert SMUR.",
 "Angine érythémateuse, TDR positif, Centor 3. Amoxicilline prescrite selon la fiche. Reconsulter si dysphagie majeure. Pas d'allergie connue.",
 "Pneumopathie du lobe inférieur droit, CRB-65 à 1, SpO2 94 %, pas de signe de gravité. Traitement ambulatoire, contrôle à 48 heures. Vaccination antigrippale faite.",
 "Entorse de cheville droite, Ottawa négatif, pas de radiographie. Protocole GREC expliqué, attelle, antalgiques. Arrêt de travail 5 jours.",
 "Nourrisson de 8 mois, bronchiolite, Silverman 2, SpO2 97 %, boit plus de la moitié des biberons. Lavage de nez, surveillance, consignes données aux parents.",
 "Crise d'asthme modérée, DEP 60 % de la théorique, sibilants diffus. Ventoline en chambre d'inhalation, Solupred, réévaluation à 1 heure : amélioration nette.",
 "Colique néphrétique gauche typique, BU : hématurie. Bi-Profénid, Spasfon, filtrage des urines, échographie rénale prescrite. Pas de fièvre.",
 "Cystite simple, BU leucocytes et nitrites positifs. Fosfomycine monodose. Consignes de reconsultation si fièvre ou douleur lombaire.",
 "Dépression caractérisée, PHQ-9 à 16, pas d'idées suicidaires, entourage présent. Orientation psychiatre, suivi rapproché, numéro 3114 remis.",
 "Hypoglycémie à 0,45 g/l chez un diabétique sous Diamicron, resucrage efficace, glycémie de contrôle 1,2 g/l. Adaptation du traitement par le médecin traitant.",
 "Zona intercostal droit T6, 3 jours d'évolution, Zelitrex selon la fiche, antalgiques. Douleur EVA 5. Œil non concerné.",
 "Gastro-entérite aiguë, pas de déshydratation, Tiorfan et Adiaril. Éviction scolaire 2 jours. Reconsulter si vomissements incoercibles.",
 "Fibrillation atriale connue sous Eliquis, palpitations depuis ce matin, FC 110 irrégulière, TA 13/8, pas de douleur thoracique. ECG transmis au cardiologue, CHA2DS2-VASc 4.",
 "Lumbago aigu sans sciatique, Lasègue négatif, pas de trouble sphinctérien. Bi-Profénid, Doliprane, mobilisation précoce, arrêt 5 jours selon le métier.",
 "Otite moyenne aiguë bilatérale chez un enfant de 3 ans, 15 kg. Amoxicilline dose-poids, Doliprane. Tympans bombés et congestifs. Pas d'allergie.",
 "Plaie du cuir chevelu de 3 cm, propre, suture par agrafes, tétanos à jour. Surveillance neurologique expliquée, pas de perte de connaissance.",
 "Érysipèle de jambe droite, placard inflammatoire bien limité, fièvre 38,8, pas de nécrose. Amoxicilline selon la fiche, repos jambe surélevée, contrôle à 48 heures.",
 "Syncope vagale à l'orthostatisme, ECG normal, glycémie 1,0, examen neurologique normal. Conseils d'hydratation, pas de conduite 24 heures.",
 "Sinusite maxillaire aiguë, douleur à la pression, rhinorrhée purulente, fièvre 38. Lavage de nez, antalgiques, antibiotique si persistance au-delà de 10 jours selon la fiche.",
 "Épicondylite droite, douleur à l'extension contrariée du poignet, pas de déficit. Paracétamol, Voltarène Emulgel, bracelet, rééducation. Revoir à 2 mois.",
 "Hypertension découverte à 17/10 confirmée aux trois mesures, pas de signe de gravité, bilan prescrit, automesure, revoir dans 15 jours.",
 "Rhinopharyngite virale, pas d'antibiotique, lavage de nez, Doliprane. Mère rassurée, consignes de reconsultation remises.",
 "Pyélonéphrite aiguë simple, fièvre 39, douleur lombaire droite, BU positive, ECBU prélevé. Oroken selon la fiche, contrôle à 72 heures.",
 "Anxiété aiguë sans élément dépressif, GAD-7 à 12. Techniques de respiration, Atarax ponctuel, orientation psychologue, suivi médecin traitant.",
 "Contusion de l'épaule après chute, mobilité conservée, pas de déformation, pas de radiographie. Antalgiques, glace, revoir si douleur persistante à 7 jours.",
 "Conjonctivite bactérienne bilatérale, sécrétions purulentes, Tobrex, lavage au sérum physiologique. Pas de baisse d'acuité visuelle.",
 "Goutte du gros orteil droit, poussée typique, colchicine selon la fiche, bilan uricémie prescrit. Pas de fièvre.",
 "Lombosciatique L5 droite, Lasègue à 40°, pas de déficit moteur, pas de trouble sphinctérien. Traitement antalgique, revoir à 10 jours.",
 "Varicelle chez un enfant de 4 ans, éruption vésiculeuse diffuse, fièvre 38,3, pas de surinfection. Doliprane, antihistaminique, éviction.",
 "Insuffisance cardiaque décompensée modérée, crépitants des bases, œdèmes, prise de poids 3 kg, SpO2 93 %. Majoration du diurétique selon avis cardiologue, bilan prescrit.",
]

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    random.seed(41)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1280,"height":900})
            await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
            await unlock(page)
            RUN="""([t,c])=>{const ctx=Object.assign({},c,{lexique:aiLexique(),courants:aiCourants(),medicaments:aiMedWords()});const an=anonymize(t,ctx);const leaks=anonLeaks(an.text,ctx);const doubts=anonDoubts(an,ctx);return {text:an.text,items:an.items.length,cats:an.items.map(i=>i.cat),ms:an.ms,leaks:leaks.map(l=>l.cat+' '+l.frag),doubts:doubts.map(d=>d.w+' ('+d.why+')')};}"""
            def ctx_of(ident): return {"patient":ident["nom"]+" "+ident["prenom"],"ddn":ident["ddn"],"ref":"21/10/2026","adresse":[ident["adr"]],"tel":[ident["tel"]],"nir":ident["nir"],"autres":[{"n":ident["proche"],"cat":"PERSONNE"}],"masquer":[],"garder":[]}
            # ---------- 1. corpus de 100 dictées piégées ----------
            VARS=[["lower"],["noacc"],["typo"],["split"],["joined"],["digits_space"],["digits_dot"],["digits_glue"],["letters_date"],["upper","digits_dot"]]
            tot=0; masked=0; blocked=0; fails=[]
            for i,ident in enumerate(IDS):
                for j,tpl in enumerate(TEMPLATES):
                    text,traps=build(ident,tpl,VARS[(i+j)%len(VARS)]); tot+=1
                    r=await page.evaluate(RUN,[text,ctx_of(ident)])
                    bad=check_out(r["text"],ident)
                    dw=[strip(d.split(" (")[0]) for d in r["doubts"]]
                    if not bad: masked+=1
                    elif r["leaks"] or all((fr in dw or any(fr in d for d in dw)) for cat,fr in bad if cat in ("nom","prénom","proche")) and all(cat in ("nom","prénom","proche") for cat,fr in bad): blocked+=1
                    else: fails.append({"id":ident["nom"],"traps":traps,"bad":bad,"doubts":r["doubts"],"out":r["text"][:160]})
            ok(f"corpus : 100 dictées piégées ({tot}) → {masked} entièrement masquées, {blocked} bloquées (second contrôle ou mot à confirmer), {len(fails)} fuites",tot==100 and not fails,fails[:3])
            # ---------- 2. fuzzing 1 000 variantes ----------
            MUT=["lower","noacc","typo","split","joined","digits_space","digits_dot","digits_glue","letters_date","upper"]
            tot=0; masked=0; blocked=0; fails=[]
            for n in range(1000):
                ident=random.choice(IDS); tpl=random.choice(TEMPLATES); variant=random.sample(MUT,random.randint(1,3))
                text,traps=build(ident,tpl,variant); tot+=1
                r=await page.evaluate(RUN,[text,ctx_of(ident)])
                bad=check_out(r["text"],ident)
                dw=[strip(d.split(" (")[0]) for d in r["doubts"]]
                if not bad: masked+=1
                elif r["leaks"] or all((fr in dw or any(fr in d for d in dw)) for cat,fr in bad if cat in ("nom","prénom","proche")) and all(cat in ("nom","prénom","proche") for cat,fr in bad): blocked+=1
                else: fails.append({"id":ident["nom"],"traps":traps,"bad":bad,"doubts":r["doubts"],"out":r["text"][:160]})
            ok(f"fuzzing : {tot} variantes → {masked} masquées, {blocked} bloquées (second contrôle ou mot à confirmer), {len(fails)} fuites (zéro exigé)",not fails,fails[:3])
            # ---------- 3. faux positifs sur 30 dictées sans identité ----------
            words=0; fp=0; samples=[]
            for text in CLEAN:
                r=await page.evaluate(RUN,[text,{"patient":"ZZZ Yyy","ddn":"01/01/1900","ref":"21/10/2026","adresse":[],"tel":[],"nir":"","autres":[]}])
                words+=len(re.findall(r"[^\W\d_]+",text)); n=sum(1 for c in r["cats"] if c in ("NOM PROPRE","PERSONNE","LIEU","MASQUÉ")); fp+=n
                if n: samples.append((text[:40],[x for x in re.findall(r"\[\[[^\]]*\]\]",r["text"])][:3]))
            rate=fp/words*100 if words else 0
            ok(f"faux positifs : {fp} mots masqués à tort sur {words} ({rate:.1f} %) dans 30 dictées sans identité (objectif < 3 %)",rate<3,samples[:5])
            # ---------- 4. chronométrage : 20 dictées de ≈ 2 000 caractères ----------
            ms=[]; chars=[]
            for k in range(20):
                ident=IDS[k%len(IDS)]; base,_=build(ident,TEMPLATES[k%len(TEMPLATES)],["digits_dot"])
                text=base
                while len(text)<2000: text+=" "+random.choice(CLEAN)
                r=await page.evaluate(RUN,[text,ctx_of(ident)]); ms.append(r["ms"]); chars.append(len(text))
            med=statistics.median(ms); mx=max(ms)
            ok(f"vitesse (cet ordinateur, Chromium) : {len(ms)} dictées de {int(statistics.mean(chars))} caractères → médiane {med:.0f} ms, maximum {mx:.0f} ms (objectif iPhone < 100 ms, non mesuré ici)",med<100,[round(x) for x in ms])
            open(os.path.join(ROOT,"tests","resultats_anon_vitesse.json"),"w",encoding="utf-8").write(json.dumps({"ms":[round(x,1) for x in ms],"chars":chars,"median":med,"max":mx},ensure_ascii=False))
            # ---------- 5. règles nouvelles : année seule, numéro de dossier, établissement, formes approchées, doutes, strict, listes ----------
            ident=IDS[2]
            r=await page.evaluate(RUN,["AVC en 2019, dossier n° 2024-00123, RPPS 10001234567. Scolarisé au Lycée Pothier, courses à Auchan. Rousselon présent. Vu par le Dr Lemoine.",ctx_of(ident)])
            ok("année seule → relative, numéro de dossier et RPPS masqués","il y a 7 ans" in r["text"] and "2024-00123" not in r["text"] and "10001234567" not in r["text"],r["text"][:200])
            ok("établissements connus masqués (Lycée Pothier, Auchan)","Pothier" not in r["text"] and "Auchan" not in r["text"] and r["cats"].count("LIEU")>=2,r["text"][:200])
            ok("second contrôle : « Rousselon » (une lettre) masqué, bloqué ou à confirmer — jamais en clair sans contrôle","Rousselon" not in r["text"] or any("forme approchée" in x for x in r["leaks"]) or any("Rousselon" in x for x in r["doubts"]),(r["text"][:120],r["leaks"],r["doubts"]))
            r1b=await page.evaluate(RUN,["vu avec rousselon ce jour, pas de fièvre.",ctx_of(ident)])
            ok("second contrôle : « rousselon » en minuscules (une lettre) repéré comme forme approchée ou doute",any("forme approchée" in x for x in r1b["leaks"]) or any("rousselon" in x for x in r1b["doubts"]),(r1b["leaks"],r1b["doubts"]))
            r2=await page.evaluate(RUN,["Patient ROUSSE LIN vu ce jour.",ctx_of(ident)])
            ok("second contrôle : nom coupé en deux repéré (« ROUSSE LIN »)",any("coupé" in x for x in r2["leaks"]) or "ROUSSE" not in r2["text"],(r2["leaks"],r2["text"]))
            r3=await page.evaluate(RUN,["Durant la nuit, douleur. Pris du Kardégic. Zxqvu présent. Hospitalisée en mars.",ctx_of(IDS[0])])
            ok("doutes : mot inconnu avec majuscule à confirmer, médicament et mot courant non signalés",any("Zxqvu" in x for x in r3["doubts"]) or "Zxqvu" not in r3["text"],r3)
            r4=await page.evaluate(RUN,["Hospitalisée en mars à Oréliance. Kardégic poursuivi. Zxqvu présent.",dict(ctx_of(IDS[0]),masquer=["Oréliance"],garder=["Zxqvu"])])
            ok("listes personnelles : « Oréliance » toujours masqué, « Zxqvu » toujours gardé et non douteux","Oréliance" not in r4["text"] and "Zxqvu" in r4["text"] and not any("Zxqvu" in x for x in r4["doubts"]),r4)
            r5=await page.evaluate(RUN,["Hospitalisée à Oréliance en 2019, Kardégic, 1500 pas par jour, dossier 45678.",dict(ctx_of(IDS[0]),strict=True)])
            r5b=await page.evaluate(RUN,["Hospitalisée à Oréliance en 2019, Kardégic, 1500 pas par jour, dossier 45678.",ctx_of(IDS[0])])
            ok("mode strict : plus de mots masqués, numéros d'au moins 4 chiffres masqués, médicament gardé",r5["items"]>=r5b["items"] and "45678" not in r5["text"] and "Kardégic" in r5["text"],(r5["text"],r5b["text"]))
            r6=await page.evaluate(RUN,["Madame a 93 ans, née le 05/10/1932.",dict(ctx_of(IDS[0]),ddn="05/10/1932")])
            ok("âge regroupé au-delà de 89 ans","90 ans ou plus" in r6["text"] and "1932" not in r6["text"],r6["text"])
            # ---------- 6. worker (anonymisation à la volée) ----------
            w=await page.evaluate("""async()=>{Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958'});const ctx=aiAnonCtx();const r=await anonAsync('Madame Durand, née le 03/04/1958, tousse depuis 3 jours. Tél 06 11 22 33 44.',ctx);return r;}""")
            ok("worker d'anonymisation : réponse hors fil principal, éléments masqués, aucune fuite, temps mesuré",w.get("ok") and not w.get("sync") and w.get("n",0)>=3 and not w.get("leaks") and isinstance(w.get("ms"),(int,float)),w)
            ok("aucune erreur JS",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_anon_v41z.md"),"w",encoding="utf-8").write("# Tests anonymisation v41z — corpus piégé, fuzzing, faux positifs, vitesse, doutes, strict, listes, worker\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
