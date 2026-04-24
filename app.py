import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import io, json
from anthropic import Anthropic

st.set_page_config(page_title="LinkedIn Analytics Analyzer", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

RED   = "#FB8500"
CREAM = "#EAF4FB"
DARK  = "#0D1B2A"
BLUE  = "#8ECAE6"
BAS_URL = "https://www.linkedin.com/in/bas-oudshoorn/"

SECTORS = {
    "Life Sciences & Health":           {"engagement": 3.3,  "frequency": "4-5x/week", "follower_growth": 20},
    "Tech & Software":                  {"engagement": 3.6,  "frequency": "3-5x/week", "follower_growth": 25},
    "Finance & Professional Services":  {"engagement": 2.6,  "frequency": "3-4x/week", "follower_growth": 15},
    "Government & Non-profit":          {"engagement": 2.8,  "frequency": "2-3x/week", "follower_growth": 10},
    "Education & Research":             {"engagement": 3.2,  "frequency": "2-4x/week", "follower_growth": 14},
    "Manufacturing & Industry":         {"engagement": 4.0,  "frequency": "2-3x/week", "follower_growth": 12},
    "Marketing & Communications":       {"engagement": 2.5,  "frequency": "4-5x/week", "follower_growth": 18},
    "Retail & E-commerce":              {"engagement": 3.9,  "frequency": "3-5x/week", "follower_growth": 22},
    "Real Estate & Construction":       {"engagement": 3.5,  "frequency": "2-3x/week", "follower_growth": 12},
    "Other":                            {"engagement": 3.85, "frequency": "3-4x/week", "follower_growth": 15},
}

DAG_EN = {"Monday":"Mon","Tuesday":"Tue","Wednesday":"Wed","Thursday":"Thu","Friday":"Fri","Saturday":"Sat","Sunday":"Sun"}
TOTAL_STEPS = 7

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');
html,body,[class*="css"]{{font-family:'Sora',sans-serif;}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding-top:2rem;max-width:1100px;}}
.hero{{background:{DARK};border-radius:20px;padding:3.5rem 3rem 3rem;margin-bottom:2rem;color:white;position:relative;overflow:hidden;}}
.hero::after{{content:'';position:absolute;bottom:-60px;right:-60px;width:300px;height:300px;background:{BLUE};opacity:0.15;border-radius:50%;}}
.hero h1{{font-family:'Lora',serif;font-size:3rem;font-weight:600;margin:0 0 .75rem;line-height:1.15;color:{CREAM};}}
.hero p{{font-size:1.1rem;opacity:.8;margin:0;max-width:560px;line-height:1.7;color:{CREAM};}}
.progress-wrap{{display:flex;gap:6px;margin-bottom:2rem;align-items:center;}}
.progress-step{{height:5px;flex:1;border-radius:3px;background:#e0d8cc;transition:background .4s;}}
.progress-step.done{{background:{BLUE};}}
.progress-step.active{{background:{RED};}}
.stButton button{{border-radius:50px!important;font-family:'Sora',sans-serif!important;font-weight:500!important;transition:all .2s!important;}}
.stButton button[kind="primary"]{{background:{RED}!important;border:none!important;color:white!important;}}
.stButton button[kind="primary"]:hover{{background:#c96a00!important;transform:translateY(-1px)!important;}}

.stButton button[kind="secondary"]{{background:transparent!important;border:1.5px solid #d8d0c4!important;color:{DARK}!important;}}
.kpi-card{{background:white;border:1.5px solid #e8e2d8;border-radius:16px;padding:1.25rem 1.5rem;}}
.kpi-label{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#888;margin-bottom:6px;font-weight:500;}}
.kpi-value{{font-size:2rem;font-weight:600;color:{DARK};line-height:1;}}
.kpi-delta{{font-size:12px;margin-top:4px;}}
.kpi-delta.pos{{color:#057642;}}
.kpi-delta.neg{{color:{RED};}}
.kpi-benchmark{{font-size:11px;color:#888;margin-top:3px;}}
.section-head{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.09em;color:#999;margin:2rem 0 .75rem;}}
.ai-box{{background:{CREAM};border:1.5px solid #e8d8b0;border-left:4px solid {RED};border-radius:0 16px 16px 0;padding:1.5rem;font-size:15px;line-height:1.8;color:{DARK};margin:1rem 0;}}
.hint-box{{background:#f8f5f0;border-radius:10px;padding:.85rem 1rem;font-size:13px;color:#666;margin-top:.5rem;line-height:1.6;}}
.hint-box code{{background:#ede8e0;padding:1px 6px;border-radius:5px;font-size:12px;}}
.cta-banner{{background:{DARK};border-radius:16px;padding:2rem 2.5rem;display:flex;align-items:center;justify-content:space-between;margin-top:3rem;gap:1rem;}}
.cta-text{{color:{CREAM};font-size:15px;line-height:1.6;}}
.cta-text strong{{color:white;font-size:17px;display:block;margin-bottom:4px;}}
.cta-btn{{background:white;color:{RED};border:2px solid white;padding:12px 28px;border-radius:50px;font-size:14px;font-weight:700;cursor:pointer;white-space:nowrap;text-decoration:none;font-family:'Sora',sans-serif;}}
.welcome-msg{{font-family:'Lora',serif;font-size:1.5rem;color:{DARK};margin-bottom:.5rem;font-style:italic;}}
.stTabs [data-baseweb="tab-list"]{{gap:6px;border-bottom:2px solid #e8e2d8;}}
.stTabs [data-baseweb="tab"]{{font-size:13px;font-weight:500;padding:10px 18px;border-radius:8px 8px 0 0;background:#e8f4fb;border:1px solid #c8e6f5;border-bottom:none;}}
.stTabs [aria-selected="true"]{{background:white!important;border-color:#e8e2d8!important;}}
.bench-card{{background:{CREAM};border:1.5px solid #e8d8b0;border-radius:14px;padding:1.25rem 1.5rem;margin-top:1rem;margin-bottom:1.5rem;line-height:1.8;color:{DARK};font-size:14px;}}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_content(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df = pd.read_excel(xl, sheet_name="Alle bijdragen", header=1, skiprows=[0])
    df.columns = ["Titel","Link","Soort","Campagne","Geplaatst_door","Aangemaakt","Campagne_start","Campagne_eind","Doelgroep","Weergaven","Weergaven2","Weergaven_buiten","Klikken","CTR","Interessant","Commentaren","Reposts","Gevolgd","Engagement_pct","Type_content"]
    df = df[df["Aangemaakt"].notna()].copy()
    df["Aangemaakt"] = pd.to_datetime(df["Aangemaakt"], errors="coerce")
    df = df[df["Aangemaakt"].notna()]
    df["Type_content"] = df["Type_content"].fillna("Text/Image")
    df["Day"] = df["Aangemaakt"].dt.day_name()
    df["Month"] = df["Aangemaakt"].dt.to_period("M").astype(str)
    df["Title_short"] = df["Titel"].str.replace("\xa0"," ").str.replace("\n"," ").str.strip().str[:80]
    for col in ["Weergaven","Klikken","Interessant","Commentaren","Reposts"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["Engagement_pct"] = pd.to_numeric(df["Engagement_pct"], errors="coerce").fillna(0)*100
    ds = pd.read_excel(xl, sheet_name="Statistieken", header=1, skiprows=[0])
    ds.columns = ["Datum","Weergaven_spontaan","Weergaven_gesponsord","Weergaven_totaal","Unieke_weergaven","Klikken_spontaan","Klikken_gesponsord","Klikken_totaal","Reacties_spontaan","Reacties_gesponsord","Reacties_totaal","Comments_spontaan","Comments_gesponsord","Comments_totaal","Reposts_spontaan","Reposts_gesponsord","Reposts_totaal","Engagement_spontaan","Engagement_gesponsord","Engagement_totaal"]
    ds["Datum"] = pd.to_datetime(ds["Datum"], errors="coerce")
    ds = ds[ds["Datum"].notna()]
    return df, ds

@st.cache_data(show_spinner=False)
def load_followers(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    g = pd.read_excel(xl, sheet_name="Nieuwe volgers")
    g["Datum"] = pd.to_datetime(g["Datum"])
    sheets = {s: pd.read_excel(xl, sheet_name=s) for s in ["Locatie","Functie","Senioriteitsniveau","Branche","Bedrijfsgrootte"]}
    return g, sheets

@st.cache_data(show_spinner=False)
def load_visitors(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df = pd.read_excel(xl, sheet_name="Statistieken over bezoekers")
    df["Datum"] = pd.to_datetime(df["Datum"])
    sheets = {s: pd.read_excel(xl, sheet_name=s) for s in ["Locatie","Functie","Senioriteitsniveau","Branche","Bedrijfsgrootte"]}
    return df, sheets

@st.cache_data(show_spinner=False)
def load_competitors(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
    # Try to find the right sheet
    sheet = None
    for s in xl.sheet_names:
        if "COMPETITOR" in s.upper() or "competitor" in s.lower():
            sheet = s
            break
    if sheet is None:
        sheet = xl.sheet_names[0]
    df = pd.read_excel(xl, sheet_name=sheet, header=1)
    # Rename columns based on position
    cols = list(df.columns)
    rename = {}
    for i, c in enumerate(cols):
        if i == 0: rename[c] = "Pagina"
        elif i == 1: rename[c] = "Nieuwe_volgers"
        elif i == 2: rename[c] = "Bijdragen"
        elif i == 3: rename[c] = "Commentaren"
        elif i == 4: rename[c] = "Commentaren_per_dag"
        elif i == 5: rename[c] = "Reacties"
    df = df.rename(columns=rename)
    df = df[df["Pagina"].notna()]
    # Remove header/total rows
    df = df[~df["Pagina"].astype(str).str.contains("Pagina|Total|Totaal", case=False, na=False)]
    return df

def bl(**kw):
    return dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(family="Sora,sans-serif",size=12,color="#555"),margin=dict(l=0,r=0,t=24,b=0),**kw)

def kpi(label,value,delta=None,pos=True,benchmark=None):
    dh = f'<div class="kpi-delta {"pos" if pos else "neg"}">{delta}</div>' if delta else ""
    bh = f'<div class="kpi-benchmark">Benchmark: {benchmark}</div>' if benchmark else ""
    return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{dh}{bh}</div>'

def hbar(df,x,y,color,h=220):
    fig = go.Figure(go.Bar(x=df[x],y=df[y],orientation="h",marker_color=color,text=df[x].apply(lambda v:f"{v:,.0f}".replace(",",".")),textposition="outside"))
    fig.update_layout(**bl(height=h),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
    return fig

def post_table(df,bench):
    d = df[["Title_short","Aangemaakt","Day","Weergaven","Interessant","Commentaren","Engagement_pct"]].copy()
    d["Aangemaakt"] = d["Aangemaakt"].dt.strftime("%Y-%m-%d")
    d["Day"] = d["Day"].map(DAG_EN)
    d["vs benchmark"] = d["Engagement_pct"].apply(lambda v: f"+{v-bench:.1f}%" if v>=bench else f"{v-bench:.1f}%")
    d["Engagement_pct"] = d["Engagement_pct"].round(1).astype(str)+"%"
    d.columns = ["Post","Date","Day","Views","Likes","Comments","Engagement","vs benchmark"]
    d["Views"] = d["Views"].apply(lambda v: f"{v:,}".replace(",","."))
    st.dataframe(d,use_container_width=True,hide_index=True)

def ai_diag(df_posts,df_stats,sector,bench_eng,api_key):
    client = Anthropic(api_key=api_key)
    monthly = df_stats.copy()
    monthly["Month"] = monthly["Datum"].dt.to_period("M").astype(str)
    ma = monthly.groupby("Month").agg(Views=("Weergaven_totaal","sum")).reset_index()
    top = df_posts.nlargest(3,"Weergaven")[["Title_short","Engagement_pct","Weergaven"]].to_dict("records")
    avg = df_posts[df_posts["Engagement_pct"]>0]["Engagement_pct"].median()
    ppw = len(df_posts)/max((df_posts["Aangemaakt"].max()-df_posts["Aangemaakt"].min()).days/7,1)
    bd = df_posts.groupby("Day")["Engagement_pct"].mean().idxmax() if len(df_posts) else "unknown"
    prompt = f"""You are a sharp, experienced LinkedIn content strategist.
Sector: {sector}, Benchmark: {bench_eng}%, Their median engagement: {avg:.1f}%, Posts/week: {ppw:.1f}, Best day: {bd}, Total posts: {len(df_posts)}
Top 3 posts: {json.dumps(top)}
Monthly views (last 6): {ma.tail(6).to_dict("records")}

Write in two parts:

PART 1 — DIAGNOSIS (3 short paragraphs, max 150 words):
A direct, clear read on their performance. Start with one genuine strength backed by their data. Then identify the key opportunity. Keep it sharp and professional — like a trusted advisor, not a cheerleader.

PART 2 — 5 ACTIONABLE IMPROVEMENTS (exactly 5 items):
Format each as: [NUMBER]. [BOLD ACTION TITLE]: [one concrete sentence explaining what to do and why]
Base these on their actual data. Make them specific and immediately actionable.

Separate the two parts with this exact line: ---ACTIONS---"""
    r = client.messages.create(model="claude-sonnet-4-5",max_tokens=600,messages=[{"role":"user","content":prompt}])
    return r.content[0].text

def write_to_sheet(name, email, company, sector, followers):
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1b29ihr0-Yt7Imz-wRStTo-SJ7iF8kY4-88tvVo1Bq_0").sheet1
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            name, email, company, sector, followers
        ])
        return True, None
    except Exception as e:
        return False, str(e)

def get_user_count():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1b29ihr0-Yt7Imz-wRStTo-SJ7iF8kY4-88tvVo1Bq_0").sheet1
        return max(0, len(sheet.get_all_values()) - 1)  # minus header row
    except:
        return 0

def ai_draft_feedback(draft, sector, bench_eng, api_key):
    client = Anthropic(api_key=api_key)
    prompt = f"""You are an experienced LinkedIn content strategist reviewing a draft post for a {sector} company.
Sector engagement benchmark: {bench_eng}%

DRAFT POST:
{draft}

Give structured feedback in this format:

HOOK: [score 1-10] — [one sentence on whether the opening grabs attention and why]
CLARITY: [score 1-10] — [one sentence on how clear and scannable it is]
CTA: [score 1-10] — [one sentence on whether there is a clear next step]
TONE: [one sentence on whether the tone fits a B2B LinkedIn audience]

READY TO POST: [Yes / Almost / Not yet] — [one sentence summary]

TOP 2 SUGGESTIONS:
1. [specific, actionable improvement — do not rewrite the post]
2. [specific, actionable improvement — do not rewrite the post]

Be direct and professional. Do not rewrite the post. Plain text only, no markdown."""
    r = client.messages.create(model="claude-sonnet-4-5", max_tokens=600,
        messages=[{"role": "user", "content": prompt}])
    return r.content[0].text

def ai_audit(posts_text,top_performers,sector,api_key):
    client = Anthropic(api_key=api_key)
    prompt = f"""You are an experienced LinkedIn content strategist reviewing posts for a {sector} company.
TOP PERFORMING POSTS (reference for what works): {top_performers}
POSTS TO REVIEW: {posts_text}

Review ALL posts. For each post output EXACTLY this format on TWO lines:
POST [N] | Hook [X]/10 | Clarity [X]/10 | CTA [X]/10 | Overall [X]/10
[One clear sentence of honest, constructive feedback.] To improve: [one specific action.]

After all posts, output:
WHAT'S WORKING: [2-3 specific strengths]
TOP OPPORTUNITY: [one high-impact improvement]

Tone: direct and professional, like a trusted advisor. Not harsh, not soft. Plain text only, no markdown, no hashtags."""
    r = client.messages.create(model="claude-sonnet-4-5",max_tokens=2500,messages=[{"role":"user","content":prompt}])
    return r.content[0].text

# Session state
for k,v in {"step":1,"email":"","name":"","company":"","sector":"Other","current_followers":0,"df_posts":None,"df_stats":None,"fol_growth":None,"fol_sheets":None,"vis_data":None,"vis_sheets":None,"df_comp":None}.items():
    if k not in st.session_state: st.session_state[k] = v

step = st.session_state.step

# Check user limit before showing anything
if step != 99:
    if get_user_count() >= 50:  # change to 50 after testing
        st.session_state.step = 99
        step = 99

st.markdown("""<div class="hero"><h1>Turn your LinkedIn data<br>into a strategy.</h1><p>Upload your LinkedIn exports and get a clear, AI-powered picture of what's working and what to do next.</p></div>""", unsafe_allow_html=True)

prog = '<div class="progress-wrap">'
for i,lbl in enumerate(["You","Sector","Content","Followers","Visitors","Competitors","Results"]):
    cls = "done" if i<step-1 else ("active" if i==step-1 else "")
    prog += f'<div class="progress-step {cls}" title="{lbl}"></div>'
prog += "</div>"
st.markdown(prog, unsafe_allow_html=True)

# STEP 1
if step == 1:
    st.markdown("### Welcome — let's get to know you")
    st.markdown("Tell us a bit about yourself so we can personalise your results.")
    col1,_ = st.columns([2,1])
    with col1:
        name = st.text_input("Your name", placeholder="Jane Smith")
        email = st.text_input("Work email", placeholder="jane@company.com")
        company = st.text_input("Company or page name", placeholder="Acme Corp")
        st.markdown("---")
        st.markdown("**Current follower count**: how many followers does your LinkedIn page have right now?")
        st.caption("Find this on your LinkedIn Page. We use it to show your real follower growth over time. Leave at 0 to skip.")
        current_followers = st.number_input("Current followers", min_value=0, value=0, step=100, label_visibility="collapsed")
        st.markdown("---")
        st.caption("Your LinkedIn data stays in your browser session only — never stored on our servers.")
        agree = st.toggle("Stay in the loop", value=True)
        st.caption("Occasional updates about this tool. No spam. Unsubscribe anytime.")
        if st.button("Let's go →", type="primary", use_container_width=True):
            if not email or "@" not in email: st.error("Please enter a valid email address.")
            elif not name: st.error("Please enter your name.")
            else:
                count = get_user_count()
                if count >= 50:
                    st.session_state.update({"step": 99})
                    st.rerun()
                else:
                    if agree:
                        result, err = write_to_sheet(name, email, company, "—", current_followers)
                        if not result:
                            st.warning(f"Could not save your details: {err}")
                    else:
                        write_to_sheet("—", "—", "—", "anonymous", 0)
                    st.session_state.update({"email":email,"name":name,"company":company,"current_followers":current_followers,"step":2})
                    st.rerun()

# WAITLIST
if step == 99:
    st.markdown("### We've reached capacity for now.")
    st.markdown("This tool is currently full. Leave your email below and we'll let you know when a spot opens up.")
    waitlist_name = st.text_input("Your name", placeholder="Jane Smith")
    waitlist_email = st.text_input("Your email", placeholder="you@company.com")
    if st.button("Join the waitlist →", type="primary"):
        if waitlist_email and "@" in waitlist_email and waitlist_name:
            write_to_sheet(waitlist_name, waitlist_email, "—", "waitlist", 0)
            st.success("You're on the list! We'll be in touch as soon as a spot opens up.")
        else:
            st.error("Please fill in your name and email.")
    st.stop()

# STEP 2
elif step == 2:
    st.markdown(f'<div class="welcome-msg">Good to meet you, {st.session_state.name}.</div>', unsafe_allow_html=True)
    st.markdown("### What sector are you in?")
    col1,_ = st.columns([2,1])
    with col1:
        sector = st.selectbox("Your sector", list(SECTORS.keys()))
        bench = SECTORS[sector]
        st.markdown(f'<div class="bench-card"><strong>Benchmarks for {sector}</strong><br>Average engagement rate: <strong>{bench["engagement"]}%</strong><br>Recommended posting frequency: <strong>{bench["frequency"]}</strong></div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True): st.session_state.step=1; st.rerun()
        with c2:
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.sector=sector; st.session_state.step=3; st.rerun()

# STEP 3
elif step == 3:
    st.markdown("### Step 1 of 4 — Your content data")
    st.markdown("This is the heart of the analysis — all your post performance in one file.")
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Content → click <code>Export</code> top right. Download the <code>.xls</code> file.<br><strong>Tip:</strong> Set the date range to the last 365 days for best results. A single week of data will not tell you much.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        content_files = st.file_uploader("Content export (.xls)", type=["xls"], accept_multiple_files=True)
        if content_files:
            with st.spinner("Loading your posts..."):
                try:
                    ap,as_ = [],[]
                    for f in content_files:
                        p,s = load_content(f.read()); ap.append(p); as_.append(s)
                    df_posts = pd.concat(ap,ignore_index=True).drop_duplicates(subset=["Link"],keep="last").sort_values("Aangemaakt").reset_index(drop=True)
                    df_stats = pd.concat(as_,ignore_index=True).drop_duplicates(subset=["Datum"],keep="last").sort_values("Datum").reset_index(drop=True)
                    st.session_state.df_posts = df_posts; st.session_state.df_stats = df_stats
                    st.success(f"Loaded {len(df_posts)} posts · {df_stats['Datum'].min().strftime('%b %Y')} – {df_stats['Datum'].max().strftime('%b %Y')}")
                except Exception:
                    st.error("Looks like that's not the right file. **How to get the correct one:** Go to your LinkedIn Page → Analytics → Content → click Export (top right) → download the .xls file.")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Back", use_container_width=True): st.session_state.step=2; st.rerun()
        with c2:
            if st.button("Continue →", type="primary", use_container_width=True, disabled=not content_files):
                st.session_state.step=4; st.rerun()

# STEP 4
elif step == 4:
    st.markdown("### Step 2 of 4 — Your followers")
    st.markdown("Who follows you, how your audience grows, and which industries and functions are most represented.")
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Followers → <code>Export</code>.<br><strong>Tip:</strong> Set the date range to the last 365 days for best results.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        ff = st.file_uploader("Followers export (.xls)", type=["xls"])
        if ff:
            with st.spinner("Loading..."):
                try:
                    g,s = load_followers(ff.read()); st.session_state.fol_growth=g; st.session_state.fol_sheets=s
                    st.success(f"Loaded · {int(g['Totaal aantal volgers'].sum()):,} new followers in period".replace(",","."))
                except Exception:
                    st.error("Looks like that's not the right file. **How to get the correct one:** LinkedIn Page → Analytics → Followers → Export → download the .xls file.")
        st.caption("Optional — you can skip this.")
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("Back", use_container_width=True): st.session_state.step=3; st.rerun()
        with c2:
            if st.button("Skip", use_container_width=True): st.session_state.step=5; st.rerun()
        with c3:
            if st.button("Continue →", type="primary", use_container_width=True): st.session_state.step=5; st.rerun()

# STEP 5
elif step == 5:
    st.markdown("### Step 3 of 4 — Page visitors")
    st.markdown("Understand who's landing on your LinkedIn page and what brings them there.")
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Visitors → <code>Export</code>.<br><strong>Tip:</strong> Set the date range to the last 365 days for best results.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        vf = st.file_uploader("Visitors export (.xls)", type=["xls"])
        if vf:
            try:
                vd,vs = load_visitors(vf.read()); st.session_state.vis_data=vd; st.session_state.vis_sheets=vs
                st.success("Visitors data loaded")
            except Exception:
                st.error("Looks like that's not the right file. **How to get the correct one:** LinkedIn Page → Analytics → Visitors → Export → download the .xls file.")
        st.caption("Optional — you can skip this.")
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("Back", use_container_width=True): st.session_state.step=4; st.rerun()
        with c2:
            if st.button("Skip", use_container_width=True): st.session_state.step=6; st.rerun()
        with c3:
            if st.button("Continue →", type="primary", use_container_width=True): st.session_state.step=6; st.rerun()

# STEP 6
elif step == 6:
    st.markdown("### Step 4 of 4 — Competitors")
    st.markdown("Benchmark yourself against similar LinkedIn pages.")
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Competitors → <code>Export</code>. This exports as <code>.xlsx</code>.<br><strong>Tip:</strong> Set the date range to the last 365 days for best results.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        cf = st.file_uploader("Competitors export (.xlsx)", type=["xlsx"])
        if cf:
            try:
                dc = load_competitors(cf.read()); st.session_state.df_comp=dc
                st.success(f"Loaded · {len(dc)} companies")
            except Exception:
                st.error("Looks like that's not the right file. **How to get the correct one:** LinkedIn Page → Analytics → Competitors → Export → download the .xlsx file.")
        st.caption("Optional — you can skip this.")
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("Back", use_container_width=True): st.session_state.step=5; st.rerun()
        with c2:
            if st.button("Skip", use_container_width=True): st.session_state.step=7; st.rerun()
        with c3:
            if st.button("Show my results →", type="primary", use_container_width=True): st.session_state.step=7; st.rerun()

# STEP 7 — DASHBOARD
elif step == 7:
    df_posts = st.session_state.df_posts
    df_stats = st.session_state.df_stats
    sector = st.session_state.sector
    bench = SECTORS[sector]
    bench_eng = bench["engagement"]
    fol_growth = st.session_state.fol_growth
    fol_sheets = st.session_state.fol_sheets
    vis_data = st.session_state.vis_data
    vis_sheets = st.session_state.vis_sheets
    df_comp = st.session_state.df_comp
    company = st.session_state.get("company","")

    if df_posts is None:
        st.warning("No data found — please start over.")
        if st.button("Start over"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
        st.stop()

    df_stats_m = df_stats.copy()
    df_stats_m["Month"] = df_stats_m["Datum"].dt.to_period("M").astype(str)
    monthly = df_stats_m.groupby("Month").agg(Views=("Weergaven_totaal","sum"),Clicks=("Klikken_totaal","sum"),Reactions=("Reacties_totaal","sum"),Engagement=("Engagement_totaal","mean")).reset_index()
    monthly["Engagement"] = (monthly["Engagement"] * 100).round(2)
    d1 = df_stats["Datum"].min().strftime("%b %Y")
    d2 = df_stats["Datum"].max().strftime("%b %Y")
    avg_eng = df_posts[df_posts["Engagement_pct"]>0]["Engagement_pct"].median()
    ppw = len(df_posts)/max((df_posts["Aangemaakt"].max()-df_posts["Aangemaakt"].min()).days/7,1)
    evb = avg_eng - bench_eng
    freq_ok = ppw >= float(bench["frequency"].split("x")[0].split("-")[0])
    best_day = df_posts.groupby("Day")["Engagement_pct"].mean().idxmax() if len(df_posts) else "—"

    st.markdown(f'<div class="welcome-msg">{"Here\'s your analysis for " + company + "." if company else "Here\'s your analysis."}</div>', unsafe_allow_html=True)
    st.markdown(f"**{d1} – {d2}** · {sector} · {len(df_posts)} posts analysed")
    st.markdown("---")

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.markdown(kpi("Median engagement",f"{avg_eng:.1f}%",f"{'Above' if evb>=0 else 'Below'} benchmark by {abs(evb):.1f}%",evb>=0,f"{bench_eng}% ({sector})"),unsafe_allow_html=True)
    with k2: st.markdown(kpi("Total views",f"{int(monthly['Views'].sum()):,}".replace(",","."),f"{d1} – {d2}"),unsafe_allow_html=True)
    with k3: st.markdown(kpi("Posts per week",f"{ppw:.1f}",f"{'On track' if freq_ok else 'Below'} — benchmark: {bench['frequency']}",freq_ok),unsafe_allow_html=True)
    with k4: st.markdown(kpi("Best day for engagement",best_day,"based on your post history"),unsafe_allow_html=True)
    st.markdown("---")

    tab_names = ["📊 Content","🧠 AI Strategy Check","📋 How did my posts do?","✏️ Is this ready to post?"]
    if fol_growth is not None: tab_names.append("👥 Followers")
    if vis_data is not None: tab_names.append("👁 Visitors")
    if df_comp is not None: tab_names.append("🏆 Competitors")
    tabs = st.tabs(tab_names)
    tm = {n:t for n,t in zip(tab_names,tabs)}

    with tm["📊 Content"]:
        st.markdown('<p class="section-head">Monthly results</p>', unsafe_allow_html=True)
        mc = st.radio("",["Views","Clicks","Reactions","Engagement %"],horizontal=True,label_visibility="collapsed")
        metric_col = "Engagement" if mc == "Engagement %" else mc
        is_pct = mc == "Engagement %"
        fig_m = go.Figure(go.Bar(x=monthly["Month"],y=monthly[metric_col],marker_color=DARK,opacity=.85,
            text=monthly[metric_col].apply(lambda v: f"{v:.1f}%" if is_pct else (f"{v/1000:.1f}k" if v>=1000 else str(v))),
            textposition="outside",textfont=dict(size=10)))
        fig_m.update_layout(**bl(height=280),xaxis=dict(tickangle=-45,showgrid=False),yaxis=dict(showgrid=True,gridcolor="#f5f0e8"),bargap=.35)
        st.plotly_chart(fig_m,use_container_width=True)
        ce,cr = st.columns(2)
        with ce:
            st.markdown('<p class="section-head">Engagement by day</p>', unsafe_allow_html=True)
            days = df_posts[df_posts["Day"].isin(DAG_EN)].groupby("Day").agg(G=("Engagement_pct","mean")).reset_index()
            ds = days.sort_values("G",ascending=True)
            fig_d = go.Figure(go.Bar(x=ds["G"].round(2),y=ds["Day"].map(DAG_EN),orientation="h",marker_color=RED,text=ds["G"].apply(lambda v:f"{v:.2f}%"),textposition="outside"))
            fig_d.update_layout(**bl(height=220),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
            fig_d.add_vline(x=bench_eng,line_dash="dot",line_color="rgba(0,0,0,0.2)",annotation_text=f"  benchmark {bench_eng}%",annotation_font_size=11)
            st.plotly_chart(fig_d,use_container_width=True)
        with cr:
            st.markdown('<p class="section-head">Reach by day</p>', unsafe_allow_html=True)
            dr = df_posts[df_posts["Day"].isin(DAG_EN)].groupby("Day").agg(G=("Weergaven","mean")).reset_index().sort_values("G",ascending=True)
            fig_r = go.Figure(go.Bar(x=dr["G"].round(0),y=dr["Day"].map(DAG_EN),orientation="h",marker_color=BLUE,text=dr["G"].apply(lambda v:f"{int(v):,}".replace(",",".")),textposition="outside"))
            fig_r.update_layout(**bl(height=220),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
            st.plotly_chart(fig_r,use_container_width=True)
        st.markdown('<p class="section-head">Top posts</p>', unsafe_allow_html=True)
        t1,t2 = st.tabs(["Most views","Highest engagement"])
        with t1: post_table(df_posts.sort_values("Weergaven",ascending=False).head(10),bench_eng)
        with t2: post_table(df_posts[df_posts["Engagement_pct"]>0].sort_values("Engagement_pct",ascending=False).head(10),bench_eng)

    with tm["🧠 AI Strategy Check"]:
        st.markdown("#### What does your data actually mean?")
        st.markdown("A plain-English read on your LinkedIn performance — what's working, where the opportunities are, and one thing to try next.")
        api_key = st.secrets.get("ANTHROPIC_API_KEY",None)
        if not api_key: st.warning("AI diagnosis is not available right now.")
        else:
            if st.button("Generate my diagnosis", type="primary"):
                with st.spinner("Analysing your data..."):
                    try:
                        diag = ai_diag(df_posts,df_stats,sector,bench_eng,api_key)
                        st.session_state.diagnosis = diag
                    except Exception as e: st.error(f"Something went wrong: {e}")
        if "diagnosis" in st.session_state:
            import re
            raw = st.session_state.diagnosis
            # Clean up unwanted headers and hashtags
            raw = re.sub(r"#{1,6}\s*", "", raw)
            raw = re.sub(r"\*?\*?PART\s+\d+[^\n]*\*?\*?\n?", "", raw)
            raw = raw.strip()
            if "---ACTIONS---" in raw:
                diag_part, actions_part = raw.split("---ACTIONS---", 1)
                diag_clean = diag_part.strip()
                st.markdown('<p class="section-head">LinkedIn Performance Analysis</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-box">{diag_clean}</div>', unsafe_allow_html=True)
                st.markdown('<p class="section-head">5 ways to improve your LinkedIn</p>', unsafe_allow_html=True)
                actions_html = ""
                for line in actions_part.strip().split("\n"):
                    line = line.strip()
                    if not line: continue
                    line = re.sub(r"#{1,6}\s*", "", line)
                    # Remove asterisks used for bold
                    line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                    line = re.sub(r"\*(.+?)\*", r"\1", line)
                    if line and line[0].isdigit():
                        # Split number+title from description
                        if ":" in line:
                            title_part, desc_part = line.split(":", 1)
                            formatted = f'<strong>{title_part}:</strong>{desc_part}'
                        else:
                            formatted = line
                        actions_html += f'<div style="background:white;border:1.5px solid #e8e2d8;border-radius:12px;padding:0.9rem 1.25rem;margin-bottom:0.6rem;font-size:14px;line-height:1.7;color:#0D1B2A;">{formatted}</div>'
                if actions_html:
                    st.markdown(actions_html, unsafe_allow_html=True)
            else:
                clean = re.sub(r"#{1,6}\s*", "", raw)
                st.markdown('<p class="section-head">LinkedIn Performance Analysis</p>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-box">{clean}</div>', unsafe_allow_html=True)

    with tm["📋 How did my posts do?"]:
        st.markdown("#### Post Review")
        st.markdown("We'll review your 10 most recent posts and give you specific, actionable feedback on each one.")
        api_key2 = st.secrets.get("ANTHROPIC_API_KEY",None)
        recent = df_posts[df_posts["Weergaven"]>0].sort_values("Aangemaakt",ascending=False).head(10)
        st.markdown('<p class="section-head">Posts to be reviewed</p>', unsafe_allow_html=True)
        prev = recent[["Aangemaakt","Title_short","Weergaven"]].copy()
        prev["Aangemaakt"] = prev["Aangemaakt"].dt.strftime("%Y-%m-%d")
        prev["Weergaven"] = prev["Weergaven"].apply(lambda v: f"{v:,}".replace(",","."))
        prev.columns = ["Date","Post","Views"]
        st.dataframe(prev,use_container_width=True,hide_index=True)
        if api_key2:
            if st.button("Review my posts →", type="primary"):
                top = df_posts.nlargest(3,"Engagement_pct")[["Title_short","Engagement_pct"]].to_dict("records")
                pt = "\n---\n".join(recent["Titel"].fillna("").str[:800].tolist())
                with st.spinner("Reviewing your posts..."):
                    try:
                        result = ai_audit(pt,str(top),sector,api_key2)
                        st.session_state.audit = result
                    except Exception as e: st.error(f"Something went wrong: {e}")
        if "audit" in st.session_state:
            raw_audit = st.session_state.audit
            lines = raw_audit.strip().split("\n")
            post_groups = []
            current_post = []
            summary_lines = []
            in_summary = False

            for line in lines:
                line = line.strip()
                if not line: continue
                if line.startswith("WHAT'S WORKING") or line.startswith("TOP OPPORTUNITY") or line.startswith("WHAT") or line.startswith("PATTERN"):
                    in_summary = True
                    if current_post:
                        post_groups.append(current_post)
                        current_post = []
                if in_summary:
                    summary_lines.append(line)
                elif line.startswith("POST "):
                    if current_post:
                        post_groups.append(current_post)
                    current_post = [line]
                else:
                    if current_post:
                        current_post.append(line)
            if current_post:
                post_groups.append(current_post)

            for group in post_groups:
                header = group[0]
                body = " ".join(group[1:]) if len(group) > 1 else ""
                st.markdown(f'''<div style="background:white;border:1.5px solid #e8e2d8;border-radius:14px;padding:1.25rem;margin-bottom:0.75rem;">
                <div style="background:#EAF4FB;border-radius:8px;padding:0.6rem 1rem;font-weight:600;font-size:13px;color:#0D1B2A;margin-bottom:0.6rem;">{header}</div>
                <div style="font-size:14px;line-height:1.7;color:#333;">{body}</div>
                </div>''', unsafe_allow_html=True)

            if summary_lines:
                st.markdown('<p class="section-head">Patterns & opportunities</p>', unsafe_allow_html=True)
                import re as _re
                html = ""
                for line in summary_lines:
                    line = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
                    line = _re.sub(r"\*(.+?)\*", r"\1", line)
                    if ":" in line:
                        label, body = line.split(":", 1)
                        html += f'<div style="display:flex;gap:10px;margin-bottom:10px;align-items:flex-start;"><span style="color:#FB8500;font-weight:700;min-width:8px;">›</span><div><strong>{label.strip()}:</strong>{body}</div></div>'
                    else:
                        html += f'<div style="display:flex;gap:10px;margin-bottom:10px;"><span style="color:#FB8500;font-weight:700;">›</span><span>{line}</span></div>'
                st.markdown(f'<div class="ai-box">{html}</div>', unsafe_allow_html=True)

    if "✏️ Is this ready to post?" in tm:
        with tm["✏️ Is this ready to post?"]:
            st.markdown("#### Is this ready to post?")
            st.markdown("Paste a draft LinkedIn post below and get specific feedback before you publish.")
            api_key3 = st.secrets.get("ANTHROPIC_API_KEY", None)
            draft_post = st.text_area("Paste your draft post here", height=200,
                placeholder="Write or paste your LinkedIn post here...")
            if api_key3:
                if st.button("Give me feedback →", type="primary", disabled=not draft_post):
                    if draft_post:
                        with st.spinner("Reviewing your draft..."):
                            try:
                                feedback = ai_draft_feedback(draft_post, sector, bench_eng, api_key3)
                                st.session_state.draft_feedback = feedback
                            except Exception as e:
                                st.error(f"Something went wrong: {e}")
            if "draft_feedback" in st.session_state:
                import re as _re
                fb = st.session_state.draft_feedback
                fb = _re.sub(r"\*\*(.+?)\*\*", r"<strong></strong>", fb)
                st.markdown(f'<div class="ai-box">{fb.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

    if "👥 Followers" in tm:
        with tm["👥 Followers"]:
            total_new = int(fol_growth["Totaal aantal volgers"].sum())
            current_fol = st.session_state.get("current_followers", 0)
            if current_fol > 0:
                start_count = max(0, current_fol - total_new)
                fol_growth["Cumulative"] = start_count + fol_growth["Totaal aantal volgers"].cumsum()
            else:
                fol_growth["Cumulative"] = fol_growth["Totaal aantal volgers"].cumsum()
            current_fol = st.session_state.get("current_followers", 0)
            if current_fol > 0:
                f1,f2,f3,f4 = st.columns(4)
            else:
                f1,f2,f3 = st.columns(3)
                f4 = None
            with f1: st.markdown(kpi("New followers (period)",f"{total_new:,}".replace(",",".")),unsafe_allow_html=True)
            with f2: st.markdown(kpi("Avg per day",f"{fol_growth['Totaal aantal volgers'].mean():.1f}"),unsafe_allow_html=True)
            with f3:
                peak = fol_growth.loc[fol_growth["Totaal aantal volgers"].idxmax()]
                st.markdown(kpi("Peak day",peak["Datum"].strftime("%d %b %Y"),delta=f"{int(peak['Totaal aantal volgers'])} new followers"),unsafe_allow_html=True)
            if f4 and current_fol > 0:
                with f4: st.markdown(kpi("Total followers now",f"{current_fol:,}".replace(",",".")),unsafe_allow_html=True)
            st.markdown('<p class="section-head">Follower growth</p>', unsafe_allow_html=True)
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=fol_growth["Datum"],y=fol_growth["Cumulative"],fill="tozeroy",line=dict(color=DARK,width=2),fillcolor="rgba(0,48,73,0.08)",name="Cumulative"))
            fig_f.add_trace(go.Bar(x=fol_growth["Datum"],y=fol_growth["Totaal aantal volgers"],marker_color=BLUE,opacity=.6,name="New per day",yaxis="y2"))
            fig_f.update_layout(**bl(height=300),yaxis=dict(showgrid=True,gridcolor="#f5f0e8"),yaxis2=dict(overlaying="y",side="right",showgrid=False),legend=dict(orientation="h",y=1.08))
            st.plotly_chart(fig_f,use_container_width=True)
            d1c,d2c = st.columns(2)
            with d1c:
                st.caption("Industry (top 10)")
                dfb = fol_sheets["Branche"].head(10).sort_values(fol_sheets["Branche"].columns[1],ascending=True)
                st.plotly_chart(hbar(dfb,dfb.columns[1],dfb.columns[0],DARK,300),use_container_width=True)
            with d2c:
                st.caption("Function (top 10)")
                dff = fol_sheets["Functie"].head(10).sort_values(fol_sheets["Functie"].columns[1],ascending=True)
                st.plotly_chart(hbar(dff,dff.columns[1],dff.columns[0],BLUE,300),use_container_width=True)

    if "👁 Visitors" in tm:
        with tm["👁 Visitors"]:
            vcols = [c for c in vis_data.columns if "totaal" in c.lower() and "uniek" not in c.lower() and "pagina" not in c.lower()]
            ucols = [c for c in vis_data.columns if "unieke bezoekers" in c.lower() and "totaal" in c.lower()]
            tc = vcols[0] if vcols else vis_data.columns[1]
            uc = ucols[0] if ucols else vis_data.columns[2]
            v1,v2 = st.columns(2)
            with v1: st.markdown(kpi("Total page views",f"{int(vis_data[tc].sum()):,}".replace(",",".")),unsafe_allow_html=True)
            with v2: st.markdown(kpi("Unique visitors",f"{int(vis_data[uc].sum()):,}".replace(",",".")),unsafe_allow_html=True)
            st.markdown('<p class="section-head">Visitor trend</p>', unsafe_allow_html=True)
            fig_v = go.Figure()
            fig_v.add_trace(go.Scatter(x=vis_data["Datum"],y=vis_data[tc],line=dict(color=DARK,width=2),name="Page views"))
            fig_v.add_trace(go.Scatter(x=vis_data["Datum"],y=vis_data[uc],line=dict(color=RED,width=2,dash="dot"),name="Unique visitors"))
            fig_v.update_layout(**bl(height=260),legend=dict(orientation="h",y=1.08))
            st.plotly_chart(fig_v,use_container_width=True)

    if "🏆 Competitors" in tm:
        with tm["🏆 Competitors"]:
            company_name = st.session_state.get("company","")
            for metric,label in [("Nieuwe_volgers","New followers"),("Bijdragen","Posts"),("Reacties","Reactions")]:
                ds2 = df_comp.sort_values(metric,ascending=True).copy()
                colors = []
                for p in ds2["Pagina"]:
                    p_str = str(p).lower().strip()
                    c_str = company_name.lower().strip() if company_name else ""
                    is_own = c_str and (c_str in p_str or p_str in c_str or p_str == c_str)
                    colors.append("#FB8500" if is_own else "#8ECAE6")
                fig = go.Figure(go.Bar(
                    x=ds2[metric], y=ds2["Pagina"],
                    orientation="h",
                    marker=dict(color=colors, line=dict(width=0)),
                    text=ds2[metric], textposition="outside", textfont=dict(size=12),
                ))
                fig.update_layout(**bl(height=max(200, len(ds2)*42)),
                    title=dict(text=label, font=dict(size=13, color=DARK)),
                    xaxis=dict(showgrid=False, visible=False),
                    yaxis=dict(showgrid=False), bargap=0.3)
                st.plotly_chart(fig, use_container_width=True)
            st.caption("Orange = your page · Blue = competitors")

    st.markdown(f"""<div class="cta-banner">
    <div class="cta-text"><strong>Rather brainstorm with a human?</strong>Connect with Bas Oudshoorn — LinkedIn strategist & Marketing Communications Manager at Leiden Bio Science Park.</div>
    <a href="{BAS_URL}" target="_blank" class="cta-btn">Connect on LinkedIn</a>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Start over with new data"):
        for k in ["df_posts","df_stats","fol_growth","fol_sheets","vis_data","vis_sheets","df_comp","diagnosis","audit"]:
            if k in st.session_state: del st.session_state[k]
        st.session_state.step = 1
        st.rerun()
