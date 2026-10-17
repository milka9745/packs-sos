# « Packs conseille, le médecin décide » (16/10/2026) : renouvellement psychiatrique signalé contre-indiqué → maintien motivé → impression.
# Données fictives. Lancer : python tests/test_ciover.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8774
MOTIF="traitement ancien prescrit par le spécialiste, renouvellement à l'identique"

async def unlock(page):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testci"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(900)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await page.get_by_text("Pas de garde",exact=True).first.click(); await page.wait_for_timeout(300)
    except Exception: pass

SETUP="""()=>{newPatient();Object.assign(state,{patient:'TEST Psy',ddn:'01/01/1976',date:'16/10/2026',sexe:'h'});state.cot.lieu='cabinet';
  const i=PACKS.findIndex(p=>p.n==='Renouvellement de traitement chronique');state.sel=i;render();const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');
  state.extra[si]=['ESCITALOPRAM 10 mg comprimé : 1 comprimé par jour, 3 mois.','HALOPÉRIDOL 1 mg comprimé : 1 comprimé par jour, 3 mois.'];render();return si;}"""

async def run(width,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":850 if width<500 else 950},device_scale_factor=2 if width<500 else 1,is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page(); errors=[]; dialogs=[]
        page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.dismiss())))
        await unlock(page); L=label+" "
        # bouton Imprimer sans fiche : explication, jamais grisé muet
        if width<500:
            await page.evaluate("newPatient();render();"); await page.wait_for_timeout(200)
            dis=await page.evaluate("document.getElementById('go_top').disabled")
            await page.click("#go_top"); await page.wait_for_timeout(200)
            t=await page.evaluate("(document.getElementById('toast')||{}).textContent||''")
            ok(L+"« Imprimer » sans fiche : actif, explique quoi faire",not dis and "Choisissez d'abord une fiche" in t,t)
        si=await page.evaluate(SETUP); await page.wait_for_timeout(300)
        al=await page.evaluate("checkAlerts(currentPack().s)")
        ok(L+"renouvellement ESCITALOPRAM + HALOPÉRIDOL : contre-indication détectée",any("CONTRE-INDICATION" in a for a in al),al[:2])
        await page.evaluate("window.__pr=0;window.print=()=>{window.__pr++;};0")
        dialogs.clear()
        await page.click("#go_top" if width<500 else "#go_only"); await page.wait_for_timeout(500)
        ok(L+"aucune fenêtre « Imprimer quand même ? » (plus de blocage par confirm)",not dialogs,dialogs[:1])
        ok(L+"écran « Avant d'imprimer » : motif, source, alternative",await page.locator("#ciover .cicard.ci").count()>=1 and "Thésaurus" in await page.inner_text("#ciover") and "Proposé" in await page.inner_text("#ciover"))
        ok(L+"une même contre-indication affichée une seule fois, sans libellé répété",await page.locator("#ciover .cicard.ci").count()==1 and not (await page.inner_text("#ciover .cicard.ci .cimot")).startswith("CONTRE-INDICATION"))
        ok(L+"conseils liés à l'alerte proposés, cochables",await page.locator("#ciover [data-cicons]").count()>=1)
        await page.screenshot(path=os.path.join(OUT,f"{label}-ci-alerte.png"))
        await page.click("#ci_keep"); await page.wait_for_timeout(200)
        ok(L+"« Je maintiens la prescription » : un geste, motif en une ligne avec 3 suggestions (+ 1 pour le QT)",await page.locator("#ci_why").is_visible() and await page.locator("#ciover [data-cichip]").count()==4)
        ok(L+"17/10 QT : motif « association ancienne prescrite par le spécialiste, ECG récent connu » proposé en premier",(await page.locator("#ciover [data-cichip]").first.get_attribute("data-cichip"))=="association ancienne prescrite par le spécialiste, ECG récent connu")
        ok(L+"17/10 QT : consigne patient cochable « palpitations, malaise ou perte de connaissance → 15 »","Palpitations, malaise ou perte de connaissance : appeler le 15." in await page.inner_text("#ciover"))
        ok(L+"17/10 QT : ECG fait / prescrit / non fait proposé",await page.locator("#ciover [name=ci_ecg]").count()==3)
        await page.locator("#ciover [data-cichip]").first.click()
        ok(L+"suggestion d'un toucher, modifiable",await page.input_value("#ci_why")=="association ancienne prescrite par le spécialiste, ECG récent connu")
        await page.locator("#ciover [name=ci_ecg][value=prescrit]").check()
        await page.fill("#ci_why",MOTIF+" (psychiatre)")
        n=await page.locator("#ciover [data-cicons]:not([disabled])").count()
        if n: await page.locator("#ciover [data-cicons]:not([disabled])").first.check()
        await page.screenshot(path=os.path.join(OUT,f"{label}-ci-maintien.png"))
        await page.click("#ci_print"); await page.wait_for_timeout(1500)
        pages=await page.evaluate("[...document.querySelectorAll('#print .page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}))")
        ordo="\n".join(x["t"] for x in pages if x["h"].startswith("Ordonnance"))
        ok(L+"aperçu et PDF après maintien (impression sur un toucher, depuis le PDF)",len(pages)>0 and await page.evaluate("window.__pr")==0)
        ok(L+"ordonnance imprimée avec les deux médicaments maintenus","ESCITALOPRAM" in ordo and "HALOPÉRIDOL" in ordo,ordo[:200])
        alltxt="\n".join(x["t"] for x in pages)
        ok(L+"motif et alerte jamais sur les documents imprimés",("psychiatre" not in alltxt) and ("passée outre" not in alltxt) and ("CONTRE-INDICATION" not in alltxt))
        if n: ok(L+"conseil coché ajouté aux consignes imprimées","appeler le 15" in alltxt.lower() or "conduire" in alltxt.lower())
        await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")
        cr=await page.evaluate("buildCR0(currentPack())")
        ok(L+"17/10 QT : ECG tracé au compte rendu (prescrit)","ECG : prescrit." in cr,[l for l in cr.split(chr(10)) if "outre" in l][:1])
        ok(L+"compte rendu : alerte passée outre, source et motif (traçabilité)","DÉCISIONS DE PRESCRIPTION" in cr and "psychiatre" in cr and "Thésaurus" in cr,[l for l in cr.split("\n") if "outre" in l][:1])
        j=await page.evaluate("JOURNAL.length?JOURNAL[JOURNAL.length-1].notes||[]:[]")
        ok(L+"journal : alerte et motif inscrits",any("psychiatre" in x and "outre" in x for x in j),j[-2:])
        dialogs.clear(); await page.click("#go_top" if width<500 else "#go_only"); await page.wait_for_timeout(800)
        ok(L+"réimpression : décision déjà prise, pas de nouvel écran",await page.locator("#ciover").count()==0 and await page.locator("#print .page").count()>0)
        await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")
        # règle légale de forme : stupéfiant → à faire, sans bloquer le reste
        await page.evaluate("""()=>{newPatient();Object.assign(state,{patient:'TEST Lombalgie',ddn:'01/01/1940',date:'16/10/2026'});state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();const p=currentPack();p.s.forEach((sh,si)=>resolve(sh,si).forEach(x=>{if(x.jr)state.lo[x.key]=true;}));render();}""")
        await page.click("#go_top" if width<500 else "#go_only"); await page.wait_for_timeout(600)
        if await page.locator("#ciover").count():
            ok(L+"stupéfiant : la règle de forme est expliquée dans l'écran d'alerte",await page.locator("#ciover .cicard.legal").count()==1)
            await page.click("#ci_keep"); await page.click("#ci_print"); await page.wait_for_timeout(1500)
        lw=await page.evaluate("(document.querySelector('#print .legalwarn')||{}).textContent||''")
        pages=await page.evaluate("[...document.querySelectorAll('#print .page')].map(x=>x.innerText).join(' ')")
        ok(L+"stupéfiant : « ordonnance sécurisée à rédiger à la main » affiché, le reste imprimé","Ordonnance sécurisée" in lw and "ACTISKENAN" not in pages and "BI-PROF" in pages,lw[:160])
        await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")
        # aucun bouton grisé sans explication sur les écrans principaux
        silent=[]
        for setup in ["newPatient();render();","state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();","state.view='journal';render();","state.view='tour';render();"]:
            await page.evaluate(setup); await page.wait_for_timeout(300)
            silent+=await page.evaluate("""()=>[...document.querySelectorAll('button[disabled],input[type=checkbox][disabled]')].filter(b=>b.offsetParent&&!b.title&&!b.getAttribute('aria-label')&&!(b.closest('label')&&/\\(|non |indisponible|activ/.test(b.closest('label').textContent))).map(b=>(b.id||b.className)+':'+b.textContent.trim().slice(0,30))""")
        await page.evaluate("state.view='';render();")
        ok(L+"aucun bouton grisé sans explication (accueil, fiche, journal, tournée)",not silent,silent)
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(1280,"pc"); await run(375,"iphone")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_ciover.md"),"w",encoding="utf-8").write("# Tests « Packs conseille, le médecin décide » (16/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
