import requests
import base64
from datetime import datetime


current_date = datetime.now().strftime('%Y-%m-%d')

# Параметры
server_paykeeper = "https://polezniemelochi2.server.paykeeper.ru"  # адрес сервера PayKeeper
uri = f'/info/payments/bydate/?start=2024-01-01&end={current_date}&payment_system_id[]=30&payment_system_id[]=6&status[]=success&status[]=canceled&status[]=refunded&status[]=failed&status[]=obtained&status[]=refunding&status[]=partially_refunded&status[]=stuck&status[]=pending&limit=50&from=0'  # Запрос 1.1 JSON API
user = "Yurii"  # Логин в личном кабинете PayKeeper
password = "qwert_51"  # Соответствующий логину пароль

# Формируем base64 хэш для Basic Auth
auth_string = f"{user}:{password}"
base64_bytes = base64.b64encode(auth_string.encode('utf-8'))
base64_auth = base64_bytes.decode('utf-8')

# Подготавливаем заголовок для авторизации
headers = {
    'Authorization': 'Basic ' + base64_auth
}

params = {
    'start': '2024-09-01',
    'end': current_date,
    'payment_system_id[]': 'MIR',
    'status[]': 'stuck',
    'from': 0,
    'limit': 100
}

# Выполняем GET-запрос
response = requests.get(server_paykeeper + uri, headers=headers)

if response.status_code == 200:
    print(response.text)  # Если запрос успешен, выводим результат
else:
    print(f"Ошибка: {response.status_code} - {response.text}")
