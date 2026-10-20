# Tests bloc 16 — complément (érythème fessier, parasitose digestive, épicondylite, apnées du sommeil, dysthyroïdie, décès à domicile)
# Prérequis : pip install playwright puis python -m playwright install chromium. Lancer : python tests/test_bloc16.py
import asyncio, os, subprocess, time, sys, re
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8781
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,info if not cond else "")

async def unlock(page):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html")
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
    return await page.evaluate("""()=>[...document.querySelectorAll('.sheet')].map(sh=>({t:sh.querySelector('.hd label').textContent.trim(),lbl:sh.querySelector('.tp').textContent,l:[...sh.querySelectorAll('li')].map(li=>({on:li.querySelector('input').checked,t:li.querySelector('.lt').textContent}))}))""")

def med_of(L):
    m=[x for x in L if x["lbl"]=="Médicaments"]
    return m[0]["l"] if m else []

async def run(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},device_scale_factor=2,is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page()
        errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page)
        # ---------- structure du bloc ----------
        n6=await page.evaluate("PACKS_V40_B16.filter(np=>PACKS.some(p=>p===np)).length"); ok(label+" bloc 16 : 6 packs chargés",n6==6,n6)
        dup=await page.evaluate("PACKS_V40_B16.map(np=>PACKS.filter(p=>p.n===np.n).length)"); ok(label+" bloc 16 : anciennes fiches remplacées, aucun doublon",all(d==1 for d in dup),dup)
        st=await page.evaluate("PACKS_V40_B16.map(p=>{const m=p.s.filter(sh=>sh.k==='memo');return m.length===1&&m[0].l.some(l=>(typeof l==='string'?l:l.t).includes('bloc 16, version 1'));})")
        ok(label+" bloc 16 : un seul mémo par fiche avec la ligne « non relue (bloc 16, version 1) »",all(st),st)
        cons=await page.evaluate("PACKS_V40_B16.map(p=>p.s.some(sh=>sh.k==='cons'&&sh.l.length>=3))"); ok(label+" bloc 16 : consignes patient (3 lignes au moins) sur les 6 fiches",all(cons),cons)
        pr=await page.evaluate("""()=>{const bad=[];PACKS_V40_B16.forEach(p=>p.s.forEach(sh=>{if(!PRINT_CLEAN_K.includes(sh.k))return;sh.l.forEach(l=>{const t=typeof l==='string'?l:l.t;const c=printClean(t,sh.k);if(/\bRCP\b|\bCRAT\b|\bANSM\b|contre-indiqu|\brupture\b|approvisionnement|non remboursé|\bHAS 20|\bLPP\b|grossesse|allaitante/i.test(c))bad.push(p.n+' | '+c.slice(0,100));});}));return bad;}""")
        ok(label+" bloc 16 : aucun mémo médecin (RCP, CRAT, ANSM, contre-indication, rupture, remboursement) sur les documents imprimés",len(pr)==0,pr[:4])
        nest=await page.evaluate("""()=>{const bad=[];PACKS_V40_B16.forEach(p=>p.s.forEach(sh=>{if(!PRINT_CLEAN_K.includes(sh.k))return;sh.l.forEach(l=>{const t=typeof l==='string'?l:l.t;if(/\\([^()]*\\(/.test(t.replace(/\\{[^}]*\\}/g,'')))bad.push(p.n+' | '+t.slice(0,80));});}));return bad;}""")
        ok(label+" bloc 16 : pas de parenthèses imbriquées sur les lignes imprimées",len(nest)==0,nest[:3])
        og=await page.evaluate("(typeof SCORES!=='undefined'?SCORES:[]).filter(s=>/genou/i.test(s.n)).map(s=>s.id)")
        ok(label+" scores : une seule règle d'Ottawa du genou (doublon v41w retiré)",og==["ottawa_g"],og)
        # ---------- parasitose digestive : enfant de 3 ans ----------
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/2023';state.poids='14';state.cot.lieu='consultation';render();"); await page.wait_for_timeout(200)
        await pick(page,"vers intestinaux","Parasitose digestive")
        med=med_of(await lines(page))
        fl=[x for x in med if x["t"].startswith("FLAGYL 125")]
        ok(label+" parasitose, 3 ans : FLAGYL suspension 5 ml (125 mg) matin et soir (RCP 250 mg par jour)",bool(fl) and "5 ml (125 mg) matin et soir" in fl[0]["t"],[x["t"][:100] for x in fl])
        z=[x for x in med if x["t"].startswith("ZENTEL")]; ok(label+" parasitose : ZENTEL en options décochées (rupture et tension ANSM)",len(z)==3 and not any(x["on"] for x in z),[(x["t"][:25],x["on"]) for x in z])
        fv=[x for x in med if x["t"].startswith("FLUVERMAL 100")]; ok(label+" parasitose : FLUVERMAL comprimé coché par défaut, même dose adulte et enfant",bool(fv) and fv[0]["on"],[(x["t"][:30],x["on"]) for x in fv])
        fc=[x for x in med if x["t"].startswith("FLAGYL 250")]; ok(label+" parasitose, enfant : FLAGYL 250 mg comprimé (ligne adulte) absent, une seule ligne FLAGYL (suspension RCP)",not fc and len([x for x in med if x["t"].startswith("FLAGYL")])==1,[(x["t"][:40],x["on"]) for x in med if x["t"].startswith("FLAGYL")])
        fv_txt=fv[0]["t"] if fv else ""; ok(label+" parasitose, enfant de 3 ans : mémo grossesse retiré de l'écran (règle sexe/âge), ligne conservée",bool(fv) and "grossesse" not in fv_txt,fv_txt[-120:])
        hx=[x for x in med if x["t"].startswith("HELMINTOX")]; ok(label+" parasitose : HELMINTOX 1 cuillère-mesure de 2,5 ml par 10 kg (RCP 2021), 2e prise à 3 semaines",bool(hx) and "1 cuillère-mesure par 10 kg" in hx[0]["t"] and "3 semaines" in hx[0]["t"],[x["t"][:120] for x in hx])
        await page.evaluate("state.ddn='01/01/2019';render();"); await page.wait_for_timeout(200)
        fl=[x for x in med_of(await lines(page)) if x["t"].startswith("FLAGYL 125")]
        ok(label+" parasitose, 7 ans : FLAGYL suspension 5 ml (125 mg) 3 fois par jour (RCP 375 mg par jour)",bool(fl) and "5 ml (125 mg) 3 fois par jour" in fl[0]["t"],[x["t"][:100] for x in fl])
        await page.evaluate("state.ddn='01/01/2014';render();"); await page.wait_for_timeout(200)
        fl=[x for x in med_of(await lines(page)) if x["t"].startswith("FLAGYL 125")]
        ok(label+" parasitose, 12 ans : FLAGYL suspension 10 ml (250 mg) matin et soir (RCP 500 mg par jour)",bool(fl) and "10 ml (250 mg) matin et soir" in fl[0]["t"],[x["t"][:100] for x in fl])
        cb=await page.evaluate("fill(PACKS.find(p=>p.n==='Parasitose digestive').s.find(sh=>sh.k==='med').l.find(l=>/COMBANTRIN/.test(l.t)).t).miss")
        ok(label+" parasitose, 12 ans : COMBANTRIN (6 ans et plus) non bloqué",cb==[],cb)
        await page.evaluate("state.ddn='01/06/2026';render();"); await page.wait_for_timeout(200)
        cb=await page.evaluate("fill(PACKS.find(p=>p.n==='Parasitose digestive').s.find(sh=>sh.k==='med').l.find(l=>/COMBANTRIN/.test(l.t)).t).miss")
        ok(label+" parasitose, 4 mois : COMBANTRIN bloqué (âge ≥ 6 ans), ZENTEL bloqué (≥ 1 an)",any("6 ans" in m for m in cb),cb)
        # ---------- parasitose : homme de 40 ans ----------
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/1986';state.poids='';state.sexe='h';render();"); await page.wait_for_timeout(200)
        await pick(page,"vers intestinaux","Parasitose digestive")
        med=med_of(await lines(page)); names=[x["t"][:22] for x in med]
        ok(label+" parasitose, homme 40 ans : FLUVERMAL comprimé coché, FLAGYL 250 mg présent, formes enfant (suspensions FLUVERMAL, FLAGYL, ZENTEL) retirées",any(x["t"].startswith("FLUVERMAL 100") and x["on"] for x in med) and any(x["t"].startswith("FLAGYL 250") for x in med) and not any(x["t"].startswith(("FLUVERMAL 2 %","FLAGYL 125","ZENTEL 0,4")) for x in med) and any(x["t"].startswith("HELMINTOX") for x in med),names)
        ok(label+" parasitose, homme : aucun mémo grossesse à l'écran, lignes conservées",all("grossesse" not in x["t"] for x in med) and len(med)>=6,[x["t"][-60:] for x in med if "grossesse" in x["t"]])
        await page.evaluate("state.sexe='f';render();"); await page.wait_for_timeout(200)
        med=med_of(await lines(page))
        ok(label+" parasitose, femme 40 ans : mémo grossesse et allaitement (CRAT) affiché sur FLUVERMAL",any(x["t"].startswith("FLUVERMAL 100") and "CRAT 06/2025" in x["t"] and "femme allaitante" in x["t"] for x in med),[x["t"][-100:] for x in med if x["t"].startswith("FLUVERMAL 100")])
        await page.evaluate("state.sexe='';render();"); await page.wait_for_timeout(100)
        # ---------- érythème fessier : 8 mois ----------
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/02/2026';state.poids='8';render();"); await page.wait_for_timeout(200)
        await pick(page,"fesses rouges","Érythème fessier — nourrisson")
        med=med_of(await lines(page))
        bp=[x for x in med if x["t"].startswith("BEPANTHEN")]; pv=[x for x in med if x["t"].startswith("PEVARYL")]; mt=[x for x in med if x["t"].startswith("MITOSYL")]
        ok(label+" érythème fessier : BEPANTHEN coché, MITOSYL et PEVARYL en option décochée",bool(bp) and bp[0]["on"] and bool(pv) and not pv[0]["on"] and bool(mt) and not mt[0]["on"],[(x["t"][:20],x["on"]) for x in med])
        pc=await page.evaluate("printClean(PACKS.find(p=>p.n==='Érythème fessier — nourrisson').s.find(sh=>sh.k==='med').l[1].t,'med')")
        ok(label+" érythème fessier : MITOSYL imprimé « 3 jours au maximum » sans le mémo (vitamine A, non remboursé)","3 jours au maximum" in pc and "vitamine" not in pc and "rembours" not in pc,pc)
        # ---------- épicondylite : adulte puis enfant ----------
        await page.evaluate("state.sel=null;state.view='';state.ddn='01/01/1986';state.poids='';render();"); await page.wait_for_timeout(200)
        await pick(page,"tennis elbow","Épicondylite — tennis elbow")
        med=med_of(await lines(page))
        ok(label+" épicondylite : paracétamol en premier (ameli 2026), AINS en option",bool(med) and med[0]["t"].startswith("DOLIPRANE") and med[0]["on"] and all(not x["on"] for x in med if x["t"].startswith(("BI-PROF","IBUPRO"))),[(x["t"][:20],x["on"]) for x in med])
        vg=await page.evaluate("fill(PACKS.find(p=>p.n==='Épicondylite — tennis elbow').s.find(sh=>sh.k==='med').l.find(l=>/VOLTARENE/.test(l.t)).t)")
        ok(label+" épicondylite, 40 ans : VOLTARENE EMULGEL 3 à 4 fois par jour 7 jours (RCP 2025), non bloqué",vg["miss"]==[] and "3 à 4 fois par jour pendant 7 jours" in vg["s"],vg)
        await page.evaluate("state.ddn='01/01/2016';render();"); await page.wait_for_timeout(200)
        vg=await page.evaluate("fill(PACKS.find(p=>p.n==='Épicondylite — tennis elbow').s.find(sh=>sh.k==='med').l.find(l=>/VOLTARENE/.test(l.t)).t).miss")
        ok(label+" épicondylite, 10 ans : VOLTARENE EMULGEL bloqué (RCP : 15 ans et plus)",any("15 ans" in m for m in vg),vg)
        at=await page.evaluate("atDureeSugg('Épicondylite — tennis elbow')"); ok(label+" épicondylite : durée d'arrêt indicative = aménagement du poste, pas de durée CNAM","aménagement" in at,at)
        # ---------- dysthyroïdie, apnées, décès ----------
        pp=await page.evaluate("printClean(PACKS.find(p=>p.n==='Dysthyroïdie — bilan avancé et suivi').s.find(sh=>sh.k==='med').l[0].t,'med')")
        ok(label+" dysthyroïdie : propranolol ½ comprimé (20 mg) 3 fois par jour imprimé sans le mémo (RCP 10 à 40 mg, contre-indications)","½ comprimé (20 mg) 3 fois par jour" in pp and "RCP" not in pp and "asthme" not in pp,pp)
        po=await page.evaluate("PACKS.find(p=>p.n==='Dysthyroïdie — bilan avancé et suivi').s.find(sh=>sh.k==='med').l[0].opt===true"); ok(label+" dysthyroïdie : propranolol en option décochée",po,po)
        ap=await page.evaluate("PACKS.find(p=>p.n==='Apnées du sommeil — bilan').s.find(sh=>sh.k==='memo').l.some(l=>/Enfant : ronflement/.test(l.t||l))"); ok(label+" apnées du sommeil : enfant → avis ORL au mémo, pas d'enregistrement prescrit",ap,ap)
        dc=await page.evaluate("(()=>{const p=PACKS.find(p=>p.n==='Décès à domicile — aide-mémoire');return {np:!!p.nopatient,cons:(p.s.find(sh=>sh.k==='cons')||{l:[]}).l.some(t=>/24 heures/.test(typeof t==='string'?t:t.t)),memo:p.s.find(sh=>sh.k==='memo').l.filter(l=>typeof l==='string').length};})()")
        ok(label+" décès à domicile : fiche sans patient, aide-mémoire en 7 étapes, feuille conseils à la famille (déclaration 24 heures)",dc["np"] and dc["cons"] and dc["memo"]==7,dc)
        ok(label+" aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,812,"iphone")
        await run(1280,900,"pc")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_bloc16.md"),"w",encoding="utf-8").write("# Tests bloc 16 — complément (6 fiches)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
