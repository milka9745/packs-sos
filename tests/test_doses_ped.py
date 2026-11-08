# -*- coding: utf-8 -*-
# Audit des doses au poids (08/11/2026) — erreur de posologie signalée en garde sur « Gastro-entérite — enfant ».
# Chaque ligne de médicament des fiches pédiatriques à dose au poids est vérifiée à 5 poids (5, 10, 15, 25, 40 kg), avec un âge
# plausible (4 mois, 1 an, 4 ans, 8 ans, 12 ans), contre les RCP de la base de données publique des médicaments et les
# recommandations (HAS, SP2A, ESPGHAN). Les bornes des tranches, l'âge minimal, l'impression (notes RCP jamais imprimées) et un
# balayage de toutes les fiches sont aussi contrôlés. Lancer : python tests/test_doses_ped.py
import asyncio, os, subprocess, time, sys, re, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:700])
PORT=8883
def ddn_months_ago(m):
    t=datetime.date.today(); y=t.year; mo=t.month-m
    while mo<=0: mo+=12; y-=1
    d=min(t.day,28); return "%02d/%02d/%04d"%(d,mo,y)
AGES={5:ddn_months_ago(4),10:ddn_months_ago(12),15:ddn_months_ago(48),25:ddn_months_ago(96),40:ddn_months_ago(144)}
WEIGHTS=(5,10,15,25,40)
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_xp','{'true' if xp else 'false'}')}}catch(e){{}}")
    await page.goto(f"http://localhost:{PORT}/index.html"); await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid",uid); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok"); await page.wait_for_selector("#rec_ack",timeout=15000); await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000); await page.wait_for_timeout(700)
# a = {n, w, ddn, risk, pick} → lignes de médicaments (gabarit brut, texte rempli, coché, manques) + pages imprimées + alertes
RUN="""(a)=>{newPatient();Object.assign(state,{patient:'TEST Enfant',ddn:a.ddn,poids:String(a.w),sexe:'f'});state.cot=state.cot||cotDefault();state.cot.lieu=a.lieu||'visite';state.cot.auto=false;if(a.risk)state.risk=a.risk;state.view='';state.sel=PACKS.findIndex(p=>p.n===a.n);
  const p=currentPack();if(!p)return {err:'pack introuvable '+a.n};
  if(a.pick){p.s.forEach((sh,si)=>{const r=resolve(sh,si);(Array.isArray(a.pick)?a.pick:[a.pick]).forEach(pk=>{const x=r.find(y=>y.fill.s.startsWith(pk)||y.t.replace(/^(\\{[^}]*\\})+/,'').startsWith(pk));if(x&&x.grp)state.gs[si+':'+x.grp]=x.key;else if(x)state.lo[x.key]=true;});});}
  render();const P=currentPack();const L=[];P.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>L.push({t:x.t.replace(/^(\\{agemin:[^}]*\\})+/,''),raw:x.t,on:x.on,s:x.fill.s,miss:x.fill.miss,adv:x.fill.adv}));});
  let pages=[];try{const d=document.createElement('div');d.innerHTML=buildPages(P,true).out;pages=[...d.querySelectorAll('.page')].map(x=>({h:(x.querySelector('h2')||{}).textContent||'',t:x.innerText}));}catch(e){pages=[{h:'erreur',t:String(e)}];}
  return {L,pages,age:ageY()};}"""
def find(r,brand):
    for x in r["L"]:
        if x["t"].startswith(brand) or x["s"].startswith(brand): return x
    for x in r["L"]:  # ligne non remplie (manque) : le gabarit brut porte le nom en minuscules, ex. {tiorfan}
        if ("{"+brand.lower().split(" ")[0]) in x["raw"].lower(): return x
    return None
def check_line(L,pack,brand,exp,r,w):
    x=find(r,brand)
    if exp is None:
        ok(L+f"{pack} · {brand} · {w} kg : ligne absente",x is None,x and x["s"][:120]); return
    if x is None:
        ok(L+f"{pack} · {brand} · {w} kg : ligne présente",False,[y["t"][:50] for y in r["L"]]); return
    if exp.startswith("MANQUE:"):
        want=exp[7:]
        ok(L+f"{pack} · {brand} · {w} kg : non proposée faute de « {want} »",any(want in m for m in x["miss"]),{"miss":x["miss"],"s":x["s"][:150]})
    else:
        ok(L+f"{pack} · {brand} · {w} kg : « {exp} »",exp in x["s"] and not x["miss"],{"s":x["s"][:260],"miss":x["miss"]})
DOLI={5:"DOLIPRANE 2,4 % suspension buvable : 1 dose-poids 5 kg (soit 3,13 ml, 75 mg) toutes les 6 heures",10:"DOLIPRANE 2,4 % suspension buvable : 1 dose-poids 10 kg (soit 6,25 ml, 150 mg) toutes les 6 heures",
      15:"DOLIPRANE 200 mg poudre en sachet : 1 sachet toutes les 6 heures",25:"DOLIPRANE 300 mg poudre en sachet : 1 sachet toutes les 6 heures",40:"DOLIPRANE 500 mg comprimé : 1 comprimé toutes les 6 heures si fièvre ou douleur, sans dépasser 4 comprimés par jour"}
DOLI_SUPP={5:"DOLIPRANE 100 mg suppositoire : 1 suppositoire toutes les 6 heures",10:"DOLIPRANE 150 mg suppositoire",15:"DOLIPRANE 200 mg suppositoire",25:"DOLIPRANE 300 mg suppositoire",40:None}
ADVIL={5:"MANQUE:âge ≥ 6 mois pour ADVILMED",10:"1 dose-poids 10 kg (soit 3,75 ml, 75 mg) 3 à 4 fois par jour",15:"1 dose-poids 15 kg (soit 5,63 ml, 112,5 mg)",25:"1 dose-poids 25 kg (soit 9,38 ml, 187,5 mg)",40:"15 ml, soit 300 mg 3 à 4 fois par jour"}
TIORFAN={5:"TIORFAN nourrisson 10 mg sachets : 1 sachet (10 mg) 3 fois par jour",10:"TIORFAN nourrisson 10 mg sachets : 2 sachets (20 mg) 3 fois par jour",15:"TIORFAN enfant 30 mg sachets : 1 sachet (30 mg) 3 fois par jour",25:"TIORFAN enfant 30 mg sachets : 1 sachet (30 mg) 3 fois par jour",40:"TIORFAN enfant 30 mg sachets : 2 sachets (60 mg) 3 fois par jour"}
ZOPHREN={5:"MANQUE:âge ≥ 6 mois pour ondansétron",10:"2,5 ml (2 mg)",15:"5 ml (4 mg)",25:"5 ml (4 mg)",40:"10 ml (8 mg)"}
VOG3={5:"MANQUE:poids ≥ 7,5 kg pour VOGALÈNE suppositoire",10:"½ suppositoire (2,5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 7,5 mg par jour",15:"1 suppositoire (5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 15 mg par jour",25:"1 suppositoire (5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 15 mg par jour",40:"1 suppositoire (5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 15 mg par jour"}
VOG2={5:"MANQUE:poids ≥ 7,5 kg pour VOGALÈNE suppositoire",10:"½ suppositoire (2,5 mg) par prise, jusqu'à 2 fois par jour, sans dépasser 5 mg par jour",15:"1 suppositoire (5 mg) par prise, jusqu'à 2 fois par jour, sans dépasser 10 mg par jour",25:"1 suppositoire (5 mg) par prise, jusqu'à 2 fois par jour, sans dépasser 10 mg par jour",40:"1 suppositoire (5 mg) par prise, jusqu'à 2 fois par jour, sans dépasser 10 mg par jour"}
ADIARIL={w:"1 sachet dans 200 ml d'eau" for w in WEIGHTS}
EXPECT=[
 ("Gastro-entérite — enfant",None,[("ADIARIL",ADIARIL),("TIORFAN",TIORFAN),("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None}),("DOLIPRANE 200",{5:None,10:None,15:DOLI[15],25:None,40:None}),("DOLIPRANE 300",{5:None,10:None,15:None,25:DOLI[25],40:None}),("DOLIPRANE 500",{5:None,10:None,15:None,25:None,40:DOLI[40]}),
   ("ZOPHREN",ZOPHREN),("VOGALÈNE",VOG3)]),
 ("Fièvre — enfant",None,[("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None}),("DOLIPRANE 200",{5:None,10:None,15:DOLI[15],25:None,40:None}),("DOLIPRANE 300",{5:None,10:None,15:None,25:DOLI[25],40:None}),("DOLIPRANE 500",{5:None,10:None,15:None,25:None,40:DOLI[40]}),("ADVILMED",ADVIL)]),
 ("Bronchiolite — nourrisson",None,[("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None}),("DOLIPRANE 200",{5:None,10:None,15:DOLI[15],25:None,40:None})]),
 ("Otite moyenne aiguë — enfant","r",[
   ("CLAMOXYL",{5:"2 ml (soit 200 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, sans dépasser 15 ml par prise, pendant 10 jours",10:"4,5 ml (soit 450 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, sans dépasser 15 ml par prise, pendant 10 jours",15:"6,5 ml (soit 650 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, sans dépasser 15 ml par prise, pendant 5 jours",25:"10,5 ml (soit 1050 mg) matin et soir",40:"15 ml (soit 1500 mg) matin et soir"}),
   ("AUGMENTIN",{5:"1,5 ml (soit 150 mg d'amoxicilline) 3 fois par jour",10:"2,5 ml (soit 250 mg d'amoxicilline) 3 fois par jour",15:"4 ml (soit 400 mg d'amoxicilline) 3 fois par jour",25:"7 ml (soit 700 mg d'amoxicilline) 3 fois par jour",40:"10 ml (soit 1000 mg d'amoxicilline) 3 fois par jour"}),
   ("ORELOX",{5:"1 dose-poids 5 kg (soit 2,5 ml, 20 mg) matin et soir",10:"1 dose-poids 10 kg (soit 5 ml, 40 mg) matin et soir",15:"1 dose-poids 15 kg (soit 7,5 ml, 60 mg) matin et soir",25:"1 dose-poids 25 kg (soit 12,5 ml, 100 mg) matin et soir",40:"20 ml, soit 160 mg matin et soir"}),
   ("BACTRIM",{5:"2 ml (soit 80 mg de sulfaméthoxazole) matin et soir",10:"4 ml (soit 160 mg de sulfaméthoxazole) matin et soir",15:"5,5 ml (soit 220 mg de sulfaméthoxazole) matin et soir",25:"9,5 ml (soit 380 mg de sulfaméthoxazole) matin et soir",40:"10 ml (soit 400 mg de sulfaméthoxazole) matin et soir"}),
   ("AERIUS",{5:"MANQUE:âge ≥ 1 an pour AERIUS",10:"2,5 ml en une prise par jour",15:"2,5 ml en une prise par jour",25:"5 ml en une prise par jour",40:"10 ml en une prise par jour"}),
   ("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None})]),
 ("Angine — enfant (TROD positif)",None,[
   ("CLAMOXYL",{5:"1,5 ml (soit 150 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, pendant 6 jours",10:"2,5 ml (soit 250 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, pendant 6 jours",15:"4 ml (soit 400 mg) matin et soir",25:"6,5 ml (soit 650 mg) matin et soir",40:"10 ml (soit 1000 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, pendant 6 jours"}),
   ("ORELOX",{5:"1 dose-poids 5 kg (soit 2,5 ml, 20 mg)",10:"1 dose-poids 10 kg (soit 5 ml, 40 mg)",15:"1 dose-poids 15 kg (soit 7,5 ml, 60 mg)",25:"1 dose-poids 25 kg (soit 12,5 ml, 100 mg)",40:"12,5 ml, soit 100 mg (dose maximale)"}),
   ("ZINNAT",{5:"2 ml (soit 50 mg) matin et soir au cours des repas, à mesurer avec la seringue graduée en ml du flacon, pendant 4 jours",10:"4 ml (soit 100 mg) matin et soir",15:"6 ml (soit 150 mg) matin et soir",25:"10 ml (soit 250 mg) matin et soir",40:"10 ml (soit 250 mg) matin et soir"}),
   ("ZITHROMAX 40",{5:"1 dose-poids 5 kg (soit 2,5 ml, 100 mg) en une prise par jour pendant 3 jours",10:"1 dose-poids 10 kg (soit 5 ml, 200 mg)",15:"1 dose-poids 15 kg (soit 7,5 ml, 300 mg)",25:"1 dose-poids 25 kg (soit 12,5 ml, 500 mg)",40:"12,5 ml, soit 500 mg (dose maximale)"}),
   ("ZITHROMAX 250",{w:None for w in WEIGHTS}),
   ("ZECLAR",{5:"1 dose-poids 5 kg (soit 0,75 ml, 37,5 mg) matin et soir pendant 5 jours",10:"1 dose-poids 10 kg (soit 1,5 ml, 75 mg) matin et soir pendant 5 jours",15:"1 dose-poids 15 kg (soit 2,25 ml, 112,5 mg) matin et soir",25:"1 dose-poids 25 kg (soit 3,75 ml, 187,5 mg) matin et soir",40:"5 ml, soit 250 mg (dose maximale) matin et soir"}),
   ("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None})]),
 ("Vomissements isolés — enfant",None,[("ADIARIL",ADIARIL),("ZOPHREN",ZOPHREN),("VOGALÈNE",VOG3),("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None}),("DOLIPRANE 500",{5:None,10:None,15:None,25:None,40:DOLI[40]})]),
 ("Convulsion fébrile simple — enfant",None,[("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None}),
   ("VALIUM",{5:"0,5 ml (soit 2,5 mg) soit 0,5 mg/kg, en une seule administration",10:"1 ml (soit 5 mg) soit 0,5 mg/kg, en une seule administration",15:"1,5 ml (soit 7,5 mg) soit 0,5 mg/kg, en une seule administration",25:"2 ml (soit 10 mg) soit 0,5 mg/kg, en une seule administration",40:"2 ml (soit 10 mg) soit 0,5 mg/kg, en une seule administration"})]),
 ("Asthme aigu — enfant",None,[("VENTOLINE",{5:"4 bouffées (1 bouffée par 2 kg, 4 au minimum, 10 au maximum)",10:"5 bouffées (1 bouffée par 2 kg",15:"8 bouffées (1 bouffée par 2 kg",25:"10 bouffées (1 bouffée par 2 kg",40:"10 bouffées (1 bouffée par 2 kg"}),
   ("SOLUPRED",{5:"SOLUPRED 5 mg comprimé orodispersible (prednisolone), dose enfant : 2 comprimés (10 mg) en une prise le matin pendant 3 jours",10:"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 1 comprimé (20 mg) en une prise le matin pendant 3 jours",15:"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 1 comprimé (20 mg)",25:"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 2 comprimés (40 mg)",40:"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 2 comprimés (40 mg)"})]),
 ("Migraine — enfant",None,[("ADVILMED",ADVIL),("VOGALÈNE",VOG2),("DOLIPRANE 2,4",{5:DOLI[5],10:DOLI[10],15:None,25:None,40:None})]),
 ("Laryngite aiguë — enfant",None,[("SOLUPRED",{5:"5 mg (1 comprimé) en une prise le matin pendant 3 jours",10:"10 mg (2 comprimés)",15:"15 mg (3 comprimés)",25:"25 mg (5 comprimés)",40:"40 mg (8 comprimés)"}),
   ("CÉLESTÈNE",{5:"50 gouttes (10 gouttes par kg",10:"100 gouttes (10 gouttes par kg",15:"150 gouttes (10 gouttes par kg",25:"250 gouttes (10 gouttes par kg",40:"400 gouttes (10 gouttes par kg"}),
   ("DECTANCYL",{5:"0,75 mg (1,5 comprimés)",10:"1,5 mg (3 comprimés)",15:"2,25 mg (4,5 comprimés)",25:"3,75 mg (7,5 comprimés)",40:"6 mg (12 comprimés)"})]),
]
SWEEP="""()=>{const out={troisSachets:[],vogOver:[],vogUnder:[],err:[]};for(const w of [5,10,15,25,40]){for(let i=0;i<PACKS.length;i++){if(!PACKS[i].s.some(sh=>sh.k==='med'))continue;try{newPatient();Object.assign(state,{patient:'X',ddn:'01/01/2016',poids:String(w),sexe:'f'});state.sel=i;const p=currentPack();
  p.s.forEach((sh,si)=>{if(sh.k!=='med')return;resolve(sh,si).forEach(x=>{const t=x.fill.s;if(/TIORFAN/.test(t)&&/3 sachets/.test(t))out.troisSachets.push([PACKS[i].n,w,t.slice(0,80)]);
    if(/VOGALÈNE 5 mg suppositoire/.test(x.t)){if(w<7.5){if(!x.fill.miss.length)out.vogUnder.push([PACKS[i].n,w,t.slice(0,90)]);}else{const m=/sans dépasser ([\\d,]+) mg par jour/.exec(t);const mx=m?parseFloat(m[1].replace(',','.')):NaN;if(!(mx<=w&&mx<=15))out.vogOver.push([PACKS[i].n,w,t.slice(0,120)]);}}});});}catch(e){out.err.push([PACKS[i].n,w,String(e).slice(0,80)]);}}}return out;}"""
async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for (w,h,lbl,xp) in [(1280,900,"ordinateur · mode complet",False),(375,812,"iPhone · Express",True)]:
                mob=w<500; L=lbl+" : "
                ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
                await ctx.route("**/*",lambda r:asyncio.ensure_future(r.continue_() if "localhost" in r.request.url else r.abort()))
                page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
                await unlock(page,"dp"+("x" if xp else "c"),xp)
                for (pack,risk,lines) in EXPECT:
                    for wkg in WEIGHTS:
                        r=await page.evaluate(RUN,{"n":pack,"w":wkg,"ddn":AGES[wkg],"risk":risk})
                        if "err" in r: ok(L+pack,False,r["err"]); break
                        for (brand,exp) in lines:
                            e=exp.get(wkg,"__skip__")
                            if e=="__skip__": continue
                            check_line(L,pack,brand,e,r,wkg)
                # bornes des tranches (RCP) : TIORFAN 9 / 13 / 27 kg ; VOGALÈNE 7,5 et 15 kg ; ondansétron 15 et 30 kg ; SOLUPRED 20 kg
                G="Gastro-entérite — enfant"
                for (wkg,exp) in [(9,"2 sachets (20 mg)"),(12.5,"2 sachets (20 mg)"),(13,"TIORFAN enfant 30 mg sachets : 1 sachet (30 mg)"),(27,"TIORFAN enfant 30 mg sachets : 1 sachet (30 mg)"),(27.5,"TIORFAN enfant 30 mg sachets : 2 sachets (60 mg)")]:
                    r=await page.evaluate(RUN,{"n":G,"w":wkg,"ddn":AGES[15]}); x=find(r,"TIORFAN")
                    ok(L+f"TIORFAN à {wkg} kg : « {exp} » (borne RCP)",x and exp in x["s"] and "3 sachets" not in x["s"],x and x["s"][:120])
                for (wkg,exp) in [(7,"MANQUE"),(7.5,"½ suppositoire (2,5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 7,5 mg par jour"),(14.5,"½ suppositoire (2,5 mg) par prise"),(15,"1 suppositoire (5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 15 mg par jour")]:
                    r=await page.evaluate(RUN,{"n":G,"w":wkg,"ddn":AGES[15]}); x=find(r,"VOGALÈNE")
                    if exp=="MANQUE": ok(L+f"VOGALÈNE à {wkg} kg : non proposée (RCP : pas de suppositoire sous 7,5 kg)",x and any("7,5 kg" in m for m in x["miss"]),x and (x["miss"],x["s"][:80]))
                    else: ok(L+f"VOGALÈNE à {wkg} kg : « {exp} »",x and exp in x["s"] and not x["miss"],x and x["s"][:160])
                for (wkg,exp) in [(14.5,"2,5 ml (2 mg)"),(15,"5 ml (4 mg)"),(30,"5 ml (4 mg)"),(30.5,"10 ml (8 mg)")]:
                    r=await page.evaluate(RUN,{"n":G,"w":wkg,"ddn":AGES[15]}); x=find(r,"ZOPHREN")
                    ok(L+f"ondansétron à {wkg} kg : « {exp} » en une seule prise",x and exp in x["s"] and "en une seule prise" in x["s"],x and x["s"][:120])
                for (wkg,exp) in [(9.5,"SOLUPRED 5 mg comprimé orodispersible (prednisolone), dose enfant : 2 comprimés (10 mg)"),(20,"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 1 comprimé (20 mg)"),(20.5,"SOLUPRED 20 mg comprimé orodispersible (prednisolone), dose enfant : 2 comprimés (40 mg)")]:
                    r=await page.evaluate(RUN,{"n":"Asthme aigu — enfant","w":wkg,"ddn":AGES[25]}); x=find(r,"SOLUPRED")
                    ok(L+f"prednisolone asthme à {wkg} kg : « {exp} » (SP2A : 20 mg jusqu'à 20 kg, 40 mg au-delà, 1 à 2 mg/kg)",x and exp in x["s"] and not x["miss"],x and x["s"][:160])
                # âge minimal TIORFAN : 1 mois (RCP du 20/10/2026)
                r=await page.evaluate(RUN,{"n":G,"w":4,"ddn":(datetime.date.today()-datetime.timedelta(days=20)).strftime("%d/%m/%Y")}); x=find(r,"TIORFAN")
                ok(L+"TIORFAN à 20 jours de vie : non proposé (RCP : à partir de 1 mois)",x and any("1 mois" in m and "TIORFAN" in m for m in x["miss"]),x and (x["miss"],x["s"][:80]))
                r=await page.evaluate(RUN,{"n":G,"w":4.5,"ddn":ddn_months_ago(2)}); x=find(r,"TIORFAN")
                ok(L+"TIORFAN à 2 mois (4,5 kg) : 1 sachet de 10 mg 3 fois par jour",x and "1 sachet (10 mg) 3 fois par jour" in x["s"] and not x["miss"],x and (x["miss"],x["s"][:100]))
                # impression : la règle RCP n'est jamais imprimée ; la dose maximale journalière de VOGALÈNE et la dose de TIORFAN le sont
                r=await page.evaluate(RUN,{"n":G,"w":10,"ddn":AGES[10],"pick":"VOGALÈNE"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"gastro 10 kg, ordonnance : TIORFAN « 2 sachets (20 mg) 3 fois par jour » et VOGALÈNE « ½ suppositoire (2,5 mg) par prise, jusqu'à 3 fois par jour, sans dépasser 7,5 mg par jour »","2 sachets (20 mg) 3 fois par jour" in ordo and "sans dépasser 7,5 mg par jour" in ordo,ordo[:600])
                ok(L+"gastro 10 kg, ordonnance : notes RCP et règles jamais imprimées","(RCP" not in ordo and "règle :" not in ordo and "mg/kg par prise" not in ordo and "(dose unique)" not in ordo and "HAS 20" not in ordo,ordo[:600])
                r=await page.evaluate(RUN,{"n":"Angine — enfant (TROD positif)","w":15,"ddn":AGES[15],"pick":"ZECLAR"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"angine 15 kg, ordonnance : ZECLAR « 1 dose-poids 15 kg (soit 2,25 ml, 112,5 mg) matin et soir pendant 5 jours » sans note HAS ni RCP","1 dose-poids 15 kg (soit 2,25 ml, 112,5 mg) matin et soir pendant 5 jours" in ordo and "HAS" not in ordo and "RCP" not in ordo and "SPILF" not in ordo,ordo[:700])
                r=await page.evaluate(RUN,{"n":"Angine — enfant (TROD positif)","w":15,"ddn":AGES[15],"pick":"ZINNAT"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"angine 15 kg, ordonnance : ZINNAT « 6 ml (soit 150 mg) matin et soir au cours des repas, à mesurer avec la seringue graduée en ml du flacon, pendant 4 jours » sans note","6 ml (soit 150 mg) matin et soir au cours des repas, à mesurer avec la seringue graduée en ml du flacon, pendant 4 jours" in ordo and "RCP" not in ordo and "SPILF" not in ordo,ordo[:700])
                r=await page.evaluate(RUN,{"n":"Otite moyenne aiguë — enfant","w":10,"ddn":AGES[10],"risk":"r"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"otite 10 kg, ordonnance : CLAMOXYL « 4,5 ml (soit 450 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, sans dépasser 15 ml par prise, pendant 10 jours » sans note HAS","4,5 ml (soit 450 mg) matin et soir, à mesurer avec une seringue pour administration orale graduée en ml, sans dépasser 15 ml par prise, pendant 10 jours" in ordo and "HAS" not in ordo and "cuillère-mesure" not in ordo,ordo[:700])
                r=await page.evaluate(RUN,{"n":"Convulsion fébrile simple — enfant","w":15,"ddn":AGES[15],"pick":"VALIUM"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"convulsion 15 kg, ordonnance : VALIUM « 1,5 ml (soit 7,5 mg) soit 0,5 mg/kg, en une seule administration » puis appel du 15, sans note RCP ni « renouvelable »","1,5 ml (soit 7,5 mg) soit 0,5 mg/kg, en une seule administration" in ordo and "appeler le 15" in ordo and "RCP" not in ordo and "renouvelable" not in ordo and "SAMU" not in ordo,ordo[:700])
                r=await page.evaluate(RUN,{"n":"Asthme aigu — enfant","w":15,"ddn":AGES[15]})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"asthme 15 kg, ordonnance : SOLUPRED 20 mg « 1 comprimé (20 mg) en une prise le matin pendant 3 jours, dispersé dans un peu d'eau » sans règle ; VENTOLINE 8 bouffées","1 comprimé (20 mg) en une prise le matin pendant 3 jours, dispersé dans un peu d'eau" in ordo and "règle" not in ordo and "SP2A" not in ordo and "8 bouffées" in ordo,ordo[:700])
                r=await page.evaluate(RUN,{"n":G,"w":40,"ddn":AGES[40],"pick":"ZOPHREN"})
                ordo=" ".join(x["t"] for x in r["pages"] if x["h"].startswith("Ordonnance"))
                ok(L+"gastro 40 kg, ordonnance : TIORFAN « 2 sachets (60 mg) 3 fois par jour », jamais « 3 sachets » ; ZOPHREN « 10 ml (8 mg) en une seule prise »","2 sachets (60 mg) 3 fois par jour" in ordo and "3 sachets" not in ordo and "10 ml (8 mg) en une seule prise" in ordo and "(règle" not in ordo,ordo[:600])
                sw=await page.evaluate(SWEEP)
                ok(L+"toutes les fiches × 5 poids : TIORFAN jamais « 3 sachets »",not sw["troisSachets"],sw["troisSachets"][:5])
                ok(L+"toutes les fiches × 5 poids : VOGALÈNE suppositoire ≤ 1 mg/kg/jour et ≤ 15 mg/jour, dose maximale écrite",not sw["vogOver"],sw["vogOver"][:5])
                ok(L+"toutes les fiches × 5 poids : VOGALÈNE suppositoire jamais proposé sous 7,5 kg",not sw["vogUnder"],sw["vogUnder"][:5])
                ok(L+"balayage sans erreur JS",not sw["err"],sw["err"][:3])
                ok(L+"aucune erreur JS",not errors,errors[:2])
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    open(os.path.join(ROOT,"tests","resultats_doses_ped.md"),"w",encoding="utf-8").write("# Audit des doses au poids — fiches pédiatriques (08/11/2026)\n\n"+"\n".join(f"- {'OK' if r[1] else 'ÉCHEC'} — {r[0]}{(' — '+str(r[2])[:300]) if not r[1] else ''}" for r in results)+f"\n\n{n}/{len(results)} tests OK\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
