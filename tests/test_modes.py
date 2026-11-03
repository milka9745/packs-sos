# Points 3 et 4 du 03/11/2026 : barre du bas qui crée le patient (Consultation), ambiances Visite / Consultation.
# Règle : aucun bouton visible de la barre ne reste sans effet (sinon grisé avec la raison). Adresses fictives, réseau extérieur coupé.
# Lancer : python tests/test_modes.py
import asyncio, os, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8863

async def unlock(page,xp):
    await page.add_init_script("try{localStorage.setItem('sos_xp','%s')}catch(e){}"%("true" if xp else "false"))
    await page.add_init_script("""window.__clicked=[];window.__toasts=[];HTMLInputElement.prototype.click=function(){window.__clicked.push(this.id||this.className);};
      document.addEventListener('click',e=>{const t=e.target;if(t&&t.type==='file')window.__clicked.push(t.id);},true);""")
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testmodes"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(900)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
    await page.evaluate("const _t=toast;window.toast=t=>{window.__toasts.push(t);_t(t);};")

TOURSET="""()=>{newPatient();TOUR.stops=[
  {id:'v1',addr:'10 rue de Bourgogne, 45000 Orléans',label:'10 Rue de Bourgogne 45000 Orléans',lat:47.9020,lon:1.9110,city:'Orléans',nom:'DURAND Paul',ddn:'01/01/1950',tel:'0611111111',ts:1,done:false,motif:'fièvre'},
  {id:'v2',addr:'5 avenue de Verdun, 45140 Saint-Jean-de-la-Ruelle',label:'5 Avenue de Verdun 45140 Saint-Jean-de-la-Ruelle',lat:47.9080,lon:1.8650,city:'Saint-Jean-de-la-Ruelle',nom:'PETIT Lou',ddn:'01/01/2018',tel:'0622222222',ts:2,done:false}];
  TOUR.order=['v1','v2'];TOUR.legs=[{km:2,min:6},{km:4,min:9}];TOUR.current='';TOUR.computed=Date.now();tourSave();state.cot.lieu='visite';state.cot.auto=false;render();}"""
CONSULT="newPatient();state.xpManual=false;TOUR.current='';state.cot=state.cot||cotDefault();state.cot.lieu='cabinet';state.cot.auto=false;render();"
SNAP="""()=>({act:document.activeElement&&(document.activeElement.id||document.activeElement.className||document.activeElement.tagName),toasts:window.__toasts.length,view:state.view||'',fil:document.body.dataset.fil||'',clicked:window.__clicked.length,manual:!!state.xpManual,list:!!XP.list,cur:TOUR.current||'',sel:String(state.sel),y:Math.round(scrollY),text:document.body.innerText.length,arr:!!(TOUR.current&&tourStop(TOUR.current)&&tourStop(TOUR.current).tArr),open:[...document.querySelectorAll('details[open]')].length})"""
BAR="""()=>[...document.querySelectorAll('#fdock .fa')].map(e=>({id:e.id||'',tag:e.tagName,txt:e.textContent.trim().slice(0,30),href:e.getAttribute('href')||'',for:e.getAttribute('for')||'',dis:!!e.disabled,title:e.title||'',bound:!!e.onclick,vis:!!e.offsetParent}))"""
STYLE="""()=>{const cs=e=>e?getComputedStyle(e):null;const lum=c=>{const m=c.match(/[\\d.]+/g)||[0,0,0];const f=v=>{v=v/255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};return 0.2126*f(+m[0])+0.7152*f(+m[1])+0.0722*f(+m[2]);};
  const ratio=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
  const fd=document.getElementById('fdock');const md=document.querySelector('#fdock .fd-mode');const on=document.querySelector('.lieu button.on');const lieu=document.querySelector('.lieu');const jb=document.querySelector('.jbar');const pc=document.querySelector('.pcard,.xp,.tcard');
  const r=lieu?lieu.getBoundingClientRect():null;
  return {mode:document.documentElement.dataset.mode,fdBorder:fd?cs(fd).borderTopColor:'',fdW:fd?cs(fd).borderTopWidth:'',mdBg:md?cs(md).backgroundColor:'',mdTxt:md?cs(md).color:'',mdLbl:md?md.textContent:'',mdRatio:md?ratio(cs(md).backgroundColor,cs(md).color):0,
    onBg:on?cs(on).backgroundColor:'',onTxt:on?on.textContent:'',onRatio:on?ratio(cs(on).backgroundColor,cs(on).color):0,lieuTop:r?Math.round(r.top+scrollY):-1,lieuVis:!!(lieu&&lieu.offsetParent),lieuInDetails:!!(lieu&&lieu.closest('details')),lieuBtns:lieu?[...lieu.querySelectorAll('[data-lieu]')].map(b=>b.textContent+':'+b.getAttribute('aria-pressed')):[],
    lieuH:on?Math.round(on.getBoundingClientRect().height):0,jbBorder:jb?cs(jb).borderBottomColor:'',pcLeft:pc?cs(pc).borderLeftColor:'',pcLeftW:pc?cs(pc).borderLeftWidth:'',st:(document.querySelector('#fdock .fd-st')||{}).innerText||''};}"""

async def click_all(page,L,label,skip=()):
    """Règle : chaque bouton visible de la barre a un effet (ou est grisé avec une raison)."""
    bar=await page.evaluate(BAR)
    for b in bar:
        name=b["id"] or b["txt"]
        if not b["vis"]: continue
        if b["dis"]:
            ok(L+f"{label} : « {name} » grisé avec la raison",bool(b["title"]),b); continue
        if b["tag"]=="A":
            ok(L+f"{label} : « {name} » (lien) a une destination",b["href"] not in ("","#") or name.startswith("Appel masqué") or "masqué" in b["txt"],b); continue
        if b["tag"]=="LABEL":
            ok(L+f"{label} : « {name} » ouvre le sélecteur de fichiers",b["for"]=="fa_shots" and await page.locator("#fa_shots").count()==1,b); continue
        if b["id"] in skip:
            ok(L+f"{label} : « {name} » relié à son action",b["bound"],b); continue
        before=await page.evaluate(SNAP)
        sel=("#fdock #"+b["id"]) if b["id"] else f"#fdock .fa:has-text('{b['txt'][:12]}')"
        try:
            await page.click(sel,timeout=3000); await page.wait_for_timeout(450)
        except Exception as e:
            ok(L+f"{label} : « {name} » cliquable",False,str(e)[:120]); continue
        after=await page.evaluate(SNAP)
        ok(L+f"{label} : « {name} » a un effet",before!=after,{"avant":before,"après":after})
        # on revient à l'état de départ si l'action a changé de vue
        if after["view"]: await page.evaluate("state.view='';render();"); await page.wait_for_timeout(200)
    return bar

async def run(xp,th,big,shots):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":375,"height":850},device_scale_factor=2,is_mobile=True,has_touch=True)
        await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
        page=await ctx.new_page(); errors=[]
        page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await unlock(page,xp)
        L=f"{'Express' if xp else 'complet'} {'grand texte ' if big else ''}{'nuit' if th=='night' else 'jour'} : "
        await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
        # ---------- point 3 : Consultation sans patient ----------
        for bid,exp in (("fa_fiche",("xp_motif","xp_q","q")),("fa_dict",("f_dict",)),("fa_scan",None)):
            await page.evaluate(CONSULT); await page.wait_for_timeout(250)
            await page.evaluate("window.__clicked=[];window.__toasts=[];document.activeElement&&document.activeElement.blur()")
            st0=await page.evaluate("({manual:!!state.xpManual,pat:patActive(),fil:document.body.dataset.fil})")
            ok(L+f"consultation sans patient : barre « Consultation · étape 1 sur 3 » (avant {bid})",st0["fil"]=="place" and not st0["manual"] and not st0["pat"] and (await page.inner_text("#fdock .fd-st")).startswith("Consultation · étape 1 sur 3"),st0)
            await page.click("#fdock #"+bid); await page.wait_for_timeout(500)
            r=await page.evaluate("({manual:!!state.xpManual,act:document.activeElement&&document.activeElement.id,clicked:window.__clicked.slice(),toasts:window.__toasts.slice(),nom:!!document.getElementById('xp_nom')||!!document.getElementById('f_patient')})")
            if exp: ok(L+f"consultation sans patient : « {bid} » crée le patient puis ouvre le champ (clavier)",r["manual"] and r["act"] in exp and r["nom"] and any(t.startswith("Nouveau patient") for t in r["toasts"]),r)
            else: ok(L+f"consultation sans patient : « {bid} » crée le patient puis lance le scanner",r["manual"] and "doc_scan" in r["clicked"] and any(t.startswith("Nouveau patient") for t in r["toasts"]),r)
        # patient déjà ouvert : pas de second « nouveau patient »
        await page.evaluate("state.patient='DURAND Paul';render();"); await page.wait_for_timeout(200)
        await page.evaluate("window.__toasts=[]"); await page.click("#fdock #fa_dict"); await page.wait_for_timeout(300)
        r=await page.evaluate("({pat:state.patient,toasts:window.__toasts.slice()})")
        ok(L+"patient ouvert : « Dicter » ne recrée pas de patient",r["pat"]=="DURAND Paul" and not any(t.startswith("Nouveau patient") for t in r["toasts"]),r)
        # texte d'aide conforme à la barre
        if xp:
            await page.evaluate(CONSULT); await page.wait_for_timeout(200)
            t=await page.evaluate("(document.querySelector('.xp-home > .hint')||{}).textContent||''")
            ok(L+"aide (Consultation) : nomme les 3 boutons réels de la barre","Choisir la fiche" in t and "Dicter" in t and "Scanner" in t and "Ajouter des fiches" not in t,t)
            await page.evaluate("newPatient();state.cot.lieu='visite';state.cot.auto=false;render();"); await page.wait_for_timeout(200)
            t=await page.evaluate("(document.querySelector('.xp-home > .hint')||{}).textContent||''")
            ok(L+"aide (Visite) : « Ajouter des fiches » est bien dans la barre","Ajouter des fiches" in t and await page.locator("#fdock label[for=fa_shots]").count()==1,t)
        # ---------- règle : aucun bouton de la barre sans effet, état par état ----------
        await page.evaluate(CONSULT); await page.wait_for_timeout(200)
        await click_all(page,L,"Consultation sans patient")
        await page.evaluate("newPatient();state.cot.lieu='visite';state.cot.auto=false;TOUR.stops=[];TOUR.order=[];tourSave();render();"); await page.wait_for_timeout(200)
        await click_all(page,L,"Visite · Demande (tournée vide)")
        await page.evaluate(TOURSET); await page.wait_for_timeout(300)
        s=await page.evaluate(STYLE); ok(L+"étiquette « Visite · Demande · étape 1 sur 5 »",s["st"].startswith("Visite · Demande · étape 1 sur 5"),s["st"])
        if shots: await page.evaluate("window.scrollTo(0,0)"); await page.wait_for_timeout(150); await page.screenshot(path=os.path.join(OUT,f"modes-visite-375-{'grand' if big else th}.png"),full_page=False)
        sv=s
        await click_all(page,L,"Visite · Demande",skip=("tc_begin",))
        await page.click("#fdock #tc_begin"); await page.wait_for_timeout(600)
        s=await page.evaluate(STYLE); ok(L+"étiquette « Visite · En route · étape 2 sur 5 »",s["st"].startswith("Visite · En route · étape 2 sur 5"),s["st"])
        await click_all(page,L,"Visite · En route",skip=("tc_arrive",))
        await page.click("#fdock #tc_arrive"); await page.wait_for_timeout(600)
        s=await page.evaluate(STYLE); ok(L+"étiquette « Visite · Sur place · étape 3 sur 5 »",s["st"].startswith("Visite · Sur place · étape 3 sur 5"),s["st"])
        await click_all(page,L,"Visite · Sur place")
        # prise en charge : une fiche choisie
        await page.evaluate("state.sel=PACKS.findIndex(p=>/^Angine/.test(p.n));state.xpPick=state.sel;render();"); await page.wait_for_timeout(400)
        s=await page.evaluate(STYLE); ok(L+"étiquette « Visite · Prise en charge · étape 4 sur 5 »",s["st"].startswith("Visite · Prise en charge · étape 4 sur 5"),s["st"])
        await click_all(page,L,"Visite · Prise en charge",skip=("fin","xp_go"))
        await page.evaluate("state.lastPrint={n:2,ts:Date.now()};render();"); await page.wait_for_timeout(300)
        s=await page.evaluate(STYLE); ok(L+"étiquette « Visite · Sortie · étape 5 sur 5 »",s["st"].startswith("Visite · Sortie · étape 5 sur 5"),s["st"])
        await click_all(page,L,"Visite · Sortie",skip=("tc_reprint","tc_valid"))
        # ---------- point 4 : ambiances ----------
        await page.evaluate(TOURSET); await page.wait_for_timeout(300)
        sv=await page.evaluate(STYLE)
        await page.evaluate(CONSULT); await page.evaluate("state.patient='MARTIN Jean';state.ddn='12/03/1960';state.sel=PACKS.findIndex(p=>/^Angine/.test(p.n));state.xpPick=state.sel;render();"); await page.wait_for_timeout(400)
        sc=await page.evaluate(STYLE)
        ok(L+"étiquette « Consultation · Prise en charge · étape 2 sur 3 »",sc["st"].startswith("Consultation · Prise en charge · étape 2 sur 3"),sc["st"])
        if shots: await page.evaluate("window.scrollTo(0,0)"); await page.wait_for_timeout(150); await page.screenshot(path=os.path.join(OUT,f"modes-consult-375-{'grand' if big else th}.png"),full_page=False)
        ok(L+"deux couleurs franches : barre du bas, étiquette, onglet actif, bandeau du haut, liseré de la carte (Visite ≠ Consultation)",
           sv["mode"]=="visite" and sc["mode"]=="consult" and sv["fdBorder"]!=sc["fdBorder"] and sv["fdBorder"]==sv["mdBg"]==sv["onBg"]==sv["jbBorder"]==sv["pcLeft"] and sc["fdBorder"]==sc["mdBg"]==sc["onBg"]==sc["jbBorder"]==sc["pcLeft"] and float(sv["pcLeftW"].replace("px",""))>=6 and float(sv["fdW"].replace("px",""))>=4,{"v":sv,"c":sc})
        ok(L+"étiquette et onglet actif lisibles (contraste ≥ 4,5)",sv["mdRatio"]>=4.5 and sc["mdRatio"]>=4.5 and sv["onRatio"]>=4.5 and sc["onRatio"]>=4.5,{"v":(sv["mdRatio"],sv["onRatio"]),"c":(sc["mdRatio"],sc["onRatio"])})
        ok(L+"sélecteur Visite / Consultation toujours en haut, deux gros onglets, jamais dans un menu",sv["lieuVis"] and sc["lieuVis"] and not sv["lieuInDetails"] and not sc["lieuInDetails"] and sv["lieuTop"]<260 and sc["lieuTop"]<260 and sv["lieuH"]>=48 and sc["lieuH"]>=48 and sv["lieuBtns"]==["Visite:true","Consultation:false"] and sc["lieuBtns"]==["Visite:false","Consultation:true"],{"v":sv,"c":sc})
        # changement de mode : confirmation et journal
        await page.evaluate("window.__toasts=[];TESTMODE=false;JOURNAL.length=0;"); await page.click(".lieu [data-lieu=visite]"); await page.wait_for_timeout(400)
        r=await page.evaluate("({toasts:window.__toasts.slice(),lieu:state.cot.lieu,log:(state.modeLog||[]).map(m=>m.lieu),risk:riskMode(),mode:document.documentElement.dataset.mode,badge:(document.querySelector('.pat-tag .mbad')||{}).textContent||''})")
        ok(L+"passage en Visite : ligne de confirmation, pack à risque, pastille V dans l'en-tête",r["toasts"]==["Passage en Visite : pack à risque et cotation visite par défaut"] and r["lieu"]=="visite" and r["risk"] and r["mode"]=="visite" and r["badge"]=="V" and r["log"]==["visite"],r)
        await page.evaluate("window.__toasts=[]"); await page.click(".lieu [data-lieu=cabinet]"); await page.wait_for_timeout(400)
        r=await page.evaluate("({toasts:window.__toasts.slice(),lieu:state.cot.lieu,log:(state.modeLog||[]).map(m=>m.lieu),risk:riskMode(),badge:(document.querySelector('.pat-tag .mbad')||{}).textContent||''})")
        ok(L+"passage en Consultation : ligne de confirmation, pack simple, pastille C dans l'en-tête",r["toasts"]==["Passage en Consultation : pack simple et cotation consultation par défaut"] and r["lieu"]=="cabinet" and not r["risk"] and r["badge"]=="C" and r["log"]==["visite","cabinet"],r)
        await page.evaluate("journalUpsert(currentPack());"); await page.wait_for_timeout(100)
        await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(400)
        r=await page.evaluate("({n:JOURNAL.length,lieu:JOURNAL[0]&&JOURNAL[0].lieu,log:JOURNAL[0]&&(JOURNAL[0].modeLog||[]).map(m=>m.lieu),row:(document.querySelector('.jrow')||{}).innerText||'',badge:(document.querySelector('.jrow .mbad')||{}).textContent||''})")
        ok(L+"journal : mode noté pour le patient (C) et passages Visite → Consultation",r["n"]==1 and r["lieu"]=="cabinet" and r["log"]==["visite","cabinet"] and r["badge"]=="C" and "Passage en Visite" in r["row"] and "Passage en Consultation" in r["row"],r)
        await page.evaluate("state.view='';TESTMODE=true;render();"); await page.wait_for_timeout(200)
        # pastilles dans les listes
        await page.evaluate(TOURSET); await page.wait_for_timeout(300)
        if xp:
            r=await page.evaluate("[...document.querySelectorAll('.xp-home .xp-row')].map(e=>(e.querySelector('.mbad')||{}).textContent||'')")
            ok(L+"liste Express : pastille V devant chaque patient en visite",r==["V","V"],r)
        await page.evaluate("state.view='tour';render();"); await page.wait_for_timeout(300)
        r=await page.evaluate("[...document.querySelectorAll('.trow')].map(e=>(e.querySelector('.mbad')||{}).textContent||'')")
        ok(L+"écran Tournée : pastille V devant chaque arrêt",len(r)>=2 and all(x=="V" for x in r),r)
        await page.evaluate("state.view='';render();"); await page.wait_for_timeout(200)
        await page.evaluate("TOUR.consults=[{id:'c1',nom:'LEROY Anne',ddn:'01/01/1980',motif:'angine'}];state.view='tour';render();"); await page.wait_for_timeout(300)
        r=await page.evaluate("[...document.querySelectorAll('[data-cstart]')].map(b=>(b.closest('.fu-row').querySelector('.mbad')||{}).textContent||'')")
        ok(L+"écran Tournée : consultations attendues avec pastille C",r==["C"],r)
        await page.evaluate("TOUR.consults=[];state.view='';render();"); await page.wait_for_timeout(200)
        ow=await page.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth")
        ok(L+"aucun débordement horizontal",ow)
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(True,"day",False,True); await run(True,"night",False,True); await run(True,"day",True,True); await run(False,"night",False,False)
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_modes.md"),"w",encoding="utf-8").write("# Tests du 03/11/2026 — barre du bas (Consultation) et ambiances Visite / Consultation\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
