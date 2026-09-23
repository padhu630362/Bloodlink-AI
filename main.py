
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3, os, re, math
from datetime import datetime
from typing import Optional

app = FastAPI(title="Intelligent Blood Emergency Response System")

DB = "blood_system.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS donors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, email TEXT, blood_group TEXT,
        city TEXT, available INTEGER DEFAULT 1, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT, phone TEXT, blood_group TEXT, component TEXT,
        units INTEGER, hospital TEXT, city TEXT, urgency TEXT,
        status TEXT DEFAULT 'OPEN', created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center TEXT, city TEXT, blood_group TEXT, component TEXT,
        units INTEGER, status TEXT
    );
    """)
    if cur.execute("SELECT COUNT(*) FROM donors").fetchone()[0] == 0:
        cur.executemany("""INSERT INTO donors(name,phone,email,blood_group,city,available,created_at)
        VALUES(?,?,?,?,?,?,?)""", [
            ("Demo Donor 1","9000000001","donor1@example.com","O+","Khammam",1,datetime.now().isoformat()),
            ("Demo Donor 2","9000000002","donor2@example.com","O-","Khammam",1,datetime.now().isoformat()),
            ("Demo Donor 3","9000000003","donor3@example.com","B+","Hyderabad",1,datetime.now().isoformat()),
            ("Demo Donor 4","9000000004","donor4@example.com","A+","Warangal",1,datetime.now().isoformat())
        ])
    if cur.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == 0:
        rows=[]
        centers=[("City Blood Centre","Khammam"),("District Hospital Blood Bank","Khammam"),
                 ("Apex Blood Centre","Hyderabad"),("Care Blood Bank","Warangal")]
        for center,city in centers:
            for bg,units in [("A+",32),("A-",8),("B+",45),("B-",7),("O+",58),("O-",11),("AB+",21),("AB-",5)]:
                status="Critical" if units<10 else ("Moderate" if units<25 else "Good")
                rows.append((center,city,bg,"Whole Blood",units,status))
        cur.executemany("INSERT INTO inventory(center,city,blood_group,component,units,status) VALUES(?,?,?,?,?,?)",rows)
    con.commit()
    con.close()

init_db()

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BloodLink AI — Intelligent Blood Emergency Response</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:#18212b;background:#fff}
a{text-decoration:none;color:inherit}.top{background:#8e1020;color:#fff;text-align:center;padding:9px;font-size:13px}
nav{height:72px;display:flex;align-items:center;justify-content:space-between;padding:0 7%;border-bottom:1px solid #eee;background:#fff;position:sticky;top:0;z-index:10}
.logo{display:flex;gap:10px;align-items:center;font-weight:800;font-size:21px;color:#8e1020}.drop{font-size:27px}
.navlinks{display:flex;gap:25px;font-size:14px;color:#49515b}.navlinks a:hover{color:#8e1020}
.btn{border:0;border-radius:9px;padding:12px 18px;font-weight:700;cursor:pointer}.primary{background:#b5122a;color:#fff}.outline{background:#fff;border:1px solid #d9b8bd;color:#8e1020}
.hero{background:linear-gradient(120deg,#fff5f6 0%,#fff 55%,#fff0f2 100%);padding:65px 7% 50px;display:grid;grid-template-columns:1.15fr .85fr;gap:45px;align-items:center}
.badge{display:inline-block;background:#ffe2e6;color:#94152a;padding:7px 11px;border-radius:30px;font-size:12px;font-weight:800}
h1{font-size:52px;line-height:1.04;margin:18px 0 15px;letter-spacing:-1.7px}.hero p{font-size:17px;line-height:1.65;color:#5f6873;max-width:650px}
.actions{display:flex;gap:12px;margin:25px 0}.stats{display:flex;gap:28px;margin-top:25px}.stat b{display:block;font-size:22px}.stat span{font-size:12px;color:#737b84}
.hero-card{background:#fff;border:1px solid #f0d7db;border-radius:22px;padding:24px;box-shadow:0 18px 55px #7c12201a}
.live{display:flex;justify-content:space-between;align-items:center}.live strong{color:#16854a;font-size:12px}.searchbox{margin-top:18px;background:#fafafa;border:1px solid #eee;border-radius:15px;padding:16px}
select,input{width:100%;padding:12px;border:1px solid #dfe3e7;border-radius:8px;background:#fff;font-size:14px}label{font-size:12px;color:#66707a;font-weight:700;display:block;margin:9px 0 6px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.section{padding:58px 7%}.section.alt{background:#fafafa}.section h2{font-size:32px;margin:0 0 8px}.muted{color:#69727d}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.card{border:1px solid #eceff1;border-radius:16px;padding:22px;background:#fff;box-shadow:0 6px 20px #11111108}.card h3{margin:9px 0}.icon{font-size:27px}.mini{font-size:13px;color:#6d7580;line-height:1.55}
.emergency{background:#8e1020;color:#fff;border-radius:22px;padding:35px;display:grid;grid-template-columns:1fr 1fr;gap:30px}.emergency .muted{color:#f6dfe2}.formgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.panel{border:1px solid #eceff1;border-radius:16px;background:#fff;padding:20px}.table{width:100%;border-collapse:collapse;font-size:13px}.table th,.table td{text-align:left;padding:11px;border-bottom:1px solid #eee}.pill{padding:5px 8px;border-radius:20px;font-size:11px;font-weight:800}.good{background:#e4f7eb;color:#187744}.moderate{background:#fff3d7;color:#966b00}.critical{background:#ffe3e6;color:#a40f28}
.ai{display:grid;grid-template-columns:1fr 1fr;gap:22px}.answer{background:#f8f9fa;border-radius:12px;padding:14px;min-height:65px;color:#4f5964;white-space:pre-wrap}
footer{background:#15191e;color:#d7dbe0;padding:40px 7%;margin-top:30px}.foot{display:flex;justify-content:space-between;gap:20px}
@media(max-width:850px){.hero,.emergency,.ai{grid-template-columns:1fr}.cards{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}.navlinks{display:none}h1{font-size:39px}}
</style>
</head>
<body>
<div class="top">Emergency blood coordination • Prototype / educational demonstration</div>
<nav>
<div class="logo"><span class="drop">🩸</span>BloodLink AI</div>
<div class="navlinks"><a href="#search">Find Blood</a><a href="#donate">Donate</a><a href="#emergency">Emergency</a><a href="#dashboard">Dashboard</a><a href="#ai">AI + RAG</a></div>
<button class="btn primary" onclick="document.getElementById('donate').scrollIntoView()">Register Donor</button>
</nav>

<section class="hero">
<div>
<span class="badge">INTELLIGENT BLOOD EMERGENCY RESPONSE</span>
<h1>Find lifesaving blood.<br><span style="color:#b5122a">Faster.</span></h1>
<p>A student-built digital platform connecting blood donors, patients, hospitals and blood centres through blood availability search, emergency requests, AI-assisted matching, forecasting and a local RAG knowledge assistant.</p>
<div class="actions"><button class="btn primary" onclick="document.getElementById('search').scrollIntoView()">Find Blood Now</button><button class="btn outline" onclick="document.getElementById('emergency').scrollIntoView()">Raise Emergency</button></div>
<div class="stats"><div class="stat"><b id="sBanks">4</b><span>Demo Centres</span></div><div class="stat"><b id="sDonors">4</b><span>Registered Donors</span></div><div class="stat"><b id="sUnits">0</b><span>Demo Units</span></div></div>
</div>
<div class="hero-card">
<div class="live"><b>Live Blood Availability</b><strong>● DEMO LIVE</strong></div>
<div class="searchbox">
<label>Blood Group</label><select id="heroBg"><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>O+</option><option>O-</option><option>AB+</option><option>AB-</option></select>
<label>City</label><input id="heroCity" placeholder="e.g. Khammam">
<button class="btn primary" style="width:100%;margin-top:12px" onclick="searchBlood()">Search Availability</button>
<div id="heroResult" class="mini" style="margin-top:12px"></div>
</div>
</div>
</section>

<section class="section" id="search">
<h2>Find blood when it matters most</h2><p class="muted">Search the prototype inventory by blood group, component and city.</p>
<div class="panel" style="margin-top:22px">
<div class="grid"><div><label>Blood Group</label><select id="bg"><option value="">All</option><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>O+</option><option>O-</option><option>AB+</option><option>AB-</option></select></div>
<div><label>Component</label><select id="component"><option>Whole Blood</option><option>Platelets</option><option>Plasma</option></select></div>
<div><label>City</label><input id="city" placeholder="Khammam"></div>
<div style="display:flex;align-items:end"><button class="btn primary" style="width:100%" onclick="searchBloodTable()">Search</button></div></div>
<div id="searchResults" style="margin-top:20px"></div>
</div>
</section>

<section class="section alt">
<h2>One platform. Every stakeholder.</h2><p class="muted">Core workflows inspired by modern blood-network platforms, implemented as an original student prototype.</p>
<div class="cards">
<div class="card"><div class="icon">🩸</div><h3>Blood Donor</h3><p class="mini">Register donor details, blood group, city and availability for emergency matching.</p></div>
<div class="card"><div class="icon">🏥</div><h3>Hospital Staff</h3><p class="mini">Raise emergency requests and view inventory across connected demo centres.</p></div>
<div class="card"><div class="icon">📊</div><h3>Blood Centre</h3><p class="mini">Monitor stock levels and identify critical inventory requiring attention.</p></div>
</div>
</section>

<section class="section" id="emergency">
<div class="emergency">
<div><span class="badge">EMERGENCY REQUEST</span><h2 style="font-size:35px;margin-bottom:8px">Need blood urgently?</h2><p class="muted">Submit a request to create a coordination record in the prototype.</p><p class="mini" style="color:#f6dfe2">The demo does not contact real donors or hospitals.</p></div>
<div class="formgrid">
<div><label style="color:#f4dadd">Patient / Case</label><input id="patient" placeholder="Patient name"></div>
<div><label style="color:#f4dadd">Contact</label><input id="phone" placeholder="10-digit number"></div>
<div><label style="color:#f4dadd">Blood Group</label><select id="ebg"><option>O+</option><option>O-</option><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>AB+</option><option>AB-</option></select></div>
<div><label style="color:#f4dadd">Units</label><input id="units" type="number" min="1" value="1"></div>
<div><label style="color:#f4dadd">Hospital</label><input id="hospital" placeholder="Hospital name"></div>
<div><label style="color:#f4dadd">City</label><input id="ecity" placeholder="Khammam"></div>
<div><label style="color:#f4dadd">Urgency</label><select id="urgency"><option>Critical</option><option>High</option><option>Moderate</option></select></div>
<div style="display:flex;align-items:end"><button class="btn" style="width:100%;background:#fff;color:#8e1020" onclick="submitEmergency()">Submit Request</button></div>
</div>
</div><div id="emResult" style="margin-top:15px"></div>
</section>

<section class="section" id="donate">
<h2>Register as a voluntary donor</h2><p class="muted">Demo registration form. Actual donation eligibility must be assessed by qualified medical professionals.</p>
<div class="panel" style="margin-top:22px">
<div class="grid"><div><label>Name</label><input id="dname" placeholder="Full name"></div><div><label>Mobile</label><input id="dphone" placeholder="Mobile number"></div><div><label>Email</label><input id="demail" placeholder="Optional"></div><div><label>Blood Group</label><select id="dbg"><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>O+</option><option>O-</option><option>AB+</option><option>AB-</option></select></div><div><label>City</label><input id="dcity" placeholder="Khammam"></div><div style="display:flex;align-items:end"><button class="btn primary" style="width:100%" onclick="registerDonor()">Register Donor</button></div></div>
<div id="donorResult" class="mini" style="margin-top:14px"></div>
</div>
</section>

<section class="section alt" id="dashboard">
<h2>Live dashboard</h2><p class="muted">Prototype analytics and inventory view.</p>
<div class="cards">
<div class="card"><div class="icon">📦</div><h3 id="dashUnits">0</h3><p class="mini">Total demo units</p></div>
<div class="card"><div class="icon">👥</div><h3 id="dashDonors">0</h3><p class="mini">Registered donors</p></div>
<div class="card"><div class="icon">🚨</div><h3 id="dashRequests">0</h3><p class="mini">Emergency requests</p></div>
</div>
<div class="panel" style="margin-top:22px"><h3>Current Inventory</h3><div id="inventoryTable"></div></div>
</section>

<section class="section" id="ai">
<h2>AI + RAG intelligence</h2><p class="muted">Educational demonstrations of machine-learning style matching, demand forecasting and retrieval-augmented answers.</p>
<div class="ai" style="margin-top:22px">
<div class="panel"><h3>🤖 AI Donor Matching</h3><p class="mini">Ranks demo donors using blood-group compatibility, city proximity and availability.</p>
<div class="grid" style="grid-template-columns:1fr 1fr"><div><label>Required Group</label><select id="matchBg"><option>O+</option><option>O-</option><option>A+</option><option>B+</option><option>AB+</option></select></div><div><label>City</label><input id="matchCity" value="Khammam"></div></div>
<button class="btn primary" style="margin-top:12px" onclick="matchDonors()">Find Matches</button><div id="matchResult" class="mini" style="margin-top:12px"></div></div>
<div class="panel"><h3>📚 RAG Assistant</h3><p class="mini">Ask a question about the prototype's stored blood-donation knowledge base.</p>
<input id="ragQ" placeholder="Example: What is blood availability search?"><button class="btn primary" style="margin-top:12px" onclick="askRag()">Ask Assistant</button><div id="ragA" class="answer" style="margin-top:12px">Your answer will appear here.</div></div>
</div>
</section>

<footer><div class="foot"><div><div class="logo" style="color:#fff">💧 BloodLink AI</div><p class="mini" style="color:#aeb6bf;max-width:520px">Intelligent Blood Emergency Response System — original student prototype for demonstration of web, database, AI/ML and RAG concepts.</p></div><div class="mini" style="color:#aeb6bf">Prototype only • Not a medical decision system</div></div></footer>

<script>
async function api(url, opts={}){const r=await fetch(url,opts);return await r.json()}
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
async function searchBlood(){
 const bg=document.getElementById('heroBg').value, city=document.getElementById('heroCity').value;
 const d=await api(`/api/inventory?blood_group=${encodeURIComponent(bg)}&city=${encodeURIComponent(city)}`);
 document.getElementById('heroResult').innerHTML=d.length?`<b>${d.reduce((a,x)=>a+x.units,0)} units</b> found across ${d.length} centre(s). Scroll down for details.`:'No demo stock found for that search.';
}
async function searchBloodTable(){
 const bg=document.getElementById('bg').value, city=document.getElementById('city').value, comp=document.getElementById('component').value;
 const d=await api(`/api/inventory?blood_group=${encodeURIComponent(bg)}&city=${encodeURIComponent(city)}&component=${encodeURIComponent(comp)}`);
 document.getElementById('searchResults').innerHTML=d.length?`<table class="table"><tr><th>Centre</th><th>City</th><th>Group</th><th>Component</th><th>Units</th><th>Status</th></tr>${d.map(x=>`<tr><td>${esc(x.center)}</td><td>${esc(x.city)}</td><td><b>${esc(x.blood_group)}</b></td><td>${esc(x.component)}</td><td>${x.units}</td><td><span class="pill ${x.status.toLowerCase()}">${x.status}</span></td></tr>`).join('')}</table>`:'No matching demo inventory found.';
}
async function submitEmergency(){
 const body=new URLSearchParams({patient:patient.value,phone:phone.value,blood_group:ebg.value,units:units.value,hospital:hospital.value,city:ecity.value,urgency:urgency.value});
 const d=await api('/api/emergency',{method:'POST',body});
 emResult.innerHTML=`<div class="panel"><b>Request #${d.id} created.</b> Status: ${d.status}. AI matching can now be demonstrated below.</div>`;
 loadDash();
}
async function registerDonor(){
 const body=new URLSearchParams({name:dname.value,phone:dphone.value,email:demail.value,blood_group:dbg.value,city:dcity.value});
 const d=await api('/api/donor',{method:'POST',body});
 donorResult.innerHTML=`Registered <b>${esc(d.name)}</b> (${d.blood_group}) successfully in the demo database.`;
 loadDash();
}
async function matchDonors(){
 const d=await api(`/api/match?blood_group=${encodeURIComponent(matchBg.value)}&city=${encodeURIComponent(matchCity.value)}`);
 matchResult.innerHTML=d.length?d.map((x,i)=>`<div style="padding:9px 0;border-bottom:1px solid #eee"><b>#${i+1} ${esc(x.name)}</b> — ${x.blood_group}, ${esc(x.city)} — Match score <b>${x.score}</b>/100</div>`).join(''):'No compatible demo donors found.';
}
async function askRag(){
 const d=await api('/api/rag',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:ragQ.value})});
 ragA.textContent=d.answer;
}
async function loadDash(){
 const d=await api('/api/dashboard');
 sBanks.textContent=d.centres;sDonors.textContent=d.donors;sUnits.textContent=d.units;
 dashUnits.textContent=d.units;dashDonors.textContent=d.donors;dashRequests.textContent=d.requests;
 inventoryTable.innerHTML=`<table class="table"><tr><th>Blood Group</th><th>Units</th><th>Status</th></tr>${d.summary.map(x=>`<tr><td><b>${x.blood_group}</b></td><td>${x.units}</td><td><span class="pill ${x.status.toLowerCase()}">${x.status}</span></td></tr>`).join('')}</table>`;
}
loadDash();
</script>
</body></html>"""

RAG = {
"availability":"Blood availability search lets a user filter demo inventory by blood group, component and city and view available units at connected centres.",
"donor":"The donor module stores a donor's name, contact, blood group, city and availability for prototype matching.",
"emergency":"An emergency request records patient or case information, required blood group, units, hospital, city and urgency.",
"ai":"The AI matching demonstration ranks compatible demo donors using blood-group compatibility, availability and location-related scoring.",
"rag":"RAG means Retrieval-Augmented Generation. In this prototype, a small local knowledge base is searched first and the most relevant stored information is returned.",
"forecast":"Demand forecasting can be implemented with historical inventory/request data and a machine-learning regression model. This prototype keeps the dashboard local and educational.",
"eligibility":"Blood donation eligibility must be assessed by qualified medical professionals. The prototype should not be used to decide whether someone can donate."
}

@app.get("/", response_class=HTMLResponse)
def home(): return PAGE

@app.get("/api/health")
def health(): return {"status":"ok"}

@app.get("/api/inventory")
def inventory(blood_group: str="", city: str="", component: str=""):
    con=db()
    q="SELECT * FROM inventory WHERE 1=1"; args=[]
    if blood_group: q+=" AND blood_group=?"; args.append(blood_group)
    if city: q+=" AND lower(city)=lower(?)"; args.append(city.strip())
    if component: q+=" AND component=?"; args.append(component)
    rows=[dict(x) for x in con.execute(q,args).fetchall()]; con.close(); return rows

@app.post("/api/donor")
def donor(name:str=Form(...),phone:str=Form(...),email:str=Form(""),blood_group:str=Form(...),city:str=Form(...)):
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO donors(name,phone,email,blood_group,city,available,created_at) VALUES(?,?,?,?,?,?,?)",
                (name,phone,email,blood_group,city,1,datetime.now().isoformat()))
    con.commit(); ident=cur.lastrowid; con.close()
    return {"id":ident,"name":name,"blood_group":blood_group}

@app.post("/api/emergency")
def emergency(patient:str=Form(...),phone:str=Form(...),blood_group:str=Form(...),units:int=Form(...),hospital:str=Form(...),city:str=Form(...),urgency:str=Form(...)):
    con=db(); cur=con.cursor()
    cur.execute("""INSERT INTO requests(patient,phone,blood_group,component,units,hospital,city,urgency,status,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (patient,phone,blood_group,"Whole Blood",units,hospital,city,urgency,"OPEN",datetime.now().isoformat()))
    con.commit(); ident=cur.lastrowid; con.close()
    return {"id":ident,"status":"OPEN"}

@app.get("/api/match")
def match(blood_group:str,city:str=""):
    con=db(); rows=[dict(x) for x in con.execute("SELECT * FROM donors WHERE available=1").fetchall()]; con.close()
    compatible={"O-":{"O-"},"O+":{"O-","O+"},"A-":{"O-","A-"},"A+":{"O-","O+","A-","A+"},
                "B-":{"O-","B-"},"B+":{"O-","O+","B-","B+"},"AB-":{"O-","A-","B-","AB-"},
                "AB+":{"O-","O+","A-","A+","B-","B+","AB-","AB+"}}
    allowed=compatible.get(blood_group,{blood_group}); out=[]
    for r in rows:
        if r["blood_group"] not in allowed: continue
        score=55
        if r["blood_group"]==blood_group: score+=25
        if city and r["city"].strip().lower()==city.strip().lower(): score+=20
        out.append({"name":r["name"],"blood_group":r["blood_group"],"city":r["city"],"score":min(score,100)})
    return sorted(out,key=lambda x:x["score"],reverse=True)

@app.post("/api/rag")
def rag(payload:dict):
    q=str(payload.get("question","")).lower()
    best=None
    for k,v in RAG.items():
        words=set(re.findall(r"[a-z]+",q))
        score=sum(1 for w in words if w in v.lower() or w in k)
        if best is None or score>best[0]: best=(score,v)
    return {"answer":best[1] if best and best[0]>0 else "I can explain blood availability, donor registration, emergency requests, AI matching, RAG and prototype safety. Try asking one of these topics."}

@app.get("/api/dashboard")
def dashboard():
    con=db()
    donors=con.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
    requests=con.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    units=con.execute("SELECT COALESCE(SUM(units),0) FROM inventory").fetchone()[0]
    centres=con.execute("SELECT COUNT(DISTINCT center) FROM inventory").fetchone()[0]
    summary=[]
    for bg in ["A+","A-","B+","B-","O+","O-","AB+","AB-"]:
        u=con.execute("SELECT COALESCE(SUM(units),0) FROM inventory WHERE blood_group=?",(bg,)).fetchone()[0]
        status="Critical" if u<20 else ("Moderate" if u<50 else "Good")
        summary.append({"blood_group":bg,"units":u,"status":status})
    con.close()
    return {"donors":donors,"requests":requests,"units":units,"centres":centres,"summary":summary}
