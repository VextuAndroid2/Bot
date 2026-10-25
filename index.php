<?php
require __DIR__ . '/config.php';
$csrf = csrf_token();
$user = current_user();
?><!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#0a0406">
<title>Vextu Bots - GUILD</title>
<style>
:root{
  --bg:#070308;--card:rgba(26,10,14,.92);--border:rgba(255,60,90,.22);
  --accent:#ff2d55;--accent2:#ff7a45;--text:#fff7f9;--muted:#c9a7ae;
  --ok:#34d399;--danger:#fb7185;--glow:0 0 60px rgba(255,45,85,.28);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
  background:var(--bg);color:var(--text);
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  overflow-x:hidden;
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(1000px 500px at 50% -10%,rgba(255,45,85,.25),transparent 60%),
    radial-gradient(600px 400px at 100% 100%,rgba(255,120,50,.08),transparent 50%),
    radial-gradient(400px 300px at 0% 80%,rgba(255,40,80,.06),transparent 50%);
  animation:bgPulse 10s ease-in-out infinite alternate;
}
body::after{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.035;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
@keyframes bgPulse{from{filter:hue-rotate(0deg) brightness(1)}to{filter:hue-rotate(14deg) brightness(1.05)}}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes pop{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:scale(1)}}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.82)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes shine{to{background-position:200% center}}
@keyframes barMove{0%{background-position:0 0}100%{background-position:60px 0}}
.wrap{position:relative;z-index:1;max-width:980px;margin:0 auto;padding:28px 16px 90px}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px;animation:fadeUp .5s ease}
.brand{display:flex;align-items:center;gap:12px}
.logo{
  width:42px;height:42px;border-radius:14px;
  background:linear-gradient(135deg,#ff2d55,#ff7a45);
  box-shadow:0 8px 24px rgba(255,45,85,.4);
  display:grid;place-items:center;font-weight:900;font-size:18px;color:#fff;
  animation:float 4s ease-in-out infinite;
}
.badge{
  display:inline-flex;align-items:center;gap:8px;
  color:var(--accent);font-size:11px;font-weight:800;letter-spacing:2.6px;text-transform:uppercase;
}
.badge i{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent);animation:pulse 1.5s infinite}
h1{
  font-size:clamp(2.1rem,5.4vw,3.3rem);font-weight:900;line-height:1.05;margin:6px 0 8px;
  background:linear-gradient(120deg,#ff2d55 0%,#ff6b6b 40%,#ffb347 100%);
  background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;
  animation:fadeUp .55s ease, shine 5s linear infinite;
}
.sub{color:var(--muted);font-size:14px;margin-bottom:22px;animation:fadeUp .6s ease}
.sub b{color:var(--accent)}
.card{
  background:var(--card);border:1px solid var(--border);border-radius:24px;padding:22px;
  margin-bottom:16px;backdrop-filter:blur(18px);
  box-shadow:0 16px 50px rgba(0,0,0,.4);
  animation:fadeUp .55s ease both;transition:transform .28s,box-shadow .28s;
}
.card:hover{transform:translateY(-3px);box-shadow:var(--glow)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.stat{padding:12px;border-radius:16px;background:rgba(255,45,85,.04);border:1px solid rgba(255,45,85,.08)}
.stat .l{font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.stat .v{font-size:1.4rem;font-weight:800;margin-top:5px;background:linear-gradient(90deg,#ffe4ea,#ff8aa0);-webkit-background-clip:text;background-clip:text;color:transparent}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:7px;font-weight:600}
input,select{
  width:100%;padding:14px 16px;border-radius:14px;border:1px solid var(--border);
  background:#12080b;color:var(--text);font-size:15px;outline:none;transition:.2s;
}
input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 4px rgba(255,45,85,.15)}
.btn{
  width:100%;padding:15px 18px;border:0;border-radius:14px;font-weight:800;font-size:15px;
  cursor:pointer;margin-top:12px;position:relative;overflow:hidden;transition:.2s;
}
.btn::after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.16),transparent);transform:translateX(-140%);transition:transform .55s}
.btn:hover::after{transform:translateX(140%)}
.btn:active{transform:scale(.975)}
.btn-p{background:linear-gradient(135deg,#ff2d55,#ff4d6d);color:#fff;box-shadow:0 10px 28px rgba(255,45,85,.38)}
.btn-g{background:#160a0d;color:var(--muted);border:1px solid var(--border)}
.btn:disabled{opacity:.45;cursor:not-allowed}
.msg{display:none;margin-top:12px;padding:12px 14px;border-radius:12px;font-size:13px;animation:pop .28s ease}
.msg.err{display:block;background:rgba(80,12,22,.55);color:#ff9aab;border:1px solid rgba(180,50,70,.35)}
.msg.ok{display:block;background:rgba(8,50,32,.45);color:var(--ok);border:1px solid rgba(30,120,70,.35)}
.hidden{display:none!important}
.flex{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.user-pill{padding:9px 14px;border-radius:999px;background:#12080b;border:1px solid var(--border);font-size:13px}
.user-pill span{color:var(--accent);font-weight:800}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:560px){.row{grid-template-columns:1fr}}
.tabs{display:flex;gap:8px;margin-bottom:16px}
.tab{flex:1;text-align:center;padding:12px;border-radius:13px;background:#12080b;border:1px solid var(--border);color:var(--muted);font-size:13px;font-weight:700;cursor:pointer;transition:.2s}
.tab.on{color:var(--accent);border-color:rgba(255,45,85,.55);background:linear-gradient(135deg,rgba(255,45,85,.18),rgba(255,100,50,.08));box-shadow:0 0 20px rgba(255,45,85,.12)}
.ulist{max-height:280px;overflow:auto;margin-top:12px}
.uitem{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border:1px solid var(--border);background:#12080b;border-radius:13px;margin-bottom:8px;animation:fadeUp .3s ease}
.uitem button{background:#241016;border:1px solid var(--border);color:var(--accent);border-radius:9px;padding:7px 12px;font-size:12px;font-weight:700;cursor:pointer}
.footer{text-align:center;margin-top:34px;color:var(--muted);font-size:12px}
.footer span{color:var(--accent);font-weight:700}
.hint{color:var(--muted);font-size:12px;margin-top:11px;line-height:1.5}
.engine-pill{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;border:1px solid var(--border);background:#12080b;font-size:13px}
.dot{width:9px;height:9px;border-radius:50%}
.dot.on{background:var(--ok);box-shadow:0 0 10px var(--ok);animation:pulse 1.3s infinite}
.dot.off{background:var(--danger);box-shadow:0 0 10px var(--danger)}

/* LOADING OVERLAY */
.loader-bg{
  position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;
  background:rgba(5,2,4,.82);backdrop-filter:blur(14px);padding:20px;animation:fadeIn .25s ease;
}
.loader-card{
  width:min(420px,100%);background:rgba(22,8,12,.95);border:1px solid var(--border);
  border-radius:24px;padding:28px 24px;text-align:center;box-shadow:var(--glow);animation:pop .3s ease;
}
.loader-orb{
  width:72px;height:72px;margin:0 auto 18px;border-radius:50%;
  background:conic-gradient(from 0deg,#ff2d55,#ffb347,#ff2d55);
  mask:radial-gradient(circle 28px,transparent 98%,#000 100%);
  -webkit-mask:radial-gradient(circle 28px,transparent 98%,#000 100%);
  animation:spin 1s linear infinite;
}
.loader-card h3{font-size:1.25rem;margin-bottom:8px}
.loader-card p{color:var(--muted);font-size:14px;min-height:40px;line-height:1.45}
.bar{height:10px;border-radius:999px;background:#1a0c10;overflow:hidden;margin:18px 0 8px}
.bar>i{
  display:block;height:100%;width:0%;border-radius:999px;
  background:linear-gradient(90deg,#ff2d55,#ff7a45,#ff2d55);background-size:60px 100%;
  animation:barMove .8s linear infinite;transition:width .35s ease;
}
.loader-pct{font-size:12px;color:var(--muted)}

.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.68);backdrop-filter:blur(8px);z-index:90;display:flex;align-items:center;justify-content:center;padding:18px;animation:fadeIn .2s ease}
.modal{width:min(430px,100%);background:var(--card);border:1px solid var(--border);border-radius:22px;padding:24px;box-shadow:0 24px 70px rgba(0,0,0,.55);animation:pop .25s ease}
.modal h3{margin-bottom:10px;font-size:1.2rem}
.modal p{color:var(--muted);font-size:14px;line-height:1.5;margin-bottom:18px}
.modal .actions{display:flex;gap:10px}
.modal .actions .btn{margin:0}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">
      <div class="logo">V</div>
      <div>
        <div class="badge"><i></i> Live System</div>
      </div>
    </div>
  </div>
  <h1>Vextu Bots - GUILD</h1>
  <p class="sub">Cuentas nuevas · Clan · 8 horas · <b>by Vextu Android</b></p>

  <div id="auth" class="<?= $user ? 'hidden' : '' ?>">
    <div class="card">
      <div class="tabs">
        <div class="tab on" data-t="login">Entrar</div>
        <div class="tab" data-t="reg">Crear cuenta</div>
      </div>
      <div id="f-login">
        <label>Usuario</label>
        <input id="l-user" maxlength="24" autocomplete="username" placeholder="tu usuario">
        <label style="margin-top:12px">Contraseña</label>
        <input id="l-pass" type="password" autocomplete="current-password" placeholder="••••••••">
        <button class="btn btn-p" id="btn-login">Entrar</button>
        <div class="msg" id="m-login"></div>
      </div>
      <div id="f-reg" class="hidden">
        <label>Usuario</label>
        <input id="r-user" maxlength="24" placeholder="mínimo 4 caracteres">
        <label style="margin-top:12px">Contraseña</label>
        <input id="r-pass" type="password" placeholder="mínimo 6">
        <label style="margin-top:12px">Repetir</label>
        <input id="r-pass2" type="password" placeholder="repite la contraseña">
        <button class="btn btn-p" id="btn-reg">Crear cuenta</button>
        <div class="msg" id="m-reg"></div>
      </div>
    </div>
  </div>

  <div id="app" class="<?= $user ? '' : 'hidden' ?>">
    <div class="card">
      <div class="flex">
        <div class="user-pill"><span id="u-name"><?= $user ? clean($user['username']) : '' ?></span> · <span id="u-cred"><?= $user ? (int)$user['credits'] : 0 ?></span> créditos</div>
        <button class="btn btn-g" style="width:auto;margin:0;padding:9px 16px;font-size:13px" id="btn-logout">Salir</button>
      </div>
    </div>

    <div class="card hidden" id="admin-sys">
      <div class="flex" style="margin-bottom:8px">
        <div class="engine-pill"><span class="dot off" id="eng-dot"></span><span id="eng-text">Motor: —</span></div>
      </div>
      <div class="grid" style="margin-top:10px">
        <div class="stat"><div class="l">Región</div><div class="v" id="s-region">—</div></div>
        <div class="stat"><div class="l">Workers</div><div class="v" id="s-bots">0</div></div>
        <div class="stat"><div class="l">Guild</div><div class="v" id="s-guild">—</div></div>
        <div class="stat"><div class="l">Restante</div><div class="v" id="s-left">—</div></div>
        <div class="stat"><div class="l">Cuentas</div><div class="v" id="s-saved">0</div></div>
        <div class="stat"><div class="l">Modo</div><div class="v" id="s-mode">—</div></div>
      </div>
      <p class="hint" id="eng-hint"></p>
    </div>

    <div class="card">
      <h3 style="font-size:1.15rem;margin-bottom:14px;font-weight:800">Lanzar bots al clan</h3>
      <div class="row">
        <div>
          <label>Región</label>
          <select id="region">
            <option>IND</option><option>PK</option><option selected>US</option><option>BR</option><option>SG</option><option>TH</option><option>ID</option><option>VN</option><option>TW</option><option>ME</option><option>RU</option><option>EU</option>
          </select>
        </div>
        <div>
          <label>Clan / Guild ID</label>
          <input id="guild" maxlength="32" placeholder="Ej: 2067735369">
        </div>
      </div>
      <button class="btn btn-p" id="btn-launch">Lanzar · 1 crédito · 4 cuentas nuevas · 8h</button>
      <div class="msg" id="m-launch"></div>
      <p class="hint">Se crean 4 cuentas nuevas, se unen al clan y juegan 8 horas.</p>
    </div>

    <div class="card">
      <h3 style="font-size:1.15rem;margin-bottom:12px;font-weight:800">Tu lanzamiento</h3>
      <div class="grid">
        <div class="stat"><div class="l">Región</div><div class="v" id="u-region">—</div></div>
        <div class="stat"><div class="l">Bots</div><div class="v" id="u-bots">0</div></div>
        <div class="stat"><div class="l">Guild</div><div class="v" id="u-guild">—</div></div>
        <div class="stat"><div class="l">Restante</div><div class="v" id="u-left">—</div></div>
      </div>
    </div>

    <div class="card hidden" id="admin-card">
      <h3 style="font-size:1.15rem;margin-bottom:12px;font-weight:800">Admin Panel</h3>
      <div class="row">
        <div><label>Usuario</label><input id="a-user" placeholder="usuario"></div>
        <div><label>Créditos</label><input id="a-amount" type="number" min="1" max="9999" value="5"></div>
      </div>
      <button class="btn btn-p" id="btn-add">Agregar créditos</button>
      <div class="msg" id="m-admin"></div>
      <div class="ulist" id="user-list"></div>
    </div>
  </div>

  <div class="footer">Vextu Bots - GUILD · <span>by Vextu Android</span></div>
</div>

<div class="modal-bg hidden" id="confirm-modal">
  <div class="modal">
    <h3>Confirmar lanzamiento</h3>
    <p id="confirm-text">¿Crear 4 cuentas nuevas y lanzarlas 8 horas?</p>
    <div class="actions">
      <button class="btn btn-g" id="confirm-no">Cancelar</button>
      <button class="btn btn-p" id="confirm-yes">Confirmar</button>
    </div>
  </div>
</div>

<div class="loader-bg hidden" id="loader">
  <div class="loader-card">
    <div class="loader-orb"></div>
    <h3>Preparando bots</h3>
    <p id="loader-msg">Enviando orden al motor...</p>
    <div class="bar"><i id="loader-bar"></i></div>
    <div class="loader-pct" id="loader-pct">0%</div>
  </div>
</div>

<script>
const CSRF=<?= json_encode($csrf) ?>;
const $=s=>document.querySelector(s);
const $$=s=>document.querySelectorAll(s);
let IS_ADMIN=false, WAITING=false, WAIT_ID=null;
function showMsg(el,text,ok=false){el.className='msg '+(ok?'ok':'err');el.textContent=text;if(ok)setTimeout(()=>el.className='msg',5000)}
async function api(action,data={}){
  const fd=new FormData();fd.append('action',action);fd.append('csrf',CSRF);
  for(const[k,v] of Object.entries(data)) fd.append(k,v);
  try{
    const r=await fetch('api.php',{method:'POST',body:fd,credentials:'same-origin',cache:'no-store'});
    const text=await r.text();
    try{return JSON.parse(text)}catch{return{ok:false,msg:'Respuesta inválida'}}
  }catch(e){return{ok:false,msg:'Sin conexión'}}
}
function showLoader(msg,pct){
  $('#loader').classList.remove('hidden');
  if(msg) $('#loader-msg').textContent=msg;
  const p=Math.max(0,Math.min(100,pct||0));
  $('#loader-bar').style.width=p+'%';
  $('#loader-pct').textContent=p+'%';
}
function hideLoader(){ $('#loader').classList.add('hidden'); WAITING=false; WAIT_ID=null; }
$$('.tab').forEach(t=>t.onclick=()=>{$$('.tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');const login=t.dataset.t==='login';$('#f-login').classList.toggle('hidden',!login);$('#f-reg').classList.toggle('hidden',login)});
$('#btn-login').onclick=async()=>{const b=$('#btn-login');b.disabled=true;b.textContent='Entrando...';const res=await api('login',{username:$('#l-user').value.trim(),password:$('#l-pass').value});b.disabled=false;b.textContent='Entrar';if(!res.ok)return showMsg($('#m-login'),res.msg||'Error');location.reload()};
$('#btn-reg').onclick=async()=>{const b=$('#btn-reg');b.disabled=true;b.textContent='Creando...';const res=await api('register',{username:$('#r-user').value.trim(),password:$('#r-pass').value,password2:$('#r-pass2').value});b.disabled=false;b.textContent='Crear cuenta';if(!res.ok)return showMsg($('#m-reg'),res.msg||'Error');showMsg($('#m-reg'),res.msg,true);setTimeout(()=>$$('.tab')[0].click(),1100)};
$('#btn-logout').onclick=async()=>{await api('logout');location.reload()};
$('#btn-launch').onclick=()=>{
  const guild=$('#guild').value.trim();
  if(!guild||guild.length<3) return showMsg($('#m-launch'),'Guild ID inválido');
  $('#confirm-text').textContent=`¿Crear 4 cuentas NUEVAS en ${$('#region').value}, unirlas al clan ${guild} y correrlas 8 horas por 1 crédito?`;
  $('#confirm-modal').classList.remove('hidden');
};
$('#confirm-no').onclick=()=>$('#confirm-modal').classList.add('hidden');
$('#confirm-yes').onclick=async()=>{
  $('#confirm-modal').classList.add('hidden');
  const b=$('#btn-launch');b.disabled=true;b.textContent='Lanzando...';
  const res=await api('launch',{region:$('#region').value,guild:$('#guild').value.trim()});
  b.disabled=false;b.textContent='Lanzar · 1 crédito · 4 cuentas nuevas · 8h';
  if(!res.ok) return showMsg($('#m-launch'),res.msg||'Error');
  showMsg($('#m-launch'),res.msg,true);
  WAITING=true; WAIT_ID=res.queue_id||null;
  showLoader('Creando cuentas nuevas...', 8);
  refresh();
};
$('#btn-add').onclick=async()=>{const res=await api('admin_add',{username:$('#a-user').value.trim(),amount:$('#a-amount').value});if(!res.ok)return showMsg($('#m-admin'),res.msg||'Error');showMsg($('#m-admin'),res.msg,true);loadUsers();refresh()};
function applyJob(job){
  if(!WAITING||!job) return;
  const st=job.status||'';
  const stage=job.stage||'';
  const msg=job.msg||'Procesando...';
  let pct=parseInt(job.progress||0,10);
  if(st==='pending' && pct<5) pct=5;
  if(stage==='creating_account' && pct<10) pct=10;
  if(stage==='starting_workers' && pct<85) pct=85;
  if(stage==='ready' || (st==='running' && pct>=100) || st==='done'){
    showLoader(msg||'Listo', 100);
    setTimeout(()=>{ hideLoader(); showMsg($('#m-launch'),'Todo listo: cuentas creadas y bots en marcha',true); }, 700);
    return;
  }
  showLoader(msg, pct);
}
async function refresh(){
  const res=await api('status'); if(!res.ok) return;
  IS_ADMIN=!!res.admin;
  $('#u-name').textContent=res.user; $('#u-cred').textContent=res.credits;
  $('#admin-sys').classList.toggle('hidden',!IS_ADMIN);
  $('#admin-card').classList.toggle('hidden',!IS_ADMIN);
  if(IS_ADMIN){
    loadUsers();
    const eng=res.engine||{};
    const online=!!eng.online;
    $('#eng-dot').className='dot '+(online?'on':'off');
    $('#eng-text').textContent=online?('Motor online · '+(eng.mode||'ok')):'Motor offline';
    $('#eng-hint').textContent=online?(eng.msg||''):'Ejecuta: python app.py';
    $('#s-saved').textContent=res.saved_accounts||0;
    $('#s-mode').textContent=eng.mode||'—';
    $('#s-region').textContent=eng.region||'—';
    $('#s-bots').textContent=eng.workers||0;
    $('#s-guild').textContent=eng.guild||'—';
    $('#s-left').textContent=eng.left_min?eng.left_min+' min':'—';
  }
  if(res.launch){
    $('#u-region').textContent=res.launch.region;
    $('#u-bots').textContent=res.launch.bots;
    $('#u-guild').textContent=res.launch.guild;
    $('#u-left').textContent=res.launch.left_min+' min';
  } else {
    $('#u-region').textContent='—';$('#u-bots').textContent='0';$('#u-guild').textContent='—';$('#u-left').textContent='—';
  }
  applyJob(res.job);
}
async function loadUsers(){
  if(!IS_ADMIN) return;
  const res=await api('admin_list'); if(!res.ok) return;
  const box=$('#user-list'); box.innerHTML='';
  (res.users||[]).forEach(u=>{
    const d=document.createElement('div'); d.className='uitem';
    d.innerHTML='<span>'+u.username+' · <b style="color:var(--accent)">'+u.credits+'</b></span><button type="button">+5</button>';
    d.querySelector('button').onclick=async()=>{await api('admin_add',{username:u.username,amount:5});loadUsers();refresh()};
    box.appendChild(d);
  });
}
['l-user','l-pass'].forEach(id=>{const el=document.getElementById(id);if(el)el.addEventListener('keydown',e=>{if(e.key==='Enter')$('#btn-login').click()})});
if(!$('#auth').classList.contains('hidden')){} else {refresh();setInterval(refresh,2000)}
</script>
</body>
</html>
