import os, sqlite3, uuid, json, re, urllib.parse, urllib.request
from datetime import datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template, flash, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from journey_engine import JourneyIntelligenceEngine
from knowledge_engine import KnowledgeIngestionEngine
BASE=os.path.dirname(__file__)
# Vercel's deployment filesystem is read-only; runtime writes must use /tmp.
RUNTIME_DIR=os.path.join('/tmp','hdvia')
DB=os.path.join(RUNTIME_DIR,"data","hdvia.db")
UPLOAD=os.path.join(RUNTIME_DIR,"private_uploads")
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(UPLOAD,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get("HDVIA_SECRET_KEY","change-me-in-production")
app.config.update(MAX_CONTENT_LENGTH=5*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
if os.environ.get("HDVIA_COOKIE_SECURE","0")=="1": app.config["SESSION_COOKIE_SECURE"]=True
PERMISSIONS={
"USER":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","ai.assistant.use"},
"GUIDE":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","itinerary.optimize","ai.assistant.use","ai.copilot.use","knowledge.create","knowledge.read","knowledge.media.publish","knowledge.source.collect"},
"PARTNER":{"profile.manage","journey.read","destination.read"},
"ADMIN":{"profile.manage","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","user.manage","guide.approve","permission.manage","security.manage","audit.read"},
"SUPER_ADMIN":{"*"}}
def now(): return datetime.utcnow().isoformat(timespec="seconds")+"Z"
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    c=db(); c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'USER',trust_level TEXT NOT NULL DEFAULT 'L1',status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS guide_applications(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,card_number TEXT NOT NULL,card_type TEXT NOT NULL,card_image TEXT NOT NULL,area TEXT,languages TEXT,status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',admin_note TEXT,reviewed_by INTEGER,reviewed_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id INTEGER,action TEXT NOT NULL,target_type TEXT,target_id INTEGER,detail TEXT,ip TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS journeys(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,title TEXT NOT NULL,itinerary TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_items(id INTEGER PRIMARY KEY AUTOINCREMENT,author_id INTEGER,title TEXT NOT NULL,content TEXT NOT NULL,content_type TEXT NOT NULL DEFAULT 'ARTICLE',destination TEXT,media_url TEXT,source_url TEXT,source_type TEXT NOT NULL DEFAULT 'HDV_VERIFIED',ai_summary TEXT,ai_facts_json TEXT,confidence TEXT NOT NULL DEFAULT 'medium',status TEXT NOT NULL DEFAULT 'PUBLISHED',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(author_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_sources(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER NOT NULL,source_url TEXT NOT NULL,source_name TEXT,source_type TEXT,source_status TEXT NOT NULL DEFAULT 'COLLECTED',raw_content TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id));
    CREATE TABLE IF NOT EXISTS knowledge_events(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER,actor_id INTEGER,event TEXT NOT NULL,detail TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id),FOREIGN KEY(actor_id) REFERENCES users(id));
    """)
    if not c.execute("SELECT id FROM users WHERE email=?",("admin@hdvia.local",)).fetchone():
        c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  ("HDVIA Admin","0000000000","admin@hdvia.local",generate_password_hash(os.environ.get("HDVIA_DEMO_ADMIN_PASSWORD","ChangeMe123!")),"ADMIN","L4","ACTIVE",now()))
    c.commit(); c.close()
def log(actor,action,target_type=None,target_id=None,detail=""):
    c=db(); c.execute("INSERT INTO audit_logs(actor_id,action,target_type,target_id,detail,ip,created_at) VALUES(?,?,?,?,?,?,?)",
                      (actor,action,target_type,target_id,detail,request.remote_addr if request else "",now())); c.commit(); c.close()
def current_user():
    uid=session.get("uid")
    if not uid:return None
    c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close(); return u
def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not current_user(): return redirect(url_for("login",next=request.path))
        return f(*a,**kw)
    return w
def role_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user()
            if not u or u["role"] not in roles:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def permission_required(permission):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user(); p=PERMISSIONS.get(u["role"],set()) if u else set()
            if not u:return redirect(url_for("login"))
            if "*" not in p and permission not in p:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def safe_next(n): return n if n and n.startswith("/") else url_for("profile")
@app.context_processor
def inject(): return {"user":current_user(),"version":"1.5.0-beta"}
@app.get("/")
def home(): return render_template("home.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        if not name or not phone or not email or len(pw)<8: flash("Vui lòng điền đủ thông tin và dùng mật khẩu tối thiểu 8 ký tự."); return redirect(url_for("register"))
        c=db()
        try:
            c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,phone,email,generate_password_hash(pw),"USER","L1","ACTIVE",now())); c.commit(); uid=c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()["id"]
        except sqlite3.IntegrityError: c.close(); flash("Email đã tồn tại."); return redirect(url_for("register"))
        c.close(); log(uid,"USER_REGISTERED","USER",uid); session["uid"]=uid; return redirect(url_for("profile"))
    return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
    nxt=request.args.get("next","")
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        c=db(); u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],pw): session["uid"]=u["id"]; log(u["id"],"LOGIN"); return redirect(safe_next(nxt))
        flash("Email hoặc mật khẩu không đúng.")
    return render_template("login.html",next=nxt)
@app.get("/logout")
def logout(): uid=session.get("uid"); session.clear(); log(uid,"LOGOUT") if uid else None; return redirect(url_for("home"))
@app.get("/profile")
@login_required
def profile():
    u=current_user(); c=db(); apps=c.execute("SELECT * FROM guide_applications WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); journeys=c.execute("SELECT id,title,created_at FROM journeys WHERE user_id=? ORDER BY id DESC LIMIT 10",(u["id"],)).fetchall(); c.close()
    return render_template("profile.html",u=u,apps=apps,journeys=journeys)
@app.route("/guide/apply",methods=["GET","POST"])
@login_required
def guide_apply():
    u=current_user()
    if request.method=="POST":
        card=request.form.get("card_number","").strip(); typ=request.form.get("card_type","").strip(); area=request.form.get("area","").strip(); langs=request.form.get("languages","").strip(); f=request.files.get("card_image")
        if not card or not typ or not f or not f.filename: flash("Cần mã thẻ, loại thẻ và ảnh thẻ HDV."); return redirect(url_for("guide_apply"))
        ext=os.path.splitext(secure_filename(f.filename))[1].lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): flash("Chỉ nhận JPG, PNG, WEBP."); return redirect(url_for("guide_apply"))
        filename=f"{uuid.uuid4().hex}{ext}"; f.save(os.path.join(UPLOAD,filename)); c=db(); cur=c.execute("INSERT INTO guide_applications(user_id,card_number,card_type,card_image,area,languages,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(u["id"],card,typ,filename,area,langs,"PENDING_REVIEW",now())); appid=cur.lastrowid; c.commit(); c.close(); log(u["id"],"GUIDE_APPLICATION_SUBMITTED","GUIDE_APPLICATION",appid); flash("Đã gửi hồ sơ. Trạng thái: PENDING_REVIEW."); return redirect(url_for("profile"))
    return render_template("guide_apply.html")
@app.route("/journey",methods=["GET","POST"])
@login_required
@permission_required("journey.analyze")
def journey():
    result=None
    if request.method=="POST":
        title=request.form.get("title","Hành trình mới").strip(); itinerary=request.form.get("itinerary","").strip(); result=engine.analyze(title,itinerary)
        c=db(); c.execute("INSERT INTO journeys(user_id,title,itinerary,result_json,created_at) VALUES(?,?,?,?,?,?)",(current_user()["id"],title,itinerary,json.dumps(result,ensure_ascii=False),now())); c.commit(); c.close(); log(current_user()["id"],"JOURNEY_ANALYZED","JOURNEY",None,title)
    return render_template("journey.html",result=result)
@app.post("/api/v1/journey/analyze")
@login_required
@permission_required("journey.analyze")
def journey_api():
    data=request.get_json(silent=True) or {}; result=engine.analyze(data.get("title","Hành trình mới"),data.get("itinerary","")); log(current_user()["id"],"JOURNEY_ANALYZED_API","JOURNEY",None,result.get("title","")); return jsonify(result)
@app.get("/api/v1/weather")
def weather_api():
    name=request.args.get("name","").strip(); lat=request.args.get("lat"); lon=request.args.get("lon")
    if not lat or not lon:
        p=engine.detect_places(name)
        if not p:return jsonify({"error":"Không nhận diện được địa điểm"}),404
        lat,lon=p[0]["lat"],p[0]["lon"]; name=p[0]["name"]
    p={"name":name,"lat":float(lat),"lon":float(lon)}
    return jsonify({"place":p,"weather":engine.weather_provider(p),"updated_at":now()})
@app.get("/api/v1/place-image")
def place_image_api():
    name=request.args.get("name","").strip()
    if not name:return jsonify({"error":"missing name"}),400
    try:
        q=urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrsearch":name+" Vietnam","gsrnamespace":6,"gsrlimit":1,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1000})
        req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+q,headers={"User-Agent":"HDVIA/1.4 Travel Intelligence"})
        with urllib.request.urlopen(req,timeout=8) as r: data=json.loads(r.read().decode("utf-8"))
        pages=data.get("query",{}).get("pages",{})
        for page in pages.values():
            info=page.get("imageinfo",[{}])[0]; return jsonify({"name":name,"image_url":info.get("thumburl") or info.get("url"),"title":page.get("title"),"source":"Wikimedia Commons"})
    except Exception as e:
        return jsonify({"name":name,"image_url":None,"source":"fallback","error":"image provider unavailable"})
    return jsonify({"name":name,"image_url":None,"source":"none"})
@app.get("/api/v1/route")
def route_api():
    names=[x.strip() for x in request.args.get("places","").split(",") if x.strip()]; points=[]
    for n in names:
        p=engine.detect_places(n)
        if p: points.append(p[0])
    return jsonify({"points":points,"total_km":round(sum(__import__('journey_engine').haversine_km(points[i],points[i+1]) for i in range(len(points)-1)),1) if len(points)>1 else 0})
@app.get("/health")
def health(): return jsonify({"status":"ok","service":"HDVIA","version":"1.5.0-beta","knowledge_hub":"enabled","time":now()})
@app.get("/knowledge")
@login_required
@permission_required("knowledge.read")
def knowledge_hub():
    c=db(); rows=c.execute("SELECT k.*,u.name AS author_name FROM knowledge_items k LEFT JOIN users u ON u.id=k.author_id WHERE k.status='PUBLISHED' ORDER BY k.id DESC LIMIT 100").fetchall(); c.close()
    return render_template("knowledge.html", rows=rows)
@app.route("/knowledge/new", methods=["GET","POST"])
@login_required
@permission_required("knowledge.create")
def knowledge_new():
    if request.method=="POST":
        u=current_user(); title=request.form.get("title","").strip(); content=request.form.get("content","").strip(); destination=request.form.get("destination","").strip(); content_type=request.form.get("content_type","ARTICLE").strip(); media_url=request.form.get("media_url","").strip(); source_url=request.form.get("source_url","").strip()
        if not title or not content: flash("Cần tiêu đề và nội dung."); return redirect(url_for("knowledge_new"))
        ai=knowledge_engine.local_ai_extract(title,content)
        c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(u["id"],title,content,content_type,destination,media_url,source_url,"HDV_VERIFIED",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PUBLISHED",now(),now())); kid=cur.lastrowid
        if source_url: c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"User supplied","EXTERNAL","DECLARED","",now()))
        c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,u["id"],"PUBLISHED","Verified Guide contribution",now())); c.commit(); c.close(); log(u["id"],"KNOWLEDGE_PUBLISHED","KNOWLEDGE",kid,title); flash("Đã đăng nội dung và đưa vào kho tri thức trung tâm."); return redirect(url_for("knowledge_hub"))
    return render_template("knowledge_new.html")
@app.get("/api/v1/knowledge/collect")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_collect():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"error":"missing q"}),400
    try:
        items=knowledge_engine.wikipedia(q)
        return jsonify({"query":q,"source":"Wikipedia","items":items,"count":len(items),"status":"COLLECTED_FOR_REVIEW"})
    except Exception:
        return jsonify({"query":q,"source":"Wikipedia","items":[],"count":0,"status":"SOURCE_UNAVAILABLE"}),502
@app.post("/api/v1/knowledge/ingest")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_ingest():
    data=request.get_json(silent=True) or {}; title=(data.get("title") or "").strip(); source_url=(data.get("source_url") or "").strip(); destination=(data.get("destination") or "").strip()
    if not title or not source_url: return jsonify({"error":"title and source_url required"}),400
    try: fetched=knowledge_engine.fetch_url(source_url); ai=knowledge_engine.local_ai_extract(title,fetched["text"])
    # intentionally stores the collected material as a knowledge draft for review
    except Exception as e: return jsonify({"error":str(e)}),400
    c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(current_user()["id"],title,fetched["text"],"SOURCE_IMPORT",destination,"",source_url,"EXTERNAL",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PENDING_REVIEW",now(),now())); kid=cur.lastrowid
    c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"External source","EXTERNAL","COLLECTED",fetched["text"],now())); c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,current_user()["id"],"SOURCE_COLLECTED","AI extraction fallback; pending review",now())); c.commit(); c.close(); return jsonify({"id":kid,"status":"PENDING_REVIEW","ai":ai})
@app.get("/admin/guides")
@role_required("ADMIN","SUPER_ADMIN")
def admin_guides():
    c=db(); rows=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id ORDER BY g.id DESC").fetchall(); c.close(); return render_template("admin_guides.html",rows=rows)
@app.route("/admin/guides/<int:appid>",methods=["GET","POST"])
@role_required("ADMIN","SUPER_ADMIN")
def admin_guide(appid):
    c=db(); g=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id WHERE g.id=?",(appid,)).fetchone(); c.close()
    if not g:return "Not found",404
    if request.method=="POST":
        action=request.form.get("action"); note=request.form.get("note","").strip(); c=db()
        if action=="APPROVE": c.execute("UPDATE guide_applications SET status='APPROVED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); c.execute("UPDATE users SET role='GUIDE',trust_level='L2' WHERE id=?",(g["user_id"],)); detail="Guide approved; role=GUIDE; trust=L2"
        elif action=="REJECT": c.execute("UPDATE guide_applications SET status='REJECTED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="Guide rejected"
        else: c.execute("UPDATE guide_applications SET status='NEED_MORE_INFORMATION',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="More information requested"
        c.commit(); c.close(); log(session["uid"],action,"GUIDE_APPLICATION",appid,detail); flash("Đã cập nhật hồ sơ."); return redirect(url_for("admin_guide",appid=appid))
    return render_template("admin_guide.html",g=g)
@app.get("/admin/guides/<int:appid>/image")
@role_required("ADMIN","SUPER_ADMIN")
def guide_image(appid):
    c=db(); g=c.execute("SELECT card_image FROM guide_applications WHERE id=?",(appid,)).fetchone(); c.close(); return send_from_directory(UPLOAD,g["card_image"]) if g else ("Not found",404)
@app.get("/admin/audit")
@role_required("ADMIN","SUPER_ADMIN")
def audit():
    c=db(); rows=c.execute("SELECT a.*,u.email FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 300").fetchall(); c.close(); return render_template("audit.html",rows=rows)
engine=JourneyIntelligenceEngine()
knowledge_engine=KnowledgeIngestionEngine()
init_db()
if __name__=="__main__": app.run(host=os.environ.get("HOST","0.0.0.0"),port=int(os.environ.get("PORT","8000")),debug=os.environ.get("FLASK_DEBUG","0")=="1")
import os, sqlite3, uuid, json, re, urllib.parse, urllib.request
from datetime import datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template, flash, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from journey_engine import JourneyIntelligenceEngine
from knowledge_engine import KnowledgeIngestionEngine
BASE=os.path.dirname(__file__)
# Vercel's deployment filesystem is read-only; runtime writes must use /tmp.
RUNTIME_DIR=os.path.join('/tmp','hdvia')
DB=os.path.join(RUNTIME_DIR,"data","hdvia.db")
UPLOAD=os.path.join(RUNTIME_DIR,"private_uploads")
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(UPLOAD,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get("HDVIA_SECRET_KEY","change-me-in-production")
app.config.update(MAX_CONTENT_LENGTH=5*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
if os.environ.get("HDVIA_COOKIE_SECURE","0")=="1": app.config["SESSION_COOKIE_SECURE"]=True
PERMISSIONS={
"USER":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","ai.assistant.use"},
"GUIDE":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","itinerary.optimize","ai.assistant.use","ai.copilot.use","knowledge.create","knowledge.read","knowledge.media.publish","knowledge.source.collect"},
"PARTNER":{"profile.manage","journey.read","destination.read"},
"ADMIN":{"profile.manage","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","user.manage","guide.approve","permission.manage","security.manage","audit.read"},
"SUPER_ADMIN":{"*"}}
def now(): return datetime.utcnow().isoformat(timespec="seconds")+"Z"
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    c=db(); c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'USER',trust_level TEXT NOT NULL DEFAULT 'L1',status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS guide_applications(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,card_number TEXT NOT NULL,card_type TEXT NOT NULL,card_image TEXT NOT NULL,area TEXT,languages TEXT,status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',admin_note TEXT,reviewed_by INTEGER,reviewed_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id INTEGER,action TEXT NOT NULL,target_type TEXT,target_id INTEGER,detail TEXT,ip TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS journeys(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,title TEXT NOT NULL,itinerary TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_items(id INTEGER PRIMARY KEY AUTOINCREMENT,author_id INTEGER,title TEXT NOT NULL,content TEXT NOT NULL,content_type TEXT NOT NULL DEFAULT 'ARTICLE',destination TEXT,media_url TEXT,source_url TEXT,source_type TEXT NOT NULL DEFAULT 'HDV_VERIFIED',ai_summary TEXT,ai_facts_json TEXT,confidence TEXT NOT NULL DEFAULT 'medium',status TEXT NOT NULL DEFAULT 'PUBLISHED',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(author_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_sources(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER NOT NULL,source_url TEXT NOT NULL,source_name TEXT,source_type TEXT,source_status TEXT NOT NULL DEFAULT 'COLLECTED',raw_content TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id));
    CREATE TABLE IF NOT EXISTS knowledge_events(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER,actor_id INTEGER,event TEXT NOT NULL,detail TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id),FOREIGN KEY(actor_id) REFERENCES users(id));
    """)
    if not c.execute("SELECT id FROM users WHERE email=?",("admin@hdvia.local",)).fetchone():
        c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  ("HDVIA Admin","0000000000","admin@hdvia.local",generate_password_hash(os.environ.get("HDVIA_DEMO_ADMIN_PASSWORD","ChangeMe123!")),"ADMIN","L4","ACTIVE",now()))
    c.commit(); c.close()
def log(actor,action,target_type=None,target_id=None,detail=""):
    c=db(); c.execute("INSERT INTO audit_logs(actor_id,action,target_type,target_id,detail,ip,created_at) VALUES(?,?,?,?,?,?,?)",
                      (actor,action,target_type,target_id,detail,request.remote_addr if request else "",now())); c.commit(); c.close()
def current_user():
    uid=session.get("uid")
    if not uid:return None
    c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close(); return u
def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not current_user(): return redirect(url_for("login",next=request.path))
        return f(*a,**kw)
    return w
def role_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user()
            if not u or u["role"] not in roles:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def permission_required(permission):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user(); p=PERMISSIONS.get(u["role"],set()) if u else set()
            if not u:return redirect(url_for("login"))
            if "*" not in p and permission not in p:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def safe_next(n): return n if n and n.startswith("/") else url_for("profile")
@app.context_processor
def inject(): return {"user":current_user(),"version":"1.5.0-beta"}
@app.get("/")
def home(): return render_template("home.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        if not name or not phone or not email or len(pw)<8: flash("Vui lòng điền đủ thông tin và dùng mật khẩu tối thiểu 8 ký tự."); return redirect(url_for("register"))
        c=db()
        try:
            c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,phone,email,generate_password_hash(pw),"USER","L1","ACTIVE",now())); c.commit(); uid=c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()["id"]
        except sqlite3.IntegrityError: c.close(); flash("Email đã tồn tại."); return redirect(url_for("register"))
        c.close(); log(uid,"USER_REGISTERED","USER",uid); session["uid"]=uid; return redirect(url_for("profile"))
    return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
    nxt=request.args.get("next","")
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        c=db(); u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],pw): session["uid"]=u["id"]; log(u["id"],"LOGIN"); return redirect(safe_next(nxt))
        flash("Email hoặc mật khẩu không đúng.")
    return render_template("login.html",next=nxt)
@app.get("/logout")
def logout(): uid=session.get("uid"); session.clear(); log(uid,"LOGOUT") if uid else None; return redirect(url_for("home"))
@app.get("/profile")
@login_required
def profile():
    u=current_user(); c=db(); apps=c.execute("SELECT * FROM guide_applications WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); journeys=c.execute("SELECT id,title,created_at FROM journeys WHERE user_id=? ORDER BY id DESC LIMIT 10",(u["id"],)).fetchall(); c.close()
    return render_template("profile.html",u=u,apps=apps,journeys=journeys)
@app.route("/guide/apply",methods=["GET","POST"])
@login_required
def guide_apply():
    u=current_user()
    if request.method=="POST":
        card=request.form.get("card_number","").strip(); typ=request.form.get("card_type","").strip(); area=request.form.get("area","").strip(); langs=request.form.get("languages","").strip(); f=request.files.get("card_image")
        if not card or not typ or not f or not f.filename: flash("Cần mã thẻ, loại thẻ và ảnh thẻ HDV."); return redirect(url_for("guide_apply"))
        ext=os.path.splitext(secure_filename(f.filename))[1].lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): flash("Chỉ nhận JPG, PNG, WEBP."); return redirect(url_for("guide_apply"))
        filename=f"{uuid.uuid4().hex}{ext}"; f.save(os.path.join(UPLOAD,filename)); c=db(); cur=c.execute("INSERT INTO guide_applications(user_id,card_number,card_type,card_image,area,languages,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(u["id"],card,typ,filename,area,langs,"PENDING_REVIEW",now())); appid=cur.lastrowid; c.commit(); c.close(); log(u["id"],"GUIDE_APPLICATION_SUBMITTED","GUIDE_APPLICATION",appid); flash("Đã gửi hồ sơ. Trạng thái: PENDING_REVIEW."); return redirect(url_for("profile"))
    return render_template("guide_apply.html")
@app.route("/journey",methods=["GET","POST"])
@login_required
@permission_required("journey.analyze")
def journey():
    result=None
    if request.method=="POST":
        title=request.form.get("title","Hành trình mới").strip(); itinerary=request.form.get("itinerary","").strip(); result=engine.analyze(title,itinerary)
        c=db(); c.execute("INSERT INTO journeys(user_id,title,itinerary,result_json,created_at) VALUES(?,?,?,?,?,?)",(current_user()["id"],title,itinerary,json.dumps(result,ensure_ascii=False),now())); c.commit(); c.close(); log(current_user()["id"],"JOURNEY_ANALYZED","JOURNEY",None,title)
    return render_template("journey.html",result=result)
@app.post("/api/v1/journey/analyze")
@login_required
@permission_required("journey.analyze")
def journey_api():
    data=request.get_json(silent=True) or {}; result=engine.analyze(data.get("title","Hành trình mới"),data.get("itinerary","")); log(current_user()["id"],"JOURNEY_ANALYZED_API","JOURNEY",None,result.get("title","")); return jsonify(result)
@app.get("/api/v1/weather")
def weather_api():
    name=request.args.get("name","").strip(); lat=request.args.get("lat"); lon=request.args.get("lon")
    if not lat or not lon:
        p=engine.detect_places(name)
        if not p:return jsonify({"error":"Không nhận diện được địa điểm"}),404
        lat,lon=p[0]["lat"],p[0]["lon"]; name=p[0]["name"]
    p={"name":name,"lat":float(lat),"lon":float(lon)}
    return jsonify({"place":p,"weather":engine.weather_provider(p),"updated_at":now()})
@app.get("/api/v1/place-image")
def place_image_api():
    name=request.args.get("name","").strip()
    if not name:return jsonify({"error":"missing name"}),400
    try:
        q=urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrsearch":name+" Vietnam","gsrnamespace":6,"gsrlimit":1,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1000})
        req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+q,headers={"User-Agent":"HDVIA/1.4 Travel Intelligence"})
        with urllib.request.urlopen(req,timeout=8) as r: data=json.loads(r.read().decode("utf-8"))
        pages=data.get("query",{}).get("pages",{})
        for page in pages.values():
            info=page.get("imageinfo",[{}])[0]; return jsonify({"name":name,"image_url":info.get("thumburl") or info.get("url"),"title":page.get("title"),"source":"Wikimedia Commons"})
    except Exception as e:
        return jsonify({"name":name,"image_url":None,"source":"fallback","error":"image provider unavailable"})
    return jsonify({"name":name,"image_url":None,"source":"none"})
@app.get("/api/v1/route")
def route_api():
    names=[x.strip() for x in request.args.get("places","").split(",") if x.strip()]; points=[]
    for n in names:
        p=engine.detect_places(n)
        if p: points.append(p[0])
    return jsonify({"points":points,"total_km":round(sum(__import__('journey_engine').haversine_km(points[i],points[i+1]) for i in range(len(points)-1)),1) if len(points)>1 else 0})
@app.get("/health")
def health(): return jsonify({"status":"ok","service":"HDVIA","version":"1.5.0-beta","knowledge_hub":"enabled","time":now()})
@app.get("/knowledge")
@login_required
@permission_required("knowledge.read")
def knowledge_hub():
    c=db(); rows=c.execute("SELECT k.*,u.name AS author_name FROM knowledge_items k LEFT JOIN users u ON u.id=k.author_id WHERE k.status='PUBLISHED' ORDER BY k.id DESC LIMIT 100").fetchall(); c.close()
    return render_template("knowledge.html", rows=rows)
@app.route("/knowledge/new", methods=["GET","POST"])
@login_required
@permission_required("knowledge.create")
def knowledge_new():
    if request.method=="POST":
        u=current_user(); title=request.form.get("title","").strip(); content=request.form.get("content","").strip(); destination=request.form.get("destination","").strip(); content_type=request.form.get("content_type","ARTICLE").strip(); media_url=request.form.get("media_url","").strip(); source_url=request.form.get("source_url","").strip()
        if not title or not content: flash("Cần tiêu đề và nội dung."); return redirect(url_for("knowledge_new"))
        ai=knowledge_engine.local_ai_extract(title,content)
        c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(u["id"],title,content,content_type,destination,media_url,source_url,"HDV_VERIFIED",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PUBLISHED",now(),now())); kid=cur.lastrowid
        if source_url: c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"User supplied","EXTERNAL","DECLARED","",now()))
        c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,u["id"],"PUBLISHED","Verified Guide contribution",now())); c.commit(); c.close(); log(u["id"],"KNOWLEDGE_PUBLISHED","KNOWLEDGE",kid,title); flash("Đã đăng nội dung và đưa vào kho tri thức trung tâm."); return redirect(url_for("knowledge_hub"))
    return render_template("knowledge_new.html")
@app.get("/api/v1/knowledge/collect")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_collect():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"error":"missing q"}),400
    try:
        items=knowledge_engine.wikipedia(q)
        return jsonify({"query":q,"source":"Wikipedia","items":items,"count":len(items),"status":"COLLECTED_FOR_REVIEW"})
    except Exception:
        return jsonify({"query":q,"source":"Wikipedia","items":[],"count":0,"status":"SOURCE_UNAVAILABLE"}),502
@app.post("/api/v1/knowledge/ingest")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_ingest():
    data=request.get_json(silent=True) or {}; title=(data.get("title") or "").strip(); source_url=(data.get("source_url") or "").strip(); destination=(data.get("destination") or "").strip()
    if not title or not source_url: return jsonify({"error":"title and source_url required"}),400
    try: fetched=knowledge_engine.fetch_url(source_url); ai=knowledge_engine.local_ai_extract(title,fetched["text"])
    # intentionally stores the collected material as a knowledge draft for review
    except Exception as e: return jsonify({"error":str(e)}),400
    c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(current_user()["id"],title,fetched["text"],"SOURCE_IMPORT",destination,"",source_url,"EXTERNAL",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PENDING_REVIEW",now(),now())); kid=cur.lastrowid
    c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"External source","EXTERNAL","COLLECTED",fetched["text"],now())); c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,current_user()["id"],"SOURCE_COLLECTED","AI extraction fallback; pending review",now())); c.commit(); c.close(); return jsonify({"id":kid,"status":"PENDING_REVIEW","ai":ai})
@app.get("/admin/guides")
@role_required("ADMIN","SUPER_ADMIN")
def admin_guides():
    c=db(); rows=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id ORDER BY g.id DESC").fetchall(); c.close(); return render_template("admin_guides.html",rows=rows)
@app.route("/admin/guides/<int:appid>",methods=["GET","POST"])
@role_required("ADMIN","SUPER_ADMIN")
def admin_guide(appid):
    c=db(); g=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id WHERE g.id=?",(appid,)).fetchone(); c.close()
    if not g:return "Not found",404
    if request.method=="POST":
        action=request.form.get("action"); note=request.form.get("note","").strip(); c=db()
        if action=="APPROVE": c.execute("UPDATE guide_applications SET status='APPROVED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); c.execute("UPDATE users SET role='GUIDE',trust_level='L2' WHERE id=?",(g["user_id"],)); detail="Guide approved; role=GUIDE; trust=L2"
        elif action=="REJECT": c.execute("UPDATE guide_applications SET status='REJECTED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="Guide rejected"
        else: c.execute("UPDATE guide_applications SET status='NEED_MORE_INFORMATION',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="More information requested"
        c.commit(); c.close(); log(session["uid"],action,"GUIDE_APPLICATION",appid,detail); flash("Đã cập nhật hồ sơ."); return redirect(url_for("admin_guide",appid=appid))
    return render_template("admin_guide.html",g=g)
@app.get("/admin/guides/<int:appid>/image")
@role_required("ADMIN","SUPER_ADMIN")
def guide_image(appid):
    c=db(); g=c.execute("SELECT card_image FROM guide_applications WHERE id=?",(appid,)).fetchone(); c.close(); return send_from_directory(UPLOAD,g["card_image"]) if g else ("Not found",404)
@app.get("/admin/audit")
@role_required("ADMIN","SUPER_ADMIN")
def audit():
    c=db(); rows=c.execute("SELECT a.*,u.email FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 300").fetchall(); c.close(); return render_template("audit.html",rows=rows)
engine=JourneyIntelligenceEngine()
knowledge_engine=KnowledgeIngestionEngine()
init_db()
if __name__=="__main__": app.run(host=os.environ.get("HOST","0.0.0.0"),port=int(os.environ.get("PORT","8000")),debug=os.environ.get("FLASK_DEBUG","0")=="1")
import os, sqlite3, uuid, json, re, urllib.parse, urllib.request
from datetime import datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template, flash, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from journey_engine import JourneyIntelligenceEngine
from knowledge_engine import KnowledgeIngestionEngine
BASE=os.path.dirname(__file__)
# Vercel's deployment filesystem is read-only; runtime writes must use /tmp.
RUNTIME_DIR=os.path.join('/tmp','hdvia')
DB=os.path.join(RUNTIME_DIR,"data","hdvia.db")
UPLOAD=os.path.join(RUNTIME_DIR,"private_uploads")
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(UPLOAD,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get("HDVIA_SECRET_KEY","change-me-in-production")
app.config.update(MAX_CONTENT_LENGTH=5*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
if os.environ.get("HDVIA_COOKIE_SECURE","0")=="1": app.config["SESSION_COOKIE_SECURE"]=True
PERMISSIONS={
"USER":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","ai.assistant.use"},
"GUIDE":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","itinerary.optimize","ai.assistant.use","ai.copilot.use","knowledge.create","knowledge.read","knowledge.media.publish","knowledge.source.collect"},
"PARTNER":{"profile.manage","journey.read","destination.read"},
"ADMIN":{"profile.manage","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","user.manage","guide.approve","permission.manage","security.manage","audit.read"},
"SUPER_ADMIN":{"*"}}
def now(): return datetime.utcnow().isoformat(timespec="seconds")+"Z"
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    c=db(); c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'USER',trust_level TEXT NOT NULL DEFAULT 'L1',status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS guide_applications(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,card_number TEXT NOT NULL,card_type TEXT NOT NULL,card_image TEXT NOT NULL,area TEXT,languages TEXT,status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',admin_note TEXT,reviewed_by INTEGER,reviewed_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id INTEGER,action TEXT NOT NULL,target_type TEXT,target_id INTEGER,detail TEXT,ip TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS journeys(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,title TEXT NOT NULL,itinerary TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_items(id INTEGER PRIMARY KEY AUTOINCREMENT,author_id INTEGER,title TEXT NOT NULL,content TEXT NOT NULL,content_type TEXT NOT NULL DEFAULT 'ARTICLE',destination TEXT,media_url TEXT,source_url TEXT,source_type TEXT NOT NULL DEFAULT 'HDV_VERIFIED',ai_summary TEXT,ai_facts_json TEXT,confidence TEXT NOT NULL DEFAULT 'medium',status TEXT NOT NULL DEFAULT 'PUBLISHED',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(author_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS knowledge_sources(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER NOT NULL,source_url TEXT NOT NULL,source_name TEXT,source_type TEXT,source_status TEXT NOT NULL DEFAULT 'COLLECTED',raw_content TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id));
    CREATE TABLE IF NOT EXISTS knowledge_events(id INTEGER PRIMARY KEY AUTOINCREMENT,knowledge_id INTEGER,actor_id INTEGER,event TEXT NOT NULL,detail TEXT,created_at TEXT NOT NULL,FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id),FOREIGN KEY(actor_id) REFERENCES users(id));
    """)
    if not c.execute("SELECT id FROM users WHERE email=?",("admin@hdvia.local",)).fetchone():
        c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  ("HDVIA Admin","0000000000","admin@hdvia.local",generate_password_hash(os.environ.get("HDVIA_DEMO_ADMIN_PASSWORD","ChangeMe123!")),"ADMIN","L4","ACTIVE",now()))
    c.commit(); c.close()
def log(actor,action,target_type=None,target_id=None,detail=""):
    c=db(); c.execute("INSERT INTO audit_logs(actor_id,action,target_type,target_id,detail,ip,created_at) VALUES(?,?,?,?,?,?,?)",
                      (actor,action,target_type,target_id,detail,request.remote_addr if request else "",now())); c.commit(); c.close()
def current_user():
    uid=session.get("uid")
    if not uid:return None
    c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close(); return u
def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if not current_user(): return redirect(url_for("login",next=request.path))
        return f(*a,**kw)
    return w
def role_required(*roles):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user()
            if not u or u["role"] not in roles:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def permission_required(permission):
    def deco(f):
        @wraps(f)
        def w(*a,**kw):
            u=current_user(); p=PERMISSIONS.get(u["role"],set()) if u else set()
            if not u:return redirect(url_for("login"))
            if "*" not in p and permission not in p:return "403 Forbidden",403
            return f(*a,**kw)
        return w
    return deco
def safe_next(n): return n if n and n.startswith("/") else url_for("profile")
@app.context_processor
def inject(): return {"user":current_user(),"version":"1.5.0-beta"}
@app.get("/")
def home(): return render_template("home.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); phone=request.form.get("phone","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        if not name or not phone or not email or len(pw)<8: flash("Vui lòng điền đủ thông tin và dùng mật khẩu tối thiểu 8 ký tự."); return redirect(url_for("register"))
        c=db()
        try:
            c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,phone,email,generate_password_hash(pw),"USER","L1","ACTIVE",now())); c.commit(); uid=c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()["id"]
        except sqlite3.IntegrityError: c.close(); flash("Email đã tồn tại."); return redirect(url_for("register"))
        c.close(); log(uid,"USER_REGISTERED","USER",uid); session["uid"]=uid; return redirect(url_for("profile"))
    return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
    nxt=request.args.get("next","")
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        c=db(); u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],pw): session["uid"]=u["id"]; log(u["id"],"LOGIN"); return redirect(safe_next(nxt))
        flash("Email hoặc mật khẩu không đúng.")
    return render_template("login.html",next=nxt)
@app.get("/logout")
def logout(): uid=session.get("uid"); session.clear(); log(uid,"LOGOUT") if uid else None; return redirect(url_for("home"))
@app.get("/profile")
@login_required
def profile():
    u=current_user(); c=db(); apps=c.execute("SELECT * FROM guide_applications WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); journeys=c.execute("SELECT id,title,created_at FROM journeys WHERE user_id=? ORDER BY id DESC LIMIT 10",(u["id"],)).fetchall(); c.close()
    return render_template("profile.html",u=u,apps=apps,journeys=journeys)
@app.route("/guide/apply",methods=["GET","POST"])
@login_required
def guide_apply():
    u=current_user()
    if request.method=="POST":
        card=request.form.get("card_number","").strip(); typ=request.form.get("card_type","").strip(); area=request.form.get("area","").strip(); langs=request.form.get("languages","").strip(); f=request.files.get("card_image")
        if not card or not typ or not f or not f.filename: flash("Cần mã thẻ, loại thẻ và ảnh thẻ HDV."); return redirect(url_for("guide_apply"))
        ext=os.path.splitext(secure_filename(f.filename))[1].lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): flash("Chỉ nhận JPG, PNG, WEBP."); return redirect(url_for("guide_apply"))
        filename=f"{uuid.uuid4().hex}{ext}"; f.save(os.path.join(UPLOAD,filename)); c=db(); cur=c.execute("INSERT INTO guide_applications(user_id,card_number,card_type,card_image,area,languages,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(u["id"],card,typ,filename,area,langs,"PENDING_REVIEW",now())); appid=cur.lastrowid; c.commit(); c.close(); log(u["id"],"GUIDE_APPLICATION_SUBMITTED","GUIDE_APPLICATION",appid); flash("Đã gửi hồ sơ. Trạng thái: PENDING_REVIEW."); return redirect(url_for("profile"))
    return render_template("guide_apply.html")
@app.route("/journey",methods=["GET","POST"])
@login_required
@permission_required("journey.analyze")
def journey():
    result=None
    if request.method=="POST":
        title=request.form.get("title","Hành trình mới").strip(); itinerary=request.form.get("itinerary","").strip(); result=engine.analyze(title,itinerary)
        c=db(); c.execute("INSERT INTO journeys(user_id,title,itinerary,result_json,created_at) VALUES(?,?,?,?,?,?)",(current_user()["id"],title,itinerary,json.dumps(result,ensure_ascii=False),now())); c.commit(); c.close(); log(current_user()["id"],"JOURNEY_ANALYZED","JOURNEY",None,title)
    return render_template("journey.html",result=result)
@app.post("/api/v1/journey/analyze")
@login_required
@permission_required("journey.analyze")
def journey_api():
    data=request.get_json(silent=True) or {}; result=engine.analyze(data.get("title","Hành trình mới"),data.get("itinerary","")); log(current_user()["id"],"JOURNEY_ANALYZED_API","JOURNEY",None,result.get("title","")); return jsonify(result)
@app.get("/api/v1/weather")
def weather_api():
    name=request.args.get("name","").strip(); lat=request.args.get("lat"); lon=request.args.get("lon")
    if not lat or not lon:
        p=engine.detect_places(name)
        if not p:return jsonify({"error":"Không nhận diện được địa điểm"}),404
        lat,lon=p[0]["lat"],p[0]["lon"]; name=p[0]["name"]
    p={"name":name,"lat":float(lat),"lon":float(lon)}
    return jsonify({"place":p,"weather":engine.weather_provider(p),"updated_at":now()})
@app.get("/api/v1/place-image")
def place_image_api():
    name=request.args.get("name","").strip()
    if not name:return jsonify({"error":"missing name"}),400
    try:
        q=urllib.parse.urlencode({"action":"query","format":"json","generator":"search","gsrsearch":name+" Vietnam","gsrnamespace":6,"gsrlimit":1,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1000})
        req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+q,headers={"User-Agent":"HDVIA/1.4 Travel Intelligence"})
        with urllib.request.urlopen(req,timeout=8) as r: data=json.loads(r.read().decode("utf-8"))
        pages=data.get("query",{}).get("pages",{})
        for page in pages.values():
            info=page.get("imageinfo",[{}])[0]; return jsonify({"name":name,"image_url":info.get("thumburl") or info.get("url"),"title":page.get("title"),"source":"Wikimedia Commons"})
    except Exception as e:
        return jsonify({"name":name,"image_url":None,"source":"fallback","error":"image provider unavailable"})
    return jsonify({"name":name,"image_url":None,"source":"none"})
@app.get("/api/v1/route")
def route_api():
    names=[x.strip() for x in request.args.get("places","").split(",") if x.strip()]; points=[]
    for n in names:
        p=engine.detect_places(n)
        if p: points.append(p[0])
    return jsonify({"points":points,"total_km":round(sum(__import__('journey_engine').haversine_km(points[i],points[i+1]) for i in range(len(points)-1)),1) if len(points)>1 else 0})
@app.get("/health")
def health(): return jsonify({"status":"ok","service":"HDVIA","version":"1.5.0-beta","knowledge_hub":"enabled","time":now()})
@app.get("/knowledge")
@login_required
@permission_required("knowledge.read")
def knowledge_hub():
    c=db(); rows=c.execute("SELECT k.*,u.name AS author_name FROM knowledge_items k LEFT JOIN users u ON u.id=k.author_id WHERE k.status='PUBLISHED' ORDER BY k.id DESC LIMIT 100").fetchall(); c.close()
    return render_template("knowledge.html", rows=rows)
@app.route("/knowledge/new", methods=["GET","POST"])
@login_required
@permission_required("knowledge.create")
def knowledge_new():
    if request.method=="POST":
        u=current_user(); title=request.form.get("title","").strip(); content=request.form.get("content","").strip(); destination=request.form.get("destination","").strip(); content_type=request.form.get("content_type","ARTICLE").strip(); media_url=request.form.get("media_url","").strip(); source_url=request.form.get("source_url","").strip()
        if not title or not content: flash("Cần tiêu đề và nội dung."); return redirect(url_for("knowledge_new"))
        ai=knowledge_engine.local_ai_extract(title,content)
        c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(u["id"],title,content,content_type,destination,media_url,source_url,"HDV_VERIFIED",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PUBLISHED",now(),now())); kid=cur.lastrowid
        if source_url: c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"User supplied","EXTERNAL","DECLARED","",now()))
        c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,u["id"],"PUBLISHED","Verified Guide contribution",now())); c.commit(); c.close(); log(u["id"],"KNOWLEDGE_PUBLISHED","KNOWLEDGE",kid,title); flash("Đã đăng nội dung và đưa vào kho tri thức trung tâm."); return redirect(url_for("knowledge_hub"))
    return render_template("knowledge_new.html")
@app.get("/api/v1/knowledge/collect")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_collect():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"error":"missing q"}),400
    try:
        items=knowledge_engine.wikipedia(q)
        return jsonify({"query":q,"source":"Wikipedia","items":items,"count":len(items),"status":"COLLECTED_FOR_REVIEW"})
    except Exception:
        return jsonify({"query":q,"source":"Wikipedia","items":[],"count":0,"status":"SOURCE_UNAVAILABLE"}),502
@app.post("/api/v1/knowledge/ingest")
@login_required
@permission_required("knowledge.source.collect")
def knowledge_ingest():
    data=request.get_json(silent=True) or {}; title=(data.get("title") or "").strip(); source_url=(data.get("source_url") or "").strip(); destination=(data.get("destination") or "").strip()
    if not title or not source_url: return jsonify({"error":"title and source_url required"}),400
    try: fetched=knowledge_engine.fetch_url(source_url); ai=knowledge_engine.local_ai_extract(title,fetched["text"])
    # intentionally stores the collected material as a knowledge draft for review
    except Exception as e: return jsonify({"error":str(e)}),400
    c=db(); cur=c.execute("INSERT INTO knowledge_items(author_id,title,content,content_type,destination,media_url,source_url,source_type,ai_summary,ai_facts_json,confidence,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(current_user()["id"],title,fetched["text"],"SOURCE_IMPORT",destination,"",source_url,"EXTERNAL",ai["summary"],json.dumps(ai["facts"],ensure_ascii=False),ai["confidence"],"PENDING_REVIEW",now(),now())); kid=cur.lastrowid
    c.execute("INSERT INTO knowledge_sources(knowledge_id,source_url,source_name,source_type,source_status,raw_content,created_at) VALUES(?,?,?,?,?,?,?)",(kid,source_url,"External source","EXTERNAL","COLLECTED",fetched["text"],now())); c.execute("INSERT INTO knowledge_events(knowledge_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(kid,current_user()["id"],"SOURCE_COLLECTED","AI extraction fallback; pending review",now())); c.commit(); c.close(); return jsonify({"id":kid,"status":"PENDING_REVIEW","ai":ai})
@app.get("/admin/guides")
@role_required("ADMIN","SUPER_ADMIN")
def admin_guides():
    c=db(); rows=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id ORDER BY g.id DESC").fetchall(); c.close(); return render_template("admin_guides.html",rows=rows)
@app.route("/admin/guides/<int:appid>",methods=["GET","POST"])
@role_required("ADMIN","SUPER_ADMIN")
def admin_guide(appid):
    c=db(); g=c.execute("SELECT g.*,u.name,u.email,u.phone FROM guide_applications g JOIN users u ON u.id=g.user_id WHERE g.id=?",(appid,)).fetchone(); c.close()
    if not g:return "Not found",404
    if request.method=="POST":
        action=request.form.get("action"); note=request.form.get("note","").strip(); c=db()
        if action=="APPROVE": c.execute("UPDATE guide_applications SET status='APPROVED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); c.execute("UPDATE users SET role='GUIDE',trust_level='L2' WHERE id=?",(g["user_id"],)); detail="Guide approved; role=GUIDE; trust=L2"
        elif action=="REJECT": c.execute("UPDATE guide_applications SET status='REJECTED',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="Guide rejected"
        else: c.execute("UPDATE guide_applications SET status='NEED_MORE_INFORMATION',admin_note=?,reviewed_by=?,reviewed_at=? WHERE id=?",(note,session["uid"],now(),appid)); detail="More information requested"
        c.commit(); c.close(); log(session["uid"],action,"GUIDE_APPLICATION",appid,detail); flash("Đã cập nhật hồ sơ."); return redirect(url_for("admin_guide",appid=appid))
    return render_template("admin_guide.html",g=g)
@app.get("/admin/guides/<int:appid>/image")
@role_required("ADMIN","SUPER_ADMIN")
def guide_image(appid):
    c=db(); g=c.execute("SELECT card_image FROM guide_applications WHERE id=?",(appid,)).fetchone(); c.close(); return send_from_directory(UPLOAD,g["card_image"]) if g else ("Not found",404)
@app.get("/admin/audit")
@role_required("ADMIN","SUPER_ADMIN")
def audit():
    c=db(); rows=c.execute("SELECT a.*,u.email FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 300").fetchall(); c.close(); return render_template("audit.html",rows=rows)
engine=JourneyIntelligenceEngine()
knowledge_engine=KnowledgeIngestionEngine()
init_db()
if __name__=="__main__": app.run(host=os.environ.get("HOST","0.0.0.0"),port=int(os.environ.get("PORT","8000")),debug=os.environ.get("FLASK_DEBUG","0")=="1")
