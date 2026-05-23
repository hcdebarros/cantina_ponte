import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cafe_ponte.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🍽️'
        );

        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            name        TEXT NOT NULL,
            price       REAL NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 0,
            image       TEXT DEFAULT NULL,
            active      INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer    TEXT NOT NULL,
            total       REAL NOT NULL DEFAULT 0,
            status      TEXT NOT NULL DEFAULT 'open',
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            name       TEXT NOT NULL,
            price      REAL NOT NULL,
            quantity   INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    # Seed default settings
    c.execute("INSERT OR IGNORE INTO settings VALUES ('admin_password', 'admin123')")
    c.execute("INSERT OR IGNORE INTO settings VALUES ('store_name', 'Cantina da Igreja')")

    # Seed categories e produtos apenas se o banco estiver vazio
    total_cats = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if total_cats == 0:
        c.execute("INSERT INTO categories (id, name, icon) VALUES (1, 'Salgados', '🥐')")
        c.execute("INSERT INTO categories (id, name, icon) VALUES (2, 'Bomboniere', '🍫')")
        c.execute("INSERT INTO categories (id, name, icon) VALUES (3, 'Bebidas', '🥤')")

        sample_products = [
            # (category_id, name, price, quantity)
            (1, "Coxinha", 5.00, 30),
            (1, "Empada", 4.50, 25),
            (1, "Risole", 4.00, 20),
            (1, "Esfirra", 3.50, 40),
            (1, "Pão de Queijo", 3.00, 50),
            (2, "Chocolate", 4.00, 20),
            (2, "Biscoito", 2.50, 30),
            (2, "Bala", 1.00, 100),
            (2, "Pirulito", 1.50, 50),
            (3, "Água Mineral", 3.00, 40),
            (3, "Refrigerante Lata", 5.00, 30),
            (3, "Suco de Caixinha", 4.00, 25),
            (3, "Achocolatado", 4.50, 20),
        ]
        c.executemany(
            "INSERT INTO products (category_id, name, price, quantity) VALUES (?,?,?,?)",
            sample_products,
        )

    conn.commit()
    conn.close()


def get_setting(key):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()
