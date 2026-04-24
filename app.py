import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io, json
from anthropic import Anthropic

st.set_page_config(page_title="LinkedIn Analytics Analyzer", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

RED   = "#780000"
CREAM = "#FDF0D5"
DARK  = "#003049"
BLUE  = "#669BBC"
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
.stButton button[kind="primary"]:hover{{background:#5a0000!important;transform:translateY(-1px)!important;}}
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
.cta-btn{{background:{RED};color:white;border:none;padding:12px 28px;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap;text-decoration:none;font-family:'Sora',sans-serif;}}
.welcome-msg{{font-family:'Lora',serif;font-size:1.5rem;color:{DARK};margin-bottom:.5rem;font-style:italic;}}
.bench-card{{background:{CREAM};border:1.5px solid #e8d8b0;border-radius:14px;padding:1.25rem 1.5rem;margin-top:1rem;line-height:1.8;color:{DARK};font-size:14px;}}
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
    df = pd.read_excel(xl, sheet_name="COMPETITORS", header=1)
    df.columns = ["Pagina","Nieuwe_volgers","Bijdragen","Commentaren","Commentaren_per_dag","Reacties"]
    return df[df["Pagina"].notna()]

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
    prompt = f"""You are a warm, experienced LinkedIn content strategist.
Sector: {sector}, Benchmark: {bench_eng}%, Their median engagement: {avg:.1f}%, Posts/week: {ppw:.1f}, Best day: {bd}, Total posts: {len(df_posts)}
Top 3 posts: {json.dumps(top)}
Monthly views (last 6): {ma.tail(6).to_dict("records")}
Write a warm, encouraging strategic diagnosis in 3-4 short paragraphs. Start with what they do well. Use their actual numbers. Write like a helpful colleague. No bullets, no headers, max 200 words."""
    r = client.messages.create(model="claude-sonnet-4-5",max_tokens=600,messages=[{"role":"user","content":prompt}])
    return r.content[0].text

def ai_audit(posts_text,top_performers,sector,api_key):
    client = Anthropic(api_key=api_key)
    prompt = f"""You are a warm, encouraging LinkedIn content coach for a {sector} company.
TOP PERFORMING POSTS: {top_performers}
POSTS TO REVIEW: {posts_text}
For each post: "Post [N]: Hook [1-10] | Clarity [1-10] | CTA [1-10] | Overall [1-10] — [one warm constructive sentence]"
Then:
WHAT'S WORKING: [2-3 genuine strengths]
OPPORTUNITY: [one specific encouraging suggestion]
Be warm and coach-like. Plain text only."""
    r = client.messages.create(model="claude-sonnet-4-5",max_tokens=1500,messages=[{"role":"user","content":prompt}])
    return r.content[0].text

# Session state
for k,v in {"step":1,"email":"","name":"","company":"","sector":"Other","df_posts":None,"df_stats":None,"fol_growth":None,"fol_sheets":None,"vis_data":None,"vis_sheets":None,"df_comp":None}.items():
    if k not in st.session_state: st.session_state[k] = v

step = st.session_state.step

st.markdown("""<div class="hero"><h1>LinkedIn Analytics<br>Analyzer</h1><p>Upload your LinkedIn exports and get a data-driven picture of what's working — benchmarked against your sector, powered by AI.</p></div>""", unsafe_allow_html=True)

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
        st.markdown('<div class="hint-box">Your data stays in your browser session only — never stored on our servers.</div>', unsafe_allow_html=True)
        if st.button("Let's go →", type="primary", use_container_width=True):
            if not email or "@" not in email: st.error("Please enter a valid email address.")
            elif not name: st.error("Please enter your name.")
            else:
                st.session_state.update({"email":email,"name":name,"company":company,"step":2})
                st.rerun()

# STEP 2
elif step == 2:
    st.markdown(f'<div class="welcome-msg">Good to meet you, {st.session_state.name}.</div>', unsafe_allow_html=True)
    st.markdown("### What sector are you in?")
    col1,_ = st.columns([2,1])
    with col1:
        sector = st.selectbox("Your sector", list(SECTORS.keys()))
        bench = SECTORS[sector]
        st.markdown(f'<div class="bench-card"><strong>Benchmarks for {sector}</strong><br>Average engagement: <strong>{bench["engagement"]}%</strong><br>Posting frequency: <strong>{bench["frequency"]}</strong><br>Annual follower growth: <strong>{bench["follower_growth"]}%</strong></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Content → click <code>Export</code> top right. Download the <code>.xls</code> file. You can upload multiple to combine periods.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        content_files = st.file_uploader("Content export (.xls)", type=["xls"], accept_multiple_files=True)
        if content_files:
            with st.spinner("Loading your posts..."):
                ap,as_ = [],[]
                for f in content_files:
                    p,s = load_content(f.read()); ap.append(p); as_.append(s)
                df_posts = pd.concat(ap,ignore_index=True).drop_duplicates(subset=["Link"],keep="last").sort_values("Aangemaakt").reset_index(drop=True)
                df_stats = pd.concat(as_,ignore_index=True).drop_duplicates(subset=["Datum"],keep="last").sort_values("Datum").reset_index(drop=True)
                st.session_state.df_posts = df_posts; st.session_state.df_stats = df_stats
            st.success(f"Loaded {len(df_posts)} posts · {df_stats['Datum'].min().strftime('%b %Y')} – {df_stats['Datum'].max().strftime('%b %Y')}")
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
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Followers → <code>Export</code>.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        ff = st.file_uploader("Followers export (.xls)", type=["xls"])
        if ff:
            with st.spinner("Loading..."):
                g,s = load_followers(ff.read()); st.session_state.fol_growth=g; st.session_state.fol_sheets=s
            st.success(f"Loaded · {int(g['Totaal aantal volgers'].sum()):,} new followers in period".replace(",","."))
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
    st.markdown("See who's visiting your LinkedIn page — even people who haven't followed you yet.")
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Visitors → <code>Export</code>.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        vf = st.file_uploader("Visitors export (.xls)", type=["xls"])
        if vf:
            vd,vs = load_visitors(vf.read()); st.session_state.vis_data=vd; st.session_state.vis_sheets=vs
            st.success("Visitors data loaded")
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
    st.markdown('<div class="hint-box"><strong>How to export:</strong> LinkedIn Page → Analytics → Competitors → <code>Export</code>. This exports as <code>.xlsx</code>.</div>', unsafe_allow_html=True)
    col1,_ = st.columns([2,1])
    with col1:
        cf = st.file_uploader("Competitors export (.xlsx)", type=["xlsx"])
        if cf:
            dc = load_competitors(cf.read()); st.session_state.df_comp=dc
            st.success(f"Loaded · {len(dc)} companies")
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
    monthly = df_stats_m.groupby("Month").agg(Views=("Weergaven_totaal","sum"),Clicks=("Klikken_totaal","sum"),Reactions=("Reacties_totaal","sum")).reset_index()
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

    tab_names = ["Content","AI Diagnosis","Post Review"]
    if fol_growth is not None: tab_names.append("Followers")
    if vis_data is not None: tab_names.append("Visitors")
    if df_comp is not None: tab_names.append("Competitors")
    tabs = st.tabs(tab_names)
    tm = {n:t for n,t in zip(tab_names,tabs)}

    with tm["Content"]:
        st.markdown('<p class="section-head">Monthly reach</p>', unsafe_allow_html=True)
        mc = st.radio("",["Views","Clicks","Reactions"],horizontal=True,label_visibility="collapsed")
        fig_m = go.Figure(go.Bar(x=monthly["Month"],y=monthly[mc],marker_color=DARK,opacity=.85,text=monthly[mc].apply(lambda v:f"{v/1000:.1f}k" if v>=1000 else str(v)),textposition="outside",textfont=dict(size=10)))
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

    with tm["AI Diagnosis"]:
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
            st.markdown(f'<div class="ai-box">{st.session_state.diagnosis}</div>', unsafe_allow_html=True)

    with tm["Post Review"]:
        st.markdown("#### How are your recent posts landing?")
        st.markdown("We'll review your 10 most recent posts and share warm, specific feedback on each one.")
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
            st.markdown(f'<div class="ai-box">{st.session_state.audit.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

    if "Followers" in tm:
        with tm["Followers"]:
            fol_growth["Cumulative"] = fol_growth["Totaal aantal volgers"].cumsum()
            total_new = int(fol_growth["Totaal aantal volgers"].sum())
            f1,f2,f3 = st.columns(3)
            with f1: st.markdown(kpi("New followers",f"{total_new:,}".replace(",",".")),unsafe_allow_html=True)
            with f2: st.markdown(kpi("Avg per day",f"{fol_growth['Totaal aantal volgers'].mean():.1f}"),unsafe_allow_html=True)
            with f3:
                peak = fol_growth.loc[fol_growth["Totaal aantal volgers"].idxmax()]
                st.markdown(kpi("Peak day",peak["Datum"].strftime("%d %b %Y"),delta=f"{int(peak['Totaal aantal volgers'])} new followers"),unsafe_allow_html=True)
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

    if "Visitors" in tm:
        with tm["Visitors"]:
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

    if "Competitors" in tm:
        with tm["Competitors"]:
            for metric,label in [("Nieuwe_volgers","New followers"),("Bijdragen","Posts"),("Reacties","Reactions")]:
                ds2 = df_comp.sort_values(metric,ascending=True)
                fig = go.Figure(go.Bar(x=ds2[metric],y=ds2["Pagina"],orientation="h",marker_color=DARK,text=ds2[metric],textposition="outside"))
                fig.update_layout(**bl(height=200),title=dict(text=label,font=dict(size=13)),xaxis=dict(showgrid=False,visible=False),yaxis=dict(showgrid=False))
                st.plotly_chart(fig,use_container_width=True)

    st.markdown(f"""<div class="cta-banner">
    <div class="cta-text"><strong>Rather brainstorm with a human?</strong>Connect with Bas Oudshoorn — LinkedIn strategist & marketing communications manager at Leiden Bio Science Park.</div>
    <a href="{BAS_URL}" target="_blank" class="cta-btn">Connect on LinkedIn</a>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Start over with new data"):
        for k in ["df_posts","df_stats","fol_growth","fol_sheets","vis_data","vis_sheets","df_comp","diagnosis","audit"]:
            if k in st.session_state: del st.session_state[k]
        st.session_state.step = 1
        st.rerun()
