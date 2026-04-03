import sqlite3
import os
from pathlib import Path

db_path = Path(__file__).parent / "sql_agent.db"

if db_path.exists():
    os.remove(db_path)
    print(f"Removed existing database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT,
    stock INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)
""")

customers = [
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com'),
    ('Bob Johnson', 'bob@example.com'),
    ('Alice Williams', 'alice@example.com'),
    ('Charlie Brown', 'charlie@example.com')
]
cursor.executemany('INSERT INTO customers (name, email) VALUES (?, ?)', customers)

products = [
    ('Laptop', 999.99, 'Electronics', 15),
    ('Mouse', 29.99, 'Electronics', 50),
    ('Keyboard', 79.99, 'Electronics', 30),
    ('Monitor', 299.99, 'Electronics', 20),
    ('Desk Chair', 199.99, 'Furniture', 10),
    ('Standing Desk', 499.99, 'Furniture', 8),
    ('Coffee Mug', 12.99, 'Accessories', 100),
    ('Notebook', 5.99, 'Accessories', 200)
]
cursor.executemany('INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)', products)

orders = [
    (1, 1, 1, 999.99, '2024-01-15'),
    (1, 2, 2, 59.98, '2024-01-15'),
    (2, 3, 1, 79.99, '2024-01-18'),
    (2, 4, 1, 299.99, '2024-01-18'),
    (3, 5, 2, 399.98, '2024-01-20'),
    (4, 1, 1, 999.99, '2024-01-22'),
    (4, 6, 1, 499.99, '2024-01-22'),
    (5, 7, 5, 64.95, '2024-01-25'),
    (5, 8, 10, 59.90, '2024-01-25'),
    (1, 4, 1, 299.99, '2024-02-01')
]
cursor.executemany('INSERT INTO orders (customer_id, product_id, quantity, total_amount, order_date) VALUES (?, ?, ?, ?, ?)', orders)

conn.commit()
conn.close()

print(f"Database initialized: {db_path}")
print("Tables created: customers, products, orders")
print(f"- {len(customers)} customers")
print(f"- {len(products)} products")
print(f"- {len(orders)} orders")
