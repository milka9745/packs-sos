# -*- coding: utf-8 -*-
# Tests du 11/11/2026 — tâche 1 (antibiotiques : un seul par ordonnance, durée selon l'âge et le diagnostic, pastilles de durée et de dose
# tracées, libellés allégés, DCI avant la marque) et tâche 2 (fiche « Renouvellement d'ordonnance » : base BDPM hors ligne, bizone ALD,
# stupéfiants, deux ordonnances au-delà d'une page). iPhone 375 × 812 tactile (Express et mode complet, jour et nuit, grand texte) et ordinateur 1280 × 900.
# Patients fictifs. Lancer : python tests/test_atb_renouvellement.py
import asyncio, os, subprocess, time, sys, re, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
PORT=8797
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
def months_ago(n):
    t=datetime.date.today(); y,m=t.year,t.month-n
    while m<=0: y-=1; m+=12
    d=min(t.day,28); return f"{d:02d}/{m:02d}/{y}"
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
SET="""(a)=>{newPatient();Object.assign(state,{patient:a.pat||'PETIT Lou',ddn:a.ddn||'',poids:a.poids||'',sexe:a.sexe||'f'});state.cot.lieu=a.lieu||'cabinet';state.cot.auto=false;state.view='';state.sel=PACKS.findIndex(p=>p.n===a.n);render();return state.sel;}"""
MEDS="""()=>{const p=currentPack();const out=[];p.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>out.push({si,key:x.key,t:String(x.t).slice(0,60),s:x.fill.s,on:!!x.on,miss:x.fill.miss,adv:x.fill.adv||[],grp:x.grp||'',atb:x.fill.atb||'',jr:!!x.jr}));});return out;}"""
PRINT="""()=>{const p=currentPack();const r=buildPages(p,true);const d=document.createElement('div');d.innerHTML=r.out;const pages=[...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}));return {pages,removed:r.removed,ordo:pages.filter(x=>x.h.startsWith('Ordonnance')).map(x=>x.t).join(' || ')};}"""
ATBS=["CLAMOXYL","AUGMENTIN","ORELOX","BACTRIM","ZINNAT","ZECLAR","ZITHROMAX","amoxicilline","cefpodoxime","cotrimoxazole","céfuroxime","clarithromycine","azithromycine"]
def natb(txt): return sum(1 for a in ATBS if a in txt)
async def shot(page,name,sel=None):
    try:
        if sel: await page.evaluate("(s)=>{const e=document.querySelector(s);if(e)e.scrollIntoView({block:'center'});}",sel); await page.wait_for_timeout(250)
        await page.screenshot(path=os.path.join(OUT,name))
    except Exception as e: print("capture",name,e)
async def run(b,w,h,xp,th,big,label):
    mob=w<500; tag=label.replace(" ","-"); L=label+" : "
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,("atb"+tag)[:12],xp)
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');try{{THEME.mode='{th}';themeApply();}}catch(e){{}}document.documentElement.setAttribute('data-theme','{th}');if({'true' if big else 'false'})document.documentElement.setAttribute('data-size','big');else document.documentElement.removeAttribute('data-size');")
    # ---------- Cas 1 : OMA, 15 mois, 8 kg ----------
    await page.evaluate(SET,{"ddn":months_ago(15),"poids":"8","n":"Otite moyenne aiguë — enfant"}); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA 15 mois 8 kg : un seul antibiotique coché (CLAMOXYL recommandé), alternatives dessous",len(on)==1 and on[0]["t"].startswith("CLAMOXYL") and len([m for m in M if m["atb"]])>=3,[(m["t"][:20],m["on"]) for m in M if m["atb"]])
    s=on[0]["s"] if on else ""
    ok(L+"OMA : libellé allégé à l'écran « 3,5 ml matin et soir pendant 10 jours » (ni « soit … mg », ni « sans dépasser », ni « seringue »)","3,5 ml matin et soir pendant 10 jours" in s and "(soit" not in s and "sans dépasser" not in s and "seringue" not in s,s[:200])
    ok(L+"OMA : mg par prise et mg/kg/j à l'écran seulement (note)",any("350 mg" in a and "mg/kg/j" in a for a in (on[0]["adv"] if on else [])),on and on[0]["adv"])
    pr=await page.evaluate(PRINT)
    ok(L+"OMA, ordonnance : « amoxicilline (CLAMOXYL) 500 mg/5 ml poudre pour suspension buvable : 3,5 ml matin et soir pendant 10 jours. »","amoxicilline (CLAMOXYL) 500 mg/5 ml poudre pour suspension buvable : 3,5 ml matin et soir pendant 10 jours." in pr["ordo"],pr["ordo"][:300])
    ok(L+"OMA, ordonnance : un seul antibiotique imprimé, rien de retiré",natb(pr["ordo"])==2 and not pr["removed"],(natb(pr["ordo"]),pr["removed"]))
    # bascule vers AUGMENTIN (geste), puis durée 7 jours (pastille), puis dose
    aug=[m for m in M if m["t"].startswith("AUGMENTIN")][0]
    if xp and mob:
        await page.locator(f'.xp-ordo [data-xk="{aug["si"]}|{aug["key"]}"]').first.click()
    else:
        await page.locator(f'input[data-grp][data-key="{aug["key"]}"]').first.click()
    await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : toucher AUGMENTIN remplace CLAMOXYL (un seul antibiotique)",len(on)==1 and on[0]["t"].startswith("AUGMENTIN"),[(m["t"][:20],m["on"]) for m in M if m["atb"]])
    ok(L+"OMA : AUGMENTIN « 1 dose-poids 8 kg 3 fois par jour au début des repas pendant 10 jours »",on and "1 dose-poids 8 kg 3 fois par jour au début des repas pendant 10 jours" in on[0]["s"],on and on[0]["s"][:200])
    pr=await page.evaluate(PRINT)
    ok(L+"OMA, ordonnance : « amoxicilline-acide clavulanique (AUGMENTIN) ENFANTS … : 1 dose-poids 8 kg 3 fois par jour … pendant 10 jours. »","amoxicilline-acide clavulanique (AUGMENTIN) ENFANTS 100 mg/12,5 mg par ml poudre pour suspension buvable : 1 dose-poids 8 kg 3 fois par jour au début des repas pendant 10 jours." in pr["ordo"],pr["ordo"][:300])
    n=await page.locator(".atbctl").count()
    ok(L+"OMA : pastilles de durée (3 · 5 · 6 · 7 · 8 · 10 · 14 j) sous l'antibiotique coché",n>=1 and await page.locator('.atbctl [data-atbdur][data-n="7"]').count()>=1 and await page.locator('.atbctl [data-atbdur][data-n="14"]').count()>=1,n)
    hh=await page.evaluate("Math.min(...[...document.querySelectorAll('.atbctl .lc')].filter(x=>x.offsetParent).map(x=>x.getBoundingClientRect().height))")
    ok(L+"OMA : pastilles d'au moins 36 px (tactile)",hh>=36,hh)
    await page.locator('.atbctl [data-atbdur][data-n="7"]').first.click(); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : durée 7 j choisie → « pendant 7 jours » à l'écran, pastille « durée modifiée (fiche : 10 j) »",on and "pendant 7 jours" in on[0]["s"] and await page.locator(".atbctl .pcd",has_text="fiche : 10 j").count()>=1,on and on[0]["s"][:160])
    await page.locator('.atbctl [data-atbdose]').first.fill("9"); await page.locator('.atbctl [data-atbdose]').first.dispatch_event("change"); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : dose modifiée d'un geste → « 1 dose-poids 9 kg »",on and "1 dose-poids 9 kg" in on[0]["s"],on and on[0]["s"][:160])
    tr=await page.evaluate("ordoTrace()")
    ok(L+"OMA : écarts tracés (« durée choisie par le médecin : 7 j (fiche : 10 j) », dose choisie)",any("durée choisie par le médecin : 7 j (fiche : 10 j)" in x and "AUGMENTIN" in x for x in tr) and any("dose choisie par le médecin : 1 dose-poids 9 kg (calculée : 1 dose-poids 8 kg)" in x for x in tr),tr)
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"OMA : compte rendu avec « durée choisie par le médecin : 7 j »","durée choisie par le médecin : 7 j (fiche : 10 j)" in cr,[l for l in cr.split(chr(10)) if "choisie" in l])
    await page.evaluate("journalUpsert(currentPack())")
    jn=await page.evaluate("JSON.stringify((JOURNAL[JOURNAL.length-1]||{}).notes||[])")
    ok(L+"OMA : journal avec la durée et la dose choisies",("durée choisie par le médecin : 7 j" in jn) and ("dose choisie par le médecin" in jn),jn[:300])
    pr=await page.evaluate(PRINT)
    ok(L+"OMA, ordonnance : « pendant 7 jours » et « 1 dose-poids 9 kg » imprimés, jamais « choisie » ni « fiche »","pendant 7 jours" in pr["ordo"] and "1 dose-poids 9 kg" in pr["ordo"] and "choisie" not in pr["ordo"] and "fiche :" not in pr["ordo"],pr["ordo"][:300])
    await shot(page,f"atb-oma-15mois-8kg-{tag}.png",".atbctl")
    # second antibiotique ajouté par la recherche : remplace, puis « Ajouter quand même »
    await page.evaluate("()=>{const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');ordoAdd(si,'ORELOX 100 mg comprimé : 2 comprimés matin et soir pendant 5 jours.');render();}"); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : antibiotique ajouté par la recherche → il remplace AUGMENTIN (un seul antibiotique)",len(on)==1 and "ORELOX" in on[0]["t"],[(m["t"][:20],m["on"]) for m in M if m["atb"]])
    ok(L+"OMA : boîte « Un seul antibiotique … AUGMENTIN remplacé par ORELOX » avec le bouton « Ajouter quand même »",await page.locator(".atbbox").count()>=1 and "AUGMENTIN remplacé par ORELOX" in (await page.locator(".atbbox").first.inner_text()) and await page.locator(".atbbox [data-atb2]").count()>=1,await page.locator(".atbbox").count())
    await shot(page,f"atb-ajouter-quand-meme-{tag}.png",".atbbox")
    await page.locator(".atbbox [data-atb2]").first.click(); await page.wait_for_timeout(250)
    ok(L+"OMA : confirmation demandée (« Deux antibiotiques par voie générale »)",await page.locator("#atbover").count()==1 and "Deux antibiotiques" in (await page.locator("#atbover").inner_text()))
    await page.click("#atb_yes"); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : après confirmation, AUGMENTIN et ORELOX cochés ensemble, sans doublon",len(on)==2 and len([m for m in M if m["t"].startswith("AUGMENTIN")])==1,[(m["t"][:20],m["on"]) for m in M if m["atb"]])
    tr=await page.evaluate("ordoTrace()")
    ok(L+"OMA : association volontaire tracée au journal et au compte rendu",any("deux antibiotiques par voie générale associés volontairement" in x and "AUGMENTIN" in x and "ORELOX" in x for x in tr),tr)
    pr=await page.evaluate(PRINT)
    ok(L+"OMA, ordonnance : les deux antibiotiques imprimés, sans mention de la confirmation","AUGMENTIN" in pr["ordo"] and "ORELOX" in pr["ordo"] and "confirm" not in pr["ordo"] and "volontaire" not in pr["ordo"],pr["ordo"][:400])
    ok(L+"OMA : pas de blocage à l'impression après confirmation",await page.evaluate("atbConflict(currentPack()).length")==0)
    # sans confirmation : impression bloquée et alerte
    await page.evaluate("state.atb2ok=false;render();"); await page.wait_for_timeout(300)
    conf=await page.evaluate("atbConflict(currentPack()).map(x=>x.b)")
    M=await page.evaluate(MEDS); on=[m for m in M if m["on"] and m["atb"]]
    ok(L+"OMA : confirmation retirée → un seul antibiotique à nouveau (le dernier touché gardé)",len(on)==1,[(m["t"][:20],m["on"]) for m in M if m["atb"]])
    # le garde-fou de l'impression : deux antibiotiques détectés sans confirmation (le passage d'exclusivité les évite normalement : on simule la détection)
    blocked=await page.evaluate("""async()=>{const orig=atbConflict;atbConflict=()=>[{b:'AUGMENTIN'},{b:'ORELOX'}];try{await printPack();}finally{atbConflict=orig;}const o=document.getElementById('atbover');return {over:!!o,txt:o?o.innerText:'',printing:document.body.classList.contains('printing')};}""")
    ok(L+"OMA : deux antibiotiques sans confirmation à l'impression → blocage et alerte (rien n'est imprimé)",blocked["over"] and "Impression bloquée" in blocked["txt"] and not blocked["printing"],blocked)
    if await page.locator("#atb_fix").count(): await page.click("#atb_fix")
    await page.wait_for_timeout(200)
    # sans date de naissance : ligne non imprimée, manque signalé
    await page.evaluate(SET,{"ddn":"","poids":"8","n":"Otite moyenne aiguë — enfant","lieu":"visite"}); await page.wait_for_timeout(300)
    M=await page.evaluate(MEDS); cl=[m for m in M if m["t"].startswith("CLAMOXYL")]
    pr=await page.evaluate(PRINT)
    ok(L+"OMA sans date de naissance : antibiotique non imprimé, « date de naissance (durée de l'antibiotique selon l'âge) » signalé",cl and any("date de naissance" in z and "durée" in z for z in cl[0]["miss"]) and natb(pr["ordo"])==0 and any("date de naissance" in z for z in pr["removed"]),(cl and cl[0]["miss"],pr["removed"][:1]))
    # ---------- Cas 2 : angine, 2 ans ----------
    await page.evaluate(SET,{"ddn":months_ago(27),"poids":"12","n":"Angine — enfant (TROD positif)"}); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); at=[m for m in M if m["atb"]]
    pr=await page.evaluate(PRINT)
    ok(L+"angine 2 ans : aucun antibiotique imprimé",natb(pr["ordo"])==0 and at and all(any("avant 3 ans" in z for z in m["miss"]) for m in at),[(m["t"][:16],m["miss"][:1]) for m in at])
    ok(L+"angine 2 ans : message à l'écran « angine avant 3 ans, pas d'antibiotique (angine virale …) »","angine avant 3 ans" in (await page.inner_text("#main")),"")
    lg=await page.evaluate("ciLegal(currentPack())")
    ok(L+"angine 2 ans : règle rappelée avant d'imprimer (jamais sur l'ordonnance)",any("angine avant 3 ans" in x for x in lg) and "avant 3 ans" not in pr["ordo"],lg[:1])
    ok(L+"angine 2 ans : le paracétamol reste imprimé","DOLIPRANE" in pr["ordo"],pr["ordo"][:200])
    await shot(page,f"angine-2ans-non-imprime-{tag}.png",".alert.rule, .xp-med.miss")
    # angine 5 ans 18 kg : durées selon l'antibiotique
    await page.evaluate(SET,{"ddn":months_ago(63),"poids":"18","n":"Angine — enfant (TROD positif)"}); await page.wait_for_timeout(350)
    M=await page.evaluate(MEDS); d={m["t"].split(" ")[0]:m["s"] for m in M if m["atb"]}
    ok(L+"angine 5 ans 18 kg : amoxicilline 6 j « 4,5 ml matin et soir pendant 6 jours », cefpodoxime 5 j, céfuroxime 4 j, clarithromycine 5 j, azithromycine 3 j","4,5 ml matin et soir pendant 6 jours" in d.get("CLAMOXYL","") and "pendant 5 jours" in d.get("ORELOX","") and "pendant 4 jours" in d.get("ZINNAT","") and "pendant 5 jours" in d.get("ZECLAR","") and "pendant 3 jours" in d.get("ZITHROMAX",""),{k:v[:110] for k,v in d.items()})
    pr=await page.evaluate(PRINT)
    ok(L+"angine 5 ans, ordonnance : « amoxicilline (CLAMOXYL) 500 mg/5 ml poudre pour suspension buvable : 4,5 ml matin et soir pendant 6 jours. »","amoxicilline (CLAMOXYL) 500 mg/5 ml poudre pour suspension buvable : 4,5 ml matin et soir pendant 6 jours." in pr["ordo"],pr["ordo"][:300])
    # pneumopathie enfant : 5 jours ; adulte : libellé DCI (marque) ; association prévue par une fiche respectée
    await page.evaluate(SET,{"ddn":months_ago(50),"poids":"16","n":"Pneumopathie aiguë — enfant"}); await page.wait_for_timeout(300)
    M=await page.evaluate(MEDS); cl=[m for m in M if m["t"].startswith("CLAMOXYL")]
    ok(L+"pneumopathie enfant 16 kg : « 7 ml matin et soir pendant 5 jours » (HAS 2024), coché seul",cl and cl[0]["on"] and "7 ml matin et soir pendant 5 jours" in cl[0]["s"] and len([m for m in M if m["on"] and m["atb"]])==1,cl and cl[0]["s"][:120])
    await page.evaluate(SET,{"ddn":"01/01/1980","poids":"70","sexe":"h","pat":"DURAND Jean","n":"Angine — adulte (TROD positif)"}); await page.wait_for_timeout(300)
    pr=await page.evaluate(PRINT)
    ok(L+"angine adulte, ordonnance : « amoxicilline (CLAMOXYL) 1 g comprimé : 1 comprimé matin et soir pendant 6 jours. »","amoxicilline (CLAMOXYL) 1 g comprimé : 1 comprimé matin et soir pendant 6 jours." in pr["ordo"],pr["ordo"][:300])
    n2=await page.locator(".atbctl").count()
    ok(L+"angine adulte : pastilles de durée aussi sur la ligne adulte",n2>=1,n2)
    if await page.evaluate("document.body.classList.contains('printing')"):
        if await page.locator("#pb_back").count(): await page.click("#pb_back")
        await page.wait_for_timeout(300)
    # ---------- Cas 3 : renouvellement de 6 médicaments dont 2 en ALD ----------
    await page.evaluate(SET,{"ddn":"11/05/1950","poids":"","sexe":"h","pat":"DURAND Jean","n":"Renouvellement d'ordonnance"}); await page.wait_for_timeout(300)
    ok(L+"renouvellement : fiche dans le catalogue, « non relue », présente dans la rangée Fréquents (adulte, sujet âgé)",await page.evaluate("PACKS.some(p=>p.n==='Renouvellement d\\'ordonnance'&&p.rnw)&&JSON.stringify(PACKS.find(p=>p.n==='Renouvellement d\\'ordonnance').s).includes('fiche non relue (bloc 17')&&FREQ_DEF.adulte.includes('Renouvellement d\\'ordonnance')&&FREQ_DEF.age.includes('Renouvellement d\\'ordonnance')"))
    ok(L+"renouvellement : trouvée par la recherche « renouvellement »",await page.evaluate("(()=>{const q=norm('renouvellement');return PACKS.filter(p=>norm(p.n+' '+(p.k||'')).includes(q)).map(p=>p.n).includes('Renouvellement d\\'ordonnance');})()"))
    ok(L+"renouvellement : panneau affiché (recherche de médicament)",await page.locator("#rnw_q").count()>=1)
    await page.wait_for_function("BDPMX.rows!==null||BDPMX.err",timeout=30000)
    nb=await page.evaluate("[BDPMX.n,BDPMX.date,BDPMX.err]")
    ok(L+"base BDPM embarquée chargée (plus de 11 000 spécialités, date du fichier)",nb[0]>11000 and nb[1] and not nb[2],nb)
    await page.evaluate("render()"); await page.wait_for_timeout(300)
    # recherche hors connexion, nom commercial, DCI, avec et sans accents
    await ctx.set_offline(True)
    r1=await page.evaluate("bdpmxSearch('amlor',3).map(r=>r.n)"); r2=await page.evaluate("bdpmxSearch('levothyroxine 50',5).map(r=>r.n)"); r3=await page.evaluate("bdpmxSearch('kétoconazole',2).map(r=>r.n)"); r4=await page.evaluate("bdpmxSearch('ketoconazole',2).map(r=>r.n)"); r5=await page.evaluate("bdpmxSearch('skenan lp 10',1).map(r=>r.n)")
    ok(L+"hors connexion : recherche par nom commercial (« amlor » → AMLOR 5 mg, gélule en tête)",r1 and r1[0]=="AMLOR 5 mg, gélule",r1)
    ok(L+"hors connexion : recherche par DCI (« levothyroxine 50 » → LEVOTHYROX 50 microgrammes)",any(x.startswith("LEVOTHYROX 50") for x in r2),r2)
    ok(L+"accents indifférents (« kétoconazole » = « ketoconazole »)",r3 and r3==r4,(r3,r4))
    ok(L+"« skenan lp 10 » → SKENAN L.P. 10 mg",r5 and r5[0].startswith("SKENAN L.P. 10 mg"),r5)
    await ctx.set_offline(False)
    # saisie dans le champ : autocomplétion, choix de la présentation
    q=page.locator("#rnw_q").first
    await q.click(); await q.fill("amlo"); await page.wait_for_timeout(400)
    sg=page.locator("#rnw_sg .sg[data-cis]")
    ok(L+"« amlo » : propositions dès 4 lettres, présentations (AMLOR 5 mg, AMLOR 10 mg, génériques)",await sg.count()>=3 and "AMLOR 5 mg" in (await sg.first.inner_text()),await sg.count())
    await sg.first.dispatch_event("mousedown"); await page.wait_for_timeout(400)
    ok(L+"ligne ajoutée : amlodipine (AMLOR) 5 mg gélule, durée 1 mois par défaut",await page.evaluate("rnwState().items.length===1&&rnwState().items[0].brand==='AMLOR'&&rnwState().items[0].dci==='amlodipine'&&rnwState().items[0].dur==='1 mois'"),await page.evaluate("JSON.stringify(rnwState().items)"))
    await page.locator('[data-rpos="0"]',has_text="1 gélule le matin").first.click(); await page.wait_for_timeout(300)
    await page.locator('[data-rald="0"]').first.check(); await page.wait_for_timeout(300)
    it0=await page.evaluate("rnwState().items[0]")
    ok(L+"posologie d'un geste (« 1 gélule le matin ») et ALD cochée",it0["poso"]=="1 gélule le matin" and it0["ald"],it0)
    await page.evaluate("""()=>{[['levothyrox 50','1 comprimé le matin à jeun',false],['metformine biogaran 1000','1 comprimé matin et soir',true],['kardegic 75','1 sachet le midi',false],['tahor 10','1 comprimé le soir',false],['inexium 20','1 comprimé le matin',false]].forEach(([q,poso,ald])=>{const r=bdpmxSearch(q,1)[0];rnwAdd(r,false);const it=rnwState().items[rnwState().items.length-1];it.poso=poso;it.ald=ald;});render();}"""); await page.wait_for_timeout(400)
    M=await page.evaluate(MEDS)
    ok(L+"6 lignes générées, DCI puis nom commercial, posologie, durée : « lévothyroxine (LEVOTHYROX) 50 microgrammes comprimé sécable : 1 comprimé le matin à jeun pendant 1 mois. »",len(M)==6 and any(m["s"]=="lévothyroxine (LEVOTHYROX) 50 microgrammes comprimé sécable : 1 comprimé le matin à jeun pendant 1 mois." for m in M),[m["s"][:90] for m in M])
    ok(L+"générique nommé par sa DCI : « METFORMINE BIOGARAN 1000 mg comprimé pelliculé : … » sans répétition",any(m["s"].startswith("METFORMINE BIOGARAN 1000 mg comprimé pelliculé : 1 comprimé matin et soir") for m in M),[m["s"][:60] for m in M])
    await page.locator('[data-rns="0"]').first.check(); await page.wait_for_timeout(300)
    pr=await page.evaluate(PRINT); o=pr["ordo"]
    ok(L+"6 médicaments dont 2 en ALD : une seule ordonnance bizone, une page (ALD en haut, maladies intercurrentes en bas)",len([p for p in pr["pages"] if p["h"].startswith("Ordonnance")])==1 and "(1/2)" not in o and "affection de longue durée reconnue" in o and "sans rapport avec l'affection de longue durée" in o and o.index("AMLOR")<o.index("affection de longue durée (maladies")<o.index("LEVOTHYROX"),o[:500])
    ok(L+"bizone : les 2 lignes ALD dans la partie haute, les 4 autres en bas",o.index("METFORMINE")<o.index("maladies intercurrentes")<o.index("KARDEGIC"),o[:500])
    ok(L+"« Non substituable (MTE) » imprimé sur la ligne choisie","amlodipine (AMLOR) 5 mg gélule : 1 gélule le matin pendant 1 mois. Non substituable (MTE)." in o,o[:300])
    ok(L+"ordonnance : date, patient, DCI + nom commercial, posologie, durée ; rien de retiré","DURAND Jean" in o and "pendant 1 mois" in o and not pr["removed"],pr["removed"])
    await page.evaluate("journalUpsert(currentPack())")
    je=await page.evaluate("JSON.stringify(JOURNAL[JOURNAL.length-1]||{})")
    ok(L+"journal : motif « Renouvellement d'ordonnance » et liste des médicaments","Renouvellement d'ordonnance" in je and "renouvellement — amlodipine (AMLOR) 5 mg gélule" in je and "(ALD)" in je,je[:400])
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"compte rendu : trame renouvellement, traitement listé, écarts","Renouvellement" in cr and "amlodipine" in cr and "ORDONNANCE ADAPTÉE" in cr,cr[:400])
    cot=await page.evaluate("(()=>{const e=JOURNAL[JOURNAL.length-1];const c=cotCompute(e);return c.codes.map(x=>x.c).join('+');})()")
    ok(L+"cotation habituelle (G ou VG + majorations selon l'heure)",re.match(r"^(G|VG)(\+|$)",cot) is not None,cot)
    ok(L+"Express / bouton : rien ne bloque (posologies renseignées, une page)",not [w for w in (await page.evaluate("xpPending(currentPack())")) if "posologie" in w or "trop longue" in w],await page.evaluate("xpPending(currentPack())"))
    sw=await page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
    ok(L+"aucun débordement horizontal",sw[0]<=sw[1],sw)
    await shot(page,f"renouvellement-liste-{tag}.png","#rnw")
    # ordre modifiable, suppression d'un geste
    await page.locator('[data-rdown="0"]').first.click(); await page.wait_for_timeout(300)
    ok(L+"ordre : « ↓ » descend AMLOR en 2e position",await page.evaluate("rnwState().items[1].brand==='AMLOR'&&rnwState().items[0].brand==='LEVOTHYROX'"))
    await page.locator('[data-rdel="5"]').first.click(); await page.wait_for_timeout(300)
    ok(L+"suppression d'un geste (×) : 5 lignes",await page.evaluate("rnwState().items.length")==5)
    # récents (chiffrés avec le profil)
    await page.evaluate("rnwLearn(currentPack())")
    nrec=await page.evaluate("RNW.recent.length")
    ok(L+"médicaments récemment renouvelés mémorisés (5)",nrec>=5,nrec)
    await page.evaluate(SET,{"ddn":"11/05/1950","poids":"","sexe":"h","pat":"MARTIN Paul","n":"Renouvellement d'ordonnance"}); await page.wait_for_timeout(350)
    ok(L+"nouveau patient : les récents sont proposés en premier (« Récemment renouvelés : AMLOR 5 mg… »)",await page.locator(".rnw-rec .chip").count()>=5 and "AMLOR" in (await page.locator(".rnw-rec").first.inner_text()),await page.locator(".rnw-rec .chip").count())
    await page.locator('.rnw-rec [data-rrec]',has_text="AMLOR").first.click(); await page.wait_for_timeout(300)
    ok(L+"récent repris avec sa posologie et sa durée",await page.evaluate("rnwState().items.length===1&&rnwState().items[0].brand==='AMLOR'&&rnwState().items[0].poso==='1 gélule le matin'"),await page.evaluate("JSON.stringify(rnwState().items[0])"))
    ok(L+"posologie absente → ligne non imprimée et manque signalé",await page.evaluate("(()=>{rnwState().items[0].poso='';render();const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');const x=resolve(p.s[si],si)[0];return x.fill.miss.some(m=>/posologie de AMLOR/.test(m))&&!buildPages(p,true).out.includes('AMLOR');})()"))
    await page.evaluate("rnwState().items[0].poso='1 gélule le matin';render();"); await page.wait_for_timeout(200)
    # ---------- Cas 4 : morphinique ----------
    await page.evaluate("()=>{const r=bdpmxSearch('skenan lp 10',1)[0];rnwAdd(r,false);const it=rnwState().items[rnwState().items.length-1];it.poso='1 gélule matin et soir';it.dur='7 jours';render();}"); await page.wait_for_timeout(350)
    al=page.locator(".rnw-it.sec .rnw-al").first
    ok(L+"morphinique (SKENAN) : alerte « ordonnance sécurisée requise, quantités en toutes lettres »",await al.count()>=1 and "Ordonnance sécurisée requise, quantités en toutes lettres" in (await al.inner_text()),await al.count())
    pr=await page.evaluate(PRINT)
    ok(L+"morphinique : pas d'impression sur le modèle simple (AMLOR imprimé, SKENAN absent)","AMLOR" in pr["ordo"] and "SKENAN" not in pr["ordo"] and "morphine" not in pr["ordo"],pr["ordo"][:300])
    lg=await page.evaluate("ciLegal(currentPack())")
    ok(L+"morphinique : « ordonnance sécurisée à rédiger à la main » rappelé avant d'imprimer, inscrit au journal et au compte rendu",any("Ordonnance sécurisée à rédiger à la main" in x and "SKENAN" in x for x in lg) and "SKENAN" in (await page.evaluate("buildCR(currentPack())")),lg[:1])
    await page.evaluate("journalUpsert(currentPack())")
    jn=await page.evaluate("JSON.stringify((JOURNAL[JOURNAL.length-1]||{}).notes||[])")
    ok(L+"morphinique : au journal avec la mention « ordonnance sécurisée à rédiger à la main, non imprimée »","SKENAN" in jn and "ordonnance sécurisée à rédiger à la main, non imprimée" in jn,jn[:300])
    await shot(page,f"renouvellement-stupefiant-{tag}.png",".rnw-it.sec")
    # réservé à l'hôpital : non imprimé ; prescription initiale hospitalière : renouvelable
    hosp=await page.evaluate("(()=>{const r=BDPMX.rows.find(x=>/H/.test(x.f)&&!/S/.test(x.f));if(!r)return null;rnwAdd(r,false);const it=rnwState().items[rnwState().items.length-1];it.poso='1 le matin';render();const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');const x=resolve(p.s[si],si).find(y=>y.rnw===rnwState().items.length-1);const out=buildPages(p,true).out;const res={miss:x.fill.miss,printed:out.includes(r.brand.slice(0,12))};rnwState().items.pop();render();return res;})()")
    ok(L+"médicament hospitalier : ligne non imprimée, règle affichée",hosp and any("hôpital" in m for m in hosp["miss"]) and not hosp["printed"],hosp)
    # ---------- Cas 5 : 20 lignes → alerte de dépassement de page, proposition de deux ordonnances ----------
    await page.evaluate("""()=>{const S=rnwState();S.items=S.items.filter(i=>!rnwSecure(i));const qs=['amlor 5','levothyrox 50','metformine biogaran 1000','kardegic 75','tahor 10','inexium 20','bisoprolol 5','ramipril 5','furosemide 40','allopurinol 100','uvedose','tardyferon 80','cacit 500','tamsulosine','lercanidipine 10','ezetimibe 10','vitamine b12','mopral 20','daflon 500','gaviscon menthe'];qs.forEach(q=>{const r=bdpmxSearch(q,1)[0];if(!r||S.items.some(x=>x.cis===r.cis))return;S.items.push({cis:r.cis,n:r.n,dci:r.dci,brand:r.brand,dos:r.dos,forme:r.forme,f:r.f,mj:r.mj,poso:'1 le matin',dur:'1 mois',ns:false,nsc:'MTE',ald:false});});S.items[0].ald=true;S.items[2].ald=true;render();}"""); await page.wait_for_timeout(400)
    n=await page.evaluate("rnwState().items.length")
    ok(L+"20 lignes : alerte « ne tient pas sur une page » et bouton « Deux ordonnances »",n>=18 and await page.locator(".rnw-foot .red").count()>=1 and await page.locator("#rnw_split").count()>=1,(n,await page.locator(".rnw-foot").first.inner_text() if await page.locator(".rnw-foot").count() else ""))
    pend=await page.evaluate("xpPending(currentPack())")
    ok(L+"20 lignes : l'impression attend la décision (« ordonnance trop longue : deux ordonnances ? »)",any("trop longue" in w for w in pend),pend)
    await shot(page,f"renouvellement-20-lignes-{tag}.png",".rnw-foot")
    await page.evaluate("printPack()"); await page.wait_for_timeout(600)
    ok(L+"20 lignes : à l'impression, alerte et proposition de deux ordonnances",await page.locator("#rnwover").count()==1 and "deux ordonnances" in (await page.locator("#rnwover").inner_text()).lower(),await page.locator("#rnwover").count())
    await page.click("#rnw_two"); await page.wait_for_timeout(900)
    if await page.locator("#ciover").count():
        await page.click("#ci_keep"); await page.wait_for_timeout(200); await page.click("#ci_print"); await page.wait_for_timeout(900)
    try:
        await page.wait_for_selector("#print .page",timeout=15000); await page.wait_for_timeout(800)
    except Exception: pass
    pg=await page.evaluate("[...document.querySelectorAll('#print .page')].map(x=>(x.querySelector('h2')||{}).textContent||'')")
    ok(L+"deux ordonnances complètes (1/2 et 2/2), chacune une page, puis les consignes",pg[:2]==["Ordonnance (1/2)","Ordonnance (2/2)"],pg)
    ok(L+"chaque ordonnance porte en-tête, patient et signature",await page.evaluate("[...document.querySelectorAll('#print .page')].slice(0,2).every(x=>x.querySelector('.ph')&&x.innerText.includes('MARTIN')&&x.querySelector('.sig,.stamp'))"))
    if not mob: await shot(page,f"renouvellement-deux-ordonnances-{tag}.png")
    if await page.locator("#pb_back").count(): await page.click("#pb_back"); await page.wait_for_timeout(300)
    # aperçu bizone (ordinateur)
    if not mob and not big:
        await page.evaluate("""()=>{const S=rnwState();S.items=S.items.slice(0,6);S.split=false;S.items[0].ald=true;S.items[2].ald=true;render();}"""); await page.wait_for_timeout(300)
        await page.evaluate("printPack()"); await page.wait_for_timeout(700)
        if await page.locator("#ciover").count():
            await page.click("#ci_keep"); await page.wait_for_timeout(200); await page.click("#ci_print"); await page.wait_for_timeout(700)
        try:
            await page.wait_for_selector("#print .page",timeout=15000); await page.wait_for_timeout(800)
        except Exception: pass
        fw=await page.evaluate("(document.querySelector('#print .fitwarn')||{}).textContent||''")
        ok(L+"aperçu bizone : une page, pas d'alerte de dépassement",not fw and await page.evaluate("document.querySelectorAll('#print .page h2')[0].textContent")=="Ordonnance",fw[:200])
        await shot(page,f"renouvellement-bizone-apercu-{tag}.png")
        if await page.locator("#pb_back").count(): await page.click("#pb_back"); await page.wait_for_timeout(300)
    ok(L+"aucune erreur JS",not errors,errors[:3])
    await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,xp,th,big,label) in [(375,812,True,"day",False,"iPhone Express jour"),(375,812,True,"night",True,"iPhone Express nuit grand texte"),(375,812,False,"day",False,"iPhone mode complet"),(1280,900,False,"day",False,"ordinateur jour"),(1280,900,False,"night",True,"ordinateur nuit grand texte")]:
                await run(b,w,h,xp,th,big,label)
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_atb_renouvellement.md"),"w",encoding="utf-8").write("# Tests antibiotiques et renouvellement d'ordonnance (11/11/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
