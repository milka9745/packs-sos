# Essai /test/ du 17/10/2026 : enfant de 9 mois, 8 kg, otite — CILOXADEX proposé à tort.
# OMA < 2 ans : amoxicilline 80 à 90 mg/kg/j en 2 prises, 10 jours (HAS 2016), dose en ml arrondie, maximum indiqué ; gouttes en option seulement.
# Otite externe : CILOXADEX à partir de 1 an (RCP 4.2, BDPM) — en dessous, ligne bloquée et motif affiché. Accords né / née, sexe manquant signalé.
# Express et mode complet, consultation et visite. Lancer : python tests/test_oma9m.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:500])
PORT=8805
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
SET="""(a)=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:a.ddn,poids:'8',sexe:a.sexe,date:'17/10/2026'});state.cot.lieu=a.lieu;state.cot.auto=false;state.view='';state.sel=PACKS.findIndex(p=>p.n===a.n);render();
  const p=currentPack();const L=[];p.s.forEach((sh,si)=>{resolve(sh,si).forEach(x=>L.push({k:sh.k,t:x.t.slice(0,60),on:x.on,s:x.fill.s,miss:x.fill.miss}));});
  const d=document.createElement('div');d.innerHTML=buildPages(p,true).out;return {L,printed:d.innerText,risk:riskMode()};}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,lbl) in [(375,812,"iphone"),(1280,900,"ordinateur")]:
                for xp in (True,False):
                    mob=w<500; L=f"{lbl} · {'Express' if xp else 'mode complet'} : "
                    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
                    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                    await unlock(page,"oma"+lbl[:3]+("x" if xp else "c"),xp)
                    DDN="17/01/2026"  # 9 mois le 17/10/2026
                    c=await page.evaluate("(d)=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:d,poids:'8',sexe:'f'});return xpCandidates('otite').ok.map(i=>PACKS[i].n);}",DDN)
                    ok(L+"OMA 9 mois 8 kg : « otite » propose l'OMA de l'enfant en tête, jamais l'otite externe adulte",c and c[0]=="Otite moyenne aiguë — enfant" and "Otite externe" not in c[:1],c[:4])
                    for lieu in ("cabinet","visite"):
                        r=await page.evaluate(SET,{"ddn":DDN,"sexe":"f","lieu":lieu,"n":"Otite moyenne aiguë — enfant"})
                        amox=[x for x in r["L"] if x["t"].startswith("CLAMOXYL")]
                        on=[x for x in r["L"] if x["on"] and x["k"]=="med"]
                        ok(L+f"OMA 9 mois 8 kg ({lieu}) : antibiotique d'emblée avant 2 ans (pack à risque)",r["risk"] and amox and amox[0]["on"],[x["t"] for x in on])
                        s=amox[0]["s"] if amox else ""
                        m=re.search(r"(\d+(?:,\d+)?) ml matin et soir",s)
                        ml=float(m.group(1).replace(",",".")) if m else 0
                        mgkgj=ml*100*2/8
                        ok(L+f"OMA 9 mois 8 kg ({lieu}) : amoxicilline {ml} ml × 2 = {mgkgj:.1f} mg/kg/j (80 à 90), 10 jours, maximum indiqué",80<=mgkgj<=90 and "pendant 10 jours" in s and "15 ml" in s,s)
                        cil=[x for x in r["L"] if "CILOXADEX" in x["t"]]
                        ok(L+f"OMA 9 mois ({lieu}) : gouttes CILOXADEX en option, non cochées",cil and not cil[0]["on"],cil)
                        ok(L+f"OMA 9 mois ({lieu}) : CILOXADEX absent des documents imprimés","CILOXADEX" not in r["printed"])
                        ok(L+f"OMA ({lieu}) : patiente « née le », jamais « né(e) »","née le" in r["printed"] and "né(e)" not in r["printed"],r["printed"][:200])
                    # dose : 80 à 90 mg/kg/j de 5 à 35 kg, jamais plus de 3 g/j
                    d=await page.evaluate("()=>{const R=[];for(let k=5;k<=40;k++){state.poids=String(k);const p=currentPack();const si=p.s.findIndex(s=>s.k==='med');const x=resolve(p.s[si],si).find(y=>y.t.startsWith('CLAMOXYL'));const m=/(\\d+(?:,\\d+)?) ml matin/.exec(x.fill.s);const ml=m?parseFloat(m[1].replace(',','.')):0;R.push([k,ml,Math.round(ml*200/k*10)/10,ml*200]);}state.poids='8';return R;}")
                    bad=[x for x in d if not ((80<=x[2]<=90) or x[3]==3000) or x[3]>3000]
                    ok(L+"amoxicilline de 5 à 40 kg : 80 à 90 mg/kg/j, 3 g par jour au maximum",not bad,bad[:5])
                    # otite externe à 9 mois : CILOXADEX bloqué (RCP : à partir de 1 an), motif affiché
                    r=await page.evaluate(SET,{"ddn":DDN,"sexe":"f","lieu":"cabinet","n":"Otite externe"})
                    cil=[x for x in r["L"] if "CILOXADEX" in x["t"]]
                    ok(L+"otite externe à 9 mois : CILOXADEX bloqué (âge minimal 1 an, RCP), jamais imprimé",cil and any("1 an" in z and "CILOXADEX" in z for z in cil[0]["miss"]) and "CILOXADEX" not in r["printed"],cil)
                    lg=await page.evaluate("ciLegal(currentPack())")
                    ok(L+"otite externe à 9 mois : alerte « âge ≥ 1 an pour CILOXADEX » à l'écran avant impression",any("1 an" in z and "CILOXADEX" in z for z in lg),lg)
                    r2=await page.evaluate(SET,{"ddn":"17/01/2020","sexe":"h","lieu":"cabinet","n":"Otite externe"})
                    cil=[x for x in r2["L"] if "CILOXADEX" in x["t"]]
                    ok(L+"otite externe à 6 ans : CILOXADEX proposé normalement, « né le »",cil and cil[0]["on"] and not cil[0]["miss"] and "CILOXADEX" in r2["printed"] and "né le" in r2["printed"],cil)
                    # sexe manquant : signalé à l'écran
                    await page.evaluate(SET,{"ddn":DDN,"sexe":"","lieu":"cabinet","n":"Otite moyenne aiguë — enfant"}); await page.wait_for_timeout(200)
                    ok(L+"sexe non renseigné : signalé à l'écran (« né(e) »)",await page.locator(".sexmiss").count()>=1 and await page.locator(".sexmiss").first.is_visible())
                    if mob and xp:
                        await page.evaluate("document.querySelector('.sexmiss').scrollIntoView({block:'center'})"); await page.wait_for_timeout(200)
                        await page.screenshot(path=os.path.join(OUT,"oma-9mois-8kg-express.png"))
                    ok(L+"aucune erreur JS",not errors,errors[:2])
                    await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_oma9m.md"),"w",encoding="utf-8").write("# Tests OMA 9 mois 8 kg (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
