/* Packs SOS — service worker (packs-sos-sub-v38) : fonctionnement hors ligne ; les cartes, BAN, OSRM et l'API ne passent jamais par le cache */
const CACHE="packs-sos-sub-v38";
const FILES=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png","./apple-touch-icon.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>Promise.all(FILES.map(f=>c.add(new Request(f,{cache:"reload"})).catch(()=>{})))));});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>false /* chaque version de secours garde son cache */).map(k=>caches.delete(k)))));}); /* pas de clients.claim() : la première page reste non contrôlée, sans rechargement surprise ; la mise à jour passe par skipWaiting (bouton « Mettre à jour ») */
self.addEventListener("message",e=>{if(e.data==="skip")self.skipWaiting();});
self.addEventListener("fetch",e=>{
  const req=e.request;if(req.method!=="GET")return;
  const url=new URL(req.url);if(url.origin!==self.location.origin)return;
  const scope=new URL(self.registration.scope).pathname;if(!url.pathname.startsWith(scope))return;
  
  e.respondWith(caches.open(CACHE).then(async c=>{const hit=await c.match(req,{ignoreSearch:true});if(hit)return hit;
    try{const res=await fetch(req);if(res&&res.ok&&(req.mode==="navigate"||url.pathname.endsWith("/")||/\.(html|webmanifest|png|js)$/.test(url.pathname)))c.put(req,res.clone());return res;}
    catch(err){if(req.mode==="navigate"){const idx=await c.match("./index.html")||await c.match("./");if(idx)return idx;}throw err;}}));
});
