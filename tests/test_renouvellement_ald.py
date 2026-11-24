# -*- coding: utf-8 -*-
# 24/11/2026 — Renouvellement d'ordonnance, patients en ALD ou non : panneau en tête de la fiche (mode complet), interrupteur
# « Patient en ALD » (toutes les lignes à 100 %, ordonnance bizone), traitement en cours du patient repris en un geste.
# Touches réelles (iPhone 375 × 812 tactile, Express et mode complet) et ordinateur 1280 × 900. Patients fictifs.
# Lancer : python tests/test_renouvellement_ald.py
import asyncio, os, subprocess, time, sys, json
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8848
UA="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
async def create(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
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
OPEN="""(a)=>{newPatient();Object.assign(state,{patient:a.pat,ddn:a.ddn,sexe:'h'});state.cot.lieu='cabinet';state.cot.auto=false;if(a.tt)state.tt=a.tt.slice();state.view='';state.sel=PACKS.findIndex(p=>p.n==="Renouvellement d'ordonnance");render();return currentPack()&&currentPack().n;}"""
PAGES="""()=>{const d=document.createElement('div');d.innerHTML=buildPages(currentPack(),true).out;return [...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText.replace(/\\s+/g,' ')}));}"""
ITEMS="rnwState().items.map(i=>[i.brand,i.dos,i.poso,i.dur,!!i.ald])"
async def run(b,mob,xp,label):
    L=label+" : "
    ctx=await b.new_context(viewport={"width":375 if mob else 1280,"height":812 if mob else 900},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,user_agent=UA if mob else None)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e)))
    await create(page,("rald"+("x" if xp else "c")+("m" if mob else "d")),xp)
    tap=(lambda loc: loc.tap()) if mob else (lambda loc: loc.click())
    # ---- 1. fiche ouverte : panneau présent, en tête en mode complet
    n=await page.evaluate(OPEN,{"pat":"DURAND Jean","ddn":"11/05/1950","tt":["AMLOR 5","LEVOTHYROX 75","metformine","AVK"]}); await page.wait_for_timeout(400)
    await page.wait_for_function("BDPMX.rows!==null||BDPMX.err",timeout=30000); await page.evaluate("render()"); await page.wait_for_timeout(400)
    ok(L+"fiche « Renouvellement d'ordonnance » ouverte, panneau présent",n=="Renouvellement d'ordonnance" and await page.locator("#rnw").count()==1,n)
    pos=await page.evaluate("()=>{const r=document.getElementById('rnw');if(!r)return null;const b=r.getBoundingClientRect();const dict=[...document.querySelectorAll('#main *')].find(e=>/^Dictée/.test((e.textContent||'').trim())&&e.children.length<40);const before=dict?!!(r.compareDocumentPosition(dict)&Node.DOCUMENT_POSITION_FOLLOWING):null;return {top:Math.round(b.top+scrollY),vh:innerHeight,before};}")
    if xp: ok(L+"Express : panneau dans la section Express (comme avant)",pos and pos["top"]<1200,pos)
    else: ok(L+"mode complet : panneau en tête de la fiche, sous le bloc patient et avant la dictée (24/11/2026)",pos and pos["before"] is not False and pos["top"]<(1.3*pos["vh"] if not mob else 1400),pos)
    # ---- 2. traitement en cours du patient → chips
    one=page.locator("#rnw [data-rtt]"); many=page.locator("#rnw [data-rttq]")
    txt1=[t.strip() for t in await one.all_inner_texts()]; txt2=[t.strip() for t in await many.all_inner_texts()]
    ok(L+"traitement en cours : « AMLOR 5 » (une seule présentation) proposé en ajout direct « + AMLOR 5 mg »",any(t.startswith("+ AMLOR 5 mg") for t in txt1),(txt1,txt2))
    ok(L+"traitement en cours : « metformine » (plusieurs présentations) et « AVK » (introuvable) proposés en recherche préremplie, jamais de dosage deviné",any(t.startswith("metformine") for t in txt2) and any(t.startswith("AVK") for t in txt2) and not any("METFORMINE" in t for t in txt1),(txt1,txt2))
    await tap(one.filter(has_text="AMLOR 5 mg").first); await page.wait_for_timeout(500)
    items=await page.evaluate(ITEMS)
    ok(L+"toucher « + AMLOR 5 mg » : ligne ajoutée (amlodipine, AMLOR 5 mg, 1 mois, hors ALD), chip retirée",len(items)==1 and items[0][0]=="AMLOR" and items[0][1]=="5 mg" and items[0][4] is False and not any("AMLOR 5 mg" in t for t in await one.all_inner_texts()),items)
    await tap(page.locator("#rnw [data-rttq]").filter(has_text="metformine").first); await page.wait_for_timeout(600)
    qv=await page.evaluate("document.getElementById('rnw_q')&&document.getElementById('rnw_q').value"); nsg=await page.locator("#rnw_sg .sg[data-cis]").count()
    ok(L+"toucher « metformine … » : recherche préremplie « metformine » et présentations proposées (choix du dosage par le médecin)",qv=="metformine" and nsg>=3,(qv,nsg))
    await page.keyboard.press("Escape"); await page.evaluate("RNW.q='';render()"); await page.wait_for_timeout(300)
    # ---- 3. interrupteur « Patient en ALD »
    sw=page.locator("label.lc:has(#rnw_ald)").first
    await sw.scroll_into_view_if_needed(); await tap(sw); await page.wait_for_timeout(400)
    st=await page.evaluate("[rnwState().ald,"+ITEMS+"]")
    ok(L+"« Patient en ALD » coché : la ligne existante passe à 100 %",st[0] is True and st[1][0][4] is True,st)
    q=page.locator("#rnw_q").first; await q.scroll_into_view_if_needed(); await tap(q); await page.keyboard.type("levothyrox 75"); await page.wait_for_timeout(600)
    sg=page.locator("#rnw_sg .sg[data-cis]"); await tap(sg.first); await page.wait_for_timeout(500)
    items=await page.evaluate(ITEMS)
    ok(L+"ligne ajoutée après le choix ALD : LEVOTHYROX 75 à 100 % d'office",len(items)==2 and items[1][0]=="LEVOTHYROX" and items[1][4] is True,items)
    foot=await page.locator("#rnw .rnw-foot").inner_text()
    ok(L+"pied du panneau : « 2 lignes · ordonnance bizone (2 ALD) »","2 lignes" in foot and "bizone (2 ALD)" in foot,foot)
    for i,chip in [(0,"1 gélule le matin"),(1,"1 comprimé le matin")]:
        c=page.locator(f'[data-rpos="{i}"]',has_text=chip).first; await c.scroll_into_view_if_needed(); await tap(c); await page.wait_for_timeout(300)
    pr=await page.evaluate(PAGES); o=" ".join(p["t"] for p in pr if p["h"].startswith("Ordonnance"))
    ok(L+"ordonnance bizone : les 2 lignes dans la partie « affection exonérante », partie basse « Néant. »","affection exonérante" in o and "maladies intercurrentes" in o and o.index("AMLOR")<o.index("maladies intercurrentes") and o.index("LEVOTHYROX")<o.index("maladies intercurrentes") and "Néant." in o,o[:500])
    # une ligne décochée va dans la partie basse, l'interrupteur reste coché
    lab=page.locator('label.lc:has([data-rald="1"])').first; await lab.scroll_into_view_if_needed(); await tap(lab); await page.wait_for_timeout(400)
    st=await page.evaluate("[rnwState().ald,"+ITEMS+"]"); pr=await page.evaluate(PAGES); o=" ".join(p["t"] for p in pr if p["h"].startswith("Ordonnance"))
    ok(L+"ligne LEVOTHYROX décochée : partie « maladies intercurrentes », AMLOR reste en haut, interrupteur toujours coché",st[0] is True and st[1][1][4] is False and o.index("AMLOR")<o.index("maladies intercurrentes")<o.index("LEVOTHYROX") and "Néant." not in o,(st,o[:400]))
    # interrupteur décoché : ordonnance simple
    await sw.scroll_into_view_if_needed(); await tap(sw); await page.wait_for_timeout(400)
    st=await page.evaluate("[rnwState().ald,"+ITEMS+"]"); pr=await page.evaluate(PAGES); o=" ".join(p["t"] for p in pr if p["h"].startswith("Ordonnance"))
    ok(L+"« Patient en ALD » décoché : plus aucune ligne à 100 %, ordonnance simple (sans bizone)",st[0] is False and not any(x[4] for x in st[1]) and "affection exonérante" not in o and "AMLOR" in o and "LEVOTHYROX" in o,(st,o[:300]))
    ok(L+"rien n'attend avant l'impression (posologies renseignées, une page)",not await page.evaluate("xpPending(currentPack())"),await page.evaluate("xpPending(currentPack())"))
    # ---- 4. nouveau patient : panneau remis à zéro (lignes, interrupteur)
    await page.evaluate("()=>{rnwState().ald=true;newPatient();}"); await page.wait_for_timeout(200)
    z=await page.evaluate("[rnwState().items.length,rnwState().ald]")
    ok(L+"« Nouveau patient » : liste vide et interrupteur ALD remis à zéro",z==[0,False],z)
    # ---- 5. sans traitement en cours ni ALD : panneau inchangé (pas de chips), ligne ajoutée hors ALD
    await page.evaluate(OPEN,{"pat":"MARTIN Paul","ddn":"02/02/1980","tt":[]}); await page.wait_for_timeout(400)
    ok(L+"sans traitement en cours : pas de rangée « Traitement en cours »",await page.locator("#rnw .rnw-tt").count()==0)
    q=page.locator("#rnw_q").first; await q.scroll_into_view_if_needed(); await tap(q); await page.keyboard.type("kardegic 75"); await page.wait_for_timeout(600); await tap(page.locator("#rnw_sg .sg[data-cis]").first); await page.wait_for_timeout(500)
    items=await page.evaluate(ITEMS)
    ok(L+"patient non ALD : ligne ajoutée hors ALD, ordonnance simple",len(items)==1 and items[0][4] is False and "affection exonérante" not in " ".join(p["t"] for p in await page.evaluate(PAGES)),items)
    ok(L+"aucune erreur JS",not errs,errs[:2])
    await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (mob,xp,label) in [(False,False,"ordinateur · mode complet"),(True,False,"iPhone · mode complet"),(True,True,"iPhone · Express")]:
                await run(b,mob,xp,label)
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_renouvellement_ald.md"),"w",encoding="utf-8").write("# Renouvellement d'ordonnance — patients en ALD ou non (24/11/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}"+("" if r[1] else f" — {str(r[2])[:300]}") for r in results)+"\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
