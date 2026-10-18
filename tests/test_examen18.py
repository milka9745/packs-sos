# Examen complet (décision du médecin, 18/10/2026) — bug de l'essai du 17/10 : « Neuro : non renseigné / non effectué » au compte rendu après dictée et répartition IA.
# Express et mode complet, sans IA et avec IA (API simulée, réponse « non renseigné / non effectué » sur les appareils non dictés) :
# exemple de référence (enfant de 3 ans fébrile), neuro normal type inséré et validé d'un geste, neuro dicté anormal conservé (alerte de gravité),
# « Retirer » un appareil, réglage désactivé, aucune mention vide au compte rendu ni au PDF, validation tracée au journal.
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
PORT=8813
KEY="sk-ant-test-0000-cle-factice"
VOID=re.compile(r"non renseign|non effectu|non examin|RAS \?|Neurologique :\s*$|Neuro :\s*$",re.I|re.M)
def api_reply(obj):
    return {"id":"msg_test","type":"message","role":"assistant","model":"claude-sonnet-5-5","stop_reason":"end_turn",
            "content":[{"type":"text","text":json.dumps(obj,ensure_ascii=False)}],"usage":{"input_tokens":1200,"output_tokens":300,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}
D="Fièvre 39 depuis hier, tire l'oreille droite. Tympan droit rouge bombé, gauche normal. Gorge rouge."
ORL="Tympan droit rouge bombé, gauche normal. Gorge rouge."
FICHE="Fièvre — enfant"
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
SETUP="""(a)=>{try{localStorage.setItem('sos_excomplet',a.exc?'1':'0')}catch(e){}newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/06/2023',poids:'15',sexe:'f',date:'18/10/2026'});
  state.sel=PACKS.findIndex(p=>p.n===a.n);state.cot.lieu='visite';state.t0=Date.now();state.obs.dict=a.d;render();return state.sel;}"""
STATE="""()=>{const o={};SYSTEMS.forEach(([k])=>o[k]={v:state.obs[k]||'',auto:examAuto(k)});const cr=buildCR0(currentPack());
  return {o,cr,ok:!!state.examOK,box:(document.querySelector('.obsauto')||{}).innerText||'',
   dictRows:[...document.querySelectorAll('.obsauto .oa-row.dict span')].map(x=>x.textContent),autoRows:[...document.querySelectorAll('.obsauto [data-oa]')].map(x=>x.dataset.oa),
   hl:[...document.querySelectorAll('.obsauto [data-oa]:not(.ok)')].map(x=>x.dataset.oa),btn:document.querySelectorAll('#oa_ok').length,
   alerts:[...document.querySelectorAll('.oa-grav,.xp-al')].map(x=>x.textContent).join(' | ')};}"""
async def repartir(page,ia,replies,obsIA):
    if not ia:
        await page.locator("#dict_go2").first.click(); await page.wait_for_timeout(400); return
    replies.append(api_reply({"packs":[FICHE],"poids":"","sexe":"","grossesse":False,"allaitement":False,"allergie_penicilline":False,"allergies":[],"traitements":[],"cst":{"temp":"39"},"obs":obsIA,"remarques":[]}))
    await page.evaluate("document.getElementById('aipanel')&&document.getElementById('aipanel').remove();aiOpen('obs')"); await page.wait_for_timeout(200)
    await page.fill("#ai_in",await page.evaluate("state.obs.dict")); await page.click("#ai_go"); await page.wait_for_timeout(300)
    await page.click("#ai_send"); await page.wait_for_timeout(800); await page.click("#ai_apply"); await page.wait_for_timeout(500)
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for xp in (True,False):
                for ia in (False,True):
                    L=f"{'Express' if xp else 'mode complet'} · {'avec IA' if ia else 'sans IA'} : "
                    ctx=await b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
                    replies=[]
                    async def handle(route):
                        cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
                        if route.request.method=="OPTIONS": await route.fulfill(status=204,headers=cors); return
                        r=replies.pop(0) if replies else api_reply({})
                        await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps(r,ensure_ascii=False))
                    await ctx.route("https://api.anthropic.com/**",handle)
                    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.fallback() if "anthropic" in r.request.url else (r.continue_() if "localhost" in r.request.url else r.abort())))
                    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
                    await unlock(page,"ex"+("x" if xp else "c")+("i" if ia else "s"),xp)
                    if ia: await page.evaluate(f"AI.key={json.dumps(KEY)};AI.cfg.mode='partiel';aiSave();"); await page.wait_for_timeout(400)
                    IA_OBS={"hist":"Fièvre 39 depuis hier, tire l'oreille droite.","orl":ORL,"neuro":"non renseigné / non effectué","cut":"RAS ?","gen":"","cv":"Cardio :","hyp":""}
                    # 1. exemple de référence
                    await page.evaluate(SETUP,{"n":FICHE,"d":D,"exc":True}); await repartir(page,ia,replies,IA_OBS)
                    st=await page.evaluate(STATE)
                    ok(L+"référence : ORL = texte dicté, intact, non surligné",st["o"]["orl"]["v"]==ORL and not st["o"]["orl"]["auto"] and any("ORL" in x for x in st["dictRows"]),(st["o"]["orl"],st["dictRows"]))
                    exp=["gen","cv","resp","abdo","neuro","cut"]
                    ok(L+"référence : Général, Cardio, Pulmonaire, Abdomen, Neuro, Cutané = normaux types surlignés",all(st["o"][k]["auto"] for k in exp) and set(exp)<=set(st["hl"]),(st["hl"],{k:st["o"][k] for k in exp}))
                    ok(L+"neuro absent de la dictée"+(" (IA : « non renseigné / non effectué »)" if ia else "")+" → normal type inséré",st["o"]["neuro"]["auto"] and "nuque souple" in st["o"]["neuro"]["v"],st["o"]["neuro"])
                    ok(L+"un seul bouton « ✓ Examen complet »",st["btn"]==1 and "✓ Examen complet" in st["box"],st["btn"])
                    if xp and not ia:
                        await page.evaluate("document.querySelector('.obsauto').scrollIntoView({block:'start'})"); await page.wait_for_timeout(200)
                        await page.screenshot(path=os.path.join(OUT,"examen18-reference-express.png"),full_page=False)
                    await page.locator("[data-oadel='cut']").first.click(); await page.wait_for_timeout(300)
                    await page.locator("#oa_ok").first.click(); await page.wait_for_timeout(400)
                    st=await page.evaluate(STATE)
                    cr=st["cr"]; exl=[l for l in cr.split("\n") if l.startswith("Examen : ")]
                    ok(L+"« Retirer » Cutané : absent du compte rendu, sans mention",not st["o"]["cut"]["v"] and "Cutané" not in cr and "Peau sans" not in cr,cr[-600:])
                    ok(L+"validé d'un geste : plus de surlignage, plus de bouton",st["ok"] and not st["hl"] and st["btn"]==0,(st["ok"],st["hl"],st["btn"]))
                    ok(L+"compte rendu : un seul paragraphe « Examen : … », texte dicté intact",len(exl)==1 and ORL.rstrip(".") in exl[0] and "Neurologique : Contact adapté à l'âge ; nuque souple" in exl[0],exl)
                    ok(L+"compte rendu : jamais « non renseigné », « non effectué », « non examiné », « RAS ? » ni libellé seul, ni surlignage",not VOID.search(cr) and "à valider" not in cr and "normal type" not in cr,[m.group(0) for m in VOID.finditer(cr)])
                    jn=await page.evaluate("(()=>{const e=JOURNAL.slice().reverse().find(x=>x.patient==='PETIT Lou');return e?{notes:e.notes||[],exam:e.exam||null}:null})()")
                    ok(L+"validation tracée au journal (heure, normaux types, appareil retiré)",jn and jn["exam"] and any(n.startswith("Examen complet validé") and "Cutané" in n and "Neurologique" in n for n in jn["notes"]),jn)
                    await page.evaluate("printPack()"); await page.wait_for_timeout(600)
                    if await page.locator("#ciover").count():
                        await page.click("#ci_keep"); await page.click("#ci_print")
                    try: await page.wait_for_selector("#print .page",timeout=15000)
                    except Exception: pass
                    pr=await page.evaluate("(document.getElementById('print')||{}).innerText||''")
                    hl=await page.evaluate("document.querySelectorAll('#print .autoins,#print .obsauto,#print .oa-tag').length")
                    ok(L+"PDF : aucun surlignage ni mention vide",hl==0 and not VOID.search(pr) and "à valider" not in pr,(hl,pr[:200]))
                    await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel()}catch(e){};state.view='';render();")
                    # 2. neuro dicté anormal
                    await page.evaluate(SETUP,{"n":FICHE,"d":D+" Nuque un peu raide.","exc":True})
                    await repartir(page,ia,replies,dict(IA_OBS,neuro="Nuque un peu raide."))
                    st=await page.evaluate(STATE)
                    ok(L+"neuro dicté anormal : phrase dictée conservée, aucun normal ajouté",st["o"]["neuro"]["v"]=="Nuque un peu raide." and not st["o"]["neuro"]["auto"],st["o"]["neuro"])
                    ok(L+"neuro dicté anormal : alerte de gravité de la fiche à l'écran","nuque un peu raide" in st["alerts"].lower() and "Gravité" in st["alerts"],st["alerts"][:300])
                    ok(L+"alerte de gravité jamais écrite au compte rendu","Signe de gravité" not in st["cr"] and "Élément de gravité" not in st["cr"] and "Nuque un peu raide" in st["cr"],st["cr"][-400:])
                    # 3. réglage désactivé : champ vide = absent du compte rendu
                    await page.evaluate(SETUP,{"n":FICHE,"d":D,"exc":False}); await repartir(page,ia,replies,IA_OBS)
                    st=await page.evaluate(STATE)
                    exl=[l for l in st["cr"].split("\n") if l.startswith("Examen : ")]
                    ok(L+"réglage désactivé : seuls les appareils dictés, aucune ligne pour les champs vides",len(exl)==1 and exl[0]=="Examen : ORL : "+ORL.rstrip(".")+"." and not any(st["o"][k]["auto"] for k in st["o"]),exl)
                    ok(L+"réglage désactivé : jamais de mention vide ni « Examen clinique non renseigné »",not VOID.search(st["cr"]) and "non renseign" not in st["cr"],[m.group(0) for m in VOID.finditer(st["cr"])])
                    # 3 bis. réglage désactivé et rien de dicté sur l'examen
                    await page.evaluate(SETUP,{"n":FICHE,"d":"Fièvre depuis hier.","exc":False}); await page.evaluate("applyDictation()")
                    cr=await page.evaluate("buildCR0(currentPack())")
                    ok(L+"réglage désactivé, aucun examen dicté : ni rubrique d'examen vide ni « non renseigné »","Examen : " not in cr and "non renseign" not in cr,cr[:500])
                    # 4. validation du patient sans « ✓ » : 1er toucher → encadré, patient non validé ; 2e toucher → examen et patient validés (jamais de fenêtre système)
                    await page.evaluate(SETUP,{"n":FICHE,"d":D,"exc":True}); await page.evaluate("applyDictation();examGate._w=0;")
                    v1=await page.evaluate("(()=>{patientValidate();return {view:state.view,ok:!!state.examOK};})()")
                    v2=await page.evaluate("(()=>{patientValidate();const v=VALID.last||{};return {view:state.view,ok:!!state.examOK,exam:!!v.exam};})()")
                    ok(L+"validation sans « ✓ » : 1er toucher montre l'examen, 2e toucher valide examen et patient (tracé)",v1["view"]!="valid" and not v1["ok"] and v2["view"]=="valid" and v2["exam"],[v1,v2])
                    # 4. réglage réactivé depuis l'encadré
                    await page.evaluate("localStorage.setItem('sos_excomplet','1');render();")
                    ok(L+"aucune erreur JS",not errors,errors[:3])
                    await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_examen18.md"),"w",encoding="utf-8").write("# Examen complet (18/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
