# Tests navigateur Packs SOS — prérequis : pip install playwright puis python -m playwright install chromium
import asyncio, os, json, subprocess, time, sys, re

from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,info if not cond else "")

async def unlock(page):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fiches_fictives as FF
async def run(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page()
        errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page)
        v=await page.evaluate("APP_VERSION"); ok(label+" version 41",v=="41",v)
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
        gone=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10,...PACKS_V40_B11,...PACKS_V40_B12,...PACKS_V40_B13,...PACKS_V40_B14,...PACKS_V40_B15].flatMap(p=>p.s.filter(sh=>sh.k!=='memo').flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).filter(t=>/JOSACINE \d|PÉDIAZOLE|VANCOMYCINE 125 mg gélule|DIFICLIR 200|MOTILIUM 10|NICOPATCH \d|BACTRIM pédiatrique suspension buvable :|VITAMINE A DULCIS/.test(t))")
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
        dd=await page.evaluate("""()=>{const out=[];const sv=[state.risk,state.ddn,state.poids];for(const pk of [...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10,...PACKS_V40_B11,...PACKS_V40_B12,...PACKS_V40_B13,...PACKS_V40_B14,...PACKS_V40_B15]){for(const rk of ['s','r']){state.risk=rk;state.ddn='01/01/1985';state.poids='70';pk.s.forEach((sh,si)=>{if(sh.k!=='med'&&sh.k!=='dm')return;expand(sh,si);(ADAPT_NOTES[si]||[]).filter(n=>/double/.test(n)).forEach(n=>out.push(pk.n+' : '+n));});}}[state.risk,state.ddn,state.poids]=sv;return [...new Set(out)];}""")
        ok(label+" fiches : aucune ligne effacée par dédoublonnage",len(dd)==0,dd[:3])
        # Bloc 5 — Rhumatologie et traumatologie, champs à saisir
        nb5=await page.evaluate("PACKS_V40_B5.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 5 : 22 packs chargés",nb5==22,nb5)
        nf=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5,...PACKS_V40_B6,...PACKS_V40_B7,...PACKS_V40_B8,...PACKS_V40_B9,...PACKS_V40_B10,...PACKS_V40_B11,...PACKS_V40_B12,...PACKS_V40_B13,...PACKS_V40_B14,...PACKS_V40_B15].filter(p=>{const u=[...JSON.stringify(p.s).matchAll(/\{f:(\w+)\}/g)].map(m=>m[1]);return u.some(k=>!(p.fields||[]).includes(k)||!FIELDS[k]);}).map(p=>p.n)")
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
        # Bloc 11 — Gynécologie-obstétrique
        nb11=await page.evaluate("PACKS_V40_B11.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 11 : 13 packs chargés",nb11==13,nb11)
        iu=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Infection urinaire de la femme enceinte');const m=p.s.find(sh=>sh.k==='med').l.filter(l=>l.grp==='atb');return [m.length,!m[0].opt&&/^MONURIL 3 g/.test(m[0].t),m.filter(l=>!l.opt).length,m.some(l=>/^OROKEN/.test(l.t)&&l.opt),p.s.find(sh=>sh.k==='bio').l.some(l=>/8 à 10 jours/.test(typeof l==='string'?l:l.t))];}""")
        ok(label+" bloc 11 : cystite gravidique, fosfomycine cochée (HAS 2025), OROKEN en option, ECBU de contrôle",iu[0]==5 and iu[1] and iu[2]==1 and iu[3] and iu[4],iu)
        ig=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Salpingite — infection génitale haute');const t=p.s.find(sh=>sh.k==='med').l.map(l=>typeof l==='string'?l:l.t).join(' | ');return [/ROCÉPHINE 1 g/.test(t),/DOXYCYCLINE 100 mg[^|]*10 jours/.test(t),/MÉTRONIDAZOLE 500 mg[^|]*10 jours/.test(t)];}""")
        ok(label+" bloc 11 : infection génitale haute, ceftriaxone + doxycycline + métronidazole 10 jours (HAS 2024)",all(ig),ig)
        nv=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Nausées et vomissements de la grossesse');const m=p.s.find(sh=>sh.k==='med').l.filter(l=>l.grp==='ae');return [m.length,/^CARIBAN/.test(m[0].t)&&!m[0].opt,m.some(l=>/ONDANSÉTRON/.test(l.t)&&l.opt&&/hors AMM/.test(l.t)&&!/hors AMM/.test(printClean(l.t)))];}""")
        ok(label+" bloc 11 : nausées de la grossesse, doxylamine-pyridoxine d'abord, ondansétron en option (hors AMM non imprimé)",nv[0]==3 and nv[1] and nv[2],nv)
        # Fiches de régulation : mention « adresse repositionnée / modifiée par » ignorée (texte fictif)
        fr=await page.evaluate(r"""()=>{const T=[
 "INFORMATIONS PATIENT\nMARTIN PAUL\nNé(e) le 03/04/1990 - 36 A\nTél patient Tél appelant\n06 11 22 33 44 06 11 22 33 44\nINTERVENTION\n15/10/2026 19:51 1h40m\nGARDE A VUE\nATTENTION, ADRESSE REPOSITIONNEE PAR\nDURAND ALAIN LE 01/02/2025 10:11:12\nOPJ EXEMPLE\nPOLICE\nADRESSE PATIENT\n12 RUE DES LILAS,\n45000, ORLÉANS",
 "MARTIN PAUL\nNé(e) le 03/04/1990\n06 11 22 33 44\nADRESSE PATIENT\n12 RUE DES LILAS,\n45000, ORLÉANS\nDOULEUR ABDO\nADRESSE MODIFIÉE PAR\nDURAND ALAIN\nLE 01/02/2025 10:11:12",
 "MARTIN PAUL\nNé(e) le 03/04/1990\nADRESSE : 12 RUE DES LILAS 45000 ORLEANS\nTOUX\nAdresse repositionné par DURAND le 01/02/2025"];
 return T.map(t=>{const r=parseFiche(t);return {addr:r.addr,motif:r.motif,note:r.note};});}""")
        ok(label+" fiches : « repositionnée / repositionné / modifiée par » ignorés, adresse réelle (rue, code postal, commune) et auteur jamais repris",all(("12 RUE DES LILAS" in x["addr"] and "45000" in x["addr"] and "PAR" not in x["addr"].upper().split() and "DURAND" not in (x["addr"]+x["note"]).upper()) for x in fr) and fr[0]["motif"]=="GARDE A VUE",fr)
        # Tournée — point 0 et planification (OSRM simulé)
        TSET="""()=>{window.__oT=window.osrmTable;window.__oP=window.osrmTrip;window.osrmTable=async(c,arr)=>({km:arr.map(()=>2),min:arr.map(()=>5)});window.osrmTrip=async(pts,hasDest)=>{const inner=pts.map((p,i)=>i).filter(i=>i>0&&!(hasDest&&i===pts.length-1));return {order:inner,legs:pts.slice(1).map(()=>({km:1,min:4})),km:pts.length,min:pts.length*4};};
          window.__tsave=JSON.stringify({stops:TOUR.stops,order:TOUR.order,legs:TOUR.legs,cur:TOUR.current,cfg:TOUR.cfg,dest:TOUR.dest,base:TOUR.base,origin:TOUR.origin});
          TOUR.base={lat:47.9029,lon:1.9093,label:"cabinet"};TOUR.origin="cabinet";TOUR.dest="";TOUR.current="";TOUR.order=[];TOUR.legs=[];TOUR.total=null;TOUR.computed=0;TOUR.cfg=null;TOUR.destLeg=null;TOUR.est=false;
          TOUR.stops=[{id:"r1",addr:"x",nom:"DUPONT Jean",ddn:"01/01/1946",motif:"fièvre toux",tel:"0612345678",lat:47.90,lon:1.91,label:"10 Rue de Bourgogne 45000 Orléans",city:"Orléans",done:false,ts:Date.now()},
           {id:"r2",addr:"y",nom:"MARTIN Léa",ddn:"02/02/2022",motif:"otite",tel:"0611111111",lat:47.902,lon:1.905,label:"5 Rue Jeanne d'Arc 45000 Orléans",city:"Orléans",done:false,ts:Date.now()-3*3600000},
           {id:"r3",addr:"z",nom:"LEROY Paul",ddn:"03/03/1976",motif:"lombalgie",tel:"0622222222",lat:47.99,lon:1.80,label:"3 Avenue de Paris 45000 Orléans",city:"Orléans",done:false,ts:Date.now()}];
          state.patient="ANCIEN Patient";state.sel=null;state.view="";state.cot=cotDefault();render();}"""
        TRESET="""()=>{window.osrmTable=window.__oT;window.osrmTrip=window.__oP;const s=JSON.parse(window.__tsave);TOUR.stops=s.stops;TOUR.order=s.order;TOUR.legs=s.legs;TOUR.current=s.cur;TOUR.cfg=s.cfg;TOUR.dest=s.dest;TOUR.base=s.base;TOUR.origin=s.origin;TOUR.near="";state.patient="";state.sel=null;state.view="";state.cot=cotDefault();tpGeoStop();render();}"""
        for where in (["main","tour"] if width<500 else ["tour"]):
            await page.evaluate(TSET)
            if where=="tour": await page.evaluate("state.view='tour';render();")
            await page.wait_for_timeout(200)
            await page.locator("#tc_begin" if where=="main" else "#tr_begin").first.click()
            await page.wait_for_timeout(900)
            r0=await page.evaluate("""()=>{const c=document.querySelector('.tcard');const r=c&&c.getBoundingClientRect();const nav=c&&[...c.querySelectorAll('a')].find(x=>/Naviguer/.test(x.textContent));return {cur:TOUR.current,p:state.patient,ddn:state.ddn,tel:(state.nh||{}).tel,adr:(state.nh||{}).adresse,hist:(state.obs||{}).hist,inView:!!(r&&r.top>=-5&&r.top<innerHeight*0.6),nav:!!nav,help:!!document.querySelector('.tc-help')||true};}""")
            ok(label+f" tournée point 0 ({where}) : « Commencer » ouvre le 1er patient prérempli et montre son adresse avec « Naviguer »",r0["cur"]=="r1" and r0["p"]=="DUPONT Jean" and r0["ddn"]=="01/01/1946" and r0["tel"]=="0612345678" and "Bourgogne" in (r0["adr"] or "") and "fièvre" in (r0["hist"] or "") and r0["inView"] and r0["nav"],r0)
            await page.evaluate(TRESET)
        await page.evaluate(TSET)
        hp=await page.evaluate("()=>{state.view='tour';render();const t=document.body.innerText;state.view='';render();return /Calcule l'ordre des visites, ouvre le premier patient/.test(t);}")
        ok(label+" tournée point 0 : phrase d'aide sous « Commencer la tournée »",hp)
        r1=await page.evaluate("""async()=>{await tourOptimize();const d=new Date(Date.now()+6*3600000);TOUR.cfg=null;tpCfg().fin=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');const ok1=tpPlan();const b1=tpBannerHTML();
           const d2=new Date(Date.now()+25*60000);tpCfg().fin=String(d2.getHours()).padStart(2,'0')+':'+String(d2.getMinutes()).padStart(2,'0');const ko=tpPlan();const hb=tpHandBack().map(s=>s.id);const b2=tpBannerHTML();
           return {ok1:ok1.ok,b1:/(Arrivée|Fin de tournée) prévue .* ✓/.test(b1)&&/Il te reste \d+ min par visite/.test(b1),ko:ko.ok,b2:/tp-alert/.test(b2)&&/⚠ (Arrivée|Fin de tournée) prévue/.test(b2),hb,wait:/attend depuis/.test(b2)};}""")
        ok(label+" tournée point 1 : arrivée prévue ✓ ou ⚠, rythme à tenir, alerte vive et visites à rendre (la plus éloignée d'abord)",r1["ok1"] and r1["b1"] and r1["ko"] is False and r1["b2"] and r1["hb"] and r1["hb"][0]=="r3",r1)
        ok(label+" tournée point 4 : patient en attente depuis plus de 2 h signalé",r1["wait"],r1)
        r2=await page.evaluate("""()=>{const save=JOURNAL.slice();const now=Date.now();JOURNAL.length=0;for(let i=0;i<3;i++)JOURNAL.push({id:'t'+i,ts:now-86400000*(i+1),tArr:now-86400000*(i+1)-40*60000,tFin:now-86400000*(i+1),lieu:'visite',pack:'Lombalgie aiguë',patient:'X'});
           const l=tpLearned('lombalgie');const d=tpLearned('otite');JOURNAL.length=0;save.forEach(x=>JOURNAL.push(x));return {l:Math.round(l.min),d:d.min};}""")
        ok(label+" tournée point 2 : durée apprise par motif sur le journal (40 min), 20 min par défaut",r2["l"]==40 and r2["d"]==20,r2)
        r3=await page.evaluate("""()=>({imp:tpImpact({lat:47.905,lon:1.92,label:'test'}),ex:tpExtra({acces:{etage:true,ehpad:true}}),auto:tpExtra({note:'4e étage sans ascenseur, digicode 1234'}),pk:Math.round(tpLegMin(10,new Date(2026,9,12,8,0).getTime())),npk:Math.round(tpLegMin(10,new Date(2026,9,12,14,0).getTime()))})""")
        ok(label+" tournée points 3, 5, 6 : impact avant ajout, minutes d'accès (cochées ou lues dans la fiche), majoration en heure de pointe",r3["imp"].startswith("Impact : +") and "arrivée" in r3["imp"] and r3["ex"]==15 and r3["auto"]==7 and r3["pk"]==12 and r3["npk"]==10,r3)
        r7=await page.evaluate("""()=>{const d=new Date(Date.now()+20*60000);tpCfg().fin=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');TOUR.dest='cabinet';const fm=tpFinMode();const nx=tourNextStop();return {fm,nx:nx&&nx.id,far:tpOnWay(tourStop('r3'))};}""")
        ok(label+" tournée point 7 : mode fin de garde, seules les visites sur le chemin du retour sont proposées",r7["fm"] and r7["nx"]!="r3" and r7["far"] is False,r7)
        r11=await page.evaluate("""async()=>{TOUR.dest='';tpCfg().fin='';tourUse('r1');render();await new Promise(r=>setTimeout(r,100));const btn=document.getElementById('tc_arrive');const big=btn&&btn.getBoundingClientRect().height>=50;btn&&btn.click();await new Promise(r=>setTimeout(r,100));const s=tourStop('r1');
           const res={big,tArr:!!s.tArr,hArr:state.cot.hArr===fmtHM(s.tArr),chrono:!!document.getElementById('tc_chrono'),onsite:/sur place/.test(document.querySelector('.tcard').innerText),dict:!!document.getElementById('tc_dict')};
           s.tArr=Date.now()-25*60000;state.patient='TEST Tournée';patientValidate();res.dur=tourStop('r1').dur;state.view='';return res;}""")
        ok(label+" tournée point 11 : « Je suis arrivé » (grand bouton) enregistre l'arrivée = heure de l'acte, chrono, « sur place », dictée ; durée réelle à la validation",r11["big"] and r11["tArr"] and r11["hArr"] and r11["chrono"] and r11["onsite"] and r11["dict"] and r11["dur"]==25,r11)
        r10=await page.evaluate("""async()=>{tourUse('r2');render();await new Promise(r=>setTimeout(r,100));const t=document.querySelector('.tcard');const a=t.querySelector('[data-tpcall]');const m=t.querySelector('[data-tpmask]');const memo=t.querySelector('.tp-memo');a&&a.addEventListener('click',e=>e.preventDefault(),{once:true});a&&a.click();const s=tourStop('r2');
           return {call:!!a,mask:!!m,memo:!!memo&&!memo.open&&/Annoncer l'arrivée vers/.test(memo.textContent),log:(s.calls||[]).length===1&&!!s.calls[0].annonce,sms:!/sms:/i.test(t.innerHTML)};}""")
        ok(label+" tournée point 10 : appel (et masqué), mémo fixe replié, heure d'appel et heure annoncée enregistrées, aucun SMS",all(r10.values()),r10)
        r8=await page.evaluate("""()=>{state.view='drive';render();const d=document.querySelector('.drive');const fs=d?parseFloat(getComputedStyle(d.querySelector('.dv-addr')).fontSize):0;const txt=d?d.innerText:'';state.view='tour';render();const bil=/Bilan de garde/.test(document.body.innerText)&&/Visites faites/.test(document.querySelector('.tp-bilan').textContent);state.view='';render();return {fs,fin:/Fin prévue/.test(txt),bil};}""")
        ok(label+" tournée points 8 et 9 : écran conduite adresse adaptative ≥ 22 px (registre n° 12), bilan de garde",r8["fs"]>=22 and r8["fin"] and r8["bil"],r8)
        r12=await page.evaluate("""async()=>{window.osrmTable=async()=>{throw new Error('réseau');};TOUR.computed=0;await tourOptimize();const b=tpBannerHTML();return {est:TOUR.est,order:TOUR.order.length,txt:/vol d'oiseau/.test(b)};}""")
        ok(label+" tournée point 12 : itinéraire indisponible, estimation à vol d'oiseau majorée et signalée",r12["est"] and r12["order"]>=1 and r12["txt"],r12)
        if width<500:
            bad=[]
            for th,big in [("day",False),("night",False),("day",True),("night",True)]:
                await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.removeItem('sos_theme_force');localStorage.setItem('sos_bigtext','{1 if big else 0}');themeApply();")
                for v in ["", "tour", "drive"]:
                    await page.evaluate(f"(()=>{{const d=new Date(Date.now()+15*60000);tpCfg().fin=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');state.view='{v}';render();}})()"); await page.wait_for_timeout(150)
                    r=await page.evaluate("()=>{const W=document.documentElement.clientWidth;const over=[...document.querySelectorAll('.tp-banner,.tcard,.drive,.tp-arrive,.dv-b,.tp-call a')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&(r.right>W+1||r.left<-1);}).length;return [over,document.documentElement.scrollWidth<=W,!!document.querySelector('.tp-banner,.drive')];}")
                    if r[0] or not r[1] or not r[2]: bad.append((th,big,v,r))
            await page.evaluate("localStorage.setItem('sos_theme','auto');localStorage.setItem('sos_bigtext','0');themeApply();")
            ok(label+" tournée 375 px : bandeau, carte, écran conduite sans débordement (jour, nuit, grand texte)",not bad,bad)
        await page.evaluate(TRESET)
        # Courriers assemblés sans IA : spécialiste / urgences et médecin traitant
        await page.evaluate("state.sel=null;state.view='';state.lettres={};state.patient='';render();"); await page.wait_for_timeout(200)
        await pick(page,"angine","Angine")
        lt=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));state.lettres={};state.patient='TEST Courrier';state.ddn='01/01/1980';state.sexe='f';state.allergies=['pénicillines'];state.tt=['LEVOTHYROX 75 µg'];state.obs=Object.assign(state.obs||{},{atcd:'',hyp:'',orl:'Amygdales érythémato-pultacées'});state.cst={temp:'38,9'};state.at=Object.assign({},state.at,{on:false});render();await w(100);
          const bs=document.querySelector('[data-leton="sp"]'),bm=document.querySelector('[data-leton="mt"]');if(!bs||!bm)return {btn:false};bs.click();await w(100);document.querySelector('[data-leton="mt"]').click();await w(100);
          const ds=document.getElementById('let_dest');ds.value='cardiologue';ds.dispatchEvent(new Event('change'));await w(100);
          const sp=letText(currentPack(),'sp'),mt=letText(currentPack(),'mt');
          const ta=document.querySelector('[data-letta="mt"]');ta.value=ta.value.replace('Cher confrère','Chère consœur, cher confrère (modifié)');ta.dispatchEvent(new Event('input'));
          await printPack();await w(1200);const pages=[...document.querySelectorAll('#print .page.lettre')];const txt=pages.map(x=>x.innerText).join(' || ');const fit=pages.every(x=>{const f=x.querySelector('.frame');return f.scrollHeight<=f.clientHeight+2;});
          document.body.classList.remove('printing');document.getElementById('print').innerHTML='';
          return {btn:true,sp,mt,n:pages.length,fit,edited:/\(modifié\)/.test(txt),bold:pages.some(x=>x.querySelector('b')&&/pénicillines/.test(x.querySelector('b').textContent+[...x.querySelectorAll('b')].map(b=>b.textContent).join(' '))),W:document.documentElement.scrollWidth<=document.documentElement.clientWidth};}""")
        ok(label+" courriers : deux boutons sur le pack, courrier au cardiologue en questions, sobre, une phrase de rendez-vous, données saisies seulement",lt.get("btn") and "À l'attention du cardiologue." in lt["sp"] and lt["sp"].count(" ?")>=2 and lt["sp"].count("rendez-vous")==1 and "Je vous laisse juge des explorations" in lt["sp"] and "LEVOTHYROX" in lt["sp"] and "Allergies : pénicillines" in lt["sp"] and "Antécédents" not in lt["sp"] and "Diagnostic" not in lt["sp"],lt.get("sp"))
        ok(label+" courriers : médecin traitant, compte rendu pour information et suivi, prescrit avec durée, avis demandé dans la suite, rien d'inventé",lt.get("btn") and "pour information et suivi" in lt["mt"] and "pendant" in lt["mt"] and "avis spécialisé demandé (cardiologue)" in lt["mt"].lower() and "Diagnostic retenu" not in lt["mt"] and "Antécédents" not in lt["mt"] and "rendez-vous" not in lt["mt"],lt.get("mt"))
        ok(label+" courriers : modifiables avant impression, une page chacun, gras conservé",lt.get("n")==2 and lt.get("fit") and lt.get("edited") and lt.get("bold") and lt.get("W"),{k:lt.get(k) for k in ["n","fit","edited","bold","W"]})
        sm=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const c=document.getElementById('let_sansmt');c.checked=true;c.dispatchEvent(new Event('change'));await w(100);state.lettres.mt.edited=false;const t=letText(currentPack(),'mt');state.lettres={};state.patient='';state.allergies=[];state.tt=[];state.obs={};state.cst={};render();return t;}""")
        ok(label+" courriers : sans médecin traitant, « À l'attention du médecin qui prendra en charge le patient »",sm.startswith("À l'attention du médecin qui prendra en charge le patient."),sm[:80])
        # Bloc 12 — Infectiologie et endocrinologie
        nb12=await page.evaluate("PACKS_V40_B12.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 12 : 11 packs chargés",nb12==11,nb12)
        rv=await page.evaluate("""()=>PACKS.flatMap(p=>p.s.filter(sh=>sh.k==='med').flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).filter(t=>/^REVAXIS|REVAXIS suspension/.test(t)).length""")
        ok(label+" bloc 12 : REVAXIS (non commercialisé) n'est plus prescrit nulle part, remplacé par un dTcaP",rv==0 and "BOOSTRIXTETRA" in await page.evaluate("REVAXIS"),rv)
        pf=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Sepsis, purpura fébrile — appel du 15');const l=p.s.find(sh=>sh.k==='med').l[0];const pd=PACKS.find(x=>x.n==='Pied diabétique — plaie infectée').s.find(sh=>sh.k==='med').l.filter(x=>x.grp==='atb');return [l.jr===true,/1 g chez l'adulte, 50 mg\/kg sans dépasser 1 g/.test(l.t),/^KEFORAL 1 g.*1 comprimé matin et soir pendant 7 jours/.test(pd[0].t)&&!pd[0].opt,pd.length];}""")
        ok(label+" bloc 12 : purpura fulminans (ceftriaxone, ligne jamais imprimée), pied diabétique céfalexine 2 g/j 7 jours (SPILF 2023, RCP)",pf[0] and pf[1] and pf[2] and pf[3]==3,pf)
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/2020';state.poids='18';render();"); await page.wait_for_timeout(200)
        await pick(page,"resucrage","Hypoglycémie")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" bloc 12 : hypoglycémie, glucagon 0,5 mg sous 25 kg (RCP GLUCAGEN)",any("GLUCAGEN" in x["t"] and "0,5 mg" in x["t"] for x in med),[x["t"][:80] for x in med])
        await page.evaluate("state.ddn='01/01/1985';state.poids='70';state.sel=null;render();")
        # Bloc 13 — Gériatrie, intoxications, soins palliatifs
        nb13=await page.evaluate("PACKS_V40_B13.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 13 : 13 packs chargés",nb13==13,nb13)
        sp=await page.evaluate("""()=>{const out=[];for(const n of ['Douleur en fin de vie','Dyspnée et encombrement de fin de vie','Agitation terminale'])for(const sh of PACKS.find(x=>x.n===n).s)if(sh.k==='med')for(const l of sh.l){const o=typeof l==='string'?{t:l}:l;if(/MIDAZOLAM|MORPHINE|ACTISKENAN|SKENAN|ORAMORPH/.test(o.t)&&!o.jr)out.push(n+' : '+o.t.slice(0,40));}return out;}""")
        ok(label+" bloc 13 : stupéfiants et midazolam (ordonnance sécurisée) jamais imprimés en soins palliatifs",not sp,sp)
        await page.evaluate("state.sel=null;state.view='';state.risk='s';state.ddn='01/01/1945';render();"); await page.wait_for_timeout(200)
        await pick(page,"INR élevé","Surdosage en anticoagulant")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        vk=[x["t"] for x in med if "VITAMINE K1" in x["t"]]
        ok(label+" bloc 13 : surdosage en AVK, vitamine K 2 mg et 5 mg per os proposées (HAS 2008), aucune cochée d'office",len(vk)==2 and any("(2 mg)" in v for v in vk) and any("(5 mg)" in v for v in vk) and not any(x["on"] for x in med if "VITAMINE K1" in x["t"]),vk)
        await page.evaluate("state.risk=undefined;state.ddn='01/01/1985';state.sel=null;render();")
        # Repères visuels : couleur du mode, patient en cours encadré et nommé, patients validés en gris
        vis=[]
        for th in ["day","night"]:
            r=await page.evaluate("""async th=>{const w=ms=>new Promise(r=>setTimeout(r,ms));THEME.mode=th;localStorage.removeItem('sos_theme_force');themeApply();
              newPatient();state.sel=null;state.view='';state.patient='DURAND Paul';state.ddn='01/01/1950';state.nh=state.nh||{};state.cot=cotDefault();state.cot.lieu='visite';render();await w(80);
              const bv=getComputedStyle(document.documentElement).getPropertyValue('--mode').trim(),mv=document.documentElement.dataset.mode;
              state.cot.lieu='cabinet';render();await w(80);const bc=getComputedStyle(document.documentElement).getPropertyValue('--mode').trim(),mc=document.documentElement.dataset.mode;
              const tag=document.querySelector('.jbar .pat-tag, .jhead .pat-tag');const tr=tag&&tag.getBoundingClientRect();const pco=getComputedStyle(document.querySelector('.pcard')).outlineStyle;const W=document.documentElement.clientWidth;
              const p1=getComputedStyle(document.documentElement).getPropertyValue('--pat-d').trim();newPatient();state.patient='MARTIN Léa';state.ddn='02/02/2022';render();await w(50);const p2=getComputedStyle(document.documentElement).getPropertyValue('--pat-d').trim();
              const res={mv,mc,bv,bc,tag:tag?tag.textContent:'',tagIn:!!(tr&&tr.top>=0&&tr.top<160&&tr.right<=W+1),outline:pco,tagTop:tr?Math.round(tr.top):null,pdiff:p1!==p2,sw:document.documentElement.scrollWidth<=W};
              state.patient='';state.ddn='';render();res.off=!document.documentElement.classList.contains('pat-on');return res;}""",th)
            if not (r["mv"]=="visite" and r["mc"]=="consult" and r["bv"]!=r["bc"] and r["tag"].startswith("D. · ") and r["tagIn"] and r["outline"]=="solid" and r["pdiff"] and r["sw"] and r["off"]): vis.append((th,r))
        await page.evaluate("THEME.mode='auto';themeApply();state.cot=cotDefault();render();")
        ok(label+" repères visuels : Visite et Consultation de couleurs distinctes, patient encadré et nommé « initiale · âge » en haut, couleur différente par patient (jour et nuit)",not vis,vis)
        gr=await page.evaluate("""()=>{const h=VALID.hist;VALID.hist=[{ts:Date.now(),patient:'TEST Gris',pack:'',snap:{}},{ts:Date.now(),patient:'TEST Côté',pending:true,pack:'',snap:{}}];validListScreen();const rows=[...document.querySelectorAll('#lock .vrow')];const ok=rows.length===2&&rows.every(r=>r.classList.contains('pat-off')&&/grayscale/.test(getComputedStyle(r).filter));VALID.hist=h;identClose();return ok;}""")
        ok(label+" repères visuels : patients validés ou mis de côté affichés en gris",gr)
        # Fiches MccMissionSG (textes fictifs) : doublons, fiches non lues, bloc Adresse, accès, « Chez Consultation »
        F1="MARTIN PAUL\nNé(e) le 03/04/1990 - 36 A\n06 11 22 33 44\nINTERVENTION\nFIEVRE\nRdv 20h30 envoyé par SMS au 06 11 22 33 44\nCommentaire : 3 rue du Moulin, sonner fort\nAdresse :\n8 RUE DES LILAS\n45400\nFLEURY-LES-AUBRAIS\nBat : B  Etg : 2  Por : 21"
        F2="DURAND LUCIE\nNé(e) le 05/06/1985\nADRESSE REPOSITIONNEE PAR TEST AGENT LE 01/02/2025 10:11:12\nTOUX\nAdresse : 12 AVENUE DES PINS, 45100, ORLÉANS-LA-SOURCE\nEtg : RDC"
        F3="LEROY ANNE\nNé(e) le 07/08/1970\n06 22 33 44 55\nLOMBALGIE\nChez Consultation SOS Médecins\nAdresse : 3 PLACE DU MARCHE 45000 ORLEANS"
        F4="PETIT LOU\nNé(e) le 09/09/2019\nOTITE\nillisible"
        await page.evaluate("()=>{window.__fsave=JSON.stringify({stops:TOUR.stops,order:TOUR.order,consults:TOUR.consults||[]});TOUR.stops=[];TOUR.order=[];TOUR.consults=[];TOUR.unread=[];window.tourOptimize=window.tourOptimize;window.__tO=window.tourOptimize;window.tourOptimize=async()=>{};}")
        fa=await page.evaluate("""([a,b])=>{const r1=parseFiche(a),r2=parseFiche(b);return {a1:r1.addr,b1:r1.bat,m1:r1.motif,a2:r2.addr,b2:r2.bat};}""",[F1,F2])
        ok(label+" fiches : adresse lue dans le bloc « Adresse » (commune composée), motif et SMS ignorés, accès Bat/Etg/Por",fa["a1"]=="8 RUE DES LILAS 45400 FLEURY-LES-AUBRAIS" and fa["b1"]=="Bât. B · Étage 2 · Porte 21" and fa["m1"]=="FIEVRE" and "ORLÉANS-LA-SOURCE" in fa["a2"] and "12 AVENUE DES PINS" in fa["a2"] and fa["b2"]=="Étage RDC",fa)
        du=await page.evaluate("""async t=>{await fichesFromText(t);const n1=TOUR.stops.length;await fichesFromText(t);const n2=TOUR.stops.length;const toastTxt=(document.getElementById('toast')||{}).textContent||'';
          const f=parseFiche(t);f.nom='AUTRE';f.prenom='NOM';f.ddn='01/01/2000';f.addr='autre adresse';TOUR.stops[0].imgHash='abc123';const byImg=!!ficheDup(f,'abc123');return {n1,n2,toast:/Déjà dans la tournée/.test(toastTxt),byImg};}""",F1)
        ok(label+" fiches : même fiche importée deux fois = « déjà dans la tournée », pas de second arrêt (nom + naissance, adresse + motif, ou même image)",du["n1"]==1 and du["n2"]==1 and du["toast"] and du["byImg"],du)
        un=await page.evaluate("""async t=>{const w=ms=>new Promise(r=>setTimeout(r,ms));TOUR.unread=[];await fichesFromText(t);await w(100);const u=TOUR.unread[0];if(!u)return {u:false};u.thumb='data:image/gif;base64,R0lGODlhAQABAAAAACw=';u.big=u.thumb;render();await w(50);
          const row=document.querySelector('[data-fu]');const txt=row?row.innerText:'';const hasImg=!!row.querySelector('img.fu-th');row.querySelector('[data-fuopen]').click();await w(80);const big=!!document.querySelector('.fu-big');const inp=document.querySelector('.fu-addr');inp.value='5 rue des Écoles, 45000 Orléans';document.querySelector('.fu-ok').click();await w(80);
          const s=TOUR.stops.find(x=>x.nom&&x.nom.startsWith('PETIT'));return {u:true,txt,hasImg,big,added:!!s,left:TOUR.unread.length,view:state.view};}""",F4)
        ok(label+" fiches : fiche non lue = miniature + éléments lus (initiale, âge, motif) + « Compléter » avec capture agrandie et saisie de l'adresse",un.get("u") and "P. · " in un["txt"] and "OTITE" in un["txt"] and un["hasImg"] and un["big"] and un["added"] and un["left"]==0,un)
        co=await page.evaluate("""async t=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const n0=TOUR.stops.length;const pr=fichesFromText(t);await w(100);const d=document.getElementById('fq');const q=d&&!d.hidden&&/Consultation au cabinet ou visite/.test(d.innerText);const def=document.getElementById('fq_c').classList.contains('p');document.getElementById('fq_c').click();await pr;
          const c1=TOUR.stops.length===n0&&(TOUR.consults||[]).length===1;TOUR.consults=[];const pr2=fichesFromText(t);await w(100);document.getElementById('fq_v').click();await pr2;const v1=TOUR.stops.length===n0+1;return {q,def,c1,v1};}""",F3)
        ok(label+" fiches : « Chez Consultation » → question « Consultation au cabinet ou visite ? », par défaut consultation sans arrêt",co["q"] and co["def"] and co["c1"] and co["v1"],co)
        await page.evaluate("()=>{const s=JSON.parse(window.__fsave);TOUR.stops=s.stops;TOUR.order=s.order;TOUR.consults=s.consults;TOUR.unread=[];window.tourOptimize=window.__tO;state.view='';state.fuOpen='';render();}")
        # Bloc 14 — Administratif et renouvellement
        nb14=await page.evaluate("PACKS_V40_B14.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 14 : 9 packs chargés",nb14==9,nb14)
        st=await page.evaluate("""()=>{const p=PACKS.find(x=>x.n==='Stupéfiants — ordonnance sécurisée');const m=p.s.find(sh=>sh.k==='med').l;const g=PACKS.find(x=>x.n==='Garde à vue — examen de compatibilité');const c=g.s.find(sh=>sh.k==='cert').l.filter(l=>l.grp==='gav');const f=['dateacc','reserve','ald1','ald2','insuline','dmliste'].every(k=>!!FIELDS[k]);return [m.every(l=>l.jr===true),c.length,!/diagnostic/i.test(c.map(l=>l.t).join(' ')),f];}""")
        ok(label+" bloc 14 : stupéfiants jamais imprimés, garde à vue en 3 conclusions sans diagnostic, champs à saisir déclarés",st[0] and st[1]==3 and st[2] and st[3],st)
        await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(200)
        await pick(page,"bon de transport","Bon de transport")
        bt=await page.evaluate("""()=>{const sh=[...document.querySelectorAll('.sheet')].find(s=>/Paramédical|Transport/i.test(s.innerText));return sh?[...sh.querySelectorAll('li')].map(li=>li.querySelector('.lt').textContent):[];}""")
        ok(label+" bloc 14 : bon de transport, VSL ou taxi conventionné en transport partagé, ambulance ou véhicule personnel",len(bt)==3 and any("transport partagé" in x for x in bt) and any("ambulance" in x for x in bt),bt)
        await page.evaluate("state.sel=null;render();")
        # Fiches : vraisemblance, « Coller les fiches » (raccourci iOS / Android), lecture par zones sur captures fictives (OCR réel)
        vr=await page.evaluate("""()=>{const a=parseFiche("DUPONT JEAN\\nNé(e) le 01/01/1980 - 30 A\\nTél patient\\n06 12 34\\nAdresse : 3 rue de la Paix 75001 PARIS\\nTOUX");const w=ficheCheck(a);const b=parseFiche("DUPONT JEAN\\nNé(e) le 01/01/1980 - 46 A\\n06 12 34 56 78\\nAdresse : 3 rue de la Paix 45000 ORLEANS\\nTOUX");return {w,ok:ficheCheck(b)};}""")
        ok(label+" fiches : vraisemblance signalée (code postal hors Loiret, téléphone incomplet, âge incohérent avec la naissance)",any("75001 hors secteur" in x for x in vr["w"]) and any("téléphone" in x for x in vr["w"]) and any("âge affiché" in x for x in vr["w"]) and vr["ok"]==[],vr)
        cl=await page.evaluate("""async()=>{const save=JSON.stringify({s:TOUR.stops,o:TOUR.order});window.__tO2=window.tourOptimize;window.tourOptimize=async()=>{};TOUR.stops=[];TOUR.order=[];TOUR.unread=[];
          const txt="DURAND LUCIE\\nNé(e) le 05/06/1985\\n06 22 33 44 55\\nTOUX\\nAdresse : 12 AVENUE DES PINS, 45100, ORLÉANS-LA-SOURCE\\n-----\\nBERNARD LEO\\nNé(e) le 02/03/2015\\n06 99 88 77 66\\nOTITE\\nAdresse : 5 RUE JEANNE D'ARC 45000 ORLEANS\\n-----\\nDURAND LUCIE\\nNé(e) le 05/06/1985\\n06 22 33 44 55\\nTOUX\\nAdresse : 12 AVENUE DES PINS, 45100, ORLÉANS-LA-SOURCE\\n";
          const o=navigator.clipboard&&navigator.clipboard.readText;try{Object.defineProperty(navigator,'clipboard',{value:{readText:async()=>txt},configurable:true});}catch(e){}
          state.view='tour';render();await new Promise(r=>setTimeout(r,50));const btn=document.querySelector('[data-fpaste]');document.querySelector('[data-fpaste]').click();await new Promise(r=>setTimeout(r,400));
          const n=TOUR.stops.length,dup=/[Dd]éjà dans la tournée/.test((document.getElementById('toast')||{}).textContent||'');const r=JSON.parse(save);TOUR.stops=r.s;TOUR.order=r.o;window.tourOptimize=window.__tO2;state.view='';render();return {n,dup,btn:!!btn};}""")
        ok(label+" fiches : « Coller les fiches » crée tous les arrêts d'un coup, doublons refusés",cl["n"]==2 and cl["dup"] and cl["btn"],cl)
        if width<500:
            paths=await FF.make(b,os.path.join(ROOT,"tests","_tmp_fiches"))
            for nm,ex in FF.EXPECT.items():
                r=await page.evaluate("""async n=>{const b=await (await fetch('tests/_tmp_fiches/fiche-'+n+'.png')).blob();const f=new File([b],'x.png',{type:'image/png'});const cv=await imageToCanvas(f,1100);const z=await ocrZonesFromCanvas(cv);const pf=parseFiche(z.text);return {zones:z.zones,addr:pf.addr,tel:pf.tel,ddn:pf.ddn,bat:pf.bat,motif:pf.motif,note:pf.note,warn:ficheCheck(pf)};}""",nm)
                good=r["zones"]>=4 and all(x in r["addr"] for x in ex["addr"]) and r["tel"]==ex["tel"] and r["ddn"]==ex["ddn"] and r["bat"]==ex["bat"] and r["motif"]==ex["motif"] and not r["warn"] and "DURAND" not in (r["addr"]+r["note"]) and "SMS" not in r["addr"]
                ok(label+f" fiches : capture fictive {nm} lue par zones repérées par leurs intitulés (adresse, commune composée, téléphone, naissance, accès, motif)",good,r)
            import shutil; shutil.rmtree(os.path.join(ROOT,"tests","_tmp_fiches"),ignore_errors=True)
        # Bloc 15 — Fiches ◇ premier recours
        nb15=await page.evaluate("PACKS_V40_B15.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 15 : 11 packs chargés",nb15==11,nb15)
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/2016';state.poids='25';render();"); await page.wait_for_timeout(200)
        await pick(page,"pipi au lit","Énurésie de l'enfant")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" bloc 15 : énurésie à 10 ans, desmopressine 120 µg le soir avec restriction hydrique (RCP MINIRINMELT)",any("MINIRINMELT 120" in x["t"] and "1 heure avant et 8 heures après" in x["t"] for x in med),[x["t"][:80] for x in med])
        await page.evaluate("state.ddn='01/01/2018';render();"); await page.wait_for_timeout(100)
        await page.evaluate("state.sel=null;render();"); await pick(page,"carence en fer","Anémie ferriprive — traitement")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" bloc 15 : fer chez l'enfant de 8 ans, 1 comprimé par jour (RCP TARDYFERON)",any("TARDYFERON" in x["t"] and "1 comprimé par jour" in x["t"] and "1 à 2" not in x["t"] for x in med),[x["t"][:80] for x in med])
        pr=await page.evaluate("""()=>['HTA — suivi et ajustement du traitement','Dyslipidémie — dépistage et traitement','Diabète de type 2 — suivi','Grossesse sans suivi — examens et orientation'].every(n=>/Premier recours/.test(JSON.stringify(PACKS.find(x=>x.n===n).s.find(sh=>sh.k==='memo'))))""")
        ok(label+" bloc 15 : chaque fiche ◇ rappelle le cadre premier recours (dépannage puis orientation)",pr)
        await page.evaluate("state.ddn='01/01/1985';state.poids='70';state.sel=null;render();")
        # Retours de garde : réglages validés sans saut d'écran, alerte d'attente compacte, sommaire du journal
        await page.evaluate("()=>{window.__rs=JSON.stringify({s:TOUR.stops,o:TOUR.order,c:TOUR.cfg});window.__tO3=window.tourOptimize;window.tourOptimize=async()=>{};const now=Date.now();TOUR.stops=[1,2,3].map(i=>({id:'w'+i,addr:'x',nom:'TEST'+i+' A',ddn:'01/01/1950',lat:47.9+i/100,lon:1.9,label:i+' rue Test 45000 Orléans',done:false,ts:now-(150+i*10)*60000}));TOUR.order=['w1','w2','w3'];TOUR.cfg=null;state.tpSetOpen=true;state.tpWaitOpen=false;state.view='tour';render();}")
        await page.wait_for_timeout(150)
        st=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const d=document.getElementById('tp_set');d.scrollIntoView({block:'center'});await w(50);const top0=d.getBoundingClientRect().top;let n=0;const R=window.render;window.render=function(){n++;return R.apply(this,arguments);};
          const f=document.getElementById('tp_fin');f.focus();f.value='23:00';f.dispatchEvent(new Event('input'));f.dispatchEvent(new Event('change'));const m=document.getElementById('tp_marge');m.focus();m.value='15';m.dispatchEvent(new Event('input'));m.dispatchEvent(new Event('change'));await w(80);
          const during={renders:n,fin:tpCfg().fin,top:Math.round(document.getElementById('tp_set').getBoundingClientRect().top-top0)};document.getElementById('tp_set_ok').click();await w(120);window.render=R;
          const d2=document.getElementById('tp_set');return {during,after:{fin:tpCfg().fin,marge:tpCfg().marge,open:d2.open,shift:Math.round(d2.getBoundingClientRect().top-top0),st:(document.getElementById('tp_set_st')||{}).textContent}};}""")
        ok(label+" réglages de tournée : aucun recalcul pendant la saisie, appliqués à la validation, la vue ne bouge pas",st["during"]["renders"]==0 and st["during"]["fin"]!="23:00" and st["during"]["top"]==0 and st["after"]["fin"]=="23:00" and st["after"]["marge"]==15 and st["after"]["open"] and abs(st["after"]["shift"])<=4,st)
        wt=await page.evaluate("""()=>{const t=document.body.innerText;const sums=[...document.querySelectorAll('details.tp-wait summary')].map(x=>x.textContent);const d=document.querySelector('details.tp-wait');return {sums,li:d?d.querySelectorAll('li').length:0,open:d?d.open:null,chips:(t.match(/attend depuis/g)||[]).length};}""")
        ok(label+" alerte d'attente : une seule ligne compacte « 3 patients attendent depuis plus de 2 h », repliée, liste sans doublon",len(set(wt["sums"]))==1 and wt["sums"][0].startswith("3 patients attendent depuis plus de 2 h") and wt["li"]==3 and wt["open"] is False and wt["chips"]==0,wt)
        await page.evaluate("()=>{const r=JSON.parse(window.__rs);TOUR.stops=r.s;TOUR.order=r.o;TOUR.cfg=r.c;window.tourOptimize=window.__tO3;state.tpSetOpen=false;state.view='journal';render();}")
        await page.wait_for_timeout(150)
        jn=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const nav=document.querySelector('.jnav');const links=nav?[...nav.querySelectorAll('a')].map(a=>a.textContent):[];const fab=document.querySelectorAll('.jfab button').length;
          const a=[...document.querySelectorAll('.jnav a')].find(x=>/Sécurité/.test(x.textContent));if(a)a.click();await w(700);const tg=a?document.getElementById(a.dataset.jnav).getBoundingClientRect().top:null;const sw=document.documentElement.scrollWidth<=document.documentElement.clientWidth;
          state.view='';render();await w(50);return {links,fab,tg:tg==null?null:Math.round(tg),sw,fabGone:document.querySelectorAll('.jfab').length===0};}""")
        ok(label+" journal : sommaire en haut (gardes et patients, sécurité, identité, sauvegarde…), lien qui amène à la partie, boutons haut et bas",len(jn["links"])>=6 and any("Gardes" in x for x in jn["links"]) and any("Identité" in x for x in jn["links"]) and any("Sauvegarde" in x for x in jn["links"]) and jn["fab"]==2 and jn["tg"] is not None and -5<=jn["tg"]<=200 and jn["sw"] and jn["fabGone"],jn)
        # Affichage : Garde (défaut, actions principales vives, une seule mise en avant) / Premium, choix dans le menu ⋯
        ga=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));const save=JSON.stringify({s:TOUR.stops,o:TOUR.order,c:TOUR.current});window.__tO4=window.tourOptimize;window.tourOptimize=async()=>{};
          TOUR.stops=[{id:'g1',addr:'x',nom:'GARDE Test',ddn:'01/01/1950',lat:47.9,lon:1.9,label:'1 rue Test 45000 Orléans',done:false,ts:Date.now()}];TOUR.order=['g1'];state.sel=null;state.view='';state.cot=cotDefault();state.cot.lieu='visite';tourUse('g1');render();await w(80);
          const def=DESIGN;const now1=[...document.querySelectorAll('.act-now')].map(x=>x.textContent.trim());const vact=[...document.querySelectorAll('.vact')].filter(b=>b.offsetParent).length;const nav=document.querySelector('.tcard .tc-nav');const bg=nav?getComputedStyle(nav).backgroundColor:'';
          nav.addEventListener('click',e=>e.preventDefault(),{once:true});nav.click();await w(120);const now2=[...document.querySelectorAll('.act-now')].map(x=>x.textContent.trim());
          const mp=document.querySelector('[data-dset="premium"]'),mg=document.querySelector('[data-dset="garde"]');const menu=isPhone()?(!!mp&&!!mg):true;if(mp)mp.click();else{DESIGN='premium';render();}await w(80);const prem=DESIGN==='premium'&&document.querySelectorAll('.vact').length===0;const mg2=document.querySelector('[data-dset="garde"]');if(mg2)mg2.click();else{DESIGN='garde';render();}await w(50);
          const r=JSON.parse(save);TOUR.current=r.c;TOUR.stops=r.s;TOUR.order=r.o;window.tourOptimize=window.__tO4;state.cot=cotDefault();newPatient();render();return {def,now1,now2,vact,bg,menu,prem,back:DESIGN};}""")
        ok(label+" affichage Garde par défaut : actions principales pleines et vives, une seule mise en avant (Naviguer puis Je suis arrivé), choix Garde / Premium dans le menu",ga["def"]=="garde" and len(ga["now1"])==1 and "Naviguer" in ga["now1"][0] and len(ga["now2"])==1 and "arrivé" in ga["now2"][0] and ga["vact"]>=3 and ga["bg"] not in ("rgba(0, 0, 0, 0)","transparent") and ga["menu"] and ga["prem"] and ga["back"]=="garde",ga)
        # Impression : critères réservés au médecin jamais imprimés (16/10/2026)
        rv=await page.evaluate("""()=>{const W=/Fagerstr|CHA2DS2|HAS-BLED|Cockcroft|clairance|\bDFG\b|\bQTc?\b|\bAMM\b|\bscores?\b|\bseuils?\b|critères?|µmol|ml\/min|\bFEVG\b|\bIPS\b|index de pression|cigarettes par jour|terrain|indication/i;const ORD=["med","dm","ide","kine","para","podo"],EX=["bio","img","spe"];const out=[];
          for(const p of PACKS)for(const sh of p.s){if(!ORD.includes(sh.k)&&!EX.includes(sh.k))continue;for(const l of sh.l||[]){const o=typeof l==="string"?{t:l}:l;if(o.jr)continue;for(const t of [o.t,...(o.alt||[])]){if(typeof t!=="string")continue;const c=printClean(t);const hit=ORD.includes(sh.k)?W.test(c):(c.match(/\([^()]*\)/g)||[]).some(x=>W.test(x));if(hit)out.push(p.n+" : "+c.slice(0,80));}}}return out;}""")
        ok(label+" impression : aucun terme réservé au médecin (score, seuil, DFG, QT, AMM, indication, terrain) dans une ordonnance",not rv,rv[:5])
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1980';state.poids='70';state.patient='TEST Patient';window.print=()=>{};render();"); await page.wait_for_timeout(300)
        await pick(page,"tabac","Sevrage tabagique")
        pt=await page.evaluate("""async()=>{await printPack();await new Promise(r=>setTimeout(r,800));const t=(document.querySelector('#print')||{}).innerText||'';return [/NICOPATCHLIB 21/.test(t),/Coller le patch le matin/.test(t),/Fagerstr|cigarettes ou plus/i.test(t)];}""")
        ok(label+" impression : NICOPATCHLIB imprimé avec la consigne de pose, sans le critère Fagerström",pt[0] and pt[1] and not pt[2],pt)
        await page.evaluate("document.body.classList.remove('printing');state.patient='';render();")
        # iPhone 375 px : lignes longues renvoyées à la ligne, crayon visible (jour, nuit, grand texte)
        if width<500:
            bad=[]
            for th,big in [("day",False),("night",False),("day",True),("night",True)]:
                await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.removeItem('sos_theme_force');localStorage.setItem('sos_bigtext','{1 if big else 0}');themeApply();")
                for q,n in [("tabac","Sevrage tabagique"),("pouls irrégulier","Fibrillation atriale — découverte ou récidive")]:
                    await page.evaluate("state.sel=null;state.view='';render();"); await page.wait_for_timeout(150)
                    await pick(page,q,n)
                    r=await page.evaluate("""()=>{const W=document.documentElement.clientWidth;let n=0,lines=0;document.querySelectorAll('.sheet ul.lines li').forEach(li=>{lines++;const r=li.getBoundingClientRect();const e=li.querySelector('.edl');const er=e&&e.getBoundingClientRect();if(r.right>W+1||!e||er.right>W+1||er.width<8||getComputedStyle(e).visibility==='hidden')n++;});return [n,lines,document.documentElement.scrollWidth<=W];}""")
                    if r[0] or not r[2] or not r[1]: bad.append((th,big,n,r))
            await page.evaluate("localStorage.setItem('sos_theme','auto');localStorage.setItem('sos_bigtext','0');themeApply();")
            ok(label+" 375 px : aucune ligne d'ordonnance ne déborde, crayon visible (jour, nuit, grand texte)",not bad,bad)
        # Bandeau « Nouvelle version disponible » (16/10/2026)
        if width<500:
            ub=[]
            for th in ["day","night"]:
                await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.removeItem('sos_theme_force');themeApply();state.sel=null;state.view='';state.patient='';render();")
                await page.evaluate("UPD.info=null;showUpdateBar();"); await page.wait_for_timeout(700)
                r=await page.evaluate("""()=>{const b=document.getElementById('updbar');const r=b.getBoundingClientRect();const g=document.getElementById('upd_go').getBoundingClientRect();const W=document.documentElement.clientWidth;const bg=getComputedStyle(b).backgroundColor;const j=document.querySelector('.jbar.phone');const jt=j?j.getBoundingClientRect().top:999;return {top:Math.round(r.top),w:Math.round(r.width),W,h:Math.round(r.height),go:Math.round(g.height),goR:Math.round(g.right),bg,txt:b.innerText,li:b.querySelectorAll('li').length,jt:Math.round(jt),sw:document.documentElement.scrollWidth};}""")
                if not (r["top"]==0 and r["w"]==r["W"] and r["go"]>=48 and r["goR"]<=r["W"] and "rgb(255, 176, 0)" in r["bg"] and bool(re.search(r"version 41[a-z]*",r["txt"])) and "Mettre à jour maintenant" in r["txt"] and 1<=r["li"]<=3 and r["jt"]>=r["h"]-2 and r["sw"]<=r["W"]): ub.append((th,r))
            await page.evaluate("localStorage.setItem('sos_theme','auto');themeApply();")
            ok(label+" mise à jour : bandeau pleine largeur en haut, jaune-orange jour et nuit, version, 1 à 3 lignes « Ce qui change », gros bouton (375 px)",not ub,ub)
            st=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));document.getElementById('upd_later').click();await w(100);const a=document.getElementById('updbar').className;state.sel=PACKS.findIndex(p=>p.n==='Angine');render();await w(100);const b=document.getElementById('updbar').className;state.sel=null;render();await w(100);const c=document.getElementById('updbar').className;return [a,b,c];}""")
            ok(label+" mise à jour : « Plus tard » réduit le bandeau, il revient au retour sur l'écran principal",st[0]=="mini" and st[1]=="mini" and st[2]=="",st)
            nr=await page.evaluate("""async()=>{window.__noReload=1;state.sel=PACKS.findIndex(p=>p.n==='Angine');render();navigator.serviceWorker.dispatchEvent(new Event('controllerchange'));await new Promise(r=>setTimeout(r,300));const res=[window.__noReload===1,UPD.pendingReload,!!document.querySelector('#updbar .uw')];UPD.pendingReload=false;UPD.ready=false;document.getElementById('updbar').remove();document.documentElement.classList.remove('upd-on');document.documentElement.style.removeProperty('--updh');state.sel=null;render();return res;}""")
            ok(label+" mise à jour : jamais de rechargement automatique pendant une consultation",nr[0] and nr[1] and nr[2],nr)
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
    open(os.path.join(ROOT,"tests","resultats.md"),"w",encoding="utf-8").write("# Tests v40 (lot 1, blocs 2 à 8)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
asyncio.run(main())
