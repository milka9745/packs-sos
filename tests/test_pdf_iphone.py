# PDF réellement produit par le moteur Safari (WebKit, iPhone 13 émulé) — 17/10/2026, essai réel du 17/10 :
# texte sous le cachet (courrier gériatre, ordonnance biologie, consignes tendinopathie d'Achille).
# Contrôle au pixel sur les pages JPEG du PDF : on refait le rendu avec le cachet invisible, et la zone du cachet doit rester blanche.
# Cachet fictif aux proportions d'un vrai tampon + signature (plus haut que large). Captures des pages produites.
# Lancer : python tests/test_pdf_iphone.py [webkit|chromium]
import asyncio, os, json, subprocess, time, sys, base64
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
ENGINE=sys.argv[1] if len(sys.argv)>1 else "webkit"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
PORT=8793
async def unlock(page,uid):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.add_script_tag(content="try{localStorage.setItem('sos_xp','false')}catch(e){}")
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=20000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=20000); await page.wait_for_timeout(800)
# cachet fictif : tampon rond + signature, 900 × 760 (proportions d'un cachet-signature scanné)
IDFAKE="""()=>{const c=document.createElement('canvas');c.width=900;c.height=760;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,900,760);g.strokeStyle='#1a3a8a';g.lineWidth=10;g.beginPath();g.arc(450,330,300,0,7);g.stroke();
  g.fillStyle='#1a3a8a';g.font='bold 54px sans-serif';g.textAlign='center';g.fillText('CACHET FICTIF',450,340);g.font='italic 60px serif';g.fillText('signature',450,700);
  identApply({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:c.toDataURL('image/png')});state.cachet=true;window.print=()=>{window.__pr=(window.__pr||0)+1;};return IDENT.on;}"""
CASES=[("chute-courrier-geriatre",["Chute du sujet âgé — bilan"],{"patient":"MARTIN Jeanne","ddn":"03/04/1938","sexe":"f"},"""(()=>{state.obs.hist="Chute de sa hauteur ce matin dans la salle de bain, relevée par sa fille au bout de vingt minutes, pas de perte de connaissance rapportée, douleur de hanche gauche à la marche, traitement par bisoprolol, ramipril, furosémide, alprazolam le soir.";})()"""),
       ("tendinopathie-achille",["Tendinopathie d'Achille"],{"patient":"DURAND Paul","ddn":"14/05/1975","sexe":"h"},""),
       ("bilan-biologie",["Fièvre prolongée / inexpliquée — bilan"],{"patient":"DURAND Paul","ddn":"14/05/1975","sexe":"h"},"")]
PDFCHK="""async()=>{const out=PDFJOB.out||'';const css=document.createElement('style');css.id='hidestamp';
  const render=async(hide)=>{if(hide){css.textContent='#pdfstage .stamp,#pdfstage .sig{visibility:hidden!important}';document.head.appendChild(css);}else{const x=document.getElementById('hidestamp');if(x)x.remove();}
    return await pdfRenderPages(out,null,()=>false);};
  const vis=await render(false);const hid=await render(true);const x=document.getElementById('hidestamp');if(x)x.remove();
  const dark=async(p)=>{const bm=await createImageBitmap(new Blob([p.jpg],{type:'image/jpeg'}));const c=document.createElement('canvas');c.width=bm.width;c.height=bm.height;const g=c.getContext('2d');g.drawImage(bm,0,0);
    if(!p.zone)return {n:0,z:null};const k=bm.width/p.pw;const [zx,zy,zw,zh]=p.zone.map(v=>Math.round(v*k));const d=g.getImageData(zx,zy,zw,zh).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]+d[i+1]+d[i+2]<420)n++;return {n,z:[zx,zy,zw,zh]};};
  const R=[];for(let i=0;i<hid.length;i++){const p=hid[i];const dk=await dark(p);R.push({i,h:p.title||'',zone:p.zone,dark:dk.n,over:!!p.over,stamp:!!p.hasStamp});}
  const img=vis.map(p=>{let s='';const b=p.jpg;for(let i=0;i<b.length;i+=8192)s+=String.fromCharCode.apply(null,b.subarray(i,i+8192));return btoa(s);});
  return {R,img,n:vis.length};}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            bt=getattr(p,ENGINE); b=await bt.launch()
            dev=p.devices["iPhone 13"] if ENGINE=="webkit" else {"viewport":{"width":390,"height":844},"is_mobile":True,"has_touch":True,"device_scale_factor":3}
            ctx=await b.new_context(**dev)
            await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
            page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await unlock(page,"pdfios"); ok(f"{ENGINE} iPhone : profil fictif avec cachet",await page.evaluate(IDFAKE))
            ua=await page.evaluate("navigator.userAgent"); print("   ",ua[:90])
            GROW="""(n)=>{const p=currentPack();p.s.forEach((sh,si)=>{if(sh.k==='bio'){state.extra[si]=Array.from({length:n},(_,i)=>['Ionogramme sanguin, créatininémie avec DFG (CKD-EPI)','Bilan hépatique (ASAT, ALAT, GGT, PAL, bilirubine)','TSH','Vitamine D (25-OH)','Albuminémie','Calcémie corrigée','Glycémie à jeun','Ferritine','Vitamine B12, folates','CRP'][i%10]+(i>=10?' (contrôle '+(i+1)+')':''));}
              if(sh.k==='cons'){state.libre[si]=Array(n).fill("Surveiller la douleur, reprendre la marche progressivement, glacer 15 minutes trois fois par jour, éviter la course et les sauts.").join(' ');}});
              state.obs.hist=(state.obs.hist||'')+Array(n).fill(" Pas de syncope, pas de douleur thoracique, vit seule à domicile avec passage infirmier le matin.").join('');render();}"""
            for tag,names,pat,extra in [(t+"-n"+str(n),nm,pt,ex+"|"+str(n)) for (t,nm,pt,ex) in CASES for n in (0,6,12,18,30)]:
                extra,grow=extra.rsplit("|",1)
                await page.evaluate("""(a)=>{newPatient();Object.assign(state,a.pat,{date:'17/10/2026'});const idx=a.names.map(n=>PACKS.findIndex(p=>p.n===n));state.sel=idx.length===1?idx[0]:idx;state.cachet=true;render();return idx;}""",{"pat":pat,"names":names})
                if extra: await page.evaluate(extra)
                await page.evaluate(GROW,int(grow))
                await page.evaluate("printPack()"); await page.wait_for_timeout(500)
                if await page.locator("#ciover").count():
                    await page.click("#ci_keep"); await page.click("#ci_print")
                await page.wait_for_selector("#print .page",timeout=15000); await page.wait_for_timeout(1500)
                r=await page.evaluate(PDFCHK)
                bad=[x for x in r["R"] if x["zone"] and x["dark"]>60]
                ok(f"{ENGINE} iPhone · {tag} : PDF produit, aucune ligne de texte dans la zone du cachet ({r['n']} page(s))",not bad,bad[:4])
                # chaque document (titre sans « (suite) ») : cachet ou signature sur sa dernière page, jamais sur une page suivie d'une suite
                docs=[];[docs.append([x]) if not x["h"].endswith("(suite)") else docs[-1].append(x) for x in r["R"]]
                ok(f"{ENGINE} iPhone · {tag} : cachet sur la dernière page de chaque document, et seulement là",all(d[-1]["zone"] and all(not y["zone"] for y in d[:-1]) for d in docs if any(y["zone"] for y in d) or True),[[ (y["h"],bool(y["zone"])) for y in d] for d in docs])
                nxt=[r["R"][i+1]["h"] if i+1<len(r["R"]) else "" for i in range(len(r["R"]))]
                ok(f"{ENGINE} iPhone · {tag} : chaque document finit par une page avec cachet ou signature",all(x["zone"] or nxt[i].endswith("(suite)") for i,x in enumerate(r["R"]) if not x["h"].startswith("Aide")),[(x["h"],bool(x["zone"])) for x in r["R"]])
                ok(f"{ENGINE} iPhone · {tag} : aucune page « Aide à l'interprétation » ni « Aide-mémoire » dans le PDF",not any(x["h"].startswith("Aide") for x in r["R"]),[x["h"] for x in r["R"]])
                for i,im in enumerate(r["img"]):
                    open(os.path.join(OUT,f"pdf-{ENGINE}-iphone-{tag}-p{i+1}.jpg"),"wb").write(base64.b64decode(im))
                await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")
            ok(f"{ENGINE} : aucune erreur JS",not errors,errors[:3])
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK"); sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
