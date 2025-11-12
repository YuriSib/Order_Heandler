import telebot
import time
import threading

from settings_file import BOT_TOKEN


bot = telebot.TeleBot(BOT_TOKEN, allow_sending_without_reply=True)

TARGET_USER_ID = 123456789


def send_inform_messages():
    """Функция отправки 3 сообщений пользователю"""
    for msg in range(5):
        bot.send_message(674796107, "🔔 На сайте оформлен заказ. Проверьте его!")
        bot.send_message(6593479727, "🔔 На сайте оформлен заказ. Проверьте его!")
        time.sleep(1)


def send_sale_alarm(text):
    """Функция отправки 3 сообщений пользователю"""
    for msg in range(2):
        bot.send_message(674796107, text)
        bot.send_message(6593479727, text)
        time.sleep(1)
