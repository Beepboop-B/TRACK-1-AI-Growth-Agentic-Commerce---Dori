import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Overhaul CSS tokens
code = re.sub(r'--ame-bg:\s*#[0-9A-Fa-f]+;', '--ame-bg:        #0D0B08;', code)
code = re.sub(r'--ame-surface:\s*#[0-9A-Fa-f]+;', '--ame-surface:   #1A1713;', code)
code = re.sub(r'--ame-surface-2:\s*#[0-9A-Fa-f]+;', '--ame-surface-2: #24201B;', code)
code = re.sub(r'--ame-text:\s*#[0-9A-Fa-f]+;', '--ame-text:      #F3E9D5;', code)
code = re.sub(r'--ame-accent:\s*#[0-9A-Fa-f]+;', '--ame-accent:    #D99A3D;', code)

# 2. Refactor Layout & Implement pages
# We will find the split point where main layout starts.
split_token = "# ============================================================================\n# MAIN LAYOUT\n# ============================================================================"
parts = code.split(split_token)
if len(parts) != 2:
    print("Could not find MAIN LAYOUT section")
    exit(1)

head, tail = parts

# Let's remove the old sidebar from head
sidebar_token = "# ============================================================================\n# SIDEBAR"
head_parts = head.split(sidebar_token)
head_no_sidebar = head_parts[0]

sidebar_code = """# ============================================================================
# SIDEBAR
# ============================================================================
page = st.sidebar.radio("Navigation", ["COMMAND CENTER", "BUYER AGENT", "MERCHANT", "TRANSACTIONS"])

"""

main_code = """
if page == "COMMAND CENTER":
    st.markdown('<div class="ame-panel-title">COMMAND CENTER</div>', unsafe_allow_html=True)
    try:
        tx_res = requests.get(f"{BACKEND_URL}/transactions", timeout=5)
        if tx_res.status_code == 200:
            tx_data = tx_res.json()
            if isinstance(tx_data, dict) and "transactions" in tx_data:
                txs = tx_data["transactions"]
            elif isinstance(tx_data, list):
                txs = tx_data
            else:
                txs = []
            
            total_gmv = sum(t.get("total_negotiated_price_inr", 0) for t in txs if t.get("status") in ["ACCEPTED", "COUNTER_OFFER"] and t.get("total_negotiated_price_inr"))
            total_tx = len(txs)
            
            st.markdown(f'''
            <div class="ame-panel">
                <div class="ame-deal-row">
                    <div class="ame-deal-item"><div class="k">TOTAL TRANSACTIONS</div><div class="v">{total_tx}</div></div>
                    <div class="ame-deal-item"><div class="k">AGGREGATE GMV</div><div class="v">{fmt_inr(total_gmv)}</div></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.error("Failed to fetch transactions.")
    except Exception as e:
        st.error(f"Error: {e}")

elif page == "BUYER AGENT":
    st.markdown('<div class="ame-panel-title">BUYER AGENT HERO</div>', unsafe_allow_html=True)
    with st.form("intent_form"):
        intent_query = st.text_input("What should I purchase?", "I want 5 units of SaaS PRO.")
        intent_submitted = st.form_submit_button("PROCESS INTENT", use_container_width=True)
        
        if intent_submitted:
            try:
                # POST /agent/buyer/intent
                intent_res = requests.post(f"{BACKEND_URL}/agent/buyer/intent", json={"query": intent_query}, timeout=15)
                if intent_res.status_code == 200:
                    intent_data = intent_res.json()
                    st.success(f"Intent resolved: {intent_data}")
                    # Map intent data to negotiate payload
                    payload = {
                        "sku": intent_data.get("sku", "SaaS-PRO-1M"),
                        "requested_quantity": intent_data.get("quantity", 1),
                        "requested_discount_pct": intent_data.get("discount", 0.0),
                    }
                    st.session_state["last_payload"] = payload
                    st.session_state["last_request_ts"] = datetime.now().strftime("%H:%M:%S")
                    st.session_state["last_payment_status_data"] = None
                    st.session_state["last_payment_status_error"] = None
                    
                    response = requests.post(f"{BACKEND_URL}/agent/negotiate", json=payload, timeout=15)
                    st.session_state["last_response"] = response.json()
                    st.session_state["_just_submitted"] = True
                    st.rerun()
                else:
                    st.error("Failed to process intent.")
            except Exception as e:
                st.error(f"Error communicating with backend: {e}")
                
"""

# The original logic should be part of BUYER AGENT or conditionally shown?
# Actually, the user says "Then automatically pipe the resulting intent... into the existing POST /agent/negotiate flow."
# So I should probably place the original `col1, col2` inside BUYER AGENT.

main_code_part2 = """
    # Original Main Layout
""" + tail.replace("col1, col2 = st.columns(2, gap=\"large\")", "col1, col2 = st.columns(2, gap=\"large\")")

# For MERCHANT page, we just render the sidebar logic there
merchant_code = """
elif page == "MERCHANT":
    st.markdown(
        '<div class="ame-panel-title" style="margin-bottom:14px;">MERCHANT'
        " CATALOG &amp; RULES</div>",
        unsafe_allow_html=True,
    )
    if catalog_error:
        st.error(catalog_error)
    else:
        active_sku = st.session_state.get("sku_input")
        for p in catalog_products:
            sku = p.get("sku", "N/A")
            name = p.get("name", sku)
            is_active = sku == active_sku
            card_cls = "ame-cat-card active" if is_active else "ame-cat-card"
            st.markdown(
                f\"\"\"
                <div class="{card_cls}">
                    <div class="ame-cat-name">{name}</div>
                    <div class="ame-cat-grid">
                        <div><span class="k">SKU</span><br/><span class="v">{sku}</span></div>
                        <div><span class="k">BASE PRICE</span><br/><span class="v">{fmt_inr(p.get('base_price_inr'))}</span></div>
                        <div><span class="k">STOCK</span><br/><span class="v">{p.get('stock')} units</span></div>
                        <div><span class="k">MAX DISCOUNT</span><br/><span class="v">{fmt_pct(p.get('max_discount_pct'))}</span></div>
                    </div>
                </div>
                \"\"\",
                unsafe_allow_html=True,
            )
"""

transactions_code = """
elif page == "TRANSACTIONS":
    st.markdown('<div class="ame-panel-title">TRANSACTION HISTORY</div>', unsafe_allow_html=True)
    try:
        tx_res = requests.get(f"{BACKEND_URL}/transactions", timeout=5)
        if tx_res.status_code == 200:
            tx_data = tx_res.json()
            if isinstance(tx_data, dict) and "transactions" in tx_data:
                txs = tx_data["transactions"]
            elif isinstance(tx_data, list):
                txs = tx_data
            else:
                txs = []
            st.dataframe(txs)
        else:
            st.error("Failed to fetch transactions.")
    except Exception as e:
        st.error(f"Error: {e}")
"""

final_code = head_no_sidebar + sidebar_code + "\n# ============================================================================\n# MAIN LAYOUT\n# ============================================================================\n" + main_code + main_code_part2.replace("\n", "\n    ") + merchant_code + transactions_code

# Wait, `tail` has top-level indentation. Replacing `\n` with `\n    ` will indent it under `elif page == "BUYER AGENT":`.
# But `col1, col2 = st.columns(2, gap="large")` and everything else is in `tail`.
indent_tail = "\n".join("    " + line for line in tail.split("\n"))

final_code = head_no_sidebar + sidebar_code + "\n# ============================================================================\n# MAIN LAYOUT\n# ============================================================================\n" + main_code + "\n" + indent_tail + "\n" + merchant_code + transactions_code

with open("app_new.py", "w", encoding="utf-8") as f:
    f.write(final_code)

print("Generated app_new.py")
