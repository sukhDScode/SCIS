import streamlit as st
import time
import pickle
import os

# ── FIREBASE IMPORT ───────────────────────────────────────────
# Import helper functions for saving/fetching Firestore data
# If serviceAccountKey.json is missing, app still runs normally
FIREBASE_ERROR = ""
try:
    from firebase_helpers import (
        save_login,
        save_placement_prediction,
        save_recommendation,
        save_resume_analysis,
        fetch_activity_log,
        fetch_placement_history,
        fetch_recommendation_history,
        fetch_resume_history,
        fetch_student_summary,
    )
    FIREBASE_ON = True
except Exception as _fb_err:
    FIREBASE_ON = False
    FIREBASE_ERROR = str(_fb_err)

# ── PAGE CONFIG (must be FIRST) ──────────────────────────────
st.set_page_config(
    page_title="Student Career Intelligence System",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── SESSION STATE ─────────────────────────────────────────────
if "stage"    not in st.session_state: st.session_state.stage    = "login"
if "username" not in st.session_state: st.session_state.username = ""
if "ra_result" not in st.session_state: st.session_state.ra_result = None

# ══════════════════════════════════════════════════════════════
#  PAGE 1 — LOADING
#  White page + 8-dot circular spinner + purple bottom banner
# ══════════════════════════════════════════════════════════════
def show_loading():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');

    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }

    /* ── peacock gradient background ── */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] section {
        background:
            radial-gradient(ellipse 80% 60% at 20% 30%, #005f5f 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 80% 70%, #003d5c 0%, transparent 60%),
            linear-gradient(135deg, #002b36 0%, #00474f 25%, #006b6b 50%, #007a7a 65%, #005f73 80%, #003d52 100%)
            !important;
    }

    /* ── full-height centre flex ── */
    .load-wrap {
        display:flex; flex-direction:column;
        align-items:center; justify-content:center;
        min-height:100vh;
        gap:0;
    }

    /* ── logo / icon ── */
    .load-icon {
        font-size:4.5rem; margin-bottom:1rem;
        filter:drop-shadow(0 0 24px rgba(0,210,200,.55));
    }

    /* ── title ── */
    .load-title {
        font-family:'Poppins',sans-serif;
        font-size:clamp(1.5rem,4vw,2.4rem);
        font-weight:800; color:#e0f7f7;
        letter-spacing:-.5px; text-align:center;
        margin-bottom:.3rem;
        text-shadow:0 0 30px rgba(0,210,200,.4);
    }
    .load-sub {
        font-family:'Poppins',sans-serif;
        font-size:.85rem; font-weight:400;
        color:rgba(160,230,230,.75);
        letter-spacing:3px; text-transform:uppercase;
        text-align:center; margin-bottom:2.8rem;
    }

    /* ── dot progress bar ── */
    .dot-bar {
        display:flex; gap:10px;
        align-items:center; justify-content:center;
        margin-bottom:1.4rem;
    }
    .dot-bar span {
        width:12px; height:12px; border-radius:50%;
        background:#00d4c8;
        animation:dot-pulse 1.4s ease-in-out infinite;
        box-shadow:0 0 8px rgba(0,212,200,.6);
    }
    .dot-bar span:nth-child(1){ animation-delay:0s;    }
    .dot-bar span:nth-child(2){ animation-delay:0.18s; }
    .dot-bar span:nth-child(3){ animation-delay:0.36s; }
    .dot-bar span:nth-child(4){ animation-delay:0.54s; }
    .dot-bar span:nth-child(5){ animation-delay:0.72s; }
    .dot-bar span:nth-child(6){ animation-delay:0.90s; }
    .dot-bar span:nth-child(7){ animation-delay:1.08s; }
    .dot-bar span:nth-child(8){ animation-delay:1.26s; }
    @keyframes dot-pulse {
        0%,100%{ transform:scale(0.6); opacity:.3;  background:#00d4c8; }
        50%    { transform:scale(1.4); opacity:1;   background:#00fff5; }
    }

    /* ── status text ── */
    .load-status {
        font-family:'Poppins',sans-serif;
        font-size:.78rem; color:rgba(160,230,230,.7);
        letter-spacing:2px; text-transform:uppercase;
        text-align:center; min-height:1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

    steps = [
        "Initialising system…",
        "Loading career database…",
        "Calibrating AI model…",
        "Mapping career pathways…",
        "Almost ready…",
    ]

    st.markdown("""
    <div class="load-wrap">
        <div class="load-icon">🎓</div>
        <div class="load-title">Student Career Intelligence System</div>
        <div class="load-sub">SCIS · AI-Powered Career Platform</div>
        <div class="dot-bar">
            <span></span><span></span><span></span><span></span>
            <span></span><span></span><span></span><span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    status_slot = st.empty()
    for msg in steps:
        status_slot.markdown(
            f'<div class="load-status">{msg}</div>',
            unsafe_allow_html=True
        )
        time.sleep(0.7)

    time.sleep(0.4)
    st.session_state.stage = "dashboard"
    st.rerun()


# ══════════════════════════════════════════════════════════════
#  PAGE 2 — LOGIN
#  Purple winter landscape background + glass card
# ══════════════════════════════════════════════════════════════
def show_login():

    # ── inject all CSS first ──────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* hide chrome */
    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer{display:none !important;}
    .block-container{padding-top:0 !important; padding-bottom:0 !important;
                     max-width:100% !important;}

    /* ── BACKGROUND on the Streamlit container itself ── */
    [data-testid="stAppViewContainer"]{
        background:
            /* moon glow */
            radial-gradient(ellipse 180px 180px at 83% 11%,
                rgba(255,200,255,.38) 0%, transparent 70%),
            /* clouds suggestion */
            radial-gradient(ellipse 120px 35px at 12% 13%,
                rgba(210,155,225,.45) 0%, transparent 100%),
            radial-gradient(ellipse  85px 25px at 78% 10%,
                rgba(210,155,225,.38) 0%, transparent 100%),
            /* sky gradient */
            linear-gradient(180deg,
                #220e4a  0%,
                #3b1a70 18%,
                #6a2d96 34%,
                #9b4ab8 47%,
                #c068c0 57%,
                #a050a0 64%,
                /* mountain tone */
                #4a2278 65.5%,
                #3b1a68 73%,
                /* snow ground */
                #8070c0 74%,
                #a090d5 82%,
                #c0b5e5 90%,
                #ddd5f5 97%,
                #ece8ff 100%
            ) !important;
    }

    /* left pine tree — CSS triangle layered */
    [data-testid="stAppViewContainer"]::before {
        content:'';
        position:fixed; bottom:0; left:0;
        width:0; height:0;
        border-left: 90px solid transparent;
        border-right: 90px solid transparent;
        border-bottom: 280px solid rgba(18,45,100,.88);
        filter: drop-shadow(4px 0 6px rgba(0,0,0,.35));
        z-index:1; pointer-events:none;
    }

    /* right cabin glow hint */
    [data-testid="stAppViewContainer"]::after {
        content:'';
        position:fixed; bottom:8%; right:6%;
        width:90px; height:90px;
        background: radial-gradient(circle,
            rgba(255,160,30,.75) 0%,
            rgba(255,100,0,.4)  40%,
            transparent 70%);
        border-radius:50%;
        animation: glow 2s ease-in-out infinite alternate;
        z-index:1; pointer-events:none;
    }
    @keyframes glow{
        from{opacity:.7; transform:scale(1);   }
        to  {opacity:1;  transform:scale(1.15);}
    }

    /* ── CARD — semi-transparent glass ── */
    .login-card {
        background: rgba(255,255,255,.16);
        border: 1px solid rgba(255,255,255,.32);
        border-radius: 22px;
        padding: 2.6rem 2.2rem 1.8rem;
        backdrop-filter: blur(22px) saturate(1.4);
        -webkit-backdrop-filter: blur(22px) saturate(1.4);
        box-shadow: 0 10px 40px rgba(30,0,70,.45),
                    inset 0 1px 0 rgba(255,255,255,.35);
        animation: cardIn .65s cubic-bezier(.22,1,.36,1) both;
        position: relative; z-index: 10;
    }
    @keyframes cardIn{
        from{opacity:0;transform:translateY(26px) scale(.97);}
        to  {opacity:1;transform:translateY(0)    scale(1);  }
    }
    .card-title{
        font-family:'Poppins',sans-serif;
        font-size:2rem; font-weight:700;
        color:#fff; text-align:center;
        margin-bottom:.2rem;
    }

    /* ── Input labels ── */
    div[data-testid="stTextInput"] > label {
        font-family:'Poppins',sans-serif !important;
        font-size:.88rem !important; font-weight:500 !important;
        color:rgba(255,255,255,.9) !important;
    }
    /* ── Input boxes ── */
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,.85) !important;
        border: none !important;
        border-bottom: 2px solid rgba(255,255,255,.8) !important;
        border-radius: 6px !important;
        color: #1a0533 !important;
        font-family:'Poppins',sans-serif !important;
        font-size:.95rem !important;
        box-shadow: none !important;
        padding: .4rem .6rem !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-bottom: 2px solid #9b4ab8 !important;
        background: rgba(255,255,255,.95) !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color:rgba(80,40,120,.5) !important;
    }
    /* remove red/blue outline Streamlit adds */
    div[data-testid="stTextInput"] > div:first-child {
        border: none !important; box-shadow: none !important;
    }

    /* ── Checkbox ── */
    div[data-testid="stCheckbox"] > label {
        font-family:'Poppins',sans-serif !important;
        font-size:.82rem !important;
        color:rgba(255,255,255,.88) !important;
    }

    /* ── Log in button ── */
    div[data-testid="stButton"] > button {
        width:100% !important;
        background:#ffffff !important;
        border: none !important;
        border-radius:30px !important;
        color:#333 !important;
        font-family:'Poppins',sans-serif !important;
        font-size:1rem !important; font-weight:600 !important;
        padding:.65rem 1.5rem !important;
        margin-top:.6rem !important;
        box-shadow:0 4px 16px rgba(0,0,0,.2) !important;
        transition:all .25s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        background:#ede0ff !important;
        transform:translateY(-2px) !important;
        box-shadow:0 7px 22px rgba(100,40,180,.3) !important;
    }

    /* ── Forget password / footer text ── */
    .fp {
        font-family:'Poppins',sans-serif;
        font-size:.82rem; font-weight:600;
        color:rgba(255,255,255,.88);
        text-align:right; padding-top:6px;
    }
    .foot {
        font-family:'Poppins',sans-serif;
        font-size:.8rem; color:rgba(255,255,255,.72);
        text-align:center; margin-top:.9rem;
    }
    .foot b { color:#fff; font-weight:700; }

    /* alert */
    div[data-testid="stAlert"] {
        border-radius:10px !important;
        font-family:'Poppins',sans-serif !important;
        font-size:.83rem !important;
        position:relative; z-index:10;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Form in a centred column ──────────────────────────────
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # Re-inject card styling so the column looks like the card
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Login</div>', unsafe_allow_html=True)

        email    = st.text_input("Email",    placeholder="Enter your email",    key="email_in")
        password = st.text_input("Password", placeholder="Enter your password", type="password", key="pass_in")

        c1, c2 = st.columns([1.3, 1])
        with c1:
            remember = st.checkbox("Remember Me")
        with c2:
            st.markdown('<p class="fp">Forget Password</p>', unsafe_allow_html=True)

        login_btn = st.button("Log in")

        USERS = {
            "student@scis.com": "career123",
            "admin@scis.com":   "admin2024",
            "demo@scis.com":    "demo",
        }

        if login_btn:
            if not email or not password:
                st.error("Please enter both email and password.")
            elif email in USERS and USERS[email] == password:
                st.session_state.username = email.split("@")[0]
                st.session_state.stage    = "loading"
                # ── FIREBASE: save login event ────────────────
                if FIREBASE_ON:
                    save_login(email.split("@")[0], email)
                st.rerun()
            else:
                st.error("Wrong credentials. Try  student@scis.com / career123")

        st.markdown('<div class="foot">Don\'t have a account? <b>Register</b></div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)   # close .login-card

    # ── ANIMATED FEATURE CARDS below login ───────────────────────
    st.markdown("""
    <style>
    .features-strip {
        padding: 2.2rem 1rem 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        position: relative; z-index: 10;
    }
    .features-label {
        font-family: 'Poppins', sans-serif;
        font-size: .7rem; font-weight: 700;
        color: rgba(255,255,255,.65);
        letter-spacing: 3px; text-transform: uppercase;
        text-align: center; margin-bottom: .3rem;
    }
    .features-row {
        display: flex; gap: .85rem;
        flex-wrap: wrap; justify-content: center;
        max-width: 700px;
    }
    .feat-card {
        background: rgba(255,255,255,.13);
        border: 1px solid rgba(255,255,255,.25);
        border-radius: 16px;
        padding: 1.1rem 1.2rem .95rem;
        width: 150px;
        backdrop-filter: blur(14px);
        text-align: center;
        animation: floatUp 3.5s ease-in-out infinite;
        transition: transform .25s ease, background .25s ease;
        cursor: default;
    }
    .feat-card:hover {
        background: rgba(255,255,255,.22);
        transform: translateY(-6px) scale(1.04) !important;
    }
    .feat-card:nth-child(1) { animation-delay: 0s;    }
    .feat-card:nth-child(2) { animation-delay: 0.5s;  }
    .feat-card:nth-child(3) { animation-delay: 1s;    }
    .feat-card:nth-child(4) { animation-delay: 1.5s;  }
    @keyframes floatUp {
        0%,100% { transform: translateY(0px);   }
        50%      { transform: translateY(-8px);  }
    }
    .feat-icon {
        font-size: 2rem; margin-bottom: .5rem;
        display: block;
        animation: iconPulse 2.5s ease-in-out infinite;
    }
    .feat-card:nth-child(1) .feat-icon { animation-delay: 0s;   }
    .feat-card:nth-child(2) .feat-icon { animation-delay: .6s;  }
    .feat-card:nth-child(3) .feat-icon { animation-delay: 1.1s; }
    .feat-card:nth-child(4) .feat-icon { animation-delay: 1.6s; }
    @keyframes iconPulse {
        0%,100% { transform: scale(1);    filter: drop-shadow(0 0 0px rgba(255,255,255,0));   }
        50%      { transform: scale(1.18); filter: drop-shadow(0 0 8px rgba(255,255,255,.5)); }
    }
    .feat-title {
        font-family: 'Poppins', sans-serif;
        font-size: .78rem; font-weight: 700;
        color: #fff; margin-bottom: .25rem;
        line-height: 1.3;
    }
    .feat-desc {
        font-family: 'Poppins', sans-serif;
        font-size: .65rem; font-weight: 400;
        color: rgba(255,255,255,.7);
        line-height: 1.4;
    }
    /* animated ticker bar */
    .ticker-wrap {
        width: 100%; max-width: 600px;
        overflow: hidden;
        background: rgba(255,255,255,.1);
        border: 1px solid rgba(255,255,255,.2);
        border-radius: 99px;
        padding: .4rem 0;
        margin-top: .5rem;
    }
    .ticker-inner {
        display: flex; gap: 3rem;
        white-space: nowrap;
        animation: ticker 18s linear infinite;
        font-family: 'Poppins', sans-serif;
        font-size: .7rem; font-weight: 600;
        color: rgba(255,255,255,.8);
        padding-left: 100%;
    }
    @keyframes ticker {
        from { transform: translateX(0); }
        to   { transform: translateX(-100%); }
    }
    </style>

    <div class="features-strip">
        <div class="features-label">✦ What SCIS Offers</div>
        <div class="features-row">
            <div class="feat-card">
                <span class="feat-icon">🎯</span>
                <div class="feat-title">Placement Prediction</div>
                <div class="feat-desc">AI-powered probability scoring</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">📈</span>
                <div class="feat-title">Skill Analysis</div>
                <div class="feat-desc">Gap detection & improvement roadmap</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">🧠</span>
                <div class="feat-title">Smart Recommendations</div>
                <div class="feat-desc">Personalised action plans for you</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">📊</span>
                <div class="feat-title">Career Insights</div>
                <div class="feat-desc">Salary estimates & growth paths</div>
            </div>
        </div>
        <div class="ticker-wrap">
            <div class="ticker-inner">
                🎓 AI-Powered Career Platform &nbsp;·&nbsp;
                📌 Real-Time Placement Scoring &nbsp;·&nbsp;
                💡 Personalised Recommendations &nbsp;·&nbsp;
                🏆 Skill Gap Analysis &nbsp;·&nbsp;
                🚀 Built for CSE Students &nbsp;·&nbsp;
                ⚡ Random Forest ML Model &nbsp;·&nbsp;
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  ARTIFACTS LOADER
# ══════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_artifacts():
    model, scaler = None, None
    for n in ["model (1).pkl", "model.pkl"]:
        if os.path.exists(n):
            with open(n,"rb") as f: model = pickle.load(f)
            break
    for n in ["scaler (1).pkl", "scaler.pkl"]:
        if os.path.exists(n):
            with open(n,"rb") as f: scaler = pickle.load(f)
            break
    return model, scaler


# ══════════════════════════════════════════════════════════════
#  PAGE 3 — HOME INTERFACE
# ══════════════════════════════════════════════════════════════
def show_dashboard():
    uname = st.session_state.get("username", "student").title()

    # ── nav modal state ───────────────────────────────────────────
    if "nav_modal" not in st.session_state:
        st.session_state.nav_modal = None   # None | "product" | "pricing" | "support"

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');

    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }

    /* soft pink-lavender-blue gradient background */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse 70% 55% at 10% 15%, rgba(255,210,230,.55) 0%, transparent 65%),
            radial-gradient(ellipse 55% 50% at 88% 12%, rgba(200,185,255,.52) 0%, transparent 60%),
            radial-gradient(ellipse 50% 45% at 70% 88%, rgba(185,210,255,.42) 0%, transparent 60%),
            linear-gradient(145deg, #fdf0f8 0%, #f3eeff 40%, #eaf2ff 75%, #fce8f5 100%)
            !important;
    }

    /* ── NAV ── */
    .top-nav {
        display:flex; align-items:center; justify-content:space-between;
        padding:1rem 2.5rem;
        background:rgba(255,255,255,.55);
        backdrop-filter:blur(14px);
        border-bottom:1px solid rgba(200,180,230,.28);
        position:sticky; top:0; z-index:100;
    }
    .nav-logo {
        display:flex; align-items:center; gap:.55rem;
        font-family:'Inter',sans-serif; font-size:1rem; font-weight:700;
        color:#1a0533;
    }
    .logo-box {
        width:30px; height:30px; background:transparent;
        border-radius:7px; display:flex; align-items:center;
        justify-content:center; font-size:1rem;
    }
    .nav-links { display:flex; gap:1.8rem; }
    .nav-link {
        font-family:'Inter',sans-serif; font-size:.85rem;
        font-weight:500; color:#44306a; cursor:pointer;
    }
    .nav-right { display:flex; align-items:center; gap:.9rem; }
    .nav-user {
        font-family:'Inter',sans-serif; font-size:.85rem;
        font-weight:500; color:#44306a;
    }
    .nav-cta {
        font-family:'Inter',sans-serif; font-size:.85rem; font-weight:700;
        background:#1a0533; color:#fff; border:none;
        border-radius:8px; padding:.45rem 1.1rem; cursor:pointer;
    }

    /* ── HERO ── */
    .hero {
        display:flex; align-items:flex-start;
        justify-content:space-between;
        padding:4.5rem 2.5rem 2.5rem; gap:2.5rem; flex-wrap:wrap;
    }
    .hero-tag {
        display:inline-flex; align-items:center; gap:.4rem;
        background:rgba(124,58,237,.1);
        border:1px solid rgba(124,58,237,.22);
        border-radius:99px; padding:.28rem .8rem;
        font-family:'Inter',sans-serif; font-size:.75rem; font-weight:600;
        color:#7c3aed; margin-bottom:1rem; letter-spacing:.4px;
    }
    .hero-title {
        font-family:'Inter',sans-serif;
        font-size:clamp(2.6rem,5.5vw,4.2rem);
        font-weight:900; color:#0f0520;
        line-height:1.06; letter-spacing:-2px;
    }
    .hero-right { max-width:360px; padding-top:1.2rem; }
    .hero-desc {
        font-family:'Inter',sans-serif; font-size:1rem;
        color:#3d2a5a; line-height:1.65; margin-bottom:1.5rem;
    }
    .hero-cta {
        display:inline-flex; align-items:center; gap:.5rem;
        background:#1a0533; color:#fff;
        font-family:'Inter',sans-serif; font-size:.92rem; font-weight:700;
        padding:.75rem 1.7rem; border-radius:10px;
        border:2px solid #7c3aed; cursor:pointer; text-decoration:none;
    }
    .hero-note {
        font-family:'Inter',sans-serif; font-size:.75rem;
        color:#8b7aaa; margin-top:.85rem;
    }

    /* ── SECTION HEADER ── */
    .sec-wrap { padding:0 2.5rem 1.4rem; }
    .sec-label {
        font-family:'Inter',sans-serif; font-size:.72rem; font-weight:700;
        color:#7c3aed; letter-spacing:2.5px; text-transform:uppercase;
        margin-bottom:.4rem;
    }
    .sec-title {
        font-family:'Inter',sans-serif; font-size:1.45rem; font-weight:800;
        color:#0f0520; letter-spacing:-.4px;
    }

    /* ── DARK MODULE CARDS ── */
    .mod-card {
        background:#0f1e3d;
        border-radius:22px;
        padding:1.6rem 1.4rem 1.4rem;
        min-height:230px;
        display:flex; flex-direction:column; justify-content:space-between;
        position:relative; overflow:hidden; cursor:pointer;
        transition:background .25s, transform .25s;
    }
    .mod-card:hover { background:#162850; transform:translateY(-4px); }

    /* arrow button top-right */
    .card-arrow {
        position:absolute; top:14px; right:14px;
        width:26px; height:26px; border-radius:50%;
        background:rgba(255,255,255,.1);
        display:flex; align-items:center; justify-content:center;
        font-size:.75rem; color:rgba(255,255,255,.6);
    }

    /* ring graphic area */
    .ring-wrap {
        position:relative; width:84px; height:84px;
        margin:0 auto 1rem;
    }
    .ring-wrap svg { width:84px; height:84px; }
    .ring-number {
        position:absolute; inset:0;
        display:flex; flex-direction:column;
        align-items:center; justify-content:center;
    }
    .rn { font-family:'Inter',sans-serif; font-size:1.6rem;
           font-weight:700; line-height:1; }
    .ru { font-family:'Inter',sans-serif; font-size:.7rem;
           opacity:.65; margin-top:2px; }

    /* per-card accent colours */
    .c-teal   .rn, .c-teal   .ru { color:#5eead4; }
    .c-purple .rn, .c-purple .ru { color:#a78bfa; }
    .c-pink   .rn, .c-pink   .ru { color:#f472b6; }
    .c-orange .rn, .c-orange .ru { color:#fb923c; }

    /* badge */
    .card-badge {
        display:inline-block;
        font-family:'Inter',sans-serif; font-size:.68rem; font-weight:600;
        padding:.2rem .65rem; border-radius:99px; margin-bottom:.6rem;
        letter-spacing:.3px;
    }
    .b-teal   { background:rgba(94,234,212,.15);  color:#5eead4; }
    .b-purple { background:rgba(167,139,250,.15); color:#a78bfa; }
    .b-pink   { background:rgba(244,114,182,.15); color:#f472b6; }
    .b-orange { background:rgba(251,146,60,.15);  color:#fb923c; }

    .card-title {
        font-family:'Inter',sans-serif; font-size:.95rem; font-weight:700;
        color:#e2e8f0; line-height:1.3; margin-bottom:.3rem;
    }
    .card-sub {
        font-family:'Inter',sans-serif; font-size:.78rem;
        color:rgba(226,232,240,.45); line-height:1.4;
    }

    /* Streamlit button (logout) */
    div[data-testid="stButton"] > button {
        background:rgba(255,255,255,.7) !important;
        border:1px solid rgba(200,180,235,.6) !important;
        border-radius:8px !important; color:#44306a !important;
        font-family:'Inter',sans-serif !important;
        font-size:.85rem !important; font-weight:600 !important;
        padding:.45rem 1.1rem !important; box-shadow:none !important;
    }
    div[data-testid="stButton"] > button:hover {
        background:#fff !important;
        border-color:rgba(124,58,237,.4) !important;
        color:#7c3aed !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── NAV ──────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    .nav-link {{
        font-family:'Inter',sans-serif; font-size:.85rem;
        font-weight:500; color:#44306a; cursor:pointer;
        padding:.35rem .6rem; border-radius:7px;
        transition: background .18s, color .18s;
        border: none; background: transparent;
    }}
    .nav-link:hover {{ background:rgba(124,58,237,.1); color:#7c3aed; }}

    /* hide the real Streamlit nav buttons — we show custom HTML ones */
    .nav-btn-row div[data-testid="stButton"] > button {{
        background: transparent !important;
        border: none !important; box-shadow: none !important;
        color: #44306a !important;
        font-family:'Inter',sans-serif !important;
        font-size:.85rem !important; font-weight:500 !important;
        padding:.35rem .6rem !important;
        border-radius:7px !important;
        transition: background .18s, color .18s !important;
        width:auto !important;
    }}
    .nav-btn-row div[data-testid="stButton"] > button:hover {{
        background:rgba(124,58,237,.1) !important;
        color:#7c3aed !important;
        transform:none !important; box-shadow:none !important;
    }}

    /* ── MODAL OVERLAY ── */
    .nm-overlay {{
        position:fixed; inset:0; z-index:1100;
        background:rgba(15,5,35,.55);
        backdrop-filter:blur(6px);
        display:flex; align-items:center; justify-content:center;
        padding:1.5rem;
        animation: nmFadeIn .25s ease both;
    }}
    @keyframes nmFadeIn {{
        from{{opacity:0;}} to{{opacity:1;}}
    }}
    .nm-card {{
        background:#fff;
        border-radius:22px;
        width:min(540px,95vw);
        max-height:85vh;
        overflow-y:auto;
        padding:2.2rem 2rem 1.8rem;
        box-shadow:0 28px 70px rgba(88,28,220,.25);
        border-top:5px solid #7c3aed;
        animation: nmSlideIn .32s cubic-bezier(.22,1,.36,1) both;
        position:relative;
    }}
    @keyframes nmSlideIn {{
        from{{opacity:0; transform:scale(.93) translateY(20px);}}
        to  {{opacity:1; transform:scale(1)   translateY(0);}}
    }}
    .nm-tag {{
        display:inline-block;
        background:rgba(124,58,237,.1); border:1px solid rgba(124,58,237,.25);
        border-radius:99px; padding:.22rem .8rem;
        font-family:'Inter',sans-serif; font-size:.65rem; font-weight:700;
        color:#7c3aed; letter-spacing:2px; text-transform:uppercase;
        margin-bottom:.7rem;
    }}
    .nm-title {{
        font-family:'Inter',sans-serif; font-size:1.5rem; font-weight:900;
        color:#0f0520; letter-spacing:-.4px; margin-bottom:.5rem;
    }}
    .nm-body {{
        font-family:'Inter',sans-serif; font-size:.88rem;
        color:#3d2a5a; line-height:1.7;
    }}
    .nm-divider {{
        border:none; border-top:1px solid #ede9fe; margin:1.2rem 0;
    }}
    .nm-row {{
        display:flex; align-items:flex-start; gap:.8rem;
        margin-bottom:.85rem;
    }}
    .nm-icon {{
        font-size:1.4rem; flex-shrink:0; margin-top:.05rem;
    }}
    .nm-row-body {{
        font-family:'Inter',sans-serif; font-size:.84rem; color:#3d2a5a; line-height:1.55;
    }}
    .nm-row-title {{
        font-family:'Inter',sans-serif; font-size:.84rem; font-weight:700;
        color:#1a0533; margin-bottom:.15rem;
    }}
    .nm-badge {{
        display:inline-block; padding:.2rem .7rem; border-radius:99px;
        font-family:'Inter',sans-serif; font-size:.72rem; font-weight:700;
        letter-spacing:.4px;
    }}
    .nm-badge-free {{ background:#d1fae5; color:#065f46; }}
    .nm-badge-soon {{ background:#fef3c7; color:#92400e; }}
    .nm-close-hint {{
        font-family:'Inter',sans-serif; font-size:.7rem; color:#a78bfa;
        text-align:center; margin-top:1.2rem;
    }}

    /* close button for modals — fixed floating above everything */
    .nm-close-btn-wrap {{
        position:fixed !important;
        top:1.2rem !important; right:1.5rem !important;
        z-index:1300 !important;
    }}
    
    </style>

    <div class="top-nav">
        <div class="nav-logo">
            <div class="logo-box">🎓</div> <span style="color:#000">SCIS</span>
        </div>
        <div class="nav-links nav-btn-row" id="nav-links-html">
            <!-- real buttons rendered below via Streamlit -->
        </div>
        <div class="nav-right">
            <span class="nav-user">👤 {uname}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit nav buttons (rendered inline, styled via CSS above)
    nav_cols = st.columns([3, 1, 1, 3])
    with nav_cols[1]:
        if st.button("Product",  key="nav_product"):
            st.session_state.nav_modal = "product"
            st.rerun()
    with nav_cols[2]:
        if st.button("Pricing",  key="nav_pricing"):
            st.session_state.nav_modal = "pricing"
            st.rerun()

    # ── HERO ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
        <div>
            <div class="hero-tag">✦ AI-Powered Career Platform</div>
            <div class="hero-title">Students,<br>welcome.</div>
        </div>
        <div class="hero-right">
            <div class="hero-desc">
                SCIS is an intelligent career platform built for students —
                that puts the focus on your skills, your growth,
                and your future.
            </div>
            <div class="hero-note">Powered by machine learning · Real-time predictions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SECTION LABEL ────────────────────────────────────────────
    st.markdown("""
    <div class="sec-wrap">
        <div class="sec-label">Core Modules</div>
        <div class="sec-title">Everything you need, in one place.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 DARK MODULE CARDS ──────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    # helper — ring SVG
    def ring_svg(color, dash, gap_val):
        return f"""
        <svg viewBox="0 0 84 84" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="42" cy="42" r="34"
            stroke="{color}" stroke-opacity=".15" stroke-width="9"/>
          <circle cx="42" cy="42" r="34"
            stroke="{color}" stroke-width="9"
            stroke-dasharray="{dash} {gap_val}"
            stroke-dashoffset="42" stroke-linecap="round"/>
        </svg>"""

    with c1:
        st.markdown(f"""
        <style>
        /* Make the Module 01 Streamlit button invisible and cover the entire card */
        div[data-testid="column"]:nth-child(1) div[data-testid="stButton"] > button {{
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            z-index: 10 !important;
            border-radius: 22px !important;
            margin: 0 !important; padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:nth-child(1) {{
            position: relative !important;
        }}
        </style>
        <div class="mod-card c-teal" style="cursor:pointer;">
            <div class="card-arrow">→</div>
            <div class="ring-wrap">
                {ring_svg("#5eead4", 152, 61)}
                <div class="ring-number">
                    <span class="rn">01</span>
                    <span class="ru">module</span>
                </div>
            </div>
            <div>
                <span class="card-badge b-teal">Active</span>
                <div class="card-title">Career<br>Prediction</div>
                <div class="card-sub">Placement probability scoring</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Module 01", key="btn_career",
                     help="Click to open Career Prediction"):
            st.session_state.stage = "career_prediction"
            st.rerun()

    with c2:
        st.markdown(f"""
        <style>
        div[data-testid="column"]:nth-child(2) div[data-testid="stButton"] > button {{
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            z-index: 10 !important;
            border-radius: 22px !important;
            margin: 0 !important; padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:nth-child(2) {{
            position: relative !important;
        }}
        </style>
        <div class="mod-card c-purple" style="cursor:pointer;">
            <div class="card-arrow">→</div>
            <div class="ring-wrap">
                {ring_svg("#a78bfa", 128, 85)}
                <div class="ring-number">
                    <span class="rn">02</span>
                    <span class="ru">module</span>
                </div>
            </div>
            <div>
                <span class="card-badge b-purple">New</span>
                <div class="card-title">Improvement<br>Recommendations</div>
                <div class="card-sub">Skill gap & learning roadmap</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Module 02", key="btn_improve",
                     help="Click to open Improvement Recommendations"):
            st.session_state.stage = "improvement_recommendations"
            st.rerun()

    with c3:
        st.markdown(f"""
        <style>
        div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] > button {{
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            z-index: 10 !important;
            border-radius: 22px !important;
            margin: 0 !important; padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:nth-child(3) {{
            position: relative !important;
        }}
        </style>
        <div class="mod-card c-pink" style="cursor:pointer;">
            <div class="card-arrow">→</div>
            <div class="ring-wrap">
                {ring_svg("#f472b6", 105, 108)}
                <div class="ring-number">
                    <span class="rn">03</span>
                    <span class="ru">module</span>
                </div>
            </div>
            <div>
                <span class="card-badge b-pink">Active</span>
                <div class="card-title">Resume<br>Analysis</div>
                <div class="card-sub">Job-role based skill analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Module 03", key="mod3_btn", help="Click to open Resume Analysis"):
            st.session_state.stage = "resume_analysis"
            st.rerun()

    with c4:
        st.markdown(f"""
        <style>
        div[data-testid="column"]:nth-child(4) div[data-testid="stButton"] > button {{
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            z-index: 10 !important;
            border-radius: 22px !important;
            margin: 0 !important; padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}
        div[data-testid="column"]:nth-child(4) {{
            position: relative !important;
        }}
        </style>
        <div class="mod-card c-orange" style="cursor:pointer;">
            <div class="card-arrow">→</div>
            <div class="ring-wrap">
                {ring_svg("#fb923c", 168, 45)}
                <div class="ring-number">
                    <span class="rn">04</span>
                    <span class="ru">module</span>
                </div>
            </div>
            <div>
                <span class="card-badge b-orange">New</span>
                <div class="card-title">Interview<br>Prep Bot</div>
                <div class="card-sub">AI-powered interview questions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Module 04", key="mod4_btn", help="Click to open Interview Prep Bot"):
            st.session_state.stage = "interview_prep"
            st.rerun()

    # ── LOGOUT ───────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([3, 1, 3])
    with mid:
        if st.button("🚪  Logout"):
            st.session_state.stage    = "login"
            st.session_state.username = ""
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    #  NAV MODALS — Product / Modules / Pricing / Support
    # ══════════════════════════════════════════════════════════════
    modal = st.session_state.get("nav_modal")

    # Inject close-button CSS only when a modal is active (won't bleed to login)
    if modal:
        st.markdown("""
        <style>
        div[data-testid="stButton"]:has(button[kind="primary"]) {
            position: fixed !important;
            top: 1.1rem !important; right: 1.4rem !important;
            bottom: auto !important; left: auto !important;
            transform: none !important;
            z-index: 1300 !important; width: auto !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) > button {
            width: auto !important;
            background: #f5c518 !important;
            color: #1a3d25 !important; border: none !important;
            border-radius: 50px !important;
            font-family: 'Poppins',sans-serif !important;
            font-size: .88rem !important; font-weight: 800 !important;
            padding: .5rem 1.5rem !important;
            box-shadow: 0 4px 18px rgba(0,0,0,.35) !important;
            letter-spacing: .3px !important;
            transition: all .2s ease !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {
            background: #ffe03a !important;
            transform: scale(1.04) !important;
        }
        </style>
        """, unsafe_allow_html=True)

    if modal == "product":
        st.session_state.stage = "product"
        st.session_state.nav_modal = None
        st.rerun()

    elif modal == "pricing":
        st.session_state.stage = "pricing"
        st.session_state.nav_modal = None
        st.rerun()

    elif modal == "support":
        st.markdown("""
        <div class="nm-overlay">
          <div class="nm-card">
            <div class="nm-tag">Support</div>
            <div class="nm-title">Help & Support 🛠️</div>
            <div class="nm-body">
              Having trouble? Find answers below or reach out to the SCIS team.
            </div>
            <hr class="nm-divider">
            <div class="nm-row">
              <div class="nm-icon">🔑</div>
              <div><div class="nm-row-title">Login Credentials</div>
              <div class="nm-row-body">
                Student: <b>student@scis.com</b> / <b>career123</b><br>
                Admin: <b>admin@scis.com</b> / <b>admin2024</b><br>
                Demo: <b>demo@scis.com</b> / <b>demo</b>
              </div></div>
            </div>
            <div class="nm-row">
              <div class="nm-icon">❓</div>
              <div><div class="nm-row-title">How does the prediction work?</div>
              <div class="nm-row-body">
                SCIS uses a <b>Random Forest ML model</b> trained on student placement
                data. It scores your inputs against key placement criteria and outputs
                a probability percentage with personalised recommendations.
              </div></div>
            </div>
            <div class="nm-row">
              <div class="nm-icon">📁</div>
              <div><div class="nm-row-title">Model not loading?</div>
              <div class="nm-row-body">
                Make sure <b>model (1).pkl</b> and <b>scaler (1).pkl</b> are placed
                in the same folder as <b>app.py</b>. The system will fall back to
                rule-based scoring if the model files are missing.
              </div></div>
            </div>
            <div class="nm-row">
              <div class="nm-icon">🏢</div>
              <div><div class="nm-row-title">Project Info</div>
              <div class="nm-row-body">
                Developed at <b>Alpha IT Managed Services</b> · Sector 67<br>
                BTEC Final Year Project · Semester 8 · CSE Department
              </div></div>
            </div>
            <p class="nm-close-hint">Click the button below to close</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✕  Close", key="nm_close_support", type="primary"):
            st.session_state.nav_modal = None
            st.rerun()



# ══════════════════════════════════════════════════════════════
#  PAGE 4 — CAREER PREDICTION MODULE  (v3 — clean UI)
# ══════════════════════════════════════════════════════════════
def show_career_prediction():

    # initialise popup state
    if "cp_show_result" not in st.session_state:
        st.session_state.cp_show_result = False
    if "cp_result" not in st.session_state:
        st.session_state.cp_result = {}

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }

    /* light blue background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(160deg,#e8f4fd 0%,#dbeafe 40%,#eff6ff 100%) !important;
    }

    /* top bar */
    .cp-topbar {
        display:flex; align-items:center; justify-content:space-between;
        padding:.9rem 2.2rem; background:#fff;
        border-bottom:1px solid #bfdbfe;
        position:sticky; top:0; z-index:100;
    }
    .cp-topbar-left { display:flex; align-items:center; gap:.7rem; }
    .cp-logo-box {
        width:30px; height:30px; background:#1e40af;
        border-radius:7px; display:flex; align-items:center;
        justify-content:center; font-size:1rem; color:#fff;
    }
    .cp-logo-txt {
        font-family:'Inter',sans-serif; font-size:1rem;
        font-weight:700; color:#1e3a5f;
    }

    /* page header */
    .cp-header {
        background:linear-gradient(135deg,#1e40af 0%,#2563eb 55%,#60a5fa 100%);
        padding:2.2rem 2.5rem 1.8rem;
    }
    .cp-header-tag {
        font-family:'Inter',sans-serif; font-size:.7rem; font-weight:600;
        color:#bfdbfe; letter-spacing:2.5px; text-transform:uppercase;
        display:block; margin-bottom:.5rem;
    }
    .cp-header-title {
        font-family:'Inter',sans-serif; font-size:1.85rem; font-weight:800;
        color:#fff; letter-spacing:-.4px; margin-bottom:.35rem;
    }
    .cp-header-sub {
        font-family:'Inter',sans-serif; font-size:.88rem;
        color:#bfdbfe; line-height:1.55; max-width:520px;
    }

    /* section card */
    .cp-section {
        background:#fff; border-radius:14px; border:1px solid #bfdbfe;
        padding:1.5rem 1.8rem; margin-bottom:1rem;
    }
    .cp-section-title {
        font-family:'Inter',sans-serif; font-size:.7rem; font-weight:700;
        color:#2563eb; letter-spacing:2px; text-transform:uppercase;
        margin-bottom:.9rem; padding-bottom:.5rem;
        border-bottom:1px solid #dbeafe;
    }

    /* input labels */
    div[data-testid="stSlider"] > label,
    div[data-testid="stSelectbox"] > label,
    div[data-testid="stTextInput"] > label,
    div[data-testid="stNumberInput"] > label {
        font-family:'Inter',sans-serif !important;
        font-size:.82rem !important; font-weight:600 !important;
        color:#1e3a5f !important;
    }
    div[data-testid="stSelectbox"] > div > div {
        border-color:#bfdbfe !important; border-radius:9px !important;
        font-family:'Inter',sans-serif !important; font-size:.88rem !important;
    }
    div[data-testid="stNumberInput"] input {
        border-color:#bfdbfe !important; border-radius:9px !important;
        font-family:'Inter',sans-serif !important; color:#1e3a5f !important;
    }
    div[data-testid="stTextInput"] input {
        border-color:#bfdbfe !important; border-radius:9px !important;
        font-family:'Inter',sans-serif !important;
        color:#1e3a5f !important; background:#f8fbff !important;
    }

    /* predict button */
    div[data-testid="stButton"] > button {
        width:100% !important;
        background:linear-gradient(135deg,#1e40af,#3b82f6) !important;
        border:none !important; border-radius:12px !important;
        color:#fff !important; font-family:'Inter',sans-serif !important;
        font-size:.95rem !important; font-weight:700 !important;
        padding:.8rem 1.5rem !important; margin-top:.4rem !important;
        box-shadow:0 4px 16px rgba(59,130,246,.3) !important;
        letter-spacing:.3px !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform:translateY(-2px) !important;
        box-shadow:0 8px 24px rgba(59,130,246,.4) !important;
    }
    /* hide the internal JS-trigger dismiss button */
    button[kind="secondary"]:has(p:contains("__dismiss_result__")),
    div[data-testid="stButton"] > button[aria-label="__dismiss_result__"] {
        display:none !important;
    }

    /* ── RESULT DISPLAY (handled inline) ── */

    /* result content */
    .res-verdict {
        font-family:'Inter',sans-serif; font-size:1.35rem; font-weight:800;
        text-align:center; margin-bottom:.3rem;
    }
    .res-pct {
        font-family:'Inter',sans-serif; font-size:3.8rem; font-weight:900;
        line-height:1; text-align:center; margin:.3rem 0;
    }
    .res-label {
        font-family:'Inter',sans-serif; font-size:.82rem;
        color:#64748b; text-align:center; margin-bottom:1rem;
    }
    .res-status-badge {
        display:block; width:fit-content; margin:0 auto .9rem;
        font-family:'Inter',sans-serif; font-size:.88rem; font-weight:700;
        padding:.4rem 1.4rem; border-radius:99px; letter-spacing:.4px;
    }
    .gauge-track {
        background:#e2e8f0; border-radius:99px; height:10px;
        overflow:hidden; margin:0 auto 1.2rem; max-width:340px;
    }
    .gauge-fill { height:100%; border-radius:99px; }
    .flags-wrap {
        display:flex; flex-wrap:wrap; gap:.45rem;
        justify-content:center; margin-bottom:1rem;
    }
    .flag-chip {
        font-family:'Inter',sans-serif; font-size:.7rem; font-weight:600;
        padding:.25rem .65rem; border-radius:99px;
    }
    .flag-ok   { background:#d1fae5; color:#065f46; }
    .flag-warn { background:#fef3c7; color:#92400e; }
    .flag-crit { background:#fee2e2; color:#991b1b; }

    /* placed */
    .verdict-placed  { color:#065f46; }
    .pct-placed      { color:#10b981; }
    .badge-placed    { background:#d1fae5; color:#065f46; border:1.5px solid #6ee7b7; }
    .gauge-placed    { background:linear-gradient(90deg,#34d399,#10b981); }
    /* uncertain */
    .verdict-mod     { color:#92400e; }
    .pct-mod         { color:#f59e0b; }
    .badge-mod       { background:#fef3c7; color:#92400e; border:1.5px solid #fcd34d; }
    .gauge-mod       { background:linear-gradient(90deg,#fbbf24,#f59e0b); }
    /* not placed */
    .verdict-low     { color:#991b1b; }
    .pct-low         { color:#ef4444; }
    .badge-low       { background:#fee2e2; color:#991b1b; border:1.5px solid #fca5a5; }
    .gauge-low       { background:linear-gradient(90deg,#f87171,#ef4444); }

    .salary-box {
        background:linear-gradient(135deg,#eff6ff,#dbeafe);
        border:1px solid #bfdbfe; border-radius:12px;
        padding:.9rem 1.2rem; margin-top:.8rem; text-align:center;
    }
    .salary-lbl { font-family:'Inter',sans-serif; font-size:.72rem; color:#2563eb; font-weight:600; letter-spacing:1px; text-transform:uppercase; }
    .salary-val { font-family:'Inter',sans-serif; font-size:1.55rem; font-weight:800; color:#1e40af; }
    </style>
    """, unsafe_allow_html=True)

    # ── TOP BAR ──────────────────────────────────────────────────
    st.markdown("""
    <div class="cp-topbar">
        <div class="cp-topbar-left">
            <div style="font-size:1.2rem;">🎓</div>
            <span class="cp-logo-txt" style="color:#000 !important;">SCIS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("Back"):
            st.session_state.stage = "dashboard"
            st.session_state.cp_show_result = False
            st.rerun()

    # ── HEADER ───────────────────────────────────────────────────
    st.markdown("""
    <div class="cp-header">
        <span class="cp-header-tag">Module 01</span>
        <div class="cp-header-title">Student Placement Prediction</div>
        <div class="cp-header-sub">
            Fill in your academic profile and skill details below,
            then click Predict to see your placement probability.
        </div>
    </div><br>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════
    #  INPUT SECTIONS
    # ════════════════════════════════════════

    # SECTION A — Basic Info
    st.markdown('<div class="cp-section"><div class="cp-section-title">Basic Information</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        student_id = st.text_input("Student ID", placeholder="e.g. STU2024001")
    with col2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    with col3:
        extracurricular = st.selectbox("Extracurricular Activities", ["Yes", "No"])
    st.markdown('</div>', unsafe_allow_html=True)

    # SECTION B — Academic Performance
    st.markdown('<div class="cp-section"><div class="cp-section-title">Academic Performance</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        ssc_pct = st.slider("SSC Percentage (%)", 0.0, 100.0, 70.0, 0.5)
    with col2:
        hsc_pct = st.slider("HSC Percentage (%)", 0.0, 100.0, 70.0, 0.5)
    with col3:
        degree_pct = st.slider("Degree Percentage (%)", 0.0, 100.0, 65.0, 0.5)

    col4, col5 = st.columns(2)
    with col4:
        cgpa = st.slider("CGPA (out of 10)", 0.0, 10.0, 7.0, 0.1)
    with col5:
        attendance = st.slider("Attendance Percentage (%)", 0.0, 100.0, 75.0, 0.5)
    st.markdown('</div>', unsafe_allow_html=True)

    # SECTION C — Entrance & Skills
    st.markdown('<div class="cp-section"><div class="cp-section-title">Entrance Exam and Skill Scores</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        entrance_score = st.slider("Entrance Exam Score", 0.0, 100.0, 65.0, 0.5)
    with col2:
        tech_score = st.slider("Technical Skill Score (%)", 0.0, 100.0, 65.0, 0.5)
    with col3:
        soft_score = st.slider("Soft Skill Score (%)", 0.0, 100.0, 65.0, 0.5)
    st.markdown('</div>', unsafe_allow_html=True)

    # SECTION D — Experience
    st.markdown('<div class="cp-section"><div class="cp-section-title">Experience, Projects and Certifications</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        internships = st.number_input("Internship Count", min_value=0, max_value=15, value=1, step=1)
    with col2:
        live_projects = st.number_input("Live Projects", min_value=0, max_value=20, value=1, step=1)
    with col3:
        certifications = st.number_input("Certifications", min_value=0, max_value=20, value=2, step=1)
    with col4:
        backlogs = st.number_input("Number of Backlogs", min_value=0, max_value=20, value=0, step=1)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PREDICT BUTTON ────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        predict = st.button("Predict My Placement")

    # ════════════════════════════════════════
    #  PREDICTION LOGIC
    # ════════════════════════════════════════
    if predict:
        IMPORTANT = [
            ("CGPA",                  cgpa,          6.0,  "gte", 18),
            ("Entrance Exam Score",   entrance_score,60.0, "gte", 14),
            ("Technical Skill Score", tech_score,    60.0, "gte", 14),
            ("Soft Skill Score",      soft_score,    60.0, "gte", 12),
            ("Attendance",            attendance,    65.0, "gte", 10),
            ("Internship Count",      internships,   1,    "gte", 12),
            ("Live Projects",         live_projects, 1,    "gte", 10),
            ("Certifications",        certifications,2,    "gte",  8),
            ("Backlogs",              backlogs,      0,    "eq",  12),
        ]

        passed, failed, raw_score = [], [], 0

        for feat, val, thresh, cond, w in IMPORTANT:
            met = (val >= thresh) if cond == "gte" else (val == thresh)
            if met:
                passed.append(feat)
                if cond == "gte" and thresh > 0:
                    raw_score += w * min(1 + (val - thresh) / thresh * 0.15, 1.15)
                else:
                    raw_score += w
            else:
                failed.append(feat)
                if cond == "gte" and thresh > 0:
                    raw_score += w * min(val / thresh, 1.0) * 0.5

        total_imp_weight = sum(w for *_, w in IMPORTANT)
        bonus = (3 if extracurricular == "Yes" else 0) + \
                (1 if ssc_pct >= 60 else 0) + \
                (1 if hsc_pct >= 60 else 0) + \
                (2 if degree_pct >= 60 else 0)

        max_possible = total_imp_weight * 1.15 + 7
        pct = min(round(((raw_score + bonus) / max_possible) * 100, 1), 99.0)
        pct = max(pct, 2.0)
        if backlogs > 0:
            pct = min(pct, 35.0)

        if pct >= 70:
            verdict, status  = "Likely to be Placed", "PLACED"
            v_cls, p_cls, b_cls, g_cls = "verdict-placed","pct-placed","badge-placed","gauge-placed"
        elif pct >= 45:
            verdict, status  = "Moderate Placement Chances", "UNCERTAIN"
            v_cls, p_cls, b_cls, g_cls = "verdict-mod","pct-mod","badge-mod","gauge-mod"
        else:
            verdict, status  = "Low Placement Chances", "NOT PLACED"
            v_cls, p_cls, b_cls, g_cls = "verdict-low","pct-low","badge-low","gauge-low"

        sal = None
        if pct >= 70:
            sal = "8 - 12 LPA" if cgpa >= 8.5 else \
                  "5 - 8 LPA"  if cgpa >= 7.5 else \
                  "3.5 - 5 LPA" if cgpa >= 6.5 else "2.5 - 3.5 LPA"

        flag_html = "".join(
            f'<span class="flag-chip flag-ok">{f}</span>' for f in passed
        ) + "".join(
            f'<span class="flag-chip flag-{"crit" if f=="Backlogs" else "warn"}">{f}</span>'
            for f in failed
        )

        salary_html = f"""
        <div class="salary-box">
            <div class="salary-lbl">Estimated Starting Salary</div>
            <div class="salary-val">Rs {sal}</div>
        </div>""" if sal else ""

        st.session_state.cp_result = {
            "pct": pct, "verdict": verdict, "status": status,
            "v_cls": v_cls, "p_cls": p_cls, "b_cls": b_cls, "g_cls": g_cls,
            "flag_html": flag_html, "salary_html": salary_html,
        }
        # ── FIREBASE: save placement prediction ───────────────
        if FIREBASE_ON:
            save_placement_prediction(
                username   = st.session_state.get("username", "unknown"),
                inputs     = {
                    "cgpa": cgpa, "ssc_pct": ssc_pct, "hsc_pct": hsc_pct,
                    "degree_pct": degree_pct, "attendance": attendance,
                    "gender": gender, "extracurricular": extracurricular,
                },
                result_pct = pct,
                verdict    = verdict,
                salary     = sal if sal else "Not estimated",
            )
        st.session_state.cp_show_result = True
        st.rerun()

    # ── POPUP RESULT ──────────────────────────────────────────────
    if st.session_state.get("cp_show_result"):
        r = st.session_state.cp_result

        # Inject CSS: full-screen transparent dismiss button sits BEHIND popup-box
        # and a styled popup-box sits on top via z-index
        st.markdown(f"""
        <style>
        /* Full-screen dismiss layer — sits under the popup card */
        div[data-testid="stButton"].dismiss-layer > button {{
            position: fixed !important;
            inset: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(15,30,70,.55) !important;
            backdrop-filter: blur(4px) !important;
            border: none !important;
            border-radius: 0 !important;
            z-index: 998 !important;
            cursor: pointer !important;
            color: transparent !important;
            box-shadow: none !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0 !important;
        }}
        /* Popup card floats above the dismiss layer */
        .popup-float {{
            position: fixed !important;
            inset: 0 !important;
            z-index: 999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 1.5rem !important;
            pointer-events: none !important;
        }}
        .popup-box {{
            pointer-events: all !important;
            background: #fff;
            border-radius: 22px;
            width: min(500px, 94vw);
            max-height: 88vh;
            overflow-y: auto;
            padding: 2.2rem 2rem 1.8rem;
            box-shadow: 0 24px 60px rgba(10,20,80,.35);
            animation: popIn .35s cubic-bezier(.22,1,.36,1) both;
        }}
        @keyframes popIn {{
            from {{ opacity:0; transform:scale(.92) translateY(20px); }}
            to   {{ opacity:1; transform:scale(1)   translateY(0);    }}
        }}
        </style>

        <div class="popup-float">
          <div class="popup-box">
            <div class="res-verdict {r['v_cls']}">{r['verdict']}</div>
            <span class="res-status-badge {r['b_cls']}">Placement Status: {r['status']}</span>
            <div class="res-pct {r['p_cls']}">{r['pct']}%</div>
            <div class="res-label">Estimated Placement Probability</div>
            <div class="gauge-track">
              <div class="gauge-fill {r['g_cls']}" style="width:{r['pct']}%;"></div>
            </div>
            <div class="flags-wrap">{r['flag_html']}</div>
            {r['salary_html']}
            <p style="font-family:'Inter',sans-serif;font-size:.75rem;color:#94a3b8;text-align:center;margin-top:1rem;">
                Tap anywhere outside this card to close
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # This Streamlit button IS the full-screen backdrop — clicking it dismisses
        dismiss_clicked = st.button(" ", key="dismiss_overlay")
        # Apply the dismiss-layer class via JS (Streamlit doesn't support custom classes on buttons directly)
        st.markdown("""
        <script>
        (function() {
            // Find the last button rendered (our dismiss button) and tag its parent
            var allBtns = window.parent.document.querySelectorAll(
                '[data-testid="stAppViewContainer"] button'
            );
            // The dismiss button has a single space as text
            for (var b of allBtns) {
                if (b.innerText === ' ' || b.innerText === '') {
                    b.parentElement.classList.add('dismiss-layer');
                    b.style.cssText = [
                        'position:fixed','inset:0','width:100vw','height:100vh',
                        'background:rgba(15,30,70,.55)','backdrop-filter:blur(4px)',
                        'border:none','border-radius:0','z-index:998',
                        'cursor:pointer','color:transparent','box-shadow:none',
                        'margin:0','padding:0','font-size:0'
                    ].join('!important;') + '!important';
                    break;
                }
            }
        })();
        </script>
        """, unsafe_allow_html=True)

        if dismiss_clicked:
            st.session_state.cp_show_result = False
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════
#  PAGE 5 — MODULE 02: IMPROVEMENT RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════
def show_improvement_recommendations():
    import numpy as np

    if "ir_show_result" not in st.session_state:
        st.session_state.ir_show_result = False
    if "ir_result" not in st.session_state:
        st.session_state.ir_result = {}

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');

    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer { display:none !important; }
    .block-container { padding:0 !important; max-width:100% !important; }

    /* white background */
    [data-testid="stAppViewContainer"] {
        background: #ffffff !important;
    }
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] section {
        background: #ffffff !important;
    }

    /* ── top bar ── */
    .ir-topbar {
        display:flex; align-items:center; gap:.6rem;
        padding:1rem 2.2rem;
        background:#fff;
        border-bottom: 2px solid #7c3aed;
    }
    .ir-logo-box {
        width:34px; height:34px; background:#7c3aed;
        border-radius:9px; display:flex; align-items:center;
        justify-content:center; font-size:1.1rem; color:#fff;
    }
    .ir-logo-txt {
        font-family:'Poppins',sans-serif; font-size:1.05rem;
        font-weight:700; color:#4c1d95;
    }
    .ir-logo-sub {
        font-family:'Poppins',sans-serif; font-size:.72rem;
        font-weight:500; color:#8b5cf6; margin-left:.3rem;
    }

    /* ── page header banner ── */
    .ir-banner {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 50%, #5b21b6 100%);
        padding: 2.2rem 2.5rem 2rem;
    }
    .ir-banner-tag {
        display:inline-block;
        background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35);
        border-radius:99px; padding:.25rem .85rem;
        font-family:'Poppins',sans-serif; font-size:.68rem; font-weight:700;
        color:#ede9fe; letter-spacing:2px; text-transform:uppercase; margin-bottom:.75rem;
    }
    .ir-banner-title {
        font-family:'Poppins',sans-serif; font-size:clamp(1.5rem,3.5vw,2.2rem);
        font-weight:800; color:#fff; letter-spacing:-.4px; margin-bottom:.4rem;
    }
    .ir-banner-sub {
        font-family:'Poppins',sans-serif; font-size:.88rem;
        color:rgba(237,233,254,.85); line-height:1.6; max-width:560px;
    }

    /* ── section cards ── */
    .ir-section {
        background: #fff;
        border: 1.5px solid #ddd6fe;
        border-left: 4px solid #7c3aed;
        border-radius: 14px;
        padding: 1.4rem 1.6rem 1rem;
        margin: 0 1.2rem 1.1rem;
        box-shadow: 0 2px 12px rgba(124,58,237,.07);
    }
    .ir-section-title {
        font-family:'Poppins',sans-serif; font-size:.72rem; font-weight:700;
        color:#7c3aed; text-transform:uppercase; letter-spacing:2px;
        margin-bottom:1rem; padding-bottom:.5rem;
        border-bottom: 1px solid #ede9fe;
        display:flex; align-items:center; gap:.4rem;
    }

    /* ── input styling ── */
    div[data-testid="stSlider"] > label,
    div[data-testid="stNumberInput"] > label,
    div[data-testid="stSelectbox"] > label,
    div[data-testid="stRadio"] > label {
        font-family:'Poppins',sans-serif !important;
        font-size:.82rem !important; font-weight:600 !important;
        color:#4c1d95 !important;
    }
    /* slider track accent */
    div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background:#7c3aed !important;
        border-color:#7c3aed !important;
    }
    div[data-testid="stNumberInput"] input {
        border-color:#c4b5fd !important; border-radius:9px !important;
        font-family:'Poppins',sans-serif !important; color:#4c1d95 !important;
        font-weight:600 !important;
    }
    div[data-testid="stSelectbox"] > div > div {
        border-color:#c4b5fd !important; border-radius:9px !important;
        font-family:'Poppins',sans-serif !important;
        color:#4c1d95 !important; font-weight:600 !important;
    }
    div[data-testid="stRadio"] span {
        font-family:'Poppins',sans-serif !important;
        color:#4c1d95 !important; font-weight:500 !important;
    }

    /* ── analyse button ── */
    div[data-testid="stButton"] > button {
        width:100% !important;
        background: linear-gradient(135deg,#7c3aed 0%,#6d28d9 100%) !important;
        border:none !important; border-radius:14px !important;
        color:#fff !important; font-family:'Poppins',sans-serif !important;
        font-size:1rem !important; font-weight:700 !important;
        padding:.85rem 2rem !important;
        box-shadow: 0 6px 22px rgba(124,58,237,.38) !important;
        letter-spacing:.5px !important; transition:all .25s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform:translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(109,40,217,.45) !important;
    }

    /* ── RESULT POPUP overlay ── */
    .ir-popup-float {
        position:fixed !important; inset:0 !important;
        z-index:999 !important; display:flex !important;
        align-items:center !important; justify-content:center !important;
        padding:1.2rem !important; pointer-events:none !important;
    }
    .ir-popup-box {
        pointer-events:all !important;
        background:#fff;
        border-radius:24px;
        width:min(580px, 96vw); max-height:88vh;
        overflow-y:auto;
        padding:2rem 1.8rem 1.6rem;
        box-shadow: 0 30px 80px rgba(88,28,220,.28);
        border-top: 5px solid #7c3aed;
        animation: irPop .38s cubic-bezier(.22,1,.36,1) both;
    }
    @keyframes irPop {
        from { opacity:0; transform:scale(.9) translateY(24px); }
        to   { opacity:1; transform:scale(1)  translateY(0);    }
    }

    /* result text styles */
    .ir-res-verdict {
        font-family:'Poppins',sans-serif; font-size:1.25rem; font-weight:800;
        text-align:center; margin-bottom:.3rem;
    }
    .ir-res-pct {
        font-family:'Poppins',sans-serif; font-size:4.2rem; font-weight:900;
        line-height:1; text-align:center; margin:.25rem 0;
    }
    .ir-res-label {
        font-family:'Poppins',sans-serif; font-size:.78rem;
        color:#a78bfa; text-align:center; margin-bottom:.8rem;
        font-weight:500;
    }
    .ir-badge {
        display:block; width:fit-content; margin:0 auto .9rem;
        font-family:'Poppins',sans-serif; font-size:.84rem; font-weight:700;
        padding:.38rem 1.4rem; border-radius:99px; letter-spacing:.5px;
    }
    .ir-gauge-track {
        background:#ede9fe; border-radius:99px; height:12px;
        overflow:hidden; margin:0 auto 1.5rem; max-width:380px;
    }
    .ir-gauge-fill { height:100%; border-radius:99px; transition:width .8s ease; }

    /* color variants */
    .ir-green  { color:#065f46; }
    .ir-pct-g  { color:#10b981; }
    .ir-bdg-g  { background:#d1fae5; color:#065f46; border:1.5px solid #6ee7b7; }
    .ir-gfill-g{ background:linear-gradient(90deg,#34d399,#10b981); }

    .ir-yellow { color:#78350f; }
    .ir-pct-y  { color:#d97706; }
    .ir-bdg-y  { background:#fef3c7; color:#78350f; border:1.5px solid #fcd34d; }
    .ir-gfill-y{ background:linear-gradient(90deg,#fbbf24,#d97706); }

    .ir-red    { color:#7f1d1d; }
    .ir-pct-r  { color:#dc2626; }
    .ir-bdg-r  { background:#fee2e2; color:#7f1d1d; border:1.5px solid #fca5a5; }
    .ir-gfill-r{ background:linear-gradient(90deg,#f87171,#dc2626); }

    /* recommendations */
    .rec-section-hdr {
        font-family:'Poppins',sans-serif; font-size:.9rem; font-weight:800;
        color:#4c1d95; margin:1.3rem 0 .7rem;
        border-left:3px solid #7c3aed; padding-left:.6rem;
    }
    .rec-card {
        border-radius:12px; padding:.85rem 1rem .8rem;
        margin-bottom:.55rem; display:flex; gap:.75rem; align-items:flex-start;
    }
    .rec-card.crit  { background:#fdf2f8; border:1px solid #f9a8d4; }
    .rec-card.warn  { background:#fffbeb; border:1px solid #fde68a; }
    .rec-card.good  { background:#ecfdf5; border:1px solid #6ee7b7; }

    .rec-icon { font-size:1.25rem; line-height:1; flex-shrink:0; margin-top:.1rem; }
    .rec-body { flex:1; }
    .rec-tag {
        display:inline-block; font-family:'Poppins',sans-serif;
        font-size:.62rem; font-weight:700; padding:.15rem .55rem;
        border-radius:99px; letter-spacing:.6px; text-transform:uppercase;
        margin-bottom:.25rem;
    }
    .tag-c { background:#fce7f3; color:#be185d; }
    .tag-w { background:#fef9c3; color:#a16207; }
    .tag-g { background:#d1fae5; color:#065f46; }
    .rec-text {
        font-family:'Poppins',sans-serif; font-size:.80rem;
        color:#3730a3; line-height:1.55; margin:0;
    }

    .ir-close-hint {
        font-family:'Poppins',sans-serif; font-size:.7rem;
        color:#a78bfa; text-align:center; margin-top:1rem;
    }

    /* dismiss overlay button */
    div[data-testid="stButton"].ir-dismiss > button {
        position:fixed !important; inset:0 !important;
        width:100vw !important; height:100vh !important;
        background:rgba(46,16,101,.5) !important;
        backdrop-filter:blur(5px) !important;
        border:none !important; border-radius:0 !important;
        z-index:998 !important; color:transparent !important;
        box-shadow:none !important; margin:0 !important;
        padding:0 !important; font-size:0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── TOP BAR ──────────────────────────────────────────────────
    st.markdown("""
    <div class="ir-topbar">
        <div style="font-size:1.2rem;">🎓</div>
        <span class="ir-logo-txt" style="color:#000 !important;">SCIS</span>
        <span class="ir-logo-sub">· Student Career Intelligence System</span>
    </div>
    """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", key="ir_back_btn"):
            st.session_state.stage = "dashboard"
            st.session_state.ir_show_result = False
            st.rerun()

    # ── BANNER ───────────────────────────────────────────────────
    st.markdown("""
    <div class="ir-banner">
        <div class="ir-banner-tag">Module 02 · New</div>
        <div class="ir-banner-title">Improvement Recommendations</div>
        <div class="ir-banner-sub">
            Rate yourself on each factor below. Our AI will calculate your placement
            probability and generate a personalised action plan to close every gap.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════
    #  INPUT FORM
    # ════════════════════════════════════════

    # ── SECTION 1: Academic ──────────────────────────────────────
    st.markdown('<div class="ir-section"><div class="ir-section-title">Academic Performance</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ir_cgpa = st.slider("CGPA (out of 10)", 0.0, 10.0, 6.5, 0.1, key="ir_cgpa",
                            help="Your cumulative grade point average. Threshold: 6.0+")
    with col2:
        ir_degree_pct = st.slider("Degree Percentage (%)", 0.0, 100.0, 65.0, 0.5, key="ir_deg",
                                  help="Your overall degree percentage. Threshold: 60%+")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION 2: Skills ────────────────────────────────────────
    st.markdown('<div class="ir-section"><div class="ir-section-title">Skills Assessment</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ir_tech_score = st.slider("Technical Skills Score (%)", 0.0, 100.0, 65.0, 0.5, key="ir_tech",
                                  help="Rate your technical knowledge (coding, tools, etc.). Threshold: 60%+")
    with col2:
        ir_soft_score = st.slider("Soft Skills Score (%)", 0.0, 100.0, 65.0, 0.5, key="ir_soft",
                                  help="Rate your communication, teamwork, leadership. Threshold: 60%+")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION 3: Experience ────────────────────────────────────
    st.markdown('<div class="ir-section"><div class="ir-section-title">Experience & Projects</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        ir_internships = st.number_input("Number of Internships", min_value=0, max_value=15,
                                         value=0, step=1, key="ir_intern",
                                         help="Minimum 1 internship recommended")
    with col2:
        ir_work_exp_months = st.number_input("Work Experience (months)", min_value=0, max_value=60,
                                              value=0, step=1, key="ir_work",
                                              help="Any full-time / part-time / freelance work. Threshold: 3+ months")
    with col3:
        ir_live_projects = st.number_input("Live Projects", min_value=0, max_value=20,
                                            value=0, step=1, key="ir_proj",
                                            help="Projects deployed or actively running. Minimum: 1")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION 4: Backlogs & Activities ────────────────────────
    st.markdown('<div class="ir-section"><div class="ir-section-title">Backlogs & Activities</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ir_backlogs = st.number_input("Number of Backlogs / Arrears", min_value=0, max_value=20,
                                       value=0, step=1, key="ir_back",
                                       help="Active failed subjects. Ideal: 0 backlogs")
    with col2:
        ir_extra = st.number_input("Extracurricular Activities (count)", min_value=0, max_value=30,
                                    value=0, step=1, key="ir_extra",
                                    help="Clubs, sports, events, competitions, volunteering, etc. Threshold: 3+")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ANALYSE BUTTON ────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        analyse_btn = st.button("Analyse & Get My Recommendations", key="ir_analyse")

    # ════════════════════════════════════════
    #  PREDICTION + RECOMMENDATION LOGIC
    # ════════════════════════════════════════
    if analyse_btn:

        # ── Thresholds & weights ──────────────────────────────────
        # Each entry: (feature_label, user_value, threshold, condition, weight, penalty_cap)
        # condition: "gte" = value >= threshold is PASS
        #            "eq0" = value == 0 is PASS (backlogs)
        CRITERIA = [
            ("CGPA",                   ir_cgpa,            6.0,  "gte",  20),
            ("Degree Percentage",       ir_degree_pct,      60.0, "gte",  15),
            ("Technical Skills",        ir_tech_score,      60.0, "gte",  15),
            ("Soft Skills",             ir_soft_score,      60.0, "gte",  12),
            ("Internships",             ir_internships,     1,    "gte",  14),
            ("Work Experience",         ir_work_exp_months, 3,    "gte",  10),
            ("Live Projects",           ir_live_projects,   1,    "gte",  10),
            ("Extracurricular",         ir_extra,           3,    "gte",   4),
            ("Backlogs",                ir_backlogs,        0,    "eq0",  12),  # PASS = 0 backlogs
        ]

        raw_score   = 0.0
        feat_status = {}   # label -> (passed:bool, value, threshold)

        for feat, val, thresh, cond, w in CRITERIA:
            if cond == "eq0":
                passed = (val == 0)
            else:
                passed = (val >= thresh)

            feat_status[feat] = (passed, val, thresh)

            if passed:
                if cond == "gte" and thresh > 0:
                    # slight bonus for exceeding threshold
                    raw_score += w * min(1.0 + (val - thresh) / max(thresh, 1) * 0.12, 1.12)
                else:
                    raw_score += w   # backlogs == 0: full marks
            else:
                if cond == "gte" and thresh > 0:
                    # partial credit — proportional, capped at 50%
                    raw_score += w * min(val / thresh, 1.0) * 0.5
                # backlogs > 0: zero contribution

        total_weight = sum(w for *_, w in CRITERIA)
        max_possible = total_weight * 1.12

        pct = min(round((raw_score / max_possible) * 100, 1), 99.0)
        pct = max(pct, 2.0)

        # Hard cap if backlogs exist
        if ir_backlogs > 0:
            pct = min(pct, 35.0)

        # ── Try actual model ──────────────────────────────────────
        model, scaler = load_artifacts()
        model_used = False
        if model is not None and scaler is not None:
            try:
                features = np.array([[
                    ir_cgpa,
                    ir_degree_pct,
                    ir_tech_score,
                    ir_soft_score,
                    float(ir_internships),
                    float(ir_work_exp_months),
                    float(ir_live_projects),
                    float(ir_extra),
                    float(ir_backlogs),
                ]])
                fs = scaler.transform(features)
                proba = model.predict_proba(fs)[0]
                model_pct = round(float(proba[1]) * 100, 1)
                # Blend 60% model + 40% rule-based
                pct = round(0.6 * model_pct + 0.4 * pct, 1)
                pct = min(pct, 99.0)
                if ir_backlogs > 0:
                    pct = min(pct, 35.0)
                model_used = True
            except Exception:
                pass

        # ── Verdict ──────────────────────────────────────────────
        if pct >= 70:
            verdict = "Strong Placement Chances 🎉"
            status  = "LIKELY PLACED"
            v_cls, p_cls, b_cls, g_cls = "c-green","c-pct-g","c-bdg-g","c-gf-g"
        elif pct >= 45:
            verdict = "Moderate Placement Chances ⚡"
            status  = "BORDERLINE"
            v_cls, p_cls, b_cls, g_cls = "c-yellow","c-pct-y","c-bdg-y","c-gf-y"
        else:
            verdict = "Low Placement Chances 📈"
            status  = "NEEDS IMPROVEMENT"
            v_cls, p_cls, b_cls, g_cls = "c-red","c-pct-r","c-bdg-r","c-gf-r"

        # ── Build recommendations ─────────────────────────────────
        recs = []   # list of (priority, icon, label, body_html)

        # BACKLOGS — always first, highest severity
        if not feat_status["Backlogs"][0]:
            recs.append(("crit", "🚨", "Backlogs",
                f"You have <b>{ir_backlogs} active backlog(s)</b> — this is the single biggest "
                "placement blocker. Most companies auto-reject candidates with any pending arrear. "
                "<b>Clear all backlogs immediately</b> before applying to any company."))

        # CGPA
        if not feat_status["CGPA"][0]:
            gap = round(6.0 - ir_cgpa, 1)
            recs.append(("crit", "📖", "CGPA Below Threshold",
                f"Your CGPA is <b>{ir_cgpa}</b>, which is below the minimum of <b>6.0</b> "
                f"(gap: {gap} points). Dedicate extra time to upcoming exams. Consult your "
                "faculty for weak subjects and aim for 75%+ in each paper this semester."))
        elif ir_cgpa < 7.5:
            recs.append(("warn", "📖", "CGPA — Room to Grow",
                f"CGPA of <b>{ir_cgpa}</b> meets the threshold but top recruiters prefer 7.5+. "
                "Target 80%+ in your next two semesters to cross that competitive benchmark."))

        # DEGREE PERCENTAGE
        if not feat_status["Degree Percentage"][0]:
            recs.append(("crit", "🎓", "Degree Percentage Below 60%",
                f"Your degree percentage is <b>{ir_degree_pct}%</b>, below the 60% eligibility cutoff "
                "most companies enforce. You may be screened out before even reaching the interview stage. "
                "Focus on scoring 65%+ in remaining semesters to recover your aggregate."))

        # TECHNICAL SKILLS
        if not feat_status["Technical Skills"][0]:
            recs.append(("crit", "💻", "Technical Skills Below 60%",
                f"Technical score of <b>{ir_tech_score}%</b> is below 60%. "
                "Practise 3–5 DSA problems daily on LeetCode or HackerRank. "
                "Complete at least one paid/free certification (AWS, Google IT, Python, Java) "
                "within the next 45 days to demonstrate domain competency."))
        elif ir_tech_score < 80:
            recs.append(("warn", "💻", "Technical Skills — Sharpen Further",
                f"Technical score <b>{ir_tech_score}%</b> is decent. Push to 80%+ by covering "
                "advanced DSA (trees, graphs, dynamic programming) and practising "
                "mock technical interviews on Pramp or InterviewBit."))

        # SOFT SKILLS
        if not feat_status["Soft Skills"][0]:
            recs.append(("crit", "🗣️", "Soft Skills Below 60%",
                f"Soft skill score of <b>{ir_soft_score}%</b> is below 60%. "
                "Recruiters heavily evaluate communication in GDs and HR rounds. "
                "Join a public speaking club, practise mock GDs weekly, "
                "and work on STAR-format answers for behavioural questions."))
        elif ir_soft_score < 80:
            recs.append(("warn", "🗣️", "Soft Skills — Polish Before Placements",
                f"Soft skills at <b>{ir_soft_score}%</b> — solid, but room to improve. "
                "Focus on professional email writing, presentation skills, "
                "and mock HR interview practice to reach 80%+."))

        # INTERNSHIPS
        if not feat_status["Internships"][0]:
            recs.append(("crit", "🏢", "No Internship Experience",
                "You have <b>0 internships</b> — a critical gap. Internships are among the "
                "top filters recruiters use. Apply immediately on Internshala, LinkedIn, "
                "and company portals. Even a 1-month remote internship significantly "
                "strengthens your resume and interview confidence."))
        elif ir_internships == 1:
            recs.append(("warn", "🏢", "Only 1 Internship",
                "1 internship is a good start. Try to secure a second one in a different domain "
                "to showcase versatility. Look for 2–3 month opportunities during semester breaks."))

        # WORK EXPERIENCE
        if not feat_status["Work Experience"][0]:
            if ir_work_exp_months == 0:
                recs.append(("warn", "💼", "No Work Experience",
                    "You have <b>0 months</b> of work experience. Any part-time job, "
                    "freelance project, or campus role (TA, club coordinator) counts. "
                    "Aim for at least 3 months before your placement season starts."))
            else:
                recs.append(("warn", "💼", "Work Experience Below 3 Months",
                    f"You have <b>{ir_work_exp_months} month(s)</b> of work experience — "
                    "below the 3-month benchmark. Try to extend or take on a new "
                    "part-time / freelance engagement to cross that threshold."))

        # LIVE PROJECTS
        if not feat_status["Live Projects"][0]:
            recs.append(("crit", "🛠️", "No Live Projects",
                "You have <b>0 live projects</b>. Recruiters want to see hands-on work. "
                "Build and deploy at least one project — a full-stack web app, "
                "a data analysis dashboard, or an ML model. Host it on GitHub or Vercel "
                "and include the link in your resume."))
        elif ir_live_projects < 3:
            recs.append(("warn", "🛠️", "Add More Projects",
                f"<b>{ir_live_projects} live project(s)</b> — good, but 3+ is competitive. "
                "Add one more project relevant to your target role "
                "(e.g., REST API, mobile app, data pipeline) before placement season."))

        # EXTRACURRICULAR
        if not feat_status["Extracurricular"][0]:
            recs.append(("warn", "🌟", "Extracurricular Activities Below 3",
                f"Only <b>{ir_extra}</b> extracurricular activit{'y' if ir_extra==1 else 'ies'} recorded. "
                "Companies value well-rounded candidates. Join technical clubs, "
                "participate in hackathons, sports teams, or volunteer initiatives. "
                "Aim for at least 3 meaningful activities to show on your resume."))

        # If everything is great
        all_passed = all(v[0] for v in feat_status.values())
        if all_passed and pct >= 70:
            recs.append(("good", "🏆", "Outstanding Profile",
                "You meet or exceed <b>every key placement criterion</b>! "
                "Focus now on company-specific prep: online aptitude rounds, "
                "technical coding tests, and HR interview practice. You are placement-ready!"))

        st.session_state.ir_result = {
            "pct": pct, "verdict": verdict, "status": status,
            "v_cls": v_cls, "p_cls": p_cls, "b_cls": b_cls, "g_cls": g_cls,
            "recs": recs, "model_used": model_used,
        }
        # ── FIREBASE: save recommendation result ──────────────
        if FIREBASE_ON:
            save_recommendation(
                username        = st.session_state.get("username", "unknown"),
                inputs          = {
                    "cgpa": ir_cgpa, "degree_pct": ir_degree_pct,
                    "tech_score": ir_tech_score, "soft_score": ir_soft_score,
                    "internships": ir_internships, "live_projects": ir_live_projects,
                    "backlogs": ir_backlogs, "work_exp": ir_work_exp_months,
                    "extra": ir_extra,
                },
                result_pct      = pct,
                recommendations = [r[2] for r in recs],  # list of rec labels
            )
        st.session_state.ir_show_result = True
        st.rerun()

    # ── RESULT POPUP ──────────────────────────────────────────────
    if st.session_state.get("ir_show_result"):
        r = st.session_state.ir_result

        # Build recommendation cards HTML
        recs_html = '<div class="rec-section-hdr">📋 Your Personalised Action Plan</div>'
        for (prio, icon, label, body) in r["recs"]:
            tag_cls = {"crit": "tag-c", "warn": "tag-w", "good": "tag-g"}[prio]
            tag_lbl = {"crit": "Critical", "warn": "Improve", "good": "Strength"}[prio]
            recs_html += (
                f'<div class="rec-card {prio}">'
                f'<div class="rec-icon">{icon}</div>'
                f'<div class="rec-body">'
                f'<span class="rec-tag {tag_cls}">{tag_lbl} · {label}</span>'
                f'<p class="rec-text">{body}</p>'
                f'</div></div>'
            )

        model_note = (
            '<p style="font-family:Poppins,sans-serif;font-size:.68rem;color:#a78bfa;'
            'text-align:center;margin-top:.4rem;">'
            '&#9889; Prediction powered by your trained Random Forest model</p>'
            if r["model_used"] else
            '<p style="font-family:Poppins,sans-serif;font-size:.68rem;color:#7c3aed;'
            'text-align:center;margin-top:.4rem;">'
            '&#128202; Rule-based scoring active</p>'
        )

        # ── ALL popup CSS + HTML in ONE st.markdown so styles always load ──
        popup_html = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap');

        /* backdrop */
        #ir-backdrop {{
            position:fixed; inset:0; z-index:998;
            background:rgba(46,16,101,.52);
            backdrop-filter:blur(5px);
        }}
        /* centred popup */
        #ir-popup-wrap {{
            position:fixed; inset:0; z-index:999;
            display:flex; align-items:center; justify-content:center;
            padding:1.2rem; pointer-events:none;
        }}
        #ir-popup-box {{
            pointer-events:all;
            background:#ffffff;
            border-radius:24px;
            width:min(580px,96vw);
            max-height:88vh;
            overflow-y:auto;
            padding:2rem 1.8rem 1.6rem;
            box-shadow:0 30px 80px rgba(88,28,220,.28);
            border-top:5px solid #7c3aed;
            animation:irPop .38s cubic-bezier(.22,1,.36,1) both;
        }}
        @keyframes irPop {{
            from{{opacity:0;transform:scale(.9) translateY(24px);}}
            to  {{opacity:1;transform:scale(1)  translateY(0);}}
        }}
        /* verdict / pct / badge */
        .ir2-verdict {{
            font-family:'Poppins',sans-serif; font-size:1.25rem; font-weight:800;
            text-align:center; margin-bottom:.3rem;
        }}
        .ir2-pct {{
            font-family:'Poppins',sans-serif; font-size:4.2rem; font-weight:900;
            line-height:1; text-align:center; margin:.25rem 0;
        }}
        .ir2-label {{
            font-family:'Poppins',sans-serif; font-size:.78rem;
            color:#a78bfa; text-align:center; margin-bottom:.8rem; font-weight:500;
        }}
        .ir2-badge {{
            display:block; width:fit-content; margin:0 auto .9rem;
            font-family:'Poppins',sans-serif; font-size:.84rem; font-weight:700;
            padding:.38rem 1.4rem; border-radius:99px; letter-spacing:.5px;
        }}
        /* gauge */
        .ir2-gauge-track {{
            background:#ede9fe; border-radius:99px; height:12px;
            overflow:hidden; margin:0 auto 1.5rem; max-width:380px;
        }}
        .ir2-gauge-fill {{ height:100%; border-radius:99px; }}
        /* colour variants */
        .c-green  {{ color:#065f46; }}
        .c-pct-g  {{ color:#10b981; }}
        .c-bdg-g  {{ background:#d1fae5; color:#065f46; border:1.5px solid #6ee7b7; }}
        .c-gf-g   {{ background:linear-gradient(90deg,#34d399,#10b981); }}
        .c-yellow {{ color:#78350f; }}
        .c-pct-y  {{ color:#d97706; }}
        .c-bdg-y  {{ background:#fef3c7; color:#78350f; border:1.5px solid #fcd34d; }}
        .c-gf-y   {{ background:linear-gradient(90deg,#fbbf24,#d97706); }}
        .c-red    {{ color:#7f1d1d; }}
        .c-pct-r  {{ color:#dc2626; }}
        .c-bdg-r  {{ background:#fee2e2; color:#7f1d1d; border:1.5px solid #fca5a5; }}
        .c-gf-r   {{ background:linear-gradient(90deg,#f87171,#dc2626); }}
        /* recommendations */
        .rec-section-hdr {{
            font-family:'Poppins',sans-serif; font-size:.9rem; font-weight:800;
            color:#4c1d95; margin:1.3rem 0 .7rem;
            border-left:3px solid #7c3aed; padding-left:.6rem;
        }}
        .rec-card {{
            border-radius:12px; padding:.85rem 1rem .8rem;
            margin-bottom:.55rem; display:flex; gap:.75rem; align-items:flex-start;
        }}
        .rec-card.crit {{ background:#fdf2f8; border:1px solid #f9a8d4; }}
        .rec-card.warn {{ background:#fffbeb; border:1px solid #fde68a; }}
        .rec-card.good {{ background:#ecfdf5; border:1px solid #6ee7b7; }}
        .rec-icon {{ font-size:1.25rem; line-height:1; flex-shrink:0; margin-top:.1rem; }}
        .rec-body {{ flex:1; }}
        .rec-tag {{
            display:inline-block; font-family:'Poppins',sans-serif;
            font-size:.62rem; font-weight:700; padding:.15rem .55rem;
            border-radius:99px; letter-spacing:.6px; text-transform:uppercase;
            margin-bottom:.25rem;
        }}
        .tag-c {{ background:#fce7f3; color:#be185d; }}
        .tag-w {{ background:#fef9c3; color:#a16207; }}
        .tag-g {{ background:#d1fae5; color:#065f46; }}
        .rec-text {{
            font-family:'Poppins',sans-serif; font-size:.80rem;
            color:#3730a3; line-height:1.55; margin:0;
        }}
        .ir2-close-btn {{ display:none; }}
        </style>

        <div id="ir-popup-wrap">
          <div id="ir-popup-box">
            <div class="ir2-verdict {r['v_cls']}">{r['verdict']}</div>
            <span class="ir2-badge {r['b_cls']}">Status: {r['status']}</span>
            <div class="ir2-pct {r['p_cls']}">{r['pct']}%</div>
            <div class="ir2-label">Estimated Placement Probability</div>
            <div class="ir2-gauge-track">
              <div class="ir2-gauge-fill {r['g_cls']}" style="width:{r['pct']}%;"></div>
            </div>
            {recs_html}
            {model_note}
          </div>
        </div>
        """

        st.markdown(popup_html, unsafe_allow_html=True)

        # ── Close button rendered ABOVE the fixed popup via z-index:1000 ──
        st.markdown("""
        <style>
        div[data-testid="stButton"]:has(button[kind="primary"]) {
            position: fixed !important;
            bottom: 2.2rem !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            z-index: 1000 !important;
            width: auto !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) > button {
            width: auto !important;
            background: linear-gradient(135deg,#7c3aed,#5b21b6) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 50px !important;
            font-family: 'Poppins',sans-serif !important;
            font-size: .95rem !important;
            font-weight: 700 !important;
            padding: .7rem 2.5rem !important;
            box-shadow: 0 6px 24px rgba(124,58,237,.55) !important;
            letter-spacing: .4px !important;
            cursor: pointer !important;
        }
        div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {
            background: linear-gradient(135deg,#6d28d9,#4c1d95) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 30px rgba(109,40,217,.6) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.button("✕  Close Results", key="ir_dismiss_overlay", type="primary"):
            st.session_state.ir_show_result = False
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  PAGE 6 — PRODUCT PAGE  (sidebar nav template)
# ══════════════════════════════════════════════════════════════
def show_product():
    import streamlit.components.v1 as components

    st.markdown("""
    <style>
    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer{display:none!important;}
    .block-container{padding:0!important;max-width:100%!important;}
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main,
    [data-testid="stAppViewContainer"] section,[data-testid="stVerticalBlock"]{
        background:#0a2e14!important; padding:0!important;
    }
    </style>
    """, unsafe_allow_html=True)

    html_code = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link href="https://fonts.googleapis.com/css2?family=Pinyon+Script&family=Great+Vibes&family=Times+New+Roman:ital@0;1&display=swap" rel="stylesheet"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;font-family:'Times New Roman',Times,serif;}

/* ══ FULLSCREEN BACKGROUND ══ */
.bg{
  position:fixed;inset:0;z-index:0;
  background:
    url('https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=1920&q=95')
    center center / cover no-repeat;
}
.bg-overlay{
  position:fixed;inset:0;z-index:1;
  background:linear-gradient(
    135deg,
    rgba(6,28,12,.91) 0%,
    rgba(10,46,20,.85) 50%,
    rgba(5,22,10,.93) 100%
  );
}

/* ══ MAIN LAYOUT ══ */
.layout{
  position:relative;z-index:2;
  display:flex;height:100vh;width:100vw;
}

/* ══ LEFT SIDEBAR ══ */
.sidebar{
  width:260px;flex-shrink:0;
  height:100vh;
  display:flex;flex-direction:column;
  padding:2.5rem 0 2rem;
  background:rgba(0,0,0,.38);
  border-right:1px solid rgba(245,197,24,.2);
  backdrop-filter:blur(12px);
}
.sidebar-logo{
  padding:0 1.8rem 2rem;
  border-bottom:1px solid rgba(245,197,24,.18);
  margin-bottom:1.8rem;
}
.sidebar-logo-main{
  font-family:'Times New Roman',serif;
  font-size:1.4rem;font-weight:700;
  color:#fff;letter-spacing:1.5px;
}
.sidebar-logo-main span{color:#f5c518;}
.sidebar-logo-sub{
  font-family:'Times New Roman',serif;
  font-size:.72rem;color:rgba(255,255,255,.5);
  margin-top:.25rem;letter-spacing:.8px;
}

/* tagline in sidebar */
.sidebar-tagline{
  font-family:'Great Vibes',cursive;
  font-size:1.55rem;
  color:#f5c518;
  line-height:1.35;
  padding:0 1.8rem 1.8rem;
  border-bottom:1px solid rgba(245,197,24,.15);
  margin-bottom:1.8rem;
  text-shadow:0 2px 12px rgba(0,0,0,.6);
}

/* nav links */
.nav-item{
  display:flex;align-items:center;gap:.75rem;
  padding:.75rem 1.8rem;
  font-family:'Times New Roman',serif;
  font-size:1rem;font-weight:700;
  color:rgba(255,255,255,.65);
  cursor:pointer;
  border-left:3px solid transparent;
  transition:all .22s ease;
  letter-spacing:.8px;
  text-transform:uppercase;
  user-select:none;
}
.nav-item:hover{
  color:#f5c518;
  background:rgba(245,197,24,.08);
  border-left-color:rgba(245,197,24,.4);
}
.nav-item.active{
  color:#f5c518;
  background:rgba(245,197,24,.13);
  border-left-color:#f5c518;
}
.nav-dot{
  width:7px;height:7px;border-radius:50%;
  background:currentColor;flex-shrink:0;
  transition:transform .2s;
}
.nav-item.active .nav-dot{transform:scale(1.5);}

/* bottom credit */
.sidebar-credit{
  padding:0 1.8rem;
  font-family:'Times New Roman',serif;
  font-size:.7rem;color:rgba(255,255,255,.3);
  line-height:1.6; margin-bottom:.8rem;
}
.back-btn{
  margin:0 1.8rem;
  width:calc(100% - 3.6rem);
  background:rgba(245,197,24,.15);
  border:1.5px solid rgba(245,197,24,.55);
  color:#f5c518;
  font-family:'Times New Roman',serif;
  font-size:.9rem; font-weight:700;
  border-radius:9px; padding:.6rem 1rem;
  cursor:pointer; letter-spacing:.5px;
  transition:background .2s;
}
.back-btn:hover{background:rgba(245,197,24,.28);}

/* ══ CONTENT AREA ══ */
.content{
  flex:1;height:100vh;overflow-y:auto;
  padding:4rem 5rem 4rem 4.5rem;
  scroll-behavior:smooth;
}
.content::-webkit-scrollbar{width:5px;}
.content::-webkit-scrollbar-track{background:transparent;}
.content::-webkit-scrollbar-thumb{background:rgba(245,197,24,.3);border-radius:99px;}

/* section — hidden by default, shown when active */
.section{display:none;}
.section.visible{display:block;animation:fadeIn .35s ease both;}
@keyframes fadeIn{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}

/* section heading */
.sec-heading{
  font-family:'Times New Roman',serif;
  font-size:26px;font-weight:700;
  color:#f5c518;
  text-transform:uppercase;
  letter-spacing:2px;
  margin-bottom:1.4rem;
  padding-bottom:.7rem;
  border-bottom:2px solid rgba(245,197,24,.3);
}

/* body text */
.sec-body{
  font-family:'Times New Roman',serif;
  font-size:19px;font-weight:400;
  color:rgba(255,255,255,.92);
  line-height:1.85;
}

/* feature list */
.feat-list{
  list-style:none;
  margin-top:1.2rem;
}
.feat-list li{
  font-family:'Times New Roman',serif;
  font-size:19px;color:rgba(255,255,255,.9);
  line-height:1.75;padding:.35rem 0;
  padding-left:1.4rem;
  position:relative;
}
.feat-list li::before{
  content:'';position:absolute;left:0;top:.9rem;
  width:7px;height:7px;border-radius:50%;
  background:#f5c518;
}

/* module cards */
.mod-grid{
  display:grid;grid-template-columns:1fr 1fr;
  gap:1.2rem;margin-top:1.5rem;
}
.mod-card{
  background:rgba(245,197,24,.07);
  border:1px solid rgba(245,197,24,.28);
  border-radius:14px;padding:1.3rem 1.5rem;
  transition:background .2s,border-color .2s;
}
.mod-card:hover{
  background:rgba(245,197,24,.13);
  border-color:rgba(245,197,24,.5);
}
.mod-card-title{
  font-family:'Times New Roman',serif;
  font-size:19px;font-weight:700;
  color:#f5c518;text-transform:uppercase;
  letter-spacing:1px;margin-bottom:.6rem;
}
.mod-card-body{
  font-family:'Times New Roman',serif;
  font-size:17px;color:rgba(255,255,255,.85);
  line-height:1.7;
}
.mod-badge{
  display:inline-block;margin-top:.65rem;
  font-family:'Times New Roman',serif;
  font-size:.72rem;font-weight:700;
  padding:.2rem .7rem;border-radius:99px;
  letter-spacing:.6px;text-transform:uppercase;
}
.b-a{background:rgba(52,211,153,.18);color:#34d399;border:1px solid rgba(52,211,153,.35);}
.b-s{background:rgba(251,191,36,.14);color:#fbbf24;border:1px solid rgba(251,191,36,.3);}
.b-b{background:rgba(99,102,241,.18);color:#a5b4fc;border:1px solid rgba(99,102,241,.3);}

/* advantages */
.adv-grid{
  display:grid;grid-template-columns:1fr 1fr;
  gap:1.2rem;margin-top:1.5rem;
}
.adv-card{
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.14);
  border-radius:14px;padding:1.3rem 1.5rem;
}
.adv-icon{font-size:1.8rem;margin-bottom:.6rem;display:block;}
.adv-title{
  font-family:'Times New Roman',serif;
  font-size:19px;font-weight:700;
  color:#f5c518;margin-bottom:.4rem;
}
.adv-body{
  font-family:'Times New Roman',serif;
  font-size:17px;color:rgba(255,255,255,.82);
  line-height:1.7;
}
</style>
</head>
<body>

<div class="bg"></div>
<div class="bg-overlay"></div>

<div class="layout">

  <!-- ══ SIDEBAR ══ -->
  <div class="sidebar">

    <div class="sidebar-logo">
      <div class="sidebar-logo-main">🎓 <span>SCIS</span></div>
      <div class="sidebar-logo-sub">Student Career Intelligence System</div>
    </div>

    <div class="sidebar-tagline" style="display:none;">
    </div>

    <div class="nav-item active" onclick="show('about')"    id="nav-about">
      <span class="nav-dot"></span> About SCIS
    </div>
    <div class="nav-item"        onclick="show('func')"     id="nav-func">
      <span class="nav-dot"></span> Functionalities
    </div>
    <div class="nav-item"        onclick="show('adv')"      id="nav-adv">
      <span class="nav-dot"></span> Advantages
    </div>

  </div><!-- /sidebar -->

  <!-- ══ CONTENT ══ -->
  <div class="content">

    <!-- ABOUT SCIS -->
    <div class="section visible" id="sec-about">
      <div style="
        font-family:'Times New Roman',serif;
        font-size:62px;
        font-weight:700;
        color:#f5c518;
        line-height:1.2;
        margin-bottom:1.4rem;
        text-align:center;
        text-shadow:0 2px 18px rgba(0,0,0,.55);
      ">Predict. Improve.<br>Land Your Dream Job.</div>
      <div class="sec-heading">About SCIS</div>
      <div class="sec-body">
        Student Career Intelligence System (SCIS) is an AI-powered placement
        prediction platform developed specifically for CSE students in the final
        year of their BTEC degree. Built during an industrial training engagement
        at Alpha IT Managed Services, Sector 67, the platform uses a trained
        Random Forest machine learning model to analyse a student's complete
        academic and skill profile and produce a real-time placement probability
        score.
        <br><br>
        The core mission of SCIS is to bridge the information gap between
        students and campus recruiters. Before placement season begins, most
        students have no objective measure of how competitive their profile
        actually is. SCIS changes that by giving every student a clear,
        data-driven picture of exactly where they stand — and what they need
        to do to improve — weeks or months before recruitment drives start.
        <br><br>
        The system is built entirely in Python using the Streamlit framework,
        combining a trained scikit-learn model with a transparent rule-based
        scoring engine to deliver results that are not only accurate but also
        fully explainable to the student.
      </div>
    </div>

    <!-- FUNCTIONALITIES -->
    <div class="section" id="sec-func">
      <div class="sec-heading">Functionalities</div>
      <div class="sec-body">
        SCIS is a full-featured career intelligence platform built around
        the specific needs of placement-bound engineering students. Its key
        functionalities include:
      </div>
      <ul class="feat-list">
        <li>Real-time placement probability scoring based on a student's live academic inputs, delivered instantly without any server delay.</li>
        <li>Analysis of nine critical placement features: CGPA, degree percentage, technical skills, soft skills, internships, live projects, work experience, backlogs, and extracurricular activities.</li>
        <li>Personalised improvement recommendations for every weak area identified in a student's profile, colour-coded by severity — Critical, Improve, or Strength.</li>
        <li>Blended prediction engine combining a trained Random Forest ML model with a transparent rule-based scoring system for accurate and explainable results.</li>
        <li>Intelligent salary estimation based on the predicted placement outcome and current market benchmarks.</li>
        <li>Secure multi-user login system with session management and role-based access for students and administrators.</li>
        <li>Clean, responsive dashboard with module cards, progress indicators, and smooth page transitions built entirely in Streamlit.</li>
        <li>Career prediction module that maps a student's profile to a specific career domain and growth path.</li>
      </ul>
    </div>

    <!-- ADVANTAGES -->
    <div class="section" id="sec-adv">
      <div class="sec-heading">Advantages</div>
      <div class="sec-body">
        SCIS delivers concrete, measurable advantages over traditional
        placement preparation approaches used by students and institutions.
      </div>
      <div class="adv-grid">

        <div class="adv-card">
          <div class="adv-title">1. Data-Driven Decisions</div>
          <div class="adv-body">
            Eliminates guesswork from placement preparation. Students receive
            an objective, model-backed probability score instead of relying
            on subjective self-assessment or peer comparison.
          </div>
        </div>

        <div class="adv-card">
          <div class="adv-title">2. Real-Time Results</div>
          <div class="adv-body">
            Predictions and recommendations are generated instantly. Students
            can adjust their inputs and see updated results in real time,
            making it a dynamic planning tool rather than a one-time report.
          </div>
        </div>

        <div class="adv-card">
          <div class="adv-title">3. Explainable AI</div>
          <div class="adv-body">
            Unlike black-box models, SCIS blends ML predictions with a
            transparent rule-based engine. Every recommendation includes a
            clear reason and a specific action, so students understand exactly
            what to fix and why.
          </div>
        </div>

        <div class="adv-card">
          <div class="adv-title">4. Personalised Roadmap</div>
          <div class="adv-body">
            Every student receives a unique action plan tailored to their
            specific profile gaps — not a generic checklist. Recommendations
            are prioritised by severity so students know what to focus on first.
          </div>
        </div>

        <div class="adv-card">
          <div class="adv-title">5. Free and Accessible</div>
          <div class="adv-body">
            Completely free for all registered CSE students with no
            subscription or hidden charges. Accessible from any device
            with a browser and runs entirely on the college server
            without requiring any software installation.
          </div>
        </div>

        <div class="adv-card">
          <div class="adv-title">6. Early Intervention</div>
          <div class="adv-body">
            Designed to be used months before placement season, giving
            students sufficient time to act on recommendations, complete
            certifications, build projects, and secure internships before
            recruiters arrive on campus.
          </div>
        </div>

      </div>
    </div>

  </div><!-- /content -->

</div><!-- /layout -->

<script>
function show(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('sec-' + id).classList.add('visible');
  document.getElementById('nav-' + id).classList.add('active');
  document.querySelector('.content').scrollTop = 0;
}
</script>
</body>
</html>"""

    components.html(html_code, height=780, scrolling=False)

    # Back button — rendered by Streamlit, positioned inside sidebar via CSS
    st.markdown("""
    <style>
    div[data-testid="stButton"]>button{
        position:fixed!important;
        bottom:3.5rem!important;left:1.2rem!important;
        width:218px!important;z-index:9999!important;
        background:rgba(245,197,24,.15)!important;
        border:1.5px solid rgba(245,197,24,.55)!important;
        color:#f5c518!important;
        font-family:'Times New Roman',serif!important;
        font-size:.9rem!important;font-weight:700!important;
        border-radius:9px!important;padding:.6rem 1rem!important;
        box-shadow:none!important;letter-spacing:.5px!important;
        transition:background .2s!important;
    }
    div[data-testid="stButton"]>button:hover{
        background:rgba(245,197,24,.28)!important;
        transform:none!important;box-shadow:none!important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("← Back to Dashboard", key="prod_back"):
        st.session_state.stage = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════
#  PAGE 7 — PRICING PAGE  (same style as product tab)
# ══════════════════════════════════════════════════════════════
def show_pricing():
    import streamlit.components.v1 as components

    st.markdown("""
    <style>
    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer{display:none!important;}
    .block-container{padding:0!important;max-width:100%!important;}
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main,
    [data-testid="stAppViewContainer"] section,[data-testid="stVerticalBlock"]{
        background:#0a2e14!important;padding:0!important;
    }
    div[data-testid="stButton"]>button{
        position:fixed!important;bottom:3.5rem!important;left:1.2rem!important;
        width:218px!important;z-index:9999!important;
        background:rgba(255,255,255,.15)!important;
        border:1.5px solid rgba(255,255,255,.6)!important;
        color:#fff!important;
        font-family:'Times New Roman',serif!important;
        font-size:.9rem!important;font-weight:700!important;
        border-radius:9px!important;padding:.6rem 1rem!important;
        box-shadow:none!important;letter-spacing:.5px!important;
    }
    div[data-testid="stButton"]>button:hover{
        background:rgba(255,255,255,.28)!important;
        transform:none!important;box-shadow:none!important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("← Back to Dashboard", key="pricing_back"):
        st.session_state.stage = "dashboard"
        st.rerun()

    html_code = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;font-family:'Times New Roman',Times,serif;}

/* fullscreen bg — deep navy/indigo like reference */
.bg{
  position:fixed;inset:0;z-index:0;
  background: linear-gradient(135deg, #6b0fa8 0%, #9c1fcc 25%, #d4237a 65%, #f0106e 100%);
}
.bg-overlay{
  position:fixed;inset:0;z-index:1;
  background: rgba(0,0,0,.18);
}

.layout{position:relative;z-index:2;display:flex;height:100vh;width:100vw;}

/* ── SIDEBAR ── */
.sidebar{
  width:260px;flex-shrink:0;height:100vh;
  display:flex;flex-direction:column;
  padding:2.5rem 0 2rem;
  background:rgba(0,0,0,.25);
  border-right:1px solid rgba(255,255,255,.2);
  backdrop-filter:blur(12px);
}
.sidebar-logo{
  padding:0 1.8rem 2rem;
  border-bottom:1px solid rgba(255,255,255,.18);
  margin-bottom:1.8rem;
}
.sidebar-logo-main{
  font-family:'Times New Roman',serif;
  font-size:1.4rem;font-weight:700;color:#fff;letter-spacing:1.5px;
}
.sidebar-logo-main span{color:#fff;}
.sidebar-logo-sub{
  font-family:'Times New Roman',serif;
  font-size:.72rem;color:rgba(255,255,255,.6);
  margin-top:.25rem;letter-spacing:.8px;
}

.sidebar-tagline{display:none;}

.nav-item{
  display:flex;align-items:center;gap:.75rem;
  padding:.75rem 1.8rem;
  font-family:'Times New Roman',serif;
  font-size:1rem;font-weight:700;
  color:rgba(255,255,255,.6);
  cursor:pointer;
  border-left:3px solid transparent;
  transition:all .22s ease;
  letter-spacing:.8px;text-transform:uppercase;
  user-select:none;
}
.nav-item:hover{color:#fff;background:rgba(255,255,255,.12);border-left-color:rgba(255,255,255,.5);}
.nav-item.active{color:#fff;background:rgba(255,255,255,.18);border-left-color:#fff;}
.nav-dot{width:7px;height:7px;border-radius:50%;background:currentColor;flex-shrink:0;transition:transform .2s;}
.nav-item.active .nav-dot{transform:scale(1.5);}

/* ── CONTENT ── */
.content{
  flex:1;height:100vh;overflow-y:auto;
  padding:4rem 5rem 4rem 4.5rem;
  scroll-behavior:smooth;
}
.content::-webkit-scrollbar{width:5px;}
.content::-webkit-scrollbar-thumb{background:rgba(255,255,255,.3);border-radius:99px;}

.section{display:none;}
.section.visible{display:block;animation:fadeIn .35s ease both;}
@keyframes fadeIn{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}

.sec-heading{
  font-family:'Times New Roman',serif;
  font-size:26px;font-weight:700;
  color:#fff;text-transform:uppercase;
  letter-spacing:2px;margin-bottom:1.4rem;
  padding-bottom:.7rem;
  border-bottom:2px solid rgba(255,255,255,.35);
}
.sec-body{
  font-family:'Times New Roman',serif;
  font-size:19px;font-weight:400;
  color:rgba(255,255,255,.92);line-height:1.85;
}

.price-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.4rem;margin-top:1.5rem;}
.price-card{
  background:rgba(255,255,255,.15);
  border:1px solid rgba(255,255,255,.3);
  border-radius:18px;padding:1.5rem 1.6rem;
  backdrop-filter:blur(8px);
  transition:background .2s,border-color .2s;
}
.price-card:hover{background:rgba(255,255,255,.22);border-color:rgba(255,255,255,.5);}
.price-card-title{
  font-family:'Times New Roman',serif;
  font-size:19px;font-weight:700;
  color:#fff;text-transform:uppercase;
  letter-spacing:1px;margin-bottom:.6rem;
}
.price-card-body{
  font-family:'Times New Roman',serif;
  font-size:17px;color:rgba(255,255,255,.88);line-height:1.7;
}
.price-badge{
  display:inline-block;margin-top:.65rem;
  font-family:'Times New Roman',serif;
  font-size:.72rem;font-weight:700;
  padding:.2rem .7rem;border-radius:99px;
  letter-spacing:.6px;text-transform:uppercase;
}
.b-free{background:rgba(255,255,255,.25);color:#fff;border:1px solid rgba(255,255,255,.5);}

.inc-list{list-style:none;margin-top:1.2rem;}
.inc-list li{
  font-family:'Times New Roman',serif;
  font-size:19px;color:rgba(255,255,255,.92);
  line-height:1.75;padding:.35rem 0;
  padding-left:1.4rem;position:relative;
}
.inc-list li::before{
  content:'';position:absolute;left:0;top:.9rem;
  width:7px;height:7px;border-radius:50%;background:#fff;
}
</style>
</head>
<body>
<div class="bg"></div>
<div class="bg-overlay"></div>

<div class="layout">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-logo">
      <div class="sidebar-logo-main">🎓 <span>SCIS</span></div>
      <div class="sidebar-logo-sub">Student Career Intelligence System</div>
    </div>

    <div class="nav-item active" onclick="show('plans')"   id="nav-plans">
      <span class="nav-dot"></span> Plans
    </div>
    <div class="nav-item"        onclick="show('includes')" id="nav-includes">
      <span class="nav-dot"></span> What's Included
    </div>
    <div class="nav-item"        onclick="show('privacy')"  id="nav-privacy">
      <span class="nav-dot"></span> Data & Privacy
    </div>
  </div>

  <!-- CONTENT -->
  <div class="content">

    <!-- PLANS -->
    <div class="section visible" id="sec-plans">
      <div style="font-family:'Times New Roman',serif;font-size:62px;font-weight:700;
                  color:#fff;line-height:1.2;margin-bottom:1.4rem;text-align:center;
                  text-shadow:0 2px 18px rgba(0,0,0,.35);">
        Free. Forever.<br>For Every Student.
      </div>
      <div class="sec-heading">Plans</div>
      <div class="sec-body">
        SCIS believes every student deserves equal access to career intelligence —
        regardless of background, institution, or financial situation. That is why
        the platform is completely free for all registered CSE students, with no
        subscription fees, no hidden charges, and no expiry date.
      </div>
      <div class="price-grid">

        <div class="price-card">
          <div class="price-card-title">Student Plan</div>
          <div class="price-card-body">
            Full unlimited access to all active modules including Career Prediction
            and Improvement Recommendations. No time limit, no usage cap, no
            payment required at any point.
          </div>
          <span class="price-badge b-free">100% Free</span>
        </div>

        <div class="price-card">
          <div class="price-card-title">Institution Plan</div>
          <div class="price-card-body">
            Colleges and training institutes can request a dedicated deployment
            of SCIS with custom branding, student batch management, and
            administrator dashboards. Contact the development team for details.
          </div>
          <span class="price-badge b-free">Contact Us</span>
        </div>

      </div>
    </div>

    <!-- WHAT'S INCLUDED -->
    <div class="section" id="sec-includes">
      <div class="sec-heading">What's Included</div>
      <div class="sec-body">
        Every registered student gets full access to the following features
        at absolutely no cost, from day one of account creation.
      </div>
      <ul class="inc-list">
        <li>Unlimited real-time placement probability predictions using the trained Random Forest ML model.</li>
        <li>Full access to Module 01 — Career Prediction with salary range estimation and career domain mapping.</li>
        <li>Full access to Module 02 — Improvement Recommendations with colour-coded personalised action plans.</li>
        <li>Detailed analysis of nine placement-critical features: CGPA, degree percentage, technical skills, soft skills, internships, live projects, work experience, backlogs, and extracurricular activities.</li>
        <li>Secure login and session management with personal profile persistence across sessions.</li>
        <li>Clean interactive dashboard with module navigation, progress indicators, and smooth transitions.</li>
        <li>Early access to upcoming modules including Resume Analysis and Student Tracking as they become available.</li>
        <li>No advertisements, no data selling, no third-party tracking of any kind.</li>
      </ul>
    </div>

    <!-- DATA & PRIVACY -->
    <div class="section" id="sec-privacy">
      <div class="sec-heading">Data & Privacy</div>
      <div class="sec-body">
        SCIS is built with student privacy as a core principle, not an afterthought.
        Every aspect of how your data is handled has been designed to protect your
        academic information and personal details.
        <br><br>
        All placement predictions are computed locally on the college server.
        Your academic inputs — CGPA, skill scores, project counts — are used
        only to generate your prediction and recommendations in that session.
        No student data is stored in an external database, sold to third parties,
        or shared with recruiters without explicit consent.
        <br><br>
        Login credentials are session-managed and never transmitted in plain text.
        The platform does not use cookies for tracking, does not embed any
        third-party analytics scripts, and does not display advertisements.
        Your academic data belongs to you — and only you.
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /layout -->

<script>
function show(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('sec-' + id).classList.add('visible');
  document.getElementById('nav-' + id).classList.add('active');
  document.querySelector('.content').scrollTop = 0;
}
</script>
</body>
</html>"""

    components.html(html_code, height=780, scrolling=False)


# ══════════════════════════════════════════════════════════════
#  PAGE 8 — MODULE 03: RESUME ANALYSIS
# ══════════════════════════════════════════════════════════════
def show_resume_analysis():
    import io, re

    # ── skill database per job role ───────────────────────────────
    JOB_ROLES = {
        "Software Engineer": {
            "important": ["programming","data structures","algorithms","database management",
                          "git","github","problem solving"],
            "advanced":  ["system design","cloud computing","docker","kubernetes"],
            "improve_tips": [
                "Add Programming languages clearly (Python, Java, C++ etc.) in a dedicated Skills section.",
                "Mention Data Structures & Algorithms practice — include LeetCode or HackerRank profile links.",
                "List any Database Management experience (MySQL, PostgreSQL, MongoDB) with project context.",
                "Include your GitHub profile URL and ensure repositories are public with README files.",
                "Describe Problem Solving examples in your experience bullets with measurable outcomes.",
                "For advanced growth — learn System Design concepts and document architecture decisions in projects.",
                "Get certified in Cloud Computing: AWS Cloud Practitioner or Google Associate Cloud Engineer.",
                "Add Docker & Kubernetes experience by containerising one of your existing projects.",
            ]
        },
        "Web Developer": {
            "important": ["html","css","javascript","react","api","apis","rest api"],
            "advanced":  ["nextjs","next.js","authentication","progressive web app","pwa"],
            "improve_tips": [
                "Ensure HTML and CSS are explicitly listed — mention semantic HTML5 and CSS3/Flexbox/Grid.",
                "Highlight JavaScript projects with live deployed URLs so recruiters can see your work.",
                "List React projects with component architecture details and state management used.",
                "Mention API integration experience — REST APIs, fetch, axios, or GraphQL.",
                "Add live links to every web project — deployed on Vercel, Netlify or GitHub Pages.",
                "Learn Next.js and build a full-stack project to move into advanced roles.",
                "Implement Authentication Systems (JWT, OAuth) in a project and mention it.",
                "Convert one project to a Progressive Web App (PWA) and document offline capabilities.",
            ]
        },
        "Cyber Security": {
            "important": ["networking","linux","ethical hacking","cryptography",
                          "penetration testing","pentest"],
            "advanced":  ["malware analysis","digital forensics","threat hunting"],
            "improve_tips": [
                "Clearly list Networking knowledge — TCP/IP, DNS, firewalls, VPNs, OSI model.",
                "Mention Linux distributions used (Kali Linux, Ubuntu) and command-line proficiency.",
                "Include any Ethical Hacking labs, CTF competitions or bug bounty participation.",
                "Add Cryptography knowledge — symmetric/asymmetric encryption, hashing, TLS/SSL.",
                "Document Penetration Testing projects — tools used (Metasploit, Nmap, Burp Suite).",
                "Study Malware Analysis — set up a sandbox lab and document your findings.",
                "Learn Digital Forensics tools (Autopsy, FTK) and mention any investigation practice.",
                "Practice Threat Hunting by analysing SIEM logs and document your methodology.",
            ]
        },
        "Graphic Designer": {
            "important": ["photoshop","illustrator","typography","branding","ui design"],
            "advanced":  ["motion graphics","ux research","3d design"],
            "improve_tips": [
                "Include Adobe Photoshop and Illustrator version proficiency and specific use cases.",
                "Showcase Typography skills by mentioning font pairing, hierarchy and readability work.",
                "Add Branding projects — logo design, brand identity guidelines, style guides.",
                "List UI Design tools (Figma, Adobe XD) and include a portfolio link prominently.",
                "Add a Behance or Dribbble portfolio link — visual roles require proof of work.",
                "Learn Motion Graphics (After Effects, Lottie) to stand out for digital design roles.",
                "Conduct and document UX Research — user interviews, wireframes, usability testing.",
                "Explore 3D Design (Blender, Cinema 4D) for product visualisation and animation roles.",
            ]
        },
        "Data Scientist": {
            "important": ["python","statistics","machine learning","sql","data visualization",
                          "data visualisation"],
            "advanced":  ["deep learning","nlp","mlops"],
            "improve_tips": [
                "List Python libraries explicitly — NumPy, Pandas, Scikit-learn, Matplotlib, Seaborn.",
                "Mention Statistics concepts applied — hypothesis testing, regression, probability.",
                "Document Machine Learning projects with model type, accuracy, and business problem solved.",
                "Include SQL query experience — JOINs, aggregations, window functions, subqueries.",
                "Add Data Visualization projects — dashboards in Tableau, Power BI or Plotly/Dash.",
                "Build a Deep Learning project using TensorFlow or PyTorch and publish it on GitHub.",
                "Work on an NLP project — sentiment analysis, text classification or chatbot.",
                "Learn MLOps tools (MLflow, DVC, Docker) to demonstrate production-ready ML skills.",
            ]
        },
        "Data Analyst": {
            "important": ["excel","sql","power bi","data cleaning","reporting"],
            "advanced":  ["predictive analytics","etl","etl pipelines","dashboard automation"],
            "improve_tips": [
                "Highlight Excel skills — pivot tables, VLOOKUP, macros, Power Query.",
                "Show SQL proficiency with examples of complex queries, joins and data aggregations.",
                "Add Power BI dashboards with screenshots or links to demonstrate visual reporting.",
                "Describe Data Cleaning processes — handling nulls, outliers, data standardisation.",
                "Mention specific Reporting deliverables — weekly reports, KPI dashboards, summaries.",
                "Learn Predictive Analytics — linear regression, forecasting models in Python or R.",
                "Build an ETL Pipeline project using Python or SQL and document the data flow.",
                "Automate a Dashboard using Python (Plotly Dash) or Power BI scheduled refresh.",
            ]
        },
    }

    # ── CSS ───────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer{display:none!important;}
    .block-container{padding:0!important;max-width:100%!important;}
    [data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main,
    [data-testid="stAppViewContainer"] section{background:#ffffff!important;}

    /* top bar */
    .ra-topbar{
        display:flex;align-items:center;justify-content:space-between;
        padding:.85rem 2.5rem;background:#fff;
        border-bottom:3px solid #ff1493;
    }
    .ra-logo{
        font-family:'Times New Roman',serif;font-size:1.15rem;
        font-weight:700;color:#ff1493;letter-spacing:1px;
    }
    .ra-tag{
        display:inline-block;
        background:#fff0f5;border:1.5px solid #ff1493;
        border-radius:99px;padding:.22rem .85rem;
        font-family:'Times New Roman',serif;font-size:.7rem;
        font-weight:700;color:#ff1493;letter-spacing:1.5px;
        text-transform:uppercase;
    }

    /* banner */
    .ra-banner{
        background:linear-gradient(135deg,#ff1493 0%,#ff69b4 100%);
        padding:2rem 2.5rem 1.8rem;
    }
    .ra-banner-title{
        font-family:'Times New Roman',serif;font-size:1.9rem;
        font-weight:700;color:#fff;margin-bottom:.4rem;
    }
    .ra-banner-sub{
        font-family:'Times New Roman',serif;font-size:1rem;
        color:rgba(255,255,255,.88);line-height:1.6;
    }

    /* section labels */
    .ra-section-label{
        font-family:'Times New Roman',serif;font-size:1rem;
        font-weight:700;color:#ff1493;text-transform:uppercase;
        letter-spacing:1.5px;margin:1.5rem 0 .5rem;
        padding-bottom:.4rem;border-bottom:2px solid #ff1493;
    }

    /* selectbox + file uploader labels */
    div[data-testid="stSelectbox"]>label,
    div[data-testid="stFileUploader"]>label{
        font-family:'Times New Roman',serif!important;
        font-size:1rem!important;font-weight:700!important;
        color:#ff1493!important;
    }
    div[data-testid="stSelectbox"]>div>div{
        border-color:#ff1493!important;border-radius:10px!important;
        font-family:'Times New Roman',serif!important;
        font-weight:600!important;color:#1a0010!important;
    }

    /* analyse button */
    div[data-testid="stButton"]>button{
        background:linear-gradient(135deg,#ff1493,#ff69b4)!important;
        border:none!important;border-radius:12px!important;
        color:#fff!important;
        font-family:'Times New Roman',serif!important;
        font-size:1rem!important;font-weight:700!important;
        padding:.75rem 2rem!important;width:100%!important;
        box-shadow:0 6px 20px rgba(255,20,147,.35)!important;
        letter-spacing:.4px!important;
    }
    div[data-testid="stButton"]>button:hover{
        transform:translateY(-2px)!important;
        box-shadow:0 10px 28px rgba(255,20,147,.45)!important;
    }

    /* result cards */
    .ra-result-box{
        background:#fff0f5;border:2px solid #ff1493;
        border-radius:16px;padding:1.5rem 1.8rem;
        margin-top:1rem;
    }
    .ra-result-title{
        font-family:'Times New Roman',serif;font-size:1.3rem;
        font-weight:700;color:#ff1493;margin-bottom:.4rem;
    }
    .ra-score-big{
        font-family:'Times New Roman',serif;font-size:3.5rem;
        font-weight:700;color:#ff1493;line-height:1;
    }
    .ra-score-label{
        font-family:'Times New Roman',serif;font-size:.85rem;
        color:#c2185b;margin-bottom:1rem;
    }
    .ra-gauge-track{
        background:#fce4ec;border-radius:99px;height:12px;
        overflow:hidden;max-width:400px;margin-bottom:1.2rem;
    }
    .ra-gauge-fill{height:100%;border-radius:99px;
        background:linear-gradient(90deg,#ff1493,#ff69b4);}

    /* skill chips */
    .ra-chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:.5rem 0 1rem;}
    .chip-found{
        background:#fce4ec;border:1px solid #f48fb1;
        border-radius:99px;padding:.22rem .8rem;
        font-family:'Times New Roman',serif;font-size:.82rem;
        font-weight:700;color:#880e4f;
    }
    .chip-missing{
        background:#fff3e0;border:1px solid #ffb74d;
        border-radius:99px;padding:.22rem .8rem;
        font-family:'Times New Roman',serif;font-size:.82rem;
        font-weight:700;color:#e65100;
    }
    .chip-bonus{
        background:#e8f5e9;border:1px solid #81c784;
        border-radius:99px;padding:.22rem .8rem;
        font-family:'Times New Roman',serif;font-size:.82rem;
        font-weight:700;color:#1b5e20;
    }

    /* tip cards */
    .tip-card{
        background:#fff;border:1.5px solid #f8bbd0;
        border-left:4px solid #ff1493;border-radius:10px;
        padding:.8rem 1.1rem;margin-bottom:.55rem;
        font-family:'Times New Roman',serif;font-size:.95rem;
        color:#4a0020;line-height:1.6;
    }
    .tip-num{
        font-weight:700;color:#ff1493;margin-right:.4rem;
    }

    /* verdict banner */
    .verdict-great{background:linear-gradient(135deg,#e8f5e9,#c8e6c9);
        border:2px solid #4caf50;border-radius:14px;padding:1rem 1.4rem;
        font-family:'Times New Roman',serif;font-size:1rem;
        font-weight:700;color:#1b5e20;text-align:center;margin-bottom:1rem;}
    .verdict-ok{background:linear-gradient(135deg,#fff3e0,#ffe0b2);
        border:2px solid #ff9800;border-radius:14px;padding:1rem 1.4rem;
        font-family:'Times New Roman',serif;font-size:1rem;
        font-weight:700;color:#e65100;text-align:center;margin-bottom:1rem;}
    .verdict-low{background:linear-gradient(135deg,#fce4ec,#f8bbd0);
        border:2px solid #ff1493;border-radius:14px;padding:1rem 1.4rem;
        font-family:'Times New Roman',serif;font-size:1rem;
        font-weight:700;color:#880e4f;text-align:center;margin-bottom:1rem;}
    </style>
    """, unsafe_allow_html=True)

    # ── TOP BAR ──────────────────────────────────────────────────
    st.markdown("""
    <div class="ra-topbar">
        <div class="ra-logo"><span style="background:transparent">🎓</span> <span style="color:#000 !important;">SCIS</span></div>
        <span class="ra-tag">Module 03 · Resume Analysis</span>
    </div>
    """, unsafe_allow_html=True)

    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", key="ra_back"):
            st.session_state.stage = "dashboard"
            st.session_state.ra_result = None
            st.rerun()

    # ── BANNER ───────────────────────────────────────────────────
    st.markdown("""
    <div class="ra-banner">
        <div class="ra-banner-title">Resume Analysis</div>
        <div class="ra-banner-sub">
            Upload your resume and select your target job role. SCIS will
            analyse your skills, identify gaps, and give you a personalised
            improvement plan to make your resume job-ready.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── INPUTS ───────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="ra-section-label">Select Target Job Role</div>',
                    unsafe_allow_html=True)
        job_role = st.selectbox("", list(JOB_ROLES.keys()), key="ra_role",
                                label_visibility="collapsed")
    with col2:
        st.markdown('<div class="ra-section-label">Upload Your Resume (PDF or TXT)</div>',
                    unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["pdf","txt"], key="ra_upload",
                                    label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        analyse = st.button("Analyse My Resume", key="ra_analyse")

    # ── ANALYSIS LOGIC ────────────────────────────────────────────
    if analyse:
        if uploaded is None:
            st.warning("Please upload your resume first.")
        else:
            # Extract text
            raw = ""
            if uploaded.type == "application/pdf":
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
                        raw = " ".join(p.extract_text() or "" for p in pdf.pages)
                except Exception:
                    try:
                        uploaded.seek(0)
                        raw = uploaded.read().decode("latin-1", errors="ignore")
                    except Exception:
                        raw = ""
            else:
                raw = uploaded.read().decode("utf-8", errors="ignore")

            text = raw.lower()

            role_data      = JOB_ROLES[job_role]
            important      = role_data["important"]
            advanced       = role_data["advanced"]
            tips           = role_data["improve_tips"]

            found_imp      = [s for s in important if s in text]
            missing_imp    = [s for s in important if s not in text]
            found_adv      = [s for s in advanced  if s in text]
            missing_adv    = [s for s in advanced  if s not in text]

            total          = len(important)
            score_pct      = round(len(found_imp) / total * 100, 1) if total else 0

            st.session_state.ra_result = {
                "role": job_role, "score": score_pct,
                "found": found_imp, "missing": missing_imp,
                "bonus": found_adv, "missing_adv": missing_adv,
                "tips": tips,
            }
            # ── FIREBASE: save resume analysis ────────────────
            if FIREBASE_ON:
                save_resume_analysis(
                    username    = st.session_state.get("username", "unknown"),
                    job_role    = job_role,
                    score       = score_pct,
                    found       = found_imp,
                    missing     = missing_imp,
                    missing_adv = missing_adv,
                )
            st.rerun()

    # ── RESULTS ───────────────────────────────────────────────────
    if st.session_state.get("ra_result"):
        r = st.session_state.ra_result

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="ra-section-label">Analysis Results</div>',
                    unsafe_allow_html=True)

        # Verdict
        if r["score"] >= 75:
            st.markdown(f'<div class="verdict-great">Strong Resume for {r["role"]} — Score: {r["score"]}%</div>',
                        unsafe_allow_html=True)
        elif r["score"] >= 45:
            st.markdown(f'<div class="verdict-ok">Moderate Match for {r["role"]} — Score: {r["score"]}% — Room to Improve</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="verdict-low">Low Match for {r["role"]} — Score: {r["score"]}% — Significant Gaps Found</div>',
                        unsafe_allow_html=True)

        # Score + gauge
        col_s, col_d = st.columns([1, 2])
        with col_s:
            st.markdown(f"""
            <div class="ra-result-box" style="text-align:center;">
                <div class="ra-result-title">Match Score</div>
                <div class="ra-score-big">{r['score']}%</div>
                <div class="ra-score-label">for {r['role']}</div>
                <div class="ra-gauge-track">
                    <div class="ra-gauge-fill" style="width:{r['score']}%;"></div>
                </div>
                <div style="font-family:'Times New Roman',serif;font-size:.85rem;color:#880e4f;">
                    {len(r['found'])} of {len(r['found'])+len(r['missing'])} important skills found
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_d:
            if r["found"]:
                st.markdown('<div class="ra-section-label">Important Skills Found</div>',
                            unsafe_allow_html=True)
                chips = "".join(f'<span class="chip-found">{s.title()}</span>' for s in r["found"])
                st.markdown(f'<div class="ra-chips">{chips}</div>', unsafe_allow_html=True)

            if r["missing"]:
                st.markdown('<div class="ra-section-label">Missing Important Skills</div>',
                            unsafe_allow_html=True)
                chips = "".join(f'<span class="chip-missing">{s.title()}</span>' for s in r["missing"])
                st.markdown(f'<div class="ra-chips">{chips}</div>', unsafe_allow_html=True)

            if r["bonus"]:
                st.markdown('<div class="ra-section-label">Advanced Skills Found</div>',
                            unsafe_allow_html=True)
                chips = "".join(f'<span class="chip-bonus">{s.title()}</span>' for s in r["bonus"])
                st.markdown(f'<div class="ra-chips">{chips}</div>', unsafe_allow_html=True)

            if r.get("missing_adv"):
                st.markdown('<div class="ra-section-label">Advanced Skills to Add</div>',
                            unsafe_allow_html=True)
                chips = "".join(f'<span class="chip-missing">{s.title()}</span>' for s in r["missing_adv"])
                st.markdown(f'<div class="ra-chips">{chips}</div>', unsafe_allow_html=True)

        # Improvement tips
        st.markdown('<div class="ra-section-label">How to Improve Your Resume</div>',
                    unsafe_allow_html=True)
        for i, tip in enumerate(r["tips"], 1):
            st.markdown(f'<div class="tip-card"><span class="tip-num">{i}.</span>{tip}</div>',
                        unsafe_allow_html=True)

        # If score is high — extra tips for great resumes
        if r["score"] >= 75:
            st.markdown('<div class="ra-section-label">Since Your Resume Looks Strong — Go Further</div>',
                        unsafe_allow_html=True)
            extra = [
                "Tailor your resume for each specific company — mirror keywords from the job description.",
                "Add a 2–3 line professional summary at the top highlighting your strongest value proposition.",
                "Quantify every achievement with numbers, percentages or business impact.",
                "Request LinkedIn recommendations from your managers or internship supervisors.",
                "Keep your resume to 1 page (fresher) or 2 pages max — remove outdated or irrelevant content.",
            ]
            for i, tip in enumerate(extra, 1):
                st.markdown(f'<div class="tip-card"><span class="tip-num">{i}.</span>{tip}</div>',
                            unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)


# Module 04 (Student Tracking) has been removed.



# ══════════════════════════════════════════════════════════════
#  PAGE — MODULE 04: INTERVIEW PREP CHATBOT
# ══════════════════════════════════════════════════════════════
def show_interview_prep():
    username = st.session_state.get("username", "student")

    if "ip_messages" not in st.session_state:
        st.session_state.ip_messages = []
    if "ip_greeted" not in st.session_state:
        st.session_state.ip_greeted = False

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    #MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stSidebar"],footer{display:none !important;}
    .block-container{padding:0 !important;max-width:100% !important;}
    [data-testid="stAppViewContainer"]{
        background:linear-gradient(145deg,#0d0600 0%,#1a0c00 50%,#0d0600 100%) !important;}
    [data-testid="stAppViewContainer"]>.main,
    [data-testid="stAppViewContainer"] section{background:transparent !important;}

    /* top bar */
    .ip-topbar{display:flex;align-items:center;justify-content:space-between;
        padding:.9rem 2.2rem;background:rgba(251,146,60,.05);
        border-bottom:2px solid rgba(251,146,60,.2);}
    .ip-logo{font-family:'Inter',sans-serif;font-size:1rem;font-weight:800;
        color:#fb923c;display:flex;align-items:center;gap:.5rem;}
    .ip-tag{font-family:'Inter',sans-serif;font-size:.68rem;font-weight:700;
        color:rgba(251,146,60,.45);letter-spacing:2.5px;text-transform:uppercase;}

    /* banner */
    .ip-banner{background:linear-gradient(135deg,#1a0800 0%,#2d1400 50%,#1a0800 100%);
        border-bottom:2px solid rgba(251,146,60,.15);padding:1.5rem 2.5rem 1.3rem;}
    .ip-banner-title{font-family:'Inter',sans-serif;
        font-size:clamp(1.4rem,3vw,2rem);font-weight:900;color:#fb923c;margin-bottom:.3rem;}
    .ip-banner-sub{font-family:'Inter',sans-serif;font-size:.86rem;
        color:rgba(251,146,60,.6);line-height:1.6;}
    .ip-banner-sub b{color:#fb923c;}

    /* chat bubbles */
    .ip-chat-wrap{padding:1.2rem 2.5rem 0;max-height:50vh;overflow-y:auto;}
    .ip-bubble-user{display:flex;justify-content:flex-end;margin-bottom:.75rem;}
    .ip-bubble-bot{display:flex;justify-content:flex-start;margin-bottom:.75rem;}
    .ip-msg-user{background:rgba(251,146,60,.18);border:1px solid rgba(251,146,60,.35);
        border-radius:18px 18px 4px 18px;padding:.65rem 1rem;max-width:65%;
        font-family:'Inter',sans-serif;font-size:.88rem;color:#fb923c;line-height:1.5;}
    .ip-msg-bot{background:rgba(255,255,255,.05);border:1px solid rgba(251,146,60,.14);
        border-radius:18px 18px 18px 4px;padding:.7rem 1.1rem;max-width:78%;
        font-family:'Inter',sans-serif;font-size:.87rem;
        color:rgba(255,255,255,.88);line-height:1.7;}
    .ip-msg-bot b{color:#fb923c;}
    .ip-msg-bot ul{margin:.35rem 0 .25rem 1.1rem;padding:0;}
    .ip-msg-bot li{margin:.25rem 0;}
    .ip-msg-bot .q-num{color:rgba(251,146,60,.55);font-size:.75rem;
        font-weight:700;margin-right:.3rem;}

    /* section header inside bot message */
    .ip-sec-hdr{font-family:'Inter',sans-serif;font-size:.7rem;font-weight:800;
        color:#fb923c;letter-spacing:2.5px;text-transform:uppercase;
        margin:1rem 0 .5rem;border-bottom:1px solid rgba(251,146,60,.2);
        padding-bottom:.3rem;}

    /* input row */
    .ip-input-row{padding:.9rem 2.5rem 1.4rem;
        border-top:1px solid rgba(251,146,60,.1);margin-top:.6rem;}
    div[data-testid="stTextInput"] input{
        background:rgba(255,255,255,.05) !important;
        border:1.5px solid rgba(251,146,60,.3) !important;
        border-radius:12px !important;color:#fb923c !important;
        font-family:'Inter',sans-serif !important;font-size:.9rem !important;}
    div[data-testid="stTextInput"] input::placeholder{color:rgba(251,146,60,.3) !important;}
    div[data-testid="stTextInput"] input:focus{
        border-color:#fb923c !important;
        box-shadow:0 0 0 2px rgba(251,146,60,.12) !important;}
    div[data-testid="stButton"]>button{
        background:rgba(251,146,60,.1) !important;
        border:1.5px solid rgba(251,146,60,.35) !important;
        border-radius:10px !important;color:#fb923c !important;
        font-family:'Inter',sans-serif !important;
        font-size:.88rem !important;font-weight:700 !important;
        padding:.5rem 1.2rem !important;box-shadow:none !important;}
    div[data-testid="stButton"]>button:hover{
        background:rgba(251,146,60,.2) !important;border-color:#fb923c !important;}
    </style>
    """, unsafe_allow_html=True)

    # top bar
    st.markdown('''
    <div class="ip-topbar">
        <div class="ip-logo">🎓 <span style="color:#000">SCIS</span></div>
        <span class="ip-tag">Module 04 · Interview Prep Bot</span>
    </div>
    ''', unsafe_allow_html=True)

    # back button
    col_back, _ = st.columns([1, 7])
    with col_back:
        if st.button("Back", key="ip_back"):
            st.session_state.stage = "dashboard"
            st.session_state.ip_messages = []
            st.session_state.ip_greeted  = False
            st.rerun()

    st.markdown('''
    <div class="ip-banner">
        <div class="ip-banner-title">Interview Preparation Assistant</div>
        <div class="ip-banner-sub">
            Say <b>hi</b> to get started. Ask questions by topic —
            e.g. <em>"Python questions"</em>, <em>"DSA questions"</em>,
            <em>"HR questions"</em>, or <em>"full set"</em>.
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── Question bank — 7 structured topics ──────────────────────
    QB = {
        "technical_core": {
            "label": "Technical Core  (OOPS · DBMS · OS Basics)",
            "questions": [
                "What are the four pillars of OOP? Explain each with an example.",
                "What is the difference between Abstraction and Encapsulation?",
                "Explain method overloading vs method overriding.",
                "What is normalization? Explain 1NF, 2NF, and 3NF with examples.",
                "What are ACID properties in a database?",
                "What is the difference between primary key, foreign key, and unique key?",
                "Explain indexing in databases and why it speeds up queries.",
                "What is a transaction? What is a deadlock in databases?",
                "What is the difference between SQL and NoSQL databases?",
                "What is a stored procedure? How is it different from a function?",
            ]
        },
        "dsa": {
            "label": "Data Structures & Algorithms",
            "questions": [
                "What is the time and space complexity of binary search?",
                "Explain the difference between BFS and DFS with use cases.",
                "What is dynamic programming? Explain with the Fibonacci example.",
                "What is the difference between a stack and a queue? Give real-world uses.",
                "How does a hash table work? How is collision handled?",
                "Compare merge sort and quick sort — time complexity and stability.",
                "What are the types of linked lists? What are their advantages?",
                "What is a binary search tree? What are its properties and operations?",
                "Explain the concept of a min-heap and max-heap.",
                "What is Dijkstra's algorithm? Explain its working and complexity.",
            ]
        },
        "python": {
            "label": "Python Programming",
            "questions": [
                "What are Python decorators? Write a simple example.",
                "Explain list comprehension vs generator expressions.",
                "What is the difference between a list and a tuple? When to use each?",
                "What are *args and **kwargs? How are they used?",
                "Explain how Python manages memory (garbage collection, reference counting).",
                "What is the GIL (Global Interpreter Lock)? How does it affect multithreading?",
                "What is the difference between shallow copy and deep copy?",
                "How does exception handling work in Python? Explain try/except/else/finally.",
                "What are lambda functions? When would you use them over regular functions?",
                "Explain the difference between a module, a package, and a library.",
            ]
        },
        "ml": {
            "label": "Machine Learning / AI",
            "questions": [
                "What is overfitting and underfitting? How do you handle each?",
                "Explain the bias-variance tradeoff.",
                "What is the difference between supervised, unsupervised, and reinforcement learning?",
                "How does a Random Forest work? What makes it better than a single decision tree?",
                "What is cross-validation? Why is k-fold preferred over a simple train-test split?",
                "What is the difference between classification and regression? Give examples.",
                "Explain gradient descent. What are batch, stochastic, and mini-batch variants?",
                "What is a confusion matrix? Define precision, recall, F1-score, and accuracy.",
                "What is feature engineering? Give examples of techniques.",
                "Explain PCA — what it does, when to use it, and its limitations.",
            ]
        },
        "networking": {
            "label": "Computer Networks",
            "questions": [
                "Explain the OSI model — name and describe all 7 layers.",
                "What is the difference between TCP and UDP? When would you use each?",
                "Explain the TCP three-way handshake (SYN, SYN-ACK, ACK).",
                "What is DNS? Walk through what happens when you type a URL in a browser.",
                "What is the difference between HTTP and HTTPS? What does SSL/TLS do?",
                "What is an IP address? What is the difference between IPv4 and IPv6?",
                "What is subnetting? Why is it used?",
                "What is ARP (Address Resolution Protocol) and how does it work?",
                "What is the difference between a router, a switch, and a hub?",
                "What is a firewall? What are the types of firewalls?",
            ]
        },
        "os": {
            "label": "Operating Systems",
            "questions": [
                "What is a deadlock? State the four Coffman conditions.",
                "Explain paging and segmentation. What is the difference?",
                "What is the difference between preemptive and non-preemptive scheduling?",
                "Explain semaphore and mutex. What is the difference?",
                "What is thrashing in an OS? How is it prevented?",
                "What is context switching? What is the overhead involved?",
                "Explain the producer-consumer problem and its solution.",
                "Name and explain CPU scheduling algorithms (FCFS, SJF, Round Robin, Priority).",
                "What is a system call? Give examples.",
                "What is virtual memory? How does demand paging work?",
            ]
        },
        "hr": {
            "label": "HR / Behavioural",
            "questions": [
                "Tell me about yourself. (Structure: Education → Skills → Projects → Goal)",
                "What are your greatest strengths? (Give 2-3 with evidence)",
                "What is your biggest weakness? (Be honest + show improvement)",
                "Where do you see yourself in 5 years?",
                "Why do you want to join this company specifically?",
                "Describe a time you worked in a team and faced a conflict. How did you resolve it?",
                "Tell me about your most challenging project. What did you learn?",
                "How do you handle pressure and tight deadlines?",
                "What makes you different from other candidates?",
                "Do you have any questions for us? (Always ask at least one!)",
            ]
        },
    }

    # ── Auto-greet ────────────────────────────────────────────────
    if not st.session_state.ip_greeted:
        greeting = (
            "Hi, buddy! I am your Interview Prep Assistant.\n\n"
            "The interview questions you MUST prepare are structured into 7 topics:\n"
            "- Technical Core (OOPS, DBMS, OS Basics)\n"
            "- Data Structures and Algorithms (DSA)\n"
            "- Python Programming\n"
            "- Machine Learning / AI\n"
            "- Computer Networks\n"
            "- Operating Systems\n"
            "- HR / Behavioural\n\n"
            "Just ask me any topic to get the questions. Examples:\n"
            "- Python questions\n"
            "- DSA questions\n"
            "- HR questions\n"
            "- OS questions\n"
            "- networking questions\n"
            "- ML questions\n"
            "- technical core questions\n"
            "- full set (get all 70 questions)"
        )
        st.session_state.ip_messages.append({"role": "bot", "text": greeting})
        st.session_state.ip_greeted = True

    # ── Render messages ───────────────────────────────────────────
    st.markdown('<div class="ip-chat-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.ip_messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="ip-bubble-user"><div class="ip-msg-user">{msg["text"]}</div></div>',
                unsafe_allow_html=True)
        else:
            import re as _re
            raw = msg["text"]
            # bold **text**
            raw = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', raw)
            lines  = raw.split("\n")
            chunks = []
            in_ul  = False
            for ln in lines:
                s = ln.strip()
                if s.startswith("- "):
                    if not in_ul:
                        chunks.append("<ul>"); in_ul = True
                    chunks.append(f"<li>{s[2:]}</li>")
                else:
                    if in_ul:
                        chunks.append("</ul>"); in_ul = False
                    if s:
                        chunks.append(f"<p style='margin:.15rem 0'>{s}</p>")
                    else:
                        chunks.append("<div style='height:.4rem'></div>")
            if in_ul: chunks.append("</ul>")
            html = "".join(chunks)
            st.markdown(
                f'<div class="ip-bubble-bot"><div class="ip-msg-bot">{html}</div></div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────
    st.markdown('<div class="ip-input-row">', unsafe_allow_html=True)
    ic1, ic2 = st.columns([5, 1])
    with ic1:
        user_input = st.text_input(
            "", key="ip_input",
            placeholder="e.g. Python questions / DSA questions / full set...",
            label_visibility="collapsed")
    with ic2:
        send_btn = st.button("Send", key="ip_send")
    st.markdown('</div>', unsafe_allow_html=True)

    if send_btn and user_input.strip():
        user_text = user_input.strip()
        st.session_state.ip_messages.append({"role": "user", "text": user_text})
        low = user_text.lower()

        # detect intent
        keys = []
        if any(w in low for w in ["hi", "hello", "hey", "start"]):
            reply = (
                "Hi again, buddy! Here are the topics you can ask me about:\n"
                "- Python questions\n"
                "- DSA questions\n"
                "- HR questions\n"
                "- OS questions\n"
                "- networking questions\n"
                "- ML questions\n"
                "- technical core questions\n"
                "- full set"
            )
        elif any(w in low for w in ["full", "all", "everything", "complete", "all topics", "every topic"]):
            keys  = list(QB.keys())
            reply = None
        elif any(w in low for w in ["python", "py", "django", "flask"]):
            keys = ["python"]; reply = None
        elif any(w in low for w in ["dsa", "data structure", "algorithm", "sorting", "tree", "graph", "linked list", "array"]):
            keys = ["dsa"]; reply = None
        elif any(w in low for w in ["ml", "machine learning", "ai", "artificial intelligence", "random forest", "neural"]):
            keys = ["ml"]; reply = None
        elif any(w in low for w in ["network", "tcp", "udp", "osi", "http", "dns", "ip address"]):
            keys = ["networking"]; reply = None
        elif any(w in low for w in ["os", "operating system", "deadlock", "scheduling", "memory management", "process"]):
            keys = ["os"]; reply = None
        elif any(w in low for w in ["hr", "behavioural", "behavioral", "soft skill", "tell me about", "strengths", "weakness"]):
            keys = ["hr"]; reply = None
        elif any(w in low for w in ["technical", "core", "cs", "dbms", "database", "oops", "object oriented", "sql"]):
            keys = ["technical_core"]; reply = None
        else:
            reply = (
                "I didn't recognise that topic. Try one of these:\n"
                "- **Python questions**\n"
                "- **DSA questions**\n"
                "- **HR questions**\n"
                "- **OS questions**\n"
                "- **networking questions**\n"
                "- **ML questions**\n"
                "- **technical core questions**\n"
                "- **full set** (all 70 questions)"
            )

        if keys:
            parts = []
            for k in keys:
                sec = QB[k]
                numbered = "\n".join(f"- **{i+1}.** {q}" for i, q in enumerate(sec["questions"]))
                parts.append(f"**{sec['label']}**\n{numbered}")
            reply = "Here are your interview questions to prepare:\n\n" + "\n\n".join(parts)

        st.session_state.ip_messages.append({"role": "bot", "text": reply})
        st.rerun()

# ── ROUTER ────────────────────────────────────────────────────
stage = st.session_state.stage
if   stage == 'loading':                    show_loading()
elif stage == 'login':                      show_login()
elif stage == 'career_prediction':          show_career_prediction()
elif stage == 'improvement_recommendations':show_improvement_recommendations()
elif stage == 'resume_analysis':            show_resume_analysis()
elif stage == 'product':                    show_product()
elif stage == 'pricing':                    show_pricing()
elif stage == 'interview_prep':             show_interview_prep()
else:                                       show_dashboard()