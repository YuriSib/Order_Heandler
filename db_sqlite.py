import sqlite3

from settings_file import STATUS
from write_to_sheets import update_status


def create_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        status TEXT NOT NULL
                    )''')

    conn.close()


def add_order(new_order: tuple):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f'INSERT INTO orders (order_id, status) VALUES {new_order}')
    conn.commit()
    conn.close()


def order_exist(order_id):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM orders WHERE order_id = '{order_id}';")
    result = cursor.fetchone()
    if result:
        return result


def order_update(order_id, new_status):
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(f"UPDATE orders SET status = '{new_status}' WHERE order_id = '{order_id}';")
    conn.commit()
    conn.close()


def order_checker(orders: list):
    new_orders = []

    for order in orders:
        order_id = order[0] if order[0] else "None"
        order_status = order[1]
        order_data = order_exist(order_id)
        if order_data:
            if order_data[2] != order_status:
                order_update(order_id, order_status)
                update_status(order_id, STATUS[order_status])
        else:
            add_order((order_id, order_status))
            new_orders.append((order_id, order_status))

    return new_orders


if __name__ == "__main__":
    # print(order_exist(14))
    order_update(14, '74568')
    # add_order((14, 'canceled'))
