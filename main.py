import telebot
import datetime
import json

import telebot_calendar
from telebot_calendar import CallbackData

from telebot.types import ReplyKeyboardRemove, CallbackQuery

import config

bot = telebot.TeleBot(config.token)

task_calendar = CallbackData("task_calendar", "action", "year", "month", "day")

tasks_list = []

def toJSON(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    else:
        return o.__dict__

class Task:
    id = -1
    name = "unidentified task"
    desc = "unidentified desc"
    date = datetime.datetime.now()
    
    def __init__(self, serial):
        if serial:
            data = json.loads(serial)

            self.id = data.get("id")
            self.name = data.get("name")
            self.desc = data.get("desc")
            self.date = datetime.datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M:%S")

    def toJSON(self):
        return json.dumps(self, default=toJSON)

@bot.message_handler(commands=["help"])
def help_message(message):
    bot.send_message(message.chat.id,
        "Данный бот используется для хранения и вывода списка дел.")
    commands_message = "Список команд:\n" \
        "/help - Вывести описание бота и список поддерживаемых команд.\n" \
        "/addtask - Добавить новое дело.\n" \
        "/deltask <Номер дела> - Удалить дело из списка.\n" \
        "/tasks - Вывести список текущих дел.\n"
    bot.send_message(message.chat.id, commands_message)

@bot.message_handler(commands=["tasks"])
def tasks(message):
    if len(tasks_list) > 0:
        for task in tasks_list:
            bot.send_message(message.chat.id, "Дело #" + str(task.id) + ": " + task.name + "\n\nОписание: " + task.desc + "\n\nДата: " + task.date.strftime("%d.%m.%Y"))
    else:
        bot.send_message(message.chat.id, "Список дел пуст. Добавьте новое дело, написав /addtask.")

@bot.message_handler(commands=["deltask"])
def del_task(message):
    try:
        id = int(message.text.split()[1])

        for task in tasks_list:
            if task.id == id:
                tasks_list.remove(task)
                bot.send_message(message.chat.id, "Дело #" + str(id) + " удалено.")
                return

        bot.send_message(message.chat.id, "Дело не найдено.")
    except TypeError:
        bot.send_message(message.chat.id, "Вы не указали номер дела.")


@bot.message_handler(commands=["addtask"])
def add_task(message):
    global new_task
    new_task = Task(None)
    bot.send_message(message.chat.id, "Введите название дела.")
    bot.register_next_step_handler(message, get_task_name)

def get_task_name(message):
    new_task.name = message.text

    bot.send_message(message.chat.id, "Введите описание дела.")

    bot.register_next_step_handler(message, get_task_desc)

def get_task_desc(message):
    new_task.desc = message.text

    now = datetime.datetime.now()
    bot.send_message(message.chat.id,
    "Выбарите дату, до которой дело должно быть выполнено.",
    reply_markup=telebot_calendar.create_calendar(
        name = task_calendar.prefix,
        year = now.year,
        month = now.month
    ))

@bot.callback_query_handler(func=lambda call: call.data.startswith(task_calendar.prefix))
def callback_inline(call: CallbackQuery):
    name, action, year, month, day = call.data.split(task_calendar.sep)
    date = telebot_calendar.calendar_query_handler(
        bot=bot, call=call, name=name, action=action, year=year, month=month, day=day
    )
    if action == "DAY":
        new_task.date = date
        max_id = 0

        for task in tasks_list:
            if task.id > max_id:
                max_id = task.id

        new_task.id = max_id + 1

        tasks_list.append(new_task)

        saveData()

        bot.send_message(call.from_user.id, "Дело сохранено!")
    elif action == "CANCEL":
        bot.send_message(call.from_user.id, "Создание дела отменено.")

def saveData():
    file = open("data.txt", "w")
    for task in tasks_list:
        print(task.toJSON())
        file.write(task.toJSON() + ";")

def loadData():
    try:
        file = open("data.txt", "r")
        foo = file.read().split(";")
        for text in foo:
            if text != "":
                tasks_list.append(Task(text))
    except IOError:
        print("Data not found")

@bot.message_handler(content_types=["text"])
def errorText(message):
    bot.send_message(message.chat.id, "Данная команда не поддерживается. Список команд: /help.")

loadData()

bot.polling()
