# -*- coding: utf-8 -*-
# 26/11/2026 — Tournée : déplacer une visite par appui long puis glisser (écran Tournée), bouton « Optimiser la tournée »
# qui garde les prioritaires ★ en tête dans l'ordre du médecin (à défaut la première visite) puis calcule la suite au plus
# court. iPhone 375 × 812 (touches réelles par CDP : touchStart, maintien, touchMove, touchEnd) et ordinateur 1280 × 900
# (souris). Requêtes externes bloquées : l'optimiseur se replie sur le plus proche voisin à vol d'oiseau. Adresses fictives.
# Lancer : python tests/test_tournee_ordre.py
import asyncio, os, subprocess, time, sys, json, math
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8851
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
BASE={"lat":47.9029,"lon":1.9093}
STOPS=[("A","1 rue de la République, Orléans",47.9040,1.9050),("B","10 rue de Bourgogne, Orléans",47.9000,1.9150),("C","5 avenue Dauphine, Orléans",47.8900,1.9100),("D","20 rue des Fossés, Saint-Jean-de-Braye",47.9130,1.9700)]
def hav(a,b):
    R=6371.0; p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(h))
def nn(start,labels,pts):
    left=list(labels); pos=start; out=[]
    while left:
        best=min(left,key=lambda l:hav(pos,pts[l])); out.append(best); pos=pts[best]; left.remove(best)
    return out
PTS={l:(la,lo) for (l,_,la,lo) in STOPS}
SET="""(a)=>{TESTMODE=true;newPatient();TOUR.base={lat:%f,lon:%f,label:'Cabinet, 44 rue Chanzy, 45000 Orléans'};TOUR.origin='cabinet';TOUR.dest='';TOUR.destGeo=null;TOUR.manual=false;TOUR.optTs=0;TOUR.optFrom='';TOUR.cfg=null;TOUR.autoChg=null;TOUR.given=[];TOUR.current='';TOUR.lastDone='';TOUR.stops=[];TOUR.order=[];TOUR.legs=[];TOUR.total=null;TOUR.computed=0;TOUR.busy=false;
  a.stops.forEach(s=>tourAdd(s[1],s[0],false,{lat:s[2],lon:s[3],label:s[1],city:'Orléans'}));tourSave();return TOUR.stops.map(s=>[s.lbl,s.id]);}"""%(BASE["lat"],BASE["lon"])
ORDER="()=>TOUR.order.map(id=>{const s=tourStop(id);return s?s.lbl:id;})"
async def create(page,uid):
    await page.add_init_script("try{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','false')}catch(e){}")
    await page.add_init_script("window.navOpen=u=>{window.__navOpened=(window.__navOpened||[]).concat([u]);};")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000); await page.wait_for_timeout(600)
    for _ in range(4):
        await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
        try:
            await page.wait_for_selector("#rec_ack",timeout=8000); break
        except Exception: await page.wait_for_timeout(600)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(800)
async def touch_drag(page,x0,y0,x1,y1,hold=750,steps=10):
    cdp=await page.context.new_cdp_session(page)
    await cdp.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[{"x":x0,"y":y0}]}); await page.wait_for_timeout(hold)
    for i in range(1,steps+1):
        await cdp.send("Input.dispatchTouchEvent",{"type":"touchMove","touchPoints":[{"x":x0+(x1-x0)*i/steps,"y":y0+(y1-y0)*i/steps}]}); await page.wait_for_timeout(40)
    await cdp.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]}); await cdp.detach()
async def mouse_drag(page,x0,y0,x1,y1,hold=750,steps=10):
    await page.mouse.move(x0,y0); await page.mouse.down(); await page.wait_for_timeout(hold); await page.mouse.move(x1,y1,steps=steps); await page.wait_for_timeout(80); await page.mouse.up()
async def row_box(page,lbl):
    return await page.evaluate("(l)=>{const s=TOUR.stops.find(x=>x.lbl===l);const e=s&&document.querySelector('.trow[data-tid=\"'+s.id+'\"]');if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};}",lbl)
async def list_into_view(page):
    # la liste des visites est sous la carte et les réglages : on l'amène en haut de l'écran avant de « poser le doigt »
    await page.evaluate("()=>{const t=document.getElementById('toast');if(t)t.classList.remove('on');const l=document.querySelector('#main .jlist .trow[data-tid]');if(l)l.scrollIntoView({block:'start'});const sc=document.querySelector('#main');[window,document.scrollingElement,document.body,sc].forEach(x=>{try{if(x===window)window.scrollBy(0,-80);else if(x)x.scrollTop=Math.max(0,x.scrollTop-80);}catch(e){}});}"); await page.wait_for_timeout(350)
async def drag_to_top(page,mob,lbl,top_lbl):
    await list_into_view(page); src=await row_box(page,lbl); dst=await row_box(page,top_lbl)
    if not src or not dst: return False
    x0=src["x"]+18; y0=src["y"]+src["h"]/2; x1=dst["x"]+18; y1=dst["y"]+6
    if mob: await touch_drag(page,x0,y0,x1,y1)
    else: await mouse_drag(page,x0,y0,x1,y1)
    await page.wait_for_timeout(700); return True
async def wait_opt(page):
    await page.wait_for_function("!TOUR.busy",timeout=20000); await page.wait_for_timeout(300)
async def run(b,mob,label):
    L=label+" : "
    ctx=await b.new_context(viewport={"width":375 if mob else 1280,"height":812 if mob else 900},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,user_agent=UA if mob else None)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await create(page,"tord"+("m" if mob else "d"))
    ids=await page.evaluate(SET,{"stops":STOPS}); await page.evaluate("tourOptimize()"); await wait_opt(page)
    exp_auto=nn((BASE["lat"],BASE["lon"]),[s[0] for s in STOPS],PTS)
    order=await page.evaluate(ORDER)
    ok(L+"4 visites, ordre automatique au plus proche voisin depuis le cabinet (hors connexion) : "+" → ".join(exp_auto),order==exp_auto and not await page.evaluate("TOUR.manual"),order)
    await page.evaluate("()=>{state.view='tour';render();}"); await page.wait_for_timeout(500)
    ok(L+"écran Tournée : 4 lignes avec identifiant, bouton « ⟳ Optimiser la tournée », aide « appui long », pas de ▲ ▼ en ordre automatique",await page.locator(".trow[data-tid]").count()==4 and await page.locator("#tr_opt").count()==1 and "Appui long" in await page.locator(".hint.tr-drag").inner_text() and await page.locator("[data-tmv]").count()==0)
    # ---- appui long puis glisser : D en tête → ordre manuel
    moved=await drag_to_top(page,mob,"D",exp_auto[0])
    order=await page.evaluate(ORDER); st=await page.evaluate("[TOUR.manual,TOUR.optTs,document.body.classList.contains('t-dragging'),document.querySelectorAll('.trow.tdragging').length]")
    ok(L+"appui long puis glisser D en tête : ordre manuel, D première, les autres dans leur ordre, plus d'état de glisser",moved and order==["D"]+[x for x in exp_auto if x!="D"] and st[0] is True and st[1]==0 and st[2] is False and st[3]==0,(order,st))
    ok(L+"ordre manuel : ▲ ▼ sur chaque visite et message « Ordre manuel … appui long »",await page.locator("[data-tmv]").count()==8 and "Ordre manuel" in await page.locator(".tr-auto").inner_text() and "appui long" in await page.locator(".tr-auto").inner_text(),await page.locator(".tr-auto").inner_text())
    # ---- priorité ★ sur B (pas de recalcul en ordre manuel), puis Optimiser : B en tête, la suite au plus court depuis B
    bid=[i for (l,i) in ids if l=="B"][0]
    await page.locator(f'[data-tprio="{bid}"]').first.click(); await page.wait_for_timeout(500)
    order2=await page.evaluate(ORDER)
    ok(L+"★ Priorité sur B en ordre manuel : aucun recalcul, ordre inchangé",order2==order and await page.evaluate("tourStop('"+bid+"').prio"),order2)
    await page.locator("#tr_opt").first.click(); await wait_opt(page)
    exp=["B"]+nn(PTS["B"],["A","C","D"],PTS); order=await page.evaluate(ORDER); msg=await page.locator(".tr-auto").inner_text(); st=await page.evaluate("[TOUR.manual,TOUR.optTs>0,TOUR.optFrom,TOUR.est]")
    ok(L+"« Optimiser la tournée » : B (prioritaire) en tête, puis "+" → ".join(exp[1:])+" au plus court depuis B ; ordre toujours manuel ; message « optimisé à … à partir de B »",order==exp and st[0] is True and st[1] and str(st[2]).startswith("B") and "optimisé à" in msg and "à partir de B" in msg,(order,st,msg))  # stopName() = repère puis rue
    # ---- sans prioritaire : la première visite de la liste sert d'ancre
    await page.locator(f'[data-tprio="{bid}"]').first.click(); await page.wait_for_timeout(400)
    moved=await drag_to_top(page,mob,"C","B")
    order=await page.evaluate(ORDER); st=await page.evaluate("[TOUR.manual,TOUR.optTs]")
    ok(L+"B retirée des prioritaires, C glissée en tête : C première, horodatage d'optimisation effacé",moved and order[0]=="C" and st[0] is True and st[1]==0,(order,st))
    await page.locator("#tr_opt").first.click(); await wait_opt(page)
    exp=["C"]+nn(PTS["C"],["A","B","D"],PTS); order=await page.evaluate(ORDER); msg=await page.locator(".tr-auto").inner_text()
    ok(L+"« Optimiser » sans prioritaire : la première visite (C) reste en tête, puis "+" → ".join(exp[1:])+" ; message « à partir de C »",order==exp and "à partir de C" in msg,(order,msg))
    # ---- ▲ ▼ restent utilisables et effacent l'horodatage
    aid=[i for (l,i) in ids if l=="A"][0]
    await page.locator(f'[data-tmv="up|{aid}"]').first.click(); await page.wait_for_timeout(500)
    order3=await page.evaluate(ORDER)
    ok(L+"▲ sur A : remontée d'une place, horodatage effacé",order3.index("A")==order.index("A")-1 and await page.evaluate("TOUR.optTs")==0,order3)
    # ---- nouvelle visite en ordre manuel : ajoutée en fin, ordre conservé
    await page.evaluate("()=>{const s=tourAdd('3 rue du Faubourg Bannier, Orléans','E',false,{lat:47.9100,lon:1.9000,label:'3 rue du Faubourg Bannier, Orléans',city:'Orléans'});tourAfterAdd(s);}"); await wait_opt(page)
    order4=await page.evaluate(ORDER)
    ok(L+"visite E ajoutée en ordre manuel : en fin de liste, ordre des autres conservé",order4==order3+["E"] and await page.evaluate("TOUR.manual") is True,order4)
    # ---- enregistrement : optTs / optFrom et ordre manuel partent avec la tournée
    saved=await page.evaluate("()=>{const o=secSet;let last=null;secSet=(n,v)=>{if(n==='sos_tour')last=v;return o(n,v);};TOUR.optTs=123456;TOUR.optFrom='C';tourSave();secSet=o;TOUR.optTs=0;TOUR.optFrom='';return last&&[last.manual,last.optTs,last.optFrom];}")
    ok(L+"tourSave : ordre manuel, optTs et optFrom enregistrés avec la tournée",saved==[True,123456,"C"],saved)
    # ---- retour à l'ordre automatique depuis la carte
    await page.evaluate("()=>{state.cot.lieu='visite';state.cot.auto=false;state.view='';render();}"); await page.wait_for_timeout(500)
    await page.evaluate("()=>{const b=document.getElementById('tc_manual');const d=b&&b.closest('details');if(d)d.open=true;}"); await page.wait_for_timeout(200)  # le bouton est dans le tiroir « Plus » de la carte
    tm=page.locator("#tc_manual").first
    ok(L+"carte de tournée (tiroir Plus) : bouton « Ordre automatique » proposé en ordre manuel",await tm.count()==1 and "automatique" in (await tm.text_content() or "").lower(),(await tm.text_content()) if await tm.count() else "absent")
    if await tm.count(): await tm.scroll_into_view_if_needed(); await tm.click(); await wait_opt(page)
    order5=await page.evaluate(ORDER); exp5=nn((BASE["lat"],BASE["lon"]),["A","B","C","D","E"],{**PTS,"E":(47.9100,1.9000)})
    ok(L+"« Ordre automatique » : recalcul depuis le cabinet ("+" → ".join(exp5)+"), plus de ▲ ▼",order5==exp5 and await page.evaluate("TOUR.manual") is False,order5)
    await page.evaluate("()=>{state.view='tour';render();}"); await page.wait_for_timeout(400)
    ok(L+"écran Tournée en ordre automatique : « ⟳ Optimiser » présent, pas de ▲ ▼",await page.locator("#tr_opt").count()==1 and await page.locator("[data-tmv]").count()==0)
    ok(L+"aucune erreur JS",not errs,errs[:2])
    await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await run(b,True,"iPhone (touches)")
            await run(b,False,"ordinateur (souris)")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_tournee_ordre.md"),"w",encoding="utf-8").write("# Tournée — appui long pour déplacer, « Optimiser la tournée » (26/11/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}"+("" if r[1] else f" — {str(r[2])[:300]}") for r in results)+"\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
