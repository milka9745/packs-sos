# Favoris → Express (17/10/2026, point h) : étoile sur les éléments du mode complet, ajout et retrait, affichage seulement quand
# l'élément s'applique, éléments de sécurité fixés sans étoile, retour à l'Express par défaut, persistance après rechargement (chiffrée, par profil).
# 375 px (jour, nuit, grand texte) et ordinateur. Patients fictifs. Lancer : python tests/test_favoris.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
PORT=8786
STOPS=open(os.path.join(ROOT,"tests","audit_express.py"),encoding="utf-8").read().split('STOPS="""')[1].split('"""')[0]

async def unlock(page,uid):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)

async def relock(page,uid):
    await page.evaluate("FAV.keys=null")  # mémoire vidée : ce qui revient vient du stockage chiffré
    await page.reload(); await page.wait_for_timeout(2500)
    if await page.locator("#pin1").count():
        await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.click("#pin_ok")
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(800)

OPEN_PLUS="""()=>{const d=document.getElementById('xp_plus');if(d)d.open=true;document.querySelectorAll('#main details.pmore,#main .pcard details').forEach(x=>x.open=true);}"""
async def star(page,key):
    await page.evaluate("if(!FAV.edit)favEditSet(true)"); await page.wait_for_timeout(250)  # 21/10/2026 : étoiles visibles seulement en mode « Modifier les favoris »
    await page.evaluate(OPEN_PLUS); await page.wait_for_timeout(150)
    loc=page.locator(f'#main .favstar[data-favk="{key}"]').first
    await loc.scroll_into_view_if_needed(); await loc.click(); await page.wait_for_timeout(400)

async def run(b,w,h,th,big,label):
    mob=w<500; uid="fav"+label.replace(" ","")[:8]
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    page.on("popup",lambda pg:asyncio.ensure_future(pg.close()))
    await unlock(page,uid)
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
    await page.evaluate(STOPS); await page.wait_for_timeout(300)
    L=label+" : "; tag=label.replace(" ","-")
    await page.evaluate("xpOpenStop('v1')"); await page.wait_for_timeout(300); await page.click("#xp_ok"); await page.wait_for_timeout(500)
    ok(L+"Express par défaut : pas d'« Allergies »",await page.locator(".xp .tt.al").count()==0)
    # 21/10/2026 : étoiles masquées hors du mode « Modifier les favoris » ; démarquage facile (✎ Favoris → ★ → Terminé)
    ok(L+"étoiles ★ masquées par défaut, lien « ✎ Favoris » dans l'en-tête Express",await page.locator("#main .favstar:visible").count()==0 and await page.locator("#xp_favedit").count()==1 and await page.locator("#favbar").count()==0)
    await page.click("#xp_favedit"); await page.wait_for_timeout(350)
    ok(L+"✎ Favoris : bandeau « Terminé », étoiles visibles (retrait d'un toucher)",await page.locator("#favbar").count()==1 and await page.locator("#main .favstar:visible").count()>0 and await page.locator(".xp .favstar.on:visible").count()>0)
    await page.click("#fav_done"); await page.wait_for_timeout(350)
    ok(L+"« Terminé » : étoiles de nouveau masquées, favoris inchangés",await page.locator("#main .favstar:visible").count()==0 and await page.locator("#favbar").count()==0 and await page.locator(".xp #xp_favs #tc_view").count()==1)
    ok(L+"chaque élément du mode complet porte une étoile (champs, documents, sections, boutons)",await page.evaluate("""(()=>{const k=[...document.querySelectorAll('#main .favstar')].map(s=>s.dataset.favk);return ['f:f_al','f:f_tt','f:f_date','sec:cot','sec:pho','sec:nh','btn:fin'].every(x=>k.includes(x))&&k.some(x=>x.startsWith('doc:'));})()"""),await page.evaluate("[...new Set([...document.querySelectorAll('#main .favstar')].map(s=>s.dataset.favk))]"))
    ok(L+"sécurité fixée, sans étoile : gravité, doses, alertes",await page.locator(".xp .xp-grav .favstar, .xp .xp-meds .favstar, .xp .xp-alerts .favstar").count()==0 and await page.locator(".xp .xp-meds").count()==1)
    # ajouter « Allergies »
    await star(page,"f:f_al")
    ok(L+"☆ « Allergies » : ajouté à l'Express (★)",await page.locator(".xp #xp_favs .tt.al").count()==1 and await page.locator('.xp #xp_favs .favstar.on[data-favk="f:f_al"]').count()==1)
    ok(L+"champ « Allergies » utilisable dans l'Express",await page.locator(".xp #f_al").is_visible())
    if mob: await page.evaluate("window.scrollTo(0,0);const d=document.getElementById('xp_plus');if(d)d.open=false;"); await page.wait_for_timeout(200); await page.evaluate("document.querySelector('.xp #xp_favs').scrollIntoView({block:'center'})"); await page.wait_for_timeout(2800); await page.screenshot(path=os.path.join(OUT,f"favoris-{tag}-allergies.png"))
    # s'applique seulement quand le choix précédent l'appelle : pas sur l'accueil (aucun patient)
    await page.evaluate("newPatient();TOUR.current='';render();"); await page.wait_for_timeout(300)
    ok(L+"accueil (aucun patient) : « Allergies » absent de l'Express",await page.locator(".xp-home").count()==1 and await page.locator(".xp .tt.al").count()==0)
    # document favori : n'apparaît que si la fiche contient ce document
    await page.evaluate("xpOpenStop('v3')"); await page.wait_for_timeout(300); await page.click("#xp_ok"); await page.wait_for_timeout(500)
    await star(page,"doc:kine")
    ok(L+"document favori « Kinésithérapie » : présent pour la chute",await page.locator('.xp #xp_favs [data-fav="doc:kine"]').count()==1)
    await page.evaluate("newPatient();xpOpenStop('v1');"); await page.wait_for_timeout(300); await page.click("#xp_ok"); await page.wait_for_timeout(500)
    ok(L+"document favori absent quand la fiche ne l'a pas (rhinopharyngite)",await page.locator('.xp [data-fav="doc:kine"]').count()==0 and await page.locator(".xp #xp_favs .tt.al").count()==1)
    # retrait d'un élément par défaut (arrêt de travail) puis de l'Allergie
    await page.evaluate("if(!FAV.edit)favEditSet(true)"); await page.wait_for_timeout(250)
    await page.locator('.xp .favstar[data-favk="sec:at"]').click(); await page.wait_for_timeout(300)
    ok(L+"élément par défaut retirable (« Arrêt de travail fait »)",await page.locator(".xp #xp_at").count()==0)
    # persistance après rechargement
    keys=await page.evaluate("FAV.keys")
    await relock(page,uid)
    k2=await page.evaluate("FAV.keys")
    ok(L+"persistance après rechargement",k2==keys and "f:f_al" in k2 and "sec:at" not in k2,[keys,k2])
    ls=await page.evaluate("JSON.stringify(Object.keys(localStorage).filter(k=>k.startsWith('sos_xpfav')))")
    ok(L+"rangés chiffrés, par profil",'sos_xpfav_specimen_enc' in ls,ls)
    await page.evaluate("xpOpenStop('v1')") if await page.evaluate("!TOUR.current") else None
    await page.wait_for_timeout(300)
    if await page.locator("#xp_ok").count(): await page.click("#xp_ok"); await page.wait_for_timeout(400)
    ok(L+"après rechargement : « Allergies » toujours dans l'Express",await page.locator(".xp #xp_favs .tt.al").count()==1)
    await page.evaluate("if(!FAV.edit)favEditSet(true)"); await page.wait_for_timeout(250)
    await page.locator('.xp .favstar[data-favk="f:f_al"]').first.click(); await page.wait_for_timeout(400)
    ok(L+"★ « Allergies » : retiré de l'Express",await page.locator(".xp .tt.al").count()==0 and "f:f_al" not in await page.evaluate("FAV.keys"))
    # poids : fixé chez l'enfant (sans étoile)
    await page.evaluate("newPatient();xpOpenStop('v2');"); await page.wait_for_timeout(300); await page.click("#xp_ok"); await page.wait_for_timeout(400)
    ok(L+"poids de l'enfant fixé, sans étoile",await page.locator(".xp #xp_poids").count()==1 and await page.locator('.xp .favstar[data-favk="f:f_poids"]').count()==0)
    # revenir à l'Express par défaut
    await page.evaluate("favReset()"); await page.wait_for_timeout(300)
    ok(L+"« Revenir à l'Express par défaut » : jeu de départ rétabli",await page.evaluate("FAV.keys===null") and await page.locator(".xp #xp_at").count()==1 and await page.locator(".xp .tt.al").count()==0)
    if mob:
        await page.click("#more_btn"); await page.wait_for_timeout(300)
        ok(L+"bouton « Revenir à l'Express par défaut » dans ⋯",await page.locator("#jmenu [data-xpreset]").is_visible())
        ok(L+"bouton « Modifier les favoris de l'Express (★) » dans ⋯ (21/10)",await page.locator("#jmenu [data-favedit]").count()==1)
        await page.click("#more_btn"); await page.wait_for_timeout(200)
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def profil(b):
    # favoris dans profil.json (chiffrés avec la phrase) et retrouvés sur un autre appareil
    ctx=await b.new_context(viewport={"width":1280,"height":900}); page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    await unlock(page,"favprof1"); L="profil : "
    kit=await page.evaluate("""async()=>{FAV.keys=['x:nav','x:call','f:f_al','sec:cot'];const st='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
      return JSON.stringify(await kitEncrypt({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:st},'girafe crayon lune cabane fraise galet'));}""")
    ok(L+"favoris absents en clair de profil.json","f:f_al" not in kit)
    await ctx.close()
    ctx=await b.new_context(viewport={"width":1280,"height":900}); page=await ctx.new_page(); page.on("pageerror",lambda e:errors.append(str(e)))
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    await unlock(page,"favprof2")
    r=await page.evaluate("async(k)=>{await identActivate(k,'girafe crayon lune cabane fraise galet');return {keys:FAV.keys,prof:favProf()};}",kit)
    ok(L+"autre appareil : favoris retrouvés après la phrase maître, rangés sous ce profil",r["keys"]==['x:nav','x:call','f:f_al','sec:cot'] and r["prof"]!="specimen",r)
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,th,big,lbl) in [(375,812,"day",False,"iphone jour"),(375,812,"night",False,"iphone nuit"),(375,812,"night",True,"iphone grand texte"),(1280,900,"day",False,"ordinateur")]:
                await run(b,w,h,th,big,lbl)
            await profil(b)
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_favoris.md"),"w",encoding="utf-8").write("# Tests favoris → Express (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
