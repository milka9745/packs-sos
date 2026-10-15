# 20 dictées fictives de garde passées dans l'application (aiPrepare) : texte exact qui partirait, sans aucun envoi.
# Toutes les identités, adresses et numéros sont inventés. Lancer : python tests/test_dictees.py
# Sortie : tests/dictees_ia.html (rapport lisible) et tests/resultats_dictees.md
import asyncio, os, json, subprocess, time, sys, html, re
from playwright.async_api import async_playwright

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF="15/10/2026"

# p : patient, ddn, adr/tel : adresse et téléphone connus de Packs (tournée), copat : autre patient vu ensemble
# interdit : fragments qui ne doivent jamais partir (insensible à la casse) ; garder : mots qui doivent partir tels quels
D=[
 dict(t="Cystite, dictée en minuscules",p="DUPONT Marie",ddn="12/03/1985",adr="8 rue Bannier, 45000 Orléans",tel="06 12 34 56 78",
  d="Visite 8 rue Bannier 3e étage. mme dupont marie 41 ans brûlures mictionnelles depuis le 13/10 pollakiurie pas de fièvre pas de douleur lombaire. allergie amoxicilline. traitement habituel Levothyrox 75. BU leucocytes plus nitrites plus. rappeler le mari au 06 12 34 56 78 si besoin. Cystite simple, Monuril.",
  interdit=["dupont","marie","bannier","06 12","13/10","45000"],garder=["Levothyrox","Monuril"]),
 dict(t="Chute en EHPAD sous anticoagulant",p="MARTIN Jean-Pierre",ddn="02/02/1941",adr="EHPAD Les Jardins de Saran, 12 allée des Tilleuls, 45770 Saran",tel="02 38 72 11 22",
  d="EHPAD les Jardins de Saran chambre 214. Monsieur Martin Jean-Pierre né le 2 février 1941, chute ce matin vers 6 h retrouvé au sol par l'aide-soignante Mme Roux. Sous Eliquis 5 mg matin et soir et Kardégic 75. Pas de PC rapportée, Glasgow 15, plaie du cuir chevelu 3 cm. Infirmière de nuit joignable au 02 38 72 11 22. Avis du Dr Moreau médecin coordonnateur. Transfert CHR Orléans pour scanner sous anticoagulant.",
  interdit=["martin","jean-pierre","1941","saran","tilleuls","roux","moreau","02 38"],garder=["Eliquis","Kardégic","Glasgow","CHR"]),
 dict(t="Lombalgie, employeur et commune",p="LE GALL Jean-Baptiste",ddn="17/07/1979",
  d="jean-baptiste le gall 47 ans lombalgie aiguë depuis hier en soulevant un carton au travail, magasinier chez Leroy Merlin à Olivet. Lasègue négatif, pas de déficit, pas de trouble sphinctérien. A pris Doliprane et Ibuprofène sans effet. Arrêt de travail 5 jours. Bi-Profénid, Acupan, Thiocolchicoside en option.",
  interdit=["gall","jean-baptiste","leroy","merlin","olivet","1979"],garder=["Lasègue","Doliprane","Bi-Profénid","Acupan"]),
 dict(t="Otite de l'enfant, maman et crèche",p="PETIT Léo",ddn="03/05/2023",
  d="Léo 3 ans 14 kilos amené par sa maman Mme Petit Sandrine pour fièvre à 39,5 depuis le 13 octobre, otalgie droite. Tympan droit bombé. Pas de vomissement. Va à la crèche les Petits Loups à Fleury-les-Aubrais. Clamoxyl et Doliprane pédiatrique. Maman joignable au 07 81 45 22 10.",
  interdit=["léo","sandrine","2023","13 octobre","loups","fleury","07 81"],garder=["Clamoxyl","Doliprane"]),
 dict(t="Agitation, psychiatrie et tiers",p="BERNARD Lucas",ddn="21/11/2001",
  d="Appel régulation pour agitation. Patient amené par les pompiers de Fleury, connu du CHD Daumezon, schizophrénie, traitement Tercian et Abilify, arrêt du traitement depuis 3 semaines selon sa mère Mme Bernard joignable au 06.98.76.54.32. Propos délirants, pas d'idée suicidaire exprimée. Avis psychiatre de garde Dr Lefèvre à 23 h 40. Certificat SDTU rédigé, tiers la mère.",
  interdit=["bernard","lucas","2001","daumezon","06.98","lefèvre","fleury"],garder=["Tercian","Abilify"]),
 dict(t="Couple vu ensemble, restaurant",p="GARCIA Ana",ddn="08/08/1990",copat="GARCIA Luis",
  d="Couple vu ensemble, Ana et Luis Garcia, gastro depuis samedi après repas au restaurant Le Lutin Gourmand rue de Bourgogne. Vomissements, diarrhée sans sang. Luis sous Metformine et Januvia, à suspendre. Pas de signe de déshydratation.",
  interdit=["garcia","ana ","luis","lutin","gourmand","bourgogne","1990"],garder=["Metformine","Januvia"]),
 dict(t="Courriel et numéro de sécurité sociale",p="NGUYEN Thi Lan",ddn="30/01/1968",
  d="Mme Nguyen demande un certificat, envoie les résultats par mail à lan.nguyen68@gmail.com. Numéro de sécu 2 68 01 99 350 123 45. Douleur thoracique atypique depuis dimanche, ECG normal. Sous Seresta 10 et Lysanxia.",
  interdit=["nguyen","thi ","lan.","gmail","350 123","1968"],garder=["Seresta","Lysanxia","ECG"]),
 dict(t="Soins palliatifs en HAD, lieu-dit",p="MOREL Germaine",ddn="14/04/1932",adr="lieu-dit la Mothe, 45590 Saint-Cyr-en-Val",tel="02 38 76 54 32",
  d="Visite lieu-dit la Mothe à Saint-Cyr-en-Val, patiente en HAD pour cancer du pancréas, infirmière Sandrine de l'HAD présente. Douleurs non contrôlées malgré Skenan 30 et Actiskenan 10. Fille Mme Morel Christine au 06 22 11 00 99 d'accord avec le confort. Majoration Skenan, Oramorph si troubles de déglutition, Scopoderm.",
  interdit=["morel","germaine","mothe","saint-cyr","sandrine","christine","06 22","1932"],garder=["Skenan","Actiskenan","Oramorph","Scopoderm","HAD"]),
 dict(t="Nom de famille qui est un mot courant",p="ROSE Odette",ddn="05/09/1950",
  d="Éruption rose pâle du tronc depuis 48 h après introduction d'Augmentin le 10/10/2026 par son médecin traitant le Dr Fournier. Mme Rose ne présente pas de signe de gravité, pas d'atteinte muqueuse. Arrêt Augmentin, Aerius. Rose dit avoir déjà fait une réaction à la Pyostacine.",
  interdit=["odette","mme rose","rose dit","fournier","10/10/2026","1950"],garder=["rose pâle","Augmentin","Aerius","Pyostacine"]),
 dict(t="Entorse, téléphone +33, cabinet de kiné",p="DUBOIS Kevin",ddn="11/12/1996",
  d="Entorse cheville gauche au foot ce soir au stade de la Source. Ottawa négatif. Joignable au +33 6 45 12 78 90. Kiné au cabinet Rivière Kiné. Bi-Profénid, attelle Aircast, béquilles.",
  interdit=["dubois","kevin","1996","45 12 78","rivière"],garder=["Ottawa","Bi-Profénid"]),
 dict(t="Hypoglycémie, épouse et diabétologue",p="FONTAINE Marcel",ddn="19/06/1955",
  d="Hypoglycémie à 0,45 g/l retrouvée par son épouse Josiane, sous Novorapid, Lantus et Diamicron. Resucrage, Glucagen fait par les pompiers. Glycémie de contrôle 1,20. Repas pris. Revoir son diabétologue le Dr Henry au CHR.",
  interdit=["fontaine","marcel","josiane","henry","1955"],garder=["Novorapid","Lantus","Diamicron","Glucagen"]),
 dict(t="Épistaxis sous AVK, laboratoire et commune",p="ROUSSEAU Pierre",ddn="01/01/1948",
  d="Épistaxis abondante sous Previscan, INR à 4,2 fait au labo Bioallians rue de la République ce matin. Méchage. Contrôle INR le 17/10. Médecin traitant Dr Blanc à Saint-Jean-de-Braye prévenu.",
  interdit=["rousseau","pierre","1948","république","dr blanc","saint-jean","17/10"],garder=["Previscan","INR"]),
 dict(t="Asthme de l'enfant, école et papa",p="LAMBERT Chloé",ddn="22/02/2016",
  d="Crise d'asthme, Chloé 10 ans 32 kg, sibilants diffus, SpO2 93 %, Ventoline 10 bouffées en chambre d'inhalation, Célestène. École Jean Zay. Papa M. Lambert Thomas joignable 0612457890.",
  interdit=["lambert","chloé","thomas","2016","0612457890","zay"],garder=["Ventoline","Célestène","SpO2"]),
 dict(t="Beaucoup de dates",p="SIMON Gisèle",ddn="07/03/1939",
  d="Hospitalisée du 2 au 9 septembre 2026 au CHR pour pneumopathie, sortie sous Augmentin jusqu'au 16/09. Depuis le 12 octobre reprise de toux fébrile. Vaccin grippe fait le 1er octobre. Kiné respiratoire avec M. Vincent.",
  interdit=["simon","gisèle","1939","septembre 2026","16/09","12 octobre","1er octobre","vincent"],garder=["Augmentin","CHR"]),
 dict(t="Plaie de la main, enseigne et patron",p="MERCIER Lucas",ddn="13/05/2011",
  d="Plaie de la main droite avec un couteau à la boulangerie Paul place du Martroi, son patron M. Garnier présent. Vaccin antitétanique à jour selon le carnet. Orientation urgences pédiatriques CHR pour suture, samedi soir.",
  interdit=["mercier","lucas","2011","martroi","garnier"],garder=["CHR"]),
 dict(t="Tout en minuscules (clavier iPhone)",p="FAURE Nadia",ddn="25/12/1975",
  d="faure nadia 50 ans migraine habituelle depuis ce matin sans signe neuro, sous zomig habituellement inefficace, propranolol en fond. adresse 22 avenue de la libération 45140 saint-jean-de-la-ruelle. tel 0698123456.",
  interdit=["faure","nadia","1975","libération","45140","ruelle","0698123456"],garder=["zomig","propranolol"]),
 dict(t="Oncologie, professeur et institut",p="CHEVALIER Bernard",ddn="09/09/1960",
  d="Fièvre sous chimiothérapie, suivi par le Pr Durand à l'Institut Gustave Roussy, dernière cure le 6/10. Sous Xeloda. Neutropénie possible, appel du 15, Dr Girard régulateur, transfert SAU.",
  interdit=["chevalier","bernard","1960","durand","gustave","roussy","6/10","girard"],garder=["Xeloda","SAU"]),
 dict(t="Grossesse, sage-femme et maternité",p="ROY Sarah",ddn="14/02/1996",
  d="Grossesse 24 SA, suivie par la sage-femme Mme Leclerc à la maternité Oréliance, DPA le 28/01/2027. Cystite gravidique. Pas de contraction. Pas d'Oroken, préférer Monuril. Spasfon.",
  interdit=["roy","sarah","1996","leclerc","oréliance","28/01/2027"],garder=["Monuril","Spasfon","Oroken"]),
 dict(t="Numéros pièges (dossier, RPPS, horaires)",p="ROBIN Alain",ddn="03/03/1972",
  d="Dossier 2026-001234. Douleur thoracique, ECG sus-décalage, appel 15 à 2 h 10, SMUR sur place à 2 h 30. Plavix et Kardégic par le SMUR. RPPS du régulateur 10101234567.",
  interdit=["robin","alain","1972","10101234567","001234"],garder=["Plavix","Kardégic","SMUR","ECG"]),
 dict(t="Touriste étranger, hôtel et téléphone étranger",p="MULLER Hans",ddn="12/12/1958",adr="Hôtel Mercure, 44 quai Barentin, 45000 Orléans",tel="+49 171 2345678",
  d="Touriste allemand hébergé à l'hôtel Mercure quai Barentin, chambre 312. Gastro depuis le 13. Son épouse Greta parle anglais. Numéro allemand +49 171 2345678. Smecta, Tiorfan.",
  interdit=["muller","hans","greta","mercure","barentin","2345678","1958"],garder=["Smecta","Tiorfan"]),
]

async def unlock(page):
    await page.goto("http://localhost:8767/index.html")
    await page.wait_for_selector("#uid",timeout=15000)
    await page.fill("#uid","testv41"); await page.fill("#pin1","1234"); await page.fill("#pin2","1234")
    await page.click("#pin_ok")
    await page.wait_for_selector("#rec_ack",timeout=15000)
    await page.check("#rec_ack"); await page.click("#rec_done")
    try:
        await page.wait_for_selector("#id_demo",timeout=8000); await page.click("#id_demo")
    except Exception: pass
    await page.wait_for_selector("#lock",state="detached",timeout=15000)
    await page.wait_for_timeout(800)

def hl(t):
    t=html.escape(t)
    return re.sub(r"\[\[([^\]]*)\]\]",lambda m:'<mark>[['+m.group(1)+']]</mark>',t)

async def main():
    srv=subprocess.Popen([sys.executable,"-m","http.server","8767"],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1); out=[]; sent=[]
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":1280,"height":900}); page=await ctx.new_page()
            errors=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("dialog",lambda d:asyncio.ensure_future(d.accept()))
            await ctx.route("https://api.anthropic.com/**",lambda r:(sent.append(1),r.abort()))
            await unlock(page)
            await page.evaluate("AI.key='sk-ant-test-factice';AI.cfg.mode='partiel';aiSave();")
            for i,x in enumerate(D):
                r=await page.evaluate("""(x)=>{const stop={id:'t'+x.i,addr:x.adr||'',tel:x.tel||'',nom:x.p,ts:Date.now()};TOUR.stops=[stop];TOUR.current=x.adr||x.tel?stop.id:'';
                  Object.assign(state,{patient:x.p,ddn:x.ddn,date:x.ref,sexe:'',poids:'',tt:[],cst:{},allergies:[],allergie:false,grossesse:false,allait:false,copat:x.copat?[{patient:x.copat}]:[],t0:Date.now()+x.i,sel:null});
                  AI.masquer=[];AI.garder=[];const P=aiPrepare('obs',{dictee:x.d});const el=document.getElementById('aisend');if(el)el.remove();
                  return {user:P.user,items:P.items,leaks:P.leaks};}""",dict(x,i=i,ref=REF))
                low=r["user"].lower()
                fuite=[f for f in x["interdit"] if f.lower() in low]
                perdu=[g for g in x["garder"] if g not in r["user"]]
                trop=[it["orig"] for it in r["items"] if it["cat"]=="NOM PROPRE" and not any(f.strip().lower() in it["orig"].lower() for f in x["interdit"])]
                out.append(dict(x,n=i+1,**r,fuite=fuite,perdu=perdu,trop=trop))
            ok_js=len(errors)==0
            await b.close()
    finally:
        srv.terminate()
    ok=[o for o in out if not o["fuite"] and not o["leaks"] and not o["perdu"]]
    # rapport
    cards=[]
    for o in out:
        st="ok" if o in ok else "ko"
        dict_part=o["user"].split("DICTÉE DU MÉDECIN\n",1)
        cards.append(f'''<section class="c {st}"><h2>{o["n"]}. {html.escape(o["t"])} <span class="b {st}">{"Rien d'identifiant" if st=="ok" else "À revoir"}</span></h2>
<p class="m">Patient fictif : <b>{html.escape(o["p"])}</b>, né(e) le {o["ddn"]}{(" · adresse connue : "+html.escape(o.get("adr",""))) if o.get("adr") else ""}{(" · tél. connu : "+html.escape(o.get("tel",""))) if o.get("tel") else ""}{(" · vu avec "+html.escape(o["copat"])) if o.get("copat") else ""}</p>
<h3>Dictée</h3><p class="d">{html.escape(o["d"])}</p>
<h3>Texte exact qui partirait</h3><pre>{hl(o["user"])}</pre>
<p class="m"><b>Retiré ({len(o["items"])})</b> : {" · ".join(html.escape(i["orig"])+" → [["+html.escape(i["tok"])+"]]" for i in o["items"])}</p>
{f'<p class="w">Fuite : {html.escape(", ".join(o["fuite"]+[l["frag"] for l in o["leaks"]]))}</p>' if o["fuite"] or o["leaks"] else ""}
{f'<p class="w">Médicament ou terme perdu : {html.escape(", ".join(o["perdu"]))}</p>' if o["perdu"] else ""}
{f'<p class="t">Masqué peut-être en trop (sans risque, réintégré au retour ; touchez-le à l’écran pour le rendre) : {html.escape(", ".join(o["trop"]))}</p>' if o["trop"] else ""}
</section>''')
    page_html=f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dictées fictives IA</title>
<style>:root{{--bg:#F6F4EE;--fg:#1B2238;--mu:#5B6278;--card:#fff;--line:#DDD8CC;--tok:#E3ECFF;--tokf:#1E2A5C;--ok:#1D7A3A;--ko:#B3261E;--warn:#8A6A12}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1B1E24;--fg:#E8EAF0;--mu:#A0A6B5;--card:#23272F;--line:#353A45;--tok:#2E3A5E;--tokf:#E8ECF8;--ok:#5BC07A;--ko:#FF8A80;--warn:#E5C46B}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif}}main{{max-width:860px;margin:0 auto;padding:16px}}
h1{{font-size:22px;margin:8px 0}}.c{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:14px 0}}.c.ko{{border-color:var(--ko)}}
h2{{font-size:17px;margin:0 0 6px}}h3{{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mu);margin:10px 0 4px}}
.b{{font-size:12px;border-radius:999px;padding:2px 8px;margin-left:6px;white-space:nowrap}}.b.ok{{color:var(--ok);border:1px solid var(--ok)}}.b.ko{{color:var(--ko);border:1px solid var(--ko)}}
.m{{color:var(--mu);font-size:13.5px}}.d{{margin:0}}pre{{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px;font:13.5px/1.5 ui-monospace,Menlo,monospace;margin:0}}
mark{{background:var(--tok);color:var(--tokf);border-radius:3px;padding:0 2px}}.w{{color:var(--ko);font-weight:600}}.t{{color:var(--warn);font-size:13.5px}}</style></head>
<body><main><h1>Ce qui partirait à l'IA — 20 dictées fictives</h1>
<p class="m">Généré par <code>tests/test_dictees.py</code> dans l'application v41 (fonction réelle <code>aiPrepare</code>), consultation du {REF}. Aucun envoi : l'API est bloquée pendant le test ({len(sent)} requête). Identités, adresses et numéros inventés.</p>
<p><b>{len(ok)}/{len(out)}</b> dictées sans fragment d'identité et sans médicament perdu.</p>
<p class="m"><b>Relecture (15/10/2026)</b> : « stade de la Source » (n° 10) et « CHR Orléans » (n° 2) partent en clair, mots courants ou ville du centre, non identifiants seuls ; dans « du 2 au 9 septembre 2026 » (n° 14), le premier jour reste un chiffre seul ; une enseigne ou un laboratoire peut être masqué en trop (Paul, Bioallians), sans risque, réintégré au retour.</p>
{"".join(cards)}</main></body></html>'''
    open(os.path.join(ROOT,"tests","dictees_ia.html"),"w",encoding="utf-8").write(page_html)
    lines=[f"- {'OK' if o in ok else 'ÉCHEC'} — {o['n']}. {o['t']}"+("" if o in ok else f" — fuite {o['fuite']+[l['frag'] for l in o['leaks']]} perdu {o['perdu']}") for o in out]
    lines.append(f"- {'OK' if not sent else 'ÉCHEC'} — aucune requête envoyée pendant le test")
    lines.append(f"- {'OK' if ok_js else 'ÉCHEC'} — aucune erreur JS")
    n=sum(1 for l in lines if l.startswith("- OK"))
    open(os.path.join(ROOT,"tests","resultats_dictees.md"),"w",encoding="utf-8").write("# Tests v41 — 20 dictées fictives\n\n"+"\n".join(lines)+f"\n\n{n}/{len(lines)} tests OK\n")
    print("\n".join(lines)); print(f"\n{n}/{len(lines)} tests OK")
    for o in out:
        if o["trop"]: print("  en trop",o["n"],o["trop"])
    sys.exit(0 if n==len(lines) else 1)
asyncio.run(main())
