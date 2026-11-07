# Copyright (c) 2026 Data market place. All rights reserved.
from flask import send_from_directory, Flask, request, redirect, render_template_string
import json, os, time
from datetime import datetime, timedelta
app = Flask(__name__)

def is_admin():
    from flask import session
    return session.get('is_admin') == True
app.config['SESSION_COOKIE_SECURE']=False
app.config['SESSION_COOKIE_SAMESITE']='Lax'
app.config['SESSION_COOKIE_HTTPONLY']=True
import os, secrets
app.secret_key = os.environ.get('SECRET_KEY', 'single-searching-stable-secret-12345')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'CHANGE-ME-NOW')

os.makedirs("static/uploads", exist_ok=True)
FILE = "data.json"
OWNER_NUMBER = "0751305288"
def load():
    if os.path.exists(FILE):
        try:
            with open(FILE) as f: return json.load(f).get("jobs", [])
        except: return []
    return []
def save(jobs):
    with open(FILE, "w") as f: json.dump({"jobs": jobs}, f)
jobs = load()
pending = {}
waiting = {}  # waiting for admin approval

PAY_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pay to Post</title>
<style>body{font-family:Arial;background:#F5F5F5;margin:0}.header{background:#FF6B00;color:#fff;padding:20px;text-align:center}.card{background:#fff;margin:15px;border-radius:14px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}input{width:100%;padding:14px;border:1px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box}button{width:100%;padding:15px;background:#FF6B00;color:#fff;border:none;border-radius:10px;font-size:17px;font-weight:bold}.momo{display:flex;gap:10px}.momo div{flex:1;text-align:center;padding:14px;border:2px solid #eee;border-radius:10px;font-weight:bold;cursor:pointer}.momo div.on{border-color:#FF6B00;background:#FF6B00;color:#fff}.box{background:#FF3E6;border:1px dashed #FF6B00;padding:12px;border-radius:10px;margin:10px 0}</style>
</head><body>
<div class="header"><h2>{{reason}}</h2><p>{{summary|safe}}</p></div>
<div class="card">
<div class="box"><b>Step 1:</b> Send <b>10000 UGX</b> to <b>0751305288</b><br>MTN: Dial <b>*165#</b> &nbsp; Airtel: Dial <b>*185#</b></div>
<form method="post" action="/pay_confirm">
<input type="hidden" name="key" value="{{key}}">
<label>Choose Network</label><br><br>
<div class="momo"><div onclick="sel(this,'MTN')">MTN MoMo</div><div onclick="sel(this,'Airtel')">Airtel Money</div></div>
<input type="hidden" name="network" id="net" value="MTN" required>
<br><label>Your MoMo Number</label><br><input name="momo_number" placeholder="e.g. 0771234567" required>
<br><br><label>Transaction ID from SMS</label><br><input name="txid" placeholder="e.g. 1234567890" required>
<br><br><button type="submit">I HAVE PAID - CONFIRM</button>
</form>
<br><a href="/" style="display:block;text-align:center;color:#777">← Back to Home</a>
</div>
<script>function sel(el,v){document.querySelectorAll('.momo div').forEach(d=>d.classList.remove('on'));el.classList.add('on');document.getElementById('net').value=v;}</script>
<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body></html>
"""

WAITING_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Waiting For Approval</title>
<style>body{font-family:Arial;background:#F5F5F5;margin:0}.header{background:#FF6B00;color:#fff;padding:20px;text-align:center}.card{background:#fff;margin:15px;border-radius:14px;padding:20px;text-align:center}</style>
</head><body>
<div class="header"><h2>Waiting For Approval</h2></div>
<div class="card">
<h2>Payment Received!</h2>
<p>We have received your payment. Admin will check and approve your advert.</p>
<p><b>Your Advert:</b><br>{{summary|safe}}</p>
<p><b>MoMo:</b> {{number}}<br><b>TxID:</b> {{txid}}<br><b>Network:</b> {{network}}</p>
<p>Usually approved in a few minutes.</p>
<a href="/"><button style="width:100%;padding:15px;background:#FF6B00;color:#fff;border:none;border-radius:10px;font-size:17px;font-weight:bold">BACK TO HOME</button></a>
</div>
<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body></html>
"""

ADMIN_HTML = """<div style="text-align:center;margin:15px 0;">
<a href="/" style="background:#ff6b00;color:white;padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:18px;display:inline-block;">🏠 Go to Unlocked Home</a>
<p style="color:white;font-size:13px;margin-top:8px;">You are still logged in - Home will be FREE + numbers visible</p>
</div>
<!DOCTYPE html><html><head><link rel="manifest" href="/static/manifest.json"><meta name="theme-color" content="#FF6B00"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Admin Approve</title>
<style>body{font-family:Arial;background:#F5F5F5;margin:0}.header{background:#222;color:#fff;padding:18px;text-align:center}.card{background:#fff;margin:12px;border-radius:14px;padding:15px}button{width:48%;padding:12px;border:none;border-radius:10px;font-weight:bold;color:#fff;font-size:15px}button.ap{background:#00802b}button.rj{background:#cc0000}</style></head><body>

<div class="header"><h2>Admin - Approve Payments</h2><p>Owner Only - Check your MoMo SMS for 0751305288</p></div>
{% for k,v in waiting.items() %}
<div class="card"><b>{{v['reason']}}</b><br>{{v['summary']|safe}}<br><br>From: <b>{{v['number']}}</b><br>TxID: <b>{{v['txid']}}</b><br>Network: {{v['network']}} - {{' *165#' if v['network']=='MTN' else ' *185#'}}<br>Amount: 10000 UGX to 0751305288<br><br>
<form method="post" action="/admin_action" style="display:flex;gap:8px"><input type="hidden" name="key" value="{{k}}"><button class="ap" name="action" value="approve">APPROVE ✅</button><button class="rj" name="action" value="reject">REJECT ❌</button></form></div>
{% else %}<div class="card"><p>No pending payments. All clear!</p></div>{% endfor %}
<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body></html>
"""

HTML = """
<!DOCTYPE html><html><head><link rel="manifest" href="/static/manifest.json"><meta name="theme-color" content="#FF6B00"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Digital Market Place</title>
<style>body{font-family:Arial;background:#F5F5F5;margin:0;color:#222}.header{background:#FF6B00;color:white;padding:18px 15px;text-align:center;position:sticky;top:0;z-index:10}.header h1{margin:0;font-size:24px}.card{background:white;margin:12px;border-radius:14px;padding:15px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}input,select,textarea{width:100%;padding:13px;margin:8px 0;border:1px solid #ddd;border-radius:10px;font-size:16px;box-sizing:border-box}textarea{height:80px}button{width:100%;padding:15px;background:#FF6B00;color:white;border:none;border-radius:10px;font-size:17px;font-weight:bold}button.green{background:#00802b}.cat span{background:#FFF3E6;border:1px solid #FF6B00;padding:8px 12px;border-radius:20px;font-size:14px;display:inline-block;margin:3px}.job{background:white;margin:12px;border-radius:14px;padding:15px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}.price{color:#FF6B00;font-weight:bold;font-size:18px}.small{color:#777;font-size:13px}.unlock{background:#FFF3E6;border:1px dashed #FF6B00;padding:10px;border-radius:10px;margin-top:10px;text-align:center}.job img{width:100%;border-radius:10px;margin-top:10px;max-height:320px;object-fit:cover}label{font-weight:bold;font-size:14px}.desc{background:#F9F9F9;padding:10px;border-radius:8px;margin-top:8px;font-size:15px;line-height:1.4}</style></head><body>

<div class="header"><h1>🛒 Digital Market Place</h1><p>Find Work • Find Workers • Daily</p></div>
<div class="card"><h3 style="margin:0;color:#FF6B00">Categories</h3><div class="cat" style="margin-top:10px"><span>Boda</span><span>Plumber</span><span>Cleaner</span><span>DJ</span><span>Electrician</span><span>Cook</span><span>Phones</span><span>Shoes</span><span>Electronics</span><span>Others</span></div></div>
<div class="card"><h3 style="margin:0">+ POST ADVERT</h3>
<form method="post" action="/post" enctype="multipart/form-data">
<label>Title</label><input name="title" placeholder="e.g. iPhone 12 for sale / Need Plumber" required>
<label>Type</label><select name="cat" required><option>For Sale - Item</option><option>Need Worker / Job</option><option>Boda</option><option>Plumber</option><option>Cleaner</option><option>DJ</option><option>Electrician</option><option>Cook</option><option>Phones</option><option>Shoes / Clothes</option><option>Electronics</option><option>Other</option></select>
<label>Description</label><textarea name="desc" placeholder="Describe it..."></textarea>
<label>Price / Budget</label><input name="price" placeholder="e.g. 50000" required>
<label>Photo (for selling items - optional)</label><input type="file" name="photo" accept="image/*">
<label>Your Phone</label><input name="phone" placeholder="e.g. 0751305288" required>
<label>Location</label><input name="location" placeholder="e.g. Kampala, Ntinda" required>
<button>CONTINUE TO PAYMENT</button></form></div>
<div style="padding:0 12px"><h3>Latest Adverts ({{jobs|length}})</h3></div>
<div style="padding-bottom:40px">
{% for j in jobs|reverse %}
<div class="job"><b style="font-size:18px">{{j['title']}}</b><br><span class="small">{{j['cat']}} - {{j['location']}}</span>
{% if j.get('photo') %}<img src="/static/uploads/{{j['photo']}}">{% endif %}
{% if j.get('desc') %}<div class="desc">{{j['desc']}}</div>{% endif %}
<br><span class="price">Price: {{j['price']}} UGX</span>
<form method="post" action="/unlock"><input type="hidden" name="id" value="{{loop.index0}}">
{% if j.get('unlocked') %}<div class="unlock">Contact: <b>{{j['phone']}}</b></div>
{% else %}<button class="green" style="margin-top:10px">UNLOCK CONTACT</button>{% endif %}</form></div>
{% else %}<div class="job"><p>No adverts yet. Be the first to post!</p></div>{% endfor %}
<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body></html>
"""

@app.route("/sw.js")
def sw():
    js = """// SingleSearching - Self-Updating SW - v2
const VERSION = 'v8-FINAL-FIX';
const CACHE = 'singlesearching-' + VERSION;
self.addEventListener('install', (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(['/'])).then(() => self.skipWaiting())); });
self.addEventListener('activate', (e) => { e.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => { if (k !== CACHE) return caches.delete(k); }))).then(() => self.clients.claim())); });
self.addEventListener('fetch', (e) => {
  if (e.request.mode === 'navigate' || e.request.url.includes('/admin') || e.request.url.includes('/api')) {
    e.respondWith(fetch(e.request).then((res) => { const copy=res.clone(); caches.open(CACHE).then((c)=>c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then((cached) => { const fp = fetch(e.request).then((res)=>{ const cp=res.clone(); caches.open(CACHE).then((c)=>c.put(e.request, cp)); return res; }).catch(()=>cached); return cached || fp; }));
});
self.addEventListener('message', (e) => { if (e.data === 'SKIP_WAITING') self.skipWaiting(); });
"""
    from flask import Response
    r = Response(js, mimetype='application/javascript')
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Service-Worker-Allowed'] = '/'
    return r


# --- 30 DAY EXPIRY ---
def is_expired_30d(job):
    try:
        at = job.get('approved_at')
        if not at:
            return False
        dt = datetime.fromisoformat(str(at).replace('Z',''))
        return datetime.now() > dt + timedelta(days=30)
    except:
        return False
# --- END EXPIRY ---

@app.route("/")
def home():
    global jobs
    # Auto-remove adverts older than 30 days from approval
    fresh = [j for j in jobs if not is_expired_30d(j)]
    if len(fresh) != len(jobs):
        print(f"Expired: removed {len(jobs)-len(fresh)} adverts")
        jobs = fresh
        save(jobs)
    # OWNER MODE: if YOU are logged in, show all numbers - display copy only, don't save
    jobs_to_show = jobs
    try:
        if session.get('is_admin'):
            import copy as _copy
            jobs_to_show = _copy.deepcopy(jobs)
            for _j in jobs_to_show:
                _j['unlocked'] = True
    except: pass
    return render_template_string(HTML, jobs=jobs_to_show, is_admin=session.get('is_admin'))
@app.route("/post", methods=["POST"])
def post():
    from flask import session
    # OWNER BYPASS: owner posts free, auto-approved
    _owner = session.get('is_admin') == True
    # OWNER POST FREE
    _is_owner_post = _owner
    from flask import session
    # ADMIN IS FREE - no payment, post directly
    if session.get('is_admin'):
        from flask import redirect
        import json as _json, time as _time, os as _os
        d = _load() if '_load' in globals() else {'jobs': []}
        # get form data
        f = request.form
        new_job = {
            'title': f.get('title',''),
            'cat': f.get('cat',''),
            'desc': f.get('desc',''),
            'price': f.get('price',''),
            'phone': f.get('phone',''),
            'location': f.get('location',''),
            'approved_at': _time.strftime('%Y-%m-%dT%H:%M:%S'),
            'by_admin': True
        }
        d.setdefault('jobs', []).append(new_job)
        # save - try both save funcs
        try:
            _save(d)
        except:
            open('data.json','w').write(_json.dumps(d))
        return redirect('/admin')
    photo_name = ""
    f = request.files.get("photo")
    if f and f.filename:
        photo_name = str(int(time.time())) + "_" + f.filename.replace(" ", "_")
        f.save(os.path.join("static/uploads", photo_name))
    key = str(int(time.time()))
    pending[key] = {"type": "post", "data": {"title": request.form["title"], "cat": request.form["cat"], "desc": request.form.get("desc",""), "price": request.form["price"], "phone": request.form["phone"], "location": request.form["location"], "photo": photo_name, "unlocked": True if session.get('is_admin') else False}}
    summary = f"<b>{request.form['title']}</b><br>{request.form['cat']} - {request.form['location']}<br>Price: {request.form['price']} UGX"
    return render_template_string(PAY_HTML, reason="Pay to Post Your Advert", summary=summary, key=key)
@app.route("/unlock", methods=["POST"])
def unlock():
    idx = int(request.form["id"]); real = len(jobs)-1-idx
    key = str(int(time.time())) + "_unlock"
    pending[key] = {"type": "unlock", "idx": real}
    j = jobs[real]
    summary = f"<b>{j['title']}</b><br>{j['cat']} - {j['location']}<br>Price: {j['price']} UGX"
    return render_template_string(PAY_HTML, reason="Pay to Unlock Contact", summary=summary, key=key)
@app.route("/pay_confirm", methods=["POST"])
def pay_confirm():
    key = request.form["key"]; number = request.form["momo_number"]; txid = request.form["txid"]; net = request.form["network"]
    if key in pending:
        p = pending.pop(key)
        p["number"] = number; p["txid"] = txid; p["network"] = net
        p["reason"] = "POST ADVERT" if p["type"]=="post" else "UNLOCK CONTACT"
        if p["type"]=="post": p["summary"] = f"<b>{p['data']['title']}</b><br>{p['data']['cat']} - {p['data']['location']}<br>Price: {p['data']['price']} UGX"
        else: j=jobs[p["idx"]]; p["summary"] = f"<b>{j['title']}</b><br>{j['cat']} - {j['location']}<br>Price: {j['price']} UGX"
        waiting[key] = p
        return render_template_string(WAITING_HTML, number=number, txid=txid, network=net)
    return redirect("/")

@app.route("/admin")
def admin_protected():
    return render_template_string(ADMIN_HTML, waiting=waiting)
# OLD_ADMIN_START

@app.route("/admin_action", methods=["POST"])
def admin_action():
    if not session.get('is_admin'):
        return redirect('/admin-login')
    key = request.form["key"]; action = request.form["action"]
    if key in waiting:
        p = waiting.pop(key)
        if action == "approve":
            if p["type"] == "post": p["data"]["approved_at"] = datetime.now().isoformat(); jobs.append(p["data"]); save(jobs)
            elif p["type"] == "unlock": jobs[p["idx"]]["unlocked"] = True; save(jobs)
    return redirect("/admin")



from flask import session, redirect, request
@app.route('/admin-login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin']=True
            return redirect('/admin')
    return '<div style="max-width:400px;margin:60px auto;padding:20px;"><h2>Admin Login</h2><form method="POST"><input name="password" type="password" placeholder="Enter Admin Password" required style="width:100%;padding:14px;border-radius:8px;"><button style="width:100%;padding:14px;background:#FF6B00;color:white;border:none;border-radius:8px;margin-top:10px;">LOGIN</button></form></div>'
@app.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect('/')
@app.before_request
def protect_admin():
    p = request.path
    if p.startswith('/admin') and p not in ('/admin-login', '/admin-logout'):
        if not session.get('is_admin'):
            return redirect('/admin-login')





# --- VISIBLE LOGIN BUTTON - injected by server ---
LOGIN_BTN = '<div style="text-align:center!important;padding:30px 0 40px 0!important;margin-top:20px!important;border-top:1px solid #eee!important"><a href="/admin-login" style="display:inline-block!important;background:#111!important;color:white!important;padding:12px 32px!important;border-radius:25px!important;font-weight:700!important;font-size:15px!important;text-decoration:none!important;font-family:sans-serif">Login</a></div>'

@app.after_request
def inject_login_button(resp):
    try:
        # FIX: Login button ONLY on home page "/"
        # Never on /post, /pay_confirm, /unlock, /admin-login, payment pages
        from flask import request
        if request.path != "/":
            return resp
        if resp.content_type and 'text/html' not in resp.content_type:
            return resp
        data = resp.get_data(as_text=True)
        if 'admin-login' not in data:
            if '<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body>' in data:
                data = data.replace('<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body>', LOGIN_BTN + '<div style="text-align:center;padding:15px;font-size:13px;color:#666;border-top:1px solid #eee;margin-top:20px;">Copyright (c) 2026 Data market place. All rights reserved.</div></body>', 1)
            elif '</html>' in data:
                data = data.replace('</html>', LOGIN_BTN + '</html>', 1)
            else:
                data = data + LOGIN_BTN
            resp.set_data(data)
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    except Exception as e:
        print("inject error", e)
    return resp
# --- END LOGIN BUTTON ---

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

@app.route('/delete/<int:idx>', methods=['POST'])
def delete_post(idx):
    from flask import session, redirect
    if not session.get('is_admin'):
        return redirect('/admin-login')
    d = _load() if '_load' in globals() else {'jobs': []}
    jobs = d.get('jobs', [])
    if 0 <= idx < len(jobs):
        jobs.pop(idx)
        try:
            _save(d)
        except:
            import json as _j; open('data.json','w').write(_j.dumps(d))
    return redirect('/admin')
