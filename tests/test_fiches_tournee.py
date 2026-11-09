# -*- coding: utf-8 -*-
"""09/11/2026 — fiches MccMissionSG (nouvelle et ancienne présentation) et tournée sans question.
1. parseFiche : nom = ligne sous « INFORMATIONS PATIENT » (noms composés, prénoms multiples, ligne illisible → vide et signalée), zones repérées par leurs intitulés,
   heure d'appel et attente lues dans « INTERVENTION » (alerte « attend depuis plus de 2 h », rang dans la tournée).
2. Tournée (iPhone 375 px) : trois demandes successives intégrées d'elles-mêmes, carte à une ligne (Appeler, Priorité), « Rendre à la régulation » dans « Plus »,
   recalcul silencieux au retrait et à la validation, ligne discrète quand l'ordre change.
Fiches et patients fictifs (aucune donnée réelle). Réseau extérieur simulé : géocodeur BAN et OSRM (table, trip) déterministes ; tout le reste bloqué.
Lancer : python tests/test_fiches_tournee.py"""
import asyncio, os, re, json, math, subprocess, sys, time, urllib.parse
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8818
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page,base,uid="testfiches"):
    await page.add_init_script("try{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','false');}catch(e){}")
    await page.goto(base+"index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

# Géocodeur BAN simulé (adresses fictives d'Orléans et alentours)
GEO={"CARMES":(47.900,1.900,"3 Rue des Carmes 45000 Orléans","Orléans"),"BEAUHAIRE":(47.909,1.868,"8 Rue Charles Beauhaire 45140 Saint-Jean-de-la-Ruelle","Saint-Jean-de-la-Ruelle"),
     "MARTROI":(47.9030,1.9090,"1 Place du Martroi 45000 Orléans","Orléans"),"BOURGOGNE":(47.9020,1.9110,"10 Rue de Bourgogne 45000 Orléans","Orléans"),
     "CHANZY":(47.9029,1.9093,"44 Rue Chanzy 45000 Orléans","Orléans"),"PINS":(47.84,1.94,"14 Avenue des Pins 45100 Orléans","Orléans")}
async def ban_mock(route):
    url=route.request.url; m=re.search(r"[?&]q=([^&]*)",url); q=urllib.parse.unquote_plus(m.group(1)) if m else ""
    if "INTROUVABLE" in q.upper(): body={"features":[]}
    else:
        hit=next((v for k,v in GEO.items() if k in q.upper()),(47.905,1.91,q,"Orléans"))
        body={"features":[{"geometry":{"coordinates":[hit[1],hit[0]]},"properties":{"label":hit[2],"city":hit[3],"score":0.9}}]}
    await route.fulfill(status=200,content_type="application/json",body=json.dumps(body))
# OSRM simulé : durées déterministes (vol d'oiseau × 1,3 à 35 km/h) ; table complète et voyage dans l'ordre donné
def hav(a,b):
    R=6371; r=math.radians
    dla=r(b[1]-a[1]); dlo=r(b[0]-a[0]); h=math.sin(dla/2)**2+math.cos(r(a[1]))*math.cos(r(b[1]))*math.sin(dlo/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))
async def osrm_mock(route):
    url=route.request.url; m=re.search(r"/(table|trip)/v1/driving/([^?]+)",url)
    if not m:
        await route.fulfill(status=200,content_type="application/json",body=json.dumps({"code":"NoRoute"})); return
    pts=[tuple(map(float,c.split(","))) for c in m.group(2).split(";")]
    if m.group(1)=="table":
        km=[[hav(a,b)*1.3 for b in pts] for a in pts]
        body={"code":"Ok","durations":[[round(d/35*3600,1) for d in row] for row in km],"distances":[[round(d*1000,1) for d in row] for row in km]}
    else:
        legs=[{"distance":round(hav(pts[i],pts[i+1])*1.3*1000,1),"duration":round(hav(pts[i],pts[i+1])*1.3/35*3600,1)} for i in range(len(pts)-1)]
        body={"code":"Ok","waypoints":[{"waypoint_index":i,"trips_index":0} for i in range(len(pts))],"trips":[{"legs":legs,"distance":sum(l["distance"] for l in legs),"duration":sum(l["duration"] for l in legs)}]}
    await route.fulfill(status=200,content_type="application/json",body=json.dumps(body))
async def net(ctx):
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    await ctx.route(re.compile(r".*router\.project-osrm\.org.*"),osrm_mock)
    await ctx.route(re.compile(r".*api-adresse\.data\.gouv\.fr.*"),ban_mock)

# Fiches fictives, construites dans la page (dates relatives à l'heure courante) : nouvelle présentation (n1 à n4), ancienne (o1 à o3)
FICHES_JS=r"""()=>{const pad=n=>String(n).padStart(2,"0");const dt=ts=>{const d=new Date(ts);return pad(d.getDate())+"/"+pad(d.getMonth()+1)+"/"+d.getFullYear()+" "+pad(d.getHours())+":"+pad(d.getMinutes());};
 const now=Date.now();const t127=now-127*60000,t45=now-45*60000,t150=now-150*60000;
 const T={
  n1:"Auto-Régulation / Visite\nCH G\nINFORMATIONS PATIENT\nDUPONT-MARTIN Jean-Pierre Marie\nNé(e) le 03/04/1958 – 68 A\nTél patient 06 12 34 56 78\nINTERVENTION\n"+dt(t127)+" 2h7m\nDL TETE / FIEVRE\nfièvre depuis hier soir, céphalées, pas de raideur de nuque\nPARTICULIER\nADRESSE PATIENT\n3 RUE DES CARMES\n45000 ORLEANS\nEtg / Por",
  n2:"CH G\nINFORMATIONS PATIENT\nLE GOFF LOUIS GABRIEL\nNé(e) le 12/05/2019 – 7 A\nTél patient\n06 98 76 54 32\nINTERVENTION\n"+dt(t45)+"\n0h45m\nOTITE\nenfant fébrile, pleure la nuit\nPARTICULIER\nADRESSE PATIENT\n8 RUE CHARLES BEAUHAIRE\n45140 SAINT-JEAN-DE-LA-RUELLE\nBat : C Etg : 4 Por : 12",
  n3:"INFORMATIONS PATIENT\n▮▮▮▮ ▮▮\nNé(e) le 01/01/1990 – 36 A\nTél patient 06 11 22 33 44\nINTERVENTION\n"+dt(t150)+" 2h30m\nGARDE A VUE\nOPJ EXEMPLE\nPOLICE\nADRESSE PATIENT\n1 PLACE DU MARTROI\n45000 ORLEANS",
  n4:"INFORMATIONS PATIENT\nDUPONT Jean ♂\nNé(e) le 05/06/1970 – 56 A\nTél patient 06 00 11 22 33\nINTERVENTION\n"+dt(t45)+" 0h45m\nTOUX\nPARTICULIER\nADRESSE PATIENT\n10 RUE DE BOURGOGNE\n45000 ORLEANS",
  o1:"DUPONT MARIE\nNée le 05/06/1990 - 36 A\nTél patient 06 12 34 56 78\nAdresse patient : 3 rue de la Gare\n45000 ORLEANS\nN° INTERVENTION 26110300123\nDL CHEVILLE\nchute dans l'escalier hier soir",
  o2:"Mission en cours\nInformations patient\nDUBOIS CLAIRE\nNée le 12/05/1958 - 68 A\nTél. patient\n02 38 00 11 22\nTél. appelant\n06 12 34 56 78\nIntervention\nDOULEUR ABDOMINALE\nCommentaire : sonner au 2e\nAdresse :\n14 AVENUE DES PINS\n45100 ORLÉANS-LA-SOURCE\nBat : C Etg : 4 Por : 12",
  o3:"INFORMATIONS PATIENT\nMARTIN PAUL\nNé(e) le 03/04/1990 - 36 A\nTél patient Tél appelant\n06 11 22 33 44 06 11 22 33 44\nINTERVENTION\n15/10/2026 19:51 1h40m\nGARDE A VUE\nATTENTION, ADRESSE REPOSITIONNEE PAR\nDURAND ALAIN LE 01/02/2025 10:11:12\nOPJ EXEMPLE\nPOLICE\nADRESSE PATIENT\n12 RUE DES LILAS,\n45000, ORLÉANS"};
 const out={now,t127,t45,t150,T};for(const k in T){const f=parseFiche(T[k]);out[k]={nom:f.nom,prenom:f.prenom,ddn:f.ddn,age:f.ageAff,tel:f.tel,tel2:f.tel2,motif:f.motif,note:f.note,addr:f.addr,bat:f.bat,regTs:f.regTs,att:f.attente,W:ficheCheck(f),sexe:f.sexe};}
 return out;}"""

# Tournée fictive en cours : cabinet, visite en cours (w1), deux visites prévues (w2, w3)
SET=r"""async()=>{TESTMODE=true;newPatient();TOUR.base={lat:47.9029,lon:1.9093,label:'Cabinet, 44 rue Chanzy, 45000 Orléans'};TOUR.origin='cabinet';TOUR.dest='';TOUR.destGeo=null;TOUR.manual=false;TOUR.cfg=null;TOUR.autoChg=null;TOUR.given=[];TOUR.unread=[];TOUR.consults=[];
  const now=Date.now();
  TOUR.stops=[{id:'w1',addr:'12 rue de la Gare, 45000 Orléans',label:'12 Rue de la Gare 45000 Orléans',lat:47.909,lon:1.905,city:'Orléans',nom:'MARTIN Jeanne',ddn:'03/04/1938',tel:'0611111111',motif:'fièvre',ts:now-30*60000,done:false},
   {id:'w2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.912,lon:1.86,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/01/2018',tel:'0622222222',motif:'otite',ts:now-25*60000,done:false},
   {id:'w3',addr:'10 rue de la Mairie, 45160 Olivet',label:'10 Rue de la Mairie 45160 Olivet',lat:47.86,lon:1.9,city:'Olivet',nom:'ROUX Anne',ddn:'02/02/1990',tel:'0644444444',motif:'angine',ts:now-20*60000,done:false}];
  TOUR.order=['w1','w2','w3'];TOUR.current='w1';TOUR.started=now;TOUR.est=false;await tpLegsRefresh();tpEtaApply();tourSave();
  state.cot=state.cot||cotDefault();state.cot.lieu='visite';state.cot.auto=false;state.patient='MARTIN Jeanne';state.ddn='03/04/1938';state.sexe='f';state.view='';render();}"""
# ajout d'une fiche par « Coller les fiches », attente de l'intégration, lecture de la carte
ADD=r"""async(t)=>{const n0=TOUR.stops.length;await fichesFromText(t);const s=TOUR.stops[TOUR.stops.length-1];for(let i=0;i<80&&!(s&&s.ins);i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,150));return window.__card(s);}"""
CARD=r"""()=>{window.__card=s=>{const card=document.querySelector('.tcard .tp-new');const d=document.getElementById('fdock');const rows=card?[...card.querySelectorAll('.tp-newrow')]:[];
  return {n:TOUR.stops.length,id:s&&s.id,isNew:!!(s&&s.isNew),ins:s&&s.ins||null,inOrder:!!(s&&TOUR.order.includes(s.id)),order:TOUR.order.slice(),pos:s?tourOrdered().filter(x=>x.id!==TOUR.current).findIndex(x=>x.id===s.id)+1:0,
   card:!!card,rows:rows.length,info:rows.map(r=>(r.querySelector('.tp-newinfo')||{}).textContent||''),names:rows.map(r=>r.querySelector('b').parentNode.firstChild.textContent||''),fil:d?d.dataset.fil:null,
   insBtn:document.querySelectorAll('[data-tpins],[data-tplater]').length,dockGive:document.querySelectorAll('#fdock [data-tpgive]').length,moreGive:document.querySelectorAll('.tc-more [data-tpgive]').length,
   call:rows.map(r=>{const a=r.querySelector('[data-tpcall]');return a?a.getAttribute('href'):'';}),prio:rows.map(r=>r.querySelectorAll('[data-tpprio]').length),wait:s?tpWait(s):0,nom:s&&s.nom||'',regTs:s&&s.regTs||null,km:s&&s.km,
   body:document.body.innerText,over:document.documentElement.scrollWidth>document.documentElement.clientWidth+1,waitBanner:(document.querySelector('.tp-wait summary')||{}).textContent||''};};return true;}"""

async def run():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    HTML=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
    # ---------- source ----------
    fe=re.search(r"const FIL_ETATS=\[[^\]]*\]",HTML); fe=fe.group(0) if fe else ""
    ok("source : « Intégrer au mieux » et « En fin de tournée » retirés des nouvelles demandes","Intégrer au mieux" not in HTML and "data-tplater" not in HTML and "data-tpins" not in HTML)
    ok("source : état « Entre deux » retiré du fil, intégration automatique et lecture par intitulés présentes","entre" not in fe and "function tpAutoInsert" in HTML and "const FICHE_HEADS=" in HTML and "function tpRank" in HTML,fe)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True)
            await net(ctx)
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page,f"http://localhost:{PORT}/")
            L="fiches : "
            # ---------- 1. lecture des fiches ----------
            F=await page.evaluate(FICHES_JS)
            n1=F["n1"]
            ok(L+"nouvelle présentation : le nom est la ligne sous « INFORMATIONS PATIENT » (« DUPONT-MARTIN » / « Jean-Pierre Marie »), jamais « CH G » de l'en-tête",n1["nom"]=="DUPONT-MARTIN" and n1["prenom"]=="Jean-Pierre Marie" and "CH" not in n1["nom"],{k:n1[k] for k in ("nom","prenom")})
            ok(L+"n1 : naissance, âge affiché, téléphone, adresse (« Etg / Por » vides ignorés)",n1["ddn"]=="03/04/1958" and n1["age"]==68 and n1["tel"]=="0612345678" and n1["addr"]=="3 RUE DES CARMES 45000 ORLEANS" and n1["bat"]=="",{k:n1[k] for k in ("ddn","age","tel","addr","bat")})
            ok(L+"n1 : motif en gras « DL TETE / FIEVRE », texte libre en note ; « PARTICULIER », la date d'appel et « 2h7m » jamais repris",n1["motif"]=="DL TETE / FIEVRE" and "fièvre depuis hier" in n1["note"] and "PARTICULIER" not in n1["note"] and "2h7m" not in n1["note"] and "/20" not in n1["note"],{k:n1[k] for k in ("motif","note")})
            ok(L+"n1 : heure d'appel lue (il y a 2 h 07) → regTs à l'heure de l'appel, attente 127 min, aucune alerte « nom non lu »",n1["regTs"] is not None and abs(n1["regTs"]-F["t127"])<60000 and n1["att"]==127 and "nom non lu" not in n1["W"],{k:n1[k] for k in ("regTs","att","W")})
            n2=F["n2"]
            ok(L+"n2 : nom composé à particule en capitales « LE GOFF » / « LOUIS GABRIEL », téléphone sur la ligne suivante, accès Bât/Étage/Porte",n2["nom"]=="LE GOFF" and n2["prenom"]=="LOUIS GABRIEL" and n2["tel"]=="0698765432" and n2["bat"]=="Bât. C · Étage 4 · Porte 12" and n2["ddn"]=="12/05/2019",{k:n2[k] for k in ("nom","prenom","tel","bat","ddn")})
            ok(L+"n2 : attente « 0h45m » sur la ligne sous la date → 45 min ; motif OTITE ; note = texte libre",n2["att"]==45 and abs((n2["regTs"] or 0)-F["t45"])<60000 and n2["motif"]=="OTITE" and n2["note"]=="enfant fébrile, pleure la nuit" and "SAINT-JEAN-DE-LA-RUELLE" in n2["addr"],{k:n2[k] for k in ("att","motif","note","addr")})
            n3=F["n3"]
            ok(L+"n3 : ligne du nom illisible → nom vide et « nom non lu » signalé ; rien n'est pris ailleurs (ni OPJ, ni POLICE, ni le motif)",n3["nom"]=="" and n3["prenom"]=="" and "nom non lu" in n3["W"] and n3["motif"]=="GARDE A VUE" and n3["note"]=="OPJ EXEMPLE" and n3["att"]==150 and n3["ddn"]=="01/01/1990",{k:n3[k] for k in ("nom","prenom","W","motif","note","att")})
            n4=F["n4"]
            ok(L+"n4 : icône de sexe lue comme un caractère isolé après le nom → ignorée (« DUPONT » / « Jean »)",n4["nom"]=="DUPONT" and n4["prenom"]=="Jean" and n4["motif"]=="TOUX" and n4["att"]==45,{k:n4[k] for k in ("nom","prenom","motif","att")})
            o1,o2,o3=F["o1"],F["o2"],F["o3"]
            ok(L+"ancienne présentation (texte collé, nom en tête) : « DUPONT » / « MARIE », « Née le » → F, motif après « N° INTERVENTION », note",o1["nom"]=="DUPONT" and o1["prenom"]=="MARIE" and o1["sexe"]=="f" and o1["motif"]=="DL CHEVILLE" and "escalier" in o1["note"] and "INTERVENTION" not in o1["note"],{k:o1[k] for k in ("nom","prenom","sexe","motif","note")})
            ok(L+"ancienne présentation Android (intitulés en minuscules) : « DUBOIS » / « CLAIRE », téléphone patient, motif, accès",o2["nom"]=="DUBOIS" and o2["prenom"]=="CLAIRE" and o2["tel"]=="0238001122" and o2["motif"]=="DOULEUR ABDOMINALE" and o2["bat"]=="Bât. C · Étage 4 · Porte 12" and "PINS" in o2["addr"],{k:o2[k] for k in ("nom","prenom","tel","motif","bat","addr")})
            ok(L+"fiche d'un autre jour : « MARTIN » / « PAUL », motif « GARDE A VUE », mention « repositionnée par » ignorée, heure d'appel trop ancienne → attente affichée (1h40m) utilisée",o3["nom"]=="MARTIN" and o3["prenom"]=="PAUL" and o3["motif"]=="GARDE A VUE" and "DURAND" not in o3["note"] and o3["att"]==100 and o3["regTs"] is not None and abs(o3["regTs"]-(F["now"]-100*60000))<60000,{k:o3[k] for k in ("nom","prenom","motif","note","att","regTs")})
            # ---------- 2. tournée : trois demandes successives ----------
            L="tournée 375 : "
            await page.evaluate(SET); await page.evaluate(CARD); await page.wait_for_timeout(400)
            st0=await page.evaluate("()=>({fil:(document.getElementById('fdock')||{}).dataset?document.getElementById('fdock').dataset.fil:null,card:!!document.querySelector('.tcard'),cur:TOUR.current})")
            ok(L+"départ : visite en cours, barre « En route »",st0["fil"]=="route" and st0["card"] and st0["cur"]=="w1",st0)
            r1=await page.evaluate(ADD,F["T"]["n2"])
            m1=re.match(r"^intégrée en (\d+)(?:re|e) position, \+ \d+ min sur la fin de tournée",r1["info"][0] if r1["info"] else "")
            ok(L+"1re demande (fiche collée) : intégrée d'elle-même, sans question — dans l'ordre, plus « nouvelle », information d'intégration",r1["n"]==4 and r1["inOrder"] and not r1["isNew"] and r1["ins"] and r1["ins"].get("d") is not None,{k:r1[k] for k in ("n","inOrder","isNew","ins")})
            ok(L+"1re demande : carte « Nouvelle demande » = une ligne « intégrée en Ne position, + N min sur la fin de tournée », rang conforme à l'ordre",r1["card"] and r1["rows"]==1 and m1 and int(m1.group(1))==r1["pos"] and r1["pos"]>=1,{k:r1[k] for k in ("rows","info","pos")})
            ok(L+"1re demande : deux boutons discrets (📞 Appeler, ★ Priorité), aucun « Intégrer au mieux » ni « En fin de tournée », barre inchangée « En route », rien dans la barre du bas",r1["call"]==["tel:0698765432"] and r1["prio"]==[1] and r1["insBtn"]==0 and r1["dockGive"]==0 and r1["fil"]=="route" and "Intégrer au mieux" not in r1["body"] and "En fin de tournée" not in r1["body"],{k:r1[k] for k in ("call","prio","insBtn","dockGive","fil")})
            ok(L+"1re demande : nom lu sur la fiche (« LE GOFF LOUIS GABRIEL »), km du cabinet calculés pour la cotation",r1["nom"]=="LE GOFF LOUIS GABRIEL" and r1["km"] is not None,{k:r1[k] for k in ("nom","km")})
            r2=await page.evaluate(ADD,F["T"]["n4"])
            ok(L+"2e demande : intégrée, deux lignes dans la carte, chaque rang écrit = rang réel",r2["n"]==5 and r2["inOrder"] and r2["rows"]==2 and all(re.search(r"en (\d+)(?:re|e) position",t) for t in r2["info"]),{k:r2[k] for k in ("n","rows","info")})
            pos2=await page.evaluate("()=>tpNewList().map(s=>({id:s.id,pos:tourOrdered().filter(x=>x.id!==TOUR.current).findIndex(x=>x.id===s.id)+1,t:tpNewInfo(s)}))")
            ok(L+"2e demande : les deux lignes d'information suivent l'ordre recalculé",all(re.search(r"en (\d+)(?:re|e) position",x["t"]) and int(re.search(r"en (\d+)(?:re|e) position",x["t"]).group(1))==x["pos"] for x in pos2),pos2)
            r3=await page.evaluate(ADD,F["T"]["n1"])
            ok(L+"3e demande (appel il y a 2 h 07) : patient qui attend déjà plus de 2 h → placé devant les autres (après les priorités), ligne « attend depuis 2 h 07 »",r3["n"]==6 and r3["wait"]>=120 and r3["order"][0]==r3["id"] and r3["pos"]==1 and "attend depuis 2 h 0" in r3["info"][-1] and "en 1re position" in r3["info"][-1],{k:r3[k] for k in ("wait","order","pos","info")})
            ok(L+"3e demande : alerte « 1 patient attend depuis plus de 2 h » dans le bandeau, 3 lignes « Nouvelle demande », pas de défilement horizontal","attend depuis plus de 2 h" in r3["waitBanner"] and r3["rows"]==3 and not r3["over"],{k:r3[k] for k in ("waitBanner","rows","over")})
            ids=await page.evaluate("()=>tpNewList().map(s=>s.id)")
            await page.evaluate("window.scrollTo(0,0)"); await page.wait_for_timeout(200)
            await page.screenshot(path=os.path.join(OUT,"fiches-tournee-375-1-demandes.png"))
            # ---------- priorité ----------
            id_otite=r1["id"]; id_wait=r3["id"]
            pr=await page.evaluate("""async(id)=>{const t0=TOUR.autoTs||0;const b=document.querySelector('[data-tpprio="'+id+'"]');if(!b)return {err:'bouton absent'};b.click();for(let i=0;i<60&&(TOUR.autoTs||0)===t0;i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,200));
              const s=tourStop(id);const bb=document.querySelector('[data-tpprio="'+id+'"]');return {prio:!!s.prio,order:TOUR.order.slice(),info:tpNewInfo(s),on:!!(bb&&bb.classList.contains('on')),fil:(document.getElementById('fdock')||{dataset:{}}).dataset.fil,auto:(TOUR.autoTs||0)>t0};}""",id_otite)
            ok(L+"★ Priorité sur une demande : passe devant tout, ordre recalculé sans question, ligne « prioritaire, intégrée en 1re position », bouton marqué",pr.get("prio") and pr.get("order",[None])[0]==id_otite and pr.get("info","").startswith("prioritaire, intégrée en 1re position") and pr.get("on") and pr.get("auto"),pr)
            ok(L+"à priorité égale, l'attente puis le trajet décident : le patient qui attend depuis plus de 2 h vient juste après la priorité",pr.get("order",[])[1]==id_wait,pr.get("order"))
            # ---------- point d'arrivée = cabinet ----------
            r4=await page.evaluate("""async()=>{TOUR.dest='cabinet';const s=tourAdd('1 place du Martroi, 45000 Orléans','Mme N',false,{lat:47.9030,lon:1.9090,label:'1 Place du Martroi 45000 Orléans',city:'Orléans'});s.tel='0633333333';tourSave();render();tourAfterAdd(s);
              for(let i=0;i<80&&!s.ins;i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,150));return window.__card(s);}""")
            ok(L+"4e demande (adresse tapée, arrivée au cabinet réglée) : « + N min sur l'arrivée au cabinet », 4 lignes",r4["ins"] and "sur l'arrivée au cabinet" in (r4["info"][-1] if r4["info"] else "") and r4["rows"]==4 and r4["inOrder"],{k:r4[k] for k in ("info","rows","inOrder")})
            id_martroi=r4["id"]
            r5=await page.evaluate("""async()=>{const s=tourAdd('12 rue INTROUVABLE, 45000 Orléans','',false,null);tourSave();render();tourAfterAdd(s);for(let i=0;i<80&&!s.ins;i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,150));
              const c=window.__card(s);c.last=TOUR.order[TOUR.order.length-1]===s.id;TOUR.stops=TOUR.stops.filter(x=>x!==s);TOUR.order=TOUR.order.filter(x=>x!==s.id);tourSave();render();return c;}""")
            ok(L+"adresse introuvable : placée en fin de tournée sans question, ligne « adresse introuvable … corrige l'adresse »",r5["ins"] and r5["last"] and "adresse introuvable" in (r5["info"][-1] if r5["info"] else ""),{k:r5[k] for k in ("info","last")})
            # ---------- « Rendre à la régulation » dans « Plus » ----------
            g=await page.evaluate("""(id)=>{const d=document.querySelector('.tcard details.tc-more');if(d)d.open=true;const b=document.querySelector('.tc-more [data-tpgive="'+id+'"]');return {more:!!d,n:document.querySelectorAll('.tc-more [data-tpgive]').length,dock:document.querySelectorAll('#fdock [data-tpgive]').length,btn:!!b,sum:d?d.querySelector('summary').textContent:''};}""",id_martroi)
            ok(L+"« Rendre à la régulation » : une entrée par demande dans le tiroir « Plus » de la carte, rien dans la barre du bas",g["more"] and g["n"]==4 and g["dock"]==0 and g["btn"] and "rendre une demande" in g["sum"],g)
            await page.evaluate("()=>{const d=document.querySelector('.tcard details.tc-more');if(d)d.scrollIntoView({block:'start'});}"); await page.wait_for_timeout(200)
            await page.screenshot(path=os.path.join(OUT,"fiches-tournee-375-2-plus.png"))
            await page.click(f'.tc-more [data-tpgive="{id_martroi}"]'); await page.wait_for_timeout(150)
            k1=await page.evaluate(f"!!tourStop('{id_martroi}')&&/Confirmer/.test((document.querySelector('.tc-more [data-tpgive=\"{id_martroi}\"]')||{{}}).textContent||'')")
            await page.click(f'.tc-more [data-tpgive="{id_martroi}"]'); await page.wait_for_timeout(400)
            k2=await page.evaluate(f"()=>({{gone:!tourStop('{id_martroi}'),given:(TOUR.given||[]).some(g=>/Mme N/.test(g.lbl)),rows:document.querySelectorAll('.tp-newrow').length,fil:(document.getElementById('fdock')||{{dataset:{{}}}}).dataset.fil}})")
            ok(L+"« Rendre à la régulation » : confirmée au 2e toucher, demande retirée et tracée, 3 lignes restantes, barre inchangée",k1 and k2["gone"] and k2["given"] and k2["rows"]==3 and k2["fil"]=="route",(k1,k2))
            # ---------- retrait d'une visite : recalcul silencieux, ligne discrète si l'ordre change ----------
            d1=await page.evaluate("""async(id)=>{window.__tO=window.tourOptimize;window.__n=0;window.tourOptimize=async function(){window.__n++;return window.__tO.apply(this,arguments);};
              state.view='tour';TOUR.order=TOUR.order.slice().reverse();TOUR.autoChg=null;render();await new Promise(r=>setTimeout(r,150));const b=document.querySelector('[data-tdel="'+id+'"]');if(!b)return {err:'bouton Retirer absent'};b.click();
              for(let i=0;i<60&&!(window.__n&&!TOUR.busy&&TOUR.autoTs);i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,300));
              return {n:window.__n,gone:!tourStop(id),chg:TOUR.autoChg,tr:(document.querySelector('.tr-auto')||{}).textContent||'',toast:(document.getElementById('toast')||{}).textContent||'',view:state.view};}""",r2["id"])
            ok(L+"« Retirer » une visite : ordre recalculé aussitôt, sans question ni message",d1.get("n",0)>=1 and d1.get("gone") and d1.get("view")=="tour" and "?" not in d1.get("toast",""),{k:d1.get(k) for k in ("n","gone","toast")})
            ok(L+"ordre modifié → une ligne discrète « Ordre mis à jour à HH h MM · prochaine visite : … »",d1.get("chg") and "Ordre mis à jour à" in d1.get("tr","") and "prochaine visite" in d1.get("tr",""),{k:d1.get(k) for k in ("chg","tr")})
            c1=await page.evaluate("()=>{state.view='';render();const e=document.querySelector('.tcard .tc-chg');return e?e.textContent:'';}")
            ok(L+"écran principal : la même ligne discrète sous la carte de visite","Ordre mis à jour à" in c1,c1)
            await page.evaluate("window.scrollTo(0,0)"); await page.wait_for_timeout(150)
            await page.screenshot(path=os.path.join(OUT,"fiches-tournee-375-3-ordre.png"))
            # ---------- validation du patient : recalcul silencieux ----------
            v1=await page.evaluate("""async()=>{const n0=window.__n;patientValidate(true);for(let i=0;i<60&&window.__n===n0;i++)await new Promise(r=>setTimeout(r,100));await new Promise(r=>setTimeout(r,200));return {n:window.__n-n0,view:state.view,done:!!tourStop('w1').done,cur:TOUR.current};}""")
            ok(L+"patient validé : visite faite, ordre recalculé de lui-même (mode test : journal intact)",v1["n"]>=1 and v1["view"]=="valid" and v1["done"] and v1["cur"]=="",v1)
            await page.evaluate("()=>{window.tourOptimize=window.__tO;state.view='tour';render();}"); await page.wait_for_timeout(300)
            await page.screenshot(path=os.path.join(OUT,"fiches-tournee-375-4-tournee.png"),full_page=False)
            tr=await page.evaluate("()=>({appel:[...document.querySelectorAll('.trow .hint')].some(e=>/appel \\d{1,2} h \\d{2}/.test(e.textContent)),rows:document.querySelectorAll('.trow').length})")
            ok(L+"écran Tournée : l'heure d'appel de la fiche est écrite sur la ligne du patient (« appel HH h MM »)",tr["appel"],tr)
            ok(L+"aucune erreur JavaScript",not errors,errors[:3])
            await ctx.close(); await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    with open(os.path.join(ROOT,"tests","resultats_fiches_tournee.md"),"w",encoding="utf-8") as f:
        f.write("# Fiches MccMissionSG et tournée sans question (09/11/2026)\n\n"+f"{n}/{len(results)} tests OK\n\n"+"\n".join(("- OK " if r[1] else "- FAIL ")+r[0]+("" if r[1] else " — "+str(r[2])[:300]) for r in results)+"\n")
    sys.exit(0 if n==len(results) else 1)
if __name__=="__main__": asyncio.run(run())
