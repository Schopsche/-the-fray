#!/usr/bin/env python3
"""
Бот-запускалка для мини-приложения THE FRAY.

Никаких зависимостей: только стандартная библиотека Python 3.
Запуск:
    BOT_TOKEN=123:ABC APP_URL=https://ник.github.io/the-fray/ python3 bot.py

Токен в коде не хранится специально — он читается из переменной окружения,
чтобы случайно не попасть в git.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
APP_URL = os.environ.get("APP_URL", "").strip()

if not TOKEN or not APP_URL:
    sys.exit(
        "Нужны обе переменные окружения:\n"
        "  BOT_TOKEN — токен от @BotFather\n"
        "  APP_URL   — https-адрес игры, например https://ник.github.io/the-fray/\n\n"
        "Пример:\n"
        "  BOT_TOKEN=123:ABC APP_URL=https://ник.github.io/the-fray/ python3 bot.py"
    )

if not APP_URL.startswith("https://"):
    sys.exit("APP_URL должен начинаться с https:// — Telegram не открывает http.")

API = "https://api.telegram.org/bot{}/".format(TOKEN)

WELCOME = (
    "THE FRAY\n\n"
    "Волны врагов лезут со всех сторон. Держи палец на экране, чтобы бежать, "
    "оружие стреляет само. Кнопки справа — Волна и рывок.\n\n"
    "Жми, чтобы играть."
)


def call(method, **params):
    """Вызов метода Bot API. Возвращает поле result или None при ошибке."""
    body = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        API + method, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=70) as resp:
            data = json.load(resp)
        if not data.get("ok"):
            print("Ошибка API {}: {}".format(method, data.get("description")))
            return None
        return data.get("result")
    except urllib.error.HTTPError as e:
        print("HTTP {} на {}: {}".format(e.code, method, e.read().decode("utf-8", "replace")))
    except Exception as e:
        print("Сбой запроса {}: {}".format(method, e))
    return None


def play_button():
    """Кнопка, открывающая мини-приложение прямо в переписке."""
    return {"inline_keyboard": [[{"text": "▶  Играть", "web_app": {"url": APP_URL}}]]}


def setup():
    """Разовая настройка бота: команды и кнопка меню у поля ввода."""
    me = call("getMe")
    if not me:
        sys.exit("Токен не принят. Проверь BOT_TOKEN.")
    print("Бот @{} на связи.".format(me.get("username")))

    call("setMyCommands", commands=[
        {"command": "start", "description": "Играть"},
        {"command": "help", "description": "Как играть"},
    ])
    # синяя кнопка слева от поля ввода — открывает игру без единого сообщения
    call("setChatMenuButton", menu_button={
        "type": "web_app",
        "text": "Играть",
        "web_app": {"url": APP_URL},
    })
    print("Кнопка меню ведёт на {}".format(APP_URL))


def handle(update):
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    # если из игры когда-нибудь прилетят данные через Telegram.WebApp.sendData
    if "web_app_data" in msg:
        payload = msg["web_app_data"].get("data", "")
        print("Данные из игры: {}".format(payload[:200]))
        call("sendMessage", chat_id=chat_id, text="Результат принят: {}".format(payload[:200]))
        return

    text = (msg.get("text") or "").strip().lower()
    if text.startswith("/help"):
        call("sendMessage", chat_id=chat_id,
             text="Бежишь пальцем по экрану, стреляешь автоматически. "
                  "Рывок делает тебя неуязвимым, Волна расшвыривает всех вокруг. "
                  "Между волнами — лавка.",
             reply_markup=play_button())
    else:
        call("sendMessage", chat_id=chat_id, text=WELCOME, reply_markup=play_button())


def main():
    setup()
    offset = None
    print("Жду сообщений. Остановить — Ctrl+C.")
    while True:
        params = {"timeout": 50, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        updates = call("getUpdates", **params)
        if updates is None:
            time.sleep(3)          # сеть моргнула — подождать и продолжить
            continue
        for u in updates:
            offset = u["update_id"] + 1
            try:
                handle(u)
            except Exception as e:
                print("Не смог обработать обновление: {}".format(e))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлен.")
