# Tests navigateur Packs SOS — prérequis : pip install playwright puis python -m playwright install chromium
import asyncio, os, json, subprocess, time, sys, re

from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,info if not cond else "")

async def unlock(page):
    await page.goto("http://localhost:8765/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testv40"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

async def pick(page,query,name):
    if not await page.locator("#q").is_visible():
        if await page.locator("#new2").count(): await page.click("#new2")
        elif await page.locator("#new").count(): await page.click("#new")
        await page.wait_for_timeout(500)
        if not await page.locator("#q").is_visible():
            await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
    await page.wait_for_selector("#q",state="visible",timeout=10000)
    await page.fill("#q",query); await page.wait_for_timeout(300)
    btn=page.locator("#res button.res",has_text=name).first
    await btn.click(); await page.wait_for_timeout(400)

async def lines(page):
    return await page.evaluate("""()=>[...document.querySelectorAll('.sheet')].map(sh=>({t:sh.querySelector('.hd label').textContent.trim(),lbl:sh.querySelector('.tp').textContent,l:[...sh.querySelectorAll('li')].map(li=>({on:li.querySelector('input').checked,t:li.querySelector('.lt').textContent,jr:!!li.querySelector('.pcd')}))}))""")

async def run(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page()
        errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page)
        v=await page.evaluate("APP_VERSION"); ok(label+" version 40",v=="40",v)
        n=await page.evaluate("PACKS.length"); ok(label+" packs chargés",n>200,n)
        dup=await page.evaluate("(()=>{const m={};PACKS.forEach(p=>m[p.n]=(m[p.n]||0)+1);return Object.keys(m).filter(k=>m[k]>1);})()"); ok(label+" pas de pack en double",len(dup)==0,dup)
        # Cystite : simple par défaut en consultation
        await page.evaluate("state.cot.lieu='consultation';state.risk=undefined;")
        await pick(page,"cystite","Cystite simple — femme")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" cystite simple : MONURIL coché",any("MONURIL" in x["t"] and x["on"] for x in med))
        ok(label+" cystite simple : pas d'OROKEN",not any("OROKEN" in x["t"] for x in med))
        ok(label+" bascule S/R visible",await page.locator(".srtog").count()==1)
        ns=await page.evaluate("document.querySelector('.title .sub').textContent"); ok(label+" cystite simple : 2 feuilles à imprimer (memo non comptée)",ns.startswith("2 "),ns)
        await page.screenshot(path=f"{OUT}/{label}-cystite-simple.png",full_page=True)
        await page.click(".srtog [data-sr=r]"); await page.wait_for_timeout(400)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" cystite à risque : FURADANTINE cochée (HAS), OROKEN en option",any("FURADANTINE" in x["t"] and x["on"] for x in med) and any("OROKEN" in x["t"] and not x["on"] for x in med),[x["t"][:30] for x in med if x["on"]])
        ok(label+" cystite à risque : 6 alternatives radio",sum(1 for x in med if any(k in x["t"] for k in ["OROKEN","FURADANTINE","MONURIL","BACTRIM","CLAMOXYL","SELEXID"]))>=6)
        ok(label+" cystite à risque : ECBU",any("ECBU" in x["t"] for x in [l for s in L if s["lbl"]=="Biologie" for l in s["l"]]))
        await page.screenshot(path=f"{OUT}/{label}-cystite-risque.png",full_page=True)
        # Lombalgie : ligne journal+CR, impression l'exclut, CR l'inclut
        await pick(page,"lombalgie","Lombalgie aiguë")
        await page.evaluate("state.risk=undefined;render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" lombalgie : kétoprofène coché, ibuprofène option",any("BI-PROFÉNID" in x["t"] and x["on"] for x in med) and any("IBUPROFÈNE" in x["t"] and not x["on"] for x in med))
        ok(label+" lombalgie : pas de tramadol",not any("TRAMADOL" in x["t"].upper() for x in med))
        jr=[x for x in med if x["jr"]]; ok(label+" lombalgie : ligne palier 3 journal+CR",len(jr)==1 and "ACTISKENAN" in jr[0]["t"])
        await page.evaluate("state.patient='Test Patient';state.ddn='01/01/1950';")
        # cocher la ligne palier 3
        key=await page.evaluate("""()=>{const li=[...document.querySelectorAll('.sheet li')].find(li=>li.querySelector('.pcd'));return li.dataset.li;}""")
        await page.evaluate(f"""()=>{{const [si,k]={json.dumps(key)}.split('|');state.lo[k]=true;render();}}""")
        await page.wait_for_timeout(300)
        cr=await page.evaluate("buildCR0(currentPack())")
        ok(label+" CR contient le palier 3 avec mention",("ACTISKENAN" in cr) and ("non imprimée" in cr))
        pages=await page.evaluate("buildPages(currentPack(),false)")
        txt=pages if isinstance(pages,str) else json.dumps(pages)
        ok(label+" impression sans le palier 3",("ACTISKENAN" not in txt) and ("BI-PROF" in txt))
        # arrêt de travail et journal
        await page.evaluate("state.at.on=true;state.at.jours='5';state.at.type='initial';state.date=normDate(new Date().toLocaleDateString('fr-FR'));journalUpsert(currentPack());")
        j=await page.evaluate("JOURNAL[JOURNAL.length-1]")
        ok(label+" journal : AT 5 j enregistré",j.get("at",{}).get("j")==5,j.get("at"))
        ok(label+" journal : ligne sécurisée enregistrée",any("ACTISKENAN" in x for x in j.get("notes",[])))
        await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(300)
        jt=await page.inner_text("#main")
        ok(label+" journal affiche AT et ordonnance sécurisée",("Arrêt de travail" in jt and "5 j" in jt) and "ACTISKENAN" in jt)
        await page.screenshot(path=f"{OUT}/{label}-journal.png",full_page=True)
        await page.click("#j_back"); await page.wait_for_timeout(500)
        # Gastro enfant : poids → racécadotril, ondansétron option
        await pick(page,"gastro enfant","Gastro-entérite — enfant")
        await page.evaluate("state.ddn='01/01/2024';state.poids='12';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" gastro enfant : TIORFAN au poids",any("TIORFAN" in x["t"] or "tiorfan" in x["t"].lower() for x in med),[x["t"][:40] for x in med])
        ok(label+" gastro enfant : ZOPHREN 2,5 ml (2 mg) à 12 kg, non coché",any("ZOPHREN" in x["t"] and "2,5 ml (2 mg)" in x["t"] and not x["on"] for x in med),[x["t"][:60] for x in med if "ZOPHREN" in x["t"]])
        ok(label+" gastro enfant : jamais de lopéramide",not any("lopéramide" in x["t"].lower() or "IMODIUM" in x["t"] for x in med))
        await page.screenshot(path=f"{OUT}/{label}-gastro-enfant.png",full_page=True)
        # Angine enfant 20 kg : 5 ml (500 mg)
        await pick(page,"angine","Angine — enfant (TROD positif)")
        await page.evaluate("state.ddn='01/01/2020';state.poids='20';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" angine enfant : CLAMOXYL 5 ml coché",any("CLAMOXYL" in x["t"] and "5 ml" in x["t"] and x["on"] for x in med),[x["t"][:70] for x in med])
        ok(label+" angine enfant : 5 antibiotiques",sum(1 for x in med if any(k in x["t"] for k in ["CLAMOXYL","ORELOX","ZINNAT","ZITHROMAX","ZECLAR"]))==5)
        # Allergie pénicilline → bascule automatique
        await page.evaluate("state.allergie=true;state.gs={};render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" angine enfant allergie : CLAMOXYL écarté",not any("CLAMOXYL" in x["t"] and x["on"] for x in med),[x["t"][:40] for x in med if x["on"]])
        await page.evaluate("state.allergie=false;")
        # Grippe adulte 80 ans en consultation → à risque automatique → TAMIFLU présent
        await pick(page,"grippe","Grippe / syndrome viral — adulte")
        await page.evaluate("state.cot.lieu='consultation';state.ddn='01/01/1945';state.poids='';state.risk=undefined;render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" grippe 80 ans : TAMIFLU (à risque automatique)",any("TAMIFLU" in x["t"] for x in med))
        await page.evaluate("state.ddn='01/01/1990';state.risk=undefined;render();"); await page.wait_for_timeout(200)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" grippe 35 ans consultation : pas de TAMIFLU",not any("TAMIFLU" in x["t"] for x in med))
        await page.evaluate("state.cot.lieu='visite';state.risk=undefined;render();"); await page.wait_for_timeout(200)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" grippe en visite : à risque par défaut",any("TAMIFLU" in x["t"] for x in med))
        await page.screenshot(path=f"{OUT}/{label}-grippe-visite.png",full_page=True)
        # Durée d'arrêt indicative
        await pick(page,"gastro","Gastro-entérite — adulte")
        await page.evaluate("state.cot.lieu='consultation';state.risk=undefined;state.ddn='';state.poids='';render();"); await page.wait_for_timeout(300)
        await page.evaluate("state.ui=state.ui||{};state.ui.open=state.ui.open||{};")
        sugg=await page.evaluate("atDureeSugg('Gastro-entérite — adulte')"); ok(label+" durée AT gastro = 3 (Docteur DEIE)",sugg.startswith("3"),sugg)
        s2=await page.evaluate("atDureeSugg('Entorse de cheville')"); ok(label+" durée AT entorse CNAM",("CNAM" in s2),s2)
        # Vogalène lyoc + suppo en choix
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" gastro adulte : VOGALÈNE LYOC coché, suppositoire en alternative",any("VOGALÈNE LYOC" in x["t"] and x["on"] for x in med) and any("suppositoire sécable" in x["t"] and not x["on"] for x in med))
        ok(label+" gastro adulte simple : pas d'antibiotique",not any("AZITHROMYCINE" in x["t"] for x in med))
        await page.click(".srtog [data-sr=r]"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" gastro adulte à risque : suspension des médicaments + 4 antibiotiques en option (DIFICLIR hospitalier)",any("suspendre le diurétique" in x["t"] for x in med) and sum(1 for x in med if any(k in x["t"] for k in ["AZITHROMYCINE","CIFLOX","BACTRIM","FLAGYL"]))==4)
        await page.screenshot(path=f"{OUT}/{label}-gastro-risque.png",full_page=True)
        # Bloc 2 — ORL et ophtalmologie
        nb2=await page.evaluate("PACKS_V40_B2.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 2 : packs chargés",nb2==len(await page.evaluate("PACKS_V40_B2"))and nb2>=30,nb2)
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"rage de dent","Douleur dentaire — abcès")
        await page.evaluate("state.cot.lieu='consultation';state.risk=undefined;state.ddn='01/01/1985';state.poids='';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" dentaire HAS 2026 : antibiotique décoché, 5 alternatives 3 jours",not any(x["on"] for x in med if "pendant 3 jours" in x["t"]) and sum(1 for x in med if any(k in x["t"] for k in ["CLAMOXYL","ZECLAR","AZITHROMYCINE","PYOSTACINE","FLAGYL"]))==5 and any("BI-PROFÉNID" in x["t"] and x["on"] for x in med),[x["t"][:40] for x in med if x["on"]])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"ethmoïdite","Sinusite aiguë — enfant")
        await page.evaluate("state.ddn='01/01/2019';state.poids='20';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" sinusite enfant 20 kg : CLAMOXYL 8 ml 10 jours coché",any("CLAMOXYL" in x["t"] and "8 ml" in x["t"] and "10 jours" in x["t"] and x["on"] for x in med),[x["t"][:70] for x in med])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"ethmoïdite","Sinusite aiguë — enfant")
        await page.evaluate("state.ddn='01/01/2017';state.poids='30';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" BACTRIM enfant 30 kg : 10 ml par prise au maximum (RCP)",any("BACTRIM 40 mg/ml" in x["t"] and ": 10 ml" in x["t"] for x in med),[x["t"][:90] for x in med if "BACTRIM" in x["t"]])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"yeux collés","Conjonctivite")
        await page.evaluate("state.ddn='01/01/1985';state.poids='';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" conjonctivite : antiseptique coché, antibiotique en alternative",any("VITABACT" in x["t"] and x["on"] for x in med) and any("AZYTER" in x["t"] and not x["on"] for x in med) and not any("corticoïde" in x["t"].lower() and x["on"] for x in med))
        # Bloc 3 — Respiratoire et digestif
        nb3=await page.evaluate("PACKS_V40_B3.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 3 : 30 packs chargés",nb3==len(await page.evaluate("PACKS_V40_B3"))and nb3>=30,nb3)
        bad=await page.evaluate("[...PACKS_V40_B2,...PACKS_V40_B3].flatMap(p=>p.s.flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).filter(t=>(t.match(/{/g)||[]).length!==(t.match(/}/g)||[]).length)")
        ok(label+" blocs 2-3 : gabarits équilibrés",len(bad)==0,bad[:2])
        await page.evaluate("state.sel=null;state.view='';state.cot.lieu='consultation';state.risk=undefined;state.ddn='01/01/1985';state.poids='';render();"); await page.wait_for_timeout(300)
        await pick(page,"crépitants","Pneumopathie aiguë — adulte")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" PAC simple : CLAMOXYL coché, pas d'AUGMENTIN",any("CLAMOXYL" in x["t"] and x["on"] for x in med) and not any("AUGMENTIN" in x["t"] for x in med),[x["t"][:40] for x in med if x["on"]])
        await page.click(".srtog [data-sr=r]"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" PAC à risque : AUGMENTIN coché",any("AUGMENTIN" in x["t"] and x["on"] for x in med),[(x["on"],x["t"][:100]) for x in med])
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;render();"); await page.wait_for_timeout(300)
        await pick(page,"emphysème","Exacerbation de BPCO")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" BPCO : antibiotique décoché par défaut (HAS 2024)",not any(x["on"] for x in med if any(k in x["t"] for k in ["CLAMOXYL","AUGMENTIN","PYOSTACINE","ZECLAR","TAVANIC","BACTRIM"])) and any("VENTOLINE" in x["t"] and x["on"] for x in med))
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"impaction","Fécalome / constipation sévère")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" fécalome : FORTRANS coché (convention), MOVICOL 8 sachets en alternative",any("FORTRANS" in x["t"] and x["on"] for x in med) and any("4 sachets dans 500 ml" in x["t"] and not x["on"] for x in med))
        # Bloc 4 — Uro-néphrologie, et disponibilité des médicaments
        nb4=await page.evaluate("PACKS_V40_B4.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 4 : 13 packs chargés",nb4==13,nb4)
        gone=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10].flatMap(p=>p.s.filter(sh=>sh.k!=='memo').flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).filter(t=>/JOSACINE \d|PÉDIAZOLE|VANCOMYCINE 125 mg gélule|DIFICLIR 200|MOTILIUM 10|NICOPATCH \d|BACTRIM pédiatrique suspension buvable :|VITAMINE A DULCIS/.test(t))")
        ok(label+" fiches : aucun médicament non commercialisé ou hospitalier",len(gone)==0,gone[:2])
        await page.evaluate("state.sel=null;state.view='';state.cot.lieu='consultation';state.risk='r';state.ddn='01/01/1985';state.poids='';render();"); await page.wait_for_timeout(300)
        await pick(page,"frissons","Pyélonéphrite aiguë simple — femme")
        await page.evaluate("state.risk='r';render();"); await page.wait_for_timeout(300)
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" PNA à risque : recommandation cochée (CIFLOX), OROKEN en option",any("CIFLOX" in x["t"] and "10 jours" in x["t"] and x["on"] for x in med) and any("OROKEN" in x["t"] and not x["on"] for x in med),[(x["on"],x["t"][:100]) for x in med])
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;render();"); await page.wait_for_timeout(300)
        await pick(page,"prostatite","Prostatite aiguë")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" prostatite : pas d'OROKEN (RCP), 14 jours",not any("OROKEN" in x["t"] for x in med) and any("14 jours" in x["t"] and x["on"] for x in med))
        dd=await page.evaluate("""()=>{const out=[];const sv=[state.risk,state.ddn,state.poids];for(const pk of [...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10]){for(const rk of ['s','r']){state.risk=rk;state.ddn='01/01/1985';state.poids='70';pk.s.forEach((sh,si)=>{if(sh.k!=='med'&&sh.k!=='dm')return;expand(sh,si);(ADAPT_NOTES[si]||[]).filter(n=>/double/.test(n)).forEach(n=>out.push(pk.n+' : '+n));});}}[state.risk,state.ddn,state.poids]=sv;return [...new Set(out)];}""")
        ok(label+" fiches : aucune ligne effacée par dédoublonnage",len(dd)==0,dd[:3])
        # Bloc 5 — Rhumatologie et traumatologie, champs à saisir
        nb5=await page.evaluate("PACKS_V40_B5.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 5 : 22 packs chargés",nb5==22,nb5)
        nf=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10].filter(p=>{const u=[...JSON.stringify(p.s).matchAll(/\{f:(\w+)\}/g)].map(m=>m[1]);return u.some(k=>!(p.fields||[]).includes(k)||!FIELDS[k]);}).map(p=>p.n)")
        ok(label+" fiches : chaque champ {f:…} a sa case de saisie",len(nf)==0,nf[:3])
        cv=await page.evaluate("atDureeSugg('Cervicalgie / torticolis')"); ok(label+" durée AT cervicalgie CNAM",("CNAM" in cv),cv)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1960';state.poids='';render();"); await page.wait_for_timeout(300)
        await pick(page,"gros orteil","Crise de goutte")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" goutte : colchicine cochée, prednisone en alternative, pas de doublon",any("COLCHICINE" in x["t"] and x["on"] for x in med) and any("CORTANCYL" in x["t"] and not x["on"] for x in med))
        # Bloc 6 — Dermatologie
        nb6=await page.evaluate("PACKS_V40_B6.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 6 : 22 packs chargés",nb6==22,nb6)
        old=await page.evaluate("PACKS.flatMap(p=>p.s.filter(sh=>sh.k!=='memo'&&sh.k!=='interp').flatMap(sh=>sh.l.filter(l=>!(l&&l.jr)).map(l=>typeof l==='string'?l:(l.t||'')))).filter(t=>/FUCIDINE 2 % crème|TRANSVERCID|LAMISIL 250|EMERADE|PRIODERM|JOSACINE \d|PÉDIAZOLE|MOTILIUM 10|BUCCOLAM|ALOPLASTINE|CALMOSINE|MOVICOL enfant/.test(t))")
        ok(label+" tous les packs : aucun produit retiré du marché prescrit",len(old)==0,old[:2])
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1985';state.poids='70';render();"); await page.wait_for_timeout(300)
        await pick(page,"jambe rouge","Érysipèle — dermohypodermite")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" érysipèle 70 kg : amoxicilline 1 g 3 fois par jour, 7 jours",any("CLAMOXYL" in x["t"] and "1000 mg" in x["t"] and "7 jours" in x["t"] and x["on"] for x in med),[x["t"][:80] for x in med if x["on"]])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"sarcopte","Gale — adulte")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" gale 70 kg : ivermectine à jeun, 5 comprimés",any("STROMECTOL" in x["t"] and "à jeun" in x["t"] and "5 comprimés" in x["t"] and x["on"] for x in med),[x["t"][:90] for x in med if "STROMECTOL" in x["t"]])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"érythème migrant","Morsure de tique")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" tique : aucun antibiotique coché par défaut (HAS 2025), doxycycline 10 jours proposée",not any(x["on"] for x in med if "DOXYCYCLINE" in x["t"] or "CLAMOXYL" in x["t"]) and any("DOXYCYCLINE" in x["t"] and "10 jours" in x["t"] for x in med))
        # Bloc 7 — Pédiatrie
        nb7=await page.evaluate("PACKS_V40_B7.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 7 : 16 packs chargés",nb7==16,nb7)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/2023';state.poids='12';render();"); await page.wait_for_timeout(300)
        await pick(page,"toux aboyante","Laryngite aiguë — enfant")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" laryngite 12 kg : prednisolone 1 mg/kg (10 mg) cochée, 3 jours",any("SOLUPRED" in x["t"] and "10 mg" in x["t"] and "3 jours" in x["t"] and x["on"] for x in med),[x["t"][:70] for x in med if x["on"]])
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/2019';state.poids='25';render();"); await page.wait_for_timeout(300)
        await pick(page,"sifflement enfant","Asthme aigu — enfant")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" asthme enfant 25 kg : prednisolone 40 mg 3 jours (SP2A 2024)",any("SOLUPRED" in x["t"] and "40 mg" in x["t"] and x["on"] for x in med),[x["t"][:70] for x in med if "SOLUPRED" in x["t"]])
        # Bloc 8 — Neurologie
        nb8=await page.evaluate("PACKS_V40_B8.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 8 : 15 packs chargés",nb8==15,nb8)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1985';state.poids='80';render();"); await page.wait_for_timeout(300)
        await pick(page,"aura","Migraine")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" migraine : PROFEMIGR coché (AMM crise), pas de forme LP",any("PROFEMIGR" in x["t"] and x["on"] for x in med) and not any("BI-PROFÉNID LP" in x["t"] for x in med),[x["t"][:40] for x in med if x["on"]])
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(300)
        await pick(page,"œil ne ferme plus","Paralysie faciale périphérique")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" paralysie faciale 80 kg : prednisolone plafonnée à 60 mg, 7 jours",any("SOLUPRED" in x["t"] and "60 mg" in x["t"] and "7 jours" in x["t"] and x["on"] for x in med),[x["t"][:70] for x in med if "SOLUPRED" in x["t"]])
        # Bloc 9 — Psychiatrie et addictions
        nb9=await page.evaluate("PACKS_V40_B9.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 9 : 13 packs chargés",nb9==13,nb9)
        sv=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Sevrage alcool ambulatoire — programmé');const m=p.s.find(sh=>sh.k==='med').l.map(l=>typeof l==='string'?{t:l}:l);return [m.some(l=>/^VALIUM 10 mg/.test(l.t)&&!l.opt),m.some(l=>/^BENERVA/.test(l.t)&&!l.opt),PACKS.flatMap(x=>x.s.filter(sh=>sh.k==='med').flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).some(t=>/SERESTA 50/.test(t))];}""")
        ok(label+" bloc 9 : sevrage au diazépam + B1 cochés (SFA 2023), plus de SERESTA 50 mg x3",sv[0] and sv[1] and not sv[2],sv)
        hy=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Insomnie');return p.s.filter(sh=>sh.k==='med').flatMap(sh=>sh.l).filter(l=>/STILNOX|zolpidem/i.test(typeof l==='string'?l:l.t)&&!(typeof l==='object'&&l.jr)).length;}""")
        ok(label+" bloc 9 : zolpidem (ordonnance sécurisée) jamais imprimé",hy==0,hy)
        sc=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Soins psychiatriques sans consentement — certificat');const c=p.s.find(sh=>sh.k==='cert').l;return [c.filter(l=>l.grp==='mode').length,(p.fields||[]).includes('heure')&&(p.fields||[]).includes('constats')&&!!FIELDS.heure&&!!FIELDS.constats];}""")
        ok(label+" bloc 9 : certificat sans consentement, 3 mentions exclusives, heure et constatations à saisir",sc[0]==3 and sc[1],sc)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1940';state.poids='70';render();"); await page.wait_for_timeout(300)
        await pick(page,"tristesse","Dépression — bilan et prise en charge initiale")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        es=[x["t"] for x in med if x["t"].startswith("ESCITALOPRAM")]; ci=[x["t"] for x in med if x["t"].startswith("CITALOPRAM")]
        ok(label+" bloc 9 : dépression après 65 ans, escitalopram 5 mg (10 mg max) et citalopram 20 mg max (RCP)",bool(es) and "5 mg" in es[0] and "10 mg par jour au maximum" in es[0] and bool(ci) and "20 mg par jour au maximum" in ci[0] and "40 mg" not in ci[0],es+ci)
        await page.evaluate("state.ddn='01/01/1985';render();")
        # Bloc 10 — Cardio-vasculaire
        nb10=await page.evaluate("PACKS_V40_B10.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 10 : 13 packs chargés",nb10==13,nb10)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1950';state.poids='70';render();"); await page.wait_for_timeout(300)
        await pick(page,"pouls irrégulier","Fibrillation atriale — découverte ou récidive")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" bloc 10 : FA, apixaban 5 et 2,5 mg et rivaroxaban affichés (aucun effacé en doublon), rien coché d'office",sum(1 for x in med if x["t"].startswith("ELIQUIS"))==2 and any(x["t"].startswith("XARELTO") for x in med) and not any(x["on"] for x in med if x["t"].startswith(("ELIQUIS","XARELTO"))),[x["t"][:30] for x in med])
        tv=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Phlébite / thrombose veineuse profonde');const m=p.s.find(sh=>sh.k==='med').l.filter(l=>l.grp==='ac');const t=PACKS.find(x=>x.n==='Thrombose veineuse superficielle (paraphlébite)').s.find(sh=>sh.k==='med').l.map(l=>typeof l==='string'?l:l.t).join(' ');return [m.length,m.filter(l=>!l.opt).length,/ARIXTRA 2,5 mg/.test(t)&&/45 jours/.test(t),!!FIELDS.hbpm&&(p.fields||[]).includes('hbpm')];}""")
        ok(label+" bloc 10 : TVP 3 anticoagulants exclusifs (apixaban par défaut, rivaroxaban, HBPM au poids à saisir), TVS fondaparinux 45 j",tv[0]==3 and tv[1]==1 and tv[2] and tv[3],tv)
        ht=await page.evaluate("""()=>PACKS.find(x=>x.n==='Poussée tensionnelle — HTA sévère sans urgence').s.filter(sh=>sh.k==='med').flatMap(sh=>sh.l).map(l=>typeof l==='string'?{t:l}:l)""")
        ok(label+" bloc 10 : poussée tensionnelle sans nifédipine, amlodipine décochée",not any("ADALATE" in l["t"] or "nifédipine" in l["t"].lower() for l in ht) and any(l["t"].startswith("AMLODIPINE") and l.get("opt") for l in ht),ht)
        await page.evaluate("state.ddn='01/01/1985';render();")
        # Cahier des corrections — points 7 et 8 (risque médical)
        r7=await page.evaluate("""()=>{const out={};for(const n of ['Lombosciatique aiguë','Colique néphrétique','Diarrhée du voyageur / diarrhée sous antibiotique','Brûlure oculaire — projection de caustique']){const i=PACKS.findIndex(p=>p.n===n);state.sel=i;state.obs={};state.cst={};out[n]=buildCR0(PACKS[i]);}return out;}""")
        ok(label+" correctif 7 : aucun pack n'injecte « tique » ou une histoire d'un autre motif",not any(re.search(r"(?<![a-zàâäéèêëïîôöùûüç])tique",v.lower()) or "Tique retirée" in v for v in r7.values()),[k for k,v in r7.items() if re.search(r"(?<![a-zàâäéèêëïîôöùûüç])tique",v.lower())])
        cp=await page.evaluate("""()=>{const i=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.sel=i;state.obs={atcd:'Asthme sévère'};state.tt=['KARDEGIC'];state.grossesse=true;const cr=withExtra({patient:'Co Patient',packName:'Lombalgie aiguë'},p=>buildCR0(p));const back=state.obs.atcd;state.obs={};state.tt=[];state.grossesse=false;return [cr,back];}""")
        ok(label+" correctif 7 : le co-patient n'hérite pas des antécédents, traitements ni de la grossesse",("Asthme" not in cp[0]) and ("KARDEGIC" not in cp[0]) and ("Grossesse" not in cp[0]) and cp[1]=="Asthme sévère")
        r8=await page.evaluate("""()=>{const i=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.sel=i;state.obs={};state.cst={};const a=buildCR0(PACKS[i]);SYSTEMS.forEach(([k,,n])=>{if(state.obs[k]===undefined)state.obs[k]=n;});const b=buildCR0(PACKS[i]);state.obs={};return [a,b];}""")
        ok(label+" correctif 8 : sans validation, aucun examen, évolution ni accord présentés comme faits",("non renseigné" in r8[0]) and not any(x in r8[0] for x in ["Examen clinique normal","Reste de l'examen normal","État stable","accord obtenu","EXAMEN CLINIQUE"]),r8[0][:300])
        ok(label+" correctif 8 : après validation explicite « Normal », l'examen figure au compte rendu",("EXAMEN CLINIQUE" in r8[1]) and ("sans anomalie sur les appareils examinés" in r8[1]))
        # Cahier des corrections — points 1, 4 et 6
        await page.evaluate("""()=>{TOUR.stops=TOUR.stops.filter(x=>x.id!=='t_cahier');TOUR.stops.push({id:'t_cahier',addr:'12 rue de Bourgogne, 45000 Orléans',label:'12 Rue de Bourgogne 45000 Orléans',city:'Orléans',nom:'DUPONT Jean',ddn:'01/01/1950',tel:'0612345678',motif:'lombalgie',lat:47.9,lon:1.9,km:1.2,ts:Date.now()});state.sel=PACKS.findIndex(p=>p.n==='Angine — adulte (TROD positif)');state.patient='ANCIEN Patient';state.obs={atcd:'Antécédent du patient précédent'};render();}""")
        await page.wait_for_timeout(300)
        await page.evaluate("tourUse('t_cahier')"); await page.wait_for_timeout(500)
        r1=await page.evaluate("({p:state.patient,ddn:state.ddn,sel:state.sel,atcd:(state.obs||{}).atcd||'',hist:(state.obs||{}).hist||'',tel:state.nh.tel,adr:state.nh.adresse,stash:VALID.hist.some(v=>v.patient==='ANCIEN Patient'),cur:TOUR.current})")
        ok(label+" correctif 1 : « Commencer » ouvre un dossier propre prérempli (nom, naissance, motif, téléphone, adresse) et met de côté le patient précédent",r1["p"]=="DUPONT Jean" and r1["ddn"]=="01/01/1950" and r1["sel"] is None and r1["atcd"]=="" and "lombalgie" in r1["hist"] and r1["tel"]=="0612345678" and "Bourgogne" in r1["adr"] and r1["stash"] and r1["cur"]=="t_cahier",r1)
        r4=await page.evaluate("""()=>{const a=[...document.querySelectorAll('a[href^="tel:0612345678"]')];return {n:a.length,outside:a.some(x=>!x.closest('details')),visible:a.some(x=>!x.closest('details')&&x.getBoundingClientRect().width>0)};}""")
        ok(label+" correctif 4 : bouton d'appel visible hors menu replié",r4["outside"] and r4["visible"],r4)
        r6=await page.evaluate("({n:stopName(tourStop('t_cahier')),card:(document.querySelector('.tcard .tc-name')||{}).textContent||''})")
        ok(label+" correctif 6 : libellé initiale · âge · rue",r6["n"].startswith("D. · ") and " ans · " in r6["n"] and r6["n"].endswith("Rue de Bourgogne") and r6["n"] in r6["card"],r6)
        await page.evaluate("()=>{TOUR.stops=TOUR.stops.filter(x=>x.id!=='t_cahier');TOUR.current='';tourSave();newPatient();}")
        # Cahier des corrections — point 3
        r3=await page.evaluate("""()=>{const v=new Date(2026,9,14,20,5).getTime(),a=new Date(2026,9,14,19,50).getTime();const avec=cotCompute({ts:v,tActe:a,lieu:'visite',extra:[],minus:[]}).codes.map(x=>x.c);const sans=cotCompute({ts:v,lieu:'visite',extra:[],minus:[]}).codes.map(x=>x.c);
          state.patient='HEURE Test';state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.cot.lieu='visite';state.cot.h='07:55';state.cot.hArr='07:50';journalUpsert(currentPack());const e=JOURNAL[JOURNAL.length-1];const t=new Date(e.tActe),ar=new Date(e.tArr);const r={avec,sans,acte:t.getHours()+':'+t.getMinutes(),arr:ar.getHours()+':'+ar.getMinutes(),ts:!!e.ts};JOURNAL.pop();journalSave();state.cot.h='';state.cot.hArr='';state.patient='';return r;}""")
        ok(label+" correctif 3 : la cotation suit l'heure de l'acte (19:50 = VG+U, pas VRN), arrivée et acte enregistrés",r3["avec"]==["VG","U"] and "VRN" in r3["sans"] and r3["acte"]=="7:55" and r3["arr"]=="7:50" and r3["ts"],r3)
        # Cahier des corrections — point 9 (itinéraires simulés, sans réseau)
        r9=await page.evaluate("""async()=>{const save={stops:TOUR.stops,order:TOUR.order,legs:TOUR.legs,dest:TOUR.dest,base:TOUR.base,cur:TOUR.current,origin:TOUR.origin};const oT=window.osrmTable,oP=window.osrmTrip;const calls=[];
          window.osrmTable=async(c,arr)=>({km:arr.map(()=>2),min:arr.map(()=>5)});window.osrmTrip=async(pts,hasDest)=>{calls.push({n:pts.length,hasDest:!!hasDest,last:pts[pts.length-1]});const inner=pts.map((p,i)=>i).filter(i=>i>0&&!(hasDest&&i===pts.length-1));return {order:inner,legs:pts.slice(1).map(()=>({km:1,min:4})),km:pts.length,min:pts.length*4};};
          TOUR.base={lat:47.90,lon:1.90};TOUR.origin='cabinet';TOUR.current='';TOUR.dest='cabinet';
          TOUR.stops=[{id:'a',addr:'A',lat:47.91,lon:1.91},{id:'b',addr:'B',lat:47.92,lon:1.92,avant:'23:59'},{id:'c',addr:'C',lat:47.93,lon:1.93,prio:true},{id:'d',addr:'D',lat:47.94,lon:1.94},{id:'e',addr:'E',lat:47.95,lon:1.95}];
          try{await tourOptimize();}finally{window.osrmTable=oT;window.osrmTrip=oP;}
          const r={order:TOUR.order.slice(),calls,eta:!!tourStop('a').eta,late:!!tourStop('b').late};Object.assign(TOUR,{stops:save.stops,order:save.order,legs:save.legs,dest:save.dest,base:save.base,current:save.cur,origin:save.origin});tourSave();return r;}""")
        ok(label+" correctif 9 : prioritaire, puis créneau horaire, puis les autres ; arrivée imposée en fin de tournée ; heure estimée",r9["order"][:2]==["c","b"] and set(r9["order"][2:])=={"a","d","e"} and any(c["hasDest"] and abs(c["last"]["lat"]-47.90)<1e-9 for c in r9["calls"]) and r9["eta"] and not r9["late"],r9)
        # Cahier des corrections — point 10
        r10=await page.evaluate("""()=>{const pg=t=>`<div class="page"><div class="frame"><h2>${t}</h2><p>x</p></div></div>`;const html=[pg('Ordonnance'),pg('Certificat médical'),pg('Courrier'),pg('Ordonnance'),pg('Consignes'),pg('Consignes')].join('');
          const was=PRINT2UP;PRINT2UP=true;const out=print2up(html);PRINT2UP=was;const b=document.createElement('div');b.innerHTML=out;const top=[...b.children];
          return {n:top.length,sheets:top.filter(x=>x.classList.contains('sheet2')).map(x=>[...x.children].map(c=>c.querySelector('h2').textContent)),ordoInSheet:top.some(x=>x.classList.contains('sheet2')&&x.textContent.includes('Ordonnance')),off:sheetCount(html),pref:lsGet('sos_2up',false)};}""")
        ok(label+" correctif 10 : 2 documents par A4 en option (désactivée par défaut), jamais pour une ordonnance",r10["n"]==4 and r10["off"]==6 and r10["sheets"]==[["Certificat médical","Courrier"],["Consignes","Consignes"]] and not r10["ordoInSheet"] and r10["pref"] is False,r10)
        r10b=await page.evaluate("""()=>{const mk=(t,n)=>`<div class="page"><div class="frame"><h2>${t}</h2>${'<p>Ligne de consigne courte.</p>'.repeat(n)}</div></div>`;const run=html=>{const box=document.createElement('div');box.style.cssText='position:absolute;left:-3000px;top:0';box.innerHTML=print2up(html);document.body.appendChild(box);unpairOverflow(box);const r=[...box.children].map(x=>x.classList.contains('sheet2')?'double':'simple');box.remove();return r;};
          return {court:run(mk('Consignes',3)+mk('Certificat médical',3)),long:run(mk('Consignes',3)+mk('Courrier',80))};}""")
        ok(label+" correctif 10 : documents courts regroupés, document trop long remis en pleine page (jamais tronqué)",r10b["court"]==["double"] and r10b["long"]==["simple","simple"],r10b)
        # Mode nuit + grand texte
        await ctx.close()
        ctx2=await b.new_context(viewport={"width":width,"height":height},color_scheme="dark",device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        page=await ctx2.new_page(); page.on("pageerror",lambda e:errors.append(str(e)))
        await unlock(page)
        await page.evaluate("document.documentElement.style.fontSize='20px'")
        await pick(page,"bronchiolite","Bronchiolite — nourrisson")
        await page.screenshot(path=f"{OUT}/{label}-nuit-bronchiolite.png",full_page=True)
        L=await lines(page); ok(label+" bronchiolite nuit : feuilles rendues",len(L)>=3,[x["lbl"] for x in L])
        ok(label+" aucune erreur JS",len(errors)==0,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8765"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,812,"iphone")
        await run(1280,900,"pc")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats.md"),"w").write("# Tests v40 (lot 1, blocs 2 à 8)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
asyncio.run(main())
