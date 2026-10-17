# Audit « Express visite » (17/10/2026, partie A) : parcours ACTUEL de 3 visites fictives à 375 px, gestes comptés,
# éléments interactifs visibles relevés écran par écran, captures. Rien n'est modifié dans l'application.
# Lancer : python tests/audit_express.py  → tests/captures/express-avant-*.png et tests/resultats_audit_express.json
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
PORT=8780

STOPS="""()=>{newPatient();TOUR.stops=[
 {id:'v1',addr:'12 rue Bannier, 45000 Orléans',label:'12 Rue Bannier 45000 Orléans',lat:47.905,lon:1.904,city:'Orléans',nom:'DURAND Paul',ddn:'14/05/1985',tel:'0611111111',motif:'rhinopharyngite',ts:1,done:false},
 {id:'v2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.908,lon:1.865,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/03/2022',tel:'0622222222',motif:'fièvre',ts:2,done:false},
 {id:'v3',addr:'8 rue de la Lionne, 45000 Orléans',label:'8 Rue de la Lionne 45000 Orléans',lat:47.901,lon:1.899,city:'Orléans',nom:'MARTIN Jeanne',ddn:'03/04/1938',tel:'0633333333',motif:'chute',ts:3,done:false}];
 TOUR.order=['v1','v2','v3'];TOUR.legs=[{km:4,min:9},{km:6,min:12},{km:5,min:10}];TOUR.current='';TOUR.computed=Date.now();tourSave();state.cot=state.cot||cotDefault();state.cot.lieu='visite';state.view='';render();window.print=()=>{window.__pr=(window.__pr||0)+1;};window.open=()=>null;}"""

INV="""()=>{const H=innerHeight;const sel='button,a.btn,a.lc,input:not([type=hidden]),select,textarea,label.btn,summary,[role=button]';
  const all=[...document.querySelectorAll(sel)].filter(e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>2&&r.height>2&&cs.visibility!=='hidden'&&cs.display!=='none'&&!e.closest('[hidden],details:not([open])>*:not(summary)');});
  const lab=e=>(e.getAttribute('aria-label')||e.textContent||e.placeholder||e.name||e.id||'').replace(/\\s+/g,' ').trim().slice(0,38);
  const vp=all.filter(e=>{const r=e.getBoundingClientRect();return r.bottom>0&&r.top<H;});
  return {total:all.length,first:vp.length,screens:Math.round(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)/H*10)/10,labels:all.map(lab).filter(Boolean)};}"""

class Run:
    def __init__(s,page,visit): s.page=page; s.v=visit; s.g=[]; s.n=0
    async def tap(s,sel,why,kind="toucher"):
        loc=s.page.locator(sel).first
        await loc.scroll_into_view_if_needed(timeout=5000); await loc.click(timeout=5000); await s.page.wait_for_timeout(450)
        s.g.append((kind,why))
    async def type(s,sel,txt,why):
        loc=s.page.locator(sel).first
        await loc.scroll_into_view_if_needed(timeout=5000); await loc.fill(txt); await s.page.wait_for_timeout(300)
        s.g.append(("saisie",why))
    def dictate(s,why): s.g.append(("dictée",why))
    async def shot(s,name):
        s.n+=1; inv=await s.page.evaluate(INV)
        await s.page.evaluate("window.scrollTo(0,0)")
        await s.page.screenshot(path=os.path.join(OUT,f"express-avant-{s.v}-{s.n}-{name}.png"),full_page=False)
        if name in ("fiche-choisie","sur-place"):
            h=int(min(9000,inv["screens"]*812)); await s.page.set_viewport_size({"width":375,"height":h}); await s.page.wait_for_timeout(300)
            await s.page.screenshot(path=os.path.join(OUT,f"express-avant-{s.v}-{s.n}-{name}-long.png")); await s.page.set_viewport_size({"width":375,"height":812}); await s.page.wait_for_timeout(300)
        return {"ecran":name,**{k:inv[k] for k in ("total","first","screens")},"elements":inv["labels"][:400]}

async def unlock(page):
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","auditexpress"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
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

async def pick(page,R,name_re,why):
    # la recherche est pré-remplie avec le motif : toucher le résultat voulu
    btn=page.locator("#res button.res").filter(has_text=__import__("re").compile(name_re))
    if await btn.count()==0:
        await R.type("#q",name_re.split("|")[0],"rechercher la fiche"); btn=page.locator("#res button.res").filter(has_text=__import__("re").compile(name_re))
    await btn.first.scroll_into_view_if_needed(); await btn.first.click(); await page.wait_for_timeout(500); R.g.append(("toucher",why))

async def visit(page,vid,first,fiche_re,extra):
    R=Run(page,vid); screens=[]
    screens.append(await R.shot("accueil"))
    if first: await R.tap("#tc_begin","▶ Commencer (patient ouvert, identité, motif)")
    screens.append(await R.shot("patient-ouvert"))
    await R.tap(".tc-nav","🧭 Naviguer (Waze)")
    await R.tap("#tc_arrive","✓ Je suis arrivé")
    screens.append(await R.shot("sur-place"))
    await R.tap("#tc_dict","🎙 Dictée"); R.dictate("dicter l'observation (micro du clavier)")
    await page.evaluate("()=>{const f=document.getElementById('f_dict');if(f){f.value='Observation dictée de test.';f.dispatchEvent(new Event('input',{bubbles:true}));}}")
    screens.append(await R.shot("dictee"))
    await pick(page,R,fiche_re,"choisir la fiche dans la liste")
    screens.append(await R.shot("fiche-choisie"))
    for e in extra: await e(page,R)
    screens.append(await R.shot("avant-impression"))
    await R.tap("#go_top","🖨 Imprimer (aperçu)")
    if await page.locator("#ciover").count():
        await R.tap("#ci_keep","Je maintiens"); await R.tap("#ci_print","Imprimer malgré l'alerte")
    await page.wait_for_selector("#print .page",timeout=8000)
    screens.append(await R.shot("apercu"))
    await R.tap("#pb_send","Envoyer à l'imprimante")
    await R.tap("#pb_valid","✓ Valider le patient")
    screens.append(await R.shot("apres-validation"))
    # le récapitulatif de validation éventuel
    for sel,why in [("#vd_next","Patient suivant"),("#vd_ok","Confirmer la validation"),("#tc_valid","✓ Valider · patient suivant")]:
        if await page.locator(sel).count() and await page.locator(sel).first.is_visible():
            await R.tap(sel,why); screens.append(await R.shot("suivant")); break
    cur=await page.evaluate("TOUR.current||''")
    return {"visite":vid,"gestes":len([g for g in R.g if g[0]!="info"]),"detail":R.g,"ecrans":screens,"suivant_ouvert":cur}

async def poids(page,R):
    if await page.locator("#f_poids").count() and await page.locator("#f_poids").first.is_visible():
        await R.type("#f_poids","17","poids de l'enfant")

async def courrier(page,R):
    n=await page.evaluate("(()=>{const p=currentPack();return p?p.s.some(s=>s.k==='let'):false})()")
    R.g.append(("info","courrier présent dans la fiche : "+("oui" if n else "non")))

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1); out=[]
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True)
            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
            page=await ctx.new_page(); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page); await page.evaluate(STOPS); await page.wait_for_timeout(400)
            for vid,first,fre,extra in [("v1-rhino-adulte",True,"Rhinopharyngite",[]),("v2-fievre-enfant",False,"Fièvre.*enfant|Fièvre du nourrisson|Fièvre",[poids]),("v3-chute-courrier",False,"Chute du sujet âgé",[courrier])]:
                try: out.append(await visit(page,vid,first,fre,extra))
                except Exception as e: out.append({"visite":vid,"erreur":str(e)[:300]})
            await b.close()
    finally:
        srv.terminate()
    json.dump(out,open(os.path.join(ROOT,"tests","resultats_audit_express.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    for v in out: print(v["visite"],v.get("gestes"),v.get("erreur",""),[ (e["ecran"],e["total"],e["first"],e["screens"]) for e in v.get("ecrans",[])])
asyncio.run(main())
