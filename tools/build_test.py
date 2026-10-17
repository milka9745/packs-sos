# Construit le dossier test/ (version de test publiée à part, adresse …/packs-sos/test/) à partir de la branche ia :
# stockage local préfixé « pst: » (jamais celui de l'outil de garde), base photos séparée, cache du service worker séparé,
# manifeste « Packs SOS TEST », icônes badgées « TEST », bandeau visible. L'outil de garde (racine, main) n'est pas modifié.
# Lancer depuis la racine du dépôt (branche ia) : python tools/build_test.py <dossier de sortie>
import os, sys, re, json, base64, asyncio, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,"test")
os.makedirs(OUT,exist_ok=True)
ver=json.load(open(os.path.join(ROOT,"version.json"),encoding="utf-8"))
V=str(ver.get("version","41"))+"-test"

SHIM='''<script>/* VERSION TEST : stockage séparé de l'outil de garde (préfixe « pst: » sur localStorage et sessionStorage) */
(function(){try{var P="pst:",S=Storage.prototype,g=S.getItem,s=S.setItem,r=S.removeItem,k=S.key;
S.getItem=function(x){return g.call(this,P+x);};S.setItem=function(x,v){return s.call(this,P+x,v);};S.removeItem=function(x){return r.call(this,P+x);};
S.clear=function(){for(var i=this.length-1;i>=0;i--){var y=k.call(this,i);if(y&&y.indexOf(P)===0)r.call(this,y);}};window.__PACKS_TEST__=true;}catch(e){}})();</script>'''
BADGE='''<style>#testbadge{position:fixed;left:0;right:0;top:0;height:4px;background:#D0021B;z-index:2147483646;pointer-events:none}
@media print{#testbadge,#testpill{display:none!important}@page{margin:0}}
#testpill{position:fixed;left:6px;bottom:calc(env(safe-area-inset-bottom,0px) + 6px);z-index:2147483646;pointer-events:none;background:#D0021B;color:#fff;font:800 11px/1 system-ui,sans-serif;letter-spacing:.6px;padding:4px 7px;border-radius:6px;opacity:.92}</style>'''
BADGE_BODY='<div id="testbadge" aria-hidden="true"></div><div id="testpill" aria-hidden="true">TEST · '+V.replace("-test","")+'</div>'

s=open(os.path.join(ROOT,"index.html"),encoding="utf-8").read()
def rep(a,b,n=1,regex=False):
    global s
    c=len(re.findall(a,s)) if regex else s.count(a)
    assert c==n,(c,a[:80])
    s=re.sub(a,b,s) if regex else s.replace(a,b)
rep("<head>","<head>\n"+SHIM)
# livraison affichée « v41x · test · date de construction » (jamais sur les documents)
import datetime
s,_n=re.subn(r'const APP_BUILD=\{v:"([^"]*)",branch:"[^"]*",date:"[^"]*"\};',lambda m:'const APP_BUILD={v:"'+m.group(1)+'",branch:"test",date:"'+datetime.datetime.now().strftime("%d/%m %H:%M")+'"};',s)
assert _n==1
rep('indexedDB.open("packs-sos-photos"','indexedDB.open("packs-sos-test-photos"')
rep('replace(/\\/v\\d+\\/(index\\.html)?$/,"/")','replace(/\\/(?:v\\d+|test)\\/(index\\.html)?$/,"/")')
rep(r'<link rel="apple-touch-icon" href="data:image/png;base64,[^"]+">','<link rel="apple-touch-icon" href="apple-touch-icon.png">',regex=True)
rep("<title>Packs SOS — Docteur Mickaël DEIE</title>","<title>Packs SOS TEST</title>")
rep('<meta name="apple-mobile-web-app-title" content="Packs SOS">','<meta name="apple-mobile-web-app-title" content="TEST Packs">')
rep('<meta name="theme-color" content="#22252B">','<meta name="theme-color" content="#D0021B">')
rep("</head>",BADGE+"</head>")
s=re.sub(r"(<body[^>]*>)",lambda m:m.group(1)+BADGE_BODY,s,count=1)
open(os.path.join(OUT,"index.html"),"w",encoding="utf-8",newline="").write(s)

w=open(os.path.join(ROOT,"sw.js"),encoding="utf-8").read()
w=re.sub(r'const CACHE="[^"]+";','const CACHE="packs-sos-test-'+V+'";',w)
w=w.replace("ks.filter(k=>/^packs-sos-v\\d+[a-z]?$/.test(k)&&k!==CACHE)","ks.filter(k=>/^packs-sos-test-/.test(k)&&k!==CACHE)")
assert "packs-sos-test-" in w and "/^packs-sos-test-/" in w
w="/* VERSION TEST (dossier test/) : cache séparé, ne touche jamais au cache de l'outil de garde */\n"+w
open(os.path.join(OUT,"sw.js"),"w",encoding="utf-8",newline="").write(w)

man=json.load(open(os.path.join(ROOT,"manifest.webmanifest"),encoding="utf-8"))
man.update({"name":"Packs SOS TEST","short_name":"TEST Packs","theme_color":"#D0021B","id":"./"})
open(os.path.join(OUT,"manifest.webmanifest"),"w",encoding="utf-8",newline="\n").write(json.dumps(man,ensure_ascii=False,indent=1))
json.dump({"version":V,"date":ver.get("date",""),"notes":["Version de test (branche ia) : données séparées de l'outil de garde."]+ver.get("notes",[])[:2]},open(os.path.join(OUT,"version.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)

async def icons():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page()
        for f in ["icon-192.png","icon-512.png","apple-touch-icon.png"]:
            src=os.path.join(ROOT,f)
            data="data:image/png;base64,"+base64.b64encode(open(src,"rb").read()).decode()
            out=await pg.evaluate("""async(d)=>{const im=new Image();im.src=d;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const g=c.getContext('2d');g.drawImage(im,0,0);
              const W=c.width,H=c.height,h=Math.round(H*0.27);g.fillStyle='#D0021B';g.fillRect(0,H-h,W,h);g.fillStyle='#fff';g.font='900 '+Math.round(h*0.72)+'px Arial, sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText('TEST',W/2,H-h/2+Math.round(h*0.04));return c.toDataURL('image/png');}""",data)
            open(os.path.join(OUT,f),"wb").write(base64.b64decode(out.split(",")[1]))
        await b.close()
asyncio.run(icons())
print("test/ construit :",V,os.listdir(OUT))
