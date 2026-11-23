# Correctif « cadenas » (22 et 23/11/2026) : sur ordinateur le code n'est jamais retenu ; cadenas visible partout ; écran de code devant toute fenêtre.
# 16 remplacements vérifiés (chaque ancre doit exister le nombre de fois attendu). Usage : python tools/correctif_cadenas.py index.html test/index.html
import sys

LOCK_FN = 'function lockNow(){if(!SEC.unlocked)return;try{secFlush();}catch(e){}SEC.unlocked=false;SEC.key=null;sessClear();lockScreen("unlock","");}'
LOCK_FN2 = 'function lockNow(q){if(!SEC.unlocked)return;try{secFlush();}catch(e){}SEC.unlocked=false;SEC.key=null;sessClear();lockScreen("unlock","");if(q&&q!==true)lockCast();}'
MENU_LOCK = '<button type="button" class="btn s" id="lock_now" title="Verrouiller l\'écran">🔒 Verrouiller l\'écran</button>'
JM_VER = '<div class="jmenu" id="jmenu" hidden><div class="jm-ver" aria-label="Version">${esc(appVerFull())}</div>'
MORE = '<button type="button" class="btn ghost more" id="more_btn"'
B = '${lockBtnHTML()}'
PIN1 = '<input id="pin1" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="6" placeholder="Code" autocomplete="off">'
PIN2 = '<input id="pin2" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="6" placeholder="Confirmer" autocomplete="off">'
UID_AC = 'autocomplete="username" autocapitalize="none"'
SESS_SAVE = 'async function sessSave(){try{const m=secMeta();if(!m)return;'
SESS_REST = 'async function sessRestore(){try{const j=JSON.parse(localStorage.getItem("sos_sess")||"null");'
AUTO = r'let busy=false;pi.oninput=async()=>{pi.value=pi.value.replace(/\D/g,"");if(busy||pi.value.length<len)return;busy=true;try{await go();}finally{busy=false;}};'
AUTO2 = r'let busy=false,prev="";pi.oninput=async()=>{pi.value=pi.value.replace(/\D/g,"");const v=pi.value,typed=!deskLike()||(v.length===prev.length+1&&v.slice(0,prev.length)===prev);prev=v;if(busy||v.length<len||!typed)return;busy=true;try{await go();}finally{busy=false;}};'

MODULE = (
    "/* 22/11/2026 — cadenas toujours à portée de main : barre du haut du téléphone, en-têtes Tournée / Journal / Fin de garde / Base médicaments / Patient validé,\n"
    "   et premier bouton du menu ⋯ (il était descendu au 8e rang, sous l'écran). Un seul écouteur pour tous les cadenas. */\n"
    "function lockBtnHTML(){return `<button type=\"button\" class=\"btn s lkbtn\" data-lock title=\"Verrouiller l'écran\" aria-label=\"Verrouiller l'écran\">🔒</button>`;}\n"
    "document.addEventListener(\"click\",ev=>{const b=ev.target&&ev.target.closest&&ev.target.closest(\"[data-lock],#lock_now\");if(!b||!SEC.unlocked)return;ev.preventDefault();lockNow(ev);});\n"
    "/* 23/11/2026 — ordinateur (poste que d'autres peuvent utiliser) : le code n'y est jamais retenu.\n"
    "   1. aucune session gardée : fermer l'onglet ou la fenêtre, ou recharger la page, redemande le code (téléphone et tablette : 20 minutes, inchangé) ;\n"
    "   2. champ du code en texte masqué et non en « mot de passe » : le navigateur ne propose plus de l'enregistrer et ne le remplit plus tout seul ;\n"
    "   3. validation automatique seulement quand les chiffres sont tapés un à un (un code collé ou rempli d'un coup attend Entrée ou « Déverrouiller ») ;\n"
    "   4. le cadenas verrouille aussi les autres onglets et fenêtres de l'app ; retour par le bouton Précédent du navigateur : code redemandé. */\n"
    "function deskLike(){return !(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)||(navigator.platform===\"MacIntel\"&&navigator.maxTouchPoints>1));}\n"
    "function pinAttr(){return deskLike()?`type=\"text\" class=\"pinmask\" name=\"c${Date.now().toString(36)}\" spellcheck=\"false\" autocorrect=\"off\" data-lpignore=\"true\" data-1p-ignore=\"true\" data-bwignore=\"true\" data-form-type=\"other\"`:`type=\"password\"`;}\n"
    "function uidAc(){return deskLike()?\"off\":\"username\";}\n"
    "let LOCK_LAST=Date.now(),LOCK_BC=null;\n"
    "[\"pointerdown\",\"keydown\",\"touchstart\"].forEach(t=>document.addEventListener(t,()=>{LOCK_LAST=Date.now();},{passive:true,capture:true}));\n"
    "document.addEventListener(\"visibilitychange\",()=>{try{if(!document.hidden&&deskLike()&&SEC.unlocked&&Date.now()-LOCK_LAST>SEC.lockDelayMin*60*1000)lockNow();}catch(e){}});\n"
    "window.addEventListener(\"pageshow\",ev=>{try{if(ev.persisted&&deskLike()&&SEC.unlocked)lockNow();}catch(e){}});\n"
    "try{LOCK_BC=new BroadcastChannel(\"packs-verrou:\"+location.pathname.slice(0,location.pathname.lastIndexOf(\"/\")+1));LOCK_BC.onmessage=ev=>{try{if(ev.data===\"verrou\"&&SEC.unlocked)lockNow(true);}catch(e){}};}catch(e){}\n"
    "function lockCast(){try{if(LOCK_BC)LOCK_BC.postMessage(\"verrou\");}catch(e){}}\n"
)

CSS = (
    "<style>/* 22/11/2026 — verrouillage : cadenas visible partout ; l'écran de code passe devant toute fenêtre ouverte (document du patient, résumé, scanner, antibiotiques…) */\n"
    ".jbar.phone .lkbtn{min-width:42px;padding:0 9px;justify-content:center;font-size:18px}\n"
    ".jhead .lkbtn{flex:none;margin-left:auto;min-width:44px;min-height:40px;display:inline-flex;align-items:center;justify-content:center}\n"
    "body.phone .jhead>span:empty{display:none}\n"
    ".lkbtn .ico{margin-right:0!important}\n"
    "@media (max-width:350px){.jbar.phone .appver{display:none!important}}\n"
    "@media screen{body.locked>*:not(#lock):not(#updbar):not(#updall):not(#testbadge){visibility:hidden!important}}\n"
    "/* 23/11/2026 — ordinateur : le code est un champ texte masqué (jamais « mot de passe ») */\n"
    ".pinmask{-webkit-text-security:disc;text-security:disc}\n"
    "</style>"
)

REPL = [
    # (nom, ancre, remplacement, nombre d'occurrences attendu)
    ("module, écouteurs et lockNow", LOCK_FN, MODULE + LOCK_FN2, 1),
    ("menu : retrait du 8e rang", MENU_LOCK, "", 1),
    ("menu : premier bouton", JM_VER, JM_VER + MENU_LOCK, 1),
    ("barre du haut du téléphone", MORE, B + MORE, 1),
    ("en-tête Journal", '<h1>Journal de garde</h1><span style="flex:1"></span>${topbarBtns()}</div>', '<h1>Journal de garde</h1><span style="flex:1"></span>${topbarBtns()}' + B + '</div>', 1),
    ("en-tête Fin de garde", '<h1>Fin de garde</h1><span style="flex:1"></span>${topbarBtns()}</div>', '<h1>Fin de garde</h1><span style="flex:1"></span>${topbarBtns()}' + B + '</div>', 1),
    ("en-tête Tournée", '<h1>Tournée</h1><span style="flex:1"></span>${topbarBtns()}</div>', '<h1>Tournée</h1><span style="flex:1"></span>${topbarBtns()}' + B + '</div>', 1),
    ("en-tête Patient validé", '<h1>Patient validé ✓</h1><span style="flex:1"></span>${topbarBtns()}</div>', '<h1>Patient validé ✓</h1><span style="flex:1"></span>${topbarBtns()}' + B + '</div>', 1),
    ("en-tête Base médicaments", '<h1>Base médicaments</h1></div>', '<h1>Base médicaments</h1>' + B + '</div>', 1),
    ("styles", "</head>", CSS + "</head>", 1),
    ("ordinateur : session non gardée (écriture)", SESS_SAVE, 'async function sessSave(){try{if(deskLike()){sessClear();return;}const m=secMeta();if(!m)return;', 1),
    ("ordinateur : session non gardée (lecture)", SESS_REST, 'async function sessRestore(){try{if(deskLike()){sessClear();return false;}const j=JSON.parse(localStorage.getItem("sos_sess")||"null");', 1),
    ("champ du code", PIN1, PIN1.replace('type="password"', '${pinAttr()}'), 2),
    ("champ de confirmation du code", PIN2, PIN2.replace('type="password"', '${pinAttr()}'), 1),
    ("champ identifiant", UID_AC, 'autocomplete="${uidAc()}" autocapitalize="none"', 2),
    ("validation automatique à la frappe", AUTO, AUTO2, 1),
]
MARKS = ("lockBtnHTML", "data-lock", "lkbtn", "deskLike", "pinAttr", "uidAc", "pinmask", "lockCast", "LOCK_BC", "LOCK_LAST")

def patch(path):
    s = open(path, encoding="utf-8", newline="").read()
    for k in MARKS:
        assert k not in s, "correctif déjà appliqué (%s) : %s" % (k, path)
    for nom, a, b, n in REPL:
        c = s.count(a)
        assert c == n, "%s : ancre trouvée %d fois (attendu %d) dans %s" % (nom, c, n, path)
        s = s.replace(a, b)
    # contrôles : un seul bouton #lock_now dans le menu, placé avant « Affichage » ; plus aucun champ de code en « mot de passe » écrit en dur
    m = s.index('id="jmenu"'); assert s.index(MENU_LOCK, m) < s.index('<div class="dmode"', m)
    assert s.count(MENU_LOCK) == 1 and s.count("lockBtnHTML()") == 7  # 1 définition + 6 emplacements
    assert s.count('id="pin1" type="password"') == 0 and s.count('id="pin2" type="password"') == 0 and s.count("${pinAttr()}") == 3
    open(path, "w", encoding="utf-8", newline="").write(s)
    print("correctif appliqué :", path, "(%d remplacements)" % len(REPL))

if __name__ == "__main__":
    for p in sys.argv[1:]:
        patch(p)
