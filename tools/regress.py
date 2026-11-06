# -*- coding: utf-8 -*-
"""Lanceur des suites Playwright, plusieurs à la fois (06/11/2026).

Usage :
  python tools/regress.py --all                      # tour complet (publication en service) ; ≈ 10 min avec 4 travaux
  python tools/regress.py test_fil6 test_express     # suites ciblées (modification limitée) ; test_fil_v41z est ajouté comme parcours complet
  python tools/regress.py --all --site <dossier>     # ajoute test_dossier_test.py <site> (site assemblé : racine + test/)
  options : --jobs 4 (travaux en parallèle), --no-fil (sans le parcours complet), --log <fichier>
Chaque suite a son port fixe (PORT=…) : les suites qui partagent un port tournent l'une après l'autre, les autres en parallèle.
test_racine_41z.py (deux sites) n'est jamais lancé d'ici : python tests/test_racine_41z.py <site_41k> <site_nouveau>.
Sortie : une ligne par suite (résultat, durée, échecs), le total, code de retour 1 si une suite échoue."""
import argparse, os, re, subprocess, sys, time, concurrent.futures as cf
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS=os.path.join(ROOT,"tests")
WITH_ARGS={"test_dossier_test.py","test_racine_41z.py"}
FIL="test_fil_v41z.py"
def port_of(path):
    try: s=open(path,encoding="utf-8").read()
    except Exception: return None
    m=re.search(r'PORT\s*=\s*"?(\d{4,5})"?',s) or re.search(r'localhost:(\d{4,5})',s)  # anciennes suites : port écrit dans l'adresse
    return int(m.group(1)) if m else None
def run_one(name,args):
    t0=time.time(); env=dict(os.environ,PYTHONIOENCODING="utf-8")
    try:
        r=subprocess.run([sys.executable,os.path.join(TESTS,name)]+args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",env=env,timeout=1800)
        out=(r.stdout or "")+(r.stderr or ""); code=r.returncode
    except subprocess.TimeoutExpired as e:
        out=str(e.stdout or "")+"\nDÉLAI DÉPASSÉ (30 min)"; code=124
    m=re.findall(r"(\d+)/(\d+) tests OK",out); score=m[-1] if m else None
    fails=[l.strip()[:160] for l in out.splitlines() if l.startswith("FAIL")]
    trace="Traceback" in out
    return {"suite":name,"code":code,"score":score,"fails":fails,"trace":trace,"s":round(time.time()-t0),"out":out}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("suites",nargs="*"); ap.add_argument("--all",action="store_true"); ap.add_argument("--jobs",type=int,default=4)
    ap.add_argument("--site"); ap.add_argument("--no-fil",action="store_true"); ap.add_argument("--log"); a=ap.parse_args()
    if a.all: names=sorted(f for f in os.listdir(TESTS) if re.match(r"test_.*\.py$",f) and f not in WITH_ARGS)
    else:
        names=[]
        for s in a.suites:
            n=os.path.basename(s); n=n if n.endswith(".py") else n+".py"; n=n if n.startswith("test_") else "test_"+n
            if not os.path.exists(os.path.join(TESTS,n)): sys.exit("suite introuvable : "+n)
            if n not in names: names.append(n)
        if not a.no_fil and FIL not in names and os.path.exists(os.path.join(TESTS,FIL)): names.append(FIL)
    if not names: sys.exit("aucune suite ; --all ou des noms")
    jobs=[(n,[]) for n in names if n not in WITH_ARGS]
    if a.site: jobs.append(("test_dossier_test.py",[a.site]))
    groups={}
    for n,args in jobs: groups.setdefault(port_of(os.path.join(TESTS,n)) or ("solo",n),[]).append((n,args))
    print(f"{len(jobs)} suites, {len(groups)} files de ports, {a.jobs} travaux en parallèle"); t0=time.time(); res=[]
    def run_group(g):
        return [run_one(n,args) for n,args in g]
    with cf.ThreadPoolExecutor(max_workers=max(1,a.jobs)) as ex:
        for lst in ex.map(run_group,groups.values()):
            for r in lst:
                res.append(r); okk=r["code"]==0 and not r["fails"] and not r["trace"]
                print(("OK   " if okk else "ÉCHEC")+f" {r['suite']:<26} {r['score'][0]+'/'+r['score'][1] if r['score'] else '—':>9} {r['s']:>4} s"+("" if okk else "  "+(" | ".join(r["fails"][:3]) or ("traceback" if r["trace"] else "code "+str(r["code"])))),flush=True)
    bad=[r for r in res if r["code"]!=0 or r["fails"] or r["trace"]]
    tot=round(time.time()-t0); print(f"\n{len(res)-len(bad)}/{len(res)} suites OK en {tot//60} min {tot%60} s"+(" — à revoir : "+", ".join(r["suite"] for r in bad) if bad else ""))
    if a.log:
        with open(a.log,"w",encoding="utf-8") as f:
            for r in res: f.write(f"=== {r['suite']} (code {r['code']}, {r['s']} s)\n{r['out']}\n")
    sys.exit(1 if bad else 0)
if __name__=="__main__": main()
