# Tests navigateur Packs SOS — prérequis : pip install playwright puis python -m playwright install chromium
import asyncio, os, json, subprocess, time, sys

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
        gone=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5].flatMap(p=>p.s.filter(sh=>sh.k!=='memo').flatMap(sh=>sh.l.map(l=>typeof l==='string'?l:l.t))).filter(t=>/JOSACINE \d|PÉDIAZOLE|VANCOMYCINE 125 mg gélule|DIFICLIR 200|MOTILIUM 10|NICOPATCH \d|BACTRIM pédiatrique suspension buvable :|VITAMINE A DULCIS/.test(t))")
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
        dd=await page.evaluate("""()=>{const out=[];const sv=[state.risk,state.ddn,state.poids];for(const pk of [...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5]){for(const rk of ['s','r']){state.risk=rk;state.ddn='01/01/1985';state.poids='70';pk.s.forEach((sh,si)=>{if(sh.k!=='med'&&sh.k!=='dm')return;expand(sh,si);(ADAPT_NOTES[si]||[]).filter(n=>/double/.test(n)).forEach(n=>out.push(pk.n+' : '+n));});}}[state.risk,state.ddn,state.poids]=sv;return [...new Set(out)];}""")
        ok(label+" fiches : aucune ligne effacée par dédoublonnage",len(dd)==0,dd[:3])
        # Bloc 5 — Rhumatologie et traumatologie, champs à saisir
        nb5=await page.evaluate("PACKS_V40_B5.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 5 : 22 packs chargés",nb5==22,nb5)
        nf=await page.evaluate("[...PACKS_V40,...PACKS_V40_B2,...PACKS_V40_B3,...PACKS_V40_B4,...PACKS_V40_B5].filter(p=>{const u=[...JSON.stringify(p.s).matchAll(/\{f:(\w+)\}/g)].map(m=>m[1]);return u.some(k=>!(p.fields||[]).includes(k)||!FIELDS[k]);}).map(p=>p.n)")
        ok(label+" fiches : chaque champ {f:…} a sa case de saisie",len(nf)==0,nf[:3])
        cv=await page.evaluate("atDureeSugg('Cervicalgie / torticolis')"); ok(label+" durée AT cervicalgie CNAM",("CNAM" in cv),cv)
        await page.evaluate("state.sel=null;state.view='';state.risk=undefined;state.ddn='01/01/1960';state.poids='';render();"); await page.wait_for_timeout(300)
        await pick(page,"gros orteil","Crise de goutte")
        L=await lines(page); med=[x for x in L if x["lbl"]=="Médicaments"][0]["l"]
        ok(label+" goutte : colchicine cochée, prednisone en alternative, pas de doublon",any("COLCHICINE" in x["t"] and x["on"] for x in med) and any("CORTANCYL" in x["t"] and not x["on"] for x in med))
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
    open(os.path.join(ROOT,"tests","resultats.md"),"w").write("# Tests v40 (lot 1, blocs 2 à 5)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
asyncio.run(main())
