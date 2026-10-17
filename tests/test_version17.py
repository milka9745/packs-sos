# Numéro de livraison (17/10/2026) : visible en haut du mode complet et du mode Express (iPhone et ordinateur), menu ⋯ « version · branche · date »,
# jamais sur un document imprimé, un PDF ou le compte rendu. Lancer : python tests/test_version17.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:400])
PORT=8801
V=json.load(open(os.path.join(ROOT,"version.json"),encoding="utf-8"))["version"]
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,lbl) in [(375,812,"iphone"),(1280,900,"ordinateur")]:
                for xp in (True,False):
                    mob=w<500; mode="Express" if xp else "mode complet"; L=f"{lbl} · {mode} : "
                    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
                    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                    await unlock(page,"ver"+lbl[:3]+("x" if xp else "c"),xp)
                    await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1975',sexe:'h',date:'17/10/2026'});state.sel=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');render();}")
                    await page.wait_for_timeout(300)
                    av=await page.evaluate("(()=>{const e=[...document.querySelectorAll('.appver')].find(x=>x.offsetParent);if(!e)return null;const r=e.getBoundingClientRect();return {t:e.textContent,top:r.top,fs:parseFloat(getComputedStyle(e).fontSize)};})()")
                    ok(L+f"numéro de livraison « v{V} » en haut, petit et discret",av and ("v"+V) in av["t"] and av["top"]<140 and av["fs"]<=12,av)
                    if mob:
                        await page.click("#more_btn"); await page.wait_for_timeout(300)
                        jm=await page.evaluate("(document.querySelector('#jmenu .jm-ver')||{}).textContent||''")
                        ok(L+"menu ⋯ : « version · branche · date »",re.match(r"^v"+V+r" · main · \d\d/\d\d \d\d:\d\d$",jm) is not None,jm)
                        await page.click("#more_btn"); await page.wait_for_timeout(200)
                    else:
                        t=await page.evaluate("(document.querySelector('.jbar .appver')||{}).textContent||''")
                        ok(L+"barre du haut (ordinateur) : « version · branche · date »",re.match(r"^v"+V+r" · main · \d\d/\d\d \d\d:\d\d$",t) is not None,t)
                    cr=await page.evaluate("buildCR(currentPack())")
                    pages=await page.evaluate("buildPages(currentPack(),true).out")
                    ok(L+"jamais dans le compte rendu ni les documents imprimés",("v"+V) not in cr and "appver" not in pages and ("v"+V) not in pages and "jm-ver" not in pages)
                    await page.emulate_media(media="print"); d=await page.evaluate("[...document.querySelectorAll('.appver,.jm-ver')].map(e=>getComputedStyle(e).display)"); await page.emulate_media(media="screen")
                    ok(L+"masqué à l'impression",d and all(x=="none" for x in d),d)
                    ok(L+"aucune erreur JS",not errors,errors[:2])
                    await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK"); sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
