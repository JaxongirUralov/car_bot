# database.py
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_NAME = "orders.db"
UZ_TZ = ZoneInfo("Asia/Tashkent")

SUPPLIER_DATA = [
    ("S", "LS", "Steel_wheel_16", "Tyre_Co", 4),
    ("S", "LS", "Halogen", "Lamp_Co", 2),
    ("S", "LS", "Windscreen", "Wind_Co", 1),
    ("S", "LS", "Tinted_glass", "Wind_Co", 5),

    ("S", "LT", "Alloy_wheel_16", "Tyre_Co", 4),
    ("S", "LT", "Roof_rack", "Roof_Co", 2),
    ("S", "LT", "Projection_type", "Lamp_Co", 2),
    ("S", "LT", "Halogen_Fog", "Lamp_Co", 2),
    ("S", "LT", "Windscreen", "Wind_Co", 1),
    ("S", "LT", "Privacy_glass", "Wind_Co", 5),

    ("S", "Premier", "Alloy_wheel_17", "Tyre_Co", 4),
    ("S", "Premier", "Roof_rack_red", "Roof_Co", 2),
    ("S", "Premier", "Sunroof", "Sunroof_Co", 1),
    ("S", "Premier", "LED", "Lamp_Co", 2),
    ("S", "Premier", "LED_Fog", "Lamp_Co", 2),
    ("S", "Premier", "Windscreen", "Wind_Co", 1),
    ("S", "Premier", "Privacy_glass", "Wind_Co", 5),
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            model TEXT,
            option TEXT,
            color TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            supplier TEXT,
            part TEXT,
            qty INTEGER,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_order(user_id, first, last, phone, model, option, color):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    now = datetime.now(UZ_TZ).strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO orders (user_id, first_name, last_name, phone, model, option, color, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, first, last, phone, model, option, color, now))

    order_id = cur.lastrowid

    for m, opt, part, supplier, qty in SUPPLIER_DATA:
        if m == model and opt == option:
            cur.execute("""
                INSERT INTO supplier_orders (order_id, supplier, part, qty, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, supplier, part, qty, now))

    conn.commit()
    conn.close()
    return order_id


def get_orders():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, first_name, last_name, phone, model, option, color, created_at
        FROM orders ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_supplier_orders(supplier):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.order_id, s.supplier, s.part, s.qty, s.created_at,
               o.first_name, o.last_name, o.phone, o.model, o.option, o.color, o.created_at
        FROM supplier_orders s
        JOIN orders o ON s.order_id = o.id
        WHERE s.supplier = ?
        ORDER BY s.id DESC
    """, (supplier,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_supplier_orders_by_order_id(order_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.supplier, s.part, s.qty,
               o.first_name, o.last_name, o.phone,
               o.model, o.option, o.color, o.created_at
        FROM supplier_orders s
        JOIN orders o ON s.order_id = o.id
        WHERE s.order_id = ?
    """, (order_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM supplier_orders WHERE order_id = ?", (order_id,))
    cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
