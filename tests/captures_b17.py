# Captures du rapport de la partie B (17/10/2026) : ordonnance avec cachet fictif (B1), document long réduit (B1),
# renouvellement maintenu (B2). Patients et cachet fictifs. Lancer : python tests/captures_b17.py
import asyncio, os, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); PORT=8781
sys.path.insert(0,os.path.join(ROOT,"tests"))
IDFAKE=open(os.path.join(ROOT,"tests","test_securite17.py"),encoding="utf-8").read().split('IDFAKE="""')[1].split('"""')[0]

async def unlock(page):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","captb17"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1280,"height":1000})
            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
            page=await ctx.new_page(); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page); await page.evaluate(IDFAKE)
            await page.evaluate("""()=>{const i=PACKS.findIndex(p=>p.n==='Renouvellement de traitement chronique');Object.assign(state,{sel:i,obs:{},lo:{},off:{},extra:{},libre:{},patient:'MARTIN Jeanne',ddn:'05/06/1975',sexe:'f',date:'17/10/2026'});
              const si=PACKS[i].s.findIndex(s=>s.k==='med');state.extra[si]=['ESCITALOPRAM 10 mg comprimé : 1 comprimé par jour, 3 mois.','HALOPÉRIDOL 1 mg comprimé : 1 comprimé par jour, 3 mois.'];render();}""")
            await page.evaluate("printPack()"); await page.wait_for_timeout(600)
            await page.click("#ci_keep"); await page.wait_for_timeout(200)
            await page.locator("[data-cichip]").first.click(); await page.wait_for_timeout(200)
            await page.locator("#ciover .aibox, #ciover > div").first.screenshot(path=os.path.join(OUT,"b17-b2-maintien.png"))
            await page.click("#ci_print"); await page.wait_for_selector("#print .page",timeout=8000); await page.wait_for_timeout(800)
            await page.add_style_tag(content="#print .printbar,#print .alert{display:none!important}"); await page.wait_for_timeout(200); pg=page.locator("#print .page").first; await pg.scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(OUT,"b17-b1-ordonnance-cachet.png"))
            await b.close()
    finally: srv.terminate()
    print("ok")
asyncio.run(main())
