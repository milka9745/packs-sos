# Incident en garde du 18/10/2026 : ZITHROMAX angine, enfant de 40 kg — ordonnance juste (12,5 ml = 500 mg/j) mais confusion avec la pipette
# dose-poids graduée jusqu'à 25 kg. Règle : dans l'étendue de la pipette « 1 dose-poids X kg (soit Y ml, Z mg) » ; au-delà, jamais « dose-poids »,
# « Y ml, soit Z mg (dose maximale) » et alerte ; toujours ml et mg (ordonnance et conseils) ; comprimé en option 1 au-dessus du seuil (RCP : 45 kg).
# Express et mode complet, iPhone et ordinateur. Lancer : python tests/test_dosepoids.py
import asyncio, os, json, subprocess, time, sys, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
PORT=8806
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
RUN="""(a)=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:a.ddn||'01/01/2016',poids:String(a.w),sexe:'f',date:'18/10/2026'});if(a.lieu)state.cot.lieu=a.lieu;state.view='';state.sel=PACKS.findIndex(p=>p.n===a.n);
  const p=currentPack();if(a.pick){p.s.forEach((sh,si)=>{const r=resolve(sh,si);const x=r.find(y=>y.t.startsWith(a.pick));if(x&&x.grp)state.gs[si+':'+x.grp]=x.key;else if(x)state.lo[x.key]=true;});}
  render();const P=currentPack();const L=[];P.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>L.push({t:x.t.slice(0,40),on:x.on,s:x.fill.s,miss:x.fill.miss}));});
  const d=document.createElement('div');d.innerHTML=buildPages(P,true).out;const pages=[...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}));
  const adv=[...document.querySelectorAll('#main .adv, #main .xp-alerts')].map(x=>x.innerText).join(' | ');return {L,pages,adv};}"""
SWEEP="""()=>{const bad=[],nomg=[];for(const w of [8,15,25,32,45]){for(let i=0;i<PACKS.length;i++){if(!PACKS[i].s.some(sh=>sh.k==='med'))continue;newPatient();Object.assign(state,{patient:'X',ddn:'01/01/2016',poids:String(w),sexe:'f'});state.sel=i;const p=currentPack();
  p.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>{if(!x.on)return;const t=x.fill.s;const m=/dose-poids (\\d+(?:,\\d+)?) kg/.exec(t);if(m&&parseFloat(m[1].replace(',','.'))>25)bad.push([PACKS[i].n,w,t.slice(0,80)]);
    if(/\{ml:|\{dp:/.test(x.t)&&/(suspension|sirop)/i.test(t)&&/\\d ml/.test(t)&&!/\\d mg\\b/.test(t.split(' : ').slice(1).join(' : ')))nomg.push([PACKS[i].n,w,t.slice(0,90)]);});});}}return {bad,nomg:nomg.slice(0,12),n:nomg.length};}"""
def line(r,start):
    x=[y for y in r["L"] if y["t"].startswith(start) and y["on"]]
    return x[0]["s"] if x else ""
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
                    await unlock(page,"dp"+lbl[:3]+("x" if xp else "c"),xp)
                    A="Angine — enfant (TROD positif)"; Z="ZITHROMAX 40 mg/ml"
                    r=await page.evaluate(RUN,{"n":A,"w":15,"pick":Z}); s=line(r,Z)
                    ok(L+"ZITHROMAX 15 kg : « 1 dose-poids 15 kg (soit 7,5 ml, 300 mg) »","1 dose-poids 15 kg (soit 7,5 ml, 300 mg)" in s,s)
                    r=await page.evaluate(RUN,{"n":A,"w":25,"pick":Z}); s=line(r,Z)
                    ok(L+"ZITHROMAX 25 kg : « 1 dose-poids 25 kg (soit 12,5 ml, 500 mg) »","1 dose-poids 25 kg (soit 12,5 ml, 500 mg)" in s,s)
                    r=await page.evaluate(RUN,{"n":A,"w":40,"pick":Z}); s=line(r,Z)
                    ok(L+"ZITHROMAX 40 kg : jamais « dose-poids », « 12,5 ml, soit 500 mg (dose maximale) »","dose-poids" not in s and "12,5 ml, soit 500 mg (dose maximale)" in s,s)
                    ok(L+"ZITHROMAX 40 kg : alerte à l'écran (au-delà de la pipette de 25 kg)","au-delà de la pipette" in r["adv"] and "25 kg" in r["adv"],r["adv"][:300])
                    ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"));cons=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Consignes"))
                    ok(L+"ZITHROMAX 40 kg : ml et mg sur l'ordonnance et dans les conseils patient","12,5 ml, soit 500 mg" in ordo and "12,5 ml" in cons and "500 mg" in cons and "dose-poids" not in ordo+cons,[ordo[:200],cons[:200]])
                    r=await page.evaluate(RUN,{"n":A,"w":40})
                    ok(L+"angine 40 kg : comprimé ZITHROMAX non proposé sous 45 kg (RCP)",not [y for y in r["L"] if y["t"].startswith("ZITHROMAX 250 mg")],[y["t"] for y in r["L"]])
                    r=await page.evaluate(RUN,{"n":A,"w":50,"ddn":"01/01/2012"})
                    names=[y["t"] for y in r["L"]]
                    zc=[i for i,t in enumerate(names) if t.startswith("ZITHROMAX 250 mg")];zs=[i for i,t in enumerate(names) if t.startswith("ZITHROMAX 40 mg/ml")]
                    ok(L+"angine 50 kg : ZITHROMAX 250 mg comprimé en option 1, suspension en option 2",zc and zs and zc[0]<zs[0],names)
                    r=await page.evaluate(RUN,{"n":"Fièvre — enfant","w":10,"ddn":"01/01/2025"}); s=line(r,"DOLIPRANE")
                    ok(L+"DOLIPRANE 10 kg : « 1 dose-poids 10 kg (soit 6,25 ml, 150 mg) »","1 dose-poids 10 kg (soit 6,25 ml, 150 mg)" in s,s)
                    r=await page.evaluate(RUN,{"n":"Fièvre — enfant","w":17,"ddn":"01/01/2022"}); s=line(r,"DOLIPRANE")
                    ok(L+"DOLIPRANE 17 kg (au-dessus de la pipette de 13 kg) : jamais « dose-poids », forme adaptée au poids","dose-poids" not in s and "mg" in s,s)
                    dd=await page.evaluate("dpDose(DP.DOLI24,20,4)")
                    ok(L+"DOLIPRANE suspension à 20 kg : « 12,5 ml, soit 300 mg », pas de dose-poids",dd["txt"]=="12,5 ml, soit 300 mg" and dd["beyond"],dd)
                    r=await page.evaluate(RUN,{"n":"Otite moyenne aiguë — enfant","w":40,"ddn":"01/01/2015","lieu":"visite"}); s=line(r,"CLAMOXYL")
                    ok(L+"CLAMOXYL OMA 40 kg (cuillère-mesure, pas de pipette) : « 15 ml (soit 1500 mg) », jamais « dose-poids »","15 ml (soit 1500 mg)" in s and "dose-poids" not in s,s)
                    r=await page.evaluate(RUN,{"n":A,"w":45,"ddn":"01/01/2013"}); s=line(r,"CLAMOXYL")
                    ok(L+"CLAMOXYL angine 45 kg : « 10 ml (soit 1000 mg) » matin et soir","10 ml (soit 1000 mg)" in s and "dose-poids" not in s,s)
                    r=await page.evaluate("[dpDose(DP.ADVIL,20,4).txt,dpDose(DP.ADVIL,28,4).txt,dpDose(DP.ADVIL,28,4).beyond]")
                    ok(L+"ADVILMED 20 kg : dose-poids ; 28 kg : ml et mg, au-delà de la pipette",r[0]=="1 dose-poids 20 kg (soit 7,5 ml, 150 mg)" and r[1]=="10,5 ml, soit 210 mg" and r[2],r)
                    r=await page.evaluate(RUN,{"n":A,"w":30,"pick":"ORELOX"}); s=line(r,"ORELOX")
                    ok(L+"ORELOX angine 30 kg : « 12,5 ml, soit 100 mg (dose maximale) » matin et soir","12,5 ml, soit 100 mg (dose maximale)" in s,s)
                    sw=await page.evaluate(SWEEP)
                    ok(L+"toutes les fiches × 5 poids : jamais « dose-poids » au-delà de l'étendue de la pipette",not sw["bad"],sw["bad"][:6])
                    ok(L+"toutes les fiches × 5 poids : suspension en ml toujours accompagnée des mg",sw["n"]==0,sw["nomg"])
                    st=await page.evaluate("(()=>{const P=PACKS.find(p=>p.n==='Angine — enfant (TROD positif)');const m=P.s.find(s=>s.k==='memo');return m.l.map(l=>typeof l==='string'?l:l.t).filter(t=>/Statut/.test(t));})()")
                    ok(L+"fiche angine modifiée : « à relire »",st and "à relire" in st[-1],st)
                    if mob and xp:
                        await page.evaluate(RUN,{"n":A,"w":40,"pick":Z}); await page.wait_for_timeout(300)
                        await page.evaluate("()=>{const e=document.querySelector('.xp .xp-meds')||document.querySelector('#main .adv');if(e)e.scrollIntoView({block:'center'});}"); await page.wait_for_timeout(200)
                        await page.screenshot(path=os.path.join(OUT,"dosepoids-zithromax-40kg.png"))
                    ok(L+"aucune erreur JS",not errors,errors[:2])
                    await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_dosepoids.md"),"w",encoding="utf-8").write("# Tests pipettes dose-poids (18/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
