# Cahier des charges du 20/10/2026 — parcours de visite (tests 10, 11, 12) : « Commencer », étapes, contre-appel dès l'étape 1, numéro d'appel visible,
# identification NOM P., arrivée et cotation à l'heure réelle (corrigeable, jamais changée après validation sans geste), réouverture tracée
# (validation initiale conservée, revalidation versionnée au journal), patient suivant, Express (mode voiture et tournée dans les favoris).
# Patients fictifs. Lancer : python tests/test_parcours20.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:800])
PORT=8816
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_excomplet','0')}}catch(e){{}}")
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
STOPS="""()=>{TOUR.stops=[];TOUR.order=[];TOUR.current='';TOUR.computed=false;delete TOUR.started;newPatient();state.cot.lieu='visite';state.cot.auto=false;
  const a=tourAdd('12 rue des Lilas 45000 Orléans','DUPONT Jean',false,{lat:47.9,lon:1.9,label:'12 rue des Lilas',city:'Orléans'});Object.assign(a,{nom:'DUPONT Jean',ddn:'01/01/1950',tel:'0612345678',motif:'lombalgie'});
  const b=tourAdd('3 rue Bannier 45000 Orléans','MARTIN Jeanne',false,{lat:47.91,lon:1.91,label:'3 rue Bannier',city:'Orléans'});Object.assign(b,{nom:'MARTIN Jeanne',ddn:'05/06/1975',tel:'0698765432',motif:'fièvre'});
  TOUR.order=[a.id,b.id];tourSave();render();return [a.id,b.id];}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for label,dev,xp in [("PC · mode complet",{"viewport":{"width":1280,"height":900}},False),("iPhone · Express",{"viewport":{"width":390,"height":844},"device_scale_factor":2,"is_mobile":True,"has_touch":True},True)]:
                L=label+" : "
                ctx=await b.new_context(**dev)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; dialogs=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
                await unlock(page,"p20"+("x" if xp else "c"),xp)
                ids=await page.evaluate(STOPS); await page.wait_for_timeout(400)
                # ---------- 12.3 identification, 12.4 appel ----------
                nm=await page.evaluate(f"stopName(tourStop('{ids[0]}'))")
                ok(L+"12.3 identification : NOM + initiale du prénom · âge · rue (plus seulement l'initiale)",nm.startswith("DUPONT J. · ") and " ans · " in nm and nm.endswith("rue des Lilas"),nm)
                if xp:
                    rows=await page.evaluate("[...document.querySelectorAll('.xp-row')].map(r=>r.innerText.replace(/\\s+/g,' '))")
                    ok(L+"12.3 liste des patients (Express) : DUPONT J. et MARTIN J. distingués",any("DUPONT J." in r for r in rows) and any("MARTIN J." in r for r in rows),rows)
                    await page.evaluate(f"xpOpenStop('{ids[0]}')"); await page.wait_for_timeout(500)
                    head=await page.evaluate("(document.querySelector('.xp-who')||{}).innerText||''"); call=await page.evaluate("[...document.querySelectorAll('.xp a[href^=\"tel:\"]')].map(a=>a.textContent)")
                    ok(L+"12.4 Express : numéro visible sur le bouton d'appel, en tête du dossier",any("06 12 34 56 78" in c for c in call) and "DUPONT" in head,(call,head))
                    favs=await page.evaluate("()=>{document.querySelectorAll('details').forEach(d=>d.open=true);return [...document.querySelectorAll('.xp #xp_favs .btn, .xp #xp_favs button')].map(b=>b.id||b.textContent.trim());}")
                    ok(L+"11 Express : « Mode voiture » et « Tournée » accessibles d'un toucher (favoris par défaut)","tc_drive" in favs and "tc_view" in favs,favs)
                    tel=await page.evaluate("document.querySelectorAll('.xp textarea[data-interro]').length")
                    ok(L+"6 Express : contre-appel dictable avant l'arrivée",tel>=1,tel)
                    pk=await page.evaluate("PACKS.findIndex(p=>p.n==='Lombalgie aiguë')")
                    await page.evaluate(f"window.__toasts=[];const t0=window.toast;window.toast=m=>{{window.__toasts.push(m);t0(m);}};xpConfirm({pk})"); await page.wait_for_timeout(900)
                    st=await page.evaluate(f"({{arr:!!tourStop('{ids[0]}').tArr,h:state.cot.hArr,t:window.__toasts.join(' | ')}})")
                    ok(L+"12.5 Express : confirmer la fiche enregistre l'arrivée, annoncée (heure de l'acte modifiable)",st["arr"] and st["h"] and "Arrivée enregistrée" in st["t"],st)
                    ok(L+"aucune erreur JS",not errors,errors[:3]); await ctx.close(); continue
                # ---------- 12.1 « Commencer », étapes 1 → 2 → 3 ----------
                await page.evaluate("()=>{document.querySelectorAll('details').forEach(d=>d.open=true);}")
                st=await page.evaluate("({begin:!!document.querySelector('#tc_begin'),step:(document.querySelector('.tc-steps li.on')||{}).textContent||'',tel:document.querySelectorAll('.tcard textarea[data-interro]').length,call:[...document.querySelectorAll('.tcard a[href^=\"tel:\"]')].map(a=>a.textContent)})")
                ok(L+"12.1 tournée prête : bouton « Commencer », contre-appel dictable dès l'étape 1, numéro visible sur « Appeler »",st["begin"] and st["step"]=="Tournée" and st["tel"]>=1 and any("06 12 34 56 78" in c for c in st["call"]),st)
                await page.click("#tc_begin")
                for _ in range(40):
                    if await page.evaluate("!!TOUR.current"): break
                    await page.wait_for_timeout(250)
                await page.wait_for_timeout(400)
                st=await page.evaluate("({cur:TOUR.current,lieu:state.cot.lieu,pat:state.patient,step:(document.querySelector('.tc-steps li.on')||{}).textContent||'',arrive:!!document.querySelector('#tc_arrive'),dict:!!document.querySelector('#tc_dict'),nav:!!document.querySelector('.tcard .tc-nav')})")
                ok(L+"12.1 « Commencer » démarre la visite : premier arrêt en cours, dossier prérempli, étape « En route » avec Naviguer, Je suis arrivé, Dictée",st["cur"]==ids[0] and st["lieu"]=="visite" and st["pat"]=="DUPONT Jean" and st["step"]=="En route" and st["arrive"] and st["dict"] and st["nav"],st)
                await page.evaluate("window.__toasts=[];const t0=window.toast;window.toast=m=>{window.__toasts.push(m);t0(m);};"); await page.click("#tc_arrive"); await page.wait_for_timeout(500)
                st=await page.evaluate(f"({{arr:!!tourStop('{ids[0]}').tArr,h:state.cot.hArr,step:(document.querySelector('.tc-steps li.on')||{{}}).textContent||'',dict:!!document.querySelector('#tc_dict'),rx:!!document.querySelector('#tc_rx'),t:window.__toasts.join(' | ')}})")
                ok(L+"12.1 « Je suis arrivé » : heure d'arrivée enregistrée et annoncée, étape « Sur place » (dictée, prescriptions)",st["arr"] and st["h"] and st["step"]=="Sur place" and st["dict"] and st["rx"] and "Arrivée enregistrée" in st["t"],st)
                # ---------- 12.5 cotation à l'heure réelle ----------
                pk=await page.evaluate("PACKS.findIndex(p=>p.n==='Lombalgie aiguë')")
                await page.evaluate(f"state.sel={pk};state.cot.hArr='07:40';state.cot.h='';render();")
                await page.evaluate("state.lastPrint={n:1,sent:true,ts:Date.now()};patientValidate(true);"); await page.wait_for_timeout(400)
                st=await page.evaluate("""()=>{const e=JOURNAL.slice().reverse().find(x=>x.patient==='DUPONT Jean');const c=cotCompute(e);return {acte:fmtHM(e.tActe),slot:pdsSlot(new Date(e.tActe)),codes:c.codes.map(x=>x.c),view:state.view,v:VALID.hist[0]&&{rev:VALID.hist[0].rev,cot:VALID.hist[0].cot&&VALID.hist[0].cot.codes}};}""")
                ok(L+"12.5 cotation sur l'heure réelle de l'acte (arrivée 07:40), pas sur l'heure de validation",st["acte"]=="07:40" and st["slot"]=="N" and "VRN" in st["codes"] and st["view"]=="valid" and st["v"]["rev"]==1,st)
                # ---------- 12.2 retour sur une visite validée : trace, document initial conservé ----------
                await page.evaluate("validListScreen()"); await page.wait_for_timeout(300)
                ok(L+"12.2 « Patients validés » : la visite validée est listée avec sa cotation",await page.locator("#lock .vrow").count()>=1 and "VRN" in await page.inner_text("#lock .vlist"))
                await page.locator("#lock [data-vopen]").first.click(); await page.wait_for_timeout(500)
                st=await page.evaluate("({pat:state.patient,view:state.view,n:VALID.hist.length,reopened:!!(VALID.hist[0]&&VALID.hist[0].reopened),revOf:state.revOf,last:VALID.last})")
                ok(L+"12.2 rouvrir : dossier remis tel quel, validation initiale conservée dans la liste (marquée rouverte), aucune nouvelle validation implicite",st["pat"]=="DUPONT Jean" and st["view"]=="" and st["n"]==1 and st["reopened"] and st["revOf"] and st["last"] is None,st)
                # cotation validée inchangée sans geste ; corrigée après un geste
                await page.evaluate("state.lastPrint={n:1,sent:true,ts:Date.now()};patientValidate(true);"); await page.wait_for_timeout(400)
                st=await page.evaluate("""()=>{const e=JOURNAL.slice().reverse().find(x=>x.patient==='DUPONT Jean');return {acte:fmtHM(e.tActe),codes:cotCompute(e).codes.map(x=>x.c),n:VALID.hist.length,rev:VALID.hist[0].rev,of:VALID.hist[0].of,orig:VALID.hist[1]&&VALID.hist[1].id,notes:(e.notes||[]).join(' | '),txt:(document.querySelector('#main')||{}).innerText||''};}""")
                ok(L+"12.2 revalidation : version 2 liée à la validation initiale (conservée), tracée au journal, affichée",st["n"]==2 and st["rev"]==2 and st["of"]==st["orig"] and "revalidé (version 2)" in st["notes"] and "version" in st["txt"].lower(),st)
                ok(L+"12.5 cotation validée inchangée sans geste du médecin",st["acte"]=="07:40" and "VRN" in st["codes"],st)
                await page.evaluate("validListScreen()"); await page.wait_for_timeout(200); await page.locator("#lock [data-vopen]").first.click(); await page.wait_for_timeout(400)
                await page.evaluate("state.cot.h='08:10';state.lastPrint={n:1,sent:true,ts:Date.now()};patientValidate(true);"); await page.wait_for_timeout(400)
                st=await page.evaluate("""()=>{const e=JOURNAL.slice().reverse().find(x=>x.patient==='DUPONT Jean');return {acte:fmtHM(e.tActe),codes:cotCompute(e).codes.map(x=>x.c),rev:VALID.hist[0].rev};}""")
                ok(L+"12.5 heure de l'acte corrigée à la main (08:10) : cotation recalculée sur ce geste, version 3",st["acte"]=="08:10" and "VRN" not in st["codes"] and "VG" in st["codes"] and st["rev"]==3,st)
                # ---------- patient suivant ----------
                await page.evaluate("patientNext();render();"); await page.wait_for_timeout(400)
                st=await page.evaluate("({cur:TOUR.current,pat:state.patient,done:tourStop('"+ids[0]+"').done})")
                ok(L+"12.2 « Patient suivant » : arrêt précédent fait, visite suivante ouverte (MARTIN Jeanne)",st["cur"]==ids[1] and st["pat"]=="MARTIN Jeanne" and st["done"],st)
                ok(L+"pastille patient : NOM P. · âge · rue",re.match(r"^MARTIN J\. · \d+ ans · ",await page.evaluate("patLabel()")),await page.evaluate("patLabel()"))
                ok(L+"aucune fenêtre système, aucune erreur JS",not dialogs and not errors,(dialogs[:2],errors[:3]))
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_parcours20.md"),"w",encoding="utf-8").write("# Parcours de visite (20/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
