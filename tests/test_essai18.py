# Essai réel du 18/10/2026 : enfant de 22 mois, 13 kg, allergie aux pénicillines, fiche « Syndrome otite-conjonctivite » (et OMA enfant).
# Moteur Safari (WebKit, iPhone 13 émulé). Trois cas : pas d'allergie, allergie sans gravité (céphalosporines possibles), allergie grave.
# Contrôles : antibiotique retenu, ml + mg, durée 10 jours, question « Allergie grave ? » à un geste, AERIUS décoché,
# une seule forme par ligne, alerte « ne tient pas sur une page » absente, cachet sans chevauchement, marges A4 blanches dans le PDF,
# impression iPhone = partage du PDF (jamais la page web), page web non imprimable (@media print), fiches « à relire ».
# Lancer : python tests/test_essai18.py [webkit|chromium]
import asyncio, os, subprocess, time, sys, base64
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
ENGINE=sys.argv[1] if len(sys.argv)>1 else "webkit"
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
PORT=8812
async def unlock(page,uid,xp):
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.add_script_tag(content=f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=20000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=20000); await page.wait_for_timeout(800)
IDFAKE="""()=>{const c=document.createElement('canvas');c.width=900;c.height=760;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,900,760);g.strokeStyle='#1a3a8a';g.lineWidth=10;g.beginPath();g.arc(450,330,300,0,7);g.stroke();
  g.fillStyle='#1a3a8a';g.font='bold 54px sans-serif';g.textAlign='center';g.fillText('CACHET FICTIF',450,340);g.font='italic 60px serif';g.fillText('signature',450,700);
  identApply({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:c.toDataURL('image/png')});state.cachet=true;window.print=()=>{window.__pr=(window.__pr||0)+1;};
  window.__share=[];navigator.canShare=()=>true;navigator.share=(d)=>{window.__share.push((d.files||[]).map(f=>({n:f.name,t:f.type,s:f.size})));return Promise.resolve();};return IDENT.on;}"""
SETUP="""(a)=>{newPatient();Object.assign(state,{patient:'PETIT Lou',ddn:'18/12/2024',poids:'13',sexe:'f',date:'18/10/2026',allergie:a.al,allergieGrave:a.g,allergies:a.al?['Pénicillines']:[]});
  state.sel=PACKS.findIndex(p=>p.n===a.n);state.cot.lieu='visite';state.cachet=true;render();const P=currentPack();const L=[];
  P.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>L.push({t:x.t.slice(0,30),on:x.on,s:x.fill.s,miss:x.fill.miss}));});
  const st=P.s.filter(s=>s.k==='memo').flatMap(s=>s.l).map(l=>typeof l==='string'?l:l.t).filter(t=>/^Statut/.test(t));
  return {L,q:!!document.querySelector('.algrave'),st};}"""
PDFCHK="""async()=>{const out=PDFJOB.out||'';const css=document.createElement('style');css.id='hidestamp';
  const render=async(hide)=>{if(hide){css.textContent='#pdfstage .stamp,#pdfstage .sig{visibility:hidden!important}';document.head.appendChild(css);}else{const x=document.getElementById('hidestamp');if(x)x.remove();}
    return await pdfRenderPages(out,null,()=>false);};
  const vis=await render(false);const hid=await render(true);const x=document.getElementById('hidestamp');if(x)x.remove();
  const px=async(p,box)=>{const bm=await createImageBitmap(new Blob([p.jpg],{type:'image/jpeg'}));const c=document.createElement('canvas');c.width=bm.width;c.height=bm.height;const g=c.getContext('2d');g.drawImage(bm,0,0);
    const mm=bm.width/210;const b=box(bm.width,bm.height,mm,bm.width/p.pw);if(!b)return 0;const [zx,zy,zw,zh]=b.map(v=>Math.max(0,Math.round(v)));const d=g.getImageData(zx,zy,Math.max(1,zw),Math.max(1,zh)).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]+d[i+1]+d[i+2]<420)n++;return n;};
  const R=[];for(let i=0;i<hid.length;i++){const p=hid[i];const v=vis[i];
    const stamp=await px(p,(W,H,mm,k)=>p.zone?p.zone.map(z=>z*k):null);
    const top=await px(v,(W,H,mm)=>[0,0,W,8*mm]),bot=await px(v,(W,H,mm)=>[0,H-8*mm,W,8*mm]),left=await px(v,(W,H,mm)=>[0,0,8*mm,H]),right=await px(v,(W,H,mm)=>[W-8*mm,0,8*mm,H]);
    R.push({i,h:p.title||'',stamp,top,bot,left,right,ratio:+(v.h/v.w).toFixed(3),zone:!!p.zone});}
  const img=vis.map(p=>{let s='';const b=p.jpg;for(let i=0;i<b.length;i+=8192)s+=String.fromCharCode.apply(null,b.subarray(i,i+8192));return btoa(s);});
  return {R,img};}"""
N_OC="Syndrome otite-conjonctivite — enfant"; N_OMA="Otite moyenne aiguë — enfant"
CASES=[("sans-allergie",False,None,"AUGMENTIN","CLAMOXYL"),("allergie-sans-gravite",True,False,"ORELOX","ORELOX"),("allergie-grave",True,True,"BACTRIM","BACTRIM")]
def on(r,start):
    x=[y for y in r["L"] if y["on"] and y["t"].startswith(start)]
    return x[0]["s"] if x else ""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            bt=getattr(p,ENGINE); b=await bt.launch()
            dev=p.devices["iPhone 13"] if ENGINE=="webkit" else {"viewport":{"width":390,"height":844},"is_mobile":True,"has_touch":True,"device_scale_factor":3}
            for xp in (False,True):
                L=f"{ENGINE} iPhone · {'Express' if xp else 'mode complet'} : "
                ctx=await b.new_context(**dev)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
                await unlock(page,"e18"+("x" if xp else "c"),xp); await page.evaluate(IDFAKE)
                for tag,al,g,atb,atb_oma in CASES:
                    r=await page.evaluate(SETUP,{"n":N_OC,"al":al,"g":g})
                    sel=[y["t"] for y in r["L"] if y["on"] and y["t"].split(" ")[0] in ("AUGMENTIN","ORELOX","BACTRIM","CLAMOXYL")]
                    ok(L+f"otite-conjonctivite 22 mois 13 kg, {tag} : {atb} seul antibiotique coché",sel and len(sel)==1 and sel[0].startswith(atb),sel)
                    s=on(r,atb)
                    exp={"AUGMENTIN":"3,5 ml (soit 350 mg d'amoxicilline) 3 fois par jour","ORELOX":"1 dose-poids 13 kg (soit 6,5 ml, 52 mg) matin et soir","BACTRIM":"5 ml (soit 200 mg de sulfaméthoxazole) matin et soir"}[atb]
                    mx={"AUGMENTIN":"sans dépasser 10 ml par prise","ORELOX":"sans dépasser 400 mg par jour","BACTRIM":"sans dépasser 10 ml par prise"}[atb]
                    ok(L+f"{tag} : {atb} en ml et en mg, dose maximale, 10 jours (moins de 2 ans)",exp in s and mx in s and "pendant 10 jours" in s,s[:260])
                    ok(L+f"{tag} : question « Allergie grave ? » {'affichée' if al else 'absente'}",r["q"]==al,r["q"])
                    aer=[y for y in r["L"] if y["t"].startswith("AERIUS")]
                    ok(L+f"{tag} : AERIUS proposé en option décochée (si allergie avérée)",aer and not aer[0]["on"] and "si allergie avérée" in aer[0]["s"],aer)
                    ok(L+f"{tag} : une seule forme galénique par ligne (pas de « (ou suppositoire) »)",not [y for y in r["L"] if y["on"] and "(ou " in y["s"].split(" : ")[0]],[y["s"][:60] for y in r["L"] if y["on"]])
                    ok(L+f"{tag} : fiche otite-conjonctivite « à relire »",r["st"] and "à relire" in r["st"][-1],r["st"])
                    ro=await page.evaluate(SETUP,{"n":N_OMA,"al":al,"g":g})
                    so=[y["t"] for y in ro["L"] if y["on"] and y["t"].split(" ")[0] in ("AUGMENTIN","ORELOX","BACTRIM","CLAMOXYL")]
                    ok(L+f"OMA enfant 22 mois 13 kg (visite), {tag} : {atb_oma} retenu, 10 jours",so and len(so)==1 and so[0].startswith(atb_oma) and "pendant 10 jours" in on(ro,atb_oma),so)
                    ok(L+f"OMA enfant : fiche « à relire »",ro["st"] and "à relire" in ro["st"][-1],ro["st"])
                    if xp: continue
                    # aperçu et PDF de la fiche otite-conjonctivite
                    await page.evaluate(SETUP,{"n":N_OC,"al":al,"g":g})
                    await page.evaluate("printPack()"); await page.wait_for_timeout(500)
                    if await page.locator("#ciover").count():
                        await page.click("#ci_keep"); await page.click("#ci_print")
                    await page.wait_for_selector("#print .page",timeout=15000); await page.wait_for_timeout(1500)
                    warn=await page.evaluate("(document.querySelector('#print .fitwarn')||{}).textContent||''")
                    ok(L+f"{tag} : pas d'alerte « ne tient pas sur une page » (documents courts)",not warn,warn[:200])
                    ptxt=await page.evaluate("[...document.querySelectorAll('#print .page')].map(x=>x.innerText).join(' ')")
                    ok(L+f"{tag} : ordonnance imprimée sans « seringue graduée en kg » à côté d'une dose en ml, sans note médecin",("seringue graduée" not in ptxt) and ("allergie grave" not in ptxt) and ("indiqué" not in ptxt),ptxt[:300])
                    rr=await page.evaluate(PDFCHK)
                    bad=[x for x in rr["R"] if x["zone"] and x["stamp"]>60]
                    ok(L+f"{tag} : PDF, aucune ligne de texte sous le cachet ({len(rr['R'])} page(s))",not bad,bad)
                    mar=[x for x in rr["R"] if x["top"]>40 or x["right"]>40 or x["left"]>40 or x["bot"]>40]
                    ok(L+f"{tag} : PDF A4 (ratio 1,414), marges de 8 mm blanches en haut, à droite, à gauche et en bas",not mar and all(abs(x["ratio"]-1.414)<0.01 for x in rr["R"]),[(x["h"],x["top"],x["right"],x["left"],x["bot"],x["ratio"]) for x in rr["R"]])
                    for i,im in enumerate(rr["img"]):
                        open(os.path.join(OUT,f"essai18-{ENGINE}-{tag}-p{i+1}.jpg"),"wb").write(base64.b64decode(im))
                    # impression iPhone : partage du PDF, jamais window.print ni la page web
                    await page.evaluate("window.__pr=0;window.__share=[];")
                    for _ in range(40):
                        if await page.evaluate("!!(PDFJOB.file)"): break
                        await page.wait_for_timeout(250)
                    btn=page.locator("#pb_send")
                    ok(L+f"{tag} : bouton « 🖨 Imprimer » présent sur iPhone",await btn.count()>=1)
                    if await btn.count(): await btn.first.click(); await page.wait_for_timeout(600)
                    sh=await page.evaluate("({s:window.__share,p:window.__pr||0})")
                    ok(L+f"{tag} : impression = partage iOS du PDF seul (application/pdf), jamais la page web",sh["p"]==0 and sh["s"] and sh["s"][-1] and sh["s"][-1][0]["t"]=="application/pdf" and sh["s"][-1][0]["s"]>5000,sh)
                    await page.emulate_media(media="print")
                    vis=await page.evaluate("[...document.body.children].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id||e.className||e.tagName)")
                    await page.emulate_media(media="screen")
                    ok(L+f"{tag} : la page web elle-même ne s'imprime pas (seul le message renvoyant au PDF)",vis==["webnoprint"],vis)
                    await page.evaluate("document.body.classList.remove('printing');document.getElementById('print').innerHTML='';pdfCancel();render();")
                # un geste : « Oui » sur la question choisit BACTRIM
                await page.evaluate(SETUP,{"n":N_OC,"al":True,"g":None}); await page.wait_for_timeout(300)
                yes=page.locator("[data-algrave='1']").first
                if xp:
                    ok(L+"question « Allergie grave ? » visible dans l'Express sans ouvrir « Plus »",await yes.is_visible())
                else:
                    await page.evaluate("()=>{const d=document.querySelector('details.pmore');if(d)d.open=true;}")
                await yes.click(); await page.wait_for_timeout(300)
                sel=await page.evaluate("(()=>{const P=currentPack();const r=[];P.s.forEach((sh,si)=>{if(sh.k==='med')resolve(sh,si).forEach(x=>{if(x.on&&x.grp)r.push(x.t.split(' ')[0]);});});return {r,g:state.allergieGrave};})()")
                ok(L+"un geste « Oui » : allergie grave enregistrée, BACTRIM retenu",sel["g"] is True and sel["r"]==["BACTRIM"],sel)
                await page.locator("[data-algrave='0']").first.click(); await page.wait_for_timeout(300)
                sel=await page.evaluate("(()=>{const P=currentPack();const r=[];P.s.forEach((sh,si)=>{if(sh.k==='med')resolve(sh,si).forEach(x=>{if(x.on&&x.grp)r.push(x.t.split(' ')[0]);});});return {r,g:state.allergieGrave};})()")
                ok(L+"un geste « Non » : ORELOX retenu",sel["g"] is False and sel["r"]==["ORELOX"],sel)
                if xp:
                    await page.evaluate("()=>{const e=document.querySelector('.algrave');if(e)e.scrollIntoView({block:'center'});}"); await page.wait_for_timeout(200)
                    await page.screenshot(path=os.path.join(OUT,f"essai18-{ENGINE}-question-allergie-grave.png"))
                # balayage : aucune ligne cochée à deux formes galéniques, sur toutes les fiches, 13, 22 et 30 kg
                sw=await page.evaluate("""()=>{const bad=[];for(const w of [13,22,30]){for(let i=0;i<PACKS.length;i++){if(!PACKS[i].s.some(sh=>sh.k==='med'))continue;newPatient();Object.assign(state,{patient:'X',ddn:'01/01/2018',poids:String(w),sexe:'f'});state.sel=i;const p=currentPack();
                  p.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>{if(x.on&&/\\((ou|or) (sachet|suppositoire|comprimé|gélule|sirop)/i.test(x.fill.s.split(' : ')[0]))bad.push([PACKS[i].n,w,x.fill.s.slice(0,70)]);});});}}return bad;}""")
                ok(L+"toutes les fiches (13, 22, 30 kg) : jamais deux formes galéniques sur une ligne cochée",not sw,sw[:5])
                ok(L+"aucune erreur JS",not errors,errors[:3])
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_essai18.md"),"w",encoding="utf-8").write("# Essai du 18/10/2026 (22 mois, 13 kg, otite-conjonctivite) — "+ENGINE+"\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
