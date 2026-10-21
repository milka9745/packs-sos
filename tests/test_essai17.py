# Essai réel du 17/10/2026 sur /test/ — points 4 à 8 (les points 1 et 2, cachet et impression, sont dans test_pdf_iphone.py et test_lot1.py).
# 4 « Aide à l'interprétation » jamais imprimée ; 5 courrier sans dictée brute, accords, constantes aberrantes ;
# 6 motif de régulation (DLMINF, jamais l'adresse, Fréquents) ; 7 favoris bouton par bouton ; 8 « reste de l'examen normal ».
# 375 px (jour, nuit, grand texte) et ordinateur. Patients fictifs.
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
PORT=8798 if os.environ.get("XP","on")!="off" else 8799
XPOFF=os.environ.get("XP","on")=="off"   # XP=off : mêmes tests en mode complet (Express coupé)
STOPS=open(os.path.join(ROOT,"tests","audit_express.py"),encoding="utf-8").read().split('STOPS="""')[1].split('"""')[0]
async def unlock(page,uid):
    if XPOFF: await page.add_init_script("try{localStorage.setItem('sos_xp','false')}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
PAGES="""()=>{const p=currentPack();const d=document.createElement('div');d.innerHTML=buildPages(p,true).out;return [...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}));}"""
SETP="""(a)=>{newPatient();Object.assign(state,a.pat,{date:'17/10/2026'});state.view='';state.sel=PACKS.findIndex(p=>p.n===a.n);if(a.obs)Object.assign(state.obs,a.obs);if(a.cst)Object.assign(state.cst,a.cst);render();return state.sel;}"""
FICHE="MARTIN PAUL\nNé(e) le 01/02/1980 - 46 A\nTél patient 06 11 22 33 44\nAdresse : 12 rue des Lilas\n45160 SAINT-HILAIRE-SAINT-\nMESMIN\n{M}\ndouleur du mollet depuis hier"
async def run(b,w,h,th,big,label):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    page.on("popup",lambda pg:asyncio.ensure_future(pg.close()))
    await unlock(page,"es"+label.replace(" ","")[:8]); L=label+" : "; tag=label.replace(" ","-")
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
    # 4 — feuilles « Pour le médecin » jamais imprimées
    await page.evaluate(SETP,{"n":"Tendinopathie d'Achille","pat":{"patient":"DURAND Paul","ddn":"14/05/1975","sexe":"h"}})
    pg=await page.evaluate(PAGES)
    ok(L+"4. « Aide à l'interprétation » et « Aide-mémoire » jamais dans les documents imprimés ni le PDF",pg and not any(x["h"].startswith("Aide") for x in pg),[x["h"] for x in pg])
    ok(L+"4. la feuille reste visible à l'écran (mode complet)",await page.evaluate("currentPack().s.some(s=>s.k==='interp')"))
    # 5 — courrier : pas de dictée brute, accords, constantes aberrantes
    HIST="Chute de sa hauteur ce matin dans la salle de bain, relevée par sa fille au bout de vingt minutes."
    await page.evaluate(SETP,{"n":"Chute du sujet âgé — bilan","pat":{"patient":"MARTIN Jeanne","ddn":"03/04/1938","sexe":"f"},"obs":{"hist":HIST,"dict":"Chute ce matin, relevée par sa fille. TA 150/10.","cv":"Bruits du cœur réguliers."},"cst":{"ta":"150/10"}})
    pg=await page.evaluate(PAGES); let_=" ".join(x["t"] for x in pg if x["h"].startswith("Courrier"))
    ok(L+"5. courrier : la dictée brute et l'histoire libre ne sont jamais recopiées","relevée par sa fille" not in let_ and "salle de bain" not in let_,let_[:300])
    ok(L+"5. courrier : champs structurés repris (constantes, examen)","Bruits du cœur réguliers" in let_ or "constantes" in let_.lower(),let_[:300])
    ok(L+"5. patiente : accords au féminin (pas de « le/la », « né(e) »)","le/la" not in let_ and "né(e)" not in let_ and "née le" in let_ and "la confie" in let_,let_[:400])
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"5. la dictée brute reste dans le compte rendu (MCC)","relevée par sa fille" in cr or "Chute de sa hauteur" in cr,cr[:200])
    ab=await page.evaluate("cstAbnormal()")
    ok(L+"5. TA 150/10 signalée comme constante à vérifier",any("150/10" in x for x in ab),ab)
    ok(L+"5. alerte visible à l'écran avant impression",await page.locator(".cstbad").count()>=1)
    if not XPOFF: ok(L+"5. Express : constante aberrante → l'aperçu s'ouvre au lieu d'imprimer","constante à vérifier" in await page.evaluate("xpPending(currentPack())"))
    await page.evaluate(SETP,{"n":"Chute du sujet âgé — bilan","pat":{"patient":"MARTIN Paul","ddn":"03/04/1938","sexe":"h"}})
    pg=await page.evaluate(PAGES); let_=" ".join(x["t"] for x in pg if x["h"].startswith("Courrier"))
    ok(L+"5. patient : accords au masculin","le/la" not in let_ and "né le" in let_ and "le confie" in let_,let_[:300])
    # 6 — motif de régulation
    r=await page.evaluate("(t)=>{const a=parseFiche(t.replace('{M}','DLMINF'));const b=parseFiche(t.replace('{M}\\n',''));return {a:a.motif,b:b.motif,addr:a.addr};}",FICHE)
    ok(L+"6. « DLMINF » reconnu comme motif",r["a"]=="DLMINF",r)
    ok(L+"6. jamais la commune (« SAINT-HILAIRE-SAINT- », « MESMIN ») comme motif","SAINT" not in r["b"] and "MESMIN" not in r["b"],r)
    c=await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'MARTIN Paul',ddn:'01/02/1980',sexe:'h'});state.xpMotif='DLMINF';return {ok:xpCandidates('DLMINF').ok.map(i=>PACKS[i].n),lib:(mccFind('DLMINF')||{}).lib};}")
    ok(L+"6. DLMINF adulte : entorse de cheville, contusion, tendinopathie, TVP selon le terrain",c["ok"][:4]==["Entorse de cheville","Contusion — traumatisme bénin","Tendinopathie d'Achille","Phlébite / thrombose veineuse profonde"] and c["lib"]=="douleur de membre inférieur",c)
    c=await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/03/2018',sexe:'f'});return xpCandidates('DLMINF').ok.map(i=>PACKS[i].n);}")
    ok(L+"6. DLMINF enfant : boiterie de l'enfant en tête, pas de tendinopathie",c and c[0]=="Boiterie de l'enfant" and "Tendinopathie d'Achille" not in c,c)
    c=await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/03/2018',sexe:'f'});return xpCandidates('XKZW').ok.map(i=>PACKS[i].n);}")
    ok(L+"6. motif non reconnu : Fréquents de l'âge, jamais une liste vide",len(c)>=3 and all("adulte" not in x for x in c),c)
    c=await page.evaluate("()=>{const T=mccTable().map(x=>Object.assign({},x));T.push({code:'DLABD',lib:'douleur abdominale',adulte:['Douleur abdominale aiguë — adulte'],enfant:[],terrain:[]});mccSave(T);newPatient();Object.assign(state,{ddn:'01/02/1980'});const r=xpCandidates('DLABD').ok.map(i=>PACKS[i].n);localStorage.removeItem('sos_mcc');return r;}")
    ok(L+"6. tableau modifiable : nouvelle abréviation prise en compte",c==["Douleur abdominale aiguë — adulte"],c)
    sr=await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'MARTIN Paul',ddn:'01/02/1980',sexe:'h'});render();search('DLMINF');return {n:[...document.querySelectorAll('#res button.res .n')].slice(0,4).map(x=>x.textContent),cat:(document.querySelector('#res .cat')||{}).textContent||''};}")
    ok(L+"6. liste « Autre fiche » / recherche du mode complet : DLMINF → fiches du tableau en tête",sr["n"][:3]==["Entorse de cheville","Contusion — traumatisme bénin","Tendinopathie d'Achille"] and "DLMINF" in sr["cat"],sr)
    sr=await page.evaluate("()=>{search('xkzwq');return {n:[...document.querySelectorAll('#res button.res .n')].length,cat:(document.querySelector('#res .cat')||{}).textContent||''};}")
    ok(L+"6. recherche du mode complet : rien de reconnu → fiches fréquentes, jamais une liste vide",sr["n"]>=3 and "fréquentes" in sr["cat"],sr)
    await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(200)
    ok(L+"6. tableau des abréviations dans le Journal (modifiable)",await page.locator(".mcct [data-mcc=code]").count()>=1)
    await page.evaluate("state.view='';render();")
    # 7 — favoris bouton par bouton dans « Plus d'options » de la tournée (sans objet en mode complet : l'Express est coupé)
    if not XPOFF:
      await page.evaluate(STOPS); await page.evaluate("xpOpenStop('v1')"); await page.wait_for_timeout(300)
      await page.evaluate("()=>{const d=document.getElementById('xp_plus');if(d)d.open=true;document.querySelectorAll('details.tc-more').forEach(x=>x.open=true);}"); await page.wait_for_timeout(200)
      ks=await page.evaluate("[...document.querySelectorAll('.tc-more .favstar')].map(s=>s.dataset.favk)")
      want=["btn:tc_free","btn:tc_addvisit","btn:tc_photo","btn:tc_fiche"]  # 18-20/10/2026 : « Tournée » et « Mode voiture » sont dans l'Express par défaut (déplacés hors de « Plus d'options »)
      ok(L+"7. « Tournée » dans les favoris de l'Express par défaut (18/10)",await page.locator(".xp #xp_favs #tc_view").count()==1)
      ok(L+"7. une étoile par bouton de « Plus d'options » (voiture, tournée, libérer, ajouter une visite, photo, fiche, autres applis)",all(k in ks for k in want) and any(k.startswith("btn:nav-") for k in ks),ks)
      ok(L+"7. plus d'étoile sur le groupe entier",await page.locator('.favstar[data-favk="sec:tcmore"]').count()==0)
      ok(L+"7. « Mode voiture » et « Tournée » dans l'Express par défaut (20/10)",await page.locator(".xp #xp_favs #tc_drive").count()==1 and await page.locator(".xp #xp_favs #tc_view").count()==1)
      await page.evaluate("if(!FAV.edit)favEditSet(true)"); await page.wait_for_timeout(250)  # 21/10/2026 : étoiles visibles seulement en mode « Modifier les favoris »
      await page.locator('.tc-more .favstar[data-favk="btn:tc_free"]').first.click(); await page.wait_for_timeout(400)
      ok(L+"7. « Libérer » ajouté à l'Express d'une étoile (seul en plus)",await page.locator(".xp #xp_favs #tc_free").count()==1 and await page.locator(".xp #xp_favs #tc_addvisit, .xp #xp_favs .tc-addv").count()==0)
      await page.evaluate("favReset()")
    # 8 — « reste de l'examen normal »
    await page.evaluate("localStorage.setItem('sos_excomplet','0')")  # 18/10 : comportement du réglage « Examen complet » désactivé (activé : test_examen18.py)
    D="Fièvre depuis hier. Tympan droit bombé, rouge. Reste de l'examen normal."
    await page.evaluate(SETP,{"n":"Otite moyenne aiguë — enfant","pat":{"patient":"PETIT Lou","ddn":"01/03/2022","sexe":"f","poids":"16"},"obs":{"dict":D}})
    await page.evaluate("applyDictation()"); await page.wait_for_timeout(200)
    o=await page.evaluate("({orl:state.obs.orl,gen:state.obs.gen,resp:state.obs.resp,auto:Object.keys(state.obsAuto||{})})")
    ok(L+"8. ce qui est dicté n'est pas modifié (ORL : tympan bombé)","bombé" in (o["orl"] or "") and "orl" not in o["auto"],o)
    ok(L+"8. examen normal inséré pour les appareils non dictés, adapté à l'enfant","enfant" in (o["gen"] or "") and "gen" in o["auto"] and "resp" in o["auto"],o)
    ok(L+"8. texte inséré surligné et modifiable avant validation",await page.locator(".obsauto [data-oa]").count()>=2)
    if XPOFF:
        await page.evaluate("state.obsOpen=true;render();"); await page.wait_for_timeout(200)
        ok(L+"8. mode complet : champs insérés surlignés dans l'observation (« inséré · à valider »)",await page.locator(".sys.autoins").count()>=2)
    if mob:
        await page.evaluate("document.querySelector('.obsauto').scrollIntoView({block:'center'})"); await page.wait_for_timeout(200)
        await page.screenshot(path=os.path.join(OUT,f"essai17-examen-normal-{tag}{'-complet' if XPOFF else ''}.png"))
    await page.locator(".obsauto [data-oa]").first.fill("Bon état général, enfant grognon mais consolable.")
    ok(L+"8. modifiable d'un toucher : la modification est gardée",await page.evaluate("state.obs.gen")=="Bon état général, enfant grognon mais consolable." and "gen" not in await page.evaluate("Object.keys(state.obsAuto||{})"))
    await page.evaluate("state.obs.dict='Fièvre depuis hier. Tympan droit bombé, rouge.';applyDictation();"); await page.wait_for_timeout(200)
    o=await page.evaluate("({resp:state.obs.resp||'',gen:state.obs.gen||'',auto:Object.keys(state.obsAuto||{})})")
    ok(L+"8. sans la phrase : rien n'est inséré (et l'insertion non modifiée est retirée), la modification du médecin est gardée",not o["auto"] and not o["resp"] and "grognon" in o["gen"],o)
    await page.evaluate(SETP,{"n":"Rhinopharyngite — adulte","pat":{"patient":"DURAND Paul","ddn":"14/05/1975","sexe":"h"},"obs":{"dict":"Toux depuis 3 jours. Auscultation : crépitants à droite. Examen normal par ailleurs."}})
    await page.evaluate("applyDictation()")
    o=await page.evaluate("({resp:state.obs.resp,auto:Object.keys(state.obsAuto||{})})")
    ok(L+"8. « examen normal par ailleurs » : l'anomalie dictée est gardée telle quelle","crépitants" in (o["resp"] or "") and "resp" not in o["auto"] and len(o["auto"])>=1,o)
    await page.evaluate("localStorage.setItem('sos_excomplet','1')")
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
    open(os.path.join(ROOT,"tests","resultats_essai17"+("_complet" if XPOFF else "")+".md"),"w",encoding="utf-8").write("# Tests de l'essai réel du 17/10/2026 (points 4 à 8)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
