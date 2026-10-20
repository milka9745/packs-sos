# Vérifications avant publication v41 (16/10/2026) : IA « Aucun » par défaut, aucun envoi réseau sans clé, écran « Ce qui part » obligatoire.
# Toutes les requêtes du navigateur sont enregistrées ; l'API Anthropic est simulée (aucun appel réel). Lancer : python tests/test_prepub.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page,first=True):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
    await page.goto("http://localhost:8769/index.html")
    if first:
        await page.wait_for_selector("#uid",timeout=15000)
        await page.fill("#uid","testv41"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
        await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
        await page.check("#rec_ack"); await page.click("#rec_done")
        try:
            await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
        except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(1000)

async def exercise(page):
    """Parcours complet d'une consultation fictive, sans jamais toucher « Envoyer »."""
    await page.evaluate("""()=>{const i=PACKS.findIndex(p=>/Cystite simple/.test(p.n));state.sel=i;state.patient='DUPONT Marie';state.ddn='12/03/1985';state.t0=Date.now();state.obsOpen=true;state.obs.dict='Mme Dupont brûlures mictionnelles depuis le 13/10.';render();}""")
    if await page.locator("#dict_go").count(): await page.click("#dict_go"); await page.wait_for_timeout(300)
    if await page.locator("#cr_copy").count(): await page.click("#cr_copy"); await page.wait_for_timeout(300)
    await page.evaluate("try{aiOpen('obs')}catch(e){}"); await page.wait_for_timeout(200)
    await page.evaluate("try{aiPrepare('obs',{dictee:'Mme Dupont, toux.'})}catch(e){}"); await page.wait_for_timeout(200)
    await page.evaluate("document.querySelectorAll('#aipanel,#aisend').forEach(e=>e.remove())")

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8769"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    html=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
    ok("code : un seul point d'appel à l'API (aiCall)",html.count("https://api.anthropic.com/v1/messages")==1)
    ok("code : verrou « Ce qui part » dans aiCall",'if(f!=="test"){if(AI._go!==true)throw' in html)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for width,label in [(375,"iphone"),(1280,"pc")]:
                ctx=await b.new_context(viewport={"width":width,"height":850},is_mobile=width<500,has_touch=width<500)
                page=await ctx.new_page(); L=label+" "
                errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
                reqs=[]; page.on("request",lambda r:reqs.append(r.url))
                api=[]
                async def handle(route):
                    req=route.request; cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
                    if req.method=="OPTIONS": await route.fulfill(status=204,headers=cors); return
                    api.append(req.post_data or "")
                    await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps({"model":"claude-sonnet-5-5","stop_reason":"end_turn","content":[{"type":"text","text":"{}"}],"usage":{"input_tokens":10,"output_tokens":5}}))
                await ctx.route("https://api.anthropic.com/**",handle)
                anth=lambda:[u for u in reqs if "anthropic.com" in u]
                # 1. Profil neuf, sans clé
                await unlock(page)
                ok(L+"profil neuf : IA « Aucun » par défaut",await page.evaluate("AI.cfg.mode")=="aucun" and await page.evaluate("aiEffective().mode")=="aucun")
                ok(L+"profil neuf : bouton IA affiché « Aucun »","Aucun" in await page.evaluate("aiBtnHTML()"))
                await exercise(page)
                ok(L+"sans clé : consultation complète sans aucune requête vers l'IA",not anth() and not api,anth())
                ok(L+"sans clé : aucune préparation d'envoi",await page.evaluate("AI.pending===null"))
                # 2. Clé saisie dans les réglages : l'IA reste sur « Aucun »
                await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(500)
                await page.fill("#ai_key","sk-ant-test-factice-prepub"); await page.click("#ai_savekey"); await page.wait_for_timeout(500)
                ok(L+"clé enregistrée : l'IA reste sur « Aucun »",await page.evaluate("AI.cfg.mode")=="aucun" and await page.evaluate("aiEffective().mode")=="aucun")
                ok(L+"clé enregistrée : message « choisissez Partiel ou Complet »","choisissez Partiel ou Complet" in await page.inner_text("#ai_setst"))
                await page.evaluate("state.view='';render();"); await page.wait_for_timeout(300)
                await exercise(page)
                ok(L+"clé enregistrée, mode Aucun : aucune requête vers l'IA",not anth() and not api,anth())
                # 3. Clé héritée de la v40 (ancien format, sans niveau) après rechargement
                await page.evaluate("secSet('sos_ai',{key:'sk-ant-ancienne-v40',model:'claude-haiku-4-5'})"); await page.wait_for_timeout(600)
                await unlock(page,first=False)
                ok(L+"clé héritée de la v40 : toujours « Aucun » après rechargement",await page.evaluate("AI.key")=="sk-ant-ancienne-v40" and await page.evaluate("AI.cfg.mode")=="aucun")
                await exercise(page)
                ok(L+"clé héritée : aucune requête vers l'IA",not anth() and not api,anth())
                # 4. Partiel choisi : rien ne part sans « Ce qui part »
                await page.evaluate("AI.cfg.mode='partiel';aiSave();render();"); await page.wait_for_timeout(300)
                err=await page.evaluate("aiCall('obs','claude-sonnet-5-5','x','Mme Dupont',10,0).then(()=>'parti').catch(e=>e.message)")
                ok(L+"appel direct sans l'écran : refusé",("Ce qui part" in err) and not anth(),err)
                await page.evaluate("aiPrepare('obs',{dictee:'Mme Dupont, toux depuis le 12/10/2026.'})"); await page.wait_for_timeout(300)
                ok(L+"Partiel : l'écran « Ce qui part » s'ouvre, rien n'est parti",await page.locator("#aisend").count()==1 and not anth())
                await page.click("#ai_cancel"); await page.wait_for_timeout(200)
                ok(L+"Annuler : rien n'est parti",not anth() and await page.evaluate("AI.pending===null"))
                # 5. Complet : préparation automatique, jamais d'envoi automatique
                await page.evaluate("AI.cfg.mode='complet';aiSave();state.obs.dict='Douleur lombaire depuis hier';state.obsOpen=true;state.aiCrAuto=false;render();"); await page.wait_for_timeout(300)
                await page.click("#dict_go"); await page.wait_for_timeout(600)
                ok(L+"Complet : « Ce qui part » ouvert automatiquement, rien n'est parti (envoi automatique désactivé tant que DPO / HDS à confirmer)",await page.locator("#aisend").count()==1 and not anth())
                await page.click("#ai_send"); await page.wait_for_timeout(800)
                ok(L+"Complet : un seul envoi, seulement après « Envoyer »",len(api)==1 and "Dupont" not in api[0])
                ok(L+"après l'envoi, le verrou est refermé",await page.evaluate("AI._go")==False)
                # 6. Hors connexion : passage en « Aucun »
                await ctx.set_offline(True); await page.wait_for_timeout(200)
                ok(L+"hors connexion : IA en « Aucun »",await page.evaluate("aiEffective().mode")=="aucun")
                await ctx.set_offline(False)
                ok(L+"aucune erreur JS",not errors,errors[:3])
                await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_prepub.md"),"w",encoding="utf-8").write("# Vérifications avant publication v41\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
