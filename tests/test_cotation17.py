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
                T="""(a)=>{const [y,m,d,h,mi]=a.t;const ts=new Date(y,m-1,d,h,mi).getTime();const r=cotCompute({ts,lieu:a.lieu,ecg:!!a.ecg,km:"",age:a.age,extra:a.extra||[],minus:[]});return {c:r.codes.map(x=>x.c),t:r.total};}"""
                r=await page.evaluate(T,{"t":[2026,10,14,15,0],"lieu":"visite","age":40,"ecg":1})
                ok(L+"visite avec ECG : VG + MU + DEQP003 + YYYY490 = 76,97 €",r["c"]==["VG","MU","DEQP003","YYYY490"] and abs(r["t"]-76.97)<0.001,r)
                r=await page.evaluate(T,{"t":[2026,10,14,15,0],"lieu":"cabinet","age":40,"ecg":1})
                ok(L+"consultation avec ECG : G + DEQP003 = 44,77 € (pas de YYYY490)",r["c"]==["G","DEQP003"] and abs(r["t"]-44.77)<0.001,r)
                r=await page.evaluate(T,{"t":[2026,10,14,21,30],"lieu":"cabinet","age":40,"ecg":1})
                ok(L+"consultation avec ECG à 21 h 30 : G + CRN + DEQP003 = 87,27 €",r["c"]==["G","CRN","DEQP003"] and abs(r["t"]-87.27)<0.001,r)
                r=await page.evaluate(T,{"t":[2026,10,14,15,0],"lieu":"visite","age":40,"extra":["DEQP003"]})
                ok(L+"ECG ajouté au journal sur une visite : YYYY490 ajouté aussi",r["c"]==["VG","MU","DEQP003","YYYY490"],r)
                ok(L+"tarifs : G 30, VG 30, DEQP003 14,77, YYYY490 9,60",await page.evaluate("TARIFS.G===30&&TARIFS.VG===30&&TARIFS.DEQP003===14.77&&TARIFS.YYYY490===9.6"))
                # « Tarifs utilisés » : modifiable, conservé
                await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(300)
                v=await page.evaluate("(()=>{const i=document.querySelector('[data-tarif=DEQP003]'),j=document.querySelector('[data-tarif=YYYY490]');return [i&&i.value,j&&j.value];})()")
                ok(L+"« Tarifs utilisés » : DEQP003 14,77 et YYYY490 9,6 affichés",v==["14,77","9,6"],v)
                await page.fill("[data-tarif=DEQP003]","15,10"); await page.dispatch_event("[data-tarif=DEQP003]","change"); await page.wait_for_timeout(200)
                ok(L+"tarif modifié, enregistré",await page.evaluate("TARIFS.DEQP003===15.1&&JSON.parse(localStorage.getItem('sos_tarifs')).DEQP003===15.1"))
                await page.evaluate("localStorage.setItem('sos_tarifs',JSON.stringify(Object.assign({},TARIFS_DEF,{DEQP003:14.77,_v:17})))")
                bad=await page.evaluate("Object.keys(TARIFS).filter(k=>['U','MDN','MDI','MM','F'].includes(k))")
                ok(L+"aucun code U, MDN, MDI, MM ni F dans les tarifs",not bad,bad)
                # écran (Express) et journal
                await page.evaluate("""()=>{newPatient();const i=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1985',sexe:'h'});state.view='';state.cot.lieu='visite';state.cot.auto=false;state.cot.h='15:00';state.sel=i;render();}""")
                await page.wait_for_timeout(300)
                xp=await page.evaluate("(document.querySelector('.xp')||{}).innerText||''")
                exp=await page.evaluate("(()=>{const c=state.cot;const a=ageY();return cotCompute({ts:Date.now(),lieu:c.lieu,ecg:c.ecg,km:c.km,age:a?a.y:null,extra:[],minus:[]}).codes.map(x=>x.c).join(' + ');})()")
                line=[l for l in xp.split(chr(10)) if "Cotation" in l]
                ok(L+f"écran Express : cotation de l'heure (« {exp} »), jamais « U » seul",line and exp in line[0] and " U " not in line[0]+" " and ("MU" in exp or "VR" in exp or "CR" in exp),line)
                await page.evaluate("journalUpsert(currentPack());state.view='journal';render();"); await page.wait_for_timeout(300)
                jt=await page.evaluate("[...document.querySelectorAll('.jcodes .chip')].map(x=>x.textContent).join(' | ')")
                jexp=await page.evaluate("cotCompute(JOURNAL[JOURNAL.length-1]).codes.map(x=>x.c)")
                ok(L+f"journal : codes de l'acte ({'+'.join(jexp)}) affichés, jamais « U »",all(c in jt for c in jexp) and not any(c.strip().startswith("U ") for c in jt.split("|")),jt)
                ok(L+"aucune erreur JS",not errors,errors[:2])
                await ctx.close()
            # anciens tarifs enregistrés : 14,26 (ancienne valeur par défaut) → 14,77 ; un montant personnalisé est conservé
            for old,exp,name in [(14.26,14.77,"ancienne valeur par défaut 14,26 → 14,77"),(15.0,15.0,"montant personnalisé (15,00) conservé")]:
                ctx=await b.new_context(viewport={"width":1280,"height":900}); page=await ctx.new_page()
                await page.add_init_script(f"try{{if(!localStorage.getItem('__t'))localStorage.setItem('sos_tarifs',JSON.stringify({{G:30,VG:30,U:22.6,DEQP003:{old}}}));localStorage.setItem('__t','1');}}catch(e){{}}")
                await unlock(page,"cotmig"+str(int(old*100)))
                r=await page.evaluate("({d:TARIFS.DEQP003,y:TARIFS.YYYY490,mu:TARIFS.MU,u:TARIFS.U})")
                ok("migration des tarifs : "+name+" ; U → MU ; YYYY490 ajouté",abs(r["d"]-exp)<0.001 and r["y"]==9.6 and r["mu"]==22.6 and r.get("u") is None,r)
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_cotation17.md"),"w",encoding="utf-8").write("# Tests cotation (17/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
