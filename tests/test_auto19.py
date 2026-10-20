# Parcours automatisé avec l'IA (20/10/2026) — API Anthropic simulée (aucun appel réel, aucune donnée réelle, patients fictifs).
# Tests demandés : 1 contre-appel téléphonique (observation structurée, aucun examen inventé) ; 2 continuité contre-appel → visite ;
# 3 consultation : une dictée déclenche la préparation ; 4 le Pack (fiches) est réellement utilisé ; 5 correction manuelle jamais écrasée ;
# 6 coupure Internet : dictée gardée, rien de validé, demande en attente ; 7 changement de patient : rien d'attribué au mauvais patient ;
# 8 rien de validé sans geste explicite ; 9 impression et PDF ; 10 téléphone, tablette, ordinateur, Express et mode complet.
# + protection des dictées (champ touché repris avant rendu, dictées récentes), réglage « écran Ce qui part à chaque fois ».
# Lancer : python tests/test_auto19.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:800])
PORT=8815
KEY="sk-ant-test-0000-cle-factice"
def api_reply(obj):
    return {"id":"msg_test","type":"message","role":"assistant","model":"claude-sonnet-5-5","stop_reason":"end_turn",
            "content":[{"type":"text","text":json.dumps(obj,ensure_ascii=False)}],"usage":{"input_tokens":1500,"output_tokens":400,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}
BASE={"poids":"","sexe":"","grossesse":False,"allaitement":False,"allergie_penicilline":False,"allergies":[],"traitements":[],"cst":{},"obs":{},"remarques":[],"justification":[],"examens":[],"courrier_mt":False,"courrier_sp":None,"social":None,"suivi":[],"manques":[],"alertes":[]}
def R(**k): d=dict(BASE); d.update(k); return d
TEL="Maman dit fièvre à 39 depuis hier, tire l'oreille droite, mange moins, pas de boutons. Pas d'allergie, pas de traitement. Poids 15 kilos."
VIS="Tympan droit rouge et bombé, gauche normal. Gorge rouge. Abdomen souple. Température 38,8."
CAB="Lombalgie depuis 3 jours après un effort de soulèvement, pas de fièvre, pas de trouble sphinctérien. Rachis lombaire raide et douloureux, Lasègue négatif, pas de déficit. Patient isolé, vit seul, ne peut plus faire ses courses."
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
async def wait_sent(page,sent,n,ms=8000):
    for _ in range(ms//150):
        if len(sent)>=n: return True
        await page.wait_for_timeout(150)
    return False
async def dictate(page,sel,text):
    await page.evaluate("()=>{document.querySelectorAll('details').forEach(d=>d.open=true);}")
    loc=page.locator(sel+":visible").first
    await loc.click(); await loc.fill(text); await loc.dispatch_event("change"); await page.evaluate("()=>{if(document.activeElement)document.activeElement.blur();}")
STOP="""()=>{const s=tourAdd('12 rue des Lilas 45000 Orléans','PETIT Lou',false,null);s.nom='PETIT Lou';s.ddn='01/06/2023';s.tel='0612345678';s.motif='fièvre';tourSave();tourUse(s.id);return s.id;}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            CTX=[("iPhone · Express",{"viewport":{"width":390,"height":844},"device_scale_factor":2,"is_mobile":True,"has_touch":True},True),
                 ("iPhone · mode complet",{"viewport":{"width":390,"height":844},"device_scale_factor":2,"is_mobile":True,"has_touch":True},False),
                 ("tablette · Express",{"viewport":{"width":820,"height":1180},"is_mobile":True,"has_touch":True},True),
                 ("PC · mode complet",{"viewport":{"width":1280,"height":900}},False)]
            for label,dev,xp in CTX:
                L=label+" : "
                ctx=await b.new_context(**dev,permissions=["clipboard-read","clipboard-write"] if "PC" in label else None)
                sent=[]; replies=[]; delays=[]
                async def handle(route):
                    cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
                    if route.request.method=="OPTIONS": await route.fulfill(status=204,headers=cors); return
                    if delays: await asyncio.sleep(delays.pop(0))
                    sent.append({"headers":route.request.headers,"body":route.request.post_data or ""})
                    r=replies.pop(0) if replies else api_reply(R())
                    await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps(r,ensure_ascii=False))
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.fallback() if "anthropic" in r.request.url else (r.continue_() if "localhost" in r.request.url else r.abort())))
                await ctx.route("https://api.anthropic.com/**",handle)
                page=await ctx.new_page(); errors=[]; dialogs=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
                await unlock(page,"au"+("x" if xp else "c")+label[:2],xp)
                await page.evaluate(f"AI.key={json.dumps(KEY)};AI.cfg.mode='complet';AI.cfg.auto='on';AI.cfg.send='auto';aiSave();render();"); await page.wait_for_timeout(300)
                ok(L+"réglages persistants : IA complet, préparation automatique, envoi automatique après pseudonymisation",await page.evaluate("aiAutoOn()&&aiSendAuto()"))
                # ---------- 1. contre-appel téléphonique ----------
                sid=await page.evaluate(STOP); await page.wait_for_timeout(300)
                n0=len(sent)
                replies.append(api_reply(R(packs=["Fièvre — enfant","Otite moyenne aiguë — enfant"],justification=["fièvre depuis hier chez un enfant de 3 ans","otalgie droite rapportée"],poids="15",
                    cst={"temp":"39"},obs={"hist":"Au téléphone, fièvre à 39 depuis hier, tire l'oreille droite, mange moins.","resp":"Crépitants en base droite","hyp":"Otite moyenne aiguë probable"},
                    manques=["Examen des tympans sur place","État d'hydratation et comportement"],suivi=["Reconsulter si la fièvre persiste au-delà de 48 heures"],alertes=[])))
                await dictate(page,"textarea[data-interro]",TEL)
                got=await wait_sent(page,sent,n0+1)
                ok(L+"1. contre-appel dicté → requête envoyée automatiquement, sans écran intermédiaire",got and await page.locator("#aisend").count()==0,(got,len(sent)))
                body=sent[-1]["body"] if sent else ""
                ok(L+"1. requête : partie « CONTRE-APPEL TÉLÉPHONIQUE » seule, aucune partie « EN PRÉSENCE »","CONTRE-APPEL TÉLÉPHONIQUE" in body and "EN PRÉSENCE DU PATIENT" not in body and "SITUATION : contre-appel" in body,body[-400:])
                ok(L+"1. requête sans identité (nom, téléphone, adresse retirés)",not any(x in body for x in ["PETIT","Lou","0612345678","Lilas"]),[x for x in ["PETIT","Lou","0612345678","Lilas"] if x in body])
                await page.wait_for_timeout(600)
                st=await page.evaluate("({tel:state.obs.tel||'',hist:state.obs.hist||'',resp:state.obs.resp||'',temp:state.cst.temp||'',poids:state.poids,pick:state.xpPick!=null?PACKS[state.xpPick].n:null,plan:state.aiPlan?{phase:state.aiPlan.phase,n:state.aiPlan.packs.map(x=>x.n),m:state.aiPlan.manques}:null,stopAi:!!tourStop('"+sid+"').ai,card:!!document.querySelector('#aisyn')})")
                ok(L+"1. observation téléphonique structurée : histoire « Au téléphone, … », éléments rapportés gardés à part",st["hist"].startswith("Au téléphone") and st["tel"].startswith("Maman dit"),st)
                ok(L+"1. aucun examen ni constante inventés (appareil « pulmonaire » et température renvoyés par l'IA écartés en mode téléphone)",st["resp"]=="" and st["temp"]=="",st)
                ok(L+"1. fiche proposée d'après le Pack, synthèse visible avec ce qu'il faudra vérifier sur place, analyse gardée sur l'arrêt",st["pick"]=="Fièvre — enfant" and st["plan"] and st["plan"]["phase"]=="tel" and st["plan"]["m"] and st["stopAi"] and st["card"],st)
                cr=await page.evaluate("buildCR0(PACKS[state.xpPick])")
                ok(L+"1. compte rendu : section « contre-appel téléphonique, patient non examiné », aucune section d'examen clinique","CONTRE-APPEL TÉLÉPHONIQUE" in cr and "NON EXAMINÉ" in cr and "EXAMEN CLINIQUE" not in cr,cr[:400])
                if "iPhone" in label:
                    await page.evaluate("()=>{const e=document.getElementById('aisyn');if(e)e.scrollIntoView({block:'start'});}"); await page.wait_for_timeout(200)
                    await page.screenshot(path=os.path.join(OUT,f"auto19-contre-appel-{'express' if xp else 'complet'}.png"))
                # ---------- 5. correction manuelle (avant la visite) ----------
                await page.evaluate("state.obs.atcd='Asthme dans l\\'enfance (saisi à la main)';(state.obsEdited=state.obsEdited||{}).atcd=true;")
                # ---------- 2. continuité : dictée en visite ----------
                n0=len(sent)
                replies.append(api_reply(R(packs=["Otite moyenne aiguë — enfant"],justification=["tympan droit bombé constaté"],poids="15",cst={"temp":"38,8"},
                    obs={"hist":"Au téléphone, fièvre à 39 depuis hier et otalgie droite ; sur place, tympan droit rouge et bombé.","atcd":"Aucun antécédent","orl":"Tympan droit rouge et bombé, gauche normal. Gorge rouge.","abdo":"Abdomen souple.","hyp":"Otite moyenne aiguë droite"},
                    courrier_mt=False,suivi=["Reconsulter si la fièvre persiste 48 heures après le début de l'antibiotique"],manques=[],alertes=[])))
                await dictate(page,"#f_dict",VIS)
                got=await wait_sent(page,sent,n0+1); body=sent[-1]["body"] if got else ""
                ok(L+"2. dictée en visite → une requête avec les deux parties (contre-appel rapporté + dictée après examen)",got and "CONTRE-APPEL TÉLÉPHONIQUE" in body and "EN PRÉSENCE DU PATIENT" in body and "Maman dit" in body and "Tympan droit" in body,body[-500:])
                await page.wait_for_timeout(600)
                st=await page.evaluate("({tel:state.obs.tel||'',hist:state.obs.hist||'',orl:state.obs.orl||'',atcd:state.obs.atcd||'',temp:state.cst.temp||'',phase:state.aiPlan&&state.aiPlan.phase,pick:state.xpPick!=null?PACKS[state.xpPick].n:null})")
                ok(L+"2. continuité : contre-appel conservé, examen constaté ajouté, histoire actualisée, température constatée reprise",st["tel"].startswith("Maman dit") and "Tympan droit" in st["orl"] and "sur place" in st["hist"] and st["temp"]=="38,8" and st["phase"]=="visite",st)
                ok(L+"5. correction manuelle (antécédents) jamais écrasée par l'IA","saisi à la main" in st["atcd"],st["atcd"])
                cr=await page.evaluate("buildCR0(PACKS[state.xpPick])")
                ok(L+"2. compte rendu : contre-appel à part, puis examen clinique constaté","CONTRE-APPEL TÉLÉPHONIQUE" in cr and "EXAMEN CLINIQUE" in cr and cr.index("CONTRE-APPEL")<cr.index("EXAMEN CLINIQUE"),cr[:600])
                # ---------- protection de la dictée : champ touché, pas d'événement input, puis rendu ----------
                await page.evaluate("()=>{const f=document.getElementById('f_dict');f.focus();f.value=f.value+' Nuque souple.';render();}")
                ok(L+"dictée jamais perdue : texte ajouté dans le champ (sans événement) repris à l'écran suivant","Nuque souple" in await page.evaluate("state.obs.dict"),await page.evaluate("state.obs.dict"))
                # ---------- 7. changement de patient pendant une requête ----------
                n0=len(sent); delays.append(1.6)
                replies.append(api_reply(R(packs=["Otite moyenne aiguë — enfant"],obs={"hist":"Au téléphone, fièvre ; sur place tympan bombé ; ajout tardif pour le patient A."})))
                await dictate(page,"#f_dict",VIS+" Pas de raideur de nuque.")
                await page.wait_for_timeout(900)
                await page.evaluate("newPatient();Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1975',sexe:'h'});state.cot.lieu='consultation';state.cot.auto=false;render();")
                await wait_sent(page,sent,n0+1); await page.wait_for_timeout(1200)
                st=await page.evaluate("({pat:state.patient,hist:state.obs.hist||'',tel:state.obs.tel||'',plan:!!state.aiPlan,dict:state.obs.dict||''})")
                ok(L+"7. changement de patient pendant la requête : la réponse n'est attribuée ni appliquée au nouveau patient",st["pat"]=="DURAND Paul" and st["hist"]=="" and st["tel"]=="" and not st["plan"] and st["dict"]=="",st)
                ok(L+"dictées récentes : la dictée du patient précédent reste reprenable (48 h)",await page.evaluate("DICTH.some(x=>/Tympan droit rouge/.test(x.txt))"))
                # ---------- 3. consultation au cabinet : une dictée → préparation ; 4. Pack ; 8. validation ----------
                n0=len(sent)
                replies.append(api_reply(R(packs=["Lombalgie aiguë"],justification=["lombalgie mécanique après effort, sans drapeau rouge"],sexe="h",
                    obs={"hist":"Lombalgie depuis 3 jours après un effort de soulèvement, sans fièvre ni trouble sphinctérien.","loco":"Rachis lombaire raide et douloureux, Lasègue négatif.","neuro":"Pas de déficit.","hyp":"Lombalgie aiguë commune"},
                    examens=[{"t":"Radiographie du rachis lombaire","pourquoi":"douleur persistante après effort, à discuter si pas d'amélioration"}],
                    courrier_mt=True,courrier_sp={"dest":"rhumatologue","question":"Une infiltration vous paraît-elle indiquée en cas d'échec du traitement médical ?","pourquoi":"lombalgie invalidante"},
                    social={"besoin":"isolement, courses impossibles","orientation":"aide à domicile (CCAS), évaluation APA","pourquoi":"vit seul, perte d'autonomie temporaire"},
                    suivi=["Reconsulter en l'absence d'amélioration ou en cas de déficit"],manques=["Poids"],alertes=[])))
                await dictate(page,"#f_dict",CAB)
                got=await wait_sent(page,sent,n0+1); body=sent[-1]["body"] if got else ""; sysm=""
                try:
                    jb=json.loads(body); sysm="".join(x.get("text","") for x in jb.get("system",[]))
                except Exception: pass
                ok(L+"3. consultation : une dictée déclenche la préparation automatique (une seule requête)",got and len(sent)==n0+1 and "SITUATION : consultation au cabinet" in body,(got,len(sent)-n0))
                ok(L+"4. le Pack SOS Médecins est transmis à l'IA : liste des fiches dans les consignes, « Lombalgie aiguë » incluse","LISTE DES FICHES" in sysm and "Lombalgie aiguë" in sysm and "Otite moyenne aiguë — enfant" in sysm,len(sysm))
                await page.wait_for_timeout(700)
                st=await page.evaluate("({sel:state.sel,pick:state.xpPick!=null?PACKS[state.xpPick].n:null,mt:!!(state.lettres&&state.lettres.mt&&state.lettres.mt.on),sp:!!(state.lettres&&state.lettres.sp&&state.lettres.sp.on),card:!!document.querySelector('#aisyn'),txt:(document.querySelector('#aisyn')||{}).innerText||'',valid:VALID.hist.filter(v=>v.patient==='DURAND Paul').length,view:state.view})")
                ok(L+"3. synthèse affichée : fiche, observation, examens, courriers, aide sociale, suivi, à vérifier",st["card"] and all(x in st["txt"] for x in ["Lombalgie aiguë","Radiographie du rachis lombaire","Médecin traitant","Spécialiste : Rhumatologue","aide à domicile","Reconsulter en l'absence","Poids"]),st["txt"][:600])
                ok(L+"8. avant « Appliquer » : fiche seulement proposée, aucun courrier activé, rien validé",st["sel"] is None and st["pick"]=="Lombalgie aiguë" and not st["mt"] and not st["sp"] and st["valid"]==0 and st["view"]!="valid",st)
                if "PC" in label: await page.screenshot(path=os.path.join(OUT,"auto19-synthese-pc.png"))
                if "iPhone" in label and xp:
                    await page.evaluate("()=>{const e=document.getElementById('aisyn');if(e)e.scrollIntoView({block:'start'});}"); await page.wait_for_timeout(200)
                    await page.screenshot(path=os.path.join(OUT,"auto19-synthese-iphone.png"))
                await page.locator("#aisyn_apply").first.click(); await page.wait_for_timeout(500)
                st=await page.evaluate("""()=>{const p=currentPack();const L=letState();const med=[];let extraMed=0,examOn=false,extraBio=[];p.s.forEach((sh,si)=>{if(sh.k==='med'){resolve(sh,si).forEach(x=>{if(x.on)med.push(x.fill.s.slice(0,50));});extraMed+=(state.extra[si]||[]).length;}
                  if(sh.k==='img'||sh.k==='bio'){resolve(sh,si).forEach(x=>{if(x.on&&/rachis lombaire/i.test(x.fill.s))examOn=true;});extraBio.push(...(state.extra[si]||[]));}});
                  const packMed=PACKS[selIdx()[0]].s.find(s=>s.k==='med');const packLines=(packMed?packMed.l:[]).map(l=>typeof l==='string'?l:l.t);
                  return {sel:selIdx().map(i=>PACKS[i].n),mt:!!(L.mt&&L.mt.on),sp:L.sp&&L.sp.on?L.sp.dest:null,q:L.sp&&L.sp.question||'',med,extraMed,examOn:examOn||extraBio.some(x=>/rachis lombaire/i.test(x)),letter:letText(p,'sp'),valid:VALID.hist.filter(v=>v.patient==='DURAND Paul').length,view:state.view,applied:!!(state.aiPlan&&state.aiPlan.applied),fromPack:med.every(m=>packLines.some(t=>norm(t).startsWith(norm(m).slice(0,20))))};}""")
                ok(L+"3. « Appliquer la synthèse » (un geste) : fiche confirmée, fiche sociale complémentaire, courriers préparés, examen coché ou ajouté",st["sel"] and st["sel"][0]=="Lombalgie aiguë" and any("maintien" in x for x in st["sel"]) and st["mt"] and st["sp"]=="rhumato" and st["examOn"] and st["applied"],st)
                ok(L+"4. l'ordonnance vient de la fiche du Pack : aucune ligne de traitement écrite par l'IA",st["med"] and st["extraMed"]==0 and st["fromPack"],(st["med"][:3],st["extraMed"]))
                ok(L+"3. courrier au spécialiste : la question préparée par la synthèse y figure, l'IA n'écrit pas le courrier","infiltration" in st["letter"] and "Cher confrère" in st["letter"],st["letter"][:300])
                ok(L+"8. après application : toujours rien de validé (impression et « Valider » restent vos gestes)",st["valid"]==0 and st["view"]!="valid",(st["valid"],st["view"]))
                # ---------- 9. impression et PDF ----------
                pg=await page.evaluate("(()=>{const r=buildPages(currentPack(),true);const d=document.createElement('div');d.innerHTML=r.out;return [...d.querySelectorAll('.page h2')].map(h=>h.textContent);})()")
                ok(L+"9. documents prêts à imprimer : ordonnance et courriers produits",any(h.startswith("Ordonnance") for h in pg) and sum(1 for h in pg if h.startswith("Courrier"))>=2,pg)
                # ---------- 8. validation explicite : deux touchers, jamais automatique ----------
                v1=await page.evaluate("(()=>{valGate._w=0;patientValidate();return state.view;})()")
                v2=await page.evaluate("(()=>{patientValidate();return state.view;})()")
                ok(L+"8. validation : 1er toucher demande confirmation, 2e toucher valide ; jamais sans geste",v1!="valid" and v2=="valid" and not dialogs,[v1,v2,dialogs[:1]])
                await page.evaluate("patientNext();render();")
                # ---------- 6. coupure Internet ----------
                await page.evaluate("newPatient();Object.assign(state,{patient:'MARTIN Jeanne',ddn:'05/06/1975',sexe:'f'});state.cot.lieu='consultation';state.cot.auto=false;render();")
                await ctx.set_offline(True); await page.evaluate("window.dispatchEvent(new Event('offline'))"); await page.wait_for_timeout(300)
                n0=len(sent); q0=await page.evaluate("AIQ.list.length")
                await dictate(page,"#f_dict","Toux sèche depuis 5 jours, pas de fièvre, auscultation normale, pas de dyspnée.")
                await page.wait_for_timeout(1500)
                st=await page.evaluate("({sent:0,q:AIQ.list.length,dict:state.obs.dict||'',view:state.view,plan:!!state.aiPlan,valid:VALID.hist.filter(v=>v.patient==='MARTIN Jeanne').length})")
                ok(L+"6. hors connexion : rien n'est envoyé, la demande est gardée sur l'appareil, la dictée est conservée, rien n'est validé",len(sent)==n0 and st["q"]==q0+1 and "Toux sèche" in st["dict"] and st["view"]!="valid" and st["valid"]==0,st)
                await ctx.set_offline(False); await page.evaluate("window.dispatchEvent(new Event('online'))"); await page.wait_for_timeout(500)
                replies.append(api_reply(R(packs=["Bronchite aiguë"],obs={"hist":"Toux sèche depuis 5 jours, sans fièvre.","resp":"Auscultation normale, pas de dyspnée.","hyp":"Bronchite aiguë"})))
                await page.evaluate("aiqOpen(AIQ.list[AIQ.list.length-1].id)"); await page.wait_for_timeout(300)
                ok(L+"6. retour du réseau : la demande en attente est reproposée à l'écran « Ce qui part »",await page.locator("#aisend #ai_send").count()==1)
                await page.click("#aisend #ai_send"); got=await wait_sent(page,sent,n0+1); await page.wait_for_timeout(700)
                st=await page.evaluate("({pick:state.xpPick!=null?PACKS[state.xpPick].n:null,hist:state.obs.hist||'',q:AIQ.list.length})")
                ok(L+"6. envoi au retour du réseau : synthèse appliquée au bon patient, file vidée",got and st["pick"]=="Bronchite aiguë" and "Toux sèche" in st["hist"] and st["q"]==q0,st)
                # ---------- réglage « écran Ce qui part à chaque fois » ----------
                await page.evaluate("AI.cfg.send='ecran';aiSave();newPatient();Object.assign(state,{patient:'BERNARD Luc',ddn:'02/02/1980',sexe:'h'});state.cot.lieu='consultation';state.cot.auto=false;render();")
                n0=len(sent)
                await dictate(page,"#f_dict","Mal de gorge depuis 2 jours avec fièvre à 38,5, amygdales rouges avec points blancs, pas de toux.")
                await page.wait_for_timeout(1200)
                ok(L+"réglage « écran Ce qui part à chaque fois » : rien ne part sans le bouton Envoyer",len(sent)==n0 and await page.locator("#aisend #ai_send").count()==1)
                await page.click("#aisend #ai_cancel"); await page.evaluate("AI.cfg.send='auto';aiSave();")
                # ---------- 10. compatibilité ----------
                ok(L+"10. aucune erreur JS",not errors,errors[:3])
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_auto19.md"),"w",encoding="utf-8").write("# Parcours automatisé avec l'IA (20/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
