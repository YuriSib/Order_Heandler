import time
from datetime import datetime

from PMscrapper import get_order_from_pk, OrderList
import db_sqlite
from settings_file import STATUS
from write_to_sheets import write_table, update_status, SaleTableError, alarm_for_sale
from logger import logger
from monitoring_bot import send_inform_messages, send_sale_alarm


def main():
    logger.debug(f'Запускаю цикл мониторинга PayKeeper')
    try:
        while True:
            # получаем список заказов от PK
            orders = get_order_from_pk()
            # выбираем те, которых нет еще в БД
            new_orders = db_sqlite.order_checker(orders)

            curr_time = datetime.now().strftime("%H:%M")
            if curr_time == "06:00":
                alarm = alarm_for_sale()
                if alarm:
                    send_sale_alarm(alarm)

            for order in new_orders[::-1]:
                order_id, order_status = order[0], order[1]
                logger.debug(f'order_id = {order_id}, order_status = {order_status}')

                ol = OrderList()
                try:
                    order_data = ol.get_order(int(order_id))
                except ValueError:
                    order_data = ol.get_order(order_id)
                    logger.error("Не удалось перевести id заказа в числовое значение!")
                else:
                    logger.debug(f'получил order_data {order_data}')

                if order_data:
                    logger.debug('Записываю данные заказа в таблицу')
                    try:
                        logger.debug('Запускаю функ. оповещения')
                        send_inform_messages()
                        logger.debug('Записываю данные в таблицу')
                        write_table(order_data, order_id)
                    except Exception as e:
                        logger.error(f'При записи данных о заказе в таблицу возникла ошибка {e}')
                    update_status(order_id, STATUS.get(order_status))
            time.sleep(20)
    except Exception as e:
        logger.critical(f"При роботе основной функции возникла ошибка. {e}")


if __name__ == "__main__":
    main()
    # ol = OrderList()
    # print(ol.get_order(71))
