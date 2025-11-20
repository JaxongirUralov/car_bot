import sqlite3
import os

DB_NAME = "orders.db"

def init_db():
    print("INIT_DB CALLED")
    print("Current working directory:", os.getcwd())
    print("Creating DB at:", DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            model TEXT,
            color TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_order(user_id, model, color):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, model, color) VALUES (?, ?, ?)",
        (user_id, model, color)
    )
    conn.commit()
    conn.close()


def get_orders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, model, color FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_order(order_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
