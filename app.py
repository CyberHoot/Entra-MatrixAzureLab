import os
import uuid
from flask import Flask, session, redirect, url_for, request, render_template_string
import msal

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", str(uuid.uuid4()))

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
TENANT_ID = os.environ["TENANT_ID"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/redirect"
SCOPE = ["User.Read"]  # simple, reliable demo scope

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

def _build_auth_url(state):
    return _build_msal_app().get_authorization_request_url(
        scopes=SCOPE,
        state=state,
        redirect_uri=url_for("authorized", _external=True, _scheme="https"),
        prompt="select_account"
    )

def _require_login():
    return session.get("user") is not None

MATRIX_BASE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>EnterTheMatrix</title>
  <style>
    body { margin:0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; background:#020a02; color:#9dff9d; }
    .wrap { max-width: 980px; margin: 0 auto; padding: 28px; }
    .card { border:1px solid #1b5; background: rgba(0,20,0,.55); border-radius: 12px; padding: 18px; box-shadow: 0 0 24px rgba(0,255,60,.12); }
    .btn { display:inline-block; padding:10px 14px; border-radius: 10px; border:1px solid #1b5; color:#9dff9d; text-decoration:none; margin-right:10px; }
    .btn:hover { background: rgba(0,255,60,.08); }
    pre { background: rgba(0,0,0,.35); padding: 14px; border-radius: 10px; overflow:auto; border:1px solid rgba(0,255,60,.25); }
    .hint { opacity:.85; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    @media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }

    /* simple "Matrix rain" */
    canvas { position:fixed; inset:0; z-index:-1; }
  </style>
</head>
<body>
<canvas id="c"></canvas>
<script>
  const c = document.getElementById('c'), ctx = c.getContext('2d');
  function resize(){ c.width = innerWidth; c.height = innerHeight; }
  addEventListener('resize', resize); resize();
  const letters = "アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズヅブプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴン0123456789";
  const fontSize = 16;
  let cols = Math.floor(c.width / fontSize);
  let drops = Array(cols).fill(1);
  function draw(){
    ctx.fillStyle = 'rgba(2,10,2,0.08)';
    ctx.fillRect(0,0,c.width,c.height);
    ctx.fillStyle = '#3f6';
    ctx.font = fontSize + 'px monospace';
    for(let i=0;i<drops.length;i++){
      const text = letters[Math.floor(Math.random()*letters.length)];
      ctx.fillText(text, i*fontSize, drops[i]*fontSize);
      if(drops[i]*fontSize > c.height && Math.random()>0.975) drops[i]=0;
      drops[i]++;
    }
    requestAnimationFrame(draw);
  }
  draw();
</script>

<div class="wrap">
  <div class="card">
    {{ body|safe }}
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    user = session.get("user")
    if not user:
        body = f"""
        <h2>ENTER THE MATRIX</h2>
        <p class="hint">This app uses Entra ID (MSAL auth code flow) so you can demo App Registration, Enterprise App, and Conditional Access.</p>
        <a class="btn" href="{url_for('login')}">Login with Entra ID</a>
        <a class="btn" href="{url_for('health')}">Health</a>
        """
        return render_template_string(MATRIX_BASE, body=body)

    body = f"""
    <h2>AUTHENTICATED</h2>
    <div class="grid">
      <div>
        <p><b>Name:</b> {user.get('name')}</p>
        <p><b>UPN:</b> {user.get('preferred_username')}</p>
        <p><b>Tenant:</b> {user.get('tid')}</p>
        <p><b>Object ID:</b> {user.get('oid')}</p>
        <p class="hint">Use this screen while you toggle CA policies. If CA blocks, you won’t get here.</p>
        <a class="btn" href="{url_for('claims')}">View Claims</a>
        <a class="btn" href="{url_for('logout')}">Logout</a>
      </div>
      <div>
        <h3>Demo checklist</h3>
        <ul>
          <li>Enterprise app appears in Entra → Enterprise applications</li>
          <li>Sign-in logs show CA applied</li>
          <li>Require MFA / Compliant device / Named location</li>
        </ul>
      </div>
    </div>
    """
    return render_template_string(MATRIX_BASE, body=body)

@app.route("/health")
def health():
    body = "<h2>OK</h2><p class='hint'>If you can see this, the app is running.</p><a class='btn' href='/'>Home</a>"
    return render_template_string(MATRIX_BASE, body=body)

@app.route("/login")
def login():
    state = str(uuid.uuid4())
    session["state"] = state
    return redirect(_build_auth_url(state))

@app.route(REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        return "State mismatch", 400

    if "error" in request.args:
        return f"Auth error: {request.args.get('error_description')}", 400

    code = request.args.get("code")
    result = _build_msal_app().acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=url_for("authorized", _external=True, _scheme="https"),
    )
    if "access_token" not in result:
        return f"Token failure: {result.get('error_description') or result}", 400

    # Pull useful ID token claims for your CA demo screen
    id_claims = result.get("id_token_claims", {})
    session["user"] = id_claims
    session["token"] = {
        "access_token": result["access_token"][:20] + "...",
        "expires_in": result.get("expires_in"),
        "scope": result.get("scope"),
    }
    return redirect(url_for("index"))

@app.route("/claims")
def claims():
    if not _require_login():
        return redirect(url_for("index"))
    body = f"""
    <h2>CLAIMS</h2>
    <p class="hint">This is what Entra issued. Great for explaining what changed when you apply CA (MFA, device, location, risk).</p>
    <pre>{session.get("user")}</pre>
    <a class="btn" href="/">Back</a>
    """
    return render_template_string(MATRIX_BASE, body=body)

@app.route("/logout")
def logout():
    session.clear()
    # Entra logout (optional but nice for clean demos)
    post_logout = url_for("index", _external=True, _scheme="https")
    return redirect(f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={post_logout}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
