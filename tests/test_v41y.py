# Tests v41y (21/10/2026) — mode voiture (boutons pleins par fonction), fiche proposée (mots de régulation), impact d'une demande
# (une seule estimation, trajets réels), compteur de secteurs, bandeaux (4 s, un seul), badge TEST du dossier test/.
# 375 × 812 (jour, nuit, grand texte) et 1280 × 900 ; captures : tournée avec deux demandes, patient avec motif non clinique, mode voiture jour et nuit.
# Patients fictifs ; aucun appel externe (OSRM simulé localement, tout le reste bloqué).
import asyncio, os, re, json, math, subprocess, time, sys, shutil
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8783; PORT_T=8784
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page,base,xp="true",uid="testv41y"):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{xp}');}}catch(e){{}}")
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

# OSRM simulé : durées déterministes à partir des coordonnées (vol d'oiseau × 1,3 à 35 km/h), matrice complète
def hav(a,b):
    R=6371; r=math.radians
    dla=r(b[1]-a[1]); dlo=r(b[0]-a[0]); h=math.sin(dla/2)**2+math.cos(r(a[1]))*math.cos(r(b[1]))*math.sin(dlo/2)**2
    return 2*R*math.asin(min(1,math.sqrt(h)))
async def osrm_mock(route):
    url=route.request.url
    m=re.search(r"/table/v1/driving/([^?]+)",url)
    if not m:
        await route.fulfill(status=200,content_type="application/json",body=json.dumps({"code":"NoRoute"})); return
    pts=[tuple(map(float,c.split(","))) for c in m.group(1).split(";")]
    km=[[hav(a,b)*1.3 for b in pts] for a in pts]
    body={"code":"Ok","durations":[[round(d/35*3600,1) for d in row] for row in km],"distances":[[round(d*1000,1) for d in row] for row in km]}
    await route.fulfill(status=200,content_type="application/json",body=json.dumps(body))
async def net(ctx):
    # la dernière route enregistrée est examinée en premier : blocage général d'abord, OSRM simulé ensuite
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    await ctx.route(re.compile(r".*router\.project-osrm\.org.*"),osrm_mock)

# Tournée fictive : cabinet, visite en cours (w1), visite prévue (w2), deux nouvelles demandes non intégrées (n1 proche, n2 lointaine)
SET="""async()=>{newPatient();TOUR.base={lat:47.9029,lon:1.9093,label:'Cabinet, 44 rue Chanzy, 45000 Orléans'};TOUR.origin='cabinet';TOUR.dest='';TOUR.destGeo=null;
  TOUR.stops=[{id:'w1',addr:'12 rue de la Gare, 45000 Orléans',label:'12 Rue de la Gare 45000 Orléans',lat:47.909,lon:1.905,city:'Orléans',nom:'MARTIN Jeanne',ddn:'03/04/1938',tel:'0611111111',motif:'O INTERVENTION',bat:'Bât. C, 3e étage',ts:1,done:false},
   {id:'w2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.912,lon:1.86,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/01/2018',tel:'0622222222',motif:'fièvre',ts:2,done:false},
   {id:'n1',addr:'3 rue des Carmes, 45000 Orléans',label:'3 Rue des Carmes 45000 Orléans',lat:47.9,lon:1.9,city:'Orléans',nom:'DUPONT Marc',ddn:'14/05/1975',tel:'0633333333',motif:'lombalgie',ts:3,done:false,isNew:true},
   {id:'n2',addr:'10 rue de la Mairie, 45160 Olivet',label:'10 Rue de la Mairie 45160 Olivet',lat:47.86,lon:1.9,city:'Olivet',nom:'ROUX Anne',ddn:'02/02/1990',tel:'0644444444',motif:'angine',ts:4,done:false,isNew:true}];
  TOUR.order=['w1','w2'];TOUR.current='w1';TOUR.started=Date.now();TOUR.est=false;await tpLegsRefresh();tpEtaApply();tourSave();state.cot.lieu='visite';state.patient='MARTIN Jeanne';state.ddn='03/04/1938';state.sexe='f';}"""

def lum(c):
    def ch(v):
        v=v/255; return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*ch(c[0])+0.7152*ch(c[1])+0.0722*ch(c[2])
def contrast(a,b):
    la,lb=lum(a),lum(b); hi,lo=max(la,lb),min(la,lb); return (hi+0.05)/(lo+0.05)
def rgb(s):
    m=re.findall(r"[\d.]+",s or ""); return tuple(float(x) for x in m[:3]) if len(m)>=3 else None

DRIVE_MEAS="""()=>{const z=[...document.querySelectorAll('.drive .dv-zone')];const out=[];
  document.querySelectorAll('.drive .dv-b, .drive .dv-q').forEach(b=>{const r=b.getBoundingClientRect();const cs=getComputedStyle(b);const zone=b.closest('.dv-zone');
    out.push({t:b.textContent.trim().slice(0,22),cls:b.className,zone:zone?(zone.classList.contains('now')?'now':'next'):'top',h:r.height,fs:parseFloat(cs.fontSize),fw:cs.fontWeight,bg:cs.backgroundColor,color:cs.color,bw:cs.borderWidth,bc:cs.borderColor});});
  const now=document.querySelector('.drive .dv-zone.now');return {btn:out,frame:now?getComputedStyle(now).borderColor:'',fin:(document.querySelector('.drive>.dv-time')||{}).textContent||''};}"""

BADGE_CHK="""()=>{const b=document.getElementById('testbadge');if(!b)return {missing:true};const r=b.getBoundingClientRect();const bad=[];
  document.querySelectorAll('button,a,input,select,textarea,label,summary,h1,h2,h3,p,li,b,span,div,small,strong').forEach(e=>{if(e===b||b.contains(e))return;const cs=getComputedStyle(e);if(cs.visibility==='hidden'||cs.display==='none'||cs.opacity==='0')return;
    const inter=/^(BUTTON|A|INPUT|SELECT|TEXTAREA|SUMMARY|LABEL)$/.test(e.tagName);const txt=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());if(!inter&&!txt)return;
    const q=e.getBoundingClientRect();if(!q.width||!q.height)return;if(q.top<r.bottom-0.5&&q.bottom>r.top+0.5&&q.left<r.right&&q.right>r.left)bad.push(e.tagName+':'+(e.textContent||'').trim().slice(0,30));});
  const jb=document.querySelector('.jbar');return {top:r.top,h:r.height,txt:b.textContent.trim(),bad:bad.slice(0,6),jbTop:jb?jb.getBoundingClientRect().top:null};}"""

async def run(width,height,theme,big,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        await net(ctx)
        page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page,f"http://localhost:{PORT}/")
        await page.evaluate(f"localStorage.setItem('sos_theme','{theme}');localStorage.setItem('sos_theme_force','null');localStorage.setItem('sos_bigtext','{1 if big else 0}');try{{THEME.mode='{theme}';}}catch(e){{}}themeApply();")
        th=await page.evaluate("document.documentElement.getAttribute('data-theme')")
        ok(label+f"thème appliqué : {theme}",th==theme,th)
        await page.evaluate(SET); await page.wait_for_timeout(300)
        # ---------- tournée : deux demandes, impact par adresse, secteurs ----------
        await page.evaluate("state.view='tour';render();"); await page.wait_for_timeout(900)
        imp=await page.evaluate("[...document.querySelectorAll('[data-tpimp]')].map(e=>({id:e.dataset.tpimp,t:e.textContent}))")
        t1=next((x["t"] for x in imp if x["id"]=="n1"),""); t2=next((x["t"] for x in imp if x["id"]=="n2"),"")
        ok(label+"tournée : impact affiché pour chaque demande, « +N min → fin de tournée HH h MM » (pas de point d'arrivée)",re.match(r"^\+\d+ min → fin de tournée \d{1,2} h \d{2}",t1) and re.match(r"^\+\d+ min → fin de tournée \d{1,2} h \d{2}",t2),(t1,t2))
        ok(label+"tournée : deux adresses différentes → impacts différents, trajets réels (pas de mention « estimation »)",t1!=t2 and "estimation" not in t1 and "estimation" not in t2,(t1,t2))
        sec=await page.evaluate("[...document.querySelectorAll('.tp-sectors .chip')].map(e=>e.textContent)")
        txt=await page.evaluate("(document.querySelector('.tp-new')||{}).textContent||''")
        ok(label+"secteurs : la puce « Orléans · 1 » compte la visite non faite, pas les demandes non intégrées ; texte « 1 visite déjà prévue »","Orléans · 1" in sec and "1 visite déjà prévue dans ce secteur" in txt,(sec,txt[:160]))
        if width<500 and theme=="day" and not big: await page.screenshot(path=os.path.join(OUT,"v41y-tournee-2demandes.png"),full_page=False)
        # même estimation : impact calculé avant intégration = fin prévue après intégration (même instant de calcul)
        r=await page.evaluate("""async()=>{const s=tourStop('n1');const geo={id:'n1',lat:s.lat,lon:s.lon,label:s.label,motif:s.motif};const legs=await tpImpactLegs(geo);const T=Date.now();const r=tpImpactCalc(geo,legs,T);
          await tpInsertBest('n1');const fin=tpEndTime({now:T}).arr;const ui=(document.querySelector('.tp-sectors')||{}).textContent||'';return {imp:r.arr,at:r.at,fin,same:fmtH(r.arr)===fmtH(fin),sec:[...document.querySelectorAll('.tp-sectors .chip')].map(e=>e.textContent),isNew:!!tourStop('n1').isNew,order:TOUR.order};}""")
        ok(label+"impact : une seule fonction d'estimation — heure annoncée avant intégration = « Fin prévue » après intégration",r["imp"]==r["fin"] and r["same"],r)
        ok(label+"secteurs : après intégration, la puce Orléans passe à 2 et la demande n'est plus « nouvelle »","Orléans · 2" in r["sec"] and not r["isNew"] and "n1" in r["order"],r)
        # point d'arrivée réglé → libellé « arrivée au cabinet »
        lab=await page.evaluate("()=>{TOUR.dest='cabinet';const s=tourStop('n2');return tpImpactText(tpImpactCalc({id:'n2',lat:s.lat,lon:s.lon,label:s.label,motif:s.motif}));}")
        ok(label+"impact : point d'arrivée = cabinet → « +N min → arrivée au cabinet HH h MM »",re.match(r"^\+\d+ min → arrivée au cabinet \d{1,2} h \d{2}",lab or ""),lab)
        off=await page.evaluate("()=>{TOUR.dest='';const s=tourStop('n2');const r=tpImpactCalc({id:'n2',lat:s.lat,lon:s.lon,label:s.label,motif:s.motif});return tpImpactText(r);}")
        ok(label+"impact hors ligne (sans trajets fournis) : vol d'oiseau majoré, signalé « estimation »","estimation" in (off or ""),off)
        # ---------- mode voiture ----------
        await page.evaluate("state.view='drive';render();"); await page.wait_for_timeout(400)
        m=await page.evaluate(DRIVE_MEAS)
        btn=m["btn"]; bad=[]
        for x in btn:
            bg=rgb(x["bg"]); col=rgb(x["color"])
            if not bg or x["bg"].startswith("rgba(0, 0, 0, 0)"): bad.append(("fond",x["t"],x["bg"])); continue
            if x["h"]<64: bad.append(("hauteur",x["t"],x["h"]))
            if x["fs"]<22: bad.append(("taille",x["t"],x["fs"]))
            if int(x["fw"] if x["fw"].isdigit() else 700)<700: bad.append(("graisse",x["t"],x["fw"]))
            if contrast(bg,col)<4.5: bad.append(("contraste",x["t"],round(contrast(bg,col),2)))
        ok(label+"voiture : tous les boutons en fond plein, hauteur ≥ 64 px, texte ≥ 22 px gras, contraste ≥ 4,5",not bad and len(btn)>=4,(bad[:4],[(x["t"],x["h"],x["fs"]) for x in btn]))
        nav=[x for x in btn if "dv-nav" in x["cls"]]; call=[x for x in btn if "dv-call" in x["cls"]]; arr=[x for x in btn if "dv-arr" in x["cls"]]; quit_=[x for x in btn if "dv-q" in x["cls"]]
        ok(label+"voiture : Naviguer et Itinéraire en bleu, même couleur pour le patient actuel et le suivant",len(nav)==2 and nav[0]["bg"]==nav[1]["bg"] and rgb(nav[0]["bg"])[2]>rgb(nav[0]["bg"])[0],[(x["zone"],x["bg"]) for x in nav])
        ok(label+"voiture : Appeler en vert, identique pour les deux patients",len(call)==2 and call[0]["bg"]==call[1]["bg"] and rgb(call[0]["bg"])[1]>rgb(call[0]["bg"])[0] and rgb(call[0]["bg"])[1]>rgb(call[0]["bg"])[2],[(x["zone"],x["bg"]) for x in call])
        ok(label+"voiture : « Je suis arrivé » en or plein, le plus gros bouton",len(arr)==1 and arr[0]["h"]>=max(x["h"] for x in btn) and rgb(arr[0]["bg"])[0]>rgb(arr[0]["bg"])[2],[(x["t"],x["h"],x["bg"]) for x in arr])
        ok(label+"voiture : Quitter en gris sombre avec contour fin",len(quit_)==1 and 0.8<=float(re.findall(r"[\d.]+",quit_[0]["bw"])[0])<=1.5 and abs(rgb(quit_[0]["bg"])[0]-rgb(quit_[0]["bg"])[1])<20,[(x["bg"],x["bw"]) for x in quit_])
        ok(label+"voiture : cadre or autour du patient actuel",rgb(m["frame"])==(255.0,179.0,0.0),m["frame"])
        ok(label+"voiture : ligne « Fin prévue » présente",m["fin"].startswith("Fin prévue"),m["fin"])
        if width<500 and not big: await page.screenshot(path=os.path.join(OUT,f"v41y-voiture-{'nuit' if theme=='night' else 'jour'}.png"),full_page=False)
        # ---------- fiche proposée ----------
        await page.evaluate("state.view='';render();"); await page.wait_for_timeout(300)
        c=await page.evaluate("()=>({a:xpCandidates('O INTERVENTION'),b:(xpCandidates('lombalgie').ok||[]).slice(0,1).map(i=>PACKS[i].n),c:xpCandidates('VAD urgence domicile').none===true,d:(xpCandidates('visite fièvre enfant').ok||[]).length>0})")
        ok(label+"fiche proposée : « O INTERVENTION » → aucune fiche (none), « lombalgie » → Lombalgie aiguë",c["a"].get("none") is True and c["b"]==["Lombalgie aiguë"] and c["c"] and c["d"],c)
        h=await page.evaluate("()=>{state.xpMotif='O INTERVENTION';const h=xpPropHTML();state.xpMotif=null;return h;}")
        ok(label+"fiche proposée : motif non clinique → bloc masqué, seul « Choisir une fiche » reste",'id="xp_list"' in h and "xp-pn" not in h and "Aucune fiche proposée" not in h and "fiches fréquentes" not in h,h[:200])
        h2=await page.evaluate("()=>{state.xpMotif='lombalgie';const h=xpPropHTML();state.xpMotif=null;return h;}")
        ok(label+"fiche proposée : « lombalgie » → Lombalgie aiguë",'xp-pn">Lombalgie aiguë<' in h2,h2[:200])
        dom=await page.evaluate("()=>({prop:!!document.querySelector('.xp-prop'),none:!!document.querySelector('.xp-prop.none'),pn:(document.querySelector('.xp-pn')||{}).textContent||''})")
        ok(label+"écran Patient (motif « O INTERVENTION » de la régulation) : aucune fiche proposée à l'écran",dom["prop"] and dom["none"] and not dom["pn"],dom)
        if width<500 and theme=="day" and not big: await page.screenshot(path=os.path.join(OUT,"v41y-patient-motif-nonclinique.png"),full_page=False)
        # ---------- bandeaux ----------
        t0=await page.evaluate("()=>{toast('CR copié · prêt à coller dans MCC');return document.getElementById('toast').classList.contains('on');}")
        await page.wait_for_timeout(4400)
        t1=await page.evaluate("document.getElementById('toast').classList.contains('on')")
        ok(label+"bandeau : visible puis disparu de lui-même après 4 s",t0 and not t1,(t0,t1))
        t2=await page.evaluate("()=>{toast('un');state.view='tour';render();return document.getElementById('toast').classList.contains('on');}")
        ok(label+"bandeau : effacé au changement d'écran",not t2,t2)
        t3=await page.evaluate("()=>{toast('deux');xpToast('CR copié · patient validé',true);const a=document.getElementById('toast').classList.contains('on'),b=document.getElementById('xptoast').classList.contains('on');toast('trois');const c=document.getElementById('xptoast').classList.contains('on');return {a,b,c};}")
        ok(label+"bandeau : un seul à la fois (le nouveau remplace l'ancien)",not t3["a"] and t3["b"] and not t3["c"],t3)
        ok(label+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def run_badge(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        await net(ctx)
        page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page,f"http://localhost:{PORT_T}/test/",uid="testbadge")
        await page.evaluate(SET); await page.wait_for_timeout(300)
        for view,name in [("tour","Tournée"),("","Patient"),("drive","Mode voiture")]:
            await page.evaluate(f"state.view='{view}';render();"); await page.wait_for_timeout(400)
            r=await page.evaluate(BADGE_CHK)
            ok(label+f"badge TEST ({name}) : en haut, sous la barre d'état, sans couvrir un bouton ni une ligne de texte",not r.get("missing") and r["top"]==0 and r["h"]>=18 and r["txt"].startswith("TEST · 41") and not r["bad"],r)
            if view=="tour":
                await page.evaluate("window.scrollTo(0,400)"); await page.wait_for_timeout(200)
                r2=await page.evaluate(BADGE_CHK); await page.evaluate("window.scrollTo(0,0)")
                ok(label+"badge TEST (Tournée, après défilement) : la barre du haut reste sous le badge",r2.get("jbTop") is None or r2["jbTop"]>=r2["h"]-0.5,r2)
        ok(label+"badge : aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    # dossier test/ construit dans un répertoire temporaire (jamais dans le dépôt)
    tmp=os.path.join(ROOT,"tests","_tmp_site41y"); shutil.rmtree(tmp,ignore_errors=True); os.makedirs(tmp,exist_ok=True)
    subprocess.run([sys.executable,os.path.join(ROOT,"tools","build_test.py"),os.path.join(tmp,"test")],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
    srv2=subprocess.Popen([sys.executable,"-m","http.server",str(PORT_T)],cwd=tmp,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,812,"day",False,"iPhone jour : ")
        await run(375,812,"night",False,"iPhone nuit : ")
        await run(375,812,"day",True,"iPhone grand texte : ")
        await run(1280,900,"day",False,"PC : ")
        await run_badge(375,812,"iPhone : ")
        await run_badge(1280,900,"PC : ")
    finally:
        srv.terminate(); srv2.terminate(); shutil.rmtree(tmp,ignore_errors=True)
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_v41y.md"),"w",encoding="utf-8").write("# Tests v41y — mode voiture, fiche proposée, impact, secteurs, bandeaux, badge TEST\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
