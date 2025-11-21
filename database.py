import sqlite3

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
            color TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_order(user_id, first_name, last_name, phone, model, color):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, first_name, last_name, phone, model, color) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, first_name, last_name, phone, model, color)
    )
    conn.commit()
    conn.close()

def get_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, first_name, last_name, phone, model, color FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

