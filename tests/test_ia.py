# Tests navigateur v41 — assistant IA facultatif (API Anthropic simulée : aucun appel réel, aucune donnée réelle)
# Prérequis : pip install playwright puis python -m playwright install chromium ; lancer : python tests/test_ia.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

KEY="sk-ant-test-0000-cle-factice"
IDENT=["DUPONT","Dupont","Marie-Claire","1985","12/03","06 12 34 56 78","0612345678","Lilas","45000","Lemoine"]

def api_reply(obj,inp=1200,out=300):
    return {"id":"msg_test","type":"message","role":"assistant","model":"claude-sonnet-5-5","stop_reason":"end_turn",
            "content":[{"type":"text","text":json.dumps(obj,ensure_ascii=False)}],
            "usage":{"input_tokens":inp,"output_tokens":out,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}

async def unlock(page):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
    await page.goto("http://localhost:8766/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testv41"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
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

async def run(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":height},is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page()
        errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        sent=[]; replies=[]
        async def handle(route):
            req=route.request
            cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
            if req.method=="OPTIONS":
                await route.fulfill(status=204,headers=cors); return
            sent.append({"headers":req.headers,"body":req.post_data or ""})
            r=replies.pop(0) if replies else api_reply({})
            await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps(r,ensure_ascii=False))
        await ctx.route("https://api.anthropic.com/**",handle)
        await unlock(page)
        L=label+" "
        ok(L+"version 41",await page.evaluate("APP_VERSION")=="41")
        # 1. Sans clé : mode Aucun, rien ne part
        ok(L+"sans clé : mode Aucun",await page.evaluate("aiEffective().mode")=="aucun")
        ok(L+"bouton IA affiché « Aucun »","Aucun" in (await page.evaluate("aiBtnHTML()")))
        await page.evaluate("aiOpen()"); await page.wait_for_timeout(200)
        ok(L+"panneau : IA coupée, aucun champ d'envoi",await page.locator("#aipanel").count()==1 and await page.locator("#ai_go").count()==0)
        await page.evaluate("document.getElementById('aipanel').remove()")
        # 2. Clé : chiffrée dans le profil, jamais en clair, jamais dans la sauvegarde
        await page.evaluate(f"AI.key={json.dumps(KEY)};AI.cfg.mode='partiel';aiSave();"); await page.wait_for_timeout(500)
        ls=await page.evaluate("JSON.stringify(Object.assign({},localStorage))")
        ok(L+"clé API absente en clair du stockage",KEY not in ls and "sos_ai_enc" in ls and '"sos_ai"' not in ls)
        bak=await page.evaluate("backupCollect().then(x=>JSON.stringify(x))")
        ok(L+"clé API absente de la sauvegarde",KEY not in bak and "sos_ai" not in json.loads(bak)["enc"])
        ok(L+"clé relue après déchiffrement",await page.evaluate("secGet('sos_ai',null).then(c=>c&&c.key)")==KEY)
        # 2 bis. Noms de médicaments jamais masqués (base intégrée, puis BDPM importée)
        mw=await page.evaluate("[aiMedWords().size,['eliquis','januvia','aricept','metformine','kardegic'].every(w=>aiMedWords().has(w))]")
        ok(L+"lexique médicaments : base intégrée chargée",mw[0]>3000 and mw[1],mw)
        await page.evaluate("state.patient='DUPONT Marie-Claire';state.ddn='12/03/1985';state.t0=Date.now()-1;aiPrepare('obs',{dictee:'Mme Dupont sous Januvia, Aricept et Lyrica, Tercian le soir.'})"); await page.wait_for_timeout(300)
        txt=await page.inner_text("#ai_sent")
        ok(L+"médicaments absents des fiches envoyés en clair, patiente masquée",all(x in txt for x in ["Januvia","Aricept","Lyrica","Tercian"]) and "Dupont" not in txt,txt[-200:])
        await page.click("#ai_cancel")
        await page.evaluate("BDPM={ts:Date.now(),n:1,rows:['ZORGLUBINE 10 mg, comprimé pelliculé|comprimé pelliculé']}")
        ok(L+"spécialité de la BDPM importée ajoutée au lexique",await page.evaluate("aiMedWords().has('zorglubine')"))
        await page.evaluate("BDPM=lsGet('sos_bdpm',null)")
        # 3. Consultation fictive avec identité complète
        await page.evaluate("""()=>{const i=PACKS.findIndex(p=>/Cystite simple/.test(p.n));state.sel=i;state.patient='DUPONT Marie-Claire';state.ddn='12/03/1985';state.date='15/10/2026';state.sexe='f';state.t0=Date.now();state.cot.lieu='consultation';render();}""")
        dictee="Mme Dupont Marie-Claire, née le 12/03/1985, 12 rue des Lilas 45000 Orléans, tél 06 12 34 56 78. Brûlures mictionnelles depuis le 13/10/2026, vue par le Dr Lemoine. Toux absente. Pas de fièvre, TA 12/7."
        await page.evaluate("aiOpen('obs')"); await page.wait_for_timeout(200)
        await page.fill("#ai_in",dictee); await page.click("#ai_go"); await page.wait_for_timeout(300)
        ok(L+"écran « Ce qui part » ouvert avant tout envoi",await page.locator("#aisend").count()==1 and len(sent)==0)
        txt=await page.inner_text("#ai_sent")
        ok(L+"texte envoyé sans nom, naissance, adresse, téléphone ni médecin",not any(x in txt for x in IDENT),[x for x in IDENT if x in txt])
        ok(L+"naissance remplacée par l'âge, date par J-2","[[ÂGE : 41 ans]]" in txt and "[[J-2]]" in txt,txt[:300])
        items=await page.inner_text(".aiitems")
        ok(L+"liste de ce qui est retiré affichée sur l'appareil","Dupont" in items and "Lilas" in items)
        await page.locator("#ai_sent .aiw",has_text="Toux").first.click(); await page.wait_for_timeout(300)
        txt=await page.inner_text("#ai_sent")
        ok(L+"mot masqué à la main sur l'écran de contrôle","Toux" not in txt and "[[MASQUÉ 1]]" in txt)
        # 4. Envoi simulé, réintégration, garde-fous
        replies.append(api_reply({"packs":["Cystite simple — femme"],"poids":"","sexe":"f","grossesse":False,"allaitement":False,"allergie_penicilline":False,"allergies":[],"traitements":[],
            "cst":{"ta":"12/7","spo2":"99"},"obs":{"hist":"[[PRÉNOM DU PATIENT]] décrit des brûlures mictionnelles depuis [[J-2]].","hyp":"Cystite aiguë simple","gen":"SpO2 99 %, bon état général","abdo":"Prendre FOSFOMYCINE 3 g en une prise"},"remarques":[]}))
        await page.click("#ai_send"); await page.wait_for_timeout(800)
        ok(L+"un seul envoi",len(sent)==1,len(sent))
        body=sent[0]["body"] if sent else ""
        ok(L+"requête sans aucune donnée identifiante",not any(x in body for x in IDENT),[x for x in IDENT if x in body])
        ok(L+"clé envoyée seulement dans l'en-tête",sent and sent[0]["headers"].get("x-api-key")==KEY and KEY not in body)
        jb=json.loads(body) if body else {}
        ok(L+"consignes fixes en cache, Sonnet pour rédiger",jb.get("model")=="claude-sonnet-5-5" and jb.get("system",[{}])[0].get("cache_control",{}).get("type")=="ephemeral")
        out=await page.inner_text("#ai_out")
        ok(L+"identité réintégrée sur l'appareil","Marie-Claire décrit" in out and "13/10/2026" in out,out[:300])
        ok(L+"constante inventée écartée (SpO2 99 absente de la dictée)","Écarté" in out and await page.evaluate("!AI.res.apply.cst.spo2&&!AI.res.apply.obs.gen"))
        ok(L+"posologie proposée par l'IA jamais appliquée",await page.evaluate("!AI.res.apply.obs.abdo||!/3 g/.test(AI.res.apply.obs.abdo)"))
        nlines=await page.evaluate("JSON.stringify(state.extra)")
        await page.click("#ai_apply"); await page.wait_for_timeout(400)
        ok(L+"observation appliquée, identité réelle dans le dossier",await page.evaluate("state.obs.hist")=="Marie-Claire décrit des brûlures mictionnelles depuis 13/10/2026.")
        ok(L+"aucune ligne d'ordonnance créée par l'IA",await page.evaluate("JSON.stringify(state.extra)")=="{}")
        ok(L+"trace de la modification par l'IA",await page.evaluate("(state.aiLog||[]).length")>=1)
        # 5. Consommation
        use=await page.evaluate("AI.use.map(u=>({f:u.f,eur:u.eur,model:u.model,keys:Object.keys(u)}))")
        ok(L+"coût enregistré sans donnée identifiante",len(use)==1 and use[0]["eur"]>0 and set(use[0]["keys"])<={"ts","f","model","in","out","cr","cw","eur","pid","gk"},use)
        await page.evaluate("aiConsoScreen()"); await page.wait_for_timeout(200)
        ct=await page.inner_text("#aiconso")
        ok(L+"écran Consommation : jour, garde, mois, par usage, par modèle, par patient",all(x in ct for x in ["Aujourd'hui","Garde en cours","Mois","Par usage","Par modèle","Coût moyen par patient","Plafond mensuel"]))
        await page.fill("#ac_cap","0,000001"); await page.click("#ac_save"); await page.wait_for_timeout(300)
        eff=await page.evaluate("aiEffective()")
        ok(L+"plafond atteint : passage automatique en Aucun",eff["mode"]=="aucun" and "plafond" in eff["why"],eff)
        await page.evaluate("document.getElementById('aiconso').remove();AI.cfg.cap=10;aiSave();")
        # 6. Hors connexion : aucun envoi
        await ctx.set_offline(True); await page.wait_for_timeout(200)
        ok(L+"hors connexion : passage automatique en Aucun",await page.evaluate("aiEffective().mode")=="aucun")
        n0=len(sent); r=await page.evaluate("aiPrepare('obs',{dictee:'test'})===null")
        ok(L+"hors connexion : rien n'est préparé ni envoyé",r and len(sent)==n0)
        ok(L+"hors connexion : demande mise en attente sur l'appareil (n° 6), jamais envoyée",await page.evaluate("AIQ.list.length")>=1 and len(sent)==n0)
        await page.evaluate("AIQ.list=[];aiqSave();netUI();")
        await ctx.set_offline(False); await page.wait_for_timeout(200)
        # 7. Compte rendu + courrier en un seul envoi
        await page.evaluate("""()=>{const i=PACKS.findIndex(p=>p.s.some(sh=>sh.k==='let')&&p.s.some(sh=>sh.k==='med'));state.sel=i;state.obs.hist='Brûlures mictionnelles, patiente très inquiète.';state.obs.dictated=true;state.obsOpen=true;render();}""")
        await page.evaluate("aiPrepare('cr',{cr:true,let:true,demande:'urologue'})"); await page.wait_for_timeout(300)
        txt=await page.inner_text("#ai_sent")
        ok(L+"compte rendu envoyé sans identité",not any(x in txt for x in IDENT),[x for x in IDENT if x in txt])
        replies.append(api_reply({"manques":["Consignes de reconsultation non tracées"],"reformulations":[{"rubrique":"Histoire","avant":"patiente très inquiète","apres":"patiente inquiète"}],
            "raisonnement":"Tableau typique sans signe de gravité, prise en charge ambulatoire.","information":"Consignes expliquées à [[PATIENT]].",
            "courrier":{"dest":"Cher confrère,","paragraphs":["Je vous adresse [[PATIENT]] pour avis.","Elle prend FOSFOMYCINE 3 g en une prise unique.","Pourriez-vous la recevoir ?"],"fin":"Bien confraternellement."}}))
        await page.click("#ai_send"); await page.wait_for_timeout(800)
        jb=json.loads(sent[-1]["body"]);
        ok(L+"compte rendu et courrier : un seul appel",len(sent)==n0+1 and "Courrier demandé" in jb["messages"][0]["content"])
        out=await page.inner_text("#ai_out")
        ok(L+"manques signalés avant validation","reconsultation" in out)
        ok(L+"courrier : identité réintégrée, posologie de l'IA retirée","Je vous adresse DUPONT Marie-Claire" in out and "FOSFOMYCINE 3 g" not in out and "Posologie retirée" in out,out[-500:])
        ok(L+"courrier : traitement repris de la fiche par Packs","Traitement prescrit ce jour" in out)
        await page.locator("[data-acc=rf0]").click(); await page.locator("[data-acc=raison]").click(); await page.wait_for_timeout(300)
        ok(L+"reformulation acceptée, faits conservés",await page.evaluate("state.obs.hist")=="Brûlures mictionnelles, patiente inquiète.")
        cr=await page.evaluate("buildCR0(currentPack())")
        ok(L+"raisonnement ajouté au compte rendu","Tableau typique sans signe de gravité" in cr)
        await page.evaluate("document.getElementById('aipanel')&&document.getElementById('aipanel').remove()")
        # 8. Mode Complet : l'écran de contrôle s'ouvre seul après la dictée, sans envoi
        await page.evaluate("AI.cfg.mode='complet';AI.cfg.send='auto';aiSave();state.obs.dict='Douleur lombaire depuis J2';state.obsOpen=true;render();"); await page.wait_for_timeout(300)
        n1=len(sent); await page.click("#dict_go")
        for _ in range(30):
            if len(sent)>n1: break
            await page.wait_for_timeout(150)
        await page.wait_for_timeout(500)
        ok(L+"Complet (20/10/2026) : dictée envoyée automatiquement après pseudonymisation, une seule requête, sans identité, sans écran intermédiaire",len(sent)==n1+1 and "Dupont" not in sent[-1]["body"] and await page.locator("#aisend").count()==0 and await page.evaluate("!!state.aiPlan"),(len(sent)-n1,await page.locator("#aisend").count()))
        await page.evaluate("AI.cfg.send='ecran';aiSave();AI._planHash='';state.obs.dict='Douleur lombaire depuis J2, irradiant à droite';render();"); await page.wait_for_timeout(200)
        n1=len(sent); await page.click("#dict_go"); await page.wait_for_timeout(900)
        ok(L+"Complet avec réglage « écran à chaque fois » : « Ce qui part » ouvert, rien n'est parti",await page.locator("#aisend").count()==1 and len(sent)==n1)
        await page.click("#ai_cancel"); await page.evaluate("AI.cfg.send='auto';aiSave();")
        # 9. Mode en un geste depuis le menu ⋯ (téléphone) ou le panneau
        if width<500:
            await page.click("#more_btn"); await page.wait_for_timeout(200)
            await page.locator("#jmenu [data-aimode=aucun]").click(); await page.wait_for_timeout(300)
        else:
            await page.evaluate("aiOpen()"); await page.locator("#aipanel [data-aimode=aucun]").click(); await page.wait_for_timeout(300)
        ok(L+"mode Aucun en un geste",await page.evaluate("AI.cfg.mode")=="aucun" and await page.evaluate("aiEffective().mode")=="aucun")
        await page.evaluate("document.getElementById('aipanel')&&document.getElementById('aipanel').remove()")
        await page.screenshot(path=os.path.join(ROOT,"tests","captures",f"{label}-ia-aucun.png"))
        await page.evaluate("AI.cfg.mode='partiel';aiSave();aiPrepare('obs',{dictee:'Mme Dupont, toux depuis le 12/10/2026.'})"); await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(ROOT,"tests","captures",f"{label}-ia-ce-qui-part.png"),full_page=False)
        ok(L+"aucune erreur JS",len(errors)==0,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8766"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,812,"iphone")
        await run(1280,900,"pc")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_ia.md"),"w",encoding="utf-8").write("# Tests v41 — assistant IA (API simulée)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
