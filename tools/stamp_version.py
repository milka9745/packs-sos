# Numéro de livraison : met à jour APP_BUILD (index.html), le cache (sw.js) et version.json avec la même lettre.
# Usage : python tools/stamp_version.py 41n   (la date et l'heure sont celles du moment ; branche « main » dans la source)
import sys, re, json, datetime
v=sys.argv[1]
now=datetime.datetime.now()
d=now.strftime("%d/%m %H:%M")
s=open("index.html",encoding="utf-8").read()
s,n=re.subn(r'const APP_BUILD=\{v:"[^"]*",branch:"[^"]*",date:"[^"]*"\};','const APP_BUILD={v:"'+v+'",branch:"main",date:"'+d+'"};',s)
assert n==1
open("index.html","w",encoding="utf-8",newline="").write(s)
w=open("sw.js",encoding="utf-8").read()
w=re.sub(r'packs-sos-v[0-9a-z]+','packs-sos-v'+v,w)
open("sw.js","w",encoding="utf-8",newline="").write(w)
j=json.load(open("version.json",encoding="utf-8"));j["version"]=v;j["date"]=now.strftime("%Y-%m-%d")
open("version.json","w",encoding="utf-8",newline="\n").write(json.dumps(j,ensure_ascii=False,indent=2)+"\n")
print("livraison v"+v+" ·",d)
