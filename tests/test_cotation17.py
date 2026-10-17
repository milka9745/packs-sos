# Cotation (17/10/2026) : libellés de la convention SOS Médecins Orléans, à l'écran (Express, mode complet) et au journal.
# VG + MU (ou VG + MD, jamais les deux), G + CRN / VG + VRN, G + CRM / VG + VRM, CRD / VRD, MEG / MOP selon l'âge, ECG DEQP003 ; jamais U, MDN, MDI, MM ni F.
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:400])
PORT=8787
async def unlock(page,uid):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
C="""(a)=>{const [y,m,d,h,mi]=a.t;const ts=new Date(y,m-1,d,h,mi).getTime();return cotCompute({ts,lieu:a.lieu,ecg:!!a.ecg,km:a.km||"",age:a.age,extra:a.extra||[],minus:[]}).codes.map(x=>x.c);}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,lbl) in [(375,812,"iphone"),(1280,900,"ordinateur")]:
                mob=w<500
                ctx=await b.new_context(viewport={"width":w,"height":h},is_mobile=mob,has_touch=mob)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                await unlock(page,"cot"+lbl[:4]); L=lbl+" : "
                cases=[("visite en journée, adulte : VG + MU",{"t":[2026,10,14,15,0],"lieu":"visite","age":40},["VG","MU"]),
                       ("visite en journée + MD : VG + MD (MU retiré)",{"t":[2026,10,14,15,0],"lieu":"visite","age":40,"extra":["MD"]},["VG","MD"]),
                       ("ancienne ligne du journal « U » : affichée MU",{"t":[2026,10,14,15,0],"lieu":"cabinet","age":40,"extra":["U"]},["G","MU"]),
                       ("visite 21 h 30 : VG + VRN",{"t":[2026,10,14,21,30],"lieu":"visite","age":40},["VG","VRN"]),
                       ("consultation 21 h 30 : G + CRN",{"t":[2026,10,14,21,30],"lieu":"cabinet","age":40},["G","CRN"]),
                       ("visite 2 h : VG + VRM",{"t":[2026,10,15,2,0],"lieu":"visite","age":40},["VG","VRM"]),
                       ("consultation 2 h : G + CRM",{"t":[2026,10,15,2,0],"lieu":"cabinet","age":40},["G","CRM"]),
                       ("consultation dimanche 15 h : G + CRD",{"t":[2026,10,18,15,0],"lieu":"cabinet","age":40},["G","CRD"]),
                       ("visite enfant de 4 ans en journée : VG + MU + MEG",{"t":[2026,10,14,15,0],"lieu":"visite","age":4},["VG","MU","MEG"]),
                       ("consultation 85 ans : G + MOP",{"t":[2026,10,14,15,0],"lieu":"cabinet","age":85},["G","MOP"]),
                       ("ECG : DEQP003",{"t":[2026,10,14,15,0],"lieu":"cabinet","age":60,"ecg":1},["G","DEQP003"])]
                for name,a,exp in cases:
                    r=await page.evaluate(C,a); ok(L+name,r==exp,r)
                bad=await page.evaluate("Object.keys(TARIFS).filter(k=>['U','MDN','MDI','MM','F'].includes(k))")
                ok(L+"aucun code U, MDN, MDI, MM ni F dans les tarifs",not bad,bad)
                # écran (Express) et journal
                await page.evaluate("""()=>{newPatient();const i=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1985',sexe:'h'});state.cot.lieu='visite';state.cot.auto=false;state.cot.h='15:00';state.sel=i;render();}""")
                await page.wait_for_timeout(300)
                xp=await page.evaluate("(document.querySelector('.xp')||{}).innerText||''")
                ok(L+"écran Express : « VG + MU »","VG + MU" in xp and "VG + U " not in xp,[l for l in xp.split(chr(10)) if "Cotation" in l])
                await page.evaluate("journalUpsert(currentPack());state.view='journal';render();"); await page.wait_for_timeout(300)
                jt=await page.evaluate("[...document.querySelectorAll('.jcodes .chip')].map(x=>x.textContent).join(' | ')")
                ok(L+"journal : chip « MU », jamais « U »","MU" in jt and not any(c.strip().startswith("U ") for c in jt.split("|")),jt)
                ok(L+"aucune erreur JS",not errors,errors[:2])
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_cotation17.md"),"w",encoding="utf-8").write("# Tests cotation (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
