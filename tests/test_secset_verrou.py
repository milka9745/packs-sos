# -*- coding: utf-8 -*-
"""23/11/2026 — confidentialité du stockage pendant le verrouillage (branche ia, non publié).
Défaut reproduit en 42d : lockNow() puis tourSave() → localStorage["sos_tour"] contenait la tournée en clair (adresse, nom, téléphone) ;
la copie restait jusqu'à la prochaine écriture chiffrée du même nom, et la modification faite pendant le verrouillage était perdue au déverrouillage
(secGet préfère la copie chiffrée, plus ancienne).
Règle : jamais d'écriture en clair quand un code avec chiffrement est configuré ; l'écriture est gardée en mémoire (_secHold) et chiffrée au
déverrouillage, avant les relectures de unlockDone(). Sans profil chiffré (aucun code, nocrypto), l'écriture en clair reste celle d'avant.
Vérifie tous les noms qui passent par secSet (journal, tournée, brouillon, patients validés, dictées, favoris, blocs, ordonnance, renouvellement,
IA, file IA, synchronisation). Patients fictifs. Lancer : python tests/test_secset_verrou.py"""
import asyncio, os, sys, json, subprocess, time, re
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8838; B=f"http://localhost:{PORT}/"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
INIT="try{localStorage.setItem('sos_xpsug','true');if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false');}catch(e){}"
async def create(page,uid):
    await page.goto(B+"index.html"); await page.wait_for_selector("#uid",timeout=20000); await page.wait_for_timeout(500)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
    try: await page.wait_for_selector("#rec_ack",timeout=25000)
    except Exception:
        await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=60000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=60000); await page.wait_for_timeout(500)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
async def enter_code(page,uid):
    await page.wait_for_selector("#pin1",timeout=15000); await page.fill("#uid",uid); await page.fill("#pin1","1234")
    try: await page.click("#pin_ok",timeout=2000)
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=30000); await page.wait_for_timeout(600)
# mots fictifs qui ne doivent jamais apparaître en clair dans le stockage
MOTS=["VERROU","Fictive","0600000099","CONFID"]
SCAN="""(mots)=>{const hits=[];for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);const v=localStorage.getItem(k)||'';for(const m of mots)if(v.includes(m))hits.push(k+' ← '+m);}return hits;}"""
WRITE_LOCKED="""()=>{
 TOUR.stops.push({id:'vx1',addr:'12 rue Fictive 45000 Orléans',nom:'VERROU Deux',ddn:'02/02/1972',motif:'fièvre',tel:'0600000099',lat:47.9,lon:1.9,label:'12 rue Fictive 45000 Orléans',done:false,ts:Date.now()});tourSave();
 JOURNAL.push({ts:Date.now(),patient:'VERROU Essai',pack:'Essai (fictif)',codes:[]});journalSave();
 DICTH.push({ts:Date.now(),txt:'CONFID dictée fictive pendant le verrouillage'});try{dictHistSave();}catch(e){secSet('sos_dicthist',DICTH);}
 secSet('sos_essai_verrou',{note:'CONFID essai'});
 return {hold:Object.keys(_secHold).sort(),clairs:['sos_tour','sos_journal','sos_dicthist','sos_essai_verrou'].filter(k=>localStorage.getItem(k)!==null)};}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":1280,"height":850},device_scale_factor=1,service_workers="block")
            await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await page.add_init_script(INIT)
            await create(page,"verrou1")
            html=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
            names=sorted(set(re.findall(r'secSet\("([a-z_]+)"',html)))
            ok("code : noms écrits par secSet (journal, brouillon, tournée, patients validés, dictées, favoris, blocs, IA, file IA, synchronisation)",{"sos_journal","sos_draft","sos_tour","sos_validhist","sos_dicthist","sos_xpfav_","sos_blocs_","sos_ai","sos_ai_use","sos_aiq","sos_sync"}<=set(names),names)
            ok("code : secSet garde l'écriture pendant le verrouillage (_secHold) et unlockDone la chiffre avant les relectures (secHoldFlush)","_secHold[name]={str,ts:Date.now()};return;" in html and "try{await secHoldFlush();}catch(e){}" in html and html.index("secHoldFlush();}catch(e){}")<html.index('JOURNAL=await secGet("sos_journal",[]);'),"")
            # 1. état de référence : une tournée et un journal chiffrés avant le verrouillage
            await page.evaluate("""()=>{TOUR.stops=[{id:'v0',addr:'1 place Fictive 45000 Orléans',nom:'VERROU Un',ddn:'01/01/1970',motif:'toux',tel:'0600000098',lat:47.9,lon:1.9,label:'1 place Fictive 45000 Orléans',done:false,ts:Date.now()}];TOUR.order=['v0'];tourSave();JOURNAL.push({ts:Date.now(),patient:'VERROU Zéro',pack:'Essai (fictif)',codes:[]});journalSave();}""")
            for _ in range(20):
                if await page.evaluate("!!localStorage.getItem('sos_tour_enc')&&!!localStorage.getItem('sos_journal_enc')"): break
                await page.wait_for_timeout(250)
            ok("déverrouillé : tournée et journal écrits chiffrés (clés _enc), aucune copie en clair",await page.evaluate("!!localStorage.getItem('sos_tour_enc')&&!!localStorage.getItem('sos_journal_enc')&&localStorage.getItem('sos_tour')===null&&localStorage.getItem('sos_journal')===null"))
            ok("déverrouillé : aucun mot fictif lisible dans le stockage",not await page.evaluate(SCAN,MOTS),await page.evaluate(SCAN,MOTS))
            # 2. verrouillage puis écritures (tournée, journal, dictées, nom quelconque)
            await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1",timeout=5000); await page.wait_for_timeout(300)
            w=await page.evaluate(WRITE_LOCKED); await page.wait_for_timeout(500)
            ok("verrouillé : secSet n'écrit rien en clair (sos_tour, sos_journal, sos_dicthist, nom quelconque absents de localStorage)",not w["clairs"],w)
            ok("verrouillé : les écritures sont gardées en mémoire (_secHold : journal, tournée, dictées, nom quelconque)",{"sos_tour","sos_journal","sos_dicthist","sos_essai_verrou"}<=set(w["hold"]),w["hold"])
            ok("verrouillé : aucun mot fictif lisible dans le stockage (adresse, nom, téléphone)",not await page.evaluate(SCAN,MOTS),await page.evaluate(SCAN,MOTS))
            enc_before=await page.evaluate("localStorage.getItem('sos_tour_enc')")
            # 3. déverrouillage : écritures chiffrées avant les relectures → rien n'est perdu
            await enter_code(page,"verrou1")
            r=await page.evaluate("""async()=>{const t=await secGet('sos_tour',null);const j=await secGet('sos_journal',[]);const d=await secGet('sos_dicthist',[]);const x=await secGet('sos_essai_verrou',null);
             return {hold:Object.keys(_secHold),memTour:TOUR.stops.some(s=>s.nom==='VERROU Deux'),memJ:JOURNAL.some(e=>e.patient==='VERROU Essai'),stTour:!!(t&&t.stops&&t.stops.some(s=>s.nom==='VERROU Deux')),stJ:j.some(e=>e.patient==='VERROU Essai'),stD:d.some(e=>e.txt&&e.txt.includes('CONFID')),stX:!!(x&&x.note),encChanged:localStorage.getItem('sos_tour_enc')!==%r,clairs:['sos_tour','sos_journal','sos_dicthist','sos_essai_verrou'].filter(k=>localStorage.getItem(k)!==null)};}"""%enc_before)
            ok("déverrouillé : la modification faite pendant le verrouillage est conservée en mémoire (tournée, journal)",r["memTour"] and r["memJ"],r)
            ok("déverrouillé : … et écrite chiffrée (secGet relit la tournée, le journal, les dictées et le nom quelconque ; sos_tour_enc a changé)",r["stTour"] and r["stJ"] and r["stD"] and r["stX"] and r["encChanged"],r)
            ok("déverrouillé : _secHold vidé, toujours aucune copie en clair",not r["hold"] and not r["clairs"],r)
            ok("déverrouillé : aucun mot fictif lisible dans le stockage",not await page.evaluate(SCAN,MOTS),await page.evaluate(SCAN,MOTS))
            # 4. rechargement + code : les données écrites pendant le verrouillage sont toujours là
            await page.reload(); await page.wait_for_timeout(1500); await enter_code(page,"verrou1")
            r2=await page.evaluate("({t:TOUR.stops.some(s=>s.nom==='VERROU Deux'),j:JOURNAL.some(e=>e.patient==='VERROU Essai'),clair:localStorage.getItem('sos_tour')===null&&localStorage.getItem('sos_journal')===null})")
            ok("après rechargement et code : tournée et journal complets, toujours chiffrés",r2["t"] and r2["j"] and r2["clair"],r2)
            # 5. sans profil chiffré, l'écriture en clair reste celle d'avant (aucun code configuré ; chiffrement indisponible : nocrypto)
            leg=await page.evaluate("""()=>{const k=SEC.key;const m=localStorage.getItem('sos_sec');let a=null,b=null;try{SEC.key=null;localStorage.removeItem('sos_sec');secSet('sos_essai_clair',{a:1});a=localStorage.getItem('sos_essai_clair');localStorage.removeItem('sos_essai_clair');
             localStorage.setItem('sos_sec',JSON.stringify({nocrypto:true,pin:'1234',uid:'x'}));secSet('sos_essai_clair2',{b:2});b=localStorage.getItem('sos_essai_clair2');localStorage.removeItem('sos_essai_clair2');}finally{localStorage.setItem('sos_sec',m);SEC.key=k;}return {a,b,hold:Object.keys(_secHold)};}""")
            ok("sans code configuré ou sans chiffrement (nocrypto) : écriture en clair inchangée, rien n'est gardé",leg["a"]=='{"a":1}' and leg["b"]=='{"b":2}' and not leg["hold"],leg)
            # 6. secRemove pendant le verrouillage oublie aussi l'écriture gardée
            await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1",timeout=5000)
            rm=await page.evaluate("()=>{secSet('sos_essai_rm',{z:1});const a=Object.keys(_secHold).includes('sos_essai_rm');secRemove('sos_essai_rm');return {a,b:Object.keys(_secHold).includes('sos_essai_rm'),clair:localStorage.getItem('sos_essai_rm')};}")
            ok("verrouillé : secRemove oublie aussi l'écriture gardée",rm["a"] and not rm["b"] and rm["clair"] is None,rm)
            await enter_code(page,"verrou1")
            ok("aucune erreur JavaScript",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
