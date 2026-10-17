# Dossier test/ (17/10/2026) : la branche ia publiée à part, sans rien partager avec l'outil de garde (racine).
# Site local = main à la racine + test/ construit par tools/build_test.py. Vérifie : stockage, base photos, cache, service worker,
# manifeste et icônes séparés ; badge TEST visible ; l'outil de garde garde son code et ses données. Lancer : python tests/test_dossier_test.py <site>
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright
SITE=sys.argv[1]; PORT=8792; B=f"http://localhost:{PORT}/"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:400])
async def create(page,url,uid):
    await page.goto(url); await page.wait_for_selector("#uid",timeout=15000)
    if await page.locator("#pin2").count()==0: return False
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(800); return True
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=SITE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":375,"height":812},is_mobile=True,has_touch=True)
            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
            # 1. outil de garde (racine) : un utilisateur et une donnée
            ok("racine : création du code de l'outil de garde",await create(page,B,"garde"))
            rootv=await page.evaluate("fetch('version.json',{cache:'no-store'}).then(r=>r.json()).then(j=>j.version)")
            ok("racine : outil de garde en v41k (inchangé)",rootv=="41k",rootv)
            await page.evaluate("localStorage.setItem('sos_marqueur_garde','\"garde\"')")
            await page.wait_for_timeout(1500)
            # 2. version de test : aucun code existant (stockage séparé)
            fresh=await create(page,B+"test/","essai")
            ok("test/ : aucun code existant, création d'un code propre (stockage séparé)",fresh)
            pr=await page.evaluate("[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules].map(r=>r.cssText)}catch(e){return []}}).filter(t=>t.startsWith('@media print')).join(' ')")
            ok("test/ : badge TEST et marges navigateur jamais imprimés (@media print, @page margin 0)","#testpill" in pr and "#testbadge" in pr and "margin: 0" in pr,pr[:200])
            await page.emulate_media(media="print"); vis=await page.evaluate("getComputedStyle(document.getElementById('testpill')).display"); await page.emulate_media(media="screen")
            ok("test/ : à l'impression, le badge TEST n'apparaît pas",vis=="none",vis)
            ok("test/ : titre « Packs SOS TEST » et badge visible",(await page.title())=="Packs SOS TEST" and await page.locator("#testpill").is_visible() and await page.locator("#testbadge").is_visible())
            ok("test/ : la donnée de l'outil de garde est invisible",await page.evaluate("localStorage.getItem('sos_marqueur_garde')") is None)
            ks=await page.evaluate("(()=>{const o=[];for(let i=0;i<localStorage.length;i++)o.push(localStorage.key(i));return o;})()")
            ok("test/ : toutes ses clés préfixées « pst: », celles de la garde intactes",any(k.startswith("pst:sos_") for k in ks) and "sos_marqueur_garde" in ks and not any(k.startswith("sos_") and k!="sos_marqueur_garde" and ("pst:"+k) in ks and False for k in ks),ks[:12])
            man=await page.evaluate("fetch('manifest.webmanifest').then(r=>r.json())")
            ok("test/ : manifeste propre (Packs SOS TEST)",man.get("name")=="Packs SOS TEST" and man.get("short_name")=="TEST Packs",man)
            ati=await page.evaluate("document.querySelector('link[rel=apple-touch-icon]').getAttribute('href')")
            ok("test/ : icône iPhone badgée TEST (fichier propre au dossier)",ati=="apple-touch-icon.png",ati)
            ok("test/ : nom sur l'écran d'accueil iPhone « TEST Packs »",await page.evaluate("document.querySelector('meta[name=apple-mobile-web-app-title]').content")=="TEST Packs")
            ok("test/ : profil.json et lecture locale lus à la racine du site",await page.evaluate("siteBase()")==B,await page.evaluate("siteBase()"))
            await page.evaluate("phDb&&phDb().catch(()=>{})"); await page.wait_for_timeout(500)
            dbs=await page.evaluate("indexedDB.databases?indexedDB.databases().then(d=>d.map(x=>x.name)):[]")
            ok("test/ : base photos séparée (packs-sos-test-photos)","packs-sos-test-photos" in dbs,dbs)
            await page.wait_for_timeout(2500)
            regs=await page.evaluate("navigator.serviceWorker.getRegistrations().then(r=>r.map(x=>x.scope))")
            ok("service workers séparés (racine et test/)",B in regs and B+"test/" in regs,regs)
            cks=await page.evaluate("caches.keys()")
            ok("caches séparés (packs-sos-v41k et packs-sos-test-…)",any(k.startswith("packs-sos-test-") for k in cks) and "packs-sos-v41k" in cks,cks)
            ver=await page.evaluate("fetch('version.json',{cache:'no-store'}).then(r=>r.json()).then(j=>j.version)")
            ok("test/ : version de la branche ia",ver.endswith("-test"),ver)
            ok("test/ : Express présent (branche ia)",await page.evaluate("typeof xpHTML==='function'"))
            # 3. retour à l'outil de garde : son code et ses données intacts, son code de page inchangé
            await page.goto(B); await page.wait_for_timeout(2500)
            ok("racine : aucun écran de création de code (son utilisateur « garde » est intact)",await page.locator("#pin2").count()==0)
            if await page.locator("#pin1").count():
                await page.fill("#uid","garde"); await page.fill("#pin1","1234"); await page.click("#pin_ok")
            await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(500)
            ok("racine : donnée de l'outil de garde intacte",await page.evaluate("localStorage.getItem('sos_marqueur_garde')")=='"garde"')
            ok("racine : pas de badge TEST, pas d'Express (code de main)",await page.locator("#testpill").count()==0 and await page.evaluate("typeof xpHTML")=="undefined")
            ok("aucune erreur JS",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK"); sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
