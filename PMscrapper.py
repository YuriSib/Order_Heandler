import requests
import base64
from datetime import datetime
import hashlib
import psycopg

from settings_file import PM_site_password, DB_NAME, DB_USERNAME, DB_PASSWORD, HOST, PORT
from logger import logger


current_date = datetime.now().strftime('%Y-%m-%d')


class OrderList:
    """Получить список заказов с сайта polezniemelochi.ru"""
    def __init__(self, num_days=30):
        self.num_days = num_days
        date = datetime.now().strftime('%Y-%m-%d')
        key_pass = hashlib.md5((PM_site_password + date).encode('utf-8')).hexdigest()
        options = {
                    'timeout': 30,
                    'auth': ('', key_pass),
                    'allow_redirects': True,
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                    }
        }
        url = f'https://polezniemelochi.ru/engine/orders/getList/{num_days}'
        self.response = requests.get(url=url, **options)
        if self.response.status_code == 200:
            try:
                self.data_orders = self.response.json()['orders']
            except Exception as e:
                logger.critical(f'Ошибка при обработке ответа сервера API {e}')
        else:
            logger.error(f'Не удалось получить список заказов по API. Статус запроса - {self.response.status_code}')
            self.data_orders = None

    def get_order(self, order_id):
        if self.data_orders:
            for order in self.data_orders:
                order_dict = {}

                if order_id == order['order_id']:
                    order_dict['Дата'] = order['date']
                    order_dict['Имя покупателя'] = order['order_form']['login']
                    order_dict['E-mail'] = order['order_form']['mail']
                    order_dict['Адрес'] = order['order_form']['address']
                    order_dict['Телефон'] = order['order_form']['phone']
                    order_dict['Дополнительно'] = order['order_form']['extra']
                    order_dict['Способ доставки'] = order['additionalFields'][1]['value']
                    order_dict['Способ связи'] = order['additionalFields'][3]['value']

                    products = order['goods']
                    order_dict['Товары'] = [{
                        'Название': prod['name'], 'Количество': prod['qt'], 'Цена за ед.': prod['price']
                    } for prod in products]

                    return order_dict


class PgSqlModel:
    def __init__(self):
        """
        Инициализация объекта для работы с PgSql.
        Добавление тригеров.
        """
        self.conn = psycopg.connect(f"dbname={DB_NAME} user={DB_USERNAME} password={DB_PASSWORD} host={HOST} port={PORT}")

    def get_store_stocks(self, product_name: str) -> dict[str: float]:
        query = (f"SELECT stocks_mol, stocks_kh, stocks_9, stocks_sol "
                 f"FROM products_product "
                 f"WHERE name = '{product_name}'")
        cursor = self.conn.cursor()
        cursor.execute(query)
        db_response = cursor.fetchone()

        stores = ['stocks_mol', 'stocks_kh', 'stocks_9', 'stocks_sol']
        if db_response:
            stocks = [float(store) if store else None for store in db_response]
            return dict(zip(stores, stocks))
        else:
            logger.warning(f"В БД не найдена номенклатура с таким наименованием: {product_name}")
            return dict(zip(stores, [0, 0, 0, 0]))


def get_order_from_pk():
    """Получить список заказов с платформы paykeeper"""
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Параметры
    server_paykeeper = "https://polezniemelochi2.server.paykeeper.ru"
    uri = f'/info/payments/bydate/?start=2024-01-01&end={current_date}&payment_system_id[]=30&payment_system_id[]=6&status[]=success&status[]=canceled&status[]=refunded&status[]=failed&status[]=obtained&status[]=refunding&status[]=partially_refunded&status[]=stuck&status[]=pending&limit=50&from=0'  # Запрос 1.1 JSON API
    user = "Yurii"
    password = "qwert_51"

    # Формируем base64 хэш для Basic Auth
    auth_string = f"{user}:{password}"
    base64_bytes = base64.b64encode(auth_string.encode('utf-8'))
    base64_auth = base64_bytes.decode('utf-8')

    headers = {
        'Authorization': 'Basic ' + base64_auth
    }

    order_list = requests.get(server_paykeeper + uri, headers=headers).json()

    orders = []
    for order in order_list:
        order_id, order_status = order['orderid'], order['status']
        orders.append((order_id, order_status))

    return orders


if __name__ == "__main__":
    ol = OrderList(365)
    print(ol.get_order(126))
    # print(get_order_from_pk())
    # PGM = PgSqlModel()
    # print(PGM.get_store_stocks('Пазлы 1000эл. Старый город 05553'))


