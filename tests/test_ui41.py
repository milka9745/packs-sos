# Tests iPhone 375 px (16/10/2026) : menu ⋯ défilable, interrupteurs lisibles, bouton IA de l'écran principal.
# Grand texte avec et sans, jour et nuit ; aucune requête vers l'IA pendant le test. Lancer : python tests/test_ui41.py
import asyncio, os, json, subprocess, time, sys
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"tests","captures")
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else info)

async def unlock(page):
    await page.goto("http://localhost:8771/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testv41"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
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

HIT="""(sel)=>{const e=document.querySelector(sel);if(!e)return {ok:false,why:'absent'};const r=e.getBoundingClientRect();const vh=window.innerHeight;if(r.bottom>vh+0.5||r.top<0)return {ok:false,why:'hors écran',top:r.top,bottom:r.bottom,vh};const h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {ok:!!h&&(h===e||e.contains(h)),why:h?h.id||h.className:''};}"""
PILL="""(sel)=>{const e=document.querySelector(sel);const p=e&&e.querySelector('.swp');if(!p)return null;const cs=getComputedStyle(p);return {txt:p.textContent.trim(),on:p.classList.contains('on'),bg:cs.backgroundColor,color:cs.color};}"""

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8771"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            ctx=await b.new_context(viewport={"width":375,"height":667},device_scale_factor=2,is_mobile=True,has_touch=True)
            page=await ctx.new_page(); errors=[]; reqs=[]
            page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            page.on("request",lambda r:reqs.append(r.url))
            await unlock(page)
            for big in [False,True]:
                for th in ["day","night"]:
                    L=f"375 px {'grand texte' if big else 'texte normal'} {('jour' if th=='day' else 'nuit')} : "
                    await page.evaluate(f"localStorage.setItem('sos_theme','{th}');localStorage.removeItem('sos_theme_force');localStorage.setItem('sos_bigtext','{1 if big else 0}');THEME.mode='{th}';themeApply();state.sel=null;state.view='';state.patient='';render();")
                    await page.wait_for_timeout(400)
                    # 1. menu ⋯ défilable jusqu'en bas
                    await page.click("#more_btn"); await page.wait_for_timeout(300)
                    m=await page.evaluate("(()=>{const m=document.getElementById('jmenu');const r=m.getBoundingClientRect();const cs=getComputedStyle(m);return {top:r.top,bottom:r.bottom,vh:innerHeight,ov:cs.overflowY,sh:m.scrollHeight,ch:m.clientHeight};})()")
                    ok(L+"menu ⋯ tient dans l'écran visible, défilement interne",m["bottom"]<=m["vh"]+0.5 and m["ov"] in ("auto","scroll"),m)
                    box=await page.evaluate("(()=>{const r=document.getElementById('jmenu').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};})()")
                    await page.mouse.move(box["x"],box["y"])
                    for _ in range(6): await page.mouse.wheel(0,600); await page.wait_for_timeout(80)
                    await page.wait_for_timeout(200)
                    hits={s:await page.evaluate(HIT,s) for s in ["#f_open","#j_open","#bak_menu"]}
                    ok(L+"lignes du bas (Sauvegarde, Journal, Fin de garde) atteignables par défilement",all(h["ok"] for h in hits.values()),hits)
                    if big and th=="night": await page.screenshot(path=os.path.join(OUT,"iphone-menu-bas-grandtexte-nuit.png"))
                    # 2. interrupteurs : pastille « activé / désactivé »
                    await page.evaluate("document.getElementById('jmenu').scrollTop=0"); await page.wait_for_timeout(150)
                    tx=await page.evaluate(PILL,"#jmenu #tx_btn"); thp=await page.evaluate(PILL,"#jmenu #th_btn"); tt=await page.evaluate(PILL,"#jmenu #t_toggle")
                    dg=await page.evaluate(PILL,"#jmenu [data-dset=garde]"); dp=await page.evaluate(PILL,"#jmenu [data-dset=premium]")
                    ok(L+"Grand texte : pastille juste",tx and tx["on"]==big and tx["txt"]==("activé" if big else "désactivé"),tx)
                    ok(L+"Mode nuit : pastille juste",thp and thp["on"]==(th=="night") and thp["txt"]==("activé" if th=="night" else "désactivé"),thp)
                    ok(L+"Mode test : pastille « désactivé »",tt and not tt["on"] and tt["txt"]=="désactivé",tt)
                    ok(L+"Affichage : une seule option « activé »",dg and dp and (dg["on"]!=dp["on"]) and {dg["txt"],dp["txt"]}=={"activé","désactivé"},[dg,dp])
                    ok(L+"pastille « activé » sur fond vert plein, « désactivé » sans fond",tx and thp and (lambda on,off:on["bg"] in ("rgb(29, 122, 58)","rgb(63, 180, 106)") and off["bg"] in ("rgba(0, 0, 0, 0)","transparent"))(*( (tx,thp) if big else (thp,tx) ) if (big!=(th=="night")) else (dg if dg["on"] else dp, dp if dg["on"] else dg)),[tx,thp,dg,dp])
                    sq=await page.evaluate("(()=>{const m=document.getElementById('jmenu');return [...m.children].filter(e=>e.getBoundingClientRect().height<30||e.scrollHeight>e.clientHeight+2).map(e=>e.id||e.className);})()")
                    ok(L+"aucune ligne du menu écrasée ni rognée",not sq,sq)
                    if not big and th=="day": await page.screenshot(path=os.path.join(OUT,"iphone-menu-interrupteurs-jour.png"))
                    if big and th=="night": await page.screenshot(path=os.path.join(OUT,"iphone-menu-interrupteurs-grandtexte-nuit.png"))
                    await page.click("#more_btn"); await page.wait_for_timeout(200)
                    # 3. bouton IA sur l'écran principal
                    await page.evaluate("AI.key='';AI.cfg.mode='aucun';aiSave();render();"); await page.wait_for_timeout(300)
                    await page.evaluate("document.querySelector('.pcard-h [data-aimain]').scrollIntoView({block:'center'})"); await page.wait_for_timeout(200)
                    hb=await page.evaluate("(()=>{const e=document.querySelector('.pcard-h [data-aimain]');if(!e)return null;const r=e.getBoundingClientRect();return {txt:e.textContent,cls:e.className,bg:getComputedStyle(e).backgroundColor,w:r.width,h:r.height,vis:r.top>=0&&r.bottom<=innerHeight&&(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)||{}).closest('[data-aimain]')===e};})()")
                    ok(L+"bouton IA dans la carte Patient (écran principal), « Aucun », gris, 44 px",hb and "Aucun" in hb["txt"] and "off" in hb["cls"] and hb["h"]>=44 and hb["vis"],hb)
                    await page.click(".pcard-h [data-aimain]"); await page.wait_for_timeout(250)
                    pop=await page.evaluate("(()=>{const m=document.getElementById('aipop');if(!m)return null;const r=m.getBoundingClientRect();return {acts:[...m.querySelectorAll('[data-aipa]')].map(b=>b.textContent.split('\\n')[0]),dis:[...m.querySelectorAll('[data-aipa]')].map(b=>b.disabled),key:!!m.querySelector('#aip_key'),in:r.left>=0&&r.right<=document.documentElement.clientWidth&&r.bottom<=innerHeight+0.5};})()")
                    ok(L+"toucher : petit choix à 4 entrées, dans l'écran",pop and len(pop["acts"])==4 and pop["in"] and all(any(a.startswith(x) for a in pop["acts"]) for x in ["Analyser la dictée","Relire le compte rendu","Rédiger le courrier","Changer le mode"]),pop)
                    clip=await page.evaluate("[...document.querySelectorAll('#aipop>*')].filter(e=>e.scrollHeight>e.clientHeight+2).map(e=>e.textContent.slice(0,20))")
                    ok(L+"petit choix IA : aucune ligne rognée",not clip,clip)
                    ok(L+"sans clé : propose de la saisir, actions IA inactives",pop and pop["key"] and pop["dis"][:3]==[True,True,True] and not pop["dis"][3],pop)
                    if not big and th=="day": await page.screenshot(path=os.path.join(OUT,"iphone-ia-choix-sans-cle.png"))
                    await page.fill("#aip_key","sk-ant-test-factice-ui"); await page.click("#aip_save"); await page.wait_for_timeout(400)
                    ok(L+"clé saisie : reste sur « Aucun », choix du mode affiché",await page.evaluate("AI.key")=="sk-ant-test-factice-ui" and await page.evaluate("AI.cfg.mode")=="aucun" and await page.locator("#aipop .aimode").count()==1)
                    await page.click("#aipop [data-aimode=partiel]"); await page.wait_for_timeout(400)
                    hb=await page.evaluate("(()=>{const e=document.querySelector('[data-aimain]');return {txt:e.textContent,cls:e.className,bg:getComputedStyle(e).backgroundColor};})()")
                    ok(L+"Partiel : bouton en couleur vive avec le mode",("Partiel" in hb["txt"]) and "vive" in hb["cls"] and hb["bg"] in ("rgb(255, 176, 0)","rgb(255, 179, 0)"),hb)
                    if big and th=="night": await page.screenshot(path=os.path.join(OUT,"iphone-ia-choix-partiel-grandtexte-nuit.png"))
                    await page.evaluate("aiPopClose()")
                    # près de la dictée et de l'observation
                    await page.evaluate("""()=>{const i=PACKS.findIndex(p=>/Cystite simple/.test(p.n));state.sel=i;state.patient='DUPONT Marie';state.ddn='12/03/1985';state.t0=Date.now();state.obsOpen=false;render();}"""); await page.wait_for_timeout(300)
                    ok(L+"bouton IA à côté de « Observation et compte rendu »",await page.locator(".obs.closed [data-aimain]").count()==1)
                    await page.evaluate("state.obsOpen=true;state.obs.dict='Mme Dupont brûlures mictionnelles depuis le 13/10.';render();"); await page.wait_for_timeout(300)
                    ok(L+"bouton IA à côté de la dictée (« Répartir »)",await page.locator(".dict-act [data-aimain]").count()==1)
                    await page.locator(".dict-act [data-aimain]").scroll_into_view_if_needed(); await page.click(".dict-act [data-aimain]"); await page.wait_for_timeout(250)
                    await page.click("#aipop [data-aipa=obs]"); await page.wait_for_timeout(400)
                    sent=await page.inner_text("#ai_sent") if await page.locator("#ai_sent").count() else ""
                    ok(L+"« Analyser la dictée » ouvre « Ce qui part », dictée anonymisée",await page.locator("#aisend").count()==1 and "Dupont" not in sent and "[[" in sent,sent[-120:])
                    await page.click("#ai_cancel"); await page.wait_for_timeout(200)
                    await page.click(".dict-act [data-aimain]"); await page.wait_for_timeout(200); await page.click("#aipop [data-aipa=cr]"); await page.wait_for_timeout(400)
                    ok(L+"« Relire le compte rendu » ouvre « Ce qui part »",await page.locator("#aisend").count()==1)
                    await page.click("#ai_cancel"); await page.wait_for_timeout(200)
                    await page.click(".dict-act [data-aimain]"); await page.wait_for_timeout(200); await page.click("#aipop [data-aipa=let]"); await page.wait_for_timeout(300)
                    ok(L+"« Rédiger le courrier » ouvre l'onglet Courrier",await page.locator("#aipanel [data-aitab=let].on").count()==1)
                    await page.evaluate("document.querySelectorAll('#aipanel,#aisend,#aipop').forEach(e=>e.remove());state.sel=null;state.obs={};render();")
            ok("375 px : aucune requête vers l'IA pendant tout le test",not [u for u in reqs if "anthropic.com" in u])
            ok("375 px : aucune erreur JS",not errors,errors[:3])
            await b.close()
    finally:
        srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_ui41.md"),"w",encoding="utf-8").write("# Tests iPhone 375 px — menu ⋯, interrupteurs, bouton IA (16/10/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
