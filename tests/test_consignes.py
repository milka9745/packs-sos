# -*- coding: utf-8 -*-
# Feuille « Consignes au patient » décochée par défaut (18/11/2026, v42f) — demande du Docteur DEIE : « que les conseils ne soient pas
# automatiquement cochés et que ce soit si je coche que c'est imprimé ».
# Vérifie : feuille décochée et signalée « non imprimée » à l'ouverture d'une fiche ; aucune page Consignes (aperçu réel et buildPages),
# ni au compte rendu, ni dans le compte des documents ; cochée par l'en-tête → page imprimée avec les consignes de la fiche ;
# se servir de la feuille la coche (consigne recochée, « Tout cocher », consigne ajoutée, texte tapé sans Entrée) ; une feuille décochée
# par le médecin reste décochée ; « Nouveau patient » la remet décochée ; Express : case « Consignes au patient » (favori par défaut,
# ajouté une fois aux favoris déjà enregistrés). iPhone 375 px et ordinateur 1280 px, mode complet et Express. Patient fictif.
# Lancer : python tests/test_consignes.py
import asyncio, os, sys, subprocess, time
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding="utf-8")
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8820
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])

async def unlock(page,uid,xp):
    await page.add_init_script("try{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','"+("true" if xp else "false")+"')}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=60000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
    await page.evaluate("window.print=()=>{window.__pr=(window.__pr||0)+1;};0")

PACK="Angine — enfant (TROD positif)"
SET="""(a)=>{const n=a.n||a;newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:a.ddn||'01/01/2016',poids:a.poids||'15',sexe:'f',date:'18/11/2026'});state.view='';state.sel=PACKS.findIndex(p=>p.n===n);render();
  const p=currentPack();return p?p.s.findIndex(sh=>sh.k==='cons'):-1;}"""
INFO="""()=>{const p=currentPack();const si=p.s.findIndex(sh=>sh.k==='cons');const r=buildPages(p,false);const d=document.createElement('div');d.innerHTML=r.out;
  const pages=[...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.textContent||''}));
  const hd=document.querySelector('[data-sheet="'+si+'"]');const sheet=hd?hd.closest('.sheet'):null;const xc=document.getElementById('xp_cons');
  return {si,off:state.off[si],shoff:shOff(p.s[si],si),hd:hd?hd.checked:null,cls:sheet?sheet.className:'',tp:sheet?sheet.querySelector('.tp').textContent:'',
    heads:pages.map(x=>x.h),cons:pages.filter(x=>x.h.startsWith('Consignes')).map(x=>x.t),n:filSheets(p),ctxCons:docCtx(p).cons,cr:buildCR0(p),
    lines:resolve(p.s[si],si).map(x=>({t:x.t,on:x.on,key:x.key,fs:x.fill.s})),extra:(state.extra[si]||[]).slice(),xp:xc?{checked:xc.checked}:null};}"""
PREVIEW="""()=>[...document.querySelectorAll('#print .page')].map(x=>(x.querySelector('h2')||{}).textContent||'')"""

async def complet(width,label):
    async with async_playwright() as p:
        b=await p.chromium.launch(); mob=width<500
        ctx=await b.new_context(viewport={"width":width,"height":850 if mob else 1000},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
        await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
        page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page,"testcons"+("i" if mob else "o"),False); L=label+" · mode complet : "
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(300)
        ok(L+"la fiche a une feuille Consignes",si>=0,si)
        i=await page.evaluate(INFO)
        ok(L+"feuille Consignes décochée par défaut (en-tête non cochée, classe « shoff », mention « non imprimée — cochez pour l'imprimer »)",i["hd"] is False and i["shoff"] and i["off"] is None and "shoff" in i["cls"] and "non imprimée" in i["tp"] and "cochez pour l'imprimer" in i["tp"],{k:i[k] for k in ("hd","shoff","off","cls","tp")})
        ok(L+"les consignes de la fiche restent cochées à l'intérieur (un seul toucher sur l'en-tête imprime la feuille préparée)",len(i["lines"])>=2 and all(x["on"] for x in i["lines"]),[(x["t"][:30],x["on"]) for x in i["lines"]])
        ok(L+"aucune page Consignes tant que la feuille n'est pas cochée ; l'ordonnance, oui",not i["cons"] and any(h.startswith("Ordonnance") for h in i["heads"]),i["heads"])
        first=i["lines"][0]["fs"][:28]
        ok(L+"non cochée : ni au compte rendu, ni dans le contexte des courriers (aucune consigne « remise » qui ne l'est pas)",i["ctxCons"] is False and first not in i["cr"],[first,i["cr"][-300:]])
        n0=i["n"]
        # aperçu réel (barre du bas) : aucune page Consignes
        await page.click("#fin, #tc_reprint"); await page.wait_for_timeout(1500)
        heads=await page.evaluate(PREVIEW)
        ok(L+"aperçu réel : aucune page Consignes, l'ordonnance est là",heads and not any(h.startswith("Consignes") for h in heads) and any(h.startswith("Ordonnance") for h in heads),heads)
        await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();"); await page.wait_for_timeout(300)
        if mob:
            el=page.locator(f'[data-sheet="{si}"]').first; await el.scroll_into_view_if_needed(); await page.wait_for_timeout(200)
            await page.screenshot(path=os.path.join(OUT,"consignes-decochee-iphone.png"))
        # 1. l'en-tête cochée → page Consignes avec les consignes de la fiche
        await page.click(f'[data-sheet="{si}"]'); await page.wait_for_timeout(400); i=await page.evaluate(INFO)
        ok(L+"en-tête cochée : page Consignes imprimée avec les consignes de la fiche, un document de plus, consignes au compte rendu",i["off"] is False and i["hd"] is True and "shoff" not in i["cls"] and len(i["cons"])==1 and first in i["cons"][0] and i["n"]==n0+1 and i["ctxCons"] is True and first in i["cr"],{k:i[k] for k in ("off","hd","n","ctxCons")}|{"cons":[c[:120] for c in i["cons"]]})
        if mob:
            el=page.locator(f'[data-sheet="{si}"]').first; await el.scroll_into_view_if_needed(); await page.wait_for_timeout(200)
            await page.screenshot(path=os.path.join(OUT,"consignes-cochee-iphone.png"))
        # 2. décochée par le médecin : recocher une consigne ne la rallume pas (son choix est respecté)
        await page.click(f'[data-sheet="{si}"]'); await page.wait_for_timeout(300)
        key=i["lines"][0]["key"]
        await page.click(f'[data-line="{key}"]'); await page.wait_for_timeout(250); await page.click(f'[data-line="{key}"]'); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"décochée par le médecin, puis une consigne décochée / recochée : la feuille reste décochée, rien d'imprimé",i["off"] is True and i["hd"] is False and not i["cons"] and i["lines"][0]["on"],{k:i[k] for k in ("off","hd")}|{"cons":len(i["cons"])})
        # 3. « Nouveau patient » : à nouveau décochée par défaut
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"« Nouveau patient » : la feuille revient décochée par défaut",i["off"] is None and i["hd"] is False and not i["cons"],{k:i[k] for k in ("off","hd")})
        # 4. feuille jamais touchée : recocher une consigne la coche (« si je coche, c'est imprimé »)
        await page.click(f'[data-line="{key}"]'); await page.wait_for_timeout(250); await page.click(f'[data-line="{key}"]'); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"feuille jamais touchée : une consigne cochée coche la feuille, qui s'imprime",i["off"] is False and i["hd"] is True and len(i["cons"])==1 and first in i["cons"][0],{k:i[k] for k in ("off","hd")}|{"cons":len(i["cons"])})
        # 5. « Tout cocher »
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(300)
        await page.click(f'[data-all="{si}"]'); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"« Tout cocher » sur la feuille : cochée et imprimée",i["off"] is False and len(i["cons"])==1,{k:i[k] for k in ("off","hd")})
        # 6. consigne ajoutée (Entrée)
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(300)
        await page.fill(f"#fl_{si}","Reprendre contact avec le médecin traitant dans une semaine pour le contrôle de l'oreille gauche."); await page.press(f"#fl_{si}","Enter"); await page.wait_for_timeout(400); i=await page.evaluate(INFO)
        ok(L+"une consigne ajoutée (Entrée) coche la feuille et s'imprime",i["off"] is False and len(i["extra"])>=1 and len(i["cons"])==1 and i["extra"][-1][:30] in i["cons"][0],{"off":i["off"],"extra":i["extra"][-1:] ,"cons":[c[-200:] for c in i["cons"]]})
        # 7. texte tapé sans Entrée : feuille cochée aussitôt (en-tête mise à jour), texte imprimé
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(300)
        await page.fill(f"#fl_{si}","Garder le carnet de santé à portée de main tout le week-end"); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"un texte tapé sans Entrée coche la feuille aussitôt (en-tête cochée à l'écran) et s'imprime",i["off"] is False and i["hd"] is True and "shoff" not in i["cls"] and len(i["cons"])==1 and "carnet de santé" in i["cons"][0],{k:i[k] for k in ("off","hd","cls")}|{"cons":len(i["cons"])})
        # 8. fiche dont seules les consignes s'imprimeraient : « Imprimer » n'ouvre rien et dit quoi faire
        si=await page.evaluate(SET,{"n":"Pleurs et coliques — nourrisson","ddn":"01/09/2026","poids":"5"}); await page.wait_for_timeout(300)
        await page.evaluate("printPack()"); await page.wait_for_timeout(600)
        tt=await page.evaluate("(document.getElementById('toast')||{}).textContent||''"); heads=await page.evaluate(PREVIEW)
        ok(L+"fiche à consignes seules (pleurs du nourrisson) : rien n'est imprimé et le message invite à cocher la feuille « Consignes au patient »",si>=0 and not heads and "Consignes au patient » est décochée" in tt,[tt,heads])
        await page.click(f'[data-sheet="{si}"]'); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"fiche à consignes seules : en-tête cochée → la page Consignes s'imprime",i["off"] is False and len(i["cons"])==1,{"off":i["off"],"heads":i["heads"]})
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def express(width,label):
    async with async_playwright() as p:
        b=await p.chromium.launch(); mob=width<500
        ctx=await b.new_context(viewport={"width":width,"height":850 if mob else 1000},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
        await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
        page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page,"testconsx"+("i" if mob else "o"),True); L=label+" · Express : "
        si=await page.evaluate(SET,PACK); await page.wait_for_timeout(400); i=await page.evaluate(INFO)
        ok(L+"case « Consignes au patient » présente (favori par défaut), décochée ; aucune page Consignes",i["xp"] is not None and i["xp"]["checked"] is False and not i["cons"] and any(h.startswith("Ordonnance") for h in i["heads"]),{"xp":i["xp"],"heads":i["heads"]})
        await page.check("#xp_cons"); await page.wait_for_timeout(400); i=await page.evaluate(INFO)
        ok(L+"case cochée : page Consignes imprimée avec les consignes de la fiche",i["off"] is False and i["xp"] and i["xp"]["checked"] is True and len(i["cons"])==1 and i["lines"][0]["fs"][:28] in i["cons"][0],{"off":i["off"],"xp":i["xp"],"cons":[c[:100] for c in i["cons"]]})
        if mob: await page.screenshot(path=os.path.join(OUT,"consignes-express-iphone.png"))
        await page.uncheck("#xp_cons"); await page.wait_for_timeout(300); i=await page.evaluate(INFO)
        ok(L+"case décochée : plus de page Consignes",i["off"] is True and not i["cons"],{"off":i["off"],"cons":len(i["cons"])})
        mig=await page.evaluate("""async()=>{FAV.keys=['x:nav','x:call','sec:at','mig:tour18','mig:drive20'];favSave();await new Promise(r=>setTimeout(r,800));await favLoad();const k=(FAV.keys||[]).slice();favReset();return k;}""")  # secSet écrit chiffré 150 ms plus tard : attendre avant de recharger
        ok(L+"favoris déjà enregistrés sans la case : « Consignes au patient » ajoutée une seule fois (mig:cons42f)","x:cons" in mig and "mig:cons42f" in mig,mig)
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    try:
        await complet(375,"iPhone"); await complet(1280,"ordinateur"); await express(375,"iPhone"); await express(1280,"ordinateur")
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
