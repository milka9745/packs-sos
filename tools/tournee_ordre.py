# -*- coding: utf-8 -*-
# 26/11/2026 — Tournée : déplacer une visite par appui long puis glisser, et « Optimiser la tournée » selon la priorité posée.
# Demande du médecin : « déplacer l'ordre des visites en appuyant de façon prolongée et les déplacer ; appuyer sur optimiser
# pour optimiser l'ordre de la visite selon l'endroit où j'ai mis la priorité ».
#  1. Écran Tournée : appui long (550 ms, immobile) sur une visite puis glisser — l'ordre devient manuel (plus de recalcul
#     automatique, ▲ ▼ aussi) ; le défilement est bloqué pendant le glisser (touchmove non passif) ; la cible est la première
#     visite sous le doigt, même sous un message passager ;
#  2. bouton « ⟳ Optimiser la tournée » (dès 2 visites) : en ordre manuel, les prioritaires ★ restent en tête dans l'ordre du
#     médecin (à défaut, la première visite de sa liste), puis la suite est calculée au plus court (OSRM, sinon vol d'oiseau)
#     à partir du dernier prioritaire ; l'ordre reste manuel ; en ordre automatique, recalcul complet ; les ancres sont
#     calculées avant tout appel réseau, pour que le repli hors connexion les respecte aussi ;
#  3. message d'ordre : « Ordre manuel · optimisé à HH:MM à partir de X » ; un déplacement à la main l'efface ;
#     optTs / optFrom enregistrés avec la tournée.
# Usage : python tools/tournee_ordre.py index.html [test/index.html ...] — chaque remplacement doit s'appliquer le nombre
# de fois attendu, sinon rien n'est écrit.
import sys

REPL=[
 ("tourOptimize : option reopt et ancres (avant tout appel réseau)",
  "async function tourOptimize(){",
  "async function tourOptimize(opt){opt=opt||{};let anchors=[];if(opt.reopt){try{const ordR=tourOrdered().filter(s=>s.lat&&s.id!==TOUR.current);anchors=ordR.filter(s=>s.prio);if(!anchors.length&&ordR.length)anchors=[ordR[0]];}catch(e){anchors=[];}} /* 26/11/2026 : opt.reopt = « Optimiser la tournée » en ordre manuel — ancres = prioritaires dans l'ordre du médecin (sinon la première visite), puis la suite au plus court */"),
 ("tourOptimize : la branche manuelle ne s'applique pas à l'optimisation demandée",
  "  if(TOUR.manual){try{for(const s of TOUR.stops)",
  "  if(TOUR.manual&&!opt.reopt){try{for(const s of TOUR.stops)"),
 ("tourOptimize : groupes avec ancres",
  "    const groups=[{l:rem.filter(s=>s.prio)},{l:rem.filter(s=>!s.prio&&avantOf(s)).sort((a,b)=>avantOf(a).localeCompare(avantOf(b))),fixed:true},{l:rem.filter(s=>!s.prio&&!avantOf(s)&&waitOf(s))},{l:rem.filter(s=>!s.prio&&!avantOf(s)&&!waitOf(s))}].filter(g=>g.l.length);",
  "    const remR=opt.reopt?rem.filter(s=>!anchors.includes(s)):rem.filter(s=>!s.prio); /* 26/11/2026 : en optimisation manuelle, les ancres sortent du calcul */\n"
  "    const groups=[opt.reopt?{l:anchors.filter(s=>rem.includes(s)),fixed:true}:{l:rem.filter(s=>s.prio)},{l:remR.filter(s=>avantOf(s)).sort((a,b)=>avantOf(a).localeCompare(avantOf(b))),fixed:true},{l:remR.filter(s=>!avantOf(s)&&waitOf(s))},{l:remR.filter(s=>!avantOf(s)&&!waitOf(s))}].filter(g=>g.l.length);"),
 ("tourOptimize : fin de calcul (ordre manuel conservé, horodatage de l'optimisation)",
  "TOUR.order=order;TOUR.legs=legs;TOUR.est=false;TOUR.total={km:Math.round(km*10)/10,min:Math.round(min)};TOUR.computed=Date.now();TOUR.autoTs=TOUR.computed;TOUR.autoSrc=TOUR.startSrc||\"le cabinet\";tourChgSet(before,order);",
  "TOUR.order=order;TOUR.legs=legs;TOUR.est=false;TOUR.total={km:Math.round(km*10)/10,min:Math.round(min)};TOUR.computed=Date.now();if(opt.reopt){TOUR.manual=true;TOUR.optTs=TOUR.computed;TOUR.optFrom=anchors.length?stopName(anchors[anchors.length-1],\"\"):\"\";}else{TOUR.autoTs=TOUR.computed;TOUR.autoSrc=TOUR.startSrc||\"le cabinet\";}tourChgSet(before,order);"),
 ("tourOptimize : repli hors connexion avec ancres",
  "}catch(e){if(tpOffline())TOUR.status=(navigator.onLine===false?\"hors connexion\":\"itinéraire indisponible\")+\" — ordre et heures estimés à vol d'oiseau (majoré)\";else TOUR.status=",
  "}catch(e){if(tpOffline(opt.reopt?anchors:null)){if(opt.reopt){TOUR.manual=true;TOUR.optTs=Date.now();TOUR.optFrom=anchors.length?stopName(anchors[anchors.length-1],\"\"):\"\";}TOUR.status=(navigator.onLine===false?\"hors connexion\":\"itinéraire indisponible\")+\" — ordre et heures estimés à vol d'oiseau (majoré)\";}else TOUR.status="),
 ("tpOffline : ancres en tête puis plus proche voisin",
  "function tpOffline(){const rem=tourRemaining().filter(s=>s.lat&&s.id!==TOUR.current);let pos=tpRef();if(!pos&&!rem.length)return false;",
  "function tpOffline(anchors){const rem0=tourRemaining().filter(s=>s.lat&&s.id!==TOUR.current);const A=(anchors||[]).filter(s=>rem0.includes(s));const rem=rem0.filter(s=>!A.includes(s));let pos=tpRef();if(!pos&&!rem0.length)return false; /* 26/11/2026 : ancres (prioritaires dans l'ordre du médecin) en tête */"),
 ("tpOffline : parcours",
  "const before=TOUR.order.slice();pick(rem.filter(s=>s.prio));pick(rem.filter(s=>!s.prio&&tpWait(s)>0));pick(rem.filter(s=>!s.prio&&!(tpWait(s)>0)));",
  "const before=TOUR.order.slice();if(A.length){A.forEach(s=>{const lg=pos?tpCrow(pos,s):{km:0,min:0};order.push(s.id);legs.push({km:lg.km,min:lg.min});km+=lg.km;min+=lg.min;pos=s;});pick(rem.filter(s=>tpWait(s)>0));pick(rem.filter(s=>!(tpWait(s)>0)));}else{pick(rem.filter(s=>s.prio));pick(rem.filter(s=>!s.prio&&tpWait(s)>0));pick(rem.filter(s=>!s.prio&&!(tpWait(s)>0)));}"),
 ("message d'ordre manuel",
  "function tourAutoMsg(){if(TOUR.manual)return \"Ordre manuel : conservé tel quel\";",
  "function tourAutoMsg(){if(TOUR.manual)return TOUR.optTs?\"Ordre manuel · optimisé à \"+fmtH(TOUR.optTs)+(TOUR.optFrom?\" à partir de \"+TOUR.optFrom:\"\")+\" · appui long sur une visite pour la déplacer\":\"Ordre manuel : conservé tel quel · appui long sur une visite pour la déplacer · « Optimiser la tournée » recalcule la suite\";"),
 ("tourLoad : optTs / optFrom",
  "TOUR.autoSrc=t.autoSrc||\"\";",
  "TOUR.autoSrc=t.autoSrc||\"\";TOUR.optTs=t.optTs||0;TOUR.optFrom=t.optFrom||\"\";"),
 ("tourSave : optTs / optFrom",
  "autoSrc:TOUR.autoSrc||\"\",",
  "autoSrc:TOUR.autoSrc||\"\",optTs:TOUR.optTs||0,optFrom:TOUR.optFrom||\"\","),
 ("carte : bascule manuel / automatique",
  "TOUR.manual=!TOUR.manual;tourSave();if(TOUR.manual){state.view=\"tour\";render();toast(\"Ordre manuel : ▲ ▼ sur chaque visite ; plus de recalcul automatique\");}",
  "TOUR.manual=!TOUR.manual;TOUR.optTs=0;TOUR.optFrom=\"\";tourSave();if(TOUR.manual){state.view=\"tour\";render();toast(\"Ordre manuel : appui long sur une visite pour la déplacer (ou ▲ ▼) ; « Optimiser la tournée » recalcule la suite ; plus de recalcul automatique\");}"),
 ("▲ ▼ : un déplacement efface l'horodatage de l'optimisation",
  "[o[i],o[j]]=[o[j],o[i]];TOUR.order=o;tourSave();render();",
  "[o[i],o[j]]=[o[j],o[i]];TOUR.order=o;TOUR.optTs=0;TOUR.optFrom=\"\";tourSave();render();"),
 ("lignes de la liste : identifiant de visite (glisser)",
  "return `<div class=\"trow${s.prio?\" prio\":\"\"}${s.err?\" err\":\"\"}\"><div class=\"trank\">",
  "return `<div class=\"trow${s.prio?\" prio\":\"\"}${s.err?\" err\":\"\"}\" data-tid=\"${esc(s.id)}\"><div class=\"trank\">"),
 ("bouton Optimiser la tournée",
  "<button type=\"button\" class=\"btn p sm\" id=\"tr_begin\" title=\"Ordre optimal si besoin, puis première visite en cours\">▶ Commencer la tournée</button>",
  "<button type=\"button\" class=\"btn p sm\" id=\"tr_begin\" title=\"Ordre optimal si besoin, puis première visite en cours\">▶ Commencer la tournée</button>${n>=2?`<button type=\"button\" class=\"btn s sm\" id=\"tr_opt\" title=\"Vos prioritaires ★ restent en tête dans votre ordre (sinon la première visite de la liste), puis la suite est calculée au plus court\">⟳ Optimiser la tournée</button>`:\"\"}"),
 ("gestionnaire du bouton Optimiser",
  "{const trb=$(\"#tr_begin\");if(trb)trb.onclick=tourBegin;",
  "{const tro=$(\"#tr_opt\");if(tro)tro.onclick=()=>{if(TOUR.busy)return;toast(TOUR.manual?\"Optimisation : prioritaires en tête, puis la suite au plus court\":\"Recalcul de l'ordre\");tourOptimize(TOUR.manual?{reopt:true}:undefined).catch(()=>{});}; /* 26/11/2026 */\n"
  "   const trb=$(\"#tr_begin\");if(trb)trb.onclick=tourBegin;"),
 ("aide au-dessus de la liste",
  "   <div class=\"jlist\">${curRow}",
  "   ${n>=2?`<div class=\"hint tr-drag\">Appui long sur une visite pour la déplacer, puis relâchez ; « Optimiser la tournée » garde vos prioritaires ★ en tête dans votre ordre et calcule la suite au plus court.</div>`:\"\"}<div class=\"jlist\">${curRow}"),
 ("glisser-déposer des visites (fonctions et appui long)",
  "function tourStatusUI(){",
  "/* 26/11/2026 : appui long (550 ms, immobile) sur une visite de l'écran Tournée, puis glisser : l'ordre devient manuel ; « Optimiser la tournée » garde les prioritaires en tête puis calcule la suite */\n"
  "function tourDragStart(row){const list=row.parentElement;if(!list)return;TOUR.drag={row,list,moved:false};row.classList.add(\"tdragging\");document.body.classList.add(\"t-dragging\");try{if(navigator.vibrate)navigator.vibrate(15);}catch(e){}document.addEventListener(\"touchmove\",tourDragBlock,{passive:false});toast(\"Glissez la visite, relâchez pour la poser\");}\n"
  "function tourDragBlock(ev){if(TOUR.drag)ev.preventDefault();}\n"
  "function tourDragMove(ev){const D=TOUR.drag;if(!D)return;if(ev.clientY<90)window.scrollBy(0,-14);else if(ev.clientY>innerHeight-90)window.scrollBy(0,14);let t=null;for(const el of document.elementsFromPoint(ev.clientX,ev.clientY)){const r=el.closest&&el.closest(\".trow[data-tid]\");if(r){t=r;break;}}if(!t||t===D.row||t.parentElement!==D.list)return;const r=t.getBoundingClientRect();if(ev.clientY<r.top+r.height/2)D.list.insertBefore(D.row,t);else D.list.insertBefore(D.row,t.nextSibling);D.moved=true;}\n"
  "function tourDragEnd(){const D=TOUR.drag;if(!D)return;TOUR.drag=null;D.row.classList.remove(\"tdragging\");document.body.classList.remove(\"t-dragging\");document.removeEventListener(\"touchmove\",tourDragBlock);\n"
  "  const ids=[...D.list.querySelectorAll(\".trow[data-tid]\")].map(e=>e.dataset.tid).filter(id=>id!==TOUR.current);const before=TOUR.order.filter(x=>x!==TOUR.current);if(!D.moved||ids.join(\"|\")===before.join(\"|\"))return;\n"
  "  TOUR.manual=true;TOUR.order=ids;TOUR.optTs=0;TOUR.optFrom=\"\";tourSave();render();toast(\"Ordre modifié à la main · « Optimiser la tournée » recalcule la suite\");tpLegsRefresh().then(()=>{tpEtaApply();tourSave();render();}).catch(()=>{});}\n"
  "(function(){let timer=null,start=null;const cancel=()=>{if(timer){clearTimeout(timer);timer=null;}start=null;};\n"
  "  document.addEventListener(\"pointerdown\",ev=>{if(ev.pointerType===\"mouse\"&&ev.button!==0)return;const tgt=ev.target;if(!tgt||!tgt.closest)return;if(tgt.closest(\"input,textarea,select,button,a,label,summary,.tedit,.sugg\"))return;const row=tgt.closest(\"#main .jlist .trow[data-tid]\");if(!row)return;start={x:ev.clientX,y:ev.clientY,row};timer=setTimeout(()=>{timer=null;if(!start)return;const r=start.row;start=null;tourDragStart(r);},550);},{passive:true});\n"
  "  document.addEventListener(\"pointermove\",ev=>{if(start&&!TOUR.drag){if(Math.abs(ev.clientX-start.x)>10||Math.abs(ev.clientY-start.y)>10)cancel();return;}if(TOUR.drag)tourDragMove(ev);},{passive:true});\n"
  "  document.addEventListener(\"pointerup\",()=>{if(TOUR.drag)tourDragEnd();cancel();},{passive:true});\n"
  "  document.addEventListener(\"pointercancel\",()=>{if(TOUR.drag)tourDragEnd();cancel();},{passive:true});})();\n"
  "function tourStatusUI(){"),
 ("CSS du glisser",
  ".trow.prio{border-color:var(--gold)}",
  ".trow.prio{border-color:var(--gold)}.trow.tdragging{opacity:.85;outline:2px solid var(--gold2);box-shadow:0 8px 20px rgba(0,0,0,.25);position:relative;z-index:3}body.t-dragging{cursor:grabbing;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}.trow .trank,.trow .tmain{-webkit-touch-callout:none}.hint.tr-drag{margin:6px 0 2px}"),
]

def apply(path):
    raw=open(path,"rb").read(); nl="\r\n" if b"\r\n" in raw[:20000] else "\n"
    s=raw.decode("utf-8")
    for item in REPL:
        lab,a,b=item[0],item[1],item[2]; want=item[3] if len(item)>3 else 1
        a2=a.replace("\n",nl); b2=b.replace("\n",nl); n=s.count(a2)
        if n!=want: sys.exit(f"ÉCHEC {path} : « {lab} » trouvé {n} fois (attendu {want}) — rien n'est écrit")
        s=s.replace(a2,b2)
    open(path,"wb").write(s.encode("utf-8"))
    print(f"{path} : {len(REPL)} remplacements appliqués")

if __name__=="__main__":
    for p in sys.argv[1:]: apply(p)
