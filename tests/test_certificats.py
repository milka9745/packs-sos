# Certificats avec durée (17/10/2026) : 1 jour par défaut, − / + ou saisie, « du … au … inclus » imprimé, durée au CR et au journal,
# visible dans l'Express quand le certificat s'applique. 375 px (jour, nuit, grand texte) et ordinateur. Patients fictifs.
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:400])
PORT=8788
STOPS=open(os.path.join(ROOT,"tests","audit_express.py"),encoding="utf-8").read().split('STOPS="""')[1].split('"""')[0]
async def unlock(page,uid):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
CERTTXT="""()=>{const p=currentPack();const out=buildPages(p,true).out;const d=document.createElement('div');d.innerHTML=out;return [...d.querySelectorAll('.page')].map(x=>x.innerText).filter(t=>/certifie/.test(t)).join('\\n');}"""
SETP="""(a)=>{newPatient();const i=PACKS.findIndex(p=>p.n===a.n);Object.assign(state,{patient:a.pat||'PETIT Lou',ddn:a.ddn||'01/03/2022',sexe:'f',date:'17/10/2026'});state.view='';state.sel=i;if(a.f)state.f=Object.assign({},a.f);
  if(a.grp){const p=currentPack();const si=p.s.findIndex(s=>s.k==='cert');const r=resolve(p.s[si],si);const x=r.find(y=>y.grp&&new RegExp(a.grp).test(y.t));if(x)state.gs[si+':'+x.grp]=x.key;}render();return i;}"""
async def run(b,w,h,th,big,label):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    page.on("popup",lambda pg:asyncio.ensure_future(pg.close()))
    await unlock(page,"cert"+label.replace(" ","")[:8]); L=label+" : "; tag=label.replace(" ","-")
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
    # enfant malade : 1 jour par défaut
    await page.evaluate(SETP,{"n":"Certificat — enfant malade"}); await page.wait_for_timeout(300)
    t=await page.evaluate(CERTTXT)
    ok(L+"enfant malade : 1 jour par défaut, « du 17/10/2026 au 17/10/2026 inclus » imprimé","du 17/10/2026 au 17/10/2026 inclus" in t,t[:200])
    vis=page.locator(".certdur").first
    ok(L+"réglage de durée visible (Express ou mode complet)",await vis.is_visible())
    ok(L+"« − » inactif à 1 jour",await page.locator('.certdur [data-cd="-1"]').first.is_disabled())
    bh=await page.evaluate("Math.min(...[...document.querySelectorAll('.certdur .cdb')].filter(x=>x.offsetParent).map(x=>x.getBoundingClientRect().height))")
    ok(L+"boutons − / + d'au moins 44 px",bh>=44,bh)
    await page.locator('.certdur [data-cd="1"]').first.click(); await page.wait_for_timeout(250)
    t=await page.evaluate(CERTTXT)
    ok(L+"« + » : 2 jours, « du 17/10/2026 au 18/10/2026 inclus »","du 17/10/2026 au 18/10/2026 inclus" in t,t[:200])
    await page.locator('.certdur [data-cdin]').first.fill("5"); await page.locator('.certdur [data-cdin]').first.dispatch_event("change"); await page.wait_for_timeout(250)
    t=await page.evaluate(CERTTXT)
    ok(L+"saisie 5 jours : « du 17/10/2026 au 21/10/2026 inclus »","du 17/10/2026 au 21/10/2026 inclus" in t,t[:200])
    await page.locator('.certdur [data-cddu]').first.fill("20102026"); await page.locator('.certdur [data-cddu]').first.dispatch_event("change"); await page.wait_for_timeout(250)
    t=await page.evaluate(CERTTXT)
    ok(L+"à partir du 20/10 : « du 20/10/2026 au 24/10/2026 inclus »","du 20/10/2026 au 24/10/2026 inclus" in t,t[:200])
    sw=await page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
    ok(L+"aucun débordement horizontal",sw[0]<=sw[1],sw)
    if mob:
        await page.evaluate("document.querySelector('.certdur').scrollIntoView({block:'center'})"); await page.wait_for_timeout(200)
        await page.screenshot(path=os.path.join(OUT,f"certificat-duree-{tag}.png"))
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"durée au compte rendu","Certificat remis (enfant malade : 5 jours, du 20/10/2026 au 24/10/2026 inclus)" in cr,[l for l in cr.split(chr(10)) if "ertificat" in l])
    await page.evaluate("journalUpsert(currentPack())")
    j=await page.evaluate("JSON.stringify(JOURNAL[JOURNAL.length-1].cert||null)")
    ok(L+"durée au journal",'"j":5' in j and "20/10/2026" in j and "24/10/2026" in j,j)
    await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(200)
    ok(L+"journal : durée affichée","5 jours, du 20/10/2026 au 24/10/2026 inclus" in await page.inner_text("#main"))
    await page.evaluate("state.view='';render();")
    # autres certificats avec durée
    for n,grp,lbl in [("Certificat — dispense de sport",None,"dispense de sport"),("Certificat d'arrêt de sport",None,"arrêt de sport"),("Certificats courants","piscine","dispense de piscine")]:
        await page.evaluate(SETP,{"n":n,"grp":grp,"pat":"DURAND Paul","ddn":"14/05/2010","f":{"type":"totale"}}); await page.wait_for_timeout(250)
        t=await page.evaluate(CERTTXT)
        ok(L+f"{lbl} : 1 jour par défaut, « du … au … inclus »","du 17/10/2026 au 17/10/2026 inclus" in t and await page.locator(".certdur").count()>=1,t[:220])
    await page.evaluate(SETP,{"n":"Certificats courants","pat":"DURAND Paul","ddn":"14/05/2010"}); await page.wait_for_timeout(250)
    ok(L+"certificat sans durée (sport, par défaut) : pas de réglage de durée",await page.locator(".certdur").count()==0)
    # Express : n'apparaît que quand le certificat s'applique
    await page.evaluate(STOPS); await page.evaluate("xpOpenStop('v2')"); await page.wait_for_timeout(300); await page.click("#xp_ok"); await page.wait_for_timeout(400)
    ok(L+"Express (fièvre de l'enfant) : pas de réglage de durée sans certificat",await page.locator(".xp .certdur").count()==0)
    await page.check("#xp_cem"); await page.wait_for_timeout(400)
    ok(L+"Express : « Certificat enfant malade » coché → durée visible (1 jour)",await page.locator(".xp .certdur").count()==1 and await page.input_value(".xp [data-cdin]")=="1")
    await page.locator('.xp .certdur [data-cd="1"]').click(); await page.wait_for_timeout(300)
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"Express : + → 2 jours, au compte rendu","enfant malade : 2 jours, du 17/10/2026 au 18/10/2026 inclus" in cr,[l for l in cr.split(chr(10)) if "ertificat" in l])
    if mob:
        await page.evaluate("document.querySelector('.xp .certdur').scrollIntoView({block:'center'})"); await page.wait_for_timeout(2800)
        await page.screenshot(path=os.path.join(OUT,f"certificat-express-{tag}.png"))
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,th,big,lbl) in [(375,812,"day",False,"iphone jour"),(375,812,"night",False,"iphone nuit"),(375,812,"night",True,"iphone grand texte"),(1280,900,"day",False,"ordinateur")]:
                await run(b,w,h,th,big,lbl)
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_certificats.md"),"w",encoding="utf-8").write("# Tests certificats avec durée (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
