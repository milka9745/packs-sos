# Registre n° 12 (16/10/2026) — mode voiture sur iPhone : zones sûres, adresse lisible jamais coupée, gros boutons toujours visibles.
# Tailles 320×568, 375×812, 430×932 en portrait et paysage, jour/nuit, grand texte, adresse longue fictive. Captures avant/après.
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8776
LONG="Résidence Les Jardins de la Source, bâtiment C, escalier 4, 1250 avenue du Président-Kennedy-Prolongée, 45100 Orléans"

async def unlock(page):
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testvoiture"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)

SET="""(a)=>{newPatient();TOUR.stops=[{id:'w1',addr:a,label:a,lat:47.85,lon:1.93,city:'Orléans',nom:'MARTIN Jeanne',ddn:'03/04/1938',tel:'0611111111',bat:'Bât. C, 3e étage, code 4512B',ts:1,done:false},
  {id:'w2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.908,lon:1.865,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/01/2018',tel:'0622222222',ts:2,done:false}];
  TOUR.order=['w1','w2'];TOUR.legs=[{km:6,min:12},{km:9,min:15}];TOUR.current='w1';tourStop('w1').cur=true;TOUR.computed=Date.now();tourSave();state.cot.lieu='visite';state.view='drive';render();}"""
MEAS="""()=>{const W=document.documentElement.clientWidth,H=innerHeight;const z=document.querySelector('.drive .dv-zone.now');const a=z.querySelector('.dv-addr');const cs=getComputedStyle(a);
  const lh=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.2;const ar=a.getBoundingClientRect();const b=[...z.querySelectorAll('.dv-btns .dv-b')];
  const order=[...z.children].map(e=>e.className.split(' ')[0]);const btxt=b.map(x=>x.textContent.trim().replace(/^[^A-Za-zÀ-ÿ]+/,'').slice(0,12));
  const vis=b.map(x=>{const r=x.getBoundingClientRect();const h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return r.top>=0&&r.bottom<=H+0.5&&r.height>=60&&!!h&&(h===x||x.contains(h));});
  return {W,H,sw:document.documentElement.scrollWidth,fs:parseFloat(cs.fontSize),lines:Math.round(a.clientHeight/lh),clip:a.classList.contains('clip'),wcut:a.scrollWidth>a.clientWidth+1,aTop:ar.top,order,btxt,vis,bh:b.map(x=>Math.round(x.getBoundingClientRect().height))};}"""

async def shot(page,path):
    await page.evaluate("window.scrollTo(0,0)"); await page.screenshot(path=path)

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            sizes=[(320,568),(375,812),(430,932)]
            for (w,h) in sizes:
                for orient in ["portrait","paysage"]:
                    vw,vh=(w,h) if orient=="portrait" else (h,w)
                    for th in ["day","night"]:
                        for big in [False,True]:
                            if big and th=="day" and orient=="paysage" and w!=320: continue
                            ctx=await b.new_context(viewport={"width":vw,"height":vh},device_scale_factor=2,is_mobile=True,has_touch=True)
                            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                            await unlock(page)
                            await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
                            await page.evaluate(SET,LONG); await page.wait_for_timeout(350)
                            L=f"{w}×{h} {orient} {'nuit' if th=='night' else 'jour'}{' grand texte' if big else ''} : "
                            r=await page.evaluate(MEAS)
                            ok(L+"aucun défilement horizontal",r["sw"]<=r["W"],{k:r[k] for k in ("sw","W")})
                            ok(L+"adresse ≥ 22 px, jamais coupée en largeur, 3 lignes au plus (sinon complète d'un toucher)",r["fs"]>=22 and not r["wcut"] and (r["lines"]<=3 or r["clip"]==False and False) or (r["fs"]>=22 and not r["wcut"] and r["clip"]),{k:r[k] for k in ("fs","lines","clip","wcut")})
                            ok(L+"ordre : adresse, accès (bâtiment, étage, code), puis boutons",r["order"].index("dv-addr")<r["order"].index("dv-acc")<r["order"].index("dv-btns"),r["order"])
                            ok(L+"boutons Naviguer, Appeler, Je suis arrivé ≥ 60 px, visibles sans défilement",r["btxt"][:3]==["Naviguer · W","Appeler","Je suis arri"] and all(r["vis"]) and min(r["bh"])>=60,{k:r[k] for k in ("btxt","bh","vis","H")})
                            if r["clip"]:
                                await page.click(".drive .dv-addr"); await page.wait_for_timeout(150)
                                full=await page.evaluate("(()=>{const a=document.querySelector('.drive .dv-addr');return a.classList.contains('full')&&a.scrollHeight<=a.clientHeight+2;})()")
                                ok(L+"adresse longue : complète d'un toucher",full)
                                await page.click(".drive .dv-addr"); await page.wait_for_timeout(100)
                            ok(L+"aucune erreur JS",not errors,errors[:2])
                            tag=f"{w}x{h}-{orient}-{th}{'-grand' if big else ''}"
                            if (w==320) or (w==375 and orient=="portrait" and big and th=="night") or (w==430 and orient=="portrait" and th=="day" and not big):
                                await shot(page,os.path.join(OUT,f"voiture-apres-{tag}.png"))
                                await page.evaluate("renderDriveV40()"); await page.wait_for_timeout(200)
                                await shot(page,os.path.join(OUT,f"voiture-avant-{tag}.png"))
                            await ctx.close()
            # zones sûres déclarées dans la feuille de style (encoche, Dynamic Island, barre d'accueil)
            ctx=await b.new_context(viewport={"width":375,"height":812}); page=await ctx.new_page(); await unlock(page)
            css=await page.evaluate("[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules].map(r=>r.cssText)}catch(e){return []}}).filter(t=>/^\\.drive\\s*\\{/.test(t)).join(' ')")
            ok("zones sûres iOS : marges env(safe-area-inset-top/bottom/left/right) sur le mode voiture",all(x in css for x in ["safe-area-inset-top","safe-area-inset-bottom","safe-area-inset-left","safe-area-inset-right"]),css[:300])
            vp=await page.evaluate("(document.querySelector('meta[name=viewport]')||{}).content||''")
            ok("zones sûres iOS : viewport-fit=cover déclaré","viewport-fit=cover" in vp,vp)
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_voiture.md"),"w",encoding="utf-8").write("# Tests registre n° 12 — mode voiture iPhone (16/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
