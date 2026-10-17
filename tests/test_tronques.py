# Boutons jamais tronqués à 375 px (17/10/2026 : « Envoyer à l'imprimante » coupé en « l'ir »). Express et mode complet, texte normal et grand texte :
# accueil, patient, fiche, aperçu. Lancer : python tests/test_tronques.py
import asyncio,sys,os,subprocess,time,json
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
src=open("tests/test_essai17.py",encoding="utf-8").read().split("async def run")[0]
ns={"__file__":os.path.abspath("tests/test_essai17.py")};exec(src.replace("PORT=8798","PORT=8803").replace("8799","8804"),ns)
CLIP="""()=>[...document.querySelectorAll('button,a.btn,label.btn,summary')].filter(e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height||!e.offsetParent)return false;const cs=getComputedStyle(e);return (e.scrollWidth>e.clientWidth+2&&cs.overflowX!=='visible')||(e.scrollWidth>e.clientWidth+2)||r.right>innerWidth+1||r.left<-1;}).map(e=>({t:e.textContent.trim().replace(/\s+/g,' ').slice(0,50),sw:e.scrollWidth,cw:e.clientWidth,l:Math.round(e.getBoundingClientRect().left),r:Math.round(e.getBoundingClientRect().right),cls:e.className.slice(0,30)}))"""
async def go():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8803"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for big in (False,True):
              for xp in (True,False):
                ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page()
                await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_bigtext','{1 if big else 0}')}}catch(e){{}}")
                await ns["unlock"](page,"clip"+str(big)+str(xp))
                await page.evaluate("themeApply()")
                out={}
                await page.evaluate(ns["STOPS"]);await page.wait_for_timeout(300);out["accueil"]=await page.evaluate(CLIP)
                await page.evaluate("xpOpenStop?xpOpenStop('v2'):tourUse('v2')");await page.wait_for_timeout(300);out["patient"]=await page.evaluate(CLIP)
                await page.evaluate("()=>{state.poids='8';state.ddn='01/01/2026';state.sel=PACKS.findIndex(p=>p.n==='Otite moyenne aiguë — enfant');state.obs.dict='Fièvre. Tympan droit bombé. Reste de l examen normal.';applyDictation();render();const d=document.getElementById('xp_plus');if(d)d.open=true;}");await page.wait_for_timeout(300);out["fiche"]=await page.evaluate(CLIP)
                await page.evaluate("printPack()");await page.wait_for_timeout(1200)
                if await page.locator("#ciover").count(): out["alerte"]=await page.evaluate(CLIP)
                else: out["apercu"]=await page.evaluate(CLIP)
                lbl=("grand texte" if big else "texte normal")+" · "+("Express" if xp else "mode complet")
                for k,v in out.items(): ok(f"375 px {lbl} · {k} : aucun bouton tronqué ni hors de l'écran",not v,v[:4])
                await ctx.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK"); sys.exit(0 if n==len(results) else 1)
asyncio.run(go())
