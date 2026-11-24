# -*- coding: utf-8 -*-
# 24/11/2026 — Renouvellement d'ordonnance, patients en ALD ou non (demande du médecin : « pouvoir faire des renouvellements
# d'ordonnance de médicaments des patients ALD ou non »). La fiche « Renouvellement d'ordonnance » (bloc 17, 11/11/2026) existait
# avec la base ANSM et la case ALD ligne par ligne ; ce script la rend accessible et rapide :
#  1. mode complet (ordinateur et iPhone hors Express) : le panneau passe en tête de la fiche, sous le bloc patient et avant la
#     dictée (il était rendu après les cartes dictée, documents et synthèse, à 2 000 px du haut sur ordinateur) ; il devient un
#     bloc « rnw » de « Organiser ma fiche » (sans clé, il suivait le bloc précédent et finissait après la dictée sur téléphone) ;
#     un ordre personnalisé enregistré avant son existence le place aussi après le patient ;
#  2. interrupteur « Patient en ALD (100 %) » : toutes les lignes passent à 100 % (ordonnance bizone), les lignes ajoutées
#     ensuite aussi ; chaque ligne reste modifiable (décochée = partie « maladies intercurrentes ») ; remis à zéro par « Nouveau
#     patient » ;
#  3. traitement en cours du patient (chips « Traitements en cours » du bloc patient, dictée ou IA) proposé en un geste dans
#     le panneau : une seule présentation dans la base ANSM → « + AMLOR 5 mg » ajoute la ligne ; plusieurs ou aucune →
#     « metformine … » prérempli la recherche pour choisir la présentation (jamais de dosage deviné).
# Usage : python tools/renouvellement_ald.py index.html [test/index.html ...] — chaque remplacement doit s'appliquer le nombre
# de fois attendu, sinon rien n'est écrit.
import sys

REPL=[
 ("panneau en tête (calcul)",
  "if(rnwIsPack(p)&&!(isPhone()&&xpActive()))extra=rnwHTML(p)+extra; /* 11/11/2026 : renouvellement d'ordonnance (en Express, le panneau est dans la section Express) */",
  "const rnwTop=(rnwIsPack(p)&&!(isPhone()&&xpActive()))?rnwHTML(p):\"\"; /* 11/11/2026 : renouvellement d'ordonnance (en Express, le panneau est dans la section Express) ; 24/11/2026 : en tête de la fiche, sous le bloc patient et avant la dictée (bloc « rnw ») */"),
 ("panneau en tête (téléphone, mode complet)",
  "m.innerHTML=head+dictCardHTML()+docsCardHTML()+aiSynthHTML()+titleHTML+multiNote+extra+warn+",
  "m.innerHTML=head+rnwTop+dictCardHTML()+docsCardHTML()+aiSynthHTML()+titleHTML+multiNote+extra+warn+"),
 ("panneau en tête (ordinateur)",
  "m.innerHTML=head+dictCardHTML()+docsCardHTML()+aiSynthHTML()+titleHTML+copatUI+multiNote+extra+extraOpts+warn+",
  "m.innerHTML=head+rnwTop+dictCardHTML()+docsCardHTML()+aiSynthHTML()+titleHTML+copatUI+multiNote+extra+extraOpts+warn+"),
 ("état : interrupteur ALD (rnwState et Nouveau patient)",
  "state.rnw={items:[],split:false}",
  "state.rnw={items:[],split:false,ald:false}", 2),
 ("ligne ajoutée : ALD par défaut si le patient est en ALD",
  "ald:fromRecent?!!r.ald:false};",
  "ald:S.ald?true:(fromRecent?!!r.ald:false)}; /* 24/11/2026 : patient en ALD → nouvelle ligne à 100 % */"),
 ("traitement en cours : chips calculées",
  "const rec=(RNW.recent||[]).filter(r=>!items.some(i=>i.cis===r.cis)).slice(0,8);const fit=rnwFit(items);",
  "const rec=(RNW.recent||[]).filter(r=>!items.some(i=>i.cis===r.cis)).slice(0,8);const fit=rnwFit(items);const ttRec=rnwTtChips(items);"),
 ("en-tête du panneau : interrupteur ALD et traitement en cours",
  "<div class=\"rnw\" id=\"rnw\" aria-label=\"Renouvellement d'ordonnance\"><div class=\"rnw-h\"><b>Renouvellement d'ordonnance</b><span class=\"hint\">médicaments un par un · ${base}</span></div>",
  "<div class=\"rnw\" id=\"rnw\" aria-label=\"Renouvellement d'ordonnance\"><div class=\"rnw-h\"><b>Renouvellement d'ordonnance</b><span class=\"hint\">médicaments un par un · ${base}</span></div>\n"
  "   <div class=\"rnw-row opts rnw-ald\"><label class=\"lc${S.ald?\" on\":\"\"}\"><input type=\"checkbox\" id=\"rnw_ald\" ${S.ald?\"checked\":\"\"}> Patient en ALD (100 %)</label><span class=\"hint\">${S.ald?\"ordonnance bizone : toutes les lignes en haut ; décocher une ligne la place dans « maladies intercurrentes »\":\"à cocher pour une ordonnance bizone (lignes à 100 %) ; sinon ordonnance simple\"}</span></div>\n"
  "   ${ttRec.length?`<div class=\"rnw-rec rnw-tt\" aria-label=\"Traitement en cours du patient\"><span class=\"hint\">Traitement en cours :</span>${ttRec.map(x=>x.one?`<button type=\"button\" class=\"chip\" data-rtt=\"${x.i}\" title=\"${esc(x.one.n)}\">+ ${esc(x.one.brand||x.one.n)}${x.one.dos?\" \"+esc(x.one.dos):\"\"}</button>`:`<button type=\"button\" class=\"chip\" data-rttq=\"${x.i}\" title=\"${x.n?\"choisir la présentation\":\"introuvable dans la base ANSM : vérifier l'orthographe\"}\">${esc(x.t)} …</button>`).join(\"\")}</div>`:\"\"}"),
 ("fonction rnwTtChips",
  "function rnwHTML(p){const S=rnwState();const items=S.items;const nAld=items.filter(x=>x.ald).length;",
  "/* 24/11/2026 : traitement en cours du patient (chips « Traitements en cours », dictée, IA) proposé en un geste — une seule présentation dans la base ANSM = ajout direct, sinon recherche préremplie (jamais de dosage deviné) */\n"
  "function rnwTtChips(items){try{if(!BDPMX.rows)return [];return (state.tt||[]).map((t,i)=>({t:String(t||\"\").trim(),i})).filter(x=>x.t).map(x=>{const L=bdpmxSearch(x.t,3);return {t:x.t,i:x.i,n:L.length,one:L.length===1?L[0]:null};}).filter(x=>!(x.one&&items.some(it=>it.cis===x.one.cis)));}catch(e){return [];}}\n"
  "function rnwHTML(p){const S=rnwState();const items=S.items;const nAld=items.filter(x=>x.ald).length;"),
 ("liaisons : interrupteur ALD et chips du traitement en cours",
  "document.querySelectorAll(\"[data-rrec]\").forEach(b=>b.onclick=()=>{const r=(RNW.recent||[]).find(x=>x.cis===b.dataset.rrec);if(r)rnwAdd(r,true);});",
  "document.querySelectorAll(\"[data-rrec]\").forEach(b=>b.onclick=()=>{const r=(RNW.recent||[]).find(x=>x.cis===b.dataset.rrec);if(r)rnwAdd(r,true);});\n"
  "  const sw=document.getElementById(\"rnw_ald\");if(sw)sw.onchange=()=>{const S0=rnwState();S0.ald=sw.checked;S0.items.forEach(x=>x.ald=sw.checked);render();}; /* 24/11/2026 : patient en ALD → toutes les lignes à 100 % (chacune reste modifiable) */\n"
  "  document.querySelectorAll(\"[data-rtt]\").forEach(b=>b.onclick=()=>{const t=(state.tt||[])[+b.dataset.rtt];const L=t?bdpmxSearch(String(t),3):[];if(L.length===1)rnwAdd(L[0],false);});\n"
  "  document.querySelectorAll(\"[data-rttq]\").forEach(b=>b.onclick=()=>{const t=(state.tt||[])[+b.dataset.rttq];if(!t)return;RNW.q=String(t);render();const q2=document.getElementById(\"rnw_q\");if(q2){q2.focus();if(q2.oninput)q2.oninput();}});"),
 ("mémo : statut",
  "Statut : fiche non relue (bloc 17, version 1).",
  "Statut : fiche non relue (bloc 17, version 2 du 24/11/2026 : panneau en tête de la fiche en mode complet, interrupteur « Patient en ALD » qui passe toutes les lignes à 100 %, traitement en cours du patient repris en un geste)."),
 ("blocs de la fiche : clé « rnw » (ordre par défaut, juste après le patient)",
  "const BLK_DEFAULT=[\"patient\",\"dict\",\"docs\",\"motif\",\"synth\",\"options\",\"alerts\",\"obs\",\"sheets\",\"lettres\"];",
  "const BLK_DEFAULT=[\"patient\",\"rnw\",\"dict\",\"docs\",\"motif\",\"synth\",\"options\",\"alerts\",\"obs\",\"sheets\",\"lettres\"]; /* 24/11/2026 : rnw = panneau de renouvellement, juste sous le patient */"),
 ("blocs : libellé",
  "const BLK_LABELS={patient:\"Patient\",dict:\"Dictée\",",
  "const BLK_LABELS={patient:\"Patient\",rnw:\"Renouvellement d'ordonnance (fiche Renouvellement)\",dict:\"Dictée\","),
 ("blocs : un ordre personnalisé enregistré sans « rnw » le place après le patient, pas en fin",
  "BLK_DEFAULT.forEach(k=>{if(!L.includes(k))L.push(k);});return L;}",
  "BLK_DEFAULT.forEach(k=>{if(!L.includes(k)){if(k===\"rnw\")L.splice(L.indexOf(\"patient\")+1,0,k);else L.push(k);}});return L;} /* 24/11/2026 : rnw inséré après le patient dans un ordre enregistré avant son existence */"),
 ("blocs : le panneau a sa propre clé (sinon il suit le bloc précédent et finit après la dictée sur téléphone)",
  "function blkKeyOf(e){if(!e||!e.matches)return \"\";if(e.id===\"dictcard\")return \"dict\";",
  "function blkKeyOf(e){if(!e||!e.matches)return \"\";if(e.id===\"rnw\")return \"rnw\";if(e.id===\"dictcard\")return \"dict\";"),
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
