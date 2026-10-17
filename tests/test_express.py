# Express visite (17/10/2026) : les 3 visites fictives de l'audit, gestes mesurés APRÈS ; points a à g et décisions 1 à 4.
# 375 px (jour, nuit, grand texte) et ordinateur. Patients fictifs, réseau extérieur coupé. Lancer : python tests/test_express.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
PORT=8782
STOPS=open(os.path.join(ROOT,"tests","audit_express.py"),encoding="utf-8").read().split('STOPS="""')[1].split('"""')[0]

async def unlock(page,uid):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

class G:
    def __init__(s): s.g=[]
    def add(s,k,w): s.g.append((k,w))

async def tap(page,G_,sel,why):
    loc=page.locator(sel).first; await loc.scroll_into_view_if_needed(timeout=5000); await loc.click(timeout=5000); await page.wait_for_timeout(350); G_.add("toucher",why)

async def ready(page):
    for _ in range(80):
        if await page.evaluate("xpReady()||(!isPhone()&&!iosLike())"): return True
        await page.wait_for_timeout(250)
    return False

async def run(b,w,h,th,big,label,shots):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,accept_downloads=True,permissions=["clipboard-read","clipboard-write"])
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; dialogs=[]
    page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
    page.on("popup",lambda pg:asyncio.ensure_future(pg.close()))
    await unlock(page,"xp"+label.replace(" ","")[:10])
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();localStorage.removeItem('sos_xp');")
    await page.evaluate(STOPS); await page.evaluate("window.print=()=>{window.__pr=(window.__pr||0)+1;};"); await page.wait_for_timeout(400)
    L=label+" : "; tag=label.replace(" ","-")
    # accueil : liste des patients de la régulation
    ok(L+"accueil = liste des patients (3), « 📷 Ajouter des fiches » et « ＋ Patient »",await page.locator(".xp-home [data-xpopen]").count()==3 and await page.locator("label[for=xp_shots]").count()==1 and await page.locator("#xp_new").count()==1)
    href=await page.get_attribute(".xp-home [data-xpopen]","href")
    ok(L+"f. en visite, toucher le patient lance la navigation (même geste)",bool(href) and ("waze" in href or "maps" in href),href)
    if mob:
        inmain=await page.evaluate("(()=>{const m=document.getElementById('main');const j=document.getElementById('jmenu');const sp=document.querySelector('.specbar');return {out:!!(sp&&!j.contains(sp)),inmenu:!!(sp&&j.contains(sp))};})()")
        ok(L+"4. bandeau profil (SPÉCIMEN) rangé dans ⋯",inmain["inmenu"] and not inmain["out"],inmain)
    if shots: await page.screenshot(path=os.path.join(OUT,f"express-apres-{tag}-1-accueil.png"))
    visits=[("v1","Rhinopharyngite — adulte",False),("v2","Fièvre — enfant",True),("v3","Chute du sujet âgé — bilan",False)]
    gest={}
    for n,(vid,fiche,kid) in enumerate(visits):
        g=G()
        if n==0: await tap(page,g,f".xp-home [data-xpopen={vid}]","toucher le patient (navigation lancée)")
        else: await tap(page,g,".xp a.btn[href*='waze'],.xp a.btn[href*='maps']","🧭 Naviguer (patient suivant déjà ouvert)")
        cur=await page.evaluate("TOUR.current")
        ok(L+f"{vid} patient ouvert",cur==vid,cur)
        prop=await page.evaluate("(()=>{const i=xpProposed();return i==null?'':PACKS[i].n;})()")
        ok(L+f"{vid} c. fiche proposée selon le motif et l'âge : « {fiche} »",prop==fiche,prop)
        if vid=="v2":
            c=await page.evaluate("xpCandidates('fièvre').ok.slice(0,6).map(i=>PACKS[i].n)")
            ok(L+"c. 4 ans, « fièvre » : Fièvre — enfant en tête, aucune fiche adulte proposée",c and c[0]=="Fièvre — enfant" and not any("adulte" in x for x in c),c)
            await page.evaluate("search('fièvre')")
            first=await page.evaluate("[...document.querySelectorAll('#res button.res .n')].slice(0,3).map(x=>x.textContent)")
            ok(L+"c. liste classique « Autre fiche » : fiche enfant en tête à 4 ans",first and first[0]=="Fièvre — enfant",first)
        if vid=="v3":
            gv=await page.evaluate("(document.querySelector('.xp .xp-grav')||{}).textContent||''")
            ok(L+"b. signes de gravité de la fiche visibles sur l'écran patient (une ligne)",gv.startswith("⚠") and len(gv)>20,gv[:80])
        if shots and n<2: await page.screenshot(path=os.path.join(OUT,f"express-apres-{tag}-{vid}-2-fiche-proposee.png"))
        await tap(page,g,"#xp_ok","✓ Confirmer la fiche")
        arr=await page.evaluate("(tourStop(TOUR.current)||{}).tArr||0")
        ok(L+f"{vid} 1. arrivée enregistrée seule à la confirmation",arr>0)
        if kid:
            ok(L+"poids demandé chez l'enfant, champ en évidence",await page.locator("#xp_poids").count()==1)
            await page.locator("#xp_poids").fill("17"); await page.locator("#xp_poids").dispatch_event("change"); await page.wait_for_timeout(300); g.add("saisie","poids")
            ok(L+"certificat enfant malade proposé (enfant)",await page.locator("#xp_cem").count()==1)
        else:
            ok(L+f"{vid} pas de champ poids sans dose au poids chez l'adulte",await page.locator("#xp_poids").count()==0)
            ok(L+f"{vid} pas de certificat enfant malade chez l'adulte",await page.locator("#xp_cem").count()==0)
        ok(L+f"{vid} d. « Arrêt de travail fait » visible, non coché",await page.locator("#xp_at").count()==1 and not await page.locator("#xp_at").is_checked())
        meds=await page.evaluate("[...document.querySelectorAll('.xp .xp-med')].map(x=>x.textContent)")
        non=await page.evaluate("(()=>{const p=currentPack();let n=0;p.s.forEach((sh,si)=>{if(sh.k!=='med'||state.off[si])return;resolve(sh,si).forEach(x=>{if(x.on&&!x.jr)n++;});});return n;})()")
        ok(L+f"{vid} a. résumé d'une ligne par médicament coché ({non}), au-dessus du bouton",len(meds)==non and (non==0 or await page.evaluate("(()=>{const m=document.querySelector('.xp .xp-meds'),b=document.getElementById('xp_go');return !!(m&&b&&(m.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING));})()")),meds[:3])
        if kid: ok(L+"a. dose au poids affichée (17 kg)",any(re.search(r"\d",x) and ("kg" in x or "ml" in x.lower() or "mg" in x) for x in meds),meds[:3])
        if vid=="v3": ok(L+"courrier prêt (fiche avec orientation)","Courrier prêt" in await page.inner_text(".xp"))
        await page.evaluate("()=>{const f=document.getElementById('f_dict');f.value='Observation dictée de test, examen rassurant.';f.dispatchEvent(new Event('input',{bubbles:true}));}"); g.add("dictée","dicter (micro du clavier)")
        if shots and n<2: await page.screenshot(path=os.path.join(OUT,f"express-apres-{tag}-{vid}-3-fiche-confirmee.png"))
        r=await ready(page)
        ok(L+f"{vid} documents préparés d'avance (PDF prêt avant le toucher)",r)
        pr0=await page.evaluate("window.__pr||0")
        await tap(page,g,"#xp_go","🖨 Imprimer et valider")
        await page.wait_for_timeout(900)
        t=await page.evaluate("(document.getElementById('xptoast')||{}).textContent||''")
        ok(L+f"{vid} g. toast « CR copié · prêt à coller dans MCC » + Annuler",("CR copié · prêt à coller dans MCC" in t) and ("Annuler" in t),t)
        clip=await page.evaluate("navigator.clipboard.readText().catch(()=>'')")
        ok(L+f"{vid} g. compte rendu copié automatiquement (presse-papiers), celui du patient",len(clip)>100 and ({"v1":"DURAND","v2":"PETIT","v3":"MARTIN"}[vid] in clip),clip[:200])
        ok(L+f"{vid} 2. pas d'écran récapitulatif après validation",await page.evaluate("state.view")!="valid")
        nxt=await page.evaluate("TOUR.current||''")
        ok(L+f"{vid} patient suivant ouvert ({'tournée terminée' if n==2 else 'v'+str(n+2)})",nxt==("" if n==2 else "v"+str(n+2)),[nxt,await page.evaluate("({view:state.view,printing:document.body.classList.contains('printing'),ci:!!document.getElementById('ciover'),pat:state.patient,xt:(document.getElementById('toast')||{}).textContent})")])
        if not mob: ok(L+f"{vid} ordinateur : impression lancée",await page.evaluate("window.__pr||0")>pr0)
        jr=await page.evaluate("JOURNAL.length")
        gest[vid]=len(g.g)
        ok(L+f"{vid} gestes : {len(g.g)} ({', '.join(x[1] for x in g.g)})",len(g.g)<=(5 if kid else 4))
        if shots and n==0: await page.screenshot(path=os.path.join(OUT,f"express-apres-{tag}-v1-4-apres-validation.png"))
    ok(L+"journal : 3 patients",await page.evaluate("JOURNAL.filter(e=>/DURAND|PETIT|MARTIN/.test(e.patient)).length")>=3)
    vl=await page.evaluate("VALID.hist.filter(v=>v.crTxt).length")
    ok(L+"g. secours : « Recopier le CR » dans « Patients validés »",vl>=3)
    await page.evaluate("validListScreen()"); await page.wait_for_timeout(200)
    ok(L+"« Patients validés » : bouton « Recopier le CR »",await page.locator("[data-vcr]").count()>=3)
    await page.evaluate("identClose()")
    ok(L+"aucune fenêtre système",not dialogs,dialogs[:2])
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()
    return gest

async def extras(b,w,h,label):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,permissions=["clipboard-read","clipboard-write"])
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,"xpx"+label[:6]); await page.evaluate("localStorage.removeItem('sos_xp');window.print=()=>{};")
    L=label+" : "
    # f. au cabinet : pas de navigation au toucher
    await page.evaluate(STOPS); await page.evaluate("state.cot.lieu='consultation';state.cot.auto=false;render();"); await page.wait_for_timeout(300)
    href=await page.get_attribute(".xp-home [data-xpopen]","href")
    ok(L+"f. au cabinet, toucher le patient n'ouvre pas la navigation",href is None,href)
    # 3 + a. alerte en attente : le bouton ouvre l'aperçu au lieu d'imprimer directement
    await page.evaluate("""()=>{newPatient();const i=PACKS.findIndex(p=>p.n==='Renouvellement de traitement chronique');Object.assign(state,{patient:'MARTIN Jeanne',ddn:'05/06/1975',sexe:'f'});state.sel=i;
      const si=PACKS[i].s.findIndex(s=>s.k==='med');state.extra[si]=['ESCITALOPRAM 10 mg comprimé : 1 comprimé par jour, 3 mois.','HALOPÉRIDOL 1 mg comprimé : 1 comprimé par jour, 3 mois.'];render();}""")
    await page.wait_for_timeout(300)
    st=await page.evaluate("(document.getElementById('xp_gost')||{}).textContent||''")
    ok(L+"a. alerte en attente annoncée sous le bouton",("alerte" in st),st)
    await page.click("#xp_go"); await page.wait_for_timeout(600)
    ok(L+"3. alerte en attente : écran d'alerte / aperçu au lieu de l'impression directe",await page.locator("#ciover").count()==1 and await page.evaluate("state.view")!="valid")
    await page.evaluate("const e=document.getElementById('ciover');if(e)e.remove();")
    # a. dose au poids sans poids : l'aperçu s'ouvre
    wn=await page.evaluate("""()=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/03/2022',sexe:'f',poids:''});
      for(let i=0;i<PACKS.length;i++){if(!/enfant/i.test(PACKS[i].n))continue;state.sel=i;const p=currentPack();if(xpMeds(p).some(m=>m.miss)){render();return PACKS[i].n;}}state.sel=null;return '';}""")
    await page.wait_for_timeout(300)
    miss=await page.evaluate("[...document.querySelectorAll('.xp .xp-med.miss')].map(x=>x.textContent)")
    ok(L+f"a. dose au poids sans poids (« {wn} ») : ligne signalée « poids manquant »",wn and len(miss)>=1,miss)
    await page.click("#xp_go"); await page.wait_for_timeout(900)
    ok(L+"a. poids manquant : le bouton ouvre l'aperçu, pas de validation",await page.evaluate("document.body.classList.contains('printing')||!!document.getElementById('ciover')") and await page.evaluate("state.view")!="valid")
    await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();const e=document.getElementById('ciover');if(e)e.remove();render();")
    # e. adulte, fiche avec anticoagulant : poids affiché
    nm=await page.evaluate("(()=>{const i=PACKS.findIndex(p=>!/enfant|nourrisson/i.test(p.n)&&p.s.some(s=>s.k==='med'&&s.l.some(l=>/LOVENOX|INNOHEP|HBPM|énoxaparine|tinzaparine|ARIXTRA/i.test(typeof l==='string'?l:l.t))));if(i<0)return '';newPatient();Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1960',sexe:'h'});state.sel=i;render();return PACKS[i].n;})()")
    await page.wait_for_timeout(300)
    ok(L+f"e. adulte, fiche avec anticoagulant (« {nm} ») : poids affiché",nm and await page.locator("#xp_poids").count()==1,nm)
    # d. arrêt de travail fait : tracé au CR et au journal ; aucun bloc amelipro, aucune durée suggérée
    await page.evaluate("""()=>{newPatient();const i=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1985',sexe:'h'});state.sel=i;render();}""")
    await page.wait_for_timeout(200)
    await page.check("#xp_at"); await page.wait_for_timeout(300); await page.fill("#xp_atj","3")
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"d. coché : « Arrêt de travail fait : 3 jours » au compte rendu","Arrêt de travail fait : 3 jours" in cr,[l for l in cr.split(chr(10)) if "rrêt" in l])
    await page.evaluate("journalUpsert(currentPack())")
    jt=await page.evaluate("JSON.stringify(JOURNAL[JOURNAL.length-1].at||null)")
    ok(L+"d. coché : tracé au journal",'"fait":true' in jt and '"j":3' in jt,jt)
    ok(L+"d. plus de bloc amelipro ni de durée suggérée",await page.locator("#at_prev,#at_copy").count()==0 and "durée indicative" not in await page.inner_text("body"))
    await page.uncheck("#xp_at"); await page.wait_for_timeout(200)
    cr=await page.evaluate("buildCR(currentPack())")
    ok(L+"d. décoché : rien au compte rendu","rrêt de travail" not in cr)
    # PDF iPhone (défaut trouvé le 17/10/2026) : taille normale si la page tient, réduite seulement si besoin, jamais sous 9 pt, sinon signalé
    r=await page.evaluate("""async()=>{newPatient();const i=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1985',sexe:'h'});state.sel=i;
      const fitOf=async out=>{const st=document.getElementById('pdfstage');const t=document.createElement('div');t.innerHTML=out;const R=[];for(const pg of [...t.children].filter(x=>x.classList.contains('page'))){st.innerHTML='';st.appendChild(pg);R.push({f:pdfFit(pg),o:pg.dataset.pdfover||'',fs:parseFloat(getComputedStyle(pg).fontSize)});}st.innerHTML='';return R;};
      const a=await fitOf(xpBuild(currentPack()));const p=currentPack();const si=p.s.findIndex(s=>s.k==='cons');
      state.libre[si]=Array(34).fill("Consigne supplémentaire de test : surveiller la température, l'hydratation et la respiration, reconsulter si besoin.").join(' ');const b=await fitOf(xpBuild(currentPack()));
      state.libre[si]=Array(220).fill("Consigne très longue de test pour dépasser une page même en petite police.").join(' ');const c=await fitOf(xpBuild(currentPack()));state.libre={};return {a,b,c};}""")
    ok(L+"PDF : page courte en taille normale (plus de 8,5 pt systématique)",all(x["f"]=="" and x["o"]=="" for x in r["a"]),r["a"])
    cb=[x for x in r["b"] if x["f"]]
    ok(L+"PDF : consignes longues réduites juste ce qu'il faut, ≥ 9 pt, sans signalement",cb and all(x["fs"]>=11.9 and x["o"]=="" for x in cb),r["b"])
    ok(L+"PDF : trop long même en dernier recours (8,5 pt) → signalé (l'Express ouvre alors l'aperçu)",any(x["o"]=="1" and x["fs"]>=11.3 for x in r["c"]),r["c"])
    # 2. Annuler (10 s) : le patient revient
    await page.evaluate("state.view='';render();")
    if mob:
        x=await page.evaluate("(()=>{const d=document.getElementById('xp_plus');return d?{open:d.open,has:!!d.querySelector('#f_patient')}:null;})()")
        ok(L+"« Plus » : dossier complet replié (identité, fiches, feuilles)",x and not x["open"] and x["has"],x)
    # 2. « Annuler » pendant 10 s : la validation est défaite, le patient revient
    await page.evaluate("render()"); await page.wait_for_timeout(300)
    for _ in range(80):
        if await page.evaluate("xpReady()||(!isPhone()&&!iosLike())"): break
        await page.wait_for_timeout(250)
    await page.click("#xp_go"); await page.wait_for_timeout(900)
    v=await page.evaluate("state.patient")
    ok(L+"2. après « Imprimer et valider » : patient validé, écran libéré",v!="DURAND Paul",v)
    await page.click("#xp_undo"); await page.wait_for_timeout(500)
    ok(L+"2. « Annuler » (10 s) : le patient revient tel quel",await page.evaluate("state.patient")=="DURAND Paul" and await page.evaluate("currentPack()&&currentPack().n")=="Rhinopharyngite — adulte")
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    allg={}
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,th,big,lbl,sh) in [(375,812,"day",False,"iphone jour",True),(375,812,"night",False,"iphone nuit",True),(375,812,"night",True,"iphone grand texte",True),(1280,900,"day",False,"ordinateur",True)]:
                allg[lbl]=await run(b,w,h,th,big,lbl,sh)
            await extras(b,375,812,"iphone")
            await extras(b,1280,900,"ordinateur")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK"); print("gestes :",allg)
    json.dump(allg,open(os.path.join(ROOT,"tests","resultats_express_gestes.json"),"w",encoding="utf-8"),ensure_ascii=False)
    open(os.path.join(ROOT,"tests","resultats_express.md"),"w",encoding="utf-8").write("# Tests Express visite (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n\nGestes : {json.dumps(allg,ensure_ascii=False)}\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
