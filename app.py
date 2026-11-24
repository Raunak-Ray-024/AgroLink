"""
Bharat AgroLink - Mini Agriculture Marketplace (Streamlit UI)

Run the API (optional):  uvicorn main:app --reload
Run this UI:             streamlit run app.py

If the FastAPI backend is reachable, the UI uses it for the product listing,
product create/update and the order calculation. If not, it falls back to
data.json and an identical local calculation, so the UI always works.
"""
import json
import os
import uuid
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Bharat AgroLink",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path(__file__).with_name("data.json")
DEFAULT_API = os.getenv("AGROLINK_API", "http://127.0.0.1:8000")
GST_RATE = 0.18
PAGES = ["Marketplace", "Cart", "Order summary", "Dashboard", "Seller desk"]
BROWNS = ["#D39A5B", "#A8693A", "#7A4B2A", "#C9A57A", "#8C5A35", "#5C3A21"]

# ------------------------------------------------------------------ styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Young+Serif&family=Figtree:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Figtree', sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 80% -10%, #3a2214 0%, #1E120B 55%); }
h1, h2, h3, .brand, .hero h1 { font-family: 'Young Serif', serif !important; letter-spacing: .2px; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; max-width: 1250px; }

section[data-testid="stSidebar"] { background: linear-gradient(180deg, #2B170D 0%, #1A0E07 100%); border-right: 1px solid #4a2f1f; }
.brand { font-size: 1.5rem; color: #F1E3D0; margin-bottom: .1rem; }
.brand-sub { color: #C9A57A; font-size: .85rem; margin-bottom: 1rem; }

/* ---- hero: drifting furrows are the one big motion on the page ---- */
.hero { position: relative; overflow: hidden; border-radius: 22px; padding: 2.2rem 2.4rem; margin-bottom: 1rem;
  background: linear-gradient(120deg, #4a2c19 0%, #6b4226 55%, #8a5a34 100%); border: 1px solid #8a5a34;
  display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }
.furrows { position: absolute; inset: -40% -10% -10% -10%; opacity: .35; transform: perspective(500px) rotateX(58deg);
  background: repeating-linear-gradient(90deg, rgba(20,10,4,.75) 0 6px, rgba(211,154,91,.35) 6px 22px, transparent 22px 44px);
  animation: drift 14s linear infinite; }
@keyframes drift { from { background-position: 0 0; } to { background-position: 440px 0; } }
.hero-inner { position: relative; z-index: 1; }
.hero h1 { color: #FBEBD3; font-size: 2.5rem; margin: 0; }
.hero p { color: #F0D9B8; margin: .4rem 0 0; max-width: 520px; font-size: 1.02rem; }
.cart-pill { position: relative; z-index: 1; background: rgba(30,18,11,.78); border: 1px solid #C9A57A; color: #FBEBD3;
  border-radius: 999px; padding: .7rem 1.2rem; font-weight: 600; backdrop-filter: blur(4px); }
.cart-pill.pop-a { animation: pop-a .45s ease; }
.cart-pill.pop-b { animation: pop-b .45s ease; }
@keyframes pop-a { 0% { transform: scale(1);} 40% { transform: scale(1.12);} 100% { transform: scale(1);} }
@keyframes pop-b { 0% { transform: scale(1);} 40% { transform: scale(1.12);} 100% { transform: scale(1);} }

.ticker { overflow: hidden; white-space: nowrap; border-top: 1px solid #4a2f1f; border-bottom: 1px solid #4a2f1f;
  margin-bottom: 1.2rem; padding: .45rem 0; color: #C9A57A; font-size: .9rem; }
.ticker span { display: inline-block; padding-left: 100%; animation: scroll 32s linear infinite; }
@keyframes scroll { to { transform: translateX(-100%); } }

/* ---- product cards ---- */
div[data-testid="stVerticalBlockBorderWrapper"] { background: #2E1C11; border-color: #5a3a24 !important; border-radius: 18px;
  transition: transform .2s ease, border-color .2s ease; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { transform: translateY(-3px); border-color: #D39A5B !important; }
.p-img { height: 120px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 3.6rem;
  background-size: cover; position: relative; overflow: hidden; }
.p-img::after { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(135deg, rgba(255,255,255,.05) 0 8px, transparent 8px 16px); }
.p-img.oos { filter: grayscale(.9) brightness(.6); }
.chip { display: inline-block; font-size: .75rem; padding: .15rem .6rem; border-radius: 999px; background: #4a2f1f; color: #E8C79A; margin: .6rem 0 .2rem; }
.p-name { font-size: 1.12rem; font-weight: 700; color: #FBEBD3; }
.p-seller { font-size: .85rem; color: #B99572; }
.p-price { font-size: 1.45rem; font-weight: 700; color: #F0B876; margin: .3rem 0; }
.bar { height: 7px; background: #43291a; border-radius: 6px; overflow: hidden; margin-top: .25rem; }
.bar i { display: block; height: 100%; border-radius: 6px; background: linear-gradient(90deg, #A8693A, #E3B27A); animation: fill 1s ease-out; }
@keyframes fill { from { width: 0 !important; } }
.stock-note { font-size: .82rem; color: #C9A57A; margin-bottom: .5rem; }
.stock-note.low { color: #F0A060; }
.stock-note.out { color: #E58B7A; }

/* ---- buttons / inputs ---- */
.stButton > button, .stFormSubmitButton > button { border-radius: 12px; border: 1px solid #8a5a34; background: #5C3A21; color: #FBEBD3; font-weight: 600; transition: all .18s ease; }
.stButton > button:hover:not(:disabled) { background: #A8693A; border-color: #D39A5B; transform: translateY(-1px); color: #fff; }
.stButton > button:disabled { background: #2a1a10; color: #7a6350; border-color: #3d281a; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background: linear-gradient(135deg, #C98B4E, #8C5A35); border: none; color: #1E120B; }

/* ---- kpis, tables, receipts ---- */
.kpi { background: linear-gradient(145deg, #3a2314, #2a170c); border: 1px solid #5a3a24; border-radius: 16px; padding: 1rem 1.2rem; animation: rise .6s ease both; }
.kpi .v { font-size: 1.8rem; font-weight: 700; color: #F0B876; }
.kpi .l { color: #C9A57A; font-size: .88rem; }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.seller-card { background: #2E1C11; border: 1px solid #5a3a24; border-left: 5px solid #D39A5B; border-radius: 14px; padding: 1rem 1.2rem; margin-bottom: .9rem; }
.seller-card h4 { margin: 0 0 .5rem; color: #FBEBD3; }
table.ord { width: 100%; border-collapse: collapse; color: #F1E3D0; font-size: .95rem; }
table.ord th { text-align: left; color: #C9A57A; font-weight: 600; border-bottom: 1px solid #5a3a24; padding: .35rem .2rem; }
table.ord td { padding: .4rem .2rem; border-bottom: 1px dashed #4a2f1f; }
table.ord td.r, table.ord th.r { text-align: right; }
.sub-row { display: flex; justify-content: space-between; margin-top: .5rem; color: #E8C79A; font-weight: 600; }
.totals { background: linear-gradient(160deg, #4a2c19, #2a170c); border: 1px solid #8a5a34; border-radius: 18px; padding: 1.2rem 1.4rem; }
.totals .row { display: flex; justify-content: space-between; padding: .3rem 0; color: #E8C79A; }
.totals .final { border-top: 1px solid #8a5a34; margin-top: .4rem; padding-top: .7rem; font-size: 1.6rem; font-weight: 700; color: #FBEBD3; }
.stamp { text-align: center; padding: 2rem; border: 2px dashed #D39A5B; border-radius: 20px; background: #2E1C11; animation: stamp .6s cubic-bezier(.2,1.4,.4,1) both; }
.stamp .big { font-size: 3.2rem; }
@keyframes stamp { from { opacity: 0; transform: scale(1.6) rotate(-6deg); } to { opacity: 1; transform: none; } }
.empty { text-align: center; padding: 2.4rem 1rem; color: #C9A57A; border: 1px dashed #5a3a24; border-radius: 18px; }
.status { display: inline-block; padding: .2rem .7rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }
.status.on { background: #3d4a22; color: #cfe3a0; }
.status.off { background: #4a2f1f; color: #E8C79A; }

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ data layer
def inr(x):
    return f"₹{x:,.2f}"


def pkey(seller_id, product):
    return f"{seller_id}::{product.lower()}"


@st.cache_data(ttl=8, show_spinner=False)
def api_online(url):
    try:
        return requests.get(f"{url}/home", timeout=0.8).ok
    except requests.RequestException:
        return False


def read_local():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def write_local(products):
    DATA_FILE.write_text(json.dumps(products, indent=4))


def refresh_products():
    url = st.session_state.api_url
    products, source = None, "data.json"
    if api_online(url):
        try:
            products = requests.get(f"{url}/products", timeout=3).json()
            source = "API"
        except Exception:
            products = None
    if products is None:
        products = read_local()
    for p in read_local():  # remember seller names (the API DTO does not carry them)
        if p.get("seller"):
            st.session_state.seller_names[p["seller_id"]] = p["seller"]
    for p in products:
        if p.get("seller"):
            st.session_state.seller_names[p["seller_id"]] = p["seller"]
    st.session_state.products = products
    st.session_state.source = source


def seller_name(seller_id):
    return st.session_state.seller_names.get(seller_id, f"Seller {seller_id}")


def stock_left(p):
    return max(0, p["stock"] - st.session_state.sold.get(pkey(p["seller_id"], p["product"]), 0))


def product_map():
    return {pkey(p["seller_id"], p["product"]): p for p in st.session_state.products}


def emoji_for(p):
    text = f"{p['product']} {p.get('category', '')}".lower()
    for words, e in [
        (("wheat",), "🌾"), (("mustard",), "🌼"), (("rice", "paddy"), "🍚"), (("urea", "fertil"), "🧪"),
        (("pest", "insect"), "🐛"), (("seed",), "🌱"), (("tractor", "tool", "equip"), "🚜"),
        (("water", "irrig"), "💧"), (("organic", "compost"), "🍂"),
    ]:
        if any(w in text for w in words):
            return e
    return "🛒"


def tile_style(p, cats):
    i = cats.index(p.get("category", "Other")) % len(BROWNS) if p.get("category", "Other") in cats else 0
    a, b = BROWNS[i], BROWNS[(i + 3) % len(BROWNS)]
    return f"background: linear-gradient(135deg, {a}, {b});"


# ------------------------------------------------------------------ cart logic
def add_to_cart(k):
    p = product_map().get(k)
    if not p:
        return
    have = st.session_state.cart.get(k, 0)
    if have >= stock_left(p):
        st.toast(f"Only {stock_left(p)} of {p['product']} in stock.", icon="⚠️")
        return
    st.session_state.cart[k] = have + 1
    st.session_state["pop"] += 1
    st.toast(f"{p['product']} added to cart", icon="🛒")


def change_qty(k, delta):
    p = product_map().get(k)
    if not p:
        return
    new = st.session_state.cart.get(k, 0) + delta
    if new > stock_left(p):
        st.toast(f"Stock limit reached for {p['product']}.", icon="⚠️")
        return
    if new <= 0:
        st.session_state.cart.pop(k, None)
    else:
        st.session_state.cart[k] = new


def remove_item(k):
    st.session_state.cart.pop(k, None)


def go(page):
    st.session_state.page = page


def sanitize_cart():
    pm = product_map()
    for k in list(st.session_state.cart):
        if k not in pm or stock_left(pm[k]) <= 0:
            st.session_state.cart.pop(k)
        else:
            st.session_state.cart[k] = min(st.session_state.cart[k], stock_left(pm[k]))


def cart_totals():
    pm = product_map()
    n = sum(st.session_state.cart.values())
    sub = sum(pm[k]["price"] * q for k, q in st.session_state.cart.items() if k in pm)
    return n, sub


def calculate_order():
    """Seller-wise grouping, subtotal, 18% GST, final total (API first, local fallback)."""
    pm = product_map()
    items = [
        {"seller_id": pm[k]["seller_id"], "product": pm[k]["product"], "quantity": q}
        for k, q in st.session_state.cart.items()
    ]
    url = st.session_state.api_url
    if api_online(url):
        try:
            r = requests.post(f"{url}/order_summary", json={"items": items}, timeout=4)
            if r.ok:
                return r.json(), "API"
            st.error(r.json().get("detail", "The API rejected this order."))
            return None, "API"
        except requests.RequestException:
            pass
    sellers, subtotal = {}, 0
    for it in items:
        p = pm[pkey(it["seller_id"], it["product"])]
        line = p["price"] * it["quantity"]
        g = sellers.setdefault(
            p["seller_id"],
            {"seller_id": p["seller_id"], "seller": seller_name(p["seller_id"]), "products": [], "subtotal": 0},
        )
        g["products"].append({"product": p["product"], "price": p["price"], "quantity": it["quantity"], "total": line})
        g["subtotal"] += line
        subtotal += line
    gst = round(subtotal * GST_RATE, 2)
    return {
        "status": "success",
        "seller_wise_orders": list(sellers.values()),
        "order_summary": {
            "subtotal": subtotal, "gst_percentage": 18, "gst_amount": gst,
            "final_order_total": round(subtotal + gst, 2),
        },
    }, "local"


# ------------------------------------------------------------------ session
ss = st.session_state
ss.setdefault("api_url", DEFAULT_API)
ss.setdefault("cart", {})
ss.setdefault("sold", {})
ss.setdefault("orders", [])
ss.setdefault("last_order", None)
ss.setdefault("pop", 0)
ss.setdefault("seller_names", {})
ss.setdefault("page", "Marketplace")
if "products" not in ss:
    refresh_products()
sanitize_cart()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="brand">🌾 Bharat AgroLink</div><div class="brand-sub">Farm inputs, straight from sellers</div>', unsafe_allow_html=True)
    st.radio("Go to", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    n_items, sub_now = cart_totals()
    st.markdown(f"**Cart:** {n_items} item(s) · {inr(sub_now)}")
    st.divider()
    with st.expander("Connection", expanded=False):
        st.text_input("FastAPI base URL", key="api_url")
        online = api_online(ss.api_url)
        st.markdown(
            f'<span class="status {"on" if online else "off"}">{"API connected" if online else "Using data.json"}</span>',
            unsafe_allow_html=True,
        )
        if st.button("Reload products", width="stretch"):
            api_online.clear()
            refresh_products()
            st.rerun()

# ------------------------------------------------------------------ hero
products = ss.products
cats = sorted({p.get("category", "Other") for p in products})
pop_cls = "pop-a" if ss["pop"] % 2 == 0 else "pop-b"
n_items, sub_now = cart_totals()
st.markdown(
    f"""
<div class="hero"><div class="furrows"></div>
<div class="hero-inner"><h1>Bharat AgroLink</h1>
<p>Compare seeds, fertilizers and farm inputs across sellers. Prices are in rupees and GST is shown before you order.</p></div>
<div class="cart-pill {pop_cls}">🛒 {n_items} item(s) &nbsp;|&nbsp; {inr(sub_now)}</div></div>
<div class="ticker"><span>{'&nbsp;&nbsp;&nbsp;&nbsp;🌱&nbsp;&nbsp;&nbsp;&nbsp;'.join(cats) if cats else 'Fresh stock from verified sellers'}&nbsp;&nbsp;&nbsp;&nbsp;🌱&nbsp;&nbsp;&nbsp;&nbsp;GST 18% shown on every order</span></div>
""",
    unsafe_allow_html=True,
)

page = ss.page

# ------------------------------------------------------------------ marketplace
if page == "Marketplace":
    st.subheader("Products")
    f1, f2, f3, f4 = st.columns([3, 2, 2, 1.6])
    q = f1.text_input("Search", placeholder="Search products or sellers", label_visibility="collapsed")
    cat = f2.selectbox("Category", ["All categories"] + cats, label_visibility="collapsed")
    sort = f3.selectbox("Sort", ["Name A-Z", "Price: low to high", "Price: high to low", "Most stock"], label_visibility="collapsed")
    only_in = f4.toggle("In stock only")

    items = list(products)
    if cat != "All categories":
        items = [p for p in items if p.get("category", "Other").lower() == cat.lower()]
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p["product"].lower() or ql in seller_name(p["seller_id"]).lower()]
    if only_in:
        items = [p for p in items if stock_left(p) > 0]
    items.sort(key={
        "Name A-Z": lambda p: p["product"].lower(),
        "Price: low to high": lambda p: p["price"],
        "Price: high to low": lambda p: -p["price"],
        "Most stock": lambda p: -stock_left(p),
    }[sort])

    st.caption(f"{len(items)} product(s) · data from {ss.source}")
    if not items:
        st.markdown('<div class="empty">No products match these filters. Clear the search or pick another category.</div>', unsafe_allow_html=True)

    max_stock = max([p["stock"] for p in products] + [1])
    cols = st.columns(3)
    for i, p in enumerate(items):
        k = pkey(p["seller_id"], p["product"])
        left = stock_left(p)
        in_cart = ss.cart.get(k, 0)
        pct = min(100, int(left / max_stock * 100)) if left else 0
        if left == 0:
            note, cls = "Out of stock", "out"
        elif left <= 5:
            note, cls = f"Only {left} left", "low"
        else:
            note, cls = f"{left} in stock", ""
        img = p.get("image")
        inner = emoji_for(p)
        style = tile_style(p, cats)
        if img:
            style = f"background-image: url('{img}'); background-size: cover;"
            inner = ""
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(
                    f"""<div class="p-img {'oos' if left == 0 else ''}" style="{style}">{inner}</div>
<span class="chip">{p.get('category', 'Other')}</span>
<div class="p-name">{p['product']}</div>
<div class="p-seller">Sold by {seller_name(p['seller_id'])}</div>
<div class="p-price">{inr(p['price'])}</div>
<div class="bar"><i style="width:{pct}%"></i></div>
<div class="stock-note {cls}">{note}{f' · {in_cart} in your cart' if in_cart else ''}</div>""",
                    unsafe_allow_html=True,
                )
                if left == 0:
                    label, dis = "Out of stock", True
                elif in_cart >= left:
                    label, dis = "Maximum in cart", True
                else:
                    label, dis = "Add to cart", False
                st.button(label, key=f"add_{k}", disabled=dis, on_click=add_to_cart, args=(k,), width="stretch")

# ------------------------------------------------------------------ cart
elif page == "Cart":
    st.subheader("Your cart")
    pm = product_map()
    if not ss.cart:
        st.markdown('<div class="empty">Your cart is empty. Add seeds, fertilizers or other inputs from the marketplace.</div>', unsafe_allow_html=True)
        st.button("Browse products", on_click=go, args=("Marketplace",))
    else:
        left_col, right_col = st.columns([2.2, 1])
        with left_col:
            for k, qty in list(ss.cart.items()):
                p = pm[k]
                avail = stock_left(p)
                with st.container(border=True):
                    c1, c2, c3, c4, c5, c6 = st.columns([0.7, 2.6, 0.7, 0.8, 0.7, 1.5])
                    c1.markdown(f"<div style='font-size:2.2rem'>{emoji_for(p)}</div>", unsafe_allow_html=True)
                    c2.markdown(
                        f"<div class='p-name'>{p['product']}</div><div class='p-seller'>{seller_name(p['seller_id'])} · {inr(p['price'])} each · {avail} available</div>",
                        unsafe_allow_html=True,
                    )
                    c3.button("−", key=f"dec_{k}", on_click=change_qty, args=(k, -1), width="stretch")
                    c4.markdown(f"<div style='text-align:center;font-size:1.3rem;font-weight:700;padding-top:.2rem'>{qty}</div>", unsafe_allow_html=True)
                    c5.button("+", key=f"inc_{k}", on_click=change_qty, args=(k, 1), disabled=qty >= avail, width="stretch")
                    c6.markdown(f"<div style='text-align:right;font-weight:700;color:#F0B876;font-size:1.1rem'>{inr(p['price'] * qty)}</div>", unsafe_allow_html=True)
                    st.button("Remove", key=f"rm_{k}", on_click=remove_item, args=(k,))
        with right_col:
            n, sub = cart_totals()
            gst = round(sub * GST_RATE, 2)
            st.markdown(
                f"""<div class="totals"><div class="row"><span>Items</span><span>{n}</span></div>
<div class="row"><span>Subtotal</span><span>{inr(sub)}</span></div>
<div class="row"><span>GST (18%)</span><span>{inr(gst)}</span></div>
<div class="row final"><span>Total</span><span>{inr(sub + gst)}</span></div></div>""",
                unsafe_allow_html=True,
            )
            st.write("")
            st.button("Review order", type="primary", on_click=go, args=("Order summary",), width="stretch")
            st.button("Clear cart", on_click=lambda: ss.cart.clear(), width="stretch")

# ------------------------------------------------------------------ order summary
elif page == "Order summary":
    st.subheader("Order summary")
    if not ss.cart:
        if ss.last_order:
            o = ss.last_order
            st.markdown(
                f"""<div class="stamp"><div class="big">✅</div><h2>Order placed</h2>
<p>Order <b>{o['id']}</b> · {inr(o['total'])} paid across {o['sellers']} seller(s)</p></div>""",
                unsafe_allow_html=True,
            )
            st.write("")
            st.button("Keep shopping", on_click=go, args=("Marketplace",))
        else:
            st.markdown('<div class="empty">Nothing to summarise yet. Add products to your cart first.</div>', unsafe_allow_html=True)
            st.button("Browse products", on_click=go, args=("Marketplace",))
    else:
        data, how = calculate_order()
        if data:
            summ = data["order_summary"]
            l, r = st.columns([2.2, 1])
            with l:
                for g in data["seller_wise_orders"]:
                    rows = "".join(
                        f"<tr><td>{x['product']}</td><td class='r'>{inr(x['price'])}</td><td class='r'>{x['quantity']}</td><td class='r'>{inr(x['total'])}</td></tr>"
                        for x in g["products"]
                    )
                    st.markdown(
                        f"""<div class="seller-card"><h4>🏪 {g.get('seller') or seller_name(g['seller_id'])}</h4>
<table class="ord"><tr><th>Product</th><th class="r">Price</th><th class="r">Qty</th><th class="r">Total</th></tr>{rows}</table>
<div class="sub-row"><span>Seller subtotal</span><span>{inr(g['subtotal'])}</span></div></div>""",
                        unsafe_allow_html=True,
                    )
            with r:
                st.markdown(
                    f"""<div class="totals"><div class="row"><span>Subtotal</span><span>{inr(summ['subtotal'])}</span></div>
<div class="row"><span>GST ({summ['gst_percentage']}%)</span><span>{inr(summ['gst_amount'])}</span></div>
<div class="row final"><span>Final total</span><span>{inr(summ['final_order_total'])}</span></div></div>""",
                    unsafe_allow_html=True,
                )
                st.caption(f"Calculated by {'the FastAPI backend' if how == 'API' else 'the local engine (API offline)'}")
                st.write("")

                def confirm():
                    oid = "AGL-" + uuid.uuid4().hex[:6].upper()
                    for k, qn in ss.cart.items():
                        ss.sold[k] = ss.sold.get(k, 0) + qn
                    ss.orders.append({"id": oid, "data": data})
                    ss.last_order = {"id": oid, "total": summ["final_order_total"], "sellers": len(data["seller_wise_orders"])}
                    ss.cart.clear()

                st.button("Place order", type="primary", on_click=confirm, width="stretch")
                st.button("Back to cart", on_click=go, args=("Cart",), width="stretch")

# ------------------------------------------------------------------ dashboard
elif page == "Dashboard":
    st.subheader("Marketplace dashboard")
    df = pd.DataFrame(products)
    if df.empty:
        st.markdown('<div class="empty">No products loaded yet. Add some from the Seller desk.</div>', unsafe_allow_html=True)
    else:
        df["category"] = df.get("category", "Other")
        df["seller_name"] = df["seller_id"].map(seller_name)
        df["left"] = [stock_left(p) for p in products]
        df["value"] = df["price"] * df["left"]
        revenue = sum(o["data"]["order_summary"]["final_order_total"] for o in ss.orders)
        k = st.columns(5)
        for col, (val, lab) in zip(k, [
            (len(df), "Listings"), (df["seller_id"].nunique(), "Sellers"),
            (inr(df["value"].sum()), "Inventory value"), (int((df["left"] == 0).sum()), "Out of stock"),
            (inr(revenue), "Orders this session"),
        ]):
            col.markdown(f'<div class="kpi"><div class="v">{val}</div><div class="l">{lab}</div></div>', unsafe_allow_html=True)
        st.write("")

        def style(ch):
            return (ch.configure(background="transparent")
                    .configure_axis(labelColor="#E8D5BC", titleColor="#C9A57A", gridColor="#43291a", domainColor="#6b452c")
                    .configure_legend(labelColor="#E8D5BC", titleColor="#C9A57A")
                    .configure_view(strokeWidth=0))

        c1, c2 = st.columns(2)
        by_cat = df.groupby("category", as_index=False).agg(units=("left", "sum"))
        c1.markdown("**Units in stock by category**")
        c1.altair_chart(style(alt.Chart(by_cat).mark_bar(cornerRadiusEnd=6, color="#D39A5B").encode(
            x=alt.X("units:Q", title="Units"), y=alt.Y("category:N", sort="-x", title=None))), width="stretch")
        by_seller = df.groupby("seller_name", as_index=False).agg(value=("value", "sum"))
        c2.markdown("**Inventory value by seller (₹)**")
        c2.altair_chart(style(alt.Chart(by_seller).mark_bar(cornerRadiusEnd=6, color="#A8693A").encode(
            x=alt.X("seller_name:N", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("value:Q", title="₹"))), width="stretch")

        c3, c4 = st.columns(2)
        share = df.groupby("category", as_index=False).agg(count=("product", "count"))
        c3.markdown("**Category share of listings**")
        c3.altair_chart(style(alt.Chart(share).mark_arc(innerRadius=55).encode(
            theta="count:Q", color=alt.Color("category:N", scale=alt.Scale(range=BROWNS)))), width="stretch")
        c4.markdown("**Stock health**")
        c4.dataframe(
            df[["product", "seller_name", "category", "price", "left"]].rename(columns={"seller_name": "seller", "left": "stock"}),
            hide_index=True, width="stretch",
            column_config={
                "price": st.column_config.NumberColumn("Price", format="₹%d"),
                "stock": st.column_config.ProgressColumn("Stock", min_value=0, max_value=int(max(df["stock"].max(), 1)), format="%d"),
            },
        )

    st.markdown("**Order history (this session)**")
    if not ss.orders:
        st.markdown('<div class="empty">No orders yet. Orders you place appear here.</div>', unsafe_allow_html=True)
    for o in reversed(ss.orders):
        s = o["data"]["order_summary"]
        with st.expander(f"{o['id']} · {inr(s['final_order_total'])}"):
            for g in o["data"]["seller_wise_orders"]:
                st.write(f"**{g.get('seller') or seller_name(g['seller_id'])}** · subtotal {inr(g['subtotal'])}")
                st.dataframe(pd.DataFrame(g["products"]), hide_index=True, width="stretch")
            st.caption(f"GST {s['gst_percentage']}%: {inr(s['gst_amount'])}")

# ------------------------------------------------------------------ seller desk
else:
    st.subheader("Seller desk")
    t1, t2 = st.tabs(["Add product", "Update product"])
    online = api_online(ss.api_url)

    with t1:
        with st.form("add_form", clear_on_submit=True):
            a, b = st.columns(2)
            sid = a.number_input("Seller ID", min_value=1, step=1)
            sname = b.text_input("Seller name", placeholder="e.g. Green Fields Traders")
            pname = a.text_input("Product name")
            pcat = b.text_input("Category", value="Seeds")
            price = a.number_input("Price (₹)", min_value=0, step=10)
            stock = b.number_input("Stock (units)", min_value=0, step=1)
            if st.form_submit_button("Add product", type="primary"):
                body = {"seller_id": int(sid), "product": pname.strip(), "price": int(price), "stock": int(stock), "category": pcat.strip() or "Other"}
                if not body["product"]:
                    st.error("Enter a product name.")
                elif pkey(body["seller_id"], body["product"]) in product_map():
                    st.error("This seller already lists that product. Use Update product instead.")
                else:
                    if sname.strip():
                        ss.seller_names[body["seller_id"]] = sname.strip()
                    ok = False
                    if online:
                        r = requests.post(f"{ss.api_url}/create_prod", json=body, timeout=4)
                        ok = r.ok
                        if not ok:
                            st.error(r.json().get("detail", "The API rejected this product."))
                    else:
                        local = read_local()
                        local.append({**body, "seller": seller_name(body["seller_id"])})
                        write_local(local)
                        ok = True
                    if ok:
                        refresh_products()
                        st.success(f"{body['product']} added.")
                        st.rerun()

    with t2:
        if not products:
            st.markdown('<div class="empty">No products to update yet.</div>', unsafe_allow_html=True)
        else:
            labels = {pkey(p["seller_id"], p["product"]): f"{p['product']} · {seller_name(p['seller_id'])}" for p in products}
            pick = st.selectbox("Product", list(labels), format_func=labels.get)
            cur = product_map()[pick]
            with st.form("upd_form"):
                a, b, c = st.columns(3)
                nprice = a.number_input("Price (₹)", min_value=0, step=10, value=int(cur["price"]))
                nstock = b.number_input("Stock (units)", min_value=0, step=1, value=int(cur["stock"]))
                ncat = c.text_input("Category", value=cur.get("category", "Other"))
                if st.form_submit_button("Save changes", type="primary"):
                    body = {"seller_id": cur["seller_id"], "product": cur["product"], "price": int(nprice), "stock": int(nstock), "category": ncat or "Other"}
                    ok = False
                    if online:
                        r = requests.put(f"{ss.api_url}/update_prod/{cur['seller_id']}/{cur['product']}", json=body, timeout=4)
                        ok = r.ok
                        if not ok:
                            st.error(r.json().get("detail", "The API could not update this product."))
                    else:
                        local = read_local()
                        for i, p in enumerate(local):
                            if p["seller_id"] == cur["seller_id"] and p["product"].lower() == cur["product"].lower():
                                local[i] = {**p, **body}
                        write_local(local)
                        ok = True
                    if ok:
                        refresh_products()
                        st.success("Product updated.")
                        st.rerun()