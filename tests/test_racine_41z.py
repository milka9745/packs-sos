# -*- coding: utf-8 -*-
# Publication en racine (06/11/2026) : la version complète (branche ia, v41z) remplace l'outil de garde v41k à la racine du site.
# Sur un même navigateur (même origine, donc même stockage), vérifie que tout ce que la v41k a écrit — code (PIN) et session,
# profil (identité), journal, tournée, réglages — est retrouvé à l'identique par la nouvelle version, que le secours /v41k/ s'ouvre
# avec le même code sur les mêmes données, et que la racine porte la nouvelle version (numéro lisible, nouveau cache).
# Patients fictifs. Lancer : python tests/test_racine_41z.py <site_41k> <site_nouveau>   (sites = dossiers locaux)
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
OLD=sys.argv[1]; NEW=sys.argv[2]; PORT=8871; B=f"http://localhost:{PORT}/"
def _ver(d,dflt):  # 08/11/2026 : numéros lus dans les sites (l'outil de garde v41k n'avait pas de version.json)
    try: return json.load(open(os.path.join(d,"version.json"),encoding="utf-8")).get("version",dflt)
    except Exception: return dflt
OLDV=_ver(OLD,"41k"); NEWV=_ver(NEW,"41z")
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
def serve(d):
    p=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=d,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2); return p
async def create(page,uid):
    await page.goto(B+"index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(1000)
async def reopen(page,uid,path):
    """autre code de page sur les mêmes données : session reprise ou code demandé ; jamais d'écran de création"""
    await page.goto(B+path+"?r="+str(int(time.time()))); await page.wait_for_timeout(2500)
    creation=await page.locator("#pin2").count()>0
    if creation: return {"creation":True}
    asked=await page.locator("#pin1").count()>0
    if asked:
        await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.click("#pin_ok")
    try: await page.wait_for_selector("#lock",state="detached",timeout=15000)
    except Exception: pass
    await page.wait_for_timeout(1500)
    return {"creation":False,"pin":asked,"unlocked":await page.locator("#lock").count()==0}
WRITE="""async()=>{localStorage.setItem('sos_theme','night');localStorage.setItem('sos_bigtext','1');
 const id={on:true,nom:'Docteur ESSAI Spécimen',adeli:'000000000',assoc:['SOS Essai (fictif)'],stamp:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',kitId:'essai',created:Date.now(),since:Date.now(),bk:''};
 if(typeof secPut==='function')await secPut('sos_ident',id);else secSet('sos_ident',id);identApply(id); /* identité fictive, comme le fait identActivate */
 const add=(pat,ddn,sexe,re)=>{newPatient();Object.assign(state,{patient:pat,ddn:ddn,sexe:sexe});const i=PACKS.findIndex(p=>re.test(p.n));if(i<0)return 'fiche absente '+re;state.sel=i;journalUpsert(currentPack());return PACKS[i].n;};
 const a=add('ESSAI Première','01/01/1980','f',/^Lombalgie/);const b=add('ESSAI Deuxième','02/02/2015','h',/^Angine/);const c=add('ESSAI Troisième','03/03/1950','h',/^Gastro/);journalSave();
 const now=Date.now();TOUR.base={lat:47.9029,lon:1.9093,label:'cabinet'};TOUR.origin='cabinet';TOUR.order=['e1','e2','e3'];TOUR.legs=[];TOUR.computed=now;TOUR.current='';
 TOUR.stops=[{id:'e1',addr:'x',nom:'ESSAI Un',ddn:'01/01/1946',motif:'fièvre toux',tel:'0600000001',lat:47.90,lon:1.91,label:'10 Rue de Bourgogne 45000 Orléans',done:false,ts:now},{id:'e2',addr:'y',nom:'ESSAI Deux',ddn:'02/02/2022',motif:'otite',tel:'0600000002',lat:47.902,lon:1.905,label:'5 Rue Jeanne d Arc 45000 Orléans',done:false,ts:now},{id:'e3',addr:'z',nom:'ESSAI Trois',ddn:'03/03/1976',motif:'lombalgie',lat:47.91,lon:1.90,label:'3 Avenue de Paris 45000 Orléans',done:true,ts:now}];
 tourSave();newPatient();return {fiches:[a,b,c],n:JOURNAL.length};}"""
SNAP="""async()=>{const ls={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);ls[k]=localStorage.getItem(k);}
 const tour=await secGet('sos_tour',null);let ident=null;try{ident=identSnapshot();}catch(e){ident='ERR '+e.message;}const identStore=await secGet('sos_ident',null);
 return {ident:ident,identStore:identStore,on:IDENT.on,journal:JSON.parse(JSON.stringify(JOURNAL)),tour:tour,tourMem:{stops:TOUR.stops,order:TOUR.order,base:TOUR.base,origin:TOUR.origin},theme:localStorage.getItem('sos_theme'),big:localStorage.getItem('sos_bigtext'),ls:ls};}"""
def jd(a,b):
    """différences entre deux objets JSON (chemins), pour le rapport"""
    out=[]
    def walk(x,y,p):
        if type(x)!=type(y): out.append(p+" : type"); return
        if isinstance(x,dict):
            for k in set(x)|set(y):
                if k not in y: out.append(p+"/"+k+" : absent après")
                elif k not in x: out.append(p+"/"+k+" : ajouté après")
                else: walk(x[k],y[k],p+"/"+k)
        elif isinstance(x,list):
            if len(x)!=len(y): out.append(p+" : %d → %d éléments"%(len(x),len(y)))
            for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+"[%d]"%i)
        elif x!=y: out.append(p+" : %r → %r"%(str(x)[:40],str(y)[:40]))
    walk(a,b,""); return out
async def main():
    srv=serve(OLD)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,service_workers="block")
            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            # 1. version en service (41k) : code, identité de démonstration, journal, tournée, réglages
            await create(page,"garde")
            v0=await page.evaluate("fetch('version.json',{cache:'no-store'}).then(r=>r.json()).then(j=>j.version)")
            ok(f"{OLDV} : version en service chargée (version.json)",v0==OLDV,v0)
            ok("41k : pas d'Express (code de la racine actuelle)",OLDV!="41k" or await page.evaluate("typeof xpHTML")=="undefined")
            w=await page.evaluate(WRITE); await page.wait_for_timeout(1500)
            ok("41k : trois patients au journal, trois demandes à la tournée (fictifs)",w["n"]>=3 and all(not str(x).startswith("fiche absente") for x in w["fiches"]),w)
            for _ in range(20):
                if await page.evaluate("!!localStorage.getItem('sos_journal_enc')&&!!localStorage.getItem('sos_tour_enc')&&!!localStorage.getItem('sos_ident_enc')"): break
                await page.wait_for_timeout(300)
            A=await page.evaluate(SNAP)
            ok("41k : journal, tournée et identité écrits chiffrés (localStorage, clés _enc)",all(k in A["ls"] for k in ("sos_journal_enc","sos_tour_enc","sos_ident_enc","sos_sec")),sorted(A["ls"]))
            ok("41k : identité (fictive) chargée : nom, Adeli, association",isinstance(A["ident"],dict) and A["ident"].get("nom")=="Docteur ESSAI Spécimen" and A["ident"].get("adeli")=="000000000" and A["ident"].get("assoc"),A["ident"])
            # 2. bascule : le même site sert maintenant la nouvelle version (même origine : mêmes données)
            srv.terminate(); srv.wait(); srv=serve(NEW)
            r=await page.evaluate("fetch('version.json',{cache:'no-store'}).then(r=>r.json())")
            ok(f"racine : version.json de la nouvelle version ({NEWV})",r.get("version")==NEWV,r)
            ok("racine : numéro de version lisible dans version.json (label « 41z · JJ/MM HH:MM »)",re.match(r"^"+re.escape(NEWV)+r" · \d\d/\d\d \d\d:\d\d$",str(r.get("label",""))) is not None,r.get("label"))
            ok("racine : 2 ou 3 lignes « Ce qui change »",2<=len(r.get("notes",[]))<=3,r.get("notes"))
            sw=await page.evaluate("fetch('sw.js',{cache:'no-store'}).then(r=>r.text())")
            ok(f"racine : nouveau cache du service worker (packs-sos-v{NEWV}, plus v41k)",('const CACHE="packs-sos-v'+NEWV+'"') in sw and "v41k" not in sw.split("\n")[1],sw[:160])
            op=await reopen(page,"garde","index.html")
            ok("nouvelle version : pas d'écran de création de code (l'utilisateur et son code sont reconnus)",not op.get("creation") and op.get("unlocked"),op)
            print("    (session reprise sans code : %s)"%("oui" if not op.get("pin") else "non, code demandé et accepté"))
            ok("nouvelle version : code de la branche ia (Express présent)",await page.evaluate("typeof xpHTML")=="function")
            av=await page.evaluate("appVerFull()")
            ok("nouvelle version : « v41z · main · JJ/MM HH:MM » affiché",re.match(r"^v"+re.escape(NEWV)+r" · main · \d\d/\d\d \d\d:\d\d$",av) is not None,av)
            await page.wait_for_timeout(1500)
            Bs=await page.evaluate(SNAP)
            ok("profil (identité) identique : nom, Adeli, association, cachet, profil actif",Bs["on"] and A["ident"]==Bs["ident"] and A["ident"].get("nom")=="Docteur ESSAI Spécimen",(A["ident"],Bs["ident"],Bs["on"]))
            di=jd(A["identStore"],Bs["identStore"])
            ok("profil (stockage chiffré) identique, champ par champ",A["identStore"] and not di,di[:10])
            dj=jd(A["journal"],Bs["journal"])
            ok("journal identique (%d entrées, mêmes champs, mêmes valeurs)"%len(A["journal"]),len(A["journal"])==len(Bs["journal"])>=3 and not dj,dj[:12])
            dt=jd(A["tour"],Bs["tour"])
            ok("tournée identique (stockage) : 3 demandes, ordre, base, origine",A["tour"] and not dt,dt[:12])
            ok("tournée identique (en mémoire)",jd(A["tourMem"],Bs["tourMem"])==[],jd(A["tourMem"],Bs["tourMem"])[:8])
            ok("réglages conservés (thème nuit, grand texte)",Bs["theme"]=="night" and Bs["big"]=="1",(Bs["theme"],Bs["big"]))
            changed=[k for k in A["ls"] if k not in Bs["ls"] or Bs["ls"][k]!=A["ls"][k]]
            missing=[k for k in A["ls"] if k not in Bs["ls"]]
            ok("stockage : aucune clé de la v41k supprimée",not missing,missing)
            print("    (clés réécrites par la nouvelle version : %s ; nouvelles clés : %s)"%(changed,[k for k in Bs["ls"] if k not in A["ls"]][:10]))
            # 3. une entrée de plus dans la nouvelle version, puis le secours /v41k/ sur les mêmes données
            w2=await page.evaluate("""()=>{newPatient();Object.assign(state,{patient:'ESSAI Quatrième',ddn:'04/04/1990',sexe:'f'});const i=PACKS.findIndex(p=>/^Lombalgie/.test(p.n));state.sel=i;journalUpsert(currentPack());journalSave();newPatient();return JOURNAL.length;}""")
            await page.wait_for_timeout(1500)
            op2=await reopen(page,"garde","v41k/index.html")
            ok("secours /v41k/ : s'ouvre avec le même code, sans création",not op2.get("creation") and op2.get("unlocked"),op2)
            t=await page.title(); ok("secours /v41k/ : titre « Packs SOS v41k », code de la v41k (pas d'Express)",t=="Packs SOS v41k" and await page.evaluate("typeof xpHTML")=="undefined",t)
            sb=await page.evaluate("siteBase()"); ok("secours /v41k/ : profil.json et OCR lus à la racine du site (siteBase)",sb==B,sb)
            sw2=await page.evaluate(f"fetch('{B}v41k/sw.js',{{cache:'no-store'}}).then(r=>r.text())")
            ok("secours /v41k/ : cache propre (packs-sos-sub-v41k), ne supprime aucun autre cache",'const CACHE="packs-sos-sub-v41k"' in sw2 and "k=>false" in sw2,sw2[:200])
            man=await page.evaluate(f"fetch('{B}v41k/manifest.webmanifest',{{cache:'no-store'}}).then(r=>r.json())")
            ok("secours /v41k/ : manifeste propre (Packs SOS v41k)",man.get("name")=="Packs SOS v41k" and man.get("short_name")=="Packs SOS 41k",man)
            C=await page.evaluate(SNAP)
            ok("secours /v41k/ : identité, tournée et les 3 patients d'avant la bascule retrouvés",C["ident"]==A["ident"] and jd(A["tour"],C["tour"])==[] and len(C["journal"])>=3 and all(any(e.get("patient")==x.get("patient") for e in C["journal"]) for x in A["journal"]),(C["ident"],len(C["journal"])))
            print("    (le secours voit %d entrées ; la nouvelle version en a écrit %d — %s)"%(len(C["journal"]),w2,"les écritures de la nouvelle version sont partagées" if len(C["journal"])>=w2 else "les écritures faites après la bascule restent dans la nouvelle version"))
            ok("aucune erreur JavaScript",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_racine_41z.md"),"w",encoding="utf-8").write("# Publication en racine (06/11/2026) : conservation des données de la v41k\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
