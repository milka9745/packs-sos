# -*- coding: utf-8 -*-
"""12/11/2026 — navigation et tournée (régression : « Naviguer » devenu « Localiser l'adresse », inactif).
1. « Naviguer » toujours en bas à gauche de l'étape En route, libellé fixe, avec ou sans coordonnées (adresse en clair normalisée : « 25BIS » → « 25 bis »,
   code postal et commune ajoutés) ; appli choisie une fois dans ⋯ (Waze / Plans / Google Maps), mémorisée, jamais de menu de choix pendant la tournée ;
   ouverture par window.location.href (window.open bloqué en mode écran d'accueil iOS) ; formats d'URL des trois applis, repli web de Google Maps.
2. Un toucher par patient : ▶ Commencer = ordre + guidage vers le 1er ; ✓ Valider (un seul toucher : confirmation du 18/10 retirée le 12/11) = visite suivante en cours + guidage ;
   retour en arrière : « Annuler » 30 s à l'horloge puis « ↩ Rouvrir NOM » en un toucher dans la carte ; arrivée automatique à moins
   de 150 m au retour dans Packs ; ordre recalculé en silence ; jamais d'attente du géocodage ni du réseau (réseau lent et hors connexion).
3. Autres boutons du parcours : Appeler, Je suis arrivé, Patient suivant (écran Patient validé), Naviguer depuis l'écran Tournée, la carte et la vue conduite.
Patients fictifs uniquement. Réseau simulé : géocodeur (Géoplateforme et ancienne adresse) et OSRM déterministes, tout le reste bloqué.
Lancer : python tests/test_navigation.py"""
import asyncio, os, re, json, math, subprocess, sys, time, urllib.parse
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8799
results=[]; TOUCHES={}
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])

IOS_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
# écran d'accueil iOS simulé : window.open bloqué (lève une erreur), navigator.standalone ; point d'ouverture navOpen remplacé pour relever les URL lancées
INIT=r"""try{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','false');localStorage.setItem('sos_design','garde');localStorage.setItem('sos_nav','waze');}catch(e){}
window.__nav=[];window.navOpen=function(u){window.__nav.push({u:u,t:Date.now()});};
try{Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});}catch(e){}
window.__openCalls=0;window.open=function(){window.__openCalls++;throw new Error('window.open bloqué (écran d\'accueil iOS)');};"""

async def unlock(page,base,uid="testnav"):
    await page.add_init_script(INIT)
    await page.goto(base+"index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=45000)
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

# Géocodeur simulé (adresses fictives) : trois adresses restent volontairement introuvables (REPUBLIQUE, BEAUHAIRE, GARE) pour éprouver le guidage par l'adresse
GEO={"CARMES":(47.900,1.900,"3 Rue des Carmes 45000 Orléans","Orléans","45000"),"BOURGOGNE":(47.902,1.911,"10 Rue de Bourgogne 45000 Orléans","Orléans","45000"),
     "CHANZY":(47.9029,1.9093,"44 Rue Chanzy 45000 Orléans","Orléans","45000"),"MARTROI":(47.9030,1.9090,"1 Place du Martroi 45000 Orléans","Orléans","45000")}
NOGEO=("REPUBLIQUE","BEAUHAIRE","GARE","INTROUVABLE")
SLOW={"s":0}
async def ban_mock(route):
    url=route.request.url; m=re.search(r"[?&]q=([^&]*)",url); q=urllib.parse.unquote_plus(m.group(1)) if m else ""
    if SLOW["s"]: await asyncio.sleep(SLOW["s"])
    if any(k in q.upper() for k in NOGEO): body={"type":"FeatureCollection","features":[]}
    else:
        hit=next((v for k,v in GEO.items() if k in q.upper()),(47.905,1.91,q,"Orléans","45000"))
        body={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[hit[1],hit[0]]},"properties":{"label":hit[2],"city":hit[3],"postcode":hit[4],"score":0.9}}]}
    await route.fulfill(status=200,content_type="application/json",body=json.dumps(body))
def hav(a,b):
    R=6371; r=math.radians
    dla=r(b[1]-a[1]); dlo=r(b[0]-a[0]); h=math.sin(dla/2)**2+math.cos(r(a[1]))*math.cos(r(b[1]))*math.sin(dlo/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))
async def osrm_mock(route):
    url=route.request.url; m=re.search(r"/(table|trip)/v1/driving/([^?]+)",url)
    if SLOW["s"]: await asyncio.sleep(SLOW["s"])
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
    await ctx.route(re.compile(r".*(data\.geopf\.fr/geocodage|api-adresse\.data\.gouv\.fr).*"),ban_mock)

# Tournée fictive : 5 patients ; p1 et p5 géocodés, p2 (« 25BIS »), p3 (sans code postal) et p4 (ni code postal ni commune) sans coordonnées
SET=r"""()=>{TESTMODE=true;newPatient();TOUR.base={lat:47.9029,lon:1.9093,label:'44 Rue Chanzy 45000 Orléans'};TOUR.origin='cabinet';TOUR.dest='';TOUR.destGeo=null;TOUR.manual=false;TOUR.cfg=null;TOUR.autoChg=null;TOUR.given=[];TOUR.unread=[];TOUR.consults=[];
 TOUR.current='';TOUR.legs=[];TOUR.total=null;TOUR.computed=0;TOUR.est=false;TOUR.lastDone='';TOUR.autoTs=0;
 const now=Date.now();
 TOUR.stops=[{id:'p1',addr:'3 RUE DES CARMES 45000 ORLEANS',label:'3 Rue des Carmes 45000 Orléans',lat:47.900,lon:1.900,city:'Orléans',nom:'DUPONT Jean',ddn:'03/04/1958',tel:'0612345678',motif:'fièvre',ts:now-40*60000,done:false},
  {id:'p2',addr:'25BIS RUE DE LA REPUBLIQUE 45000 ORLEANS',nom:'MARTIN Léa',ddn:'02/02/2022',tel:'0611111111',motif:'otite',ts:now-35*60000,done:false},
  {id:'p3',addr:'8 RUE CHARLES BEAUHAIRE SAINT-JEAN-DE-LA-RUELLE',nom:'LE GOFF Louis',ddn:'12/05/2019',tel:'0698765432',motif:'toux',ts:now-30*60000,done:false},
  {id:'p4',addr:'12 TER RUE DE LA GARE',nom:'BERNARD Luc',ddn:'04/04/1980',tel:'0622222222',motif:'malaise',ts:now-25*60000,done:false},
  {id:'p5',addr:'10 RUE DE BOURGOGNE 45000 ORLEANS',label:'10 Rue de Bourgogne 45000 Orléans',lat:47.902,lon:1.911,city:'Orléans',nom:'ROUX Anne',ddn:'02/02/1990',tel:'0644444444',motif:'angine',ts:now-20*60000,done:false}];
 TOUR.order=[];tourSave();state.cot=cotDefault();state.cot.lieu='visite';state.cot.auto=false;state.view='';window.__nav=[];render();return TOUR.stops.map(s=>s.id);}"""
DOCK=r"""()=>{const d=document.getElementById('fdock');if(!d)return null;const fa=[...d.querySelectorAll('.fa')].map(b=>{const q=b.getBoundingClientRect();return {t:b.textContent.replace(/\s+/g,' ').trim(),id:b.id,x:Math.round(q.left),w:Math.round(q.width),h:Math.round(q.height),main:b.classList.contains('fa-main'),now:b.classList.contains('act-now'),tag:b.tagName,href:b.getAttribute('href')||'',navgo:b.dataset.navgo||''};});
 return {st:d.dataset.fil,fa,cur:TOUR.current,view:state.view,nav:window.__nav.slice(),W:document.documentElement.clientWidth};}"""
WAIT=r"""async([cond,ms])=>{const f=new Function('return ('+cond+')');const t0=performance.now();while(performance.now()-t0<ms){if(f())return Math.round(performance.now()-t0);await new Promise(r=>setTimeout(r,40));}return -1;}"""
async def wait_cond(page,cond,ms=3000):
    return await page.evaluate(WAIT,[cond,ms])
async def touch(page,key,sel):
    TOUCHES[key]=TOUCHES.get(key,0)+1
    await page.click(sel); await page.wait_for_timeout(120)
async def shot(page,name):
    try: await page.screenshot(path=os.path.join(OUT,name))
    except Exception: pass
def q_of(u):
    m=re.search(r"[?&]q=([^&]*)",u); return urllib.parse.unquote(m.group(1)) if m else ""

async def acte(page):
    """acte médical simulé (hors compte des touchers de tournée) : fiche choisie, impression faite, compte rendu copié → étape Sortie"""
    await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>p.n==='Grippe / syndrome viral — adulte');render();}"); await page.wait_for_timeout(150)
    await page.evaluate("()=>{state.lastPrint={n:1,sent:true,ts:Date.now()};state.crCopied=true;render();}"); await page.wait_for_timeout(150)

UBAR=r"""()=>{const e=document.getElementById('undobar');return {t:e?e.textContent:'',vis:!!(e&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0)};}"""
ETAT=r"""(a)=>{const [prev,cur]=a;return {cur:TOUR.current,done:!!tourStop(prev).done,nextCur:!!tourStop(cur).cur,nextTodo:tourRemaining().some(s=>s.id===cur)&&!tourStop(cur).done,patient:state.patient,hist:VALID.hist.length,pending:VALID.hist.filter(v=>v.pending).length,
  reopened:!!(VALID.hist.find(v=>v.stopId===prev)||{}).reopened,fil:(document.getElementById('fdock')||{dataset:{}}).dataset.fil,bar:!!document.getElementById('undobar')};}"""
async def retour_rouvrir(page,L,prev,cur):
    """retour en arrière après le délai : « ↩ Rouvrir NOM » en un toucher dans la carte (validation conservée, version tracée), puis nouvelle validation en un toucher"""
    nom=await page.evaluate("VALID.last.patient")
    await page.evaluate("VALID.undoUntil=Date.now()-1"); await page.wait_for_timeout(900)
    r=await page.evaluate("()=>({bar:!!document.getElementById('undobar'),btn:(document.getElementById('tc_reopen')||{}).textContent||'',list:(document.getElementById('tc_vlist')||{}).textContent||''})")
    ok(L+"délai écoulé : la barre s'efface, la carte propose « ↩ Rouvrir NOM » (un toucher) et « Validés (n) »",not r["bar"] and r["btn"]=="↩ Rouvrir "+nom and r["list"].startswith("Validés ("),r)
    h=await page.evaluate("VALID.hist.length")
    await touch(page,"(retour en arrière) ↩ Rouvrir le patient validé","#tc_reopen"); await page.wait_for_timeout(400)
    st=await page.evaluate(ETAT,[prev,cur])
    ok(L+f"↩ Rouvrir : {prev} redevient en cours (documents tels quels, étape Sortie), {cur} redevient à faire sans être « mis de côté », validation conservée et marquée rouverte",
       st["cur"]==prev and not st["done"] and not st["nextCur"] and st["nextTodo"] and st["patient"]==nom and st["reopened"] and st["hist"]==h and st["pending"]==0 and st["fil"]=="sortie" and not st["bar"],st)
    n1=await page.evaluate("window.__nav.length")
    await touch(page,"(retour en arrière) ✓ Valider de nouveau","#fdock #tc_valid")
    ms=await wait_cond(page,f"TOUR.current==='{cur}'&&window.__nav.length>{n1}",3000)
    st=await page.evaluate(f"()=>({{rev:VALID.hist[0].rev,stop:VALID.hist[0].stopId,hist:VALID.hist.length,done:!!tourStop('{prev}').done}})")
    ok(L+f"nouvelle validation en un toucher : version 2 tracée (la validation initiale est conservée), {cur} de nouveau en cours et guidage lancé",ms>=0 and st["rev"]==2 and st["stop"]==prev and st["hist"]==h+1 and st["done"],st)
async def retour_annuler(page,L,prev,cur,h0):
    """retour en arrière dans les 30 s : « Annuler » = comme si la validation n'avait pas eu lieu, puis nouvelle validation en un toucher"""
    nom=await page.evaluate("VALID.last.patient")
    await touch(page,"(retour en arrière) Annuler (dans les 30 s)","#undo_go"); await page.wait_for_timeout(400)
    st=await page.evaluate(ETAT,[prev,cur])
    ok(L+f"Annuler : {prev} redevient en cours à l'étape Sortie, {cur} redevient à faire sans être « mis de côté », la validation disparaît de l'historique",
       st["cur"]==prev and not st["done"] and not st["nextCur"] and st["nextTodo"] and st["patient"]==nom and st["hist"]==h0 and st["pending"]==0 and st["fil"]=="sortie" and not st["bar"],st)
    n1=await page.evaluate("window.__nav.length")
    await touch(page,"(retour en arrière) ✓ Valider de nouveau","#fdock #tc_valid")
    ms=await wait_cond(page,f"TOUR.current==='{cur}'&&window.__nav.length>{n1}",3000)
    st=await page.evaluate("()=>({rev:VALID.hist[0].rev,stop:VALID.hist[0].stopId,hist:VALID.hist.length})")
    ok(L+f"nouvelle validation en un toucher : version 1 (aucune trace de l'essai annulé), {cur} de nouveau en cours et guidage lancé",ms>=0 and st["rev"]==1 and st["stop"]==prev and st["hist"]==h0+1,st)

async def parcours(b,base):
    """iPhone 375 × 812, tactile, écran d'accueil : tournée de 5 patients de bout en bout en comptant les touchers"""
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=IOS_UA,geolocation={"latitude":47.95,"longitude":2.0},permissions=["geolocation"])
    await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,base); L="iPhone écran d'accueil : "
    ids=await page.evaluate(SET); await page.wait_for_timeout(300)
    d=await page.evaluate(DOCK)
    ok(L+"étape Demande : « ▶ Lancer la tournée » en action principale",d and d["st"]=="demande" and any(f["id"]=="tc_begin" and f["main"] for f in d["fa"]),d)
    # ▶ un toucher : première visite en cours + guidage, sans attendre le réseau
    t0=time.time(); await touch(page,"▶ Lancer la tournée","#fdock #tc_begin")
    ms=await wait_cond(page,"window.__nav.length>=1&&!!TOUR.current",3000)
    d=await page.evaluate(DOCK)
    cur=await page.evaluate("()=>{const s=tourStop(TOUR.current);return {id:s.id,lat:s.lat||null,lon:s.lon||null,url:navUrl('waze',s),nom:s.nom};}")
    ok(L+"▶ : visite en cours et guidage lancé en un toucher (moins de 1 s), patient le plus proche du cabinet (coordonnées connues)",ms>=0 and ms<1000 and cur["id"]=="p5" and d["st"]=="route",{"ms":ms,"cur":cur,"nav":d and d["nav"]})
    ok(L+"▶ : URL Waze avec les coordonnées (ll=LAT,LON&navigate=yes), identique à navUrl",d and len(d["nav"])==1 and d["nav"][0]["u"]==cur["url"] and d["nav"][0]["u"].startswith("https://waze.com/ul?ll=47.902,1.911&navigate=yes"),d and d["nav"])
    nav=[f for f in d["fa"] if f["id"]=="fa_nav"]
    ok(L+"En route : « Naviguer » en bas à gauche, libellé fixe, bouton (pas de lien), sans nom d'appli, puis Appeler, puis Je suis arrivé",len(nav)==1 and d["fa"][0]["id"]=="fa_nav" and re.sub(r"^[^\wÀ-ÿ]+","",nav[0]["t"])=="Naviguer" and nav[0]["tag"]=="BUTTON" and nav[0]["href"]=="" and d["fa"][1]["t"].endswith("Appeler") and d["fa"][2]["id"]=="tc_arrive" and d["fa"][2]["main"],d["fa"])
    ok(L+"En route : « Appeler » = lien tel: du patient en cours",d["fa"][1]["href"]=="tel:0644444444")
    ok(L+"aucun menu de choix d'appli dans la tournée (seulement dans ⋯)",await page.evaluate("document.querySelectorAll('[data-navpref]:not(#jmenu [data-navpref])').length===0"))
    await shot(page,"nav-barre-en-route-iphone.png")
    # retour dans Packs : loin de l'adresse → le bouton reste ; à moins de 150 m → Arrivé sans toucher
    await page.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); await page.wait_for_timeout(1200)
    st=await page.evaluate("({arr:!!tourStop(TOUR.current).tArr,btn:!!document.querySelector('#fdock #tc_arrive')})")
    ok(L+"retour dans Packs loin de l'adresse (5 km) : rien ne change, « Je suis arrivé » reste",not st["arr"] and st["btn"],st)
    await ctx.set_geolocation({"latitude":47.9025,"longitude":1.9105}); await page.evaluate("NAV_CHK=0;document.dispatchEvent(new Event('visibilitychange'))")
    ms=await wait_cond(page,"!!tourStop(TOUR.current).tArr",4000)
    d=await page.evaluate(DOCK); tt=await page.evaluate("(document.getElementById('toast')||{}).textContent||''")
    ok(L+"retour dans Packs à moins de 150 m (60 m) : passage seul à « Sur place », message « arrivée enregistrée »",ms>=0 and d["st"]=="place" and "150 m" in tt,{"ms":ms,"st":d and d["st"],"toast":tt})
    await shot(page,"nav-arrivee-auto-iphone.png")
    # acte médical (non compté), puis ✓ Valider (un seul toucher) → visite suivante en cours + guidage ; retour en arrière : Annuler (30 s, horloge) puis ↩ Rouvrir (carte)
    await acte(page)
    d=await page.evaluate(DOCK)
    ok(L+"Sortie : « ✓ Valider · patient suivant » en action principale",d and d["st"]=="sortie" and any(f["id"]=="tc_valid" and f["main"] for f in d["fa"]),d)
    seq=[]
    for n,(exp_id,exp_q) in enumerate([("p1",""),("p2","25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS"),("p3","8 RUE CHARLES BEAUHAIRE 45140 SAINT-JEAN-DE-LA-RUELLE"),("p4","12 ter RUE DE LA GARE 45000 Orléans"),(None,"")]):
        n0=await page.evaluate("window.__nav.length"); prev=await page.evaluate("TOUR.current"); h0=await page.evaluate("VALID.hist.length")
        await touch(page,"✓ Valider · patient suivant (un seul toucher)","#fdock #tc_valid")
        if exp_id:
            ms=await wait_cond(page,f"TOUR.current==='{exp_id}'&&window.__nav.length>{n0}",3000)
            d=await page.evaluate(DOCK); u=d["nav"][-1]["u"] if d and d["nav"] else ""
            ub=await page.evaluate(UBAR); undo=ub["t"]
            ok(L+f"validation {n+1} en un seul toucher (plus de « Confirmer ») : patient précédent fait, visite suivante {exp_id} en cours et guidage lancé, en route (pas d'écran intermédiaire), barre « Annuler (30 s) » visible",
               ms>=0 and d["st"]=="route" and d["view"]=="" and await page.evaluate(f"tourStop('{prev}').done") and re.search(r"Annuler \((29|30) s\)",undo) and "en route vers" in undo and ub["vis"],{"ms":ms,"st":d and d["st"],"undo":undo[:80],"vis":ub["vis"]})
            if exp_q: ok(L+f"{exp_id} sans coordonnées : guidage par l'adresse en clair normalisée « {exp_q} » (Waze ?q=…)",u.startswith("https://waze.com/ul?q=") and q_of(u)==exp_q and u.endswith("&navigate=yes"),u)
            else: ok(L+f"{exp_id} : guidage par les coordonnées",u.startswith("https://waze.com/ul?ll=47.9,1.9&navigate=yes"),u)
            seq.append(exp_id)
            if n==0:
                await shot(page,"nav-valide-suivant-iphone.png")
                # compte à rebours lu sur l'horloge : l'échéance avancée de 20 s se lit au tic suivant (retour de l'appli de navigation : minuteurs suspendus, délai exact)
                await page.evaluate("VALID.undoUntil-=20000"); await page.wait_for_timeout(700)
                t=await page.evaluate("(document.getElementById('undo_go')||{}).textContent||''")
                ok(L+"barre d'annulation : compte à rebours lu sur l'horloge (échéance avancée de 20 s → « Annuler (9 s) » au tic suivant)",re.search(r"Annuler \(([5-9]|10) s\)",t),t)
            if n==1: await retour_rouvrir(page,L,prev,exp_id)
            if n==2: await retour_annuler(page,L,prev,exp_id,h0)
            # arrivée : automatique si l'adresse est géocodée, sinon le bouton reste et il faut un toucher
            s=await page.evaluate("()=>{const s=tourStop(TOUR.current);return {lat:s.lat||null,lon:s.lon||null};}")
            if s["lat"]:
                await ctx.set_geolocation({"latitude":s["lat"]+0.0005,"longitude":s["lon"]}); await page.evaluate("NAV_CHK=0;document.dispatchEvent(new Event('visibilitychange'))")
                ms=await wait_cond(page,"!!tourStop(TOUR.current).tArr",4000); ok(L+f"{exp_id} : arrivée automatique (55 m)",ms>=0,ms)
            else:
                await page.evaluate("NAV_CHK=0;document.dispatchEvent(new Event('visibilitychange'))"); await page.wait_for_timeout(600)
                st=await page.evaluate("({arr:!!tourStop(TOUR.current).tArr,btn:!!document.querySelector('#fdock #tc_arrive')})")
                ok(L+f"{exp_id} sans coordonnées : pas d'arrivée automatique possible, « Je suis arrivé » reste",not st["arr"] and st["btn"],st)
                await touch(page,"✓ Je suis arrivé (adresse non géocodée)","#fdock #tc_arrive")
                ok(L+f"{exp_id} : « Je suis arrivé » → Sur place",await page.evaluate("!!tourStop(TOUR.current).tArr&&document.getElementById('fdock').dataset.fil==='place'"))
            await acte(page)
        else:
            await page.wait_for_timeout(500)
            fin=await page.evaluate("({view:state.view,cur:TOUR.current,done:TOUR.stops.filter(s=>s.done).length,nav:window.__nav.length,txt:document.body.innerText})")
            ok(L+"dernière validation : écran « Patient validé », tournée terminée, aucun guidage lancé",fin["view"]=="valid" and fin["cur"]=="" and fin["done"]==5 and fin["nav"]==n0 and "tournée terminée" in fin["txt"],{k:fin[k] for k in ("view","cur","done","nav")})
    ok(L+"ordre réel de la tournée après le premier patient : p1 (géocodé, le plus proche), puis p2, p3, p4 dans l'ordre des demandes",seq==["p1","p2","p3","p4"],seq)
    ok(L+"recalcul silencieux après chaque validation (horodatage de l'ordre automatique posé, sans fenêtre ni question)",await page.evaluate("!!TOUR.autoTs&&!document.querySelector('#aiover,.aibox')"),await page.evaluate("TOUR.autoTs"))
    ok(L+"window.open jamais appelé (écran d'accueil iOS : tout passe par window.location.href)",await page.evaluate("window.__openCalls===0"))
    ok(L+"aucune erreur JavaScript",not errs,errs[:3])
    await ctx.close()

async def boutons(b,base):
    """autres boutons du parcours Visite et autres accès à « Naviguer » : écran Tournée, carte, vue conduite, Patient suivant, Express"""
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=IOS_UA,geolocation={"latitude":47.95,"longitude":2.0},permissions=["geolocation"])
    await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,base); L="iPhone boutons : "
    await page.evaluate(SET); await page.evaluate("window.tourOptimize=async()=>{};TOUR.order=['p1','p5','p2','p3','p4'];TOUR.computed=Date.now();tourSave();render();"); await page.wait_for_timeout(200)
    # menu ⋯ : choix de l'appli, mémorisé
    await page.click("#more_btn"); await page.wait_for_timeout(250)
    m=await page.evaluate("()=>{const b=[...document.querySelectorAll('#jmenu [data-navpref]')];return {n:b.length,t:b.map(x=>x.textContent.replace(/activé|désactivé/g,'').trim()),on:b.filter(x=>x.getAttribute('aria-pressed')==='true').map(x=>x.dataset.navpref)};}")
    ok(L+"menu ⋯ : « Navigation » avec Waze, Plans, Google Maps ; Waze activé par défaut",m["n"]==3 and m["t"]==["Waze","Plans","Google Maps"] and m["on"]==["waze"],m)
    await shot(page,"nav-menu-appli-iphone.png")
    await page.click("#jmenu [data-navpref='plans']"); await page.wait_for_timeout(300)
    ok(L+"Plans choisi : mémorisé (sos_nav), message « Guidage avec Plans »",await page.evaluate("localStorage.getItem('sos_nav')==='plans'&&navPref()==='plans'&&/Guidage avec Plans/.test((document.getElementById('toast')||{}).textContent||'')"))
    await page.click("#more_btn"); await page.wait_for_timeout(200)
    ok(L+"menu ⋯ rouvert : Plans marqué activé",await page.evaluate("(document.querySelector('#jmenu [data-navpref=plans]')||{}).getAttribute&&document.querySelector('#jmenu [data-navpref=plans]').getAttribute('aria-pressed')==='true'"))
    await page.evaluate("document.getElementById('jmenu').hidden=true"); await page.evaluate("localStorage.setItem('sos_nav','waze');render();"); await page.wait_for_timeout(150)
    # écran Tournée : un seul « Naviguer » par ligne (appli du menu), trajet complet par bouton, Appeler et Patient en cours intacts
    await page.evaluate("state.view='tour';render();"); await page.wait_for_timeout(700)
    r=await page.evaluate("()=>{const rows=[...document.querySelectorAll('.jlist .trow')];return {n:rows.length,nav:rows.map(x=>x.querySelectorAll('[data-navgo]').length),old:document.querySelectorAll('.jlist a.nav,.jlist a[target=_blank]').length,txt:[...document.querySelectorAll('.jlist [data-navgo]')].map(x=>x.textContent.trim()),full:!!document.querySelector('#tr_full[data-navopen]'),use:document.querySelectorAll('.jlist [data-tuse]').length,call:document.querySelectorAll('.jlist a[href^=\"tel:\"]').length};}")
    ok(L+"écran Tournée : un bouton « Naviguer » par arrêt (coordonnées ou non), plus de liens Waze / Maps / Plans, « Patient en cours » et « Appeler » conservés",r["n"]==5 and r["nav"]==[1]*5 and r["old"]==0 and all(t.endswith("Naviguer") for t in r["txt"]) and r["use"]==5 and r["call"]==5,r)
    n0=await page.evaluate("window.__nav.length"); await page.click(".jlist .trow [data-navgo='p3']"); await page.wait_for_timeout(200)
    u=await page.evaluate("window.__nav.length?window.__nav[window.__nav.length-1].u:''")
    ok(L+"écran Tournée : « Naviguer » sur un arrêt non géocodé lance l'adresse normalisée (code postal ajouté)",await page.evaluate("window.__nav.length")==n0+1 and q_of(u)=="8 RUE CHARLES BEAUHAIRE 45140 SAINT-JEAN-DE-LA-RUELLE",u)
    await page.click("#tr_full"); await page.wait_for_timeout(200)
    u=await page.evaluate("window.__nav[window.__nav.length-1].u")
    ok(L+"écran Tournée : « Trajet complet (Google Maps) » ouvert par location.href",u.startswith("https://www.google.com/maps/dir/?api=1&destination=") and "waypoints" in u,u)
    await shot(page,"nav-tournee-ecran-iphone.png")
    # carte : fenêtre d'un arrêt → Naviguer
    mp=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));for(let i=0;i<40&&!(MAP.marks&&MAP.marks.length);i++)await w(100);const mk=(MAP.marks||[]).find(m=>m.getPopup&&m.getPopup()&&/data-navgo="p1"/.test(m.getPopup().getContent()));if(!mk)return {marks:(MAP.marks||[]).length};mk.openPopup();await w(300);const b=document.querySelector('.leaflet-popup [data-navgo]');const n0=window.__nav.length;if(b)b.click();await w(200);return {marks:MAP.marks.length,btn:!!b,txt:b?b.textContent.trim():'',old:document.querySelectorAll('.leaflet-popup a[target=_blank]').length,launched:window.__nav.length===n0+1,u:window.__nav.length?window.__nav[window.__nav.length-1].u:''};}""")
    ok(L+"carte : fenêtre d'un arrêt → bouton « Naviguer » (plus de lien), guidage lancé",mp.get("btn") and mp.get("launched") and mp.get("old")==0 and mp["u"].startswith("https://waze.com/ul?ll=47.9,1.9"),mp)
    await shot(page,"nav-carte-popup-iphone.png")
    # Patient en cours depuis l'écran Tournée, puis vue conduite
    await page.evaluate("tourUse('p1');state.view='drive';render();"); await page.wait_for_timeout(300)
    dv=await page.evaluate("()=>{const z=[...document.querySelectorAll('.drive .dv-zone')];return {z:z.map(x=>({cls:x.className,nav:[...x.querySelectorAll('[data-navgo]')].map(b=>b.textContent.trim()),call:x.querySelectorAll('[data-tpcall]').length,arr:x.querySelectorAll('#dv_arr').length})),old:document.querySelectorAll('.drive a[target=_blank]').length};}")
    ok(L+"vue conduite : patient actuel et suivant avec « Naviguer » (bouton), Appeler, « Je suis arrivé » sur l'actuel",len(dv["z"])==2 and dv["z"][0]["nav"]==["🧭 Naviguer"] and dv["z"][1]["nav"]==["🧭 Naviguer"] and dv["z"][0]["call"]==1 and dv["z"][0]["arr"]==1 and dv["old"]==0,dv)
    n0=await page.evaluate("window.__nav.length"); await page.click(".drive .dv-zone.now [data-navgo]"); await page.wait_for_timeout(200)
    ok(L+"vue conduite : « Naviguer » lance le guidage et reste en vue conduite",await page.evaluate("window.__nav.length")==n0+1 and await page.evaluate("state.view==='drive'"))
    await shot(page,"nav-conduite-iphone.png")
    await page.click("#dv_arr"); await page.wait_for_timeout(300)
    ok(L+"vue conduite : « Je suis arrivé » → Sur place",await page.evaluate("!!tourStop('p1').tArr&&state.view===''&&document.getElementById('fdock').dataset.fil==='place'"))
    # écran « Patient validé » (validation depuis l'écran Tournée) : « Patient suivant » = visite suivante + guidage
    await acte(page); await page.evaluate("patientValidate(true);"); await page.wait_for_timeout(300)
    ok(L+"écran Patient validé : prochain arrêt annoncé avec un bouton « Naviguer »",await page.evaluate("state.view==='valid'&&!!document.querySelector('.vnext [data-navgo]')&&!!document.querySelector('#vd_next')"))
    n0=await page.evaluate("window.__nav.length"); await page.click("#vd_next"); await page.wait_for_timeout(400)
    ok(L+"« Patient suivant » : visite suivante en cours, étape En route, guidage lancé",await page.evaluate(f"TOUR.current==='p5'&&document.getElementById('fdock').dataset.fil==='route'&&window.__nav.length==={n0+1}"))
    # Express : la rangée du patient lance aussi le guidage (bouton, pas de lien), même sans coordonnées
    await page.evaluate("localStorage.setItem('sos_xp','true');state.view='';newPatient();TOUR.current='';state.cot=cotDefault();state.cot.lieu='visite';render();"); await page.wait_for_timeout(400)
    xp=await page.evaluate("()=>{const r=[...document.querySelectorAll('.xp-home [data-xpopen]')];return {n:r.length,nav:r.filter(x=>x.dataset.navgo).length,a:r.filter(x=>x.tagName==='A').length};}")
    ok(L+"Express : chaque patient de la liste lance le guidage d'un toucher (bouton, pas de lien), avec ou sans coordonnées",xp["n"]>=3 and xp["nav"]==xp["n"] and xp["a"]==0,xp)
    await page.evaluate("localStorage.setItem('sos_xp','false');render();")
    ok(L+"window.open jamais appelé",await page.evaluate("window.__openCalls===0"))
    ok(L+"aucune erreur JavaScript",not errs,errs[:3])
    await ctx.close()

async def formats(b,base):
    """les trois applis et l'adresse normalisée (iPhone) ; repli web de Google Maps ; variantes ordinateur ; menu ⋯ de l'ordinateur"""
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=IOS_UA)
    await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await unlock(page,base); L="formats iPhone : "
    await page.evaluate(SET)
    A=await page.evaluate("""()=>{const c={id:'c',lat:47.9,lon:1.9,label:'3 Rue des Carmes 45000 Orléans'},t={id:'t',addr:'25BIS RUE DE LA REPUBLIQUE 45000 ORLEANS'};
      return {ios:tpIsIOS(),wc:navUrl('waze',c),wt:navUrl('waze',t),pc:navUrl('plans',c),pt:navUrl('plans',t),gc:navUrl('maps',c),gt:navUrl('maps',t),fc:navFallbackUrl('maps',c),fw:navFallbackUrl('waze',c),
       a1:navAddr({addr:'25BIS RUE DE LA REPUBLIQUE 45000 ORLEANS'}),a2:navAddr({addr:'12 TER RUE DE LA GARE'}),a3:navAddr({addr:'8 RUE CHARLES BEAUHAIRE SAINT-JEAN-DE-LA-RUELLE'}),a4:navAddr({addr:'5 avenue de Verdun, Fleury les Aubrais'}),
       a5:navAddr({addr:'3 rue des Lilas 45770'}),a6:navAddr({addr:'3 rue des Lilas 45400'}),a7:navAddr({addr:'4 rue du Port',city:'Olivet'}),a8:navAddr({addr:'x',label:'10 Rue de Bourgogne 45000 Orléans'}),a9:navAddr({addr:'7 quater rue Royale 45000 ORLÉANS'}),a10:navAddr({addr:'2 rue de la Mairie, Saint-Pryvé-Saint-Mesmin'})};}""")
    ok(L+"Waze : ll=LAT,LON&navigate=yes avec coordonnées, sinon ?q=ADRESSE&navigate=yes",A["ios"] and A["wc"]=="https://waze.com/ul?ll=47.9,1.9&navigate=yes" and A["wt"]=="https://waze.com/ul?q="+urllib.parse.quote("25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS")+"&navigate=yes",A)
    ok(L+"Plans : maps://?daddr=…&dirflg=d (coordonnées ou adresse)",A["pc"]=="maps://?daddr=47.9,1.9&dirflg=d" and A["pt"]=="maps://?daddr="+urllib.parse.quote("25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS")+"&dirflg=d",A)
    ok(L+"Google Maps : comgooglemaps://?daddr=…&directionsmode=driving, repli https://www.google.com/maps/dir/?api=1&destination=… (Waze : pas de repli)",A["gc"]=="comgooglemaps://?daddr=47.9,1.9&directionsmode=driving" and A["gt"].startswith("comgooglemaps://?daddr="+urllib.parse.quote("25 bis")) and A["fc"]=="https://www.google.com/maps/dir/?api=1&destination=47.9,1.9&travelmode=driving" and A["fw"]=="",A)
    ok(L+"adresse normalisée : « 25BIS » → « 25 bis », « TER », « quater » ; code postal et commune ajoutés s'ils manquent (commune reconnue, commune du géocodage, sinon Orléans) ; code postal partagé sans commune imposée",
       A["a1"]=="25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS" and A["a2"]=="12 ter RUE DE LA GARE 45000 Orléans" and A["a3"]=="8 RUE CHARLES BEAUHAIRE 45140 SAINT-JEAN-DE-LA-RUELLE" and A["a4"]=="5 avenue de Verdun, 45400 Fleury les Aubrais" and A["a5"]=="3 rue des Lilas 45770 Saran" and A["a6"]=="3 rue des Lilas 45400" and A["a7"]=="4 rue du Port 45160 Olivet" and A["a8"]=="10 Rue de Bourgogne 45000 Orléans" and A["a9"]=="7 quater rue Royale 45000 ORLÉANS" and A["a10"]=="2 rue de la Mairie, 45750 Saint-Pryvé-Saint-Mesmin",A)
    # repli Google Maps : schéma d'abord, page encore visible 1,5 s après → adresse web
    fb=await page.evaluate("""async()=>{localStorage.setItem('sos_nav','maps');window.__nav=[];navGo(tourStop('p1'));const n1=window.__nav.length;await new Promise(r=>setTimeout(r,1900));localStorage.setItem('sos_nav','waze');return {n1,urls:window.__nav.map(x=>x.u),dt:window.__nav.length>1?window.__nav[1].t-window.__nav[0].t:null};}""")
    ok(L+"Google Maps : le schéma comgooglemaps:// part aussitôt ; la page restant visible, repli web après 1,5 s",fb["n1"]==1 and len(fb["urls"])==2 and fb["urls"][0].startswith("comgooglemaps://") and fb["urls"][1].startswith("https://www.google.com/maps/dir/") and fb["dt"] and 1300<=fb["dt"]<=2200,fb)
    ok(L+"aucune erreur JavaScript",not errs,errs[:3]); await ctx.close()
    # ordinateur
    ctx=await b.new_context(viewport={"width":1280,"height":900}); await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await unlock(page,base); L="ordinateur : "
    await page.evaluate(SET); await page.wait_for_timeout(200)
    await page.evaluate("state.view='tour';render();"); await page.wait_for_timeout(500)
    B=await page.evaluate("()=>{const c={id:'c',lat:47.9,lon:1.9};return {ios:tpIsIOS(),p:navUrl('plans',c),g:navUrl('maps',c),w:navUrl('waze',c),menu:[...document.querySelectorAll('#tp_set .navset [data-navpref]')].map(b=>b.textContent.replace(/activé|désactivé/g,'').trim()),on:(document.querySelector('#tp_set .navset [aria-pressed=true]')||{}).dataset,head:document.querySelectorAll('.jbar [data-navpref]').length};}")
    ok(L+"hors iPhone : Plans et Google Maps par leurs adresses web, Waze inchangé",not B["ios"] and B["p"]=="https://maps.apple.com/?daddr=47.9,1.9&dirflg=d" and B["g"]=="https://www.google.com/maps/dir/?api=1&destination=47.9,1.9&travelmode=driving" and B["w"]=="https://waze.com/ul?ll=47.9,1.9&navigate=yes",B)
    ok(L+"Tournée › Réglages : Navigation Waze / Plans / Google Maps, Waze activé ; rien dans l'en-tête (une seule ligne)",B["menu"]==["Waze","Plans","Google Maps"] and B["on"] and B["on"].get("navpref")=="waze" and B["head"]==0,B)
    await page.evaluate("()=>{const d=document.getElementById('tp_set');if(d){d.open=true;d.scrollIntoView({block:'center'});}}"); await page.wait_for_timeout(200); await shot(page,"nav-reglages-appli-ordinateur.png")
    await page.evaluate("document.querySelector('#tp_set .navset [data-navpref=maps]').click()"); await page.wait_for_timeout(300)
    ok(L+"choix Google Maps mémorisé",await page.evaluate("navPref()==='maps'"))
    await page.evaluate("localStorage.setItem('sos_nav','waze')")
    ok(L+"aucune erreur JavaScript",not errs,errs[:3]); await ctx.close()

async def reseau(b,base):
    """jamais d'attente : réseau lent (géocodeur et OSRM à 4 s) puis hors connexion"""
    SLOW["s"]=4
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=IOS_UA,geolocation={"latitude":47.95,"longitude":2.0},permissions=["geolocation"])
    await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await unlock(page,base); L="réseau lent (4 s par appel) : "
    await page.evaluate(SET); await page.wait_for_timeout(200)
    await page.click("#fdock #tc_begin")
    ms=await wait_cond(page,"window.__nav.length>=1&&!!TOUR.current",3000)
    ok(L+"▶ : guidage lancé en moins de 1 s sans attendre le géocodage ni l'ordre OSRM",ms>=0 and ms<1000,ms)
    cur0=await page.evaluate("TOUR.current")
    ms2=await wait_cond(page,"!TOUR.busy&&TOUR.status!=='calcul en cours…'",40000)
    st=await page.evaluate("({cur:TOUR.current,busy:TOUR.busy,status:TOUR.status,autoTs:TOUR.autoTs,fil:document.getElementById('fdock').dataset.fil})")
    ok(L+"recalcul en arrière-plan terminé seul (délais bornés), patient en cours inchangé, étape En route",ms2>=0 and st["cur"]==cur0 and not st["busy"] and st["fil"]=="route",{"ms":ms2,**st})
    SLOW["s"]=0
    ok(L+"aucune erreur JavaScript",not errs,errs[:3]); await ctx.close()
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=IOS_UA)
    await net(ctx); page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await unlock(page,base); L="hors connexion : "
    await page.evaluate(SET); await page.evaluate("TOUR.stops=TOUR.stops.filter(s=>!s.lat);TOUR.order=[];tourSave();render();"); await page.wait_for_timeout(200)
    await ctx.set_offline(True); await page.wait_for_timeout(200)
    await page.click("#fdock #tc_begin")
    ms=await wait_cond(page,"window.__nav.length>=1&&!!TOUR.current",3000)
    r=await page.evaluate("({cur:TOUR.current,u:window.__nav.length?window.__nav[0].u:'',busy:TOUR.busy,status:TOUR.status,online:navigator.onLine,fil:document.getElementById('fdock').dataset.fil,nav:!!document.querySelector('#fdock #fa_nav')})")
    ok(L+"▶ sans réseau ni coordonnées : guidage par l'adresse en clair, aussitôt, « Naviguer » présent, aucun calcul bloqué",ms>=0 and ms<1000 and r["u"].startswith("https://waze.com/ul?q=") and q_of(r["u"])=="25 bis RUE DE LA REPUBLIQUE 45000 ORLEANS" and not r["busy"] and r["fil"]=="route" and r["nav"] and r["online"] is False,{"ms":ms,**r})
    await shot(page,"nav-hors-connexion-iphone.png")
    await ctx.set_offline(False)
    ok(L+"aucune erreur JavaScript",not errs,errs[:3]); await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    HTML=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
    ok("source : plus de « Localiser l'adresse » ni de lien de navigation target=_blank ; ouverture par window.location.href","Localiser l'adresse" not in HTML and 'rel="noopener" href="${navUrl' not in HTML and "window.navOpen=function(u){if(tpIsIOS()){window.location.href=u;return;}" in HTML)
    ok("source : géocodeur Géoplateforme (IGN) en premier, ancienne adresse en secours, délai borné (AbortController)",'const BAN_URLS=["https://data.geopf.fr/geocodage/search","https://api-adresse.data.gouv.fr/search/"]' in HTML and "AbortController" in HTML.split("async function banFetch")[1][:400])
    ok("source : communes d'Orléans Métropole (23 couples) pour compléter les adresses",HTML.count('["Saint-Jean-de-Braye","45800"]')==1 and len(re.findall(r'\["[^"]+","45\d{3}"\]',HTML.split("const NAV_CP=")[1].split("\n")[0]))==23)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); base=f"http://localhost:{PORT}/"
            await parcours(b,base); await boutons(b,base); await formats(b,base); await reseau(b,base)
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    with open(os.path.join(ROOT,"tests","resultats_navigation.md"),"w",encoding="utf-8") as f:
        f.write("# Navigation et tournée — 12/11/2026\n\n")
        f.write("Touchers de tournée sur le parcours iPhone (5 patients fictifs, hors acte médical : fiche, impression ; les essais de retour en arrière sont comptés à part) :\n\n| Geste | Touchers |\n|---|---|\n")
        for k,v in TOUCHES.items(): f.write(f"| {k} | {v} |\n")
        tour={k:v for k,v in TOUCHES.items() if not k.startswith("(retour")}; tot=sum(tour.values()); f.write(f"| **Total tournée** | **{tot}** — soit {tot/5:.1f} par patient ; aucun toucher « Naviguer », « Patient suivant » ni « Confirmer » |\n\n")
        f.write(f"Résultat : {n}/{len(results)} tests OK\n\n| Test | Résultat |\n|---|---|\n")
        for name,c,info in results: f.write(f"| {name} | {'OK' if c else 'ÉCHEC — '+str(info)[:300]} |\n")
    print("touchers :",TOUCHES)
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
