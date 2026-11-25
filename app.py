import os, sqlite3, uuid, json, re, urllib.parse, urllib.request, traceback
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, session, render_template, render_template_string, flash, send_from_directory, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from oauth import init_oauth, provider_enabled
from connect import init_connect_blueprint
from journey_engine import JourneyIntelligenceEngine
from destination_catalog import DESTINATIONS, BY_SLUG, BY_NAME
from province_data import PROVINCES_2025, BY_PROVINCE_SLUG, resolve_province
from knowledge_layer import answer_from_knowledge
from conversation_engine import ConversationIntelligenceEngine
from warehouse import COLLECTIONS, warehouse_schema, warehouse_seed, normalize_record
from data_core import COLLECTIONS as CORE_COLLECTIONS, schema as core_schema, seed as core_seed, resolve_context
from data_core_bridge import DataCoreBridge
from copilot import CopilotEngine
from agent import HDVIAAgent, ToolRegistry
from external_connect import ExternalConnectManager, DEFAULT_EXTERNAL_CONNECTORS
from external_world import build_external_world_from_env, SyncEngine, ExternalAIOrchestrator, AgentExecutor, AgentExecutionPolicy
from public_apis import weather, geocode, air_quality, marine, search_place, route, wikipedia_search, wikidata_search, country
from open_api import OPEN_API_VERSION, OPEN_API_CATALOG, issue_key, hash_key, utcnow
from api_adapters import OPEN_API_ADAPTER, API_LAYER_VERSION
from knowledge_learning import KnowledgeLearningPipeline
from data_acquisition import candidate_from_web, google_cse_search, source_manifest

BASE=os.path.dirname(__file__)
# Vercel serverless filesystem is read-only outside /tmp.
RUNTIME_DIR=os.path.join('/tmp','hdvia')
DB=os.path.join(RUNTIME_DIR,'data','hdvia.db')
UPLOAD=os.path.join(RUNTIME_DIR,'private_uploads')
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(UPLOAD,exist_ok=True)
app=Flask(__name__)
# Vercel terminates HTTPS/proxying before forwarding to Flask. Trust the standard
# forwarded host/proto headers so OAuth callback URLs use the public domain.
app.wsgi_app=ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key=os.environ.get("HDVIA_SECRET_KEY","change-me-in-production")
# Unified HDVIA session: one authenticated browser session is shared by every module.
# The session is persistent across browser restarts for a bounded period; explicit
# logout remains the normal way to end it.
app.config.update(
    MAX_CONTENT_LENGTH=5*1024*1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    SESSION_REFRESH_EACH_REQUEST=True,
)
oauth=init_oauth(app)
init_connect_blueprint(app, provider_enabled)

@app.after_request
def _response_hardening(response):
    # Beta deployments must not serve stale HTML/API from an intermediary cache.
    if response.content_type and (response.content_type.startswith("text/html") or response.content_type.startswith("application/json")):
        response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        response.headers.setdefault("Pragma", "no-cache")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response
if os.environ.get("HDVIA_COOKIE_SECURE","0")=="1": app.config["SESSION_COOKIE_SECURE"]=True

PERMISSIONS={
"USER":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","ai.assistant.use","ai.copilot.use","itinerary.optimize","knowledge.read","knowledge.write"},
"GUIDE":{"profile.manage","journey.create","journey.read","journey.analyze","weather.read","destination.read","destination.intelligence","itinerary.optimize","ai.assistant.use","ai.copilot.use"},
"PARTNER":{"profile.manage","journey.read","destination.read"},
"ADMIN":{"*"},
"SUPER_ADMIN":{"*"}}

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def nearest_destination(lat, lon):
    """Return the nearest catalog destination using a lightweight haversine distance."""
    from math import radians, sin, cos, sqrt, atan2
    best=None; best_d=None
    for d in DESTINATIONS:
        dlat=radians(float(d["lat"])-float(lat)); dlon=radians(float(d["lon"])-float(lon))
        a=sin(dlat/2)**2+cos(radians(float(lat)))*cos(radians(float(d["lat"])))*sin(dlon/2)**2
        km=6371.0*2*atan2(sqrt(a),sqrt(max(0,1-a)))
        if best_d is None or km<best_d: best,best_d=d,km
    return best, best_d

@app.get("/api/v1/location-context")
def location_context():
    """Resolve browser-provided coordinates to the closest HDVIA destination.

    The browser decides whether location access is allowed. No coordinates are
    persisted by this endpoint. The response is intentionally small so the UI
    can use it to select a destination-themed background in a later release.
    """
    try:
        lat=float(request.args.get("lat")); lon=float(request.args.get("lon"))
        if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError
    except Exception:
        return jsonify({"ok":False,"error":"Tọa độ không hợp lệ."}),400
    d,km=nearest_destination(lat,lon)
    if not d: return jsonify({"ok":False}),404
    return jsonify({"ok":True,"destination":d["name"],"slug":d["slug"],"region":d["region"],"distance_km":round(km,1)})

def init_db():
    c=db(); c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL DEFAULT '',email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL DEFAULT '',role TEXT NOT NULL DEFAULT 'USER',trust_level TEXT NOT NULL DEFAULT 'L1',status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS social_accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,provider TEXT NOT NULL,provider_user_id TEXT NOT NULL,provider_email TEXT,created_at TEXT NOT NULL,last_login_at TEXT NOT NULL,UNIQUE(provider,provider_user_id),FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS guide_applications(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,card_number TEXT NOT NULL,card_type TEXT NOT NULL,card_image TEXT NOT NULL,area TEXT,languages TEXT,status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',admin_note TEXT,reviewed_by INTEGER,reviewed_at TEXT,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id INTEGER,action TEXT NOT NULL,target_type TEXT,target_id INTEGER,detail TEXT,ip TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS journeys(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,title TEXT NOT NULL,itinerary TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS journey_feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,journey_id INTEGER,score INTEGER NOT NULL,comment TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id),FOREIGN KEY(journey_id) REFERENCES journeys(id));
    CREATE TABLE IF NOT EXISTS knowledge_posts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,title TEXT NOT NULL,content TEXT NOT NULL,place TEXT,status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS warehouse_records(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,payload_json TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'DRAFT',created_by INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(created_by) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS api_keys(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,key_hash TEXT UNIQUE NOT NULL,owner_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL,last_used_at TEXT,FOREIGN KEY(owner_id) REFERENCES users(id));
    """)
    admin_email=os.environ.get("HDVIA_ADMIN_EMAIL","").strip().lower()
    admin_password=os.environ.get("HDVIA_DEMO_ADMIN_PASSWORD","").strip()
    admin_id=None
    # Production-safe bootstrap: missing admin credentials must not crash the
    # Vercel function. Admin/warehouse seeding is deferred until credentials
    # are configured in the deployment environment.
    if admin_email and admin_password:
        row=c.execute("SELECT id FROM users WHERE email=?",(admin_email,)).fetchone()
        if not row:
            c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                      ("HDVIA Super Admin","0000000000",admin_email,generate_password_hash(admin_password),"SUPER_ADMIN","L4","ACTIVE",now()))
            admin_id=c.execute("SELECT id FROM users WHERE email=?",(admin_email,)).fetchone()[0]
        else:
            admin_id=row[0]
    # Bootstrap the first curated warehouse seed once on a fresh runtime database.
    # Existing records are never overwritten. This keeps the demo data available
    # after deployment while preserving any data already entered by an admin.
    if admin_id and c.execute("SELECT COUNT(*) FROM warehouse_records").fetchone()[0] == 0:
        seed = warehouse_seed()
        for kind in COLLECTIONS:
            for payload in seed.get(kind, []):
                c.execute(
                    "INSERT INTO warehouse_records(kind,payload_json,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (kind, json.dumps(payload, ensure_ascii=False), payload.get("status", "DRAFT") or "DRAFT", admin_id, now(), payload.get("updated_at", now()))
                )
    # Additive bootstrap for the linked 8-domain data core. Existing rows are preserved.
    # Seed is inserted per kind only when that core kind is still empty, so upgrades
    # never duplicate or overwrite curated/admin-entered data.
    admin_id = c.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone()[0]
    core_seed_data = core_seed()
    for kind in CORE_COLLECTIONS:
        if c.execute("SELECT COUNT(*) FROM warehouse_records WHERE kind=?", (kind,)).fetchone()[0] == 0:
            for payload in core_seed_data.get(kind, []):
                c.execute(
                    "INSERT INTO warehouse_records(kind,payload_json,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                    (kind, json.dumps(payload, ensure_ascii=False), payload.get("status", "ACTIVE") or "ACTIVE", admin_id, now(), payload.get("updated_at", now()))
                )
    c.commit(); c.close()

def log(actor,action,target_type=None,target_id=None,detail=""):
    c=db(); c.execute("INSERT INTO audit_logs(actor_id,action,target_type,target_id,detail,ip,created_at) VALUES(?,?,?,?,?,?,?)",
                      (actor,action,target_type,target_id,detail,request.remote_addr if request else "",now())); c.commit(); c.close()

def _user_snapshot(u):
    return {k: u[k] for k in ("id", "name", "phone", "email", "role", "trust_level", "status")}

def establish_session(u):
    """Establish the single HDVIA identity used by every module."""
    session.permanent = True
    session["uid"] = int(u["id"])
    # Keep a small identity snapshot so a fresh serverless instance can still
    # recognize the authenticated browser before the backing DB is restored.
    session["user_snapshot"] = _user_snapshot(u)
    session.modified = True

def current_user():
    uid=session.get("uid")
    if not uid:return None
    try:
        c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close()
        if u:
            session["user_snapshot"] = _user_snapshot(u)
            return u
    except Exception:
        pass
    snap=session.get("user_snapshot")
    return snap if snap and int(snap.get("id", -1)) == int(uid) else None

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

def public_base_url():
    """Return the public OAuth origin for the current HDVIA hostname.

    Both apex and www are first-class production hosts. The callback must use
    the same host that started OAuth so the browser session/state cookie remains
    on the same origin. A fixed HDVIA_PUBLIC_BASE_URL can still be used for
    non-production/local deployments.
    """
    host=request.host.split(":",1)[0].lower()
    allowed={h.strip().lower() for h in os.environ.get(
        "HDVIA_ALLOWED_HOSTS", "hdvia.vn,www.hdvia.vn"
    ).split(",") if h.strip()}
    if host in allowed:
        proto=request.headers.get("X-Forwarded-Proto", request.scheme).split(",",1)[0].strip()
        return f"{proto}://{host}"
    return os.environ.get("HDVIA_PUBLIC_BASE_URL", request.url_root.rstrip("/"))

def oauth_callback_url(provider):
    return f"{public_base_url()}/auth/{provider}/callback"

def provider_profile(provider, token):
    client=oauth.create_client(provider)
    if provider == "google":
        return {"id": token.get("userinfo",{}).get("sub"), "name": token.get("userinfo",{}).get("name"), "email": token.get("userinfo",{}).get("email"), "email_verified": token.get("userinfo",{}).get("email_verified",False)}
    if provider == "facebook":
        r=client.get("me", params={"fields":"id,name,email"}, token=token); r.raise_for_status(); return r.json()
    if provider == "zalo":
        r=client.get("me", params={"fields":"id,name,picture"}, token=token); r.raise_for_status(); return r.json()
    raise ValueError("Unsupported provider")

def _social_identity_exists(c, provider, pid):
    return c.execute("SELECT * FROM social_accounts WHERE provider=? AND provider_user_id=?", (provider, pid)).fetchone()

def link_social_account(user_id, provider, profile):
    """Attach an OAuth identity to an already authenticated HDVIA account."""
    pid=str(profile.get("id") or "").strip()
    if not pid:
        raise ValueError("Provider did not return a user id")
    email=(profile.get("email") or "").strip().lower()
    c=db(); existing=_social_identity_exists(c, provider, pid)
    if existing and int(existing["user_id"]) != int(user_id):
        c.close(); raise ValueError("Identity này đã được liên kết với tài khoản HDVIA khác.")
    if existing:
        c.execute("UPDATE social_accounts SET provider_email=?,last_login_at=? WHERE id=?", (email, now(), existing["id"]))
    else:
        c.execute("INSERT INTO social_accounts(user_id,provider,provider_user_id,provider_email,created_at,last_login_at) VALUES(?,?,?,?,?,?)", (user_id,provider,pid,email,now(),now()))
    c.commit(); c.close()
    log(user_id, "CONNECT_IDENTITY_LINKED", "SOCIAL_ACCOUNT", None, provider)
    return True

def unlink_social_account(user_id, provider):
    c=db(); row=c.execute("SELECT id FROM social_accounts WHERE user_id=? AND provider=?", (user_id, provider)).fetchone()
    if not row:
        c.close(); raise ValueError("Nhà cung cấp chưa được liên kết.")
    count=int(c.execute("SELECT COUNT(*) AS n FROM social_accounts WHERE user_id=?", (user_id,)).fetchone()["n"])
    pw=c.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()["password_hash"]
    if count <= 1 and not pw:
        c.close(); raise ValueError("Không thể ngắt liên kết tài khoản đăng nhập cuối cùng.")
    c.execute("DELETE FROM social_accounts WHERE id=?", (row["id"],)); c.commit(); c.close()
    log(user_id, "CONNECT_IDENTITY_UNLINKED", "SOCIAL_ACCOUNT", None, provider)
    return True

def social_login(provider, profile):
    pid=str(profile.get("id") or "").strip();
    if not pid: raise ValueError("Provider did not return a user id")
    email=(profile.get("email") or "").strip().lower()
    name=(profile.get("name") or f"HDVIA {provider.title()} User").strip()
    c=db(); row=c.execute("SELECT user_id FROM social_accounts WHERE provider=? AND provider_user_id=?",(provider,pid)).fetchone()
    if row: uid=row["user_id"]
    else:
        uid=None
        if email:
            existing=c.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone(); uid=existing["id"] if existing else None
        if uid is None:
            local_email=email or f"{provider}_{pid}@social.hdvia.local"
            c.execute("INSERT INTO users(name,phone,email,password_hash,role,trust_level,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,"",local_email,"","USER","L1","ACTIVE",now())); uid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.execute("INSERT INTO audit_logs(actor_id,action,target_type,target_id,detail,ip,created_at) VALUES(?,?,?,?,?,?,?)",(uid,"USER_REGISTERED_SOCIAL","USER",uid,provider,request.remote_addr if request else "",now()))
        c.execute("INSERT OR IGNORE INTO social_accounts(user_id,provider,provider_user_id,provider_email,created_at,last_login_at) VALUES(?,?,?,?,?,?)",(uid,provider,pid,email,now(),now()))
    c.execute("UPDATE social_accounts SET provider_email=?,last_login_at=? WHERE provider=? AND provider_user_id=?",(email,now(),provider,pid)); c.commit(); c.close(); return uid

def csrf_token():
    token=session.get("csrf_token")
    if not token:
        token=uuid.uuid4().hex
        session["csrf_token"]=token
    return token

def require_csrf():
    expected=session.get("csrf_token")
    supplied=request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    return bool(expected and supplied and supplied==expected)

@app.context_processor
def inject(): return {"user":current_user(),"version":"1.9.3-beta-data-warehouse","csrf_token":csrf_token()}

@app.get("/")
def home(): return render_template("home.html")

@app.get("/destinations")
def destinations():
    """Legacy compatibility route. Destination discovery now lives inside Hành Trình AI."""
    return redirect(url_for("journey"))

@app.get("/destinations/<slug>")
def destination_detail(slug):
    """Legacy destination route: hand the destination question to Hành Trình AI."""
    d=BY_SLUG.get(slug)
    if not d: return "404 Not Found",404
    return redirect(url_for("journey", q=f"Thông tin điểm đến {d['name']}"))

@app.get("/api/v1/destinations")
def destinations_api():
    q=request.args.get("q","").strip().lower()
    region=request.args.get("region","").strip()
    data=[d for d in DESTINATIONS if (not q or q in d["name"].lower() or q in d["overview"].lower()) and (not region or d["region"]==region)]
    return jsonify({"scope":"VIETNAM","count":len(data),"destinations":data})

@app.get("/api/v1/provinces")
def provinces_api():
    """Official 34-province administrative data effective from 2025-07-01."""
    return jsonify({
        "scope":"VIETNAM_ADMIN_2025",
        "effective_date":"2025-07-01",
        "source":"Nghị quyết 202/2025/QH15; Quyết định 19/2025/QĐ-TTg",
        "count":len(PROVINCES_2025),
        "provinces":PROVINCES_2025,
    })

@app.get("/api/v1/provinces/<slug>")
def province_detail_api(slug):
    p=resolve_province(slug)
    if not p:
        return jsonify({"ok":False,"error":"Không tìm thấy tỉnh/thành."}),404
    return jsonify(p)

@app.get("/api/v1/destination/<slug>")
def destination_detail_api(slug):
    d=BY_SLUG.get(slug)
    if not d: return jsonify({"error":"Không tìm thấy điểm đến"}),404
    return jsonify(d)

@app.route("/register",methods=["GET","POST"])
def register():
    # Beta: close manual member registration. Users register/sign in through social identity providers.
    return redirect(url_for("login"))

@app.get("/auth/<provider>")
def oauth_start(provider):
    if provider not in ("google","facebook","zalo") or not provider_enabled(provider):
        flash(f"Đăng nhập bằng {provider.title()} chưa được cấu hình.")
        return redirect(url_for("login"))
    client=oauth.create_client(provider)
    if request.args.get("link") == "1":
        if not current_user():
            return redirect(url_for("login", next=url_for("profile")))
        session["oauth_link_user"] = int(current_user()["id"])
    session["oauth_next"]=request.args.get("next","")
    log(session.get("uid"), "CONNECT_OAUTH_STARTED", "PROVIDER", None, provider) if session.get("uid") else None
    return client.authorize_redirect(oauth_callback_url(provider))

@app.get("/auth/<provider>/callback")
def oauth_callback(provider):
    if provider not in ("google","facebook","zalo") or not provider_enabled(provider):
        flash("Nhà cung cấp đăng nhập chưa được cấu hình."); return redirect(url_for("login"))
    try:
        client=oauth.create_client(provider); token=client.authorize_access_token(); profile=provider_profile(provider,token)
        link_uid=session.pop("oauth_link_user", None)
        if link_uid:
            link_social_account(link_uid, provider, profile); return redirect(url_for("profile"))
        uid=social_login(provider,profile)
        c=db(); u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); c.close()
        if u:
            establish_session(u)
        else:
            session["uid"] = uid
            session.permanent = True
        log(uid,"LOGIN_SOCIAL", "USER",uid,provider); return redirect(safe_next(session.pop("oauth_next","")))
    except Exception:
        flash("Không thể hoàn tất đăng nhập. Vui lòng thử lại."); return redirect(url_for("login"))

@app.route("/login",methods=["GET","POST"])
def login():
    nxt=request.args.get("next","")
    # Keep local email/password login only for existing/admin accounts; public registration is social-only.
    if request.method=="POST":
        if not require_csrf(): return "Yêu cầu không hợp lệ", 400
        email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
        c=db(); u=c.execute("SELECT * FROM users WHERE email=? AND password_hash!=''",(email,)).fetchone(); c.close()
        if u and check_password_hash(u["password_hash"],pw):
            establish_session(u); log(u["id"],"LOGIN"); return redirect(safe_next(nxt))
        flash("Email hoặc mật khẩu không đúng.")
    providers=[p for p in ("google","facebook","zalo") if provider_enabled(p)]
    return render_template("login.html",next=nxt,providers=providers)

@app.get("/logout")
def logout(): uid=session.get("uid"); session.clear(); log(uid,"LOGOUT") if uid else None; return redirect(url_for("home"))

@app.get("/profile")
@login_required
def profile():
    u=current_user(); c=db(); apps=c.execute("SELECT * FROM guide_applications WHERE user_id=? ORDER BY id DESC",(u["id"],)).fetchall(); journeys=c.execute("SELECT id,title,created_at FROM journeys WHERE user_id=? ORDER BY id DESC LIMIT 10",(u["id"],)).fetchall(); c.close()
    return render_template("profile.html",u=u,apps=apps,journeys=journeys)

@app.get("/account/connections")
@login_required
def account_connections():
    u=current_user(); c=db(); rows=c.execute("SELECT provider,provider_email,created_at,last_login_at FROM social_accounts WHERE user_id=? ORDER BY provider", (u["id"],)).fetchall(); c.close()
    return render_template("account_connections.html", u=u, connections=rows, providers=[p for p in ("google","facebook","zalo") if provider_enabled(p)])

@app.post("/account/connections/<provider>/disconnect")
@login_required
def account_connection_disconnect(provider):
    if not require_csrf(): return "Yêu cầu không hợp lệ", 400
    if provider not in ("google","facebook","zalo"): return "Nhà cung cấp không hợp lệ",400
    try:
        unlink_social_account(current_user()["id"], provider)
        flash(f"Đã ngắt liên kết {provider.title()}.")
    except ValueError as exc:
        flash(str(exc))
    return redirect(url_for("account_connections"))

@app.route("/guide/apply",methods=["GET","POST"])
@login_required
def guide_apply():
    u=current_user()
    if request.method=="POST":
        if not require_csrf(): return "Yêu cầu không hợp lệ", 400
        card=request.form.get("card_number","").strip(); typ=request.form.get("card_type","").strip(); area=request.form.get("area","").strip(); langs=request.form.get("languages","").strip(); f=request.files.get("card_image")
        if not card or not typ or not f or not f.filename: flash("Cần mã thẻ, loại thẻ và ảnh thẻ HDV."); return redirect(url_for("guide_apply"))
        ext=os.path.splitext(secure_filename(f.filename))[1].lower()
        if ext not in (".jpg",".jpeg",".png",".webp"): flash("Chỉ nhận JPG, PNG, WEBP."); return redirect(url_for("guide_apply"))
        filename=f"{uuid.uuid4().hex}{ext}"; f.save(os.path.join(UPLOAD,filename)); c=db(); cur=c.execute("INSERT INTO guide_applications(user_id,card_number,card_type,card_image,area,languages,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(u["id"],card,typ,filename,area,langs,"PENDING_REVIEW",now())); appid=cur.lastrowid; c.commit(); c.close(); log(u["id"],"GUIDE_APPLICATION_SUBMITTED","GUIDE_APPLICATION",appid); flash("Đã gửi hồ sơ. Trạng thái: PENDING_REVIEW."); return redirect(url_for("profile"))
    return render_template("guide_apply.html")

@app.get("/kinh-nghiem")
@login_required
@permission_required("knowledge.read")
def knowledge():
    q=request.args.get("q","").strip()[:100]
    c=db()
    if q:
        rows=c.execute("SELECT k.*,u.name FROM knowledge_posts k JOIN users u ON u.id=k.user_id WHERE k.status='PUBLISHED' AND (k.title LIKE ? OR k.content LIKE ? OR k.place LIKE ?) ORDER BY k.id DESC LIMIT 100",(f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    else:
        rows=c.execute("SELECT k.*,u.name FROM knowledge_posts k JOIN users u ON u.id=k.user_id WHERE k.status='PUBLISHED' ORDER BY k.id DESC LIMIT 100").fetchall()
    c.close()
    return render_template("knowledge.html",rows=rows,q=q)

@app.route("/kinh-nghiem/viet",methods=["GET","POST"])
@login_required
@permission_required("knowledge.write")
def knowledge_write():
    if request.method=="POST":
        if not require_csrf(): return "Yêu cầu không hợp lệ", 400
        title=request.form.get("title","").strip()[:180]
        place=request.form.get("place","").strip()[:120]
        content=request.form.get("content","").strip()[:12000]
        if len(title)<5 or len(content)<20:
            flash("Tiêu đề tối thiểu 5 ký tự và nội dung tối thiểu 20 ký tự.")
            return redirect(url_for("knowledge_write"))
        c=db(); cur=c.execute("INSERT INTO knowledge_posts(user_id,title,content,place,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(current_user()["id"],title,content,place,"PENDING_REVIEW",now(),now())); pid=cur.lastrowid; c.commit(); c.close()
        log(current_user()["id"],"KNOWLEDGE_POST_CREATED","KNOWLEDGE",pid,title)
        flash("Đã đăng bài vào Kho kinh nghiệm.")
        return redirect(url_for("knowledge"))
    return render_template("knowledge_write.html")

@app.get("/kinh-nghiem/<int:post_id>")
@login_required
@permission_required("knowledge.read")
def knowledge_detail(post_id):
    c=db(); row=c.execute("SELECT k.*,u.name FROM knowledge_posts k JOIN users u ON u.id=k.user_id WHERE k.id=? AND k.status='PUBLISHED'",(post_id,)).fetchone(); c.close()
    if not row:return "Không tìm thấy bài viết",404
    return render_template("knowledge_detail.html",post=row)

@app.route("/tro-ly-ai", methods=["GET", "POST"])
@login_required
@permission_required("ai.assistant.use")
def ai_assistant():
    answer=None
    question=""
    predicted_questions=[]
    confidence=""
    if request.method=="POST":
        if not require_csrf(): return "Yêu cầu không hợp lệ", 400
        question=request.form.get("question","").strip()[:2000]
        if not question:
            answer="Hãy nhập câu hỏi hoặc tình huống bạn muốn HDVIA hỗ trợ."
        else:
            result=conversation_engine.answer(question)
            answer=result.get("answer")
            predicted_questions=result.get("predicted_questions",[])
            confidence=result.get("confidence","")
    return render_template("ai_assistant.html",answer=answer,question=question,
                           predicted_questions=predicted_questions,confidence=confidence)


def _normalize_journey_input(title, itinerary):
    title = (title or "Hành trình mới").strip()[:200]
    itinerary = (itinerary or "").strip()[:20000]
    if not title:
        title = "Hành trình mới"
    if not itinerary:
        raise ValueError("Vui lòng nhập lịch trình trước khi phân tích.")
    return title, itinerary


def _safe_journey_analyze(title, itinerary, start_date=None):
    """Run the Journey engine without allowing any Journey POST exception to escape."""
    try:
        title, itinerary = _normalize_journey_input(title, itinerary)
        result = engine.analyze(title, itinerary, start_date=start_date)
        # Resolve the live Journey result against the same eight-domain Data Core.
        # This is additive: existing Journey fields remain unchanged.
        result = data_core_bridge.enrich_journey(result)
        if not isinstance(result, dict):
            raise RuntimeError("Journey engine returned an invalid result")
        # Keep the response/template contract stable even if a provider returns partial data.
        result.setdefault("title", title)
        result.setdefault("days", [])
        result.setdefault("places", [])
        result.setdefault("weather", {})
        result.setdefault("risk_map", {})
        result.setdefault("risks", [])
        result.setdefault("recommendations", ["Kiểm tra lại lịch trình và thời tiết trước tour."])
        # Destination intelligence is now part of the Journey result contract.
        # Keep it here so HTML, API and future clients receive the same unified payload.
        result["destination_context"] = _destination_context_for_places(result.get("places") or [])
        return result, None
    except Exception as exc:
        # Log the full traceback for Vercel Runtime Logs while keeping the public response safe.
        try:
            traceback.print_exc()
        except Exception:
            pass
        return None, f"Journey analysis failed: {type(exc).__name__}: {exc}"


def _destination_context_for_places(places):
    """Return curated destination knowledge for the Journey AI result.

    The former destination module is now a data capability of Journey AI, not a
    separate UI module. This keeps the destination catalog reusable while making
    destination facts available in the same Journey Intelligence response.
    """
    contexts=[]
    for place in places or []:
        name=(place.get("name") if isinstance(place, dict) else str(place)).strip()
        if not name:
            continue
        d=BY_NAME.get(name.lower())
        if not d:
            # Accept small naming differences from the conversation resolver.
            d=next((x for x in DESTINATIONS if x["name"].lower() in name.lower() or name.lower() in x["name"].lower()), None)
        if d:
            contexts.append({
                "slug":d["slug"], "name":d["name"], "region":d["region"],
                "type":d["type"], "overview":d["overview"],
                "highlights":d.get("highlights",[]), "culture":d.get("culture",""),
                "history":d.get("history",""), "food":d.get("food",""),
                "best_for":d.get("best_for","")
            })
    return contexts


def _merge_conversation_result(journey_result, conversation_result):
    """Overlay conversational fields without destroying Journey Intelligence data.

    ConversationIntelligence returns a lightweight answer contract with empty/default
    journey fields in some paths. Never let those defaults erase live weather, route,
    risk, Plan B or briefing data already produced by Journey Intelligence.
    """
    merged = dict(journey_result or {})
    conv = dict(conversation_result or {})
    for key in ("ok", "engine", "query", "intent", "intents", "answer",
                "confidence", "sources", "predicted_questions"):
        if key in conv and conv[key] not in (None, ""):
            merged[key] = conv[key]
    return merged


def _ai_query_analyze(query):
    """Unified Hành Trình AI adapter with conversation understanding.

    The conversation layer first identifies intent/place and predicts useful
    follow-up questions. Journey Intelligence is then used when live weather,
    risk, route or itinerary context is needed. Curated knowledge is used for
    destination/history/culture/food/script questions.
    """
    q = " ".join((query or "").strip().split())
    if not q:
        return None, "Hãy nhập địa điểm, câu hỏi hoặc lịch trình."

    intents = conversation_engine.detect_intents(q)
    places = conversation_engine.resolve_places(q)
    start_date = None
    for _pat in (r"(?:khởi hành|khoi hanh|bắt đầu|bat dau|ngày đi|ngay di)\s*(?:ngày)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
                  r"(?:từ|tu)\s*(\d{4}-\d{1,2}-\d{1,2})"):
        _m = re.search(_pat, q, re.I)
        if _m:
            start_date = _m.group(1)
            break
    weather_intent = "WEATHER" in intents
    journey_like = any(x in intents for x in ("ITINERARY", "ROUTE", "RISK", "PLAN_B"))
    mutation_like = bool(re.search(r"\b(?:thêm|them|bỏ|bo|xóa|xoa|chuyển|chuyen|đổi|doi|sang|qua)\b", q.lower())) and bool(re.search(r"\bngày\s*\d+\b", q.lower()))

    # Journey Memory: when a follow-up omits the place name (e.g.
    # "Ngày 2 mưa thì làm sao?"), reuse the latest saved journey as context.
    remembered_journey = None
    if not places and (weather_intent or journey_like):
        try:
            u = current_user()
            if u:
                remembered_journey = _load_latest_journey_for_user(u)
        except Exception:
            remembered_journey = None

    if weather_intent and places:
        place = places[0]["name"]
        result, error = _safe_journey_analyze(f"Thời tiết {place}", f"Ngày 1: {place}", start_date=start_date)
        if result is not None:
            result = _merge_conversation_result(
                result, conversation_engine.answer(q, journey=result)
            )
            result["intent"] = "WEATHER"
            result["destination_context"] = _destination_context_for_places(result.get("places") or places)
        return result, error

    if mutation_like and remembered_journey:
        try:
            base_itinerary = remembered_journey.get("itinerary") or "\n".join(
                f"Ngày {d.get('day')}: {d.get('text','')}" for d in remembered_journey.get("days",[])
            )
            mutation = engine.mutate_journey(base_itinerary, q)
            if mutation.get("changed"):
                title = remembered_journey.get("title") or "Hành Trình AI"
                result, error = _safe_journey_analyze(title, mutation["itinerary"])
                if result is not None:
                    result["mutation"] = {"changed":True,"notes":mutation.get("notes",[]),"itinerary":mutation["itinerary"]}
                    result = _merge_conversation_result(result, conversation_engine.answer(q, journey=result))
                    result["destination_context"] = _destination_context_for_places(result.get("places") or places)
                return result, error
        except Exception:
            pass

    if journey_like:
        title = places[0]["name"] if places else "Phân tích Hành Trình AI"
        result, error = _safe_journey_analyze(title, q, start_date=start_date)
        if result is not None:
            result = _merge_conversation_result(
                result, conversation_engine.answer(q, journey=result)
            )
            result["destination_context"] = _destination_context_for_places(result.get("places") or places)
        return result, error

    # A place-less follow-up can still be answered against the remembered journey.
    # This keeps the conversation anchored to the active tour instead of falling
    # back to generic knowledge search.
    if remembered_journey:
        result = conversation_engine.answer(q, journey=remembered_journey)
        result = _merge_conversation_result(remembered_journey, result)
        result["query"] = q
        result["title"] = remembered_journey.get("title") or "Hành Trình AI"
        result["destination_context"] = _destination_context_for_places(result.get("places") or places)
        return result, None

    # Knowledge / destination / natural-language question path. We still enrich
    # the response with a small Journey result when a recognized place exists,
    # so the same screen can show weather/risk context without forcing an itinerary.
    journey_context = None
    if places:
        place = places[0]["name"]
        journey_context, _ = _safe_journey_analyze(place, f"Ngày 1: {place}")
    result = conversation_engine.answer(q, journey=journey_context)
    if journey_context:
        # Keep the existing Journey Intelligence contract while replacing only
        # conversational fields. Do not overwrite route/weather/risk/Plan B.
        journey_context = _merge_conversation_result(journey_context, result)
        journey_context["title"] = journey_context.get("title") or places[0]["name"]
        journey_context["query"] = q
        journey_context["destination_context"] = _destination_context_for_places(journey_context.get("places") or places)
        return journey_context, None
    result["title"] = "Hành Trình AI"
    result["days"] = []
    result["weather"] = {}
    result["risk_map"] = {}
    result["risks"] = []
    result["recommendations"] = ["Chọn một câu hỏi gợi ý để HDVIA phân tích tiếp."]
    result["destination_context"] = _destination_context_for_places(result.get("places") or [])
    result["confidence"] = result.get("confidence", "LOW")
    return result, None


@app.route("/journey",methods=["GET","POST"])
@login_required
@permission_required("journey.analyze")
def journey():
    result=None
    error=None
    query = request.args.get("q","").strip()
    title="Hành trình mới"
    itinerary=""
    if request.method=="GET" and query:
        result, error = _ai_query_analyze(query)
    if request.method=="POST":
        try:
            if not require_csrf(): return "Yêu cầu không hợp lệ", 400
            query=request.form.get("query","").strip()
            # Backward compatibility for older saved/bookmarked form submissions.
            if not query:
                title=request.form.get("title","Hành trình mới")
                itinerary=request.form.get("itinerary","")
                start_date=request.form.get("start_date", "").strip() or None
                result, error = _safe_journey_analyze(title, itinerary, start_date=start_date)
                if result is not None:
                    result["destination_context"] = _destination_context_for_places(result.get("places") or [])
            else:
                result, error = _ai_query_analyze(query)
                title = result.get("title","Hành trình AI") if result else "Hành trình AI"
                itinerary = query
            if result is not None:
                try:
                    u=current_user()
                    if not u:
                        return redirect(url_for("login", next=request.path))
                    c=db()
                    c.execute("INSERT INTO journeys(user_id,title,itinerary,result_json,created_at) VALUES(?,?,?,?,?)",
                              (u["id"], result.get("title",title), itinerary, json.dumps(result,ensure_ascii=False), now()))
                    c.commit()
                    c.close()
                    try:
                        log(u["id"],"JOURNEY_ANALYZED","JOURNEY",None,result.get("title",title))
                    except Exception:
                        pass
                except Exception as exc:
                    # Analysis is still useful even when the ephemeral Vercel SQLite store is unavailable.
                    error = f"Phân tích thành công nhưng chưa lưu được lịch sử: {exc}"
            if error:
                flash("Không thể hoàn tất phân tích hành trình. Sếp kiểm tra lại dữ liệu và thử lại.")
        except Exception as exc:
            traceback.print_exc()
            result=None
            error=f"Không thể hoàn tất phân tích hành trình: {type(exc).__name__}: {exc}"
    try:
        return render_template("journey.html",result=result,journey_error=error)
    except Exception:
        # Final safety net: never turn a journey analysis failure into a blank
        # Vercel 500 page. The analysis form remains usable even if a template
        # receives an unexpected/partial result from the engine.
        fallback = """<!doctype html><html lang='vi'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>HDVIA — Phân tích hành trình</title><style>body{font-family:Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#172033}textarea,input{width:100%;box-sizing:border-box;padding:12px;margin:8px 0;border:1px solid #ccd3df;border-radius:8px}textarea{min-height:180px}button{padding:12px 18px;border:0;border-radius:8px;background:#1769e0;color:#fff;font-weight:600}.alert{padding:12px;border-radius:8px;background:#fff3cd;margin-bottom:16px}.back{display:inline-block;margin-bottom:20px}</style></head><body><a class='back' href='/'>← Về HDVIA</a><h1>Phân tích hành trình</h1><div class='alert'>HDVIA chưa thể hiển thị đầy đủ kết quả ở lần này. Sếp có thể giữ nguyên lịch trình và bấm phân tích lại.</div><form method='post'><input name='title' value='Hành trình mới' required><textarea name='itinerary' required placeholder='Ngày 1: Huế\nNgày 2: Đà Nẵng\nNgày 3: Hội An'>{{ request.form.get('itinerary','Ngày 1: Huế\nNgày 2: Đà Nẵng\nNgày 3: Hội An') }}</textarea><button type='submit'>Phân tích lại</button></form></body></html>"""
        return render_template_string(fallback), 200


@app.post("/api/v1/journey/analyze")
@login_required
@permission_required("journey.analyze")
def journey_api():
    data=request.get_json(silent=True) or {}
    result, error = _safe_journey_analyze(data.get("title","Hành trình mới"), data.get("itinerary",""), data.get("start_date"))
    if error:
        return jsonify({"error":"Không thể phân tích hành trình.","detail":"Dữ liệu hoặc nguồn phân tích tạm thời không khả dụng."}), 422
    try:
        log(current_user()["id"],"JOURNEY_ANALYZED_API","JOURNEY",None,result.get("title",""))
    except Exception:
        pass
    return jsonify(result)

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
        req=urllib.request.Request("https://commons.wikimedia.org/w/api.php?"+q,headers={"User-Agent":"HDVIA/1.9.0-beta-commercial Travel Intelligence"})
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

def _load_latest_journey_for_user(u):
    c=db(); row=c.execute("SELECT result_json FROM journeys WHERE user_id=? ORDER BY id DESC LIMIT 1",(u["id"],)).fetchone(); c.close()
    if not row: return None
    try: return json.loads(row["result_json"])
    except Exception: return None

def _open_api_auth():
    raw=request.headers.get("X-HDVia-Key","").strip()
    if raw:
        c=db(); row=c.execute("SELECT id,owner_id FROM api_keys WHERE key_hash=? AND status='ACTIVE'",(hash_key(raw),)).fetchone()
        if row:
            c.execute("UPDATE api_keys SET last_used_at=? WHERE id=?",(utcnow(),row["id"])); c.commit(); c.close(); return row["owner_id"]
        c.close()
    u=current_user()
    return u["id"] if u else None

def _open_api_required(f):
    @wraps(f)
    def w(*a,**kw):
        owner=_open_api_auth()
        if not owner: return jsonify({"ok":False,"error":"API key hoặc phiên đăng nhập không hợp lệ."}),401
        return f(*a,**kw)
    return w



@app.get("/api/v1/public-api/health")
def public_api_health():
    return jsonify({"ok": True, "adapter": OPEN_API_ADAPTER.status(), "time": now()})

@app.get("/api/v1/public-api/catalog")
def public_api_catalog():
    return jsonify({"ok": True, "version": API_LAYER_VERSION, "providers": [
        {"name":"open_meteo","group":"weather","free":True,"auth":"none"},
        {"name":"open_meteo_geocoding","group":"geocoding","free":True,"auth":"none"},
        {"name":"open_meteo_air_quality","group":"air_quality","free":True,"auth":"none"},
        {"name":"open_meteo_marine","group":"marine","free":True,"auth":"none"},
        {"name":"osm_nominatim","group":"maps_geocoding","free":True,"auth":"none","rate_limit":"1 req/s on public server"},
        {"name":"osrm","group":"routing","free":True,"auth":"none","note":"public demo server; cache/rate-limit required"},
        {"name":"wikipedia","group":"knowledge","free":True,"auth":"none"},
        {"name":"wikidata","group":"knowledge_graph","free":True,"auth":"none"},
        {"name":"rest_countries","group":"countries","free":True,"auth":"bearer token"},
        {"name":"sunrise_sunset","group":"astronomy","free":True,"auth":"none"},
        {"name":"overpass","group":"osm_poi","free":True,"auth":"none","rate_limit":"public infrastructure; cache and rate-limit required"},
        {"name":"opentripmap","group":"tourism_poi","free":False,"auth":"api key","note":"optional; key supplied via OPENTRIPMAP_API_KEY"},
    ]})

@app.get("/api/v1/public-api/weather")
def public_api_weather():
    return jsonify(OPEN_API_ADAPTER.weather(float(request.args.get("lat")), float(request.args.get("lon")), int(request.args.get("days", 7))))

@app.get("/api/v1/public-api/geocode")
def public_api_geocode():
    return jsonify(OPEN_API_ADAPTER.geocode(request.args.get("q", "")))

@app.get("/api/v1/public-api/air-quality")
def public_api_air_quality():
    return jsonify(air_quality(float(request.args.get("lat")), float(request.args.get("lon"))))

@app.get("/api/v1/public-api/marine")
def public_api_marine():
    return jsonify(marine(float(request.args.get("lat")), float(request.args.get("lon"))))

@app.get("/api/v1/public-api/search-place")
def public_api_search_place():
    return jsonify(search_place(request.args.get("q", ""), int(request.args.get("limit", 5))))

@app.get("/api/v1/public-api/route")
def public_api_route():
    return jsonify(OPEN_API_ADAPTER.route(request.args.get("coords", ""), request.args.get("profile", "driving")))

@app.get("/api/v1/public-api/sun")
def public_api_sun():
    return jsonify(OPEN_API_ADAPTER.sun(float(request.args.get("lat")), float(request.args.get("lon")), request.args.get("date")))

@app.get("/api/v1/public-api/osm")
def public_api_osm():
    return jsonify(OPEN_API_ADAPTER.osm_search(request.args.get("q", ""), int(request.args.get("limit", 5))))

@app.get("/api/v1/public-api/opentripmap/places")
def public_api_opentripmap_places():
    return jsonify(OPEN_API_ADAPTER.opentripmap_places(float(request.args.get("lat")), float(request.args.get("lon")), int(request.args.get("radius", 5000)), request.args.get("kinds", "interesting_places")))

@app.get("/api/v1/public-api/opentripmap/details")
def public_api_opentripmap_details():
    return jsonify(OPEN_API_ADAPTER.opentripmap_details(request.args.get("xid", "")))

@app.get("/api/v1/public-api/destination/enrich")
def public_api_destination_enrich():
    return jsonify(OPEN_API_ADAPTER.enrich_destination(request.args.get("q", ""), request.args.get("lat", type=float), request.args.get("lon", type=float)))

@app.get("/api/v1/public-api/wikipedia")
def public_api_wikipedia():
    return jsonify(wikipedia_search(request.args.get("q", ""), request.args.get("lang", "en"), int(request.args.get("limit", 5))))

@app.get("/api/v1/public-api/wikidata")
def public_api_wikidata():
    return jsonify(wikidata_search(request.args.get("q", ""), int(request.args.get("limit", 5))))

@app.get("/api/v1/public-api/country")
def public_api_country():
    return jsonify(country(request.args.get("q", "")))

@app.get("/api/v1/external-world/status")
def external_world_status():
    return jsonify({"ok": True, "version": API_LAYER_VERSION, "layers": {
        "two_way_sync": True, "provider_integration": True, "external_ai_orchestration": True, "agent_execution": True
    }, "providers": external_world.status(), "agent": {"dry_run_default": True}})

@app.post("/api/v1/external-world/provider/<provider>/connect")
def external_world_provider_connect(provider):
    return jsonify(external_world.connect(provider))

@app.post("/api/v1/external-world/provider/<provider>/disconnect")
def external_world_provider_disconnect(provider):
    return jsonify(external_world.disconnect(provider))

@app.get("/api/v1/external-world/agent/audit")
def external_world_agent_audit():
    return jsonify({"ok": True, "count": len(external_agent.audit_log), "records": external_agent.audit_log[-100:]})

@app.post("/api/v1/external-world/sync/pull")
def external_world_pull():
    body=request.get_json(silent=True) or {}
    result=external_sync.pull((body.get("provider") or "").strip(), (body.get("resource") or "/").strip(), records_key=body.get("records_key", "records"))
    return jsonify({"ok": result.ok, "provider": result.provider, "direction": result.direction, "records_read": result.records_read, "records_written": result.records_written, "skipped": result.skipped, "error": result.error, "trace_id": result.trace_id}), (200 if result.ok else 400)

@app.post("/api/v1/external-world/sync/push")
def external_world_push():
    body=request.get_json(silent=True) or {}
    records=body.get("records") or []
    if not isinstance(records, list): return jsonify({"ok":False,"error":"records phải là list"}),400
    result=external_sync.push((body.get("provider") or "").strip(), (body.get("resource") or "/").strip(), records)
    return jsonify({"ok": result.ok, "provider": result.provider, "direction": result.direction, "records_written": result.records_written, "error": result.error, "trace_id": result.trace_id}), (200 if result.ok else 400)

@app.post("/api/v1/external-world/ai/orchestrate")
def external_world_ai_orchestrate():
    body=request.get_json(silent=True) or {}
    result=external_ai.run((body.get("task") or "").strip(), body.get("payload") or {}, providers=body.get("providers"))
    return jsonify(result), (200 if result.get("ok") else 502)

@app.post("/api/v1/external-world/agent/execute")
def external_world_agent_execute():
    body=request.get_json(silent=True) or {}
    requested_dry=body.get("dry_run", True)
    # Production execution is opt-in at both request and environment level.
    dry_run=bool(requested_dry) or os.environ.get("HDVIA_AGENT_LIVE_EXECUTION", "0") != "1"
    policy=AgentExecutionPolicy(allowed_tools=set(body.get("allowed_tools") or []), dry_run=dry_run)
    try:
        result=external_agent.execute(tool=(body.get("tool") or "").strip(), provider=(body.get("provider") or "").strip(), resource=(body.get("resource") or "/").strip(), payload=body.get("payload") or {}, policy=policy)
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),403
    return jsonify(result), (200 if result.get("ok") else 502)

@app.get("/api/v1/openapi/status")
@_open_api_required
def openapi_status():
    return jsonify({"ok":True,"version":OPEN_API_VERSION,"service":"HDVIA","endpoints":OPEN_API_CATALOG,"connectors":external_connect.status()})

@app.post("/api/v1/openapi/copilot")
@_open_api_required
def openapi_copilot():
    u=current_user() or {"id":_open_api_auth(),"role":"API_CLIENT"}
    data=request.get_json(silent=True) or {}
    journey=data.get("journey") or _load_latest_journey_for_user(u)
    return jsonify(copilot_engine.compose(user=dict(u),journey=journey,question=str(data.get("question","")),data_context=(journey or {}).get("data_context")))

@app.post("/api/v1/openapi/agent/inspect-tour")
@_open_api_required
def openapi_agent():
    u=current_user() or {"id":_open_api_auth(),"role":"API_CLIENT"}
    data=request.get_json(silent=True) or {}
    journey=data.get("journey") or _load_latest_journey_for_user(u)
    return jsonify(agent_engine.inspect_tour(user=dict(u),journey=journey,data_context=(journey or {}).get("data_context")))

@app.get("/api/v1/openapi/connect/status")
@_open_api_required
def openapi_connect_status(): return jsonify({"ok":True,"connectors":external_connect.status()})

@app.post("/admin/api-keys")
@role_required("SUPER_ADMIN")
def admin_issue_api_key():
    if not require_csrf(): return "Yêu cầu không hợp lệ",400
    name=request.form.get("name","HDVIA API Client").strip()[:100] or "HDVIA API Client"
    raw,digest=issue_key("hdvia")
    c=db(); c.execute("INSERT INTO api_keys(name,key_hash,owner_id,status,created_at) VALUES(?,?,?,?,?)",(name,digest,current_user()["id"],"ACTIVE",utcnow())); c.commit(); c.close()
    log(current_user()["id"],"API_KEY_CREATED","API_KEY",None,name)
    return jsonify({"ok":True,"name":name,"api_key":raw,"warning":"Lưu khóa ngay; HDVIA không hiển thị lại khóa thô."})

@app.get("/admin/connect")
@role_required("ADMIN","SUPER_ADMIN")
def admin_connect(): return render_template_string("""{% extends 'base.html' %}{% block title %}External Connect – HDVIA{% endblock %}{% block content %}<div class='page-head'><div><span class='eyebrow'>EXTERNAL CONNECT</span><h1>Kết nối bên ngoài</h1><p>Quản lý trạng thái connector và khả năng tích hợp.</p></div></div><div class='warehouse-grid'>{% for c in connectors %}<div class='card'><span class='eyebrow'>{{c.category}}</span><h2>{{c.name}}</h2><p>Trạng thái: {% if c.enabled %}Đang bật{% else %}Chưa cấu hình{% endif %}</p><p>{{ ', '.join(c.capabilities) }}</p></div>{% endfor %}</div>{% endblock %}""",connectors=external_connect.status())

@app.post("/admin/knowledge/learning")
@role_required("ADMIN","SUPER_ADMIN")
def admin_learning_ingest():
    if not require_csrf(): return "Yêu cầu không hợp lệ",400
    rec=learning_pipeline.ingest(source_type=request.form.get("source_type","manual"),title=request.form.get("title",""),content=request.form.get("content",""),source_url=request.form.get("source_url",""))
    rec["validation"]=learning_pipeline.validate(rec)
    return jsonify(rec)

@app.get("/health")
def health(): return jsonify({"status":"ok","service":"HDVIA","version":"1.14.5-open-api-orchestrator","modules":["journey_intelligence","ai_copilot","ai_agent","external_connect","open_api","knowledge_learning","mobile_contract","weather_7_day","route_intelligence","knowledge_hub","admin_full_control"],"time":now()})

@app.get("/__version")
def build_info():
    return jsonify({"service":"HDVIA","version":"1.14.5-open-api-orchestrator","python_entrypoint":"app.py","deployment_mode":"vercel-zero-config","phases":{"A":"AI Copilot Foundation","B":"External Connect Foundation","C":"AI Agent Foundation","D":"Open API Foundation","E":"Mobile Native Contract"}})


@app.post("/api/v1/journey/feedback")
@login_required
@permission_required("journey.read")
def journey_feedback_api():
    data=request.get_json(silent=True) or {}
    try: score=int(data.get("score",0))
    except (TypeError,ValueError): score=0
    if score not in (1,2,3,4,5): return jsonify({"error":"score phải từ 1 đến 5"}),400
    journey_id=data.get("journey_id"); comment=str(data.get("comment","")).strip()[:2000]
    c=db()
    if journey_id:
        row=c.execute("SELECT id FROM journeys WHERE id=? AND user_id=?",(journey_id,current_user()["id"])).fetchone()
        if not row: c.close(); return jsonify({"error":"Không tìm thấy hành trình"}),404
    cur=c.execute("INSERT INTO journey_feedback(user_id,journey_id,score,comment,created_at) VALUES(?,?,?,?,?)",
                  (current_user()["id"],journey_id,score,comment,now()))
    c.commit(); fid=cur.lastrowid; c.close()
    log(current_user()["id"],"JOURNEY_FEEDBACK","JOURNEY",journey_id,f"score={score}")
    return jsonify({"ok":True,"feedback_id":fid})

@app.get("/admin")
@role_required("ADMIN","SUPER_ADMIN")
def admin_dashboard():
    c=db()
    stats={
        "users": c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "pending_guides": c.execute("SELECT COUNT(*) FROM guide_applications WHERE status='PENDING_REVIEW'").fetchone()[0],
        "pending_knowledge": c.execute("SELECT COUNT(*) FROM knowledge_posts WHERE status='PENDING_REVIEW'").fetchone()[0],
        "warehouse": c.execute("SELECT COUNT(*) FROM warehouse_records").fetchone()[0],
        "published_knowledge": c.execute("SELECT COUNT(*) FROM knowledge_posts WHERE status='PUBLISHED'").fetchone()[0],
    }
    c.close()
    return render_template("admin_dashboard.html",stats=stats)

@app.get("/admin/users")
@role_required("ADMIN","SUPER_ADMIN")
def admin_users():
    c=db(); rows=c.execute("SELECT id,name,email,role,trust_level,status,created_at FROM users ORDER BY id DESC LIMIT 500").fetchall(); c.close()
    return render_template("admin_users.html",rows=rows)

@app.post("/admin/users/<int:user_id>/update")
@role_required("ADMIN","SUPER_ADMIN")
def admin_user_update(user_id):
    if not require_csrf(): return "Yêu cầu không hợp lệ", 400
    role=request.form.get("role","USER").strip().upper()
    status=request.form.get("status","ACTIVE").strip().upper()
    if role not in ("USER","GUIDE","PARTNER","ADMIN","SUPER_ADMIN") or status not in ("ACTIVE","SUSPENDED","PENDING"):
        return "Dữ liệu quyền không hợp lệ",400
    if user_id==current_user()["id"] and role != "SUPER_ADMIN":
        return "Không thể tự hạ quyền tài khoản quản trị hiện tại.",400
    c=db(); c.execute("UPDATE users SET role=?,status=? WHERE id=?",(role,status,user_id)); c.commit(); c.close()
    log(current_user()["id"],"USER_ADMIN_UPDATE","USER",user_id,f"role={role};status={status}")
    flash("Đã cập nhật quyền và trạng thái thành viên.")
    return redirect(url_for("admin_users"))

@app.get("/admin/kho-du-lieu-8")
@role_required("ADMIN","SUPER_ADMIN")
def admin_data_core():
    return render_template_string("""{% extends 'base.html' %}{% block title %}8 kho dữ liệu – HDVIA{% endblock %}{% block content %}<div class="page-head"><div><span class="eyebrow">HDVIA DATA CORE</span><h1>8 kho dữ liệu sống</h1><p>Kiến trúc dữ liệu chuẩn hóa, có nguồn, phiên bản và trạng thái kiểm duyệt.</p></div></div><div class="warehouse-grid">{% for k in collections %}<div class="card"><span class="eyebrow">{{k}}</span><h2>{{schema[k].label}}</h2><p>Trường bắt buộc: {{schema[k].required|join(', ')}}</p><span class="badge">{{counts[k]}} bản ghi</span></div>{% endfor %}</div>{% endblock %}""",collections=CORE_COLLECTIONS,schema=core_schema()["collections"],counts=counts_core())

def counts_core():
    c=db(); out={}
    for k in CORE_COLLECTIONS:
        out[k]=c.execute("SELECT COUNT(*) FROM warehouse_records WHERE kind=?",(k,)).fetchone()[0]
    c.close(); return out

@app.get("/admin/kho-du-lieu")
@role_required("ADMIN","SUPER_ADMIN")
def admin_data_warehouse():
    schema = warehouse_schema().get("collections", {})
    c = db()
    counts = {kind: c.execute("SELECT COUNT(*) FROM warehouse_records WHERE kind=?", (kind,)).fetchone()[0] for kind in COLLECTIONS}
    c.close()
    return render_template("admin_data_warehouse.html", schema=schema, counts=counts)

@app.post("/admin/kho-du-lieu/add")
@role_required("ADMIN","SUPER_ADMIN")
def admin_data_warehouse_add():
    if not require_csrf(): return "Yêu cầu không hợp lệ", 400
    kind = request.form.get("kind", "").strip()
    try:
        payload = normalize_record(kind, request.form.to_dict(flat=True))
    except ValueError as exc:
        flash(str(exc)); return redirect(url_for("admin_data_warehouse"))
    c = db(); cur = c.execute("INSERT INTO warehouse_records(kind,payload_json,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)", (kind, json.dumps(payload, ensure_ascii=False), payload.get("status", "DRAFT") or "DRAFT", current_user()["id"], now(), now())); rid = cur.lastrowid; c.commit(); c.close()
    log(current_user()["id"], "WAREHOUSE_RECORD_CREATED", "WAREHOUSE", rid, kind)
    flash("Đã nạp dữ liệu vào Kho dữ liệu HDVIA.")
    return redirect(url_for("admin_data_warehouse"))

@app.get("/admin/kho-du-lieu/export/<kind>")
@role_required("ADMIN","SUPER_ADMIN")
def admin_data_warehouse_export(kind):
    if kind not in COLLECTIONS: return "Loại dữ liệu không hợp lệ", 400
    c = db(); rows = c.execute("SELECT payload_json FROM warehouse_records WHERE kind=? ORDER BY id", (kind,)).fetchall(); c.close()
    records = [json.loads(r["payload_json"]) for r in rows]
    response = jsonify({"version":"1.0","kind":kind,"count":len(records),"records":records})
    response.headers["Content-Disposition"] = f'attachment; filename="hdvia_{kind}.json"'
    return response

@app.get("/api/v1/data-acquisition/status")
def data_acquisition_status():
    return jsonify({"ok":True,"version":"1.0.0","manifest":source_manifest()})

@app.post("/api/v1/data-acquisition/fetch")
@login_required
def data_acquisition_fetch():
    if current_user().get("role") not in ("ADMIN","SUPER_ADMIN"):
        return jsonify({"ok":False,"error":"Chỉ ADMIN/SUPER_ADMIN được chạy ingestion."}),403
    body=request.get_json(silent=True) or {}
    url=(body.get("url") or "").strip()
    kind=(body.get("kind") or "knowledge").strip()
    if not url: return jsonify({"ok":False,"error":"Thiếu url."}),400
    try:
        item=candidate_from_web(url=url, requested_kind=kind, destination_id=(body.get("destination_id") or ""), admin_id=(body.get("admin_id") or ""))
    except (ValueError, RuntimeError) as exc:
        return jsonify({"ok":False,"error":str(exc)}),400
    c=db(); now_s=now(); rec=item["record"]; rec["status"]="CANDIDATE"
    cur=c.execute("INSERT INTO warehouse_records(kind,payload_json,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)", (item["kind"], json.dumps(rec,ensure_ascii=False), "CANDIDATE", current_user()["id"], now_s, now_s))
    # Store lineage as a separate first-class warehouse record.
    lin=item["lineage"]; c.execute("INSERT INTO warehouse_records(kind,payload_json,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?)", ("lineage", json.dumps(lin,ensure_ascii=False), "CANDIDATE", current_user()["id"], now_s, now_s))
    c.commit(); c.close(); log(current_user()["id"],"DATA_ACQUISITION_CANDIDATE","WAREHOUSE",cur.lastrowid,item["kind"]+" <- "+item["fetch"]["url"])
    return jsonify({"ok":True,"status":"CANDIDATE","kind":item["kind"],"record":rec,"lineage":lin,"fetch":item["fetch"]}),201

@app.get("/api/v1/data-acquisition/google-search")
@login_required
def data_acquisition_google_search():
    if current_user().get("role") not in ("ADMIN","SUPER_ADMIN"):
        return jsonify({"ok":False,"error":"Chỉ ADMIN/SUPER_ADMIN được dùng connector."}),403
    q=(request.args.get("q") or "").strip()
    if not q:return jsonify({"ok":False,"error":"Thiếu q."}),400
    try:
        num = max(1, min(10, int(request.args.get("num", 5))))
        return jsonify({"ok":True,"query":q,"results":google_cse_search(q,num=num)})
    except (ValueError,RuntimeError) as exc:
        return jsonify({"ok":False,"error":str(exc)}),400

@app.get("/api/v1/data-warehouse/<kind>")
def data_warehouse_api(kind):
    if kind not in COLLECTIONS: return jsonify({"ok":False,"error":"Loại dữ liệu không hợp lệ."}),400
    c=db(); rows=c.execute("SELECT payload_json FROM warehouse_records WHERE kind=? AND status IN ('PUBLISHED','ACTIVE') ORDER BY id",(kind,)).fetchall(); c.close()
    return jsonify({"ok":True,"version":"1.0","kind":kind,"count":len(rows),"records":[json.loads(r["payload_json"]) for r in rows]})

@app.get("/api/v1/data-core/context/<journey_id>")
def data_core_context(journey_id):
    """Return one linked context graph for a journey across all eight domains."""
    c=db()
    records={k:[json.loads(r["payload_json"]) for r in c.execute("SELECT payload_json FROM warehouse_records WHERE kind=? AND status IN ('PUBLISHED','ACTIVE') ORDER BY id",(k,)).fetchall()] for k in CORE_COLLECTIONS}
    c.close()
    graph=resolve_context(records, journey_id=journey_id)
    return jsonify({"ok":True,"version":"2.0.0-linked","journey_id":journey_id,"graph":graph,"counts":{k:len(v) for k,v in graph.items()}})

@app.get("/api/v1/data-core/context/destination/<destination_id>")
def data_core_destination_context(destination_id):
    """Return all eight-domain records linked to a destination."""
    c=db(); records={k:[json.loads(r["payload_json"]) for r in c.execute("SELECT payload_json FROM warehouse_records WHERE kind=? AND status IN ('PUBLISHED','ACTIVE') ORDER BY id",(k,)).fetchall()] for k in CORE_COLLECTIONS}; c.close()
    graph=resolve_context(records, destination_id=destination_id)
    return jsonify({"ok":True,"version":"2.0.0-linked","destination_id":destination_id,"graph":graph,"counts":{k:len(v) for k,v in graph.items()}})

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

@app.get("/admin/kinh-nghiem")
@role_required("ADMIN","SUPER_ADMIN")
def admin_knowledge():
    c=db(); rows=c.execute("SELECT k.*,u.name,u.email FROM knowledge_posts k JOIN users u ON u.id=k.user_id ORDER BY k.id DESC LIMIT 300").fetchall(); c.close()
    return render_template("admin_knowledge.html",rows=rows)

@app.post("/admin/kinh-nghiem/<int:post_id>/<action>")
@role_required("ADMIN","SUPER_ADMIN")
def admin_knowledge_action(post_id, action):
    if not require_csrf(): return "Yêu cầu không hợp lệ", 400
    if action not in ("publish","reject"):
        return "Không hợp lệ",400
    c=db(); status="PUBLISHED" if action=="publish" else "REJECTED"; c.execute("UPDATE knowledge_posts SET status=?,updated_at=? WHERE id=?",(status,now(),post_id)); c.commit(); c.close()
    log(current_user()["id"],"KNOWLEDGE_"+action.upper(),"KNOWLEDGE",post_id)
    flash("Đã cập nhật bài viết.")
    return redirect(url_for("admin_knowledge"))

@app.get("/dieu-khoan")
def terms(): return render_template("terms.html")

@app.get("/chinh-sach")
def privacy(): return render_template("privacy.html")

@app.get("/data-deletion")
@app.get("/data_deletion")
def data_deletion():
    # Public page used by external providers (e.g. Facebook) to explain how
    # a user can request deletion of HDVIA account data.
    return render_template(
        "data_deletion.html",
        contact_email=os.environ.get("HDVIA_ADMIN_EMAIL", "admin@hdvia.vn").strip(),
    )

@app.get("/admin/audit")
@role_required("ADMIN","SUPER_ADMIN")
def audit():
    c=db(); rows=c.execute("SELECT a.*,u.email FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 300").fetchall(); c.close(); return render_template("audit.html",rows=rows)

engine=JourneyIntelligenceEngine()
conversation_engine=ConversationIntelligenceEngine()
copilot_engine=CopilotEngine()
data_core_bridge=DataCoreBridge(db)
external_connect=ExternalConnectManager(DEFAULT_EXTERNAL_CONNECTORS)
external_world=build_external_world_from_env()
external_sync=SyncEngine(external_world)
external_ai=ExternalAIOrchestrator({p.name:p for p in [external_world.get("external_ai")] if p}, default_order=("external_ai",))
external_agent=AgentExecutor(external_world)
learning_pipeline=KnowledgeLearningPipeline()
agent_tools=ToolRegistry()
agent_tools.register("journey.summary", lambda journey=None: {"title": (journey or {}).get("title",""), "days": len((journey or {}).get("days",[])), "risk_count": len((journey or {}).get("risks",[]))})
agent_tools.register("weather.summary", lambda journey=None: {"risk_count": len([x for x in ((journey or {}).get("risks") or []) if x.get("level") in ("HIGH","MEDIUM")]), "risk_levels": [x.get("level") for x in ((journey or {}).get("risks") or [])]})
agent_engine=HDVIAAgent(agent_tools)
init_db()
if __name__=="__main__": app.run(host=os.environ.get("HOST","0.0.0.0"),port=int(os.environ.get("PORT","8000")),debug=os.environ.get("FLASK_DEBUG","0")=="1")
