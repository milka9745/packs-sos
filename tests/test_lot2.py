# Tests du lot 2 du registre du 16/10/2026 (n° 1 à 4) : visite par étapes, appels, mode voiture, nouvelles demandes.
# Adresses et numéros fictifs ; réseau extérieur coupé (trajets estimés à vol d'oiseau). Lancer : python tests/test_lot2.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8775

async def unlock(page):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testlot2"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(900)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

TOURSET="""()=>{newPatient();TOUR.stops=[
  {id:'v1',addr:'10 rue de Bourgogne, 45000 Orléans',label:'10 Rue de Bourgogne 45000 Orléans',lat:47.9020,lon:1.9110,city:'Orléans',nom:'DURAND Paul',ddn:'01/01/1950',tel:'0611111111',ts:1,done:false,motif:'fièvre'},
  {id:'v2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.9080,lon:1.8650,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/01/2018',tel:'0622222222',ts:2,done:false},
  {id:'v3',addr:'2 rue Nationale, 45140 Saint-Jean-de-la-Ruelle',label:'2 Rue Nationale 45140 Saint-Jean-de-la-Ruelle',lat:47.9100,lon:1.8700,city:'Saint-Jean-de-la-Ruelle',nom:'ROUX Max',ddn:'01/01/1990',ts:3,done:false}];
  TOUR.order=['v1','v2','v3'];TOUR.legs=[{km:2,min:6},{km:4,min:9},{km:1,min:3}];TOUR.current='';TOUR.computed=Date.now();tourSave();state.cot.lieu='visite';state.cot.auto=false;render();}"""
MAIN="""()=>{const c=document.querySelector('.tcard');if(!c)return null;const m=c.querySelector('.tc-main');const vis=e=>e&&e.getBoundingClientRect().width>0&&!e.closest('details:not([open])');
  return {step:(c.className.match(/step(\\d)/)||[])[1]||'',main:m?[...m.querySelectorAll('a,button')].filter(vis).map(e=>e.id||e.textContent.trim().slice(0,24)):[],calls:[...c.querySelectorAll('[data-tpcall]')].filter(vis).map(e=>e.dataset.tpcall),more:!!c.querySelector('details.tc-more:not([open])'),txt:c.innerText};}"""

async def run(width,label,big=False,th="day",shots=True):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":850 if width<500 else 950},device_scale_factor=2 if width<500 else 1,is_mobile=width<500,has_touch=width<500)
        await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
        page=await ctx.new_page(); errors=[]
        page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page); L=f"{label} {'grand texte ' if big else ''}{'nuit' if th=='night' else 'jour'} : "
        await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
        await page.evaluate(TOURSET); await page.wait_for_timeout(300)
        c=await page.evaluate(MAIN)
        ok(L+"n°1 étape 1 « tournée prête » : 2 à 4 actions principales (appel, commencer · itinéraire, mode voiture)",c and c["step"]=="1" and 2<=len(c["main"])<=4 and "tc_begin" in c["main"] and "tc_drive" in c["main"] and "v1" in c["calls"] and c["more"],c and {k:c[k] for k in ("step","main","calls","more")})
        if shots: await page.locator(".tcard").screenshot(path=os.path.join(OUT,f"{label}-lot2-etape1-{'grand' if big else 'normal'}-{th}.png"))
        await page.click("#tc_begin"); await page.wait_for_timeout(500)
        c=await page.evaluate(MAIN)
        ok(L+"n°1 étape 2 « en route » : naviguer, je suis arrivé, dictée (+ appel)",c and c["step"]=="2" and len(c["main"])<=4 and "tc_arrive" in c["main"] and "tc_dict" in c["main"] and any("Naviguer" in x for x in c["main"]),c and {k:c[k] for k in ("step","main")})
        ok(L+"n°2 appel du patient en cours et du suivant visibles (un toucher)","v1" in c["calls"] and "v2" in c["calls"],c["calls"])
        ok(L+"n°2 appel depuis la fiche patient",await page.locator(".pcard .pcall[href='tel:0611111111']").count()==1)
        if shots: await page.locator(".tcard").screenshot(path=os.path.join(OUT,f"{label}-lot2-etape2-{'grand' if big else 'normal'}-{th}.png"))
        # n° 3 : mode voiture
        await page.evaluate("state.view='drive';render();"); await page.wait_for_timeout(300)
        d=await page.evaluate("""()=>{const z=[...document.querySelectorAll('.drive .dv-zone')].map(x=>({cls:x.className,txt:x.innerText,calls:[...x.querySelectorAll('[data-tpcall]')].map(a=>a.dataset.tpcall),nav:!!x.querySelector('a[href*="waze"],a[href*="maps"]'),bh:Math.min(...[...x.querySelectorAll('.dv-b')].map(b=>b.getBoundingClientRect().height))}));const W=document.documentElement.clientWidth;return {z,arr:!!document.getElementById('dv_arr'),fs:parseFloat(getComputedStyle(document.querySelector('.drive .dv-addr')).fontSize),over:document.documentElement.scrollWidth>W};}""")
        ok(L+"n°3 mode voiture : patient actuel et patient suivant",len(d["z"])==2 and "patient actuel" in d["z"][0]["txt"].lower() and "patient suivant" in d["z"][1]["txt"].lower(),[x["txt"][:40] for x in d["z"]])
        ok(L+"n°3 actuel : appeler, naviguer, je suis arrivé ; suivant : appeler, itinéraire",d["z"][0]["calls"]==["v1"] and d["z"][0]["nav"] and d["arr"] and d["z"][1]["calls"]==["v2"] and d["z"][1]["nav"],d)
        ok(L+"n°3 gros boutons (≥ 60 px) et adresse adaptative ≥ 22 px (registre n° 12), sans débordement",min(x["bh"] for x in d["z"])>=60 and d["fs"]>=22 and not d["over"],{k:d[k] for k in ("fs","over")})
        if shots: await page.screenshot(path=os.path.join(OUT,f"{label}-lot2-voiture-{'grand' if big else 'normal'}-{th}.png"),full_page=True)
        await page.click("#dv_arr"); await page.wait_for_timeout(500)
        c=await page.evaluate(MAIN)
        ok(L+"n°1 étape 3 « sur place » : dictée, prescriptions, IA (sans navigation)",c and c["step"]=="3" and "tc_dict" in c["main"] and "tc_rx" in c["main"] and not any("Naviguer" in x for x in c["main"]) and len(c["main"])<=4,c and {k:c[k] for k in ("step","main")})
        await page.evaluate("document.activeElement&&document.activeElement.blur()"); await page.click("#tc_dict"); await page.wait_for_timeout(200)
        ok(L+"n°1 « Dictée » sur place : grand champ prêt pour le micro du clavier",await page.evaluate("document.activeElement&&document.activeElement.id")=="f_dict")
        await page.evaluate("state.sel=PACKS.findIndex(p=>p.n==='Grippe / syndrome viral — adulte');state.lastPrint={n:2,sent:true,ts:Date.now()};render();"); await page.wait_for_timeout(300)
        c=await page.evaluate(MAIN)
        ok(L+"n°1 étape 4 « fin de visite » : valider · patient suivant, appeler le suivant, réimprimer",c and c["step"]=="4" and "tc_valid" in c["main"] and "tc_reprint" in c["main"] and "v2" in c["calls"],c and {k:c[k] for k in ("step","main","calls")})
        if shots: await page.locator(".tcard").screenshot(path=os.path.join(OUT,f"{label}-lot2-etape4-{'grand' if big else 'normal'}-{th}.png"))
        # n° 4 : nouvelle demande pendant la tournée
        await page.evaluate("""()=>{tourAdd('8 rue Charles Beauhaire, 45140 Saint-Jean-de-la-Ruelle','Mme N',false,{lat:47.9090,lon:1.8680,label:'8 Rue Charles Beauhaire 45140 Saint-Jean-de-la-Ruelle',city:'Saint-Jean-de-la-Ruelle'});const s=TOUR.stops[TOUR.stops.length-1];s.tel='0633333333';s.nom='NOUVEAU Test';tourSave();render();}""")
        await page.wait_for_timeout(300)
        nv=await page.evaluate("(()=>{const b=document.querySelector('.tcard .tp-new');return b?{txt:b.innerText,vis:b.getBoundingClientRect().width>0&&!b.closest('details:not([open])')}:null;})()")
        ok(L+"n°4 nouvelle demande visible tout de suite dans la carte de visite, avec son secteur",nv and nv["vis"] and "Nouvelle demande" in nv["txt"] and "Saint-Jean-de-la-Ruelle" in nv["txt"] and "déjà prévue" in nv["txt"],nv)
        await page.evaluate("state.view='drive';render();"); await page.wait_for_timeout(200)
        ok(L+"n°4 nouvelle demande visible aussi en mode voiture",await page.locator(".drive .tp-new").count()==1)
        await page.evaluate("state.view='tour';render();"); await page.wait_for_timeout(200)
        ok(L+"n°4 écran Tournée : nouvelle demande en tête, avec son secteur",await page.locator("#main .tp-new").count()>=1 and "Saint-Jean-de-la-Ruelle" in await page.inner_text("#main .tp-new"))
        ok(L+"n°2 liste des visites : appel d'un toucher par visite",await page.locator(".trow [data-tpcall]").count()>=2)
        await page.evaluate("state.view='';render();"); await page.wait_for_timeout(200)
        await page.click(".tcard [data-tpins]"); await page.wait_for_timeout(1200)
        r=await page.evaluate("(()=>{const s=TOUR.stops[TOUR.stops.length-1];const i=TOUR.order.indexOf(s.id);const nb=[TOUR.order[i-1],TOUR.order[i+1]].filter(Boolean).map(id=>tpSector(tourStop(id)));return {isNew:!!s.isNew,order:TOUR.order.slice(),id:s.id,nb,banner:!!document.querySelector('.tp-new')};})()")
        ok(L+"n°4 « Intégrer au mieux » : insérée à côté des visites du même secteur, bandeau retiré",not r["isNew"] and r["id"] in r["order"] and "Saint-Jean-de-la-Ruelle" in r["nb"] and not r["banner"],r)
        await page.evaluate("""()=>{tourAdd('1 place du Martroi, 45000 Orléans','',false,{lat:47.9030,lon:1.9090,label:'1 Place du Martroi 45000 Orléans',city:'Orléans'});render();}"""); await page.wait_for_timeout(200)
        await page.click(".tcard [data-tplater]"); await page.wait_for_timeout(300)
        r=await page.evaluate("(()=>{const s=TOUR.stops[TOUR.stops.length-1];return {isNew:!!s.isNew,last:TOUR.order[TOUR.order.length-1]===s.id};})()")
        ok(L+"n°4 « En fin de tournée » : ajoutée en dernier",not r["isNew"] and r["last"],r)
        # cabinet : mêmes étapes visibles (iPhone)
        if width<500:
            await page.evaluate("newPatient();state.cot.lieu='cabinet';state.cot.auto=false;render();"); await page.wait_for_timeout(200)
            ok(L+"n°1 consultation au cabinet : étapes Patient → Dictée → Fiche → Imprimer → Validé",await page.locator(".steps.cab li").count()==5)
        ow=await page.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth")
        ok(L+"aucun débordement horizontal",ow)
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,"iphone",False,"day"); await run(375,"iphone",False,"night"); await run(375,"iphone",True,"day"); await run(375,"iphone",True,"night",shots=True); await run(1280,"pc",False,"day")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_lot2.md"),"w",encoding="utf-8").write("# Tests lot 2 — registre du 16/10/2026 (n° 1 à 4)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
