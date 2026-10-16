# Registre du 16/10/2026, lot 3 : n° 6 (hors connexion) et n° 11 (clé API Claude chiffrée dans profil.json, retrouvée avec la phrase maître).
# API Anthropic simulée (aucun appel réel), patient et clé fictifs. 375 px jour, nuit, grand texte, et ordinateur. Lancer : python tests/test_lot3.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8778
KEY="sk-ant-test-lot3-cle-factice-A1B2"
KEY2="sk-ant-test-lot3-nouvelle-cle-Z9Y8"
PHRASE="girafe crayon lune cabane fraise galet"

def api_reply(obj):
    return {"id":"msg_test","type":"message","role":"assistant","model":"claude-sonnet-5-5","stop_reason":"end_turn",
            "content":[{"type":"text","text":json.dumps(obj,ensure_ascii=False)}],"usage":{"input_tokens":900,"output_tokens":200,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}

async def unlock(page,uid="testlot3"):
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(700)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

async def newctx(b,w,h):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},is_mobile=mob,has_touch=mob,device_scale_factor=2 if mob else 1)
    sent=[]
    async def handle(route):
        req=route.request;url=req.url
        cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
        if "api.anthropic.com" in url:
            if req.method=="OPTIONS": await route.fulfill(status=204,headers=cors); return
            sent.append(req.post_data or "")
            await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps(api_reply({"obs":{},"packs":[]}),ensure_ascii=False)); return
        if "localhost" in url: await route.continue_(); return
        await route.abort()
    await ctx.route("**/*",handle)
    return ctx,sent

SETUP="""()=>{newPatient();state.patient='LEBRUN Odile';state.ddn='02/02/1950';state.sexe='f';state.t0=Date.now();AI.key='%s';AI.cfg.mode='partiel';aiSave();render();}"""%KEY

async def lot6(b,w,h,th,big,label):
    ctx,sent=await newctx(b,w,h); page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page)
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
    await page.evaluate(SETUP); await page.wait_for_timeout(300)
    L=label+" : "
    await ctx.set_offline(True); await page.wait_for_timeout(300)
    bar=await page.evaluate("(()=>{const e=document.getElementById('netbar');return e?e.innerText:''})()")
    ok(L+"n°6 hors connexion signalé à l'écran, « rien n'est perdu »","Hors connexion" in bar and "rien n'est perdu" in bar,bar[:120])
    await page.click("#nb_tog"); await page.wait_for_timeout(150)
    bar=await page.evaluate("document.getElementById('netbar').innerText")
    ok(L+"n°6 ce qui fonctionne sans réseau et ce qui attend le réseau, affichés","Fonctionne sans réseau" in bar and "Attend le réseau" in bar and "Assistant IA" in bar and "Synchronisation" in bar,bar[:200])
    sw=await page.evaluate("[document.documentElement.scrollWidth,document.documentElement.clientWidth]")
    ok(L+"n°6 bandeau sans débordement horizontal",sw[0]<=sw[1],sw)
    if w<500: await page.screenshot(path=os.path.join(OUT,f"lot3-horsligne-{label.replace(' ','-')}.png"))
    await page.click("#nb_tog"); await page.wait_for_timeout(100)
    # dictée hors connexion : enregistrée chiffrée à chaque frappe
    await page.evaluate("state.obs.dict='Mme Lebrun, toux depuis 3 jours, fièvre 38,5, crépitants base droite.';draftSaveNow&&draftSaveNow();")
    await page.wait_for_timeout(400)
    dr=await page.evaluate("secGet('sos_draft',null).then(d=>JSON.stringify(d||{}))")
    ok(L+"n°6 dictée hors connexion enregistrée chiffrée sur l'appareil","crépitants" in dr and "crépitants" not in await page.evaluate("JSON.stringify(localStorage)"),dr[:80])
    # demande IA hors connexion : préparée, anonymisée, mise en attente ; rien ne part
    n0=len(sent)
    r=await page.evaluate("aiPrepare('obs',{dictee:state.obs.dict})")
    q=await page.evaluate("AIQ.list.map(x=>({u:x.P.user,k:x.P.kind}))")
    ok(L+"n°6 demande IA mise en attente, rien n'est parti",r is None and len(q)==1 and len(sent)==n0,q)
    ok(L+"n°6 demande en attente déjà anonymisée (nom retiré)",q and "Lebrun" not in q[0]["u"] and "LEBRUN" not in q[0]["u"],q[0]["u"][:160] if q else "")
    ls=await page.evaluate("JSON.stringify(localStorage)")
    await page.wait_for_timeout(300); ls=await page.evaluate("JSON.stringify(localStorage)")
    ok(L+"n°6 file d'attente rangée chiffrée (aucun texte en clair)","sos_aiq_enc" in ls and "crépitants" not in ls,[k for k in json.loads(ls) if "crépitants" in json.loads(ls)[k]]+["aiq" if "sos_aiq_enc" in ls else "noaiq"])
    # retour du réseau : aucun envoi automatique, proposition « Ce qui part »
    await ctx.set_offline(False); await page.wait_for_timeout(1200)
    bar=await page.evaluate("(()=>{const e=document.getElementById('netbar');return e?e.innerText:''})()")
    ok(L+"n°6 réseau revenu : rien n'est envoyé tout seul",len(sent)==n0,len(sent)-n0)
    ok(L+"n°6 réseau revenu : demande proposée (« Voir ce qui part »)","Réseau revenu" in bar and await page.locator("[data-aiqgo]").count()==1,bar[:120])
    if w<500: await page.screenshot(path=os.path.join(OUT,f"lot3-reseau-revenu-{label.replace(' ','-')}.png"))
    await page.click("[data-aiqgo]"); await page.wait_for_timeout(300)
    ok(L+"n°6 l'écran « Ce qui part » s'ouvre, envoi au choix du médecin",await page.locator("#aisend #ai_send:not([disabled])").count()==1 and len(sent)==n0)
    await page.click("#aisend #ai_send"); await page.wait_for_timeout(800)
    ok(L+"n°6 après « Envoyer » : un seul envoi, file vidée, bandeau retiré",len(sent)==n0+1 and await page.evaluate("AIQ.list.length")==0 and await page.locator("#netbar").count()==0,[len(sent)-n0])
    await page.evaluate("const e=document.getElementById('aipanel');if(e)e.remove();")
    # autre consultation : ne s'applique plus ici
    await ctx.set_offline(True); await page.wait_for_timeout(200)
    await page.evaluate("aiPrepare('obs',{dictee:'toux sèche'});")
    await page.evaluate("newPatient();state.patient='ROUX Paul';state.t0=Date.now()+5;render();")
    await ctx.set_offline(False); await page.wait_for_timeout(500)
    bar=await page.evaluate("(()=>{const e=document.getElementById('netbar');return e?e.innerText:''})()")
    ok(L+"n°6 demande d'une autre consultation : signalée, jamais appliquée au patient suivant","autre consultation" in bar and await page.locator("[data-aiqgo]").count()==0,bar[:160])
    await page.click("[data-aiqdel]"); await page.wait_for_timeout(300)
    ok(L+"n°6 demande retirée d'un geste",await page.evaluate("AIQ.list.length")==0)
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def lot11(b):
    # appareil 1 : clé enregistrée, profil créé (signature fictive), profil publié avec la clé
    ctx,sent=await newctx(b,375,812); page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
    msgs=[]
    async def dlg(d):
        msgs.append(d.message)
        if d.type=="prompt": await d.accept(PHRASE)
        else: await d.accept()
    page.on("dialog",lambda d:asyncio.ensure_future(dlg(d)))
    await unlock(page,"testkit1")
    L="n°11 : "
    kit=await page.evaluate("""async()=>{AI.key='%s';aiSave();const stamp='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
      const kit=await kitEncrypt({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp},'%s');return JSON.stringify(kit);}"""%(KEY,PHRASE))
    ok(L+"profil.json : clé API absente en clair (chiffrée avec la phrase maître)",KEY not in kit and "sk-ant" not in kit and '"ct"' in kit)
    dec=await page.evaluate("async(k)=>{const id=await kitDecrypt(k,'%s');return id.ai&&id.ai.key;}"%PHRASE,kit)
    ok(L+"profil.json déchiffré par la phrase : clé API retrouvée",dec==KEY,dec)
    bad=await page.evaluate("async(k)=>{try{await kitDecrypt(k,'mauvaise phrase de test');return 'ouvert';}catch(e){return e.message;}}",kit)
    ok(L+"mauvaise phrase : rien n'est déchiffré",bad!="ouvert" and "incorrecte" in bad,bad)
    # réglages : jamais en clair, remplaçable d'un geste
    await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(300)
    html=await page.evaluate("document.documentElement.outerHTML")
    ok(L+"réglages : clé jamais affichée ni présente dans la page",KEY not in html and await page.locator("#ai_key").input_value()=="")
    tail=await page.evaluate("document.getElementById('ai_setst').textContent")
    ok(L+"réglages : clé reconnaissable sans être lisible (4 derniers caractères)","…A1B2" in tail,tail)
    await page.fill("#ai_key",KEY2); await page.click("#ai_savekey"); await page.wait_for_timeout(400)
    k2=await page.evaluate("secGet('sos_ai',null).then(c=>c&&c.key)")
    ok(L+"clé remplacée d'un geste (coller, « Remplacer »), rangée chiffrée",k2==KEY2 and KEY2 not in await page.evaluate("JSON.stringify(localStorage)"),k2)
    txt=await page.evaluate("document.body.innerText")
    ok(L+"avertissement : la sécurité dépend de la solidité de la phrase maître","solidité de la phrase" in txt)
    ok(L+"avertissement repris à la publication du profil","solidité de la phrase maître" in await page.evaluate("AI_KIT_WARN"))
    kit2=await page.evaluate("async()=>JSON.stringify(await kitEncrypt({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='},'%s'))"%PHRASE)
    await ctx.close()
    # appareil 2 : neuf, sans clé ; la phrase maître suffit
    ctx,sent=await newctx(b,1280,860); page=await ctx.new_page(); page.on("pageerror",lambda e:errors.append(str(e)))
    await unlock(page,"testkit2")
    ok(L+"appareil neuf : aucune clé avant activation",await page.evaluate("AI.key")=="")
    r=await page.evaluate("async(k)=>{const id=await identActivate(k,'%s');return {ok:id.aiOk,key:AI.key,mode:AI.cfg.mode,stored:await secGet('sos_ai',null).then(c=>c&&c.key),ident:JSON.stringify(await secGet('sos_ident',null))};}"%PHRASE,kit2)
    ok(L+"autre appareil : clé disponible après la phrase maître, rangée chiffrée",r["ok"] and r["key"]==KEY2 and r["stored"]==KEY2,{k:str(r[k])[-6:] for k in ("ok","mode","key","stored")})
    ok(L+"autre appareil : IA laissée sur « Aucun » (rien ne part sans choix du médecin)",r["mode"]=="aucun")
    ok(L+"clé non dupliquée dans l'identité enregistrée",KEY2 not in r["ident"])
    n0=len(sent); await page.wait_for_timeout(500)
    ok(L+"activation : aucun appel à l'API",len(sent)==n0==0)
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,th,big,lbl) in [(375,812,"day",False,"iphone jour"),(375,812,"night",False,"iphone nuit"),(375,812,"night",True,"iphone grand texte"),(1280,860,"day",False,"ordinateur")]:
                await lot6(b,w,h,th,big,lbl)
            await lot11(b)
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_lot3.md"),"w",encoding="utf-8").write("# Tests lot 3 du registre du 16/10/2026 (n° 6 et 11)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
