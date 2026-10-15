# Tests navigateur v41 — import de documents et d'images vers l'IA (lecture locale réelle, API simulée, document fictif)
# Lancer : python tests/test_doc.py
import asyncio, os, json, subprocess, time, sys, base64
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)
IDENT=["DUPONT","Dupont","Marie-Claire","1985","06 12","Bioallians","République","123456789"]

# Faux compte rendu de biologie dessiné dans la page ; photo JPEG avec un bloc EXIF et une position GPS factices
MAKE="""async(mode)=>{const cv=document.createElement('canvas');cv.width=1400;cv.height=760;const c=cv.getContext('2d');c.fillStyle='#fff';c.fillRect(0,0,1400,760);c.fillStyle='#000';c.font='38px Arial';
 const L=['Laboratoire Bioallians','12 rue de la République 45000 Orléans','Patient : DUPONT Marie-Claire','Née le 12/03/1985','Tél 06 12 34 56 78','Dossier 123456789','Hémoglobine 12,5 g/dl','CRP 85 mg/l'];
 L.forEach((t,i)=>c.fillText(t,60,80+i*85));
 const b64=cv.toDataURL('image/jpeg',0.92).split(',')[1];const raw=Uint8Array.from(atob(b64),x=>x.charCodeAt(0));
 const exif=new TextEncoder().encode('Exif\\0\\0GPSLatitude=47.9029;GPSLongitude=1.9093;Owner=DUPONT');const app1=new Uint8Array(4+exif.length);app1[0]=0xFF;app1[1]=0xE1;app1[2]=((exif.length+2)>>8)&255;app1[3]=(exif.length+2)&255;app1.set(exif,4);
 const out=new Uint8Array(raw.length+app1.length);out.set(raw.subarray(0,2),0);out.set(app1,2);out.set(raw.subarray(2),2+app1.length);
 return new File([out],'photo.jpg',{type:'image/jpeg'});}"""

async def unlock(page):
    await page.goto("http://localhost:8768/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testv41"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)

async def idle(page,ms=90000):
    t=time.time()
    while time.time()-t<ms/1000:
        if not await page.evaluate("DOC.busy"): return True
        await page.wait_for_timeout(300)
    return False

async def import_doc(page):
    await page.evaluate("(async()=>{const f=await ("+MAKE+")();aiDocImport(f);})()")
    await page.wait_for_selector("#aidoc",timeout=10000); await page.wait_for_timeout(300)
    return await idle(page)

async def go_until_sent(page,tries=4):
    for _ in range(tries):
        await page.click("#ad_go"); await page.wait_for_timeout(300); await idle(page)
        if await page.locator("#aisend").count(): return True
        if await page.locator("#ad_fix").count(): await page.click("#ad_fix"); await page.wait_for_timeout(300)
        if not await page.evaluate("DOC.checked"): await page.check("#ad_ok"); await page.wait_for_timeout(200)
    return await page.locator("#aisend").count()>0

async def run(width,height,label):
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":width,"height":height},is_mobile=width<500,has_touch=width<500)
        page=await ctx.new_page(); errors=[]; dialogs=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
        sent=[]; replies=[]
        async def handle(route):
            req=route.request; cors={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"POST, OPTIONS"}
            if req.method=="OPTIONS": await route.fulfill(status=204,headers=cors); return
            sent.append(req.post_data or "")
            r=replies.pop(0) if replies else {}
            await route.fulfill(status=200,headers=dict(cors,**{"content-type":"application/json"}),body=json.dumps({"model":"claude-sonnet-5-5","stop_reason":"end_turn","content":[{"type":"text","text":json.dumps(r,ensure_ascii=False)}],"usage":{"input_tokens":2000,"output_tokens":300}},ensure_ascii=False))
        await ctx.route("https://api.anthropic.com/**",handle)
        await unlock(page); L=label+" "
        await page.evaluate("AI.key='sk-ant-test-factice';AI.cfg.mode='partiel';aiSave();Object.assign(state,{patient:'DUPONT Marie-Claire',ddn:'12/03/1985',date:'15/10/2026',sexe:'f',t0:Date.now()});render();")
        # 0. PDF refusé avec explication
        await page.evaluate("aiDocImport(new File(['%PDF-1.4'],'cr.pdf',{type:'application/pdf'}))"); await page.wait_for_timeout(300)
        ok(L+"PDF : refusé avec la marche à suivre (capture d'écran)",any("capture" in d for d in dialogs) and await page.locator("#aidoc").count()==0)
        # 1. Onglet Document dans le panneau
        await page.evaluate("aiOpen('doc')"); await page.wait_for_timeout(200)
        ok(L+"onglet « Document ou image » avec import de photo",await page.locator("#ai_file").count()==1 and "image/*"==await page.get_attribute("#ai_file","accept"))
        await page.evaluate("document.getElementById('aipanel').remove()")
        # 2. Import : identité détectée et masquée sur l'appareil
        fini=await import_doc(page)
        ok(L+"lecture locale terminée",fini)
        await page.screenshot(path=os.path.join(ROOT,"tests","captures",f"{label}-doc-masquage.png"))
        auto=await page.evaluate("DOC.auto")
        ok(L+"identité repérée et masquée automatiquement",auto>=3,auto)
        ok(L+"envoi impossible tant que la vérification n'est pas cochée",await page.is_disabled("#ad_go"))
        # 3. Sans masque (tout annulé) : recadrage seul → envoi bloqué par la vérification finale
        while not await page.is_disabled("#ad_undo"): await page.click("#ad_undo"); await page.wait_for_timeout(100)
        ok(L+"sans recadrage ni masque : envoi impossible même coché",(await page.evaluate("DOC.edits"))==0 and (await page.check("#ad_ok") or True) and await page.is_disabled("#ad_go"))
        await page.evaluate("aiDocCrop({x:2,y:2,w:DOC.cv.width-4,h:DOC.cv.height-4});aiDocScreen();"); await page.wait_for_timeout(200)
        await page.click("#ad_go"); await page.wait_for_timeout(300); await idle(page)
        flag=await page.evaluate("DOC.flag")
        ok(L+"identité encore lisible : envoi bloqué, éléments listés",len(flag)>0 and await page.locator("#aisend").count()==0,flag)
        ok(L+"rien n'est parti",len(sent)==0)
        # 4. « Masquer ces zones » puis texte lu sur l'appareil, anonymisé
        await page.click("#ad_fix"); await page.wait_for_timeout(300)
        ok(L+"« Ce qui part » atteint après masquage",await go_until_sent(page))
        txt=await page.inner_text("#ai_sent") if await page.locator("#ai_sent").count() else ""
        ok(L+"mode texte : aucune identité dans le texte envoyé",txt and not any(x in txt for x in IDENT),[x for x in IDENT if x in txt])
        ok(L+"mode texte : les résultats partent",("CRP" in txt) or ("Hémoglobine" in txt),txt[-200:])
        ok(L+"mode texte : aucune image jointe",await page.locator("#aisend img.aiimg").count()==0)
        replies.append({"type":"Bilan biologique","resume":"Syndrome inflammatoire biologique.","resultats":["CRP 85 mg/l","AMOXICILLINE 1 g 3 fois par jour"],"ecg":"","antecedents":["Diabète de type 2"],"traitements":["METFORMINE 1000 mg matin et soir","Kardégic 75 mg"],"remarques":[]})
        await page.click("#ai_send"); await page.wait_for_timeout(900)
        body=sent[-1] if sent else ""
        ok(L+"requête texte sans identité ni image",body and not any(x in body for x in IDENT) and '"type": "image"' not in body and '"type":"image"' not in body)
        out=await page.inner_text("#ai_out") if await page.locator("#ai_out").count() else ""
        ok(L+"posologie du document jamais reprise",("AMOXICILLINE" not in out) and ("1000" not in out) and ("METFORMINE" in out),out[:400])
        await page.locator("[data-dacc=docs]").click(); await page.locator("[data-dacc=tt]").click(); await page.wait_for_timeout(300)
        cr=await page.evaluate("buildCR0(PACKS[0])")
        ok(L+"résultats ajoutés au compte rendu (documents consultés)","Documents consultés : Bilan biologique" in cr and "CRP 85 mg/l" in cr,cr[:200])
        tt=await page.evaluate("state.tt")
        ok(L+"traitements repris sans dose",any("METFORMINE" in t for t in tt) and not any("1000" in t or "mg" in t for t in tt),tt)
        await page.evaluate("document.getElementById('aipanel')&&document.getElementById('aipanel').remove()")
        # 5. Mode image : image masquée ré-encodée, sans métadonnées
        await import_doc(page)
        await page.check("#ad_ok"); await page.check("[name=ad_mode][value=image]"); await page.wait_for_timeout(100)
        ok(L+"mode image : « Ce qui part » atteint",await go_until_sent(page))
        ok(L+"mode image : l'image exacte est montrée avant envoi",await page.locator("#aisend img.aiimg").count()==1)
        await page.screenshot(path=os.path.join(ROOT,"tests","captures",f"{label}-doc-ce-qui-part.png"))
        n0=len(sent); replies.append({"type":"Bilan biologique","resume":"CRP élevée.","resultats":["CRP 85 mg/l"],"ecg":"","antecedents":[],"traitements":[],"remarques":[]})
        await page.click("#ai_send"); await page.wait_for_timeout(900)
        ok(L+"mode image : un seul envoi",len(sent)==n0+1)
        jb=json.loads(sent[-1]) if len(sent)>n0 else {}
        cont=jb.get("messages",[{}])[0].get("content",[])
        img=[c for c in cont if isinstance(c,dict) and c.get("type")=="image"]
        raw=base64.b64decode(img[0]["source"]["data"]) if img else b""
        ok(L+"mode image : JPEG ré-encodé, sans EXIF ni GPS",raw[:2]==b"\xff\xd8" and b"Exif" not in raw and b"GPS" not in raw and b"DUPONT" not in raw)
        txtpart=" ".join(c.get("text","") for c in cont if isinstance(c,dict))
        ok(L+"mode image : texte joint sans identité",not any(x in txtpart for x in IDENT))
        out=await page.inner_text("#ai_out") if await page.locator("#ai_out").count() else ""
        ok(L+"mode image : valeurs signalées à vérifier si absentes de la lecture locale","CRP" in out)
        # 6. Mode Aucun : pas d'onglet document
        await page.evaluate("document.getElementById('aipanel')&&document.getElementById('aipanel').remove();AI.cfg.mode='aucun';aiSave();aiOpen('doc')"); await page.wait_for_timeout(200)
        ok(L+"mode Aucun : pas d'import vers l'IA",await page.locator("#ai_file").count()==0)
        ok(L+"aucune erreur JS",len(errors)==0,errors[:3])
        await b.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8768"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        await run(375,812,"iphone"); await run(1280,900,"pc")
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_doc.md"),"w",encoding="utf-8").write("# Tests v41 — documents et images vers l'IA (lecture locale réelle, API simulée)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
