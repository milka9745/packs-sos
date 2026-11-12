# -*- coding: utf-8 -*-
# 06/11/2026 (v41z) — (1) l'impression aboutit à chaque étape du fil (Consultation, Visite, iPhone, ordinateur ; écran « Avant d'imprimer » sans clavier ni barre qui recouvre ; PDF),
# (2) Consultation : « Patient suivant » en un geste (validation puis patient vierge, annulation 8 s), (3) Visite : aucune fiche proposée, recherche vide, fréquents, réglage,
# (4) certificats enfant malade et absence scolaire (dates d'un geste, date de naissance, heure, une page, journal, sans secret médical).
# Patients fictifs ; aucun appel externe. Lancer : python tests/test_fil_v41z.py
import asyncio, os, re, json, subprocess, sys, time, datetime
from playwright.async_api import async_playwright
IOS_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"  # 07/11/2026 : iPhone réel (iosLike) → PDF partagé ; sans cet UA, 375 px = fenêtre d'impression du navigateur
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,"tests","captures"); PORT=8872
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:900])
STOPS="""()=>{TOUR.stops=[];TOUR.order=[];TOUR.current='';TOUR.computed=false;delete TOUR.started;newPatient();state.cot.lieu='visite';state.cot.auto=false;
  const a=tourAdd('12 rue des Lilas 45000 Orléans','DUPONT Jean',false,{lat:47.9,lon:1.9,label:'12 rue des Lilas',city:'Orléans'});Object.assign(a,{nom:'DUPONT Jean',ddn:'01/01/1950',tel:'0612345678',motif:'douleur lombaire'});TOUR.order=[a.id];tourSave();render();return a.id;}"""
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_excomplet','0');}}catch(e){{}}")
    await page.add_init_script("window.navOpen=u=>{window.__navOpened=(window.__navOpened||[]).concat([u]);};")  # 12/11/2026 : guidage relevé, jamais lancé pendant les tests
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=20000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=20000); await page.wait_for_timeout(600)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
    await page.evaluate("()=>{window.__printed=0;window.print=()=>{window.__printed++;};}")  # 07/11/2026 : l'impression = fenêtre du navigateur sur l'aperçu (ordinateur, 375 px) ; iPhone réel (UA iOS) = PDF partagé
def dmy(d): return d.strftime("%d/%m/%Y")
async def open_print(page,L,expect_ci):
    """touche le bouton d'impression de la barre (Express : 2 touchers, le 1er arme) ; passe l'écran « Avant d'imprimer » s'il s'ouvre ; retourne l'état"""
    sel="#xp_go" if await page.locator("#xp_go").count() else "#fin"
    await page.click(sel); await page.wait_for_timeout(500)
    if sel=="#xp_go" and not await page.locator("#ciover").count() and not await page.evaluate("()=>document.body.classList.contains('printing')"):
        await page.click(sel); await page.wait_for_timeout(600)
    ci=await page.locator("#ciover").count()
    info={"sel":sel,"ci":bool(ci)}
    if ci:
        st=await page.evaluate("()=>({focus:document.activeElement&&document.activeElement.id,dock:(()=>{const d=document.getElementById('fdock');return d?getComputedStyle(d).display:'absent';})(),keep:!!document.getElementById('ci_keep')})")
        await page.click("#ci_keep"); await page.wait_for_timeout(300)
        st2=await page.evaluate("()=>{const b=document.getElementById('ci_print');const r=b.getBoundingClientRect();const el=document.elementFromPoint(r.left+r.width/2,Math.min(innerHeight-1,r.top+r.height/2));return {focus:document.activeElement&&document.activeElement.id,inView:r.top>=0&&r.bottom<=innerHeight,hit:!!(el&&(el===b||b.contains(el)))};}")
        info.update(st); info["step2"]=st2
        await page.click("#ciover [data-cichip]"); await page.click("#ci_print"); await page.wait_for_timeout(700)
    info["printing"]=await page.evaluate("()=>document.body.classList.contains('printing')"); info["pages"]=await page.evaluate("()=>document.querySelectorAll('#print .page').length")
    ok(L+("écran « Avant d'imprimer » puis " if ci else "")+"aperçu ouvert dès le bouton de la barre"+(" (confirmation au 2e toucher en Express)" if sel=="#xp_go" else ""),info["printing"] and info["pages"]>=1 and (ci==bool(expect_ci)),info)
    if ci:
        ok(L+"écran « Avant d'imprimer » : barre du bas masquée, pas de clavier (champ Motif non pris au focus sur iPhone), bouton « Imprimer » visible et atteignable",
           info["dock"]=="none" and (info["step2"]["focus"]!="ci_why" or not info.get("phone")) and info["step2"]["inView"] and info["step2"]["hit"],info)
    return info
async def pdf_and_back(page,L,pc):
    if pc:
        n0=await page.evaluate("()=>window.__printed"); await page.evaluate("()=>document.getElementById('pb_print').click()")
        try: await page.wait_for_function("(n0)=>window.__printed>n0",arg=n0,timeout=30000)
        except Exception: pass
        ok(L+"ordinateur : « Imprimer » de l'aperçu ouvre la fenêtre d'impression du navigateur tout de suite, sans PDF (07/11/2026)",await page.evaluate("()=>window.__printed")>n0 and await page.evaluate("()=>!PDFJOB.busy&&!PDFJOB.file"),{"printed":await page.evaluate("()=>window.__printed"),"st":await page.evaluate("()=>(document.getElementById('pdf_st')||{}).textContent||''")})
    await page.evaluate("()=>document.getElementById('pb_pdf').click()"); await page.wait_for_function("()=>(PDFJOB&&PDFJOB.file)||/enregistr|prêt|Partager/.test((document.getElementById('pdf_st')||{}).textContent||'')",timeout=30000)
    st=await page.evaluate("()=>({file:!!(PDFJOB&&PDFJOB.file),n:PDFJOB&&PDFJOB.n,msg:(document.getElementById('pdf_st')||{}).textContent||''})")
    ok(L+"« Enregistrer en PDF » : PDF préparé et remis",st["file"] or "enregistr" in st["msg"],st)
    await page.evaluate("()=>(document.getElementById('pb_back')||document.getElementById('pb_back2')).click()"); await page.wait_for_timeout(400)
    ok(L+"retour à la fiche après l'aperçu, barre du bas de retour",not await page.evaluate("()=>document.body.classList.contains('printing')") and await page.locator("#fdock").count()==1)
async def run(b,w,h,xp,label,tag):
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if w<500 else 1,is_mobile=w<500,has_touch=w<500,**({"user_agent":IOS_UA} if w<500 else {}))
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,"fil"+tag,xp); L=label+" : "; phone=w<500; pc=not phone
    # ---------- 1. Consultation : impression à chaque étape ----------
    await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"); await page.wait_for_timeout(500)
    st=await page.evaluate("()=>({fil:filState(),btn:(document.querySelector('#xp_go,#fin')||{}).textContent||''})")
    ok(L+"consultation, fiche choisie : état « prise en charge », bouton d'impression dans la barre",st["fil"]=="pec" and ("Imprimer" in st["btn"]),st)
    info=await open_print(page,L+"consultation · ",False); info["phone"]=phone
    if phone: await page.screenshot(path=os.path.join(OUT,f"fil-{tag}-apercu.png"))
    await pdf_and_back(page,L+"consultation · ",pc)
    st=await page.evaluate("()=>({fil:filState(),rep:!!document.getElementById('tc_reprint'),next:(document.getElementById('fa_next_c')||{}).textContent||''})")
    ok(L+"après impression : état « sortie », « Réimprimer » et « ✓ Patient suivant » dans la barre (consultation)",st["fil"]=="sortie" and st["rep"] and "Patient suivant" in st["next"],st)
    await page.click("#tc_reprint"); await page.wait_for_timeout(600)
    ok(L+"« Réimprimer » rouvre l'aperçu (étape sortie)",await page.evaluate("()=>document.body.classList.contains('printing')&&document.querySelectorAll('#print .page').length>=1"))
    await pdf_and_back(page,L+"réimpression · ",pc)
    # ---------- 2. Consultation : patient suivant en un geste ----------
    if phone: await page.screenshot(path=os.path.join(OUT,f"fil-{tag}-sortie-consultation.png"))
    n0=await page.evaluate("()=>JOURNAL.length"); v0=await page.evaluate("()=>VALID.hist.length")
    await page.click("#fa_next_c"); await page.wait_for_timeout(300)
    armed=await page.evaluate("()=>(document.getElementById('fa_next_c')||{}).textContent||''")
    await page.click("#fa_next_c"); await page.wait_for_timeout(600)
    st=await page.evaluate("()=>({patient:state.patient,lieu:state.cot.lieu,manual:!!state.xpManual,view:state.view,valid:VALID.hist.length,j:JOURNAL.length,last:VALID.hist[0]&&VALID.hist[0].patient,cot:VALID.hist[0]&&VALID.hist[0].cot&&VALID.hist[0].cot.codes,undo:!!document.getElementById('undobar'),dock:!!document.getElementById('fdock'),fil:filState()})")
    ok(L+"« ✓ Patient suivant » (confirmation au 2e toucher) : patient validé (journal, cotation), patient vierge ouvert aussitôt en Consultation, sans écran de liste, annulation proposée 8 s",
       "Confirmer" in armed and st["patient"]=="" and st["lieu"]=="consultation" and st["manual"] and st["view"]=="" and st["valid"]==v0+1 and st["last"]=="DURAND Martine" and st["cot"] and st["j"]>=n0 and st["undo"] and st["dock"],st)
    if phone: await page.screenshot(path=os.path.join(OUT,f"fil-{tag}-patient-suivant.png"))
    await page.click("#undo_go"); await page.wait_for_timeout(500)
    st=await page.evaluate("()=>({patient:state.patient,undo:!!document.getElementById('undobar')})")
    ok(L+"« Annuler » dans les 8 s : le patient validé est rouvert",st["patient"]=="DURAND Martine" and not st["undo"],st)
    # ---------- 1 bis. Visite : écran « Avant d'imprimer » puis aperçu ----------
    sid=await page.evaluate(STOPS); await page.wait_for_timeout(300)
    await page.evaluate("(id)=>{TOUR.current=id;const s=tourStop(id);s.tArr=Date.now();Object.assign(state,{patient:'DUPONT Jean',ddn:'01/01/1950',sexe:'h'});state.cot.lieu='visite';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.view='';render();}",sid); await page.wait_for_timeout(500)
    info=await open_print(page,L+"visite (76 ans, AINS) · ",True); info["phone"]=phone
    if phone and info.get("ci"): pass
    await pdf_and_back(page,L+"visite · ",pc)
    st=await page.evaluate("()=>({fil:filState(),valid:(document.getElementById('tc_valid')||{}).textContent||''})")
    ok(L+"visite après impression : « Valider · patient suivant » inchangé",st["fil"]=="sortie" and "patient suivant" in st["valid"],st)
    # ---------- 3. Visite : aucune fiche proposée, recherche vide, fréquents, réglage ----------
    if xp:
        await page.evaluate("()=>{newPatient();TOUR.current='';}"); sid=await page.evaluate(STOPS); await page.wait_for_timeout(200)
        await page.evaluate("(id)=>xpOpenStop(id)",sid); await page.wait_for_timeout(400)
        st=await page.evaluate("()=>({ok:!!document.getElementById('xp_ok'),nosug:!!document.querySelector('.xp-prop.nosug'),btn:(document.getElementById('xp_list')||{}).textContent||'',motif:xpMotif(),sel:state.sel})")
        ok(L+"visite avec motif de régulation « douleur lombaire » : aucune fiche proposée, « Choisir une fiche » à la place",not st["ok"] and st["nosug"] and "Choisir" in st["btn"] and st["motif"]=="douleur lombaire" and st["sel"] is None,st)
        await page.click("#xp_list"); await page.wait_for_timeout(300)
        st=await page.evaluate("()=>({q:(document.getElementById('xp_q')||{}).value,cands:document.querySelectorAll('#xp_prop .xp-cand').length,hint:(document.querySelector('#xp_prop .hint')||{}).textContent||''})")
        ok(L+"la recherche s'ouvre vide, avec les fiches fréquentes",st["q"]=="" and st["cands"]>=5 and "fréquentes" in st["hint"],st)
        if phone: await page.screenshot(path=os.path.join(OUT,f"fil-{tag}-visite-sans-proposition.png"))
        await page.fill("#xp_q","lombalgie"); await page.wait_for_timeout(400)
        st=await page.evaluate("()=>({cands:[...document.querySelectorAll('#xp_prop .xp-cand')].map(b=>b.textContent),motif:xpMotif()})")
        ok(L+"recherche par mots-clés : « lombalgie » → fiches de lombalgie, le motif de régulation reste intact",any("Lombalgie" in c for c in st["cands"]) and st["motif"]=="douleur lombaire",st)
        await page.click("#xp_prop .xp-cand"); await page.wait_for_timeout(400)
        ok(L+"une fiche choisie dans la recherche est retenue",await page.evaluate("()=>state.sel!=null&&!!currentPack()"))
        await page.evaluate("()=>{newPatient();TOUR.current='';}"); sid=await page.evaluate(STOPS); await page.evaluate("(id)=>xpOpenStop(id)",sid); await page.wait_for_timeout(300)
        await page.evaluate("()=>{document.getElementById('jmenu').hidden=false;}"); await page.click("#jmenu [data-xpsug]"); await page.wait_for_timeout(400)
        st=await page.evaluate("()=>({on:xpSuggestOn(),ok:!!document.getElementById('xp_ok'),prop:(document.querySelector('.xp-prop .xp-pn')||{}).textContent||''})")
        ok(L+"réglage ⋯ « Fiche proposée en visite » : réactivée → une proposition d'après le motif revient (ici « "+st["prop"]+" », d'où la demande de la désactiver)",st["on"] and st["ok"] and st["prop"]!="",st)
        await page.evaluate("()=>{document.getElementById('jmenu').hidden=false;}"); await page.click("#jmenu [data-xpsug]"); await page.wait_for_timeout(300)
        ok(L+"réglage désactivé à nouveau",not await page.evaluate("()=>xpSuggestOn()"))
        await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'MARTIN Jeanne',ddn:'05/06/1975',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.xpManual=true;state.xpMotif='lombalgie';render();}"); await page.wait_for_timeout(400)
        ok(L+"en consultation, la fiche proposée d'après le motif saisi reste disponible",await page.evaluate("()=>!!document.getElementById('xp_ok')"))
    # ---------- 4. certificats ----------
    today=datetime.date.today(); hier=today-datetime.timedelta(days=1); fin=hier+datetime.timedelta(days=2)
    await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'PETIT Léa',ddn:'12/03/2019',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Certificat — absence scolaire');render();}"); await page.wait_for_timeout(500)
    st=await page.evaluate("()=>({set:document.querySelectorAll('[data-cdset]').length,start:document.querySelectorAll('[data-cdstart]').length,xpcas:!!document.getElementById('xp_cas')})")
    ok(L+"certificat d'absence scolaire : durée d'un geste (1 j, 2 j, 3 j, 5 j) et début (Aujourd'hui, Hier, Avant-hier)",st["set"]>=4 and st["start"]>=3,st)
    await page.click('[data-cdstart="1"]'); await page.wait_for_timeout(300); await page.click('[data-cdset="3"]'); await page.wait_for_timeout(300)
    per=await page.evaluate("()=>certPeriod()")
    ok(L+"« Hier » + « 3 j » : du "+dmy(hier)+" au "+dmy(fin)+" inclus (commence avant la consultation)",per["du"]==dmy(hier) and per["au"]==dmy(fin) and per["j"]==3,per)
    if phone: await page.screenshot(path=os.path.join(OUT,f"fil-{tag}-certificat-dates.png"))
    r=await page.evaluate("()=>{const p=currentPack();const r=buildPages(p,true);const d=document.createElement('div');d.innerHTML=r.out;const pages=d.querySelectorAll('.page');return {n:pages.length,txt:pages[0]?pages[0].textContent.replace(/\\s+/g,' '):'',removed:r.removed};}")
    hh=await page.evaluate("()=>fmtH(Date.now())")
    ok(L+"une page : « certifie que l'état de santé de PETIT Léa, née le 12/03/2019, justifie son absence scolaire du … au … inclus », établi le jour à l'heure, en-tête et signature du modèle (profil) ; ni diagnostic, ni symptôme, ni traitement",
       r["n"]==1 and "certifie que l'état de santé de PETIT Léa, née le 12/03/2019, justifie son absence scolaire du "+dmy(hier)+" au "+dmy(fin)+" inclus" in r["txt"] and ("le "+dmy(today)+" à "+hh.split(" ")[0]+" h") in r["txt"] and "Certificat médical" in r["txt"] and not re.search(r"diagnostic|fièvre|angine|traitement|DOLIPRANE",r["txt"]),{"n":r["n"],"txt":r["txt"][:400]})
    await page.evaluate("()=>printPack()"); await page.wait_for_timeout(700)
    st=await page.evaluate("()=>({printing:document.body.classList.contains('printing'),pages:document.querySelectorAll('#print .page').length,notes:(JOURNAL[JOURNAL.length-1]||{}).notes||[],cr:buildCR(currentPack())})")
    ok(L+"impression du certificat : une page ; durée inscrite au journal et au compte rendu",st["printing"] and st["pages"]==1 and any(x.startswith("Certificat : absence scolaire : 3 jours, du "+dmy(hier)) for x in st["notes"]) and ("Certificat remis (absence scolaire : 3 jours, du "+dmy(hier)) in st["cr"],{"pages":st["pages"],"notes":st["notes"]})
    await page.evaluate("()=>(document.getElementById('pb_back')||document.getElementById('pb_back2')).click()"); await page.wait_for_timeout(300)
    await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>p.n==='Certificat — enfant malade');render();}"); await page.wait_for_timeout(400)
    r=await page.evaluate("()=>{const p=currentPack();const r=buildPages(p,true);const d=document.createElement('div');d.innerHTML=r.out;const pages=d.querySelectorAll('.page');return {n:pages.length,txt:pages[0]?pages[0].textContent.replace(/\\s+/g,' '):''};}")
    ok(L+"certificat enfant malade (employeur) : « l'état de santé de l'enfant PETIT Léa, née le 12/03/2019, nécessite la présence d'un parent à ses côtés du … au … inclus », une page, date et heure",
       r["n"]==1 and "certifie que l'état de santé de l'enfant PETIT Léa, née le 12/03/2019, nécessite la présence d'un parent à ses côtés du "+dmy(hier)+" au "+dmy(fin)+" inclus" in r["txt"] and ("le "+dmy(today)+" à ") in r["txt"] and not re.search(r"diagnostic|symptôme|traitement",r["txt"]),r["txt"][:300])
    await page.evaluate("()=>{state.ddn='';render();}"); await page.wait_for_timeout(300)
    st=await page.evaluate("()=>{const p=currentPack();const sh=p.s.findIndex(x=>x.k==='cert');const L=resolve(p.s[sh],sh);return {miss:L.flatMap(x=>x.fill.miss),warn:(document.querySelector('#main .warn')||{}).textContent||''};}")
    ok(L+"sans date de naissance : certificat signalé incomplet avant impression (jamais de trou)",any("date de naissance" in m for m in st["miss"]) and "date de naissance" in st["warn"],st)
    # jeune adulte (étudiante de 20 ans) : même certificat, remis à l'intéressée
    await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'ROUX Camille',ddn:'15/02/2006',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Certificat — absence scolaire');render();}"); await page.wait_for_timeout(400)
    r=await page.evaluate("()=>{const p=currentPack();const r=buildPages(p,true);const d=document.createElement('div');d.innerHTML=r.out;const pages=d.querySelectorAll('.page');return {n:pages.length,txt:pages[0]?pages[0].textContent.replace(/\\s+/g,' '):''};}")
    ok(L+"absence scolaire pour une étudiante de 20 ans : une page, « justifie son absence scolaire », remis en main propre à l'intéressée (pas « aux parents »)",r["n"]==1 and "ROUX Camille, née le 15/02/2006, justifie son absence scolaire du" in r["txt"] and "remis en main propre à l'intéressée" in r["txt"] and "aux parents" not in r["txt"],r["txt"][:300])
    if xp:
        await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'ROUX Camille',ddn:'15/02/2006',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.xpManual=true;state.xpMotif='angine';render();}"); await page.wait_for_timeout(400)
        try: await page.click("#xp_ok",timeout=3000); await page.wait_for_timeout(400)
        except Exception: pass
        st=await page.evaluate("()=>({cem:!!document.getElementById('xp_cem'),cas:!!document.getElementById('xp_cas')})")
        ok(L+"Express (20 ans) : case « Certificat absence scolaire » présente, « enfant malade » absente",st["cas"] and not st["cem"],st)
        await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'PETIT Léa',ddn:'12/03/2019',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.xpManual=true;state.xpMotif='angine';render();}"); await page.wait_for_timeout(400)
        try: await page.click("#xp_ok",timeout=3000); await page.wait_for_timeout(400)
        except Exception: pass
        st=await page.evaluate("()=>({cem:!!document.getElementById('xp_cem'),cas:!!document.getElementById('xp_cas')})")
        ok(L+"Express (enfant) : cases « Certificat enfant malade » et « Certificat absence scolaire »",st["cem"] and st["cas"],st)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def run_pc_express(b):
    """ordinateur, Express : « Imprimer et valider » (2 touchers) imprime le PDF préparé puis valide le patient ; l'écran « Avant d'imprimer » en visite ne bloque pas"""
    L="ordinateur Express : "
    ctx=await b.new_context(viewport={"width":1280,"height":900}); await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,"filpcxp",True); await page.evaluate("()=>{window.__printed=0;}")  # 07/11/2026 : window.print (stub) puis xpAfterPrint par printScreen
    await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"); await page.wait_for_timeout(500)
    v0=await page.evaluate("()=>VALID.hist.length"); await page.click("#xp_go"); await page.wait_for_timeout(300); await page.click("#xp_go")
    try: await page.wait_for_function("(v0)=>VALID.hist.length>v0&&window.__printed>=1",arg=v0,timeout=30000)
    except Exception: pass
    st=await page.evaluate("(v0)=>({printed:window.__printed,valid:VALID.hist.length-v0,view:state.view,last:VALID.hist[0]&&VALID.hist[0].patient})",v0)
    ok(L+"consultation : « Imprimer et valider » (2 touchers) → fenêtre d'impression du navigateur puis patient validé",st["printed"]>=1 and st["valid"]==1 and st["last"]=="DURAND Martine",st)
    await page.evaluate("()=>{patientNext();}"); sid=await page.evaluate(STOPS); await page.wait_for_timeout(300)
    await page.evaluate("(id)=>{TOUR.current=id;const s=tourStop(id);s.tArr=Date.now();Object.assign(state,{patient:'DUPONT Jean',ddn:'01/01/1950',sexe:'h'});state.cot.lieu='visite';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.view='';render();}",sid); await page.wait_for_timeout(500)
    v0=await page.evaluate("()=>VALID.hist.length"); n0=await page.evaluate("()=>window.__printed"); await page.click("#xp_go"); await page.wait_for_timeout(400)
    if not await page.locator("#ciover").count(): await page.click("#xp_go"); await page.wait_for_timeout(600)  # 1er toucher : confirmation
    ci=await page.locator("#ciover").count()
    if ci:
        await page.click("#ci_keep"); await page.click("#ciover [data-cichip]"); await page.click("#ci_print")
    try: await page.wait_for_function("()=>document.body.classList.contains('printing')",timeout=10000)
    except Exception: pass
    await page.evaluate("()=>{const b=document.getElementById('pb_print');if(b)b.click();}")
    try: await page.wait_for_function("(n0)=>window.__printed>n0",arg=n0,timeout=30000)
    except Exception: pass
    await page.evaluate("()=>{const b=document.getElementById('pb_valid');if(b)b.click();}"); await page.wait_for_timeout(300); await page.evaluate("()=>{const b=document.getElementById('pb_valid');if(b)b.click();}"); await page.wait_for_timeout(700)
    st=await page.evaluate("(a)=>({ci:!!document.getElementById('ciover'),printed:window.__printed-a[1],valid:VALID.hist.length-a[0],view:state.view})",[v0,n0])
    ok(L+"visite (76 ans) : écran « Avant d'imprimer », décision, aperçu (alertes à vérifier), impression, puis validation depuis l'aperçu",ci and not st["ci"] and st["printed"]>=1 and st["valid"]==1,st)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await run(b,375,812,True,"iPhone Express","iphone-express")
            await run(b,375,812,False,"iPhone complet","iphone-complet")
            await run(b,1280,900,False,"ordinateur complet","pc-complet")
            await run_pc_express(b)
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); tot=len(results); print(f"\n{n}/{tot} OK")
    with open(os.path.join(ROOT,"tests","resultats_fil_v41z.md"),"w",encoding="utf-8") as f:
        f.write("# Résultats — impression, patient suivant, visite sans proposition, certificats (v41z, 06/11/2026)\n\n%s\n\n%d/%d OK\n\n"%(datetime.date.today().isoformat(),n,tot))
        for name,c,info in results: f.write("- %s %s%s\n"%("OK" if c else "FAIL",name,"" if c else " — "+str(info)[:300]))
    sys.exit(0 if n==tot else 1)
asyncio.run(main())
