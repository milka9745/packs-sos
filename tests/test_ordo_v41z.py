# -*- coding: utf-8 -*-
# Ordonnance modifiable d'un geste (06/11/2026) : « + Ajouter un médicament » sous les lignes (Express et mode complet), propositions
# (mes ajouts fréquents, ma posologie habituelle, fiches, base RCP), contrôles immédiats (doublon, allergie, interactions), retrait d'un
# toucher, appui long (retirer pour ce patient / par défaut pour moi, ajouter à mon pack par défaut, modifier le texte), impression sur la
# même ordonnance, compte rendu et journal. Pack gastro adulte + antiémétique. iPhone 375 px (Visite et Consultation) et ordinateur.
# Patients fictifs. Lancer : python tests/test_ordo_v41z.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
PORT="8875"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
src=open(os.path.join(ROOT,"tests","test_packs.py"),encoding="utf-8").read()
ns={"__file__":os.path.join(ROOT,"tests","test_packs.py")}; exec(src.split("async def run(")[0].replace("8765",PORT),ns)
unlock=ns["unlock"]
PACK="Gastro-entérite — adulte"
SET="""(lieu)=>{newPatient();Object.assign(state,{patient:'ESSAI Gastro',ddn:'10/05/1985',sexe:'h'});state.cot=state.cot||cotDefault();state.cot.lieu=lieu;state.cot.auto=false;state.xpManual=true;state.sel=PACKS.findIndex(p=>p.n===%r);render();}"""%PACK
PAGES="""()=>{const r=buildPages(currentPack(),true);const d=document.createElement('div');d.innerHTML=r.out;const pages=[...d.querySelectorAll('.page')];const ordo=pages.filter(p=>/TIORFAN/.test(p.textContent));return {n:pages.length,nOrdo:ordo.length,h2:pages.map(p=>(p.querySelector('h2')||{}).textContent||''),li:ordo.length?[...ordo[0].querySelectorAll('li')].map(x=>x.textContent.trim()):[],txt:ordo.length?ordo[0].textContent.replace(/\\s+/g,' '):''};}"""
LINES="""()=>[...document.querySelectorAll('.xp-ordo [data-xk]')].filter(e=>!e.closest('details.xp-opts')).map(e=>({t:e.textContent.trim().slice(0,220),off:e.classList.contains('off'),dup:e.classList.contains('dup'),k:e.dataset.xk,h:e.getBoundingClientRect().height,chips:[...e.querySelectorAll('.pcd')].map(c=>c.textContent)}))"""
OPTS="""()=>{const d=document.querySelector('.xp-ordo details.xp-opts');return d?{n:d.querySelectorAll('[data-xk]').length,open:d.open,sum:d.querySelector('summary').textContent.trim()}:null;}"""
async def long_press(page,loc):
    await loc.evaluate("e=>e.scrollIntoView({block:'center'})"); await page.wait_for_timeout(250)
    b=await loc.bounding_box(); x=b["x"]+min(40,b["width"]/3); y=b["y"]+min(b["height"]/2,20)
    await page.mouse.move(x,y); await page.mouse.down(); await page.wait_for_timeout(750); await page.mouse.up(); await page.wait_for_timeout(250)
async def menu_click(page,label):
    b=page.locator("#ordomenu button",has_text=label).first
    present=await b.count()>0
    if present: await b.click(); await page.wait_for_timeout(350)
    return present
async def run_express(b,lieu,label,shots=False):
    L=label+" : "; tag=label.replace(" ","-")
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await page.add_init_script("try{localStorage.setItem('sos_xp','true');localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_design','garde');}catch(e){}")
    await unlock(page); await page.evaluate("()=>{if(!ORDO.loaded)ORDO.loaded=true;ORDO.pmod={};ORDO.learn={};ORDO.poso={};}")
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    ls=await page.evaluate(LINES); op=await page.evaluate(OPTS)
    ok(L+"Express : les lignes cochées de l'ordonnance affichées (hauteur de toucher ≥ 36 px), options décochées du pack sous un volet fermé",len(ls)>=5 and all(not x["off"] for x in ls) and all(x["h"]>=34 for x in ls) and op and op["n"]>=1 and not op["open"] and op["sum"].startswith("Options du pack"),([(x["t"][:25],x["off"],round(x["h"])) for x in ls],op))
    await page.locator(".xp-ordo details.xp-opts summary").click(); await page.wait_for_timeout(300)
    opt=page.locator(".xp-ordo details.xp-opts [data-xk]").first; optt=await opt.text_content(); await opt.click(); await page.wait_for_timeout(300)
    ls=await page.evaluate(LINES)
    ok(L+"un toucher sur une option du pack la coche (elle rejoint la liste)",any(x["t"][:30]==optt.strip()[:30] and not x["off"] for x in ls),(optt[:40],[x["t"][:25] for x in ls]))
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    inp=page.locator("#xp_add")
    ok(L+"champ « + Ajouter un médicament » toujours visible sous les lignes (≥ 44 px)",await inp.is_visible() and (await inp.bounding_box())["height"]>=44 and (await inp.get_attribute("placeholder")).startswith("+ Ajouter un médicament"),await inp.get_attribute("placeholder"))
    sw=await page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
    ok(L+"aucun débordement horizontal à 375 px",sw[0]<=sw[1],sw)
    # retirer d'un toucher
    doli=page.locator(".xp-ordo [data-xk]",has_text="DOLIPRANE").first
    await doli.click(); await page.wait_for_timeout(300)
    ls=await page.evaluate(LINES); d=[x for x in ls if "DOLIPRANE" in x["t"]]
    pg=await page.evaluate(PAGES)
    ok(L+"un toucher sur DOLIPRANE : ligne barrée, retirée de l'ordonnance imprimée",d and d[0]["off"] and not any("DOLIPRANE" in l for l in pg["li"]),(d,pg["li"][:6]))
    # ajout d'un antiémétique : VOGALÈNE retiré d'un toucher (sinon deux antiémétiques → interaction signalée), 4 lettres, proposition, choix
    await page.locator(".xp-ordo [data-xk]",has_text="VOGALÈNE LYOC").first.click(); await page.wait_for_timeout(300)
    await inp.click(); await inp.type("prim",delay=30); await page.wait_for_timeout(350)
    sg=await page.evaluate("[...document.querySelectorAll('#xp_sg .sg')].map(b=>({n:(b.querySelector('b')||{}).textContent||'',tag:(b.querySelector('.otag')||{}).textContent||'',t:(b.querySelector('small')||{}).textContent||''}))")
    ok(L+"« prim » : PRIMPÉRAN proposé (début d'un mot du nom : pas « comprimé » ni « triméthoprime ») avec la posologie adulte du RCP (10 mg, 3 fois par jour, 5 jours)",sg and all(x["n"].upper().startswith("PRIM") for x in sg) and any("10 mg" in x["t"] and "5 jours" in x["t"] for x in sg),sg[:4])
    await page.locator("#xp_sg .sg",has_text="5 jours au maximum").first.dispatch_event("mousedown"); await page.wait_for_timeout(500)
    ls=await page.evaluate(LINES); pr=[x for x in ls if "PRIMP" in x["t"]]
    msg=await page.evaluate("(document.querySelector('.xp-ordomsg')||{}).textContent||''")
    ok(L+"PRIMPÉRAN ajouté : ligne cochée en fin de liste, bouton ×, message « Ajouté », champ vidé",pr and not pr[0]["off"] and ls[-1] is pr[0] and msg.startswith("✓ Ajouté") and await page.evaluate("document.getElementById('xp_add').value")=="",(pr,msg))
    pg=await page.evaluate(PAGES)
    ok(L+"impression : la ligne ajoutée est sur la même ordonnance, au même format, après les lignes du pack, une page",pg["nOrdo"]==1 and pg["li"] and pg["li"][-1].startswith("PRIMPÉRAN 10 mg") and "DOLIPRANE" not in pg["txt"] and "VOGALÈNE" not in pg["txt"],(pg["nOrdo"],pg["h2"],pg["li"][-3:]))
    # texte libre avec note médecin : affichée à l'écran, jamais imprimée
    await inp.click(); await inp.fill("ESSAIMED 10 mg comprimé : 1 comprimé matin et soir (si douleur) pendant 3 jours"); await page.keyboard.press("Enter"); await page.wait_for_timeout(500)
    pg=await page.evaluate(PAGES); scr=await page.evaluate("[...document.querySelectorAll('.xp-ordo [data-xk]')].map(e=>e.textContent).join(' ')")
    ok(L+"ligne libre avec note médecin : ajoutée, imprimée sans la parenthèse, une page",pg["nOrdo"]==1 and any(l.startswith("ESSAIMED") and "(" not in l and "pendant 3 jours" in l for l in pg["li"]) and "ESSAIMED" in scr,[l for l in pg["li"] if "ESSAIMED" in l])
    await page.locator(".xp-ordo [data-xk]",has_text="VOGALÈNE LYOC").first.click(); await page.wait_for_timeout(300)
    # doublon : VOGALÈNE déjà coché (groupe)
    await inp.click(); await inp.type("vog",delay=30); await page.wait_for_timeout(350)
    await page.locator("#xp_sg .sg",has_text="VOGAL").first.dispatch_event("mousedown"); await page.wait_for_timeout(500)
    ls=await page.evaluate(LINES); vg=[x for x in ls if "VOGAL" in x["t"]]; msg=await page.evaluate("(document.querySelector('.xp-ordomsg')||{}).textContent||''")
    ok(L+"doublon (VOGALÈNE déjà coché) : avertissement immédiat, ligne ajoutée visible mais décochée, pastille « doublon »",("doublon" in msg) and any(x["dup"] and x["off"] and "doublon" in x["chips"] for x in vg),(msg,vg))
    await page.evaluate("()=>{const si=currentPack().s.findIndex(s=>s.k==='med');state.extra[si]=state.extra[si].filter(t=>!/^VOGAL/.test(t));render();}"); await page.wait_for_timeout(300)
    # compte rendu et journal
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"compte rendu : PRIMPÉRAN prescrit, « ORDONNANCE ADAPTÉE » (+ PRIMPÉRAN, − DOLIPRANE retiré pour ce patient)","PRIMPÉRAN" in cr and "ORDONNANCE ADAPTÉE" in cr and re.search(r"- \+ PRIMPÉRAN.*\(ajouté\)",cr) and "− DOLIPRANE (retiré pour ce patient)" in cr,[l for l in cr.split("\n") if "ORDONNANCE" in l or "PRIMP" in l or "DOLIPRANE" in l][:5])
    await page.evaluate("journalUpsert(currentPack())"); await page.wait_for_timeout(200)
    notes=await page.evaluate("(JOURNAL[JOURNAL.length-1]||{}).notes||[]")
    ok(L+"journal : « Ordonnance : + PRIMPÉRAN … (ajouté) » et « − DOLIPRANE (retiré pour ce patient) »",any(n.startswith("Ordonnance : + PRIMPÉRAN") for n in notes) and any(n=="Ordonnance : − DOLIPRANE (retiré pour ce patient)" for n in notes),notes)
    # appui long sur la ligne ajoutée : modifier le texte en une ligne
    prl=page.locator(".xp-ordo [data-xk]",has_text="PRIMP").first
    await long_press(page,prl)
    menu=await page.evaluate("[...document.querySelectorAll('#ordomenu button')].map(b=>b.textContent.trim())")
    ok(L+"appui long sur la ligne ajoutée : menu Retirer / Ajouter à mon pack par défaut / Supprimer / Modifier",any("Retirer pour ce patient" in m for m in menu) and any("Ajouter à mon pack par défaut" in m for m in menu) and any("Supprimer" in m for m in menu) and any("Modifier le texte" in m for m in menu),menu)
    await menu_click(page,"Modifier le texte")
    ed=page.locator(".oedit")
    ok(L+"« Modifier le texte » : saisie en une ligne, préremplie",await ed.count()==1 and "PRIMPÉRAN 10 mg" in (await ed.input_value()))
    v=await ed.input_value(); await ed.fill(v.replace("5 jours au maximum","3 jours au maximum")); await page.keyboard.press("Enter"); await page.wait_for_timeout(400)
    pg=await page.evaluate(PAGES)
    ok(L+"dose / rythme / durée modifiés : la ligne imprimée suit (3 jours)",any(l.startswith("PRIMPÉRAN") and "3 jours au maximum" in l for l in pg["li"]),[l for l in pg["li"] if "PRIMP" in l])
    # apprentissage : deux impressions → « Souvent ici », posologie habituelle proposée en premier
    await page.evaluate("()=>{ordoLearn(currentPack());ordoLearn(currentPack());}"); await page.wait_for_timeout(300)
    lrn=await page.evaluate("()=>({n:((ORDO.learn[%r]||{})['PRIMPÉRAN']||{}).n,poso:(ORDO.poso['primperan']||ORDO.poso[Object.keys(ORDO.poso).find(k=>/primp/.test(k))]||{}).t})"%PACK)
    ok(L+"appris sur l'appareil : PRIMPÉRAN compté 2 fois dans ce pack, posologie habituelle = ma ligne modifiée (3 jours)",lrn["n"]==2 and lrn["poso"] and "3 jours au maximum" in lrn["poso"],lrn)
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    chip=page.locator(".xp-ordo .xp-freq .chip",has_text="PRIMP")
    ok(L+"nouveau patient, même pack : « Souvent ici : + PRIMPÉRAN » proposé en premier",await chip.count()==1)
    await chip.click(); await page.wait_for_timeout(400)
    ls=await page.evaluate(LINES); pr=[x for x in ls if "PRIMP" in x["t"]]
    ok(L+"un geste sur la puce : PRIMPÉRAN ajouté avec ma posologie habituelle (3 jours)",pr and not pr[0]["off"] and "3 jours" in pr[0]["t"],pr)
    await inp.click(); await inp.type("prim",delay=30); await page.wait_for_timeout(350)
    sg=await page.evaluate("[...document.querySelectorAll('#xp_sg .sg')].map(b=>((b.querySelector('b')||{}).textContent||'')+' · '+((b.querySelector('.otag')||{}).textContent||''))")
    ok(L+"« prim » : ma posologie habituelle (« souvent ici » / « habituel ») avant la ligne du RCP",sg and ("souvent ici" in sg[0] or "habituel" in sg[0]) and any(("fiche" in x or "RCP" in x) for x in sg),sg)
    await page.keyboard.press("Escape"); await inp.fill(""); await page.wait_for_timeout(200)
    # « Ajouter à mon pack par défaut » puis « Ne plus ajouter »
    prl=page.locator(".xp-ordo [data-xk]",has_text="PRIMP").first; await long_press(page,prl); await menu_click(page,"Ajouter à mon pack par défaut")
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    ls=await page.evaluate(LINES); pr=[x for x in ls if "PRIMP" in x["t"]]; pg=await page.evaluate(PAGES)
    ok(L+"« Ajouter à mon pack par défaut » : nouveau patient → PRIMPÉRAN présent d'office (pastille « mon ajout »), imprimé",pr and not pr[0]["off"] and "mon ajout" in pr[0]["chips"] and any(l.startswith("PRIMPÉRAN") for l in pg["li"]),(pr,pg["li"][-2:]))
    enc=await page.evaluate("()=>{const ks=Object.keys(localStorage);return {enc:ks.some(k=>/^sos_ordo_.*_enc$/.test(k)),clair:ks.some(k=>/^sos_ordo_/.test(k)&&!/_enc$/.test(k)),fuite:Object.values(localStorage).some(v=>/PRIMP|DOLIPRANE/i.test(v))};}")
    ok(L+"mémoire du profil chiffrée (sos_ordo_…_enc), rien en clair",enc["enc"] and not enc["clair"] and not enc["fuite"],enc)
    prl=page.locator(".xp-ordo [data-xk]",has_text="PRIMP").first; await long_press(page,prl); had=await menu_click(page,"Ne plus ajouter par défaut")
    ls=await page.evaluate(LINES)
    ok(L+"« Ne plus ajouter par défaut » : la ligne disparaît",had and not any("PRIMP" in x["t"] for x in ls),[x["t"][:20] for x in ls])
    # retirer par défaut (DOLIPRANE) puis rétablir
    doli=page.locator(".xp-ordo [data-xk]",has_text="DOLIPRANE").first; await long_press(page,doli); had=await menu_click(page,"Retirer par défaut de ce pack pour moi")
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    ls=await page.evaluate(LINES); d=[x for x in ls if "DOLIPRANE" in x["t"]]; pg=await page.evaluate(PAGES)
    ok(L+"« Retirer par défaut de ce pack pour moi » : nouveau patient → DOLIPRANE décoché d'office (pastille), absent de l'ordonnance, visible pour le remettre",had and d and d[0]["off"] and "retiré par défaut" in d[0]["chips"] and not any("DOLIPRANE" in l for l in pg["li"]),(d,pg["li"][:3]))
    await page.wait_for_timeout(600); rl=await page.evaluate("async()=>{ORDO.pmod={};ORDO.learn={};ORDO.poso={};ORDO.loaded=false;await ordoLoad();return {loaded:ORDO.loaded,rm:((ORDO.pmod[%r]||{}).rm||[]).length};}"%PACK)
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400)
    ls=await page.evaluate(LINES); d=[x for x in ls if "DOLIPRANE" in x["t"]]
    ok(L+"mémoire vidée puis relue depuis le stockage chiffré : le retrait par défaut est retrouvé",rl["loaded"] and rl["rm"]==1 and d and d[0]["off"] and "retiré par défaut" in d[0]["chips"],(rl,d))
    await doli.click(); await page.wait_for_timeout(300); ls=await page.evaluate(LINES); d=[x for x in ls if "DOLIPRANE" in x["t"]]
    ok(L+"un toucher remet DOLIPRANE pour ce patient",d and not d[0]["off"])
    doli=page.locator(".xp-ordo [data-xk]",has_text="DOLIPRANE").first; await long_press(page,doli); had=await menu_click(page,"Rétablir par défaut")
    await page.evaluate(SET,lieu); await page.wait_for_timeout(400); ls=await page.evaluate(LINES); d=[x for x in ls if "DOLIPRANE" in x["t"]]
    ok(L+"« Rétablir par défaut » : DOLIPRANE coché d'office de nouveau",had and d and not d[0]["off"],d)
    # allergie et interaction : contrôle immédiat
    await page.evaluate("()=>{state.allergie=true;state.allergies=['Pénicillines'];render();}"); await page.wait_for_timeout(300)
    await inp.click(); await inp.type("augm",delay=30); await page.wait_for_timeout(350)
    await page.locator("#xp_sg .sg",has_text="AUGMENTIN").first.dispatch_event("mousedown"); await page.wait_for_timeout(500)
    ls=await page.evaluate(LINES); au=[x for x in ls if "AUGMENTIN" in x["t"]]; msg=await page.evaluate("(document.querySelector('.xp-ordomsg')||{}).textContent||''")
    ok(L+"allergie aux pénicillines : AUGMENTIN ajouté → avertissement immédiat « allergie », ligne décochée",au and au[0]["off"] and "allergie" in msg.lower(),(au,msg))
    await page.evaluate("()=>{state.allergie=false;state.allergies=[];state.tt=['fluindione (PREVISCAN)'];const si=currentPack().s.findIndex(s=>s.k==='med');state.extra[si]=[];render();}"); await page.wait_for_timeout(300)
    await inp.click(); await inp.type("ibup",delay=30); await page.wait_for_timeout(350)
    await page.locator("#xp_sg .sg",has_text="IBUPROF").first.dispatch_event("mousedown"); await page.wait_for_timeout(600)
    msg=await page.evaluate("(document.querySelector('.xp-ordomsg')||{}).textContent||''"); al=await page.evaluate("[...document.querySelectorAll('.xp-alerts .xp-al')].map(e=>e.textContent)")
    ok(L+"interaction (AVK en cours + ibuprofène) : avertissement immédiat sous le champ et dans les alertes",re.search(r"⚠|⛔",msg) and re.search(r"fluindione|PREVISCAN|anticoag",msg,re.I) and any(re.search(r"fluindione|PREVISCAN",a,re.I) and re.search(r"ibuprof",a,re.I) for a in al),(msg[:160],al[:3]))
    if shots:
        await page.evaluate(SET,lieu); await page.wait_for_timeout(300); await inp.click(); await inp.type("prim",delay=30); await page.wait_for_timeout(400)
        await page.evaluate("document.querySelector('.xp-ordo').scrollIntoView({block:'start'})"); await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT,f"ordo-{tag}-propositions.png"))
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def run_full(b,w,h,label):
    L=label+" : "; mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await page.add_init_script("try{localStorage.setItem('sos_xp','false');localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_design','garde');}catch(e){}")
    await unlock(page); await page.evaluate("()=>{if(!ORDO.loaded)ORDO.loaded=true;ORDO.pmod={};ORDO.learn={};ORDO.poso={};}")
    await page.evaluate(SET,"consultation"); await page.wait_for_timeout(400)
    si=await page.evaluate("currentPack().s.findIndex(s=>s.k==='med')")
    inp=page.locator(f"#fl_{si}")
    ok(L+"mode complet : champ « + Ajouter un médicament » sous les lignes de l'ordonnance",await inp.is_visible() and (await inp.get_attribute("placeholder")).startswith("+ Ajouter un médicament"))
    cb=page.locator(".lines li",has_text="DOLIPRANE").first.locator("input[type=checkbox]"); await cb.uncheck(); await page.wait_for_timeout(300)
    pg=await page.evaluate(PAGES)
    ok(L+"décocher DOLIPRANE : retiré de l'ordonnance",not any("DOLIPRANE" in l for l in pg["li"]),pg["li"][:6])
    await inp.click(); await inp.type("prim",delay=30); await page.wait_for_timeout(350)
    sg=await page.evaluate(f"[...document.querySelectorAll('#sg_{si} .sg')].map(b=>((b.querySelector('b')||{{}}).textContent||'')+' · '+((b.querySelector('.otag')||{{}}).textContent||''))")
    ok(L+"« prim » : PRIMPÉRAN proposé (fiche ou RCP), rien d'autre",sg and all(x.upper().startswith("PRIM") for x in sg) and any("PRIMP" in x and ("fiche" in x or "RCP" in x) for x in sg),sg[:4])
    await page.locator(f"#sg_{si} .sg",has_text="PRIMP").first.dispatch_event("mousedown"); await page.wait_for_timeout(500)
    li=page.locator(".lines li",has_text="PRIMPÉRAN").first
    ok(L+"PRIMPÉRAN ajouté : ligne cochée avec ×, ✎",await li.count()==1 and await li.locator("input[type=checkbox]").is_checked() and await li.locator(".del").count()==1 and await li.locator(".edl").count()==1)
    pg=await page.evaluate(PAGES)
    ok(L+"impression : ligne ajoutée sur la même ordonnance, après les lignes du pack, une page",pg["nOrdo"]==1 and pg["li"] and pg["li"][-1].startswith("PRIMPÉRAN 10 mg") and "DOLIPRANE" not in pg["txt"],pg["li"])
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"compte rendu : ORDONNANCE ADAPTÉE (+ PRIMPÉRAN, − DOLIPRANE)","ORDONNANCE ADAPTÉE" in cr and "+ PRIMPÉRAN" in cr and "− DOLIPRANE (retiré pour ce patient)" in cr)
    # appui long (souris : clic droit ou appui) sur la ligne du pack
    doli=page.locator(".lines li",has_text="DOLIPRANE").first
    if mob: await long_press(page,doli)
    else: await doli.locator(".lt").click(button="right"); await page.wait_for_timeout(300)
    menu=await page.evaluate("[...document.querySelectorAll('#ordomenu button')].map(b=>b.textContent.trim())")
    ok(L+("appui long" if mob else "clic droit")+" sur une ligne du pack : menu Remettre / Retirer par défaut / Modifier",any("Remettre pour ce patient" in m for m in menu) and any("Retirer par défaut de ce pack pour moi" in m for m in menu) and any("Modifier le texte" in m for m in menu),menu)
    await menu_click(page,"Retirer par défaut de ce pack pour moi")
    await page.evaluate(SET,"consultation"); await page.wait_for_timeout(400)
    st=await page.evaluate("()=>{const li=[...document.querySelectorAll('.lines li')].find(l=>/DOLIPRANE/.test(l.textContent));return li?{off:li.classList.contains('off'),chk:li.querySelector('input').checked,chip:[...li.querySelectorAll('.pcd')].map(c=>c.textContent)}:null;}")
    ok(L+"« Retirer par défaut » : nouveau patient → DOLIPRANE décoché d'office, pastille « retiré par défaut »",st and not st["chk"] and "retiré par défaut" in st["chip"],st)
    if not mob:
        # impression réelle (aperçu) → apprentissage de l'ajout
        await inp.click(); await inp.type("prim",delay=30); await page.wait_for_timeout(350); await page.locator(f"#sg_{si} .sg",has_text="PRIMP").first.dispatch_event("mousedown"); await page.wait_for_timeout(400)
        await page.evaluate("()=>{window.print=()=>{};window.pdfPrintFile=()=>{};}"); await page.evaluate("printPack()")
        try: await page.wait_for_selector("#print .page",timeout=15000)
        except Exception: pass
        if await page.locator("#ciover").count():
            await page.click("#ci_keep"); await page.click("#ciover [data-cichip]"); await page.click("#ci_print")
            try: await page.wait_for_selector("#print .page",timeout=15000)
            except Exception: pass
        lrn=await page.evaluate("()=>((ORDO.learn[%r]||{})['PRIMPÉRAN']||{}).n||0"%PACK)
        ok(L+"« Imprimer » (aperçu) : l'ajout est appris pour ce pack",lrn==1,lrn)
        bk=page.locator("#pb_back");
        if await bk.count(): await bk.click(); await page.wait_for_timeout(300)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await run_express(b,"visite","iPhone Express Visite",shots=True)
            await run_express(b,"consultation","iPhone Express Consultation")
            await run_full(b,375,812,"iPhone complet")
            await run_full(b,1280,900,"ordinateur complet")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_ordo_v41z.md"),"w",encoding="utf-8").write("# Ordonnance modifiable d'un geste (06/11/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
