# -*- coding: utf-8 -*-
"""09/11/2026 — bandeau « Nouvelle version » (bug 42b.1 sur iPhone : trop haut, pas de défilement, boutons hors écran).
À 375 px (iPhone), jour et nuit, texte normal et grand texte, puis iPhone SE en paysage (568 × 320) :
- boutons « Mettre à jour maintenant » et « Plus tard » en tête du bandeau, entièrement dans l'écran, au-dessus de la liste ;
- « Ce qui change » : 3 lignes courtes au plus (une ligne chacune, coupée par « … ») et lien « Voir tout » ;
- « Voir tout » : fenêtre défilable avec toutes les notes en texte complet, fermée par « Fermer », Échap ou un toucher à côté ;
- hauteur du bandeau ≤ 40 % de l'écran, défilement interne de la liste au-delà (paysage) ; l'écran commence sous le bandeau ;
- « Plus tard » réduit le bandeau, il revient au retour sur l'écran principal ;
- règle gardée : jamais de mise à jour automatique pendant une consultation (controllerchange → attente ; « Mettre à jour » demande confirmation).
version.json simulé (notes longues fictives) ; service worker bloqué ; aucun appel extérieur. Lancer : python tests/test_updbar.py"""
import asyncio, os, re, json, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures"); os.makedirs(OUT,exist_ok=True)
PORT=8819
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:900])

NOTES=[
 "Fiches de régulation : le nom est lu sur la ligne sous « INFORMATIONS PATIENT » (plus jamais « CH G »), ancienne et nouvelle présentation ; ligne illisible → nom vide et « nom non lu » ; l'heure d'appel et l'attente de la fiche alimentent l'alerte « attend depuis plus de 2 h » et l'ordre de la tournée (patients qui attendent placés avant les autres, après les priorités).",
 "Tournée : une nouvelle demande est intégrée d'elle-même au meilleur rang (depuis ma position, vers le point d'arrivée, dans l'heure limite), sans question ; la carte garde une ligne (« intégrée en 3e position, + 19 min sur l'arrivée au cabinet ») et deux boutons, Appeler et Priorité ; « Rendre à la régulation » dans « Plus » ; retrait ou validation → ordre recalculé en silence, une ligne discrète s'il change.",
 "Champ « Nom Prénom » : l'espace s'écrit normalement (iPhone, clavier et dictée) ; seule Entrée (ou OK) passe à la date de naissance ; à la sortie du champ le nom passe en capitales et le prénom en capitale initiale, « Prénom NOM » reconnu quand le nom est en capitales, particules gardées avec le nom, bouton ⇄ pour inverser.",
 "Doses au poids de l'enfant revues ligne par ligne sur les RCP et la HAS, 5 poids testés par ligne : TIORFAN jamais « 3 sachets », VOGALÈNE suppositoire par tranche avec la dose maximale par jour, jamais sous 7,5 kg, ondansétron 2 / 4 / 8 mg ; la règle RCP s'affiche à l'écran et ne s'imprime jamais.",
 "Impression : la fenêtre d'impression s'ouvre tout de suite sur l'aperçu (un seul bouton Imprimer), PDF seulement pour « Enregistrer en PDF » ; sur iPhone, PDF partagé avec barre de progression ; une page par document, aucun champ vide.",
 "Fiche patient : bloc identité en tête (Nom Prénom · Naissance · Sexe F/M · Poids) à la couleur du mode, allergies et traitements juste dessous avec les propositions des documents scannés à valider d'un toucher, options en petit ; en Visite, l'identité se remplit depuis la fiche de régulation."
]
VERSION={"version":"42b.9-test","label":"42b.9 · 09/11 13:00","date":"2026-11-09","notes":NOTES}

async def unlock(page,base,uid):
    await page.add_init_script("try{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','false');}catch(e){}")
    await page.goto(base+"index.html"); await page.wait_for_selector("#uid",timeout=20000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234"); await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=60000); await page.check("#rec_ack"); await page.click("#rec_done")  # 60 s : création du code lente quand plusieurs suites tournent ensemble
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=60000); await page.wait_for_timeout(600)
    try:
        pg=page.get_by_text("Pas de garde",exact=True)
        if await pg.count(): await pg.first.click(); await page.wait_for_timeout(300)
    except Exception: pass

MEASURE="""()=>{const R=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {t:Math.round(r.top),b:Math.round(r.bottom),l:Math.round(r.left),r:Math.round(r.right),h:Math.round(r.height),w:Math.round(r.width)};};
  const b=document.getElementById('updbar');if(!b)return {err:'pas de bandeau'};const H=window.innerHeight,W=document.documentElement.clientWidth;
  const go=document.getElementById('upd_go'),later=document.getElementById('upd_later'),ul=b.querySelector('ul'),all=document.getElementById('upd_all'),bd=b.querySelector('.ubd');
  const lis=[...b.querySelectorAll('li')].map(li=>{const cs=getComputedStyle(li);return {h:Math.round(li.getBoundingClientRect().height),fs:parseFloat(cs.fontSize),cut:li.scrollWidth>li.clientWidth+1,txt:li.textContent.slice(0,30)};});
  const j=document.querySelector('.jbar.phone')||document.querySelector('.jbar');const jr=R(j);let jhit=false;if(jr){const el=document.elementFromPoint(Math.min(W-10,jr.l+Math.min(40,jr.w/2)),Math.min(H-2,jr.t+Math.min(jr.h/2,20)));jhit=!!(el&&j.contains(el));}
  const updh=getComputedStyle(document.documentElement).getPropertyValue('--updh').trim();const pad=parseFloat(getComputedStyle(document.body).paddingTop);
  return {H,W,bar:R(b),fs:parseFloat(getComputedStyle(b).fontSize),bg:getComputedStyle(b).backgroundColor,go:R(go),later:R(later),ul:R(ul),all:R(all),allVisible:!!(all&&all.offsetParent!==null),li:lis,
    scrollW:document.documentElement.scrollWidth,jbar:jr,jhit,updh,pad:Math.round(pad),bdScroll:bd?bd.scrollHeight>bd.clientHeight+1:false,bdH:bd?Math.round(bd.clientHeight):0,
    uw:!!b.querySelector('.uw'),txt:b.innerText,size:document.documentElement.getAttribute('data-size'),theme:document.documentElement.getAttribute('data-theme'),cls:b.className};}"""

MODAL="""(notes)=>{const R=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {t:Math.round(r.top),b:Math.round(r.bottom),l:Math.round(r.left),r:Math.round(r.right),h:Math.round(r.height),w:Math.round(r.width)};};
  const o=document.getElementById('updall');if(!o)return {err:'pas de fenêtre'};const H=window.innerHeight,W=document.documentElement.clientWidth;const p=o.querySelector('.uap'),bd=o.querySelector('.uab'),x=document.getElementById('updall_x'),g=document.getElementById('updall_go');
  const txt=bd.innerText;return {H,W,panel:R(p),body:R(bd),x:R(x),go:R(g),scroll:bd.scrollHeight>bd.clientHeight+1,sh:bd.scrollHeight,ch:bd.clientHeight,full:notes.every(n=>txt.includes(n)),n:bd.querySelectorAll('li').length,
    bg:getComputedStyle(p).backgroundColor,fg:getComputedStyle(p).color,title:(document.getElementById('updall_t')||{}).textContent||'',focus:document.activeElement&&document.activeElement.id};}"""

async def scenario(b,base,vw,vh,theme,big,tag,full):
    ctx=await b.new_context(viewport={"width":vw,"height":vh},device_scale_factor=2,is_mobile=True,has_touch=True,service_workers="block")
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    await ctx.route(re.compile(r"localhost:\d+/version\.json"),lambda r:asyncio.ensure_future(r.fulfill(status=200,content_type="application/json",body=json.dumps(VERSION,ensure_ascii=False))))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
    await unlock(page,base,"tupd"+tag.replace(" ","").replace("·","")[:12])
    await page.evaluate("(a)=>{themeSet(a.theme);try{localStorage.setItem('sos_bigtext',a.big?'1':'0');}catch(e){}themeApply();state.sel=null;state.view='';state.patient='';render();window.scrollTo(0,0);}",{"theme":theme,"big":big})
    await page.wait_for_timeout(200)
    await page.evaluate("UPD.info=null;UPD.collapsed=false;showUpdateBar();"); await page.wait_for_timeout(900)
    m=await page.evaluate(MEASURE)
    L=f"{vw} × {vh} · {theme} · {'grand texte' if big else 'texte normal'} : "
    cap=f"updbar-{vw}-{theme}-{'grand-texte' if big else 'texte-normal'}"
    bar=m.get("bar") or {}
    ok(L+"bandeau en haut, hauteur ≤ 40 % de l'écran, rien ne déborde en largeur, jaune-orange",bar and bar["t"]<=1 and bar["h"]<=round(0.4*m["H"])+1 and m["scrollW"]<=m["W"] and "rgb(255, 176, 0)" in m["bg"] and re.search(r"version 42b\.9",m["txt"] or ""),{k:m.get(k) for k in ("bar","H","scrollW","bg")})
    g,lt,ul=m.get("go"),m.get("later"),m.get("ul")
    ok(L+"« Mettre à jour maintenant » et « Plus tard » en tête du bandeau, entièrement dans l'écran et dans le bandeau, au-dessus de la liste",g and lt and ul and g["t"]>=bar["t"] and g["b"]<=min(bar["b"],m["H"])+1 and lt["b"]<=min(bar["b"],m["H"])+1 and lt["r"]<=m["W"] and g["b"]<=ul["t"]+1 and g["h"]>=(44 if vh<400 else 48) and lt["h"]>=44,{"go":g,"later":lt,"ul":ul,"bar":bar})
    lis=m.get("li") or []
    ok(L+"« Ce qui change » : 3 lignes courtes (une ligne chacune, coupées par « … ») et lien « Voir tout » visible dans le bandeau",len(lis)==3 and all(x["h"]<=x["fs"]*1.7 for x in lis) and sum(1 for x in lis if x["cut"])>=2 and m["allVisible"] and m["all"] and m["all"]["b"]<=min(bar["b"],m["H"])+1,{"li":lis,"all":m.get("all"),"bar":bar})
    ok(L+"l'écran commence sous le bandeau (barre du haut entièrement dessous et cliquable), hauteur réservée = hauteur du bandeau",m["jbar"] and m["jbar"]["t"]>=bar["b"]-2 and m["jhit"] and abs(m["pad"]-bar["h"])<=2 and m["updh"]==f"{bar['h']}px" or (m["jbar"] and m["jbar"]["t"]>=bar["b"]-2 and m["jhit"] and abs(m["pad"]-bar["h"])<=2),{"jbar":m.get("jbar"),"jhit":m.get("jhit"),"pad":m.get("pad"),"updh":m.get("updh"),"bar":bar})
    if big: ok(L+"grand texte : caractères du bandeau agrandis (≥ 17 px) sans sortir des 40 %",m["size"]=="big" and m["fs"]>=17 and bar["h"]<=round(0.4*m["H"])+1,{"size":m.get("size"),"fs":m.get("fs"),"bar":bar})
    if vh<400: ok(L+"écran bas (paysage) : la liste défile à l'intérieur du bandeau, les boutons restent visibles",m["bdScroll"] and g and g["b"]<=m["H"],{"bdScroll":m.get("bdScroll"),"bdH":m.get("bdH"),"go":g,"bar":bar})
    await page.screenshot(path=os.path.join(OUT,cap+".png"))
    # ---- « Voir tout » ----
    await page.click("#upd_all"); await page.wait_for_timeout(350)
    a=await page.evaluate(MODAL,NOTES)
    ok(L+"« Voir tout » : fenêtre avec toutes les notes en texte complet, qui défile, entièrement dans l'écran",not a.get("err") and a["full"] and a["n"]==len(NOTES) and a["scroll"] and a["panel"]["t"]>=0 and a["panel"]["b"]<=a["H"] and a["panel"]["r"]<=a["W"] and "42b.9" in a["title"],{k:a.get(k) for k in ("err","full","n","scroll","sh","ch","panel","title")})
    ok(L+"« Fermer » visible en haut de la fenêtre, « Mettre à jour maintenant » en bas, dans l'écran",not a.get("err") and a["x"] and a["x"]["t"]>=0 and a["x"]["b"]<=a["H"] and a["go"] and a["go"]["b"]<=a["H"] and a["x"]["b"]<a["body"]["t"]+1 and a["go"]["t"]>=a["body"]["b"]-1,{"x":a.get("x"),"go":a.get("go"),"body":a.get("body")})
    if full:
        bgs=await page.evaluate("()=>{const p=document.querySelector('#updall .uap');return getComputedStyle(p).backgroundColor;}")
        full.setdefault("modal_bg",{})[theme]=bgs
    await page.screenshot(path=os.path.join(OUT,cap+"-voir-tout.png"))
    await page.click("#updall_x"); await page.wait_for_timeout(200)
    c1=await page.evaluate("()=>!document.getElementById('updall')")
    await page.click("#upd_all"); await page.wait_for_timeout(200); await page.keyboard.press("Escape"); await page.wait_for_timeout(200)
    c2=await page.evaluate("()=>!document.getElementById('updall')")
    await page.click("#upd_all"); await page.wait_for_timeout(200)
    await page.mouse.click(vw//2,vh-5); await page.wait_for_timeout(200)
    c3=await page.evaluate("()=>!document.getElementById('updall')")
    ok(L+"la fenêtre se ferme par « Fermer », par Échap et par un toucher à côté",c1 and c2 and c3,[c1,c2,c3])
    if full:
        # ---- règle : jamais de mise à jour automatique pendant une consultation ----
        r=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));window.__noReload=1;state.sel=PACKS.findIndex(p=>p.n==='Angine');render();await w(250);
          const b=document.getElementById('updbar');const uw=b.querySelector('.uhd .uw');const g=document.getElementById('upd_go').getBoundingClientRect();const u=b.querySelector('ul').getBoundingClientRect();const H=window.innerHeight;
          navigator.serviceWorker.dispatchEvent(new Event('controllerchange'));await w(300);const pend=UPD.pendingReload===true;const still=window.__noReload===1;
          window.confirm=()=>false;document.getElementById('upd_all').click();await w(200);const modal=!!document.getElementById('updall');document.getElementById('updall_go').click();await w(300);
          const res={uw:!!uw,uwTxt:uw?uw.textContent:'',goVisible:g.bottom<=H&&g.top<u.top,pend,still,modal,closed:!document.getElementById('updall'),noOk:!window.__updOk,still2:window.__noReload===1,barH:Math.round(b.getBoundingClientRect().height),H};
          UPD.pendingReload=false;state.sel=null;render();await w(250);return res;}""")
        ok(L+"consultation en cours : avertissement en tête, boutons toujours visibles, controllerchange → attente (pas de rechargement), « Mettre à jour » depuis la fenêtre demande confirmation et n'agit pas si refusée",r["uw"] and "Consultation en cours" in r["uwTxt"] and r["goVisible"] and r["pend"] and r["still"] and r["modal"] and r["closed"] and r["noOk"] and r["still2"] and r["barH"]<=round(0.4*r["H"])+1,r)
        st=await page.evaluate("""async()=>{const w=ms=>new Promise(r=>setTimeout(r,ms));document.getElementById('upd_later').click();await w(150);const b=document.getElementById('updbar');const a=b.className;const h=Math.round(b.getBoundingClientRect().height);const updh=getComputedStyle(document.documentElement).getPropertyValue('--updh').trim();
          state.sel=PACKS.findIndex(p=>p.n==='Angine');render();await w(150);const c=b.className;state.sel=null;render();await w(150);const d=b.className;return {a,h,updh,c,d,ok:h<=70};}""")
        ok(L+"« Plus tard » réduit le bandeau à une ligne (≤ 70 px, hauteur réservée suivie), il revient au retour sur l'écran principal",st["a"]=="mini" and st["ok"] and st["updh"]==f"{st['h']}px" and st["c"]=="mini" and st["d"]=="",st)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3])
    await ctx.close()

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    base=f"http://localhost:{PORT}/"
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); full={}
            for theme in ("day","night"):
                for big in (False,True):
                    await scenario(b,base,375,812,theme,big,f"i{theme}{int(big)}",full if (theme=="day" and not big) else {"modal_bg":full.setdefault("modal_bg",{})})
            ok("fenêtre « Voir tout » : fond différent le jour et la nuit (suit le thème)",full.get("modal_bg",{}).get("day") and full["modal_bg"].get("night") and full["modal_bg"]["day"]!=full["modal_bg"]["night"],full.get("modal_bg"))
            await scenario(b,base,568,320,"day",False,"sed",None)
            await scenario(b,base,568,320,"night",True,"sen",None)
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    with open(os.path.join(ROOT,"tests","resultats_updbar.md"),"w",encoding="utf-8") as f:
        f.write("# Bandeau « Nouvelle version » — iPhone 375 px (jour, nuit, grand texte) et SE paysage — "+time.strftime("%d/%m/%Y %H:%M")+"\n\n")
        for name,c,info in results: f.write(("- OK " if c else "- **FAIL** ")+name+("" if c else " — "+str(info)[:600])+"\n")
        f.write(f"\n**{n}/{len(results)} tests OK**\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
