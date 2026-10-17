# Consignes du 17/10/2026, partie B (sécurité), sur TOUTES les fiches : cachet jamais recouvert ni texte masqué (B1),
# aucune prescription bloquée (B2), aucune phrase d'action non faite ni renvoi à un document absent (B3), IA document en texte seul (B4).
# Patients fictifs. 375 px (jour, nuit + grand texte) et ordinateur. Lancer : python tests/test_securite17.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:600])
PORT=8779

async def unlock(page):
    await page.goto(f"http://localhost:{PORT}/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testsecu17"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

# identité fictive en mémoire (jamais enregistrée) pour imprimer avec un vrai cachet
IDFAKE="""()=>{const c=document.createElement('canvas');c.width=600;c.height=300;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,600,300);g.strokeStyle='#1a3a8a';g.lineWidth=8;g.strokeRect(10,10,580,280);g.fillStyle='#1a3a8a';g.font='bold 40px sans-serif';g.fillText('CACHET FICTIF',120,160);
  identApply({nom:'Docteur TEST Fictif',adeli:'000000000',assoc:[],stamp:c.toDataURL('image/png')});state.cachet=true;window.print=()=>{};return IDENT.on;}"""

SWEEP="""async(range)=>{const res=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const idx=range?range:PACKS.map((_,i)=>i);
  for(const i of idx){const p0=PACKS[i];const nm=p0.n;const kid=/enfant|nourrisson|bébé|pédiatr/i.test(nm);const old=/âgé|gériatr|chute/i.test(nm);
    try{const e=document.getElementById('ciover');if(e)e.remove();}catch(e){}
    document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel();}catch(e){}
    Object.assign(state,{sel:i,obs:{},cst:{},actions:{},lo:{},gs:{},off:{},extra:{},libre:{},f:{},tt:[],copat:[],ciOver:null,patient:kid?'PETIT Lou':'MARTIN Jeanne',ddn:kid?'01/01/2019':(old?'03/04/1938':'05/06/1975'),date:'17/10/2026',sexe:/prostat|testic|homme/i.test(nm)?'m':'f',poids:kid?'20':'',grossesse:false,allait:false,photos:[]});
    try{autoAgePack();}catch(e){}
    let blocked='',ci=0;
    try{await printPack();}catch(e){blocked='exception : '+e.message;}
    for(let t=0;t<40&&!document.querySelector('#print .page');t++){const c=document.getElementById('ciover');
      if(c){ci++;const k=c.querySelector('#ci_keep');if(k&&!c.__k){c.__k=1;k.click();await sleep(30);}const pb=c.querySelector('#ci_print');if(pb){if(pb.disabled){blocked='bouton « imprimer » grisé à l\\'écran d\\'alerte';break;}pb.click();}}
      await sleep(60);}
    for(let t=0;t<30&&document.querySelector('#print .page')&&!document.querySelector('#print .printbar');t++)await sleep(50);
    await sleep(80);
    const pages=[...document.querySelectorAll('#print .page')];
    if(!pages.length&&!blocked)blocked='aucun aperçu';
    const hit=[],clip=[],over=[];let txt='';
    pages.forEach((pg,pi)=>{const fr=pg.querySelector('.frame');if(!fr)return;const h=pg.querySelector('h2');const t=(h?h.textContent:'Document')+' p'+(pi+1);
      const z=[...fr.querySelectorAll('.stamp,.sig')].map(e=>e.getBoundingClientRect()).filter(r=>r.height);
      const els=[...fr.querySelectorAll('p,li,h2,h3,td,th,.meta,div')].filter(e=>!e.closest('.stamp,.sig')&&!e.querySelector('p,li,div,td,.stamp,.sig')&&e.textContent.trim());
      z.forEach(r=>els.forEach(e=>{const b=e.getBoundingClientRect();if(b.height&&b.bottom>r.top+0.5&&b.top<r.bottom-0.5&&b.right>r.left+0.5&&b.left<r.right-0.5)hit.push(t+' : '+e.textContent.trim().slice(0,40));}));
      if(getComputedStyle(fr).overflow==='hidden'&&fr.scrollHeight>fr.clientHeight+1)clip.push(t);
      if(pg.dataset.over)over.push(t);txt+='\\n'+fr.innerText;});
    const warn=!!document.querySelector('#print .fitwarn');
    res.push({i,nm,blocked,ci,n:pages.length,hit,clip,over,warn,
      revus:/revu les médicaments|ont été revus|médicaments revus/i.test(txt),
      joint:/compte rendu (?:ci-)?joint|ci-joint (?:le |mon )?compte rendu|compte rendu en pièce jointe/i.test(txt),
      trou:/à compléter|\\[[^\\]]*\\]|\\{[a-z]+:/i.test(txt)});
  }
  document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel();}catch(e){}render();return res;}"""

async def sweep(b,w,h,th,big,label,sample=None):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; dialogs=[]
    page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:(dialogs.append(d.message),asyncio.ensure_future(d.accept())))
    await unlock(page)
    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();")
    ok(label+" : identité fictive avec cachet (en mémoire)",await page.evaluate(IDFAKE))
    n=await page.evaluate("PACKS.length")
    rng=None
    if sample: rng=list(range(0,n,max(1,n//sample)))
    res=[]
    chunk=40; idx=rng or list(range(n))
    for k in range(0,len(idx),chunk):
        res+=await page.evaluate(SWEEP,idx[k:k+chunk])
    L=f"{label} ({len(res)} fiches) : "
    bl=[(r["nm"],r["blocked"]) for r in res if r["blocked"] and not (("à la carte" in r["nm"] or "aide-mémoire" in r["nm"]) and r["blocked"]=="aucun aperçu")]  # aide-mémoire : écran seulement (17/10/2026)  # fiches « à la carte » vides : rien à imprimer, message à l'écran
    ok(L+"B2 aucune fiche bloquée à l'impression (alertes : maintien possible)",not bl,bl[:8])
    ok(L+"B2 aucune fenêtre système bloquante pendant l'impression",not dialogs,dialogs[:3])
    hit=[(r["nm"],r["hit"][:2]) for r in res if r["hit"]]
    ok(L+"B1 aucun texte sous le cachet ou la signature, sur tous les documents",not hit,hit[:6])
    cl=[(r["nm"],r["clip"]) for r in res if r["clip"]]
    ok(L+"B1 aucun texte masqué",not cl,cl[:6])
    ov=[(r["nm"],r["over"]) for r in res if r["over"] and not r["warn"]]
    ok(L+"B1 document trop long : toujours signalé à l'écran avant impression",not ov,ov[:6])
    rv=[r["nm"] for r in res if r["revus"]]
    ok(L+"B3 « médicaments revus » jamais imprimé si l'action n'est ni cochée ni dictée",not rv,rv[:6])
    jt=[r["nm"] for r in res if r["joint"]]
    ok(L+"B3 aucun renvoi à un compte rendu joint (non imprimé)",not jt,jt[:6])
    tr=[r["nm"] for r in res if r["trou"]]
    ok(L+"documents sans trou (« à compléter », crochet, gabarit non résolu)",not tr,tr[:8])
    ok(L+"aucune erreur JS",not errors,errors[:2])
    ovl=[(r["nm"],r["over"]) for r in res if r["over"]]
    print("   documents trop longs (signalés) :",len(ovl),ovl[:10])
    print("   fiches avec écran d'alerte :",sum(1 for r in res if r["ci"]))
    await ctx.close()


# B3 étendu (17/10/2026) : dans chaque courrier, « J'ai prescrit … » cite exactement les examens cochés (biologie, imagerie, ECG),
# sur toutes les fiches avec courrier, en réglage par défaut puis toutes les cases d'examen inversées.
SWEEP2="""async(range)=>{const res=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  const noise=/^(Résultats|Résultat|À faire|A faire|Prélèvement|Ordonnance|Bilan à|À jeun)|transmettre|messagerie|MSSanté|fax|cabinet SOS|laboratoire de ville/i;
  const STOP=['les','des','une','pour','avec','sur','dans','par','aux','sang','bilan','dosage','recherche','examen','test'];
  const key=t=>{const w=(norm(String(t).split(' : ')[0].replace(/\\([^)]*\\)/g,' ')).match(/[a-z0-9]{2,}/g)||[]).filter(w=>!STOP.includes(w)&&w.length>=3||/^(nfs|crp|ecg|tsh|bnp|vs|ast|alt|ggt|inr|tca|tp)$/.test(w));return w[0]||'';};
  const idx=range;
  for(const i of idx){const nm=PACKS[i].n;
    for(const flip of [false,true]){
      document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel();}catch(e){}
      try{const e=document.getElementById('ciover');if(e)e.remove();}catch(e){}
      const kid=/enfant|nourrisson|bébé|pédiatr/i.test(nm);
      Object.assign(state,{sel:i,obs:{},cst:{},actions:{},lo:{},gs:{},off:{},extra:{},libre:{},f:{},tt:[],copat:[],ciOver:null,patient:kid?'PETIT Lou':'MARTIN Jeanne',ddn:kid?'01/01/2019':'03/04/1938',date:'17/10/2026',sexe:'f',poids:kid?'20':'',photos:[]});
      try{autoAgePack();}catch(e){}
      const p=currentPack();
      if(flip)p.s.forEach((sh,si)=>{if(!/^(bio|img)$/.test(sh.k))return;resolve(sh,si).forEach(x=>{if(!x.grp)state.lo[x.key]=!x.on;});});
      const ck=[],un=[];p.s.forEach((sh,si)=>{if(state.off[si]||!/^(bio|img)$/.test(sh.k))return;resolve(sh,si).forEach(x=>{if(x.jr||x.fill.miss.length)return;const t=x.fill.s;if(sh.k==='bio'&&(noise.test(t)||t.length>=160))return;(x.on?ck:un).push(t);});});
      try{await printPack();}catch(e){}
      for(let t=0;t<40&&!document.querySelector('#print .page');t++){const c=document.getElementById('ciover');if(c){const k=c.querySelector('#ci_keep');if(k&&!c.__k){c.__k=1;k.click();await sleep(30);}const pb=c.querySelector('#ci_print');if(pb)pb.click();}await sleep(60);}
      await sleep(60);
      const letters=[...document.querySelectorAll('#print .page')].filter(pg=>{const h=pg.querySelector('h2');return h&&/Courrier/i.test(h.textContent);}).map(pg=>(pg.querySelector('.frame')||pg).innerText.replace(/\\s+/g,' '));
      for(const lt of letters){const m=lt.match(/J'ai prescrit[^.]*\\./);const sent=m?norm(m[0]):'';
        const ckTxt=norm(ck.join(' '));const miss=[],extra=[];
        if(sent){ck.forEach(t=>{const k=key(t);if(k&&!sent.includes(k))miss.push(t.slice(0,40));});
          un.forEach(t=>{const k=key(t);if(k&&sent.includes(k)&&!ckTxt.includes(k))extra.push(t.slice(0,40));});}
        if(/ECG/.test(m?m[0]:'')&&!ck.some(t=>/ECG/.test(t))&&!/ECG/.test(JSON.stringify(state.actions||{})))extra.push('ECG non coché');
        res.push({nm,flip,sent:m?m[0].slice(0,160):'',miss,extra});}
    }}
  document.body.classList.remove('printing');document.getElementById('print').innerHTML='';try{pdfCancel();}catch(e){}render();return res;}"""

async def sweep_presc(b):
    ctx=await b.new_context(viewport={"width":1280,"height":900})
    await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page); await page.evaluate(IDFAKE)
    idx=await page.evaluate("PACKS.map((p,i)=>p.s.some(s=>s.k==='let')&&p.s.some(s=>s.k==='bio'||s.k==='img')?i:-1).filter(i=>i>=0)")
    res=[]
    for k in range(0,len(idx),20): res+=await page.evaluate(SWEEP2,idx[k:k+20])
    n=await page.evaluate("PACKS.length")
    L=f"B3 courriers ({len(idx)} fiches avec courrier et examens sur {n}, réglage par défaut puis cases inversées) : "
    withs=[r for r in res if r["sent"]]
    ok(L+"« J'ai prescrit » cite tous les examens cochés",not [r for r in res if r["miss"]],[(r["nm"],r["flip"],r["miss"],r["sent"]) for r in res if r["miss"]][:6])
    ok(L+"« J'ai prescrit » ne cite aucun examen non coché",not [r for r in res if r["extra"]],[(r["nm"],r["flip"],r["extra"],r["sent"]) for r in res if r["extra"]][:6])
    ok(L+"phrases contrôlées",len(withs)>=10,len(withs))
    ok(L+"aucune erreur JS",not errors,errors[:2])
    print("   phrases « J'ai prescrit » contrôlées :",len(withs),"courriers :",len(res))
    await ctx.close()

async def b4(b,w,h,label):
    mob=w<500
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
    sent=[]
    async def handle(route):
        req=route.request
        if "api.anthropic.com" in req.url:
            if req.method=="OPTIONS": await route.fulfill(status=204,headers={"access-control-allow-origin":"*","access-control-allow-headers":"*"}); return
            sent.append(req.post_data or ""); await route.fulfill(status=200,headers={"access-control-allow-origin":"*","content-type":"application/json"},body=json.dumps({"content":[{"type":"text","text":"{}"}],"usage":{"input_tokens":1,"output_tokens":1}})); return
        if "localhost" in req.url: await route.continue_(); return
        await route.abort()
    await ctx.route("**/*",handle)
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page); L=label+" : "
    await page.evaluate("AI.key='sk-ant-test-b4-factice';AI.cfg.mode='partiel';aiSave();state.patient='MARTIN Jeanne';state.ddn='03/04/1938';render();")
    src=await page.evaluate("aiDocPrepare.toString()+aiSend.toString()")
    ok(L+"B4 aucun envoi d'image possible (code : pas de bloc image vers l'API)",'type:"image"' not in src and "'image'" not in src)
    await page.evaluate("aiOpen('doc')"); await page.wait_for_timeout(300)
    t=await page.evaluate("(document.getElementById('aipanel')||{}).innerText||''")
    ok(L+"B4 panneau Document : texte seul annoncé, jamais d'image",("texte" in t.lower()) and ("jamais" in t.lower()) and ("image masquée" not in t.lower()),t[:300])
    # document importé, lecture locale impossible (OCR indisponible) : envoi grisé avec la raison
    r=await page.evaluate("""async()=>{const c=document.createElement('canvas');c.width=400;c.height=300;const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,400,300);g.fillStyle='#000';g.font='20px sans-serif';g.fillText('Hémoglobine 12,1 g/dL',20,60);
      window.ocrLoad=async()=>{throw new Error('lecture locale indisponible (test)');};
      const blob=await new Promise(r=>c.toBlob(r,'image/png'));const f=new File([blob],'bio.png',{type:'image/png'});await aiDocImport(f);await new Promise(r=>setTimeout(r,600));
      const el=document.getElementById('aidoc');const b=el&&[...el.querySelectorAll('button')].find(x=>/Voir ce qui part/.test(x.textContent));return {txt:el?el.innerText:'',dis:b?b.disabled:null,title:b?(b.title||''):''};}""")
    ok(L+"B4 sans lecture locale : « Voir ce qui part » grisé, avec la raison",r["dis"] is True and ("lecture" in (r["txt"]+r["title"]).lower()),{k:r[k] for k in ("dis","title")} | {"txt":r["txt"][:200]})
    ok(L+"B4 rien n'est parti",len(sent)==0)
    if mob: await page.screenshot(path=os.path.join(OUT,"secu17-b4-document.png"))
    ok(L+"aucune erreur JS",not errors,errors[:2])
    await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await sweep_presc(b)
            if os.environ.get("ONLY")=="presc": await b.close(); return
            await sweep(b,1280,900,"day",False,"ordinateur")
            await sweep(b,375,812,"day",False,"iphone jour")
            await sweep(b,375,812,"night",True,"iphone nuit grand texte",sample=40)
            await b4(b,375,812,"iphone")
            await b4(b,1280,900,"ordinateur")
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_securite17.md"),"w",encoding="utf-8").write("# Tests sécurité du 17/10/2026 (B1 à B4), toutes les fiches\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:500]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
