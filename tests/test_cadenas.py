# -*- coding: utf-8 -*-
"""23/11/2026 — correctif « cadenas » (42g à la racine, 42f.2 dans test/) : verrouillage de l'application.
Ordinateur (identité d'ordinateur, 1280 px et fenêtre étroite 700 px) : le code n'est jamais retenu (aucune session sos_sess, F5 et
nouvel onglet redemandent le code, une sos_sess laissée par l'ancienne version est effacée au démarrage), champ du code en texte masqué
(jamais « mot de passe »), identifiant sans remplissage automatique, validation automatique seulement à la frappe chiffre par chiffre
(valeur posée d'un coup → reste verrouillé ; Entrée → déverrouille ; mauvais code → refusé), le cadenas verrouille les autres onglets
(BroadcastChannel), retour après 20 minutes sans activité ou par le bouton Précédent → verrouillé, dossier en cours retrouvé après le code.
Téléphone (identité iPhone, 375 px) : champ « mot de passe » et session de 20 minutes inchangés ; 🔒 dans la barre du haut sans ouvrir de
menu ; « Verrouiller l'écran » premier bouton du menu ⋯, visible sans défiler ; 🔒 dans l'en-tête de Tournée, Journal, Fin de garde,
Base médicaments et Patient validé.
Partout : résumé du patient, « Organiser ma fiche » et fenêtre antibiotiques ouverts puis verrouillage → seul l'écran de code répond
(document.elementFromPoint) ; bandeau « Nouvelle version » utilisable sur l'écran de code.
Avec un dossier de l'ancienne version (archive de la 42d) : écran du profil (identScreen) et aperçu avant impression identiques,
application en 42d → bandeau → 42g, même code, journal et réglages conservés.
Patients fictifs. Service worker bloqué, aucun appel extérieur.
Lancer : python tests/test_cadenas.py [<dossier de l'ancienne version>]   (sans argument, les comparaisons avec l'ancienne version sont sautées)
"""
import asyncio, os, re, sys, json, subprocess, time
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
OLD=sys.argv[1] if len(sys.argv)>1 and os.path.isdir(sys.argv[1]) else None
PORT=8832; PORT_OLD=8833; PORT_UPD=8834
B=f"http://localhost:{PORT}/"
UA_IPHONE="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
INIT="try{['','pst:'].forEach(p=>{localStorage.setItem(p+'sos_xpsug','true');if(localStorage.getItem(p+'sos_xp')===null)localStorage.setItem(p+'sos_xp','false');});}catch(e){}"  # écran complet (l'Express a sa suite)
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
def serve(d,port):
    p=subprocess.Popen([sys.executable,"-m","http.server",str(port)],cwd=d,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2); return p

async def no_garde(page):
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass
async def create(page,base,uid):
    """première ouverture : création du code (identifiant + 4 chiffres), clé de secours, profil de démonstration"""
    await page.goto(base+"index.html"); await page.wait_for_selector("#uid",timeout=20000); await page.wait_for_timeout(500)  # l'écran de création peut être redessiné juste après le premier affichage : laisser le démarrage se poser
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
    try: await page.wait_for_selector("#rec_ack",timeout=25000)
    except Exception:  # diagnostic puis nouvel essai (création du code lente quand plusieurs suites tournent ensemble)
        info=await page.evaluate("()=>({msg:(document.querySelector('.lockmsg')||{}).textContent||'',txt:((document.getElementById('lock')||{}).innerText||'').slice(0,160),uid:(document.getElementById('uid')||{}).value,p1:(document.getElementById('pin1')||{}).value,p2:(document.getElementById('pin2')||{}).value,btn:!!document.getElementById('pin_ok'),ua:navigator.userAgent.slice(0,40)})")
        print("    (création du code : pas de clé de secours après 25 s —",info,"— nouvel essai)")
        try: await page.screenshot(path=os.path.join(OUT,"cadenas-echec-creation.png"))
        except Exception: pass
        if info.get("btn"):
            await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
        await page.wait_for_selector("#rec_ack",timeout=60000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=60000); await page.wait_for_timeout(500)
    await no_garde(page)
async def enter_code(page,uid,how="click"):
    """écran de code affiché : identifiant + code ; « click » = bouton Déverrouiller, « enter » = touche Entrée, « type » = chiffres un à un"""
    await page.wait_for_selector("#pin1",timeout=15000)
    await page.fill("#uid",uid)
    if how=="type": await page.type("#pin1","1234",delay=70)
    else:
        await page.fill("#pin1","1234")
        if how=="enter": await page.press("#pin1","Enter")
        else:
            try: await page.click("#pin_ok",timeout=2000)
            except Exception: pass  # déjà validé (téléphone : code rempli d'un coup)
    await page.wait_for_selector("#lock",state="detached",timeout=30000); await page.wait_for_timeout(400)
    await no_garde(page)

STATE="({locked:!!document.getElementById('lock'),un:SEC.unlocked,keyNull:SEC.key===null,sess:localStorage.getItem('sos_sess')})"
# tout l'écran : rien d'autre que l'écran de code (et le bandeau de mise à jour ou la pastille TEST) ne répond au toucher
EF="""()=>{const W=innerWidth,H=innerHeight,bad=new Set();const sx=Math.max(24,Math.floor(W/14)),sy=Math.max(24,Math.floor(H/14));
 for(let x=4;x<W;x+=sx)for(let y=4;y<H;y+=sy){const e=document.elementFromPoint(x,y);if(!e)continue;if(e.closest('#lock')||e.closest('#updbar')||e.closest('#updall')||e.closest('#testbadge'))continue;
 bad.add((e.id?'#'+e.id:e.tagName.toLowerCase())+(typeof e.className==='string'&&e.className?'.'+e.className.split(' ')[0]:''));}return [...bad];}"""
HIT="""(sel)=>{const b=document.querySelector(sel);if(!b)return null;const r=b.getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
 return {x:r.left+r.width/2,y:r.top+r.height/2,w:Math.round(r.width),h:Math.round(r.height),hit:!!(e&&(e===b||b.contains(e))),inView:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth&&r.width>0};}"""
VERSION_FAKE={"version":"99z","label":"99z · 31/12 23:59","date":"2026-12-31","notes":["Essai du bandeau sur l'écran de code (fictif)."]}
# remise en haut de page, comme la routine de l'application : sur la mise en page iPhone (body.ios), c'est body qui défile, pas la fenêtre
SCROLL0="()=>{window.scrollTo(0,0);try{document.body.scrollTop=0;document.documentElement.scrollTop=0;if(document.scrollingElement)document.scrollingElement.scrollTop=0;const m=document.getElementById('main');if(m)m.scrollTop=0;}catch(e){}}"
VJSON=re.compile(r"localhost:\d+/(test/)?version\.json.*")

async def overlays(page,L,uid):
    """résumé du patient, Organiser ma fiche, fenêtre antibiotiques : ouverts puis verrouillage → seul l'écran de code répond"""
    await page.evaluate("()=>{const i=PACKS.findIndex(p=>/^Angine/.test(p.n));if(i>=0)state.sel=i;Object.assign(state,{patient:'CADENAS Essai',ddn:'01/01/1980',sexe:'f'});render();}")
    await page.wait_for_timeout(200)
    for name,open_js,sel in (("résumé du patient (synthScreen)","synthScreen()","#synthview"),("« Organiser ma fiche » (blkOrgScreen)","blkOrgScreen()","#blkorg"),("fenêtre antibiotiques (atbOver)","atbOver('<p>essai</p>')","#atbover")):
        try: await page.evaluate(open_js)
        except Exception as e: ok(L+name+" : ouverture",False,str(e)[:200]); continue
        await page.wait_for_timeout(300)
        shown=await page.evaluate("(s)=>{const e=document.querySelector(s);return !!(e&&e.getBoundingClientRect().width>0);}",sel)
        await page.evaluate("lockNow()"); await page.wait_for_timeout(350)
        bad=await page.evaluate(EF)
        vis=await page.evaluate("(s)=>{const e=document.querySelector(s);return e?getComputedStyle(e).visibility:'absent';}",sel)
        ok(L+name+" ouvert puis verrouillage : sur tout l'écran, seul l'écran de code répond (elementFromPoint)",shown and not bad and vis=="hidden",{"ouvert":shown,"hors #lock":bad[:6],"visibilité":vis})
        if sel=="#synthview" and "1280" in L and "racine" in L: await page.screenshot(path=os.path.join(OUT,"cadenas-verrou-ordinateur.png"))
        await enter_code(page,uid)
        await page.evaluate("(s)=>{const e=document.querySelector(s);if(e)e.remove();}",sel)
async def banner(page,ctx,L,uid):
    """bandeau « Nouvelle version » : toujours visible et utilisable sur l'écran de code"""
    await ctx.route(VJSON,lambda r:asyncio.ensure_future(r.fulfill(status=200,content_type="application/json",body=json.dumps(VERSION_FAKE,ensure_ascii=False))))
    await page.evaluate("UPD.info=null;UPD.collapsed=false;showUpdateBar();"); await page.wait_for_timeout(1200)
    shown=await page.evaluate("!!document.getElementById('upd_go')")
    await page.evaluate("lockNow()"); await page.wait_for_timeout(350)
    r=await page.evaluate("""()=>{const g=document.getElementById('upd_go'),b=document.getElementById('updbar');if(!g||!b)return {g:false};const rc=g.getBoundingClientRect();const e=document.elementFromPoint(rc.left+rc.width/2,rc.top+rc.height/2);
     return {g:true,vis:getComputedStyle(b).visibility,hit:!!(e&&(e===g||g.contains(e))),inView:rc.top>=0&&rc.bottom<=innerHeight&&rc.width>0,txt:b.textContent.slice(0,60),locked:!!document.getElementById('lock')};}""")
    ok(L+"bandeau « Nouvelle version » toujours visible et utilisable sur l'écran de code",shown and r.get("g") and r["vis"]=="visible" and r["hit"] and r["inView"] and r["locked"],r)
    await ctx.unroute(VJSON)
    await enter_code(page,uid)
    await page.evaluate("()=>{UPD.info=null;UPD.ready=false;const b=document.getElementById('updbar');if(b)b.remove();document.documentElement.classList.remove('upd-on');document.documentElement.style.removeProperty('--updh');}")
async def headers(page,L,phone,uid):
    """🔒 dans l'en-tête de Tournée, Journal, Fin de garde, Base médicaments, Patient validé"""
    for view,name in (("tour","Tournée"),("journal","Journal de garde"),("fin","Fin de garde"),("drugs","Base médicaments"),("valid","Patient validé")):
        try:
            await page.evaluate(SCROLL0)  # avant le rendu : la tournée restaure (en différé) la position de défilement enregistrée au rendu précédent
            if view=="valid":  # l'écran « Patient validé » affiche la dernière validation (VALID.last) : validation fictive
                await page.evaluate("()=>{VALID.last={ts:Date.now(),id:'t1',rev:1,lieu:'visite',of:'',exam:null,patient:'CADENAS Essai',nom:'CADENAS',prenom:'Essai',ddn:'01/01/1980',pack:'Angine (essai)',sheets:0,sent:false,cr:true,cot:null,stopId:'',stopLbl:'',snap:{sexe:'f'}};VALID.undoUntil=0;state.view='valid';render();}")
            else: await page.evaluate("(v)=>{state.view=v;render();}",view)
        except Exception as e: ok(L+name+" : ouverture",False,str(e)[:200]); continue
        await page.wait_for_timeout(350); await page.evaluate(SCROLL0); await page.wait_for_timeout(250)  # l'écran s'ouvre en haut de page (même remise à zéro que l'application)
        h=await page.evaluate("""()=>{const hd=document.querySelector('.jhead');if(!hd)return {hd:false};const b=hd.querySelector('.lkbtn');const h1=(hd.querySelector('h1')||{}).textContent||'';if(!b)return {hd:true,b:false,h1};
         const r=b.getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {hd:true,b:true,h1,hit:!!(e&&(e===b||b.contains(e))),inView:r.top>=0&&r.bottom<=innerHeight&&r.right<=innerWidth+1,w:Math.round(r.width),h:Math.round(r.height),x:r.left+r.width/2,y:r.top+r.height/2};}""")
        ok(L+name+" : 🔒 dans l'en-tête, visible et cliquable",h.get("b") and h["hit"] and h["inView"] and h["w"]>=40 and h["h"]>=36 and name.split(" ")[0] in h["h1"],h)
        if view=="tour" and phone and "racine" in L: await page.screenshot(path=os.path.join(OUT,"cadenas-tournee-iphone.png"))
        if view=="journal" and h.get("b"):
            await page.mouse.click(h["x"],h["y"]); await page.wait_for_timeout(700)
            st=await page.evaluate(STATE)
            ok(L+"Journal : un toucher sur 🔒 → écran de code, SEC.key effacée, sos_sess supprimée",st["locked"] and not st["un"] and st["keyNull"] and st["sess"] is None,st)
            await enter_code(page,uid)
    await page.evaluate("state.view='';render();"); await page.wait_for_timeout(200)

async def desk(b,base,width,label):
    ctx=await b.new_context(viewport={"width":width,"height":850},device_scale_factor=1,service_workers="block")
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await page.add_init_script(INIT)
    L=f"{label} · ordinateur {width} px : "; uid="cad"+str(width)+label[:3].replace("/","")
    await create(page,base,uid)
    dl=await page.evaluate("deskLike()")
    ok(L+"identité d'ordinateur reconnue (deskLike)",dl)
    # écran de code
    await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1",timeout=5000)
    f=await page.evaluate("""()=>{const p=document.getElementById('pin1'),u=document.getElementById('uid');return {type:p.getAttribute('type'),cls:p.className,name:p.getAttribute('name')||'',sec:getComputedStyle(p).getPropertyValue('-webkit-text-security'),
     pw:document.querySelectorAll('#lock input[type=password]').length,uac:u.getAttribute('autocomplete'),lp:p.getAttribute('data-lpignore'),locked:document.body.classList.contains('locked')};}""")
    ok(L+"écran de code : #pin1 champ texte masqué (type=text, pinmask, points), aucun input[type=password], #uid en autocomplete=off",f["type"]=="text" and "pinmask" in f["cls"] and f["sec"]=="disc" and f["pw"]==0 and f["uac"]=="off" and f["name"].startswith("c") and f["lp"]=="true",f)
    # valeur posée d'un coup + input → reste verrouillé ; Entrée → déverrouille
    await page.fill("#uid",uid)
    await page.evaluate("()=>{const p=document.getElementById('pin1');p.value='1234';p.dispatchEvent(new Event('input',{bubbles:true}));}"); await page.wait_for_timeout(1500)
    st=await page.evaluate(STATE)
    ok(L+"code posé d'un coup (collé ou rempli par le navigateur) + événement input : reste verrouillé",st["locked"] and not st["un"],st)
    await page.press("#pin1","Enter")
    try: await page.wait_for_selector("#lock",state="detached",timeout=30000); ent=True
    except Exception: ent=False
    ok(L+"Entrée : déverrouille",ent and await page.evaluate("SEC.unlocked&&!!SEC.key"))
    await no_garde(page)
    s1=await page.evaluate("localStorage.getItem('sos_sess')")
    await page.mouse.click(8,8); await page.keyboard.press("Shift"); await page.wait_for_timeout(400)
    s2=await page.evaluate("localStorage.getItem('sos_sess')")
    ok(L+"localStorage.sos_sess n'existe jamais (après déverrouillage, après activité)",s1 is None and s2 is None,(s1,s2))
    # chiffres un à un → validé au dernier
    await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1")
    await page.fill("#uid",uid); await page.type("#pin1","1234",delay=70)
    try: await page.wait_for_selector("#lock",state="detached",timeout=30000); typed=True
    except Exception: typed=False
    ok(L+"chiffres tapés un à un : validé au dernier chiffre (ni Entrée ni clic)",typed)
    await no_garde(page)
    # mauvais code → refusé
    await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1")
    await page.fill("#uid",uid); await page.fill("#pin1","9999"); await page.click("#pin_ok"); await page.wait_for_timeout(1500)
    m=await page.evaluate("()=>({msg:(document.querySelector('.lockmsg')||{}).textContent||'',locked:!!document.getElementById('lock'),un:SEC.unlocked,v:document.getElementById('pin1').value})")
    ok(L+"mauvais code : refusé (« Identifiant ou code incorrect »), champ vidé",m["locked"] and not m["un"] and "incorrect" in m["msg"] and m["v"]=="",m)
    await enter_code(page,uid)
    # retour après 20 minutes sans activité (simulé) ; retour par le bouton Précédent (pageshow persisted)
    await page.evaluate("LOCK_LAST=Date.now()-21*60*1000;document.dispatchEvent(new Event('visibilitychange'));"); await page.wait_for_timeout(400)
    st=await page.evaluate(STATE)
    ok(L+"fenêtre retrouvée après 20 min sans activité (simulé) : verrouillée",st["locked"] and not st["un"] and st["keyNull"],st)
    await enter_code(page,uid)
    await page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));"); await page.wait_for_timeout(400)
    st=await page.evaluate(STATE)
    ok(L+"retour par le bouton Précédent (page restaurée) : verrouillée",st["locked"] and not st["un"],st)
    await enter_code(page,uid)
    # patient en cours, F5 → code redemandé → dossier retrouvé
    await page.evaluate("()=>{const i=PACKS.findIndex(p=>/^Angine/.test(p.n));state.sel=i;Object.assign(state,{patient:'CADENAS Essai',ddn:'01/01/1980',sexe:'f'});render();draftSaveNow();}"); await page.wait_for_timeout(900)
    await page.reload(); await page.wait_for_timeout(1800)
    asked=await page.evaluate("!!document.getElementById('pin1')&&!document.getElementById('pin2')&&!SEC.unlocked")
    ok(L+"F5 sans verrouiller : code redemandé (aucune session gardée)",asked)
    await enter_code(page,uid)
    pat=await page.evaluate("({p:state.patient,ddn:state.ddn,sel:state.sel!==null&&state.sel!==undefined})")
    ok(L+"patient en cours, F5, code : dossier retrouvé tel quel (nom, naissance, fiche)",pat["p"]=="CADENAS Essai" and pat["ddn"]=="01/01/1980" and pat["sel"],pat)
    # sos_sess laissée par l'ancienne version → effacée au démarrage
    await page.evaluate("localStorage.setItem('sos_sess',JSON.stringify({k:'AAAA',ts:Date.now()}))")
    await page.reload(); await page.wait_for_timeout(1800)
    g=await page.evaluate("({sess:localStorage.getItem('sos_sess'),asked:!!document.getElementById('pin1'),un:SEC.unlocked})")
    ok(L+"sos_sess laissée par l'ancienne version : effacée au démarrage, code demandé",g["sess"] is None and g["asked"] and not g["un"],g)
    await enter_code(page,uid)
    # nouvel onglet → code redemandé ; deux onglets déverrouillés : 🔒 dans l'un → l'autre se verrouille
    p2=await ctx.new_page(); await p2.add_init_script(INIT); await p2.goto(base+"index.html"); await p2.wait_for_timeout(1800)
    ok(L+"nouvel onglet : code redemandé",await p2.evaluate("!!document.getElementById('pin1')&&!SEC.unlocked"))
    await enter_code(p2,uid)
    await page.evaluate("state.view='journal';render();"); await page.wait_for_timeout(400)
    h=await page.evaluate(HIT,".jhead [data-lock]")
    ok(L+"Journal : 🔒 dans l'en-tête, cliquable",h and h["hit"] and h["inView"],h)
    if h: await page.mouse.click(h["x"],h["y"]); await page.wait_for_timeout(900)
    st=await page.evaluate(STATE); st2=await p2.evaluate(STATE)
    ok(L+"clic sur 🔒 : écran de code, SEC.key effacée, sos_sess absente",st["locked"] and not st["un"] and st["keyNull"] and st["sess"] is None,st)
    ok(L+"deux onglets déverrouillés : le clic sur 🔒 dans l'un verrouille l'autre (BroadcastChannel)",st2["locked"] and not st2["un"] and st2["keyNull"],st2)
    await p2.close()
    await enter_code(page,uid)
    await headers(page,L,False,uid)
    await overlays(page,L,uid)
    await banner(page,ctx,L,uid)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3])
    await ctx.close()

async def phone(b,base,label):
    ctx=await b.new_context(viewport={"width":375,"height":812},device_scale_factor=2,is_mobile=True,has_touch=True,user_agent=UA_IPHONE,service_workers="block")
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await page.add_init_script(INIT)
    L=f"{label} · iPhone 375 px : "; uid="cadi"+label[:3].replace("/","")
    await create(page,base,uid)
    ok(L+"identité iPhone reconnue (deskLike faux)",not await page.evaluate("deskLike()"))
    await page.evaluate("lockNow()"); await page.wait_for_selector("#pin1",timeout=5000)
    t=await page.evaluate("({type:document.getElementById('pin1').getAttribute('type'),uac:document.getElementById('uid').getAttribute('autocomplete'),pw:document.querySelectorAll('#lock input[type=password]').length})")
    ok(L+"écran de code : #pin1 reste un champ « mot de passe », identifiant en autocomplete=username (inchangé)",t["type"]=="password" and t["uac"]=="username" and t["pw"]==1,t)
    await page.fill("#uid",uid); await page.fill("#pin1","1234")
    try: await page.wait_for_selector("#lock",state="detached",timeout=30000); auto=True
    except Exception: auto=False
    ok(L+"code rempli d'un coup : validé aussitôt (inchangé au téléphone)",auto)
    await no_garde(page)
    await page.wait_for_timeout(600)
    ok(L+"session de 20 minutes écrite (sos_sess)",await page.evaluate("!!localStorage.getItem('sos_sess')"))
    await page.evaluate("LOCK_LAST=Date.now()-21*60*1000;document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));"); await page.wait_for_timeout(400)
    ok(L+"retour sur la fenêtre, page restaurée : ne verrouille pas au téléphone (règle de l'ordinateur seulement)",await page.evaluate("SEC.unlocked&&!document.getElementById('lock')"))
    await page.reload(); await page.wait_for_timeout(2200)
    ok(L+"rechargement sans verrouiller : rouvre sans code (20 minutes, inchangé)",await page.evaluate("!document.getElementById('lock')&&SEC.unlocked"))
    await no_garde(page)
    # barre du haut : 🔒 à côté de ⋯, sans menu
    bar=await page.evaluate("""()=>{const b=document.querySelector('.jbar.phone .lkbtn');if(!b)return null;const r=b.getBoundingClientRect();const e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);const m=document.getElementById('more_btn');const rm=m?m.getBoundingClientRect():null;const j=document.getElementById('jmenu');
     return {x:r.left+r.width/2,y:r.top+r.height/2,w:Math.round(r.width),h:Math.round(r.height),hit:!!(e&&(e===b||b.contains(e))),inView:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth,beforeMore:rm?r.right<=rm.left+1:null,menuHidden:j?j.hidden:true,ver:!!document.querySelector('.jbar.phone .appver')};}""")
    ok(L+"🔒 visible dans la barre du haut, à gauche de ⋯, sans ouvrir de menu (≥ 40 px)",bar and bar["hit"] and bar["inView"] and bar["beforeMore"] and bar["menuHidden"] and bar["w"]>=40,bar)
    if "racine" in label: await page.screenshot(path=os.path.join(OUT,"cadenas-barre-iphone.png"))
    if bar: await page.mouse.click(bar["x"],bar["y"]); await page.wait_for_timeout(700)
    st=await page.evaluate(STATE)
    ok(L+"un toucher sur 🔒 : écran de code, SEC.key effacée, sos_sess supprimée",st["locked"] and not st["un"] and st["keyNull"] and st["sess"] is None,st)
    await enter_code(page,uid,"type")
    # menu ⋯ : « Verrouiller l'écran » en premier, visible sans défiler
    await page.click("#more_btn"); await page.wait_for_timeout(450)
    mn=await page.evaluate("""()=>{const m=document.getElementById('jmenu');if(!m||m.hidden)return {open:false};const first=m.querySelector('button');const lk=document.getElementById('lock_now');const r=lk?lk.getBoundingClientRect():null;const e=r?document.elementFromPoint(r.left+r.width/2,r.top+r.height/2):null;
     const all=[...m.querySelectorAll('button')].map(b=>b.id||b.textContent.trim().slice(0,22));return {open:true,firstIsLock:first===lk,rank:all.indexOf('lock_now')+1,n:all.length,inView:!!(r&&r.top>=0&&r.bottom<=innerHeight),scroll:m.scrollTop,hit:!!(e&&lk&&(e===lk||lk.contains(e))),txt:lk?lk.textContent.trim():'',x:r?r.left+r.width/2:0,y:r?r.top+r.height/2:0};}""")
    ok(L+"menu ⋯ : « Verrouiller l'écran » est le premier bouton, visible sans faire défiler",mn.get("open") and mn["firstIsLock"] and mn["rank"]==1 and mn["inView"] and mn["scroll"]==0 and mn["hit"] and "Verrouiller" in mn["txt"],mn)
    if "racine" in label: await page.screenshot(path=os.path.join(OUT,"cadenas-menu-iphone.png"))
    if mn.get("open"): await page.mouse.click(mn["x"],mn["y"]); await page.wait_for_timeout(700)
    st=await page.evaluate(STATE)
    ok(L+"menu ⋯ → Verrouiller l'écran : écran de code, sos_sess supprimée",st["locked"] and not st["un"] and st["keyNull"] and st["sess"] is None,st)
    await enter_code(page,uid,"type")
    await headers(page,L,True,uid)
    await overlays(page,L,uid)
    await banner(page,ctx,L,uid)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3])
    await ctx.close()

# ----- comparaisons avec l'ancienne version (archive de la 42d) -----
PRINT_SETUP="""()=>{newPatient();Object.assign(state,{patient:'CADENAS Essai',ddn:'01/01/1980',sexe:'f',date:'16/10/2026',t0:1760600000000});render();}"""
PAGES="""(re)=>{const i=PACKS.findIndex(p=>new RegExp(re).test(p.n));if(i<0)return 'fiche absente '+re;state.sel=i;state.off={};state.lo={};state.gs={};state.edits={};state.f={};state.libre={};state.extra={};render();
 const r=buildPages(currentPack(),true);const h=x=>typeof x==='string'?x:(x&&x.outerHTML)||JSON.stringify(x);return PACKS[i].n+'\\n'+(Array.isArray(r)?r.map(h).join('\\n'):h(r));}"""
def norm(h):
    h=re.sub(r"v?42[a-z](?:\.\d+)?(?: · (?:main|test) · \d\d/\d\d \d\d:\d\d)?","VER",h)
    h=re.sub(r"\d\d/\d\d/\d{4}(?: à \d\d:\d\d)?","DATE",h); h=re.sub(r"\b\d\d:\d\d\b","HH:MM",h)
    return h
async def compare_old(b):
    srv=serve(OLD,PORT_OLD)
    try:
        ctx=await b.new_context(viewport={"width":1280,"height":850},device_scale_factor=1,service_workers="block")
        await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
        po=await ctx.new_page(); pn=await ctx.new_page(); errs=[]
        for p in (po,pn): await p.add_init_script(INIT); p.on("pageerror",lambda e:errs.append(str(e))); p.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await create(po,f"http://localhost:{PORT_OLD}/","cmpold"); await create(pn,B,"cmpnew")
        vo=await po.evaluate("APP_BUILD.v"); vn=await pn.evaluate("APP_BUILD.v")
        print(f"    (ancienne version {vo}, nouvelle {vn})")
        for p in (po,pn): await p.evaluate(PRINT_SETUP); await p.wait_for_timeout(200)
        diffs=[]; n=0
        for rx in ("^Angine","^Cystite simple","^Lombalgie","^Gastro","^Otite"):
            a=await po.evaluate(PAGES,rx); c=await pn.evaluate(PAGES,rx)
            if a.startswith("fiche absente") or c.startswith("fiche absente"): diffs.append(rx+" : "+a[:40]+" / "+c[:40]); continue
            n+=1
            if norm(a)!=norm(c):
                A,C=norm(a),norm(c); k=next((i for i in range(min(len(A),len(C))) if A[i]!=C[i]),min(len(A),len(C)))
                diffs.append(rx+" : différence à %d (%r … / %r …)"%(k,A[k:k+60],C[k:k+60]))
        ok(f"aperçu avant impression identique à l'ancienne version ({vo} → {vn}, {n} fiches, patient fictif)",n>=4 and not diffs,diffs[:3])
        io_=[]
        for p in (po,pn):
            await p.evaluate("identScreen('activate','');"); await p.wait_for_timeout(300)
            io_.append(await p.evaluate("()=>{const l=document.querySelector('#lock .lockbox');return l?l.innerHTML:'';}"))
        ok(f"écran du profil (identScreen) identique à l'ancienne version ({vo} → {vn})",io_[0] and norm(io_[0])==norm(io_[1]),(len(io_[0]),len(io_[1])))
        ok("comparaisons : aucune erreur JavaScript",not errs,errs[:3])
        await ctx.close()
    finally: srv.terminate()
async def update(b):
    """application en 42d (ancienne version) : bandeau « Nouvelle version » → 42g, même code, journal et réglages conservés"""
    srv=serve(OLD,PORT_UPD); base=f"http://localhost:{PORT_UPD}/"
    try:
        ctx=await b.new_context(viewport={"width":1280,"height":850},device_scale_factor=1,service_workers="block")
        await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
        page=await ctx.new_page(); errs=[]; page.on("pageerror",lambda e:errs.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
        await page.add_init_script(INIT)
        await create(page,base,"cadupd")
        vo=await page.evaluate("APP_BUILD.v")
        w=await page.evaluate("""()=>{newPatient();Object.assign(state,{patient:'CADENAS Avant',ddn:'05/05/1975',sexe:'h'});const i=PACKS.findIndex(p=>/^Lombalgie/.test(p.n));state.sel=i;journalUpsert(currentPack());journalSave();localStorage.setItem('sos_theme','night');return JOURNAL.length;}""")
        for _ in range(20):
            if await page.evaluate("!!localStorage.getItem('sos_journal_enc')"): break
            await page.wait_for_timeout(300)
        ok(f"ancienne version ({vo}) : un patient fictif au journal, thème nuit",w>=1)
        srv.terminate(); srv.wait(); srv=serve(ROOT,PORT_UPD)
        await page.evaluate("UPD.info=null;UPD.collapsed=false;showUpdateBar();"); await page.wait_for_timeout(1500)
        txt=await page.evaluate("(document.getElementById('updbar')||{}).textContent||''")
        nv=json.load(open(os.path.join(ROOT,"version.json"),encoding="utf-8")).get("version","")
        ok(f"application en {vo} : le bandeau « Nouvelle version » annonce la {nv} avec ses notes",nv in txt and "Cadenas" in txt,txt[:160])
        await page.reload(); await page.wait_for_timeout(1800)  # le service worker est bloqué dans la suite : la mise à jour réelle passe par updGo → skipWaiting → rechargement
        asked=await page.evaluate("!!document.getElementById('pin1')&&!document.getElementById('pin2')")
        await enter_code(page,"cadupd")
        r=await page.evaluate("({v:APP_BUILD.v,n:JOURNAL.length,pat:JOURNAL.some(e=>e.patient==='CADENAS Avant'),theme:localStorage.getItem('sos_theme'),sess:localStorage.getItem('sos_sess')})")
        ok(f"{vo} → {nv} : code redemandé (ordinateur) et accepté, journal et réglages conservés, aucune session écrite",asked and r["v"]==nv and r["pat"] and r["theme"]=="night" and r["sess"] is None,r)
        ok("mise à jour : aucune erreur JavaScript",not errs,errs[:3])
        await ctx.close()
    finally: srv.terminate()

async def main():
    srv=serve(ROOT,PORT)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            only=os.environ.get("CADENAS_ONLY","")  # mise au point : « desk », « phone », « old » (vide = tout)
            for base,label in ((B,"racine"),(B+"test/","test/")):
                if not only or "desk" in only:
                    await desk(b,base,1280,label)
                    if label=="racine": await desk(b,base,700,label)
                if not only or "phone" in only: await phone(b,base,label)
            if only and "old" not in only: pass
            elif OLD:
                await compare_old(b); await update(b)
            else: print("    (pas de dossier de l'ancienne version : comparaisons et mise à jour sautées)")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
