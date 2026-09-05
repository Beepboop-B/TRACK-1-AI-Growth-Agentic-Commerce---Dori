import os
import time
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="A.M.E. // Agentic Merchant Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ============================================================================
# SESSION STATE — single source of truth for the entire app
# ============================================================================
_defaults = {
    "theme": "dark",
    "last_payload": None,
    "last_response": None,
    "last_request_ts": None,
    "last_payment_status_data": None,
    "last_payment_status_error": None,
    "_just_submitted": False,
    "merchant_approved": False,
    "merchant_declined": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

is_dark = st.session_state.theme == "dark"

# ============================================================================
# DESIGN SYSTEM — one CSS injection, driven by one theme variable
# ============================================================================
_dark_vars = """
    --bg: #0D0B08; --surface: #15120E; --surface-el: #1B1712;
    --surface-hover: #211C15;
    --border: rgba(243,233,213,0.10); --border-s: rgba(243,233,213,0.18);
    --t1: #F3E9D5; --t2: #A99B88; --t3: #6E6355;
    --amber: #D99A3D; --amber-l: #E8B45B; --amber-soft: rgba(217,154,61,0.14);
    --green: #35C978; --green-soft: rgba(53,201,120,0.12);
    --red: #E85D5D; --red-soft: rgba(232,93,93,0.12);
    --warn: #E6A43A; --warn-soft: rgba(230,164,58,0.12);
    --shadow: rgba(0,0,0,0.25);
"""
_light_vars = """
    --bg: #F5F1E8; --surface: #FFFFFF; --surface-el: #FFFDF8;
    --surface-hover: #FAF7F0;
    --border: rgba(25,20,15,0.08); --border-s: rgba(25,20,15,0.14);
    --t1: #17130F; --t2: #6F675D; --t3: #9E9588;
    --amber: #D99024; --amber-l: #F0A832; --amber-soft: rgba(217,144,36,0.10);
    --green: #20A866; --green-soft: rgba(32,168,102,0.10);
    --red: #D94B4B; --red-soft: rgba(217,75,75,0.10);
    --warn: #D99024; --warn-soft: rgba(217,144,36,0.10);
    --shadow: rgba(0,0,0,0.06);
"""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {{ {_dark_vars if is_dark else _light_vars} }}

/* ---- Global ---- */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, .stApp {{
    background: var(--bg) !important; color: var(--t1) !important;
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif !important;
}}
.block-container {{
    padding: 2.5rem 2rem 3rem 2rem !important; max-width: 1480px;
}}
section.main {{ overflow-x: hidden; }}
[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--t2) !important; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{ color: var(--t1) !important; }}

/* ---- Hide Streamlit chrome ---- */
header[data-testid="stHeader"] {{ background: transparent !important; }}
#MainMenu, footer {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ---- Typography ---- */
h1,h2,h3,h4,h5,h6 {{ color: var(--t1) !important; font-family: 'Inter', sans-serif !important; }}
.ame-page-title {{
    font-size: 1.7rem; font-weight: 800; color: var(--t1);
    letter-spacing: -0.02em; margin: 0 0 4px 0;
}}
.ame-page-sub {{
    font-size: 0.9rem; color: var(--t2); margin: 0 0 24px 0; line-height: 1.5;
}}

/* ---- Cards ---- */
.card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 16px; padding: 22px 24px; margin-bottom: 16px;
    transition: transform 200ms ease, box-shadow 200ms ease;
    box-shadow: 0 2px 8px var(--shadow);
}}
.card:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px var(--shadow); }}
.card-header {{
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--t3); margin-bottom: 14px;
}}
.card-accent {{ border-left: 3px solid var(--amber); }}

/* ---- KPI ---- */
.kpi {{ text-align: left; }}
.kpi-label {{
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--t3); margin-bottom: 8px;
}}
.kpi-val {{
    font-size: 2rem; font-weight: 800; color: var(--t1);
    line-height: 1.1; margin-bottom: 4px;
}}
.kpi-sub {{ font-size: 0.78rem; color: var(--t2); }}

/* ---- Status pills ---- */
.pill {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 100px; font-size: 0.7rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
    white-space: nowrap;
}}
.pill-green {{ background: var(--green-soft); color: var(--green); }}
.pill-amber {{ background: var(--amber-soft); color: var(--amber); }}
.pill-red   {{ background: var(--red-soft);   color: var(--red); }}

/* ---- Funnel ---- */
.funnel {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
.funnel-step {{
    flex: 1; min-width: 90px; text-align: center; padding: 14px 8px;
    background: var(--surface-el); border-radius: 12px;
    border: 1px solid var(--border);
    transition: border-color 200ms ease;
}}
.funnel-step .fval {{ font-size: 1.6rem; font-weight: 800; color: var(--t1); }}
.funnel-step .flbl {{
    font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--t3); margin-top: 4px;
}}
.funnel-step.fs-green {{ border-color: var(--green); }}
.funnel-step.fs-green .fval {{ color: var(--green); }}
.funnel-step.fs-amber {{ border-color: var(--amber); }}
.funnel-step.fs-amber .fval {{ color: var(--amber); }}
.funnel-arr {{ color: var(--t3); font-size: 0.9rem; flex-shrink: 0; }}

/* ---- Agent messages ---- */
.amsg {{
    padding: 14px 18px; border-radius: 12px; margin-bottom: 10px;
    font-size: 0.88rem; line-height: 1.5; border: 1px solid var(--border);
    background: var(--surface-el);
}}
.amsg-buyer  {{ border-left: 3px solid var(--t2); }}
.amsg-merch  {{ border-left: 3px solid var(--amber); }}
.amsg-pay    {{ border-left: 3px solid var(--green); }}
.amsg-amber  {{ border-left: 3px solid var(--amber); background: var(--amber-soft); }}
.amsg-green  {{ border-left: 3px solid var(--green); background: var(--green-soft); }}
.amsg-red    {{ border-left: 3px solid var(--red); background: var(--red-soft); }}
.amsg-who {{
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--t3); margin-bottom: 4px;
}}

/* ---- Deal row ---- */
.deal-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid var(--border);
}}
.deal-row:last-child {{ border-bottom: none; }}
.deal-k {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--t3); }}
.deal-v {{ font-size: 0.95rem; font-weight: 600; color: var(--t1); }}

/* ---- Table ---- */
.tx-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
.tx-table th {{
    text-align: left; padding: 10px 12px; font-size: 0.68rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--t3); border-bottom: 2px solid var(--border-s);
    white-space: nowrap;
}}
.tx-table td {{
    padding: 12px 12px; border-bottom: 1px solid var(--border);
    color: var(--t1); vertical-align: middle;
}}
.tx-table tr:hover td {{ background: var(--surface-el); }}
.tx-mono {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace; font-size: 0.78rem; }}

/* ---- Buttons ---- */
.stButton > button, .stFormSubmitButton > button {{
    background: var(--amber) !important; color: #0D0B08 !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 10px !important; padding: 10px 20px !important;
    font-size: 0.88rem !important; letter-spacing: 0.01em !important;
    transition: background 180ms ease, transform 180ms ease !important;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
    background: var(--amber-l) !important; transform: translateY(-1px) !important;
}}
.stTextInput > div > div > input {{
    background: var(--surface-el) !important; color: var(--t1) !important;
    border: 1px solid var(--border-s) !important; border-radius: 10px !important;
    padding: 12px 16px !important; font-size: 1rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px var(--amber-soft) !important;
}}

/* ---- Sidebar nav override ---- */
[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: 8px 14px !important; border-radius: 8px !important;
    margin-bottom: 2px !important; transition: background 150ms ease !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: var(--surface-el) !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {{
    background: var(--amber-soft) !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] p {{
    color: var(--amber) !important; font-weight: 700 !important;
}}

/* ---- Expander ---- */
details summary {{ color: var(--t2) !important; font-weight: 600 !important; }}
details {{ border: 1px solid var(--border) !important; border-radius: 12px !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FORMATTING HELPERS
# ============================================================================
def fmt_inr(val):
    if val is None: return "—"
    v = round(float(val), 2)
    return f"₹{int(v):,}" if v == int(v) else f"₹{v:,.2f}"

def fmt_pct(val):
    if val is None: return "—"
    v = round(float(val), 2)
    return f"{int(v)}%" if v == int(v) else f"{v:.1f}%"

# ============================================================================
# DATA FETCH — cached to avoid redundant backend calls per rerun
# ============================================================================
@st.cache_data(ttl=5)
def fetch_transactions():
    try:
        r = requests.get(f"{BACKEND_URL}/transactions", timeout=5)
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict) and "transactions" in d:
                return d["transactions"]
            if isinstance(d, list):
                return d
    except Exception:
        pass
    return []

@st.cache_data(ttl=60)
def fetch_catalog():
    try:
        r = requests.get(f"{BACKEND_URL}/catalog", timeout=5)
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict) and "products" in d:
                return d["products"]
            if isinstance(d, list):
                return d
    except Exception:
        pass
    return []

def check_backend_online():
    try:
        return requests.get(f"{BACKEND_URL}/", timeout=2).status_code == 200
    except Exception:
        return False

txs = fetch_transactions()
catalog_products = fetch_catalog()
agent_online = check_backend_online()

def get_product(sku):
    return next((p for p in catalog_products if p.get("sku") == sku), None)

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown(
        "<h2 style='margin:0 0 2px 0; font-size:1.4rem; font-weight:800; "
        "color:var(--t1) !important; letter-spacing:-0.02em;'>A.M.E.</h2>"
        "<p style='font-size:0.72rem; color:var(--t3) !important; "
        "margin:0 0 20px 0; letter-spacing:0.03em; text-transform:uppercase;'>"
        "Agentic Merchant Engine</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:0 0 12px 0;'/>", unsafe_allow_html=True)

    page = st.radio(
        "NAV", ["COMMAND CENTER", "BUYER AGENT", "TRANSACTIONS"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.62rem; color:var(--t3) !important; "
        "text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;'>Powered by Razorpay</p>",
        unsafe_allow_html=True,
    )

# ============================================================================
# GLOBAL HEADER
# ============================================================================
hdr_l, hdr_r = st.columns([3, 1])
with hdr_l:
    st.markdown(
        "<div class='ame-page-title'>A.M.E. // AGENTIC COMMERCE ENGINE</div>"
        "<div style='font-size:0.85rem; color:var(--t2); margin-bottom:6px;'>"
        "Autonomous commerce infrastructure for AI buyers and merchants.</div>",
        unsafe_allow_html=True,
    )
with hdr_r:
    c_status, c_theme = st.columns([2, 1])
    with c_status:
        dot = "var(--green)" if agent_online else "var(--red)"
        txt = "MERCHANT AGENT ONLINE" if agent_online else "AGENT OFFLINE"
        st.markdown(
            f"<div style='text-align:right; padding-top:8px;'>"
            f"<span class='pill pill-green' style='font-size:0.62rem;'>"
            f"<span style='display:inline-block; width:6px; height:6px; "
            f"border-radius:50%; background:{dot};'></span> {txt}</span></div>",
            unsafe_allow_html=True,
        )
    with c_theme:
        label = "☀ Light" if is_dark else "☾ Dark"
        if st.button(label, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

st.markdown("<hr style='border:none; border-top:1px solid var(--border); margin:4px 0 20px 0;'/>", unsafe_allow_html=True)

# ============================================================================
# PAGE: COMMAND CENTER
# ============================================================================
if page == "COMMAND CENTER":
    st.markdown(
        "<div class='ame-page-title'>COMMAND CENTER</div>"
        "<div class='ame-page-sub'>Agentic commerce performance at a glance.</div>",
        unsafe_allow_html=True,
    )

    # ---- Compute metrics from REAL data ----
    paid_txs = [t for t in txs if t.get("status") == "PAID"]
    gmv = sum(t.get("total_negotiated_price_inr", 0) for t in paid_txs)
    n_orders = len(paid_txs)
    units = sum(t.get("requested_quantity", 0) for t in paid_txs)
    aov = gmv / n_orders if n_orders > 0 else 0
    discs = [t.get("requested_discount_pct", 0) for t in paid_txs]
    avg_disc = sum(discs) / len(discs) if discs else 0

    # ---- REVENUE STORY HERO ----
    st.markdown(f"""<div class='card card-accent' style='background:
        {"linear-gradient(135deg, var(--surface) 0%, var(--surface-el) 100%)" if is_dark
         else "linear-gradient(135deg, #FFFCF5 0%, #FFF8EB 100%)"};
        padding: 32px 36px; margin-bottom: 24px;'>
        <div style='font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); margin-bottom: 12px;'>REVENUE GENERATED</div>
        <div style='font-size: 4rem; font-weight: 800; color: var(--green); line-height: 1.1; margin-bottom: 8px;'>{fmt_inr(gmv)}</div>
        <div style='font-size: 1.05rem; color: var(--t2); font-weight: 500; margin-bottom: 32px;'>
            {n_orders} paid transaction{'s' if n_orders != 1 else ''} &middot; {units} units &middot; {fmt_pct(avg_disc)} avg negotiated discount
        </div>
        
        <div style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--t3); margin-bottom: 16px;'>HOW A.M.E. GENERATED THIS REVENUE</div>
        <div style='display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 0.85rem; font-weight: 600; color: var(--t2);'>
            <div style='background: var(--surface-el); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);'>Buyer intent</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--surface-el); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);'>Product match</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--surface-el); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);'>Policy validation</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--surface-el); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);'>Negotiation</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--amber-soft); color: var(--amber); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--amber);'>Merchant approval</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--surface-el); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);'>Razorpay</div>
            <div style='color: var(--t3);'>&rarr;</div>
            <div style='background: var(--green-soft); color: var(--green); padding: 8px 16px; border-radius: 8px; border: 1px solid var(--green);'>Paid</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ---- ROW 2: Funnel + Merchant Growth ----
    cf, cg = st.columns([2, 1])
    with cf:
        req = len(txs)
        neg = sum(1 for t in txs if t.get("status") in ("ACCEPTED", "COUNTER_OFFER", "PAID"))
        auth = n_orders  # Backend does not track auth explicitly, assuming all paid were authorized
        paid_n = n_orders
        steps = [
            ("REQUESTED", req, ""),
            ("VALIDATED", req, ""), 
            ("NEGOTIATED", neg, ""),
            ("AUTHORIZED", auth, "fs-amber"),
            ("PAID", paid_n, "fs-green"), 
        ]
        funnel_html = "<div class='card'><div class='card-header'>AGENT COMMERCE FUNNEL</div><div class='funnel'>"
        for i, (lbl, val, cls) in enumerate(steps):
            funnel_html += f"<div class='funnel-step {cls}'><div class='fval'>{val}</div><div class='flbl'>{lbl}</div></div>"
            if i < len(steps) - 1:
                funnel_html += "<div class='funnel-arr'>→</div>"
        funnel_html += "</div></div>"
        st.markdown(funnel_html, unsafe_allow_html=True)

    with cg:
        # Cross-sell: for each paid SaaS-PRO-1M, the agent would offer API-CRED-10K at 5% off = 4750
        xs_val = sum(4750 for t in paid_txs if t.get("sku") == "SaaS-PRO-1M")
        st.markdown(f"""<div class='card'>
            <div class='card-header'>MERCHANT GROWTH</div>
            <div style='margin-bottom:16px;'>
                <div class='kpi-label'>REALIZED GMV</div>
                <div class='kpi-val' style='font-size:1.8rem; color:var(--green);'>{fmt_inr(gmv)}</div>
                <div class='kpi-sub'>Actual revenue generated</div>
            </div>
            <hr style='border:none; border-top:1px solid var(--border); margin:12px 0;'/>
            <div>
                <div class='kpi-label'>CROSS-SELL OPPORTUNITY</div>
                <div class='kpi-val' style='font-size:1.5rem;'>{fmt_inr(xs_val)}</div>
                <div style='margin-top:6px;'><span class='pill pill-amber'>OFFERED — NOT PURCHASED</span></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ---- ROW 3: Commerce Performance + Activity ----
    cp, ca = st.columns([1, 2])
    with cp:
        base_val = sum(
            t.get("requested_quantity", 0) * (get_product(t.get("sku", "")) or {}).get("base_price_inr", 0)
            for t in paid_txs
        )
        savings = base_val - gmv
        st.markdown(f"""<div class='card'>
            <div class='card-header'>COMMERCE PERFORMANCE</div>
            <div class='deal-row'><span class='deal-k'>BASE VALUE</span><span class='deal-v'>{fmt_inr(base_val)}</span></div>
            <div class='deal-row'><span class='deal-k'>NEGOTIATED VALUE</span><span class='deal-v'>{fmt_inr(gmv)}</span></div>
            <div class='deal-row'><span class='deal-k' style='color:var(--green);'>CUSTOMER SAVINGS</span>
                <span class='deal-v' style='color:var(--green);'>{fmt_inr(savings)}</span></div>
            <hr style='border:none; border-top:1px solid var(--border); margin:8px 0;'/>
            <div class='deal-row' style='border:none;'><span class='deal-k'>MERCHANT REALIZED</span>
                <span style='font-size:1.4rem; font-weight:800; color:var(--green);'>{fmt_inr(gmv)}</span></div>
        </div>""", unsafe_allow_html=True)

        # Guardrails
        pro = get_product("SaaS-PRO-1M")
        if pro:
            st.markdown(f"""<div class='card'>
                <div class='card-header'>MERCHANT GUARDRAILS</div>
                <div class='deal-row'><span class='deal-k'>MAX DISCOUNT</span><span class='deal-v'>{fmt_pct(pro.get('max_discount_pct'))}</span></div>
                <div class='deal-row'><span class='deal-k'>INVENTORY</span><span class='deal-v'>{pro.get('stock')} units</span></div>
                <div class='deal-row'><span class='deal-k'>POLICY SOURCE</span><span class='deal-v'>Merchant Catalog</span></div>
                <div style='font-size:0.75rem; color:var(--t3); margin-top:10px; line-height:1.5;'>
                    Discount and inventory constraints are deterministic merchant rules. The agent cannot exceed them.
                </div>
            </div>""", unsafe_allow_html=True)

    with ca:
        act_html = "<div class='card'><div class='card-header'>RECENT AGENT ACTIVITY</div>"
        if txs:
            for t in reversed(txs[-5:]):
                s = t.get("status", "")
                pcls = "pill-green" if s == "PAID" else ("pill-red" if s == "REJECTED" else "pill-amber")
                ts = t.get("timestamp", "")[:19].replace("T", " ")
                tid = t.get("transaction_id", "")[-8:]
                act_html += f"""<div style='padding:12px 0; border-bottom:1px solid var(--border);'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>
                        <span style='font-size:0.72rem; color:var(--t3);'>{ts}</span>
                        <span class='pill {pcls}'>{s}</span>
                    </div>
                    <div style='font-size:0.88rem;'>AI Buyer → <b>{t.get('requested_quantity')} × {t.get('sku')}</b>
                        — {fmt_pct(t.get('requested_discount_pct'))} discount
                        — <b>{fmt_inr(t.get('total_negotiated_price_inr'))}</b>
                        <span class='tx-mono' style='color:var(--t3); margin-left:8px;'>{tid}</span>
                    </div>
                </div>"""
        else:
            act_html += "<div style='color:var(--t3); font-size:0.88rem; padding:20px 0;'>No agent activity yet. Run the Buyer Agent to create your first transaction.</div>"
        act_html += "</div>"
        st.markdown(act_html, unsafe_allow_html=True)

        # Top products
        prod_sales = {}
        for t in paid_txs:
            sk = t.get("sku", "")
            prod_sales[sk] = prod_sales.get(sk, {"units": 0, "rev": 0})
            prod_sales[sk]["units"] += t.get("requested_quantity", 0)
            prod_sales[sk]["rev"] += t.get("total_negotiated_price_inr", 0)

        tp_html = "<div class='card'><div class='card-header'>TOP PRODUCTS</div>"
        if prod_sales:
            for sk, d in sorted(prod_sales.items(), key=lambda x: -x[1]["rev"]):
                pname = (get_product(sk) or {}).get("name", sk)
                tp_html += f"""<div class='deal-row'>
                    <div><span style='font-weight:600;'>{pname}</span>
                    <span class='tx-mono' style='color:var(--t3); margin-left:8px; font-size:0.72rem;'>{sk}</span></div>
                    <div style='text-align:right;'><span style='font-weight:700;'>{fmt_inr(d['rev'])}</span>
                    <span style='color:var(--t3); font-size:0.78rem; margin-left:8px;'>{d['units']} units</span></div>
                </div>"""
        else:
            tp_html += "<div style='color:var(--t3); font-size:0.85rem;'>No product sales data yet.</div>"
        tp_html += "</div>"
        st.markdown(tp_html, unsafe_allow_html=True)


# ============================================================================
# PAGE: BUYER AGENT
# ============================================================================
elif page == "BUYER AGENT":
    st.markdown(
        "<div class='ame-page-title'>BUYER AGENT</div>"
        "<div class='ame-page-sub'>Tell the agent what you want to buy.</div>",
        unsafe_allow_html=True,
    )

    # ---- Intent form ----
    with st.form("intent_form"):
        intent_query = st.text_input(
            "", value="Find me 5 Pro Licenses under ₹9,500 and buy them.",
            label_visibility="collapsed",
        )
        intent_submitted = st.form_submit_button("PROCESS INTENT →", use_container_width=True)

        if intent_submitted:
            try:
                intent_res = requests.post(
                    f"{BACKEND_URL}/agent/buyer/intent",
                    json={"query": intent_query}, timeout=15,
                )
                if intent_res.status_code == 200:
                    intent_data = intent_res.json()
                    payload = {
                        "sku": intent_data.get("sku", "SaaS-PRO-1M"),
                        "requested_quantity": intent_data.get("requested_quantity", 1),
                        "requested_discount_pct": intent_data.get("requested_discount_pct", 0.0),
                    }
                    st.session_state["last_payload"] = payload
                    st.session_state["last_request_ts"] = datetime.now().strftime("%H:%M:%S")
                    st.session_state["last_payment_status_data"] = None
                    st.session_state["last_payment_status_error"] = None
                    response = requests.post(
                        f"{BACKEND_URL}/agent/negotiate", json=payload, timeout=15,
                    )
                    st.session_state["last_response"] = response.json()
                    st.session_state["_just_submitted"] = True
                    st.session_state["merchant_approved"] = False
                    st.session_state["merchant_declined"] = False
                    st.rerun()
                else:
                    st.error("Failed to process intent. Check backend logs.")
            except Exception as e:
                st.error(f"Error communicating with backend: {e}")

    # ---- Agent journey pipeline ----
    res = st.session_state.get("last_response")
    payl = st.session_state.get("last_payload") or {}
    psd = st.session_state.get("last_payment_status_data")
    pse = st.session_state.get("last_payment_status_error")
    live_pay_status = (psd or {}).get("status")
    is_paid = live_pay_status == "paid"

    if res:
        status = res.get("status", "")
        prod = get_product(payl.get("sku"))

        # Determine pipeline stage states
        is_appr = st.session_state.merchant_approved
        is_decl = st.session_state.merchant_declined
        
        stages = [
            ("DISCOVER", True, "green"),
            ("SELECT", True, "green"),
            ("VALIDATE", status != "REJECTED", "green" if status != "REJECTED" else "red"),
            ("NEGOTIATE", status in ("ACCEPTED", "COUNTER_OFFER"), "green" if status in ("ACCEPTED", "COUNTER_OFFER") else "red"),
            ("AUTHORIZE", is_appr or is_decl or status in ("ACCEPTED", "COUNTER_OFFER"), "green" if is_appr else ("red" if is_decl else "amber")),
            ("PAY", bool(res.get("razorpay_order_id")) and is_appr, "amber" if (is_appr and not is_paid) else ("green" if is_paid else "")),
            ("CONFIRM", is_paid, "green" if is_paid else ""),
        ]
        pipe_html = "<div style='display:flex; align-items:center; gap:8px; margin:16px 0 28px 0; flex-wrap:wrap;'>"
        for i, (lbl, active, color) in enumerate(stages):
            if active and color == "green":
                bg, tc = "var(--green-soft)", "var(--green)"
            elif active and color == "amber":
                bg, tc = "var(--amber-soft)", "var(--amber)"
            elif active and color == "red":
                bg, tc = "var(--red-soft)", "var(--red)"
            else:
                bg, tc = "var(--surface-el)", "var(--t3)"
            icon = "✓" if active and color == "green" else ("●" if active else "○")
            pipe_html += f"<div style='display:flex; align-items:center; gap:6px; padding:6px 14px; border-radius:8px; background:{bg};'>"
            pipe_html += f"<span style='color:{tc}; font-size:0.8rem;'>{icon}</span>"
            pipe_html += f"<span style='color:{tc}; font-size:0.68rem; font-weight:700; letter-spacing:0.05em;'>{lbl}</span></div>"
            if i < len(stages) - 1:
                pipe_html += "<span style='color:var(--t3);'>→</span>"
        pipe_html += "</div>"
        st.markdown(pipe_html, unsafe_allow_html=True)

        # ---- Two-column layout ----
        c_left, c_right = st.columns([1, 1], gap="large")

        with c_left:
            # Agent-to-Agent conversation
            st.markdown("<div class='card-header'>AGENT-TO-AGENT COMMERCE</div>", unsafe_allow_html=True)

            msgs = []
            msgs.append(("AI BUYER", "buyer", f'I need {payl.get("requested_quantity")} units of {payl.get("sku")} with a {payl.get("requested_discount_pct")}% discount.'))
            if prod:
                msgs.append(("MERCHANT AGENT", "merch", f'Catalog match: <b>{prod.get("name")}</b>. Inventory validated — {prod.get("stock")} units available.'))
                msgs.append(("POLICY ENGINE", "merch", f'Requested discount: {fmt_pct(payl.get("requested_discount_pct"))}. Maximum permitted: {fmt_pct(prod.get("max_discount_pct"))}. <b>WITHIN POLICY</b>.'))
            msgs.append(("MERCHANT AGENT", "merch", f'Offer <b>{status}</b>. Unit price: <b>{fmt_inr(res.get("negotiated_unit_price"))}</b>. Total: <b>{fmt_inr(res.get("total_negotiated_price_inr"))}</b>.'))
            
            if not is_appr and not is_decl:
                msgs.append(("SYSTEM", "amber", "MERCHANT AUTHORIZATION REQUIRED"))
            elif is_decl:
                msgs.append(("SYSTEM", "red", "MERCHANT AUTHORIZATION DECLINED"))
            elif is_appr:
                msgs.append(("SYSTEM", "green", "MERCHANT AUTHORIZATION GRANTED"))
                if res.get("razorpay_order_id"):
                    msgs.append(("RAZORPAY", "pay", f'Order created: <span class="tx-mono">{res.get("razorpay_order_id")}</span>'))
                if is_paid:
                    msgs.append(("BUYER", "pay", f"✓ Payment completed and verified. <b>{fmt_inr(res.get('total_negotiated_price_inr'))} PAID</b>"))

            for who, cls, text in msgs:
                st.markdown(f'<div class="amsg amsg-{cls}"><div class="amsg-who">{who}</div>{text}</div>', unsafe_allow_html=True)

            # Cross-sell opportunity
            cross = res.get("cross_sell")
            if cross:
                cs_name = cross.get("name", "")
                cs_base = cross.get("base_price_inr")
                cs_price = cross.get("offered_price_inr")
                cs_disc = cross.get("offered_discount_pct")
                st.markdown(f"""<div class='card' style='border-color:var(--amber);'>
                    <div class='card-header'>REVENUE OPPORTUNITY</div>
                    <div class='deal-row'><span class='deal-k'>PRODUCT</span><span class='deal-v'>{cs_name}</span></div>
                    <div class='deal-row'><span class='deal-k'>BASE PRICE</span><span class='deal-v' style='text-decoration:line-through; color:var(--t3);'>{fmt_inr(cs_base)}</span></div>
                    <div class='deal-row'><span class='deal-k'>AGENT OFFER</span><span class='deal-v' style='color:var(--green);'>{fmt_inr(cs_price)}</span></div>
                    <div style='margin-top:8px;'><span class='pill pill-amber'>OFFERED — NOT PURCHASED</span></div>
                </div>""", unsafe_allow_html=True)

            # Audit trail
            with st.expander("AUDIT TRAIL — RAW EVENT PAYLOAD"):
                st.json(res)
                if psd:
                    st.caption("Latest Razorpay payment status:")
                    st.json(psd)

        with c_right:
            # Live Deal card
            st.markdown("<div class='card-header'>LIVE DEAL</div>", unsafe_allow_html=True)
            base_p = (prod.get("base_price_inr", 0) if prod else 0)
            qty = payl.get("requested_quantity", 1)
            base_total = base_p * qty
            neg_total = res.get("total_negotiated_price_inr", 0)
            deal_savings = base_total - neg_total

            st_pill = "pill-green" if is_paid else "pill-amber"
            st_text = "✓ PAID — ORDER COMPLETE" if is_paid else "PAYMENT PENDING"

            st.markdown(f"""<div class='card' style='border-color:var(--amber);'>
                <div class='deal-row'><span class='deal-k'>PRODUCT</span><span class='deal-v'>{prod.get('name') if prod else payl.get('sku')}</span></div>
                <div class='deal-row'><span class='deal-k'>SKU</span><span class='deal-v tx-mono'>{payl.get('sku')}</span></div>
                <div class='deal-row'><span class='deal-k'>QUANTITY</span><span class='deal-v'>{qty} units</span></div>
                <div class='deal-row'><span class='deal-k'>ORIGINAL TOTAL</span><span class='deal-v' style='text-decoration:line-through; color:var(--t3);'>{fmt_inr(base_total)}</span></div>
                <hr style='border:none; border-top:1px solid var(--border); margin:6px 0;'/>
                <div style='display:flex; justify-content:space-between; align-items:end; padding:12px 0;'>
                    <span class='deal-k'>NEGOTIATED TOTAL</span>
                    <span style='font-size:2.4rem; font-weight:800; color:var(--t1); line-height:1;'>{fmt_inr(neg_total)}</span>
                </div>
                <div class='deal-row' style='color:var(--green);'>
                    <span class='deal-k' style='color:var(--green);'>SAVINGS</span>
                    <span class='deal-v' style='color:var(--green);'>{fmt_inr(deal_savings)}</span>
                </div>
                <div style='text-align:right; margin-top:12px;'><span class='pill {st_pill}'>{st_text}</span></div>
            </div>""", unsafe_allow_html=True)

            # Why This Decision
            st.markdown("<div class='card-header'>WHY THIS DECISION?</div>", unsafe_allow_html=True)
            max_d = prod.get("max_discount_pct", 0) if prod else 0
            req_d = payl.get("requested_discount_pct", 0)
            within = req_d <= max_d
            st.markdown(f"""<div class='card'>
                <div class='deal-row'><span class='deal-k'>REQUESTED DISCOUNT</span><span class='deal-v'>{fmt_pct(req_d)}</span></div>
                <div class='deal-row'><span class='deal-k'>MAX PERMITTED</span><span class='deal-v'>{fmt_pct(max_d)}</span></div>
                <div class='deal-row'><span class='deal-k'>REQUESTED QTY</span><span class='deal-v'>{qty}</span></div>
                <div class='deal-row'><span class='deal-k'>INVENTORY</span><span class='deal-v'>{prod.get('stock') if prod else '—'} units</span></div>
                <hr style='border:none; border-top:1px solid var(--border); margin:6px 0;'/>
                <div style='font-weight:700; font-size:0.95rem; margin-bottom:4px;'>REQUEST {status}</div>
                <div style='font-size:0.82rem; color:var(--t2); line-height:1.5;'>
                    {'Autonomous agent check passed: requested discount is within acceptable merchant bounds.'
                     if within else res.get('reason', 'Policy check completed.')}
                </div>
            </div>""", unsafe_allow_html=True)

            # Guardrails
            if prod:
                st.markdown(f"""<div class='card'>
                    <div class='card-header'>MERCHANT GUARDRAILS</div>
                    <div class='deal-row'><span class='deal-k'>MAX DISCOUNT</span><span class='deal-v'>{fmt_pct(prod.get('max_discount_pct'))}</span></div>
                    <div class='deal-row'><span class='deal-k'>STOCK</span><span class='deal-v'>{prod.get('stock')} units</span></div>
                    <div class='deal-row'><span class='deal-k'>POLICY</span><span class='deal-v'>Merchant Catalog</span></div>
                    <div style='font-size:0.75rem; color:var(--t3); margin-top:10px; line-height:1.5;'>
                        Discount bounds and inventory limits are hard-coded merchant rules, not LLM judgment.
                    </div>
                </div>""", unsafe_allow_html=True)

            # ---- MERCHANT AUTHORIZATION & RAZORPAY CHECKOUT ----
            order_id = res.get("razorpay_order_id")
            payment_error = res.get("payment_error")

            if payment_error:
                st.error(f"Razorpay order creation failed: {payment_error}")
            elif is_decl:
                st.markdown("<div class='card' style='border-color:var(--red);'>"
                            "<div class='card-header' style='color:var(--red);'>MERCHANT DECLINED</div>"
                            "<div style='font-size:0.85rem; color:var(--t2);'>A.M.E. prepared the transaction, but merchant authorization was not granted. Transaction not charged.</div>"
                            "</div>", unsafe_allow_html=True)
            elif order_id and not is_paid and not is_appr:
                st.markdown(f"<div class='card' style='border-color:var(--amber);'>"
                            "<div class='card-header'>MERCHANT AUTHORIZATION</div>"
                            "<div style='font-size:0.85rem; color:var(--t2); margin-bottom:12px;'>A.M.E. has prepared a transaction.</div>"
                            f"<div class='deal-row'><span class='deal-k'>PRODUCT</span><span class='deal-v'>{qty} × {prod.get('name') if prod else payl.get('sku')}</span></div>"
                            f"<div class='deal-row'><span class='deal-k'>UNIT PRICE</span><span class='deal-v'>{fmt_inr(res.get('negotiated_unit_price'))}</span></div>"
                            f"<div class='deal-row'><span class='deal-k'>DISCOUNT</span><span class='deal-v'>{fmt_pct(req_d)}</span></div>"
                            f"<hr style='border:none; border-top:1px solid var(--border); margin:8px 0;'/>"
                            f"<div class='deal-row'><span class='deal-k'>EXPECTED REVENUE</span><span class='deal-v' style='font-size:1.4rem; color:var(--green);'>{fmt_inr(neg_total)}</span></div>"
                            "</div>", unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("APPROVE PAYMENT", type="primary", use_container_width=True):
                        st.session_state.merchant_approved = True
                        st.rerun()
                with c_btn2:
                    if st.button("REJECT", use_container_width=True):
                        st.session_state.merchant_declined = True
                        st.rerun()

                st.markdown("<div style='text-align:center; font-size:0.75rem; color:var(--t3); margin-top:8px;'>Merchant approval link accessible in deployed version</div>", unsafe_allow_html=True)

            elif order_id and not is_paid and is_appr:
                st.markdown("<div class='card-header' style='color:var(--green); margin-top:8px;'>✓ MERCHANT APPROVED</div>", unsafe_allow_html=True)
                key_id = res.get("razorpay_key_id") or ""
                amount_paise = res.get("amount_paise") or 0
                checkout_html = f"""
                <div style="font-family:'Inter',-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
                  <button id="rzp-btn-{order_id}" style="
                      background:#D99A3D; color:#0D0B08; font-weight:700; font-size:14px;
                      letter-spacing:0.01em; padding:12px 24px; border:none;
                      border-radius:10px; cursor:pointer; width:100%;">
                    PAY VIA RAZORPAY →
                  </button>
                  <div id="rzp-result-{order_id}" style="margin-top:10px; font-family:'SFMono-Regular',Consolas,monospace; font-size:12px; color:#A99B88;"></div>
                  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                  <script>
                    (function() {{
                      var resetIframe = function() {{
                        if (window.frameElement) {{
                          window.frameElement.style.position = 'static';
                          window.frameElement.style.width = '100%';
                          window.frameElement.style.height = '110px';
                          window.frameElement.style.zIndex = 'auto';
                        }}
                      }};

                      var options = {{
                        "key": "{key_id}",
                        "amount": "{amount_paise}",
                        "currency": "INR",
                        "name": "A.M.E. Merchant",
                        "description": "Order {order_id}",
                        "order_id": "{order_id}",
                        "handler": function (response) {{
                          resetIframe();
                          document.getElementById("rzp-result-{order_id}").innerText =
                            "Submitted — payment_id " + response.razorpay_payment_id +
                            ". Click CHECK PAYMENT STATUS below to confirm.";
                        }},
                        "modal": {{
                          "ondismiss": function () {{
                            resetIframe();
                            document.getElementById("rzp-result-{order_id}").innerText =
                              "Checkout closed without completing payment.";
                          }}
                        }},
                        "theme": {{ "color": "#D99A3D" }}
                      }};
                      var rzp = new Razorpay(options);
                      rzp.on("payment.failed", function (response) {{
                        resetIframe();
                        document.getElementById("rzp-result-{order_id}").innerText =
                          "Payment failed: " + response.error.description;
                      }});
                      document.getElementById("rzp-btn-{order_id}").onclick = function (e) {{
                        e.preventDefault();
                        if (window.frameElement) {{
                          window.frameElement.style.position = 'fixed';
                          window.frameElement.style.top = '0';
                          window.frameElement.style.left = '0';
                          window.frameElement.style.width = '100vw';
                          window.frameElement.style.height = '100vh';
                          window.frameElement.style.zIndex = '999999';
                        }}
                        rzp.open();
                      }};
                    }})();
                  </script>
                </div>
                """
                components.html(checkout_html, height=110)

            if order_id and is_appr:
                if st.button("CHECK PAYMENT STATUS", key=f"chk_{order_id}", use_container_width=True):
                    try:
                        sr = requests.get(f"{BACKEND_URL}/agent/payment-status/{order_id}", timeout=10)
                        if sr.status_code == 200:
                            st.session_state["last_payment_status_data"] = sr.json()
                            st.session_state["last_payment_status_error"] = None
                        else:
                            st.session_state["last_payment_status_data"] = None
                            try:
                                detail = sr.json().get("detail", sr.text)
                            except Exception:
                                detail = sr.text
                            st.session_state["last_payment_status_error"] = detail
                    except Exception as e:
                        st.session_state["last_payment_status_data"] = None
                        st.session_state["last_payment_status_error"] = f"Backend error: {e}"
                    st.rerun()

                if pse:
                    st.error(f"Could not verify payment: {pse}")
                elif psd:
                    amt_inr = (psd.get("amount_paid") or 0) / 100
                    st.markdown(
                        f"<div style='font-size:0.82rem; color:var(--t2); margin-top:8px;'>"
                        f"Razorpay status: <b>{psd.get('status')}</b> · "
                        f"Amount paid: <b>{fmt_inr(amt_inr)}</b></div>",
                        unsafe_allow_html=True,
                    )

    else:
        # Empty state
        st.markdown("""<div class='card' style='text-align:center; padding:40px 20px;'>
            <div style='font-size:1.1rem; color:var(--t2); margin-bottom:8px;'>
                Enter a natural-language purchase request above to begin.
            </div>
            <div style='font-size:0.85rem; color:var(--t3);'>
                Example: "Find me 5 Pro Licenses under ₹9,500 and buy them."
            </div>
        </div>""", unsafe_allow_html=True)


# ============================================================================
# PAGE: TRANSACTIONS
# ============================================================================
elif page == "TRANSACTIONS":
    st.markdown(
        "<div class='ame-page-title'>TRANSACTION HISTORY</div>"
        "<div class='ame-page-sub'>Every autonomous commerce event recorded by A.M.E.</div>",
        unsafe_allow_html=True,
    )

    if txs:
        # Build HTML table using ACTUAL transaction schema fields
        tbl = "<div style='overflow-x:auto;'><table class='tx-table'><thead><tr>"
        cols = ["Timestamp", "SKU", "Qty", "Total", "Authorization", "Payment", "Razorpay Order"]
        for c in cols:
            tbl += f"<th>{c}</th>"
        tbl += "</tr></thead><tbody>"

        for t in reversed(txs):
            s = t.get("status", "")
            auth_s = "APPROVED" if s == "PAID" else ("DECLINED" if s == "REJECTED" else "PENDING")
            auth_cls = "pill-green" if auth_s == "APPROVED" else ("pill-red" if auth_s == "DECLINED" else "pill-amber")
            
            pay_s = s if s in ("PAID", "FAILED") else "PENDING"
            pay_cls = "pill-green" if pay_s == "PAID" else ("pill-red" if pay_s == "FAILED" else "pill-amber")
            
            ts_raw = t.get("timestamp", "")
            ts_display = ts_raw[:19].replace("T", " ") if ts_raw else "—"
            oid = t.get("razorpay_order_id") or "—"

            tbl += "<tr>"
            tbl += f"<td class='tx-mono'>{ts_display}</td>"
            tbl += f"<td class='tx-mono'>{t.get('sku', '—')}</td>"
            tbl += f"<td>{t.get('requested_quantity', '—')}</td>"
            tbl += f"<td style='font-weight:700;'>{fmt_inr(t.get('total_negotiated_price_inr'))}</td>"
            tbl += f"<td><span class='pill {auth_cls}'>{auth_s}</span></td>"
            tbl += f"<td><span class='pill {pay_cls}'>{pay_s}</span></td>"
            tbl += f"<td class='tx-mono' style='font-size:0.72rem;'>{oid}</td>"
            tbl += "</tr>"

        tbl += "</tbody></table></div>"
        st.markdown(tbl, unsafe_allow_html=True)
    else:
        st.markdown("""<div class='card' style='text-align:center; padding:40px 20px;'>
            <div style='font-size:1.1rem; color:var(--t2); margin-bottom:8px;'>
                NO COMPLETED TRANSACTIONS YET
            </div>
            <div style='font-size:0.85rem; color:var(--t3);'>
                Run the Buyer Agent to create your first autonomous commerce transaction.
            </div>
        </div>""", unsafe_allow_html=True)
