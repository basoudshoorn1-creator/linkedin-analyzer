import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io, json, os, re
from anthropic import Anthropic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Analytics Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Brand & Benchmarks ────────────────────────────────────────────────────────
ACCENT   = "#0A66C2"  # LinkedIn blue
ORANGE   = "#E87722"
GREEN    = "#057642"
GRAY     = "#666666"
BAS_URL  = "https://www.linkedin.com/in/bas-oudshoorn/"

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

DAG_EN = {
    "Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed",
    "Thursday": "Thu", "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun",
}

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
}}

/* Hide default streamlit elements */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 2rem; max-width: 1200px; }}

/* Hero */
.hero {{
    background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
    border-radius: 16px;
    padding: 3rem 3rem 2.5rem;
    margin-bottom: 2rem;
    color: white;
    position: relative;
    overflow: hidden;
}}
.hero::before {{
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}}
.hero h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    font-weight: 400;
    margin: 0 0 0.5rem;
    line-height: 1.15;
}}
.hero p {{
    font-size: 1.1rem;
    opacity: 0.85;
    margin: 0;
    max-width: 600px;
}}

/* Step cards */
.step-card {{
    background: white;
    border: 1.5px solid #e8e8e8;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}}
.step-card.active {{
    border-color: {ACCENT};
    box-shadow: 0 0 0 3px rgba(10,102,194,0.08);
}}
.step-card.done {{
    border-color: {GREEN};
    background: #f6fbf8;
}}
.step-number {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: {ACCENT};
    color: white;
    font-size: 13px;
    font-weight: 600;
    margin-right: 10px;
}}
.step-number.done {{
    background: {GREEN};
}}

/* Progress bar */
.progress-wrap {{
    display: flex;
    gap: 8px;
    margin-bottom: 2rem;
    align-items: center;
}}
.progress-step {{
    height: 4px;
    flex: 1;
    border-radius: 2px;
    background: #e0e0e0;
    transition: background 0.3s;
}}
.progress-step.done {{ background: {GREEN}; }}
.progress-step.active {{ background: {ACCENT}; }}

/* KPI cards */
.kpi-card {{
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
}}
.kpi-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {GRAY};
    margin-bottom: 6px;
}}
.kpi-value {{
    font-size: 2rem;
    font-weight: 600;
    color: #1a1a1a;
    line-height: 1;
}}
.kpi-delta {{
    font-size: 12px;
    margin-top: 4px;
}}
.kpi-delta.pos {{ color: {GREEN}; }}
.kpi-delta.neg {{ color: #cc1016; }}
.kpi-delta.neu {{ color: {GRAY}; }}
.kpi-benchmark {{
    font-size: 11px;
    color: {GRAY};
    margin-top: 3px;
}}

/* Section headers */
.section-head {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {GRAY};
    margin: 2rem 0 0.75rem;
}}

/* AI insight box */
.ai-box {{
    background: linear-gradient(135deg, #f0f7ff 0%, #e8f3ff 100%);
    border: 1px solid #b8d9f8;
    border-left: 4px solid {ACCENT};
    border-radius: 0 12px 12px 0;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
    font-size: 15px;
    line-height: 1.7;
    color: #1a1a1a;
}}

/* CTA banner */
.cta-banner {{
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 3rem;
}}
.cta-text {{ font-size: 15px; color: #333; }}
.cta-text strong {{ color: #1a1a1a; }}

/* Upload hint */
.upload-hint {{
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 13px;
    color: {GRAY};
    margin-top: 0.5rem;
}}
.upload-hint code {{
    background: #e8e8e8;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 12px;
}}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 2px solid #e8e8e8;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 13px;
    font-weight: 500;
    padding: 8px 16px;
    border-radius: 6px 6px 0 0;
}}
</style>
""", unsafe_allow_html=True)


# ── Loaders ───────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_content(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df_posts = pd.read_excel(xl, sheet_name="Alle bijdragen", header=1, skiprows=[0])
    df_posts.columns = ["Titel","Link","Soort","Campagne","Geplaatst_door","Aangemaakt",
                        "Campagne_start","Campagne_eind","Doelgroep","Weergaven","Weergaven2",
                        "Weergaven_buiten","Klikken","CTR","Interessant","Commentaren",
                        "Reposts","Gevolgd","Engagement_pct","Type_content"]
    df_posts = df_posts[df_posts["Aangemaakt"].notna()].copy()
    df_posts["Aangemaakt"] = pd.to_datetime(df_posts["Aangemaakt"], errors="coerce")
    df_posts = df_posts[df_posts["Aangemaakt"].notna()]
    df_posts["Type_content"] = df_posts["Type_content"].fillna("Text/Image")
    df_posts["Day"] = df_posts["Aangemaakt"].dt.day_name()
    df_posts["Month"] = df_posts["Aangemaakt"].dt.to_period("M").astype(str)
    df_posts["Title_short"] = df_posts["Titel"].str.replace("\xa0"," ").str.replace("\n"," ").str.strip().str[:80]
    for col in ["Weergaven","Klikken","Interessant","Commentaren","Reposts"]:
        df_posts[col] = pd.to_numeric(df_posts[col], errors="coerce").fillna(0).astype(int)
    df_posts["Engagement_pct"] = pd.to_numeric(df_posts["Engagement_pct"], errors="coerce").fillna(0) * 100
    df_stats = pd.read_excel(xl, sheet_name="Statistieken", header=1, skiprows=[0])
    df_stats.columns = ["Datum","Weergaven_spontaan","Weergaven_gesponsord","Weergaven_totaal",
                        "Unieke_weergaven","Klikken_spontaan","Klikken_gesponsord","Klikken_totaal",
                        "Reacties_spontaan","Reacties_gesponsord","Reacties_totaal",
                        "Comments_spontaan","Comments_gesponsord","Comments_totaal",
                        "Reposts_spontaan","Reposts_gesponsord","Reposts_totaal",
                        "Engagement_spontaan","Engagement_gesponsord","Engagement_totaal"]
    df_stats["Datum"] = pd.to_datetime(df_stats["Datum"], errors="coerce")
    df_stats = df_stats[df_stats["Datum"].notna()]
    return df_posts, df_stats

@st.cache_data(show_spinner=False)
def load_followers(file_bytes):
    xl = pd.ExcelFile(io.BytesIO(file_bytes), engine="xlrd")
    df_growth = pd.read_excel(xl, sheet_name="Nieuwe volgers")
    df_growth["Datum"] = pd.to_datetime(df_growth["Datum"])
    sheets = {s: pd.read_excel(xl, sheet_name=s) for s in ["Locatie","Functie","Senioriteitsniveau","Branche","Bedrijfsgrootte"]}
    return df_growth, sheets

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

def base_layout(**kw):
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans, sans-serif", size=12, color="#555"),
                margin=dict(l=0, r=0, t=24, b=0), **kw)

def benchmark_line(fig, benchmark, label="Sector benchmark", axis="y"):
    fig.add_hline(y=benchmark, line_dash="dot", line_color="rgba(0,0,0,0.25)",
                  annotation_text=f"  {label}: {benchmark}%",
                  annotation_position="right", annotation_font_size=11)
    return fig

def kpi_card(label, value, delta=None, benchmark=None, delta_positive=True):
    delta_html = ""
    if delta:
        cls = "pos" if delta_positive else "neg"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    bench_html = ""
    if benchmark:
        bench_html = f'<div class="kpi-benchmark">Benchmark: {benchmark}</div>'
    return f"""<div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
    {delta_html}{bench_html}
    </div>"""

def horiz_bar(df, x_col, y_col, color, height=220):
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col], orientation="h",
        marker_color=color,
        text=df[x_col].apply(lambda v: f"{v:,.0f}".replace(",",".")),
        textposition="outside",
    ))
    fig.update_layout(**base_layout(height=height),
                      xaxis=dict(showgrid=False, visible=False),
                      yaxis=dict(showgrid=False))
    return fig

def post_table(df, sector_benchmark):
    d = df[["Title_short","Aangemaakt","Day","Weergaven","Interessant","Commentaren","Engagement_pct"]].copy()
    d["Aangemaakt"] = d["Aangemaakt"].dt.strftime("%Y-%m-%d")
    d["Day"] = d["Day"].map(DAG_EN)
    d["vs benchmark"] = d["Engagement_pct"].apply(
        lambda v: f"✅ +{v-sector_benchmark:.1f}%" if v >= sector_benchmark else f"🔴 {v-sector_benchmark:.1f}%"
    )
    d["Engagement_pct"] = d["Engagement_pct"].round(1).astype(str) + "%"
    d.columns = ["Post","Date","Day","Views","Likes","Comments","Engagement","vs benchmark"]
    d["Views"] = d["Views"].apply(lambda v: f"{v:,}".replace(",","."))
    st.dataframe(d, use_container_width=True, hide_index=True)


# ── AI Functions ──────────────────────────────────────────────────────────────
def ai_diagnosis(df_posts, df_stats, sector, benchmark_eng, api_key):
    client = Anthropic(api_key=api_key)
    monthly = df_stats.copy()
    monthly["Month"] = monthly["Datum"].dt.to_period("M").astype(str)
    monthly_agg = monthly.groupby("Month").agg(Views=("Weergaven_totaal","sum")).reset_index()
    top_posts = df_posts.nlargest(3, "Weergaven")[["Title_short","Engagement_pct","Weergaven"]].to_dict("records")
    avg_eng = df_posts[df_posts["Engagement_pct"]>0]["Engagement_pct"].median()
    posts_per_week = len(df_posts) / max((df_posts["Aangemaakt"].max() - df_posts["Aangemaakt"].min()).days / 7, 1)
    best_day = df_posts.groupby("Day")["Engagement_pct"].mean().idxmax() if len(df_posts) > 0 else "unknown"

    prompt = f"""You are a LinkedIn content strategist analyzing a company's LinkedIn performance data.

Sector: {sector}
Sector engagement benchmark: {benchmark_eng}%
Their median engagement rate: {avg_eng:.1f}%
Average posts per week: {posts_per_week:.1f}
Best performing day: {best_day}
Total posts analyzed: {len(df_posts)}
Top 3 posts by views: {json.dumps(top_posts, indent=2)}
Monthly views trend (last 6 months): {monthly_agg.tail(6).to_dict("records")}

Write a concise, direct strategic diagnosis in 3-4 short paragraphs:
1. How they compare to their sector benchmark and what that means
2. What their data reveals about what's working (and what isn't)
3. The single most important thing they should do differently tomorrow

Be specific, use their actual numbers, and write like a consultant — not a chatbot. No bullet points. No headers. Plain paragraphs. Maximum 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def ai_content_audit(posts_text, top_performers, sector, api_key):
    client = Anthropic(api_key=api_key)
    prompt = f"""You are a LinkedIn content strategist. Audit these LinkedIn posts for a {sector} company.

TOP PERFORMING POSTS (for reference — these worked well):
{top_performers}

POSTS TO AUDIT:
{posts_text}

For each post give ONE line: "Post [N]: Hook [1-10] | Clarity [1-10] | CTA [1-10] | Overall [1-10] — [one sentence of feedback]"

Then write:
PATTERNS: [3 bullet points about what you see across all posts]
TOP RECOMMENDATION: [one specific actionable thing they should change immediately]

Be constructive, warm, and coach-like — you want them to improve, not feel bad. Use encouraging language while still being specific and honest. Plain text only, no JSON, no markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "step" not in st.session_state:
    st.session_state.step = 1
if "email" not in st.session_state:
    st.session_state.email = ""
if "sector" not in st.session_state:
    st.session_state.sector = "Other"
if "df_posts" not in st.session_state:
    st.session_state.df_posts = None
if "df_stats" not in st.session_state:
    st.session_state.df_stats = None
if "fol_growth" not in st.session_state:
    st.session_state.fol_growth = None
if "fol_sheets" not in st.session_state:
    st.session_state.fol_sheets = None
if "vis_data" not in st.session_state:
    st.session_state.vis_data = None
if "vis_sheets" not in st.session_state:
    st.session_state.vis_sheets = None
if "df_comp" not in st.session_state:
    st.session_state.df_comp = None

step = st.session_state.step

# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""<div class="hero">
<h1>LinkedIn Analytics<br>Analyzer</h1>
<p>Upload your LinkedIn exports and get an instant data-driven diagnosis of your content strategy — benchmarked against your sector.</p>
</div>""", unsafe_allow_html=True)

# Progress bar
steps_done = step - 1
progress_html = '<div class="progress-wrap">'
labels = ["You", "Sector", "Content", "Followers", "Visitors", "Results"]
for i, lbl in enumerate(labels):
    cls = "done" if i < steps_done else ("active" if i == steps_done else "")
    progress_html += f'<div class="progress-step {cls}" title="{lbl}"></div>'
progress_html += "</div>"
st.markdown(progress_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Email + name
# ══════════════════════════════════════════════════════════════════════════════
if step == 1:
    st.markdown("### Step 1 of 5 — Tell us who you are")
    col1, col2 = st.columns([2,1])
    with col1:
        name = st.text_input("Your name", placeholder="Jane Smith")
        email = st.text_input("Work email", placeholder="jane@company.com")
        company = st.text_input("Company name", placeholder="Acme Corp")
        st.markdown('<div class="upload-hint">Your data stays in your browser session and is never stored on our servers.</div>', unsafe_allow_html=True)

        if st.button("Continue →", type="primary", use_container_width=True):
            if not email or "@" not in email:
                st.error("Please enter a valid email address.")
            elif not name:
                st.error("Please enter your name.")
            else:
                st.session_state.email = email
                st.session_state.name = name
                st.session_state.company = company
                st.session_state.step = 2
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Sector
# ══════════════════════════════════════════════════════════════════════════════
elif step == 2:
    st.markdown("### Step 2 of 5 — Select your sector")
    st.markdown("We'll benchmark your performance against companies in your industry.")

    col1, col2 = st.columns([2,1])
    with col1:
        sector = st.selectbox("Your sector", list(SECTORS.keys()), index=list(SECTORS.keys()).index("Other"))
        bench = SECTORS[sector]

        st.markdown(f"""<div class="ai-box">
        <strong>Sector benchmark for {sector}:</strong><br>
        📊 Avg engagement rate: <strong>{bench['engagement']}%</strong><br>
        📅 Recommended posting frequency: <strong>{bench['frequency']}</strong><br>
        📈 Typical annual follower growth: <strong>{bench['follower_growth']}%</strong>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with c2:
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.sector = sector
                st.session_state.step = 3
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Content export
# ══════════════════════════════════════════════════════════════════════════════
elif step == 3:
    st.markdown("### Step 3 of 5 — Upload your Content export")
    st.markdown("This is the most important file — it contains all your post performance data.")

    st.markdown("""<div class="upload-hint">
    How to export: Go to your <strong>LinkedIn Page</strong> → <strong>Analytics</strong> → <strong>Content</strong> → click <code>Export</code> in the top right. Download the <code>.xls</code> file.
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        content_files = st.file_uploader(
            "Content export (.xls) — you can upload multiple files to combine periods",
            type=["xls"], accept_multiple_files=True
        )

        if content_files:
            with st.spinner("Loading your data..."):
                all_posts, all_stats = [], []
                for f in content_files:
                    p, s = load_content(f.read())
                    all_posts.append(p); all_stats.append(s)
                df_posts = pd.concat(all_posts, ignore_index=True).drop_duplicates(subset=["Link"], keep="last").sort_values("Aangemaakt").reset_index(drop=True)
                df_stats = pd.concat(all_stats, ignore_index=True).drop_duplicates(subset=["Datum"], keep="last").sort_values("Datum").reset_index(drop=True)
                st.session_state.df_posts = df_posts
                st.session_state.df_stats = df_stats

            date_from = df_stats["Datum"].min().strftime("%b %Y")
            date_to = df_stats["Datum"].max().strftime("%b %Y")
            st.success(f"✅ Loaded {len(df_posts)} posts · {date_from} – {date_to}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with c2:
            if st.button("Continue →", type="primary", use_container_width=True, disabled=not content_files):
                st.session_state.step = 4
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Followers export
# ══════════════════════════════════════════════════════════════════════════════
elif step == 4:
    st.markdown("### Step 4 of 5 — Upload your Followers export")
    st.markdown("This shows who follows you and how your audience is growing.")

    st.markdown("""<div class="upload-hint">
    How to export: Go to your <strong>LinkedIn Page</strong> → <strong>Analytics</strong> → <strong>Followers</strong> → click <code>Export</code>. Download the <code>.xls</code> file.
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        followers_file = st.file_uploader("Followers export (.xls)", type=["xls"])

        if followers_file:
            with st.spinner("Loading..."):
                fol_growth, fol_sheets = load_followers(followers_file.read())
                st.session_state.fol_growth = fol_growth
                st.session_state.fol_sheets = fol_sheets
            st.success(f"✅ Loaded follower data · {int(fol_growth['Totaal aantal volgers'].sum()):,} new followers in period".replace(",","."))

        st.markdown("*This file is optional — you can skip it and still get content insights.*")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with c2:
            if st.button("Skip →", use_container_width=True):
                st.session_state.step = 5
                st.rerun()
        with c3:
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.step = 5
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Visitors + Competitors
# ══════════════════════════════════════════════════════════════════════════════
elif step == 5:
    st.markdown("### Step 5 of 5 — Optional: Visitors & Competitors")

    st.markdown("""<div class="upload-hint">
    <strong>Visitors:</strong> LinkedIn Page → Analytics → Visitors → Export<br>
    <strong>Competitors:</strong> LinkedIn Page → Analytics → Competitors → Export
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        visitors_file = st.file_uploader("Visitors export (.xls) — optional", type=["xls"])
        competitor_file = st.file_uploader("Competitors export (.xlsx) — optional", type=["xlsx"])

        if visitors_file:
            vis_data, vis_sheets = load_visitors(visitors_file.read())
            st.session_state.vis_data = vis_data
            st.session_state.vis_sheets = vis_sheets
            st.success("✅ Visitors loaded")

        if competitor_file:
            df_comp = load_competitors(competitor_file.read())
            st.session_state.df_comp = df_comp
            st.success(f"✅ Competitor data loaded · {len(df_comp)} companies")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 4
                st.rerun()
        with c2:
            if st.button("Skip →", use_container_width=True):
                st.session_state.step = 6
                st.rerun()
        with c3:
            if st.button("View my results →", type="primary", use_container_width=True):
                st.session_state.step = 6
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif step == 6:
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

    if df_posts is None:
        st.warning("No data found. Please start over.")
        if st.button("Start over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.stop()

    # Monthly agg
    df_stats_m = df_stats.copy()
    df_stats_m["Month"] = df_stats_m["Datum"].dt.to_period("M").astype(str)
    monthly = df_stats_m.groupby("Month").agg(
        Views=("Weergaven_totaal","sum"), Clicks=("Klikken_totaal","sum"),
        Reactions=("Reacties_totaal","sum"),
    ).reset_index()

    date_from = df_stats["Datum"].min().strftime("%b %Y")
    date_to = df_stats["Datum"].max().strftime("%b %Y")
    avg_eng = df_posts[df_posts["Engagement_pct"]>0]["Engagement_pct"].median()
    posts_per_week = len(df_posts) / max((df_posts["Aangemaakt"].max() - df_posts["Aangemaakt"].min()).days / 7, 1)
    eng_vs_bench = avg_eng - bench_eng
    freq_ok = posts_per_week >= float(bench["frequency"].split("x")[0].split("-")[0])

    name = st.session_state.get("name", "")
    company = st.session_state.get("company", "")

    st.markdown(f"#### Results for {company if company else 'your page'} · {date_from} – {date_to} · Sector: {sector}")

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        delta_eng = f"{'↑' if eng_vs_bench >= 0 else '↓'} {abs(eng_vs_bench):.1f}% vs benchmark"
        st.markdown(kpi_card("Median engagement rate", f"{avg_eng:.1f}%",
                    delta=delta_eng, delta_positive=eng_vs_bench>=0,
                    benchmark=f"{bench_eng}% ({sector})"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Total views", f"{int(monthly['Views'].sum()):,}".replace(",","."),
                    delta=f"{date_from} – {date_to}"), unsafe_allow_html=True)
    with k3:
        freq_delta = f"{'✅' if freq_ok else '⚠️'} Benchmark: {bench['frequency']}"
        st.markdown(kpi_card("Posts per week", f"{posts_per_week:.1f}",
                    delta=freq_delta, delta_positive=freq_ok), unsafe_allow_html=True)
    with k4:
        best_day = df_posts.groupby("Day")["Engagement_pct"].mean().idxmax()
        st.markdown(kpi_card("Best day for engagement", best_day,
                    delta="based on your data"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_names = ["📊 Content", "🤖 AI Diagnosis", "✍️ Content Audit"]
    if fol_growth is not None: tab_names.append("👥 Followers")
    if vis_data is not None: tab_names.append("👁 Visitors")
    if df_comp is not None: tab_names.append("🏆 Competitors")

    tabs = st.tabs(tab_names)
    tm = {n: t for n, t in zip(tab_names, tabs)}

    # ── CONTENT TAB ───────────────────────────────────────────────────────────
    with tm["📊 Content"]:
        st.markdown('<p class="section-head">Monthly reach</p>', unsafe_allow_html=True)
        mc = st.radio("Metric", ["Views","Clicks","Reactions"], horizontal=True, label_visibility="collapsed")
        metric_map = {"Views":"Views","Clicks":"Clicks","Reactions":"Reactions"}
        fig_m = go.Figure(go.Bar(
            x=monthly["Month"], y=monthly[metric_map[mc]],
            marker_color=ACCENT, opacity=0.85,
            text=monthly[metric_map[mc]].apply(lambda v: f"{v/1000:.1f}k" if v>=1000 else str(v)),
            textposition="outside", textfont=dict(size=10),
        ))
        fig_m.update_layout(**base_layout(height=280),
                            xaxis=dict(tickangle=-45, showgrid=False),
                            yaxis=dict(showgrid=True, gridcolor="#f0f0f0"), bargap=0.35)
        st.plotly_chart(fig_m, use_container_width=True)

        col_e, col_r = st.columns(2)
        with col_e:
            st.markdown('<p class="section-head">Engagement by day</p>', unsafe_allow_html=True)
            days = df_posts[df_posts["Day"].isin(DAG_EN)].groupby("Day").agg(
                Gem_engagement=("Engagement_pct","mean")).reset_index()
            days_s = days.sort_values("Gem_engagement", ascending=True)
            fig_d = go.Figure(go.Bar(
                x=days_s["Gem_engagement"].round(2),
                y=days_s["Day"].map(DAG_EN),
                orientation="h", marker_color=ACCENT,
                text=days_s["Gem_engagement"].apply(lambda v: f"{v:.2f}%"),
                textposition="outside",
            ))
            fig_d.update_layout(**base_layout(height=220),
                                xaxis=dict(showgrid=False, visible=False),
                                yaxis=dict(showgrid=False))
            benchmark_line(fig_d, bench_eng)
            st.plotly_chart(fig_d, use_container_width=True)

        with col_r:
            st.markdown('<p class="section-head">Reach by day</p>', unsafe_allow_html=True)
            days_r = df_posts[df_posts["Day"].isin(DAG_EN)].groupby("Day").agg(
                Gem_weergaven=("Weergaven","mean")).reset_index()
            days_rs = days_r.sort_values("Gem_weergaven", ascending=True)
            fig_r = go.Figure(go.Bar(
                x=days_rs["Gem_weergaven"].round(0),
                y=days_rs["Day"].map(DAG_EN),
                orientation="h", marker_color=ORANGE,
                text=days_rs["Gem_weergaven"].apply(lambda v: f"{int(v):,}".replace(",",".")),
                textposition="outside",
            ))
            fig_r.update_layout(**base_layout(height=220),
                                xaxis=dict(showgrid=False, visible=False),
                                yaxis=dict(showgrid=False))
            st.plotly_chart(fig_r, use_container_width=True)

        st.markdown('<p class="section-head">Top posts</p>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["Most views", "Highest engagement"])
        with t1: post_table(df_posts.sort_values("Weergaven", ascending=False).head(10), bench_eng)
        with t2: post_table(df_posts[df_posts["Engagement_pct"]>0].sort_values("Engagement_pct", ascending=False).head(10), bench_eng)

        st.markdown('<p class="section-head">Views vs engagement</p>', unsafe_allow_html=True)
        sc = df_posts[df_posts["Weergaven"]>0].copy()
        fig_sc = px.scatter(sc, x="Weergaven", y="Engagement_pct",
            hover_data={"Title_short":True,"Aangemaakt":True,"Engagement_pct":":.1f"},
            labels={"Weergaven":"Views","Engagement_pct":"Engagement %"},
            color_discrete_sequence=[ACCENT])
        fig_sc.update_traces(marker=dict(size=8, opacity=0.6))
        fig_sc.add_hline(y=bench_eng, line_dash="dot", line_color="rgba(0,0,0,0.3)",
                         annotation_text=f"  Benchmark: {bench_eng}%", annotation_font_size=11)
        fig_sc.update_layout(**base_layout(height=300), legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── AI DIAGNOSIS TAB ──────────────────────────────────────────────────────
    with tm["🤖 AI Diagnosis"]:
        st.markdown("#### AI-powered strategic diagnosis")
        st.markdown("Get a plain-English analysis of your LinkedIn performance — what's working, what isn't, and what to do next.")

        api_key = st.secrets.get("ANTHROPIC_API_KEY", None)
        if not api_key:
            st.warning("AI diagnosis is not configured. Contact the administrator.")
        else:
            if st.button("Generate diagnosis", type="primary"):
                with st.spinner("Analyzing your data..."):
                    try:
                        diagnosis = ai_diagnosis(df_posts, df_stats, sector, bench_eng, api_key)
                        st.session_state.diagnosis = diagnosis
                    except Exception as e:
                        st.error(f"Error: {e}")

        if "diagnosis" in st.session_state:
            st.markdown(f'<div class="ai-box">{st.session_state.diagnosis}</div>', unsafe_allow_html=True)

    # ── CONTENT AUDIT TAB ─────────────────────────────────────────────────────
    with tm["✍️ Content Audit"]:
        st.markdown("#### Content audit")
        st.markdown("We'll automatically audit your 10 most recent posts and score each one on hook strength, clarity, relevance, and call to action.")

        api_key_audit = st.secrets.get("ANTHROPIC_API_KEY", None)

        # Show the 10 most recent posts
        recent_posts = df_posts[df_posts["Weergaven"] > 0].sort_values("Aangemaakt", ascending=False).head(10)
        st.markdown('<p class="section-head">Posts to be audited</p>', unsafe_allow_html=True)
        preview = recent_posts[["Aangemaakt","Title_short","Weergaven"]].copy()
        preview["Aangemaakt"] = preview["Aangemaakt"].dt.strftime("%Y-%m-%d")
        preview["Weergaven"] = preview["Weergaven"].apply(lambda v: f"{v:,}".replace(",","."))
        preview.columns = ["Date","Post","Views"]
        st.dataframe(preview, use_container_width=True, hide_index=True)

        if api_key_audit:
            if st.button("Audit these 10 posts →", type="primary"):
                top_performers = df_posts.nlargest(3, "Engagement_pct")[["Title_short","Engagement_pct"]].to_dict("records")
                posts_text = "\n---\n".join(recent_posts["Titel"].fillna("").str[:800].tolist())
                with st.spinner("Auditing your content..."):
                    try:
                        result = ai_content_audit(posts_text, str(top_performers), sector, api_key_audit)
                        st.session_state.audit = result
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("AI audit is not configured.")

        if "audit" in st.session_state:
            st.markdown(f'<div class="ai-box">{st.session_state.audit.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True)

    # ── FOLLOWERS TAB ─────────────────────────────────────────────────────────
    if "👥 Followers" in tm:
        with tm["👥 Followers"]:
            total_new = int(fol_growth["Totaal aantal volgers"].sum())
            fol_growth["Cumulative"] = fol_growth["Totaal aantal volgers"].cumsum()

            f1, f2, f3 = st.columns(3)
            with f1: st.markdown(kpi_card("New followers (period)", f"{total_new:,}".replace(",",".")), unsafe_allow_html=True)
            with f2: st.markdown(kpi_card("Avg per day", f"{fol_growth['Totaal aantal volgers'].mean():.1f}"), unsafe_allow_html=True)
            with f3:
                peak = fol_growth.loc[fol_growth["Totaal aantal volgers"].idxmax()]
                st.markdown(kpi_card("Peak day", peak["Datum"].strftime("%d %b %Y"), delta=f"{int(peak['Totaal aantal volgers'])} new followers"), unsafe_allow_html=True)

            st.markdown('<p class="section-head">Follower growth over time</p>', unsafe_allow_html=True)
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=fol_growth["Datum"], y=fol_growth["Cumulative"],
                fill="tozeroy", line=dict(color=ACCENT, width=2),
                fillcolor="rgba(10,102,194,0.1)", name="Cumulative"))
            fig_f.add_trace(go.Bar(x=fol_growth["Datum"], y=fol_growth["Totaal aantal volgers"],
                marker_color=ORANGE, opacity=0.5, name="New per day", yaxis="y2"))
            fig_f.update_layout(**base_layout(height=300),
                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                yaxis2=dict(overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig_f, use_container_width=True)

            d1, d2 = st.columns(2)
            with d1:
                st.caption("Industry (top 10)")
                df_b = fol_sheets["Branche"].head(10).sort_values(fol_sheets["Branche"].columns[1], ascending=True)
                st.plotly_chart(horiz_bar(df_b, df_b.columns[1], df_b.columns[0], ACCENT, height=300), use_container_width=True)
            with d2:
                st.caption("Function (top 10)")
                df_fn = fol_sheets["Functie"].head(10).sort_values(fol_sheets["Functie"].columns[1], ascending=True)
                st.plotly_chart(horiz_bar(df_fn, df_fn.columns[1], df_fn.columns[0], ORANGE, height=300), use_container_width=True)

    # ── VISITORS TAB ──────────────────────────────────────────────────────────
    if "👁 Visitors" in tm:
        with tm["👁 Visitors"]:
            vcols = [c for c in vis_data.columns if "totaal" in c.lower() and "uniek" not in c.lower() and "pagina" not in c.lower()]
            ucols = [c for c in vis_data.columns if "unieke bezoekers" in c.lower() and "totaal" in c.lower()]
            tc = vcols[0] if vcols else vis_data.columns[1]
            uc = ucols[0] if ucols else vis_data.columns[2]

            v1, v2 = st.columns(2)
            with v1: st.markdown(kpi_card("Total page views", f"{int(vis_data[tc].sum()):,}".replace(",",".")), unsafe_allow_html=True)
            with v2: st.markdown(kpi_card("Unique visitors", f"{int(vis_data[uc].sum()):,}".replace(",",".")), unsafe_allow_html=True)

            st.markdown('<p class="section-head">Visitor trend</p>', unsafe_allow_html=True)
            fig_v = go.Figure()
            fig_v.add_trace(go.Scatter(x=vis_data["Datum"], y=vis_data[tc], line=dict(color=ACCENT, width=2), name="Page views"))
            fig_v.add_trace(go.Scatter(x=vis_data["Datum"], y=vis_data[uc], line=dict(color=ORANGE, width=2, dash="dot"), name="Unique visitors"))
            fig_v.update_layout(**base_layout(height=260), legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig_v, use_container_width=True)

    # ── COMPETITORS TAB ───────────────────────────────────────────────────────
    if "🏆 Competitors" in tm:
        with tm["🏆 Competitors"]:
            st.markdown('<p class="section-head">Benchmark vs competitors</p>', unsafe_allow_html=True)
            for metric, label in [("Nieuwe_volgers","New followers"),("Bijdragen","Posts"),("Reacties","Reactions")]:
                ds = df_comp.sort_values(metric, ascending=True)
                fig = go.Figure(go.Bar(
                    x=ds[metric], y=ds["Pagina"], orientation="h",
                    marker_color=ACCENT,
                    text=ds[metric], textposition="outside",
                ))
                fig.update_layout(**base_layout(height=200),
                                  title=dict(text=label, font=dict(size=13)),
                                  xaxis=dict(showgrid=False, visible=False),
                                  yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True)

    # ── CTA BANNER ────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="cta-banner">
    <div class="cta-text">
        <strong>Rather brainstorm with a human?</strong><br>
        Connect with Bas Oudshoorn — LinkedIn strategist & marketing lead at Leiden Bio Science Park.
    </div>
    <a href="{BAS_URL}" target="_blank">
        <button style="background:#0A66C2;color:white;border:none;padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">
            Connect on LinkedIn →
        </button>
    </a>
    </div>""", unsafe_allow_html=True)

    # Start over
    st.markdown("---")
    if st.button("← Start over with new data"):
        for key in ["df_posts","df_stats","fol_growth","fol_sheets","vis_data","vis_sheets","df_comp","diagnosis","audit"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.step = 1
        st.rerun()
