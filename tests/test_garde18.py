# Garde du 18/10/2026 (main v41k, PC) — vérifications et corrections, branche ia :
# 1 fiches et lignes réservées à un sexe (blocage + alerte, lignes jamais imprimées) ; 2 mémo médecin jamais imprimé (tout le catalogue) ;
# 3 ordonnance courte sur une seule page, cachet jamais scindé (PC Chrome, PC Edge, iPhone WebKit ; écrans Windows à 100, 125 et 150 %) ;
# 4 jamais « né(e) » ; 5 ligne en texte libre (majuscule, nom commercial en majuscules) ; + validation confirmée en 2 touchers ; Tournée dans les favoris Express.
# Lancer : python tests/test_garde18.py
import asyncio, os, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
PORT=8814
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=20000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=20000); await page.wait_for_timeout(800)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
IDFAKE="""()=>{const c=document.createElement('canvas');c.width=900;c.height=760;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,900,760);g.strokeStyle='#1a3a8a';g.lineWidth=10;g.beginPath();g.arc(450,330,300,0,7);g.stroke();
  g.fillStyle='#1a3a8a';g.font='bold 54px sans-serif';g.textAlign='center';g.fillText('CACHET FICTIF',450,340);g.font='italic 60px serif';g.fillText('signature',450,700);
  identApply({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:c.toDataURL('image/png')});state.cachet=true;window.print=()=>{window.__pr=(window.__pr||0)+1;};
  window.__share=[];navigator.canShare=()=>true;navigator.share=(d)=>{window.__share.push((d.files||[]).map(f=>({n:f.name,t:f.type,s:f.size})));return Promise.resolve();};return IDENT.on;}"""
SET="""(a)=>{newPatient();Object.assign(state,{patient:a.pat||'DURAND Paul',ddn:a.ddn||'14/05/1975',sexe:a.sx===undefined?'h':a.sx,poids:a.w||'',date:'18/10/2026'});state.sel=PACKS.findIndex(p=>p.n===a.n);state.cot.lieu='consultation';state.cachet=true;render();return state.sel;}"""
PAGES="(()=>{const d=document.createElement('div');d.innerHTML=buildPages(currentPack(),true).out;return [...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}));})()"
DOC_RE=re.compile(r"indiqu|différencier|femme en âge de procréer|contre-indiqu|\bDFG\b|critère|suspicion|gynécomastie vraie|adipomastie|cellulite|conjonctivite grave|RCP|hors AMM",re.I)
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for xp in (False,True):
                L=f"PC · {'Express' if xp else 'mode complet'} : "
                ctx=await b.new_context(viewport={"width":1280,"height":900})
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; dialogs=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
                await unlock(page,"g18"+("x" if xp else "c"),xp); await page.evaluate(IDFAKE)
                # 1. sexe
                await page.evaluate(SET,{"n":"Gynécomastie","sx":"f","pat":"MARTIN Jeanne","ddn":"05/06/1975"}); await page.wait_for_timeout(300)
                al=await page.evaluate("[...document.querySelectorAll('.sexmis')].map(x=>x.innerText).join(' | ')")
                ok(L+"1. Gynécomastie chez une femme : alerte rouge « réservée aux hommes » à l'écran","réservée aux hommes" in al and "bloquée" in al,al[:200])
                pg=await page.evaluate(PAGES)
                ok(L+"1. Gynécomastie chez une femme : aucun document produit (blocage)",not pg,[x["h"] for x in pg])
                await page.evaluate("window.__toast='';const t0=window.toast;window.toast=m=>{window.__toast=m;t0(m);};printPack()"); await page.wait_for_timeout(500)
                ok(L+"1. impression bloquée avec message",await page.locator("#print .page").count()==0 and "bloquée" in await page.evaluate("window.__toast"),await page.evaluate("window.__toast"))
                if xp: ok(L+"1. Express : « Imprimer et valider » renvoie à la vérification (fiche réservée)",any("réservée" in w for w in await page.evaluate("xpPending(currentPack())")))
                await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';state.view='';render();")
                await page.evaluate(SET,{"n":"Grossesse — premier trimestre et nausées","sx":"h"})
                ok(L+"1. fiche grossesse chez un homme : bloquée",not await page.evaluate(PAGES) and await page.locator(".sexmis").count()>=1)
                await page.evaluate(SET,{"n":"Gynécomastie","sx":"h"})
                ok(L+"1. Gynécomastie chez un homme : documents produits, pas d'alerte",len(await page.evaluate(PAGES))>=1 and await page.locator(".sexmis").count()==0)
                await page.evaluate(SET,{"n":"Gynécomastie","sx":""}); await page.wait_for_timeout(200)
                ok(L+"1. sexe non renseigné : alerte avec bouton « Homme »",await page.locator("[data-sexfix='h']").count()>=1)
                await page.locator("[data-sexfix='h']:visible").first.click(); await page.wait_for_timeout(300)
                ok(L+"1. un toucher : sexe fixé à homme",await page.evaluate("state.sexe")=="h")
                await page.evaluate(SET,{"n":"Fuites urinaires — incontinence (homme / femme)","sx":"h"})
                t=" ".join(x["t"] for x in await page.evaluate(PAGES))
                ok(L+"1. fiche mixte, homme : jamais d'ovule ni de crème vaginale imprimés","TROPHIGIL" not in t and "vaginal" not in t.lower(),t[:200])
                await page.evaluate(SET,{"n":"Fuites urinaires — incontinence (homme / femme)","sx":"f","pat":"MARTIN Jeanne"})
                t=" ".join(x["t"] for x in await page.evaluate(PAGES))
                ok(L+"1. fiche mixte, femme : jamais de PSA imprimé","PSA" not in t,t[:200])
                await page.evaluate(SET,{"n":"Dépistage IST complet","sx":"h"})
                t=" ".join(x["t"] for x in await page.evaluate(PAGES))
                ok(L+"1. dépistage IST, homme : aucune ligne « (femme) » ni auto-prélèvement vaginal seul","(femme)" not in t,t[:300])
                sw=await page.evaluate("""()=>{const bad=[];for(const sx of ['h','f']){for(let i=0;i<PACKS.length;i++){const ps=packSex(PACKS[i]);if(ps&&ps!==sx)continue;newPatient();Object.assign(state,{patient:'X',ddn:'01/01/1980',sexe:sx});state.sel=i;let out='';try{out=buildPages(PACKS[i],true).out;}catch(e){continue;}
                  const d=document.createElement('div');d.innerHTML=out;const t=d.innerText;if(sx==='h'&&/test (urinaire )?de grossesse|\\bovules?\\b|frottis (cervico|du col)/i.test(t))bad.push([PACKS[i].n,sx]);if(sx==='f'&&/\\bPSA\\b|échographie (testiculaire|scrotale)/i.test(t))bad.push([PACKS[i].n,sx]);}}return bad;}""")
                ok(L+"1. tout le catalogue : jamais une ligne réservée imprimée pour l'autre sexe",not sw,sw[:6])
                # 2. mémo médecin
                mm=await page.evaluate("""()=>{const bad=[];const DOC=/indiqué\s*:|\(indiqu|\(si |\(sauf |différencier|femme en âge de procréer|critère d'|adipomastie|gynécomastie vraie|conjonctivite grave|\bRCP\b|hors AMM|\bDFG\s*[<>≤≥]/i;let n=0;
                  const ctx=[{ddn:'01/01/1975',sexe:'h',poids:'75'},{ddn:'01/01/1980',sexe:'f',poids:'60'},{ddn:'01/01/2019',sexe:'f',poids:'22'}];
                  for(const c of ctx){for(let i=0;i<PACKS.length;i++){newPatient();Object.assign(state,{patient:'TEST X'},c);state.sel=i;if(sexConflict().length)continue;
                    PACKS[i].s.forEach((sh,si)=>{if(!PRINT_CLEAN_K.includes(sh.k))return;let r=[];try{r=resolve(sh,si);}catch(e){return;}
                      r.forEach(x=>{if(!x.on||x.jr||x.fill.miss.length)return;n++;const t=printClean(x.fill.s,sh.k);const again=memoSplit(t,sh.k);if(again.m.length||DOC.test(t))bad.push([PACKS[i].n,sh.k,(again.m[0]||t).slice(0,80)]);});});}}
                  return {n:bad.length,lignes:n,ex:bad.slice(0,10)};}""")
                ok(L+f"2. tout le catalogue × 3 profils ({mm['lignes']} lignes imprimées) : aucun mémo médecin",mm["n"]==0,mm)
                for n,sx,forbid in [("Gynécomastie","h",["gynécomastie vraie","adipomastie","différencier","tumeur testiculaire"]),("Hyperprolactinémie — bilan","f",["femme en âge de procréer","hypothyroïdie","adénome suspecté"]),("Angine — enfant (TROD positif)","f",["indiqué","allergie aux pénicillines","RCP"]),("Syndrome otite-conjonctivite — enfant","f",["indiqué","seringue graduée","allergie grave"])]:
                    await page.evaluate(SET,{"n":n,"sx":sx,"ddn":"01/01/2016" if "enfant" in n else "01/01/1980","w":"20" if "enfant" in n else ""})
                    t=" ".join(x["t"] for x in await page.evaluate(PAGES) if not re.match(r"(Consignes|Compte rendu|Courrier|Aide)",x["h"]))
                    hit=[f for f in forbid if f.lower() in t.lower()]
                    ok(L+f"2. « {n} » : aucun mémo médecin imprimé ({', '.join(forbid)})",not hit,hit)
                await page.evaluate(SET,{"n":"Gynécomastie","sx":"h"})
                if not xp:
                    dn=await page.evaluate("[...document.querySelectorAll('.dnote')].map(x=>x.textContent).join(' | ')")
                    ok(L+"2. écran : le mémo médecin reste visible (grisé, « jamais imprimé »)","gynécomastie vraie" in dn or "adipomastie" in dn,dn[:200])
                ok(L+"2. utile au patient gardé : « (soit 350 mg d'amoxicilline) », DCI, « (ou équivalent) »",await page.evaluate("[memoSplit('X : 3,5 ml (soit 350 mg) matin et soir.').p.includes('(soit 350 mg)'),memoSplit('ADVILMED (ibuprofène) : 5 ml.').p.includes('(ibuprofène)'),memoSplit('Attelle (ou équivalent).','dm').p.includes('(ou équivalent)'),memoSplit('CLAMOXYL poudre pour suspension buvable : 5 ml matin et soir.').p.includes('5 ml matin')].every(Boolean)"))
                # 4. né(e)
                await page.evaluate(SET,{"n":"Rhinopharyngite — adulte","sx":""})
                t=" ".join(x["t"] for x in await page.evaluate(PAGES))
                ok(L+"4. sexe non renseigné : jamais « né(e) » (formule neutre « date de naissance »)","né(e)" not in t and "date de naissance" in t,t[:200])
                await page.evaluate(SET,{"n":"Rhinopharyngite — adulte","sx":"f","pat":"MARTIN Jeanne"})
                t=" ".join(x["t"] for x in await page.evaluate(PAGES))
                ok(L+"4. patiente : « née le »","née le" in t and "né(e)" not in t)
                # 5. ligne libre
                if not xp:
                    await page.evaluate(SET,{"n":"Rhinopharyngite — adulte","sx":"h"})
                    si=await page.evaluate("currentPack().s.findIndex(s=>s.k==='med')")
                    await page.fill(f"#fl_{si}","kardegic 75 mg : 1 sachet par jour"); await page.wait_for_timeout(300)
                    await page.evaluate(f"document.getElementById('sg_{si}').innerHTML=''")
                    await page.press(f"#fl_{si}","Enter"); await page.wait_for_timeout(300)
                    ex=await page.evaluate(f"(state.extra[{si}]||[]).slice(-1)[0]||''")
                    ok(L+"5. ligne libre : nom commercial en majuscules, majuscule initiale",ex.startswith("KARDEGIC 75 mg : 1 sachet par jour"),ex)
                ok(L+"5. ligne libre : majuscule initiale, DCI et mots inconnus tels quels",await page.evaluate("[normFreeLine('paracétamol 500 mg'),normFreeLine('crème hydratante soir'),normFreeLine('eliquis 5 mg')]")==["Paracétamol 500 mg","Crème hydratante soir","ELIQUIS 5 mg"])
                # validation confirmée en 2 touchers
                await page.evaluate("localStorage.setItem('sos_excomplet','0')")
                await page.evaluate(SET,{"n":"Rhinopharyngite — adulte","sx":"h"}); await page.evaluate("valGate._w=0;state.view='';render();")
                v1=await page.evaluate("(()=>{patientValidate();return state.view;})()")
                v2=await page.evaluate("(()=>{patientValidate();return state.view;})()")
                ok(L+"validation : 1er toucher = demande de confirmation, 2e toucher = validé (jamais de fenêtre système)",v1!="valid" and v2=="valid" and not dialogs,[v1,v2,dialogs[:1]])
                await page.evaluate("localStorage.setItem('sos_excomplet','1');state.view='';render();")
                # Tournée dans les favoris de l'Express
                ok(L+"Tournée dans les favoris de l'Express par défaut",await page.evaluate("favHas('btn:tc_view')"))
                ok(L+"aucune erreur JS",not errors,errors[:3])
                await ctx.close()
            # 3. une page, cachet entier : PC (Chrome, Edge ; Windows 100/125/150 %) et iPhone
            async def onepage(br,label,dev):
                ctx=await br.new_context(**dev)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
                await unlock(page,"op"+label[:5].replace(" ",""),False); await page.evaluate(IDFAKE)
                for n,extra in [("Tendinopathie d'Achille",0),("Rhinopharyngite — adulte",0),("Tendinopathie d'Achille",8)]:
                    await page.evaluate(SET,{"n":n,"sx":"h"})
                    if extra: await page.evaluate(f"(()=>{{const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');state.extra[si]=Array.from({{length:{extra}}},(_,i)=>'Ligne de test '+(i+1)+' : 1 comprimé matin et soir pendant 5 jours.');render();}})()")
                    nmed=await page.evaluate("(()=>{const p=currentPack();let n=0;p.s.forEach((sh,si)=>{if(sh.k==='med')resolve(sh,si).forEach(x=>{if(x.on&&!x.jr&&!x.fill.miss.length)n++;});});return n;})()")
                    await page.evaluate("printPack()"); await page.wait_for_timeout(500)
                    if await page.locator("#ciover").count(): await page.click("#ci_keep"); await page.click("#ci_print")
                    await page.wait_for_selector("#print .page",timeout=15000); await page.wait_for_timeout(1200)
                    warn=await page.evaluate("(document.querySelector('#print .fitwarn')||{}).textContent||''")
                    r=await page.evaluate("""async()=>{const d=document.createElement('div');d.innerHTML=PDFJOB.out;const docs=[...d.querySelectorAll('.page')].length;const pages=await pdfRenderPages(PDFJOB.out,null,()=>false);return {docs,p:pages.map(p=>({h:p.title||'',stamp:!!p.zone,ratio:+(p.h/p.w).toFixed(3)}))};}""")
                    suite=[x for x in r["p"] if "(suite)" in x["h"]]
                    ok(f"{label} : « {n} » ordonnance de {nmed} lignes → 1 page A4 par document ({r['docs']}), jamais de suite, cachet entier sur chacun, pas d'alerte de page",len(r["p"])==r["docs"] and not suite and all(x["stamp"] and abs(x["ratio"]-1.414)<0.01 for x in r["p"]) and not warn,(nmed,r,warn[:80]))
                    if "iPhone" not in label:
                        await page.evaluate("window.__pr=0;window.__pdfprint=0;")
                        for _ in range(40):
                            if await page.evaluate("!!PDFJOB.file"): break
                            await page.wait_for_timeout(250)
                        bt=page.locator("#pb_print").first
                        if await bt.count(): await bt.click(); await page.wait_for_timeout(800)
                        pp=await page.evaluate("({pr:window.__pr||0,pdf:window.__pdfprint||0})")
                        ok(f"{label} : « Imprimer » imprime le PDF (jamais la page web)",pp["pr"]==0 and pp["pdf"]>=1,pp)
                    await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel()}catch(e){};document.getElementById('pdfprint')&&document.getElementById('pdfprint').remove();state.view='';render();")
                ok(f"{label} : aucune erreur JS",not errors,errors[:3])
                await ctx.close()
            for dsf in (1,1.25,1.5):
                await onepage(b,f"PC Chrome {int(dsf*100)} %",{"viewport":{"width":1366,"height":768},"device_scale_factor":dsf})
            await b.close()
            try:
                e=await p.chromium.launch(channel="msedge")
                await onepage(e,"PC Edge 125 %",{"viewport":{"width":1366,"height":768},"device_scale_factor":1.25}); await e.close()
            except Exception as ex: ok("PC Edge : navigateur disponible",False,str(ex)[:200])
            w=await p.webkit.launch()
            await onepage(w,"iPhone WebKit",p.devices["iPhone 13"]); await w.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_garde18.md"),"w",encoding="utf-8").write("# Garde du 18/10/2026 — vérifications\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
