# Documents imprimés — test PDF du 16/10/2026 (patient fictif, fiches « Chute du sujet âgé » + « Douleur en fin de vie »).
# Lancer : python tests/test_pdf16.py   (captures : tests/captures/pdf16-*.png)
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8773
CHUTE="Chute du sujet âgé — bilan"; FDV="Douleur en fin de vie"

async def unlock(page):
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testpdf"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
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

SETUP="""(names)=>{state.sel=null;state.obs={};state.cst={};state.actions={};state.lo={};state.gs={};state.off={};state.extra={};state.libre={};Object.assign(state,{patient:'MARTIN Jeanne',ddn:'03/04/1938',date:'16/10/2026',sexe:'f',poids:'',photos:[]});
  const idx=names.map(n=>PACKS.findIndex(p=>p.n===n));state.sel=idx.length===1?idx[0]:idx;render();return idx;}"""
PAGES="""()=>[...document.querySelectorAll('#print .page')].map((pg,i)=>{const fr=pg.querySelector('.frame');const h=pg.querySelector('h2');
  const z=fr?[...fr.querySelectorAll('.stamp,.sig')].map(e=>e.getBoundingClientRect()).filter(r=>r.height):[];
  const txt=fr?[...fr.querySelectorAll('p,li,h2,h3,td,th,.meta')].filter(e=>!e.closest('.stamp,.sig')):[];
  const hit=[];z.forEach(r=>txt.forEach(e=>{const t=e.getBoundingClientRect();if(t.height&&t.bottom>r.top+0.5&&t.top<r.bottom&&t.right>r.left&&t.left<r.right)hit.push(e.textContent.slice(0,40));}));
  const clipped=fr&&getComputedStyle(fr).overflow==='hidden'&&fr.scrollHeight>fr.clientHeight+1;
  return {i,t:h?h.textContent:'',hit,clipped,over:pg.dataset.over||'',fit:pg.dataset.fit||'',txt:fr?fr.innerText:''};})"""

async def preview(page,width):
    await page.evaluate("window.print=()=>{window.__pr=(window.__pr||0)+1;}")
    await page.click("#go_top" if width<500 else "#go_only"); await page.wait_for_timeout(1500)

async def back(page):
    await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")

async def run(width,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":850 if width<500 else 1000},device_scale_factor=2 if width<500 else 1,is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page(); errors=[]; dialogs=[]
        page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
        await unlock(page); L=label+" "
        await page.evaluate(SETUP,[CHUTE,FDV]); await page.wait_for_timeout(300)
        # 4. fiche Chute : HbA1c en option non cochée
        bio=await page.evaluate("""()=>{const p=currentPack();const si=p.s.findIndex(s=>s.k==='bio');return resolve(p.s[si],si).filter(x=>/HbA1c|Glycémie/.test(x.t)).map(x=>({t:x.t,on:x.on,opt:!!x.opt}));}""")
        ok(L+"n°4 Chute : HbA1c en option, non cochée par défaut ; glycémie cochée",any("HbA1c" in x["t"] and not x["on"] and x["opt"] for x in bio) and any(x["t"].startswith("Glycémie") and x["on"] for x in bio),bio)
        await preview(page,width)
        pg=await page.evaluate(PAGES)
        ok(L+"n°1 aucune ligne de texte ne chevauche le cachet ou la signature (tous les documents)",all(not x["hit"] for x in pg),[(x["t"],x["hit"]) for x in pg if x["hit"]])
        ok(L+"n°1 aucun texte masqué (jamais de débordement coupé)",all(not x["clipped"] for x in pg),[x["t"] for x in pg if x["clipped"]])
        let=[x for x in pg if x["t"]=="Courrier"]
        ok(L+"n°2 deux fiches avec courrier : deux pages « Courrier », une par destinataire",len(let)==2 and "gériatre" in let[0]["txt"] and "hospitalisation à domicile" in let[1]["txt"] and "gériatre" not in let[1]["txt"],[x["txt"][:80] for x in let])
        ok(L+"n°2 chaque courrier : une seule ligne de signature",all(sum(1 for ln in x["txt"].split(chr(10)) if ln.strip().startswith("Docteur"))==1 for x in let),[[ln for ln in x["txt"].split(chr(10)) if ln.strip().startswith("Docteur")] for x in let])
        ok(L+"n°2 chaque courrier : formule d'appel, formule finale et signature",all(("Cher confrère" in x["txt"]) and ("sentiments confraternels" in x["txt"]) and ("Docteur" in x["txt"]) for x in let),[x["txt"][-200:] for x in let])
        cons=[x for x in pg if x["t"].startswith("Consignes")]
        ok(L+"n°2 consignes de deux fiches : un titre par fiche",(len(cons)==1 and "Chute du sujet âgé" in cons[0]["txt"] and "Douleur en fin de vie" in cons[0]["txt"]) or len(cons)==2,[x["t"] for x in cons])
        alltxt="\n".join(x["txt"] for x in pg)
        ok(L+"n°3 « médicaments revus » absent tant que l'action n'est ni cochée ni dictée",("revu les médicaments" not in alltxt) and ("ont été revus" not in alltxt))
        ok(L+"n°3 aucun renvoi au compte rendu joint (non imprimé)","compte rendu joint" not in alltxt.lower())
        ok(L+"n°3 « J'ai prescrit » liste ce qui est coché (NFS, CRP, ECG, kinésithérapie) et pas l'HbA1c non cochée","J'ai prescrit un bilan biologique (NFS" in alltxt and "CRP" in alltxt and "un ECG" in alltxt and "kinésithérapie" in alltxt and "HbA1c" not in alltxt.split("J'ai prescrit")[1].split(".")[0],alltxt[alltxt.find("J'ai prescrit"):][:300])
        if width>=500:
            for n,(nm,sel) in enumerate([("courrier-geriatre",0),("courrier-had",1)]):
                el=page.locator("#print .page").nth(let[sel]["i"]); await el.scroll_into_view_if_needed(); await el.screenshot(path=os.path.join(OUT,f"pdf16-{nm}.png"))
            el=page.locator("#print .page").nth(cons[0]["i"]); await el.scroll_into_view_if_needed(); await el.screenshot(path=os.path.join(OUT,"pdf16-consignes.png"))
        await back(page)
        # 3. actions cochées ou dictées, examens décochés / cochés
        ok(L+"n°3 case « Médicaments revus » proposée (une consigne en parle)",await page.locator("#act_meds").count()==1)
        await page.check("#act_meds"); await page.wait_for_timeout(300)
        await page.evaluate("""()=>{const p=currentPack();const si=p.s.findIndex(s=>s.k==='bio');const r=resolve(p.s[si],si);const crp=r.find(x=>/^CRP/.test(x.t));const hb=r.find(x=>/HbA1c/.test(x.t));state.lo[crp.key]=false;state.lo[hb.key]=true;state.obs.hist='Chute de sa hauteur ce matin, relevée par sa fille, pas de perte de connaissance.';render();}""")
        await preview(page,width); pg=await page.evaluate(PAGES); alltxt="\n".join(x["txt"] for x in pg)
        ph=alltxt[alltxt.find("J'ai prescrit"):].split(".")[0] if "J'ai prescrit" in alltxt else ""
        ok(L+"n°3 action cochée : « revu les médicaments » et « ont été revus » apparaissent","revu les médicaments" in alltxt and "ont été revus" in alltxt)
        ok(L+"n°3 liste des examens exacte : CRP décochée absente, HbA1c cochée présente","CRP" not in ph and "HbA1c" in ph,ph[:300])
        ok(L+"n°3 éléments dictés repris à la place du renvoi au compte rendu","Éléments recueillis ce jour" in alltxt and "relevée par sa fille" in alltxt)
        ok(L+"n°1 après modification : toujours aucun chevauchement du cachet",all(not x["hit"] for x in pg) and all(not x["clipped"] for x in pg))
        await back(page)
        # 1. contenu trop long : police réduite, sinon alerte ; jamais masqué
        await page.evaluate(SETUP,[FDV]); await page.wait_for_timeout(200)
        found=None
        for nrep in [12,14,16,18,20,22]:
            await page.evaluate("""(n)=>{const p=currentPack();const si=p.s.findIndex(s=>s.k==='cons');state.libre[si]=Array(n).fill("Consigne supplémentaire de test : surveiller la douleur, l'alimentation, l'hydratation, le transit et le sommeil, noter les doses supplémentaires prises.").join(" ");render();}""",nrep)
            await preview(page,width); pg=await page.evaluate(PAGES); c=[x for x in pg if x["t"].startswith("Consignes")]
            await back(page)
            if c and c[0]["fit"]: found=(nrep,c[0]); break
        ok(L+"n°1 consignes longues : police réduite (≥ 9 pt) sans chevauchement ni texte masqué",found and not found[1]["hit"] and not found[1]["clipped"] and not found[1]["over"] and float(found[1]["fit"])>=0.8,found and (found[0],{k:found[1][k] for k in ("fit","over","hit","clipped")}))
        await page.evaluate("""()=>{const p=currentPack();const si=p.s.findIndex(s=>s.k==='cons');state.libre[si]=Array(60).fill("Consigne très longue de test pour dépasser une page même en petite police.").join(" ");render();}""")
        dialogs.clear(); await preview(page,width); pg=await page.evaluate(PAGES); c=[x for x in pg if x["t"].startswith("Consignes")]
        warn=await page.evaluate("(document.querySelector('#print .fitwarn')||{}).textContent||''")
        ok(L+"n°1 trop long même à 9 pt : alerte à l'écran avant impression, texte jamais masqué",c and c[0]["over"] and not c[0]["clipped"] and "ne tient pas sur une page" in warn,{k:(c[0][k] if c else None) for k in ("over","clipped")})
        await back(page)
        # 4. fiche « sujet âgé » chez un patient de moins de 65 ans
        await page.evaluate(SETUP,[CHUTE]); await page.evaluate("Object.assign(state,{ddn:'01/01/1974'});render();"); await page.wait_for_timeout(200)
        ok(L+"n°4 fiche « sujet âgé » à 52 ans : alerte à l'écran",await page.locator(".agemis").count()>=1 and "65 ans" in await page.inner_text(".agemis"))
        # aucun pack du catalogue ne renvoie au compte rendu joint (contrôle sur toutes les fiches avec courrier ou consignes)
        bad=await page.evaluate("""()=>{const out=[];PACKS.forEach((p,i)=>{if(!p.s.some(s=>['let','cons','cert'].includes(s.k)))return;state.sel=i;state.obs={};state.actions={};try{const r=buildPages(currentPack(),false).out.replace(/<[^>]+>/g,' ');if(/compte[- ]rendu joint/i.test(r))out.push(p.n);if(/revu les médicaments|ont été revus/.test(r))out.push(p.n+' (revus)');}catch(e){out.push(p.n+' : '+e.message);}});state.sel=null;render();return out;}""")
        ok(L+"n°3 toutes les fiches : ni « compte rendu joint » ni « médicaments revus » non cochés dans les documents",not bad,bad[:8])
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
    open(os.path.join(ROOT,"tests","resultats_pdf16.md"),"w",encoding="utf-8").write("# Tests documents imprimés — test PDF du 16/10/2026\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
