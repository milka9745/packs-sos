# v41z (21/10/2026, demande globale III) — réponse IA : modèle par étape, flux continu avec progression et « Arrêter »,
# premier essai borné puis une seule relance sur le modèle rapide, 60 s au total, résultat incomplet jamais appliqué,
# coupure réseau = arrêt immédiat, doutes à confirmer sur « Ce qui part », reprise de la file au retour du réseau, consommation détaillée.
# API simulée localement (aucun appel externe) ; patient fictif.
import asyncio, os, re, json, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8787
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page):
    await page.add_init_script("try{localStorage.setItem('sos_xp','false');}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testia41z"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(600)

MOCK={"delays":[],"stop":"end_turn","calls":[],"kind":"plan"}
PLAN={"packs":["Lombalgie aiguë"],"justification":["douleur lombaire mécanique sans signe neurologique"],"poids":"","sexe":"f","grossesse":False,"allaitement":False,"allergie_penicilline":False,"allergies":[],"traitements":[],"cst":{},"obs":{"hist":"Douleur lombaire depuis deux jours, sans fièvre.","atcd":"","hyp":"Lombalgie aiguë","trace":""},"examens":[],"courrier_mt":False,"courrier_sp":None,"social":None,"suivi":["reconsulter si déficit"],"manques":[],"alertes":[],"remarques":[]}
CR={"manques":[],"reformulations":[],"raisonnement":"","information":"","courrier":None}
def sse(model,text,stop):
    ev=[]
    ev.append('event: message_start\ndata: {"type":"message_start","message":{"id":"msg_1","model":"%s","usage":{"input_tokens":120,"output_tokens":0}}}\n\n'%model)
    for i in range(0,len(text),40):
        ev.append('event: content_block_delta\ndata: %s\n\n'%json.dumps({"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":text[i:i+40]}},ensure_ascii=False))
    ev.append('event: message_delta\ndata: %s\n\n'%json.dumps({"type":"message_delta","delta":{"stop_reason":stop},"usage":{"output_tokens":60}}))
    ev.append('event: message_stop\ndata: {"type":"message_stop"}\n\n')
    return "".join(ev)
async def api_mock(route):
    try: body=json.loads(route.request.post_data or "{}")
    except Exception: body={}
    n=len(MOCK["calls"]); MOCK["calls"].append({"model":body.get("model"),"stream":body.get("stream"),"t":time.time()})
    d=MOCK["delays"][n] if n<len(MOCK["delays"]) else 0
    if d: await asyncio.sleep(d)
    text=json.dumps(PLAN if MOCK["kind"]=="plan" else CR,ensure_ascii=False)
    await route.fulfill(status=200,content_type="text/event-stream",body=sse(body.get("model","m"),text,MOCK["stop"]))

async def prepare(page):
    await page.evaluate("""()=>{AI.pending=null;AI.busy=false;AI.res=null;state.aiPlan=null;const e=document.getElementById('aisend');if(e)e.remove();AI._planHash='';
      Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.obs=state.obs||{};state.obs.dict='Douleur lombaire depuis deux jours sans fièvre, pas de déficit moteur.';state.cot.lieu='consultation';
      aiAutoFlow('cabinet',{manual:true});}""")
    await page.wait_for_selector("#aisend",timeout=5000)

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1280,"height":900})
            await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
            await ctx.route(re.compile(r".*api\.anthropic\.com/v1/messages.*"),api_mock)
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page)
            await page.evaluate("()=>{AI.key='sk-ant-test-0000';AI.cfg.mode='complet';AI.cfg.auto='on';AI.cfg.send='ecran';AI.cfg.cap=50;aiSave();Object.assign(AI_BOUNDS,{t1:1500,t2:1200,total:3000});}")
            # ---------- modèle par étape ----------
            await prepare(page)
            m1=await page.evaluate("AI.pending&&AI.pending.model")
            ok("III.8 : observation et suggestions (synthèse) sur le modèle rapide (Haiku)","haiku" in str(m1),m1)
            await page.evaluate("()=>{AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');aiPrepare('cr',{cr:true,let:true,demande:''});}")
            m2=await page.evaluate("AI.pending&&AI.pending.model"); await page.evaluate("()=>{AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();aiPrepare('cr',{cr:true,let:false,demande:''});}")
            m3=await page.evaluate("AI.pending&&AI.pending.model")
            ok("III.8 : courrier (document rédigé) sur le modèle complet (Sonnet), relecture seule sur le modèle rapide","sonnet" in str(m2) and "haiku" in str(m3),(m2,m3))
            await page.evaluate("()=>{AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();state.sel=null;}")
            # ---------- réponse en flux, progression, consommation ----------
            MOCK.update(delays=[0.6],stop="end_turn",calls=[],kind="plan")
            await prepare(page)
            sent=await page.evaluate("()=>({dis:document.getElementById('ai_send').disabled,btn:document.getElementById('ai_send').textContent,n:document.querySelectorAll('#aisend .aiact .btn').length})")
            ok("II.7 : écran « Ce qui part » avec un seul bouton principal « Envoyer »",sent["btn"]=="Envoyer" and sent["n"]==1,sent)
            await page.click("#ai_send"); await page.wait_for_timeout(250)
            prog=await page.evaluate("()=>{const e=document.getElementById('aiprog');return e?{txt:e.textContent,stop:!!e.querySelector('#aiprog_stop'),bar:!!e.querySelector('.aibar')}:null;}")
            ok("III.9 : affichage en continu dès la première seconde (progression, modèle, bouton « Arrêter »)",prog and prog["stop"] and prog["bar"] and "Haiku" in prog["txt"],prog)
            await page.wait_for_function("state.aiPlan&&state.aiPlan.packs&&state.aiPlan.packs.length>0",timeout=8000)
            res=await page.evaluate("()=>({packs:state.aiPlan.packs.map(x=>x.n),use:AI.use.slice(-1)[0],prog:!!document.getElementById('aiprog'),send:!!document.getElementById('aisend')})")
            ok("III.10 : résultat complet appliqué, progression refermée, écran d'envoi fermé",res["packs"]==["Lombalgie aiguë"] and not res["prog"] and not res["send"],res)
            ok("III.13 : consommation par appel — modèle, temps de réponse, temps d'anonymisation, coût",res["use"] and "haiku" in res["use"]["model"] and res["use"]["ms"]>=500 and res["use"]["am"]>=0 and res["use"]["eur"]>0,res["use"])
            # ---------- premier essai trop long → une seule relance sur le modèle rapide, résultat complet ----------
            MOCK.update(delays=[9,0.2],calls=[],stop="end_turn")
            await prepare(page); await page.click("#ai_send")
            await page.wait_for_function("state.aiPlan&&state.aiPlan.packs&&state.aiPlan.packs.length>0",timeout=12000)
            r2=await page.evaluate("()=>({calls:AI.use.slice(-2).map(u=>({model:u.model,retry:u.retry})),log:(state.aiLog||[]).slice(-3).map(x=>x.quoi)})")
            ok("III.10 : premier essai au-delà de la borne → une seule relance automatique sur le modèle rapide, même travail complet",len(MOCK["calls"])==2 and "haiku" in str(MOCK["calls"][1]["model"]) and any("relance" in x for x in r2["log"]),(len(MOCK["calls"]),r2))
            # ---------- deux essais trop longs → arrêt net à 60 s (ici 3 s), message clair, un seul bouton « Réessayer », rien d'appliqué ----------
            MOCK.update(delays=[9,9],calls=[])
            await prepare(page); t0=time.time(); await page.click("#ai_send")
            await page.wait_for_selector("#aisend .aifail",timeout=12000); dt=time.time()-t0
            f=await page.evaluate("()=>({msg:document.querySelector('#aisend .aifail').textContent,btn:document.getElementById('ai_send').textContent,plan:state.aiPlan,res:AI.res,prog:!!document.getElementById('aiprog')})")
            ok("III.10 : total maximal atteint → arrêt net, message clair, bouton « Réessayer », aucun résultat partiel affiché ni enregistré",dt<6 and "Délai" in f["msg"] and "rien n'est modifié" in f["msg"].lower() and f["btn"]=="Réessayer" and f["plan"] is None and f["res"] is None and not f["prog"] and len(MOCK["calls"])==2,(round(dt,1),f["msg"],f["btn"],len(MOCK["calls"])))
            # ---------- « Arrêter » : arrêt immédiat, pas de relance ----------
            MOCK.update(delays=[9,9],calls=[])
            await prepare(page); await page.click("#ai_send"); await page.wait_for_selector("#aiprog_stop",timeout=3000); await page.click("#aiprog_stop")
            await page.wait_for_selector("#aisend .aifail",timeout=5000)
            s=await page.evaluate("()=>({msg:document.querySelector('#aisend .aifail').textContent,calls:AI.use.length})"); await page.wait_for_timeout(1500)
            ok("III.9 : « Arrêter » interrompt immédiatement, sans relance",("Arrêt" in s["msg"]) and len(MOCK["calls"])==1,(s["msg"],len(MOCK["calls"])))
            # ---------- réponse tronquée (max_tokens) : jamais appliquée, pas de relance ----------
            MOCK.update(delays=[0.2],calls=[],stop="max_tokens")
            await prepare(page); await page.click("#ai_send"); await page.wait_for_selector("#aisend .aifail",timeout=6000)
            t=await page.evaluate("()=>({msg:document.querySelector('#aisend .aifail').textContent,plan:state.aiPlan})")
            ok("III.10 : réponse incomplète (tronquée) jamais affichée comme terminée ni enregistrée","tronquée" in t["msg"] and t["plan"] is None and len(MOCK["calls"])==1,(t["msg"],len(MOCK["calls"])))
            # ---------- coupure réseau pendant l'appel : arrêt immédiat ----------
            MOCK.update(delays=[9,9],calls=[],stop="end_turn")
            await prepare(page); await page.click("#ai_send"); await page.wait_for_timeout(300); await page.evaluate("window.dispatchEvent(new Event('offline'))")
            await page.wait_for_selector("#aisend .aifail",timeout=4000)
            c=await page.evaluate("()=>document.querySelector('#aisend .aifail').textContent")
            ok("III.10 : coupure réseau détectée avant le délai → arrêt tout de suite","Coupure réseau" in c and len(MOCK["calls"])==1,(c,len(MOCK["calls"])))
            await page.evaluate("window.dispatchEvent(new Event('online'))"); await page.wait_for_timeout(300)
            # ---------- doutes à confirmer mot par mot ----------
            MOCK.update(delays=[0.2],calls=[],stop="end_turn")
            await page.evaluate("""()=>{AI.pending=null;AI.busy=false;state.aiPlan=null;AI._planHash='';const e=document.getElementById('aisend');if(e)e.remove();Object.assign(state,{patient:'PETIT Louise',ddn:'28/06/2019',sexe:'f'});state.obs.dict='Un petit saignement du nez ce matin, pas de fièvre, pas de trouble de la coagulation connu.';aiAutoFlow('cabinet',{manual:true});}""")
            await page.wait_for_selector("#aisend",timeout=5000)
            d=await page.evaluate("()=>({dis:document.getElementById('ai_send').disabled,doubts:[...document.querySelectorAll('#aisend [data-dw]')].map(b=>b.dataset.dw),mark:document.querySelectorAll('#aisend .aidoubt').length})")
            ok("I.5 : homonyme du nom en minuscules (« petit » pour PETIT) surligné comme doute, envoi bloqué tant qu'il n'est pas confirmé","petit" in d["doubts"] and d["dis"] and d["mark"]>=1,d)
            await page.click("#aisend [data-dw]"); await page.wait_for_selector("#aiwchoice",timeout=2000); await page.click("#aiwchoice [data-wc=garder]"); await page.wait_for_timeout(400)
            d2=await page.evaluate("()=>({dis:document.getElementById('ai_send').disabled,doubts:document.querySelectorAll('#aisend [data-dw]').length,okw:AI.okw})")
            ok("I.5 : confirmation d'un toucher (« Garder ») → envoi possible",not d2["dis"] and d2["doubts"]==0 and "petit" in d2["okw"],d2)
            await page.evaluate("()=>{const w=[...document.querySelectorAll('#aisend .aiw')].find(x=>x.dataset.w==='petit');w.click();}"); await page.wait_for_selector("#aiwchoice",timeout=2000); await page.click("#aiwchoice [data-wc=tmasquer]"); await page.wait_for_timeout(400)
            d3=await page.evaluate("()=>({mask:AI.cfg.alwaysMask,text:document.getElementById('ai_sent').textContent})")
            ok("I.3 : « Toujours masquer » mémorisé et appliqué aussitôt","petit" in d3["mask"] and "petit saignement" not in d3["text"] and "[[MASQUÉ" in d3["text"],d3)
            n0=await page.evaluate("AI.pending.items.length"); await page.click("#ai_strict"); await page.wait_for_timeout(400)
            st=await page.evaluate("()=>({strict:AI.strict,n:AI.pending.items.length,btn:document.getElementById('ai_strict').textContent})")
            ok("I.5 : « Tout masquer davantage » (mode strict) actif, au moins autant d'éléments masqués",st["strict"] and st["n"]>=n0 and st["btn"]=="Masquage normal",(n0,st))
            await page.evaluate("()=>{AI.cfg.alwaysMask=[];aiSave();AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();}")
            # ---------- retour du réseau : demande en attente reproposée ----------
            await page.evaluate("""()=>{Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>false});AI._planHash='';state.aiPlan=null;Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});state.obs.dict='Toux depuis trois jours sans fièvre, auscultation normale.';aiAutoFlow('cabinet',{manual:true});}""")
            await page.wait_for_timeout(400)
            q=await page.evaluate("AIQ.list.length")
            await page.evaluate("()=>{Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>true});window.dispatchEvent(new Event('online'));}")
            await page.wait_for_selector("#netbar [data-aiqgo]",timeout=5000); sent0=len(MOCK["calls"]); await page.click("#netbar [data-aiqgo]"); await page.wait_for_selector("#aisend",timeout=5000)
            ok("III.12 : hors connexion la demande est gardée ; au retour du réseau elle est proposée dans le bandeau (« Voir ce qui part »), rien n'est envoyé ni ouvert tout seul, un toucher ouvre « Ce qui part »",q==1 and len(MOCK["calls"])==sent0,(q,len(MOCK["calls"])-sent0))
            await page.evaluate("()=>{AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();AIQ.list=[];aiqSave();}")
            # ---------- consommation ----------
            await page.evaluate("aiConsoScreen()"); await page.wait_for_selector("#aiconso",timeout=2000)
            cs=await page.evaluate("()=>document.getElementById('aiconso').textContent")
            ok("III.13 : écran Consommation — derniers envois avec modèle, anonymisation, réponse et coût","Derniers envois" in cs and "Haiku" in cs and " s" in cs and "Anonymisation sur l'appareil" in cs,cs[:200])
            ok("aucune erreur JS",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_ia_v41z.md"),"w",encoding="utf-8").write("# Tests IA v41z — modèles par étape, flux continu, bornes 40 + 20 s, arrêt, tronqué, coupure réseau, doutes, file d'attente, consommation\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
