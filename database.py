import sqlite3
from datetime import datetime, timezone, timedelta

DB_NAME = "orders.db"


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
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()



import pandas as pd

DB_NAME = "orders.db"

def load_supplier_table():
    """Exceldagi supplier ma’lumotlarni SQLite bazaga yuklaydi."""

    # 1) Excelni o'qish
    df = pd.read_excel("/mnt/data/Database for.xlsx", sheet_name="Supplier")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 2) Jadval yaratish
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            option TEXT,
            part TEXT,
            supplier TEXT,
            qty INTEGER
        )
    """)

    # 3) Jadvalni tozalash (har safar boshidan yuklash uchun)
    cursor.execute("DELETE FROM supplier_parts")

    # 4) Ma’lumotlarni bazaga qo‘shish
    for _, row in df.iterrows():
        cursor.execute(
            "INSERT INTO supplier_parts (model, option, part, supplier, qty) VALUES (?, ?, ?, ?, ?)",
            (row["Model"], row["Option"], row["Part"], row["Supplier_name"], row["Q-ty"])
        )

    conn.commit()
    conn.close()

    print("Supplier table loaded successfully!")








def add_order(user_id, first_name, last_name, phone, model, option, color):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- ALWAYS UTC+5 TASHKENT TIME (guaranteed correct) ---
    tz = timezone(timedelta(hours=5))
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO orders (user_id, first_name, last_name, phone, model, option, color, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, first_name, last_name, phone, model, option, color, timestamp)
    )

    conn.commit()
    conn.close()


def get_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, first_name, last_name, phone, model, option, color, timestamp FROM orders"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
