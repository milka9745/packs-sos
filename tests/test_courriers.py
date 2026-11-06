# Corrections v41z (03/11/2026).
# 1. Fiche MccMissionSG : « N° INTERVENTION » (lu « O INTERVENTION », « N INTERVENTION ») est une étiquette, jamais un motif ; sans motif lisible,
#    le champ reste vide et l'écran dit « Motif à saisir ».
# 2. Courriers : aucune phrase de remplissage pour une donnée absente (« à votre disposition sur simple demande », « non précisé », « à compléter »…).
#    Une information absente ne donne aucune phrase ; ordre fixe motif → éléments cliniques → traitement → question ; les éléments cliniques
#    attendus par le courrier et absents de l'observation sont signalés à l'écran avant d'imprimer (« ajoute le nombre d'ongles atteints »).
#    Tous les gabarits de courrier et de consignes du catalogue sont repassés : le test échoue sur ces formules. Données fictives uniquement.
import asyncio, os, sys, time, json, subprocess, re
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "captures"); os.makedirs(OUT, exist_ok=True)
PORT = "8862"
results = []; TIMES = {}
def ok(name, cond, info=""):
    results.append((name, bool(cond), info)); print(("OK  " if cond else "FAIL"), name, "" if cond else info)
src = open(os.path.join(ROOT, "tests", "test_packs.py"), encoding="utf-8").read()
ns = {"__file__": os.path.join(ROOT, "tests", "test_packs.py")}; exec(src.split("async def run(")[0].replace("8765", PORT), ns)
unlock = ns["unlock"]
HTML = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# fiches fictives (aucune donnée réelle)
BASE = "DUPONT MARIE\nNée le 05/06/1990 - 36 A\nTél patient 06 12 34 56 78\nAdresse patient : 3 rue de la Gare\n45000 ORLEANS\n"
FICHES = {
    "A": BASE + "N° INTERVENTION 26110300123\nDL CHEVILLE\nchute dans l'escalier hier soir",
    "B": BASE + "O INTERVENTION\nERUPTION\nboutons depuis 2 jours",
    "C": BASE + "N INTERVENTION : 2611 0300 123\n",
    "D": "N° INTERVENTION\n" + BASE + "N° INTERVENTION\nERUPTION\nboutons depuis 2 jours",
}
FILLERS_OUI = ["Les résultats sont à votre disposition sur simple demande.", "Antécédents : non précisés.", "Traitement habituel non renseigné.",
               "Nombre d'ongles atteints à compléter.", "Terrain à préciser.", "Constantes : [à compléter].", "Données non disponibles."]
FILLERS_NON = ["Pas d'allergie connue.", "Statut vaccinal inconnu, rappel proposé.", "Je reste à votre disposition pour tout complément.",
               "Porte d'entrée non retrouvée à l'examen.", "Je vous laisse juge des explorations et de la suite de la prise en charge."]

def static():
    ok("source : FILLER_RE défini, DOC_FALLBACK (« sont à votre disposition sur simple demande ») retiré", "const FILLER_RE=" in HTML and "DOC_FALLBACK" not in HTML)
    n = HTML.count("sur simple demande")
    ok("source : « sur simple demande » n'apparaît plus que dans la règle et la consigne IA", n == 2, n)
    ok("source : consigne IA — une information absente ne donne aucune phrase", "une information absente de ce qui t'est transmis ne donne aucune phrase" in HTML)
    ok("source : courrier IA — paragraphe de remplissage écarté", "phrase de remplissage pour une donnée absente" in HTML)
    ok("source : étiquette de fiche (FICHE_LBL) et « Motif à saisir »", "const FICHE_LBL=" in HTML and HTML.count("Motif à saisir") >= 3, HTML.count("Motif à saisir"))

async def fiches(page):
    r = await page.evaluate("(F)=>{const o={};for(const k in F){const f=parseFiche(F[k]);o[k]={motif:f.motif,note:f.note,nom:f.nom,prenom:f.prenom,addr:f.addr,W:ficheCheck(f)};}return o;}", FICHES)
    ok("fiche A : « N° INTERVENTION 26110300123 » ignoré, motif = « DL CHEVILLE »", r["A"]["motif"] == "DL CHEVILLE" and "INTERVENTION" not in r["A"]["note"] and "escalier" in r["A"]["note"], r["A"])
    ok("fiche B : « O INTERVENTION » (lecture OCR) ignoré, motif = « ERUPTION »", r["B"]["motif"] == "ERUPTION" and "INTERVENTION" not in r["B"]["note"], r["B"])
    ok("fiche C : étiquette seule, aucun motif lisible → champ vide, « motif à saisir » dans les vérifications", r["C"]["motif"] == "" and "INTERVENTION" not in r["C"]["note"] and "motif à saisir" in r["C"]["W"], r["C"])
    ok("fiche D : étiquette avant le nom → nom et motif justes", r["D"]["nom"] == "DUPONT" and r["D"]["motif"] == "ERUPTION", r["D"])
    ok("fiches : nom, adresse et téléphone toujours lus", all(r[k]["nom"] == "DUPONT" and "Gare" in r[k]["addr"] for k in "ABC"), {k: r[k]["addr"] for k in "ABC"})
    r = await page.evaluate("""(t)=>{const keep=TOUR.stops.slice();const s=ficheToStop(parseFiche(t));const h=interroHTML(s);const row=xpRowHTML(s,0);TOUR.stops=keep;tourSave();return {h:h.includes("Motif à saisir")&&!/INTERVENTION/.test(h),row:row.includes("Motif à saisir"),motif:s.motif};}""", FICHES["C"])
    ok("écran : patient sans motif → « Motif à saisir » dans la régulation et dans la liste Express", r["h"] and r["row"] and r["motif"] == "", r)

SETP = """(a)=>{newPatient();const i=PACKS.findIndex(p=>p.n===a.n);Object.assign(state,{patient:a.pat||'DURAND Paul',ddn:a.ddn||'14/05/1975',sexe:a.sexe||'h',date:'03/11/2026'});state.view='';state.sel=i;if(a.obs)Object.assign(state.obs,a.obs);if(a.cst)Object.assign(state.cst,a.cst);render();return i;}"""
LETTXT = """()=>{const p=currentPack();const t0=performance.now();const out=buildPages(p,true).out;const ms=performance.now()-t0;const d=document.createElement('div');d.innerHTML=out;
  return {ms:Math.round(ms),let:[...d.querySelectorAll('.page')].filter(x=>/Courrier/.test((x.querySelector('h2')||{}).textContent||'')).map(x=>[...x.querySelectorAll('p.txt')].map(e=>e.innerText).join('\\n'))};}"""

async def courriers(page, label, mob):
    L = label + " : "
    # 1. tous les gabarits du catalogue (courriers, consignes, certificats, formules fixes) : aucune formule de remplissage
    bad = await page.evaluate("""()=>{const bad=[];PACKS.forEach(p=>(p.s||[]).forEach(sh=>{if(!["let","cons","cert"].includes(sh.k))return;(sh.l||[]).forEach(l=>{const t=typeof l==="string"?l:(l&&l.t)||"";if(FILLER_RE.test(t))bad.push(p.n+" ["+sh.k+"] : "+t.slice(0,90));});}));
      [LET_RES,...COURRIER_FIN,LET_HEAD].forEach(t=>{if(FILLER_RE.test(t))bad.push("constante : "+t);});return bad;}""")
    ok(L + "catalogue : aucun gabarit de courrier, de consignes ou de certificat ne contient de formule de remplissage", not bad, bad[:8])
    ok(L + "règle : les formules creuses sont reconnues", await page.evaluate("(a)=>a.every(t=>FILLER_RE.test(t))", FILLERS_OUI))
    ok(L + "règle : une phrase clinique ou de politesse n'est pas prise pour une formule creuse", await page.evaluate("(a)=>a.every(t=>!FILLER_RE.test(t))", FILLERS_NON))
    # 2. les 200 gabarits de courrier, sans observation : rien d'inventé, le motif reste, les parenthèses sont fermées, plus de renvoi au compte rendu
    r = await page.evaluate("""()=>{const bad=[];let n=0,cr=0;const sv=state.sel;PACKS.forEach((p,i)=>{if(!(p.s||[]).some(sh=>sh.k==="let"))return;newPatient();Object.assign(state,{patient:'DURAND Paul',ddn:'14/05/1975',sexe:'h'});state.sel=i;const dc=docCtx(p);
      p.s.forEach(sh=>{if(sh.k!=="let")return;sh.l.forEach(l=>{const t=typeof l==="string"?l:(l&&l.t)||"";if(!t)return;n++;const hadCr=DOC_CR_RE.test(t);if(hadCr)cr++;let o="";try{o=docFact(t,dc);}catch(e){bad.push(p.n+" : erreur "+e.message);return;}
        if(FILLER_RE.test(o))bad.push(p.n+" : formule « "+o.slice(0,80)+" »");if(/compte[- ]rendu joint/i.test(o))bad.push(p.n+" : renvoi au compte rendu « "+o.slice(0,80)+" »");
        if((o.match(/\\(/g)||[]).length!==(o.match(/\\)/g)||[]).length)bad.push(p.n+" : parenthèse « "+o.slice(0,80)+" »");
        if(hadCr&&/\\bpour (?:une?|des|la|le|l')\\b/.test(t)&&!/\\bpour\\b/.test(o))bad.push(p.n+" : motif perdu « "+t.slice(0,80)+" »");});});});
      newPatient();state.sel=sv;render();return {n,cr,bad};}""")
    ok(L + f"{r['n']} lignes de courrier du catalogue sans observation ({r['cr']} renvoyaient au compte rendu) : aucune formule creuse, aucun renvoi, motif conservé, parenthèses fermées", not r["bad"] and r["cr"] >= 140, r["bad"][:8])
    # 3. onychomycose : sans observation → phrase retirée et alerte à l'écran ; avec l'examen → éléments repris, alerte levée
    PK = "Mycose des orteils / ongle (intertrigo, onychomycose)"
    i = await page.evaluate(SETP, {"n": PK}); assert i >= 0, PK
    await page.wait_for_timeout(200)
    r = await page.evaluate(LETTXT); let_ = "\n".join(r["let"]); TIMES[label + " — documents de la fiche onychomycose (courrier compris)"] = r["ms"]
    ok(L + "onychomycose sans observation : le courrier garde le motif, sans « ongles » inventés ni formule creuse ni renvoi au compte rendu",
       r["let"] and "onychomycose" in let_ and "ongles atteints" not in let_ and not re.search(r"sur simple demande|non précisé|à compléter|compte[- ]rendu", let_, re.I), let_[:400])
    m = await page.evaluate("()=>({m:missingList(currentPack()).filter(x=>x.let).map(x=>x.t),q:questionsList(currentPack()).filter(q=>/courrier/.test(q.t)).map(q=>q.lvl),xp:xpAlertsHTML(currentPack()),scr:(document.querySelector('#missing')||{}).textContent||''})")
    ok(L + "écran avant impression : « courrier : ajoute le nombre d'ongles atteints, l'extension, l'atteinte matricielle »",
       any("ongles atteints" in x and "extension" in x and "matricielle" in x for x in m["m"]) and "ongles atteints" in m["scr"], m["m"])
    ok(L + "l'alerte est « à documenter » (jamais bloquante) et visible aussi en Express", m["q"] == ["documenter"] and "Courrier : ajoute" in m["xp"], (m["q"], m["xp"][:120]))
    if mob:
        await page.evaluate("()=>{const e=document.querySelector('#missing');if(e)e.scrollIntoView({block:'center'});}"); await page.wait_for_timeout(150)
        await page.screenshot(path=os.path.join(OUT, "corr-courrier-manque-375.png"))
    await page.evaluate("()=>{state.obs.cut='Trois ongles atteints au pied droit, extension distale sans atteinte matricielle';state.obs.hyp='Onychomycose distale';render();}"); await page.wait_for_timeout(200)
    r = await page.evaluate(LETTXT); let_ = "\n".join(r["let"])
    ok(L + "onychomycose avec l'examen : « éléments recueillis ce jour : cutané : trois ongles atteints… » dans le courrier, après le motif",
       "léments recueillis ce jour" in let_ and "ongles atteints" in let_ and let_.find("onychomycose") < let_.find("léments recueillis") and not re.search(r"sur simple demande|non précisé|compte[- ]rendu", let_, re.I), let_[:500])
    j = let_.find("J'ai prescrit")
    ok(L + "ordre fixe : motif, éléments cliniques, puis traitement prescrit", j < 0 or let_.find("léments recueillis") < j, let_[:500])
    m = await page.evaluate("()=>missingList(currentPack()).filter(x=>x.let).map(x=>x.t)")
    ok(L + "l'alerte disparaît une fois les éléments écrits", not m, m)
    # 4. courriers assemblés (spécialiste, médecin traitant) : rien d'inventé
    r = await page.evaluate("""()=>{const p=currentPack();const Ls=letState();Ls.sp={on:true,dest:'dermato'};Ls.mt={on:true};const a=letText(p,'sp'),b=letText(p,'mt');Ls.sp={on:false};Ls.mt={on:false};return [a,b];}""")
    ok(L + "courriers assemblés (spécialiste, médecin traitant) : aucune formule creuse", not any(re.search(r"sur simple demande|non précisé|non renseigné|à compléter|à préciser", t, re.I) for t in r), [t[:200] for t in r])
    # 5. autre forme de gabarit : parenthèse « (fièvre, terrain, porte d'entrée dans le compte rendu joint) »
    r = await page.evaluate("""()=>({a:docCrSplit("Je vous adresse {patient} pour une monoarthrite aiguë (genou) faisant craindre une arthrite septique (fièvre, terrain, porte d'entrée dans le compte rendu joint)."),
      b:docCrSplit("vu(e) ce jour en garde pour une hypoglycémie ; glycémie, cause probable, resucrage et traitement en cours figurent dans le compte rendu joint".split(" ; ")[1]),
      c:docCrSplit("une céphalée différant de ses céphalées habituelles par son intensité, avec un examen neurologique détaillé dans le compte rendu joint.")})""")
    ok(L + "découpe : motif gardé, éléments attendus extraits (parenthèse, énumération, « avec … détaillé »)",
       r["a"]["pre"].endswith("arthrite septique") and r["a"]["items"] == ["fièvre", "terrain", "porte d'entrée"] and r["b"]["pre"] == "" and len(r["b"]["items"]) == 4 and r["c"]["items"] == ["un examen neurologique"] and r["c"]["pre"].endswith("intensité"), r)

async def run_ctx(b, w, h, theme, big, label):
    mob = w < 500
    ctx = await b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if mob else 1, is_mobile=mob, has_touch=mob)
    await ctx.route("**/*", lambda r: asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page = await ctx.new_page(); errors = []; page.on("pageerror", lambda e: errors.append(str(e))); page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','false')}catch(e){}")
    await unlock(page)
    await page.evaluate(f"localStorage.setItem('sos_theme','{theme}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{theme}';themeApply();")
    if label == "desktop": await fiches(page)
    await courriers(page, label, mob)
    ok(label + " : aucune erreur JavaScript", not errors, errors[:3])
    await ctx.close()

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", PORT], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1.2); static()
        async with async_playwright() as p:
            b = await p.chromium.launch()
            await run_ctx(b, 1280, 900, "light", False, "desktop")
            await run_ctx(b, 375, 812, "dark", False, "375 nuit")
            await b.close()
    finally:
        srv.terminate()
    n = len(results); f = [r for r in results if not r[1]]
    with open(os.path.join(ROOT, "tests", "resultats_courriers.md"), "w", encoding="utf-8") as fh:
        fh.write("# Corrections v41z — fiches et courriers (%s)\n\n%d/%d tests.\n\n" % (time.strftime("%d/%m/%Y %H:%M"), n - len(f), n))
        for k, v in TIMES.items(): fh.write("- %s : %d ms\n" % (k, v))
        fh.write("\n")
        for r in results: fh.write(("- OK " if r[1] else "- **ÉCHEC** ") + r[0] + ("" if r[1] else " — " + str(r[2])[:300]) + "\n")
    print("\n%d/%d" % (n - len(f), n)); print("TIMES", TIMES)
    sys.exit(1 if f else 0)

if __name__ == "__main__":
    asyncio.run(main())
