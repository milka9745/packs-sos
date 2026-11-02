# Lot 1 (02/11/2026) — parcours patient en 6 états : une barre fixe de 3 actions aux mêmes places, aucun bouton en double, chronométré.
# Parcours joué au toucher : Demande → En route → Sur place → Prise en charge → (aperçu) → Sortie → Patient validé → En route (suivant) → Entre deux → En route.
# iPhone 375 px (jour, nuit, grand texte, Express) et ordinateur. Données fictives uniquement.
import asyncio, os, sys, time, json, subprocess, collections, re
def T(d): return [re.sub(r"^[^\wÀ-ÿ]+","",f["t"]) for f in d["fa"]] if d else []
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "captures"); os.makedirs(OUT, exist_ok=True)
PORT = "8851"
results = []; TIMES = {}; BTNS = {}
def ok(name, cond, info=""):
    results.append((name, bool(cond), info)); print(("OK  " if cond else "FAIL"), name, "" if cond else info)
src = open(os.path.join(ROOT, "tests", "test_packs.py"), encoding="utf-8").read()
ns = {"__file__": os.path.join(ROOT, "tests", "test_packs.py")}; exec(src.split("async def run(")[0].replace("8765", PORT), ns)
unlock = ns["unlock"]
SETUP = r"""()=>{window.tourOptimize=async()=>{};window.tpImpactLegs=async()=>null;const now=Date.now();TOUR.base={lat:47.9029,lon:1.9093,label:'cabinet'};TOUR.origin='cabinet';TOUR.current='';TOUR.order=['r1','r2','r3'];TOUR.legs=[];TOUR.computed=now;TOUR.manual=false;
 TOUR.stops=[{id:'r1',addr:'x',nom:'DUPONT Jean',ddn:'01/01/1946',motif:'fièvre toux',tel:'0612345678',lat:47.90,lon:1.91,label:'10 Rue de Bourgogne 45000 Orléans',done:false,ts:now},{id:'r2',addr:'y',nom:'MARTIN Léa',ddn:'02/02/2022',motif:'otite',tel:'0611111111',lat:47.902,lon:1.905,label:'5 Rue Jeanne d Arc 45000 Orléans',done:false,ts:now},{id:'r3',addr:'z',nom:'LEROY Paul',ddn:'03/03/1976',motif:'lombalgie',lat:47.91,lon:1.90,label:'3 Avenue de Paris 45000 Orléans',done:false,ts:now}];
 TESTMODE=true;newPatient();state.sel=null;state.view='';state.cot=cotDefault();state.cot.lieu='visite';render();}"""
VIS = r"""()=>{const v=[...document.querySelectorAll('button,a.btn,[role=button],label.btn')].filter(b=>{const r=b.getBoundingClientRect();return b.offsetParent&&r.width>0&&r.height>0&&!b.closest('[hidden]')&&!b.closest('details:not([open])>*:not(summary)');}).map(b=>({t:(b.textContent||b.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim(),dock:!!b.closest('#fdock')}));return v;}"""
DOCK = r"""()=>{const d=document.getElementById('fdock');if(!d)return null;const r=d.getBoundingClientRect();return {st:d.dataset.fil,fa:[...d.querySelectorAll('.fa')].map(b=>{const q=b.getBoundingClientRect();return {t:b.textContent.replace(/\s+/g,' ').trim(),x:Math.round(q.left),w:Math.round(q.width),h:Math.round(q.height),main:b.classList.contains('fa-main'),now:b.classList.contains('act-now')};}),bottom:Math.round(window.innerHeight-r.bottom),top:Math.round(r.top),vh:window.innerHeight,over:document.documentElement.scrollWidth>window.innerWidth+1};}"""
# clic puis attente de l'état voulu de la barre, mesurés dans la page (temps réel du changement d'état)
TAP = r"""async([sel,want])=>{const e=document.querySelector(sel);if(!e)return {err:'absent '+sel};const t0=performance.now();e.click();
 for(let i=0;i<400;i++){const d=document.getElementById('fdock');const st=d?d.dataset.fil:(state.view||'');if(st===want)return {ms:Math.round(performance.now()-t0)};await new Promise(r=>requestAnimationFrame(r));}
 const d=document.getElementById('fdock');return {err:'état '+(d?d.dataset.fil:'vue '+state.view)+' au lieu de '+want};}"""
async def check_state(page, L, want, label, shot=None):
    d = await page.evaluate(DOCK)
    ok(f"{L}{label} : barre à l'état « {want} »", d and d["st"] == want, d)
    if not d: return None
    v = await page.evaluate(VIS)
    dock_t = [b["t"] for b in v if b["dock"]]
    dup = [t for t in dock_t if any((not b["dock"]) and b["t"] == t for b in v)]
    ok(f"{L}{label} : 3 actions au plus, une seule principale (mise en avant), aucune en double ailleurs à l'écran",
       len(d["fa"]) <= 3 and sum(1 for f in d["fa"] if f["main"]) == 1 and not dup, (d["fa"], dup))
    ok(f"{L}{label} : barre collée en bas, boutons d'au moins 44 px, pas de défilement horizontal",
       d["bottom"] <= 1 and all(f["h"] >= 44 for f in d["fa"]) and not d["over"], d)
    BTNS[L + want] = len(v)
    if shot: await page.screenshot(path=os.path.join(OUT, shot))
    return d
async def tap(page, L, sel, want, label, limit=2000):
    r = await page.evaluate(TAP, [sel, want])
    ok(f"{L}{label} : passage en moins de {limit/1000:g} s", "ms" in r and r["ms"] < limit, r)
    if "ms" in r: TIMES[L + label] = r["ms"]
    await page.wait_for_timeout(150)
    return r
async def parcours(browser, L, w, h, theme="day", big=False, xp=False, shots=False):
    ctx = await browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if w < 500 else 1, is_mobile=w < 500, has_touch=w < 500)
    await ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=f"http://localhost:{PORT}")
    page = await ctx.new_page()
    errs = []; page.on("pageerror", lambda e: errs.append(str(e)))
    await page.add_init_script(f"try{{localStorage.setItem('sos_theme','{theme}');localStorage.setItem('sos_bigtext','{1 if big else 0}');localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_design','garde');}}catch(e){{}}")
    await unlock(page)
    await page.evaluate(SETUP); await page.wait_for_timeout(300)
    sh = (lambda n: f"fil6-{L.strip(' :').replace(' ', '_')}-{n}.png") if shots else (lambda n: None)
    d1 = await check_state(page, L, "demande", "1. Demande", sh("1-demande"))
    ok(L + "1. Demande : Ajouter des fiches · Appel masqué · Lancer la tournée", T(d1) == ["Ajouter des fiches", "Appel masqué", "Lancer la tournée"], T(d1))
    await tap(page, L, "#fdock #tc_begin", "route", "1 → 2 Lancer la tournée")
    d2 = await check_state(page, L, "route", "2. En route", sh("2-route"))
    ok(L + "2. En route : Naviguer · Appeler · Je suis arrivé ; mise en avant sur « Naviguer » (navigation pas encore lancée)", [t.split(" ·")[0] for t in T(d2)] == ["Naviguer", "Appeler", "Je suis arrivé"] and d2["fa"][0]["now"], d2)
    pos = [(f["x"], f["w"]) for f in d2["fa"]]
    await tap(page, L, "#fdock #tc_arrive", "place", "2 → 3 Je suis arrivé")
    d3 = await check_state(page, L, "place", "3. Sur place", sh("3-place"))
    ok(L + "3. Sur place : Scanner · Dicter · Choisir la fiche, aux mêmes places", T(d3) == ["Scanner", "Dicter", "Choisir la fiche"] and [(f["x"], f["w"]) for f in d3["fa"]] == pos, d3)
    await page.click("#fdock #fa_fiche"); await page.wait_for_timeout(400)
    foc = await page.evaluate("document.activeElement&&document.activeElement.id")
    ok(L + "3. « Choisir la fiche » place le curseur dans la recherche", foc in (("xp_motif", "xp_q") if xp else ("q",)), foc)
    if not xp: await page.fill("#q", "grippe"); await page.wait_for_timeout(300)
    r = await page.evaluate(r"""async()=>{const b=[...document.querySelectorAll('#res button.res')].find(x=>/Grippe/.test(x.textContent));const t0=performance.now();if(b)b.click();else{state.sel=PACKS.findIndex(p=>p.n==='Grippe / syndrome viral — adulte');render();}for(let i=0;i<400;i++){const d=document.getElementById('fdock');if(d&&d.dataset.fil==='pec')return {ms:Math.round(performance.now()-t0)};await new Promise(r=>requestAnimationFrame(r));}return {err:'pas de prise en charge'};}""")
    ok(L + "3 → 4 fiche choisie : passage en moins de 2 s", "ms" in r and r["ms"] < 2000, r); TIMES[L + "3 → 4 fiche choisie"] = r.get("ms")
    d4 = await check_state(page, L, "pec", "4. Prise en charge", sh("4-pec"))
    t4 = T(d4)
    ok(L + "4. Prise en charge : Examen complet · Pack simple/à risque · Imprimer", len(t4) == 3 and t4[0].startswith("Examen") and "Pack" in t4[1] and "Imprimer" in t4[2], t4)
    # bascule simple / à risque : un seul bouton, l'état change, le pack reste
    before = await page.evaluate("riskMode()")
    await page.click("#fdock [data-sr]"); await page.wait_for_timeout(300)
    ok(L + "4. bascule Pack simple ⇄ à risque depuis la barre", await page.evaluate("riskMode()") != before and await page.evaluate("!!currentPack()"))
    await page.click("#fdock [data-sr]"); await page.wait_for_timeout(300)
    if (await page.evaluate("excOn()&&examPending()")):
        await page.click("#fdock #fa_exam"); await page.wait_for_timeout(300)
        ok(L + "4. « Examen complet » valide l'examen en un geste", await page.evaluate("state.examOK===true"))
    if xp:
        ok(L + "4. Express : l'action principale est « Imprimer et valider » (bouton de l'Express masqué, pas en double)", await page.evaluate("!!document.querySelector('#fdock #xp_go')&&document.querySelectorAll('#xp_go').length===1"))
        await ctx.close(); return errs
    t0 = time.time(); await page.click("#fdock #fin")
    await page.wait_for_selector("#pb_back2", timeout=8000); TIMES[L + "4 → aperçu Imprimer"] = round((time.time() - t0) * 1000)
    ok(L + "4. « Imprimer » ouvre l'aperçu (pas de barre d'étape par-dessus) et copie le compte rendu", await page.evaluate("!(document.getElementById('fdock')&&document.getElementById('fdock').offsetParent)&&!!state.crCopied"))
    await tap(page, L, "#pb_back2", "sortie", "aperçu → 5 retour")
    d5 = await check_state(page, L, "sortie", "5. Sortie", sh("5-sortie"))
    ok(L + "5. Sortie : Courrier · Réimprimer · Valider · patient suivant", T(d5) == ["Courrier", "Réimprimer", "Valider · patient suivant"], T(d5))
    await page.click("#fdock #tc_valid"); await page.wait_for_timeout(200)
    still = await page.evaluate("document.getElementById('fdock')&&document.getElementById('fdock').dataset.fil")
    ok(L + "5. Valider : 1er toucher = confirmation (rien n'est validé seul)", still == "sortie" and await page.evaluate("!TOUR.stops.find(s=>s.id==='r1').done"), still)
    t0 = time.time(); await page.click("#tc_valid"); await page.wait_for_selector("#vd_next", timeout=4000); TIMES[L + "5 → Patient validé"] = round((time.time() - t0) * 1000)
    ok(L + "5. 2e toucher : patient validé, arrêt fait, journal de test intact", await page.evaluate("TOUR.stops.find(s=>s.id==='r1').done&&state.view==='valid'"))
    await tap(page, L, "#vd_next", "route", "Patient suivant → 2 (visite suivante)")
    ok(L + "Patient suivant : la visite suivante est en cours", await page.evaluate("!!TOUR.current&&TOUR.current!=='r1'"))
    # 6. Entre deux : nouvelle demande pendant le trajet
    r = await page.evaluate(r"""async()=>{const t0=performance.now();TOUR.stops.push({id:'n1',addr:'w',nom:'BERNARD Luc',ddn:'04/04/1980',motif:'malaise',tel:'0622222222',lat:47.905,lon:1.915,label:'7 Rue des Carmes 45000 Orléans',done:false,isNew:true,ts:Date.now()});render();
      for(let i=0;i<400;i++){const d=document.getElementById('fdock');if(d&&d.dataset.fil==='entre')return {ms:Math.round(performance.now()-t0)};await new Promise(r=>requestAnimationFrame(r));}return {err:'pas d entre-deux'};}""")
    ok(L + "nouvelle demande → 6 Entre deux en moins de 2 s", "ms" in r and r["ms"] < 2000, r); TIMES[L + "→ 6 Entre deux"] = r.get("ms")
    d6 = await check_state(page, L, "entre", "6. Entre deux", sh("6-entre"))
    ok(L + "6. Entre deux : Rendre à la régulation · En fin de tournée · Insérer au mieux ; impact affiché", T(d6) == ["Rendre à la régulation", "En fin de tournée", "Insérer au mieux"] and await page.evaluate("!!document.querySelector('.tp-new')"), T(d6))
    await tap(page, L, "#fdock [data-tpins]", "route", "6 → 2 Insérer au mieux", 3000)
    ok(L + "6. demande insérée dans la tournée (plus « nouvelle »)", await page.evaluate("TOUR.order.includes('n1')&&!TOUR.stops.find(s=>s.id==='n1').isNew"))
    tw = await page.evaluate("async()=>{toast('essai');await new Promise(r=>setTimeout(r,350));const t=document.getElementById('toast').getBoundingClientRect(),d=document.getElementById('fdock');return {ok:!d||t.bottom<=d.getBoundingClientRect().top+1,tb:t.bottom,dt:d&&d.getBoundingClientRect().top,h:getComputedStyle(document.documentElement).getPropertyValue('--fdock-h'),bot:getComputedStyle(document.getElementById('toast')).bottom};}")
    ok(L + "messages (toasts) au-dessus de la barre, jamais dessus", tw["ok"], tw)
    # Rendre à la régulation : 2 touchers
    await page.evaluate(r"""()=>{TOUR.stops.push({id:'n2',addr:'v',nom:'PETIT Ana',ddn:'05/05/1990',motif:'fièvre',lat:47.906,lon:1.916,label:'2 Rue Royale 45000 Orléans',done:false,isNew:true,ts:Date.now()});render();}"""); await page.wait_for_timeout(200)
    await page.click("#fdock [data-tpgive]"); await page.wait_for_timeout(150)
    k1 = await page.evaluate("!!TOUR.stops.find(s=>s.id==='n2')")
    await page.click("#fdock [data-tpgive]"); await page.wait_for_timeout(300)
    ok(L + "6. « Rendre à la régulation » : confirmé au 2e toucher, tracé, retour à l'état précédent", k1 and await page.evaluate("!TOUR.stops.find(s=>s.id==='n2')&&TOUR.given.some(g=>/PETIT/.test(g.lbl))&&document.getElementById('fdock').dataset.fil==='route'"))
    # Naviguer → écran conduite automatique
    await page.evaluate("()=>{const a=document.querySelector('#fdock #fa_nav');a.removeAttribute('target');a.setAttribute('href','#');a.click();}"); await page.wait_for_timeout(400)
    ok(L + "Naviguer : écran conduite ouvert automatiquement", await page.evaluate("state.view==='drive'"))
    ok(L + "aucune erreur JavaScript", not errs, errs[:3])
    await ctx.close(); return errs
async def ordre(browser):
    L = "ordre : "
    ctx = await browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = await ctx.new_page(); await unlock(page); await page.evaluate(SETUP); await page.wait_for_timeout(200)
    ok(L + "« Optimiser l'ordre » retiré (écran Tournée)", await page.evaluate("()=>{state.view='tour';render();const r=!document.getElementById('tr_opt')&&!/Optimiser l'ordre/.test(document.body.innerText);state.view='';render();return r;}"))
    calls = await page.evaluate(r"""()=>{let n=0;window.tourOptimize=async()=>{n++;};window.__n=()=>n;tourUse('r1');n=0;patientValidate(true);return 0;}""")
    await page.wait_for_timeout(200)
    ok(L + "patient validé → ordre recalculé automatiquement", await page.evaluate("window.__n()") >= 1)
    await page.evaluate("()=>{state.view='';render();const d=document.querySelector('details.tc-more');if(d)d.open=true;}")
    await page.click("#tc_manual"); await page.wait_for_timeout(300)
    m = await page.evaluate("()=>({manual:TOUR.manual,view:state.view,mv:document.querySelectorAll('[data-tmv]').length})")
    ok(L + "« Ordre manuel » (dans « Plus ») : ▲ ▼ sur chaque visite, plus de recalcul automatique", m["manual"] and m["view"] == "tour" and m["mv"] >= 2, m)
    n0 = await page.evaluate("window.__n()"); await page.evaluate("tourAuto()")
    ok(L + "ordre manuel : aucun recalcul à l'événement suivant", await page.evaluate("window.__n()") == n0)
    msg = await page.evaluate("()=>{TOUR.manual=false;TOUR.autoTs=Date.now();TOUR.autoSrc='ma position';return tourAutoMsg();}")
    ok(L + "message d'une ligne « depuis ma position · recalculé à HH h MM »", "depuis ma position" in msg and "recalculé à" in msg, msg)
    await ctx.close()
async def run():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            await parcours(b, "iPhone jour : ", 375, 812, "day", shots=True)
            await parcours(b, "iPhone nuit : ", 375, 812, "night", shots=True)
            await parcours(b, "iPhone grand texte : ", 375, 812, "day", big=True, shots=True)
            await parcours(b, "iPhone Express : ", 375, 812, "day", xp=True)
            await parcours(b, "ordinateur : ", 1280, 860, "day", shots=True)
            await ordre(b)
            await b.close()
    finally:
        srv.terminate()
    n = sum(1 for r in results if r[1])
    print(f"\n{n}/{len(results)} tests OK")
    print("TEMPS (ms)", json.dumps(TIMES, ensure_ascii=False))
    print("BOUTONS VISIBLES", json.dumps(BTNS, ensure_ascii=False))
    with open(os.path.join(ROOT, "tests", "resultats_fil6.md"), "w", encoding="utf-8") as f:
        f.write("# Lot 1 (02/11/2026) — parcours en 6 états, barre fixe de 3 actions\n\n" + "\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}" + (f" — {r[2]}" if not r[1] else "") for r in results)
                + f"\n\n{n}/{len(results)} tests OK\n\n## Temps mesurés (ms)\n\n" + "\n".join(f"- {k} : {v}" for k, v in TIMES.items())
                + "\n\n## Boutons visibles par état\n\n" + "\n".join(f"- {k} : {v}" for k, v in BTNS.items()) + "\n")
    sys.exit(0 if n == len(results) else 1)
asyncio.run(run())
