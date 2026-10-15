// Tests de l'anonymisation locale v41 (aucun navigateur requis) : node tests/test_anon.js
// Le module est lu tel quel dans index.html, entre /*ANON-BEGIN et /*ANON-END*/.
const fs=require("fs"),path=require("path");
const html=fs.readFileSync(path.join(__dirname,"..","index.html"),"utf8");
const ia=html.indexOf("/*ANON-BEGIN"),ib=html.indexOf("/*ANON-END*/");
if(ia<0||ib<0){console.log("FAIL module ANON introuvable");process.exit(1);}
const A=new Function(html.slice(ia,ib)+";return {anonymize,anonLeaks,reidentify,aiDoseGuard,aiFactGuard,anonAge,anonRel,anonParseDDN,anonNorm,ANON_NOMS};")();
/* Lexique comme dans l'application : les mots des fiches (PACKS) */
const pa=html.search(/const PACKS\s*=/),pb=html.indexOf("const SYSTEMS");
const WORDS=html.slice(pa,pb).match(/[A-Za-zÀ-ÖØ-öø-ÿŒœ]{2,}/g)||[];
const LEX=new Set(WORDS.map(A.anonNorm)),COUR=new Set(WORDS.filter(w=>w===w.toLowerCase()).map(A.anonNorm));
// 10. Médicaments jamais masqués (base intégrée : premier mot de chaque spécialité + DCI, comme aiMedWords)
const bA=html.indexOf("const blob=`")+12,bB=html.indexOf("`;blob.split",bA);
const MED=new Set();const addW=w=>{const k=A.anonNorm(w).replace(/[.,;:]+$/,"");if(k.length>=3&&!/^\d/.test(k))MED.add(k);};
html.slice(bA,bB).split("\n").forEach(l=>{if(!l)return;const i=l.indexOf("=");const k=i<0?l:l.slice(0,i);addW(k.trim().split(/\s+/)[0]);if(i>=0)l.slice(i+1).split("|").forEach(d=>d.split(/[\s,()+\/]+/).forEach(addW));});
const REF="15/10/2026";
let ok=0,ko=0;const res=[];
function t(name,cond,info){res.push([name,!!cond]);if(cond){ok++;console.log("OK  ",name);}else{ko++;console.log("FAIL",name,info===undefined?"":JSON.stringify(info));}}
function run(text,ctx){ctx=Object.assign({ref:REF,lexique:LEX,courants:COUR},ctx);const r=A.anonymize(text,ctx);return Object.assign(r,{leaks:A.anonLeaks(r.text,ctx),back:A.reidentify(r.text,r.map)});}
const absent=(s,arr)=>arr.every(x=>!s.toLowerCase().includes(String(x).toLowerCase()));

// 1. Identité du patient
let r=run("Mme DUPONT Marie-Claire, 41 ans, vue pour fièvre. Marie-Claire dit que Dupont est son nom d'usage.",{patient:"DUPONT Marie-Claire",ddn:"12/03/1985"});
t("nom et prénom du patient retirés",absent(r.text,["dupont","marie-claire","marie","claire"]),r.text);
t("nom seul → [[NOM DU PATIENT]]",r.text.includes("[[NOM DU PATIENT]]"),r.text);
t("prénom seul → [[PRÉNOM DU PATIENT]]",r.text.includes("[[PRÉNOM DU PATIENT]]"),r.text);
t("réintégration exacte (aller-retour identique)",r.back.text==="Mme DUPONT Marie-Claire, 41 ans, vue pour fièvre. Marie-Claire dit que Dupont est son nom d'usage."&&!r.back.unresolved.length,r.back);
r=run("dupont marie appelle pour sa fille, pas de fièvre.",{patient:"DUPONT Marie"});
t("nom dicté en minuscules retiré",absent(r.text,["dupont","marie"])&&!r.leaks.length,r.text);
r=run("Patiente vue avec son mari. Antécédent de lupus. Liquide blanc à l'examen.",{patient:"BLANC Rose"});
t("nom qui est aussi un mot courant : le mot courant reste (« blanc »)",r.text.includes("Liquide blanc"),r.text);
r=run("Mme Blanc présente une éruption ; Rose ne tousse pas.",{patient:"BLANC Rose"});
t("…mais le nom propre avec majuscule est retiré",absent(r.text,["Blanc","Rose"])&&!r.leaks.length,r.text);
r=run("Vu avec Jean-Pierre, son fils Kevin et l'infirmière Mme Roux.",{patient:"MARTIN Jean-Pierre"});
t("prénom composé retiré",absent(r.text,["jean-pierre","jean","pierre"]),r.text);
t("proches nommés retirés (fils, infirmière)",absent(r.text,["kevin","roux"]),r.text);

// 2. Date de naissance → âge
r=run("Née le 12/03/1985, enceinte de 20 SA.",{patient:"X Y",ddn:"12/03/1985"});
t("date de naissance → [[ÂGE : 41 ans]]",r.text.includes("[[ÂGE : 41 ans]]")&&!r.text.includes("1985"),r.text);
r=run("ddn 12031985",{patient:"X Y",ddn:"12031985"});
t("date de naissance compacte (12031985) retirée",!r.text.includes("12031985")&&!r.leaks.length,r.text);
r=run("Né le 1er mars 1930.",{patient:"X Y",ddn:"01/03/1930"});
t("date de naissance en toutes lettres → âge, 90 ans ou plus regroupés",r.text.includes("[[ÂGE : 90 ans ou plus]]")&&!/1930|mars/.test(r.text),r.text);
r=run("Patient né en 1985.",{patient:"X Y",ddn:"02/05/1985"});
t("année de naissance seule → âge",!r.text.includes("1985")&&r.back.text==="Patient né en 1985.",r);
t("âge nourrisson en mois",A.anonAge(A.anonParseDDN("01/02/2025"),A.anonParseDDN(REF))==="20 mois");
t("âge nouveau-né en jours",A.anonAge(A.anonParseDDN("10/10/2026"),A.anonParseDDN(REF))==="5 jours");

// 3. Dates exactes → relatives
r=run("Fièvre depuis le 10/10/2026, vu par un confrère le 3 octobre, contrôle le 20/10/2026, ECG du 2026-10-14.",{patient:"X Y"});
t("dates exactes → J-5, J-12, J+5, J-1",["[[J-5]]","[[J-12]]","[[J+5]]","[[J-1]]"].every(x=>r.text.includes(x))&&!/2026|octobre/.test(r.text),r.text);
r=run("Hospitalisé en mars 2024 puis revu le 14/10.",{patient:"X Y"});
t("mois + année et jour/mois → relatifs",!/2024|mars|14\/10/.test(r.text)&&r.text.includes("[[J-1]]"),r.text);
r=run("TA 13/8, puis 14/9. Sat 95 %.",{patient:"X Y"});
t("une tension (13/8) n'est pas prise pour une date",r.text.includes("TA 13/8, puis 14/9"),r.text);
t("relatif au-delà d'un mois : en mois",A.anonRel(A.anonParseDDN("15/05/2026"),A.anonParseDDN(REF))==="il y a 5 mois");

// 4. Adresse, téléphone, NIR, courriel, codes
r=run("Domicile : 12 rue des Lilas, 45000 Orléans, bâtiment B, digicode 4512B. Tél 06 12 34 56 78 ou +33 2 38 11 22 33. NIR 1 85 03 45 234 567 89. Mail jp.martin@orange.fr",{patient:"MARTIN Jean",adresse:["12 rue des Lilas, 45000 Orléans"],tel:["06 12 34 56 78"],nir:"1 85 03 45 234 567 89"});
t("adresse retirée (voie, code postal), ville gardée en clair",absent(r.text,["lilas","45000"])&&r.text.includes("[[CODE POSTAL]] Orléans"),r.text);
t("digicode retiré",!r.text.includes("4512B"),r.text);
t("téléphones (06… et +33…) retirés",!/06 12|38 11/.test(r.text),r.text);
t("NIR retiré",!/234 567/.test(r.text)&&r.text.includes("[[NIR]]"),r.text);
t("courriel retiré",!r.text.includes("@"),r.text);
t("aucune fuite détectée après anonymisation",!r.leaks.length,r.leaks);
t("réintégration exacte de l'adresse et des numéros",r.back.text.includes("12 rue des Lilas, 45000 Orléans")&&r.back.text.includes("06 12 34 56 78")&&r.back.text.includes("1 85 03 45 234 567 89"),r.back.text);
r=run("adresse 22 avenue de la libération 45140 saint-jean-de-la-ruelle. tel connu.",{patient:"X Y"});
t("adresse en minuscules masquée en bloc, ville comprise (décision du 15/10/2026)",absent(r.text,["libération","45140","ruelle","saint-jean"])&&r.text.includes("[[ADRESSE]]"),r.text);
r=run("Habite 3 bis avenue de la Libération à Saran.",{patient:"X Y"});
t("adresse dictée inconnue de Packs retirée",absent(r.text,["libération","saran"]),r.text);
r=run("Numéro de dossier 123456789012.",{patient:"X Y"});
t("numéro long (dossier, RPPS) retiré",!r.text.includes("123456789"),r.text);

// 5. Noms propres
r=run("Vu par le Dr Lemoine la semaine dernière. Avis de M. Bernard. Sa voisine Josiane a appelé. Puis Kevin est arrivé.",{patient:"X Y"});
t("médecin, civilité, voisine et prénom isolé retirés",absent(r.text,["lemoine","bernard","josiane","kevin"]),r.text);
r=run("Signe de Murphy positif, Lasègue négatif, score de Glasgow à 15. Traité par DOLIPRANE et SPASFON. Avis SAMU, transfert au CHU.",{patient:"X Y"});
t("éponymes, médicaments et sigles conservés",["Murphy","Lasègue","Glasgow","DOLIPRANE","SPASFON","SAMU","CHU"].every(x=>r.text.includes(x)),r.text);
r=run("Appel de Mickaël DEIE au patient.",{patient:"X Y",autres:[{n:"Mickaël DEIE",cat:"MÉDECIN"}]});
t("nom du médecin → [[MÉDECIN]]",r.text.includes("[[MÉDECIN]]")&&!/deie/i.test(r.text),r.text);
r=run("Le frère, Paul Durand, et le patient.",{patient:"X Y",autres:[{n:"DURAND Paul",cat:"AUTRE PATIENT"}]});
t("autre patient vu ensemble → [[AUTRE PATIENT]]",r.text.includes("[[AUTRE PATIENT]]")&&!/durand|paul/i.test(r.text),r.text);
r=run("Julie, 4 ans, fièvre.",{patient:"X Y",masquer:[]});
t("prénom inconnu en début de phrase retiré",!r.text.includes("Julie"),r.text);
r=run("Toux sèche chez Murphy.",{patient:"X Y",masquer:["sèche"]});
t("masquage manuel d'un mot (écran « Ce qui part »)",!r.text.includes("sèche")&&r.back.text==="Toux sèche chez Murphy.",r.text);
r=run("Arrivée de Gaspard.",{patient:"X Y",garder:["Gaspard"]});
t("mot rendu à la main (garder) conservé",r.text.includes("Gaspard"),r.text);

r=run("Neutropénie possible. Hospitalisée en mars. Dyspnée d'effort. Maman présente.",{patient:"X Y"});
t("début de phrase : mots médicaux et courants non masqués",["Neutropénie","Hospitalisée","Dyspnée","Maman"].every(x=>r.text.includes(x)),r.text);
r=run("Gaspard a de la fièvre. Agnès a appelé. Émilie et Dominique sont là. Florence rappellera.",{patient:"X Y"});
t("début de phrase : prénoms masqués, même à terminaison de mot courant",absent(r.text,["gaspard","agnès","émilie","dominique","florence"]),r.text);
r=run("Papa M. Lambert Thomas joignable.",{patient:"LAMBERT Chloé"});
t("civilité abrégée après un lien (Papa M.) : pas de jeton parasite",r.text.includes("M. ")&&!/\[\[PERSONNE \d\]\]\./.test(r.text)&&!/thomas|lambert/i.test(r.text),r.text);

// 5 bis. Consigne du 15/10/2026 : hôpital et ville en clair, tous les autres lieux précis masqués
r=run("Transfert CHR d'Orléans. Suivi à l'Institut Gustave Roussy, accouchement à la maternité Oréliance, opéré à la clinique de l'Archette, connu du CHD Daumezon, scanner au CHU de Tours.",{patient:"X Y"});
t("noms d'hôpitaux gardés en clair",["CHR d'Orléans","Institut Gustave Roussy","maternité Oréliance","clinique de l'Archette","CHD Daumezon","CHU de Tours"].every(x=>r.text.includes(x)),r.text);
r=run("Vit à Saint-Jean-de-Braye, travaille à Olivet, hospitalisé à Paris, pompiers de Fleury-les-Aubrais, famille à La Ferté-Saint-Aubin.",{patient:"X Y"});
t("villes gardées en clair",["Saint-Jean-de-Braye","Olivet","Paris","Fleury-les-Aubrais","La Ferté-Saint-Aubin"].every(x=>r.text.includes(x)),r.text);
r=run("Vit à l'EHPAD les Jardins de Saran. Chute au stade de la Source. Fils à l'école Jean Zay, fille à la crèche les Petits Loups. Coupure à la boulangerie Paul, repas au restaurant Le Lutin Gourmand, magasinier chez Leroy Merlin, ordonnance à la pharmacie du Martroi, prise de sang au labo Bioallians. Habite à la Source, quartier Saint-Marceau.",{patient:"X Y",medicaments:MED});
t("lieux précis masqués même s'ils ressemblent à des mots courants",absent(r.text,["jardins","source","zay","loups","paul","lutin","gourmand","leroy","merlin","martroi","bioallians","marceau"]),r.text);
t("type de lieu gardé lisible (EHPAD, stade, école, boulangerie…)",["EHPAD [[LIEU","stade [[LIEU","école [[LIEU","boulangerie [[LIEU","chez [[LIEU","pharmacie [[LIEU"].every(x=>r.text.includes(x)),r.text);
t("lieux réintégrés à l'identique",r.back.text.startsWith("Vit à l'EHPAD les Jardins de Saran. Chute au stade de la Source.")&&r.back.text.endsWith("Habite à la Source, quartier Saint-Marceau."),r.back.text);
r=run("Visite lieu-dit la Mothe à Saint-Cyr-en-Val.",{patient:"X Y",adresse:["lieu-dit la Mothe, 45590 Saint-Cyr-en-Val"]});
t("adresse connue : lieu-dit masqué, ville en clair, pas de fausse fuite",!/mothe/i.test(r.text)&&r.text.includes("Saint-Cyr-en-Val")&&!r.leaks.length,[r.text,r.leaks]);
// Intervalles de dates
r=run("Hospitalisée du 2 au 9 septembre 2026, puis entre le 3 et le 5/10, et du 2 au 4 octobre.",{patient:"X Y"});
t("intervalle « du 2 au 9 septembre 2026 » → du J-43 au J-36",r.text.includes("du [[J-43]] au [[J-36]]"),r.text);
t("intervalle « entre le 3 et le 5/10 » → J-12 et J-10",r.text.includes("entre le [[J-12]] et le [[J-10]]"),r.text);
t("même numéro de jour dans deux intervalles : jetons distincts",r.text.includes("du [[J-13]] au [[J-11]]")&&!r.leaks.length,r.text);
t("intervalles réintégrés à l'identique",r.back.text==="Hospitalisée du 2 au 9 septembre 2026, puis entre le 3 et le 5/10, et du 2 au 4 octobre."&&!r.back.unresolved.length,r.back);
t("intervalle resté en clair détecté comme fuite",A.anonLeaks("hospitalisé du 2 au 9 septembre",{patient:"X Y"}).some(l=>l.cat==="intervalle de dates"));

// 6. Contrôle de fuite
t("fuite de nom détectée",A.anonLeaks("Patient Dupont vu ce jour",{patient:"DUPONT Marie",lexique:LEX}).some(l=>l.cat==="nom"));
t("fuite de date de naissance détectée",A.anonLeaks("né le 12/03/1985",{patient:"X Y",ddn:"12/03/1985"}).some(l=>l.cat==="naissance"));
t("fuite de téléphone détectée",A.anonLeaks("rappeler au 06.12.34.56.78",{patient:"X Y",tel:"0612345678"}).some(l=>l.cat==="téléphone"));
t("fuite de NIR détectée",A.anonLeaks("NIR 185034523456789",{patient:"X Y",nir:"1 85 03 45 234 567 89"}).some(l=>l.cat==="NIR"));
t("toute date complète restante bloque l'envoi",A.anonLeaks("vu le 03/10/2026",{patient:"X Y"}).some(l=>l.cat==="date exacte"));
t("pas de faux positif sur un texte propre",!A.anonLeaks("[[PATIENT]], [[ÂGE : 41 ans]], TA 13/8, SpO2 95 %.",{patient:"DUPONT Marie",ddn:"12/03/1985",tel:"0612345678",lexique:LEX}).length);

// 7. Réintégration
let b=A.reidentify("Je vous adresse [[PATIENT]] ([[ âge : 41 ans ]]).",{"PATIENT":"DUPONT Marie","ÂGE : 41 ans":"12/03/1985"});
t("réintégration tolérante à la casse et aux espaces",b.text==="Je vous adresse DUPONT Marie (12/03/1985)."&&!b.unresolved.length,b);
b=A.reidentify("Vu avec [[PERSONNE 9]].",{"PATIENT":"X"});
t("jeton inventé signalé, jamais remplacé au hasard",b.unresolved.length===1&&b.text.includes("[[PERSONNE 9]]"),b);

// 8. Posologies : jamais de l'IA
let d=A.aiDoseGuard("Patient informé. Poursuivre AUGMENTIN 1 g matin et soir pendant 7 jours. Revoir si fièvre.");
t("posologie retirée d'une réponse de l'IA",!/1 g|7 jours/.test(d.text)&&d.text.includes("Revoir si fièvre")&&d.found.length>=1,d);
d=A.aiDoseGuard("Paracétamol 15 mg/kg toutes les 6 h. Consignes données.");
t("dose au poids et fréquence repérées",!/mg\/kg|6 h/.test(d.text)&&d.text==="Consignes données.",d);
d=A.aiDoseGuard("Douleur à 6/10, fièvre à 38,5 °C depuis 2 jours.");
t("pas de faux positif sur constantes et durée d'évolution",d.text.includes("38,5")&&!d.found.length,d);

// 9. Un fait ne se crée pas
t("nombre ajouté par l'IA détecté",!A.aiFactGuard("TA 13/8, FC 92","TA 13/8, FC 92, SpO2 97 %").ok);
t("nombre retiré d'une reformulation détecté",!A.aiFactGuard("douleur à 7/10 depuis 3 h","douleur intense",true).ok);
t("sigles chiffrés (SpO2, HbA1c) ne comptent pas comme nombres",A.aiFactGuard("SpO2 95 %","SpO2 95 %, HbA1c dans la norme").ok);
t("reformulation fidèle acceptée",A.aiFactGuard("patient très agité, TA 13/8","patient agité, TA 13/8",true).ok);

t("base intégrée chargée (plus de 3 000 noms)",MED.size>3000,MED.size);
/* Médicaments absents des fiches actuelles (vérifié) + médicaments courants des fiches */
const DICT="Sous Januvia, Aricept et Ebixa. Modopar arrêté, Lyrica le soir, Tercian si agitation. Ezetrol et Inegy. Aussi Eliquis, Kardégic, Levothyrox et Tahor.";
const DRUGS=["Januvia","Aricept","Ebixa","Modopar","Lyrica","Tercian","Ezetrol","Inegy","Eliquis","Kardégic","Levothyrox","Tahor"];
const ABSENTS=["Januvia","Aricept","Ebixa","Modopar","Lyrica","Tercian","Ezetrol","Inegy"];
r=run(DICT,{patient:"MARTIN Paul"});
t("sans la base, les médicaments absents des fiches étaient masqués (constat v41)",ABSENTS.every(x=>!r.text.includes(x)),r.text);
r=run(DICT,{patient:"MARTIN Paul",medicaments:MED});
t("avec la base, aucun médicament n'est masqué",DRUGS.every(x=>r.text.includes(x)),DRUGS.filter(x=>!r.text.includes(x)));
r=run("ELIQUIS 5 mg matin et soir, KARDEGIC 75.",{patient:"MARTIN Paul",medicaments:MED});
t("médicaments en capitales conservés",r.text.includes("ELIQUIS")&&r.text.includes("KARDEGIC"),r.text);
r=run("Mme Rose, sous Eliquis.",{patient:"X Y",medicaments:new Set([...MED,"rose"])});
t("un prénom fréquent reste masqué même s'il est aussi un nom de médicament",!r.text.includes("Rose")&&r.text.includes("Eliquis"),r.text);
r=run("tahor et eliquis pour tahor yves, suivi par Tahor.",{patient:"TAHOR Yves",medicaments:MED});
t("patient homonyme d'un médicament : son nom reste masqué partout",!/tahor/i.test(r.text)&&!r.leaks.length,r.text);
r=run("Vu par le Dr Biogaran pour son traitement.",{patient:"X Y",medicaments:MED});
t("un nom après une civilité reste masqué même s'il ressemble à un laboratoire",!r.text.includes("Biogaran"),r.text);
r=run("Sa fille Fabre et Pierre sont présents.",{patient:"X Y",medicaments:MED});
t("noms de laboratoire (second mot d'une spécialité) non ajoutés au lexique",!r.text.includes("Pierre")&&!r.text.includes("Fabre"),r.text);

console.log(`\n${ok}/${ok+ko} tests d'anonymisation OK`);
fs.writeFileSync(path.join(__dirname,"resultats_anon.md"),"# Tests v41 — anonymisation locale (node tests/test_anon.js)\n\n"+res.map(([n,c])=>`- ${c?"OK":"ÉCHEC"} — ${n}`).join("\n")+`\n\n${ok}/${ok+ko} tests OK\n`);
process.exit(ko?1:0);
