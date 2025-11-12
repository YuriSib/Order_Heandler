import time
import datetime
import gspread
from gspread.utils import rowcol_to_a1

from logger import logger
from PMscrapper import PgSqlModel


class SaleTableError(Exception):
    def __init__(self, message):
        super().__init__(message)


def write_table(order_dt, order_id):
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("Orders").sheet1
    rows = sheet.get_all_values()
    cur_row = len(rows)

    order_data = [
        gspread.Cell(cur_row + 1, 1, order_id),
        gspread.Cell(cur_row+1, 2, order_dt['Дата']),
        gspread.Cell(cur_row + 1, 3, order_dt['Имя покупателя']),
        gspread.Cell(cur_row + 1, 4, order_dt['Телефон']),
        gspread.Cell(cur_row + 1, 5, order_dt['E-mail']),
        gspread.Cell(cur_row + 1, 14, order_dt['Способ доставки']),
        gspread.Cell(cur_row + 1, 17, order_dt["Способ связи"]),
    ]
    sheet.update_cells(order_data)

    products = order_dt['Товары']
    quantity_prod = len(products)

    words = ['A', 'B', 'C', 'D', 'E', 'G', 'N', 'O', 'P', 'Q', 'R', 'S']

    # Объединяем ячейки с данными о заказе.
    if quantity_prod > 1:
        def col_to_index(col_letter):
            return gspread.utils.a1_to_rowcol(f'{col_letter}1')[1] - 1

        requests = []
        for word in words:
            requests.append(
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet.id,
                            "startRowIndex": cur_row,
                            "endRowIndex": cur_row+quantity_prod,
                            "startColumnIndex": col_to_index(word),
                            "endColumnIndex": col_to_index(word) + 1
                        },
                        "mergeType": "MERGE_COLUMNS"
                    }
                }
            )
        sheet.spreadsheet.batch_update({'requests': requests})

    PGM = PgSqlModel()

    row = cur_row+1

    products_data = []
    summ = 0
    for product in products:
        # Добавляем в список на формирование строки заранее известные значения (Стоимость, наименование, кол-во)
        products_data.append(gspread.Cell(row, 6, product['Цена за ед.']))
        products_data.append(gspread.Cell(row, 8, product['Название']))
        products_data.append(gspread.Cell(row, 9, product['Количество']))

        summ += float(product['Цена за ед.'].replace(",", ".")) * float(product['Количество'].replace(",", "."))

        # Берем из БД значения складских остатков по товару (итерируемся по каждому складу)

        stocks = PGM.get_store_stocks(product['Название'])
        col = 10
        for store, stock in stocks.items():
            if not stock:
                stock = 0
            products_data.append(gspread.Cell(row, col, stock))
            col += 1
        row += 1
        logger.debug(
            f"""Добавил в список значения {product['Цена за ед.'], product['Название'], product['Количество'], stocks}"""
        )

    sheet.update_cells(products_data)
    sheet.update_cell(row=cur_row+1, col=7, value=summ)


def update_status(order_id, order_status):
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("Orders").sheet1

    status_color = {
        'ОТМЕНЕН': {"red": 0.5, "green": 0.5, "blue": 0.5},
        'НЕ СОСТОЯЛСЯ': {"red": 2.0, "green": 0.0, "blue": 0.0},
        'СОЗДАН': {"red": 0.0, "green": 0.0, "blue": 0.0},
        'ОЖИДАЕТ ОПЛАТЫ': {"red": 0.0, "green": 0.0, "blue": 3.0},
        'ПОЛУЧЕН': {"red": 1, "green": 1, "blue": 0},
        'СОВЕРШЕН БЕЗ ОПОВЕЩЕНИЯ': {"red": 0, "green": 3, "blue": 0},
        'СОВЕРШЕН': {"red": 0, "green": 1.5, "blue": 0},

        'ИНИЦИИРОВАН ВОЗВРАТ': {"red": 0.0, "green": 1, "blue": 2},
        'ЧАСТИЧНО ВОЗВРАЩЕН': {"red": 0.0, "green": 1, "blue": 2},
        'ВОЗВРАЩЕН': {"red": 0.0, "green": 1, "blue": 2},
    }

    try:
        color = status_color[order_status]
    except Exception as e:
        logger.error('Не удалось получить статус заказа. ')

    else:
        values = sheet.col_values(1)
        curr_row = 0
        for value in values:
            curr_row += 1
            if value == order_id:
                sheet.update_cell(row=curr_row, col=19, value=order_status)
                sheet.format(f'S{curr_row}', {
                    "backgroundColor": color,
                })


def alarm_for_sale():
    gc = gspread.service_account(filename='creds.json')
    sheet = gc.open("Sale_schedule").sheet1

    # Назначаю колонки "наименование Скидки"
    col_sale_name_1, col_sale_name_2, col_sale_name_3 = 2, 7, 12

    # Ищем номер строки с сегодняшней датой
    day_today = datetime.date.today().strftime("%d.%m")
    dates = sheet.col_values(1)
    current_row = None
    for table_date in dates:
        if table_date == day_today:
            current_row = dates.index(table_date) + 1
            break
    if not current_row:
        time.sleep(40)
        raise SaleTableError(f"Сегодняшней даты ({day_today}) не было найдено в таблице.")

    for col_sale_name in (col_sale_name_1, col_sale_name_2, col_sale_name_3):
        # Есть ли скидка сегодня?
        sale_name = sheet.cell(col=col_sale_name, row=current_row).value
        # Была ли эта скидка вчера?
        yesterday_sale_name = sheet.cell(col=col_sale_name, row=current_row - 1).value
        logger.debug(sale_name)

        if sale_name:
            if not yesterday_sale_name:
                sale_name = sheet.cell(col=col_sale_name, row=current_row).value
                return f"""Пора назначать скидку "{sale_name}" """
        else:
            if yesterday_sale_name:
                sale_name = sheet.cell(col=col_sale_name, row=current_row-1).value
                return f"""Пора отменять скидку "{sale_name}" """
    time.sleep(40)



if __name__ == "__main__":
    # update_status('75', 'НЕ СОСТОЯЛСЯ')
    # alarm_for_sale()

    curr_time = datetime.datetime.now().strftime("%H:%M")
    if curr_time == "16:27":
        alarm = alarm_for_sale()
        if alarm:
            print(alarm)
    # print(datetime.date.today().strftime("%d.%m"))
