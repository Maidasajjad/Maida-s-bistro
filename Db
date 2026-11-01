"""SQLite database layer. All queries are parameterised (safe from SQL injection)."""
import os
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE, "data", "maidas_bistro.db"))
TZ = ZoneInfo("Asia/Karachi")
ORDER_STATUSES = ["Pending", "Preparing", "Completed", "Cancelled"]
RES_STATUSES = ["Pending", "Confirmed", "Completed", "Cancelled"]
TIME_SLOTS = [f"{h:02d}:00" for h in range(12, 23)]  # 12:00 - 22:00


def now():
    return datetime.now(TZ)


@contextmanager
def conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def stock_status(qty, threshold):
    """Availability is computed automatically from stock quantity."""
    if qty <= 0:
        return "Out of Stock"
    return "Low Stock" if qty <= threshold else "Available"


SEED = [  # name, category, description, price PKR, emoji, stock, low-threshold
    ("Chicken Malai Boti", "Starters", "Creamy, tender chicken morsels grilled over charcoal.", 1290, "🍢", 25, 5),
    ("Dahi Bhallay", "Starters", "Soft lentil dumplings in chilled yogurt with tamarind chutney.", 650, "🥣", 20, 5),
    ("Crispy Samosa Platter", "Starters", "Six golden samosas with mint and date-tamarind dips.", 590, "🥟", 30, 8),
    ("Mutton Karahi", "Main Course", "Wok-fired mutton with tomato, ginger and green chilli.", 3200, "🍲", 12, 4),
    ("Butter Chicken", "Main Course", "Rich tomato-butter gravy, served with fresh naan.", 1850, "🍛", 18, 5),
    ("Beef Nihari", "Main Course", "Slow-cooked overnight, finished with fried ginger.", 1950, "🥘", 10, 3),
    ("Chicken Biryani", "Main Course", "Fragrant basmati layered with spiced chicken and saffron.", 1250, "🍚", 22, 5),
    ("Mixed BBQ Platter", "BBQ & Grill", "Seekh kebab, tikka, malai boti and chops for two.", 3900, "🍖", 8, 3),
    ("Gulab Jamun", "Desserts", "Warm milk dumplings in cardamom-rose syrup.", 450, "🍮", 30, 8),
    ("Kheer", "Desserts", "Slow-simmered rice pudding with pistachios.", 420, "🍨", 15, 5),
    ("Kashmiri Chai", "Beverages", "Pink tea with milk, almonds and pistachio.", 350, "🍵", 40, 10),
    ("Mango Lassi", "Beverages", "Thick chilled yogurt drink with ripe Sindhri mango.", 480, "🥭", 25, 6),
]


def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS menu_items(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL,
          description TEXT DEFAULT '', price INTEGER NOT NULL CHECK(price>=0), image_url TEXT DEFAULT '',
          emoji TEXT DEFAULT '🍽️', stock_qty INTEGER NOT NULL DEFAULT 0, low_threshold INTEGER NOT NULL DEFAULT 5,
          is_active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(
          id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, phone TEXT NOT NULL,
          notes TEXT DEFAULT '', total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS order_items(
          id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
          item_id INTEGER, name TEXT NOT NULL, qty INTEGER NOT NULL, price INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS tables_(
          id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT NOT NULL, capacity INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS reservations(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT UNIQUE NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL,
          party_size INTEGER NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL, table_id INTEGER REFERENCES tables_(id),
          requests TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT NOT NULL);
        """)
        if c.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
            c.executemany("INSERT INTO menu_items(name,category,description,price,emoji,stock_qty,low_threshold) "
                          "VALUES(?,?,?,?,?,?,?)", SEED)
        if c.execute("SELECT COUNT(*) FROM tables_").fetchone()[0] == 0:
            c.executemany("INSERT INTO tables_(label,capacity) VALUES(?,?)",
                          [("T1", 2), ("T2", 2), ("T3", 4), ("T4", 4), ("T5", 4), ("T6", 6), ("T7", 6), ("T8", 10)])


# ---------- Menu ----------
def get_menu(include_inactive=False):
    q = "SELECT * FROM menu_items" + ("" if include_inactive else " WHERE is_active=1") + " ORDER BY category, name"
    with conn() as c:
        rows = [dict(r) for r in c.execute(q)]
    for r in rows:
        r["status"] = stock_status(r["stock_qty"], r["low_threshold"])
    return rows


def save_item(item_id, name, category, description, price, image_url, emoji, stock_qty, low_threshold, is_active):
    vals = (name.strip(), category.strip(), description.strip(), int(price), image_url.strip(),
            emoji.strip() or "🍽️", int(stock_qty), int(low_threshold), int(is_active))
    with conn() as c:
        if item_id is None:
            c.execute("INSERT INTO menu_items(name,category,description,price,image_url,emoji,stock_qty,"
                      "low_threshold,is_active) VALUES(?,?,?,?,?,?,?,?,?)", vals)
        else:
            c.execute("UPDATE menu_items SET name=?,category=?,description=?,price=?,image_url=?,emoji=?,"
                      "stock_qty=?,low_threshold=?,is_active=? WHERE id=?", vals + (item_id,))


def update_stock(item_id, qty, threshold):
    with conn() as c:
        c.execute("UPDATE menu_items SET stock_qty=?, low_threshold=? WHERE id=?",
                  (max(0, int(qty)), max(0, int(threshold)), item_id))


def delete_item(item_id):
    with conn() as c:
        c.execute("DELETE FROM menu_items WHERE id=?", (item_id,))


# ---------- Orders ----------
def place_order(name, phone, notes, cart):
    """cart = {item_id: qty}. Stock is checked and reduced atomically; status updates automatically."""
    with conn() as c:
        c.execute("BEGIN IMMEDIATE")
        lines, total = [], 0
        for item_id, qty in cart.items():
            r = c.execute("SELECT * FROM menu_items WHERE id=? AND is_active=1", (item_id,)).fetchone()
            if r is None:
                raise ValueError("An item in your cart is no longer on the menu.")
            if r["stock_qty"] < qty:
                raise ValueError(f"Sorry, only {r['stock_qty']} x {r['name']} left.")
            lines.append((r, qty))
            total += r["price"] * qty
        cur = c.execute("INSERT INTO orders(customer_name,phone,notes,total,created_at) VALUES(?,?,?,?,?)",
                        (name, phone, notes, total, now().strftime("%Y-%m-%d %H:%M")))
        for r, qty in lines:
            c.execute("INSERT INTO order_items(order_id,item_id,name,qty,price) VALUES(?,?,?,?,?)",
                      (cur.lastrowid, r["id"], r["name"], qty, r["price"]))
            c.execute("UPDATE menu_items SET stock_qty=stock_qty-? WHERE id=?", (qty, r["id"]))
        return cur.lastrowid, total


def get_orders():
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT o.*, (SELECT GROUP_CONCAT(qty||'x '||name, ', ') FROM order_items WHERE order_id=o.id) AS items "
            "FROM orders o ORDER BY o.id DESC")]


def set_order_status(order_id, status):
    """Cancelling an order automatically returns its items to stock."""
    with conn() as c:
        old = c.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if old is None:
            return
        if status == "Cancelled" and old["status"] != "Cancelled":
            c.execute("UPDATE menu_items SET stock_qty=stock_qty+(SELECT qty FROM order_items WHERE order_id=? "
                      "AND item_id=menu_items.id) WHERE id IN (SELECT item_id FROM order_items WHERE order_id=?)",
                      (order_id, order_id))
        c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


# ---------- Reservations ----------
def _free_table(c, date, time, party):
    return c.execute(
        "SELECT * FROM tables_ WHERE capacity>=? AND id NOT IN (SELECT table_id FROM reservations "
        "WHERE date=? AND time=? AND status IN ('Pending','Confirmed') AND table_id IS NOT NULL) "
        "ORDER BY capacity LIMIT 1", (party, date, time)).fetchone()


def available_slots(date, party):
    with conn() as c:
        return [t for t in TIME_SLOTS if _free_table(c, date, t, party)]


def create_reservation(name, phone, party, date, time, requests):
    with conn() as c:
        c.execute("BEGIN IMMEDIATE")
        t = _free_table(c, date, time, party)
        if t is None:
            raise ValueError("Sorry, that time was just taken. Please choose another slot.")
        ref = "MB-" + secrets.token_hex(3).upper()
        c.execute("INSERT INTO reservations(ref,name,phone,party_size,date,time,table_id,requests,created_at) "
                  "VALUES(?,?,?,?,?,?,?,?,?)",
                  (ref, name, phone, party, date, time, t["id"], requests, now().strftime("%Y-%m-%d %H:%M")))
        return ref, t["label"]


def get_reservations():
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT r.*, t.label AS table_label FROM reservations r LEFT JOIN tables_ t ON t.id=r.table_id "
            "ORDER BY r.date DESC, r.time DESC")]


def set_reservation_status(res_id, status):
    with conn() as c:
        c.execute("UPDATE reservations SET status=? WHERE id=?", (status, res_id))
