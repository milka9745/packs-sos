# Lot 2 (03/11/2026) — un seul catalogue et stockage sans perte.
# Catalogue : les anciennes fiches remplacées par leur version v40 ne gardent que leur nom (place et numéros inchangés), une seule fusion (catAdd),
# fiches jumelles regroupées dans la recherche (« Autre version »), rien de supprimé.
# Stockage : IndexedDB chiffré, copie de secours en localStorage pour journal / tournée / brouillon / identité / synchronisation, la plus récente gagne,
# migration des anciennes données, échec d'écriture jamais silencieux, écriture immédiate au verrouillage, bases médicaments en IndexedDB,
# archive des validés après 12 h (sans images), jauge dans Réglages. Données fictives uniquement.
import asyncio, os, sys, time, json, subprocess, re
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "captures"); os.makedirs(OUT, exist_ok=True)
PORT = "8861"
results = []; TIMES = {}
def ok(name, cond, info=""):
    results.append((name, bool(cond), info)); print(("OK  " if cond else "FAIL"), name, "" if cond else info)
src = open(os.path.join(ROOT, "tests", "test_packs.py"), encoding="utf-8").read()
ns = {"__file__": os.path.join(ROOT, "tests", "test_packs.py")}; exec(src.split("async def run(")[0].replace("8765", PORT), ns)
unlock = ns["unlock"]
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
W = "()=>new Promise(r=>setTimeout(r,450))"

def catalogue_source():
    # chaque fiche v40 n'est définie en entier qu'une fois dans le fichier (plus d'ancienne version morte)
    noms = re.findall(r'\{n:"((?:[^"\\]|\\.)*)",k:', HTML)
    dbl = sorted({n for n in noms if noms.count(n) > 1})
    ok("catalogue : aucune fiche définie deux fois en entier dans le fichier (anciennes versions remplacées retirées)", not dbl, dbl[:10])
    stubs = re.findall(r'\{n:"(?:[^"\\]|\\.)*"\}', HTML.split("const PACKS = [", 1)[1].split("const PACKS_V40=[", 1)[0])
    ok("catalogue : 90 anciennes fiches réduites à leur nom (leur place est gardée)", len(stubs) == 90, len(stubs))
    ok("catalogue : une seule fusion (catAdd) au lieu de 17 boucles (bloc 17 : renouvellement d'ordonnance, 11/11/2026)", HTML.count("PACKS.findIndex(p=>p.n===np.n)") == 1 and HTML.count("catAdd(PACKS_V40") == 17, HTML.count("PACKS.findIndex(p=>p.n===np.n)"))

async def catalogue(page):
    r = await page.evaluate("""()=>({n:PACKS.length,vide:PACKS.filter(p=>!Array.isArray(p.s)||!p.s.length).map(p=>p.n),uniq:new Set(PACKS.map(p=>p.n)).size,
      tw:(()=>{twinOf(0);return _twinIdx.size;})(),twn:Object.keys(CAT_TWIN).length})""")
    ok("catalogue : 401 fiches, toutes avec contenu, noms uniques", r["n"] == 401 and not r["vide"] and r["uniq"] == 401, r)
    ok("catalogue : les 13 fiches jumelles retrouvent leur fiche v40 (dont Renouvellement de traitement chronique → Renouvellement d'ordonnance)", r["tw"] == 13 == r["twn"], r)
    await page.fill("#q", "insomnie"); await page.wait_for_timeout(250)
    rows = await page.evaluate("()=>[...document.querySelectorAll('#res .res .n')].map(e=>e.textContent)")
    tw = await page.evaluate("()=>[...document.querySelectorAll('#res .twin')].map(e=>e.textContent)")
    ok("recherche « insomnie » : une ligne « Insomnie », l'ancienne fiche en « Autre version » dessous (plus de doublon)",
       any(x.startswith("Insomnie") and "chronique" not in x for x in rows) and not any("Insomnie chronique" in x for x in rows) and "Autre version : Insomnie chronique" in tw, (rows, tw))
    await page.evaluate("()=>{const t=document.querySelector('#res .twin');if(t)t.scrollIntoView({block:'center'});}"); await page.wait_for_timeout(150)
    await page.screenshot(path=os.path.join(OUT, "lot2-recherche-jumelles.png"))
    await page.click("#res .twin")
    sel = await page.evaluate("()=>selIdx().map(i=>PACKS[i].n)")
    ok("« Autre version » sélectionne l'ancienne fiche (rien n'est perdu)", sel == ["Insomnie chronique"], sel)
    await page.evaluate("()=>{state.sel=null;render();}")
    await page.fill("#q", "insomnie chronique"); await page.wait_for_timeout(250)
    rows = await page.evaluate("()=>[...document.querySelectorAll('#res .res .n')].map(e=>e.textContent)")
    ok("recherche précise « insomnie chronique » : l'ancienne fiche en ligne normale", any(x.startswith("Insomnie chronique") for x in rows), rows)
    await page.fill("#q", ""); await page.wait_for_timeout(100)
    x = await page.evaluate("()=>{const c=xpCandidates('érysipèle jambe');const L=[...c.ok,...c.other].map(i=>PACKS[i].n);return L;}")
    ok("Express : la fiche v40 passe avant sa jumelle", "Érysipèle — dermohypodermite" in x and "Érysipèle de jambe — adulte" in x and x.index("Érysipèle — dermohypodermite") < x.index("Érysipèle de jambe — adulte"), x)

async def stockage(page):
    # 1. journal : IndexedDB chiffré + copie de secours chiffrée en localStorage, identiques, sans texte en clair
    r = await page.evaluate("""async()=>{JOURNAL.push({id:'jt1',ts:Date.now(),patient:'ZEBULON Fictif',pack:'Angine — adulte',codes:[]});const t0=performance.now();journalSave();await secWriteNow('sos_journal');const ms=performance.now()-t0;
      const db=await kvGet('sos_journal_enc');const ls=localStorage.getItem('sos_journal_enc');return {ms:Math.round(ms),db:!!db,same:db===ls,clair:(db||'').includes('ZEBULON')||(ls||'').includes('ZEBULON'),ts:encTs(db),back:(await secGet('sos_journal',[])).some(e=>e.id==='jt1')};}""")
    ok("journal : écrit chiffré dans IndexedDB, copie de secours identique en localStorage, aucun nom en clair", r["db"] and r["same"] and not r["clair"] and r["ts"] > 0 and r["back"], r)
    TIMES["écriture chiffrée du journal"] = r["ms"]
    r = await page.evaluate("""async()=>{const keep=JOURNAL.slice();for(let i=0;i<1000;i++)JOURNAL.push({id:'jf'+i,ts:Date.now()-i*6e4,patient:'FICTIF '+i,pack:'Angine — adulte',age:40,codes:[{c:'VG'},{c:'MU'}],cr:'Compte rendu fictif '.repeat(20)});
      const t0=performance.now();journalSave();await secWriteNow('sos_journal');const ms=performance.now()-t0;const n=(await secGet('sos_journal',[])).length;const t1=performance.now()-t0-ms;JOURNAL=keep;journalSave();await secWriteNow('sos_journal');
      return {ms:Math.round(ms),lecture:Math.round(t1),n,ko:Math.round(((await kvGet('sos_journal_enc'))||'').length/1024)};}""")
    ok("journal de 1 000 patients : écrit en moins de 1 s et relu en entier", r["ms"] < 1000 and r["n"] >= 1000, r)
    TIMES["journal de 1 000 patients : écriture chiffrée"] = r["ms"]; TIMES["journal de 1 000 patients : lecture"] = r["lecture"]
    # 2. historique des validés : IndexedDB seulement
    r = await page.evaluate("""async()=>{await secPut('sos_validhist',[{ts:Date.now(),snap:{patient:'ZEBULON Fictif',photos:[]}}]);return {db:!!(await kvGet('sos_validhist_enc')),ls:localStorage.getItem('sos_validhist_enc')};}""")
    ok("patients validés : IndexedDB seulement (plus en localStorage)", r["db"] and r["ls"] is None, r)
    # 3. migration d'une ancienne donnée (version précédente : sans heure) → reprise puis IndexedDB, localStorage libéré
    r = await page.evaluate("""async()=>{await kvDel('sos_dicthist_enc');localStorage.setItem('sos_dicthist_enc',await encStr(JSON.stringify([{ts:Date.now(),txt:'dictée fictive'}])));
      const v=await secGet('sos_dicthist',[]);await (_secW['sos_dicthist']||Promise.resolve());await new Promise(r=>setTimeout(r,100));
      return {v:v.length,db:!!(await kvGet('sos_dicthist_enc')),ls:localStorage.getItem('sos_dicthist_enc')};}""")
    ok("migration : ancienne donnée de localStorage lue, copiée dans IndexedDB, puis retirée de localStorage", r["v"] == 1 and r["db"] and r["ls"] is None, r)
    # 4. la plus récente gagne ; une copie écrite par une version précédente (sans heure) gagne aussi
    r = await page.evaluate("""async()=>{const enc=async(o,ts)=>{const x=JSON.parse(await encStr(JSON.stringify(o)));if(ts)x.ts=ts;return JSON.stringify(x);};
      await kvPut('sos_tour_enc',await enc({stops:[{id:'neuf'}]},Date.now()));localStorage.setItem('sos_tour_enc',await enc({stops:[{id:'vieux'}]},Date.now()-60000));const a=(await secGet('sos_tour',null)).stops[0].id;
      localStorage.setItem('sos_tour_enc',await enc({stops:[{id:'v40'}]},0));const b=(await secGet('sos_tour',null)).stops[0].id;await new Promise(r=>setTimeout(r,300));
      tourSave();await secWriteNow('sos_tour');return {a,b};}""")
    ok("lecture : la copie la plus récente gagne ; une écriture de /v40/ (sans heure) est reprise", r["a"] == "neuf" and r["b"] == "v40", r)
    # 5. IndexedDB en panne : repli sur localStorage, rien de perdu
    r = await page.evaluate("""async()=>{const real=KV.db;KV.db={transaction(){throw new Error('panne simulée');}};KV.errTs=0;
      try{await secPut('sos_validhist',[{ts:Date.now(),snap:{patient:'REPLI',photos:[]}}]);}catch(e){}KV.db=real;
      const ls=!!localStorage.getItem('sos_validhist_enc');const v=await secGet('sos_validhist',[]);return {ls,v:v[0]&&v[0].snap.patient,err:KV.errTs};}""")
    ok("IndexedDB indisponible : la donnée part en localStorage et se relit (aucune perte)", r["ls"] and r["v"] == "REPLI" and not r["err"], r)
    # 6. tout est plein : échec visible (message, bandeau rouge), jamais silencieux
    r = await page.evaluate("""async()=>{const real=KV.db,si=Storage.prototype.setItem;KV.db={transaction(){throw new DOMException('plein','QuotaExceededError');}};
      Storage.prototype.setItem=function(k,v){if(/sos_validhist/.test(k))throw new DOMException('plein','QuotaExceededError');return si.call(this,k,v);};let thrown=false;
      try{await secPut('sos_validhist',[{ts:Date.now(),snap:{patient:'PLEIN',photos:[]}}]);}catch(e){thrown=true;}KV.db=real;Storage.prototype.setItem=si;
      await new Promise(r=>setTimeout(r,200));state.view='';render();
      return {thrown,toast:(document.getElementById('toast')||{}).textContent||'',lv:storeLevel(),bar:!!document.querySelector('.stbar.bad')};}""")
    ok("stockage plein : l'appel échoue, message « Non enregistré », bandeau rouge sur l'écran principal", r["thrown"] and "Non enregistré" in r["toast"] and r["lv"] == 2 and r["bar"], r)
    await page.evaluate("()=>{const b=document.querySelector('.stbar');if(b)b.scrollIntoView({block:'center'});}"); await page.wait_for_timeout(150)
    await page.screenshot(path=os.path.join(OUT, "lot2-bandeau-stockage.png"))
    await page.evaluate("()=>{KV.errTs=0;KV.err='';render();}")
    # 7. verrouillage juste après une frappe : l'écriture en attente est faite avec la clé du moment
    r = await page.evaluate("""async()=>{const K=SEC.key;JOURNAL.push({id:'jt2',ts:Date.now(),patient:'VERROU Fictif',pack:'x',codes:[]});journalSave();lockNow();
      await new Promise(r=>setTimeout(r,500));SEC.key=K;SEC.unlocked=true;const l=document.getElementById('lock');if(l)l.remove();document.body.classList.remove('locked');
      const j=await secGet('sos_journal',[]);return j.some(e=>e.id==='jt2');}""")
    ok("verrouillage immédiat après une saisie : rien n'est perdu", r is True, r)
    # 8. bases médicaments : localStorage → IndexedDB, relues au démarrage
    r = await page.evaluate("""async()=>{localStorage.setItem('sos_bdpm',JSON.stringify({ts:123,n:1,rows:['DOLIPRANE 1000 mg|comprimé']}));await bigBoot();const ls=localStorage.getItem('sos_bdpm');
      BDPM=null;await bigBoot();const back=BDPM&&BDPM.ts;const bak=(await backupCollect()).plain.sos_bdpm;await kvDel('sos_bdpm');BDPM=null;return {ls,back,bak:!!bak};}""")
    ok("base médicaments : déplacée dans IndexedDB, relue au démarrage, incluse dans la sauvegarde", r["ls"] is None and r["back"] == 123 and r["bak"], r)
    # 9. patient validé depuis plus de 12 h → archive chiffrée, sans images, incluse dans la sauvegarde
    r = await page.evaluate("""async()=>{await secRemove('sos_archive');const old=Date.now()-13*3600e3;
      VALID.hist=[{ts:Date.now(),snap:{patient:'RECENT Fictif',photos:[]}},{ts:old,snap:{patient:'ANCIEN Fictif',photos:[{id:'ph1',src:'data:image/jpeg;base64,AAAA'}],docs:[{t:'bilan',pages:[{id:'dp1',src:'data:x'}]}]}}];VALID.stale=[];
      validSave();await secWriteNow('sos_validhist');await validLoad();await (_secW['sos_archive']||Promise.resolve());const a=await secGet('sos_archive',[]);const b=await backupCollect();
      return {hist:VALID.hist.map(v=>v.snap.patient),arch:a.map(v=>v.snap.patient),img:JSON.stringify(a).includes('base64'),src:a[0]&&a[0].snap.docs[0].pages[0].src,bak:!!(b.enc.sos_archive&&b.enc.sos_archive.length),db:!!(await kvGet('sos_archive_enc')),ls:localStorage.getItem('sos_archive_enc')};}""")
    ok("validé depuis plus de 12 h : quitte « Rouvrir », entre dans l'archive chiffrée (IndexedDB) sans photo ni image de page",
       r["hist"] == ["RECENT Fictif"] and r["arch"] == ["ANCIEN Fictif"] and not r["img"] and r["src"] == "" and r["db"] and r["ls"] is None, r)
    ok("archive incluse dans la sauvegarde chiffrée", r["bak"], r)

async def jauge(page, L):
    await page.evaluate("()=>{state.view='journal';render();}")
    await page.wait_for_function("()=>{const g=document.getElementById('st_gauge');return g&&/utilisés/.test(g.textContent);}", timeout=8000)
    r = await page.evaluate("()=>{const g=document.getElementById('st_gauge');(document.getElementById('st_sec')||g).scrollIntoView({block:'start'});return {t:g.textContent,bar:!!g.querySelector('[role=meter]'),cats:[...g.querySelectorAll('.stg-l li span')].map(e=>e.textContent),over:document.documentElement.scrollWidth>window.innerWidth+1};}")
    ok(L + "jauge de stockage dans Réglages : barre, total utilisé, détail par catégorie, sans débordement",
       r["bar"] and "utilisés" in r["t"] and len(r["cats"]) >= 1 and "localStorage" in r["t"] and not r["over"], r)
    await page.wait_for_timeout(200)
    await page.screenshot(path=os.path.join(OUT, f"lot2-jauge-{L.strip(' :').replace(' ', '_')}.png"))
    await page.evaluate("()=>{state.view='';render();}")

async def run():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    catalogue_source()
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            for L, w, h, theme, big in [("iPhone jour : ", 375, 812, "day", False), ("iPhone nuit : ", 375, 812, "night", False), ("iPhone grand texte : ", 375, 812, "day", True), ("ordinateur : ", 1280, 860, "day", False)]:
                ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 500 else 1, is_mobile=w < 500, has_touch=w < 500)
                page = await ctx.new_page(); errs = []; page.on("pageerror", lambda e: errs.append(str(e)))
                await page.add_init_script(f"try{{localStorage.setItem('sos_theme','{theme}');localStorage.setItem('sos_bigtext','{1 if big else 0}');localStorage.setItem('sos_design','garde');}}catch(e){{}}")
                await unlock(page)
                if L.startswith("iPhone jour"):
                    await catalogue(page); await stockage(page)
                await jauge(page, L)
                ok(L + "aucune erreur JavaScript", not errs, errs[:3])
                await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    n = sum(1 for r in results if r[1])
    print(f"\n{n}/{len(results)} tests OK"); print("TEMPS (ms)", json.dumps(TIMES, ensure_ascii=False))
    with open(os.path.join(ROOT, "tests", "resultats_stock.md"), "w", encoding="utf-8") as f:
        f.write("# Lot 2 (03/11/2026) — un seul catalogue, stockage sans perte\n\n" + "\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}" + (f" — {r[2]}" if not r[1] else "") for r in results)
                + f"\n\n{n}/{len(results)} tests OK\n\n## Temps mesurés (ms)\n\n" + "\n".join(f"- {k} : {v}" for k, v in TIMES.items()) + "\n")
    sys.exit(0 if n == len(results) else 1)
asyncio.run(run())
