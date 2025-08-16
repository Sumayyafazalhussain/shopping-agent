
# import chainlit as cl
# import json
# import os
# import re
# import sqlite3
# import threading
# import uuid
# from datetime import datetime

# # --- Static files via FastAPI (serve local images like /static/tshirt.jpg) ---
# # pip install fastapi uvicorn
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# import uvicorn

# STATIC_DIR = "static"
# STATIC_HOST = "0.0.0.0"
# STATIC_PORT = 8000

# # Make sure static folder exists
# os.makedirs(STATIC_DIR, exist_ok=True)

# _fastapi_started = False
# def _run_fastapi():
#     app = FastAPI()
#     app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
#     uvicorn.run(app, host=STATIC_HOST, port=STATIC_PORT, log_level="warning")

# def start_static_server_once():
#     global _fastapi_started
#     if not _fastapi_started:
#         t = threading.Thread(target=_run_fastapi, daemon=True)
#         t.start()
#         _fastapi_started = True

# # -------------------------
# # Config / Files / DB Init
# # -------------------------
# PRODUCTS_FILE = "products.json"
# DB_FILE = "shop.db"

# # Load products
# if os.path.exists(PRODUCTS_FILE):
#     with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
#         PRODUCTS = json.load(f)
# else:
#     PRODUCTS = []
#     print("⚠️ products.json not found! Using empty catalog.")

# # Ensure each product has category and tags keys (avoid KeyError)
# for p in PRODUCTS:
#     p.setdefault("category", "general")
#     p.setdefault("tags", [])
#     # TIP: for local files, set p["image"] like "http://127.0.0.1:8000/static/tshirt.jpg"

# # Initialize SQLite DB (orders)
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id TEXT PRIMARY KEY,
#             name TEXT,
#             address TEXT,
#             phone TEXT,
#             total REAL,
#             items_json TEXT,
#             created_at TEXT
#         )
#         """
#     )
#     conn.commit()
#     conn.close()

# init_db()

# # -------------------------
# # Utility Functions
# # -------------------------
# def search_products(query):
#     """
#     Smart search that accepts:
#       - keywords
#       - category:men
#       - price<50 or price>20 or price<=100 etc.
#     Returns list of product dicts.
#     """
#     q = query.strip().lower()

#     # extract category
#     category_match = re.search(r"category:([a-z0-9_-]+)", q)
#     category = category_match.group(1) if category_match else None
#     if category:
#         q = re.sub(r"category:[a-z0-9_-]+", "", q)

#     # extract price filters
#     price_filters = re.findall(r"price\s*(<=|>=|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)", q)
#     # also handle "<2000" or "under 2000" patterns
#     under_match = re.search(r"(under|less than|below)\s*([0-9]+)", q)
#     if under_match:
#         price_filters.append(("<", under_match.group(2)))

#     greater_match = re.search(r"(over|above|more than)\s*([0-9]+)", q)
#     if greater_match:
#         price_filters.append((">", greater_match.group(2)))

#     # clean query (remove price words)
#     q_clean = re.sub(r"price\s*(<=|>=|<|>|=)\s*[0-9]+(?:\.[0-9]+)?", "", q)
#     q_clean = re.sub(r"(under|less than|below|over|above|more than)\s*[0-9]+", "", q_clean)
#     q_clean = q_clean.strip()

#     results = []
#     for p in PRODUCTS:
#         name_desc = f"{p.get('name','')} {p.get('desc','')}".lower()

#         # basic keyword match
#         if q_clean:
#             if q_clean not in name_desc and not any(q_clean in t.lower() for t in p.get("tags", [])):
#                 continue

#         # category filter
#         if category and category != p.get("category", "").lower():
#             continue

#         # price filters
#         price_ok = True
#         for op, num in price_filters:
#             try:
#                 numf = float(num)
#                 price = float(p.get("price", 0))
#                 if op == "<" and not (price < numf): price_ok = False
#                 elif op == "<=" and not (price <= numf): price_ok = False
#                 elif op == ">" and not (price > numf): price_ok = False
#                 elif op == ">=" and not (price >= numf): price_ok = False
#                 elif op == "=" and not (price == numf): price_ok = False
#             except:
#                 price_ok = False
#         if not price_ok:
#             continue

#         results.append(p)

#     return results

# def get_cart():
#     return cl.user_session.get("cart", [])

# def save_cart(cart):
#     cl.user_session.set("cart", cart)

# def add_product_to_cart(pid, qty=1):
#     product = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not product:
#         return False, "Product not found."

#     cart = get_cart()
#     for item in cart:
#         if item["id"] == pid:
#             item["qty"] += qty
#             break
#     else:
#         cart.append({
#             "id": product["id"],
#             "name": product["name"],
#             "price": product["price"],
#             "qty": qty
#         })
#     save_cart(cart)
#     return True, product

# def remove_from_cart(pid):
#     cart = get_cart()
#     new_cart = [it for it in cart if it["id"] != pid]
#     save_cart(new_cart)
#     return len(new_cart) != len(cart)

# def clear_cart():
#     save_cart([])

# def cart_total(cart=None):
#     c = cart if cart is not None else get_cart()
#     return sum(item["price"] * item["qty"] for item in c)

# def recommend_for_cart():
#     """
#     Simple rule-based recommendations:
#     - If cart has 'sneakers' recommend 'jeans' or 't-shirt'
#     - Otherwise recommend cheapest 3 not in cart
#     """
#     cart = get_cart()
#     names = " ".join([it["name"].lower() for it in cart])
#     recs = []

#     def add_by_keyword(kw, limit=2):
#         for p in PRODUCTS:
#             if kw in p["name"].lower() and p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#                 if len(recs) >= limit:
#                     break

#     if "sneaker" in names or "sneakers" in names:
#         add_by_keyword("jeans")
#         add_by_keyword("t-shirt")
#     elif "jacket" in names or "hoodie" in names:
#         add_by_keyword("sneakers")
#         add_by_keyword("t-shirt")
#     else:
#         for p in sorted(PRODUCTS, key=lambda x: x.get("price", 0)):
#             if p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#             if len(recs) >= 3:
#                 break

#     seen = set()
#     dedup = []
#     for r in recs:
#         if r["id"] not in seen:
#             dedup.append(r)
#             seen.add(r["id"])
#         if len(dedup) >= 3:
#             break
#     return dedup

# def save_order(name, address, phone, cart):
#     order_id = str(uuid.uuid4())[:8]
#     total = cart_total(cart)
#     items_json = json.dumps(cart, ensure_ascii=False)
#     created_at = datetime.utcnow().isoformat()
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         "INSERT INTO orders (id, name, address, phone, total, items_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
#         (order_id, name, address, phone, total, items_json, created_at)
#     )
#     conn.commit()
#     conn.close()
#     return order_id, total

# # -------------------------
# # UI / Chat Handlers
# # -------------------------
# @cl.on_chat_start
# async def start():
#     # ensure static server is running (for local images)
#     start_static_server_once()

#     welcome = (
#         "👋 **Welcome to ShopBot Pro!**\n\n"
#         "Try natural queries like:\n"
#         " - `search sneakers`\n"
#         " - `search jackets category:men price<100`\n"
#         " - `search shirts under 50`\n\n"
#         "Commands:\n"
#         " - `show cart` — view cart\n"
#         " - `remove <product id>` — remove item\n"
#         " - `clear cart` — empty cart\n"
#         " - `checkout` — start checkout\n\n"
       
#     )
#     await cl.Message(content=welcome).send()

# @cl.on_message
# async def handle_message(message: cl.Message):
#     text = (message.content or "").strip()

#     # If we are in a checkout flow, route to checkout handler
#     if cl.user_session.get("checkout_state"):
#         await handle_checkout_flow(text)
#         return

#     low = text.lower()

#     # search command (smart) — send ONE message PER product (like your working demo)
#     if low.startswith("search"):
#         query = text.replace("search", "", 1).strip()
#         if not query:
#             await cl.Message(content="Type something to search, e.g. `search sneakers`").send()
#             return

#         results = search_products(query)
#         if not results:
#             await cl.Message(content=f"❌ No products found for `{query}`.").send()
#             return

#         # Send each product as its own message with image + Add/Details actions
#         header = f"**Search results for:** `{query}`\nShowing {min(len(results), 8)} of {len(results)}"
#         await cl.Message(content=header).send()

#         for p in results[:8]:
#             img = cl.Image(url=p["image"], name=p["name"], display="inline")
#             actions = [
#                 cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]}),
#                 cl.Action(name="product_detail", label="Details", payload={"id": p["id"]})
#             ]
#             content = (
#                 f"**{p['name']}**\n"
#                 f"{p.get('desc','')}\n\n"
#                 f"Category: `{p.get('category','')}`\n"
#                 f"💵 Price: **${p['price']}**"
#             )
#             await cl.Message(content=content, elements=[img], actions=actions).send()
#         return

#     # view cart
#     if low in ("show cart", "view cart", "cart"):
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Try `search sneakers`.").send()
#             return

#         lines = []
#         for it in cart:
#             lines.append(f"`{it['id']}` — **{it['name']}** x{it['qty']} = ${it['price']*it['qty']:.2f}")
#         total = cart_total(cart)

#         elements = [
#             cl.Action(name="checkout", label="✅ Checkout", payload={}),
#             cl.Action(name="clear_cart", label="🗑 Clear Cart", payload={})
#         ]

#         # show recommendations as well (as quick adds)
#         recs = recommend_for_cart()
#         rec_section = ""
#         if recs:
#             rec_lines = [f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)" for r in recs]
#             rec_section = "\n\n**You might also like:**\n" + "\n".join(rec_lines)
#             for r in recs:
#                 elements.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))

#         await cl.Message(
#             content=f"**🛒 Your Cart:**\n\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}" + rec_section,
#             actions=elements
#         ).send()
#         return

#     # remove single item by command "remove p3"
#     if low.startswith("remove"):
#         pid = low.replace("remove", "", 1).strip()
#         if not pid:
#             await cl.Message(content="Usage: `remove <product id>` (e.g. `remove p3`)").send()
#             return
#         ok = remove_from_cart(pid)
#         if ok:
#             await cl.Message(content=f"✅ Removed `{pid}` from cart.").send()
#         else:
#             await cl.Message(content=f"❌ `{pid}` not found in your cart.").send()
#         return

#     # clear cart
#     if low in ("clear cart", "clear_cart"):
#         clear_cart()
#         await cl.Message(content="🗑 Cart cleared.").send()
#         return

#     # start checkout
#     if low == "checkout":
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Add items before checkout.").send()
#             return

#         cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#         await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#         return

#     # unknown command fallback
#     await cl.Message(content="❓ I didn't understand. Try `search <term>` or `show cart`.").send()

# # -------------------------
# # Action callbacks
# # -------------------------
# @cl.action_callback("add_to_cart")
# async def on_add_to_cart(action):
#     pid = action.payload.get("id")
#     ok, result = add_product_to_cart(pid)
#     if not ok:
#         await cl.Message(content=str(result)).send()
#         await action.remove()
#         return

#     product = result
#     await cl.Message(content=f"✅ Added **{product['name']}** to cart.").send()
#     await action.remove()

# @cl.action_callback("product_detail")
# async def on_product_detail(action):
#     pid = action.payload.get("id")
#     p = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not p:
#         await cl.Message(content="Product not found.").send()
#         await action.remove()
#         return

#     img = cl.Image(url=p["image"], name=p["name"], display="inline")
#     actions = [cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]})]
#     content = (
#         f"**{p['name']}**\n\n{p.get('desc','')}\n\n"
#         f"Category: `{p.get('category','')}`\n"
#         f"Price: **${p['price']}**"
#     )
#     await cl.Message(content=content, elements=[img], actions=actions).send()
#     await action.remove()

# @cl.action_callback("clear_cart")
# async def on_clear_cart(action):
#     clear_cart()
#     await cl.Message(content="🗑 Cart cleared.").send()
#     await action.remove()

# @cl.action_callback("checkout")
# async def on_checkout(action):
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         await action.remove()
#         return

#     cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#     await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#     await action.remove()

# # -------------------------
# # Checkout multi-step flow
# # -------------------------
# async def handle_checkout_flow(text):
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing. Type `checkout` to start.").send()
#         return

#     step = state.get("step")
#     data = state.get("data", {})

#     if step == "name":
#         name = text.strip()
#         if not name or len(name) < 2:
#             await cl.Message(content="Please provide a valid full name.").send()
#             return
#         data["name"] = name
#         state["step"] = "address"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Got it. Now enter your **shipping address**:").send()
#         return

#     if step == "address":
#         address = text.strip()
#         if not address or len(address) < 5:
#             await cl.Message(content="Please provide a valid address (street, city, etc.).").send()
#             return
#         data["address"] = address
#         state["step"] = "phone"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Great. Finally, please provide your **phone number**:").send()
#         return

#     if step == "phone":
#         phone = text.strip()
#         digits = re.sub(r"\D", "", phone)
#         if len(digits) < 7:
#             await cl.Message(content="Please provide a valid phone number (at least 7 digits).").send()
#             return
#         data["phone"] = phone
#         state["step"] = "confirm"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)

#         cart = get_cart()
#         lines = [f"- {it['name']} x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
#         total = cart_total(cart)
#         summary = f"**Order summary:**\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}\n\n"
#         summary += f"**Ship to:** {data['name']}, {data['address']}, 📞 {data['phone']}\n\n"
#         summary += "Type `confirm` to place the order or `cancel` to abort."

#         elements = [
#             cl.Action(name="confirm_order", label="✅ Confirm", payload={}),
#             cl.Action(name="cancel_order", label="❌ Cancel", payload={})
#         ]
#         await cl.Message(content=summary, actions=elements).send()
#         return

#     if step == "confirm":
#         low = text.lower().strip()
#         if low == "confirm":
#             await finalize_order()
#         elif low == "cancel":
#             cl.user_session.set("checkout_state", None)
#             await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#         else:
#             await cl.Message(content="Type `confirm` to place order or `cancel` to abort.").send()
#         return

# @cl.action_callback("confirm_order")
# async def on_confirm_order(action):
#     await finalize_order()
#     await action.remove()

# @cl.action_callback("cancel_order")
# async def on_cancel_order(action):
#     cl.user_session.set("checkout_state", None)
#     await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#     await action.remove()

# async def finalize_order():
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing.").send()
#         return
#     data = state.get("data", {})
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         cl.user_session.set("checkout_state", None)
#         return

#     order_id, total = save_order(data["name"], data["address"], data["phone"], cart)
#     clear_cart()
#     cl.user_session.set("checkout_state", None)

#     await cl.Message(
#         content=(
#             f"🎉 **Order placed!**\n"
#             f"Order ID: `{order_id}`\n"
#             f"Total: ${total:.2f}\n"
#             f"We saved your order — we'll contact you at {data['phone']}."
#         ),
#         elements=[cl.Image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", name="Order Placed")]
#     ).send()

# # -------------------------
# # End of file
# # -------------------------


# import chainlit as cl
# import json
# import os
# import re
# import sqlite3
# import threading
# import uuid
# from datetime import datetime

# # --- Static files via FastAPI (serve local images like /static/tshirt.jpg) ---
# # pip install fastapi uvicorn
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# import uvicorn

# STATIC_DIR = "static"
# STATIC_HOST = "0.0.0.0"
# STATIC_PORT = 8000

# # Make sure static folder exists
# os.makedirs(STATIC_DIR, exist_ok=True)

# _fastapi_started = False
# def _run_fastapi():
#     app = FastAPI()
#     app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
#     uvicorn.run(app, host=STATIC_HOST, port=STATIC_PORT, log_level="warning")

# def start_static_server_once():
#     global _fastapi_started
#     if not _fastapi_started:
#         t = threading.Thread(target=_run_fastapi, daemon=True)
#         t.start()
#         _fastapi_started = True

# # -------------------------
# # Config / Files / DB Init
# # -------------------------
# PRODUCTS_FILE = "products.json"
# DB_FILE = "shop.db"

# # Phase-5 persistence files
# CART_FILE = "cart.json"
# WISHLIST_FILE = "wishlist.json"

# def _read_json(path, default_val):
#     try:
#         if os.path.exists(path):
#             with open(path, "r", encoding="utf-8") as f:
#                 return json.load(f)
#     except Exception as e:
#         print(f"⚠️ Failed reading {path}: {e}")
#     return default_val

# def _write_json(path, data):
#     try:
#         with open(path, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#     except Exception as e:
#         print(f"⚠️ Failed writing {path}: {e}")

# # Load products
# if os.path.exists(PRODUCTS_FILE):
#     with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
#         PRODUCTS = json.load(f)
# else:
#     PRODUCTS = []
#     print("⚠️ products.json not found! Using empty catalog.")

# # Ensure each product has category/tags keys & optional 'thumb'
# for p in PRODUCTS:
#     p.setdefault("category", "general")
#     p.setdefault("tags", [])
#     # Optional smaller preview image:
#     p.setdefault("thumb", p.get("image", ""))  # if 'thumb' missing, fallback to main image

# # Initialize SQLite DB (orders)
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id TEXT PRIMARY KEY,
#             name TEXT,
#             address TEXT,
#             phone TEXT,
#             total REAL,
#             items_json TEXT,
#             created_at TEXT
#         )
#         """
#     )
#     conn.commit()
#     conn.close()

# init_db()

# # -------------------------
# # Utility Functions
# # -------------------------
# def search_products(query):
#     """
#     Smart search that accepts:
#       - keywords
#       - category:men
#       - price<50 or price>20 or price<=100 etc.
#     Returns list of product dicts.
#     """
#     q = query.strip().lower()

#     # extract category
#     category_match = re.search(r"category:([a-z0-9_-]+)", q)
#     category = category_match.group(1) if category_match else None
#     if category:
#         q = re.sub(r"category:[a-z0-9_-]+", "", q)

#     # extract price filters
#     price_filters = re.findall(r"price\s*(<=|>=|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)", q)
#     # also handle "<2000" or "under 2000" patterns
#     under_match = re.search(r"(under|less than|below)\s*([0-9]+)", q)
#     if under_match:
#         price_filters.append(("<", under_match.group(2)))

#     greater_match = re.search(r"(over|above|more than)\s*([0-9]+)", q)
#     if greater_match:
#         price_filters.append((">", greater_match.group(2)))

#     # clean query (remove price words)
#     q_clean = re.sub(r"price\s*(<=|>=|<|>|=)\s*[0-9]+(?:\.[0-9]+)?", "", q)
#     q_clean = re.sub(r"(under|less than|below|over|above|more than)\s*[0-9]+", "", q_clean)
#     q_clean = q_clean.strip()

#     results = []
#     for p in PRODUCTS:
#         name_desc = f"{p.get('name','')} {p.get('desc','')}".lower()

#         # basic keyword match (also search in tags)
#         if q_clean:
#             if (q_clean not in name_desc) and (not any(q_clean in t.lower() for t in p.get("tags", []))):
#                 continue

#         # category filter
#         if category and category != p.get("category", "").lower():
#             continue

#         # price filters
#         price_ok = True
#         for op, num in price_filters:
#             try:
#                 numf = float(num)
#                 price = float(p.get("price", 0))
#                 if op == "<" and not (price < numf): price_ok = False
#                 elif op == "<=" and not (price <= numf): price_ok = False
#                 elif op == ">" and not (price > numf): price_ok = False
#                 elif op == ">=" and not (price >= numf): price_ok = False
#                 elif op == "=" and not (price == numf): price_ok = False
#             except:
#                 price_ok = False
#         if not price_ok:
#             continue

#         results.append(p)

#     return results

# # ------- Phase-5: Persisted session state helpers -------
# def _ensure_session_defaults():
#     cl.user_session.set("cart", cl.user_session.get("cart", []))
#     cl.user_session.set("wishlist", cl.user_session.get("wishlist", []))

# def _load_persisted_state_into_session():
#     cl.user_session.set("cart", _read_json(CART_FILE, []))
#     cl.user_session.set("wishlist", _read_json(WISHLIST_FILE, []))

# def _persist_session():
#     _write_json(CART_FILE, cl.user_session.get("cart", []))
#     _write_json(WISHLIST_FILE, cl.user_session.get("wishlist", []))

# # ------- Cart helpers -------
# def get_cart():
#     return cl.user_session.get("cart", [])

# def save_cart(cart):
#     cl.user_session.set("cart", cart)
#     _persist_session()

# def add_product_to_cart(pid, qty=1):
#     product = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not product:
#         return False, "Product not found."

#     cart = get_cart()
#     for item in cart:
#         if item["id"] == pid:
#             item["qty"] += qty
#             break
#     else:
#         cart.append({
#             "id": product["id"],
#             "name": product["name"],
#             "price": product["price"],
#             "qty": qty
#         })
#     save_cart(cart)
#     return True, product

# def remove_from_cart(pid):
#     cart = get_cart()
#     new_cart = [it for it in cart if it["id"] != pid]
#     save_cart(new_cart)
#     return len(new_cart) != len(cart)

# def clear_cart():
#     save_cart([])

# def cart_total(cart=None):
#     c = cart if cart is not None else get_cart()
#     return sum(item["price"] * item["qty"] for item in c)

# # ------- Wishlist helpers (Phase-5) -------
# def get_wishlist():
#     return cl.user_session.get("wishlist", [])

# def save_wishlist(wishlist):
#     cl.user_session.set("wishlist", wishlist)
#     _persist_session()

# def add_to_wishlist(pid):
#     product = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not product:
#         return False, "Product not found."

#     wishlist = get_wishlist()
#     if pid not in [w["id"] for w in wishlist]:
#         wishlist.append({
#             "id": product["id"],
#             "name": product["name"],
#             "price": product["price"]
#         })
#         save_wishlist(wishlist)
#     return True, product

# def remove_from_wishlist(pid):
#     wishlist = get_wishlist()
#     new_list = [w for w in wishlist if w["id"] != pid]
#     save_wishlist(new_list)
#     return len(new_list) != len(wishlist)

# def clear_wishlist():
#     save_wishlist([])

# # ------- Recommendations -------
# def recommend_for_cart():
#     """
#     Simple rule-based recommendations:
#     - If cart has 'sneakers' recommend 'jeans' or 't-shirt'
#     - Otherwise recommend cheapest 3 not in cart
#     """
#     cart = get_cart()
#     names = " ".join([it["name"].lower() for it in cart])
#     recs = []

#     def add_by_keyword(kw, limit=2):
#         for p in PRODUCTS:
#             if kw in p["name"].lower() and p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#                 if len(recs) >= limit:
#                     break

#     if "sneaker" in names or "sneakers" in names:
#         add_by_keyword("jeans")
#         add_by_keyword("t-shirt")
#     elif "jacket" in names or "hoodie" in names:
#         add_by_keyword("sneakers")
#         add_by_keyword("t-shirt")
#     else:
#         for p in sorted(PRODUCTS, key=lambda x: x.get("price", 0)):
#             if p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#             if len(recs) >= 3:
#                 break

#     seen = set()
#     dedup = []
#     for r in recs:
#         if r["id"] not in seen:
#             dedup.append(r)
#             seen.add(r["id"])
#         if len(dedup) >= 3:
#             break
#     return dedup

# def related_by_tags(product, limit=3):
#     """Return up to `limit` products sharing at least one tag with `product`."""
#     tags = set([t.lower() for t in product.get("tags", [])])
#     if not tags:
#         return []

#     rel = []
#     for p in PRODUCTS:
#         if p["id"] == product["id"]:
#             continue
#         if tags.intersection([t.lower() for t in p.get("tags", [])]):
#             rel.append(p)
#     # prioritize by number of shared tags, then price ascending
#     rel.sort(key=lambda x: (-len(tags.intersection([t.lower() for t in x.get("tags", [])])), x.get("price", 0)))
#     return rel[:limit]

# def save_order(name, address, phone, cart):
#     order_id = str(uuid.uuid4())[:8]
#     total = cart_total(cart)
#     items_json = json.dumps(cart, ensure_ascii=False)
#     created_at = datetime.utcnow().isoformat()
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         "INSERT INTO orders (id, name, address, phone, total, items_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
#         (order_id, name, address, phone, total, items_json, created_at)
#     )
#     conn.commit()
#     conn.close()
#     return order_id, total

# # -------------------------
# # UI / Chat Handlers
# # -------------------------
# @cl.on_chat_start
# async def start():
#     # static server (for local images)
#     start_static_server_once()
#     # Phase-5: load persisted state into this Chainlit session
#     _load_persisted_state_into_session()
#     _ensure_session_defaults()

#     welcome = (
#         "👋 **Welcome to ShopBot Pro (Phase 5)!**\n\n"
#         "Try:\n"
#         " - `search sneakers`\n"
#         " - `search jackets category:men price<100`\n"
#         " - `search shirts under 50`\n\n"
#         "**Cart commands:** `show cart`, `remove <id>`, `clear cart`, `checkout`\n"
#         "**Wishlist commands:** `show wishlist`, `remove wish <id>`, `clear wishlist`\n"
#         "You can also use buttons on each product card.\n"
#     )
#     await cl.Message(content=welcome).send()

# @cl.on_message
# async def handle_message(message: cl.Message):
#     text = (message.content or "").strip()

#     # If in checkout flow, route to checkout handler
#     if cl.user_session.get("checkout_state"):
#         await handle_checkout_flow(text)
#         return

#     low = text.lower()

#     # search command (smart) — one message per product
#     if low.startswith("search"):
#         query = text.replace("search", "", 1).strip()
#         if not query:
#             await cl.Message(content="Type something to search, e.g. `search sneakers`").send()
#             return

#         results = search_products(query)
#         if not results:
#             await cl.Message(content=f"❌ No products found for `{query}`.").send()
#             return

#         header = f"**Search results for:** `{query}`\nShowing {min(len(results), 8)} of {len(results)}"
#         await cl.Message(content=header).send()

#         for p in results[:8]:
#             # main product card
#             img = cl.Image(url=p["image"], name=p["name"], display="inline")
#             actions = [
#                 cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]}),
#                 cl.Action(name="add_to_wishlist", label="♡ Wishlist", payload={"id": p["id"]}),
#                 cl.Action(name="product_detail", label="Details", payload={"id": p["id"]}),
#             ]
#             content = (
#                 f"**{p['name']}**\n"
#                 f"{p.get('desc','')}\n\n"
#                 f"Category: `{p.get('category','')}`\n"
#                 f"💵 Price: **${p['price']}**"
#             )
#             await cl.Message(content=content, elements=[img], actions=actions).send()

#             # related mini-thumbs (by tags)
#             rel = related_by_tags(p, limit=3)
#             if rel:
#                 rel_elements = []
#                 rel_lines = []
#                 for r in rel:
#                     rel_elements.append(cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline"))
#                     rel_elements.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#                     rel_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#                 await cl.Message(
#                     content="**Related products:**\n" + "\n".join(rel_lines),
#                     elements=rel_elements
#                 ).send()
#         return

#     # view cart
#     if low in ("show cart", "view cart", "cart"):
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Try `search sneakers`.").send()
#             return

#         lines = [f"`{it['id']}` — **{it['name']}** x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
#         total = cart_total(cart)

#         actions = [
#             cl.Action(name="checkout", label="✅ Checkout", payload={}),
#             cl.Action(name="clear_cart", label="🗑 Clear Cart", payload={})
#         ]

#         # recs for cart (quick add + mini images)
#         recs = recommend_for_cart()
#         rec_section = ""
#         elements = []
#         if recs:
#             rec_lines = []
#             for r in recs:
#                 rec_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#                 elements.append(cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline"))
#                 actions.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#             rec_section = "\n\n**You might also like:**\n" + "\n".join(rec_lines)

#         await cl.Message(
#             content=f"**🛒 Your Cart:**\n\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}" + rec_section,
#             elements=elements,
#             actions=actions
#         ).send()
#         return

#     # wishlist views
#     if low in ("show wishlist", "wishlist"):
#         wl = get_wishlist()
#         if not wl:
#             await cl.Message(content="♡ Your wishlist is empty. Add items via the '♡ Wishlist' button.").send()
#             return
#         lines = [f"`{w['id']}` — **{w['name']}** — ${w['price']:.2f}" for w in wl]
#         actions = [cl.Action(name="clear_wishlist", label="🗑 Clear Wishlist", payload={})]
#         # also let user quickly add wishlist items to cart
#         for w in wl:
#             actions.append(cl.Action(name="add_to_cart", label=f"Add {w['name']} to cart", payload={"id": w["id"]}))
#         await cl.Message(content="**♡ Your Wishlist:**\n\n" + "\n".join(lines), actions=actions).send()
#         return

#     # remove single item by command "remove p3"
#     if low.startswith("remove"):
#         # two patterns: "remove p3" (cart) or "remove wish p3"
#         if low.startswith("remove wish"):
#             pid = low.replace("remove wish", "", 1).strip()
#             if not pid:
#                 await cl.Message(content="Usage: `remove wish <product id>`").send()
#                 return
#             ok = remove_from_wishlist(pid)
#             if ok:
#                 await cl.Message(content=f"✅ Removed `{pid}` from your wishlist.").send()
#             else:
#                 await cl.Message(content=f"❌ `{pid}` not in your wishlist.").send()
#             return
#         else:
#             pid = low.replace("remove", "", 1).strip()
#             if not pid:
#                 await cl.Message(content="Usage: `remove <product id>` (e.g. `remove p3`)").send()
#                 return
#             ok = remove_from_cart(pid)
#             if ok:
#                 await cl.Message(content=f"✅ Removed `{pid}` from cart.").send()
#             else:
#                 await cl.Message(content=f"❌ `{pid}` not found in your cart.").send()
#             return

#     # clear cart
#     if low in ("clear cart", "clear_cart"):
#         clear_cart()
#         await cl.Message(content="🗑 Cart cleared.").send()
#         return

#     # clear wishlist
#     if low in ("clear wishlist", "clear_wishlist"):
#         clear_wishlist()
#         await cl.Message(content="🗑 Wishlist cleared.").send()
#         return

#     # start checkout
#     if low == "checkout":
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Add items before checkout.").send()
#             return

#         cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#         await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#         return

#     # unknown command fallback
#     await cl.Message(content="❓ Try `search <term>`, `show cart`, or `show wishlist`.").send()

# # -------------------------
# # Action callbacks
# # -------------------------
# @cl.action_callback("add_to_cart")
# async def on_add_to_cart(action):
#     pid = action.payload.get("id")
#     ok, result = add_product_to_cart(pid)
#     if not ok:
#         await cl.Message(content=str(result)).send()
#         await action.remove()
#         return

#     product = result
#     await cl.Message(content=f"✅ Added **{product['name']}** to cart.").send()

#     # Phase-5: show related items (mini-thumbs) right after adding
#     rel = related_by_tags(product, limit=3)
#     if rel:
#         rel_elements = []
#         rel_lines = []
#         actions = []
#         for r in rel:
#             rel_elements.append(cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline"))
#             actions.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#             rel_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#         await cl.Message(content="**Related you may like:**\n" + "\n".join(rel_lines), elements=rel_elements, actions=actions).send()

#     await action.remove()

# @cl.action_callback("add_to_wishlist")
# async def on_add_to_wishlist(action):
#     pid = action.payload.get("id")
#     ok, result = add_to_wishlist(pid)
#     if not ok:
#         await cl.Message(content=str(result)).send()
#         await action.remove()
#         return
#     product = result
#     await cl.Message(content=f"♡ Added **{product['name']}** to your wishlist. Use `show wishlist` to view.").send()
#     await action.remove()

# @cl.action_callback("product_detail")
# async def on_product_detail(action):
#     pid = action.payload.get("id")
#     p = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not p:
#         await cl.Message(content="Product not found.").send()
#         await action.remove()
#         return

#     img = cl.Image(url=p["image"], name=p["name"], display="inline")
#     actions = [
#         cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]}),
#         cl.Action(name="add_to_wishlist", label="♡ Wishlist", payload={"id": p["id"]}),
#     ]
#     content = (
#         f"**{p['name']}**\n\n{p.get('desc','')}\n\n"
#         f"Category: `{p.get('category','')}`\n"
#         f"Price: **${p['price']}**"
#     )
#     await cl.Message(content=content, elements=[img], actions=actions).send()

#     # Related (mini-thumbs)
#     rel = related_by_tags(p, limit=3)
#     if rel:
#         rel_elements = []
#         rel_lines = []
#         rel_actions = []
#         for r in rel:
#             rel_elements.append(cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline"))
#             rel_actions.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#             rel_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#         await cl.Message(content="**Related products:**\n" + "\n".join(rel_lines), elements=rel_elements, actions=rel_actions).send()

#     await action.remove()

# @cl.action_callback("clear_cart")
# async def on_clear_cart(action):
#     clear_cart()
#     await cl.Message(content="🗑 Cart cleared.").send()
#     await action.remove()

# @cl.action_callback("checkout")
# async def on_checkout(action):
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         await action.remove()
#         return

#     cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#     await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#     await action.remove()

# @cl.action_callback("clear_wishlist")
# async def on_clear_wishlist(action):
#     clear_wishlist()
#     await cl.Message(content="🗑 Wishlist cleared.").send()
#     await action.remove()

# # -------------------------
# # Checkout multi-step flow
# # -------------------------
# async def handle_checkout_flow(text):
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing. Type `checkout` to start.").send()
#         return

#     step = state.get("step")
#     data = state.get("data", {})

#     if step == "name":
#         name = text.strip()
#         if not name or len(name) < 2:
#             await cl.Message(content="Please provide a valid full name.").send()
#             return
#         data["name"] = name
#         state["step"] = "address"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Got it. Now enter your **shipping address**:").send()
#         return

#     if step == "address":
#         address = text.strip()
#         if not address or len(address) < 5:
#             await cl.Message(content="Please provide a valid address (street, city, etc.).").send()
#             return
#         data["address"] = address
#         state["step"] = "phone"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Great. Finally, please provide your **phone number**:").send()
#         return

#     if step == "phone":
#         phone = text.strip()
#         digits = re.sub(r"\D", "", phone)
#         if len(digits) < 7:
#             await cl.Message(content="Please provide a valid phone number (at least 7 digits).").send()
#             return
#         data["phone"] = phone
#         state["step"] = "confirm"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)

#         cart = get_cart()
#         lines = [f"- {it['name']} x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
#         total = cart_total(cart)
#         summary = f"**Order summary:**\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}\n\n"
#         summary += f"**Ship to:** {data['name']}, {data['address']}, 📞 {data['phone']}\n\n"
#         summary += "Type `confirm` to place the order or `cancel` to abort."

#         elements = [
#             cl.Action(name="confirm_order", label="✅ Confirm", payload={}),
#             cl.Action(name="cancel_order", label="❌ Cancel", payload={})
#         ]
#         await cl.Message(content=summary, actions=elements).send()
#         return

#     if step == "confirm":
#         low = text.lower().strip()
#         if low == "confirm":
#             await finalize_order()
#         elif low == "cancel":
#             cl.user_session.set("checkout_state", None)
#             await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#         else:
#             await cl.Message(content="Type `confirm` to place order or `cancel` to abort.").send()
#         return

# @cl.action_callback("confirm_order")
# async def on_confirm_order(action):
#     await finalize_order()
#     await action.remove()

# @cl.action_callback("cancel_order")
# async def on_cancel_order(action):
#     cl.user_session.set("checkout_state", None)
#     await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#     await action.remove()

# async def finalize_order():
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing.").send()
#         return
#     data = state.get("data", {})
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         cl.user_session.set("checkout_state", None)
#         return

#     order_id, total = save_order(data["name"], data["address"], data["phone"], cart)
#     clear_cart()
#     cl.user_session.set("checkout_state", None)

#     await cl.Message(
#         content=(
#             f"🎉 **Order placed!**\n"
#             f"Order ID: `{order_id}`\n"
#             f"Total: ${total:.2f}\n"
#             f"We saved your order — we'll contact you at {data['phone']}."
#         ),
#         elements=[cl.Image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", name="Order Placed")]
#     ).send()

# # -------------------------
# # End of file
# # -------------------------


# import chainlit as cl
# import json
# import os
# import re
# import sqlite3
# import threading
# import uuid
# from datetime import datetime

# # --- Static files via FastAPI (serve local images like /static/tshirt.jpg) ---
# # pip install fastapi uvicorn
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# import uvicorn

# STATIC_DIR = "static"
# STATIC_HOST = "0.0.0.0"
# STATIC_PORT = 8000

# # Make sure static folder exists
# os.makedirs(STATIC_DIR, exist_ok=True)

# _fastapi_started = False
# def _run_fastapi():
#     app = FastAPI()
#     app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
#     uvicorn.run(app, host=STATIC_HOST, port=STATIC_PORT, log_level="warning")

# def start_static_server_once():
#     global _fastapi_started
#     if not _fastapi_started:
#         t = threading.Thread(target=_run_fastapi, daemon=True)
#         t.start()
#         _fastapi_started = True

# # -------------------------
# # Config / Files / DB Init
# # -------------------------
# PRODUCTS_FILE = "products.json"
# DB_FILE = "shop.db"

# # Phase-5 persistence files
# CART_FILE = "cart.json"
# WISHLIST_FILE = "wishlist.json"

# def _read_json(path, default_val):
#     try:
#         if os.path.exists(path):
#             with open(path, "r", encoding="utf-8") as f:
#                 return json.load(f)
#     except Exception as e:
#         print(f"⚠️ Failed reading {path}: {e}")
#     return default_val

# def _write_json(path, data):
#     try:
#         with open(path, "w", encoding="utf-8") as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#     except Exception as e:
#         print(f"⚠️ Failed writing {path}: {e}")

# # Load products
# if os.path.exists(PRODUCTS_FILE):
#     with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
#         PRODUCTS = json.load(f)
# else:
#     PRODUCTS = []
#     print("⚠️ products.json not found! Using empty catalog.")

# # Ensure each product has category/tags keys & optional 'thumb'
# for p in PRODUCTS:
#     p.setdefault("category", "general")
#     p.setdefault("tags", [])
#     # Optional smaller preview image:
#     p.setdefault("thumb", p.get("image", ""))  # if 'thumb' missing, fallback to main image

# # Initialize SQLite DB (orders)
# def init_db():
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS orders (
#             id TEXT PRIMARY KEY,
#             name TEXT,
#             address TEXT,
#             phone TEXT,
#             total REAL,
#             items_json TEXT,
#             created_at TEXT
#         )
#         """
#     )
#     conn.commit()
#     conn.close()

# init_db()

# # -------------------------
# # Utility Functions
# # -------------------------
# def search_products(query):
#     """
#     Smart search that accepts:
#       - keywords
#       - category:men
#       - price<50 or price>20 or price<=100 etc.
#     Returns list of product dicts.
#     """
#     q = query.strip().lower()

#     # extract category
#     category_match = re.search(r"category:([a-z0-9_-]+)", q)
#     category = category_match.group(1) if category_match else None
#     if category:
#         q = re.sub(r"category:[a-z0-9_-]+", "", q)

#     # extract price filters
#     price_filters = re.findall(r"price\s*(<=|>=|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)", q)
#     # also handle "<2000" or "under 2000" patterns
#     under_match = re.search(r"(under|less than|below)\s*([0-9]+)", q)
#     if under_match:
#         price_filters.append(("<", under_match.group(2)))

#     greater_match = re.search(r"(over|above|more than)\s*([0-9]+)", q)
#     if greater_match:
#         price_filters.append((">", greater_match.group(2)))

#     # clean query (remove price words)
#     q_clean = re.sub(r"price\s*(<=|>=|<|>|=)\s*[0-9]+(?:\.[0-9]+)?", "", q)
#     q_clean = re.sub(r"(under|less than|below|over|above|more than)\s*[0-9]+", "", q_clean)
#     q_clean = q_clean.strip()

#     results = []
#     for p in PRODUCTS:
#         name_desc = f"{p.get('name','')} {p.get('desc','')}".lower()

#         # basic keyword match (also search in tags)
#         if q_clean:
#             if (q_clean not in name_desc) and (not any(q_clean in t.lower() for t in p.get("tags", []))):
#                 continue

#         # category filter
#         if category and category != p.get("category", "").lower():
#             continue

#         # price filters
#         price_ok = True
#         for op, num in price_filters:
#             try:
#                 numf = float(num)
#                 price = float(p.get("price", 0))
#                 if op == "<" and not (price < numf): price_ok = False
#                 elif op == "<=" and not (price <= numf): price_ok = False
#                 elif op == ">" and not (price > numf): price_ok = False
#                 elif op == ">=" and not (price >= numf): price_ok = False
#                 elif op == "=" and not (price == numf): price_ok = False
#             except:
#                 price_ok = False
#         if not price_ok:
#             continue

#         results.append(p)

#     return results

# # ------- Phase-5: Persisted session state helpers -------
# def _ensure_session_defaults():
#     cl.user_session.set("cart", cl.user_session.get("cart", []))
#     cl.user_session.set("wishlist", cl.user_session.get("wishlist", []))

# def _load_persisted_state_into_session():
#     cl.user_session.set("cart", _read_json(CART_FILE, []))
#     cl.user_session.set("wishlist", _read_json(WISHLIST_FILE, []))

# def _persist_session():
#     _write_json(CART_FILE, cl.user_session.get("cart", []))
#     _write_json(WISHLIST_FILE, cl.user_session.get("wishlist", []))

# # ------- Cart helpers -------
# def get_cart():
#     return cl.user_session.get("cart", [])

# def save_cart(cart):
#     cl.user_session.set("cart", cart)
#     _persist_session()

# def add_product_to_cart(pid, qty=1):
#     product = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not product:
#         return False, "Product not found."

#     cart = get_cart()
#     for item in cart:
#         if item["id"] == pid:
#             item["qty"] += qty
#             break
#     else:
#         cart.append({
#             "id": product["id"],
#             "name": product["name"],
#             "price": product["price"],
#             "qty": qty
#         })
#     save_cart(cart)
#     return True, product

# def remove_from_cart(pid):
#     cart = get_cart()
#     new_cart = [it for it in cart if it["id"] != pid]
#     save_cart(new_cart)
#     return len(new_cart) != len(cart)

# def clear_cart():
#     save_cart([])

# def cart_total(cart=None):
#     c = cart if cart is not None else get_cart()
#     return sum(item["price"] * item["qty"] for item in c)

# # ------- Wishlist helpers (Phase-5) -------
# def get_wishlist():
#     return cl.user_session.get("wishlist", [])

# def save_wishlist(wishlist):
#     cl.user_session.set("wishlist", wishlist)
#     _persist_session()

# def add_to_wishlist(pid):
#     product = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not product:
#         return False, "Product not found."

#     wishlist = get_wishlist()
#     if pid not in [w["id"] for w in wishlist]:
#         wishlist.append({
#             "id": product["id"],
#             "name": product["name"],
#             "price": product["price"]
#         })
#         save_wishlist(wishlist)
#     return True, product

# def remove_from_wishlist(pid):
#     wishlist = get_wishlist()
#     new_list = [w for w in wishlist if w["id"] != pid]
#     save_wishlist(new_list)
#     return len(new_list) != len(wishlist)

# def clear_wishlist():
#     save_wishlist([])

# # ------- Recommendations -------
# def recommend_for_cart():
#     """
#     Simple rule-based recommendations:
#     - If cart has 'sneakers' recommend 'jeans' or 't-shirt'
#     - Otherwise recommend cheapest 3 not in cart
#     """
#     cart = get_cart()
#     names = " ".join([it["name"].lower() for it in cart])
#     recs = []

#     def add_by_keyword(kw, limit=2):
#         for p in PRODUCTS:
#             if kw in p["name"].lower() and p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#                 if len(recs) >= limit:
#                     break

#     if "sneaker" in names or "sneakers" in names:
#         add_by_keyword("jeans")
#         add_by_keyword("t-shirt")
#     elif "jacket" in names or "hoodie" in names:
#         add_by_keyword("sneakers")
#         add_by_keyword("t-shirt")
#     else:
#         for p in sorted(PRODUCTS, key=lambda x: x.get("price", 0)):
#             if p["id"] not in [it["id"] for it in cart]:
#                 recs.append(p)
#             if len(recs) >= 3:
#                 break

#     seen = set()
#     dedup = []
#     for r in recs:
#         if r["id"] not in seen:
#             dedup.append(r)
#             seen.add(r["id"])
#         if len(dedup) >= 3:
#             break
#     return dedup

# def related_by_tags(product, limit=3):
#     """Return up to `limit` products sharing at least one tag with `product`."""
#     tags = set([t.lower() for t in product.get("tags", [])])
#     if not tags:
#         return []

#     rel = []
#     for p in PRODUCTS:
#         if p["id"] == product["id"]:
#             continue
#         if tags.intersection([t.lower() for t in p.get("tags", [])]):
#             rel.append(p)
#     # prioritize by number of shared tags, then price ascending
#     rel.sort(key=lambda x: (-len(tags.intersection([t.lower() for t in x.get("tags", [])])), x.get("price", 0)))
#     return rel[:limit]

# def save_order(name, address, phone, cart):
#     order_id = str(uuid.uuid4())[:8]
#     total = cart_total(cart)
#     items_json = json.dumps(cart, ensure_ascii=False)
#     created_at = datetime.utcnow().isoformat()
#     conn = sqlite3.connect(DB_FILE)
#     cur = conn.cursor()
#     cur.execute(
#         "INSERT INTO orders (id, name, address, phone, total, items_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
#         (order_id, name, address, phone, total, items_json, created_at)
#     )
#     conn.commit()
#     conn.close()
#     return order_id, total

# # -------------------------
# # UI helpers (cards & grids)
# # -------------------------
# async def send_product_card(p):
#     """Send a main product card with image + actions."""
#     img = cl.Image(url=p["image"], name=p["name"], display="inline")
#     actions = [
#         cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]}),
#         cl.Action(name="add_to_wishlist", label="♡ Wishlist", payload={"id": p["id"]}),
#         cl.Action(name="product_detail", label="Details", payload={"id": p["id"]}),
#     ]
#     content = (
#         f"**{p['name']}**\n"
#         f"{p.get('desc','')}\n\n"
#         f"Category: `{p.get('category','')}`\n"
#         f"💵 Price: **${p['price']}**"
#     )
#     await cl.Message(content=content, elements=[img], actions=actions).send()

# async def send_related_grid(related):
#     """
#     Show small thumbnail 'grid' for related products with two actions each:
#     - View (opens product detail)
#     - Quick Add (adds to cart)
#     """
#     if not related:
#         return

#     # 1) Thumbnails inline (forms a grid/row)
#     thumb_elements = [cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline") for r in related]
#     await cl.Message(content="**Related products:**", elements=thumb_elements).send()

#     # 2) Buttons (View / Quick Add) for each related item
#     # Chainlit actions are message-level; we'll stack pairs of buttons per product (max 3)
#     btns = []
#     lines = []
#     for r in related:
#         btns.append(cl.Action(name="show_product", label=f"View {r['name']}", payload={"id": r["id"]}))
#         btns.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#         lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#     await cl.Message(content="\n".join(lines), actions=btns).send()

# # -------------------------
# # UI / Chat Handlers
# # -------------------------
# @cl.on_chat_start
# async def start():
#     # static server (for local images)
#     start_static_server_once()
#     # Phase-5: load persisted state into this Chainlit session
#     _load_persisted_state_into_session()
#     _ensure_session_defaults()

#     welcome = (
#         "👋 **Welcome to ShopBot Pro (Phase 5)!**\n\n"
#         "Try:\n"
#         " - `search sneakers`\n"
#         " - `search jackets category:men price<100`\n"
#         " - `search shirts under 50`\n\n"
#         "**Cart commands:** `show cart`, `remove <id>`, `clear cart`, `checkout`\n"
#         "**Wishlist commands:** `show wishlist`, `remove wish <id>`, `clear wishlist`\n"
#         "Tip: Related products thumbnails appear under each card. Click **View** to open that product.\n"
#     )
#     await cl.Message(content=welcome).send()

# @cl.on_message
# async def handle_message(message: cl.Message):
#     text = (message.content or "").strip()

#     # If in checkout flow, route to checkout handler
#     if cl.user_session.get("checkout_state"):
#         await handle_checkout_flow(text)
#         return

#     low = text.lower()

#     # search command (smart) — one message per product
#     if low.startswith("search"):
#         query = text.replace("search", "", 1).strip()
#         if not query:
#             await cl.Message(content="Type something to search, e.g. `search sneakers`").send()
#             return

#         results = search_products(query)
#         if not results:
#             await cl.Message(content=f"❌ No products found for `{query}`.").send()
#             return

#         header = f"**Search results for:** `{query}`\nShowing {min(len(results), 8)} of {len(results)}"
#         await cl.Message(content=header).send()

#         for p in results[:8]:
#             # main product card
#             await send_product_card(p)

#             # related mini-thumbs (by tags) shown as a small grid
#             rel = related_by_tags(p, limit=3)
#             await send_related_grid(rel)

#         return

#     # view cart
#     if low in ("show cart", "view cart", "cart"):
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Try `search sneakers`.").send()
#             return

#         lines = [f"`{it['id']}` — **{it['name']}** x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
#         total = cart_total(cart)

#         actions = [
#             cl.Action(name="checkout", label="✅ Checkout", payload={}),
#             cl.Action(name="clear_cart", label="🗑 Clear Cart", payload={})
#         ]

#         # recs for cart (quick add + mini images)
#         recs = recommend_for_cart()
#         rec_section = ""
#         if recs:
#             rec_lines = []
#             thumbs = []
#             rec_btns = []
#             for r in recs:
#                 rec_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")
#                 thumbs.append(cl.Image(url=r.get("thumb") or r.get("image"), name=r["name"], display="inline"))
#                 rec_btns.append(cl.Action(name="show_product", label=f"View {r['name']}", payload={"id": r["id"]}))
#                 rec_btns.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
#             rec_section = "\n\n**You might also like:**\n" + "\n".join(rec_lines)

#             # Show thumbs row
#             await cl.Message(content="**You might also like (thumbnails):**", elements=thumbs).send()
#             # Show buttons row
#             actions.extend(rec_btns)

#         await cl.Message(
#             content=f"**🛒 Your Cart:**\n\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}" + rec_section,
#             actions=actions
#         ).send()
#         return

#     # wishlist views
#     if low in ("show wishlist", "wishlist"):
#         wl = get_wishlist()
#         if not wl:
#             await cl.Message(content="♡ Your wishlist is empty. Add items via the '♡ Wishlist' button.").send()
#             return
#         lines = [f"`{w['id']}` — **{w['name']}** — ${w['price']:.2f}" for w in wl]
#         actions = [cl.Action(name="clear_wishlist", label="🗑 Clear Wishlist", payload={})]
#         for w in wl:
#             actions.append(cl.Action(name="show_product", label=f"View {w['name']}", payload={"id": w["id"]}))
#             actions.append(cl.Action(name="add_to_cart", label=f"Add {w['name']} to cart", payload={"id": w["id"]}))
#         await cl.Message(content="**♡ Your Wishlist:**\n\n" + "\n".join(lines), actions=actions).send()
#         return

#     # remove single item by command "remove p3"
#     if low.startswith("remove"):
#         # two patterns: "remove p3" (cart) or "remove wish p3"
#         if low.startswith("remove wish"):
#             pid = low.replace("remove wish", "", 1).strip()
#             if not pid:
#                 await cl.Message(content="Usage: `remove wish <product id>`").send()
#                 return
#             ok = remove_from_wishlist(pid)
#             if ok:
#                 await cl.Message(content=f"✅ Removed `{pid}` from your wishlist.").send()
#             else:
#                 await cl.Message(content=f"❌ `{pid}` not in your wishlist.").send()
#             return
#         else:
#             pid = low.replace("remove", "", 1).strip()
#             if not pid:
#                 await cl.Message(content="Usage: `remove <product id>` (e.g. `remove p3`)").send()
#                 return
#             ok = remove_from_cart(pid)
#             if ok:
#                 await cl.Message(content=f"✅ Removed `{pid}` from cart.").send()
#             else:
#                 await cl.Message(content=f"❌ `{pid}` not found in your cart.").send()
#             return

#     # clear cart
#     if low in ("clear cart", "clear_cart"):
#         clear_cart()
#         await cl.Message(content="🗑 Cart cleared.").send()
#         return

#     # clear wishlist
#     if low in ("clear wishlist", "clear_wishlist"):
#         clear_wishlist()
#         await cl.Message(content="🗑 Wishlist cleared.").send()
#         return

#     # start checkout
#     if low == "checkout":
#         cart = get_cart()
#         if not cart:
#             await cl.Message(content="🛒 Your cart is empty. Add items before checkout.").send()
#             return

#         cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#         await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#         return

#     # unknown command fallback
#     await cl.Message(content="❓ Try `search <term>`, `show cart`, or `show wishlist`.").send()

# # -------------------------
# # Action callbacks
# # -------------------------
# @cl.action_callback("add_to_cart")
# async def on_add_to_cart(action):
#     pid = action.payload.get("id")
#     ok, result = add_product_to_cart(pid)
#     if not ok:
#         await cl.Message(content=str(result)).send()
#         await action.remove()
#         return

#     product = result
#     await cl.Message(content=f"✅ Added **{product['name']}** to cart.").send()

#     # Show related (mini-thumbs) right after adding
#     rel = related_by_tags(product, limit=3)
#     await send_related_grid(rel)

#     await action.remove()

# @cl.action_callback("add_to_wishlist")
# async def on_add_to_wishlist(action):
#     pid = action.payload.get("id")
#     ok, result = add_to_wishlist(pid)
#     if not ok:
#         await cl.Message(content=str(result)).send()
#         await action.remove()
#         return
#     product = result
#     await cl.Message(content=f"♡ Added **{product['name']}** to your wishlist. Use `show wishlist` to view.").send()
#     await action.remove()

# @cl.action_callback("product_detail")
# async def on_product_detail(action):
#     pid = action.payload.get("id")
#     p = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not p:
#         await cl.Message(content="Product not found.").send()
#         await action.remove()
#         return

#     await send_product_card(p)

#     # Related (mini-thumbs) as grid + buttons
#     rel = related_by_tags(p, limit=3)
#     await send_related_grid(rel)

#     await action.remove()

# @cl.action_callback("show_product")
# async def on_show_product(action):
#     """Open the selected product (from related grid or wishlist/cart suggestions)."""
#     pid = action.payload.get("id")
#     p = next((x for x in PRODUCTS if x["id"] == pid), None)
#     if not p:
#         await cl.Message(content="Product not found.").send()
#         await action.remove()
#         return

#     # Show selected product card
#     await send_product_card(p)

#     # And show its related grid
#     rel = related_by_tags(p, limit=3)
#     await send_related_grid(rel)

#     await action.remove()

# @cl.action_callback("clear_cart")
# async def on_clear_cart(action):
#     clear_cart()
#     await cl.Message(content="🗑 Cart cleared.").send()
#     await action.remove()

# @cl.action_callback("checkout")
# async def on_checkout(action):
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         await action.remove()
#         return

#     cl.user_session.set("checkout_state", {"step": "name", "data": {}})
#     await cl.Message(content="✅ Checkout started. Please provide your **full name**:").send()
#     await action.remove()

# @cl.action_callback("clear_wishlist")
# async def on_clear_wishlist(action):
#     clear_wishlist()
#     await cl.Message(content="🗑 Wishlist cleared.").send()
#     await action.remove()

# # -------------------------
# # Checkout multi-step flow
# # -------------------------
# async def handle_checkout_flow(text):
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing. Type `checkout` to start.").send()
#         return

#     step = state.get("step")
#     data = state.get("data", {})

#     if step == "name":
#         name = text.strip()
#         if not name or len(name) < 2:
#             await cl.Message(content="Please provide a valid full name.").send()
#             return
#         data["name"] = name
#         state["step"] = "address"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Got it. Now enter your **shipping address**:").send()
#         return

#     if step == "address":
#         address = text.strip()
#         if not address or len(address) < 5:
#             await cl.Message(content="Please provide a valid address (street, city, etc.).").send()
#             return
#         data["address"] = address
#         state["step"] = "phone"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)
#         await cl.Message(content="Great. Finally, please provide your **phone number**:").send()
#         return

#     if step == "phone":
#         phone = text.strip()
#         digits = re.sub(r"\D", "", phone)
#         if len(digits) < 7:
#             await cl.Message(content="Please provide a valid phone number (at least 7 digits).").send()
#             return
#         data["phone"] = phone
#         state["step"] = "confirm"
#         state["data"] = data
#         cl.user_session.set("checkout_state", state)

#         cart = get_cart()
#         lines = [f"- {it['name']} x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
#         total = cart_total(cart)
#         summary = f"**Order summary:**\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}\n\n"
#         summary += f"**Ship to:** {data['name']}, {data['address']}, 📞 {data['phone']}\n\n"
#         summary += "Type `confirm` to place the order or `cancel` to abort."

#         elements = [
#             cl.Action(name="confirm_order", label="✅ Confirm", payload={}),
#             cl.Action(name="cancel_order", label="❌ Cancel", payload={})
#         ]
#         await cl.Message(content=summary, actions=elements).send()
#         return

#     if step == "confirm":
#         low = text.lower().strip()
#         if low == "confirm":
#             await finalize_order()
#         elif low == "cancel":
#             cl.user_session.set("checkout_state", None)
#             await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#         else:
#             await cl.Message(content="Type `confirm` to place order or `cancel` to abort.").send()
#         return

# @cl.action_callback("confirm_order")
# async def on_confirm_order(action):
#     await finalize_order()
#     await action.remove()

# @cl.action_callback("cancel_order")
# async def on_cancel_order(action):
#     cl.user_session.set("checkout_state", None)
#     await cl.Message(content="❌ Checkout canceled. Your cart is intact.").send()
#     await action.remove()

# async def finalize_order():
#     state = cl.user_session.get("checkout_state")
#     if not state:
#         await cl.Message(content="Checkout state missing.").send()
#         return
#     data = state.get("data", {})
#     cart = get_cart()
#     if not cart:
#         await cl.Message(content="🛒 Your cart is empty.").send()
#         cl.user_session.set("checkout_state", None)
#         return

#     order_id, total = save_order(data["name"], data["address"], data["phone"], cart)
#     clear_cart()
#     cl.user_session.set("checkout_state", None)

#     await cl.Message(
#         content=(
#             f"🎉 **Order placed!**\n"
#             f"Order ID: `{order_id}`\n"
#             f"Total: ${total:.2f}\n"
#             f"We saved your order — we'll contact you at {data['phone']}."
#         ),
#         elements=[cl.Image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", name="Order Placed")]
#     ).send()

# # -------------------------
# # End of file
# # -------------------------


# app.py (updated) ----------------------------------------
import chainlit as cl
import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime

# --- Static files via FastAPI (serve local images like /static/tshirt.jpg) ---
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

STATIC_DIR = "static"
STATIC_HOST = "127.0.0.1"   # use 127.0.0.1 for local dev
STATIC_PORT = 8000

os.makedirs(STATIC_DIR, exist_ok=True)

_fastapi_started = False
def _run_fastapi():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    uvicorn.run(app, host=STATIC_HOST, port=STATIC_PORT, log_level="warning")

def start_static_server_once():
    global _fastapi_started
    if not _fastapi_started:
        t = threading.Thread(target=_run_fastapi, daemon=True)
        t.start()
        _fastapi_started = True

# -------------------------
# Config / Files / DB Init
# -------------------------
PRODUCTS_FILE = "products.json"
DB_FILE = "shop.db"

CART_FILE = "cart.json"
WISHLIST_FILE = "wishlist.json"

def _read_json(path, default_val):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed reading {path}: {e}")
    return default_val

def _write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Failed writing {path}: {e}")

# Load products
if os.path.exists(PRODUCTS_FILE):
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        PRODUCTS = json.load(f)
else:
    PRODUCTS = []
    print("⚠️ products.json not found! Using empty catalog.")

# Ensure each product has keys & thumb fallback
for p in PRODUCTS:
    p.setdefault("category", "general")
    p.setdefault("tags", [])
    p.setdefault("thumb", p.get("image", ""))

# db init
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            phone TEXT,
            total REAL,
            items_json TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Utilities (search / related)
# -------------------------
def search_products(query):
    q = query.strip().lower()
    category_match = re.search(r"category:([a-z0-9_-]+)", q)
    category = category_match.group(1) if category_match else None
    if category:
        q = re.sub(r"category:[a-z0-9_-]+", "", q)
    price_filters = re.findall(r"price\s*(<=|>=|<|>|=)\s*([0-9]+(?:\.[0-9]+)?)", q)
    under_match = re.search(r"(under|less than|below)\s*([0-9]+)", q)
    if under_match:
        price_filters.append(("<", under_match.group(2)))
    greater_match = re.search(r"(over|above|more than)\s*([0-9]+)", q)
    if greater_match:
        price_filters.append((">", greater_match.group(2)))
    q_clean = re.sub(r"price\s*(<=|>=|<|>|=)\s*[0-9]+(?:\.[0-9]+)?", "", q)
    q_clean = re.sub(r"(under|less than|below|over|above|more than)\s*[0-9]+", "", q_clean)
    q_clean = q_clean.strip()

    results = []
    for p in PRODUCTS:
        name_desc = f"{p.get('name','')} {p.get('desc','')}".lower()
        if q_clean:
            if (q_clean not in name_desc) and (not any(q_clean in t.lower() for t in p.get("tags", []))):
                continue
        if category and category != p.get("category","").lower():
            continue
        price_ok = True
        for op, num in price_filters:
            try:
                numf = float(num)
                price = float(p.get("price", 0))
                if op == "<" and not (price < numf): price_ok = False
                elif op == "<=" and not (price <= numf): price_ok = False
                elif op == ">" and not (price > numf): price_ok = False
                elif op == ">=" and not (price >= numf): price_ok = False
                elif op == "=" and not (price == numf): price_ok = False
            except:
                price_ok = False
        if not price_ok:
            continue
        results.append(p)
    return results

def related_by_tags(product, limit=3):
    tags = set([t.lower() for t in product.get("tags", [])])
    if not tags:
        return []
    rel = []
    for p in PRODUCTS:
        if p["id"] == product["id"]:
            continue
        if tags.intersection([t.lower() for t in p.get("tags", [])]):
            rel.append(p)
    rel.sort(key=lambda x: (-len(tags.intersection([t.lower() for t in x.get("tags", [])])), x.get("price", 0)))
    return rel[:limit]

# -------------------------
# Persistence helpers
# -------------------------
def _load_persisted_state_into_session():
    cl.user_session.set("cart", _read_json(CART_FILE, []))
    cl.user_session.set("wishlist", _read_json(WISHLIST_FILE, []))

def _persist_session():
    _write_json(CART_FILE, cl.user_session.get("cart", []))
    _write_json(WISHLIST_FILE, cl.user_session.get("wishlist", []))

def _ensure_session_defaults():
    cl.user_session.set("cart", cl.user_session.get("cart", []))
    cl.user_session.set("wishlist", cl.user_session.get("wishlist", []))

# -------------------------
# Cart / wishlist / orders
# -------------------------
def get_cart():
    return cl.user_session.get("cart", [])

def save_cart(cart):
    cl.user_session.set("cart", cart)
    _persist_session()

def add_product_to_cart(pid, qty=1):
    product = next((x for x in PRODUCTS if x["id"] == pid), None)
    if not product:
        return False, "Product not found."
    cart = get_cart()
    for item in cart:
        if item["id"] == pid:
            item["qty"] += qty
            break
    else:
        cart.append({"id": product["id"], "name": product["name"], "price": product["price"], "qty": qty})
    save_cart(cart)
    return True, product

def remove_from_cart(pid):
    cart = get_cart()
    new_cart = [it for it in cart if it["id"] != pid]
    save_cart(new_cart)
    return len(new_cart) != len(cart)

def clear_cart():
    save_cart([])

def cart_total(cart=None):
    c = cart if cart is not None else get_cart()
    return sum(item["price"] * item["qty"] for item in c)

def get_wishlist():
    return cl.user_session.get("wishlist", [])

def save_wishlist(wl):
    cl.user_session.set("wishlist", wl)
    _persist_session()

def add_to_wishlist(pid):
    product = next((x for x in PRODUCTS if x["id"] == pid), None)
    if not product:
        return False, "Product not found."
    wl = get_wishlist()
    if pid not in [w["id"] for w in wl]:
        wl.append({"id": product["id"], "name": product["name"], "price": product["price"]})
        save_wishlist(wl)
    return True, product

def remove_from_wishlist(pid):
    wl = get_wishlist()
    new_list = [w for w in wl if w["id"] != pid]
    save_wishlist(new_list)
    return len(new_list) != len(wl)

def clear_wishlist():
    save_wishlist([])

def save_order(name, address, phone, cart):
    order_id = str(uuid.uuid4())[:8]
    total = cart_total(cart)
    items_json = json.dumps(cart, ensure_ascii=False)
    created_at = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (id, name, address, phone, total, items_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (order_id, name, address, phone, total, items_json, created_at)
    )
    conn.commit()
    conn.close()
    return order_id, total

# -------------------------
# UI helpers: product card + related grid
# -------------------------
async def send_product_card(p):
    img = cl.Image(url=p["image"], name=p["name"], display="inline")
    actions = [
        cl.Action(name="add_to_cart", label=f"Add to cart (${p['price']})", payload={"id": p["id"]}),
        cl.Action(name="add_to_wishlist", label="♡ Wishlist", payload={"id": p["id"]}),
        cl.Action(name="product_detail", label="Details", payload={"id": p["id"]}),
    ]
    content = f"**{p['name']}**\n{p.get('desc','')}\n\nCategory: `{p.get('category','')}`\n💵 Price: **${p['price']}**"
    await cl.Message(content=content, elements=[img], actions=actions).send()

async def send_related_grid(related):
    """
    Important: elements (images) and actions are sent in SAME message so Chainlit shows them together.
    """
    if not related:
        return

    # build image elements (thumbnails)
    thumb_elements = []
    for r in related:
        # use thumb if provided else main image
        thumb_url = r.get("thumb") or r.get("image")
        thumb_elements.append(cl.Image(url=thumb_url, name=r["name"], display="inline"))

    # build actions: for each related product we create two actions (View and Quick Add)
    actions = []
    text_lines = []
    for r in related:
        actions.append(cl.Action(name="show_product", label=f"View {r['name']}", payload={"id": r["id"]}))
        actions.append(cl.Action(name="add_to_cart", label=f"Quick Add {r['name']}", payload={"id": r["id"]}))
        text_lines.append(f"- **{r['name']}** — ${r['price']} (id: `{r['id']}`)")

    # send one message containing thumbs + actions
    await cl.Message(content="**Related products:**\n" + "\n".join(text_lines), elements=thumb_elements, actions=actions).send()

# -------------------------
# Chat handlers
# -------------------------
@cl.on_chat_start
async def start():
    start_static_server_once()
    _load_persisted_state_into_session()
    _ensure_session_defaults()

    welcome = (
        "👋 Welcome to ShopBot Pro!\n\n"
        "Try `search sneakers` or `search jeans`.\n"
        "Commands: `show cart`, `show wishlist`, `checkout`, `clear cart`."
    )
    await cl.Message(content=welcome).send()

@cl.on_message
async def handle_message(message: cl.Message):
    text = (message.content or "").strip()
    if cl.user_session.get("checkout_state"):
        await handle_checkout_flow(text)
        return

    low = text.lower()
    if low.startswith("search"):
        query = text.replace("search","",1).strip()
        if not query:
            await cl.Message(content="Type something to search, e.g. `search sneakers`").send()
            return
        results = search_products(query)
        if not results:
            await cl.Message(content=f"No products found for `{query}`").send()
            return
        await cl.Message(content=f"**Search results for:** `{query}` — showing {min(len(results),8)}").send()
        for p in results[:8]:
            await send_product_card(p)
            rel = related_by_tags(p, limit=3)
            await send_related_grid(rel)
        return

    if low in ("show cart","view cart","cart"):
        cart = get_cart()
        if not cart:
            await cl.Message(content="🛒 Your cart is empty. Try `search sneakers`.").send()
            return
        lines = [f"`{it['id']}` — **{it['name']}** x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
        total = cart_total(cart)
        actions = [cl.Action(name="checkout", label="✅ Checkout", payload={}), cl.Action(name="clear_cart", label="🗑 Clear Cart", payload={})]
        await cl.Message(content="**🛒 Your Cart:**\n\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}", actions=actions).send()
        return

    if low in ("show wishlist","wishlist"):
        wl = get_wishlist()
        if not wl:
            await cl.Message(content="♡ Your wishlist is empty.").send()
            return
        lines = [f"`{w['id']}` — **{w['name']}** — ${w['price']:.2f}" for w in wl]
        actions = [cl.Action(name="clear_wishlist", label="🗑 Clear Wishlist", payload={})]
        for w in wl:
            actions.append(cl.Action(name="show_product", label=f"View {w['name']}", payload={"id": w["id"]}))
        await cl.Message(content="**♡ Wishlist:**\n\n" + "\n".join(lines), actions=actions).send()
        return

    if low.startswith("remove"):
        if low.startswith("remove wish"):
            pid = low.replace("remove wish","",1).strip()
            ok = remove_from_wishlist(pid)
            await cl.Message(content=f"Removed from wishlist: {pid}" if ok else f"{pid} not in wishlist").send()
            return
        pid = low.replace("remove","",1).strip()
        ok = remove_from_cart(pid)
        await cl.Message(content=f"Removed from cart: {pid}" if ok else f"{pid} not in cart").send()
        return

    if low in ("clear cart","clear_cart"):
        clear_cart()
        await cl.Message(content="Cart cleared.").send()
        return

    if low in ("clear wishlist","clear_wishlist"):
        clear_wishlist()
        await cl.Message(content="Wishlist cleared.").send()
        return

    if low == "checkout":
        cart = get_cart()
        if not cart:
            await cl.Message(content="Cart empty. Add items before checkout.").send()
            return
        cl.user_session.set("checkout_state", {"step":"name","data":{}})
        await cl.Message(content="Checkout: please enter your full name:").send()
        return

    await cl.Message(content="I didn't understand. Try `search <term>` or `show cart`.").send()

# -------------------------
# Action callbacks (add/view/quick-add)
# -------------------------
@cl.action_callback("add_to_cart")
async def on_add_to_cart(action):
    pid = action.payload.get("id")
    ok, product = add_product_to_cart(pid)
    if not ok:
        await cl.Message(content=product).send()
        await action.remove()
        return
    await cl.Message(content=f"✅ Added **{product['name']}** to cart.").send()
    # show related grid after adding
    rel = related_by_tags(product, limit=3)
    await send_related_grid(rel)
    await action.remove()

@cl.action_callback("add_to_wishlist")
async def on_add_to_wishlist(action):
    pid = action.payload.get("id")
    ok, product = add_to_wishlist(pid)
    if not ok:
        await cl.Message(content=product).send()
        await action.remove()
        return
    await cl.Message(content=f"♡ Added **{product['name']}** to wishlist.").send()
    await action.remove()

@cl.action_callback("product_detail")
async def on_product_detail(action):
    pid = action.payload.get("id")
    p = next((x for x in PRODUCTS if x["id"] == pid), None)
    if not p:
        await cl.Message(content="Product not found.").send()
        await action.remove()
        return
    await send_product_card(p)
    rel = related_by_tags(p, limit=3)
    await send_related_grid(rel)
    await action.remove()

@cl.action_callback("show_product")
async def on_show_product(action):
    pid = action.payload.get("id")
    p = next((x for x in PRODUCTS if x["id"] == pid), None)
    if not p:
        await cl.Message(content="Product not found.").send()
        await action.remove()
        return
    await send_product_card(p)
    rel = related_by_tags(p, limit=3)
    await send_related_grid(rel)
    await action.remove()

@cl.action_callback("clear_cart")
async def on_clear_cart(action):
    clear_cart()
    await cl.Message(content="Cart cleared.").send()
    await action.remove()

@cl.action_callback("checkout")
async def on_checkout(action):
    cl.user_session.set("checkout_state", {"step":"name","data":{}})
    await cl.Message(content="Checkout: please enter your full name:").send()
    await action.remove()

@cl.action_callback("clear_wishlist")
async def on_clear_wishlist(action):
    clear_wishlist()
    await cl.Message(content="Wishlist cleared.").send()
    await action.remove()

# -------------------------
# Checkout flow (unchanged)
# -------------------------
async def handle_checkout_flow(text):
    state = cl.user_session.get("checkout_state")
    if not state:
        await cl.Message(content="Checkout state missing.").send()
        return
    step = state.get("step")
    data = state.get("data", {})
    if step == "name":
        name = text.strip()
        if not name or len(name) < 2:
            await cl.Message(content="Provide a valid name.").send()
            return
        data["name"] = name
        state["step"] = "address"
        state["data"] = data
        cl.user_session.set("checkout_state", state)
        await cl.Message(content="Enter shipping address:").send()
        return
    if step == "address":
        address = text.strip()
        if not address or len(address) < 5:
            await cl.Message(content="Provide a valid address.").send()
            return
        data["address"] = address
        state["step"] = "phone"
        state["data"] = data
        cl.user_session.set("checkout_state", state)
        await cl.Message(content="Enter phone number:").send()
        return
    if step == "phone":
        phone = text.strip()
        digits = re.sub(r"\D","",phone)
        if len(digits) < 7:
            await cl.Message(content="Provide valid phone (at least 7 digits).").send()
            return
        data["phone"] = phone
        state["step"] = "confirm"
        state["data"] = data
        cl.user_session.set("checkout_state", state)
        cart = get_cart()
        lines = [f"- {it['name']} x{it['qty']} = ${it['price']*it['qty']:.2f}" for it in cart]
        total = cart_total(cart)
        summary = f"**Order summary:**\n" + "\n".join(lines) + f"\n\n**Total:** ${total:.2f}\n\nShip to: {data['name']}, {data['address']}, {data['phone']}\n\nType `confirm` to place order."
        elements = [cl.Action(name="confirm_order", label="✅ Confirm", payload={}), cl.Action(name="cancel_order", label="❌ Cancel", payload={})]
        await cl.Message(content=summary, actions=elements).send()
        return
    if step == "confirm":
        if text.lower().strip() == "confirm":
            await finalize_order()
        elif text.lower().strip() == "cancel":
            cl.user_session.set("checkout_state", None)
            await cl.Message(content="Checkout cancelled.").send()
        else:
            await cl.Message(content="Type `confirm` or `cancel`.").send()
        return

@cl.action_callback("confirm_order")
async def on_confirm_order(action):
    await finalize_order()
    await action.remove()

@cl.action_callback("cancel_order")
async def on_cancel_order(action):
    cl.user_session.set("checkout_state", None)
    await cl.Message(content="Checkout cancelled.").send()
    await action.remove()

async def finalize_order():
    state = cl.user_session.get("checkout_state")
    if not state:
        await cl.Message(content="Checkout state missing.").send()
        return
    data = state.get("data", {})
    cart = get_cart()
    if not cart:
        await cl.Message(content="Cart empty.").send()
        cl.user_session.set("checkout_state", None)
        return
    order_id, total = save_order(data["name"], data["address"], data["phone"], cart)
    clear_cart()
    cl.user_session.set("checkout_state", None)
    await cl.Message(content=f"🎉 Order placed! ID: `{order_id}` Total: ${total:.2f}", elements=[cl.Image(url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExNGtuY2Q3ZTJxNDc2YjFvbzNyMnowNWpmYjIydWc3ODNoN2l5MWw5cyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/bRpa6DFERjTR9roQcQ/giphy.gif", name="Done")]).send()

# -------------------------
# End of file
# -------------------------------------------------------
