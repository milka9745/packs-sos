# -*- coding: utf-8 -*-
"""Dossier de secours d'une version en service (06/11/2026), sur le modèle de v38/ et v39/.

Usage : python tools/secours.py 41k [origin/main]
Copie les six fichiers de l'application (index.html, sw.js, manifest.webmanifest, trois icônes) depuis la racine de la
révision donnée (par défaut origin/main, la version en service) dans le dossier v<version>/ :
- titre et nom d'écran d'accueil distincts (« Packs SOS v41k », « Packs SOS 41k ») ;
- service worker à cache propre (« packs-sos-sub-v41k »), qui ne supprime jamais les autres caches ;
- pas de version.json : le secours ne propose jamais de mise à jour.
Les données (journal, tournée, profil) restent celles du site, partagées avec la racine, comme pour v39/."""
import io, os, re, subprocess, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V=sys.argv[1]; REV=sys.argv[2] if len(sys.argv)>2 else "origin/main"
OUT=os.path.join(ROOT,"v"+V)
assert re.fullmatch(r"\d+[a-z]?",V), "version attendue : 41k"
assert not os.path.exists(OUT), OUT+" existe déjà : rien n'est écrasé"
os.makedirs(OUT)
def show(path):
    return subprocess.run(["git","show",REV+":"+path],cwd=ROOT,capture_output=True,check=True).stdout
for f in ("apple-touch-icon.png","icon-192.png","icon-512.png"):
    open(os.path.join(OUT,f),"wb").write(show(f))
s=show("index.html").decode("utf-8")
s,n1=re.subn(r"<title>[^<]*</title>","<title>Packs SOS v"+V+"</title>",s,count=1)
s,n2=re.subn(r'(<meta name="apple-mobile-web-app-title" content=")[^"]*(">)',r"\g<1>Packs SOS "+V+r"\g<2>",s,count=1)
assert n1==1 and n2==1,(n1,n2)
# le dossier porte une lettre (v41k) : siteBase() doit quand même remonter à la racine du site pour profil.json et ocr/
old_sb=r'replace(/\/v\d+\/(index\.html)?$/,"/")'; new_sb=r'replace(/\/v\d+[a-z]?\/(index\.html)?$/,"/")'
assert s.count(old_sb)+s.count(new_sb)==1,(s.count(old_sb),s.count(new_sb))
s=s.replace(old_sb,new_sb)
io.open(os.path.join(OUT,"index.html"),"w",encoding="utf-8",newline="").write(s)
w=show("sw.js").decode("utf-8")
w,n3=re.subn(r'const CACHE="[^"]+";','const CACHE="packs-sos-sub-v'+V+'";',w,count=1)
w=re.sub(r"\(packs-sos-[^)]*\)","(packs-sos-sub-v"+V+")",w,count=1)
w,n4=re.subn(r"ks\.filter\(k=>[^)]*\)&&k!==CACHE\)","ks.filter(k=>false /* chaque version de secours garde son cache */)",w,count=1)
w,n5=re.subn(r"\n[^\n]*sous-dossiers de versions : leur propre service worker[^\n]*","",w,count=1)
assert n3==1 and n4==1 and n5==1,(n3,n4,n5)
io.open(os.path.join(OUT,"sw.js"),"w",encoding="utf-8",newline="").write(w)
m=show("manifest.webmanifest").decode("utf-8")
m,n6=re.subn(r'"name":\s*"[^"]*"','"name": "Packs SOS v'+V+'"',m,count=1)
m,n7=re.subn(r'"short_name":\s*"[^"]*"','"short_name": "Packs SOS '+V+'"',m,count=1)
assert n6==1 and n7==1,(n6,n7)
io.open(os.path.join(OUT,"manifest.webmanifest"),"w",encoding="utf-8",newline="").write(m)
print("secours écrit :",OUT,sorted(os.listdir(OUT)))
