# -*- coding: utf-8 -*-
# 08/11/2026 (v41z) — fiche patient : (1) bloc identité en tête de la carte patient, couleur du mode, gros caractères, ordre fixe Nom · Prénom · Naissance (âge) · Sexe F/M · Poids,
# une ligne sur ordinateur, deux sur iPhone, Entrée ou Tab passe au champ suivant, âge et sexe pilotent doses et accords ; (2) lignes Allergies (case pénicillines) et Traitements
# (base médicaments, interactions) juste dessous, remplies par les documents en proposition à valider ; (3) options secondaires en plus petit, cachet coché par défaut ;
# (4) Visite : identité remplie depuis la fiche de régulation (sexe lu « Née le » / « Sexe : M » ou déduit du prénom, téléphone, adresse), modifiable d'un toucher ;
# (5) en-tête ordinateur sur une ligne à 1280 et 1920 px, jour et nuit, grand texte (secondaires dans ⋯). Patients fictifs ; aucun appel externe.
# Lancer : python tests/test_fiche_patient_v41z.py
import asyncio, os, re, json, subprocess, sys, time, datetime
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,"tests","captures"); PORT=8877
results=[]
def ok(name,cond,info=""):
    results.append((name,bool(cond),info)); print(("OK  " if cond else "FAIL"),name,"" if cond else str(info)[:900])
FICHE_F="""Auto-Régulation / Visite
INFORMATIONS PATIENT
DUBOIS CLAIRE
Née le 12/05/1958 - 68 A
Tél patient 02 38 00 11 22
INTERVENTION
08/11/2026 10:12
DOULEUR ABDOMINALE
ADRESSE PATIENT
14 AVENUE DES PINS
45100 ORLEANS
Bat : C Etg : 4 Por : 12"""
FICHE_AMB="""Auto-Régulation / Visite
INFORMATIONS PATIENT
MARTIN PAUL
Né(e) le 03/04/1990 - 36 A
Tél patient 06 11 22 33 44
INTERVENTION
08/11/2026 10:20
FIEVRE
ADRESSE PATIENT
8 RUE DES LILAS
45400 FLEURY-LES-AUBRAIS
Bat : B Etg : 2 Por : 21"""
FICHE_M="""INFORMATIONS PATIENT
BERNARD DOMINIQUE
Né(e) le 02/02/1960 - 66 A
Sexe : M
Tél patient 06 55 66 77 88
INTERVENTION
08/11/2026 11:00
LOMBALGIE
ADRESSE PATIENT
3 RUE BANNIER
45000 ORLEANS"""
FICHE_UNK="""INFORMATIONS PATIENT
ZORGLUB XYLO
Né(e) le 09/09/1980 - 46 A
Tél patient 06 00 11 22 33
INTERVENTION
08/11/2026 11:30
TOUX
ADRESSE PATIENT
5 RUE JEANNE D ARC
45000 ORLEANS"""
async def unlock(page,uid,xp):
    await page.add_init_script(f"try{{localStorage.setItem('sos_xp','{'true' if xp else 'false'}');localStorage.setItem('sos_xpsug','true');localStorage.setItem('sos_excomplet','0');}}catch(e){{}}")
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
    await page.evaluate("()=>{window.__printed=0;window.print=()=>{window.__printed++;};}")
R="""(sel)=>{const e=document.querySelector(sel);if(!e)return null;const b=e.getBoundingClientRect();return {t:Math.round(b.top),b:Math.round(b.bottom),l:Math.round(b.left),r:Math.round(b.right),h:Math.round(b.height),w:Math.round(b.width),vis:!!(b.width&&b.height)};}"""
def age_of(d,m,y):
    n=datetime.date.today(); a=n.year-y-((n.month,n.day)<(m,d)); return a
async def run(b,w,h,xp,label,tag):
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=2 if w<500 else 1,is_mobile=w<500,has_touch=w<500)
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
    await unlock(page,"fp"+tag,xp); L=label+" : "; phone=w<500
    await page.evaluate("()=>{newPatient();state.xpManual=true;state.cot=state.cot||cotDefault();state.cot.lieu='cabinet';state.cot.auto=false;render();}"); await page.wait_for_timeout(400)
    pfx="xi_" if (phone and xp) else "f_"   # Express iPhone : bloc identité de l'Express (la carte complète est repliée dans « Plus ») ; sinon carte Patient
    ids=[pfx+k for k in ("patient","prenom","ddn","sexe","poids")]
    # ---------- 1. bloc identité : en tête, ordre, une ou deux lignes, couleur du mode, gros caractères ----------
    st=await page.evaluate("""(a)=>{const [pfx,ids]=a;const box=document.getElementById(pfx+'ident');if(!box)return {box:false};const main=box.querySelector('.id-main');
      const order=[...main.querySelectorAll('input,.segs')].map(e=>e.id);const r=id=>{const e=document.getElementById(id);const b=e.getBoundingClientRect();return {t:Math.round(b.top),h:Math.round(b.height),w:Math.round(b.width)};};
      const rects=ids.map(r);const card=box.closest('.pcard,.xp');const first=card?[...card.children].find(e=>!e.classList.contains('pcard-h')&&!e.classList.contains('favbar')):null;
      const probe=document.createElement('span');probe.style.color='var(--mode)';document.body.appendChild(probe);const mode=getComputedStyle(probe).color;probe.remove();
      const cs=getComputedStyle(box);const fs=parseFloat(getComputedStyle(document.getElementById(pfx+'patient')).fontSize);
      return {box:true,order,rects,first:first?(first.id||first.className):'',inWho:!!box.closest('.xp-who'),border:cs.borderTopColor,mode,bw:cs.borderTopWidth,fs,sexBtns:[...document.querySelectorAll('#'+pfx+'sexe [data-sex]')].map(x=>x.textContent.trim())};}""",[pfx,ids])
    ok(L+"bloc identité présent, tout en haut de la carte patient (premier élément après le titre)",st.get("box") and (st["first"].startswith(pfx+"ident") or st["inWho"]),st)
    ok(L+"ordre fixe : Nom · Prénom · Date de naissance · Sexe · Poids",st.get("order")==ids,st.get("order"))
    tops=[x["t"] for x in st.get("rects",[])]
    if phone: ok(L+"iPhone : deux lignes (Nom et Prénom ; Naissance, Sexe, Poids)",len(tops)==5 and tops[0]==tops[1] and tops[2]==tops[3]==tops[4] and tops[2]>tops[0],tops)
    else: ok(L+"ordinateur : une seule ligne",len(tops)==5 and len(set(tops))==1,tops)
    ok(L+"encadré de la couleur du mode (Consultation), bordure ≥ 2 px",st.get("border")==st.get("mode") and float(str(st.get("bw","0")).replace("px",""))>=2,(st.get("border"),st.get("mode"),st.get("bw")))
    ok(L+"gros caractères (≥ 18 px iPhone, ≥ 20 px ordinateur), sexe F / M",st.get("fs",0)>=(18 if phone else 20) and st.get("sexBtns")==["F","M"],(st.get("fs"),st.get("sexBtns")))
    # ---------- 2. saisie : Entrée passe au champ suivant, NOM Prénom séparés, âge calculé, sexe déduit du prénom, Tab ----------
    await page.focus("#"+ids[0]); await page.keyboard.type("dupont marie"); await page.keyboard.press("Enter"); await page.wait_for_timeout(450)
    s2=await page.evaluate("(ids)=>({nom:document.getElementById(ids[0]).value,pre:document.getElementById(ids[1]).value,pat:state.patient,focus:document.activeElement&&document.activeElement.id,sexe:state.sexe,src:state.sexeSrc})",ids)
    ok(L+"« dupont marie » puis Entrée : NOM en capitales, prénom séparé (« DUPONT Marie »), focus sur la date de naissance",s2["nom"]=="DUPONT" and s2["pre"]=="Marie" and s2["pat"]=="DUPONT Marie" and s2["focus"]==ids[2],s2)
    ok(L+"sexe déduit du prénom (Marie → F), marqué comme déduit",s2["sexe"]=="f" and s2["src"]=="prenom",s2)
    await page.keyboard.type("03041958"); await page.keyboard.press("Enter"); await page.wait_for_timeout(450)
    s3=await page.evaluate("(ids)=>({ddn:state.ddn,age:(document.getElementById(ids[0].replace('patient','age'))||{}).textContent,focus:document.activeElement&&document.activeElement.id,guess:!!document.querySelector('#'+ids[3]+'.guess'),mark:!!document.querySelector('#'+ids[0].replace('patient','ident')+' .id-g')})",ids)
    ok(L+"« 03041958 » puis Entrée : date normalisée, âge calculé affiché, focus sur le poids (sexe déjà déduit)",s3["ddn"]=="03/04/1958" and s3["age"]==f"{age_of(3,4,1958)} ans" and s3["focus"]==ids[4],s3)
    ok(L+"sexe déduit affiché en pointillé avec la mention « prénom ? » (à confirmer d'un toucher)",s3["guess"] and s3["mark"],s3)
    await page.keyboard.type("72"); await page.keyboard.press("Enter"); await page.wait_for_timeout(450)
    s4=await page.evaluate("()=>({poids:state.poids,focus:document.activeElement&&document.activeElement.id})")
    ok(L+"« 72 » puis Entrée : poids enregistré, focus sur le motif (recherche de fiche)",s4["poids"]=="72" and s4["focus"] in ("q","xp_motif","xp_q"),s4)
    await page.focus("#"+ids[0]); await page.keyboard.press("Tab"); await page.wait_for_timeout(100)
    ok(L+"Tab passe aussi du nom au prénom",await page.evaluate("()=>document.activeElement&&document.activeElement.id")==ids[1])
    await page.click("#"+ids[3]+" [data-sex='h']"); await page.wait_for_timeout(400)
    s5=await page.evaluate("(ids)=>({sexe:state.sexe,src:state.sexeSrc,guess:!!document.querySelector('#'+ids[3]+'.guess'),on:(document.querySelector('#'+ids[3]+' .on')||{}).textContent,ne:neLe(),acc:sexAccord('Je vous adresse le/la patient(e), examiné(e) ce jour.')})",ids)
    ok(L+"toucher M : sexe homme confirmé (plus de pointillé), « né le », accords au masculin sur les documents",s5["sexe"]=="h" and s5["src"]=="" and not s5["guess"] and s5["on"]=="M" and s5["ne"]=="né le " and s5["acc"]=="Je vous adresse le patient, examiné ce jour.",s5)
    await page.click("#"+ids[3]+" [data-sex='f']"); await page.wait_for_timeout(400)
    s6=await page.evaluate("()=>({ne:neLe(),acc:sexAccord('Je vous adresse le/la patient(e), examiné(e) ce jour.')})")
    ok(L+"toucher F : « née le », accords au féminin",s6["ne"]=="née le " and s6["acc"]=="Je vous adresse la patiente, examinée ce jour.",s6)
    await page.evaluate("()=>{state.sexe='';state.sexeSrc='';render();}"); await page.wait_for_timeout(300)
    s7=await page.evaluate("(ids)=>{const g=document.getElementById(ids[3]);const f=g&&g.closest('.id-sex');return {miss:!!(f&&f.classList.contains('miss')),q:!!(f&&f.querySelector('.id-l .q')),ne:neLe()};}",ids)
    ok(L+"sexe obligatoire : sans sexe, le champ est signalé en rouge (« Sexe ? ») et les documents restent neutres (« date de naissance : »)",s7["miss"] and s7["q"] and s7["ne"]=="date de naissance : ",s7)
    await page.click("#"+ids[3]+" [data-sex='f']"); await page.wait_for_timeout(300)
    # ---------- 3. âge et poids pilotent les doses ----------
    r3=await page.evaluate("""()=>{const pi=PACKS.findIndex(p=>/enfant/i.test(p.n)&&p.s.some(sh=>sh.k==='med'&&sh.l.some(l=>/\\{(ml|mg|mgpk):/.test(typeof l==='string'?l:l.t))));if(pi<0)return null;
      state.ddn='03/04/2021';state.sexe='h';state.poids='18';state.sel=pi;state.off={};state.lo={};state.gs={};render();const p=currentPack();const si=p.s.findIndex(sh=>sh.k==='med');const a=resolve(p.s[si],si).filter(x=>/\\d/.test(x.fill.s)).map(x=>x.fill.s).join(' | ');
      state.poids='24';render();const b=resolve(p.s[si],si).filter(x=>/\\d/.test(x.fill.s)).map(x=>x.fill.s).join(' | ');return {pack:p.n,a:a.slice(0,160),b:b.slice(0,160),diff:a!==b,age:ageLabel()};}""")
    ok(L+"doses au poids : les lignes de médicaments changent avec le poids (18 → 24 kg) sur une fiche enfant, âge affiché",r3 and r3["diff"] and r3["age"]==f"{age_of(3,4,2021)} ans",r3)
    await page.evaluate("()=>{newPatient();state.xpManual=true;Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f',poids:'72'});state.cot.lieu='cabinet';state.cot.auto=false;render();}"); await page.wait_for_timeout(400)
    # ---------- 4. lignes Allergies et Traitements juste sous l'identité, visibles ----------
    pc_card="#xp_plus .pcard:has(> #f_ident)" if (phone and xp) else ".pcard:has(> #f_ident)"
    if phone and xp: await page.evaluate("()=>{const d=document.getElementById('xp_plus');if(d)d.open=true;}")
    s8=await page.evaluate("""(sel)=>{const card=document.querySelector(sel);if(!card)return null;const K=[...card.children];const kids=K.map(e=>e.id||e.className);const al=card.querySelector('.tt.al'),tt=card.querySelector('.tt:not(.al)');
      const ix=f=>K.findIndex(f);const iId=ix(e=>e.id==='f_ident'),iAl=ix(e=>e.classList.contains('tt')&&e.classList.contains('al')),iTt=ix(e=>e.classList.contains('tt')&&!e.classList.contains('al'));
      const vis=e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0;};return {kids,al:!!al,tt:!!tt,alVis:al&&vis(al),ttVis:tt&&vis(tt),pen:!!(al&&al.querySelector('.tl .pen #f_all')),alBefore:iAl>=0&&iAl<iTt,identBefore:iId>=0&&iId<iAl};}""",pc_card)
    ok(L+"Allergies (champ + case « Allergie aux pénicillines ») puis Traitements en cours, juste sous l'identité, visibles sans dépliage",s8 and s8["identBefore"] and s8["alBefore"] and s8["alVis"] and s8["ttVis"] and s8["pen"],s8)
    await page.focus(pc_card+" #f_tt"); await page.keyboard.type("metf"); await page.wait_for_timeout(300)
    sg=await page.evaluate("()=>[...document.querySelectorAll('#sg_tt .sg')].map(b=>b.textContent)")
    await page.keyboard.press("Enter"); await page.wait_for_timeout(400)
    ok(L+"Traitements : « metf » propose METFORMINE depuis la base médicaments, Entrée l'ajoute",any("METFORMINE" in x.upper() for x in sg) and "METFORMINE" in await page.evaluate("()=>state.tt.join('|')"),(sg,await page.evaluate("()=>state.tt")))
    await page.focus(pc_card+" #f_al"); await page.keyboard.type("Iode"); await page.keyboard.press("Enter"); await page.wait_for_timeout(400)
    await page.click(pc_card+" #f_all"); await page.wait_for_timeout(400)
    s9=await page.evaluate("()=>({al:state.allergies.slice(),pen:state.allergie,chips:[...document.querySelectorAll('.pcard .tt.al .chip:not(.prop)')].map(c=>c.textContent.replace('×','').trim())})")
    ok(L+"Allergies : « Iode » ajouté, case pénicillines cochée → allergie pénicillines retenue, pastilles visibles",s9["al"][0].startswith("Iode") and s9["pen"] and any("nicillin" in c.lower() for c in s9["chips"]),s9)
    r4=await page.evaluate("""()=>{const pi=PACKS.findIndex(p=>p.n==='Lombalgie aiguë');state.sel=pi;state.off={};state.lo={};state.gs={};state.tt=['PREVISCAN'];render();const A=checkAlerts(currentPack().s);return {n:A.length,hit:A.some(t=>/AVK|anticoag|INR|fluindione|PREVISCAN/i.test(String(t)))};}""")
    ok(L+"Traitements : AVK saisi + fiche avec AINS → alerte d'interaction affichée avant l'ordonnance",r4["hit"],r4)
    # ---------- 5. propositions des documents scannés : à valider, rien n'est repris sans accord ----------
    await page.evaluate("""()=>{state.sel=null;state.tt=['METFORMINE'];state.allergies=[];state.allergie=false;state.docProps=null;
      const ana=(o)=>Object.assign({meds:[],allergies:[],atcd:[],labs:null,vacc:[],concl:'',spe:'',date:'',err:''},o);
      state.docs=[{id:'d1',type:'ordo',label:'',ts:Date.now(),date:'01/10/2026',src:'test',pages:[{id:'p1',ok:true,text:'RAMIPRIL 5 mg le matin'}],text:'RAMIPRIL 5 mg le matin',ana:ana({meds:[{name:'RAMIPRIL',flags:[],poso:'5 mg le matin'}],date:'01/10/2026'})},
        {id:'d2',type:'courrier',label:'',ts:Date.now(),date:'12/09/2026',src:'test',pages:[{id:'p2',ok:true,text:'Allergie à l iode'}],text:'Allergie à l iode',ana:ana({allergies:['Iode'],date:'12/09/2026'})}];
      docProposalsBuild();render();}""")
    await page.wait_for_timeout(400)
    s10=await page.evaluate("(sel)=>{const c=document.querySelector(sel);return {tt:[...c.querySelectorAll('.tt:not(.al) .chip.prop')].map(x=>x.textContent),al:[...c.querySelectorAll('.tt.al .chip.prop')].map(x=>x.textContent),inTT:state.tt.includes('RAMIPRIL'),inAL:state.allergies.includes('Iode')};}",pc_card)
    ok(L+"documents : traitement et allergie lus apparaissent en proposition (pastille pointillée « proposé · source ») dans chaque ligne, sans être repris",len(s10["tt"])==1 and "RAMIPRIL" in s10["tt"][0] and "Ordonnance" in s10["tt"][0] and len(s10["al"])==1 and "Iode" in s10["al"][0] and not s10["inTT"] and not s10["inAL"],s10)
    await page.click(pc_card+" .tt:not(.al) .chip.prop [data-dpok]"); await page.wait_for_timeout(400)
    await page.click(pc_card+" .tt.al .chip.prop [data-dpno]"); await page.wait_for_timeout(400)
    s11=await page.evaluate("(sel)=>{const c=document.querySelector(sel);return {tt:state.tt.slice(),al:state.allergies.slice(),props:c.querySelectorAll('.chip.prop').length,poso:(state.ttInfo||{})[medKey('RAMIPRIL')],off:state.docProps&&state.docProps.allergies.length?state.docProps.allergies[0].on:'absent',card:[...document.querySelectorAll('#docprops input[data-docprop]')].map(i=>i.dataset.docprop+':'+i.checked)};}",pc_card)
    ok(L+"✓ reprend le traitement (posologie lue gardée), ✕ écarte l'allergie ; plus aucune proposition affichée",s11["tt"]==["METFORMINE","RAMIPRIL"] and s11["al"]==[] and s11["props"]==0 and s11["poso"] and s11["poso"]["poso"]=="5 mg le matin" and s11["off"] is False and s11["card"]==["allergies:0:false"],s11)
    await page.evaluate("()=>{state.docs=[];state.docProps=null;render();}"); await page.wait_for_timeout(300)
    # ---------- 6. options secondaires en plus petit, sous l'identité ; cachet coché par défaut ----------
    if phone: await page.evaluate("(sel)=>{const d=document.querySelector(sel+' details.pmore');if(d)d.open=true;}",pc_card)
    s12=await page.evaluate("""(a)=>{const [sel,phone]=a;const c=document.querySelector(sel);const o=c.querySelector('.opts.sec');if(!o)return null;const ids=[...o.querySelectorAll('input')].map(i=>i.id);const fs=parseFloat(getComputedStyle(o.querySelector('label')).fontSize);const idfs=parseFloat(getComputedStyle(c.querySelector('#f_patient')).fontSize);
      const K=[...c.children];const iTt=K.findIndex(e=>e.classList.contains('tt')&&!e.classList.contains('al'));const iO=K.findIndex(e=>e.classList.contains(phone?'pmore':'opts'));const after=iO>iTt&&iTt>=0;const det=o.closest('details.pmore');
      return {ids,fs,idfs,after,cachet:!!document.getElementById('f_cachet').checked,inDetails:!!det,sum:det?det.querySelector('summary').textContent.trim():'',gross:getComputedStyle(document.getElementById('f_gross').closest('label')).display};}""",[pc_card,phone])
    ok(L+"options secondaires (date, cachet, grossesse, allaitement, 2 par A4) sous les lignes allergies et traitements, en plus petit que l'identité",s12 and s12["after"] and s12["fs"]<s12["idfs"]*0.75 and all(k in s12["ids"] for k in ("f_date","f_cachet","f_gross","f_allait","f_2up")),s12)
    ok(L+"« Signature et cachet » coché par défaut ; grossesse et allaitement masqués pour une patiente de 68 ans",s12 and s12["cachet"] and s12["gross"]=="none",s12)
    if phone: ok(L+"iPhone : options repliées sous « Options » (allergies et traitements restent visibles)",s12 and s12["inDetails"] and s12["sum"].startswith("Options"),s12)
    await page.screenshot(path=os.path.join(OUT,f"fiche-patient-{tag}.png"))
    # ---------- 7. Visite : identité remplie depuis la fiche de régulation ----------
    OPEN="""async(t)=>{TOUR.stops=[];TOUR.order=[];TOUR.current='';TOUR.unread=[];newPatient();state.cot=state.cot||cotDefault();state.cot.lieu='visite';state.cot.auto=false;const f=parseFiche(t);const s=ficheToStop(f);tourSave();xpOpenStop(s.id);await new Promise(r=>setTimeout(r,350));
      const g=id=>{const e=document.getElementById(id);return e?e.value:null;};const sum=document.getElementById('xi_sum');
      return {fs:f.sexe,fnom:f.nom,fpre:f.prenom,pat:state.patient,ddn:state.ddn,sexe:state.sexe,src:state.sexeSrc,tel:state.nh.tel,adr:state.nh.adresse,v:{nom:g('f_patient'),pre:g('f_prenom'),ddn:g('f_ddn'),tel:g('f_tel'),adr:g('f_adr'),xnom:g('xi_patient'),xtel:g('xi_tel')},sum:sum?sum.textContent:null,sumGuess:!!(sum&&sum.querySelector('.xw-sx.guess')),miss:!!document.querySelector('.id-sex.miss'),guess:!!document.querySelector('.segs.guess'),lieu:state.cot.lieu};}"""
    v1=await page.evaluate(OPEN,FICHE_F)
    ok(L+"visite · fiche « Née le » : NOM / Prénom (« DUBOIS » / « Claire »), naissance, sexe F lu sur la fiche, téléphone et adresse repris dans le bloc identité",
       v1["fs"]=="f" and v1["pat"]=="DUBOIS Claire" and v1["ddn"]=="12/05/1958" and v1["sexe"]=="f" and v1["src"]=="fiche" and v1["tel"]=="0238001122" and "AVENUE DES PINS" in v1["adr"] and v1["v"]["nom"]=="DUBOIS" and v1["v"]["pre"]=="Claire" and v1["v"]["tel"]=="02 38 00 11 22" and "AVENUE DES PINS" in (v1["v"]["adr"] or ""),v1)
    if phone and xp:
        ok(L+"Express iPhone : identité complète → résumé d'une ligne (nom, née le, âge, F) encadré, un toucher pour modifier",v1["sum"] and "DUBOIS" in v1["sum"] and "Claire" in v1["sum"] and "née le 12/05/1958" in v1["sum"] and re.search(r"\bF\b",v1["sum"]),v1["sum"])
        await page.click("#xi_sum"); await page.wait_for_timeout(400)
        t1=await page.evaluate("()=>({nom:(document.getElementById('xi_patient')||{}).value,tel:(document.getElementById('xi_tel')||{}).value,focus:document.activeElement&&document.activeElement.id,sum:!!document.getElementById('xi_sum')})")
        ok(L+"Express iPhone : après le toucher, champs modifiables (nom, téléphone…), focus sur le nom",t1["nom"]=="DUBOIS" and t1["tel"]=="02 38 00 11 22" and t1["focus"]=="xi_patient" and not t1["sum"],t1)
        await page.fill("#xi_prenom","Claire-Marie"); await page.wait_for_timeout(500)
        ok(L+"Express iPhone : prénom corrigé d'un toucher → patient « DUBOIS Claire-Marie »",await page.evaluate("()=>state.patient")=="DUBOIS Claire-Marie")
        await page.click("#xi_close"); await page.wait_for_timeout(400)
        ok(L+"Express iPhone : « ✓ OK » replie le bloc en résumé",await page.evaluate("()=>!!document.getElementById('xi_sum')&&!document.getElementById('xi_patient')"))
    elif xp:
        ok(L+"Express ordinateur : résumé en tête de l'Express et bloc modifiable dans la carte Patient (un clic sur le résumé y conduit)",v1["sum"] and "DUBOIS" in v1["sum"] and v1["v"]["nom"]=="DUBOIS",v1)
        await page.click("#xi_sum"); await page.wait_for_timeout(500)
        ok(L+"Express ordinateur : le clic place le curseur sur le nom de la carte Patient",await page.evaluate("()=>document.activeElement&&document.activeElement.id")=="f_patient")
    v2=await page.evaluate(OPEN,FICHE_AMB)
    ok(L+"visite · fiche « Né(e) le » (ambiguë) : sexe déduit du prénom (PAUL → M), signalé comme déduit",v2["fs"]=="" and v2["pat"]=="MARTIN Paul" and v2["sexe"]=="h" and v2["src"]=="prenom" and (v2["guess"] or v2["sumGuess"]),v2)
    v3=await page.evaluate(OPEN,FICHE_M)
    ok(L+"visite · fiche « Sexe : M » avec prénom mixte (Dominique) : sexe lu sur la fiche",v3["fs"]=="h" and v3["sexe"]=="h" and v3["src"]=="fiche" and v3["pat"]=="BERNARD Dominique",v3)
    v4=await page.evaluate(OPEN,FICHE_UNK)
    ok(L+"visite · prénom inconnu et « Né(e) » : sexe laissé vide et signalé (obligatoire), rien d'inventé",v4["fs"]=="" and v4["sexe"]=="" and v4["miss"],v4)
    await page.evaluate("()=>{const s=TOUR.stops[0];const e=document.getElementById('xi_sexe')||document.getElementById('f_sexe');e.querySelector('[data-sex=\"f\"]').click();}"); await page.wait_for_timeout(400)
    ok(L+"visite : un toucher sur F fixe le sexe",await page.evaluate("()=>state.sexe")=="f")
    if phone: await page.screenshot(path=os.path.join(OUT,f"fiche-patient-{tag}-visite.png"))
    c1=await page.evaluate("""async()=>{TOUR.current='';newPatient();TOUR.consults=[{id:'c1',nom:'LEROY ANNE',pnom:'LEROY',pprenom:'ANNE',sexe:'',ddn:'01/01/1980',motif:'angine',tel:'0600000000'}];state.view='tour';render();await new Promise(r=>setTimeout(r,200));const b=document.querySelector('[data-cstart]');if(!b)return {b:false};b.click();await new Promise(r=>setTimeout(r,300));return {b:true,pat:state.patient,sexe:state.sexe,src:state.sexeSrc,lieu:state.cot.lieu};}""")
    ok(L+"consultation attendue (fiche « Chez Consultation ») : identité et sexe déduit du prénom (ANNE → F) à l'ouverture du dossier",c1.get("b") and c1["pat"]=="LEROY Anne" and c1["sexe"]=="f" and c1["src"]=="prenom" and c1["lieu"]=="cabinet",c1)
    ok(L+"aucune erreur JavaScript",not errors,errors[:3])
    await ctx.close()
async def header(b,w,xp,tag):
    ctx=await b.new_context(viewport={"width":w,"height":900}); page=await ctx.new_page(); errors=[]; page.on("pageerror",lambda e:errors.append(str(e)))
    await ctx.route(re.compile(r"^(?!.*localhost).*$"),lambda r:asyncio.ensure_future(r.abort()))
    await unlock(page,"fh"+tag,xp); L=f"en-tête {w} px {'Express' if xp else 'complet'} : "
    await page.evaluate("()=>{for(let i=0;i<2;i++)JOURNAL.push({ts:Date.now()-i*600000,patient:'TEST '+i,codes:['G'],total:25});}")
    for lieu in ("visite","cabinet"):
        for theme in ("day","night"):
            for big in (False,True):
                await page.evaluate("(a)=>{state.cot=state.cot||cotDefault();state.cot.lieu=a.lieu;state.cot.auto=false;themeSet(a.theme);try{localStorage.setItem('sos_bigtext',a.big?'1':'0');}catch(e){}themeApply();newPatient();Object.assign(state,{patient:'DURAND Martine',ddn:'03/04/1958',sexe:'f'});render();window.scrollTo(0,0);const m=document.getElementById('main');if(m)m.scrollTop=0;}",{"lieu":lieu,"theme":theme,"big":big})
                await page.wait_for_timeout(350)
                m=await page.evaluate("""()=>{const r=e=>{if(!e)return null;const b=e.getBoundingClientRect();return {t:Math.round(b.top),b:Math.round(b.bottom),l:Math.round(b.left),r:Math.round(b.right),h:Math.round(b.height)};};
                  const jb=document.querySelector('.jbar');const lieu=document.querySelector('.lieu');const xh=document.querySelector('.xp-hd, .xp-who, .pcard');const tab=lieu&&lieu.querySelector('button');
                  const tr=tab?tab.getBoundingClientRect():null;const el=tr?document.elementFromPoint(tr.left+tr.width/2,tr.top+tr.height/2):null;
                  const btnH=(()=>{const b=jb.querySelector('.btn');return b?b.getBoundingClientRect().height:0;})();
                  return {jbar:r(jb),btnH:Math.round(btnH),lieu:r(lieu),next:r(xh),theme:document.documentElement.getAttribute('data-theme'),size:document.documentElement.getAttribute('data-size'),tabHit:!!(el&&lieu.contains(el)),overflow:jb.scrollWidth>jb.clientWidth+1,
                    j:!!(document.getElementById('j_open')&&document.getElementById('j_open').offsetParent),f:!!(document.getElementById('f_open')&&document.getElementById('f_open').offsetParent),more:!!(document.getElementById('more_pc')&&document.getElementById('more_pc').offsetParent),dopen:!!(document.getElementById('d_open')&&document.getElementById('d_open').offsetParent),tag:!!document.querySelector('.jbar .pat-tag'),bg:getComputedStyle(jb).backgroundColor};}""")
                S=f"{lieu} · {m['theme']} · {'grand texte' if big else 'texte normal'} : "
                ok(L+S+"une seule ligne (hauteur ≤ 1,6 bouton), rien ne déborde, étiquette du patient en ligne",m["jbar"] and m["jbar"]["h"]<=m["btnH"]*1.6+2 and not m["overflow"] and m["tag"],m)
                ok(L+S+"onglets Visite / Consultation entièrement sous la barre et cliquables, carte suivante non recouverte",m["lieu"] and m["lieu"]["t"]>=m["jbar"]["b"]-1 and m["tabHit"] and m["next"] and m["next"]["t"]>=m["lieu"]["b"]-1,m)
                ok(L+S+"« Journal » et « Fin de garde » visibles ; secondaires dans ⋯ quand la place manque",m["j"] and m["f"] and (m["more"]!=m["dopen"]) and (m["more"] if (w<1500 or (big and w<1700)) else (not m["more"] and m["dopen"])),m)
                if m["more"]:
                    await page.click("#more_pc"); await page.wait_for_timeout(200)
                    o=await page.evaluate("()=>{const d=document.getElementById('d_open');const r=d.getBoundingClientRect();const jb=document.querySelector('.jbar').getBoundingClientRect();return {vis:!!d.offsetParent,below:r.top>=jb.bottom-4,inView:r.right<=innerWidth&&r.left>=0,items:[...document.querySelectorAll('#jsec .btn')].map(b=>b.id)};}")
                    ok(L+S+"⋯ ouvre version, mode test, base médicaments, tournée sous la barre",o["vis"] and o["below"] and o["inView"] and all(k in o["items"] for k in ("t_toggle","d_open","tour_open")),o)
                    await page.keyboard.press("Escape"); await page.wait_for_timeout(150)
                    ok(L+S+"Échap (ou un clic ailleurs) referme ⋯",not await page.evaluate("()=>!!document.querySelector('.jbar.pc.open')"))
                if theme=="night" and big and lieu=="visite": await page.screenshot(path=os.path.join(OUT,f"entete-{w}-{tag}-nuit-grand.png"),clip={"x":0,"y":0,"width":w,"height":380})
                if theme=="day" and not big and lieu=="cabinet": await page.screenshot(path=os.path.join(OUT,f"entete-{w}-{tag}-jour.png"),clip={"x":0,"y":0,"width":w,"height":380})
    ok(L+"aucune erreur JavaScript",not errors,errors[:3])
    await ctx.close()
async def main():
    os.makedirs(OUT,exist_ok=True)
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1.2)
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            await run(b,1280,900,False,"ordinateur 1280 · complet","pc")
            await run(b,1280,900,True,"ordinateur 1280 · Express","pcxp")
            await run(b,375,812,False,"iPhone 375 · complet","iphone")
            await run(b,375,812,True,"iPhone 375 · Express","iphonexp")
            for w in (1280,1920):
                for xp in (True,False): await header(b,w,xp,"xp" if xp else "complet")
            await b.close()
    finally: srv.terminate()
    n=sum(1 for r in results if r[1]); print(f"\n{n}/{len(results)} tests OK")
    with open(os.path.join(ROOT,"tests","resultats_fiche_patient_v41z.md"),"w",encoding="utf-8") as f:
        f.write(f"# Fiche patient (08/11/2026) — {n}/{len(results)} tests OK\n\nBloc identité, allergies et traitements, options, fiche de régulation, en-tête ordinateur. Patients fictifs.\n\n| Résultat | Point | Détail |\n|---|---|---|\n")
        for name,c,info in results: f.write(f"| {'OK' if c else 'ÉCHEC'} | {name} | {'' if c else str(info)[:300].replace('|','／')} |\n")
    sys.exit(0 if n==len(results) else 1)
asyncio.run(main())
