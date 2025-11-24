# database.py
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_NAME = "orders.db"
UZ_TZ = ZoneInfo("Asia/Tashkent")

# --------------------------
# SUPPLIER DATA (Option A)
# --------------------------
SUPPLIER_DATA = [
    # ------- S -------
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

    # ------- H -------
    ("H", "LS", "Steel_wheel_16", "Tyre_Co", 4),
    ("H", "LT", "Alloy_wheel_16", "Tyre_Co", 4),
    ("H", "Premier", "Alloy_wheel_17", "Tyre_Co", 4),
    ("H", "LT", "Roof_rack", "Roof_Co", 2),
    ("H", "Premier", "Roof_rack_red", "Roof_Co", 2),
    ("H", "Premier", "Sunroof", "Sunroof_Co", 1),
    ("H", "LS", "Halogen", "Lamp_Co", 2),
    ("H", "LT", "Projection_type", "Lamp_Co", 2),
    ("H", "Premier", "LED", "Lamp_Co", 2),
    ("H", "LT", "Halogen_Fog", "Lamp_Co", 2),
    ("H", "Premier", "LED_Fog", "Lamp_Co", 2),
    ("H", "LS", "Windscreen", "Wind_Co", 1),
    ("H", "LT", "Windscreen", "Wind_Co", 1),
    ("H", "Premier", "Windscreen", "Wind_Co", 1),
    ("H", "LS", "Tinted_glass", "Wind_Co", 5),
    ("H", "LT", "Privacy_glass", "Wind_Co", 5),
    ("H", "Premier", "Privacy_glass", "Wind_Co", 5),

    # ------- V -------
    ("V", "LS", "Steel_wheel_16", "Tyre_Co", 4),
    ("V", "LS", "Halogen", "Lamp_Co", 2),
    ("V", "LS", "Windscreen", "Wind_Co", 1),
    ("V", "LS", "Tinted_glass", "Wind_Co", 5),

    ("V", "LT", "Alloy_wheel_16", "Tyre_Co", 4),
    ("V", "LT", "Roof_rack", "Roof_Co", 2),
    ("V", "LT", "Projection_type", "Lamp_Co", 2),
    ("V", "LT", "Halogen_Fog", "Lamp_Co", 2),
    ("V", "LT", "Windscreen", "Wind_Co", 1),
    ("V", "LT", "Privacy_glass", "Wind_Co", 5),

    ("V", "Premier", "Alloy_wheel_17", "Tyre_Co", 4),
    ("V", "Premier", "Roof_rack_red", "Roof_Co", 2),
    ("V", "Premier", "Sunroof", "Sunroof_Co", 1),
    ("V", "Premier", "LED", "Lamp_Co", 2),
    ("V", "Premier", "LED_Fog", "Lamp_Co", 2),
    ("V", "Premier", "Windscreen", "Wind_Co", 1),
    ("V", "Premier", "Privacy_glass", "Wind_Co", 5),
]

# ----------------------------------------------------
# DB initialization
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            supplier TEXT,
            part TEXT,
            qty INTEGER,
            created_at TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    conn.commit()
    conn.close()


# ----------------------------------------------------
# Add main order and create supplier orders automatically
# ----------------------------------------------------
def add_order(user_id, first, last, phone, model, option, color):
    """Insert order and corresponding supplier orders.
       Returns new order_id."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now(UZ_TZ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO orders (user_id, first_name, last_name, phone, model, option, color, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, first, last, phone, model, option, color, now))

    order_id = cursor.lastrowid

    # insert supplier orders for matching model+option
    for m, opt, part, supplier, qty in SUPPLIER_DATA:
        if m == model and opt == option:
            cursor.execute("""
                INSERT INTO supplier_orders (order_id, supplier, part, qty, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, supplier, part, qty, now))

    conn.commit()
    conn.close()
    return order_id


# ----------------------------------------------------
# Fetch all orders (for super admin)
# ----------------------------------------------------
def get_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, first_name, last_name, phone, model, option, color, created_at
        FROM orders
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ----------------------------------------------------
# Get supplier-specific orders (for supplier admins)
# Return joined data with order context
# ----------------------------------------------------
def get_supplier_orders(supplier_name):
    """
    Returns rows:
    supplier_order_id, order_id, supplier, part, qty, supplier_created_at,
    order_first_name, order_last_name, order_phone, order_model, order_option, order_color, order_created_at
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.order_id, s.supplier, s.part, s.qty, s.created_at,
               o.first_name, o.last_name, o.phone, o.model, o.option, o.color, o.created_at
        FROM supplier_orders s
        JOIN orders o ON s.order_id = o.id
        WHERE s.supplier = ?
        ORDER BY s.id DESC
    """, (supplier_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ----------------------------------------------------
# Delete order (and its supplier orders)
# ----------------------------------------------------
def delete_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM supplier_orders WHERE order_id = ?", (order_id,))
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))

    conn.commit()
    conn.close()
