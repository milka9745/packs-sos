# Tests du lot 1 du registre du 16/10/2026 (n° 10, 5, 9, 7, 8). Données fictives. Lancer : python tests/test_lot1.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
PORT=8772
DICT="Vient pour fièvre depuis hier, toux sèche. Pas de dyspnée. TA 12/7, pouls 90, température 38,6. Gorge rouge. Diagnostic rhinopharyngite."

async def unlock(page,first=True):
    await page.add_init_script("try{if(localStorage.getItem('sos_xp')===null)localStorage.setItem('sos_xp','false')}catch(e){}")  # écran complet (l'Express a sa suite : test_express.py)
    await page.goto(f"http://localhost:{PORT}/index.html")
    if first:
        await page.wait_for_selector("#uid",timeout=15000)
        await page.fill("#uid","testlot1"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
        await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
        await page.check("#rec_ack"); await page.click("#rec_done")
        try:
            await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
        except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(900)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

PICK="""(n)=>{const i=PACKS.findIndex(p=>p.n===n);let cur=selIdx();if(!cur.includes(i))cur=[...cur,i];state.sel=cur.length===1?cur[0]:cur;state.off={};state.lo={};state.gs={};state.edits={};state.f={};state.libre={};state.extra={};render();return i;}"""
DRAFT="(async()=>{const d=await secGet('sos_draft',null);return d&&d.state?{dict:(d.state.obs||{}).dict||'',hist:(d.state.obs||{}).hist||'',photos:(d.state.photos||[]).map(p=>Object.keys(p).join(','))}:null;})()"

async def run(width,label):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={"width":width,"height":800 if width<500 else 900},device_scale_factor=1,is_mobile=width<500,has_touch=width<500,accept_downloads=True)
        page=await ctx.new_page(); errors=[]; dialogs=[]
        page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
        await unlock(page); L=label+" "
        await page.evaluate("Object.assign(state,{patient:'TEST Fictif',ddn:'01/01/1980',date:'16/10/2026',t0:Date.now()});render();")
        # ---------- n° 10 + n° 5 : dictée toujours visible, enregistrée à chaque frappe ----------
        ok(L+"n°5 carte Dictée visible sans fiche choisie",await page.locator("#dictcard #f_dict").count()==1)
        fs=await page.evaluate("(()=>{const t=document.getElementById('f_dict');const cs=getComputedStyle(t);const r=t.getBoundingClientRect();return {fs:parseFloat(cs.fontSize),h:r.height,w:r.width,cw:t.closest('#dictcard').clientWidth-40};})()")
        ok(L+"n°5 grand champ (≥ 140 px de haut, texte 16 px : pas de zoom iPhone, toute la largeur de la carte)",fs["fs"]>=16 and fs["h"]>=140 and fs["w"]>=fs["cw"]*0.95,fs)
        await page.click("#f_dict"); await page.keyboard.type(DICT[:60],delay=5)
        await page.wait_for_timeout(700)
        d=await page.evaluate(DRAFT)
        ok(L+"n°10 dictée enregistrée (chiffrée) pendant la frappe, sans changer d'écran",d and d["dict"]==DICT[:60],d)
        ls=await page.evaluate("JSON.stringify(Object.assign({},localStorage))")
        ok(L+"n°10 aucune dictée en clair dans le stockage",DICT[:30] not in ls)
        ok(L+"n°10 indicateur « enregistrée » affiché","enregistrée" in await page.inner_text("#dictcard"))
        await page.keyboard.type(DICT[60:],delay=2); await page.wait_for_timeout(500)
        # changement de zone : journal, base médicaments, panneau IA, fiches
        await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(300)
        await page.evaluate("state.view='';render();"); await page.wait_for_timeout(300)
        ok(L+"n°10 aller au journal puis revenir : dictée intacte",await page.input_value("#f_dict")==DICT)
        await page.evaluate(PICK,"Rhinopharyngite — adulte"); await page.wait_for_timeout(300)
        await page.evaluate("state.obsOpen=true;render();"); await page.wait_for_timeout(200)
        hist=await page.query_selector('textarea[data-obs="hist"]')
        if hist: await hist.fill("Histoire saisie à la main."); await page.wait_for_timeout(400)
        await page.evaluate(PICK,"Angine — adulte (TROD positif)"); await page.wait_for_timeout(300)
        await page.evaluate("(()=>{const i=PACKS.findIndex(p=>p.n==='Rhinopharyngite — adulte');state.sel=selIdx().filter(x=>x!==i);state.sel=state.sel.length===1?state.sel[0]:state.sel;render();})()"); await page.wait_for_timeout(300)
        ok(L+"n°10 choisir, ajouter, retirer une fiche : dictée et observation conservées",await page.input_value("#f_dict")==DICT and await page.evaluate("state.obs.hist")=="Histoire saisie à la main.")
        await page.evaluate("aiOpen('let')"); await page.wait_for_timeout(200)
        if await page.locator("#ai_in").count():
            await page.fill("#ai_in","ORL, otites à répétition"); await page.wait_for_timeout(200)
            await page.evaluate("document.getElementById('aipanel').remove();aiOpen('cr')"); await page.wait_for_timeout(200)
            await page.evaluate("document.getElementById('aipanel').remove();aiOpen('let')"); await page.wait_for_timeout(200)
            ok(L+"n°10 panneau IA : texte saisi gardé après changement d'onglet",await page.input_value("#ai_in")=="ORL, otites à répétition")
            await page.evaluate("document.getElementById('aipanel').remove()")
        else:
            ok(L+"n°10 panneau IA : (IA sur Aucun, pas de champ) — dictée gardée",await page.input_value("#f_dict")==DICT)
        # fermeture brutale : rechargement de la page (reprise de session sans code)
        await page.wait_for_timeout(600)
        await unlock(page,first=False)
        ok(L+"n°10 après fermeture et réouverture : dictée restaurée automatiquement",await page.input_value("#f_dict")==DICT)
        ok(L+"n°10 après réouverture : observation et fiche restaurées",await page.evaluate("state.obs.hist")=="Histoire saisie à la main." and await page.evaluate("!!currentPack()"))
        # effacement : la dictée reste reprenable
        await page.fill("#f_dict",""); await page.wait_for_timeout(600)
        await page.evaluate("render()"); await page.wait_for_timeout(200)
        ok(L+"n°10 champ effacé : « Dictées récentes » proposé",await page.locator("#dict_hist").count()==1)
        await page.click("#dict_hist"); await page.wait_for_timeout(200)
        await page.click("#dicth [data-dh]"); await page.wait_for_timeout(300)
        ok(L+"n°10 dictée effacée reprise d'un geste",await page.input_value("#f_dict")==DICT,await page.input_value("#f_dict"))
        # n° 5 : « 🎙 Dicter » de la tournée sans zone d'interrogatoire → grand champ
        await page.evaluate("document.activeElement&&document.activeElement.blur();tpDictate();")
        ok(L+"n°5 « Dicter » sans fiche de régulation : focus immédiat dans le grand champ",await page.evaluate("document.activeElement&&document.activeElement.id")=="f_dict")
        await page.screenshot(path=os.path.join(OUT,f"{label}-lot1-dictee.png"))
        # ---------- n° 8 : âge réel prioritaire ----------
        await page.evaluate("state.sel=null;state.obs={};Object.assign(state,{patient:'TEST Enfant',ddn:'01/01/2023',poids:'14'});render();")
        await page.evaluate(PICK,"Gastro-entérite — adulte"); await page.wait_for_timeout(300)
        cr=await page.evaluate("buildCR0(currentPack())")
        ok(L+"n°8 enfant + fiche adulte : aucune mention « adulte » dans le compte rendu","adulte" not in cr.lower(),[l for l in cr.split("\n") if "adulte" in l.lower()])
        ok(L+"n°8 enfant + fiche adulte : doses toujours adaptées (formes enfant)",("enfant" in cr) and ("TIORFAN enfant" in cr or "200 mg sachet" in cr))
        ok(L+"n°8 alerte « fiche adulte pour un patient de 3 ans » avec bascule",await page.locator(".agemis [data-agesw]").count()==1 and "3 ans" in await page.inner_text(".agemis"))
        await page.evaluate(PICK,"Gastro-entérite — enfant"); await page.wait_for_timeout(300)
        cr=await page.evaluate("buildCR0(currentPack())")
        dg=cr.split("Diagnostic retenu : ")[1].split(".")[0]
        ok(L+"n°8 même diagnostic choisi deux fois (adulte + enfant) : aucun doublon",dg=="Gastro-entérite" and "adulte" not in cr.lower() and "gastro-entérite — enfant" not in cr.lower(),[l for l in cr.split("\n") if "astro" in l])
        await page.evaluate("(()=>{const i=PACKS.findIndex(p=>p.n==='Gastro-entérite — enfant');state.sel=selIdx().filter(x=>x!==i)[0];render();})()"); await page.wait_for_timeout(200)
        await page.evaluate("state.obs.hist='Vomissements depuis ce matin.';render();")
        await page.click(".agemis [data-agesw]"); await page.wait_for_timeout(300)
        ok(L+"n°8 bascule en un geste vers la fiche enfant, observation conservée",await page.evaluate("currentPack().n")=="Gastro-entérite — enfant" and await page.evaluate("state.obs.hist")=="Vomissements depuis ce matin.")
        await page.evaluate("state.sel=null;Object.assign(state,{patient:'TEST Adulte',ddn:'01/01/1970',poids:''});render();")
        await page.evaluate(PICK,"Gastro-entérite — enfant"); await page.wait_for_timeout(300)
        ok(L+"n°8 adulte + fiche enfant : alerte et bascule vers l'adulte",await page.locator(".agemis [data-agesw]").count()==1 and "adulte" in await page.inner_text(".agemis"))
        # ---------- n° 7 : photos ----------
        await page.evaluate("state.sel=null;render();"); await page.evaluate(PICK,"Plaie simple / suture"); await page.wait_for_timeout(200)
        await page.evaluate("""(async()=>{const fs=[];for(let k=0;k<12;k++){const cv=document.createElement('canvas');cv.width=4032;cv.height=3024;const c=cv.getContext('2d');const g=c.createLinearGradient(0,0,4032,3024);g.addColorStop(0,'#'+(k*20+30).toString(16).padStart(2,'0')+'8844');g.addColorStop(1,'#224488');c.fillStyle=g;c.fillRect(0,0,4032,3024);c.fillStyle='#fff';c.font='200px Arial';c.fillText('Document '+(k+1),300,1500);for(let n=0;n<4000;n++){c.fillStyle='rgba('+(n%255)+',90,'+(255-n%255)+',.5)';c.fillRect(Math.random()*4032,Math.random()*3024,30,30);}
          const bl=await new Promise(r=>cv.toBlob(r,'image/jpeg',0.95));fs.push(new File([bl],'IMG_'+k+'.jpg',{type:'image/jpeg'}));}
          window.__big=fs.map(f=>f.size);await addPhotoFiles(fs);})()""")
        t0=time.time()
        while await page.evaluate("PHOTO.busy") and time.time()-t0<120: await page.wait_for_timeout(300)
        n=await page.evaluate("state.photos.length"); big=await page.evaluate("Math.round(window.__big.reduce((a,b)=>a+b,0)/1048576)")
        ok(L+f"n°7 12 photos de 12 Mpx ({big} Mo) intégrées au dossier",n==12,n)
        sz=await page.evaluate("state.photos.map(p=>Math.round(p.src.length*0.75/1024))")
        ok(L+"n°7 compressées sur l'appareil (< 450 Ko chacune)",sz and max(sz)<450,sz)
        st=await page.evaluate("(document.getElementById('ph_status')||{}).textContent||PHOTO.last||''")
        ok(L+"n°7 confirmation affichée avec poids et espace libre","12 photos ajoutées" in st and "chiffrées" in st and "espace libre" in st,st)
        await page.wait_for_timeout(700)
        d=await page.evaluate(DRAFT); lsz=await page.evaluate("Object.keys(localStorage).reduce((a,k)=>a+(localStorage.getItem(k)||'').length,0)")
        ok(L+"n°7 brouillon sans images (aucun dépassement du stockage local)",d and all(x=="id,cap,kb" for x in d["photos"]) and lsz<1500000,[d and d["photos"][:2],lsz])
        idb=await page.evaluate("""phTx('readonly',st=>st.getAll()).then(v=>({n:v.length,clair:v.some(x=>JSON.stringify(x).includes('data:image')),enc:v.every(x=>x.enc&&x.enc.iv&&x.enc.ct)}))""")
        ok(L+"n°7 coffre photos chiffré (AES-GCM), aucune image en clair",idb["n"]>=12 and not idb["clair"] and idb["enc"],idb)
        await unlock(page,first=False)
        t0=time.time()
        while await page.evaluate("state.photos.filter(p=>p.src).length")<12 and time.time()-t0<20: await page.wait_for_timeout(300)
        ok(L+"n°7 après fermeture : les 12 photos reviennent",await page.evaluate("state.photos.filter(p=>p.src).length")==12)
        await page.evaluate("PHOTO._sp=phSpace;phSpace=async()=>({free:3*1048576,quota:1e9});")
        dialogs.clear(); await page.evaluate("""(async()=>{const cv=document.createElement('canvas');cv.width=800;cv.height=600;const bl=await new Promise(r=>cv.toBlob(r,'image/jpeg'));await addPhotoFiles([new File([bl],'x.jpg',{type:'image/jpeg'})]);})()""")
        await page.wait_for_timeout(500)
        ok(L+"n°7 stockage presque plein : refus expliqué avec la limite exacte (Mo libres)",any("presque plein" in m and "Mo libres" in m for m in dialogs),dialogs[-1:] )
        await page.evaluate("phSpace=PHOTO._sp;")
        # ---------- n° 9 : impression et PDF ----------
        await page.evaluate("window.__pr=0;window.print=()=>{window.__pr++;};")
        await page.evaluate("Object.assign(state,{patient:'TEST Fictif',ddn:'01/01/1980'});state.photos=[];render();")
        if width<500:
            await page.click("#go_top"); await page.wait_for_timeout(1200)
            ok(L+"n°9 aperçu : boutons Envoyer, Enregistrer le PDF, Impression visibles",all([await page.locator(s).is_visible() for s in ["#pb_send","#pb_pdf","#pb_ios"]]))
            await page.click("#pb_ios"); await page.wait_for_timeout(200)
            ok(L+"n°9 « Impression » ouvre la fenêtre d'impression",await page.evaluate("window.__pr")>=1)
        else:
            await page.click("#go_only"); await page.wait_for_timeout(1200)
            ok(L+"n°9 « Imprimer » ouvre la fenêtre d'impression sans Ctrl+P",await page.evaluate("window.__pr")>=1)
            hit=await page.evaluate("['pb_print2','pb_pdf2','pb_valid2','pb_back2','pb_print','pb_pdf','pb_valid','pb_back'].map(id=>{const e=document.getElementById(id);if(!e)return id+':absent';const r=e.getBoundingClientRect();const pts=[[r.left+4,r.top+4],[r.left+r.width/2,r.top+r.height/2],[r.right-4,r.bottom-4]];return pts.every(([x,y])=>{const h=document.elementFromPoint(x,y);return h&&(h===e||e.contains(h));})?'':id;}).filter(Boolean)")
            ok(L+"n°9 aperçu : chaque bouton entièrement cliquable (barres sans chevauchement)",not hit,hit)
            await page.click("#pb_print2"); await page.wait_for_timeout(200)
            ok(L+"n°9 bouton « Imprimer » de l'aperçu",await page.evaluate("window.__pr")>=2)
        try:
            async with page.expect_download(timeout=90000) as dl:
                await page.click("#pb_pdf")
            f=await dl.value; path=await f.path(); head=open(path,"rb").read(5)
            ok(L+"n°9 « Enregistrer en PDF » produit un vrai fichier PDF",f.suggested_filename.endswith(".pdf") and head==b"%PDF-",f.suggested_filename)
        except Exception as e:
            ok(L+"n°9 « Enregistrer en PDF » produit un vrai fichier PDF",False,str(e)[:200])
        await page.screenshot(path=os.path.join(OUT,f"{label}-lot1-impression.png"))
        ok(L+"aucune erreur JS",not errors,errors[:3])
        await b.close()

async def visuals():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for big in [False,True]:
            for th in ["day","night"]:
                ctx=await b.new_context(viewport={"width":375,"height":800},device_scale_factor=2,is_mobile=True,has_touch=True)
                page=await ctx.new_page(); await unlock(page)
                await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();state.obs={{dict:'Vient pour fièvre depuis hier.'}};render();")
                await page.wait_for_timeout(300)
                r=await page.evaluate("(()=>{const c=document.getElementById('dictcard');const W=document.documentElement.clientWidth;const over=[...c.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>W+1).length;return {over,sw:document.documentElement.scrollWidth,W};})()")
                tag=f"375 px {'grand texte' if big else 'normal'} {'jour' if th=='day' else 'nuit'}"
                ok(tag+" : carte Dictée sans débordement horizontal",r["over"]==0 and r["sw"]<=r["W"],r)
                await page.evaluate("document.getElementById('dictcard').scrollIntoView({block:'start'})"); await page.wait_for_timeout(150)
                await page.screenshot(path=os.path.join(OUT,f"iphone-lot1-dictee-{'grand' if big else 'normal'}-{th}.png"))
                await ctx.close()
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,"iphone"); await run(1280,"pc"); await visuals()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_lot1.md"),"w",encoding="utf-8").write("# Tests lot 1 — registre du 16/10/2026 (n° 10, 5, 9, 7, 8)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
