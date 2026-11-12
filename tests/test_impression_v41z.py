# -*- coding: utf-8 -*-
# 07/11/2026 (v41z) — Impression d'un geste : au clic sur « Imprimer », la fenêtre d'impression du navigateur s'ouvre dans la seconde, sur les pages
# déjà préparées à l'écran, sans fabrication de PDF (le PDF ne se fabrique que pour « Enregistrer en PDF », barre de progression et bouton désactivé
# pendant ce temps) ; un seul bouton « Imprimer » par écran, à place fixe (barre du bas), le même sur iPhone et ordinateur ; à chaque étape du fil
# (prise en charge, aperçu, écran « Avant d'imprimer », sortie / réimpression, Express « Imprimer et valider », synthèse du patient) ; document trop
# long coupé en « suite » (rien de masqué) ; iPhone réel (UA iOS) : PDF partagé (Phomemo, AirPrint) avec progression sur le bouton, jamais la page web.
# Ordinateur 1280 px et iPhone 375 px (Chromium), Consultation et Visite, mode complet et Express. Patients fictifs. Lancer : python tests/test_impression_v41z.py
import asyncio, os, io, re, json, subprocess, sys, time, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,"tests","captures"); PORT="8876"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
src=open(os.path.join(ROOT,"tests","test_packs.py"),encoding="utf-8").read()
ns={"__file__":os.path.join(ROOT,"tests","test_packs.py")}; exec(src.split("async def run(")[0].replace("8765",PORT),ns)
unlock=ns["unlock"]
IOS_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
LIMIT=1000  # ms entre le clic et l'ouverture de la fenêtre d'impression
HOOK="""(slow)=>{window.__ev=[];const mark=(k)=>window.__ev.push([k,performance.now()]);window.__mark=mark;
 document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('button,a.btn');if(b&&/imprimer|confirmer/i.test(b.textContent))mark('clic '+(b.id||b.textContent.trim().slice(0,20)));},true);
 window.__pr=[];window.print=()=>{mark('print');window.__pr.push(performance.now());};
 const h=window.html2canvas;window.__h2c=0;window.html2canvas=async function(){window.__h2c++;if(slow)await new Promise(r=>setTimeout(r,slow));return h.apply(this,arguments);};
 window.__share=[];navigator.share=o=>{mark('share');window.__share.push((o.files||[]).map(f=>[f.type,f.size]));return Promise.resolve();};navigator.canShare=()=>true;}"""
STOPS="""()=>{TOUR.stops=[];TOUR.order=[];TOUR.current='';TOUR.computed=false;delete TOUR.started;newPatient();state.cot.lieu='visite';state.cot.auto=false;
  const a=tourAdd('12 rue des Lilas 45000 Orléans','DUPONT Jean',false,{lat:47.9,lon:1.9,label:'12 rue des Lilas',city:'Orléans'});Object.assign(a,{nom:'DUPONT Jean',ddn:'01/01/1950',tel:'0612345678',motif:'douleur lombaire'});TOUR.order=[a.id];tourSave();render();return a.id;}"""
CONS="""()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.cot=state.cot||cotDefault();state.cot.lieu='consultation';state.cot.auto=false;state.xpManual=true;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"""
VIS="""(id)=>{TOUR.current=id;const s=tourStop(id);s.tArr=Date.now();Object.assign(state,{patient:'DUPONT Jean',ddn:'01/01/1950',sexe:'h'});state.cot.lieu='visite';state.cot.auto=false;state.xpManual=true;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.view='';render();}"""
# état de l'écran : boutons « Imprimer » visibles (id, désactivé, position), barre du bas fixe, aperçu, PDF
SCREEN="""()=>{const vis=e=>!!(e.offsetParent||getComputedStyle(e).position==='fixed')&&getComputedStyle(e).display!=='none'&&e.getBoundingClientRect().height>0;
 const btns=[...document.querySelectorAll('button,a.btn,label.btn')].filter(b=>/imprimer/i.test(b.textContent)&&vis(b)&&!b.closest('#ciover'));
 const bar=document.querySelector('#print .printbar:not(.top)');const r=bar?bar.getBoundingClientRect():null;
 return {imprimer:btns.map(b=>({id:b.id,dis:b.disabled,busy:b.classList.contains('busy'),aria:b.getAttribute('aria-busy'),txt:b.textContent.trim().slice(0,40),top:Math.round(b.getBoundingClientRect().top),bottom:Math.round(b.getBoundingClientRect().bottom)})),
  vh:innerHeight,printing:document.body.classList.contains('printing'),pages:[...document.querySelectorAll('#print>.page')].length,ci:!!document.getElementById('ciover'),
  bar:bar?{fixed:getComputedStyle(bar).position==='fixed',bottom:Math.round(r.bottom),top:Math.round(r.top),ids:[...bar.querySelectorAll('button')].map(b=>b.id)}:null,
  topbar:(()=>{const t=document.querySelector('#print .printbar.top');return t?[...t.querySelectorAll('button')].map(b=>b.id):null;})(),
  pdf:{busy:PDFJOB.busy,file:!!PDFJOB.file,h2c:window.__h2c},pr:window.__pr.length,ev:window.__ev.map(([k,t])=>[k,Math.round(t)])};}"""
def delay(ev,click_id=None):
    """ms entre le dernier clic sur un bouton d'impression (ou le clic nommé) et l'appel de window.print / du partage qui le suit"""
    clicks=[t for k,t in ev if k.startswith("clic") and (click_id is None or click_id in k)]
    if not clicks: return None
    c=clicks[-1]; outs=[t for k,t in ev if k in("print","share") and t>=c-1]
    return round(outs[0]-c) if outs else None
async def hook(page,slow=0): await page.evaluate(HOOK,slow)
async def print_pdf(page):
    """impression réelle du navigateur (headless) : PDF de la page en média print → nombre de pages, format, textes"""
    import pypdf
    await page.emulate_media(media="print")
    vis=await page.evaluate("[...document.body.children].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id||e.className||e.tagName)")
    pdf=await page.pdf(prefer_css_page_size=True,print_background=True)
    await page.emulate_media(media="screen")
    r=pypdf.PdfReader(io.BytesIO(pdf)); texts=[(pg.extract_text() or "").replace("\n"," ") for pg in r.pages]
    boxes=[(round(float(pg.mediabox[2])),round(float(pg.mediabox[3]))) for pg in r.pages]
    return {"n":len(r.pages),"vis":vis,"texts":texts,"boxes":boxes,"bytes":pdf}
async def new_page(b,w,h,xp,ios=False):
    kw=dict(viewport={"width":w,"height":h},device_scale_factor=2 if w<500 else 1,is_mobile=w<500,has_touch=w<500,accept_downloads=True)
    if ios: kw["user_agent"]=IOS_UA
    ctx=await b.new_context(**kw)
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_excomplet','0');}}catch(e){{}}")
    await unlock(page); await page.wait_for_timeout(300)
    return ctx,page,errors
async def go_print(page,xp):
    """touche le bouton d'impression de la barre (Express : 2 touchers, le 1er arme) ; retourne l'état juste après le toucher"""
    sel="#xp_go" if xp else "#fin"
    await page.click(sel); await page.wait_for_timeout(120)
    if xp and "Confirmer" in (await page.locator(sel).text_content() or ""):
        await page.click(sel)
    st=await page.evaluate(SCREEN); st["sel"]=sel
    await page.wait_for_timeout(900)
    return st
async def run(b,w,h,xp,label,tag):
    ctx,page,errors=await new_page(b,w,h,xp); L=label+" : "; phone=w<500
    await hook(page,400)
    # ---------- 1. Consultation, prise en charge : un seul bouton Imprimer, fenêtre d'impression dans la seconde ----------
    await page.evaluate(CONS); await page.wait_for_timeout(500)
    st0=await page.evaluate(SCREEN)
    ok(L+"fiche choisie (consultation) : un seul bouton « Imprimer » sur l'écran, dans la barre du bas",len(st0["imprimer"])==1 and st0["imprimer"][0]["id"]==("xp_go" if xp else "fin") and st0["imprimer"][0]["bottom"]<=st0["vh"] and st0["imprimer"][0]["top"]>st0["vh"]*0.6 and not st0["printing"],st0["imprimer"])
    st=await go_print(page,xp)
    ok(L+"dès le toucher : retour visible (bouton désactivé, barre de progression) avant la fenêtre d'impression",any(b["dis"] and b["busy"] and b["aria"]=="true" for b in st["imprimer"]) or st["pr"]>=1,st["imprimer"])
    st=await page.evaluate(SCREEN); d=delay(st["ev"])
    ok(L+"« Imprimer » de la barre : aperçu préparé et fenêtre d'impression du navigateur ouverte dans la seconde (%s ms), sans fabrication de PDF"%d,(xp or (st["printing"] and st["pages"]>=1)) and st["pr"]==1 and d is not None and d<LIMIT and st["pdf"]["h2c"]==0 and not st["pdf"]["busy"] and not st["pdf"]["file"],{"ev":st["ev"],"pdf":st["pdf"],"pages":st["pages"]})
    if xp:
        await page.wait_for_timeout(600)
        ok(L+"Express : patient validé après la fenêtre d'impression (journal, patient suivant)",await page.evaluate("()=>VALID.hist.length>=1&&VALID.hist[0].patient==='DURAND Martine'&&!document.body.classList.contains('printing')"),await page.evaluate("()=>({v:VALID.hist.length,p:VALID.hist[0]&&VALID.hist[0].patient,printing:document.body.classList.contains('printing')})"))
        await page.evaluate("()=>{try{patientUndo();}catch(e){}}"); await page.wait_for_timeout(300)
        await page.evaluate(CONS); await page.wait_for_timeout(300); await page.evaluate("()=>printPack()"); await page.wait_for_timeout(900)  # aperçu seul, pour les vérifications de l'aperçu
        st=await page.evaluate(SCREEN)
    # ---------- 2. aperçu : barre du bas unique et fixe, mêmes boutons sur iPhone et ordinateur ----------
    ok(L+"aperçu : un seul bouton « Imprimer » (#pb_print), dans la barre du bas fixe ; la barre du haut n'a plus de bouton Imprimer",st["printing"] and len(st["imprimer"])==1 and st["imprimer"][0]["id"]=="pb_print" and st["bar"] and st["bar"]["fixed"] and st["bar"]["bottom"]<=st["vh"]+1 and st["bar"]["ids"]==["pb_print","pb_pdf","pb_back","pb_valid"] and st["topbar"]==["pb_back2"],{"imprimer":st["imprimer"],"bar":st["bar"],"top":st["topbar"]})
    if phone: await page.screenshot(path=os.path.join(OUT,f"impression-{tag}-apercu.png"))
    n0=st["pr"]; await page.click("#pb_print"); await page.wait_for_timeout(300); st=await page.evaluate(SCREEN); d=delay(st["ev"],"pb_print")
    ok(L+"« Imprimer » de l'aperçu : fenêtre d'impression tout de suite (%s ms), une seule fois, toujours sans PDF"%d,st["pr"]==n0+1 and d is not None and d<LIMIT and st["pdf"]["h2c"]==0 and not st["pdf"]["busy"],{"ev":st["ev"][-3:],"pdf":st["pdf"]})
    r=await print_pdf(page)
    ok(L+"impression réelle du navigateur : une page A4 par document (%d), seul l'aperçu s'imprime, texte complet (patient, documents)"%st["pages"],r["n"]==st["pages"] and r["vis"]==["print"] and all(bx==(595,842) for bx in r["boxes"]) and all("DURAND Martine" in t for t in r["texts"]) and not any("ne s'imprime pas" in t for t in r["texts"]) and all(len(t)>200 for t in r["texts"]),{"n":r["n"],"vis":r["vis"],"boxes":r["boxes"][:3],"len":[len(t) for t in r["texts"]]})
    if not phone: open(os.path.join(OUT,f"impression-{tag}-navigateur.pdf"),"wb").write(r["bytes"])
    # ---------- 3. « Enregistrer en PDF » : seul moment où le PDF se fabrique, progression sur le bouton, désactivé ----------
    async with page.expect_download(timeout=60000) as dl:
        await page.click("#pb_pdf"); await page.wait_for_timeout(250)
        mid=await page.evaluate("()=>{const b=document.getElementById('pb_pdf');return {dis:b.disabled,busy:b.classList.contains('busy'),aria:b.getAttribute('aria-busy'),txt:b.textContent,pct:b.style.getPropertyValue('--pct'),h:getComputedStyle(b,'::after').height,job:PDFJOB.busy};}")
    f=await dl.value; path=await f.path(); head=open(path,"rb").read(5)
    after=await page.evaluate("()=>{const b=document.getElementById('pb_pdf');return {dis:b.disabled,busy:b.classList.contains('busy'),txt:b.textContent,h2c:window.__h2c,pr:window.__pr.length};}")
    ok(L+"« Enregistrer en PDF » : pendant la fabrication le bouton est désactivé avec une barre de progression (« PDF… k/n »), puis un vrai PDF est remis et le bouton revient",mid["dis"] and mid["busy"] and mid["aria"]=="true" and mid["txt"].startswith("PDF…") and mid["pct"].endswith("%") and mid["h"]=="5px" and head==b"%PDF-" and f.suggested_filename.endswith(".pdf") and not after["dis"] and not after["busy"] and after["txt"].startswith("⬇ Enregistrer en PDF") and after["h2c"]>=1 and after["pr"]==n0+1,{"mid":mid,"after":after,"file":f.suggested_filename})
    if phone: await page.screenshot(path=os.path.join(OUT,f"impression-{tag}-apercu-bas.png"),clip={"x":0,"y":h-140,"width":w,"height":140})
    # ---------- 4. sortie : « Réimprimer » ----------
    await page.click("#pb_back"); await page.wait_for_timeout(400)
    st=await page.evaluate(SCREEN)
    ok(L+"retour : étape « sortie », « Réimprimer » dans la barre, un seul bouton d'impression",not st["printing"] and await page.evaluate("()=>filState()")=="sortie" and len(st["imprimer"])==1 and st["imprimer"][0]["id"]=="tc_reprint",st["imprimer"])
    n0=st["pr"]; await page.click("#tc_reprint"); await page.wait_for_timeout(900); st=await page.evaluate(SCREEN); d=delay(st["ev"],"tc_reprint")
    ok(L+"« Réimprimer » : aperçu et fenêtre d'impression dans la seconde (%s ms), une seule impression par toucher"%d,st["printing"] and st["pr"]==n0+1 and d is not None and d<LIMIT,{"ev":st["ev"][-3:],"pr":st["pr"]})
    await page.click("#pb_back"); await page.wait_for_timeout(300)
    # ---------- 5. Visite 76 ans : écran « Avant d'imprimer », puis « Imprimer » de cet écran ----------
    sid=await page.evaluate(STOPS); await page.wait_for_timeout(200); await page.evaluate(VIS,sid); await page.wait_for_timeout(500)
    st=await go_print(page,xp)
    ok(L+"visite (76 ans, AINS) : l'écran « Avant d'imprimer » s'ouvre d'abord, sans impression",st["ci"] and st["pr"]==0 or (st["ci"] and delay(st["ev"]) is None),{"ci":st["ci"],"ev":st["ev"][-3:]})
    if st["ci"]:
        await page.click("#ci_keep"); await page.wait_for_timeout(200); await page.click("#ciover [data-cichip]")
        n0=await page.evaluate("()=>window.__pr.length"); await page.click("#ci_print"); await page.wait_for_timeout(900)
        st=await page.evaluate(SCREEN); d=delay(st["ev"],"ci_print")
        ok(L+"« Imprimer » de l'écran « Avant d'imprimer » : aperçu et fenêtre d'impression dans la seconde (%s ms)"%d,st["printing"] and st["pr"]==n0+1 and d is not None and d<LIMIT and not st["ci"],{"ev":st["ev"][-3:]})
        await page.click("#pb_valid"); await page.wait_for_timeout(600)  # 12/11/2026 : un seul toucher
        ok(L+"« Valider le patient » depuis l'aperçu (un seul toucher) : patient validé"+(" (Express : alertes décidées, la validation reste un geste du médecin)" if xp else ""),await page.evaluate("()=>VALID.hist.length>=1&&VALID.hist[0].patient==='DUPONT Jean'&&!document.body.classList.contains('printing')"),await page.evaluate("()=>({v:VALID.hist.map(x=>x.patient),printing:document.body.classList.contains('printing')})"))
    # ---------- 6. document trop long : coupé en « suite », rien de masqué, impression = aperçu ----------
    if not xp:
        await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'LONG Ordonnance',ddn:'02/02/1970',sexe:'h'});state.cot.lieu='consultation';state.cot.auto=false;state.xpManual=true;state.sel=PACKS.findIndex(p=>p.n==='Tendinopathie d\\'Achille');const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');state.extra[si]=Array.from({length:26},(_,i)=>'ESSAILIGNE numéro '+(i+1)+' : 1 comprimé matin et soir pendant 5 jours, à prendre au cours du repas avec un grand verre d\\'eau.');render();}"); await page.wait_for_timeout(300)
        await page.evaluate("()=>printPack()"); await page.wait_for_timeout(1200)
        if await page.locator("#ciover").count(): await page.click("#ci_keep"); await page.click("#ciover [data-cichip]"); await page.click("#ci_print"); await page.wait_for_timeout(1200)
        dom=await page.evaluate("()=>{const pgs=[...document.querySelectorAll('#print>.page')];return {n:pgs.length,h2:pgs.map(p=>(p.querySelector('h2')||{}).textContent||''),stamp:pgs.map(p=>!!p.querySelector('.stamp,.sig')),over:pgs.map(p=>p.dataset.over||''),warn:(document.querySelector('#print .fitwarn')||{}).textContent||'',last:pgs.map(p=>/ESSAILIGNE numéro 26/.test(p.textContent))};}")
        suite=[i for i,x in enumerate(dom["h2"]) if x.endswith("(suite)")]
        ok(L+"ordonnance de 26 lignes ajoutées : coupée dans l'aperçu, la suite porte le cachet, la première partie non ; alerte « suite » ; dernière ligne présente",suite and all(dom["stamp"][i] for i in suite) and all(not dom["stamp"][i-1] for i in suite) and "suite" in dom["warn"] and any(dom["last"]) and not any(dom["over"]),dom)
        r=await print_pdf(page)
        ok(L+"impression réelle : autant de pages que l'aperçu (%d), la dernière ligne ajoutée est imprimée (rien de masqué)"%dom["n"],r["n"]==dom["n"] and any("ESSAILIGNE numéro 26" in t for t in r["texts"]) and any("(suite)" in t for t in r["texts"]),{"n":r["n"],"dom":dom["n"],"h2":dom["h2"]})
        if not phone: open(os.path.join(OUT,f"impression-{tag}-suite.pdf"),"wb").write(r["bytes"])
        await page.click("#pb_back"); await page.wait_for_timeout(300)
    # ---------- 7. synthèse du patient : même barre du bas ----------
    await page.evaluate("()=>{newPatient();TOUR.current='';Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;render();synthPrint();}"); await page.wait_for_timeout(500)
    st=await page.evaluate(SCREEN); n0=st["pr"]
    ok(L+"synthèse du patient : aperçu avec la même barre du bas (Imprimer, Enregistrer en PDF), un seul bouton Imprimer",st["printing"] and len(st["imprimer"])==1 and st["imprimer"][0]["id"]=="sy_go" and st["bar"] and st["bar"]["fixed"] and st["bar"]["ids"][:2]==["sy_go","pb_pdf"],{"imprimer":st["imprimer"],"bar":st["bar"]})
    await page.click("#sy_go"); await page.wait_for_timeout(300); st=await page.evaluate(SCREEN); d=delay(st["ev"],"sy_go")
    ok(L+"synthèse : « Imprimer » ouvre la fenêtre d'impression tout de suite (%s ms)"%d,st["pr"]==n0+1 and d is not None and d<LIMIT,st["ev"][-3:])
    await page.click("#sy_back2"); await page.wait_for_timeout(200)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def run_ios(b,xp,label,tag):
    """iPhone réel (UA iOS) : l'impression passe par le PDF partagé (Phomemo, AirPrint) ; pendant la fabrication, barre de progression sur le bouton, désactivé ; jamais la page web"""
    ctx,page,errors=await new_page(b,375,812,xp,ios=True); L=label+" : "
    await hook(page,700)
    await page.evaluate(CONS); await page.wait_for_timeout(500)
    if xp:
        for _ in range(60):
            if await page.evaluate("()=>xpReady()"): break
            await page.wait_for_timeout(250)
        ok(L+"Express : documents (PDF) préparés d'avance, bouton prêt",await page.evaluate("()=>xpReady()&&!document.getElementById('xp_go').classList.contains('wait')"))
        await page.click("#xp_go"); await page.wait_for_timeout(600)  # 12/11/2026 : un seul toucher
        st=await page.evaluate(SCREEN); d=delay(st["ev"],"xp_go")
        ok(L+"Express « Imprimer et valider » : menu Partager ouvert dans la seconde (%s ms) avec le PDF, jamais window.print, patient validé"%d,d is not None and d<LIMIT and st["pr"]==0 and await page.evaluate("()=>window.__share.length===1&&window.__share[0][0][0]==='application/pdf'&&VALID.hist.length>=1"),{"ev":st["ev"][-3:],"share":await page.evaluate("()=>window.__share")})
        await page.evaluate("()=>{try{patientUndo();}catch(e){}}"); await page.wait_for_timeout(300); await page.evaluate(CONS); await page.wait_for_timeout(300); await page.evaluate("()=>printPack()")
    else:
        await page.click("#fin")
    await page.wait_for_timeout(500)
    mid=await page.evaluate("()=>{const b=document.getElementById('pb_print');return b?{dis:b.disabled,busy:b.classList.contains('busy'),aria:b.getAttribute('aria-busy'),txt:b.textContent,pct:b.style.getPropertyValue('--pct'),job:PDFJOB.busy,pdfbtn:document.getElementById('pb_pdf').disabled}:null;}")
    ok(L+"aperçu : pendant la préparation du PDF, le bouton « Imprimer » est désactivé avec une barre de progression (« PDF… k/n ») ; aucun toucher sans retour",mid and mid["dis"] and mid["busy"] and mid["aria"]=="true" and mid["txt"].startswith("PDF…") and mid["pct"].endswith("%") and mid["job"] and not mid["pdfbtn"],mid)
    await page.screenshot(path=os.path.join(OUT,f"impression-{tag}-preparation.png"),clip={"x":0,"y":812-140,"width":375,"height":140})
    for _ in range(80):
        if await page.evaluate("()=>!!PDFJOB.file"): break
        await page.wait_for_timeout(250)
    st=await page.evaluate(SCREEN)
    ok(L+"PDF prêt : bouton « 🖨 Imprimer » actif, un seul, dans la barre du bas fixe (mêmes boutons que sur ordinateur)",len(st["imprimer"])==1 and st["imprimer"][0]["id"]=="pb_print" and not st["imprimer"][0]["dis"] and st["imprimer"][0]["txt"]=="🖨 Imprimer" and st["bar"]["fixed"] and st["bar"]["ids"]==["pb_print","pb_pdf","pb_back","pb_valid"] and st["topbar"]==["pb_back2"],st)
    await page.click("#pb_print"); await page.wait_for_timeout(300); st=await page.evaluate(SCREEN); d=delay(st["ev"],"pb_print")
    ok(L+"« Imprimer » : menu Partager (PDF) ouvert dans la seconde (%s ms), jamais la page web"%d,d is not None and d<LIMIT and st["pr"]==0 and await page.evaluate("()=>window.__share.length>=1&&window.__share.slice(-1)[0][0][0]==='application/pdf'&&window.__share.slice(-1)[0][0][1]>5000"),{"ev":st["ev"][-3:]})
    await page.emulate_media(media="print")
    vis=await page.evaluate("[...document.body.children].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id||e.className||e.tagName)")
    await page.emulate_media(media="screen")
    ok(L+"la page web elle-même ne s'imprime pas sur iPhone (seul le message renvoyant au bouton)",vis==["webnoprint"],vis)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3]); await ctx.close()
async def main():
    os.makedirs(OUT,exist_ok=True)
    srv=subprocess.Popen([sys.executable,"-m","http.server",PORT],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await run(b,1280,900,False,"ordinateur complet","pc-complet")
            await run(b,375,812,False,"iPhone 375 px complet","iphone-complet")
            await run(b,1280,900,True,"ordinateur Express","pc-express")
            await run(b,375,812,True,"iPhone 375 px Express","iphone-express")
            await run_ios(b,False,"iPhone réel (UA iOS) complet","ios-complet")
            await run_ios(b,True,"iPhone réel (UA iOS) Express","ios-express")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); tot=len(results); print(f"\n{n}/{tot} tests OK")
    with open(os.path.join(ROOT,"tests","resultats_impression_v41z.md"),"w",encoding="utf-8") as f:
        f.write("# Résultats — impression d'un geste : fenêtre d'impression dans la seconde, un seul bouton, PDF à la demande (v41z, 07/11/2026)\n\n%s\n\n%d/%d OK\n\n"%(datetime.date.today().isoformat(),n,tot))
        for name,c,info in results: f.write("- %s %s%s\n"%("OK" if c else "FAIL",name,"" if c else " — "+str(info)[:400]))
    sys.exit(0 if n==tot else 1)
asyncio.run(main())
