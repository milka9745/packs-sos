"""Captures fictives de fiches MccMissionSG (aucune donnée réelle) : mise en page iPhone (clair) et Android (sombre, intitulés différents)."""
IOS = """<html><head><meta charset="utf-8"><style>
body{margin:0;font-family:-apple-system,Helvetica,Arial,sans-serif;background:#fff;color:#1d2b4a;width:375px}
.top{background:#26416b;color:#fff;padding:18px 16px 40px;font-size:15px}.top b{display:block;font-size:16px}
.card{margin:10px 12px;border:1px solid #d8dde8;border-radius:16px;padding:12px 14px;background:#f6f8fc}
.h{font-weight:700;font-size:15px;letter-spacing:.5px;margin-bottom:8px}.big{font-size:17px;font-weight:700}
.tel{display:flex;gap:14px}.tel div{flex:1}.num{color:#2b6fd6;font-size:16px}
</style></head><body>
<div class="top"><b>Auto-Régulation / Visite</b>1v+2c méd, 30 c + 0 t</div>
<div class="card"><div class="h">INFORMATIONS PATIENT</div><div class="big">MARTIN PAUL</div><div>Né(e) le 03/04/1990 - 36 A</div>
<div class="tel"><div>Tél patient<br><span class="num">06 11 22 33 44</span></div><div>Tél appelant<br><span class="num">06 55 66 77 88</span></div></div></div>
<div class="card"><div class="h">INTERVENTION</div><div>16/10/2026 19:51</div><br><div class="big">FIEVRE</div><br>
<div>ATTENTION, ADRESSE REPOSITIONNEE PAR<br>DURAND ALAIN LE 01/02/2025 10:11:12</div><div>Rdv 20h30 envoyé par SMS au 06 11 22 33 44</div></div>
<div class="card"><div class="h">ADRESSE PATIENT</div><div class="big">8 RUE DES LILAS,<br>45400, FLEURY-LES-AUBRAIS</div><div>Bat : B  Etg : 2  Por : 21</div></div>
</body></html>"""
ANDROID = """<html><head><meta charset="utf-8"><style>
body{margin:0;font-family:Roboto,Arial,sans-serif;background:#121212;color:#e8e8e8;width:412px}
.bar{background:#1f2a44;padding:14px 18px;font-size:18px}
.sec{padding:14px 18px;border-bottom:1px solid #333}.l{color:#9fb3d9;font-size:13px;text-transform:uppercase}.v{font-size:18px;margin-top:4px}
</style></head><body>
<div class="bar">Mission en cours</div>
<div class="sec"><div class="l">Informations patient</div><div class="v">DUBOIS CLAIRE</div><div class="v">Née le 12/05/1958 - 68 A</div></div>
<div class="sec"><div class="l">Tél. patient</div><div class="v">02 38 00 11 22</div></div>
<div class="sec"><div class="l">Tél. appelant</div><div class="v">06 12 34 56 78</div></div>
<div class="sec"><div class="l">Intervention</div><div class="v">DOULEUR ABDOMINALE</div><div class="v">Commentaire : sonner au 2e</div></div>
<div class="sec"><div class="l">Adresse :</div><div class="v">14 AVENUE DES PINS</div><div class="v">45100 ORLÉANS-LA-SOURCE</div><div class="v">Bat : C Etg : 4 Por : 12</div></div>
</body></html>"""
EXPECT = {
 "ios": {"addr": ["8 RUE DES LILAS", "45400", "FLEURY-LES-AUBRAIS"], "tel": "0611223344", "ddn": "03/04/1990", "bat": "Bât. B · Étage 2 · Porte 21", "motif": "FIEVRE"},
 "android": {"addr": ["14 AVENUE DES PINS", "45100", "ORLÉANS-LA-SOURCE"], "tel": "0238001122", "ddn": "12/05/1958", "bat": "Bât. C · Étage 4 · Porte 12", "motif": "DOULEUR ABDOMINALE"},
}
async def make(browser, out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, html, w, dpr in [("ios", IOS, 375, 3), ("android", ANDROID, 412, 2.625)]:
        ctx = await browser.new_context(viewport={"width": w, "height": 900}, device_scale_factor=dpr)
        pg = await ctx.new_page()
        await pg.set_content(html)
        path = os.path.join(out_dir, f"fiche-{name}.png")
        await pg.screenshot(path=path, full_page=True)
        await ctx.close()
        paths[name] = path
    return paths
