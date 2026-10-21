# -*- coding: utf-8 -*-
# v41z, retours du 21/10/2026 sur les documents : (1) blocs déplaçables (ordre par mode, « Organiser ma fiche », appui long, Express),
# (2) scanner avec détection des bords, aperçu à 4 coins ajustables, redressement, noir et blanc, « Importer un scan »,
# (3) noms lisibles et types de documents, (4) résumé : doublons par molécule, classes exactes, posologie lue, antécédents non répétés.
# Documents et patients fictifs ; iPhone 375 px ; aucun appel externe. Lancer : python tests/test_docs2_v41z.py
import asyncio, os, re, json, subprocess, sys, time, tempfile, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,"tests","captures"); PORT=8790
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:900])
ns={"__file__":os.path.join(ROOT,"tests","test_docs_v41z.py")}
exec(open(os.path.join(ROOT,"tests","test_docs_v41z.py"),encoding="utf-8").read().split("async def unlock")[0],ns)
BIO1,COURRIER,CRH,VACCIN,sheet_html,screen_html,make_pdf,ORDO_PDF=ns["BIO1"],ns["COURRIER"],ns["CRH"],ns["VACCIN"],ns["sheet_html"],ns["screen_html"],ns["make_pdf"],ns["ORDO_PDF"]
ORDO_IMG="""Docteur Paul MARTIN - Cardiologue
Ordonnance du 03/09/2026
Madame DURAND Martine
ELIQUIS 5 mg : 1 cp matin et soir
APROVEL 150 mg : 1 cp le matin
LEVOTHYROX 75 µg : 1 cp le matin à jeun
APIXABAN 5 mg : 1 comprimé matin et soir (générique)
QSP 3 mois"""
RADIO="""CABINET DE RADIOLOGIE
Radiographie du thorax de face du 12/10/2026
Technique : cliché de face debout.
Résultat : pas de foyer parenchymateux, pas d'épanchement pleural.
Conclusion : cardiomégalie modérée sans foyer infectieux."""
async def unlock(page,uid):
    await page.add_init_script("try{localStorage.setItem('sos_xp','true');localStorage.setItem('sos_excomplet','0');}catch(e){}")
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
SET="()=>{newPatient();Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f',poids:'70'});state.cot.lieu='consultation';state.cot.auto=false;state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"
ORDER="()=>{const fp=document.getElementById('f_patient');const c=fp&&fp.closest('section.pcard').parentElement;return c?[...c.children].map(e=>e.dataset.blk).filter((k,i,a)=>k&&a.indexOf(k)===i):[];}"
XPORDER="()=>[...document.querySelectorAll('#main > .xp > [data-blk]')].map(e=>e.dataset.blk)"
async def net(ctx):
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
async def main():
    tmp=tempfile.mkdtemp(prefix="docs2_41z_")
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); c0=await b.new_context(viewport={"width":1000,"height":1400}); F={}
            async def shot(name,html,q=88):
                pg=await c0.new_page(); await pg.set_content(html); F[name]=os.path.join(tmp,name); await pg.screenshot(path=F[name],type="jpeg",quality=q); await pg.close()
            await shot("bio1.jpg",sheet_html(BIO1)); await shot("ordo.jpg",sheet_html(ORDO_IMG,0.7)); await shot("courrier.jpg",sheet_html(COURRIER,0.5,0,25)); await shot("crh.jpg",sheet_html(CRH,-0.6,0,25)); await shot("vaccin.jpg",sheet_html(VACCIN,0.4)); await shot("radio.jpg",sheet_html(RADIO,0.3))
            await shot("clair.jpg",sheet_html(BIO1).replace("background:#3b3b3b","background:#f4f4f4")); await shot("ecran.jpg",screen_html(ORDO_IMG))
            await c0.close(); F["ordo.pdf"]=os.path.join(tmp,"ordo.pdf"); make_pdf(F["ordo.pdf"],ORDO_PDF)
            ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True); await net(ctx)
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page,"docs2ret"); await page.evaluate(SET); await page.wait_for_timeout(300)
            # ---------- 1. blocs déplaçables ----------
            xo=await page.evaluate(XPORDER)
            ok("1. Express actif : une seule carte Documents, cartes de l'Express dans l'ordre (dictée, documents, favoris)",xo==["dict","docs","options"] and await page.evaluate("()=>document.querySelectorAll('#docscard').length")==1,xo)
            await page.evaluate("()=>{localStorage.setItem('sos_xp','false');render();}"); await page.wait_for_timeout(300)
            o=await page.evaluate(ORDER)
            ok("1. mode complet : ordre par défaut, Scanner et documents juste avant le Motif (patient, dictée, documents, motif, …, observation, ordonnances, courriers)",o[:4]==["patient","dict","docs","motif"] and o[-3:]==["obs","sheets","lettres"],o)
            await page.evaluate("()=>{document.getElementById('jmenu').hidden=false;}")
            ok("1. ⋯ → « Organiser ma fiche (ordre des blocs) »",await page.locator("#jmenu [data-blkorg]").count()==1)
            await page.click("#jmenu [data-blkorg]"); await page.wait_for_selector("#blk_list li",timeout=5000)
            lis=await page.evaluate("()=>[...document.querySelectorAll('#blk_list li')].map(l=>l.dataset.blkk)")
            ok("1. écran « Organiser ma fiche » : liste des blocs avec poignée, Monter, Descendre, mode Visite / Consultation",lis==["patient","dict","docs","motif","synth","options","alerts","obs","sheets","lettres"] and await page.locator("#blk_list .blk-handle").count()==10 and await page.locator("[data-blkmode]").count()==2,lis)
            await page.screenshot(path=os.path.join(OUT,"docs2-iphone-organiser.png"))
            for _ in range(5): await page.click('#blk_list [data-blkup="obs"]'); await page.wait_for_timeout(60)
            await page.click("#blk_close"); await page.wait_for_timeout(200)
            o2=await page.evaluate(ORDER)
            ok("1. « Monter » ×5 sur Observation : appliqué aussitôt à la fiche (observation avant les documents et le motif)",o2.index("obs")<o2.index("docs") and o2.index("obs")<o2.index("motif"),o2)
            await page.evaluate("()=>{state.cot.lieu='visite';render();}"); ov=await page.evaluate(ORDER)
            await page.evaluate("()=>{state.cot.lieu='consultation';render();}"); oc=await page.evaluate(ORDER)
            ok("1. ordre mémorisé par mode : la visite garde l'ordre par défaut, la consultation l'ordre modifié",ov.index("obs")>ov.index("motif") and oc.index("obs")<oc.index("motif"),(ov,oc))
            await page.evaluate("()=>draftSaveNow()"); await page.reload(); await reunlock(page); await page.evaluate("()=>{state.cot.lieu='consultation';state.sel=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');render();}"); await page.wait_for_timeout(300)
            o3=await page.evaluate(ORDER); enc=await page.evaluate("()=>Object.keys(localStorage).some(k=>/sos_blocs_/.test(k)&&/_enc$/.test(k))")
            ok("1. après fermeture et réouverture : ordre retrouvé, enregistré chiffré dans le profil",o3.index("obs")<o3.index("motif") and enc,(o3,enc))
            await page.evaluate("()=>{localStorage.setItem('sos_xp','true');render();}"); await page.wait_for_timeout(300)
            # appui long et glisser dans l'Express : Documents avant Dictée
            r=await page.evaluate("""async()=>{const docs=document.getElementById('docscard'),dict=document.getElementById('dictcard');if(!docs||!dict||docs.parentElement!==dict.parentElement)return {err:'cartes non voisines'};
              const ev=(t,el,cx,cy)=>el.dispatchEvent(new PointerEvent(t,{bubbles:true,clientX:cx,clientY:cy,pointerId:1,pointerType:'touch',isPrimary:true}));const r=docs.getBoundingClientRect();
              ev('pointerdown',docs.querySelector('.pcard-h')||docs,r.left+30,r.top+8);await new Promise(x=>setTimeout(x,700));const dragging=document.body.classList.contains('blk-dragging');
              const rd=dict.getBoundingClientRect();ev('pointermove',document.body,rd.left+30,rd.top+6);await new Promise(x=>setTimeout(x,60));ev('pointerup',document.body,rd.left+30,rd.top+6);await new Promise(x=>setTimeout(x,250));
              const xp=[...docs.parentElement.children].map(e=>e.dataset.blk).filter(Boolean);return {dragging,xp,order:blkOrder()};}""")
            ok("1. appui long (0,55 s) puis glisser : Documents déposé avant Dictée dans l'Express, ordre enregistré",r.get("dragging") and r.get("xp",[])[:2]==["docs","dict"] and r["order"].index("docs")<r["order"].index("dict"),r)
            await page.evaluate("()=>{BLK.order={visite:null,consultation:null};blkSave();render();}")
            # ---------- 2. scanner ----------
            await page.evaluate("()=>{DOCS.scan={id:null,n:0};}"); await page.set_input_files("#doc_scan",F["bio1.jpg"]); await page.wait_for_selector("#scanprev .scanh",timeout=15000)
            sp=await page.evaluate("()=>({auto:SCAN.auto,quad:SCAN.quad.map(p=>[Math.round(p.x),Math.round(p.y)]),w:SCAN.cv.width,h:SCAN.cv.height,handles:document.querySelectorAll('#scanprev .scanh').length,msg:document.getElementById('scan_msg').textContent,btns:[...document.querySelectorAll('#scanprev .scanacts button')].map(b=>b.id)})")
            q=sp["quad"]; near=lambda pt,x,y:abs(pt[0]-x)<60 and abs(pt[1]-y)<60
            ok("2. photo → aperçu immédiat : bords détectés automatiquement, 4 coins posés sur la feuille (± 60 px), Valider / Toute l'image / Reprendre / Annuler",
               sp["auto"] and sp["handles"]==4 and near(q[0],70,105) and near(q[1],930,125) and near(q[2],930,1295) and near(q[3],70,1275) and sp["btns"]==["scan_ok","scan_full","scan_retake","scan_cancel"],sp)
            await page.screenshot(path=os.path.join(OUT,"docs2-iphone-scanner-coins.png"))
            mv=await page.evaluate("""()=>{const h=document.querySelector('#scanprev .scanh[data-corner="0"]');const wrap=document.getElementById('scanwrap').getBoundingClientRect();const ev=(t,cx,cy)=>h.dispatchEvent(new PointerEvent(t,{bubbles:true,clientX:cx,clientY:cy,pointerId:2,pointerType:'touch',isPrimary:true}));ev('pointerdown',wrap.left+20,wrap.top+30);ev('pointermove',wrap.left+40,wrap.top+50);ev('pointerup',wrap.left+40,wrap.top+50);const k=SCAN.scale;return {x:SCAN.quad[0].x*k,y:SCAN.quad[0].y*k,auto:SCAN.auto};}""")
            ok("2. coin ajustable au doigt : le coin 1 suit le doigt",abs(mv["x"]-40)<3 and abs(mv["y"]-50)<3 and not mv["auto"],mv)
            await page.click("#scan_ok"); await page.wait_for_function("()=>!document.getElementById('scanprev')&&/enregistrée|non enregistrée/.test(DOCS.status)",timeout=20000)
            pg1=await page.evaluate("()=>({status:DOCS.status,thumbs:document.querySelectorAll('.scanthumbs img').length,p:docsList()[0].pages[0],next:!!document.getElementById('doc_next'),fin:!!document.getElementById('doc_finish')})")
            ok("2. « Valider la page » : redressement en perspective, noir et blanc, ≈ 50–120 Ko, miniature affichée, « Page suivante » et « Terminer »",pg1["p"]["cropped"] and pg1["p"]["ok"] and 30<=pg1["p"]["kb"]<=230 and pg1["thumbs"]==1 and pg1["next"] and pg1["fin"],pg1)
            bw=await page.evaluate("()=>{const img=new Image();img.src=DOCS.src[docsList()[0].pages[0].id];return new Promise(r=>{img.onload=()=>{const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const g=c.getContext('2d');g.drawImage(img,0,0);const d=g.getImageData(0,0,c.width,c.height).data;let mid=0;for(let i=0;i<d.length;i+=4*7){if(d[i]>70&&d[i]<185)mid++;}r({mid:mid/(d.length/28),w:img.width,h:img.height});};});}")
            ok("2. la page stockée est bien un scan noir et blanc contrasté (presque aucun gris intermédiaire), jamais la photo brute",bw["mid"]<0.08,bw)
            await page.set_input_files("#doc_scan",F["clair.jpg"]); await page.wait_for_selector("#scanprev .scanh",timeout=15000)
            cl=await page.evaluate("()=>({auto:SCAN.auto,msg:document.getElementById('scan_msg').textContent,quad:SCAN.quad.map(p=>[Math.round(p.x),Math.round(p.y)])})")
            ok("2. fond clair (bords non détectables) : dit franchement, coins proposés à placer à la main",not cl["auto"] and "non détectés" in cl["msg"] and cl["quad"][0]==[80,112],cl)
            await page.click("#scan_full"); await page.click("#scan_ok"); await page.wait_for_function("()=>!document.getElementById('scanprev')&&/enregistrée|non enregistrée|illisible|reprenez/.test(DOCS.status)",timeout=20000)
            n2=await page.evaluate("()=>({n:DOCS.scan.n,p:docsList()[0].pages[1]})")
            ok("2. « Toute l'image » : page gardée entière, pages enchaînées (compteur 2)",n2["n"]==2 and n2["p"] and not n2["p"]["cropped"],n2)
            await page.evaluate("()=>docScanFinish()"); await page.wait_for_function("()=>!DOCS.busy&&docsList()[0].ana",timeout=120000)
            d0=await page.evaluate("()=>{const d=docsList()[0];return {type:d.type,label:d.label,pages:d.pages.length,n:d.ana.labs&&d.ana.labs.n};}")
            ok("3. document scanné nommé lisiblement : « Bilan sanguin 12/10/2026 » (type + date)",d0["label"]=="Bilan sanguin 12/10/2026" and d0["type"]=="bio" and d0["n"]>=5,d0)
            await page.evaluate("()=>{DOCS.screen=true;DOCS.scan={id:null,n:0};}"); await page.set_input_files("#doc_scan",F["ecran.jpg"]); await page.wait_for_selector("#scanprev .scanh",timeout=15000)
            sc=await page.evaluate("()=>({auto:SCAN.auto,full:SCAN.quad[2].x===SCAN.cv.width&&SCAN.quad[2].y===SCAN.cv.height,msg:document.getElementById('scan_msg').textContent})")
            await page.click("#scan_ok"); await page.wait_for_function("()=>!document.getElementById('scanprev')&&/enregistrée/.test(DOCS.status)",timeout=20000); await page.evaluate("()=>docScanFinish()"); await page.wait_for_function("()=>!DOCS.busy&&docsList()[1]&&docsList()[1].ana",timeout=120000); await page.evaluate("()=>{DOCS.screen=false;}")
            e1=await page.evaluate("()=>{const d=docsList()[1];return {type:d.type,label:d.label,words:d.pages[0].words,meds:d.ana.meds.map(m=>m.name)};}")
            ok("2. écran de téléphone : toute l'image proposée, texte clair sur fond sombre lu, ordonnance reconnue et nommée",sc["full"] and "Écran" in sc["msg"] and e1["type"]=="ordo" and e1["label"].startswith("Ordonnance") and "ELIQUIS" in e1["meds"],(sc,e1))
            # ---------- 2 et 3. import : « Importer un scan », types, noms ----------
            lab=await page.evaluate("()=>document.getElementById('doc_import_btn').textContent")
            ok("2. bouton « Importer un scan » (PDF du scanner de Notes ou de Fichiers, photos)","Importer un scan" in lab,lab)
            await page.evaluate("()=>{docsList().length=0;DOCS.scan=null;}")
            await page.set_input_files("#doc_import",[F["ordo.jpg"],F["courrier.jpg"],F["crh.jpg"],F["vaccin.jpg"],F["bio1.jpg"],F["radio.jpg"],F["ordo.pdf"]]); await page.wait_for_function("()=>!DOCS.busy&&/ajouté/.test(DOCS.status)",timeout=240000)
            docs=await page.evaluate("()=>docsList().map(d=>({type:d.type,label:d.label,src:d.src}))")
            types=[d["type"] for d in docs]; labels=[d["label"] for d in docs]
            ok("3. 7 documents importés, 7 types reconnus (aucun « Document »)",types==["ordo","courrier","crh","vaccin","bio","imagerie","ordo"],types)
            ok("3. noms lisibles générés : type + spécialité + date (« Ordonnance 03/09/2026 », « Courrier cardiologue 15/09/2026 », « Compte rendu d'hospitalisation (pneumologie) 02/06/2026 », « Carte de vaccination », « Bilan sanguin 12/10/2026 », « Radiographie du thorax 12/10/2026 »)",
               labels==["Ordonnance 03/09/2026","Courrier cardiologue 15/09/2026","Compte rendu d'hospitalisation (pneumologie) 02/06/2026","Carte de vaccination","Bilan sanguin 12/10/2026","Radiographie du thorax 12/10/2026","Ordonnance 03/09/2026"],labels)
            await page.evaluate("()=>{const i=document.querySelector('#docscard input[data-doclabel]');i.value='Ordonnance cardiologue (septembre)';i.dispatchEvent(new Event('change',{bubbles:true}));}")
            ed=await page.evaluate("()=>({label:docsList()[0].label,manual:!!docsList()[0].labelManual,cons:docsConsultedLines()[0]})")
            ok("3. nom modifiable d'un toucher, conservé et repris dans « Documents consultés »",ed["label"]=="Ordonnance cardiologue (septembre)" and ed["manual"] and "« Ordonnance cardiologue (septembre) »" in ed["cons"],ed)
            await page.evaluate("()=>{const c=document.getElementById('docscard');if(c)c.scrollIntoView();}"); await page.wait_for_timeout(200); await page.screenshot(path=os.path.join(OUT,"docs2-iphone-noms.png"))
            T=await page.evaluate("""()=>{const mk=t=>{const d={type:'autre',text:t,pages:[],ana:null};docAnalyze(d);return d.type;};return [
              mk('Dr A. B. Pneumologue\\nle 3 mars 2026\\nCher ami,\\nje revois ce jour Mr X pour sa BPCO. Le VEMS est stable.\\nBien amicalement'),
              mk('ORDONNANCE\\nAMLOR 5 mg 1 cp le matin\\nTAHOR 20 mg 1 cp le soir\\nQSP 3 mois'),
              mk('Resultats\\nHemoglobine 13.1 g/dl\\nLeucocytes 6.2 G/l\\nPlaquettes 210 G/l\\nCreatinine 78 umol/l'),
              mk('Service des urgences\\nMotif d admission : chute\\nSorti le 02/05/2026\\nTraitement de sortie : DOLIPRANE'),
              mk('Radiographie du genou droit de face et de profil\\nPas de fracture visible. Pincement femoro-tibial interne.'),
              mk('Carnet de sante\\nREVAXIS 12/03/2015\\nINFLUVAC 05/11/2024'),
              mk('Compte rendu de consultation\\nMadame X, 72 ans\\nvue ce jour pour douleurs du genou\\nje propose une infiltration\\nDr Y rhumatologue')];}""")
            ok("3. textes courts ou bruités (lecture imparfaite) : courrier, ordonnance, bilan, compte rendu, imagerie, vaccination, courrier",T==["courrier","ordo","bio","crh","imagerie","vaccin","courrier"],T)
            # ---------- 4. résumé ----------
            P=await page.evaluate("()=>{const P=state.docProps;return P.tt.map(x=>({t:x.t,l:medLabel(x.t),poso:x.poso}));}")
            ok("4. propositions : une seule ligne par molécule (ELIQUIS et APIXABAN fusionnés), DCI (marque) — classe exacte, posologie lue",
               [x["t"] for x in P].count("ELIQUIS")==1 and not any(x["t"]=="APIXABAN" for x in P) and any(x["l"].startswith("APIXABAN (ELIQUIS) — anticoagulant oral direct") and x["poso"]=="5 mg : 1 cp matin et soir" for x in P) and any(x["l"].startswith("IRBESARTAN (APROVEL) — sartan") for x in P) and any(x["l"].startswith("LEVOTHYROXINE (LEVOTHYROX) — hormone thyroïdienne") for x in P),P)
            await page.evaluate("()=>{state.tt=['APIXABAN','APROVEL 150'];docAccept();}")
            S=await page.evaluate("()=>{const S=synthBuild();return {tt:S.tt.map(x=>x.t),att:S.att.map(x=>x.t),atcd:Object.values(S.atcd).flat().map(x=>x.t),ttState:state.tt};}")
            ok("4. résumé : APIXABAN saisi + ELIQUIS lu = une ligne « APIXABAN (ELIQUIS) — anticoagulant oral direct (anti-Xa) : … (posologie lue) » ; APROVEL = sartan ; LEVOTHYROX = hormone thyroïdienne",
               sum(1 for t in S["tt"] if t.startswith("APIXABAN"))==1 and any(t.startswith("APIXABAN (ELIQUIS) — anticoagulant oral direct (anti-Xa) : 5 mg : 1 cp matin et soir (posologie lue)") for t in S["tt"]) and any(t.startswith("IRBESARTAN (APROVEL) — sartan") for t in S["tt"]) and any(t.startswith("LEVOTHYROXINE (LEVOTHYROX) — hormone thyroïdienne") for t in S["tt"]) and "ELIQUIS" not in S["ttState"],S)
            await page.evaluate("()=>{state.labs=null;}")
            S2=await page.evaluate("()=>{const S=synthBuild();return {att:S.att.map(x=>x.t),atcd:Object.values(S.atcd).flat().map(x=>x.t)};}")
            fa_att=[t for t in S2["att"] if t.startswith("fibrillation")]; fa_atcd=[t for t in S2["atcd"] if t.startswith("fibrillation")]
            bpco_att=[t for t in S2["att"] if t.startswith("BPCO")]; bpco_atcd=[t for t in S2["atcd"] if t.startswith("BPCO")]
            ok("4. antécédent déjà en « Points d'attention » : répété seulement s'il justifie une alerte (FA sous anticoagulant → « alerte active »), sinon non répété",
               (not fa_att or (fa_atcd and "alerte active" in fa_atcd[0])) and (not bpco_att or not bpco_atcd or "alerte active" in bpco_atcd[0]) and len(S2["att"])<=3,S2)
            await page.evaluate("()=>synthScreen()"); await page.wait_for_selector("#synthview",timeout=5000); await page.wait_for_timeout(200); await page.screenshot(path=os.path.join(OUT,"docs2-iphone-resume.png")); await page.evaluate("()=>{const e=document.getElementById('synthview');if(e)e.remove();}")
            ok("sécurité : aucune erreur JavaScript",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); tot=len(results); print(f"\n{n}/{tot} OK")
    with open(os.path.join(ROOT,"tests","resultats_docs2_v41z.md"),"w",encoding="utf-8") as f:
        f.write("# Résultats — retours documents v41z (blocs, scanner, noms, résumé)\n\n%s\n\n%d/%d OK\n\n"%(datetime.date.today().isoformat(),n,tot))
        for name,c,info in results: f.write("- %s %s%s\n"%("OK" if c else "FAIL",name,"" if c else " — "+str(info)[:300]))
    sys.exit(0 if n==tot else 1)
asyncio.run(main())
