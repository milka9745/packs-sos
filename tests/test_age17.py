# Âge (17/10/2026, essai réel : « Tendinopathie d'Achille » adulte appliquée à une enfant de 3 ans, sans alerte) — 398 fiches.
# Chaque médicament a une tranche d'âge ; chez l'enfant, les médicaments adultes sont décochés et signalés, alerte en tête pour une fiche adulte.
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
PORT=8796 if os.environ.get("XP","off")=="off" else 8800
XPON=os.environ.get("XP","off")=="on"   # XP=on : mêmes tests avec l'Express
async def unlock(page,uid):
    if not XPON: await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
SWEEP="""()=>{const res=[];const cls={tous:0,adulte:0};let lines=0;
  PACKS.forEach((P,i)=>{P.s.forEach(sh=>{if(sh.k!=='med')return;sh.l.forEach(l=>{const t=typeof l==='string'?l:(l&&l.t)||'';const c=lineAge(t);if(!(c in cls))cls[c]=0;cls[c]++;lines++;});});
    newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/01/2023',poids:'14',sexe:'f',date:'17/10/2026'});state.sel=i;
    let adultOn=[],pedOn=0,medOn=0;try{const p=currentPack();p.s.forEach((sh,si)=>{if(sh.k!=='med'||state.off[si])return;resolve(sh,si).forEach(x=>{if(!x.on||x.jr)return;medOn++;if(lineAge(x.t)==='adulte'&&!/enfant|nourrisson|bébé|pédiatr|néonat/i.test(P.n))adultOn.push(x.t.slice(0,50));else pedOn++;});});}catch(e){adultOn.push('ERREUR '+e.message);}
    const range=packAgeRange(P);const mm=ageMismatch();const alert=mm.some(x=>x.i===i);
    const hasMed=P.s.some(sh=>sh.k==='med'&&sh.l.some(l=>!(l&&(l.opt||l.grp||l.jr))));res.push({n:P.n,range,adultOn,medOn,alert,hasMed});});
  return {res,cls,lines};}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,lbl) in [(375,812,"iphone"),(1280,900,"ordinateur")]:
                mob=w<500; ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                await unlock(page,"age"+lbl[:4]); L=lbl+" : "
                r=await page.evaluate(SWEEP)
                ok(L+f"chaque médicament a une tranche d'âge ({r['lines']} lignes : {r['cls']})",set(r["cls"].keys())<={"tous","adulte"} and sum(r["cls"].values())==r["lines"],r["cls"])
                bad=[(x["n"],x["adultOn"][:2]) for x in r["res"] if x["adultOn"]]
                ok(L+f"enfant de 3 ans, {len(r['res'])} fiches : aucun médicament adulte coché par défaut",not bad,bad[:8])
                noal=[x["n"] for x in r["res"] if x["range"]=="adulte" and not x["alert"]]
                ok(L+"fiche adulte pour un enfant : toujours une alerte en tête",not noal,noal[:8])
                ped=[x["n"] for x in r["res"] if x["range"]=="enfant"]
                ok(L+f"fiches enfant ({len(ped)}) : jamais signalées comme adultes",all(not x["alert"] for x in r["res"] if x["range"]=="enfant"),[x["n"] for x in r["res"] if x["range"]=="enfant" and x["alert"]][:6])
                lost=[x["n"] for x in r["res"] if x["range"]=="enfant" and x["hasMed"] and x["medOn"]==0]
                ok(L+"fiches enfant : leurs médicaments restent cochés chez l'enfant (rien de décoché à tort)",not lost,lost[:8])
                ach=[x for x in r["res"] if x["n"]=="Tendinopathie d'Achille"][0]
                ok(L+"Tendinopathie d'Achille : fiche adulte, alerte, VOLTARÈNE non coché à 3 ans",ach["range"]=="adulte" and ach["alert"] and not ach["adultOn"],ach)
                # écran : alerte visible en tête, médicaments décochés signalés
                await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/01/2023',poids:'14',sexe:'f'});state.sel=PACKS.findIndex(p=>p.n===\"Tendinopathie d'Achille\");render();}")
                await page.wait_for_timeout(300)
                al=await page.evaluate("(document.querySelector('.agemis')||{}).textContent||''")
                ok(L+"écran : alerte « fiche prévue pour l'adulte », médicaments décochés nommés","prévue pour l'adulte" in al and "décochés" in al,al[:250])
                if mob:
                    await page.evaluate("document.querySelector('.agemis').scrollIntoView({block:'center'})"); await page.wait_for_timeout(200)
                    await page.screenshot(path=os.path.join(OUT,"age-achille-enfant-3ans"+("-express" if XPON else "")+".png"))
                # adulte : rien n'est décoché pour l'âge
                r2=await page.evaluate("""()=>{newPatient();Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1975',sexe:'h'});state.sel=PACKS.findIndex(p=>p.n==="Tendinopathie d'Achille");const p=currentPack();let n=0;p.s.forEach((sh,si)=>{if(sh.k==='med')resolve(sh,si).forEach(x=>{if(x.on)n++;});});return {n,mm:ageMismatch().length};}""")
                ok(L+"adulte : médicaments de la fiche cochés, pas d'alerte d'âge",r2["n"]>=1 and r2["mm"]==0,r2)
                # Express : à 3 ans, une fiche adulte n'est pas proposée en tête
                c=await page.evaluate("()=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'01/01/2023',sexe:'f'});return xpCandidates('tendon talon').ok.map(i=>PACKS[i].n).slice(0,5);}")
                ok(L+"Express à 3 ans : « Tendinopathie d'Achille » rangée dans « Autres âges »","Tendinopathie d'Achille" not in c,c)
                ok(L+"aucune erreur JS",not errors,errors[:2])
                print("   fiches adultes :",sum(1 for x in r["res"] if x["range"]=="adulte"),"enfant :",sum(1 for x in r["res"] if x["range"]=="enfant"),"tous âges :",sum(1 for x in r["res"] if x["range"]=="tous"))
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_age17"+("_express" if XPON else "")+".md"),"w",encoding="utf-8").write("# Tests âge (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
