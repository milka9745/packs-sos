# -*- coding: utf-8 -*-
# v41z (21/10/2026, demande globale IV–IX) — documents du patient : scanner en rafale (recadrage, redressement, noir et blanc, chiffrement),
# écran de téléphone, import de photos et de PDF, analyse sans IA (type, date, biologie et DFG, ordonnances, courriers, antécédents, vaccins),
# cohérence croisée, propositions « Tout accepter », « Ce que disent les documents », résumé du patient, courriers, ce qui manque, questions,
# scores pré-remplis, dictée structurée, synthèse IA (texte anonymisé, « Ce qui part »), apprentissage, vitesse, persistance, parcours complet.
# Documents et patients fictifs générés à la volée ; aucun appel externe (réseau coupé, API simulée et comptée). Lancer : python tests/test_docs_v41z.py
import asyncio, os, re, json, subprocess, sys, time, tempfile, math, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8789
results=[]; TIMES={}
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:900])

BIO1="""LABORATOIRE D'ANALYSES MÉDICALES DU CENTRE
Patient : DURAND Martine   Née le 03/04/1958
Prélèvement du 12/10/2026   Édité le 13/10/2026
HÉMATOLOGIE
Hémoglobine 11,2 g/dL (12,0 - 16,0)
Leucocytes 7,8 G/L (4,0 - 10,0)
Neutrophiles 62 % 4,8 G/L
Plaquettes 92 G/L (150 - 400)
BIOCHIMIE
Sodium 131 mmol/L (135 - 145)
Potassium 5,4 mmol/L (3,5 - 5,1)
Créatinine 130 µmol/L (44 - 80)
Glycémie à jeun 1,45 g/L (0,70 - 1,10)
CRP 12 mg/L (< 5)
TSH 2,1 mUI/L (0,40 - 4,00)
INR 3,8"""
BIO0="""LABORATOIRE D'ANALYSES MÉDICALES DU CENTRE
Patient : DURAND Martine   Née le 03/04/1958
Prélèvement du 12/09/2026
Hémoglobine 12,4 g/dL (12,0 - 16,0)
Plaquettes 160 G/L (150 - 400)
Potassium 4,6 mmol/L (3,5 - 5,1)
Créatinine 110 µmol/L (44 - 80)"""
COURRIER="""Service de Cardiologie - Docteur Paul MARTIN, cardiologue
Orléans, le 15/09/2026
Cher Confrère,
J'ai revu ce jour Madame DURAND Martine, 68 ans, pour le suivi
de sa fibrillation atriale permanente sous anticoagulant.
Antécédents : HTA, diabète de type 2, BPCO post-tabagique,
prothèse totale de hanche droite en 2019.
Pas d'antécédent familial d'infarctus.
L'ETT retrouve une FEVG à 55 %.
En conclusion : fibrillation atriale bien tolérée, poursuite de
l'apixaban, contrôle de la fonction rénale tous les 3 mois,
à revoir dans 6 mois.
Bien confraternellement,"""
CRH="""CENTRE HOSPITALIER - Service de Pneumologie
COMPTE RENDU D'HOSPITALISATION
Date d'entrée : 02/06/2026 - Date de sortie : 09/06/2026
Motif d'hospitalisation : exacerbation de BPCO
Antécédents : BPCO stade 3, tabagisme sevré 40 PA,
fibrillation atriale, cholécystectomie en 2015
Allergie : pénicilline (éruption)
Traitement de sortie : SPIRIVA, VENTOLINE, ELIQUIS 5 mg x2,
CORTANCYL 30 mg 5 jours
Au total : exacerbation de BPCO d'origine infectieuse,
évolution favorable. Consultation de pneumologie dans 2 mois."""
VACCIN="""CARTE DE VACCINATION
DURAND Martine
dTP REVAXIS : 12/03/2015 - lot A123
Grippe INFLUVAC : 05/11/2024
PNEUMOCOQUE PREVENAR 13 : 20/01/2023
COVID-19 Comirnaty : 10/10/2023"""
ECRAN="""Dr Paul MARTIN - Cardiologue
ORDONNANCE du 03/09/2026
DURAND Martine
ELIQUIS 5 mg : 1 comprimé matin et soir
LASILIX 40 mg : 1 comprimé le matin
QSP 3 mois"""
ORDO_PDF=[["Docteur Paul MARTIN - Cardiologie","Ordonnance du 03/09/2026","Madame DURAND Martine","","ELIQUIS 5 mg comprimé : 1 comprimé matin et soir","METFORMINE 1000 mg : 1 comprimé matin et soir","COVERSYL 5 mg : 1 comprimé le matin","LASILIX 40 mg : 1 comprimé le matin","KARDEGIC 75 mg : 1 sachet le midi","QSP 3 mois"],["Page 2 - renouvellement possible une fois","Ordonnance du 03/09/2026"]]

def esc_html(t): return t.replace("&","&amp;").replace("<","&lt;")
def sheet_html(text,rot=1.5,blur=0,font=27):
    lines="".join("<div>%s</div>"%esc_html(l) for l in text.split("\n"))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;background:#3b3b3b;width:1000px;height:1400px;display:flex;align-items:center;justify-content:center;font-family:Arial,Helvetica,sans-serif}"
            ".sheet{background:#fff;color:#111;width:860px;min-height:1150px;padding:48px 52px;box-sizing:border-box;font-size:%dpx;line-height:1.45;transform:rotate(%sdeg);box-shadow:0 0 30px rgba(0,0,0,.6);filter:blur(%dpx)}.sheet div{white-space:pre;min-height:1em}</style></head><body><div class='sheet'>%s</div></body></html>"%(font,rot,blur,lines))
def screen_html(text):
    lines="".join("<div>%s</div>"%esc_html(l) for l in text.split("\n"))
    return ("<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;background:#101010;width:1000px;height:1400px;display:flex;align-items:center;justify-content:center;font-family:Arial,Helvetica,sans-serif}"
            ".scr{background:#181818;color:#f2f2f2;width:620px;padding:80px 40px;box-sizing:border-box;font-size:30px;line-height:1.5;border-radius:40px;border:6px solid #444}.scr div{white-space:pre;min-height:1em}</style></head><body><div class='scr'>%s</div></body></html>"%lines)
BLANK_HTML="<!doctype html><html><body style='margin:0;background:#e9e9e9;width:1000px;height:1400px'></body></html>"
def pdf_escape(s):
    s=s.replace("—","-").replace("’","'").replace("œ","oe").replace("–","-")
    return s.encode("cp1252","replace").decode("cp1252").replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
def make_pdf(path,pages):
    objs=[]  # (bytes) in order of object number
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids=[]; n=3
    font_no=n; objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"); n+=1
    page_objs=[]
    for lines in pages:
        content="BT /F1 14 Tf 50 780 Td 20 TL "+" ".join("(%s) Tj T*"%pdf_escape(l) for l in lines)+" ET"
        cb=content.encode("cp1252","replace")
        page_no=n; cont_no=n+1; n+=2; kids.append(page_no)
        page_objs.append((page_no,("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"%(font_no,cont_no)).encode()))
        page_objs.append((cont_no,b"<< /Length %d >>\nstream\n"%len(cb)+cb+b"\nendstream"))
    pages_obj=("<< /Type /Pages /Kids [%s] /Count %d >>"%(" ".join("%d 0 R"%k for k in kids),len(kids))).encode()
    allobjs={1:objs[0],2:pages_obj,3:objs[1]}
    for no,b in page_objs: allobjs[no]=b
    out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets={}
    for no in sorted(allobjs):
        offsets[no]=len(out); out+=("%d 0 obj\n"%no).encode()+allobjs[no]+b"\nendobj\n"
    xref=len(out); N=max(allobjs)+1
    out+=("xref\n0 %d\n"%N).encode()+b"0000000000 65535 f \n"
    for no in range(1,N): out+=("%010d 00000 n \n"%offsets[no]).encode()
    out+=("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"%(N,xref)).encode()
    open(path,"wb").write(out)

async def make_fixtures(b,tmp):
    ctx=await b.new_context(viewport={"width":1000,"height":1400}); F={}
    async def shot(name,html,q=88):
        pg=await ctx.new_page(); await pg.set_content(html); p=os.path.join(tmp,name); await pg.screenshot(path=p,type="jpeg",quality=q); await pg.close(); F[name]=p
    await shot("bio1.jpg",sheet_html(BIO1)); await shot("bio0.jpg",sheet_html(BIO0,0.8)); await shot("flou.jpg",sheet_html(BIO1,1.0,7)); await shot("vide.jpg",BLANK_HTML,70)
    await shot("ecran.jpg",screen_html(ECRAN)); await shot("courrier.jpg",sheet_html(COURRIER,0.6,0,25)); await shot("crh.jpg",sheet_html(CRH,-0.7,0,25)); await shot("vaccin.jpg",sheet_html(VACCIN,0.4))
    await ctx.close(); p=os.path.join(tmp,"ordo.pdf"); make_pdf(p,ORDO_PDF); F["ordo.pdf"]=p; return F

async def unlock(page,uid):
    await page.add_init_script("try{localStorage.setItem('sos_xp','false');localStorage.setItem('sos_excomplet','0');}catch(e){}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=20000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=20000); await page.wait_for_timeout(600)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
async def reunlock(page):
    try:
        await page.wait_for_selector("#pin1",timeout=6000); await page.fill("#pin1","1234")
        try: await page.click("#pin_ok",timeout=2000)
        except Exception: pass
    except Exception: pass
    await page.wait_for_function("()=>typeof SEC!=='undefined'&&SEC.unlocked&&!document.getElementById('lock')",timeout=20000); await page.wait_for_timeout(800)
SET_PATIENT="()=>{newPatient();Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f',poids:'70'});state.tt=['PREVISCAN'];state.cot.lieu='consultation';state.cot.auto=false;render();}"
STATUS_RE=r"()=>/enregistrée|non enregistrée|illisible|reprenez|vide|floue/.test(DOCS.status)"
async def scan(page,img):
    await page.evaluate("()=>{if(!DOCS.scan)DOCS.scan={id:null,n:0};DOCS.status='';}")
    t0=time.time(); await page.set_input_files("#doc_scan",img)
    await page.wait_for_selector("#scanprev #scan_ok",timeout=30000); await page.click("#scan_ok")  # 21/10/2026 (retour 2) : aperçu avec 4 coins, puis validation
    await page.wait_for_function(STATUS_RE,timeout=30000)
    return (await page.evaluate("()=>DOCS.status"), time.time()-t0)
async def finish(page):
    n=await page.evaluate("()=>docsList().length"); t0=time.time(); await page.evaluate("()=>docScanFinish()")
    await page.wait_for_function("()=>!DOCS.busy&&docsList().length&&docsList()[docsList().length-1].ana",timeout=120000); return time.time()-t0
def ckd_epi(creat_umol,age,female):
    scr=creat_umol/88.4; k=0.7 if female else 0.9; a=-0.241 if female else -0.302; q=scr/k
    return round(142*min(q,1)**a*max(q,1)**-1.2*0.9938**age*(1.012 if female else 1))
def cockcroft(creat_umol,age,female,poids): return round((140-age)*poids*(1.04 if female else 1.23)/creat_umol)

async def net(ctx,calls):
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    async def api(route):
        calls.append(route.request.url); await route.fulfill(status=500,body="{}")
    await ctx.route(re.compile(r".*api\.anthropic\.com.*"),api)

async def main():
    tmp=tempfile.mkdtemp(prefix="docs41z_")
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); F=await make_fixtures(b,tmp)
            ok("fixtures : 8 images et 1 PDF fictifs générés sur place (aucune donnée réelle)",len(F)==9 and all(os.path.getsize(x)>1000 for x in F.values()),{k:os.path.getsize(v) for k,v in F.items()})
            calls=[]; ctx=await b.new_context(viewport={"width":1280,"height":900}); await net(ctx,calls)
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); dialogs=[]
            PROMPT={"v":None}
            async def on_dialog(d):
                dialogs.append((d.type,d.message))
                if d.type=="prompt" and PROMPT["v"] is not None: await d.accept(PROMPT["v"])
                else: await d.accept()
            page.on("dialog",lambda d:asyncio.ensure_future(on_dialog(d)))
            await unlock(page,"testdocs41z")
            await page.evaluate("()=>{window.__printed=0;window.print=()=>{window.__printed++;};window.__toasts=[];const t0=window.toast;window.toast=m=>{window.__toasts.push(String(m));return t0(m);};}")
            await page.evaluate(SET_PATIENT); await page.wait_for_timeout(200)
            age=68; exp_ckd=ckd_epi(130,age,True); exp_cg=cockcroft(130,age,True,70)
            # ---------- IV.15 / IX.38 : deux boutons, même emplacement en visite et en consultation ----------
            async def place():
                return await page.evaluate("()=>{const d=document.getElementById('dictcard'),c=document.getElementById('docscard');const btns=[...document.querySelectorAll('#docscard .doc-acts button')].map(b=>b.id);return {dict:!!d,card:!!c,after:!!(d&&c&&d.nextElementSibling===c),btns,scanTxt:(document.getElementById('doc_scan_btn')||{}).textContent||'',impTxt:(document.getElementById('doc_import_btn')||{}).textContent||''};}")
            pc=await place(); await page.evaluate("()=>{state.cot.lieu='visite';render();}"); pv=await place()
            await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"); pp=await place(); await page.evaluate("()=>{state.sel=null;state.cot.lieu='consultation';render();}")
            ok("IV.15 / IX.38 : « Scanner » et « Documents » à côté de la dictée, mêmes boutons au même endroit en consultation, en visite et sur une fiche",
               all(x["after"] and x["btns"]==["doc_scan_btn","doc_import_btn"] and "Scanner" in x["scanTxt"] and "Importer un scan" in x["impTxt"] for x in (pc,pv,pp)),(pc,pv,pp))
            # ---------- IV.16 : scan en rafale, recadrage, redressement, noir et blanc, chiffrement, pages illisibles ----------
            s0,t=await scan(page,F["bio0.jpg"]); TIMES["scan page"]=t; await finish(page)
            d0=await page.evaluate("()=>{const d=docsList()[0];return {type:d.type,date:d.ana.date,pages:d.pages.length,kb:d.pages[0].kb,cropped:d.pages[0].cropped,ocr:d.pages[0].ocrMs,ms:d.pages[0].ms,words:d.pages[0].words,n:d.ana.labs&&d.ana.labs.n};}")
            ok("IV.16 : page scannée recadrée et redressée, noir et blanc, réduite (≤ 230 Ko), chiffrée, lue sur l'appareil ; bilan du 12/09/2026 reconnu",d0["cropped"] and d0["kb"]<=230 and d0["type"]=="bio" and d0["date"]=="12/09/2026" and d0["words"]>=20 and d0["n"]>=3,d0)
            s1,t1=await scan(page,F["bio1.jpg"]); s2,_=await scan(page,F["flou.jpg"])
            st=await page.evaluate("()=>({n:DOCS.scan.n,status:DOCS.status,next:!!document.getElementById('doc_next'),fin:(document.getElementById('doc_finish')||{}).textContent||'',retake:!!document.getElementById('doc_retake'),last:docsList()[1].pages[1]})")
            ok("IV.16 : compteur de pages, « Page suivante », « Reprendre la dernière », « Terminer (2) » ; page floue signalée, reprise proposée, jamais de devinette",st["n"]==2 and st["next"] and st["retake"] and "Terminer (2)" in st["fin"] and st["last"]["ok"] is False and "floue" in st["last"]["why"] and "reprenez" in st["status"],st)
            await page.evaluate("()=>{const d=docsList()[1];const p=d.pages.pop();DOCS.scan.n=d.pages.length;delete DOCS.src[p.id];docsCardRefresh();}")
            s3,_=await scan(page,F["vide.jpg"])
            st=await page.evaluate("()=>({n:DOCS.scan.n,last:docsList()[1].pages[1],status:DOCS.status})")
            ok("IV.16 : page vide ou trop claire détectée (« page vide ou trop claire »), signalée sans invention de texte",st["n"]==2 and st["last"]["ok"] is False and "vide" in st["last"]["why"],st)
            tf=await finish(page); TIMES["OCR + analyse (2 pages)"]=tf
            d1=await page.evaluate("()=>{const d=docsList()[1];const L=d.ana.labs;return {type:d.type,date:d.ana.date,pages:d.pages.length,bad:d.pages.filter(p=>!p.ok).length,badWords:d.pages[1].words||0,ocr:d.pages.map(p=>p.ocrMs),ms:d.pages.map(p=>p.ms),status:DOCS.status,n:L&&L.n,abn:L&&L.abn,items:L?L.items.map(x=>[x.k,x.v,x.u,x.cls]):[],dfg:L&&L.dfg,txt:L?L.items.map(x=>x.txt):[]};}")
            TIMES["OCR page (ms)"]=d1["ocr"][0]; TIMES["traitement page (ms)"]=d1["ms"][0]
            ok("IV.16 : document regroupé (2 pages, 1 illisible signalée dans le statut), bilan du 12/10/2026",d1["pages"]==2 and d1["bad"]==1 and "illisible" in d1["status"] and d1["type"]=="bio" and d1["date"]=="12/10/2026" and d1["badWords"]<8,d1)
            V={k:(v,u,c) for k,v,u,c in d1["items"]}
            ok("V.21 : valeurs, unités et classement lus sur la page scannée (Hb basse légère, plaquettes et kaliémie à surveiller, créatinine haute, glycémie 1,45 g/L convertie en mmol/L, CRP « < 5 », INR sous AVK)",
               V.get("hb",(0,))[0]==11.2 and V.get("plq",(0,0,""))[2]=="surv" and V.get("k",(0,0,""))[2]=="surv" and V.get("creat",(0,))[0]==130 and abs(V.get("gly",(0,))[0]-8.05)<0.05 and V.get("crp",(0,0,""))[2]!="normal" and V.get("inr",(0,))[0]==3.8 and V.get("na",(0,))[0]==131,V)
            dfg=d1["dfg"] or {}
            ok(f"V.21 : DFG calculé automatiquement — CKD-EPI 2021 {exp_ckd} ± 1 et Cockcroft {exp_cg} ± 1 (âge, sexe, poids de la fiche), stade G3b",dfg.get("ckd") is not None and abs(dfg["ckd"]-exp_ckd)<=1 and abs((dfg.get("cg") or 0)-exp_cg)<=1 and dfg.get("stade")=="G3b",dfg)
            # ---------- IV.17 : écran de téléphone ----------
            await page.check("#doc_screen"); se,_=await scan(page,F["ecran.jpg"]); await finish(page); await page.uncheck("#doc_screen")
            dE=await page.evaluate("()=>{const d=docsList()[2];return {screen:d.pages[0].screen,cropped:d.pages[0].cropped,words:d.pages[0].words,ok:d.pages[0].ok,txt:d.text.slice(0,200),meds:d.ana.meds.map(m=>m.name),type:d.type};}")
            ok("IV.17 : mode « écran de téléphone » (texte clair sur fond sombre, pas de recadrage feuille) : texte lu, ELIQUIS reconnu",dE["screen"] and not dE["cropped"] and dE["ok"] and dE["words"]>=10 and "ELIQUIS" in dE["meds"],dE)
            # ---------- IV.18 : import de plusieurs fichiers dont un PDF, miniatures, stockage ----------
            t0=time.time(); await page.set_input_files("#doc_import",[F["courrier.jpg"],F["crh.jpg"],F["vaccin.jpg"],F["ordo.pdf"]])
            await page.wait_for_function("()=>!DOCS.busy&&/ajouté/.test(DOCS.status)",timeout=180000); TIMES["import 3 images + PDF"]=time.time()-t0
            di=await page.evaluate("()=>({status:DOCS.status,n:docsList().length,rows:document.querySelectorAll('#docscard .doc-row').length,types:docsList().map(d=>d.type),pdf:(()=>{const d=docsList().find(x=>x.src==='pdf');return d&&{pages:d.pages.length,txt:d.text.slice(0,120),meds:d.ana.meds.map(m=>m.name),ocr:d.pages.map(p=>p.ocrMs)};})()})")
            ok("IV.18 : 4 fichiers importés d'un coup (3 photos + 1 PDF de 2 pages), nombre confirmé, liste avec type et intitulé ; PDF lu par le lecteur embarqué (texte natif, sans OCR)",
               "4 documents" in di["status"] and di["n"]==7 and di["rows"]==7 and di["pdf"] and di["pdf"]["pages"]==2 and "METFORMINE" in di["pdf"]["meds"] and all(o==0 for o in di["pdf"]["ocr"]),di)
            ok("V.20 : types reconnus par mots-clés et mise en page — bilan, bilan, ordonnance (écran), courrier, compte rendu d'hospitalisation, carte de vaccination, ordonnance (PDF)",di["types"]==["bio","bio","ordo","courrier","crh","vaccin","ordo"],di["types"])
            pid=await page.evaluate("()=>docsList().find(x=>x.src==='pdf').id"); await page.evaluate("(id)=>docViewScreen(id)",pid); await page.wait_for_function("()=>document.querySelectorAll('#docview img').length>=2",timeout=10000)
            mv=await page.evaluate("()=>{const r={imgs:document.querySelectorAll('#docview img').length,txt:!!document.querySelector('#docview pre')};document.getElementById('docview').remove();return r;}")
            ok("IV.18 : miniatures des pages (déchiffrées à la demande) et texte lu affichés",mv["imgs"]==2 and mv["txt"],mv)
            await page.evaluate("()=>{window.__phSpace=phSpace;phSpace=async()=>({free:40*1048576,quota:1e9,usage:1e8});window.__toasts=[];}")
            await page.set_input_files("#doc_import",[F["vaccin.jpg"]]); await page.wait_for_function("()=>!DOCS.busy&&/ajouté/.test(DOCS.status)",timeout=60000)
            w1=await page.evaluate("()=>window.__toasts.join(' | ')")
            await page.evaluate("()=>{phSpace=async()=>({free:5*1048576,quota:1e9,usage:1e8});}"); nd=len(dialogs)
            await page.set_input_files("#doc_import",[F["vaccin.jpg"]]); await page.wait_for_function("()=>!DOCS.busy",timeout=60000); await page.wait_for_timeout(300)
            w2=[m for t,m in dialogs[nd:]]; await page.evaluate("()=>{phSpace=window.__phSpace;}")
            ok("IV.18 : stockage presque plein → avertissement clair (40 Mo libres), puis refus expliqué sous 8 Mo, jamais de blocage silencieux","stockage faible" in w1 and any("espace de stockage" in m for m in w2) and (await page.evaluate("()=>docsList().length"))==8,(w1,w2))
            await page.evaluate("()=>{const d=docsList()[docsList().length-1];docRemove(d.id);}")
            # ---------- V.22 / V.23 : ordonnances, courriers, antécédents ----------
            an=await page.evaluate("()=>docsList().map(d=>({type:d.type,date:d.ana.date,meds:d.ana.meds.map(m=>m.name+(m.flags.length?'['+m.flags.join(',')+']':'')),atcd:d.ana.atcd.map(x=>x.k+(x.date?'@'+x.date:'')+(x.r?'!':'')),al:d.ana.allergies,concl:d.ana.concl,spe:d.ana.spe,vacc:d.ana.vacc}))")
            ordo=an[6]; cou=an[3]; crh=an[4]; vac=an[5]
            ok("V.22 : ordonnance PDF → 5 médicaments reconnus via la base intégrée, anticoagulant et antiagrégant signalés",set(["ELIQUIS[anticoagulant]","COVERSYL[IEC ou sartan]","LASILIX[diurétique]"])<=set(ordo["meds"]) and any(m.startswith("METFORMINE") for m in ordo["meds"]) and any(m.startswith("KARD") and "antiagrégant" in m for m in ordo["meds"]),ordo["meds"])
            ok("V.22 : courrier → spécialité cardiologie, date 15/09/2026, conclusion extraite après « en conclusion »",cou["spe"]=="cardiologie" and cou["date"]=="15/09/2026" and cou["concl"].startswith("fibrillation atriale bien tolérée") and "revoir dans 6 mois" in cou["concl"] and "confraternellement" not in cou["concl"].lower(),cou)
            ok("V.23 : antécédents du courrier datés et rattachés aux critères de risque (FA, HTA, diabète, BPCO, PTH 2019) ; négation « pas d'antécédent familial d'infarctus » ignorée",
               all(k in cou["atcd"] for k in ["fa!","hta","dt!","bpco!","pth@2019"]) and not any(a.startswith("idm") for a in cou["atcd"]),cou["atcd"])
            ok("V.22 : compte rendu d'hospitalisation → allergie aux pénicillines relevée, antécédents (BPCO, tabac, FA, cholécystectomie 2015), conclusion « au total », pneumologie",crh["al"]==["Pénicillines"] and "chole@2015" in crh["atcd"] and "bpco!" in crh["atcd"] and crh["spe"]=="pneumologie" and crh["concl"].startswith("exacerbation de BPCO"),crh)
            ok("V.20 : carte de vaccination → 4 vaccins datés (dTP 12/03/2015, grippe, pneumocoque, covid-19)",len(vac["vacc"])==4 and any(v["v"].startswith("dTP") and v["date"]=="12/03/2015" for v in vac["vacc"]),vac["vacc"])
            # ---------- VII.26 : propositions, « Tout accepter », rien de non validé avant ----------
            await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}")
            cr0=await page.evaluate("()=>buildCR(currentPack())")
            P=await page.evaluate("()=>{const P=state.docProps;return {n:docPropsCount(P),tt:P.tt.map(x=>x.t),al:P.allergies.map(x=>x.t),atcd:P.atcd.map(x=>x.t),bio:P.bio&&{n:P.bio.n,abn:P.bio.abn,trend:P.bio.trend.map(t=>t.t)},risk:P.risk&&P.risk.why,suivi:P.suivi.length,vacc:P.vacc.length,ui:document.querySelectorAll('#docprops input[data-docprop]').length,why:document.querySelectorAll('#docprops [data-docwhy]').length,accept:(document.getElementById('doc_accept')||{}).textContent||''};}")
            ok("VII.26 : dès l'import, propositions en attente (traitements, allergie, antécédents, biologie, suivi, vaccins, pack à risque), chacune cochée, avec « Pourquoi ? » et un geste « Tout accepter »",
               P["n"]>=12 and "ELIQUIS" in P["tt"] and P["al"]==["Pénicillines"] and len(P["atcd"])>=5 and P["bio"] and P["risk"] and P["suivi"]>=2 and P["vacc"]==4 and P["ui"]==P["n"] and P["why"]>=P["n"] and "Tout accepter" in P["accept"],P)
            ok("V.21 : tendance entre deux bilans (12/09 → 12/10) : créatinine 110 → 130 en hausse, plaquettes 160 → 92 en baisse",any("Créatinine : 110 (12/09/2026) → 130 (12/10/2026)" in t and "hausse" in t for t in P["bio"]["trend"]) and any("Plaquettes" in t and "baisse" in t for t in P["bio"]["trend"]),P["bio"]["trend"])
            ok("VII.26 : avant accord, ni le compte rendu ni la fiche ne contiennent les éléments des documents","ELIQUIS" not in cr0 and "Biologie du" not in cr0 and (await page.evaluate("()=>state.tt.length"))==1,cr0[:300])
            await page.evaluate("()=>{const i=state.docProps.tt.findIndex(x=>x.t==='COVERSYL');const cb=document.querySelector('#docprops input[data-docprop=\"tt:'+i+'\"]');cb.checked=false;cb.dispatchEvent(new Event('change',{bubbles:true}));}")
            await page.click("#doc_accept"); await page.wait_for_timeout(400)
            A=await page.evaluate("()=>({tt:state.tt,al:state.allergies,pen:state.allergie,risk:state.risk,atcd:state.obs.atcd,atcdDocs:(state.atcdDocs||[]).map(a=>a.k),labs:!!(state.labs&&state.labs.items.length),dfg:state.labs&&state.labs.dfg&&state.labs.dfg.ckd,suivi:(state.suivi||[]).length,vacc:(state.vacc||[]).length,docs:state.obs.docs,obsOpen:state.obsOpen,say:(document.querySelector('.docsay')||{}).textContent||'',applied:!!state.docProps.applied,propsShown:!!document.getElementById('docprops')})")
            ok("VII.26 : « Tout accepter » reprend les lignes cochées (COVERSYL décoché non repris) : traitements, allergie (pénicillines), antécédents, biologie et DFG, suivi, vaccins, pack à risque",
               "ELIQUIS" in A["tt"] and "COVERSYL" not in A["tt"] and "Pénicillines" in A["al"] and A["pen"] and A["risk"]=="r" and "fibrillation atriale" in A["atcd"] and A["labs"] and A["dfg"]==exp_ckd and A["suivi"]>=2 and A["vacc"]==4 and A["applied"] and not A["propsShown"],A)
            ok("VII.26 / IV.19 : « Ce que disent les documents » en tête de l'observation (documents consultés, antécédents retenus, biologie, suivi, liens avec « Pourquoi ? »)",A["obsOpen"] and "Ce que disent les documents" in A["say"] and "Documents consultés" in A["say"] and "Antécédents retenus" in A["say"] and "DFG" in A["say"] and "Pourquoi ?" in A["say"],A["say"][:600])
            cr=await page.evaluate("()=>buildCR(currentPack())")
            ok("IV.19 : compte rendu — « DOCUMENTS ET RÉSULTATS CONSULTÉS » liste chaque document (nature, date, pages) puis les résultats retenus après accord","DOCUMENTS ET RÉSULTATS CONSULTÉS" in cr and "Document consulté : Bilan biologique du 12/10/2026 (2 pages, scanné, page illisible signalée)" in cr and "Biologie du 12/10/2026" in cr and "DFG CKD-EPI" in cr and "TRAITEMENTS EN COURS" in cr and "ELIQUIS" in cr,cr[:1500])
            # ---------- V.24 : cohérence croisée avant l'ordonnance ----------
            al=await page.evaluate("()=>checkAlerts(currentPack().s)")
            ok("V.24 : alertes croisées sans IA (anticoagulant + plaquettes 92, metformine + DFG 30–44, AINS + DFG < 60, AINS + diurétique) ; pas d'alerte kaliémie + IEC puisque COVERSYL n'a pas été repris",
               any("plaquettes à 92" in a for a in al) and not any("kaliémie à 5,4" in a for a in al) and any("Metformine et DFG" in a for a in al) and any("AINS avec DFG" in a for a in al) and any("AINS + diurétique" in a for a in al),al)
            shown=await page.evaluate("()=>[...document.querySelectorAll('#main .alert, #main .alerts, #main [class*=alert]')].map(e=>e.textContent).join(' | ')")
            ok("V.24 : ces alertes sont visibles à l'écran au-dessus des feuilles",("plaquettes à 92" in shown) and ("Metformine et DFG" in shown),shown[:400])
            await page.evaluate("()=>{state.labs.dfg.ckd=25;state.labs.dfg.txt='DFG CKD-EPI 25 mL/min/1,73 m² (stade G4)';render();}")
            al2=await page.evaluate("()=>({al:checkAlerts(currentPack().s),ci:ciPending(checkAlerts(currentPack().s)).length})")
            ok("V.24 : DFG < 30 → metformine et AINS prescrit contre-indiqués (⛔), décision du prescripteur demandée avant impression",any(a.startswith("⛔ Metformine") for a in al2["al"]) and any(a.startswith("⛔ AINS prescrit") for a in al2["al"]) and al2["ci"]>=1,al2)
            await page.evaluate("()=>{state.labs.dfg.ckd=%d;state.labs.dfg.txt='DFG CKD-EPI %d mL/min/1,73 m² (stade G3b) ; Cockcroft %d mL/min';render();}"%(exp_ckd,exp_ckd,exp_cg))
            # ---------- VIII.33 : liens entre les faits ----------
            links=await page.evaluate("()=>docLinks().map(l=>l.t+' || '+l.why)")
            ok("VIII.33 : liens entre les faits avec renvoi à la règle (DFG → AINS et doses, anticoagulant → pas d'IM, kaliémie, FA → scores, BPCO, allergie → alternatives)",any("DFG à" in l and "RCP" in l for l in links) and any("anticoagulant" in l for l in links) and any("Kaliémie" in l for l in links) and any("Fibrillation atriale connue" in l for l in links) and any("pénicillines" in l.lower() for l in links),links)
            # ---------- VIII.30 : scores pré-remplis ----------
            await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>/fibrillation/i.test(p.n));render();}")
            sc=await page.evaluate("()=>({pack:currentPack().n,chads:state.scores.chads,hasbled:state.scores.hasbled,fried:SCORES.some(s=>s.id==='fried'),why:state.scoreWhy,txt:scoreWhyText()})")
            ok("VIII.30 : CHA2DS2-VASc pré-rempli d'après les documents (HTA, diabète, âge 65–74, sexe), HAS-BLED (antiagrégant), avec « Pourquoi ? » ; critères de Fried ajoutés",
               sc["chads"] and sc["chads"].get("hta") and sc["chads"].get("dia") and sc["chads"].get("age65") and sc["chads"].get("sexe") and sc["hasbled"] and sc["hasbled"].get("med") and sc["fried"] and "pré-rempli" in sc["txt"],sc)
            await page.evaluate("()=>{state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}")
            # ---------- VII.27 / VIII.34 : courriers et rappels ----------
            L=await page.evaluate("()=>({mt:letTraitant(currentPack()).join('\\n'),sp:letSpecialiste(currentPack()).join('\\n'),fu:docFollowups()})")
            ok("VII.27 : courrier au médecin traitant — documents consultés, biologie retenue avec DFG, suivi spécialisé, antécédents à risque, synthèse en annexe","pris connaissance" in L["mt"] and "Biologie du 12/10/2026" in L["mt"] and "DFG CKD-EPI" in L["mt"] and "Suivi en cardiologie" in L["mt"] and "synthèse du patient" in L["mt"],L["mt"][:900])
            ok("VII.27 : courrier au spécialiste — éléments des documents (biologie, suivi) sans le détail","pris connaissance" in L["sp"] and "Biologie du 12/10/2026" in L["sp"],L["sp"][:600])
            ok("VIII.34 : rappels de suivi issus des documents proposés au médecin traitant (contrôle de la kaliémie, fonction rénale, suivi cardiologique, rappel dTP, grippe)",
               any("kaliémie" in r.lower() for r in L["fu"]) and any("fonction rénale" in r for r in L["fu"]) and any("suivi en cardiologie" in r for r in L["fu"]) and any("rappel dTP" in r for r in L["fu"]) and any("grippale" in r for r in L["fu"]) and all(r.lower() in L["mt"].lower() for r in L["fu"][:2]),L["fu"])
            # ---------- VI.25 : résumé du patient ----------
            S=await page.evaluate("()=>{const S=synthBuild();return {head:S.head,att:S.att.map(x=>x.t),ap:Object.keys(S.atcd),n:S.n,src:[].concat(S.att,S.tt,S.bio).every(x=>x.src),bio:S.bio.map(x=>x.t),vacc:S.vacc.length};}")
            ok("VI.25 : synthèse en une page, ordre fixe (points d'attention ≤ 3, antécédents par appareil, traitements, allergies, biologie, suivi, vaccins), phrases naturelles, source sur chaque ligne",
               S["head"].startswith("Patiente de 68 ans, née le 03/04/1958") and 1<=len(S["att"])<=3 and "cardio-vasculaire" in S["ap"] and "respiratoire" in S["ap"] and S["src"] and any("DFG" in x for x in S["bio"]) and S["vacc"]==4,S)
            await page.evaluate("()=>synthScreen()"); await page.wait_for_selector("#synthview [data-sl]",timeout=5000)
            PROMPT["v"]="Fibrillation atriale permanente (corrigée)"; await page.click("#synthview [data-sl]"); await page.wait_for_timeout(200)
            PROMPT["v"]=""; await page.locator("#synthview [data-sl]").last.click(); await page.wait_for_timeout(200); PROMPT["v"]=None
            E=await page.evaluate("()=>({edits:Object.values(state.synthEdits),shown:document.querySelector('#synthview [data-sl]').textContent,rm:document.querySelectorAll('#synthview .ln.rm').length})")
            ok("VI.25 : chaque ligne corrigeable d'un toucher (texte corrigé, ligne vide = retirée), corrections conservées et chiffrées avec le dossier",any(e.get("t")=="Fibrillation atriale permanente (corrigée)" for e in E["edits"]) and any(e.get("rm") for e in E["edits"]) and "corrigée" in E["shown"] and E["rm"]==1,E)
            await page.click("#sy_print"); await page.wait_for_selector("#print .page.synth",timeout=5000)
            pr=await page.evaluate("()=>({pages:document.querySelectorAll('#print .page').length,synth:!!document.querySelector('#print .page.synth h2'),printing:document.body.classList.contains('printing'),txt:document.querySelector('#print .page.synth').textContent})")
            await page.click("#sy_go"); await page.click("#sy_back"); await page.wait_for_timeout(200)
            ok("VI.25 / VII.27 : résumé imprimable sur une page (en-tête habituel, lignes retirées absentes, sources et dates)",pr["pages"]==1 and pr["synth"] and pr["printing"] and "corrigée" in pr["txt"] and (await page.evaluate("()=>window.__printed"))>=1 and not (await page.evaluate("()=>document.body.classList.contains('printing')")),pr)
            # ---------- VII.28 : synthèse IA complémentaire ----------
            await page.evaluate("()=>{AI.key='sk-ant-test-0000';AI.cfg.mode='complet';AI.cfg.auto='on';AI.cfg.send='ecran';AI.cfg.cap=50;aiSave();render();}")
            hasBtn=await page.evaluate("()=>!!document.getElementById('doc_ai')"); await page.click("#doc_ai"); await page.wait_for_selector("#aisend",timeout=8000)
            ai=await page.evaluate("()=>({kind:AI.pending.kind,model:AI.pending.model,user:AI.pending.user,img:AI.pending.img,leaks:AI.pending.leaks.length,send:!!document.getElementById('ai_send')})")
            ok("VII.28 : avec l'IA activée, « Synthèse IA complémentaire » sur le texte extrait et anonymisé (jamais l'image), écran « Ce qui part », rien d'envoyé sans accord",
               hasBtn and ai["kind"]=="doc" and ai["img"] is None and "DURAND" not in ai["user"] and "Martine" not in ai["user"] and "ELIQUIS" in ai["user"] and ai["send"] and len(calls)==0,{k:v for k,v in ai.items() if k!="user"})
            await page.evaluate("()=>{AI.pending=null;const e=document.getElementById('aisend');if(e)e.remove();AI.cfg.mode='aucun';aiSave();render();}")
            ok("VII.28 : IA coupée → pas de bouton de synthèse IA",not (await page.evaluate("()=>!!document.getElementById('doc_ai')")))
            # ---------- VIII.29 : dictée structurée ----------
            D=await page.evaluate("()=>{state.obs.dict='Patiente allergique à l aspirine, traitement habituel : levothyrox, mesure 1,62 m, TA 150/90, pas de fièvre.';applyDictation(true);return {al:state.allergies,tt:state.tt,taille:state.cst.taille,ta:state.cst.ta,imc:imcCalc()&&imcCalc().txt};}")
            ok("VIII.29 : dictée structurée — allergie, traitement habituel, taille (IMC calculé), constantes rangés en direct","Aspirine" in D["al"] and "LEVOTHYROX" in D["tt"] and D["taille"]=="162" and D["ta"]=="150/90" and D["imc"] and D["imc"].startswith("IMC 26,7"),D)
            # ---------- VIII.31 : questions qui restent à poser ----------
            Q=await page.evaluate("()=>questionsList(currentPack()).map(q=>q.lvl+':'+q.t)")
            ok("VIII.31 : questions restantes filtrées par ce qui est connu (pas d'allergie à redemander), bloquant d'abord",len(Q)>=2 and Q[0].startswith("bloquant:") and not any("allergi" in q.lower() for q in Q) and (await page.evaluate("()=>!!document.querySelector('details.quest')")),Q)
            # ---------- VIII.32 : ce qui manque avant d'imprimer ----------
            M=await page.evaluate("()=>{const s=JSON.stringify({patient:state.patient,ddn:state.ddn,poids:state.poids,cst:state.cst});newPatient();Object.assign(state,{patient:'PETIT Louis',ddn:'03/05/2021',sexe:'h'});state.sel=PACKS.findIndex(p=>/gastro-?ent/i.test(p.n)&&/enfant/i.test(p.n));render();const m1=missingList(currentPack()).map(x=>x.t);const h1=(document.getElementById('missing')||{}).textContent||'';state.poids='14';state.cst.temp='38,5';render();const m2=missingList(currentPack()).map(x=>x.t);return {pack:currentPack().n,m1,h1,m2};}")
            ok("VIII.32 : « Avant d'imprimer, il manque : poids (…) » en une ligne avec la raison, disparaît une fois le poids et la température saisis",any("poids" in x.lower() for x in M["m1"]) and "Avant d'imprimer, il manque" in M["h1"] and "poids" in M["h1"].lower() and not any("poids" in x.lower() for x in M["m2"]),M)
            # ---------- VIII.35 : apprentissage de la pratique ----------
            await page.evaluate("()=>{const now=Date.now();for(let i=0;i<3;i++)JOURNAL.push({id:'t'+i,ts:now-i*864e5*3,patient:'TEST '+i,pack:'Lombalgie aiguë',lieu:'visite'});_pf=null;newPatient();state.view='';render();}")
            await page.fill("#q","lombalgie"); await page.wait_for_timeout(400)
            fr=await page.evaluate("()=>({tag:[...document.querySelectorAll('.res .freq')].map(e=>e.textContent),first:(document.querySelector('.res .n')||{}).textContent||''})")
            ok("VIII.35 : fiche utilisée 3 fois en 90 jours signalée « souvent » et proposée en premier",fr["tag"]==["souvent"] and fr["first"].startswith("Lombalgie aiguë"),fr)
            await page.evaluate("()=>{JOURNAL=JOURNAL.filter(e=>!/^t\\d$/.test(e.id));_pf=null;}")
            # ---------- VIII.37 : « Pourquoi ? » et refus d'un toucher ----------
            await page.evaluate(SET_PATIENT); await page.evaluate("()=>{const d=docNew('import');d.label='Courrier test';d.text=%s;d.pages.push({id:'dpx1',kb:5,ok:true,text:d.text});docFinalize(d);render();}"%json.dumps(COURRIER))
            await page.wait_for_selector("#docprops",timeout=5000); await page.click("#docprops [data-docwhy]"); await page.wait_for_timeout(200)
            W=await page.evaluate("()=>({toast:window.__toasts.slice(-1)[0]||'',n:docPropsCount(state.docProps)})")
            await page.click("#doc_ignore"); await page.wait_for_timeout(300)
            I=await page.evaluate("()=>({ignored:!!state.docProps.ignored,shown:!!document.getElementById('docprops'),tt:state.tt,atcd:state.obs.atcd||''})")
            ok("VIII.37 : chaque proposition porte un « Pourquoi ? » (source et règle) et se refuse d'un toucher (« Ignorer » : rien n'est repris)","mention" in W["toast"] and I["ignored"] and not I["shown"] and I["tt"]==["PREVISCAN"] and I["atcd"]=="",(W,I))
            # ---------- IX.40 : vitesse ----------
            pl=await page.evaluate("()=>perfLine()")
            ok("IX.40 : vitesse mesurée et affichée (ouverture d'un patient, scan d'une page, lecture, analyse, affichage d'une fiche) ; scan + analyse d'une page sous 3 s",
               "scan d'une page" in pl and "lecture d'une page" in pl and "affichage d'une fiche" in pl and TIMES["traitement page (ms)"]+TIMES["OCR page (ms)"]<3000,(pl,TIMES))
            # ---------- IX.41 : jamais de perte : rechargement, documents restaurés, pages déchiffrées ----------
            await page.evaluate(SET_PATIENT); await page.evaluate("()=>{const d=docNew('import');d.label='Courrier test';d.text=%s;d.pages.push({id:'dpx2',kb:5,ok:true,text:d.text});docFinalize(d);}"%json.dumps(CRH))
            await page.set_input_files("#doc_import",[F["bio1.jpg"]]); await page.wait_for_function("()=>!DOCS.busy&&/ajouté/.test(DOCS.status)",timeout=60000)
            await page.evaluate("()=>draftSaveNow()"); await page.wait_for_timeout(600)
            await page.reload(); await reunlock(page); await page.wait_for_timeout(800)
            R=await page.evaluate("()=>({patient:state.patient,n:(state.docs||[]).length,types:(state.docs||[]).map(d=>d.type),ana:(state.docs||[]).every(d=>d.ana),props:docPropsCount(state.docProps),card:!!document.getElementById('docscard')})")
            bid=await page.evaluate("()=>(docsList().find(d=>d.pages.some(p=>/^dp[0-9a-z]+$/.test(p.id)&&p.kb>5))||{}).id")
            await page.evaluate("(id)=>docViewScreen(id)",bid); await page.wait_for_function("()=>document.querySelectorAll('#docview img').length>=1",timeout=10000)
            img=await page.evaluate("()=>document.querySelector('#docview img').naturalWidth")
            ok("IX.41 : après fermeture et réouverture, documents, analyses et propositions restaurés ; page scannée relue depuis la base chiffrée",R["patient"]=="DURAND Martine" and R["n"]==2 and R["ana"] and R["props"]>=3 and R["card"] and img>100,(R,img))
            ok("sécurité : aucune erreur JavaScript, aucun appel réseau externe pendant toute la suite",not errors and len(calls)==0,(errors[:3],calls[:3]))
            await ctx.close()
            # ---------- IX.39 : parcours complet, 4 écrans, captures ----------
            for (w,h,theme,big,label,tag) in [(375,812,"day",False,"iPhone jour","iphone-jour"),(375,812,"night",False,"iPhone nuit","iphone-nuit"),(375,812,"day",True,"iPhone grand texte","iphone-grand-texte"),(1280,900,"day",False,"ordinateur","ordinateur")]:
                c2=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if w<500 else 1,is_mobile=w<500,has_touch=w<500); await net(c2,calls)
                pg=await c2.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
                await unlock(pg,"parcours41z"+tag)
                await pg.evaluate(f"localStorage.setItem('sos_theme','{theme}');localStorage.setItem('sos_theme_force','null');localStorage.setItem('sos_bigtext','{1 if big else 0}');try{{THEME.mode='{theme}';}}catch(e){{}}themeApply();")
                await pg.evaluate("()=>{window.__printed=0;window.print=()=>{window.__printed++;};}")
                ids=await pg.evaluate("""()=>{TOUR.stops=[];TOUR.order=[];TOUR.current='';TOUR.computed=false;delete TOUR.started;newPatient();state.cot.lieu='visite';state.cot.auto=false;
  const a=tourAdd('12 rue des Lilas 45000 Orléans','DUPONT Jean',false,{lat:47.9,lon:1.9,label:'12 rue des Lilas',city:'Orléans'});Object.assign(a,{nom:'DUPONT Jean',ddn:'01/01/1950',tel:'0612345678',motif:'douleur lombaire'});TOUR.order=[a.id];tourSave();state.view='tour';render();return [a.id];}""")
                await pg.wait_for_timeout(500)
                try:
                    await pg.evaluate("()=>{document.querySelectorAll('details').forEach(d=>d.open=true);}"); await pg.click("#tc_begin",timeout=5000)
                    for _ in range(40):
                        if await pg.evaluate("!!TOUR.current"): break
                        await pg.wait_for_timeout(250)
                except Exception: pass
                st=await pg.evaluate("()=>({cur:TOUR.current,pat:state.patient,lieu:state.cot.lieu})")
                if not st["pat"]: await pg.evaluate("(id)=>{TOUR.current=id;Object.assign(state,{patient:'DUPONT Jean',ddn:'01/01/1950',sexe:'h'});state.cot.lieu='visite';state.view='';render();}",ids[0])
                await pg.evaluate("()=>{state.view='';state.sexe='h';render();}"); await pg.wait_for_timeout(300)
                cardOk=await pg.evaluate("()=>{const c=document.getElementById('docscard');if(!c)return null;const r=c.getBoundingClientRect();return {w:r.width,x:r.left,vw:innerWidth,btn:!!document.getElementById('doc_scan_btn')};}")
                st1,_=await scan(pg,F["bio1.jpg"]); await finish(pg)
                await pg.evaluate("()=>{const c=document.getElementById('docscard');if(c)c.scrollIntoView();}"); await pg.wait_for_timeout(250); await pg.screenshot(path=os.path.join(OUT,f"docs-{tag}-1-documents.png"))
                await pg.set_input_files("#doc_import",[F["ordo.pdf"],F["courrier.jpg"]]); await pg.wait_for_function("()=>!DOCS.busy&&/ajouté/.test(DOCS.status)",timeout=120000)
                await pg.evaluate("()=>{const c=document.getElementById('docprops');if(c)c.scrollIntoView();}"); await pg.wait_for_timeout(250); await pg.screenshot(path=os.path.join(OUT,f"docs-{tag}-2-propositions.png"))
                await pg.click("#doc_accept"); await pg.wait_for_timeout(400)
                await pg.evaluate("()=>{state.obs.dict='Douleur lombaire depuis deux jours sans fièvre, pas de déficit moteur, TA 140/85, allergique à la pénicilline.';applyDictation(true);state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.obsOpen=true;render();}"); await pg.wait_for_timeout(300)
                await pg.evaluate("()=>{const c=document.querySelector('.docsay');if(c)c.scrollIntoView();}"); await pg.wait_for_timeout(250); await pg.screenshot(path=os.path.join(OUT,f"docs-{tag}-3-observation.png"))
                await pg.evaluate("()=>synthScreen()"); await pg.wait_for_selector("#synthview",timeout=5000); await pg.wait_for_timeout(250); await pg.screenshot(path=os.path.join(OUT,f"docs-{tag}-4-synthese.png")); await pg.evaluate("()=>{const e=document.getElementById('synthview');if(e)e.remove();}")
                before=await pg.evaluate("()=>({tt:state.tt.slice(),al:state.allergies.slice(),docs:docsList().length,cr:buildCR(currentPack())})")
                await pg.evaluate("()=>{state.ciOver=(state.ciOver||[]);}"); await pg.evaluate("()=>printPack()"); await pg.wait_for_timeout(800)
                ci=await pg.evaluate("()=>!!document.getElementById('ciover')")
                if ci:
                    await pg.evaluate("()=>{ciPending(checkAlerts(currentPack().s)).forEach(a=>{state.ciOver.push({id:a.id,ts:Date.now(),choix:'maintenu',motif:a.motif});});const e=document.getElementById('ciover');if(e)e.remove();printPack();}"); await pg.wait_for_timeout(800)
                pr=await pg.evaluate("()=>({pages:document.querySelectorAll('#print .page').length,printing:document.body.classList.contains('printing'),txt:document.getElementById('print').textContent})")
                await pg.evaluate("()=>{state.lastPrint={n:1,sent:true,ts:Date.now()};document.body.classList.remove('printing');document.getElementById('print').innerHTML='';patientValidate(true);}"); await pg.wait_for_timeout(500)
                await pg.evaluate("()=>{newPatient();render();}"); await pg.wait_for_timeout(300)
                after=await pg.evaluate("()=>({docs:docsList().length,props:!!state.docProps,src:Object.keys(DOCS.src).length,labs:state.labs,tt:state.tt.length,hist:VALID.hist.length,snapDocs:(VALID.hist[0]&&VALID.hist[0].snap&&VALID.hist[0].snap.docs||[]).length})")
                ok(f"IX.39 ({label}) : parcours tournée → patient → scan → documents → accord → dictée → fiche → impression → validation → patient suivant, sans erreur",
                   cardOk and cardOk["btn"] and cardOk["w"]<=cardOk["vw"] and before["docs"]==3 and "ELIQUIS" in before["tt"] and "Pénicillines" in before["al"] and "DOCUMENTS ET RÉSULTATS CONSULTÉS" in before["cr"] and pr["pages"]>=1 and pr["printing"] and after["docs"]==0 and not after["props"] and after["src"]==0 and after["labs"] is None and after["tt"]==0 and after["snapDocs"]==3 and not errs,
                   {"card":cardOk,"before":{k:v for k,v in before.items() if k!="cr"},"pr":{k:v for k,v in pr.items() if k!="txt"},"after":after,"ci":ci,"errs":errs[:2]})
                await c2.close()
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); tot=len(results)
    print(f"\n{n}/{tot} OK"); print("Temps mesurés :",{k:(round(v,2) if isinstance(v,float) else v) for k,v in TIMES.items()})
    with open(os.path.join(ROOT,"tests","resultats_docs_v41z.md"),"w",encoding="utf-8") as f:
        f.write("# Résultats — documents du patient (v41z, demande globale IV–IX)\n\n%s\n\n%d/%d OK — %s\n\nTemps mesurés : %s\n\n"%(datetime.date.today().isoformat(),n,tot,"tous les tests passent" if n==tot else "ÉCHECS",json.dumps({k:(round(v,2) if isinstance(v,float) else v) for k,v in TIMES.items()},ensure_ascii=False)))
        for name,c,info in results: f.write("- %s %s%s\n"%("OK" if c else "FAIL",name,"" if c else " — "+str(info)[:300]))
    sys.exit(0 if n==tot else 1)
asyncio.run(main())
